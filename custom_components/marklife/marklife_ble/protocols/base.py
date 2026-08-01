"""Protocol interface shared by every Marklife BLE printer family."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from ..imaging import Bitmap1bpp
    from ..models import DeviceProfile

PaperType = Literal["gap", "continuous"]
ResponseKind = Literal["success", "credit", "mtu", "status", "battery", "info"]


class InfoKind(StrEnum):
    """Identity/diagnostic values that can be read back from the printer."""

    MODEL = "model"
    FIRMWARE = "firmware"
    SERIAL = "serial"
    MAC = "mac"
    BT_VERSION = "bt_version"
    BT_NAME = "bt_name"
    SPEED = "speed"


@dataclass(frozen=True, slots=True)
class Command:
    """One chunk of bytes to push at the printer.

    ``bulk`` marks the start of the payload section of a print job. Everything
    from the first bulk command onwards is concatenated and sent as a single
    credit-paced stream; everything before it is the preamble.
    """

    label: str
    data: bytes
    bulk: bool = False


@dataclass(frozen=True, slots=True)
class Response:
    """A decoded notification from the printer."""

    kind: ResponseKind
    raw: bytes
    value: int | str | None = None


@dataclass(frozen=True, slots=True)
class PrintOptions:
    """Per-job settings resolved from the service call and the device profile."""

    density: int | None = None
    paper_type: PaperType = "gap"


class Protocol(ABC):
    """Builds command sequences and decodes notifications for one printer family."""

    id: str

    @abstractmethod
    def build_print_sequence(
        self,
        bitmap: Bitmap1bpp,
        profile: DeviceProfile,
        options: PrintOptions,
    ) -> list[Command]:
        """Return the full command sequence for a single label."""

    @abstractmethod
    def build_status_query(self) -> Command:
        """Return the command that asks the printer for its current state."""

    @abstractmethod
    def build_battery_query(self) -> Command:
        """Return the command that asks the printer for its battery level."""

    @abstractmethod
    def build_info_query(self, kind: InfoKind) -> Command:
        """Return the command that reads back one identity value."""

    @abstractmethod
    def parse_response(self, data: bytes) -> Response | None:
        """Decode one notification payload, or None if it is not recognised."""
