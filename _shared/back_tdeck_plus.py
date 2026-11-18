# SPDX-License-Identifier: MIT
"""What the LilyGO T-Deck Plus prints on its back, for ``emit_back_svg.py``

The shell's back carries no sticker: four prints in one light-grey ink, all
on its flat outer face (the STEP's z -19.0 in the build frame), tone on tone:

* ``T-DECK`` large in the raised top frame (plane ``frame``), and round it
  a thin outline (plane ``frame-line``) that follows the frame: a run over
  the name, a chamfer and a short drop at each end, and a tail out under
  each screw hole;
* on the trapezoid's inner panel, LilyGO's mascot (the figure of its logo:
  one hand raised in a V, a bracelet on the wrist, a tablet held at her
  side) over the panel's small hole, and a small ``T-DECK`` under the hole
  (plane ``badge``);
* ``LILYGO®`` on the band at the bottom end (plane ``base``), on the flat
  face and not on the slope round the end.

Each plane holds prints of one weight, so a reader that leaves out the
prints too thin for its scale keeps the large name after the outline and
the badge are gone.

Measured on LilyGO's straight-on back photo (the T-Deck Plus pinmap sheet,
3000 px), registered on the model's back through the two screw holes and the
nut seat, 15.99 px a mm: every letter's ink box at half its contrast, read on
profiles across its strokes, the cap height from the flat letters. That unit
prints the top frame's name and the run over it about 0.6 degrees off level;
both are drawn level, at the mean of their ends. The badge's prints keep
their place in the trapezoid round them rather than against the screws: once
the screws are matched, the photo's grooves either side of the small word lie
0.48 mm left of the STEP's, so both prints move 0.48 mm right.

The real faces are LilyGO's: ``T-DECK`` is a square face with chamfered
corners and 1.5 mm stems, LILYGO its own wordmark. Each letter is set in
Inter Bold, the one face the models carry, scaled to the box the photo prints
it in, so the letters' places and sizes are the photo's and their shapes are
Inter's (rounder, its stems 1.2-1.4 mm). The hyphens are bars, and the
outline is a stroke 0.3 mm wide (the photo reads 0.3-0.4 mm at half its
contrast, blurred over its own pixel). The mascot is the outline of the
print on the same photo, traced at half its contrast, smoothed over 0.06 mm
(finer than the photo's pixel, 0.063 mm) and simplified to 0.008 mm.

All in the back frame (``board_faces.py``): mm, x from the case's left edge
as seen from behind, y down from its top.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import emit_front_svg as fronts

#: The ink: the photo's print (170-176 on every word) over the case beside
#: it (120-137), white-balanced in linear light onto the model's case color
#: (``measurements.json`` ``case.color`` #525357).
TDECK_BACK_INK = '#767b7f'
#: Inter Bold's ink extents in font units (unitsPerEm 2048, cap height 1490):
#: xMin and xMax of each glyph the back sets (Inter 4.1, ``fonts``).
INTER_BOLD_X = {'T': (75, 1292), 'D': (135, 1385), 'E': (135, 1134), 'C': (94, 1428),
                'K': (135, 1422), 'L': (135, 1083), 'I': (135, 440), 'Y': (49, 1448),
                'G': (94, 1438), 'O': (94, 1484)}
INTER_UPEM = 2048
INTER_CAP = 1490
#: Inter's registered sign: its ring's extents in font units (x, then y up).
INTER_BOLD_REG = (97, 1260, 346, 1510)

#: A word: its cap top and baseline, then each letter with its ink's left and
#: right edge, and each bar (a hyphen) as x0, x1, y0, y1.
Word = Tuple[float, float, Sequence[Tuple[str, float, float]], Sequence[Tuple[float, float, float, float]]]

#: The top frame's name: 6.11 mm caps (the mean of T's, D's, E's and K's,
#: 14.17..20.50 from the K to the T on that unit), 31.1 mm long.
TDECK_FRAME_WORD: Word = (
    14.28, 20.39,
    (('T', 20.28, 25.53), ('D', 29.48, 34.72), ('E', 35.48, 40.03), ('C', 40.82, 45.82),
     ('K', 46.43, 51.40)),
    ((25.79, 28.44, 17.60, 18.74),),
)
#: The outline round it: one stroke through these points, left tail to
#: right tail, symmetric about the screws' axis (x 36.235).
TDECK_FRAME_LINE = (
    (8.615, 15.115), (12.69, 15.115), (14.80, 12.91), (14.80, 10.23), (16.39, 8.49),
    (56.08, 8.49), (57.67, 10.23), (57.67, 12.91), (59.78, 15.115), (63.855, 15.115),
)
TDECK_FRAME_LINE_WIDTH = 0.3
#: The badge's name under its hole, as the photo prints it against the
#: screws: 2.4 mm caps.
TDECK_BADGE_WORD: Word = (
    82.82, 85.22,
    (('T', 29.98, 31.94), ('D', 33.60, 35.62), ('E', 36.02, 37.95), ('C', 38.18, 40.14),
     ('K', 40.31, 42.32)),
    ((32.13, 33.13, 84.05, 84.55),),
)
#: How far right of the photo's place (against the screws) the badge's two
#: prints are drawn, to keep their place in the trapezoid round them.
TDECK_BADGE_SHIFT = 0.48
#: The bottom end's wordmark: 4.11 mm caps.
TDECK_BASE_WORD: Word = (
    100.86, 104.97,
    (('L', 25.47, 28.10), ('I', 28.56, 29.67), ('L', 30.55, 33.26), ('Y', 33.10, 37.05),
     ('G', 37.04, 40.99), ('O', 41.48, 45.76)),
    (),
)
#: The registered sign after it: its ring's box (x0, x1, y0, y1).
TDECK_BASE_REG = (45.80, 48.15, 100.17, 102.56)

#: The mascot: its outline and the four holes in it, traced from the photo
#: (against the screws, like the badge's name).
TDECK_MASCOT = (
    (
        (37.73, 69.66), (37.59, 69.77), (37.45, 69.86), (37.33, 70.03), (37.28, 70.07), (37.21, 70.09),
        (37, 70.07), (36.89, 70.1), (36.71, 70.2), (36.53, 70.4), (36.43, 70.46), (36.17, 70.49),
        (36.02, 70.47), (35.89, 70.41), (35.72, 70.25), (35.7, 70.24), (35.66, 70.25), (35.54, 70.38),
        (35.34, 70.5), (35.24, 70.57), (35.09, 70.71), (35.03, 70.78), (34.93, 71.03), (34.93, 71.11),
        (34.97, 71.28), (34.96, 71.34), (34.94, 71.39), (34.85, 71.45), (34.61, 71.49), (34.55, 71.53),
        (34.55, 71.57), (34.57, 71.65), (34.81, 71.92), (34.9, 72.26), (35.01, 72.51), (35.06, 72.58),
        (35.13, 72.63), (35.51, 72.86), (35.64, 73.02), (35.68, 73.05), (35.87, 73.08), (35.92, 73.1),
        (35.96, 73.17), (35.97, 73.25), (35.96, 73.31), (35.93, 73.36), (35.89, 73.39), (35.56, 73.55),
        (35.31, 73.64), (35.16, 73.77), (35.08, 73.8), (35, 73.78), (34.78, 73.68), (34.49, 73.66),
        (34.04, 73.58), (33.88, 73.52), (33.69, 73.42), (33.52, 73.38), (33.46, 73.33), (33.43, 73.28),
        (33.42, 73.19), (33.46, 72.65), (33.42, 72.42), (33.44, 72.18), (33.43, 72), (33.44, 71.91),
        (33.56, 71.39), (33.55, 71.31), (33.39, 71.14), (33.34, 71.04), (33.35, 70.96), (33.43, 70.64),
        (33.42, 70.31), (33.38, 70.23), (33.34, 70.2), (33.29, 70.19), (33.14, 70.2), (33.1, 70.18),
        (32.96, 70.03), (32.87, 69.98), (32.81, 69.98), (32.77, 70.01), (32.74, 70.06), (32.7, 70.17),
        (32.68, 70.31), (32.7, 70.61), (32.73, 70.69), (32.87, 70.93), (32.91, 71.04), (32.9, 71.09),
        (32.88, 71.14), (32.76, 71.26), (32.73, 71.31), (32.72, 71.52), (32.76, 71.59), (32.8, 71.62),
        (32.96, 71.68), (33, 71.72), (33.02, 71.77), (33.02, 71.86), (33, 71.91), (32.88, 72.03),
        (32.86, 72.1), (32.9, 72.18), (33.02, 72.3), (33.05, 72.38), (33.05, 72.68), (33.17, 73.21),
        (33.14, 73.47), (33.14, 73.53), (33.16, 73.58), (33.22, 73.64), (33.3, 73.68), (33.77, 73.79),
        (34.24, 73.98), (34.56, 74.01), (34.96, 74.2), (34.99, 74.25), (34.99, 74.33), (34.86, 74.6),
        (34.84, 74.68), (34.91, 74.9), (34.95, 75.19), (34.98, 75.24), (35.03, 75.28), (35.59, 75.62),
        (35.66, 75.67), (35.69, 75.71), (35.72, 75.8), (35.75, 76.15), (35.79, 76.22), (35.89, 76.27),
        (36.37, 76.3), (36.48, 76.27), (36.67, 76.19), (36.7, 76.15), (36.72, 76.1), (36.66, 75.87),
        (36.67, 75.82), (36.7, 75.77), (36.89, 75.59), (37.17, 75.41), (37.34, 75.17), (37.47, 75.04),
        (37.56, 74.83), (37.62, 74.78), (37.68, 74.77), (37.76, 74.8), (38.14, 75.09), (39.02, 75.6),
        (39.1, 75.62), (39.18, 75.6), (39.24, 75.55), (39.29, 75.48), (39.29, 75.36), (39.25, 75.29),
        (38.94, 75.01), (38.7, 74.71), (38.49, 74.55), (38.44, 74.48), (38.42, 74.43), (38.43, 74.37),
        (38.46, 74.29), (38.76, 73.92), (38.93, 73.47), (39.15, 73.08), (39.22, 72.82), (39.32, 72.65),
        (39.33, 72.57), (39.31, 72.48), (39.26, 72.38), (39.2, 72.31), (39.1, 72.27), (39.05, 72.28),
        (39.02, 72.31), (39.02, 72.35), (39.04, 72.5), (39.05, 72.59), (38.99, 72.82), (38.97, 73.05),
        (38.95, 73.14), (38.88, 73.27), (38.74, 73.47), (38.64, 73.65), (38.58, 73.71), (38.53, 73.74),
        (38.45, 73.75), (38.4, 73.73), (38.36, 73.7), (38.32, 73.62), (38.32, 73.54), (38.41, 73.36),
        (38.42, 73.31), (38.37, 73.15), (38.36, 73.07), (38.48, 72.86), (38.64, 72.45), (38.7, 72.38),
        (38.86, 72.26), (38.88, 72.23), (38.86, 72.19), (38.82, 72.15), (38.59, 72.02), (38.4, 71.84),
        (38.29, 71.8), (38.05, 71.78), (37.97, 71.79), (37.9, 71.83), (37.67, 72.06), (37.58, 72.34),
        (37.46, 72.51), (37.28, 72.85), (37.21, 73.11), (37.1, 73.27), (37.06, 73.5), (37.02, 73.57),
        (36.97, 73.59), (36.89, 73.59), (36.69, 73.46), (36.47, 73.4), (36.4, 73.36), (36.36, 73.28),
        (36.36, 73.2), (36.37, 73.08), (36.44, 72.88), (36.62, 72.68), (36.74, 72.52), (36.98, 72.35),
        (37, 72.31), (37.07, 72.08), (37.32, 71.67), (37.34, 71.56), (37.31, 71.3), (37.33, 71.16),
        (37.39, 71.09), (37.67, 70.92), (37.73, 70.83), (37.78, 70.6), (37.75, 70.4), (37.76, 70.31),
        (37.81, 70.25), (37.99, 70.14), (38.03, 70.07), (38.04, 69.96), (37.98, 69.82), (37.92, 69.76),
        (37.82, 69.69), (37.77, 69.67),
    ),
    (
        (38.17, 71.97), (38.23, 71.98), (38.28, 72.01), (38.38, 72.11), (38.42, 72.22), (38.41, 72.3),
        (38.38, 72.35), (38.31, 72.4), (38.15, 72.45), (38.1, 72.47), (37.98, 72.64), (37.71, 72.92),
        (37.69, 72.97), (37.63, 73.17), (37.6, 73.21), (37.53, 73.24), (37.48, 73.23), (37.44, 73.17),
        (37.43, 73.11), (37.44, 73.06), (37.59, 72.8), (37.69, 72.48), (37.74, 72.37), (37.94, 72.07),
        (38.03, 72.01),
    ),
    (
        (37.58, 73.99), (37.62, 74.01), (37.66, 74.05), (37.75, 74.21), (37.86, 74.35), (37.89, 74.42),
        (37.88, 74.45), (37.81, 74.45), (37.7, 74.41), (37.63, 74.36), (37.52, 74.22), (37.49, 74.14),
        (37.48, 74.06), (37.53, 74),
    ),
    (
        (36.21, 71.64), (36.28, 71.68), (36.33, 71.75), (36.37, 71.83), (36.41, 72.03), (36.54, 72.23),
        (36.56, 72.31), (36.53, 72.38), (36.24, 72.63), (36.11, 72.7), (35.96, 72.73), (35.87, 72.74),
        (35.67, 72.71), (35.56, 72.67), (35.42, 72.56), (35.32, 72.41), (35.14, 72.1), (35.11, 72.02),
        (35.12, 71.94), (35.15, 71.92), (35.19, 71.93), (35.34, 72.1), (35.41, 72.14), (35.65, 72.19),
        (35.73, 72.19), (35.78, 72.17), (35.85, 72.11), (36.02, 71.87), (36.15, 71.67),
    ),
    (
        (35.71, 71.29), (35.76, 71.34), (35.79, 71.43), (35.81, 71.54), (35.82, 71.69), (35.8, 71.78),
        (35.77, 71.83), (35.71, 71.88), (35.66, 71.89), (35.62, 71.87), (35.6, 71.8), (35.63, 71.53),
        (35.63, 71.38), (35.65, 71.31), (35.69, 71.28),
    ),
)


def _letter(out: List[str], char: str, left: float, right: float, top: float, base: float) -> None:
    """One letter, Inter Bold, its ink from ``left`` to ``right`` and its caps from ``top`` to ``base``."""
    x0, x1 = INTER_BOLD_X[char]
    size = (base - top) * INTER_UPEM / INTER_CAP
    sx = (right - left) / ((x1 - x0) * size / INTER_UPEM)
    tx = left - x0 * size / INTER_UPEM * sx
    out.append(f'<text x="0" y="0" transform="translate({fronts.f(tx)} {fronts.f(base)}) '
               f'scale({fronts.f(round(sx, 4))} 1)" font-size="{fronts.f(round(size, 4))}" '
               f'fill="{TDECK_BACK_INK}" font-weight="700">{char}</text>\n')


def _word(out: List[str], word: Word, shift: float = 0.0) -> None:
    top, base, letters, bars = word
    for char, left, right in letters:
        _letter(out, char, round(left + shift, 4), round(right + shift, 4), top, base)
    for x0, x1, y0, y1 in bars:
        x0, x1 = round(x0 + shift, 4), round(x1 + shift, 4)
        out.append(f'<rect x="{fronts.f(x0)}" y="{fronts.f(y0)}" width="{fronts.f(round(x1 - x0, 4))}" '
                   f'height="{fronts.f(round(y1 - y0, 4))}" fill="{TDECK_BACK_INK}"/>\n')


def _registered(out: List[str]) -> None:
    """The ® after LILYGO, Inter Bold's sign scaled to the ring the photo prints."""
    x0, x1, y0, y1 = TDECK_BASE_REG
    gx0, gx1, gy0, gy1 = INTER_BOLD_REG
    size = (y1 - y0) * INTER_UPEM / (gy1 - gy0)
    sx = (x1 - x0) / ((gx1 - gx0) * size / INTER_UPEM)
    tx = x0 - gx0 * size / INTER_UPEM * sx
    base = y1 + gy0 * size / INTER_UPEM
    out.append(f'<text x="0" y="0" transform="translate({fronts.f(tx)} {fronts.f(round(base, 4))}) '
               f'scale({fronts.f(round(sx, 4))} 1)" font-size="{fronts.f(round(size, 4))}" '
               f'fill="{TDECK_BACK_INK}" font-weight="700">®</text>\n')


