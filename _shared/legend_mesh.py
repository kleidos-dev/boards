# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""What a board's drawings print on it, as flat geometry for the board model

A board model holds no image and no texture (``build_board_glb.py``), so what
is printed on a keyboard or on the case is geometry too: every glyph outline
and every drawn mark, triangulated into flat sheets a hair above the surface
they are printed on, one sheet an ink color, each with a material of its own.
Any reader of the model draws them as it draws the case, with no change.

**One source.** Nothing is typed here or in a board's ``spec.json``: the
legends are the ``<g class="legend">`` groups of the board's ``svg/front.svg``,
which ``emit_front_svg.py`` writes from the same constants it draws the board
with (its legend contract), and of the drawings of its other faces
(``svg/back.svg``, by ``emit_back_svg.py``), each in its own face's frame
(``board_faces.py``). The groups and what places them are found by
``legend_source.py``, which also digests them, so what this module reads is
what a model's record holds it to. A group is what is printed for one key
(``data-key``, the slug of the key's hotspot) or one other print on the board
(``data-mark``, a name of its own), and says which surface it is printed on:
its ``data-plane`` (``keys`` when a key's group names none; two prints of
one ink on one surface that are not as thin as each other go on two planes,
so that each sheet's ``stroke_mm`` is its own print's). A ``legends``
mesh of the model draws one plane. Text, position, size, stretch and color
are read from the drawing; an element or an attribute this module does not
understand is refused, so a legend never goes missing quietly.

**What a group may hold.** ``<text>`` (one plain run), ``<polygon>``,
``<rect>``, ``<circle>`` (filled, or stroked with ``fill="none"``) and
``<path>`` (``M L H V Q C A Z``, either case; filled by the nonzero rule or,
with ``fill-rule="evenodd"``, by the even-odd one; or stroked with
``fill="none"``, with ``stroke-linecap`` and ``stroke-linejoin``), each in one
flat ``#rrggbb`` color, and ``<g transform>`` around them. A miter join is
drawn up to SVG's default limit (4); a sharper corner is refused, because a
browser bevels it and this module does not.

**The face.** A ``<text>`` is set in the first family the drawing names for
it, Inter, from the pinned files under ``fonts/inter/`` (SIL Open Font
License 1.1; the digests are read from ``fonts/VERSIONS.md`` and any
other bytes are refused), at the weight it asks for or the nearest pinned one
as CSS picks it. Glyphs are placed by their advance widths, with no kerning
and no ligature: a legend is one to four glyphs, and a run whose width the
drawing pins (``textLength``) is drawn to that width exactly, as a browser
draws it.

**The geometry.** Curves are flattened to within ``flatness`` mm. Every
shape is moved into the model's frame, where its corners are rounded to the
model's position grid (``quant_mm``) before anything is triangulated, so the
triangles written are the triangles the grid holds: none collapses or turns
over when the builder quantizes them. The shapes of one plane are painted in
the drawing's order: a later shape of another color cuts the earlier one (a
legend over its orange arrow), so no two sheets overlap and the plane holds
no two faces at one depth; where two colors meet, both sheets carry the same
corners, so no seam opens between them. Each polygon is triangulated by ear
clipping (mapbox_earcut), counterclockwise in the face's (u, up) plane, and
laid on the face it is printed on, facing out of it (+Z on the front, -Z on
the back): a right-handed frame per face, so no sheet needs a winding of its
own and none is laid mirrored.

**How thin.** Each sheet's ``stroke_mm`` is twice its area over the length of
its outline: for a shape made of strokes w wide and L long in all (L much more
than w) the area is about w L and the outline about 2 L, so the figure is
about w. It is what a reader weighs against its pixels a millimeter to decide
whether the sheet is worth drawing at all (``build_board_glb.py``).

