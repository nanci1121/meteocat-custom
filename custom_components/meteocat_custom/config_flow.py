"""Config flow for Meteocat Custom integration."""
import logging
import voluptuous as vol
import aiohttp
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_API_KEY, CONF_STATION_ID, CONF_TOWN_ID, CONF_STATION_NAME, API_QUOTA_URL

_LOGGER = logging.getLogger(__name__)


class MeteocatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meteocat Custom."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step: user provides API key, station, and town."""
        errors = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            valid, client_name = await self._test_credentials(api_key)

            if valid:
                # Prevent duplicate entries
                await self.async_set_unique_id(
                    f"meteocat_{user_input[CONF_STATION_ID]}_{user_input[CONF_TOWN_ID]}"
                )
                self._abort_if_unique_id_configured()

                station_name = user_input.get(CONF_STATION_NAME, user_input[CONF_STATION_ID])
                return self.async_create_entry(
                    title=f"Meteocat {station_name}",
                    data={
                        CONF_API_KEY: api_key,
                        CONF_STATION_ID: user_input[CONF_STATION_ID],
                        CONF_TOWN_ID: user_input[CONF_TOWN_ID],
                        CONF_STATION_NAME: station_name,
                    },
                )
            else:
                errors["base"] = "auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_STATION_ID, default="WP"): str,
                    vol.Required(CONF_TOWN_ID, default="082798"): str,
                    vol.Optional(CONF_STATION_NAME, default="Terrassa"): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "docs_url": "https://apidocs.meteocat.gencat.cat/documentacio/",
            },
        )

    async def _test_credentials(self, api_key: str) -> tuple[bool, str]:
        """Test the API key by calling the quota endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"x-api-key": api_key}
                async with session.get(API_QUOTA_URL, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        client_name = data.get("client", {}).get("nom", "Unknown")
                        _LOGGER.info("Meteocat API key validated for client: %s", client_name)
                        return True, client_name
                    else:
                        _LOGGER.error("Meteocat API key validation failed: %s", response.status)
                        return False, ""
        except Exception as err:
            _LOGGER.error("Error testing Meteocat credentials: %s", err)
            return False, ""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return MeteocatOptionsFlowHandler(config_entry)


class MeteocatOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Meteocat Custom."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_API_KEY,
                        default=self.config_entry.data.get(CONF_API_KEY, ""),
                    ): str,
                }
            ),
        )
