# Architect's Technical Guide

Welcome, Architect. You are in control of the intelligence core. Here is how to maximize the analytical IQ of DiscoverAI.

## 1. The Prompt Matrix (v4.0)
The heart of the system is the **Layered Prompting Engine**. Every analysis is composed of four layers:
- **Base Layer**: The static technical knowledge.
- **Domain Layer**: Specialized logic for Finance, Health, or Retail.
- **Org Layer**: Your company's specific naming conventions and standards.
- **Solution Layer**: Project-specific logic (e.g., "In this repo, table X is the gold source").

## 2. Tuning the Reasoning Brain
Use the **REASONER** layer to define how the agent should think. 
- You can instruct it to focus on **redundancy detection**, **GDPR compliance**, or **performance bottlenecks**.
- The agent uses a "Scratchpad" approach—it will reason about your instructions before outputting the final JSON.

## 3. High-Fidelity Extraction
For complex legacy systems like **SSIS** or **DataStage**, use the structural parsers. These don't just "read" code; they rebuild the XML/DSX hierarchy to ensure zero-loss lineage.

> [!TIP]
> Always verify your "Solution Layers" after a reprocess run to ensure the agent is learning from your feedback loop.
