"""Data sanitization and PII scrubbing for LLM interactions.

This module provides utilities to sanitize financial data and scrub PII
before sending to LLM services.
"""

import copy
import logging
import re
from typing import Dict, List, Optional, Any, Tuple

from guardrails import Guard, OnFailAction

# Set up logging
logger = logging.getLogger(__name__)

# Try to import hub validators, but make them optional
try:
    from guardrails.hub import DetectPII
    HAS_DETECT_PII = True
except ImportError:
    # Guardrails hub validators not available - use regex patterns only
    HAS_DETECT_PII = False
    DetectPII = None


# Patterns for detecting financial account numbers
ACCOUNT_NUMBER_PATTERN = re.compile(r'\b\d{13,19}\b')  # Credit card numbers (13-19 digits)
ROUTING_NUMBER_PATTERN = re.compile(r'\b\d{9}\b')  # Bank routing numbers
SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b')  # SSN formats
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s?\d{3}-\d{4}\b|\b\d{10}\b')


class DataSanitizer:
    """Sanitizes financial data and user inputs before sending to LLM."""
    
    def __init__(self):
        """Initialize data sanitizer with PII detection."""
        # Initialize Guardrails PII detector
        if HAS_DETECT_PII and DetectPII:
            try:
                self.pii_detector = Guard().use(
                    DetectPII(
                        pii_entities=["phone_number", "email", "ssn", "credit_card"],
                        on_fail=OnFailAction.EXCEPTION
                    )
                )
            except (ImportError, AttributeError, ValueError, TypeError) as e:
                # Fallback if Guardrails Hub validators not installed or misconfigured
                logger.debug(f"Guardrails PII detector initialization failed: {e}")
                self.pii_detector = None
            except Exception as e:
                # Log unexpected errors but don't fail initialization
                logger.warning(f"Unexpected error initializing Guardrails PII detector: {e}")
                self.pii_detector = None
        else:
            # Guardrails hub validators not available
            self.pii_detector = None
    
    def sanitize_user_message(self, message: str) -> Tuple[str, List[str]]:
        """Sanitize user message by removing PII.
        
        Args:
            message: User's message/question
            
        Returns:
            Tuple of (sanitized_message, detected_pii_types)
        """
        # Validate input
        if not message:
            return message, []
        if not isinstance(message, str):
            logger.warning(f"sanitize_user_message received non-string input: {type(message)}")
            message = str(message)
        
        detected_pii = []
        sanitized = message
        
        # Check for PII patterns
        if ACCOUNT_NUMBER_PATTERN.search(sanitized):
            detected_pii.append("account_number")
            sanitized = ACCOUNT_NUMBER_PATTERN.sub("[ACCOUNT_NUMBER]", sanitized)
        
        if ROUTING_NUMBER_PATTERN.search(sanitized):
            detected_pii.append("routing_number")
            sanitized = ROUTING_NUMBER_PATTERN.sub("[ROUTING_NUMBER]", sanitized)
        
        if SSN_PATTERN.search(sanitized):
            detected_pii.append("ssn")
            sanitized = SSN_PATTERN.sub("[SSN]", sanitized)
        
        if EMAIL_PATTERN.search(sanitized):
            detected_pii.append("email")
            sanitized = EMAIL_PATTERN.sub("[EMAIL]", sanitized)
        
        if PHONE_PATTERN.search(sanitized):
            detected_pii.append("phone")
            sanitized = PHONE_PATTERN.sub("[PHONE]", sanitized)
        
        # Use Guardrails PII detector if available
        if self.pii_detector:
            try:
                self.pii_detector.validate(sanitized)
            except Exception as e:
                # If PII detected, sanitize further
                # Extract PII types from error message
                error_msg = str(e).lower()
                if "phone" in error_msg or "phone_number" in error_msg:
                    detected_pii.append("phone")
                if "email" in error_msg:
                    detected_pii.append("email")
                if "ssn" in error_msg or "social_security" in error_msg:
                    detected_pii.append("ssn")
                if "credit_card" in error_msg:
                    detected_pii.append("credit_card")
        
        detected_pii_unique = list(set(detected_pii))
        if detected_pii_unique:
            logger.info(f"Sanitized message detected PII types: {detected_pii_unique}")
        
        return sanitized, detected_pii_unique
    
    def sanitize_financial_context(
        self,
        user_features: Dict[str, Any],
        recent_transactions: List[Dict[str, Any]],
        persona: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Sanitize financial context data before sending to LLM.
        
        Args:
            user_features: User's computed features
            recent_transactions: List of recent transactions
            persona: User's persona assignment (optional)
            
        Returns:
            Sanitized dictionary with same structure
        """
        sanitized_features = {}
        
        # Sanitize credit utilization data
        if user_features.get('credit_utilization'):
            cu = user_features['credit_utilization'].copy()
            if cu.get('accounts'):
                sanitized_accounts = []
                for acc in cu['accounts']:
                    sanitized_acc = acc.copy()
                    # Only keep last 4 digits of account mask
                    account_mask = sanitized_acc.get('account_mask', '')
                    if account_mask and len(account_mask) > 4:
                        sanitized_acc['account_mask'] = account_mask[-4:]
                    sanitized_accounts.append(sanitized_acc)
                cu['accounts'] = sanitized_accounts
            sanitized_features['credit_utilization'] = cu
        
        # Sanitize subscription data - remove merchant names that might be PII
        if user_features.get('subscriptions'):
            subs = user_features['subscriptions'].copy()
            if subs.get('recurring_merchants'):
                sanitized_merchants = []
                for merchant in subs['recurring_merchants']:
                    sanitized_merchant = merchant.copy()
                    # Keep merchant name but ensure no PII
                    merchant_name = sanitized_merchant.get('merchant', '')
                    # Remove any potential email patterns from merchant names
                    if EMAIL_PATTERN.search(merchant_name):
                        sanitized_merchant['merchant'] = EMAIL_PATTERN.sub("[EMAIL]", merchant_name)
                    sanitized_merchants.append(sanitized_merchant)
                subs['recurring_merchants'] = sanitized_merchants
            sanitized_features['subscriptions'] = subs
        
        # Copy other features as-is (they're already aggregated/calculated)
        for key, value in user_features.items():
            if key not in sanitized_features:
                sanitized_features[key] = value
        
        # Sanitize transactions
        sanitized_transactions = []
        for txn in recent_transactions:
            # Use deepcopy to handle nested dictionaries safely
            sanitized_txn = copy.deepcopy(txn)
            
            # Remove potentially sensitive fields
            sensitive_fields = [
                'location_address', 'location_city', 'location_region',
                'location_postal_code', 'location_lat', 'location_lon',
                'authorized_date'
            ]
            for field in sensitive_fields:
                sanitized_txn.pop(field, None)
            
            # Sanitize merchant names (remove email patterns)
            merchant_name = sanitized_txn.get('merchant_name', '')
            if merchant_name and EMAIL_PATTERN.search(merchant_name):
                sanitized_txn['merchant_name'] = EMAIL_PATTERN.sub("[EMAIL]", merchant_name)
            
            sanitized_transactions.append(sanitized_txn)
        
        return {
            'user_features': sanitized_features,
            'recent_transactions': sanitized_transactions,
            'persona': persona  # Persona is already anonymized
        }
    
    def mask_financial_amounts(self, amount: float, precision: int = 2) -> str:
        """Mask financial amounts to prevent exact value exposure.
        
        Args:
            amount: Financial amount
            precision: Number of decimal places (default 2, must be between 0 and 10)
            
        Returns:
            Formatted amount string
            
        Raises:
            ValueError: If precision is out of valid range
        """
        if precision < 0 or precision > 10:
            raise ValueError("Precision must be between 0 and 10")
        # Round to nearest precision (already done in most cases)
        return f"${amount:.{precision}f}"
    
    def redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive data patterns from text.
        
        Args:
            text: Text to redact
            
        Returns:
            Text with sensitive data redacted
        """
        redacted = text
        
        # Redact account numbers
        redacted = ACCOUNT_NUMBER_PATTERN.sub("[ACCOUNT_NUMBER]", redacted)
        
        # Redact routing numbers
        redacted = ROUTING_NUMBER_PATTERN.sub("[ROUTING_NUMBER]", redacted)
        
        # Redact SSNs
        redacted = SSN_PATTERN.sub("[SSN]", redacted)
        
        # Redact emails (keep domain for context)
        redacted = EMAIL_PATTERN.sub("[EMAIL]", redacted)
        
        # Redact phone numbers
        redacted = PHONE_PATTERN.sub("[PHONE]", redacted)
        
        return redacted
    
    def is_guardrails_available(self) -> bool:
        """Check if Guardrails Hub validators are available.
        
        Returns:
            True if Guardrails PII detector is available, False otherwise
        """
        return self.pii_detector is not None


# Global instance
_sanitizer_instance: Optional[DataSanitizer] = None


def get_sanitizer() -> DataSanitizer:
    """Get or create data sanitizer instance.
    
    Returns:
        DataSanitizer instance
    """
    global _sanitizer_instance
    if _sanitizer_instance is None:
        _sanitizer_instance = DataSanitizer()
    return _sanitizer_instance

