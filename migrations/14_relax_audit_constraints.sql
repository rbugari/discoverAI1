-- Migration 14: Relax audit constraints to support all LLM strategies and actions
-- These constraints were too restrictive for the evolution of the system.

ALTER TABLE file_processing_log DROP CONSTRAINT IF EXISTS chk_strategy;
ALTER TABLE file_processing_log DROP CONSTRAINT IF EXISTS chk_action_name;
ALTER TABLE file_processing_log DROP CONSTRAINT IF EXISTS chk_status;

-- Note: We remove these to allow 'LLM_ONLY', 'PARSER_PLUS_LLM', and 
-- granular actions like 'extract.deep_dive' without failing the audit insert.
