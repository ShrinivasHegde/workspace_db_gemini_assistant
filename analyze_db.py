"""Compatibility command for printing the configured database metadata.

The reusable implementation lives in app.db.schema_extractor and powers the
FastAPI routes. Start the web application with `python main.py`.
"""
from app.db.schema_extractor import extract_schema
from app.exceptions import DatabaseConnectionError

def fetch_db_schema():
    return extract_schema()

if __name__ == "__main__":
    try:
        print(fetch_db_schema())
    except DatabaseConnectionError as error:
        print(f"Schema extraction failed: {error}")
        raise SystemExit(1)
