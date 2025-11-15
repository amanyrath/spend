"""Database utilities for SpendSense.

This module provides database connection management and schema initialization
for the SQLite database used by SpendSense.
"""

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime


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
    
    # Ensure directory exists (only when actually connecting)
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    except (OSError, PermissionError):
        # On read-only filesystems (like Vercel), this will fail
        # Try using an in-memory database instead
        if not os.path.exists(db_path):
            db_path = ":memory:"
    
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
    
    # Run migrations after schema initialization
    run_migrations(db_path)


def run_migrations(db_path: Optional[str] = None) -> None:
    """Run database migrations to add new columns to existing tables.
    
    This function checks if columns exist before adding them, making it safe
    to run multiple times (idempotent).
    
    Args:
        db_path: Path to SQLite database file. If None, uses default path.
    """
    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        return  # No migrations to run
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Check if transactions table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='transactions'
        """)
        if not cursor.fetchone():
            return  # Table doesn't exist yet, schema.sql will create it
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(transactions)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Define new columns to add
        new_columns = [
            ("location_address", "TEXT"),
            ("location_city", "TEXT"),
            ("location_region", "TEXT"),
            ("location_postal_code", "TEXT"),
            ("location_country", "TEXT"),
            ("location_lat", "REAL"),
            ("location_lon", "REAL"),
            ("iso_currency_code", "TEXT DEFAULT 'USD'"),
            ("payment_channel", "TEXT"),
            ("authorized_date", "TEXT"),
        ]
        
        # Add missing columns
        added_iso_currency = False
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE transactions ADD COLUMN {column_name} {column_type}")
                    print(f"Added column: {column_name}")
                    if column_name == "iso_currency_code":
                        added_iso_currency = True
                except sqlite3.OperationalError as e:
                    # Column might already exist (race condition) or other error
                    if "duplicate column" not in str(e).lower():
                        print(f"Warning: Could not add column {column_name}: {e}")
        
        # Set default USD for existing rows if we just added the column
        if added_iso_currency:
            cursor.execute("UPDATE transactions SET iso_currency_code = 'USD' WHERE iso_currency_code IS NULL")


def store_operator_action(
    operator_id: str,
    user_id: str,
    action_type: str,
    reason: str,
    recommendation_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> int:
    """Store an operator action in the audit trail.
    
    Args:
        operator_id: ID of the operator performing the action
        user_id: ID of the user the action is performed on
        action_type: Type of action ('override' or 'flag')
        reason: Reason for the action
        recommendation_id: ID of recommendation (for override actions, None for flag)
        db_path: Path to SQLite database file. If None, uses default path.
        
    Returns:
        ID of the created action record
    """
    created_at = datetime.now().isoformat()
    
    query = """
        INSERT INTO operator_actions (operator_id, user_id, action_type, recommendation_id, reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    
    with get_db_connection(db_path) as conn:
        cursor = conn.execute(query, (operator_id, user_id, action_type, recommendation_id, reason, created_at))
        return cursor.lastrowid


def get_operator_actions(
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Optional[str] = None
) -> list:
    """Get operator actions from the audit trail.

    Args:
        user_id: Filter by user_id (optional)
        action_type: Filter by action_type (optional)
        limit: Maximum number of results (optional)
        offset: Number of results to skip
        start_date: Start date filter (ISO format, optional)
        end_date: End date filter (ISO format, optional)
        db_path: Path to SQLite database file. If None, uses default path.

    Returns:
        List of operator action records
    """
    conditions = []
    params = []

    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)

    if action_type:
        conditions.append("action_type = ?")
        params.append(action_type)

    if start_date:
        conditions.append("created_at >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("created_at <= ?")
        params.append(end_date)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT id, operator_id, user_id, action_type, recommendation_id, reason, created_at
        FROM operator_actions
        {where_clause}
        ORDER BY created_at DESC
    """

    if limit:
        query += f" LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    elif offset:
        query += f" OFFSET ?"
        params.append(offset)

    rows = fetch_all(query, tuple(params), db_path)
    return [dict(row) for row in rows]


def get_all_chat_logs(
    user_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Optional[str] = None
) -> list:
    """Get chat logs with optional filtering.
    
    Args:
        user_id: Filter by user_id (optional)
        limit: Maximum number of results (optional)
        offset: Number of results to skip
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        db_path: Path to SQLite database file. If None, uses default path.
        
    Returns:
        List of chat log records
    """
    conditions = []
    params = []
    
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    
    if start_date:
        conditions.append("created_at >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("created_at <= ?")
        params.append(end_date)
    
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    
    query = f"""
        SELECT id, user_id, message, response, citations, guardrails_passed, created_at
        FROM chat_logs
        {where_clause}
        ORDER BY created_at DESC
    """
    
    if limit:
        query += f" LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    elif offset:
        query += f" OFFSET ?"
        params.append(offset)
    
    rows = fetch_all(query, tuple(params), db_path)
    return [dict(row) for row in rows]


def get_recommendation_traces(
    user_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Optional[str] = None
) -> list:
    """Get recommendations with optional filtering.
    
    Args:
        user_id: Filter by user_id (optional)
        limit: Maximum number of results (optional)
        offset: Number of results to skip
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        db_path: Path to SQLite database file. If None, uses default path.
        
    Returns:
        List of recommendation records
    """
    conditions = []
    params = []
    
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    
    if start_date:
        conditions.append("shown_at >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("shown_at <= ?")
        params.append(end_date)
    
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    
    query = f"""
        SELECT recommendation_id, user_id, type, content_id, title, rationale,
               decision_trace, shown_at, overridden, override_reason,
               overridden_at, overridden_by
        FROM recommendations
        {where_clause}
        ORDER BY shown_at DESC
    """
    
    if limit:
        query += f" LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    elif offset:
        query += f" OFFSET ?"
        params.append(offset)
    
    rows = fetch_all(query, tuple(params), db_path)
    return [dict(row) for row in rows]


def get_timeline_events(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, list]:
    """Get all timeline events for a user across all tables.
    
    Args:
        user_id: User ID
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        db_path: Path to SQLite database file. If None, uses default path.
        
    Returns:
        Dictionary with lists of different event types
    """
    return {
        "chat_logs": get_all_chat_logs(user_id, start_date=start_date, end_date=end_date, db_path=db_path),
        "recommendations": get_recommendation_traces(user_id, start_date=start_date, end_date=end_date, db_path=db_path),
        "operator_actions": get_operator_actions(user_id, start_date=start_date, end_date=end_date, db_path=db_path),
    }


def get_consent_status(user_id: str, db_path: Optional[str] = None) -> Optional[dict]:
    """Get consent status for a user.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database file. If None, uses default path.
        
    Returns:
        Dictionary with granted, timestamp, version, or None if user not found
    """
    query = """
        SELECT consent_status, consent_timestamp, consent_version
        FROM users
        WHERE user_id = ?
    """
    
    row = fetch_one(query, (user_id,), db_path)
    if row:
        return {
            "granted": bool(row["consent_status"]),
            "timestamp": row["consent_timestamp"],
            "version": row["consent_version"]
        }
    return {"granted": False, "timestamp": None, "version": None}


def store_consent(
    user_id: str,
    granted: bool,
    ip_address: Optional[str] = None,
    version: str = "1.0",
    db_path: Optional[str] = None
) -> None:
    """Store or update user consent.
    
    Args:
        user_id: User ID
        granted: Whether consent is granted
        ip_address: IP address of the request (optional)
        version: Consent version (default: "1.0")
        db_path: Path to SQLite database file. If None, uses default path.
    """
    created_at = datetime.now().isoformat()
    
    query = """
        UPDATE users
        SET consent_status = ?,
            consent_timestamp = ?,
            consent_version = ?
        WHERE user_id = ?
    """
    
    with get_db_connection(db_path) as conn:
        conn.execute(query, (1 if granted else 0, created_at if granted else None, version, user_id))
        
        # Log consent action to audit trail
        audit_query = """
            INSERT INTO consent_audit_log (user_id, action, ip_address, timestamp)
            VALUES (?, ?, ?, ?)
        """
        action = "granted" if granted else "revoked"
        conn.execute(audit_query, (user_id, action, ip_address or "unknown", created_at))


def revoke_consent(user_id: str, db_path: Optional[str] = None) -> None:
    """Revoke user consent.
    
    Args:
        user_id: User ID
        db_path: Path to SQLite database file. If None, uses default path.
    """
    created_at = datetime.now().isoformat()
    
    query = """
        UPDATE users
        SET consent_status = 0,
            consent_timestamp = NULL
        WHERE user_id = ?
    """
    
    with get_db_connection(db_path) as conn:
        conn.execute(query, (user_id,))
        
        # Log consent revocation to audit trail
        audit_query = """
            INSERT INTO consent_audit_log (user_id, action, ip_address, timestamp)
            VALUES (?, ?, ?, ?)
        """
        conn.execute(audit_query, (user_id, "revoked", "unknown", created_at))


if __name__ == "__main__":
    # Initialize schema when run directly
    print("Initializing database schema...")
    init_schema()
    print("Database schema initialized successfully!")

