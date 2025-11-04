"""FastAPI application for SpendSense API.

This module provides REST API endpoints for the SpendSense operator interface.
"""

import json
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional

from src.database import db
from src.personas.assignment import get_persona_assignment
from src.features.signal_detection import get_user_features

# Import Firestore functions for deployment
USE_FIRESTORE = os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None or os.path.exists('firebase-service-account.json')
if USE_FIRESTORE:
    from src.database.firestore import (
        get_all_users as firestore_get_all_users,
        get_user as firestore_get_user,
        get_persona_assignments as firestore_get_persona_assignments,
        get_recommendations as firestore_get_recommendations,
        db as firestore_db
    )
    from firebase_admin import firestore

app = FastAPI(
    title="SpendSense API",
    description="API for SpendSense financial education platform",
    version="1.0.0"
)

# Configure CORS
# Allow local development and common frontend ports, plus Vercel deployment
origins = [
    "https://spendsense-operator-ui.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/users")
def list_users():
    """List all users with their persona assignments and behavior counts"""
    try:
        if USE_FIRESTORE:
            # Use Firestore
            users = firestore_get_all_users()
            
            enriched_users = []
            for user in users:
                user_id = user['user_id']
                
                # Get persona assignment for 30d window
                persona_ref = firestore_db.collection('users').document(user_id)\
                                .collection('persona_assignments')\
                                .where('time_window', '==', '30d')\
                                .order_by('assigned_at', direction=firestore.Query.DESCENDING)\
                                .limit(1)
                personas = list(persona_ref.stream())
                persona_30d = personas[0].to_dict().get('persona') if personas else None
                
                # Count behaviors (computed features) for 30d window
                features_ref = firestore_db.collection('users').document(user_id)\
                                .collection('computed_features')\
                                .where('time_window', '==', '30d')
                behavior_count = len(list(features_ref.stream()))
                
                # Count recommendations
                recs_ref = firestore_db.collection('users').document(user_id)\
                            .collection('recommendations')
                recommendation_count = len(list(recs_ref.stream()))
                
                enriched_user = {
                    "user_id": user_id,
                    "name": user.get('name', 'Unknown'),
                    "persona_30d": persona_30d,
                    "behavior_count": behavior_count,
                    "recommendation_count": recommendation_count
                }
                enriched_users.append(enriched_user)
            
            return enriched_users
        else:
            # Use SQLite
            users_query = "SELECT user_id, name FROM users ORDER BY user_id"
            users = db.fetch_all(users_query)
            
            enriched_users = []
            for user_row in users:
                user_id = user_row["user_id"]
                
                # Get persona assignment for 30d window
                persona_query = """
                    SELECT persona
                    FROM persona_assignments
                    WHERE user_id = ? AND time_window = ?
                    ORDER BY assigned_at DESC
                    LIMIT 1
                """
                persona_row = db.fetch_one(persona_query, (user_id, "30d"))
                persona_30d = persona_row["persona"] if persona_row else None
                
                # Count behaviors (computed features) for 30d window
                behavior_query = """
                    SELECT COUNT(*) as count
                    FROM computed_features
                    WHERE user_id = ? AND time_window = ?
                """
                behavior_row = db.fetch_one(behavior_query, (user_id, "30d"))
                behavior_count = behavior_row["count"] if behavior_row else 0
                
                # Count recommendations
                rec_query = """
                    SELECT COUNT(*) as count
                    FROM recommendations
                    WHERE user_id = ?
                """
                rec_row = db.fetch_one(rec_query, (user_id,))
                recommendation_count = rec_row["count"] if rec_row else 0
                
                enriched_user = {
                    "user_id": user_id,
                    "name": user_row["name"],
                    "persona_30d": persona_30d,
                    "behavior_count": behavior_count,
                    "recommendation_count": recommendation_count
                }
                enriched_users.append(enriched_user)
            
            return enriched_users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


