"""Shared Entity definition for IQua Integration."""
from __future__ import annotations

import logging

import homeassistant.helpers.device_registry as dr
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_ATTRIBUTION, DEFAULT_BRAND, DOMAIN

_LOGGER = logging.getLogger(__name__)


class IQuaEntity(Entity):
    """Base class for IQua Entities."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments
    # pylint: disable=line-too-long
    # Seven is reasonable in this case.

    def __init__(
        self,
        iqua_api,
        coordinator: DataUpdateCoordinator,
        device_data,
        description,
        entries: ConfigEntry,
    ):
        """Initialize the entity."""
        if description:
            self.entity_description = description

        self.iqua_api = iqua_api
        self.coordinator = coordinator
        self.device_data = device_data
        self.entry: ConfigEntry = entries
        self._attr_available = self.coordinator.last_update_success
        self._attr_unique_id = f"{self.entry.unique_id}_{self.entity_description.key}"
        self._attr_name = f"{DEFAULT_BRAND} {self.entity_description.key}"
        self._attr_device_info = DeviceInfo(
            manufacturer=DEFAULT_BRAND,
            via_device=(DOMAIN, self.entry.unique_id),
            connections={(dr.CONNECTION_NETWORK_MAC, self.entry.unique_id)},
            configuration_url="https://github.com/briis/homeassistant-iqua-softener",
        )

    @property
    def extra_state_attributes(self):
        """Return common attributes"""
        return {
            ATTR_ATTRIBUTION: DEFAULT_ATTRIBUTION,
        }

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
