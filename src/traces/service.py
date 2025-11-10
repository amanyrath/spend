"""Trace service for aggregating data from multiple tables into unified trace objects."""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Make SQLite imports optional for Vercel deployment
try:
    from src.database.db import get_db_connection
    HAS_SQLITE = True
except ImportError:
    # SQLite not available - use Firestore only
    HAS_SQLITE = False
    get_db_connection = None

from src.utils.logging import get_logger

logger = get_logger("traces")

# Trace type constants
TRACE_TYPE_CHAT = "chat_interaction"
TRACE_TYPE_RECOMMENDATION = "recommendation_generated"
TRACE_TYPE_OVERRIDE = "recommendation_overridden"
TRACE_TYPE_FLAG = "user_flagged"
TRACE_TYPE_PERSONA = "persona_assigned"
TRACE_TYPE_FEATURES = "features_computed"

ALL_TRACE_TYPES = [
    TRACE_TYPE_CHAT,
    TRACE_TYPE_RECOMMENDATION,
    TRACE_TYPE_OVERRIDE,
    TRACE_TYPE_FLAG,
    TRACE_TYPE_PERSONA,
    TRACE_TYPE_FEATURES
]


def _parse_json_field(value: Optional[str]) -> Any:
    """Safely parse JSON field."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def _format_chat_trace(row: tuple, columns: List[str]) -> Dict[str, Any]:
    """Format chat log into trace object."""
    data = dict(zip(columns, row))
    
    return {
        "trace_id": f"chat_{data['id']}",
        "trace_type": TRACE_TYPE_CHAT,
        "user_id": data["user_id"],
        "timestamp": data["created_at"],
        "summary": data["message"][:100] + "..." if len(data["message"]) > 100 else data["message"],
        "details": {
            "chat_id": data["id"],
            "message": data["message"],
            "response": data["response"],
            "citations": _parse_json_field(data.get("citations")),
            "guardrails_passed": bool(data.get("guardrails_passed", 0))
        },
        "related_traces": [],
        "persona": None
    }


def _format_recommendation_trace(row: tuple, columns: List[str]) -> Dict[str, Any]:
    """Format recommendation into trace object."""
    data = dict(zip(columns, row))
    
    decision_trace = _parse_json_field(data.get("decision_trace"))
    persona = None
    if decision_trace and isinstance(decision_trace, dict):
        persona = decision_trace.get("persona_match")
    
    return {
        "trace_id": f"rec_{data['recommendation_id']}",
        "trace_type": TRACE_TYPE_RECOMMENDATION,
        "user_id": data["user_id"],
        "timestamp": data["shown_at"],
        "summary": f"Recommendation: {data['title']}",
        "details": {
            "recommendation_id": data["recommendation_id"],
            "type": data["type"],
            "content_id": data["content_id"],
            "title": data["title"],
            "rationale": data["rationale"],
            "decision_trace": decision_trace,
            "overridden": bool(data.get("overridden", 0)),
            "override_reason": data.get("override_reason")
        },
        "related_traces": [],
        "persona": persona
    }


def _format_operator_action_trace(row: tuple, columns: List[str]) -> Dict[str, Any]:
    """Format operator action into trace object."""
    data = dict(zip(columns, row))
    
    action_type = data["action_type"]
    if action_type == "override":
        trace_type = TRACE_TYPE_OVERRIDE
        summary = f"Overridden recommendation: {data.get('recommendation_id', 'N/A')}"
    elif action_type == "flag":
        trace_type = TRACE_TYPE_FLAG
        summary = "User flagged for review"
    else:
        trace_type = action_type
        summary = f"Action: {action_type}"
    
    return {
        "trace_id": f"action_{data['id']}",
        "trace_type": trace_type,
        "user_id": data["user_id"],
        "timestamp": data["created_at"],
        "summary": summary,
        "details": {
            "action_id": data["id"],
            "operator_id": data["operator_id"],
            "action_type": action_type,
            "recommendation_id": data.get("recommendation_id"),
            "reason": data.get("reason")
        },
        "related_traces": [f"rec_{data['recommendation_id']}"] if data.get("recommendation_id") else [],
        "persona": None
    }


def _format_persona_trace(row: tuple, columns: List[str]) -> Dict[str, Any]:
    """Format persona assignment into trace object."""
    data = dict(zip(columns, row))
    
    persona = data.get("persona") or data.get("primary_persona")
    criteria_met = _parse_json_field(data.get("criteria_met"))
    
    return {
        "trace_id": f"persona_{data['id']}",
        "trace_type": TRACE_TYPE_PERSONA,
        "user_id": data["user_id"],
        "timestamp": data["assigned_at"],
        "summary": f"Persona assigned: {persona}",
        "details": {
            "assignment_id": data["id"],
            "persona": persona,
            "primary_persona": data.get("primary_persona"),
            "time_window": data["time_window"],
            "criteria_met": criteria_met,
            "match_percentages": {
                "high_utilization": data.get("match_high_utilization", 0.0),
                "variable_income": data.get("match_variable_income", 0.0),
                "subscription_heavy": data.get("match_subscription_heavy", 0.0),
                "savings_builder": data.get("match_savings_builder", 0.0),
                "general_wellness": data.get("match_general_wellness", 0.0)
            }
        },
        "related_traces": [],
        "persona": persona
    }


def _format_feature_trace(row: tuple, columns: List[str]) -> Dict[str, Any]:
    """Format computed feature into trace object."""
    data = dict(zip(columns, row))
    
    signal_type = data["signal_type"]
    signal_data = _parse_json_field(data.get("signal_data"))
    
    return {
        "trace_id": f"feature_{data['id']}",
        "trace_type": TRACE_TYPE_FEATURES,
        "user_id": data["user_id"],
        "timestamp": data["computed_at"],
        "summary": f"Features computed: {signal_type}",
        "details": {
            "feature_id": data["id"],
            "signal_type": signal_type,
            "time_window": data["time_window"],
            "signal_data": signal_data
        },
        "related_traces": [],
        "persona": None
    }


def get_all_traces(
    user_id: Optional[str] = None,
    trace_types: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    persona: Optional[str] = None,
    search_query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Get all traces with filtering.
    
    Args:
        user_id: Filter by user ID
        trace_types: List of trace types to include
        start_date: Start date for filtering (ISO format)
        end_date: End date for filtering (ISO format)
        persona: Filter by persona
        search_query: Search in trace content
        limit: Maximum number of traces to return
        offset: Offset for pagination
        db_path: Path to SQLite database
        
    Returns:
        Dictionary with traces and metadata
    """
    if trace_types is None:
        trace_types = ALL_TRACE_TYPES
    
    traces = []
    
    try:
        with get_db_connection(db_path) as conn:
            # Get chat logs
            if TRACE_TYPE_CHAT in trace_types:
                chat_query = "SELECT * FROM chat_logs WHERE 1=1"
                params = []
                
                if user_id:
                    chat_query += " AND user_id = ?"
                    params.append(user_id)
                if start_date:
                    chat_query += " AND created_at >= ?"
                    params.append(start_date)
                if end_date:
                    chat_query += " AND created_at <= ?"
                    params.append(end_date)
                if search_query:
                    chat_query += " AND (message LIKE ? OR response LIKE ?)"
                    params.extend([f"%{search_query}%", f"%{search_query}%"])
                
                cursor = conn.execute(chat_query, params)
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    traces.append(_format_chat_trace(row, columns))
            
            # Get recommendations
            if TRACE_TYPE_RECOMMENDATION in trace_types:
                rec_query = "SELECT * FROM recommendations WHERE 1=1"
                params = []
                
                if user_id:
                    rec_query += " AND user_id = ?"
                    params.append(user_id)
                if start_date:
                    rec_query += " AND shown_at >= ?"
                    params.append(start_date)
                if end_date:
                    rec_query += " AND shown_at <= ?"
                    params.append(end_date)
                if search_query:
                    rec_query += " AND (title LIKE ? OR rationale LIKE ?)"
                    params.extend([f"%{search_query}%", f"%{search_query}%"])
                
                cursor = conn.execute(rec_query, params)
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    trace = _format_recommendation_trace(row, columns)
                    if persona and trace["persona"] != persona:
                        continue
                    traces.append(trace)
            
            # Get operator actions
            if TRACE_TYPE_OVERRIDE in trace_types or TRACE_TYPE_FLAG in trace_types:
                action_query = "SELECT * FROM operator_actions WHERE 1=1"
                params = []
                
                if user_id:
                    action_query += " AND user_id = ?"
                    params.append(user_id)
                if start_date:
                    action_query += " AND created_at >= ?"
                    params.append(start_date)
                if end_date:
                    action_query += " AND created_at <= ?"
                    params.append(end_date)
                if search_query:
                    action_query += " AND reason LIKE ?"
                    params.append(f"%{search_query}%")
                
                # Filter by action type
                action_types = []
                if TRACE_TYPE_OVERRIDE in trace_types:
                    action_types.append("override")
                if TRACE_TYPE_FLAG in trace_types:
                    action_types.append("flag")
                
                if action_types:
                    placeholders = ",".join(["?" for _ in action_types])
                    action_query += f" AND action_type IN ({placeholders})"
                    params.extend(action_types)
                
                cursor = conn.execute(action_query, params)
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    traces.append(_format_operator_action_trace(row, columns))
            
            # Get persona assignments
            if TRACE_TYPE_PERSONA in trace_types:
                persona_query = "SELECT * FROM persona_assignments WHERE 1=1"
                params = []
                
                if user_id:
                    persona_query += " AND user_id = ?"
                    params.append(user_id)
                if start_date:
                    persona_query += " AND assigned_at >= ?"
                    params.append(start_date)
                if end_date:
                    persona_query += " AND assigned_at <= ?"
                    params.append(end_date)
                if persona:
                    persona_query += " AND (persona = ? OR primary_persona = ?)"
                    params.extend([persona, persona])
                
                cursor = conn.execute(persona_query, params)
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    traces.append(_format_persona_trace(row, columns))
            
            # Get computed features
            if TRACE_TYPE_FEATURES in trace_types:
                feature_query = "SELECT * FROM computed_features WHERE 1=1"
                params = []
                
                if user_id:
                    feature_query += " AND user_id = ?"
                    params.append(user_id)
                if start_date:
                    feature_query += " AND computed_at >= ?"
                    params.append(start_date)
                if end_date:
                    feature_query += " AND computed_at <= ?"
                    params.append(end_date)
                if search_query:
                    feature_query += " AND signal_type LIKE ?"
                    params.append(f"%{search_query}%")
                
                cursor = conn.execute(feature_query, params)
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    traces.append(_format_feature_trace(row, columns))
    
    except Exception as e:
        logger.error(f"Error fetching traces: {e}")
        raise
    
    # Sort by timestamp (most recent first)
    traces.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    
    # Apply pagination
    total = len(traces)
    traces = traces[offset:offset + limit]
    
    return {
        "traces": traces,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(traces) < total
    }


