-- Nexus Discovery Platform - PostgreSQL Schema

-- 1. Organizations (Tenant Root)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    tier TEXT DEFAULT 'FREE', -- FREE, PRO, ENTERPRISE
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Solutions (Projects)
CREATE TABLE IF NOT EXISTS solutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    storage_path TEXT NOT NULL, -- Path to the ZIP file in Supabase Storage
    status TEXT DEFAULT 'DRAFT', -- DRAFT, QUEUED, PROCESSING, READY, ERROR
    config JSONB DEFAULT '{}', -- Additional config (e.g., ignore patterns)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Jobs (Execution History)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solution_id UUID NOT NULL REFERENCES solutions(id) ON DELETE CASCADE,
    status TEXT NOT NULL, -- QUEUED, RUNNING, COMPLETED, FAILED
    logs TEXT[], -- Simple array of log strings for debugging
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. API Vault (Secrets)
CREATE TABLE IF NOT EXISTS api_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    service_name TEXT NOT NULL, -- 'OPENROUTER', 'AZURE_OPENAI', 'DATABRICKS'
    encrypted_value TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_solutions_org ON solutions(org_id);
CREATE INDEX IF NOT EXISTS idx_jobs_solution ON jobs(solution_id);
