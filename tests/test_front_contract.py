# SPDX-License-Identifier: MIT
"""Every drawn front keeps the elements its readers rely on, and no vendor artwork.

``_shared/emit_front_svg.py`` is the only writer of ``<board>/svg/front.svg``,
and ``_shared/schema.md`` is the contract those files answer to: one glass
rectangle, one group of outside annotations, one group of press targets, and
no vendor demo screen (a vendor's screen artwork is not ours to publish). A
reader strips the annotations and the targets and refuses a front without the
glass, so a front that quietly lost one would publish a board with mm callouts
on it, or leave a finger overlay nowhere to land.

This pins all of it: the elements are there and are what they say, the
targets sit on the case, the ids are unique and named as the schema says, and
the two touch boards' zone targets are the touch sensor's own bands rather
than the decoration printed on the glass. It also pins the generator's
idempotence: running it again writes the same bytes.

Host-only: no build, no hardware, no network.
"""

from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT
GENERATOR = CAD / "_shared" / "emit_front_svg.py"

#: Every face a hotspot may name, from ``_shared/schema.md``.
FACES = {"front", "left", "right", "top", "bottom"}

#: What each front's hotspot group holds, as (the named controls, how many
#: keycaps). The keycaps are counted rather than listed: they are the legends
#: printed on the board, which the generator owns.
EXPECTED: dict[str, tuple[set[str], int]] = {
    "sticks3": ({"BtnA", "BtnB", "Power"}, 0),
    "m5stickc-plus1": ({"BtnA", "BtnB", "Power"}, 0),
    "m5stickc-plus2": ({"BtnA", "BtnB", "Power"}, 0),
    "m5stickc-plus-se": ({"BtnA", "BtnB", "Power"}, 0),
    "m5stack-core2-v13": ({"TouchA", "TouchB", "TouchC"}, 0),
    "cores3-se": ({"TouchA", "TouchB", "TouchC"}, 0),
    "coreink": ({"DialUp", "DialMid", "DialDown", "Power", "BtnEXT"}, 0),
    "cardputer": (set(), 56),
    "tdeck-plus": ({"Trackball"}, 35),
}

#: The fronts that wrap what they print in ``<g class="legend">`` groups, as
#: (how many keys each has, the other prints by plane) (``_shared/schema.md``,
#: "Legends"). No other front prints anything: every front is held to this.
LEGEND_GROUPS: dict[str, tuple[int, dict[str, set[str]]]] = {
    "cardputer": (56, {"panel": {"brand-panel"}, "stamp": {"stamp-label"}}),
    "tdeck-plus": (
        35,
        {
            "glass": {"lilygo-glass"},
            "plate": {"band-print", "bottom-print"},
            "plate-marks": {"round-marks"},
        },
    ),
}
SVG_NS = "http://www.w3.org/2000/svg"
#: What a keyboard board's ``keyboard`` block in ``measurements.json`` holds:
#: its grid and its wiring (``_shared/schema.md``, "Field rules"). No legend.
KEYBOARD_FIELDS = {
    "rows",
    "cols",
    "origin_x_mm",
    "origin_y_mm",
    "key_w_mm",
    "key_h_mm",
    "gap_mm",
    "controller",
    "i2c_addr",
    "notes",
}

#: The FT6x36 boards: the sensor's rows below the display and the columns a
#: contact there is split into (the Kleidos firmware's
#: ``src/config/device_config.h`` and ``src/hal/common/m5_touch_button_input.cpp``).
TOUCH_BAND_PX = 40
TOUCH_COLUMNS = 3


def front(device_id: str) -> ET.Element:
    """Parse one device's generated front."""
    return ET.fromstring((CAD / device_id / "svg" / "front.svg").read_text(encoding="utf-8"))


def group(root: ET.Element, group_id: str) -> ET.Element:
    """Return the one element with *group_id*, or fail saying it is missing."""
    found = root.findall(f".//*[@id='{group_id}']")
    assert len(found) == 1, f"expected exactly one '{group_id}', found {len(found)}"
    return found[0]


def case_box(device_id: str) -> tuple[float, float]:
    """The device's case, in mm, from the file the front is drawn against."""
    measured = json.loads((CAD / device_id / "measurements.json").read_text(encoding="utf-8"))
    return float(measured["case"]["width"]), float(measured["case"]["height"])


