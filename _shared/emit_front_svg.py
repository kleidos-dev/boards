#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate the committed `svg/front.svg` of every board.

Output convention
-----------------
* `1 SVG unit = 1 mm` — true physical scale.
* `viewBox` includes a left/top margin for dimension callouts and a bottom
  margin for the device-name caption.
* Body shapes, screen aspect ratios, button positions, keyboard layouts and
  accent colors were measured on the vendors' product photos and renders,
  registered onto case millimeters, and cross-checked against the vendors'
  CAD bounding boxes and dimension drawings. Those photos and renders are not
  part of this repository (``NOTICE.md``); only the numbers taken from them
  are, here and in each ``measurements.json``.

These SVGs are self-contained vector drawings: they embed **no** third-party
imagery and no vendor screen artwork.

Screen contract
---------------
Every front exposes its display the same way, so a compositor can drop a
firmware screenshot into it:

* ``<rect id="screen-active" x y width height data-resolution="WxH"/>`` — the
  panel's active pixel area in mm: the datasheet size, centered where the
  device's front photo shows the lit pixels. Where that photo is not cropped
  exactly to the case (the Core2's shows only its black glass, turned and
  framed with a margin, because the white case frame around it vanishes into
  the white background; the CoreInk's front face is drawn larger than the
  case outline), it is registered first: the Core2's through the glass
  outline onto the glass, the CoreInk's through its four hole centers onto
  the case. The CoreS3 SE's comes from M5Stack's dimension drawing of its
  shell, which its front render matches within 0.2 mm. The three
  Plus-chassis devices take it from M5Stack's drawings of that mold, which
  dimension the active rectangle; the registered front photos of a Plus 1.1,
  a Plus2 and a Plus SE put the lit area 0.09-0.15 mm higher than that, so
  the drawn rectangle sits on the drawings' center (see ``PLUS_SCREEN_Y``).
  ``data-resolution`` is the pixel grid as seen in this front view
  (Sticks 135x240, Cardputer 240x135, Core2 / CoreS3 SE / T-Deck 320x240,
  CoreInk 200x200). The rect has no fill and no stroke; it is a geometry
  marker drawn over the bare panel: dark glass on the LCDs, blank paper on
  the CoreInk. Legends printed on the case or bezel are drawn outside it.
  No front draws a vendor's demo screen.

Legend contract
---------------
What is printed on a key, or beside it for that key, is drawn inside
``<g class="legend" data-key="<slug>">``, one group a key, where the paint
order puts it: the legend, its shifted and fn legends, the arrow behind it.
The slug is the one of the key's hotspot (``hs-key-<slug>``). Nothing else
is in the group: the cap, the strip and a colored block under a legend stay
outside it. Any other print on the board (a wordmark, the marks on a
sticker, the traces printed on a plate) is drawn inside
``<g class="legend" data-mark="<name>" data-plane="<plane>">``, the plane
being the surface it is printed on; a key's group is on the plane ``keys``
unless it names another. The board model's builder turns these groups, and
nothing it types again, into the model's ``*_legends_*`` meshes, one
``legends`` mesh a plane (``_shared/legend_mesh.py``), and refuses a model
that leaves a plane out. A mesh is one ink of one plane and says how thin
its print is, so that a reader showing the board small can leave it out;
two prints of one ink on one surface that are not as thin as each other
therefore go on two planes (the T-Deck Plus's plate: ``plate``, with its
hairline traces, and ``plate-marks``, the discs of its two round marks in
the same ink). The Cardputer ADV's and the T-Deck Plus's fronts
carry them; no other front prints anything its model does not already hold
as geometry.

To composite a screenshot, place an ``<image>`` at the ``screen-active``
x / y / width / height with ``preserveAspectRatio="none"``: the 1.14" glass
of the Sticks and the Cardputer has non-square pixels (0.110 x 0.104 mm), so
the screenshot fills the rect instead of keeping its pixel aspect.

This script is the only writer of ``<board>/svg/front.svg`` and of
``fronts-contact-sheet.svg``; the ``measurements.json`` files are maintained
by hand (``_shared/schema.md``).

Usage: ``emit_front_svg.py`` regenerates every board; ``emit_front_svg.py
<board_id> ...`` regenerates only the named ones. ``--contact-sheet`` then
also rebuilds ``fronts-contact-sheet.svg`` from every ``front.svg`` on disk:
all nine fronts on a grid of tiles, each scaled to its tile, with every id
and every ``url(#...)`` / ``href`` reference prefixed with ``<board_id>--``
so no two fronts share an id.
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Tuple

ROOT = Path(__file__).resolve().parent.parent

MARGIN_LEFT_MM = 12.0
MARGIN_TOP_MM = 6.0
MARGIN_RIGHT_MM = 12.0
MARGIN_BOTTOM_MM = 14.0
DEFS_OPEN = "<defs>\n"
DEFS_CLOSE = "</defs>\n"
SVG_CLOSE = "</svg>\n"


def f(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def svg_header(name: str, body_w: float, body_h: float) -> str:
    vb_w = body_w + MARGIN_LEFT_MM + MARGIN_RIGHT_MM
    vb_h = body_h + MARGIN_TOP_MM + MARGIN_BOTTOM_MM
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{-MARGIN_LEFT_MM} {-MARGIN_TOP_MM} {f(vb_w)} {f(vb_h)}" '
        f'width="{f(vb_w)}mm" height="{f(vb_h)}mm" '
        'shape-rendering="geometricPrecision" '
        'font-family="Inter, Helvetica, Arial, sans-serif">\n'
        f'<title>{name}: front mockup (1 SVG unit = 1 mm)</title>\n'
    )


def caption_block(name: str, body_w: float, body_h: float,
                  extra: List[str] | None = None) -> str:
    """The drawing's outside callouts: the two mm dimensions and the title.

    They sit in the margins, outside the case, and describe the drawing
    rather than the device, so they are grouped under one id a consumer can
    drop (``schema.md``, "Annotations"). Nothing inside the case outline
    belongs here: the legends printed on the hardware are part of the face.

    :param extra: Further margin callouts to carry in the same group, such
        as the Sticks' two side-key names.
    """
    return (
        '<g id="annotations">\n'
        + "".join(extra or [])
        + f'<text x="{f(body_w / 2)}" y="-3.0" font-size="1.8" fill="#7d7d80" '
        f'text-anchor="middle">{f(body_w)} mm</text>\n'
        f'<text x="-7.5" y="{f(body_h / 2)}" font-size="1.8" fill="#7d7d80" '
        f'text-anchor="middle" transform="rotate(-90 -7.5 {f(body_h / 2)})">'
        f'{f(body_h)} mm</text>\n'
        f'<text x="{f(body_w / 2)}" y="{f(body_h + 8.5)}" font-size="2.6" '
        f'fill="#2c2c30" text-anchor="middle" font-weight="700">{name}</text>\n'
        '</g>\n'
    )


def shadow_filter(device_id: str) -> str:
    return (
        f'<filter id="shadow_{device_id}" x="-10%" y="-10%" '
        'width="120%" height="120%">\n'
        '<feDropShadow dx="0.3" dy="0.6" stdDeviation="0.6" flood-opacity="0.28"/>\n'
        '</filter>\n'
    )


def linear_gradient(grad_id: str, c_top: str, c_bot: str) -> str:
    return (
        f'<linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">\n'
        f'<stop offset="0%" stop-color="{c_top}"/>\n'
        f'<stop offset="100%" stop-color="{c_bot}"/>\n'
        '</linearGradient>\n'
    )


def screen_gradient(grad_id: str, c_in: str = "#1a2336",
                    c_out: str = "#05060c") -> str:
    return (
        f'<radialGradient id="{grad_id}" cx="50%" cy="20%" r="85%">\n'
        f'<stop offset="0%" stop-color="{c_in}"/>\n'
        f'<stop offset="100%" stop-color="{c_out}"/>\n'
        '</radialGradient>\n'
    )


def rounded_rect(x: float, y: float, w: float, h: float, r: float,
                 fill: str, stroke: str = "none",
                 stroke_w: float = 0.0, opacity: float = 1.0,
                 filter_id: str | None = None) -> str:
    attrs = [
        f'x="{f(x)}"', f'y="{f(y)}"',
        f'width="{f(w)}"', f'height="{f(h)}"',
        f'rx="{f(r)}"', f'ry="{f(r)}"',
        f'fill="{fill}"',
    ]
    if stroke != "none":
        attrs.append(f'stroke="{stroke}"')
        attrs.append(f'stroke-width="{f(stroke_w)}"')
    if opacity < 1.0:
        attrs.append(f'opacity="{opacity:.2f}"')
    if filter_id:
        attrs.append(f'filter="url(#{filter_id})"')
    return f'<rect {" ".join(attrs)}/>\n'


def circle(cx: float, cy: float, r: float,
           fill: str = "none", stroke: str = "none",
           stroke_w: float = 0.0, opacity: float = 1.0) -> str:
    attrs = [f'cx="{f(cx)}"', f'cy="{f(cy)}"', f'r="{f(r)}"', f'fill="{fill}"']
    if stroke != "none":
        attrs.append(f'stroke="{stroke}"')
        attrs.append(f'stroke-width="{f(stroke_w)}"')
    if opacity < 1.0:
        attrs.append(f'opacity="{opacity:.2f}"')
    return f'<circle {" ".join(attrs)}/>\n'


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def text(x: float, y: float, content: str, *,
         size: float = 2.0, fill: str = "#222",
         anchor: str = "middle", weight: str = "400",
         opacity: float = 1.0,
         font_family: str | None = None,
         length: float | None = None,
         stroke: str = "none", stroke_w: float = 0.0,
         scale_x: float = 1.0, scale_y: float = 1.0) -> str:
    """One text run.

    ``length`` pins the run's drawn width (``textLength``, honored by
    browsers; librsvg ignores it, so ``size`` and ``scale_x`` are chosen to
    land close to it with Helvetica). ``scale_x`` / ``scale_y`` stretch the
    glyphs about the anchor point, for faces narrower or taller than any
    installed one.
    """
    if scale_x != 1.0 or scale_y != 1.0:
        attrs = ['x="0"', 'y="0"',
                 f'transform="translate({f(x)} {f(y)}) '
                 f'scale({f(scale_x)} {f(scale_y)})"']
    else:
        attrs = [f'x="{f(x)}"', f'y="{f(y)}"']
    attrs += [
        f'font-size="{f(size)}"', f'fill="{fill}"',
        f'text-anchor="{anchor}"', f'font-weight="{weight}"',
    ]
    if stroke != "none":
        attrs.append(f'stroke="{stroke}"')
        attrs.append(f'stroke-width="{f(stroke_w)}"')
    if opacity < 1.0:
        attrs.append(f'opacity="{opacity:.2f}"')
    if length is not None:
        attrs.append(f'textLength="{f(length / scale_x)}"')
        attrs.append('lengthAdjust="spacingAndGlyphs"')
    if font_family:
        # Use &apos;/&quot; to safely embed font names with spaces.
        ff = font_family.replace('"', '&quot;')
        attrs.append(f"font-family='{ff}'")
    return f'<text {" ".join(attrs)}>{_xml_escape(content)}</text>\n'


@dataclass(frozen=True)
class ScreenRect:
    """Active pixel area of a panel in mm, and its pixel grid in this view."""
    x: float
    y: float
    w: float
    h: float
    resolution: str


def append_screen(out: List[str], screen: ScreenRect) -> None:
    """Emit the ``screen-active`` marker over the bare panel the caller drew."""
    out.append(f'<rect id="screen-active" x="{f(screen.x)}" y="{f(screen.y)}" '
               f'width="{f(screen.w)}" height="{f(screen.h)}" fill="none" '
               f'data-resolution="{screen.resolution}"/>\n')


# ---------------------------------------------------------------------------
# Hotspots: where a finger lands on each physical control
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Hotspot:
    """One physical control as a press target, in front-view mm.

    The drawing already knows where every control is, so the target is
    emitted beside it instead of being measured again downstream: a front
    turned for its own layout (the Sticks are drawn portrait) would need
    that transform repeated, and the two would drift apart.

    :ivar hid: Id suffix; the element's id is ``hs-<hid>``.
    :ivar cx: Center across the front view.
    :ivar cy: Center down the front view. On a control that lives on
        another face, the center sits on the edge the face meets.
    :ivar w: Width of the control as the front draws it.
    :ivar h: Its height.
    :ivar face: Which face carries it, so an overlay can come in from the
        right side: ``front``, ``left``, ``right``, ``top`` or ``bottom``;
        ``back`` on a back drawing's own targets (``emit_back_svg.py``).
    :ivar label: What is printed on it, when anything is.
    """
    hid: str
    cx: float
    cy: float
    w: float
    h: float
    face: str = "front"
    label: str | None = None


def _xml_attr(s: str) -> str:
    return _xml_escape(s).replace('"', "&quot;")


LEGEND_CLOSE = "</g>\n"


def legend_open(slug: str) -> str:
    """Open the group that holds what is printed for the key ``slug``.

    The group draws as its children do, so wrapping them changes no pixel;
    it is what the board model's builder reads (``legend_mesh.py``). A
    key's group is on the plane ``keys``.
    """
    return f'<g class="legend" data-key="{_xml_attr(slug)}">\n'


def print_open(name: str, plane: str) -> str:
    """Open the group that holds a print that is no key's: ``name`` on the
    surface ``plane`` (a sticker, the glass, a plate).

    Closed with ``LEGEND_CLOSE`` as a key's group is. A stroked element
    inside one says ``fill="none"``, and nothing in it is translucent: the
    builder draws flat ink.
    """
    return (f'<g class="legend" data-mark="{_xml_attr(name)}" '
            f'data-plane="{_xml_attr(plane)}">\n')


def hotspots_block(spots: List[Hotspot]) -> str:
    """Emit the hotspot group: one circle per control, hidden by default.

    ``r`` is half the control's shorter side, the largest fingertip ring
    that stays on it; ``data-w`` / ``data-h`` carry the drawn box for a
    consumer that wants the whole control.
    """
    out = ['<g id="hotspots" display="none">\n']
    for spot in spots:
        attrs = [f'id="hs-{spot.hid}"', f'cx="{f(spot.cx)}"',
                 f'cy="{f(spot.cy)}"', f'r="{f(min(spot.w, spot.h) / 2)}"',
                 f'data-face="{spot.face}"', f'data-w="{f(spot.w)}"',
                 f'data-h="{f(spot.h)}"']
        if spot.label is not None:
            attrs.append(f'data-label="{_xml_attr(spot.label)}"')
        out.append(f'<circle {" ".join(attrs)}/>\n')
    out.append('</g>\n')
    return "".join(out)


# The A/B/C touch zones of the two FT6x36 boards are not printed marks but
# bands of the sensor: it reaches TOUCH_ZONE_BAND_PX rows below the last
# screen row, and a contact there routes to one of three equal columns of
# the panel's width (the Kleidos firmware's `zoneForSample`, src/hal/common/m5_touch_button_input.cpp;
# `kTouchZoneTopY`, src/config/device_config.h; both boards set
# TOUCH_ZONE_STRIP_BELOW_DISPLAY). So the targets follow the screen rect,
# in the same mm the screenshot is composited into. On the Core2 that lands
# within 0.25 mm of the three printed rings, which is the cross-check; on
# the CoreS3 SE the printed "< < O > >" is decorative and its inner
# chevrons sit across a band boundary.
TOUCH_ZONE_BAND_PX = 40
TOUCH_ZONE_COLUMNS = 3


def touch_zone_hotspots(screen: ScreenRect) -> List[Hotspot]:
    """The A/B/C touch-zone targets under a 320x240 FT6x36 panel."""
    rows = float(screen.resolution.split("x")[1])
    band_h = screen.h * TOUCH_ZONE_BAND_PX / rows
    band_w = screen.w / TOUCH_ZONE_COLUMNS
    cy = screen.y + screen.h + band_h / 2
    return [
        Hotspot(f"Touch{letter}",
                screen.x + band_w * (index + 0.5), cy, band_w, band_h)
        for index, letter in enumerate("ABC")
    ]


# ---------------------------------------------------------------------------
# Stick-class (Plus1 / Plus2 / StickS3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlusFacePalette:
    """Colors of the M5StickC Plus / Plus2 face, sampled on the vendor's
    straight-on front photos registered onto the 24 x 48 mm case.

    The four walls of the window opening darken from top to bottom (on the
    Plus 1.1 photos, luma 98 / 96 / 92 / 88 against a 115 face), so one
    vertical gradient down the opening gives all four their tone."""
    lip_top: str        # top wall of the window opening
    lip_bottom: str     # bottom wall, the darkest of the four
    slot: str           # walls of the BtnA flex slot, between rim and core
    slot_core: str      # dark gap along the middle of the slot
    slot_rim: str       # light edge where the face turns into the slot
    letter: str         # floor of the debossed "M5"
    letter_edge: str    # walls of the debossed letters


@dataclass(frozen=True)
class StickLikeStyle:
    case_top: str
    case_bot: str
    case_stroke: str
    btn_a_color: str = "#1d72d4"
    case_r: float = 3.2
    screen_resolution: str = "135x240"
    face_kind: str = "plus"
    # Active area in mm (portrait front view): the datasheet size of the
    # 1.14" ST7789 glass, horizontally centered on the body; screen_y_mm is
    # the top of the active area.
    screen_w_mm: float = 14.86
    screen_h_mm: float = 24.91
    screen_y_mm: float = 4.9
    plus: PlusFacePalette | None = None
    # Side buttons as seen from the front, (top, bottom) in mm: BtnB on the
    # right edge, Power on the left edge. None keeps the generic marks.
    btn_b_span: Tuple[float, float] | None = None
    power_span: Tuple[float, float] | None = None


#: Width of the drawn mark that stands for a key on a side edge.
STICK_SIDE_W = 0.7


def stick_side_spans(body_h: float,
                     style: StickLikeStyle) -> Tuple[Tuple[float, float],
                                                     Tuple[float, float]]:
    """The (power, BtnB) side-key spans this style draws, in mm."""
    power = style.power_span or (body_h * 0.72 - 2.6, body_h * 0.72 + 2.6)
    btn_b = style.btn_b_span or (body_h / 2 - 2.0, body_h / 2 + 2.0)
    return power, btn_b


def append_stick_side_indicators(out: List[str], body_w: float,
                                 body_h: float,
                                 style: StickLikeStyle) -> List[str]:
    """Draw the two side keys' marks; return their names for the margin.

    The marks stand for the keys and belong to the drawing of the device;
    the two names beside them are outside the case and are handed back for
    the ``annotations`` group.
    """
    side_w = STICK_SIDE_W
    (power_y0, power_y1), (btn_b_y0, btn_b_y1) = stick_side_spans(body_h,
                                                                  style)

    power_x = -side_w + 0.15
    out.append(rounded_rect(power_x, power_y0, side_w, power_y1 - power_y0,
                            r=0.25, fill="#2a2a2d"))

    btn_b_x = body_w - 0.15
    out.append(rounded_rect(btn_b_x, btn_b_y0, side_w, btn_b_y1 - btn_b_y0,
                            r=0.25, fill="#2a2a2d"))
    return [
        text(power_x - 0.5, (power_y0 + power_y1) / 2 + 0.5,
             "Power", size=1.4, fill="#7d7d80", anchor="end"),
        text(btn_b_x + 2.0, (btn_b_y0 + btn_b_y1) / 2 + 0.5,
             "BtnB", size=1.4, fill="#7d7d80", anchor="start"),
    ]


def stick_vertical_gradient(grad_id: str, y0: float, y1: float,
                            c0: str, c1: str) -> str:
    """Vertical gradient in user space from c0 at y0 to c1 at y1."""
    return (
        f'<linearGradient id="{grad_id}" gradientUnits="userSpaceOnUse" '
        f'x1="0" y1="{f(y0)}" x2="0" y2="{f(y1)}">\n'
        f'<stop offset="0%" stop-color="{c0}"/>\n'
        f'<stop offset="100%" stop-color="{c1}"/>\n'
        '</linearGradient>\n'
    )


# StickS3 face, in mm from the case's top-left corner, measured on the
# vendor's two straight-on front photos (shop image with the lit "STICK S3"
# boot screen, shop image with the screen off) registered onto the
# 24 x 48 mm case (both agree within 0.05 mm):
# * window opening in the case 3.92-20.08 x 4.08-30.18, corners about 1.0;
#   its left and bottom walls catch the light, the top wall is in shadow.
# * glass visible inside it 4.53-19.49 x 4.42-29.57: the active area plus
#   0.04 mm on the sides and 0.23 mm above it.
# * BtnA pill 6.25-17.86 x 36.50-38.60 (11.6 x 2.1, center 12.05, 37.55)
#   where its blue gives way to the dark rim; the drawn pill is 0.2 / 0.1
#   larger so its own rim lands on the same edges.
# * the rest of the face is flat: a profile across the whole width below
#   the pill holds the case tone from 0.5 mm inside one edge to 0.5 mm
#   inside the other, with no step at 2 mm, so the face carries no inner
#   plate and no print.
S3_OPENING = (3.92, 4.08, 20.08, 30.18)
S3_OPENING_R = 1.0
S3_GLASS_PAD = (0.04, 0.23, 0.04, 0.0)   # left, top, right, bottom
S3_GLASS_R = 0.3
S3_PILL_W = 11.8
S3_PILL_H = 2.2
S3_PILL_CX = 12.05
S3_PILL_CY = 37.55
# Face colors on the photos: the face #4b4b4c (slightly lighter toward the
# bottom), the four walls of the window opening each in its own tone (the
# lit left wall #7c7c7c, bottom #5a5a5a, right #585858, the shaded top wall
# #414141); the pill #0367f3 with a faint lighter top (#0e7afc) and a dark
# rim below it.
S3_WALL_LEFT = "#7a7a7b"
S3_WALL_TOP = "#414143"
S3_WALL_RIGHT_BOTTOM = "#59595b"
S3_PILL_HIGHLIGHT = "#2c86ff"
# Side keys, (top, bottom) in mm: KEY2 (BtnB) on the right side, its cap
# 19.64-28.22 on the vendor's straight side view (shop image of the right
# side, registered on the 48 mm case length); the power button on the left
# side next to the USB end, 39.5-44.5 on the vendor's two angled front
# views (the face mapped through the lit active area, the side edge read
# off that mapping, about 0.5 mm uncertain).
S3_BTN_B_SPAN = (19.64, 28.22)
S3_POWER_SPAN = (39.5, 44.5)


def append_s3_window_walls(out: List[str], device_id: str,
                           opening: Tuple[float, float, float, float],
                           glass: Tuple[float, float, float, float]) -> None:
    """The StickS3 window opening drawn as its four walls, which meet on
    the diagonals from the opening's corners to the glass corners: the
    right and bottom walls share one tone, the left and top walls are
    laid over it, clipped to the opening's rounded outline."""
    ox0, oy0, ox1, oy1 = opening
    gx0, gy0, gx1, gy1 = glass
    clip_id = f"s3_opening_{device_id}"
    out.append(DEFS_OPEN)
    out.append(f'<clipPath id="{clip_id}">\n'
               + rounded_rect(ox0, oy0, ox1 - ox0, oy1 - oy0,
                              r=S3_OPENING_R, fill="#000000")
               + '</clipPath>\n')
    out.append(DEFS_CLOSE)
    out.append(rounded_rect(ox0, oy0, ox1 - ox0, oy1 - oy0,
                            r=S3_OPENING_R, fill=S3_WALL_RIGHT_BOTTOM))
    walls = (
        (S3_WALL_LEFT, ((ox0, oy0), (gx0, gy0), (gx0, gy1), (ox0, oy1))),
        (S3_WALL_TOP, ((ox0, oy0), (ox1, oy0), (gx1, gy0), (gx0, gy0))),
    )
    for color, points in walls:
        d = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in points) + " Z"
        out.append(f'<path d="{d}" fill="{color}" '
                   f'clip-path="url(#{clip_id})"/>\n')


def append_sticks3_face(out: List[str], device_id: str,
                        body_w: float, body_h: float,
                        grad_screen: str, style: StickLikeStyle) -> None:
    lcd_w = style.screen_w_mm
    lcd_h = style.screen_h_mm
    lcd_x = (body_w - lcd_w) / 2
    lcd_y = style.screen_y_mm
    pad_l, pad_t, pad_r, pad_b = S3_GLASS_PAD
    glass = (lcd_x - pad_l, lcd_y - pad_t,
             lcd_x + lcd_w + pad_r, lcd_y + lcd_h + pad_b)
    append_s3_window_walls(out, device_id, S3_OPENING, glass)
    out.append(rounded_rect(glass[0], glass[1], glass[2] - glass[0],
                            glass[3] - glass[1], r=S3_GLASS_R,
                            fill="#0b0b0d"))
    out.append(rounded_rect(lcd_x, lcd_y, lcd_w, lcd_h, r=0.22,
                            fill=f"url(#{grad_screen})"))
    append_screen(out, ScreenRect(lcd_x, lcd_y, lcd_w, lcd_h,
                                  style.screen_resolution))
    pill_x = S3_PILL_CX - S3_PILL_W / 2
    pill_y = S3_PILL_CY - S3_PILL_H / 2
    out.append(rounded_rect(pill_x, pill_y + 0.2, S3_PILL_W, S3_PILL_H,
                            r=S3_PILL_H / 2, fill="#050506", opacity=0.45))
    out.append(rounded_rect(pill_x, pill_y, S3_PILL_W, S3_PILL_H,
                            r=S3_PILL_H / 2, fill=style.btn_a_color,
                            stroke="#1a1a1d", stroke_w=0.12))
    out.append(rounded_rect(pill_x + 0.8, pill_y + 0.3,
                            S3_PILL_W - 1.6, 0.45, r=0.22,
                            fill=S3_PILL_HIGHLIGHT, opacity=0.55))