def _mascot(out: List[str]) -> None:
    rings = ' '.join('M ' + ' L '.join(f'{fronts.f(round(x + TDECK_BADGE_SHIFT, 4))} {fronts.f(y)}'
                                       for x, y in ring) + ' Z'
                     for ring in TDECK_MASCOT)
    out.append(f'<path d="{rings}" fill="{TDECK_BACK_INK}" fill-rule="evenodd"/>\n')


def _frame_line(out: List[str]) -> None:
    points = ' L '.join(f'{fronts.f(x)} {fronts.f(y)}' for x, y in TDECK_FRAME_LINE)
    out.append(f'<path d="M {points}" fill="none" stroke="{TDECK_BACK_INK}" '
               f'stroke-width="{fronts.f(TDECK_FRAME_LINE_WIDTH)}" stroke-linecap="butt" '
               f'stroke-linejoin="miter"/>\n')


def append_tdeck_plus_back(out: List[str]) -> None:
    """The T-Deck Plus's four back prints, a legend group each, on four planes."""
    out.append(fronts.print_open('tdeck-frame', 'frame'))
    _word(out, TDECK_FRAME_WORD)
    out.append(fronts.LEGEND_CLOSE)
    out.append(fronts.print_open('tdeck-frame-line', 'frame-line'))
    _frame_line(out)
    out.append(fronts.LEGEND_CLOSE)
    out.append(fronts.print_open('tdeck-badge', 'badge'))
    _mascot(out)
    _word(out, TDECK_BADGE_WORD, TDECK_BADGE_SHIFT)
    out.append(fronts.LEGEND_CLOSE)
    out.append(fronts.print_open('lilygo-base', 'base'))
    _word(out, TDECK_BASE_WORD)
    _registered(out)
    out.append(fronts.LEGEND_CLOSE)
