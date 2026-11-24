# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Hold a board model's legends to where its drawings print them

A board's printed legends are drawn once, in its ``svg/front.svg`` (and in
``svg/back.svg`` for its back), and built into its model as flat meshes
(``legend_mesh.py``, ``build_board_glb.py``). This reads the two again, apart,
and measures one against the other in each drawing's own frame: the front
frame of ``measurements.json`` (mm, x across from the case's left edge, y down
from its top edge), or the back frame, x across from the left edge as seen
from behind (``board_faces.py``), placed by the frame ``source.json`` records:

- the drawing's legend groups, read as the builder reads them, each plane
  painted in the drawing's order, with no grid: what every key and every other
  print should show, ink by ink;
- the model's legend meshes as written, their quantized triangles joined into
  areas and placed in the front frame by the ``center_mm`` and ``front_frame``
  the model's ``source.json`` records.

Each piece of ink in the model goes to the group whose drawn ink it lies on.
For every group and ink, ``outline_mm`` is the Hausdorff distance between the
two outlines (the furthest any point of one lies from the other: a shift, a
stretch, a missing stroke and a wrong glyph all raise it) and ``shift_mm`` how
far the middle of the ink's box moved. A model is held to ``tolerance_mm``
(0.02: two position steps; rounding to the model's 0.01 mm grid and the
0.004 mm flattening of curves stay under it) on every group, and to more
besides: no group without its ink, no ink that belongs to no group, the same
inks as the drawing on each plane, every legend mesh flat at the height its
record gives and wearing an opaque material of its own ink's color and name,
the ``stroke_mm`` it carries true to its own area, facing out of its face
(its normals that face's, every triangle wound towards its viewer), and the
drawing still printing, on each plane, what the model was built from
(``legend_source.digest``: the legend groups and what places them, so a
drawing changed anywhere else is still the model's).

The model is read as a glTF reader draws it (``model_raster.read_glb``): a
mesh lies where its node and the nodes above it place it, so a legend moved by
a node's translation is as far off as one whose corners were moved.

``--selftest`` plants defects in a copy of the Cardputer ADV's model (a mesh
moved 0.05 mm, a key's legend taken out, two inks swapped, the legends scaled
by 0.2 %, a mesh lifted off its plane, a legend moved in the drawing after the
build, a ``stroke_mm`` that is not the mesh's, and, written into the file
itself, a legend's node and the root node given a translation of 0.06 mm and
an ink's material turned red), and in the back print of the two-face fixture
(``face_fixture.py``: mirrored, moved, lifted, wound inwards, turned, its
drawing moved, laid on its face, looked for from the front), and fails unless
the check catches each one,
passes the model as committed, and passes it against a drawing changed only
where no model reads (a callout, a hotspot, a cap).

Needs the builder's libraries (``build_board_glb.py``): numpy, shapely,
mapbox_earcut and fonttools.

Usage::

    python -I _shared/legend_placement.py \\
        <board> [--glb FILE] [--tolerance-mm X] [--json FILE]
    python -I _shared/legend_placement.py --selftest
"""

import argparse
import dataclasses
import json
import re
import sys
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import numpy.typing as npt
from shapely.geometry.base import BaseGeometry

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Every E402 below: the import follows the sys.path set-up above, which
# finds the sibling modules.
import board_faces  # noqa: E402
import glb_legends  # noqa: E402
import legend_mesh  # noqa: E402
import legend_source  # noqa: E402
import model_raster  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402
import shapely.affinity  # noqa: E402
import shapely.geometry as sg  # noqa: E402
from paths import OutsideError, in_tree, work_path  # noqa: E402

#: How far a group's ink may lie from where the drawing puts it, in mm.
TOLERANCE_MM = 0.02
#: The grid the drawing's own shapes are overlaid on: far under the model's.
DRAWING_GRID_MM = 0.0001
#: How far from a group's drawn ink a piece of the model's may lie and still
#: be that group's, in mm. Further off, it belongs to no group.
REACH_MM = 1.0


def _polygons(geom: BaseGeometry) -> list[sg.Polygon]:
    if geom.is_empty:
        return []
    if isinstance(geom, sg.Polygon):
        return [geom]
    return [p for g in getattr(geom, "geoms", []) for p in _polygons(g)]


def frame_of(record: dict[str, Any], face: str = "front") -> dict[str, Any]:
    """How glTF-frame mm map to the frame of one face's drawing (``board_faces.py``).

    For the front: x + dx across, dy - y down. For another face, the frame
    ``source.json`` records under ``parameters.face_frames``; with ``frame``,
    a ``board_faces.FaceFrame`` that places any face.
    """
    params = record.get("parameters", {})
    center, front = params.get("center_mm"), params.get("front_frame")
    if not center or not front:
        raise ValueError("source.json records no center_mm and front_frame")
    if face == "front":
        frame = board_faces.FaceFrame("front", front["left_x"], front["top_y"])
    else:
        numbers = (params.get("face_frames") or {}).get(face)
        if numbers is None:
            raise ValueError(f"source.json records no frame for the {face} face")
        frame = board_faces.face_frame(face, numbers)
    return {
        "dx": center[0] - front["left_x"],
        "dy": front["top_y"] - center[1],
        "center_z": center[2],
        "center": list(center),
        "face": face,
        "frame": frame,
        "quant_mm": params.get("quant_mm", 0.01),
    }


def drawing_of(entry: dict[str, Any]) -> str:
    """The drawing a legends record was read from, relative to the repository."""
    return str(entry.get("drawing", entry.get("front")))


def height_of(entry: dict[str, Any]) -> tuple[int, float]:
    """(the build-frame axis a legends record's sheets lie at a height on, that height)."""
    key = board_faces.height_key(entry.get("face", "front"))
    return board_faces.AXES.index(key), entry[f"{key}_mm"]


def ink_of(mesh: model_raster.Mesh) -> str:
    """The color a mesh is drawn in, as ``rrggbb`` (sRGB)."""
    return "".join(f"{round(float(c) * 255):02x}" for c in mesh.color)


def model_areas(
    meshes: list[model_raster.Mesh], place: dict[str, Any], prefix: str | None = None
) -> dict[str, tuple[BaseGeometry, float, float]]:
    """{legend mesh name: (its area in the face's drawing frame, its lowest, its highest)}.

    The lowest and highest are of the meshes' positions on the face's normal
    axis, center taken off (z on the front and the back). With *prefix*, only
    the legend meshes whose names start with it.

    The triangles are joined in whole position steps, where three corners in
    a line are exactly in a line, so two triangles that meet along part of an
    edge join with no crack between them; the area is then moved to mm. (No
    fixed-precision overlay: on a grid as coarse as the corners' own it folds
    away the thinnest triangles and splits what they hold together.)
    """
    step = place["quant_mm"]
    face = place.get("face", "front")
    axis = board_faces.normal(face)[0]
    if face == "front":
        across, down = place["dx"], place["dy"]
    else:
        du, dv = place["frame"].offsets(place["center"])
        across, down = -du, dv
    out = {}
    for mesh in meshes:
        if not glb_legends.is_legend(mesh.name) or not len(mesh.faces):
            continue
        if prefix is not None and not mesh.name.startswith(prefix):
            continue
        flat = board_faces.to_face(mesh.positions, face)
        tri = np.rint(flat[mesh.faces][..., :2] / step)
        area = shapely.union_all(shapely.polygons(tri))
        area = shapely.affinity.affine_transform(area, [step, 0, 0, -step, across, down])
        out[mesh.name] = (
            area,
            float(mesh.positions[:, axis].min()),
            float(mesh.positions[:, axis].max()),
        )
    return out


def facing_problems(mesh: model_raster.Mesh, face: str) -> list[str]:
    """What is wrong with the way a legend mesh faces, in words: [] when it faces out of *face*.

    Every vertex normal must be the face's outward normal, and every triangle
    wound counterclockwise as that face's viewer sees it, so a reader that
    culls back faces draws the print from the side it is printed on.
    """
    want = board_faces.basis(face)[2]
    out = []
    if len(mesh.normals) and not np.allclose(mesh.normals, want, atol=0.02):
        out.append(f"{mesh.name}: its normals are not {want.tolist()}, the {face} face's")
    if len(mesh.faces):
        tri = mesh.positions[mesh.faces]
        turn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]) @ want
        if (turn <= 0).any():
            out.append(
                f"{mesh.name}: {int((turn <= 0).sum())} of its {len(turn)} triangles are "
                f"wound to face away from the {face} face's viewer"
            )
    return out


def drawn_areas(
    legends: list[legend_mesh.Legend], plane: str
) -> tuple[dict[str, BaseGeometry], dict[str, dict[str, BaseGeometry]]]:
    """({fill: area}, {group name: {fill: area}}) of one plane of the drawing.

    The shapes are painted in the drawing's order, a later ink cutting an
    earlier one, as the builder paints them, on a grid far finer than the
    model's; each group then takes the part of every ink its own shapes cover.
    """
    chosen = [legend for legend in legends if legend.plane == plane]
    whole = legend_mesh.partition(chosen, lambda geom: geom, DRAWING_GRID_MM)
    groups: dict[str, dict[str, BaseGeometry]] = {}
    for legend in chosen:
        own: dict[str, list[BaseGeometry]] = {}
        for fill, geom in legend.shapes:
            own.setdefault(fill, []).append(geom)
        groups[legend.name] = {}
        for fill, shapes in own.items():
            cover = shapely.set_precision(shapely.union_all(shapes), DRAWING_GRID_MM)
            part = shapely.intersection(
                whole.get(fill, sg.Polygon()), cover, grid_size=DRAWING_GRID_MM
            )
            part = shapely.union_all(_polygons(part))
            if not part.is_empty:
                groups[legend.name][fill] = part
    return whole, groups


def assign(
    model_area: BaseGeometry, drawn: dict[str, BaseGeometry]
) -> tuple[dict[str, BaseGeometry], list[sg.Polygon]]:
    """({group: the model's ink that lies on its drawn ink}, pieces that lie on none).

    *drawn* is {group: area} for one ink. Each piece of the model's ink goes
    to the group whose drawn ink it covers most of, or, covering none, to the
    nearest within reach.
    """
    names = list(drawn)
    taken: dict[str, list[BaseGeometry]] = {name: [] for name in names}
    stray = []
    tree = shapely.STRtree([drawn[name] for name in names])
    for piece in _polygons(model_area):
        near = tree.query(piece.buffer(REACH_MM))
        best, score = None, None
        for index in near:
            target = drawn[names[index]]
            overlap = piece.intersection(target).area
            rank = (overlap, -piece.distance(target))
            if piece.distance(target) <= REACH_MM and (score is None or rank > score):
                best, score = names[index], rank
        if best is None:
            stray.append(piece)
        else:
            taken[best].append(piece)
    return {name: shapely.union_all(parts) for name, parts in taken.items() if parts}, stray


def outline_distance(a: BaseGeometry, b: BaseGeometry) -> float:
    """The Hausdorff distance between two areas' outlines, in mm."""
    return float(shapely.hausdorff_distance(a.boundary, b.boundary, densify=0.25))


def placement(
    meshes: list[model_raster.Mesh],
    extras: list[dict[str, Any]],
    front_svg: str | Path | Mapping[str, Path] | None,
    record: dict[str, Any],
    tolerance_mm: float = TOLERANCE_MM,
) -> dict[str, Any]:
    """Measure a model's legends against its front drawing.

    *meshes* is ``model_raster.read_glb`` of the model, *extras* what
    ``glb_legends.legends`` reads from it, *record* its ``source.json``.
    Returns a report: ``ok``; ``problems``, a list of what is wrong, in words;
    ``groups`` and ``keys``; ``worst_mm``, ``mean_mm`` and ``worst_group``
    (``outline_mm`` over every group); ``shift_worst_mm`` and
    ``shift_mean_mm``; ``meshes`` (each legends mesh's plane, height and
    inks); and ``per_group`` ({name: {plane, outline_mm, shift_mm}}).
    """
    place = frame_of(record)
    problems = []
    listed = record.get("legends") or []
    said = {entry["name"]: entry for entry in extras}
    drawn_as = {mesh.name: mesh for mesh in meshes if glb_legends.is_legend(mesh.name)}
    # each legend mesh in the frame of the face its record says it is printed on
    places = {"front": place}
    areas = model_areas(meshes, place)
    for entry in listed:
        face = entry.get("face", "front")
        if face not in places:
            try:
                places[face] = frame_of(record, face)
            except ValueError as exc:
                problems.append(f"{entry['mesh']}: {exc}")
                continue
        if face != "front":
            areas.update(model_areas(meshes, places[face], entry["mesh"] + "_"))
    report: dict[str, Any] = {
        "tolerance_mm": tolerance_mm,
        "front": None,
        "meshes": {},
        "per_group": {},
    }
    if not listed:
        if areas:
            problems.append("the model holds legend meshes its source.json does not record")
        report.update(ok=not problems, problems=problems, groups=0, keys=0)
        return report
    known = {
        f"{entry['mesh']}_{sheet['fill'][1:]}" for entry in listed for sheet in entry["sheets"]
    }
    problems.extend(
        f"{name}: a legend mesh its source.json does not record"
        for name in sorted(set(areas) - known)
    )
    drawings = {}
    planes_read: dict[
        tuple[Path, float], set[str]
    ] = {}  # (drawing, flatness) -> the planes of it a legends mesh draws
    for entry in listed:
        face = entry.get("face", "front")
        if face not in places:
            continue
        if front_svg is None:
            front = in_tree(drawing_of(entry))
        elif isinstance(front_svg, Mapping):
            front = Path(front_svg.get(face, in_tree(drawing_of(entry))))
        else:
            front = Path(front_svg) if face == "front" else in_tree(drawing_of(entry))
        key = (front, entry.get("flatness_mm", 0.004))
        if key not in drawings:
            drawings[key] = legend_mesh.read_legends(front, key[1])
        planes_read.setdefault(key, set()).add(entry["plane"])
        digest = legend_source.digest(front, entry["plane"])
        if digest != entry.get("legends_sha256"):
            problems.append(
                f"{drawing_of(entry)} no longer prints on the plane "
                f"{entry['plane']!r} what the model was built from (its legends "
                f"digest to {digest[:12]}, recorded "
                f"{str(entry.get('legends_sha256'))[:12]}): rebuild the model"
            )
        legends = drawings[key]
        if face == "front":
            report["front"] = entry["front"]
        else:
            report.setdefault("drawings", {})[face] = drawing_of(entry)
        whole, groups = drawn_areas(legends, entry["plane"])
        inks = {sheet["fill"][1:] for sheet in entry["sheets"]}
        if inks != set(whole):
            problems.append(
                f"{entry['mesh']}: inks {sorted(inks)} against the drawing's "
                f"{sorted(whole)} on the plane {entry['plane']!r}"
            )
        axis, at = height_of(entry)
        key_mm = f"{board_faces.AXES[axis]}_mm"
        height = at - place["center"][axis] if "center" in place else at - place["center_z"]
        report["meshes"][entry["mesh"]] = {
            "plane": entry["plane"],
            "on": entry["on"],
            key_mm: at,
            "groups": len(groups),
            "inks": sorted(f"#{ink}" for ink in inks),
        }
        if face != "front":
            report["meshes"][entry["mesh"]]["face"] = face
        for fill in sorted(inks | set(whole)):
            name = f"{entry['mesh']}_{fill}"
            if name not in areas:
                problems.append(f"{name}: the model has no such mesh")
                continue
            area, low, high = areas[name]
            if abs(low - height) > 1e-6 or abs(high - height) > 1e-6:
                problems.append(
                    f"{name}: lies at {board_faces.AXES[axis]} "
                    f"{low + at - height:.4f} to {high + at - height:.4f} mm, not "
                    f"flat at {at:g}"
                )
            problems += facing_problems(drawn_as[name], face)
            carried = (said.get(name) or {}).get("stroke_mm")
            width = legend_mesh.stroke_mm(area)
            if carried is None or abs(carried - width) > 0.0015:
                problems.append(f"{name}: carries stroke_mm {carried}, its area gives {width:.3f}")
            if (said.get(name) or {}).get("on") != entry["on"]:
                problems.append(
                    f"{name}: carries on {(said.get(name) or {}).get('on')!r}, "
                    f"recorded {entry['on']!r}"
                )
            # the ink: the color the mesh is drawn in, the material's name, what it says
            worn, material = drawn_as[name], (said.get(name) or {}).get("material")
            if ink_of(worn) != fill or worn.alpha < 1.0:
                problems.append(
                    f"{name}: is drawn in #{ink_of(worn)}"
                    + (f" at alpha {worn.alpha:g}" if worn.alpha < 1.0 else "")
                    + f" by its material {material!r}, not in its ink #{fill}"
                )
            if material != f"{glb_legends.INK_PREFIX}{fill}":
                problems.append(
                    f"{name}: wears the material {material!r}, not "
                    f"{glb_legends.INK_PREFIX + fill!r}"
                )
            if (said.get(name) or {}).get("fill") != f"#{fill}":
                problems.append(
                    f"{name}: carries fill {(said.get(name) or {}).get('fill')!r}, not #{fill}"
                )
            drawn = {group: inks_[fill] for group, inks_ in groups.items() if fill in inks_}
            taken, stray = assign(area, drawn)
            if stray:
                spot = stray[0].representative_point()
                problems.append(
                    f"{name}: {len(stray)} piece(s) of ink on no legend of the "
                    f"drawing, one at {face} ({spot.x:.2f}, {spot.y:.2f}) mm"
                )
            for group, want in drawn.items():
                row = report["per_group"].setdefault(
                    group, {"plane": entry["plane"], "outline_mm": 0.0, "shift_mm": 0.0}
                )
                got = taken.get(group)
                if got is None:
                    row["outline_mm"] = None
                    problems.append(f"{name}: nothing printed for {group!r}")
                    continue
                if row["outline_mm"] is not None:
                    row["outline_mm"] = round(
                        max(row["outline_mm"], outline_distance(want, got)), 4
                    )
                a, b = want.bounds, got.bounds
                shift = float(
                    np.hypot((b[0] + b[2] - a[0] - a[2]) / 2, (b[1] + b[3] - a[1] - a[3]) / 2)
                )
                row["shift_mm"] = round(max(row["shift_mm"], shift), 4)
        for legend in legends:
            if legend.plane == entry["plane"]:
                report["per_group"].setdefault(
                    legend.name, {"plane": legend.plane, "outline_mm": None, "shift_mm": None}
                )
    for key, legends in drawings.items():
        for plane in legend_mesh.planes(legends):
            if plane not in planes_read[key]:
                problems.append(
                    f"the drawing prints on the plane {plane!r}, which no legends "
                    f"mesh of the model draws"
                )
    measured = {g: row for g, row in report["per_group"].items() if row["outline_mm"] is not None}
    for group, row in sorted(report["per_group"].items()):
        if row["outline_mm"] is not None and row["outline_mm"] > tolerance_mm:
            problems.append(
                f"{group!r}: its print lies {row['outline_mm']:.3f} mm from the "
                f"drawing's, over {tolerance_mm:g} mm"
            )
    keys = {legend.name for legends in drawings.values() for legend in legends if legend.key}
    worst = max(measured, key=lambda g: measured[g]["outline_mm"], default=None)
    report.update(
        ok=not problems,
        problems=problems,
        groups=len(report["per_group"]),
        keys=len(keys & set(report["per_group"])),
        worst_group=worst,
        worst_mm=None if worst is None else measured[worst]["outline_mm"],
        mean_mm=round(float(np.mean([r["outline_mm"] for r in measured.values()])), 4)
        if measured
        else None,
        shift_worst_mm=max((r["shift_mm"] for r in measured.values()), default=None),
        shift_mean_mm=round(float(np.mean([r["shift_mm"] for r in measured.values()])), 4)
        if measured
        else None,
    )
    return report


def check(
    board_dir: str | Path, glb: str | Path | None = None, tolerance_mm: float = TOLERANCE_MM
) -> dict[str, Any] | None:
    """The placement report of a board directory's model (None when it prints nothing)."""
    board_dir = Path(board_dir)
    record = json.loads((Path(board_dir) / "model" / "source.json").read_text())
    glb = Path(glb) if glb else in_tree(record["model"])
    data = glb.read_bytes()
    extras = glb_legends.legends(glb_legends.read(data)[0])
    if not extras and not record.get("legends"):
        return None
    return placement(model_raster.read_glb(glb), extras, None, record, tolerance_mm)


def outlines(
    board_dir: str | Path, face: str = "front"
) -> list[tuple[str, str, list[npt.NDArray[np.float64]]]]:
    """[(plane, fill, rings)] of what a board's drawing of one face prints, for a picture.

    Each ring is an (N, 2) array in that drawing's frame, mm.
    """
    record = json.loads((Path(board_dir) / "model" / "source.json").read_text())
    out, read = [], {}
    for entry in record.get("legends") or []:
        if entry.get("face", "front") != face:
            continue
        key = (drawing_of(entry), entry.get("flatness_mm", 0.004))
        if key not in read:
            read[key] = legend_mesh.read_legends(in_tree(key[0]), key[1])
        whole, _ = drawn_areas(read[key], entry["plane"])
        for fill, area in sorted(whole.items()):
            rings = [
                np.asarray(ring.coords)
                for poly in _polygons(area)
                for ring in [poly.exterior, *poly.interiors]
            ]
            out.append((entry["plane"], fill, rings))
    return out


# ---------------------------------------------------------------- self-test


def _moved(
    mesh: model_raster.Mesh, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0, scale: float = 1.0
) -> model_raster.Mesh:
    positions = mesh.positions.copy()
    positions[:, :2] *= scale
    positions += np.array([dx, dy, dz])
    return dataclasses.replace(mesh, positions=positions)


def _drawing_plants(drawing: str) -> tuple[str, str]:
    """(a front with the Q key's legend moved 0.05 mm, a front changed where no model reads).

    The second is what regenerating a front gives when its legends did not
    change: a new callout, a new hotspot, a cap of another color.
    """
    moved, done = re.subn(
        r'(<g class="legend" data-key="Q">\s*<text x=")([0-9.]+)',
        lambda m: f"{m.group(1)}{float(m.group(2)) + 0.05:.2f}",
        drawing,
        count=1,
    )
    if not done:
        raise ValueError("the drawing has no Q key whose legend is a text")
    elsewhere = drawing
    for mark, added in (
        (
            '<g id="annotations">',
            '<text x="0" y="0" font-size="2" fill="#000000">a new callout</text>',
        ),
        (
            '<g id="hotspots" display="none">',
            '<circle id="hs-Planted" cx="1" cy="1" r="1" data-face="front" data-w="2" data-h="2"/>',
        ),
    ):
        if elsewhere.count(mark) != 1:
            raise ValueError(f"the drawing does not hold {mark} once")
        elsewhere = elsewhere.replace(mark, f"{mark}\n{added}")
    # the first cap the drawing fills, outside every legend group
    elsewhere, done = re.subn(
        r'(<rect [^>]*fill=")#171719(")', r"\g<1>#27272a\g<2>", elsewhere, count=1
    )
    if not done:
        raise ValueError("the drawing has no cap of the color this plant repaints")
    return moved, elsewhere


def _rewritten(
    glb: str | Path, change: Callable[[dict[str, Any]], None], out: str | Path
) -> tuple[list[model_raster.Mesh], list[dict[str, Any]]]:
    """A copy of a model with *change* made to its JSON chunk: (its meshes, its legends' extras)."""
    js, bin_ = glb_legends.read(Path(glb).read_bytes())
    change(js)
    with open(out, "wb") as fh:
        fh.write(glb_legends.write(js, bin_))
    return model_raster.read_glb(out), glb_legends.legends(js)


def selftest(
    board: str = "cardputer",
) -> tuple[dict[str, Any], list[tuple[str, bool, str]], list[tuple[str, bool, str]]]:
    """Plant defects in a board's committed model: (the clean report, the plants, the controls).

    The plants are ``[(what, caught, how)]``, each of which the check must
    fail; the controls ``[(what, passed, how)]``, changes that are no defect
    and that it must pass, as it passes the model as committed.
    """
    board_dir = HERE.parent / board
    record = json.loads((Path(board_dir) / "model" / "source.json").read_text())
    glb = in_tree(record["model"])
    extras = glb_legends.legends(glb_legends.read(glb.read_bytes())[0])
    meshes = model_raster.read_glb(glb)
    names = [m.name for m in meshes if glb_legends.is_legend(m.name)]
    first, second = names[0], names[1]
    place = frame_of(record)
    legends = legend_mesh.read_legends(
        in_tree(record["legends"][0]["front"]), record["legends"][0].get("flatness_mm", 0.004)
    )
    key = next(legend for legend in legends if legend.key and legend.name == "Q")
    box = shapely.union_all([geom for _, geom in key.shapes]).buffer(0.2)

    def without_key(mesh: model_raster.Mesh) -> model_raster.Mesh:
        tri = mesh.positions[mesh.faces].mean(axis=1)
        inside = shapely.contains_xy(box, tri[:, 0] + place["dx"], place["dy"] - tri[:, 1])
        return dataclasses.replace(mesh, faces=mesh.faces[~inside])

    def swap(mesh: model_raster.Mesh) -> model_raster.Mesh:
        return dataclasses.replace(
            mesh, name={first: second, second: first}.get(mesh.name, mesh.name)
        )

    def each(
        change: Callable[[model_raster.Mesh], model_raster.Mesh], only: str | None = None
    ) -> list[model_raster.Mesh]:
        return [
            change(m) if glb_legends.is_legend(m.name) and only in (None, m.name) else m
            for m in meshes
        ]

    thin = [
        dict(entry, stroke_mm=(entry["stroke_mm"] or 0) + 0.05) if entry["name"] == first else entry
        for entry in extras
    ]
    drawing = in_tree(record["legends"][0]["front"]).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="legend-selftest-") as tmp:
        moved_front, elsewhere_front = Path(tmp) / "moved.svg", Path(tmp) / "elsewhere.svg"
        for path, text in zip(
            (moved_front, elsewhere_front), _drawing_plants(drawing), strict=True
        ):
            path.write_text(text, encoding="utf-8")

        # planted in the file itself, where a reader of the model meets them
        def node_moved(js: dict[str, Any], name: str = first) -> None:
            node = next(n for n in js["nodes"] if n.get("name") == name)
            node["translation"] = [0.06 * model_raster.MM, 0.0, 0.0]

        def root_moved(js: dict[str, Any]) -> None:
            js["nodes"][js["scenes"][0]["nodes"][0]]["translation"] = [
                0.06 * model_raster.MM,
                0.0,
                0.0,
            ]

        def ink_turned_red(js: dict[str, Any], name: str = first) -> None:
            node = next(n for n in js["nodes"] if n.get("name") == name)
            material = js["meshes"][node["mesh"]]["primitives"][0]["material"]
            js["materials"][material]["pbrMetallicRoughness"]["baseColorFactor"] = [
                1.0,
                0.0,
                0.0,
                1.0,
            ]

        files = {
            change.__name__: _rewritten(glb, change, Path(tmp) / f"{change.__name__}.glb")
            for change in (node_moved, root_moved, ink_turned_red)
        }
        # what is planted, the model, its extras, its drawing (None: the committed one), and
        # words of the problem it must raise
        plants = [
            (
                "one legend mesh moved 0.05 mm across",
                each(lambda m: _moved(m, dx=0.05), first),
                extras,
                None,
                "its print lies",
            ),
            (
                "the Q key's legend taken out",
                each(without_key),
                extras,
                None,
                "nothing printed for 'Q'",
            ),
            ("two inks swapped", each(swap), extras, None, "nothing printed for"),
            (
                "the legends scaled by 0.2 %",
                each(lambda m: _moved(m, scale=1.002)),
                extras,
                None,
                "its print lies",
            ),
            (
                "one legend mesh lifted 0.01 mm off its plane",
                each(lambda m: _moved(m, dz=0.01), first),
                extras,
                None,
                "not flat at",
            ),
            (
                "the Q key's legend moved 0.05 mm in the drawing after the build",
                meshes,
                extras,
                moved_front,
                "what the model was built from",
            ),
            ("a stroke_mm that is not the mesh's", meshes, thin, None, "carries stroke_mm"),
            (
                "one legend mesh moved 0.06 mm by its node's translation",
                *files["node_moved"],
                None,
                "its print lies",
            ),
            (
                "the whole model moved 0.06 mm by its root node's translation",
                *files["root_moved"],
                None,
                "its print lies",
            ),
            ("an ink's material turned red", *files["ink_turned_red"], None, "not in its ink"),
        ]
        clean = placement(meshes, extras, None, record)
        results = []
        for what, planted, said, front, words in plants:
            got = placement(planted, said, front, record)
            raised = [problem for problem in got["problems"] if words in problem]
            results.append(
                (
                    what,
                    bool(raised) and not got["ok"],
                    raised[0] if raised else f"no problem saying {words!r}",
                )
            )
        # what is no defect: the check must pass it
        controls = []
        for what, front in (
            (
                "the drawing changed where no model reads (a callout, a hotspot, a cap)",
                elsewhere_front,
            ),
        ):
            got = placement(meshes, extras, front, record)
            controls.append(
                (what, got["ok"], "no problem" if got["ok"] else "; ".join(got["problems"][:2]))
            )
    return clean, results, controls


