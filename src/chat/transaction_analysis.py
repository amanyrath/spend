"""Transaction analysis utilities for chat context building.

Provides specialized analysis functions for extracting insights from
transaction data including temporal patterns, category intelligence,
merchant analysis, payment channels, and account activity.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import random

from src.utils.category_utils import get_primary_category


def calculate_weekday_spending(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze spending patterns by weekday vs weekend.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Dictionary with weekday/weekend spending analysis
    """
    weekday_amounts = []
    weekend_amounts = []
    day_totals = defaultdict(float)
    
    for txn in transactions:
        if txn.get('amount', 0) >= 0:
            continue  # Skip income/deposits
            
        amount = abs(txn.get('amount', 0))
        date_str = txn.get('date')
        
        if not date_str:
            continue
            
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
            day_name = date_obj.strftime('%A')
            
            day_totals[day_name] += amount
            
            if weekday >= 5:  # Saturday or Sunday
                weekend_amounts.append(amount)
            else:
                weekday_amounts.append(amount)
        except (ValueError, TypeError):
            continue
    
    weekday_avg = sum(weekday_amounts) / len(weekday_amounts) if weekday_amounts else 0
    weekend_avg = sum(weekend_amounts) / len(weekend_amounts) if weekend_amounts else 0
    
    # Find highest spending day
    highest_day = max(day_totals.items(), key=lambda x: x[1]) if day_totals else ("Unknown", 0)
    
    return {
        'weekday_avg': round(weekday_avg, 2),
        'weekend_avg': round(weekend_avg, 2),
        'weekday_total': round(sum(weekday_amounts), 2),
        'weekend_total': round(sum(weekend_amounts), 2),
        'weekday_count': len(weekday_amounts),
        'weekend_count': len(weekend_amounts),
        'highest_day': highest_day[0],
        'highest_day_total': round(highest_day[1], 2)
    }


