-- Migration: Create module_interactions table for tracking user engagement with education modules
-- This table tracks all user interactions with the interactive education modules
-- including inputs, outputs, and completion status for operator oversight

CREATE TABLE IF NOT EXISTS module_interactions (
    interaction_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL,
    module_type TEXT NOT NULL CHECK (module_type IN (
        'balance_transfer',
        'subscription',
        'savings_goal',
        'budget_breakdown'
    )),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    inputs TEXT, -- JSON string of user inputs
    outputs TEXT, -- JSON string of calculation results
    completed BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_module_interactions_user ON module_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_module_interactions_type ON module_interactions(module_type);
CREATE INDEX IF NOT EXISTS idx_module_interactions_timestamp ON module_interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_module_interactions_completed ON module_interactions(completed);

-- Migration complete







