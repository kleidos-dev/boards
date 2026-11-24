# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Hold a board's KiCad schematic to its ``netlist.yaml``, pin by pin.

KiCad exports the drawn schematic's netlist (``kicad-cli sch export netlist``,
the XML form); this check maps each drawn pin back to the vendor's pin through
``layout.yaml``'s pin maps and compares, for every component of
``netlist.yaml``:

- that it is drawn, once per unit it has, and that nothing else is;
- that every vendor pin is drawn and lands on the net ``netlist.yaml`` names
  (an unconnected pin, ``NC``, on no net with another pin);
- that no two vendor nets were merged and none was split.

Power symbols (``#PWR``, ``#FLG``) are drawing aids and take no part.

It also holds the board's Kleidos additions and corrections (``kleidos`` in
``netlist.yaml``, ``additions()``): every entry is well formed, names its
source (a type and a non-empty citation) and an element the netlist has; every
entry is marked on the drawing ("K3") and has its row in the contents page's
table, and every marker and row is an entry's. ``check_schematic_links.py``
holds where their links land.

And it holds what the index pages say of them (``index_pages()``), read from
the KiCad files: a board with entries says so under the contents page's heading
and in every page's title block, and one without does not; every row of an
index table and every box of the power tree that shows an entry's element again
carries its marker, and no other does; in a GPIO table that says what each pin
does, a pin on no net reads "not connected" under Net and, under "What it
does", the netlist's own text, else what the Kleidos entries on it say, else
nothing (the Net cell has said it). The contents pages are page 1 and the
continuation a board's layout may add (``index: additions``).

Usage::

    python3 _shared/check_schematic.py <board> [--netlist FILE.xml]

Without ``--netlist`` it runs ``kicad-cli`` itself: the one ``KICAD_CLI`` names
in the environment or the one on the ``PATH``, never one named on the command
line. Exit status 0 on a match, 1 otherwise.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "kicad"))
import kleidos_kicad as kit
from paths import ROOT, OutsideError, board_id, work_path


def export(board: str) -> Path:
    """The netlist kicad-cli exports of a board's schematic, in a folder of its own."""
    folder = ROOT / board / "schematic"
    out = Path(tempfile.mkdtemp()) / f"{board}.xml"
    subprocess.run(
        [
            kit.kicad_cli(),
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadxml",
            "-o",
            str(out),
            str(folder / f"{board}.kicad_sch"),
        ],
        check=True,
        capture_output=True,
    )
    return out


def drawn_nets(xml: Path) -> dict[tuple[str, str], str]:
    """(reference, our pin) -> net name, from KiCad's XML netlist."""
    root = ET.parse(xml).getroot()  # noqa: S314  (this repository's own file)
    out: dict[tuple[str, str], str] = {}
    for net in root.iter("net"):
        name = net.get("name", "")
        # a local label carries its sheet path; an unconnected pin's net is named
        # after the pin ("unconnected-(U1-IO11/CMD-Pad30)"), whose name may hold a "/"
        if not name.startswith(("unconnected-", "Net-(")):
            name = name.rsplit("/", 1)[-1]
        nodes = [(n.get("ref", ""), n.get("pin", "")) for n in net.iter("node")]
        nodes = [x for x in nodes if not x[0].startswith("#")]
        if name.startswith("unconnected-") or (len(nodes) == 1 and name.startswith("Net-(")):
            name = "NC"
        for node in nodes:
            out[node] = name
    return out


