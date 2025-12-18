"""
Action Runner - Ejecuta acciones de LLM con soporte de fallbacks
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
from ..config import settings

@dataclass
class ActionResult:
    """Resultado de ejecutar una acción"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    # Métricas
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_estimate_usd: Optional[float] = None
    
    # Información de fallback
    fallback_used: bool = False
    models_attempted: Optional[List[str]] = None

class ActionRunner:
    """
    Ejecuta acciones de LLM con soporte de fallbacks automáticos
    """
    
    def __init__(self, logger: Optional[FileProcessingLogger] = None):
        self.router = get_model_router()
        self.logger = logger or FileProcessingLogger()
        self.llm_service = get_llm_adapter()
        
        # Estimaciones de costo por modelo (USD por 1K tokens)
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
        }
    
    def run_action(
        self, 
        action_name: str, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any],
        log_id: Optional[str] = None
    ) -> ActionResult:
        """
        Ejecuta una acción con su configuración primaria
        
        Args:
            action_name: Nombre de la acción (ej: 'triage_fast')
            input_data: Datos de entrada para la acción
            context: Contexto adicional (job_id, file_path, etc.)
            log_id: ID del log de auditoría (opcional)
            
        Returns:
            ActionResult con el resultado de la ejecución
        """
        start_time = time.time()
        
        try:
            # Obtener configuración de la acción
            action_config = self.router.get_action_config(action_name)
            
            # Ejecutar con el modelo primario
            result = self._execute_single_model(
                action_config.primary, 
                input_data, 
                context,
                log_id
            )
            
            # Si falló y hay fallbacks, intentarlos
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
            error_msg = f"Error ejecutando acción '{action_name}': {str(e)}"
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
        """Ejecuta un modelo individual"""
        start_time = time.time()
        
        try:
            # Cargar prompt
            prompt_content = self._load_prompt(model_config.prompt_file, input_data, context)
            
            # Preparar mensajes para LLM
            # Truncar input_data. Groq parece rechazar inputs > 100k tokens incluso en paid.
            # Bajamos a 30k chars (~7.5k tokens) para máxima seguridad.
            input_json = json.dumps(input_data)
            if len(input_json) > 30000: 
                print(f"[ACTION_RUNNER] Truncating input from {len(input_json)} chars to 30000")
                input_json = input_json[:30000] + "... (truncated)"
            
            messages = [
                {"role": "system", "content": prompt_content},
                {"role": "user", "content": input_json}
            ]
            
            # Ejecutar LLM
            llm_result = self.llm_service.call_model(
                model=model_config.model,
                messages=messages,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                provider=settings.LLM_PROVIDER # Usar provider configurado (groq/openrouter)
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            if not llm_result.get("success"):
                return ActionResult(
                    success=False,
                    error_message=llm_result.get("error", "Unknown LLM error"),
                    error_type="llm_error",
                    model_used=model_config.model,
                    latency_ms=latency_ms
                )
            
            # Parsear respuesta
            response_content = llm_result.get("content", "")
            
            # Validar JSON si es necesario
            if self._requires_json_validation(model_config.prompt_file):
                try:
                    # Limpiar respuesta para extraer JSON
                    cleaned_content = self._clean_json_response(response_content)
                    parsed_data = json.loads(cleaned_content)
                    
                    # Validar contra esquema específico
                    validation_error = self._validate_json_schema(
                        parsed_data, 
                        model_config.prompt_file
                    )
                    
                    if validation_error:
                        return ActionResult(
                            success=False,
                            error_message=f"JSON validation failed: {validation_error}",
                            error_type="validation_error",
                            model_used=model_config.model,
                            latency_ms=latency_ms
                        )
                    
                    response_data = parsed_data
                    
                except json.JSONDecodeError as e:
                    return ActionResult(
                        success=False,
                        error_message=f"Invalid JSON response: {str(e)}",
                        error_type="json_parse_error",
                        model_used=model_config.model,
                        latency_ms=latency_ms
                    )
            else:
                response_data = {"content": response_content}
            
            # Calcular costo estimado
            tokens_in = llm_result.get("tokens_in", 0)
            tokens_out = llm_result.get("tokens_out", 0)
            total_tokens = tokens_in + tokens_out
            
            cost_estimate = self._estimate_cost(
                model_config.model, 
                total_tokens
            )
            
            # Actualizar log de auditoría si existe
            if log_id:
                self.logger.update_model_usage(log_id, "openrouter", model_config.model)
                self.logger.update_tokens_and_cost(
                    log_id, tokens_in, tokens_out, cost_estimate, latency_ms
                )
            
            return ActionResult(
                success=True,
                data=response_data,
                model_used=model_config.model,
                latency_ms=latency_ms,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                total_tokens=total_tokens,
                cost_estimate_usd=cost_estimate
            )
            
        except Exception as e:
            error_msg = f"Error ejecutando modelo '{model_config.model}': {str(e)}"
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
        """Ejecuta cadena de fallbacks"""
        
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
                # Marcar que se usó fallback
                result.fallback_used = True
                result.models_attempted = models_attempted
                
                if log_id:
                    self.logger.update_model_usage(
                        log_id, 
                        "openrouter", 
                        result.model_used,
                        fallback_used=True,
                        fallback_chain=models_attempted
                    )
                
                print(f"[ACTION_RUNNER] Fallback successful with {result.model_used}")
                return result
        
        # Todos los fallbacks fallaron
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
        """Carga y prepara el prompt"""
        try:
            # Construir path completo del prompt.
            # __file__ = apps/api/app/actions/__init__.py
            # prompt_dir = apps/api/app/prompts
            prompt_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
            
            # models.yml puede tener "prompts/file.txt", extraemos solo el nombre
            filename = os.path.basename(prompt_file)
            
            prompt_path = os.path.join(prompt_dir, filename)
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # Combinar input_data y context para interpolación
            format_data = {**input_data, **context}
            
            # Interpolar variables de forma segura
            try:
                # Usar format_map para ignorar claves faltantes si es necesario, 
                # pero format() es estándar. Si faltan claves, fallará, lo cual es bueno para debugging.
                # Sin embargo, los prompts pueden tener {json} que no son variables.
                # Mejor hacemos un reemplazo manual de las claves conocidas o escapamos llaves.
                
                # Estrategia simple: Reemplazar solo las claves que sabemos que existen
                for key, value in format_data.items():
                    if isinstance(value, str):
                        prompt_template = prompt_template.replace(f"{{{key}}}", value)
                    elif isinstance(value, (int, float, bool)):
                        prompt_template = prompt_template.replace(f"{{{key}}}", str(value))
                        
                # Para content que puede ser grande o json, a veces se pasa directo en messages,
                # pero aquí el prompt template lo incluye.
                
                return prompt_template
            except Exception as fmt_e:
                print(f"[ACTION_RUNNER] Warning: Prompt interpolation failed: {fmt_e}")
                return prompt_template
            
        except FileNotFoundError:
            # Si no existe el archivo específico, usar prompt genérico
            return self._get_generic_prompt(prompt_file, input_data, context)
        except Exception as e:
            print(f"[ACTION_RUNNER] Error loading prompt {prompt_file}: {e}")
            return self._get_generic_prompt(prompt_file, input_data, context)
    
    def _get_generic_prompt(self, prompt_file: str, input_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Prompt genérico cuando no se encuentra el archivo específico"""
        
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
        """Determina si el prompt requiere validación JSON"""
        return "extract" in prompt_file or "strict" in prompt_file
    
    def _validate_json_schema(self, data: Dict[str, Any], prompt_file: str) -> Optional[str]:
        """Valida el JSON contra el esquema esperado"""
        try:
            if "extract" in prompt_file:
                # Validar que tenga nodes y edges
                if "nodes" not in data:
                    return "Missing 'nodes' field"
                if "edges" not in data:
                    return "Missing 'edges' field"
                
                # Validar estructura de nodos
                if not isinstance(data["nodes"], list):
                    return "'nodes' must be a list"
                
                # Validar estructura de edges
                if not isinstance(data["edges"], list):
                    return "'edges' must be a list"
                
                # Validar campos requeridos en nodos
                for i, node in enumerate(data["nodes"]):
                    if not isinstance(node, dict):
                        return f"Node {i} must be an object"
                    if "node_id" not in node:
                        return f"Node {i} missing 'node_id'"
                    if "node_type" not in node:
                        return f"Node {i} missing 'node_type'"
                
                # Validar campos requeridos en edges
                for i, edge in enumerate(data["edges"]):
                    if not isinstance(edge, dict):
                        return f"Edge {i} must be an object"
                    if "from_node_id" not in edge:
                        return f"Edge {i} missing 'from_node_id'"
                    if "to_node_id" not in edge:
                        return f"Edge {i} missing 'to_node_id'"
            
            return None  # Validación exitosa
            
        except Exception as e:
            return f"Schema validation error: {str(e)}"
    
    def _clean_json_response(self, text: str) -> str:
        """Limpia la respuesta del LLM para extraer solo el JSON"""
        text = text.strip()
        
        # Intentar encontrar bloque de código JSON
        import re
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            return json_match.group(1)
            
        # Si no hay bloque de código, intentar encontrar el primer { y el último }
        # Esto es más agresivo pero necesario si el LLM devuelve texto alrededor
        try:
            start = text.index('{')
            end = text.rindex('}') + 1
            return text[start:end]
        except ValueError:
            return text

    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estima el costo en USD basado en el modelo y tokens"""
        cost_per_1k = self.cost_estimates.get(model, 0.002)  # Default a 0.002 si no conocemos el modelo
        return (tokens / 1000) * cost_per_1k