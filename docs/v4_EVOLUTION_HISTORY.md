# DiscoverAI v4.0 - Evolution History

This document preserves the architectural journey and sprint-by-sprint development of DiscoverAI v4.0.

## 🏛️ Architectural Evolution

The v4.0 milestone marked the transition from a monolithic "V3" engine to a **Hierarchical & Structural** intelligence model.

### 1. Tiered Prompting Architecture
The system evolved into a 4-layer composition model where instructions are dynamically fused by the `PromptService`:
- **BASE**: Core technical action logic.
- **DOMAIN**: Specialized technology knowledge (SSIS, DataStage, etc.).
- **ORG**: Organizational standards and quality guidelines.
- **SOLUTION**: Project-specific rules and normalization logic.

### 2. High-Fidelity Structural Parsers
To minimize LLM hallucinations, v4.0 introduced native structural parsing:
- **SSIS (.dtsx)**: XML-based traversal of Control Flow and Data Flow tasks.
- **DataStage (.dsx)**: Metadata extraction from native DataStage export files.

---

## 🏃 Sprint Highlights

### Sprint 1: Kernel & Extraction v4.0
- **Goal**: Establish the foundation for structural parsing and layered prompts.
- **Key Deliverables**: 
    - Basic `PromptService` implementation.
    - Initial SSIS XML parser supporting Connection Managers and DFT internal mappings.
    - Centralized Admin Router for metadata management.

### Sprint 2: Hierarchical & Contextual Context
- **Goal**: Enable project-specific intelligence and normalization.
- **Key Deliverables**:
    - Expanded 4-layer hierarchy implementation.
    - **Prompt Matrix UI**: A professional dashboard to manage global and solution-specific layers.
    - Verification of "Northwind Normalization" where multiple connection strings are consolidated via the Solution Layer.

### Sprint 3: Governance Hub & Final Stabilization
- **Goal**: Externalize findings and stabilize the v4.0 core.
- **Key Deliverables**:
    - **GovernanceExportService**: platform-specific exports for **Microsoft Purview** (CSV), **Unity Catalog** (CSV), and **dbt** (`sources.yml`).
    - Final worker refactor for robustness and state-based progression.
    - Removal of legacy prompt files and archival of v3.0 logic.

---

## 🏁 Milestone Completion
DiscoverAI v4.0 is now the stable base for all subsequent "Agentic" features. It provides the high-fidelity extraction and contextual flexibility required for enterprise-grade data discovery.