# M5StickC Plus / Plus2 face (one chassis), in mm from the case's top-left
# corner. Measured on M5Stack's dimension drawing of the M5StickC Plus
# (docs.m5stack.com product page, also linked from the Plus2 page; front
# view registered on its 24 x 48 mm outline, 23.58 px/mm, line centers
# from profiles), and confirmed on the registered straight-on front photos
# of both models (the vendor's shop images and a real Adafruit photo of a
# Plus2 with the screen off) within 0.15 mm.
PLUS_CASE_R = 3.0
# The window is built outwards from the active area, because the drawing's
# inner line (4.606-19.426 x 3.552-28.441, corners 0.28) is the active area
# itself within 0.04 mm, and its outer line runs 0.600 mm outside it all
# round (4.006-20.026 x 2.952-29.043, corners 0.86). The registered photos
# put the visible black 0.00-0.16 mm outside that inner line on each side.
# So: glass = active area + PLUS_GLASS_PAD, opening = active area +
# PLUS_WALL, and the whole window follows screen_y_mm.
PLUS_WALL = 0.600
PLUS_GLASS_PAD = 0.08
PLUS_OPENING_R = 0.86
PLUS_GLASS_R = 0.36
# Top of the active area, one value for the three devices on this chassis.
# Both of M5Stack's drawings of this mold dimension the active rectangle as
# 14.8 x 24.86: the Plus SE's (K016-P-SE, 23.624 px/mm from its "24" and
# "48" extension lines) draws it at x 4.598-19.396, y 3.562-28.417 and the
# Plus 1.1's at 4.602-19.401, 3.566-28.421, so both center it on
# (12.00, 15.99). The fronts draw the datasheet active area instead,
# 14.86 x 24.91, which is 0.06 wider and 0.05 taller, and center it on that
# same point: across the case in x, and 24.91/2 above 15.99 here. On the
# registered straight-on photos the lit area reads 3.39-3.46 at the top and
# 28.29-28.42 at the bottom (two Plus 1.1 and two Plus2 shop images and the
# Plus SE's), center 15.84-15.93.
PLUS_SCREEN_Y = 3.535
# BtnA: a 0.6 mm flex slot shaped as an inverted U (outer corners 1.6,
# inner 1.0, legs ending in round caps at y 41.79) around the debossed
# "M5". Across the slot the photos show a light rim on both edges, the lit
# walls, and a dark gap 0.25-0.3 mm wide (0.30-0.40 mm at half depth) whose
# middle lies within 0.15 mm of the slot's center line.
PLUS_SLOT_CORE_W = 0.28
PLUS_SLOT_RIM_W = 0.14
PLUS_SLOT_PATH = (
    "M 4.608 41.49 V 35.093 A 1.6 1.6 0 0 1 6.208 33.493 H 17.834 "
    "A 1.6 1.6 0 0 1 19.434 35.093 V 41.49 "
    "A 0.3005 0.3005 0 0 1 18.833 41.49 V 35.095 "
    "A 1 1 0 0 0 17.833 34.095 H 6.209 A 1 1 0 0 0 5.209 35.095 V 41.49 "
    "A 0.3005 0.3005 0 0 1 4.608 41.49 Z")
# The gap's round ends stop at y 41.75, where the photos' dark line ends
# (41.66-41.90), inside the slot's own round caps.
PLUS_SLOT_CORE_PATH = (
    "M 4.909 41.61 V 35.094 A 1.3 1.3 0 0 1 6.209 33.794 H 17.834 "
    "A 1.3 1.3 0 0 1 19.134 35.094 V 41.61")
# Debossed "M5" glyph outlines (sharp corners), 7.14 mm tall
# (y 35.24-42.38): M stems 0.84 wide at x 6.44 and 11.58, its V meeting at
# x 9.43; 5 from x 13.20, bowl centered (15.49, 40.11) with radii 2.27
# outside and 1.44 inside.
PLUS_M_GLYPH = ((6.439, 42.38), (6.439, 35.25), (7.31, 35.25),
                (9.428, 38.11), (11.55, 35.25), (12.417, 35.25),
                (12.417, 42.38), (11.58, 42.38), (11.58, 36.95),
                (9.428, 39.73), (7.277, 36.95), (7.277, 42.38))
PLUS_5_GLYPH_PATH = (
    "M 13.203 35.239 H 17.659 V 36.083 H 14.055 V 37.842 H 15.49 "
    "A 2.2715 2.2715 0 0 1 15.49 42.385 H 13.203 V 41.554 H 15.49 "
    "A 1.44 1.44 0 0 0 15.49 38.674 H 13.203 Z")
# Side buttons in the drawing's front view: BtnB's cap on the right edge
# (it stands 0.4-0.5 mm proud on the Plus 1.1 photos, flush on the Plus2's)
# and the power button's opening on the left edge.
PLUS_BTN_B_SPAN = (13.96, 17.65)
PLUS_POWER_SPAN = (35.97, 41.19)
# Ink box of the debossed "M5" (x0, y0, x1, y1), from the two glyph paths
# above: the face a thumb presses on this chassis, the Plus SE included,
# which draws the same two glyphs raised on its flap.
PLUS_M5_INK = (6.439, 35.239, 17.659, 42.385)


def append_plus_face(out: List[str], device_id: str,
                     body_w: float, body_h: float,
                     grad_screen: str, style: StickLikeStyle) -> None:
    palette = style.plus
    assert palette is not None
    lcd_w = style.screen_w_mm
    lcd_h = style.screen_h_mm
    lcd_x = (body_w - lcd_w) / 2
    lcd_y = style.screen_y_mm
    gx0, gy0 = lcd_x - PLUS_GLASS_PAD, lcd_y - PLUS_GLASS_PAD
    gx1, gy1 = lcd_x + lcd_w + PLUS_GLASS_PAD, lcd_y + lcd_h + PLUS_GLASS_PAD
    ox0, oy0 = lcd_x - PLUS_WALL, lcd_y - PLUS_WALL
    ox1, oy1 = lcd_x + lcd_w + PLUS_WALL, lcd_y + lcd_h + PLUS_WALL
    wall_id = f"plus_wall_{device_id}"
    out.append(DEFS_OPEN)
    out.append(stick_vertical_gradient(wall_id, oy0, oy1,
                                       palette.lip_top, palette.lip_bottom))
    out.append(DEFS_CLOSE)
    out.append(rounded_rect(ox0, oy0, ox1 - ox0, oy1 - oy0,
                            r=PLUS_OPENING_R, fill=f"url(#{wall_id})"))
    out.append(rounded_rect(gx0, gy0, gx1 - gx0, gy1 - gy0,
                            r=PLUS_GLASS_R, fill="#050506"))
    out.append(rounded_rect(lcd_x, lcd_y, lcd_w, lcd_h, r=0.22,
                            fill=f"url(#{grad_screen})"))
    screen = ScreenRect(lcd_x, lcd_y, lcd_w, lcd_h, style.screen_resolution)
    append_screen(out, screen)
    # The rim stroke is centered on the slot outline; the slot's own fill
    # then covers its inner half, leaving the light edge on the face.
    out.append(f'<path d="{PLUS_SLOT_PATH}" fill="none" '
               f'stroke="{palette.slot_rim}" '
               f'stroke-width="{f(PLUS_SLOT_RIM_W)}" '
               'stroke-linejoin="round"/>\n')
    out.append(f'<path d="{PLUS_SLOT_PATH}" fill="{palette.slot}"/>\n')
    out.append(f'<path d="{PLUS_SLOT_CORE_PATH}" stroke="{palette.slot_core}" '
               f'stroke-width="{f(PLUS_SLOT_CORE_W)}" '
               'stroke-linecap="round" fill="none"/>\n')
    m_path = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in PLUS_M_GLYPH)
    for d in (m_path + " Z", PLUS_5_GLYPH_PATH):
        out.append(f'<path d="{d}" fill="{palette.letter}" '
                   f'stroke="{palette.letter_edge}" stroke-width="0.08" '
                   'stroke-linejoin="miter"/>\n')


# ---------------------------------------------------------------------------
# M5StickC Plus SE face (the Plus chassis in a translucent orange shell)
# ---------------------------------------------------------------------------


# The SE is the Plus mold without the IMU, so its window, its BtnA slot and
# its "M5" are the Plus's: M5Stack's dimension drawing of the SE (K016-P-SE,
# 7016 x 4961 px, 23.62 px/mm) and its drawing of the Plus agree within
# 0.02 mm on the window rectangle, on the slot's four lines and on every
# stroke of the "M5", whose glyph paths above are reused here. The window is
# built outwards from the active area exactly as the Plus's is (PLUS_WALL,
# PLUS_SCREEN_Y), and the case is the same 24 x 48 with R3 corners.
#
# What the shell adds is everything seen through it, measured on M5Stack's
# one straight-on front photo of the SE (its shop image of the BLE demo, the
# same shot as the docs' and The Pi Hut's) registered onto the 24 x 48 mm
# case: the LCD module, the PCB under the button, the USB-C receptacle, the
# two screw bosses, the two side keys and the frosted BtnA flap. Black parts
# read brown through the orange plastic, so none of these colors is the
# part's own; the diffuse ones are blurred, because only the LCD sits right
# under the front plate and stays crisp.
# BtnA's flex slot, as its center line: the drawing's four lines are
# 4.598 / 5.203 on the left, 18.797 / 19.396 on the right and
# 33.413 / 34.018 across the top, 0.60 apart, and its legs end in round
# caps whose semicircles bottom out at 41.70.
SE_SLOT_X = (4.90, 19.10)
SE_SLOT_TOP = 33.72
SE_SLOT_END = 41.45         # center of the legs' round end caps
SE_SLOT_R = 1.05            # center-line corner radius
SE_SLOT_W = 0.60
# What reads dark on the photo is narrower than the mold slot and differs
# from part to part: across the top only a 0.33 band at 0.10 below the center
# line is black, the slot's upper wall being lit there, and the right leg
# has a dark core over that band.
SE_SLOT_CORE_W = 0.34
SE_SLOT_CORE_DY = 0.10
# The left leg carries no dark slot above y 36.15: light runs down it from
# the top-left corner, over 0.40 of the slot's 0.60 width, and the photo
# reads 137-144 either side of it against 167-183 along it (luma; the width
# is the photo's own, undoing its 1.0 % horizontal stretch). The pale stroke
# is laid 0.46 wide so it covers the dark core around that corner.
SE_SLOT_PALE_W = 0.46
SE_SLOT_PALE_END = 36.15
SE_CAP_BOTTOM = 41.6        # where the flap blends into the face (photo)
SE_CAP_RIM_INSET = 0.08     # frosted edge of the flap, just inside the slot
# Internals glimpsed through the clear flap: the tactile switch's dome and a
# milky bar with two dark dashes over it.
SE_CAP_DOME = (12.0, 35.5, 0.65)
SE_CAP_BAR = (7.4, 39.9, 10.5, 1.1)
SE_CAP_DASHES = (9.2, 14.8)
# LCD module seen through the shell, in mm from the active area's top edge:
# the module runs 1.58 above it and 29.58 below it, its lower glass-and-FPC
# block starting at the window's bottom.
SE_LCD_X = (3.2, 20.7)
SE_LCD_DY = (-1.58, 29.58)
SE_LCD_STREAKS = (26.4, 27.1, 27.8, 28.5, 29.1)
SE_LCD_FIDUCIAL = (20.4, 26.6, 0.22)
SE_OPENING_R = 0.6          # corners of the window opening (drawing)
SE_WALL_INSET = 2.4         # inner side walls seen edge-on
SE_WALL_LINE_INSET = 2.92
SE_TOP_BAND = (3.2, 1.0, 17.6, 0.7)
# Everything behind the lower half darkens the shell down to the case
# bottom, out to x 4.2 and 19.8: at y 36.5-39.5 the photo's red channel
# falls from 236 beside the top wall to 188-221 on the left of the flap and
# 209-214 on its right, and both screw bosses sit inside that darker field.
SE_PCB = (4.2, 33.0, 15.6, 15.5)
SE_BOSSES = ((4.0, 43.5), (20.0, 43.5))
SE_BOSS_R = 1.5
SE_USB = (8.15, 42.0, 7.55, 6.3)
SE_USB_HIGHLIGHT_X = (8.6, 15.2)
SE_USB_LATCH_X = (9.45, 13.10)
SE_USB_LATCH = (44.45, 1.2, 1.85)
# Side keys, (top, bottom) in mm, read on the drawing's two side views: the
# frame of BtnB's opening on the right edge (its cap 13.85-17.64) and of the
# power key's on the left (cap 36.62-40.39). Both are flush with the front
# outline, which shows no bump.
SE_BTN_B_SPAN = (13.12, 18.37)
SE_POWER_SPAN = (35.87, 41.10)
SE_DIFFUSE_MM = 0.35
SE_FILLET_INSET = 0.70      # front fillet tangent line (drawing)
# Colors, each an area mean on the registered photo. The shell over nothing
# is #f2633e at the top and #ec542f at the bottom, its silhouette #c23a1b.
SE_WALL = "#c0522f"
SE_WALL_HI = "#ee7650"
SE_TOP_BAND_INK = "#f8834f"
SE_PCB_INK = "#a8402a"
SE_BTN_B = ("#f6865c", "#b04a2c")
SE_POWER = ("#f6904e", "#c24a2c", "#a8402a")
SE_BOSS = ("#b03a20", "#8e3a20")
SE_LCD_INK = "#7a4c3a"
SE_LCD_LOW = "#5f4136"
SE_LCD_STREAK = "#6e4b3e"
SE_LCD_FIDUCIAL_INK = "#b8846a"
SE_RING_TOP = "#5e2918"     # glass border, in shadow under the top wall
SE_RING_SIDE = "#7a4232"    # glass border, lit orange from inside the shell
SE_GLASS = "#3a2118"        # black glass below the active area, lit
SE_CAP_TOP = "#a84a2c"
SE_CAP_BOTTOM_INK = "#b65033"
SE_CAP_FROST = "#fff4ee"
SE_CAP_RIM = "#f6c3ad"
SE_CAP_DOME_INK = "#8a2c14"
SE_CAP_BAR_INK = "#f2c0aa"
SE_CAP_DASH_INK = "#5a2a1a"
SE_LETTER = "#a0351a"        # the raised "M5", through which darker
SE_LETTER_EDGE = "#fbd6c6"   # internals show; its edges are frosted
SE_SLOT_INK = "#7a2410"      # the mold slot, both legs
SE_SLOT_CORE_INK = "#1a0904"  # see-through gap across the top
SE_SLOT_LEG_INK = "#43190a"   # the right leg, which is darker than the left
SE_SLOT_PALE_INK = "#f3ae69"   # the lit left leg, area mean on the photo
SE_USB_INK = "#f0874e"
SE_USB_HI = "#f7a062"
SE_LATCH = "#7e4123"
SE_LATCH_IN = "#e88a52"


def se_slot_path(offset: float, bottom: float | None = None) -> str:
    """The BtnA slot as an inverted U, ``offset`` mm inside its centerline.

    ``offset`` 0 is the centerline itself; half the slot width is the
    outline of the flap inside it.
    """
    x0, x1 = SE_SLOT_X[0] + offset, SE_SLOT_X[1] - offset
    top = SE_SLOT_TOP + offset
    r = SE_SLOT_R - offset
    end = SE_SLOT_END if bottom is None else bottom
    return (f"M {f(x0)} {f(end)} V {f(top + r)} "
            f"A {f(r)} {f(r)} 0 0 1 {f(x0 + r)} {f(top)} "
            f"H {f(x1 - r)} "
            f"A {f(r)} {f(r)} 0 0 1 {f(x1)} {f(top + r)} V {f(end)}")


def se_slot_top_path(dy: float) -> str:
    """The slot's top segment with its two corners, corner to corner,
    ``dy`` mm below its centerline."""
    x0, x1 = SE_SLOT_X
    r = SE_SLOT_R
    return (f"M {f(x0)} {f(SE_SLOT_TOP + r)} "
            f"A {f(r)} {f(r)} 0 0 1 {f(x0 + r)} {f(SE_SLOT_TOP + dy)} "
            f"H {f(x1 - r)} "
            f"A {f(r)} {f(r)} 0 0 1 {f(x1)} {f(SE_SLOT_TOP + r)}")


def se_slot_leg_path(x: float, bottom: float = SE_SLOT_END,
                     top: float | None = None) -> str:
    """One leg of the slot, from the corner (or ``top``) down."""
    start = SE_SLOT_TOP + SE_SLOT_R if top is None else top
    return f"M {f(x)} {f(start)} V {f(bottom)}"


def se_slot_pale_path() -> str:
    """The lit left leg: half way round the top-left corner, then down."""
    cx, cy = SE_SLOT_X[0] + SE_SLOT_R, SE_SLOT_TOP + SE_SLOT_R
    k = SE_SLOT_R / math.sqrt(2.0)
    return (f"M {f(cx - k)} {f(cy - k)} "
            f"A {f(SE_SLOT_R)} {f(SE_SLOT_R)} 0 0 0 "
            f"{f(SE_SLOT_X[0])} {f(cy)} V {f(SE_SLOT_PALE_END)}")


def append_plus_se_internals(out: List[str], device_id: str) -> None:
    """The soft shapes seen through the shell, blurred as the photo shows
    them: the PCB behind the button and the USB, the two side keys and the
    two screw bosses."""
    out.append(f'<g filter="url(#diffuse_{device_id})">\n')
    pcb_x, pcb_y, pcb_w, pcb_h = SE_PCB
    out.append(rounded_rect(pcb_x, pcb_y, pcb_w, pcb_h, r=1.0,
                            fill=SE_PCB_INK, opacity=0.85))
    btn_b_y0, btn_b_y1 = SE_BTN_B_SPAN
    out.append(rounded_rect(20.9, btn_b_y0, 2.3, btn_b_y1 - btn_b_y0, r=0.5,
                            fill=SE_BTN_B[0], opacity=0.45))
    out.append(rounded_rect(21.65, 13.9, 1.25, 2.9, r=0.45,
                            fill=SE_BTN_B[1], opacity=0.55))
    power_y0, power_y1 = SE_POWER_SPAN
    out.append(rounded_rect(2.4, 34.3, 1.9, 1.5, r=0.4, fill=SE_POWER[0],
                            opacity=0.5))
    out.append(rounded_rect(2.2, power_y0, 2.1, power_y1 - power_y0, r=0.5,
                            fill=SE_POWER[1], opacity=0.35))
    out.append(rounded_rect(2.3, 36.8, 1.0, 1.4, r=0.35, fill=SE_POWER[2],
                            opacity=0.5))
    for bx, by in SE_BOSSES:
        out.append(circle(bx, by, SE_BOSS_R, fill="none", stroke=SE_BOSS[0],
                          stroke_w=0.35, opacity=0.6))
        out.append(circle(bx, by, 0.28, fill=SE_BOSS[1], opacity=0.75))
    out.append('</g>\n')


def append_plus_se_button(out: List[str], device_id: str) -> None:
    """BtnA: the frosted flap, the raised "M5" on it and the slot around it."""
    cap = se_slot_path(SE_SLOT_W / 2, bottom=SE_CAP_BOTTOM) + " Z"
    out.append(f'<path d="{cap}" fill="url(#cap_{device_id})"/>\n')
    out.append(f'<path d="{cap}" fill="{SE_CAP_FROST}" opacity="0.04"/>\n')
    dome_x, dome_y, dome_r = SE_CAP_DOME
    out.append(circle(dome_x, dome_y, dome_r, fill=SE_CAP_DOME_INK,
                      opacity=0.45))
    bar_x, bar_y, bar_w, bar_h = SE_CAP_BAR
    out.append(rounded_rect(bar_x, bar_y, bar_w, bar_h, r=bar_h / 2,
                            fill=SE_CAP_BAR_INK, opacity=0.35))
    for dash_x in SE_CAP_DASHES:
        out.append(rounded_rect(dash_x - 0.45, bar_y + 0.38, 0.9, 0.34,
                                r=0.15, fill=SE_CAP_DASH_INK, opacity=0.7))
    m_path = "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in PLUS_M_GLYPH)
    for d in (m_path + " Z", PLUS_5_GLYPH_PATH):
        out.append(f'<path d="{d}" fill="{SE_LETTER}" '
                   f'stroke="{SE_LETTER_EDGE}" stroke-width="0.06" '
                   'stroke-opacity="0.55" stroke-linejoin="round"/>\n')
    round_ends = 'stroke-linecap="round" stroke-linejoin="round"'
    # The mold slot runs the whole right leg but only the foot of the left
    # one, which is lit above y 36.15; across the top only the see-through
    # core is dark, the slot's upper wall being lit there.
    for x, top in ((SE_SLOT_X[0], SE_SLOT_PALE_END), (SE_SLOT_X[1], None)):
        out.append(f'<path d="{se_slot_leg_path(x, top=top)}" fill="none" '
                   f'stroke="{SE_SLOT_INK}" stroke-width="{f(SE_SLOT_W)}" '
                   'opacity="0.75" stroke-linecap="round"/>\n')
    out.append(f'<path d="{se_slot_top_path(SE_SLOT_CORE_DY)}" fill="none" '
               f'stroke="{SE_SLOT_CORE_INK}" '
               f'stroke-width="{f(SE_SLOT_CORE_W)}" {round_ends}/>\n')
    out.append(f'<path d="{se_slot_leg_path(SE_SLOT_X[1])}" fill="none" '
               f'stroke="{SE_SLOT_LEG_INK}" '
               f'stroke-width="{f(SE_SLOT_CORE_W)}" '
               'stroke-linecap="round"/>\n')
    out.append(f'<path d="{se_slot_pale_path()}" fill="none" '
               f'stroke="{SE_SLOT_PALE_INK}" '
               f'stroke-width="{f(SE_SLOT_PALE_W)}" {round_ends}/>\n')
    rim = se_slot_path(SE_SLOT_W / 2 + SE_CAP_RIM_INSET,
                       bottom=SE_CAP_BOTTOM - 0.2)
    out.append(f'<path d="{rim}" fill="none" stroke="{SE_CAP_RIM}" '
               f'stroke-width="0.14" opacity="0.55" {round_ends}/>\n')


def append_plus_se_usb(out: List[str]) -> None:
    """The USB-C receptacle seen through the bottom end, with its two latch
    holes; the body clip cuts it at the case edge."""
    usb_x, usb_y, usb_w, usb_h = SE_USB
    out.append(rounded_rect(usb_x, usb_y, usb_w, usb_h, r=0.5,
                            fill=SE_USB_INK))
    for x in SE_USB_HIGHLIGHT_X:
        out.append(f'<path d="M {f(x)} {f(usb_y + 0.3)} '
                   f'V {f(usb_y + usb_h)}" stroke="{SE_USB_HI}" '
                   'stroke-width="0.35" opacity="0.70" fill="none"/>\n')
    latch_y, latch_w, latch_h = SE_USB_LATCH
    for x in SE_USB_LATCH_X:
        out.append(rounded_rect(x, latch_y, latch_w, latch_h, r=0.2,
                                fill=SE_LATCH_IN))
        out.append(f'<path d="M {f(x)} {f(latch_y + latch_h)} '
                   f'V {f(latch_y + 0.2)} '
                   f'Q {f(x)} {f(latch_y)} {f(x + 0.2)} {f(latch_y)} '
                   f'H {f(x + latch_w - 0.2)} '
                   f'Q {f(x + latch_w)} {f(latch_y)} '
                   f'{f(x + latch_w)} {f(latch_y + 0.2)} '
                   f'V {f(latch_y + latch_h)}" fill="none" '
                   f'stroke="{SE_LATCH}" stroke-width="0.3" '
                   'stroke-linecap="round"/>\n')


