# Firebase Emulator Setup Guide

## Quick Start

### 1. Install Firebase CLI (if not already installed)

```bash
npm install -g firebase-tools
```

### 2. Login to Firebase (optional, only needed for production)

```bash
firebase login
```

### 3. Start the Emulator

```bash
# Start Firestore emulator
firebase emulators:start --only firestore

# Or start emulator with UI (recommended)
firebase emulators:start
```

This will start:
- Firestore emulator on `localhost:8080`
- Emulator UI on `http://localhost:4000`

### 4. Run Your Scripts

**Good News:** The system automatically detects when Firebase emulator is running on `localhost:8080`! No environment variables needed.

Just start the emulator and run your scripts:

```bash
# In terminal 1: Start emulator
firebase emulators:start

# In terminal 2: Run your scripts (auto-detects emulator)
python src/features/compute_all.py
uvicorn src.api.main:app --reload
```

The system will automatically detect the emulator and use it instead of SQLite or production Firebase.

**Note:** If you want to explicitly set the emulator host (e.g., custom port), you can still set:
```bash
export FIRESTORE_EMULATOR_HOST=localhost:8080
```

## Benefits

- ✅ Same API as production Firebase
- ✅ No credentials needed locally
- ✅ Data persists in emulator (until you restart)
- ✅ Easy to reset/clear data
- ✅ Visual UI at http://localhost:4000

## Switching Between Modes

- **Emulator**: Auto-detected when running on `localhost:8080` (or set `FIRESTORE_EMULATOR_HOST=localhost:8080`)
- **Production**: Set `FIREBASE_SERVICE_ACCOUNT` or have `firebase-service-account.json`
- **SQLite** (fallback): When no emulator detected and no Firebase credentials (defaults to SQLite)

**Priority Order:**
1. If `FIRESTORE_EMULATOR_HOST` is set → Use emulator
2. If emulator detected on port 8080 → Use emulator (auto-detected)
3. If `FIREBASE_SERVICE_ACCOUNT` or `firebase-service-account.json` exists → Use production Firebase
4. Otherwise → Use SQLite

## Clearing Emulator Data

The emulator stores data in memory by default. To persist data, add to `firebase.json`:

```json
{
  "emulators": {
    "firestore": {
      "port": 8080,
      "host": "localhost"
    }
  }
}
```

Data will be stored in `.firebase/` directory.

