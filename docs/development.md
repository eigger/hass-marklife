# Development & Real Home Assistant Testing

[English README](../README.md) · [한국어 README](../README.ko.md) · [Adoption Checklist](../ADOPTION_CHECKLIST.md)

This integration is distributed as a HACS custom integration via `custom_components/marklife/`. It conforms to Home Assistant Core component structure, config entry lifecycles, and public APIs.

## Architecture and Test Boundaries

- **Implementation**: `custom_components/marklife/` containing config flow, coordinator/entry setup, entity, sensor, binary_sensor, image, services, and the `marklife_ble/` protocol layer.
- **Tests**: Located in `tests/components/marklife/`, with common fixtures in `tests/conftest.py` (`auto_enable_custom_integrations`).
- **Real HA Fixtures**: Tests run against real Home Assistant core fixtures via `pytest-homeassistant-custom-component` (`hass`, `MockConfigEntry`), testing the component loader, entry setup/teardown, platform forward/unload, entity registry, device registry, and services.
- **Mock Boundary**: Only external Bluetooth hardware/GATT transport boundaries are mocked (`PrinterTransport`). The protocol encoder, rasterizer, client state machine, flow controller, and Home Assistant integration logic remain entirely real.

## Support Baselines and Current Testing

| Scope | Python | Home Assistant | pytest-homeassistant-custom-component | Declaration |
|---|---|---|---|---|
| Historical Support Baseline | 3.13 | 2025.9.0 | 0.13.277 | `hacs.json`, `requirements_test_min.txt` |
| Current Testing Target | 3.14 | 2026.10.2 | 0.13.373 | `requirements_test.txt` |

The declared minimum support baseline (`2025.9.0`) reflects the requirements of `OptionsFlowWithReload` and `AddConfigEntryEntitiesCallback`. `requirements_test_min.txt` is excluded from automated dependency updates to prevent accidental version drift.

## Running Tests Locally

### Current Environment (Python 3.14 / HA 2026.10.2)

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt imagespec
pytest tests/components/marklife/ -v
pip check
```

### Minimum HA Environment (Python 3.13 / HA 2025.1.0)

```bash
python3.13 -m venv .venv-min
source .venv-min/bin/activate
pip install -r requirements_test_min.txt imagespec
pytest tests/components/marklife/ -v
pip check
```

### Linting and Formatting

```bash
pip install -r requirements_lint.txt
ruff check .
ruff format --check .
```

## Dependencies & Manifest

- Runtime dependencies are declared in `manifest.json` (`imagespec[datamatrix]>=1.1.0`).
- Home Assistant integration dependencies (`bluetooth_adapters`) and after-dependencies (`recorder`) are declared explicitly.
- Testing and linting tools are declared in dedicated `requirements_*.txt` files.
