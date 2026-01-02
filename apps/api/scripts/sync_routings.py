import yaml
import os

routing_dir = r"c:\proyectos_dev\discoverIA - gravity\apps\api\config\routings"
files = ["DeepSeek.yml", "routing-economy-groq.yml", "routing-groq-fast.yml", "routing-openrouter-gemini.yml"]

default_model = "allenai/olmo-3.1-32b-think:free"

required_actions = [
    "planner.classifier",
    "extract.schema",
    "extract.lineage.package",
    "extract.lineage.sql",
    "extract.python",
    "extract.strict",
    "extract.deep_dive",
    "summarize.asset",
    "qa.chat",
    "generate.dbt",
    "reasoning.architect",
    "expert.report",
    "action.analyze_iteration"
]

def sync_routings():
    for filename in files:
        filepath = os.path.join(routing_dir, filename)
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        
        provider = data.get('provider', '')
        # Determine fallback model based on provider
        if 'groq' in provider.lower():
            fallback_model = "llama-3.3-70b-versatile" # More powerful for reasoning
            fallback_fast = "llama-3.1-8b-instant"   # For simple extraction
        else:
            fallback_model = "allenai/olmo-3.1-32b-think:free"
            fallback_fast = "allenai/olmo-3.1-32b-think:free"

        if 'actions' not in data:
            data['actions'] = {}
            
        modified = False
        for action in required_actions:
            # If the model is from a different provider, treat it as missing/wrong
            current_model = data['actions'].get(action, {}).get('model', '')
            is_wrong_provider = False
            if 'groq' in provider.lower() and 'allenai' in current_model:
                is_wrong_provider = True
            
            if action not in data['actions'] or is_wrong_provider:
                print(f"Fixing/Adding action {action} in {filename} (Provider: {provider})")
                
                target_model = fallback_fast if "extract" in action or "planner" in action else fallback_model
                
                data['actions'][action] = {
                    "model": target_model,
                    "temperature": 0.1 if "extract" in action or "planner" in action else 0.3,
                    "max_tokens": 4096 if "extract" in action else 2000
                }
                modified = True
        
        if modified:
            with open(filepath, 'w') as f:
                yaml.dump(data, f, sort_keys=False)
            print(f"Updated {filename}")
        else:
            print(f"No changes needed for {filename}")

if __name__ == "__main__":
    sync_routings()
