-- SpendSense Database Schema
-- SQLite database for storing users, accounts, transactions, features, personas, and recommendations

-- Users
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    created_at TEXT
);

-- Accounts
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    user_id TEXT,
    type TEXT,
    subtype TEXT,
    balance REAL,
    limit REAL,
    mask TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT,
    user_id TEXT,
    date TEXT,
    amount REAL,
    merchant_name TEXT,
    category TEXT,
    pending INTEGER,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Computed Features
CREATE TABLE IF NOT EXISTS computed_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    time_window TEXT,
    signal_type TEXT,
    signal_data TEXT,  -- JSON
    computed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Persona Assignments
CREATE TABLE IF NOT EXISTS persona_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    time_window TEXT,
    persona TEXT,
    criteria_met TEXT,  -- JSON array
    assigned_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Recommendations
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id TEXT PRIMARY KEY,
    user_id TEXT,
    type TEXT,
    content_id TEXT,
    title TEXT,
    rationale TEXT,
    decision_trace TEXT,  -- JSON
    shown_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_computed_features_user_id ON computed_features(user_id);
CREATE INDEX IF NOT EXISTS idx_computed_features_time_window ON computed_features(time_window);
CREATE INDEX IF NOT EXISTS idx_persona_assignments_user_id ON persona_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);

