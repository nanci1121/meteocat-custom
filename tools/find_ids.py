#!/usr/bin/env python3
"""
Meteocat Reference Tool - Find Town ID (6 digits)
--------------------------------------------------
This script helps users find their Town ID for the Meteocat Custom integration.
To find your Station ID (2 letters), visit the official XEMA map.
"""
import requests
import argparse
import sys

def find_town_id(api_key, query):
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }
    
    print(f"\n🔍 Buscando municipio: '{query}'...")
    try:
        # The /referencia/v1/municipis endpoint is public for API users
        r = requests.get("https://api.meteo.cat/referencia/v1/municipis", headers=headers)
        
        if r.status_code == 200:
            towns = r.json()
            matches = [t for t in towns if query.lower() in str(t.get("nom", "")).lower()]
            
            if not matches:
                print("❌ No se encontraron municipios con ese nombre.")
                return

            print(f"✅ Se han encontrado {len(matches)} coincidencias:")
            print("-" * 65)
            print(f"{'Municipio':<35} | {'Town ID':<10} | {'Provincia':<15}")
            print("-" * 65)
            for t in matches:
                nom = t.get("nom", "Desconocido")
                codi = t.get("codi", "N/A")
                prov = t.get("nomProvincia", "N/A")
                print(f"{nom:<35} | {codi:<10} | {prov:<15}")
            
            print("-" * 65)
            print("\n💡 Tip: El 'Town ID' es el código de 6 dígitos que necesitas para configurar")
            print("   la predicción municipal en Home Assistant.")
            print("\n📡 Para encontrar tu 'Station ID' (2 caracteres, ej: WP), visita el mapa:")
            print("   https://cremet.meteocat.gencat.cat/xema/")
            
        elif r.status_code == 403:
            print("❌ Error: Acceso denegado (403). Revisa si tu API Key es correcta.")
        else:
            print(f"❌ Error consultando la API de Meteocat (HTTP {r.status_code})")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Busca el Town ID de cualquier municipio de Cataluña")
    parser.add_argument("query", help="Nombre del municipio (ej: Sabadell)")
    parser.add_argument("--key", help="Tu API Key de Meteocat", required=True)
    
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    find_town_id(args.key, args.query)