def pin_maps(layout: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    """reference -> our pin -> the vendor pins it stands for (identity when unlisted)."""
    out = {}
    parts = layout["parts"]
    for ref, spec in parts.items():
        if ref.startswith("_") or not isinstance(spec, dict) or "pins" not in spec:
            continue
        out[ref] = {
            str(k): ([str(i) for i in v] if isinstance(v, list) else [str(v)])
            for k, v in spec["pins"].items()
        }
    return out


def compare(board: str, xml: Path) -> list[str]:
    folder = ROOT / board / "schematic"
    facts = yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8"))["components"]
    layout = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    maps = pin_maps(layout)
    drawn = drawn_nets(xml)
    errors: list[str] = []
    seen: dict[tuple[str, str], str] = {}
    refs_drawn = {r for r, _ in drawn}
    errors.extend(
        f"{ref}: drawn but not in netlist.yaml" for ref in sorted(refs_drawn - set(facts))
    )
    for (ref, ours), net in sorted(drawn.items()):
        if ref not in facts:
            continue
        for vend in maps.get(ref, {}).get(ours, [ours]):
            if vend == "-":
                continue
            if (ref, vend) in seen and seen[(ref, vend)] != net:
                errors.append(f"{ref}.{vend}: drawn on {seen[(ref, vend)]} and on {net}")
            seen[(ref, vend)] = net
    # the drawn net names must be the facts' names, pin for pin
    for ref, comp in sorted(facts.items()):
        for pin, want in comp["pins"].items():
            got = seen.get((ref, str(pin)))
            if got is None:
                errors.append(f"{ref}.{pin}: not drawn (netlist.yaml: {want})")
            elif got != want:
                errors.append(f"{ref}.{pin}: drawn on {got}, netlist.yaml says {want}")
    return errors


def contents_pages(layout: dict[str, Any]) -> set[int]:
    """The pages that list the Kleidos additions and corrections: the contents
    page, and the continuation a layout adds when page 1 runs out of room
    (a sheet with ``index: additions``)."""
    return {1} | {
        page for page, sh in enumerate(layout["sheets"], start=2) if sh.get("index") == "additions"
    }


def drawn_marks(board: str) -> tuple[dict[str, list[int]], dict[str, bool]]:
    """What the KiCad files show of the Kleidos additions and corrections:
    every marker ("K3", a linked text off the contents page) with the pages it
    is on, and every row of the contents page's table (id -> whether it links)."""
    from kicad_schematic import ADD_ID, parse

    folder = ROOT / board / "schematic"
    layout = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    files = [f"{board}.kicad_sch"] + [sh["file"] for sh in layout["sheets"]]
    contents = contents_pages(layout)
    markers: dict[str, list[int]] = {}
    rows: dict[str, bool] = {}
    for page, name in enumerate(files, start=1):
        for node in parse((folder / name).read_text(encoding="utf-8")):
            if not (
                isinstance(node, list)
                and node
                and node[0] == "text"
                and ADD_ID.fullmatch(str(node[1]))
            ):
                continue
            eff = next((x for x in node if isinstance(x, list) and x[:1] == ["effects"]), [])
            linked = any(isinstance(x, list) and x[:1] == ["href"] for x in eff)
            if page in contents:
                rows[str(node[1])] = linked
            else:
                markers.setdefault(str(node[1]), []).append(page)
    return markers, rows


def additions(board: str) -> list[str]:
    """The Kleidos additions and corrections: netlist.yaml's ``kleidos`` entries
    are well formed and each names its source; every entry is marked where its
    element is drawn (a pin, a part or a net on a drawing page, a GPIO, an I2C
    address, a pull or a rail on an index page; ``index_pages()`` holds the
    markers the index pages repeat) and has its row on the contents page, and
    every marker and row is an entry's."""
    from kicad_schematic import additions_errors

    folder = ROOT / board / "schematic"
    facts = yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8"))
    layout = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    errors = [f"kleidos: {e}" for e in additions_errors(facts, layout)]
    entries = [e for e in facts.get("kleidos") or [] if isinstance(e, dict)]
    ids = [str(e.get("id")) for e in entries]
    index = {
        page for page, sh in enumerate(layout["sheets"], start=2) if "index" in sh
    } - contents_pages(layout)
    markers, rows = drawn_marks(board)
    for e in entries:
        given = e.get("element")
        eid, el = str(e.get("id")), given if isinstance(given, dict) else {}
        drawn = any(k in el for k in ("pin", "part", "net"))  # its element is on a drawing page
        if not any((page in index) != drawn for page in markers.get(eid, [])):
            errors.append(
                f"kleidos {eid}: no marker on " + ("the drawing" if drawn else "an index page")
            )
        if eid not in rows:
            errors.append(f"kleidos {eid}: no row in the contents page's table")
        elif not rows[eid]:
            errors.append(f"kleidos {eid}: its row on the contents page leads nowhere")
    errors.extend(
        f"{eid}: marked on page(s) {sorted(set(markers[eid]))}, but netlist.yaml has no such entry"
        for eid in sorted(set(markers) - set(ids))
    )
    errors.extend(
        f"{eid}: a row of the contents page's table, but netlist.yaml has no such entry"
        for eid in sorted(set(rows) - set(ids))
    )
    return errors


def _child(node: list[Any], key: str) -> list[Any] | None:
    return next((x for x in node if isinstance(x, list) and x and x[0] == key), None)


def _need(node: list[Any], key: str) -> list[Any]:
    """The child ``(key ...)`` of a node, which a KiCad file always writes there."""
    found = _child(node, key)
    if found is None:
        raise ValueError(f"a ({node[0] if node else '?'} ...) node with no ({key} ...)")
    return found


def page_items(path: Path) -> dict[str, Any]:
    """What a KiCad sheet file draws that ``index_pages()`` reads: its texts
    (body, place, size, bold, linked), its horizontal rules, its rectangles and
    the lines of its title block (the company and the comments)."""
    from kicad_schematic import parse

    out: dict[str, Any] = {"texts": [], "rules": [], "rects": [], "block": []}
    for node in parse(path.read_text(encoding="utf-8")):
        if not (isinstance(node, list) and node):
            continue
        if node[0] == "title_block":
            out["block"] = [
                str(n[-1])
                for n in node[1:]
                if isinstance(n, list) and n[0] in ("company", "comment")
            ]
        elif node[0] == "text":
            pos, eff = _need(node, "at"), _need(node, "effects")
            fnt = _need(eff, "font")
            out["texts"].append(
                {
                    "body": str(node[1]),
                    "x": float(pos[1]),
                    "y": float(pos[2]),
                    "size": float(_need(fnt, "size")[1]),
                    "bold": _child(fnt, "bold") is not None,
                    "href": _child(eff, "href") is not None,
                }
            )
        elif node[0] == "polyline":
            pts = _need(node, "pts")[1:]
            if len(pts) == 2 and abs(float(pts[0][2]) - float(pts[1][2])) < 1e-6:
                xs = sorted((float(pts[0][1]), float(pts[1][1])))
                out["rules"].append((xs[0], xs[1], float(pts[0][2])))
        elif node[0] == "rectangle":
            a, b = _need(node, "start"), _need(node, "end")
            xs, ys = sorted((float(a[1]), float(b[1]))), sorted((float(a[2]), float(b[2])))
            out["rects"].append((xs[0], ys[0], xs[1], ys[1]))
    return out


def index_tables(page: dict[str, Any]) -> list[dict[str, Any]]:
    """The tables of an index page as drawn: under each rule with a header on
    it (bold texts 1.6 mm above), ``head`` (the column names), ``title`` (the
    heading above, if any) and ``rows``, each {y, cells (per column, its texts
    in reading order; a line with nothing in the first column continues the
    row above), marks (the Kleidos ids after the row's first line)}."""
    from kicad_schematic import ADD_ID

    texts = page["texts"]

    def marker(t: dict[str, Any]) -> bool:
        return bool(t["href"] and t["bold"] and ADD_ID.fullmatch(t["body"]))

    tables = []
    for x0, x1, ry in page["rules"]:

        def within(t: dict[str, Any], lo: float = x0 - 0.1, hi: float = x1 + 0.1) -> bool:
            return bool(lo <= t["x"] <= hi)

        head = sorted(
            (t for t in texts if t["bold"] and within(t) and abs(t["y"] - (ry - 1.6)) < 0.05),
            key=lambda t: t["x"],
        )
        if not head or abs(head[0]["x"] - x0) > 0.1:
            continue
        above = [
            t
            for t in texts
            if t["bold"] and t["size"] > 1.9 and abs(t["x"] - x0) < 0.1 and t["y"] < ry - 1.7
        ]
        title = max(above, key=lambda t: t["y"])["body"] if above else ""
        end = min(
            (
                t["y"]
                for t in texts
                if t["bold"] and within(t) and t["y"] > ry + 0.1 and not marker(t)
            ),
            default=float("inf"),
        )  # the next table's heading, or the page row
        cols = [h["x"] for h in head]
        rows: list[dict[str, Any]] = []
        cells = sorted(
            (t for t in texts if within(t) and ry < t["y"] < end and not t["bold"]),
            key=lambda t: (round(t["y"], 2), t["x"]),
        )
        for t in cells:
            col = max(i for i, cx in enumerate(cols) if t["x"] >= cx - 0.05)
            if col == 0 and not (rows and abs(rows[-1]["y"] - t["y"]) < 0.05):
                rows.append({"y": t["y"], "cells": [[] for _ in cols], "marks": []})
            if rows:
                rows[-1]["cells"][col].append(t["body"])
        for t in texts:
            if marker(t) and x1 < t["x"] <= x1 + 15 and ry < t["y"] < end:
                row = next((r for r in rows if abs(r["y"] - t["y"]) < 0.05), None)
                if row:
                    row["marks"].append(t)
        tables.append({"head": [h["body"] for h in head], "title": title, "rows": rows})
    return tables


def index_pages(board: str) -> list[str]:
    """What the index pages and the title blocks say of the Kleidos additions
    and corrections, read from the KiCad files (the module's docstring): the
    wording under the heading and in every title block, each entry marked on
    every row and power-tree box that shows its element again and on no other,
    and what a GPIO table says of a pin on no net."""
    from kicad_schematic import (
        ADD_ID,
        ADD_SUBTITLE,
        NC_TEXT,
        additions_by_element,
        gpio_maps,
        index_keys,
    )

    folder = ROOT / board / "schematic"
    facts = yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8"))
    layout = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    adds = facts.get("kleidos") or []
    by_element = additions_by_element(facts, layout)
    errors: list[str] = []

    def says(text: object) -> bool:
        return ADD_SUBTITLE.lower() in str(text).lower()

    # the line under the contents page's heading, and every page's title block
    root = page_items(folder / f"{board}.kicad_sch")
    sub = str(layout["root"]["subheading"])
    drawn = [t["body"] for t in root["texts"] if t["body"].startswith(sub)]
    want = sub + (f", {ADD_SUBTITLE}" if adds else "")
    if drawn != [want]:
        errors.append(f"contents page: the line under the heading reads {drawn}, not {want!r}")
    pages = {1: root}
    for page, sh in enumerate(layout["sheets"], start=2):
        pages[page] = page_items(folder / sh["file"])
    for page, items in pages.items():
        told = [line for line in items["block"] if says(line)]
        if adds and len(told) != 1:
            errors.append(
                f'page {page}: the title block says "{ADD_SUBTITLE}" {len(told)} times, not once'
            )
        if not adds and told:
            errors.append(
                f'page {page}: the title block says "{ADD_SUBTITLE}", but netlist.yaml has none'
            )

    def held(page: int, where: str, marks: list[dict[str, Any]], keys: list[Any]) -> None:
        """The markers a row or box carries are those of the entries its elements have."""
        got = sorted(t["body"] for t in marks)
        want = sorted({by_element[k]["id"] for k in keys if k in by_element})
        errors.extend(
            f"page {page}: {eid} is not marked on {where}, which shows its element again"
            for eid in sorted(set(want) - set(got), key=lambda i: int(i[1:]))
        )
        errors.extend(
            f"page {page}: {eid} is marked on {where}, which shows none of its element"
            for eid in sorted(set(got) - set(want), key=lambda i: int(i[1:]))
        )
        if len(got) != len(set(got)):
            errors.append(f"page {page}: a marker is drawn twice on {where}")

    nets_sheet: dict[str, Any] = next(
        (sh for sh in layout["sheets"] if sh.get("index") == "nets"), {}
    )
    maps = {t["title"]: t["map"] for t in gpio_maps(facts, nets_sheet)}
    for page, sh in enumerate(layout["sheets"], start=2):
        if (
            "index" not in sh or sh["index"] == "additions"
        ):  # the contents' continuation: additions()
            continue
        items = pages[page]
        seen = []  # the markers a row or a box accounts for
        for table in index_tables(items):
            head = table["head"]
            for row in table["rows"]:

                def cell(i: int, cells: list[list[str]] = row["cells"]) -> str:
                    return " ".join(cells[i])

                if head[:3] == ["GPIO", "Pin", "Net"]:
                    kind, name, keys = (
                        "gpio",
                        cell(0),
                        index_keys(facts, "gpio", cell(0), cell(1), table["title"]),
                    )
                elif head[:2] == ["Net", "Nominal"]:
                    kind, name, keys = "nets", cell(0), index_keys(facts, "nets", cell(0))
                elif head[0] == "Rail":
                    kind, name, keys = "rails", cell(0), index_keys(facts, "rails", cell(0))
                elif head[:3] == ["Address", "Ref", "Part"]:
                    kind, name, keys = "i2c", cell(1), index_keys(facts, "i2c", cell(1))
                elif head[:4] == ["Signal", "Pull", "To", "Via"]:
                    kind, name, keys = "pulls", cell(3), index_keys(facts, "pulls", cell(3))
                elif "Kind" in head:
                    kind, name, keys = "parts", cell(0), index_keys(facts, "parts", cell(0))
                elif head[0] == "Ref":
                    kind, name, keys = (
                        "test points",
                        cell(0),
                        index_keys(facts, "test_points", cell(0)),
                    )
                else:
                    errors.append(
                        f"page {page}: a table headed {head} that the check does not know"
                    )
                    break
                where = f"the row of {name}" + (
                    f" ({table['title']})" if table["title"] else f" ({kind})"
                )
                held(page, where, row["marks"], keys)
                seen += row["marks"]
                if kind == "gpio" and "What it does" in head and cell(2) == NC_TEXT:
                    said = " ".join(cell(head.index("What it does")).split())
                    own = " ".join(
                        str(maps.get(table["title"], {}).get(name, {}).get("what") or "").split()
                    )
                    entries = [by_element[k] for k in keys if k in by_element]
                    entries_said = " ".join(
                        " ".join(str(e["what"]).split())
                        for e in sorted(entries, key=lambda e: int(str(e["id"])[1:]))
                    )
                    if said != (
                        own or entries_said
                    ):  # blank when nothing more than the Net cell can be said
                        errors.append(
                            f"page {page}: {where} is on no net and says {said!r} under "
                            f'"What it does", not {(own or entries_said)!r}'
                        )
        if sh["index"] == "power":  # the power tree: a box is a rectangle with a linked first line
            for x0, y0, x1, y1 in items["rects"]:
                inside = sorted(
                    (t for t in items["texts"] if x0 <= t["x"] <= x1 and y0 <= t["y"] <= y1),
                    key=lambda t: t["y"],
                )
                if not inside or not inside[0]["href"]:
                    continue
                name = inside[0]["body"].split()[0]
                marks = [
                    t
                    for t in items["texts"]
                    if t["href"]
                    and ADD_ID.fullmatch(t["body"])
                    and x0 <= t["x"] <= x1 + 0.5
                    and y0 - 3.0 <= t["y"] < y0
                ]
                held(
                    page, f"the power tree's box of {name}", marks, index_keys(facts, "tree", name)
                )
                seen += marks
        errors.extend(
            f"page {page}: {t['body']} at ({t['x']:.1f}, {t['y']:.1f}) mm marks no row and no box"
            for t in items["texts"]
            if t["href"]
            and t["bold"]
            and ADD_ID.fullmatch(t["body"])
            and not any(t is s for s in seen)
        )
    return errors


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("board")
    ap.add_argument("--netlist", type=Path)
    args = ap.parse_args(argv)
    try:
        board = board_id(args.board)
        xml = export(board) if args.netlist is None else work_path(args.netlist)
    except OutsideError as exc:
        ap.error(str(exc))
    errors = compare(board, xml) + additions(board) + index_pages(board)
    for e in errors:
        print(f"FAIL {e}")
    if not errors:
        n = len(
            yaml.safe_load((ROOT / board / "schematic" / "netlist.yaml").read_text())["components"]
        )
        print(f"ok   {board}: the drawing matches netlist.yaml, {n} components, pin for pin")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
