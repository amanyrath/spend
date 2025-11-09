"""Tests for database functions: operator actions and consent tracking."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.database import db
from src.database.db import (
    store_operator_action,
    get_operator_actions,
    get_consent_status,
    store_consent,
    revoke_consent,
    get_db_connection
)


class TestOperatorActions:
    """Tests for operator actions functionality."""
    
    @patch('src.database.db.get_db_connection')
    def test_store_operator_action(self, mock_conn):
        """Test storing operator action."""
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.return_value.__enter__.return_value.execute.return_value = mock_cursor
        
        action_id = store_operator_action(
            operator_id="op_123",
            user_id="user_456",
            action_type="override",
            reason="Test reason",
            recommendation_id="rec_789"
        )
        
        assert action_id == 1
        mock_conn.return_value.__enter__.return_value.execute.assert_called_once()
    
    @patch('src.database.db.fetch_all')
    def test_get_operator_actions(self, mock_fetch_all):
        """Test getting operator actions."""
        # Create a mock row that behaves like sqlite3.Row
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "id": 1,
            "operator_id": "op_123",
            "user_id": "user_456",
            "action_type": "override",
            "recommendation_id": "rec_789",
            "reason": "Test reason",
            "created_at": "2024-01-01T00:00:00"
        }.get(key)
        mock_row.keys = lambda: ["id", "operator_id", "user_id", "action_type", "recommendation_id", "reason", "created_at"]
        mock_row.__iter__ = lambda self: iter(["id", "operator_id", "user_id", "action_type", "recommendation_id", "reason", "created_at"])
        
        mock_fetch_all.return_value = [mock_row]
        
        actions = get_operator_actions(user_id="user_456")
        
        assert len(actions) == 1
        assert actions[0]["action_type"] == "override"
        mock_fetch_all.assert_called_once()
    
    @patch('src.database.db.fetch_all')
    def test_get_operator_actions_filtered(self, mock_fetch_all):
        """Test getting operator actions with filters."""
        mock_rows = []
        mock_fetch_all.return_value = mock_rows
        
        actions = get_operator_actions(
            user_id="user_456",
            action_type="flag",
            limit=10,
            offset=0
        )
        
        assert isinstance(actions, list)
        mock_fetch_all.assert_called_once()


class TestConsentTracking:
    """Tests for consent tracking functionality."""
    
    @patch('src.database.db.fetch_one')
    def test_get_consent_status_granted(self, mock_fetch_one):
        """Test getting consent status when granted."""
        # Create a mock row that behaves like sqlite3.Row
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "consent_status": 1,
            "consent_timestamp": "2024-01-01T00:00:00",
            "consent_version": "1.0"
        }.get(key)
        mock_fetch_one.return_value = mock_row
        
        status = get_consent_status("user_123")
        
        assert status is not None
        assert status["consent_status"] == True
        assert status["consent_version"] == "1.0"
    
    @patch('src.database.db.fetch_one')
    def test_get_consent_status_not_granted(self, mock_fetch_one):
        """Test getting consent status when not granted."""
        # Create a mock row that behaves like sqlite3.Row
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "consent_status": 0,
            "consent_timestamp": None,
            "consent_version": "1.0"
        }.get(key)
        mock_fetch_one.return_value = mock_row
        
        status = get_consent_status("user_123")
        
        assert status is not None
        assert status["consent_status"] == False
    
    @patch('src.database.db.fetch_one')
    def test_get_consent_status_user_not_found(self, mock_fetch_one):
        """Test getting consent status for non-existent user."""
        mock_fetch_one.return_value = None
        
        status = get_consent_status("user_999")
        
        assert status is None
    
    @patch('src.database.db.get_db_connection')
    def test_store_consent_granted(self, mock_conn):
        """Test storing granted consent."""
        store_consent("user_123", granted=True, version="1.0")
        
        mock_conn.return_value.__enter__.return_value.execute.assert_called_once()
    
    @patch('src.database.db.get_db_connection')
    def test_store_consent_revoked(self, mock_conn):
        """Test storing revoked consent."""
        store_consent("user_123", granted=False)
        
        mock_conn.return_value.__enter__.return_value.execute.assert_called_once()
    
    @patch('src.database.db.get_db_connection')
    def test_revoke_consent(self, mock_conn):
        """Test revoking consent."""
        revoke_consent("user_123")
        
        mock_conn.return_value.__enter__.return_value.execute.assert_called_once()

