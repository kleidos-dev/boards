# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""The commands that check, list, weigh and draw a model, on the checks' own test board.

``_shared/check_board_model.py`` and ``_shared/legend_placement.py`` hold a
model to its drawings, ``_shared/glb_legends.py`` takes its legends out,
``_shared/legend_source.py`` gives a drawing's digest, ``_shared/export_obj.py``
writes its OBJ and ``_shared/models_contact_sheet.py`` draws every model side by
side. Each command is run on ``_shared/fixtures/faces`` as committed, which
must pass, and on a copy with a defect planted, which must not.

The boards' own models are held by ``tests/test_board_model_legends.py``.

Host-only: no build, no hardware, no network.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))
import check_board_model  # noqa: E402  after the sys.path set-up above
import export_obj  # noqa: E402  after the sys.path set-up above
import glb_legends  # noqa: E402  after the sys.path set-up above
import legend_placement  # noqa: E402  after the sys.path set-up above
import legend_source  # noqa: E402  after the sys.path set-up above
import media_meta  # noqa: E402  after the sys.path set-up above
import model_raster  # noqa: E402  after the sys.path set-up above
import models_contact_sheet  # noqa: E402  after the sys.path set-up above
import paths  # noqa: E402  after the sys.path set-up above

FIXTURE = ROOT / "_shared" / "fixtures" / "faces"
MODEL = FIXTURE / "model" / "faces.glb"


def planted(tmp_path: Path, change: Callable[[dict[str, Any]], None]) -> Path:
    """A copy of the test board's model with *change* made to its JSON chunk."""
    js, body = glb_legends.read(MODEL.read_bytes())
    change(js)
    out = tmp_path / "planted.glb"
    out.write_bytes(glb_legends.write(js, body))
    return out


def node(js: dict[str, Any], name: str) -> dict[str, Any]:
    found: dict[str, Any] = next(n for n in js["nodes"] if n.get("name", "").startswith(name))
    return found


def _print_moved(js: dict[str, Any]) -> None:
    node(js, "name_legends")["translation"] = [0.001, 0.0, 0.0]


def _print_sunk(js: dict[str, Any]) -> None:
    node(js, "name_legends")["translation"] = [0.0, 0.0, -0.00003]


def _print_see_through(js: dict[str, Any]) -> None:
    """The print's ink drawn half transparent, under the name it had."""
    for material in js["materials"]:
        if material.get("name", "").startswith(glb_legends.INK_PREFIX):
            material["alphaMode"] = "BLEND"
            material["pbrMetallicRoughness"]["baseColorFactor"][3] = 0.5


# --- check_board_model --------------------------------------------------------------


def test_the_model_check_passes_the_board_as_committed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "views"
    assert check_board_model.main([str(FIXTURE), "--out", str(out)]) == 0
    report = json.loads((out / "faces-check.json").read_text(encoding="utf-8"))
    assert report["worst_mm"] == 0.0 and report["legends"]["ok"] and report["depth"]["ok"]
    assert (out / "faces-views.png").read_bytes().startswith(b"\x89PNG")
    shown = json.loads(capsys.readouterr().out)
    assert "per_group" in report["legends"] and "per_group" not in shown["legends"]


def test_the_model_check_names_a_folder_of_its_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "mkdtemp", lambda prefix: str(tmp_path))
    assert check_board_model.main([str(FIXTURE), "--glb", str(MODEL)]) == 0
    assert (tmp_path / "faces-check.json").is_file()
    assert json.loads(capsys.readouterr().out)["png"] == str(tmp_path / "faces-views.png")


