"""Signal detection module for SpendSense.

This module implements detection algorithms for various financial behavior signals:
- Subscription detection
- Credit utilization detection
- Savings behavior detection
- Income stability detection
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import statistics
import os

# Make SQLite imports optional for Vercel deployment
try:
    from src.database import db
    HAS_SQLITE = True
except ImportError:
    # SQLite not available - use Firestore only
    HAS_SQLITE = False
    db = None

from src.database.firestore import get_user_transactions, get_user_accounts, store_feature as firestore_store_feature, get_user_features as firestore_get_user_features
from src.utils.category_utils import normalize_category, get_primary_category, category_contains

# Use Firestore if emulator is enabled, service account env var is set, or service account file exists
USE_FIRESTORE = (
    os.getenv('FIRESTORE_EMULATOR_HOST') is not None or 
    os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true' or
    os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None or 
    os.path.exists('firebase-service-account.json')
)


class DictRow:
    """Mock Row class to make Firestore dicts compatible with SQLite Row interface"""
    def __init__(self, data):
        self._data = data
    
    def __getitem__(self, key):
        return self._data.get(key)
    
    def get(self, key, default=None):
        return self._data.get(key, default)


def _is_irregular_frequency(median_pay_gap: float, intervals: List[float]) -> bool:
    """Determine if pay frequency is irregular based on median gap and variance.
    
    Args:
        median_pay_gap: Median days between paychecks
        intervals: List of intervals between paychecks in days
        
    Returns:
        True if frequency is irregular, False otherwise
    """
    # Check if median gap matches known regular patterns
    if 6 <= median_pay_gap <= 8:  # Weekly
        return False
    elif 13 <= median_pay_gap <= 15:  # Biweekly
        return False
    elif 28 <= median_pay_gap <= 31:  # Monthly
        return False
    
    # If median doesn't match patterns, check variance
    if len(intervals) > 1:
        std_dev = statistics.stdev(intervals)
        # High variance indicates irregularity
        return std_dev > 7
    
    return True  # Default to irregular if unclear


def _get_transactions(user_id: str, cutoff_date: str, filters: Dict[str, Any] = None) -> List:
    """Get transactions from either SQLite or Firestore"""
    if USE_FIRESTORE:
        transactions = get_user_transactions(user_id, cutoff_date)
        # Apply filters
        filtered = []
        for txn in transactions:
            if filters:
                if filters.get('amount_lt') and txn.get('amount', 0) >= filters['amount_lt']:
                    continue
                if filters.get('amount_gt') and txn.get('amount', 0) <= filters['amount_gt']:
                    continue
                if filters.get('category') and not category_contains(txn.get('category', ''), filters['category']):
                    continue
            filtered.append(DictRow(txn))
        return filtered
    else:
        # SQLite path
        where_clauses = ["user_id = ?", "date >= ?"]
        params = [user_id, cutoff_date]
        
        if filters:
            if filters.get('amount_lt'):
                where_clauses.append("amount < ?")
                params.append(filters['amount_lt'])
            if filters.get('amount_gt'):
                where_clauses.append("amount > ?")
                params.append(filters['amount_gt'])
        
        query = f"""
            SELECT merchant_name, date, amount, category, account_id,
                   payment_channel, authorized_date, location_city, location_region, iso_currency_code
            FROM transactions
            WHERE {' AND '.join(where_clauses)}
            ORDER BY date
        """
        return db.fetch_all(query, tuple(params))


def _get_accounts(user_id: str, account_type: str = None, subtype: str = None) -> List:
    """Get accounts from either SQLite or Firestore"""
    if USE_FIRESTORE:
        accounts = get_user_accounts(user_id, account_type, subtype)
        return [DictRow(acc) for acc in accounts]
    else:
        # SQLite path
        where_clauses = ["user_id = ?"]
        params = [user_id]
        
        if account_type:
            where_clauses.append("type = ?")
            params.append(account_type)
        if subtype:
            where_clauses.append("subtype = ?")
            params.append(subtype)
        
        query = f"""
            SELECT account_id, balance, "limit", type, subtype
            FROM accounts
            WHERE {' AND '.join(where_clauses)}
        """
        return db.fetch_all(query, tuple(params))


def _get_date_window_days_ago(days: int) -> str:
    """Helper function to get date string N days ago.
    
    Args:
        days: Number of days ago
        
    Returns:
        ISO format date string
    """
    date = datetime.now() - timedelta(days=days)
    return date.strftime("%Y-%m-%d")


def _parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object.
    
    Args:
        date_str: ISO format date string
        
    Returns:
        datetime object
    """
    return datetime.fromisoformat(date_str)


