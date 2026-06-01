"""
RetailCo ERP Extractor — Checkpoint 2
======================================
Pulls all 9 entities from the ERP API into the lake_db (raw schema).

Features:
- Pagination          : follows cursors until has_more = false
- Incremental loading : passes ?updated_after= on every run after the first
- Rate limit handling : respects 429 Retry-After header
- Transient errors    : retries up to 5 times with exponential backoff
- Idempotent upserts  : same data run twice = no duplicates
- Watermarks          : saves last updated_at per entity for next run
"""

import os
import time
import json
import logging
import requests
import psycopg
from datetime import datetime, timezone
from typing import Optional

# ─────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────
# CONFIGURATION  (reads from environment)
# ─────────────────────────────────────────
API_KEY      = os.environ["ERP_API_KEY"]
BASE_URL     = os.environ.get("ERP_BASE_URL", "https://hngstage8da-55c7f5f769c8.herokuapp.com")

DB_HOST      = os.environ.get("LAKE_POSTGRES_HOST", "localhost")
DB_PORT      = os.environ.get("LAKE_POSTGRES_PORT", "5433")
DB_NAME      = os.environ.get("LAKE_POSTGRES_DB",   "lake_db")
DB_USER      = os.environ.get("LAKE_POSTGRES_USER", "lake_user")
DB_PASSWORD  = os.environ.get("LAKE_POSTGRES_PASSWORD", "lake_pass_2024")

MAX_RETRIES  = 5
PAGE_SIZE    = 100


# ─────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────
def get_db_connection():
    """Open and return a psycopg v3 connection to the lake database."""
    return psycopg.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=False,
    )


# ─────────────────────────────────────────
# WATERMARK HELPERS
# ─────────────────────────────────────────
def get_watermark(conn, entity: str) -> Optional[str]:
    """
    Return the last successfully extracted timestamp for this entity.
    Returns None if this is the first run (triggers a full extract).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT last_updated FROM raw.watermarks WHERE entity_name = %s",
            (entity,)
        )
        row = cur.fetchone()
        if row:
            # Format as ISO 8601 string for the API
            return row[0].strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        return None


def save_watermark(conn, entity: str, timestamp: str):
    """Save or update the watermark for this entity after a successful extract."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw.watermarks (entity_name, last_updated, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (entity_name)
            DO UPDATE SET last_updated = EXCLUDED.last_updated,
                          updated_at   = NOW()
            """,
            (entity, timestamp)
        )
    conn.commit()
    log.info(f"  Watermark saved for '{entity}': {timestamp}")


# ─────────────────────────────────────────
# HTTP REQUEST WITH RETRY + BACKOFF
# ─────────────────────────────────────────
def api_get(endpoint: str, params: dict) -> dict:
    """
    Call the ERP API with automatic retry on 429 and 5xx errors.
    - 429: reads Retry-After header and waits exactly that long
    - 5xx: exponential backoff (2, 4, 8, 16, 32 seconds)
    - Raises an exception after MAX_RETRIES failed attempts
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {"X-API-Key": API_KEY}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            # ── Rate limited ──────────────────────────────────────
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 60))
                log.warning(f"  Rate limited. Waiting {wait}s before retry {attempt}/{MAX_RETRIES}...")
                time.sleep(wait)
                continue

            # ── Transient server error ────────────────────────────
            if response.status_code >= 500:
                wait = 2 ** attempt   # 2, 4, 8, 16, 32 seconds
                log.warning(f"  Server error {response.status_code}. Waiting {wait}s before retry {attempt}/{MAX_RETRIES}...")
                time.sleep(wait)
                continue

            # ── Auth error — no point retrying ───────────────────
            if response.status_code == 401:
                raise Exception("API key rejected (401). Check your ERP_API_KEY in .env")

            # ── Success ───────────────────────────────────────────
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            wait = 2 ** attempt
            log.warning(f"  Request timed out. Waiting {wait}s before retry {attempt}/{MAX_RETRIES}...")
            time.sleep(wait)

        except requests.exceptions.ConnectionError as e:
            wait = 2 ** attempt
            log.warning(f"  Connection error: {e}. Waiting {wait}s before retry {attempt}/{MAX_RETRIES}...")
            time.sleep(wait)

    raise Exception(f"Failed to fetch {endpoint} after {MAX_RETRIES} attempts")


# ─────────────────────────────────────────
# GENERIC PAGINATED FETCH
# ─────────────────────────────────────────
def fetch_all(endpoint: str, updated_after: Optional[str] = None) -> list:
    """
    Fetch all pages from a list endpoint, following cursors until has_more=false.
    Returns a flat list of all records across all pages.
    """
    all_records = []
    params = {"limit": PAGE_SIZE}

    if updated_after:
        params["updated_after"] = updated_after
        log.info(f"  Incremental extract from {updated_after}")
    else:
        log.info(f"  Full extract (first run)")

    page = 1
    while True:
        log.info(f"  Fetching page {page} of {endpoint}...")
        data = api_get(endpoint, params)

        records = data.get("data", [])
        all_records.extend(records)
        log.info(f"  Page {page}: got {len(records)} records (total so far: {len(all_records)})")

        meta = data.get("meta", {})
        if not meta.get("has_more", False):
            break

        # Follow the cursor to the next page
        params["cursor"] = meta["cursor"]
        # Remove updated_after after first page — cursor handles position now
        params.pop("updated_after", None)
        page += 1

    return all_records


