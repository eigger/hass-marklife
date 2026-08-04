"""Label rendering.

Unchanged from hass-niimbot apart from the font directory: rendering is a
function of the payload and the canvas, not of the printer, so nothing here is
Marklife-specific.
"""

from __future__ import annotations

import os

from homeassistant.components.recorder.history import get_significant_states
from homeassistant.exceptions import HomeAssistantError
from imagespec import RenderContext, RenderError, render


def _make_context(hass, *, default_font, palette):
    def font_resolver(name):
        base_name = os.path.basename(name)

        # 1. Fonts shipped with this integration
        local_path = os.path.join(os.path.dirname(__file__), "fonts", base_name)
        if os.path.exists(local_path):
            return local_path

        # 2. Home Assistant www/fonts
        www_path = os.path.join(hass.config.path("www/fonts"), base_name)
        if os.path.exists(www_path):
            return www_path

        return None

    def history_provider(entity_ids, start, end):
        return get_significant_states(
            hass,
            start_time=start,
            entity_ids=list(entity_ids),
            significant_changes_only=False,
            minimal_response=True,
            no_attributes=False,
        )

    return RenderContext(
        font_resolver=font_resolver,
        history_provider=history_provider,
        default_font=default_font,
        palette=palette,
    )


def render_image(entity_id, service, hass, default_width: int = 384):
    """Render the service payload into a PIL image.

    ``default_width`` is the print head width of the resolved device profile, so
    a payload that omits ``width`` fills the label edge to edge instead of
    defaulting to an arbitrary canvas.
    """
    try:
        return render(
            payload=service.data.get("payload", ""),
            width=service.data.get("width", default_width),
            height=service.data.get("height", 240),
            rotate=service.data.get("rotate", 0),
            rotate_mode="image",  # label printer: variable size, drawing rotates
            background=service.data.get("background", "white"),
            dither=service.data.get("dither", False),
            context=_make_context(hass, default_font="ppb.ttf", palette=["black", "white"]),
        )
    except RenderError as err:
        raise HomeAssistantError(str(err)) from err
