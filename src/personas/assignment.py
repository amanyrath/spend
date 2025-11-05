"""Persona assignment module for SpendSense.

This module implements hierarchical persona assignment based on behavioral signals.
Personas are assigned in priority order, with the first matching persona winning.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from src.database import db
from src.features.signal_detection import get_user_features

# Check if using Firestore
USE_FIRESTORE = (
    os.getenv('FIRESTORE_EMULATOR_HOST') is not None or 
    os.getenv('USE_FIREBASE_EMULATOR', '').lower() == 'true' or
    os.getenv('FIREBASE_SERVICE_ACCOUNT') is not None or 
    os.path.exists('firebase-service-account.json')
)

if USE_FIRESTORE:
    from src.database.firestore import store_persona as firestore_store_persona


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


def calculate_persona_scores(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate match percentage scores for all personas.
    
    Args:
        signals: Dictionary of all computed signals for user
        
    Returns:
        Dictionary with:
        - match_percentages: Dict mapping persona name to match percentage (0-100)
        - criteria_details: Dict mapping persona name to list of criteria details
        - primary_persona: Highest scoring persona name
    """
    match_percentages = {}
    criteria_details = {}
    
    if not signals:
        # No signals - default to general wellness
        match_percentages[PERSONA_GENERAL_WELLNESS] = 100.0
        criteria_details[PERSONA_GENERAL_WELLNESS] = ["No signals available"]
        return {
            "match_percentages": match_percentages,
            "criteria_details": criteria_details,
            "primary_persona": PERSONA_GENERAL_WELLNESS
        }
    
    # Calculate High Utilization score
    credit_signals = signals.get("credit_utilization", {})
    high_util_score = 0.0
    high_util_criteria = []
    
    if credit_signals:
        total_utilization = credit_signals.get("total_utilization", 0.0)
        utilization_decimal = total_utilization / 100.0 if total_utilization else 0.0
        
        if utilization_decimal >= 0.50:
            high_util_score += 25.0
            high_util_criteria.append("credit_utilization >= 50%")
        
        if credit_signals.get("interest_charged", 0.0) > 0:
            high_util_score += 25.0
            high_util_criteria.append("interest_charged > 0")
        
        if credit_signals.get("minimum_payment_only", False):
            high_util_score += 25.0
            high_util_criteria.append("minimum_payment_only")
        
        if credit_signals.get("is_overdue", False):
            high_util_score += 25.0
            high_util_criteria.append("is_overdue")
    
    match_percentages[PERSONA_HIGH_UTILIZATION] = high_util_score
    criteria_details[PERSONA_HIGH_UTILIZATION] = high_util_criteria
    
    # Calculate Variable Income score
    income_signals = signals.get("income_stability", {})
    variable_income_score = 0.0
    variable_income_criteria = []
    
    if income_signals:
        median_pay_gap = income_signals.get("median_pay_gap", 0)
        irregular_frequency = income_signals.get("irregular_frequency", False)
        cash_flow_buffer = income_signals.get("cash_flow_buffer", 0.0)
        
        income_irregular = median_pay_gap > 45 or irregular_frequency
        if income_irregular:
            variable_income_score += 50.0
            variable_income_criteria.append("irregular_income_pattern")
        
        if cash_flow_buffer < 1.0:
            variable_income_score += 50.0
            variable_income_criteria.append("cash_flow_buffer < 1.0")
    
    match_percentages[PERSONA_VARIABLE_INCOME] = variable_income_score
    criteria_details[PERSONA_VARIABLE_INCOME] = variable_income_criteria
    
    # Calculate Subscription-Heavy score
    subscription_signals = signals.get("subscriptions", {})
    subscription_heavy_score = 0.0
    subscription_heavy_criteria = []
    
    if subscription_signals:
        recurring_merchants = subscription_signals.get("recurring_merchants", [])
        monthly_recurring = subscription_signals.get("monthly_recurring", 0.0)
        subscription_share = subscription_signals.get("subscription_share", 0.0)
        subscription_share_decimal = subscription_share / 100.0 if subscription_share else 0.0
        
        if len(recurring_merchants) >= 3:
            subscription_heavy_score += 50.0
            subscription_heavy_criteria.append(f"recurring_merchants >= 3 ({len(recurring_merchants)} found)")
        
        if monthly_recurring >= 50.0 or subscription_share_decimal >= 0.10:
            subscription_heavy_score += 50.0
            subscription_heavy_criteria.append(f"monthly_recurring >= $50 OR subscription_share >= 10%")
    
    match_percentages[PERSONA_SUBSCRIPTION_HEAVY] = subscription_heavy_score
    criteria_details[PERSONA_SUBSCRIPTION_HEAVY] = subscription_heavy_criteria
    
    # Calculate Savings Builder score
    savings_signals = signals.get("savings_behavior", {})
    credit_signals = signals.get("credit_utilization", {})
    savings_builder_score = 0.0
    savings_builder_criteria = []
    
    if savings_signals:
        growth_rate = savings_signals.get("growth_rate", 0.0)
        growth_rate_decimal = growth_rate / 100.0 if growth_rate else 0.0
        net_inflow = savings_signals.get("net_inflow", 0.0)
        
        has_savings_activity = growth_rate_decimal >= 0.02 or net_inflow >= 200.0
        if has_savings_activity:
            savings_builder_score += 50.0
            savings_builder_criteria.append("savings_growth_rate >= 2% OR net_inflow >= $200")
        
        # Check credit utilization is low
        all_credit_low = True
        if credit_signals:
            total_utilization = credit_signals.get("total_utilization", 0.0)
            utilization_decimal = total_utilization / 100.0 if total_utilization else 0.0
            
            if utilization_decimal >= 0.30:
                all_credit_low = False
            else:
                accounts = credit_signals.get("accounts", [])
                for account in accounts:
                    account_utilization = account.get("utilization", 0.0)
                    account_utilization_decimal = account_utilization / 100.0 if account_utilization else 0.0
                    if account_utilization_decimal >= 0.30:
                        all_credit_low = False
                        break
        
        if all_credit_low:
            savings_builder_score += 50.0
            savings_builder_criteria.append("all_credit_utilization < 30%")
    
    match_percentages[PERSONA_SAVINGS_BUILDER] = savings_builder_score
    criteria_details[PERSONA_SAVINGS_BUILDER] = savings_builder_criteria
    
    # Calculate General Wellness score (baseline + bonus if no other persona scores high)
    general_wellness_score = 20.0  # Baseline
    general_wellness_criteria = ["baseline_score"]
    
    # If no other persona scores > 50%, add bonus
    max_other_score = max([
        match_percentages.get(PERSONA_HIGH_UTILIZATION, 0.0),
        match_percentages.get(PERSONA_VARIABLE_INCOME, 0.0),
        match_percentages.get(PERSONA_SUBSCRIPTION_HEAVY, 0.0),
        match_percentages.get(PERSONA_SAVINGS_BUILDER, 0.0)
    ])
    
    if max_other_score < 50.0:
        general_wellness_score += 30.0
        general_wellness_criteria.append("no_other_persona_strong_match")
    
    match_percentages[PERSONA_GENERAL_WELLNESS] = general_wellness_score
    criteria_details[PERSONA_GENERAL_WELLNESS] = general_wellness_criteria
    
    # Determine primary persona (highest scoring)
    primary_persona = max(match_percentages.items(), key=lambda x: x[1])[0]
    
    return {
        "match_percentages": match_percentages,
        "criteria_details": criteria_details,
        "primary_persona": primary_persona
    }


