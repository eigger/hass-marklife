"""CommandPort compressed protocol -- P50, P80, S2, X2, M60.

thermoprint ships this as ``protocol/x2/`` because M60 is the only device it has
a profile for, but the command set is exactly the vendor app's protocol #3
(``CommandPort``): ``1F C0 01 00`` / ``1F C0 01 01`` session framing, ``1F 10``
compressed raster, ``1F 11`` position adjust, ``1F 12`` printer location. The
P50 print sequence documented in the reverse-engineering notes matches this
step for step, so the same class drives both families.

Compression: the vendor app defaults to ``DFunction.code()``, a proprietary
encoder inside ``libDFunction.so``, and switches to standard zlib when
``getZLibCompressVersion()`` returns 1. thermoprint uses plain zlib level 6 and
that works on real hardware, so the firmware accepts both.
"""

from __future__ import annotations

import zlib
from typing import TYPE_CHECKING

from .base import Command, PrintOptions, Protocol
from .common import BleQueryMixin

if TYPE_CHECKING:
    from ..imaging import Bitmap1bpp
    from ..models import DeviceProfile

#: The vendor calls ``YxqZLib.code(raw, 14, 16384, 6)`` -- level 6 with a 14-bit
#: (16 KB) window. thermoprint uses fflate's default instead, which declares a
#: 15-bit (32 KB) window in the zlib header.
#:
#: That difference is not cosmetic. An inflater initialised with a 16 KB window
#: rejects a 32 KB stream outright ("invalid window size"), while a 16 KB stream
#: decodes on both. Since the firmware's buffer size is unknown and the vendor
#: documents 14, the narrower window is the strictly safer choice.
_ZLIB_LEVEL = 6
_ZLIB_WBITS = 14

def wakeup() -> Command:
    """6 zero bytes (shorter than the L11 wakeup)."""
    return Command("wakeup", bytes(6))


def start_job() -> Command:
    """``1F C0 01 00`` -- begin the print session."""
    return Command("start-job", bytes((0x1F, 0xC0, 0x01, 0x00)))


def stop_job() -> Command:
    """``1F C0 01 01`` -- end the print session."""
    return Command("stop-job", bytes((0x1F, 0xC0, 0x01, 0x01)))


def set_density(value: int) -> Command:
    """``1F 70 02 VV``."""
    return Command("set-density", bytes((0x1F, 0x70, 0x02, value & 0xFF)))


def set_paper_type_gap() -> Command:
    """``1F 80 02 20`` -- select die-cut (gap) media."""
    return Command("set-paper-type", bytes((0x1F, 0x80, 0x02, 0x20)))


def feed_dots(dots: int) -> Command:
    """``1B 4A <lo> <hi> 00`` -- note the 16-bit operand, unlike L11."""
    return Command(
        "feed-dots", bytes((0x1B, 0x4A, dots & 0xFF, (dots >> 8) & 0xFF, 0x00))
    )


def adjust_position_auto(param: int) -> Command:
    """``1F 11 PP`` -- 0x51 opens a label, 0x50 closes it."""
    return Command("adjust-position", bytes((0x1F, 0x11, param & 0xFF)))


def printer_location(x: int, y: int) -> Command:
    """``1F 12 XX YY``."""
    return Command("printer-location", bytes((0x1F, 0x12, x & 0xFF, y & 0xFF)))


def print_bitmap(bitmap: Bitmap1bpp) -> Command:
    """``1F 10 WH WL HH HL L3 L2 L1 L0`` + zlib-compressed raster.

    Width (in bytes per row) and height are big-endian 16-bit here -- the
    opposite of the L11 raster header. The payload length is big-endian 32-bit.
    """
    compressor = zlib.compressobj(_ZLIB_LEVEL, zlib.DEFLATED, _ZLIB_WBITS)
    compressed = compressor.compress(bitmap.data) + compressor.flush()
    header = bytes(
        (
            0x1F,
            0x10,
            (bitmap.bytes_per_row >> 8) & 0xFF,
            bitmap.bytes_per_row & 0xFF,
            (bitmap.height >> 8) & 0xFF,
            bitmap.height & 0xFF,
            (len(compressed) >> 24) & 0xFF,
            (len(compressed) >> 16) & 0xFF,
            (len(compressed) >> 8) & 0xFF,
            len(compressed) & 0xFF,
        )
    )
    return Command("print-bitmap", header + compressed, bulk=True)


class CompressedProtocol(BleQueryMixin, Protocol):
    """P50 / P80 / S2 / X2 / M60 command builder."""

    id = "compressed"

    def build_print_sequence(
        self,
        bitmap: Bitmap1bpp,
        profile: DeviceProfile,
        options: PrintOptions,
    ) -> list[Command]:
        commands: list[Command] = []
        gap = options.paper_type == "gap"

        if gap:
            commands.append(set_paper_type_gap())

        density = options.density if options.density is not None else profile.defaults.density
        if density is not None:
            commands.append(set_density(profile.map_density(density)))

        commands.append(wakeup())
        commands.append(start_job())
        commands.append(adjust_position_auto(0x51) if gap else feed_dots(100))
        commands.append(print_bitmap(bitmap))
        commands.append(printer_location(0x20, 0x00) if gap else printer_location(0x00, 0x00))
        commands.append(stop_job())
        commands.append(adjust_position_auto(0x50) if gap else adjust_position_auto(0x00))

        return commands
