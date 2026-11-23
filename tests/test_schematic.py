# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""A board's schematic stays its ``netlist.yaml``, and the check catches what is planted.

``_shared/check_schematic.py`` compares the netlist KiCad exports from the
drawing with ``netlist.yaml``, pin by pin. KiCad is not needed here: a netlist
in KiCad's XML form is written from ``netlist.yaml`` and ``layout.yaml`` the way
a faithful drawing would export it, the check must pass it, and each kind of
drawing mistake (a pin on the wrong net, a pin left out, two nets joined, a
not-connected pin joined, a part the netlist lacks) is planted in a copy and
must fail it.

The generator is also run and must give back the committed files byte for
byte (it reads no KiCad library: every symbol is this project's).

Host-only: no hardware, no network.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pypdf import PdfWriter

import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml
from pytest import MonkeyPatch, TempPathFactory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))
import check_schematic as cs  # noqa: E402
import kicad_schematic as ks  # noqa: E402

BOARDS = sorted(p.parent.parent.name for p in ROOT.glob("*/schematic/netlist.yaml"))


def faithful_nodes(board: str) -> dict[str, list[tuple[str, str]]]:
    """net -> [(reference, our pin)], as a drawing true to netlist.yaml exports it."""
    folder = ROOT / board / "schematic"
    facts = yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8"))["components"]
    maps = cs.pin_maps(yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8")))
    nets: dict[str, list[Any]] = {}
    for ref, comp in facts.items():
        inverse: dict[str, list[str]] = {}
        for ours, vends in maps.get(ref, {}).items():
            for v in vends:
                inverse.setdefault(v, []).append(ours)
        for pin, net in comp["pins"].items():
            for ours in inverse.get(str(pin), [str(pin)]):
                key = f"unconnected-({ref}-Pad{ours})" if net == "NC" else f"/{net}"
                nets.setdefault(key, []).append((ref, ours))
    return nets


def write_xml(nets: dict[str, list[Any]], path: Path) -> Path:
    root = ET.Element("export", version="E")
    xnets = ET.SubElement(root, "nets")
    for code, (name, nodes) in enumerate(sorted(nets.items()), start=1):
        n = ET.SubElement(xnets, "net", code=str(code), name=name)
        for ref, pin in nodes:
            ET.SubElement(n, "node", ref=ref, pin=pin)
    ET.ElementTree(root).write(path)
    return path


@pytest.mark.parametrize("board", BOARDS)
def test_a_faithful_drawing_passes(board: str, tmp_path: Path) -> None:
    assert cs.compare(board, write_xml(faithful_nodes(board), tmp_path / "n.xml")) == []


def _first_signal_pins(nets: dict[str, Any]) -> list[str]:
    named = [k for k, v in nets.items() if k.startswith("/") and k != "/GND" and len(v) >= 2]
    return sorted(named)[:2]


@pytest.mark.parametrize("board", BOARDS)
def test_an_unconnected_pin_named_with_a_slash_stays_unconnected(
    board: str, tmp_path: Path
) -> None:
    """KiCad names an unconnected pin's net after the pin, "/" and all
    ("unconnected-(U1-IO11/CMD-Pad30)")."""
    nets = faithful_nodes(board)
    for key in [k for k in nets if k.startswith("unconnected-")]:
        nets[key.replace("-Pad", "-A/B-Pad")] = nets.pop(key)
    assert cs.compare(board, write_xml(nets, tmp_path / "n.xml")) == []


@pytest.mark.parametrize("board", BOARDS)
def test_a_pin_on_the_wrong_net_fails(board: str, tmp_path: Path) -> None:
    nets = faithful_nodes(board)
    a, b = _first_signal_pins(nets)
    nets[b].append(nets[a].pop())
    errors = cs.compare(board, write_xml(nets, tmp_path / "n.xml"))
    assert any("drawn on" in e for e in errors)


@pytest.mark.parametrize("board", BOARDS)
def test_a_pin_left_out_fails(board: str, tmp_path: Path) -> None:
    nets = faithful_nodes(board)
    a, _ = _first_signal_pins(nets)
    nets[a].pop()
    errors = cs.compare(board, write_xml(nets, tmp_path / "n.xml"))
    assert any("not drawn" in e for e in errors)


@pytest.mark.parametrize("board", BOARDS)
def test_two_nets_joined_fail(board: str, tmp_path: Path) -> None:
    nets = faithful_nodes(board)
    a, b = _first_signal_pins(nets)
    nets[a] += nets.pop(b)
    errors = cs.compare(board, write_xml(nets, tmp_path / "n.xml"))
    assert any("drawn on" in e for e in errors)


@pytest.mark.parametrize("board", BOARDS)
def test_a_not_connected_pin_joined_fails(board: str, tmp_path: Path) -> None:
    nets = faithful_nodes(board)
    nc = sorted(k for k in nets if k.startswith("unconnected-"))[0]
    a, _ = _first_signal_pins(nets)
    nets[a] += nets.pop(nc)
    errors = cs.compare(board, write_xml(nets, tmp_path / "n.xml"))
    assert any("netlist.yaml says NC" in e for e in errors)


@pytest.mark.parametrize("board", BOARDS)
def test_a_part_the_netlist_lacks_fails(board: str, tmp_path: Path) -> None:
    nets = faithful_nodes(board)
    nets["/GND"].append(("R999", "1"))
    errors = cs.compare(board, write_xml(nets, tmp_path / "n.xml"))
    assert any(e.startswith("R999: drawn but not in netlist.yaml") for e in errors)


@pytest.mark.parametrize("board", BOARDS)
def test_power_symbols_take_no_part(board: str, tmp_path: Path) -> None:
    nets = faithful_nodes(board)
    nets["/GND"].append(("#PWR001", "1"))
    assert cs.compare(board, write_xml(nets, tmp_path / "n.xml")) == []


@pytest.mark.parametrize("board", BOARDS)
def test_the_nets_section_agrees_with_the_components(board: str) -> None:
    """netlist.yaml's per-net index lists exactly the pins the components put on it."""
    doc = yaml.safe_load((ROOT / board / "schematic" / "netlist.yaml").read_text(encoding="utf-8"))
    derived: dict[str, set[Any]] = {}
    for ref, comp in doc["components"].items():
        for pin, net in comp["pins"].items():
            if net != "NC":
                derived.setdefault(net, set()).add(f"{ref}.{pin}")
    listed = {net: set(v["pins"]) for net, v in doc["nets"].items()}
    assert listed == derived


@pytest.mark.parametrize("board", BOARDS)
def test_the_generator_gives_back_the_committed_files(board: str, tmp_path: Path) -> None:
    folder = ROOT / board / "schematic"
    copy = tmp_path / "repo"
    (copy / "_shared").mkdir(parents=True)
    for f in (ROOT / "_shared").glob("*.py"):
        shutil.copy(f, copy / "_shared" / f.name)
    shutil.copytree(ROOT / "_shared" / "kicad", copy / "_shared" / "kicad")
    (copy / board / "schematic").mkdir(parents=True)
    for name in ("netlist.yaml", "layout.yaml"):
        shutil.copy(folder / name, copy / board / "schematic" / name)
    subprocess.run(
        [sys.executable, str(copy / "_shared" / "kicad_schematic.py"), board],
        check=True,
        capture_output=True,
    )
    for out in sorted((copy / board / "schematic").iterdir()):
        if out.name in ("netlist.yaml", "layout.yaml"):
            continue
        committed = folder / out.name
        assert committed.exists(), f"{out.name} is generated but not committed"
        assert out.read_bytes() == committed.read_bytes(), (
            f"{out.name} differs from the generator's"
        )


# --- what the generator adds to the drawing ---------------------------------


def test_zones_follow_the_drawing_sheets_grid() -> None:
    """KiCad's default A3 sheet: columns 1-8 and rows A-F, 50 mm apart from (10, 10) mm."""
    assert ks.zone(10.0, 10.0) == "A1"
    assert ks.zone(59.9, 59.9) == "A1"
    assert ks.zone(60.0, 60.0) == "B2"
    assert ks.zone(409.0, 286.0) == "F8"
    assert ks.zone(0.0, 0.0) == "A1"  # the margin belongs to the first zone


@pytest.mark.parametrize("board", BOARDS)
def test_parts_not_fitted_are_marked_dnp(board: str) -> None:
    """A part whose value is NC is drawn with KiCad's DNP mark, and no other part is."""
    folder = ROOT / board / "schematic"
    facts = yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8"))["components"]
    marked = set()
    for sch in folder.glob("*.kicad_sch"):
        for node in ks.parse(sch.read_text(encoding="utf-8")):
            if isinstance(node, list) and node and node[0] == "symbol":
                ref = next(
                    (
                        f[2]
                        for f in node
                        if isinstance(f, list) and f[:2] == ["property", "Reference"]
                    ),
                    "",
                )
                if ["dnp", "yes"] in node:
                    marked.add(str(ref))
    assert marked == {r for r, c in facts.items() if ks.not_fitted(c["value"])}


def test_a_part_is_not_fitted_when_its_value_is_nc_or_says_dnp() -> None:
    for value in ("NC", "nc", "NC(TBD)", "DNP", "RF_C(TBD:DNP)", "10K DNP"):
        assert ks.not_fitted(value), value
    for value in ("10K", "NCP1117", "DNPX", "ADNP", "0.1uF", ""):
        assert not ks.not_fitted(value), value


def _nets_sheet(b: ks.Builder) -> dict[str, Any]:
    sheet: dict[str, Any] = next(sh for sh in b.lay["sheets"] if sh.get("index") == "nets")
    return sheet


@pytest.mark.parametrize("board", BOARDS)
def test_the_gpio_tables_name_the_boards_own_chips(board: str) -> None:
    """Each GPIO table of the nets page is titled after a part the board has, and none is empty."""
    b = ks.Builder(board)
    tables = b.gpio_tables(_nets_sheet(b))
    assert tables, "no GPIO table"
    for t in tables:
        assert t["map"], t["title"]
        ref = re.search(r"\((U\d+)", t["title"])
        assert ref and ref.group(1) in b.comps, f"{t['title']!r} names no part of {board}"
        for gpio, v in t[
            "map"
        ].items():  # the pin's own net, or one past a series part the row names
            on = b.comps[ref.group(1)]["pins"].get(str(v["pin"]))
            assert (
                str(v["net"]) == "NC" or on == v["net"] or f"net {on}" in str(v.get("what", ""))
            ), f"{t['title']}: {gpio} is pin {v['pin']}, on {on}, not {v['net']}"


def test_the_gpio_tables_default_to_the_esp32_and_its_power_manager() -> None:
    b = ks.Builder("sticks3")
    b.net = {
        "esp32_gpio": {"GPIO1": {"pin": 1, "net": "A"}},
        "pmic_gpio": {"P0": {"pin": 2, "net": "NC"}, "P1": {"pin": 3, "net": "B", "what": "it"}},
    }
    soc, pm = b.gpio_tables({})
    assert (soc["title"], soc["what"], soc["sort"]) == ("ESP32-S3 GPIO (U20)", True, True)
    assert (pm["title"], pm["what"], pm["sort"]) == (
        "M5PM1 GPIO (U16)",
        True,
        False,
    )  # a pin says what it does
    titled = b.gpio_tables({"gpio_title": "ESP32 GPIO (U7)", "pmic_title": "AXP192 GPIO (U4)"})
    assert [t["title"] for t in titled] == ["ESP32 GPIO (U7)", "AXP192 GPIO (U4)"]
    b.net = {"esp32_gpio": {"GPIO1": {"pin": 1, "net": "A"}}, "pmic_gpio": {}}
    assert [t["title"] for t in b.gpio_tables({})] == ["ESP32-S3 GPIO (U20)"]  # no empty table
    b.net = {
        "gpio_maps": [
            {"title": "C3 GPIO (U5)", "map": {"GPIO2": {"pin": 6, "net": "X"}}, "what": False},
            {"title": "empty", "map": {}},
        ]
    }
    assert [(t["title"], t["what"]) for t in b.gpio_tables({})] == [("C3 GPIO (U5)", False)]


@pytest.mark.parametrize("board", BOARDS)
def test_test_points_are_named_tp_or_drawn_as_one(board: str) -> None:
    b = ks.Builder(board)
    for ref in b.comps:
        drawn = b.part(ref)["symbol"] == "kleidos:TestPoint"
        assert b.is_test_point(ref) == (ref.startswith("TP") or drawn), ref


@pytest.mark.parametrize("board", BOARDS)
def test_the_project_ignores_only_the_erc_checks_layout_names(board: str) -> None:
    """Every board ignores KiCad's two library checks; layout.yaml's erc_ignore adds its own, each
    said why."""
    folder = ROOT / board / "schematic"
    lay = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    pro = json.loads((folder / f"{board}.kicad_pro").read_text(encoding="utf-8"))
    ignored = {k for k, v in pro["erc"]["rule_severities"].items() if v == "ignore"}
    assert ignored == {"lib_symbol_issues", "lib_symbol_mismatch"} | set(
        lay.get("erc_ignore") or []
    )


def _pins(node: Any) -> Iterator[list[Any]]:
    for unit in (n for n in node if isinstance(n, list) and n and n[0] == "symbol"):
        yield from (n for n in unit if isinstance(n, list) and n and n[0] == "pin")


def test_an_own_symbol_takes_its_pin_length_and_may_hide_its_numbers() -> None:
    spec = {"left": ["1 VBUS", "2 CC1"], "right": ["3 GND"], "bottom": ["4 SHELL"]}
    plain = ks.own_symbol("J", spec)
    assert {p[4][1] for p in _pins(plain)} == {ks.PIN_LEN}
    assert not any(isinstance(n, list) and n[:1] == ["pin_numbers"] for n in plain)
    long = ks.own_symbol("J", dict(spec, pin_length=6.35, hide_pin_numbers=True))
    assert {p[4][1] for p in _pins(long)} == {6.35}
    assert ["pin_numbers", ["hide", "yes"]] in long


def test_a_transistor_pair_draws_base_collector_and_emitter() -> None:
    node = ks.own_symbol(
        "Q",
        {
            "kind": "mosfet_pair",
            "units": [
                {"type": "NPN", "b": "5", "c": "3", "e": "4"},
                {"type": "N", "g": "1", "d": "2", "s": "6"},
            ],
        },
    )
    names = [(p[5][1], p[6][1]) for p in _pins(node)]
    assert names == [("B", "5"), ("C", "3"), ("E", "4"), ("G", "1"), ("D", "2"), ("S", "6")]


@pytest.mark.parametrize("board", BOARDS)
def test_the_contents_page_boxes_take_the_layouts_size(board: str) -> None:
    """A drawing page's box on the contents page is root.sheet_box's
    height (27.94 mm by default)."""
    folder = ROOT / board / "schematic"
    lay = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    h = float((lay["root"].get("sheet_box") or (27.94, 31.75))[0])
    drawing = {sh["file"] for sh in lay["sheets"] if "index" not in sh}
    for node in ks.parse((folder / f"{board}.kicad_sch").read_text(encoding="utf-8")):
        if isinstance(node, list) and node and node[0] == "sheet":
            size = next(n for n in node if isinstance(n, list) and n[:1] == ["size"])
            sheetfile = next(
                n[2] for n in node if isinstance(n, list) and n[:2] == ["property", "Sheetfile"]
            )
            if sheetfile in drawing:
                assert float(size[2]) == pytest.approx(h), sheetfile


@pytest.mark.parametrize("board", BOARDS)
def test_the_power_tree_refuses_a_connection_the_netlist_lacks(board: str) -> None:
    b = ks.Builder(board)
    tree = b.lay.get("power_tree")
    if not tree:
        pytest.skip("no power tree")
    for a, z in tree["edges"]:
        b.check_edge(a, z)  # every drawn arrow is a connection
    part = next(n for n in tree["nodes"] if n in b.comps)
    stranger = next(
        n for n in tree["nodes"] if n not in b.comps and n not in b.comps[part]["pins"].values()
    )
    with pytest.raises(SystemExit, match="not a connection"):
        b.check_edge(part, stranger)  # a part to a rail it has no pin on


# --- the PDF's links ---------------------------------------------------------
# _shared/check_schematic_links.py holds every link of the committed PDF to the
# place it should land on. It must pass the committed PDF and fail a copy with
# a link sent to the wrong page, to a whole page, or 40 mm off its label, the
# links on a page's references taken away, a page's links taken away, a script
# link added, or KiCad's script put back in the document.


def _pdf(board: str) -> Path:
    return ROOT / board / "schematic" / f"{board}.pdf"


PDF_BOARDS = [b for b in BOARDS if _pdf(b).exists()]


def _planted(board: str, tmp_path: Path, plant: Any) -> Path:
    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter(clone_from=str(_pdf(board)))
    plant(pypdf, writer)
    out = tmp_path / "planted.pdf"
    with open(out, "wb") as fh:
        writer.write(fh)
    return out


def _annots(writer: PdfWriter, page: int) -> Any:
    """The /Annots array of a page (from 1) of a PDF being written."""
    return writer.pages[page - 1]["/Annots"].get_object()


def _page_links(writer: PdfWriter, page: int) -> list[Any]:
    return [a for a in _annots(writer, page) if a.get_object().get("/Subtype") == "/Link"]


@pytest.mark.parametrize("board", PDF_BOARDS)
def test_the_committed_pdf_links_lead_where_they_should(board: str) -> None:
    pytest.importorskip("pypdf")
    import check_schematic_links as csl

    errors, lines = csl.check(board, _pdf(board))
    assert errors == []
    assert any(line.startswith("bookmark") for line in lines)


def _place_link(writer: PdfWriter, page: int) -> Any:
    """A link of ``page`` that KiCad made and the PDF step sent to a place (/XYZ)."""
    for a in _page_links(writer, page):
        d = a.get_object().get("/Dest")
        if (
            d is not None
            and len(d) > 1
            and d[1] == "/XYZ"
            and d[0] != writer.pages[page - 1].indirect_reference
        ):
            return a.get_object()
    raise AssertionError(f"page {page} has no link to a place")


@pytest.mark.parametrize("board", PDF_BOARDS)
def test_a_link_to_the_wrong_page_fails(board: str, tmp_path: Path) -> None:
    import check_schematic_links as csl

    def plant(
        pypdf: ModuleType, writer: PdfWriter
    ) -> None:  # a [page/zone] of page 2, sent to page 2 itself
        a = _place_link(writer, 2)
        a[pypdf.generic.NameObject("/Dest")] = pypdf.generic.ArrayObject(
            [writer.pages[1].indirect_reference, pypdf.generic.NameObject("/FitB")]
        )

    errors, _ = csl.check(board, _planted(board, tmp_path, plant))
    assert any(e.startswith("page 2:") and "leads to page 2" in e for e in errors)


@pytest.mark.parametrize("board", PDF_BOARDS)
def test_a_link_to_the_whole_page_fails(board: str, tmp_path: Path) -> None:
    import check_schematic_links as csl

    def plant(
        pypdf: ModuleType, writer: PdfWriter
    ) -> None:  # the right page, but the whole of it, as KiCad leaves it
        a = _place_link(writer, 2)
        a[pypdf.generic.NameObject("/Dest")] = pypdf.generic.ArrayObject(
            [a["/Dest"][0], pypdf.generic.NameObject("/FitB")]
        )

    errors, _ = csl.check(board, _planted(board, tmp_path, plant))
    assert any("leads to the whole page" in e for e in errors)


@pytest.mark.parametrize("board", PDF_BOARDS)
def test_a_link_to_the_wrong_place_fails(board: str, tmp_path: Path) -> None:
    import check_schematic_links as csl

    def plant(pypdf: ModuleType, writer: PdfWriter) -> None:  # the right page, 40 mm off its label
        a = _place_link(writer, 2)
        d = a["/Dest"]
        d[2] = pypdf.generic.FloatObject(float(d[2]) + 40 * 72 / 25.4)

    errors, _ = csl.check(board, _planted(board, tmp_path, plant))
    assert any("mm from the nearest" in e for e in errors)


@pytest.mark.parametrize("board", PDF_BOARDS)
def test_a_reference_without_its_link_fails(board: str, tmp_path: Path) -> None:
    import check_schematic_links as csl

    lay = yaml.safe_load((ROOT / board / "schematic" / "layout.yaml").read_text(encoding="utf-8"))
    page = next(
        n for n, sh in enumerate(lay["sheets"], start=2) if "index" not in sh
    )  # the first drawing

    def plant(
        pypdf: ModuleType, writer: PdfWriter
    ) -> None:  # the links the PDF step adds on that page's references, taken away
        annots = _annots(writer, page)
        keep = [
            a for a in annots if "in the parts list" not in str(a.get_object().get("/Contents", ""))
        ]
        writer.pages[page - 1][pypdf.generic.NameObject("/Annots")] = pypdf.generic.ArrayObject(
            keep
        )

    errors, _ = csl.check(board, _planted(board, tmp_path, plant))
    assert any(
        e.startswith(f"page {page}: the reference") and "no link to the parts list" in e
        for e in errors
    )


@pytest.mark.parametrize("board", PDF_BOARDS)
def test_a_script_in_the_document_fails(board: str, tmp_path: Path) -> None:
    import check_schematic_links as csl

    def plant(
        pypdf: ModuleType, writer: PdfWriter
    ) -> None:  # KiCad's JSInit, put back in the catalog's name tree
        g = pypdf.generic
        js = writer._add_object(
            g.DictionaryObject(
                {
                    g.NameObject("/S"): g.NameObject("/JavaScript"),
                    g.NameObject("/JS"): g.TextStringObject("function ShM(a) {}"),
                }
            )
        )
        tree = g.DictionaryObject(
            {g.NameObject("/Names"): g.ArrayObject([g.TextStringObject("JSInit"), js])}
        )
        names = writer._root_object.setdefault(g.NameObject("/Names"), g.DictionaryObject())
        names.get_object()[g.NameObject("/JavaScript")] = writer._add_object(tree)

    errors, _ = csl.check(board, _planted(board, tmp_path, plant))
    assert any(e.startswith("script:") for e in errors)


@pytest.mark.parametrize("board", PDF_BOARDS)
def test_a_missing_link_fails(board: str, tmp_path: Path) -> None:
    import check_schematic_links as csl

    def plant(pypdf: ModuleType, writer: PdfWriter) -> None:  # every link of page 1 taken away
        writer.pages[0][pypdf.generic.NameObject("/Annots")] = pypdf.generic.ArrayObject()

    errors, _ = csl.check(board, _planted(board, tmp_path, plant))
    assert any(e.startswith("page 1: sheet") and "has no link" in e for e in errors)
    assert any(e.startswith("page 1: no link to page") for e in errors)


@pytest.mark.parametrize("board", PDF_BOARDS)
def test_a_script_link_fails(board: str, tmp_path: Path) -> None:
    import check_schematic_links as csl

    def plant(
        pypdf: ModuleType, writer: PdfWriter
    ) -> None:  # a KiCad-style property pop-up over nothing linked
        g = pypdf.generic
        annot = g.DictionaryObject(
            {
                g.NameObject("/Type"): g.NameObject("/Annot"),
                g.NameObject("/Subtype"): g.NameObject("/Link"),
                g.NameObject("/Rect"): g.ArrayObject(
                    [g.FloatObject(v) for v in (300, 300, 320, 310)]
                ),
                g.NameObject("/A"): g.DictionaryObject(
                    {
                        g.NameObject("/S"): g.NameObject("/JavaScript"),
                        g.NameObject("/JS"): g.TextStringObject('ShM([["Reference = R1"]]);'),
                    }
                ),
            }
        )
        _annots(writer, 3).append(writer._add_object(annot))

    errors, _ = csl.check(board, _planted(board, tmp_path, plant))
    assert any("matches nothing drawn" in e and "JavaScript" in e for e in errors)


# --- Kleidos additions and corrections ---------------------------------------
# netlist.yaml's ``kleidos`` list marks what the drawing adds to the vendor's
# print or corrects in it, each with its source. The generator marks each where
# it is drawn ("K3", dotted wires for an added connection) and lists it on the
# contents page; check_schematic.py holds that each entry is well formed,
# marked and listed, and what the index pages and the title blocks say of them
# (the wording, the marker repeated wherever an index page shows the element
# again, what a pin on no net says); check_schematic_links.py where their links
# land. The tests plant a set of their own on a copy of the Plus2, in place of
# the board's.

ADD_BOARD = "m5stickc-plus2"
ADDITIONS: list[dict[str, Any]] = [
    {
        "id": "K1",
        "kind": "addition",
        "what": "U9 answers at I2C address 0x51.",
        "element": {"i2c": "U9"},
        "source": {
            "type": "datasheet",
            "cite": "BM8563 datasheet V1.1, I2C interface (write address A2h)",
        },
    },
    {
        "id": "K2",
        "kind": "addition",
        "what": "U9 pin 7 left open.",
        "element": {"pin": "U9.7"},
        "source": {"type": "bench", "cite": "bench/plus2-u9.md, 2026-11-17"},
    },
    {
        "id": "K3",
        "kind": "correction",
        "what": "SDA is one net.",
        "vendor": "two labels",
        "element": {"net": "SDA"},
        "source": {"type": "vendor-doc", "cite": "M5Stack docs page, PinMap"},
    },
    {
        "id": "K4",
        "kind": "addition",
        "what": "R10 is fitted.",
        "element": {"part": "R10"},
        "source": {"type": "firmware", "cite": "Kleidos firmware, src/hal/i2c.cpp: kFittedR10"},
    },
    {
        "id": "K5",
        "kind": "addition",
        "what": "GPIO21 is SDA.",
        "element": {"gpio": "GPIO21"},
        "source": {"type": "firmware", "cite": "Kleidos firmware, src/hal/i2c.cpp: kSdaPin"},
    },
    {
        "id": "K6",
        "kind": "correction",
        "what": "R13 is 2.2K.",
        "vendor": "4.7K",
        "element": {"pull": "R13"},
        "source": {"type": "bench", "cite": "bench/plus2-r13.md, 2026-11-17"},
    },
    {
        "id": "K7",
        "kind": "addition",
        "what": "+3.3V is 3.3 V.",
        "element": {"rail": "+3.3V"},
        "source": {"type": "datasheet", "cite": "SY8089 datasheet, Vout equation"},
    },
    {
        "id": "K8",
        "kind": "addition",
        "what": "U9 pin 4 is grounded.",
        "element": {"pin": "U9.4"},
        "source": {"type": "datasheet", "cite": "BM8563 datasheet V1.1, pin table"},
    },
    {
        "id": "K9",
        "kind": "addition",
        "what": "IO9 is the in-package PSRAM's CS.",
        "element": {"pin": "U1.28"},
        "source": {"type": "datasheet", "cite": "ESP32-PICO-V3-02 datasheet, pin table"},
    },
]


def _with_additions(
    adds: list[dict[str, Any]] = ADDITIONS, wording: bool = True
) -> tuple[dict[str, Any], dict[str, Any]]:
    folder = ROOT / ADD_BOARD / "schematic"
    net = yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8"))
    lay = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    net["kleidos"] = [dict(a) for a in adds]
    notes = next(p for p in lay["root"]["panels"] if p["title"] == "Notes")
    claims = ks.ADD_WORDING in " ".join(notes["text"].split())
    if wording and not claims:
        notes["text"] = notes["text"].replace(
            "public documentation\n", f"public documentation,\n{ks.ADD_WORDING}\n", 1
        )
    elif not wording and claims:  # the Plus2's own notes claim its entries; take the claim out
        notes["text"] = " ".join(notes["text"].split()).replace(f", {ks.ADD_WORDING}", "")
    return net, lay


def test_additions_as_planted_are_well_formed() -> None:
    assert ks.additions_errors(*_with_additions()) == []


@pytest.mark.parametrize("board", BOARDS)
def test_each_boards_additions_are_well_formed_and_marked_only_when_present(board: str) -> None:
    folder = ROOT / board / "schematic"
    net = yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8"))
    lay = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    assert ks.additions_errors(net, lay) == []
    if not net.get("kleidos"):  # zero additions: no table, no marker, no claim in the notes
        root = (folder / f"{board}.kicad_sch").read_text(encoding="utf-8")
        assert ks.ADD_TITLE not in root
        assert cs.drawn_marks(board) == ({}, {})
    else:  # with additions: the contents page lists them
        root = (folder / f"{board}.kicad_sch").read_text(encoding="utf-8")
        assert ks.ADD_TITLE in root


@pytest.mark.parametrize(
    "change, message",
    [
        (lambda a: a[0]["source"].update(cite=" "), "source.cite is empty"),
        (
            lambda a: a[0].update(source={"type": "a forum post", "cite": "x"}),
            "source.type is one of",
        ),
        (lambda a: a[0].pop("source"), "source.type is one of"),
        (lambda a: a[2].pop("vendor"), "a correction says what the vendor's print shows"),
        (lambda a: a[0].update(vendor="x"), "'vendor' is a correction's"),
        (lambda a: a[0].update(kind="guess"), "kind 'guess'"),
        (lambda a: a[0].update(what=""), "no 'what'"),
        (lambda a: a[1].update(element={"pin": "U9.99"}), "pin U9.99 is not a pin"),
        (lambda a: a[3].update(element={"part": "R999"}), "part R999 is not in netlist.yaml"),
        (lambda a: a[2].update(element={"net": "GND"}), "net GND is not a net"),
        (lambda a: a[4].update(element={"gpio": "GPIO99"}), "gpio GPIO99 is in 0 GPIO tables"),
        (lambda a: a[0].update(element={"i2c": "U1"}), "i2c U1 is not a device"),
        (lambda a: a[5].update(element={"pull": "R1000"}), "pull R1000 is not a resistor"),
        (
            lambda a: a[6].update(element={"rail": "+12V"}),
            "rail +12V is not in netlist.yaml's rails",
        ),
        (lambda a: a[6].update(element={"rail": "+3.3V", "net": "SDA"}), "element is one of"),
        (lambda a: a[7].update(element={"pin": "U9.7"}), "marks the same pin as K2"),
        (lambda a: a[1].update(id="K9"), "this one should be K2"),
        (lambda a: a[1].update(id="R13"), "should be K2"),
    ],
)
def test_a_malformed_addition_fails(change: Callable[..., Any], message: str) -> None:
    adds = [{**a, "source": dict(a["source"]), "element": dict(a["element"])} for a in ADDITIONS]
    change(adds)
    errors = ks.additions_errors(*_with_additions(adds))
    assert any(message in e for e in errors), errors


def test_an_id_that_is_a_part_or_a_net_fails() -> None:
    net, lay = _with_additions()
    net["components"]["K1"] = {"value": "relay", "pins": {"1": "GND"}}
    assert any("also a part or a net" in e for e in ks.additions_errors(net, lay))


def test_the_notes_claim_additions_exactly_when_there_are_some() -> None:
    assert any("the notes say" in e for e in ks.additions_errors(*_with_additions(wording=False)))
    net, lay = _with_additions()
    net["kleidos"] = []
    assert any("but netlist.yaml has none" in e for e in ks.additions_errors(net, lay))


def test_the_layout_leaves_the_subtitle_and_title_block_wording_to_the_generator() -> None:
    net, lay = _with_additions()
    lay["root"]["subheading"] += f", {ks.ADD_SUBTITLE}"
    assert any(
        "root subheading" in e and "the generator's to add" in e
        for e in ks.additions_errors(net, lay)
    )
    net, lay = _with_additions()
    lay["title_block"]["comments"] = (lay["title_block"]["comments"] + ["One more line"] * 3)[
        :3
    ] + [ks.ADD_BLOCK_LINE]
    errors = ks.additions_errors(net, lay)
    assert any("title_block" in e and "the generator's to add" in e for e in errors)
    assert any(
        "the drawing sheet prints" in e for e in errors
    )  # and no room is left for the generator's line


def test_a_gpio_tables_chip_is_the_reference_that_opens_its_titles_brackets() -> None:
    assert ks.chip_of("ESP32-S3 GPIO (U20)") == "U20"
    assert ks.chip_of("ESP32-C3 GPIO (U5, keyboard)") == "U5"
    assert ks.chip_of("Pads") is None


def test_an_index_row_shows_its_element_and_what_hangs_on_it() -> None:
    """The elements whose Kleidos entries a row of an index table, or a box of the power tree,
    repeats."""
    net: dict[str, Any] = {
        "components": {
            "R1": {"pins": {"1": "A", "2": "GND"}},
            "U1": {"pins": {"1": "A", "2": "B", "3": "C"}},
        }
    }
    assert ks.index_keys(net, "nets", "A") == [("rail", "A")]  # a net's row shows no value of it
    assert ks.index_keys(net, "rails", "A") == [("rail", "A")]
    assert ks.index_keys(net, "tree", "A") == [("rail", "A")]
    assert ks.index_keys(net, "tree", "U1") == [("part", "U1")]
    assert ks.index_keys(net, "gpio", "GPIO4", 2, "SoC GPIO (U1)") == [
        ("gpio", "GPIO4", "SoC GPIO (U1)"),
        ("pin", "U1.2"),
    ]
    assert ks.index_keys(net, "gpio", "P0", 2, "Pads") == [("gpio", "P0", "Pads")]
    assert ks.index_keys(net, "i2c", "U1") == [("i2c", "U1"), ("part", "U1")]
    assert ks.index_keys(net, "pulls", "R1") == [("pull", "R1"), ("part", "R1")]
    assert ks.index_keys(net, "test_points", "R1") == [("part", "R1")]
    assert ks.index_keys(net, "parts", "R1") == [
        ("part", "R1"),
        ("pin", "R1.1"),
        ("pin", "R1.2"),
    ]  # its nets are printed
    assert ks.index_keys(net, "parts", "U1") == [("part", "U1")]  # "3 pins"


def test_a_pin_on_no_net_says_what_it_is_in_the_gpio_table() -> None:
    """The map's own text; else what the Kleidos entries on the row or the pin say; else nothing,
    since the
    Net cell already reads "not connected"."""
    b = ks.Builder("sticks3")
    gt = {"title": "SoC GPIO (U1)"}
    b.net = {"components": {}}
    b.add_at = {
        ("pin", "U1.7"): {"id": "K2", "what": "IO7 serves the flash."},
        ("gpio", "GPIO7", "SoC GPIO (U1)"): {"id": "K1", "what": "A strap."},
        ("pin", "U1.8"): {"id": "K3", "what": "Drives the LED."},
    }
    assert b.gpio_what(gt, "GPIO6", {"pin": 6, "net": "NC"}) == ""
    assert ks.NC_TEXT == "not connected"
    assert (
        b.gpio_what(gt, "GPIO7", {"pin": 7, "net": "NC"}) == "A strap. IO7 serves the flash."
    )  # in id order
    assert (
        b.gpio_what(gt, "GPIO7", {"pin": 7, "net": "NC", "what": "its own text"}) == "its own text"
    )
    assert (
        b.gpio_what(gt, "GPIO8", {"pin": 8, "net": "LED"}) == ""
    )  # a pin on a net keeps the map's text
    assert b.gpio_what(gt, "GPIO8", {"pin": 8, "net": "LED", "what": "the LED"}) == "the LED"


def test_a_gpio_in_two_tables_needs_its_table() -> None:
    net: dict[str, Any] = {
        "components": {},
        "gpio_maps": [
            {"title": "A (U1)", "map": {"GPIO1": {"pin": 1, "net": "X"}}},
            {"title": "B (U2)", "map": {"GPIO1": {"pin": 2, "net": "Y"}}},
        ],
        "kleidos": [
            {
                "id": "K1",
                "kind": "addition",
                "what": "w",
                "element": {"gpio": "GPIO1"},
                "source": {"type": "bench", "cite": "c"},
            }
        ],
    }
    lay = {"root": {"panels": [{"title": "Notes", "text": ks.ADD_WORDING}]}}
    assert any("say which with 'table'" in e for e in ks.additions_errors(net, lay))
    net["kleidos"][0]["element"]["table"] = "B (U2)"
    assert ks.additions_errors(net, lay) == []


@pytest.fixture(scope="module")
def planted_repo(tmp_path_factory: TempPathFactory) -> Path:
    """A copy of the Plus2's schematic sources with ADDITIONS planted, generated."""
    root = tmp_path_factory.mktemp("repo")
    (root / ADD_BOARD / "schematic").mkdir(parents=True)
    net, lay = _with_additions()
    folder = root / ADD_BOARD / "schematic"
    (folder / "netlist.yaml").write_text(
        yaml.safe_dump(net, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    (folder / "layout.yaml").write_text(
        yaml.safe_dump(lay, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    mp = pytest.MonkeyPatch()
    mp.setattr(ks, "ROOT", root)
    ks.main([ADD_BOARD])
    mp.undo()
    return root


def _dotted_wires(doc: list[Any]) -> int:
    return sum(
        1
        for n in doc
        if isinstance(n, list)
        and n[:1] == ["wire"]
        and ["type", ks.ADD_WIRE]
        in next(x for x in n if isinstance(x, list) and x[:1] == ["stroke"])
    )


def test_the_generator_marks_and_lists_every_addition(planted_repo: Path) -> None:
    folder = planted_repo / ADD_BOARD / "schematic"
    links = json.loads((folder / "links.json").read_text(encoding="utf-8"))
    for a in ADDITIONS:
        assert f"add-{a['id']}" in links["marks"], a["id"]
        assert links["marks"][f"add-{a['id']}"]["page"] != 1
        back = [
            j
            for j in links["jumps"]
            if j["page"] != 1 and j["to"]["page"] == 1 and a["id"] in j["alt"]
        ]
        assert back, f"no marker of {a['id']} leads to its row"
    root = (folder / f"{ADD_BOARD}.kicad_sch").read_text(encoding="utf-8")
    assert ks.ADD_TITLE in root
    assert any(
        k["title"] == ks.ADD_TITLE
        for k in next(o for o in links["outline"] if o["page"] == 1)["kids"]
    )
    # the added pins' and the added part's wires are dotted: U9.4 (to ground) and R10's two, which
    # the
    # layout draws without stubs, so they get one each; a correction (K3, K6) dots nothing
    dotted = {
        f.name: _dotted_wires(ks.parse(f.read_text(encoding="utf-8")))
        for f in folder.glob("*.kicad_sch")
    }
    assert dotted["rails.kicad_sch"] >= 1 and dotted["soc.kicad_sch"] == 2, dotted


def test_the_check_holds_a_generated_drawing_with_additions(
    planted_repo: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(cs, "ROOT", planted_repo)
    assert cs.additions(ADD_BOARD) == []
    assert cs.index_pages(ADD_BOARD) == []


@pytest.mark.parametrize("board", BOARDS)
def test_each_boards_index_pages_and_title_blocks_say_what_they_should(board: str) -> None:
    """The committed files: the wording under the heading and in every title block, each entry
    marked on
    every row and power-tree box that shows its element again, and what a pin on no net says."""
    assert cs.index_pages(board) == []


def _index_pages(board: str, folder: Path) -> dict[int, str]:
    lay = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    return {page: sh["file"] for page, sh in enumerate(lay["sheets"], start=2) if "index" in sh}


def test_an_entry_is_marked_wherever_an_index_page_shows_its_element_again(
    planted_repo: Path,
) -> None:
    """A rail's entry: on its row of the rails table, above each of its boxes in the power tree and
    on its
    row of the nets page; a part's: after its reference and on its row of the parts list; a pin's on
    no
    net: by its cross and on its GPIO's row, which says what the entry says."""
    folder = planted_repo / ADD_BOARD / "schematic"
    lay = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    index = {sh["index"]: page for page, sh in enumerate(lay["sheets"], start=2) if "index" in sh}
    boxes = sum(1 for n in lay["power_tree"]["nodes"] if n.split("@")[0] == "+3.3V")
    assert boxes >= 1
    monkey = pytest.MonkeyPatch()
    monkey.setattr(cs, "ROOT", planted_repo)
    markers, _ = cs.drawn_marks(ADD_BOARD)
    monkey.undo()
    assert sorted(markers["K7"]) == sorted([index["power"]] * (1 + boxes) + [index["nets"]])
    assert index["parts"] in markers["K4"] and any(p not in index.values() for p in markers["K4"])
    assert index["nets"] in markers["K9"] and any(p not in index.values() for p in markers["K9"])
    nets = (folder / "nets.kicad_sch").read_text(encoding="utf-8")
    assert '(text "IO9 is the in-package PSRAM\'s CS."' in nets
    facts = yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8"))
    open_pins = sum(
        1 for v in facts["esp32_gpio"].values() if str(v["net"]) == "NC" and not v.get("what")
    )
    assert open_pins > 1  # each reads "not connected" under Net, and only there
    assert nets.count(f'(text "{ks.NC_TEXT}"') == open_pins
    root = (folder / f"{ADD_BOARD}.kicad_sch").read_text(encoding="utf-8")
    assert f'public documentation, {ks.ADD_SUBTITLE}"' in root
    for name in [f"{ADD_BOARD}.kicad_sch"] + [sh["file"] for sh in lay["sheets"]]:
        assert re.search(
            r'\(comment \d "' + re.escape(ks.ADD_BLOCK_LINE) + r'"\)',
            (folder / name).read_text(encoding="utf-8"),
        ), name


def _drop_text(path: Path, body: str, nth: int = 1) -> None:
    """Take the nth text item reading ``body`` out of a KiCad sheet file."""
    text = path.read_text(encoding="utf-8")
    found = list(
        re.finditer(r'\n\t\(text "' + re.escape(body) + r'"\n.*?\n\t\)', text, flags=re.DOTALL)
    )
    m = found[nth - 1]
    path.write_text(text[: m.start()] + text[m.end() :], encoding="utf-8")


@pytest.mark.parametrize(
    "plant, message",
    [
        ("drop-nets-row-marker", "K7 is not marked on the row of +3.3V"),
        ("drop-tree-marker", "K7 is not marked on the power tree's box of +3.3V"),
        ("drop-parts-row-marker", "K4 is not marked on the row of R10 (parts)"),
        ("stray-row-marker", "K1 is marked on the row of +3.3V"),
        ("blank-what", "is on no net and says '' under"),
        ("wrong-what", "is on no net and says 'IO9 is something else.' under"),
        ("subtitle", "the line under the heading reads"),
        ("title-block", "page 2: the title block says"),
        ("claims-without-entries", "but netlist.yaml has none"),
    ],
)
def test_the_check_fails_index_pages_that_do_not_say_what_they_should(
    planted_repo: Path, tmp_path: Path, monkeypatch: MonkeyPatch, plant: Any, message: str
) -> None:
    root = tmp_path / "repo"
    shutil.copytree(planted_repo, root)
    folder = root / ADD_BOARD / "schematic"
    nets, power, parts, soc = (folder / f"{n}.kicad_sch" for n in ("nets", "power", "parts", "soc"))
    top = folder / f"{ADD_BOARD}.kicad_sch"
    if plant == "drop-nets-row-marker":
        _drop_text(nets, "K7")
    elif plant == "drop-tree-marker":  # the power tree is written before the rails table
        _drop_text(power, "K7", 1)
    elif plant == "drop-parts-row-marker":
        _drop_text(parts, "K4")
    elif plant == "stray-row-marker":
        nets.write_text(nets.read_text().replace('(text "K7"', '(text "K1"', 1))
    elif plant == "blank-what":  # K9's row says nothing under What it does
        _drop_text(nets, "IO9 is the in-package PSRAM's CS.")
    elif plant == "wrong-what":
        nets.write_text(
            nets.read_text().replace("IO9 is the in-package PSRAM's CS.", "IO9 is something else.")
        )
    elif plant == "subtitle":
        top.write_text(top.read_text().replace(f', {ks.ADD_SUBTITLE}"', '"', 1))
    elif plant == "title-block":
        soc.write_text(
            re.sub(
                r'\(comment \d "' + re.escape(ks.ADD_BLOCK_LINE) + r'"\)',
                "",
                soc.read_text(),
                count=1,
            )
        )
    elif plant == "claims-without-entries":
        net = yaml.safe_load((folder / "netlist.yaml").read_text())
        net["kleidos"] = []
        (folder / "netlist.yaml").write_text(
            yaml.safe_dump(net, sort_keys=False, allow_unicode=True)
        )
    monkeypatch.setattr(cs, "ROOT", root)
    errors = cs.index_pages(ADD_BOARD)
    assert any(message in e for e in errors), errors


@pytest.fixture(scope="module")
def bare_repo(tmp_path_factory: TempPathFactory) -> Path:
    """A copy of the Plus2's schematic sources with no Kleidos entry at all, generated."""
    root = tmp_path_factory.mktemp("bare")
    folder = root / ADD_BOARD / "schematic"
    folder.mkdir(parents=True)
    net, lay = _with_additions([], wording=False)
    (folder / "netlist.yaml").write_text(
        yaml.safe_dump(net, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    (folder / "layout.yaml").write_text(
        yaml.safe_dump(lay, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    mp = pytest.MonkeyPatch()
    mp.setattr(ks, "ROOT", root)
    ks.main([ADD_BOARD])
    mp.undo()
    return root


def test_a_board_without_entries_says_nothing_of_them(
    bare_repo: Path, monkeypatch: MonkeyPatch
) -> None:
    """No table, no marker, no word of them under the heading or in a title block; a pin on no net
    still
    says so on the nets page."""
    folder = bare_repo / ADD_BOARD / "schematic"
    monkeypatch.setattr(cs, "ROOT", bare_repo)
    assert cs.additions(ADD_BOARD) == [] and cs.index_pages(ADD_BOARD) == []
    assert cs.drawn_marks(ADD_BOARD) == ({}, {})
    for sch in folder.glob("*.kicad_sch"):
        assert ks.ADD_SUBTITLE.lower() not in sch.read_text(encoding="utf-8").lower(), sch.name
    assert f'(text "{ks.NC_TEXT}"' in (folder / "nets.kicad_sch").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "plant, message",
    [
        ("drop-marker", "K4: no marker on the drawing"),
        ("drop-row", "K2: no row in the contents page's table"),
        ("unlink-row", "K2: its row on the contents page leads nowhere"),
        ("stray-marker", "K10: marked on page(s)"),
        ("empty-source", "source.cite is empty"),
    ],
)
def test_the_check_fails_a_drawing_whose_additions_are_not_marked_and_listed(
    planted_repo: Path, tmp_path: Path, monkeypatch: MonkeyPatch, plant: Any, message: str
) -> None:
    root = tmp_path / "repo"
    shutil.copytree(planted_repo, root)
    folder = root / ADD_BOARD / "schematic"
    soc, top = folder / "soc.kicad_sch", folder / f"{ADD_BOARD}.kicad_sch"
    if plant == "drop-marker":  # R10's marker taken off the drawing
        soc.write_text(re.sub(r'\n\t\(text "K4"\n.*?\n\t\)', "", soc.read_text(), flags=re.DOTALL))
    elif plant == "drop-row":
        top.write_text(re.sub(r'\n\t\(text "K2"\n.*?\n\t\)', "", top.read_text(), flags=re.DOTALL))
    elif plant == "unlink-row":
        top.write_text(
            re.sub(
                r'(\(text "K2"\n.*?)\n\t+\(href "#\d+"\)',
                r"\1",
                top.read_text(),
                count=1,
                flags=re.DOTALL,
            )
        )
    elif plant == "stray-marker":
        soc.write_text(soc.read_text().replace('(text "K4"', '(text "K10"', 1))
    elif plant == "empty-source":
        net = yaml.safe_load((folder / "netlist.yaml").read_text())
        net["kleidos"][0]["source"]["cite"] = ""
        (folder / "netlist.yaml").write_text(
            yaml.safe_dump(net, sort_keys=False, allow_unicode=True)
        )
    monkeypatch.setattr(cs, "ROOT", root)
    errors = cs.additions(ADD_BOARD)
    assert any(message in e for e in errors), errors


# The links of a PDF with additions: exported once with kicad-cli, held by
# check_schematic_links.py, then each planted defect must fail it.


def _kicad_cli() -> str | None:
    return shutil.which(os.environ.get("KICAD_CLI", "kicad-cli"))


@pytest.fixture(scope="module")
def planted_pdf(planted_repo: Path) -> Path:
    if not _kicad_cli():
        pytest.skip("kicad-cli is not installed")
    pytest.importorskip("pypdf")
    shared = planted_repo / "_shared"
    shared.mkdir(exist_ok=True)
    for f in (ROOT / "_shared").iterdir():
        if f.suffix in (".py", ".json"):
            shutil.copy(f, shared / f.name)
    if not (shared / "kicad").exists():
        shutil.copytree(ROOT / "_shared" / "kicad", shared / "kicad")
    # what the PDF's metadata is written from: the board's identity and REUSE's license
    shutil.copy(ROOT / ADD_BOARD / "board.json", planted_repo / ADD_BOARD / "board.json")
    shutil.copy(ROOT / "REUSE.toml", planted_repo / "REUSE.toml")
    out = subprocess.run(
        [sys.executable, str(shared / "export_schematic.py"), ADD_BOARD],
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, out.stdout + out.stderr
    return planted_repo / ADD_BOARD / "schematic" / f"{ADD_BOARD}.pdf"


@pytest.mark.selftest
def test_the_links_of_a_pdf_with_additions_lead_both_ways(
    planted_pdf: Path, monkeypatch: MonkeyPatch
) -> None:
    import check_schematic_links as csl

    monkeypatch.setattr(csl, "ROOT", planted_pdf.parents[2])
    errors, lines = csl.check(ADD_BOARD, planted_pdf)
    assert errors == []
    assert sum(1 for line in lines if line.startswith("p1 ") and re.search(r"'K\d+'", line)) == len(
        ADDITIONS
    )


def _add_link(writer: PdfWriter, page: int, eid: str) -> Any:
    for annot in _annots(writer, page):
        a = annot.get_object()
        said = str(a.get("/Contents", ""))
        if a.get("/Subtype") == "/Link" and said.startswith((f"{eid}:", f"{eid} in the ")):
            return a
    raise AssertionError(f"no link of {eid} on page {page}")


@pytest.mark.selftest
@pytest.mark.parametrize(
    "plant, message",
    [
        ("row-off", "place 'K4'"),  # a row's link sent 40 mm off its marker
        ("marker-off", "place 'K4'"),  # a marker's link sent 40 mm off its row
        ("no-dest", "named destination add-K4"),
        ("moved-marker", "marker K4"),  # the marker moved away from R10's reference
        ("moved-row-marker", "marker K7"),  # a marker of the nets page moved off the row of +3.3V
    ],
)
def test_a_pdf_whose_additions_do_not_lead_both_ways_fails(
    planted_pdf: Path, tmp_path: Path, monkeypatch: MonkeyPatch, plant: Any, message: str
) -> None:
    import check_schematic_links as csl
    import pypdf

    g = pypdf.generic
    root = tmp_path / "repo"
    shutil.copytree(planted_pdf.parents[2], root)
    pdf = root / ADD_BOARD / "schematic" / f"{ADD_BOARD}.pdf"
    writer = pypdf.PdfWriter(clone_from=str(pdf))
    if plant == "row-off":
        d = _add_link(writer, 1, "K4")["/Dest"]
        d[2] = g.FloatObject(float(d[2]) + 40 * 72 / 25.4)
    elif plant == "marker-off":
        d = _add_link(writer, 2, "K4")["/Dest"]
        d[3] = g.FloatObject(float(d[3]) - 40 * 72 / 25.4)
    elif plant == "no-dest":

        def drop(node: Any) -> bool:  # the name tree may be flat or split into kids
            node = node.get_object()
            arr = node.get("/Names")
            if arr is not None:
                k = next((i for i in range(0, len(arr), 2) if str(arr[i]) == "add-K4"), None)
                if k is not None:
                    del arr[k : k + 2]
                    return True
            return any(drop(kid) for kid in node.get("/Kids", []))

        names: Any = writer._root_object["/Names"].get_object()
        assert drop(names["/Dests"])
    elif plant == "moved-marker":
        soc = root / ADD_BOARD / "schematic" / "soc.kicad_sch"
        text = soc.read_text()
        m = re.search(
            r'\(text "K4"\n\t+\(exclude_from_sim no\)\n\t+\(at ([\d.]+) ([\d.]+) 0\)', text
        )
        assert m is not None
        soc.write_text(
            text.replace(
                m.group(0),
                m.group(0).replace(
                    f"(at {m.group(1)} {m.group(2)} 0)",
                    f"(at {m.group(1)} {float(m.group(2)) + 30:.2f} 0)",
                ),
            )
        )
    elif plant == "moved-row-marker":
        nets = root / ADD_BOARD / "schematic" / "nets.kicad_sch"
        text = nets.read_text()
        m = re.search(
            r'\(text "K7"\n\t+\(exclude_from_sim no\)\n\t+\(at ([\d.]+) ([\d.]+) 0\)', text
        )
        assert m is not None
        nets.write_text(
            text.replace(
                m.group(0),
                m.group(0).replace(
                    f"(at {m.group(1)} {m.group(2)} 0)",
                    f"(at {m.group(1)} {float(m.group(2)) + 1.27:.2f} 0)",
                ),
            )
        )
    with open(pdf, "wb") as fh:
        writer.write(fh)
    monkeypatch.setattr(csl, "ROOT", root)
    errors, _ = csl.check(ADD_BOARD, pdf)
    assert any(message in e for e in errors), errors
