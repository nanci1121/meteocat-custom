import requests
import json

api_key = "tvBILl61L85FBNkEDx4jAXCyWWvfXgSU1kqUDyc0"
headers = {"x-api-key": api_key, "Accept": "application/json"}
station_id = "WP"

# Intentamos obtener los metadatos de la estación usando el plan de REFERENCIA (que tienes casi 2000)
# La URL correcta suele ser /referencia/v1/estacions/{id}
url = f"https://api.meteo.cat/referencia/v1/estacions/{station_id}"

try:
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print("✅ Información de la estación obtenida con éxito:")
        print(f"Nombre: {data.get('nom')}")
        print(f"Estado: {data.get('estat')}")
        variables = data.get('variables', [])
        print(f"Sensores disponibles ({len(variables)}):")
        for v in variables:
            print(f" - [{v.get('codi')}] {v.get('nom')}")
    else:
        print(f"❌ Error: {r.text}")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