def calculate_monthly_progression(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze month-to-date spending with projections.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Dictionary with MTD spending and projections
    """
    now = datetime.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    days_in_month = (now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)).day if now.month < 12 else 31
    days_elapsed = now.day
    
    mtd_spending = 0
    mtd_count = 0
    
    for txn in transactions:
        if txn.get('amount', 0) >= 0:
            continue  # Skip income/deposits
            
        date_str = txn.get('date')
        if not date_str:
            continue
            
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            if date_obj >= current_month_start:
                mtd_spending += abs(txn.get('amount', 0))
                mtd_count += 1
        except (ValueError, TypeError):
            continue
    
    daily_avg = mtd_spending / days_elapsed if days_elapsed > 0 else 0
    projected_monthly = daily_avg * days_in_month
    
    return {
        'spent_mtd': round(mtd_spending, 2),
        'transaction_count_mtd': mtd_count,
        'days_elapsed': days_elapsed,
        'days_remaining': days_in_month - days_elapsed,
        'daily_avg': round(daily_avg, 2),
        'projected_monthly': round(projected_monthly, 2),
        'current_month': now.strftime('%B %Y')
    }


def calculate_spending_velocity(transactions: List[Dict[str, Any]], window_days: int = 30) -> Dict[str, Any]:
    """Calculate spending trend (increasing/decreasing).
    
    Args:
        transactions: List of transaction dictionaries
        window_days: Number of days to analyze
        
    Returns:
        Dictionary with spending velocity analysis
    """
    now = datetime.now()
    midpoint = now - timedelta(days=window_days // 2)
    
    first_half_spending = 0
    second_half_spending = 0
    
    for txn in transactions:
        if txn.get('amount', 0) >= 0:
            continue
            
        date_str = txn.get('date')
        if not date_str:
            continue
            
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            amount = abs(txn.get('amount', 0))
            
            if date_obj < midpoint:
                first_half_spending += amount
            else:
                second_half_spending += amount
        except (ValueError, TypeError):
            continue
    
    if first_half_spending > 0:
        change_pct = ((second_half_spending - first_half_spending) / first_half_spending) * 100
    else:
        change_pct = 0
    
    trend = 'stable'
    if change_pct > 10:
        trend = 'increasing'
    elif change_pct < -10:
        trend = 'decreasing'
    
    return {
        'first_half_spending': round(first_half_spending, 2),
        'second_half_spending': round(second_half_spending, 2),
        'change_pct': round(change_pct, 1),
        'trend': trend
    }


def build_detailed_category_analysis(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build comprehensive category spending analysis.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        List of category analysis dictionaries, sorted by amount
    """
    category_data = defaultdict(lambda: {'amount': 0, 'count': 0})
    total_spending = 0
    
    for txn in transactions:
        if txn.get('amount', 0) >= 0:
            continue  # Skip income/deposits
            
        amount = abs(txn.get('amount', 0))
        total_spending += amount
        
        category = get_primary_category(txn.get('category', 'Uncategorized'))
        category_data[category]['amount'] += amount
        category_data[category]['count'] += 1
    
    # Build sorted list
    category_breakdown = []
    for category, data in category_data.items():
        percentage = (data['amount'] / total_spending * 100) if total_spending > 0 else 0
        avg_transaction = data['amount'] / data['count'] if data['count'] > 0 else 0
        
        category_breakdown.append({
            'category': category,
            'amount': round(data['amount'], 2),
            'percentage': round(percentage, 1),
            'transaction_count': data['count'],
            'avg_transaction': round(avg_transaction, 2)
        })
    
    # Sort by amount descending
    category_breakdown.sort(key=lambda x: x['amount'], reverse=True)
    
    return category_breakdown


def analyze_merchant_patterns(transactions: List[Dict[str, Any]]) -> List[tuple]:
    """Analyze merchant visit patterns.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        List of (merchant_name, data_dict) tuples for frequent merchants
    """
    merchant_data = {}
    
    for txn in transactions:
        if txn.get('amount', 0) >= 0:
            continue  # Skip income/deposits
            
        merchant = txn.get('merchant_name', 'Unknown')
        if merchant == 'Unknown' or not merchant:
            continue
            
        amount = abs(txn.get('amount', 0))
        date = txn.get('date', '')
        
        if merchant not in merchant_data:
            merchant_data[merchant] = {
                'visit_count': 0,
                'total_spent': 0,
                'last_visit': date,
                'first_visit': date,
                'transactions': []
            }
        
        merchant_data[merchant]['visit_count'] += 1
        merchant_data[merchant]['total_spent'] += amount
        merchant_data[merchant]['last_visit'] = max(merchant_data[merchant]['last_visit'], date) if date else merchant_data[merchant]['last_visit']
        merchant_data[merchant]['first_visit'] = min(merchant_data[merchant]['first_visit'], date) if date else merchant_data[merchant]['first_visit']
        merchant_data[merchant]['transactions'].append(amount)
    
    # Filter to frequent merchants (3+ visits) and sort by visit count
    frequent_merchants = [
        (merchant, data) 
        for merchant, data in merchant_data.items() 
        if data['visit_count'] >= 3
    ]
    frequent_merchants.sort(key=lambda x: x[1]['visit_count'], reverse=True)
    
    return frequent_merchants[:5]  # Top 5 frequent merchants


def analyze_payment_channels(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze online vs in-store spending patterns.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Dictionary with payment channel analysis
    """
    channel_data = defaultdict(lambda: {'count': 0, 'amount': 0})
    
    for txn in transactions:
        if txn.get('amount', 0) >= 0:
            continue  # Skip income/deposits
            
        channel = txn.get('payment_channel', 'other')
        amount = abs(txn.get('amount', 0))
        
        channel_data[channel]['count'] += 1
        channel_data[channel]['amount'] += amount
    
    result = {}
    for channel, data in channel_data.items():
        result[channel] = {
            'count': data['count'],
            'amount': round(data['amount'], 2)
        }
    
    return result


def analyze_by_account(transactions: List[Dict[str, Any]], user_accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Group transactions by account for account-specific insights.
    
    Args:
        transactions: List of transaction dictionaries
        user_accounts: List of account dictionaries
        
    Returns:
        Dictionary mapping account_id to activity data
    """
    # Build account lookup
    account_lookup = {acc['account_id']: acc for acc in user_accounts}
    
    account_activity = {}
    
    for txn in transactions:
        account_id = txn.get('account_id')
        if not account_id:
            continue
            
        if account_id not in account_activity:
            account = account_lookup.get(account_id, {})
            account_activity[account_id] = {
                'mask': account.get('mask', 'Unknown'),
                'type': account.get('type', 'unknown'),
                'subtype': account.get('subtype', 'unknown'),
                'transaction_count': 0,
                'total_spent': 0,
                'total_income': 0
            }
        
        amount = txn.get('amount', 0)
        account_activity[account_id]['transaction_count'] += 1
        
        if amount < 0:
            account_activity[account_id]['total_spent'] += abs(amount)
        else:
            account_activity[account_id]['total_income'] += amount
    
    # Round amounts
    for account_id in account_activity:
        account_activity[account_id]['total_spent'] = round(account_activity[account_id]['total_spent'], 2)
        account_activity[account_id]['total_income'] = round(account_activity[account_id]['total_income'], 2)
    
    return account_activity


def analyze_pending_transactions(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Track pending transactions that will impact balances.
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        Dictionary with pending transaction analysis
    """
    pending_transactions = [t for t in transactions if t.get('pending')]
    
    pending_charges = 0
    pending_deposits = 0
    
    for txn in pending_transactions:
        amount = txn.get('amount', 0)
        if amount < 0:
            pending_charges += abs(amount)
        else:
            pending_deposits += amount
    
    return {
        'count': len(pending_transactions),
        'pending_charges': round(pending_charges, 2),
        'pending_deposits': round(pending_deposits, 2),
        'net_pending': round(pending_deposits - pending_charges, 2)
    }







