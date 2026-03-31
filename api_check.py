import requests
import json

url = "http://127.0.0.1:8000/match"
payload = {"filters": {"Diagnosis": "ALL", "Age (Days)": 5000}}
try:
    response = requests.post(url, json=payload, timeout=10)
    data = response.json()
    results = data.get("results", [])
    print(f"Results Count: {len(results)}")
    if results:
        for r in results[:3]:
            print(f"- Trial: {r['trial_id']}, Score: {r['match_score']}")
    else:
        print("NO RESULTS RETURNED")
except Exception as e:
    print(f"ERROR: {e}")
