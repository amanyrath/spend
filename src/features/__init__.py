"""Features module for SpendSense.

This module provides signal detection functionality for analyzing
financial behavior patterns.
"""

from src.features.signal_detection import (
    detect_subscriptions,
    detect_credit_utilization,
    detect_savings_behavior,
    detect_income_stability,
    compute_all_features,
    store_feature,
    get_user_features,
)

__all__ = [
    "detect_subscriptions",
    "detect_credit_utilization",
    "detect_savings_behavior",
    "detect_income_stability",
    "compute_all_features",
    "store_feature",
    "get_user_features",
]











