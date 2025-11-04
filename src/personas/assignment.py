"""Persona assignment module for SpendSense.

This module implements hierarchical persona assignment based on behavioral signals.
Personas are assigned in priority order, with the first matching persona winning.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.database import db
from src.features.signal_detection import get_user_features


# Persona names
PERSONA_HIGH_UTILIZATION = "high_utilization"
PERSONA_VARIABLE_INCOME = "variable_income"
PERSONA_SUBSCRIPTION_HEAVY = "subscription_heavy"
PERSONA_SAVINGS_BUILDER = "savings_builder"
PERSONA_GENERAL_WELLNESS = "general_wellness"

# Persona priority order (1 = highest priority)
PERSONA_PRIORITY = {
    PERSONA_HIGH_UTILIZATION: 1,
    PERSONA_VARIABLE_INCOME: 2,
    PERSONA_SUBSCRIPTION_HEAVY: 3,
    PERSONA_SAVINGS_BUILDER: 4,
    PERSONA_GENERAL_WELLNESS: 5  # Default, lowest priority
}


def check_high_utilization(signals: Dict[str, Any]) -> bool:
    """Check if user matches High Utilization persona criteria.
    
    Criteria:
    - credit_utilization >= 0.50 OR
    - interest_charged > 0 OR
    - minimum_payment_only == True OR
    - is_overdue == True
    
    Args:
        signals: Dictionary of all computed signals for user
        
    Returns:
        True if user matches High Utilization persona, False otherwise
    """
    credit_signals = signals.get("credit_utilization", {})
    
    if not credit_signals:
        return False
    
    # Check total utilization percentage (convert from percentage to decimal)
    total_utilization = credit_signals.get("total_utilization", 0.0)
    utilization_decimal = total_utilization / 100.0 if total_utilization else 0.0
    
    # Check individual criteria
    if utilization_decimal >= 0.50:
        return True
    
    if credit_signals.get("interest_charged", 0.0) > 0:
        return True
    
    if credit_signals.get("minimum_payment_only", False):
        return True
    
    if credit_signals.get("is_overdue", False):
        return True
    
    # Check account-level utilization
    accounts = credit_signals.get("accounts", [])
    for account in accounts:
        account_utilization = account.get("utilization", 0.0)
        account_utilization_decimal = account_utilization / 100.0 if account_utilization else 0.0
        if account_utilization_decimal >= 0.50:
            return True
    
    return False


def check_variable_income(signals: Dict[str, Any]) -> bool:
    """Check if user matches Variable Income persona criteria.
    
    Criteria:
    - (median_pay_gap > 45 days OR irregular_frequency == True) AND
    - cash_flow_buffer < 1.0
    
    Args:
        signals: Dictionary of all computed signals for user
        
    Returns:
        True if user matches Variable Income persona, False otherwise
    """
    income_signals = signals.get("income_stability", {})
    
    if not income_signals:
        return False
    
    median_pay_gap = income_signals.get("median_pay_gap", 0)
    irregular_frequency = income_signals.get("irregular_frequency", False)
    cash_flow_buffer = income_signals.get("cash_flow_buffer", 0.0)
    
    # Check if income pattern is irregular
    income_irregular = median_pay_gap > 45 or irregular_frequency
    
    # Check if cash flow buffer is low
    buffer_low = cash_flow_buffer < 1.0
    
    return income_irregular and buffer_low


def check_subscription_heavy(signals: Dict[str, Any]) -> bool:
    """Check if user matches Subscription-Heavy persona criteria.
    
    Criteria:
    - recurring_merchants >= 3 AND
    - (monthly_recurring >= 50 OR subscription_share >= 0.10)
    
    Args:
        signals: Dictionary of all computed signals for user
        
    Returns:
        True if user matches Subscription-Heavy persona, False otherwise
    """
    subscription_signals = signals.get("subscriptions", {})
    
    if not subscription_signals:
        return False
    
    recurring_merchants = subscription_signals.get("recurring_merchants", [])
    monthly_recurring = subscription_signals.get("monthly_recurring", 0.0)
    subscription_share = subscription_signals.get("subscription_share", 0.0)
    
    # Convert subscription_share from percentage to decimal
    subscription_share_decimal = subscription_share / 100.0 if subscription_share else 0.0
    
    # Check criteria
    has_enough_merchants = len(recurring_merchants) >= 3
    has_high_spend = monthly_recurring >= 50.0 or subscription_share_decimal >= 0.10
    
    return has_enough_merchants and has_high_spend


def check_savings_builder(signals: Dict[str, Any]) -> bool:
    """Check if user matches Savings Builder persona criteria.
    
    Criteria:
    - (savings_growth_rate >= 0.02 OR net_savings_inflow >= 200) AND
    - ALL credit_utilization < 0.30
    
    Args:
        signals: Dictionary of all computed signals for user
        
    Returns:
        True if user matches Savings Builder persona, False otherwise
    """
    savings_signals = signals.get("savings_behavior", {})
    credit_signals = signals.get("credit_utilization", {})
    
    if not savings_signals:
        return False
    
    # Check savings growth or inflow
    growth_rate = savings_signals.get("growth_rate", 0.0)
    # Convert growth_rate from percentage to decimal
    growth_rate_decimal = growth_rate / 100.0 if growth_rate else 0.0
    net_inflow = savings_signals.get("net_inflow", 0.0)
    
    has_savings_activity = growth_rate_decimal >= 0.02 or net_inflow >= 200.0
    
    if not has_savings_activity:
        return False
    
    # Check that all credit utilization is low
    if not credit_signals:
        return True  # No credit accounts, so criteria is met
    
    # Check total utilization
    total_utilization = credit_signals.get("total_utilization", 0.0)
    utilization_decimal = total_utilization / 100.0 if total_utilization else 0.0
    
    if utilization_decimal >= 0.30:
        return False
    
    # Check individual accounts
    accounts = credit_signals.get("accounts", [])
    for account in accounts:
        account_utilization = account.get("utilization", 0.0)
        account_utilization_decimal = account_utilization / 100.0 if account_utilization else 0.0
        if account_utilization_decimal >= 0.30:
            return False
    
    return True


def assign_persona(user_id: str, time_window: str = "30d") -> str:
    """Assign persona to user based on hierarchical criteria.
    
    Checks personas in priority order (1-4), first match wins.
    Defaults to "general_wellness" if no criteria met.
    
    Args:
        user_id: User identifier
        time_window: Time window string ("30d" or "180d")
        
    Returns:
        Assigned persona name
    """
    # Get user signals
    signals = get_user_features(user_id, time_window)
    
    if not signals:
        # No signals available, assign default
        persona = PERSONA_GENERAL_WELLNESS
        criteria_met = []
    else:
        # Check personas in priority order
        persona = PERSONA_GENERAL_WELLNESS
        criteria_met = []
        
        # Priority 1: High Utilization
        if check_high_utilization(signals):
            persona = PERSONA_HIGH_UTILIZATION
            criteria_met = ["credit_utilization >= 0.50 OR interest_charged > 0 OR minimum_payment_only OR is_overdue"]
        # Priority 2: Variable Income
        elif check_variable_income(signals):
            persona = PERSONA_VARIABLE_INCOME
            criteria_met = ["(median_pay_gap > 45 days OR irregular_frequency) AND cash_flow_buffer < 1.0"]
        # Priority 3: Subscription-Heavy
        elif check_subscription_heavy(signals):
            persona = PERSONA_SUBSCRIPTION_HEAVY
            criteria_met = ["recurring_merchants >= 3 AND (monthly_recurring >= 50 OR subscription_share >= 0.10)"]
        # Priority 4: Savings Builder
        elif check_savings_builder(signals):
            persona = PERSONA_SAVINGS_BUILDER
            criteria_met = ["(savings_growth_rate >= 0.02 OR net_savings_inflow >= 200) AND all_credit_utilization < 0.30"]
    
    # Store persona assignment
    store_persona_assignment(user_id, time_window, persona, criteria_met)
    
    return persona


def store_persona_assignment(
    user_id: str,
    time_window: str,
    persona: str,
    criteria_met: List[str]
) -> None:
    """Store persona assignment in database.
    
    Args:
        user_id: User identifier
        time_window: Time window string ("30d" or "180d")
        persona: Assigned persona name
        criteria_met: List of criteria strings that were met
    """
    criteria_json = json.dumps(criteria_met)
    assigned_at = datetime.now().isoformat()
    
    # Delete existing assignment if it exists and insert new one (idempotent)
    delete_query = """
        DELETE FROM persona_assignments
        WHERE user_id = ? AND time_window = ?
    """
    insert_query = """
        INSERT INTO persona_assignments (user_id, time_window, persona, criteria_met, assigned_at)
        VALUES (?, ?, ?, ?, ?)
    """
    
    with db.get_db_connection() as conn:
        conn.execute(delete_query, (user_id, time_window))
        conn.execute(insert_query, (user_id, time_window, persona, criteria_json, assigned_at))


def get_persona_assignment(user_id: str, time_window: str = "30d") -> Optional[Dict[str, Any]]:
    """Retrieve persona assignment for a user.
    
    Args:
        user_id: User identifier
        time_window: Time window string ("30d" or "180d")
        
    Returns:
        Dictionary with persona assignment data or None if not found
    """
    query = """
        SELECT persona, criteria_met, assigned_at
        FROM persona_assignments
        WHERE user_id = ? AND time_window = ?
    """
    row = db.fetch_one(query, (user_id, time_window))
    
    if not row:
        return None
    
    return {
        "persona": row["persona"],
        "criteria_met": json.loads(row["criteria_met"]),
        "assigned_at": row["assigned_at"]
    }

