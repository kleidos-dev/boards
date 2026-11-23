# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Write the LILYGO T-Deck Plus case into its model's spec, from this repository's own data

The T-Deck Plus's model draws its case from no vendor file: every part of the
shell, the front frame round the face, the side key and the power slide is a
shape of ``tdeck-plus/model/spec.json``, and this script writes those shapes
there, replacing the case meshes it wrote before and leaving every other mesh
(the face, the keyboard, the trackball, the prints) as it is. Run it, then
rebuild the model::

    python -I _shared/tdeck_plus_case.py
    python -I _shared/build_board_glb.py tdeck-plus/model/spec.json

What it is built from:

* the outline, the bevel, the glass and the keyboard plate of the front
  drawing, ``svg/front.svg``, as ``emit_front_svg.py`` draws them
  (``TDECK_PLUS_BODY`` and its rails, ``tdeck_plus_inset``): the case's
  plan is the drawing's outline, and the front frame's opening the glass's
  and the plate's outlines 0.4 mm in, so their edges lie under the frame;
* ``measurements.json``: the width, height and depth (73.14 x 114.98 x 20.4);
* the places this repository records for the side and end openings
  (``docs/models-and-drawings.md``, "Where the models disagree with
  measurements.json": the power slide at y 61.5 to 67.0 on the right face,
  the 6.4 x 3.8 mm key at y 41.8 to 48.2 and the 12.3 x 5.3 mm opening at
  y 23.0 to 35.3 on the left, the USB-C opening at x 32.49 to 41.73 and
  z -10.7 to -6.7, six 2 mm holes in the bottom end), and the back's flat
  face at z -19.0 that ``back_tdeck_plus.py`` prints on;
* what those leave open, measured on LILYGO's published product pictures of
  the T-Deck Plus (the PINMAP sheet's straight-on back, registered on the
  back drawing's printed T-DECK and LILYGO at 15.9 px a mm; the
  specification sheet's four side views, about 15 px a mm), each figure
  read off the picture, never traced: the back's slope round its edge (5.0
  mm across the sides, 4.3 at the top end, 9.0 at the bottom end, over 5.0 mm
  of depth), the 1/4-inch nut's boss (r 5.4 at x 36.1, y 43.9 of the back,
  its lobe r 1.9 at x 43.8, 1.4 mm proud: the case's 20.4 mm), the two screw
  holes, the top frame's lower edge, the badge's pocket and its five rings,
  the two lines from the badge to the sides, the seam round the sides at
  z -8.7, the front frame's side rails (to z -4.4), the microSD slot, the
  two knock-outs in the top end, and the bottom holes' places.

No vendor CAD file, drawing or picture is read by this script or kept in the
repository: the numbers below are the measurements.

