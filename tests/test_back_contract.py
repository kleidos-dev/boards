# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Every board with a model has a back drawing, in the back's frame, of the back's contract.

``_shared/emit_back_svg.py`` is the only writer of
``<device>/svg/back.svg``, the drawing of what a board prints on its back,
seen from behind (``_shared/schema.md``, "Back drawings";
``_shared/board_faces.py``, the back frame). A model's builder lays its legend
groups on the back of the model, so the frame is the contract that matters
most: x runs from the case's left edge as seen from behind, and the case
outline is the front's mirrored. A back drawn in the front's frame would put
every print on the model mirrored.

This pins: one back for each board with a model and none for another, and
the drawings of the side faces (``FACE_PRINTS``, the Core2 v1.3's top) held to
the same contract; its
case outline first, and the mirror of the front's; the legend groups as flat
ink, with no key's group (a back has no keys); the annotations last; no
screen or demo screen, and hotspots only on a back that has a control (the
CoreInk's reset key); and the writer's idempotence.

Host-only: no build, no hardware, no network.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT
SHARED = CAD / "_shared"
sys.path.insert(0, str(SHARED))
import emit_back_svg  # noqa: E402  after the sys.path set-up above

SVG = "{http://www.w3.org/2000/svg}"
#: The back drawings that print anything, as {board: {plane: {mark, ...}}};
#: every other back is the outline its prints will be drawn in.
BACK_PRINTS: dict[str, dict[str, set[str]]] = {
    "cardputer": {
        "label": {
            "adv-flag",
            "audio-lines",
            "audio-rails",
            "bat-in",
            "bat-out",
            "battery",
            "battery-lines",
            "bmi270",
            "chg-ic",
            "cn809",
            "codec-data",
            "dcdc-sy7088",
            "dcdc-sy8089",
            "divider",
            "es8311",
            "ext-names",
            "ext-table",
            "headphones",
            "hp-det",
            "i2c-lines",
            "i2s-pins",
            "jack",
            "jack-pins",
            "key-matrix",
            "key-matrix-names",
            "lcd",
            "lcd-pins",
            "line-key",
            "m5-stack",
            "mic",
            "mosfets",
            "ns4150",
            "port-a",
            "port-a-switch",
            "rails-3v3",
            "rails-out",
            "speaker",
            "stamp-s3a",
            "switch",
            "tca8418",
            "usb",
            "usb-5vin",
            "vbat-sense",
        }
    },
    "coreink": {"label": {"back-label"}},
    "m5stack-core2-v13": {"sticker": {"back-label"}},
    "m5stickc-plus-se": {
        "label": {
            "banner",
            "banner-bars",
            "battery",
            "bps",
            "btn-b-mark",
            "ce",
            "cube",
            "esp32",
            "fcc",
            "fields",
            "giteki",
            "i2c",
            "lcd-mic",
            "lcd-mic-lines",
            "maker",
            "model-name",
            "pin-cells",
            "pin-names",
            "pmic-rtc",
            "port",
            "power",
            "weee",
        }
    },
    "sticks3": {"label": {"back-label"}},
    "tdeck-plus": {
        "frame": {"tdeck-frame"},
        "frame-line": {"tdeck-frame-line"},
        "badge": {"tdeck-badge"},
        "base": {"lilygo-base"},
    },
    "m5stickc-plus1": {"label": {"back-label"}},
    "m5stickc-plus2": {"label": {"back-label"}},
}
#: The backs that carry a control, as {board: its targets' names}: such a back
#: has a ``hotspots`` group just before its annotations and names each control
#: there; no other back has the group.
BACK_CONTROLS: dict[str, set[str]] = {
    "coreink": {"Reset"},
}
#: The drawings of another face than the front and the back, as
#: {(board, face): {plane: {mark, ...}}}; the writer's ``FACE_PRINTS``.
FACE_DRAWINGS: dict[tuple[str, str], dict[str, set[str]]] = {
    ("cardputer", "left"): {"side": {"five-volt-switch", "grove-pins"}},
    ("cardputer", "top"): {"strip": {"btn-rst", "ir-led", "micro-sd", "stamp-name", "switch-g0"}},
    ("coreink", "left"): {"side": {"side-label"}},
    ("m5stack-core2-v13", "top"): {"rating": {"rating-label"}},
    ("sticks3", "left"): {"strip": {"stick-s3"}},
    ("cores3-se", "top"): {"rating": {"rating-label"}, "port-tag": {"port-tag"}},
}


def back(device_id: str) -> ET.Element:
    return ET.fromstring((CAD / device_id / "svg" / "back.svg").read_text(encoding="utf-8"))  # noqa: S314  (this repository's own file)


def boards_with_models() -> list[str]:
    """The boards with a model: a model's spec and a front drawing.

    A modeled part that is no board (the microSD card a flow inserts) has a
    spec and no front, and so no back.
    """
    return sorted(
        p.name
        for p in CAD.iterdir()
        if (p / "model" / "spec.json").is_file() and (p / "svg" / "front.svg").is_file()
    )


def test_each_board_with_a_model_has_a_back_and_no_other_board_has_one() -> None:
    found = sorted(p.name for p in CAD.iterdir() if (p / "svg" / "back.svg").is_file())
    assert found == boards_with_models() == sorted(emit_back_svg.BOARDS)


@pytest.mark.parametrize("device_id", sorted(emit_back_svg.BOARDS))
def test_a_back_draws_the_front_outline_mirrored_first(device_id: str) -> None:
    """The case as seen from behind: the front's outline across the case's width."""
    text = (CAD / device_id / "svg" / "back.svg").read_text(encoding="utf-8")
    first = emit_back_svg.front_outline(text)
    assert 'id="case-outline"' in first, first
    spec = emit_back_svg.device(device_id)
    front = (CAD / device_id / "svg" / "front.svg").read_text(encoding="utf-8")
    found_fill = re.search(r'fill="([^"]+)"', first)
    assert found_fill is not None, first
    fill = found_fill.group(1)
    assert first + "\n" == emit_back_svg.back_outline(
        emit_back_svg.front_outline(front), spec.body_w, fill
    )


@pytest.mark.parametrize("device_id", sorted(emit_back_svg.BOARDS))
def test_a_back_holds_its_contract_and_nothing_of_a_fronts(device_id: str) -> None:
    root = back(device_id)
    ids = [el.get("id") for el in root.iter() if el.get("id")]
    assert len(ids) == len(set(ids)), device_id
    for front_only in ("screen-active", "screen-demo"):
        assert front_only not in ids, device_id
    assert root[-1].get("id") == "annotations", "the annotations are the drawing's last group"
    controls = BACK_CONTROLS.get(device_id)
    assert ("hotspots" in ids) == (controls is not None), device_id
    if controls is not None:
        spots = root[-2]
        assert spots.get("id") == "hotspots" and spots.get("display") == "none", device_id
        assert {spot.get("id") for spot in spots} == {f"hs-{name}" for name in controls}
        case = emit_back_svg.device(device_id)
        for spot in spots:
            assert spot.get("data-face") == "back", spot.attrib
            x, y, r = (float(spot.attrib[a]) for a in ("cx", "cy", "r"))
            assert 0.0 <= x <= case.body_w and 0.0 <= y <= case.body_h, spot.attrib
            assert r == pytest.approx(
                min(float(spot.attrib["data-w"]), float(spot.attrib["data-h"])) / 2, abs=5e-4
            )
        names = {el.text for el in root[-1]}
        assert controls <= names, "a back names its controls in the margin"
    assert [el.get("id") for el in root.iter() if el.get("id") == "annotations"] == ["annotations"]
    found: dict[str, set[str]] = {}
    for group in root.iter(f"{SVG}g"):
        if "legend" not in (group.get("class") or "").split():
            continue
        assert group.get("data-key") is None, "a back has no keys"
        assert set(group.attrib) == {"class", "data-mark", "data-plane"}, group.attrib
        found.setdefault(group.get("data-plane", ""), set()).add(group.get("data-mark", ""))
        drawn = [el for el in group.iter() if el is not group]
        assert drawn, group.attrib
        for el in drawn:
            assert el.tag.removeprefix(SVG) in {"text", "polygon", "rect", "circle", "path", "g"}
            assert "legend" not in (el.get("class") or "").split(), "a group in a group"
            assert not {"opacity", "filter", "clip-path", "mask"} & set(el.attrib), el.attrib
            for paint in ("fill", "stroke"):
                assert "url(" not in el.get(paint, ""), el.attrib
    assert found == BACK_PRINTS.get(device_id, {}), device_id


def test_the_side_drawings_are_the_writers_and_no_other() -> None:
    """A ``svg/<face>.svg`` of a side face exists exactly where the writer draws one."""
    found = sorted(
        (p.parent.parent.name, p.stem)
        for p in CAD.glob("*/svg/*.svg")
        if p.stem in ("top", "bottom", "left", "right")
    )
    assert found == sorted(emit_back_svg.FACE_PRINTS) == sorted(FACE_DRAWINGS)


@pytest.mark.parametrize("board_face", sorted(FACE_DRAWINGS))
def test_a_side_drawing_holds_the_backs_contract(board_face: tuple[str, str]) -> None:
    """Its case outline first (the face's rectangle), flat legend groups, the annotations last."""
    board, face = board_face
    root = ET.fromstring((CAD / board / "svg" / f"{face}.svg").read_text(encoding="utf-8"))  # noqa: S314  (this repository's own file)
    shapes = [el for el in root if el.tag.removeprefix(SVG) in {"rect", "path", "polygon"}]
    assert shapes and shapes[0].get("id") == "case-outline", board_face
    assert root[-1].get("id") == "annotations", board_face
    found: dict[str, set[str]] = {}
    for group in root.iter(f"{SVG}g"):
        if "legend" not in (group.get("class") or "").split():
            continue
        assert set(group.attrib) == {"class", "data-mark", "data-plane"}, group.attrib
        found.setdefault(group.get("data-plane", ""), set()).add(group.get("data-mark", ""))
        for el in group.iter():
            if el is not group:
                assert "legend" not in (el.get("class") or "").split(), "a group in a group"
                assert not {"opacity", "filter", "clip-path", "mask"} & set(el.attrib), el.attrib
    assert found == FACE_DRAWINGS[board_face], board_face


def test_a_path_mirrored_twice_is_the_path() -> None:
    """Absolute and relative moves, lines, arcs (their sweep and turn) and curves."""
    d = (
        "M 3 0 H 37 A 3 3 15 0 1 40 3 V 53 L 30 56 C 20 56 10 50 3 53 Q 1 40 0 30 Z "
        "M 1.7 4 a 2.3 2.3 0 1 0 4.6 0 l -1 2 h -2 z"
    )
    once = emit_back_svg.mirror_path(d, 40.0)
    assert once.startswith("M 37 0 H 3 A 3 3 -15 0 0 0 3 V 53 L 10 56 C 20 56 30 50 37 53")
    twice = emit_back_svg.mirror_path(once, 40.0)
    numbers = [float(t) for t in re.findall(r"-?\d*\.?\d+", twice)]
    assert numbers == [float(t) for t in re.findall(r"-?\d*\.?\d+", d)]


def test_the_writer_writes_what_is_committed() -> None:
    """Running it again changes nothing: the backs in git are its output."""
    before = {
        (name, "back"): (CAD / name / "svg" / "back.svg").read_bytes()
        for name in emit_back_svg.BOARDS
    }
    before.update(
        {
            (name, face): (CAD / name / "svg" / f"{face}.svg").read_bytes()
            for name, face in emit_back_svg.FACE_PRINTS
        }
    )
    assert emit_back_svg.main([]) == 0
    for (name, face), data in before.items():
        assert (CAD / name / "svg" / f"{face}.svg").read_bytes() == data, (name, face)
