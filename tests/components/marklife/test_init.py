"""Load and unload the actual integration and all declared platforms."""

from __future__ import annotations

import logging

from bleak.exc import BleakError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er

from custom_components.marklife.const import DOMAIN, PRINT_LOCK


async def test_setup_and_unload(hass, loaded_entry, transport, entity_id):
    entry = loaded_entry
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get(entity_id("battery")).state == "85"
    assert hass.states.get(entity_id("status")).state == "cover_closed"
    assert hass.states.get(entity_id("cover_open", "binary_sensor")).state == "off"
    assert hass.states.get(entity_id("last_label_made", "image")) is not None

    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert len({e.device_id for e in entities}) == 1
    assert transport.connections > 0

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert transport.disconnects > 0
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
    assert PRINT_LOCK not in hass.data


async def test_reload_closes_kept_connection(hass, loaded_entry, transport):
    entry_data = hass.data[DOMAIN][loaded_entry.entry_id]
    original = entry_data["device"]
    original.keep_connection = True
    await entry_data["coordinator"].async_refresh()
    assert original.is_connected

    assert await hass.config_entries.async_reload(loaded_entry.entry_id)
    await hass.async_block_till_done()
    assert not original.is_connected
    new_entry_data = hass.data[DOMAIN][loaded_entry.entry_id]
    assert new_entry_data["device"] is not original


async def test_failed_poll_retains_state_and_recovers(
    hass, loaded_entry, transport, entity_id
):
    entry_data = hass.data[DOMAIN][loaded_entry.entry_id]
    state = hass.states.get(entity_id("battery")).state
    assert state == "85"

    transport.silent = True
    await entry_data["coordinator"].async_refresh()
    await hass.async_block_till_done()
    # State is retained
    assert hass.states.get(entity_id("battery")).state == state

    transport.silent = False
    transport.battery_level = 90
    transport.status_code = 0x01  # out_of_paper
    await entry_data["coordinator"].async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("battery")).state == "90"
    assert hass.states.get(entity_id("status")).state == "out_of_paper"
    assert hass.states.get(entity_id("out_of_paper", "binary_sensor")).state == "on"


async def test_initial_connection_failure_is_recoverable(
    hass, entry, advertisement, transport
):
    transport.fail_connect = True
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert entry.entry_id in hass.data[DOMAIN]
    assert (
        hass.data[DOMAIN][entry.entry_id]["coordinator"].data.sensors["status"] is None
    )


async def test_expected_poll_failures_are_quiet_and_redacted(
    hass, loaded_entry, transport, caplog
):
    async def denied(*_args, **_kwargs):
        raise BleakError("No route to AA:BB:CC:DD:EE:FF")

    transport.write_gatt_char = denied
    with caplog.at_level(logging.DEBUG, logger="custom_components.marklife"):
        for _ in range(2):
            await hass.data[DOMAIN][loaded_entry.entry_id][
                "coordinator"
            ].async_refresh()
        await hass.async_block_till_done()

    own_logs = [r for r in caplog.records if r.name == "custom_components.marklife"]
    assert not [r for r in own_logs if r.levelno >= logging.WARNING]
    assert all("AA:BB:CC:DD:EE:FF" not in r.getMessage() for r in own_logs)


async def test_failed_platform_setup_releases_resources(
    hass, entry, advertisement, transport, monkeypatch
):

    async def fail_forward(*_args, **_kwargs):
        raise RuntimeError("simulated platform load failure")

    monkeypatch.setattr(hass.config_entries, "async_forward_entry_setups", fail_forward)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
    assert PRINT_LOCK not in hass.data
    assert transport.disconnects > 0
