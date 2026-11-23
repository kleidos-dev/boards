# SPDX-License-Identifier: MIT
"""Render a board model's front, left, top and back views against its drawings

Draws orthographic, shaded views of a board's ``.glb`` (front, left side, top,
and, for a board with an ``svg/back.svg``, the back as its viewer sees it),
with the board's ``svg/front.svg`` outline (and ``back.svg``'s on the back),
the ``measurements.json`` box and the display's active area over them, and
reports in mm how far the model is from each:

- ``extents``: the model's width, height and depth (the whole model, and its
  ``case_*`` meshes alone) against ``case.width`` / ``height`` / ``depth``;
- ``outline``: the front silhouette against the case outline of ``front.svg``
  (each bounding edge, the largest and mean distance between the two outlines,
  and their area overlap); ``back_outline`` the same for the back silhouette,
  in the back frame (``board_faces.py``), against ``back.svg``'s case outline;
- ``screen``: each edge of the model's ``screen`` mesh against the active area
  of ``measurements.json`` and the ``screen-active`` rect of ``front.svg``, and
  its ``clearance``: how far the nearest face under it and the nearest over it
  (the glass) lie from its plane (``model_raster.screen_clearance``), which must
  be at least one quantization step each;
- ``legends``, for a board whose front prints any: every legend group of
  ``front.svg`` against the ink the model holds for it
  (``legend_placement.py``: the furthest any point of either outline lies from
  the other, group by group, which must be within ``--legend-tolerance-mm``,
  0.02 mm unless given; no group without its ink and no ink without a group;
  each legend mesh in an opaque material of its own ink; the drawing still
  printing what the model was built from, by the digest of its legend groups,
  ``legend_source.py``), and each legends mesh's
  ``clearance`` over the mesh it is printed on
  (``model_raster.legend_clearance``, from the viewer of the face it is printed
  on). Each drawing's legend outlines are laid over its own face's view;
- ``depth``: every pair of meshes of different materials that cover one place
  at one depth, facing the same way less than one position step apart
  (``model_raster.coplanar_overlaps``), which must be none: a depth test keeps
  either by rounding, differently from one renderer to the next.

The model is placed in the front frame of ``measurements.json`` (x across from
the case's left edge, y down from its top edge) by the ``center_mm`` and
``front_frame`` its ``model/source.json`` records (written by
``build_board_glb.py``); a model without one is aligned on its silhouette's
top-left corner. Silhouettes come from ``render_views.silhouette_polygon``; the
shaded views are drawn with a depth buffer (``model_raster.py``), so what the
picture shows in front is what is nearest. Every check reads the model as a
glTF reader draws it, each mesh where its node and the nodes above it place it
(``model_raster.read_glb``): a part moved by a node's translation is measured
where it is drawn.

Writes ``<board>-views.png`` and ``<board>-check.json`` into ``--out`` and
prints the deviations. Exits 1 when the screen's clearance is short, when the
legends are not where the drawing prints them or lie too near the face under
them, when two meshes share a depth, and, with ``--max-dev-mm``, when an
outline edge, an extent or a screen edge is further off than that.
``--selftest`` runs the checks' own tests instead: defects planted in the
Cardputer ADV's model and in the back print of the two-face fixture, each of
which the legend check must catch (``legend_placement.selftest`` and
``faces_selftest``), and depth ties planted in the T-Deck Plus's
and the Cardputer's, each of which the depth check must catch, beside changes
that are no tie, which it must pass (``model_raster.coplanar_selftest``).

Needs the builder's libraries (see ``build_board_glb.py``) plus::

    pip install matplotlib==3.11.2 cascadio==0.1.1

Usage::

    python -I _shared/check_board_model.py \\
        <board> [--glb FILE] [--out DIR] [--max-dev-mm X] \\
        [--legend-tolerance-mm X]
    python -I _shared/check_board_model.py --selftest
"""

