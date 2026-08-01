"""Device profiles and the name-prefix registry.

A profile fuses two things thermoprint and hass-niimbot each hold half of:

* transport/protocol facts (thermoprint ``DeviceProfile``) -- service and
  characteristic UUIDs, packet size, tick interval, which density command the
  model understands;
* hardware metadata (hass-niimbot ``modelsLibrary``) -- print head width in
  dots and DPI. thermoprint's web editor works in millimetres and never needs
  the dot count, but Home Assistant renders a pixel canvas so it does.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from .protocols import PaperType

#: Primary GATT service, used by every BLE Marklife printer except P80/T3.
SERVICE_PRIMARY = "0000ff00-0000-1000-8000-00805f9b34fb"
CHAR_RX_PRIMARY = "0000ff01-0000-1000-8000-00805f9b34fb"  # notify: printer -> host
CHAR_TX_PRIMARY = "0000ff02-0000-1000-8000-00805f9b34fb"  # write:  host -> printer
CHAR_CX_PRIMARY = "0000ff03-0000-1000-8000-00805f9b34fb"  # notify: credits + MTU

#: Fallback service used by P80 and T3. It has no CX characteristic, so there
#: is no credit feedback and pacing degrades to pure time-based throttling.
SERVICE_ALT = "49535343-fe7d-4ae5-8fa9-9fafd205e455"
CHAR_RX_ALT = "49535343-1e4d-4bd9-ba61-23c647249616"
CHAR_TX_ALT = "49535343-8841-43f4-a8d4-ecbe34729bb3"

DEFAULT_PACKET_SIZE = 237  # MTU 240 - 3


@dataclass(frozen=True, slots=True)
class LabelSize:
    width_mm: float
    height_mm: float


@dataclass(frozen=True, slots=True)
class PrintDefaults:
    density: int = 2
    paper_type: PaperType = "gap"


@dataclass(frozen=True, slots=True)
class LabelConfig:
    supported_paper_types: tuple[PaperType, ...] = ("gap",)
    default_size: LabelSize = LabelSize(40, 12)
    gap_sizes: tuple[LabelSize, ...] = ()
    continuous_sizes: tuple[LabelSize, ...] = ()


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    """Everything the client needs to talk to one family of printers."""

    model_id: str
    protocol_id: str

    # --- transport ---
    service_uuid: str = SERVICE_PRIMARY
    tx_uuid: str = CHAR_TX_PRIMARY
    rx_uuid: str = CHAR_RX_PRIMARY
    cx_uuid: str | None = CHAR_CX_PRIMARY
    packet_size: int | None = None
    tick_ms: int = 30

    # --- hardware ---
    printhead_px: int = 384
    dpi: int = 203

    # --- print parameters ---
    density_command: Literal["density", "thickness"] = "density"
    density_map: dict[int, int] | None = None
    defaults: PrintDefaults = PrintDefaults()
    label_config: LabelConfig = LabelConfig()

    # --- discovery ---
    name_prefixes: tuple[str, ...] = ()

    #: False for SPP / external-library models. They are listed so the config
    #: flow can explain *why* they will never work rather than just not
    #: appearing. See UnsupportedDeviceError.
    supported: bool = True
    unsupported_reason: str = ""

    def map_density(self, density: int) -> int:
        """Translate a 1-3 UI density onto the scale this model expects."""
        if self.density_map is None:
            return density
        return self.density_map.get(density, next(iter(self.density_map.values())))

    @property
    def uses_credits(self) -> bool:
        """Whether the printer grants flow-control credits over CX."""
        return self.cx_uuid is not None

    @property
    def effective_packet_size(self) -> int:
        return self.packet_size or DEFAULT_PACKET_SIZE


_PROFILES: list[DeviceProfile] = []
#: (prefix, profile) sorted longest-prefix-first -- rebuilt on every register.
_PREFIX_INDEX: list[tuple[str, DeviceProfile]] = []


def register_profile(profile: DeviceProfile) -> None:
    """Add a profile and rebuild the prefix index."""
    _PROFILES.append(profile)
    _reindex()


def _reindex() -> None:
    """Rebuild the prefix index, longest prefix first.

    thermoprint matches prefixes in profile registration order, which is
    order-dependent and wrong once prefixes overlap: "P1s" (P15 family) vs
    "P11"/"P12" (P12 family), "P15" vs "P15R" vs "P15S", "P50" vs "P50S",
    "P7" vs "P7R". Sorting by descending length makes the match deterministic
    and always picks the most specific profile.
    """
    _PREFIX_INDEX.clear()
    pairs = [(p, prof) for prof in _PROFILES for p in prof.name_prefixes]
    pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
    _PREFIX_INDEX.extend(pairs)


def find_profile_by_name(name: str | None) -> DeviceProfile | None:
    """Resolve an advertised BLE name to a profile, or None if unrecognised.

    Marklife printers expose no device-type query -- unlike Niimbot, which
    reports a numeric model ID -- so the advertised name is the only handle we
    have for picking a protocol.
    """
    if not name:
        return None
    upper = name.upper()
    for prefix, profile in _PREFIX_INDEX:
        if upper.startswith(prefix.upper()):
            return profile
    return None


def advertisement_contradicts(
    profile: DeviceProfile, advertised_uuids: Iterable[str]
) -> bool:
    """True when the advertisement rules this profile out.

    A name prefix alone is weak evidence: ``M1-``, ``S2-``, ``T3-`` and friends
    are short enough to collide with unrelated hardware. When the advertisement
    also carries service UUIDs we can demand that the profile's service is among
    them, which turns a name collision into a rejection.

    The check is deliberately one-sided. An advertisement that carries **no**
    service UUIDs proves nothing -- plenty of peripherals keep the list out of
    the advertisement and only expose services after connecting -- so an empty
    list is never treated as a contradiction. Only a populated list that omits
    our service counts as evidence against.
    """
    advertised = {uuid.lower() for uuid in advertised_uuids}
    if not advertised:
        return False
    return profile.service_uuid.lower() not in advertised


def get_profile(model_id: str) -> DeviceProfile | None:
    return next((p for p in _PROFILES if p.model_id == model_id), None)


def registered_profiles() -> list[DeviceProfile]:
    return list(_PROFILES)


def all_name_prefixes() -> list[str]:
    """Every known prefix, including unsupported models."""
    return [prefix for prefix, _ in _PREFIX_INDEX]


def _register_builtins() -> None:
    # Imported here so profile modules can import DeviceProfile from this module.
    from .profiles import BUILTIN_PROFILES

    for profile in BUILTIN_PROFILES:
        register_profile(profile)


_register_builtins()