def append_plus_se_face(out: List[str], device_id: str,
                        body_w: float, body_h: float,
                        grad_screen: str, style: StickLikeStyle) -> None:
    lcd_w = style.screen_w_mm
    lcd_h = style.screen_h_mm
    lcd_x = (body_w - lcd_w) / 2
    lcd_y = style.screen_y_mm
    ox0, oy0 = lcd_x - PLUS_WALL, lcd_y - PLUS_WALL
    ox1, oy1 = lcd_x + lcd_w + PLUS_WALL, lcd_y + lcd_h + PLUS_WALL
    out.append(DEFS_OPEN)
    out.append(f'<clipPath id="body-clip_{device_id}">\n'
               + rounded_rect(0, 0, body_w, body_h, r=style.case_r,
                              fill="#000000")
               + '</clipPath>\n')
    out.append(f'<filter id="diffuse_{device_id}" x="-20%" y="-20%" '
               'width="140%" height="140%">\n'
               f'<feGaussianBlur stdDeviation="{f(SE_DIFFUSE_MM)}"/>\n'
               '</filter>\n')
    # The glass border is in shadow along the top wall only, so the ring
    # reaches its lit tone within the first 8 % of the window's height.
    out.append(stick_vertical_gradient(f"ring_{device_id}", oy0,
                                       oy0 + (oy1 - oy0) * 0.08,
                                       SE_RING_TOP, SE_RING_SIDE))
    out.append(linear_gradient(f"cap_{device_id}", SE_CAP_TOP,
                               SE_CAP_BOTTOM_INK))
    out.append(DEFS_CLOSE)
    out.append(f'<g clip-path="url(#body-clip_{device_id})">\n')
    out.append(rounded_rect(SE_WALL_INSET, SE_WALL_INSET,
                            body_w - 2 * SE_WALL_INSET,
                            body_h - 2 * SE_WALL_INSET, r=1.2, fill="none",
                            stroke=SE_WALL, stroke_w=0.8, opacity=0.52))
    out.append(rounded_rect(SE_WALL_LINE_INSET, SE_WALL_LINE_INSET,
                            body_w - 2 * SE_WALL_LINE_INSET,
                            body_h - 2 * SE_WALL_LINE_INSET, r=0.8,
                            fill="none", stroke=SE_WALL_HI, stroke_w=0.16,
                            opacity=0.45))
    band_x, band_y, band_w, band_h = SE_TOP_BAND
    out.append(rounded_rect(band_x, band_y, band_w, band_h, r=band_h / 2,
                            fill=SE_TOP_BAND_INK, opacity=0.4))
    append_plus_se_internals(out, device_id)
    # The LCD module is the one part right under the front plate, so it is
    # drawn crisp; it follows the active area, being the same part as the
    # glass.
    mod_x0, mod_x1 = SE_LCD_X
    mod_y0, mod_y1 = lcd_y + SE_LCD_DY[0], lcd_y + SE_LCD_DY[1]
    out.append(rounded_rect(mod_x0, mod_y0, mod_x1 - mod_x0,
                            mod_y1 - mod_y0, r=0.35, fill=SE_LCD_INK))
    out.append(rounded_rect(mod_x0, oy1, mod_x1 - mod_x0, mod_y1 - oy1,
                            r=0.35, fill=SE_LCD_LOW))
    for dy in SE_LCD_STREAKS:
        out.append(f'<path d="M {f(mod_x0 + 0.3)} {f(lcd_y + dy)} '
                   f'H {f(mod_x1 - 0.3)}" stroke="{SE_LCD_STREAK}" '
                   'stroke-width="0.14" opacity="0.55" fill="none"/>\n')
    fid_x, fid_dy, fid_r = SE_LCD_FIDUCIAL
    out.append(circle(fid_x, lcd_y + fid_dy, fid_r,
                      fill=SE_LCD_FIDUCIAL_INK, opacity=0.6))
    out.append(rounded_rect(ox0, oy0, ox1 - ox0, oy1 - oy0, r=SE_OPENING_R,
                            fill=f"url(#ring_{device_id})"))
    # The true black glass border shows only along the FPC edge, below the
    # active area; the other three sides are the lit ring above.
    out.append(rounded_rect(lcd_x, lcd_y, lcd_w, oy1 - 0.06 - lcd_y, r=0.22,
                            fill=SE_GLASS))
    out.append(rounded_rect(lcd_x, lcd_y, lcd_w, lcd_h, r=0.22,
                            fill=f"url(#{grad_screen})"))
    screen = ScreenRect(lcd_x, lcd_y, lcd_w, lcd_h, style.screen_resolution)
    append_screen(out, screen)
    # The USB-C sits deeper than the flap, whose "M5" runs over its top edge.
    append_plus_se_usb(out)
    append_plus_se_button(out, device_id)
    out.append('</g>\n')
    # The internals reach the case edge, so the silhouette the body rect
    # carries is stroked again over them, with the same width and color.
    out.append(rounded_rect(0, 0, body_w, body_h, r=style.case_r,
                            fill="none", stroke=style.case_stroke,
                            stroke_w=0.25))
    out.append(rounded_rect(SE_FILLET_INSET, SE_FILLET_INSET,
                            body_w - 2 * SE_FILLET_INSET,
                            body_h - 2 * SE_FILLET_INSET,
                            r=style.case_r - SE_FILLET_INSET, fill="none",
                            stroke=SE_WALL_HI, stroke_w=0.12, opacity=0.25))


# The face each `StickLikeStyle.face_kind` draws inside the case rect.
STICK_FACES: dict[str, Callable[..., None]] = {
    "plus": append_plus_face,
    "plus_se": append_plus_se_face,
    "sticks3_brand": append_sticks3_face,
}


def stick_hotspots(body_w: float, body_h: float,
                   style: StickLikeStyle) -> List[Hotspot]:
    """BtnA on the face, and the two side keys on the edges they sit on.

    BtnA is the blue pill on the StickS3 and the debossed "M5" on the three
    boards of the Plus chassis; the side keys take the span the face draws
    their mark at, on the edge, so an overlay knows to come in from there.
    """
    if style.face_kind == "sticks3_brand":
        btn_a = Hotspot("BtnA", S3_PILL_CX, S3_PILL_CY,
                        S3_PILL_W, S3_PILL_H)
    else:
        x0, y0, x1, y1 = PLUS_M5_INK
        btn_a = Hotspot("BtnA", (x0 + x1) / 2, (y0 + y1) / 2,
                        x1 - x0, y1 - y0, label="M5")
    (power_y0, power_y1), (btn_b_y0, btn_b_y1) = stick_side_spans(body_h,
                                                                  style)
    return [
        btn_a,
        Hotspot("BtnB", body_w, (btn_b_y0 + btn_b_y1) / 2,
                STICK_SIDE_W, btn_b_y1 - btn_b_y0, face="right"),
        Hotspot("Power", 0.0, (power_y0 + power_y1) / 2,
                STICK_SIDE_W, power_y1 - power_y0, face="left"),
    ]


def gen_stick_like(device_id: str, name: str,
                   body_w: float, body_h: float,
                   *,
                   style: StickLikeStyle) -> str:
    """Stick-class portrait body.

    * Plus 1.1 / Plus2: window opening with the glass inside it, the BtnA
      flex slot around the debossed "M5", drawn from M5Stack's dimension
      drawing and checked on the photos.
    * StickS3: window opening with the glass, the blue BtnA pill.
    * Plus SE: the Plus chassis in a translucent shell, which shows the
      LCD module, the PCB, the USB-C receptacle and both side keys.
    * Side marks show BtnB (right edge) and Power (left edge).
    """
    grad_case = f"case_{device_id}"
    grad_screen = f"screen_{device_id}"
    out = [svg_header(name, body_w, body_h),
           DEFS_OPEN,
           shadow_filter(device_id),
           linear_gradient(grad_case, style.case_top, style.case_bot),
           screen_gradient(grad_screen, c_in="#101015", c_out="#020203"),
           DEFS_CLOSE]
    out.append(rounded_rect(0, 0, body_w, body_h, r=style.case_r,
                            fill=f"url(#{grad_case})",
                            stroke=style.case_stroke, stroke_w=0.25,
                            filter_id=f"shadow_{device_id}"))
    STICK_FACES[style.face_kind](out, device_id, body_w, body_h,
                                 grad_screen, style)
    labels = append_stick_side_indicators(out, body_w, body_h, style)
    out.append(hotspots_block(stick_hotspots(body_w, body_h, style)))
    out.append(caption_block(name, body_w, body_h, labels))
    out.append(SVG_CLOSE)
    return "".join(out)


# ---------------------------------------------------------------------------
# M5Stack CoreS3 SE (54×54)
# ---------------------------------------------------------------------------


# Both faces sit in the M5Stack Core shell. M5Stack's own models of it
# (M5_Hardware Basic_v2.7_Middle_Frame.stl and CoreS3-SE.stl, cut through
# at the face) give the same front: a 54.0 mm square with R5.0 corners whose
# face rounds off over its outer 1.0 mm, and a pocket whose wall meets the
# face 1.465 mm (Basic) or 1.474 mm (CoreS3 SE) inside the outline, its
# corners concentric with the outline's (R3.53). M5Stack's dimension drawing
# of the CoreS3 Lite shell draws the same pocket line, 1.473 mm in at R3.53.
# The pocket holds the CoreS3 SE's glass.
CORE_SHELL_R = 5.0
CORE_FRAME_W = 1.47
CORE_POCKET_R = CORE_SHELL_R - CORE_FRAME_W
# Shaded band just inside the case outline, where the rounded outer edge
# turns away from the light: lit at the top left, darker at the bottom right.
CORE_EDGE_BAND_W = 0.4


def append_core_shell(out: List[str], device_id: str, body_w: float,
                      body_h: float, stroke: str) -> None:
    """Case outline with its gradient, drop shadow and shaded outer edge."""
    out.append(rounded_rect(0, 0, body_w, body_h, r=CORE_SHELL_R,
                            fill=f"url(#case_{device_id})", stroke=stroke,
                            stroke_w=0.2,
                            filter_id=f"shadow_{device_id}"))
    band = CORE_EDGE_BAND_W / 2
    out.append(rounded_rect(band, band, body_w - 2 * band,
                            body_h - 2 * band, r=CORE_SHELL_R - band,
                            fill="none", stroke=f"url(#edge_{device_id})",
                            stroke_w=CORE_EDGE_BAND_W))


def core_shell_defs(device_id: str, body_w: float, body_h: float,
                    case: Tuple[str, str],
                    edge: Tuple[str, str]) -> List[str]:
    """Shadow filter and the case and outer-edge gradients."""
    return [shadow_filter(device_id),
            user_space_gradient(f"case_{device_id}", (0.0, 0.0),
                                (body_w, body_h), *case),
            user_space_gradient(f"edge_{device_id}", (0.0, 0.0),
                                (body_w, body_h), *edge)]


# M5Stack CoreS3 SE: one black glass in the shell's pocket, inside the light
# grey frame. The glass outline, the window and the panel come from
# M5Stack's dimension drawing of the CoreS3 Lite (the same shell; its front
# view draws the pocket line, the window and nothing past the outline). The
# print and the boot logo are measured on M5Stack's renders of the CoreS3
# SE, each registered onto case mm through its glass outline (four edges
# straight within 0.02 mm) placed on the pocket: the front render
# (the vendor front render) and the shop's three-quarter renders (shop images 1
# and 3). The renders agree on the print's layout and height and on the
# logo, but the three-quarter ones move the whole print 0.8 mm right of the
# front render's, which centers it on the glass as the drawing centers its
# own bottom features. The side Power and bottom Reset buttons sit in the
# side walls and the drawing's front view shows neither, so the face draws
# neither.
#
# Light grey case: the renders show the frame's face between #c5c5c5 and
# #ebebeb, the side walls near #c0c0c0.
CORES3_CASE = ("#e4e4e6", "#cacacd")
CORES3_EDGE_BAND = ("#f4f4f6", "#b2b2b7")
CORES3_CASE_STROKE = "#98989d"
CORES3_GLASS = "#0a0a0c"
# Glare on the glass, over the window's unlit border too: white, its
# opacity falling from the glass's top-left corner to zero at
# CORES3_GLARE_END. Both are a least-squares fit of that clamped ramp to the
# front render's glass brightness outside the window and the print (157 of
# 255 at the corner, 54 at the top edge's middle, 60 at the left edge's,
# black past a line through those two): the ramp runs 43 degrees down from
# the corner and is spent 27.5 mm along it, so the glass is already black
# at the bottom-left and top-right corners, as the renders show it. The
# renders show no edge where the lit rectangle meets the glass.
CORES3_GLARE_OPACITY = 0.66
CORES3_GLARE_END = (21.6, 20.2)
# Window in the glass print (x, y, w, h): the drawing's 41.6 x 31.4 mm
# rectangle centered on the case, 0.4 mm around the active area on every
# side. The front render's lit rectangle lands within 0.2 mm of it
# (6.33..47.72 x 11.38..42.52 mm); its corners are sharp.
CORES3_WINDOW = (6.2, 11.3, 41.6, 31.4)
CORES3_WINDOW_R = 0.1
# The panel's unlit border between the window edge and the active area: as
# dark as the panel's black pixels, so a dark screenshot reaches the window
# edge.
CORES3_WINDOW_FILL = "#000000"
# 2.0" ILI9342C active area: the datasheet's 40.8 x 30.6 mm centered in the
# window (the renders' lit rectangle is 41.1 to 41.4 mm wide).
CORES3_SCREEN = ScreenRect(6.6, 11.7, 40.8, 30.6, "320x240")


# Print under the window, centered on the glass as in the front render
# (ring center 27.02 mm): the red touch marks "< < O > >" and a microphone
# hole at each end (the CoreS3 SE's two microphones; it has no light
# sensor). Every height and size below is the front render's, the one view
# taken square to the face; the three-quarter renders agree on the layout
# but sit up to 0.15 mm lower, as refraction moves each mark's dark lower
# edge toward their camera.
CORES3_PRINT_X = 27.0
CORES3_PRINT_RED = "#b8493e"
# Ring (cy, centerline radius, stroke): the radius at which the render's
# red is brightest, and the width of that band at half its height.
CORES3_RING = (46.4, 1.29, 0.28)
# Chevrons: apex ink edge offsets from CORES3_PRINT_X (inner, outer), the
# row's center line, the ink width and height, and the stroke.
CORES3_CHEVRON_DX = (5.69, 9.40)
CORES3_CHEVRON_Y = 46.37
CORES3_CHEVRON_W = 0.9
CORES3_CHEVRON_H = 1.76
CORES3_CHEVRON_STROKE = 0.18
# Microphone holes: offset either side of the ring, height and radius. The
# front render draws each as a round hole with a lit bevel, its rim 13.91 /
# 13.94 mm either side of the ring and spanning 46.55 to 47.90 mm (M5Stack's
# CoreS3 Lite drawing puts its two microphone holes level, at 47.25 mm).
CORES3_MIC_DX = 13.93
CORES3_MIC_Y = 47.22
CORES3_MIC_R = 0.62
CORES3_MIC_RIM = ("#36363a", 0.08)


def cores3_chevron(apex_x: float, direction: int) -> str:
    """One touch chevron; direction -1 points left, +1 points right.

    The ink spans CORES3_CHEVRON_W from its apex edge at apex_x, and
    CORES3_CHEVRON_H tall around CORES3_CHEVRON_Y; the path runs along the
    stroke's centerline with a mitered apex.
    """
    s = CORES3_CHEVRON_STROKE
    half_h = (CORES3_CHEVRON_H - s) / 2
    depth = CORES3_CHEVRON_W - s
    # Centerline apex: half the stroke inside the ink edge, plus the miter.
    miter = (s / 2) * math.hypot(depth, half_h) / half_h
    tip_x = apex_x - direction * miter
    arm_x = tip_x - direction * (depth - miter + s / 2)
    cy = CORES3_CHEVRON_Y
    return (f'<path d="M {f(arm_x)} {f(cy - half_h)} L {f(tip_x)} {f(cy)} '
            f'L {f(arm_x)} {f(cy + half_h)}" fill="none" '
            f'stroke="{CORES3_PRINT_RED}" stroke-width="{f(s)}" '
            'stroke-linejoin="miter" stroke-linecap="butt"/>\n')


def append_cores3_print(out: List[str]) -> None:
    """Touch marks and the two microphone holes under the glass."""
    cx = CORES3_PRINT_X
    for dx in CORES3_CHEVRON_DX:
        out.append(cores3_chevron(cx - dx, -1))
        out.append(cores3_chevron(cx + dx, 1))
    ring_y, ring_r, ring_s = CORES3_RING
    out.append(circle(cx, ring_y, ring_r, stroke=CORES3_PRINT_RED,
                      stroke_w=ring_s))
    rim_color, rim_w = CORES3_MIC_RIM
    for mic_x in (cx - CORES3_MIC_DX, cx + CORES3_MIC_DX):
        out.append(circle(mic_x, CORES3_MIC_Y, CORES3_MIC_R, fill="#000000",
                          stroke=rim_color, stroke_w=rim_w))


def gen_cores3_se(device_id: str, name: str,
                  body_w: float, body_h: float) -> str:
    """M5Stack CoreS3 SE face: white frame, glass, window and touch print."""
    glass_w = body_w - 2 * CORE_FRAME_W
    glass_h = body_h - 2 * CORE_FRAME_W
    out = [svg_header(name, body_w, body_h), DEFS_OPEN]
    out.extend(core_shell_defs(device_id, body_w, body_h, CORES3_CASE,
                               CORES3_EDGE_BAND))
    out.append(white_fade_gradient(f"glare_{device_id}",
                                   (CORE_FRAME_W, CORE_FRAME_W),
                                   CORES3_GLARE_END, CORES3_GLARE_OPACITY,
                                   0.0))
    out.append(screen_gradient(f"screen_{device_id}"))
    out.append(DEFS_CLOSE)
    append_core_shell(out, device_id, body_w, body_h, CORES3_CASE_STROKE)
    out.append(rounded_rect(CORE_FRAME_W, CORE_FRAME_W, glass_w, glass_h,
                            r=CORE_POCKET_R, fill=CORES3_GLASS))
    win_x, win_y, win_w, win_h = CORES3_WINDOW
    out.append(rounded_rect(win_x, win_y, win_w, win_h, r=CORES3_WINDOW_R,
                            fill=CORES3_WINDOW_FILL))
    out.append(rounded_rect(CORE_FRAME_W, CORE_FRAME_W, glass_w, glass_h,
                            r=CORE_POCKET_R,
                            fill=f"url(#glare_{device_id})"))
    screen = CORES3_SCREEN
    out.append(rounded_rect(screen.x, screen.y, screen.w, screen.h, r=0.0,
                            fill=f"url(#screen_{device_id})"))
    append_screen(out, screen)
    append_cores3_print(out)
    out.append(hotspots_block(touch_zone_hotspots(screen)))
    out.append(caption_block(name, body_w, body_h))
    out.append(SVG_CLOSE)
    return "".join(out)


# ---------------------------------------------------------------------------
# M5Stack Core2 v1.3 (54×54, one glass front)
# ---------------------------------------------------------------------------


# The Core2's case is white: its front is one black glass panel set inside a
# thin white frame. The glass has no bezel step: the panel shows through a
# window in the glass print, and three printed rings mark the touch zones
# below it. The vendor front photo shows only the glass, turned by 0.4 degrees
# with a margin around it: the frame vanishes into the photo's white
# background. A front product photo of the same shot, where the frame's outer
# edge shows as a faint shadow line on the background, gives the frame:
# scaled so the lit window spans the datasheet's 40.8 x 30.6 mm active area,
# the glass spans 51.0 x 51.1 mm and the frame's outer edge 54.0 mm wide,
# 1.47 / 1.52 mm left / right and 1.48 mm top of the glass (1.31 mm at the
# bottom, where the shaded rounded edge pulls the line inwards); the face
# draws it even, CORE2_FRAME on every side. Every value on the glass is
# measured on the vendor front photo registered through its glass outline onto
# the 51 x 51 mm glass, and lands within 0.15 mm of the product photo. The
# side Power and bottom Reset buttons are not visible from the front, so the
# face draws neither.
#
# Case outline: the K010-V13 drawing's R5, concentric with the glass corners
# around the 1.5 mm frame within 0.1 mm.
CORE2_CORNER_R = 5.0
# White case frame. The front photo shows its face as white as the
# background, so the face stays near white, with a faint gradient from the
# lit top-left corner; a grey outline marks the rounded outer edge, and a
# band inside it shades that edge on the bottom and right, where the photo
# shows the frame's outer edge as a faint shadow line.
CORE2_CASE_TOP = "#fdfdfd"
CORE2_CASE_BOT = "#f1f1f3"
CORE2_CASE_STROKE = "#a8a8ac"
CORE2_EDGE_BAND_W = 0.4
CORE2_EDGE_BAND = ("#ffffff", "#d6d6da")
# Frame width around the glass. The glass meets it with no seam and no
# highlight: the photo steps straight from the glass to the white frame.
CORE2_FRAME = 1.5
# Glass corner radius: a rounded-rectangle fit on the glass's own edges gives
# 3.56 to 3.68 mm at the three corners the glare leaves clean (rms 0.01 mm),
# the same as the vendor front photo's outline fit once registered onto the
# 51 mm glass.
CORE2_GLASS_R = 3.6
CORE2_FACE = "#030304"
# Window in the glass print (x, y, w, h): the photo's lit rectangle.
CORE2_WINDOW = (6.71, 11.72, 40.86, 30.6)
CORE2_WINDOW_R = 0.28
# The panel's unlit border between the window edge and the active area: as
# dark as the panel's black pixels, so a dark screenshot reaches the window
# edge.
CORE2_WINDOW_FILL = "#000000"
# 2.0" ILI9342C active area, the datasheet's 40.8 x 30.6 mm centered in the
# window.
CORE2_SCREEN = ScreenRect(6.75, 11.72, 40.8, 30.6, "320x240")
# Touch-zone rings: centers, centerline radius, stroke and the photo's warm
# grey print.
CORE2_RING_XS = (13.54, 27.04, 40.51)
CORE2_RING_Y = 45.11
CORE2_RING_R = 1.04
CORE2_RING_STROKE = 0.19
CORE2_RING_COLOR = "#6b645f"
# Faint round mark under the glass, left of the first ring (cx, cy, r).
CORE2_MARK = (11.27, 46.32, 0.31)
# Glare on the glass: white, its opacity falling linearly from the glass's
# top-left corner to zero at CORE2_GLARE_END (a least-squares plane through
# the photo's glass brightness outside the window).
CORE2_GLARE_OPACITY = 0.635
CORE2_GLARE_END = (20.57, 28.36)


def user_space_gradient(grad_id: str, start: Tuple[float, float],
                        end: Tuple[float, float], c_start: str,
                        c_end: str) -> str:
    """Opaque linear gradient in user space between two colors."""
    return (
        f'<linearGradient id="{grad_id}" gradientUnits="userSpaceOnUse" '
        f'x1="{f(start[0])}" y1="{f(start[1])}" '
        f'x2="{f(end[0])}" y2="{f(end[1])}">\n'
        f'<stop offset="0%" stop-color="{c_start}"/>\n'
        f'<stop offset="100%" stop-color="{c_end}"/>\n'
        '</linearGradient>\n'
    )


def white_fade_gradient(grad_id: str, start: Tuple[float, float],
                        end: Tuple[float, float], opacity_start: float,
                        opacity_end: float) -> str:
    """White linear gradient in user space, fading between two opacities."""
    return (
        f'<linearGradient id="{grad_id}" gradientUnits="userSpaceOnUse" '
        f'x1="{f(start[0])}" y1="{f(start[1])}" '
        f'x2="{f(end[0])}" y2="{f(end[1])}">\n'
        f'<stop offset="0%" stop-color="#ffffff" '
        f'stop-opacity="{f(opacity_start)}"/>\n'
        f'<stop offset="100%" stop-color="#ffffff" '
        f'stop-opacity="{f(opacity_end)}"/>\n'
        '</linearGradient>\n'
    )


def append_core2_case(out: List[str], device_id: str,
                      body_w: float, body_h: float) -> None:
    """White case frame: its gradient, outline and shaded outer edge."""
    out.append(rounded_rect(0, 0, body_w, body_h, r=CORE2_CORNER_R,
                            fill=f"url(#case_{device_id})",
                            stroke=CORE2_CASE_STROKE, stroke_w=0.2,
                            filter_id=f"shadow_{device_id}"))
    band = CORE2_EDGE_BAND_W / 2
    out.append(rounded_rect(band, band, body_w - 2 * band,
                            body_h - 2 * band, r=CORE2_CORNER_R - band,
                            fill="none", stroke=f"url(#edge_{device_id})",
                            stroke_w=CORE2_EDGE_BAND_W))


def append_core2_glass(out: List[str], device_id: str,
                       body_w: float, body_h: float) -> None:
    """Black glass inside the frame, with its glare."""
    glass_w = body_w - 2 * CORE2_FRAME
    glass_h = body_h - 2 * CORE2_FRAME
    out.append(rounded_rect(CORE2_FRAME, CORE2_FRAME, glass_w, glass_h,
                            r=CORE2_GLASS_R, fill=CORE2_FACE))
    out.append(rounded_rect(CORE2_FRAME, CORE2_FRAME, glass_w, glass_h,
                            r=CORE2_GLASS_R, fill=f"url(#glare_{device_id})"))


def gen_core2(device_id: str, name: str,
              body_w: float, body_h: float) -> str:
    """M5Stack Core2 v1.3 face: white frame, glass, window and touch rings."""
    grad_screen = f"screen_{device_id}"
    out = [svg_header(name, body_w, body_h),
           DEFS_OPEN,
           shadow_filter(device_id),
           user_space_gradient(f"case_{device_id}", (0.0, 0.0),
                               (body_w, body_h), CORE2_CASE_TOP,
                               CORE2_CASE_BOT),
           user_space_gradient(f"edge_{device_id}", (0.0, 0.0),
                               (body_w, body_h), *CORE2_EDGE_BAND),
           white_fade_gradient(f"glare_{device_id}",
                               (CORE2_FRAME, CORE2_FRAME), CORE2_GLARE_END,
                               CORE2_GLARE_OPACITY, 0.0),
           screen_gradient(grad_screen),
           DEFS_CLOSE]
    append_core2_case(out, device_id, body_w, body_h)
    append_core2_glass(out, device_id, body_w, body_h)
    win_x, win_y, win_w, win_h = CORE2_WINDOW
    out.append(rounded_rect(win_x, win_y, win_w, win_h, r=CORE2_WINDOW_R,
                            fill=CORE2_WINDOW_FILL))
    screen = CORE2_SCREEN
    out.append(rounded_rect(screen.x, screen.y, screen.w, screen.h,
                            r=0.15, fill=f"url(#{grad_screen})"))
    append_screen(out, screen)
    for ring_x in CORE2_RING_XS:
        out.append(circle(ring_x, CORE2_RING_Y, CORE2_RING_R,
                          stroke=CORE2_RING_COLOR,
                          stroke_w=CORE2_RING_STROKE))
    mark_x, mark_y, mark_r = CORE2_MARK
    out.append(circle(mark_x, mark_y, mark_r, fill="#0d0d0f"))
    out.append(hotspots_block(touch_zone_hotspots(screen)))
    out.append(caption_block(name, body_w, body_h))
    out.append(SVG_CLOSE)
    return "".join(out)


# ---------------------------------------------------------------------------
# CoreInk (40 × 56 e-paper)
# ---------------------------------------------------------------------------


