# SpendSense - Deployment Guide

**Deployment Stack:** Firebase + Vercel  
**Estimated Time:** 4-6 hours  
**Cost:** Free tier available for MVP

---

## Overview

This guide adds deployment to the simplified SpendSense project. You can deploy after completing core development or deploy incrementally as you build.

### Architecture

```
Frontend (Operator UI)
    ↓
Vercel (Static Hosting)
    ↓
Backend API (FastAPI)
    ↓
Vercel Serverless Functions
    ↓
Firebase Firestore (Database)
```

**Key Changes from Local Version:**
- SQLite → Firebase Firestore
- Local files → Cloud database
- `localhost` → Production URLs

---

## Prerequisites

- [ ] Completed core development (data generation, features, recommendations)
- [ ] Google account (for Firebase)
- [ ] GitHub account (for Vercel)
- [ ] Project pushed to GitHub repository

---

## Phase 1: Firebase Setup (1-2 hours)

### Step 1.1: Create Firebase Project

- [ ] **Task 1.1.1:** Go to [Firebase Console](https://console.firebase.google.com/)
- [ ] **Task 1.1.2:** Click "Add project"
- [ ] **Task 1.1.3:** Enter project name: `spendsense-mvp`
- [ ] **Task 1.1.4:** Disable Google Analytics (not needed for MVP)
- [ ] **Task 1.1.5:** Click "Create project"
- [ ] **Output:** Firebase project created

### Step 1.2: Set Up Firestore Database

- [ ] **Task 1.2.1:** In Firebase Console, click "Firestore Database"
- [ ] **Task 1.2.2:** Click "Create database"
- [ ] **Task 1.2.3:** Choose "Start in production mode"
- [ ] **Task 1.2.4:** Select location: `us-central1` (or nearest region)
- [ ] **Task 1.2.5:** Click "Enable"
- [ ] **Output:** Firestore database created

### Step 1.3: Configure Firestore Security Rules

- [ ] **Task 1.3.1:** Go to Firestore → Rules tab
- [ ] **Task 1.3.2:** Replace with:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow all reads/writes for MVP (no auth)
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```
- [ ] **Task 1.3.3:** Click "Publish"
- [ ] **⚠️ Warning:** This is insecure - only for demo/MVP
- [ ] **Output:** Firestore accessible publicly

### Step 1.4: Get Firebase Credentials

- [ ] **Task 1.4.1:** Go to Project Settings (gear icon)
- [ ] **Task 1.4.2:** Scroll to "Your apps" section
- [ ] **Task 1.4.3:** Click web icon (`</>`) to add web app
- [ ] **Task 1.4.4:** Register app name: `SpendSense Operator UI`
- [ ] **Task 1.4.5:** Copy Firebase config:
```javascript
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "spendsense-mvp.firebaseapp.com",
  projectId: "spendsense-mvp",
  storageBucket: "spendsense-mvp.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```
- [ ] **Task 1.4.6:** Save to `.env.local` (frontend) and `.env` (backend)
- [ ] **Output:** Firebase credentials saved

### Step 1.5: Get Service Account Key (Backend)

- [ ] **Task 1.5.1:** Go to Project Settings → Service Accounts
- [ ] **Task 1.5.2:** Click "Generate new private key"
- [ ] **Task 1.5.3:** Click "Generate key"
- [ ] **Task 1.5.4:** Download JSON file
- [ ] **Task 1.5.5:** Rename to `firebase-service-account.json`
- [ ] **Task 1.5.6:** Add to `.gitignore`: `firebase-service-account.json`
- [ ] **⚠️ Warning:** Never commit this file
- [ ] **Output:** Service account key downloaded

---

## Phase 2: Adapt Code for Firestore (2-3 hours)

### Step 2.1: Install Firebase SDKs

- [ ] **Task 2.1.1:** Backend - Add to `requirements.txt`:
```
firebase-admin==6.2.0
```
- [ ] **Task 2.1.2:** Install: `pip install firebase-admin`
- [ ] **Task 2.1.3:** Frontend - Install Firebase SDK:
```bash
cd operator_ui
npm install firebase
```
- [ ] **Output:** Firebase SDKs installed

### Step 2.2: Create Firestore Adapter (Backend)

- [ ] **Task 2.2.1:** Create file: `src/database/firestore.py`
```python
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin
cred = credentials.Certificate('firebase-service-account.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def get_collection(collection_name):
    """Get Firestore collection reference"""
    return db.collection(collection_name)

def store_user(user_data):
    """Store user in Firestore"""
    user_ref = db.collection('users').document(user_data['user_id'])
    user_ref.set(user_data)
    return user_data['user_id']

def store_feature(user_id, signal_type, signal_data, time_window):
    """Store computed feature"""
    feature_ref = db.collection('users').document(user_id)\
                    .collection('computed_features').document()
    feature_ref.set({
        'signal_type': signal_type,
        'signal_data': signal_data,
        'time_window': time_window,
        'computed_at': firestore.SERVER_TIMESTAMP
    })

def get_user_features(user_id, time_window=None):
    """Get user's computed features"""
    features_ref = db.collection('users').document(user_id)\
                     .collection('computed_features')
    
    if time_window:
        features_ref = features_ref.where('time_window', '==', time_window)
    
    return [doc.to_dict() for doc in features_ref.stream()]

def store_persona(user_id, persona_data):
    """Store persona assignment"""
    persona_ref = db.collection('users').document(user_id)\
                    .collection('persona_assignments').document()
    persona_ref.set(persona_data)

def store_recommendation(user_id, recommendation_data):
    """Store recommendation"""
    rec_ref = db.collection('users').document(user_id)\
                .collection('recommendations').document()
    rec_ref.set(recommendation_data)
    return rec_ref.id

def get_all_users():
    """Get all users"""
    users_ref = db.collection('users')
    return [{'user_id': doc.id, **doc.to_dict()} for doc in users_ref.stream()]

def get_user(user_id):
    """Get single user"""
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        return {'user_id': user_id, **user_doc.to_dict()}
    return None
```
- [ ] **Output:** Firestore adapter created

### Step 2.3: Update Data Loader for Firestore

- [ ] **Task 2.3.1:** Update `src/ingest/data_loader.py`:
```python
from src.database.firestore import store_user, db
import json
import pandas as pd

def load_users_to_firestore():
    """Load users from JSON to Firestore"""
    with open('data/users.json', 'r') as f:
        users = json.load(f)
    
    for user in users:
        store_user(user)
        print(f"Loaded user: {user['user_id']}")

def load_accounts_to_firestore():
    """Load accounts from CSV to Firestore"""
    accounts_df = pd.read_csv('data/accounts.csv')
    
    for _, account in accounts_df.iterrows():
        user_id = account['user_id']
        account_data = account.to_dict()
        
        db.collection('users').document(user_id)\
          .collection('accounts').document(account['account_id'])\
          .set(account_data)
        
        print(f"Loaded account: {account['account_id']}")

def load_transactions_to_firestore():
    """Load transactions from CSV to Firestore"""
    transactions_df = pd.read_csv('data/transactions.csv')
    
    # Batch write for efficiency (max 500 per batch)
    batch = db.batch()
    count = 0
    
    for _, txn in transactions_df.iterrows():
        user_id = txn['user_id']
        txn_data = txn.to_dict()
        
        txn_ref = db.collection('users').document(user_id)\
                    .collection('transactions').document(txn['transaction_id'])
        batch.set(txn_ref, txn_data)
        count += 1
        
        # Commit batch every 500 operations
        if count % 500 == 0:
            batch.commit()
            batch = db.batch()
            print(f"Loaded {count} transactions...")
    
    # Commit remaining
    batch.commit()
    print(f"Total transactions loaded: {count}")

if __name__ == '__main__':
    print("Loading users...")
    load_users_to_firestore()
    
    print("Loading accounts...")
    load_accounts_to_firestore()
    
    print("Loading transactions...")
    load_transactions_to_firestore()
    
    print("Data loading complete!")
```
- [ ] **Output:** Data loader updated

### Step 2.4: Update Feature Detection for Firestore

- [ ] **Task 2.4.1:** Update `src/features/signal_detection.py` to use Firestore:
```python
from src.database.firestore import db, get_user_features, store_feature

def get_user_transactions(user_id, days=90):
    """Get transactions from Firestore"""
    transactions_ref = db.collection('users').document(user_id)\
                         .collection('transactions')
    
    # Get transactions (Firestore doesn't have direct date filtering without index)
    transactions = [doc.to_dict() for doc in transactions_ref.stream()]
    
    # Filter in Python (or create Firestore index for date queries)
    # ... existing logic
    
    return transactions

# Update all detection functions to use Firestore queries
```
- [ ] **Output:** Feature detection updated

### Step 2.5: Update API Endpoints for Firestore

- [ ] **Task 2.5.1:** Update `src/api/main.py`:
```python
from fastapi import FastAPI, HTTPException
from src.database.firestore import get_all_users, get_user, get_user_features, db

app = FastAPI()

@app.get("/api/users")
def list_users():
    """List all users"""
    users = get_all_users()
    
    # Enrich with persona data
    for user in users:
        persona_ref = db.collection('users').document(user['user_id'])\
                        .collection('persona_assignments')\
                        .order_by('assigned_at', direction='DESCENDING')\
                        .limit(1)
        personas = list(persona_ref.stream())
        if personas:
            user['persona_30d'] = personas[0].to_dict().get('persona')
    
    return {"users": users}

@app.get("/api/users/{user_id}")
def get_user_detail(user_id: str):
    """Get user details"""
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get persona assignments
    personas_ref = db.collection('users').document(user_id)\
                     .collection('persona_assignments')\
                     .order_by('assigned_at', direction='DESCENDING')
    personas = [doc.to_dict() for doc in personas_ref.stream()]
    
    user['personas'] = personas
    return user

@app.get("/api/users/{user_id}/signals")
def get_user_signals(user_id: str):
    """Get user's behavioral signals"""
    features = get_user_features(user_id)
    return {"signals": features}

@app.get("/api/users/{user_id}/recommendations")
def get_user_recommendations(user_id: str):
    """Get user's recommendations"""
    recs_ref = db.collection('users').document(user_id)\
                 .collection('recommendations')
    recommendations = [doc.to_dict() for doc in recs_ref.stream()]
    return {"recommendations": recommendations}
```
- [ ] **Output:** API updated for Firestore

---

## Phase 3: Vercel Backend Deployment (1 hour)

### Step 3.1: Prepare Backend for Vercel

- [ ] **Task 3.1.1:** Create `vercel.json` in project root:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "src/api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "src/api/main.py"
    }
  ],
  "env": {
    "FIREBASE_PROJECT_ID": "@firebase_project_id"
  }
}
```
- [ ] **Output:** Vercel config created

- [ ] **Task 3.1.2:** Create `requirements.txt` in root (if not exists):
```
fastapi==0.104.1
uvicorn==0.24.0
firebase-admin==6.2.0
pandas==2.1.3
pydantic==2.5.0
```

- [ ] **Task 3.1.3:** Update imports in `src/api/main.py`:
```python
# Change relative imports to absolute
from src.database.firestore import get_all_users, get_user
```

- [ ] **Task 3.1.4:** Create `api/index.py` (Vercel entry point):
```python
from src.api.main import app

