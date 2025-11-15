"""Script to generate recommendations for all users.

This script loops through all users in the database and generates
recommendations for both 30d and 180d time windows.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import db
from src.recommend.engine import generate_recommendations
from src.database.db_config import USE_FIRESTORE

if USE_FIRESTORE:
    from src.database.firestore import get_all_users


def generate_all_recommendations():
    """Generate recommendations for all users."""
    # Ensure database schema is initialized (only for SQLite)
    if not USE_FIRESTORE:
        print("Ensuring database schema is initialized...")
        db.init_schema()
        print("Schema check complete.\n")
    
    # Get all users
    if USE_FIRESTORE:
        users = get_all_users()
        # Convert to list of dicts with user_id key
        users = [{"user_id": user["user_id"]} for user in users]
    else:
        users_query = "SELECT user_id FROM users"
        users = db.fetch_all(users_query)
    
    if not users:
        print("No users found in database.")
        return
    
    total_users = len(users)
    print(f"Found {total_users} users. Generating recommendations...")
    
    total_recommendations = 0
    
    for idx, user_row in enumerate(users, 1):
        user_id = user_row["user_id"]
        print(f"[{idx}/{total_users}] Generating recommendations for user {user_id}...")
        
        try:
            # Generate for 30d window
            recs_30d = generate_recommendations(user_id, "30d")
            
            # Generate for 180d window
            recs_180d = generate_recommendations(user_id, "180d")
            
            total_recs = len(recs_30d) + len(recs_180d)
            total_recommendations += total_recs
            
            print(f"  ✓ Generated {len(recs_30d)} recommendations (30d) and {len(recs_180d)} recommendations (180d)")
        except Exception as e:
            print(f"  ✗ Error generating recommendations: {e}")
            continue
    
    print(f"\nCompleted! Generated {total_recommendations} total recommendations for {total_users} users.")
    print(f"Average: {total_recommendations / total_users:.1f} recommendations per user")


if __name__ == "__main__":
    generate_all_recommendations()

