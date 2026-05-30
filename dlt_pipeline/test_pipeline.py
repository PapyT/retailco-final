"""
test_pipeline.py — run this to test the dlt pipeline locally
Usage: python test_pipeline.py
"""
from dotenv import load_dotenv
import os

# Load .env from project root
load_dotenv(dotenv_path="../.env")

# Override ports for running OUTSIDE Docker
# (inside Docker: lake_db:5432, outside: localhost:5433)
os.environ["LAKE_POSTGRES_HOST"]      = "localhost"
os.environ["LAKE_POSTGRES_PORT"]      = "5433"
os.environ["WAREHOUSE_POSTGRES_HOST"] = "localhost"
os.environ["WAREHOUSE_POSTGRES_PORT"] = "5434"

from pipeline import run_pipeline
run_pipeline()
