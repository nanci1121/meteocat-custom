"""Weather platform for Meteocat Custom integration."""
import logging
from datetime import datetime, timezone

from homeassistant.components.weather import (
    WeatherEntity,
    Forecast,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfSpeed,
    UnitOfPressure,
    UnitOfPrecipitationDepth,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SKY_STATES
from .coordinator import MeteocatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Meteocat weather entity."""
    coordinator: MeteocatCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MeteocatWeather(coordinator)], update_before_add=True)


class MeteocatWeather(CoordinatorEntity, WeatherEntity):
    """Representation of Meteocat weather."""

    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY
    )
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS

    def __init__(self, coordinator: MeteocatCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_name = f"Meteocat {coordinator.station_name}"
        self._attr_unique_id = f"meteocat_{coordinator.station_id}_weather"

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
    def condition(self) -> str | None:
        """Return the current weather condition from forecast."""
        forecast = self.coordinator.data.get("forecast") if self.coordinator.data else None
        if not forecast:
            return None

        now = datetime.now(timezone.utc)
        sky_code = self._get_closest_forecast_value(forecast, "estatCel", now)

        if sky_code is not None:
            state_info = SKY_STATES.get(int(sky_code))
            return state_info[1] if state_info else None
        return None

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature from XEMA."""
        if not self.coordinator.data:
            return None
        obs = self.coordinator.data.get("observations", {})
        temp_data = obs.get(32)
        if temp_data:
            return temp_data.get("value")
        return None

    @property
    def humidity(self) -> float | None:
        """Return the current humidity."""
        if not self.coordinator.data:
            return None
        obs = self.coordinator.data.get("observations", {})
        hum_data = obs.get(33)
        if hum_data:
            return hum_data.get("value")
        return None

    @property
    def native_pressure(self) -> float | None:
        """Return the current pressure."""
        if not self.coordinator.data:
            return None
        obs = self.coordinator.data.get("observations", {})
        pres_data = obs.get(71)
        if pres_data:
            return pres_data.get("value")
        return None

    @property
    def native_wind_speed(self) -> float | None:
        """Return wind speed (km/h)."""
        if not self.coordinator.data:
            return None
        obs = self.coordinator.data.get("observations", {})
        wind_data = obs.get(46) or obs.get(26)
        if wind_data:
            val = wind_data.get("value")
            if obs.get(46) is None and val is not None:
                return round(val * 3.6, 1)
            return val
        return None

    @property
    def wind_bearing(self) -> float | None:
        """Return wind bearing."""
        if not self.coordinator.data:
            return None
        obs = self.coordinator.data.get("observations", {})
        dir_data = obs.get(47) or obs.get(27)
        if dir_data:
            return dir_data.get("value")
        return None

    # ── FORECAST DAILY (8 días) ──

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return daily forecast (8 days / 1 week)."""
        if not self.coordinator.data:
            return None

        daily_data = self.coordinator.data.get("daily_forecast")
        if not daily_data:
            return None

        forecasts = []
        for day in daily_data.get("dies", []):
            try:
                date_str = day.get("data", "").replace("Z", "")
                variables = day.get("variables", {})

                tmax = variables.get("tmax", {}).get("valor")
                tmin = variables.get("tmin", {}).get("valor")
                precip_chance = variables.get("precipitacio", {}).get("valor")
                sky_code = variables.get("estatCel", {}).get("valor")

                condition = None
                if sky_code is not None:
                    state_info = SKY_STATES.get(int(sky_code))
                    condition = state_info[1] if state_info else None

                forecast = Forecast(
                    datetime=f"{date_str}T00:00:00+00:00",
                    native_temperature=float(tmax) if tmax else None,
                    native_templow=float(tmin) if tmin else None,
                    precipitation_probability=float(precip_chance) if precip_chance else None,
                    condition=condition,
                )
                forecasts.append(forecast)
            except (ValueError, KeyError, TypeError) as err:
                _LOGGER.debug("Error procesando predicción diaria: %s", err)

        return forecasts

    # ── FORECAST HOURLY (72 horas) ──

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return hourly forecast (72 hours)."""
        if not self.coordinator.data:
            return None

        forecast_data = self.coordinator.data.get("forecast")
        if not forecast_data:
            return None

        forecasts = []
        now = datetime.now(timezone.utc)

        for day in forecast_data.get("dies", []):
            variables = day.get("variables", {})

            temp_values = {
                e["data"]: float(e["valor"])
                for e in variables.get("temp", {}).get("valors", [])
            }
            humidity_values = {
                e["data"]: float(e["valor"])
                for e in variables.get("humitat", {}).get("valors", [])
            }
            precip_list = variables.get("precipitacio", {}).get("valor",
                          variables.get("precipitacio", {}).get("valors", []))
            precip_values = {
                e["data"]: float(e["valor"])
                for e in precip_list
            } if isinstance(precip_list, list) else {}
            wind_values = {
                e["data"]: float(e["valor"])
                for e in variables.get("velVent", {}).get("valors", [])
            }
            wind_dir_values = {
                e["data"]: float(e["valor"])
                for e in variables.get("dirVent", {}).get("valors", [])
            }
            sky_values = {
                e["data"]: int(e["valor"])
                for e in variables.get("estatCel", {}).get("valors", [])
            }

            for ts_str in temp_values:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts < now:
                        continue

                    sky_code = sky_values.get(ts_str)
                    condition = None
                    if sky_code:
                        state_info = SKY_STATES.get(sky_code)
                        condition = state_info[1] if state_info else None

                    forecast = Forecast(
                        datetime=ts.isoformat(),
                        native_temperature=temp_values.get(ts_str),
                        humidity=humidity_values.get(ts_str),
                        native_precipitation=precip_values.get(ts_str),
                        native_wind_speed=wind_values.get(ts_str),
                        wind_bearing=wind_dir_values.get(ts_str),
                        condition=condition,
                    )
                    forecasts.append(forecast)
                except (ValueError, KeyError) as err:
                    _LOGGER.debug("Error procesando predicción horaria para %s: %s", ts_str, err)

        return forecasts

    # ── HELPER ──

    def _get_closest_forecast_value(self, forecast_data, var_key, now):
        """Get the forecast value closest to the given time."""
        best_value = None
        best_diff = float("inf")

        for day in forecast_data.get("dies", []):
            variables = day.get("variables", {})
            var_info = variables.get(var_key, {})
            values = var_info.get("valors", var_info.get("valor", []))
            if not isinstance(values, list):
                continue

            for entry in values:
                try:
                    ts = datetime.fromisoformat(entry["data"].replace("Z", "+00:00"))
                    diff = abs((ts - now).total_seconds())
                    if diff < best_diff:
                        best_diff = diff
                        best_value = entry.get("valor")
                except (ValueError, KeyError):
                    continue

        return best_value
