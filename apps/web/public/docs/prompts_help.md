# Prompt Manager Help

The **Prompt Manager** is the "Brain" of DiscoverAI. It allows you to control exactly how the LLM thinks and behaves during different stages of the analysis.

## Key Concepts

### 1. Layered Prompting (Tiered Intelligence)
To ensure both global standards and local project nuances are respected, DiscoverAI uses a **4-layer composition model**:

1.  **BASE**: Fundamental logic. Defines how an action (like extraction) should be performed generally.
2.  **DOMAIN**: Specialist knowledge. Adds expertise for specific technologies like SSIS, SQL, or DataStage.
3.  **ORG**: Quality standards. Injects your company's coding and documentation guidelines.
4.  **SOLUTION**: Project-specific rules. Contains overrides for naming conventions or local business logic (e.g., "Northwind" mapping).

### 2. The Prompt Matrix
The **Action Mappings** tab shows the hierarchy for every feature in the system. 
- You can tune a single layer (e.g., update the ORG layer) and it will affect all actions using it.
- **Vertical Vibe**: Configure all layers for a specific action.
- **Horizontal Vibe**: Use a single ORG or DOMAIN layer across multiple actions for consistency.

## Pro Tips
- Use `{{variable_name}}` for interpolation. DiscoverAI will inject project context into these placeholders.
- Always verify your **Solution Layer** if a project has inconsistent naming conventions (like 3 different names for the same database).
