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
    provider: str = "openrouter" # Added to support multiple providers
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
    Router de modelos dinámico (v3.0).
    Lee la configuración activa vía ConfigManager o cae a models.yml
    """
    
    def __init__(self, config_path: str = None):
        from ..services.config_manager import ConfigManager
        
        self.config_root = os.path.join(Path(__file__).parent.parent.parent, "config")
        self.config_manager = ConfigManager(self.config_root)
        
        # Intentar cargar config activa
        try:
            # Check for Economy Mode override via ENV
            economy_mode = os.getenv("LLM_ECONOMY_MODE", "false").lower() == "true"
            
            if economy_mode:
                routing_path = "routings/routing-economy-groq.yml"
                self.config = self.config_manager.get_routing(routing_path)
                # Ensure we use groq provider for economy mode
                self.provider_name = "groq"
                print(f"[ROUTER] ⚡ ECONOMY MODE ACTIVE: Overriding to {routing_path} (Provider: {self.provider_name})")
            else:
                active = self.config_manager.get_active_config()
                if active and active.get("routing"):
                    routing_path = active.get("routing")
                    self.config = self.config_manager.get_routing(routing_path)
                    self.provider_name = self._extract_provider_name(active.get("provider"))
                    print(f"[ROUTER] Loaded v3 routing: {routing_path} (Provider: {self.provider_name})")
                else:
                    raise Exception("No active v3 config")
                    
            print(f"[ROUTER] Actions in YAML: {list(self.config.get('actions', {}).keys())}")
        except Exception as e:
            print(f"[ROUTER] Fallback to legacy models.yml: {e}")
            self.provider_name = "openrouter" # Legacy default
            if config_path is None:
                config_path = os.path.join(self.config_root, "models.yml")
            self.config_path = config_path
            self.config = self._load_config()
            
        self._validate_config()

    def _extract_provider_name(self, provider_path: str) -> str:
        if not provider_path: return "openrouter"
        if "groq" in provider_path.lower(): return "groq"
        if "openai" in provider_path.lower(): return "openai"
        return "openrouter"
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga configuración desde YAML (Legacy)"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._get_default_config()
        except Exception:
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        # Resumen simplificado si falla todo
        return {"actions": {}}

    def _validate_config(self):
        if "actions" not in self.config:
            self.config["actions"] = {}

    def get_action_config(self, action_name: str) -> ActionConfig:
        if action_name not in self.config["actions"]:
            # Fallback dinámico si la acción no está en el YAML pero queremos ejecutarla
            print(f"[ROUTER] Warning: Action '{action_name}' not in config. Using defaults.")
            # Standard model IDs for fallback
            default_model = "google/gemini-3-flash-preview" if self.provider_name == "openrouter" else "llama-3.3-70b-versatile"
            action_cfg = {
                "model": default_model,
                "prompt_file": f"prompts/{action_name.replace('.', '_')}.md" # Map dot to underscore for prompt files
            }
        else:
            action_cfg = self.config["actions"][action_name]
            # Si es un string (formato ultra simplificado v3), convertir a dict
            if isinstance(action_cfg, str):
                action_cfg = {"model": action_cfg}

        defaults = self.config.get("defaults", {})
        
        # Crear ModelConfig primario
        primary_config = ModelConfig(
            model=action_cfg.get("model", "unknown"),
            prompt_file=action_cfg.get("prompt_file", f"prompts/{action_name}.md"),
            provider=action_cfg.get("provider", self.provider_name), # Action level override
            temperature=action_cfg.get("temperature", defaults.get("temperature", 0.1)),
            max_tokens=action_cfg.get("max_tokens", defaults.get("max_tokens", 4000)),
            timeout_ms=action_cfg.get("timeout_ms", defaults.get("timeout_ms", 60000))
        )
        
        print(f"[ROUTER] Resolved {action_name} -> {primary_config.model} (Provider: {primary_config.provider})")
        
        # Fallbacks
        fallbacks = []
        if "fallbacks" in self.config and action_name in self.config["fallbacks"]:
            for fb in self.config["fallbacks"][action_name]:
                fallbacks.append(ModelConfig(
                    model=fb["model"],
                    prompt_file=fb.get("prompt_file", primary_config.prompt_file),
                    provider=self.provider_name,
                    temperature=fb.get("temperature", primary_config.temperature),
                    max_tokens=fb.get("max_tokens", primary_config.max_tokens)
                ))
        
        return ActionConfig(name=action_name, primary=primary_config, fallbacks=fallbacks)
    
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