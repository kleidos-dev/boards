# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Hold every link of a board's schematic PDF to the place it should lead to.

The PDF ``export_schematic.py`` writes is meant to be read on a screen and
followed by clicking. This check reads the KiCad files to learn what is drawn
where (texts, net labels, each part's reference, the index tables' rules), then
reads the PDF (with ``pypdf``) and fails unless:

- every sheet's box on the contents page leads to that sheet's page, and the
  "Contents" and page row on every page lead to the page they name (none to
  its own), so every page links back to the contents and to every other page;
- every ``[page/zone]`` after a net label lands, on that page, within
  ``LAND`` mm of a label of the same net, and that label sits in the zone the
  text prints. A link's landing point is where its ``/XYZ`` destination puts
  the target: ``VIEW_LEFT`` mm right of the window's left edge and
  ``VIEW_TOP`` mm below its top (``kicad_schematic.py``);
- every place in an index page (a ``page/zone`` in a table, a reference or a
  net a table or the power tree names) lands on what its row names: a ``page/
  zone`` on the part or net in its row's first cell that names one (its row:
  the texts at its height between the ends of the table's rule; a wrapped line
  belongs to the row above), any other linked text on the part or net its
  first word names, the zone again the one printed;
- every part's reference on the drawing is a link to its row in the parts
  list, and that row's reference leads back to the part;
- every link says what it leads to (``/Contents``), and no link does
  anything else: no script, no web address, none over nothing drawn;
- the document holds no script at all (no ``/JavaScript`` name tree, no
  ``/JS``, no open action);
- the bookmarks hold one entry per page and, under each drawing page, one per
  part on it, landing on its reference; every part has a named destination
  ``part-<ref>``, and each ``net-<net>-p<page>`` lands on a label of that net;
- every Kleidos addition or correction (``kleidos`` in ``netlist.yaml``) has
  a linked row on the contents page that lands on a marker of its id, and at
  least one marker ("K3") that lands back on that row; each marker sits beside
  the element its entry names (on the line of the net's label or the part's
  reference, by the ground or not-connected flag of a pin; on an index page,
  on a row that names the element or above its box of the power tree, where
  ``check_schematic.py`` holds which rows and boxes), its named destination
  ``add-K<n>`` lands on a marker, and its source is not empty; no marker or
  row names an entry the netlist lacks.

Usage::

    python3 _shared/check_schematic_links.py <board> [--pdf FILE] [--list]

``--list`` prints every link of every page with where it lands. Exit status 0
when every link is right.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_schematic import (
    LABEL_CHAR_W,
    LABEL_PAD,
    PAPER,
    REF_CHAR_W,
    VIEW_LEFT,
    VIEW_TOP,
    chip_of,
    gpio_maps,
    parse,
    zone,
)
from paths import ROOT, OutsideError, board_id, work_path

PT = 72 / 25.4
SLACK = 0.6  # mm a link's box may miss its text's anchor by
LAND = 5.0  # mm a link may land from its target
TOKEN = re.compile(r"^\[?(\d+)/([A-Z]\d+)\]?$")
NAV = re.compile(r"^\[(\d+)\]$")


#: The ground symbols of this project's library (``kicad_schematic.generic_symbol``).
GROUND_SYMBOLS = ("kleidos:GND", "kleidos:GNDA", "kleidos:GNDREF")


def child(node: list[Any], key: str) -> list[Any] | None:
    return next((x for x in node if isinstance(x, list) and x and x[0] == key), None)


def need(node: list[Any], key: str) -> list[Any]:
    """The child ``(key ...)`` of a node, which a KiCad file always writes there."""
    found = child(node, key)
    if found is None:
        raise ValueError(f"a ({node[0] if node else '?'} ...) node with no ({key} ...)")
    return found


