import requests
import json
from datetime import datetime

api_key = "tvBILl61L85FBNkEDx4jAXCyWWvfXgSU1kqUDyc0"
headers = {"x-api-key": api_key, "Accept": "application/json"}
station_id = "WP"

# Formateamos la fecha de hoy: YYYY/MM/DD
today = datetime.now().strftime("%Y/%m/%d")

# Este endpoint debería dar TODAS las variables del día para esa estación en 1 sola consulta
url = f"https://api.meteo.cat/xema/v1/estacions/mesurades/{station_id}/{today}"

print(f"Probando endpoint 'Todo en uno' para la fecha: {today}...")

try:
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print("✅ ¡Éxito! Hemos recibido datos.")
        # Mostramos un resumen de qué ha venido
        variables_recibidas = set()
        for lectura in data:
            variables_recibidas.add(lectura.get('codi'))
        print(f"Se han recibido datos de {len(variables_recibidas)} variables distintas en una sola llamada.")
    elif r.status_code == 429:
        print("❌ Error 429: Confirmado, te has quedado sin cuota XEMA para hoy.")
        print("Pero la URL es válida. Si implementamos esto, gastarás 14 veces menos cuota.")
    else:
        print(f"❌ Error inesperado: {r.text}")
except Exception as e:
    print(f"❌ Error: {e}")
