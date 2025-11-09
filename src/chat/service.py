"""Chat service for handling AI chat interactions."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from openai import OpenAI

from src.chat.prompts import SYSTEM_PROMPT, build_user_context
from src.guardrails.guardrails_ai import get_guardrails
from src.guardrails.data_sanitizer import get_sanitizer
from src.utils.logging import get_logger

# Initialize logger
logger = get_logger("chat")

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

# Chat agent configuration from environment
CHAT_MAX_CONTEXT_TOKENS = int(os.getenv('CHAT_MAX_CONTEXT_TOKENS', '2000'))
CHAT_MAX_TRANSACTIONS = int(os.getenv('CHAT_MAX_TRANSACTIONS', '100'))


def generate_chat_response(
    message: str,
    user_features: dict,
    recent_transactions: list,
    persona: Optional[dict] = None,
    max_retries: int = 2,
    transaction_window_days: int = 30,
    user_accounts: Optional[list] = None
) -> Dict[str, Any]:
    """Generate chat response using OpenAI API with guardrails.
    
    Args:
        message: User's message/question
        user_features: User's computed features from get_user_features()
        recent_transactions: List of recent transactions
        persona: User's persona assignment (optional)
        max_retries: Maximum number of retries if validation fails
        transaction_window_days: Number of days in transaction window
        user_accounts: List of user account dictionaries (optional)
        
    Returns:
        Dictionary with 'response' and 'citations' keys
        
    Raises:
        ValueError: If OpenAI API key is not configured
        RuntimeError: If response fails validation after retries
    """
    if not client:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Initialize sanitizer
    sanitizer = get_sanitizer()
    
    # Sanitize user message
    sanitized_message, detected_pii = sanitizer.sanitize_user_message(message)
    
    if detected_pii:
        # Log PII detection (in production, this should go to security logs)
        logger.warning(
            f"PII detected in user message",
            extra={"detected_pii": detected_pii}
        )
    
    # Sample transactions if count exceeds maximum
    if len(recent_transactions) > CHAT_MAX_TRANSACTIONS:
        logger.info(
            f"Sampling transactions from {len(recent_transactions)} to {CHAT_MAX_TRANSACTIONS}"
        )
        recent_transactions = sanitizer.sample_transactions_representative(
            recent_transactions,
            max_count=CHAT_MAX_TRANSACTIONS
        )
    
    # Sanitize financial context
    sanitized_context = sanitizer.sanitize_financial_context(
        user_features,
        recent_transactions,
        persona
    )
    
    # Estimate token usage
    estimated_tokens = sanitizer.estimate_context_tokens(
        sanitized_context['user_features'],
        sanitized_context['recent_transactions']
    )
    
    logger.info(f"Estimated context tokens: {estimated_tokens}")
    
    # If estimated tokens exceed limit, reduce transaction context
    if estimated_tokens > CHAT_MAX_CONTEXT_TOKENS:
        logger.warning(
            f"Context tokens ({estimated_tokens}) exceed limit ({CHAT_MAX_CONTEXT_TOKENS}). "
            "Reducing transaction context."
        )
        sanitized_context['recent_transactions'] = sanitizer.reduce_transaction_context(
            sanitized_context['recent_transactions'],
            target_tokens=CHAT_MAX_CONTEXT_TOKENS
        )
        
        # Re-estimate after reduction
        new_token_estimate = sanitizer.estimate_context_tokens(
            sanitized_context['user_features'],
            sanitized_context['recent_transactions']
        )
        logger.info(f"Reduced context tokens to: {new_token_estimate}")
    
    # Validate merchant names in transactions
    guardrails = get_guardrails()
    merchant_names = [
        txn.get('merchant_name', '') 
        for txn in sanitized_context['recent_transactions']
        if txn.get('merchant_name')
    ]
    
    if merchant_names:
        all_valid, invalid_merchants = guardrails.validate_merchant_names(merchant_names)
        if not all_valid:
            logger.warning(
                f"Found {len(invalid_merchants)} merchants with potential PII patterns",
                extra={"invalid_count": len(invalid_merchants)}
            )
    
    # Build user context with sanitized data and accounts
    user_context = build_user_context(
        sanitized_context['user_features'],
        sanitized_context['recent_transactions'],
        sanitized_context['persona'],
        user_accounts=user_accounts or [],
        transaction_window_days=transaction_window_days
    )
    
    # Build messages for OpenAI
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""User's Financial Context:
{user_context}

User Question: {sanitized_message}

Please provide an educational response that cites specific data points from the user's financial information above."""
        }
    ]
    
    # Generate response with retries if validation fails
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Validate with Guardrails AI
            is_valid, validated_text, errors = guardrails.validate(response_text)
            
            if not is_valid:
                prohibited = guardrails.check_prohibited_phrases(response_text)
                if attempt < max_retries:
                    # Retry with stricter prompt
                    messages.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    messages.append({
                        "role": "user",
                        "content": f"Please revise your response. Avoid these phrases: {', '.join(prohibited)}. Use more neutral, educational language."
                    })
                    continue
                else:
                    # Filter out prohibited phrases as fallback
                    for phrase in prohibited:
                        response_text = response_text.replace(phrase, "")
                    # Log warning but proceed
            
            # Use validated text if available
            response_text = validated_text if validated_text else response_text
            
            # Ensure disclaimer is present
            disclaimer = "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
            if disclaimer.lower() not in response_text.lower():
                response_text += f"\n\n{disclaimer}"
            
            # Extract citations (simple pattern matching for now)
            citations = extract_citations(response_text, user_features, recent_transactions)
            
            return {
                "response": response_text,
                "citations": citations
            }
            
        except Exception as e:
            if attempt < max_retries:
                continue
            raise RuntimeError(f"Failed to generate chat response: {str(e)}")
    
    raise RuntimeError("Failed to generate valid response after retries")