# Vercel expects 'app' or handler in api/ folder
handler = app
```

### Step 3.2: Deploy Backend to Vercel

- [ ] **Task 3.2.1:** Install Vercel CLI:
```bash
npm install -g vercel
```

- [ ] **Task 3.2.2:** Login to Vercel:
```bash
vercel login
```

- [ ] **Task 3.2.3:** Link project:
```bash
vercel link
```
- Follow prompts to create new project or link existing

- [ ] **Task 3.2.4:** Add Firebase service account as secret:
```bash
# Method 1: Via Vercel Dashboard
# Go to Project Settings → Environment Variables
# Add: FIREBASE_SERVICE_ACCOUNT = <paste entire JSON as string>

# Method 2: Via CLI
vercel env add FIREBASE_SERVICE_ACCOUNT production
# Paste the entire JSON content
```

- [ ] **Task 3.2.5:** Deploy:
```bash
vercel --prod
```

- [ ] **Task 3.2.6:** Note deployment URL: `https://spendsense-mvp.vercel.app`

- [ ] **Output:** Backend API deployed ✅

### Step 3.3: Test Backend API

- [ ] **Task 3.3.1:** Test health endpoint:
```bash
curl https://spendsense-mvp.vercel.app/api/health
```

- [ ] **Task 3.3.2:** Test users endpoint:
```bash
curl https://spendsense-mvp.vercel.app/api/users
```

