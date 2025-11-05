"""Plaid category taxonomy mapping.

Plaid uses a hierarchical category system with primary and detailed categories.
Categories are arrays like: ["Food and Drink", "Groceries"]

Based on Plaid's documentation, common primary categories include:
- Food and Drink
- General Merchandise  
- Transportation
- Travel
- Service
- General Services
- Government and Non-Profit
- Entertainment
- Gas Stations
- Groceries
- Healthcare
- Shops
- etc.

This module provides mappings from our legacy categories to Plaid categories.
"""

from typing import List, Tuple
import random

# Mapping from legacy category strings to Plaid category arrays
LEGACY_TO_PLAID_CATEGORIES = {
    "groceries": ["Food and Drink", "Groceries"],
    "restaurants": ["Food and Drink", "Restaurants"],
    "bills": ["General Services", "Utilities"],
    "shopping": ["General Merchandise", "Department Stores"],
    "entertainment": ["Entertainment", "Streaming Services"],
    "gas": ["Gas Stations", "Gas Stations"],
    "subscriptions": ["Entertainment", "Streaming Services"],
    "transfer": ["Transfer", "Transfer"],
    "rent": ["Rent And Utilities", "Rent"],
    "mortgage": ["Rent And Utilities", "Mortgage"],
    "auto_loan": ["Loan Payments", "Auto Loan Payment"],
    "student_loan": ["Loan Payments", "Student Loan Payment"],
    "healthcare": ["Healthcare", "Doctors"],
    "insurance": ["Insurance", "Health Insurance"],
    "education": ["Education", "Tuition"],
}

# Plaid category hierarchy for random selection
PLAID_PRIMARY_CATEGORIES = [
    "Food and Drink",
    "General Merchandise",
    "Transportation",
    "Travel",
    "Service",
    "General Services",
    "Government and Non-Profit",
    "Entertainment",
    "Gas Stations",
    "Groceries",
    "Healthcare",
    "Shops",
    "Rent And Utilities",
    "Loan Payments",
    "Insurance",
    "Education",
    "Transfer",
]

# Detailed categories for each primary category
PLAID_DETAILED_CATEGORIES = {
    "Food and Drink": [
        "Restaurants",
        "Groceries",
        "Fast Food",
        "Coffee Shops",
        "Bars",
    ],
    "General Merchandise": [
        "Department Stores",
        "Discount Stores",
        "Online",
        "Books",
        "Electronics",
    ],
    "Transportation": [
        "Public Transit",
        "Parking",
        "Tolls",
        "Rideshare",
    ],
    "Entertainment": [
        "Streaming Services",
        "Movies",
        "Music",
        "Sports",
        "Games",
    ],
    "Gas Stations": [
        "Gas Stations",
    ],
    "General Services": [
        "Utilities",
        "Internet",
        "Phone",
        "Cable",
    ],
    "Rent And Utilities": [
        "Rent",
        "Mortgage",
        "Utilities",
    ],
    "Loan Payments": [
        "Auto Loan Payment",
        "Student Loan Payment",
        "Personal Loan Payment",
        "Credit Card Payment",
    ],
    "Healthcare": [
        "Doctors",
        "Pharmacies",
        "Hospitals",
        "Dentists",
    ],
    "Insurance": [
        "Health Insurance",
        "Auto Insurance",
        "Home Insurance",
    ],
    "Education": [
        "Tuition",
        "Books",
        "Supplies",
    ],
    "Transfer": [
        "Transfer",
        "Deposit",
        "Withdrawal",
    ],
}


def get_plaid_category(legacy_category: str) -> List[str]:
    """Convert legacy category to Plaid category array.
    
    Args:
        legacy_category: Legacy category string (e.g., "groceries")
        
    Returns:
        Plaid category array (e.g., ["Food and Drink", "Groceries"])
    """
    return LEGACY_TO_PLAID_CATEGORIES.get(
        legacy_category.lower(),
        ["General Merchandise", "Other"]
    )


def get_random_plaid_category(primary_category: str = None) -> List[str]:
    """Get a random Plaid category array.
    
    Args:
        primary_category: Optional primary category to use
        
    Returns:
        Plaid category array
    """
    if primary_category and primary_category in PLAID_DETAILED_CATEGORIES:
        detailed = random.choice(PLAID_DETAILED_CATEGORIES[primary_category])
        return [primary_category, detailed]
    
    # Random selection
    primary = random.choice(PLAID_PRIMARY_CATEGORIES)
    if primary in PLAID_DETAILED_CATEGORIES:
        detailed = random.choice(PLAID_DETAILED_CATEGORIES[primary])
        return [primary, detailed]
    
    return [primary, "Other"]


def get_category_for_merchant(merchant_name: str, category_hint: str = None) -> List[str]:
    """Get appropriate Plaid category for a merchant.
    
    Args:
        merchant_name: Name of the merchant
        category_hint: Optional hint about the category
        
    Returns:
        Plaid category array
    """
    merchant_lower = merchant_name.lower()
    
    # Grocery stores
    if any(term in merchant_lower for term in ['whole foods', 'kroger', 'safeway', 'trader joe', 'walmart', 'target']):
        if 'walmart' in merchant_lower or 'target' in merchant_lower:
            return ["General Merchandise", "Department Stores"]
        return ["Food and Drink", "Groceries"]
    
    # Restaurants
    if any(term in merchant_lower for term in ['starbucks', 'mcdonald', 'chipotle', 'olive garden', 'pizza']):
        return ["Food and Drink", "Restaurants"]
    
    # Gas stations
    if any(term in merchant_lower for term in ['shell', 'exxon', 'chevron', 'bp', 'gas']):
        return ["Gas Stations", "Gas Stations"]
    
    # Streaming services
    if any(term in merchant_lower for term in ['netflix', 'spotify', 'disney', 'hulu', 'youtube premium']):
        return ["Entertainment", "Streaming Services"]
    
    # Utilities
    if any(term in merchant_lower for term in ['electric', 'water', 'utility', 'internet', 'phone company']):
        return ["General Services", "Utilities"]
    
    # Shopping
    if any(term in merchant_lower for term in ['amazon', 'best buy', 'macy', 'home depot']):
        return ["General Merchandise", "Department Stores"]
    
    # Use category hint if provided
    if category_hint:
        return get_plaid_category(category_hint)
    
    # Default
    return ["General Merchandise", "Other"]

