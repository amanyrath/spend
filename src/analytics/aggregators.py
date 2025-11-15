"""Analytics aggregation functions for operator dashboard.

This module provides functions to compute metrics for the operator analytics dashboard:
- Persona distribution over time
- Active user counts
- Success metrics by persona
- Recommendation safety indicators
- Financial outcome trends
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json

# Use centralized database configuration
from src.database.db_config import USE_FIRESTORE, HAS_SQLITE

# Make SQLite imports optional for Vercel deployment
try:
    from src.database.db import get_db_connection, DEFAULT_DB_PATH
except ImportError:
    # SQLite not available - use Firestore only
    get_db_connection = None
    DEFAULT_DB_PATH = None

# Import Firestore functions
try:
    from src.database.firestore import get_db as firestore_get_db
    FIRESTORE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    FIRESTORE_AVAILABLE = False
    def firestore_get_db():
        return None

from src.utils.logging import get_logger

logger = get_logger("analytics")


def get_persona_distribution_by_week(
    weeks: int = 12,
    db_path: Optional[str] = None,
    use_firestore: bool = False
) -> List[Dict[str, Any]]:
    """Get persona distribution aggregated by week.
    
    Args:
        weeks: Number of weeks to look back (default: 12)
        db_path: Path to SQLite database
        use_firestore: Whether to use Firestore
        
    Returns:
        List of weekly snapshots with persona counts
    """
    if use_firestore:
        return _get_persona_distribution_by_week_firestore(weeks)
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)
    
    weekly_data = []
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Generate week boundaries
        current_week_start = start_date
        while current_week_start <= end_date:
            week_end = current_week_start + timedelta(days=7)
            
            # Get persona assignments within this week
            query = """
                SELECT 
                    persona,
                    COUNT(DISTINCT user_id) as count
                FROM persona_assignments
                WHERE time_window = '30d'
                    AND assigned_at >= ?
                    AND assigned_at < ?
                GROUP BY persona
            """
            
            cursor.execute(query, (
                current_week_start.isoformat(),
                week_end.isoformat()
            ))
            
            rows = cursor.fetchall()
            
            # Build persona counts for this week
            week_data = {
                "week_start": current_week_start.strftime("%Y-%m-%d"),
                "high_utilization": 0,
                "variable_income": 0,
                "subscription_heavy": 0,
                "savings_builder": 0,
                "general_wellness": 0
            }
            
            for row in rows:
                persona = row[0]
                count = row[1]
                if persona:
                    week_data[persona] = count
            
            weekly_data.append(week_data)
            current_week_start = week_end
    
    return weekly_data


def _get_persona_distribution_by_week_firestore(weeks: int) -> List[Dict[str, Any]]:
    """Firestore implementation of persona distribution by week."""
    db = firestore_get_db()
    if db is None:
        return []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)
    
    weekly_data = []
    
    # Generate week boundaries
    current_week_start = start_date
    while current_week_start <= end_date:
        week_end = current_week_start + timedelta(days=7)
        
        week_data = {
            "week_start": current_week_start.strftime("%Y-%m-%d"),
            "high_utilization": 0,
            "variable_income": 0,
            "subscription_heavy": 0,
            "savings_builder": 0,
            "general_wellness": 0
        }
        
        # Query Firestore for persona assignments in this week
        users_ref = db.collection('users')
        for user_doc in users_ref.stream():
            personas_ref = user_doc.reference.collection('persona_assignments')\
                .where('time_window', '==', '30d')\
                .where('assigned_at', '>=', current_week_start.isoformat())\
                .where('assigned_at', '<', week_end.isoformat())
            
            for persona_doc in personas_ref.stream():
                data = persona_doc.to_dict()
                persona = data.get('primary_persona') or data.get('persona')
                if persona in week_data:
                    week_data[persona] += 1
        
        weekly_data.append(week_data)
        current_week_start = week_end
    
    return weekly_data


def get_current_persona_distribution(
    db_path: Optional[str] = None,
    use_firestore: bool = False
) -> Dict[str, int]:
    """Get current persona distribution across all users.
    
    Args:
        db_path: Path to SQLite database
        use_firestore: Whether to use Firestore
        
    Returns:
        Dictionary with persona counts
    """
    if use_firestore:
        return _get_current_persona_distribution_firestore()
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    distribution = {
        "high_utilization": 0,
        "variable_income": 0,
        "subscription_heavy": 0,
        "savings_builder": 0,
        "general_wellness": 0
    }
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Get most recent persona assignment per user (simplified query)
        query = """
            WITH latest_personas AS (
                SELECT 
                    user_id,
                    persona,
                    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY assigned_at DESC) as rn
                FROM persona_assignments
                WHERE time_window = '30d'
            )
            SELECT 
                persona,
                COUNT(DISTINCT user_id) as count
            FROM latest_personas
            WHERE rn = 1
            GROUP BY persona
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            persona = row[0]
            count = row[1]
            if persona in distribution:
                distribution[persona] = count
    
    return distribution


