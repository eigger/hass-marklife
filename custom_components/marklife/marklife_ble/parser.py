"""Home Assistant facing adapter around MarklifeClient.

Mirrors hass-niimbot's ``NiimbotDevice``: owns the connection, serialises access
with a lock, and exposes the coordinator-friendly ``BLEData`` snapshot.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import logging
import time
from collections.abc import AsyncIterator, Callable

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from blesession import (
    DISCONNECT_TIMEOUT_S,
    SessionReports,
    SessionTrace,
    ble_session,
    build_report,
    still_up,
)
from PIL import Image

from .client import MarklifeClient
from .errors import ErrorCode, MarklifeError, UnsupportedDeviceError
from .imaging import fit_to_printhead, to_raster
from .models import DeviceProfile, find_profile_by_name, get_profile
from .protocols import InfoKind, PrintOptions

_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class BLEData:
    """Snapshot of everything known about the printer."""

    name: str = ""
    address: str = ""
    identifier: str = ""
    model: str = ""
    model_id: str = ""
    hw_version: str = ""
    sw_version: str = ""
    serial_number: str = ""
    mac: str = ""
    printhead_px: int = 384
    dpi: int = 203
    sensors: dict[str, str | float | None] = dataclasses.field(
        default_factory=lambda: {"battery": None, "status": None}
    )


class MarklifeDevice:
    """Connection owner and print entry point for one printer."""

    def __init__(
        self,
        address: str,
        *,
        model_id: str | None = None,
        keep_connection: bool = False,
        tick_ms: int | None = None,
        starvation_ms: int = 2000,
        packet_size_cap: int = 180,
        radio_facts: Callable[[SessionTrace], dict] | None = None,
    ) -> None:
        self.address = address
        self.forced_model_id = model_id
        self.keep_connection = keep_connection
        self._tick_ms = tick_ms
        self._starvation_ms = starvation_ms
        self._packet_size_cap = packet_size_cap
        self._radio_facts = radio_facts
        self.reports = SessionReports()
        self.last_error: str | None = None
        self.last_error_time: float | None = None
        self.error_count = 0
        self.last_print_report: dict | None = None

        self.lock = asyncio.Lock()
        self.client: BleakClient | None = None
        self.profile: DeviceProfile | None = None
        self.ble_data = BLEData(
            address=address,
            name="Marklife",
            identifier=address.replace(":", "")[-6:],
        )

        # Several entities watch the same two state changes (the print-duration
        # sensor and the "printing" binary sensor both need printing updates),
        # so these are listener sets rather than single callback slots.
        self._connection_listeners: set[Callable[[], None]] = set()
        self._printing_listeners: set[Callable[[], None]] = set()
        self._is_printing = False
        self._print_start: float | None = None
        self._print_end: float | None = None

    def add_connection_listener(
        self, listener: Callable[[], None]
    ) -> Callable[[], None]:
        """Subscribe to connect/disconnect. Returns an unsubscribe callable."""
        self._connection_listeners.add(listener)
        return lambda: self._connection_listeners.discard(listener)

    def add_printing_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Subscribe to print start/finish. Returns an unsubscribe callable."""
        self._printing_listeners.add(listener)
        return lambda: self._printing_listeners.discard(listener)

    # ------------------------------------------------------------------
    # state
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return still_up(self.client)

    @property
    def is_printing(self) -> bool:
        return self._is_printing

    @property
    def print_duration(self) -> float:
        if self._print_start is None:
            return 0.0
        if self._is_printing:
            return time.time() - self._print_start
        if self._print_end is not None:
            return self._print_end - self._print_start
        return 0.0

    def _notify_connection(self) -> None:
        for listener in list(self._connection_listeners):
            listener()

    def _notify_printing(self) -> None:
        for listener in list(self._printing_listeners):
            listener()

    # ------------------------------------------------------------------
    # connection
    # ------------------------------------------------------------------

    def _resolve_profile(self, ble_device: BLEDevice) -> DeviceProfile:
        """Pick the device profile from the advertised name.

        Marklife printers expose no model-ID query, so the BLE name is the only
        signal available. hass-niimbot can ask the printer what it is; here the
        name is load-bearing.
        """
        if self.profile is not None:
            return self.profile

        if self.forced_model_id:
            # The user picked the model by hand because the advertised name
            # matched nothing. Trust it over any name-based guess.
            profile = get_profile(self.forced_model_id)
            if profile is None:
                raise MarklifeError(
                    ErrorCode.UNKNOWN_DEVICE,
                    f"Unknown Marklife model {self.forced_model_id!r}",
                )
        else:
            profile = find_profile_by_name(ble_device.name)
        if profile is None:
            raise MarklifeError(
                ErrorCode.UNKNOWN_DEVICE,
                f"No Marklife profile matches the BLE name {ble_device.name!r}",
            )
        if not profile.supported:
            raise UnsupportedDeviceError(
                ble_device.name or profile.model_id, profile.unsupported_reason
            )

        self.profile = profile
        self.ble_data.model_id = profile.model_id
        self.ble_data.printhead_px = profile.printhead_px
        self.ble_data.dpi = profile.dpi
        return profile

    @contextlib.asynccontextmanager
    async def _operation(
        self, device: BLEDevice | Callable[[], BLEDevice], operation: str
    ) -> AsyncIterator[tuple[MarklifeClient, DeviceProfile, SessionTrace]]:
        """Own the link and commit diagnostics after all cleanup finishes.

        Callers hold the device lock. Resolve a fresh HA route here, after
        any queued job has finished, so proxy failover is respected.
        """
        trace = SessionTrace(
            stage_map={
                "prepare": "session",
                "subscribe": "session",
                "status": "session",
            }
        )
        outcome: Exception | None = None
        cancelled = False
        try:
            ble_device = device() if callable(device) else device
            with trace.timed("prepare"):
                profile = self._resolve_profile(ble_device)
                if self.ble_data.name == "Marklife":
                    self.ble_data.name = ble_device.name or "Marklife"
            async with ble_session(
                ble_device,
                trace=trace,
                client=self.client,
                keep=self.keep_connection,
                use_services_cache=False,
                disconnected_callback=lambda _client: self._notify_connection(),
            ) as client:
                self.client = client
                self._notify_connection()
                printer = self._make_client(client, profile)
                printer.trace = trace
                try:
                    with trace.timed("subscribe"):
                        await printer.start()
                    yield printer, profile, trace
                finally:
                    await printer.stop()
        except asyncio.CancelledError:
            cancelled = True
            raise
        except Exception as err:
            outcome = err
            raise
        finally:
            if not self.keep_connection:
                self.client = None
            if not cancelled:
                self._commit_report(operation, trace, outcome)
            self._notify_connection()

    def _commit_report(
        self, operation: str, trace: SessionTrace, error: Exception | None
    ) -> None:
        try:
            facts = self._radio_facts(trace) if self._radio_facts else {}
        except Exception:  # noqa: BLE001 - diagnostics must preserve the outcome
            _LOGGER.debug("Unable to resolve BLE radio diagnostics")
            facts = {}
        report = build_report(
            operation=operation, trace=trace, exc=error, facts=facts, noun="printer"
        )
        report["timestamp"] = time.time()
        if operation == "print":
            self.last_print_report = report
        # A sleeping printer is expected between jobs. Keep the latest session
        # visible without replacing the last actionable failure every poll.
        if operation == "update" and report.get("failed_stage") in {
            "connect",
            "unreachable",
        }:
            self.reports.last = report
            return
        self.reports.record(report)
        if error is not None:
            self.last_error = (
                error.code.value
                if isinstance(error, MarklifeError)
                else type(error).__name__
            )
            self.last_error_time = report["timestamp"]
            self.error_count += 1

    def _make_client(
        self, client: BleakClient, profile: DeviceProfile
    ) -> MarklifeClient:
        return MarklifeClient(
            client,
            profile,
            tick_ms=self._tick_ms,
            starvation_ms=self._starvation_ms,
            packet_size_cap=self._packet_size_cap,
        )

    async def disconnect(self) -> None:
        if self.client and self.client.is_connected:
            try:
                async with asyncio.timeout(DISCONNECT_TIMEOUT_S):
                    await self.client.disconnect()
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Disconnect failed", exc_info=True)
        self.client = None
        self._notify_connection()

    # ------------------------------------------------------------------
    # polling
    # ------------------------------------------------------------------

    async def update_device(
        self, ble_device: BLEDevice | Callable[[], BLEDevice]
    ) -> BLEData:
        """Refresh the BLEData snapshot."""
        async with self.lock:
            async with self._operation(ble_device, "update") as (
                printer,
                profile,
                trace,
            ):
                # Identity values never change; read each one once.
                if not self.ble_data.model:
                    self.ble_data.model = (
                        await printer.get_info(InfoKind.MODEL)
                        or profile.model_id.upper()
                    )
                if not self.ble_data.sw_version:
                    self.ble_data.sw_version = (
                        await printer.get_info(InfoKind.FIRMWARE) or ""
                    )
                if not self.ble_data.serial_number:
                    self.ble_data.serial_number = (
                        await printer.get_info(InfoKind.SERIAL) or ""
                    )
                if not self.ble_data.mac:
                    self.ble_data.mac = await printer.get_info(InfoKind.MAC) or ""

                battery = await printer.get_battery()
                if battery is not None:
                    self.ble_data.sensors["battery"] = battery
                status = await printer.get_status()
                if status is not None:
                    self.ble_data.sensors["status"] = status
                if battery is None and status is None:
                    trace.fail("status")
                    raise MarklifeError(
                        ErrorCode.TIMEOUT,
                        "Printer did not answer battery or status queries",
                    )
            _LOGGER.debug("Obtained BLEData: %s", self.ble_data)
            return self.ble_data

    # ------------------------------------------------------------------
    # printing
    # ------------------------------------------------------------------

    async def print_image(
        self,
        ble_device: BLEDevice | Callable[[], BLEDevice],
        image: Image.Image,
        *,
        density: int | None = None,
        paper_type: str = "gap",
        copies: int = 1,
        dither: bool = True,
        threshold: int = 128,
    ) -> dict:
        """Render and print one label."""
        async with self.lock:
            self._is_printing = True
            self._print_start = time.time()
            self._print_end = None
            self._notify_printing()

            try:
                async with self._operation(ble_device, "print") as (
                    printer,
                    profile,
                    trace,
                ):
                    fitted = fit_to_printhead(image, profile.printhead_px)
                    bitmap = to_raster(fitted, dither=dither, threshold=threshold)
                    options = PrintOptions(density=density, paper_type=paper_type)  # type: ignore[arg-type]
                    await printer.print_bitmap(bitmap, options, copies=copies)
            finally:
                self._print_end = time.time()
                self._is_printing = False
                self._notify_printing()

        return {
            "status": "ok",
            "duration": self.print_duration,
            "width": bitmap.width,
            "height": bitmap.height,
            "copies": copies,
        }
