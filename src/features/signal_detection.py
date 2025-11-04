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

from src.database import db


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
    - Calculate monthly recurring total
    - Calculate subscription share of total spend
    
    Args:
        user_id: User identifier
        window_days: Number of days to look back
        
    Returns:
        Dictionary with subscription signals:
        - recurring_merchants: List of merchant names with recurring patterns
        - monthly_recurring: Total monthly recurring amount
        - subscription_share: Percentage of total spend that is subscriptions
        - merchant_details: List of dicts with merchant, frequency, amount
    """
    cutoff_date = _get_date_window_days_ago(window_days)
    
    # Get all transactions for user in the window
    query = """
        SELECT merchant_name, date, amount, category
        FROM transactions
        WHERE user_id = ? AND date >= ? AND amount < 0
        ORDER BY date
    """
    transactions = db.fetch_all(query, (user_id, cutoff_date))
    
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
        merchant_transactions[merchant].append({
            "date": _parse_date(tx["date"]),
            "amount": abs(tx["amount"])
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
        
        if is_monthly or is_weekly:
            recurring_merchants.append(merchant)
            
            # Calculate monthly cost
            if is_monthly:
                monthly_cost = avg_amount
            elif is_weekly:
                monthly_cost = avg_amount * 4.33  # Approximate weeks per month
            
            monthly_recurring += monthly_cost
            
            merchant_details.append({
                "merchant": merchant,
                "frequency": "monthly" if is_monthly else "weekly",
                "amount": avg_amount,
                "monthly_equivalent": monthly_cost,
                "occurrences": len(txs)
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
    - Check overdue status from liabilities (if available)
    
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
    """
    cutoff_date = _get_date_window_days_ago(window_days)
    
    # Get all credit accounts for user
    query = """
        SELECT account_id, balance, "limit", type, subtype
        FROM accounts
        WHERE user_id = ? AND type = 'credit' AND "limit" > 0
    """
    credit_accounts = db.fetch_all(query, (user_id,))
    
    if not credit_accounts:
        return {
            "total_utilization": 0.0,
            "utilization_level": "low",
            "accounts": [],
            "interest_charged": 0.0,
            "minimum_payment_only": False,
            "is_overdue": False
        }
    
    # Get recent payments and interest charges
    account_ids = [acc["account_id"] for acc in credit_accounts]
    placeholders = ",".join(["?"] * len(account_ids))
    
    payments_query = f"""
        SELECT account_id, date, amount, merchant_name, category
        FROM transactions
        WHERE account_id IN ({placeholders}) 
        AND date >= ? 
        AND amount > 0
        ORDER BY date DESC
    """
    payments = db.fetch_all(payments_query, tuple(account_ids) + (cutoff_date,))
    
    # Get interest charges (negative amounts that might be interest)
    interest_query = f"""
        SELECT account_id, SUM(amount) as total_interest
        FROM transactions
        WHERE account_id IN ({placeholders})
        AND date >= ?
        AND amount < 0
        AND (category LIKE '%interest%' OR merchant_name LIKE '%interest%' OR category LIKE '%fee%')
        GROUP BY account_id
    """
    interest_charges = db.fetch_all(interest_query, tuple(account_ids) + (cutoff_date,))
    interest_map = {row["account_id"]: abs(row["total_interest"] or 0) for row in interest_charges}
    
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
            # Estimate minimum payment as ~2% of balance or $25, whichever is higher
            estimated_min = max(balance * 0.02, 25.0)
            recent_payment = account_payments[0]["amount"]
            if abs(recent_payment - estimated_min) <= 5.0:
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
        "is_overdue": is_overdue
    }


def detect_savings_behavior(user_id: str, window_days: int = 180) -> Dict[str, Any]:
    """Detect savings account behavior patterns.
    
    Logic:
    - Identify savings accounts (type = savings, money market, HSA)
    - Calculate net inflow (deposits - withdrawals)
    - Calculate growth rate: (current - 180d_ago) / 180d_ago
    - Calculate emergency fund coverage: savings / avg_monthly_expenses
    - Assign coverage flag: excellent/good/building/low
    
    Args:
        user_id: User identifier
        window_days: Number of days to look back
        
    Returns:
        Dictionary with savings behavior signals:
        - total_savings: Total balance across all savings accounts
        - net_inflow: Net deposits minus withdrawals in window
        - growth_rate: Percentage growth rate
        - emergency_fund_coverage: Months of expenses covered
        - coverage_level: "excellent", "good", "building", or "low"
        - accounts: List of account-level details
    """
    cutoff_date = _get_date_window_days_ago(window_days)
    
    # Get savings accounts
    query = """
        SELECT account_id, balance, type, subtype
        FROM accounts
        WHERE user_id = ? 
        AND (subtype IN ('savings', 'money market', 'hsa') OR type = 'depository' AND subtype LIKE '%savings%')
    """
    savings_accounts = db.fetch_all(query, (user_id,))
    
    if not savings_accounts:
        return {
            "total_savings": 0.0,
            "net_inflow": 0.0,
            "growth_rate": 0.0,
            "emergency_fund_coverage": 0.0,
            "coverage_level": "low",
            "accounts": []
        }
    
    # Get historical balance if available (we'll use current balance as proxy)
    # For a real implementation, you'd track balance history
    # Here we'll calculate based on transaction flows
    
    account_ids = [acc["account_id"] for acc in savings_accounts]
    placeholders = ",".join(["?"] * len(account_ids))
    
    # Get all transactions for savings accounts
    transactions_query = f"""
        SELECT account_id, date, amount
        FROM transactions
        WHERE account_id IN ({placeholders}) AND date >= ?
        ORDER BY date
    """
    transactions = db.fetch_all(transactions_query, tuple(account_ids) + (cutoff_date,))
    
    # Calculate net inflow
    net_inflow = 0.0
    account_flows = defaultdict(float)
    
    for tx in transactions:
        amount = tx["amount"]
        account_flows[tx["account_id"]] += amount
        net_inflow += amount
    
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
    checking_query = """
        SELECT SUM(ABS(amount)) as total_spend
        FROM transactions
        WHERE user_id = ? 
        AND account_id IN (
            SELECT account_id FROM accounts 
            WHERE user_id = ? AND subtype = 'checking'
        )
        AND date >= ?
        AND amount < 0
    """
    expense_data = db.fetch_one(checking_query, (user_id, user_id, cutoff_date))
    total_spend = expense_data["total_spend"] or 0.0 if expense_data else 0.0
    
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
        "avg_monthly_expenses": round(avg_monthly_expenses, 2)
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
    checking_query = """
        SELECT account_id, balance
        FROM accounts
        WHERE user_id = ? AND subtype = 'checking'
        LIMIT 1
    """
    checking_account = db.fetch_one(checking_query, (user_id,))
    
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
    # Look for transactions with keywords or large positive amounts
    payroll_query = """
        SELECT date, amount, merchant_name, category
        FROM transactions
        WHERE account_id = ? 
        AND date >= ?
        AND amount > 0
        AND (amount > 500 OR merchant_name LIKE '%payroll%' OR merchant_name LIKE '%employer%' 
             OR category LIKE '%income%' OR merchant_name LIKE '%salary%')
        ORDER BY date
    """
    payroll_transactions = db.fetch_all(payroll_query, (account_id, cutoff_date))
    
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
    pay_dates = [_parse_date(tx["date"]) for tx in payroll_transactions]
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
    
    irregular_frequency = frequency == "irregular"
    
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

