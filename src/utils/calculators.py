"""Financial calculation utilities for SpendSense education modules."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import math


def calculate_balance_transfer_savings(
    current_balance: float,
    current_apr: float,
    transfer_fee_percent: float = 5.0,
    intro_apr: float = 0.0,
    intro_period_months: int = 18,
    current_monthly_payment: float = 0.0,
    additional_monthly_payment: float = 0.0
) -> Dict[str, Any]:
    """Calculate savings from a balance transfer.
    
    Args:
        current_balance: Current credit card balance
        current_apr: Current APR as percentage (e.g., 24.99 for 24.99%)
        transfer_fee_percent: Balance transfer fee as percentage (e.g., 5.0 for 5%)
        intro_apr: Introductory APR as percentage (typically 0.0)
        intro_period_months: Number of months at intro APR
        current_monthly_payment: Current monthly payment amount
        additional_monthly_payment: Additional payment to make each month
        
    Returns:
        Dictionary with:
        - transfer_fee: Fee amount
        - new_balance: Balance after transfer fee
        - monthly_payment_needed: Required monthly payment
        - payoff_months: Months to pay off at intro APR
        - total_interest_current: Total interest with current card
        - total_interest_new: Total interest with new card
        - total_savings: Total savings after transfer fee
        - monthly_savings: Monthly savings during intro period
    """
    # Calculate transfer fee
    transfer_fee = current_balance * (transfer_fee_percent / 100.0)
    new_balance = current_balance + transfer_fee
    
    # Calculate monthly payment needed
    total_monthly_payment = current_monthly_payment + additional_monthly_payment
    
    # If no payment specified, estimate minimum payment (2% of balance or $25, whichever is higher)
    if total_monthly_payment <= 0:
        total_monthly_payment = max(new_balance * 0.02, 25.0)
    
    # Calculate payoff time at 0% APR
    if total_monthly_payment >= new_balance:
        payoff_months = 1
    else:
        payoff_months = math.ceil(new_balance / total_monthly_payment)
    
    # Cap payoff months to intro period (assume regular APR kicks in after)
    payoff_months_at_intro = min(payoff_months, intro_period_months)
    remaining_balance = max(0, new_balance - (total_monthly_payment * payoff_months_at_intro))
    
    # Calculate interest with current card (simplified: assume minimum payment)
    # Using monthly APR approximation
    monthly_apr_current = current_apr / 12.0 / 100.0
    remaining_balance_current = current_balance
    
    # Estimate months to pay off with current card (simplified calculation)
    if total_monthly_payment <= 0:
        monthly_payment_current = max(current_balance * 0.02, 25.0)
    else:
        monthly_payment_current = total_monthly_payment
    
    total_interest_current = 0.0
    months_current = 0
    balance_current = current_balance
    
    # Simulate paying off with current APR
    while balance_current > 0.01 and months_current < 120:  # Cap at 10 years
        interest_this_month = balance_current * monthly_apr_current
        total_interest_current += interest_this_month
        balance_current = balance_current + interest_this_month - monthly_payment_current
        if balance_current <= 0:
            balance_current = 0
        months_current += 1
    
    # Calculate interest with new card (only after intro period if balance remains)
    total_interest_new = 0.0
    if remaining_balance > 0:
        # Use regular APR after intro period (estimate at 20% if not specified)
        regular_apr = 20.0  # Default estimate
        monthly_apr_new = regular_apr / 12.0 / 100.0
        balance_new = remaining_balance
        
        months_new = 0
        while balance_new > 0.01 and months_new < 120:
            interest_this_month = balance_new * monthly_apr_new
            total_interest_new += interest_this_month
            balance_new = balance_new + interest_this_month - total_monthly_payment
            if balance_new <= 0:
                balance_new = 0
            months_new += 1
    
    # Calculate savings
    total_savings = total_interest_current - total_interest_new - transfer_fee
    
    # Monthly savings during intro period (current interest vs 0%)
    monthly_interest_current = current_balance * monthly_apr_current
    monthly_savings = monthly_interest_current if payoff_months_at_intro > 0 else 0.0
    
    return {
        "transfer_fee": round(transfer_fee, 2),
        "new_balance": round(new_balance, 2),
        "monthly_payment_needed": round(total_monthly_payment, 2),
        "payoff_months": payoff_months_at_intro,
        "total_interest_current": round(total_interest_current, 2),
        "total_interest_new": round(total_interest_new, 2),
        "total_savings": round(total_savings, 2),
        "monthly_savings": round(monthly_savings, 2),
        "payoff_months_current": months_current
    }


def calculate_subscription_savings(
    subscriptions: List[Dict[str, Any]],
    selected_subscription_indices: List[int]
) -> Dict[str, Any]:
    """Calculate savings from canceling selected subscriptions.
    
    Args:
        subscriptions: List of subscription dicts with 'merchant', 'amount', 'monthly_equivalent'
        selected_subscription_indices: List of indices of subscriptions to cancel
        
    Returns:
        Dictionary with:
        - monthly_savings: Monthly savings amount
        - yearly_savings: Yearly savings amount
        - canceled_count: Number of subscriptions canceled
    """
    selected_subscriptions = [
        subscriptions[i] for i in selected_subscription_indices 
        if i < len(subscriptions)
    ]
    
    monthly_savings = sum(
        sub.get('monthly_equivalent', sub.get('amount', 0))
        for sub in selected_subscriptions
    )
    
    yearly_savings = monthly_savings * 12
    
    return {
        "monthly_savings": round(monthly_savings, 2),
        "yearly_savings": round(yearly_savings, 2),
        "canceled_count": len(selected_subscriptions)
    }


def calculate_savings_goal_timeline(
    current_savings: float,
    goal_amount: float,
    monthly_savings_rate: float
) -> Dict[str, Any]:
    """Calculate timeline to reach savings goal.
    
    Args:
        current_savings: Current savings balance
        goal_amount: Target savings goal
        monthly_savings_rate: Amount saved per month
        
    Returns:
        Dictionary with:
        - months_needed: Number of months to reach goal
        - years_needed: Number of years to reach goal (decimal)
        - amount_needed: Additional amount needed
        - is_achievable: Boolean indicating if goal is achievable
    """
    amount_needed = max(0, goal_amount - current_savings)
    
    if monthly_savings_rate <= 0:
        return {
            "months_needed": None,
            "years_needed": None,
            "amount_needed": round(amount_needed, 2),
            "is_achievable": False
        }
    
    months_needed = math.ceil(amount_needed / monthly_savings_rate)
    years_needed = months_needed / 12.0
    
    return {
        "months_needed": months_needed,
        "years_needed": round(years_needed, 2),
        "amount_needed": round(amount_needed, 2),
        "is_achievable": True
    }


def generate_budget_breakdown(
    avg_monthly_income: float,
    avg_monthly_expenses: float,
    category_spending: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate recommended budget breakdown.
    
    Args:
        avg_monthly_income: Average monthly income
        avg_monthly_expenses: Average monthly expenses
        category_spending: List of dicts with 'category' and 'amount' keys
        
    Returns:
        Dictionary with:
        - essentials_target: Target for essentials (50-60% of income)
        - savings_target: Target for savings (20% of income)
        - discretionary_target: Target for discretionary (20-30% of income)
        - category_allocations: Recommended allocations by category
        - rationale: Explanation of budget breakdown
    """
    # Use 50/30/20 rule as base, adjust if expenses are high
    if avg_monthly_expenses > avg_monthly_income * 0.9:
        # Tight budget: 60/20/20
        essentials_percent = 0.60
        savings_percent = 0.20
        discretionary_percent = 0.20
    else:
        # Standard budget: 50/30/20
        essentials_percent = 0.50
        savings_percent = 0.20
        discretionary_percent = 0.30
    
    essentials_target = avg_monthly_income * essentials_percent
    savings_target = avg_monthly_income * savings_percent
    discretionary_target = avg_monthly_income * discretionary_percent
    
    # Categorize current spending
    essential_categories = [
        'Housing', 'Utilities', 'Transportation', 'Groceries',
        'Healthcare', 'Insurance', 'Debt Payments'
    ]
    
    category_allocations = []
    current_essentials = 0.0
    current_discretionary = 0.0
    
    for cat_spend in category_spending:
        category = cat_spend.get('category', '')
        amount = cat_spend.get('amount', 0)
        
        is_essential = any(
            essential.lower() in category.lower() 
            for essential in essential_categories
        )
        
        if is_essential:
            current_essentials += amount
            allocation_type = 'essential'
        else:
            current_discretionary += amount
            allocation_type = 'discretionary'
        
        category_allocations.append({
            "category": category,
            "current_spending": round(amount, 2),
            "recommended_max": round(
                essentials_target if is_essential else discretionary_target,
                2
            ),
            "type": allocation_type,
            "over_budget": amount > (essentials_target if is_essential else discretionary_target)
        })
    
    # Generate rationale
    if avg_monthly_expenses > avg_monthly_income:
        rationale = (
            f"Your expenses (${avg_monthly_expenses:,.0f}/month) exceed your income "
            f"(${avg_monthly_income:,.0f}/month). We recommend focusing on essentials first, "
            f"then building savings when cash flow improves."
        )
    elif avg_monthly_expenses > avg_monthly_income * 0.9:
        rationale = (
            f"Your expenses are ${avg_monthly_expenses:,.0f}/month, which is quite tight. "
            f"Consider reducing discretionary spending to build a buffer."
        )
    else:
        rationale = (
            f"Based on your average income of ${avg_monthly_income:,.0f}/month, "
            f"we recommend allocating {essentials_percent*100:.0f}% to essentials, "
            f"{savings_percent*100:.0f}% to savings, and {discretionary_percent*100:.0f}% to discretionary spending."
        )
    
    return {
        "essentials_target": round(essentials_target, 2),
        "savings_target": round(savings_target, 2),
        "discretionary_target": round(discretionary_target, 2),
        "essentials_percent": essentials_percent * 100,
        "savings_percent": savings_percent * 100,
        "discretionary_percent": discretionary_percent * 100,
        "category_allocations": category_allocations,
        "current_essentials": round(current_essentials, 2),
        "current_discretionary": round(current_discretionary, 2),
        "rationale": rationale
    }







