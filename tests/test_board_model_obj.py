# SPDX-License-Identifier: MIT
"""Every board's OBJ and MTL are what its master GLB gives, and read back as that model.

``_shared/export_obj.py`` writes ``<board>/model/<board>.obj`` and ``.mtl`` from
the board's master GLB and from nothing else, and ``model/source.json``
records the two under ``obj``. This holds, on the files as committed:

- the OBJ, the MTL and their record are, byte for byte, what the committed GLB
  gives now, and the OBJ's header names that GLB's digest;
- read back by another reader (trimesh), the OBJ has the GLB's vertices,
  triangles and bounds (millimetres against the GLB's metres), one object per
  mesh of the GLB in its order, and every material it uses is in its MTL,
  which holds the GLB's materials in their order;
- the numbers are written in fixed decimals with no ``-0``.

Host-only: no build, no hardware, no network.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))
from paths import BOARDS  # noqa: E402

pytestmark = pytest.mark.models


def library(name: str):
    """A library the check needs: skipped where it is missing, a failure in CI, which installs it."""
    try:
        return __import__(name)
    except ImportError:
        if os.environ.get("CI"):
            pytest.fail(f"{name} is not installed: a broken install of requirements.txt")
        pytest.skip(f"{name} is not installed: pip install -r requirements.txt")


def exporter():
    library("numpy")
    import export_obj

    return export_obj


def record(board: str) -> dict:
    return json.loads((ROOT / board / "model" / "source.json").read_text(encoding="utf-8"))


def glb_json(path: Path) -> dict:
    data = path.read_bytes()
    return json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])


def lines(path: Path, key: str) -> list[str]:
    """The argument of every line of *path* that starts with *key*."""
    prefix = key + " "
    return [line[len(prefix):] for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith(prefix)]


@pytest.mark.parametrize("board", BOARDS)
def test_the_obj_and_mtl_are_what_the_glb_gives(board: str) -> None:
    """Rewritten from the committed GLB, both files and their record come out the same."""
    assert exporter().problems(board) == [], f"run: python -I _shared/export_obj.py {board}"
    rec = record(board)
    obj = rec["obj"]
    assert obj["obj"] == f"{board}/model/{board}.obj" and obj["mtl"] == f"{board}/model/{board}.mtl"
    assert obj["units"] == "mm" and obj["up"] == "+Y"
    for kind in ("obj", "mtl"):
        data = (ROOT / obj[kind]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == obj[f"{kind}_sha256"]
        assert len(data) == obj[f"{kind}_bytes"]
        assert b"\r" not in data and data.endswith(b"\n")
    # the leading comments: the metadata block, then the exporter's header
    lines = (ROOT / obj["obj"]).read_text(encoding="utf-8").splitlines()
    header = lines[:next(i for i, line in enumerate(lines) if not line.startswith("#"))]
    assert f"# Source: {board}.glb, sha256 {rec['model_sha256']}" in header
    assert any(line.startswith("# Units: millimetres") for line in header)
    assert obj["triangles"] == rec["triangles"] and obj["materials"] == rec["materials"]


@pytest.mark.parametrize("board", BOARDS)
def test_the_obj_reads_back_as_the_glb(board: str) -> None:
    """Another reader finds the GLB's vertices, triangles and bounds, in millimetres."""
    np = library("numpy")
    trimesh = library("trimesh")
    glb_path = ROOT / record(board)["model"]
    obj_path = glb_path.with_suffix(".obj")
    glb = trimesh.load(glb_path, force="scene", process=False)
    obj = trimesh.load(obj_path, force="scene", process=False)
    glb_parts, obj_parts = glb.dump(), obj.dump()
    assert sum(len(m.faces) for m in obj_parts) == sum(len(m.faces) for m in glb_parts)
    assert sum(len(m.vertices) for m in obj_parts) == sum(len(m.vertices) for m in glb_parts)
    assert np.abs(obj.bounds - glb.bounds * 1000.0).max() < 1e-3, "not in millimetres"
    assert record(board)["obj"]["vertices"] == sum(len(m.vertices) for m in glb_parts)


