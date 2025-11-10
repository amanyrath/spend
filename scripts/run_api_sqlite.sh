#!/bin/bash
# Run the API server with SQLite for local testing

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Force SQLite mode by completely bypassing .env file
# We'll set environment variables manually to override .env
export USE_SQLITE=true
export FIRESTORE_EMULATOR_HOST=""
export USE_FIREBASE_EMULATOR=false
export GOOGLE_APPLICATION_CREDENTIALS=""

echo "============================================================"
echo "STARTING API WITH LOCAL SQLITE"
echo "============================================================"
echo "Database: SQLite (data/spendsense.db)"
echo "API URL: http://localhost:8000"
echo "Environment:"
echo "  USE_SQLITE=$USE_SQLITE"
echo "  FIRESTORE_EMULATOR_HOST=$FIRESTORE_EMULATOR_HOST"
echo "============================================================"
echo ""

# Start the API (don't use --reload to avoid .env being reloaded)
python -c "import os; os.environ['USE_SQLITE']='true'; os.environ.pop('FIRESTORE_EMULATOR_HOST', None); os.environ.pop('GOOGLE_APPLICATION_CREDENTIALS', None); exec(open('run_uvicorn.py').read())" 2>/dev/null || \
uvicorn src.api.main:app --port 8000

