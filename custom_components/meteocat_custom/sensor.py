"""Sensor platform for Meteocat Custom integration."""
import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, XEMA_VARIABLES, FORECAST_VARIABLES, SKY_STATES
from .coordinator import MeteocatCoordinator

_LOGGER = logging.getLogger(__name__)

# Map string device classes to HA SensorDeviceClass
DEVICE_CLASS_MAP = {
    "temperature": SensorDeviceClass.TEMPERATURE,
    "humidity": SensorDeviceClass.HUMIDITY,
    "precipitation": SensorDeviceClass.PRECIPITATION,
    "irradiance": SensorDeviceClass.IRRADIANCE,
    "wind_speed": SensorDeviceClass.WIND_SPEED,
    "atmospheric_pressure": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Meteocat sensors from a config entry."""
    coordinator: MeteocatCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # --- XEMA Observation Sensors ---
    for var_code, (name, unit, icon, device_class_str) in XEMA_VARIABLES.items():
        entities.append(
            MeteocatObservationSensor(
                coordinator=coordinator,
                var_code=var_code,
                name=name,
                unit=unit,
                icon_str=icon,
                device_class_str=device_class_str,
            )
        )

    # --- Forecast Sensors (current hour) ---
    for var_key, (name, unit, icon, device_class_str) in FORECAST_VARIABLES.items():
        entities.append(
            MeteocatForecastSensor(
                coordinator=coordinator,
                var_key=var_key,
                name=name,
                unit=unit,
                icon_str=icon,
                device_class_str=device_class_str,
            )
        )

    # --- Quota Sensors ---
    entities.append(MeteocatQuotaSensor(coordinator, "XEMA"))
    entities.append(MeteocatQuotaSensor(coordinator, "Predicció"))
    entities.append(MeteocatQuotaSensor(coordinator, "Quota"))

    async_add_entities(entities, update_before_add=True)


class MeteocatObservationSensor(CoordinatorEntity, SensorEntity):
    """Sensor for real-time XEMA observations."""

    def __init__(self, coordinator, var_code, name, unit, icon_str, device_class_str):
        """Initialize."""
        super().__init__(coordinator)
        self._var_code = var_code
        self._attr_name = f"Meteocat {coordinator.station_name} {name}"
        self._attr_unique_id = f"meteocat_{coordinator.station_id}_obs_{var_code}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon_str
        self._attr_state_class = SensorStateClass.MEASUREMENT

        if device_class_str and device_class_str in DEVICE_CLASS_MAP:
            self._attr_device_class = DEVICE_CLASS_MAP[device_class_str]

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.station_id)},
            "name": f"Meteocat {self.coordinator.station_name}",
            "manufacturer": "Servei Meteorològic de Catalunya",
            "model": f"Estació {self.coordinator.station_id}",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self):
        """Return the sensor value."""
        if not self.coordinator.data:
            return None
        obs = self.coordinator.data.get("observations", {})
        var_data = obs.get(self._var_code)
        if var_data:
            return var_data.get("value")
        return None

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        if not self.coordinator.data:
            return {}
        obs = self.coordinator.data.get("observations", {})
        var_data = obs.get(self._var_code)
        if var_data:
            return {"timestamp": var_data.get("timestamp")}
        return {}


class MeteocatForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor for municipal forecast data."""

    def __init__(self, coordinator, var_key, name, unit, icon_str, device_class_str):
        """Initialize."""
        super().__init__(coordinator)
        self._var_key = var_key
        self._attr_name = f"Meteocat {coordinator.station_name} {name}"
        self._attr_unique_id = f"meteocat_{coordinator.town_id}_forecast_{var_key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon_str

        if device_class_str and device_class_str in DEVICE_CLASS_MAP:
            self._attr_device_class = DEVICE_CLASS_MAP[device_class_str]
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.station_id)},
            "name": f"Meteocat {self.coordinator.station_name}",
            "manufacturer": "Servei Meteorològic de Catalunya",
            "model": f"Estació {self.coordinator.station_id}",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self):
        """Return the current hour forecast value."""
        forecast = self._get_current_forecast()
        if forecast is None:
            return None

        if self._var_key == "estatCel":
            # Sky state: return text description
            val = forecast
            if isinstance(val, (int, float)):
                state_info = SKY_STATES.get(int(val))
                return state_info[0] if state_info else str(val)
            return val

        return forecast

    @property
    def extra_state_attributes(self):
        """Return extra attributes with next hours forecast."""
        if not self.coordinator.data or not self.coordinator.data.get("forecast"):
            return {}

        attrs = {}
        forecast_data = self.coordinator.data["forecast"]
        days = forecast_data.get("dies", [])

        # Build next 12 hours preview
        upcoming = []
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        for day in days:
            variables = day.get("variables", {})
            var_info = variables.get(self._var_key, {})

            # Handle different key names (valors vs valor)
            values = var_info.get("valors", var_info.get("valor", []))
            if not isinstance(values, list):
                continue

            for entry in values:
                try:
                    ts = datetime.fromisoformat(entry["data"].replace("Z", "+00:00"))
                    if ts >= now:
                        val = entry.get("valor", "")
                        upcoming.append(f"{ts.strftime('%H:%M')}: {val}")
                        if len(upcoming) >= 12:
                            break
                except (ValueError, KeyError):
                    continue
            if len(upcoming) >= 12:
                break

        if upcoming:
            attrs["próximas_horas"] = " | ".join(upcoming)

        return attrs

    def _get_current_forecast(self):
        """Get the forecast value closest to the current hour."""
        if not self.coordinator.data or not self.coordinator.data.get("forecast"):
            return None

        forecast_data = self.coordinator.data["forecast"]
        days = forecast_data.get("dies", [])

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        best_value = None
        best_diff = float("inf")

        for day in days:
            variables = day.get("variables", {})
            var_info = variables.get(self._var_key, {})

            values = var_info.get("valors", var_info.get("valor", []))
            if not isinstance(values, list):
                continue

            for entry in values:
                try:
                    ts = datetime.fromisoformat(entry["data"].replace("Z", "+00:00"))
                    diff = abs((ts - now).total_seconds())
                    if diff < best_diff:
                        best_diff = diff
                        best_value = entry.get("valor", "")
                except (ValueError, KeyError):
                    continue

        if best_value is not None:
            try:
                return float(best_value)
            except (ValueError, TypeError):
                return best_value
        return None