Needs, beside the builder's libraries, ``pip install fonttools==4.68.0``.
"""

import math
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import mapbox_earcut
import numpy as np
import numpy.typing as npt
import shapely
import shapely.affinity
import shapely.geometry as sg
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely.geometry.base import BaseGeometry

sys.path.insert(0, str(Path(__file__).resolve().parent))
import legend_source
import svg_read

if TYPE_CHECKING:
    import board_faces
from paths import FONTS

SVG = legend_source.SVG
#: The pinned faces of each family a legend may be set in, by CSS weight.
FACES = {
    "Inter": {
        400: "inter/Inter-Regular.ttf",
        500: "inter/Inter-Medium.ttf",
        700: "inter/Inter-Bold.ttf",
    },
}
_PATH_TOKEN = re.compile(rf"[MmLlHhVvQqCcAaZz]|{svg_read.NUMBER}")
_TRANSFORM = re.compile(r"(translate|scale|rotate|matrix)\s*\(([^)]*)\)")
#: What each drawn element of a legend may carry; anything else is refused.
_KNOWN = {
    "text": {
        "x",
        "y",
        "transform",
        "font-size",
        "fill",
        "text-anchor",
        "font-weight",
        "textLength",
        "lengthAdjust",
        "font-family",
    },
    "polygon": {"points", "fill", "transform"},
    "rect": {"x", "y", "width", "height", "rx", "ry", "fill", "transform"},
    "circle": {"cx", "cy", "r", "fill", "stroke", "stroke-width", "transform"},
    "path": {
        "d",
        "fill",
        "fill-rule",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "transform",
    },
    "g": {"transform"},
}
#: What the legend group itself may carry.
_GROUP = {"class", "data-key", "data-mark", "data-plane", "transform"}
_NAME = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
#: The plane of a key's group that names none.
KEYS_PLANE = legend_source.KEYS_PLANE
#: SVG's default ``stroke-miterlimit``: a miter longer than this many stroke
#: widths is a bevel in a browser, which this module does not draw.
MITER_LIMIT = 4.0
_CAPS: dict[str, Literal["round", "flat", "square"]] = {
    "round": "round",
    "butt": "flat",
    "square": "square",
}
_JOINS = ("miter", "round", "bevel")


class LegendError(ValueError):
    """The drawing holds a legend this module cannot turn into geometry."""


@dataclass
class Legend:
    """What one legend group prints: its name, its plane and its shapes, in paint order."""

    #: The key's slug (``data-key``) or the print's own name (``data-mark``).
    name: str
    #: The surface it is printed on, as the drawing names it (``data-plane``).
    plane: str
    #: True for a key's legend, False for another print on the board.
    key: bool
    #: (fill as ``rrggbb``, the shape in the drawing's front frame, mm)
    shapes: list[Any] = field(default_factory=list)
    #: The pinned font files its texts are set in (paths under ``fonts``).
    fonts: set[Any] = field(default_factory=set)
    #: How many of its drawn elements a reader's ``keep`` left out (``read_legends``).
    dropped: int = 0


# ---------------------------------------------------------------- the faces


def pinned_digests() -> dict[str, str]:
    """{path under fonts: sha256} as ``fonts/VERSIONS.md`` pins them."""
    text = (FONTS / "VERSIONS.md").read_text(encoding="utf-8")
    return dict(re.findall(r"`([\w./\[\],-]+\.ttf)`\s+`([0-9a-f]{64})`", text))


class Faces:
    """The pinned font files, opened once each, and their flattened glyphs."""

    def __init__(self) -> None:
        self._fonts: dict[str, TTFont] = {}
        self._glyphs: dict[tuple[str, str, float], tuple[float, BaseGeometry]] = {}
        self._pins: dict[str, str] | None = None
        self.used: dict[str, str] = {}

    def font(self, family: str, weight: int) -> tuple[str, TTFont]:
        """(path under fonts, TTFont) for a family at a CSS weight."""
        faces = FACES.get(family)
        if faces is None:
            raise LegendError(f"no pinned face for the family {family!r}; pinned: {sorted(FACES)}")
        # CSS font matching: 400 and 500 try each other first; above 500 the
        # heavier faces first, below 400 the lighter ones first
        have = sorted(faces)
        if weight in faces:
            pick = weight
        elif weight > 500:
            pick = min((w for w in have if w > weight), default=max(have))
        else:
            pick = max((w for w in have if w < weight), default=min(have))
        rel = faces[pick]
        if rel not in self._fonts:
            if self._pins is None:
                self._pins = pinned_digests()
            pins = self._pins
            data = (FONTS / rel).read_bytes()
            digest = sha256(data).hexdigest()
            if pins.get(rel) != digest:
                raise LegendError(f"fonts/{rel} is not the file VERSIONS.md pins (sha256 {digest})")
            self._fonts[rel] = TTFont(FONTS / rel)
            self.used[rel] = digest
        return rel, self._fonts[rel]

    def glyph(
        self, rel: str, font: TTFont, char: str, tolerance: float
    ) -> tuple[float, BaseGeometry]:
        """(advance, shapely geometry) of one character, in font units, y up."""
        key = (rel, char, round(tolerance, 6))
        if key not in self._glyphs:
            name = (font.getBestCmap() or {}).get(ord(char))
            if name is None:
                raise LegendError(f"fonts/{rel} has no glyph for {char!r} (U+{ord(char):04X})")
            pen = _Outline(font.getGlyphSet(), tolerance)
            font.getGlyphSet()[name].draw(pen)
            self._glyphs[key] = (font["hmtx"][name][0], _fill(pen.rings))
        return self._glyphs[key]


class _Outline(BasePen):
    """A glyph's contours as closed rings of points, curves flattened to a tolerance."""

    def __init__(self, glyph_set: Any, tolerance: float) -> None:
        super().__init__(glyph_set)
        self.tolerance = tolerance
        self.rings: list[list[tuple[float, float]]] = []
        self._ring: list[tuple[float, float]] = []

    def _moveTo(self, pt: tuple[float, float]) -> None:
        self._ring = [pt]

    def _lineTo(self, pt: tuple[float, float]) -> None:
        self._ring.append(pt)

    def _qCurveToOne(self, pt1: tuple[float, float], pt2: tuple[float, float]) -> None:
        self._ring += quadratic(self._ring[-1], pt1, pt2, self.tolerance)

    def _curveToOne(
        self, pt1: tuple[float, float], pt2: tuple[float, float], pt3: tuple[float, float]
    ) -> None:
        self._ring += cubic(self._ring[-1], pt1, pt2, pt3, self.tolerance)

    def _closePath(self) -> None:
        if len(self._ring) >= 3:
            self.rings.append(self._ring)
        self._ring = []

    _endPath = _closePath


