"""
RetailCo Data Pipeline — Airflow DAG
======================================
Checkpoint 5: Orchestrates the full pipeline on a daily schedule.

Task order (strict, each depends on the previous):
  extract → dlt_load → dbt_snapshot → dbt_staging → dbt_marts → dbt_test

Features:
- Daily schedule (@midnight)
- Backfill-capable (catchup=True)
- All tasks have retries with exponential backoff
- Failure at any task stops all downstream tasks
- Full pipeline observable via Airflow UI at http://localhost:8080
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# ─────────────────────────────────────────
# DEFAULT ARGUMENTS
# Applied to every task unless overridden
# ─────────────────────────────────────────
default_args = {
    "owner": "retailco",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}

# ─────────────────────────────────────────
# DBT COMMAND TEMPLATE
# Runs dbt directly inside the Airflow container
# (avoids Docker-in-Docker complexity)
# ─────────────────────────────────────────
DBT_PROJECT_DIR = "/opt/airflow/dbt_retailco"

def dbt_command(dbt_cmd: str) -> str:
    """Build a dbt command to run directly inside the Airflow container."""
    return (
        f"cd {DBT_PROJECT_DIR} && "
        f"dbt {dbt_cmd} "
        f"--profiles-dir {DBT_PROJECT_DIR} "
        f"--project-dir {DBT_PROJECT_DIR}"
    )


# ─────────────────────────────────────────
# PYTHON CALLABLES
# ─────────────────────────────────────────
def run_extraction(**context):
    """
    Task 1: Extract all 9 entities from ERP API → lake_db.
    Uses watermarks for incremental loading.
    """
    import sys
    import os
    sys.path.insert(0, "/opt/airflow/extractor")

    # Inside Docker, DB host is the service name
    os.environ["LAKE_POSTGRES_HOST"] = "lake_db"
    os.environ["LAKE_POSTGRES_PORT"] = "5432"

    from extract import run_extraction
    run_extraction()


def run_dlt_pipeline(**context):
    """
    Task 2: Load lake_db → warehouse_db using dlt pipeline.
    Only moves new/updated rows (incremental).
    """
    import sys
    import os
    sys.path.insert(0, "/opt/airflow/dlt_pipeline")

    os.environ["LAKE_POSTGRES_HOST"]      = "lake_db"
    os.environ["LAKE_POSTGRES_PORT"]      = "5432"
    os.environ["WAREHOUSE_POSTGRES_HOST"] = "warehouse_db"
    os.environ["WAREHOUSE_POSTGRES_PORT"] = "5432"

    from pipeline import run_pipeline
    run_pipeline()


# ─────────────────────────────────────────
# DAG DEFINITION
# ─────────────────────────────────────────
with DAG(
    dag_id="retailco_pipeline",
    description="RetailCo end-to-end data pipeline: Extract → Load → dbt",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=True,           # backfill-capable
    max_active_runs=1,      # prevent concurrent runs overlapping
    tags=["retailco", "etl", "dbt"],
) as dag:

    # ── Task 1: Extract ──────────────────────────────────────
    extract = PythonOperator(
        task_id="extract",
        python_callable=run_extraction,
        retries=3,
        retry_delay=timedelta(minutes=2),
        doc_md="""
        ## Extract
        Calls the ERP REST API and loads all 9 entities into lake_db.
        Uses watermarks for incremental loading — only fetches rows
        updated since the last successful run.
        """,
    )

    # ── Task 2: dlt Load ─────────────────────────────────────
    dlt_load = PythonOperator(
        task_id="dlt_load",
        python_callable=run_dlt_pipeline,
        doc_md="""
        ## dlt Load
        Moves new/updated rows from lake_db → warehouse_db.
        Applies type coercion (string prices → numeric, etc).
        """,
    )

    # ── Task 3: dbt snapshot ─────────────────────────────────
    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command=dbt_command("snapshot"),
        doc_md="""
        ## dbt Snapshot
        Runs SCD2 snapshots for dim_customer and dim_product.
        Captures history when customer segments or product prices change.
        """,
    )

    # ── Task 4: dbt staging ──────────────────────────────────
    dbt_staging = BashOperator(
        task_id="dbt_staging",
        bash_command=dbt_command("run --select staging"),
        doc_md="""
        ## dbt Staging
        Builds all 9 staging views: casts types, renames columns,
        flags soft-deletes and anomalous payments.
        """,
    )

    # ── Task 5: dbt marts ────────────────────────────────────
    dbt_marts = BashOperator(
        task_id="dbt_marts",
        bash_command=dbt_command("run --select marts"),
        doc_md="""
        ## dbt Marts
        Builds all dimension and fact tables:
        6 dims + 4 facts + flagged_payments.
        """,
    )

    # ── Task 6: dbt test ─────────────────────────────────────
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=dbt_command("test"),
        doc_md="""
        ## dbt Test
        Runs all 78 tests: not_null, unique, relationships,
        accepted_values, and 4 custom data quality tests.
        """,
    )

    # ── Task dependency chain ────────────────────────────────
    # Each task only starts if the previous one succeeded.
    # Failure at any step stops all downstream tasks.
    extract >> dlt_load >> dbt_snapshot >> dbt_staging >> dbt_marts >> dbt_test