-- Runs automatically when the warehouse_db container starts for the first time
-- Creates the schemas dlt and dbt will write into

CREATE SCHEMA IF NOT EXISTS raw;      -- dlt writes here (copy of lake data)
CREATE SCHEMA IF NOT EXISTS staging;  -- dbt staging models live here
CREATE SCHEMA IF NOT EXISTS marts;    -- dbt dimension + fact tables live here