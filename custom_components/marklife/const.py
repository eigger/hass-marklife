"""Constants for the Marklife BLE integration."""

from __future__ import annotations

import base64

from homeassistant.components.image import Image

from .marklife_ble import BLEData

DOMAIN = "marklife"

#: Domain-wide print lock, kept outside ``hass.data[DOMAIN]`` so that dict stays
#: a clean entry_id -> runtime mapping.
PRINT_LOCK = f"{DOMAIN}_print_lock"

#: Model chosen by hand when a printer's advertised name matches no profile.
#: Marklife printers have no model-ID query, so without a name match there is
#: nothing to infer the protocol from and the user has to say.
CONF_MODEL = "model"

CONF_KEEP_CONNECTION = "keep_connection"
CONF_TICK_MS = "tick_ms"
CONF_STARVATION_MS = "starvation_ms"
CONF_PACKET_SIZE_CAP = "packet_size_cap"

DEFAULT_SCAN_INTERVAL = 600

#: 0 means "use the value from the device profile" (30 ms for most models, 1 ms
#: for M60/X2). Exposed because the profile numbers come from the vendor app
#: running on a phone with a direct BLE link.
DEFAULT_TICK_MS = 0

#: The vendor app forces a credit after 1 s of silence. Over an ESPHome proxy
#: the credit notification takes an extra network hop, so a 1 s timeout fires
#: while the printer is merely slow -- and forcing credits past a printer that
#: has not asked for data is what corrupts a job.
DEFAULT_STARVATION_MS = 2000

#: Hard ceiling on packet size regardless of what the printer announces. The
#: profile cap and the negotiated MTU are the other two limits; whichever is
#: smallest wins.
DEFAULT_PACKET_SIZE_CAP = 180

DEFAULT_KEEP_CONNECTION = False

EMPTY_PNG: bytes = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAkgAAAFeCAIAAADxG3fjAAAFP0lEQVR4nO3VwQkAIBDAMHX/nc8lBKEkE/TXPTMLACrO7wAAeMnYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIMXYAEgxNgBSjA2AFGMDIOUCZNwFueVq8qcAAAAASUVORK5CYII="
)

ImageAndBLEData = tuple[Image, BLEData]
