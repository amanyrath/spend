"""Centralized database configuration and detection logic.

This module provides a single source of truth for determining which database
backend to use (SQLite vs Firebase) across all modules in the application.

Rules:
1. On Vercel/serverless (no SQLite available): Always use Firebase
2. If USE_SQLITE=true: Force SQLite (local development override)
3. If Firebase credentials exist: Use Firebase
4. Default: Use SQLite (local development)
"""

import os

# Try to import SQLite - will fail on Vercel where it's excluded from deployment
try:
    from src.database import db
    HAS_SQLITE = True
except ImportError:
    # SQLite not available (Vercel/serverless environment)
    HAS_SQLITE = False
    db = None


def should_use_firestore() -> bool:
    """Determine if Firestore should be used instead of SQLite.

    This function encapsulates all the logic for choosing between SQLite
    and Firebase, ensuring consistent behavior across all modules.

    Returns:
        True if Firestore should be used, False if SQLite should be used
    """
    # Rule 1: If SQLite is not available (Vercel deployment), MUST use Firestore
    if not HAS_SQLITE:
        return True

    # Rule 2: Force SQLite if explicitly requested (local development override)
    # This takes precedence over all Firebase configuration
    if os.getenv('USE_SQLITE', '').lower() == 'true':
        return False

    # Rule 3: Use Firestore if Firebase is configured
    # Check for emulator or production credentials
    has_emulator = (
        os.getenv('FIRESTORE_EMULATOR_HOST') is not None or
        os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    )
    has_production_creds = (
        os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None or
        os.path.exists('firebase-service-account.json')
    )

    if has_emulator or has_production_creds:
        # Verify Firebase is actually available
        try:
            from src.database.firestore import get_db as firestore_get_db
            db_client = firestore_get_db()
            return db_client is not None
        except (ImportError, Exception):
            # Firebase import or initialization failed
            return False

    # Rule 4: Default to SQLite for local development
    return False


def get_database_info() -> dict:
    """Get information about the current database configuration.

    Returns:
        Dictionary with database configuration details
    """
    use_firestore = should_use_firestore()

    info = {
        'backend': 'firestore' if use_firestore else 'sqlite',
        'has_sqlite': HAS_SQLITE,
        'environment': 'vercel' if not HAS_SQLITE else 'local',
    }

    if use_firestore:
        # Add Firebase-specific info
        info['firebase_mode'] = 'emulator' if os.getenv('FIRESTORE_EMULATOR_HOST') else 'production'
        if info['firebase_mode'] == 'emulator':
            info['emulator_host'] = os.getenv('FIRESTORE_EMULATOR_HOST', 'unknown')
    else:
        # Add SQLite-specific info
        try:
            from src.database.db import DEFAULT_DB_PATH
            info['db_path'] = DEFAULT_DB_PATH
        except (ImportError, AttributeError):
            info['db_path'] = 'unknown'

    return info


# Cache the initial state for performance
# This is recalculated on each import, but cached within a single process
USE_FIRESTORE = should_use_firestore()


# Convenience function for logging/debugging
def print_database_config():
    """Print current database configuration (useful for debugging)."""
    info = get_database_info()
    print("=" * 60)
    print("DATABASE CONFIGURATION")
    print("=" * 60)
    print(f"Backend: {info['backend'].upper()}")
    print(f"Environment: {info['environment']}")
    print(f"SQLite Available: {info['has_sqlite']}")

    if info['backend'] == 'firestore':
        print(f"Firebase Mode: {info.get('firebase_mode', 'unknown')}")
        if 'emulator_host' in info:
            print(f"Emulator Host: {info['emulator_host']}")
    else:
        print(f"Database Path: {info.get('db_path', 'unknown')}")

    print("=" * 60)
