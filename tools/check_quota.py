import requests
import json
import os

api_key = "tvBILl61L85FBNkEDx4jAXCyWWvfXgSU1kqUDyc0"
headers = {"x-api-key": api_key, "Accept": "application/json"}
url = "https://api.meteo.cat/quotes/v1/consum-actual"

try:
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2))
    else:
        print(f"Error: {r.status_code} - {r.text}")
except Exception as e:
    print(f"Error: {e}")
