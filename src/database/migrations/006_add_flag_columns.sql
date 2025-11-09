-- Migration script to add flag columns to users table
-- Run this script if you have an existing database created before the schema update

-- Add flag columns to users table
ALTER TABLE users ADD COLUMN flagged INTEGER DEFAULT 0;  -- 0 = false, 1 = true
ALTER TABLE users ADD COLUMN flag_reason TEXT;
ALTER TABLE users ADD COLUMN flagged_at TEXT;
ALTER TABLE users ADD COLUMN flagged_by TEXT;  -- operator_id

-- Create index for flagged users queries
CREATE INDEX IF NOT EXISTS idx_users_flagged ON users(flagged);







