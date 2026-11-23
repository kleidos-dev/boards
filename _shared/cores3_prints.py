# SPDX-License-Identifier: MIT
"""What the M5Stack CoreS3 SE prints on its top side, with its battery base

The CoreS3 SE's model stands on the M5GO Battery Bottom3 its owner uses
(``cores3-se/model/spec.json``, module ``bottom3``), so its top side carries
two prints, one above the other:

* the frame's rating label in its recess (the model's ``top_label`` solid, x
  10.92..26.98, z -2.98..9.38): CE, the crossed-out wheelie bin and the bar
  under it, FCC's mark, Japan's radio mark and the boxed R, the Giteki number
  ``219-239073``, ``FCC ID: 2AN3WCORES3`` and ``CoreS3`` reading upward on a
  gray band;
* the base's port tag, a white sticker on the shell's tab between its two Grove
  housings (the model's ``base_port_tag`` solid, x 23.15..30.85, z
  -9.42..-5.85): ``PORT`` over a blue ``C`` and a black ``B``, each housing's
  letter on its side, on a light gray lower half, with a gray triangle
  pointing at each housing.

The base's underside prints nothing (four felt feet, the LEGO tubes and studs,
and the marks beside the pogo pins molded into the shell), and the frame's own
back label leaves with the cover the base replaces.

Both prints are measured on M5Stack's product photos (reference only, never
committed): the label on the shop's photo of the top side at 9.06 px/mm, the
tag on the shop's photo of the base's Grove side at 10.44 px/mm. Each photo
shows its print upright, the screen side up, so each is drawn upright in a
frame of its own, from its paper's top-left corner as the photo shows it (the
paper scaled to the model's solid: the label's photo paper is 16.3 x 12.7 mm
against the recess's 16.06 x 12.36, the tag's 7.66 x 3.64 against 7.7 x 3.57),
and turned half round into the top frame by its group's transform: the top
frame (``board_faces.py``) has the back at the top and runs left to right as
the front is seen, which is the photo's right to left.

The label's own face is a narrow humanist sans and the tag's a heavy
geometric one; every run is set in Inter, the only face the models carry, at
the size and ``textLength`` that put its ink on the box the photo's ink
fills (``textLength`` sets the run's advance, so a lone letter's length is
wider than its ink). Inter Bold is lighter than both photos' bold words:
``CoreS3`` and ``PORT`` carry about a quarter less ink than they print. At 9 px/mm the marks' finer
strokes (the bin's handle
and wheel, the gap between the FCC mark's two C's, the radio mark's bolt) are
a pixel or two wide, so their shapes follow the marks' published forms at the
sizes and stroke widths the photo measures. Inks: the photo's paper is gray
(226), so the gray band (142) is scaled to the model's paper (238) as 150; the
black is the photo's darkest; the tag's blue is its letter's core.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from emit_front_svg import (
    LEGEND_CLOSE,
    cardputer_label_up,
    circle,
    f,
    print_open,
    stamp_arc,
    stamp_line,
    text,
)

Point = tuple[float, float]

BLACK = "#111111"
BAND_GRAY = "#969696"  # the band behind CoreS3
TAG_BLUE = "#1a7fc0"  # PORT.C's letter, the housing's color
TAG_GRAY = "#a9a49e"  # the two triangles
TAG_BAND = "#dbdcdb"  # the tag's lower half, behind C and B

#: Where the model's solids put each print's paper in the top frame: the
#: paper's corner the photo shows at the top left (the larger x, the
#: higher z), as (u, v) of the top frame of ``face_frames.top``.
TOP_BACK_Z = -12.3  # the base's floor: the stack's back edge
LABEL_CORNER = (26.98, 9.38 - TOP_BACK_Z)
TAG_CORNER = (30.85, -5.85 - TOP_BACK_Z)


def _turned(corner: Point) -> str:
    """Open the group that sets an upright print, drawn from its top-left corner, in the top
    frame: half a turn about that corner. The legend group around it carries no transform."""
    return f'<g transform="translate({f(corner[0])} {f(corner[1])}) rotate(180)">\n'


def _poly(points: Sequence[Point], ink: str, width: float, closed: bool = False) -> str:
    d = " L ".join(f"{f(x)} {f(y)}" for x, y in points)
    return (
        f'<path d="M {d}{" Z" if closed else ""}" fill="none" stroke="{ink}" '
        f'stroke-width="{f(width)}" stroke-linejoin="round"/>\n'
    )


# ------------------------------------------------------------------ the rating label
#: Where each arc of CE ends, in degrees either side of the open side's
#: middle: the arcs turn round the closed side through 360 less twice this,
#: so their tips sit right of the centers.
CE_TIP_DEG = 83.6


def append_ce(out: list[str]) -> None:
    """CE: two arcs 5.66 mm tall with 0.82 mm strokes, cut where the photo cuts them
    (0.27 mm past their centers), and the E's middle bar, 0.86 mm thick."""
    out.append(stamp_arc(3.03, 3.55, 2.42, -CE_TIP_DEG, CE_TIP_DEG, BLACK, 0.82))
    out.append(stamp_arc(7.85, 3.55, 2.42, -CE_TIP_DEG, CE_TIP_DEG, BLACK, 0.82))
    out.append(f'<rect x="5.43" y="3.12" width="2.05" height="0.86" fill="{BLACK}"/>\n')