- [ ] **Task 3.3.3:** Fix any errors (check Vercel logs)

- [ ] **Output:** API working in production

---

## Phase 4: Frontend Deployment (1 hour)

### Step 4.1: Update Frontend for Production

- [ ] **Task 4.1.1:** Update `operator_ui/.env.production`:
```
VITE_API_URL=https://spendsense-mvp.vercel.app
VITE_FIREBASE_API_KEY=AIza...
VITE_FIREBASE_AUTH_DOMAIN=spendsense-mvp.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=spendsense-mvp
VITE_FIREBASE_STORAGE_BUCKET=spendsense-mvp.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abc123
```

- [ ] **Task 4.1.2:** Update API calls to use environment variable:
```javascript
// src/api/client.js
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchUsers() {
  const response = await fetch(`${API_URL}/api/users`);
  return response.json();
}
```

- [ ] **Task 4.1.3:** Initialize Firebase in frontend (if using Firestore directly):
```javascript
// src/firebase.js
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
```

### Step 4.2: Deploy Frontend to Vercel

- [ ] **Task 4.2.1:** Push to GitHub (if not already):
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

- [ ] **Task 4.2.2:** Go to [Vercel Dashboard](https://vercel.com/dashboard)

- [ ] **Task 4.2.3:** Click "Add New Project"

- [ ] **Task 4.2.4:** Import from GitHub → Select your repository

- [ ] **Task 4.2.5:** Configure project:
- Framework Preset: Vite
- Root Directory: `operator_ui`
- Build Command: `npm run build`
- Output Directory: `dist`

- [ ] **Task 4.2.6:** Add environment variables:
- Click "Environment Variables"
- Add all `VITE_*` variables from `.env.production`

- [ ] **Task 4.2.7:** Click "Deploy"

- [ ] **Task 4.2.8:** Wait for deployment (~2 minutes)

- [ ] **Task 4.2.9:** Note frontend URL: `https://spendsense-operator-ui.vercel.app`

- [ ] **Output:** Frontend deployed ✅

### Step 4.3: Test Full Application

- [ ] **Task 4.3.1:** Visit frontend URL
- [ ] **Task 4.3.2:** Verify user list loads
- [ ] **Task 4.3.3:** Click into user detail
- [ ] **Task 4.3.4:** Verify signals display
- [ ] **Task 4.3.5:** Verify recommendations display
- [ ] **Task 4.3.6:** Check decision trace viewer

- [ ] **Output:** Full app working! 🎉

---

## Phase 5: Load Production Data (30 min)

### Step 5.1: Run Data Pipeline Against Firestore

- [ ] **Task 5.1.1:** Update environment to use Firebase service account locally:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="./firebase-service-account.json"
```

- [ ] **Task 5.1.2:** Run data loader:
```bash
python src/ingest/data_loader.py
```

- [ ] **Task 5.1.3:** Verify data in Firebase Console:
- Go to Firestore Database
- Check `users` collection has documents

- [ ] **Task 5.1.4:** Run feature computation:
```bash
python src/features/compute_all.py
```

- [ ] **Task 5.1.5:** Run persona assignment:
```bash
python src/personas/assign_all.py
```

- [ ] **Task 5.1.6:** Run recommendation generation:
```bash
python src/recommend/generate_all.py
```

- [ ] **Task 5.1.7:** Verify in Firebase Console:
- Check `users/{userId}/computed_features` subcollection
- Check `users/{userId}/recommendations` subcollection

- [ ] **Output:** Production data loaded ✅

---

## Phase 6: Configure CORS & Security (30 min)

### Step 6.1: Update CORS in Backend

- [ ] **Task 6.1.1:** Update `src/api/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow your Vercel frontend domain
origins = [
    "https://spendsense-operator-ui.vercel.app",
    "http://localhost:5173",  # Local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Task 6.1.2:** Redeploy backend:
```bash
vercel --prod
```

### Step 6.2: Update Firestore Security Rules (Optional)

For demo purposes, keep open. For production, add rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read: if true;  // Public read for demo
      allow write: if false;  // No writes from client
      
      match /{document=**} {
        allow read: if true;
        allow write: if false;
      }
    }
  }
}
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Core development complete
- [ ] Local testing passed
- [ ] Code pushed to GitHub
- [ ] Environment variables documented

