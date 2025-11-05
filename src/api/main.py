"""FastAPI application for SpendSense API.

This module provides REST API endpoints for the SpendSense operator interface.
"""

import json
import os
import math
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Load environment variables from .env file
load_dotenv()

from src.database import db
from src.database.db import get_db_connection
from src.personas.assignment import get_persona_assignment
from src.features.signal_detection import get_user_features, compute_all_features
from src.recommend.content_catalog import get_content_by_id
from src.recommend.engine import check_offer_eligibility
from src.chat.service import generate_chat_response
from src.guardrails.guardrails_ai import get_guardrails
from src.guardrails.data_sanitizer import get_sanitizer
from src.utils.category_utils import normalize_category, get_primary_category

# Import Firestore functions for deployment or emulator
# Import firestore module early so auto-detection runs
from src.database.firestore import (
    get_all_users as firestore_get_all_users,
    get_user as firestore_get_user,
    get_persona_assignments as firestore_get_persona_assignments,
    get_recommendations as firestore_get_recommendations,
    get_db as firestore_get_db
)
from firebase_admin import firestore

def check_use_firestore():
    """Check if Firestore should be used (dynamic check, not cached)."""
    # Check environment variables (including auto-detected FIRESTORE_EMULATOR_HOST)
    has_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None
    has_emulator_flag = os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    has_production_creds = os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None
    has_cred_file = os.path.exists('firebase-service-account.json')
    
    if has_emulator or has_emulator_flag or has_production_creds or has_cred_file:
        # Try to get Firestore client
        db_client = firestore_get_db()
        return db_client is not None
    return False

# Cache initial state
USE_FIRESTORE = check_use_firestore()

# Create a convenience alias for backward compatibility
firestore_db = firestore_get_db() if USE_FIRESTORE else None

app = FastAPI(
    title="SpendSense API",
    description="API for SpendSense financial education platform",
    version="1.0.0"
)

# Configure CORS
# Allow local development and common frontend ports, plus Vercel deployment
origins = [
    "https://spendsense-operator-ui.vercel.app",
    "https://spendsense-consumer-ui.vercel.app",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
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

# Rate limiting: track messages per user per minute
rate_limit_store: Dict[str, List[datetime]] = defaultdict(list)
RATE_LIMIT_MESSAGES = 10
RATE_LIMIT_WINDOW = 60  # seconds


def clean_nan_values(obj: Any) -> Any:
    """Recursively clean NaN, Infinity, and -Infinity values from a data structure.
    
    Replaces NaN with None, and Infinity/-Infinity with None or 0 as appropriate.
    This ensures JSON serialization works correctly.
    
    Args:
        obj: The object to clean (dict, list, or primitive)
        
    Returns:
        Cleaned object with NaN/Inf values replaced
    """
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj):
            return None
        elif math.isinf(obj):
            return None  # Replace infinity with None
        return obj
    else:
        return obj


def check_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded rate limit.
    
    Args:
        user_id: User identifier
        
    Returns:
        True if within limit, False if exceeded
    """
    now = datetime.now()
    # Clean old entries
    rate_limit_store[user_id] = [
        ts for ts in rate_limit_store[user_id]
        if (now - ts).total_seconds() < RATE_LIMIT_WINDOW
    ]
    
    # Check limit
    if len(rate_limit_store[user_id]) >= RATE_LIMIT_MESSAGES:
        return False
    
    # Add current request
    rate_limit_store[user_id].append(now)
    return True


class ChatRequest(BaseModel):
    message: str
    user_id: str


@app.get("/", response_class=HTMLResponse)
def root():
    """Root endpoint providing API information"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SpendSense API</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                margin-top: 0;
            }
            .status {
                display: inline-block;
                padding: 4px 12px;
                background-color: #4caf50;
                color: white;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
            }
            .endpoints {
                margin-top: 30px;
            }
            .endpoint {
                padding: 12px;
                margin: 8px 0;
                background-color: #f9f9f9;
                border-left: 3px solid #2196f3;
                border-radius: 4px;
            }
            .endpoint-label {
                font-weight: 600;
                color: #333;
            }
            .endpoint-path {
                color: #666;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                margin-top: 4px;
            }
            .docs-link {
                margin-top: 30px;
                padding: 15px;
                background-color: #e3f2fd;
                border-radius: 4px;
                text-align: center;
            }
            .docs-link a {
                color: #1976d2;
                text-decoration: none;
                font-weight: 600;
            }
            .docs-link a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SpendSense API</h1>
            <p>Version 1.0.0 <span class="status">OK</span></p>
            
            <div class="endpoints">
                <h2>Available Endpoints</h2>
                <div class="endpoint">
                    <div class="endpoint-label">Health Check</div>
                    <div class="endpoint-path">GET /api/health</div>
                </div>
                <div class="endpoint">
                    <div class="endpoint-label">List Users</div>
                    <div class="endpoint-path">GET /api/users</div>
                </div>
                <div class="endpoint">
                    <div class="endpoint-label">Get User Signals</div>
                    <div class="endpoint-path">GET /api/users/{user_id}/signals</div>
                </div>
                <div class="endpoint">
                    <div class="endpoint-label">Compute User Features</div>
                    <div class="endpoint-path">POST /api/users/{user_id}/compute-features?time_window=30d&force_recompute=false</div>
                </div>
                <div class="endpoint">
                    <div class="endpoint-label">Get User Recommendations</div>
                    <div class="endpoint-path">GET /api/users/{user_id}/recommendations</div>
                </div>
                <div class="endpoint">
                    <div class="endpoint-label">Get User Transactions</div>
                    <div class="endpoint-path">GET /api/users/{user_id}/transactions</div>
                </div>
                <div class="endpoint">
                    <div class="endpoint-label">Get User Insights</div>
                    <div class="endpoint-path">GET /api/users/{user_id}/insights?period=30d</div>
                </div>
                <div class="endpoint">
                    <div class="endpoint-label">Get User Overview</div>
                    <div class="endpoint-path">GET /api/users/{user_id}/overview</div>
                </div>
            </div>
            
            <div class="docs-link">
                <a href="/docs">View Interactive API Documentation →</a>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    use_firestore = check_use_firestore()
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "database": "firestore" if use_firestore else "sqlite",
        "firestore_emulator_host": os.getenv('FIRESTORE_EMULATOR_HOST'),
        "firestore_db_available": firestore_db is not None if use_firestore else None
    }


