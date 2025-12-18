-- Corrección: Permitir estado 'pending' y 'processing' en auditoría
-- Objetivo: Ajustar constraint para permitir estados intermedios

ALTER TABLE file_processing_log DROP CONSTRAINT IF EXISTS chk_status;

ALTER TABLE file_processing_log 
ADD CONSTRAINT chk_status CHECK (status IN ('pending', 'processing', 'success', 'failed', 'fallback_exhausted'));
