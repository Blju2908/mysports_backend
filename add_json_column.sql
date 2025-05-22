-- Add the JSON column to the training_plans table
ALTER TABLE training_plans ADD COLUMN IF NOT EXISTS training_principles_json JSONB; 