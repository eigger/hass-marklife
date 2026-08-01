"""Translation files must stay structurally in step with strings.json.

A missing key does not raise — Home Assistant just renders the raw key name in
the UI — so drift here is invisible until someone switches language.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

COMPONENT_DIR = (
    Path(__file__).resolve().parents[1] / "custom_components" / "marklife"
)
STRINGS = COMPONENT_DIR / "strings.json"
TRANSLATIONS = sorted((COMPONENT_DIR / "translations").glob("*.json"))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def key_paths(node, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    """Every leaf path in a nested dict."""
    if not isinstance(node, dict):
        return {prefix}
    return {p for k, v in node.items() for p in key_paths(v, (*prefix, k))}


def test_translation_files_exist():
    assert TRANSLATIONS, "no translation files found"
    assert any(p.name == "en.json" for p in TRANSLATIONS)


@pytest.mark.parametrize("path", TRANSLATIONS, ids=lambda p: p.name)
def test_translation_matches_strings(path):
    missing = key_paths(load(STRINGS)) - key_paths(load(path))
    assert not missing, f"{path.name} is missing {sorted('.'.join(m) for m in missing)}"


@pytest.mark.parametrize("path", [STRINGS, *TRANSLATIONS], ids=lambda p: p.name)
def test_manual_step_is_translated(path):
    """The manual step is the fallback when no printer is recognised by name."""
    manual = load(path)["config"]["step"]["manual"]
    assert "{count}" in manual["description"]
    assert "address" in manual["data"]
    assert "model" in manual["data"]


@pytest.mark.parametrize("path", [STRINGS, *TRANSLATIONS], ids=lambda p: p.name)
def test_invalid_address_error_is_translated(path):
    assert load(path)["config"]["error"]["invalid_address"]


@pytest.mark.parametrize("path", [STRINGS, *TRANSLATIONS], ids=lambda p: p.name)
def test_no_devices_found_is_gone(path):
    """The user step now falls through to manual entry instead of aborting."""
    assert "no_devices_found" not in load(path)["config"]["abort"]


#: Protocol knobs that only make sense once a printer is misbehaving. Every one
#: has a working default, so setup must not ask for them -- a first-time user
#: cannot pick a credit starvation timeout.
TUNING_FIELDS = {"tick_ms", "starvation_ms", "packet_size_cap"}

#: Answerable without knowing anything about the hardware, so setup does ask.
SETUP_FIELDS = {"scan_interval", "keep_connection"}


@pytest.mark.parametrize("path", [STRINGS, *TRANSLATIONS], ids=lambda p: p.name)
def test_setup_steps_do_not_ask_for_tuning(path):
    for step, fields in load(path)["config"]["step"].items():
        asked = set(fields.get("data", {}))
        leaked = asked & TUNING_FIELDS
        assert not leaked, f"config step '{step}' asks for {sorted(leaked)}"


@pytest.mark.parametrize("path", [STRINGS, *TRANSLATIONS], ids=lambda p: p.name)
def test_setup_steps_offer_the_basic_settings(path):
    for step, fields in load(path)["config"]["step"].items():
        missing = SETUP_FIELDS - set(fields.get("data", {}))
        assert not missing, f"config step '{step}' is missing {sorted(missing)}"


@pytest.mark.parametrize("path", [STRINGS, *TRANSLATIONS], ids=lambda p: p.name)
def test_options_offers_everything(path):
    init = load(path)["options"]["step"]["init"]
    missing = (TUNING_FIELDS | SETUP_FIELDS) - set(init["data"])
    assert not missing, f"options is missing {sorted(missing)}"


@pytest.mark.parametrize("path", [STRINGS, *TRANSLATIONS], ids=lambda p: p.name)
def test_every_option_explains_itself(path):
    """Without a description these read as jargon in the Configure dialog."""
    init = load(path)["options"]["step"]["init"]
    described = init.get("data_description", {})
    for field in init["data"]:
        assert described.get(field), f"option '{field}' has no data_description"


@pytest.mark.parametrize("path", [STRINGS, *TRANSLATIONS], ids=lambda p: p.name)
def test_every_setup_field_explains_itself(path):
    for step, fields in load(path)["config"]["step"].items():
        described = fields.get("data_description", {})
        for field in SETUP_FIELDS:
            assert described.get(field), f"'{field}' has no description in step '{step}'"