def read_sheets(board: str) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    """page -> what is drawn on it; and the board's facts."""
    folder = ROOT / board / "schematic"
    layout = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    facts = yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8"))
    files = {1: (f"{board}.kicad_sch", layout["root"]["title"], None)}
    for page, sh in enumerate(layout["sheets"], start=2):
        files[page] = (sh["file"], sh["name"], sh.get("index"))
    pages = {}
    for page, (name, title, index) in files.items():
        doc = parse((folder / name).read_text(encoding="utf-8"))
        info = {
            "name": title,
            "index": index,
            "texts": [],
            "labels": [],
            "fields": [],
            "boxes": [],
            "rules": [],
            "ncs": [],
            "powers": [],
        }
        for item in doc:
            if not isinstance(item, list) or not item:
                continue
            if item[0] == "text":
                pos, eff = need(item, "at"), child(item, "effects")
                href = child(eff, "href") if eff else None
                info["texts"].append(
                    {
                        "body": str(item[1]),
                        "x": float(pos[1]),
                        "y": float(pos[2]),
                        "href": str(href[1]) if href else None,
                    }
                )
            elif item[0] == "global_label":
                pos = need(item, "at")
                lw = (
                    len(str(item[1])) * LABEL_CHAR_W + LABEL_PAD
                )  # the box KiCad draws round the name
                x, a = float(pos[1]), int(float(pos[3])) if len(pos) > 3 else 0
                info["labels"].append(
                    {
                        "net": str(item[1]),
                        "x": x,
                        "y": float(pos[2]),
                        "span": (x, x + lw) if a == 0 else (x - lw, x),
                        "angle": a,
                    }
                )
            elif item[0] == "symbol":
                for f in item:
                    if (
                        isinstance(f, list)
                        and f[:2] == ["property", "Reference"]
                        and not str(f[2]).startswith("#")
                    ):
                        pos = need(f, "at")
                        info["fields"].append(
                            {"ref": str(f[2]), "x": float(pos[1]), "y": float(pos[2])}
                        )
                if str(need(item, "lib_id")[1]) in GROUND_SYMBOLS:  # a ground: its net and place
                    pos = need(item, "at")
                    value = next(
                        str(f[2])
                        for f in item
                        if isinstance(f, list) and f[:2] == ["property", "Value"]
                    )
                    info["powers"].append((value, float(pos[1]), float(pos[2])))
            elif item[0] == "no_connect":
                pos = need(item, "at")
                info["ncs"].append((float(pos[1]), float(pos[2])))
            elif item[0] == "polyline":
                pts = need(item, "pts")[1:]
                if len(pts) == 2 and abs(float(pts[0][2]) - float(pts[1][2])) < 1e-6:
                    info["rules"].append(
                        (
                            min(float(pts[0][1]), float(pts[1][1])),
                            max(float(pts[0][1]), float(pts[1][1])),
                            float(pts[0][2]),
                        )
                    )
            elif item[0] == "sheet":
                pos, size = need(item, "at"), need(item, "size")
                sname = next(
                    str(f[2])
                    for f in item
                    if isinstance(f, list) and f[:2] == ["property", "Sheetname"]
                )
                target = next(p for p, v in files.items() if v[1] == sname)
                x, y, w, h = float(pos[1]), float(pos[2]), float(size[1]), float(size[2])
                info["boxes"].append(
                    {"label": sname, "box": (x, y, x + w, y + h), "target": target}
                )
        pages[page] = info
    return pages, facts


def _page_number(reader: Any, destination: Any) -> int:
    """The page (from 1) a bookmark or a named destination leads to."""
    number = reader.get_destination_page_number(destination)
    if number is None:
        raise ValueError(f"a destination that leads to no page: {destination!r}")
    return int(number) + 1


