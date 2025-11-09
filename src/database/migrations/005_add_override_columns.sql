-- Migration script to add override columns to recommendations table
-- Run this script if you have an existing database created before the schema update

-- Add override columns
ALTER TABLE recommendations ADD COLUMN overridden INTEGER DEFAULT 0;  -- 0 = false, 1 = true
ALTER TABLE recommendations ADD COLUMN override_reason TEXT;
ALTER TABLE recommendations ADD COLUMN overridden_at TEXT;
ALTER TABLE recommendations ADD COLUMN overridden_by TEXT;  -- operator_id

-- Create indexes for override queries
CREATE INDEX IF NOT EXISTS idx_recommendations_overridden ON recommendations(overridden);
CREATE INDEX IF NOT EXISTS idx_recommendations_overridden_at ON recommendations(overridden_at);







