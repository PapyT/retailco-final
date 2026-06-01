"""
RetailCo dlt Pipeline — Checkpoint 3
======================================
Moves data from lake_db (raw schema) → warehouse_db (raw schema).

Features:
- Incremental loading  : only moves new/updated rows each run
- Type coercion        : handles string prices, signed integers, nullable fields
- Idempotent           : safe to run multiple times — no duplicates
- All 9 entities       : same tables as the extractor produced
"""

import os
import json
import logging
import psycopg
from datetime import datetime, timezone
from typing import Iterator, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
LAKE_HOST     = os.environ.get("LAKE_POSTGRES_HOST",     "localhost")
LAKE_PORT     = os.environ.get("LAKE_POSTGRES_PORT",     "5433")
LAKE_DB       = os.environ.get("LAKE_POSTGRES_DB",       "lake_db")
LAKE_USER     = os.environ.get("LAKE_POSTGRES_USER",     "lake_user")
LAKE_PASSWORD = os.environ.get("LAKE_POSTGRES_PASSWORD", "lake_pass_2024")

WH_HOST       = os.environ.get("WAREHOUSE_POSTGRES_HOST",     "localhost")
WH_PORT       = os.environ.get("WAREHOUSE_POSTGRES_PORT",     "5434")
WH_DB         = os.environ.get("WAREHOUSE_POSTGRES_DB",       "warehouse_db")
WH_USER       = os.environ.get("WAREHOUSE_POSTGRES_USER",     "warehouse_user")
WH_PASSWORD   = os.environ.get("WAREHOUSE_POSTGRES_PASSWORD", "warehouse_pass_2024")


# ─────────────────────────────────────────
# CONNECTIONS
# ─────────────────────────────────────────
def lake_conn():
    return psycopg.connect(
        host=LAKE_HOST, port=int(LAKE_PORT), dbname=LAKE_DB,
        user=LAKE_USER, password=LAKE_PASSWORD, autocommit=False,
    )

def warehouse_conn():
    return psycopg.connect(
        host=WH_HOST, port=int(WH_PORT), dbname=WH_DB,
        user=WH_USER, password=WH_PASSWORD, autocommit=False,
    )


# ─────────────────────────────────────────
# TYPE COERCION
# Cleans raw API data before writing to warehouse
# ─────────────────────────────────────────
def coerce_record(table: str, record: dict) -> dict:
    """
    Apply table-specific type fixes:
    - prices stored as strings → cast to float
    - signed quantity integers → keep as int
    - boolean strings → cast to bool
    - None values → keep as None (warehouse accepts NULLs)
    """
    r = dict(record)  # don't mutate the original

    # Products: sellingPrice and costPrice come as strings e.g. "1500.00"
    if table == "products":
        for field in ("sellingPrice", "costPrice", "unitPrice"):
            if field in r and r[field] is not None:
                try:
                    r[field] = float(str(r[field]).replace(",", ""))
                except (ValueError, TypeError):
                    r[field] = None

    # Payments: amountPaid can be negative (refund) or zero (flagged)
    if table == "payments":
        if "amountPaid" in r and r["amountPaid"] is not None:
            try:
                r["amountPaid"] = float(r["amountPaid"])
            except (ValueError, TypeError):
                r["amountPaid"] = None

    # Order items: quantity and discount must be numeric
    if table == "order_items":
        for field in ("quantity", "unitPrice", "discountPct", "lineTotal"):
            if field in r and r[field] is not None:
                try:
                    r[field] = float(r[field])
                except (ValueError, TypeError):
                    r[field] = None

    # Inventory movements: quantity is signed (negative = outbound)
    if table == "inventory_movements":
        if "quantity" in r and r["quantity"] is not None:
            try:
                r["quantity"] = int(r["quantity"])
            except (ValueError, TypeError):
                r["quantity"] = None

    return r


