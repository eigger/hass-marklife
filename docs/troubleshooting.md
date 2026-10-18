# Marklife Troubleshooting

[Home](../README.md) | [한국어](ko/troubleshooting.md)

Refer to the shared [Bluetooth proxy setup](https://github.com/eigger/hass-repo-standards/blob/main/docs/bluetooth.md#troubleshooting) guide for ESPHome configuration, proxy recommendations (such as XIAO W5500 Ethernet Adapter V1.2 and M5Stack AtomS3U), and general Bluetooth troubleshooting.

## 1. Prepare the Printer

- **Power and Wake**: Ensure the printer is charged and powered on. Bluetooth BLE sleeps when idle; press the power button to wake it before connecting.
- **Paper & Cover**: Make sure paper is properly inserted and the cover is securely latched. Marklife printers report conditions (`cover_open`, `out_of_paper`, `overheating`, `low_battery`) that prevent printing.
- **Disconnect Phone Apps**: Thermal printers only support a single concurrent Bluetooth central. If the vendor app (Marklife) is connected on your smartphone, Home Assistant cannot establish a connection.
- **Confirm Supported Model**: Models using Bluetooth Classic (e.g. S8, D210, HM-24-28) or proprietary encrypted protocols (D100, X4) cannot connect via BLE. See [supported models](user-guide.md#supported-models).

## 2. Identify the Problem

| Symptom | Check and Action |
|---|---|
| **No discovery** | Ensure the printer is awake and advertising. Check proxy distance and online status. If the advertised name does not match known prefixes, use manual setup. |
| **Discovered but cannot connect** | Ensure ESPHome proxy has `active: true` enabled under `bluetooth_proxy`. An ESP32 proxy supports at most 3 concurrent connections — verify slots are not exhausted by other integrations. Disconnect the printer from phone Bluetooth. |
| **Print stops partway or bands are missing** | Flow control credit starvation: in integration **Configure**, **increase Credit starvation timeout** (e.g. to 3000–5000 ms), or **reduce Max packet size** (e.g. to 100–120 bytes). |
| **Connected but unresponsive** | Marklife printers report one condition at a time. Check `sensor.<device>_status` to ensure no cover/paper fault is active. |

## 3. Diagnostic Entities

Inspect the entities in Home Assistant under **Settings** → **Devices & Services** → **Marklife** → your device:

- `sensor.<device>_status`: Reports `cover_closed`, `cover_open`, `out_of_paper`, `overheating`, or `low_battery`.
- `sensor.<device>_battery`: Battery percentage reported by the device.
- `binary_sensor.<device>_connection`: True while a BLE GATT connection is active.
- `binary_sensor.<device>_printing`: True while raster data is actively transmitting.
- `image.<device>_last_label_made`: Displays the most recent rendered bitmap to verify formatting before physical printing.

## 4. Reporting an Issue

Before opening an issue, capture debug logs:

```yaml
logger:
  default: warning
  logs:
    custom_components.marklife: debug
```

When posting in [Issues](https://github.com/eigger/hass-marklife/issues):
- Redact sensitive information (device MAC addresses, private label payloads).
- Specify your printer model and the exact advertised Bluetooth name.
- Mention your Bluetooth adapter type (local USB adapter or ESPHome proxy version/board).
- Include the debug log excerpt covering the connection and print attempt.
