import requests
import json

api_key = "tvBILl61L85FBNkEDx4jAXCyWWvfXgSU1kqUDyc0"
headers = {"x-api-key": api_key, "Accept": "application/json"}
station_id = "WP"

# Metadata endpoint
url = f"https://api.meteo.cat/xema/v1/estacions/{station_id}/metadades"

try:
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        variables = data.get("variables", [])
        print(f"Station {station_id} has {len(variables)} variables:")
        for v in variables:
            print(f"- {v.get('codi')}: {v.get('nom')}")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Error: {e}")
