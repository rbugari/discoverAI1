-- 10_v4_deep_lineage.sql
-- Refinements for deep column-level lineage and functional mapping

-- 1. Column Lineage Table
CREATE TABLE IF NOT EXISTS column_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES solutions(id) ON DELETE CASCADE,
    package_id UUID REFERENCES package(package_id) ON DELETE CASCADE,
    ir_id UUID REFERENCES transformation_ir(ir_id) ON DELETE CASCADE,
    
    source_asset_id UUID REFERENCES asset(asset_id) ON DELETE SET NULL,
    source_column TEXT,
    
    target_asset_id UUID REFERENCES asset(asset_id) ON DELETE SET NULL,
    target_column TEXT,
    
    transformation_rule TEXT,
    confidence NUMERIC DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Refine Package Component with Mapping fields if not present
-- (Adding columns to existing table from migration 09 if needed)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='package' AND column_name='source_system') THEN
        ALTER TABLE package ADD COLUMN source_system TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='package' AND column_name='target_system') THEN
        ALTER TABLE package ADD COLUMN target_system TEXT;
    END IF;
END $$;

-- 3. Refine Package Component for Source/Target Mapping
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='package_component' AND column_name='source_mapping') THEN
        ALTER TABLE package_component ADD COLUMN source_mapping JSONB DEFAULT '[]';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='package_component' AND column_name='target_mapping') THEN
        ALTER TABLE package_component ADD COLUMN target_mapping JSONB DEFAULT '[]';
    END IF;
END $$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_col_lineage_project ON column_lineage(project_id);
CREATE INDEX IF NOT EXISTS idx_col_lineage_pkg ON column_lineage(package_id);
CREATE INDEX IF NOT EXISTS idx_col_lineage_ir ON column_lineage(ir_id);
