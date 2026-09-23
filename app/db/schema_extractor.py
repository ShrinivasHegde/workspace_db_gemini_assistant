import sqlite3
from urllib.parse import urlparse

from app.core.config import settings
from app.exceptions import DatabaseConnectionError


def extract_schema() -> str:
    if not settings.target_database_url:
        raise DatabaseConnectionError("TARGET_DATABASE_URL is not configured. Add the database you want to analyze to .env.local.")
    url = settings.target_database_url
    try:
        if url.startswith("sqlite:///"):
            return _sqlite_schema(url.removeprefix("sqlite:///"))
        if url.startswith(("postgresql://", "postgres://")):
            return _postgres_schema(url)
        if url.startswith("mysql://"):
            return _mysql_schema(url)
    except Exception as error:
        raise DatabaseConnectionError(f"Could not read the target database schema: {error}") from error
    raise DatabaseConnectionError("Unsupported DATABASE_URL. Use postgresql://, mysql://, or sqlite:///.")


def _sqlite_schema(path: str) -> str:
    with sqlite3.connect(path) as connection:
        tables = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        lines = ["DATABASE METADATA", "Schema: main"]
        for (table,) in tables:
            lines.append(f"  Table: {table}")
            for _, name, dtype, _, _, _ in connection.execute(f"PRAGMA table_info('{table.replace("'", "''")}')"):
                lines.append(f"    - {name} ({dtype or 'unknown'})")
    return "\n".join(lines)


def _postgres_schema(url: str) -> str:
    import psycopg2
    with psycopg2.connect(url) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT table_schema, table_name, column_name, data_type FROM information_schema.columns WHERE table_schema NOT IN ('pg_catalog', 'information_schema') ORDER BY table_schema, table_name, ordinal_position")
        rows = cursor.fetchall()
    return _render_rows(rows)


def _mysql_schema(url: str) -> str:
    import mysql.connector
    parsed = urlparse(url)
    database = parsed.path.lstrip('/')
    with mysql.connector.connect(host=parsed.hostname, port=parsed.port or 3306, user=parsed.username, password=parsed.password, database=database) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT table_schema, table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = %s ORDER BY table_name, ordinal_position", (database,))
        rows = cursor.fetchall()
    return _render_rows(rows)


def _render_rows(rows) -> str:
    if not rows:
        return "DATABASE METADATA\nNo user tables or columns were found."
    lines, current_schema, current_table = ["DATABASE METADATA"], None, None
    for schema, table, column, dtype in rows:
        if schema != current_schema:
            current_schema, current_table = schema, None
            lines.append(f"Schema: {schema}")
        if table != current_table:
            current_table = table
            lines.append(f"  Table: {table}")
        lines.append(f"    - {column} ({dtype})")
    return "\n".join(lines)
