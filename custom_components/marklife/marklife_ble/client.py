"""Marklife BLE client -- notification routing and print orchestration.

Port of thermoprint ``printer.ts``, adapted to bleak. Owns one connected
``BleakClient`` and does not manage the connection lifecycle itself; that is
``MarklifeDevice``'s job.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from time import monotonic

from bleak import BleakClient

from .errors import ErrorCode, MarklifeError, PrinterError
from .flow import CreditFlowController
from .imaging import Bitmap1bpp
from .models import DEFAULT_PACKET_SIZE, DeviceProfile
from .protocols import (
    FAULT_STATUSES,
    Command,
    InfoKind,
    PrintOptions,
    Response,
    get_protocol,
)

_LOGGER = logging.getLogger(__name__)

PRINT_RESULT_TIMEOUT = 30.0
QUERY_TIMEOUT = 5.0
INITIAL_CREDIT_TIMEOUT = 3.0

#: Waiter kinds that accept an unparsed notification as their answer. The
#: printer replies to identity queries with bare payloads that carry no
#: recognisable prefix, so anything unrecognised while such a query is pending
#: is the answer to it.
_RAW_FALLBACK_KINDS = frozenset({"battery", "info", "status"})


class MarklifeClient:
    """Talks to one connected printer."""

    def __init__(
        self,
        client: BleakClient,
        profile: DeviceProfile,
        *,
        tick_ms: int | None = None,
        starvation_ms: int = 2000,
        packet_size_cap: int = 180,
    ) -> None:
        self._client = client
        self._profile = profile
        self._protocol = get_protocol(profile.protocol_id)
        self._packet_size_cap = packet_size_cap
        self._pending: list[tuple[str, asyncio.Future[Response]]] = []
        self._subscribed: list[str] = []
        self._printing = False
        self._fault: str | None = None
        self._last_status: str | None = None
        self.on_status: Callable[[str], None] | None = None
        self.on_progress: Callable[[int, int], None] | None = None

        self._flow = CreditFlowController(
            self._write_tx,
            packet_size=min(profile.effective_packet_size, packet_size_cap),
            tick_ms=tick_ms if tick_ms is not None else profile.tick_ms,
            starvation_ms=starvation_ms,
            uses_credits=profile.uses_credits,
        )

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Subscribe to notifications and wait for the opening credit grant."""
        services = self._client.services
        if services.get_service(self._profile.service_uuid) is None:
            raise MarklifeError(
                ErrorCode.SERVICE_NOT_FOUND,
                f"BLE service {self._profile.service_uuid} not found on this device",
            )

        # Track subscriptions as they succeed. If CX fails after RX is already
        # subscribed, stop() still has to unsubscribe RX -- otherwise a kept-open
        # connection carries a live handler bound to a dead client into the next
        # poll, and re-subscribing the same characteristic then fails.
        await self._client.start_notify(self._profile.rx_uuid, self._on_rx)
        self._subscribed.append(self._profile.rx_uuid)
        if self._profile.cx_uuid:
            await self._client.start_notify(self._profile.cx_uuid, self._on_cx)
            self._subscribed.append(self._profile.cx_uuid)

        if self._profile.uses_credits:
            # The printer grants [0x01, 0x04] shortly after connecting. Starting
            # a job before it lands means the first packets go out under
            # starvation recovery at one per second, which shows up as a band of
            # missing rows at the top of the label.
            await self._wait_for_initial_credits()

    async def stop(self) -> None:
        """Unsubscribe. Safe to call more than once, and after a failed start."""
        while self._subscribed:
            uuid = self._subscribed.pop()
            try:
                await self._client.stop_notify(uuid)
            except Exception:  # noqa: BLE001 - teardown must not mask the real error
                _LOGGER.debug("stop_notify(%s) failed", uuid, exc_info=True)

    @property
    def is_printing(self) -> bool:
        return self._printing

    @property
    def last_status(self) -> str | None:
        return self._last_status

    # ------------------------------------------------------------------
    # printing
    # ------------------------------------------------------------------

    async def print_bitmap(
        self,
        bitmap: Bitmap1bpp,
        options: PrintOptions,
        *,
        copies: int = 1,
    ) -> None:
        """Print ``bitmap`` ``copies`` times."""
        commands = self._protocol.build_print_sequence(bitmap, self._profile, options)
        preamble, bulk = _split_at_bulk(commands)

        total = (len(preamble) + len(bulk)) * copies
        _LOGGER.debug(
            "Print %dx%d, %d bytes (preamble=%d bulk=%d) copies=%d",
            bitmap.width,
            bitmap.height,
            total,
            len(preamble),
            len(bulk),
            copies,
        )

        self._printing = True
        self._fault = None
        try:
            for copy in range(copies):
                base = copy * (len(preamble) + len(bulk))

                def report(sent: int, _base: int = base) -> None:
                    if self.on_progress:
                        self.on_progress(_base + len(preamble) + sent, total)

                # Register the completion waiter before any byte of this copy
                # goes out. A small label can be confirmed while data is still
                # being written, and a notification that arrives with nobody
                # waiting for it is dropped -- turning a successful print into a
                # 30 s timeout.
                waiter = self._add_waiter("success")
                try:
                    if preamble:
                        await self._flow.send(preamble)
                        # Let the printer chew through the setup commands and
                        # hand credits back, so the raster starts with a full
                        # window and streams without a stall mid-label.
                        await self._flow.wait_for_credits(3, 1.0)

                    await self._flow.send(bulk, report)
                    await self._wait_for_print_result(waiter)
                finally:
                    self._drop_waiter("success", waiter)
        finally:
            self._printing = False

    # ------------------------------------------------------------------
    # queries
    # ------------------------------------------------------------------

    async def get_battery(self) -> int | None:
        """Return the battery percentage, or None if the printer did not answer."""
        response = await self._query("battery", self._protocol.build_battery_query())
        if response is None:
            return None
        if isinstance(response.value, int):
            return response.value
        # Raw form: [0x10, level] or a bare level byte.
        if len(response.raw) >= 2:
            return response.raw[1]
        return response.raw[0] if response.raw else None

    async def get_status(self) -> str | None:
        """Return the current printer condition, e.g. ``out_of_paper``."""
        response = await self._query("status", self._protocol.build_status_query())
        if response is None:
            return None
        if isinstance(response.value, str):
            return response.value
        return None

    async def get_info(self, kind: InfoKind) -> str | None:
        """Read back one identity value (model, firmware, serial, MAC, ...)."""
        response = await self._query("info", self._protocol.build_info_query(kind))
        if response is None:
            return None
        if isinstance(response.value, str) and response.value:
            return response.value
        text = response.raw.decode("ascii", errors="replace").replace("\x00", "").strip()
        return text or None

    async def _query(self, kind: str, command: Command) -> Response | None:
        if self._printing:
            raise MarklifeError(
                ErrorCode.PRINT_FAILED, "Cannot query the printer while it is printing"
            )
        waiter = self._add_waiter(kind)
        try:
            await self._flow.send(command.data)
            return await asyncio.wait_for(waiter, QUERY_TIMEOUT)
        except TimeoutError:
            _LOGGER.debug("No %s response within %.0fs", kind, QUERY_TIMEOUT)
            return None
        finally:
            self._drop_waiter(kind, waiter)

    # ------------------------------------------------------------------
    # notification handling
    # ------------------------------------------------------------------

    def _on_rx(self, _sender: object, data: bytearray) -> None:
        payload = bytes(data)
        response = self._protocol.parse_response(payload)
        _LOGGER.debug("RX %s -> %s", payload.hex(":"), response.kind if response else "?")

        if response is not None:
            if response.kind == "status" and isinstance(response.value, str):
                self._last_status = response.value
                if response.value in FAULT_STATUSES and self._printing:
                    self._fault = response.value
                if self.on_status:
                    self.on_status(response.value)
            if self._resolve(response.kind, response):
                return

        # Identity queries come back as bare payloads with no prefix to match on,
        # so hand anything unrecognised to a query that is waiting for an answer.
        if response is None and self._pending:
            kind, future = self._pending[0]
            if kind in _RAW_FALLBACK_KINDS:
                self._resolve(kind, Response(kind, payload))  # type: ignore[arg-type]

    def _on_cx(self, _sender: object, data: bytearray) -> None:
        payload = bytes(data)
        response = self._protocol.parse_response(payload)
        _LOGGER.debug("CX %s -> %s", payload.hex(":"), response.kind if response else "?")
        if response is None:
            return

        if response.kind == "credit" and isinstance(response.value, int):
            self._flow.grant(response.value)
        elif response.kind == "mtu" and isinstance(response.value, int):
            self._apply_mtu(response.value)

        # Some models acknowledge job completion on CX rather than RX.
        self._resolve(response.kind, response)

    def _apply_mtu(self, mtu: int) -> None:
        """Clamp the packet size against the announced MTU.

        Three caps, because each can be the binding one: what the link
        negotiated, what the profile says the firmware tolerates, and a hard
        ceiling for ESPHome proxies whose own MTU may be smaller than whatever
        the printer advertises.
        """
        if mtu <= 3:
            return
        size = min(
            mtu - 3,
            self._profile.packet_size or DEFAULT_PACKET_SIZE,
            self._packet_size_cap,
        )
        self._flow.set_packet_size(size)

    async def _write_tx(self, chunk: bytes) -> None:
        await self._client.write_gatt_char(self._profile.tx_uuid, chunk, response=False)

    # ------------------------------------------------------------------
    # waiters
    # ------------------------------------------------------------------

    def _add_waiter(self, kind: str) -> asyncio.Future[Response]:
        future: asyncio.Future[Response] = asyncio.get_running_loop().create_future()
        self._pending.append((kind, future))
        return future

    def _drop_waiter(self, kind: str, future: asyncio.Future[Response]) -> None:
        entry = (kind, future)
        if entry in self._pending:
            self._pending.remove(entry)

    def _resolve(self, kind: str, response: Response) -> bool:
        for entry in self._pending:
            if entry[0] == kind:
                self._pending.remove(entry)
                if not entry[1].done():
                    entry[1].set_result(response)
                return True
        return False

    async def _wait_for_initial_credits(self) -> None:
        deadline = monotonic() + INITIAL_CREDIT_TIMEOUT
        while self._flow.credits <= 0:
            if monotonic() >= deadline:
                _LOGGER.debug("No initial credits within %.0fs", INITIAL_CREDIT_TIMEOUT)
                return
            await asyncio.sleep(0.05)

    async def _wait_for_print_result(self, waiter: asyncio.Future[Response]) -> None:
        """Wait for the printer to confirm the page.

        Success is ``0xAA`` / ``'O'`` / ``'K'`` on RX. A disconnect after the
        data is already out counts as success too: some models power down as
        soon as the job finishes.

        The waiter is created by the caller, before the last packet is sent, so
        an early confirmation is not missed.
        """
        deadline = monotonic() + PRINT_RESULT_TIMEOUT
        while True:
            if self._fault:
                raise PrinterError(self._fault)
            if waiter.done():
                return
            if not self._client.is_connected:
                _LOGGER.debug("Disconnected after send; treating as success")
                return
            # asyncio.wait leaves the future alone on timeout, unlike wait_for.
            await asyncio.wait({waiter}, timeout=0.5)
            if waiter.done():
                return
            if monotonic() >= deadline:
                raise MarklifeError(
                    ErrorCode.TIMEOUT,
                    f"Printer did not confirm the page within "
                    f"{PRINT_RESULT_TIMEOUT:.0f}s",
                )


def _split_at_bulk(commands: list[Command]) -> tuple[bytes, bytes]:
    """Split a command sequence into preamble and bulk payload.

    Everything from the first bulk-flagged command onward is one stream, so the
    raster and its trailing commands are paced together without a credit stall
    in between.
    """
    preamble = bytearray()
    bulk = bytearray()
    seen = False
    for command in commands:
        if command.bulk:
            seen = True
        (bulk if seen else preamble).extend(command.data)
    return bytes(preamble), bytes(bulk)