### Firebase Setup
- [ ] Firebase project created
- [ ] Firestore database enabled
- [ ] Security rules configured
- [ ] Service account key downloaded
- [ ] Firebase credentials saved

### Code Adaptation
- [ ] Firebase SDKs installed
- [ ] Firestore adapter created
- [ ] SQLite code migrated to Firestore
- [ ] API endpoints updated
- [ ] Frontend API calls updated

### Backend Deployment
- [ ] Vercel config created
- [ ] Requirements.txt updated
- [ ] Service account added to Vercel secrets
- [ ] Backend deployed to Vercel
- [ ] API endpoints tested

### Frontend Deployment
- [ ] Environment variables configured
- [ ] Frontend connected to GitHub
- [ ] Frontend deployed to Vercel
- [ ] Frontend tested end-to-end

### Data Loading
- [ ] Data loaded to Firestore
- [ ] Features computed
- [ ] Personas assigned
- [ ] Recommendations generated

### Final Testing
- [ ] User list loads
- [ ] User detail displays
- [ ] Signals visible
- [ ] Recommendations visible
- [ ] Decision traces work
- [ ] No CORS errors
- [ ] Mobile responsive (optional)

---

## Troubleshooting

### Common Issues

**1. "Module not found" errors on Vercel**
- Check `requirements.txt` has all dependencies
- Verify imports use absolute paths (`from src.api import...`)
- Check `vercel.json` paths are correct

