"""Marklife thermal label printer protocol layer.

Python port of the BLE protocol core from https://github.com/tomLadder/thermoprint
(MIT), extended with device metadata in the style of hass-niimbot.
"""

from __future__ import annotations

from .client import MarklifeClient
from .errors import ErrorCode, MarklifeError, PrinterError, UnsupportedDeviceError
from .imaging import Bitmap1bpp, fit_to_printhead, to_raster
from .models import (
    DeviceProfile,
    advertisement_contradicts,
    all_name_prefixes,
    find_profile_by_name,
    get_profile,
    registered_profiles,
)
from .parser import BLEData, MarklifeDevice
from .protocols import FAULT_STATUSES, STATUS_CODES, InfoKind, PrintOptions

__version__ = "0.1.0"

__all__ = [
    "BLEData",
    "Bitmap1bpp",
    "DeviceProfile",
    "ErrorCode",
    "FAULT_STATUSES",
    "InfoKind",
    "MarklifeClient",
    "MarklifeDevice",
    "MarklifeError",
    "PrintOptions",
    "PrinterError",
    "STATUS_CODES",
    "UnsupportedDeviceError",
    "advertisement_contradicts",
    "all_name_prefixes",
    "find_profile_by_name",
    "fit_to_printhead",
    "get_profile",
    "registered_profiles",
    "to_raster",
]
