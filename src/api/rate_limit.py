"""Rate limiting infrastructure for SpendSense API.

This module provides in-memory rate limiting for serverless deployments.
For production cross-instance rate limiting, consider using Redis or similar.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import os


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


class InMemoryRateLimitStorage:
    """In-memory rate limit storage for serverless deployments."""

    def __init__(self):
        self.store: Dict[str, List[datetime]] = defaultdict(list)

    def get_count(self, user_id: str, endpoint: str, window_start: datetime) -> int:
        """Get current count for user/endpoint within window."""
        key = f"{user_id}:{endpoint}"
        now = datetime.now()
        # Clean old entries
        self.store[key] = [
            ts for ts in self.store[key]
            if (now - ts).total_seconds() < RATE_LIMIT_WINDOW
        ]
        return len(self.store[key])

    def increment(self, user_id: str, endpoint: str, window_start: datetime) -> None:
        """Increment count for user/endpoint."""
        key = f"{user_id}:{endpoint}"
        self.store[key].append(datetime.now())

    def cleanup(self, older_than: datetime) -> None:
        """Clean up old entries."""
        now = datetime.now()
        for key in list(self.store.keys()):
            self.store[key] = [
                ts for ts in self.store[key]
                if (now - ts).total_seconds() < RATE_LIMIT_WINDOW
            ]


# Use in-memory storage for serverless deployment
rate_limit_storage = InMemoryRateLimitStorage()


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







