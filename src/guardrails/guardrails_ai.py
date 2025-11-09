"""Guardrails AI integration for SpendSense.

This module provides guardrails validation using the Guardrails AI framework
with custom validators for financial education tone and prohibited phrases.
"""

import re
from typing import Optional, List

# Make guardrails optional for Vercel deployment
try:
    from guardrails import Guard, OnFailAction
    from guardrails.validators import Validator, register_validator
    HAS_GUARDRAILS = True
except ImportError:
    # Guardrails not available - use fallback implementations
    HAS_GUARDRAILS = False
    Guard = None
    OnFailAction = None
    Validator = None
    
    def register_validator(name=None, data_type=None):
        """Fallback decorator when guardrails not available."""
        def decorator(cls):
            return cls
        return decorator

# Try to import hub validators, but make them optional
try:
    from guardrails.hub import ToxicLanguage, DetectPII
    HAS_HUB_VALIDATORS = True
except ImportError:
    # Guardrails hub validators not available - use custom validators only
    HAS_HUB_VALIDATORS = False
    ToxicLanguage = None
    DetectPII = None


# Prohibited phrases that should not appear in responses
PROHIBITED_PHRASES = [
    "overspending",
    "bad habits",
    "poor choices",
    "irresponsible",
    "wasteful",
    "you're overspending",
    "bad habit",
    "poor choice"
]

# Sensitive patterns that should not appear in merchant names or financial data
MERCHANT_PII_PATTERNS = [
    (r'@', 'email address'),
    (r'\d{3}-\d{3}-\d{4}', 'phone number'),
    (r'\d{3}-\d{2}-\d{4}', 'SSN'),
    (r'\b\d{13,19}\b', 'account number'),
]


@register_validator(name="prohibited_phrases", data_type="string")
class ProhibitedPhrasesValidator(Validator if HAS_GUARDRAILS else object):
    """Custom validator for prohibited phrases in financial education context.
    
    Validates that text does not contain judgmental or shaming language
    specific to financial education.
    """
    
    def __init__(self, prohibited_phrases: Optional[List[str]] = None, on_fail: Optional[any] = None, **kwargs):
        if HAS_GUARDRAILS:
            super().__init__(on_fail=on_fail, **kwargs)
        self.prohibited_phrases = prohibited_phrases or PROHIBITED_PHRASES
    
    def validate(self, value: str, metadata: dict = None) -> str:
        """Validate that text does not contain prohibited phrases.
        
        Args:
            value: Text to validate
            metadata: Optional metadata
            
        Returns:
            Validated text
            
        Raises:
            ValidationError: If prohibited phrase is found
        """
        if not value:
            return value
        
        text_lower = value.lower()
        found_phrases = []
        
        for phrase in self.prohibited_phrases:
            if phrase in text_lower:
                found_phrases.append(phrase)
        
        if found_phrases:
            raise ValueError(
                f"Response contains prohibited phrases: {', '.join(found_phrases)}. "
                "Please use neutral, educational language."
            )
        
        return value


@register_validator(name="merchant_name_validator", data_type="string")
class MerchantNameValidator(Validator if HAS_GUARDRAILS else object):
    """Custom validator for merchant names to detect PII patterns.
    
    Validates that merchant names do not contain personally identifiable
    information patterns like email addresses, phone numbers, or account numbers.
    """
    
    def __init__(self, patterns: Optional[List[tuple]] = None, on_fail: Optional[any] = None, **kwargs):
        if HAS_GUARDRAILS:
            super().__init__(on_fail=on_fail, **kwargs)
        self.patterns = patterns or MERCHANT_PII_PATTERNS
    
    def validate(self, value: str, metadata: dict = None) -> str:
        """Validate that merchant name does not contain PII patterns.
        
        Args:
            value: Merchant name to validate
            metadata: Optional metadata
            
        Returns:
            Validated merchant name
            
        Raises:
            ValidationError: If PII pattern is found
        """
        if not value:
            return value
        
        found_patterns = []
        
        for pattern, description in self.patterns:
            if re.search(pattern, value):
                found_patterns.append(description)
        
        if found_patterns:
            raise ValueError(
                f"Merchant name contains sensitive patterns: {', '.join(found_patterns)}. "
                "This data should be sanitized before use."
            )
        
        return value


