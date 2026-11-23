# SPDX-License-Identifier: MIT
"""Check a board's KiCad schematic and write its PDF and SVGs.

Runs, in ``<board>/schematic/``:

1. ``kicad-cli sch erc``: fails on any error or warning (the report is
   printed);
2. ``check_schematic.py``: the drawn netlist against ``netlist.yaml``, pin by
   pin, every Kleidos addition or correction marked and listed, and what the
   index pages and the title blocks say of them;
3. ``kicad-cli sch export pdf``: ``<board>.pdf``, every sheet, in the Kleidos
   dark theme and on the Kleidos drawing sheet (the kit in ``kicad/`` beside
   this script, copied from brand: ``kicad/KIT.json``), with
   KiCad's page links (a sheet's box on the contents page, the ``[page/zone]``
   after a net label, the places in the index pages, the page row on every
   page), but without the property pop-ups, which only Acrobat's scripting
   opens; every page must draw the kit's mark once, one image object for all;
   then ``schematic_pdf.py`` sends each link that names a place to that
   place, adds a link on every part's reference to its row in the parts list,
   writes the named destinations and the bookmarks, and removes every script;
4. ``kicad-cli sch export svg``: one SVG per sheet into ``svg/``, renamed to
   ``<board>-<page>-<sheet>.svg`` (no spaces), in the same theme;
5. ``check_schematic_links.py``: every link of the PDF leads to the page,
   and the place, it should; no script; the bookmarks list every page.

kicad-cli runs through the kit's ``kleidos_kicad.py``, the same way as in every
Kleidos repository: a settings folder of its own (``KICAD_CONFIG_HOME``) that
asks for English and holds the themes, so the output is the same on every
machine; ``--theme``, ``--drawing-sheet`` and the kit's face on every export.
Two checks guard the theme: kicad-cli falls back to its default theme without
a word when ``--theme`` names one it cannot find, so every SVG's background
must be the theme's; and every line drawn in the wire colour (wires, pin lines,
junctions) must have the one width the project sets.

Usage::

    python3 _shared/export_schematic.py <board> [--kicad-cli PATH] [--no-export] [--out DIR]

``KICAD_CLI`` also names kicad-cli. ``--out`` writes the PDF and the SVGs to
another folder instead of the board's. Exit status 0 when every check passes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "kicad"))
import kleidos_kicad as kit  # noqa: E402  (the Kleidos KiCad kit, copied from brand)
from check_schematic import additions, compare, index_pages  # noqa: E402
from paths import ROOT  # noqa: E402

GROUND = "dark"  # what is published and committed
THEME = kit.theme_name(GROUND)  # the name kicad-cli is given: the theme file's name in colors/
THEME_FILE = kit.theme_file(GROUND)
SHEET_FILE = kit.sheet(GROUND)


def theme_colours() -> dict[str, str]:
    """The theme's schematic colours as SVG writes them (#RRGGBB)."""
    return kit.theme_colors(GROUND)


def run(cli: str, args: list[str], cwd: Path, env: dict):
    return kit.run(args, cwd, env, cli)


def line_mil(folder: Path, board: str) -> float:
    pro = json.loads((folder / f"{board}.kicad_pro").read_text(encoding="utf-8"))
    widths = {c["wire_width"] for c in pro["net_settings"]["classes"]}
    widths.add(pro["schematic"]["drawing"]["default_line_thickness"])
    if len(widths) != 1:
        raise SystemExit(
            f"{board}.kicad_pro: the wire and default line widths differ ({sorted(widths)} mil)"
        )
    return widths.pop()


