-- 09_v4_deep_dive_schema.sql
-- Subgraphs by Package & Intermediate Representation (IR)

-- 1. Package Table
CREATE TABLE IF NOT EXISTS package (
    package_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES solutions(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES asset(asset_id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    type TEXT, -- SSIS, DataStage, Python
    config JSONB DEFAULT '{}',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Package Components (Internal Hierarchy)
CREATE TABLE IF NOT EXISTS package_component (
    component_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id UUID NOT NULL REFERENCES package(package_id) ON DELETE CASCADE,
    parent_component_id UUID REFERENCES package_component(component_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- DataFlowTask, SQLTask, SequenceContainer, etc.
    logic_raw TEXT,
    config JSONB DEFAULT '{}',
    order_index INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Transformation IR (Intermediate Representation)
CREATE TABLE IF NOT EXISTS transformation_ir (
    ir_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES solutions(id) ON DELETE CASCADE,
    source_component_id UUID REFERENCES package_component(component_id) ON DELETE CASCADE,
    operation TEXT NOT NULL, -- READ, WRITE, SELECT, FILTER, JOIN, AGGREGATE, LOOKUP, DERIVE, SCD
    logic_summary TEXT,
    metadata JSONB DEFAULT '{}', -- { "input_cols": [...], "output_cols": [...], "expressions": "..." }
    confidence NUMERIC DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_package_project ON package(project_id);
CREATE INDEX IF NOT EXISTS idx_pkg_comp_package ON package_component(package_id);
CREATE INDEX IF NOT EXISTS idx_trans_ir_project ON transformation_ir(project_id);
CREATE INDEX IF NOT EXISTS idx_trans_ir_component ON transformation_ir(source_component_id);
