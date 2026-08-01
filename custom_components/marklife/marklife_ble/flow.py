"""Credit-based flow control.

Port of thermoprint ``transport/flow-control.ts``. The printer grants credits on
the CX characteristic (``[0x01, n]``); each outbound packet spends one. A tick
timer releases at most one packet per interval, because sending faster than the
printer's BLE stack drains its buffer makes it stop granting credits entirely.

This is a closed loop, which is what makes it safe over an ESPHome Bluetooth
proxy: if the link is slow, credits arrive slowly and the sender simply waits.
The one escape hatch is starvation recovery -- forcing a credit after silence --
and that is exactly the part that breaks the loop, so its timeout is generous by
default and configurable.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from time import monotonic

_LOGGER = logging.getLogger(__name__)

WriteFn = Callable[[bytes], Awaitable[None]]
ProgressFn = Callable[[int], None]


class CreditFlowController:
    """Paces writes to the TX characteristic against printer credits."""

    def __init__(
        self,
        write: WriteFn,
        *,
        packet_size: int,
        tick_ms: int,
        starvation_ms: int,
        uses_credits: bool = True,
    ) -> None:
        self._write = write
        self._packet_size = packet_size
        self._tick = max(tick_ms, 1) / 1000
        self._starvation = starvation_ms / 1000
        self._uses_credits = uses_credits
        self._credits = 0
        self._last_credit = monotonic()

    @property
    def credits(self) -> int:
        return self._credits

    @property
    def packet_size(self) -> int:
        return self._packet_size

    def set_packet_size(self, size: int) -> None:
        if size > 0 and size != self._packet_size:
            _LOGGER.debug("Packet size %d -> %d", self._packet_size, size)
            self._packet_size = size

    def grant(self, count: int) -> None:
        """Record a credit grant from the CX characteristic."""
        self._credits += count
        self._last_credit = monotonic()
        _LOGGER.debug("Credits +%d (total %d)", count, self._credits)

    def reset(self) -> None:
        self._credits = 0
        self._last_credit = monotonic()

    async def wait_for_credits(self, minimum: int = 3, timeout: float = 1.0) -> bool:
        """Block until at least ``minimum`` credits are banked.

        Returns False if the wait timed out. Timing out is not fatal -- the send
        loop still has starvation recovery -- so callers proceed either way.
        """
        if not self._uses_credits:
            return True
        deadline = monotonic() + timeout
        while self._credits < minimum:
            if monotonic() >= deadline:
                _LOGGER.debug(
                    "Credit wait timed out (have %d, wanted %d)", self._credits, minimum
                )
                return False
            await asyncio.sleep(0.02)
        return True

    async def send(self, data: bytes, on_progress: ProgressFn | None = None) -> None:
        """Write ``data`` to the printer, one packet per tick."""
        if not data:
            return

        started = monotonic()
        offset = 0
        total = len(data)
        self._last_credit = monotonic()
        _LOGGER.debug(
            "Sending %d bytes in %d packets (credits=%d)",
            total,
            -(-total // self._packet_size),
            self._credits,
        )

        while offset < total:
            if self._uses_credits and self._credits <= 0:
                if monotonic() - self._last_credit >= self._starvation:
                    # The loop is broken: the printer has gone quiet. Force a
                    # single credit so the job can limp forward rather than hang.
                    _LOGGER.debug("Credit starvation, forcing one credit")
                    self._credits = 1
                    self._last_credit = monotonic()
                else:
                    await asyncio.sleep(self._tick)
                    continue

            chunk = data[offset : offset + self._packet_size]
            await self._write(chunk)
            if self._uses_credits:
                self._credits -= 1
            offset += len(chunk)

            if on_progress is not None:
                on_progress(offset)

            if offset < total:
                await asyncio.sleep(self._tick)

        _LOGGER.debug("Sent %d bytes in %.2fs", total, monotonic() - started)
