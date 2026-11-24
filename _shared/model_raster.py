# SPDX-License-Identifier: MIT AND Apache-2.0
"""Z-buffered orthographic pictures of a board model written by ``build_board_glb.py``

Reads a ``.glb`` straight from its buffers (quantized or float positions, the
vertex normals the builder wrote, the ``screen`` mesh's UVs and each material's
base color), each mesh where its node and the nodes it hangs from place it, as
any glTF reader places it, and rasterizes it with a depth buffer, so a large
face never paints over a nearer small one, whatever the order. Faces whose
material is not double-sided are drawn from the front only, as a GPU culling
back faces draws them (the film's own renderer does).

Two passes, as a glTF reader draws ``alphaMode: BLEND``: every opaque mesh
first, writing depth; then every blended mesh, farthest first by the depth of
its box's center (three.js's order for what it blends), each triangle in its
own order, tested against the opaque depth and writing none, its color laid
over what is there by its alpha (straight alpha, in the shaded colors, as a
blend into an sRGB canvas lays it). The glass contract's ``glass`` mesh is left
out: a page draws its own cover glass over the capture.

A lit face is shaded in linear light and tone mapped as the landing film's own
renderer tone maps its case (the Kleidos repository's ``site/src/scripts/film/gl/shaders.ts``): an
ambient and one key light, scaled so a face toward the viewer is under unit
white light; a dielectric's 4 % reflection over it, and a highlight; then the
Khronos PBR Neutral tone mapper and the sRGB transfer. A face toward the viewer
so shows its base color, which for a case is the color measured on the board,
as the film shows it.

The ``screen`` mesh can carry a test card through its UVs: the panel's pixels
split into four colored quadrants with a white corner mark on the image's
top-left, so a picture shows at a glance that a capture would read upright
(``build_board_glb.py``'s glass contract).

Three checks of a written model live here too, because they read it the same
way: ``screen_clearance`` (the glass contract's gap either side of the screen),
``legend_clearance`` (the gap under a model's legends, that nothing lies over
them, and that each lies on the mesh it is printed on) and
``coplanar_overlaps`` (no two meshes of different materials covering one place
at one depth, with ``coplanar_selftest``, the depth ties it must catch). The
builder runs all three on what it wrote.

Used by ``check_board_model.py`` (its three views) and
``models_contact_sheet.py`` (every board side by side). Needs numpy only.
"""

import json
import math
import struct
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

MM = 0.001
_COMPONENTS = {
    5120: np.int8,
    5121: np.uint8,
    5122: np.int16,
    5123: np.uint16,
    5125: np.uint32,
    5126: np.float32,
}
_WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
#: Test-card quadrant colors (sRGB 0-1): top-left, top-right, bottom-left, bottom-right.
CARD_COLORS = ((0.13, 0.31, 0.75), (0.75, 0.19, 0.19), (0.19, 0.63, 0.25), (0.82, 0.75, 0.19))
#: The ambient light and the key light's share of a lit face's light, before the
#: whole is scaled so a face toward the viewer takes exactly one.
AMBIENT, KEY = 0.36, 0.64
#: A dielectric's reflection at normal incidence, which PBR Neutral takes away.
F0 = 0.04


@dataclass
class Mesh:
    """One node of a board model, positions in mm in the glTF frame."""

    name: str
    positions: np.ndarray
    normals: np.ndarray
    faces: np.ndarray
    uv: np.ndarray | None
    color: np.ndarray
    alpha: float
    metal: float
    rough: float
    unlit: bool
    double: bool
    #: The name of its material (``#<index>`` for one with no name).
    material: str = ""


