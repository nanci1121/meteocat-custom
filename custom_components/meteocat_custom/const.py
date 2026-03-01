"""Constants for the Meteocat Custom integration."""

DOMAIN = "meteocat_custom"

# API Base URLs
API_BASE_URL = "https://api.meteo.cat"
API_XEMA_URL = f"{API_BASE_URL}/xema/v1"
API_FORECAST_URL = f"{API_BASE_URL}/pronostic/v1"
API_FORECAST_DAILY_URL = f"{API_BASE_URL}/pronostic/v1/municipal"
API_QUOTA_URL = f"{API_BASE_URL}/quotes/v1/consum-actual"

# Config Keys
CONF_API_KEY = "api_key"
CONF_STATION_ID = "station_id"
CONF_TOWN_ID = "town_id"
CONF_STATION_NAME = "station_name"

# Update intervals (minutes)
UPDATE_INTERVAL_XEMA = 15       # Observations every 15 min
UPDATE_INTERVAL_FORECAST = 360  # Forecast every 6 hours (only updates at 5AM/5PM)
UPDATE_INTERVAL_DAILY = 720     # Daily forecast every 12 hours
QUOTA_CHECK_INTERVAL = 60       # Check quota every hour

# Quota minimums (reserve tokens)
MIN_QUOTA_XEMA = 50
MIN_QUOTA_FORECAST = 10

# XEMA Variable Codes -> (name_es, unit, icon, device_class)
XEMA_VARIABLES = {
    32: ("Temperatura", "°C", "mdi:thermometer", "temperature"),
    33: ("Humedad Relativa", "%", "mdi:water-percent", "humidity"),
    35: ("Precipitación", "mm", "mdi:weather-rainy", "precipitation"),
    36: ("Irradiación Solar Global", "W/m²", "mdi:white-balance-sunny", "irradiance"),
    40: ("Temperatura Mínima", "°C", "mdi:thermometer-chevron-down", "temperature"),
    42: ("Temperatura Máxima", "°C", "mdi:thermometer-chevron-up", "temperature"),
    46: ("Velocidad del viento (escalar)", "km/h", "mdi:weather-windy", None),
    47: ("Dirección del viento (escalar)", "°", "mdi:compass", None),
    26: ("Velocidad del Viento", "m/s", "mdi:weather-windy", "wind_speed"),
    27: ("Dirección del Viento", "°", "mdi:compass", None),
    28: ("Racha de Viento", "m/s", "mdi:weather-windy-variant", None),
    56: ("Racha de Viento (10m)", "m/s", "mdi:weather-windy-variant", None),
    64: ("Nubosidad", "octas", "mdi:cloud", None),
    71: ("Presión Atmosférica", "hPa", "mdi:gauge", "atmospheric_pressure"),
}

# Forecast variable mapping
FORECAST_VARIABLES = {
    "temp": ("Temperatura Prevista", "°C", "mdi:thermometer", "temperature"),
    "tempXafogor": ("Sensación Térmica", "°C", "mdi:thermometer-lines", "temperature"),
    "humitat": ("Humedad Prevista", "%", "mdi:water-percent", "humidity"),
    "precipitacio": ("Precipitación Prevista", "mm", "mdi:weather-pouring", "precipitation"),
    "velVent": ("Viento Previsto", "km/h", "mdi:weather-windy", "wind_speed"),
    "dirVent": ("Dirección Viento Prevista", "°", "mdi:compass", None),
    "estatCel": ("Estado del Cielo", None, "mdi:weather-partly-cloudy", None),
}

# Sky state codes -> text and HA condition
SKY_STATES = {
    1: ("Cel serè", "sunny"),
    2: ("Cel serè nit", "clear-night"),
    3: ("Cel poc ennuvolat", "partlycloudy"),
    4: ("Cel poc ennuvolat nit", "partlycloudy"),
    5: ("Cel mig ennuvolat", "partlycloudy"),
    6: ("Cel mig ennuvolat nit", "partlycloudy"),
    7: ("Cel molt ennuvolat", "cloudy"),
    8: ("Cel molt ennuvolat nit", "cloudy"),
    9: ("Cel cobert", "cloudy"),
    10: ("Cel cobert nit", "cloudy"),
    11: ("Pluja feble", "rainy"),
    12: ("Pluja feble nit", "rainy"),
    13: ("Pluja moderada", "rainy"),
    14: ("Pluja moderada nit", "rainy"),
    15: ("Pluja forta", "pouring"),
    16: ("Pluja forta nit", "pouring"),
    17: ("Tempesta", "lightning-rainy"),
    18: ("Tempesta nit", "lightning-rainy"),
    19: ("Neu", "snowy"),
    20: ("Intervals de núvols", "partlycloudy"),
    21: ("Intervals de núvols nit", "partlycloudy"),
    22: ("Intervals de núvols amb pluja", "rainy"),
    23: ("Intervals de núvols amb pluja nit", "rainy"),
    24: ("Intervals de núvols amb tempesta", "lightning-rainy"),
    25: ("Boira", "fog"),
    26: ("Boirina", "fog"),
}
