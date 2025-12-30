# DiscoverAI - Roadmap & Release Strategy

## ✅ Released: v4.0 "High-Fidelity Core"
The full base version of DiscoverAI.
- [x] **Hierarchical Prompting**: 4-layer intelligence (Base, Domain, Org, Solution).
- [x] **Structural Parsers**: Accurate native parsing for SSIS (.dtsx) and DataStage (.dsx).
- [x] **Governance Gateway**: Manual export system for Purview, Unity Catalog, and dbt.
- [x] **Integrated Documentation**: Contextual 'Guide' panels in Prompt Manager and Model Config.
- [x] **LLM Resilience**: Automated retry system for 429 errors.

---

## 🚀 Incoming: v5.0 "Ecosystem & Experience"
Focusing on seamless ingestion, automated syncs, and premium UI.

### 1. Ingestion & Automated Governance
- [ ] **dbt Manifest Ingestion**: Read `manifest.json` to overlay existing dbt documentation on technical lineage.
- [ ] **Direct Governance Sync**: Automated push to Unity Catalog/Purview via REST APIs (Phase 2).
- [ ] **Incremental Deep Dive**: Re-analyze only the specific sub-tasks changed in a project.

### 2. UI/UX "WOW" Factor
- [ ] **Interactive Lineage UI**: Drill-down from high-level packages to specific column transformations in the graph.
- [ ] **Glassmorphic Dashboard**: Modernized analytics view with high-quality micro-animations.
- [ ] **Real-time Progress Engine**: WebSocket-based progress bars for long-running analyses.

### 3. Infrastructure & Scale
- [ ] **Docker Deployment**: Full containerization for scale and easy on-premise installs.
- [ ] **Cloud-Native Workers**: Auto-scaling job processors based on queue depth.

---

## Known Issues (v4.0)
- **Neo4j Connectivity:** Transient "routing information" errors in Free tier AuraDB. (Status: Retry logic active).
- **Processing Scale:** ZIP files >50MB may experience UI timeouts while processing. (Status: Optimization scheduled for v5.1).

---
© 2025 DiscoverAI
