"""Control and query commands shared by every Marklife BLE protocol.

thermoprint duplicates these byte-for-byte between ``l11/commands.ts`` and
``x2/commands.ts`` (battery, status, model, firmware, serial, MAC, BT version,
BT name, speed) along with an identical ``parseResponse``. They are not
protocol-specific -- they live in the shared BLE transport layer of the vendor
app -- so they are hoisted into one mixin here.

What genuinely differs between protocol families is only the print sequence and
the bitmap encoding.
"""

from __future__ import annotations

from .base import Command, InfoKind, Response

#: RX notification ``[0xFF, code]`` -> condition name.
STATUS_CODES: dict[int, str] = {
    0x01: "out_of_paper",
    0x02: "cover_open",
    0x03: "overheating",
    0x04: "low_battery",
    0x05: "cover_closed",
}

#: Conditions that mean "the printer cannot print right now".
FAULT_STATUSES = frozenset({"out_of_paper", "cover_open", "overheating"})

#: First byte of an RX notification that confirms a finished job.
SUCCESS_BYTES = frozenset({0xAA, 0x4F, 0x4B})  # 0xAA, 'O', 'K'

_INFO_COMMANDS: dict[InfoKind, bytes] = {
    InfoKind.MODEL: bytes((0x10, 0xFF, 0x20, 0xF0)),
    InfoKind.FIRMWARE: bytes((0x10, 0xFF, 0x20, 0xF1)),
    InfoKind.SERIAL: bytes((0x10, 0xFF, 0x20, 0xF2)),
    InfoKind.MAC: bytes((0x10, 0xFF, 0x20, 0xF3)),
    InfoKind.BT_VERSION: bytes((0x10, 0xFF, 0x30, 0x10)),
    InfoKind.BT_NAME: bytes((0x10, 0xFF, 0x30, 0x11)),
    InfoKind.SPEED: bytes((0x1F, 0x60, 0x00)),
}


class BleQueryMixin:
    """Query commands and notification decoding common to all BLE families."""

    def build_status_query(self) -> Command:
        return Command("get-status", bytes((0x10, 0xFF, 0x40)))

    def build_detailed_status_query(self) -> Command:
        return Command("get-detailed-status", bytes((0x1F, 0x20, 0x00)))

    def build_battery_query(self) -> Command:
        return Command("get-battery", bytes((0x10, 0xFF, 0x50, 0xF1)))

    def build_info_query(self, kind: InfoKind) -> Command:
        return Command(f"get-{kind.value}", _INFO_COMMANDS[kind])

    def build_shutdown_time_query(self) -> Command:
        return Command("get-shutdown-time", bytes((0x10, 0xFF, 0x13)))

    def parse_response(self, data: bytes) -> Response | None:
        """Decode an RX or CX notification.

        Four shapes exist on the wire:
          ``0xAA`` / ``'O'`` / ``'K'``  -- job finished (may be a single byte)
          ``[0x01, n]``                 -- flow-control credit grant (CX)
          ``[0x02, lo, hi]``            -- MTU announcement (CX)
          ``[0xFF, code]``              -- status/fault report (RX)
        """
        if not data:
            return None

        first = data[0]
        if first in SUCCESS_BYTES:
            return Response("success", data)

        if len(data) < 2:
            return None
        second = data[1]

        if first == 0x01:
            return Response("credit", data, second)

        if first == 0x02 and len(data) >= 3:
            # Little-endian, despite the big-endian style of the rest of the protocol.
            return Response("mtu", data, (data[2] << 8) | data[1])

        if first == 0xFF:
            return Response(
                "status", data, STATUS_CODES.get(second, f"unknown_{second:02x}")
            )

        return None
