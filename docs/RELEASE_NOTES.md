# Release Notes - Nexus Discovery v4.0
 
**Date:** December 25, 2025
**Theme:** "Deep Understanding"
 
## 🌟 v4.0 Highlights
 
Nexus Discovery v4.0 introduces the **Deep Dive** engine, enabling granular extraction of ETL logic and column-level lineage.
 
### 1. Package Deep Dive
- **Granular Extraction**: The system now breaks down ETL packages (SSIS, DataStage) into internal components (DataFlowTasks, SQLTasks, Containers).
- **Intermediate Representation (IR)**: Normalization of business logic into a platform-agnostic format to facilitate future migrations.
 
### 2. Column-Level Lineage
- **Field-to-Field Mapping**: Precision tracking of data movement from source systems to targets, including intermediate transformation rules.
- **Deep Lineage Table**: New dedicated storage for high-resolution field mappings with confidence scores.
 
### 3. Silent Mode & Automation
- **Auto-Approval**: New `requires_approval: false` mode allows full end-to-end processing without manual plan confirmation.
- **LLM Resilience**: Integrated automatic retries with exponential backoff for handling 429 rate limit errors from providers like OpenRouter.
 
### 4. Optimized Model
- **Gemini 2.0 Flash Lite**: Configured as the primary model for technical extraction, providing superior speed and cost-effectiveness.

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