def quadratic(
    p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], tolerance: float
) -> list[tuple[float, float]]:
    """The points after *p0* of a quadratic curve, each chord within *tolerance* of it.

    A chord across a parameter step h strays |p0 - 2 p1 + p2| h^2 / 4 at most.
    """
    bend = math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1])
    n = max(1, math.ceil(math.sqrt(bend / (4 * tolerance))))
    out = []
    for i in range(1, n + 1):
        t = i / n
        a, b, c = (1 - t) * (1 - t), 2 * t * (1 - t), t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return out


def cubic(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    tolerance: float,
) -> list[tuple[float, float]]:
    """The points after *p0* of a cubic curve, each chord within *tolerance* of it."""
    bend = max(
        math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1]),
        math.hypot(p1[0] - 2 * p2[0] + p3[0], p1[1] - 2 * p2[1] + p3[1]),
    )
    n = max(1, math.ceil(math.sqrt(0.75 * bend / tolerance)))
    out = []
    for i in range(1, n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t**3
        out.append(
            (
                a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1],
            )
        )
    return out


def _fill(rings: list[list[tuple[float, float]]]) -> BaseGeometry:
    """The area a set of closed rings fills by the nonzero rule, for rings that nest.

    From the largest ring inward, a ring wound as the largest one adds its
    area and one wound the other way takes it away: an outline, its counters,
    and an island inside a counter each land as drawn.
    """
    polys: list[tuple[float, BaseGeometry]] = []
    for ring in rings:
        poly = sg.Polygon(ring)
        if poly.area > 0:
            polys.append((_signed_area(ring), shapely.make_valid(poly)))
    polys.sort(key=lambda item: -abs(item[0]))
    area: BaseGeometry = sg.Polygon()
    for signed, part in polys:
        same = (signed > 0) == (polys[0][0] > 0)
        area = area.union(part) if same else area.difference(part)
    return area


def _signed_area(ring: npt.ArrayLike) -> float:
    pts = np.asarray(ring, dtype=float)
    x, y = pts[:, 0], pts[:, 1]
    return float((x * np.roll(y, -1) - np.roll(x, -1) * y).sum() / 2)


def _even_odd(rings: list[list[tuple[float, float]]]) -> BaseGeometry:
    """The area a set of closed rings fills by the even-odd rule, for rings that do not cross.

    From the largest ring inward, each ring turns over what it covers: an
    outline, the counter inside it, an island inside the counter.
    """
    polys: list[BaseGeometry] = []
    for ring in rings:
        poly = sg.Polygon(ring)
        if poly.area > 0:
            polys.append(shapely.make_valid(poly))
    polys.sort(key=lambda poly: -poly.area)
    area: BaseGeometry = sg.Polygon()
    for part in polys:
        area = area.symmetric_difference(part)
    return area


# ---------------------------------------------------------------- the drawing


def _number(el: ET.Element, name: str) -> float:
    """A numeric attribute an element must carry."""
    value = el.get(name)
    if value is None:
        raise LegendError(f"a <{el.tag.removeprefix(SVG)}> with no {name}")
    return float(value)


def _matrix(text: str | None) -> npt.NDArray[np.float64]:
    """An SVG ``transform`` attribute as a 3 x 3 matrix."""
    m = np.eye(3)
    for kind, args in _TRANSFORM.findall(text or ""):
        v = svg_read.numbers(args)
        if kind == "translate":
            step = np.array([[1, 0, v[0]], [0, 1, v[1] if len(v) > 1 else 0], [0, 0, 1]])
        elif kind == "scale":
            step = np.diag([v[0], v[1] if len(v) > 1 else v[0], 1])
        elif kind == "rotate":
            c, s = math.cos(math.radians(v[0])), math.sin(math.radians(v[0]))
            turn = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
            if len(v) == 3:
                to = np.array([[1, 0, v[1]], [0, 1, v[2]], [0, 0, 1]])
                back = np.array([[1, 0, -v[1]], [0, 1, -v[2]], [0, 0, 1]])
                step = to @ turn @ back
            else:
                step = turn
        else:
            step = np.array([[v[0], v[2], v[4]], [v[1], v[3], v[5]], [0, 0, 1]])
        m = m @ step
    return m


def _apply(geom: BaseGeometry, m: npt.NDArray[np.float64]) -> BaseGeometry:
    return shapely.affinity.affine_transform(
        geom, [m[0, 0], m[0, 1], m[1, 0], m[1, 1], m[0, 2], m[1, 2]]
    )


def _stretch(m: npt.NDArray[np.float64]) -> float:
    """The most a matrix lengthens a unit step."""
    return float(np.linalg.svd(m[:2, :2], compute_uv=False)[0])


def _color(value: str | None, where: str) -> str:
    """A fill as ``rrggbb``; a legend's ink is one flat opaque color."""
    v = (value or "").strip().lower()
    if re.fullmatch(r"#[0-9a-f]{3}", v):
        v = "#" + "".join(ch * 2 for ch in v[1:])
    if not re.fullmatch(r"#[0-9a-f]{6}", v):
        raise LegendError(f"{where}: fill {value!r} is not a flat #rrggbb color")
    return v[1:]


def _arc_steps(radius: float, tolerance: float, turn: float = 2 * math.pi) -> int:
    """How many chords keep within *tolerance* of an arc of *radius* over *turn*."""
    if radius <= tolerance:
        return max(1, math.ceil(turn / (math.pi / 2)))
    return max(1, math.ceil(turn / (2 * math.acos(1 - tolerance / radius))))


