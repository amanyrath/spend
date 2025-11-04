"""Pytest configuration for SpendSense tests.

This file adds the project root to sys.path so that imports like
`from src.features import signal_detection` work correctly.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

