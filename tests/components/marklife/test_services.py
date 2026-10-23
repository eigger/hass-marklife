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

    monkeypatch.setattr(
        bluetooth, "async_ble_device_from_address", lambda *_args, **_kwargs: None
    )

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


async def test_print_schema_preserves_supported_payload(hass, loaded_entry):
    response = await hass.services.async_call(
        DOMAIN,
        "print",
        {
            "payload": [{"type": "text", "value": "Schema", "x": 0, "y": 0}],
            "preview": True,
        },
        blocking=True,
        return_response=True,
    )
    assert response["image"].startswith("data:image/png;base64,")


def test_print_schema_preserves_legacy_string_and_extra_fields():
    """Do not change renderer error handling or remove existing caller data."""
    from custom_components.marklife import PRINT_SCHEMA

    data = {"payload": "legacy string", "device_id": ["device"], "background": "white"}
    assert PRINT_SCHEMA(data) == data


@pytest.mark.parametrize(
    "data",
    [
        {"payload": 42},
        {"payload": [], "width": 0},
        {"payload": [], "height": "invalid"},
    ],
)
async def test_print_schema_rejects_invalid_data(hass, loaded_entry, transport, data):
    import voluptuous as vol

    before = len(transport.writes)
    with pytest.raises(vol.Invalid):
        await hass.services.async_call(DOMAIN, "print", data, blocking=True)
    assert len(transport.writes) == before


async def test_print_legacy_string_keeps_renderer_error(hass, loaded_entry):
    """String payloads keep their existing render failure rather than new parsing."""
    with pytest.raises(
        ServiceValidationError, match="each payload element must be a dict"
    ):
        await hass.services.async_call(
            DOMAIN,
            "print",
            {"payload": "- type: text\n  value: Example", "preview": True},
            blocking=True,
        )
