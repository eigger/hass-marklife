"""Protocol layer tests.

Byte-level expectations come from the Marklife APK reverse-engineering notes in
tomLadder/thermoprint (``REVERSE_ENGINEERING.md``), so a regression here means
the port drifted from the documented wire format.

Async tests call ``asyncio.run`` directly rather than depending on
pytest-asyncio.
"""

from __future__ import annotations

import asyncio
import zlib

import pytest
from PIL import Image

from marklife_ble.client import _split_at_bulk
from marklife_ble.flow import CreditFlowController
from marklife_ble.imaging import fit_to_printhead, to_raster
from marklife_ble.models import find_profile_by_name, get_profile
from marklife_ble.protocols import PrintOptions, get_protocol


@pytest.fixture
def raster():
    """An 8x2 raster: row 0 is black on the left half, row 1 is blank."""
    img = Image.new("L", (8, 2), color=255)
    for x in range(4):
        img.putpixel((x, 0), 0)
    return to_raster(img, dither=False, threshold=128)


# --------------------------------------------------------------- profiles


@pytest.mark.parametrize(
    ("name", "model_id"),
    [
        ("P15-A1B2", "p15"),
        ("P15R_0042", "p15"),
        ("P15S-7", "p15"),
        ("P7R-9", "p15"),
        ("P1s-0001", "p15"),
        ("LPC74-2", "p15"),
        ("P12-XYZ", "p12"),
        ("P11-XYZ", "p12"),
        ("LP90-1", "p12"),
        ("M60-77", "m60"),
        ("X2-3", "m60"),
        ("P50S_1", "p50"),
        ("D50-8", "p50"),
        ("P80-3", "p80"),
    ],
)
def test_name_prefix_resolves_to_profile(name, model_id):
    assert find_profile_by_name(name).model_id == model_id


def test_overlapping_prefixes_pick_the_most_specific():
    """P1s/P11/P12 and P15/P15R all share leading characters.

    thermoprint matches in profile registration order, which makes the winner
    depend on how the registry happens to be built. Longest-prefix-first makes
    it deterministic.
    """
    assert find_profile_by_name("P1s-1").model_id == "p15"
    assert find_profile_by_name("P11-1").model_id == "p12"
    assert find_profile_by_name("P15-1").model_id == "p15"


def test_unknown_and_missing_names():
    assert find_profile_by_name("Govee_H5075") is None
    assert find_profile_by_name(None) is None
    assert find_profile_by_name("") is None


def test_spp_models_are_recognised_but_unsupported():
    profile = find_profile_by_name("S8-1234")
    assert profile is not None
    assert profile.supported is False
    assert "SPP" in profile.unsupported_reason


def test_p80_has_no_credit_channel():
    assert get_profile("p80").uses_credits is False
    assert get_profile("p15").uses_credits is True


def test_density_scales():
    assert get_profile("p15").map_density(3) == 3  # no remap
    assert get_profile("m60").map_density(1) == 3
    assert get_profile("m60").map_density(2) == 8
    assert get_profile("m60").map_density(3) == 14


# ---------------------------------------------------------------- imaging


def test_raster_packing_is_msb_first_with_one_meaning_ink(raster):
    assert raster.bytes_per_row == 1
    assert len(raster.data) == 2
    assert raster.data[0] == 0xF0  # leftmost four pixels black
    assert raster.data[1] == 0x00


def test_rows_pad_to_byte_boundaries():
    img = Image.new("L", (9, 1), color=255)
    packed = to_raster(img, dither=False)
    assert packed.bytes_per_row == 2


def test_fit_to_printhead_scales_down_and_keeps_ratio():
    fitted = fit_to_printhead(Image.new("L", (800, 10)), 384)
    assert fitted.width == 384
    assert fitted.height == 5


def test_fit_to_printhead_leaves_narrow_images_alone():
    img = Image.new("L", (100, 10))
    assert fit_to_printhead(img, 384) is img


# ------------------------------------------------------------------- L11


