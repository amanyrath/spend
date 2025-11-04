import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Initialize Firebase Admin
# Support both local file and Vercel environment variable
_initialized = False

def initialize_firebase():
    """Initialize Firebase Admin SDK with proper credentials"""
    global _initialized
    if _initialized:
        return
    
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
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'firebase-service-account.json')
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase service account file not found: {cred_path}. "
                "Set GOOGLE_APPLICATION_CREDENTIALS or FIREBASE_SERVICE_ACCOUNT environment variable."
            )
        cred = credentials.Certificate(cred_path)
        with open(cred_path) as f:
            sa_data = json.load(f)
            print(f"Using Firebase service account from file: {sa_data.get('client_email', 'unknown')}")

    # Only initialize if not already initialized
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        _initialized = True

# Initialize on import
initialize_firebase()

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

def get_persona_assignments(user_id):
    """Get all persona assignments for a user"""
    from firebase_admin import firestore
    personas_ref = db.collection('users').document(user_id)\
                     .collection('persona_assignments')\
                     .order_by('assigned_at', direction=firestore.Query.DESCENDING)
    return [doc.to_dict() for doc in personas_ref.stream()]

def get_recommendations(user_id):
    """Get all recommendations for a user"""
    from firebase_admin import firestore
    recs_ref = db.collection('users').document(user_id)\
                 .collection('recommendations')\
                 .order_by('shown_at', direction=firestore.Query.DESCENDING)
    return [doc.to_dict() for doc in recs_ref.stream()]

def get_user_transactions(user_id, start_date=None):
    """Get all transactions for a user, optionally filtered by date"""
    transactions_ref = db.collection('users').document(user_id)\
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
    accounts_ref = db.collection('users').document(user_id)\
                     .collection('accounts')
    
    all_accounts = [doc.to_dict() for doc in accounts_ref.stream()]
    
    if account_type:
        all_accounts = [acc for acc in all_accounts if acc.get('type') == account_type]
    
    if subtype:
        all_accounts = [acc for acc in all_accounts if acc.get('subtype') == subtype]
    
    return all_accounts