@pytest.fixture(scope="module")
def devices() -> list[str]:
    """Every device folder that carries a generated front."""
    found = sorted(p.name for p in CAD.iterdir() if (p / "svg" / "front.svg").is_file())
    assert found == sorted(EXPECTED), "a front appeared or vanished"
    return found


def test_every_front_carries_the_three_contract_elements(devices):
    """The glass, the annotations and the targets."""
    for device_id in devices:
        root = front(device_id)
        for element_id in ("screen-active", "annotations", "hotspots"):
            group(root, element_id)


def test_no_front_draws_a_vendor_screen_or_an_image(devices):
    """The panel is bare: no demo screen, no embedded raster, no clip left for one."""
    for device_id in devices:
        text = (CAD / device_id / "svg" / "front.svg").read_text(encoding="utf-8")
        root = ET.fromstring(text)
        assert not root.findall(".//*[@id='screen-demo']"), device_id
        assert "screen-clip_" not in text, device_id
        assert not [el for el in root.iter() if el.tag.endswith("}image")], device_id
        assert "data:image" not in text, device_id


def test_the_hotspot_group_draws_nothing(devices):
    """It is geometry, not artwork: a front renders the same with or without it."""
    for device_id in devices:
        assert group(front(device_id), "hotspots").get("display") == "none", device_id


def test_the_annotations_hold_the_outside_callouts_and_nothing_else(devices):
    """The mm dimensions, the title, and the names of the keys in a board's walls.

    The Sticks name their two side keys, the CoreInk its power key and its top key.

    Everything in the group is text in the margins; the legends printed on the
    hardware stay on the face, where a reader of the published front sees them.
    """
    for device_id in devices:
        annotations = group(front(device_id), "annotations")
        texts = [child.text or "" for child in annotations]
        assert all(child.tag.endswith("text") for child in annotations), device_id
        case_w, case_h = case_box(device_id)
        assert f"{case_w:g} mm" in texts, device_id
        assert f"{case_h:g} mm" in texts, device_id
        if device_id.startswith(("sticks3", "m5stickc")):
            assert {"Power", "BtnB"} <= set(texts), device_id
        if device_id == "coreink":
            assert {"Power", "BtnEXT"} <= set(texts), device_id


def test_every_target_names_a_face_and_sits_on_the_case(devices):
    """A hotspot is a point on the device, in the front view's own mm."""
    for device_id in devices:
        case_w, case_h = case_box(device_id)
        for spot in group(front(device_id), "hotspots"):
            name = spot.get("id", "")
            assert spot.get("data-face") in FACES, f"{device_id} {name}"
            x, y, r = (float(spot.get(a, "nan")) for a in ("cx", "cy", "r"))
            assert 0.0 <= x <= case_w, f"{device_id} {name}: x {x}"
            assert 0.0 <= y <= case_h, f"{device_id} {name}: y {y}"
            assert r > 0.0, f"{device_id} {name}: r {r}"
            width = float(spot.get("data-w", "nan"))
            height = float(spot.get("data-h", "nan"))
            assert r == pytest.approx(min(width, height) / 2, abs=5e-4), name


def test_each_front_names_the_controls_it_has(devices):
    """A front that lost a control, or grew one, has to say so here."""
    for device_id in devices:
        ids = [spot.get("id", "")[len("hs-") :] for spot in group(front(device_id), "hotspots")]
        named, keys = EXPECTED[device_id]
        assert len(ids) == len(set(ids)), device_id
        assert {name for name in ids if not name.startswith("key-")} == named, device_id
        assert len([name for name in ids if name.startswith("key-")]) == keys, device_id


def test_no_front_repeats_an_id(devices):
    """Ids have to be unique: the contact sheet merges all nine into one file."""
    for device_id in devices:
        ids = [element.get("id") for element in front(device_id).iter() if element.get("id")]
        assert len(ids) == len(set(ids)), device_id


def test_a_key_id_is_addressable(devices):
    """A keycap's id is a slug; its printed legend rides along in a label."""
    for device_id in ("cardputer", "tdeck-plus"):
        for spot in group(front(device_id), "hotspots"):
            name = spot.get("id", "")
            assert name.replace("-", "").replace("_", "").isalnum(), f"{device_id} {name}"
            if name.startswith("hs-key-"):
                assert spot.get("data-label"), name


def legend_groups(root: ET.Element) -> list[ET.Element]:
    """Every ``<g class="legend">`` of a front, in the drawing's order."""
    return [g for g in root.iter(f"{{{SVG_NS}}}g") if "legend" in (g.get("class") or "").split()]


