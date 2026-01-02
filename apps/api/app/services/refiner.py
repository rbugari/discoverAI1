from typing import Dict, List, Any
from .auditor import DiscoveryAuditor
from ..router import get_model_router
from ..actions import ActionRunner
import logging

logger = logging.getLogger(__name__)

class DiscoveryRefiner:
    def __init__(self, auditor: DiscoveryAuditor, action_runner: ActionRunner):
        self.auditor = auditor
        self.action_runner = action_runner

    def generate_recommendations(self, project_id: str) -> Dict[str, Any]:
        """
        Synthesizes audit results and uses an LLM to suggest specific improvements.
        Includes Model IQ Switcher logic.
        """
        # 1. Get Audit Report
        audit_report = self.auditor.run_audit(project_id)
        
        # 2. Complexity Analysis (v5.0 Phase 3)
        complexity = self.auditor.analyze_complexity(project_id)
        
        # 3. Extract Top Gaps for Context
        gaps_summary = "\n".join([f"- {g['type']}: {g['description']}" for g in audit_report['gaps']])
        
        # 4. Preparing Refinement Input
        refine_input = {
            "metrics": audit_report['metrics'],
            "gaps": gaps_summary,
            "complexity": complexity,
            "sample_assets": self._get_sample_data(project_id)
        }
        
        try:
            res = self.action_runner.run_action("action.analyze_iteration", refine_input, {"project_id": project_id})
            
            if res.success:
                suggestions = res.data.get("suggestions", [])
                
                # Model IQ Switcher logic
                if complexity["is_high_complexity"]:
                    suggestions.append({
                        "type": "MODEL_UPGRADE",
                        "priority": "HIGH",
                        "description": "Project complexity is high. Recommendation: Use GPT-4o or Claude 3.5 for deeper lineage extraction.",
                        "potential_impact": "+20% Accuracy in complex packages"
                    })

                # Merge AI suggestions into audit report recommendations for persistence
                for sug in suggestions:
                    if isinstance(sug, dict):
                        desc = sug.get("description", str(sug))
                        audit_report["recommendations"].append(f"AI Suggestion: {desc}")
                    else:
                        audit_report["recommendations"].append(f"AI Suggestion: {sug}")

                return {
                    "project_id": project_id,
                    "audit": audit_report,
                    "complexity": complexity,
                    "ai_suggestions": suggestions,
                    "suggested_solution_layer": res.data.get("solution_layer_patch", ""),
                    "next_best_action": res.data.get("next_best_action", "Refine the Solution Layer and run analysis again.")
                }
        except Exception as e:
            logger.error(f"[REFINER] AI Refinement failed: {e}")

        return {
            "project_id": project_id,
            "audit": audit_report,
            "complexity": complexity,
            "ai_suggestions": ["Perform a secondary run with higher model temperature."],
            "suggested_solution_layer": "",
            "next_best_action": "Manual review of orphan assets."
        }

    def _get_sample_data(self, project_id: str) -> str:
        # Fetch some assets with 'unknown' tags or low confidence to help the LLM
        res = self.auditor.supabase.table("asset").select("name_display, tags").eq("project_id", project_id).limit(10).execute()
        return "\n".join([f"- {a['name_display']}: {str(a['tags'])[:200]}" for a in res.data])
