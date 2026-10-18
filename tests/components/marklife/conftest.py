"""Real HA entries and deterministic external Bluetooth transport."""

from __future__ import annotations

from time import monotonic

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakError
from habluetooth import get_manager
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.marklife.const import DOMAIN
from custom_components.marklife.marklife_ble import client as client_module
from custom_components.marklife.marklife_ble.models import (
    CHAR_CX_PRIMARY,
    CHAR_RX_PRIMARY,
    CHAR_TX_PRIMARY,
    SERVICE_PRIMARY,
)

ADDRESS = "AA:BB:CC:DD:EE:FF"


class FakeServices:
    def __init__(self, uuid: str) -> None:
        self._uuid = uuid.lower()

    def get_service(self, uuid: str):
        return object() if uuid.lower() == self._uuid else None


class PrinterTransport:
    """Emulate only the device GATT boundary, keeping protocol and client code real."""

    def __init__(self, service_uuid: str = SERVICE_PRIMARY) -> None:
        self.is_connected = False
        self.connections = 0
        self.disconnects = 0
        self.silent = False
        self.fail_connect = False
        self.status_code = 0x05  # cover_closed
        self.battery_level = 85
        self.writes: list[bytes] = []
        self.services = FakeServices(service_uuid)
        self._handlers: dict[str, object] = {}
        self.on_write = None

    async def connect(self, *_args, **_kwargs):
        if self.fail_connect:
            raise BleakError("Test printer unavailable")
        self.connections += 1
        self.is_connected = True
        return self

    async def disconnect(self):
        self.disconnects += 1
        self.is_connected = False

    async def start_notify(self, uuid: str, handler) -> None:
        self._handlers[uuid] = handler
        if uuid == CHAR_CX_PRIMARY and not self.silent:
            self.fire(CHAR_CX_PRIMARY, b"\x01\x64")  # 100 credits

    async def stop_notify(self, uuid: str) -> None:
        self._handlers.pop(uuid, None)

    async def write_gatt_char(
        self, uuid: str, data: bytes, response: bool = False
    ) -> None:
        assert uuid == CHAR_TX_PRIMARY
        self.writes.append(bytes(data))
        if self.on_write is not None:
            self.on_write(len(self.writes))
        if self.silent:
            return
        packet = bytes(data)
        if packet == bytes((0x10, 0xFF, 0x20, 0xF0)):  # MODEL
            self.fire(CHAR_RX_PRIMARY, b"P15")
        elif packet == bytes((0x10, 0xFF, 0x20, 0xF1)):  # FIRMWARE
            self.fire(CHAR_RX_PRIMARY, b"1.0.0")
        elif packet == bytes((0x10, 0xFF, 0x20, 0xF2)):  # SERIAL
            self.fire(CHAR_RX_PRIMARY, b"ML123456")
        elif packet == bytes((0x10, 0xFF, 0x20, 0xF3)):  # MAC
            self.fire(CHAR_RX_PRIMARY, b"AA:BB:CC:DD:EE:FF")
        elif packet == bytes((0x10, 0xFF, 0x50, 0xF1)):  # BATTERY
            self.fire(CHAR_RX_PRIMARY, bytes([0x10, self.battery_level]))
        elif packet == bytes((0x10, 0xFF, 0x40)):  # STATUS
            self.fire(CHAR_RX_PRIMARY, bytes([0xFF, self.status_code]))
        elif (
            packet.startswith(bytes((0x10, 0xFF, 0xF1, 0x45)))
            or b"\x10\xff\xf1\x45" in packet
            or packet.startswith(bytes((0x1F, 0xC0, 0x01, 0x01)))
            or b"\x1f\xc0\x01\x01" in packet
        ):
            self.fire(CHAR_RX_PRIMARY, b"\xaa")

    def fire(self, uuid: str, payload: bytes) -> None:
        if uuid in self._handlers:
            self._handlers[uuid](None, bytearray(payload))

    @property
    def sent(self) -> bytes:
        return b"".join(self.writes)


@pytest.fixture
def transport(monkeypatch):
    device = PrinterTransport()

    async def fake_establish(*_args, **_kwargs):
        await device.connect()
        return device

    monkeypatch.setattr(
        "custom_components.marklife.marklife_ble.parser.establish_connection",
        fake_establish,
    )
    monkeypatch.setattr(client_module, "QUERY_TIMEOUT", 0.05)
    monkeypatch.setattr(client_module, "INITIAL_CREDIT_TIMEOUT", 0.05)
    monkeypatch.setattr(client_module, "PRINT_RESULT_TIMEOUT", 0.05)
    return device


@pytest.fixture
async def advertisement(hass, enable_bluetooth):
    """Feed a scan result through the actual HA Bluetooth manager."""
    device = BLEDevice(
        ADDRESS, "P15-0000", details={"path": "/org/bluez/hci0/dev_AA"}, rssi=-55
    )
    advertisement_data = AdvertisementData(
        local_name="P15-0000",
        manufacturer_data={},
        service_data={},
        service_uuids=[SERVICE_PRIMARY],
        tx_power=None,
        rssi=-55,
        platform_data=(),
    )
    info = BluetoothServiceInfoBleak.from_scan(
        "00:00:00:00:00:01", device, advertisement_data, monotonic(), True
    )
    get_manager().scanner_adv_received(info)
    await hass.async_block_till_done()
    return info


@pytest.fixture
def entry(hass):
    config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ADDRESS,
        title="P15-0000",
        data={"address": ADDRESS, "model": "p15"},
    )
    config.add_to_hass(hass)
    return config


@pytest.fixture
async def loaded_entry(hass, entry, transport, advertisement):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
def entity_id(hass):
    from homeassistant.helpers import entity_registry as er

    def lookup(suffix, domain="sensor"):
        entities = er.async_entries_for_config_entry(
            er.async_get(hass),
            next(e.entry_id for e in hass.config_entries.async_entries(DOMAIN)),
        )
        return next(
            e.entity_id
            for e in entities
            if e.domain == domain and e.unique_id.endswith("_" + suffix)
        )

    return lookup