class MeteocatQuotaSensor(CoordinatorEntity, SensorEntity):
    """Sensor to track API quota usage."""

    def __init__(self, coordinator, plan_name):
        """Initialize."""
        super().__init__(coordinator)
        self._plan_name = plan_name
        self._attr_name = f"Meteocat Cuota {plan_name}"
        self._attr_unique_id = f"meteocat_{coordinator.station_id}_quota_{plan_name.lower().replace(' ', '_')}"
        self._attr_icon = "mdi:counter"
        self._attr_native_unit_of_measurement = "consultas"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.station_id)},
            "name": f"Meteocat {self.coordinator.station_name}",
            "manufacturer": "Servei Meteorològic de Catalunya",
            "model": f"Estació {self.coordinator.station_id}",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self):
        """Return remaining quota."""
        if not self.coordinator.data:
            return None
        quotas = self.coordinator.data.get("quotas", {})
        for name, info in quotas.items():
            if self._plan_name.lower() in name.lower():
                return info.get("remaining")
        return None

    @property
    def extra_state_attributes(self):
        """Return quota details."""
        if not self.coordinator.data:
            return {}
        quotas = self.coordinator.data.get("quotas", {})
        for name, info in quotas.items():
            if self._plan_name.lower() in name.lower():
                return {
                    "plan": name,
                    "max_consultas": info.get("max"),
                    "usadas": info.get("used"),
                    "restantes": info.get("remaining"),
                }
        return {}
