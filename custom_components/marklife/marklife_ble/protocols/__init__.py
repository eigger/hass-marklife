"""Protocol registry."""

from __future__ import annotations

from ..errors import ErrorCode, MarklifeError
from .base import Command, InfoKind, PaperType, PrintOptions, Protocol, Response
from .common import FAULT_STATUSES, STATUS_CODES
from .compressed import CompressedProtocol
from .l11 import L11Protocol

_PROTOCOLS: dict[str, type[Protocol]] = {
    L11Protocol.id: L11Protocol,
    CompressedProtocol.id: CompressedProtocol,
}


def get_protocol(protocol_id: str) -> Protocol:
    """Instantiate the protocol registered under ``protocol_id``."""
    try:
        return _PROTOCOLS[protocol_id]()
    except KeyError:
        raise MarklifeError(
            ErrorCode.UNKNOWN_PROTOCOL, f"Unknown protocol: {protocol_id}"
        ) from None


def registered_protocol_ids() -> list[str]:
    return list(_PROTOCOLS)


__all__ = [
    "Command",
    "FAULT_STATUSES",
    "InfoKind",
    "PaperType",
    "PrintOptions",
    "Protocol",
    "Response",
    "STATUS_CODES",
    "get_protocol",
    "registered_protocol_ids",
]
