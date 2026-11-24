# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Draw a board's schematic in KiCad from its netlist and a layout.

Inputs, both in ``<board>/schematic/``:

- ``netlist.yaml``: every component, its value and each of its pins with the
  net it is on (the facts, with the public sources they come from);
- ``layout.yaml``: how to draw them: which symbol each part takes (one of
  this project's generic library, ``kleidos:<name>``, or the board's own,
  ``<board>:<name>``, defined in the same file), which
  sheet and block it sits in, and in what order.

Outputs, in the same folder: ``<board>.kicad_sym`` (our symbols),
``<board>.kicad_sch`` (the root sheet) and one ``.kicad_sch`` per child sheet,
``<board>.kicad_pro``, ``sym-lib-table`` and ``links.json`` (where each link of
the PDF lands, for ``schematic_pdf.py``). ``kicad-cli`` then runs the ERC and
writes the PDF and the SVGs (the board's ``schematic/README.md``).

The drawing connects by net labels, not by wires: every pin ends in a short
stub carrying its net's name as a global label, a ground symbol, or a
no-connect flag. After a label of a net that other pages also carry, one
``[page/zone]`` per such page names the zone of the net's label there (the
grid the drawing sheet prints in its border: ``3/C4``) and is a text linked to
that page; ``schematic_pdf.py`` then sends the link to that label. A part
documented as not fitted (value NC) carries KiCad's DNP mark. Neighboring pins of one part on one
net share a
stub bar and a single label. Each block is laid out on its own: the main parts
in a row, the two-pin parts in columns of flat rows beside or below them. The
root sheet is the contents: one box per sheet, linked to its page, with what is
on it, beside a legend, notes and the revision history; every other sheet
links back to it and to each page. A sheet with ``index`` in ``layout.yaml`` is
a page of tables written from ``netlist.yaml`` once the drawing is laid out:
``power`` (the power tree and the rails), ``nets`` (every net on more than one
page and every rail, the GPIO maps, I2C, test points, pull-ups and
pull-downs), ``parts`` (every part, its value, kind, nets, DNP and place),
each place in them a link.
What the drawing adds to the vendor's print or corrects in it (``kleidos`` in
``netlist.yaml``, each with its source) is marked where it is drawn by its id
("K3", bold, in ``MARK_COLOR``), an added connection's wires dotted, and listed
on the contents page, each id linked to its marker and each marker back to its
row. The index pages repeat the marker wherever they show the element again:
on its row of each table and above its box of the power tree (``index_keys``).
A board with entries says so under its heading and in every title block
(``ADD_SUBTITLE``, ``ADD_BLOCK_LINE``); a board with none draws exactly as it
did before. A pin on no net says so in the GPIO tables, or what its Kleidos
entry says of it (``gpio_what``).
Wires and pin lines take one width (``LINE_MIL``, the width kicad-cli gives
pins, set as the project's netclass and default line). The same netlist and layout give the same
files byte for byte
(uuids are derived from names).

Usage: ``python3 _shared/kicad_schematic.py <board>``. Every symbol is this
project's: the board's own in ``<board>.kicad_sym`` and the generic ones
(passives, diodes, transistors, switches, connectors, grounds) in
``kleidos.kicad_sym``, drawn by ``generic_symbol``; no KiCad library is read.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import uuid as uuidlib
from collections.abc import Callable, Iterable, Iterator, Sequence
from itertools import pairwise
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "kicad"))
import kleidos_kicad as kit
from paths import ROOT, OutsideError, board_id

# The style's numbers come from the kit (kicad/style.json): the grid, the pin
# pitch and length, the stub, the text sizes, the one line width, the zone
# grid and the title block of the drawing sheet, the explicit colors.
STYLE = kit.style()
GRID: float = STYLE["lines"]["grid"]
PITCH: float = STYLE["lines"]["pin_pitch"]
PIN_LEN: float = STYLE["lines"]["pin_length"]
STUB: float = STYLE["lines"]["stub"]
CHAR_W = 1.12  # an estimate of KiCad's stroke font advance at 1.27 mm (with margin)
LABEL_CHAR_W = 1.1  # a global label's length per character of its name
LABEL_PAD = 1.6  # ... plus its outline's (both fitted on rendered labels of 6 to 13 characters)
FONT: float = STYLE["text"]["body"]
ROW = 8.89  # pitch of the flat two-pin rows
GAP = 7.62  # between items in a row, between rows in a block
COL_GAP = 7.62  # between columns of two-pin rows
BLOCK_PAD = 5.08
SHEET_GAP = 7.62
REF_FONT: float = STYLE["text"]["small"]  # the "[n]" page links after a label
REF_CHAR_W = 0.95  # their advance per character at REF_FONT (with margin)
REF_GAP = 0.8
ROOT_FONT: float = STYLE["text"]["running"]  # the contents page's running text
LINE_PITCH: float = STYLE["text"][
    "line_pitch"
]  # a multi-line text's line pitch, per unit of its size
# Wires and pin lines, in mils: one width for every connection. kicad-cli draws a
# symbol's pins (and any symbol line left at the default width) at its own fixed
# symbol line width, 6 mil, whatever the project's default line thickness says
# (SCH_ITEM::GetEffectivePenWidth takes m_SymbolLineWidth for an item of a
# library symbol, and the CLI never sets it); a pin has no width of its own. So
# the wires take the pins' 6 mil, and a wire never meets a thinner pin.
LINE_MIL = STYLE["lines"]["connection_mil"]
BUS_MIL = STYLE["lines"]["bus_mil"]
PAPER = {"A4": (297.0, 210.0), "A3": (420.0, 297.0), "A2": (594.0, 420.0)}
# The zone grid the kit's drawing sheet prints in the border (KiCad's default
# geometry): columns numbered from 1 and rows lettered from A, every 50 mm from
# the frame's outer corner at (10, 10) mm. A cross-reference names a place as
# "page/zone": 3/C4.
ZONE_ORIGIN = float(STYLE["sheet"]["margin"])
ZONE_STEP = float(STYLE["sheet"]["zone_step"])
# What the title block takes from a page's right-bottom corner: nothing is
# placed right of KEEPOUT_X and below KEEPOUT_Y mm from it; the page row
# ("Page 3 of 9") goes NAV_X, NAV_Y mm from it, above the block.
KEEPOUT_X = float(STYLE["sheet"]["keepout"]["right"])
KEEPOUT_Y = float(STYLE["sheet"]["keepout"]["bottom"])
NAV_X = float(STYLE["sheet"]["page_row"]["right"])
NAV_Y = float(STYLE["sheet"]["page_row"]["bottom"])
# Where a link's destination puts its target in the reader's window: the
# target sits this far (mm) right of the window's left edge and below its top,
# at this zoom (2.0: the 1.27 mm text reads at about 7 pt). The PDF step
# (schematic_pdf.py) writes it, check_schematic_links.py holds it.
VIEW_LEFT = 30.0
VIEW_TOP = 20.0
VIEW_ZOOM = 2.0
TABLE_PITCH: float = STYLE["text"]["table_row"]  # row pitch of the index pages' tables
TABLE_GAP = 2.54  # between two columns of a table
# Kleidos additions and corrections (``kleidos`` in netlist.yaml): what the
# drawing shows beyond the vendor's print, or differently from it, each with its
# source. Every one is marked where it is drawn by its id ("K3"), bold, in this
# color, which nothing else on the drawing takes, and is a row of the table on
# the contents page; an added connection's wires are also dotted, at the one
# wire width (a pin that carries its label at its end gets a stub to show it).
# A correction takes the marker only.
MARK_COLOR = kit.explicit("dark")["addition"]
MARK_FONT: float = STYLE["text"]["small"]
MARK_CHAR_W = 1.1  # a marker's advance per character (bold, with margin)
MARK_GAP = 1.5  # from what it follows
TREE_MARK = 1.1  # a power-tree box's markers: this far above its top edge
ADD_WIRE = "dot"  # an added connection's wires: dotted, at the one width (a dash at 6 mil
# shows one gap on a 2.54 mm stub and reads as a solid line)
ADD_KINDS = ("addition", "correction")
ADD_SOURCES = ("datasheet", "vendor-doc", "firmware", "bench")
ADD_ELEMENTS = ("pin", "part", "net", "gpio", "i2c", "pull", "rail")
ADD_ID = re.compile(r"K([1-9]\d*)")
ADD_TITLE = "Kleidos additions and corrections"
# what the contents page's notes say when a board has any, and only then
ADD_WORDING = "with Kleidos additions and corrections listed on page 1"
# ... what the generator then adds to the line under the contents page's heading,
# and the line it adds to every page's title block (its next comment)
ADD_SUBTITLE = "with Kleidos additions and corrections"
ADD_BLOCK_LINE = "With Kleidos additions and corrections, listed on page 1"
ADD_HEAD = ["Id", "Kind", "What", "Source"]  # the additions table, page 1 and its continuation
ADD_WRAPS = [None, None, 56, 48]
BLOCK_LINES = STYLE["sheet"][
    "comment_lines"
]  # the comments the kit's drawing sheet prints in the title block
RULE_COLOR = kit.explicit("dark")["rule"]  # a table's and the power tree's rules
# What every page's title block prints from the project (kit.cell_findings
# holds each line to its cell): the license and where the files live.
LICENSE = "MIT"
SOURCE_URL = "github.com/kleidos-dev/boards"
NC_TEXT = "not connected"  # a pin on no net, in the GPIO tables