def _get_current_persona_distribution_firestore() -> Dict[str, int]:
    """Firestore implementation of current persona distribution."""
    db = firestore_get_db()
    if db is None:
        return {}
    
    distribution = {
        "high_utilization": 0,
        "variable_income": 0,
        "subscription_heavy": 0,
        "savings_builder": 0,
        "general_wellness": 0
    }
    
    users_ref = db.collection('users')
    for user_doc in users_ref.stream():
        # Get most recent 30d persona
        personas_ref = user_doc.reference.collection('persona_assignments')\
            .where('time_window', '==', '30d')\
            .order_by('assigned_at', direction='DESCENDING')\
            .limit(1)
        
        for persona_doc in personas_ref.stream():
            data = persona_doc.to_dict()
            persona = data.get('primary_persona') or data.get('persona')
            if persona in distribution:
                distribution[persona] += 1
            break
    
    return distribution


def get_active_users_count(
    days: int = 7,
    db_path: Optional[str] = None,
    use_firestore: bool = False
) -> int:
    """Count users with activity in the specified time window.
    
    Activity includes: transactions, chat messages, module interactions.
    
    Args:
        days: Number of days to look back
        db_path: Path to SQLite database
        use_firestore: Whether to use Firestore
        
    Returns:
        Count of active users
    """
    if use_firestore:
        return _get_active_users_count_firestore(days)
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Count distinct users with any activity
        query = """
            SELECT COUNT(DISTINCT user_id) FROM (
                SELECT user_id FROM chat_logs WHERE created_at >= ?
                UNION
                SELECT user_id FROM module_interactions WHERE timestamp >= ?
                UNION
                SELECT user_id FROM recommendations WHERE shown_at >= ?
            )
        """
        
        cursor.execute(query, (cutoff_date, cutoff_date, cutoff_date))
        result = cursor.fetchone()
        
        return result[0] if result else 0


def _get_active_users_count_firestore(days: int) -> int:
    """Firestore implementation of active users count."""
    db = firestore_get_db()
    if db is None:
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days)
    active_users = set()
    
    # Check chat logs
    users_ref = db.collection('users')
    for user_doc in users_ref.stream():
        user_id = user_doc.id
        
        # Check for chat activity
        chat_ref = user_doc.reference.collection('chat_logs')\
            .where('created_at', '>=', cutoff_date.isoformat())\
            .limit(1)
        
        for _ in chat_ref.stream():
            active_users.add(user_id)
            break
        
        # Check for recommendation views
        rec_ref = user_doc.reference.collection('recommendations')\
            .where('shown_at', '>=', cutoff_date.isoformat())\
            .limit(1)
        
        for _ in rec_ref.stream():
            active_users.add(user_id)
            break
    
    return len(active_users)


