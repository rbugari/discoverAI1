# Model Configuration Help

The **Model Configuration** screen manages the "Nervous System" of DiscoverAI. It determines which LLM provider and which specific models are used for each task.

## Key Concepts

### 1. Provider Profiles
DiscoverAI is multi-cloud. You can switch between providers to balance cost, performance, and privacy:
- **Groq**: Ultra-fast inference. Best for quick extractions and triage.
- **OpenRouter**: Access to a wide variety of models (Claude, GPT-4o, etc.).
- **OpenAI**: The standard for high-complex reasoning.

### 2. Routing Strategy
Different tasks require different "IQ" levels. A Routing Strategy maps actions to models:
- **Fast models** (e.g., Gemini Flash) are used for high-volume file triage.
- **Smart models** (e.g., GPT-4o or Claude 3.5) are used for complex architectural reasoning.

## How to Switch
1. Select a **Provider** (defines the API keys and endpoints).
2. Select a **Routing Strategy** (defines which model goes to which action).
3. Click **Apply Configuration**. The system will immediately update its routing table for all new jobs.

## Note on Stability
Changing the configuration while a job is running is safe; the job will continue with its initial configuration, and new jobs will use the updated settings.