Coordinates: the model's build frame (``build_board_glb.py``), x across from
the case's left edge as the front is seen, y up from its bottom, z out of the
front (0 at the frame's top). The back's figures are written as the back
drawing has them (``board_faces.py``: x from the left edge as seen from
behind, y down from the top) and turned here.
"""

from __future__ import annotations

import json
import math
import sys
from collections.abc import Sequence
from itertools import pairwise
from pathlib import Path
from typing import Any

import shapely.geometry as sg
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_front_svg as fronts
from paths import ROOT

SPEC = ROOT / "tdeck-plus" / "model" / "spec.json"
MEAS = json.loads((ROOT / "tdeck-plus" / "measurements.json").read_text())
W = float(MEAS["case"]["width"])  # 73.14
H = float(MEAS["case"]["height"])  # 114.98
DEPTH = float(MEAS["case"]["depth"])  # 20.4

#: One position step (the spec's quant_mm): a dark mark lies one step proud
#: of the face it marks, so no two materials share a depth.
STEP = 0.01
#: Depths (z), from the frame's top at 0.
Z_TOP_CHAMFER = -0.35  # the frame's top edge: a 0.35 mm chamfer
Z_FRAME_BOTTOM = -2.2  # the frame's opening runs down to the body, under the plate (-2.0)
Z_BACK_EDGE = -14.0  # where the sides end and the back's slope begins
Z_BACK = -19.0  # the back's flat face, which the back drawing prints on
Z_BOSS = -DEPTH + STEP  # the nut's boss: its dark marks one step out reach the 20.4 mm
RAIL_Z = (-4.4, -0.6)  # the side rails of the front frame
SEAM_Z = (-8.85, -8.55)  # the seam round the sides, 0.25 mm deep
SEAM_DEPTH = 0.25
#: The back's slope: how far in the flat face starts from the sides, the top
#: end and the bottom end (the PINMAP back, against its 5.0 mm of depth on
#: the side views).
BACK_INSET = (5.0, 4.3, 9.0)
#: A relief line on the back: its width and how far it stands proud.
RIDGE_W = 0.4
RIDGE_H = 0.2


def r3(v: float) -> float:
    return round(float(v) + 0.0, 3)


def front_pt(x: float, y: float) -> tuple[Any, ...]:
    """A point of the front drawing (x across, y down) in the build frame."""
    return (x, H - y)


def back_pt(x: float, y: float) -> tuple[Any, ...]:
    """A point of the back drawing (x across as seen from behind, y down)."""
    return (W - x, H - y)


def ring(poly: sg.Polygon) -> list[Any]:
    """A polygon's outline as the spec writes it, counterclockwise, not closed."""
    poly = sg.polygon.orient(poly, 1.0)
    return [[r3(x), r3(y)] for x, y in list(poly.exterior.coords)[:-1]]


def holes(poly: sg.Polygon) -> list[Any]:
    poly = sg.polygon.orient(poly, 1.0)
    return [[[r3(x), r3(y)] for x, y in list(h.coords)[:-1]] for h in poly.interiors]


def _one_polygon(shape: BaseGeometry) -> sg.Polygon:
    """A prism's profile: one polygon."""
    if not isinstance(shape, sg.Polygon):
        raise ValueError(f"a prism profile is one polygon, not a {shape.geom_type}")
    return shape


def prism(
    shape: BaseGeometry, z0: float, z1: float, faces: list[str] | None = None, axis: str = "z"
) -> dict[str, Any]:
    poly = _one_polygon(shape)
    p: dict[str, Any] = {
        "axis": axis,
        "range": [r3(z0), r3(z1)],
        "profile": {"polygon": ring(poly)},
    }
    if poly.interiors:
        p["profile"]["holes"] = holes(poly)
    if faces:
        p["faces"] = faces
    return {"prism": p}


def simple(points: Sequence[tuple[float, float]]) -> sg.Polygon:
    poly = sg.Polygon(points)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly


def front_poly(points: Sequence[tuple[float, float]]) -> sg.Polygon:
    return simple([front_pt(x, y) for x, y in points])


# ---------------------------------------------------------------- the plan


def body_points() -> list[Any]:
    """The body's outline (the drawing's, without the rails), front drawing frame."""
    return list(fronts.TDECK_PLUS_BODY)


def body() -> sg.Polygon:
    return front_poly(body_points())


def inset(
    d_side: float,
    d_top: float,
    d_bottom: float,
    points: Sequence[tuple[float, float]] | None = None,
) -> list[Any]:
    """The body outline moved in (front drawing frame), point for point."""
    return fronts.tdeck_plus_inset(list(points or body_points()), d_side, d_top, d_bottom)


def opening() -> sg.Polygon:
    """The front frame's opening: the glass's and the plate's outlines 0.4 mm in."""
    glass_y = fronts.TDECK_PLUS_GLASS_BOTTOM
    # the glass's opening runs 0.3 mm past the glass's foot, so the step where
    # it meets the plate's narrower one lies on no face of the plate's edge
    glass = fronts.tdeck_plus_clip_y(inset(2.0 + 0.4, 2.15 + 0.4, 2.35), glass_y + 0.3, True)
    plate = fronts.tdeck_plus_clip_y(
        fronts.tdeck_plus_shift_x(inset(2.33 + 0.4, 2.0, 1.7 + 0.4), fronts.TDECK_PLUS_PLATE_DX),
        glass_y,
        False,
    )
    return unary_union([front_poly(glass), front_poly(plate)]).buffer(0)


def rails() -> list[Any]:
    """The two side rails, 0.65 and 0.54 mm proud, where the drawing has them."""
    left, right = fronts.TDECK_PLUS_BODY_SIDES
    y0, y1, y2, y3 = fronts.TDECK_PLUS_RAIL_ENDS
    lx, rx = fronts.TDECK_PLUS_RAIL_X, W
    over = 0.1  # into the body, so no gap shows
    return [
        front_poly(
            [(left + over, y0), (left, y0), (lx, y1), (lx, y2), (left, y3), (left + over, y3)]
        ),
        front_poly(
            [(right - over, y0), (right, y0), (rx, y1), (rx, y2), (right, y3), (right - over, y3)]
        ),
    ]


# ---------------------------------------------------------------- side and end openings

#: Each opening of the walls: a notch of the body in plan (front drawing
#: frame) over a range of z, and the dark floor it shows.
#: (name, x0, x1, y0, y1, z0, z1)
LEFT, RIGHT = fronts.TDECK_PLUS_BODY_SIDES
NOTCHES = [
    # the left face's 12.3 x 5.3 mm opening (the GPS's Grove seat shows through it)
    ("grove", LEFT - 1, LEFT + 1.6, 23.0, 35.3, -13.15, -7.85),
    # the right face's microSD slot (specification sheet's right side view)
    ("microsd", RIGHT - 1.2, RIGHT + 1, 27.0, 40.2, -9.3, -7.9),
    # the power slide's slot
    ("power", RIGHT - 1.0, RIGHT + 1, 61.5, 67.0, -12.0, -6.0),
    # the USB-C opening in the bottom end
    ("usb", 32.49, 41.73, 107.3, H + 1, -10.7, -6.7),
]
#: The six holes of the bottom end (2 mm, as recorded; their places read on
#: the specification sheet's bottom view), each three bands deep so it reads
#: round: (x center).
BOTTOM_HOLES_X = (16.8, 21.2, 25.5, 48.7, 52.8, 57.0)
BOTTOM_HOLE_Z = -6.3
BOTTOM_HOLE_D = 2.0
BOTTOM_HOLE_DEPTH = 1.5


def bottom_y_at(x: float) -> float:
    """The body's bottom edge at x (front drawing frame, y down)."""
    line = sg.LineString([front_pt(x, -1), front_pt(x, H + 1)])
    hit = body().exterior.intersection(line)
    ys = [float(p.y) for p in getattr(hit, "geoms", [hit])]
    return H - min(ys)


def hole_notches() -> list[Any]:
    out = []
    r = BOTTOM_HOLE_D / 2
    # a 2 mm hole drawn in three bands: 1.2 mm wide, 2.0, 1.2
    bands = [(-r, -0.6 * r, 0.6 * r), (-0.6 * r, 0.6 * r, r), (0.6 * r, r, 0.6 * r)]
    for i, x in enumerate(BOTTOM_HOLES_X):
        floor = bottom_y_at(x) - BOTTOM_HOLE_DEPTH
        for j, (dz0, dz1, half) in enumerate(bands):
            out.append(
                (
                    f"hole{i}{j}",
                    x - half,
                    x + half,
                    floor,
                    H + 1,
                    BOTTOM_HOLE_Z + dz0,
                    BOTTOM_HOLE_Z + dz1,
                )
            )
    return out


def notch_poly(n: Sequence[Any]) -> sg.Polygon:
    _, x0, x1, y0, y1, _, _ = n
    return front_poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def bands() -> list[Any]:
    """The body's walls from the back's edge to the frame, cut where an opening is."""
    notches = NOTCHES + hole_notches()
    cuts = {Z_BACK_EDGE, Z_FRAME_BOTTOM, *SEAM_Z}
    for n in notches:
        cuts |= {n[5], n[6]}
    steps = sorted(round(c, 4) for c in cuts if Z_BACK_EDGE <= c <= Z_FRAME_BOTTOM)
    out = []
    base = body()
    seam = base.buffer(-SEAM_DEPTH, join_style="mitre")
    for z0, z1 in pairwise(steps):
        mid = (z0 + z1) / 2
        poly: BaseGeometry = seam if SEAM_Z[0] <= mid <= SEAM_Z[1] else base
        for n in notches:
            if n[5] <= mid <= n[6]:
                poly = poly.difference(notch_poly(n))
        poly = poly.buffer(0)
        out.append((z0, z1, poly))
    return out


def floors() -> list[Any]:
    """The dark floor of each opening: one step out of the face it lies on."""
    out = []
    for n in NOTCHES + hole_notches():
        name, x0, x1, y0, y1, z0, z1 = n
        if name == "usb":
            continue  # the receptacle fills it
        if name in ("grove", "microsd", "power"):
            left = name == "grove"
            fx = x1 if left else x0  # the floor's x (front drawing frame)
            a, b = (fx - STEP, fx) if left else (fx, fx + STEP)
            # a slab whose outer face is one step out of the floor
            out.append({"box": [r3(a), r3(b), r3(H - y1), r3(H - y0), r3(z0), r3(z1)]})
        else:  # a bottom hole: its floor faces the bottom end
            out.append({"box": [r3(x0), r3(x1), r3(H - y0 - STEP), r3(H - y0), r3(z0), r3(z1)]})
    return out


# ---------------------------------------------------------------- the back


def back_line(points: Sequence[tuple[float, float]], width: float = RIDGE_W) -> sg.Polygon:
    """A relief line through *points* of the back drawing, *width* wide."""
    return sg.LineString([back_pt(x, y) for x, y in points]).buffer(
        width / 2, cap_style="flat", join_style="mitre"
    )


def back_closed(points: Sequence[Sequence[float]], width: float = RIDGE_W) -> BaseGeometry:
    pts = [back_pt(x, y) for x, y in points]
    outer = sg.Polygon(pts).buffer(width / 2, join_style="mitre")
    inner = sg.Polygon(pts).buffer(-width / 2, join_style="mitre")
    return outer.difference(inner)


def lerp(a: Sequence[float], b: Sequence[float], t: float) -> tuple[float, ...]:
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(2))


