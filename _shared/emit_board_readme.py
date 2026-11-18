# SPDX-License-Identifier: MIT
"""Write each ``<board>/README.md`` from its ``board.json``, one layout for all.

A board's page is a reading of its specification and nothing else: the
dimensions, every component grouped by what it does, every wiring fact, what
the board does not have, the notes, and the sources each value cites by
number, then what the folder holds. Change ``board.json`` and run this; never
edit the page by hand. ``tests/test_board_readme.py`` fails when a committed
page differs from what this writes.

Usage::

    python3 _shared/emit_board_readme.py [BOARD ...]          # write the pages
    python3 _shared/emit_board_readme.py --check [BOARD ...]  # exit 1 if any differs

Without a board it does every folder that holds a ``board.json``.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: The component tables, in page order: a heading and the roles it gathers.
#: Every role of ``_shared/board.schema.json`` is in exactly one group.
GROUPS = [
    ("Processing and memory", ["soc", "flash", "psram", "crystal"]),
    ("Power", ["pmic", "charger", "fuel_gauge", "regulator", "battery"]),
    ("Display and touch", ["display_panel", "display_controller", "touch_controller"]),
    ("Sensors and timekeeping", ["imu", "magnetometer", "rtc"]),
    ("Audio", ["audio_codec", "microphone", "audio_amp", "speaker", "buzzer"]),
    ("Input and indicators", ["button", "keyboard_controller", "io_expander", "led", "ir_led"]),
    ("Radio and positioning", ["antenna", "lora", "gps"]),
    ("Connectors, storage and USB", ["connector", "sd_slot", "usb_uart_bridge"]),
    ("Protection", ["esd"]),
    ("Other parts", ["other"]),
]

#: How tall the front drawing is shown at the top of a page, in CSS pixels: tall
#: enough that its legends read on GitHub, its width following its viewBox.
FRONT_HEIGHT_PX = 320

KINDS = {"vendor_docs": "vendor docs", "datasheet": "datasheet", "schematic": "schematic",
         "product_page": "product page", "measured": "measured", "teardown": "teardown"}

#: What a board folder may hold beside board.json, in the order the page lists
#: it, each with what it is. ``{b}`` is the board's folder name.
FOLDER = [
    ("board.json", "every part on the board, each value with its source "
                   "([`_shared/board.schema.json`](../_shared/board.schema.json)); this page is written from it"),
    ("measurements.json", "the case, display, button and keyboard geometry the front is drawn against "
                          "([`_shared/schema.md`](../_shared/schema.md))"),
    ("sources.md", "the vendor drawings, photos and CAD files the measurements were taken on"),
    ("icon.svg", "a 64 px pictogram of the board"),
    ("svg/front.svg", "the front at 1 unit = 1 mm: the screen's active area, a press target for every "
                      "control and each printed legend as a group of its own"),
    ("svg/back.svg", "the back, seen from behind, with what it prints"),
    ("svg/top.svg", "the top face and what it prints"),
    ("svg/left.svg", "the left face and what it prints"),
    ("svg/right.svg", "the right face and what it prints"),
    ("svg/bottom.svg", "the bottom face and what it prints"),
    ("model/{b}.glb", "the 3D model, glTF 2.0 binary in metres (glTF's unit), every print kept: the format "
                      "for the web and most viewers"),
    ("model/{b}-web.glb", "its web level of detail"),
    ("model/{b}.obj", "the same model as Wavefront OBJ, in millimetres, Y up, one object per part: the format "
                      "for most other 3D tools (Blender, FreeCAD, Fusion, MeshLab, slicers); "
                      "written from the master by [`_shared/export_obj.py`](../_shared/export_obj.py)"),
    ("model/{b}.mtl", "the OBJ's materials: each part's colour, transparency, roughness and metalness"),
    ("model/spec.json", "the recipe both are built from"),
    ("model/source.json", "the master's provenance"),
    ("model/web.json", "the web level's record"),
    ("schematic/{b}.pdf", "the connectivity schematic, made to be followed by clicking"),
    ("schematic/README.md", "the schematic's sources, its Kleidos additions and corrections, and its open questions"),
    ("schematic/netlist.yaml", "every part, pin and net of the schematic with its source"),
    ("schematic/improvements.md", "the triage behind the additions and corrections"),
    ("schematic/bench/", "the bench probe records"),
]


def cell(text) -> str:
    """A value fit for one Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def fmt_value(value) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:g}"
    if isinstance(value, list):
        return " / ".join(fmt_value(v) for v in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}: {fmt_value(v)}" for k, v in value.items())
    return str(value)


