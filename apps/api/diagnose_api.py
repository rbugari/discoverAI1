import requests
import json
import time

base_url = "http://localhost:8000"
solution_id = "7021ac4b-921d-402f-bc21-1c63701b8180"

endpoints = [
    "/health",
    f"/solutions/{solution_id}",
    f"/solutions/{solution_id}/stats",
    f"/solutions/{solution_id}/active-plan",
    f"/solutions/{solution_id}/audit/history"
]

print(f"=== DIAGNOSING API RESPONSIVENESS ===")

for ep in endpoints:
    url = base_url + ep
    print(f"\nFETCHING: {url}")
    try:
        start_time = time.time()
        res = requests.get(url, timeout=10)
        end_time = time.time()
        print(f"STATUS: {res.status_code}")
        print(f"TIME: {end_time - start_time:.2f}s")
        if res.status_code == 200:
            data = res.json()
            # print(f"DATA: {json.dumps(data, indent=2)[:200]}...")
            print(f"SUCCESS: Data received ({len(str(data))} chars)")
        else:
            print(f"ERROR: {res.text}")
    except Exception as e:
        print(f"FAILED: {str(e)}")

print("\n=== WEB SERVER CHECK (PORT 3000) ===")
try:
    res = requests.get("http://localhost:3000", timeout=5)
    print(f"FRONTEND STATUS: {res.status_code}")
except Exception as e:
    print(f"FRONTEND FAILED: {str(e)}")
