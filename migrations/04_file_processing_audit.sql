-- Migración: Sistema de Auditoría de Procesamiento de Archivos
-- Objetivo: Registrar qué pasó con cada archivo (modelo usado, tokens, errores, etc.)

-- 1. Tabla principal de auditoría por archivo
CREATE TABLE IF NOT EXISTS file_processing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES job_run(job_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    file_hash TEXT,
    
    -- Acción ejecutada
    action_name TEXT NOT NULL, -- triage_fast, extract_strict, summarize
    strategy_used TEXT, -- native_parser, structural, llm_heavy
    
    -- Modelo usado
    model_provider TEXT, -- openrouter, local
    model_used TEXT, -- deepseek/deepseek-chat, qwen/qwen-2.5-instruct
    fallback_used BOOLEAN DEFAULT FALSE,
    fallback_chain TEXT[], -- lista de modelos intentados
    
    -- Resultados
    status TEXT NOT NULL, -- success, failed, fallback_exhausted
    input_tokens INT,
    output_tokens INT,
    total_tokens INT,
    latency_ms BIGINT,
    cost_estimate_usd NUMERIC(10,6),
    
    -- Error tracking
    error_type TEXT, -- validation_error, timeout, rate_limit
    error_message TEXT,
    retry_count INT DEFAULT 0,
    
    -- Resultados del procesamiento
    nodes_extracted INT DEFAULT 0,
    edges_extracted INT DEFAULT 0,
    evidences_extracted INT DEFAULT 0,
    result_hash TEXT, -- hash del resultado para deduplicación
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Índices para performance
CREATE INDEX IF NOT EXISTS idx_file_log_job ON file_processing_log(job_id);
CREATE INDEX IF NOT EXISTS idx_file_log_path ON file_processing_log(file_path);
CREATE INDEX IF NOT EXISTS idx_file_log_status ON file_processing_log(status);
CREATE INDEX IF NOT EXISTS idx_file_log_model ON file_processing_log(model_used);
CREATE INDEX IF NOT EXISTS idx_file_log_action ON file_processing_log(action_name);
CREATE INDEX IF NOT EXISTS idx_file_log_created ON file_processing_log(created_at);

-- 3. Vista resumen para dashboard
CREATE OR REPLACE VIEW file_processing_summary AS
SELECT 
    job_id,
    COUNT(*) as total_files,
    COUNT(*) FILTER (WHERE status = 'success') as successful_files,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_files,
    COUNT(*) FILTER (WHERE fallback_used = true) as fallback_files,
    SUM(total_tokens) as total_tokens_used,
    SUM(cost_estimate_usd) as total_cost,
    AVG(latency_ms) as avg_latency_ms,
    MIN(created_at) as started_at,
    MAX(created_at) as finished_at
FROM file_processing_log
GROUP BY job_id;

-- 4. Vista de estadísticas por modelo
CREATE OR REPLACE VIEW model_usage_stats AS
SELECT 
    model_used,
    COUNT(*) as total_usages,
    COUNT(*) FILTER (WHERE status = 'success') as successful_usages,
    COUNT(*) FILTER (WHERE fallback_used = true) as fallback_usages,
    AVG(total_tokens) as avg_tokens,
    AVG(cost_estimate_usd) as avg_cost,
    AVG(latency_ms) as avg_latency,
    MIN(created_at) as first_used,
    MAX(created_at) as last_used
FROM file_processing_log
WHERE model_used IS NOT NULL
GROUP BY model_used;

-- 5. Vista de errores por tipo
CREATE OR REPLACE VIEW error_analysis AS
SELECT 
    error_type,
    COUNT(*) as error_count,
    COUNT(*) FILTER (WHERE fallback_used = true) as fallback_errors,
    AVG(retry_count) as avg_retries,
    model_used,
    action_name,
    MIN(created_at) as first_seen,
    MAX(created_at) as last_seen
FROM file_processing_log
WHERE status = 'failed' AND error_type IS NOT NULL
GROUP BY error_type, model_used, action_name;

-- 6. Extender job_run con metadata del routing
ALTER TABLE job_run ADD COLUMN IF NOT EXISTS artifact_hash TEXT;
ALTER TABLE job_run ADD COLUMN IF NOT EXISTS prompt_version TEXT;
ALTER TABLE job_run ADD COLUMN IF NOT EXISTS routing_version TEXT;
ALTER TABLE job_run ADD COLUMN IF NOT EXISTS llm_provider TEXT;
ALTER TABLE job_run ADD COLUMN IF NOT EXISTS llm_default_model TEXT;

-- 7. Extender job_stage_run con métricas estandarizadas
ALTER TABLE job_stage_run ADD COLUMN IF NOT EXISTS action_name TEXT;
ALTER TABLE job_stage_run ADD COLUMN IF NOT EXISTS model_used TEXT;
ALTER TABLE job_stage_run ADD COLUMN IF NOT EXISTS fallback_used BOOLEAN DEFAULT FALSE;
ALTER TABLE job_stage_run ADD COLUMN IF NOT EXISTS tokens_in INT;
ALTER TABLE job_stage_run ADD COLUMN IF NOT EXISTS tokens_out INT;
ALTER TABLE job_stage_run ADD COLUMN IF NOT EXISTS total_tokens INT;
ALTER TABLE job_stage_run ADD COLUMN IF NOT EXISTS cost_estimate_usd NUMERIC(10,6);

-- 8. Agregar constraints y validaciones
ALTER TABLE file_processing_log 
ADD CONSTRAINT chk_status CHECK (status IN ('success', 'failed', 'fallback_exhausted'));

ALTER TABLE file_processing_log 
ADD CONSTRAINT chk_action_name CHECK (action_name IN ('triage_fast', 'extract_strict', 'summarize'));

ALTER TABLE file_processing_log 
ADD CONSTRAINT chk_strategy CHECK (strategy_used IN ('native_parser', 'structural', 'llm_heavy'));

-- 9. Función para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_file_processing_updated_at 
    BEFORE UPDATE ON file_processing_log 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();