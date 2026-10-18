"""Test the marklife sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.marklife.const import DOMAIN


async def test_sensors(hass, loaded_entry, entity_id, transport):
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    devices = dr.async_entries_for_config_entry(dev_reg, loaded_entry.entry_id)
    assert len(devices) == 1
    device = devices[0]
    assert device.manufacturer == "Marklife"
    assert device.model == "P15"
    assert device.sw_version == "1.0.0"
    assert device.serial_number == "ML123456"

    # Battery sensor
    battery_id = entity_id("battery")
    battery_state = hass.states.get(battery_id)
    assert battery_state is not None
    assert battery_state.state == "85"
    assert battery_state.attributes["unit_of_measurement"] == PERCENTAGE
    assert battery_state.attributes["device_class"] == SensorDeviceClass.BATTERY

    battery_entry = ent_reg.async_get(battery_id)
    assert battery_entry is not None
    assert battery_entry.unique_id.endswith("_battery")
    assert battery_entry.device_id == device.id

    # Status sensor
    status_id = entity_id("status")
    status_state = hass.states.get(status_id)
    assert status_state is not None
    assert status_state.state == "cover_closed"
    assert status_state.attributes["device_class"] == SensorDeviceClass.ENUM
    assert "out_of_paper" in status_state.attributes["options"]

    # Print duration sensor
    duration_id = entity_id("print_duration")
    duration_state = hass.states.get(duration_id)
    assert duration_state is not None
    assert duration_state.state == "0.0"
    assert duration_state.attributes["unit_of_measurement"] == UnitOfTime.SECONDS
    assert duration_state.attributes["device_class"] == SensorDeviceClass.DURATION

    # Update through coordinator
    transport.battery_level = 72
    transport.status_code = 0x01  # out_of_paper
    await hass.data[DOMAIN][loaded_entry.entry_id]["coordinator"].async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(battery_id).state == "72"
    assert hass.states.get(status_id).state == "out_of_paper"
