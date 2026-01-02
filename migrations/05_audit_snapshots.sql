-- DiscoverAI v5.0 P2: Run History & Snapshots
-- Store accuracy metrics and gaps after each iteration

CREATE TABLE IF NOT EXISTS audit_snapshot (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES solutions(id) ON DELETE CASCADE,
    job_id UUID REFERENCES job_run(job_id),
    metrics JSONB NOT NULL, -- {coverage_score, avg_confidence, total_assets, etc}
    gaps JSONB,           -- List of identified gaps
    recommendations JSONB, -- AI suggested improvements
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add index for performance on large projects
CREATE INDEX IF NOT EXISTS idx_audit_snapshot_project_id ON audit_snapshot(project_id);
CREATE INDEX IF NOT EXISTS idx_audit_snapshot_job_id ON audit_snapshot(job_id);