@pytest.mark.parametrize("board", BOARDS)
def test_one_object_per_mesh_and_every_material_in_the_mtl(board: str) -> None:
    """The GLB's meshes, in order, as objects; its materials, in order, in the MTL."""
    js = glb_json(ROOT / record(board)["model"])
    obj_path = ROOT / record(board)["obj"]["obj"]
    mtl_path = ROOT / record(board)["obj"]["mtl"]
    meshes = [js["nodes"][i] for i in js["nodes"][0]["children"]]
    assert lines(obj_path, "o") == lines(obj_path, "g") == [n["name"] for n in meshes]
    assert lines(obj_path, "mtllib") == [mtl_path.name]
    declared = lines(mtl_path, "newmtl")
    assert declared == [m["name"] for m in js["materials"]]
    assert set(lines(obj_path, "usemtl")) <= set(declared)
    # each material's colour is the GLB's base colour in sRGB, with its roughness
    # and metalness; a blended material keeps its alpha, the unlit screen its
    # constant colour
    to_srgb = exporter().model_raster.linear_to_srgb
    for index, mat in enumerate(js["materials"]):
        block = mtl_path.read_text(encoding="utf-8").split(f"newmtl {mat['name']}\n")[1]
        block = block.split("\n\n")[0].splitlines()
        values = {x.split(" ", 1)[0]: x.split(" ", 1)[1] for x in block}
        pbr = mat["pbrMetallicRoughness"]
        kd = [float(v) for v in values["Kd"].split()]
        assert kd == pytest.approx(list(to_srgb(pbr["baseColorFactor"][:3])), abs=1e-4), (
            board, mat["name"])
        assert float(values["Pr"]) == pytest.approx(pbr.get("roughnessFactor", 1.0), abs=1e-4)
        assert float(values["Pm"]) == pytest.approx(pbr.get("metallicFactor", 1.0), abs=1e-4)
        alpha = mat["pbrMetallicRoughness"]["baseColorFactor"][3]
        expected = alpha if mat.get("alphaMode") == "BLEND" else 1.0
        assert float(next(x for x in block if x.startswith("d "))[2:]) == pytest.approx(
            expected, abs=1e-4), (board, index)
        unlit = "KHR_materials_unlit" in mat.get("extensions", {})
        assert ("illum 0" if unlit else "illum 2") in block, (board, mat["name"])


def test_numbers_are_fixed_decimals_with_no_negative_zero() -> None:
    export_obj = exporter()
    assert export_obj.num(-0.00001, 4) == "0"
    assert export_obj.num(12.3400, 4) == "12.34"
    assert export_obj.num(5.0, 4) == "5"
    assert export_obj.num(-7.39, 4) == "-7.39"
    assert export_obj.num(0.123456, 5) == "0.12346"
    assert export_obj.name_of("ink black") == "ink_black"


def test_an_unnamed_material_has_one_name_in_both_files() -> None:
    """``usemtl`` names what ``newmtl`` declares, never ``#<index>`` (a comment in OBJ)."""
    export_obj = exporter()
    js = {"materials": [{"name": "case"}, {}]}

    class Mesh:
        name, material = "part", "#1"

    assert export_obj.material_names(js) == ["case", "material_1"]
    assert export_obj.material_of(Mesh, js) == "material_1"
    Mesh.material = "#"
    with pytest.raises(ValueError):
        export_obj.material_of(Mesh, js)


def test_only_a_board_master_gets_an_obj() -> None:
    """``<board>/model/<board>.glb`` does; the checks' fixture and another name do not."""
    export_obj = exporter()
    assert export_obj.applies("sticks3/model/sticks3.glb")
    assert not export_obj.applies("sticks3/model/sticks3-web.glb")
    assert not export_obj.applies("_shared/fixtures/faces/model/faces.glb")
