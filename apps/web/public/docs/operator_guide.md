# Operator's Management Guide

Hello, Operator. Your mission is to ensure the Discovery engine runs smoothly, efficiently, and at scale.

## 1. Monitoring the Flow
The **Job Queue** is your primary dashboard.
- Watch for real-time status updates: `INGEST` -> `PLANNING` -> `AUDIT` -> `REASONING`.
- If a job stays in `PENDING_APPROVAL`, it's waiting for an Architect to validate the plan.

## 2. Reprocessing (Nuclear Option)
When a solution needs a completely fresh start (e.g., after significant source code changes):
- Use the **Nuclear Reset**. This wipes the knowledge graph and artifacts for that solution to ensure no stale data remains.
- The system will automatically restart the ingestion and planning phase.

## 3. Storage & Artifacts
The **Artifact Sandbox** keeps a tidy record of every discovery.
- Use the sandbox to manage archival PDFs and markdown summaries.
- Ensure the local storage has sufficient headroom for large ETL repositories.

> [!WARNING]
> Reprocessing is irreversible. Always ensure you have a backup of manual notes before a Nuclear Reset.