def check_svg(svg: Path, colours: dict[str, str], width_mm: float, wires: bool = True) -> list[str]:
    """The page background is the theme's, and every wire-coloured line has one width (the kit's check)."""
    if round(width_mm, 4) != round(kit.connection_mm(), 4):
        return [
            f"{svg.name}: the project's line width {width_mm:.4f} mm is not the kit's {kit.connection_mm():.4f}"
        ]
    return kit.svg_findings(svg, GROUND, wires)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("board")
    ap.add_argument("--kicad-cli", default=os.environ.get("KICAD_CLI", "kicad-cli"))
    ap.add_argument("--no-export", action="store_true", help="check only, write no PDF or SVG")
    ap.add_argument(
        "--out", type=Path, help="write the PDF and svg/ here instead of the board's folder"
    )
    args = ap.parse_args(argv)
    folder = ROOT / args.board / "schematic"
    out_dir = (args.out or folder).resolve()
    sch = f"{args.board}.kicad_sch"
    env = kit.environment()
    tmp = Path(tempfile.mkdtemp())

    erc = tmp / "erc.rpt"
    run(args.kicad_cli, ["sch", "erc", "--severity-all", "-o", str(erc), sch], folder, env)
    report = erc.read_text(encoding="utf-8") if erc.exists() else ""
    m = re.search(r"ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)", report)
    if not m:
        print(report or "ERC did not run")
        return 1
    print(f"ERC: {m.group(1)} messages, {m.group(2)} errors, {m.group(3)} warnings")
    if m.group(1) != "0":
        print("\n".join(report.splitlines()[:60]))
        return 1

    xml = tmp / "netlist.xml"
    run(
        args.kicad_cli,
        ["sch", "export", "netlist", "--format", "kicadxml", "-o", str(xml), sch],
        folder,
        env,
    )
    errors = compare(args.board, xml) + additions(args.board) + index_pages(args.board)
    for e in errors:
        print(f"FAIL {e}")
    if errors:
        return 1
    n = len(
        yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8")).get("kleidos") or []
    )
    print(
        "netlist: the drawing matches netlist.yaml, pin for pin"
        + (
            f"; {n} Kleidos additions and corrections, each marked and listed, and again wherever an "
            "index page shows its element"
            if n
            else ""
        )
    )
    if args.no_export:
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / f"{args.board}.pdf"
    out = kit.export_pdf(folder / sch, pdf, env, GROUND, args.kicad_cli)
    if out.returncode:
        print(out.stdout, out.stderr)
        return 1
    from pypdf import PdfReader

    errors = kit.pdf_findings(PdfReader(pdf), GROUND)
    for e in errors:
        print(f"FAIL the mark: {e}")
    if errors:
        return 1
    import schematic_pdf

    errors = schematic_pdf.finish(args.board, pdf)
    for e in errors:
        print(f"FAIL {e}")
    if errors:
        return 1
    svg_tmp = tmp / "svg"
    svg_tmp.mkdir()
    out = kit.export_svg(folder / sch, svg_tmp, env, GROUND, args.kicad_cli)
    if out.returncode:
        print(out.stdout, out.stderr)
        return 1
    # page order: the root first, then the sheets as layout.yaml lists them
    layout = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    names = [(f"{args.board}.svg", "contents")] + [
        (f"{args.board}-{sh['name']}.svg", sh["file"].removesuffix(".kicad_sch"))
        for sh in layout["sheets"]
    ]
    colours = theme_colours()
    width_mm = line_mil(folder, args.board) * 0.0254
    errors = []
    for page, (got, _) in enumerate(names, start=1):
        src = svg_tmp / got
        if not src.exists():
            print(f"FAIL kicad-cli wrote no {got}")
            return 1
        drawing = page > 1 and "index" not in layout["sheets"][page - 2]
        errors += check_svg(src, colours, width_mm, wires=drawing)
    for e in errors:
        print(f"FAIL {e}")
    if errors:
        return 1
    print(
        f"theme: {THEME}, background {colours['background']} on every page; "
        f"wires and pin lines {width_mm:.4f} mm; the drawing sheet {SHEET_FILE.name}, the mark on every page"
    )
    dest = out_dir / "svg"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir()
    for page, (got, slug) in enumerate(names, start=1):
        shutil.copyfile(svg_tmp / got, dest / f"{args.board}-{page}-{slug.replace('_', '-')}.svg")
    print(f"wrote {pdf.name} and {len(names)} SVGs in {dest}")

    import check_schematic_links

    return check_schematic_links.main([args.board, "--pdf", str(pdf)])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
