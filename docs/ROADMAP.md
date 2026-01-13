# DiggerAI - Roadmap & Release Strategy

## ✅ Released: v6.0 "Immersive Intelligence"
La versión de cierre para el ciclo "Reasoning & Governance".
- [x] **Optimization Auditor**: Detección de brechas y auto-parcheo de prompts.
- [x] **Master Synthesis**: Reportes técnicos profesionales (PDF/MD) autogenerados.
- [x] **Governance Gateways**: Purview, Unity Catalog y dbt support.
- [x] **Hi-Fi Parsers**: Soporte nativo SSIS, DataStage y dbt.
- [x] **LLM Resilience**: Sistema robusto de reintentos y backoff.

---

## 🚀 Incoming: v7.0 "Deep Insight & Scale"
Enfocado en granularidad, integraciones nativas y escala masiva.

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
© 2026 DiggerAI
