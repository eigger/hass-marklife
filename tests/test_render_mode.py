"""Rotation convention guard.

imagespec offers two rotation modes and the right one depends on the device:

* ``rotate_mode="canvas"`` — the working canvas is pre-swapped to
  ``(height, width)``, drawn on, then rotated back, so the **output keeps the
  requested width × height**. Correct for a fixed-resolution e-ink panel, where
  the pixel grid cannot change.
* ``rotate_mode="image"`` — the canvas is created at ``width × height``, drawn
  on, then the whole image is rotated, so the **output dimensions swap**.
  Correct for a label printer, where the feed length is free.

Marklife printers are label printers: the raster's width spans the 384-dot head
and its height is however far the paper feeds. Turning a 40 × 12 mm design into
the 96 × 320 raster the printer wants *requires* the dimensions to swap, so
``"image"`` is the only mode that works. ``"canvas"`` would hand back a
320 × 96 raster and the label would print rotated.

This is easy to get wrong by copying a renderer from a sibling e-ink
integration, hence the guard: the modules are otherwise nearly identical.
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw

RENDER_PY = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "marklife"
    / "render.py"
)


def test_renderer_uses_image_rotation_mode():
    source = RENDER_PY.read_text(encoding="utf-8")
    match = re.search(r'rotate_mode\s*=\s*"([a-z]+)"', source)
    assert match, "render.py does not set rotate_mode at all"
    assert match.group(1) == "image", (
        f'rotate_mode is "{match.group(1)}"; a label printer needs "image" so the '
        "output dimensions swap on a 90 degree rotation"
    )


def test_rotate_is_passed_through_to_imagespec():
    source = RENDER_PY.read_text(encoding="utf-8")
    assert 'service.data.get("rotate"' in source


def test_image_mode_swaps_dimensions_but_canvas_mode_does_not():
    """Pin down the behaviour this integration depends on.

    Mirrors what imagespec does internally: build the canvas, then
    ``img.rotate(-rotate, expand=True)``.
    """
    W, H = 320, 96

    # image mode: canvas at width x height, rotate the finished drawing
    image_mode = Image.new("RGB", (W, H), "white").rotate(-90, expand=True)
    assert image_mode.size == (H, W), "image mode must swap the output dimensions"

    # canvas mode: canvas pre-swapped, rotated back, output unchanged
    canvas_mode = Image.new("RGB", (H, W), "white").rotate(-90, expand=True)
    assert canvas_mode.size == (W, H), "canvas mode must preserve the output size"


def test_rotate_90_turns_clockwise():
    """thermoprint's editor rotates its design canvas 90 degrees clockwise.

    imagespec applies ``rotate(-90)``, and PIL rotates counter-clockwise for
    positive angles, so a negative angle is clockwise -- the same direction.
    A mismatch here would print every label upside down.
    """
    img = Image.new("RGB", (320, 96), "white")
    ImageDraw.Draw(img).rectangle((0, 0, 40, 20), fill="black")  # top-left marker
    out = img.rotate(-90, expand=True)

    px = out.load()
    w, h = out.size
    assert px[w - 6, 5] == (0, 0, 0), "marker should land top-right (clockwise)"
    assert px[5, 5] != (0, 0, 0)