def pdf_read(
    pdf: Path,
) -> tuple[
    dict[int, list[dict[str, Any]]],
    list[dict[str, Any]],
    dict[str, Any],
    list[str],
    tuple[float, float],
]:
    """The PDF's links per page, bookmarks, named destinations, scripts, page size."""
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError
    from pypdf.generic import DictionaryObject

    reader = PdfReader(pdf)
    index = {
        p.indirect_reference.idnum: i
        for i, p in enumerate(reader.pages, start=1)
        if p.indirect_reference is not None
    }
    height = float(reader.pages[0].mediabox.height)

    def where(dest: Any) -> tuple[int | None, str, float | None, float | None] | None:
        """(page, kind, landing x, landing y) of an explicit destination array."""
        if not (isinstance(dest, list) and dest and hasattr(dest[0], "idnum")):
            return None
        page = index.get(dest[0].idnum)
        kind = str(dest[1]) if len(dest) > 1 else ""
        if kind == "/XYZ" and len(dest) >= 4 and dest[2] is not None and dest[3] is not None:
            return (
                page,
                kind,
                float(dest[2]) / PT + VIEW_LEFT,
                (height - float(dest[3])) / PT + VIEW_TOP,
            )
        return page, kind, None, None

    out: dict[int, list[Any]] = {}
    for i, page in enumerate(reader.pages, start=1):
        links = []
        for ref in page.get("/Annots") or []:
            a = ref.get_object()
            if a.get("/Subtype") != "/Link":
                continue
            x0, y0, x1, y1 = (float(v) for v in a["/Rect"])
            rect = (
                min(x0, x1) / PT,
                (height - max(y0, y1)) / PT,
                max(x0, x1) / PT,
                (height - min(y0, y1)) / PT,
            )
            dest, act, other = a.get("/Dest"), a.get("/A"), None
            if act is not None:
                act = act.get_object()
                if act.get("/S") == "/GoTo":
                    dest = act.get("/D")
                else:
                    other = f"{act.get('/S')} {str(act.get('/JS') or act.get('/URI') or '')[:60]!r}"
            w = where(dest) if other is None else None
            links.append(
                {
                    "rect": rect,
                    "to": w,
                    "other": other or (None if w else f"destination {dest!r}"),
                    "contents": str(a.get("/Contents") or ""),
                }
            )
        out[i] = links
    outline = []

    def walk(items: list[Any], depth: int, parent: str | None = None) -> None:
        last = parent
        for it in items:
            if isinstance(it, list):
                walk(it, depth + 1, last)
                continue
            last = str(it.title)
            page = _page_number(reader, it)
            land = None
            if str(it.typ) == "/XYZ" and it.left is not None and it.top is not None:
                land = (float(it.left) / PT + VIEW_LEFT, (height - float(it.top)) / PT + VIEW_TOP)
            outline.append(
                {
                    "depth": depth,
                    "title": str(it.title),
                    "page": page,
                    "land": land,
                    "parent": parent,
                }
            )

    walk(reader.outline, 0)
    marks = {}
    for name, d in reader.named_destinations.items():
        land = None
        if str(d.typ) == "/XYZ" and d.left is not None and d.top is not None:
            land = (float(d.left) / PT + VIEW_LEFT, (height - float(d.top)) / PT + VIEW_TOP)
        marks[str(name)] = (_page_number(reader, d), land)
    scripts = []
    root = reader.trailer["/Root"].get_object()
    if not isinstance(root, DictionaryObject):
        raise ValueError(f"{pdf}: the catalog is not a dictionary")
    names = root.get("/Names")
    if names is not None and "/JavaScript" in names.get_object():
        scripts.append("the catalog's /Names holds a /JavaScript tree")
    if "/OpenAction" in root or "/AA" in root:
        scripts.append("the catalog has an open action")
    for num in range(1, int(str(reader.trailer["/Size"]))):
        try:
            obj = reader.get_object(num)
        except PyPdfError, ValueError, KeyError:  # a free or unreadable object holds nothing
            continue
        if isinstance(obj, DictionaryObject) and ("/JS" in obj or obj.get("/S") == "/JavaScript"):
            scripts.append(f"object {num} is a script ({str(obj.get('/JS') or '')[:40]!r})")
    size = (float(reader.pages[0].mediabox.width) / PT, height / PT)
    return out, outline, marks, scripts, size


