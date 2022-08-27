"""Constant definitions for IQua Water Softener."""

from enum import IntEnum

DOMAIN = "iqua_softener"

CONF_DEVICE_SERIAL_NUMBER = "device_sn"
CONF_INTERVAL_SENSORS = "update_interval"
CONFIG_OPTIONS = [
    CONF_INTERVAL_SENSORS,
]

DEFAULT_BRAND = "IQua"
DEFAULT_ATTRIBUTION = "Data delivered by Ecowater"
DEFAULT_INTERVAL_SENSORS = 5

IQUA_PLATFORMS = ["sensor"]

VOLUME_FLOW_RATE_LITERS_PER_MINUTE = "L/min"
VOLUME_FLOW_RATE_GALLONS_PER_MINUTE = "gal/min"


class IquaSoftenerVolumeUnit(IntEnum):
    """IQua Volumne unit definition."""

    GALLONS = 0
    LITERS = 1
