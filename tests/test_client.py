"""Print orchestration tests against a fake BLE client.

These exercise MarklifeClient end to end -- notification routing, credit
handling and the print sequence -- without hardware.
"""

from __future__ import annotations

import asyncio

import pytest
from PIL import Image

from marklife_ble.client import MarklifeClient, _split_at_bulk
from marklife_ble.errors import ErrorCode, MarklifeError, PrinterError
from marklife_ble.imaging import to_raster
from marklife_ble.models import (
    CHAR_CX_PRIMARY,
    CHAR_RX_PRIMARY,
    CHAR_TX_PRIMARY,
    get_profile,
)
from marklife_ble.protocols import PrintOptions, get_protocol


class FakeServices:
    def __init__(self, uuid: str) -> None:
        self._uuid = uuid

    def get_service(self, uuid: str):
        return object() if uuid == self._uuid else None


class FakeBleakClient:
    """Records writes and lets a test push notifications back."""

    def __init__(self, service_uuid: str) -> None:
        self.is_connected = True
        self.writes: list[bytes] = []
        self.services = FakeServices(service_uuid)
        self._handlers: dict[str, object] = {}
        self.on_write = None

    async def start_notify(self, uuid: str, handler) -> None:
        self._handlers[uuid] = handler

    async def stop_notify(self, uuid: str) -> None:
        self._handlers.pop(uuid, None)

    async def write_gatt_char(self, uuid: str, data: bytes, response: bool = True) -> None:
        assert uuid == CHAR_TX_PRIMARY
        assert response is False, "TX must use write-without-response"
        self.writes.append(bytes(data))
        if self.on_write is not None:
            self.on_write(len(self.writes))

    def fire(self, uuid: str, payload: bytes) -> None:
        self._handlers[uuid](None, bytearray(payload))

    @property
    def sent(self) -> bytes:
        return b"".join(self.writes)


@pytest.fixture
def bitmap():
    img = Image.new("L", (384, 96), color=255)
    for y in range(img.height):
        for x in range(0, img.width, 3):
            img.putpixel(((x + y * 7) % img.width, y), 0)
    return to_raster(img, dither=False)


async def _connected(profile, **kwargs) -> tuple[MarklifeClient, FakeBleakClient]:
    """Start a client and grant it the opening credits."""
    fake = FakeBleakClient(profile.service_uuid)
    printer = MarklifeClient(fake, profile, tick_ms=1, starvation_ms=50, **kwargs)
    task = asyncio.create_task(printer.start())
    await asyncio.sleep(0.05)
    if profile.uses_credits:
        fake.fire(CHAR_CX_PRIMARY, b"\x01\x64")  # 100 credits
    await asyncio.wait_for(task, 5)
    return printer, fake


def test_start_requires_the_profile_service():
    async def run():
        fake = FakeBleakClient("0000dead-0000-1000-8000-00805f9b34fb")
        printer = MarklifeClient(fake, get_profile("p15"))
        with pytest.raises(MarklifeError) as excinfo:
            await printer.start()
        assert excinfo.value.code is ErrorCode.SERVICE_NOT_FOUND

    asyncio.run(run())


def test_print_sends_the_full_command_sequence(bitmap):
    async def run():
        profile = get_profile("p15")
        printer, fake = await _connected(profile)
        options = PrintOptions(density=2, paper_type="gap")

        task = asyncio.create_task(printer.print_bitmap(bitmap, options))
        await asyncio.sleep(0.3)
        fake.fire(CHAR_RX_PRIMARY, b"\xaa")
        await asyncio.wait_for(task, 5)

        expected = get_protocol("l11").build_print_sequence(bitmap, profile, options)
        preamble, bulk = _split_at_bulk(expected)
        assert fake.sent == preamble + bulk

    asyncio.run(run())


def test_writes_are_chunked_to_the_profile_packet_size(bitmap):
    async def run():
        printer, fake = await _connected(get_profile("p15"))
        task = asyncio.create_task(
            printer.print_bitmap(bitmap, PrintOptions(density=2))
        )
        await asyncio.sleep(0.3)
        fake.fire(CHAR_RX_PRIMARY, b"\xaa")
        await asyncio.wait_for(task, 5)

        # P15 caps at 95 bytes; the default 180 byte ceiling is not binding here.
        assert all(len(chunk) <= 95 for chunk in fake.writes)
        assert max(len(chunk) for chunk in fake.writes) == 95

    asyncio.run(run())


def test_confirmation_during_the_send_is_not_lost(bitmap):
    """Regression: the success waiter must exist before the last packet goes out.

    A short label can be confirmed between the final write and the waiter being
    installed. With the waiter registered afterwards, that notification lands
    with nobody listening and a successful print becomes a 30 s timeout.
    """
    async def run():
        printer, fake = await _connected(get_profile("p15"))
        # Confirm as early as possible: right after the very first packet.
        fake.on_write = lambda n: (
            fake.fire(CHAR_RX_PRIMARY, b"\xaa") if n == 1 else None
        )
        await asyncio.wait_for(
            printer.print_bitmap(bitmap, PrintOptions(density=2)), 5
        )

    asyncio.run(run())


def test_fault_during_printing_raises(bitmap):
    async def run():
        printer, fake = await _connected(get_profile("p15"))
        fake.on_write = lambda n: (
            fake.fire(CHAR_RX_PRIMARY, b"\xff\x01") if n == 1 else None
        )
        with pytest.raises(PrinterError) as excinfo:
            await asyncio.wait_for(
                printer.print_bitmap(bitmap, PrintOptions(density=2)), 5
            )
        assert excinfo.value.status == "out_of_paper"

    asyncio.run(run())


