import os
import sys
from pathlib import Path
from dotenv import load_dotenv

root = Path(r"c:\proyectos_dev\discoverIA - gravity")
load_dotenv(root / ".env")

# Mock app path
sys.path.append(str(root / "apps" / "api"))

from app.services.config_manager import ConfigManager
from app.router import get_model_router

def test_switch():
    config_dir = root / "apps" / "api" / "config"
    manager = ConfigManager(str(config_dir))
    
    print("Activating Gemini routing...")
    manager.activate_config("providers/openrouter.yml", "routings/routing-openrouter-gemini.yml")
    
    # Reload router
    router = get_model_router()
    router.reload_config() # Need to check if I added reload_config or if it just re-inits
    
    print(f"Router Provider after switch: {router.provider_name}")
    cfg = router.get_action_config("extract.schema")
    print(f"Model for extract.schema: {cfg.primary.model}")
    print(f"Provider for extract.schema: {cfg.primary.provider}")

if __name__ == "__main__":
    test_switch()