#: The badge's five rings, outermost and innermost (back drawing frame): each a
#: trapezoid, its bottom corners cut at 45 degrees.
BADGE_OUTER = ((27.3, 63.4), (45.6, 63.4), (52.6, 91.4), (20.9, 91.4))
BADGE_INNER = ((31.7, 68.3), (40.8, 68.3), (46.4, 87.6), (27.4, 87.6))
BADGE_RINGS = 5
#: The pocket the rings sit in.
BADGE_POCKET = ((24.6, 60.9), (47.0, 60.9), (56.3, 92.0), (54.5, 96.3), (19.5, 96.3), (17.2, 92.0))
#: The top frame's lower edge, and the two lines from the badge's foot to the sides.
FRAME_EDGE = ((5.8, 16.2), (16.2, 26.4), (55.3, 26.4), (65.7, 16.2))
FOOT_LINES = (((5.6, 95.3), (17.6, 89.6)), ((55.6, 89.6), (67.5, 95.3)))
#: The 1/4-inch nut's boss and its lobe, the brass insert and the lobe's hole.
BOSS = ((36.1, 43.9), 5.4)
LOBE = ((43.8, 44.0), 1.9)
INSERT_R = 2.7
INSERT_RING_R = 3.2
LOBE_HOLE_R = 1.15
#: The two screw holes, either side of the frame's name.
SCREWS = (((9.43, 10.6), 1.35), ((63.04, 10.6), 1.35))


