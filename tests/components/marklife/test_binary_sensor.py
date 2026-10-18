"""Test the marklife binary sensor platform."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.marklife.const import DOMAIN


async def test_binary_sensors(hass, loaded_entry, entity_id, transport):
    # Initial state with status cover_closed
    assert hass.states.get(entity_id("cover_open", "binary_sensor")).state == "off"
    assert hass.states.get(entity_id("out_of_paper", "binary_sensor")).state == "off"
    assert hass.states.get(entity_id("overheating", "binary_sensor")).state == "off"
    assert hass.states.get(entity_id("low_battery", "binary_sensor")).state == "off"
    assert hass.states.get(entity_id("connection", "binary_sensor")).state == "off"
    assert hass.states.get(entity_id("printing", "binary_sensor")).state == "off"

    # Status out_of_paper
    transport.status_code = 0x01
    await hass.data[DOMAIN][loaded_entry.entry_id]["coordinator"].async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("out_of_paper", "binary_sensor")).state == "on"
    assert hass.states.get(entity_id("cover_open", "binary_sensor")).state == "off"

    # Status cover_open
    transport.status_code = 0x02
    await hass.data[DOMAIN][loaded_entry.entry_id]["coordinator"].async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("cover_open", "binary_sensor")).state == "on"
    assert hass.states.get(entity_id("out_of_paper", "binary_sensor")).state == "off"

    # Status overheating
    transport.status_code = 0x03
    await hass.data[DOMAIN][loaded_entry.entry_id]["coordinator"].async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("overheating", "binary_sensor")).state == "on"

    # Status low_battery
    transport.status_code = 0x04
    await hass.data[DOMAIN][loaded_entry.entry_id]["coordinator"].async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity_id("low_battery", "binary_sensor")).state == "on"

    # Check device classes
    assert (
        hass.states.get(entity_id("out_of_paper", "binary_sensor")).attributes[
            "device_class"
        ]
        == BinarySensorDeviceClass.PROBLEM
    )
    assert (
        hass.states.get(entity_id("cover_open", "binary_sensor")).attributes[
            "device_class"
        ]
        == BinarySensorDeviceClass.OPENING
    )
    assert (
        hass.states.get(entity_id("overheating", "binary_sensor")).attributes[
            "device_class"
        ]
        == BinarySensorDeviceClass.HEAT
    )
    assert (
        hass.states.get(entity_id("low_battery", "binary_sensor")).attributes[
            "device_class"
        ]
        == BinarySensorDeviceClass.BATTERY
    )
    assert (
        hass.states.get(entity_id("connection", "binary_sensor")).attributes[
            "device_class"
        ]
        == BinarySensorDeviceClass.CONNECTIVITY
    )
    assert (
        hass.states.get(entity_id("printing", "binary_sensor")).attributes[
            "device_class"
        ]
        == BinarySensorDeviceClass.RUNNING
    )
