"""Support for the IQua Water Softener."""
from __future__ import annotations

import logging
from datetime import timedelta

import homeassistant.helpers.device_registry as dr
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
)

from iqua_softener import (
    IquaSoftener,
    IquaSoftenerData,
    IquaSoftenerException,
)

from .const import (
    DOMAIN,
    CONF_DEVICE_SERIAL_NUMBER,
    CONF_INTERVAL_SENSORS,
    CONFIG_OPTIONS,
    DEFAULT_BRAND,
    DEFAULT_INTERVAL_SENSORS,
    IQUA_PLATFORMS,
)
from .models import IQuaEntryData

_LOGGER = logging.getLogger(__name__)


@callback
def _async_import_options_from_data_if_missing(hass: HomeAssistant, entry: ConfigEntry):
    options = dict(entry.options)
    data = dict(entry.data)
    modified = False
    for importable_option in CONFIG_OPTIONS:
        if importable_option not in entry.options and importable_option in entry.data:
            options[importable_option] = entry.data[importable_option]
            del data[importable_option]
            modified = True

    if modified:
        hass.config_entries.async_update_entry(entry, data=data, options=options)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the WeatherFlow config entries."""
    _async_import_options_from_data_if_missing(hass, entry)

    _LOGGER.debug("USER: %s", entry.data[CONF_USERNAME])
    iqua_api = IquaSoftener(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_DEVICE_SERIAL_NUMBER],
    )

    try:
        device_data: IquaSoftenerData = await hass.async_add_executor_job(
            iqua_api.get_data
        )

    except IquaSoftenerException as notreadyerror:
        _LOGGER.debug("Something went wrong when trying to retrieve data.")
        raise ConfigEntryNotReady from notreadyerror

    if entry.unique_id is None:
        hass.config_entries.async_update_entry(
            entry, unique_id=CONF_DEVICE_SERIAL_NUMBER
        )

    async def async_update_data():
        """Obtain the latest data from WeatherFlow."""
        try:
            data: IquaSoftenerData = await hass.async_add_executor_job(
                iqua_api.get_data
            )
            return data

        except IquaSoftenerException as err:
            raise UpdateFailed(f"Error while retreiving data: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(
            seconds=entry.options.get(CONF_INTERVAL_SENSORS, DEFAULT_INTERVAL_SENSORS)
        ),
    )
    await coordinator.async_config_entry_first_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = IQuaEntryData(
        coordinator=coordinator,
        iqua_api=iqua_api,
        device_data=device_data,
    )

    await _async_get_or_create_nvr_device_in_registry(hass, entry, device_data)
    await hass.config_entries.async_forward_entry_setups(entry, IQUA_PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def _async_get_or_create_nvr_device_in_registry(
    hass: HomeAssistant, entry: ConfigEntry, device_data: IquaSoftenerData
) -> None:
    device_registry = dr.async_get(hass)

    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, entry.unique_id)},
        identifiers={(DOMAIN, entry.data[CONF_DEVICE_SERIAL_NUMBER])},
        manufacturer=DEFAULT_BRAND,
        name=f"{DEFAULT_BRAND} ({entry.data[CONF_DEVICE_SERIAL_NUMBER]})",
        model=device_data.model,
        sw_version=device_data.software_version,
    )


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry):
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload IQua entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, IQUA_PLATFORMS)
    return unload_ok
