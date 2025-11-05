# Testing with Firebase Emulators

This guide explains how to test SpendSense using Firebase emulators with SQL/CSV data.

## Quick Start

**Good News:** The system automatically detects when Firebase emulator is running! Just start the emulator and everything will automatically use it.

### Option 1: Automated Script (Recommended)

Use the automated test script that handles everything:

```bash
# Test with SQLite data (default)
python test_with_emulators.py

# Test with CSV data (loads CSV into SQLite first, then pushes to emulator)
python test_with_emulators.py --data-source csv

# Start only backend (no frontend)
python test_with_emulators.py --no-frontend

# Start only frontend (assumes backend is already running)
python test_with_emulators.py --no-backend

# Skip loading data (use existing emulator data)
python test_with_emulators.py --skip-load
```

The script will:
1. ✅ Check prerequisites (Firebase CLI, Python)
2. ✅ Start Firebase emulator
3. ✅ Load data from SQLite or CSV into emulator
4. ✅ Start backend API (auto-detects emulator)
5. ✅ Start frontend (connected to backend API)

### Option 2: Manual Steps

If you prefer manual control:

#### Step 1: Start Firebase Emulator

```bash
firebase emulators:start
```

This starts:
- Firestore emulator on `localhost:8080`
- Emulator UI on `http://localhost:4000`

#### Step 2: Set Environment Variable

In a new terminal:

```bash
export FIRESTORE_EMULATOR_HOST=localhost:8080
export USE_FIREBASE_EMULATOR=true
```

#### Step 3: Load Data into Emulator

**Option A: From SQLite (if you have spendsense.db)**

```bash
python -m src.ingest.push_from_sqlite
```

**Option B: From CSV Files**

First load CSV into SQLite, then push to emulator:

```bash
# Load CSV into SQLite
python -m src.ingest.data_loader

# Push SQLite to emulator
python -m src.ingest.push_from_sqlite
```

#### Step 4: Start Backend API

```bash
# Make sure FIRESTORE_EMULATOR_HOST is set
export FIRESTORE_EMULATOR_HOST=localhost:8080
uvicorn src.api.main:app --reload --port 8000
```

#### Step 5: Start Frontend

In another terminal:

```bash
cd consumer_ui
export VITE_API_URL=http://localhost:8000
npm run dev
```

## Accessing Services

Once everything is running:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Firebase Emulator UI**: http://localhost:4000

## Data Flow

```
CSV Files → SQLite → Firebase Emulator → Backend API → Frontend
         (optional)    (localhost:8080)   (localhost:8000)  (localhost:5173)
```

## Troubleshooting

### Emulator won't start

- Check if Firebase CLI is installed: `firebase --version`
- Check if `firebase.json` exists
- Try: `firebase emulators:start --only firestore`

### Backend can't connect to emulator

- The system auto-detects emulator on `localhost:8080` - just make sure emulator is running
- Check emulator is running: visit http://localhost:4000
- Restart backend after starting emulator
- If auto-detection fails, manually set: `export FIRESTORE_EMULATOR_HOST=localhost:8080`

### Frontend can't connect to backend

- Check backend is running: visit http://localhost:8000/docs
- Ensure `VITE_API_URL=http://localhost:8000` is set
- Check browser console for CORS errors

### Data not loading

- Verify SQLite database exists: `ls -lh data/spendsense.db`
- Verify CSV files exist: `ls -lh data/*.csv`
- Check emulator UI: http://localhost:4000 (should show collections)

## Verifying Data in Emulator

1. Open Firebase Emulator UI: http://localhost:4000
2. Click on "Firestore" tab
3. You should see collections:
   - `users`
   - `accounts`
   - `transactions`
   - `features` (if computed)
   - `personas` (if computed)
   - `recommendations` (if computed)

## Resetting Emulator Data

Simply restart the emulator:

```bash
# Stop emulator (Ctrl+C)
# Then start again
firebase emulators:start
```

Or use the automated script:

```bash
python test_with_emulators.py --skip-load  # Won't load data
```

## Next Steps

After setting up emulators:

1. **Compute Features**: Run feature computation
   ```bash
   export FIRESTORE_EMULATOR_HOST=localhost:8080
   python src/features/compute_all_vectorized.py
   ```

2. **Assign Personas**: Run persona assignment
   ```bash
   export FIRESTORE_EMULATOR_HOST=localhost:8080
   python src/personas/assign_all.py
   ```

3. **Generate Recommendations**: Run recommendation generation
   ```bash
   export FIRESTORE_EMULATOR_HOST=localhost:8080
   python src/recommend/generate_all.py
   ```

4. **View in Frontend**: Open http://localhost:5173/user_001/overview

## Environment Variables Reference

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `FIRESTORE_EMULATOR_HOST` | Firestore emulator host | Auto-detected if emulator running on port 8080 | No* |
| `USE_FIREBASE_EMULATOR` | Explicitly enable emulator mode | Auto-detected | No* |
| `VITE_API_URL` | Frontend API URL | `http://localhost:8000` | No |

\* The system automatically detects if Firebase emulator is running on `localhost:8080`. You only need to set these if using a custom port or to override auto-detection.

## Benefits of Using Emulators

✅ **No credentials needed** - Test Firebase features locally  
✅ **Fast iteration** - No network latency  
✅ **Safe testing** - Won't affect production data  
✅ **Visual debugging** - Emulator UI shows all data  
✅ **Easy reset** - Restart emulator to clear data  