def test_a_front_with_legend_groups_has_one_for_each_key(devices):
    """What is printed for a key sits in its own group, named as its hotspot.

    The board model's builder turns these groups into the model's legends and
    types nothing again (``_shared/legend_mesh.py``), so a key without a group
    is a key with no legend on the model, and a group may hold only what the
    builder draws: flat ink, with no opacity, gradient, filter or clip. A
    print that is no key's names itself and the surface it is printed on; a
    key's group is on the plane ``keys``.
    """
    for device_id in devices:
        root = front(device_id)
        groups = legend_groups(root)
        count, prints = LEGEND_GROUPS.get(device_id, (0, {}))
        keys = [g.get("data-key") for g in groups if g.get("data-key") is not None]
        assert len(keys) == count, device_id
        spots = {
            spot.get("id", "")[len("hs-key-") :]
            for spot in group(root, "hotspots")
            if spot.get("id", "").startswith("hs-key-")
        }
        assert set(keys) == (spots if count else set()), device_id
        assert len(set(keys)) == len(keys), device_id
        found: dict[str, set[str]] = {}
        for legend in groups:
            key, mark = legend.get("data-key"), legend.get("data-mark")
            assert (key is None) != (mark is None), legend.attrib
            assert set(legend.attrib) <= {"class", "data-key", "data-mark", "data-plane"}
            if mark is None:
                assert legend.get("data-plane", "keys") == "keys", legend.attrib
            else:
                found.setdefault(legend.get("data-plane", ""), set()).add(mark)
            drawn = [el for el in legend.iter() if el is not legend]
            assert drawn, legend.attrib
            for el in drawn:
                assert el.tag.split("}")[1] in {"text", "polygon", "rect", "circle", "path", "g"}
                assert "legend" not in (el.get("class") or "").split(), "a group in a group"
                assert not {"opacity", "filter", "clip-path", "mask"} & set(el.attrib), el.attrib
                for paint in ("fill", "stroke"):
                    assert "url(" not in el.get(paint, ""), el.attrib
                if el.get("stroke", "none") != "none":
                    assert el.get("fill") == "none", el.attrib
        assert found == prints, device_id


def test_a_keyboards_legends_are_listed_in_its_front_and_nowhere_else(devices):
    """``measurements.json`` holds a keyboard's grid and wiring, and no legend.

    What a key prints has one source, the generator's own table, and one
    place a reader finds it: the front, whose hotspot carries the legend
    (``data-label``) and whose legend group draws it. The two keyboards'
    ``measurements.json`` once repeated the legends by hand in a
    ``keyboard.matrix`` nothing read, which drifted from the fronts (four
    keys for the T-Deck Plus's bottom row of five, the Cardputer's block
    colors). The block is held to its geometry, which the Kleidos site's
    schematic of a board draws its caps from, so a second list cannot come
    back unnoticed.
    """
    for device_id in devices:
        measured = json.loads((CAD / device_id / "measurements.json").read_text(encoding="utf-8"))
        keys, _prints = LEGEND_GROUPS.get(device_id, (0, {}))
        assert ("keyboard" in measured) == bool(keys), device_id
        if not keys:
            continue
        assert set(measured["keyboard"]) == KEYBOARD_FIELDS, device_id
        labeled = [
            spot
            for spot in group(front(device_id), "hotspots")
            if spot.get("id", "").startswith("hs-key-") and spot.get("data-label")
        ]
        assert len(labeled) == keys, f"{device_id}: a key whose hotspot carries no legend"


@pytest.mark.parametrize("device_id", ["m5stack-core2-v13", "cores3-se"])
def test_the_touch_targets_are_the_firmware_zones(device_id):
    """Not the printed marks: the bands the touch sensor reports below the panel.

    The sensor reaches 40 rows below the last screen row and splits that strip
    into three equal columns of the panel's width, so the three targets follow
    ``screen-active`` — the same rectangle a screenshot is composited into.
    """
    root = front(device_id)
    glass = group(root, "screen-active")
    x, y, w, h = (float(glass.get(a, "nan")) for a in ("x", "y", "width", "height"))
    rows = float(str(glass.get("data-resolution")).split("x")[1])
    band_h = h * TOUCH_BAND_PX / rows
    band_w = w / TOUCH_COLUMNS
    spots = {spot.get("id"): spot for spot in group(root, "hotspots")}
    for index, letter in enumerate("ABC"):
        spot = spots[f"hs-Touch{letter}"]
        assert float(spot.get("cx")) == pytest.approx(x + band_w * (index + 0.5), abs=5e-4)
        assert float(spot.get("cy")) == pytest.approx(y + h + band_h / 2, abs=5e-4)
        assert spot.get("data-face") == "front"