import argparse
import json
import math
import re
import struct
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import glb_legends  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import model_raster  # noqa: E402
import numpy as np  # noqa: E402
import render_views  # noqa: E402
import shapely.affinity  # noqa: E402
import shapely.geometry as sg  # noqa: E402
import trimesh  # noqa: E402
from paths import ROOT as REPO  # noqa: E402  (the repository root)
from shapely.ops import unary_union  # noqa: E402

#: How far a legend may lie from where the drawing prints it, in mm.
LEGEND_TOLERANCE_MM = 0.02
VIEWS = ("front", "left", "top")
#: The view a board with a back drawing (``svg/back.svg``) is also drawn in.
BACK_VIEW = "back"
#: Pixels per mm of the shaded views.
VIEW_PPM = 8
#: Direction from the model towards the viewer, per view (glTF frame).
TOWARDS_VIEWER = {"front": (0, 0, 1), "left": (-1, 0, 0), "top": (0, 1, 0), "back": (0, 0, -1)}


# ---------------------------------------------------------------- model


def glb_json(path):
    raw = Path(path).read_bytes()
    if struct.unpack_from("<I", raw, 0)[0] != 0x46546C67:
        raise ValueError(f"{path}: not a GLB")
    jlen = struct.unpack_from("<I", raw, 12)[0]
    return json.loads(raw[20 : 20 + jlen])


def quant_step_mm(path):
    """The quantization step of a model's quantized meshes, in mm (its nodes'
    scale), or 0.01 when it has none."""
    scales = [n["scale"][0] for n in glb_json(path)["nodes"] if "scale" in n]
    return round(min(scales) * 1000.0, 9) if scales else 0.01


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, dtype=float), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def load_model(path):
    """[(node name, mesh in mm, sRGB color, alpha)] in the glTF frame."""
    js = glb_json(path)
    looks = {}
    for node in js["nodes"][1:]:
        if "mesh" not in node:
            continue
        prim = js["meshes"][node["mesh"]]["primitives"][0]
        mat = js["materials"][prim["material"]] if "material" in prim else {}
        f = mat.get("pbrMetallicRoughness", {}).get("baseColorFactor", [0.6, 0.6, 0.6, 1.0])
        alpha = f[3] if mat.get("alphaMode") == "BLEND" else 1.0
        looks[node["name"]] = (linear_to_srgb(f[:3]), alpha)
    scene = trimesh.load(str(path))
    out = []
    for node in scene.graph.nodes_geometry:
        transform, gname = scene.graph[node]
        mesh = scene.geometry[gname].copy()
        mesh.apply_transform(transform)
        mesh.apply_scale(1000.0)
        color, alpha = looks.get(node, (np.array([0.6, 0.6, 0.6]), 1.0))
        out.append((node, mesh, color, alpha))
    return out


def concat(meshes):
    return meshes[0] if len(meshes) == 1 else trimesh.util.concatenate(meshes)


# ---------------------------------------------------------------- front.svg


_TOKEN = re.compile(r"[MmLlHhVvAaCcQqZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


def _arc(x1, y1, rx, ry, phi_deg, fa, fs, x2, y2, step=0.15):
    """Points along an SVG elliptical arc (SVG 1.1 F.6.5), end included."""
    if rx == 0 or ry == 0:
        return [(x2, y2)]
    phi = math.radians(phi_deg)
    cp, sp = math.cos(phi), math.sin(phi)
    dx2, dy2 = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cp * dx2 + sp * dy2, -sp * dx2 + cp * dy2
    rx, ry = abs(rx), abs(ry)
    lam = x1p**2 / rx**2 + y1p**2 / ry**2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2
    den = rx**2 * y1p**2 + ry**2 * x1p**2
    coef = math.sqrt(max(0.0, num / den)) if den else 0.0
    if fa == fs:
        coef = -coef
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)

    th1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dth = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dth > 0:
        dth -= 2 * math.pi
    elif fs and dth < 0:
        dth += 2 * math.pi
    n = max(4, math.ceil(abs(dth) * max(rx, ry) / step))
    pts = []
    for i in range(1, n + 1):
        t = th1 + dth * i / n
        pts.append(
            (
                cp * rx * math.cos(t) - sp * ry * math.sin(t) + cx,
                sp * rx * math.cos(t) + cp * ry * math.sin(t) + cy,
            )
        )
    return pts


