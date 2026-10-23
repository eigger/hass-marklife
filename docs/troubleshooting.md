# Marklife Troubleshooting

[Home](../README.md) | [한국어](troubleshooting.ko.md)

## Common troubleshooting

Start with [common Bluetooth troubleshooting](https://github.com/eigger/blesession/blob/main/docs/troubleshooting.md).

Refer to the shared [Bluetooth proxy setup](https://github.com/eigger/blesession/blob/main/docs/bluetooth.md) guide for ESPHome configuration, proxy recommendations (such as XIAO W5500 Ethernet Adapter V1.2 and M5Stack AtomS3U), and general Bluetooth troubleshooting.

## Device-specific checks

- **Power and Wake**: Ensure the printer is charged and powered on. Bluetooth BLE sleeps when idle; press the power button to wake it before connecting.
- **Paper & Cover**: Make sure paper is properly inserted and the cover is securely latched. Marklife printers report conditions (`cover_open`, `out_of_paper`, `overheating`, `low_battery`) that prevent printing.
- **Disconnect Phone Apps**: Thermal printers only support a single concurrent Bluetooth central. If the vendor app (Marklife) is connected on your smartphone, Home Assistant cannot establish a connection.
- **Confirm Supported Model**: Models using Bluetooth Classic (e.g. S8, D210, HM-24-28) or proprietary encrypted protocols (D100, X4) cannot connect via BLE. See [supported models](user-guide.md#supported-models).

## Symptoms and actions

| Symptom | Failing stage | Checks | Action |
|---|---|---|---|
| **No discovery** | `unreachable` | Power, advertisements, proxy availability | Ensure the printer is awake and advertising. Check proxy distance and online status. If the advertised name does not match known prefixes, use manual setup. |
| **Discovered but cannot connect** | `connect` | Active connections and occupied proxy slots | Ensure ESPHome proxy has `active: true` enabled under `bluetooth_proxy`. An ESP32 proxy supports at most 3 concurrent connections — verify slots are not exhausted by other integrations. Disconnect the printer from phone Bluetooth. |
| **Print stops partway or bands are missing** | `transfer` | Credit flow and packet size | Flow control credit starvation: in integration **Configure**, **increase Credit starvation timeout** (e.g. to 3000–5000 ms), or **reduce Max packet size** (e.g. to 100–120 bytes). |
| **Connected but unresponsive** | `session / finish` | Cover, paper, status responses | Marklife printers report one condition at a time. Check `sensor.<device>_status` to ensure no cover/paper fault is active. |

## Diagnostics and logs

Inspect the entities in Home Assistant under **Settings** → **Devices & Services** → **Marklife** → your device:

- `sensor.<device>_status`: Reports `cover_closed`, `cover_open`, `out_of_paper`, `overheating`, or `low_battery`.
- `sensor.<device>_battery`: Battery percentage reported by the device.
- `binary_sensor.<device>_connection`: True while a BLE GATT connection is active.
- `binary_sensor.<device>_printing`: True while raster data is actively transmitting.
- `image.<device>_last_label_made`: Displays the most recent rendered bitmap to verify formatting before physical printing.


BLE sessions use [blesession](https://github.com/eigger/blesession). The **Connection** diagnostic binary sensor indicates an actual GATT link, rather than printer power. With keep connection disabled it turns off after a successful poll or print. Attributes describe the latest session: `operation`, `success`, radio (`via`, `via_type`), signal (`rssi`), available routes (`paths`), and stage timings (`connect_s`, `session_s`, `transfer_s`, `finish_s`, `disconnect_s`) where available. Reused links have `reused` and no `connect_s`. When `via_unconfirmed` is true, the route is an estimate from advertisements, not a confirmed connection route.

**Last error** and **Error count** are diagnostic sensors. They record print failures and failures after a polling connection is established. Routine polls that cannot see or connect to a sleeping printer do not increment the count. A later success preserves the last failure's `timestamp`, `failed_stage`, `failed_detail`, `error`, and `likely_cause` until the next failure. Reloading the integration or restarting HA resets the history and count. **Print Duration** attributes retain the most recent print session independently of status polls. Failed prints are not automatically replayed.

See [shared BLE troubleshooting](https://github.com/eigger/blesession/blob/main/docs/troubleshooting.md) for report interpretation. Existing credit flow control and packet size limits still apply over proxies. Physical Marklife printer and ESPHome proxy behavior requires separate hardware validation.

## If the problem persists

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

Include HA/integration/blesession/ESPHome versions, printer and proxy models/revisions, connection method, failure time/stage and reproduction steps. Capture only the reproduction interval and disable `custom_components.marklife` debug logging afterward. Remove addresses, credentials, tokens and private label content from public records.
