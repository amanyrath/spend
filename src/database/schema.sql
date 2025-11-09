-- SpendSense Database Schema
-- SQLite database for storing users, accounts, transactions, features, personas, and recommendations

-- Users
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    created_at TEXT,
    -- Consent tracking
    consent_status INTEGER DEFAULT 0,  -- 0 = not granted, 1 = granted
    consent_timestamp TEXT,
    consent_version TEXT DEFAULT '1.0',
    -- User flagging
    flagged INTEGER DEFAULT 0,  -- 0 = false, 1 = true
    flag_reason TEXT,
    flagged_at TEXT,
    flagged_by TEXT  -- operator_id
);

-- Accounts
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    user_id TEXT,
    type TEXT,
    subtype TEXT,
    balance REAL,
    "limit" REAL,
    mask TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Liabilities (credit card and loan details)
CREATE TABLE IF NOT EXISTS liabilities (
    account_id TEXT PRIMARY KEY,
    account_type TEXT,
    account_subtype TEXT,
    -- Credit card fields
    aprs TEXT,  -- JSON array of APR objects
    minimum_payment_amount REAL,
    last_payment_amount REAL,
    is_overdue INTEGER,  -- 0 = false, 1 = true
    last_statement_balance REAL,
    -- Loan fields
    origination_date TEXT,
    original_principal_balance REAL,
    interest_rate REAL,
    next_payment_due_date TEXT,
    principal_balance REAL,
    escrow_balance REAL,
    property_address TEXT,
    guarantor TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT,
    user_id TEXT,
    date TEXT,
    amount REAL,
    merchant_name TEXT,
    category TEXT,  -- JSON array: ["Food and Drink", "Groceries"] or legacy string
    pending INTEGER,
    -- Location fields (Plaid-compatible)
    location_address TEXT,
    location_city TEXT,
    location_region TEXT,
    location_postal_code TEXT,
    location_country TEXT,
    location_lat REAL,
    location_lon REAL,
    -- Additional Plaid fields
    iso_currency_code TEXT DEFAULT 'USD',
    payment_channel TEXT,  -- 'online', 'in store', 'other'
    authorized_date TEXT,
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
    -- Match percentage scores for each persona
    match_high_utilization REAL DEFAULT 0.0,
    match_variable_income REAL DEFAULT 0.0,
    match_subscription_heavy REAL DEFAULT 0.0,
    match_savings_builder REAL DEFAULT 0.0,
    match_general_wellness REAL DEFAULT 0.0,
    -- Primary persona (highest scoring persona)
    primary_persona TEXT,
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
    -- Override tracking
    overridden INTEGER DEFAULT 0,  -- 0 = false, 1 = true
    override_reason TEXT,
    overridden_at TEXT,
    overridden_by TEXT,  -- operator_id
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Chat Logs
CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    message TEXT,
    response TEXT,
    citations TEXT,  -- JSON
    guardrails_passed INTEGER,  -- 0 or 1
    created_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Operator Actions (audit trail for operator actions)
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

-- Module Interactions (tracking user engagement with education modules)
CREATE TABLE IF NOT EXISTS module_interactions (
    interaction_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    module_type TEXT NOT NULL CHECK (module_type IN (
        'balance_transfer',
        'subscription',
        'savings_goal',
        'budget_breakdown'
    )),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    inputs TEXT,  -- JSON string of user inputs
    outputs TEXT,  -- JSON string of calculation results
    completed INTEGER DEFAULT 0,  -- 0 = false, 1 = true
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_liabilities_account_id ON liabilities(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_computed_features_user_id ON computed_features(user_id);
CREATE INDEX IF NOT EXISTS idx_computed_features_time_window ON computed_features(time_window);
CREATE INDEX IF NOT EXISTS idx_persona_assignments_user_id ON persona_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_logs_user_id ON chat_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_logs_created_at ON chat_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_operator_actions_user_id ON operator_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_operator_actions_created_at ON operator_actions(created_at);
CREATE INDEX IF NOT EXISTS idx_operator_actions_action_type ON operator_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_users_consent_status ON users(consent_status);
CREATE INDEX IF NOT EXISTS idx_users_flagged ON users(flagged);
CREATE INDEX IF NOT EXISTS idx_recommendations_overridden ON recommendations(overridden);
CREATE INDEX IF NOT EXISTS idx_recommendations_overridden_at ON recommendations(overridden_at);
CREATE INDEX IF NOT EXISTS idx_module_interactions_user ON module_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_module_interactions_type ON module_interactions(module_type);
CREATE INDEX IF NOT EXISTS idx_module_interactions_timestamp ON module_interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_module_interactions_completed ON module_interactions(completed);