def test_l11_print_sequence(raster):
    seq = get_protocol("l11").build_print_sequence(
        raster, get_profile("p15"), PrintOptions(density=2, paper_type="gap")
    )
    assert [c.label for c in seq] == [
        "set-thickness", "wakeup", "enable", "print-bitmap", "position-to-gap", "stop"
    ]
    assert seq[0].data.hex() == "10ff100002"  # P15 uses thickness, not density
    assert len(seq[1].data) == 15
    assert seq[2].data.hex() == "10fff102"
    assert seq[5].data.hex() == "10fff145"


def test_l11_raster_header_is_gs_v_0_little_endian(raster):
    seq = get_protocol("l11").build_print_sequence(
        raster, get_profile("p15"), PrintOptions(density=2)
    )
    bitmap = seq[3]
    # 1D 76 30 <quality> <bytesPerRow lo hi> <height lo hi>
    assert bitmap.data[:8].hex() == "1d763000" + "0100" + "0200"
    assert bitmap.data[8:] == raster.data
    assert bitmap.bulk is True


def test_l11_paper_type_changes_the_trailing_feed(raster):
    l11 = get_protocol("l11")
    gap = l11.build_print_sequence(raster, get_profile("p15"), PrintOptions(paper_type="gap"))
    cont = l11.build_print_sequence(
        raster, get_profile("p15"), PrintOptions(paper_type="continuous")
    )
    assert gap[4].data.hex() == "1d0c"    # position to gap
    assert cont[4].data.hex() == "1b4a64"  # feed 100 dots


def test_l11_density_falls_back_to_profile_default(raster):
    seq = get_protocol("l11").build_print_sequence(
        raster, get_profile("p15"), PrintOptions()
    )
    assert seq[0].data.hex() == "10ff100002"


def test_p12_uses_the_density_command(raster):
    seq = get_protocol("l11").build_print_sequence(
        raster, get_profile("p12"), PrintOptions(density=3)
    )
    assert seq[0].data.hex() == "1f700203"


# ------------------------------------------------------------ compressed


def test_compressed_print_sequence_matches_the_documented_p50_order(raster):
    seq = get_protocol("compressed").build_print_sequence(
        raster, get_profile("m60"), PrintOptions(density=2, paper_type="gap")
    )
    assert [c.label for c in seq] == [
        "set-paper-type", "set-density", "wakeup", "start-job", "adjust-position",
        "print-bitmap", "printer-location", "stop-job", "adjust-position",
    ]
    assert seq[0].data.hex() == "1f800220"
    assert seq[1].data.hex() == "1f700208"  # M60 remaps density 2 -> 8
    assert len(seq[2].data) == 6            # shorter wakeup than L11
    assert seq[3].data.hex() == "1fc00100"
    assert seq[4].data.hex() == "1f1151"
    assert seq[6].data.hex() == "1f122000"
    assert seq[7].data.hex() == "1fc00101"
    assert seq[8].data.hex() == "1f1150"


def test_compressed_raster_header_is_big_endian_with_zlib_body(raster):
    seq = get_protocol("compressed").build_print_sequence(
        raster, get_profile("m60"), PrintOptions(density=2)
    )
    bitmap = seq[5]
    body = bitmap.data[10:]
    # 1F 10 <bytesPerRow BE16> <height BE16> <length BE32>
    assert bitmap.data[:6].hex() == "1f10" + "0001" + "0002"
    assert int.from_bytes(bitmap.data[6:10], "big") == len(body)
    assert zlib.decompress(body) == raster.data
    assert bitmap.bulk is True


# ------------------------------------------------------ response parsing


@pytest.mark.parametrize("payload", [b"\xaa", b"O", b"K", b"OK"])
def test_success_bytes(payload):
    assert get_protocol("l11").parse_response(payload).kind == "success"


def test_credit_and_mtu_notifications():
    l11 = get_protocol("l11")
    credit = l11.parse_response(b"\x01\x04")
    assert (credit.kind, credit.value) == ("credit", 4)
    # MTU is little-endian, unlike the rest of the protocol.
    mtu = l11.parse_response(b"\x02\xf0\x00")
    assert (mtu.kind, mtu.value) == ("mtu", 240)


@pytest.mark.parametrize(
    ("code", "status"),
    [(0x01, "out_of_paper"), (0x02, "cover_open"), (0x03, "overheating"),
     (0x04, "low_battery"), (0x05, "cover_closed")],
)
def test_status_codes(code, status):
    response = get_protocol("l11").parse_response(bytes((0xFF, code)))
    assert (response.kind, response.value) == ("status", status)