# M5Stack CoreInk front in case mm. The four LEGO-compatible holes sit on an
# 8 mm grid, 4 mm in from each edge. The vendor front photo shows the front face
# 1.2 % larger than the case silhouette and 0.4 mm left of it, so every
# feature below was measured on the photo and mapped onto the case through
# the four hole centers; the e-paper's pixel pitch (0.138 mm) lands on the
# datasheet value through the same mapping.
COREINK_HOLES = ((4.0, 4.0), (36.0, 4.0), (4.0, 52.0), (36.0, 52.0))
COREINK_HOLE_R = 2.3
COREINK_COUNTERSINK_R = 3.15
# 1.54" GDEY0154D67 e-paper: 200 x 200 px at 0.138 mm. The factory clock's
# pixels in the photo put the active area here.
COREINK_SCREEN = ScreenRect(6.39, 11.66, 27.6, 27.6, "200x200")
# Window opening in the front cover (x0, y0, x1, y1); its bevel walls run
# down to the edge of the active area, so a capture fills the visible paper.
COREINK_WINDOW = (4.96, 10.695, 35.19, 40.235)
COREINK_TAB = (9.19, 30.81, 2.9)
COREINK_PAPER = "#c8c8c4"
# Right-edge pocket and the jog wheel in it: the pocket's floor and its two
# sloped ends, then the wheel's rim as the photo shows it, from the pocket
# wall out to COREINK_DIAL_REACH_X. The wheel rocks up, presses in and
# rocks down (GPIO 37 / 38 / 39); measurements.json puts the three detents
# COREINK_DIAL_PITCH apart around the wheel's own center.
COREINK_POCKET = (9.95, 13.75, 25.75, 29.6)
COREINK_POCKET_X = 37.53
COREINK_DIAL_SPAN = (15.87, 24.02)
COREINK_DIAL_WALL_X = 37.92
COREINK_DIAL_REACH_X = 39.73
COREINK_DIAL_PITCH = 2.05
# The two plain keys in the case walls, each a tongue molded into the back
# shell, flush with its wall (M5Stack's CoreInk.stl, the file the board's
# model is built from): its center along the edge and the width of its pad's
# face. The power key (G27) is in the right wall, under the dial's pocket:
# opening y 37.97..44.03, pad y 39.06..42.94, z 8.3..12.1 from the back. The
# top key (G5, BtnEXT) is in the top end: opening x 22.27..29.73, pad
# x 23.36..28.64, z 3.5..7.9. Neither shows from the front, so the drawing
# has no mark for them: each is a target on the edge its wall meets and a
# name in the margin. The third plain key, the reset, is on the back
# (coreink_back.py).
COREINK_POWER_KEY = (41.0, 3.88)
COREINK_TOP_KEY = (26.0, 5.28)
# Debossed logo outline as polygons in drawing order (clockwise on screen):
# the M (stems 1.19 mm, V-notch at x 16.52) and the 5, whose bowl is two
# circular arcs given as (cx, cy, r, start, end) in degrees.
COREINK_M_OUTLINE: List[Tuple[float, float]] = [
    (12.32, 42.94), (13.51, 42.94), (16.52, 46.81), (19.54, 42.94),
    (20.72, 42.94), (20.72, 52.81), (19.54, 52.81), (19.54, 45.35),
    (16.52, 49.2), (13.51, 45.35), (13.51, 52.81), (12.32, 52.81)]
COREINK_5_TOP: List[Tuple[float, float]] = [
    (21.78, 42.94), (28.19, 42.94), (28.19, 44.16), (22.97, 44.16),
    (22.97, 46.51)]
COREINK_5_OUTER_BOWL = (25.03, 49.66, 3.25, -75.7, 75.7)
COREINK_5_INNER_BOWL = (24.58, 49.77, 2.37, 56.6, -54.5)
# Unit vector toward the light that shades the debossed walls (upper left).
COREINK_LIGHT = (-0.7071, -0.7071)


def coreink_body_path(body_w: float, body_h: float) -> str:
    """Case outline (3 mm corners) with the four through holes cut out."""
    r = f(3.0)
    w, h = f(body_w), f(body_h)
    d = [f"M {r} 0 H {f(body_w - 3.0)} A {r} {r} 0 0 1 {w} {r} "
         f"V {f(body_h - 3.0)} A {r} {r} 0 0 1 {f(body_w - 3.0)} {h} "
         f"H {r} A {r} {r} 0 0 1 0 {f(body_h - 3.0)} "
         f"V {r} A {r} {r} 0 0 1 {r} 0 Z"]
    hr = f(COREINK_HOLE_R)
    for cx, cy in COREINK_HOLES:
        d.append(f"M {f(cx - COREINK_HOLE_R)} {f(cy)} "
                 f"a {hr} {hr} 0 1 0 {f(2 * COREINK_HOLE_R)} 0 "
                 f"a {hr} {hr} 0 1 0 {f(-2 * COREINK_HOLE_R)} 0 Z")
    return " ".join(d)


def append_coreink_holes(out: List[str], device_id: str) -> None:
    """Countersink ring around each bore: shaded on its upper-left slope,
    lit on its lower-right slope."""
    grad = f"countersink_{device_id}"
    out.append(DEFS_OPEN)
    out.append(f'<linearGradient id="{grad}" x1="0" y1="0" x2="1" y2="1">\n'
               '<stop offset="0%" stop-color="#b0b0ac"/>\n'
               '<stop offset="45%" stop-color="#d8d8d4"/>\n'
               '<stop offset="75%" stop-color="#fbfbfa"/>\n'
               '<stop offset="100%" stop-color="#ffffff"/>\n'
               '</linearGradient>\n')
    out.append(DEFS_CLOSE)
    ro = COREINK_COUNTERSINK_R
    ri = COREINK_HOLE_R
    for cx, cy in COREINK_HOLES:
        out.append(f'<path d="M {f(cx - ro)} {f(cy)} '
                   f'a {f(ro)} {f(ro)} 0 1 0 {f(2 * ro)} 0 '
                   f'a {f(ro)} {f(ro)} 0 1 0 {f(-2 * ro)} 0 Z '
                   f'M {f(cx - ri)} {f(cy)} '
                   f'a {f(ri)} {f(ri)} 0 1 0 {f(2 * ri)} 0 '
                   f'a {f(ri)} {f(ri)} 0 1 0 {f(-2 * ri)} 0 Z" '
                   f'fill="url(#{grad})" fill-rule="evenodd"/>\n')
        out.append(circle(cx, cy, ro, stroke="#c9c9c5", stroke_w=0.1))
        out.append(circle(cx, cy, ri, stroke="#8e8e8a", stroke_w=0.14))


def append_coreink_tab(out: List[str]) -> None:
    """Seam of the top cover tab, open at the top edge."""
    x0, x1, y1 = COREINK_TAB
    r = 0.7
    seam = (f"M {f(x0)} 0 V {f(y1 - r)} Q {f(x0)} {f(y1)} {f(x0 + r)} {f(y1)} "
            f"H {f(x1 - r)} Q {f(x1)} {f(y1)} {f(x1)} {f(y1 - r)} V 0")
    out.append(f'<path d="{seam}" fill="none" stroke="#ffffff" '
               'stroke-width="0.16" transform="translate(0.1 0.12)"/>\n')
    out.append(f'<path d="{seam}" fill="none" stroke="#9a9a96" '
               'stroke-width="0.14"/>\n')


def append_coreink_window(out: List[str], device_id: str) -> None:
    """Window opening, its bevel walls, the paper and the demo clock."""
    wx0, wy0, wx1, wy1 = COREINK_WINDOW
    s = COREINK_SCREEN
    px0, py0, px1, py1 = s.x, s.y, s.x + s.w, s.y + s.h
    clip_id = f"window_{device_id}"
    out.append(DEFS_OPEN)
    out.append(f'<clipPath id="{clip_id}">\n'
               + rounded_rect(wx0, wy0, wx1 - wx0, wy1 - wy0, r=0.6,
                              fill="#000")
               + '</clipPath>\n')
    out.append(DEFS_CLOSE)
    # Bevel walls lit from the upper left: the upper and left walls fall in
    # shade, the lower and right walls catch the light.
    walls = [
        ([(wx0, wy0), (wx1, wy0), (px1, py0), (px0, py0)], "#d3d3cf"),
        ([(wx0, wy0), (px0, py0), (px0, py1), (wx0, wy1)], "#c6c6c2"),
        ([(wx1, wy0), (wx1, wy1), (px1, py1), (px1, py0)], "#fafaf8"),
        ([(wx0, wy1), (px0, py1), (px1, py1), (wx1, wy1)], "#f4f4f2"),
    ]
    out.append(f'<g clip-path="url(#{clip_id})">\n')
    for points, fill in walls:
        pts = " ".join(f"{f(x)},{f(y)}" for x, y in points)
        out.append(f'<polygon points="{pts}" fill="{fill}"/>\n')
    out.append('</g>\n')
    out.append(rounded_rect(wx0, wy0, wx1 - wx0, wy1 - wy0, r=0.6,
                            fill="none", stroke="#d9d9d5", stroke_w=0.1))
    # Gap between the cover and the panel: a dark line in the shade along
    # the upper and left edges, a fine one along the lit edges.
    out.append(f'<rect x="{f(px0 - 0.05)}" y="{f(py0 - 0.05)}" '
               f'width="{f(s.w + 0.1)}" height="{f(s.h + 0.1)}" '
               'fill="none" stroke="#a6a6a2" stroke-width="0.1"/>\n')
    out.append(f'<path d="M {f(px0 - 0.11)} {f(py1)} V {f(py0 - 0.11)} '
               f'H {f(px1)}" fill="none" stroke="#85857f" '
               'stroke-width="0.22"/>\n')
    out.append(f'<rect x="{f(px0)}" y="{f(py0)}" width="{f(s.w)}" '
               f'height="{f(s.h)}" fill="{COREINK_PAPER}"/>\n')
    append_screen(out, s)


def append_coreink_dial(out: List[str], device_id: str,
                        body_w: float) -> None:
    """Pocket in the right edge and the knurled rim of the dial wheel in it."""
    grad = f"dial_pocket_{device_id}"
    out.append(DEFS_OPEN)
    out.append(f'<linearGradient id="{grad}" x1="0" y1="0" x2="1" y2="0">\n'
               '<stop offset="0%" stop-color="#cfcfcb"/>\n'
               '<stop offset="55%" stop-color="#bdbdb9"/>\n'
               '<stop offset="100%" stop-color="#c9c9c5"/>\n'
               '</linearGradient>\n')
    out.append(DEFS_CLOSE)
    top, floor_top, floor_bottom, bottom = COREINK_POCKET
    pocket = [(body_w, top), (COREINK_POCKET_X, floor_top),
              (COREINK_POCKET_X, floor_bottom), (body_w, bottom)]
    pts = " ".join(f"{f(x)},{f(y)}" for x, y in pocket)
    out.append(f'<polygon points="{pts}" fill="url(#{grad})" '
               'stroke="#b2b2ae" stroke-width="0.08"/>\n')
    # Wheel rim: the arc of a wheel whose axle sits behind the cover, seen
    # from the pocket wall (x 37.92, y 15.87-24.02) out to x 39.73, knurled
    # with ten teeth 0.22 mm deep.
    wall_x, reach_x = COREINK_DIAL_WALL_X, COREINK_DIAL_REACH_X
    top_y, bottom_y = COREINK_DIAL_SPAN
    cy = (top_y + bottom_y) / 2
    half_chord = (bottom_y - top_y) / 2
    depth = reach_x - wall_x
    r_out = (depth * depth + half_chord * half_chord) / (2 * depth)
    r_in = r_out - 0.22
    cx = reach_x - r_out
    half = math.asin(half_chord / r_out)
    teeth = 10
    rim = [f"M {f(wall_x)} {f(top_y)}"]
    for i in range(2 * teeth + 1):
        a = -half + i * half / teeth
        rr = r_out if i % 2 == 0 else r_in
        rim.append(f"L {f(cx + rr * math.cos(a))} {f(cy + rr * math.sin(a))}")
    rim.append(f"L {f(wall_x)} {f(bottom_y)} Z")
    out.append(f'<path d="{" ".join(rim)}" fill="#262628" '
               'stroke="#111113" stroke-width="0.08" '
               'stroke-linejoin="round"/>\n')
    out.append(f'<line x1="{f(wall_x + 0.2)}" y1="{f(cy - 3.2)}" '
               f'x2="{f(wall_x + 0.2)}" y2="{f(cy + 3.2)}" '
               'stroke="#4a4a4e" stroke-width="0.12"/>\n')


def coreink_arc_points(arc: Tuple[float, float, float, float, float],
                       steps: int = 14) -> List[Tuple[float, float]]:
    cx, cy, r, a0, a1 = arc
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steps)))
            for i in range(steps + 1)]


def coreink_m5_outlines() -> List[List[Tuple[float, float]]]:
    five = list(COREINK_5_TOP)
    five += coreink_arc_points(COREINK_5_OUTER_BOWL)
    five += [(21.78, 52.81), (21.78, 51.72)]
    five += coreink_arc_points(COREINK_5_INNER_BOWL)
    five += [(21.78, 47.82)]
    return [COREINK_M_OUTLINE, five]


def append_coreink_debossed_m5(out: List[str], device_id: str) -> None:
    """The M5 debossed into the cover. Each wall of the recess is shaded by
    how squarely it faces the light from the upper left: walls facing away
    draw a dark line, walls facing it a bright one, walls along the light
    almost nothing. The lines are clipped to the inside of the glyphs."""
    outlines = coreink_m5_outlines()
    shape = " ".join(
        "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
        for pts in outlines)
    clip_id = f"m5_deboss_{device_id}"
    out.append(f'{DEFS_OPEN}<clipPath id="{clip_id}"><path d="{shape}"/>'
               f'</clipPath>\n{DEFS_CLOSE}')
    out.append(f'<g clip-path="url(#{clip_id})" fill="none" '
               'stroke-linecap="round">\n')
    lx, ly = COREINK_LIGHT
    for pts in outlines:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            length = math.hypot(x1 - x0, y1 - y0)
            if length < 1e-6:
                continue
            # Outward normal of a clockwise outline; the wall faces inward.
            nx, ny = (y1 - y0) / length, -(x1 - x0) / length
            facing = -(nx * lx + ny * ly)
            if facing < 0:
                color, width, alpha = "#a5a5a1", 0.36, min(1.0, -facing * 1.1)
            else:
                color, width, alpha = "#ffffff", 0.64, min(1.0, facing * 1.1)
            if alpha < 0.05:
                continue
            out.append(f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" '
                       f'y2="{f(y1)}" stroke="{color}" '
                       f'stroke-width="{f(width)}" opacity="{alpha:.2f}"/>\n')
    out.append('</g>\n')


def coreink_hotspots(body_w: float) -> List[Hotspot]:
    """The jog wheel's three detents, the power key and the top key.

    The wheel shows in its pocket, so its targets sit on it. The power key
    (right wall) and the top key (top end) are flush with their walls and do
    not show from the front: each target sits on the edge its wall meets,
    centered on the key, as deep as the mark a Stick's side key is drawn
    with (``STICK_SIDE_W``), so an overlay comes in from that side.
    """
    cx = (COREINK_DIAL_WALL_X + COREINK_DIAL_REACH_X) / 2
    depth = COREINK_DIAL_REACH_X - COREINK_DIAL_WALL_X
    top_y, bottom_y = COREINK_DIAL_SPAN
    wheel_cy = (top_y + bottom_y) / 2
    power_cy, power_span = COREINK_POWER_KEY
    top_cx, top_span = COREINK_TOP_KEY
    spots = [Hotspot(hid, cx, wheel_cy + dy * COREINK_DIAL_PITCH, depth,
                     COREINK_DIAL_PITCH, face="right", label=label)
             for hid, dy, label in (("DialUp", -1.0, "\u25b2"),
                                    ("DialMid", 0.0, "OK"),
                                    ("DialDown", 1.0, "\u25bc"))]
    spots.append(Hotspot("Power", body_w, power_cy, STICK_SIDE_W, power_span,
                         face="right"))
    spots.append(Hotspot("BtnEXT", top_cx, 0.0, top_span, STICK_SIDE_W,
                         face="top"))
    return spots


def coreink_key_names(body_w: float) -> List[str]:
    """The two wall keys' names, in the margins beside where each key is."""
    power_cy, _ = COREINK_POWER_KEY
    top_cx, _ = COREINK_TOP_KEY
    return [
        text(body_w + 1.2, power_cy + 0.5, "Power", size=1.4,
             fill="#7d7d80", anchor="start"),
        text(top_cx, -0.6, "BtnEXT", size=1.4, fill="#7d7d80",
             anchor="middle"),
    ]


def gen_coreink(device_id: str, name: str,
                body_w: float, body_h: float) -> str:
    grad_case = f"case_{device_id}"
    out = [svg_header(name, body_w, body_h),
           DEFS_OPEN,
           shadow_filter(device_id),
           linear_gradient(grad_case, "#f7f7f5", "#e6e6e1"),
           DEFS_CLOSE]
    out.append(f'<path d="{coreink_body_path(body_w, body_h)}" '
               f'fill="url(#{grad_case})" fill-rule="evenodd" '
               'stroke="#bcbcb8" stroke-width="0.25" '
               f'filter="url(#shadow_{device_id})"/>\n')
    append_coreink_holes(out, device_id)
    append_coreink_tab(out)
    append_coreink_window(out, device_id)
    append_coreink_dial(out, device_id, body_w)
    append_coreink_debossed_m5(out, device_id)
    out.append(hotspots_block(coreink_hotspots(body_w)))
    out.append(caption_block(name, body_w, body_h,
                             coreink_key_names(body_w)))
    out.append(SVG_CLOSE)
    return "".join(out)


# ---------------------------------------------------------------------------
# Cardputer ADV (84 × 54)
# ---------------------------------------------------------------------------

# M5Stack Cardputer ADV front, photo-measured on the vendor front photo (84 mm
# across): the brand panel, the LCD module and the debossed M5 on a raised
# top plate with a tongue under the LCD, the StampS3A module on the right,
# and four white legend strips, each with its row of 14 black push buttons.
CARDPUTER_ORANGE = "#ff6633"
CARDPUTER_KEY_BLUE = "#3a6ea5"
CARDPUTER_KEY_GREEN = "#33c995"
CARDPUTER_KEY_GRAY = "#d9d9dc"
CARDPUTER_SHIFT_BLUE = "#2e6db0"
CARDPUTER_INK = "#111113"

# Keyboard legends, one row per strip: (primary legend, shifted legend
# printed in blue at the upper right, orange navigation arrow drawn behind
# the primary legend). The colored blocks and the esc / del / ok / space
# keys are drawn by their own functions.
CARDPUTER_KEYS: List[List[Tuple[str, str | None, str | None]]] = [
    [("esc", None, None), ("1", "!", None), ("2", "@", None),
     ("3", "#", None), ("4", "$", None), ("5", "%", None),
     ("6", "^", None), ("7", "&", None), ("8", "*", None),
     ("9", "(", None), ("0", ")", None), ("_", "-", None),
     ("=", "+", None), ("del", None, None)],
    [("tab", None, None), ("Q", None, None), ("W", None, None),
     ("E", None, None), ("R", None, None), ("T", None, None),
     ("Y", None, None), ("U", None, None), ("I", None, None),
     ("O", None, None), ("P", None, None), ("[", "{", None),
     ("]", "}", None), ("\\", "|", None)],
    [("fn", None, None), ("Aa", None, None), ("A", None, None),
     ("S", None, None), ("D", None, None), ("F", None, None),
     ("G", None, None), ("H", None, None), ("J", None, None),
     ("K", None, None), ("L", None, None), (";", ":", "up"),
     ("‘", "“", None), ("ok", None, None)],
    [("ctrl", None, None), ("opt", None, None), ("alt", None, None),
     ("Z", None, None), ("X", None, None), ("C", None, None),
     ("V", None, None), ("B", None, None), ("N", None, None),
     ("M", None, None), (",", "<", "left"), (".", ">", "down"),
     ("/", "?", "right"), ("space", None, None)],
]


@dataclass(frozen=True)
class CardputerRow:
    """One legend strip and the button row below it, in mm."""
    strip_top: float
    strip_bottom: float
    baseline: float
    legend_size: float
    shift_baseline: float
    button_cy: float


CARDPUTER_ROWS = (
    CardputerRow(21.55, 25.45, 24.31, 2.48, 23.23, 26.98),
    CardputerRow(28.95, 32.45, 31.62, 2.34, 30.68, 34.44),
    CardputerRow(36.25, 39.8, 38.94, 2.34, 38.04, 41.93),
    CardputerRow(43.9, 47.6, 46.74, 2.6, 45.58, 49.41),
)
CARDPUTER_STRIP_X0 = 1.3
CARDPUTER_STRIP_X1 = 82.55
CARDPUTER_BUTTON_W = 3.95
CARDPUTER_BUTTON_H = 2.42
CARDPUTER_BUTTON_PITCH = 5.773
CARDPUTER_LEGEND_PITCH = 5.74


@dataclass(frozen=True)
class CardputerBlock:
    """A colored legend block spanning its strip's height, in mm."""
    x0: float
    x1: float
    fill: str
    ink: str
    size: float
    stretch: float
    center_x: float
    baseline: float


CARDPUTER_BLOCKS = {
    (1, 0): CardputerBlock(2.37, 7.07, CARDPUTER_KEY_GRAY, CARDPUTER_INK,
                           1.79, 1.21, 4.74, 31.43),
    (2, 0): CardputerBlock(2.37, 7.02, CARDPUTER_ORANGE, "#ffffff",
                           1.91, 1.3, 4.75, 38.84),
    (2, 1): CardputerBlock(8.10, 12.85, CARDPUTER_KEY_BLUE, "#ffffff",
                           1.93, 1.13, 10.53, 38.84),
    (3, 0): CardputerBlock(2.17, 6.82, CARDPUTER_KEY_GRAY, CARDPUTER_INK,
                           2.07, 1.09, 4.5, 46.55),
    (3, 1): CardputerBlock(7.91, 12.65, CARDPUTER_KEY_GREEN, CARDPUTER_INK,
                           1.84, 1.18, 10.23, 46.25),
    (3, 2): CardputerBlock(13.64, 18.38, CARDPUTER_KEY_GRAY, CARDPUTER_INK,
                           2.07, 1.12, 16.0, 46.55),
}


def cardputer_button_cx(col: int) -> float:
    return 41.875 + (col - 6.5) * CARDPUTER_BUTTON_PITCH


def cardputer_legend_cx(col: int) -> float:
    return 42.0 + (col - 6.5) * CARDPUTER_LEGEND_PITCH


def cardputer_polygon(points: List[Tuple[float, float]], fill: str,
                      stroke: str = "none", stroke_w: float = 0.0) -> str:
    pts = " ".join(f"{f(x)},{f(y)}" for x, y in points)
    extra = (f' stroke="{stroke}" stroke-width="{f(stroke_w)}"'
             if stroke != "none" else "")
    return f'<polygon points="{pts}" fill="{fill}"{extra}/>\n'


def cardputer_rotated(angle: float, x: float, y: float, element: str) -> str:
    """Wrap ``element`` in a rotation about (x, y)."""
    return (f'<g transform="rotate({f(angle)} {f(x)} {f(y)})">\n'
            f'{element}</g>\n')


def cardputer_label_up(x: float, y: float, content: str, size: float,
                       fill: str, weight: str = "400",
                       length: float | None = None, anchor: str = "start",
                       stretch: float = 1.0) -> str:
    """Text reading bottom to top: baseline on x, starting at y.

    ``stretch`` scales the glyphs along the reading direction so that
    librsvg's Helvetica covers ``length`` like the printed face does.
    """
    return cardputer_rotated(-90, x, y, text(
        x, y, content, size=size, fill=fill, anchor=anchor, weight=weight,
        length=length, scale_x=stretch))


def append_cardputer_button(out: List[str], cx: float, cy: float) -> None:
    w, h = CARDPUTER_BUTTON_W, CARDPUTER_BUTTON_H
    x, y = cx - w / 2, cy - h / 2
    out.append(rounded_rect(x, y + 0.25, w, h, r=0.95,
                            fill="#050506", opacity=0.45))
    out.append(rounded_rect(x, y, w, h, r=0.95, fill="#171719",
                            stroke="#000000", stroke_w=0.13))
    out.append(rounded_rect(x + 0.45, y + 0.25, w - 0.9, 0.45, r=0.22,
                            fill="#4a4a4d", opacity=0.6))


def append_cardputer_arrow(out: List[str], kind: str, cx: float,
                           baseline: float) -> None:
    """Orange navigation arrow printed behind a legend."""
    shapes = {
        "up": [(cx, baseline - 1.22), (cx + 1.91, baseline + 0.69),
               (cx - 1.91, baseline + 0.69)],
        "down": [(cx - 1.91, baseline - 1.26), (cx + 1.91, baseline - 1.26),
                 (cx, baseline + 0.74)],
        "left": [(cx - 1.49, baseline - 0.79), (cx + 0.62, baseline - 1.89),
                 (cx + 0.62, baseline + 0.32)],
        "right": [(cx - 0.52, baseline - 1.89), (cx + 1.49, baseline - 0.79),
                  (cx - 0.52, baseline + 0.51)],
    }
    out.append(cardputer_polygon(shapes[kind], CARDPUTER_ORANGE))


def append_cardputer_esc(out: list[str], row: CardputerRow,
                         legend: str) -> None:
    # Orange flag with "esc"; the backtick and the blue tilde below it.
    out.append(cardputer_polygon(
        [(2.42, 21.66), (7.07, 21.66), (7.0, 22.78), (2.37, 23.58)],
        CARDPUTER_ORANGE))
    out.append(legend)
    out.append(text(4.25, 22.82, "esc", size=1.77, fill="#ffffff",
                    weight="700", length=3.13, scale_x=1.09))
    out.append(cardputer_polygon(
        [(4.06, 24.05), (4.6, 24.05), (5.36, 24.63), (4.82, 24.63)],
        CARDPUTER_INK))
    out.append(text(5.84, row.shift_baseline + 0.72, "~", size=1.9,
                    fill=CARDPUTER_SHIFT_BLUE, weight="700"))


