"""Weatherbit Sensors for Home Assistant."""
from __future__ import annotations
from datetime import datetime, timedelta

import logging
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    VOLUME_FLOW_RATE_LITERS_PER_MINUTE,
    VOLUME_FLOW_RATE_GALLONS_PER_MINUTE,
    IquaSoftenerVolumeUnit,
)
from .entity import IQuaEntity
from .models import IQuaEntryData


@dataclass
class IQuaSensorEntityDescription(SensorEntityDescription):
    """Describes IQua Sensor entity."""


SENSOR_TYPES = IQuaSensorEntityDescription = (
    IQuaSensorEntityDescription(
        key="state",
        name="Status",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IQuaSensorEntityDescription(
        key="days_since_last_regeneration",
        name="Last regeneration",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    IQuaSensorEntityDescription(
        key="out_of_salt_estimated_days",
        name="Out of salt estimated day",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    IQuaSensorEntityDescription(
        key="salt_level_percent",
        name="Salt Level",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-minus",
        native_unit_of_measurement=PERCENTAGE,
    ),
    IQuaSensorEntityDescription(
        key="total_water_available",
        name="Available water",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:water",
    ),
    IQuaSensorEntityDescription(
        key="current_water_flow",
        name="Current Water Flow",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-pump",
    ),
    IQuaSensorEntityDescription(
        key="today_use",
        name="Today water usage",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:water-minus",
    ),
    IQuaSensorEntityDescription(
        key="today_consumption",
        name="Today water consumption",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    IQuaSensorEntityDescription(
        key="average_daily_use",
        name="Water usage daily average",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:waves",
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up sensors for IQua integration."""
    entry_data: IQuaEntryData = hass.data[DOMAIN][entry.entry_id]
    iqua_api = entry_data.iqua_api
    coordinator = entry_data.coordinator
    device_data = entry_data.device_data

    entities = []
    for description in SENSOR_TYPES:
        entities.append(
            IQuaSensor(
                iqua_api,
                coordinator,
                device_data,
                description,
                entry,
            )
        )

        _LOGGER.debug(
            "Adding sensor entity %s",
            description.name,
        )

    async_add_entities(entities)


class IQuaSensor(IQuaEntity, SensorEntity):
    """Implementation if IQua sensor."""

    def __init__(
        self,
        iqua_api,
        coordinator,
        device_data,
        description,
        entries: ConfigEntry,
    ):
        """Initialize an IQua sensor."""
        super().__init__(
            iqua_api,
            coordinator,
            device_data,
            description,
            entries,
        )
        self._attr_name = f"{DOMAIN.capitalize()} {self.entity_description.name}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.key == "state":
            return str(self.device_data.state.value)

        if self.entity_description.key == "days_since_last_regeneration":
            return (
                datetime.now(self.device_data.device_date_time.tzinfo)
                - timedelta(days=self.device_data.days_since_last_regeneration)
            ).replace(hour=0, minute=0, second=0)

        if self.entity_description.key == "out_of_salt_estimated_days":
            return (
                datetime.now(self.device_data.device_date_time.tzinfo)
                + timedelta(days=self.device_data.out_of_salt_estimated_days)
            ).replace(hour=0, minute=0, second=0)

        if self.entity_description.key == "today_consumption":
            return (
                self.device_data.today_use * 0.001
                if self.device_data.volume_unit == IquaSoftenerVolumeUnit.LITERS
                else self.device_data.today_use * 0.0353146667
            )

        return (
            getattr(self.coordinator.data, self.entity_description.key)
            if self.coordinator.data
            else None
        )

    @property
    def icon(self):
        """Return icon for the sensor."""
        if self.entity_description.key == "salt_level_percent":
            if self.device_data.salt_level_percent is not None:
                level_icon = "mdi:signal-off"
                if self.device_data.salt_level_percent > 75:
                    level_icon = "mdi:signal-cellular-3"
                elif self.device_data.salt_level_percent > 50:
                    level_icon = "mdi:signal-cellular-2"
                elif self.device_data.salt_level_percent > 25:
                    level_icon = "mdi:signal-cellular-1"
                elif self.device_data.salt_level_percent > 5:
                    level_icon = "mdi:signal-cellular-outline"
                return level_icon

            return "mdi:signal"

        return self.entity_description.icon

    @property
    def native_unit_of_measurement(self) -> str | None:
        # m3 ft3
        if self.entity_description.key in [
            "today_use",
            "total_water_available",
            "average_daily_use",
        ]:
            return (
                UnitOfVolume.LITERS
                if self.device_data.volume_unit == IquaSoftenerVolumeUnit.LITERS
                else UnitOfVolume.GALLONS
            )

        if self.entity_description.key in ["current_water_flow"]:
            return (
                VOLUME_FLOW_RATE_LITERS_PER_MINUTE
                if self.device_data.volume_unit == IquaSoftenerVolumeUnit.LITERS
                else VOLUME_FLOW_RATE_GALLONS_PER_MINUTE
            )

        if self.entity_description.key in ["today_consumption"]:
            return (
                UnitOfVolume.CUBIC_METERS
                if self.device_data.volume_unit == IquaSoftenerVolumeUnit.LITERS
                else UnitOfVolume.CUBIC_FEET
            )

        return super().native_unit_of_measurement

    @property
    def last_reset(self) -> datetime | None:
        if self.entity_description.key in ["total_water_available"]:
            return datetime.now(self.device_data.device_date_time.tzinfo) - timedelta(
                days=self.device_data.days_since_last_regeneration
            )

        return super().last_reset

    @property
    def extra_state_attributes(self):
        """Return the sensor state attributes."""
        return super().extra_state_attributes
