-- Migration script to add consent tracking to users table
-- Run this script if you have an existing database created before the schema update

-- Add consent columns to users table
ALTER TABLE users ADD COLUMN consent_status INTEGER DEFAULT 0;  -- 0 = not granted, 1 = granted
ALTER TABLE users ADD COLUMN consent_timestamp TEXT;
ALTER TABLE users ADD COLUMN consent_version TEXT DEFAULT '1.0';

-- Create index for consent queries
CREATE INDEX IF NOT EXISTS idx_users_consent_status ON users(consent_status);







