"""Script to assign personas to all users.

This script loops through all users in the database and assigns
personas for both 30d and 180d time windows.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import db
from src.personas.assignment import assign_persona

# Check if using Firestore (emulator or production)
USE_FIRESTORE = (
    os.getenv('FIRESTORE_EMULATOR_HOST') is not None or 
    os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true' or
    os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None or 
    os.path.exists('firebase-service-account.json')
)

if USE_FIRESTORE:
    from src.database.firestore import get_all_users


def assign_all_users():
    """Assign personas to all users."""
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
    print(f"Found {total_users} users. Assigning personas...")
    
    persona_counts = {}
    
    for idx, user_row in enumerate(users, 1):
        user_id = user_row["user_id"]
        print(f"[{idx}/{total_users}] Assigning persona for user {user_id}...")
        
        try:
            # Assign for 30d window
            persona_30d = assign_persona(user_id, "30d")
            
            # Assign for 180d window
            persona_180d = assign_persona(user_id, "180d")
            
            # Track persona distribution
            persona_counts[persona_30d] = persona_counts.get(persona_30d, 0) + 1
            
            print(f"  ✓ 30d: {persona_30d}, 180d: {persona_180d}")
        except Exception as e:
            print(f"  ✗ Error assigning persona: {e}")
            continue
    
    print(f"\nCompleted! Assigned personas for {total_users} users.")
    print("\nPersona distribution (30d window):")
    for persona, count in sorted(persona_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {persona}: {count}")


if __name__ == "__main__":
    assign_all_users()

