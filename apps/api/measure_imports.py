import time
import sys
import os

print("--- MEASURING IMPORT TIMES ---")

def measure_import(name):
    start = time.time()
    try:
        __import__(name)
        print(f"Import {name}: {time.time() - start:.2f}s")
    except Exception as e:
        print(f"Import {name} FAILED: {e}")

# Adding the apps/api to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

measure_import("app.config")
measure_import("app.services.queue")
measure_import("app.pipeline.orchestrator")
measure_import("app.services.planner")
measure_import("app.worker")

print("--- FINISHED ---")
