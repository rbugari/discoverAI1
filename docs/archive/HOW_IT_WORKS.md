# How DiscoverAI Works: A Logical Autopsy

This document explains the internal reasoning process of DiscoverAI ("The System"), detailing exactly what happens when you upload a repository or select a project. It breaks down the "thought process," the criteria used for decisions, and the flow of data from raw code to an intelligent knowledge graph.

---

## 🏗️ Phase 1: Ingestion & The "Sensory" Scan
**Goal:** Create a structured inventory of the unknown.

When you point the system to a repository (e.g., a ZIP file or GitHub repo), it doesn't just "read" it; it **audits** it.

### 1.1 The Walk (The Senses)
The System's `PlannerService` physically walks through every directory and file. It builds a manifest of what exists, ignoring noise (like `.git`, `node_modules`).

### 1.2 Classification Strategy (The Cortex)
For every file found, the `Planner` applies a **Heuristic Classification** to decide *how* to process it. It doesn't treat all files equally.

*   **Logic:**
    *   **Is it Foundation?** (`.sql`, `.ddl`, `schema` folders) -> **High Priority**. These define the "Truth".
        *   *Strategy:* `PARSER_PLUS_LLM`. Use a strict SQL parser first, then LLM for context.
    *   **Is it Orchestration?** (`.dtsx` for SSIS, `.dsx` for Datastage, `jobs` folders) -> **Critical**. These define "Movement".
        *   *Strategy:* `HYBRID_PARSER`. Extract hard-coded flows programmatically, use AI to understand business intent.
    *   **Is it Scripting?** (`.py`, `.sh`, `.ps1`) -> **Context**.
        *   *Strategy:* `LLM_ONLY`. Pure reading by the AI Model to understand logic.
    *   **Is it Configuration?** (`.xml`, `.json`, `.yaml`) -> **Support**.
        *   *Strategy:* `PARSER_ONLY`. Extract key-values (connections, credentials).

**Outcome:** A `JobPlan` is created. This is a battle plan. It groups files into "Areas" (Foundation, Packages, Auxiliary) and assigns a processing cost/time estimate.

### 🔬 Technical Deep Dive: Planner
*   **Logic File**: `apps/api/app/services/policy_engine.py`
*   **Input**: File Metadata (`path`, `size`, `extension`).
*   **Key Function**: `evaluate(file_path, size_bytes)`
*   **Decision Matrix**:
    *   `node_modules/` OR `.git/` → `RecommendedAction.SKIP`
    *   `size > 500MB` → `RecommendedAction.SKIP`
    *   `.sql` → `Strategy.PARSER_PLUS_LLM`
    *   `.py` → `Strategy.LLM_ONLY`


---

## 🧠 Phase 2: Autonomous Reasoning (AI Processing)
**Goal:** Convert "Files" into "Meaning".

Once the Plan is approved (or auto-run), the **Pipeline Orchestrator** wakes up the Agents. This is where the "Thinking" happens.

### 2.1 The Decomposition (Refiner Agent)
The System picks up a file (e.g., `UpdateSales.sql`) and sends it to the LLM (e.g., Gemini 2.0 / GPT-4o) with a specific **Cognitive Prompt**.

**The Prompt Structure:**
> "You are an Expert Data Architect. meticulous and precise.
> **Context:** This file is part of [Project Name].
> **Task:** Reverse engineer the data lineage.
> **Criteria:**
> 1. Identify all **INPUTS** (Tables, Views, APIs).
> 2. Identify all **OUTPUTS** (Target Tables).
> 3. Extract **TRANSFORMATIONS** (joins, filters, business rules).
> 4. Assign a **CONFIDENCE SCORE** (0.0 - 1.0) to your findings."

**The Result:** The AI doesn't just summary text; it returns a **Structured Graph JSON**. It says: *"I am 95% sure `Table_A` feeds `Table_B` using a Left Join on `customer_id`"*.

### 🔬 Technical Deep Dive: Refiner Agent
*   **Logic File**: `apps/api/app/prompts/extract_deep_dive.md` (Template)
*   **Injection Mechanism**: `apps/api/app/services/prompt_service.py`
*   **Input Variables**:
    *   `{content}`: The raw file content (read from disk).
    *   `{file_type}`: e.g., "SQL Script" or "SSIS Package".
    *   `{macro_nodes}`: Context from previous shallow scans.
*   **Expected LLM Output (JSON)**:
    ```json
    {
      "package": { "name": "UpdateSales", "type": "SQL" },
      "lineage": [
        { "source_asset_name": "Staging_Sales", "target_asset_name": "Fact_Sales", "confidence": 0.95 }
      ]
    }
    ```

### 🔬 Technical Deep Dive: X-Ray Visualization
The "X-Ray Mode" in the frontend bridges the gap between the Backend's reasoning and the User's eye.
*   **Data Flow**: `GraphService` -> `edge.data` -> `rationale` & `confidence`.
*   **Visual**: A "Glassmorphic" tooltip renders this metadata on hover, allowing users to audit the AI's "Confidence Score" without leaving the graph.

### 2.2 The "Missing Link" Analysis
If the AI sees a reference to `crm.users` but hasn't seen that table definition yet, it creates a **Ghost Node** (a Hypothesis).
*   *Logic:* "I see usage, but no definition. Marker: `IS_HYPOTHESIS = True`."
*   *Purpose:* This helps identify missing files or external dependencies.

---

## 🔗 Phase 3: Synthesis & Graph Construction
**Goal:** Connect the dots.

The `GraphService` takes thousands of these individual file analyses and stitches them together into a single **Neo4j Knowledge Graph**.

### 3.1 Link Resolution
*   File A says: "I write to `Sales_Final`".
*   File B says: "I read from `Sales_Final`".
*   **The System's Logic:** "Match! Create an edge: `File A` -> [Lineage] -> `File B`."

### 3.2 The Audit (Self-Reflection)
After building the graph, the `DiscoveryAuditor` runs a self-check.

**Criteria for "Gaps":**
1.  **Orphan Assets:** Nodes with 0 connections. (Why does this script exist if it talks to nothing?)
2.  **Low Confidence Clusters:** Areas where the AI was unsure (< 50% confidence).
    *   *System Decision:* Flag as a "Risk Area" for human review.
3.  **Cyclic Dependencies:** Logic loops that might break pipelines.

---

## ✨ Phase 4: Executive Synthesis ("The Brain")
**Goal:** Explain *why* it matters.

Finally, the `ReasoningService` looks at the entire graph (Inventory + Hotspots + Gaps) and asks the High-Tier Model (Gemini 2.0 Flash / Pro) to write a summary.

**The Prompt:**
> "Review the entire architecture inventory provided below.
> Identify logical clusters.
> Spot architectural risks (spaghetti code, single points of failure).
> Suggest 3 strategic improvements."

**Output:** THIS is what you see in the Dashboard under "Discovery Health" and "Knowledge Gaps".

---

## Summary of Decision Making

| Step | Who Decides? | Criteria |
| :--- | :--- | :--- |
| **Parsing Strategy** | `PlannerService` (Code) | File Extension + Folder Path (Regex) |
| **Lineage logic** | `RefinerAgent` (AI) | SQL Syntax, Variable Data Flow, Table References |
| **Risk/Gap Flags** | `DiscoveryAuditor` (Code) | Confidence < 0.5, Degree Centrality = 0 (Orphan) |
| **Global Insight** | `ReasoningService` (AI) | Pattern Recognition across the full Inventory |

This hybrid approach (Strict Code Logic + Fluid AI Reasoning) allows DiscoverAI to be precise with syntax (SQL) but adaptive with intent (Business Logic).
