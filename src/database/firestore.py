import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import socket
from typing import List, Dict, Any, Optional

def is_port_open(host: str, port: int) -> bool:
    """Check if a port is open (i.e., service is running)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def auto_detect_emulator():
    """Automatically detect if Firebase emulator is running and set environment variable."""
    # Skip auto-detection if SQLite is explicitly requested
    if os.getenv('USE_SQLITE', '').lower() == 'true':
        return
    
    # Only auto-detect if not already set
    if os.getenv('FIRESTORE_EMULATOR_HOST') is None:
        # Check if emulator is explicitly requested
        if os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true':
            os.environ['FIRESTORE_EMULATOR_HOST'] = '127.0.0.1:8080'
        # Auto-detect: check if port 8080 is open on localhost or 127.0.0.1
        elif is_port_open('localhost', 8080) or is_port_open('127.0.0.1', 8080):
            # Prefer 127.0.0.1 as it matches firebase.json configuration
            os.environ['FIRESTORE_EMULATOR_HOST'] = '127.0.0.1:8080'
            # Optionally print a message (but only once)
            if not os.getenv('_FIRESTORE_AUTO_DETECTED'):
                print("✓ Auto-detected Firebase emulator running on 127.0.0.1:8080")
                os.environ['_FIRESTORE_AUTO_DETECTED'] = 'true'

# Auto-detect emulator on import
auto_detect_emulator()

# Initialize Firebase Admin
# Support both local file and Vercel environment variable
_initialized = False

def initialize_firebase():
    """Initialize Firebase Admin SDK with proper credentials or emulator"""
    global _initialized
    if _initialized:
        return
    
    # Skip Firebase initialization if SQLite is explicitly requested
    if os.getenv('USE_SQLITE', '').lower() == 'true':
        _initialized = True
        return
    
    # Check if Firebase emulator is enabled
    use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None or os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
    
    if use_emulator:
        # Use Firebase emulator for local development
        emulator_host = os.getenv('FIRESTORE_EMULATOR_HOST', 'localhost:8080')
        print("=" * 60)
        print("🔥 INITIALIZING FIREBASE EMULATOR")
        print("=" * 60)
        print(f"📍 Target: {emulator_host}")
        print("=" * 60)
        
        # Initialize Firebase Admin for emulator
        # The emulator doesn't validate credentials, but SDK needs valid format
        if not firebase_admin._apps:
            # Use service account file if available (real or dummy - emulator doesn't care)
            cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-service-account.json')
            if os.path.exists(cred_path):
                try:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                except Exception as e:
                    print(f"Warning: Failed to load service account file: {e}")
                    print("Trying to continue with emulator...")
                    # If file exists but is invalid, try to initialize anyway
                    # The emulator may still work
                    try:
                        firebase_admin.initialize_app(options={'projectId': 'demo-project'})
                    except Exception:
                        pass
            else:
                # No service account file - try to initialize with minimal config
                # This may fail, but emulator should still work if FIRESTORE_EMULATOR_HOST is set
                try:
                    firebase_admin.initialize_app(options={'projectId': 'demo-project'})
                except Exception:
                    pass
        _initialized = True
        return
    
    # Check if Firebase credentials exist before trying to initialize
    has_env_var = os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-service-account.json')
    has_file = os.path.exists(cred_path)
    
    if not has_env_var and not has_file:
        # No Firebase credentials - skip initialization (will use SQLite)
        _initialized = True
        return
    
    # Production Firebase - warn before initializing
    print("=" * 60)
    print("🔥 INITIALIZING FIREBASE PRODUCTION")
    print("=" * 60)
    print("⚠️  WARNING: Connecting to Firebase PRODUCTION environment")
    if has_file:
        print(f"📁 Using credentials file: {cred_path}")
    if has_env_var:
        print("📁 Using credentials from FIREBASE_SERVICE_ACCOUNT environment variable")
    print("=" * 60)
    
    if os.getenv('FIREBASE_SERVICE_ACCOUNT'):
        # Vercel: service account is stored as JSON string in environment variable
        try:
            service_account_json = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
            cred = credentials.Certificate(service_account_json)
            print(f"Using Firebase service account from environment: {service_account_json.get('client_email', 'unknown')}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid FIREBASE_SERVICE_ACCOUNT JSON: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse FIREBASE_SERVICE_ACCOUNT: {e}")
    else:
        # Local: use service account file
        cred = credentials.Certificate(cred_path)
        with open(cred_path) as f:
            sa_data = json.load(f)
            print(f"Using Firebase service account from file: {sa_data.get('client_email', 'unknown')}")

    # Only initialize if not already initialized
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        _initialized = True

# Initialize on import (will gracefully skip if no credentials)
initialize_firebase()

# Only create db client if Firebase was initialized and credentials exist
_db = None

def get_db():
    """Get Firestore client, initializing if needed"""
    global _db
    if _db is None:
        # Skip Firebase if SQLite is explicitly requested
        if os.getenv('USE_SQLITE', '').lower() == 'true':
            _db = None
            return None
        
        # Re-check for emulator (in case it was started after module import)
        auto_detect_emulator()
        
        # Check if Firebase emulator is enabled
        use_emulator = os.getenv('FIRESTORE_EMULATOR_HOST') is not None or os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true'
        
        # Check if Firebase credentials exist
        has_env_var = os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-service-account.json')
        has_file = os.path.exists(cred_path)
        
        if use_emulator or has_env_var or has_file:
            initialize_firebase()
            _db = firestore.client()
        else:
            # Return None if no Firebase credentials (will use SQLite instead)
            _db = None
    return _db

db = None  # Will be set by get_db() if Firebase is available

def get_collection(collection_name):
    """Get Firestore collection reference"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    return client.collection(collection_name)