class ChatGuardrails:
    """Guardrails manager for chat responses.
    
    Combines multiple validators to ensure chat responses meet quality
    and safety standards for financial education.
    """
    
    def __init__(self):
        """Initialize guardrails with validators."""
        if not HAS_GUARDRAILS:
            # Fallback: use simple validation without guardrails library
            self.guard = None
            self.validators = [
                ProhibitedPhrasesValidator(prohibited_phrases=PROHIBITED_PHRASES),
                MerchantNameValidator(patterns=MERCHANT_PII_PATTERNS)
            ]
            return
            
        validators = []
        
        # Add toxic language detection if available
        if HAS_HUB_VALIDATORS and ToxicLanguage:
            validators.append(
                ToxicLanguage(
                    threshold=0.5,
                    validation_method="sentence",
                    on_fail=OnFailAction.EXCEPTION
                )
            )
        
        # Always add custom prohibited phrases validator
        validators.append(
            ProhibitedPhrasesValidator(
                prohibited_phrases=PROHIBITED_PHRASES,
                on_fail=OnFailAction.EXCEPTION
            )
        )
        
        # Add merchant name validator
        validators.append(
            MerchantNameValidator(
                patterns=MERCHANT_PII_PATTERNS,
                on_fail=OnFailAction.EXCEPTION
            )
        )
        
        # Create guard with validators
        if validators:
            self.guard = Guard().use_many(*validators)
        else:
            # Fallback: use just the custom validator
            self.guard = Guard().use(ProhibitedPhrasesValidator(
                prohibited_phrases=PROHIBITED_PHRASES,
                on_fail=OnFailAction.EXCEPTION
            ))
        self.validators = None
    
    def validate(self, text: str) -> tuple[bool, Optional[str], List[str]]:
        """Validate text against guardrails.
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (is_valid, validated_text, errors)
            - is_valid: True if validation passes
            - validated_text: Validated text (same as input if valid)
            - errors: List of error messages if validation fails
        """
        if not text:
            return True, text, []
        
        # Use fallback validation if guardrails not available
        if not HAS_GUARDRAILS or self.guard is None:
            errors = []
            for validator in self.validators:
                try:
                    validator.validate(text)
                except Exception as e:
                    errors.append(str(e))
            
            if errors:
                return False, text, errors
            return True, text, []
        
        # Use full guardrails validation
        try:
            validated_text, *rest = self.guard.validate(text)
            return True, validated_text, []
        except Exception as e:
            error_msg = str(e)
            # Extract specific errors from Guardrails exception
            errors = [error_msg]
            return False, text, errors
    
    def validate_merchant_names(self, merchant_names: List[str]) -> tuple[bool, List[str]]:
        """Validate a list of merchant names for PII patterns.
        
        Args:
            merchant_names: List of merchant names to validate
            
        Returns:
            Tuple of (all_valid, invalid_merchants)
            - all_valid: True if all merchant names are valid
            - invalid_merchants: List of invalid merchant names
        """
        validator = MerchantNameValidator(patterns=MERCHANT_PII_PATTERNS)
        invalid_merchants = []
        
        for merchant_name in merchant_names:
            try:
                validator.validate(merchant_name)
            except (ValueError, Exception):
                invalid_merchants.append(merchant_name)
        
        return len(invalid_merchants) == 0, invalid_merchants
    
    def check_prohibited_phrases(self, text: str) -> List[str]:
        """Check which prohibited phrases are present in text.
        
        Args:
            text: Text to check
            
        Returns:
            List of prohibited phrases found
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found_phrases = []
        
        for phrase in PROHIBITED_PHRASES:
            if phrase in text_lower:
                found_phrases.append(phrase)
        
        return found_phrases


# Global instance for convenience
_guardrails_instance: Optional[ChatGuardrails] = None


def get_guardrails() -> ChatGuardrails:
    """Get or create guardrails instance.
    
    Returns:
        ChatGuardrails instance
    """
    global _guardrails_instance
    if _guardrails_instance is None:
        _guardrails_instance = ChatGuardrails()
    return _guardrails_instance


# Backward compatibility functions
def validate_tone(text: str) -> bool:
    """Validate that text does not contain prohibited phrases.
    
    DEPRECATED: Use ChatGuardrails.validate() instead.
    This function is kept for backward compatibility.
    
    Args:
        text: Text to validate
        
    Returns:
        True if text passes validation (no prohibited phrases found),
        False if prohibited phrase detected
    """
    is_valid, _, _ = get_guardrails().validate(text)
    return is_valid


def check_prohibited_phrases(text: str) -> List[str]:
    """Find all prohibited phrases in text.
    
    DEPRECATED: Use ChatGuardrails.check_prohibited_phrases() instead.
    This function is kept for backward compatibility.
    
    Args:
        text: Text to check
        
    Returns:
        List of prohibited phrases found (empty if none found)
    """
    return get_guardrails().check_prohibited_phrases(text)

