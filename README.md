# RetailCo Data Pipeline

End-to-end modern data pipeline for RetailCo, a Nigerian retail chain with stores in Lagos, Abuja, Port Harcourt, and Kano. Built for HNG Stage 8.

## Architecture

```
ERP REST API
     │  HTTPS
     ▼
Python Extractor  ──►  Lake PostgreSQL (raw schema)
                               │
                          dlt Pipeline
                               │
                               ▼
                     Warehouse PostgreSQL
                        (raw schema)
                               │
                           dbt models
                               │
                    ┌──────────┴──────────┐
                  staging              marts
                (9 views)    (6 dims + 4 facts)
                               │
                          Airflow DAG
                        (daily @midnight)
```

## Stack

| Layer | Tool | Version |
|---|---|---|
| Orchestration | Apache Airflow | 2.9.3 |
| Extraction | Python | 3.11+ |
| Lake storage | PostgreSQL | 15 |
| Loading | dlt | latest |
| Warehouse storage | PostgreSQL | 15 |
| Transformation | dbt-core + dbt-postgres | 1.7.17 |
| Containerisation | Docker + Docker Compose | 24+ / v2+ |

## Prerequisites

- Docker Desktop 24+ with Docker Compose v2+
- Git

---

## Setup

### Step 1 — Clone the repository

**Windows (PowerShell) / Mac / Linux:**
```bash
git clone https://github.com/PapyT/retailco-pipeline.git
cd retailco-pipeline
```

---

### Step 2 — Create your `.env` file

**Windows (PowerShell):**
```powershell
cp .env.example .env
```

**Mac / Linux:**
```bash
cp .env.example .env
```

Then open `.env` in any text editor and replace `your_api_key_here` with your real ERP API key:
```
ERP_API_KEY=your_actual_key_here
```
All other values are pre-configured for local development.

---

### Step 3 — Start all services

**Windows / Mac / Linux (same command):**
```bash
docker compose up -d
```

This starts:
- `lake_db` — PostgreSQL on port 5433 (raw ERP data)
- `warehouse_db` — PostgreSQL on port 5434 (clean analytics data)
- `airflow_meta_db` — PostgreSQL on port 5432 (Airflow metadata)
- `airflow-webserver` — Airflow UI on port 8080
- `airflow-scheduler` — Airflow task runner

Wait ~2 minutes for all services to become healthy:
```bash
docker compose ps
```

All services should show `(healthy)` in the STATUS column.

---

### Step 4 — Access the Airflow UI

Open **http://localhost:8080** in your browser.
- Username: `admin`
- Password: `admin`

---

## Running the Pipeline

### Option A — via Airflow UI (recommended)
1. Go to http://localhost:8080
2. Find `retailco_pipeline` in the DAG list
3. Click the blue toggle to unpause it
4. Click the **▶ Trigger DAG** button
5. Click on the DAG run to watch tasks execute in order

### Option B — via command line (Windows / Mac / Linux — same command)
```bash
docker exec retailco_airflow_scheduler airflow dags trigger retailco_pipeline
```

### Monitor progress
```bash
docker exec retailco_airflow_scheduler airflow dags list-runs --dag-id retailco_pipeline
```

---

## Pipeline Task Order

```
extract → dlt_load → dbt_snapshot → dbt_staging → dbt_marts → dbt_test
```

Each task only starts if the previous one succeeded. Failure at any task stops all downstream tasks.

---

## Running Components Individually

### Extractor (ERP API → lake_db)

**Windows / Mac / Linux:**
```bash
cd extractor
python test_extract.py
```

### dlt Pipeline (lake_db → warehouse_db)

```bash
cd dlt_pipeline
python test_pipeline.py
```

### dbt commands

> **Windows users:** All dbt commands must be on a **single line** in PowerShell.
> Use the Windows tab below for copy-paste-ready single-line commands.

#### Install dbt packages

**Windows (PowerShell) — single line:**
```powershell
docker run --rm --network retailco-pipeline_retailco_net -v "C:\path\to\retailco-pipeline\dbt_retailco:/dbt" ghcr.io/dbt-labs/dbt-postgres:1.7.17 deps --profiles-dir /dbt --project-dir /dbt
```

**Mac / Linux:**
```bash
docker run --rm --network retailco-pipeline_retailco_net \
  -v "$(pwd)/dbt_retailco:/dbt" \
  ghcr.io/dbt-labs/dbt-postgres:1.7.17 \
  deps --profiles-dir /dbt --project-dir /dbt
```

#### Run snapshots (SCD2)

**Windows (PowerShell) — single line:**
```powershell
docker run --rm --network retailco-pipeline_retailco_net -v "C:\path\to\retailco-pipeline\dbt_retailco:/dbt" ghcr.io/dbt-labs/dbt-postgres:1.7.17 snapshot --profiles-dir /dbt --project-dir /dbt
```

**Mac / Linux:**
```bash
docker run --rm --network retailco-pipeline_retailco_net \
  -v "$(pwd)/dbt_retailco:/dbt" \
  ghcr.io/dbt-labs/dbt-postgres:1.7.17 \
  snapshot --profiles-dir /dbt --project-dir /dbt
```

#### Run all models

**Windows (PowerShell) — single line:**
```powershell
docker run --rm --network retailco-pipeline_retailco_net -v "C:\path\to\retailco-pipeline\dbt_retailco:/dbt" ghcr.io/dbt-labs/dbt-postgres:1.7.17 run --profiles-dir /dbt --project-dir /dbt
```

