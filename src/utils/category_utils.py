"""Category normalization utilities for handling Plaid category format.

This module provides utilities to normalize transaction categories between
string format (legacy) and array format (Plaid-compatible).

Plaid categories are arrays like: ["Food and Drink", "Groceries"]
Legacy categories are strings like: "groceries"
"""

from typing import Union, List, Optional
import json


def normalize_category(category: Union[str, List[str], None]) -> List[str]:
    """Normalize a category to array format.
    
    Handles both legacy string format and new array format.
    
    Args:
        category: Category as string, list, or None
        
    Returns:
        List of category strings (primary category first)
        
    Examples:
        >>> normalize_category("groceries")
        ["groceries"]
        >>> normalize_category(["Food and Drink", "Groceries"])
        ["Food and Drink", "Groceries"]
        >>> normalize_category(None)
        ["Uncategorized"]
    """
    if category is None:
        return ["Uncategorized"]
    
    if isinstance(category, str):
        # Try to parse as JSON first (in case it's stored as JSON string)
        try:
            parsed = json.loads(category)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Return as single-element array
        return [category]
    
    if isinstance(category, list):
        # Ensure all elements are strings
        return [str(c) for c in category if c]
    
    # Fallback
    return ["Uncategorized"]


def get_primary_category(category: Union[str, List[str], None]) -> str:
    """Extract the primary category from a category value.
    
    The primary category is the first element of the array, or the string itself.
    
    Args:
        category: Category as string, list, or None
        
    Returns:
        Primary category string
        
    Examples:
        >>> get_primary_category("groceries")
        "groceries"
        >>> get_primary_category(["Food and Drink", "Groceries"])
        "Food and Drink"
        >>> get_primary_category(None)
        "Uncategorized"
    """
    normalized = normalize_category(category)
    return normalized[0] if normalized else "Uncategorized"


def category_matches(
    category: Union[str, List[str], None], 
    match_value: str,
    case_sensitive: bool = False
) -> bool:
    """Check if a category matches a value.
    
    Checks both the primary category and all subcategories.
    
    Args:
        category: Category as string, list, or None
        match_value: Value to match against
        case_sensitive: Whether to do case-sensitive matching
        
    Returns:
        True if category matches, False otherwise
        
    Examples:
        >>> category_matches(["Food and Drink", "Groceries"], "groceries")
        True
        >>> category_matches("groceries", "Groceries")
        True
        >>> category_matches(["Food and Drink", "Restaurants"], "groceries")
        False
    """
    normalized = normalize_category(category)
    
    if not case_sensitive:
        match_value = match_value.lower()
        normalized = [c.lower() for c in normalized]
    
    return match_value in normalized


def category_contains(
    category: Union[str, List[str], None],
    search_term: str,
    case_sensitive: bool = False
) -> bool:
    """Check if category contains a search term.
    
    Useful for partial matching (e.g., "interest" in category).
    
    Args:
        category: Category as string, list, or None
        search_term: Term to search for
        case_sensitive: Whether to do case-sensitive matching
        
    Returns:
        True if any category contains the search term
        
    Examples:
        >>> category_contains(["Food and Drink", "Groceries"], "food")
        True
        >>> category_contains("interest charge", "interest")
        True
    """
    normalized = normalize_category(category)
    category_str = " ".join(normalized)
    
    if not case_sensitive:
        search_term = search_term.lower()
        category_str = category_str.lower()
    
    return search_term in category_str