@pytest.mark.parametrize(
    ("change", "options", "words"),
    [
        (_print_moved, [], "FAIL: legends:"),
        (_print_sunk, [], "FAIL: legends:"),
        (_print_see_through, [], "at alpha 0.5"),
        (lambda js: None, ["--max-dev-mm", "-1"], "FAIL: worst deviation"),
    ],
)
def test_the_model_check_fails_a_defect(
    change: Callable[[dict[str, Any]], None],
    options: list[str],
    words: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    glb = planted(tmp_path, change)
    argv = [str(FIXTURE), "--glb", str(glb), "--out", str(tmp_path), *options]
    assert check_board_model.main(argv) == 1
    assert words in capsys.readouterr().err


def test_the_model_check_fails_two_materials_at_one_depth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The depth and the screen's clearance end the command too, whatever the legends say."""
    real = check_board_model.check

    def tied(*args: Any) -> dict[str, Any]:
        report = real(*args)
        del report["legends"]
        pair = {
            "meshes": ["a", "b"],
            "area_mm2": 1,
            "facing": "front",
            "gap_mm": 0,
            "at_mm": [0, 0],
        }
        report["depth"] = {"ok": False, "pairs": [pair], "least_mm": 0.01}
        return report

    monkeypatch.setattr(check_board_model, "check", tied)
    assert check_board_model.main([str(FIXTURE), "--out", str(tmp_path)]) == 1
    assert "FAIL: depth: a and b cover 1 mm2" in capsys.readouterr().err

    def close(*args: Any) -> dict[str, Any]:
        clearance = {"ok": False, "behind_mm": 0.001, "in_front_mm": 1, "quant_mm": 0.01}
        return {**real(*args), "screen": {"clearance": clearance}}

    monkeypatch.setattr(check_board_model, "check", close)
    assert check_board_model.main([str(FIXTURE), "--out", str(tmp_path)]) == 1
    assert "FAIL: the screen is 0.001 mm in front" in capsys.readouterr().err


def test_a_boards_model_is_its_specs_output_or_the_one_named_after_it(tmp_path: Path) -> None:
    assert check_board_model.model_of(FIXTURE) == MODEL
    folder = tmp_path / "other"
    (folder / "model").mkdir(parents=True)
    assert check_board_model.model_of(folder) == folder / "model" / "other.glb"
    spec = folder / "model" / "spec.json"
    spec.write_text(json.dumps({"output": "../../etc/other.glb"}), encoding="utf-8")
    with pytest.raises(paths.OutsideError):
        check_board_model.model_of(folder)


def test_a_file_that_is_no_model_is_refused(tmp_path: Path) -> None:
    other = tmp_path / "other.glb"
    other.write_bytes(b"not a model, of any kind")
    with pytest.raises(ValueError, match="not a GLB"):
        check_board_model.glb_json(other)
    with pytest.raises(ValueError, match="not a GLB"):
        model_raster.read_glb(other)
    with pytest.raises(ValueError, match="not a GLB"):
        export_obj.glb_json(other.read_bytes())


@pytest.mark.parametrize("module", [check_board_model, legend_placement])
def test_a_check_is_given_a_board_or_its_selftest_and_not_both(
    module: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    for argv in ([], [str(FIXTURE), "--selftest"]):
        with pytest.raises(SystemExit) as stop:
            module.main(argv)
        assert stop.value.code == 2
        assert "--selftest" in capsys.readouterr().err


def test_the_selftest_runs_both_checks_selftests(monkeypatch: pytest.MonkeyPatch) -> None:
    ran: list[str] = []

    def placed(argv: list[str]) -> int:
        ran.append(" ".join(argv))
        return 0

    monkeypatch.setattr(legend_placement, "main", placed)
    for depth, code in ((True, 0), (False, 1)):
        monkeypatch.setattr(check_board_model, "depth_selftest", lambda depth=depth: depth)
        assert check_board_model.main(["--selftest"]) == code
    assert ran == ["--selftest"] * 2


# --- legend_placement ---------------------------------------------------------------


def test_the_placement_check_passes_the_board_as_committed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "report.json"
    assert legend_placement.main([str(FIXTURE), "--json", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["ok"] and set(report["per_group"]) >= {"front-name"}
    assert "per_group" not in json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("change", [_print_moved, _print_see_through])
def test_the_placement_check_fails_a_print_planted_elsewhere(
    change: Callable[[dict[str, Any]], None], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    glb = planted(tmp_path, change)
    assert legend_placement.main([str(FIXTURE), "--glb", str(glb)]) == 1
    assert json.loads(capsys.readouterr().out)["problems"]


@pytest.mark.parametrize(
    ("plane", "key", "given"),
    [
        ("name", "front", None),
        ("label", "drawing", None),
        ("label", "drawing", {"front": FIXTURE / "svg" / "front.svg"}),
        ("label", "drawing", FIXTURE / "svg" / "front.svg"),
    ],
)
def test_a_record_names_a_drawing_of_the_repository(
    plane: str, key: str, given: Any, tmp_path: Path
) -> None:
    """The drawing as it is, but out of the repository: whole paths and ones that climb out."""
    copy = tmp_path / "copy"
    shutil.copytree(FIXTURE, copy)
    path = copy / "model" / "source.json"
    written = json.loads(path.read_text(encoding="utf-8"))
    extras = glb_legends.legends(glb_legends.read(MODEL.read_bytes())[0])
    meshes = model_raster.read_glb(MODEL)
    for outside in (
        str(copy / "svg" / f"{'front' if plane == 'name' else 'back'}.svg"),
        os.path.relpath(copy / "svg" / f"{'front' if plane == 'name' else 'back'}.svg", ROOT),
    ):
        record = json.loads(json.dumps(written))
        (entry,) = (e for e in record["legends"] if e["plane"] == plane)
        entry[key] = outside
        with pytest.raises(paths.OutsideError):
            legend_placement.placement(meshes, extras, given, record, 0.02)
        path.write_text(json.dumps(record), encoding="utf-8")
        with pytest.raises(paths.OutsideError):
            legend_placement.outlines(copy, entry.get("face", "front"))
        if given is None:
            with pytest.raises(paths.OutsideError):
                legend_placement.main([str(copy), "--glb", str(MODEL)])


def test_a_print_is_in_its_ink_and_opaque(tmp_path: Path) -> None:
    """An alpha under 1 is a defect however little under, and 1 is none."""
    record = json.loads((FIXTURE / "model" / "source.json").read_text(encoding="utf-8"))
    extras = glb_legends.legends(glb_legends.read(MODEL.read_bytes())[0])
    meshes = model_raster.read_glb(MODEL)
    for alpha, drawn in ((1.0, True), (0.999, False)):
        worn = [
            dataclasses.replace(m, alpha=alpha) if glb_legends.is_legend(m.name) else m
            for m in meshes
        ]
        report = legend_placement.placement(worn, extras, None, record, 0.02)
        assert report["ok"] is drawn, (alpha, report["problems"])


def test_a_planted_copy_is_the_model_with_its_json_changed(tmp_path: Path) -> None:
    """What the selftest plants its defects with: the copy is written whole and read back."""
    out = tmp_path / "copy.glb"
    meshes, extras = legend_placement._rewritten(MODEL, _print_moved, out)
    assert out.read_bytes() == planted(tmp_path, _print_moved).read_bytes()
    assert [m.name for m in meshes] == [m.name for m in model_raster.read_glb(MODEL)]
    assert len(extras) == 3


def test_a_model_that_prints_nothing_has_nothing_to_place(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    copy = tmp_path / "plain"
    shutil.copytree(FIXTURE, copy)
    bare = copy / "model" / "bare.glb"
    bare.write_bytes(glb_legends.strip(MODEL.read_bytes()))
    record = copy / "model" / "source.json"
    said = json.loads(record.read_text(encoding="utf-8"))
    record.write_text(json.dumps({**said, "legends": []}), encoding="utf-8")
    assert legend_placement.main([str(copy), "--glb", str(bare)]) == 0
    assert "plain: the model prints nothing" in capsys.readouterr().out
    record.write_text(json.dumps({**said, "model": "../../etc/hosts"}), encoding="utf-8")
    with pytest.raises(paths.OutsideError):
        legend_placement.check(copy)


def test_the_outlines_are_the_prints_of_the_face_asked_for() -> None:
    (front,) = legend_placement.outlines(FIXTURE)
    assert front[0] == "name" and all(len(ring) > 2 for ring in front[2])
    assert {plane for plane, _, _ in legend_placement.outlines(FIXTURE, "back")} == {"label"}
    assert legend_placement.outlines(FIXTURE, "left") == []


# --- glb_legends, legend_source -----------------------------------------------------


def test_the_legends_are_listed_and_taken_out(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert glb_legends.main(["list", str(MODEL)]) == 0
    assert "3 legend meshes" in capsys.readouterr().out
    out = tmp_path / "bare.glb"
    assert glb_legends.main(["strip", str(MODEL), str(out)]) == 0
    assert out.read_bytes() == glb_legends.strip(MODEL.read_bytes())
    assert "3 of 3 legend meshes left out" in capsys.readouterr().out
    # only the prints too thin to draw at that scale, with and without multisampling
    for options, left in ((["--px-per-mm", "2"], 2), (["--px-per-mm", "1.5", "--no-antialias"], 1)):
        assert glb_legends.main(["strip", str(MODEL), str(out), *options]) == 0
        assert len(glb_legends.legends(glb_legends.read(out.read_bytes())[0])) == left
    assert glb_legends.main(["strip", str(MODEL), str(MODEL)]) == 1
    assert "the output is the model itself" in capsys.readouterr().err


def test_a_print_that_does_not_say_its_stroke_is_not_judged_by_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def forget(js: dict[str, Any]) -> None:
        for entry in js["nodes"] + js["meshes"]:
            entry.pop("extras", None)

    glb = planted(tmp_path, forget)
    assert glb_legends.main(["strip", str(glb), str(tmp_path / "x.glb"), "--px-per-mm", "2"]) == 1
    assert "built before its legends carried stroke_mm" in capsys.readouterr().err
    assert glb_legends.main(["list", str(glb)]) == 0


def test_a_drawings_digest_is_the_one_its_model_records(
    capsys: pytest.CaptureFixture[str],
) -> None:
    record = json.loads((FIXTURE / "model" / "source.json").read_text(encoding="utf-8"))
    said = {entry["plane"]: entry["legends_sha256"] for entry in record["legends"]}
    front = FIXTURE / "svg" / "front.svg"
    assert legend_source.main([str(front), "--plane", "name"]) == 0
    assert capsys.readouterr().out == f"{said['name']}  1 legend group(s) on the plane 'name'\n"
    assert legend_source.main([str(front)]) == 0
    assert "1 legend group(s)\n" in capsys.readouterr().out


# --- export_obj, models_contact_sheet -----------------------------------------------


def test_the_obj_is_the_model_in_millimeters(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every vertex, face and material of the test board's model, in its order."""
    monkeypatch.setattr(media_meta, "record", lambda path: path)
    monkeypatch.setattr(media_meta, "obj_header", lambda meta: [f"# header of {meta}"])
    monkeypatch.setattr(media_meta, "mtl_header", lambda meta: [f"# header of {meta}"])
    obj, mtl, counts = export_obj.export(MODEL, "faces")
    meshes = model_raster.read_glb(MODEL)
    lines = obj.decode().splitlines()
    assert lines[0] == "# header of _shared/fixtures/faces/model/faces.obj"
    vertices = [line for line in lines if line.startswith("v ")]
    assert len(vertices) == counts["vertices"] == sum(len(m.positions) for m in meshes)
    assert vertices[0] == f"v {export_obj.row(meshes[0].positions[0], 4)}"
    assert sum(line.startswith("f ") for line in lines) == counts["triangles"]
    assert [line[2:] for line in lines if line.startswith("o ")] == [m.name for m in meshes]
    assert mtl.decode().count("newmtl ") == counts["materials"]
    record = export_obj.record(MODEL, obj, mtl, counts)
    assert record["obj"] == "_shared/fixtures/faces/model/faces.obj"
    assert record["obj_bytes"] == len(obj) and record["triangles"] == counts["triangles"]


def test_a_record_names_a_model_of_the_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert export_obj.master("sticks3") == ROOT / "sticks3" / "model" / "sticks3.glb"
    (tmp_path / "sticks3" / "model").mkdir(parents=True)
    record = tmp_path / "sticks3" / "model" / "source.json"
    record.write_text(json.dumps({"model": "../../etc/sticks3.glb"}), encoding="utf-8")
    monkeypatch.setattr(export_obj, "ROOT", tmp_path)
    with pytest.raises(paths.OutsideError):
        export_obj.master("sticks3")


def test_the_sheet_is_drawn_where_it_is_told(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every model in one picture, at a scale small enough to draw in a test."""
    entry = {
        "board": "faces",
        "name": "Test board",
        "glb": MODEL,
        "triangles": 148,
        "gzip": 4096,
    }
    monkeypatch.setattr(models_contact_sheet, "BOARDS", ("faces", "faces"))
    monkeypatch.setattr(models_contact_sheet, "board_entry", lambda board: dict(entry))
    out = tmp_path / "new" / "sheet.png"
    assert models_contact_sheet.main(["--out", str(out), "--ppm", "2"]) == 0
    assert out.read_bytes().startswith(b"\x89PNG")
    assert capsys.readouterr().out.count("faces: 148 triangles") == 2
    assert models_contact_sheet.main(["--check", "--ppm", "2"]) == 1
    assert "is not what the models give" in capsys.readouterr().out


def test_the_sheets_entry_of_a_board_is_its_specs_and_its_records() -> None:
    entry = models_contact_sheet.board_entry("sticks3")
    assert entry["glb"] == ROOT / "sticks3" / "model" / "sticks3.glb"
    record = json.loads((ROOT / "sticks3/model/source.json").read_text(encoding="utf-8"))
    assert entry["triangles"] == record["triangles"]
    sheet = models_contact_sheet.sheet_record(b"png", [entry], 5.0)
    assert sheet["models"]["sticks3"]["model_sha256"] == record["model_sha256"]