def append_cardputer_del(out: list[str], row: CardputerRow,
                         legend: str) -> None:
    # Split block: orange over a diagonal, black under it, white arrow.
    top, bottom = row.strip_top, row.strip_bottom
    out.append(cardputer_polygon(
        [(76.98, top), (81.7, top), (81.7, 24.14), (76.98, 22.27)],
        CARDPUTER_ORANGE))
    out.append(cardputer_polygon(
        [(76.98, 22.27), (81.7, 24.14), (81.7, bottom), (76.98, bottom)],
        CARDPUTER_INK))
    out.append(legend)
    out.append(text(80.25, 22.92, "del", size=1.51, fill="#ffffff",
                    weight="700", length=2.17, scale_x=1.07))
    out.append(cardputer_polygon(
        [(77.38, 24.06), (78.35, 23.3), (78.35, 23.7), (79.55, 23.7),
         (79.55, 24.42), (78.35, 24.42), (78.35, 24.82)],
        "#ffffff"))


def append_cardputer_ok(out: list[str], row: CardputerRow,
                        legend: str) -> None:
    out.append(rounded_rect(76.98, row.strip_top, 4.67,
                            row.strip_bottom - row.strip_top, r=0.12,
                            fill=CARDPUTER_INK))
    out.append(legend)
    out.append(text(78.32, 37.65, "ok", size=1.24, fill="#ffffff",
                    weight="700", length=1.68, scale_x=1.2))
    # Return arrow: a stem down the right, a shaft and a head to the left.
    out.append(cardputer_polygon(
        [(78.47, 38.95), (79.3, 38.2), (79.3, 38.62), (80.18, 38.62),
         (80.18, 37.95), (80.74, 37.95), (80.74, 39.18), (79.3, 39.18),
         (79.3, 39.62)],
        "#ffffff"))


def append_cardputer_space(out: List[str]) -> None:
    out.append(
        f'<path d="M 77.78 46 V 47.02 H 81.06 V 46 H 80.52 V 46.5 '
        f'H 78.32 V 46 Z" fill="{CARDPUTER_INK}"/>\n'
    )


def cardputer_comma(cx: float, cy: float, scale: float = 1.0,
                    flip: bool = False) -> str:
    """A heavy comma: a round head with a tail curling down-left from
    (cx, cy); ``flip`` turns it into an opening quote (tail up-right)."""
    k = -scale if flip else scale
    head = circle(cx, cy, 0.34 * scale, fill=CARDPUTER_INK)
    tail = (f'<path d="M {f(cx + 0.34 * k)} {f(cy)} '
            f'Q {f(cx + 0.3 * k)} {f(cy + 0.8 * k)} '
            f'{f(cx - 0.3 * k)} {f(cy + 1.05 * k)} '
            f'L {f(cx - 0.36 * k)} {f(cy + 0.86 * k)} '
            f'Q {f(cx + 0.02 * k)} {f(cy + 0.6 * k)} {f(cx - 0.05 * k)} '
            f'{f(cy + 0.3 * k)} Z" fill="{CARDPUTER_INK}"/>\n')
    return head + tail


def append_cardputer_punctuation(out: List[str], label: str, cx: float,
                                 baseline: float) -> bool:
    """Draw the heavy punctuation legends as shapes (the printed marks are
    far bolder than any font's); False when ``label`` is not one."""
    if label == "_":
        out.append(rounded_rect(cx - 0.59, baseline - 0.14, 1.18, 0.26,
                                r=0.05, fill=CARDPUTER_INK))
    elif label == "=":
        for bar_top in (baseline - 1.34, baseline - 0.72):
            out.append(rounded_rect(cx - 0.5, bar_top, 1.15, 0.31,
                                    r=0.05, fill=CARDPUTER_INK))
    elif label == ".":
        out.append(circle(cx + 0.02, baseline - 0.12, 0.34,
                          fill=CARDPUTER_INK))
    elif label == ",":
        out.append(cardputer_comma(cx + 0.02, baseline - 0.54))
    elif label == ";":
        out.append(circle(cx, baseline - 1.32, 0.3, fill=CARDPUTER_INK))
        out.append(cardputer_comma(cx, baseline - 0.64, scale=0.8))
    elif label == "‘":
        out.append(cardputer_comma(cx + 0.05, baseline - 0.64, flip=True))
    else:
        return False
    return True


def append_cardputer_shift_mark(out: List[str], mark: str, cx: float,
                                shift_baseline: float) -> bool:
    """Draw the shifted legends a font sets too small or too high as
    shapes: the six-spoke asterisk, the heavy caret and the wide dash.
    False when ``mark`` is not one."""
    blue = CARDPUTER_SHIFT_BLUE
    if mark == "*":
        x = cx + 1.865
        y = shift_baseline - 0.51
        spokes = " ".join(
            f"M {f(x - dx)} {f(y - dy)} L {f(x + dx)} {f(y + dy)}"
            for dx, dy in ((0.0, 0.3), (0.26, 0.15), (0.26, -0.15)))
        out.append(f'<path d="{spokes}" fill="none" stroke="{blue}" '
                   'stroke-width="0.27" stroke-linecap="round"/>\n')
    elif mark == "^":
        x = cx + 1.76
        top = shift_baseline - 0.94
        foot = shift_baseline - 0.13
        out.append(cardputer_polygon(
            [(x - 0.42, foot), (x - 0.11, top), (x + 0.11, top),
             (x + 0.42, foot), (x + 0.19, foot), (x, foot - 0.5),
             (x - 0.19, foot)], blue))
    elif mark == "-":
        out.append(rounded_rect(cx + 1.37, shift_baseline - 0.65, 0.6, 0.2,
                                r=0.04, fill=blue))
    else:
        return False
    return True


def append_cardputer_legend(out: List[str], row: CardputerRow, col: int,
                            key: Tuple[str, str | None, str | None]) -> None:
    label, shifted, arrow = key
    cx = cardputer_legend_cx(col)
    if arrow:
        append_cardputer_arrow(out, arrow, cx, row.baseline)
    if not append_cardputer_punctuation(out, label, cx, row.baseline):
        out.append(text(cx, row.baseline, label, size=row.legend_size,
                        fill=CARDPUTER_INK, weight="700"))
    if shifted and append_cardputer_shift_mark(out, shifted, cx,
                                               row.shift_baseline):
        return
    if shifted == "“":
        out.append(text(cx + 1.65, row.shift_baseline + 1.0, shifted,
                        size=2.6, fill=CARDPUTER_SHIFT_BLUE, weight="700"))
    elif shifted:
        out.append(text(cx + 1.7, row.shift_baseline, shifted, size=1.65,
                        fill=CARDPUTER_SHIFT_BLUE, weight="700"))


def append_cardputer_keyboard(out: List[str]) -> None:
    custom = {(0, 0): "esc", (0, 13): "del", (2, 13): "ok", (3, 13): "space"}
    for r_idx, (row, keys) in enumerate(zip(CARDPUTER_ROWS, CARDPUTER_KEYS)):
        out.append(rounded_rect(CARDPUTER_STRIP_X0, row.strip_top - 0.1,
                                CARDPUTER_STRIP_X1 - CARDPUTER_STRIP_X0,
                                row.strip_bottom - row.strip_top + 0.2,
                                r=0.35, fill="#fbfbfc",
                                stroke="#b9b9bd", stroke_w=0.12))
        for c_idx, key in enumerate(keys):
            block = CARDPUTER_BLOCKS.get((r_idx, c_idx))
            special = custom.get((r_idx, c_idx))
            # What is printed for this key goes in its legend group; the
            # colored block under it is drawn before the group opens.
            legend = legend_open(key_slug(key[0]))
            if block:
                out.append(rounded_rect(block.x0, row.strip_top,
                                        block.x1 - block.x0,
                                        row.strip_bottom - row.strip_top,
                                        r=0.12, fill=block.fill))
                out.append(legend)
                out.append(text(block.center_x, block.baseline, key[0],
                                size=block.size, fill=block.ink,
                                weight="700", scale_x=block.stretch))
            elif special == "esc":
                append_cardputer_esc(out, row, legend)
            elif special == "del":
                append_cardputer_del(out, row, legend)
            elif special == "ok":
                append_cardputer_ok(out, row, legend)
            elif special == "space":
                out.append(legend)
                append_cardputer_space(out)
            else:
                out.append(legend)
                append_cardputer_legend(out, row, c_idx, key)
            out.append(LEGEND_CLOSE)
            append_cardputer_button(out, cardputer_button_cx(c_idx),
                                    row.button_cy)


def append_cardputer_plate(out: List[str], device_id: str) -> None:
    """Lower ledge between the top plate and the keyboard, and the raised
    tongue of the top plate under the LCD (45-degree side and front
    chamfers)."""
    out.append('<rect x="0.7" y="17.6" width="82.6" height="3.95" '
               'fill="#b4b4b8"/>\n')
    out.append('<rect x="17.35" y="17.6" width="34.1" height="3.35" '
               'fill="#c3c3c7"/>\n')
    out.append(cardputer_polygon(
        [(17.35, 17.6), (19.4, 19.65), (19.6, 20.95), (17.35, 20.95)],
        "#d3d3d6"))
    out.append(cardputer_polygon(
        [(51.45, 17.6), (49.55, 19.65), (49.5, 20.95), (51.45, 20.95)],
        "#a9a9ad"))
    out.append(cardputer_polygon(
        [(17.35, 17.6), (51.45, 17.6), (49.55, 19.65), (19.4, 19.65)],
        "#ededf0"))
    out.append(cardputer_polygon(
        [(19.4, 19.65), (49.55, 19.65), (49.5, 20.1), (19.6, 20.1)],
        f"url(#tongue_{device_id})"))
    out.append('<rect x="17.6" y="20.95" width="33.6" height="0.55" '
               'fill="#8a8a8e" opacity="0.55"/>\n')


def append_cardputer_brand_panel(out: List[str]) -> None:
    """CARDPUTER ADV panel: a light plate with a round notch over the left
    screw, cyan corner marks, the wordmark and a microphone icon."""
    out.append(
        '<path d="M 2.3 1.45 H 18.4 A 0.8 0.8 0 0 1 19.2 2.25 V 15.75 '
        'A 0.8 0.8 0 0 1 18.4 16.55 H 15.63 A 2.9 2.9 0 0 0 10.37 16.55 '
        'H 2.3 A 0.8 0.8 0 0 1 1.5 15.75 V 2.25 A 0.8 0.8 0 0 1 2.3 1.45 Z" '
        'fill="#fafafb" stroke="#bdbdc1" stroke-width="0.15"/>\n'
    )
    # What is printed on the plate: its ten marks, one group for the model.
    out.append(print_open("brand-panel", "panel"))
    for corner_x, corner_y, dx, dy in ((2.08, 2.47, 1, 1),
                                       (18.68, 2.47, -1, 1),
                                       (2.08, 11.86, 1, -1),
                                       (18.68, 11.86, -1, -1)):
        x = corner_x + 0.16 * dx
        y = corner_y + 0.16 * dy
        out.append(
            f'<path d="M {f(x)} {f(corner_y + 1.19 * dy)} V {f(y)} '
            f'H {f(corner_x + 1.08 * dx)}" fill="none" stroke="#14c8ee" '
            'stroke-width="0.32"/>\n'
        )
    out.append(text(10.375, 5.63, "CARDPUTER", size=2.01, fill="#1a1a1c",
                    weight="400", length=14.03, scale_x=1.14))
    # ADV, geometric bold capitals as outlines.
    out.append(
        '<path fill-rule="evenodd" fill="#1a1a1c" d="'
        'M 3.66 10.67 L 5.33 6.82 H 6.22 L 7.9 10.67 H 6.92 L 6.65 9.95 '
        'H 4.84 L 4.55 10.67 Z M 5.19 9.1 H 6.33 L 5.79 7.64 Z '
        'M 8.7 6.82 H 10.625 A 1.925 1.925 0 0 1 10.625 10.67 H 8.7 Z '
        'M 9.59 7.62 V 9.87 H 10.625 A 1.125 1.125 0 0 0 10.625 7.62 Z '
        'M 12.92 6.82 H 13.9 L 15.12 9.54 L 16.24 6.82 H 17.12 '
        'L 15.55 10.67 H 14.6 Z"/>\n'
    )
    # Microphone: orange capsule in a black cradle on a stand.
    out.append(rounded_rect(8.2, 12.35, 1.09, 2.37, r=0.545,
                            fill=CARDPUTER_ORANGE))
    out.append('<path d="M 7.62 14.13 A 1.075 1.075 0 0 0 9.77 14.13" '
               f'fill="none" stroke="{CARDPUTER_INK}" '
               'stroke-width="0.42"/>\n')
    out.append(f'<rect x="8.53" y="15.15" width="0.34" height="0.5" '
               f'fill="{CARDPUTER_INK}"/>\n')
    out.append(cardputer_polygon(
        [(8.0, 16.01), (9.4, 16.01), (8.92, 15.55), (8.48, 15.55)],
        CARDPUTER_INK))
    out.append(LEGEND_CLOSE)


def append_cardputer_debossed_m5(out: List[str], device_id: str) -> None:
    """The M5 debossed into the top plate: a recessed channel, shaded on
    its upper / left walls and lit on its lower / right walls."""
    m_glyph = ("M 47.65 7.98 V 2.7 H 48.4 L 50 4.45 L 51.57 2.7 H 52.2 "
               "V 7.98 H 51.42 V 4.34 L 50 5.95 L 48.45 4.25 V 7.98 Z")
    five_glyph = ("M 52.65 2.72 H 55.85 V 3.48 H 53.38 V 4.5 H 54.28 "
                  "A 1.72 1.72 0 0 1 54.28 7.94 H 52.65 V 7.22 H 54.28 "
                  "A 0.97 0.97 0 0 0 54.28 5.28 H 52.65 Z")
    shape = f"{m_glyph} {five_glyph}"
    clip_id = f"m5_deboss_{device_id}"
    out.append(f'{DEFS_OPEN}<clipPath id="{clip_id}"><path d="{shape}"/>'
               f'</clipPath>\n{DEFS_CLOSE}')
    out.append(f'<path d="{shape}" fill="none" stroke="#ffffff" '
               'stroke-width="0.14" transform="translate(0.05 0.05)"/>\n')
    out.append(f'<path d="{shape}" fill="#dadadd"/>\n')
    out.append(f'<g clip-path="url(#{clip_id})" fill="none" '
               'stroke-width="0.2">\n'
               f'<path d="{shape}" stroke="#9c9ca1" '
               'transform="translate(0.07 0.07)"/>\n'
               f'<path d="{shape}" stroke="#f7f7f8" '
               'transform="translate(-0.07 -0.07)"/>\n'
               '</g>\n')


def append_cardputer_screw(out: List[str], device_id: str,
                           cx: float, cy: float) -> None:
    """Socket-head screw in its counterbore."""
    out.append(circle(cx, cy, 2.0, fill="#2a2a2e"))
    out.append(circle(cx, cy, 1.6, fill=f"url(#screw_{device_id})",
                      stroke="#9a9a9e", stroke_w=0.08))
    hexagon = [(cx + 0.88 * dx, cy + 0.88 * dy)
               for dx, dy in ((0.0, 1.0), (-0.866, 0.5), (-0.866, -0.5),
                              (0.0, -1.0), (0.866, -0.5), (0.866, 0.5))]
    out.append(cardputer_polygon(hexagon, "#8e8e93", stroke="#3a3a3e",
                                 stroke_w=0.14))
    out.append(circle(cx, cy, 0.42, fill="#5e5e63", opacity=0.8))


def append_cardputer_usb_c(out: List[str]) -> None:
    """The StampS3A USB-C receptacle in its notch on the right edge."""
    out.append('<path d="M 81.9 4.85 H 84 V 15.1 H 81.9 Z" '
               'fill="#a5a5a9"/>\n')
    out.append(rounded_rect(81.3, 6.95, 2.4, 6.5, r=0.5, fill="#e9e9ec",
                            stroke="#8c8c90", stroke_w=0.12))
    for slot_y, slot_h in ((8.05, 1.3), (11.6, 1.35)):
        out.append(rounded_rect(81.45, slot_y, 1.2, slot_h, r=0.5,
                                fill="#1a1a1c"))


# The StampS3A's label, measured on M5Stack's front product photo of the
# Cardputer ADV (the image reference/front.png crops, 10.1 px/mm) and checked
# on its 1600 px three-quarter photo and on the loose "Pin Sticker" of the
# Cardputer Accessory Kit v1.1 (cdn.shopify.com/s/files/1/0056/7689/2250/files/
# 9_e979ae23-d47f-4037-9da6-5c3bc25e0362.webp, 4_b49dc0d0-3bbd-4373-9424-
# 594e06052cd0.webp and 1_1e50f491-80e1-4e4f-a47d-d1bd3f805838.webp; M5Stack's
# images, used as reference only). Each ink is the median of the photo's bright,
# saturated pixels on that print, scaled so that the photo's paper (#e7e9e8)
# is the model's (#fcfcfa); the comment beside each gives what it prints.
STAMP_LABEL = (58.30, 2.00, 81.30, 19.00)  # the label's paper, = the model's
STAMP_LABEL_CUT = 0.7  # its corners, chamfered like the module's
STAMP_PAPER = "#fcfcfa"  # the model's sticker material
STAMP_RED = "#e22c34"  # S3A, the R of RGB
# ESP32's thin strokes blur into the paper on the photo: their median is
# #b07e7e and their darkest cores #8a5b5b; the ink lies between, a duller
# red than S3A's.
STAMP_ROSE = "#a8585c"  # ESP32
STAMP_VERMILION = "#d2390c"  # the Espressif tile, 3V3, 5V, 11-3V3, 1-5V
STAMP_LIME = "#cbcb4a"  # GPIO 39 to 42, DOWNLOAD MODE
STAMP_GREEN = "#44c294"  # GPIO 11, 12, 14, 46, the G of RGB, 2-G18 to 4-G16
STAMP_YELLOW = "#f8cf1d"  # GPIO 13
STAMP_PALE_YELLOW = "#f6e08a"  # the SDA pill, the box round RGB
STAMP_MAGENTA = "#ee2f80"  # OTG/SERIAL, 5-BL-G38
STAMP_PURPLE = "#9a1a96"  # EN
STAMP_LILAC = "#f3a0ec"  # the RST pill
STAMP_SALMON = "#ea8f8d"  # LCD.PORT, the GPIO 0 pill
STAMP_PALE_PINK = "#f6cbc6"  # Ext.
STAMP_PERIWINKLE = "#78a3f2"  # GPIO 43, 44
STAMP_AZURE = "#2f97cc"  # S3FN8, the B of RGB, BACKSIDE
STAMP_M5_BLUE = "#2176ae"  # the M5 logotype, darker than S3FN8
STAMP_TEAL = "#06302d"  # the BTN pill
STAMP_GRAY = "#bcbcb9"  # GPIO 15, the leads, the dotted rules
STAMP_PALE_GRAY = "#dfdfdc"  # the GPIO and SCL pills
STAMP_CYAN = "#14c8ee"  # GPIO 1-10, as the brand panel's corners
STAMP_BLUE = CARDPUTER_SHIFT_BLUE  # the LCD port's 7-10 and 12
# The box round the R prints as a grey line, lighter than the black of the
# certification text beside it.
STAMP_DARK_GRAY = "#6f706e"
STAMP_WHITE = "#ffffff"


def stamp_dots(points: List[Tuple[float, float]], fill: str,
               pitch: float = 0.18, size: float = 0.06) -> List[str]:
    """A dotted rule along a polyline: squares ``size`` mm a side every
    ``pitch`` mm (a legend has no dash pattern; the model prints each dot)."""
    dots: List[str] = []
    carry = pitch / 2
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        s = carry
        while s <= length:
            t = s / length
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            dots.append(f'<rect x="{f(cx - size / 2)}" y="{f(cy - size / 2)}" '
                        f'width="{f(size)}" height="{f(size)}" fill="{fill}"/>\n')
            s += pitch
        carry = s - length
    return dots


def stamp_dashes(points: List[Tuple[float, float]], ink: str,
                 pitch: float = 0.39, dash: float = 0.2,
                 width: float = 0.08, lead: float = 0.3) -> List[str]:
    """A dashed rule along a polyline: dashes ``dash`` mm long and ``width``
    mm across every ``pitch`` mm, the first centered ``lead`` mm from the
    start (a legend has no dash pattern; the model prints each dash)."""
    dashes: List[str] = []
    s = lead
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        while s <= length:
            cx, cy = x0 + ux * s, y0 + uy * s
            ax, ay = cx - ux * dash / 2, cy - uy * dash / 2
            bx, by = cx + ux * dash / 2, cy + uy * dash / 2
            dashes.append(f'<path d="M {f(ax)} {f(ay)} L {f(bx)} {f(by)}" '
                          f'fill="none" stroke="{ink}" '
                          f'stroke-width="{f(width)}"/>\n')
            s += pitch
        s -= length
    return dashes


def stamp_number(cx: float, cy: float, number: str, size: float, ink: str,
                 stretch: float = 1.0) -> str:
    """A pin number centered on its disc at (cx, cy), reading bottom to
    top: Inter Bold's cap height (0.727 of the size) centered across."""
    return cardputer_label_up(cx + 0.3637 * size, cy, number, size=size,
                              fill=ink, weight="700", anchor="middle",
                              stretch=stretch)


def stamp_line(points: List[Tuple[float, float]], ink: str,
               width: float) -> str:
    """A stroked polyline, round at its joins."""
    d = " L ".join(f"{f(x)} {f(y)}" for x, y in points)
    return (f'<path d="M {d}" fill="none" stroke="{ink}" '
            f'stroke-width="{f(width)}" stroke-linejoin="round"/>\n')


def stamp_box(x0: float, y0: float, x1: float, y1: float, r: float,
              ink: str, width: float) -> str:
    """The outline of a rounded rectangle, stroked."""
    return (f'<path d="M {f(x0 + r)} {f(y0)} H {f(x1 - r)} '
            f'A {f(r)} {f(r)} 0 0 1 {f(x1)} {f(y0 + r)} V {f(y1 - r)} '
            f'A {f(r)} {f(r)} 0 0 1 {f(x1 - r)} {f(y1)} H {f(x0 + r)} '
            f'A {f(r)} {f(r)} 0 0 1 {f(x0)} {f(y1 - r)} V {f(y0 + r)} '
            f'A {f(r)} {f(r)} 0 0 1 {f(x0 + r)} {f(y0)} Z" fill="none" '
            f'stroke="{ink}" stroke-width="{f(width)}" '
            'stroke-linejoin="round"/>\n')


def stamp_arc(cx: float, cy: float, r: float, start_deg: float,
              end_deg: float, ink: str, width: float) -> str:
    """A circular arc about (cx, cy) from ``start_deg`` round to ``end_deg``
    the way the angle falls (on the page: counterclockwise), the long way
    when it turns through more than half a circle."""
    a0, a1 = math.radians(start_deg), math.radians(end_deg)
    turn = (start_deg - end_deg) % 360
    return (f'<path d="M {f(cx + r * math.cos(a0))} {f(cy + r * math.sin(a0))} '
            f'A {f(r)} {f(r)} 0 {1 if turn > 180 else 0} 0 '
            f'{f(cx + r * math.cos(a1))} {f(cy + r * math.sin(a1))}" '
            f'fill="none" stroke="{ink}" stroke-width="{f(width)}"/>\n')


def stamp_zero(cx: float, cy: float, length: float, width: float,
               stroke: float, ink: str) -> str:
    """The label's 0: one stroke shaped like a stadium, ``length`` by
    ``width`` mm over its outer edge, its long side along the label's up
    (the front's x)."""
    run, across = length - stroke, width - stroke
    return stamp_box(cx - run / 2, cy - across / 2, cx + run / 2,
                     cy + across / 2, across / 2, ink, stroke)


def stamp_m5(x: float, y: float, ink: str) -> str:
    """M5Stack's thin M5 logotype, reading bottom to top: its baseline on the
    front's x = ``x`` + 1.3, the M's left leg on y = ``y``. Strokes 0.22 mm,
    the M's V reaching 0.6 of the cap height, the 5 square-shouldered with a
    flat top and a rounded bowl."""
    top, base = x, x + 1.3
    left, right = y, y - 1.18
    bowl = x + 0.55  # the 5's bowl top
    s5l, s5r = y - 1.51, y - 2.33  # the 5's left stroke, its right side
    r = 0.3
    return (
        f'<path d="M {f(base)} {f(left)} L {f(top)} {f(left)} '
        f'L {f(top + 0.86)} {f((left + right) / 2)} L {f(top)} {f(right)} '
        f'L {f(base)} {f(right)}" '
        f'fill="none" stroke="{ink}" stroke-width="0.22" '
        'stroke-linejoin="bevel" stroke-linecap="butt"/>\n'
        f'<path d="M {f(top)} {f(s5r)} L {f(top)} {f(s5l)} L {f(bowl)} {f(s5l)} '
        f'L {f(bowl)} {f(s5r + r)} '
        f'A {f(r)} {f(r)} 0 0 1 {f(bowl + r)} {f(s5r)} '
        f'L {f(base - r)} {f(s5r)} '
        f'A {f(r)} {f(r)} 0 0 1 {f(base)} {f(s5r + r)} '
        f'L {f(base)} {f(s5l - 0.02)}" '
        f'fill="none" stroke="{ink}" stroke-width="0.22" '
        'stroke-linejoin="miter" stroke-linecap="butt"/>\n')


