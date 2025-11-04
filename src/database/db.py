"""Database utilities for SpendSense.

This module provides database connection management and schema initialization
for the SQLite database used by SpendSense.
"""

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional


# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "spendsense.db"


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a database connection.
    
    Args:
        db_path: Path to SQLite database file. If None, uses default path.
        
    Returns:
        sqlite3.Connection: Database connection object.
    """
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


@contextmanager
def get_db_connection(db_path: Optional[str] = None):
    """Context manager for database connections.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM users")
            rows = cursor.fetchall()
    
    Args:
        db_path: Path to SQLite database file. If None, uses default path.
        
    Yields:
        sqlite3.Connection: Database connection object.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(query: str, params: tuple = (), db_path: Optional[str] = None) -> sqlite3.Cursor:
    """Execute a SQL query and return the cursor.
    
    Args:
        query: SQL query string.
        params: Parameters for the query.
        db_path: Path to SQLite database file. If None, uses default path.
        
    Returns:
        sqlite3.Cursor: Cursor object with query results.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        return cursor


def fetch_one(query: str, params: tuple = (), db_path: Optional[str] = None) -> Optional[sqlite3.Row]:
    """Execute a query and fetch one row.
    
    Args:
        query: SQL query string.
        params: Parameters for the query.
        db_path: Path to SQLite database file. If None, uses default path.
        
    Returns:
        sqlite3.Row or None: Single row result or None if no rows.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchone()


def fetch_all(query: str, params: tuple = (), db_path: Optional[str] = None) -> list[sqlite3.Row]:
    """Execute a query and fetch all rows.
    
    Args:
        query: SQL query string.
        params: Parameters for the query.
        db_path: Path to SQLite database file. If None, uses default path.
        
    Returns:
        list[sqlite3.Row]: List of all row results.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def init_schema(db_path: Optional[str] = None) -> None:
    """Initialize the database schema by executing schema.sql.
    
    Args:
        db_path: Path to SQLite database file. If None, uses default path.
    """
    schema_path = Path(__file__).parent / "schema.sql"
    
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    
    with get_db_connection(db_path) as conn:
        conn.executescript(schema_sql)


if __name__ == "__main__":
    # Initialize schema when run directly
    print("Initializing database schema...")
    init_schema()
    print("Database schema initialized successfully!")

