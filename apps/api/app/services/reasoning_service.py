import logging
import json
from datetime import datetime
from typing import Dict, Any, List
from supabase import Client

from .catalog import CatalogService
from .llm_adapter import get_llm_adapter
from .prompt_service import PromptService

logger = logging.getLogger(__name__)

class ReasoningService:
    """
    The "Brain" of DiscoverAI v6.0.
    Coordinates architectural reasoning, expert consensus, and executive synthesis.
    """
    
    def __init__(self, supabase: Client, catalog: CatalogService, prompt_service: PromptService):
        self.supabase = supabase
        self.catalog = catalog
        self.prompts = prompt_service
        self.llm = get_llm_adapter()

    async def synthesize_global_conclusion(self, job_id: str, project_id: str) -> Dict[str, Any]:
        """
        Main execution loop for Reasoning Synthesis.
        1. Gathers context (Inventory, Hotspots, Packages).
        2. Runs the Reasoning Loop (Thoughts -> Synthesis).
        3. Persists results.
        """
        print(f"[REASONING AGENT] Starting synthesis for job {job_id}")
        
        try:
            # 1. Gather Context
            context = self.catalog.get_solution_context(project_id)
            
            # 2. Prepare Messages for the Reasoner
            # We'll use the 'REASONER' layer from PromptService (V6 upgrade)
            # The PromptService handles Base + Domain + Org + Solution layers.
            input_data = {"inventory_json": json.dumps(context, indent=2)}
            system_prompt = self.prompts.get_composed_prompt(
                "reasoning.architect", 
                input_data, 
                {"project_id": project_id, "job_id": job_id}
            )

            messages = [
                {"role": "system", "content": "You are a sentient architectural reasoning assistant specialized in data lineage."},
                {"role": "user", "content": system_prompt}
            ]

            # 3. Call High-Tier Reasoner (e.g., Gemini 1.5 Pro via OpenRouter)
            # Default to the configured model but suggest high-tier
            res = self.llm.call_model(
                model="google/gemini-2.0-flash-exp:free", # Preference for high-tier reasoning
                messages=messages,
                temperature=0.3, # Slightly more creative for synthesis
                max_tokens=2500
            )

            if not res["success"]:
                raise Exception(f"LLM Reasoning failed: {res.get('error')}")

            raw_content = res["content"]
            
            # 4. Parse "Chain of Thought" vs "Synthesis"
            # Simple heuristic: Split by a marker or just store the whole thing if not strictly separated.
            # In v6.2 we want to separate 'thought_process' from 'final_synthesis'.
            
            thought_process = "Agent analyzed inventory and identified key clusters." # Placeholder or extracted
            final_synthesis = raw_content
            
            # Try to extract JSON if the agent followed instructions
            try:
                if "{" in raw_content:
                    json_start = raw_content.find("{")
                    json_end = raw_content.rfind("}") + 1
                    json_str = raw_content[json_start:json_end]
                    # Validate JSON
                    json.loads(json_str)
                    # If valid, we could use this for structured fields
            except:
                pass

            # 5. Persist to DB
            log_entry = {
                "job_id": job_id,
                "solution_id": project_id,
                "thought_process": thought_process,
                "final_synthesis": final_synthesis,
                "model_consensus": {
                    "provider": res["provider"],
                    "model": "google/gemini-2.0-flash-exp:free",
                    "tokens_in": res["tokens_in"],
                    "tokens_out": res["tokens_out"]
                }
            }
            
            self.supabase.table("reasoning_log").insert(log_entry).execute()
            
            # 6. Update Job Run cache
            summary_snippet = final_synthesis[:500] + "..." if len(final_synthesis) > 500 else final_synthesis
            self.supabase.table("job_run").update({"synthesis_summary": summary_snippet}).eq("job_id", job_id).execute()

            print(f"[REASONING AGENT] Synthesis completed for job {job_id}")
            return log_entry

        except Exception as e:
            logger.error(f"Reasoning synthesis failed: {e}")
            print(f"[REASONING AGENT] ERROR: {e}")
            return {"error": str(e)}
