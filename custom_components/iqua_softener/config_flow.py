"""Config flow to configure IQua Water Softener component."""
from __future__ import annotations

import logging
from homeassistant import config_entries

from homeassistant.core import callback
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
)
import voluptuous as vol

from iqua_softener import (
    IquaSoftener,
    IquaSoftenerException,
)
from .const import (
    DOMAIN,
    CONF_DEVICE_SERIAL_NUMBER,
    CONF_INTERVAL_SENSORS,
    DEFAULT_INTERVAL_SENSORS,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA_USER = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_DEVICE_SERIAL_NUMBER): str,
        vol.Optional(CONF_INTERVAL_SENSORS, default=DEFAULT_INTERVAL_SENSORS): int,
    }
)


class IquaSoftenerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle and IQua config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if user_input is None:
            return await self._show_setup_form(user_input)

        errors = {}

        iqua_api = IquaSoftener(
            user_input[CONF_USERNAME],
            user_input[CONF_PASSWORD],
            user_input[CONF_DEVICE_SERIAL_NUMBER],
        )

        try:
            await self.hass.async_add_executor_job(iqua_api.get_data)

        except IquaSoftenerException as err:
            _LOGGER.debug(err)
            errors["base"] = "connection_error"
            return await self._show_setup_form(errors)

        unique_id = f"{DOMAIN}_{user_input[CONF_DEVICE_SERIAL_NUMBER]}"

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"IQua {user_input[CONF_DEVICE_SERIAL_NUMBER]}",
            data={
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_DEVICE_SERIAL_NUMBER: user_input[CONF_DEVICE_SERIAL_NUMBER],
            },
            options={
                CONF_INTERVAL_SENSORS: DEFAULT_INTERVAL_SENSORS,
            },
        )

    async def _show_setup_form(self, errors=None):
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_DEVICE_SERIAL_NUMBER): str,
                }
            ),
            errors=errors or {},
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

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
                    vol.Optional(
                        CONF_INTERVAL_SENSORS,
                        default=self.config_entry.options.get(
                            CONF_INTERVAL_SENSORS, DEFAULT_INTERVAL_SENSORS
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=DEFAULT_INTERVAL_SENSORS, max=3600),
                    ),
                }
            ),
        )