def detect_subscriptions(user_id: str, window_days: int = 90) -> Dict[str, Any]:
    """Detect recurring subscription patterns from transaction history.
    
    Logic:
    - Group transactions by merchant name
    - Find merchants with >= 3 occurrences
    - Check for regular cadence (monthly ±3 days, weekly ±1 day)
    - Prioritize online transactions for subscription detection
    - Calculate monthly recurring total
    - Calculate subscription share of total spend
    - Use authorized_date if available, fall back to date
    
    Args:
        user_id: User identifier
        window_days: Number of days to look back
        
    Returns:
        Dictionary with subscription signals:
        - recurring_merchants: List of merchant names with recurring patterns
        - monthly_recurring: Total monthly recurring amount
        - subscription_share: Percentage of total spend that is subscriptions
        - merchant_details: List of dicts with merchant, frequency, amount, payment_channel
    """
    cutoff_date = _get_date_window_days_ago(window_days)
    
    # Get all transactions for user in the window
    transactions = _get_transactions(user_id, cutoff_date, filters={'amount_lt': 0})
    
    if not transactions:
        return {
            "recurring_merchants": [],
            "monthly_recurring": 0.0,
            "subscription_share": 0.0,
            "merchant_details": []
        }
    
    # Group transactions by merchant
    merchant_transactions = defaultdict(list)
    total_spend = 0.0
    
    for tx in transactions:
        merchant = tx["merchant_name"] or "Unknown"
        # Use authorized_date if available, otherwise fall back to date
        tx_date = tx.get("authorized_date") or tx["date"]
        merchant_transactions[merchant].append({
            "date": _parse_date(tx_date),
            "amount": abs(tx["amount"]),
            "payment_channel": tx.get("payment_channel")
        })
        total_spend += abs(tx["amount"])
    
    # Find recurring patterns
    recurring_merchants = []
    merchant_details = []
    monthly_recurring = 0.0
    
    for merchant, txs in merchant_transactions.items():
        if len(txs) < 3:
            continue
        
        # Sort by date
        txs.sort(key=lambda x: x["date"])
        
        # Count online vs other payment channels
        online_count = sum(1 for tx in txs if tx.get("payment_channel") == "online")
        online_ratio = online_count / len(txs) if txs else 0.0
        
        # Prioritize merchants with online transactions (more likely to be subscriptions)
        # But still include in-store recurring patterns
        is_likely_subscription = online_ratio >= 0.5
        
        # Calculate intervals between transactions
        intervals = []
        amounts = []
        for i in range(1, len(txs)):
            delta = (txs[i]["date"] - txs[i-1]["date"]).days
            intervals.append(delta)
            amounts.append(txs[i]["amount"])
        
        avg_amount = statistics.mean(amounts) if amounts else 0.0
        
        # Check for monthly pattern (28-31 days, ±3 days tolerance)
        avg_interval = statistics.mean(intervals) if intervals else 0.0
        is_monthly = 25 <= avg_interval <= 34
        
        # Check for weekly pattern (7 days, ±1 day tolerance)
        is_weekly = 6 <= avg_interval <= 8
        
        # If it's a likely subscription (online) or has regular pattern, include it
        if (is_monthly or is_weekly) and (is_likely_subscription or len(txs) >= 4):
            recurring_merchants.append(merchant)
            
            # Calculate monthly cost
            if is_monthly:
                monthly_cost = avg_amount
            elif is_weekly:
                monthly_cost = avg_amount * 4.33  # Approximate weeks per month
            
            monthly_recurring += monthly_cost
            
            # Determine primary payment channel
            payment_channels = [tx.get("payment_channel") for tx in txs if tx.get("payment_channel")]
            primary_channel = max(set(payment_channels), key=payment_channels.count) if payment_channels else None
            
            merchant_details.append({
                "merchant": merchant,
                "frequency": "monthly" if is_monthly else "weekly",
                "amount": avg_amount,
                "monthly_equivalent": monthly_cost,
                "occurrences": len(txs),
                "payment_channel": primary_channel,
                "online_ratio": round(online_ratio, 2)
            })
    
    subscription_share = (monthly_recurring / total_spend * 100) if total_spend > 0 else 0.0
    
    return {
        "recurring_merchants": recurring_merchants,
        "monthly_recurring": round(monthly_recurring, 2),
        "subscription_share": round(subscription_share, 2),
        "merchant_details": merchant_details
    }


