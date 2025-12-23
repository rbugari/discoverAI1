import os
import sys
from pathlib import Path
from dotenv import load_dotenv

root = Path(r"c:\proyectos_dev\discoverIA - gravity")
load_dotenv(root / ".env")

# Mock app path
sys.path.append(str(root / "apps" / "api"))

from app.config import settings
from app.services.config_manager import ConfigManager

def check_env():
    print(f"Global LLM_PROVIDER: {settings.LLM_PROVIDER}")
    print(f"OPENAI_API_KEY: {'Set' if settings.OPENAI_API_KEY else 'Not Set'}")
    print(f"GROQ_API_KEY: {'Set' if settings.GROQ_API_KEY else 'Not Set'}")
    
    config_dir = root / "apps" / "api" / "config"
    manager = ConfigManager(str(config_dir))
    active = manager.get_active_config()
    print(f"Active Config in active.yml: {active}")
    
    if active:
        action_name = "extract.schema"
        action_cfg = manager.get_action_config(action_name)
        print(f"Config for action '{action_name}': {action_cfg}")

if __name__ == "__main__":
    check_env()
