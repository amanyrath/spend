"""Script to compute all features for all users.

This script loops through all users in the database and computes
features for both 30d and 180d time windows.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import db
from src.features.signal_detection import compute_all_features


def compute_all_users():
    """Compute features for all users."""
    # Get all users
    users_query = "SELECT user_id FROM users"
    users = db.fetch_all(users_query)
    
    if not users:
        print("No users found in database.")
        return
    
    total_users = len(users)
    print(f"Found {total_users} users. Computing features...")
    
    for idx, user_row in enumerate(users, 1):
        user_id = user_row["user_id"]
        print(f"[{idx}/{total_users}] Computing features for user {user_id}...")
        
        try:
            # Compute for 30d window
            compute_all_features(user_id, "30d")
            
            # Compute for 180d window
            compute_all_features(user_id, "180d")
            
            print(f"  ✓ Features computed successfully")
        except Exception as e:
            print(f"  ✗ Error computing features: {e}")
            continue
    
    print(f"\nCompleted! Computed features for {total_users} users.")


if __name__ == "__main__":
    compute_all_users()

