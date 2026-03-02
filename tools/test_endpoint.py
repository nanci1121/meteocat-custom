import requests
import json

api_key = "tvBILl61L85FBNkEDx4jAXCyWWvfXgSU1kqUDyc0"
headers = {"x-api-key": api_key, "Accept": "application/json"}
station_id = "WP" # Example station from find_ids.py tip

# Test a potential "all variables" endpoint
url = f"https://api.meteo.cat/xema/v1/estacions/{station_id}/mesurades/ultimes"

try:
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2)[:1000] + "...")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Error: {e}")
