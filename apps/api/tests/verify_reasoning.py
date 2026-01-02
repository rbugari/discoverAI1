import asyncio
import os
import sys
from unittest.mock import MagicMock

# Set up path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.reasoning_service import ReasoningService
from app.services.catalog import CatalogService
from app.services.prompt_service import PromptService

async def verify_reasoning():
    print("--- Reasoning Agent Verification ---")
    
    # Mock dependencies
    supabase = MagicMock()
    catalog = MagicMock()
    prompts = MagicMock()
    
    # Set up mock returns
    catalog.get_solution_context.return_value = {
        "inventory": [{"asset_type": "table", "count": 45}, {"asset_type": "view", "count": 12}],
        "hotspots": [{"from": "A", "to": "B", "confidence": 0.4}],
        "packages": [{"name": "SalesData", "type": "SSIS"}]
    }
    
    prompts.get_composed_prompt.return_value = "Mock system prompt with context."
    
    # Instantiate service
    reasoning = ReasoningService(supabase, catalog, prompts)
    
    # Mock LLM call indirectly (ReasoningService uses get_llm_adapter())
    # This might be tricky without patching the singleton, so we'll just check if it instantiates.
    print("[TEST] ReasoningService instantiated successfully.")
    
    job_id = "00000000-0000-0000-0000-000000000000"
    project_id = "11111111-1111-1111-1111-111111111111"
    
    print(f"[TEST] Attempting synthesis for job {job_id}...")
    # This will actually call the LLM if not patched. 
    # For a safe verification, we'll just check the orchestration logic if we can.
    
    # Let's patch the LLM adapter in the service instance
    reasoning.llm = MagicMock()
    reasoning.llm.call_model.return_value = {
        "success": True,
        "content": "Architectural Overview: This is a complex ETL pipeline... Executive Summary: Highly recommended to refactor cluster B.",
        "provider": "mock",
        "tokens_in": 100,
        "tokens_out": 200
    }
    
    result = await reasoning.synthesize_global_conclusion(job_id, project_id)
    
    if "error" in result:
        print(f"[FAIL] Reasoning failed: {result['error']}")
    else:
        print("[SUCCESS] Reasoning synthesis completed successfully.")
        print(f"[DATA] Synthesis Preview: {result['final_synthesis'][:100]}...")
        
        # Verify DB calls
        if supabase.table.called:
            print("[SUCCESS] Database persistence calls were triggered.")

if __name__ == "__main__":
    asyncio.run(verify_reasoning())