def badge_rings() -> list[Any]:
    out = []
    for i in range(BADGE_RINGS):
        t = i / (BADGE_RINGS - 1)
        quad = [lerp(BADGE_OUTER[k], BADGE_INNER[k], t) for k in range(4)]
        out.append(back_closed(quad, 0.3))
    return out


def disc(center: tuple[float, float], r: float, res: int = 48) -> sg.Polygon:
    x, y = back_pt(*center)
    return sg.Point(x, y).buffer(r, quad_segs=res // 4)


# ---------------------------------------------------------------- the top end

#: The two knock-outs of the top end (specification sheet's top view): a ring
#: and four slots round a disc, on the top face, x across the front.
KNOCKOUTS_X = (16.6, 56.5)
KNOCKOUT_Z = -8.7
KNOCKOUT_RING = (3.55, 3.8)
KNOCKOUT_SLOTS = (2.0, 2.8)


def knockout_marks(cx: float) -> list[Any]:
    """The knock-out's dark ring and slots, in the top face's (x, z) plane."""
    cz = KNOCKOUT_Z
    out = [
        sg.Point(cx, cz)
        .buffer(KNOCKOUT_RING[1], quad_segs=16)
        .difference(sg.Point(cx, cz).buffer(KNOCKOUT_RING[0], quad_segs=16))
    ]
    r0, r1 = KNOCKOUT_SLOTS
    for k in range(4):
        a0 = math.radians(45 + 90 * k - 30)
        a1 = math.radians(45 + 90 * k + 30)
        arc = [a0 + (a1 - a0) * i / 8 for i in range(9)]
        pts = [(cx + r1 * math.cos(a), cz + r1 * math.sin(a)) for a in arc] + [
            (cx + r0 * math.cos(a), cz + r0 * math.sin(a)) for a in reversed(arc)
        ]
        out.append(sg.Polygon(pts))
    return out


def xz_prism(shape: BaseGeometry, y0: float, y1: float, faces: list[str] | None) -> dict[str, Any]:
    """A prism along y from a polygon in (x, z)."""
    poly = _one_polygon(shape)
    p: dict[str, Any] = {"axis": "y", "range": [r3(y0), r3(y1)], "profile": {"polygon": ring(poly)}}
    if poly.interiors:
        p["profile"]["holes"] = holes(poly)
    p["faces"] = faces
    return {"prism": p}


# ---------------------------------------------------------------- the meshes


def loft_ring(points: Sequence[tuple[float, float]]) -> list[Any]:
    return [[r3(x), r3(H - y)] for x, y in points]


def case_meshes() -> list[Any]:
    base_pts = body_points()
    top_pts = inset(0.35, 0.35, 0.35)
    back_pts = inset(*BACK_INSET)
    hole = opening()
    frame_top = front_poly(top_pts).difference(hole)
    frame_wall = body().difference(hole)
    shell = [prism(poly, z0, z1, ["outer", "top", "bottom"]) for z0, z1, poly in bands()]
    shell.append(
        {
            "loft": {
                "axis": "z",
                "caps": ["last"],
                "sections": [
                    {"at": Z_BACK_EDGE, "polygon": loft_ring(base_pts)},
                    {"at": Z_BACK, "polygon": loft_ring(back_pts)},
                ],
            }
        }
    )
    boss = unary_union(
        [
            disc(*BOSS),
            disc(*LOBE),
            sg.LineString([back_pt(*BOSS[0]), back_pt(*LOBE[0])]).buffer(1.6),
        ]
    )
    shell.append(prism(boss, Z_BOSS, Z_BACK, ["bottom", "outer"]))
    relief = unary_union(
        badge_rings()
        + [back_closed(BADGE_POCKET), back_line(FRAME_EDGE)]
        + [back_line(line) for line in FOOT_LINES]
    )
    lines = [
        prism(poly, Z_BACK - RIDGE_H, Z_BACK, ["bottom", "outer"])
        for poly in getattr(relief, "geoms", [relief])
    ]
    # the groove the picture shows round the boss's foot
    lines.append(
        prism(boss.buffer(0.3, quad_segs=12).difference(boss), Z_BACK - STEP, Z_BACK, ["bottom"])
    )
    frame = [
        {
            "loft": {
                "axis": "z",
                "sections": [
                    {"at": Z_TOP_CHAMFER, "polygon": loft_ring(base_pts)},
                    {"at": 0.0, "polygon": loft_ring(top_pts)},
                ],
            }
        },
        prism(frame_top, Z_TOP_CHAMFER, 0.0, ["top", "inner"]),
        prism(frame_wall, Z_FRAME_BOTTOM, Z_TOP_CHAMFER, ["outer", "inner"]),
    ] + [prism(r, RAIL_Z[0], RAIL_Z[1]) for r in rails()]
    # the dark marks: the openings' floors, the screw holes, the nut's ring and
    # the lobe's hole, each one step out of the face under it; the knock-outs'
    # ring and slots one step out of the top end
    marks = floors()
    insert = disc(BOSS[0], INSERT_RING_R).difference(disc(BOSS[0], INSERT_R))
    for poly in [disc(c, r) for c, r in SCREWS]:
        marks.append(prism(poly, Z_BACK - STEP, Z_BACK, ["bottom"]))
    for ring_shape in (insert, disc(LOBE[0], LOBE_HOLE_R)):
        marks.append(prism(ring_shape, Z_BOSS - STEP, Z_BOSS, ["bottom"]))
    for cx in KNOCKOUTS_X:
        for poly in knockout_marks(cx):
            marks.append(xz_prism(poly, H, H + STEP, ["top"]))
    left, right = fronts.TDECK_PLUS_BODY_SIDES
    return [
        {
            "name": "case_shell",
            "note": "Written by _shared/tdeck_plus_case.py: the walls from "
            "the back's edge to the front frame, cut where the openings are, the back's slope "
            "and its flat face (z -19.0, which the back prints on), the nut's boss and the "
            "back's relief lines.",
            "material": "case",
            "smooth_deg": 40,
            "shapes": shell,
        },
        {
            "name": "case_relief",
            "note": "Written by _shared/tdeck_plus_case.py: the back's "
            "relief lines, which the picture shows dark, 0.2 mm proud of the flat face: the top "
            "frame's lower edge, the badge's pocket and five rings, the two lines from its foot "
            "to the sides, and the groove round the nut's boss, one step out.",
            "material": "relief",
            "shapes": lines,
        },
        {
            "name": "case_frame",
            "note": "Written by _shared/tdeck_plus_case.py: the front "
            "frame round the face, its top chamfered, its opening the glass's and the plate's "
            "outlines 0.4 mm in, and its two side rails.",
            "material": "case",
            "smooth_deg": 40,
            "shapes": frame,
        },
        {
            "name": "key_left",
            "note": "The left face's key, 6.4 x 3.8 mm, as proud as the rails.",
            "material": "black_plastic",
            "smooth_deg": 40,
            "shapes": [
                {
                    "prism": {
                        "axis": "x",
                        "range": [0.0, r3(left + 0.1)],
                        "profile": {
                            "rounded_rect": [r3(H - 48.2), r3(H - 41.8), -10.2, -6.4],
                            "r": 0.9,
                            "res": 4,
                        },
                    }
                }
            ],
        },
        {
            "name": "key_right",
            "note": "The power slide's knob in its slot, 0.45 mm proud.",
            "material": "black_plastic",
            "smooth_deg": 40,
            "shapes": [
                {
                    "prism": {
                        "axis": "x",
                        "range": [r3(right - 1.0 + STEP), r3(right + 0.45)],
                        "profile": {
                            "rounded_rect": [r3(H - 66.1), r3(H - 62.4), -11.3, -6.7],
                            "r": 0.6,
                            "res": 4,
                        },
                    }
                }
            ],
        },
        {
            "name": "case_marks",
            "note": "Written by _shared/tdeck_plus_case.py: what shows dark "
            "on the case, each one position step out of the face under it: the openings' floors, "
            "the bottom holes, the screw holes, the nut's ring and the lobe's hole, the "
            "knock-outs' rings and slots.",
            "material": "hole",
            "shapes": marks,
        },
        {
            "name": "nut_insert",
            "note": "The brass 1/4-inch nut in its boss, one position step out of the boss.",
            "material": "brass",
            "smooth_deg": 40,
            "shapes": [prism(disc(BOSS[0], INSERT_R), Z_BOSS - STEP, Z_BOSS, ["bottom"])],
        },
        {
            "name": "grove_socket",
            "note": "The Grove connector seen through the left opening: "
            "its white housing standing on the opening's floor.",
            "material": "ring_white",
            "shapes": [
                {
                    "box": [
                        r3(LEFT + 0.9),
                        r3(LEFT + 1.6 - STEP),
                        r3(H - 33.7),
                        r3(H - 24.6),
                        -12.6,
                        -8.4,
                    ]
                }
            ],
        },
    ]


CASE = (
    "case_shell",
    "case_relief",
    "case_frame",
    "key_left",
    "key_right",
    "case_marks",
    "nut_insert",
    "grove_socket",
)


def dump(obj: object, indent: int = 0) -> str:
    """JSON with objects one key a line and lists of numbers on one line."""
    pad = "  " * indent
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        inner = ",\n".join(f"{pad}  {json.dumps(k)}: {dump(v, indent + 1)}" for k, v in obj.items())
        return "{\n" + inner + "\n" + pad + "}"
    if isinstance(obj, list):
        if all(not isinstance(v, (dict, list)) for v in obj) or (
            obj
            and all(
                isinstance(v, list) and all(not isinstance(w, (dict, list)) for w in v) for v in obj
            )
        ):
            return json.dumps(obj, ensure_ascii=False)
        inner = ",\n".join(f"{pad}  {dump(v, indent + 1)}" for v in obj)
        return "[\n" + inner + "\n" + pad + "]"
    return json.dumps(obj, ensure_ascii=False)


def main() -> int:
    spec = json.loads(SPEC.read_text())
    meshes = [m for m in spec["meshes"] if m["name"] not in CASE + ("internal",)]
    spec["meshes"] = case_meshes() + meshes
    for key in ("volumes", "cull", "parts", "transform", "tessellation"):
        spec.pop(key, None)
    SPEC.write_text(dump(spec) + "\n")
    print(f"wrote the case of {SPEC.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