def test_unrecognised_payloads():
    l11 = get_protocol("l11")
    assert l11.parse_response(b"") is None
    assert l11.parse_response(b"\x77\x77") is None
    assert l11.parse_response(b"\xff\x7f").value == "unknown_7f"


def test_both_protocols_decode_identically():
    """Query and notification handling is transport-level, not per-family."""
    l11, comp = get_protocol("l11"), get_protocol("compressed")
    for payload in (b"\xaa", b"\x01\x04", b"\x02\xf0\x00", b"\xff\x02", b"\x77"):
        assert l11.parse_response(payload) == comp.parse_response(payload)
    assert l11.build_battery_query().data == comp.build_battery_query().data
    assert l11.build_status_query().data == comp.build_status_query().data


# ---------------------------------------------------------- bulk splitting


def test_split_puts_raster_and_trailing_commands_in_one_stream(raster):
    seq = get_protocol("l11").build_print_sequence(
        raster, get_profile("p15"), PrintOptions(density=2)
    )
    preamble, bulk = _split_at_bulk(seq)
    assert len(preamble) == 5 + 15 + 4       # thickness + wakeup + enable
    assert bulk[:3].hex() == "1d7630"        # starts at the raster
    assert bulk[-4:].hex() == "10fff145"     # ends with stop, no stall before it


# ------------------------------------------------------------ flow control


def _collector():
    sent: list[bytes] = []

    async def write(chunk: bytes) -> None:
        sent.append(bytes(chunk))

    return sent, write


def test_send_chunks_by_packet_size_and_spends_credits():
    sent, write = _collector()
    fc = CreditFlowController(write, packet_size=4, tick_ms=1, starvation_ms=50)
    fc.grant(10)
    asyncio.run(fc.send(b"0123456789"))
    assert sent == [b"0123", b"4567", b"89"]
    assert fc.credits == 7


def test_starvation_recovery_drains_the_buffer_without_credits():
    sent, write = _collector()
    fc = CreditFlowController(write, packet_size=4, tick_ms=1, starvation_ms=10)
    asyncio.run(asyncio.wait_for(fc.send(b"abcdefgh"), timeout=2))
    assert b"".join(sent) == b"abcdefgh"


def test_profiles_without_credits_send_on_the_tick_alone():
    sent, write = _collector()
    fc = CreditFlowController(
        write, packet_size=3, tick_ms=1, starvation_ms=10_000, uses_credits=False
    )
    asyncio.run(asyncio.wait_for(fc.send(b"abcdef"), timeout=2))
    assert sent == [b"abc", b"def"]


def test_progress_is_reported_cumulatively():
    _, write = _collector()
    fc = CreditFlowController(write, packet_size=4, tick_ms=1, starvation_ms=50)
    fc.grant(10)
    seen: list[int] = []
    asyncio.run(fc.send(b"0123456789", seen.append))
    assert seen == [4, 8, 10]


def test_empty_send_is_a_noop():
    sent, write = _collector()
    fc = CreditFlowController(write, packet_size=4, tick_ms=1, starvation_ms=50)
    asyncio.run(fc.send(b""))
    assert sent == []


def test_compressed_raster_uses_a_16k_zlib_window(raster):
    """The vendor calls ``YxqZLib.code(raw, 14, 16384, 6)`` -- a 16 KB window.

    thermoprint uses fflate's default instead, which declares a 32 KB window.
    That matters: an inflater initialised with 16 KB rejects a 32 KB stream
    outright, while a 16 KB stream decodes on both. Since the firmware's buffer
    size is unknown, the narrower window is the safe choice.
    """
    seq = get_protocol("compressed").build_print_sequence(
        raster, get_profile("m60"), PrintOptions(density=2)
    )
    body = seq[5].data[10:]
    assert body[0] >> 4 == 6, "CINFO must be 6 (16 KB), not 7 (32 KB)"

    narrow = zlib.decompressobj(14)
    assert narrow.decompress(body) + narrow.flush() == raster.data
    assert zlib.decompress(body) == raster.data  # and a 32 KB inflater too
