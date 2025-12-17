-- 1. Jobs & Queue System
CREATE TABLE IF NOT EXISTS job_run (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL, -- References solutions(id) ideally, but keeping generic for now
    artifact_id UUID,
    artifact_hash TEXT,
    prompt_version TEXT,
    status TEXT NOT NULL DEFAULT 'queued', -- queued, running, completed, failed, canceled
    progress_pct INT DEFAULT 0,
    current_stage TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    llm_provider TEXT,
    llm_model TEXT,
    error_message TEXT,
    error_details JSONB
);

CREATE TABLE IF NOT EXISTS job_stage_run (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES job_run(job_id) ON DELETE CASCADE,
    stage_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    duration_ms BIGINT,
    metrics JSONB,
    error JSONB
);

-- Simple SQL Queue
CREATE TABLE IF NOT EXISTS job_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES job_run(job_id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending', -- pending, processing, failed, completed
    attempts INT DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    locked_until TIMESTAMPTZ -- For simple locking mechanism
);

-- 2. Evidence & Trust
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    artifact_id UUID,
    file_path TEXT,
    kind TEXT, -- code, xml, log, config, regex_match
    locator JSONB, -- { line_start, line_end, xpath, ... }
    snippet TEXT,
    hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Operational Catalog (Read Model)
CREATE TABLE IF NOT EXISTS asset (
    asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Stable ID
    project_id UUID NOT NULL,
    asset_type TEXT NOT NULL, -- table, view, file, process, etc.
    name_display TEXT NOT NULL,
    canonical_name TEXT,
    system TEXT,
    tags JSONB,
    owner TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS asset_version (
    asset_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES asset(asset_id) ON DELETE CASCADE,
    artifact_id UUID,
    source_file TEXT,
    hash TEXT,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS edge_index (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    from_asset_id UUID NOT NULL REFERENCES asset(asset_id) ON DELETE CASCADE,
    to_asset_id UUID NOT NULL REFERENCES asset(asset_id) ON DELETE CASCADE,
    edge_type TEXT NOT NULL,
    confidence NUMERIC CHECK (confidence >= 0 AND confidence <= 1),
    extractor_id TEXT,
    is_hypothesis BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS edge_evidence (
    edge_id UUID NOT NULL REFERENCES edge_index(edge_id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    PRIMARY KEY (edge_id, evidence_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_run_project ON job_run(project_id);
CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status);
CREATE INDEX IF NOT EXISTS idx_asset_project ON asset(project_id);
CREATE INDEX IF NOT EXISTS idx_edge_index_from ON edge_index(from_asset_id);
CREATE INDEX IF NOT EXISTS idx_edge_index_to ON edge_index(to_asset_id);