def _bezier(p, steps=16):
    p = np.asarray(p, dtype=float)
    t = np.linspace(0, 1, steps + 1)[1:, None]
    if len(p) == 3:
        q = (1 - t) ** 2 * p[0] + 2 * (1 - t) * t * p[1] + t**2 * p[2]
    else:
        q = (
            (1 - t) ** 3 * p[0]
            + 3 * (1 - t) ** 2 * t * p[1]
            + 3 * (1 - t) * t**2 * p[2]
            + t**3 * p[3]
        )
    return [tuple(v) for v in q]


def path_rings(d):
    """The subpaths of an SVG path's ``d`` as point lists."""
    toks = _TOKEN.findall(d)
    rings, ring = [], []
    i, cmd = 0, None
    x = y = sx = sy = 0.0

    def take(n):
        nonlocal i
        vals = [float(v) for v in toks[i : i + n]]
        i += n
        return vals

    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if ring:
                    rings.append(ring)
                ring = []
                x, y = sx, sy
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            nx, ny = take(2)
            if rel:
                nx, ny = x + nx, y + ny
            if ring:
                rings.append(ring)
            ring = [(nx, ny)]
            x, y, sx, sy = nx, ny, nx, ny
            cmd = "l" if rel else "L"  # later pairs are line-tos
        elif c == "L":
            nx, ny = take(2)
            x, y = (x + nx, y + ny) if rel else (nx, ny)
            ring.append((x, y))
        elif c == "H":
            (nx,) = take(1)
            x = x + nx if rel else nx
            ring.append((x, y))
        elif c == "V":
            (ny,) = take(1)
            y = y + ny if rel else ny
            ring.append((x, y))
        elif c == "A":
            rx, ry, phi, fa, fs, nx, ny = take(7)
            if rel:
                nx, ny = x + nx, y + ny
            ring += _arc(x, y, rx, ry, phi, int(fa), int(fs), nx, ny)
            x, y = nx, ny
        elif c in "CQ":
            k = 6 if c == "C" else 4
            v = take(k)
            pts = [(v[j] + (x if rel else 0), v[j + 1] + (y if rel else 0)) for j in range(0, k, 2)]
            ring += _bezier([(x, y)] + pts)
            x, y = pts[-1]
        else:
            raise ValueError(f"unsupported path command {cmd!r}")
    if ring:
        rings.append(ring)
    return rings


def _attrs(tag):
    return dict(re.findall(r'([\w:-]+)="([^"]*)"', tag))


def svg_outline(svg_path):
    """(case outline polygon, screen-active box) of a front.svg, front-frame mm."""
    text = Path(svg_path).read_text()
    body = re.sub(r"<defs>.*?</defs>", "", text, flags=re.S)
    m = re.search(r"<(rect|path|polygon)\b[^>]*>", body)
    if not m:
        raise ValueError(f"{svg_path}: no case outline")
    tag, a = m.group(1), _attrs(m.group(0))
    if tag == "rect":
        x, y = float(a.get("x", 0)), float(a.get("y", 0))
        w, h = float(a["width"]), float(a["height"])
        r = float(a.get("rx", a.get("ry", 0)))
        outline = (
            sg.box(x + r, y + r, x + w - r, y + h - r).buffer(r, quad_segs=24)
            if r > 0
            else sg.box(x, y, x + w, y + h)
        )
    elif tag == "polygon":
        v = [float(t) for t in re.split(r"[\s,]+", a["points"].strip())]
        outline = sg.Polygon(list(zip(v[0::2], v[1::2], strict=True)))
    else:
        rings = path_rings(a["d"])
        outline = sg.Polygon(rings[0], [r for r in rings[1:] if len(r) >= 3])
    sa = re.search(r'<rect\b[^>]*id="screen-active"[^>]*>', text)
    screen = None
    if sa:
        s = _attrs(sa.group(0))
        screen = (
            float(s["x"]),
            float(s["y"]),
            float(s["x"]) + float(s["width"]),
            float(s["y"]) + float(s["height"]),
        )
    return outline, screen