#: The board of two boxes that prints on its front and its back (``face_fixture.py``).
FACE_FIXTURE = HERE / "fixtures" / "faces"


def _clearance(
    meshes: list[model_raster.Mesh], prefix: str, step: float, on: str, face: str = "front"
) -> dict[str, Any]:
    """``model_raster.legend_clearance`` of a model whose legends are there to measure."""
    found = model_raster.legend_clearance(meshes, prefix, step, on=on, face=face)
    if found is None:
        raise AssertionError(f"no {prefix}* legend mesh to measure")
    return found


def faces_selftest(
    board_dir: str | Path = FACE_FIXTURE,
) -> tuple[dict[str, Any], list[tuple[str, bool, str]], list[tuple[str, bool, str]]]:
    """Plant defects in the back print of the two-face fixture: (the clean report, plants,
    controls).

    The fixture prints an ``F`` and ``K1`` on its back (``face_fixture.py``),
    built into the model from the back's own drawing. The placement check
    must find each of: the back print mirrored across the case (laid with the
    front's frame, the one mistake a back drawing invites), moved 0.05 mm,
    lifted off its plane, its triangles wound to face into the case, its
    normals turned to the front, and the back drawing moved after the build;
    the clearance check must find the back print laid on the base's face it
    is printed on, and must not take the front's way of looking for the back's.
    """
    record = json.loads((Path(board_dir) / "model" / "source.json").read_text())
    glb = in_tree(record["model"])
    extras = glb_legends.legends(glb_legends.read(glb.read_bytes())[0])
    meshes = model_raster.read_glb(glb)
    back = next(entry for entry in record["legends"] if entry.get("face") == "back")
    prefix = back["mesh"] + "_"
    step = record["parameters"]["quant_mm"]

    def each(change: Callable[[model_raster.Mesh], model_raster.Mesh]) -> list[model_raster.Mesh]:
        return [change(m) if m.name.startswith(prefix) else m for m in meshes]

    def mirrored(mesh: model_raster.Mesh) -> model_raster.Mesh:
        positions = mesh.positions.copy()
        positions[:, 0] *= -1  # about the case's middle, which the fixture's center is on
        return dataclasses.replace(mesh, positions=positions, faces=mesh.faces[:, ::-1].copy())

    def rewound(mesh: model_raster.Mesh) -> model_raster.Mesh:
        return dataclasses.replace(mesh, faces=mesh.faces[:, ::-1].copy())

    def turned(mesh: model_raster.Mesh) -> model_raster.Mesh:
        return dataclasses.replace(mesh, normals=-mesh.normals)

    drawing = in_tree(back["drawing"]).read_text(encoding="utf-8")
    moved_drawing, done = re.subn(r'points="3,3 ', 'points="3.05,3 ', drawing, count=1)
    if not done:
        raise ValueError("the fixture's back drawing has no F where this plant moves it")
    with tempfile.TemporaryDirectory(prefix="faces-selftest-") as tmp:
        moved_back = Path(tmp) / "back.svg"
        moved_back.write_text(moved_drawing, encoding="utf-8")
        plants = [
            (
                "the back print laid mirrored across the case",
                each(mirrored),
                None,
                "on no legend of the drawing",
            ),
            (
                "the back print moved 0.05 mm across",
                each(lambda m: _moved(m, dx=0.05)),
                None,
                "its print lies",
            ),
            (
                "the back print lifted 0.01 mm off its plane",
                each(lambda m: _moved(m, dz=0.01)),
                None,
                "not flat at",
            ),
            (
                "the back print wound to face into the case",
                each(rewound),
                None,
                "wound to face away",
            ),
            (
                "the back print's normals turned to the front",
                each(turned),
                None,
                "its normals are not",
            ),
            (
                "the back drawing moved 0.05 mm after the build",
                meshes,
                {"back": moved_back},
                "what the model was built from",
            ),
        ]
        clean = placement(meshes, extras, None, record)
        results = []
        for what, planted, drawings, words in plants:
            got = placement(planted, extras, drawings, record)
            raised = [problem for problem in got["problems"] if words in problem]
            results.append(
                (
                    what,
                    bool(raised) and not got["ok"],
                    raised[0] if raised else f"no problem saying {words!r}",
                )
            )
    gap = _clearance(meshes, prefix, step, on=back["on"], face="back")
    sunk = _clearance(
        each(lambda m: _moved(m, dz=3 * step)), prefix, step, on=back["on"], face="back"
    )
    results.append(
        (
            "the back print laid on the face it is printed on",
            not sunk["ok"],
            f"{sunk['under_mm']} mm over {sunk['under_mesh']}",
        )
    )
    as_front = _clearance(meshes, prefix, step, on=back["on"])
    results.append(
        (
            "the back print looked for from the front",
            not as_front["ok"],
            f"over: {as_front['over_mesh']}, under: {as_front['under_mesh']}",
        )
    )
    controls = [
        (
            "the back print as built, from the back",
            gap["ok"],
            f"{gap['under_mm']} mm over {gap['under_mesh']}",
        )
    ]
    return clean, results, controls


