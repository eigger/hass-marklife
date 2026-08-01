"""Test setup for the standalone protocol layer.

The ``marklife_ble`` package under ``custom_components/marklife`` has no Home
Assistant imports, so it can be tested on its own. Two things are needed: its
parent directory on ``sys.path`` (importing ``custom_components.marklife``
instead would pull in the HA integration), and a stub for
``bleak_retry_connector``, which ships with Home Assistant rather than bleak.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

COMPONENT_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "marklife"
sys.path.insert(0, str(COMPONENT_DIR))

if "bleak_retry_connector" not in sys.modules:
    stub = types.ModuleType("bleak_retry_connector")
    stub.establish_connection = None
    stub.close_stale_connections_by_address = None
    sys.modules["bleak_retry_connector"] = stub