def detect_credit_utilization(user_id: str, window_days: int = 30) -> Dict[str, Any]:
    """Detect credit utilization patterns and behaviors.
    
    Logic:
    - For each credit account: utilization = balance / limit
    - Flag: high (≥50%), medium (30-50%), low (<30%)
    - Detect minimum payment only (last_payment ≈ minimum_payment within $5)
    - Sum interest charges from transactions
    - Analyze spending patterns using payment_channel (online vs in-store)
    - Check overdue status from liabilities (if available)
    - Use authorized_date for payment timing when available
    
    Args:
        user_id: User identifier
        window_days: Number of days to look back
        
    Returns:
        Dictionary with credit utilization signals:
        - total_utilization: Overall utilization percentage
        - utilization_level: "high", "medium", or "low"
        - accounts: List of account-level details
        - interest_charged: Total interest charged in window
        - minimum_payment_only: Boolean indicating if only minimum payments made
        - is_overdue: Boolean indicating if any account is overdue
        - online_spending_share: Percentage of credit spending that is online
    """
    cutoff_date = _get_date_window_days_ago(window_days)
    
    # Get all credit accounts for user
    credit_accounts = _get_accounts(user_id, account_type='credit')
    # Filter out accounts with no limit
    credit_accounts = [acc for acc in credit_accounts if acc.get("limit", 0) > 0]
    
    if not credit_accounts:
        return {
            "total_utilization": 0.0,
            "utilization_level": "low",
            "accounts": [],
            "interest_charged": 0.0,
            "minimum_payment_only": False,
            "is_overdue": False,
            "online_spending_share": 0.0
        }
    
    # Get recent payments and interest charges
    account_ids = [acc["account_id"] for acc in credit_accounts]
    
    if USE_FIRESTORE:
        # Get all transactions for user
        all_txns = get_user_transactions(user_id, cutoff_date)
        # Filter for credit account transactions
        payments = [DictRow(txn) for txn in all_txns 
                   if txn.get('account_id') in account_ids and txn.get('amount', 0) > 0]
        
        # Get spending transactions (negative amounts) for payment channel analysis
        spending_txns = [DictRow(txn) for txn in all_txns 
                        if txn.get('account_id') in account_ids and txn.get('amount', 0) < 0]
        
        # Calculate interest charges
        interest_map = {}
        for account_id in account_ids:
            account_txns = [txn for txn in all_txns 
                          if txn.get('account_id') == account_id 
                          and txn.get('amount', 0) < 0
                          and cutoff_date <= txn.get('date', '')]
            total_interest = sum(abs(txn.get('amount', 0)) for txn in account_txns
                               if category_contains(txn.get('category', ''), 'interest')
                               or 'interest' in str(txn.get('merchant_name', '')).lower()
                               or category_contains(txn.get('category', ''), 'fee'))
            interest_map[account_id] = total_interest
    else:
        # SQLite path
        placeholders = ",".join(["?"] * len(account_ids))
        payments_query = f"""
            SELECT account_id, date, amount, merchant_name, category,
                   payment_channel, authorized_date, iso_currency_code
            FROM transactions
            WHERE account_id IN ({placeholders}) 
            AND date >= ? 
            AND amount > 0
            ORDER BY date DESC
        """
        payments = db.fetch_all(payments_query, tuple(account_ids) + (cutoff_date,))
        
        # Get spending transactions for payment channel analysis
        spending_query = f"""
            SELECT account_id, amount, payment_channel
            FROM transactions
            WHERE account_id IN ({placeholders})
            AND date >= ?
            AND amount < 0
        """
        spending_txns = db.fetch_all(spending_query, tuple(account_ids) + (cutoff_date,))
        
        # Fetch transactions and filter by category in Python (handles JSON arrays)
        interest_query = f"""
            SELECT account_id, amount, merchant_name, category,
                   payment_channel, authorized_date, iso_currency_code
            FROM transactions
            WHERE account_id IN ({placeholders})
            AND date >= ?
            AND amount < 0
        """
        all_transactions = db.fetch_all(interest_query, tuple(account_ids) + (cutoff_date,))
        
        # Filter transactions by category using category_contains (handles JSON arrays)
        interest_by_account = defaultdict(float)
        for txn in all_transactions:
            account_id = txn["account_id"]
            category = txn.get("category", "")
            merchant_name = str(txn.get("merchant_name", "")).lower()
            
            # Check if transaction is interest or fee related
            is_interest = (category_contains(category, 'interest') or 
                          category_contains(category, 'fee') or
                          'interest' in merchant_name)
            
            if is_interest:
                interest_by_account[account_id] += abs(txn["amount"])
        
        interest_map = dict(interest_by_account)
    
    # Calculate payment channel distribution (online vs in-store)
    total_spending = 0.0
    online_spending = 0.0
    
    for txn in spending_txns:
        amount = abs(txn.get("amount", 0))
        total_spending += amount
        if txn.get("payment_channel") == "online":
            online_spending += amount
    
    online_spending_share = (online_spending / total_spending * 100) if total_spending > 0 else 0.0
    
    # Calculate utilization for each account
    accounts_detail = []
    total_balance = 0.0
    total_limit = 0.0
    total_interest = 0.0
    
    for acc in credit_accounts:
        account_id = acc["account_id"]
        balance = acc["balance"] or 0.0
        limit = acc["limit"] or 1.0  # Avoid division by zero
        
        utilization = (balance / limit) * 100 if limit > 0 else 0.0
        
        # Find recent payments for this account
        account_payments = [p for p in payments if p["account_id"] == account_id]
        
        # Check if only minimum payments (heuristic: payment amount is small relative to balance)
        minimum_payment_only = False
        if account_payments:
            # Use authorized_date if available for more accurate payment timing
            recent_payment = account_payments[0]
            payment_date = recent_payment.get("authorized_date") or recent_payment["date"]
            
            # Estimate minimum payment as ~2% of balance or $25, whichever is higher
            estimated_min = max(balance * 0.02, 25.0)
            payment_amount = recent_payment["amount"]
            if abs(payment_amount - estimated_min) <= 5.0:
                minimum_payment_only = True
        
        interest_charged = interest_map.get(account_id, 0.0)
        total_interest += interest_charged
        
        accounts_detail.append({
            "account_id": account_id,
            "balance": balance,
            "limit": limit,
            "utilization": round(utilization, 2),
            "utilization_level": "high" if utilization >= 50 else "medium" if utilization >= 30 else "low",
            "interest_charged": round(interest_charged, 2),
            "minimum_payment_only": minimum_payment_only
        })
        
        total_balance += balance
        total_limit += limit
    
    # Calculate overall utilization
    overall_utilization = (total_balance / total_limit * 100) if total_limit > 0 else 0.0
    
    if overall_utilization >= 50:
        utilization_level = "high"
    elif overall_utilization >= 30:
        utilization_level = "medium"
    else:
        utilization_level = "low"
    
    # Check if any account has minimum payment only pattern
    any_minimum_only = any(acc["minimum_payment_only"] for acc in accounts_detail)
    
    # Note: overdue status would come from liabilities table if it exists
    # For now, we'll infer from high utilization and interest charges
    is_overdue = overall_utilization >= 90 or total_interest > 0
    
    return {
        "total_utilization": round(overall_utilization, 2),
        "utilization_level": utilization_level,
        "accounts": accounts_detail,
        "interest_charged": round(total_interest, 2),
        "minimum_payment_only": any_minimum_only,
        "is_overdue": is_overdue,
        "online_spending_share": round(online_spending_share, 2)
    }


