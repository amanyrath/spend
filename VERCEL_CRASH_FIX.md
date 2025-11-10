# Quick Fix: Vercel Python Process Crash (Exit Status 1)

## Problem
Your Vercel deployment shows `Python process exited with exit status: 1` with 500 errors on all endpoints.

## Root Cause
The `.vercelignore` file was excluding the entire `src/database/` directory, which prevented the required `src/database/firestore.py` module from being deployed. When the API tried to start, it couldn't import the Firestore module and crashed immediately.

## Solution Applied

### 1. Fixed `.vercelignore` 
Changed from excluding entire directory:
```
src/database/
```

To excluding only SQLite-specific file:
```
src/database/db.py
```

This ensures:
- `src/database/firestore.py` is included (required for Vercel)
- `src/database/__init__.py` is included (required for imports)
- Only SQLite code (`db.py`) is excluded

### 2. Verify Environment Variables

**Critical**: Ensure these are set in Vercel Dashboard:

#### `FIREBASE_SERVICE_ACCOUNT` (Required)
- Go to: https://console.firebase.google.com
- Navigate to: Project Settings > Service Accounts
- Click: "Generate New Private Key"
- Copy the entire JSON content
- In Vercel: Settings > Environment Variables
- Paste the JSON as a single-line string
- **Without this variable, the API will crash on startup**

#### `OPENAI_API_KEY` (Required for chat)
- Get from: https://platform.openai.com/api-keys
- Format: `sk-...`
- Add to Vercel: Settings > Environment Variables

## Deploy the Fix

```bash
git add .vercelignore VERCEL_DEPLOYMENT_FIX.md VERCEL_CRASH_FIX.md
git commit -m "fix: Include required Firestore module in Vercel deployment"
git push origin main
```

Vercel will automatically redeploy.

## Verify the Fix

After deployment completes:

1. Check deployment status in Vercel dashboard
2. Test the API:
   ```bash
   curl https://your-app.vercel.app/api/health
   ```
3. Check logs for any remaining errors

## Expected Result
- No more "Python process exited with exit status: 1" errors
- API endpoints return 200 status codes
- Health check returns successful response

## If Still Failing

Check Vercel deployment logs for:
1. Missing environment variables (FIREBASE_SERVICE_ACCOUNT)
2. Invalid Firebase credentials
3. Import errors for other modules
4. Function size exceeding 250 MB limit

## Additional Notes
- The `.vercelignore` change is minimal and low-risk
- Firestore module is ~2-3 KB, won't affect function size
- SQLite code (`db.py`) remains excluded as intended

