# Vercel Deployment Fix: Serverless Function Size Optimization

## Problem
The SpendSense API serverless function exceeded Vercel's 250 MB unzipped size limit due to heavy Python dependencies like pandas (100+ MB) and guardrails-ai (40+ MB).

## Solution
We've optimized the deployment by:
1. Creating a minimal requirements file specifically for Vercel
2. Making heavy dependencies optional with graceful fallbacks
3. Configuring build settings to exclude unnecessary files
4. Updating code to handle missing optional dependencies

## Changes Made

### 1. Swapped Requirements Files
**Files:**
- `requirements.txt` - Now contains minimal production dependencies (for Vercel)
- `requirements-full.txt` - Contains all dependencies (for local development)

The production `requirements.txt` includes only essential dependencies:
- FastAPI, Uvicorn, Pydantic (API framework)
- Firebase Admin, PyJWT (authentication & database)
- OpenAI (chat functionality)

Excluded (to reduce bundle size):
- pandas (100+ MB) - only used for batch operations, not required for API endpoints
- guardrails-ai (40+ MB) - made optional with fallback validation
- faker, pytest - development dependencies not needed in production

### 2. Updated `vercel.json`
- Configured function memory (1024 MB) and max duration (10s)
- Set max lambda size to 50 MB
- Vercel automatically uses `requirements.txt` for Python builds

### 3. Created `.vercelignore`
Excludes from deployment:
- Data files (CSV, DB files)
- Documentation
- Test files
- Node modules
- Frontend source files
- Development scripts

### 4. Made Dependencies Optional

#### `src/guardrails/guardrails_ai.py`
- Added try/except for guardrails import
- Implemented fallback validation using simple prohibited phrase checking
- Works without guardrails library, just with reduced toxic language detection

#### `src/personas/assignment.py`
- Made pandas/numpy imports optional
- Core `get_persona_assignment()` function doesn't use pandas
- Only batch `calculate_persona_scores_vectorized()` requires pandas (not used by API)

## Deployment Instructions

### Option 1: Deploy via Git Push (Recommended)
```bash
git add .
git commit -m "fix: Optimize serverless function for Vercel deployment"
git push origin main
```

Vercel will automatically redeploy using the new configuration.

### Option 2: Deploy via Vercel CLI
```bash
vercel --prod
```

## Testing After Deployment

1. **Health Check**
   ```bash
   curl https://your-app.vercel.app/api/health
   ```

2. **Test API Endpoints**
   ```bash
   # Get users
   curl https://your-app.vercel.app/api/users
   
   # Get user signals
   curl https://your-app.vercel.app/api/users/{user_id}/signals
   ```

3. **Check Function Size**
   - Go to Vercel Dashboard → Your Project → Deployments
   - Click on latest deployment
   - Check "Function Size" in the deployment details

## What Still Works

- All read-only API endpoints (users, signals, recommendations, transactions)
- User authentication and authorization
- Chat functionality with basic guardrails validation
- Persona assignment for individual users
- Credit utilization, subscription, savings, and income detection

## What Requires Pandas (Not Available in Serverless)

- Batch vectorized persona scoring (`calculate_persona_scores_vectorized`)
- Batch feature computation scripts
- Data analysis notebooks
- ETL scripts for data generation

These operations should be run locally or in a different environment, not via the serverless API.

## Monitoring

After deployment, monitor:
1. **Function execution time** - Should be under 10 seconds
2. **Memory usage** - Should be under 1024 MB
3. **Cold start time** - Reduced bundle size improves cold starts
4. **Error logs** - Check for any import errors related to missing dependencies

## Rollback Plan

If issues occur, you can rollback by:
1. Renaming `requirements.txt` to `requirements-minimal.txt`
2. Renaming `requirements-full.txt` back to `requirements.txt`
3. Redeploying

However, this will bring back the 250 MB size issue.

## Future Optimizations

Consider:
1. **Splitting API into multiple functions** - Separate chat endpoints from data endpoints
2. **Using Vercel Edge Functions** for lightweight operations
3. **Moving compute-intensive operations** to a separate service (AWS Lambda, Cloud Run)
4. **Caching compiled dependencies** to improve cold start times

## Environment Variables

**Required** - Ensure these are set in Vercel Dashboard (Settings > Environment Variables):

1. **`FIREBASE_SERVICE_ACCOUNT`** (Required)
   - Firebase Admin SDK credentials as JSON string
   - Get from: Firebase Console > Project Settings > Service Accounts > Generate New Private Key
   - Format: Paste the entire JSON file contents as a single-line string
   - Example: `{"type":"service_account","project_id":"your-project",...}`
   - **Critical**: Without this, the API will crash on startup (Python process exit 1)

2. **`OPENAI_API_KEY`** (Required for chat)
   - OpenAI API key for chat functionality
   - Get from: https://platform.openai.com/api-keys
   - Format: `sk-...`
   - Without this, chat endpoints will fail but other endpoints will work

**How to Set in Vercel:**
1. Go to your Vercel project dashboard
2. Click Settings > Environment Variables
3. Add each variable for Production, Preview, and Development environments
4. Redeploy after adding variables

## Notes

- `requirements.txt` is now minimal for production deployment (Vercel uses this automatically)
- `requirements-full.txt` has all dependencies for local development
- For local development, run: `pip install -r requirements-full.txt`
- The serverless function will have limited computational capacity
- For data processing operations, use local environment or dedicated compute service
- Guardrails validation still works but without advanced toxic language detection

