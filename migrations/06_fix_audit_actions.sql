-- Corrección: Permitir nuevas acciones en auditoría
-- Objetivo: Ampliar constraint chk_action_name para incluir extract_sql, extract_python, etc.

ALTER TABLE file_processing_log DROP CONSTRAINT IF EXISTS chk_action_name;

ALTER TABLE file_processing_log 
ADD CONSTRAINT chk_action_name CHECK (action_name IN (
    'triage_fast', 
    'extract_strict', 
    'extract_loose', 
    'extract_sql', 
    'extract_python', 
    'summarize'
));
