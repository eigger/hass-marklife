"""Device profiles for the CommandPort compressed family.

M60/X2 is the only member thermoprint ships a profile for and therefore the
only one proven to work. P50/P80/S2 use the same command sequence per the
reverse-engineering notes, but nothing here has been run against that hardware.
Unverified fields are marked; treat them as starting points, not facts.
"""

from __future__ import annotations

from ..models import (
    CHAR_RX_ALT,
    CHAR_TX_ALT,
    SERVICE_ALT,
    DeviceProfile,
    LabelConfig,
    LabelSize,
    PrintDefaults,
)

_M60_GAP_SIZES = (
    LabelSize(20, 10),
    LabelSize(30, 15),
    LabelSize(40, 12),
    LabelSize(40, 20),
    LabelSize(40, 30),
    LabelSize(50, 30),
    LabelSize(50, 40),
)

_M60_CONTINUOUS_SIZES = (
    LabelSize(30, 15),
    LabelSize(40, 20),
    LabelSize(40, 30),
    LabelSize(50, 30),
    LabelSize(50, 40),
)

M60 = DeviceProfile(
    model_id="m60",
    protocol_id="compressed",
    packet_size=None,  # falls back to MTU-3, capped by the client
    tick_ms=1,
    # TODO(unverified): thermoprint records label sizes in mm only and never
    # the dot count. 384 is the family default; confirm against a real M60
    # before trusting renders wider than 48 mm.
    printhead_px=384,
    dpi=203,
    density_command="density",
    density_map={1: 3, 2: 8, 3: 14},
    defaults=PrintDefaults(density=2, paper_type="gap"),
    label_config=LabelConfig(
        supported_paper_types=("gap", "continuous"),
        default_size=LabelSize(50, 30),
        gap_sizes=_M60_GAP_SIZES,
        continuous_sizes=_M60_CONTINUOUS_SIZES,
    ),
    name_prefixes=("M60", "X2"),
)

#: TODO(unverified): no thermoprint profile exists for these. Command sequence
#: is taken from the reverse-engineering notes section 3.3 ("P50 Full Print
#: Sequence"), packet size from section 2.4. Print head width is a guess.
P50 = DeviceProfile(
    model_id="p50",
    protocol_id="compressed",
    packet_size=95,
    tick_ms=30,
    printhead_px=384,
    dpi=203,
    density_command="density",
    defaults=PrintDefaults(density=2, paper_type="gap"),
    label_config=LabelConfig(
        supported_paper_types=("gap", "continuous"),
        default_size=LabelSize(40, 30),
    ),
    name_prefixes=("P50", "P50S", "D50", "ewtto ET-"),
)

#: TODO(unverified): P80/T3 sit on the fallback service and expose no CX
#: characteristic, so there is no credit feedback at all -- the flow controller
#: degrades to fixed-interval pacing. This path has never been exercised.
P80 = DeviceProfile(
    model_id="p80",
    protocol_id="compressed",
    service_uuid=SERVICE_ALT,
    tx_uuid=CHAR_TX_ALT,
    rx_uuid=CHAR_RX_ALT,
    cx_uuid=None,
    packet_size=None,
    tick_ms=30,
    printhead_px=576,
    dpi=203,
    density_command="density",
    defaults=PrintDefaults(density=2, paper_type="gap"),
    label_config=LabelConfig(supported_paper_types=("gap", "continuous")),
    name_prefixes=("P80", "T3"),
)

#: Deprecated in the vendor app (protocol #2) but still the compressed path.
S2 = DeviceProfile(
    model_id="s2",
    protocol_id="compressed",
    packet_size=95,
    tick_ms=30,
    printhead_px=384,
    dpi=203,
    density_command="density",
    defaults=PrintDefaults(density=2, paper_type="gap"),
    name_prefixes=("S2",),
)

PROFILES = (M60, P50, P80, S2)