def calculate_persona_scores_vectorized(features_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate persona scores for all users using vectorized operations.
    
    Args:
        features_df: DataFrame with columns: user_id, time_window, subscriptions,
                    credit_utilization, savings_behavior, income_stability
                    Each signal column contains a dict with signal data
        
    Returns:
        DataFrame with columns: user_id, time_window, persona, primary_persona,
        match_high_utilization, match_variable_income, match_subscription_heavy,
        match_savings_builder, match_general_wellness, criteria_met,
        match_percentages, criteria_details
    """
    if features_df.empty:
        return pd.DataFrame()
    
    # Create a copy to avoid modifying original
    df = features_df.copy()
    
    # Helper function to safely extract nested dict values
    def safe_get(signal_dict, key, default=0.0):
        """Extract value from signal dict, handling NaN and missing keys."""
        if pd.isna(signal_dict) or not isinstance(signal_dict, dict):
            return default
        return signal_dict.get(key, default)
    
    # Extract credit utilization signals
    df['credit_total_utilization'] = df['credit_utilization'].apply(
        lambda x: safe_get(x, 'total_utilization', 0.0)
    )
    df['credit_utilization_decimal'] = df['credit_total_utilization'] / 100.0
    df['credit_interest_charged'] = df['credit_utilization'].apply(
        lambda x: safe_get(x, 'interest_charged', 0.0)
    )
    df['credit_minimum_payment_only'] = df['credit_utilization'].apply(
        lambda x: safe_get(x, 'minimum_payment_only', False)
    )
    df['credit_is_overdue'] = df['credit_utilization'].apply(
        lambda x: safe_get(x, 'is_overdue', False)
    )
    
    # Extract income stability signals
    df['income_median_pay_gap'] = df['income_stability'].apply(
        lambda x: safe_get(x, 'median_pay_gap', 0)
    )
    df['income_irregular_frequency'] = df['income_stability'].apply(
        lambda x: safe_get(x, 'irregular_frequency', False)
    )
    df['income_cash_flow_buffer'] = df['income_stability'].apply(
        lambda x: safe_get(x, 'cash_flow_buffer', 0.0)
    )
    
    # Extract subscription signals
    df['sub_recurring_merchants'] = df['subscriptions'].apply(
        lambda x: len(safe_get(x, 'recurring_merchants', [])) if isinstance(safe_get(x, 'recurring_merchants', []), list) else 0
    )
    df['sub_monthly_recurring'] = df['subscriptions'].apply(
        lambda x: safe_get(x, 'monthly_recurring', 0.0)
    )
    df['sub_subscription_share'] = df['subscriptions'].apply(
        lambda x: safe_get(x, 'subscription_share', 0.0) / 100.0 if safe_get(x, 'subscription_share', 0.0) else 0.0
    )
    
    # Extract savings behavior signals
    df['savings_growth_rate'] = df['savings_behavior'].apply(
        lambda x: safe_get(x, 'growth_rate', 0.0) / 100.0 if safe_get(x, 'growth_rate', 0.0) else 0.0
    )
    df['savings_net_inflow'] = df['savings_behavior'].apply(
        lambda x: safe_get(x, 'net_inflow', 0.0)
    )
    
    # Calculate High Utilization score
    high_util_score = np.zeros(len(df))
    high_util_criteria_list = []
    
    # Check each criterion
    mask_util_high = df['credit_utilization_decimal'] >= 0.50
    high_util_score[mask_util_high] += 25.0
    
    mask_interest = df['credit_interest_charged'] > 0
    high_util_score[mask_interest] += 25.0
    
    mask_min_payment = df['credit_minimum_payment_only'] == True
    high_util_score[mask_min_payment] += 25.0
    
    mask_overdue = df['credit_is_overdue'] == True
    high_util_score[mask_overdue] += 25.0
    
    # Build criteria strings
    for i in range(len(df)):
        criteria_parts = []
        if mask_util_high.iloc[i]:
            criteria_parts.append("credit_utilization >= 50%")
        if mask_interest.iloc[i]:
            criteria_parts.append("interest_charged > 0")
        if mask_min_payment.iloc[i]:
            criteria_parts.append("minimum_payment_only")
        if mask_overdue.iloc[i]:
            criteria_parts.append("is_overdue")
        high_util_criteria_list.append("; ".join(criteria_parts))
    
    # Check account-level utilization (requires iterating through accounts)
    def check_account_utilization(credit_dict):
        """Check if any account has utilization >= 50%."""
        if pd.isna(credit_dict) or not isinstance(credit_dict, dict):
            return False
        accounts = credit_dict.get('accounts', [])
        for account in accounts:
            if isinstance(account, dict):
                util = account.get('utilization', 0.0)
                util_decimal = util / 100.0 if util else 0.0
                if util_decimal >= 0.50:
                    return True
        return False
    
    mask_account_util = df['credit_utilization'].apply(check_account_utilization)
    high_util_score[mask_account_util] += 0.0  # Already counted in total_utilization
    # Note: Account-level checks are already factored into total_utilization in most cases
    
    df['match_high_utilization'] = high_util_score
    df['high_util_criteria'] = high_util_criteria_list
    
    # Calculate Variable Income score
    variable_income_score = np.zeros(len(df))
    variable_income_criteria_list = []
    
    mask_irregular = (df['income_median_pay_gap'] > 45) | (df['income_irregular_frequency'] == True)
    variable_income_score[mask_irregular] += 50.0
    
    mask_buffer_low = df['income_cash_flow_buffer'] < 1.0
    variable_income_score[mask_buffer_low] += 50.0
    
    # Build criteria strings
    for i in range(len(df)):
        criteria_parts = []
        if mask_irregular.iloc[i]:
            criteria_parts.append("irregular_income_pattern")
        if mask_buffer_low.iloc[i]:
            criteria_parts.append("cash_flow_buffer < 1.0")
        variable_income_criteria_list.append("; ".join(criteria_parts))
    
    df['match_variable_income'] = variable_income_score
    df['variable_income_criteria'] = variable_income_criteria_list
    
    # Calculate Subscription-Heavy score
    subscription_heavy_score = np.zeros(len(df))
    subscription_heavy_criteria_list = []
    
    mask_merchants = df['sub_recurring_merchants'] >= 3
    subscription_heavy_score[mask_merchants] += 50.0
    
    mask_spend = (df['sub_monthly_recurring'] >= 50.0) | (df['sub_subscription_share'] >= 0.10)
    subscription_heavy_score[mask_spend] += 50.0
    
    # Build criteria strings
    for i in range(len(df)):
        criteria_parts = []
        if mask_merchants.iloc[i]:
            criteria_parts.append(f"recurring_merchants >= 3 ({df['sub_recurring_merchants'].iloc[i]} found)")
        if mask_spend.iloc[i]:
            criteria_parts.append("monthly_recurring >= $50 OR subscription_share >= 10%")
        subscription_heavy_criteria_list.append("; ".join(criteria_parts))
    
    df['match_subscription_heavy'] = subscription_heavy_score
    df['subscription_heavy_criteria'] = subscription_heavy_criteria_list
    
    # Calculate Savings Builder score
    savings_builder_score = np.zeros(len(df))
    savings_builder_criteria_list = []
    
    mask_savings_activity = (df['savings_growth_rate'] >= 0.02) | (df['savings_net_inflow'] >= 200.0)
    savings_builder_score[mask_savings_activity] += 50.0
    
    # Check that all credit utilization is low
    def check_all_credit_low(credit_dict):
        """Check if all credit utilization is < 30%."""
        if pd.isna(credit_dict) or not isinstance(credit_dict, dict):
            return True  # No credit accounts, so criteria is met
        total_util = credit_dict.get('total_utilization', 0.0)
        util_decimal = total_util / 100.0 if total_util else 0.0
        if util_decimal >= 0.30:
            return False
        accounts = credit_dict.get('accounts', [])
        for account in accounts:
            if isinstance(account, dict):
                util = account.get('utilization', 0.0)
                util_decimal = util / 100.0 if util else 0.0
                if util_decimal >= 0.30:
                    return False
        return True
    
    mask_all_credit_low = df['credit_utilization'].apply(check_all_credit_low)
    savings_builder_score[mask_all_credit_low] += 50.0
    
    # Build criteria strings
    for i in range(len(df)):
        criteria_parts = []
        if mask_savings_activity.iloc[i]:
            criteria_parts.append("savings_growth_rate >= 2% OR net_inflow >= $200")
        if mask_all_credit_low.iloc[i]:
            criteria_parts.append("all_credit_utilization < 30%")
        savings_builder_criteria_list.append("; ".join(criteria_parts))
    
    df['match_savings_builder'] = savings_builder_score
    df['savings_builder_criteria'] = savings_builder_criteria_list
    
    # Calculate General Wellness score
    general_wellness_score = np.full(len(df), 20.0)  # Baseline
    general_wellness_criteria_list = []
    
    # Find max other score for each row
    max_other_score = df[['match_high_utilization', 'match_variable_income', 
                         'match_subscription_heavy', 'match_savings_builder']].max(axis=1)
    mask_no_strong_match = max_other_score < 50.0
    general_wellness_score[mask_no_strong_match] += 30.0
    
    # Build criteria strings
    for i in range(len(df)):
        criteria_parts = ["baseline_score"]
        if mask_no_strong_match.iloc[i]:
            criteria_parts.append("no_other_persona_strong_match")
        general_wellness_criteria_list.append("; ".join(criteria_parts))
    
    df['match_general_wellness'] = general_wellness_score
    df['general_wellness_criteria'] = general_wellness_criteria_list
    
    # Determine primary persona (highest scoring)
    persona_scores = df[['match_high_utilization', 'match_variable_income',
                       'match_subscription_heavy', 'match_savings_builder',
                       'match_general_wellness']]
    
    persona_names = [PERSONA_HIGH_UTILIZATION, PERSONA_VARIABLE_INCOME,
                    PERSONA_SUBSCRIPTION_HEAVY, PERSONA_SAVINGS_BUILDER,
                    PERSONA_GENERAL_WELLNESS]
    
    primary_persona_idx = persona_scores.values.argmax(axis=1)
    df['primary_persona'] = [persona_names[idx] for idx in primary_persona_idx]
    df['persona'] = df['primary_persona']  # For backward compatibility
    
    # Build criteria_met for primary persona
    def get_criteria_for_persona(row):
        """Get criteria list for the primary persona."""
        persona = row['primary_persona']
        if persona == PERSONA_HIGH_UTILIZATION:
            return row['high_util_criteria'].split('; ') if row['high_util_criteria'] else []
        elif persona == PERSONA_VARIABLE_INCOME:
            return row['variable_income_criteria'].split('; ') if row['variable_income_criteria'] else []
        elif persona == PERSONA_SUBSCRIPTION_HEAVY:
            return row['subscription_heavy_criteria'].split('; ') if row['subscription_heavy_criteria'] else []
        elif persona == PERSONA_SAVINGS_BUILDER:
            return row['savings_builder_criteria'].split('; ') if row['savings_builder_criteria'] else []
        elif persona == PERSONA_GENERAL_WELLNESS:
            return row['general_wellness_criteria'].split('; ') if row['general_wellness_criteria'] else []
        return []
    
    df['criteria_met'] = df.apply(get_criteria_for_persona, axis=1)
    
    # Build match_percentages and criteria_details as JSON strings
    def build_match_percentages(row):
        """Build match_percentages dict."""
        return {
            PERSONA_HIGH_UTILIZATION: float(row['match_high_utilization']),
            PERSONA_VARIABLE_INCOME: float(row['match_variable_income']),
            PERSONA_SUBSCRIPTION_HEAVY: float(row['match_subscription_heavy']),
            PERSONA_SAVINGS_BUILDER: float(row['match_savings_builder']),
            PERSONA_GENERAL_WELLNESS: float(row['match_general_wellness'])
        }
    
    def build_criteria_details(row):
        """Build criteria_details dict."""
        return {
            PERSONA_HIGH_UTILIZATION: row['high_util_criteria'].split('; ') if row['high_util_criteria'] else [],
            PERSONA_VARIABLE_INCOME: row['variable_income_criteria'].split('; ') if row['variable_income_criteria'] else [],
            PERSONA_SUBSCRIPTION_HEAVY: row['subscription_heavy_criteria'].split('; ') if row['subscription_heavy_criteria'] else [],
            PERSONA_SAVINGS_BUILDER: row['savings_builder_criteria'].split('; ') if row['savings_builder_criteria'] else [],
            PERSONA_GENERAL_WELLNESS: row['general_wellness_criteria'].split('; ') if row['general_wellness_criteria'] else []
        }
    
    df['match_percentages'] = df.apply(build_match_percentages, axis=1)
    df['criteria_details'] = df.apply(build_criteria_details, axis=1)
    
    # Select and return final columns
    result_df = df[[
        'user_id', 'time_window', 'persona', 'primary_persona',
        'match_high_utilization', 'match_variable_income', 'match_subscription_heavy',
        'match_savings_builder', 'match_general_wellness', 'criteria_met',
        'match_percentages', 'criteria_details'
    ]].copy()
    
    return result_df


def assign_persona(user_id: str, time_window: str = "30d") -> str:
    """Assign persona to user based on percentage match scores.
    
    Calculates match percentages for all personas and sets primary_persona
    to the highest scoring persona. Returns primary_persona for backward compatibility.
    
    Args:
        user_id: User identifier
        time_window: Time window string ("30d" or "180d")
        
    Returns:
        Primary persona name (highest scoring persona)
    """
    # Get user signals
    signals = get_user_features(user_id, time_window)
    
    # Calculate scores for all personas
    score_results = calculate_persona_scores(signals)
    match_percentages = score_results["match_percentages"]
    criteria_details = score_results["criteria_details"]
    primary_persona = score_results["primary_persona"]
    
    # Store persona assignment with all scores
    store_persona_assignment(
        user_id,
        time_window,
        primary_persona,
        criteria_details.get(primary_persona, []),
        match_percentages,
        criteria_details
    )
    
    return primary_persona


def store_persona_assignment(
    user_id: str,
    time_window: str,
    persona: str,
    criteria_met: List[str],
    match_percentages: Dict[str, float] = None,
    criteria_details: Dict[str, List[str]] = None
) -> None:
    """Store persona assignment in database.
    
    Args:
        user_id: User identifier
        time_window: Time window string ("30d" or "180d")
        persona: Primary persona name (highest scoring persona)
        criteria_met: List of criteria strings that were met for primary persona
        match_percentages: Dict mapping persona name to match percentage (0-100)
        criteria_details: Dict mapping persona name to list of criteria details
    """
    criteria_json = json.dumps(criteria_met)
    assigned_at = datetime.now().isoformat()
    
    # Extract match percentages (default to 0.0 if not provided)
    if match_percentages is None:
        match_percentages = {}
    if criteria_details is None:
        criteria_details = {}
    
    match_high_util = match_percentages.get(PERSONA_HIGH_UTILIZATION, 0.0)
    match_var_income = match_percentages.get(PERSONA_VARIABLE_INCOME, 0.0)
    match_sub_heavy = match_percentages.get(PERSONA_SUBSCRIPTION_HEAVY, 0.0)
    match_savings = match_percentages.get(PERSONA_SAVINGS_BUILDER, 0.0)
    match_general = match_percentages.get(PERSONA_GENERAL_WELLNESS, 0.0)
    
    # Primary persona is the same as persona parameter (for backward compat)
    primary_persona = persona
    
    # Store in database (SQLite or Firestore)
    if USE_FIRESTORE:
        # Store in Firestore
        persona_data = {
            'user_id': user_id,
            'time_window': time_window,
            'persona': persona,
            'primary_persona': primary_persona,
            'criteria_met': criteria_met,
            'match_high_utilization': match_high_util,
            'match_variable_income': match_var_income,
            'match_subscription_heavy': match_sub_heavy,
            'match_savings_builder': match_savings,
            'match_general_wellness': match_general,
            'assigned_at': assigned_at
        }
        firestore_store_persona(user_id, persona_data)
    else:
        # Store in SQLite
        # Delete existing assignment if it exists and insert new one (idempotent)
        delete_query = """
            DELETE FROM persona_assignments
            WHERE user_id = ? AND time_window = ?
        """
        insert_query = """
            INSERT INTO persona_assignments (
                user_id, time_window, persona, criteria_met, assigned_at,
                match_high_utilization, match_variable_income, match_subscription_heavy,
                match_savings_builder, match_general_wellness, primary_persona
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        with db.get_db_connection() as conn:
            conn.execute(delete_query, (user_id, time_window))
            conn.execute(insert_query, (
                user_id, time_window, persona, criteria_json, assigned_at,
                match_high_util, match_var_income, match_sub_heavy,
                match_savings, match_general, primary_persona
            ))


def get_persona_assignment(user_id: str, time_window: str = "30d") -> Optional[Dict[str, Any]]:
    """Retrieve persona assignment for a user.
    
    Args:
        user_id: User identifier
        time_window: Time window string ("30d" or "180d")
        
    Returns:
        Dictionary with persona assignment data including match percentages, or None if not found
    """
    if USE_FIRESTORE:
        # Get from Firestore
        from src.database.firestore import get_persona_assignments as firestore_get_persona_assignments
        personas = firestore_get_persona_assignments(user_id)
        
        # Find the most recent assignment for the requested time window
        matching_personas = [p for p in personas if p.get('time_window') == time_window]
        if not matching_personas:
            return None
        
        # Get most recent (they're already sorted by assigned_at DESC)
        persona_data = matching_personas[0]
        
        # Build match_percentages dict
        match_percentages = {
            PERSONA_HIGH_UTILIZATION: persona_data.get("match_high_utilization", 0.0) or 0.0,
            PERSONA_VARIABLE_INCOME: persona_data.get("match_variable_income", 0.0) or 0.0,
            PERSONA_SUBSCRIPTION_HEAVY: persona_data.get("match_subscription_heavy", 0.0) or 0.0,
            PERSONA_SAVINGS_BUILDER: persona_data.get("match_savings_builder", 0.0) or 0.0,
            PERSONA_GENERAL_WELLNESS: persona_data.get("match_general_wellness", 0.0) or 0.0
        }
        
        # Primary persona (use primary_persona if available, otherwise fall back to persona)
        primary_persona = persona_data.get("primary_persona") or persona_data.get("persona")
        
        # Parse criteria_met if it's a string
        criteria_met = persona_data.get("criteria_met", [])
        if isinstance(criteria_met, str):
            try:
                criteria_met = json.loads(criteria_met)
            except json.JSONDecodeError:
                criteria_met = []
        
        return {
            "persona": persona_data.get("persona", primary_persona),  # Backward compatibility
            "primary_persona": primary_persona,
            "match_percentages": match_percentages,
            "criteria_met": criteria_met,
            "assigned_at": persona_data.get("assigned_at", "")
        }
    else:
        # SQLite path
        query = """
            SELECT persona, criteria_met, assigned_at,
                   match_high_utilization, match_variable_income, match_subscription_heavy,
                   match_savings_builder, match_general_wellness, primary_persona
            FROM persona_assignments
            WHERE user_id = ? AND time_window = ?
        """
        row = db.fetch_one(query, (user_id, time_window))
        
        if not row:
            return None
        
        # Build match_percentages dict
        match_percentages = {
            PERSONA_HIGH_UTILIZATION: row.get("match_high_utilization", 0.0) or 0.0,
            PERSONA_VARIABLE_INCOME: row.get("match_variable_income", 0.0) or 0.0,
            PERSONA_SUBSCRIPTION_HEAVY: row.get("match_subscription_heavy", 0.0) or 0.0,
            PERSONA_SAVINGS_BUILDER: row.get("match_savings_builder", 0.0) or 0.0,
            PERSONA_GENERAL_WELLNESS: row.get("match_general_wellness", 0.0) or 0.0
        }
        
        # Primary persona (use primary_persona if available, otherwise fall back to persona)
        primary_persona = row.get("primary_persona") or row["persona"]
        
        return {
            "persona": row["persona"],  # Backward compatibility (same as primary_persona)
            "primary_persona": primary_persona,
            "match_percentages": match_percentages,
            "criteria_met": json.loads(row["criteria_met"]),
            "assigned_at": row["assigned_at"]
        }

