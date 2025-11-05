-- Migration script to add persona match percentage columns to persona_assignments table
-- Run this script if you have an existing database created before the schema update

-- Add match percentage columns for each persona
ALTER TABLE persona_assignments ADD COLUMN match_high_utilization REAL DEFAULT 0.0;
ALTER TABLE persona_assignments ADD COLUMN match_variable_income REAL DEFAULT 0.0;
ALTER TABLE persona_assignments ADD COLUMN match_subscription_heavy REAL DEFAULT 0.0;
ALTER TABLE persona_assignments ADD COLUMN match_savings_builder REAL DEFAULT 0.0;
ALTER TABLE persona_assignments ADD COLUMN match_general_wellness REAL DEFAULT 0.0;

-- Add primary_persona column (highest scoring persona)
ALTER TABLE persona_assignments ADD COLUMN primary_persona TEXT;

-- Update existing rows: set primary_persona = persona for backward compatibility
-- Note: Match percentages will remain 0.0 until personas are recalculated
UPDATE persona_assignments SET primary_persona = persona WHERE primary_persona IS NULL;