**2. CORS errors**
- Verify frontend URL in CORS origins
- Check Vercel deployment URL matches
- Ensure `allow_credentials=True` if needed

**3. Firebase permission denied**
- Check Firestore security rules
- Verify service account key is correct
- Check `FIREBASE_SERVICE_ACCOUNT` environment variable

**4. Slow Firestore queries**
- Create composite indexes for common queries
- Use subcollections for user-scoped data
- Limit query results (`.limit(100)`)

**5. Vercel build fails**
- Check Python version (use 3.9-3.11)
- Verify all files committed to Git
- Check build logs in Vercel dashboard

---

## Cost Estimates (Free Tier)

### Firestore
- **Reads:** 50K/day free
- **Writes:** 20K/day free
- **Storage:** 1GB free
- **MVP Usage:** ~5K reads/day, 1K writes/day
- **Cost:** $0/month ✅

### Vercel
- **Bandwidth:** 100GB/month free
- **Serverless Function Executions:** 100GB-hours free
- **Build Minutes:** 6,000 minutes/month free
- **MVP Usage:** Well within free tier
- **Cost:** $0/month ✅

**Total Monthly Cost:** $0 for MVP 🎉

---

## Optional: Custom Domain

If you want a custom domain like `spendsense.yourdomain.com`:

1. Buy domain from Namecheap, Google Domains, etc.
2. In Vercel project settings → Domains
3. Add custom domain
4. Update DNS records (Vercel provides instructions)
5. Wait for DNS propagation (~24 hours)

---

## Deployment Timeline

| Phase | Time | Can Skip? |
|-------|------|-----------|
| Firebase Setup | 1-2 hours | No |
| Code Adaptation | 2-3 hours | No |
| Backend Deployment | 1 hour | No |
| Frontend Deployment | 1 hour | No |
| Data Loading | 30 min | No |
| Security Config | 30 min | Yes (for demo) |
| **Total** | **4-6 hours** | |

**Note:** If you're time-constrained for the assignment submission, you can skip deployment and just submit the local version. Deployment is impressive but not required.

---

## When to Deploy?

**Option 1: Deploy Early (Recommended)**
- Deploy basic API after Week 1
- Deploy frontend after Week 2
- Easier to debug incrementally

**Option 2: Deploy at End**
- Finish all local development first
- Deploy everything Week 3
- One-time effort, but riskier

**Option 3: Skip Deployment (Fastest)**
- Submit local version only
- Include "Future: Deploy to Vercel/Firebase" in docs
- Focus on core algorithms

---

**Ready to deploy? Start with Phase 1: Firebase Setup!**