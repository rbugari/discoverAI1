-- Legacy cleanup migration
-- Remove tables that are no longer used or have been replaced

DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS api_vault;
