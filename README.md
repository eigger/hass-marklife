# hass-marklife

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?logo=home-assistant)](https://hacs.xyz/)
[![GitHub Release](https://img.shields.io/github/release/eigger/hass-marklife.svg)](https://github.com/eigger/hass-marklife/releases)
[![License](https://img.shields.io/github/license/eigger/hass-marklife)](https://github.com/eigger/hass-marklife/blob/main/LICENSE)

Marklife Label Printer Home Assistant Integration

BLE protocol layer ported from [tomLadder/thermoprint](https://github.com/tomLadder/thermoprint) (MIT).

> [!CAUTION]
> **No printer has been tested yet — not one model.**
>
> Every entry in [Supported Models](#supported-models) is marked *untested*, and
> that is literal: the protocol layer is a port that passes unit tests against
> the documented wire format, but it has never driven a physical Marklife
> printer. Treat this as a starting point for testing, not a working
> integration.
>
> If you own any of these printers, [a report either way](https://github.com/eigger/hass-marklife/issues)
> is the single most useful thing you can contribute right now — including
> "it printed nothing and here is the debug log".

## Feedback & Support

- Found a bug? [Open an issue](https://github.com/eigger/hass-marklife/issues)
- Have a printer to test with? Please say so in an issue — see [Reporting a test](#reporting-a-test)

---

## Supported Models

Two BLE protocol families cover every Marklife printer Home Assistant can reach.
**Status is confidence in the port, not evidence of it working.**

| Model | Family | Print head | Status |
|-------|--------|-----------|--------|
| P15, P15R, P15S | L11 | 384 px | untested — protocol proven in thermoprint |
| P7, P7R | L11 | 384 px | untested — protocol proven in thermoprint |
| P12, P11 | L11 | 384 px | untested — protocol proven in thermoprint |
| P1s, M1, S15, S12, LP15, LP90, LPC74, iSPACE_LP15, OUT_LPC | L11 | 384 px | untested — mapped to the P15/P12 profile by the vendor app |
| M60, X2 | Compressed | 384 px (unverified) | untested — protocol proven in thermoprint |
| P50, P50S, D50, ewtto ET- | Compressed | unverified | untested — profile inferred from APK notes |
| P80, T3 | Compressed | unverified | untested — **no flow control**, see below |

### Not supported, and never will be

| Models | Why |
|--------|-----|
| S8, D210, 210, IP_D80, DP_D80, DP_8028, HM-24-28, A31, U210, A50, X8 | Bluetooth Classic **SPP (RFCOMM)**. bleak has no RFCOMM support, and an ESPHome Bluetooth proxy is BLE-only hardware. There is no path from Home Assistant's Bluetooth stack to these printers. |
| D100, X4, L100, D200 | Driven by a closed third-party Android library with no documented wire protocol. |

These are still in the device registry so the config flow can tell you *why* a
printer you can see in the Marklife app will not appear here, instead of
silently ignoring it.

---

## Installation

1. Install with HACS (custom repository required), or copy this repo into `custom_components/marklife`.
2. Restart Home Assistant.
3. Go to **Settings** → **Integrations** and add **Marklife**.
4. Select a discovered printer from the list.

### Automatic discovery

Home Assistant selects candidates by **advertised Bluetooth name**; the
integration then corroborates each one against the advertised **service UUID**
where possible — see [Service UUID as a second signal](#service-uuid-as-a-second-signal).

Home Assistant's matcher requires at least **three literal characters before any
wildcard**, so models with a two-character prefix (`P7`, `M1`, `S2`, `X2`, `T3`)
are listed with their separator instead — `P7R*`, `P7-*`, `P7_*`, `M1-*`, and so
on. Those separators are educated guesses: no advertised name for these models
has been observed yet.

Name matching in the manifest is also **case-sensitive** (Home Assistant
compiles the patterns with `fnmatch.translate`), which is why both `P1s*` and
`P1S*` are listed. The device registry inside the integration matches
case-insensitively, so only the manifest needs the duplicate.

### Adding a printer manually

If nothing is discovered automatically, **Add integration** → **Marklife** does
not dead-end. When no visible device matches a known name prefix, the flow falls
through to a manual step that lists **every** Bluetooth device Home Assistant
can currently see — and lets you type an address directly if the printer is not
even in that list.

The manual step also asks for the **printer model**, and that part is not
optional. Marklife printers have no model-ID query: the advertised name is the
only thing that identifies them over the air. Once the name matches nothing,
there is no way to infer which protocol, packet size, or darkness command to
use, so you have to say. A manually chosen model always wins over name matching.

If you end up here, please
[report the exact advertised name](https://github.com/eigger/hass-marklife/issues)
so the matcher can be fixed for everyone.

#### Service UUID as a second signal

A short prefix is weak evidence. Unrelated hardware can advertise as `M1-…` or
`S2-…` and would then be offered as a printer, so the integration also checks
the **service UUID** carried in the advertisement.

The check is one-sided on purpose:

| Advertisement | Result |
|---|---|
| Lists service UUIDs, ours among them | Discovered |
| Lists service UUIDs, ours absent | **Rejected** — name collision |
| Lists no service UUIDs at all | Discovered (silence is not evidence) |

This runs in the config flow rather than the manifest, and only for *automatic*
discovery. Adding a printer manually stays permissive — you picked it
deliberately.

**Why not put `service_uuid` in the manifest?** It would work: Home Assistant
ANDs every field in a matcher, so `{"local_name": "M1-*", "service_uuid": "…"}`
requires both. The problem is that it is all-or-nothing — if these printers turn
out **not** to advertise their service, automatic discovery breaks completely,
with no signal to distinguish that from having no printer nearby.

And whether they advertise it is genuinely unknown. thermoprint matches by name
in both of its transports, and the vendor Android app filters by
`name.startsWith(...)` and RSSI only — but neither proves the UUID is absent
from the advertisement, it only shows the authors chose not to rely on it. The
config-flow check gets the same protection while degrading to name-only matching
when the data is unavailable.

**Finding out for real.** Enable [debug logging](#reporting-a-test) and the
integration logs the advertised name and service UUIDs for every candidate:

```
Advertised name 'P15-A1B2', service UUIDs ['0000ff00-0000-1000-8000-00805f9b34fb']
```

If real printers do advertise `0000ff00-…`, moving the check into the manifest
becomes safe and strictly better — it stops Home Assistant from even creating a
config flow for a colliding device. [Report what you see](https://github.com/eigger/hass-marklife/issues).

One caveat either way: `0000ff00-…` is an unassigned vendor-range 16-bit UUID
that many cheap BLE devices reuse, and the P80/T3 fallback service
`49535343-…` is Microchip's stock transparent-UART service. Combined with a
model-specific name prefix they are a useful filter; neither identifies a
Marklife printer on its own.

### Brand icon and logo

Since Home Assistant **2026.3.0** a custom component can ship its own brand
images — no PR to the `home-assistant/brands` repository needed. Drop them in a
`brand/` folder next to `manifest.json` and they take priority over the brands
CDN:

```
custom_components/marklife/
├── manifest.json
└── brand/
    ├── icon.png       256×256, square
    ├── icon@2x.png    512×512, square
    ├── logo.png       shortest side 128–256 px
    └── logo@2x.png    shortest side 256–512 px
```

`dark_icon.png` / `dark_logo.png` (and their `@2x` variants) are optional. All
files must be PNG, compressed, and trimmed of surrounding empty space.

This repository ships `icon.png`, `icon@2x.png`, `logo.png` and `logo@2x.png`,
all derived from the official Marklife app icon (Shenzhen Yinxiaoqian Technology
Co. Ltd., the same publisher as the vendor app this integration's protocol was
reverse-engineered from).

The source matters more than the output size here. Apple's App Store CDN serves
this icon at 1024 px, but that render is itself upscaled — its red/white edges
ramp over 3 px (up to 11), and a flat two-colour mark stored as 2,678 distinct
colours is the giveaway. Google Play serves the developer's native 512 px asset,
where the same edges ramp over 1 px. The artwork here comes from Play.

Two clean-ups are then applied. The mark is a red disc drawn on a white page, so
its outer 6 px are a light pink anti-aliasing ramp; compositing the disc over its
own fill colour through a mask inset past that ramp gives a solid brand-red edge
with only the alpha feathered, instead of a pale halo on dark backgrounds. And
because the art is flat two-colour, it is upscaled to 2048 px, every pixel is
snapped to whichever of the two colours is nearer, and the result is downsampled
— which turns the source's residual blur back into clean anti-aliasing. The
proportion of pixels that are neither brand red nor white drops from 3.8 % to
2.2 %.

The wordmark published on the Marklife site is not usable as `logo.png`: at
176 × 71 px with a 157 × 37 px subject it would need roughly a 3.5× upscale to
clear the 128 px minimum and would look visibly soft. The logo is built from the
icon instead — a landscape canvas in the mark's own red with the white figure
centred at its natural ratio. A full-bleed brand colour reads on both the light
and dark themes and leaves no empty margin, which a square mark padded into a
landscape frame otherwise would.

The Marklife name and mark are trademarks of their owner, used here for
identification only — the convention the brands repository sets out.

`tests/test_brand.py` checks the size, format and trimming rules, so a
replacement image that breaks them fails before it ships.

## Important Notice

It is **strongly recommended to use a Bluetooth proxy** instead of a built-in
Bluetooth adapter for more stable connections and better range.

> [!TIP]
> Hardware recommendations: [Great ESP32 Board for an ESPHome Bluetooth Proxy](https://community.home-assistant.io/t/great-esp32-board-for-an-esphome-bluetooth-proxy/916767/31)

```yaml
esp32_ble_tracker:
  scan_parameters:
    active: true

bluetooth_proxy:
  active: true
```

An ESP32 proxy supports **three concurrent BLE connections**. Each poll opens
one, so keep the scan interval long and leave **Keep BLE connection open** off
unless you print frequently.

---

## Options

Setup asks only what you can answer without knowing the hardware. The protocol
knobs all have working defaults — the one that matters is already derived from
the model — and live in **Settings** → **Devices & Services** → **Marklife** →
**Configure**, for when a printer actually misbehaves.

**Asked during setup:**

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| **Scan interval** | 600 | 30–9999 s | How often to poll battery and status |
| **Keep BLE connection open** | Off | On/Off | Holds a connection between jobs — and a proxy connection slot |

**Configure dialog only:**

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| **Packet interval** | 0 | 0–200 ms | Minimum gap between packets. `0` uses the device profile — 30 ms for most models, 1 ms for M60/X2 |
| **Credit starvation timeout** | 2000 | 500–10000 ms | How long to wait for a flow-control credit before forcing one |
| **Max packet size** | 180 | 20–237 B | Upper bound regardless of the negotiated MTU |

There is no sound setting: unlike Niimbot, whose `0x58` command toggles the
connection and power beeps, the Marklife command set has nothing for the buzzer
in either protocol family.

### Why these defaults differ from the vendor app

Marklife printers use **credit-based flow control**: the printer grants credits
on a dedicated BLE characteristic and each outbound packet spends one. This is a
closed loop, which makes it well suited to a Bluetooth proxy — if the link is
slow, credits arrive slowly and the sender simply waits. No manual
tuning of a fixed per-packet delay is required.

The one escape hatch is **starvation recovery**: after silence, one credit is
forced so a stalled job can limp forward. That breaks the loop, and forcing data
at a printer that has not asked for it is what corrupts a label. The vendor app
waits 1000 ms with a direct phone-to-printer link; over a proxy the credit
notification takes an extra network hop, so the default here is **2000 ms**.

If prints come out with missing bands or stop partway, **raise the starvation
timeout first**, then lower the max packet size. Leave the packet interval at
`0` unless that fails too — at `0` it already follows the device profile, which
is the value the vendor app uses for that model.

---

## Payload & rendering (`imagespec`)

Labels are rendered with **[imagespec](https://github.com/eigger/imagespec)** —
a declarative YAML/JSON list of drawing elements that becomes a bitmap sent to
the printer.

| Topic | Link |
|-------|------|
| Element examples with preview images | [imagespec/docs/elements.md](https://github.com/eigger/imagespec/blob/main/docs/elements.md) |
| All element fields & defaults | [imagespec README — Element Reference](https://github.com/eigger/imagespec#elements-reference) |
| Layout, palette, LLM authoring guide | [imagespec/docs/authoring.md](https://github.com/eigger/imagespec/blob/main/docs/authoring.md) |

**Marklife-specific behaviour:**

- **Palette:** black & white only. Off-palette colors are quantized to the nearest supported color.
- **Rotation:** `rotate: 90/180/270` rotates the drawing and **swaps output width/height** (label-printer mode).
- **Default width:** omit `width` and the canvas matches the print head (384 dots on every profile so far). Anything wider is scaled down rather than truncated.
- **Orientation:** the raster's **width runs across the print head**, its height is the feed direction — and on a die-cut roll the label's *short* side is the one across the head. So a 40 × 12 mm label is **96 px wide by 320 px tall**, not the other way round. Author it in reading orientation and let `rotate: 90` swap the axes (see [Label orientation](#label-orientation)).
- **Sizing in millimetres:** all these printers are 203 dpi, i.e. **8 dots per mm**. The 384-dot head is 48 mm wide.
- **Default font:** `ppb.ttf` in `custom_components/marklife/fonts/`. Custom fonts also work from `www/fonts/`.
- **`plot` element:** reads history from Home Assistant **Recorder**.
- **`dither`:** set on the service call to halftone photos/charts. Keep text and barcodes undithered for sharp edges — see [imagespec dithering docs](https://github.com/eigger/imagespec#dithering).
- **Layout:** prefer `row` / `column` / `stack` over hand-calculated coordinates.

---

## Service: `marklife.print`

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `payload` | yes | — | List of [imagespec elements](https://github.com/eigger/imagespec/blob/main/docs/elements.md) |
| `width` | no | print head width | Canvas width in pixels |
| `height` | no | `240` | Canvas height in pixels |
| `rotate` | no | `0` | `0`, `90`, `180`, or `270` |
| `density` | no | profile default | Print darkness 1–3 |
| `paper_type` | no | `gap` | `gap` advances to the next die-cut label; `continuous` feeds a fixed distance |
| `copies` | no | `1` | Number of identical labels |
| `dither` | no | `false` | Halftone the whole label while rendering |
| `preview` | no | `false` | Render only; do not send to the printer |

Use `response_variable` in scripts to receive the generated image as a `data:`
URL. The response also carries `status`, `duration`, `width`, `height`, and
`copies`.

> [!NOTE]
> Density is **1–3**, and the scale is per-family: the P15 sets darkness with a
> different command than the P12, and M60 remaps 1/2/3 onto 3/8/14 internally.
> Use 1–3 and let the device profile translate.

### Basic example

```yaml
action: marklife.print
target:
  device_id: <your device>
data:
  payload:
    - type: text
      value: Hello World!
      font: ppb.ttf
      x: 10
      y: 10
      size: 40
    - type: qrcode
      data: "https://www.home-assistant.io"
      x: 270
      y: 10
      width: 80
      height: 80
  width: 384
  height: 96
```

### 40 × 12 mm gap label (P15 default media)

Design in reading orientation and rotate — `rotate: 90` swaps the output axes, so
the 12 mm side ends up across the print head:

```yaml
action: marklife.print
target:
  device_id: <your device>
data:
  payload:
    - type: text
      value: "Pantry"
      font: ppb.ttf
      x: 8
      y: 20
      size: 48
  width: 320      # 40 mm x 8 dots/mm — the long side, along the feed
  height: 96      # 12 mm x 8 dots/mm — the short side, across the head
  rotate: 90      # -> 96 x 320 raster
  paper_type: gap
  density: 2
```

### Label orientation

The raster goes to the printer with its **width across the print head** and its
height as the feed direction. On a die-cut roll the roll's width is the label's
short side, so that short side is what spans the head — a 40 × 12 mm label is
12 mm across the head and 40 mm of feed.

Writing that canvas directly (`width: 96, height: 320`) means composing sideways,
so the practical pattern is the one above: give the label's natural
`width` × `height` and add `rotate: 90`.

That works because the renderer runs imagespec in **`rotate_mode="image"`**,
where the drawing is rotated and the **output dimensions swap** — 320 × 96
becomes 96 × 320. The other mode, `"canvas"`, pre-swaps the working canvas and
rotates it back so the output keeps its requested size; that is what a
fixed-resolution e-ink panel needs and it would be wrong here, handing the
printer a 320 × 96 raster and printing the label sideways.

The direction lines up too: imagespec applies `rotate(-90)`, which is 90°
**clockwise**, the same way thermoprint's editor rotates its design canvas
before sending. A mismatch would print every label upside down.

Nothing here is per-model. Every Marklife printer Home Assistant can reach has
the same 384-dot head and the same raster convention, so unlike Niimbot — whose
model table tags the small 96–192 dot printers with a `LEFT` print direction —
there is no device-dependent orientation to resolve.

The raster is also sent at its natural width rather than padded out to 384 dots.
That matches thermoprint's editor, which notes that the printer handles
positioning and that padding would quadruple the data for narrow labels.

### Continuous media

```yaml
action: marklife.print
target:
  device_id: <your device>
data:
  payload:
    - type: text
      value: "{{ now().strftime('%Y-%m-%d %H:%M') }}"
      x: 8
      y: 8
      size: 32
  height: 64
  paper_type: continuous
```

### Preview without printing

Use **`preview: true`** while designing labels so nothing is sent to the
printer. Every print or preview updates `image.<device>_last_label_made`.

```yaml
action: marklife.print
target:
  device_id: <your device>
data:
  preview: true
  payload:
    - type: text
      value: Preview Test
      x: 10
      y: 10
      size: 30
  width: 384
  height: 96
```

---

## Entities

| Entity | Notes |
|--------|-------|
| `sensor.<device>_battery` | Percentage |
| `sensor.<device>_status` | `out_of_paper`, `cover_open`, `overheating`, `low_battery`, `cover_closed` |
| `sensor.<device>_print_duration` | Live during a job, final total after |
| `binary_sensor.<device>_out_of_paper` / `_cover_open` / `_overheating` / `_low_battery` | Derived from the status code |
| `binary_sensor.<device>_connection` / `_printing` | Connection and job state |
| `image.<device>_last_label_made` | Last label printed or previewed |

Marklife printers report **one condition at a time** as a status code, not a
bitfield, so exactly one fault sensor is on at a time. There is no RFID,
label-type, or paper-remaining data available on these printers.

---

## Custom fonts

Place `.ttf` files in `custom_components/marklife/fonts/` or
`config/www/fonts/` and reference by filename (e.g. `ppb.ttf`, `rbm.ttf`).

---

## Architecture

```
custom_components/marklife/
├── __init__.py          coordinator, print service, image preview
├── config_flow.py       discovery + options
├── sensor.py            battery, status, print duration
├── binary_sensor.py     faults, connection, printing
├── image.py             last label rendered
├── render.py            imagespec payload -> PIL image
└── marklife_ble/        protocol layer — no Home Assistant imports
    ├── client.py        notification routing, print orchestration
    ├── flow.py          credit-based flow control
    ├── parser.py        connection ownership, BLEData snapshot
    ├── imaging.py       PIL -> 1bpp raster
    ├── models.py        DeviceProfile + longest-prefix registry
    ├── profiles/        per-model data (l11, compressed, unsupported)
    └── protocols/       l11, compressed, shared queries
```

**Image pipeline:** PIL image → invert → Floyd-Steinberg → 1bpp MSB-first pack.
PIL's `convert("1")` and `tobytes()` produce byte-identical output to
thermoprint's hand-written pipeline, so 130 lines of TypeScript collapse into
two calls.

**Protocol split:** the two families differ only in the print sequence and
bitmap encoding. Battery, status, model, firmware, serial, MAC, and BT queries
are transport-level and shared — thermoprint duplicates them per family; here
they live in one mixin.

**Device resolution:** Marklife printers expose no model-ID query, so the
advertised BLE name is the only handle. Prefixes are matched **longest first**
because `P1s`/`P11`/`P12` and `P15`/`P15R`/`P15S` overlap.

Adding a printer is a data change: one `DeviceProfile` in `profiles/`.

### Running the tests

The `marklife_ble/` package has no Home Assistant dependency and is tested standalone:

```bash
python3 -m pytest tests/ -q
```

---

## Verification status

Ordered by confidence. Nothing below has been run against real hardware **by
this project**.

| Area | Status |
|------|--------|
| L11 print path (P15/P12/P7) | Byte-compared against thermoprint, which runs it on real hardware |
| Compressed print path (M60) | Byte-compared against thermoprint, which runs it on real hardware |
| Credit flow control | Unit-tested including starvation recovery and the no-credit path |
| Image pipeline | Unit-tested for packing, padding, and print-head fitting |
| Connection lifecycle, proxy pacing | **Never executed** — needs hardware |
| P50 / P80 / S2 profiles | **Never executed.** Sequence documented and shared with M60; packet sizes from the APK notes; print head widths are guesses, marked `TODO(unverified)` in the source |
| P80 / T3 flow control | **Never executed.** These sit on the fallback service UUID with no credit characteristic, so pacing degrades to a fixed interval with no feedback |
| Print head widths for M60/P50/P80 | Inferred — thermoprint records label sizes in millimetres only, never the dot count |

## Reporting a test

Enable debug logging first:

```yaml
logger:
  default: warning
  logs:
    custom_components.marklife: debug
```

This logs every packet, credit grant, MTU announcement, and the built command
sequence. Useful in a report:

- Printer model and the exact name it advertises over Bluetooth
- Local adapter or ESPHome proxy (and the ESPHome version)
- What the label actually did — nothing, partial, banded, garbled, correct
- The debug log around the print attempt

---

## References

- [imagespec](https://github.com/eigger/imagespec) — rendering engine
- [tomLadder/thermoprint](https://github.com/tomLadder/thermoprint) — protocol core and APK reverse-engineering notes
