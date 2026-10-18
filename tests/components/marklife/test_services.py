"""Test the marklife.print service."""

from __future__ import annotations

import base64
import io

import pytest
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr
from PIL import Image

from custom_components.marklife.const import DOMAIN, PRINT_LOCK


async def test_print_service_preview(hass, loaded_entry, transport, entity_id):
    before = len(transport.writes)
    response = await hass.services.async_call(
        DOMAIN,
        "print",
        {
            "preview": True,
            "payload": [{"type": "text", "value": "Test", "x": 10, "y": 10}],
            "width": 384,
            "height": 96,
        },
        blocking=True,
        return_response=True,
    )
    assert response is not None
    assert "image" in response
    assert response["image"].startswith("data:image/png;base64,")
    assert len(transport.writes) == before

    image_bytes = base64.b64decode(response["image"].split(",")[1])
    with Image.open(io.BytesIO(image_bytes)) as img:
        assert img.size == (384, 96)

    # image entity should be updated
    img_entity = entity_id("last_label_made", "image")
    assert hass.states.get(img_entity) is not None


async def test_print_service_actual_print(hass, loaded_entry, transport, entity_id):
    devices = dr.async_entries_for_config_entry(
        dr.async_get(hass), loaded_entry.entry_id
    )
    assert devices
    device = devices[0]

    response = await hass.services.async_call(
        DOMAIN,
        "print",
        {
            "payload": [{"type": "text", "value": "Print Me", "x": 10, "y": 10}],
            "width": 384,
            "height": 96,
            "copies": 1,
            "paper_type": "gap",
        },
        target={"device_id": device.id},
        blocking=True,
        return_response=True,
    )
    assert response is not None
    assert response["status"] == "ok"
    assert "image" in response
    assert transport.writes


async def test_print_service_validation_error(hass, loaded_entry):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "print",
            {
                # Missing required 'x' and 'y' in text element
                "payload": [{"type": "text", "value": "Missing XY"}],
            },
            blocking=True,
        )


async def test_print_service_target_unconfigured(hass):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "print",
            {
                "preview": True,
                "payload": [{"type": "text", "value": "Test", "x": 0, "y": 0}],
            },
            blocking=True,
        )


async def test_print_service_device_not_found_on_bluetooth(
    hass, loaded_entry, monkeypatch
):
    from homeassistant.components import bluetooth

    monkeypatch.setattr(bluetooth, "async_ble_device_from_address", lambda *_args: None)

    with pytest.raises(HomeAssistantError) as excinfo:
        await hass.services.async_call(
            DOMAIN,
            "print",
            {
                "payload": [{"type": "text", "value": "Test", "x": 0, "y": 0}],
                "width": 384,
                "height": 96,
            },
            blocking=True,
        )
    assert "**REDACTED**" in str(excinfo.value)
    assert loaded_entry.unique_id not in str(excinfo.value)


async def test_unload_removes_service_when_last_entry(hass, loaded_entry):
    assert hass.services.has_service(DOMAIN, "print")
    assert PRINT_LOCK in hass.data

    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    await hass.async_block_till_done()

    assert not hass.services.has_service(DOMAIN, "print")
    assert PRINT_LOCK not in hass.data