def get_recommendation_safety_indicators(
    db_path: Optional[str] = None,
    use_firestore: bool = False
) -> Dict[str, Any]:
    """Calculate recommendation safety metrics.
    
    Args:
        db_path: Path to SQLite database
        use_firestore: Whether to use Firestore
        
    Returns:
        Dictionary with safety indicators
    """
    if use_firestore:
        return _get_recommendation_safety_indicators_firestore()
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    indicators = {
        "total_recommendations": 0,
        "overridden_count": 0,
        "override_rate": 0.0,
        "total_chat_logs": 0,
        "guardrails_passed_count": 0,
        "guardrails_pass_rate": 0.0,
        "flagged_users_count": 0
    }
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Count total and overridden recommendations
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN overridden = 1 THEN 1 ELSE 0 END) as overridden
            FROM recommendations
        """)
        row = cursor.fetchone()
        if row:
            indicators["total_recommendations"] = row[0] or 0
            indicators["overridden_count"] = row[1] or 0
            if indicators["total_recommendations"] > 0:
                indicators["override_rate"] = indicators["overridden_count"] / indicators["total_recommendations"]
        
        # Count chat logs with guardrails
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN guardrails_passed = 1 THEN 1 ELSE 0 END) as passed
            FROM chat_logs
        """)
        row = cursor.fetchone()
        if row:
            indicators["total_chat_logs"] = row[0] or 0
            indicators["guardrails_passed_count"] = row[1] or 0
            if indicators["total_chat_logs"] > 0:
                indicators["guardrails_pass_rate"] = indicators["guardrails_passed_count"] / indicators["total_chat_logs"]
        
        # Count flagged users
        cursor.execute("SELECT COUNT(*) FROM users WHERE flagged = 1")
        row = cursor.fetchone()
        if row:
            indicators["flagged_users_count"] = row[0] or 0
    
    return indicators


def _get_recommendation_safety_indicators_firestore() -> Dict[str, Any]:
    """Firestore implementation of safety indicators."""
    db = firestore_get_db()
    if db is None:
        return {}
    
    indicators = {
        "total_recommendations": 0,
        "overridden_count": 0,
        "override_rate": 0.0,
        "total_chat_logs": 0,
        "guardrails_passed_count": 0,
        "guardrails_pass_rate": 0.0,
        "flagged_users_count": 0
    }
    
    users_ref = db.collection('users')
    
    for user_doc in users_ref.stream():
        # Check if user is flagged
        user_data = user_doc.to_dict()
        if user_data.get('flagged'):
            indicators["flagged_users_count"] += 1
        
        # Count recommendations
        for rec_doc in user_doc.reference.collection('recommendations').stream():
            indicators["total_recommendations"] += 1
            rec_data = rec_doc.to_dict()
            if rec_data.get('overridden'):
                indicators["overridden_count"] += 1
        
        # Count chat logs
        for chat_doc in user_doc.reference.collection('chat_logs').stream():
            indicators["total_chat_logs"] += 1
            chat_data = chat_doc.to_dict()
            if chat_data.get('guardrails_passed'):
                indicators["guardrails_passed_count"] += 1
    
    # Calculate rates
    if indicators["total_recommendations"] > 0:
        indicators["override_rate"] = indicators["overridden_count"] / indicators["total_recommendations"]
    if indicators["total_chat_logs"] > 0:
        indicators["guardrails_pass_rate"] = indicators["guardrails_passed_count"] / indicators["total_chat_logs"]
    
    return indicators