def zone(x: float, y: float, paper: str = "A3") -> str:
    """The drawing sheet's zone of a point: "C4" is row C, column 4."""
    w, h = PAPER[paper]
    cols = max(1, math.ceil((w - 2 * ZONE_ORIGIN) / ZONE_STEP - 1e-6))
    rows = max(1, math.ceil((h - 2 * ZONE_ORIGIN) / ZONE_STEP - 1e-6))
    col = min(max(int((x - ZONE_ORIGIN) // ZONE_STEP) + 1, 1), cols)
    row = min(max(int((y - ZONE_ORIGIN) // ZONE_STEP), 0), rows - 1)
    return f"{'ABCDEFGHJK'[row]}{col}"


def natural_zone(z: str) -> tuple[Any, ...]:
    """Sort key of a zone: row, then column (A2 before A10, A10 before B1)."""
    return (z[0], int(z[1:]))


# The kind of part a generic symbol (kleidos.kicad_sym) stands for, in the parts list.
STD_KINDS = [
    (r"kleidos:R", "Resistor"),
    (r"kleidos:C", "Capacitor"),
    (r"kleidos:L", "Inductor"),
    (r"kleidos:FerriteBead.*", "Ferrite bead"),
    (r"kleidos:D_TVS", "TVS diode"),
    (r"kleidos:D_Schottky", "Schottky diode"),
    (r"kleidos:LED", "LED"),
    (r"kleidos:Q_NMOS", "N-MOSFET"),
    (r"kleidos:D_Photo", "Photodiode"),
    (r"kleidos:SW_Push", "Push button"),
    (r"kleidos:TestPoint", "Test point"),
    (r"kleidos:USB_C_Receptacle.*", "USB-C receptacle"),
    (r"kleidos:Conn_.*", "Connector"),
]


def natural(ref: str) -> tuple[Any, ...]:
    """Sort key: C2 before C10, then by prefix."""
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def part_references(text: str) -> set[str]:
    """The parts a text names ("U1, Q3"): capital letters, then a number."""
    runs = re.findall(r"[A-Z]+|\d+|[^A-Z\d]+", text)
    return {a + b for a, b in pairwise(runs) if "A" <= a[0] <= "Z" and b[0].isdecimal()}


def not_fitted(value: object) -> bool:
    """A part the vendor documents as not fitted: its value is NC (or NC(TBD)),
    or says DNP as a word (DNP, RF_C(TBD:DNP))."""
    v = str(value).upper()
    return v.split("(")[0].strip() == "NC" or bool(re.search(r"(?<![A-Z0-9])DNP(?![A-Z0-9])", v))


def title_block_lines(lay: dict[str, Any], adds: bool) -> list[tuple[str, str]]:
    """Every line the title blocks of a board print, with the kit's cell it goes in."""
    tb = lay.get("title_block") or {}
    lines = [("comments", str(tb.get("company", "")))]
    lines += [
        ("comments", str(c))
        for c in list(tb.get("comments", [])) + ([ADD_BLOCK_LINE] if adds else [])
    ]
    titles = [(lay.get("root") or {}).get("title", "")] + [
        sh.get("name", "") for sh in lay.get("sheets", [])
    ]
    lines += [("title", f"{tb.get('title', '')}: {t}") for t in titles]
    lines += [("file", sh["file"]) for sh in lay.get("sheets", []) if "file" in sh]
    lines += [("license", LICENSE), ("source", SOURCE_URL)]
    return lines


def title_block_errors(lay: dict[str, Any], adds: bool) -> list[str]:
    """The title-block lines wider than their cell of the kit's drawing sheet."""
    return kit.cell_findings(title_block_lines(lay, adds))


def gpio_maps(net: dict[str, Any], sh: dict[str, Any]) -> list[dict[str, Any]]:
    """The GPIO maps of the nets page, each {title, map, what, wrap, sort};
    a map with no entry is left out.

    ``gpio_maps`` in netlist.yaml lists them, each {title, map, what}
    (``what: false`` leaves out the "What it does" column), in GPIO order.
    Without it: ``esp32_gpio``, in GPIO order, and ``pmic_gpio`` (a power
    manager's or an I/O expander's pins), in the order listed and with a
    "What it does" column when any of its pins has one; their titles are the
    nets sheet's ``gpio_title`` and ``pmic_title``."""
    maps = net.get("gpio_maps")
    if maps is None:
        pm = net.get("pmic_gpio") or {}
        maps = [
            {
                "title": sh.get("gpio_title", "ESP32-S3 GPIO (U20)"),
                "map": net.get("esp32_gpio") or {},
                "what": True,
                "wrap": 60,
                "sort": True,
            },
            {
                "title": sh.get("pmic_title", "M5PM1 GPIO (U16)"),
                "map": pm,
                "what": any("what" in v for v in pm.values()),
                "wrap": 44,
                "sort": False,
            },
        ]
    return [
        {
            "title": m["title"],
            "map": m["map"],
            "what": m.get("what", True),
            "wrap": m.get("wrap", 60),
            "sort": m.get("sort", True),
        }
        for m in maps
        if m.get("map")
    ]


def element_key(el: dict[str, Any]) -> tuple[Any, ...]:
    """What an addition marks, as a key: ("pin", "U9.5"), ("gpio", "GPIO21", table or None)."""
    kind = next(k for k in ADD_ELEMENTS if k in el)
    return (kind, str(el[kind]), el.get("table")) if kind == "gpio" else (kind, str(el[kind]))


def additions_by_element(
    net: dict[str, Any], lay: dict[str, Any]
) -> dict[tuple[Any, ...], dict[str, Any]]:
    """The Kleidos additions and corrections by the element each names
    (``element_key()``; a GPIO's key carries its table's title, the one table
    that lists it where the entry names none)."""
    nets_sheet: dict[str, Any] = next(
        (sh for sh in lay.get("sheets", []) if sh.get("index") == "nets"), {}
    )
    out: dict[tuple[Any, ...], dict[str, Any]] = {}
    for e in net.get("kleidos") or []:
        el = e["element"]
        if "gpio" in el and not el.get("table"):
            el = dict(
                el,
                table=next(
                    t["title"] for t in gpio_maps(net, nets_sheet) if str(el["gpio"]) in t["map"]
                ),
            )
        out[element_key(el)] = e
    return out


def chip_of(title: str) -> str | None:
    """The part a GPIO table is about: the reference that opens its title's
    brackets ("ESP32-S3 GPIO (U20)" is U20's)."""
    m = re.search(r"\(([A-Z]+\d+)\b", title)
    return m.group(1) if m else None


def index_keys(
    net: dict[str, Any],
    table: str,
    row: str,
    pin: str | int | None = None,
    title: str | None = None,
) -> list[tuple[Any, ...]]:
    """The elements a row of an index table (or a box of the power tree) shows
    again, as ``element_key()`` keys: every Kleidos addition or correction that
    names one of them is marked on that row too. ``table`` is one of nets,
    rails, tree (a row or box named after a net), gpio (``row`` the GPIO,
    ``pin`` its pin, ``title`` the table's), i2c, pulls, test_points, parts
    (``row`` the part's reference; in the parts list a part of one or two pins
    also shows each pin's net). Only values shown again count: a rail's row
    and box carry its nominal value, so a rail's entry is marked there, but a
    net's row shows only where it is drawn, so a net's entry is marked after
    its labels on the drawing and nowhere else."""
    if table in ("nets", "rails"):
        return [("rail", row)]
    if table == "tree":
        return [("part", row)] if row in (net.get("components") or {}) else [("rail", row)]
    if table == "gpio":
        chip = chip_of(title or "")
        return [("gpio", row, title)] + ([("pin", f"{chip}.{pin}")] if chip else [])
    if table == "i2c":
        return [("i2c", row), ("part", row)]
    if table == "pulls":
        return [("pull", row), ("part", row)]
    if table == "test_points":
        return [("part", row)]
    if table == "parts":
        pins = (net.get("components") or {}).get(row, {}).get("pins", {})
        return [("part", row)] + ([("pin", f"{row}.{p}") for p in pins] if len(pins) <= 2 else [])
    raise ValueError(table)


def additions_errors(net: dict[str, Any], lay: dict[str, Any]) -> list[str]:
    """What is wrong with netlist.yaml's ``kleidos`` list, the board's additions
    to and corrections of the vendor's print (``docs/models-and-drawings.md``,
    "Schematics"): each entry {id, kind, what, vendor (a correction's), element,
    source {type, cite}}. Ids run K1, K2... in order; the element is one of
    ``ADD_ELEMENTS`` and must name something the netlist has; the contents
    page's notes say ``ADD_WORDING`` when there is an entry, and only then;
    the subheading and the title block leave ``ADD_SUBTITLE`` to the generator,
    which adds it where there is an entry."""
    adds = net.get("kleidos") or []
    errors: list[str] = []
    if not isinstance(adds, list):
        return ["kleidos: a list of entries"]
    comps = net.get("components") or {}
    grounds = set(lay.get("grounds") or {})
    nets = {str(n) for c in comps.values() for n in c["pins"].values()} - {"NC"}
    nets_sheet: dict[str, Any] = next(
        (sh for sh in lay.get("sheets", []) if sh.get("index") == "nets"), {}
    )
    tables = gpio_maps(net, nets_sheet)
    seen: dict[tuple[Any, ...], str] = {}
    for i, e in enumerate(adds, start=1):
        if not isinstance(e, dict):
            errors.append(f"kleidos entry {i}: not a mapping")
            continue
        eid = str(e.get("id", ""))
        where = f"kleidos {eid or f'entry {i}'}"
        if eid != f"K{i}":
            errors.append(f"{where}: ids run K1, K2... in order; this one should be K{i}")
        if eid in comps or eid in nets:
            errors.append(f"{where}: the id is also a part or a net of the board")
        if e.get("kind") not in ADD_KINDS:
            errors.append(f"{where}: kind {e.get('kind')!r}, not one of {', '.join(ADD_KINDS)}")
        if not str(e.get("what") or "").strip():
            errors.append(f"{where}: no 'what' (what the drawing adds or corrects)")
        if e.get("kind") == "correction" and not str(e.get("vendor") or "").strip():
            errors.append(f"{where}: a correction says what the vendor's print shows ('vendor')")
        if e.get("kind") == "addition" and "vendor" in e:
            errors.append(
                f"{where}: 'vendor' is a correction's; an addition is what the print does not show"
            )
        src = e.get("source")
        if not isinstance(src, dict) or src.get("type") not in ADD_SOURCES:
            errors.append(f"{where}: source.type is one of {', '.join(ADD_SOURCES)}")
        if not isinstance(src, dict) or not str(src.get("cite") or "").strip():
            errors.append(
                f"{where}: source.cite is empty (document and page or table, firmware path and "
                "symbol, or bench record and date)"
            )
        given = e.get("element")
        el: dict[str, Any] = given if isinstance(given, dict) else {}
        kinds = [k for k in ADD_ELEMENTS if isinstance(el, dict) and k in el]
        if (
            len(kinds) != 1
            or set(el) - set(ADD_ELEMENTS) - {"table"}
            or ("table" in el and kinds != ["gpio"])
        ):
            errors.append(
                f"{where}: element is one of {{{', '.join(f'{k}: ...' for k in ADD_ELEMENTS)}}}"
                " (a gpio may add 'table')"
            )
            continue
        kind, val = kinds[0], str(el[kinds[0]])
        if kind == "pin":
            ref, _, pin = val.partition(".")
            if ref not in comps or pin not in {str(p) for p in comps[ref]["pins"]}:
                errors.append(f"{where}: pin {val} is not a pin of netlist.yaml (REF.PIN)")
        elif kind == "part" and val not in comps:
            errors.append(f"{where}: part {val} is not in netlist.yaml")
        elif kind == "net" and (val not in nets or val in grounds):
            errors.append(
                f"{where}: net {val} is not a net netlist.yaml has (grounds are marked by pin)"
            )
        elif kind == "gpio":
            holders = [t["title"] for t in tables if val in t["map"]]
            if el.get("table"):
                holders = [h for h in holders if h == el["table"]]
            if len(holders) != 1:
                errors.append(
                    f"{where}: gpio {val} is in {len(holders)} GPIO tables"
                    + ("; say which with 'table'" if len(holders) > 1 else "")
                )
            else:
                el = dict(el, table=holders[0])
        elif kind == "i2c" and val not in {
            str(d["ref"]) for d in (net.get("i2c") or {}).get("devices", [])
        }:
            errors.append(f"{where}: i2c {val} is not a device of netlist.yaml's i2c")
        elif kind == "pull" and val not in {str(p["via"]) for p in net.get("pulls") or []}:
            errors.append(f"{where}: pull {val} is not a resistor of netlist.yaml's pulls")
        elif kind == "rail" and (val not in (net.get("rails") or {}) or val in grounds):
            errors.append(f"{where}: rail {val} is not in netlist.yaml's rails")
        key = element_key(el)
        if key in seen:
            errors.append(f"{where}: marks the same {kind} as {seen[key]}")
        seen[key] = eid
    notes = " ".join(
        " ".join(str(p.get("text", "")).split()) for p in (lay.get("root") or {}).get("panels", [])
    )
    if adds and ADD_WORDING not in notes:
        errors.append(f'layout.yaml root panels: with additions, the notes say "{ADD_WORDING}"')
    if not adds and ADD_WORDING in notes:
        errors.append(
            f'layout.yaml root panels: the notes say "{ADD_WORDING}", but netlist.yaml has none'
        )
    tb = lay.get("title_block") or {}
    for where, said in [
        ("root subheading", (lay.get("root") or {}).get("subheading", "")),
        (
            "title_block",
            " ".join([str(tb.get("company", ""))] + list(map(str, tb.get("comments", [])))),
        ),
    ]:
        if ADD_SUBTITLE.lower() in str(said).lower():
            errors.append(
                f'layout.yaml {where}: "{ADD_SUBTITLE}" is the generator\'s to add, where a board '
                "has entries"
            )
    if adds and len(tb.get("comments", [])) >= BLOCK_LINES:
        errors.append(
            f"layout.yaml title_block: with additions the generator adds a comment line, and the "
            f"drawing sheet prints {BLOCK_LINES}"
        )
    return errors


# ---------------------------------------------------------------- s-expressions
class Sym(str):
    """A bare token (written without quotes)."""


OPEN, CLOSE = object(), object()


def tokenize(text: str) -> Iterator[object]:
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "()":
            yield OPEN if c == "(" else CLOSE
            i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while text[j] != '"':
                if text[j] == "\\":
                    buf.append(text[j + 1])
                    j += 2
                else:
                    buf.append(text[j])
                    j += 1
            yield str("".join(buf))
            i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in "()":
                j += 1
            yield Sym(text[i:j])
            i = j


def parse(text: str) -> list[Any]:
    stack: list[list[Any]] = [[]]
    for tok in tokenize(text):
        if tok is OPEN:
            stack.append([])
        elif tok is CLOSE:
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(tok)
    root: list[Any] = stack[0][0]
    return root


def fmt_num(v: float) -> str:
    v = round(v, 4)
    if abs(v) < 1e-9:
        v = 0.0
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s != "-0" else "0"


def dump(node: object, indent: int = 0) -> str:
    """Serialize a node in KiCad's style: a list holding only atoms on one line."""
    if isinstance(node, Sym):
        return str(node)
    if isinstance(node, str):
        return '"' + node.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(node, (int, float)):
        return fmt_num(node)
    if not isinstance(node, list):
        raise TypeError(f"not a KiCad node: {node!r}")
    head = [dump(x) for x in node if not isinstance(x, list)]
    kids = [x for x in node if isinstance(x, list)]
    if not kids:
        return "(" + " ".join(head) + ")"
    pad = "\t" * (indent + 1)
    out = "(" + " ".join(head)
    for k in kids:
        out += "\n" + pad + dump(k, indent + 1)
    return out + "\n" + "\t" * indent + ")"


def at(x: float, y: float, a: float | None = None) -> list[Any]:
    return [Sym("at"), x, y] + ([] if a is None else [a])


def font(size: float = FONT, bold: bool = False, color: Sequence[int] | None = None) -> list[Any]:
    f = [Sym("font"), [Sym("size"), size, size]]
    if bold:
        f.append([Sym("bold"), Sym("yes")])
    if color:
        f.append([Sym("color"), *color, 1])
    return f


def effects(
    size: float = FONT,
    justify: str | None = None,
    hide: bool = False,
    bold: bool = False,
    href: str | None = None,
    color: Sequence[int] | None = None,
) -> list[Any]:
    e = [Sym("effects"), font(size, bold, color)]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify.split()])
    if href:
        e.append([Sym("href"), href])
    if hide:
        e.append([Sym("hide"), Sym("yes")])
    return e


def stroke(width: float = 0.0, kind: str = "default") -> list[Any]:
    return [Sym("stroke"), [Sym("width"), width], [Sym("type"), Sym(kind)]]


# ------------------------------------------------------------------- geometry
def snap(v: float) -> float:
    return round(v / GRID) * GRID


def rot(px: float, py: float, a: int) -> tuple[float, float]:
    """A library offset (y up) on the sheet (y down) under a counter-clockwise turn a."""
    x, y = px, -py
    r = math.radians(a)
    c, s = round(math.cos(r)), round(math.sin(r))
    return (x * c + y * s, -x * s + y * c)


DIRS = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}  # sheet direction -> vector
LIB_DIRS = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}


def outward(pin_angle: int, sym_angle: int) -> int:
    """The sheet direction a pin points away from its body (0 right, 90 up, 180 left, 270 down)."""
    return (pin_angle + 180 + sym_angle) % 360


def text_w(s: str, size: float = FONT) -> float:
    s = re.sub(r"~\{([^}]*)\}", r"\1", s)
    return len(s) * CHAR_W * size / FONT


class Box:
    def __init__(self) -> None:
        self.x0 = self.y0 = math.inf
        self.x1 = self.y1 = -math.inf

    def add(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.x0, self.y0 = min(self.x0, x0, x1), min(self.y0, y0, y1)
        self.x1, self.y1 = max(self.x1, x0, x1), max(self.y1, y0, y1)

    @property
    def w(self) -> float:
        return self.x1 - self.x0

    @property
    def h(self) -> float:
        return self.y1 - self.y0

    @property
    def empty(self) -> bool:
        return self.x0 == math.inf


# --------------------------------------------------------------- symbol model
class LibSymbol:
    """A symbol's pins per unit (number -> (x, y, angle, name, length)), body and extent."""

    def __init__(self, lib_id: str, node: list[Any]) -> None:
        self.lib_id = lib_id
        self.node = node
        self.pins: dict[int, dict[str, tuple[Any, ...]]] = {}
        self.body = Box()  # graphics and the pins' inner ends
        self.extent = Box()  # the body and the pins' outer ends
        self._scan(node)

    def _scan(self, node: list[Any]) -> None:
        def child(g: list[Any], key: str) -> list[Any]:
            return next(x for x in g if isinstance(x, list) and x and x[0] == key)

        for kid in node:
            if not isinstance(kid, list) or not kid or kid[0] != "symbol":
                continue
            m = re.search(r"_(\d+)_(\d+)$", kid[1])
            unit = int(m.group(1)) if m else 0
            for g in kid[2:]:
                if not isinstance(g, list):
                    continue
                if g[0] == "pin":
                    a, num = child(g, "at"), child(g, "number")[1]
                    nm, ln = child(g, "name")[1], float(child(g, "length")[1])
                    x, y, ang = float(a[1]), float(a[2]), int(float(a[3]))
                    self.pins.setdefault(unit, {})[str(num)] = (x, y, ang, str(nm), ln)
                    dx, dy = LIB_DIRS[ang]
                    self.body.add(x + dx * ln, y + dy * ln, x + dx * ln, y + dy * ln)
                    self.extent.add(x, y, x, y)
                elif g[0] == "rectangle":
                    s, e = child(g, "start"), child(g, "end")
                    self.body.add(float(s[1]), float(s[2]), float(e[1]), float(e[2]))
                elif g[0] == "polyline":
                    for p in child(g, "pts")[1:]:
                        self.body.add(float(p[1]), float(p[2]), float(p[1]), float(p[2]))
                elif g[0] == "circle":
                    c, r = child(g, "center"), float(child(g, "radius")[1])
                    self.body.add(
                        float(c[1]) - r, float(c[2]) - r, float(c[1]) + r, float(c[2]) + r
                    )
        b = self.body
        if not b.empty:
            self.extent.add(b.x0, b.y0, b.x1, b.y1)

    def unit_pins(self, unit: int) -> dict[str, tuple[Any, ...]]:
        out = dict(self.pins.get(0, {}))
        out.update(self.pins.get(unit, {}))
        return out


# ---------------------------------------------------------- this project's library
#: The library of this project's own generic symbols: the passives, the
#: discrete semiconductors, the switches, the generic connectors, the test
#: point and the ground and flag symbols every board draws. Each is drawn here
#: (``generic_symbol``), and the generator writes them to ``kleidos.kicad_sym``
#: beside each board's own library; no file of KiCad's libraries is read or
#: copied. Their pins keep the places and numbers the boards' layouts were
#: drawn with, so a part lands where it did.
GENERIC_LIB = "kleidos"
THIN = 0.0  # a symbol line at KiCad's default width
THICK = 0.254


def _g_line(*pts: tuple[float, float], width: float = THIN, fill: str = "none") -> list[Any]:
    return [
        Sym("polyline"),
        [Sym("pts")] + [[Sym("xy"), x, y] for x, y in pts],
        stroke(width),
        [Sym("fill"), [Sym("type"), Sym(fill)]],
    ]


def _g_rect(
    x0: float, y0: float, x1: float, y1: float, width: float = THICK, fill: str = "background"
) -> list[Any]:
    return [
        Sym("rectangle"),
        [Sym("start"), x0, y0],
        [Sym("end"), x1, y1],
        stroke(width),
        [Sym("fill"), [Sym("type"), Sym(fill)]],
    ]


def _g_circle(cx: float, cy: float, r: float, width: float = THIN, fill: str = "none") -> list[Any]:
    return [
        Sym("circle"),
        [Sym("center"), cx, cy],
        [Sym("radius"), r],
        stroke(width),
        [Sym("fill"), [Sym("type"), Sym(fill)]],
    ]


def _g_pin(
    num: str,
    name: str,
    x: float,
    y: float,
    ang: float,
    length: float,
    etype: str = "passive",
    hide: bool = False,
) -> list[Any]:
    node = [Sym("pin"), Sym(etype), Sym("line"), at(x, y, ang), [Sym("length"), length]]
    if hide:
        node.append([Sym("hide"), Sym("yes")])
    return node + [[Sym("name"), name, effects()], [Sym("number"), num, effects()]]


def _g_arrow(x0: float, y0: float, x1: float, y1: float, head: float = 0.5) -> list[Any]:
    """A line from (x0, y0) to (x1, y1) with an open head at its end."""
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    px, py = -uy, ux
    bx, by = x1 - ux * head, y1 - uy * head
    return [
        _g_line((x0, y0), (x1, y1)),
        _g_line(
            (bx + px * head / 2, by + py * head / 2),
            (x1, y1),
            (bx - px * head / 2, by - py * head / 2),
        ),
    ]


def _g_diode(kind: str) -> list[Any]:
    """A diode along x, cathode at x -1.27 (its pin K left), anode at 1.27."""
    out = [
        _g_line((-1.27, 0), (1.27, 0)),
        _g_line((1.27, 1.27), (1.27, -1.27), (-1.27, 0), (1.27, 1.27), width=THICK),
    ]
    if kind == "schottky":
        out.append(
            _g_line(
                (-1.9, 0.76),
                (-1.9, 1.27),
                (-1.27, 1.27),
                (-1.27, -1.27),
                (-0.64, -1.27),
                (-0.64, -0.76),
                width=THICK,
            )
        )
    elif kind == "zener":
        out.append(
            _g_line((-1.9, 1.27), (-1.27, 1.27), (-1.27, -1.27), (-0.64, -1.27), width=THICK)
        )
    else:
        out.append(_g_line((-1.27, 1.27), (-1.27, -1.27), width=THICK))
    return out


def _g_fet(p_channel: bool) -> list[Any]:
    out = [
        _g_circle(0.635, 0, 2.794, THICK),
        _g_line((-2.54, 0), (-1.016, 0)),
        _g_line((-1.016, 1.524), (-1.016, -1.524), width=THICK),
    ]
    for y0, y1 in ((1.016, 1.778), (-0.381, 0.381), (-1.778, -1.016)):
        out.append(_g_line((-0.381, y0), (-0.381, y1), width=THICK))
    out += [
        _g_line((-0.381, 1.397), (2.54, 1.397), (2.54, 2.54)),
        _g_line((-0.381, -1.397), (2.54, -1.397), (2.54, -2.54)),
        _g_line((2.54, -1.397), (2.54, 0), (-0.381, 0)),
    ]
    tip, back = (0.889, -0.127) if p_channel else (-0.127, 0.889)
    out.append(_g_line((tip, 0), (back, 0.508), (back, -0.508), (tip, 0), fill="outline"))
    return out


def _conn_rows(n: int) -> float:
    return math.floor((n - 1) / 2) * PITCH


def generic_symbol(name: str) -> list[Any]:
    """This project's drawing of a generic symbol, by name (``kleidos:<name>``)."""
    hide_both: list[Any] = [
        [Sym("pin_numbers"), [Sym("hide"), Sym("yes")]],
        [Sym("pin_names"), [Sym("offset"), 0], [Sym("hide"), Sym("yes")]],
    ]
    hide_names: list[Any] = [[Sym("pin_names"), [Sym("offset"), 1.016], [Sym("hide"), Sym("yes")]]]
    show_names: list[Any] = [[Sym("pin_names"), [Sym("offset"), 1.016]]]

    def two_v(length: float = 1.27, half: float = 3.81) -> list[Any]:
        return [
            _g_pin("1", "~", 0, half, 270, length),
            _g_pin("2", "~", 0, -half, 90, length),
        ]

    diode_pins = [_g_pin("1", "K", -3.81, 0, 0, 2.54), _g_pin("2", "A", 3.81, 0, 180, 2.54)]
    ref, flags, gfx, pins, power = "U", hide_both, [], [], None
    m = re.fullmatch(r"Conn_(\d\d)x(\d\d)(?:_(Odd_Even|Counter_Clockwise))?", name)
    if name in ("GND", "GNDA", "GNDREF"):
        ref, power = "#PWR", "global"
        gfx = [_g_line((0, 0), (0, -1.27)), _g_line((-1.27, -1.27), (1.27, -1.27), width=THICK)]
        if name == "GND":
            gfx += [
                _g_line((-0.762, -1.905), (0.762, -1.905), width=THICK),
                _g_line((-0.254, -2.54), (0.254, -2.54), width=THICK),
            ]
        elif name == "GNDA":
            gfx += [_g_line((-1.27, -1.27), (0, -2.54), (1.27, -1.27))]
        else:
            gfx += [_g_line((x, -1.27), (x - 0.635, -2.286)) for x in (-0.635, 0.254, 1.143)]
        pins = [_g_pin("1", name, 0, 0, 270, 0, "power_in", hide=True)]
    elif name == "PWR_FLAG":
        ref, power = "#FLG", "global"
        gfx = [_g_line((0, 0), (0, 2.54)), _g_line((0, 2.54), (1.016, 2.032), (0, 1.524))]
        pins = [_g_pin("1", "~", 0, 0, 90, 0, "power_out")]
    elif name == "R":
        ref, gfx, pins = "R", [_g_rect(-0.889, -2.54, 0.889, 2.54, fill="none")], two_v()
    elif name in ("C", "C_Polarized"):
        ref, pins = "C", two_v(3.175)
        gfx = [_g_line((-2.032, 0.635), (2.032, 0.635), width=0.381)]
        if name == "C":
            gfx.append(_g_line((-2.032, -0.635), (2.032, -0.635), width=0.381))
        else:
            gfx += [
                _g_line(
                    (-2.286, -1.016),
                    (-1.143, -0.762),
                    (0, -0.635),
                    (1.143, -0.762),
                    (2.286, -1.016),
                    width=0.381,
                ),
                _g_line((-1.651, 1.524), (-1.651, 2.54)),
                _g_line((-2.159, 2.032), (-1.143, 2.032)),
            ]
    elif name == "L":
        ref, pins = "L", two_v()
        pts = []
        for k in range(4):
            y0 = 2.54 - k * 1.27
            pts += [(0.635 * math.sin(math.pi * t / 6), y0 - 1.27 * t / 6) for t in range(7)]
        gfx = [_g_line(*pts)]
    elif name == "FerriteBead_Small":
        ref, pins = "FB", two_v(1.27, 2.54)
        gfx = [
            _g_line(
                (-1.524, 0.254),
                (0.254, -1.524),
                (1.524, -0.254),
                (-0.254, 1.524),
                (-1.524, 0.254),
                width=THICK,
            ),
            _g_line((0, 1.27), (0, 0.889)),
            _g_line((0, -1.27), (0, -0.889)),
        ]
    elif name in ("Fuse", "Polyfuse"):
        ref, pins = "F", two_v()
        gfx = [_g_rect(-0.762, -2.54, 0.762, 2.54, fill="none"), _g_line((0, -2.54), (0, 2.54))]
        if name == "Polyfuse":
            gfx = [gfx[0], _g_line((-1.524, -2.54), (-1.524, -1.778), (1.524, 1.778))]
    elif name in ("D", "D_Schottky", "D_Zener"):
        ref, pins = "D", diode_pins
        gfx = _g_diode({"D": "plain", "D_Schottky": "schottky", "D_Zener": "zener"}[name])
    elif name == "LED":
        ref, pins = "D", diode_pins
        gfx = (
            _g_diode("plain")
            + _g_arrow(-0.508, 1.651, -1.778, 2.921)
            + _g_arrow(0.762, 1.651, -0.508, 2.921)
        )
    elif name == "D_TVS":
        ref = "D"
        pins = [_g_pin("1", "A1", -3.81, 0, 0, 2.54), _g_pin("2", "A2", 3.81, 0, 180, 2.54)]
        gfx = [
            _g_line((-1.27, 0), (1.27, 0)),
            _g_line((-1.27, 1.016), (-1.27, -1.016), (0, 0), (-1.27, 1.016), width=THICK),
            _g_line((1.27, 1.016), (1.27, -1.016), (0, 0), (1.27, 1.016), width=THICK),
            _g_line((-0.508, 1.27), (0, 1.016), (0, -1.016), (0.508, -1.27), width=THICK),
        ]
    elif name == "D_Photo":
        ref = "D"
        pins = [_g_pin("1", "K", -5.08, 0, 0, 2.54), _g_pin("2", "A", 2.54, 0, 180, 2.54)]
        gfx = [
            _g_line((-2.54, 0), (0, 0)),
            _g_line((0, 1.27), (0, -1.27), (-2.54, 0), (0, 1.27), width=THICK),
            _g_line((-2.54, 1.27), (-2.54, -1.27), width=THICK),
        ]
        gfx += _g_arrow(1.016, 3.048, -0.508, 1.524) + _g_arrow(0, 3.302, -1.524, 1.778)
    elif name in ("Q_NMOS", "Q_PMOS"):
        ref, flags = "Q", hide_names
        pins = [
            _g_pin("D", "D", 2.54, 5.08, 270, 2.54),
            _g_pin("G", "G", -5.08, 0, 0, 2.54, "input"),
            _g_pin("S", "S", 2.54, -5.08, 90, 2.54),
        ]
        gfx = _g_fet(name == "Q_PMOS")
    elif name == "Q_NPN":
        ref, flags = "Q", hide_names
        pins = [
            _g_pin("B", "B", -5.08, 0, 0, 2.54, "input"),
            _g_pin("C", "C", 2.54, 5.08, 270, 2.54),
            _g_pin("E", "E", 2.54, -5.08, 90, 2.54),
        ]
        gfx = [
            _g_circle(0.635, 0, 2.794, THICK),
            _g_line((-2.54, 0), (-0.635, 0)),
            _g_line((-0.635, 1.524), (-0.635, -1.524), width=THICK),
            _g_line((-0.635, 0.635), (2.54, 2.54)),
            _g_line((-0.635, -0.635), (2.54, -2.54)),
        ]
        gfx += _g_arrow(-0.635, -0.635, 1.651, -2.0, 0.7)
    elif name in ("Crystal", "Crystal_GND24"):
        ref = "Y"
        flags = [[Sym("pin_names"), [Sym("offset"), 1.016], [Sym("hide"), Sym("yes")]]]
        pins = [
            _g_pin("1", "1", -3.81, 0, 0, 1.27),
            _g_pin(
                "3" if name.endswith("24") else "2",
                "3" if name.endswith("24") else "2",
                3.81,
                0,
                180,
                1.27,
            ),
        ]
        gfx = [
            _g_rect(-0.762, -1.397, 0.762, 1.397, fill="none"),
            _g_line((-1.397, 1.905), (-1.397, -1.905), width=THICK),
            _g_line((1.397, 1.905), (1.397, -1.905), width=THICK),
            _g_line((-2.54, 0), (-1.397, 0)),
            _g_line((1.397, 0), (2.54, 0)),
        ]
        if name == "Crystal_GND24":
            pins += [
                _g_pin("2", "G", 0, -5.08, 90, 1.27),
                _g_pin("4", "G", 0, -5.08, 90, 1.27, hide=True),
            ]
            gfx += [_g_line((0, -3.81), (0, -2.794)), _g_line((-2.032, -2.794), (2.032, -2.794))]
    elif name == "Battery_Cell":
        ref = "BT"
        pins = [_g_pin("1", "+", 0, 5.08, 270, 2.54), _g_pin("2", "-", 0, -2.54, 90, 2.54)]
        gfx = [
            _g_line((0, 2.54), (0, 1.778)),
            _g_line((-2.032, 1.778), (2.032, 1.778), width=THICK),
            _g_line((-1.016, 0.762), (1.016, 0.762), width=0.508),
            _g_line((0, 0.762), (0, 0)),
            _g_line((1.27, 3.302), (2.286, 3.302)),
            _g_line((1.778, 2.794), (1.778, 3.81)),
        ]
    elif name in ("Antenna", "Antenna_Shield"):
        ref, flags = "AE", hide_names
        pins = [_g_pin("1", "A", 0, -5.08, 90, 2.54, "input")]
        gfx = [
            _g_line((0, -2.54), (0, 2.54)),
            _g_line((-1.27, 2.54), (0, 0.508), (1.27, 2.54), (-1.27, 2.54)),
        ]
        if name == "Antenna_Shield":
            pins.append(_g_pin("2", "Shield", 2.54, -5.08, 90, 2.54, "input"))
            gfx.append(_g_line((2.54, -2.54), (2.54, -0.762), (0.762, -0.762)))
    elif name == "SW_Push":
        ref, flags = "SW", hide_names
        pins = [_g_pin("1", "1", -5.08, 0, 0, 2.54), _g_pin("2", "2", 5.08, 0, 180, 2.54)]
        gfx = [
            _g_circle(-2.032, 0, 0.508),
            _g_circle(2.032, 0, 0.508),
            _g_line((-2.286, 1.27), (2.286, 1.27), width=THICK),
            _g_line((0, 1.27), (0, 2.794)),
            _g_line((-0.762, 2.794), (0.762, 2.794)),
        ]
    elif name == "SW_SPDT":
        ref, flags = "SW", hide_names
        pins = [
            _g_pin("1", "A", 5.08, 2.54, 180, 2.54),
            _g_pin("2", "B", -5.08, 0, 0, 2.54),
            _g_pin("3", "C", 5.08, -2.54, 180, 2.54),
        ]
        gfx = [
            _g_circle(-2.032, 0, 0.508),
            _g_circle(2.032, 2.54, 0.508),
            _g_circle(2.032, -2.54, 0.508),
            _g_line((-1.651, 0.254), (1.778, 1.905), width=THICK),
        ]
    elif name == "TestPoint":
        ref, flags = "TP", hide_names
        pins = [_g_pin("1", "1", 0, 0, 90, 2.54)]
        gfx = [_g_circle(0, 3.302, 0.762, THICK)]
    elif name == "MountingHole_Pad":
        ref, flags = "H", hide_names
        pins = [_g_pin("1", "1", 0, -2.54, 90, 2.54, "input")]
        gfx = [_g_circle(0, 1.27, 1.27, THICK), _g_circle(0, 1.27, 0.508)]
    elif m:
        cols, rows = int(m.group(1)), int(m.group(2))
        ref, flags = "J", hide_names
        top = _conn_rows(rows)
        right = 1.27 if cols == 1 else 3.81
        gfx = [_g_rect(-1.27, top + 1.27, right, top - (rows - 1) * PITCH - 1.27)]
        for i in range(rows):
            y = top - i * PITCH
            if cols == 1:
                num = i + 1
                pins.append(_g_pin(str(num), f"Pin_{num}", -5.08, y, 0, 3.81))
                continue
            if m.group(3) == "Odd_Even":
                a, b = 2 * i + 1, 2 * i + 2
            else:  # counter-clockwise: 1..n down the left, then up the right
                a, b = i + 1, 2 * rows - i
            pins += [
                _g_pin(str(a), f"Pin_{a}", -5.08, y, 0, 3.81),
                _g_pin(str(b), f"Pin_{b}", 7.62, y, 180, 3.81),
            ]
        for p in pins:  # a small mark where each pin meets the body
            x, y = float(p[3][1]), float(p[3][2])
            ex = -1.27 if x < 0 else right
            gfx.append(_g_line((ex, y), (ex + (0.508 if x < 0 else -0.508), y), width=THICK))
    elif name == "USB_C_Receptacle_USB2.0_16P":
        ref, flags = "J", show_names
        gfx = [
            _g_rect(-10.16, 17.78, 10.16, -17.78),
            _g_rect(-7.62, 6.35, -3.81, -6.35, width=THICK, fill="none"),
            [Sym("text"), "USB-C", at(-5.715, 8.89, 0), effects(1.016)],
        ]
        spec = [
            ("A1", "GND", 0, -22.86, 90, False),
            ("A12", "GND", 0, -22.86, 90, True),
            ("B1", "GND", 0, -22.86, 90, True),
            ("B12", "GND", 0, -22.86, 90, True),
            ("A4", "VBUS", 15.24, 15.24, 180, False),
            ("A9", "VBUS", 15.24, 15.24, 180, True),
            ("B4", "VBUS", 15.24, 15.24, 180, True),
            ("B9", "VBUS", 15.24, 15.24, 180, True),
            ("A5", "CC1", 15.24, 10.16, 180, False),
            ("B5", "CC2", 15.24, 7.62, 180, False),
            ("A7", "D-", 15.24, 2.54, 180, False),
            ("B7", "D-", 15.24, 0, 180, False),
            ("A6", "D+", 15.24, -2.54, 180, False),
            ("B6", "D+", 15.24, -5.08, 180, False),
            ("A8", "SBU1", 15.24, -12.7, 180, False),
            ("B8", "SBU2", 15.24, -15.24, 180, False),
            ("SH", "SHIELD", -7.62, -22.86, 90, False),
        ]
        for pnum, nm, x, y, a, hid in spec:
            etype = (
                "bidirectional" if nm in ("CC1", "CC2", "D-", "D+", "SBU1", "SBU2") else "passive"
            )
            pins.append(_g_pin(pnum, nm, x, y, a, 5.08, etype, hid))
    else:
        raise SystemExit(f"{GENERIC_LIB}:{name}: no such symbol in this project's library")
    node: list[Any] = [Sym("symbol"), name]
    if power:
        node.append([Sym("power"), Sym(power)])
    node += flags + [
        [Sym("exclude_from_sim"), Sym("no")],
        [Sym("in_bom"), Sym("no" if power else "yes")],
        [Sym("on_board"), Sym("no" if power else "yes")],
        [Sym("property"), "Reference", ref, at(0, 5.08, 0), effects(hide=bool(power))],
        [Sym("property"), "Value", name, at(0, -5.08, 0), effects()],
        [Sym("property"), "Footprint", "", at(0, 0, 0), effects(hide=True)],
        [Sym("property"), "Datasheet", "", at(0, 0, 0), effects(hide=True)],
        [
            Sym("property"),
            "Description",
            f"Kleidos boards: {name}",
            at(0, 0, 0),
            effects(hide=True),
        ],
        [Sym("symbol"), f"{name}_0_1"] + gfx,
        [Sym("symbol"), f"{name}_1_1"] + pins,
        [Sym("embedded_fonts"), Sym("no")],
    ]
    return node


def split_pin(p: str) -> tuple[str, str] | None:
    if p == "-":
        return None
    num, _, nm = str(p).partition(" ")
    nm = nm or num
    return num, ("~" if nm == num else nm)


def own_symbol(name: str, spec: dict[str, Any]) -> list[Any]:
    """Our symbol: a box with pins left, right and along the bottom, or a MOSFET pair.

    Optional: ``pin_length`` (default ``PIN_LEN``), longer where the vendor's pin
    numbers are wide (``VBUS``, ``SHELL``); ``hide_pin_numbers``, for a part the
    vendor draws with pin names only, or only some pins numbered (the names then
    carry the numbers)."""
    if spec.get("kind") == "mosfet_pair":
        return mosfet_pair(name, spec)
    L = [split_pin(p) for p in spec.get("left", [])]
    R = [split_pin(p) for p in spec.get("right", [])]
    B = [split_pin(p) for p in spec.get("bottom", [])]
    rows = max(len(L), len(R), 1)
    plen = float(spec.get("pin_length", PIN_LEN))
    lw = max([text_w(p[1]) for p in L if p and p[1] != "~"] + [0])
    rw = max([text_w(p[1]) for p in R if p and p[1] != "~"] + [0])
    bw = (len(B) + 1) * PITCH
    half = max(
        math.ceil((lw + rw + 5.0) / 2 / PITCH) * PITCH, math.ceil(bw / 2 / PITCH) * PITCH, 5.08
    )
    top = math.floor((rows - 1) / 2) * PITCH
    pins = []
    types = spec.get("types", {})
    for i, p in enumerate(L):
        if p:
            pins.append(
                pin_node(p[0], p[1], -half - plen, top - i * PITCH, 0, types.get(p[0]), length=plen)
            )
    for i, p in enumerate(R):
        if p:
            pins.append(
                pin_node(
                    p[0], p[1], half + plen, top - i * PITCH, 180, types.get(p[0]), length=plen
                )
            )
    y_top = top + PITCH
    y_bot = top - (rows - 1) * PITCH - PITCH
    if B:  # room for the bottom pins' names, which read upwards
        names = max([text_w(p[1]) for p in B if p and p[1] != "~"] + [0])
        y_bot -= math.ceil((names + 1.5) / PITCH) * PITCH
        x0 = -(len(B) - 1) * PITCH / 2
        x0 = math.floor(x0 / PITCH) * PITCH
        for i, p in enumerate(B):
            if p:
                pins.append(
                    pin_node(
                        p[0],
                        p[1],
                        x0 + i * PITCH,
                        y_bot - plen,
                        90,
                        types.get(p[0]),
                        bottom=True,
                        length=plen,
                    )
                )
    body = [
        Sym("rectangle"),
        [Sym("start"), -half, y_top],
        [Sym("end"), half, y_bot],
        stroke(0.254),
        [Sym("fill"), [Sym("type"), Sym("background")]],
    ]
    node = sym_header(
        name,
        spec.get("ref", "U"),
        spec.get("value", name),
        y_top + 1.27,
        y_bot - 1.27,
        spec.get("description", ""),
    )
    if spec.get("hide_pin_numbers"):
        node.insert(2, [Sym("pin_numbers"), [Sym("hide"), Sym("yes")]])
    node.append([Sym("symbol"), f"{name}_0_1", body])
    node.append([Sym("symbol"), f"{name}_1_1"] + pins)
    node.append([Sym("embedded_fonts"), Sym("no")])
    return node


def mosfet_pair(name: str, spec: dict[str, Any]) -> list[Any]:
    """Two MOSFETs in one package, one per unit: gate left, drain and source
    right. A unit given as ``{type, b, c, e}`` is a transistor instead: base
    left, collector and emitter right, with the vendor's pin numbers."""
    node = sym_header(
        name,
        spec.get("ref", "Q"),
        spec.get("value", name),
        5.08,
        -5.08,
        spec.get("description", ""),
    )
    for u, unit in enumerate(spec["units"], start=1):
        bjt = "b" in unit
        gfx = [
            [
                Sym("rectangle"),
                [Sym("start"), -3.81, 5.08],
                [Sym("end"), 3.81, -5.08],
                stroke(0.254),
                [Sym("fill"), [Sym("type"), Sym("background")]],
            ],
            [
                Sym("text"),
                unit["type"] if bjt else f"{unit['type']}-ch",
                at(0, -3.9, 0),
                effects(1.0),
            ],
        ]
        g, d, s_ = ("b", "c", "e") if bjt else ("g", "d", "s")
        pins = [
            pin_node(unit[g], g.upper(), -6.35, 0, 0, None),
            pin_node(unit[d], d.upper(), 6.35, 2.54, 180, None),
            pin_node(unit[s_], s_.upper(), 6.35, -1.27, 180, None),
        ]
        node.append([Sym("symbol"), f"{name}_{u}_1"] + gfx + pins)
    node.append([Sym("embedded_fonts"), Sym("no")])
    return node


def sym_header(name: str, ref: str, value: str, y_ref: float, y_val: float, desc: str) -> list[Any]:
    return [
        Sym("symbol"),
        name,
        [Sym("pin_names"), [Sym("offset"), 0.762]],
        [Sym("exclude_from_sim"), Sym("no")],
        [Sym("in_bom"), Sym("yes")],
        [Sym("on_board"), Sym("yes")],
        [Sym("property"), "Reference", ref, at(0, y_ref, 0), effects()],
        [Sym("property"), "Value", value, at(0, y_val, 0), effects()],
        [Sym("property"), "Footprint", "", at(0, 0, 0), effects(hide=True)],
        [Sym("property"), "Datasheet", "", at(0, 0, 0), effects(hide=True)],
        [Sym("property"), "Description", desc, at(0, 0, 0), effects(hide=True)],
    ]


def pin_node(
    num: str,
    name: str,
    x: float,
    y: float,
    ang: float,
    etype: str | None,
    bottom: bool = False,
    length: float = PIN_LEN,
) -> list[Any]:
    return [
        Sym("pin"),
        Sym(etype or "passive"),
        Sym("line"),
        at(x, y, ang),
        [Sym("length"), length],
        [Sym("name"), name, effects()],
        [Sym("number"), num, effects()],
    ]


def renamed(node: list[Any], full: str) -> list[Any]:
    out = list(node)
    out[1] = full
    return out


# ------------------------------------------------------------------ the board
class Builder:
    def __init__(self, board: str) -> None:
        self.board = board
        self.dir = ROOT / board / "schematic"
        self.net = yaml.safe_load((self.dir / "netlist.yaml").read_text(encoding="utf-8"))
        self.lay = yaml.safe_load((self.dir / "layout.yaml").read_text(encoding="utf-8"))
        self.comps = self.net["components"]
        self.lib: dict[str, LibSymbol] = {}
        self.own: dict[str, list[Any]] = {}
        self.generic: dict[str, list[Any]] = {}
        self.project = board
        self.root_uuid = self.uid("root")
        self.grounds = dict(self.lay.get("grounds", {}))
        self.pwr_n = 0
        self.cur_path = ""
        self.paper = self.lay.get("paper", "A3")
        # Recorded while the sheets are drawn, read once every item has its
        # final place (shift() moves the "at" lists these hold in place):
        self.labels: list[
            dict[str, Any]
        ] = []  # every net label: net, page, the part it hangs from, its "at"
        self.tokens: list[
            dict[str, Any]
        ] = []  # every "[page/zone]" after a label: its text node, net, pages
        self.fields: list[
            dict[str, Any]
        ] = []  # every placed symbol's Reference field: ref, unit, page, "at", width
        self.jumps: list[
            dict[str, Any]
        ] = []  # every linked text that leads to a place: page, anchor, target
        self.marks: dict[str, dict[str, Any]] = {}  # named destinations
        self.sections: dict[int, list[Any]] = {}  # an index page's bookmarks: its tables' headings
        # the Kleidos additions and corrections, by what they mark, and every
        # marker drawn ("K3" beside its element), linked once page 1 is laid out
        errors = additions_errors(self.net, self.lay)
        if errors:
            raise SystemExit("netlist.yaml kleidos:\n  " + "\n  ".join(errors))
        self.adds: list[dict[str, Any]] = self.net.get("kleidos") or []
        self.add_at = additions_by_element(self.net, self.lay)
        self.markers: list[dict[str, Any]] = []

    def uid(self, *key: object) -> str:
        return str(
            uuidlib.uuid5(
                uuidlib.NAMESPACE_URL, f"kleidos-boards/{self.board}/" + "/".join(map(str, key))
            )
        )

    # --- symbols
    def symbol(self, lib_id: str) -> LibSymbol:
        if lib_id not in self.lib:
            lib, name = lib_id.split(":", 1)
            if lib == self.board:
                node = own_symbol(name, self.lay["symbols"][name])
                self.own[name] = node
            elif lib == GENERIC_LIB:
                node = generic_symbol(name)
                self.generic[name] = node
            else:
                raise SystemExit(
                    f"{lib_id}: a part takes one of this project's symbols, "
                    f"{self.board}:<name> or {GENERIC_LIB}:<name>"
                )
            self.lib[lib_id] = LibSymbol(lib_id, node)
        return self.lib[lib_id]

    def part(self, ref: str) -> dict[str, Any]:
        """The symbol a component takes, its angle, stub and pin map (ours -> the vendor's)."""
        parts = self.lay["parts"]
        spec = parts.get(ref)
        if spec is None:
            found = re.match(r"^[A-Z]+", ref)
            if found is None:
                raise SystemExit(f"{ref}: a reference starts with its letters")
            prefix = found.group(0)
            spec = parts["_by_prefix"].get(prefix)
            if spec is None:
                raise SystemExit(f"{ref}: no symbol for it in layout.yaml parts")
        return {"symbol": spec} if isinstance(spec, str) else spec

    # --- the whole project
    def build(self) -> dict[str, list[Any]]:
        where = {}
        for sh in self.lay["sheets"]:
            for blk in sh.get("blocks", []):
                for row in blk["rows"]:
                    for it in row:
                        for ref in item_refs(it):
                            where[ref.split(":")[0]] = sh["file"]
        missing = sorted(set(self.comps) - set(where))
        if missing:
            raise SystemExit(f"components placed nowhere: {', '.join(missing)}")
        wide = title_block_errors(self.lay, bool(self.adds))
        if wide:
            raise SystemExit(
                "layout.yaml title_block: a line wider than its cell, which KiCad would "
                "condense:\n  " + "\n  ".join(wide)
            )
        sheets_of: dict[str, set[Any]] = {}
        for ref, c in self.comps.items():
            for net in c["pins"].values():
                sheets_of.setdefault(net, set()).add(where[ref])
        self.page_of = {sh["file"]: page for page, sh in enumerate(self.lay["sheets"], start=2)}
        self.net_pages = {n: sorted(self.page_of[f] for f in sh) for n, sh in sheets_of.items()}
        self.pages = len(self.lay["sheets"]) + 1
        self.names = {1: self.lay["root"]["title"]}
        self.names.update({p: sh["name"] for p, sh in enumerate(self.lay["sheets"], start=2)})
        self.index_page = {
            sh["index"]: p for p, sh in enumerate(self.lay["sheets"], start=2) if "index" in sh
        }
        files = {}
        for page, sh in enumerate(self.lay["sheets"], start=2):  # the drawing first,
            if "index" not in sh:
                files[sh["file"]] = self.child_sheet(sh, page)
        self.resolve()  # then where every net lands,
        self.part_rows: dict[str, dict[str, Any]] = {}
        for page, sh in enumerate(self.lay["sheets"], start=2):  # then the pages that index it,
            if "index" in sh and sh["index"] != "additions":
                files[sh["file"]] = self.index_sheet(sh, page)
        self.adds_rest: list[Any] = []  # the rows of the additions table page 1 has no room for
        files[f"{self.board}.kicad_sch"] = self.root_sheet()  # then the contents,
        for page, sh in enumerate(self.lay["sheets"], start=2):  # and the contents' continuation
            if sh.get("index") == "additions":
                files[sh["file"]] = self.index_sheet(sh, page)
        files[f"{self.board}.kicad_sym"] = [
            Sym("kicad_symbol_lib"),
            [Sym("version"), 20251024],
            [Sym("generator"), "kleidos_boards"],
            [Sym("generator_version"), "1.0"],
        ] + [self.own[k] for k in sorted(self.own)]
        files[f"{GENERIC_LIB}.kicad_sym"] = [
            Sym("kicad_symbol_lib"),
            [Sym("version"), 20251024],
            [Sym("generator"), "kleidos_boards"],
            [Sym("generator_version"), "1.0"],
        ] + [self.generic[k] for k in sorted(self.generic)]
        files = {
            k: files[k]
            for k in [f"{self.board}.kicad_sch"]
            + [sh["file"] for sh in self.lay["sheets"]]
            + [f"{self.board}.kicad_sym", f"{GENERIC_LIB}.kicad_sym"]
        }
        return files

    # --- where things land, for the PDF's links
    @staticmethod
    def spot(page: int, node_at: list[Any]) -> dict[str, Any]:
        return {"page": page, "x": round(float(node_at[1]), 4), "y": round(float(node_at[2]), 4)}

    def zone_of(self, s: dict[str, Any]) -> str:
        return zone(s["x"], s["y"], self.paper)

    def where(self, s: dict[str, Any]) -> str:
        """A place as a cross-reference prints it: page/zone."""
        return f"{s['page']}/{self.zone_of(s)}"

    def target_label(self, net: str, page: int) -> dict[str, Any]:
        """The label a link to ``net`` on ``page`` lands on: the one at the part
        that feeds the rail (``rails.from``), else the first in reading order."""
        cands = [lab for lab in self.labels if lab["net"] == net and lab["page"] == page]
        if not cands:
            raise SystemExit(f"{net}: no label on page {page}")
        rail = (self.net.get("rails") or {}).get(net)
        feeders = part_references(str(rail.get("from", ""))) if rail else set()
        pool = [lab for lab in cands if lab["ref"] in feeders] or cands
        return min(pool, key=lambda lab: (float(lab["at"][2]), float(lab["at"][1])))

    def net_spot(self, net: str, page: int) -> dict[str, Any]:
        return self.spot(page, self.target_label(net, page)["at"])

    def field_spot(self, ref: str, unit: int | None = None) -> dict[str, Any]:
        f = min(
            (f for f in self.fields if f["ref"] == ref and unit in (None, f["unit"])),
            key=lambda f: f["unit"],
        )
        return self.spot(f["page"], f["at"])

    def resolve(self) -> None:
        """Give every "[page/??]" its zone, and record where each leads."""
        for t in self.tokens:
            dest = self.net_spot(t["net"], t["to"])
            t["node"][1] = f"[{self.where(dest)}]"
            self.jumps.append(
                {
                    "page": t["page"],
                    "at": t["node"][3],
                    "to": dest,
                    "alt": f"{t['net']} on page {self.where(dest)}",
                }
            )
        for net, pages in sorted(self.net_pages.items()):
            for p in pages:
                if net != "NC" and net not in self.grounds:
                    self.marks[f"net-{net}-p{p}"] = self.net_spot(net, p)
        for ref in sorted(self.comps, key=natural):
            self.marks[f"part-{ref}"] = self.field_spot(ref)

    def link_map(self) -> dict[str, Any]:
        """What the PDF step does to KiCad's PDF (schematic_pdf.py): the links
        it sends to a place instead of a whole page, the links it adds on each
        part's reference, the named destinations and the bookmarks."""
        W, H = PAPER[self.paper]
        parts = self.index_page.get("parts")
        added = []
        for f in self.fields:
            x, y = float(f["at"][1]), float(f["at"][2])
            x0 = x if f["justify"] == "left" else x - f["w"] / 2
            row = self.part_rows.get(f["ref"])
            if parts and row:
                added.append(
                    {
                        "page": f["page"],
                        "rect": [
                            round(x0 - 0.3, 3),
                            round(y - 0.95, 3),
                            round(x0 + f["w"] + 0.3, 3),
                            round(y + 0.95, 3),
                        ],
                        "to": row,
                        "alt": f"{f['ref']} in the parts list, page {parts}",
                    }
                )
        jumps = [
            {
                "page": j["page"],
                "at": [round(float(j["at"][1]), 4), round(float(j["at"][2]), 4)],
                "to": j["to"],
                "alt": j["alt"],
            }
            for j in self.jumps
        ]
        outline = []
        for page in range(1, self.pages + 1):
            kids = []
            refs = sorted({f["ref"] for f in self.fields if f["page"] == page}, key=natural)
            kids += [
                {"title": f"{r} {self.comps[r]['value']}", "to": self.field_spot(r)} for r in refs
            ]
            kids += self.sections.get(page, [])
            outline.append(
                {"title": f"{self.names[page]} (Page {page})", "page": page, "kids": kids}
            )
        return {
            "paper": [W, H],
            "view": {"left": VIEW_LEFT, "top": VIEW_TOP, "zoom": VIEW_ZOOM},
            "jumps": jumps,
            "added": added,
            "marks": self.marks,
            "outline": outline,
        }

    # --- one placed symbol
    def place(self, ref: str, unit: int, x: float, y: float, items: list[Any], box: Box) -> None:
        spec = self.part(ref)
        ls = self.symbol(spec["symbol"])
        angle = int(spec.get("angle", 0))
        comp = self.comps[ref]
        pinmap = {
            str(k): ([str(i) for i in v] if isinstance(v, list) else str(v))
            for k, v in (spec.get("pins") or {}).items()
        }
        upins = ls.unit_pins(unit)
        value = str(comp["value"])
        sym = [
            Sym("symbol"),
            [Sym("lib_id"), ls.lib_id],
            at(x, y, angle),
            [Sym("unit"), unit],
            [Sym("exclude_from_sim"), Sym("no")],
            [Sym("in_bom"), Sym("yes")],
            [Sym("on_board"), Sym("yes")],
            [Sym("dnp"), Sym("yes" if not_fitted(value) else "no")],
            [Sym("uuid"), self.uid("sym", ref, unit)],
        ]
        ext = Box()
        for bx, by in (
            (ls.extent.x0, ls.extent.y0),
            (ls.extent.x1, ls.extent.y1),
            (ls.extent.x0, ls.extent.y1),
            (ls.extent.x1, ls.extent.y0),
        ):
            sx, sy = rot(bx, by, angle)
            ext.add(x + sx, y + sy, x + sx, y + sy)
        box.add(ext.x0, ext.y0, ext.x1, ext.y1)
        flat = len(upins) <= 2 and ext.w >= ext.h
        fa = 90 if angle in (90, 270) else 0  # a field's angle turns with its symbol
        up = any(outward(pa, angle) == 90 for (_, _, pa, _, _) in upins.values())
        if flat:  # a flat two-pin part: reference above, value below, centered
            refpos, valpos, rj, vj = (
                (x, min(ext.y0 - 1.27, y - 2.54)),
                (x, max(ext.y1 + 1.27, y + 2.54)),
                None,
                None,
            )
        elif up:  # pins on top too: both fields to the right of the body
            bx1 = x + max(rot(ls.body.x0, 0, angle)[0], rot(ls.body.x1, 0, angle)[0])
            refpos, valpos, rj, vj = (bx1 + 1.27, y - 1.27), (bx1 + 1.27, y + 1.27), "left", "left"
        else:  # both fields above the body: the value, and the reference over it
            refpos, valpos, rj, vj = (
                (ext.x0, ext.y0 - 3.81),
                (ext.x0, ext.y0 - 1.27),
                "left",
                "left",
            )
        ref_at = at(*refpos, fa)
        sym.append([Sym("property"), "Reference", ref, ref_at, effects(justify=rj)])
        sym.append([Sym("property"), "Value", value, at(*valpos, fa), effects(justify=vj)])
        self.fields.append(
            {
                "ref": ref,
                "unit": unit,
                "page": self.cur_page,
                "at": ref_at,
                "justify": rj,
                "w": text_w(ref),
            }
        )
        for text, (tx, ty), j in ((ref, refpos, rj), (value, valpos, vj)):
            tw = text_w(text)
            x0 = tx if j == "left" else tx - tw / 2
            box.add(x0, ty - 1.0, x0 + tw, ty + 1.0)
        part_add = self.add_at.get(("part", ref))
        if part_add:  # an added or corrected part: its marker after its reference
            tw = text_w(ref)
            x0 = refpos[0] if rj == "left" else refpos[0] - tw / 2
            self.marker(
                part_add, x0 + tw + MARK_GAP, refpos[1], items, box, key=("part", ref, unit)
            )
        sym.extend(
            [Sym("property"), f, "", at(x, y, 0), effects(hide=True)]
            for f in ("Footprint", "Datasheet", "Description")
        )
        ends: dict[tuple[Any, ...], list[Any]] = {}
        for num, (px, py, pa, _name, _ln) in sorted(upins.items()):
            vend = pinmap.get(num, num)
            vl = []
            if vend == "-":
                net = "NC"
            else:
                vl = vend if isinstance(vend, list) else [vend]
                missing = [v for v in vl if v not in comp["pins"]]
                if missing:
                    raise SystemExit(
                        f"{ref}: our pin {num} stands for vendor pin(s) {missing}, "
                        "which netlist.yaml lacks"
                    )
                found = {comp["pins"][v] for v in vl}
                if len(found) != 1:
                    raise SystemExit(
                        f"{ref}: our pin {num} stands for vendor pins on different nets {found}"
                    )
                net = found.pop()
            sx, sy = rot(px, py, angle)
            key = (round(x + sx, 3), round(y + sy, 3))
            ends.setdefault(key, []).append((num, net, outward(pa, angle), tuple(vl)))
            sym.append([Sym("pin"), num, [Sym("uuid"), self.uid("pin", ref, unit, num)]])
        sym.append(
            [
                Sym("instances"),
                [
                    Sym("project"),
                    self.project,
                    [Sym("path"), self.cur_path, [Sym("reference"), ref], [Sym("unit"), unit]],
                ],
            ]
        )
        items.append(sym)
        stub = float(spec.get("stub", STUB))
        sides: dict[int, list[Any]] = {}
        for (ex, ey), lst in ends.items():
            nets = {n for _, n, _, _ in lst}
            if len(nets) != 1:
                raise SystemExit(
                    f"{ref}: pins {[p for p, _, _, _ in lst]} share a point but sit on {nets}"
                )
            sides.setdefault(lst[0][2], []).append(
                (ex, ey, nets.pop(), tuple(v for *_, vs in lst for v in vs))
            )
        for d, pts in sides.items():
            along = 1 if d in (0, 180) else 0
            pts.sort(key=lambda p: p[along])
            run: list[Any] = []
            for p in pts + [None]:
                if run and (p is None or p[2] != run[-1][2] or p[2] == "NC" or not stub):
                    self.decorate(ref, run, d, stub, items, box)
                    run = []
                if p is not None:
                    run.append(p)

    # --- what the end of a pin (or of a run of neighboring pins on one net) gets
    def pin_adds(self, ref: str, vpins: Iterable[str]) -> tuple[list[dict[str, Any]], bool]:
        """The additions and corrections marking these vendor pins of ``ref``
        (in id order), and whether their connection is an addition (the part's
        own, or one of the pins')."""
        found = {
            self.add_at[("pin", f"{ref}.{v}")]["id"]: self.add_at[("pin", f"{ref}.{v}")]
            for v in vpins
            if ("pin", f"{ref}.{v}") in self.add_at
        }
        part = self.add_at.get(("part", ref))
        added = (part is not None and part["kind"] == "addition") or any(
            e["kind"] == "addition" for e in found.values()
        )
        return [found[k] for k in sorted(found, key=lambda i: int(i[1:]))], added

    def decorate(
        self, ref: str, run: list[tuple[Any, ...]], d: int, stub: float, items: list[Any], box: Box
    ) -> None:
        net = run[0][2]
        vx, vy = DIRS[d]
        looks = [self.pin_adds(ref, p[3]) for p in run]
        marks = [e for m, _ in looks for e in m]
        dashed = [a for _, a in looks]
        every = all(dashed)  # the wires the run shares: dashed when all of it is added
        if net == "NC":
            for x, y, *_ in run:
                items.append(
                    [Sym("no_connect"), at(x, y), [Sym("uuid"), self.uid("nc", ref, x, y)]]
                )
                box.add(x - 1, y - 1, x + 1, y + 1)
            x, y = run[-1][0], run[-1][1]  # beyond the cross, on the pin's line
            for e in marks:
                if d == 180:
                    x -= (
                        self.marker(
                            e,
                            x - 1.27 - MARK_GAP,
                            y,
                            items,
                            box,
                            key=("nc", ref, x, y),
                            right_to_left=True,
                        )
                        + MARK_GAP
                    )
                else:
                    x += (
                        self.marker(e, x + 1.27 + MARK_GAP, y, items, box, key=("nc", ref, x, y))
                        + MARK_GAP
                    )
            return
        # an added connection always has a wire to show as one: a stub, even
        # where the part's pins otherwise carry their labels at the pin's end
        stub = STUB if (every and not stub) else stub
        ends = []
        for (x, y, *_), dash in zip(run, dashed, strict=True):
            ex, ey = x + vx * stub, y + vy * stub
            if stub:
                self.wire(x, y, ex, ey, items, ("stub", ref, x, y), dash)
            ends.append((ex, ey))
        for (ax, ay), (bx, by) in pairwise(ends):
            self.wire(ax, ay, bx, by, items, ("bar", ref, ax, ay), every)
        for jx, jy in ends[1:-1]:
            self.junction(jx, jy, items)
        ax, ay = ends[0]
        if net in self.grounds:
            if d == 270:  # bottom pins: the ground hangs from the first
                if len(ends) > 1:
                    self.junction(ax, ay, items)
                self.power(self.grounds[net], net, ax, ay, 270, items, box)
            else:
                if len(ends) > 1 or stub:
                    if len(ends) > 1:
                        self.junction(ax, ay, items)
                    ex, ey = ax + vx * STUB, ay + vy * STUB
                    self.wire(ax, ay, ex, ey, items, ("gext", ref, ax, ay), every)
                    ax, ay = ex, ey
                self.power(self.grounds[net], net, ax, ay, d, items, box)
            mx = ax + (
                1.6 if d in (90, 270) else 1.27
            )  # beside the ground symbol, clear of its name
            for e in marks:
                mx += (
                    self.marker(e, mx + MARK_GAP, ay - 1.6, items, box, key=("gnd", ref, ax, ay))
                    + MARK_GAP
                )
            return
        if d in (90, 270):  # a vertical pin: turn right, label flat
            if len(ends) > 1:
                ax, ay = ends[-1]
            ex = ax + PITCH
            self.wire(ax, ay, ex, ay, items, ("turn", ref, ax, ay), every)
            if len(ends) > 1:
                self.junction(ax, ay, items)
            ax, d = ex, 0
        elif len(ends) > 1:
            ex, ey = ax + vx * PITCH, ay
            self.junction(ax, ay, items)
            self.wire(ax, ay, ex, ey, items, ("lext", ref, ax, ay), every)
            ax = ex
        self.label(net, ax, ay, d, items, box, key=(ref, ax, ay), marks=marks)
        for x, y in ends:
            box.add(x, y, x, y)

    def wire(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        items: list[Any],
        key: tuple[Any, ...],
        dashed: bool = False,
    ) -> None:
        """A wire, at the project's one width; dotted (``ADD_WIRE``)
        where it is a Kleidos addition."""
        items.append(
            [
                Sym("wire"),
                [Sym("pts"), [Sym("xy"), x0, y0], [Sym("xy"), x1, y1]],
                stroke(0.0, ADD_WIRE if dashed else "default"),
                [Sym("uuid"), self.uid("w", *key)],
            ]
        )

    def marker(
        self,
        entry: dict[str, Any],
        x: float,
        y: float,
        items: list[Any],
        box: Box,
        key: tuple[Any, ...],
        right_to_left: bool = False,
    ) -> float:
        """A Kleidos addition's or correction's id ("K3") at (x, y), read from
        the left (or ending at x), linked to its row on the contents page once
        that page is laid out; return its width."""
        w = len(entry["id"]) * MARK_CHAR_W * MARK_FONT
        x0 = x - w if right_to_left else x
        node = [
            Sym("text"),
            entry["id"],
            [Sym("exclude_from_sim"), Sym("no")],
            at(x0, y, 0),
            effects(MARK_FONT, justify="left", bold=True, href="#1", color=MARK_COLOR),
            [Sym("uuid"), self.uid("mark", self.cur_path, entry["id"], *key)],
        ]
        items.append(node)
        self.markers.append({"id": entry["id"], "page": self.cur_page, "node": node})
        box.add(x0, y - 1.4, x0 + w, y + 1.4)
        return w

    def junction(self, x: float, y: float, items: list[Any]) -> None:
        items.append(
            [
                Sym("junction"),
                at(x, y),
                [Sym("diameter"), 0],
                [Sym("color"), 0, 0, 0, 0],
                [Sym("uuid"), self.uid("j", self.cur_path, x, y)],
            ]
        )

    def label(
        self,
        net: str,
        x: float,
        y: float,
        d: int,
        items: list[Any],
        box: Box,
        key: tuple[Any, ...],
        marks: Sequence[dict[str, Any]] = (),
    ) -> None:
        lw = len(net) * LABEL_CHAR_W + LABEL_PAD
        just = "left" if d == 0 else "right"
        label_at = at(x, y, d)
        items.append(
            [
                Sym("global_label"),
                net,
                [Sym("shape"), Sym("passive")],
                label_at,
                [Sym("fields_autoplaced"), Sym("yes")],
                effects(justify=just),
                [Sym("uuid"), self.uid("gl", *key)],
            ]
        )
        self.labels.append({"net": net, "page": self.cur_page, "ref": key[0], "at": label_at})
        # one linked "[page/zone]" per other page the net is on, read left to
        # right; the zone is filled in once every page is laid out (resolve()),
        # and every token is as wide as "[3/C4]", so filling it moves nothing
        pages = [p for p in self.net_pages.get(net, []) if p != self.cur_page]
        toks = [f"[{p}/??]" for p in pages]
        widths = [len(t) * REF_CHAR_W for t in toks]
        refs_w = sum(widths) + REF_GAP * max(len(toks) - 1, 0)
        start = x + lw + 1.2 if d == 0 else x - lw - 1.2 - refs_w
        tx = start
        for p, tok, tw in zip(pages, toks, widths, strict=True):
            node = self.text(
                tok, tx, y, REF_FONT, "left", href=f"#{p}", key=("ref", *key, f"[{p}]")
            )
            items.append(node)
            self.tokens.append({"node": node, "net": net, "page": self.cur_page, "to": p})
            tx += tw + REF_GAP
        w = lw + (refs_w + 1.2 if toks else 0)
        # the Kleidos additions and corrections at this label: its pins', and the net's own
        net_add = self.add_at.get(("net", net))
        for e in list(marks) + ([net_add] if net_add and net_add not in marks else []):
            if d == 0:
                w += MARK_GAP + self.marker(e, x + w + MARK_GAP, y, items, box, key=key)
            else:
                w += MARK_GAP + self.marker(
                    e, x - w - MARK_GAP, y, items, box, key=key, right_to_left=True
                )
        if d == 0:
            box.add(x, y - 1.4, x + w, y + 1.4)
        else:
            box.add(x - w, y - 1.4, x, y + 1.4)

    def text(
        self,
        body: str,
        x: float,
        y: float,
        size: float = FONT,
        justify: str = "left",
        bold: bool = False,
        href: str | None = None,
        key: tuple[Any, ...] | None = None,
        color: Sequence[int] | None = None,
    ) -> list[Any]:
        """A text item; with ``href`` ("#n" for page n) it is a link in the PDF."""
        return [
            Sym("text"),
            body,
            [Sym("exclude_from_sim"), Sym("no")],
            at(x, y, 0),
            effects(size, justify=justify, bold=bold, href=href, color=color),
            [Sym("uuid"), self.uid("txt", self.cur_path, *(key or (body[:40], x, y)))],
        ]

    def nav(self, x: float, y: float, page: int) -> list[Any]:
        """A row of page links: the contents, then each page by number."""
        out = []
        size = 1.5
        if page != 1:
            out.append(
                self.text(
                    "Contents", x, y, size, "left", bold=True, href="#1", key=("nav", "contents")
                )
            )
            x += text_w("Contents", size) + 3.0
        out.append(self.text("Pages:", x, y, size, "left", key=("nav", "pages")))
        x += text_w("Pages:", size) + 1.5
        for p in range(1, self.pages + 1):
            tok = f"[{p}]"
            if p == page:
                out.append(self.text(tok, x, y, size, "left", bold=True, key=("nav", p)))
            else:
                out.append(self.text(tok, x, y, size, "left", href=f"#{p}", key=("nav", p)))
            x += len(tok) * REF_CHAR_W * size / REF_FONT + 1.2
        return out

    def power(
        self, lib_id: str, net: str, x: float, y: float, d: int, items: list[Any], box: Box
    ) -> None:
        """A ground symbol at (x, y) pointing in sheet direction d."""
        self.symbol(lib_id)
        a = {270: 0, 0: 90, 180: 270, 90: 180}[d]
        self.pwr_n += 1
        ref = f"#PWR{self.pwr_n:03d}"
        vx, vy = DIRS[d]
        if d in (0, 180):  # stored right-justified: KiCad flips it upright on the right-hand glyph
            tx, ty, just, fa = x + vx * 3.4, y, "right", 90
        else:
            tx, ty, just, fa = x, y + vy * 4.0, None, 0
        node = [
            Sym("symbol"),
            [Sym("lib_id"), lib_id],
            at(x, y, a),
            [Sym("unit"), 1],
            [Sym("exclude_from_sim"), Sym("no")],
            [Sym("in_bom"), Sym("yes")],
            [Sym("on_board"), Sym("yes")],
            [Sym("dnp"), Sym("no")],
            [Sym("uuid"), self.uid("pwr", self.cur_path, net, x, y)],
            [Sym("property"), "Reference", ref, at(x, y, 0), effects(hide=True)],
            [Sym("property"), "Value", net, at(tx, ty, fa), effects(1.0, justify=just)],
        ]
        node.extend(
            [Sym("property"), f, "", at(x, y, 0), effects(hide=True)]
            for f in ("Footprint", "Datasheet", "Description")
        )
        node.append([Sym("pin"), "1", [Sym("uuid"), self.uid("pwrpin", self.cur_path, net, x, y)]])
        node.append(
            [
                Sym("instances"),
                [
                    Sym("project"),
                    self.project,
                    [Sym("path"), self.cur_path, [Sym("reference"), ref], [Sym("unit"), 1]],
                ],
            ]
        )
        items.append(node)
        tw = text_w(net, 1.0)
        if d == 0:
            box.add(x, y - 1.6, x + 3.4 + tw, y + 1.6)
        elif d == 180:
            box.add(x - 3.4 - tw, y - 1.6, x, y + 1.6)
        else:
            box.add(x - max(1.6, tw / 2), y, x + max(1.6, tw / 2), y + vy * 5.0)

    # --- blocks and sheets
    def item(self, it: dict[str, Any]) -> tuple[list[Any], Box]:
        """Lay one row item out around the origin; return its nodes and box."""
        items: list[Any] = []
        box = Box()
        if isinstance(it, str):
            ref, _, unit = it.partition(":")
            self.place(ref, {"": 1, "A": 1, "B": 2}[unit], 0, 0, items, box)
        elif "col" in it or "cols" in it:
            cx = 0.0
            for col in it.get("cols") or [it["col"]]:
                cbox, citems = Box(), []
                cy, bottom = 0.0, -math.inf
                for ref in col:
                    if ref != "-":  # a row each, or more where a tall part needs it
                        pitems: list[Any] = []
                        pbox = Box()
                        self.place(ref, 1, 0, cy, pitems, pbox)
                        dy = (
                            0.0
                            if bottom == -math.inf
                            else max(0.0, math.ceil((bottom + GRID - pbox.y0) / GRID - 1e-6) * GRID)
                        )
                        shift(pitems, 0, dy)
                        citems += pitems
                        cbox.add(pbox.x0, pbox.y0 + dy, pbox.x1, pbox.y1 + dy)
                        bottom = pbox.y1 + dy
                        cy += dy
                    cy += ROW
                dx = snap(cx - cbox.x0 + GRID / 2)
                shift(citems, dx, 0)
                items += citems
                box.add(cbox.x0 + dx, cbox.y0, cbox.x1 + dx, cbox.y1)
                cx = cbox.x1 + dx + COL_GAP
        elif "text" in it:
            size = it.get("size", FONT)
            lines = it["text"].rstrip().split("\n")
            items.append(
                [
                    Sym("text"),
                    it["text"].rstrip(),
                    [Sym("exclude_from_sim"), Sym("no")],
                    at(0, 0, 0),
                    effects(size, justify="left top"),
                    [Sym("uuid"), self.uid("txt", self.cur_path, it["text"][:40])],
                ]
            )
            box.add(0, 0, max(text_w(ln, size) for ln in lines), len(lines) * size * 1.7)
        else:
            raise SystemExit(f"layout item not understood: {it}")
        return items, box

    def child_sheet(self, sh: dict[str, Any], page: int) -> list[Any]:
        sheet_uuid = self.uid("sheet", sh["file"])
        self.cur_path = f"/{self.root_uuid}/{sheet_uuid}"
        self.cur_page = page
        out: list[Any] = []
        W, H = PAPER[self.lay.get("paper", "A3")]
        margin = 12.7
        sky = Skyline(
            margin, W - margin, margin, floor=H - 10.0, keepout=(W - KEEPOUT_X, H - KEEPOUT_Y)
        )
        for blk in sh["blocks"]:
            bitems, bbox, y = [], Box(), 0.0
            for row in blk["rows"]:
                x, rh = 0.0, 0.0
                for it in row:
                    its, ib = self.item(it)
                    if ib.empty:
                        continue
                    dx, dy = snap(x - ib.x0 + GRID / 2), snap(y - ib.y0 + GRID / 2)
                    shift(its, dx, dy)
                    bitems += its
                    bbox.add(ib.x0 + dx, ib.y0 + dy, ib.x1 + dx, ib.y1 + dy)
                    x = ib.x1 + dx + GAP
                    rh = max(rh, ib.h)
                y += rh + GAP
            title_h = 6.35
            bw = snap(bbox.w + 2 * BLOCK_PAD + GRID)
            bh = snap(bbox.h + 2 * BLOCK_PAD + title_h + GRID)
            if "at" in blk:
                bx, by = blk["at"]
            else:
                bx, by = sky.put(bw + SHEET_GAP, bh + SHEET_GAP)
            bx, by = snap(bx), snap(by)
            shift(bitems, snap(bx + BLOCK_PAD - bbox.x0), snap(by + BLOCK_PAD + title_h - bbox.y0))
            out += bitems
            out.append(
                [
                    Sym("rectangle"),
                    [Sym("start"), bx, by],
                    [Sym("end"), bx + bw, by + bh],
                    stroke(0.254, "dash"),
                    [Sym("fill"), [Sym("type"), Sym("none")]],
                    [Sym("uuid"), self.uid("frame", sh["file"], blk["title"])],
                ]
            )
            out.append(
                [
                    Sym("text"),
                    blk["title"],
                    [Sym("exclude_from_sim"), Sym("no")],
                    at(bx + 1.905, by + 1.905, 0),
                    effects(2.0, justify="left top", bold=True),
                    [Sym("uuid"), self.uid("title", sh["file"], blk["title"])],
                ]
            )
            if bx + bw > W - KEEPOUT_X and by + bh > H - KEEPOUT_Y and "at" not in blk:
                print(
                    f"warning: {sh['file']}: block {blk['title']!r} reaches into the title block's "
                    "corner",
                    file=sys.stderr,
                )
            if bx + bw > W - 5 or by + bh > H - 5:
                print(
                    f"warning: {sh['file']}: block {blk['title']!r} runs off the sheet "
                    f"({bx + bw:.0f} x {by + bh:.0f} mm of {W:.0f} x {H:.0f})",
                    file=sys.stderr,
                )
        for k, net in enumerate(sh.get("pwr_flags", [])):
            out += self.pwr_flag(
                net, snap(W - 130), snap(H - 45 - 17.78 * k)
            )  # stacked, clear of the page row
        out += self.nav(W - NAV_X, H - NAV_Y, page)
        return self.sheet_header(sh["name"]) + out + [[Sym("embedded_fonts"), Sym("no")]]

    # --- the index pages: tables of text, every place in them a link
    def rule(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        key: tuple[Any, ...],
        width: float = 0.15,
        color: Sequence[int] | None = None,
    ) -> list[Any]:
        """A graphic line (no connection)."""
        st = [Sym("stroke"), [Sym("width"), width], [Sym("type"), Sym("solid")]]
        if color:
            st.append([Sym("color"), *color, 1])
        return [
            Sym("polyline"),
            [Sym("pts"), [Sym("xy"), x0, y0], [Sym("xy"), x1, y1]],
            st,
            [Sym("fill"), [Sym("type"), Sym("none")]],
            [Sym("uuid"), self.uid("rule", self.cur_path, *key)],
        ]

    def link_text(
        self,
        body: str,
        x: float,
        y: float,
        to: dict[str, Any],
        items: list[Any],
        key: tuple[Any, ...],
        size: float = FONT,
        bold: bool = False,
        color: Sequence[int] | None = None,
    ) -> list[Any]:
        """A text that leads to a place (``to``: page, x, y); KiCad links it to
        the page, and the PDF step sends the link to the place."""
        node = self.text(
            body, x, y, size, "left", bold=bold, href=f"#{to['page']}", key=key, color=color
        )
        items.append(node)
        self.jumps.append(
            {
                "page": self.cur_page,
                "at": node[3],
                "to": to,
                "alt": f"{body}: {self.names[to['page']]}, {self.where(to)}",
            }
        )
        return node

    @staticmethod
    def cell_lines(cell: Any, wrap_chars: int | None) -> list[list[tuple[Any, ...]]]:
        """A table cell as lines, each a list of (text, place or None)."""
        if cell is None or cell == "":
            return []
        if isinstance(cell, dict) and "links" in cell:  # several places, a few per line
            per = cell.get("per", 4)
            toks = cell["links"]
            return [toks[i : i + per] for i in range(0, len(toks), per)]
        if isinstance(cell, dict):
            return [[(cell["text"], cell["to"])]]
        lines = wrap(str(cell), wrap_chars) if wrap_chars else [str(cell)]
        return [[(ln, None)] for ln in lines]

    @staticmethod
    def line_w(line: list[tuple[str, Any]]) -> float:
        return sum(text_w(t) for t, _ in line) + 1.27 * max(len(line) - 1, 0)

    def widths(
        self, head: Sequence[str], rows: Sequence[Sequence[Any]], wraps: Sequence[int | None]
    ) -> list[float]:
        out = []
        for i, h in enumerate(head):
            w = text_w(h) * 1.1  # bold
            for row in rows:
                for line in self.cell_lines(row[i], wraps[i]):
                    w = max(w, self.line_w(line))
            out.append(snap(w + TABLE_GAP + GRID / 2))
        return out

    def table(
        self,
        x: float,
        y: float,
        head: Sequence[str],
        rows: Sequence[Sequence[Any]],
        widths: Sequence[float],
        wraps: Sequence[int | None],
        key: str,
        items: list[Any],
    ) -> tuple[float, list[float]]:
        """Draw a table from (x, y): its header, a rule, then the rows; return
        the y below it and the y of each row."""
        cx = x
        for i, h in enumerate(head):
            items.append(self.text(h, cx, y, FONT, "left", bold=True, key=(key, "h", i)))
            cx += widths[i]
        items.append(self.rule(x, y + 1.6, x + sum(widths) - TABLE_GAP, y + 1.6, (key, "rule")))
        y += TABLE_PITCH + 0.8
        ys = []
        for r, row in enumerate(rows):
            cells = [self.cell_lines(c, wraps[i]) for i, c in enumerate(row)]
            cx = x
            for i, lines in enumerate(cells):
                for li, line in enumerate(lines):
                    tx = cx
                    for k, (t, to) in enumerate(line):
                        if to:
                            self.link_text(
                                t, tx, y + li * TABLE_PITCH, to, items, key=(key, r, i, li, k)
                            )
                        else:
                            items.append(
                                self.text(
                                    t,
                                    tx,
                                    y + li * TABLE_PITCH,
                                    FONT,
                                    "left",
                                    key=(key, r, i, li, k),
                                )
                            )
                        tx += text_w(t) + 1.27
                cx += widths[i]
            ys.append(y)
            y += max(1, *(len(c) for c in cells)) * TABLE_PITCH
        return y, ys

    def heading(
        self,
        body: str,
        x: float,
        y: float,
        items: list[Any],
        key: tuple[Any, ...],
        sub: str | None = None,
    ) -> float:
        items.append(self.text(body, x, y, 2.0, "left", bold=True, key=("head", key)))
        self.sections.setdefault(self.cur_page, []).append(
            {"title": body, "to": {"page": self.cur_page, "x": x, "y": y}}
        )
        if sub:
            items.append(self.text(sub, x, y + 3.81, FONT, "left", key=("sub", key)))
            return y + 3.81 + TABLE_PITCH + 1.0
        return y + 4.445

    def flow(
        self, tables: list[dict[str, Any]], items: list[Any], x0: float = 15.24, y0: float = 33.02
    ) -> None:
        """Set tables down in columns, top to bottom, a new column where the
        next would run past the page's foot (or into the title block's corner)."""
        W, H = PAPER[self.paper]
        x, y, right = x0, y0, x0
        for t in tables:
            w = sum(t["widths"]) - TABLE_GAP
            h = 4.445 + (6.35 if t.get("sub") else 0) + TABLE_PITCH + 0.8 + t["lines"] * TABLE_PITCH
            floor = H - 50.0 if x + w > W - KEEPOUT_X else H - 15.0
            if y > y0 and y + h > floor:
                x, y = right + 10.16, y0
                floor = H - 50.0 if x + w > W - KEEPOUT_X else H - 15.0
            if y + h > floor or x + w > W - 12.0:
                print(
                    f"warning: page {self.cur_page}: table {t['title']!r} runs off the sheet",
                    file=sys.stderr,
                )
            ty = self.heading(t["title"], x, y, items, t["title"], t.get("sub"))
            y, ys = self.table(
                x, ty, t["head"], t["rows"], t["widths"], t["wraps"], t["title"], items
            )
            if t.get("on_rows"):
                t["on_rows"](x, ys)
            y += 7.62
            right = max(
                right, x + w + max(0.0, t.get("mark_w", 0.0) + 1.27 - 7.62)
            )  # a long run of markers

    def adds_of(self, keys: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
        """The Kleidos additions and corrections that name any of these
        elements, each once, in id order."""
        found = {self.add_at[k]["id"]: self.add_at[k] for k in keys if k in self.add_at}
        return [found[i] for i in sorted(found, key=lambda i: int(i[1:]))]

    def mark_run(
        self,
        entries: list[dict[str, Any]],
        x: float,
        y: float,
        items: list[Any],
        key: tuple[Any, ...],
        right_to_left: bool = False,
    ) -> float:
        """The markers of ``entries`` side by side from x (or ending at x), in
        id order; return the run's width."""
        if right_to_left:
            x -= sum(len(e["id"]) * MARK_CHAR_W * MARK_FONT for e in entries) + MARK_GAP * (
                len(entries) - 1
            )
        x0 = x
        for e in entries:
            x += self.marker(e, x, y, items, Box(), key=key) + MARK_GAP
        return x - MARK_GAP - x0 if entries else 0.0

    def row_marks(
        self,
        t: dict[str, Any],
        keys: list[list[tuple[Any, ...]]],
        items: list[Any],
        name: str | None = None,
    ) -> None:
        """Mark the rows of index table ``t`` that a Kleidos addition or
        correction names (``keys``: the elements each row shows,
        ``index_keys()``), after the row; ``name`` tells apart the tables of
        one page (the table's title by default)."""
        name = name or t["title"]
        hits = [(k, es) for k, es in ((k, self.adds_of(ks)) for k, ks in enumerate(keys)) if es]
        if not hits:
            return
        t["mark_w"] = max(
            sum(len(e["id"]) * MARK_CHAR_W * MARK_FONT + MARK_GAP for e in es) for _, es in hits
        )

        def on_rows(x: float, ys: list[float]) -> None:
            xe = x + sum(t["widths"]) - TABLE_GAP + 1.27
            for k, es in hits:
                self.mark_run(es, xe, ys[k], items, key=("row", name, k))

        t["on_rows"] = on_rows

    def gpio_what(self, gt: dict[str, Any], gpio: str, v: dict[str, Any]) -> str:
        """A GPIO row's "What it does": the map's own text; where it has none
        and the pin is on no net, what the Kleidos entries on the row or on the
        pin say. Nothing more: the Net cell already says "not connected", so
        the row does not say it twice."""
        said = str(v.get("what") or "").strip()
        if said or str(v["net"]) != "NC":
            return said
        entries = self.adds_of(index_keys(self.net, "gpio", str(gpio), v["pin"], gt["title"]))
        return " ".join(str(e["what"]).strip() for e in entries)

    def mk_table(
        self,
        title: str,
        head: list[str],
        rows: list[list[Any]],
        wraps: list[int | None] | None = None,
        sub: str | None = None,
        on_rows: Callable[[float, list[float]], None] | None = None,
    ) -> dict[str, Any]:
        wraps = wraps or [None] * len(head)
        lines = sum(
            max(1, *(len(self.cell_lines(c, wraps[i])) for i, c in enumerate(r))) for r in rows
        )
        return {
            "title": title,
            "head": head,
            "rows": rows,
            "wraps": wraps,
            "sub": sub,
            "on_rows": on_rows,
            "widths": self.widths(head, rows, wraps),
            "lines": lines,
        }

    def places(self, net: str, every: bool = False) -> list[tuple[Any, ...]]:
        """Where a net is drawn, as (page/zone, place): one per page (the
        label a page link lands on), or one per zone of each page."""
        out = []
        for p in self.net_pages.get(net, []):
            first = self.net_spot(net, p)
            if not every:
                out.append((self.where(first), first))
                continue
            seen = {self.zone_of(first): first}
            for lab in sorted(
                (lab for lab in self.labels if lab["net"] == net and lab["page"] == p),
                key=lambda lab: (float(lab["at"][2]), float(lab["at"][1])),
            ):
                s = self.spot(p, lab["at"])
                seen.setdefault(self.zone_of(s), s)
            out += [
                (self.where(s), s)
                for _, s in sorted(seen.items(), key=lambda kv: natural_zone(kv[0]))
            ]
        return out

    def kind(self, ref: str) -> str:
        spec = self.part(ref)
        if spec.get("short"):
            return str(spec["short"])
        lib, name = spec["symbol"].split(":", 1)
        if lib == self.board:
            own = self.lay["symbols"][name]
            return str(own.get("short") or own.get("description", ""))
        for pat, k in STD_KINDS:
            if re.fullmatch(pat, spec["symbol"]):
                return k
        return ""

    def index_sheet(self, sh: dict[str, Any], page: int) -> list[Any]:
        self.cur_path = f"/{self.root_uuid}/{self.uid('sheet', sh['file'])}"
        self.cur_page = page
        W, H = PAPER[self.paper]
        out: list[Any] = []
        out.append(self.text(sh["name"], 15.24, 20.32, 3.0, "left", bold=True, key=("title",)))
        if sh.get("intro"):
            out.append(self.text(sh["intro"].strip(), 15.24, 25.4, FONT, "left", key=("intro",)))
        getattr(self, f"index_{sh['index']}")(sh, out)
        out += self.nav(W - NAV_X, H - NAV_Y, page)
        return self.sheet_header(sh["name"]) + out + [[Sym("embedded_fonts"), Sym("no")]]

    def index_parts(self, sh: dict[str, Any], items: list[Any]) -> None:
        rows, keys = [], []
        for ref in sorted(self.comps, key=natural):
            comp = self.comps[ref]
            pins = comp["pins"]
            nets = (
                " / ".join(str(pins[p]) for p in sorted(pins, key=str))
                if len(pins) <= 2
                else f"{len(pins)} pins"
            )
            units = sorted({f["unit"] for f in self.fields if f["ref"] == ref})
            spots = [self.field_spot(ref, u) for u in units]
            rows.append(
                [
                    {"text": ref, "to": spots[0]},
                    str(comp["value"]),
                    self.kind(ref),
                    nets,
                    "DNP" if not_fitted(comp["value"]) else "",
                    {"links": [(self.where(s), s) for s in spots], "per": 2},
                ]
            )
            keys.append(ref)
        head = ["Ref", "Value", "Kind", "Nets (pin 1 / pin 2)", "Fit", "Where"]
        wraps = [None, 22, None, None, None, None]
        n = len(sh.get("columns", [])) or 3
        # split into n columns of about as many lines each
        lines = [max(1, len(self.cell_lines(r[1], 22))) for r in rows]
        groups: list[Any] = []
        total, acc, start = sum(lines), 0, 0
        for i, ln in enumerate(lines):
            acc += ln
            if acc >= total * (len(groups) + 1) / n and len(groups) < n - 1:
                groups.append((start, i + 1))
                start = i + 1
        groups.append((start, len(rows)))
        widths = self.widths(head, rows, wraps)
        x = 15.24
        for gi, (a, b) in enumerate(groups):

            def keep(xg: float, ys: list[float], a: Any = a) -> None:
                for k, yy in enumerate(ys):
                    self.part_rows[keys[a + k]] = {
                        "page": self.cur_page,
                        "x": xg,
                        "y": round(yy, 4),
                    }

            y, ys = self.table(x, 33.02, head, rows[a:b], widths, wraps, f"parts{gi}", items)
            keep(x, ys)
            for k, yy in enumerate(ys):  # a part an entry names, or a pin of a two-pin part
                self.mark_run(
                    self.adds_of(index_keys(self.net, "parts", keys[a + k])),
                    x + sum(widths) - TABLE_GAP + 1.27,
                    yy,
                    items,
                    key=("row", "parts", keys[a + k]),
                )
            x += sum(widths) - TABLE_GAP + 10.16
        self.sections.setdefault(self.cur_page, []).extend(
            {"title": f"{keys[a]} to {keys[b - 1]}", "to": self.part_rows[keys[a]]}
            for a, b in groups
        )

    def index_nets(self, sh: dict[str, Any], items: list[Any]) -> None:
        rails = self.net.get("rails") or {}
        nominal = {n: str(r.get("nominal", "")) for n, r in rails.items()}
        multi = [
            n
            for n, p in self.net_pages.items()
            if len(p) > 1 and n != "NC" and n not in self.grounds
        ]
        order = [n for n in rails if n in self.net_pages and n not in self.grounds] + sorted(
            (n for n in multi if n not in rails), key=str.lower
        )
        rows = [
            [n, nominal.get(n, ""), {"links": self.places(n, every=True), "per": 6}] for n in order
        ]
        tables = [
            self.mk_table(
                "Nets on more than one page, and every rail",
                ["Net", "Nominal", "Drawn at"],
                rows,
                sub="Rails first; each place is page/zone, and leads to it.",
            )
        ]
        self.row_marks(tables[0], [index_keys(self.net, "nets", str(n)) for n in order], items)
        for gt in self.gpio_tables(sh):
            what = gt["what"]
            items_ = (
                sorted(gt["map"].items(), key=lambda kv: int(re.sub(r"\D", "", kv[0]) or 0))
                if gt["sort"]
                else list(gt["map"].items())
            )
            grows = []
            for g, v in items_:
                net = str(v["net"])
                row = [g, str(v["pin"]), NC_TEXT if net == "NC" else net]
                row += [self.gpio_what(gt, g, v)] if what else []
                row.append("" if net == "NC" else {"links": self.places(net), "per": 3})
                grows.append(row)
            head = ["GPIO", "Pin", "Net"] + (["What it does"] if what else []) + ["Drawn at"]
            tables.append(
                self.mk_table(
                    gt["title"],
                    head,
                    grows,
                    wraps=[None, None, None, gt["wrap"], None] if what else None,
                )
            )
            self.row_marks(
                tables[-1],
                [index_keys(self.net, "gpio", str(g), v["pin"], gt["title"]) for g, v in items_],
                items,
            )
        i2c = self.net.get("i2c") or {}
        if i2c:
            irows = [
                [
                    str(d["address"]),
                    {"text": d["ref"], "to": self.field_spot(d["ref"])},
                    str(d["part"]),
                    {"links": [(self.where(self.field_spot(d["ref"])), self.field_spot(d["ref"]))]},
                ]
                for d in i2c["devices"]
            ]
            bus = i2c["bus"]
            tables.append(
                self.mk_table(
                    "I2C bus",
                    ["Address", "Ref", "Part", "Drawn at"],
                    irows,
                    sub=f"SDA {bus['sda']}, SCL {bus['scl']}",
                )
            )
            self.row_marks(
                tables[-1],
                [index_keys(self.net, "i2c", str(d["ref"])) for d in i2c["devices"]],
                items,
            )
        tp = (
            sh.get("test_points") or {}
        )  # the table's title, a value column, a line under the title
        trows = []
        tps = sorted((r for r in self.comps if self.is_test_point(r)), key=natural)
        for ref in tps:
            s = self.field_spot(ref)
            row = [
                {"text": ref, "to": s},
                str(self.comps[ref]["pins"].get("1", "")),
                {"links": [(self.where(s), s)]},
            ]
            if tp.get("value"):
                row.insert(1, str(self.comps[ref].get("value", "")))
            trows.append(row)
        if trows:
            head = (
                ["Ref", "Value", "Net", "Drawn at"]
                if tp.get("value")
                else ["Ref", "Net", "Drawn at"]
            )
            tables.append(
                self.mk_table(tp.get("title", "Test points"), head, trows, sub=tp.get("sub"))
            )
            self.row_marks(tables[-1], [index_keys(self.net, "test_points", r) for r in tps], items)
        pulls = self.net.get("pulls") or []
        if pulls:
            urows = []
            for pl in pulls:
                way = "up" if "up" in pl else "down"
                urows.append(
                    [
                        str(pl["signal"]),
                        way,
                        str(pl[way]),
                        {"text": str(pl["via"]), "to": self.field_spot(str(pl["via"]))},
                        str(pl["value"]),
                        {"links": self.places(str(pl["signal"])), "per": 3},
                    ]
                )
            tables.append(
                self.mk_table(
                    "Pull-ups and pull-downs",
                    ["Signal", "Pull", "To", "Via", "Value", "Drawn at"],
                    urows,
                    sub="Every resistor with one end on a rail or ground.",
                )
            )
            self.row_marks(
                tables[-1], [index_keys(self.net, "pulls", str(pl["via"])) for pl in pulls], items
            )
        self.flow(tables, items)

    def gpio_tables(self, sh: dict[str, Any]) -> list[dict[str, Any]]:
        """The GPIO maps of the nets page (``gpio_maps()``)."""
        return gpio_maps(self.net, sh)

    def is_test_point(self, ref: str) -> bool:
        """A test point or pad: a part named TP, or drawn with KiCad's test point symbol."""
        return ref.startswith("TP") or self.part(ref)["symbol"] == "kleidos:TestPoint"

    def index_power(self, sh: dict[str, Any], items: list[Any]) -> None:
        tree = self.lay.get("power_tree") or {}
        y_end = self.power_tree(tree, items, 15.24, 38.1) if tree else 33.02
        rails = self.net.get("rails") or {}
        rows, keys = [], []
        for n, r in rails.items():
            if n in self.grounds or n not in self.net_pages:
                continue
            rows.append(
                [
                    n,
                    str(r.get("nominal", "")),
                    str(r.get("what", "")),
                    str(r.get("enable", "")),
                    {"links": self.places(n), "per": 3},
                ]
            )
            keys.append(index_keys(self.net, "rails", str(n)))
        t = self.mk_table(
            "Rails",
            ["Rail", "Nominal", "What feeds it, and what it supplies", "Enable", "Drawn at"],
            rows,
            wraps=[None, None, 70, 44, None],
        )
        self.row_marks(t, keys, items)
        self.flow([t], items, y0=y_end + 7.62)

    def power_tree(self, tree: dict[str, Any], items: list[Any], x0: float, y0: float) -> float:
        """Boxes for the sources, the parts that pass power on and the rails,
        left to right in the order power flows, each a link to where it is drawn."""
        px, py = tree.get("pitch", [27.94, 17.78])
        bw = tree.get("box", 24.13)
        boxes = {}
        rails = self.net.get("rails") or {}
        items.append(
            self.text(
                tree.get("title", "Power tree"),
                x0,
                y0 - 5.08,
                2.0,
                "left",
                bold=True,
                key=("head", "tree"),
            )
        )
        self.sections.setdefault(self.cur_page, []).append(
            {
                "title": tree.get("title", "Power tree"),
                "to": {"page": self.cur_page, "x": x0, "y": y0 - 5.08},
            }
        )
        bottom = y0
        for nid, (col, row) in tree["nodes"].items():
            name = nid.split("@")[0]
            cx, cy = x0 + col * px, y0 + row * py
            if name in self.comps:
                lines = [(f"{name} {self.kind(name)}", FONT), (str(self.comps[name]["value"]), 1.0)]
                en = self.enable_of(name)
                if en:
                    lines.append((en, 1.0))
                color = (224, 224, 224)
                to = self.field_spot(name)
            elif name in self.net_pages:
                lines = [(name, FONT), (str(rails.get(name, {}).get("nominal", "")), 1.0)]
                color = (127, 230, 255)
                to = self.net_spot(name, self.rail_page(name))
            else:
                raise SystemExit(f"power_tree: {nid} is neither a part nor a net")
            h = 2.2 + 2.3 * len(lines)
            y_top = cy - h / 2
            items.append(
                [
                    Sym("rectangle"),
                    [Sym("start"), cx, y_top],
                    [Sym("end"), cx + bw, y_top + h],
                    [
                        Sym("stroke"),
                        [Sym("width"), 0.2],
                        [Sym("type"), Sym("solid")],
                        [Sym("color"), *color, 1],
                    ],
                    [Sym("fill"), [Sym("type"), Sym("none")]],
                    [Sym("uuid"), self.uid("tbox", nid)],
                ]
            )
            ly = y_top + 2.3
            for i, (t, size) in enumerate(lines):
                if not t:
                    continue
                if i == 0:
                    self.link_text(t, cx + 1.27, ly, to, items, key=("tree", nid, i), size=size)
                else:
                    items.append(self.text(t, cx + 1.27, ly, size, "left", key=("tree", nid, i)))
                if text_w(t, size) > bw - 1.0:
                    print(f"warning: power_tree: {t!r} is wider than its box", file=sys.stderr)
                ly += 2.3
            # the box's part or rail again: its markers above the box's right corner
            self.mark_run(
                self.adds_of(index_keys(self.net, "tree", name)),
                cx + bw,
                y_top - TREE_MARK,
                items,
                key=("tree", nid),
                right_to_left=True,
            )
            boxes[nid] = (cx, cy, cx + bw)
            bottom = max(bottom, y_top + h)
        grey = RULE_COLOR
        for a, b in tree["edges"]:
            self.check_edge(a, b)
            ax0, ay, ax1 = boxes[a]
            bx0, by, _ = boxes[b]
            pts = (
                [(ax1, ay), (bx0 - 1.27, by)]
                if abs(ay - by) < 0.01
                else [(ax1, ay), (bx0 - 1.905, ay), (bx0 - 1.905, by), (bx0 - 1.27, by)]
            )
            items.append(
                [
                    Sym("polyline"),
                    [Sym("pts")] + [[Sym("xy"), px_, py_] for px_, py_ in pts],
                    [
                        Sym("stroke"),
                        [Sym("width"), 0.2],
                        [Sym("type"), Sym("solid")],
                        [Sym("color"), *grey, 1],
                    ],
                    [Sym("fill"), [Sym("type"), Sym("none")]],
                    [Sym("uuid"), self.uid("tedge", a, b)],
                ]
            )
            items.append(
                [
                    Sym("polyline"),
                    [
                        Sym("pts"),
                        [Sym("xy"), bx0 - 1.27, by - 0.635],
                        [Sym("xy"), bx0, by],
                        [Sym("xy"), bx0 - 1.27, by + 0.635],
                        [Sym("xy"), bx0 - 1.27, by - 0.635],
                    ],
                    [
                        Sym("stroke"),
                        [Sym("width"), 0.2],
                        [Sym("type"), Sym("solid")],
                        [Sym("color"), *grey, 1],
                    ],
                    [Sym("fill"), [Sym("type"), Sym("color")], [Sym("color"), *grey, 1]],
                    [Sym("uuid"), self.uid("tarrow", a, b)],
                ]
            )
        y = bottom + 5.08
        if tree.get("note"):
            note = tree["note"].strip()
            items.append(self.text(note, x0, y, FONT, "left", key=("tree", "note")))
            y += TABLE_PITCH
        return y

    def rail_page(self, net: str) -> int:
        """The page a rail is made on: where the part that feeds it is drawn."""
        rail = (self.net.get("rails") or {}).get(net, {})
        feeders = part_references(str(rail.get("from", "")))
        for p in self.net_pages[net]:
            if self.target_label(net, p)["ref"] in feeders:
                return p
        return self.net_pages[net][0]

    def enable_of(self, ref: str) -> str:
        """A part's enable as the drawing shows it: the net on its EN (nEN, CE)
        pin, or "always on" when that pin sits on a rail or on ground."""
        spec = self.part(ref)
        lib, name = spec["symbol"].split(":", 1)
        if lib != self.board:
            return ""
        own = self.lay["symbols"][name]
        rails = self.net.get("rails") or {}
        for side in ("left", "right", "bottom"):
            for p in own.get(side, []):
                sp = split_pin(p)
                if sp and sp[1] in ("EN", "nEN", "CE"):
                    net = str(self.comps[ref]["pins"].get(sp[0], "NC"))
                    if net in rails or net in self.grounds:
                        return "always on"
                    return f"{sp[1]} {net}"
        return ""

    def check_edge(self, a: str, b: str) -> None:
        """A power-tree arrow stands for a connection netlist.yaml has."""
        a0, b0 = a.split("@")[0], b.split("@")[0]

        def nets(r: str) -> set[str]:
            return set(map(str, self.comps[r]["pins"].values())) - {"NC"}

        if a0 in self.comps and b0 in self.comps:
            ok = bool((nets(a0) & nets(b0)) - set(self.grounds))
        elif a0 in self.comps:
            ok = b0 in nets(a0)
        elif b0 in self.comps:
            ok = a0 in nets(b0)
        else:
            ok = False
        if not ok:
            raise SystemExit(f"power_tree: {a} -> {b} is not a connection netlist.yaml has")

    def pwr_flag(self, net: str, x: float, y: float) -> list[Any]:
        self.symbol("kleidos:PWR_FLAG")
        self.pwr_n += 1
        ref = f"#FLG{self.pwr_n:03d}"
        nodes = [
            [
                Sym("symbol"),
                [Sym("lib_id"), "kleidos:PWR_FLAG"],
                at(x, y, 0),
                [Sym("unit"), 1],
                [Sym("exclude_from_sim"), Sym("no")],
                [Sym("in_bom"), Sym("yes")],
                [Sym("on_board"), Sym("yes")],
                [Sym("dnp"), Sym("no")],
                [Sym("uuid"), self.uid("flag", net)],
                [Sym("property"), "Reference", ref, at(x, y, 0), effects(hide=True)],
                [Sym("property"), "Value", "PWR_FLAG", at(x, y - 3.81, 0), effects(1.0)],
                [Sym("property"), "Footprint", "", at(x, y, 0), effects(hide=True)],
                [Sym("property"), "Datasheet", "", at(x, y, 0), effects(hide=True)],
                [Sym("property"), "Description", "", at(x, y, 0), effects(hide=True)],
                [Sym("pin"), "1", [Sym("uuid"), self.uid("flagpin", net)]],
                [
                    Sym("instances"),
                    [
                        Sym("project"),
                        self.project,
                        [Sym("path"), self.cur_path, [Sym("reference"), ref], [Sym("unit"), 1]],
                    ],
                ],
            ]
        ]
        self.power(self.grounds[net], net, x, y, 270, nodes, Box())
        return nodes

    def sheet_header(self, title: str, root: bool = False) -> list[Any]:
        tb = self.lay["title_block"]
        last = (self.lay.get("revisions") or [tb])[-1]  # the title block shows the latest revision
        comments = list(tb.get("comments", [])) + ([ADD_BLOCK_LINE] if self.adds else [])
        return [
            Sym("kicad_sch"),
            [Sym("version"), 20250114],
            [Sym("generator"), "kleidos_boards"],
            [Sym("generator_version"), "1.0"],
            [Sym("uuid"), self.root_uuid if root else self.uid("file", title)],
            [Sym("paper"), self.lay.get("paper", "A3")],
            [
                Sym("title_block"),
                [Sym("title"), f"{tb['title']}: {title}"],
                [Sym("date"), str(last["date"])],
                [Sym("rev"), str(last["rev"])],
                [Sym("company"), tb["company"]],
            ]
            + [[Sym("comment"), i + 1, c] for i, c in enumerate(comments)],
            [Sym("lib_symbols")],
        ]

    def root_sheet(self) -> list[Any]:
        """The contents: a heading, one box per sheet (linked to its page) and a legend."""
        self.cur_path = f"/{self.root_uuid}"
        self.cur_page = 1
        root = self.lay["root"]
        doc = self.sheet_header(root["title"], root=True)
        x, y = 25.4, 22.86
        doc.append(self.text(root["heading"], x, y, 3.0, "left top", bold=True, key=("heading",)))
        doc.append(
            self.text(
                root["subheading"] + (f", {ADD_SUBTITLE}" if self.adds else ""),
                x,
                y + 6.35,
                ROOT_FONT,
                "left top",
                key=("subheading",),
            )
        )
        doc += self.nav(x, y + 13.97, 1)
        w, pad = 172.72, 2.54
        y = 40.64
        for page, sh in enumerate(self.lay["sheets"], start=2):
            h, step = (
                (17.78, 20.32) if "index" in sh else tuple(root.get("sheet_box", (27.94, 31.75)))
            )
            doc.append(
                [
                    Sym("sheet"),
                    at(x, y),
                    [Sym("size"), w, h],
                    [Sym("exclude_from_sim"), Sym("no")],
                    [Sym("in_bom"), Sym("yes")],
                    [Sym("on_board"), Sym("yes")],
                    [Sym("dnp"), Sym("no")],
                    stroke(0.254, "solid"),
                    [Sym("fill"), [Sym("color"), 0, 0, 0, 0.0]],
                    [Sym("uuid"), self.uid("sheet", sh["file"])],
                    [
                        Sym("property"),
                        "Sheetname",
                        sh["name"],
                        at(x + pad, y + pad, 0),
                        effects(2.0, justify="left top", bold=True),
                    ],
                    [
                        Sym("property"),
                        "Sheetfile",
                        sh["file"],
                        at(x, y + h + 0.5884, 0),
                        effects(justify="left top", hide=True),
                    ],
                    [
                        Sym("instances"),
                        [
                            Sym("project"),
                            self.project,
                            [Sym("path"), f"/{self.root_uuid}", [Sym("page"), str(page)]],
                        ],
                    ],
                ]
            )
            doc.append(
                self.text(
                    f"Page {page}",
                    x + w - pad,
                    y + pad,
                    2.0,
                    "right top",
                    bold=True,
                    key=("page", page),
                )
            )
            cols = int((w - 2 * pad) / text_w("x", ROOT_FONT))
            body = wrap(sh["summary"], cols)
            if sh.get("parts"):
                body += [""] + wrap("Main parts: " + sh["parts"], cols)
            doc.append(
                self.text(
                    "\n".join(body), x + pad, y + 7.62, ROOT_FONT, "left top", key=("sum", page)
                )
            )
            y += step
        x, y = 215.9, 40.64
        for panel in root["panels"]:
            doc.append(
                self.text(
                    panel["title"], x, y, 2.0, "left top", bold=True, key=("ptitle", panel["title"])
                )
            )
            lines = panel["text"].rstrip().split("\n")
            doc.append(
                self.text(
                    "\n".join(lines),
                    x,
                    y + 4.445,
                    ROOT_FONT,
                    "left top",
                    key=("ptext", panel["title"]),
                )
            )
            y += 4.445 + len(lines) * ROOT_FONT * LINE_PITCH + 6.35
        if self.adds:
            y = self.additions_table(x, y, doc)
        if "additions" not in self.index_page:  # else the revision history is the continuation's
            self.revision_history(x, y, doc)
        return doc + [
            [Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]],
            [Sym("embedded_fonts"), Sym("no")],
        ]

    def revision_history(self, x: float, y: float, doc: list[Any]) -> None:
        """The revision history from (x, y), its changes kept left of the title
        block where it reaches down beside it."""
        revs = self.lay.get("revisions") or []
        if revs:
            doc.append(
                self.text(
                    "Revision history", x, y, 2.0, "left top", bold=True, key=("ptitle", "revs")
                )
            )
            rows = [[str(r["rev"]), str(r["date"]), str(r["change"])] for r in revs]
            head, (W, H) = ["Rev", "Date", "Change"], PAPER[self.paper]

            def laid(chars: int) -> tuple[list[int | None], list[float], float]:
                """The table with its changes wrapped at ``chars``: the wraps, the widths, the y
                below it."""
                wraps = [None, None, chars]
                lines = sum(len(wrap(r[2], chars)) for r in rows)
                return (
                    wraps,
                    self.widths(head, rows, wraps),
                    y + 6.35 + TABLE_PITCH + 0.8 + lines * TABLE_PITCH,
                )

            wraps, widths, y_end = laid(70)
            if (
                y_end > H - KEEPOUT_Y
            ):  # it reaches down beside the title block: keep its text left of the block
                room = W - KEEPOUT_X - (x + widths[0] + widths[1])
                wraps, widths, y_end = laid(max(30, int(room / CHAR_W)))
            if y_end > H - 12.0:
                print(
                    "warning: contents page: the revision history runs off the sheet",
                    file=sys.stderr,
                )
            self.table(x, y + 6.35, head, rows, widths, wraps, "revs", doc)

    def element_spot(self, eid: str) -> dict[str, Any]:
        """Where an addition or correction is drawn: its first marker, in page
        and reading order."""
        found = [m for m in self.markers if m["id"] == eid]
        if not found:
            raise SystemExit(
                f"kleidos {eid}: its element is not drawn anywhere (a rail or GPIO no table lists?)"
            )
        first = min(
            found, key=lambda m: (m["page"], float(m["node"][3][2]), float(m["node"][3][1]))
        )
        return self.spot(first["page"], first["node"][3])

    def additions_table(self, x: float, y: float, doc: list[Any]) -> float:
        """The contents page's table of the Kleidos additions and corrections:
        each id leads to its element, and each marker of it back to its row;
        return the y below it. The rows page 1 has no room for (above the
        title block's corner) go on to the contents' continuation, when the
        layout has one (a sheet with ``index: additions``)."""
        doc.append(self.text(ADD_TITLE, x, y, 2.0, "left top", bold=True, key=("ptitle", "adds")))
        self.sections.setdefault(1, []).append(
            {"title": ADD_TITLE, "to": {"page": 1, "x": x, "y": y}}
        )
        rows = []
        for e in self.adds:
            what = str(e["what"]).strip()
            if e["kind"] == "correction":
                what += f" The vendor's print: {str(e['vendor']).strip()}"
            src = e["source"]
            rows.append(
                [
                    {"text": e["id"], "to": self.element_spot(e["id"])},
                    e["kind"],
                    what,
                    f"{src['type']}: {str(src['cite']).strip()}",
                ]
            )
        self.add_widths = self.widths(ADD_HEAD, rows, ADD_WRAPS)
        floor = PAPER[self.paper][1] - 48.0
        keep = len(rows)
        if "additions" in self.index_page:
            top, keep = y + 6.35 + TABLE_PITCH + 0.8, 0
            for r in rows:
                top += (
                    max(1, *(len(self.cell_lines(c, ADD_WRAPS[i])) for i, c in enumerate(r)))
                    * TABLE_PITCH
                )
                if top > floor:
                    break
                keep += 1
        self.adds_rest = list(zip(self.adds[keep:], rows[keep:], strict=True))
        y_end = self.add_rows(
            x, y + 6.35, list(zip(self.adds[:keep], rows[:keep], strict=True)), doc
        )
        if y_end > floor:
            print(
                f"warning: contents page: the {ADD_TITLE} table reaches into the title block's "
                "corner",
                file=sys.stderr,
            )
        return y_end + 6.35

    def add_rows(self, x: float, y: float, rows: list[Any], doc: list[Any]) -> float:
        """Rows of the additions table on the current page, from (x, y), each
        id drawn as its markers are (bold, in the marker color) and leading to
        its element; every marker of it leads back here. Return the y below."""
        y_end, ys = self.table(
            x, y, ADD_HEAD, [[""] + r[1:] for _, r in rows], self.add_widths, ADD_WRAPS, "adds", doc
        )
        for (e, r), ry in zip(rows, ys, strict=True):
            self.link_text(
                e["id"],
                x,
                ry,
                r[0]["to"],
                doc,
                key=("adds", e["id"]),
                size=MARK_FONT * FONT,
                bold=True,
                color=MARK_COLOR,
            )
            row = {"page": self.cur_page, "x": x, "y": round(ry, 4)}
            self.marks[f"add-{e['id']}"] = self.element_spot(e["id"])
            for m in (m for m in self.markers if m["id"] == e["id"]):
                for part in m["node"]:  # the marker leads to the page its row is on
                    if isinstance(part, list) and part[:1] == [Sym("effects")]:
                        for sub in part:
                            if isinstance(sub, list) and sub[:1] == [Sym("href")]:
                                sub[1] = f"#{self.cur_page}"
                self.jumps.append(
                    {
                        "page": m["page"],
                        "at": m["node"][3],
                        "to": row,
                        "alt": f"{e['id']} in the {ADD_TITLE} table, page {self.cur_page}",
                    }
                )
        return y_end

    def index_additions(self, sh: dict[str, Any], items: list[Any]) -> None:
        """The contents' continuation: the rest of the additions table, if
        page 1 had no room for all of it, then the revision history."""
        x, y = 15.24, 33.02
        if self.adds_rest:
            title = f"{ADD_TITLE} (continued)"
            items.append(self.text(title, x, y, 2.0, "left top", bold=True, key=("ptitle", "adds")))
            self.sections.setdefault(self.cur_page, []).append(
                {"title": title, "to": {"page": self.cur_page, "x": x, "y": y}}
            )
            y = self.add_rows(x, y + 6.35, self.adds_rest, items) + 6.35
            if (
                y > PAPER[self.paper][1] - 48.0
                and x + sum(self.add_widths) > PAPER[self.paper][0] - 125.0
            ):
                print(
                    f"warning: page {self.cur_page}: the {ADD_TITLE} table reaches into the title "
                    "block's corner",
                    file=sys.stderr,
                )
        self.revision_history(x, y, items)


class Skyline:
    """Bottom-left packing: each block goes where it sits highest, then leftmost."""

    def __init__(
        self,
        x0: float,
        x1: float,
        y0: float,
        floor: float = math.inf,
        keepout: tuple[Any, ...] | None = None,
    ) -> None:
        self.x0, self.x1 = x0, x1
        self.floor = floor  # no block reaches below this
        self.keepout = keepout  # (x from, y from): the title block's corner
        self.segs = [(x0, x1, y0)]  # (start, end, top free y)

    def fits(self, x: float, y: float, w: float, h: float) -> bool:
        if y + h > self.floor + 0.01:
            return False
        return not (self.keepout and x + w > self.keepout[0] and y + h > self.keepout[1] + 0.01)

    def put(self, w: float, h: float) -> tuple[float, float]:
        best = None
        for start, _, _ in self.segs:
            if start + w > self.x1 + 0.01:
                continue
            y = max(t for s, e, t in self.segs if s < start + w - 0.01 and e > start + 0.01)
            if not self.fits(start, y, w, h):
                continue
            if best is None or y < best[1] - 0.01:
                best = (start, y)
        if best is None:
            best = (self.x0, max(t for _, _, t in self.segs))
        x, y = best
        segs = []
        for s, e, t in self.segs:
            if e <= x or s >= x + w:
                segs.append((s, e, t))
                continue
            if s < x:
                segs.append((s, x, t))
            if e > x + w:
                segs.append((x + w, e, t))
        segs.append((x, x + w, y + h))
        self.segs = sorted(segs)
        return best


def wrap(text: str, cols: int) -> list[str]:
    """Break a paragraph into lines of at most ``cols`` characters, at spaces."""
    lines = [""]
    for word in text.split():
        if lines[-1] and len(lines[-1]) + 1 + len(word) > cols:
            lines.append("")
        lines[-1] = (lines[-1] + " " + word).strip()
    return lines


def item_refs(it: dict[str, Any]) -> list[str]:
    if isinstance(it, str):
        return [it]
    if "col" in it:
        return [r for r in it["col"] if r != "-"]
    if "cols" in it:
        return [r for c in it["cols"] for r in c if r != "-"]
    return []


def shift(nodes: list[Any], dx: float, dy: float) -> None:
    """Move every sheet coordinate of the given items."""
    for n in nodes:
        _shift(n, dx, dy)


def _shift(n: Any, dx: float, dy: float) -> None:
    if not isinstance(n, list) or not n:
        return
    if n[0] in ("at", "xy", "start", "end") and len(n) >= 3 and not isinstance(n[1], list):
        n[1] = round(n[1] + dx, 4)
        n[2] = round(n[2] + dy, 4)
        return
    for k in n[1:]:
        _shift(k, dx, dy)


PRO_TEMPLATE = """{
  "meta": {
    "filename": "@BOARD@.kicad_pro",
    "version": 3
  },
  "erc": {
    "erc_exclusions": [],
    "meta": {
      "version": 0
    },
    "pin_map": [],
    "rule_severities": {
      "lib_symbol_issues": "ignore",
      "lib_symbol_mismatch": "ignore"@ERC_EXTRA@
    }
  },
  "schematic": {
    "drawing": {
      "default_line_thickness": @LINE_MIL@.0,
      "default_text_size": 50.0,
      "intersheets_ref_own_page": false,
      "intersheets_ref_prefix": "[",
      "intersheets_ref_short": false,
      "intersheets_ref_show": false,
      "intersheets_ref_suffix": "]"
    },
    "legacy_lib_dir": "",
    "page_layout_descr_file": "../../_shared/kicad/kleidos-dark.kicad_wks",
    "legacy_lib_list": []
  },
  "net_settings": {
    "classes": [
      {
        "bus_width": @BUS_MIL@,
        "line_style": 0,
        "name": "Default",
        "priority": 2147483647,
        "schematic_color": "rgba(0, 0, 0, 0.000)",
        "wire_width": @LINE_MIL@
      }
    ],
    "meta": {
      "version": 4
    },
    "net_colors": null,
    "netclass_assignments": null,
    "netclass_patterns": []
  },
  "sheets": [],
  "text_variables": {
    "LICENSE": "@LICENSE@",
    "SOURCE_URL": "@SOURCE_URL@"
  }
}
"""


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("board")
    args = ap.parse_args(argv)
    try:
        board = board_id(args.board)
    except OutsideError as exc:
        ap.error(str(exc))
    b = Builder(board)
    files = b.build()
    for name, doc in files.items():
        if name.endswith(".kicad_sch") and name != f"{board}.kicad_sch":
            used = sorted({n[1][1] for n in doc if isinstance(n, list) and n and n[0] == "symbol"})
            lib = next(n for n in doc if isinstance(n, list) and n and n[0] == "lib_symbols")
            lib += [renamed(b.lib[u].node, u) for u in used]
    for name, doc in files.items():
        (b.dir / name).write_text(dump(doc) + "\n", encoding="utf-8")
    (b.dir / "links.json").write_text(json.dumps(b.link_map(), indent=1) + "\n", encoding="utf-8")
    (b.dir / "sym-lib-table").write_text(
        "(sym_lib_table\n\t(version 7)\n"
        f'\t(lib (name "{board}") (type "KiCad") (uri "${{KIPRJMOD}}/{board}.kicad_sym") '
        f'(options "") (descr "Kleidos boards: {board} symbols"))\n'
        f'\t(lib (name "{GENERIC_LIB}") (type "KiCad") (uri '
        f'"${{KIPRJMOD}}/{GENERIC_LIB}.kicad_sym") '
        f'(options "") (descr "Kleidos boards: the generic symbols"))\n)\n',
        encoding="utf-8",
    )
    # a board may switch off more ERC checks, each named in layout.yaml's erc_ignore (its README
    # says why)
    extra = "".join(f',\n      "{rule}": "ignore"' for rule in b.lay.get("erc_ignore") or [])
    (b.dir / f"{board}.kicad_pro").write_text(
        PRO_TEMPLATE.replace("@BOARD@", board)
        .replace("@ERC_EXTRA@", extra)
        .replace("@LINE_MIL@", str(LINE_MIL))
        .replace("@BUS_MIL@", str(BUS_MIL))
        .replace("@LICENSE@", LICENSE)
        .replace("@SOURCE_URL@", SOURCE_URL),
        encoding="utf-8",
    )
    print(f"wrote {len(files) + 3} files to {b.dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
