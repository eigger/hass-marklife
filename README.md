# hass-marklife

<!-- hass-standards:badges:start -->
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square)](#installation)
[![Release](https://img.shields.io/github/v/release/eigger/hass-marklife?style=flat-square)](https://github.com/eigger/hass-marklife/releases)
[![Home Assistant minimum](https://img.shields.io/badge/HA-%E2%89%A5%202025.1.0-41BDF5?style=flat-square)](hacs.json)
[![Tests](https://img.shields.io/github/actions/workflow/status/eigger/hass-marklife/tests.yml?branch=main&style=flat-square&label=Tests)](https://github.com/eigger/hass-marklife/actions/workflows/tests.yml)
[![Validate](https://img.shields.io/github/actions/workflow/status/eigger/hass-marklife/validate.yml?branch=main&style=flat-square&label=Validate)](https://github.com/eigger/hass-marklife/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/eigger/hass-marklife?style=flat-square)](LICENSE)
[![Analytics reporting installs](https://img.shields.io/badge/dynamic/json?style=flat-square&color=41BDF5&label=Usage&query=%24.marklife.total&url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json)](https://analytics.home-assistant.io/)
<!-- hass-standards:badges:end -->

**English** | [한국어](README.ko.md)

A HACS custom integration for Marklife Bluetooth thermal label printers (such as P15, P12, M60, P50, and compatible models) using Home Assistant's native Bluetooth stack and ESPHome Bluetooth proxies. Generates and prints declarative label layouts via [imagespec](https://github.com/eigger/imagespec).

## Supported Devices

- **Tested & Verified**: **Marklife P15** (L11 protocol family, 384 px print head) with local Bluetooth adapters and ESPHome proxies.
- **Compatible Families**: P12, P11, P7, P1s, M1, M60, X2, P50, and related BLE models.
- **Unsupported**: Bluetooth Classic models (S8, D210, HM-24-28, etc.) and proprietary protocols (D100, X4).
- See the [User Guide](docs/user-guide.md#supported-models) for the full model matrix and print head specifications.

## Requirements

- Home Assistant **2025.1.0** or newer.
- A functional Bluetooth adapter or [ESPHome Bluetooth proxy](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md) with active connections enabled (`bluetooth_proxy: active: true`).
- A supported Marklife BLE printer. Disconnect vendor mobile apps before printing.

## Installation

1. Add `https://github.com/eigger/hass-marklife` to **HACS → Integrations → Custom repositories** (category *Integration*), or copy `custom_components/marklife/` into your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.
3. Open **Settings → Devices & services** and confirm the automatically discovered printer, or choose **Add integration → Marklife** (falls through to a manual address/model selection step if not automatically detected).

Refer to the [Bluetooth proxy guide](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md) for ESPHome setup recommendations (e.g. XIAO W5500 V1.2 or M5Stack AtomS3U).

## Quick Start

Print a basic label via the `marklife.print` action:

```yaml
action: marklife.print
target:
  device_id: <your device id>
data:
  payload:
    - type: text
      value: "Hello World!"
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

## Important Limitations

- **Single Connection**: BLE thermal printers accept only one active connection at a time. Close the smartphone vendor app before attempting to connect from Home Assistant.
- **Bluetooth Classic & Proprietary**: Models requiring Bluetooth Classic or proprietary protocols cannot be connected via BLE and will be rejected during discovery.
- **Proxy Capacity**: An ESP32 proxy supports up to 3 concurrent BLE connections. Ensure connection slots are not exhausted.

## Documentation

- [User Guide](docs/user-guide.md) — Comprehensive model table, advanced options, entities, orientation guidelines, and `imagespec` examples.
- [Troubleshooting](docs/troubleshooting.md) — Credit starvation tuning, packet sizes, connection issues, and debug log reporting.
- [Development](docs/development.md) — Repository architecture, real Home Assistant test suite, and standards adoption.
- [Bluetooth Proxy Setup](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md) — General hardware and ESPHome proxy configuration guide.

## Support

- Report bugs or request model support via [GitHub Issues](https://github.com/eigger/hass-marklife/issues).
- General questions and template sharing in [GitHub Discussions](https://github.com/eigger/hass-marklife/discussions).

## License

- Licensed under [MIT](LICENSE).
- Protocol core ported from [tomLadder/thermoprint](https://github.com/tomLadder/thermoprint) (MIT).
- Built-in font `ppb.ttf` included for label rendering.
