"""Recommendation engine for SpendSense.

This module generates personalized recommendations by matching content
and offers to user personas and signals, generating rationales, and
creating decision traces for auditability.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

# Make SQLite imports optional for Vercel deployment
try:
    from src.database import db
    HAS_SQLITE = True
except ImportError:
    # SQLite not available - use Firestore only
    HAS_SQLITE = False
    db = None

from src.personas.assignment import get_persona_assignment
from src.features.signal_detection import get_user_features
from src.recommend.content_catalog import (
    get_education_content,
    get_partner_offers,
    get_content_by_persona
)
from src.recommend.rationale_generator import generate_rationale
from src.guardrails.guardrails_ai import get_guardrails
from src.utils.logging import get_logger

logger = get_logger("recommend.engine")


def match_education_content(persona: str, signals: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Match education content to user's persona and signals.
    
    Args:
        persona: User's assigned persona
        signals: Dictionary of all computed signals
        
    Returns:
        List of 3-5 matched education content items
    """
    # Get content for this persona
    persona_content = get_content_by_persona(persona)
    
    if not persona_content:
        return []
    
    # Filter by trigger signals (if available)
    matched_content = []
    
    for item in persona_content:
        trigger_signals = item.get("trigger_signals", [])
        
        # If no trigger signals specified, include item
        if not trigger_signals:
            matched_content.append(item)
            continue
        
        # Check if any trigger signal matches
        matches = False
        
        for trigger in trigger_signals:
            if trigger == "credit_utilization_high":
                credit_signals = signals.get("credit_utilization", {})
                utilization = credit_signals.get("total_utilization", 0.0)
                if utilization >= 50.0:
                    matches = True
                    break
            elif trigger == "minimum_payment_only":
                credit_signals = signals.get("credit_utilization", {})
                if credit_signals.get("minimum_payment_only", False):
                    matches = True
                    break
            elif trigger == "interest_charged":
                credit_signals = signals.get("credit_utilization", {})
                if credit_signals.get("interest_charged", 0.0) > 0:
                    matches = True
                    break
            elif trigger == "irregular_frequency":
                income_signals = signals.get("income_stability", {})
                if income_signals.get("irregular_frequency", False):
                    matches = True
                    break
            elif trigger == "median_pay_gap_high":
                income_signals = signals.get("income_stability", {})
                if income_signals.get("median_pay_gap", 0) > 45:
                    matches = True
                    break
            elif trigger == "cash_flow_buffer_low":
                income_signals = signals.get("income_stability", {})
                if income_signals.get("cash_flow_buffer", 0.0) < 1.0:
                    matches = True
                    break
            elif trigger == "subscription_count_high":
                subscription_signals = signals.get("subscriptions", {})
                if len(subscription_signals.get("recurring_merchants", [])) >= 3:
                    matches = True
                    break
            elif trigger == "monthly_recurring_high":
                subscription_signals = signals.get("subscriptions", {})
                if subscription_signals.get("monthly_recurring", 0.0) >= 50.0:
                    matches = True
                    break
            elif trigger == "savings_growth_rate_positive":
                savings_signals = signals.get("savings_behavior", {})
                if savings_signals.get("growth_rate", 0.0) > 0:
                    matches = True
                    break
            elif trigger == "emergency_fund_adequate":
                savings_signals = signals.get("savings_behavior", {})
                if savings_signals.get("emergency_fund_coverage", 0.0) >= 3.0:
                    matches = True
                    break
            elif trigger == "savings_balance_positive":
                savings_signals = signals.get("savings_behavior", {})
                if savings_signals.get("total_savings", 0.0) > 0:
                    matches = True
                    break
        
        if matches:
            matched_content.append(item)
    
    # If no matches from triggers, use all persona content
    if not matched_content:
        matched_content = persona_content
    
    # Return 3-5 items (or all if fewer than 3)
    return matched_content[:5]


