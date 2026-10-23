# Marklife User Guide

[Home](../README.md) | [한국어](ko/user-guide.md)

Detailed reference for supported models, options, entities, services, and `imagespec` label templates preserved from the integration documentation.

## Gallery

| P15 |
| :---: |
| <img src="images/p15.jpg" width="300" alt="Marklife P15"> |

> BLE protocol layer ported from [tomLadder/thermoprint](https://github.com/tomLadder/thermoprint) (MIT).
> [Stash](https://github.com/eigger/stash) can print labels via this Home Assistant integration.

---

## Supported Models

Two BLE protocol families cover every Marklife printer Home Assistant can reach.
**Status reflects implementation coverage; verify physical operation on your device.**

| Model | Family | Print head | Status |
|---|---|---|---|
| P15, P15R, P15S | L11 | 384 px | ✅ P15 confirmed working |
| P7, P7R | L11 | 384 px | untested — protocol proven in thermoprint |
| P12, P11 | L11 | 384 px | untested — protocol proven in thermoprint |
| P1s, M1, S15, S12, LP15, LP90, LPC74, iSPACE_LP15, OUT_LPC | L11 | 384 px | untested — mapped to the P15/P12 profile by the vendor app |
| M60, X2 | Compressed | 384 px (unverified) | untested — protocol proven in thermoprint |
| P50, P50S, D50, ewtto ET- | Compressed | unverified | untested — profile inferred from APK notes |
| P80, T3 | Compressed | unverified | untested — **no flow control** |

### Unsupported Hardware

| Models | Why |
|---|---|
| S8, D210, 210, IP_D80, DP_D80, DP_8028, HM-24-28, A31, U210, A50, X8 | These use Bluetooth Classic, which is not supported by Home Assistant's Bluetooth stack or ESPHome proxies. |
| D100, X4, L100, D200 | These use a closed, proprietary communication protocol that cannot currently be supported. |

If you attempt to add an unsupported model, the integration will explicitly inform you that the transport is unsupported rather than failing silently.

---

## Configuration & Options

Most settings have sensible defaults based on your printer model. To adjust them, go to **Settings** → **Devices & Services** → **Marklife** → **Configure**.

### Setup Options

| Option | Default | Range | Description |
|---|---|---|---|
| **Scan interval** | 600 | 30–9999 s | How often to poll battery and status |
| **Keep BLE connection open** | Off | On/Off | Holds a connection between jobs (reserves a proxy connection slot) |

### Advanced Options (Configure Dialog)

| Option | Default | Range | Description |
|---|---|---|---|
| **Packet interval** | 0 | 0–200 ms | Minimum gap between packets. `0` uses the device profile (30 ms for most models, 1 ms for M60/X2) |
| **Credit starvation timeout** | 2000 | 500–10000 ms | How long to wait for a flow-control credit before forcing one |
| **Max packet size** | 180 | 20–237 B | Upper bound regardless of the negotiated MTU |

*Note:* Unlike Niimbot, Marklife printers do not support buzzer or volume commands in either protocol family.

---

## Entities

| Entity | Description |
|---|---|
| `sensor.<device>_battery` | Battery level percentage |
| `sensor.<device>_status` | Current condition: `out_of_paper`, `cover_open`, `overheating`, `low_battery`, `cover_closed` |
| `sensor.<device>_last_error` | Last actionable error; attributes retain the failed session, stage, radio, timings and likely cause |
| `sensor.<device>_error_count` | Actionable failures since integration setup (resets on reload/restart) |
| `sensor.<device>_print_duration` | Print duration in seconds (live during a job, total after completion) |
| `binary_sensor.<device>_out_of_paper` | True if paper is out |
| `binary_sensor.<device>_cover_open` | True if the cover is open |
| `binary_sensor.<device>_overheating` | True if the print head is overheating |
| `binary_sensor.<device>_low_battery` | True if battery is low |
| `binary_sensor.<device>_connection` | Active Bluetooth connection state |
| `binary_sensor.<device>_printing` | True while printing a job |
| `image.<device>_last_label_made` | Image entity showing the last label printed or previewed |

*Note:* Marklife printers report **one condition at a time**, so at most one fault sensor is active at any given moment.

---

## Service: `marklife.print`

### Parameters

| Parameter | Required | Default | Description |
|---|---|---|---|
| `payload` | yes | — | List of [imagespec elements](https://github.com/eigger/imagespec/blob/main/docs/elements.md) |
| `width` | no | print head width | Canvas width in pixels (defaults to 384) |
| `height` | no | `240` | Canvas height in pixels |
| `rotate` | no | `0` | Rotation: `0`, `90`, `180`, or `270` |
| `density` | no | profile default | Darkness: 1–3 |
| `paper_type` | no | `gap` | `gap` (die-cut label roll) or `continuous` |
| `copies` | no | `1` | Number of identical copies |
| `preview` | no | `false` | Render only; updates image entity without physical printing |

### Basic Example

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

### 40 × 12 mm Gap Label (P15 Default Media)

Design in reading orientation and rotate — `rotate: 90` swaps output dimensions so the 12 mm side spans across the print head:

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
  width: 320      # 40 mm x 8 dots/mm — feed direction
  height: 96      # 12 mm x 8 dots/mm — across print head
  rotate: 90      # -> 96 x 320 raster
  paper_type: gap
  density: 2
```

### Label Orientation Details

The raster goes to the printer with its **width across the print head** and **height along the feed direction**. On a die-cut roll, the roll width is the label's short side (e.g. 12 mm across the head and 40 mm feed length).

Design your label in natural reading orientation (`width: 320`, `height: 96`) and add `rotate: 90`. The integration automatically handles rotating and dimension transposition.

### Continuous Media

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

### Preview Without Printing

Set `preview: true` to generate the image and update `image.<device>_last_label_made` without physical printing:

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

### Per-Element Dithering

Do not dither text or barcodes. Apply `dither` (`floyd`, `atkinson`, `bayer8`) only to charts and images:

```yaml
action: marklife.print
target:
  device_id: <your device>
data:
  payload:
    - type: text
      value: Product
      font: ppb.ttf
      x: 10
      y: 8
      size: 28
    - type: dlimg
      url: "https://example.com/photo.jpg"
      x: 10
      y: 40
      xsize: 120
      ysize: 90
      dither: floyd
  width: 384
  height: 200
```

---

## Custom Fonts

Place `.ttf` files in `custom_components/marklife/fonts/` or `config/www/fonts/` and reference by filename (e.g., `ppb.ttf`).
