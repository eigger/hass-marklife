"""Brand image tests.

Since Home Assistant 2026.3.0 a custom component can ship its own brand images
in ``custom_components/<domain>/brand/``, and local files take priority over the
brands CDN. The size rules come from the ``home-assistant/brands`` repository:
icons are square 256x256 (512x512 for hDPI), logos have a shortest side of
128-256 px (256-512 px for hDPI), and images must be trimmed of empty edges.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

BRAND_DIR = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "marklife"
    / "brand"
)

ICON_SIZES = {"icon.png": 256, "dark_icon.png": 256, "icon@2x.png": 512, "dark_icon@2x.png": 512}
LOGO_BOUNDS = {
    "logo.png": (128, 256),
    "dark_logo.png": (128, 256),
    "logo@2x.png": (256, 512),
    "dark_logo@2x.png": (256, 512),
}

ALLOWED = set(ICON_SIZES) | set(LOGO_BOUNDS)


def present(names: dict) -> list[Path]:
    return [BRAND_DIR / name for name in names if (BRAND_DIR / name).is_file()]


def test_brand_directory_exists():
    assert BRAND_DIR.is_dir(), "brand/ directory is missing"


def test_only_recognised_filenames():
    """Home Assistant ignores anything it does not know by name."""
    unexpected = {p.name for p in BRAND_DIR.iterdir() if p.is_file()} - ALLOWED
    assert not unexpected, f"unrecognised brand files: {sorted(unexpected)}"


def test_an_icon_is_shipped():
    """The icon doubles as the logo fallback, so it is the one required file."""
    assert (BRAND_DIR / "icon.png").is_file()


@pytest.mark.parametrize("name", sorted(ICON_SIZES))
def test_icon_dimensions(name):
    path = BRAND_DIR / name
    if not path.is_file():
        pytest.skip(f"{name} not shipped")
    with Image.open(path) as im:
        assert im.format == "PNG"
        assert im.size == (ICON_SIZES[name], ICON_SIZES[name])


@pytest.mark.parametrize("name", sorted(LOGO_BOUNDS))
def test_logo_dimensions(name):
    path = BRAND_DIR / name
    if not path.is_file():
        pytest.skip(f"{name} not shipped")
    low, high = LOGO_BOUNDS[name]
    with Image.open(path) as im:
        assert im.format == "PNG"
        assert low <= min(im.size) <= high, (
            f"{name} shortest side {min(im.size)} outside {low}-{high}"
        )


@pytest.mark.parametrize("path", present(ALLOWED), ids=lambda p: p.name)
def test_images_are_trimmed(path):
    """No transparent or single-colour border around the subject."""
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
        bbox = rgba.getbbox()
        assert bbox == (0, 0, *rgba.size), f"{path.name} has empty edges: {bbox}"


@pytest.mark.parametrize("path", present(ALLOWED), ids=lambda p: p.name)
def test_hdpi_matches_its_base_image(path):
    """An @2x file must be double the base file, not a different picture."""
    if "@2x" not in path.name:
        pytest.skip("base image")
    base = BRAND_DIR / path.name.replace("@2x", "")
    if not base.is_file():
        pytest.skip("no base image shipped")
    with Image.open(path) as hdpi, Image.open(base) as normal:
        assert hdpi.size == (normal.width * 2, normal.height * 2)