def check_offer_eligibility(offer: Dict[str, Any], signals: Dict[str, Any]) -> bool:
    """Check if user is eligible for a partner offer.
    
    Args:
        offer: Partner offer dictionary
        signals: Dictionary of all computed signals
        
    Returns:
        True if user is eligible, False otherwise
    """
    eligibility = offer.get("eligibility_criteria", {})
    
    if not eligibility:
        return True  # No criteria means available to all
    
    # Check credit utilization
    if "credit_utilization" in eligibility:
        credit_signals = signals.get("credit_utilization", {})
        utilization = credit_signals.get("total_utilization", 0.0)
        utilization_decimal = utilization / 100.0
        
        criteria = eligibility["credit_utilization"]
        if "min" in criteria and utilization_decimal < criteria["min"]:
            return False
        if "max" in criteria and utilization_decimal > criteria["max"]:
            return False
    
    # Check overdue status
    if "is_overdue" in eligibility:
        credit_signals = signals.get("credit_utilization", {})
        is_overdue = credit_signals.get("is_overdue", False)
        expected = eligibility["is_overdue"].get("equals", False)
        if is_overdue != expected:
            return False
    
    # Check subscription count
    if "subscription_count" in eligibility:
        subscription_signals = signals.get("subscriptions", {})
        count = len(subscription_signals.get("recurring_merchants", []))
        criteria = eligibility["subscription_count"]
        if "min" in criteria and count < criteria["min"]:
            return False
    
    # Check savings balance
    if "savings_balance" in eligibility:
        savings_signals = signals.get("savings_behavior", {})
        balance = savings_signals.get("total_savings", 0.0)
        criteria = eligibility["savings_balance"]
        if "min" in criteria and balance < criteria["min"]:
            return False
    
    return True


def build_customer_info_from_signals(signals: Dict[str, Any]) -> Optional['CustomerInfo']:
    """Build CustomerInfo from SpendSense signals for credit offers API.
    
    This helper function converts SpendSense signal format to credit offers
    CustomerInfo format, handling type conversions and missing fields gracefully.
    
    Args:
        signals: Dictionary of SpendSense signals
        
    Returns:
        CustomerInfo object or None if conversion fails
    """
    try:
        from src.recommend.credit_offers import CustomerInfo, UtilizationLevel, AccountUtilization
        
        credit_signal = signals.get("credit_utilization", {})
        savings_signal = signals.get("savings_behavior", {})
        
        # Convert utilization_level string to enum with error handling
        utilization_level_str = credit_signal.get("utilization_level", "low").lower()
        try:
            utilization_level = UtilizationLevel(utilization_level_str)
        except ValueError:
            # Default to LOW if invalid value
            logger.warning(f"Invalid utilization_level '{utilization_level_str}', defaulting to LOW")
            utilization_level = UtilizationLevel.LOW
        
        # Build per_account_utilization list
        per_account_utilization = []
        accounts = credit_signal.get("accounts", [])
        for acc in accounts:
            try:
                per_account_utilization.append(AccountUtilization(
                    account_id=acc.get("account_id", ""),
                    utilization=float(acc.get("utilization", 0.0)),
                    credit_limit=float(acc.get("limit", 0.0)),
                    balance=float(acc.get("balance", 0.0))
                ))
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error parsing account utilization: {e}, skipping account")
                continue
        
        # Build CustomerInfo with defaults for missing fields
        try:
            customer_info = CustomerInfo(
                total_utilization=float(credit_signal.get("total_utilization", 0.0)),
                utilization_level=utilization_level,
                interest_charged=float(credit_signal.get("interest_charged", 0.0)),
                minimum_payment_only=bool(credit_signal.get("minimum_payment_only", False)),
                is_overdue=bool(credit_signal.get("is_overdue", False)),
                online_spending_share=float(credit_signal.get("online_spending_share", 0.0)),
                per_account_utilization=per_account_utilization if per_account_utilization else None,
                total_savings=float(savings_signal.get("total_savings", 0.0)),
                net_inflow=float(savings_signal.get("net_inflow", 0.0)),
                growth_rate=float(savings_signal.get("growth_rate", 0.0)),
                emergency_fund_coverage=float(savings_signal.get("emergency_fund_coverage", 0.0)),
                avg_monthly_savings=float(savings_signal.get("avg_monthly_savings", 0.0))
            )
            return customer_info
        except (ValueError, TypeError) as e:
            logger.error(f"Error building CustomerInfo: {e}")
            return None
            
    except ImportError as e:
        logger.error(f"Error importing credit_offers module: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error building CustomerInfo: {e}", exc_info=True)
        return None


