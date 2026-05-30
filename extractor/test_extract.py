"""
test_extract.py  —  run this to test the extractor locally
Usage:  python test_extract.py
"""
from dotenv import load_dotenv
import os

# Load your .env file so environment variables are available
load_dotenv(dotenv_path="../.env")

# Override DB host/port for running OUTSIDE Docker
# (inside Docker the host is 'lake_db', outside it's 'localhost')
os.environ["LAKE_POSTGRES_HOST"] = "localhost"
os.environ["LAKE_POSTGRES_PORT"] = "5433"

# Now run the extractor
from extract import run_extraction
run_extraction()