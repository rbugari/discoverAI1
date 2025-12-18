"""
Model Router - Sistema de routing de modelos por acción
"""
import os
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ModelConfig:
    """Configuración de modelo para una acción"""
    model: str
    prompt_file: str
    temperature: float = 0.1
    max_tokens: int = 1800
    timeout_ms: int = 60000
    
@dataclass
class ActionConfig:
    """Configuración completa de una acción"""
    name: str
    primary: ModelConfig
    fallbacks: List[ModelConfig]
    
class ModelRouter:
    """
    Router de modelos que lee configuración de config/models.yml
    y proporciona modelos según la acción solicitada
    """
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(Path(__file__).parent.parent.parent, "config", "models.yml")
        
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Carga configuración desde YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Configuración por defecto si no existe el archivo
            return self._get_default_config()
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing models.yml: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            "version": 1,
            "defaults": {
                "temperature": 0.1,
                "max_tokens": 8000, # Gemini tiene gran contexto
                "timeout_ms": 60000
            },
            "actions": {
                "triage_fast": {
                    "model": "google/gemini-2.0-flash-exp",
                    "prompt_file": "prompts/triage_fast.md",
                    "temperature": 0.1,
                    "max_tokens": 1000
                },
                "extract_strict": {
                    "model": "google/gemini-2.0-flash-exp",
                    "prompt_file": "prompts/extract_strict_json.md",
                    "temperature": 0.0,
                    "max_tokens": 8000
                },
                "extract_sql": {
                    "model": "google/gemini-2.0-flash-exp",
                    "prompt_file": "prompts/extract_sql.md",
                    "temperature": 0.0,
                    "max_tokens": 8000
                },
                "extract_python": {
                    "model": "google/gemini-2.0-flash-exp",
                    "prompt_file": "prompts/extract_python.md",
                    "temperature": 0.0,
                    "max_tokens": 8000
                },
                "summarize": {
                    "model": "google/gemini-2.0-flash-exp",
                    "prompt_file": "prompts/summarize.md",
                    "temperature": 0.2,
                    "max_tokens": 2000
                }
            },
            "fallbacks": {
                "extract_strict": [
                    {
                        "model": "meta-llama/llama-3-8b-instruct:free",
                        "prompt_file": "prompts/extract_strict_json.md",
                        "temperature": 0.0,
                        "max_tokens": 2200
                    }
                ],
                "extract_sql": [
                    {
                        "model": "meta-llama/llama-3-8b-instruct:free",
                        "prompt_file": "prompts/extract_sql.md",
                        "temperature": 0.0,
                        "max_tokens": 2200
                    }
                ]
            }
        }
    
    def _validate_config(self):
        """Valida que la configuración tenga la estructura correcta"""
        required_keys = ["actions"]
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required key '{key}' in models.yml")
        
        # Validar que cada acción tenga los campos requeridos
        for action_name, action_config in self.config["actions"].items():
            required_action_keys = ["model", "prompt_file"]
            for key in required_action_keys:
                if key not in action_config:
                    raise ValueError(f"Action '{action_name}' missing required field '{key}'")
    
    def get_action_config(self, action_name: str) -> ActionConfig:
        """
        Obtiene configuración para una acción específica
        
        Args:
            action_name: Nombre de la acción (ej: 'triage_fast', 'extract_strict')
            
        Returns:
            ActionConfig con configuración de la acción
            
        Raises:
            ValueError: Si la acción no existe
        """
        if action_name not in self.config["actions"]:
            raise ValueError(f"Unknown action: '{action_name}'. Available actions: {list(self.config['actions'].keys())}")
        
        action_config = self.config["actions"][action_name]
        defaults = self.config.get("defaults", {})
        
        # Crear ModelConfig primario
        primary_config = ModelConfig(
            model=action_config["model"],
            prompt_file=action_config["prompt_file"],
            temperature=action_config.get("temperature", defaults.get("temperature", 0.1)),
            max_tokens=action_config.get("max_tokens", defaults.get("max_tokens", 1800)),
            timeout_ms=action_config.get("timeout_ms", defaults.get("timeout_ms", 60000))
        )
        
        # Crear lista de fallbacks
        fallbacks = []
        if "fallbacks" in self.config and action_name in self.config["fallbacks"]:
            for fallback_config in self.config["fallbacks"][action_name]:
                fallback_model = ModelConfig(
                    model=fallback_config["model"],
                    prompt_file=fallback_config["prompt_file"],
                    temperature=fallback_config.get("temperature", defaults.get("temperature", 0.1)),
                    max_tokens=fallback_config.get("max_tokens", defaults.get("max_tokens", 1800)),
                    timeout_ms=fallback_config.get("timeout_ms", defaults.get("timeout_ms", 60000))
                )
                fallbacks.append(fallback_model)
        
        return ActionConfig(
            name=action_name,
            primary=primary_config,
            fallbacks=fallbacks
        )
    
    def get_fallback_chain(self, action_name: str) -> List[ModelConfig]:
        """
        Obtiene la cadena completa de modelos para fallback (incluyendo el primario)
        
        Args:
            action_name: Nombre de la acción
            
        Returns:
            Lista de ModelConfig en orden de ejecución (primario + fallbacks)
        """
        action_config = self.get_action_config(action_name)
        return [action_config.primary] + action_config.fallbacks
    
    def get_available_actions(self) -> List[str]:
        """Obtiene lista de acciones disponibles"""
        return list(self.config["actions"].keys())
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de la configuración para debugging"""
        return {
            "version": self.config.get("version", 1),
            "actions": list(self.config["actions"].keys()),
            "fallbacks": list(self.config.get("fallbacks", {}).keys()),
            "defaults": self.config.get("defaults", {})
        }
    
    def reload_config(self):
        """Recarga la configuración desde el archivo"""
        self.config = self._load_config()
        self._validate_config()

# Singleton instance
_router_instance = None

def get_model_router() -> ModelRouter:
    """Obtiene instancia singleton del ModelRouter"""
    global _router_instance
    if _router_instance is None:
        _router_instance = ModelRouter()
    return _router_instance