# ---------------------------------------------------------------- geometry


def largest(poly):
    if poly.geom_type == "Polygon":
        return poly
    return max(poly.geoms, key=lambda g: g.area)


def outline_deviation(svg_poly, model_poly):
    """Distances in mm between the two outlines' exteriors."""
    a = sg.LinearRing(largest(svg_poly).exterior.coords)
    b = sg.LinearRing(largest(model_poly).exterior.coords)
    pts = [a.interpolate(t) for t in np.arange(0, a.length, 0.1)]
    d_ab = np.array([b.distance(p) for p in pts])
    inter = svg_poly.intersection(model_poly).area
    union = svg_poly.union(model_poly).area
    sb, mb = svg_poly.bounds, model_poly.bounds
    return {
        "hausdorff_mm": round(a.hausdorff_distance(b), 3),
        "svg_to_model_mean_mm": round(float(d_ab.mean()), 3),
        "svg_to_model_max_mm": round(float(d_ab.max()), 3),
        "iou": round(inter / union, 4) if union else 0.0,
        "edges_mm": {
            "left": round(mb[0] - sb[0], 3),
            "top": round(mb[1] - sb[1], 3),
            "right": round(mb[2] - sb[2], 3),
            "bottom": round(mb[3] - sb[3], 3),
        },
    }


def to_front(points, place):
    """glTF-frame mm (x, y) -> front-frame mm (x across, y down)."""
    pts = np.asarray(points, dtype=float)
    return np.column_stack([pts[:, 0] + place["dx"], place["dy"] - pts[:, 1]])


def poly_to_front(poly, place):
    def tf(ring):
        return to_front(np.asarray(ring.coords)[:, :2], place)

    def one(p):
        return sg.Polygon(tf(p.exterior), [tf(r) for r in p.interiors])

    if poly.geom_type == "Polygon":
        return one(poly)
    return unary_union([one(p) for p in poly.geoms])


def poly_to_back(poly, place):
    """A glTF-frame silhouette seen from the front, as the back's viewer sees it, back-frame mm."""
    front = poly_to_front(poly, place)
    return shapely.affinity.affine_transform(front, [-1, 0, 0, 1, place["back_w"], 0])


def placement(board_dir, case_front_poly, width=None):
    """How glTF-frame mm map to the front frame: front x = x + dx, y = dy - y.

    ``back_w`` is how far the back frame's origin lies across the front frame
    (``board_faces.py``): a back drawing's u is ``back_w`` less the front's x.
    It is the back frame's ``right_x`` less the front's ``left_x`` where
    ``source.json`` records one, else *width*, the case's.
    """
    rec = board_dir / "model" / "source.json"
    if rec.is_file():
        p = json.loads(rec.read_text()).get("parameters", {})
        c, ff = p.get("center_mm"), p.get("front_frame")
        if c and ff:
            back = (p.get("face_frames") or {}).get("back")
            return {
                "dx": c[0] - ff["left_x"],
                "dy": ff["top_y"] - c[1],
                "how": "source.json",
                "back_w": back["right_x"] - ff["left_x"] if back else width,
            }
    minx, _, _, maxy = case_front_poly.bounds
    return {"dx": -minx, "dy": maxy, "how": "silhouette top-left", "back_w": width}


# ---------------------------------------------------------------- drawing


def view_coords(points, view, place):
    """(h, v) plot coordinates of glTF-frame mm points in one view."""
    p = np.asarray(points, dtype=float)
    fx = p[..., 0] + place["dx"]
    fy = place["dy"] - p[..., 1]
    if view == "front":
        return np.stack([fx, fy], axis=-1)
    if view == "back":
        return np.stack([place["back_w"] - fx, fy], axis=-1)
    if view == "left":
        return np.stack([p[..., 2], fy], axis=-1)
    return np.stack([fx, p[..., 2]], axis=-1)  # top: z down the page after the flip