def stamp_upright(cx: float, cy: float, body: str) -> str:
    """Shapes drawn upright in the label's own frame around (cx, cy): the
    label reads from bottom to top, so its right is the front's up."""
    return cardputer_rotated(-90, cx, cy, body)


def stamp_pill(cx: float, y0: float, y1: float, w: float, fill: str) -> str:
    """A pill along the label's reading direction, ``w`` mm across."""
    return rounded_rect(cx - w / 2, y0, w, y1 - y0, r=w / 2, fill=fill)


def append_cardputer_stamp_marks(out: List[str]) -> None:
    """The label's certification marks: Japan's radio mark, the WEEE bin and
    its bar, FCC, CE, and the maker's name, each where the photo has it."""
    # Japan's technical-conformity mark, upright: a ring broken on its right
    # by a lightning stroke across its upper half, over a stem with two bars.
    gx, gy = 66.75, 13.67
    ring = 0.97
    start, end = math.radians(-18), math.radians(24)
    bolt = [(gx - 0.93, gy - 0.27), (gx - 0.03, gy - 0.44),
            (gx + 0.106, gy - 0.125),
            (gx + ring * math.cos(start), gy + ring * math.sin(start))]
    path = " L ".join(f"{f(px)} {f(py)}" for px, py in bolt)
    out.append(stamp_upright(gx, gy,
        f'<path d="M {path} A {f(ring)} {f(ring)} 0 1 0 '
        f'{f(gx + ring * math.cos(end))} {f(gy + ring * math.sin(end))}" '
        f'fill="none" stroke="{CARDPUTER_INK}" stroke-width="0.1" '
        'stroke-linejoin="round"/>\n'
        f'<path d="M {f(gx - 0.52)} {f(gy + 0.19)} H {f(gx + 0.56)} '
        f'M {f(gx - 0.52)} {f(gy + 0.425)} H {f(gx + 0.56)} '
        f'M {f(gx + 0.03)} {f(gy + 0.425)} V {f(gy + 0.77)}" fill="none" '
        f'stroke="{CARDPUTER_INK}" stroke-width="0.08"/>\n'))
    # WEEE: the crossed-out wheelie bin, upright in the label's frame.
    out.append(stamp_upright(69.25, 13.6,
        '<path d="M 68.6 12.75 H 69.9 M 68.7 12.9 L 68.85 14.2 H 69.65 '
        'L 69.8 12.9" fill="none" '
        f'stroke="{CARDPUTER_INK}" stroke-width="0.1" '
        'stroke-linejoin="round"/>\n'
        f'{rounded_rect(69.05, 12.57, 0.4, 0.18, r=0.0, fill=CARDPUTER_INK)}'
        f'{circle(68.97, 14.35, 0.12, fill=CARDPUTER_INK)}'
        f'{circle(69.53, 14.35, 0.12, fill=CARDPUTER_INK)}'
        '<path d="M 67.95 12.25 L 70.55 14.95 M 70.55 12.25 L 67.95 14.95" '
        f'fill="none" stroke="{CARDPUTER_INK}" stroke-width="0.1"/>\n'))
    # The bin's bar, 0.4 mm clear of the F beside it.
    out.append(rounded_rect(71.15, 12.5, 0.5, 2.2, r=0.0, fill=CARDPUTER_INK))
    # The maker, three lines beside the bar, in the certification text's
    # black.
    for x, y, word, length in ((72.42, 14.92, "M5Stack", 2.2),
                               (72.93, 15.12, "Technology", 2.68),
                               (73.42, 14.82, "Co., Ltd", 2.0)):
        out.append(cardputer_label_up(x, y, word, size=0.48,
                                      fill=CARDPUTER_INK, length=length))
    # FCC, read upright: the F's stem along the bottom of the mark, its two
    # arms rising from it, then the outer C round the inner one, each open
    # toward the label's right (the front's up).
    out.append(stamp_line([(71.14, 11.925), (73.22, 11.925)],
                          CARDPUTER_INK, 0.33))
    out.append(stamp_line([(71.33, 11.05), (71.33, 11.8)], CARDPUTER_INK,
                          0.38))
    out.append(stamp_line([(72.1, 11.2), (72.1, 11.8)], CARDPUTER_INK, 0.33))
    out.append(stamp_arc(72.2, 10.0, 0.85, 241.93, 298.07, CARDPUTER_INK, 0.3))
    out.append(stamp_arc(72.2, 10.05, 0.52, 239.97, 300.03, CARDPUTER_INK,
                         0.15))
    # CE: the C and the E each a little over half a circle of one radius,
    # the E's middle bar shorter than its arc is deep, the E clear of the C.
    out.append(stamp_arc(72.2, 8.05, 0.85, 186.75, 353.25, CARDPUTER_INK, 0.3))
    out.append(stamp_arc(72.2, 6.25, 0.83, 190.41, 349.59, CARDPUTER_INK,
                         0.28))
    out.append(stamp_line([(72.2, 6.32), (72.2, 7.0)], CARDPUTER_INK, 0.22))


def append_cardputer_stamp_pins(out: List[str]) -> None:
    """Pin legend of the StampS3A label, rotated like the module. Every pin
    disc is one size, 1.42 mm across (the photo's discs measure 1.38 to
    1.48 mm), each where the photo centers it. The printed numbers are a
    taller, narrower face than Inter Bold: their cap height is 0.72 to
    0.87 mm, so they take a larger size squeezed along the line (two
    digits to about 0.82 of their width)."""
    disc = 0.71
    pair = 0.82  # two digits' squeeze
    # GPIO 1-10: two staggered rows of cyan dots along the bottom edge, each
    # even one on its faint lead, under the hairline bracket round GPIO+ADC.
    odd = (59.68, 62.22, 64.75, 67.32, 69.89)
    even = (60.94, 63.47, 66.01, 68.59, 71.0)
    for x in even:
        out.append(rounded_rect(x - 0.27, 16.88, 0.54, 1.82, r=0.27,
                                fill=STAMP_PALE_GRAY))
    for k in range(5):
        for number, x, y in ((2 * k + 1, odd[k], 18.1),
                             (2 * k + 2, even[k], 16.88)):
            out.append(circle(x, y, disc, fill=STAMP_CYAN))
            out.append(stamp_number(x, y, str(number), 1.18, CARDPUTER_INK,
                                    0.84 if number == 10 else 0.95))
    out.append(stamp_line([(59.42, 16.6), (59.44, 16.05), (59.65, 15.85),
                           (63.45, 15.85)], STAMP_GRAY, 0.05))
    out.append(stamp_line([(69.85, 15.85), (70.75, 15.85), (71.1, 16.05)],
                          STAMP_GRAY, 0.05))
    out.append(cardputer_rotated(180, 66.65, 15.45, text(
        66.65, 15.45, "GPIO+ADC", size=0.67, fill=CARDPUTER_INK,
        weight="700", length=5.3, scale_x=1.52)))
    # Top edge: the RST and GPIO 0 pills hang from their dots, as wide as
    # the photo prints them.
    out.append(stamp_pill(75.01, 2.85, 5.55, 1.04, STAMP_LILAC))
    out.append(stamp_pill(77.57, 2.82, 5.95, 1.0, STAMP_SALMON))
    for number, x, y, fill, ink in (
            ("43", 69.88, 2.82, STAMP_PERIWINKLE, STAMP_WHITE),
            ("44", 72.44, 2.82, STAMP_PERIWINKLE, STAMP_WHITE),
            ("EN", 75.01, 2.85, STAMP_PURPLE, STAMP_WHITE),
            ("39", 79.05, 2.86, STAMP_LIME, CARDPUTER_INK),
            ("42", 71.15, 4.72, STAMP_LIME, CARDPUTER_INK),
            ("41", 73.72, 5.02, STAMP_LIME, CARDPUTER_INK),
            ("40", 76.3, 5.02, STAMP_LIME, CARDPUTER_INK),
            ("46", 68.61, 4.24, STAMP_GREEN, CARDPUTER_INK)):
        out.append(circle(x, y, disc, fill=fill))
        if number == "EN":
            out.append(stamp_number(x, y, number, 0.97, ink, 0.72))
        else:
            out.append(stamp_number(x, y, number, 1.0, ink, pair))
    out.append(circle(77.57, 2.82, disc, fill=CARDPUTER_ORANGE))
    out.append(stamp_zero(77.54, 2.8, 0.86, 0.52, 0.09, STAMP_WHITE))
    # Pin names beside their dots, each centered on its dot along the label's
    # up (the front's x).
    for x, y, word, size, length, anchor, stretch in (
            (68.84, 3.42, "GP", 0.58, 0.95, "start", 1.0),
            (69.77, 4.0, "U0", 0.45, None, "middle", 1.0),
            (70.21, 4.0, "TX", 0.45, None, "middle", 1.0),
            (71.33, 3.84, "MMS", 0.5, None, "start", 1.0),
            (72.68, 5.52, "U0Rx", 0.55, 1.82, "start", 1.0),
            (73.9, 4.16, "MDI", 0.5, None, "start", 1.3),
            (75.22, 4.62, "RST", 0.58, None, "middle", 1.0),
            (76.48, 4.14, "MDO", 0.5, None, "start", 1.3),
            (77.77, 4.645, "GPIO", 0.55, None, "middle", 1.215)):
        # the M's notches stay open at the Bold's own width or wider: no
        # length on them, a stretch at most
        out.append(cardputer_label_up(x, y, word, size=size,
                                      fill=CARDPUTER_INK, weight="700",
                                      length=length, anchor=anchor,
                                      stretch=stretch))
    out.append(cardputer_label_up(78.92, 5.47, "G21", size=0.8,
                                  fill=CARDPUTER_INK, length=1.32))
    # RGB on its filled pale-yellow box, STATUS under it.
    out.append(rounded_rect(79.03, 3.87, 0.7, 2.06, r=0.2,
                            fill=STAMP_PALE_YELLOW))
    for letter, ink, y in (("R", STAMP_RED, 5.36), ("G", STAMP_GREEN, 4.82),
                           ("B", STAMP_AZURE, 4.27)):
        out.append(cardputer_label_up(79.5, y, letter, size=0.55, fill=ink,
                                      weight="700", anchor="middle"))
    out.append(cardputer_label_up(80.03, 5.74, "STATUS", size=0.38,
                                  fill=CARDPUTER_INK, weight="700",
                                  length=1.96))
    # The top GND pin: a black pill with white letters; its lead drops from
    # the label's top edge beside 39, then kinks right onto the pill's top.
    out.append(stamp_line([(80.09, 2.12), (80.09, 2.86), (80.5, 3.62)],
                          CARDPUTER_INK, 0.06))
    out.append(stamp_pill(80.76, 3.55, 5.47, 0.96, CARDPUTER_INK))
    out.append(cardputer_label_up(81.1, 4.45, "GND", size=0.93,
                                  fill=STAMP_WHITE, weight="700",
                                  anchor="middle", stretch=0.83))
    # Bottom edge, right half: power and I2C pins, each GPIO name on a pale
    # pill joined to its dot.
    out.append(stamp_pill(72.415, 16.24, 18.8, 1.27, CARDPUTER_INK))
    out.append(cardputer_label_up(72.8, 17.54, "GND", size=1.07,
                                  fill=STAMP_WHITE, weight="700",
                                  anchor="middle", stretch=0.77))
    out.append(stamp_pill(74.96, 16.22, 18.8, 1.28, STAMP_VERMILION))
    out.append(cardputer_label_up(75.34, 17.54, "5V", size=1.05,
                                  fill=STAMP_WHITE, weight="700",
                                  anchor="middle", stretch=0.77))
    for number, x, y in (("11", 73.71, 15.82), ("12", 76.26, 15.82),
                         ("14", 78.79, 15.82)):
        out.append(stamp_pill(x, y, 18.4, 0.84, STAMP_PALE_GRAY))
        out.append(circle(x, y, disc, fill=STAMP_GREEN))
        out.append(stamp_number(x, y, number, 1.0, CARDPUTER_INK,
                                1.0 if number == "11" else pair))
        out.append(cardputer_label_up(x + 0.22, 17.49, "GPIO", size=0.6,
                                      fill=CARDPUTER_INK, weight="700",
                                      length=1.85, anchor="middle"))
    out.append(stamp_pill(77.48, 14.95, 18.06, 1.0, STAMP_PALE_YELLOW))
    out.append(cardputer_label_up(77.7, 16.36, "SDA", size=0.6,
                                  fill=CARDPUTER_INK, weight="700",
                                  length=1.53, anchor="middle"))
    out.append(circle(77.48, 18.06, disc, fill=STAMP_YELLOW))
    out.append(stamp_number(77.48, 18.13, "13", 1.0, CARDPUTER_INK, 0.94))
    out.append(stamp_pill(80.06, 15.1, 18.06, 0.84, STAMP_PALE_GRAY))
    out.append(cardputer_label_up(80.31, 16.43, "SCL", size=0.6,
                                  fill=CARDPUTER_INK, weight="700",
                                  length=1.45, anchor="middle"))
    out.append(circle(80.06, 18.06, disc, fill=STAMP_GRAY))
    out.append(stamp_number(80.06, 18.13, "15", 1.0, CARDPUTER_INK, 0.9))


def append_cardputer_stamp(out: List[str]) -> None:
    """StampS3A module: a black frame around its printed label. The label
    is rotated a quarter turn: its text reads from bottom to top. Its paper
    is the model's ``stamp_label`` solid; everything printed on it is one
    legend group on the plane ``stamp``."""
    x0, y0, x1, y1, cut = 57.43, 1.28, 81.95, 19.68, 1.0
    out.append(
        f'<path d="M {f(x0 + cut)} {f(y0)} H {f(x1 - cut)} '
        f'L {f(x1)} {f(y0 + cut)} V {f(y1 - cut)} L {f(x1 - cut)} {f(y1)} '
        f'H {f(x0 + cut)} L {f(x0)} {f(y1 - cut)} V {f(y0 + cut)} Z" '
        'fill="#111114"/>\n'
    )
    lx0, ly0, lx1, ly1 = STAMP_LABEL
    c = STAMP_LABEL_CUT
    out.append(
        f'<path d="M {f(lx0 + c)} {f(ly0)} H {f(lx1 - c)} '
        f'L {f(lx1)} {f(ly0 + c)} V {f(ly1 - c)} L {f(lx1 - c)} {f(ly1)} '
        f'H {f(lx0 + c)} L {f(lx0)} {f(ly1 - c)} V {f(ly0 + c)} Z" '
        f'fill="{STAMP_PAPER}"/>\n'
    )
    out.append(print_open("stamp-label", "stamp"))
    # Name block in its dotted frame: STAMP S3A, ESP32 / S3FN8, 3D-ANT, the
    # Espressif mark.
    out.extend(stamp_dots([(58.95, 15.35), (58.95, 2.85), (59.35, 2.45),
                           (63.35, 2.45), (63.75, 2.85), (63.75, 14.95),
                           (63.35, 15.35), (58.95, 15.35)], STAMP_GRAY))
    out.append(cardputer_label_up(60.68, 15.12, "STAMP", size=2.14,
                                  fill=CARDPUTER_INK, length=6.84,
                                  stretch=0.98))
    out.append(cardputer_label_up(61.57, 8.32, "S3A", size=3.08,
                                  fill=STAMP_RED, weight="700", length=5.79,
                                  stretch=0.93))
    out.append(cardputer_label_up(61.96, 12.25, "ESP32", size=1.22,
                                  fill=STAMP_ROSE, length=3.46, stretch=0.95))
    out.append(cardputer_label_up(63.54, 12.29, "S3FN8", size=1.86,
                                  fill=STAMP_AZURE, weight="700", length=3.26,
                                  stretch=0.58))
    out.append(cardputer_label_up(63.35, 8.27, "3D-ANT", size=1.79,
                                  fill=CARDPUTER_INK, length=5.54,
                                  stretch=0.83))
    # Espressif's mark on its tile, upright: a white disc cut by four
    # vermilion arcs about a point low on its left, the innermost leaving a
    # white dot there.
    out.append(rounded_rect(60.97, 12.57, 2.47, 2.39, r=0.35,
                            fill=STAMP_VERMILION))
    ex, ey, er = 62.2, 13.77, 0.82
    ax, ay = ex - 0.45, ey + 0.45
    arcs = []
    for radius in (0.32, 0.6, 0.88, 1.16):
        # where the circle of this radius about (ax, ay) crosses the disc's
        # edge, its arc running inside the disc
        d = math.hypot(ex - ax, ey - ay)
        along = (radius ** 2 - er ** 2 + d ** 2) / (2 * d)
        across = math.sqrt(radius ** 2 - along ** 2)
        ux, uy = (ex - ax) / d, (ey - ay) / d
        mx, my = ax + ux * along, ay + uy * along
        tp = math.degrees(math.atan2(my + ux * across - ay,
                                     mx - uy * across - ax))
        tq = math.degrees(math.atan2(my - ux * across - ay,
                                     mx + uy * across - ax))
        tu = math.degrees(math.atan2(uy, ux))
        # the arc that runs through the disc's side of (ax, ay)
        if (tp - tu) % 360 > (tp - tq) % 360:
            tp, tq = tq, tp
        arcs.append(stamp_arc(ax, ay, radius, tp, tq, STAMP_VERMILION, 0.085))
    out.append(stamp_upright(ex, ey,
        f'{circle(ex, ey, er, fill=STAMP_WHITE)}{"".join(arcs)}'))
    # Certification block, M5 STACK, the boot button, USB.
    printed = (
        (64.75, 15.06, "Model Name: M5Cardputer", 0.62, CARDPUTER_INK,
         "700", 8.6, 1.1),
        (65.42, 15.06, "FCC ID:2AN3WM5CARDPUTER", 0.62, CARDPUTER_INK,
         "700", 9.78, 1.07),
        (67.1, 10.63, "219-249271", 0.98, CARDPUTER_INK, "400", 5.18, 1.04),
        (66.51, 4.87, "STACK", 0.68, CARDPUTER_INK, "700", 2.47, 1.1),
        (75.3, 14.9, "USB", 2.13, CARDPUTER_INK, "700", 4.74, 1.12),
        (74.85, 9.6, "D-:G19", 1.1, CARDPUTER_INK, "400", 3.3, 1.0),
        (75.85, 9.6, "D+:G20", 1.1, CARDPUTER_INK, "400", 3.35, 0.96),
    )
    out.append('<path d="M 66.2 11.14 H 67.31 V 12.32 H 66.2 Z" fill="none" '
               f'stroke="{STAMP_DARK_GRAY}" stroke-width="0.13"/>\n')
    out.append(cardputer_label_up(67.04, 11.73, "R", size=0.8,
                                  fill=CARDPUTER_INK, anchor="middle"))
    out.append(stamp_m5(64.33, 4.69, STAMP_M5_BLUE))
    append_cardputer_stamp_marks(out)
    out.append(rounded_rect(66.65, 2.19, 1.25, 2.39, r=0.62,
                            fill=STAMP_VERMILION))
    out.append(cardputer_label_up(67.645, 3.26, "3V3", size=1.07,
                                  fill=STAMP_WHITE, weight="700",
                                  anchor="middle", stretch=0.78))
    out.append(rounded_rect(67.8, 4.94, 2.76, 6.92, r=1.38,
                            fill=STAMP_TEAL))
    out.append(circle(69.225, 6.22, 0.935, fill=CARDPUTER_ORANGE))
    out.append(stamp_zero(69.1, 6.2, 1.4, 0.77, 0.14, STAMP_WHITE))
    out.append(cardputer_label_up(69.18, 11.0, "BTN", size=1.35,
                                  fill=STAMP_WHITE, weight="700", length=3.36,
                                  stretch=1.35))
    out.append(cardputer_label_up(69.74, 11.04, "DOWNLOAD", size=0.43,
                                  fill=STAMP_LIME, weight="700", length=3.32,
                                  stretch=1.35))
    out.append(cardputer_label_up(70.22, 10.17, "MODE", size=0.43,
                                  fill=STAMP_LIME, weight="700", length=1.54,
                                  stretch=1.2))
    for x, y, word, size, ink, weight, length, stretch in printed:
        out.append(cardputer_label_up(x, y, word, size=size, fill=ink,
                                      weight=weight, length=length,
                                      stretch=stretch))
    out.append(stamp_pill(76.0, 9.88, 14.92, 1.0, STAMP_MAGENTA))
    out.append(cardputer_label_up(76.28, 14.6, "OTG/SERIAL", size=0.76,
                                  fill=STAMP_WHITE, weight="700", length=4.4,
                                  stretch=1.0))
    # LCD port pin list, printed upside down beside the USB-C, in a frame
    # of black dashes whose side stops where the OTG/SERIAL pill begins, the back
    # side's pins named along it; the bar's Ext. end is paler than its
    # LCD.PORT end.
    out.extend(stamp_dashes([(81.2, 6.18), (76.07, 6.18), (76.07, 9.6)],
                            CARDPUTER_INK, lead=0.0))
    out.extend(stamp_dashes([(76.7, 14.82), (81.25, 14.82)], CARDPUTER_INK,
                            width=0.07, lead=0.14))
    out.append(rounded_rect(80.2, 6.35, 1.05, 8.45, r=0.1, fill=STAMP_SALMON))
    out.append(rounded_rect(80.2, 12.15, 1.05, 2.65, r=0.1,
                            fill=STAMP_PALE_PINK))
    out.append(cardputer_label_up(80.98, 11.23, "LCD.PORT", size=0.66,
                                  fill=CARDPUTER_INK, weight="700",
                                  length=3.83, stretch=1.11))
    out.append(cardputer_label_up(80.98, 14.17, "Ext.", size=0.66,
                                  fill=CARDPUTER_INK, weight="700",
                                  stretch=1.16))
    pin_lines = (("12-G37/CS", STAMP_BLUE), ("11-3V3", STAMP_VERMILION),
                 ("10-G36/SCK", STAMP_BLUE), ("9-G35/DAT", STAMP_BLUE),
                 ("8-G34/RS", STAMP_BLUE), ("7-G33/RST", STAMP_BLUE),
                 ("6-GND", CARDPUTER_INK), ("5-BL-G38", STAMP_MAGENTA),
                 ("4-G16", STAMP_GREEN), ("3-G17", STAMP_GREEN),
                 ("2-G18", STAMP_GREEN), ("1-5V", STAMP_VERMILION))
    # each row's ink centroid on the photo, rows 12 to 1; the baseline of a
    # row printed upside down sits 0.22 mm above its centroid
    rows = (6.75, 7.45, 8.16, 8.98, 9.77, 10.61, 11.27, 11.89, 12.50, 13.14,
            13.77, 14.39)
    for (line, ink), row in zip(pin_lines, rows):
        y = row - 0.22
        out.append(cardputer_rotated(180, 80.05, y, text(
            80.05, y, line, size=0.62, fill=ink, anchor="start",
            weight="700", scale_x=0.98)))
    # BACKSIDE rises to the label's right, from above 1-5V toward the end of
    # the OTG/SERIAL pill: on the front it runs up and to the left.
    out.append(cardputer_rotated(-120, 78.3, 14.6, text(
        78.3, 14.6, "BACKSIDE", size=0.55, fill=STAMP_M5_BLUE,
        anchor="start", weight="500", length=2.95)))
    append_cardputer_stamp_pins(out)
    out.append(LEGEND_CLOSE)


# A key's id has to survive as an id: the printed legend goes in
# ``data-label`` and the id carries this slug instead, so ``hs-key-slash``
# is addressable where ``hs-key-/`` would not be.
KEY_SLUGS = {
    "_": "underscore", "=": "equal", "[": "lbracket", "]": "rbracket",
    "\\": "backslash", ";": "semicolon", "\u2018": "quote",
    ",": "comma", ".": "period", "/": "slash", "$": "dollar",
}


def key_slug(label: str) -> str:
    """The id suffix for a keycap printed with *label*."""
    return KEY_SLUGS.get(label, label)


def cardputer_hotspots() -> List[Hotspot]:
    """One target per key, on the button the strip's legend belongs to.

    The legend is printed on the strip above its key; what moves is the
    black button under it, which is what a press has to land on.
    """
    return [
        Hotspot(f"key-{key_slug(key[0])}", cardputer_button_cx(col),
                row.button_cy, CARDPUTER_BUTTON_W, CARDPUTER_BUTTON_H,
                label=key[0])
        for row, keys in zip(CARDPUTER_ROWS, CARDPUTER_KEYS)
        for col, key in enumerate(keys)
    ]


