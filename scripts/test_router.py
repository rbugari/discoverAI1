import os
import sys
from pathlib import Path
from dotenv import load_dotenv

root = Path(r"c:\proyectos_dev\discoverIA - gravity")
load_dotenv(root / ".env")

# Mock app path
sys.path.append(str(root / "apps" / "api"))

from app.router import get_model_router

def test_router():
    router = get_model_router()
    print(f"Router Provider: {router.provider_name}")
    
    action = "extract.schema"
    cfg = router.get_action_config(action)
    print(f"Config for '{action}':")
    print(f"  Model: {cfg.primary.model}")
    print(f"  Provider: {cfg.primary.provider}")
    print(f"  Prompt: {cfg.primary.prompt_file}")

if __name__ == "__main__":
    test_router()
