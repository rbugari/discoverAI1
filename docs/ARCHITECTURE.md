# DiggerAI: Architecture & Reasoning Logic

This document details the internal "brain" of DiggerAI, explaining how the platform transforms raw code into a structured, navigable knowledge graph using a hybrid approach of **Deterministic Parsing** and **Agentic Reasoning**.

---

## 🏗️ Phase 1: Ingestion & Strategic Planning
**Goal:** Map the territory and define the extraction strategy.

The `PlannerService` performs an initial audit of the repository to categorize files and assign them to the most efficient processing strategy:

- **Foundation Assets** (`.sql`, `.ddl`): Processed via `PARSER_PLUS_LLM` for maximum precision.
- **Data Movement Packages** (`.dtsx`, `.dsx`): Handled by a **Hybrid Parser** that extracts programmatic flows before AI enrichment.
- **Application Logic** (`.py`, `.sh`): Analyzed via **Autonomous Reasoning (LLM-Only)** to understand complex data transformations.

---

## 🧠 Phase 2: Autonomous Refinement
**Goal:** Extract meaning and internal lineage.

The **Pipeline Orchestrator** dispatches tasks to the **Refiner Agents**. Each agent is equipped with a **Multi-Layer Prompt Matrix** (Base, Domain, Org, Solution) to ensure the extraction is both technically accurate and contextually aware.

- **X-Ray Analysis**: The agent assigns a **Confidence Score** and a **Rationale** to every link it finds.
- **Ghost Node Hypotheses**: If a dependency is detected but not found in the source code, a "Ghost Node" is created to identify knowledge gaps.

---

## 🔗 Phase 3: Graph Synthesis & Neo4j Linking
**Goal:** Connect the dots across the entire ecosystem.

Individual file insights are pushed to a **Neo4j Graph Database**. The `GraphService` then resolves cross-file dependencies:
- **Link Resolution**: If File A writes to `Sales_Final` and File B reads from it, a **Global Lineage Edge** is automatically established.
- **Audit Mode**: The `DiscoveryAuditor` scans the final graph for **Orphan Assets** (nodes with no connections) and **High-Risk Clusters** (low-confidence lineage).

---

## 📈 Phase 4: Executive Insight (The Reasoning Layer)
**Goal:** Synthesize the "Big Picture".

The final stage involves the **ReasoningService**, which analyzes the complete topology to identify architectural patterns, technical debt, and modernization opportunities. This intelligence is delivered via the **Solution Dashboard** and the **Autonomous Discovery Agent**.

---
© 2026 DiggerAI | Advanced Agentic Coding