def detect_savings_behavior(user_id: str, window_days: int = 180) -> Dict[str, Any]:
    """Detect savings account behavior patterns.
    
    Logic:
    - Identify savings accounts (type = savings, money market, HSA)
    - Calculate net inflow (deposits - withdrawals)
    - Filter out travel-related transactions (location changes)
    - Calculate growth rate: (current - 180d_ago) / 180d_ago
    - Calculate emergency fund coverage: savings / avg_monthly_expenses
    - Assign coverage flag: excellent/good/building/low
    
    Args:
        user_id: User identifier
        window_days: Number of days to look back
        
    Returns:
        Dictionary with savings behavior signals:
        - total_savings: Total balance across all savings accounts
        - net_inflow: Net deposits minus withdrawals in window (excluding travel)
        - growth_rate: Percentage growth rate
        - emergency_fund_coverage: Months of expenses covered
        - coverage_level: "excellent", "good", "building", or "low"
        - accounts: List of account-level details
        - avg_monthly_savings: Average monthly savings over last 90 days
        - travel_filtered_transactions: Count of transactions filtered due to location changes
    """
    cutoff_date = _get_date_window_days_ago(window_days)
    
    # Get savings accounts
    all_accounts = _get_accounts(user_id)
    savings_accounts = [acc for acc in all_accounts 
                       if acc.get('subtype') in ('savings', 'money market', 'hsa') 
                       or (acc.get('type') == 'depository' and 'savings' in str(acc.get('subtype', '')).lower())]
    
    if not savings_accounts:
        return {
            "total_savings": 0.0,
            "net_inflow": 0.0,
            "growth_rate": 0.0,
            "emergency_fund_coverage": 0.0,
            "coverage_level": "low",
            "accounts": [],
            "avg_monthly_savings": 0.0,
            "travel_filtered_transactions": 0
        }
    
    # Get historical balance if available (we'll use current balance as proxy)
    # For a real implementation, you'd track balance history
    # Here we'll calculate based on transaction flows
    
    account_ids = [acc["account_id"] for acc in savings_accounts]
    
    if USE_FIRESTORE:
        all_txns = get_user_transactions(user_id, cutoff_date)
        transactions = [DictRow(txn) for txn in all_txns if txn.get('account_id') in account_ids]
    else:
        placeholders = ",".join(["?"] * len(account_ids))
        transactions_query = f"""
            SELECT account_id, date, amount, location_city, location_region, iso_currency_code
            FROM transactions
            WHERE account_id IN ({placeholders}) AND date >= ?
            ORDER BY date
        """
        transactions = db.fetch_all(transactions_query, tuple(account_ids) + (cutoff_date,))
    
    # Calculate net inflow, filtering out travel-related transactions
    # Also calculate avg_monthly_savings using 90-day window (regardless of window_days)
    net_inflow = 0.0
    account_flows = defaultdict(float)
    travel_filtered_count = 0
    
    # For avg_monthly_savings, always use 90 days to get meaningful monthly average
    savings_window_days = 90
    savings_cutoff_date = _get_date_window_days_ago(savings_window_days)
    
    # Get transactions for monthly savings calculation (90 days)
    if USE_FIRESTORE:
        savings_txns = get_user_transactions(user_id, savings_cutoff_date)
        savings_transactions = [DictRow(txn) for txn in savings_txns if txn.get('account_id') in account_ids]
    else:
        placeholders = ",".join(["?"] * len(account_ids))
        savings_transactions_query = f"""
            SELECT account_id, date, amount, location_city, location_region, iso_currency_code
            FROM transactions
            WHERE account_id IN ({placeholders}) AND date >= ?
            ORDER BY date
        """
        savings_transactions = db.fetch_all(savings_transactions_query, tuple(account_ids) + (savings_cutoff_date,))
    
    # Track location changes to identify travel
    user_locations = set()  # Track all unique locations seen
    previous_location = None
    
    # Track monthly savings for avg_monthly_savings calculation
    monthly_savings = defaultdict(float)
    
    for tx in transactions:
        amount = tx["amount"]
        account_id = tx["account_id"]
        
        # Check for location change (travel detection)
        location_city = tx.get("location_city")
        location_region = tx.get("location_region")
        
        # Build location key
        location_key = None
        if location_city and location_region:
            location_key = f"{location_city},{location_region}"
        elif location_city:
            location_key = location_city
        
        # If we have location info and it differs from previous, likely travel
        is_travel_transaction = False
        if location_key and previous_location and location_key != previous_location:
            # Only filter if it's a significant change (different city/region)
            # Don't filter first transaction
            if location_key not in user_locations:
                is_travel_transaction = True
                travel_filtered_count += 1
        
        # Update location tracking
        if location_key:
            user_locations.add(location_key)
            previous_location = location_key
        
        # Only count non-travel transactions for savings calculations
        if not is_travel_transaction:
            account_flows[account_id] += amount
            net_inflow += amount
    
    # Calculate avg_monthly_savings from 90-day window transactions
    savings_user_locations = set()
    savings_previous_location = None
    
    for tx in savings_transactions:
        amount = tx["amount"]
        
        # Check for travel (same logic as above)
        location_city = tx.get("location_city")
        location_region = tx.get("location_region")
        
        location_key = None
        if location_city and location_region:
            location_key = f"{location_city},{location_region}"
        elif location_city:
            location_key = location_city
        
        is_travel_transaction = False
        if location_key and savings_previous_location and location_key != savings_previous_location:
            if location_key not in savings_user_locations:
                is_travel_transaction = True
        
        if location_key:
            savings_user_locations.add(location_key)
            savings_previous_location = location_key
        
        # Group by month for avg_monthly_savings (excluding travel)
        if not is_travel_transaction:
            tx_date = _parse_date(tx["date"])
            month_key = tx_date.strftime("%Y-%m")
            monthly_savings[month_key] += amount
    
    # Calculate average monthly savings
    if monthly_savings:
        avg_monthly_savings = sum(monthly_savings.values()) / len(monthly_savings)
    else:
        avg_monthly_savings = 0.0
    
    # Get current total savings
    total_savings = sum(acc["balance"] or 0.0 for acc in savings_accounts)
    
    # Estimate balance 180 days ago (current - net_inflow)
    balance_180d_ago = total_savings - net_inflow
    
    # Calculate growth rate
    if balance_180d_ago > 0:
        growth_rate = ((total_savings - balance_180d_ago) / balance_180d_ago) * 100
    else:
        growth_rate = 100.0 if total_savings > 0 else 0.0
    
    # Calculate average monthly expenses (from checking account transactions)
    checking_accounts = _get_accounts(user_id, subtype='checking')
    checking_account_ids = [acc["account_id"] for acc in checking_accounts]
    
    if USE_FIRESTORE:
        all_txns = get_user_transactions(user_id, cutoff_date)
        total_spend = sum(abs(txn.get('amount', 0)) for txn in all_txns 
                         if txn.get('account_id') in checking_account_ids and txn.get('amount', 0) < 0)
    else:
        placeholders = ",".join(["?"] * len(checking_account_ids)) if checking_account_ids else ""
        if checking_account_ids:
            checking_query = f"""
                SELECT SUM(ABS(amount)) as total_spend
                FROM transactions
                WHERE user_id = ? 
                AND account_id IN ({placeholders})
                AND date >= ?
                AND amount < 0
            """
            expense_data = db.fetch_one(checking_query, (user_id,) + tuple(checking_account_ids) + (cutoff_date,))
            total_spend = expense_data["total_spend"] or 0.0 if expense_data else 0.0
        else:
            total_spend = 0.0
    
    # Calculate average monthly expenses
    months_in_window = window_days / 30.0
    avg_monthly_expenses = total_spend / months_in_window if months_in_window > 0 else 0.0
    
    # Calculate emergency fund coverage (months)
    if avg_monthly_expenses > 0:
        emergency_fund_coverage = total_savings / avg_monthly_expenses
    else:
        emergency_fund_coverage = 0.0
    
    # Assign coverage level
    if emergency_fund_coverage >= 6:
        coverage_level = "excellent"
    elif emergency_fund_coverage >= 3:
        coverage_level = "good"
    elif emergency_fund_coverage > 0:
        coverage_level = "building"
    else:
        coverage_level = "low"
    
    # Build account details
    accounts_detail = []
    for acc in savings_accounts:
        account_id = acc["account_id"]
        net_flow = account_flows.get(account_id, 0.0)
        accounts_detail.append({
            "account_id": account_id,
            "balance": acc["balance"] or 0.0,
            "net_inflow": round(net_flow, 2),
            "subtype": acc["subtype"]
        })
    
    return {
        "total_savings": round(total_savings, 2),
        "net_inflow": round(net_inflow, 2),
        "growth_rate": round(growth_rate, 2),
        "emergency_fund_coverage": round(emergency_fund_coverage, 2),
        "coverage_level": coverage_level,
        "accounts": accounts_detail,
        "avg_monthly_expenses": round(avg_monthly_expenses, 2),
        "avg_monthly_savings": round(avg_monthly_savings, 2),
        "travel_filtered_transactions": travel_filtered_count
    }


