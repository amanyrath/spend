"""Run API server with SQLite - bypassing .env file settings"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variables BEFORE any imports
os.environ['USE_SQLITE'] = 'true'
# Remove problematic env vars that might be in .env
os.environ.pop('FIRESTORE_EMULATOR_HOST', None)
os.environ.pop('GOOGLE_APPLICATION_CREDENTIALS', None)

print("=" * 60)
print("STARTING API WITH LOCAL SQLITE")
print("=" * 60)
print("Database: SQLite (data/spendsense.db)")
print("API URL: http://localhost:8000")
print(f"USE_SQLITE={os.getenv('USE_SQLITE')}")
print("=" * 60)
print()

# Import the app directly (not as a string) so our env vars are preserved
from src.api.main import app, USE_FIRESTORE
print(f"DEBUG: USE_FIRESTORE={USE_FIRESTORE}")
print()

# Now run uvicorn
import uvicorn

if __name__ == "__main__":
    # Pass the app object directly, not as a string
    uvicorn.run(app, host="0.0.0.0", port=8000)