# ─────────────────────────────────────────
# WATERMARK HELPERS (warehouse side)
# ─────────────────────────────────────────
def ensure_watermark_table(wh: psycopg.Connection):
    """Create the watermarks table in warehouse if it doesn't exist."""
    with wh.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.watermarks (
                entity_name  VARCHAR(100) PRIMARY KEY,
                last_updated TIMESTAMPTZ NOT NULL,
                updated_at   TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    wh.commit()


def get_wh_watermark(wh: psycopg.Connection, table: str):
    """Get the last loaded timestamp for this table in the warehouse."""
    with wh.cursor() as cur:
        cur.execute(
            "SELECT last_updated FROM raw.watermarks WHERE entity_name = %s",
            (table,)
        )
        row = cur.fetchone()
        return row[0] if row else None


def save_wh_watermark(wh: psycopg.Connection, table: str, ts):
    """Save the new watermark after a successful load."""
    with wh.cursor() as cur:
        cur.execute("""
            INSERT INTO raw.watermarks (entity_name, last_updated, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (entity_name)
            DO UPDATE SET last_updated = EXCLUDED.last_updated,
                          updated_at   = NOW()
        """, (table, ts))
    wh.commit()


# ─────────────────────────────────────────
# CORE LOAD FUNCTION
# ─────────────────────────────────────────
def load_table(lake: psycopg.Connection, wh: psycopg.Connection, table: str):
    """
    Incremental load for one table:
    1. Get warehouse watermark (last loaded updated_at)
    2. Read only newer rows from lake
    3. Coerce types
    4. Upsert into warehouse raw schema
    5. Save new watermark
    """
    log.info(f"─── Loading: {table} ───")

    # Step 1: get watermark
    wm = get_wh_watermark(wh, table)
    if wm:
        log.info(f"  Incremental from {wm}")
    else:
        log.info(f"  Full load (first run)")

    # Step 2: read from lake
    with lake.cursor() as cur:
        if wm:
            cur.execute(
                f"SELECT id, data, updated_at FROM raw.{table} WHERE updated_at > %s ORDER BY updated_at",
                (wm,)
            )
        else:
            cur.execute(
                f"SELECT id, data, updated_at FROM raw.{table} ORDER BY updated_at"
            )
        rows = cur.fetchall()

    if not rows:
        log.info(f"  No new rows to load for {table}")
        return

    log.info(f"  Read {len(rows)} rows from lake")

    # Step 3 + 4: coerce and upsert into warehouse
    with wh.cursor() as cur:
        # Create table if it doesn't exist yet
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS raw.{table} (
                id           TEXT PRIMARY KEY,
                data         JSONB NOT NULL,
                extracted_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at   TIMESTAMPTZ
            )
        """)

        upserted = 0
        max_ts = None

        for (row_id, data, updated_at) in rows:
            # data comes as dict from psycopg JSONB
            if isinstance(data, str):
                data = json.loads(data)

            # Apply type coercion
            data = coerce_record(table, data)

            cur.execute(f"""
                INSERT INTO raw.{table} (id, data, extracted_at, updated_at)
                VALUES (%s, %s::jsonb, NOW(), %s)
                ON CONFLICT (id) DO UPDATE
                    SET data         = EXCLUDED.data,
                        extracted_at = EXCLUDED.extracted_at,
                        updated_at   = EXCLUDED.updated_at
            """, (row_id, json.dumps(data), updated_at))

            upserted += 1
            if max_ts is None or (updated_at and updated_at > max_ts):
                max_ts = updated_at

    wh.commit()
    log.info(f"  Upserted {upserted} rows into warehouse raw.{table}")

    # Step 5: save watermark
    if max_ts:
        save_wh_watermark(wh, table, max_ts)
        log.info(f"  Watermark saved: {max_ts}")


# ─────────────────────────────────────────
# ENTITIES TO LOAD
# ─────────────────────────────────────────
TABLES = [
    "stores",
    "employees",
    "payment_methods",
    "customers",
    "products",
    "orders",
    "order_items",
    "payments",
    "inventory_movements",
]


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def run_pipeline():
    """
    Load all 9 tables from lake_db → warehouse_db.
    Called by Airflow DAG or directly from command line.
    """
    import time
    log.info("=" * 60)
    log.info("RetailCo dlt Pipeline starting")
    log.info(f"Lake      : {LAKE_HOST}:{LAKE_PORT}/{LAKE_DB}")
    log.info(f"Warehouse : {WH_HOST}:{WH_PORT}/{WH_DB}")
    log.info("=" * 60)

    lake = lake_conn()
    wh   = warehouse_conn()
    log.info("Both database connections established ✓")

    ensure_watermark_table(wh)

    start     = time.time()
    succeeded = []
    failed    = []

    for table in TABLES:
        try:
            load_table(lake, wh, table)
            succeeded.append(table)
        except Exception as e:
            log.error(f"FAILED: {table} — {e}")
            failed.append(table)

    lake.close()
    wh.close()

    log.info("=" * 60)
    log.info(f"Pipeline done in {time.time() - start:.1f}s")
    log.info(f"Succeeded : {len(succeeded)}/{len(TABLES)} — {succeeded}")

    if failed:
        log.error(f"Failed    : {failed}")
        raise Exception(f"Pipeline failed for: {failed}")

    log.info("All tables loaded into warehouse successfully ✓")
    log.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