def detect_income_stability(user_id: str, window_days: int = 180) -> Dict[str, Any]:
    """Detect income stability patterns from payroll deposits.
    
    Logic:
    - Find payroll deposits (ACH with "PAYROLL" or employer names)
    - Identify frequency (weekly, biweekly, monthly)
    - Calculate variability (coefficient of variation)
    - Calculate cash-flow buffer: checking_balance / avg_monthly_expenses
    
    Args:
        user_id: User identifier
        window_days: Number of days to look back
        
    Returns:
        Dictionary with income stability signals:
        - frequency: "weekly", "biweekly", "monthly", or "irregular"
        - median_pay_gap: Median days between paychecks
        - irregular_frequency: Boolean indicating irregular patterns
        - coefficient_of_variation: Measure of income variability
        - cash_flow_buffer: Months of expenses covered by checking balance
        - avg_monthly_income: Average monthly income
    """
    cutoff_date = _get_date_window_days_ago(window_days)
    
    # Get checking account
    checking_accounts = _get_accounts(user_id, subtype='checking')
    checking_account = checking_accounts[0] if checking_accounts else None
    
    if not checking_account:
        return {
            "frequency": "unknown",
            "median_pay_gap": 0,
            "irregular_frequency": True,
            "coefficient_of_variation": 0.0,
            "cash_flow_buffer": 0.0,
            "avg_monthly_income": 0.0
        }
    
    account_id = checking_account["account_id"]
    checking_balance = checking_account["balance"] or 0.0
    
    # Get payroll deposits (positive amounts, likely ACH or deposits)
    # Look for transactions with keywords or income category
    # Tightened detection: require amount > 500 AND keywords, OR income category
    if USE_FIRESTORE:
        all_txns = get_user_transactions(user_id, cutoff_date)
        payroll_transactions = []
        for txn in all_txns:
            if txn.get('account_id') != account_id:
                continue
            if txn.get('amount', 0) <= 0:
                continue
            if txn.get('iso_currency_code') not in ('USD', None):
                continue
            
            amount = txn.get('amount', 0)
            merchant_name = str(txn.get('merchant_name', '')).lower()
            category = txn.get('category', '')
            
            # Check if transaction matches payroll criteria
            # Require: (amount > 500 AND keywords) OR (income category)
            has_keywords = ('payroll' in merchant_name or
                           'employer' in merchant_name or
                           'salary' in merchant_name or
                           'direct deposit' in merchant_name)
            has_income_category = category_contains(category, 'income') or category_contains(category, 'payroll')
            
            is_payroll = ((amount > 500 and has_keywords) or has_income_category)
            
            if is_payroll:
                # Filter out known non-payroll patterns
                if not any(x in merchant_name for x in ['savings', 'transfer', 'refund', 'tax']):
                    payroll_transactions.append(DictRow(txn))
    else:
        # Fetch transactions and filter in Python (handles JSON arrays in category)
        payroll_query = """
            SELECT date, amount, merchant_name, category,
                   authorized_date, iso_currency_code, payment_channel
            FROM transactions
            WHERE account_id = ? 
            AND date >= ?
            AND amount > 0
            ORDER BY date
        """
        all_transactions = db.fetch_all(payroll_query, (account_id, cutoff_date))
        
        # Filter payroll transactions using category_contains (handles JSON arrays)
        # Also filter by USD currency and use authorized_date when available
        # Tightened detection: require amount > 500 AND keywords, OR income category
        payroll_transactions = []
        for txn in all_transactions:
            amount = txn.get("amount", 0)
            merchant_name = str(txn.get("merchant_name", "")).lower()
            category = txn.get("category", "")
            iso_currency = txn.get("iso_currency_code")
            
            # Filter out non-USD transactions (unless currency is NULL/not set)
            if iso_currency and iso_currency != 'USD':
                continue
            
            # Check if transaction matches payroll criteria
            # Require: (amount > 500 AND keywords) OR (income category)
            has_keywords = ('payroll' in merchant_name or
                           'employer' in merchant_name or
                           'salary' in merchant_name or
                           'direct deposit' in merchant_name)
            has_income_category = category_contains(category, 'income') or category_contains(category, 'payroll')
            
            is_payroll = ((amount > 500 and has_keywords) or has_income_category)
            
            if is_payroll:
                # Filter out known non-payroll patterns
                if not any(x in merchant_name for x in ['savings', 'transfer', 'refund', 'tax']):
                    payroll_transactions.append(txn)
    
    if len(payroll_transactions) < 2:
        return {
            "frequency": "unknown",
            "median_pay_gap": 0,
            "irregular_frequency": True,
            "coefficient_of_variation": 0.0,
            "cash_flow_buffer": 0.0,
            "avg_monthly_income": 0.0
        }
    
    # Calculate intervals between paychecks
    # Use authorized_date if available, fall back to date for more accurate timing
    pay_dates = []
    for tx in payroll_transactions:
        tx_date = tx.get("authorized_date") or tx["date"]
        pay_dates.append(_parse_date(tx_date))
    
    pay_amounts = [tx["amount"] for tx in payroll_transactions]
    
    intervals = []
    for i in range(1, len(pay_dates)):
        delta = (pay_dates[i] - pay_dates[i-1]).days
        intervals.append(delta)
    
    median_pay_gap = statistics.median(intervals) if intervals else 0
    
    # Determine frequency
    if 6 <= median_pay_gap <= 8:
        frequency = "weekly"
    elif 13 <= median_pay_gap <= 15:
        frequency = "biweekly"
    elif 28 <= median_pay_gap <= 31:
        frequency = "monthly"
    else:
        frequency = "irregular"
    
    # Use standardized helper function for irregular frequency detection
    irregular_frequency = _is_irregular_frequency(median_pay_gap, intervals)
    
    # Calculate coefficient of variation (standard deviation / mean)
    if pay_amounts:
        mean_amount = statistics.mean(pay_amounts)
        if mean_amount > 0:
            std_amount = statistics.stdev(pay_amounts) if len(pay_amounts) > 1 else 0.0
            coefficient_of_variation = (std_amount / mean_amount) * 100
        else:
            coefficient_of_variation = 0.0
    else:
        coefficient_of_variation = 0.0
    
    # Calculate average monthly income
    total_income = sum(pay_amounts)
    months_in_window = window_days / 30.0
    avg_monthly_income = total_income / months_in_window if months_in_window > 0 else 0.0
    
    # Calculate average monthly expenses
    if USE_FIRESTORE:
        all_txns = get_user_transactions(user_id, cutoff_date)
        total_spend = sum(abs(txn.get('amount', 0)) for txn in all_txns 
                         if txn.get('account_id') == account_id and txn.get('amount', 0) < 0)
    else:
        expense_query = """
            SELECT SUM(ABS(amount)) as total_spend
            FROM transactions
            WHERE account_id = ? 
            AND date >= ?
            AND amount < 0
        """
        expense_data = db.fetch_one(expense_query, (account_id, cutoff_date))
        total_spend = expense_data["total_spend"] or 0.0 if expense_data else 0.0
    avg_monthly_expenses = total_spend / months_in_window if months_in_window > 0 else 0.0
    
    # Calculate cash-flow buffer
    if avg_monthly_expenses > 0:
        cash_flow_buffer = checking_balance / avg_monthly_expenses
    else:
        cash_flow_buffer = 0.0
    
    return {
        "frequency": frequency,
        "median_pay_gap": int(median_pay_gap),
        "irregular_frequency": irregular_frequency,
        "coefficient_of_variation": round(coefficient_of_variation, 2),
        "cash_flow_buffer": round(cash_flow_buffer, 2),
        "avg_monthly_income": round(avg_monthly_income, 2),
        "avg_monthly_expenses": round(avg_monthly_expenses, 2)
    }


