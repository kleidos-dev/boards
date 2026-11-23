# SPDX-License-Identifier: MIT
"""The Kleidos KiCad kit under _shared/kicad/: brand's files, byte for byte, and what the generator takes from them."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "_shared" / "kicad"
sys.path.insert(0, str(ROOT / "_shared"))
sys.path.insert(0, str(KIT))

import kicad_schematic as ks  # noqa: E402
import kleidos_kicad as kit  # noqa: E402

IGNORED = {"__pycache__"}


def test_every_file_of_the_kit_is_the_one_its_manifest_records():
    manifest = json.loads((KIT / "KIT.json").read_text(encoding="utf-8"))
    assert manifest["kit"] == "kleidos-kicad/1"
    assert manifest["source"] == "https://github.com/kleidos-dev/brand"
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["commit"]), "sync the kit from a brand commit"
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((KIT / name).read_bytes()).hexdigest() == digest, (
            f"{name}: never edit a copy; sync it from brand"
        )
    extra = {p.name for p in KIT.iterdir()} - set(manifest["files"]) - {"KIT.json"} - IGNORED
    assert not extra, f"not part of the kit: {sorted(extra)}"


def test_the_generator_takes_its_numbers_from_the_kit():
    style = kit.style()
    assert (ks.GRID, ks.PITCH, ks.PIN_LEN, ks.STUB) == (
        style["lines"]["grid"],
        style["lines"]["pin_pitch"],
        style["lines"]["pin_length"],
        style["lines"]["stub"],
    )
    assert (ks.FONT, ks.REF_FONT, ks.ROOT_FONT) == (
        style["text"]["body"],
        style["text"]["small"],
        style["text"]["running"],
    )
    assert ks.LINE_MIL == style["lines"]["connection_mil"] == 6
    assert (ks.ZONE_ORIGIN, ks.ZONE_STEP) == (10.0, 50.0)
    assert (ks.KEEPOUT_X, ks.KEEPOUT_Y, ks.NAV_X, ks.NAV_Y) == (125.0, 48.0, 112.0, 47.0)
    assert ks.MARK_COLOUR == (255, 184, 0) and ks.RULE_COLOUR == (136, 153, 170)
    assert ks.BLOCK_LINES == style["sheet"]["comment_lines"]


def test_every_board_s_project_names_the_kit_s_sheet_and_its_variables():
    for pro in sorted(ROOT.glob("*/schematic/*.kicad_pro")):
        data = json.loads(pro.read_text(encoding="utf-8"))
        sheet = (pro.parent / data["schematic"]["page_layout_descr_file"]).resolve()
        assert sheet == kit.sheet("dark").resolve(), pro
        assert data["text_variables"] == {
            "LICENSE": "MIT",
            "SOURCE_URL": "github.com/kleidos-dev/boards",
        }, pro


def test_every_title_block_line_fits_its_cell():
    import yaml

    for layout in sorted(ROOT.glob("*/schematic/layout.yaml")):
        lay = yaml.safe_load(layout.read_text(encoding="utf-8"))
        net = yaml.safe_load((layout.parent / "netlist.yaml").read_text(encoding="utf-8"))
        assert ks.title_block_errors(lay, bool(net.get("kleidos"))) == [], layout


def test_a_title_too_wide_for_its_cell_is_refused():
    lay = {
        "title_block": {
            "title": "A board with a very long name indeed (K000-LONG)",
            "company": "c",
            "comments": [],
        },
        "root": {"title": "Contents"},
        "sheets": [
            {"name": "Power input, charging, protection and the fuel gauge", "file": "p.kicad_sch"}
        ],
    }
    errors = ks.title_block_errors(lay, False)
    assert any("title cell" in e for e in errors)


def test_the_license_comment_left_the_layouts():
    for layout in sorted(ROOT.glob("*/schematic/layout.yaml")):
        assert "License: MIT" not in layout.read_text(encoding="utf-8"), layout