def store_user(user_data):
    """Store user in Firestore"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    user_ref = client.collection('users').document(user_data['user_id'])
    user_ref.set(user_data)
    return user_data['user_id']

def store_feature(user_id, signal_type, signal_data, time_window):
    """Store computed feature"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    feature_ref = client.collection('users').document(user_id)\
                    .collection('computed_features').document()
    feature_ref.set({
        'signal_type': signal_type,
        'signal_data': signal_data,
        'time_window': time_window,
        'computed_at': firestore.SERVER_TIMESTAMP
    })

def get_user_features(user_id, time_window=None):
    """Get user's computed features"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    features_ref = client.collection('users').document(user_id)\
                     .collection('computed_features')
    
    if time_window:
        features_ref = features_ref.where('time_window', '==', time_window)
    
    return [doc.to_dict() for doc in features_ref.stream()]

def store_persona(user_id, persona_data):
    """Store persona assignment"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    persona_ref = client.collection('users').document(user_id)\
                    .collection('persona_assignments').document()
    persona_ref.set(persona_data)

def store_recommendation(user_id, recommendation_data):
    """Store recommendation"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    rec_ref = client.collection('users').document(user_id)\
                .collection('recommendations').document()
    rec_ref.set(recommendation_data)
    return rec_ref.id

def get_all_users():
    """Get all users"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    users_ref = client.collection('users')
    return [{'user_id': doc.id, **doc.to_dict()} for doc in users_ref.stream()]

def get_user(user_id):
    """Get single user"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    user_ref = client.collection('users').document(user_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        return {'user_id': user_id, **user_doc.to_dict()}
    return None

def get_persona_assignments(user_id):
    """Get all persona assignments for a user"""
    from firebase_admin import firestore
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    personas_ref = client.collection('users').document(user_id)\
                     .collection('persona_assignments')\
                     .order_by('assigned_at', direction=firestore.Query.DESCENDING)
    return [doc.to_dict() for doc in personas_ref.stream()]

def get_recommendations(user_id):
    """Get all recommendations for a user"""
    from firebase_admin import firestore
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    recs_ref = client.collection('users').document(user_id)\
                 .collection('recommendations')\
                 .order_by('shown_at', direction=firestore.Query.DESCENDING)
    return [doc.to_dict() for doc in recs_ref.stream()]

def get_user_transactions(user_id, start_date=None):
    """Get all transactions for a user, optionally filtered by date"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    transactions_ref = client.collection('users').document(user_id)\
                         .collection('transactions')
    
    # Firestore doesn't support direct date filtering without index
    # Get all and filter in Python for now
    all_transactions = [doc.to_dict() for doc in transactions_ref.stream()]
    
    if start_date:
        # Filter transactions >= start_date
        filtered = []
        for txn in all_transactions:
            txn_date = txn.get('date', '')
            if txn_date >= start_date:
                filtered.append(txn)
        return filtered
    
    return all_transactions

