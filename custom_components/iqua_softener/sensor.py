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
from homeassistant.const import PERCENTAGE, VOLUME_LITERS, VOLUME_GALLONS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType

from iqua_softener import (
    IquaSoftener,
    IquaSoftenerData,
    IquaSoftenerVolumeUnit,
    IquaSoftenerException,
)

from .const import (
    DOMAIN,
    VOLUME_FLOW_RATE_LITERS_PER_MINUTE,
    VOLUME_FLOW_RATE_GALLONS_PER_MINUTE,
)
from .entity import IQuaEntity
from .models import IQuaEntryData


@dataclass
class IQuaSensorEntityDescription(SensorEntityDescription):
    """Describes IQua Sensor entity."""


SENSOR_TYPES = IQuaSensorEntityDescription = (
    IQuaSensorEntityDescription(
        key="state",
        name="Online",
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
        key="today_use",
        name="Today water usage",
        state_class=SensorStateClass.TOTAL,
        icon="mdi:water-minus",
        native_unit_of_measurement=VOLUME_LITERS,
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
        return (
            getattr(self.coordinator.data, self.entity_description.key)
            if self.coordinator.data
            else None
        )

    @property
    def icon(self):
        """Return icon for the sensor."""

        return self.entity_description.icon

    @property
    def native_unit_of_measurement(self) -> str | None:
        if self.entity_description.key == "today_use":
            return (
                VOLUME_LITERS
                if self.device_data.volume_unit == IquaSoftenerVolumeUnit.LITERS
                else VOLUME_GALLONS
            )

        return super().native_unit_of_measurement

    @property
    def extra_state_attributes(self):
        """Return the sensor state attributes."""
        return super().extra_state_attributes


# from abc import ABC, abstractmethod
# from datetime import datetime, timedelta
# import logging

# from homeassistant.core import callback
# from homeassistant.helpers.update_coordinator import (
#     DataUpdateCoordinator,
#     UpdateFailed,
#     CoordinatorEntity,
# )


# from homeassistant import config_entries, core
# from homeassistant.components.sensor import (
#     SensorEntity,
#     SensorDeviceClass,
#     SensorStateClass,
#     SensorEntityDescription,
# )
# from homeassistant.const import PERCENTAGE, VOLUME_LITERS, VOLUME_GALLONS

# from .const import (
#     DOMAIN,
#     CONF_USERNAME,
#     CONF_PASSWORD,
#     CONF_DEVICE_SERIAL_NUMBER,
#     VOLUME_FLOW_RATE_LITERS_PER_MINUTE,
#     VOLUME_FLOW_RATE_GALLONS_PER_MINUTE,
# )

# _LOGGER = logging.getLogger(__name__)

# UPDATE_INTERVAL = timedelta(seconds=5)


# async def async_setup_entry(
#     hass: core.HomeAssistant,
#     config_entry: config_entries.ConfigEntry,
#     async_add_entities,
# ):
#     config = hass.data[DOMAIN][config_entry.entry_id]
#     if config_entry.options:
#         config.update(config_entry.options)
#     device_serial_number = config[CONF_DEVICE_SERIAL_NUMBER]
#     coordinator = IquaSoftenerCoordinator(
#         hass,
#         IquaSoftener(
#             config[CONF_USERNAME], config[CONF_PASSWORD], device_serial_number
#         ),
#     )
#     await coordinator.async_config_entry_first_refresh()
#     sensors = [
#         clz(coordinator, device_serial_number, entity_description)
#         for clz, entity_description in (
#             (
#                 IquaSoftenerStateSensor,
#                 SensorEntityDescription(key="State", name="State"),
#             ),
#             (
#                 IquaSoftenerDeviceDateTimeSensor,
#                 SensorEntityDescription(
#                     key="DATE_TIME",
#                     name="Date/time",
#                     icon="mdi:clock",
#                 ),
#             ),
#             (
#                 IquaSoftenerLastRegenerationSensor,
#                 SensorEntityDescription(
#                     key="LAST_REGENERATION",
#                     name="Last regeneration",
#                     device_class=SensorDeviceClass.TIMESTAMP,
#                 ),
#             ),
#             (
#                 IquaSoftenerOutOfSaltEstimatedDaySensor,
#                 SensorEntityDescription(
#                     key="OUT_OF_SALT_ESTIMATED_DAY",
#                     name="Out of salt estimated day",
#                     device_class=SensorDeviceClass.TIMESTAMP,
#                 ),
#             ),
#             (
#                 IquaSoftenerSaltLevelSensor,
#                 SensorEntityDescription(
#                     key="SALT_LEVEL",
#                     name="Salt level",
#                     state_class=SensorStateClass.MEASUREMENT,
#                     native_unit_of_measurement=PERCENTAGE,
#                 ),
#             ),
#             (
#                 IquaSoftenerAvailableWaterSensor,
#                 SensorEntityDescription(
#                     key="AVAILABLE_WATER",
#                     name="Available water",
#                     state_class=SensorStateClass.TOTAL,
#                     icon="mdi:water",
#                 ),
#             ),
#             (
#                 IquaSoftenerWaterCurrentFlowSensor,
#                 SensorEntityDescription(
#                     key="WATER_CURRENT_FLOW",
#                     name="Water current flow",
#                     state_class=SensorStateClass.MEASUREMENT,
#                     icon="mdi:water-pump",
#                 ),
#             ),
#             (
#                 IquaSoftenerWaterUsageTodaySensor,
#                 SensorEntityDescription(
#                     key="WATER_USAGE_TODAY",
#                     name="Today water usage",
#                     state_class=SensorStateClass.TOTAL,
#                     icon="mdi:water-minus",
#                 ),
#             ),
#             (
#                 IquaSoftenerWaterUsageDailyAverageSensor,
#                 SensorEntityDescription(
#                     key="WATER_USAGE_DAILY_AVERAGE",
#                     name="Water usage daily average",
#                     state_class=SensorStateClass.MEASUREMENT,
#                 ),
#             ),
#         )
#     ]
#     async_add_entities(sensors)


# class IquaSoftenerCoordinator(DataUpdateCoordinator):
#     def __init__(self, hass: core.HomeAssistant, iqua_softener: IquaSoftener):
#         super().__init__(
#             hass,
#             _LOGGER,
#             name="Iqua Softener",
#             update_interval=UPDATE_INTERVAL,
#         )
#         self._iqua_softener = iqua_softener

#     async def _async_update_data(self) -> IquaSoftenerData:
#         try:
#             return await self.hass.async_add_executor_job(
#                 lambda: self._iqua_softener.get_data()
#             )
#         except IquaSoftenerException as err:
#             raise UpdateFailed(f"Get data failed: {err}")


# class IquaSoftenerSensor(SensorEntity, CoordinatorEntity, ABC):
#     def __init__(
#         self,
#         coordinator: IquaSoftenerCoordinator,
#         device_serial_number: str,
#         entity_description: SensorEntityDescription = None,
#     ):
#         super().__init__(coordinator)
#         self._attr_unique_id = (
#             f"{device_serial_number}_{entity_description.key}".lower()
#         )

#         if entity_description is not None:
#             self.entity_description = entity_description

#     @callback
#     def _handle_coordinator_update(self) -> None:
#         self.update(self.coordinator.data)
#         self.async_write_ha_state()

#     @abstractmethod
#     def update(self, data: IquaSoftenerData):
#         ...


# class IquaSoftenerStateSensor(IquaSoftenerSensor):
#     def update(self, data: IquaSoftenerData):
#         self._attr_native_value = str(data.state.value)


# class IquaSoftenerDeviceDateTimeSensor(IquaSoftenerSensor):
#     def update(self, data: IquaSoftenerData):
#         self._attr_native_value = data.device_date_time.strftime("%Y-%m-%d %H:%M:%S")


# class IquaSoftenerLastRegenerationSensor(IquaSoftenerSensor):
#     def update(self, data: IquaSoftenerData):
#         self._attr_native_value = (
#             datetime.now(data.device_date_time.tzinfo)
#             - timedelta(days=data.days_since_last_regeneration)
#         ).replace(hour=0, minute=0, second=0)


# class IquaSoftenerOutOfSaltEstimatedDaySensor(IquaSoftenerSensor):
#     def update(self, data: IquaSoftenerData):
#         self._attr_native_value = (
#             datetime.now(data.device_date_time.tzinfo)
#             + timedelta(days=data.out_of_salt_estimated_days)
#         ).replace(hour=0, minute=0, second=0)


# class IquaSoftenerSaltLevelSensor(IquaSoftenerSensor):
#     def update(self, data: IquaSoftenerData):
#         self._attr_native_value = data.salt_level_percent

#     @property
#     def icon(self) -> str | None:
#         if self._attr_native_value is not None:
#             if self._attr_native_value > 75:
#                 return "mdi:signal-cellular-3"
#             elif self._attr_native_value > 50:
#                 return "mdi:signal-cellular-2"
#             elif self._attr_native_value > 25:
#                 return "mdi:signal-cellular-1"
#             elif self._attr_native_value > 5:
#                 return "mdi:signal-cellular-outline"
#             return "mdi:signal-off"
#         else:
#             return "mdi:signal"


# class IquaSoftenerAvailableWaterSensor(IquaSoftenerSensor):
#     def update(self, data: IquaSoftenerData):
#         self._attr_native_value = data.total_water_available
#         self._attr_native_unit_of_measurement = (
#             VOLUME_LITERS
#             if data.volume_unit == IquaSoftenerVolumeUnit.LITERS
#             else VOLUME_GALLONS
#         )
#         self._attr_last_reset = datetime.now(data.device_date_time.tzinfo) - timedelta(
#             days=data.days_since_last_regeneration
#         )


# class IquaSoftenerWaterCurrentFlowSensor(IquaSoftenerSensor):
#     def update(self, data: IquaSoftenerData):
#         self._attr_native_value = data.current_water_flow
#         self._attr_native_unit_of_measurement = (
#             VOLUME_FLOW_RATE_LITERS_PER_MINUTE
#             if data.volume_unit == IquaSoftenerVolumeUnit.LITERS
#             else VOLUME_FLOW_RATE_GALLONS_PER_MINUTE
#         )


# class IquaSoftenerWaterUsageTodaySensor(IquaSoftenerSensor):
#     def update(self, data: IquaSoftenerData):
#         self._attr_native_value = data.today_use
#         self._attr_native_unit_of_measurement = (
#             VOLUME_LITERS
#             if data.volume_unit == IquaSoftenerVolumeUnit.LITERS
#             else VOLUME_GALLONS
#         )
#         self._attr_last_reset = datetime.now(data.device_date_time.tzinfo).replace(
#             hour=0, minute=0, second=0
#         )


# class IquaSoftenerWaterUsageDailyAverageSensor(IquaSoftenerSensor):
#     def update(self, data: IquaSoftenerData):
#         self._attr_native_value = data.average_daily_use
#         self._attr_native_unit_of_measurement = (
#             VOLUME_LITERS
#             if data.volume_unit == IquaSoftenerVolumeUnit.LITERS
#             else VOLUME_GALLONS
#         )
