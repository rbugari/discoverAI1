-- Phase 6.2: Reasoning Logs and Synthesis
-- Storage for the Reasoning Agent's internal thought process and model consensus.

CREATE TABLE IF NOT EXISTS reasoning_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES job_run(job_id) ON DELETE CASCADE,
    solution_id UUID REFERENCES solutions(id) ON DELETE CASCADE,
    model_consensus JSONB, -- Stores findings from multiple models (e.g., Gemini, DeepSeek)
    thought_process TEXT, -- The agent's "Scratchpad" or internal monologue
    final_synthesis TEXT, -- The final executive narrative
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add a column to job_run to cache the latest synthesis summary for quick UI access
ALTER TABLE job_run ADD COLUMN IF NOT EXISTS synthesis_summary TEXT;

COMMENT ON TABLE reasoning_log IS 'Stores the agentic reasoning process and synthesized architectural conclusions.';