def linear_to_srgb(c: npt.ArrayLike) -> npt.NDArray[np.float64]:
    x: npt.NDArray[np.float64] = np.clip(np.asarray(c, dtype=float), 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def srgb_to_linear(c: npt.ArrayLike) -> npt.NDArray[np.float64]:
    x: npt.NDArray[np.float64] = np.clip(np.asarray(c, dtype=float), 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def pbr_neutral(c: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """Khronos PBR Neutral on linear Rec. 709 colors (rows of r, g, b): the
    function of ``PBR_Neutral/pbrNeutral.glsl`` in KhronosGroup/ToneMapping
    (Apache License 2.0, Copyright 2024 The Khronos Group Inc.), operation for
    operation, on arrays; the film's lit shader runs the same."""
    c = np.asarray(c, dtype=float)
    start, desaturation = 0.8 - 0.04, 0.15
    x = c.min(axis=-1, keepdims=True)
    c = c - np.where(x < 0.08, x - 6.25 * x * x, 0.04)
    peak = c.max(axis=-1, keepdims=True)
    d = 1.0 - start
    new_peak = 1.0 - d * d / (peak + d - start)
    g = 1.0 - 1.0 / (desaturation * (peak - new_peak) + 1.0)
    compressed = c * (new_peak / np.where(peak > 0, peak, 1.0)) * (1 - g) + new_peak * g
    return np.where(peak < start, c, compressed)


def _accessor(js: dict[str, Any], bin_: bytes, index: int) -> npt.NDArray[Any]:
    acc = js["accessors"][index]
    bv = js["bufferViews"][acc["bufferView"]]
    dt = np.dtype(_COMPONENTS[acc["componentType"]])
    width = _WIDTH[acc["type"]]
    stride = bv.get("byteStride", width * dt.itemsize) // dt.itemsize
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    arr = np.frombuffer(bin_, dtype=dt, count=acc["count"] * stride, offset=off)
    arr = arr.reshape(acc["count"], stride)[:, :width].astype(float)
    if acc.get("normalized"):
        arr = np.clip(arr / float(np.iinfo(dt.type).max), -1.0, 1.0)
    return arr


#: What a node may carry, beside its ``scale``, that places its mesh.
_PLACING = ("matrix", "translation", "rotation")


def _local(node: dict[str, Any]) -> npt.NDArray[np.float64]:
    """A node's own transform as a 4 x 4 matrix: its ``matrix`` (stored by
    columns), or its translation, rotation and scale composed as glTF composes
    them (T R S)."""
    if "matrix" in node:
        return np.array(node["matrix"], dtype=float).reshape(4, 4).T
    out = np.eye(4)
    if "rotation" in node:
        x, y, z, w = (float(v) for v in node["rotation"])
        out[:3, :3] = [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    out[:3, :3] *= np.array(node.get("scale", [1.0, 1.0, 1.0]), dtype=float)
    out[:3, 3] = node.get("translation", [0.0, 0.0, 0.0])
    return out


def _placements(nodes: list[dict[str, Any]]) -> dict[int, npt.NDArray[np.float64] | None]:
    """{node index: its 4 x 4 world matrix, or None when its own scale is all that places it}.

    A model the builder writes hangs every mesh from one root, a mesh node
    carrying a scale (its quantization step) and nothing else: those keep the
    arithmetic they always had, a position times its node's scale. Any other
    node (one with a translation, a rotation or a matrix, or under a node that
    carries any transform) gets its whole world matrix, so a model is read as
    a glTF reader draws it and a check run on these meshes sees a node moved
    by its transform.
    """
    above = {child: index for index, node in enumerate(nodes) for child in node.get("children", [])}
    out: dict[int, npt.NDArray[np.float64] | None] = {}
    for index, node in enumerate(nodes):
        chain = [index]
        while chain[-1] in above and above[chain[-1]] not in chain:
            chain.append(above[chain[-1]])
        if not any(key in node for key in _PLACING) and not any(
            key in nodes[i] for i in chain[1:] for key in (*_PLACING, "scale")
        ):
            out[index] = None
            continue
        world = np.eye(4)
        for i in reversed(chain):
            world = world @ _local(nodes[i])
        out[index] = world
    return out


def read_glb(path: str | Path) -> list[Mesh]:
    """[Mesh] of a GLB, each mesh where its node and the nodes above it place it."""
    raw = Path(path).read_bytes()
    if struct.unpack_from("<I", raw, 0)[0] != 0x46546C67:
        raise ValueError(f"{path}: not a GLB")
    jlen = struct.unpack_from("<I", raw, 12)[0]
    js = json.loads(raw[20 : 20 + jlen])
    bin_ = raw[20 + jlen + 8 :]
    placed = _placements(js["nodes"])
    out = []
    for index, node in enumerate(js["nodes"]):
        if "mesh" not in node:
            continue
        world = placed[index]
        scale = np.array(node.get("scale", [1.0, 1.0, 1.0])) / MM
        for prim in js["meshes"][node["mesh"]]["primitives"]:
            attrs = prim["attributes"]
            pos = _accessor(js, bin_, attrs["POSITION"])
            nrm = _accessor(js, bin_, attrs["NORMAL"])
            if world is None:
                pos = pos * scale
            else:
                pos = (pos @ world[:3, :3].T + world[:3, 3]) / MM
                # a normal turns with the inverse transpose of what moves the points
                nrm = nrm @ np.linalg.inv(world[:3, :3])
            nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
            uv = _accessor(js, bin_, attrs["TEXCOORD_0"]) if "TEXCOORD_0" in attrs else None
            faces = _accessor(js, bin_, prim["indices"]).astype(np.int64).reshape(-1, 3)
            mat = js["materials"][prim["material"]] if "material" in prim else {}
            pbr = mat.get("pbrMetallicRoughness", {})
            f = pbr.get("baseColorFactor", [0.6, 0.6, 0.6, 1.0])
            out.append(
                Mesh(
                    name=node.get("name", ""),
                    positions=pos,
                    normals=nrm,
                    faces=faces,
                    uv=uv,
                    color=linear_to_srgb(f[:3]),
                    alpha=f[3] if mat.get("alphaMode") == "BLEND" else 1.0,
                    metal=float(pbr.get("metallicFactor", 1.0)),
                    rough=float(pbr.get("roughnessFactor", 1.0)),
                    unlit="KHR_materials_unlit" in mat.get("extensions", {}),
                    double=bool(mat.get("doubleSided", False)),
                    material=mat.get("name", f"#{prim.get('material', '')}"),
                )
            )
    return out


def _clip_to_box(
    points: npt.NDArray[np.float64], box: tuple[float, float, float, float]
) -> list[npt.NDArray[np.float64]]:
    """The part of a polygon (rows of x, y, z) inside x0 <= x <= x1, y0 <= y <= y1
    (Sutherland-Hodgman, plane by plane, so an upright face clips too)."""
    x0, x1, y0, y1 = box
    poly: list[npt.NDArray[np.float64]] = [np.asarray(p, dtype=float) for p in points]
    for axis, bound, keep_above in ((0, x0, True), (0, x1, False), (1, y0, True), (1, y1, False)):
        if not poly:
            break
        out = []
        for i, cur in enumerate(poly):
            prev = poly[i - 1]
            cur_in = cur[axis] >= bound if keep_above else cur[axis] <= bound
            prev_in = prev[axis] >= bound if keep_above else prev[axis] <= bound
            if cur_in != prev_in:
                t = (bound - prev[axis]) / (cur[axis] - prev[axis])
                out.append(prev + t * (cur - prev))
            if cur_in:
                out.append(cur)
        poly = out
    return poly


def screen_clearance(meshes: list[Mesh], quant_mm: float) -> dict[str, Any] | None:
    """How far from the ``screen`` quad's plane the nearest faces lie, either side.

    A face of any other mesh counts when part of it lies inside the screen's
    rectangle seen from the front, that rectangle less half a quantization step
    on each side (the most a quantized vertex moves, so a face that only reaches
    in by rounding is left out). A face behind the plane is under the screen
    (the LCD, the filler); one in front of it is the glass, or covers part of
    the screen (a bezel lip over the active area's corners). A depth-tested
    renderer keeps them apart only when each is at least one quantization step
    (*quant_mm*) off the plane: nearer than that, the face rounds to the
    screen's own depth and the capture flickers or vanishes. A face that
    crosses the plane is 0 off it.

    Returns None for a model with no ``screen`` mesh, else a dict:
    ``screen_z_mm``; ``behind_mm`` and ``behind_mesh``, the nearest face under
    the screen; ``in_front_mm`` and ``in_front_mesh``, the nearest face over it
    (None when there is none); ``quant_mm``; and ``ok``, true when both are at
    least *quant_mm*.
    """
    screens = [m for m in meshes if m.name == "screen"]
    if not screens:
        return None
    screen = screens[0]
    lo = screen.positions[:, :2].min(axis=0)
    hi = screen.positions[:, :2].max(axis=0)
    inset = quant_mm / 2
    box = (lo[0] + inset, hi[0] - inset, lo[1] + inset, hi[1] - inset)
    plane = float(screen.positions[:, 2].min())
    nearest: dict[str, tuple[float | None, str | None]] = {
        "behind": (None, None),
        "in_front": (None, None),
    }
    for m in meshes:
        if m is screen or not len(m.faces):
            continue
        tri = m.positions[m.faces]
        t_lo, t_hi = tri.min(axis=1), tri.max(axis=1)
        near = (
            (t_hi[:, 0] >= box[0])
            & (t_lo[:, 0] <= box[1])
            & (t_hi[:, 1] >= box[2])
            & (t_lo[:, 1] <= box[3])
        )
        for corners in tri[near]:
            part = _clip_to_box(corners, box)
            if not part:
                continue
            z = np.array([p[2] for p in part])
            if z.max() <= plane:
                side, gap = "behind", plane - float(z.max())
            elif z.min() >= plane:
                side, gap = "in_front", float(z.min()) - plane
            else:
                side, gap = ("behind" if plane - z.min() >= z.max() - plane else "in_front"), 0.0
            best = nearest[side][0]
            if best is None or gap < best:
                nearest[side] = (gap, m.name)
    out: dict[str, Any] = {"screen_z_mm": round(plane, 6)}
    ok = True
    for side in ("behind", "in_front"):
        side_gap, name = nearest[side]
        out[f"{side}_mm"] = None if side_gap is None else round(side_gap, 6)
        out[f"{side}_mesh"] = name
        # 1e-6 mm absorbs the float32 rounding of the screen's own depth
        ok = ok and (side_gap is None or side_gap >= quant_mm - 1e-6)
    out["quant_mm"] = quant_mm
    out["ok"] = ok
    return out


def legend_clearance(
    meshes: list[Mesh],
    prefix: str,
    quant_mm: float,
    steps: int = 2,
    on: str | None = None,
    face: str = "front",
) -> dict[str, Any] | None:
    """How far over the rest of the model the legends lie, and whether anything covers them.

    The legends are the meshes whose names start with *prefix*: flat sheets a
    hair over the faces they are printed on (``legend_mesh.py``). Under the
    center of each of their triangles, the nearest face of any other opaque
    mesh is found; a depth-tested renderer keeps the two apart only while that
    gap is more than a step of its depth buffer, so it must be at least *steps*
    quantization steps (*quant_mm* each). A face over a triangle's center
    hides that part of a legend, which no drawing means. Upright faces cover
    nothing seen from the front and are left out, as are the blended meshes
    and the ``glass``. With *on*, the name of the mesh the legends are printed
    on, every triangle's center must also have a face of that mesh under it:
    a legend that hangs past its key, or lies on another part, is found.

    Returns None for a model with no such mesh, else a dict: ``triangles``;
    ``under_mm`` and ``under_mesh``, the nearest face under a legend (None when
    nothing lies under any); ``over_mm`` and ``over_mesh``, the nearest face
    over one (None when none does); ``on`` and ``off``, the mesh the legends
    are printed on and how many triangles have no face of it under them (0
    with no *on*); ``quant_mm``, ``least_mm``; and ``ok``, true when a face
    lies under the legends, the nearest one at least ``least_mm`` away, none
    lies over them, and none is off its mesh.

    *face* is the face of the board the legends are printed on
    (``board_faces.FACES``): "under" is behind the print as that face's viewer
    sees it, "over" between the print and that viewer, and an upright face is
    one along that face's normal. The front is measured along +Z as it always
    was; another face's meshes are first turned into that face's frame.
    """
    legends = [m for m in meshes if m.name.startswith(prefix) and len(m.faces)]
    if not legends:
        return None
    if face != "front":
        import dataclasses

        import board_faces

        meshes = [
            dataclasses.replace(m, positions=board_faces.to_face(m.positions, face)) for m in meshes
        ]
        legends = [m for m in meshes if m.name.startswith(prefix) and len(m.faces)]
    cent = np.concatenate([m.positions[m.faces].mean(axis=1) for m in legends])
    lo, hi = cent[:, :2].min(axis=0), cent[:, :2].max(axis=0)
    nearest: dict[str, tuple[float | None, str | None]] = {
        "under": (None, None),
        "over": (None, None),
    }
    printed_on = np.zeros(len(cent), dtype=bool)
    for m in meshes:
        if m.name.startswith(prefix) or m.name == "glass" or m.alpha < 1.0 or not len(m.faces):
            continue
        tri = m.positions[m.faces]
        t_lo, t_hi = tri.min(axis=1), tri.max(axis=1)
        near = (
            (t_hi[:, 0] >= lo[0])
            & (t_lo[:, 0] <= hi[0])
            & (t_hi[:, 1] >= lo[1])
            & (t_lo[:, 1] <= hi[1])
        )
        for (a, b, c), b_lo, b_hi in zip(tri[near], t_lo[near], t_hi[near], strict=True):
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-12:
                continue
            at = np.flatnonzero(
                (cent[:, 0] >= b_lo[0])
                & (cent[:, 0] <= b_hi[0])
                & (cent[:, 1] >= b_lo[1])
                & (cent[:, 1] <= b_hi[1])
            )
            if not len(at):
                continue
            p = cent[at]
            wa = ((b[1] - c[1]) * (p[:, 0] - c[0]) + (c[0] - b[0]) * (p[:, 1] - c[1])) / den
            wb = ((c[1] - a[1]) * (p[:, 0] - c[0]) + (a[0] - c[0]) * (p[:, 1] - c[1])) / den
            wc = 1 - wa - wb
            inside = (wa >= 0) & (wb >= 0) & (wc >= 0)
            if not inside.any():
                continue
            gap = p[inside, 2] - (wa[inside] * a[2] + wb[inside] * b[2] + wc[inside] * c[2])
            if m.name == on:
                printed_on[at[inside][gap >= 0]] = True
            for side, found in (("under", gap[gap >= 0]), ("over", -gap[gap < 0])):
                best = nearest[side][0]
                if len(found) and (best is None or found.min() < best):
                    nearest[side] = (float(found.min()), m.name)
    least = steps * quant_mm
    under, over = nearest["under"], nearest["over"]
    off = 0 if on is None else int((~printed_on).sum())
    return {
        "triangles": int(len(cent)),
        "under_mm": None if under[0] is None else round(under[0], 6),
        "under_mesh": under[1],
        "over_mm": None if over[0] is None else round(over[0], 6),
        "over_mesh": over[1],
        "on": on,
        "off": off,
        "quant_mm": quant_mm,
        "least_mm": least,
        # 1e-6 mm absorbs the rounding of a position read back from its step
        "ok": (over[0] is None and under[0] is not None and under[0] >= least - 1e-6 and off == 0),
    }


#: The normals of two faces that may lie on one plane differ by less than this.
_PARALLEL = math.cos(math.radians(2.0))
#: How many plane offsets a bucket of faces spans, in position steps.
_BUCKET_STEPS = 4
#: How finely a bucket of faces divides the directions they face (32 a unit).
_BUCKET_TURN = 32


def _plane_axes(
    normal: npt.NDArray[np.float64],
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Two unit vectors across a plane facing *normal*, (u, v) with u x v = normal."""
    seed = np.array([1.0, 0.0, 0.0]) if abs(normal[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(normal, seed)
    u /= np.linalg.norm(u)
    return u, np.cross(normal, u)


def _clip_convex(
    subject: list[tuple[float, float]], clip: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    """The part of polygon *subject* inside the convex polygon *clip*, both counterclockwise."""
    out = list(subject)
    for k, a in enumerate(clip):
        if not out:
            break
        b = clip[(k + 1) % len(clip)]
        ex, ey = b[0] - a[0], b[1] - a[1]
        given, out = out, []
        for i, p in enumerate(given):
            q = given[(i + 1) % len(given)]
            sp = ex * (p[1] - a[1]) - ey * (p[0] - a[0])
            sq = ex * (q[1] - a[1]) - ey * (q[0] - a[0])
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def _polygon_area(points: list[tuple[float, float]]) -> float:
    return (
        abs(
            sum(
                p[0] * q[1] - q[0] * p[1]
                for p, q in zip(points, points[1:] + points[:1], strict=True)
            )
        )
        / 2
    )


def coplanar_overlaps(
    meshes: list[Mesh], quant_mm: float, min_area_mm2: float | None = None
) -> dict[str, Any]:
    """Where two meshes of different materials cover one place at one depth.

    Two faces that face the same way, lie on one plane and overlap draw the
    same pixels at the same depth: a depth test then keeps one or the other by
    rounding, pixel by pixel, and which one wins differs between renderers and
    between frames (a CPU rasterizer drew the round marks of an earlier T-Deck
    Plus model as a dark pinwheel where a GPU drew them as a light disc:
    the light dot and the dark disc under it, two solids of the spec, rounded
    to one height). No depth
    offset is safe at every distance, so the faces of a model must not share a
    plane where they overlap: a print is cut out of what it is printed on, a
    solid that sits on another starts where that one ends, and a layer over
    another lies a whole number of position steps above it.

    The faces of two meshes are on one plane when they face within 2 degrees
    of one way and every corner of each lies less than one position step
    (*quant_mm*) from the other's plane. That is the depth the readers of these
    models cannot separate: the grid puts every face of the builder's prisms on
    a multiple of the step, so two faces nearer than a step are one plane to
    the model, and one step is more than two units of a 24-bit depth buffer at
    the clip planes and the farthest distances the landing film (near 0.01 m,
    far 4 m, the StickS3 at most 0.8 m away: 2.6 units) and the videos (near
    0.01 m out to 0.3 m, and near 0.05 m out to 1 m: 8 units or more) draw a
    board at. Faces that face opposite ways do not count: a reader culls the
    back face of a material that is not double-sided, so of two such faces it
    draws at most one from any side; on a double-sided material they count.
    An overlap smaller than *min_area_mm2* (one position step squared unless
    given) is a shared edge, not a shared face.

    Returns a dict: ``pairs``, one entry for each pair of meshes and the plane
    they share (``meshes``, ``materials``, ``facing``, the unit normal they
    face; ``gap_mm``, the farthest apart two of their overlapping faces are;
    ``area_mm2``, the area they share; ``at_mm``, a point of it), the largest
    area first; ``least_mm``, the step; ``min_area_mm2``; and ``ok``, true when
    there is no pair.
    """
    least = quant_mm - 1e-6  # 1e-6 mm absorbs the rounding of a position read back
    min_area = quant_mm * quant_mm if min_area_mm2 is None else min_area_mm2
    tris: list[npt.NDArray[np.float64]] = []
    normals: list[npt.NDArray[np.float64]] = []
    offsets: list[npt.NDArray[np.float64]] = []
    owners: list[npt.NDArray[np.int64]] = []
    mirrors: list[npt.NDArray[np.bool_]] = []
    los: list[npt.NDArray[np.float64]] = []
    his: list[npt.NDArray[np.float64]] = []
    for index, m in enumerate(meshes):
        if not len(m.faces):
            continue
        t = m.positions[m.faces].astype(float)
        cross = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        size = np.linalg.norm(cross, axis=1)
        keep = size > 1e-9
        t, n = t[keep], cross[keep] / size[keep, None]
        sides = [(t, n)]
        if m.double:
            sides.append((t[:, ::-1], -n))
        for back, (faces, facing) in enumerate(sides):
            mirrors.append(np.full(len(faces), bool(back)))
            tris.append(faces)
            normals.append(facing)
            offsets.append(np.einsum("ij,ij->i", facing, faces[:, 0]))
            owners.append(np.full(len(faces), index))
            los.append(faces.min(axis=1) - quant_mm)
            his.append(faces.max(axis=1) + quant_mm)
    if not tris:
        return {"pairs": [], "least_mm": quant_mm, "min_area_mm2": min_area, "ok": True}
    tri, normal, offset = np.concatenate(tris), np.concatenate(normals), np.concatenate(offsets)
    owner, lo, hi = np.concatenate(owners), np.concatenate(los), np.concatenate(his)
    mirror = np.concatenate(mirrors)
    material = np.array([meshes[i].material for i in owner])
    grouped: dict[tuple[int, ...], list[int]] = {}
    keys = np.column_stack(
        [
            np.rint(normal * _BUCKET_TURN).astype(int),
            np.floor(offset / (_BUCKET_STEPS * quant_mm)).astype(int),
        ]
    )
    for i, key in enumerate(map(tuple, keys)):
        grouped.setdefault(key, []).append(i)
    buckets = {key: np.array(found) for key, found in grouped.items()}
    steps = [
        (a, b, c, d) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1) for d in (-1, 0, 1)
    ]
    found: dict[Any, Any] = {}
    for key, here in buckets.items():
        for step in steps:
            other = tuple(k + s for k, s in zip(key, step, strict=True))
            if other < key or other not in buckets:
                continue
            there = buckets[other]
            for start in range(0, len(here), 256):
                a = here[start : start + 256]
                pick = (
                    (material[a][:, None] != material[there][None, :])
                    & (np.abs(offset[a][:, None] - offset[there][None, :]) < 2 * quant_mm)
                    & np.all(lo[a][:, None, :] <= hi[there][None, :, :], axis=2)
                    & np.all(lo[there][None, :, :] <= hi[a][:, None, :], axis=2)
                )
                if other == key:
                    pick &= a[:, None] < there[None, :]
                for pi, pj in zip(*np.nonzero(pick), strict=True):
                    i, j = int(a[pi]), int(there[pj])
                    if (
                        owner[i] == owner[j]
                        or (mirror[i] and mirror[j])
                        or normal[i] @ normal[j] < _PARALLEL
                    ):
                        continue
                    gap = max(
                        np.abs(tri[j] @ normal[i] - offset[i]).max(),
                        np.abs(tri[i] @ normal[j] - offset[j]).max(),
                    )
                    if gap >= least:
                        continue
                    u, v = _plane_axes(normal[i])
                    flat_i = [(float(p @ u), float(p @ v)) for p in tri[i]]
                    flat_j = [(float(p @ u), float(p @ v)) for p in tri[j]]
                    shared = _clip_convex(flat_j, flat_i)
                    if len(shared) < 3:
                        continue
                    area = _polygon_area(shared)
                    if area <= 0:
                        continue
                    names = sorted(
                        [(meshes[owner[i]].name, material[i]), (meshes[owner[j]].name, material[j])]
                    )
                    plane = (
                        tuple(float(c) + 0.0 for c in np.round(normal[i], 3)),
                        round(float(offset[i]), 2),
                    )
                    entry = found.setdefault(
                        (tuple(names), plane),
                        {
                            "meshes": [names[0][0], names[1][0]],
                            "materials": [names[0][1], names[1][1]],
                            "facing": list(plane[0]),
                            "gap_mm": 0.0,
                            "area_mm2": 0.0,
                            "at_mm": [round(float(c), 3) for c in tri[i].mean(axis=0)],
                        },
                    )
                    entry["gap_mm"] = max(entry["gap_mm"], round(float(gap), 6))
                    entry["area_mm2"] += area
    pairs = []
    for entry in found.values():
        if entry["area_mm2"] >= min_area:
            entry["area_mm2"] = round(entry["area_mm2"], 6)
            pairs.append(entry)
    pairs.sort(key=lambda e: (-e["area_mm2"], e["meshes"]))
    return {"pairs": pairs, "least_mm": quant_mm, "min_area_mm2": min_area, "ok": not pairs}


def coplanar_selftest(
    cad_dir: str | Path | None = None,
) -> tuple[dict[str, dict[str, Any]], list[tuple[str, bool, str]], list[tuple[str, Any, str]]]:
    """Plant depth ties in two committed models: (the clean reports, the plants, the controls).

    ``coplanar_overlaps`` must find nothing in the T-Deck Plus's and the
    Cardputer ADV's models as committed, find each tie planted in them
    (``[(what, caught, how)]``: a print laid on the face it is printed on, the
    T-Deck's trackball gap lowered a step onto the metal ring as the round
    marks of an earlier model lay on one another, a print half a step over its
    face off the grid, a block sunk back into its strip with its sides on the
    strip's, a mesh moved by its node's translation in the file, a material
    made double-sided over a face it rests on), and pass each change that is no
    tie (``[(what, passed, how)]``: a print one whole step over its face).
    """
    import dataclasses
    import tempfile

    import glb_legends
    from paths import write_file

    cad = Path(cad_dir) if cad_dir else Path(__file__).resolve().parent.parent
    repo = cad

    def model(board: str) -> tuple[Path, float]:
        record = json.loads((cad / board / "model" / "source.json").read_text())
        return repo / record["model"], record["parameters"]["quant_mm"]

    def moved(meshes: list[Mesh], name: str, dz: float) -> list[Mesh]:
        if not any(m.name == name for m in meshes):
            raise AssertionError(name)
        return [
            dataclasses.replace(m, positions=m.positions + np.array([0.0, 0.0, dz]))
            if m.name == name
            else m
            for m in meshes
        ]

    def rewritten(
        glb: str | Path, change: Callable[[dict[str, Any]], None], out: str | Path
    ) -> list[Mesh]:
        js, bin_ = glb_legends.read(Path(glb).read_bytes())
        change(js)
        write_file(out, glb_legends.write(js, bin_))
        return read_glb(out)

    def gap_lowered(js: dict[str, Any]) -> None:
        node = next(n for n in js["nodes"] if n.get("name") == "trackball_gap")
        node["translation"] = [0.0, 0.0, -0.01 * MM]

    def keys_double_sided(js: dict[str, Any]) -> None:
        material = next(m for m in js["materials"] if m.get("name") == "key")
        material["doubleSided"] = True

    tdeck, step = model("tdeck-plus")
    cardputer, card_step = model("cardputer")
    t_meshes, c_meshes = read_glb(tdeck), read_glb(cardputer)
    clean = {
        "tdeck-plus": coplanar_overlaps(t_meshes, step),
        "cardputer": coplanar_overlaps(c_meshes, card_step),
    }
    with tempfile.TemporaryDirectory(prefix="coplanar-selftest-") as tmp:
        # what is planted, the meshes, the step, and the two meshes the tie must name
        plants = [
            (
                "the round marks' discs laid on the plate they are printed on",
                moved(t_meshes, "plate_mark_legends_dcdde2", -8 * step),
                step,
                {"keyboard_plate", "plate_mark_legends_dcdde2"},
            ),
            (
                "the trackball's gap lowered a step onto the metal ring (as the round marks of "
                "an earlier model lay: a light dot on a dark disc, both at one height)",
                moved(t_meshes, "trackball_gap", -step),
                step,
                {"trackball_gap", "trackball_metal"},
            ),
            (
                "the keys' legends half a step over the caps, off the grid",
                moved(t_meshes, "key_legends_f2f3f5", -2.5 * step),
                step,
                {"key_legends_f2f3f5", "keys"},
            ),
            (
                "a colored block sunk back into its strip, its sides on the strip's",
                moved(c_meshes, "legend_gray", -4 * card_step),
                card_step,
                {"legend_gray", "legend_strips"},
            ),
            (
                "the trackball's gap lowered a step by its node's translation, in the file",
                rewritten(tdeck, gap_lowered, Path(tmp) / "gap.glb"),
                step,
                {"trackball_gap", "trackball_metal"},
            ),
            (
                "the keys' material made double-sided, a cap's underside on its rim's top",
                rewritten(tdeck, keys_double_sided, Path(tmp) / "double.glb"),
                step,
                {"key_rims", "keys"},
            ),
        ]
        results = []
        for what, meshes, quant, pair in plants:
            got = coplanar_overlaps(meshes, quant)
            named = [p for p in got["pairs"] if set(p["meshes"]) == pair]
            results.append(
                (
                    what,
                    bool(named) and not got["ok"],
                    f"{named[0]['meshes']} facing {named[0]['facing']}, "
                    f"{named[0]['area_mm2']:.3f} mm2"
                    if named
                    else f"no tie between {sorted(pair)}",
                )
            )
    controls = []
    for what, meshes, quant in (
        (
            "the keys' legends lowered to one whole step over the caps",
            moved(t_meshes, "key_legends_f2f3f5", -2 * step),
            step,
        ),
    ):
        got = coplanar_overlaps(meshes, quant)
        controls.append(
            (
                what,
                got["ok"],
                "no tie" if got["ok"] else "; ".join(str(p["meshes"]) for p in got["pairs"][:3]),
            )
        )
    return clean, results, controls


def test_card(uv: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """The test card's sRGB color at each UV (glTF convention: v grows down)."""
    u, v = np.clip(uv[..., 0], 0, 1), np.clip(uv[..., 1], 0, 1)
    right, bottom = u >= 0.5, v >= 0.5
    quad = right.astype(int) + 2 * bottom.astype(int)
    col = np.asarray(CARD_COLORS)[quad]
    mark = (u < 0.12) & (v < 0.12) & ((u < 0.04) | (v < 0.04))
    col[mark] = 1.0
    out: npt.NDArray[np.float64] = col.astype(float)
    return out


def orthographic(
    towards: Sequence[float], up: Sequence[float] = (0.0, 1.0, 0.0)
) -> tuple[Callable[[npt.NDArray[np.float64]], npt.NDArray[np.float64]], npt.NDArray[np.float64]]:
    """(project, towards): glTF-frame mm -> (h, v, depth) for a viewer along
    *towards* (from the model to the eye), *up* on the picture's up; h grows
    right, v grows up, depth grows towards the viewer."""
    d = np.asarray(towards, dtype=float)
    d /= np.linalg.norm(d)
    upv = np.asarray(up, dtype=float)
    right = np.cross(upv, d)
    right /= np.linalg.norm(right)
    upv = np.cross(d, right)

    def project(p: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        return np.stack([p @ right, p @ upv, p @ d], axis=-1)

    return project, d


def rasterize(
    meshes: list[Mesh],
    project: Callable[[npt.NDArray[np.float64]], npt.NDArray[np.float64]],
    towards: npt.NDArray[np.float64],
    ppm: float,
    bounds: tuple[float, float, float, float] | None = None,
    light: npt.ArrayLike | None = None,
    screen_card: bool = False,
    supersample: int = 2,
    skip: Iterable[str] = (),
) -> tuple[npt.NDArray[np.uint8], tuple[float, float, float, float]]:
    """Draw *meshes* through *project* at *ppm* pixels per mm.

    *project* maps (N, 3) glTF-frame mm to (h, v, depth); *towards* is the
    model-to-viewer direction in the glTF frame (for back faces and light).
    *bounds* (h0, h1, v0, v1) in mm fixes the picture's window (default: the
    model's own, 1 mm wider each side). Returns (RGBA float image, row 0 at
    v1 (the top), bounds).
    """
    towards = np.asarray(towards, dtype=float)
    towards = towards / np.linalg.norm(towards)
    if light is None:
        light = towards + np.array([-0.35, 0.55, 0.25])
    key_dir = np.asarray(light, dtype=float)
    key_dir = key_dir / np.linalg.norm(key_dir)
    half = key_dir + towards
    half /= np.linalg.norm(half)
    # the light a face toward the viewer takes, which the shading divides by
    facing = AMBIENT + KEY * max(float(towards @ key_dir), 0.0)
    shown = [m for m in meshes if len(m.faces) and m.name not in skip and m.name != "glass"]
    drawn = [m for m in shown if m.alpha >= 1.0]
    blended = [m for m in shown if m.alpha < 1.0]
    proj = [project(m.positions) for m in drawn]
    blend_proj = [project(m.positions) for m in blended]
    if bounds is None:
        allp = np.concatenate(proj + blend_proj)
        bounds = (
            allp[:, 0].min() - 1,
            allp[:, 0].max() + 1,
            allp[:, 1].min() - 1,
            allp[:, 1].max() + 1,
        )
    h0, h1, v0, v1 = bounds
    s = ppm * supersample
    nx, ny = int(np.ceil((h1 - h0) * s)), int(np.ceil((v1 - v0) * s))
    zbuf = np.full((ny, nx), -np.inf)
    rgb = np.zeros((ny, nx, 3))
    cover = np.zeros((ny, nx))
    # farthest first, by the depth of each blended mesh's box's center
    order = sorted(
        range(len(blended)),
        key=lambda i: float((blend_proj[i][:, 2].min() + blend_proj[i][:, 2].max()) / 2),
    )
    passes = [(m, p, False) for m, p in zip(drawn, proj, strict=True)]
    passes += [(blended[i], blend_proj[i], True) for i in order]
    for m, p, blend in passes:
        tri = m.positions[m.faces]
        fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        front = (fn @ towards) > 1e-12
        if m.double:
            front |= (fn @ towards) < -1e-12
        px = (p[:, 0] - h0) * s
        py = (v1 - p[:, 1]) * s  # row 0 at the top
        dz = p[:, 2]
        card = screen_card and m.name == "screen" and m.uv is not None
        for fi in np.nonzero(front)[0]:
            a, b, c = m.faces[fi]
            x = px[[a, b, c]]
            y = py[[a, b, c]]
            xa, xb = max(int(np.floor(x.min())), 0), min(int(np.ceil(x.max())), nx - 1)
            ya, yb = max(int(np.floor(y.min())), 0), min(int(np.ceil(y.max())), ny - 1)
            if xa > xb or ya > yb:
                continue
            den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(den) < 1e-12:
                continue
            gx, gy = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
            wa = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
            wb = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
            wc = 1 - wa - wb
            inside = (wa >= -1e-6) & (wb >= -1e-6) & (wc >= -1e-6)
            if not inside.any():
                continue
            z = wa * dz[a] + wb * dz[b] + wc * dz[c]
            zsub = zbuf[ya : yb + 1, xa : xb + 1]
            win = inside & (z > zsub)
            if not win.any():
                continue
            if not blend:
                zsub[win] = z[win]
            if card and m.uv is not None:
                uv = wa[win, None] * m.uv[a] + wb[win, None] * m.uv[b] + wc[win, None] * m.uv[c]
                col = test_card(uv)
            elif m.unlit:
                col = np.broadcast_to(m.color, (int(win.sum()), 3))
            else:
                n = (
                    wa[win, None] * m.normals[a]
                    + wb[win, None] * m.normals[b]
                    + wc[win, None] * m.normals[c]
                )
                n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
                if m.double and (fn[fi] @ towards) < 0:
                    n = -n
                shade = (AMBIENT + KEY * np.clip(n @ key_dir, 0, 1))[:, None] / facing
                shine = (1.0 - m.rough) ** 2
                lobe = 8 + 120 * shine
                # the highlight where a face turns toward the light further than
                # a face toward the viewer, which keeps its base color
                spec = (
                    np.clip(n @ half, 0, 1) ** lobe - max(float(towards @ half), 0.0) ** lobe
                ).clip(0) * (0.08 + 0.5 * shine)
                base = srgb_to_linear(m.color)[None, :]
                # a dielectric: its base color less the reflection, and the
                # reflection; a metal: its base color is its reflection
                lit = (
                    (1.0 - m.metal) * (shade * base * (1.0 - F0) + F0)
                    + m.metal * shade * base
                    + spec[:, None] * ((1.0 - m.metal) + m.metal * base)
                )
                col = linear_to_srgb(pbr_neutral(lit))
            col = np.clip(col, 0, 1)
            if blend:
                # straight alpha over what is there: a over b, coverage too
                a = m.alpha
                under = cover[ya : yb + 1, xa : xb + 1][win]
                after = a + under * (1.0 - a)
                col = (
                    col * a + rgb[ya : yb + 1, xa : xb + 1][win] * (under * (1.0 - a))[:, None]
                ) / after[:, None]
                cover[ya : yb + 1, xa : xb + 1][win] = after
            else:
                cover[ya : yb + 1, xa : xb + 1][win] = 1.0
            rgb[ya : yb + 1, xa : xb + 1][win] = col
    img = np.concatenate([rgb, cover[..., None]], axis=2)
    if supersample > 1:
        ny2, nx2 = ny // supersample * supersample, nx // supersample * supersample
        img = img[:ny2, :nx2]
        # premultiplied box filter, then back to straight alpha
        img[..., :3] *= img[..., 3:4]
        img = img.reshape(ny2 // supersample, supersample, nx2 // supersample, supersample, 4).mean(
            axis=(1, 3)
        )
        a = img[..., 3:4]
        img[..., :3] = np.where(a > 0, img[..., :3] / np.maximum(a, 1e-9), 0)
    return img, (h0, h1, v0, v1)