def get_user_accounts(user_id, account_type=None, subtype=None):
    """Get accounts for a user, optionally filtered by type or subtype"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    accounts_ref = client.collection('users').document(user_id)\
                     .collection('accounts')
    
    all_accounts = [doc.to_dict() for doc in accounts_ref.stream()]
    
    if account_type:
        all_accounts = [acc for acc in all_accounts if acc.get('type') == account_type]
    
    if subtype:
        all_accounts = [acc for acc in all_accounts if acc.get('subtype') == subtype]
    
    return all_accounts

def store_chat_log(user_id, message, response, citations, guardrails_passed):
    """Store chat log entry"""
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    chat_log_ref = client.collection('users').document(user_id)\
                     .collection('chat_logs').document()
    chat_log_ref.set({
        'user_id': user_id,
        'message': message,
        'response': response,
        'citations': citations,
        'guardrails_passed': guardrails_passed,
        'created_at': firestore.SERVER_TIMESTAMP
    })
    return chat_log_ref.id


# Batch write functions for processed data

def store_feature_batch(features: List[Dict[str, Any]], batch_size: int = 500):
    """Batch store multiple features.
    
    Args:
        features: List of feature dictionaries, each must have:
                  {'user_id': str, 'signal_type': str, 'signal_data': dict, 'time_window': str}
        batch_size: Batch size (default: 500, max: 500).
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    batch = client.batch()
    count = 0
    batches_committed = 0
    
    for feature in features:
        user_id = feature['user_id']
        feature_ref = client.collection('users').document(user_id)\
                          .collection('computed_features').document()
        batch.set(feature_ref, {
            'signal_type': feature['signal_type'],
            'signal_data': feature['signal_data'],
            'time_window': feature['time_window'],
            'computed_at': firestore.SERVER_TIMESTAMP
        })
        count += 1
        
        if count % batch_size == 0:
            batch.commit()
            batch = client.batch()
            batches_committed += 1
    
    # Commit remaining
    if count % batch_size != 0:
        batch.commit()
        batches_committed += 1
    
    return count


def store_persona_batch(personas: List[Dict[str, Any]], batch_size: int = 500):
    """Batch store multiple persona assignments.
    
    Args:
        personas: List of persona dictionaries, each must have:
                  {'user_id': str, 'time_window': str, 'persona': str, ...}
        batch_size: Batch size (default: 500, max: 500).
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    batch = client.batch()
    count = 0
    batches_committed = 0
    
    for persona in personas:
        user_id = persona['user_id']
        persona_ref = client.collection('users').document(user_id)\
                          .collection('persona_assignments').document()
        batch.set(persona_ref, persona)
        count += 1
        
        if count % batch_size == 0:
            batch.commit()
            batch = client.batch()
            batches_committed += 1
    
    # Commit remaining
    if count % batch_size != 0:
        batch.commit()
        batches_committed += 1
    
    return count


def store_recommendation_batch(recommendations: List[Dict[str, Any]], batch_size: int = 500):
    """Batch store multiple recommendations.
    
    Args:
        recommendations: List of recommendation dictionaries, each must have:
                         {'user_id': str, 'type': str, ...}
        batch_size: Batch size (default: 500, max: 500).
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    batch = client.batch()
    count = 0
    batches_committed = 0
    
    for rec in recommendations:
        user_id = rec['user_id']
        rec_ref = client.collection('users').document(user_id)\
                      .collection('recommendations').document()
        batch.set(rec_ref, rec)
        count += 1
        
        if count % batch_size == 0:
            batch.commit()
            batch = client.batch()
            batches_committed += 1
    
    # Commit remaining
    if count % batch_size != 0:
        batch.commit()
        batches_committed += 1
    
    return count


