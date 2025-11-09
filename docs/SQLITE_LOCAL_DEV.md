# Using SQLite for Local Development

To force your application to use SQLite instead of Firebase (even if the Firebase emulator is running), set the `USE_SQLITE` environment variable:

## Quick Start

### Option 1: Set environment variable in your shell
```bash
export USE_SQLITE=true
uvicorn src.api.main:app --reload
```

### Option 2: Set it inline when running commands
```bash
USE_SQLITE=true uvicorn src.api.main:app --reload
```

### Option 3: Create a `.env` file (if using python-dotenv)
```bash
echo "USE_SQLITE=true" > .env
```

## What This Does

When `USE_SQLITE=true` is set:
- ✅ Forces SQLite usage (takes precedence over Firebase emulator auto-detection)
- ✅ Prevents Firebase initialization
- ✅ Uses `data/spendsense.db` for all data
- ✅ Faster and simpler for local development

## Verify It's Working

Check the API health endpoint:
```bash
curl http://localhost:8000/health
```

The response should show:
```json
{
  "database": {
    "type": "sqlite",
    ...
  }
}
```

## Running Scripts with SQLite

All scripts will automatically use SQLite when `USE_SQLITE=true`:
```bash
USE_SQLITE=true python scripts/run_etl.py
USE_SQLITE=true python -m src.features.compute_all_vectorized
```

## Notes

- The Firebase emulator can still be running - it will just be ignored
- No need to stop the emulator or remove Firebase credentials
- SQLite data is stored in `data/spendsense.db`
- This only affects local development - production still uses Firebase



