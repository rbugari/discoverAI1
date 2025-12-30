-- v4.0 Layered Prompting Schema

-- Table for reusable prompt fragments/layers
CREATE TABLE IF NOT EXISTS prompt_layer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    layer_type TEXT NOT NULL, -- 'BASE', 'DOMAIN', 'ORG'
    name TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Junction table to configure prompts per action
CREATE TABLE IF NOT EXISTS action_prompt_config (
    action_name TEXT PRIMARY KEY, -- e.g. 'extract.deep_dive'
    base_layer_id UUID REFERENCES prompt_layer(id),
    domain_layer_id UUID REFERENCES prompt_layer(id),
    org_layer_id UUID REFERENCES prompt_layer(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_prompt_layer_type ON prompt_layer(layer_type);

-- Trigger for updated_at (optional, assuming current DB setup has it)
-- CREATE TRIGGER set_updated_at BEFORE UPDATE ON prompt_layer FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
