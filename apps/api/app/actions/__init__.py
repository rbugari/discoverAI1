"""
Action Runner - Executes LLM actions with fallback support
"""
import time
import json
import traceback
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

from ..router import get_model_router, ActionConfig, ModelConfig
from ..audit import FileProcessingLogger
from ..services.llm_adapter import get_llm_adapter
from ..services.prompt_service import PromptService
from ..config import settings
from supabase import create_client

@dataclass
class ActionResult:
    """Result of executing an action"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    # Metrics
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_estimate_usd: Optional[float] = None
    
    # Fallback information
    fallback_used: bool = False
    models_attempted: Optional[List[str]] = None

class ActionRunner:
    """
    Executes LLM actions with automatic fallback support
    """
    
    def __init__(self, logger: Optional[FileProcessingLogger] = None):
        self.router = get_model_router()
        self.logger = logger or FileProcessingLogger()
        self.llm_service = get_llm_adapter()
        
        # v4.0 Prompt Service
        from ..routers.solutions import get_supabase
        self.supabase = get_supabase()
        self.prompt_service = PromptService(self.supabase)
        
        # Cost estimates per model (USD per 1K tokens)
        self.cost_estimates = {
            "llama-3.3-70b-versatile": 0.00059, # Groq
            "llama-3.1-8b-instant": 0.00005,    # Groq
            "mistralai/devstral-2512:free": 0.0, 
            "google/gemini-2.0-flash-exp": 0.0, 
            "google/gemini-1.5-flash": 0.000075,
            "meta-llama/llama-3-8b-instruct:free": 0.0,
            "qwen/qwen-2.5-instruct": 0.0008,
            "qwen/qwen-2.5-coder": 0.001,
            "deepseek/deepseek-chat": 0.002,
            "google/gemini-2.0-flash-thinking": 0.003,
            "deepseek/deepseek-v3.2": 0.0006, # Estimated for V3
            "google/gemini-2.5-flash-lite": 0.00005, # Premium Lite pricing
        }
    
    def run_action(
        self, 
        action_name: str, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any],
        log_id: Optional[str] = None
    ) -> ActionResult:
        """
        Executes an action with its primary configuration
        
        Args:
            action_name: Name of the action (e.g., 'triage_fast')
            input_data: Input data for the action
            context: Additional context (job_id, file_path, etc.)
            log_id: Audit log ID (optional)
            
        Returns:
            ActionResult with the execution result
        """
        start_time = time.time()
        
        try:
            # Get action configuration
            action_config = self.router.get_action_config(action_name)
            
            # Execute with primary model
            result = self._execute_single_model(
                action_config.primary, 
                input_data, 
                context,
                log_id
            )
            
            # If failed and fallbacks exist, try them
            if not result.success and action_config.fallbacks:
                return self._execute_fallbacks(
                    action_config.fallbacks,
                    input_data,
                    context,
                    log_id,
                    start_time,
                    action_config.primary.model
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing action '{action_name}': {str(e)}"
            print(f"[ACTION_RUNNER] {error_msg}")
            
            return ActionResult(
                success=False,
                error_message=error_msg,
                error_type="action_execution_error",
                latency_ms=int((time.time() - start_time) * 1000)
            )
    
    def _execute_single_model(
        self, 
        model_config: ModelConfig, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any],
        log_id: Optional[str] = None
    ) -> ActionResult:
        """Executes a single model"""
        start_time = time.time()
        
        try:
            # v4.0 Composed Prompt
            prompt_content = self.prompt_service.get_composed_prompt(model_config.prompt_file, input_data, context)
            print(f"[ACTION_RUNNER] Executing {model_config.model} (Provider: {model_config.provider})")
            
            # Prepare messages for LLM
            is_diagram = "diagram" in model_config.prompt_file or "diagram" in context.get("file_path", "").lower()
            
            if is_diagram and isinstance(input_data.get("content"), str):
                file_path = context.get('file_path', '').lower()
                ext = file_path.split('.')[-1] if '.' in file_path else "jpg"
                
                mime_type = "image/jpeg"
                if ext == "png": mime_type = "image/png"
                elif ext == "webp": mime_type = "image/webp"
                elif ext == "gif": mime_type = "image/gif"
                
                messages = [
                    {"role": "system", "content": prompt_content},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": f"Analyze this diagram from file: {context.get('file_path')}. Identify all entities and relationships."},
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{input_data['content']}"
                                }
                            }
                        ]
                    }
                ]
            else:
                # Standard Text format
                safe_input = input_data.copy()
                if "content" in safe_input and isinstance(safe_input["content"], str):
                    if len(safe_input["content"]) > 100000:
                        safe_input["content"] = safe_input["content"][:100000] + "... (truncated)"
                
                input_json = json.dumps(safe_input)
                
                messages = [
                    {"role": "system", "content": prompt_content},
                    {"role": "user", "content": input_json}
                ]
            
            # Call LLM
            llm_result = self.llm_service.call_model(
                model=model_config.model,
                messages=messages,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                provider=model_config.provider,
                json_mode=self._requires_json_validation(model_config.prompt_file)
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            if not llm_result.get("success"):
                error_detail = llm_result.get("error", "Unknown LLM error")
                print(f"[ACTION_RUNNER] Model {model_config.model} failed: {error_detail}")
                return ActionResult(
                    success=False,
                    error_message=error_detail,
                    error_type="llm_error",
                    model_used=model_config.model,
                    latency_ms=latency_ms
                )
            
            # Parse response
            response_content = llm_result.get("content", "")
            
            # Validate JSON if required
            if self._requires_json_validation(model_config.prompt_file):
                try:
                    # Clean response to extract JSON
                    cleaned_content = self._clean_json_response(response_content)
                    parsed_data = json.loads(cleaned_content)
                    
                    # Validate against specific schema
                    validation_error, fixed_data = self._validate_json_schema(
                        parsed_data, 
                        model_config.prompt_file
                    )
                    
                    if validation_error:
                        print(f"[ACTION_RUNNER] JSON Validation Failed for {model_config.model}: {validation_error}")
                        print(f"[ACTION_RUNNER] Raw Content Preview: {cleaned_content[:200]}...")
                        return ActionResult(
                            success=False,
                            error_message=f"JSON validation failed: {validation_error}",
                            error_type="validation_error",
                            model_used=model_config.model,
                            latency_ms=latency_ms
                        )
                    
                    response_data = fixed_data
                    
                except json.JSONDecodeError as e:
                    print(f"[ACTION_RUNNER] JSON Decode Error for {model_config.model}: {e}")
                    print(f"[ACTION_RUNNER] Raw Content Preview: {cleaned_content[:200]}...")
                    return ActionResult(
                        success=False,
                        error_message=f"Invalid JSON response: {str(e)}",
                        error_type="json_parse_error",
                        model_used=model_config.model,
                        latency_ms=latency_ms
                    )
            else:
                response_data = {"content": response_content}
            
            # Estimate cost
            tokens_in = llm_result.get("tokens_in", 0)
            tokens_out = llm_result.get("tokens_out", 0)
            total_tokens = tokens_in + tokens_out
            cost_estimate_usd = self._estimate_cost(model_config.model, total_tokens)
            
            # Update audit log if exists
            if log_id:
                self.logger.update_model_usage(log_id, model_config.provider, model_config.model)
                self.logger.update_tokens_and_cost(
                    log_id, tokens_in, tokens_out, cost_estimate_usd, latency_ms
                )
            
            return ActionResult(
                success=True,
                data=response_data,
                model_used=model_config.model,
                latency_ms=latency_ms,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                total_tokens=total_tokens,
                cost_estimate_usd=cost_estimate_usd
            )
            
        except Exception as e:
            error_msg = f"Error executing model '{model_config.model}': {str(e)}"
            print(f"[ACTION_RUNNER] {error_msg}")
            
            return ActionResult(
                success=False,
                error_message=error_msg,
                error_type="model_execution_error",
                model_used=model_config.model,
                latency_ms=int((time.time() - start_time) * 1000)
            )
    
    def _execute_fallbacks(
        self,
        fallback_configs: List[ModelConfig],
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        log_id: Optional[str],
        start_time: float,
        primary_model: str
    ) -> ActionResult:
        """Executes fallback chain"""
        
        print(f"[ACTION_RUNNER] Primary model '{primary_model}' failed, trying fallbacks...")
        
        models_attempted = [primary_model]
        
        for i, fallback_config in enumerate(fallback_configs):
            print(f"[ACTION_RUNNER] Trying fallback {i+1}/{len(fallback_configs)}: {fallback_config.model}")
            
            result = self._execute_single_model(
                fallback_config, 
                input_data, 
                context,
                log_id
            )
            
            models_attempted.append(fallback_config.model)
            
            if result.success:
                # Mark that fallback was used
                result.fallback_used = True
                result.models_attempted = models_attempted
                
                if log_id:
                    self.logger.update_model_usage(
                        log_id, 
                        fallback_config.provider, 
                        result.model_used,
                        fallback_used=True,
                        fallback_chain=models_attempted
                    )
                
                print(f"[ACTION_RUNNER] Fallback successful with {result.model_used}")
                return result
        
        # All fallbacks failed
        print(f"[ACTION_RUNNER] All fallbacks exhausted. Models attempted: {models_attempted}")
        
        return ActionResult(
            success=False,
            error_message="All models failed. Fallback chain exhausted.",
            error_type="fallback_exhausted",
            fallback_used=True,
            models_attempted=models_attempted,
            latency_ms=int((time.time() - start_time) * 1000)
        )
    
    def _load_prompt(self, prompt_file: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Loads and prepares the prompt"""
        try:
            # Build full prompt path
            prompt_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
            
            # models.yml can contain "prompts/file.txt", extract only the basename
            filename = os.path.basename(prompt_file)
            
            prompt_path = os.path.join(prompt_dir, filename)
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # Combine input_data and context for interpolation
            format_data = {**input_data, **context}
            
            # Interpolate variables safely
            try:
                # Simple strategy: Replace only known keys
                for key, value in format_data.items():
                    if isinstance(value, str):
                        prompt_template = prompt_template.replace(f"{{{key}}}", value)
                    elif isinstance(value, (int, float, bool)):
                        prompt_template = prompt_template.replace(f"{{{key}}}", str(value))
                
                return prompt_template
            except Exception as fmt_e:
                print(f"[ACTION_RUNNER] Warning: Prompt interpolation failed: {fmt_e}")
                return prompt_template
            
        except FileNotFoundError:
            # If specific file not found, use generic prompt
            return self._get_generic_prompt(prompt_file, input_data, context)
        except Exception as e:
            print(f"[ACTION_RUNNER] Error loading prompt {prompt_file}: {e}")
            return self._get_generic_prompt(prompt_file, input_data, context)
    
    def _get_generic_prompt(self, prompt_file: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generic prompt when specific file is not found"""
        
        if "triage" in prompt_file:
            return f"""
You are a data engineering expert. Analyze the following file content and determine:
1. What type of file is this? (SQL, Python, SSIS, etc.)
2. Does it contain data processing logic?
3. Should we use heavy extraction on this file?

File path: {context.get('file_path', 'unknown')}
Content preview: {str(input_data)[:200]}...

Respond with JSON: {{"doc_type": "type", "needs_heavy": boolean, "why": "reason"}}
"""
        
        elif "extract" in prompt_file:
            return f"""
You are a data lineage expert. Extract data assets and relationships from this code.

File: {context.get('file_path', 'unknown')}
Content: {json.dumps(input_data, indent=2)}

Extract:
- Tables/views mentioned
- Files read/written  
- APIs called
- Data transformations

Respond with JSON containing "nodes" and "edges" arrays.
"""
        
        elif "summarize" in prompt_file:
            return f"""
Summarize what this data asset does in one concise paragraph.

File: {context.get('file_path', 'unknown')}
Content: {json.dumps(input_data, indent=2)}

Provide a clear, technical summary suitable for documentation.
"""
        
        else:
            return f"""
Analyze the following data and provide insights.

Input: {json.dumps(input_data, indent=2)}

Respond with JSON containing your analysis.
"""
    
    def _requires_json_validation(self, prompt_file: str) -> bool:
        """Determines if the prompt requires JSON validation"""
        return "extract" in prompt_file or "strict" in prompt_file
    
    def _validate_json_schema(self, data: Dict[str, Any], prompt_file: str) -> Optional[str]:
        """Validates JSON against expected schema"""
        try:
            # Skip validation for deep_dive as it has a different structure
            if "deep_dive" in prompt_file:
                return None, data

            if "extract" in prompt_file:
                # AUTO-FIX: If model returned a list directly (common in VLM fragments)
                if isinstance(data, list):
                    print(f"[ACTION_RUNNER] Auto-mapping list to nodes object for {prompt_file}")
                    data = {"nodes": data, "edges": []}

                # Ensure nodes and edges exist
                if "nodes" not in data:
                    return "Missing 'nodes' field", data
                if "edges" not in data:
                    data["edges"] = [] # Default empty edges
                
                # Validate node structure
                if not isinstance(data["nodes"], list):
                    return "'nodes' must be a list", data
                
                # Validate edge structure
                if not isinstance(data["edges"], list):
                    data["edges"] = []
                
                # Validate required fields in nodes (with AUTO-FIX for 'id' -> 'node_id')
                for i, node in enumerate(data["nodes"]):
                    if not isinstance(node, dict):
                        continue # Skip invalid nodes instead of failing entirely
                    
                    # AUTO-FIX: normalize keys to node_id
                    if node.get("node_id") is None:
                        node["node_id"] = node.get("id") or node.get("entity_id") or node.get("entity_name") or node.get("entity") or node.get("name")
                    
                    if node.get("node_type") is None:
                        node["node_type"] = node.get("entity_type") or node.get("type") or "unknown"

                    if node.get("node_id") is None:
                        node["node_id"] = f"unnamed_{i}"
                    
                    if node.get("name") is None:
                        node["name"] = node.get("node_id")

                # Validate required fields in edges (filter invalid ones)
                valid_edges = []
                invalid_edges_count = 0
                for i, edge in enumerate(data["edges"]):
                    if isinstance(edge, dict) and ("from_node_id" in edge or "source_id" in edge) and ("to_node_id" in edge or "target_id" in edge):
                         # Normalize to from/to if legacy source/target used
                         if "from_node_id" not in edge: edge["from_node_id"] = edge.get("source_id") or edge.get("from")
                         if "to_node_id" not in edge: edge["to_node_id"] = edge.get("target_id") or edge.get("to")
                         valid_edges.append(edge)
                    else:
                         invalid_edges_count += 1
                
                if invalid_edges_count > 0:
                     print(f"[ACTION_RUNNER] Warning: Ignored {invalid_edges_count} invalid edges in {prompt_file}")
                
                data["edges"] = valid_edges # Update list with valid only
            
            return None, data  # Success
            
        except Exception as e:
            return f"Schema validation error: {str(e)}", data
    
    def _clean_json_response(self, text: str) -> str:
        """Cleans LLM response to extract only JSON"""
        text = text.strip()
        
        # Try to find JSON code block
        import re
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
            
        # If no code block, try to find first { or [ and last } or ]
        try:
            start_curly = text.find('{')
            start_square = text.find('[')
            
            # Use the first one found
            if start_curly != -1 and (start_square == -1 or start_curly < start_square):
                start = start_curly
                end = text.rindex('}') + 1
            elif start_square != -1:
                start = start_square
                end = text.rindex(']') + 1
            else:
                return text
                
            json_fragment = text[start:end].strip()
            
            # HEURISTIC: Handle multiple objects not wrapped in a list
            if not json_fragment.startswith('[') and re.search(r'}\s*,?\s*{', json_fragment):
                print(f"[ACTION_RUNNER] Auto-wrapping fragmented JSON")
                json_fragment = "[" + json_fragment + "]"

            # HEURISTIC: Fix unquoted keys (common in some VLM outputs) e.g. { entities: ... }
            # Match word chars followed by colon, not preceded by quote
            # Be careful not to match inside strings. This is a simple heuristic.
            # If it fails, the original syntax error will persist.
            if "Expecting property name enclosed in double quotes" in str(text) or "{" in text:
                 # Regex to find unquoted keys: `\s(\w+):` -> ` "\1":`
                 # Only if we suspect standard unquoted keys.
                 # Let's try fixing common pattern: `{ key: value }`
                 # We only enable this if json loads fails later, but we are in cleaning phase.
                 pass
                 
            return json_fragment
        except ValueError:
            return text

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimates cost in USD based on model and tokens"""
        cost_per_1k = self.cost_estimates.get(model, 0.002)  # Default to 0.002
        return (tokens / 1000) * cost_per_1k