# Batch read functions for loading data

def get_all_features(time_window: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all features for all users (for loading to SQLite).
    
    Args:
        time_window: Optional time window filter (e.g., "30d", "180d").
        
    Returns:
        List of all features with user_id included.
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    all_features = []
    users_ref = client.collection('users')
    
    for user_doc in users_ref.stream():
        user_id = user_doc.id
        features_ref = user_doc.reference.collection('computed_features')
        
        if time_window:
            features_ref = features_ref.where('time_window', '==', time_window)
        
        for feature_doc in features_ref.stream():
            feature_data = feature_doc.to_dict()
            feature_data['user_id'] = user_id  # Add user_id for SQLite loading
            all_features.append(feature_data)
    
    return all_features


def get_all_personas(time_window: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all persona assignments for all users (for loading to SQLite).
    
    Args:
        time_window: Optional time window filter (e.g., "30d", "180d").
        
    Returns:
        List of all persona assignments with user_id included.
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    all_personas = []
    users_ref = client.collection('users')
    
    for user_doc in users_ref.stream():
        user_id = user_doc.id
        personas_ref = user_doc.reference.collection('persona_assignments')
        
        if time_window:
            personas_ref = personas_ref.where('time_window', '==', time_window)
        
        for persona_doc in personas_ref.stream():
            persona_data = persona_doc.to_dict()
            persona_data['user_id'] = user_id  # Add user_id for SQLite loading
            all_personas.append(persona_data)
    
    return all_personas


def get_all_recommendations() -> List[Dict[str, Any]]:
    """Get all recommendations for all users (for loading to SQLite).
    
    Returns:
        List of all recommendations with user_id included.
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    all_recommendations = []
    users_ref = client.collection('users')
    
    for user_doc in users_ref.stream():
        user_id = user_doc.id
        recs_ref = user_doc.reference.collection('recommendations')
        
        for rec_doc in recs_ref.stream():
            rec_data = rec_doc.to_dict()
            rec_data['user_id'] = user_id  # Add user_id for SQLite loading
            rec_data['recommendation_id'] = rec_doc.id  # Add recommendation_id
            all_recommendations.append(rec_data)
    
    return all_recommendations


def store_operator_action(
    operator_id: str,
    user_id: str,
    action_type: str,
    reason: str,
    recommendation_id: Optional[str] = None
) -> str:
    """Store an operator action in the audit trail.
    
    Args:
        operator_id: ID of the operator performing the action
        user_id: ID of the user the action is performed on
        action_type: Type of action ('override' or 'flag')
        reason: Reason for the action
        recommendation_id: ID of recommendation (for override actions, None for flag)
        
    Returns:
        ID of the created action document
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    action_ref = client.collection('users').document(user_id)\
                       .collection('operator_actions').document()
    
    action_data = {
        'operator_id': operator_id,
        'user_id': user_id,
        'action_type': action_type,
        'reason': reason,
        'created_at': firestore.SERVER_TIMESTAMP
    }
    
    if recommendation_id:
        action_data['recommendation_id'] = recommendation_id
    
    action_ref.set(action_data)
    return action_ref.id


def get_operator_actions(
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get operator actions from the audit trail.
    
    Args:
        user_id: Filter by user_id (required)
        action_type: Filter by action_type (optional)
        limit: Maximum number of results (optional)
        offset: Number of results to skip
        
    Returns:
        List of operator action records
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    if not user_id:
        return []
    
    actions_ref = client.collection('users').document(user_id)\
                        .collection('operator_actions')
    
    if action_type:
        actions_ref = actions_ref.where('action_type', '==', action_type)
    
    # Order by created_at descending
    actions_ref = actions_ref.order_by('created_at', direction=firestore.Query.DESCENDING)
    
    # Apply pagination
    if offset > 0:
        # Firestore doesn't support offset directly, need to use start_after
        # For simplicity, we'll fetch all and slice (fine for small datasets)
        pass
    
    actions = []
    for action_doc in actions_ref.stream():
        action_data = action_doc.to_dict()
        action_data['id'] = action_doc.id
        actions.append(action_data)
    
    # Apply offset and limit manually (Firestore limitation)
    if offset > 0:
        actions = actions[offset:]
    
    if limit:
        actions = actions[:limit]
    
    return actions


def get_consent_status(user_id: str) -> Optional[Dict[str, Any]]:
    """Get consent status for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with granted, timestamp, version
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    user_ref = client.collection('users').document(user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return {"granted": False, "timestamp": None, "version": None}
    
    user_data = user_doc.to_dict()
    return {
        "granted": user_data.get("consent_status", False),
        "timestamp": user_data.get("consent_timestamp"),
        "version": user_data.get("consent_version", "1.0")
    }


def store_consent(
    user_id: str,
    granted: bool,
    ip_address: Optional[str] = None,
    version: str = "1.0"
) -> None:
    """Store or update user consent.
    
    Args:
        user_id: User ID
        granted: Whether consent is granted
        ip_address: IP address of the request (optional)
        version: Consent version (default: "1.0")
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized. Ensure FIREBASE_SERVICE_ACCOUNT is set or firebase-service-account.json exists.")
    
    user_ref = client.collection('users').document(user_id)
    
    update_data = {
        'consent_status': granted,
        'consent_version': version
    }
    
    if granted:
        update_data['consent_timestamp'] = firestore.SERVER_TIMESTAMP
    else:
        update_data['consent_timestamp'] = None
    
    user_ref.update(update_data)
    
    # Log consent action to audit trail
    audit_ref = client.collection('consent_audit_log').document()
    audit_ref.set({
        'user_id': user_id,
        'action': 'granted' if granted else 'revoked',
        'ip_address': ip_address or 'unknown',
        'timestamp': firestore.SERVER_TIMESTAMP
    })


def revoke_consent(user_id: str) -> None:
    """Revoke user consent.
    
    Args:
        user_id: User ID
    """
    store_consent(user_id, granted=False)


def get_all_chat_logs_firestore(
    user_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> list:
    """Get chat logs with optional filtering from Firestore.
    
    Args:
        user_id: Filter by user_id (optional)
        limit: Maximum number of results (optional)
        offset: Number of results to skip
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        
    Returns:
        List of chat log records
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized")
    
    if user_id:
        # Query specific user's chat logs
        query = client.collection('users').document(user_id).collection('chat_logs')
    else:
        # Query all chat logs across users
        query = client.collection_group('chat_logs')
    
    if start_date:
        query = query.where('created_at', '>=', start_date)
    if end_date:
        query = query.where('created_at', '<=', end_date)
    
    query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
    
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    
    docs = query.stream()
    return [{'id': doc.id, **doc.to_dict()} for doc in docs]


def get_recommendation_traces_firestore(
    user_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> list:
    """Get recommendations with optional filtering from Firestore.
    
    Args:
        user_id: Filter by user_id (optional)
        limit: Maximum number of results (optional)
        offset: Number of results to skip
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        
    Returns:
        List of recommendation records
    """
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase not initialized")
    
    if user_id:
        query = client.collection('users').document(user_id).collection('recommendations')
    else:
        query = client.collection_group('recommendations')
    
    if start_date:
        query = query.where('shown_at', '>=', start_date)
    if end_date:
        query = query.where('shown_at', '<=', end_date)
    
    query = query.order_by('shown_at', direction=firestore.Query.DESCENDING)
    
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    
    docs = query.stream()
    return [{'recommendation_id': doc.id, **doc.to_dict()} for doc in docs]


def get_timeline_events_firestore(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, list]:
    """Get all timeline events for a user from Firestore.
    
    Args:
        user_id: User ID
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        
    Returns:
        Dictionary with lists of different event types
    """
    return {
        "chat_logs": get_all_chat_logs_firestore(user_id, start_date=start_date, end_date=end_date),
        "recommendations": get_recommendation_traces_firestore(user_id, start_date=start_date, end_date=end_date),
        "operator_actions": get_operator_actions(user_id, start_date=start_date, end_date=end_date),
    }