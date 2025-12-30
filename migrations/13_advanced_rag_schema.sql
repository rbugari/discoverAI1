-- RAG Advanced AI Migration
-- Enable pgvector and create table for code embeddings

-- 1. Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Embeddings table
CREATE TABLE IF NOT EXISTS code_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES solutions(id) ON DELETE CASCADE,
    evidence_id UUID REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    file_path TEXT,
    snippet TEXT,
    embedding vector(1536), -- 1536 for text-embedding-3-small or similar
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_project ON code_embeddings(project_id);
