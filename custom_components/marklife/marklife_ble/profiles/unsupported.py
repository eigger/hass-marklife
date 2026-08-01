"""Models that are recognised but can never work from Home Assistant.

These are listed on purpose. Without them the config flow would silently ignore
a printer the user can see in the Marklife app, and every report would look
like a bug. With them we can say exactly why it will not work.

Neither limitation is about effort:

* SPP models speak Bluetooth Classic RFCOMM. bleak has no RFCOMM support on any
  platform, and an ESPHome Bluetooth proxy is BLE-only hardware-wise. There is
  no path from Home Assistant's Bluetooth stack to these printers.
* The D100/X4 family is driven by a closed third-party Android library
  (``caysn.autoreplyprint``) rather than a documented wire protocol.
"""

from __future__ import annotations

from ..models import DeviceProfile

_SPP = "uses Bluetooth Classic SPP (RFCOMM), which neither bleak nor an ESPHome Bluetooth proxy can reach"
_EXTERNAL = "is driven by a closed third-party library with no documented wire protocol"

SPP_FAMILY = DeviceProfile(
    model_id="spp",
    protocol_id="unsupported",
    name_prefixes=(
        "S8",
        "D210",
        "210",
        "IP_D80",
        "DP_D80",
        "DP_8028",
        "HM-24-28",
        "A31",
        "U210",
        "A50",
        "X8",
    ),
    supported=False,
    unsupported_reason=_SPP,
)

EXTERNAL_FAMILY = DeviceProfile(
    model_id="external",
    protocol_id="unsupported",
    name_prefixes=("D100", "X4", "L100", "D200"),
    supported=False,
    unsupported_reason=_EXTERNAL,
)

PROFILES = (SPP_FAMILY, EXTERNAL_FAMILY)
