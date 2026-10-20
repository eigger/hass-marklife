# Marklife payload guide

[README](../README.md) · [한국어](payload.ko.md)

## Common payload guide

The [imagespec payload guide](https://github.com/eigger/imagespec/blob/main/docs/payload.md) documents element syntax, colors, rotation and dithering. Marklife uses the installed `imagespec[datamatrix]>=1.1.0` renderer.

## Using payloads in this integration

Use the `marklife.print` action with a configured printer's `device_id` target and a list at `data.payload`. Home Assistant resolves action templates before rendering. The example target resolves the device belonging to `sensor.p15_0000_ddeeff_battery`; replace that entity with your printer's battery sensor or select its device in the action editor. Set `preview: true` to return a base64 PNG without printing; remove it or set it to false to print.

The real renderer resolves `ppb.ttf` from the integration's bundled fonts, then other font names from the integration or `/config/www/fonts`. It provides recorder history to imagespec history elements; those need recorder data for the requested entity and time range. Home Assistant templates belong in action data; this integration does not add another Jinja pass inside the renderer.

## Minimal working example

[Complete minimal action YAML](../examples/payload/minimal.yaml) renders the existing quick-start text and QR code on a 384 × 96 pixel label. [Template action YAML](../examples/payload/template.yaml) uses the real printer battery state and bundled font. Both examples use preview mode; they do not send a printer command during contract verification.

## Device output settings

The verified P15 has a 384-dot print head. Width defaults to the selected device profile's print head width; height defaults to 240 pixels. These examples explicitly use width 384 and height 96. Output uses black and white, with dithering disabled. `rotate` defaults to 0; image rotation can exchange output width and height at 90 or 270 degrees. See the [model table and orientation instructions](user-guide.md) before choosing dimensions for another printer. This does not establish hardware validation for untested model families.

## Supported features and limitations

The installed imagespec version defines supported elements; the declared minimum includes the datamatrix extra. Text, QR codes and real Home Assistant state templates are exercised by the linked examples. Fonts must exist locally. History requires recorder data; remote images require their actual network source at runtime. The contract uses no remote images or device writes. The printer receives monochrome raster output. Bluetooth Classic and proprietary models listed in the README remain unsupported. Existing [advanced examples](user-guide.md) and device limits still apply.

## Troubleshooting

Check action templates, device selection, local fonts, dimensions and imagespec errors first. Use preview mode to inspect rendering before printing. For BLE connection and transfer issues follow [device troubleshooting](troubleshooting.md). Report reproducible rendering problems through the existing [Issues](https://github.com/eigger/hass-marklife/issues) process with sanitized action data and versions.
