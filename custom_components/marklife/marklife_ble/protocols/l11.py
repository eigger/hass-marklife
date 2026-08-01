"""L11 binary protocol -- P15, P12, P11, P7 and relatives.

Port of thermoprint ``packages/core/src/protocol/l11/``. The raster command is
plain ESC/POS ``GS v 0`` (``1D 76 30``); the surrounding control commands are
Marklife-specific. There is no framing and no checksum: commands are raw byte
strings concatenated into one stream.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Command, PrintOptions, Protocol
from .common import BleQueryMixin

if TYPE_CHECKING:
    from ..imaging import Bitmap1bpp
    from ..models import DeviceProfile


def wakeup() -> Command:
    """15 zero bytes -- wakes the BLE stack before the engine is enabled."""
    return Command("wakeup", bytes(15))


def enable() -> Command:
    """``10 FF F1 02`` -- activate the print engine."""
    return Command("enable", bytes((0x10, 0xFF, 0xF1, 0x02)))


def stop() -> Command:
    """``10 FF F1 45`` -- end the print session."""
    return Command("stop", bytes((0x10, 0xFF, 0xF1, 0x45)))


def set_density(density: int) -> Command:
    """``1F 70 02 DD``."""
    return Command("set-density", bytes((0x1F, 0x70, 0x02, density & 0xFF)))


def set_thickness(thickness: int) -> Command:
    """``10 FF 10 00 TT`` -- the P15 family uses this instead of set_density."""
    return Command("set-thickness", bytes((0x10, 0xFF, 0x10, 0x00, thickness & 0xFF)))


def feed_dots(dots: int) -> Command:
    """``1B 4A NN`` (ESC J)."""
    return Command("feed-dots", bytes((0x1B, 0x4A, dots & 0xFF)))


def feed_lines(lines: int) -> Command:
    """``1B 64 NN`` (ESC d)."""
    return Command("feed-lines", bytes((0x1B, 0x64, lines & 0xFF)))


def position_to_gap() -> Command:
    """``1D 0C`` -- advance to the next die-cut label gap."""
    return Command("position-to-gap", bytes((0x1D, 0x0C)))


def backoff() -> Command:
    """``10 FF F2`` -- reverse feed."""
    return Command("backoff", bytes((0x10, 0xFF, 0xF2)))


def learn_gap() -> Command:
    """``10 FF 03`` -- calibrate the gap sensor."""
    return Command("learn-gap", bytes((0x10, 0xFF, 0x03)))


def self_check() -> Command:
    """``1F 40`` -- print the self-test page."""
    return Command("self-check", bytes((0x1F, 0x40)))


def print_bitmap(bitmap: Bitmap1bpp, quality: int = 0) -> Command:
    """``1D 76 30 QQ WL WH HL HH`` + raw raster (ESC/POS GS v 0).

    Width is expressed in *bytes* per row, both fields little-endian.
    """
    header = bytes(
        (
            0x1D,
            0x76,
            0x30,
            quality & 0x03,
            bitmap.bytes_per_row & 0xFF,
            (bitmap.bytes_per_row >> 8) & 0xFF,
            bitmap.height & 0xFF,
            (bitmap.height >> 8) & 0xFF,
        )
    )
    return Command("print-bitmap", header + bitmap.data, bulk=True)


class L11Protocol(BleQueryMixin, Protocol):
    """P15 / P12 / P11 / P7 command builder."""

    id = "l11"

    def build_print_sequence(
        self,
        bitmap: Bitmap1bpp,
        profile: DeviceProfile,
        options: PrintOptions,
    ) -> list[Command]:
        commands: list[Command] = []

        density = options.density if options.density is not None else profile.defaults.density
        if density is not None:
            value = profile.map_density(density)
            commands.append(
                set_thickness(value)
                if profile.density_command == "thickness"
                else set_density(value)
            )

        commands.append(wakeup())
        commands.append(enable())
        commands.append(print_bitmap(bitmap))

        if options.paper_type == "gap":
            commands.append(position_to_gap())
        else:
            commands.append(feed_dots(100))

        commands.append(stop())
        return commands