def _rounded(x: float, y: float, w: float, h: float, r: float, tolerance: float) -> sg.Polygon:
    r = min(r, w / 2, h / 2)
    if r <= 0:
        return sg.box(x, y, x + w, y + h)
    n = _arc_steps(r, tolerance, math.pi / 2)
    pts = []
    for cx, cy, start in (
        (x + w - r, y + r, -90),
        (x + w - r, y + h - r, 0),
        (x + r, y + h - r, 90),
        (x + r, y + r, 180),
    ):
        for i in range(n + 1):
            a = math.radians(start + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return sg.Polygon(pts)


def _arc(
    p0: tuple[float, float],
    rx: float,
    ry: float,
    turn_deg: float,
    large: bool,
    sweep: bool,
    p1: tuple[float, float],
    tolerance: float,
) -> list[tuple[float, float]]:
    """The points after *p0* of an SVG elliptical arc, each chord within *tolerance* of it.

    The center is found from the two ends as SVG 1.1 gives it (F.6.5); radii
    too short to span the ends are grown until they do (F.6.6).
    """
    if rx == 0 or ry == 0 or p0 == p1:
        return [p1]
    phi = math.radians(turn_deg)
    cos_p, sin_p = math.cos(phi), math.sin(phi)
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1, y1 = cos_p * dx + sin_p * dy, -sin_p * dx + cos_p * dy
    rx, ry = abs(rx), abs(ry)
    short = x1 * x1 / (rx * rx) + y1 * y1 / (ry * ry)
    if short > 1:
        rx, ry = rx * math.sqrt(short), ry * math.sqrt(short)
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    den = rx * rx * y1 * y1 + ry * ry * x1 * x1
    k = math.sqrt(max(num / den, 0.0)) * (-1 if large == sweep else 1)
    cx1, cy1 = k * rx * y1 / ry, -k * ry * x1 / rx
    cx = cos_p * cx1 - sin_p * cy1 + (p0[0] + p1[0]) / 2
    cy = sin_p * cx1 + cos_p * cy1 + (p0[1] + p1[1]) / 2
    t0 = math.atan2((y1 - cy1) / ry, (x1 - cx1) / rx)
    t1 = math.atan2((-y1 - cy1) / ry, (-x1 - cx1) / rx)
    turn = t1 - t0
    if sweep and turn < 0:
        turn += 2 * math.pi
    elif not sweep and turn > 0:
        turn -= 2 * math.pi
    n = _arc_steps(max(rx, ry), tolerance, abs(turn))
    out = []
    for i in range(1, n):
        t = t0 + turn * i / n
        ex, ey = rx * math.cos(t), ry * math.sin(t)
        out.append((cos_p * ex - sin_p * ey + cx, sin_p * ex + cos_p * ey + cy))
    out.append(p1)
    return out


def _path_rings(
    d: str, tolerance: float, where: str
) -> tuple[list[list[tuple[float, float]]], list[bool]]:
    """(rings, closed flags) of a path's M L H V Q C A Z commands, either case."""
    tokens = _PATH_TOKEN.findall(d)
    if "".join(tokens) != re.sub(r"[\s,]+", "", d):
        raise LegendError(f"{where}: a path command this module does not draw in {d!r}")
    rings: list[list[tuple[float, float]]] = []
    closed: list[bool] = []
    ring: list[tuple[float, float]] = []
    pos = start = (0.0, 0.0)
    i, cmd = 0, ""

    def take(n: int) -> list[float]:
        nonlocal i
        vals = [float(t) for t in tokens[i : i + n]]
        i += n
        return vals

    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
        if not cmd:
            raise LegendError(f"{where}: a path that does not start with a command in {d!r}")
        rel = cmd.islower()
        base = pos if rel else (0.0, 0.0)
        op = cmd.upper()
        if op == "M":
            x, y = take(2)
            if ring:
                rings.append(ring)
                closed.append(False)
            pos = start = (base[0] + x, base[1] + y)
            ring = [pos]
            cmd = "l" if rel else "L"
        elif op == "L":
            x, y = take(2)
            pos = (base[0] + x, base[1] + y)
            ring.append(pos)
        elif op == "H":
            (x,) = take(1)
            pos = (base[0] + x, pos[1])
            ring.append(pos)
        elif op == "V":
            (y,) = take(1)
            pos = (pos[0], base[1] + y)
            ring.append(pos)
        elif op == "Q":
            x1, y1, x, y = take(4)
            end = (base[0] + x, base[1] + y)
            ring += quadratic(pos, (base[0] + x1, base[1] + y1), end, tolerance)
            pos = end
        elif op == "C":
            x1, y1, x2, y2, x, y = take(6)
            end = (base[0] + x, base[1] + y)
            ring += cubic(
                pos, (base[0] + x1, base[1] + y1), (base[0] + x2, base[1] + y2), end, tolerance
            )
            pos = end
        elif op == "A":
            rx, ry, turn, large, sweep, x, y = take(7)
            if large not in (0.0, 1.0) or sweep not in (0.0, 1.0):
                raise LegendError(f"{where}: an arc flag that is not 0 or 1 in {d!r}")
            end = (base[0] + x, base[1] + y)
            ring += _arc(pos, rx, ry, turn, bool(large), bool(sweep), end, tolerance)
            pos = end
        elif op == "Z":
            rings.append(ring)
            closed.append(True)
            ring, pos = [], start
        else:  # pragma: no cover - the token pattern admits no other letter
            raise LegendError(f"{where}: path command {cmd!r}")
    if ring:
        rings.append(ring)
        closed.append(False)
    return rings, closed


def _miter_ratio(rings: list[list[tuple[float, float]]], closed: list[bool]) -> float:
    """The longest miter of a set of polylines, in stroke widths.

    Where two segments turn by an angle t, the miter reaches 1 / cos(t / 2)
    stroke widths across (SVG's ``stroke-miterlimit`` is a limit on it).
    """
    worst = 1.0
    for ring, shut in zip(rings, closed, strict=True):
        pts = [p for i, p in enumerate(ring) if i == 0 or p != ring[i - 1]]
        if shut and len(pts) > 1 and pts[0] == pts[-1]:
            pts = pts[:-1]
        if len(pts) < 3:
            continue
        corners = range(len(pts)) if shut else range(1, len(pts) - 1)
        for i in corners:
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            turn = abs(
                math.remainder(
                    math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(b[1] - a[1], b[0] - a[0]),
                    2 * math.pi,
                )
            )
            half = math.cos(turn / 2)
            worst = max(worst, math.inf if half <= 1e-12 else 1 / half)
    return worst


def _stroke(
    el: ET.Element,
    rings: list[list[tuple[float, float]]],
    closed: list[bool],
    tolerance: float,
    where: str,
) -> BaseGeometry:
    """The area a stroke along a set of polylines covers."""
    half = float(el.get("stroke-width", "0")) / 2
    if half <= 0:
        raise LegendError(f"{where}: a stroke with no stroke-width")
    cap, join = el.get("stroke-linecap", "butt"), el.get("stroke-linejoin", "miter")
    if cap not in _CAPS or join not in _JOINS:
        raise LegendError(
            f"{where}: stroke-linecap {cap!r} or stroke-linejoin {join!r} "
            f"is not one this module draws"
        )
    lines = [
        sg.LinearRing(r) if c else sg.LineString(r) for r, c in zip(rings, closed, strict=True)
    ]
    quad = max(1, _arc_steps(half, tolerance, math.pi / 2))
    if join == "miter":
        ratio = _miter_ratio(rings, closed)
        if ratio > MITER_LIMIT:
            raise LegendError(
                f"{where}: a miter {ratio:.2f} stroke widths long, over the "
                f"limit of {MITER_LIMIT:g} at which a browser bevels the corner"
            )
        return shapely.union_all(
            [
                ln.buffer(
                    half,
                    cap_style=_CAPS[cap],
                    join_style="mitre",
                    mitre_limit=MITER_LIMIT,
                    quad_segs=quad,
                )
                for ln in lines
            ]
        )
    return shapely.union_all(
        [
            ln.buffer(
                half,
                cap_style=_CAPS[cap],
                join_style="round" if join == "round" else "bevel",
                quad_segs=quad,
            )
            for ln in lines
        ]
    )


def _text(
    el: ET.Element,
    m: npt.NDArray[np.float64],
    faces: Faces,
    inherited_family: str | None,
    flatness: float,
    where: str,
) -> tuple[BaseGeometry, str]:
    family = (el.get("font-family") or inherited_family or "").split(",")[0].strip(" '\"")
    weight = int(el.get("font-weight", "400"))
    size = _number(el, "font-size")
    rel, font = faces.font(family, weight)
    own = _matrix(el.get("transform"))
    upm = font["head"].unitsPerEm
    scale = size / upm
    content = el.text or ""
    if not content.strip() or len(el):
        raise LegendError(f"{where}: a legend text is one plain run of characters")
    full = m @ own
    tolerance = flatness / (scale * _stretch(full))
    pen, run = 0.0, []
    for char in content:
        advance, outline = faces.glyph(rel, font, char, tolerance)
        if not outline.is_empty:
            run.append(shapely.affinity.translate(outline, xoff=pen))
        pen += advance
    # textLength pins the run's width; spacingAndGlyphs stretches the glyphs to it
    widen = 1.0
    if el.get("textLength") is not None:
        if el.get("lengthAdjust") != "spacingAndGlyphs":
            raise LegendError(f'{where}: textLength without lengthAdjust="spacingAndGlyphs"')
        widen = _number(el, "textLength") / (pen * scale)
    anchor = {"start": 0.0, "middle": 0.5, "end": 1.0}[el.get("text-anchor", "start")]
    x, y = float(el.get("x", "0")), float(el.get("y", "0"))
    # font units, y up -> the text's own user space, y down
    place = np.array(
        [[scale * widen, 0, x - anchor * pen * scale * widen], [0, -scale, y], [0, 0, 1]]
    )
    return _apply(shapely.union_all(run), full @ place), rel


def _disc(cx: float, cy: float, r: float, tolerance: float) -> sg.Polygon:
    n = max(8, _arc_steps(r, tolerance))
    return sg.Polygon(
        [
            (cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
            for i in range(n)
        ]
    )


def _shape(
    el: ET.Element, tag: str, m: npt.NDArray[np.float64], flatness: float, where: str
) -> BaseGeometry:
    full = m @ _matrix(el.get("transform"))
    tolerance = flatness / _stretch(full)
    stroked = el.get("stroke", "none") != "none"
    if stroked and el.get("fill") != "none":
        raise LegendError(
            f'{where}: a <{tag}> both filled and stroked (a stroked one says fill="none")'
        )
    geom: BaseGeometry
    if tag == "polygon":
        v = svg_read.numbers(el.get("points", ""))
        if len(v) % 2 or len(v) < 6:
            raise LegendError(f"{where}: a polygon of {len(v)} numbers")
        geom = sg.Polygon(list(zip(v[0::2], v[1::2], strict=True)))
    elif tag == "rect":
        rx = float(el.get("rx", el.get("ry", "0")))
        if float(el.get("ry", rx)) != rx:
            raise LegendError(f"{where}: a rect with rx unlike ry")
        geom = _rounded(
            float(el.get("x", "0")),
            float(el.get("y", "0")),
            _number(el, "width"),
            _number(el, "height"),
            rx,
            tolerance,
        )
    elif tag == "circle":
        r = _number(el, "r")
        cx, cy = float(el.get("cx", "0")), float(el.get("cy", "0"))
        if stroked:
            # a ring: the stroke lies half its width either side of the circle
            half = float(el.get("stroke-width", "0")) / 2
            if half <= 0:
                raise LegendError(f"{where}: a stroke with no stroke-width")
            geom = _disc(cx, cy, r + half, tolerance)
            if r > half:
                geom = geom.difference(_disc(cx, cy, r - half, tolerance))
        else:
            geom = _disc(cx, cy, r, tolerance)
    else:
        rings, closed = _path_rings(el.get("d", ""), tolerance, where)
        rule = el.get("fill-rule", "nonzero")
        if rule not in ("nonzero", "evenodd"):
            raise LegendError(f"{where}: fill-rule {rule!r}")
        if stroked:
            if "fill-rule" in el.attrib:
                raise LegendError(f"{where}: a fill-rule on a stroked path")
            geom = _stroke(el, rings, closed, tolerance, where)
        else:
            if not all(closed):
                raise LegendError(f"{where}: a filled path left open")
            geom = _even_odd(rings) if rule == "evenodd" else _fill(rings)
    return _apply(shapely.make_valid(geom), full)


def width_mm(geom: BaseGeometry) -> float:
    """How wide a drawn element's strokes are, in mm: what a reader weighs against a pixel.

    Each polygon is taken as the rectangle of its area and its outline's
    length (holes counted), whose shorter side is ``(P - sqrt(P^2 - 16 A)) / 4``:
    a stroke w wide gives w whatever its length, a square or a dot of side s
    gives s, a disc of diameter d about 0.79 d (where no rectangle has that
    area and outline, the square's P / 4). The element's width is its
    polygons' widths weighed by their areas, so a run of text is its glyphs'
    stroke and a filled mark its own size.
    """
    total = weighted = 0.0
    for poly in _polygons(geom):
        area, outline = poly.area, poly.length
        if area <= 0:
            continue
        width = (outline - math.sqrt(max(0.0, outline * outline - 16 * area))) / 4
        total += area
        weighted += area * width
    return weighted / total if total else 0.0


def read_legends(
    front_svg: str | Path,
    flatness: float,
    faces: Faces | None = None,
    keep: Callable[[BaseGeometry], bool] | None = None,
) -> list[Legend]:
    """[Legend] of a drawing, in its own frame (mm, y down), in paint order.

    *flatness* is the most a flattened curve strays from the drawn one, in mm.
    Every legend group of the drawing is read, whatever its plane. *keep*, when
    given, is asked of each drawn element's geometry (a run of text, a shape)
    whether to draw it, and of the texts of a group set in one face at one
    size once, of the most legible of them, so a row of labels is kept or left
    whole: one it refuses is left out before any shape is cut by another, so
    a print over a surface leaves no hole in it, and counted in its group's
    ``dropped``. A group that keeps nothing is returned with no
    shape, so its name and plane stay on record.
    """
    faces = faces or Faces()
    root = ET.parse(front_svg).getroot()  # noqa: S314  (this repository's own file)
    out = []

    def draw(
        el: ET.Element,
        m: npt.NDArray[np.float64],
        family: str | None,
        legend: Legend,
        where: str,
        drawn: list[Any],
    ) -> None:
        tag = el.tag.removeprefix(SVG)
        if legend_source.is_legend(el):
            raise LegendError(f"{where}: a legend group inside a legend group")
        if tag not in _KNOWN:
            raise LegendError(f"{where}: <{tag}> inside a legend")
        extra = sorted(set(el.attrib) - _KNOWN[tag])
        if extra:
            raise LegendError(f"{where}: <{tag}> carries {extra}, which a legend does not draw")
        family = el.get("font-family", family)
        if tag == "g":
            inner = m @ _matrix(el.get("transform"))
            for child in el:
                draw(child, inner, family, legend, where, drawn)
            return
        style = None
        if tag == "text":
            geom, rel = _text(el, m, faces, family, flatness, where)
            legend.fonts.add(rel)
            fill = _color(el.get("fill"), where)
            # texts set in one face at one size, as drawn, are kept or left together
            size = _number(el, "font-size") * _stretch(m @ _matrix(el.get("transform")))
            style = (rel, round(size, 4))
        else:
            geom = _shape(el, tag, m, flatness, where)
            fill = _color(el.get("stroke") if el.get("fill") == "none" else el.get("fill"), where)
        if geom.is_empty:
            raise LegendError(f"{where}: <{tag}> draws nothing")
        drawn.append((fill, geom, style))

    def group(el: ET.Element) -> Legend:
        """The Legend a group's own attributes describe, with no shape yet."""
        extra = sorted(set(el.attrib) - _GROUP)
        if extra:
            raise LegendError(f"a legend group carries {extra}; it takes {sorted(_GROUP)}")
        key, mark = el.get("data-key"), el.get("data-mark")
        if (key is None) == (mark is None):
            raise LegendError(
                "a legend group names one key (data-key) or one other print "
                "(data-mark), not both and not neither"
            )
        name = key if mark is None else mark
        plane = el.get("data-plane", KEYS_PLANE if mark is None else None)
        if name is None or plane is None:
            raise LegendError(f"legend {name!r}: a print that is not a key's names its data-plane")
        for what, value in (("name", name), ("plane", plane)):
            if not _NAME.fullmatch(value):
                raise LegendError(
                    f"legend {name!r}: its {what} {value!r} is not letters "
                    f"and digits joined by hyphens"
                )
        return Legend(name, plane, mark is None)

    # the groups, and of what lies around each only what legend_source digests:
    # the transforms of the <g> elements and the font family they hand down
    for el, around in legend_source.groups(root):
        m, family = np.eye(3), None
        for outer in around:
            family = outer.get("font-family", family)
            if outer.tag == SVG + "g":
                m = m @ _matrix(outer.get("transform"))
        legend = group(el)
        inner = m @ _matrix(el.get("transform"))
        drawn: list[tuple[str, BaseGeometry, Any]] = []
        for child in el:
            draw(child, inner, family, legend, f"legend {legend.name!r}", drawn)
        if keep is None:
            legend.shapes = [(fill, geom) for fill, geom, _style in drawn]
        else:
            # a text is judged with the texts set like it in its group: by
            # the most legible of them, so a line of labels goes or stays whole
            alike: dict[Any, list[BaseGeometry]] = {}
            for _fill, geom, style in drawn:
                if style is not None:
                    alike.setdefault(style, []).append(geom)
            verdict = {style: keep(max(geoms, key=width_mm)) for style, geoms in alike.items()}
            for fill, geom, style in drawn:
                if verdict[style] if style is not None else keep(geom):
                    legend.shapes.append((fill, geom))
                else:
                    legend.dropped += 1
        if not legend.shapes and not legend.dropped:
            raise LegendError(f"legend {legend.name!r} draws nothing")
        out.append(legend)
    names = [legend.name for legend in out]
    if len(set(names)) != len(names):
        twice = sorted(k for k in set(names) if names.count(k) > 1)
        raise LegendError(f"legend names repeat: {twice}")
    return out


def planes(legends: list[Legend]) -> list[str]:
    """The planes a list of legends names, in the drawing's order."""
    return list(dict.fromkeys(legend.plane for legend in legends))


# ---------------------------------------------------------------- the sheets


def _polygons(geom: BaseGeometry) -> list[sg.Polygon]:
    """The polygons of any geometry, lines and points dropped."""
    if geom.is_empty:
        return []
    if isinstance(geom, sg.Polygon):
        return [geom]
    return [p for g in getattr(geom, "geoms", []) for p in _polygons(g)]


def _area(geom: BaseGeometry) -> BaseGeometry:
    return shapely.union_all(_polygons(geom)) if not geom.is_empty else sg.Polygon()


def partition(
    legends: list[Legend], to_model: Callable[[BaseGeometry], BaseGeometry], grid: float
) -> dict[str, BaseGeometry]:
    """{fill: area} in the model's plane, on its grid, no two areas overlapping.

    *to_model* maps a front-frame geometry into the model's frame less its
    center, where the positions the model stores are whole multiples of
    *grid*. The shapes are laid in paint order: a later one of another fill
    cuts the earlier. A last pass takes from each area what any other still
    covers, on the grid, which also gives two areas that meet the same
    corners along the line they share.
    """
    areas: dict[str, BaseGeometry] = {}
    for legend in legends:
        for fill, geom in legend.shapes:
            shape = _area(shapely.set_precision(to_model(geom), grid))
            if shape.is_empty:
                continue
            for other in areas:
                if other != fill and areas[other].intersects(shape):
                    areas[other] = _area(shapely.difference(areas[other], shape, grid_size=grid))
            areas[fill] = _area(shapely.union(areas.get(fill, sg.Polygon()), shape, grid_size=grid))
    fills = sorted(areas)
    for fill in fills:
        rest = [areas[other] for other in fills if other != fill and not areas[other].is_empty]
        if rest:
            areas[fill] = _area(
                shapely.difference(areas[fill], shapely.union_all(rest), grid_size=grid)
            )
    return {fill: area for fill, area in areas.items() if not area.is_empty}


def _split_at_corners(
    steps: npt.NDArray[np.int64], tri: npt.NDArray[np.int64]
) -> npt.NDArray[np.int64]:
    """*tri* with every triangle cut where a corner of the polygon lies inside one of its edges.

    Ear clipping can leave a corner on the edge of a triangle that does not
    use it (it clips the flat ear there, of no area, and a later triangle
    spans the two edges as one). The two sides of that edge are then drawn
    from different corners, and a rasterizer may leave a hole a fraction of a
    pixel wide between them. Cut at the corner, every edge inside the polygon
    is the same edge on both its sides. *steps* are the corners in whole grid
    steps, so "on the edge" is exact.
    """

    def cut(i: int, j: int, k: int) -> list[tuple[int, int, int]]:
        for a, b, c in ((i, j, k), (j, k, i), (k, i, j)):
            along = steps[b] - steps[a]
            off = steps - steps[a]
            cross = along[0] * off[:, 1] - along[1] * off[:, 0]
            reach = off @ along
            inside = np.flatnonzero((cross == 0) & (reach > 0) & (reach < along @ along))
            if len(inside):
                m = int(inside[np.argmin(reach[inside])])
                return cut(a, m, c) + cut(m, b, c)
        return [(i, j, k)]

    out = [piece for t in tri for piece in cut(int(t[0]), int(t[1]), int(t[2]))]
    return np.asarray(out, dtype=np.int64).reshape(-1, 3)


def triangulate(
    area: BaseGeometry, grid: float
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.int64]]:
    """(points[N, 2], triangles[M, 3]) of an area on the grid, each triangle counterclockwise.

    Ear clipping uses the polygons' own corners and adds none, so every point
    is a grid point. A triangle of no area (three corners in a line) is left
    out; the corners are counted in whole grid steps, so the test is exact.
    Where that leaves a corner inside another triangle's edge, the triangle
    is cut there (``_split_at_corners``): no edge inside a polygon is one
    edge on one side and two on the other.
    """
    points, triangles, base = [], [], 0
    for part in _polygons(area):
        poly = sg.polygon.orient(part, 1.0)
        rings = [np.asarray(poly.exterior.coords)[:-1]]
        rings += [np.asarray(ring.coords)[:-1] for ring in poly.interiors]
        pts = np.vstack(rings)
        ends = np.cumsum([len(ring) for ring in rings]).astype(np.uint32)
        tri = mapbox_earcut.triangulate_float64(pts, ends).reshape(-1, 3).astype(np.int64)
        steps = np.rint(pts / grid).astype(np.int64)
        a, b, c = steps[tri[:, 0]], steps[tri[:, 1]], steps[tri[:, 2]]
        twice = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (
            c[:, 0] - a[:, 0]
        )
        tri[twice < 0] = tri[twice < 0][:, [0, 2, 1]]
        tri = _split_at_corners(steps, tri[twice != 0])
        used = np.unique(tri)
        remap = np.full(len(pts), -1, dtype=np.int64)
        remap[used] = np.arange(len(used))
        points.append(steps[used] * grid)
        triangles.append(remap[tri] + base)
        base += len(used)
    if not points:
        return np.zeros((0, 2)), np.zeros((0, 3), dtype=np.int64)
    return np.vstack(points), np.vstack(triangles)


def stroke_mm(area: BaseGeometry) -> float:
    """The mean stroke width of an area: twice the area over its outline's length."""
    return 2 * area.area / area.length if area.length else 0.0


def sheets(
    legends: list[Legend],
    plane: str,
    frame: board_faces.FaceFrame,
    center: npt.ArrayLike,
    z: float,
    grid: float,
    faces: Faces | None = None,
) -> tuple[
    list[
        tuple[str, npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64], float]
    ],
    dict[str, Any],
]:
    """The legends of one plane of a drawing as flat sheets in the build frame.

    *legends* is what ``read_legends`` gave; those of *plane* are drawn.
    *frame* is the ``board_faces.FaceFrame`` of the drawing: which face of the
    board it draws and where its origin lies in the build frame. *center* is
    the model's origin there, *z* the height the sheets lie at along the
    face's normal axis (a z for the front and the back, a y for the top and
    the bottom, an x for the sides), *grid* the model's position step, all in
    mm; *faces* the ``Faces`` the legends were read with, for the digests of
    the fonts used. Returns ``([(fill, positions[N, 3], normals[N, 3],
    triangles[M, 3], stroke_mm)], record)``, the sheets in the order of their
    fills, each facing out of its face, and what was drawn: the plane, its
    groups' names, how many of them are keys, the fonts used with their
    digests, and each sheet's counts, area and mean stroke width.
    """
    drawn = [legend for legend in legends if legend.plane == plane]
    du, dv = frame.offsets(center)

    def to_model(geom: BaseGeometry) -> BaseGeometry:
        # the drawing's frame (v down) -> along the face's u and up, less the center
        return shapely.affinity.affine_transform(geom, [1, 0, 0, -1, du, dv])

    out, counts = [], []
    for fill, area in sorted(partition(drawn, to_model, grid).items()):
        pts, tri = triangulate(area, grid)
        if not len(tri):
            continue
        width = round(stroke_mm(area), 3)
        pos = frame.embed(pts, center, z)
        nrm = frame.normals(len(pts))
        out.append((fill, pos, nrm, tri, width))
        counts.append(
            {
                "fill": f"#{fill}",
                "vertices": int(len(pts)),
                "triangles": int(len(tri)),
                "area_mm2": round(float(area.area), 3),
                "stroke_mm": width,
            }
        )
    used = sorted({rel for legend in drawn for rel in legend.fonts})
    digests = faces.used if faces is not None else {}
    record = {
        "plane": plane,
        "groups": [legend.name for legend in drawn],
        "keys": sum(1 for legend in drawn if legend.key),
        "shapes": sum(len(legend.shapes) for legend in drawn),
        "fonts": {f"fonts/{rel}": digests.get(rel) for rel in used},
        "sheets": counts,
    }
    left = sum(legend.dropped for legend in drawn)
    if left:
        # a reader's keep left these out (read_legends): a lighter model's record
        record["dropped"] = {
            "shapes": left,
            "groups": [legend.name for legend in drawn if not legend.shapes],
        }
    return out, record
