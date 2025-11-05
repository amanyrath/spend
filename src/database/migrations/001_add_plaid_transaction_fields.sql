-- Migration script to add Plaid-compatible fields to transactions table
-- Run this script if you have an existing database created before the schema update

-- Add location fields
ALTER TABLE transactions ADD COLUMN location_address TEXT;
ALTER TABLE transactions ADD COLUMN location_city TEXT;
ALTER TABLE transactions ADD COLUMN location_region TEXT;
ALTER TABLE transactions ADD COLUMN location_postal_code TEXT;
ALTER TABLE transactions ADD COLUMN location_country TEXT;
ALTER TABLE transactions ADD COLUMN location_lat REAL;
ALTER TABLE transactions ADD COLUMN location_lon REAL;

-- Add Plaid fields
ALTER TABLE transactions ADD COLUMN iso_currency_code TEXT DEFAULT 'USD';
ALTER TABLE transactions ADD COLUMN payment_channel TEXT;
ALTER TABLE transactions ADD COLUMN authorized_date TEXT;

-- Update existing rows to have default USD currency
UPDATE transactions SET iso_currency_code = 'USD' WHERE iso_currency_code IS NULL;

