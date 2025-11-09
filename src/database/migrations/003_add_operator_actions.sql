-- Migration script to add operator_actions table for audit trail
-- Run this script if you have an existing database created before the schema update

-- Create operator_actions table
CREATE TABLE IF NOT EXISTS operator_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    action_type TEXT NOT NULL,  -- 'override' or 'flag'
    recommendation_id TEXT,  -- NULL for flag actions
    reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_operator_actions_user_id ON operator_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_operator_actions_created_at ON operator_actions(created_at);
CREATE INDEX IF NOT EXISTS idx_operator_actions_action_type ON operator_actions(action_type);







