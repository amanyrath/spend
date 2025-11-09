#!/usr/bin/env python3
"""
Script to create demo Firebase Auth accounts for SpendSense.

This script creates 3 demo accounts:
1. hannah@demo.com - Consumer (High Utilization persona)
2. sam@demo.com - Consumer (Subscription-Heavy persona)
3. operator@demo.com - Operator role

Usage:
    python scripts/create_demo_accounts.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from firebase_admin import auth, firestore
from src.database.firestore import initialize_firebase, get_db

# Demo accounts configuration
DEMO_ACCOUNTS = [
    {
        "email": "hannah@demo.com",
        "password": "demo123",
        "role": "consumer",
        "name": "Hannah Martinez",
        "user_id": "user_001"  # Map to existing synthetic user
    },
    {
        "email": "sam@demo.com",
        "password": "demo123",
        "role": "consumer",
        "name": "Sam Patel",
        "user_id": "user_002"  # Map to existing synthetic user
    },
    {
        "email": "operator@demo.com",
        "password": "demo123",
        "role": "operator",
        "name": "Operator User",
        "user_id": None  # Operators don't map to synthetic users
    }
]


def create_demo_accounts():
    """Create demo Firebase Auth accounts and store user data in Firestore."""
    
    print("=" * 60)
    print("CREATING DEMO FIREBASE AUTH ACCOUNTS")
    print("=" * 60)
    
    # Initialize Firebase
    initialize_firebase()
    db = get_db()
    
    if db is None:
        print("ERROR: Firebase not initialized. Make sure:")
        print("  1. firebase-service-account.json exists, OR")
        print("  2. FIREBASE_SERVICE_ACCOUNT environment variable is set, OR")
        print("  3. Firebase emulator is running")
        sys.exit(1)
    
    created_count = 0
    updated_count = 0
    
    for account in DEMO_ACCOUNTS:
        email = account["email"]
        password = account["password"]
        role = account["role"]
        name = account["name"]
        user_id = account["user_id"]
        
        try:
            # Try to create the user in Firebase Auth
            try:
                user = auth.create_user(
                    email=email,
                    password=password,
                    display_name=name
                )
                print(f"✓ Created Auth user: {email} (UID: {user.uid})")
                created_count += 1
            except auth.EmailAlreadyExistsError:
                # User already exists, get the UID
                user = auth.get_user_by_email(email)
                print(f"ℹ Auth user exists: {email} (UID: {user.uid})")
                # Update password in case it changed
                auth.update_user(user.uid, password=password)
                updated_count += 1
            
            # Store/update user data in Firestore
            user_data = {
                'email': email,
                'name': name,
                'role': role,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            # For consumers, link to synthetic user data
            if user_id:
                user_data['synthetic_user_id'] = user_id
            
            db.collection('users').document(user.uid).set(user_data, merge=True)
            print(f"  → Stored user data in Firestore (role: {role})")
            
            # Set custom claims for role-based access
            auth.set_custom_user_claims(user.uid, {'role': role})
            print(f"  → Set custom claims (role: {role})")
            
        except Exception as e:
            print(f"✗ Error creating {email}: {str(e)}")
            continue
    
    print()
    print("=" * 60)
    print(f"SUMMARY: Created {created_count}, Updated {updated_count}")
    print("=" * 60)
    print()
    print("Demo accounts:")
    print("  Consumer (High Utilization): hannah@demo.com / demo123")
    print("  Consumer (Subscription-Heavy): sam@demo.com / demo123")
    print("  Operator: operator@demo.com / demo123")
    print()
    print("Note: Consumer accounts are linked to existing synthetic users")
    print("      (user_001 and user_002) for transaction data.")
    print()


if __name__ == "__main__":
    create_demo_accounts()





