"""Exercise the actual HA flow manager and duplicate validation."""

from __future__ import annotations

from time import monotonic

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
)
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS, CONF_SCAN_INTERVAL
from homeassistant.data_entry_flow import FlowResultType

from custom_components.marklife.const import (
    CONF_KEEP_CONNECTION,
    CONF_MODEL,
    DOMAIN,
)


async def test_bluetooth_confirmation(hass, advertisement, transport):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=advertisement,
    )
    if (
        result["type"] is FlowResultType.ABORT
        and result["reason"] == "already_in_progress"
    ):
        progress = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
        assert len(progress) == 1
        result = await hass.config_entries.flow.async_configure(progress[0]["flow_id"])
    assert result["type"] is FlowResultType.FORM, result
    assert result["step_id"] == "bluetooth_confirm"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 300,
            CONF_KEEP_CONNECTION: False,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == advertisement.address
    assert result["result"].data[CONF_SCAN_INTERVAL] == 300


async def test_bluetooth_duplicate(hass, entry, advertisement):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=advertisement,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_unsupported_discovery(hass, enable_bluetooth):
    info = BluetoothServiceInfoBleak.from_scan(
        "00:00:00:00:00:01",
        BLEDevice(
            "00:11:22:33:44:55",
            "S8-0000",
            details={"path": "/org/bluez/hci0/dev_BB"},
            rssi=-60,
        ),
        AdvertisementData(
            local_name="S8-0000",
            manufacturer_data={},
            service_data={},
            service_uuids=[],
            tx_power=None,
            rssi=-60,
            platform_data=(),
        ),
        monotonic(),
        True,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=info,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unsupported_transport"


async def test_manual_flow_and_errors(hass, enable_bluetooth, entry):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    # Test invalid address (contains colon but invalid MAC)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: "AA:broken",
            CONF_MODEL: "p15",
            CONF_SCAN_INTERVAL: 600,
            CONF_KEEP_CONNECTION: False,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_ADDRESS: "invalid_address"}

    # Test duplicate address
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: entry.unique_id,
            CONF_MODEL: "p15",
            CONF_SCAN_INTERVAL: 600,
            CONF_KEEP_CONNECTION: False,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_manual_flow_success(hass, enable_bluetooth, transport):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: "11:22:33:44:55:66",
            CONF_MODEL: "p15",
            CONF_SCAN_INTERVAL: 600,
            CONF_KEEP_CONNECTION: False,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "11:22:33:44:55:66"


async def test_options_flow(hass, loaded_entry):
    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SCAN_INTERVAL: 120,
            CONF_KEEP_CONNECTION: True,
            "tick_ms": 10,
            "starvation_ms": 3000,
            "packet_size_cap": 150,
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert loaded_entry.options[CONF_SCAN_INTERVAL] == 120
    assert loaded_entry.options[CONF_KEEP_CONNECTION] is True
