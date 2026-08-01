"""Image -> 1bpp raster conversion.

Replaces thermoprint's grayscale.ts + dither.ts + pack.ts. PIL already does all
three steps: ``convert("1")`` applies Floyd-Steinberg dithering, and ``tobytes()``
on a mode ``"1"`` image yields MSB-first rows padded to byte boundaries -- byte
for byte identical to thermoprint's ``packBits()``.

The one difference is that thermoprint uses a serpentine (bidirectional) FS
variant while PIL's is unidirectional. That changes the dither pattern very
slightly; it does not change output quality.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageOps


@dataclass(frozen=True, slots=True)
class Bitmap1bpp:
    """A packed monochrome raster ready to hand to a protocol encoder.

    Bit set (1) means black/ink, MSB is the leftmost pixel, and every row starts
    on a byte boundary.
    """

    data: bytes
    width: int
    height: int
    bytes_per_row: int

    def __post_init__(self) -> None:
        expected = self.bytes_per_row * self.height
        if len(self.data) != expected:
            raise ValueError(
                f"raster is {len(self.data)} bytes, expected {expected} "
                f"({self.bytes_per_row} x {self.height})"
            )


def to_raster(
    image: Image.Image,
    *,
    dither: bool = True,
    threshold: int = 128,
) -> Bitmap1bpp:
    """Convert a PIL image into a printer-ready 1bpp raster."""
    # Invert first so that dark source pixels become high values, then mode "1"
    # packs "high" as a set bit -- i.e. 1 = ink. Same trick hass-niimbot uses.
    gray = ImageOps.invert(image.convert("L"))
    if dither:
        bw = gray.convert("1")
    else:
        cutoff = 255 - threshold
        bw = gray.point(lambda p: 255 if p > cutoff else 0, mode="1")

    return Bitmap1bpp(
        data=bw.tobytes(),
        width=bw.width,
        height=bw.height,
        bytes_per_row=-(-bw.width // 8),
    )


def fit_to_printhead(image: Image.Image, printhead_px: int) -> Image.Image:
    """Clamp an image to the print head width.

    The print head is a fixed number of dots wide (384 for most Marklife
    models). Anything wider is silently truncated by the printer, so scale it
    down instead and keep the aspect ratio.
    """
    if image.width <= printhead_px:
        return image
    height = max(1, round(image.height * printhead_px / image.width))
    return image.resize((printhead_px, height), Image.LANCZOS)
