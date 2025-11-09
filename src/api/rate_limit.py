"""Rate limiting infrastructure for SpendSense API.

This module provides rate limiting functionality with support for multiple
storage backends (in-memory, database, Redis).
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import os

from src.database import db
from src.database.db import get_db_connection


# Rate limit configuration
RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# Per-endpoint rate limits
RATE_LIMITS = {
    "chat": {"limit": RATE_LIMIT_MESSAGES, "window": RATE_LIMIT_WINDOW},
    "compute_features": {"limit": 5, "window": 60},
    "override": {"limit": 20, "window": 60},
    "flag": {"limit": 20, "window": 60},
}


class RateLimitStorage:
    """Abstract interface for rate limit storage."""
    
    def get_count(self, user_id: str, endpoint: str, window_start: datetime) -> int:
        """Get current count for user/endpoint within window."""
        raise NotImplementedError
    
    def increment(self, user_id: str, endpoint: str, window_start: datetime) -> None:
        """Increment count for user/endpoint."""
        raise NotImplementedError
    
    def cleanup(self, older_than: datetime) -> None:
        """Clean up old entries."""
        raise NotImplementedError


class InMemoryRateLimitStorage(RateLimitStorage):
    """In-memory rate limit storage (for development)."""
    
    def __init__(self):
        self.store: Dict[str, List[datetime]] = defaultdict(list)
    
    def get_count(self, user_id: str, endpoint: str, window_start: datetime) -> int:
        key = f"{user_id}:{endpoint}"
        now = datetime.now()
        # Clean old entries
        self.store[key] = [
            ts for ts in self.store[key]
            if (now - ts).total_seconds() < RATE_LIMIT_WINDOW
        ]
        return len(self.store[key])
    
    def increment(self, user_id: str, endpoint: str, window_start: datetime) -> None:
        key = f"{user_id}:{endpoint}"
        self.store[key].append(datetime.now())
    
    def cleanup(self, older_than: datetime) -> None:
        now = datetime.now()
        for key in list(self.store.keys()):
            self.store[key] = [
                ts for ts in self.store[key]
                if (now - ts).total_seconds() < RATE_LIMIT_WINDOW
            ]


class DatabaseRateLimitStorage(RateLimitStorage):
    """Database-backed rate limit storage."""
    
    def __init__(self):
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure rate_limits table exists."""
        with get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    count INTEGER DEFAULT 1,
                    window_start TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, endpoint, window_start)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rate_limits_user_endpoint 
                ON rate_limits(user_id, endpoint)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rate_limits_expires_at 
                ON rate_limits(expires_at)
            """)
    
    def get_count(self, user_id: str, endpoint: str, window_start: datetime) -> int:
        window_start_str = window_start.isoformat()
        expires_at_str = (window_start + timedelta(seconds=RATE_LIMIT_WINDOW)).isoformat()
        
        query = """
            SELECT SUM(count) as total
            FROM rate_limits
            WHERE user_id = ? AND endpoint = ? 
            AND window_start >= ? AND expires_at > ?
        """
        
        row = db.fetch_one(query, (user_id, endpoint, window_start_str, datetime.now().isoformat()))
        return row["total"] if row and row["total"] else 0
    
    def increment(self, user_id: str, endpoint: str, window_start: datetime) -> None:
        window_start_str = window_start.isoformat()
        expires_at_str = (window_start + timedelta(seconds=RATE_LIMIT_WINDOW)).isoformat()
        
        query = """
            INSERT INTO rate_limits (user_id, endpoint, count, window_start, expires_at)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(user_id, endpoint, window_start) DO UPDATE SET count = count + 1
        """
        
        with get_db_connection() as conn:
            conn.execute(query, (user_id, endpoint, window_start_str, expires_at_str))
    
    def cleanup(self, older_than: datetime) -> None:
        query = "DELETE FROM rate_limits WHERE expires_at < ?"
        with get_db_connection() as conn:
            conn.execute(query, (older_than.isoformat(),))


# Select storage backend based on configuration
RATE_LIMIT_STORAGE_TYPE = os.getenv("RATE_LIMIT_STORAGE", "database").lower()

if RATE_LIMIT_STORAGE_TYPE == "memory":
    rate_limit_storage = InMemoryRateLimitStorage()
else:
    rate_limit_storage = DatabaseRateLimitStorage()


def check_rate_limit(user_id: str, endpoint: str = "default") -> tuple[bool, Optional[int]]:
    """Check if user has exceeded rate limit for endpoint.
    
    Args:
        user_id: User identifier
        endpoint: Endpoint identifier (e.g., "chat", "compute_features")
        
    Returns:
        Tuple of (is_allowed, retry_after_seconds)
        - is_allowed: True if within limit, False if exceeded
        - retry_after_seconds: Seconds until limit resets (None if allowed)
    """
    now = datetime.now()
    config = RATE_LIMITS.get(endpoint, {"limit": RATE_LIMIT_MESSAGES, "window": RATE_LIMIT_WINDOW})
    limit = config["limit"]
    window = config["window"]
    
    # Calculate window start
    window_start = now - timedelta(seconds=window % window)
    window_start = datetime(window_start.year, window_start.month, window_start.day, 
                          window_start.hour, window_start.minute, window_start.second // window * window)
    
    # Get current count
    count = rate_limit_storage.get_count(user_id, endpoint, window_start)
    
    if count >= limit:
        # Calculate retry after
        expires_at = window_start + timedelta(seconds=window)
        retry_after = int((expires_at - now).total_seconds()) + 1
        return False, retry_after
    
    # Increment count
    rate_limit_storage.increment(user_id, endpoint, window_start)
    
    return True, None


def cleanup_rate_limits():
    """Clean up expired rate limit entries."""
    cutoff = datetime.now() - timedelta(seconds=RATE_LIMIT_WINDOW * 2)
    rate_limit_storage.cleanup(cutoff)