def compute_all_features(user_id: str, time_window: str = "30d") -> Dict[str, Any]:
    """Compute all features for a user and store in database.
    
    Args:
        user_id: User identifier
        time_window: Time window string ("30d" or "180d")
        
    Returns:
        Dictionary with all computed features
    """
    # Convert time_window to days
    window_days = 30 if time_window == "30d" else 180
    
    # Compute all signals
    subscription_signals = detect_subscriptions(user_id, window_days)
    credit_signals = detect_credit_utilization(user_id, window_days)
    savings_signals = detect_savings_behavior(user_id, window_days)
    income_signals = detect_income_stability(user_id, window_days)
    
    # Combine all signals
    all_features = {
        "subscriptions": subscription_signals,
        "credit_utilization": credit_signals,
        "savings_behavior": savings_signals,
        "income_stability": income_signals
    }
    
    # Store each signal type separately
    for signal_type, signal_data in all_features.items():
        store_feature(user_id, signal_type, signal_data, time_window)
    
    return all_features


def store_feature(user_id: str, signal_type: str, signal_data: Dict[str, Any], time_window: str) -> None:
    """Store computed feature in database.
    
    Args:
        user_id: User identifier
        signal_type: Type of signal (e.g., "subscriptions", "credit_utilization")
        signal_data: Dictionary with signal data
        time_window: Time window string ("30d" or "180d")
    """
    if USE_FIRESTORE:
        firestore_store_feature(user_id, signal_type, signal_data, time_window)
    else:
        signal_json = json.dumps(signal_data)
        computed_at = datetime.now().isoformat()
        
        # Delete existing feature if it exists and insert new feature (idempotent)
        # Do both in a single transaction
        delete_query = """
            DELETE FROM computed_features
            WHERE user_id = ? AND signal_type = ? AND time_window = ?
        """
        insert_query = """
            INSERT INTO computed_features (user_id, time_window, signal_type, signal_data, computed_at)
            VALUES (?, ?, ?, ?, ?)
        """
        with db.get_db_connection() as conn:
            conn.execute(delete_query, (user_id, signal_type, time_window))
            conn.execute(insert_query, (user_id, time_window, signal_type, signal_json, computed_at))


def get_user_features(user_id: str, time_window: str = "30d") -> Dict[str, Any]:
    """Retrieve all features for a user.
    
    Args:
        user_id: User identifier
        time_window: Time window string ("30d" or "180d")
        
    Returns:
        Dictionary with all features, parsed from JSON
    """
    if USE_FIRESTORE:
        features_list = firestore_get_user_features(user_id, time_window)
        features = {}
        for feature_doc in features_list:
            signal_type = feature_doc.get('signal_type')
            signal_data = feature_doc.get('signal_data')
            if signal_type and signal_data:
                features[signal_type] = signal_data
        return features
    else:
        query = """
            SELECT signal_type, signal_data
            FROM computed_features
            WHERE user_id = ? AND time_window = ?
        """
        rows = db.fetch_all(query, (user_id, time_window))
        
        features = {}
        for row in rows:
            signal_type = row["signal_type"]
            signal_data = json.loads(row["signal_data"])
            features[signal_type] = signal_data
        
        return features