def test_disconnect_after_send_counts_as_success(bitmap):
    """Some models power down as soon as the job finishes."""
    async def run():
        printer, fake = await _connected(get_profile("p15"))
        fake.on_write = lambda n: setattr(fake, "is_connected", False)
        await asyncio.wait_for(
            printer.print_bitmap(bitmap, PrintOptions(density=2)), 5
        )

    asyncio.run(run())


def test_mtu_notification_shrinks_the_packet_size(bitmap):
    async def run():
        printer, fake = await _connected(get_profile("p15"), packet_size_cap=180)
        # MTU 64 -> 61 byte payload, below both the cap and the profile's 95.
        fake.fire(CHAR_CX_PRIMARY, b"\x02\x40\x00")
        task = asyncio.create_task(
            printer.print_bitmap(bitmap, PrintOptions(density=2))
        )
        await asyncio.sleep(0.3)
        fake.fire(CHAR_RX_PRIMARY, b"\xaa")
        await asyncio.wait_for(task, 5)
        assert max(len(chunk) for chunk in fake.writes) == 61

    asyncio.run(run())


def test_packet_size_cap_beats_a_larger_mtu(bitmap):
    async def run():
        printer, fake = await _connected(get_profile("p15"), packet_size_cap=64)
        fake.fire(CHAR_CX_PRIMARY, b"\x02\xf0\x00")  # MTU 240 -> 237, profile says 95
        task = asyncio.create_task(
            printer.print_bitmap(bitmap, PrintOptions(density=2))
        )
        await asyncio.sleep(0.3)
        fake.fire(CHAR_RX_PRIMARY, b"\xaa")
        await asyncio.wait_for(task, 5)
        assert max(len(chunk) for chunk in fake.writes) == 64

    asyncio.run(run())


def test_queries_are_refused_while_printing(bitmap):
    async def run():
        from marklife_ble.protocols import InfoKind

        printer, fake = await _connected(get_profile("p15"))
        task = asyncio.create_task(
            printer.print_bitmap(bitmap, PrintOptions(density=2))
        )
        await asyncio.sleep(0.05)
        with pytest.raises(MarklifeError):
            await printer.get_info(InfoKind.MODEL)
        fake.fire(CHAR_RX_PRIMARY, b"\xaa")
        await asyncio.wait_for(task, 5)

    asyncio.run(run())


def test_identity_query_falls_back_to_raw_payload():
    """The printer answers identity queries with a bare payload, no prefix."""
    async def run():
        from marklife_ble.protocols import InfoKind

        printer, fake = await _connected(get_profile("p15"))
        task = asyncio.create_task(printer.get_info(InfoKind.MODEL))
        await asyncio.sleep(0.05)
        fake.fire(CHAR_RX_PRIMARY, b"P15\x00")
        assert await asyncio.wait_for(task, 5) == "P15"

    asyncio.run(run())


def test_battery_query_reads_the_second_byte():
    async def run():
        printer, fake = await _connected(get_profile("p15"))
        task = asyncio.create_task(printer.get_battery())
        await asyncio.sleep(0.05)
        fake.fire(CHAR_RX_PRIMARY, b"\x10\x4b")  # 75 %
        assert await asyncio.wait_for(task, 5) == 0x4B

    asyncio.run(run())


def test_status_query_decodes_the_condition():
    async def run():
        printer, fake = await _connected(get_profile("p15"))
        task = asyncio.create_task(printer.get_status())
        await asyncio.sleep(0.05)
        fake.fire(CHAR_RX_PRIMARY, b"\xff\x02")
        assert await asyncio.wait_for(task, 5) == "cover_open"

    asyncio.run(run())


def test_copies_replay_the_whole_session(bitmap):
    async def run():
        profile = get_profile("p15")
        printer, fake = await _connected(profile)
        options = PrintOptions(density=2)

        # Each copy registers its waiter before its first byte, so the first
        # write of a copy resolves that copy; the rest land with no waiter.
        fake.on_write = lambda _n: fake.fire(CHAR_RX_PRIMARY, b"\xaa")
        await asyncio.wait_for(
            printer.print_bitmap(bitmap, options, copies=2), 10
        )

        preamble, bulk = _split_at_bulk(
            get_protocol("l11").build_print_sequence(bitmap, profile, options)
        )
        assert fake.sent == (preamble + bulk) * 2

    asyncio.run(run())


def test_stop_unsubscribes_after_a_partial_start():
    """A failure subscribing CX must not leave RX subscribed.

    With keep_connection on, a stale handler bound to a discarded client would
    ride the same connection into the next poll, and re-subscribing the same
    characteristic then fails.
    """
    class FlakyClient(FakeBleakClient):
        async def start_notify(self, uuid: str, handler) -> None:
            if uuid == CHAR_CX_PRIMARY:
                raise RuntimeError("CX subscribe failed")
            await super().start_notify(uuid, handler)

    async def run():
        profile = get_profile("p15")
        fake = FlakyClient(profile.service_uuid)
        printer = MarklifeClient(fake, profile, tick_ms=1)

        with pytest.raises(RuntimeError):
            await printer.start()
        assert fake._handlers, "RX was subscribed before CX failed"

        await printer.stop()
        assert not fake._handlers, "stop() left a subscription behind"
        await printer.stop()  # idempotent

    asyncio.run(run())


def test_stop_is_safe_before_any_start():
    async def run():
        fake = FakeBleakClient(get_profile("p15").service_uuid)
        await MarklifeClient(fake, get_profile("p15")).stop()

    asyncio.run(run())
