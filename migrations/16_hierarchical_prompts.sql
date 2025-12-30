-- v4.0 Hierarchical Prompting Expansion (Sprint 2)

-- Add SOLUTION type support (enforcing via check or documentation)
-- Add optional project_id to prompt_layer for project-specific fragments
ALTER TABLE prompt_layer ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES solutions(id);

-- Create table for project-specific action overrides/layers
CREATE TABLE IF NOT EXISTS project_action_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES solutions(id),
    action_name TEXT NOT NULL,
    solution_layer_id UUID REFERENCES prompt_layer(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(project_id, action_name)
);

-- Index for project-specific lookups
CREATE INDEX IF NOT EXISTS idx_project_action_config_proj ON project_action_config(project_id);
