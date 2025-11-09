"""FastAPI application for SpendSense API.

This module provides REST API endpoints for the SpendSense operator interface.
"""

import json
import os
import math
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
import time

# Load environment variables from .env file
load_dotenv()

from src.database import db
from src.database.db import (
    get_db_connection,
    store_operator_action as sqlite_store_operator_action,
    get_operator_actions as sqlite_get_operator_actions,
    get_consent_status as sqlite_get_consent_status,
    store_consent as sqlite_store_consent,
    revoke_consent as sqlite_revoke_consent
)
from src.personas.assignment import get_persona_assignment
from src.features.signal_detection import get_user_features, compute_all_features
from src.api.exceptions import (
    SpendSenseException,
    UserNotFoundError,
    InvalidInputError,
    UnauthorizedError,
    ForbiddenError,
    RateLimitError
)
from src.api.validators import (
    validate_user_id,
    validate_time_window,
    validate_limit,
    validate_offset
)
from src.api.error_handlers import (
    spendsense_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from src.api.rate_limit import check_rate_limit as check_rate_limit_new, RATE_LIMITS
from src.api.exceptions import RateLimitError
from src.api.auth import (
    get_current_user,
    require_operator,
    require_consumer,
    create_access_token,
    User
)
from src.utils.logging import get_logger
from src.recommend.content_catalog import get_content_by_id
from src.recommend.engine import check_offer_eligibility
from src.chat.service import generate_chat_response
from src.guardrails.guardrails_ai import get_guardrails
from src.guardrails.data_sanitizer import get_sanitizer
from src.utils.category_utils import normalize_category, get_primary_category
from src.utils.calculators import (
    calculate_balance_transfer_savings,
    calculate_subscription_savings,
    calculate_savings_goal_timeline,
    generate_budget_breakdown
)

# Import Firestore functions for deployment or emulator
# Import firestore module early so auto-detection runs
from src.database.firestore import (
    get_all_users as firestore_get_all_users,
    get_user as firestore_get_user,
    get_persona_assignments as firestore_get_persona_assignments,
    get_recommendations as firestore_get_recommendations,
    get_db as firestore_get_db,
    store_operator_action as firestore_store_operator_action,
    get_operator_actions as firestore_get_operator_actions,
    get_consent_status as firestore_get_consent_status,
    store_consent as firestore_store_consent,
    revoke_consent as firestore_revoke_consent
)
from firebase_admin import firestore

def check_use_firestore():
    """Check if Firestore should be used (dynamic check, not cached)."""
    # Force SQLite if explicitly requested (takes precedence over everything)
    if os.getenv('USE_SQLITE', '').lower() == 'true':
        return False
    
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

# Initialize logger
logger = get_logger("api")

app = FastAPI(
    title="SpendSense API",
    description="API for SpendSense financial education platform",
    version="1.0.0"
)

# Add exception handlers
app.add_exception_handler(SpendSenseException, spendsense_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Configure CORS
# Allow local development and common frontend ports, plus Vercel deployment
origins = [
    "https://spendsense-operator-ui.vercel.app",
    "https://spendsense-consumer-ui.vercel.app",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://localhost:4000",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:4000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    import uuid
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests and responses."""
    import time
    
    # Get request ID
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log request
    start_time = time.time()
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params)
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} - {response.status_code}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2)
        }
    )
    
    return response

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
    transaction_window_days: Optional[int] = 30
    
    @validator('transaction_window_days')
    def validate_window(cls, v):
        """Validate transaction_window_days is within acceptable range."""
        if v and (v < 7 or v > 180):
            raise ValueError('transaction_window_days must be between 7 and 180')
        return v or 30


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
    """Health check endpoint with database connectivity"""
    try:
        use_firestore = check_use_firestore()
        
        # Check database connectivity
        db_status = "unknown"
        db_error = None
        
        try:
            if use_firestore:
                # Test Firestore connection
                if firestore_db:
                    # Try to read a collection
                    list(firestore_db.collection('users').limit(1).stream())
                    db_status = "connected"
                else:
                    db_status = "disconnected"
                    db_error = "Firestore client not initialized"
            else:
                # Test SQLite connection
                with get_db_connection() as conn:
                    conn.execute("SELECT 1")
                    db_status = "connected"
        except Exception as e:
            db_status = "error"
            db_error = str(e)
            logger.error(f"Database health check failed: {str(e)}", exc_info=True)
        
        health_response = {
            "status": "ok" if db_status == "connected" else "degraded",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "type": "firestore" if use_firestore else "sqlite",
                "status": db_status,
                "error": db_error
            },
            "firestore_emulator_host": os.getenv('FIRESTORE_EMULATOR_HOST'),
            "firestore_db_available": firestore_db is not None if use_firestore else None
        }
        
        status_code = 200 if db_status == "connected" else 503
        return health_response
    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }, 503


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
    - limit: Items per page (default: 50, max: 100)
    """
    try:
        # Validate pagination parameters
        is_valid, error_msg, normalized_limit = validate_limit(limit, default=50, max_limit=100)
        if not is_valid:
            raise InvalidInputError(error_msg, field="limit")
        limit = normalized_limit
        
        is_valid, error_msg, normalized_offset = validate_offset((page - 1) * limit if page > 0 else 0)
        if not is_valid:
            raise InvalidInputError(error_msg, field="page")
        offset = normalized_offset
        
        # Validate search string if provided
        if search:
            search = search.strip()[:100]  # Limit length
        
        # Validate persona if provided
        if persona:
            valid_personas = ["high_utilization", "variable_income", "subscription_heavy", "savings_builder", "general_wellness"]
            if persona not in valid_personas:
                raise InvalidInputError(f"Invalid persona: {persona}. Must be one of: {', '.join(valid_personas)}", field="persona")
        if USE_FIRESTORE:
            if firestore_db is None:
                raise HTTPException(status_code=500, detail="Firestore database not initialized")
            
            start_time = time.time()
            
            # Use Firestore
            users = firestore_get_all_users() or []
            logger.info(f"Fetched {len(users)} users from Firestore in {time.time() - start_time:.2f}s")
            
            # Pre-filter users by search if provided (before expensive queries)
            if search:
                search_lower = search.lower()
                users = [
                    u for u in users 
                    if search_lower in u.get('name', '').lower() or search_lower in u.get('user_id', '').lower()
                ]
                logger.info(f"Filtered to {len(users)} users matching search")
            
            # Process users in parallel for better performance
            def process_user(user):
                """Process a single user and return enriched data"""
                try:
                    user_id = user.get('user_id')
                    if not user_id:
                        return None
                    
                    # Get persona assignment for 30d window
                    try:
                        persona_ref = firestore_db.collection('users').document(user_id)\
                                        .collection('persona_assignments')\
                                        .where('time_window', '==', '30d')\
                                        .order_by('assigned_at', direction=firestore.Query.DESCENDING)\
                                        .limit(1)
                        personas = list(persona_ref.stream())
                        persona_data = personas[0].to_dict() if personas else None
                    except Exception as e:
                        # If query fails (e.g., missing index), try without order_by
                        try:
                            persona_ref = firestore_db.collection('users').document(user_id)\
                                            .collection('persona_assignments')\
                                            .where('time_window', '==', '30d')
                            personas = list(persona_ref.stream())
                            if personas:
                                personas.sort(key=lambda x: x.to_dict().get('assigned_at', ''), reverse=True)
                            persona_data = personas[0].to_dict() if personas else None
                        except Exception as e2:
                            logger.warning(f"Persona query failed for {user_id} even without order_by: {e2}")
                            persona_data = None
                    
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
                    try:
                        features_ref = firestore_db.collection('users').document(user_id)\
                                        .collection('computed_features')\
                                        .where('time_window', '==', '30d')
                        behavior_count = len(list(features_ref.stream()))
                    except Exception as e:
                        logger.warning(f"Features query failed for {user_id}: {e}")
                        behavior_count = 0
                    
                    # Count recommendations
                    try:
                        recs_ref = firestore_db.collection('users').document(user_id)\
                                    .collection('recommendations')
                        recommendation_count = len(list(recs_ref.stream()))
                    except Exception as e:
                        logger.warning(f"Recommendations query failed for {user_id}: {e}")
                        recommendation_count = 0
                    
                    # Handle flagged field - check if it exists and is not None, default to False
                    flagged_value = False
                    if 'flagged' in user:
                        flagged_value = bool(user.get('flagged')) if user.get('flagged') is not None else False
                    
                    return {
                        "user_id": user_id,
                        "name": user.get('name', 'Unknown'),
                        "created_at": user.get('created_at'),
                        "flagged": flagged_value,
                        "persona_30d": persona_30d,
                        "match_percentages_30d": match_percentages_30d,
                        "behavior_count": behavior_count,
                        "recommendation_count": recommendation_count
                    }
                except Exception as e:
                    logger.warning(f"Error processing user {user.get('user_id', 'unknown')}: {e}")
                    return None
            
            # Process users in parallel (reduced to 5 workers for Firestore emulator stability)
            # For production Firestore, you can increase this to 10-20
            process_start = time.time()
            filtered_users = []
            stats_total_users = 0
            total_behaviors = 0
            total_recommendations = 0
            total_flagged = 0
            users_by_persona = defaultdict(int)
            
            # Use fewer workers for emulator, more for production
            max_workers = 5 if os.getenv('FIRESTORE_EMULATOR_HOST') else 10
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_user = {executor.submit(process_user, user): user for user in users}
                completed = 0
                for future in as_completed(future_to_user):
                    enriched_user = future.result()
                    completed += 1
                    
                    # Log progress every 10 users
                    if completed % 10 == 0:
                        elapsed = time.time() - process_start
                        rate = completed / elapsed if elapsed > 0 else 0
                        logger.info(f"Processed {completed}/{len(users)} users ({rate:.1f} users/s)")
                    
                    if enriched_user is None:
                        continue
                    
                    # Update stats (for all users matching search, regardless of persona filter)
                    stats_total_users += 1
                    total_behaviors += enriched_user.get('behavior_count', 0)
                    total_recommendations += enriched_user.get('recommendation_count', 0)
                    if enriched_user.get('flagged'):
                        total_flagged += 1
                    
                    # Count personas only if no persona filter is applied
                    persona_key = enriched_user.get('persona_30d') or 'none'
                    if not persona:
                        users_by_persona[persona_key] += 1
                    
                    # Apply persona filter for returned users
                    if persona and enriched_user.get('persona_30d') != persona:
                        continue
                    
                    filtered_users.append(enriched_user)
            
            process_time = time.time() - process_start
            logger.info(f"Processed {len(users)} users in {process_time:.2f}s ({len(filtered_users)} after filters)")
            
            # Sort by user_id for consistent pagination
            filtered_users.sort(key=lambda x: x['user_id'])
            
            # Calculate total before pagination (for pagination metadata)
            total_users = len(filtered_users)
            
            # Apply pagination
            start_idx = offset
            end_idx = offset + limit
            paginated_users = filtered_users[start_idx:end_idx]
            
            # Calculate averages (using stats_total_users which includes all users matching search)
            avg_behaviors = round(total_behaviors / stats_total_users, 2) if stats_total_users > 0 else 0.0
            avg_recommendations = round(total_recommendations / stats_total_users, 2) if stats_total_users > 0 else 0.0
        else:
            # Use SQLite - OPTIMIZED with JOINs and database-level pagination
            import sqlite3
            
            # Check if flagged column exists
            flagged_column_exists = True
            try:
                test_query = "SELECT flagged FROM users LIMIT 1"
                db.fetch_one(test_query)
            except sqlite3.OperationalError as e:
                if "no such column: flagged" in str(e).lower():
                    flagged_column_exists = False
            
            # Build base query with optional flagged column
            flagged_select = "COALESCE(u.flagged, 0) as flagged" if flagged_column_exists else "0 as flagged"
            
            # Optimized query using JOINs and subqueries for counts
            # Get latest persona assignment per user using window function
            # Count behaviors and recommendations in subqueries
            base_query = f"""
                SELECT 
                    u.user_id,
                    u.name,
                    u.created_at,
                    {flagged_select},
                    COALESCE(p.persona, NULL) as persona_30d,
                    COALESCE(p.match_high_utilization, 0.0) as match_high_utilization,
                    COALESCE(p.match_variable_income, 0.0) as match_variable_income,
                    COALESCE(p.match_subscription_heavy, 0.0) as match_subscription_heavy,
                    COALESCE(p.match_savings_builder, 0.0) as match_savings_builder,
                    COALESCE(p.match_general_wellness, 0.0) as match_general_wellness,
                    COALESCE(bf.behavior_count, 0) as behavior_count,
                    COALESCE(rc.recommendation_count, 0) as recommendation_count
                FROM users u
                LEFT JOIN (
                    SELECT 
                        user_id,
                        COALESCE(primary_persona, persona) as persona,
                        match_high_utilization,
                        match_variable_income,
                        match_subscription_heavy,
                        match_savings_builder,
                        match_general_wellness
                    FROM (
                        SELECT 
                            user_id,
                            COALESCE(primary_persona, persona) as persona,
                            match_high_utilization,
                            match_variable_income,
                            match_subscription_heavy,
                            match_savings_builder,
                            match_general_wellness,
                            ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY assigned_at DESC) as rn
                        FROM persona_assignments
                        WHERE time_window = '30d'
                    )
                    WHERE rn = 1
                ) p ON u.user_id = p.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as behavior_count
                    FROM computed_features
                    WHERE time_window = '30d'
                    GROUP BY user_id
                ) bf ON u.user_id = bf.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as recommendation_count
                    FROM recommendations
                    GROUP BY user_id
                ) rc ON u.user_id = rc.user_id
            """
            
            # Build WHERE clause for filters
            where_clauses = []
            query_params = []
            
            if search:
                where_clauses.append("(LOWER(u.name) LIKE ? OR LOWER(u.user_id) LIKE ?)")
                search_pattern = f"%{search.lower()}%"
                query_params.extend([search_pattern, search_pattern])
            
            if persona:
                where_clauses.append("p.persona = ?")
                query_params.append(persona)
            
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
            
            # Get total count for pagination (before LIMIT)
            count_query = f"""
                SELECT COUNT(DISTINCT u.user_id) as total
                FROM users u
                LEFT JOIN (
                    SELECT 
                        user_id,
                        COALESCE(primary_persona, persona) as persona
                    FROM (
                        SELECT 
                            user_id,
                            COALESCE(primary_persona, persona) as persona,
                            ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY assigned_at DESC) as rn
                        FROM persona_assignments
                        WHERE time_window = '30d'
                    )
                    WHERE rn = 1
                ) p ON u.user_id = p.user_id
                {where_clause}
            """
            
            total_count_row = db.fetch_one(count_query, tuple(query_params))
            total_users = total_count_row["total"] if total_count_row else 0
            
            # Calculate summary stats (optimized query)
            stats_where = ""
            stats_params = []
            if search:
                stats_where = "WHERE (LOWER(u.name) LIKE ? OR LOWER(u.user_id) LIKE ?)"
                search_pattern = f"%{search.lower()}%"
                stats_params = [search_pattern, search_pattern]
            
            # Build flagged condition for stats query
            flagged_condition = "u.flagged = 1" if flagged_column_exists else "0 = 1"
            
            stats_query = f"""
                SELECT 
                    COUNT(DISTINCT u.user_id) as total_users,
                    SUM(COALESCE(bf.behavior_count, 0)) as total_behaviors,
                    SUM(COALESCE(rc.recommendation_count, 0)) as total_recommendations,
                    SUM(CASE WHEN {flagged_condition} THEN 1 ELSE 0 END) as total_flagged
                FROM users u
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as behavior_count
                    FROM computed_features
                    WHERE time_window = '30d'
                    GROUP BY user_id
                ) bf ON u.user_id = bf.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as recommendation_count
                    FROM recommendations
                    GROUP BY user_id
                ) rc ON u.user_id = rc.user_id
                {stats_where}
            """
            
            stats_row = db.fetch_one(stats_query, tuple(stats_params) if stats_params else ())
            stats_total_users = stats_row["total_users"] if stats_row else 0
            total_behaviors = stats_row["total_behaviors"] if stats_row else 0
            total_recommendations = stats_row["total_recommendations"] if stats_row else 0
            total_flagged = stats_row["total_flagged"] if stats_row else 0
            
            # Get users by persona for summary (only if no persona filter)
            users_by_persona = defaultdict(int)
            if not persona:
                persona_stats_query = f"""
                    SELECT 
                        COALESCE(p.persona, 'none') as persona,
                        COUNT(DISTINCT u.user_id) as count
                    FROM users u
                    LEFT JOIN (
                        SELECT 
                            user_id,
                            COALESCE(primary_persona, persona) as persona
                        FROM (
                            SELECT 
                                user_id,
                                COALESCE(primary_persona, persona) as persona,
                                ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY assigned_at DESC) as rn
                            FROM persona_assignments
                            WHERE time_window = '30d'
                        )
                        WHERE rn = 1
                    ) p ON u.user_id = p.user_id
                    {stats_where}
                    GROUP BY p.persona
                """
                persona_stats = db.fetch_all(persona_stats_query, tuple(stats_params) if stats_params else ())
                for row in persona_stats:
                    persona_name = row["persona"] if row["persona"] else "none"
                    users_by_persona[persona_name] = row["count"]
            
            # Add ORDER BY and pagination
            order_by = "ORDER BY u.user_id"
            query_with_pagination = f"{base_query} {where_clause} {order_by} LIMIT ? OFFSET ?"
            query_params.extend([limit, offset])
            
            # Execute optimized query
            users = db.fetch_all(query_with_pagination, tuple(query_params))
            
            # Build enriched users from query results
            enriched_users = []
            for row in users:
                persona_30d = row["persona_30d"] if row["persona_30d"] else None
                
                # Build match percentages dict
                match_percentages_30d = None
                if persona_30d:
                    match_percentages_30d = {
                        "high_utilization": float(row.get("match_high_utilization", 0.0) or 0.0),
                        "variable_income": float(row.get("match_variable_income", 0.0) or 0.0),
                        "subscription_heavy": float(row.get("match_subscription_heavy", 0.0) or 0.0),
                        "savings_builder": float(row.get("match_savings_builder", 0.0) or 0.0),
                        "general_wellness": float(row.get("match_general_wellness", 0.0) or 0.0)
                    }
                
                flagged_value = bool(row.get("flagged", 0)) if row.get("flagged") is not None else False
                
                enriched_user = {
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "created_at": row.get("created_at"),
                    "flagged": flagged_value,
                    "persona_30d": persona_30d,
                    "match_percentages_30d": match_percentages_30d,
                    "behavior_count": int(row.get("behavior_count", 0) or 0),
                    "recommendation_count": int(row.get("recommendation_count", 0) or 0)
                }
                enriched_users.append(enriched_user)
            
            # Calculate averages
            avg_behaviors = round(total_behaviors / stats_total_users, 2) if stats_total_users > 0 else 0.0
            avg_recommendations = round(total_recommendations / stats_total_users, 2) if stats_total_users > 0 else 0.0
            
            # Paginated users are already limited by query
            paginated_users = enriched_users
        
        return {
            "users": paginated_users,
            "summary": {
                "total_users": total_users,
                "users_by_persona": dict(users_by_persona),
                "avg_behaviors": avg_behaviors,
                "avg_recommendations": avg_recommendations,
                "total_flagged": total_flagged
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
        # Validate user_id format
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            raise InvalidInputError(error_msg, field="user_id")
        
        # Validate time_window
        is_valid, error_msg, normalized_window = validate_time_window(time_window)
        if not is_valid:
            raise InvalidInputError(error_msg, field="time_window")
        time_window = normalized_window
        
        if USE_FIRESTORE:
            # Use Firestore - verify user exists
            user = firestore_get_user(user_id)
            if not user:
                raise UserNotFoundError(user_id)
            
            # Get signals using existing function (which handles Firestore)
            try:
                signals = get_user_features(user_id, time_window) or {}
            except Exception as e:
                logger.error(f"Error fetching signals from Firestore: {e}", exc_info=True)
                signals = {}
            
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
                raise UserNotFoundError(user_id)
            
            # Get signals using existing function
            try:
                signals = get_user_features(user_id, time_window) or {}
            except Exception as e:
                logger.error(f"Error fetching signals from SQLite: {e}", exc_info=True)
                signals = {}
            
            response = {
                "user_id": user_id,
                "time_window": time_window,
                "signals": signals
            }
            
            # Clean NaN values before returning
            return clean_nan_values(response)
    except (SpendSenseException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error fetching signals: {str(e)}", exc_info=True)
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
        # Validate user_id format
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            raise InvalidInputError(error_msg, field="user_id")
        
        # Validate time_window parameter
        is_valid, error_msg, normalized_window = validate_time_window(time_window)
        if not is_valid:
            raise InvalidInputError(error_msg, field="time_window")
        time_window = normalized_window
        
        # Check rate limit
        is_allowed, retry_after = check_rate_limit_new(user_id, "compute_features")
        if not is_allowed:
            raise RateLimitError(f"Rate limit exceeded for compute-features endpoint", retry_after=retry_after)
        
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise UserNotFoundError(user_id)
        else:
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise UserNotFoundError(user_id)
        
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
        # Validate user_id format
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            raise InvalidInputError(error_msg, field="user_id")
        
        # Verify user exists and get signals for eligibility checking
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get recommendations from Firestore
            try:
                recommendations_list = firestore_get_recommendations(user_id) or []
            except Exception as e:
                logger.error(f"Error fetching recommendations from Firestore: {e}", exc_info=True)
                recommendations_list = []
            
            # Get user signals for eligibility checking
            try:
                signals = get_user_features(user_id, time_window or "30d") or {}
            except Exception as e:
                logger.warning(f"Error fetching signals for recommendations: {e}")
                signals = {}
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
            recommendations_list = [dict(row) for row in rec_rows] if rec_rows else []
            
            # Get user signals for eligibility checking
            try:
                signals = get_user_features(user_id, time_window or "30d") or {}
            except Exception as e:
                logger.warning(f"Error fetching signals for recommendations: {e}")
                signals = {}
        
        # Enrich recommendations with content catalog data
        education_items = []
        offers = []
        
        for rec in recommendations_list:
            try:
                # Parse decision_trace if it's a string
                decision_trace = rec.get('decision_trace')
                if isinstance(decision_trace, str):
                    try:
                        decision_trace = json.loads(decision_trace)
                    except json.JSONDecodeError:
                        decision_trace = {}
                
                content_id = rec.get('content_id', '')
                rec_type = rec.get('type', '')
                
                # Get content from catalog - handle None gracefully
                content_item = None
                if content_id:
                    try:
                        content_item = get_content_by_id(content_id)
                    except Exception as e:
                        logger.warning(f"Error fetching content {content_id}: {e}")
                        content_item = None
                
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
                    if content_item and signals:
                        try:
                            eligible = check_offer_eligibility(content_item, signals)
                        except Exception as e:
                            logger.warning(f"Error checking eligibility: {e}")
                            eligible = True
                    
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
            except Exception as e:
                logger.warning(f"Error processing recommendation {rec.get('recommendation_id', 'unknown')}: {e}")
                continue
        
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
        logger.error(f"Error fetching recommendations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {str(e)}")


@app.post("/api/users/{user_id}/credit-offers/prequalify")
async def get_credit_offers_prequalification(user_id: str, time_window: str = "30d"):
    """Get pre-qualified credit offers for user with detailed match information
    
    Returns full credit offers API response with match percentages and reasons.
    """
    try:
        # Validate user_id format
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            raise InvalidInputError(error_msg, field="user_id")
        
        # Validate time_window
        is_valid, error_msg, normalized_window = validate_time_window(time_window)
        if not is_valid:
            raise InvalidInputError(error_msg, field="time_window")
        time_window = normalized_window
        
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise UserNotFoundError(user_id)
        else:
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise UserNotFoundError(user_id)
        
        # Get signals
        signals = get_user_features(user_id, time_window)
        
        # Build CustomerInfo from signals (same logic as match_offers)
        from src.recommend.engine import build_customer_info_from_signals
        from src.recommend.credit_offers import create_prequalification, PrequalificationResponse
        
        customer_info = build_customer_info_from_signals(signals)
        
        if not customer_info:
            raise HTTPException(
                status_code=400,
                detail="Unable to build customer information from signals. Please ensure features are computed."
            )
        
        # Get prequalification
        prequal_response = create_prequalification(customer_info)
        
        # Convert Pydantic model to dict for JSON response
        return {
            "prequalificationId": prequal_response.prequalificationId,
            "qualifiedProducts": [
                {
                    "productId": product.productId,
                    "code": product.code,
                    "productDisplayName": product.productDisplayName,
                    "priority": product.priority,
                    "tier": product.tier,
                    "creditRating": product.creditRating.value,
                    "images": product.images,
                    "introPurchaseApr": product.introPurchaseApr,
                    "purchaseApr": product.purchaseApr,
                    "introBalanceTransferApr": product.introBalanceTransferApr,
                    "balanceTransferFee": product.balanceTransferFee,
                    "annualMembershipFee": product.annualMembershipFee,
                    "mainMarketingCopy": product.mainMarketingCopy,
                    "extraMarketingCopy": product.extraMarketingCopy,
                    "applyNowLink": product.applyNowLink,
                    "matchPercentage": product.matchPercentage,
                    "matchReason": product.matchReason,
                    "bonusAmount": product.bonusAmount,
                    "bonusRequirement": product.bonusRequirement,
                    "estimatedSavings": product.estimatedSavings
                }
                for product in prequal_response.qualifiedProducts
            ],
            "customerCreditRating": prequal_response.customerCreditRating.value,
            "timestamp": prequal_response.timestamp
        }
        
    except (SpendSenseException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error fetching credit offers prequalification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching credit offers: {str(e)}")


@app.get("/api/users/{user_id}/transactions")
def get_user_transactions(user_id: str, start_date: Optional[str] = None, limit: Optional[int] = 100):
    """Get user's transactions"""
    try:
        # Validate user_id format
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            raise InvalidInputError(error_msg, field="user_id")
        
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
            
            try:
                transactions_list = firestore_get_user_transactions(user_id, start_date) or []
            except Exception as e:
                logger.error(f"Error fetching transactions from Firestore: {e}", exc_info=True)
                transactions_list = []
            
            # Get accounts to create account_mask lookup
            try:
                accounts_list = firestore_get_user_accounts(user_id) or []
            except Exception as e:
                logger.error(f"Error fetching accounts from Firestore: {e}", exc_info=True)
                accounts_list = []
            
            account_lookup = {acc.get('account_id'): acc.get('mask', '') for acc in accounts_list if acc}
            
            # Enhance transactions with account_mask
            enhanced_transactions = []
            for txn in transactions_list:
                try:
                    account_id = txn.get('account_id')
                    account_mask = account_lookup.get(account_id, '') if account_id else ''
                    enhanced_txn = dict(txn)
                    enhanced_txn['account_mask'] = account_mask
                    # Normalize category to array format - handle None
                    category = txn.get('category')
                    enhanced_txn['category'] = normalize_category(category) if category else []
                    enhanced_transactions.append(enhanced_txn)
                except Exception as e:
                    logger.warning(f"Error processing transaction {txn.get('transaction_id', 'unknown')}: {e}")
                    continue
            
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
                    "category": normalize_category(row["category"]) if row.get("category") else [],  # Normalize to array format
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
        logger.error(f"Error fetching transactions: {str(e)}", exc_info=True)
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
            # Note: acc_util is already in percentage form, so we calculate weighted average
            total_util = 0.0
            total_limit_weight = 0.0
            for acc in credit_signal['accounts']:
                acc_limit = acc.get('limit', 0)
                acc_util = acc.get('utilization', 0)
                if acc_limit > 0:
                    total_util += acc_util * acc_limit
                    total_limit_weight += acc_limit
            credit_utilization_overall = (total_util / total_limit_weight) if total_limit_weight > 0 else 0.0
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


@app.get("/api/users/{user_id}/accounts")
def get_user_accounts_with_details(user_id: str):
    """Get user's accounts with detailed liability information (APR, due dates, etc.)"""
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
        
        # Get accounts with liability details
        if USE_FIRESTORE:
            # For Firestore, we'll need to implement separate logic
            # For now, return basic account info
            from src.database.firestore import get_user_accounts as firestore_get_user_accounts
            all_accounts = firestore_get_user_accounts(user_id)
            # Map to expected format
            accounts_list = []
            for acc in all_accounts:
                account_data = {
                    "account_id": acc.get('account_id'),
                    "user_id": user_id,
                    "type": acc.get('type'),
                    "subtype": acc.get('subtype'),
                    "balance": acc.get('balance'),
                    "limit": acc.get('limit'),
                    "mask": acc.get('mask'),
                    "name": f"{acc.get('subtype', '').replace('_', ' ').title()}" if acc.get('subtype') else "Account",
                    "liability": None  # Firestore doesn't have liabilities yet
                }
                accounts_list.append(account_data)
        else:
            # SQLite: Join accounts with liabilities table
            accounts_query = """
                SELECT 
                    a.account_id, a.user_id, a.type, a.subtype, a.balance, a."limit", a.mask,
                    l.aprs, l.minimum_payment_amount, l.last_payment_amount, l.is_overdue,
                    l.last_statement_balance, l.origination_date, l.original_principal_balance,
                    l.interest_rate, l.next_payment_due_date, l.principal_balance,
                    l.escrow_balance, l.property_address, l.guarantor
                FROM accounts a
                LEFT JOIN liabilities l ON a.account_id = l.account_id
                WHERE a.user_id = ?
                ORDER BY a.type, a.subtype
            """
            accounts_rows = db.fetch_all(accounts_query, (user_id,))
            
            accounts_list = []
            for row in accounts_rows:
                row_dict = dict(row)
                
                # Build account data
                account_data = {
                    "account_id": row_dict['account_id'],
                    "user_id": row_dict['user_id'],
                    "type": row_dict['type'],
                    "subtype": row_dict['subtype'],
                    "balance": round(float(row_dict['balance']), 2),
                    "limit": round(float(row_dict['limit']), 2) if row_dict['limit'] else None,
                    "mask": row_dict['mask'],
                    "name": f"{row_dict['subtype'].replace('_', ' ').title()}" if row_dict['subtype'] else "Account"
                }
                
                # Add liability details if available
                liability_data = None
                if row_dict.get('aprs') or row_dict.get('interest_rate'):
                    liability_data = {}
                    
                    # Credit card fields
                    if row_dict.get('aprs'):
                        try:
                            aprs_parsed = json.loads(row_dict['aprs'])
                            liability_data['aprs'] = aprs_parsed
                            # Extract first APR percentage for convenience
                            if aprs_parsed and len(aprs_parsed) > 0:
                                liability_data['apr_percentage'] = aprs_parsed[0].get('apr_percentage')
                        except:
                            liability_data['aprs'] = []
                    
                    if row_dict.get('minimum_payment_amount'):
                        liability_data['minimum_payment_amount'] = round(float(row_dict['minimum_payment_amount']), 2)
                    if row_dict.get('last_payment_amount'):
                        liability_data['last_payment_amount'] = round(float(row_dict['last_payment_amount']), 2)
                    if row_dict.get('is_overdue') is not None:
                        liability_data['is_overdue'] = bool(row_dict['is_overdue'])
                    if row_dict.get('last_statement_balance'):
                        liability_data['last_statement_balance'] = round(float(row_dict['last_statement_balance']), 2)
                    
                    # Loan fields
                    if row_dict.get('origination_date'):
                        liability_data['origination_date'] = row_dict['origination_date']
                    if row_dict.get('original_principal_balance'):
                        liability_data['original_principal_balance'] = round(float(row_dict['original_principal_balance']), 2)
                    if row_dict.get('interest_rate'):
                        liability_data['interest_rate'] = round(float(row_dict['interest_rate']), 2)
                    if row_dict.get('next_payment_due_date'):
                        liability_data['next_payment_due_date'] = row_dict['next_payment_due_date']
                    if row_dict.get('principal_balance'):
                        liability_data['principal_balance'] = round(float(row_dict['principal_balance']), 2)
                    if row_dict.get('escrow_balance'):
                        liability_data['escrow_balance'] = round(float(row_dict['escrow_balance']), 2)
                    if row_dict.get('property_address'):
                        liability_data['property_address'] = row_dict['property_address']
                    if row_dict.get('guarantor'):
                        liability_data['guarantor'] = row_dict['guarantor']
                
                account_data['liability'] = liability_data
                
                # Add utilization for credit accounts
                if account_data['type'] == 'credit' and account_data['limit']:
                    credit_balance = abs(account_data['balance'])
                    utilization = (credit_balance / account_data['limit'] * 100) if account_data['limit'] > 0 else 0
                    account_data['utilization'] = round(utilization, 1)
                    account_data['available'] = round(account_data['limit'] - credit_balance, 2)
                
                accounts_list.append(account_data)
        
        return {
            "user_id": user_id,
            "accounts": accounts_list
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching accounts with details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching accounts: {str(e)}")


class BalanceTransferRequest(BaseModel):
    balance_transfer_amount: float
    transfer_fee_percent: float = 5.0
    apr_percent: float = 0.0
    additional_monthly_payment: float = 0.0


class SubscriptionSavingsRequest(BaseModel):
    selected_subscription_indices: List[int]


class SavingsGoalRequest(BaseModel):
    goal_amount: float


@app.post("/api/users/{user_id}/calculate-balance-transfer")
def calculate_balance_transfer_savings_endpoint(
    user_id: str,
    request: BalanceTransferRequest
):
    """Calculate savings from a balance transfer."""
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
        
        # Get credit account information
        signals = get_user_features(user_id, "30d")
        credit_signal = signals.get('credit_utilization', {})
        
        if not credit_signal.get('accounts'):
            raise HTTPException(
                status_code=400,
                detail="No credit accounts found for this user"
            )
        
        # Calculate total balance and average APR
        total_balance = sum(
            acc.get('balance', 0) for acc in credit_signal['accounts']
        )
        total_interest = credit_signal.get('interest_charged', 0)
        
        # Estimate current APR from interest charged (simplified)
        # If interest charged in 30 days, annualize it
        estimated_monthly_interest = total_interest
        if total_balance > 0:
            estimated_apr = (estimated_monthly_interest / total_balance) * 12 * 100
            # Cap at reasonable range
            estimated_apr = min(max(estimated_apr, 15.0), 30.0)
        else:
            estimated_apr = 24.99  # Default estimate
        
        # Use balance transfer amount or total balance
        balance_to_transfer = request.balance_transfer_amount or total_balance
        
        # Estimate current monthly payment (2% of balance minimum)
        current_monthly_payment = max(total_balance * 0.02, 25.0)
        
        # Calculate savings
        result = calculate_balance_transfer_savings(
            current_balance=balance_to_transfer,
            current_apr=estimated_apr,
            transfer_fee_percent=request.transfer_fee_percent,
            intro_apr=request.apr_percent,
            intro_period_months=18,  # Default intro period
            current_monthly_payment=current_monthly_payment,
            additional_monthly_payment=request.additional_monthly_payment
        )
        
        return {
            "user_id": user_id,
            "calculation": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating balance transfer savings: {str(e)}"
        )


@app.post("/api/users/{user_id}/calculate-subscription-savings")
def calculate_subscription_savings_endpoint(
    user_id: str,
    request: SubscriptionSavingsRequest
):
    """Calculate savings from canceling selected subscriptions."""
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
        
        # Get subscription data
        signals = get_user_features(user_id, "30d")
        subscription_signal = signals.get('subscriptions', {})
        
        merchant_details = subscription_signal.get('merchant_details', [])
        
        if not merchant_details:
            raise HTTPException(
                status_code=400,
                detail="No subscriptions found for this user"
            )
        
        # Calculate savings
        result = calculate_subscription_savings(
            subscriptions=merchant_details,
            selected_subscription_indices=request.selected_subscription_indices
        )
        
        return {
            "user_id": user_id,
            "calculation": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating subscription savings: {str(e)}"
        )


@app.post("/api/users/{user_id}/calculate-savings-goal")
def calculate_savings_goal_endpoint(
    user_id: str,
    request: SavingsGoalRequest
):
    """Calculate timeline to reach savings goal."""
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
        
        # Get savings data
        signals = get_user_features(user_id, "30d")
        savings_signal = signals.get('savings_behavior', {})
        
        # Get current savings from overview
        overview_response = get_user_overview(user_id)
        current_savings = overview_response['data']['summary'].get('total_savings', 0)
        
        # Get monthly savings rate
        monthly_savings_rate = savings_signal.get('avg_monthly_savings', 0)
        
        # Calculate timeline
        result = calculate_savings_goal_timeline(
            current_savings=current_savings,
            goal_amount=request.goal_amount,
            monthly_savings_rate=monthly_savings_rate
        )
        
        return {
            "user_id": user_id,
            "calculation": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating savings goal: {str(e)}"
        )


@app.post("/api/users/{user_id}/budget-breakdown")
def generate_budget_breakdown_endpoint(user_id: str):
    """Generate recommended budget breakdown."""
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
        
        # Get income and spending data
        signals = get_user_features(user_id, "180d")  # Use 180d for income stability
        
        income_signal = signals.get('income_stability', {})
        savings_signal = signals.get('savings_behavior', {})
        
        avg_monthly_income = income_signal.get('avg_monthly_income', 0)
        avg_monthly_expenses = (
            savings_signal.get('avg_monthly_expenses', 0) or
            income_signal.get('avg_monthly_expenses', 0)
        )
        
        # Get category spending from insights
        insights_response = get_user_insights(user_id, period="30d")
        category_spending = insights_response.get('data', {}).get('charts', {}).get('spending_by_category', [])
        
        # Generate budget breakdown
        result = generate_budget_breakdown(
            avg_monthly_income=avg_monthly_income,
            avg_monthly_expenses=avg_monthly_expenses,
            category_spending=category_spending
        )
        
        return {
            "user_id": user_id,
            "budget": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating budget breakdown: {str(e)}"
        )


class OverrideRequest(BaseModel):
    recommendation_id: str
    reason: str


class ModuleInteractionRequest(BaseModel):
    module_type: str
    inputs: dict
    outputs: dict
    completed: bool = False


@app.post("/api/users/{user_id}/track-module-interaction")
def track_module_interaction(
    user_id: str,
    request: ModuleInteractionRequest
):
    """Track user interaction with an education module."""
    try:
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Store interaction in Firestore
            import uuid
            from datetime import datetime
            interaction_id = str(uuid.uuid4())
            
            interaction_data = {
                'interaction_id': interaction_id,
                'user_id': user_id,
                'module_type': request.module_type,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'inputs': json.dumps(request.inputs),
                'outputs': json.dumps(request.outputs),
                'completed': request.completed
            }
            
            firestore_db.collection('module_interactions').document(interaction_id).set(interaction_data)
            
        else:
            # Store interaction in SQLite
            import uuid
            import datetime as dt
            
            interaction_id = str(uuid.uuid4())
            timestamp = dt.datetime.utcnow().isoformat()
            
            insert_query = """
                INSERT INTO module_interactions 
                (interaction_id, user_id, module_type, timestamp, inputs, outputs, completed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            db.execute(
                insert_query,
                (
                    interaction_id,
                    user_id,
                    request.module_type,
                    timestamp,
                    json.dumps(request.inputs),
                    json.dumps(request.outputs),
                    1 if request.completed else 0
                )
            )
            db.commit()
        
        return {
            "interaction_id": interaction_id,
            "message": "Module interaction tracked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error tracking module interaction: {str(e)}"
        )


class OverrideRequest(BaseModel):
    recommendation_id: str
    reason: str


class FlagRequest(BaseModel):
    reason: str


@app.post("/api/users/{user_id}/override")
def override_recommendation(
    user_id: str,
    request: OverrideRequest,
    current_user: User = Depends(require_operator)
):
    """Override a recommendation for a user (operator only)"""
    try:
        # Validate user_id format
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            raise InvalidInputError(error_msg, field="user_id")
        
        # Validate recommendation_id format
        from src.api.validators import validate_recommendation_id
        is_valid, error_msg = validate_recommendation_id(request.recommendation_id)
        if not is_valid:
            raise InvalidInputError(error_msg, field="recommendation_id")
        
        # Check rate limit
        is_allowed, retry_after = check_rate_limit_new(user_id, "override")
        if not is_allowed:
            raise RateLimitError(f"Rate limit exceeded for override endpoint", retry_after=retry_after)
        
        # Extract operator_id from authenticated user
        operator_id = current_user.user_id
        
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise UserNotFoundError(user_id)
            
            # Update recommendation in Firestore
            rec_ref = firestore_db.collection('users').document(user_id)\
                           .collection('recommendations')\
                           .document(request.recommendation_id)
            rec_doc = rec_ref.get()
            
            if not rec_doc.exists:
                from src.api.exceptions import RecommendationNotFoundError
                raise RecommendationNotFoundError(request.recommendation_id)
            
            # Extract operator_id from authenticated user
            operator_id = current_user.user_id
            
            # Update recommendation with override columns
            rec_ref.update({
                'overridden': True,
                'override_reason': request.reason,
                'overridden_at': firestore.SERVER_TIMESTAMP,
                'overridden_by': operator_id
            })
            
            # Store operator action
            firestore_store_operator_action(
                operator_id=operator_id,
                user_id=user_id,
                action_type='override',
                reason=request.reason,
                recommendation_id=request.recommendation_id
            )
            
            return {"status": "success", "message": "Recommendation overridden"}
        else:
            # Use SQLite
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise UserNotFoundError(user_id)
            
            # Check if recommendation exists
            rec_query = "SELECT recommendation_id FROM recommendations WHERE recommendation_id = ? AND user_id = ?"
            rec_row = db.fetch_one(rec_query, (request.recommendation_id, user_id))
            if not rec_row:
                from src.api.exceptions import RecommendationNotFoundError
                raise RecommendationNotFoundError(request.recommendation_id)
            
            # Extract operator_id from authenticated user
            operator_id = current_user.user_id
            
            # Update recommendation with override columns
            overridden_at = datetime.now().isoformat()
            update_query = """
                UPDATE recommendations
                SET overridden = 1,
                    override_reason = ?,
                    overridden_at = ?,
                    overridden_by = ?
                WHERE recommendation_id = ? AND user_id = ?
            """
            with get_db_connection() as conn:
                conn.execute(
                    update_query,
                    (request.reason, overridden_at, operator_id, request.recommendation_id, user_id)
                )
            
            # Store operator action
            sqlite_store_operator_action(
                operator_id=operator_id,
                user_id=user_id,
                action_type='override',
                reason=request.reason,
                recommendation_id=request.recommendation_id
            )
            
            return {"status": "success", "message": "Recommendation overridden"}
    except (SpendSenseException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error overriding recommendation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error overriding recommendation: {str(e)}")


@app.post("/api/users/{user_id}/flag")
def flag_user(
    user_id: str,
    request: FlagRequest,
    current_user: User = Depends(require_operator)
):
    """Flag a user for review (operator only)"""
    try:
        # Validate user_id format
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            raise InvalidInputError(error_msg, field="user_id")
        
        # Check rate limit
        is_allowed, retry_after = check_rate_limit_new(user_id, "flag")
        if not is_allowed:
            raise RateLimitError(f"Rate limit exceeded for flag endpoint", retry_after=retry_after)
        
        # Extract operator_id from authenticated user
        operator_id = current_user.user_id
        
        # Verify user exists
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise UserNotFoundError(user_id)
            
            # Extract operator_id from authenticated user
            operator_id = current_user.user_id
            
            # Update user with flag info
            user_ref = firestore_db.collection('users').document(user_id)
            user_ref.update({
                'flagged': True,
                'flag_reason': request.reason,
                'flagged_at': firestore.SERVER_TIMESTAMP,
                'flagged_by': operator_id
            })
            
            # Store operator action
            firestore_store_operator_action(
                operator_id=operator_id,
                user_id=user_id,
                action_type='flag',
                reason=request.reason,
                recommendation_id=None
            )
            
            return {"status": "success", "message": "User flagged for review"}
        else:
            # Use SQLite
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise UserNotFoundError(user_id)
            
            # Extract operator_id from authenticated user
            operator_id = current_user.user_id
            
            # Update user with flag info
            flagged_at = datetime.now().isoformat()
            update_query = """
                UPDATE users
                SET flagged = 1,
                    flag_reason = ?,
                    flagged_at = ?,
                    flagged_by = ?
                WHERE user_id = ?
            """
            with get_db_connection() as conn:
                conn.execute(
                    update_query,
                    (request.reason, flagged_at, operator_id, user_id)
                )
            
            # Store operator action
            sqlite_store_operator_action(
                operator_id=operator_id,
                user_id=user_id,
                action_type='flag',
                reason=request.reason,
                recommendation_id=None
            )
            
            return {"status": "success", "message": "User flagged for review"}
    except (SpendSenseException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error flagging user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error flagging user: {str(e)}")


@app.get("/api/users/{user_id}/actions")
def get_user_actions(user_id: str):
    """Get audit log of operator actions for a user"""
    try:
        # Validate user_id format
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            raise InvalidInputError(error_msg, field="user_id")
        
        # Verify user exists and get actions
        if USE_FIRESTORE:
            user = firestore_get_user(user_id)
            if not user:
                raise UserNotFoundError(user_id)
            
            actions = firestore_get_operator_actions(user_id=user_id)
            return {"actions": actions}
        else:
            # Use SQLite
            user_query = "SELECT user_id FROM users WHERE user_id = ?"
            user_row = db.fetch_one(user_query, (user_id,))
            if not user_row:
                raise UserNotFoundError(user_id)
            
            # Get operator actions
            actions = sqlite_get_operator_actions(user_id=user_id)
            return {"actions": actions}
    except (SpendSenseException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error fetching actions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching actions: {str(e)}")


@app.post("/api/chat")
def chat(request: ChatRequest):
    """Chat endpoint for AI-powered financial questions with configurable transaction window"""
    try:
        user_id = request.user_id
        transaction_window_days = request.transaction_window_days
        
        # Environment-based maximum limits
        max_window = int(os.getenv('CHAT_MAX_TRANSACTION_WINDOW', '180'))
        max_transactions = int(os.getenv('CHAT_MAX_TRANSACTIONS', '100'))
        
        # Validate and enforce limits
        if transaction_window_days > max_window:
            transaction_window_days = max_window
            logger.warning(f"Transaction window capped at {max_window} days")
        
        # Calculate transaction limit: ~3 transactions per day, capped at max
        transaction_limit = min(transaction_window_days * 3, max_transactions)
        
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
        is_allowed, retry_after = check_rate_limit_new(user_id, "chat")
        if not is_allowed:
            raise RateLimitError(f"Rate limit exceeded. Maximum {RATE_LIMITS['chat']['limit']} messages per {RATE_LIMITS['chat']['window']} seconds.", retry_after=retry_after)
        
        # Sanitize user message before processing
        sanitizer = get_sanitizer()
        sanitized_message, detected_pii = sanitizer.sanitize_user_message(request.message)
        
        if detected_pii:
            # Log PII detection for security monitoring
            logger.warning(
                f"PII detected in chat message from user {user_id}",
                extra={
                    "user_id": user_id,
                    "detected_pii": detected_pii
                }
            )
        
        # Get user data
        user_features = get_user_features(user_id, "30d")
        
        # Get user accounts for account-level analysis
        user_accounts = []
        if USE_FIRESTORE:
            from src.database.firestore import get_user_accounts as firestore_get_user_accounts
            user_accounts = firestore_get_user_accounts(user_id) or []
        else:
            accounts_query = "SELECT * FROM accounts WHERE user_id = ?"
            accounts_rows = db.fetch_all(accounts_query, (user_id,))
            user_accounts = [dict(row) for row in accounts_rows]
        
        # Get recent transactions with configurable window
        if USE_FIRESTORE:
            from src.database.firestore import get_user_transactions as firestore_get_user_transactions
            cutoff_date = (datetime.now() - timedelta(days=transaction_window_days)).strftime("%Y-%m-%d")
            recent_transactions = firestore_get_user_transactions(user_id, cutoff_date)[:transaction_limit]
        else:
            cutoff_date = (datetime.now() - timedelta(days=transaction_window_days)).strftime("%Y-%m-%d")
            txn_query = """
                SELECT transaction_id, account_id, user_id, date, amount, 
                       merchant_name, category, pending,
                       location_address, location_city, location_region,
                       location_postal_code, location_country, location_lat, location_lon,
                       iso_currency_code, payment_channel, authorized_date
                FROM transactions
                WHERE user_id = ? AND date >= ?
                ORDER BY date DESC
                LIMIT ?
            """
            txn_rows = db.fetch_all(txn_query, (user_id, cutoff_date, transaction_limit))
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
                persona_dict,
                transaction_window_days=transaction_window_days,
                user_accounts=user_accounts
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


# ============================================================================
# TRACE ENDPOINTS
# ============================================================================
# Consent Management API Endpoints
# ============================================================================

@app.post("/api/users/{user_id}/consent")
async def grant_consent(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Grant consent for data processing.
    
    Args:
        user_id: User ID to grant consent for
        request: FastAPI request object (to get IP address)
        current_user: Authenticated user from token
        
    Returns:
        Success response with message
        
    Raises:
        ForbiddenError: If user tries to consent for another user
    """
    # Verify user can only consent for themselves
    if current_user.user_id != user_id:
        raise ForbiddenError("Cannot consent for another user")
    
    ip_address = request.client.host if request.client else "unknown"
    
    try:
        if USE_FIRESTORE:
            firestore_store_consent(user_id, granted=True, ip_address=ip_address)
        else:
            sqlite_store_consent(user_id, granted=True, ip_address=ip_address)
        
        logger.info(f"Consent granted for user {user_id} from IP {ip_address}")
        return {"success": True, "message": "Consent granted"}
    
    except Exception as e:
        logger.error(f"Error granting consent for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error granting consent: {str(e)}")


@app.delete("/api/users/{user_id}/consent")
async def revoke_consent(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Revoke consent for data processing.
    
    Args:
        user_id: User ID to revoke consent for
        current_user: Authenticated user from token
        
    Returns:
        Success response with message
        
    Raises:
        ForbiddenError: If user tries to revoke consent for another user
    """
    # Verify user can only revoke their own consent
    if current_user.user_id != user_id:
        raise ForbiddenError("Cannot revoke consent for another user")
    
    try:
        if USE_FIRESTORE:
            firestore_revoke_consent(user_id)
        else:
            sqlite_revoke_consent(user_id)
        
        logger.info(f"Consent revoked for user {user_id}")
        return {"success": True, "message": "Consent revoked"}
    
    except Exception as e:
        logger.error(f"Error revoking consent for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error revoking consent: {str(e)}")


@app.get("/api/users/{user_id}/consent")
async def get_consent_status_endpoint(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get consent status for user.
    
    Args:
        user_id: User ID to check consent for
        current_user: Authenticated user from token
        
    Returns:
        Consent status object with granted flag and metadata
        
    Raises:
        ForbiddenError: If non-operator tries to view another user's consent
    """
    # Users can view their own consent, operators can view any
    if current_user.user_id != user_id and not current_user.is_operator():
        raise ForbiddenError("Cannot view consent for another user")
    
    try:
        if USE_FIRESTORE:
            consent = firestore_get_consent_status(user_id)
        else:
            consent = sqlite_get_consent_status(user_id)
        
        return consent
    
    except Exception as e:
        logger.error(f"Error fetching consent status for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching consent status: {str(e)}")


# ============================================================================

@app.get("/api/traces")
def get_traces(
    user_id: Optional[str] = None,
    trace_types: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    persona: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get all traces with filtering.
    
    Query parameters:
        - user_id: Filter by user ID
        - trace_types: Comma-separated list of trace types
        - start_date: Start date (ISO format)
        - end_date: End date (ISO format)
        - persona: Filter by persona
        - search: Search query
        - limit: Results per page (default: 50)
        - offset: Pagination offset (default: 0)
    """
    try:
        from src.traces.service import get_all_traces
        
        # Parse trace types
        trace_types_list = None
        if trace_types:
            trace_types_list = [t.strip() for t in trace_types.split(',')]
        
        result = get_all_traces(
            user_id=user_id,
            trace_types=trace_types_list,
            start_date=start_date,
            end_date=end_date,
            persona=persona,
            search_query=search,
            limit=limit,
            offset=offset
        )
        
        return {
            "data": result["traces"],
            "meta": {
                "total": result["total"],
                "limit": result["limit"],
                "offset": result["offset"],
                "has_more": result["has_more"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching traces: {str(e)}")


@app.get("/api/traces/users/{user_id}")
def get_user_traces(
    user_id: str,
    trace_types: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get all traces for a specific user."""
    try:
        from src.traces.service import get_all_traces
        
        # Parse trace types
        trace_types_list = None
        if trace_types:
            trace_types_list = [t.strip() for t in trace_types.split(',')]
        
        result = get_all_traces(
            user_id=user_id,
            trace_types=trace_types_list,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return {
            "data": result["traces"],
            "meta": {
                "total": result["total"],
                "limit": result["limit"],
                "offset": result["offset"],
                "has_more": result["has_more"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user traces: {str(e)}")


@app.get("/api/traces/users/{user_id}/timeline")
def get_user_timeline(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get chronological timeline of all events for a user."""
    try:
        from src.traces.service import get_user_timeline as get_timeline
        
        traces = get_timeline(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "data": traces,
            "meta": {
                "user_id": user_id,
                "total": len(traces)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user timeline: {str(e)}")


@app.get("/api/traces/{trace_id}")
def get_trace_detail(trace_id: str):
    """Get detailed information for a specific trace."""
    try:
        from src.traces.service import get_trace_by_id
        
        trace = get_trace_by_id(trace_id)
        
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return {
            "data": trace
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trace: {str(e)}")


@app.get("/api/traces/stats")
def get_trace_stats(user_id: Optional[str] = None):
    """Get statistics about traces."""
    try:
        from src.traces.service import get_trace_stats as get_stats
        
        stats = get_stats(user_id=user_id)
        
        return {
            "data": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trace stats: {str(e)}")


# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.get("/api/analytics/overview")
def get_analytics_overview():
    """Get comprehensive analytics overview for operator dashboard.
    
    Returns:
        - summary: Total users, active users, recommendations, safety metrics
        - personas: Current distribution and weekly history
        - success_metrics: Metrics by persona
    """
    try:
        from src.analytics.aggregators import (
            get_total_users_count,
            get_active_users_count,
            get_recommendation_safety_indicators,
            get_current_persona_distribution,
            get_persona_distribution_by_week,
            get_success_metrics_by_persona
        )
        
        # Get safety indicators (includes total recommendations)
        safety = get_recommendation_safety_indicators(use_firestore=USE_FIRESTORE)
        
        # Build summary
        summary = {
            "total_users": get_total_users_count(use_firestore=USE_FIRESTORE),
            "active_users_7d": get_active_users_count(days=7, use_firestore=USE_FIRESTORE),
            "active_users_30d": get_active_users_count(days=30, use_firestore=USE_FIRESTORE),
            "total_recommendations": safety["total_recommendations"],
            "override_rate": round(safety["override_rate"], 3),
            "guardrails_pass_rate": round(safety["guardrails_pass_rate"], 3),
            "flagged_users_count": safety["flagged_users_count"]
        }
        
        # Get persona data
        personas = {
            "current_distribution": get_current_persona_distribution(use_firestore=USE_FIRESTORE),
            "weekly_history": get_persona_distribution_by_week(weeks=12, use_firestore=USE_FIRESTORE)
        }
        
        # Get success metrics by persona
        success_metrics = {
            "by_persona": get_success_metrics_by_persona(time_window="30d", use_firestore=USE_FIRESTORE)
        }
        
        return {
            "summary": summary,
            "personas": personas,
            "success_metrics": success_metrics
        }
    
    except Exception as e:
        logger.error(f"Error fetching analytics overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching analytics overview: {str(e)}")


@app.get("/api/analytics/persona-trends")
def get_analytics_persona_trends(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "weekly"
):
    """Get time-series data for persona distribution changes.
    
    Query params:
        - start_date: Start date (ISO format)
        - end_date: End date (ISO format)
        - granularity: Time granularity (default: "weekly")
        
    Returns:
        List of time-series data points with persona counts
    """
    try:
        from src.analytics.aggregators import get_persona_distribution_by_week
        from datetime import datetime
        
        # Calculate weeks based on date range
        weeks = 12  # Default
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                days_diff = (end - start).days
                weeks = max(1, days_diff // 7)
            except ValueError:
                pass
        
        weekly_data = get_persona_distribution_by_week(weeks=weeks, use_firestore=USE_FIRESTORE)
        
        return {
            "data": weekly_data,
            "meta": {
                "granularity": granularity,
                "weeks": weeks
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching persona trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching persona trends: {str(e)}")


@app.get("/api/analytics/success-metrics")
def get_analytics_success_metrics(
    persona: Optional[str] = None,
    time_window: str = "30d"
):
    """Get detailed success metrics filtered by persona.
    
    Query params:
        - persona: Filter by specific persona (optional)
        - time_window: Time window for metrics (default: "30d")
        
    Returns:
        Detailed success metrics including:
        - Engagement metrics (recommendations, chat, modules)
        - Financial outcomes (utilization changes, savings growth)
        - System performance (acceptance rate, override rate)
    """
    try:
        from src.analytics.aggregators import get_success_metrics_by_persona
        
        # Validate persona if provided
        if persona:
            valid_personas = ["high_utilization", "variable_income", "subscription_heavy", 
                            "savings_builder", "general_wellness"]
            if persona not in valid_personas:
                raise InvalidInputError(
                    f"Invalid persona: {persona}. Must be one of: {', '.join(valid_personas)}",
                    field="persona"
                )
        
        # Validate time_window
        valid_windows = ["30d", "90d", "180d"]
        if time_window not in valid_windows:
            raise InvalidInputError(
                f"Invalid time_window: {time_window}. Must be one of: {', '.join(valid_windows)}",
                field="time_window"
            )
        
        metrics = get_success_metrics_by_persona(
            persona=persona,
            time_window=time_window,
            use_firestore=USE_FIRESTORE
        )
        
        return {
            "data": metrics,
            "meta": {
                "persona_filter": persona,
                "time_window": time_window
            }
        }
    
    except (InvalidInputError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error fetching success metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching success metrics: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
