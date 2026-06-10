"""
JobFlow Database Manager
SQLite connection manager with context managers and utility methods.
"""

import sqlite3
import json
import os
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "jobflow.db")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
MIGRATIONS_PATH = Path(__file__).parent / "migrations"


def get_db_path() -> str:
    """Return the absolute path to the database file."""
    if os.path.isabs(DATABASE_PATH):
        return DATABASE_PATH
    # Resolve relative to project root (two levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    return str(project_root / DATABASE_PATH)


def init_db() -> None:
    """Initialize the database by running the schema SQL."""
    db_path = get_db_path()
    logger.info(f"Initializing database at {db_path}")

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    with get_connection() as conn:
        if SCHEMA_PATH.exists():
            schema_sql = SCHEMA_PATH.read_text()
            conn.executescript(schema_sql)
            conn.commit()
            logger.info("Database schema applied successfully")
        else:
            logger.warning(f"Schema file not found at {SCHEMA_PATH}")


def run_migrations() -> None:
    """Run any pending migration files in order."""
    db_path = get_db_path()
    logger.info("Running migrations...")

    with get_connection() as conn:
        # Create migrations tracking table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        if not MIGRATIONS_PATH.exists():
            logger.warning(f"Migrations directory not found at {MIGRATIONS_PATH}")
            return

        migration_files = sorted(MIGRATIONS_PATH.glob("*.sql"))
        for migration_file in migration_files:
            version = migration_file.stem
            # Check if already applied
            row = conn.execute(
                "SELECT version FROM schema_migrations WHERE version = ?", (version,)
            ).fetchone()

            if row is None:
                logger.info(f"Applying migration: {version}")
                sql = migration_file.read_text()
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
                )
                conn.commit()
                logger.info(f"Migration {version} applied successfully")
            else:
                logger.debug(f"Migration {version} already applied, skipping")


@contextmanager
def get_connection():
    """
    Context manager that yields a SQLite connection.
    Automatically commits on success and rolls back on exception.

    Usage:
        with get_connection() as conn:
            conn.execute("SELECT * FROM jobs")
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error, rolling back: {e}")
        raise
    finally:
        conn.close()


def execute_query(
    sql: str,
    params: Optional[Union[Tuple, List, Dict]] = None,
    fetch: str = "none"
) -> Any:
    """
    Execute a SQL query with optional parameters.

    Args:
        sql: SQL statement to execute
        params: Query parameters (tuple, list, or dict for named params)
        fetch: 'none', 'one', or 'all'

    Returns:
        None, single row dict, or list of row dicts depending on fetch mode
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        if params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        if fetch == "one":
            row = cursor.fetchone()
            return dict(row) if row else None
        elif fetch == "all":
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        else:
            conn.commit()
            return cursor.lastrowid


def fetch_all(sql: str, params: Optional[Union[Tuple, List, Dict]] = None) -> List[Dict]:
    """
    Execute a SELECT query and return all results as a list of dicts.

    Args:
        sql: SELECT SQL statement
        params: Optional query parameters

    Returns:
        List of row dicts
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        if params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def fetch_one(sql: str, params: Optional[Union[Tuple, List, Dict]] = None) -> Optional[Dict]:
    """
    Execute a SELECT query and return a single result as a dict.

    Args:
        sql: SELECT SQL statement
        params: Optional query parameters

    Returns:
        Single row dict or None
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        if params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        row = cursor.fetchone()
        return dict(row) if row else None


def insert_row(table: str, data: Dict[str, Any]) -> int:
    """
    Insert a row into a table.

    Args:
        table: Table name
        data: Dict of column -> value

    Returns:
        Last inserted row ID
    """
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    with get_connection() as conn:
        cursor = conn.execute(sql, list(data.values()))
        conn.commit()
        return cursor.lastrowid


def update_row(table: str, row_id: Any, data: Dict[str, Any], id_column: str = "id") -> int:
    """
    Update a row in a table.

    Args:
        table: Table name
        row_id: Value of the ID column
        data: Dict of column -> value to update
        id_column: Name of the ID column

    Returns:
        Number of rows affected
    """
    set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
    sql = f"UPDATE {table} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE {id_column} = ?"
    params = list(data.values()) + [row_id]
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.rowcount


def upsert_setting(key: str, value: Any) -> None:
    """Insert or update a setting key-value pair."""
    value_str = json.dumps(value) if not isinstance(value, str) else value
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
            (key, value_str)
        )
        conn.commit()


def get_setting(key: str, default: Any = None) -> Any:
    """Retrieve a setting value by key."""
    row = fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
    if row is None:
        return default
    value = row["value"]
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value