def gen_cardputer(device_id: str, name: str,
                  body_w: float = 84.0, body_h: float = 54.0) -> str:
    grad_case = f"case_{device_id}"
    grad_screen = f"screen_{device_id}"
    out = [svg_header(name, body_w, body_h),
           DEFS_OPEN,
           shadow_filter(device_id),
           linear_gradient(grad_case, "#f4f4f6", "#e2e2e6"),
           linear_gradient(f"tongue_{device_id}", "#ededf0", "#c3c3c7"),
           screen_gradient(grad_screen),
           f'<linearGradient id="recess_{device_id}" x1="0" y1="0" '
           'x2="1" y2="1">\n<stop offset="0%" stop-color="#9a9a9e"/>\n'
           '<stop offset="100%" stop-color="#f4f4f6"/>\n</linearGradient>\n',
           f'<radialGradient id="screw_{device_id}" cx="40%" cy="35%" '
           'r="70%">\n<stop offset="0%" stop-color="#ffffff"/>\n'
           '<stop offset="100%" stop-color="#c4c4c8"/>\n</radialGradient>\n',
           DEFS_CLOSE]
    out.append(rounded_rect(0, 0, body_w, body_h, r=4.0,
                            fill=f"url(#{grad_case})",
                            stroke="#9d9da0", stroke_w=0.25,
                            filter_id=f"shadow_{device_id}"))
    append_cardputer_plate(out, device_id)
    # LCD module, photo-measured: the black glass is exactly the 24.91 x
    # 14.86 mm active area (240 x 135 px) at x 20.75 / y 2.95, in a recess
    # shaded on its top and left walls. Everything inside it, the
    # Aa/fn/ctrl/opt/alt modifier column included, is the vendor demo UI.
    lcd_w = 24.91
    lcd_h = 14.86
    lcd_x = 20.75
    lcd_y = 2.95
    out.append(rounded_rect(lcd_x - 0.63, lcd_y - 0.65,
                            lcd_w + 0.72, lcd_h + 0.77, r=0.6,
                            fill=f"url(#recess_{device_id})"))
    out.append(rounded_rect(lcd_x - 0.06, lcd_y - 0.06,
                            lcd_w + 0.12, lcd_h + 0.12, r=0.25,
                            fill="#050507"))
    out.append(rounded_rect(lcd_x, lcd_y, lcd_w, lcd_h, r=0.2,
                            fill=f"url(#{grad_screen})"))
    append_screen(out, ScreenRect(lcd_x, lcd_y, lcd_w, lcd_h, "240x135"))
    append_cardputer_brand_panel(out)
    # Two black slots under the microphone icon.
    for slot_x in (7.81, 8.99):
        out.append(rounded_rect(slot_x, 17.2, 0.6, 2.07, r=0.3,
                                fill=CARDPUTER_INK))
    append_cardputer_debossed_m5(out, device_id)
    append_cardputer_usb_c(out)
    append_cardputer_stamp(out)
    for screw_x, screw_y in ((13.0, 17.77), (54.47, 17.75)):
        append_cardputer_screw(out, device_id, screw_x, screw_y)
    append_cardputer_keyboard(out)
    out.append(hotspots_block(cardputer_hotspots()))
    out.append(caption_block(name, body_w, body_h))
    out.append(SVG_CLOSE)
    return "".join(out)

# ---------------------------------------------------------------------------
# T-Deck Plus
# ---------------------------------------------------------------------------
# Every T-Deck Plus value is in mm in the case frame: x from the case's left
# edge, y down from its top edge. The outline and the side rails come from
# LILYGO's T-Deck Plus shell STEP. Everything on the face is measured on two
# vendor front photos (the shop front photo and LILYGO's 3000 px pinmap photo),
# each registered onto that STEP outline through a homography fitted on the
# photo's silhouette (0.08 mm rms); the two photos agree within 0.05 mm.

# STEP shell outline without the side rails, clockwise from the top edge.
TDECK_PLUS_BODY: List[Tuple[float, float]] = [
    (12.82, 0), (60.37, 0), (62.12, 0.15), (63.72, 0.5), (64.69, 0.83),
    (65.67, 1.26), (66.48, 1.69), (67.37, 2.26), (68.24, 2.94), (68.92, 3.55),
    (70.02, 4.8), (70.54, 5.53), (71.02, 6.31), (71.44, 7.13), (71.81, 8.01),
    (72.24, 9.39), (72.5, 10.78), (72.6, 12.12), (72.6, 99.18),
    (72.44, 101.01), (72.08, 102.71), (71.54, 104.27), (70.91, 105.54),
    (70.08, 106.81), (69.15, 107.93), (67.94, 109.06), (66.48, 110.15),
    (64.9, 111.08), (62.92, 111.99), (61.09, 112.66), (58.52, 113.39),
    (56.55, 113.82), (54.37, 114.19), (50.7, 114.62), (48.04, 114.82),
    (44.87, 114.95), (42.98, 114.95), (41.97, 114.98), (37.78, 114.98),
    (35.28, 114.95), (28.96, 114.61), (23.9, 114.22), (20.59, 113.84),
    (17.71, 113.36), (14.99, 112.79), (12.28, 112.04), (10.31, 111.36),
    (9.07, 110.85), (7.95, 110.32), (6.92, 109.76), (6.02, 109.2),
    (4.71, 108.21), (4.08, 107.65), (3.49, 107.03), (2.92, 106.35),
    (2.45, 105.68), (2.02, 104.95), (1.65, 104.18), (1.32, 103.35),
    (1.11, 102.62), (0.8, 101.07), (0.65, 99.12), (0.65, 12.18),
    (0.75, 10.83), (0.94, 9.76), (1.24, 8.61), (1.66, 7.48), (2.08, 6.6),
    (2.75, 5.48), (3.28, 4.75), (4.15, 3.72), (4.66, 3.24), (5.4, 2.63),
    (6.43, 1.9), (7.25, 1.43), (8.56, 0.84), (9.53, 0.5), (10.45, 0.27),
    (11.48, 0.1),
]
# Body sides (STEP) and the side rails standing proud of them: the rails span
# the full case width, from x 0 to the case width, between the chamfered ends
# at these y values. The ends are the registered front photos' (same on both
# sides): each rail starts 0.45 mm higher than in the STEP, and its lower
# chamfer is the STEP's.
TDECK_PLUS_BODY_SIDES = (0.65, 72.6)
TDECK_PLUS_RAIL_X = 0.0
TDECK_PLUS_RAIL_ENDS = (12.95, 13.4, 62.4, 62.85)
# Glass bottom edge = top edge of the keyboard plate (photo: the black glass
# gives way to the plate at y 62.1-62.2 in both photos).
TDECK_PLUS_GLASS_BOTTOM = 62.15
# Viewing window: the panel aperture in the glass, the rectangle that is lit
# in both photos. Its edge is the dark hairline between the bezel and the lit
# picture, at x 7.06-66.20 and y 15.78-60.23; the steepest brightness step
# sits 0.2 mm inside it and gives the same center, 36.63, 38.00.
TDECK_PLUS_WINDOW = (7.06, 15.78, 59.14, 44.44)
# Active area 57.6 x 43.2 mm (ST7789 2.8", 0.18 mm pixel pitch, datasheet),
# centered in the viewing window. The window is 2.6 % larger on both axes, the
# usual margin between a panel's viewing area and its active area.
TDECK_PLUS_SCREEN = ScreenRect(7.83, 16.40, 57.6, 43.2, "320x240")
# Keyboard plate print (photo): the black band behind the trackball and the
# clear window around the keys, inside the plate's bright edge.
TDECK_PLUS_PRINT_X = (3.95, 69.2)
# The plate's offset from the body's center line (photo).
TDECK_PLUS_PLATE_DX = -0.1
TDECK_PLUS_BAND_BOTTOM = 73.75
# The window narrows to a tab under the bottom key row, between the two dark
# corners that carry the printed circle marks.
TDECK_PLUS_TAB = (11.05, 62.55, 98.9, 105.45)
# Trackball center and the axis the band print mirrors about (photo: both
# sit 1.4 mm right of the case center).
TDECK_PLUS_TRACKBALL = (37.97, 67.85)
# The ball itself, inside its bezel and rings: what a fingertip rolls and
# clicks (measurements.json, photo radial profile).
TDECK_PLUS_BALL_D = 4.96
TDECK_PLUS_BAND_AXIS = 37.98
# Keycaps (photo): column pitch 6.40 from the first column's left edge, key
# 5.47 x 6.71 including the dark rim, rows 7.85 apart.
TDECK_PLUS_KEY_X0 = 5.27
TDECK_PLUS_KEY_PITCH = 6.40
TDECK_PLUS_KEY_W = 5.47
TDECK_PLUS_KEY_H = 6.71
TDECK_PLUS_ROW_TOPS = (75.02, 82.87, 90.72)
# Legend offsets from the key center (photo), per row as (left half, right
# half): primaries of the middle row sit left on the left half, and every
# secondary prints toward the outer side.
TDECK_PLUS_PRIMARY_DX = ((0.0, 0.0), (-0.45, 0.2), (0.0, 0.0))
TDECK_PLUS_SECONDARY_DX = ((-0.55, 0.55), (-0.95, 0.65), (-0.57, 0.66))
# Single legends that print off their row's offset (photo, gradient
# correlation per glyph), as (dx, dy) on top of it: the J's stem sits left,
# '#' and ')' sit further out, and the two quote marks are slanted marks
# printed lower than a cap-height straight quote.
TDECK_PLUS_LEGEND_NUDGE = {
    "J": (-0.35, 0.0), "#": (-0.45, 0.0), ")": (0.3, 0.0),
    "\u2019": (0.0, 0.5), "\u201d": (0.3, 0.5),
}
# (primary, secondary) per key.
TDECK_PLUS_KEY_ROWS: List[List[Tuple[str, str]]] = [
    [("Q", "#"), ("W", "1"), ("E", "2"), ("R", "3"), ("T", "("),
     ("Y", ")"), ("U", "_"), ("I", "-"), ("O", "+"), ("P", "@")],
    [("A", "*"), ("S", "4"), ("D", "5"), ("F", "6"), ("G", "/"),
     ("H", ":"), ("J", ";"), ("K", "\u2019"), ("L", "\u201d"),
     ("backspace", "")],
    [("alt", ""), ("Z", "7"), ("X", "8"), ("C", "9"), ("V", "?"),
     ("B", "!"), ("N", ","), ("M", "."), ("$", "speaker"), ("enter", "")],
]
# Bottom row (photo): key spans in x, top and bottom in y.
TDECK_PLUS_BOTTOM_ROW_Y = (98.65, 104.14)
TDECK_PLUS_BOTTOM_KEYS: List[Tuple[str, float, float]] = [
    ("shift", 11.6, 18.35), ("mic", 19.55, 26.45), ("space", 27.75, 45.95),
    ("sym", 47.25, 54.1), ("shift", 55.05, 62.0),
]

# LILYGO prints (photo): each glyph's ink center in x; caps 9.84-12.71 on
# the glass, 107.16-109.54 under the keyboard.
TDECK_PLUS_TOP_LETTERS: List[Tuple[str, float]] = [
    ("L", 30.33), ("I", 32.15), ("L", 34.0), ("Y", 36.85), ("G", 39.8),
    ("O", 42.8)]
TDECK_PLUS_BOTTOM_LETTERS: List[Tuple[str, float]] = [
    ("L", 32.0), ("I", 33.35), ("L", 34.93), ("Y", 36.75), ("G", 39.0),
    ("O", 41.55)]

TDECK_PLUS_LEGEND = "#f2f3f5"
TDECK_PLUS_PRINT = "#dcdde2"


def tdeck_plus_shell_points(body_w: float) -> List[Tuple[float, float]]:
    """The STEP outline: the body polygon with the two side rails added."""
    left, right = TDECK_PLUS_BODY_SIDES
    y0, y1, y2, y3 = TDECK_PLUS_RAIL_ENDS
    points: List[Tuple[float, float]] = []
    count = len(TDECK_PLUS_BODY)
    for index, point in enumerate(TDECK_PLUS_BODY):
        points.append(point)
        nxt = TDECK_PLUS_BODY[(index + 1) % count]
        if point[0] == nxt[0] == right and point[1] < y0 < nxt[1]:
            points += [(right, y0), (body_w, y1), (body_w, y2), (right, y3)]
        elif point[0] == nxt[0] == left and point[1] > y3 > nxt[1]:
            points += [(left, y3), (TDECK_PLUS_RAIL_X, y2),
                       (TDECK_PLUS_RAIL_X, y1), (left, y0)]
    return points


def tdeck_plus_inset(points: List[Tuple[float, float]], d_side: float,
                     d_top: float,
                     d_bottom: float) -> List[Tuple[float, float]]:
    """Offset a clockwise outline inward (mitered corners).

    Each edge moves by d_side when vertical, blending to d_top / d_bottom as
    it turns horizontal along the top / bottom of the outline.
    """
    count = len(points)
    lines = []
    for index in range(count):
        x0, y0 = points[index]
        x1, y1 = points[(index + 1) % count]
        length = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / length, (x1 - x0) / length
        dist = d_side * nx * nx + (d_top if ny > 0 else d_bottom) * ny * ny
        lines.append((x0 + nx * dist, y0 + ny * dist, x1 - x0, y1 - y0))
    out = []
    for index in range(count):
        ax, ay, adx, ady = lines[index - 1]
        bx, by, bdx, bdy = lines[index]
        cross = adx * bdy - ady * bdx
        if abs(cross) < 1e-9:
            out.append((bx, by))
            continue
        t = ((bx - ax) * bdy - (by - ay) * bdx) / cross
        out.append((ax + adx * t, ay + ady * t))
    return out


def tdeck_plus_shift_x(points: List[Tuple[float, float]],
                       dx: float) -> List[Tuple[float, float]]:
    """The polygon moved dx mm along x."""
    return [(x + dx, y) for x, y in points]


def tdeck_plus_clip_y(points: List[Tuple[float, float]], y_cut: float,
                      keep_above: bool) -> List[Tuple[float, float]]:
    """Clip a polygon to the part above (or below) the line y = y_cut."""
    def inside(point: Tuple[float, float]) -> bool:
        return point[1] <= y_cut if keep_above else point[1] >= y_cut

    def crossing(a: Tuple[float, float],
                 b: Tuple[float, float]) -> Tuple[float, float]:
        t = (y_cut - a[1]) / (b[1] - a[1])
        return (a[0] + (b[0] - a[0]) * t, y_cut)

    out: List[Tuple[float, float]] = []
    for index, cur in enumerate(points):
        prev = points[index - 1]
        if inside(cur):
            if not inside(prev):
                out.append(crossing(prev, cur))
            out.append(cur)
        elif inside(prev):
            out.append(crossing(prev, cur))
    return out


def tdeck_plus_path(points: List[Tuple[float, float]]) -> str:
    head, *rest = points
    return (f"M {f(head[0])},{f(head[1])} L "
            + " ".join(f"{f(x)},{f(y)}" for x, y in rest) + " Z")


def tdeck_plus_gradient(grad_id: str, start: Tuple[float, float],
                        end: Tuple[float, float],
                        stops: List[Tuple[float, str]]) -> str:
    """Multi-stop linear gradient in user space (mm)."""
    body = "".join(f'<stop offset="{f(offset * 100)}%" '
                   f'stop-color="{color}"/>\n' for offset, color in stops)
    return (f'<linearGradient id="{grad_id}" gradientUnits="userSpaceOnUse" '
            f'x1="{f(start[0])}" y1="{f(start[1])}" '
            f'x2="{f(end[0])}" y2="{f(end[1])}">\n{body}'
            '</linearGradient>\n')


def tdeck_plus_flip(x: float, mirrored: bool, axis: float) -> float:
    """x itself, or its mirror image across the vertical line x = axis."""
    return 2 * axis - x if mirrored else x


def append_tdeck_plus_case(out: List[str], device_id: str,
                           body_w: float) -> None:
    """Shell, the light bevel around the face, the glass and the plate."""
    body = TDECK_PLUS_BODY
    out.append(f'<path d="{tdeck_plus_path(tdeck_plus_shell_points(body_w))}" '
               f'fill="url(#case_{device_id})" stroke="#0a0a0c" '
               f'stroke-width="0.2" filter="url(#shadow_{device_id})"/>\n')
    # Bevel of the shell around the face: in the photos the bright band runs
    # x 1.82-2.63 on the left and 70.62-71.55 on the right, i.e. a 0.85 mm
    # band centered 1.54 in from the body sides; 1.20 in from the top, where
    # the band is dimmer and narrower.
    rim = tdeck_plus_inset(body, 1.54, 1.20, 1.95)
    out.append(f'<path d="{tdeck_plus_path(rim)}" fill="#161618" '
               f'stroke="url(#rim_{device_id})" stroke-width="0.85"/>\n')
    glass_y = TDECK_PLUS_GLASS_BOTTOM
    # Glass: just inside the bevel, 2.0 mm in from the body sides and 2.15
    # from the top (photo: the glass is dark from x 2.66 and y 2.2).
    glass = tdeck_plus_clip_y(tdeck_plus_inset(body, 2.0, 2.15, 2.35),
                              glass_y, True)
    out.append(f'<path d="{tdeck_plus_path(glass)}" fill="#111113"/>\n')
    # Keyboard plate: bright translucent edge, dark print inside it. Its
    # outer edge (photo, half-intensity crossings averaged over the key rows)
    # is at x 2.88 and 70.16: 67.3 wide (the PMMA plate of LILYGO's T-Deck 3D
    # model is 67.2) and 0.1 mm left of the body's center line; 1.7 mm in
    # from the bottom.
    plate = tdeck_plus_clip_y(
        tdeck_plus_shift_x(tdeck_plus_inset(body, 2.33, 2.0, 1.7),
                           TDECK_PLUS_PLATE_DX), glass_y, False)
    out.append(f'<path d="{tdeck_plus_path(plate)}" '
               f'fill="url(#plate_edge_{device_id})"/>\n')
    plate_print = tdeck_plus_clip_y(tdeck_plus_inset(body, 3.3, 2.0, 2.45),
                                    glass_y, False)
    out.append(f'<path d="{tdeck_plus_path(plate_print)}" '
               'fill="#2a2b2e"/>\n')
    x0, x1 = TDECK_PLUS_PRINT_X
    tx0, tx1, ty0, ty1 = TDECK_PLUS_TAB
    corner = 0.5
    out.append(
        f'<path d="M {f(x0)} {f(TDECK_PLUS_BAND_BOTTOM)} H {f(x1)} '
        f'V {f(ty0)} H {f(tx1)} V {f(ty1 - corner)} '
        f'Q {f(tx1)} {f(ty1)} {f(tx1 - corner)} {f(ty1)} '
        f'H {f(tx0 + corner)} Q {f(tx0)} {f(ty1)} {f(tx0)} {f(ty1 - corner)} '
        f'V {f(ty0)} H {f(x0)} Z" fill="url(#window_{device_id})"/>\n')
    out.append(rounded_rect(x0, TDECK_PLUS_GLASS_BOTTOM, x1 - x0,
                            TDECK_PLUS_BAND_BOTTOM - TDECK_PLUS_GLASS_BOTTOM,
                            r=0.0, fill=f"url(#band_{device_id})"))


def append_tdeck_plus_wordmark(out: List[str],
                               letters: List[Tuple[str, float]],
                               baseline: float, *, size: float, fill: str,
                               weight: str, scale_x: float = 1.0) -> None:
    """A wordmark set letter by letter at the photo's glyph centers."""
    for letter, cx in letters:
        out.append(text(cx, baseline, letter, size=size, fill=fill,
                        weight=weight, scale_x=scale_x))


def append_tdeck_plus_top(out: List[str]) -> None:
    """The slot above the screen (light ends, dark middle; its purpose is
    undocumented: LILYGO labels nothing there, and the speaker sounds through
    the lower edge) and the LILYGO print on the glass (photo)."""
    out.append(rounded_rect(29.33, 5.6, 15.17, 1.23, r=0.615,
                            fill="#77787c"))
    out.append(rounded_rect(32.58, 5.7, 8.14, 1.03, r=0.5, fill="#2a2a2d"))
    out.append(print_open("lilygo-glass", "glass"))
    append_tdeck_plus_wordmark(out, TDECK_PLUS_TOP_LETTERS, 12.71, size=4.15,
                               fill="#cfd2d8", weight="300")
    out.append(LEGEND_CLOSE)


def append_tdeck_plus_screen(out: List[str], device_id: str,
                             grad_screen: str, grad_wall: str) -> None:
    # The panel fills its viewing window; the picture is the active area,
    # inside it by the panel's 0.77 x 0.62 mm viewing-area margin.
    win_x, win_y, win_w, win_h = TDECK_PLUS_WINDOW
    # The aperture is edged by a hairline darker than the bezel (photo).
    out.append(rounded_rect(win_x, win_y, win_w, win_h, r=0.0,
                            fill=f"url(#{grad_screen})", stroke="#040406",
                            stroke_w=0.15))
    screen = TDECK_PLUS_SCREEN
    append_screen(out, screen)


def tdeck_plus_chevron(notch_x: float, tip_x: float, cy: float) -> str:
    """One printed chevron: 4.7 mm tall, edges leaning 0.55 mm per mm."""
    lean = 2.35 * 0.55
    direction = 1.0 if tip_x > notch_x else -1.0
    back = notch_x - direction * lean
    front = tip_x - direction * lean
    return (f'<path d="M {f(back)} {f(cy - 2.35)} L {f(front)} {f(cy - 2.35)} '
            f'L {f(tip_x)} {f(cy)} L {f(front)} {f(cy + 2.35)} '
            f'L {f(back)} {f(cy + 2.35)} L {f(notch_x)} {f(cy)} Z" '
            'fill="#bcbfc5"/>\n')


def append_tdeck_plus_band(out: List[str]) -> None:
    """Printed chevrons and trace lines either side of the trackball (photo,
    left half measured; the right half mirrors it about the band axis, the
    long traces running to the print's edge on each side)."""
    stroke = (f'stroke="{TDECK_PLUS_PRINT}" stroke-width="0.32" '
              'fill="none" stroke-linejoin="miter"')
    lean = 0.75  # trace diagonals: 0.75 mm across per mm up
    # The three traces of the left half: run along y, bend at x, then climb
    # to y 64.51; the lowest one then runs above the chevrons and steps down.
    # The band print is the one thing on the plate that is not square to the
    # case: it is turned about 0.38 deg clockwise, 0.21 mm at the far ends.
    # It is drawn level at its measured mean.
    traces = [(67.89, 9.31), (68.73, 9.73), (69.47, 10.43)]
    axis = TDECK_PLUS_BAND_AXIS
    out.append(print_open("band-print", "plate"))
    for mirrored in (False, True):
        edge = (TDECK_PLUS_PRINT_X[1] - 0.1 if mirrored
                else TDECK_PLUS_PRINT_X[0] + 0.1)

        def at(x: float, flip: bool = mirrored) -> str:
            return f(tdeck_plus_flip(x, flip, axis))
        for index, (y_run, x_bend) in enumerate(traces):
            x_top = x_bend + lean * (y_run - 64.51)
            path = (f'M {f(edge)} {f(y_run)} H {at(x_bend)} '
                    f'L {at(x_top)} {f(64.51)}')
            if index == len(traces) - 1:
                path += (f' H {at(25.38)} L {at(26.55)} {f(66.06)} '
                         f'H {at(28.22)}')
            out.append(f'<path d="{path}" {stroke}/>\n')
        for mark in range(3):
            x_mid = 11.82 + 0.85 * mark
            out.append(f'<path d="M {at(x_mid + 0.32)} {f(69.08)} '
                       f'L {at(x_mid - 0.36)} {f(69.93)}" {stroke}/>\n')
        for chevron in range(3):
            notch = 15.77 + 3.83 * chevron
            out.append(tdeck_plus_chevron(
                tdeck_plus_flip(notch, mirrored, axis),
                tdeck_plus_flip(notch + 2.8, mirrored, axis), 67.48))
    out.append(LEGEND_CLOSE)


def append_tdeck_plus_trackball(out: List[str], device_id: str) -> None:
    """Trackball (photo radial profile): bezel edge r 5.3, metal ring
    3.45-4.75 brightest at r 4.0, white ring 2.5-3.2 around the 2.48 mm
    ball."""
    cx, cy = TDECK_PLUS_TRACKBALL
    out.append(circle(cx, cy, 5.15, fill="#202124", stroke="#4a4b4f",
                      stroke_w=0.3))
    out.append(circle(cx, cy, 4.1, fill="none", stroke="#808184",
                      stroke_w=1.3))
    out.append(circle(cx, cy, 4.0, fill="none", stroke="#b6b7b9",
                      stroke_w=0.5))
    out.append(circle(cx, cy, 3.32, fill="#1a1b1d"))
    out.append(circle(cx, cy, 2.85, fill="none", stroke="#e4e5e3",
                      stroke_w=0.7))
    out.append(circle(cx, cy, 2.48, fill=f"url(#ball_{device_id})"))
    out.append(circle(cx - 0.2, cy - 0.5, 0.35, fill="#ffffff", opacity=0.35))


def append_tdeck_plus_keycap(out: List[str], device_id: str, x: float,
                             y: float, w: float, h: float) -> None:
    """Keycap with its dark rim; (x, y, w, h) is the rim's outer edge."""
    out.append(rounded_rect(x + 0.14, y + 0.14, w - 0.28, h - 0.28, r=1.0,
                            fill=f"url(#key_{device_id})", stroke="#141416",
                            stroke_w=0.28))


