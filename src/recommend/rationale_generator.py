"""Rationale generator for SpendSense recommendations.

This module generates personalized rationales by substituting variables
in templates with actual signal data from the user's financial profile.
"""

import re
from typing import Dict, Any, Optional


def format_currency(amount: float) -> str:
    """Format amount as currency string.
    
    Args:
        amount: Amount to format
        
    Returns:
        Formatted currency string (e.g., "$1,234.56")
    """
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    return f"${amount:,.2f}"


def format_percentage(value: float, decimal: bool = False) -> str:
    """Format value as percentage string.
    
    Args:
        value: Percentage value (as decimal if decimal=True, otherwise as percentage)
        decimal: If True, value is already a decimal (0.68), otherwise percentage (68.0)
        
    Returns:
        Formatted percentage string (e.g., "68%")
    """
    if decimal:
        return f"{value * 100:.1f}%"
    return f"{value:.1f}%"


def extract_signal_value(signals: Dict[str, Any], path: str) -> Optional[Any]:
    """Extract a value from signals dictionary using dot notation path.
    
    Args:
        signals: Dictionary of all signals
        path: Dot-notation path (e.g., "credit_utilization.total_utilization")
        
    Returns:
        Extracted value or None if not found
    """
    parts = path.split(".")
    current = signals
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    
    return current


def get_card_name(account: Dict[str, Any]) -> str:
    """Get formatted card name from account data.
    
    Args:
        account: Account dictionary
        
    Returns:
        Formatted card name (e.g., "Visa ending in 4523")
    """
    mask = account.get("mask", "****")
    card_type = account.get("subtype", "card")
    
    if mask and mask != "****":
        return f"{card_type.title()} ending in {mask}"
    return f"{card_type.title()} card"


def generate_rationale(template: str, signals: Dict[str, Any], content_item: Optional[Dict[str, Any]] = None) -> str:
    """Generate personalized rationale by substituting variables in template.
    
    Supported variables:
    - {card_name} - Formatted card name from credit account
    - {utilization} - Credit utilization percentage
    - {balance} - Account balance (formatted as currency)
    - {limit} - Credit limit (formatted as currency)
    - {interest_charged} - Interest charged (formatted as currency)
    - {subscription_count} - Number of subscriptions
    - {monthly_recurring} - Monthly recurring amount (formatted as currency)
    - {total_balance} - Total credit card balance (formatted as currency)
    - {total_savings} - Total savings balance (formatted as currency)
    - {growth_rate} - Savings growth rate (formatted as percentage)
    - {cash_flow_buffer} - Cash flow buffer in months
    - {median_pay_gap} - Median days between paychecks
    
    Args:
        template: Rationale template with variable placeholders
        signals: Dictionary of all computed signals
        content_item: Optional content item for context
        
    Returns:
        Personalized rationale string with variables substituted
    """
    rationale = template
    
    # Get credit utilization signals
    credit_signals = signals.get("credit_utilization", {})
    accounts = credit_signals.get("accounts", [])
    
    # Get subscription signals
    subscription_signals = signals.get("subscriptions", {})
    
    # Get savings signals
    savings_signals = signals.get("savings_behavior", {})
    
    # Get income signals
    income_signals = signals.get("income_stability", {})
    
    # Substitute variables
    # Card name - use first credit account if available
    if "{card_name}" in rationale and accounts:
        card_name = get_card_name(accounts[0])
        rationale = rationale.replace("{card_name}", card_name)
    
    # Utilization - use total or first account
    if "{utilization}" in rationale:
        if accounts:
            utilization = accounts[0].get("utilization", credit_signals.get("total_utilization", 0.0))
        else:
            utilization = credit_signals.get("total_utilization", 0.0)
        rationale = rationale.replace("{utilization}", format_percentage(utilization))
    
    # Balance - use first account balance
    if "{balance}" in rationale and accounts:
        balance = accounts[0].get("balance", 0.0)
        rationale = rationale.replace("{balance}", format_currency(balance))
    
    # Limit - use first account limit
    if "{limit}" in rationale and accounts:
        limit = accounts[0].get("limit", 0.0)
        rationale = rationale.replace("{limit}", format_currency(limit))
    
    # Interest charged
    if "{interest_charged}" in rationale:
        interest = credit_signals.get("interest_charged", 0.0)
        rationale = rationale.replace("{interest_charged}", format_currency(interest))
    
    # Subscription count
    if "{subscription_count}" in rationale:
        subscriptions = subscription_signals.get("recurring_merchants", [])
        count = len(subscriptions)
        rationale = rationale.replace("{subscription_count}", str(count))
    
    # Monthly recurring
    if "{monthly_recurring}" in rationale:
        monthly = subscription_signals.get("monthly_recurring", 0.0)
        rationale = rationale.replace("{monthly_recurring}", format_currency(monthly))
    
    # Total credit balance
    if "{total_balance}" in rationale:
        total_balance = sum(acc.get("balance", 0.0) for acc in accounts)
        rationale = rationale.replace("{total_balance}", format_currency(total_balance))
    
    # Total savings
    if "{total_savings}" in rationale:
        total_savings = savings_signals.get("total_savings", 0.0)
        rationale = rationale.replace("{total_savings}", format_currency(total_savings))
    
    # Growth rate
    if "{growth_rate}" in rationale:
        growth_rate = savings_signals.get("growth_rate", 0.0)
        rationale = rationale.replace("{growth_rate}", format_percentage(growth_rate))
    
    # Cash flow buffer
    if "{cash_flow_buffer}" in rationale:
        buffer = income_signals.get("cash_flow_buffer", 0.0)
        rationale = rationale.replace("{cash_flow_buffer}", f"{buffer:.1f}")
    
    # Median pay gap
    if "{median_pay_gap}" in rationale:
        pay_gap = income_signals.get("median_pay_gap", 0)
        rationale = rationale.replace("{median_pay_gap}", str(pay_gap))
    
    # Clean up any remaining placeholders
    # Replace any remaining {variable} with empty string or a safe default
    remaining_placeholders = re.findall(r'\{[^}]+\}', rationale)
    for placeholder in remaining_placeholders:
        rationale = rationale.replace(placeholder, "")
    
    return rationale.strip()











