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

Resolve each environment with the central environment installer. It preserves manifest extras and constraints when resolving the actual HA component dependencies:

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install packaging==26.3
export STANDARDS_CHECKOUT=/path/to/reviewed/hass-repo-standards
export RUNNER_TEMP="$(mktemp -d)"
INPUT_DOMAIN=marklife \
INPUT_REQUIREMENTS=requirements_test.txt \
INPUT_TEST_PROFILE=ha \
INPUT_EXPECTED_HA_VERSION=2026.10.2 \
INPUT_HA_COMPONENTS="bluetooth recorder image sensor binary_sensor" \
INPUT_DEPENDENCY_MODE=minimum \
INPUT_MINIMUM_PACKAGES='["imagespec"]' \
.venv/bin/python "$STANDARDS_CHECKOUT/actions/python-environment/install.py"
```

For current renderer coverage set `INPUT_DEPENDENCY_MODE=current`. Keep each resolved combination in a separate environment. For exact minimum imagespec coverage, constrain `imagespec==1.1.0` together with the original `imagespec[datamatrix]>=1.1.0` manifest requirement in the same resolver run. Never replace the renderer after resolving an environment.

### Minimum HA Environment (Python 3.13 / HA 2025.9.0)

Create a Python 3.13 environment such as `.venv-min`, use its Python in the command above, and change `INPUT_REQUIREMENTS` to `requirements_test_min.txt` and `INPUT_EXPECTED_HA_VERSION` to `2025.9.0`. Preserve its pinned HA, plugin and pycares baseline. The workflow tests both current and exact minimum imagespec in each HA environment.

### Payload Contract and Regression Tests

After resolving either environment, run the required contract first with that environment's Python (use `.venv-min/bin/python` for minimum HA):

```bash
export STANDARDS_CHECKOUT=/path/to/reviewed/hass-repo-standards
export PAYLOAD_REPOSITORY="$PWD"
export PAYLOAD_DOMAIN=marklife
export PYTHONPATH="$STANDARDS_CHECKOUT/scripts${PYTHONPATH:+:$PYTHONPATH}"
.venv/bin/python -m pip check
.venv/bin/python -m pytest -p hass_standards_payload tests/components/marklife/test_payload_examples.py -v
```

Only after the contract succeeds, run the ordinary suite excluding its managed scaffold:

```bash
.venv/bin/python -m pytest tests/components/marklife/ --ignore=tests/components/marklife/test_payload_examples.py -v
```

The contract loads the real integration and validates complete action YAML through Home Assistant, comparing production rendering with installed imagespec output. It never dispatches the print action. Example templates use the real fixture's battery state and local bundled font.

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
