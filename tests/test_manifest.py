"""Manifest and Bluetooth auto-discovery tests.

Home Assistant's Bluetooth matcher has two rules that are easy to violate and
that fail loudly only at runtime:

1. ``_local_name_to_index_key`` raises ``ValueError`` if ``*`` or ``[`` appears
   in the **first three characters** of a ``local_name`` pattern, because such a
   matcher would be too broad. A pattern like ``"P7*"`` breaks integration setup.
2. Matching is **case-sensitive**. The bucket lookup compares the pattern's
   literal first three characters against ``service_info.name[:3]``, and the
   pattern itself is compiled with ``fnmatch.translate``, which does not
   normalise case.

These tests reimplement both rules so a bad matcher fails here rather than in
someone's Home Assistant log.
"""

from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

import pytest

from marklife_ble.models import find_profile_by_name

MANIFEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "marklife"
    / "manifest.json"
)

# homeassistant.components.bluetooth.match
LOCAL_NAME_MIN_MATCH_LENGTH = 3

# script.hassfest.manifest -- the only keys allowed in a bluetooth matcher.
ALLOWED_MATCHER_KEYS = {
    "connectable",
    "service_uuid",
    "service_data_uuid",
    "local_name",
    "manufacturer_id",
    "manufacturer_data_start",
}


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def matchers(manifest) -> list[dict]:
    return manifest["bluetooth"]


def index_key(pattern: str) -> str:
    """Reimplementation of HA's ``_local_name_to_index_key``."""
    match_part = pattern[:LOCAL_NAME_MIN_MATCH_LENGTH]
    if "*" in match_part or "[" in match_part:
        raise ValueError(
            f"Local name matchers may not have patterns in the first "
            f"{LOCAL_NAME_MIN_MATCH_LENGTH} characters ({pattern})"
        )
    return match_part


def ha_matches(name: str, pattern: str) -> bool:
    """Reimplementation of HA's local-name matching, bucket lookup included."""
    if index_key(pattern) != name[:LOCAL_NAME_MIN_MATCH_LENGTH]:
        return False
    return bool(re.compile(fnmatch.translate(pattern)).match(name))


# ------------------------------------------------------------ manifest shape


def test_domain_matches_the_component_directory(manifest):
    assert manifest["domain"] == MANIFEST_PATH.parent.name


def test_required_manifest_keys(manifest):
    for key in ("domain", "name", "documentation", "codeowners", "version"):
        assert manifest.get(key), f"manifest is missing {key}"
    assert manifest["config_flow"] is True
    assert "bluetooth_adapters" in manifest["dependencies"]


def test_matchers_only_use_supported_keys(matchers):
    for matcher in matchers:
        unknown = set(matcher) - ALLOWED_MATCHER_KEYS
        assert not unknown, f"unsupported matcher keys {unknown} in {matcher}"


def test_uuid_matchers_are_lowercase(matchers):
    """hassfest applies ``verify_lowercase`` to both UUID fields."""
    for matcher in matchers:
        for key in ("service_uuid", "service_data_uuid"):
            if value := matcher.get(key):
                assert value == value.lower(), f"{key} must be lowercase: {value}"


# ------------------------------------------------------- local name matchers


def test_no_wildcard_in_the_first_three_characters(matchers):
    """A violation raises at HA startup, taking the whole integration down."""
    for matcher in matchers:
        if pattern := matcher.get("local_name"):
            index_key(pattern)  # raises ValueError if too broad


def test_patterns_are_long_enough(matchers):
    for matcher in matchers:
        if pattern := matcher.get("local_name"):
            assert len(pattern) > LOCAL_NAME_MIN_MATCH_LENGTH, (
                f"{pattern} has no wildcard after its literal prefix"
            )


def test_every_matcher_resolves_to_a_supported_profile(matchers):
    """The manifest and the device registry must agree.

    A matcher that fires but has no profile would abort the config flow, and one
    that maps to an SPP model would offer a printer we cannot drive.
    """
    for matcher in matchers:
        pattern = matcher.get("local_name")
        if not pattern:
            continue
        sample = pattern.replace("*", "0042")
        profile = find_profile_by_name(sample)
        assert profile is not None, f"{pattern} matches no device profile"
        assert profile.supported, f"{pattern} maps to unsupported profile {profile.model_id}"


@pytest.mark.parametrize(
    ("advertised_name", "model_id"),
    [
        ("P15-A1B2", "p15"),
        ("P15R_0042", "p15"),
        ("P15S-7", "p15"),
        ("P7R-9", "p15"),
        ("P7-0001", "p15"),
        ("P7_0001", "p15"),
        ("P1s-0001", "p15"),
        ("P1S-0001", "p15"),
        ("LP15_2", "p15"),
        ("LPC74-2", "p15"),
        ("S15-1", "p15"),
        ("S12-1", "p15"),
        ("OUT_LPC-3", "p15"),
        ("iSPACE_LP15-4", "p15"),
        ("M1-7", "p15"),
        ("P12-XYZ", "p12"),
        ("P11-XYZ", "p12"),
        ("LP90-1", "p12"),
        ("M60-77", "m60"),
        ("X2-3", "m60"),
        ("P50S_1", "p50"),
        ("D50-8", "p50"),
        ("P80-3", "p80"),
        ("T3-1", "p80"),
        ("S2-1", "s2"),
    ],
)
def test_realistic_names_are_auto_discovered(matchers, advertised_name, model_id):
    """Each name must both trigger a matcher and resolve to the right profile."""
    patterns = [m["local_name"] for m in matchers if "local_name" in m]
    assert any(ha_matches(advertised_name, p) for p in patterns), (
        f"{advertised_name} triggers no manifest matcher"
    )
    assert find_profile_by_name(advertised_name).model_id == model_id


@pytest.mark.parametrize(
    "advertised_name",
    ["Govee_H5075", "ATC_1a2b3c", "LE-Bose Mini", "S8-1234", "D100-9"],
)
def test_unrelated_and_unsupported_devices_are_not_matched(matchers, advertised_name):
    patterns = [m["local_name"] for m in matchers if "local_name" in m]
    assert not any(ha_matches(advertised_name, p) for p in patterns)


def test_matching_is_case_sensitive_so_both_p1s_spellings_are_listed(matchers):
    """thermoprint spells this prefix ``P1s``; a printer may advertise ``P1S``.

    HA compiles patterns with ``fnmatch.translate``, which is case-sensitive, so
    one spelling does not cover the other. The device registry is
    case-insensitive, so only the manifest needs both.
    """
    patterns = [m["local_name"] for m in matchers if "local_name" in m]
    assert any(ha_matches("P1s-1", p) for p in patterns)
    assert any(ha_matches("P1S-1", p) for p in patterns)
    assert not ha_matches("P1S-1", "P1s*")


def test_short_prefix_patterns_would_be_rejected_by_home_assistant():
    """Documents why P7/M1/S2/X2/T3 need a separator in their pattern."""
    for pattern in ("P7*", "M1*", "S2*", "X2*", "T3*"):
        with pytest.raises(ValueError, match="first 3 characters"):
            index_key(pattern)
