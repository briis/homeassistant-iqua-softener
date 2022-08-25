"""The IQua Water Softener integration models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from iqua_softener import (
    IquaSoftener,
    IquaSoftenerData,
)


@dataclass
class IQuaEntryData:
    """Data for the weatherbit integration."""

    iqua_api: IquaSoftener
    coordinator: DataUpdateCoordinator
    device_data: IquaSoftenerData
