"""DataUpdateCoordinator for Meteocat Custom integration."""
import asyncio
from datetime import timedelta, datetime
import logging
from typing import Any

import aiohttp
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    API_XEMA_URL,
    API_FORECAST_URL,
    API_FORECAST_DAILY_URL,
    API_QUOTA_URL,
    CONF_API_KEY,
    CONF_STATION_ID,
    CONF_TOWN_ID,
    CONF_STATION_NAME,
    UPDATE_INTERVAL_XEMA,
    XEMA_VARIABLES,
    MIN_QUOTA_XEMA,
    MIN_QUOTA_FORECAST,
)

_LOGGER = logging.getLogger(__name__)


class MeteocatCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching data from Meteocat API."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialize the coordinator."""
        self.api_key = entry.data[CONF_API_KEY]
        self.station_id = entry.data[CONF_STATION_ID]
        self.town_id = entry.data[CONF_TOWN_ID]
        self.station_name = entry.data.get(CONF_STATION_NAME, self.station_id)
        self.headers = {"x-api-key": self.api_key, "Accept": "application/json"}

        # Quota tracking
        self._quotas: dict[str, dict] = {}
        self._last_quota_check: datetime | None = None

        # Forecast cache (to avoid burning tokens)
        self._forecast_data: dict | None = None
        self._last_forecast_fetch: datetime | None = None

        # Daily forecast cache (8 days)
        self._daily_forecast_data: dict | None = None
        self._last_daily_forecast_fetch: datetime | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.station_id}",
            update_interval=timedelta(minutes=UPDATE_INTERVAL_XEMA),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Meteocat API with quota protection."""
        data: dict[str, Any] = {
            "observations": {},
            "forecast": None,
            "daily_forecast": None,
            "quotas": {},
            "station_id": self.station_id,
            "town_id": self.town_id,
            "station_name": self.station_name,
        }

        try:
            async with aiohttp.ClientSession() as session:
                # 1. Check quotas first
                await self._update_quotas(session, data)

                # 2. Fetch XEMA observations (if quota allows)
                await self._fetch_observations(session, data)

                # 3. Fetch hourly forecast (with smart caching)
                await self._fetch_forecast(session, data)

                # 4. Fetch daily/weekly forecast (8 days, with caching)
                await self._fetch_daily_forecast(session, data)

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error de conexión con Meteocat: {err}") from err
        except Exception as err:
            _LOGGER.error("Error inesperado actualizando Meteocat: %s", err)
            raise UpdateFailed(f"Error inesperado: {err}") from err

        return data

    async def _update_quotas(self, session: aiohttp.ClientSession, data: dict) -> None:
        """Fetch current quota usage."""
        try:
            async with session.get(API_QUOTA_URL, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    quota_data = await resp.json()
                    plans = quota_data.get("plans", [])
                    for plan in plans:
                        name = plan.get("nom", "")
                        data["quotas"][name] = {
                            "max": plan.get("maxConsultes", 0),
                            "remaining": plan.get("consultesRestants", 0),
                            "used": plan.get("consultesRealitzades", 0),
                        }
                    self._quotas = data["quotas"]
                    self._last_quota_check = datetime.now()
                    _LOGGER.debug("Cuotas actualizadas: %s", data["quotas"])
                else:
                    _LOGGER.warning("No se pudieron obtener cuotas (HTTP %s), continuando con datos en caché", resp.status)
        except Exception as err:
            _LOGGER.warning("Error obteniendo cuotas: %s. Continuando sin verificación de cuota.", err)

    def _has_quota(self, plan_prefix: str, minimum: int) -> bool:
        """Check if we have enough quota for a given plan."""
        for name, info in self._quotas.items():
            if plan_prefix.lower() in name.lower():
                remaining = info.get("remaining", 0)
                if remaining < minimum:
                    _LOGGER.warning("Cuota baja para %s: %d restantes (mínimo: %d)", name, remaining, minimum)
                    return False
                return True
        # If we can't find the plan, allow (optimistic)
        return True

    async def _fetch_observations(self, session: aiohttp.ClientSession, data: dict) -> None:
        """Fetch latest XEMA observations for all configured variables."""
        if not self._has_quota("XEMA", MIN_QUOTA_XEMA):
            _LOGGER.warning("Cuota XEMA insuficiente, omitiendo observaciones")
            return

        for var_code in XEMA_VARIABLES:
            try:
                url = f"{API_XEMA_URL}/variables/mesurades/{var_code}/ultimes?codiEstacio={self.station_id}"
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        var_data = await resp.json()
                        lectures = var_data.get("lectures", [])
                        if lectures:
                            # Get the most recent reading
                            latest = lectures[-1]
                            data["observations"][var_code] = {
                                "value": latest.get("valor"),
                                "timestamp": latest.get("data"),
                            }
                            _LOGGER.debug(
                                "Variable %d (%s): %s",
                                var_code,
                                XEMA_VARIABLES[var_code][0],
                                latest.get("valor"),
                            )
                    elif resp.status == 403:
                        _LOGGER.debug("Variable %d no disponible para esta estación (403)", var_code)
                    elif resp.status == 429:
                        _LOGGER.warning("Rate limit alcanzado en variable %d, deteniendo", var_code)
                        break
                    else:
                        _LOGGER.debug("Variable %d: HTTP %s", var_code, resp.status)
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout obteniendo variable %d", var_code)
            except Exception as err:
                _LOGGER.debug("Error obteniendo variable %d: %s", var_code, err)

    async def _fetch_forecast(self, session: aiohttp.ClientSession, data: dict) -> None:
        """Fetch municipal hourly forecast with smart caching."""
        now = datetime.now()

        # Only fetch forecast every 6 hours or if we have none
        if self._forecast_data and self._last_forecast_fetch:
            hours_since = (now - self._last_forecast_fetch).total_seconds() / 3600
            if hours_since < 6:
                data["forecast"] = self._forecast_data
                _LOGGER.debug("Usando predicción en caché (hace %.1f horas)", hours_since)
                return

        if not self._has_quota("Predicció", MIN_QUOTA_FORECAST):
            _LOGGER.warning("Cuota de predicción insuficiente, usando caché")
            data["forecast"] = self._forecast_data
            return

        try:
            url = f"{API_FORECAST_URL}/municipalHoraria/{self.town_id}"
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    forecast = await resp.json()
                    self._forecast_data = forecast
                    self._last_forecast_fetch = now
                    data["forecast"] = forecast
                    _LOGGER.info("Predicción municipal actualizada para %s", self.town_id)
                elif resp.status == 429:
                    _LOGGER.warning("Rate limit en predicción, usando caché")
                    data["forecast"] = self._forecast_data
                else:
                    _LOGGER.warning("Error obteniendo predicción: HTTP %s", resp.status)
                    data["forecast"] = self._forecast_data
        except Exception as err:
            _LOGGER.warning("Error obteniendo predicción: %s, usando caché", err)
            data["forecast"] = self._forecast_data

    async def _fetch_daily_forecast(self, session: aiohttp.ClientSession, data: dict) -> None:
        """Fetch daily municipal forecast (8 days) with smart caching."""
        now = datetime.now()

        # Only fetch daily forecast every 12 hours or if we have none
        if self._daily_forecast_data and self._last_daily_forecast_fetch:
            hours_since = (now - self._last_daily_forecast_fetch).total_seconds() / 3600
            if hours_since < 12:
                data["daily_forecast"] = self._daily_forecast_data
                _LOGGER.debug("Usando predicción diaria en caché (hace %.1f horas)", hours_since)
                return

        if not self._has_quota("Predicció", MIN_QUOTA_FORECAST):
            _LOGGER.warning("Cuota de predicción insuficiente para diaria, usando caché")
            data["daily_forecast"] = self._daily_forecast_data
            return

        try:
            url = f"{API_FORECAST_DAILY_URL}/{self.town_id}"
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    forecast = await resp.json()
                    self._daily_forecast_data = forecast
                    self._last_daily_forecast_fetch = now
                    data["daily_forecast"] = forecast
                    _LOGGER.info("Predicción diaria (8 días) actualizada para %s", self.town_id)
                elif resp.status == 429:
                    _LOGGER.warning("Rate limit en predicción diaria, usando caché")
                    data["daily_forecast"] = self._daily_forecast_data
                else:
                    _LOGGER.warning("Error obteniendo predicción diaria: HTTP %s", resp.status)
                    data["daily_forecast"] = self._daily_forecast_data
        except Exception as err:
            _LOGGER.warning("Error obteniendo predicción diaria: %s, usando caché", err)
            data["daily_forecast"] = self._daily_forecast_data
