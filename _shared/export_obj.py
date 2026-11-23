# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Write a board model's Wavefront OBJ and MTL from its master GLB

The master model (``<board>/model/<board>.glb``, glTF 2.0) is what the site,
the videos and most viewers read. Many other tools (Blender, FreeCAD, Fusion,
SketchUp, MeshLab, slicers) import Wavefront OBJ with its MTL material
library more readily than glTF, so every board also carries
``<board>/model/<board>.obj`` and ``<board>.mtl``, written here from the master
and from nothing else: the same triangles, normals and screen coordinates,
the same parts and materials.

What the two files hold:

- millimeters, one unit a millimeter, the unit of ``measurements.json``
  (the GLB stores meters, as glTF requires);
- the glTF frame, Y up: +Y up the screen, +Z out of the screen, +X to the
  device's right, the origin where the GLB has it;
- one object (``o``) and one group (``g``) per mesh of the GLB, named as its
  node is, in the GLB's order, each with its material (``usemtl``);
- each vertex of the GLB once, with its normal (``vn``, each distinct one
  written once) and, on the meshes that have them (the screen and the
  glass), its texture coordinate (``vt``, turned to OBJ's convention, v up);
- in the MTL, each material of the GLB, in its order: ``Kd`` its base color
  in sRGB (the GLB stores it linear), ``d`` its alpha (1 opaque), ``Pr`` and
  ``Pm`` its roughness and metalness (the PBR extension of MTL most importers
  read), ``Ns`` and ``Ks`` a classic reader's approximation of the two, and
  ``illum 0`` for an unlit material (the screen) or ``2`` for a lit one. The
  models carry no texture, so neither file names one.

The bytes follow from the GLB alone: numbers in fixed decimals with trailing
zeros dropped (positions 4, normals 4, texture coordinates 5, colors 4), LF
line endings, the GLB's order throughout. The header names the GLB and its
SHA-256, so an OBJ says which master it was written from.

Each file opens with its embedded metadata (``media_meta.obj_header`` and
``mtl_header``, from the file's record): the SPDX tags ``REUSE.toml`` states
for it, then, between REUSE's ignore markers, its title, description,
address, project and terms (the license with its URL, the credits of the
model's parts, the trademark notes). Only that block comes from somewhere
other than the GLB: the board's ``board.json``, its ``model/spec.json`` and
``REUSE.toml``.

The builder (``build_board_glb.py``) runs this whenever it writes a board's
master and records the two files' digests in ``model/source.json`` under
``obj``; ``tests/test_board_model_obj.py`` fails when the committed files or
that record are not what the committed GLB gives. Only a board's own master
(``<board>/model/<board>.glb``) gets them; the checks' fixture does not.

Usage::

    python -I _shared/export_obj.py [BOARD ...] [--check]

With no board, all nine. ``--check`` writes nothing and exits 1 when a
board's OBJ, MTL or record differs from what its GLB gives.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import struct
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_meta
import model_raster
from paths import BOARDS, ROOT

#: Bumped when the same GLB would give other bytes (1.2.0: the header and the
#: MTL comment in US spelling, "millimeters", "meters", "color").
EXPORTER_VERSION = "1.2.0"
#: Decimal places of each kind of number written.
POSITION_PLACES, NORMAL_PLACES, UV_PLACES, COLOR_PLACES = 4, 4, 5, 4


def num(value: float, places: int) -> str:
    """*value* in fixed decimals, its trailing zeros dropped, never ``-0``."""
    text = f"{value:.{places}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def row(values: Iterable[float], places: int) -> str:
    return " ".join(num(float(v), places) for v in values)


def name_of(text: str) -> str:
    """A name OBJ and MTL read as one token: whitespace becomes ``_``."""
    return "_".join(text.split()) or "unnamed"


def material_names(js: dict[str, Any]) -> list[str]:
    """The name each material of the GLB takes in the MTL, in its
    order (``material_<i>`` unnamed)."""
    return [
        name_of(mat.get("name") or f"material_{index}")
        for index, mat in enumerate(js.get("materials", []))
    ]


def material_of(mesh: model_raster.Mesh, js: dict[str, Any]) -> str:
    """The MTL name of *mesh*'s material (``model_raster`` names an unnamed one ``#<index>``)."""
    names = material_names(js)
    if mesh.material.startswith("#") and mesh.material[1:].isdigit():
        return names[int(mesh.material[1:])]
    if mesh.material.startswith("#"):
        raise ValueError(f"{mesh.name}: a primitive with no material")
    return name_of(mesh.material)


def glb_json(data: bytes) -> dict[str, Any]:
    if struct.unpack_from("<I", data, 0)[0] != 0x46546C67:
        raise ValueError("not a GLB")
    length = struct.unpack_from("<I", data, 12)[0]
    js: dict[str, Any] = json.loads(data[20 : 20 + length])
    return js


def mtl_text(board: str, glb_name: str, glb_sha: str, js: dict[str, Any], head: list[str]) -> str:
    """The material library: its metadata *head*, then every material of the GLB, in its order."""
    out = [
        *head,
        f"# {board}: materials of {Path(glb_name).stem}.obj, written from {glb_name} "
        f"by _shared/export_obj.py {EXPORTER_VERSION}",
        f"# Source: {glb_name}, sha256 {glb_sha}",
        "# Kd: base color in sRGB; d: alpha (1 opaque); Pr, Pm: roughness and metalness "
        "(PBR); Ns, Ks: their classic approximation; illum 0 unlit, 2 lit. No textures.",
    ]
    for name, mat in zip(material_names(js), js.get("materials", []), strict=True):
        pbr = mat.get("pbrMetallicRoughness", {})
        factor = pbr.get("baseColorFactor", [1.0, 1.0, 1.0, 1.0])
        kd = model_raster.linear_to_srgb(factor[:3])
        alpha = float(factor[3]) if mat.get("alphaMode") == "BLEND" else 1.0
        metal = float(pbr.get("metallicFactor", 1.0))
        rough = float(pbr.get("roughnessFactor", 1.0))
        ks = (1 - metal) * np.array([0.5, 0.5, 0.5]) + metal * kd
        unlit = "KHR_materials_unlit" in mat.get("extensions", {})
        out += [
            "",
            f"newmtl {name}",
            f"Kd {row(kd, COLOR_PLACES)}",
            f"Ks {row(ks, COLOR_PLACES)}",
            f"Ns {num(1000 * (1 - rough) ** 2, COLOR_PLACES - 2)}",
            f"Pr {num(rough, COLOR_PLACES)}",
            f"Pm {num(metal, COLOR_PLACES)}",
            f"d {num(alpha, COLOR_PLACES)}",
            f"illum {0 if unlit else 2}",
        ]
    return "\n".join(out) + "\n"


def export(glb_path: Path, board: str) -> tuple[bytes, bytes, dict[str, Any]]:
    """(OBJ bytes, MTL bytes, counts) of the GLB at *glb_path*."""
    glb_path = Path(glb_path)
    data = glb_path.read_bytes()
    js = glb_json(data)
    sha = hashlib.sha256(data).hexdigest()
    meshes = model_raster.read_glb(glb_path)
    stem = glb_path.stem
    vertices = sum(len(m.positions) for m in meshes)
    triangles = sum(len(m.faces) for m in meshes)
    objects = len({m.name for m in meshes})
    obj_path, mtl_path = paths(glb_path)
    head = [
        *media_meta.obj_header(media_meta.record(rel(obj_path))),
        f"# {board}: Wavefront OBJ written from {glb_path.name} by _shared/export_obj.py "
        f"{EXPORTER_VERSION}",
        f"# Source: {glb_path.name}, sha256 {sha}",
        "# Units: millimeters (1 unit = 1 mm), as measurements.json; the GLB stores meters.",
        "# Axes as glTF, Y up: +Y up the screen, +Z out of the screen, +X to the device's right.",
        f"# {objects} objects, {vertices} vertices, {triangles} triangles; "
        f"materials in {stem}.mtl.",
    ]
    head.append(f"mtllib {stem}.mtl")
    lines = head
    normal_index: dict[str, int] = {}
    v_base = vt_base = 0
    previous = None
    for mesh in meshes:
        name = name_of(mesh.name)
        if name != previous:
            lines += [f"o {name}", f"g {name}"]
            previous = name
        lines.append(f"usemtl {material_of(mesh, js)}")
        lines.extend(f"v {row(p, POSITION_PLACES)}" for p in mesh.positions)
        if mesh.uv is not None:
            # glTF puts (0, 0) at the image's top left, OBJ at its bottom left
            lines.extend(f"vt {num(u, UV_PLACES)} {num(1.0 - v, UV_PLACES)}" for u, v in mesh.uv)
        ref = []
        for n in mesh.normals:
            key = row(n, NORMAL_PLACES)
            if key not in normal_index:
                normal_index[key] = len(normal_index) + 1
                lines.append(f"vn {key}")
            ref.append(normal_index[key])
        for a, b, c in mesh.faces.tolist():
            if mesh.uv is None:
                lines.append(
                    f"f {v_base + a + 1}//{ref[a]} {v_base + b + 1}//{ref[b]} "
                    f"{v_base + c + 1}//{ref[c]}"
                )
            else:
                lines.append(
                    f"f {v_base + a + 1}/{vt_base + a + 1}/{ref[a]} "
                    f"{v_base + b + 1}/{vt_base + b + 1}/{ref[b]} "
                    f"{v_base + c + 1}/{vt_base + c + 1}/{ref[c]}"
                )
        v_base += len(mesh.positions)
        if mesh.uv is not None:
            vt_base += len(mesh.uv)
    obj = ("\n".join(lines) + "\n").encode()
    mtl = mtl_text(
        board, glb_path.name, sha, js, media_meta.mtl_header(media_meta.record(rel(mtl_path)))
    ).encode()
    counts = {
        "objects": objects,
        "vertices": vertices,
        "normals": len(normal_index),
        "triangles": triangles,
        "materials": len(js.get("materials", [])),
    }
    return obj, mtl, counts


def paths(glb_path: Path) -> tuple[Path, Path]:
    """Where a master's OBJ and MTL go: beside it, under its name."""
    glb_path = Path(glb_path)
    return glb_path.with_suffix(".obj"), glb_path.with_suffix(".mtl")


def applies(output: str) -> bool:
    """True for a board's own master, ``<board>/model/<board>.glb`` (a spec's ``output``)."""
    parts = Path(output).parts
    return (
        len(parts) == 3
        and parts[1] == "model"
        and parts[2] == f"{parts[0]}.glb"
        and (ROOT / parts[0]).is_dir()
    )


def rel(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT).as_posix()


def record(glb_path: Path, obj: bytes, mtl: bytes, counts: dict[str, Any]) -> dict[str, Any]:
    """What ``source.json`` records of the two files under ``obj``."""
    obj_path, mtl_path = paths(glb_path)
    return {
        "exporter": {"script": "_shared/export_obj.py", "version": EXPORTER_VERSION},
        "units": "mm",
        "up": "+Y",
        "obj": rel(obj_path),
        "obj_sha256": hashlib.sha256(obj).hexdigest(),
        "obj_bytes": len(obj),
        "obj_gzip_bytes": len(gzip.compress(obj, compresslevel=9, mtime=0)),
        "mtl": rel(mtl_path),
        "mtl_sha256": hashlib.sha256(mtl).hexdigest(),
        "mtl_bytes": len(mtl),
        **counts,
    }


def write(glb_path: str | Path, board: str) -> dict[str, Any]:
    """Write the OBJ and MTL beside the master at *glb_path*; return their record."""
    glb_path = Path(glb_path)
    obj, mtl, counts = export(glb_path, board)
    obj_path, mtl_path = paths(glb_path)
    obj_path.write_bytes(obj)
    mtl_path.write_bytes(mtl)
    return record(glb_path, obj, mtl, counts)


def master(board: str) -> Path:
    """A board's master GLB, as its ``source.json`` names it."""
    rec = json.loads((ROOT / board / "model" / "source.json").read_text(encoding="utf-8"))
    return ROOT / str(rec["model"])


def problems(board: str) -> list[str]:
    """What differs between a board's committed OBJ, MTL and record and what its GLB gives."""
    glb = master(board)
    obj, mtl, counts = export(glb, board)
    obj_path, mtl_path = paths(glb)
    found = []
    for path, data in ((obj_path, obj), (mtl_path, mtl)):
        if not path.is_file():
            found.append(f"{rel(path)}: missing")
        elif path.read_bytes() != data:
            found.append(f"{rel(path)}: not what {glb.name} gives")
    rec = json.loads((ROOT / board / "model" / "source.json").read_text(encoding="utf-8"))
    if rec.get("obj") != record(glb, obj, mtl, counts):
        found.append(f"{board}/model/source.json: its obj record is not what {glb.name} gives")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("boards", nargs="*", help="board ids (default: all nine)")
    parser.add_argument(
        "--check", action="store_true", help="write nothing; exit 1 when a file or record differs"
    )
    args = parser.parse_args(argv)
    boards = args.boards or list(BOARDS)
    unknown = [b for b in boards if b not in BOARDS]
    if unknown:
        parser.error(f"not a board: {', '.join(unknown)}")
    failed = False
    for board in boards:
        if args.check:
            found = problems(board)
            for line in found:
                print(f"FAIL {line}")
            if not found:
                print(f"ok   {board}: OBJ and MTL are what its GLB gives")
            failed = failed or bool(found)
            continue
        glb = master(board)
        rec = write(glb, board)
        dest = ROOT / board / "model" / "source.json"
        data = json.loads(dest.read_text(encoding="utf-8"))
        data["obj"] = rec
        dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(
            f"wrote {rec['obj']} ({rec['obj_bytes']} bytes) and {rec['mtl']} "
            f"({rec['mtl_bytes']} bytes)"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