def extract_citations(response_text: str, user_features: dict, recent_transactions: list) -> List[Dict[str, str]]:
    """Extract data citations from response text.
    
    Args:
        response_text: Generated response text
        user_features: User's computed features
        recent_transactions: List of recent transactions
        
    Returns:
        List of citation dictionaries with 'data_point' and 'value' keys
    """
    citations = []
    
    # Extract credit utilization citations
    if user_features.get('credit_utilization'):
        cu = user_features['credit_utilization']
        for acc in cu.get('accounts', []):
            account_mask = acc.get('account_mask', '')
            utilization = acc.get('utilization', 0)
            if account_mask and utilization > 0:
                utilization_pct = round(utilization * 100, 1)
                if account_mask in response_text or str(utilization_pct) in response_text:
                    citations.append({
                        "data_point": f"Account ending in {account_mask[-4:]}" if len(account_mask) >= 4 else account_mask,
                        "value": f"{utilization_pct}% utilization"
                    })
    
    # Extract subscription citations
    if user_features.get('subscriptions'):
        subs = user_features['subscriptions']
        monthly_total = subs.get('monthly_recurring', 0)
        if monthly_total > 0 and str(monthly_total) in response_text:
            citations.append({
                "data_point": "Recurring subscriptions",
                "value": f"${monthly_total:.2f}/month"
            })
    
    # Extract savings rate citations
    if user_features.get('savings_behavior'):
        sb = user_features['savings_behavior']
        avg_income = sb.get('avg_monthly_income', 0)
        avg_expenses = sb.get('avg_monthly_expenses', 0)
        if avg_income > 0:
            savings_rate = ((avg_income - avg_expenses) / avg_income) * 100
            if str(round(savings_rate, 1)) in response_text:
                citations.append({
                    "data_point": "Savings rate",
                    "value": f"{savings_rate:.1f}%"
                })
    
    return citations

