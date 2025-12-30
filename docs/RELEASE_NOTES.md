# Release Notes - DiscoverAI v4.0 (Full Base)
 
**Date:** December 30, 2025
**Theme:** "Deep Understanding & Governance"
 
## 🌟 v4.0 Highlights
 
Nexus Discovery v4.0 establishes the "Full Base" version of the platform, moving from simple extraction to structured enterprise-grade intelligence.
 
### 1. High-Fidelity structural Parsers
- **SSIS & DataStage**: Native XML and metadata parsing for `.dtsx` and `.dsx` files, ensuring 100% accurate lineage extraction without LLM hallucinations.
 
### 2. Hierarchical Prompt System (Sprint 2)
- **4-Layer Composition**: Dynamic fusion of Base, Domain, Org, and Solution layers for project-specific intelligence.
- **Prompt Matrix UI**: Redesigned administrative dashboard for managing global and solution-specific prompt fragments.
 
### 3. Governance Hub & Exports (Sprint 3)
- **Manual Gateways**: Direct generation of metadata for **Microsoft Purview**, **Unity Catalog**, and **dbt** (`sources.yml`).
- **Standardized Lineage**: Column-level results exported in platform-specific formats for easy ingestion.
 
### 4. integrated Documentation (V5 Phase 1)
- **In-App Guides**: Integrated help overlays in the Prompt Manager and Model Config to bridge the technical knowledge gap.
 
### 5. Silent Mode & LLM Resilience
- **Automation**: `requires_approval: false` for full E2E processing.
- **Backoff System**: Automated retry logic for 429 rate limit errors.

---

# Release Notes - Nexus Discovery v3.1

**Date:** December 23, 2025
**Theme:** "Performance & Precision"

## 🌟 Highlights

DiscoverAI v3.1 finalizes the **Plan-Driven Orchestrator** and stabilizes the extraction engine.

### 1. Multi-provider & Dynamic Routing
- **Provider Agnostic**: The system can now route different files to different LLM providers (OpenRouter, Groq, Anthropic) based on cost and capability.
- **Dynamic Config**: Admins can switch models and providers at runtime via a centralized configuration system.

### 2. Truly Incremental Processing
- **Hash Tracking**: Each file's hash is stored. Retrying or updating a solution now skips unchanged files automatically, saving tokens and money.

### 3. UX Consolidation
- **Optimized Dashboard**: Fast solution loading using a new consolidated `/active-plan` endpoint.
- **Direct Actions**: "View Graph" and "View Catalog" buttons added to the dashboard.
- **Graph Filtering**: Built-in filters to isolate lineage by node type (Table, Pipeline, etc.).

## 🛠 Technical Improvements
- **Extraction Success**: Achieved 100% success rate (43/43) on large SSIS packages using optimized Gemini-2.0 routes.
- **Neo4j Sync**: Reliable background synchronization between relation graph and SQL warehouse.

## 🐛 Bug Fixes
- **Audit System**: Fixed a critical `chk_strategy` constraint violation and ID mismatch in the auditing layer.
- **Cleanup**: Improved "Full Re-analyze" mode to reliably clean Neo4j, plans, and audit logs.
- **Constraint Fix**: Resolved strategy mapping issues (SQL enum mismatches).

## 🔜 What's Next (v3.2)
- Advanced RAG over lineage (Impact Analysis chat).
- Column-level lineage visualization.
- PDF Export for technical documentation.