def fmt_number(value, unit: str) -> str:
    return f"{value:.1f} {unit}" if isinstance(value, (int, float)) else f"{value} {unit}"


def ohms(value) -> str:
    if value >= 1_000_000 and value % 1_000_000 == 0:
        return f"{value // 1_000_000:g}M"
    if value >= 1000:
        return f"{value / 1000:g}k"
    return f"{value:g}"


def label(role: str) -> str:
    return role.replace("_", " ")


class Page:
    def __init__(self, board: str, data: dict):
        self.board = board
        self.data = data
        self.comps = data["components"]
        self.by_id = {c["id"]: c for c in self.comps}
        self.numbers = {sid: n for n, sid in enumerate(data["sources"], start=1)}

    def src(self, ids) -> str:
        return " ".join(f"[{self.numbers[i]}]" for i in ids or [])

    def name(self, cid: str) -> str:
        """How a connection names a component: its part number, else its
        role and reference, else its id."""
        if cid == "external":
            return "external"
        c = self.by_id[cid]
        if c.get("part"):
            return c["part"]
        if c.get("designator"):
            return f"{label(c['role'])} {c['designator']}"
        return label(c["role"]) if sum(1 for o in self.comps if o["role"] == c["role"]) == 1 else cid

    def pictures(self) -> str:
        """The icon, and beside it the front drawing linked to the file, sized to read."""
        name = self.data["identity"]["name"]
        out = f'<img src="icon.svg" width="96" height="96" alt="{name} icon">'
        front = ROOT / self.board / "svg" / "front.svg"
        if front.is_file():
            box = re.search(r'<svg\b[^>]*\bviewBox="([^"]+)"', front.read_text(encoding="utf-8"))
            _x, _y, w, h = (float(v) for v in box.group(1).split())
            width = round(FRONT_HEIGHT_PX * w / h)
            out += (f' <a href="svg/front.svg"><img src="svg/front.svg" width="{width}" '
                    f'height="{FRONT_HEIGHT_PX}" alt="{name} front drawing, true to scale: the case, '
                    f'the screen, the controls and the printed legends"></a>')
        return out

    def lines(self) -> list[str]:
        d, ident = self.data, self.data["identity"]
        out = [self.pictures(), "", f'# {ident["name"]}', ""]
        head = f'{ident["vendor"]} · SKU **{ident["sku"]}**'
        if ident.get("revision"):
            head += f' · revision {ident["revision"]}'
        if ident.get("aka"):
            head += " · also sold as " + ", ".join(ident["aka"])
        out += [head + f' {self.src(ident["src"])}', ""]
        out += ["Every value below comes from [`board.json`](board.json), where each one carries the id of its "
                "source; the numbers in brackets point to the sources listed at the end of this page. This page "
                "is written from that file by [`_shared/emit_board_readme.py`](../_shared/emit_board_readme.py): "
                "change the file, then run the script.", ""]
        links = ident.get("links") or {}
        if links:
            out += ["Vendor links: " + " · ".join(f"[{k}]({v})" for k, v in links.items()), ""]
        out += self.physical() + self.components() + self.connections() + self.absent()
        if d.get("notes"):
            out += ["## Notes", ""] + [p.strip() + "\n" for p in str(d["notes"]).split("\n\n") if p.strip()]
            out[-1] = out[-1].rstrip("\n")
            out.append("")
        out += self.sources() + self.folder()
        return out

    def physical(self) -> list[str]:
        phys = self.data.get("physical")
        if not phys:
            return []
        cols = [(t, k, u) for t, k, u in (("Width", "width_mm", "mm"), ("Height", "height_mm", "mm"),
                                          ("Depth", "depth_mm", "mm"), ("Weight", "weight_g", "g")) if k in phys]
        out = ["## Dimensions", ""]
        if cols:
            out += ["| " + " | ".join(t for t, _, _ in cols) + " |", "|" + " --- |" * len(cols),
                    "| " + " | ".join(fmt_number(phys[k], u) for _, k, u in cols) + " |", ""]
        out += [(cell(phys["notes"]) + " " if phys.get("notes") else "") + self.src(phys["src"]), ""]
        return out

    def components(self) -> list[str]:
        total = sum(c["quantity"] for c in self.comps)
        out = ["## Components", "", f"{len(self.comps)} entries ({total} parts counting quantities).", ""]
        placed = set()
        for title, roles in GROUPS:
            rows = [c for c in self.comps if c["role"] in roles]
            if not rows:
                continue
            out += [f"### {title}", "", "| Part | Role | Ref. | Qty | Key facts | Src |",
                    "| --- | --- | --- | --- | --- | --- |"]
            for c in rows:
                placed.add(c["id"])
                part = c.get("part", "—") + (f' ({c["manufacturer"]})' if c.get("manufacturer") else "")
                facts = "; ".join(f"{label(k)}: {fmt_value(v)}" for k, v in (c.get("specs") or {}).items())
                if c.get("notes"):
                    facts += (" — " if facts else "") + c["notes"]
                out.append(f'| {cell(part)} | {label(c["role"])} | {cell(c.get("designator", "—"))} | '
                           f'{c["quantity"]} | {cell(facts)} | {self.src(c["src"])} |')
            out.append("")
        lost = [c["id"] for c in self.comps if c["id"] not in placed]
        if lost:
            raise SystemExit(f"{self.board}: components of no group: {', '.join(lost)}")
        return out

    def connections(self) -> list[str]:
        rows = []
        for c in self.comps:
            for link in c.get("connects_to") or []:
                pins = "<br>".join(f"{cell(k)} → {cell(v)}" for k, v in (link.get("pins") or {}).items())
                pulls = "<br>".join(
                    f'{cell(p["signal"])}: {p["direction"]}'
                    + (f' {ohms(p["ohms"])}' if "ohms" in p else "")
                    + (f' to {cell(p["to"])}' if p.get("to") else "")
                    + (f' ({cell(p["designator"])})' if p.get("designator") else "")
                    for p in link.get("pulls") or [])
                rows.append(f'| {cell(self.name(c["id"]))} | {cell(self.name(link["to"]))} | '
                            f'{cell(link.get("bus", ""))} | {cell(link.get("address", ""))} | {pins} | {pulls} | '
                            f'{cell(link.get("notes", ""))} | {self.src(link.get("src") or c["src"])} |')
        if not rows:
            return []
        return ["## Connections", "", "Each row is one fact of wiring, read from the component in the first column; "
                "a row without sources of its own takes its component's.", "",
                "| From | To | Bus | Address | Pins | Pulls | Notes | Src |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |"] + rows + [""]

    def absent(self) -> list[str]:
        rows = self.data.get("absent") or []
        if not rows:
            return []
        return (["## Not on this board", "", "| Role | Notes | Src |", "| --- | --- | --- |"]
                + [f'| {label(a["role"])} | {cell(a.get("notes", ""))} | {self.src(a["src"])} |' for a in rows]
                + [""])

    def sources(self) -> list[str]:
        out = ["## Sources", ""]
        for sid, s in self.data["sources"].items():
            line = f'{self.numbers[sid]}. ' + (f'[{s["title"]}]({s["url"]})' if s.get("url") else s["title"])
            line += f' — {KINDS.get(s["kind"], label(s["kind"]))}, checked {s["checked"]} (`{sid}`)'
            if s.get("mirror_of"):
                line += f'; read at a mirror of <{s["mirror_of"]}>'
            if s.get("found_via"):
                line += f'; found through [{self.numbers[s["found_via"]]}]'
            line += "."
            for key in ("method", "notes"):
                if s.get(key):
                    line += " " + " ".join(str(s[key]).split())
            out.append(line)
        return out + [""]

    def folder(self) -> list[str]:
        out = ["## In this folder", ""]
        for path, what in FOLDER:
            rel = path.format(b=self.board)
            target = ROOT / self.board / rel
            if target.exists() and (not rel.endswith("/") or any(target.iterdir())):
                out.append(f"- [`{rel}`]({rel}): {what}.")
        out += ["", "How the drawings, models and schematics are made, and which script writes each file: "
                "[`docs/models-and-drawings.md`](../docs/models-and-drawings.md)."]
        return out


def render(board: str) -> str:
    data = json.loads((ROOT / board / "board.json").read_text(encoding="utf-8"))
    return "\n".join(Page(board, data).lines()).rstrip("\n") + "\n"


def boards() -> list[str]:
    return sorted(p.parent.name for p in ROOT.glob("*/board.json"))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("boards", nargs="*")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if a page differs")
    args = ap.parse_args(argv)
    stale = []
    for board in args.boards or boards():
        page, text = ROOT / board / "README.md", render(board)
        if page.exists() and page.read_text(encoding="utf-8") == text:
            continue
        if args.check:
            stale.append(board)
        else:
            page.write_text(text, encoding="utf-8")
            print(f"wrote {page.relative_to(ROOT)}")
    for board in stale:
        print(f"FAIL {board}/README.md differs from what board.json writes (run _shared/emit_board_readme.py {board})")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
