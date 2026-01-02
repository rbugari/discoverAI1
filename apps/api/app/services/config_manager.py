import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Handles multi-provider and multi-routing LLM configurations (v3.0).
    """
    def __init__(self, config_root: str):
        self.config_root = Path(config_root)
        self.active_path = self.config_root / "active.yml"
        self._active_config = None
        self._provider_cache = {}
        self._routing_cache = {}

    def get_active_config(self) -> Dict[str, Any]:
        """Loads and returns the current active configuration."""
        if not self.active_path.exists():
            logger.warning(f"Active config not found at {self.active_path}. Using defaults.")
            return {}

        with open(self.active_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get("active", {})

    def get_routing(self, routing_rel_path: str) -> Dict[str, Any]:
        """Loads a specific routing profile."""
        if routing_rel_path in self._routing_cache:
            return self._routing_cache[routing_rel_path]

        full_path = self.config_root / routing_rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"Routing config not found: {full_path}")

        with open(full_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self._routing_cache[routing_rel_path] = data
            return data

    def get_provider(self, provider_rel_path: str) -> Dict[str, Any]:
        """Loads a specific provider profile."""
        if provider_rel_path in self._provider_cache:
            return self._provider_cache[provider_rel_path]

        full_path = self.config_root / provider_rel_path
        if not full_path.exists():
            raise FileNotFoundError(f"Provider config not found: {full_path}")

        with open(full_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self._provider_cache[provider_rel_path] = data
            return data

    def get_action_config(self, action_name: str) -> Dict[str, Any]:
        """
        Synthesizes the configuration for a specific action based on active routing.
        """
        active = self.get_active_config()
        routing_path = active.get("routing")
        if not routing_path:
            return {}

        routing = self.get_routing(routing_path)
        action_cfg = routing.get("actions", {}).get(action_name, {})
        
        # Merge with provider defaults if needed (to be extended)
        provider_path = active.get("provider")
        provider = self.get_provider(provider_path) if provider_path else {}
        
        return {
            **action_cfg,
            "provider_info": provider
        }

    def list_available_configs(self) -> Dict[str, Any]:
        """Lists all providers and enriched routings available in the system."""
        providers = []
        for p in (self.config_root / "providers").glob("*.yml"):
            providers.append(f"providers/{p.name}")
            
        routings = []
        for r in (self.config_root / "routings").glob("*.yml"):
            rel_path = f"routings/{r.name}"
            try:
                # Enforce 1:N mapping by reading the routing's provider
                with open(r, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    routings.append({
                        "path": rel_path,
                        "name": data.get("name", r.name),
                        "provider": data.get("provider", "Unknown")
                    })
            except Exception as e:
                logger.error(f"Failed to parse routing {r}: {e}")
                routings.append({"path": rel_path, "name": r.name, "provider": "Unknown"})
            
        return {
            "providers": providers,
            "routings": routings,
            "active": self.get_active_config()
        }

    def activate_config(self, provider_path: str, routing_path: str):
        """Updates the active configuration pointer."""
        # Validate paths exist
        if not (self.config_root / provider_path).exists():
            raise FileNotFoundError(f"Provider not found: {provider_path}")
        if not (self.config_root / routing_path).exists():
            raise FileNotFoundError(f"Routing not found: {routing_path}")

        new_active = {
            "active": {
                "provider": provider_path,
                "routing": routing_path
            }
        }
        
        with open(self.active_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(new_active, f)
            
        # Clear cache
        self._provider_cache = {}
        self._routing_cache = {}
    def _secure_path(self, rel_path: str) -> Path:
        """Ensures the path is within the config root and allowed subdirs."""
        full_path = (self.config_root / rel_path).resolve()
        root_path = self.config_root.resolve()
        
        # Security: Prevent path traversal
        if not str(full_path).startswith(str(root_path)):
            raise PermissionError("Access denied: Path is outside configuration root.")
            
        # Only allow access to providers/ or routings/ subdirs
        rel_to_root = full_path.relative_to(root_path)
        parts = rel_to_root.parts
        if not parts or parts[0] not in ["providers", "routings"]:
            raise PermissionError("Access denied: Only provider or routing files can be modified.")
            
        return full_path

    def read_config_file(self, rel_path: str) -> str:
        """Reads the raw content of a configuration file."""
        path = self._secure_path(rel_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {rel_path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_config_file(self, rel_path: str, content: str):
        """Writes raw content to a configuration file."""
        path = self._secure_path(rel_path)
        
        # Verify valid YAML before saving
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML content: {str(e)}")
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Clear cache to ensure changes are picked up
        self._provider_cache = {}
        self._routing_cache = {}
