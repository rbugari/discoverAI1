import os
import logging
from typing import Dict, Any, Optional, List
from supabase import Client

logger = logging.getLogger(__name__)

class PromptService:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        # Default to file system if DB fails or for transition
        self.prompt_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")

    def get_composed_prompt(self, action_name: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Composes a layered prompt: Base + Domain + Org + Solution Rules.
        If no DB config found, falls back to legacy file system.
        """
        try:
            project_id = context.get("project_id")
            
            # 1. Fetch global and project-specific layers from DB
            layers = self._fetch_layers_for_action(action_name, project_id)
            
            if not layers:
                # Fallback to legacy file system
                logger.debug(f"[PROMPT] No DB layers for {action_name}, falling back to files.")
                full_prompt = self._load_from_file(action_name)
            else:
                composed = []
                if layers.get("base"): composed.append(layers["base"])
                if layers.get("domain"): composed.append(f"\n### DOMAIN SPECIALIZED INSTRUCTIONS\n{layers['domain']}")
                if layers.get("org"): composed.append(f"\n### ORGANIZATIONAL GUIDELINES\n{layers['org']}")
                if layers.get("solution"): composed.append(f"\n### PROJECT-SPECIFIC RULES (SOLUTION LAYER)\n{layers['solution']}")
                if layers.get("reasoner"): composed.append(f"\n### REASONING AGENT INSTRUCTIONS\n{layers['reasoner']}")
                full_prompt = "\n\n".join(composed)
            
            # 2. Interpolate variables
            return self._interpolate(full_prompt, input_data, context)
            
        except Exception as e:
            logger.error(f"[PROMPT] Error composing prompt for {action_name}: {e}")
            # Final fallback
            return self._load_from_file(action_name)

    def _fetch_layers_for_action(self, action_name: str, project_id: Optional[str] = None) -> Dict[str, str]:
        """Queries Supabase for the active prompt layers (Global + Project Specific)"""
        try:
            # Normalize: prompts/v3/extract_lineage_package.txt -> v3.extract.lineage.package
            norm_name = action_name.replace("prompts/", "").replace("_", ".").replace(".md", "").replace(".txt", "").replace("/", ".")
            if norm_name.startswith("."): norm_name = norm_name[1:]
            
            # 1. Query Global Layers
            res = self.supabase.table("action_prompt_config")\
                .select("*, base:base_layer_id(content), domain:domain_layer_id(content), org:org_layer_id(content)")\
                .eq("action_name", norm_name)\
                .execute()
            
            if not res.data:
                # Try with original name just in case
                res = self.supabase.table("action_prompt_config")\
                    .select("*, base:base_layer_id(content), domain:domain_layer_id(content), org:org_layer_id(content)")\
                    .eq("action_name", action_name)\
                    .execute()
            
            layers = {}
            if res.data:
                row = res.data[0]
                layers = {
                    "base": row.get("base", {}).get("content") if row.get("base") else None,
                    "domain": row.get("domain", {}).get("content") if row.get("domain") else None,
                    "org": row.get("org", {}).get("content") if row.get("org") else None,
                    "reasoner": row.get("reasoner", {}).get("content") if row.get("reasoner") else None
                }

            # 2. Query Project-Specific (Solution) Layer
            if project_id:
                p_res = self.supabase.table("project_action_config")\
                    .select("*, solution:solution_layer_id(content)")\
                    .eq("project_id", project_id)\
                    .eq("action_name", norm_name)\
                    .execute()
                
                if p_res.data:
                    layers["solution"] = p_res.data[0].get("solution", {}).get("content")

            return layers
        except Exception as e:
            logger.warning(f"[PROMPT] DB query failed: {e}")
            return {}

    def _load_from_file(self, action_name: str) -> str:
        """Legacy file loading logic for compatibility"""
        # Clean action name (e.g. extract.deep_dive -> extract_deep_dive)
        clean_name = action_name.replace('.', '_')
        
        # Try different extensions
        for ext in ['.md', '.txt']:
            path = os.path.join(self.prompt_dir, f"{clean_name}{ext}")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        # Fallback to name-based base prompt
        return f"Act as an expert analyst for the task: {action_name}. Return a technical JSON response."

    def _interpolate(self, template: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Robust interpolation of {variables} in the prompt string"""
        format_data = {**input_data, **context}
        for key, value in format_data.items():
            # Only replace if the key is actually in the template to avoid breaking JSON braces
            placeholder = f"{{{key}}}"
            if placeholder in template:
                if isinstance(value, str):
                    template = template.replace(placeholder, value)
                elif isinstance(value, (int, float, bool)):
                    template = template.replace(placeholder, str(value))
        return template
