# Running SpendSense Locally

## Prerequisites

1. Python 3.11+ installed
2. Node.js and npm installed

## Step 1: Start the Backend API

Open a terminal and run:

```bash
# Navigate to project root
cd /Users/alexismanyrath/Code/spend

# Activate virtual environment (if you have one)
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install Python dependencies (if not already installed)
pip install -r requirements.txt

# Start the FastAPI server
python -m uvicorn src.api.main:app --reload --port 8000
```

The API will be available at: `http://localhost:8000`

You can verify it's working by visiting: `http://localhost:8000/api/health`

## Step 2: Start the Consumer UI

Open a **new terminal** and run:

```bash
# Navigate to consumer_ui directory
cd /Users/alexismanyrath/Code/spend/consumer_ui

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The consumer UI will be available at: `http://localhost:5173`

## Step 3: Access the Application

1. Open your browser and go to: `http://localhost:5173`
2. The app will automatically redirect to `http://localhost:5173/user_001` (default user ID)
3. You should see the Education page with recommendations

## Environment Variables (Optional)

If you want to customize the API URL, create a `.env` file in `consumer_ui/`:

```bash
cd consumer_ui
echo "VITE_API_URL=http://localhost:8000" > .env
```

By default, the app uses `http://localhost:8000` if no environment variable is set.

## Troubleshooting

### API not connecting
- Make sure the backend API is running on port 8000
- Check browser console for CORS errors
- Verify the API URL in `consumer_ui/src/lib/api.ts`

### No data showing
- Make sure you have data in your database
- Check that the user ID exists (default is `user_001`)
- Check browser network tab for API errors

### Port conflicts
- If port 8000 is taken, change the API port and update `VITE_API_URL`
- If port 5173 is taken, Vite will automatically use the next available port

## Quick Start Commands

**Terminal 1 (Backend):**
```bash
cd /Users/alexismanyrath/Code/spend
python -m uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd /Users/alexismanyrath/Code/spend/consumer_ui
npm run dev
```

Then open: `http://localhost:5173`