# ─────────────────────────────────────────
# UPSERT HELPERS
# ─────────────────────────────────────────
def upsert_records(conn, table: str, records: list):
    """
    Idempotent upsert: insert new records, update existing ones on conflict.
    Uses PostgreSQL's INSERT ... ON CONFLICT DO UPDATE.
    """
    if not records:
        log.info(f"  No records to upsert into raw.{table}")
        return

    # Build the INSERT statement dynamically from the record keys
    # We store the entire record as JSONB in a 'data' column
    # plus the primary key and updated_at for easy querying
    with conn.cursor() as cur:
        # Ensure the table exists
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS raw.{table} (
                id          TEXT PRIMARY KEY,
                data        JSONB NOT NULL,
                extracted_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ
            )
        """)

        # Upsert each record
        upserted = 0
        for record in records:
            record_id  = str(record.get("id", ""))
            updated_at = record.get("updated_at")

            cur.execute(
                f"""
                INSERT INTO raw.{table} (id, data, extracted_at, updated_at)
                VALUES (%s, %s::jsonb, NOW(), %s)
                ON CONFLICT (id) DO UPDATE
                    SET data         = EXCLUDED.data,
                        extracted_at = EXCLUDED.extracted_at,
                        updated_at   = EXCLUDED.updated_at
                """,
                (record_id, json.dumps(record), updated_at)
            )
            upserted += 1

    conn.commit()
    log.info(f"  Upserted {upserted} records into raw.{table}")


def get_max_updated_at(records: list) -> Optional[str]:
    """
    Find the maximum updated_at across all fetched records.
    This becomes the new watermark for the next run.
    """
    timestamps = [r["updated_at"] for r in records if r.get("updated_at")]
    if not timestamps:
        return None
    return max(timestamps)


# ─────────────────────────────────────────
# ENTITY EXTRACTORS
# ─────────────────────────────────────────
# Each entity maps to: (api_endpoint, lake_table_name)
ENTITIES = [
    ("/stores/",               "stores"),
    ("/employees/",            "employees"),
    ("/payment_methods/",      "payment_methods"),
    ("/customers/",            "customers"),
    ("/products/",             "products"),
    ("/orders/",               "orders"),
    ("/order_items/",          "order_items"),
    ("/payments/",             "payments"),
    ("/inventory_movements/",  "inventory_movements"),
]


def extract_entity(conn, endpoint: str, table: str):
    """
    Full extract-and-load cycle for one entity:
    1. Get watermark (last successful run timestamp)
    2. Fetch all pages from API (incremental if watermark exists)
    3. Upsert into lake database
    4. Save new watermark
    """
    log.info(f"─── Extracting: {table} ({endpoint}) ───")

    # Step 1: get watermark
    watermark = get_watermark(conn, table)

    # Step 2: fetch all records
    records = fetch_all(endpoint, updated_after=watermark)

    if not records:
        log.info(f"  No new/updated records found for {table}")
        return

    # Step 3: upsert into lake
    upsert_records(conn, table, records)

    # Step 4: save new watermark
    max_ts = get_max_updated_at(records)
    if max_ts:
        save_watermark(conn, table, max_ts)
    else:
        # Fallback: use current time as watermark
        save_watermark(conn, table, datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────
def run_extraction():
    """
    Main function — extracts all 9 entities sequentially.
    Called by the Airflow DAG or directly from the command line.
    """
    log.info("=" * 60)
    log.info("RetailCo ERP Extraction starting")
    log.info(f"API base URL : {BASE_URL}")
    log.info(f"Lake DB      : {DB_HOST}:{DB_PORT}/{DB_NAME}")
    log.info("=" * 60)

    conn = get_db_connection()
    log.info("Database connection established")

    start_time = time.time()
    success_count = 0
    failed_entities = []

    for endpoint, table in ENTITIES:
        try:
            extract_entity(conn, endpoint, table)
            success_count += 1
        except Exception as e:
            log.error(f"FAILED to extract {table}: {e}")
            failed_entities.append(table)
            # Continue with remaining entities even if one fails
            continue

    conn.close()

    elapsed = time.time() - start_time
    log.info("=" * 60)
    log.info(f"Extraction complete in {elapsed:.1f}s")
    log.info(f"Successful: {success_count}/{len(ENTITIES)}")

    if failed_entities:
        log.error(f"Failed entities: {failed_entities}")
        raise Exception(f"Extraction failed for: {failed_entities}")

    log.info("All entities extracted successfully ✓")
    log.info("=" * 60)


if __name__ == "__main__":
    run_extraction()