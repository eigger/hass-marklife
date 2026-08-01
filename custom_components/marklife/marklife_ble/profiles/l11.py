"""Device profiles for the L11 family.

Name prefixes and packet sizes come from the reverse-engineering notes
(sections 2.4 and 5) plus thermoprint's shipped p15/p12 profiles.
"""

from __future__ import annotations

from ..models import DeviceProfile, LabelConfig, LabelSize, PrintDefaults

_GAP_SIZES = (
    LabelSize(22, 12),
    LabelSize(22, 14),
    LabelSize(26, 15),
    LabelSize(30, 12),
    LabelSize(30, 14),
    LabelSize(30, 15),
    LabelSize(40, 12),
    LabelSize(40, 14),
    LabelSize(40, 15),
    LabelSize(50, 15),
)

#: P15 and everything the vendor app maps onto the P15 series.
P15 = DeviceProfile(
    model_id="p15",
    protocol_id="l11",
    packet_size=95,
    tick_ms=30,
    printhead_px=384,
    dpi=203,
    # The P15 family sets darkness with 10 FF 10 00 TT, not 1F 70 02 DD.
    density_command="thickness",
    defaults=PrintDefaults(density=2, paper_type="gap"),
    label_config=LabelConfig(
        supported_paper_types=("gap",),
        default_size=LabelSize(40, 12),
        gap_sizes=_GAP_SIZES,
    ),
    name_prefixes=(
        "P15",
        "P15R",
        "P15S",
        "P7",
        "P7R",
        "P1s",
        "M1",
        "S15",
        "S12",
        "LP15",
        "LPC74",
        "iSPACE_LP15",
        "OUT_LPC",
    ),
)

P12 = DeviceProfile(
    model_id="p12",
    protocol_id="l11",
    packet_size=90,
    tick_ms=30,
    printhead_px=384,
    dpi=203,
    density_command="density",
    defaults=PrintDefaults(density=2, paper_type="gap"),
    label_config=LabelConfig(
        supported_paper_types=("gap", "continuous"),
        default_size=LabelSize(40, 15),
        gap_sizes=_GAP_SIZES,
        continuous_sizes=_GAP_SIZES,
    ),
    name_prefixes=("P12", "P11", "LP90"),
)

PROFILES = (P15, P12)