def test_the_core2_targets_land_on_its_printed_rings():
    """The one board that prints a mark per zone is the cross-check.

    Its three rings are photo-measured and sit in ``measurements.json``; the
    targets are computed from the panel. They have to agree, or one of the two
    is wrong.
    """
    measured = json.loads(
        (CAD / "m5stack-core2-v13" / "measurements.json").read_text(encoding="utf-8")
    )
    rings = {b["id"]: b for b in measured["buttons"] if b["id"].startswith("Touch")}
    spots = {spot.get("id"): spot for spot in group(front("m5stack-core2-v13"), "hotspots")}
    for letter in "ABC":
        ring = rings[f"Touch{letter}"]
        spot = spots[f"hs-Touch{letter}"]
        assert abs(float(spot.get("cx")) - ring["center_x_mm"]) <= 0.25, letter
        assert abs(float(spot.get("cy")) - ring["center_y_mm"]) <= 0.25, letter


def test_the_coreink_plain_keys_sit_where_they_are_measured():
    """Its three plain keys: the top key, the power key on the dial's side, the reset on the back.

    None shows from the front (each is a tongue of the back shell, flush with
    its wall), so the front carries the two wall keys as targets on the edge
    their wall meets, and the back drawing carries the reset
    (``tests/test_back_contract.py``). ``measurements.json`` places each from
    the vendor's case file; the drawings' targets are held to it here.
    """
    measured = json.loads((CAD / "coreink" / "measurements.json").read_text(encoding="utf-8"))
    keys = {b["id"]: b for b in measured["buttons"]}
    assert "PowerSwitch" not in keys, "the power key is a push key"
    case_w = measured["case"]["width"]
    spots = {spot.get("id"): spot for spot in group(front("coreink"), "hotspots")}

    top, top_spot = keys["BtnEXT"], spots["hs-BtnEXT"]
    assert top["gpio"] == 5 and top["face"] == top_spot.get("data-face") == "top"
    assert float(top_spot.get("cx")) == pytest.approx(top["center_x_mm"], abs=0.01)
    assert float(top_spot.get("cy")) == 0.0
    assert float(top_spot.get("data-w")) == pytest.approx(top["width_mm"], abs=0.01)

    power, power_spot = keys["Power"], spots["hs-Power"]
    assert power["gpio"] == 27 and power["active"] == "low"
    assert power["face"] == power_spot.get("data-face") == "right"
    assert float(power_spot.get("cx")) == case_w == power["center_x_mm"]
    assert float(power_spot.get("cy")) == pytest.approx(power["center_y_mm"], abs=0.01)
    assert float(power_spot.get("data-h")) == pytest.approx(power["height_mm"], abs=0.01)
    dial = [float(spots[f"hs-{name}"].get("cy")) for name in ("DialUp", "DialMid", "DialDown")]
    assert power["center_y_mm"] > max(dial), "the power key is under the dial, not in its pocket"

    reset = keys["Reset"]
    assert reset["face"] == "back" and "hs-Reset" not in spots
    back = ET.fromstring((CAD / "coreink" / "svg" / "back.svg").read_text(encoding="utf-8"))
    reset_spot = group(back, "hs-Reset")
    # The back frame's x runs from the case's other edge.
    assert case_w - float(reset_spot.get("cx")) == pytest.approx(reset["center_x_mm"], abs=0.01)
    assert float(reset_spot.get("cy")) == pytest.approx(reset["center_y_mm"], abs=0.01)
    assert float(reset_spot.get("data-w")) == pytest.approx(reset["width_mm"], abs=0.01)
    assert float(reset_spot.get("data-h")) == pytest.approx(reset["height_mm"], abs=0.01)


def test_the_generator_writes_what_is_committed(tmp_path, devices):
    """Running it again changes nothing: the fronts in git are its output."""
    before = {name: (CAD / name / "svg" / "front.svg").read_bytes() for name in devices}
    sheet = (CAD / "fronts-contact-sheet.svg").read_bytes()
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--contact-sheet"],
        cwd=GENERATOR.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    for name, data in before.items():
        assert (CAD / name / "svg" / "front.svg").read_bytes() == data, name
    assert (CAD / "fronts-contact-sheet.svg").read_bytes() == sheet
