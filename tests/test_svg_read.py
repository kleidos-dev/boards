# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""A drawing's text is read as SVG writes it, and in time that grows with its length.

``_shared/svg_read.py`` reads the numbers, the start tags and the attributes
that the generators and the model's checks take from a drawing. What it must
give is pinned here, and that a text holding a long run which never becomes
what is looked for is read once, not once from each of its characters.

Host-only: no build, no hardware, no network.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))
import check_board_model  # noqa: E402  after the sys.path set-up above
import emit_back_svg  # noqa: E402  after the sys.path set-up above
import kicad_schematic  # noqa: E402  after the sys.path set-up above
import legend_mesh  # noqa: E402  after the sys.path set-up above
import media_meta  # noqa: E402  after the sys.path set-up above
import svg_read  # noqa: E402  after the sys.path set-up above

#: How long a hostile text is, and the seconds that reading it may take:
#: linear code needs milliseconds, a pattern tried again from each character
#: far more than the bound.
LONG = 50_000
SECONDS = 2.0


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("1 2", [1.0, 2.0]),
        ("-1.5+2.25", [-1.5, 2.25]),
        ("1.5.5", [1.5, 0.5]),
        ("12. 3", [12.0, 3.0]),
        (".5-.25", [0.5, -0.25]),
        ("1e3,1E-2", [1000.0, 0.01]),
        ("1e", [1.0]),
        ("e3 - .", [3.0]),
        ("", []),
    ],
)
def test_numbers_are_read_as_svg_writes_them(text: str, found: list[float]) -> None:
    assert svg_read.numbers(text) == found


def test_tags_are_the_start_tags_of_the_elements_named() -> None:
    text = '<g><rect x="1"/><path d="M0 0\n1 1"/></g><rectangle/><text>a</text>'
    assert list(svg_read.tags(text, "rect", "path")) == ['<rect x="1"/>', '<path d="M0 0\n1 1"/>']
    assert list(svg_read.tags(text, "circle")) == []


def test_attributes_are_read_whole_or_refused() -> None:
    assert svg_read.attributes("<rect>") == {}
    assert svg_read.attributes('<rect x="1" data-key="a=b" xlink:href="#q"/>') == {
        "x": "1",
        "data-key": "a=b",
        "xlink:href": "#q",
    }
    assert svg_read.attributes('<rect\n  x = "1"\n  y=""/>') == {"x": "1", "y": ""}
    for tag in ('<rect x="1>', '<rect "1">', '<rect x "1">', "<rect x='1' \"2\">"):
        with pytest.raises(ValueError, match="a tag"):
            svg_read.attributes(tag)


def test_an_element_is_read_to_its_own_end() -> None:
    text = '<title id="t">A</title><g/><desc>B</desc><title>C</title>'
    title = svg_read.element_text(text, "title")
    assert title is not None and title[0] == "A"
    desc = svg_read.element_text(text, "desc", title[1])
    assert desc is not None and desc[0] == "B"
    later = svg_read.element_text(text, "title", desc[1])
    assert later is not None and later[0] == "C"
    assert svg_read.element_text(text, "metadata") is None
    assert svg_read.element_text("<title>never closed", "title") is None
    assert svg_read.element_text(text, "title", later[1]) is None


def _outline(body: str, tmp_path: Path) -> tuple[tuple[float, ...], object]:
    path = tmp_path / "front.svg"
    path.write_text(f"<svg><defs><rect width='1'/></defs>{body}</svg>", encoding="utf-8")
    polygon, screen = check_board_model.svg_outline(path)
    return tuple(round(v, 6) for v in (*polygon.bounds, polygon.area)), screen


def test_a_fronts_outline_and_screen_are_read_from_its_shapes(tmp_path: Path) -> None:
    """The first shape outside ``<defs>``, and the rect that says it is the active screen."""
    case = '<rect x="0" y="0" width="10" height="20"/>'
    screen = '<rect x="1" id="screen-active" y="2" width="3" height="4"/>'
    other = '<rect id="screen-other" x="9" y="9" width="1" height="1"/>'
    assert _outline(case + other + screen, tmp_path) == (
        (0.0, 0.0, 10.0, 20.0, 200.0),
        (1.0, 2.0, 4.0, 6.0),
    )
    rounded, none = _outline('<rect width="10" height="20" rx="2"/>', tmp_path)
    assert none is None and rounded[:4] == (0.0, 0.0, 10.0, 20.0) and 196 < rounded[4] < 200
    assert _outline('<polygon points="0,0 4,0 4,2"/>', tmp_path)[0] == (0.0, 0.0, 4.0, 2.0, 4.0)
    ringed = '<path d="M0 0H10V10H0Z M2 2h2v2h-2z"/>'
    assert _outline(ringed, tmp_path)[0] == (0.0, 0.0, 10.0, 10.0, 96.0)
    with pytest.raises(ValueError, match="no case outline"):
        _outline("<g/>", tmp_path)