**Mac / Linux:**
```bash
docker run --rm --network retailco-pipeline_retailco_net \
  -v "$(pwd)/dbt_retailco:/dbt" \
  ghcr.io/dbt-labs/dbt-postgres:1.7.17 \
  run --profiles-dir /dbt --project-dir /dbt
```

#### Run tests

**Windows (PowerShell) — single line:**
```powershell
docker run --rm --network retailco-pipeline_retailco_net -v "C:\path\to\retailco-pipeline\dbt_retailco:/dbt" ghcr.io/dbt-labs/dbt-postgres:1.7.17 test --profiles-dir /dbt --project-dir /dbt
```

**Mac / Linux:**
```bash
docker run --rm --network retailco-pipeline_retailco_net \
  -v "$(pwd)/dbt_retailco:/dbt" \
  ghcr.io/dbt-labs/dbt-postgres:1.7.17 \
  test --profiles-dir /dbt --project-dir /dbt
```

> **Tip for Windows users:** Replace `C:\path\to\retailco-pipeline` with your actual path, e.g. `C:\Users\Papy T\Downloads\retailco-pipeline`

---

## Querying the Warehouse

Connect to the warehouse database:

**Windows / Mac / Linux:**
```bash
docker exec retailco_warehouse_db psql -U warehouse_user -d warehouse_db
```

**Revenue by store:**
```sql
SELECT
    s.store_name,
    SUM(f.net_revenue) AS total_revenue,
    COUNT(DISTINCT f.order_id) AS total_orders
FROM staging_marts.fct_sales f
JOIN staging_marts.dim_store s ON f.store_key = s.store_key
GROUP BY s.store_name
ORDER BY total_revenue DESC;
```

**Top 10 products by revenue:**
```sql
SELECT
    p.product_name,
    p.category,
    SUM(f.net_revenue) AS total_revenue,
    SUM(f.quantity) AS units_sold
FROM staging_marts.fct_sales f
JOIN staging_marts.dim_product p ON f.product_key = p.product_key
WHERE p.is_current = true
GROUP BY p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;
```

**Payment method breakdown:**
```sql
SELECT
    pm.method_name,
    COUNT(*) AS payment_count,
    SUM(amount_paid) AS total_amount,
    SUM(CASE WHEN is_refund THEN 1 ELSE 0 END) AS refund_count
FROM staging_marts.fct_payments f
JOIN staging_marts.dim_payment_method pm ON f.payment_method_key = pm.payment_method_key
GROUP BY pm.method_name
ORDER BY total_amount DESC;
```

**Flagged payments (anomalies):**
```sql
SELECT flag_reason, COUNT(*), SUM(amount_paid)
FROM staging_marts.flagged_payments
GROUP BY flag_reason;
```

**Order lifecycle (fulfilment speed):**
```sql
SELECT
    current_status,
    COUNT(*) AS order_count,
    ROUND(AVG(days_to_deliver)::numeric, 1) AS avg_days_to_deliver
FROM staging_marts.fct_order_lifecycle
WHERE days_to_deliver IS NOT NULL
GROUP BY current_status
ORDER BY order_count DESC;
```

---

## Project Structure

```
retailco-pipeline/
├── .env                        # secrets (never committed)
├── .env.example                # template — copy to .env and fill in your key
├── .gitignore
├── docker-compose.yml          # all services
├── Dockerfile.dbt
├── README.md
├── insights.md                 # business insights write-up
├── sql/
│   ├── lake_init.sql           # creates raw schema in lake
│   └── warehouse_init.sql      # creates raw/staging/marts schemas
├── extractor/
│   ├── extract.py              # ERP API extractor
│   ├── test_extract.py         # local test runner
│   └── requirements.txt
├── dlt_pipeline/
│   ├── pipeline.py             # lake → warehouse loader
│   ├── test_pipeline.py        # local test runner
│   └── requirements.txt
├── dbt_retailco/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── packages.yml
│   ├── snapshots/              # SCD2 snapshots (customers, products)
│   ├── models/
│   │   ├── staging/            # 9 staging views
│   │   └── marts/
│   │       ├── dimensions/     # 6 dimension tables
│   │       └── facts/          # 4 fact tables + flagged_payments
│   └── tests/                  # 4 custom data quality tests
├── airflow/
│   ├── dags/
│   │   └── retailco_dag.py     # main pipeline DAG
│   └── requirements.txt
└── design_artifacts/
    ├── bus_matrix.png
    ├── erd.png
    └── architecture.png
```

---

## Data Volume

| Entity | Rows |
|---|---|
| stores | 4 |
| employees | 50 |
| payment_methods | 5 |
| customers | 5,000 |
| products | 2,000 |
| orders | 80,000 |
| order_items | 360,463 |
| payments | 71,900 |
| inventory_movements | 355,102 |
| **Total** | **873,524** |

---

## dbt Test Results

- **77 PASS** / 1 WARN / 0 ERROR out of 78 tests
- Warning: `assert_fct_inventory_non_negative_stock` — expected behaviour when movements start mid-history without opening balances

---

## Stopping the Pipeline

```bash
docker compose down        # stop containers, keep data
docker compose down -v     # stop containers AND delete all data
```