def append_tdeck_plus_key_icon(out: List[str], kind: str, cx: float,
                               top: float) -> None:
    """Icon legends drawn as shapes (photo)."""
    white = TDECK_PLUS_LEGEND
    line = f'stroke="{white}" fill="none" stroke-linejoin="round"'
    if kind == "backspace":
        y0, y1 = top + 3.7, top + 5.75
        out.append(f'<path d="M {f(cx - 1.12)} {f((y0 + y1) / 2)} '
                   f'L {f(cx - 0.6)} {f(y0)} H {f(cx + 1.12)} V {f(y1)} '
                   f'H {f(cx - 0.6)} Z" {line} stroke-width="0.2"/>\n')
        out.append(f'<path d="M {f(cx - 0.2)} {f(y0 + 0.45)} '
                   f'L {f(cx + 0.65)} {f(y1 - 0.45)} M {f(cx + 0.65)} '
                   f'{f(y0 + 0.45)} L {f(cx - 0.2)} {f(y1 - 0.45)}" {line} '
                   'stroke-width="0.3"/>\n')
    elif kind == "enter":
        out.append(f'<path d="M {f(cx + 0.75)} {f(top + 3.45)} '
                   f'V {f(top + 4.95)} H {f(cx - 0.45)}" {line} '
                   'stroke-width="0.42"/>\n')
        out.append(f'<path d="M {f(cx - 1.0)} {f(top + 4.95)} '
                   f'L {f(cx - 0.35)} {f(top + 4.35)} '
                   f'L {f(cx - 0.35)} {f(top + 5.55)} Z" fill="{white}"/>\n')
    elif kind == "speaker":
        out.append(f'<path d="M {f(cx - 0.75)} {f(top + 1.42)} '
                   f'H {f(cx - 0.4)} L {f(cx + 0.05)} {f(top + 1.02)} '
                   f'V {f(top + 2.27)} L {f(cx - 0.4)} {f(top + 1.87)} '
                   f'H {f(cx - 0.75)} Z" fill="{white}"/>\n')
        out.append(f'<path d="M {f(cx + 0.35)} {f(top + 1.25)} '
                   f'Q {f(cx + 0.6)} {f(top + 1.65)} {f(cx + 0.35)} '
                   f'{f(top + 2.05)} M {f(cx + 0.62)} {f(top + 1.0)} '
                   f'Q {f(cx + 1.0)} {f(top + 1.65)} {f(cx + 0.62)} '
                   f'{f(top + 2.3)}" {line} stroke-width="0.16"/>\n')
    elif kind == "shift":
        out.append(f'<path d="M {f(cx)} {f(top)} L {f(cx + 0.75)} '
                   f'{f(top + 0.95)} H {f(cx + 0.4)} V {f(top + 2.1)} '
                   f'H {f(cx - 0.4)} V {f(top + 0.95)} H {f(cx - 0.75)} Z" '
                   f'fill="{white}"/>\n')
    elif kind == "mic":
        out.append(rounded_rect(cx - 0.45, top, 0.9, 1.5, r=0.45, fill=white))
        out.append(f'<path d="M {f(cx - 0.8)} {f(top + 0.8)} '
                   f'Q {f(cx - 0.8)} {f(top + 1.85)} {f(cx)} {f(top + 1.85)} '
                   f'Q {f(cx + 0.8)} {f(top + 1.85)} {f(cx + 0.8)} '
                   f'{f(top + 0.8)}" {line} stroke-width="0.25"/>\n')
        out.append(f'<path d="M {f(cx - 0.18)} {f(top + 1.85)} '
                   f'H {f(cx + 0.18)} V {f(top + 2.05)} H {f(cx + 0.6)} '
                   f'V {f(top + 2.3)} H {f(cx - 0.6)} V {f(top + 2.05)} '
                   f'H {f(cx - 0.18)} Z" fill="{white}"/>\n')


def append_tdeck_plus_keyboard(out: List[str], device_id: str) -> None:
    """Three rows of ten keys and the bottom row (photo-measured)."""
    for row_index, row in enumerate(TDECK_PLUS_KEY_ROWS):
        top = TDECK_PLUS_ROW_TOPS[row_index]
        for col, (primary, secondary) in enumerate(row):
            x = TDECK_PLUS_KEY_X0 + col * TDECK_PLUS_KEY_PITCH
            cx = x + TDECK_PLUS_KEY_W / 2
            append_tdeck_plus_keycap(out, device_id, x, top,
                                     TDECK_PLUS_KEY_W, TDECK_PLUS_KEY_H)
            # What is printed on the cap goes in the key's legend group.
            out.append(legend_open(key_slug(primary)))
            if primary in ("backspace", "enter"):
                append_tdeck_plus_key_icon(out, primary, cx, top)
            elif primary == "alt":
                out.append(text(cx - 0.45, top + 5.0, "alt", size=2.9,
                                fill=TDECK_PLUS_LEGEND, weight="500"))
            else:
                dx = TDECK_PLUS_PRIMARY_DX[row_index][col >= 5]
                dx += TDECK_PLUS_LEGEND_NUDGE.get(primary, (0.0, 0.0))[0]
                out.append(text(cx + dx, top + 5.27, primary, size=3.2,
                                fill=TDECK_PLUS_LEGEND, weight="500",
                                scale_x=0.88))
            if secondary == "speaker":
                append_tdeck_plus_key_icon(out, "speaker", cx + 0.5, top)
            elif secondary:
                outward = TDECK_PLUS_SECONDARY_DX[row_index][col >= 5]
                nudge_x, nudge_y = TDECK_PLUS_LEGEND_NUDGE.get(secondary,
                                                               (0.0, 0.0))
                out.append(text(cx + outward + nudge_x,
                                top + 2.25 + nudge_y, secondary,
                                size=2.0, fill=TDECK_PLUS_LEGEND,
                                weight="500"))
            out.append(LEGEND_CLOSE)
    y0, y1 = TDECK_PLUS_BOTTOM_ROW_Y
    for (kind, x0, x1), slug in zip(TDECK_PLUS_BOTTOM_KEYS,
                                    tdeck_plus_bottom_slugs(),
                                    strict=True):
        cx = (x0 + x1) / 2
        append_tdeck_plus_keycap(out, device_id, x0, y0, x1 - x0, y1 - y0)
        out.append(legend_open(slug))
        if kind == "shift":
            # Photo: the left arrow sits 0.75 mm left of its key center and
            # 1.75 below the key top, the right one 0.3 left and 2.5 below.
            icon_x, icon_top = ((cx - 0.77, 1.75) if x0 < 36
                                else (cx - 0.32, 2.5))
            append_tdeck_plus_key_icon(out, "shift", icon_x, y0 + icon_top)
        elif kind == "mic":
            out.append(text(cx - 1.93, y0 + 2.4, "0", size=2.0,
                            fill=TDECK_PLUS_LEGEND, weight="500"))
            append_tdeck_plus_key_icon(out, "mic", cx - 0.4, y0 + 1.95)
        elif kind == "space":
            out.append(f'<path d="M {f(32.72)} {f(y0 + 1.75)} '
                       f'V {f(y0 + 3.05)} H {f(39.73)} V {f(y0 + 1.75)}" '
                       f'stroke="{TDECK_PLUS_LEGEND}" stroke-width="0.28" '
                       'fill="none"/>\n')
        elif kind == "sym":
            out.append(text(cx - 0.1, y0 + 3.35, "sym", size=2.4,
                            fill=TDECK_PLUS_LEGEND, weight="500",
                            scale_x=0.92))
        out.append(LEGEND_CLOSE)


# The two round marks printed beside the bottom row (photo): each one's
# center, and how far its dark bar leans across per mm down.
TDECK_PLUS_ROUND_MARKS = ((7.82, 101.72, 0.45), (66.0, 101.78, -0.45))


def append_tdeck_plus_round_marks(out: List[str]) -> None:
    """The solid part of the two printed round marks: a disc split by a dark
    bar, each inside the ring ``append_tdeck_plus_bottom_print`` draws.

    A print of their own, on a plane of their own: in the board's model a
    plane is one legends mesh an ink, which says how thin its print is so a
    reader showing the board small can leave a mesh out. These 2 mm discs
    are printed in the ink of the plate's hairline traces, and on the
    traces' plane they were left out with them. Their 0.3 mm rings are
    hairlines and stay with the traces. The discs and bars touch no other
    print (a ring's inner edge is 0.08 mm outside its disc), so where the
    group is painted changes no pixel.
    """
    out.append(print_open("round-marks", "plate-marks"))
    for cx, cy, slope in TDECK_PLUS_ROUND_MARKS:
        out.append(circle(cx, cy, 1.0, fill=TDECK_PLUS_PRINT))
        dx, dy = 1.1 * slope, 1.1
        out.append(f'<path d="M {f(cx - dx)} {f(cy - dy)} L {f(cx + dx)} '
                   f'{f(cy + dy)}" stroke="#2f3033" stroke-width="0.32" '
                   'fill="none"/>\n')
    out.append(LEGEND_CLOSE)


def append_tdeck_plus_bottom_print(out: List[str]) -> None:
    """The rings of the two round marks beside the bottom row and the LILYGO
    print under it (photo): traces from 0.5 mm rings, arrowheads, the bold
    wordmark. The marks' discs and bars are a print of their own
    (``append_tdeck_plus_round_marks``)."""
    out.append(print_open("bottom-print", "plate"))
    for cx, cy, _slope in TDECK_PLUS_ROUND_MARKS:
        out.append(circle(cx, cy, 1.45, fill="none", stroke=TDECK_PLUS_PRINT,
                          stroke_w=0.3))
    axis = 37.1  # the print's mirror axis (photo)
    stroke = (f'stroke="{TDECK_PLUS_PRINT}" stroke-width="0.28" '
              'fill="none"')
    for mirrored in (False, True):
        def at(x: float, flip: bool = mirrored) -> str:
            return f(tdeck_plus_flip(x, flip, axis))
        out.append(circle(tdeck_plus_flip(12.28, mirrored, axis), 106.94,
                          0.5, fill="none", stroke=TDECK_PLUS_PRINT,
                          stroke_w=0.25))
        out.append(f'<path d="M {at(12.62)} {f(107.31)} '
                   f'L {at(13.45)} {f(108.21)} H {at(27.55)}" {stroke}/>\n')
        out.append(f'<path d="M {at(28.42)} {f(107.47)} '
                   f'L {at(29.65)} {f(108.17)} L {at(28.42)} {f(108.87)} Z" '
                   f'fill="{TDECK_PLUS_PRINT}"/>\n')
    append_tdeck_plus_wordmark(out, TDECK_PLUS_BOTTOM_LETTERS, 109.54,
                               size=3.35, fill="#e9eaed", weight="800",
                               scale_x=0.93)
    out.append(text(43.57, 108.14, "®", size=2.2, fill="#e9eaed",
                    weight="600"))
    out.append(LEGEND_CLOSE)


def tdeck_plus_bottom_slugs() -> list[str]:
    """The slug of each bottom-row key, in the row's order.

    The row's two shift keys share a legend, so their slugs say which one:
    ``shift-left`` and ``shift-right``.
    """
    seen: dict[str, int] = {}
    slugs: list[str] = []
    for kind, _x0, _x1 in TDECK_PLUS_BOTTOM_KEYS:
        seen[kind] = seen.get(kind, 0) + 1
        slugs.append(kind if kind != "shift" else (
            "shift-left" if seen[kind] == 1 else "shift-right"))
    return slugs


def tdeck_plus_hotspots() -> List[Hotspot]:
    """Every keycap, then the trackball.

    The bottom row's two shift keys share a legend, so their ids say which
    one: ``hs-key-shift-left`` and ``hs-key-shift-right``.
    """
    spots: List[Hotspot] = []
    for row_index, row in enumerate(TDECK_PLUS_KEY_ROWS):
        top = TDECK_PLUS_ROW_TOPS[row_index]
        for col, (primary, _secondary) in enumerate(row):
            cx = (TDECK_PLUS_KEY_X0 + col * TDECK_PLUS_KEY_PITCH
                  + TDECK_PLUS_KEY_W / 2)
            spots.append(Hotspot(f"key-{key_slug(primary)}", cx,
                                 top + TDECK_PLUS_KEY_H / 2,
                                 TDECK_PLUS_KEY_W, TDECK_PLUS_KEY_H,
                                 label=primary))
    y0, y1 = TDECK_PLUS_BOTTOM_ROW_Y
    for (kind, x0, x1), hid in zip(TDECK_PLUS_BOTTOM_KEYS,
                                   tdeck_plus_bottom_slugs(),
                                   strict=True):
        spots.append(Hotspot(f"key-{hid}", (x0 + x1) / 2, (y0 + y1) / 2,
                             x1 - x0, y1 - y0, label=kind))
    ball_x, ball_y = TDECK_PLUS_TRACKBALL
    spots.append(Hotspot("Trackball", ball_x, ball_y,
                         TDECK_PLUS_BALL_D, TDECK_PLUS_BALL_D))
    return spots


def gen_tdeck_plus(device_id: str, name: str,
                   body_w: float, body_h: float) -> str:
    grad_screen = f"screen_{device_id}"
    grad_wall = f"wall_{device_id}"
    across = ((TDECK_PLUS_PRINT_X[0], 0.0), (TDECK_PLUS_PRINT_X[1], 0.0))
    out = [svg_header(name, body_w, body_h),
           DEFS_OPEN,
           shadow_filter(device_id),
           linear_gradient(f"case_{device_id}", "#525357", "#36373b"),
           # Shell bevel brightness down the case (photo): 100 at the top,
           # 130-140 along the screen, 85-100 beside the keys, dark below.
           tdeck_plus_gradient(f"rim_{device_id}", (0, 0), (0, body_h), [
               (0.0, "#6a6b6f"), (0.2, "#86878b"), (0.75, "#6c6d71"),
               (0.9, "#38393c"), (1.0, "#242427")]),
           linear_gradient(f"plate_edge_{device_id}", "#b4b5bb", "#6f7075"),
           linear_gradient(f"key_{device_id}", "#66686f", "#45474d"),
           tdeck_plus_gradient(f"band_{device_id}", across[0], across[1], [
               (0.0, "#46474b"), (0.3, "#202124"), (0.42, "#141416"),
               (0.6, "#151517"), (0.8, "#323336"), (1.0, "#4a4b4f")]),
           tdeck_plus_gradient(f"window_{device_id}", across[0], across[1], [
               (0.0, "#b0b0b6"), (0.3, "#8e8e94"), (0.5, "#838389"),
               (0.75, "#8e8e94"), (1.0, "#b4b4ba")]),
           screen_gradient(grad_screen, c_in="#15171d", c_out="#050608"),
           screen_gradient(grad_wall, c_in="#3a4a6a", c_out="#0c0e16"),
           screen_gradient(f"ball_{device_id}", c_in="#3c3d40",
                           c_out="#101113"),
           DEFS_CLOSE]
    append_tdeck_plus_case(out, device_id, body_w)
    append_tdeck_plus_top(out)
    append_tdeck_plus_screen(out, device_id, grad_screen, grad_wall)
    append_tdeck_plus_band(out)
    append_tdeck_plus_trackball(out, device_id)
    append_tdeck_plus_keyboard(out, device_id)
    append_tdeck_plus_bottom_print(out)
    append_tdeck_plus_round_marks(out)
    out.append(hotspots_block(tdeck_plus_hotspots()))
    out.append(caption_block(name, body_w, body_h))
    out.append(SVG_CLOSE)
    return "".join(out)


# ---------------------------------------------------------------------------
# Device registry
# ---------------------------------------------------------------------------


@dataclass
class DeviceSpec:
    device_id: str
    name: str
    body_w: float
    body_h: float
    builder: Callable[..., str]
    builder_kwargs: dict = field(default_factory=dict)


DEVICES: List[DeviceSpec] = [
    # M5Stack publishes 48.0 x 24.0 x 13.5 mm for both the Plus 1.1 and the
    # Plus2 (one chassis); its dimension drawing gives 24 x 48 with R3
    # corners, and the registered front photos give a width / height ratio
    # of 0.494-0.500.
    DeviceSpec("m5stickc-plus1", "M5StickC Plus 1.1", 24.0, 48.0,
               gen_stick_like, {
                   "style": StickLikeStyle(
                       # Case and wall tones sampled on the registered
                       # photos: face #fe3d1e at the top and #fe3a1a at the
                       # bottom, window walls #fa2705 (top) to #ee1c06
                       # (bottom).
                       case_top="#fe3d1e", case_bot="#fc3a1b",
                       case_stroke="#e2301a",
                       case_r=PLUS_CASE_R,
                       plus=PlusFacePalette(
                           lip_top="#fa2705", lip_bottom="#ee1c06",
                           slot="#c41b0c", slot_core="#820000",
                           slot_rim="#ff4b2e",
                           letter="#fb2307", letter_edge="#c41a05"),
                       screen_y_mm=PLUS_SCREEN_Y,
                       btn_b_span=PLUS_BTN_B_SPAN,
                       power_span=PLUS_POWER_SPAN)}),
    DeviceSpec("m5stickc-plus2", "M5StickC Plus2", 24.0, 48.0,
               gen_stick_like, {
                   "style": StickLikeStyle(
                       # Face #feb722 at the top and #feb420 at the bottom
                       # on the registered photos; of the window walls only
                       # the top one reads there (#f9a512), the others
                       # follow the Plus 1.1's fall-off.
                       case_top="#feb722", case_bot="#fbb31f",
                       case_stroke="#e39e1f",
                       case_r=PLUS_CASE_R,
                       plus=PlusFacePalette(
                           lip_top="#f9a512", lip_bottom="#ef9a0c",
                           slot="#d39a4a", slot_core="#3a1004",
                           slot_rim="#fdcb5c",
                           letter="#f7a30a", letter_edge="#c27808"),
                       # Same chassis and screen origin as the Plus 1.1.
                       screen_y_mm=PLUS_SCREEN_Y,
                       btn_b_span=PLUS_BTN_B_SPAN,
                       power_span=PLUS_POWER_SPAN)}),
    # The Plus chassis again (M5Stack's own drawing of the SE gives the same
    # 24 x 48 with R3 corners and the same window), in a translucent orange
    # shell. Case tones sampled on the registered front photo: the shell
    # over nothing reads #f2633e at the top and #ec542f at the bottom, and
    # its silhouette, where the plastic is thickest, #c23a1b.
    DeviceSpec("m5stickc-plus-se", "M5StickC Plus SE", 24.0, 48.0,
               gen_stick_like, {
                   "style": StickLikeStyle(
                       case_top="#f2633e", case_bot="#ec542f",
                       case_stroke="#c23a1b",
                       case_r=PLUS_CASE_R,
                       screen_y_mm=PLUS_SCREEN_Y,
                       face_kind="plus_se",
                       btn_b_span=SE_BTN_B_SPAN,
                       power_span=SE_POWER_SPAN)}),
    DeviceSpec("sticks3", "M5StickS3", 24.0, 48.0,
               gen_stick_like, {
                   "style": StickLikeStyle(
                       case_top="#4a4a4c", case_bot="#525254",
                       case_stroke="#636366",
                       btn_a_color="#0868f0",
                       # The photo's white demo field spans 4.56-19.42 x
                       # 4.65-29.56 mm (14.87 x 24.91, the datasheet size).
                       screen_y_mm=4.65,
                       face_kind="sticks3_brand",
                       btn_b_span=S3_BTN_B_SPAN,
                       power_span=S3_POWER_SPAN)}),
    DeviceSpec("m5stack-core2-v13", "M5Stack Core2 v1.3", 54.0, 54.0,
               gen_core2),
    DeviceSpec("cores3-se", "M5Stack CoreS3 SE", 54.0, 54.0,
               gen_cores3_se),
    DeviceSpec("coreink", "M5Stack CoreInk", 40.0, 56.0, gen_coreink),
    DeviceSpec("cardputer", "M5Stack Cardputer ADV", 84.0, 54.0, gen_cardputer),
    DeviceSpec("tdeck-plus", "LILYGO T-Deck Plus", 73.14, 114.98,
               gen_tdeck_plus),
]


# ---------------------------------------------------------------------------
# Contact sheet
# ---------------------------------------------------------------------------


# fronts-contact-sheet.svg: every device's front.svg, in DEVICES order, on a
# grid of white tiles under a two-line heading. Sheet units are arbitrary
# (the fronts are scaled per tile, not to one common mm scale). Each front
# is scaled to fit its tile's inner box and centered in it.
CONTACT_SHEET_PATH = ROOT / "fronts-contact-sheet.svg"
SHEET_COLUMNS = 5
SHEET_MARGIN = 14.0
SHEET_TOP = 38.0
SHEET_TILE_W = 136.0
SHEET_TILE_H = 166.0
SHEET_GAP = 10.0
# Inner box of a tile: inset from the tile's left and top edges, size.
SHEET_TILE_PAD_X = 9.0
SHEET_TILE_PAD_Y = 8.0
SHEET_FIT_W = SHEET_TILE_W - 2 * SHEET_TILE_PAD_X
SHEET_FIT_H = SHEET_TILE_H - 2 * SHEET_TILE_PAD_Y
SHEET_PIXEL_W = 1600

_SVG_ROOT_RE = re.compile(r"\A\s*<svg\b([^>]*)>\n?(.*)</svg>\s*\Z", re.S)
_ATTR_RE = re.compile(r'([\w:-]+)="([^"]*)"')
_ID_RE = re.compile(r'(?<![\w:-])id="([^"]+)"')
_URL_REF_RE = re.compile(r"url\(#([^)\s]+)\)")
_HREF_REF_RE = re.compile(r'((?:xlink:)?href)="#([^"]+)"')


def namespace_ids(body: str, prefix: str) -> str:
    """Prefix every id in ``body`` and every reference to one of them
    (``url(#...)``, ``href="#..."``) with ``prefix``, so several fronts can
    share one document. A reference to an id the body does not define is
    an error: it would silently point at another front's element."""
    ids = set(_ID_RE.findall(body))

    def target(name: str) -> str:
        if name not in ids:
            raise ValueError(f"reference to undefined id #{name}")
        return prefix + name

    body = _ID_RE.sub(lambda m: f'id="{prefix}{m.group(1)}"', body)
    body = _URL_REF_RE.sub(lambda m: f"url(#{target(m.group(1))})", body)
    return _HREF_REF_RE.sub(
        lambda m: f'{m.group(1)}="#{target(m.group(2))}"', body)


def contact_sheet_tile(device_id: str, front_svg: str, tile_x: float,
                       tile_y: float) -> str:
    """One tile: its frame, then the front scaled into the inner box."""
    match = _SVG_ROOT_RE.match(front_svg)
    if not match:
        raise ValueError(f"{device_id}: front.svg has no <svg> root")
    attrs = dict(_ATTR_RE.findall(match.group(1)))
    min_x, min_y, vb_w, vb_h = (float(v) for v in attrs["viewBox"].split())
    scale = min(SHEET_FIT_W / vb_w, SHEET_FIT_H / vb_h)
    tx = tile_x + SHEET_TILE_PAD_X + (SHEET_FIT_W - vb_w * scale) / 2
    ty = tile_y + SHEET_TILE_PAD_Y + (SHEET_FIT_H - vb_h * scale) / 2
    # The front's root presentation attributes move onto its group.
    inherited = "".join(f' {name}="{attrs[name]}"'
                        for name in ("shape-rendering", "font-family")
                        if name in attrs)
    body = namespace_ids(match.group(2), f"{device_id}--")
    return (
        f'<g id="tile_{device_id}">\n'
        + rounded_rect(tile_x, tile_y, SHEET_TILE_W, SHEET_TILE_H, r=3.0,
                       fill="#ffffff", stroke="#d9dee8", stroke_w=0.4)
        + f'<g transform="translate({f(tx)} {f(ty)}) scale({f(scale)}) '
        f'translate({f(-min_x)} {f(-min_y)})"{inherited}>\n'
        + body
        + '</g>\n</g>\n'
    )


def build_contact_sheet(fronts: List[Tuple[str, str]]) -> str:
    """The contact sheet for ``fronts``, a list of (device_id, front.svg)."""
    rows = -(-len(fronts) // SHEET_COLUMNS)
    sheet_w = (2 * SHEET_MARGIN + SHEET_COLUMNS * SHEET_TILE_W
               + (SHEET_COLUMNS - 1) * SHEET_GAP)
    sheet_h = (SHEET_TOP + rows * SHEET_TILE_H + (rows - 1) * SHEET_GAP
               + SHEET_MARGIN)
    pixel_h = round(SHEET_PIXEL_W * sheet_h / sheet_w)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {f(sheet_w)} {f(sheet_h)}" width="{SHEET_PIXEL_W}" '
        f'height="{pixel_h}" shape-rendering="geometricPrecision" '
        'font-family="Inter, Helvetica, Arial, sans-serif">\n',
        '<title>Kleidos device front.svg contact sheet</title>\n',
        f'<rect x="0" y="0" width="{f(sheet_w)}" height="{f(sheet_h)}" '
        'fill="#f6f7f9"/>\n',
        text(SHEET_MARGIN, 21.0, "Kleidos front.svg assets", size=6.0,
             fill="#20242b", anchor="start", weight="800"),
        text(SHEET_MARGIN, 29.0,
             "Final vector fronts, scaled per tile for review", size=3.2,
             fill="#68707d", anchor="start"),
    ]
    for index, (device_id, front_svg) in enumerate(fronts):
        col = index % SHEET_COLUMNS
        row = index // SHEET_COLUMNS
        out.append(contact_sheet_tile(
            device_id, front_svg,
            SHEET_MARGIN + col * (SHEET_TILE_W + SHEET_GAP),
            SHEET_TOP + row * (SHEET_TILE_H + SHEET_GAP)))
    out.append(SVG_CLOSE)
    return "".join(out)


def write_contact_sheet() -> None:
    """Rebuild fronts-contact-sheet.svg from the front.svg files on disk."""
    fronts = [(spec.device_id,
               (ROOT / spec.device_id / "svg" / "front.svg")
               .read_text(encoding="utf-8"))
              for spec in DEVICES]
    CONTACT_SHEET_PATH.write_text(build_contact_sheet(fronts),
                                  encoding="utf-8")
    print(f"ok  {CONTACT_SHEET_PATH.name}")


def main(argv: List[str]) -> int:
    flags = [arg for arg in argv if arg.startswith("--")]
    device_ids = [arg for arg in argv if not arg.startswith("--")]
    unknown_flags = [flag for flag in flags if flag != "--contact-sheet"]
    if unknown_flags:
        print(f"unknown option(s): {', '.join(unknown_flags)}; "
              "known: --contact-sheet", file=sys.stderr)
        return 2
    known = {spec.device_id for spec in DEVICES}
    unknown = [device_id for device_id in device_ids
               if device_id not in known]
    if unknown:
        print(f"unknown device id(s): {', '.join(unknown)}; "
              f"known: {', '.join(sorted(known))}", file=sys.stderr)
        return 2
    for spec in DEVICES:
        if device_ids and spec.device_id not in device_ids:
            continue
        out_path = ROOT / spec.device_id / "svg" / "front.svg"
        svg = spec.builder(
            spec.device_id, spec.name, spec.body_w, spec.body_h,
            **spec.builder_kwargs,
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(svg, encoding="utf-8")
        print(f"ok  {spec.device_id:<22s}  {spec.body_w}×{spec.body_h} mm")
    if flags:
        write_contact_sheet()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
