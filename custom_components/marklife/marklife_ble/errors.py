"""Exceptions for the Marklife BLE protocol layer."""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    """Machine-readable cause of a MarklifeError."""

    UNKNOWN_DEVICE = "unknown_device"
    UNSUPPORTED_DEVICE = "unsupported_device"
    UNKNOWN_PROTOCOL = "unknown_protocol"
    SERVICE_NOT_FOUND = "service_not_found"
    CHARACTERISTIC_NOT_FOUND = "characteristic_not_found"
    NOT_CONNECTED = "not_connected"
    PRINT_FAILED = "print_failed"
    TIMEOUT = "timeout"
    PRINTER_ERROR = "printer_error"


class MarklifeError(Exception):
    """Base error raised by the protocol layer."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class PrinterError(MarklifeError):
    """The printer reported a fault (out of paper, cover open, ...)."""

    def __init__(self, status: str, raw: bytes = b"") -> None:
        super().__init__(ErrorCode.PRINTER_ERROR, f"Printer error: {status}")
        self.status = status
        self.raw = raw


class UnsupportedDeviceError(MarklifeError):
    """The model was recognised but cannot work over Home Assistant Bluetooth.

    Marklife's SPP (S8/D210/X8 family) and external-library (D100/X4) printers
    speak Bluetooth Classic RFCOMM or a proprietary transport. Neither bleak nor
    an ESPHome Bluetooth proxy can reach them -- this is a transport limitation,
    not a missing feature.
    """

    def __init__(self, model_id: str, reason: str) -> None:
        super().__init__(
            ErrorCode.UNSUPPORTED_DEVICE,
            f"{model_id} cannot be controlled from Home Assistant: {reason}",
        )
        self.model_id = model_id
        self.reason = reason
