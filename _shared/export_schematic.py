# SPDX-License-Identifier: MIT
"""Check a board's KiCad schematic and write its PDF and SVGs.

Runs, in ``<board>/schematic/``:

1. ``kicad-cli sch erc``: fails on any error or warning (the report is
   printed);
2. ``check_schematic.py``: the drawn netlist against ``netlist.yaml``, pin by
   pin, every Kleidos addition or correction marked and listed, and what the
   index pages and the title blocks say of them;
3. ``kicad-cli sch export pdf``: ``<board>.pdf``, every sheet, in the Kleidos
   dark theme (``kicad-theme-kleidos-dark.json`` beside this script), with
   KiCad's page links (a sheet's box on the contents page, the ``[page/zone]``
   after a net label, the places in the index pages, the page row on every
   page), but without the property pop-ups, which only Acrobat's scripting
   opens; then ``schematic_pdf.py`` sends each link that names a place to that
   place, adds a link on every part's reference to its row in the parts list,
   writes the named destinations and the bookmarks, and removes every script;
4. ``kicad-cli sch export svg``: one SVG per sheet into ``svg/``, renamed to
   ``<board>-<page>-<sheet>.svg`` (no spaces), in the same theme;
5. ``check_schematic_links.py``: every link of the PDF leads to the page,
   and the place, it should; no script; the bookmarks list every page.

Two checks guard the theme. kicad-cli falls back to its default theme without a
word when ``--theme`` names one it cannot find, so every SVG's background must
be the theme's; and every line drawn in the wire colour (wires, pin lines,
junctions) must have the one width the project sets.

kicad-cli prints in the language of the KiCad install's settings, and so does
the PDF ("File:" under each sheet). The script runs it with a settings folder
of its own (``KICAD_CONFIG_HOME``) that asks for English and holds the theme,
so the output is the same on every machine.

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
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_schematic import additions, compare, index_pages  # noqa: E402
from paths import ROOT  # noqa: E402

THEME_FILE = Path(__file__).resolve().parent / "kicad-theme-kleidos-dark.json"
THEME = "kleidos-dark"           # the name kicad-cli is given: the file's name in colors/


def theme_colours() -> dict[str, str]:
    """The theme's schematic colours as SVG writes them (#RRGGBB)."""
    data = json.loads(THEME_FILE.read_text(encoding="utf-8"))["schematic"]
    out = {}
    for key, val in data.items():
        m = re.fullmatch(r"rgba?\((\d+), (\d+), (\d+)(?:, [\d.]+)?\)", str(val))
        if m:
            out[key] = "#" + "".join(f"{int(c):02X}" for c in m.groups())
    return out


def kicad_config() -> str:
    """A KiCad settings folder holding the language (English) and the theme."""
    home = Path(tempfile.mkdtemp(prefix="kicad-cfg-"))
    for version in ("9.0", "10.0", "11.0"):
        (home / version / "colors").mkdir(parents=True)
        (home / version / "kicad_common.json").write_text(
            json.dumps({"system": {"language": "English"}}), encoding="utf-8")
        shutil.copyfile(THEME_FILE, home / version / "colors" / f"{THEME}.json")
    return str(home)


def run(cli: str, args: list[str], cwd: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([cli, *args], cwd=cwd, env=env, capture_output=True, text=True)


def line_mil(folder: Path, board: str) -> float:
    pro = json.loads((folder / f"{board}.kicad_pro").read_text(encoding="utf-8"))
    widths = {c["wire_width"] for c in pro["net_settings"]["classes"]}
    widths.add(pro["schematic"]["drawing"]["default_line_thickness"])
    if len(widths) != 1:
        raise SystemExit(f"{board}.kicad_pro: the wire and default line widths differ ({sorted(widths)} mil)")
    return widths.pop()


def check_svg(svg: Path, colours: dict[str, str], width_mm: float, wires: bool = True) -> list[str]:
    """The page background is the theme's, and every wire-coloured line has one width."""
    text = svg.read_text(encoding="utf-8")
    errors = []
    bg = re.search(r'<g style="fill:(#[0-9A-F]{6});[^>]*>\s*<rect x="0\.0+" y="0\.0+"', text)
    if not bg or bg.group(1) != colours["background"]:
        errors.append(f"{svg.name}: background {bg.group(1) if bg else 'missing'}, "
                      f"the theme's is {colours['background']} (was the theme found?)")
    wire = colours["wire"]
    widths = set()
    for m in re.finditer(r'<g style="([^"]*)"', text):
        style = m.group(1)
        if f"stroke:{wire};" in style and "fill:none" in style:
            w = re.search(r"stroke-width:([\d.]+)", style)
            if w:
                widths.add(round(float(w.group(1)), 4))
    if widths and widths != {round(width_mm, 4)}:
        errors.append(f"{svg.name}: lines in the wire colour take widths {sorted(widths)} mm, "
                      f"not only {width_mm:.4f}")
    if wires and not widths:
        errors.append(f"{svg.name}: no line in the wire colour {wire}")
    return errors


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("board")
    ap.add_argument("--kicad-cli", default=os.environ.get("KICAD_CLI", "kicad-cli"))
    ap.add_argument("--no-export", action="store_true", help="check only, write no PDF or SVG")
    ap.add_argument("--out", type=Path, help="write the PDF and svg/ here instead of the board's folder")
    args = ap.parse_args(argv)
    folder = ROOT / args.board / "schematic"
    out_dir = (args.out or folder).resolve()
    sch = f"{args.board}.kicad_sch"
    env = dict(os.environ, KICAD_CONFIG_HOME=kicad_config())
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
    run(args.kicad_cli, ["sch", "export", "netlist", "--format", "kicadxml", "-o", str(xml), sch], folder, env)
    errors = compare(args.board, xml) + additions(args.board) + index_pages(args.board)
    for e in errors:
        print(f"FAIL {e}")
    if errors:
        return 1
    n = len(yaml.safe_load((folder / "netlist.yaml").read_text(encoding="utf-8")).get("kleidos") or [])
    print("netlist: the drawing matches netlist.yaml, pin for pin"
          + (f"; {n} Kleidos additions and corrections, each marked and listed, and again wherever an "
             "index page shows its element" if n else ""))
    if args.no_export:
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / f"{args.board}.pdf"
    out = run(args.kicad_cli, ["sch", "export", "pdf", "--theme", THEME, "--exclude-pdf-property-popups",
                               "-o", str(pdf), sch], folder, env)
    if out.returncode:
        print(out.stdout, out.stderr)
        return 1
    import schematic_pdf
    errors = schematic_pdf.finish(args.board, pdf)
    for e in errors:
        print(f"FAIL {e}")
    if errors:
        return 1
    svg_tmp = tmp / "svg"
    svg_tmp.mkdir()
    out = run(args.kicad_cli, ["sch", "export", "svg", "--theme", THEME, "-o", str(svg_tmp), sch], folder, env)
    if out.returncode:
        print(out.stdout, out.stderr)
        return 1
    # page order: the root first, then the sheets as layout.yaml lists them
    layout = yaml.safe_load((folder / "layout.yaml").read_text(encoding="utf-8"))
    names = [(f"{args.board}.svg", "contents")] + [
        (f"{args.board}-{sh['name']}.svg", sh["file"].removesuffix(".kicad_sch")) for sh in layout["sheets"]]
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
    print(f"theme: {THEME}, background {colours['background']} on every page; "
          f"wires and pin lines {width_mm:.4f} mm")
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