def draw_shaded(ax, meshes, view, place):
    """Draw the model's shaded view, depth-buffered, under the outlines."""
    towards = np.array(TOWARDS_VIEWER[view], dtype=float)

    def project(p):
        # the plot's v grows down the page: the raster's up is -v
        hv = view_coords(p, view, place)
        return np.column_stack([hv[:, 0], -hv[:, 1], p @ towards])

    img, (h0, h1, v0, v1) = model_raster.rasterize(meshes, project, towards, VIEW_PPM)
    ax.imshow(img, extent=[h0, h1, -v0, -v1], origin="upper", interpolation="bilinear", zorder=0)


def outline_coords(poly, view, place):
    """A glTF-frame silhouette's rings in one view's plot coordinates."""
    out = []
    for p in [poly] if poly.geom_type == "Polygon" else list(poly.geoms):
        for ring in [p.exterior] + list(p.interiors):
            c = np.asarray(ring.coords)
            if view == "front":
                out.append(to_front(c, place))
            elif view == "back":
                # MODEL_VIEW_AXES back: (-x, y)
                out.append(
                    np.column_stack(
                        [c[:, 0] + place["back_w"] - place["dx"], place["dy"] - c[:, 1]]
                    )
                )
            elif view == "left":
                # MODEL_VIEW_AXES left: (z, y)
                out.append(np.column_stack([c[:, 0], place["dy"] - c[:, 1]]))
            else:
                # MODEL_VIEW_AXES top: (x, -z)
                out.append(np.column_stack([c[:, 0] + place["dx"], -c[:, 1]]))
    return out


# ---------------------------------------------------------------- check


def legends_report(board_dir, glb, raster_meshes, tolerance_mm):
    """(report, outlines) of a model's legends against its drawing; (None, []) with none.

    The report is ``legend_placement.placement``'s, with each legends mesh's
    clearance over the mesh it is printed on; the outlines are what the
    drawing prints, for the front view.
    """
    extras = glb_legends.legends(glb_json(glb))
    source = board_dir / "model" / "source.json"
    record = json.loads(source.read_text()) if source.is_file() else {}
    if not extras and not record.get("legends"):
        return None, []
    import legend_placement  # only a model with legends needs fontTools

    report = legend_placement.placement(raster_meshes, extras, None, record, tolerance_mm)
    step = quant_step_mm(glb)
    for entry in record.get("legends") or []:
        gap = model_raster.legend_clearance(
            raster_meshes,
            entry["mesh"] + "_",
            step,
            on=entry["on"],
            face=entry.get("face", "front"),
        )
        if gap is None:
            continue
        report["meshes"].setdefault(entry["mesh"], {})["clearance"] = gap
        if not gap["ok"]:
            report["ok"] = False
            report["problems"].append(
                f"{entry['mesh']}: clearance {gap['under_mm']} mm over {gap['under_mesh']} "
                f"(at least {gap['least_mm']:g}), {gap['over_mesh']} over it at "
                f"{gap['over_mm']}, {gap['off']} triangle(s) off {entry['on']}"
            )
    return report, legend_placement.outlines(board_dir)


