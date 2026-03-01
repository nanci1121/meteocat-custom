# Meteocat Custom - Home Assistant Integration

Integración personalizada para **Home Assistant** que obtiene datos meteorológicos del [Servei Meteorològic de Catalunya (Meteocat)](https://www.meteo.cat/) usando su API oficial.

## ✨ Características

- **Observaciones en tiempo real** (XEMA): Temperatura, humedad, presión, viento, precipitación, irradiación solar, nubosidad
- **Predicción horaria** (72 horas): Temperatura, humedad, precipitación, viento, estado del cielo
- **Predicción diaria/semanal** (8 días): Temperatura máx/mín, probabilidad de lluvia, estado del cielo
- **Monitorización de cuotas**: Sensores que muestran cuántas consultas API te quedan
- **Protección inteligente de cuotas**: No pide datos si estás cerca del límite
- **Caché de predicciones**: Solo pide predicción horaria cada 6h y diaria cada 12h
- **Nunca se bloquea**: Si un endpoint falla, el resto de sensores siguen funcionando

## 📦 Instalación vía HACS

1. Abre **HACS** en tu Home Assistant
2. Ve a **Integraciones**
3. Haz clic en los **3 puntos** (arriba a la derecha) → **Repositorios personalizados**
4. Pega esta URL: `https://github.com/nanci1121/meteocat-custom`
5. Selecciona categoría: **Integración**
6. Haz clic en **Añadir**
7. Busca **"Meteocat Custom"** e **Instala**
8. **Reinicia Home Assistant**

## ⚙️ Configuración

1. Ve a **Ajustes** → **Dispositivos y servicios** → **Añadir integración**
2. Busca **"Meteocat Custom"**
3. Introduce:
   - **API Key**: Tu clave de [Meteocat API](https://apidocs.meteocat.gencat.cat/)
   - **Station ID**: Código de estación XEMA (ej: `WP` para Terrassa)
   - **Town ID**: Código de municipio de 6 dígitos (ej: `082798` para Terrassa)
   - **Nombre**: Nombre descriptivo (ej: `Terrassa`)

## 📊 Sensores Creados

### Observación en Tiempo Real (cada 15 min)
| Sensor | Unidad |
|--------|--------|
| Temperatura | °C |
| Humedad Relativa | % |
| Precipitación | mm |
| Irradiación Solar Global | W/m² |
| Velocidad del Viento | m/s |
| Dirección del Viento | ° |
| Presión Atmosférica | hPa |
| Nubosidad | octas |

### Predicción (horaria + diaria)
| Sensor | Descripción |
|--------|-------------|
| Temperatura Prevista | Hora actual |
| Sensación Térmica | Wind chill |
| Humedad Prevista | % previsto |
| Precipitación Prevista | mm previstos |
| Viento Previsto | km/h |
| Estado del Cielo | Descripción textual |

### Cuotas API
| Sensor | Plan |
|--------|------|
| Cuota XEMA | Consultas restantes |
| Cuota Predicción | Consultas restantes |
| Cuota General | Consultas restantes |

### Entidad Weather
Se crea una entidad `weather.meteocat_*` compatible con la tarjeta de tiempo de HA, con predicción **horaria (72h)** y **diaria (8 días)**.

## 🔑 Obtener API Key

1. Ve a [https://apidocs.meteocat.gencat.cat/](https://apidocs.meteocat.gencat.cat/)
2. Regístrate para obtener tu clave gratuita
3. Planes disponibles: XEMA (750 consultas/mes), Predicción (100 consultas/mes)

## 📄 Licencia

MIT
