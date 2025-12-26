-- Fix Package table columns to match v4 models
ALTER TABLE package ADD COLUMN IF NOT EXISTS source_system TEXT;
ALTER TABLE package ADD COLUMN IF NOT EXISTS target_system TEXT;
ALTER TABLE package ADD COLUMN IF NOT EXISTS business_intent TEXT;

-- Ensure lineage table is solid
-- (Already added in migration 10, but let's be sure about the names if needed)