def test_a_path_is_read_command_by_command() -> None:
    """Lines, arcs and curves, absolute and relative, with their repeats."""
    rings = check_board_model.path_rings("M 0 0 10 0 l 0 10 -10 0 z m 1 1 H 3 v 2 h -2 z")
    assert rings == [
        [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)],
        [(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)],
    ]
    (arc,) = check_board_model.path_rings("M 0 0 A 5 5 0 0 1 10 0 Z")
    assert arc[-1] == pytest.approx((10.0, 0.0), abs=1e-9)
    assert max(abs((x - 5) ** 2 + y**2 - 25) for x, y in arc) < 1e-6
    (relative,) = check_board_model.path_rings("M 2 3 a 5 5 0 0 1 10 0 z")
    assert relative[-1] == pytest.approx((12.0, 3.0), abs=1e-9)
    (curve,) = check_board_model.path_rings("M 0 0 C 0 1 1 1 1 0 q 1 -1 2 0")
    assert curve[-1] == pytest.approx((3.0, 0.0))
    (flat,) = check_board_model.path_rings("M 0 0 A 0 5 0 0 1 4 4")
    assert flat == [(0.0, 0.0), (4.0, 4.0)]
    with pytest.raises(ValueError, match="unsupported path command"):
        check_board_model.path_rings("M 0 0 S 1 1 2 2")


def test_the_parts_a_rail_names_are_found() -> None:
    assert kicad_schematic.part_references("U1, Q3 and SW102") == {"U1", "Q3", "SW102"}
    assert kicad_schematic.part_references("U1Q3, the cell") == {"U1", "Q3"}
    assert kicad_schematic.part_references("battery, 12 V") == set()


def test_a_back_mirrors_each_shape_a_front_may_be_outlined_with() -> None:
    svg = '<svg><defs><rect x="9"/></defs><polygon points="0,0 4,0 4,2"/><rect/></svg>'
    assert emit_back_svg.front_outline(svg) == '<polygon points="0,0 4,0 4,2"/>'
    with pytest.raises(ValueError, match="no case outline"):
        emit_back_svg.front_outline("<svg><g/></svg>")
    back = emit_back_svg.back_outline('<polygon points="0,0 4,0 4,2" stroke="#111"/>', 10, "#fff")
    assert back == '<polygon id="case-outline" points="10,0 6,0 6,2" fill="#fff"/>\n'
    rect = emit_back_svg.back_outline(
        '<rect x="1" y="2" width="3" height="4" rx="1" stroke="#111" stroke-width="0.2"/>',
        10,
        "#fff",
    )
    assert rect == (
        '<rect id="case-outline" x="6" y="2" width="3" height="4" rx="1" fill="#fff" '
        'stroke="#111" stroke-width="0.2"/>\n'
    )
    with pytest.raises(ValueError, match="not an element"):
        emit_back_svg.back_outline("rect", 10, "#fff")


_TAG = "SPDX-" + "License-Identifier:"
HOSTILE: dict[str, Callable[[], object]] = {
    "numbers, digits": lambda: svg_read.numbers("1" * LONG + "e"),
    "a path, digits": lambda: check_board_model._TOKEN.findall("1" * LONG + "!"),
    "a legend's path, digits": lambda: legend_mesh._PATH_TOKEN.findall("1" * LONG + "x"),
    "a mirrored path, digits": lambda: emit_back_svg._PATH_TOKEN.findall("1" * LONG + "!"),
    "tags, never closed": lambda: list(svg_read.tags("<rect " * LONG, "rect")),
    "attributes, one long name": lambda: svg_read.attributes("<rect " + "a" * LONG + '="1">'),
    "attributes, a long value": lambda: svg_read.attributes('<rect a="' + "b" * LONG + '">'),
    "an element, never closed": lambda: svg_read.element_text("<title>" * (LONG // 7), "title"),
    "part references, capitals": lambda: kicad_schematic.part_references("A" * LONG),
    "an address, spaces": lambda: media_meta._without_email("A" + " " * LONG + "B"),
    "an address, brackets": lambda: media_meta._without_email("A" + "<" * LONG),
    "a tag of a file, spaces": lambda: media_meta._tag_of(f"{_TAG} A{' ' * LONG}B"),
    "an e-mail address, letters": lambda: media_meta.deny_hits("a" * LONG),
}


@pytest.mark.parametrize("name", HOSTILE)
def test_a_long_run_that_never_matches_is_read_once(name: str) -> None:
    start = time.perf_counter()
    HOSTILE[name]()
    assert time.perf_counter() - start < SECONDS