def inside(rect: Sequence[float], x: float, y: float, slack: float = SLACK) -> bool:
    return rect[0] - slack <= x <= rect[2] + slack and rect[1] - slack <= y <= rect[3] + slack


def check(board: str, pdf: Path) -> tuple[list[str], list[str]]:
    """The errors, and one line per link (page, box, what it is, where it lands)."""
    pages, facts = read_sheets(board)
    got, outline, marks, scripts, size = pdf_read(pdf)
    layout = yaml.safe_load(
        (ROOT / board / "schematic" / "layout.yaml").read_text(encoding="utf-8")
    )
    paper = layout.get("paper", "A3")
    refs = set(facts["components"])
    nets = {lab["net"] for p in pages.values() for lab in p["labels"]}
    adds = {
        str(e["id"]): e for e in facts.get("kleidos") or [] if isinstance(e, dict) and "id" in e
    }
    parts_page = next((p for p, v in pages.items() if v["index"] == "parts"), None)
    errors, lines = [], []
    W, H = PAPER[paper]
    if abs(size[0] - W) > 1 or abs(size[1] - H) > 1:
        errors.append(
            f"the PDF's pages are {size[0]:.0f} x {size[1]:.0f} mm, not {W:.0f} x {H:.0f}"
        )
    if sorted(got) != sorted(pages):
        errors.append(f"the PDF has {len(got)} pages, the schematic {len(pages)}")
    errors += [f"script: {s}" for s in scripts]

    def targets(subject: str, page: int) -> list[tuple[float, float]]:
        """The places on ``page`` a link about ``subject`` may land on."""
        p = pages.get(page)
        if not p:
            return []
        if subject in adds:  # a Kleidos addition: its row on a contents page, its markers elsewhere
            return [(t["x"], t["y"]) for t in p["texts"] if t["body"] == subject and t["href"]]
        if subject in refs:
            return [(f["x"], f["y"]) for f in p["fields"] if f["ref"] == subject]
        return [(lab["x"], lab["y"]) for lab in p["labels"] if lab["net"] == subject]

    def row_subject(page: int, t: dict[str, Any]) -> str | None:
        """The part or net a table row is about: its first cell that names one."""
        p = pages[page]
        if p["index"] is None:  # on the drawing: the label its run of tokens follows
            line = sorted(
                (c for c in p["texts"] if TOKEN.match(c["body"]) and abs(c["y"] - t["y"]) < 0.2),
                key=lambda c: c["x"],
            )
            k = line.index(t)
            lo = hi = k
            while (
                lo > 0
                and line[lo]["x"] - (line[lo - 1]["x"] + len(line[lo - 1]["body"]) * REF_CHAR_W)
                < 1.6
            ):
                lo -= 1
            while (
                hi < len(line) - 1
                and line[hi + 1]["x"] - (line[hi]["x"] + len(line[hi]["body"]) * REF_CHAR_W) < 1.6
            ):
                hi += 1
            run = line[lo : hi + 1]
            x0, x1 = run[0]["x"], run[-1]["x"] + len(run[-1]["body"]) * REF_CHAR_W
            best = None
            for lab in p["labels"]:
                if abs(lab["y"] - t["y"]) >= 0.2:
                    continue
                gap = x0 - lab["span"][1] if lab["angle"] == 0 else lab["span"][0] - x1
                if -1.0 <= gap <= 4.0 and (best is None or abs(gap - 1.2) < best[0]):
                    best = (abs(gap - 1.2), lab["net"])
            return best[1] if best else None
        above = [r for r in p["rules"] if r[0] - 0.1 <= t["x"] <= r[1] + 0.1 and r[2] < t["y"]]
        if not above:
            return None
        x0, x1, _ = max(above, key=lambda r: r[2])
        cells = [
            c
            for c in p["texts"]
            if x0 - 0.1 <= c["x"] < t["x"]
            and c["y"] <= t["y"] + 0.2
            and (c["body"] in refs or c["body"] in nets)
        ]
        if not cells:
            return None
        y = max(c["y"] for c in cells)
        return str(min((c for c in cells if abs(c["y"] - y) < 0.2), key=lambda c: c["x"])["body"])

    def judge(
        page: int,
        what: str,
        link: dict[str, Any],
        target_page: int,
        subject: str | None,
        printed_zone: str | None = None,
    ) -> str | None:
        """None when ``link`` lands on ``subject`` on ``target_page``, else what is wrong."""
        if link["other"]:
            return f"does {link['other']}"
        tp, kind, lx, ly = link["to"]
        if tp != target_page:
            return f"leads to page {tp}, not {target_page}"
        if lx is None:
            return f"leads to the whole page ({kind}), not to {subject}"
        cands = targets(subject, tp) if subject else []
        if not cands:
            return f"names {subject!r}, which page {tp} does not draw"
        best = min(cands, key=lambda c: math.hypot(c[0] - lx, c[1] - ly))
        dist = math.hypot(best[0] - lx, best[1] - ly)
        if dist > LAND:
            return f"lands {dist:.1f} mm from the nearest {subject} on page {tp}"
        if printed_zone and zone(*best, paper) != printed_zone:
            return f"prints zone {printed_zone}, but {subject} there is in {zone(*best, paper)}"
        return None

    for page in sorted(got):
        links = got[page]
        used = [False] * len(links)
        reach: set[int] = set()
        p = pages.get(page, {"texts": [], "boxes": [], "fields": []})

        def hits_at(x: float, y: float, links: list[dict[str, Any]] = links) -> list[int]:
            return [k for k, lk in enumerate(links) if inside(lk["rect"], x, y)]

        def note(
            k: int,
            kind: str,
            label: str,
            verdict: str | None,
            links: list[dict[str, Any]] = links,
            used: list[bool] = used,
            reach: set[int] = reach,
            page: int = page,
        ) -> None:
            lk = links[k]
            used[k] = True
            r = lk["rect"]
            to = lk["to"]
            dest = (
                f"page {to[0]}"
                + (f" at {zone(to[2], to[3], paper)}" if to and to[2] is not None else "")
                if to
                else lk["other"]
            )
            if not lk["contents"]:
                errors.append(f"page {page}: {kind} {label!r} has no /Contents (what it leads to)")
            if verdict:
                errors.append(f"page {page}: {kind} {label!r} {verdict}")
            lines.append(
                f"p{page}  [{r[0]:6.1f} {r[1]:6.1f} {r[2]:6.1f} {r[3]:6.1f}] mm  {kind:5} "
                f"{label!r:28} -> {dest}  {'WRONG' if verdict else 'ok'}"
            )
            if to:
                reach.add(to[0])

        for t in p["texts"]:
            if not t["href"]:
                continue
            target = int(t["href"].lstrip("#"))
            hits = hits_at(t["x"] + 0.3, t["y"])
            if not hits:
                errors.append(
                    f"page {page}: text {t['body']!r} at ({t['x']:.1f}, {t['y']:.1f}) mm has no "
                    "link"
                )
                continue
            if target == page:
                errors.append(f"page {page}: text {t['body']!r} links to its own page")
            m = TOKEN.match(t["body"])
            for k in hits:
                lk = links[k]
                if NAV.match(t["body"]) or t["body"] == "Contents":
                    ok = lk["to"] and lk["to"][0] == target and not lk["other"]
                    note(
                        k,
                        "page",
                        t["body"],
                        None if ok else f"leads to {lk['to'] or lk['other']}, not page {target}",
                    )
                elif m:
                    if int(m.group(1)) != target:
                        errors.append(
                            f"page {page}: {t['body']!r} prints page {m.group(1)} but links to "
                            f"{target}"
                        )
                    subject = row_subject(page, t)
                    note(
                        k,
                        "place",
                        f"{t['body']} {subject}",
                        judge(page, "place", lk, target, subject, m.group(2)),
                    )
                else:
                    subject = t["body"].split()[0]
                    note(k, "place", t["body"], judge(page, "place", lk, target, subject))
        for b in p["boxes"]:
            bx0, by0, bx1, by1 = b["box"]
            hits = [
                k
                for k in hits_at((bx0 + bx1) / 2, (by0 + by1) / 2)
                if inside(links[k]["rect"], bx0, by0, 1.0)
                and inside(links[k]["rect"], bx1, by1, 1.0)
            ]
            if not hits:
                errors.append(
                    f"page {page}: sheet {b['label']!r} has no link (it should lead to page "
                    f"{b['target']})"
                )
            for k in hits:
                lk = links[k]
                ok = lk["to"] and lk["to"][0] == b["target"]
                note(
                    k,
                    "sheet",
                    b["label"],
                    None if ok else f"leads to {lk['to'] or lk['other']}, not page {b['target']}",
                )
        for f in p["fields"]:
            hits = [k for k in hits_at(f["x"], f["y"]) if not used[k]]
            if parts_page is None:
                continue
            if not hits:
                errors.append(
                    f"page {page}: the reference {f['ref']} has no link to the parts list"
                )
                continue
            for k in hits:
                lk = links[k]
                if lk["other"]:
                    verdict: str | None = f"does {lk['other']}"
                elif lk["to"][0] != parts_page:
                    verdict = (
                        f"leads to page {lk['to'][0]}, not to the parts list (page {parts_page})"
                    )
                elif lk["to"][2] is None:
                    verdict = "leads to the whole parts list, not to its row"
                else:
                    rows = [
                        (c["x"], c["y"])
                        for c in pages[parts_page]["texts"]
                        if c["body"] == f["ref"]
                    ]
                    best = min(
                        (math.hypot(x - lk["to"][2], y - lk["to"][3]) for x, y in rows),
                        default=math.inf,
                    )
                    verdict = (
                        None
                        if best <= LAND
                        else f"lands {best:.1f} mm from its row in the parts list"
                    )
                note(k, "ref", f["ref"], verdict)
        for k, lk in enumerate(links):
            if not used[k]:
                r = lk["rect"]
                errors.append(
                    f"page {page}: a link at [{r[0]:.1f} {r[1]:.1f} {r[2]:.1f} {r[3]:.1f}] mm "
                    f"that matches nothing drawn, leading to {lk['to'] or lk['other']}"
                )
                lines.append(
                    f"p{page}  [{r[0]:6.1f} {r[1]:6.1f} {r[2]:6.1f} {r[3]:6.1f}] mm  ?     "
                    f"{'(nothing drawn)':28} -> {lk['to'] or lk['other']}  STRAY"
                )
        missing = set(pages) - {page} - reach
        if missing:
            errors.append(f"page {page}: no link to page(s) {sorted(missing)}")

    # every part's row in the parts list leads back to it
    if parts_page:
        listed = {t["body"] for t in pages[parts_page]["texts"] if t["href"] and t["body"] in refs}
        for ref in sorted(refs - listed):
            errors.append(f"parts list: no linked row for {ref}")

    # the Kleidos additions and corrections: a row on page 1 for each, every
    # marker beside the element its entry names (the links both ways are held
    # above: a marker lands on its row, a row on a marker of its id)
    grounds = set(layout.get("grounds") or {})
    comps = facts["components"]
    gpio_tables = gpio_maps(
        facts, next((sh for sh in layout["sheets"] if sh.get("index") == "nets"), {})
    )

    def beside(e: dict[str, Any], page: int, t: dict[str, Any]) -> str | None:
        """None when the marker ``t`` sits beside the element entry ``e`` names, else what it sits
        by."""
        el = e.get("element") or {}
        kind = next(
            (k for k in ("pin", "part", "net", "gpio", "i2c", "pull", "rail") if k in el), None
        )
        val, p = str(el.get(kind, "")), pages[page]

        def line(y: float, at: float = t["y"]) -> bool:
            return abs(y - at) < 0.3

        if p["index"] is not None:
            # an index page: on a row that names the element (a pin's: its part, or its GPIO in its
            # chip's table), or just above the power-tree box whose first line names it
            names = {val}
            if kind == "pin":
                ref, _, pin = val.partition(".")
                names = {ref} | {
                    str(g)
                    for tb in gpio_tables
                    if chip_of(tb["title"]) == ref
                    for g, v in tb["map"].items()
                    if str(v["pin"]) == pin
                }
            ok = any(
                c["body"] in names and line(c["y"]) and c["x"] < t["x"] for c in p["texts"]
            ) or any(
                c["href"]
                and c["body"].split()[:1] == [val]
                and 0 < c["y"] - t["y"] < 6
                and -2 < t["x"] - c["x"] < 40
                for c in p["texts"]
            )
            return None if ok else f"not on a row or a power-tree box of {kind} {val}"
        if kind == "pin":
            ref, _, pin = val.partition(".")
            kind, val = "net", str(comps.get(ref, {}).get("pins", {}).get(pin, ""))
            if val == "NC":
                ok = any(math.hypot(x - t["x"], y - t["y"]) < 12 for x, y in p["ncs"])
                return None if ok else f"no not-connected pin near it ({val})"
            if val in grounds:
                ok = any(
                    n == val and math.hypot(x - t["x"], y - t["y"]) < 12 for n, x, y in p["powers"]
                )
                return None if ok else f"no {val} symbol near it"
        if kind == "net":
            ok = any(
                lab["net"] == val and line(lab["y"]) and abs(t["x"] - lab["x"]) < 80
                for lab in p["labels"]
            )
            return None if ok else f"no label of {val} on its line"
        if kind == "part":
            ok = any(
                f["ref"] == val and line(f["y"]) and 0 < t["x"] - f["x"] < 30 for f in p["fields"]
            )
            return None if ok else f"not after the reference {val}"
        return f"a {kind} is marked on an index page, and this is a drawing page"

    contents = {pg for pg, info in pages.items() if pg == 1 or info["index"] == "additions"}
    for eid, e in sorted(adds.items(), key=lambda kv: int(kv[0][1:]) if kv[0][1:].isdigit() else 0):
        if not any(t["body"] == eid and t["href"] for pg in contents for t in pages[pg]["texts"]):
            errors.append(f"kleidos {eid}: no linked row in the contents page's table")
        drawn_at = [
            (pg, t)
            for pg, info in pages.items()
            if pg not in contents
            for t in info["texts"]
            if t["body"] == eid and t["href"]
        ]
        if not drawn_at:
            errors.append(f"kleidos {eid}: no marker on the drawing")
        for pg, t in drawn_at:
            why = beside(e, pg, t)
            if why:
                errors.append(
                    f"page {pg}: marker {eid} at ({t['x']:.1f}, {t['y']:.1f}) mm is not beside its "
                    f"element: {why}"
                )
        m = marks.get(f"add-{eid}")
        if (
            m is None
            or m[1] is None
            or not targets(eid, m[0])
            or m[0] in contents
            or min(math.hypot(x - m[1][0], y - m[1][1]) for x, y in targets(eid, m[0])) > LAND
        ):
            errors.append(f"named destination add-{eid}: missing, or not on a marker of {eid}")
        given = e.get("source")
        src: dict[str, Any] = given if isinstance(given, dict) else {}
        if not str(src.get("cite") or "").strip() or not str(src.get("type") or "").strip():
            errors.append(f"kleidos {eid}: its source is empty")
    for pg, info in pages.items():
        for t in info["texts"]:
            if (
                t["href"]
                and re.fullmatch(r"K[1-9]\d*", t["body"])
                and t["body"] not in adds
                and t["body"] not in refs
            ):
                errors.append(
                    f"page {pg}: {t['body']} is marked, but netlist.yaml has no such entry"
                )

    # bookmarks and named destinations
    for page, info in pages.items():
        top = [
            o
            for o in outline
            if o["depth"] == 0 and o["title"].startswith(f"{info['name']} (Page {page})")
        ]
        if not top:
            errors.append(f"bookmarks: no entry for {info['name']!r}")
            continue
        if top[0]["page"] != page:
            errors.append(f"bookmarks: {info['name']!r} leads to page {top[0]['page']}, not {page}")
        lines.append(f"bookmark  {top[0]['title']!r} -> page {page}  ok")
    drawn = {f["ref"]: (pg, f["x"], f["y"]) for pg, info in pages.items() for f in info["fields"]}
    drawing_titles = {
        f"{info['name']} (Page {pg})" for pg, info in pages.items() if info["index"] is None
    }
    kids = {
        o["title"].split()[0]: o
        for o in outline
        if o["depth"] == 1 and o["parent"] in drawing_titles
    }
    for ref, (pg, _x, _y) in sorted(drawn.items()):
        o = kids.get(ref)
        if o is None:
            errors.append(f"bookmarks: no entry for {ref} under its page")
        elif (
            o["page"] != pg
            or o["land"] is None
            or min(math.hypot(fx - o["land"][0], fy - o["land"][1]) for fx, fy in targets(ref, pg))
            > LAND
        ):
            errors.append(f"bookmarks: {ref} does not land on its reference (page {o['page']})")
    for ref in sorted(refs):
        m = marks.get(f"part-{ref}")
        if (
            m is None
            or m[1] is None
            or not targets(ref, m[0])
            or min(math.hypot(fx - m[1][0], fy - m[1][1]) for fx, fy in targets(ref, m[0])) > LAND
        ):
            errors.append(f"named destination part-{ref}: missing, or not on its reference")
    for name, (pg, land) in sorted(marks.items()):
        mm = re.fullmatch(r"net-(.+)-p(\d+)", name)
        if mm:
            cands = targets(mm.group(1), int(mm.group(2)))
            if (
                pg != int(mm.group(2))
                or land is None
                or not cands
                or min(math.hypot(x - land[0], y - land[1]) for x, y in cands) > LAND
            ):
                errors.append(f"named destination {name}: not on a label of that net")
    lines.append(f"named destinations {len(marks)}")
    return errors, lines


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("board")
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--list", action="store_true", help="print every link and where it lands")
    args = ap.parse_args(argv)
    try:
        board = board_id(args.board)
        pdf = (
            ROOT / board / "schematic" / f"{board}.pdf" if args.pdf is None else work_path(args.pdf)
        )
    except OutsideError as exc:
        ap.error(str(exc))
    errors, lines = check(board, pdf)
    if args.list:
        print("\n".join(lines))
    per_page: dict[str, int] = {}
    for line in lines:
        if re.match(r"p\d+ ", line):
            per_page[line.split()[0]] = per_page.get(line.split()[0], 0) + 1
    marks = sum(1 for line in lines if line.startswith("bookmark"))
    counts = ", ".join(
        f"{k} {v}" for k, v in sorted(per_page.items(), key=lambda kv: int(kv[0][1:]))
    )
    print(f"links: {counts}; page bookmarks {marks}")
    for e in errors[:200]:
        print(f"FAIL {e}")
    if len(errors) > 200:
        print(f"FAIL ... and {len(errors) - 200} more")
    if not errors:
        print(
            f"ok   {board}: every link of {pdf.name} lands where it should, and it holds no script"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
