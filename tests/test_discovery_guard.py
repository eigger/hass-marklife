"""Advertisement corroboration tests.

A local-name prefix is weak evidence on its own. ``M1-``, ``S2-``, ``T3-`` and
``X2-`` are short enough that unrelated hardware can carry the same prefix, and
Home Assistant's manifest matcher cannot express "at least N characters" beyond
its own three-character floor.

``advertisement_contradicts`` adds a second signal: when the advertisement lists
service UUIDs, the profile's service must be among them. It is one-sided on
purpose — an advertisement with no service UUIDs at all is not evidence against
a match, because many peripherals expose services only after connecting.
"""

from __future__ import annotations

import pytest

from marklife_ble.models import (
    SERVICE_ALT,
    SERVICE_PRIMARY,
    advertisement_contradicts,
    get_profile,
)


def test_no_advertised_uuids_is_never_a_contradiction():
    """Silence proves nothing, so discovery must not be blocked by it."""
    assert advertisement_contradicts(get_profile("p15"), []) is False


def test_matching_uuid_corroborates():
    assert advertisement_contradicts(get_profile("p15"), [SERVICE_PRIMARY]) is False


def test_uuid_comparison_ignores_case():
    """Advertisement data casing varies by backend; the manifest requires lowercase."""
    assert (
        advertisement_contradicts(get_profile("p15"), [SERVICE_PRIMARY.upper()]) is False
    )


def test_populated_but_missing_uuid_is_a_contradiction():
    """A device named like a printer but advertising something else is rejected."""
    unrelated = [
        "0000180f-0000-1000-8000-00805f9b34fb",  # Battery Service
        "0000180a-0000-1000-8000-00805f9b34fb",  # Device Information
    ]
    assert advertisement_contradicts(get_profile("p15"), unrelated) is True


def test_extra_uuids_alongside_ours_still_corroborate():
    advertised = ["0000180a-0000-1000-8000-00805f9b34fb", SERVICE_PRIMARY]
    assert advertisement_contradicts(get_profile("m60"), advertised) is False


def test_p80_is_checked_against_its_own_fallback_service():
    """P80/T3 sit on the ISSC service, not the primary one."""
    p80 = get_profile("p80")
    assert p80.service_uuid == SERVICE_ALT
    assert advertisement_contradicts(p80, [SERVICE_ALT]) is False
    # The primary service must not satisfy a P80 profile.
    assert advertisement_contradicts(p80, [SERVICE_PRIMARY]) is True


@pytest.mark.parametrize("model_id", ["p15", "p12", "m60", "p50", "s2"])
def test_primary_service_profiles_agree_on_the_uuid(model_id):
    assert get_profile(model_id).service_uuid == SERVICE_PRIMARY


def test_generic_prefix_collision_is_the_case_this_guards():
    """The motivating scenario: an unrelated device advertising as "M1-...".

    It resolves to the P15 profile by name alone, and only the advertised
    service UUIDs distinguish it from a real printer.
    """
    from marklife_ble.models import find_profile_by_name

    profile = find_profile_by_name("M1-2200")
    assert profile is not None and profile.model_id == "p15"

    impostor = ["0000fe9f-0000-1000-8000-00805f9b34fb"]
    assert advertisement_contradicts(profile, impostor) is True
    assert advertisement_contradicts(profile, [SERVICE_PRIMARY]) is False