def get_user_timeline(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get chronological timeline of all events for a user.
    
    Args:
        user_id: User ID
        start_date: Start date for filtering (ISO format)
        end_date: End date for filtering (ISO format)
        db_path: Path to SQLite database
        
    Returns:
        List of trace objects sorted chronologically
    """
    result = get_all_traces(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=1000,  # Get all events for timeline
        offset=0,
        db_path=db_path
    )
    
    return result["traces"]


def get_trace_by_id(trace_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get a specific trace by ID.
    
    Args:
        trace_id: Trace ID (e.g., 'chat_123', 'rec_abc')
        db_path: Path to SQLite database
        
    Returns:
        Trace object or None if not found
    """
    parts = trace_id.split("_", 1)
    if len(parts) != 2:
        return None
    
    trace_prefix, id_value = parts
    
    try:
        with get_db_connection(db_path) as conn:
            if trace_prefix == "chat":
                cursor = conn.execute("SELECT * FROM chat_logs WHERE id = ?", (id_value,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return _format_chat_trace(row, columns)
            
            elif trace_prefix == "rec":
                cursor = conn.execute("SELECT * FROM recommendations WHERE recommendation_id = ?", (id_value,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return _format_recommendation_trace(row, columns)
            
            elif trace_prefix == "action":
                cursor = conn.execute("SELECT * FROM operator_actions WHERE id = ?", (id_value,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return _format_operator_action_trace(row, columns)
            
            elif trace_prefix == "persona":
                cursor = conn.execute("SELECT * FROM persona_assignments WHERE id = ?", (id_value,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return _format_persona_trace(row, columns)
            
            elif trace_prefix == "feature":
                cursor = conn.execute("SELECT * FROM computed_features WHERE id = ?", (id_value,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return _format_feature_trace(row, columns)
    
    except Exception as e:
        logger.error(f"Error fetching trace {trace_id}: {e}")
    
    return None


def get_trace_stats(
    user_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """Get statistics about traces.
    
    Args:
        user_id: Filter by user ID (optional)
        db_path: Path to SQLite database
        
    Returns:
        Dictionary with trace statistics
    """
    stats = {
        "total": 0,
        "by_type": {},
        "last_24h": 0,
        "last_7d": 0,
        "last_30d": 0
    }
    
    now = datetime.now()
    day_ago = (now.replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
    week_ago = (now.replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
    month_ago = (now.replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
    
    try:
        # Get counts for each time period
        result_24h = get_all_traces(user_id=user_id, start_date=day_ago, limit=10000, db_path=db_path)
        result_7d = get_all_traces(user_id=user_id, start_date=week_ago, limit=10000, db_path=db_path)
        result_30d = get_all_traces(user_id=user_id, start_date=month_ago, limit=10000, db_path=db_path)
        result_all = get_all_traces(user_id=user_id, limit=10000, db_path=db_path)
        
        stats["last_24h"] = result_24h["total"]
        stats["last_7d"] = result_7d["total"]
        stats["last_30d"] = result_30d["total"]
        stats["total"] = result_all["total"]
        
        # Count by type
        for trace in result_all["traces"]:
            trace_type = trace["trace_type"]
            stats["by_type"][trace_type] = stats["by_type"].get(trace_type, 0) + 1
    
    except Exception as e:
        logger.error(f"Error calculating trace stats: {e}")
    
    return stats







