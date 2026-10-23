"""Exercise real BLE sessions and diagnostic entities at the GATT boundary."""

from __future__ import annotations

import asyncio
from functools import partial

import pytest
from bleak.exc import BleakError
from blesession import SessionDropped, guarded_write
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.marklife.const import DOMAIN
from custom_components.marklife.marklife_ble import client as client_module


async def print_label(hass):
    return await hass.services.async_call(
        DOMAIN,
        "print",
        {
            "payload": [{"type": "text", "value": "BLE", "x": 0, "y": 0}],
            "width": 384,
            "height": 32,
        },
        blocking=True,
        return_response=True,
    )


async def test_reused_session_and_unexpected_disconnect(
    hass, loaded_entry, transport, entity_id
):
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    device = runtime["device"]
    device.keep_connection = True
    await runtime["coordinator"].async_refresh()
    connections = transport.connections
    await runtime["coordinator"].async_refresh()
    await hass.async_block_till_done()
    state = hass.states.get(entity_id("connection", "binary_sensor"))
    assert state.state == "on"
    assert state.attributes["reused"] is True
    assert "connect_s" not in state.attributes
    assert transport.connections == connections
    registry_entry = er.async_get(hass).async_get(state.entity_id)
    assert registry_entry.entity_category == EntityCategory.DIAGNOSTIC

    # The callback updates the entity immediately, without waiting for a poll.
    await transport.disconnect()
    await hass.async_block_till_done()
    assert hass.states.get(state.entity_id).state == "off"
    await runtime["coordinator"].async_refresh()
    assert transport.connections == connections + 1
    assert device.is_connected


async def test_failed_print_diagnostics_survive_success(
    hass, loaded_entry, transport, entity_id
):
    transport.fail_connect = True
    with pytest.raises(HomeAssistantError):
        await print_label(hass)
    await hass.async_block_till_done()
    error = hass.states.get(entity_id("last_error"))
    assert error.state == "ConnectFailed"
    assert error.attributes["operation"] == "print"
    assert error.attributes["failed_stage"] == "connect"
    assert error.attributes["success"] is False
    assert error.attributes["timestamp"] > 0
    assert hass.states.get(entity_id("error_count")).state == "1"
    saved = dict(error.attributes)

    # Sleeping-printer polls cannot replace the print failure or count it again.
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    await runtime["coordinator"].async_refresh()
    assert runtime["device"].error_count == 1
    transport.fail_connect = False
    await runtime["coordinator"].async_refresh()
    await print_label(hass)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("last_error")).attributes == saved
    assert hass.states.get(entity_id("error_count")).state == "1"
    report = hass.states.get(entity_id("print_duration")).attributes
    assert report["success"] is True
    assert "transfer_s" in report
    assert "finish_s" in report
    assert "disconnect_s" in report


async def test_no_radio_is_reported_before_connect(
    hass, loaded_entry, transport, entity_id, monkeypatch
):
    from homeassistant.components import bluetooth

    monkeypatch.setattr(
        bluetooth, "async_ble_device_from_address", lambda *a, **k: None
    )
    before = transport.connections
    with pytest.raises(HomeAssistantError):
        await print_label(hass)
    await hass.async_block_till_done()
    error = hass.states.get(entity_id("last_error"))
    assert error.state == "Unreachable"
    assert error.attributes["failed_stage"] == "unreachable"
    assert transport.connections == before


async def test_query_drop_is_reported_and_reconnects(
    hass, loaded_entry, transport, entity_id
):
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    device = runtime["device"]
    device.keep_connection = True
    await runtime["coordinator"].async_refresh()
    transport.silent = True

    def drop(_writes):
        transport.is_connected = False
        transport._handlers.clear()
        transport.disconnected_callback(transport)

    transport.on_write = drop
    await runtime["coordinator"].async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("last_error")).state == "SessionDropped"
    assert not transport._handlers
    assert device.error_count == 1
    transport.silent = False
    transport.on_write = None
    before = transport.connections
    await runtime["coordinator"].async_refresh()
    assert transport.connections == before + 1


async def test_partial_subscribe_cleanup(hass, loaded_entry, transport):
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    device = runtime["device"]
    original = transport.start_notify

    async def fail_second(uuid, handler):
        if transport._handlers:
            raise BleakError("subscription refused")
        await original(uuid, handler)

    transport.start_notify = fail_second
    await runtime["coordinator"].async_refresh()
    assert not transport._handlers
    assert not device.is_connected
    assert device.reports.last_failure["failed_detail"] == "subscribe"


async def test_cancelled_operation_cleans_up_without_recording_failure(
    hass, loaded_entry, transport
):
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    entered = asyncio.Event()

    async def hanging_write(*args, **kwargs):
        entered.set()
        await asyncio.Event().wait()

    transport.write_gatt_char = hanging_write
    task = asyncio.create_task(runtime["coordinator"].async_refresh())
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not transport._handlers
    assert not runtime["device"].is_connected
    assert runtime["device"].error_count == 0


async def test_transport_failure_does_not_replay_print(hass, loaded_entry, transport):
    before = len(transport.writes)

    async def failed_write(*args, **kwargs):
        raise SessionDropped("transfer")

    transport.write_gatt_char = failed_write
    with pytest.raises(HomeAssistantError):
        await print_label(hass)
    assert len(transport.writes) == before
    device = hass.data[DOMAIN][loaded_entry.entry_id]["device"]
    assert device.error_count == 1
    assert device.reports.last_failure["failed_stage"] == "transfer"


async def test_unanswered_poll_retains_readings_and_reports_timeout(
    hass, loaded_entry, transport, entity_id
):
    transport.silent = True
    runtime = hass.data[DOMAIN][loaded_entry.entry_id]
    await runtime["coordinator"].async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("battery")).state == "85"
    error = hass.states.get(entity_id("last_error"))
    assert error.state == "timeout"
    assert error.attributes["failed_detail"] == "status"


async def test_poll_write_timeout_preserves_transport_error(
    hass, loaded_entry, transport, entity_id, monkeypatch
):
    async def hanging_write(*args, **kwargs):
        await asyncio.Event().wait()

    transport.write_gatt_char = hanging_write
    monkeypatch.setattr(
        client_module, "guarded_write", partial(guarded_write, timeout=0.01)
    )
    await hass.data[DOMAIN][loaded_entry.entry_id]["coordinator"].async_refresh()
    await hass.async_block_till_done()
    error = hass.states.get(entity_id("last_error"))
    assert error.state == "WriteTimeout"
    assert "write" in error.attributes["error"].lower()
    assert not transport._handlers
    assert not transport.is_connected


async def test_gatt_error_becomes_redacted_service_error(
    hass, loaded_entry, transport, entity_id
):
    async def failed_write(*args, **kwargs):
        raise BleakError("GATT write failed for AA:BB:CC:DD:EE:FF")

    transport.write_gatt_char = failed_write
    with pytest.raises(HomeAssistantError, match="Failed to print") as raised:
        await print_label(hass)
    assert "AA:BB:CC:DD:EE:FF" not in str(raised.value)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("last_error")).state == "BleakError"
    assert hass.states.get(entity_id("error_count")).state == "1"
    assert not transport.is_connected