def append_weee(out: list[str]) -> None:
    """The crossed-out wheelie bin (its lid, handle, body, mark and wheel) and the bar under it."""
    out.append(stamp_line([(8.45, 0.85), (13.0, 5.85)], BLACK, 0.16))
    out.append(stamp_line([(13.15, 0.95), (8.5, 5.8)], BLACK, 0.16))
    out.append(f'<rect x="9.46" y="1.58" width="2.72" height="0.26" fill="{BLACK}"/>\n')
    out.append(_poly([(10.1, 1.58), (10.25, 1.17), (11.17, 1.17), (11.32, 1.58)], BLACK, 0.14))
    out.append(_poly([(9.72, 1.84), (9.97, 4.95), (11.55, 4.95), (11.86, 1.84)], BLACK, 0.16))
    out.append(f'<rect x="10.45" y="2.5" width="0.9" height="0.24" fill="{BLACK}"/>\n')
    out.append(circle(11.82, 5.0, 0.24, stroke=BLACK, stroke_w=0.12))
    out.append(f'<rect x="8.61" y="6.98" width="4.19" height="1.0" fill="{BLACK}"/>\n')


def append_fcc(out: list[str]) -> None:
    """FCC's mark: an F whose middle arm runs into two C's, one inside
    the other, open to the right."""
    out.append(
        f'<path d="M 0.28 10.31 V 7.46 H 1.7 V 7.96 H 0.76 V 8.7 H 2.3 V 9.06 H 0.76 '
        f'V 10.31 Z" fill="{BLACK}"/>\n'
    )
    out.append(stamp_arc(2.95, 8.92, 1.1, -32, 32, BLACK, 0.4))
    out.append(stamp_arc(2.98, 8.95, 0.66, -42, 42, BLACK, 0.32))


def append_giteki(out: list[str]) -> None:
    """Japan's radio mark (a ring broken on its right by a lightning stroke across its upper
    half, over a stem with two bars) and the boxed R beside it."""
    gx, gy, ring = 5.53, 7.6, 1.04
    start, end = math.radians(-18), math.radians(24)
    bolt = [
        (gx - 1.0, gy - 0.29),
        (gx - 0.03, gy - 0.47),
        (gx + 0.11, gy - 0.13),
        (gx + ring * math.cos(start), gy + ring * math.sin(start)),
    ]
    path = " L ".join(f"{f(px)} {f(py)}" for px, py in bolt)
    out.append(
        f'<path d="M {path} A {f(ring)} {f(ring)} 0 1 0 '
        f'{f(gx + ring * math.cos(end))} {f(gy + ring * math.sin(end))}" fill="none" '
        f'stroke="{BLACK}" stroke-width="0.13" stroke-linejoin="round"/>\n'
    )
    out.append(
        f'<path d="M {f(gx - 0.56)} {f(gy + 0.2)} H {f(gx + 0.6)} M {f(gx - 0.56)} '
        f'{f(gy + 0.46)} H {f(gx + 0.6)} M {f(gx + 0.03)} {f(gy + 0.46)} V {f(gy + 0.82)}" '
        f'fill="none" stroke="{BLACK}" stroke-width="0.11"/>\n'
    )
    out.append(
        f'<path d="M 6.8 6.94 H 8.21 V 8.24 H 6.8 Z" fill="none" stroke="{BLACK}" '
        'stroke-width="0.14"/>\n'
    )
    out.append(text(7.45, 7.98, "R", size=1.06, fill=BLACK, anchor="middle"))


def append_label(out: list[str]) -> None:
    """The frame's rating label: one legend group on the plane ``rating``."""
    out.append(print_open("rating-label", "rating"))
    out.append(_turned(LABEL_CORNER))
    out.append(f'<rect x="13.3" y="0" width="2.76" height="8.37" fill="{BAND_GRAY}"/>\n')
    append_ce(out)
    append_weee(out)
    append_fcc(out)
    append_giteki(out)
    out.append(text(4.53, 10.42, "219-239073", size=2.13, fill=BLACK, anchor="start", length=11.03))
    out.append(
        text(
            0.22,
            12.19,
            "FCC ID: 2AN3WCORES3",
            size=1.51,
            fill=BLACK,
            anchor="start",
            weight="500",
            length=15.56,
        )
    )
    out.append(
        cardputer_label_up(15.52, 8.09, "CoreS3", size=2.34, fill=BLACK, weight="700", length=7.76)
    )
    out.append("</g>\n")
    out.append(LEGEND_CLOSE)


# ------------------------------------------------------------------ the base's port tag
def append_port_tag(out: list[str]) -> None:
    """The base's port tag: one legend group on the plane ``port-tag``."""
    out.append(print_open("port-tag", "port-tag"))
    out.append(_turned(TAG_CORNER))
    out.append(f'<rect x="0" y="1.33" width="7.7" height="2.24" fill="{TAG_BAND}"/>\n')
    out.append(
        text(
            1.547, 1.226, "PORT", size=1.459, fill=BLACK, anchor="start", weight="700", length=4.706
        )
    )
    out.append(text(1.509, 3.317, "C", size=2.356, fill=TAG_BLUE, anchor="start", length=1.849))
    out.append(text(4.434, 3.33, "B", size=2.364, fill=BLACK, anchor="start", length=1.977))
    out.append(f'<polygon points="0.34,2.47 1.13,1.81 1.13,3.13" fill="{TAG_GRAY}"/>\n')
    out.append(f'<polygon points="7.57,2.43 6.77,1.76 6.77,3.09" fill="{TAG_GRAY}"/>\n')
    out.append("</g>\n")
    out.append(LEGEND_CLOSE)


def append_top(out: list[str]) -> None:
    """Everything the CoreS3 SE, on its base, prints on its top side."""
    append_label(out)
    append_port_tag(out)