def get_success_metrics_by_persona(
    persona: Optional[str] = None,
    time_window: str = "30d",
    db_path: Optional[str] = None,
    use_firestore: bool = False
) -> Dict[str, Dict[str, Any]]:
    """Calculate success metrics grouped by persona.
    
    Args:
        persona: Specific persona to filter (None for all)
        time_window: Time window for metrics
        db_path: Path to SQLite database
        use_firestore: Whether to use Firestore
        
    Returns:
        Dictionary of metrics by persona
    """
    if use_firestore:
        return _get_success_metrics_by_persona_firestore(persona, time_window)
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    metrics_by_persona = {}
    personas = [persona] if persona else [
        "high_utilization", "variable_income", "subscription_heavy",
        "savings_builder", "general_wellness"
    ]
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        for p in personas:
            metrics = {
                "persona": p,
                "user_count": 0,
                "avg_recommendations": 0.0,
                "chat_messages": 0,
                "module_completions": 0,
                "override_rate": 0.0
            }
            
            # Get users with this persona
            cursor.execute("""
                WITH latest_personas AS (
                    SELECT 
                        user_id,
                        persona,
                        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY assigned_at DESC) as rn
                    FROM persona_assignments
                    WHERE time_window = ?
                )
                SELECT DISTINCT user_id
                FROM latest_personas
                WHERE rn = 1 AND persona = ?
            """, (time_window, p))
            
            user_ids = [row[0] for row in cursor.fetchall()]
            metrics["user_count"] = len(user_ids)
            
            if user_ids:
                # Count recommendations
                placeholders = ','.join('?' * len(user_ids))
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN overridden = 1 THEN 1 ELSE 0 END) as overridden
                    FROM recommendations
                    WHERE user_id IN ({placeholders})
                """, user_ids)
                
                row = cursor.fetchone()
                if row and row[0]:
                    total_recs = row[0]
                    overridden = row[1] or 0
                    metrics["avg_recommendations"] = total_recs / len(user_ids)
                    metrics["override_rate"] = overridden / total_recs if total_recs > 0 else 0.0
                
                # Count chat messages
                cursor.execute(f"""
                    SELECT COUNT(*) FROM chat_logs
                    WHERE user_id IN ({placeholders})
                """, user_ids)
                row = cursor.fetchone()
                if row:
                    metrics["chat_messages"] = row[0] or 0
                
                # Count module completions
                cursor.execute(f"""
                    SELECT COUNT(*) FROM module_interactions
                    WHERE user_id IN ({placeholders}) AND completed = 1
                """, user_ids)
                row = cursor.fetchone()
                if row:
                    metrics["module_completions"] = row[0] or 0
            
            metrics_by_persona[p] = metrics
    
    return metrics_by_persona


def _get_success_metrics_by_persona_firestore(
    persona: Optional[str],
    time_window: str
) -> Dict[str, Dict[str, Any]]:
    """Firestore implementation of success metrics by persona."""
    db = firestore_get_db()
    if db is None:
        return {}
    
    # Simplified implementation for Firestore
    # In production, this would need more sophisticated querying
    return {}


def get_total_users_count(
    db_path: Optional[str] = None,
    use_firestore: bool = False
) -> int:
    """Get total user count.
    
    Args:
        db_path: Path to SQLite database
        use_firestore: Whether to use Firestore
        
    Returns:
        Total number of users
    """
    if use_firestore:
        db = firestore_get_db()
        if db is None:
            return 0
        users_ref = db.collection('users')
        return len(list(users_ref.stream()))
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        result = cursor.fetchone()
        return result[0] if result else 0


def get_financial_outcome_trends(
    days: int = 90,
    db_path: Optional[str] = None,
    use_firestore: bool = False
) -> Dict[str, Any]:
    """Track financial outcome improvements over time.
    
    Args:
        days: Number of days to analyze
        db_path: Path to SQLite database
        use_firestore: Whether to use Firestore
        
    Returns:
        Dictionary with financial outcome metrics
    """
    if use_firestore:
        return {}  # Simplified for now
    
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    
    outcomes = {
        "users_improving_utilization": 0,
        "users_growing_savings": 0,
        "avg_utilization_change": 0.0,
        "avg_savings_growth": 0.0
    }
    
    # This would require comparing computed_features over time
    # For now, return placeholder metrics
    return outcomes