@app.get("/api/users/{user_id}")
def get_user_detail(user_id: str):
    """Get detailed user information including personas for both time windows"""
    try:
        if USE_FIRESTORE:
            # Use Firestore
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get persona assignments
            personas = firestore_get_persona_assignments(user_id)
            
            # Organize personas by time window
            personas_by_window = {}
            for persona in personas:
                window = persona.get('time_window', '30d')
                if window not in personas_by_window:
                    personas_by_window[window] = []
                personas_by_window[window].append(persona)
            
            # Get most recent persona for each window
            persona_30d = None
            persona_180d = None
            for window_personas in personas_by_window.get('30d', []):
                persona_30d = window_personas
            for window_personas in personas_by_window.get('180d', []):
                persona_180d = window_personas
            
            user_detail = {
                "user_id": user.get('user_id', user_id),
                "name": user.get('name', 'Unknown'),
                "created_at": user.get('created_at', ''),
                "personas": {
                    "30d": persona_30d,
                    "180d": persona_180d
                }
            }
            
            return user_detail
        else:
            # Use SQLite
            user_query = "SELECT user_id, name, created_at FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get persona assignments for both windows
            persona_30d = get_persona_assignment(user_id, "30d")
            persona_180d = get_persona_assignment(user_id, "180d")
            
            user_detail = {
                "user_id": user_row["user_id"],
                "name": user_row["name"],
                "created_at": user_row["created_at"],
                "personas": {
                    "30d": persona_30d,
                    "180d": persona_180d
                }
            }
            
            return user_detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


@app.get("/api/users/{user_id}/signals")
def get_user_signals(user_id: str, time_window: str = "30d"):
    """Get user's behavioral signals"""
    try:
        if USE_FIRESTORE:
            # Use Firestore - verify user exists
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get signals using existing function (which handles Firestore)
            signals = get_user_features(user_id, time_window)
            
            return {
                "user_id": user_id,
                "time_window": time_window,
                "signals": signals
            }
        else:
            # Use SQLite - verify user exists
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get signals using existing function
            signals = get_user_features(user_id, time_window)
            
            return {
                "user_id": user_id,
                "time_window": time_window,
                "signals": signals
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching signals: {str(e)}")


@app.get("/api/users/{user_id}/recommendations")
def get_user_recommendations(user_id: str, time_window: Optional[str] = None):
    """Get user's recommendations with decision traces"""
    try:
        if USE_FIRESTORE:
            # Use Firestore - verify user exists
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get recommendations from Firestore
            recommendations_list = firestore_get_recommendations(user_id)
            
            recommendations = []
            for rec in recommendations_list:
                # Parse decision_trace if it's a string
                decision_trace = rec.get('decision_trace')
                if isinstance(decision_trace, str):
                    try:
                        decision_trace = json.loads(decision_trace)
                    except json.JSONDecodeError:
                        decision_trace = {}
                
                recommendation = {
                    "recommendation_id": rec.get('recommendation_id', ''),
                    "user_id": rec.get('user_id', user_id),
                    "type": rec.get('type', ''),
                    "content_id": rec.get('content_id', ''),
                    "title": rec.get('title', ''),
                    "rationale": rec.get('rationale', ''),
                    "decision_trace": decision_trace,
                    "shown_at": rec.get('shown_at', '')
                }
                recommendations.append(recommendation)
            
            return {
                "user_id": user_id,
                "time_window": time_window,
                "recommendations": recommendations
            }
        else:
            # Use SQLite - verify user exists
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get recommendations from database
            rec_query = """
                SELECT recommendation_id, user_id, type, content_id, title, 
                       rationale, decision_trace, shown_at
                FROM recommendations
                WHERE user_id = ?
                ORDER BY shown_at DESC
            """
            rec_rows = db.fetch_all(rec_query, (user_id,))
            
            recommendations = []
            for row in rec_rows:
                # Parse decision_trace JSON
                decision_trace = None
                if row["decision_trace"]:
                    try:
                        decision_trace = json.loads(row["decision_trace"])
                    except json.JSONDecodeError:
                        decision_trace = {}
                
                recommendation = {
                    "recommendation_id": row["recommendation_id"],
                    "user_id": row["user_id"],
                    "type": row["type"],
                    "content_id": row["content_id"],
                    "title": row["title"],
                    "rationale": row["rationale"],
                    "decision_trace": decision_trace,
                    "shown_at": row["shown_at"]
                }
                recommendations.append(recommendation)
            
            return {
                "user_id": user_id,
                "time_window": time_window,
                "recommendations": recommendations
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
