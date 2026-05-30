-- Runs automatically when the lake_db container starts for the first time
-- Creates the raw schema where the Python extractor will write data

CREATE SCHEMA IF NOT EXISTS raw;

-- Watermarks table — tracks the last successful extract time per entity
-- This is how incremental loading knows where to pick up from
CREATE TABLE IF NOT EXISTS raw.watermarks (
    entity_name   VARCHAR(100) PRIMARY KEY,
    last_updated  TIMESTAMPTZ NOT NULL,
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);