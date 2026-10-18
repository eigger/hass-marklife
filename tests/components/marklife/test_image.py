"""Test the marklife image platform."""

from __future__ import annotations

import io

from PIL import Image

from custom_components.marklife.const import DOMAIN


async def test_image_entity(hass, loaded_entry, entity_id, transport):
    img_entity = entity_id("last_label_made", "image")
    state = hass.states.get(img_entity)
    assert state is not None
    assert state.state not in ("unavailable",)

    # Trigger a print preview to update image
    response = await hass.services.async_call(
        DOMAIN,
        "print",
        {
            "preview": True,
            "payload": [{"type": "text", "value": "Preview Label", "x": 0, "y": 0}],
            "width": 384,
            "height": 96,
        },
        blocking=True,
        return_response=True,
    )
    assert response is not None
    assert "image" in response
    await hass.async_block_till_done()

    new_state = hass.states.get(img_entity)
    assert new_state is not None
    assert new_state.state != "unavailable"

    # Verify image data can be retrieved from component
    image_coordinator = hass.data[DOMAIN][loaded_entry.entry_id]["image_coordinator"]
    img_obj, ble_data = image_coordinator.data
    assert img_obj.content_type == "image/png"
    assert len(img_obj.content) > 0
    with Image.open(io.BytesIO(img_obj.content)) as im:
        assert im.format == "PNG"
        assert im.size == (384, 96)