def match_offers(signals: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Match partner offers based on eligibility criteria.
    
    Includes both existing partner offers and credit offers from credit offers API.
    
    Args:
        signals: Dictionary of all computed signals
        
    Returns:
        List of 1-3 eligible partner offers
    """
    all_offers = get_partner_offers()
    
    eligible_offers = [
        offer for offer in all_offers
        if check_offer_eligibility(offer, signals)
    ]
    
    # Add credit offers from credit offers API
    try:
        from src.recommend.credit_offers import create_prequalification
        
        customer_info = build_customer_info_from_signals(signals)
        
        if customer_info:
            prequal_response = create_prequalification(customer_info)
            
            # Transform ProductOffer to partner offer format
            for product in prequal_response.qualifiedProducts:
                if product.matchPercentage >= 60:  # Match threshold
                    try:
                        partner_offer = {
                            "offer_id": product.productId,
                            "type": "partner_offer",
                            "title": product.productDisplayName,
                            "partner": "Credit Partner",  # Default partner name
                            "summary": ". ".join(product.mainMarketingCopy),
                            "rationale_template": product.matchReason,
                            "eligibility_criteria": {},  # Already filtered by match percentage
                            # Preserve credit-specific metadata
                            "credit_rating": product.creditRating.value,
                            "match_percentage": product.matchPercentage,
                            "purchase_apr": product.purchaseApr,
                            "intro_purchase_apr": product.introPurchaseApr,
                            "intro_balance_transfer_apr": product.introBalanceTransferApr,
                            "balance_transfer_fee": product.balanceTransferFee,
                            "annual_fee": product.annualMembershipFee,
                            "bonus_amount": product.bonusAmount,
                            "bonus_requirement": product.bonusRequirement,
                            "estimated_savings": product.estimatedSavings,
                            "tier": product.tier,
                            "code": product.code,
                            "images": product.images
                        }
                        eligible_offers.append(partner_offer)
                    except Exception as e:
                        logger.warning(f"Error transforming ProductOffer {product.productId}: {e}, skipping")
                        continue
        else:
            logger.debug("Could not build CustomerInfo from signals, skipping credit offers")
            
    except ImportError as e:
        logger.warning(f"Credit offers module not available: {e}, continuing with existing offers only")
    except Exception as e:
        logger.warning(f"Error fetching credit offers: {e}, continuing with existing offers only", exc_info=True)
    
    # Return 1-3 offers total (combining both sources)
    return eligible_offers[:3]


def create_decision_trace(
    recommendation: Dict[str, Any],
    signals: Dict[str, Any],
    persona: str
) -> Dict[str, Any]:
    """Create decision trace for a recommendation.
    
    Args:
        recommendation: Recommendation dictionary
        signals: Dictionary of all computed signals
        persona: User's assigned persona
        
    Returns:
        Decision trace dictionary
    """
    # Identify which signals were used
    signals_used = []
    
    content_id = recommendation.get("content_id") or recommendation.get("offer_id")
    
    # Extract relevant signal values based on content type
    if recommendation.get("type") == "education":
        # For education content, check which signals are relevant
        credit_signals = signals.get("credit_utilization", {})
        if credit_signals:
            utilization = credit_signals.get("total_utilization", 0.0)
            if utilization > 0:
                signals_used.append({
                    "signal": "credit_utilization",
                    "value": utilization,
                    "threshold": 50.0
                })
        
        subscription_signals = signals.get("subscriptions", {})
        if subscription_signals:
            count = len(subscription_signals.get("recurring_merchants", []))
            if count > 0:
                signals_used.append({
                    "signal": "subscription_count",
                    "value": count,
                    "threshold": 3
                })
    
    guardrails_passed = {
        "tone_check": recommendation.get("tone_valid", True),
        "eligibility_check": recommendation.get("eligible", True)
    }
    
    return {
        "persona_match": persona,
        "content_id": content_id,
        "signals_used": signals_used,
        "guardrails_passed": guardrails_passed,
        "timestamp": datetime.now().isoformat()
    }


def generate_recommendations(user_id: str, time_window: str = "30d") -> List[Dict[str, Any]]:
    """Generate personalized recommendations for a user.
    
    Args:
        user_id: User identifier
        time_window: Time window string ("30d" or "180d")
        
    Returns:
        List of recommendation dictionaries
    """
    # Get user persona
    persona_assignment = get_persona_assignment(user_id, time_window)
    if not persona_assignment:
        return []
    
    # Use primary_persona (same as persona for backward compatibility)
    persona = persona_assignment.get("primary_persona") or persona_assignment["persona"]
    
    # Get user signals
    signals = get_user_features(user_id, time_window)
    if not signals:
        return []
    
    recommendations = []
    
    # Match education content
    education_items = match_education_content(persona, signals)
    
    for item in education_items:
        # Generate rationale
        rationale = generate_rationale(item["rationale_template"], signals, item)
        
        # Validate tone
        guardrails = get_guardrails()
        is_valid, _, _ = guardrails.validate(rationale)
        tone_valid = is_valid
        
        if not tone_valid:
            # Skip if tone validation fails
            continue
        
        # Create recommendation
        recommendation_id = f"rec_{uuid.uuid4().hex[:12]}"
        
        recommendation = {
            "recommendation_id": recommendation_id,
            "user_id": user_id,
            "type": "education",
            "content_id": item["content_id"],
            "title": item["title"],
            "rationale": rationale,
            "tone_valid": tone_valid,
            "eligible": True
        }
        
        # Create decision trace
        decision_trace = create_decision_trace(recommendation, signals, persona)
        recommendation["decision_trace"] = decision_trace
        
        recommendations.append(recommendation)
    
    # Match partner offers
    offers = match_offers(signals)
    
    for offer in offers:
        # Generate rationale
        rationale = generate_rationale(offer["rationale_template"], signals, offer)
        
        # Validate tone
        guardrails = get_guardrails()
        is_valid, _, _ = guardrails.validate(rationale)
        tone_valid = is_valid
        
        if not tone_valid:
            continue
        
        # Create recommendation
        recommendation_id = f"rec_{uuid.uuid4().hex[:12]}"
        
        recommendation = {
            "recommendation_id": recommendation_id,
            "user_id": user_id,
            "type": "partner_offer",
            "content_id": offer["offer_id"],
            "title": offer["title"],
            "rationale": rationale,
            "tone_valid": tone_valid,
            "eligible": True
        }
        
        # Create decision trace
        decision_trace = create_decision_trace(recommendation, signals, persona)
        recommendation["decision_trace"] = decision_trace
        
        recommendations.append(recommendation)
    
    # Store recommendations in database
    for rec in recommendations:
        store_recommendation(rec)
    
    return recommendations


def store_recommendation(recommendation: Dict[str, Any]) -> None:
    """Store recommendation in database.
    
    Args:
        recommendation: Recommendation dictionary
    """
    recommendation_id = recommendation["recommendation_id"]
    user_id = recommendation["user_id"]
    rec_type = recommendation["type"]
    content_id = recommendation["content_id"]
    title = recommendation["title"]
    rationale = recommendation["rationale"]
    decision_trace = json.dumps(recommendation["decision_trace"])
    shown_at = datetime.now().isoformat()
    
    # Delete existing recommendation if it exists and insert new one (idempotent)
    delete_query = """
        DELETE FROM recommendations
        WHERE recommendation_id = ?
    """
    insert_query = """
        INSERT INTO recommendations (
            recommendation_id, user_id, type, content_id, title, rationale, decision_trace, shown_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    with db.get_db_connection() as conn:
        conn.execute(delete_query, (recommendation_id,))
        conn.execute(insert_query, (
            recommendation_id, user_id, rec_type, content_id, title, rationale, decision_trace, shown_at
        ))