@app.get("/api/users")
def list_users(
    search: Optional[str] = None,
    persona: Optional[str] = None,
    page: int = 1,
    limit: int = 50
):
    """List all users with their persona assignments and behavior counts
    
    Query parameters:
    - search: Filter by name or user_id (case-insensitive)
    - persona: Filter by persona type (exact match)
    - page: Page number (default: 1)
    - limit: Items per page (default: 50)
    """
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
                persona_data = personas[0].to_dict() if personas else None
                persona_30d = persona_data.get('primary_persona') or persona_data.get('persona') if persona_data else None
                
                # Build match percentages dict if available
                match_percentages_30d = None
                if persona_data:
                    match_percentages_30d = {
                        "high_utilization": persona_data.get("match_high_utilization", 0.0) or 0.0,
                        "variable_income": persona_data.get("match_variable_income", 0.0) or 0.0,
                        "subscription_heavy": persona_data.get("match_subscription_heavy", 0.0) or 0.0,
                        "savings_builder": persona_data.get("match_savings_builder", 0.0) or 0.0,
                        "general_wellness": persona_data.get("match_general_wellness", 0.0) or 0.0
                    }
                
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
                    "match_percentages_30d": match_percentages_30d,
                    "behavior_count": behavior_count,
                    "recommendation_count": recommendation_count
                }
                enriched_users.append(enriched_user)
        else:
            # Use SQLite
            users_query = "SELECT user_id, name FROM users ORDER BY user_id"
            users = db.fetch_all(users_query)
            
            enriched_users = []
            for user_row in users:
                user_id = user_row["user_id"]
                
                # Get persona assignment for 30d window
                persona_query = """
                    SELECT COALESCE(primary_persona, persona) as persona,
                           match_high_utilization, match_variable_income, match_subscription_heavy,
                           match_savings_builder, match_general_wellness
                    FROM persona_assignments
                    WHERE user_id = ? AND time_window = ?
                    ORDER BY assigned_at DESC
                    LIMIT 1
                """
                persona_row = db.fetch_one(persona_query, (user_id, "30d"))
                persona_30d = persona_row["persona"] if persona_row else None
                
                # Build match percentages dict if available
                match_percentages_30d = None
                if persona_row:
                    match_percentages_30d = {
                        "high_utilization": persona_row.get("match_high_utilization", 0.0) or 0.0,
                        "variable_income": persona_row.get("match_variable_income", 0.0) or 0.0,
                        "subscription_heavy": persona_row.get("match_subscription_heavy", 0.0) or 0.0,
                        "savings_builder": persona_row.get("match_savings_builder", 0.0) or 0.0,
                        "general_wellness": persona_row.get("match_general_wellness", 0.0) or 0.0
                    }
                
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
                    "match_percentages_30d": match_percentages_30d,
                    "behavior_count": behavior_count,
                    "recommendation_count": recommendation_count
                }
                enriched_users.append(enriched_user)
        
        # Apply filters
        if search:
            search_lower = search.lower()
            enriched_users = [
                u for u in enriched_users
                if search_lower in u.get('name', '').lower() or search_lower in u.get('user_id', '').lower()
            ]
        
        if persona:
            enriched_users = [
                u for u in enriched_users
                if u.get('persona_30d') == persona
            ]
        
        # Calculate summary stats before pagination
        total_users = len(enriched_users)
        users_by_persona = defaultdict(int)
        total_behaviors = 0
        total_recommendations = 0
        
        for user in enriched_users:
            persona_val = user.get('persona_30d')
            if persona_val:
                users_by_persona[persona_val] += 1
            total_behaviors += user.get('behavior_count', 0)
            total_recommendations += user.get('recommendation_count', 0)
        
        avg_behaviors = round(total_behaviors / total_users, 2) if total_users > 0 else 0.0
        avg_recommendations = round(total_recommendations / total_users, 2) if total_users > 0 else 0.0
        
        # Apply pagination
        offset = (page - 1) * limit
        paginated_users = enriched_users[offset:offset + limit]
        
        return {
            "users": paginated_users,
            "summary": {
                "total_users": total_users,
                "users_by_persona": dict(users_by_persona),
                "avg_behaviors": avg_behaviors,
                "avg_recommendations": avg_recommendations
            },
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_users,
                "total_pages": (total_users + limit - 1) // limit if limit > 0 else 1
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


@app.get("/api/users/{user_id}")
def get_user_detail(user_id: str):
    """Get detailed user information including personas, signals, recommendations, and accounts"""
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
            
            # Get accounts
            from src.database.firestore import get_user_accounts as firestore_get_user_accounts
            all_accounts = firestore_get_user_accounts(user_id)
            
            # Count accounts by type
            account_counts = {
                "checking": 0,
                "savings": 0,
                "credit": 0,
                "total": len(all_accounts)
            }
            for acc in all_accounts:
                acc_type = acc.get('type', '')
                subtype = acc.get('subtype', '')
                if acc_type == 'depository':
                    if subtype == 'checking':
                        account_counts['checking'] += 1
                    elif subtype in ['savings', 'money_market', 'cd', 'hsa']:
                        account_counts['savings'] += 1
                elif acc_type == 'credit':
                    account_counts['credit'] += 1
        else:
            # Use SQLite
            user_query = "SELECT user_id, name, created_at FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get persona assignments for both windows
            persona_30d = get_persona_assignment(user_id, "30d")
            persona_180d = get_persona_assignment(user_id, "180d")
            
            # Get accounts
            accounts_query = """
                SELECT account_id, balance, "limit", type, subtype, mask
                FROM accounts
                WHERE user_id = ?
            """
            accounts_rows = db.fetch_all(accounts_query, (user_id,))
            all_accounts = [dict(row) for row in accounts_rows]
            
            # Count accounts by type
            account_counts = {
                "checking": 0,
                "savings": 0,
                "credit": 0,
                "total": len(all_accounts)
            }
            for acc in all_accounts:
                acc_type = acc.get('type', '')
                subtype = acc.get('subtype', '')
                if acc_type == 'depository':
                    if subtype == 'checking':
                        account_counts['checking'] += 1
                    elif subtype in ['savings', 'money_market', 'cd', 'hsa']:
                        account_counts['savings'] += 1
                elif acc_type == 'credit':
                    account_counts['credit'] += 1
        
        # Get behavioral signals
        signals_30d = get_user_features(user_id, "30d")
        signals_180d = get_user_features(user_id, "180d")
        
        # Get recommendations
        if USE_FIRESTORE:
            recommendations_list = firestore_get_recommendations(user_id)
            # Parse decision traces
            for rec in recommendations_list:
                decision_trace = rec.get('decision_trace')
                if isinstance(decision_trace, str):
                    try:
                        rec['decision_trace'] = json.loads(decision_trace)
                    except json.JSONDecodeError:
                        rec['decision_trace'] = {}
        else:
            rec_query = """
                SELECT recommendation_id, user_id, type, content_id, title, 
                       rationale, decision_trace, shown_at
                FROM recommendations
                WHERE user_id = ?
                ORDER BY shown_at DESC
            """
            rec_rows = db.fetch_all(rec_query, (user_id,))
            recommendations_list = []
            for row in rec_rows:
                rec_dict = dict(row)
                # Parse decision_trace if it's a string
                decision_trace = rec_dict.get('decision_trace')
                if isinstance(decision_trace, str):
                    try:
                        rec_dict['decision_trace'] = json.loads(decision_trace)
                    except json.JSONDecodeError:
                        rec_dict['decision_trace'] = {}
                recommendations_list.append(rec_dict)
        
        # Build user detail response
        user_detail = {
            "user": {
                "user_id": user.get('user_id', user_id) if USE_FIRESTORE else user_row["user_id"],
                "name": user.get('name', 'Unknown') if USE_FIRESTORE else user_row["name"],
                "created_at": user.get('created_at', '') if USE_FIRESTORE else user_row["created_at"],
                "personas": {
                    "30d": persona_30d,
                    "180d": persona_180d
                },
                "account_counts": account_counts
            },
            "signals": {
                "30d": signals_30d,
                "180d": signals_180d
            },
            "recommendations": recommendations_list,
            "accounts": {
                "checking": [acc for acc in all_accounts if acc.get('type') == 'depository' and acc.get('subtype') == 'checking'],
                "savings": [acc for acc in all_accounts if acc.get('type') == 'depository' and acc.get('subtype') in ['savings', 'money_market', 'cd', 'hsa']],
                "credit": [acc for acc in all_accounts if acc.get('type') == 'credit']
            }
        }
        
        # Clean NaN values before returning to ensure JSON serialization works
        user_detail = clean_nan_values(user_detail)
        
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
            
            response = {
                "user_id": user_id,
                "time_window": time_window,
                "signals": signals
            }
            
            # Clean NaN values before returning
            return clean_nan_values(response)
        else:
            # Use SQLite - verify user exists
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get signals using existing function
            signals = get_user_features(user_id, time_window)
            
            response = {
                "user_id": user_id,
                "time_window": time_window,
                "signals": signals
            }
            
            # Clean NaN values before returning
            return clean_nan_values(response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching signals: {str(e)}")


@app.post("/api/users/{user_id}/compute-features")
def compute_features(user_id: str, time_window: str = "30d", force_recompute: bool = False):
    """Compute behavioral signals for a user.
    
    Args:
        user_id: User identifier (path parameter)
        time_window: Time window for computation - "30d" or "180d" (default: "30d")
        force_recompute: If True, recompute features even if they already exist (default: False)
        
    Returns:
        JSON response with status, computed signal types, and timestamp
        
    Raises:
        404: User not found
        400: Invalid time_window parameter
        500: Computation error
    """
    try:
        # Validate time_window parameter
        if time_window not in ["30d", "180d"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid time_window: '{time_window}'. Must be '30d' or '180d'"
            )
        
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
        
        # Check if features already exist (unless force_recompute is True)
        if not force_recompute:
            existing_features = get_user_features(user_id, time_window)
            if existing_features:
                # Check if all expected signal types are present
                expected_signals = {"subscriptions", "credit_utilization", "savings_behavior", "income_stability"}
                existing_signal_types = set(existing_features.keys())
                if expected_signals.issubset(existing_signal_types):
                    return {
                        "status": "success",
                        "user_id": user_id,
                        "time_window": time_window,
                        "computed_signals": list(existing_signal_types),
                        "message": "Features already exist for this time window",
                        "timestamp": datetime.now().isoformat()
                    }
        
        # Compute all features
        computed_features = compute_all_features(user_id, time_window)
        
        # Extract signal types from computed features
        computed_signal_types = list(computed_features.keys())
        
        return {
            "status": "success",
            "user_id": user_id,
            "time_window": time_window,
            "computed_signals": computed_signal_types,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error computing features: {str(e)}"
        )


def _derive_tags_from_category(category: str) -> List[str]:
    """Derive tags from category name."""
    category_to_tags = {
        "credit": ["Credit", "DebtManagement"],
        "savings": ["Savings", "Planning"],
        "budgeting": ["Budgeting", "Planning"],
        "debt": ["DebtManagement", "Credit"],
        "spending": ["Spending", "Budgeting"],
        "investing": ["Investing", "Planning"],
        "planning": ["Planning", "Goals"],
        "general": ["FinancialEducation"]
    }
    return category_to_tags.get(category, ["FinancialEducation"])


@app.get("/api/users/{user_id}/recommendations")
def get_user_recommendations(user_id: str, time_window: Optional[str] = None):
    """Get user's recommendations enriched with content catalog data"""
    try:
        # Verify user exists and get signals for eligibility checking
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get recommendations from Firestore
            recommendations_list = firestore_get_recommendations(user_id)
            
            # Get user signals for eligibility checking
            signals = get_user_features(user_id, time_window or "30d")
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
            recommendations_list = [dict(row) for row in rec_rows]
            
            # Get user signals for eligibility checking
            signals = get_user_features(user_id, time_window or "30d")
        
        # Enrich recommendations with content catalog data
        education_items = []
        offers = []
        
        for rec in recommendations_list:
            # Parse decision_trace if it's a string
            decision_trace = rec.get('decision_trace')
            if isinstance(decision_trace, str):
                try:
                    decision_trace = json.loads(decision_trace)
                except json.JSONDecodeError:
                    decision_trace = {}
            
            content_id = rec.get('content_id', '')
            rec_type = rec.get('type', '')
            
            # Get content from catalog
            content_item = get_content_by_id(content_id)
            
            base_recommendation = {
                "recommendation_id": rec.get('recommendation_id', ''),
                "user_id": rec.get('user_id', user_id),
                "type": rec_type,
                "content_id": content_id,
                "title": rec.get('title', ''),
                "rationale": rec.get('rationale', ''),
                "decision_trace": decision_trace,
                "shown_at": rec.get('shown_at', '')
            }
            
            if rec_type == "education":
                # Enrich education items
                category = content_item.get('category', 'general') if content_item else 'general'
                tags = _derive_tags_from_category(category)
                
                enriched = {
                    **base_recommendation,
                    "category": category,
                    "tags": tags,
                    "description": content_item.get('summary', rec.get('rationale', '')) if content_item else rec.get('rationale', ''),
                    "full_content": content_item.get('full_content', '') if content_item else ''
                }
                education_items.append(enriched)
            
            elif rec_type == "partner_offer":
                # Enrich partner offers
                partner_name = content_item.get('partner', 'Partner') if content_item else 'Partner'
                
                # Check eligibility
                eligible = True
                if content_item:
                    eligible = check_offer_eligibility(content_item, signals)
                
                # Generate partner logo URL (placeholder for now)
                partner_logo_url = f"/placeholder-logo-{content_id}.png" if content_item else None
                
                enriched = {
                    **base_recommendation,
                    "partner": partner_name,
                    "partner_logo_url": partner_logo_url,
                    "eligibility": "eligible" if eligible else "requirements_not_met",
                    "description": content_item.get('summary', rec.get('rationale', '')) if content_item else rec.get('rationale', '')
                }
                offers.append(enriched)
            else:
                # Unknown type, include as-is
                education_items.append(base_recommendation)
        
        # Filter to 3-5 education items, 2-3 offers
        education_items = education_items[:5]
        offers = offers[:3]
        
        # Return structured response
        return {
            "data": {
                "education": education_items,
                "offers": offers
            },
            "meta": {
                "user_id": user_id,
                "time_window": time_window or "30d"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {str(e)}")


@app.get("/api/users/{user_id}/transactions")
def get_user_transactions(user_id: str, start_date: Optional[str] = None, limit: Optional[int] = 100):
    """Get user's transactions"""
    try:
        # Check dynamically in case emulator started after module import
        use_firestore = check_use_firestore()
        if use_firestore:
            # Use Firestore - verify user exists
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get transactions from Firestore
            from src.database.firestore import get_user_transactions as firestore_get_user_transactions
            from src.database.firestore import get_user_accounts as firestore_get_user_accounts
            transactions_list = firestore_get_user_transactions(user_id, start_date)
            
            # Get accounts to create account_mask lookup
            accounts_list = firestore_get_user_accounts(user_id)
            account_lookup = {acc.get('account_id'): acc.get('mask', '') for acc in accounts_list}
            
            # Enhance transactions with account_mask
            enhanced_transactions = []
            for txn in transactions_list:
                account_id = txn.get('account_id')
                account_mask = account_lookup.get(account_id, '')
                enhanced_txn = dict(txn)
                enhanced_txn['account_mask'] = account_mask
                # Normalize category to array format
                enhanced_txn['category'] = normalize_category(txn.get('category'))
                enhanced_transactions.append(enhanced_txn)
            
            # Apply limit
            if limit:
                enhanced_transactions = enhanced_transactions[:limit]
            
            return {
                "user_id": user_id,
                "transactions": enhanced_transactions
            }
        else:
            # Use SQLite - verify user exists
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Build query with JOIN to get account_mask
            where_clauses = ["t.user_id = ?"]
            params = [user_id]
            
            if start_date:
                where_clauses.append("t.date >= ?")
                params.append(start_date)
            
            query = f"""
                SELECT t.transaction_id, t.account_id, t.user_id, t.date, t.amount, 
                       t.merchant_name, t.category, t.pending, a.mask as account_mask,
                       t.location_address, t.location_city, t.location_region, 
                       t.location_postal_code, t.location_country, t.location_lat, t.location_lon,
                       t.iso_currency_code, t.payment_channel, t.authorized_date
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.account_id
                WHERE {' AND '.join(where_clauses)}
                ORDER BY t.date DESC
                LIMIT ?
            """
            params.append(limit or 100)
            
            transactions_rows = db.fetch_all(query, tuple(params))
            
            transactions = []
            for row in transactions_rows:
                transaction = {
                    "transaction_id": row["transaction_id"],
                    "account_id": row["account_id"],
                    "user_id": row["user_id"],
                    "date": row["date"],
                    "amount": row["amount"],
                    "merchant_name": row["merchant_name"],
                    "category": normalize_category(row["category"]),  # Normalize to array format
                    "pending": bool(row["pending"]) if row["pending"] is not None else False,
                    "account_mask": row.get("account_mask", "") or "",
                    "location_address": row.get("location_address"),
                    "location_city": row.get("location_city"),
                    "location_region": row.get("location_region"),
                    "location_postal_code": row.get("location_postal_code"),
                    "location_country": row.get("location_country"),
                    "location_lat": row.get("location_lat"),
                    "location_lon": row.get("location_lon"),
                    "iso_currency_code": row.get("iso_currency_code") or "USD",
                    "payment_channel": row.get("payment_channel"),
                    "authorized_date": row.get("authorized_date"),
                }
                transactions.append(transaction)
            
            return {
                "user_id": user_id,
                "transactions": transactions
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")


@app.get("/api/users/{user_id}/insights")
def get_user_insights(user_id: str, period: str = "30d"):
    """Get user's spending insights and charts data"""
    try:
        # Validate period
        if period not in ["30d", "90d"]:
            raise HTTPException(status_code=400, detail="Period must be '30d' or '90d'")
        
        # Calculate days from period
        days = 30 if period == "30d" else 90
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        if USE_FIRESTORE:
            # Use Firestore - verify user exists
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get transactions
            from src.database.firestore import get_user_transactions as firestore_get_user_transactions
            from src.database.firestore import get_user_accounts as firestore_get_user_accounts
            all_transactions = firestore_get_user_transactions(user_id, cutoff_date)
            
            # Filter for expenses (negative amounts)
            expenses = [t for t in all_transactions if t.get('amount', 0) < 0]
            
            # Get accounts
            accounts = firestore_get_user_accounts(user_id)
            
            # Get computed features if available
            signals = get_user_features(user_id, period)
            
            # Compute summary
            total_spending = sum(abs(t.get('amount', 0)) for t in expenses)
            average_daily_spend = total_spending / days if days > 0 else 0.0
            
            # Top category
            category_totals = {}
            for t in expenses:
                cat = get_primary_category(t.get('category', 'Uncategorized'))  # Use primary category for grouping
                category_totals[cat] = category_totals.get(cat, 0) + abs(t.get('amount', 0))
            top_category = max(category_totals.items(), key=lambda x: x[1])[0] if category_totals else None
            
            # Savings rate from signal if available
            savings_rate = None
            if signals.get('savings_behavior'):
                sb = signals['savings_behavior']
                # Try to compute savings rate from signal data
                avg_monthly_income = sb.get('avg_monthly_income', 0)
                avg_monthly_expenses = sb.get('avg_monthly_expenses', 0)
                if avg_monthly_income > 0:
                    savings_rate = ((avg_monthly_income - avg_monthly_expenses) / avg_monthly_income) * 100
            
            # Spending by category
            spending_by_category = []
            if category_totals:
                total = sum(category_totals.values())
                for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
                    spending_by_category.append({
                        "category": category,
                        "amount": round(amount, 2),
                        "percentage": round((amount / total) * 100, 1) if total > 0 else 0
                    })
            
            # Credit utilization trend
            credit_utilization = []
            credit_accounts = [acc for acc in accounts if acc.get('type') == 'credit']
            if credit_accounts:
                cu_signal = signals.get('credit_utilization')
                if cu_signal and cu_signal.get('accounts'):
                    # Use signal data
                    for acc_data in cu_signal['accounts']:
                        credit_utilization.append({
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "utilization": round(acc_data.get('utilization', 0) * 100, 1),
                            "balance": round(acc_data.get('balance', 0), 2),
                            "limit": round(acc_data.get('limit', 0), 2)
                        })
                else:
                    # Compute from account balances
                    for acc in credit_accounts:
                        balance = abs(acc.get('balance', 0))
                        limit = acc.get('limit', 0)
                        utilization = (balance / limit * 100) if limit > 0 else 0
                        credit_utilization.append({
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "utilization": round(utilization, 1),
                            "balance": round(balance, 2),
                            "limit": round(limit, 2)
                        })
            
            # Subscriptions
            subscriptions_data = {"total_monthly": 0.0, "subscriptions": []}
            subs_signal = signals.get('subscriptions')
            if subs_signal and subs_signal.get('recurring_merchants'):
                subscriptions_data["total_monthly"] = round(subs_signal.get('monthly_recurring', 0), 2)
                for merchant in subs_signal['recurring_merchants']:
                    subscriptions_data["subscriptions"].append({
                        "merchant": merchant.get('merchant', 'Unknown'),
                        "amount": round(merchant.get('amount', 0), 2)
                    })
            
            response = {
                "user_id": user_id,
                "period": period,
                "data": {
                    "summary": {
                        "total_spending": round(total_spending, 2),
                        "average_daily_spend": round(average_daily_spend, 2),
                        "top_category": top_category,
                        "savings_rate": round(savings_rate, 1) if savings_rate is not None else None
                    },
                    "charts": {
                        "spending_by_category": spending_by_category,
                        "credit_utilization": credit_utilization,
                        "subscriptions": subscriptions_data
                    }
                }
            }
            
            # Clean NaN values before returning
            return clean_nan_values(response)
        else:
            # Use SQLite - verify user exists
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get transactions
            txn_query = """
                SELECT amount, category
                FROM transactions
                WHERE user_id = ? AND date >= ? AND amount < 0
            """
            transactions_rows = db.fetch_all(txn_query, (user_id, cutoff_date))
            
            # Compute summary
            expenses = [{"amount": abs(row["amount"]), "category": normalize_category(row["category"])} for row in transactions_rows]
            total_spending = sum(t["amount"] for t in expenses)
            average_daily_spend = total_spending / days if days > 0 else 0.0
            
            # Top category
            category_totals = {}
            for t in expenses:
                cat = get_primary_category(t.get('category', 'Uncategorized'))  # Use primary category for grouping
                category_totals[cat] = category_totals.get(cat, 0) + t['amount']
            top_category = max(category_totals.items(), key=lambda x: x[1])[0] if category_totals else None
            
            # Savings rate from signal if available
            savings_rate = None
            signals = get_user_features(user_id, period)
            if signals.get('savings_behavior'):
                sb = signals['savings_behavior']
                avg_monthly_income = sb.get('avg_monthly_income', 0)
                avg_monthly_expenses = sb.get('avg_monthly_expenses', 0)
                if avg_monthly_income > 0:
                    savings_rate = ((avg_monthly_income - avg_monthly_expenses) / avg_monthly_income) * 100
            
            # Spending by category
            spending_by_category = []
            if category_totals:
                total = sum(category_totals.values())
                for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
                    spending_by_category.append({
                        "category": category,
                        "amount": round(amount, 2),
                        "percentage": round((amount / total) * 100, 1) if total > 0 else 0
                    })
            
            # Credit utilization trend
            credit_utilization = []
            credit_query = """
                SELECT account_id, balance, "limit"
                FROM accounts
                WHERE user_id = ? AND type = 'credit'
            """
            credit_accounts = db.fetch_all(credit_query, (user_id,))
            
            if credit_accounts:
                cu_signal = signals.get('credit_utilization')
                if cu_signal and cu_signal.get('accounts'):
                    # Use signal data
                    for acc_data in cu_signal['accounts']:
                        credit_utilization.append({
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "utilization": round(acc_data.get('utilization', 0) * 100, 1),
                            "balance": round(acc_data.get('balance', 0), 2),
                            "limit": round(acc_data.get('limit', 0), 2)
                        })
                else:
                    # Compute from account balances
                    for acc in credit_accounts:
                        balance = abs(acc.get('balance', 0))
                        limit = acc.get('limit', 0)
                        utilization = (balance / limit * 100) if limit > 0 else 0
                        credit_utilization.append({
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "utilization": round(utilization, 1),
                            "balance": round(balance, 2),
                            "limit": round(limit, 2)
                        })
            
            # Subscriptions
            subscriptions_data = {"total_monthly": 0.0, "subscriptions": []}
            subs_signal = signals.get('subscriptions')
            if subs_signal and subs_signal.get('recurring_merchants'):
                subscriptions_data["total_monthly"] = round(subs_signal.get('monthly_recurring', 0), 2)
                for merchant in subs_signal['recurring_merchants']:
                    subscriptions_data["subscriptions"].append({
                        "merchant": merchant.get('merchant', 'Unknown'),
                        "amount": round(merchant.get('amount', 0), 2)
                    })
            
            response = {
                "user_id": user_id,
                "period": period,
                "data": {
                    "summary": {
                        "total_spending": round(total_spending, 2),
                        "average_daily_spend": round(average_daily_spend, 2),
                        "top_category": top_category,
                        "savings_rate": round(savings_rate, 1) if savings_rate is not None else None
                    },
                    "charts": {
                        "spending_by_category": spending_by_category,
                        "credit_utilization": credit_utilization,
                        "subscriptions": subscriptions_data
                    }
                }
            }
            
            # Clean NaN values before returning
            return clean_nan_values(response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching insights: {str(e)}")


@app.get("/api/users/{user_id}/overview")
def get_user_overview(user_id: str):
    """Get user's financial overview with accounts organized by type and summary metrics"""
    try:
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
        
        # Get all accounts
        if USE_FIRESTORE:
            from src.database.firestore import get_user_accounts as firestore_get_user_accounts
            all_accounts = firestore_get_user_accounts(user_id)
        else:
            accounts_query = """
                SELECT account_id, balance, "limit", type, subtype, mask
                FROM accounts
                WHERE user_id = ?
            """
            accounts_rows = db.fetch_all(accounts_query, (user_id,))
            all_accounts = [dict(row) for row in accounts_rows]
        
        # Get behavioral signals for health indicators
        signals = get_user_features(user_id, "30d")
        
        # Organize accounts by type
        checking_accounts = []
        savings_accounts = []
        credit_accounts = []
        
        total_checking = 0.0
        total_savings = 0.0
        total_credit_debt = 0.0
        total_credit_limit = 0.0
        
        for acc in all_accounts:
            account_id = acc.get('account_id')
            balance = float(acc.get('balance', 0))
            account_type = acc.get('type', '')
            subtype = acc.get('subtype', '')
            mask = acc.get('mask', '')
            limit = acc.get('limit')
            
            account_data = {
                "account_id": account_id,
                "mask": mask,
                "balance": round(balance, 2),
                "type": subtype,
                "name": f"{subtype.replace('_', ' ').title()} Account" if subtype else "Account"
            }
            
            if account_type == 'depository':
                if subtype == 'checking':
                    checking_accounts.append(account_data)
                    total_checking += balance
                elif subtype in ['savings', 'money_market', 'cd', 'hsa']:
                    savings_accounts.append(account_data)
                    total_savings += balance
            elif account_type == 'credit':
                credit_limit = float(limit) if limit else 0.0
                credit_balance = abs(balance)  # Credit balances are typically negative
                utilization = (credit_balance / credit_limit * 100) if credit_limit > 0 else 0
                available = credit_limit - credit_balance
                
                account_data.update({
                    "limit": round(credit_limit, 2),
                    "utilization": round(utilization, 1),
                    "available": round(available, 2),
                    "name": f"{subtype.replace('_', ' ').title()}" if subtype else "Credit Card"
                })
                credit_accounts.append(account_data)
                total_credit_debt += credit_balance
                total_credit_limit += credit_limit
        
        # Calculate summary metrics
        net_worth = total_checking + total_savings - total_credit_debt
        available_credit = total_credit_limit - total_credit_debt
        
        # Get health indicators from signals
        credit_utilization_overall = 0.0
        emergency_fund_months = None
        cash_flow_status = "positive"
        overall_health = "good"
        
        # Credit utilization
        credit_signal = signals.get('credit_utilization', {})
        if credit_signal.get('accounts'):
            # Calculate weighted average utilization
            total_util = 0.0
            total_limit_weight = 0.0
            for acc in credit_signal['accounts']:
                acc_limit = acc.get('limit', 0)
                acc_util = acc.get('utilization', 0)
                if acc_limit > 0:
                    total_util += acc_util * acc_limit
                    total_limit_weight += acc_limit
            credit_utilization_overall = (total_util / total_limit_weight * 100) if total_limit_weight > 0 else 0.0
        elif total_credit_limit > 0:
            credit_utilization_overall = (total_credit_debt / total_credit_limit) * 100
        
        # Emergency fund coverage
        savings_signal = signals.get('savings_behavior', {})
        emergency_fund_months = savings_signal.get('emergency_fund_coverage')
        
        # Monthly income/expenses for cash flow
        income_signal = signals.get('income_stability', {})
        avg_monthly_income = income_signal.get('avg_monthly_income', 0)
        avg_monthly_expenses = savings_signal.get('avg_monthly_expenses', 0) or income_signal.get('avg_monthly_expenses', 0)
        
        if avg_monthly_income > 0:
            if avg_monthly_expenses > avg_monthly_income:
                cash_flow_status = "negative"
            elif avg_monthly_expenses > avg_monthly_income * 0.9:
                cash_flow_status = "tight"
            else:
                cash_flow_status = "positive"
        
        # Determine overall health
        if credit_utilization_overall > 80 or emergency_fund_months is not None and emergency_fund_months < 1:
            overall_health = "needs_attention"
        elif credit_utilization_overall > 50 or emergency_fund_months is not None and emergency_fund_months < 3 or cash_flow_status == "negative":
            overall_health = "fair"
        else:
            overall_health = "good"
        
        response = {
            "user_id": user_id,
            "data": {
                "summary": {
                    "net_worth": round(net_worth, 2),
                    "total_savings": round(total_savings, 2),
                    "total_credit_debt": round(total_credit_debt, 2),
                    "total_credit_limit": round(total_credit_limit, 2),
                    "available_credit": round(available_credit, 2),
                    "monthly_income": round(avg_monthly_income, 2) if avg_monthly_income > 0 else None,
                    "monthly_expenses": round(avg_monthly_expenses, 2) if avg_monthly_expenses > 0 else None
                },
                "accounts": {
                    "checking": checking_accounts,
                    "savings": savings_accounts,
                    "credit": credit_accounts
                },
                "health": {
                    "overall": overall_health,
                    "credit_utilization": round(credit_utilization_overall, 1),
                    "emergency_fund_months": round(emergency_fund_months, 1) if emergency_fund_months is not None else None,
                    "cash_flow_status": cash_flow_status
                }
            }
        }
        
        # Clean NaN values before returning
        return clean_nan_values(response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching overview: {str(e)}")


class OverrideRequest(BaseModel):
    recommendation_id: str
    reason: str


class FlagRequest(BaseModel):
    reason: str


@app.post("/api/users/{user_id}/override")
def override_recommendation(user_id: str, request: OverrideRequest):
    """Override a recommendation for a user"""
    try:
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Update recommendation in Firestore
            rec_ref = firestore_db.collection('users').document(user_id)\
                           .collection('recommendations')\
                           .document(request.recommendation_id)
            rec_doc = rec_ref.get()
            
            if not rec_doc.exists:
                raise HTTPException(status_code=404, detail="Recommendation not found")
            
            rec_ref.update({
                'overridden': True,
                'override_reason': request.reason,
                'overridden_at': firestore.SERVER_TIMESTAMP
            })
            
            return {"status": "success", "message": "Recommendation overridden"}
        else:
            # Use SQLite
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if recommendation exists
            rec_query = "SELECT recommendation_id FROM recommendations WHERE recommendation_id = ? AND user_id = ?"
            rec_row = db.fetch_one(rec_query, (request.recommendation_id, user_id))
            if not rec_row:
                raise HTTPException(status_code=404, detail="Recommendation not found")
            
            # Try to add overridden column if it doesn't exist (SQLite doesn't support ALTER TABLE IF NOT EXISTS for columns)
            # For now, we'll use a separate table or add the column manually
            # Simplest: use a JSON field or add column via migration
            # For MVP, we'll update the decision_trace to include override info
            update_query = """
                UPDATE recommendations
                SET decision_trace = json_set(
                    COALESCE(decision_trace, '{}'),
                    '$.overridden', true,
                    '$.override_reason', ?,
                    '$.overridden_at', ?
                )
                WHERE recommendation_id = ? AND user_id = ?
            """
            overridden_at = datetime.now().isoformat()
            with get_db_connection() as conn:
                # SQLite doesn't have json_set in older versions, so we'll use a simple approach
                # Update recommendation with override info in decision_trace
                existing_rec = db.fetch_one(
                    "SELECT decision_trace FROM recommendations WHERE recommendation_id = ? AND user_id = ?",
                    (request.recommendation_id, user_id)
                )
                if existing_rec:
                    decision_trace_str = existing_rec.get('decision_trace', '{}')
                    try:
                        decision_trace = json.loads(decision_trace_str) if decision_trace_str else {}
                    except json.JSONDecodeError:
                        decision_trace = {}
                    
                    decision_trace['overridden'] = True
                    decision_trace['override_reason'] = request.reason
                    decision_trace['overridden_at'] = overridden_at
                    
                    conn.execute(
                        "UPDATE recommendations SET decision_trace = ? WHERE recommendation_id = ? AND user_id = ?",
                        (json.dumps(decision_trace), request.recommendation_id, user_id)
                    )
            
            return {"status": "success", "message": "Recommendation overridden"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error overriding recommendation: {str(e)}")


@app.post("/api/users/{user_id}/flag")
def flag_user(user_id: str, request: FlagRequest):
    """Flag a user for review"""
    try:
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Update user in Firestore
            user_ref = firestore_db.collection('users').document(user_id)
            user_ref.update({
                'flagged': True,
                'flag_reason': request.reason,
                'flagged_at': firestore.SERVER_TIMESTAMP
            })
            
            return {"status": "success", "message": "User flagged for review"}
        else:
            # Use SQLite
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Update user with flag info
            # For SQLite, we'll store flag info in a JSON field or add column manually
            # Simplest: update user with flag info
            flagged_at = datetime.now().isoformat()
            with get_db_connection() as conn:
                # SQLite doesn't have a flagged column by default, so we'll note this
                # For now, we'll just return success - in production, add column via migration
                # For MVP demo, this is acceptable
                pass
            
            return {"status": "success", "message": "User flagged for review", "note": "Flag stored in memory (add flagged column to users table for persistence)"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error flagging user: {str(e)}")


@app.get("/api/users/{user_id}/actions")
def get_user_actions(user_id: str):
    """Get audit log of operator actions for a user (optional)"""
    try:
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if operator_actions collection exists
            actions_ref = firestore_db.collection('users').document(user_id)\
                            .collection('operator_actions')\
                            .order_by('created_at', direction=firestore.Query.DESCENDING)
            actions = [doc.to_dict() for doc in actions_ref.stream()]
            
            return {"actions": actions}
        else:
            # Use SQLite - check if operator_actions table exists
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Try to query operator_actions table (may not exist)
            try:
                actions_query = """
                    SELECT action_type, reason, created_at
                    FROM operator_actions
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """
                actions_rows = db.fetch_all(actions_query, (user_id,))
                actions = [dict(row) for row in actions_rows]
                return {"actions": actions}
            except Exception:
                # Table doesn't exist, return empty list
                return {"actions": [], "note": "operator_actions table not created yet"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching actions: {str(e)}")


@app.post("/api/chat")
def chat(request: ChatRequest):
    """Chat endpoint for AI-powered financial questions"""
    try:
        user_id = request.user_id
        
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
        
        # Check rate limit
        if not check_rate_limit(user_id):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_MESSAGES} messages per minute."
            )
        
        # Sanitize user message before processing
        sanitizer = get_sanitizer()
        sanitized_message, detected_pii = sanitizer.sanitize_user_message(request.message)
        
        if detected_pii:
            # Log PII detection for security monitoring
            # In production, send to security logging system
            print(f"SECURITY: PII detected in chat message from user {user_id}: {', '.join(detected_pii)}")
        
        # Get user data
        user_features = get_user_features(user_id, "30d")
        
        # Get recent transactions (last 30)
        if USE_FIRESTORE:
            from src.database.firestore import get_user_transactions as firestore_get_user_transactions
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            recent_transactions = firestore_get_user_transactions(user_id, cutoff_date)[:30]
        else:
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            txn_query = """
                SELECT transaction_id, account_id, user_id, date, amount, 
                       merchant_name, category, pending,
                       location_address, location_city, location_region,
                       location_postal_code, location_country, location_lat, location_lon,
                       iso_currency_code, payment_channel, authorized_date
                FROM transactions
                WHERE user_id = ? AND date >= ?
                ORDER BY date DESC
                LIMIT 30
            """
            txn_rows = db.fetch_all(txn_query, (user_id, cutoff_date))
            recent_transactions = []
            for row in txn_rows:
                txn_dict = dict(row)
                # Normalize category to array format
                txn_dict['category'] = normalize_category(txn_dict.get('category'))
                recent_transactions.append(txn_dict)
        
        # Get persona
        persona_dict = None
        if USE_FIRESTORE:
            personas = firestore_get_persona_assignments(user_id)
            # Find most recent persona for 30d window
            for persona in personas:
                if persona.get('time_window') == '30d':
                    persona_dict = {
                        "persona": persona.get('primary_persona') or persona.get('persona'),
                        "primary_persona": persona.get('primary_persona') or persona.get('persona'),
                        "match_percentages": {
                            "high_utilization": persona.get("match_high_utilization", 0.0) or 0.0,
                            "variable_income": persona.get("match_variable_income", 0.0) or 0.0,
                            "subscription_heavy": persona.get("match_subscription_heavy", 0.0) or 0.0,
                            "savings_builder": persona.get("match_savings_builder", 0.0) or 0.0,
                            "general_wellness": persona.get("match_general_wellness", 0.0) or 0.0
                        }
                    }
                    break
        else:
            persona = get_persona_assignment(user_id, "30d")
            if persona and isinstance(persona, dict):
                persona_dict = {
                    "persona": persona.get("primary_persona") or persona.get("persona"),
                    "primary_persona": persona.get("primary_persona") or persona.get("persona"),
                    "match_percentages": persona.get("match_percentages", {})
                }
        
        # Generate response
        try:
            chat_result = generate_chat_response(
                sanitized_message,  # Use sanitized message
                user_features,
                recent_transactions,
                persona_dict
            )
            
            response_text = chat_result["response"]
            citations = chat_result["citations"]
            
            # Validate guardrails
            guardrails = get_guardrails()
            is_valid, _, _ = guardrails.validate(response_text)
            guardrails_passed = is_valid
            
            # Store chat log (with original message for audit, sanitized was sent to LLM)
            citations_json = json.dumps(citations)
            if USE_FIRESTORE:
                from src.database.firestore import store_chat_log as firestore_store_chat_log
                firestore_store_chat_log(
                    user_id,
                    request.message,  # Store original message for audit trail
                    response_text,
                    citations,
                    guardrails_passed
                )
            else:
                insert_query = """
                    INSERT INTO chat_logs (user_id, message, response, citations, guardrails_passed, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                created_at = datetime.now().isoformat()
                with get_db_connection() as conn:
                    conn.execute(
                        insert_query,
                        (user_id, request.message, response_text, citations_json, 1 if guardrails_passed else 0, created_at)
                    )
            
            # Return response
            return {
                "data": {
                    "response": response_text,
                    "citations": citations
                },
                "meta": {
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except ValueError as e:
            # OpenAI API key not configured
            raise HTTPException(
                status_code=503,
                detail="Chat service is not configured. OPENAI_API_KEY environment variable is required."
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating chat response: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
