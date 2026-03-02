import requests
import json

api_key = "tvBILl61L85FBNkEDx4jAXCyWWvfXgSU1kqUDyc0"
headers = {"x-api-key": api_key, "Accept": "application/json"}

# Probamos a listar estaciones para ver el formato
url = "https://api.meteo.cat/referencia/v1/estacions"

try:
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        estaciones = r.json()
        print(f"✅ Se han encontrado {len(estaciones)} estaciones.")
        # Buscamos la tuya (WP)
        tu_estacion = next((e for e in estaciones if e.get('codi') == 'WP'), None)
        if tu_estacion:
            print("Detalles de tu estación (WP):")
            print(json.dumps(tu_estacion, indent=2))
        else:
            print("No he encontrado la estación 'WP' en la lista general.")
    else:
        print(f"❌ Error: {r.text}")
except Exception as e:
    print(f"❌ Error: {e}")
