import os
import sys
from pathlib import Path

# Add apps/api to path
root = Path(r"c:\proyectos_dev\discoverIA - gravity")
sys.path.append(str(root / "apps" / "api"))

try:
    from app.services.config_manager import ConfigManager
    
    config_dir = root / "apps" / "api" / "config"
    print(f"Testing ConfigManager with dir: {config_dir}")
    print(f"Dir exists: {config_dir.exists()}")
    
    manager = ConfigManager(str(config_dir))
    configs = manager.list_available_configs()
    print("Configs loaded successfully:")
    print(configs)
except Exception as e:
    import traceback
    print("Error loading configs:")
    traceback.print_exc()
