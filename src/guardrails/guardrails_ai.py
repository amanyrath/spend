"""Guardrails AI integration for SpendSense.

This module provides guardrails validation using the Guardrails AI framework
with custom validators for financial education tone and prohibited phrases.
"""

from typing import Optional, List
from guardrails import Guard, OnFailAction
from guardrails.validators import Validator, register_validator

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


@register_validator(name="prohibited_phrases", data_type="string")
class ProhibitedPhrasesValidator(Validator):
    """Custom validator for prohibited phrases in financial education context.
    
    Validates that text does not contain judgmental or shaming language
    specific to financial education.
    """
    
    def __init__(self, prohibited_phrases: Optional[List[str]] = None, on_fail: Optional[OnFailAction] = None, **kwargs):
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


class ChatGuardrails:
    """Guardrails manager for chat responses.
    
    Combines multiple validators to ensure chat responses meet quality
    and safety standards for financial education.
    """
    
    def __init__(self):
        """Initialize guardrails with validators."""
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
        
        # Create guard with validators
        if validators:
            self.guard = Guard().use_many(*validators)
        else:
            # Fallback: use just the custom validator
            self.guard = Guard().use(ProhibitedPhrasesValidator(
                prohibited_phrases=PROHIBITED_PHRASES,
                on_fail=OnFailAction.EXCEPTION
            ))
    
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
        
        try:
            validated_text, *rest = self.guard.validate(text)
            return True, validated_text, []
        except Exception as e:
            error_msg = str(e)
            # Extract specific errors from Guardrails exception
            errors = [error_msg]
            return False, text, errors
    
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

