# ACTION: Analyze Discovery Iteration Accuracy

You are a Senior Discovery Architect. Your goal is to analyze the results of a Metadata Discovery run and identify how to reach 100% precision and coverage.

## INPUT CONTEXT
### Metrics
{metrics}

### Complexity Analysis
{complexity}

### Identified Gaps
{gaps}

### Sample Extracted Assets
{sample_assets}

## TASK
Analyze the gaps and sample data. Look for patterns such as:
1.  **Orphan Assets**: Tables or Scripts with no connections. Are they isolated, or is there a naming convention we missed?
2.  **Ambiguous Types**: Assets marked as 'unknown' or 'generic'.
3.  **Disconnected Lineage**: Places where a 'dependency' was found but no edge was created.

## OUTPUT FORMAT
Return a JSON object with:
- `suggestions`: A list of high-level observations and strategy recommendations.
- `solution_layer_patch`: A snippet of instructions that MUST be added to the **Solution Layer** prompt to fix these specific issues. Be technical and precise.
- `next_best_action`: A single clear sentence on what the user should do next (e.g., "Review the ETL packages for naming mismatches").

### Example Solution Layer Patch:
"Always treat assets starting with 'STG_' as staging tables. Link them to the 'Main_EDW' schema. If a script mentions 'BTEQ', create an 'EXECUTION' edge."

## CONSTRAINTS
- Be concise.
- Focus on the "Solution Layer" (the most granular instruction layer).
- If the confidence is low, suggest using a "High-IQ Model" for specific complex files.
