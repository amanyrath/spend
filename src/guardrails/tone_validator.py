"""Tone guardrails for SpendSense recommendations.

This module validates that recommendation rationales use appropriate,
non-shaming language and avoid prohibited phrases.
"""

# Prohibited phrases that should not appear in rationales
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


def validate_tone(text: str) -> bool:
    """Validate that text does not contain prohibited phrases.
    
    Args:
        text: Text to validate
        
    Returns:
        True if text passes validation (no prohibited phrases found),
        False if prohibited phrase detected
    """
    if not text:
        return True
    
    text_lower = text.lower()
    
    for phrase in PROHIBITED_PHRASES:
        if phrase in text_lower:
            return False
    
    return True


def check_prohibited_phrases(text: str) -> list[str]:
    """Find all prohibited phrases in text.
    
    Args:
        text: Text to check
        
    Returns:
        List of prohibited phrases found (empty if none found)
    """
    if not text:
        return []
    
    text_lower = text.lower()
    found_phrases = []
    
    for phrase in PROHIBITED_PHRASES:
        if phrase in text_lower:
            found_phrases.append(phrase)
    
    return found_phrases