def main(argv: list[str] | None = None) -> int:
    """Check a board's legends from the command line; return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    subject = parser.add_mutually_exclusive_group(required=True)
    subject.add_argument("board_dir", type=Path, nargs="?", help="<board>")
    parser.add_argument("--glb", type=Path, help="the model (default: source.json's)")
    parser.add_argument("--tolerance-mm", type=float, default=TOLERANCE_MM)
    parser.add_argument("--json", type=Path, help="write the report here")
    subject.add_argument(
        "--selftest",
        action="store_true",
        help="plant defects in the Cardputer ADV model and in the back print of "
        "the two-face fixture, and expect each caught",
    )
    args = parser.parse_args(argv)
    if args.selftest:
        good = True
        for label, (clean, results, controls) in (
            ("the Cardputer ADV", selftest()),
            ("the two-face fixture", faces_selftest()),
        ):
            print(
                f"{label} as committed: {'passes' if clean['ok'] else 'FAILS'} "
                f"({clean['groups']} groups, worst {clean['worst_mm']} mm)"
            )
            for problem in clean["problems"]:
                print(f"  {problem}")
            for what, caught, how in results:
                print(f"{'caught' if caught else 'MISSED'}: {what} -> {how}")
            for what, passed, how in controls:
                print(f"{'passed' if passed else 'FAILED'}: {what} -> {how}")
            good = good and (
                clean["ok"]
                and all(caught for _, caught, _ in results)
                and all(passed for _, passed, _ in controls)
            )
        print("selftest " + ("passed" if good else "FAILED"))
        return 0 if good else 1
    try:
        board_dir = work_path(args.board_dir)
        glb = None if args.glb is None else work_path(args.glb)
        out = None if args.json is None else work_path(args.json)
    except OutsideError as exc:
        parser.error(str(exc))
    report = check(board_dir, glb, args.tolerance_mm)
    if report is None:
        print(f"{board_dir.name}: the model prints nothing")
        return 0
    if out is not None:
        out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "per_group"}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