def check(board_dir, glb, out_dir, max_dev=None, legend_tolerance=LEGEND_TOLERANCE_MM):
    board_dir = Path(board_dir)
    board = board_dir.name
    meas = json.loads((board_dir / "measurements.json").read_text())
    case = meas["case"]
    disp = meas["display"]
    nodes = load_model(glb)
    raster_meshes = model_raster.read_glb(glb)
    whole = concat([m for _, m, _, _ in nodes])
    case_nodes = [m for n, m, _, _ in nodes if n.startswith("case")]
    case_mesh = concat(case_nodes) if case_nodes else whole

    back_svg = board_dir / "svg" / "back.svg"
    views = VIEWS + ((BACK_VIEW,) if back_svg.is_file() else ())
    sil = {
        v: render_views.silhouette_polygon(whole, v, render_views.MODEL_VIEW_AXES) for v in views
    }
    case_front = render_views.silhouette_polygon(case_mesh, "front", render_views.MODEL_VIEW_AXES)
    place = placement(board_dir, case_front, float(case["width"]))

    ext_whole = whole.extents
    ext_case = case_mesh.extents
    report = {
        "board": board,
        "glb": str(glb),
        "placement": place["how"],
        "triangles": int(sum(len(m.faces) for _, m, _, _ in nodes)),
        "bytes": Path(glb).stat().st_size,
        "extents": {
            "measured_mm": [case["width"], case["height"], case["depth"]],
            "model_mm": [round(float(v), 3) for v in ext_whole],
            "model_delta_mm": [
                round(float(ext_whole[i]) - [case["width"], case["height"], case["depth"]][i], 3)
                for i in range(3)
            ],
            "case_mm": [round(float(v), 3) for v in ext_case],
            "case_delta_mm": [
                round(float(ext_case[i]) - [case["width"], case["height"], case["depth"]][i], 3)
                for i in range(3)
            ],
        },
    }

    svg_path = board_dir / "svg" / "front.svg"
    svg_poly = svg_screen = None
    if svg_path.is_file():
        svg_poly, svg_screen = svg_outline(svg_path)
        report["outline"] = outline_deviation(svg_poly, poly_to_front(sil["front"], place))
    back_poly = None
    if back_svg.is_file():
        # the back drawing's outline against the silhouette seen from behind, in its frame
        back_poly, _ = svg_outline(back_svg)
        report["back_outline"] = outline_deviation(back_poly, poly_to_back(sil["front"], place))

    m_screen = [(n, m) for n, m, _, _ in nodes if n == "screen"]
    meas_screen = (
        disp["origin_x_mm"],
        disp["origin_y_mm"],
        disp["origin_x_mm"] + disp["active_w_mm"],
        disp["origin_y_mm"] + disp["active_h_mm"],
    )
    if m_screen:
        v = m_screen[0][1].vertices
        f = to_front(v[:, :2], place)
        model_rect = (f[:, 0].min(), f[:, 1].min(), f[:, 0].max(), f[:, 1].max())

        def edges(ref):
            return {
                k: round(float(model_rect[i] - ref[i]), 3)
                for i, k in enumerate(("left", "top", "right", "bottom"))
            }

        report["screen"] = {
            "model_rect_mm": [round(float(c), 3) for c in model_rect],
            "vs_measurements_mm": edges(meas_screen),
        }
        if svg_screen:
            report["screen"]["vs_front_svg_mm"] = edges(svg_screen)
        report["screen"]["clearance"] = model_raster.screen_clearance(
            raster_meshes, quant_step_mm(glb)
        )

    printed, legend_rings = legends_report(board_dir, glb, raster_meshes, legend_tolerance)
    if printed is not None:
        report["legends"] = printed
    report["depth"] = model_raster.coplanar_overlaps(raster_meshes, quant_step_mm(glb))

    # ---- picture
    ratios = [case["width"], case["depth"] * 1.6, case["width"]]
    ratios += [case["width"]] * (len(views) - len(VIEWS))
    fig, axes = plt.subplots(
        1, len(views), figsize=(5 * len(views), 7), dpi=150, gridspec_kw={"width_ratios": ratios}
    )
    zc = (whole.bounds[0][2] + whole.bounds[1][2]) / 2
    boxes = {
        "front": (0, 0, case["width"], case["height"]),
        "left": (zc - case["depth"] / 2, 0, zc + case["depth"] / 2, case["height"]),
        "top": (0, zc - case["depth"] / 2, case["width"], zc + case["depth"] / 2),
        "back": (0, 0, case["width"], case["height"]),
    }
    back_rings = []
    if back_svg.is_file() and printed is not None:
        import legend_placement

        back_rings = legend_placement.outlines(board_dir, BACK_VIEW)
    for ax, view in zip(axes, views, strict=True):
        draw_shaded(ax, raster_meshes, view, place)
        for ring in outline_coords(sil[view], view, place):
            ax.plot(ring[:, 0], ring[:, 1], color="#202020", lw=0.5)
        x0, y0, x1, y1 = boxes[view]
        ax.plot(
            [x0, x1, x1, x0, x0],
            [y0, y0, y1, y1, y0],
            ls="--",
            color="#1f6fd1",
            lw=0.8,
            label="measurements.json box",
        )
        if view == "front":
            if svg_poly is not None:
                for ring in [svg_poly.exterior] + list(svg_poly.interiors):
                    c = np.asarray(ring.coords)
                    ax.plot(c[:, 0], c[:, 1], color="#d62728", lw=0.8, label="front.svg outline")
                    break
            sx0, sy0, sx1, sy1 = meas_screen
            ax.plot(
                [sx0, sx1, sx1, sx0, sx0],
                [sy0, sy0, sy1, sy1, sy0],
                color="#2ca02c",
                lw=0.8,
                label="active area (measurements)",
            )
            if svg_screen:
                sx0, sy0, sx1, sy1 = svg_screen
                ax.plot(
                    [sx0, sx1, sx1, sx0, sx0],
                    [sy0, sy0, sy1, sy1, sy0],
                    color="#e377c2",
                    lw=0.6,
                    ls=":",
                    label="screen-active (front.svg)",
                )
            for index, (_plane, _fill, rings) in enumerate(legend_rings):
                for nth, ring in enumerate(rings):
                    ax.plot(
                        ring[:, 0],
                        ring[:, 1],
                        color="#17becf",
                        lw=0.25,
                        label="legends (front.svg)" if index == 0 and nth == 0 else None,
                    )
        if view == BACK_VIEW:
            for ring in [back_poly.exterior]:
                c = np.asarray(ring.coords)
                ax.plot(c[:, 0], c[:, 1], color="#d62728", lw=0.8)
            for _plane, _fill, rings in back_rings:
                for ring in rings:
                    ax.plot(ring[:, 0], ring[:, 1], color="#17becf", lw=0.25)
        ax.set_aspect("equal")
        ax.autoscale_view()
        lo_x, hi_x = sorted(ax.get_xlim())
        lo_y, hi_y = sorted(ax.get_ylim())
        ax.set_xlim(min(lo_x, boxes[view][0]) - 2, max(hi_x, boxes[view][2]) + 2)
        ax.set_ylim(max(hi_y, boxes[view][3]) + 2, min(lo_y, boxes[view][1]) - 2)
        ax.set_title(view)
        ax.grid(True, alpha=0.25)
        ax.set_xlabel("mm")
    axes[0].legend(loc="lower center", bbox_to_anchor=(0.5, -0.32), fontsize=7, ncol=2)
    ext = report["extents"]
    fig.suptitle(
        f"{board}: model {ext['model_mm'][0]:.2f} x {ext['model_mm'][1]:.2f} x "
        f"{ext['model_mm'][2]:.2f} mm, measured {case['width']} x {case['height']} x "
        f"{case['depth']} mm, {report['triangles']} triangles"
    )
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f"{board}-views.png"
    fig.tight_layout()
    fig.savefig(png)
    plt.close(fig)
    report["png"] = str(png)

    worst = []
    for key in ("outline", "back_outline"):
        if key in report:
            worst += [abs(v) for v in report[key]["edges_mm"].values()]
            worst.append(report[key]["svg_to_model_max_mm"])
    worst += [abs(v) for v in report["extents"]["case_delta_mm"][:2]]
    if "screen" in report:
        worst += [abs(v) for v in report["screen"]["vs_measurements_mm"].values()]
    report["worst_mm"] = round(max(worst), 3) if worst else 0.0
    (out_dir / f"{board}-check.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def depth_selftest():
    """Run ``model_raster.coplanar_selftest`` and print it; True when every part passed."""
    clean, results, controls = model_raster.coplanar_selftest(HERE.parent)
    for board, got in clean.items():
        print(
            f"depth: the {board} model as committed: "
            f"{'passes' if got['ok'] else 'FAILS'} ({len(got['pairs'])} tie(s))"
        )
        for pair in got["pairs"]:
            print(f"  {pair['meshes']} facing {pair['facing']}, {pair['area_mm2']} mm2")
    for what, caught, how in results:
        print(f"depth: {'caught' if caught else 'MISSED'}: {what} -> {how}")
    for what, passed, how in controls:
        print(f"depth: {'passed' if passed else 'FAILED'}: {what} -> {how}")
    good = (
        all(got["ok"] for got in clean.values())
        and all(c for _, c, _ in results)
        and all(p for _, p, _ in controls)
    )
    print("depth selftest " + ("passed" if good else "FAILED"))
    return good


def main(argv=None):
    """Run the check from the command line; return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("board_dir", type=Path, nargs="?", help="<board>")
    parser.add_argument(
        "--glb", type=Path, help="the model (default: the spec's output, or model/<board>.glb)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="where the picture and report go (default: a new temporary directory)",
    )
    parser.add_argument(
        "--max-dev-mm",
        type=float,
        help="exit 1 when an outline edge, a case extent or a screen edge is further off than this",
    )
    parser.add_argument(
        "--legend-tolerance-mm",
        type=float,
        default=LEGEND_TOLERANCE_MM,
        help="how far a legend may lie from where front.svg prints it "
        f"(default {LEGEND_TOLERANCE_MM})",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run the checks' own tests: defects planted in the Cardputer "
        "ADV's and the T-Deck Plus's models, each of which they must "
        "catch",
    )
    args = parser.parse_args(argv)
    if args.selftest:
        import legend_placement

        legends_ok = legend_placement.main(["--selftest"]) == 0
        return 0 if depth_selftest() and legends_ok else 1
    if args.board_dir is None:
        parser.error("give a board directory, or --selftest")
    board_dir = args.board_dir.resolve()
    glb = args.glb
    if glb is None:
        spec = board_dir / "model" / "spec.json"
        glb = (
            REPO / json.loads(spec.read_text())["output"]
            if spec.is_file()
            else board_dir / "model" / f"{board_dir.name}.glb"
        )
    out = args.out or Path(tempfile.mkdtemp(prefix=f"{board_dir.name}-check-"))
    report = check(board_dir, glb, out, args.max_dev_mm, args.legend_tolerance_mm)
    shown = dict(report)
    if "legends" in shown:
        # the group-by-group table stays in <board>-check.json
        shown["legends"] = {k: v for k, v in shown["legends"].items() if k != "per_group"}
    print(json.dumps(shown, indent=2))
    clearance = report.get("screen", {}).get("clearance")
    if clearance is not None and not clearance["ok"]:
        print(
            f"FAIL: the screen is {clearance['behind_mm']} mm in front of the nearest face "
            f"under it and {clearance['in_front_mm']} mm behind the nearest over it; each "
            f"must be at least {clearance['quant_mm']} mm",
            file=sys.stderr,
        )
        return 1
    printed = report.get("legends")
    if printed is not None and not printed["ok"]:
        for problem in printed["problems"]:
            print(f"FAIL: legends: {problem}", file=sys.stderr)
        return 1
    if not report["depth"]["ok"]:
        for pair in report["depth"]["pairs"]:
            print(
                f"FAIL: depth: {pair['meshes'][0]} and {pair['meshes'][1]} cover "
                f"{pair['area_mm2']} mm2 facing {pair['facing']}, {pair['gap_mm']} mm apart "
                f"(under {report['depth']['least_mm']}), near {pair['at_mm']}",
                file=sys.stderr,
            )
        return 1
    if args.max_dev_mm is not None and report["worst_mm"] > args.max_dev_mm:
        print(
            f"FAIL: worst deviation {report['worst_mm']} mm > {args.max_dev_mm} mm", file=sys.stderr
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
