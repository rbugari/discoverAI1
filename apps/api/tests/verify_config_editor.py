import sys
import os
import yaml
from pathlib import Path

# Fix path to include apps/api
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from app.services.config_manager import ConfigManager

def test_config_manager_editor():
    config_dir = os.path.join(os.getcwd(), "apps", "api", "config")
    manager = ConfigManager(config_dir)
    
    test_file = "providers/openrouter.yml"
    
    print(f"--- Testing Read: {test_file} ---")
    try:
        content = manager.read_config_file(test_file)
        print("SUCCESS: Read content (first 50 chars):")
        print(content[:50] + "...")
    except Exception as e:
        print(f"FAILED: {e}")
        return

    print(f"\n--- Testing Write: {test_file} ---")
    original_content = content
    try:
        # Append a harmless comment
        new_content = original_content + "\n# Verification test comment"
        manager.write_config_file(test_file, new_content)
        
        # Verify it was written
        verified_content = manager.read_config_file(test_file)
        if "# Verification test comment" in verified_content:
            print("SUCCESS: Write persisted.")
        else:
            print("FAILED: Write did not persist.")
            
        # Clean up
        manager.write_config_file(test_file, original_content)
        print("SUCCESS: Cleaned up original content.")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\n--- Testing Security: Path Traversal ---")
    try:
        manager.read_config_file("../../.env")
        print("FAILED: Allowed reading outside root!")
    except PermissionError as e:
        print(f"SUCCESS: Blocked path traversal: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected exception: {e}")

    print("\n--- Testing Security: Restricted Directory ---")
    try:
        manager.read_config_file("active.yml")
        print("FAILED: Allowed reading non-allowed directory file!")
    except PermissionError as e:
        print(f"SUCCESS: Blocked non-allowed directory: {e}")

    print("\n--- Testing YAML Validation ---")
    try:
        manager.write_config_file(test_file, "invalid: yaml: :")
        print("FAILED: Allowed writing invalid YAML!")
    except ValueError as e:
        print(f"SUCCESS: Blocked invalid YAML: {e}")

if __name__ == "__main__":
    test_config_manager_editor()
