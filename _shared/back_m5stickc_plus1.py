# SPDX-License-Identifier: MIT
"""What the M5StickC Plus 1.1 prints on its back: the label, in the back frame

The label covers the back from the top end down to just above the two
inserts: a row of eight pin names over the header, the ``M5STICK CPlus 1.1``
title, the colored fields of what is inside (BTN, BUZZER, IR, LED, ESP32,
LCD, MIC, the IMU, the PMIC, the RTC), the certification marks (FCC, CE,
WEEE, Japan's radio mark with its number), the serial speeds, the maker's
mark and the Grove port's pins, and PWR. Every size, place and color here is
measured on a straight-on product photo of the back (Pi Hut, 13.7 px/mm at
the label), its plane fitted on the two insert holes 16 mm apart and the
label's upright edges, and every ink is the photo's, taken where the print is
solid; every place is checked again on M5Stack's own straight-on photo of the
back (14.9 px/mm), and where the two read a different color the ink sits
between them. The I2C line reads ``SDA G21:SCL:G22/INT:G35`` on both photos,
its separators a pixel or two wide. ``emit_back_svg.py`` draws it; the model lays it on its ``back_label``
paper (``m5stickc-plus1/model/spec.json``, ``label_legends``).

Inter is the only face (``fonts/inter``). The label is set in a
condensed sans and a heavy display face (``M5STICK``, ``CPlus 1.1``,
``LCD``, ``MIC``, ``HY2.0-4P``); each run is Inter at the weight nearest the
print, sized to the photo's cap height and squeezed or widened to the
photo's ink width (``textLength``), so it covers what the print covers in a
lighter stroke.

Frame: the back frame (``emit_back_svg.py``), 1 mm a unit, x from the case's
left edge as seen from behind, y down from its top.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_front_svg as fronts  # noqa: E402

f = fronts.f

#: The label's paper, as the model's ``back_label`` solid lies under it: the
#: part over the header (rounded at the top end) and the part in the back's
#: recess, which is the wider (the photo's label is 21.0 mm across there).
PAPER_TOP = (1.62, 0.12, 22.38, 8.0, 1.2)
PAPER_BOTTOM = (1.5, 4.0, 22.5, 37.75, 0.4)
PAPER = "#fcfcfa"
#: How far inside the paper's edge a print that runs to the edge stops.
EDGE = 0.03

# Inks, each the photo's color where the print is solid.
PLUS1_INK = "#111111"  # black text, the GND field, the marks
PLUS1_WHITE = "#ffffff"  # text on the dark fields, the Espressif mark, the G33 cell
PLUS1_TEXT = "#3a3a3a"  # the small dark-grey text
PLUS1_MAKER = "#858585"  # the maker's lines, the R box, the rule, the key marks
PLUS1_ORANGE = "#c8320a"  # the left 5V field, the ESP32 tile, V OUT
PLUS1_RED = "#e64824"  # the right 5V field
PLUS1_LIGHT = "#e6e7e7"  # the G26 and G0 fields
PLUS1_GRAY = "#cbcbc9"  # the G36/G25 field, the BPS bar, the HY2.0-4P block
PLUS1_BAT = "#fa6665"  # the BAT field
PLUS1_YELLOW = "#fcce0f"  # 3V3, G32, SLEEP, the left 5V's arrow, OUT
PLUS1_BLUE = "#1d95da"  # the title, BTN G37
PLUS1_CYAN = "#7ad7ed"  # BTN G39
PLUS1_NAVY = "#003f5f"  # the two BTN fields' text
PLUS1_TAN = "#c48c4f"  # BUZZER
PLUS1_MAGENTA = "#e20e63"  # IR
PLUS1_SALMON = "#ef6968"  # LED
PLUS1_LCD = "#e8642f"  # the LCD word
PLUS1_MIC = "#0d4f82"  # the MIC word
PLUS1_BATTERY = "#9da09e"  # the BATTERY field and the bar beside it
PLUS1_BROWN = "#8a3a3a"  # D:G34/C:G0, the I2C pins
PLUS1_PWR = "#b0402a"  # PWR
PLUS1_IMU = "#c33161"  # the 6-Axis IMU field
PLUS1_GREEN = "#309963"  # the PMIC field
PLUS1_WAKE = "#bcca9d"  # WAKE
PLUS1_CUBE = "#3d6e8f"  # the maker's cube
PLUS1_RTC = "#118cd0"  # the RTC field
PLUS1_TAB = "#5f5b58"  # the two blocks at the title's ends

#: The pin row over the header: each field's left edge (and the last one's
#: right), its ink, as the photo divides the label (not on the header's
#: 2.54 mm pitch).
PIN_EDGES = (1.62, 4.19, 6.71, 9.43, 12.09, 14.69, 17.27, 19.92, 22.38)
PIN_FILLS = (PLUS1_INK, PLUS1_ORANGE, PLUS1_LIGHT, PLUS1_GRAY, PLUS1_LIGHT,
             PLUS1_BAT, PLUS1_YELLOW, PLUS1_RED)
PIN_BOTTOM = 6.3

#: Every text run: key, string, x, y, size, length, weight, rotation, ink.
#: Unrotated, (x, y) is the run's start on its baseline; rotated -90 (read
#: bottom to top), x is the baseline and y where the run starts. ``length``
#: is the run's drawn width (``textLength``), which puts its ink where the
#: photo's is.
PLUS1_TEXTS: Tuple[Tuple[str, str, float, float, float, float, int, int, str], ...] = (
    ('gnd', 'GND', 3.710, 5.969, 2.170, 5.218, 500, -90, PLUS1_WHITE),
    ('5v_l', '5V', 6.340, 5.807, 2.309, 2.719, 500, -90, PLUS1_WHITE),
    ('g26', 'G26', 8.960, 5.522, 2.279, 4.392, 500, -90, PLUS1_INK),
    ('g36', 'G36', 10.880, 6.131, 1.492, 2.931, 500, -90, PLUS1_INK),
    ('g25', 'G25', 11.740, 2.823, 1.519, 2.596, 500, -90, PLUS1_INK),
    ('g0', 'G0', 14.200, 4.786, 2.265, 2.921, 500, -90, PLUS1_INK),
    ('bat', 'BAT', 16.750, 5.347, 2.199, 4.188, 500, -90, PLUS1_WHITE),
    ('3v3', '3V3', 19.380, 5.298, 2.279, 4.093, 500, -90, PLUS1_INK),
    ('5v_r', '5V', 21.930, 5.737, 2.213, 2.719, 500, -90, PLUS1_WHITE),
    ('m5stick', 'M5STICK', 2.453, 9.800, 2.800, 9.170, 700, 0, PLUS1_WHITE),
    ('cplus', 'CPlus 1.1', 12.826, 9.800, 2.800, 8.740, 700, 0, PLUS1_INK),
    ('btn1', 'BTN', 3.188, 12.450, 1.443, 2.874, 500, 0, PLUS1_NAVY),
    ('g39', 'G39', 3.521, 13.550, 1.071, 2.158, 500, 0, PLUS1_NAVY),
    ('btn2', 'BTN', 6.887, 12.500, 1.512, 2.907, 500, 0, PLUS1_NAVY),
    ('g37', 'G37', 7.237, 13.550, 1.099, 2.213, 500, 0, PLUS1_NAVY),
    ('buzzer', 'BUZZER', 10.553, 12.320, 1.100, 4.257, 500, 0, PLUS1_WHITE),
    ('g2', 'G2', 11.893, 13.600, 1.194, 1.656, 500, 0, PLUS1_WHITE),
    ('ir', 'IR', 15.897, 12.320, 1.237, 0.952, 500, 0, PLUS1_WHITE),
    ('g9', 'G9', 15.681, 13.580, 1.166, 1.478, 500, 0, PLUS1_WHITE),
    ('led', 'LED', 18.355, 12.250, 1.223, 2.230, 500, 0, PLUS1_WHITE),
    ('g10', 'G10', 18.293, 13.520, 1.085, 2.240, 500, 0, PLUS1_WHITE),
    ('esp32', 'ESP32', 7.050, 15.800, 1.492, 3.879, 400, 0, PLUS1_WHITE),
    ('pico', 'PICO(4M)', 7.068, 17.060, 1.244, 4.904, 400, 0, PLUS1_WHITE),
    ('lcd', 'LCD', 15.170, 17.455, 2.380, 3.239, 700, -90, PLUS1_LCD),
    ('tft', '1.14 TFT,135x240', 15.445, 14.930, 0.773, 6.221, 400, 0, PLUS1_TEXT),
    ('st7789', 'ST7789V2', 15.409, 16.360, 1.546, 6.200, 400, 0, PLUS1_INK),
    ('pins', 'G15/13/23/18/5', 15.425, 17.340, 0.840, 6.551, 400, 0, PLUS1_INK),
    ('battery', 'BATTERY:', 2.725, 18.940, 0.962, 4.610, 500, 0, PLUS1_WHITE),
    ('mah', '120mAh', 3.253, 19.890, 0.963, 3.940, 500, 0, PLUS1_WHITE),
    ('mic', 'MIC', 15.170, 20.542, 2.380, 2.425, 700, -90, PLUS1_MIC),
    ('spm', 'SPM1423', 15.375, 19.300, 1.709, 6.454, 400, 0, PLUS1_INK),
    ('dg34', 'D:G34/C:G0', 15.473, 20.420, 1.103, 6.273, 400, 0, PLUS1_BROWN),
    ('model', 'Model Name: M5StickC Plus', 2.204, 21.040, 0.978, 11.033, 500, 0, PLUS1_TEXT),
    ('fccid', 'FCC-ID: 2AN3WM5STICKCPLUS', 2.211, 21.980, 0.814, 11.407, 500, 0, PLUS1_TEXT),
    ('axis', '6-Axis IMU', 16.278, 22.440, 0.932, 4.619, 400, 0, PLUS1_WHITE),
    ('mpu', 'MPU6886', 15.645, 23.680, 1.153, 5.686, 400, 0, PLUS1_WHITE),
    ('r', 'R', 5.950, 23.650, 0.810, 0.560, 400, 0, PLUS1_MAKER),
    ('r211', '211-200620', 7.236, 23.680, 1.302, 5.553, 400, 0, PLUS1_TEXT),
    ('sda', 'SDA G21:SCL:G22/INT:G35', 14.880, 30.761, 1.024, 9.425, 400, -90, PLUS1_BROWN),
    ('pmic', 'PMIC', 16.796, 25.860, 1.438, 3.581, 400, 0, PLUS1_WHITE),
    ('axp', 'AXP192', 16.532, 27.020, 1.383, 4.068, 400, 0, PLUS1_WHITE),
    ('rtc', 'RTC', 15.947, 29.220, 1.356, 2.378, 400, 0, PLUS1_WHITE),
    ('bm', 'BM8563', 15.311, 30.160, 0.963, 3.592, 400, 0, PLUS1_WHITE),
    ('sleep', 'SLEEP', 19.590, 28.630, 0.746, 2.197, 700, 0, PLUS1_INK),
    ('wake', 'WAKE', 19.673, 30.240, 0.660, 2.195, 700, 0, PLUS1_INK),
    ('bps', 'BPS', 13.321, 31.970, 0.936, 2.382, 500, 0, PLUS1_INK),
    ('baud', '1200-115200/250K/500K/750K/1.5M', 7.340, 33.070, 0.906, 14.494, 400, 0, PLUS1_TEXT),
    ('m5stack', 'M5STACK', 2.340, 34.750, 0.980, 4.720, 400, 0, PLUS1_TEXT),
    ('mk1', 'M5Stack', 3.236, 35.920, 0.665, 3.014, 400, 0, PLUS1_MAKER),
    ('mk2', 'Technology', 2.675, 36.600, 0.605, 4.094, 400, 0, PLUS1_MAKER),
    ('mk3', 'Co.,Ltd.', 3.420, 37.400, 0.700, 2.580, 400, 0, PLUS1_MAKER),
    ('hy', 'HY2.0-4P', 9.346, 34.460, 0.949, 5.537, 700, 0, PLUS1_INK),
    ('g', 'G', 8.454, 36.560, 1.800, 1.307, 500, 0, PLUS1_WHITE),
    ('v', 'V', 10.511, 35.960, 1.429, 1.108, 500, 0, PLUS1_WHITE),
    ('out', 'OUT', 10.453, 36.620, 0.570, 1.289, 700, 0, PLUS1_YELLOW),
    ('pwr', 'PWR', 17.183, 35.240, 1.814, 4.568, 400, 0, PLUS1_PWR),
    ('off', '(6S=OFF)', 16.947, 36.400, 1.072, 5.306, 400, 0, PLUS1_TEXT),
)
#: The Grove port's two signal names, set on a slant in their cells:
#: (string, center, size, length, ink).
PLUS1_SLANTED = (
    ('G32', (12.93, 35.87), 1.07, 1.85, PLUS1_INK),
    ('G33', (14.98, 35.88), 1.07, 1.85, PLUS1_TEXT),
)
PLUS1_SLANT_DEG = -45.0


def text_run(key_row: Tuple[str, str, float, float, float, float, int, int, str]) -> str:
    """One row of ``PLUS1_TEXTS`` as a ``<text>``."""
    _key, content, x, y, size, length, weight, rot, ink = key_row
    attrs = (f'font-size="{f(size)}" fill="{ink}" text-anchor="start" '
             f'font-weight="{weight}" textLength="{f(length)}" '
             'lengthAdjust="spacingAndGlyphs"')
    body = fronts._xml_escape(content)
    if rot:
        return (f'<text x="0" y="0" transform="translate({f(x)} {f(y)}) '
                f'rotate({f(rot)})" {attrs}>{body}</text>\n')
    return f'<text x="{f(x)}" y="{f(y)}" {attrs}>{body}</text>\n'


def slanted_run(content: str, center: Tuple[float, float], size: float,
                length: float, ink: str) -> str:
    """A run centered on ``center``, its cap height centered across, turned
    by ``PLUS1_SLANT_DEG`` (reading up and to the right)."""
    cx, cy = center
    return (f'<text x="0" y="{f(0.3637 * size)}" '
            f'transform="translate({f(cx)} {f(cy)}) rotate({f(PLUS1_SLANT_DEG)})" '
            f'font-size="{f(size)}" fill="{ink}" text-anchor="middle" '
            f'font-weight="500" textLength="{f(length)}" '
            f'lengthAdjust="spacingAndGlyphs">{fronts._xml_escape(content)}</text>\n')


def rect(x0: float, y0: float, x1: float, y1: float, fill: str, r: float = 0.0) -> str:
    return fronts.rounded_rect(x0, y0, x1 - x0, y1 - y0, r=r, fill=fill)


def line(points: List[Tuple[float, float]], ink: str, width: float,
         cap: str = "butt", join: str = "miter") -> str:
    d = " L ".join(f"{f(x)} {f(y)}" for x, y in points)
    return (f'<path d="M {d}" fill="none" stroke="{ink}" stroke-width="{f(width)}" '
            f'stroke-linecap="{cap}" stroke-linejoin="{join}"/>\n')


def polygon(points: List[Tuple[float, float]], fill: str) -> str:
    pts = " ".join(f"{f(x)},{f(y)}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}"/>\n'


def arc(cx: float, cy: float, r: float, start_deg: float, end_deg: float,
        ink: str, width: float) -> str:
    """A stroked circular arc about (cx, cy) from ``start_deg`` down to
    ``end_deg`` (angles on the page, y down: it turns counterclockwise as
    seen), the long way when it turns through more than half a circle."""
    a0, a1 = math.radians(start_deg), math.radians(end_deg)
    turn = (start_deg - end_deg) % 360
    return (f'<path d="M {f(cx + r * math.cos(a0))} {f(cy + r * math.sin(a0))} '
            f'A {f(r)} {f(r)} 0 {1 if turn > 180 else 0} 0 '
            f'{f(cx + r * math.cos(a1))} {f(cy + r * math.sin(a1))}" '
            f'fill="none" stroke="{ink}" stroke-width="{f(width)}"/>\n')


def outline_box(x0: float, y0: float, x1: float, y1: float, r: float,
                ink: str, width: float) -> str:
    """A rounded rectangle's outline, stroked on its center line."""
    return (f'<path d="M {f(x0 + r)} {f(y0)} H {f(x1 - r)} '
            f'A {f(r)} {f(r)} 0 0 1 {f(x1)} {f(y0 + r)} V {f(y1 - r)} '
            f'A {f(r)} {f(r)} 0 0 1 {f(x1 - r)} {f(y1)} H {f(x0 + r)} '
            f'A {f(r)} {f(r)} 0 0 1 {f(x0)} {f(y1 - r)} V {f(y0 + r)} '
            f'A {f(r)} {f(r)} 0 0 1 {f(x0 + r)} {f(y0)} Z" fill="none" '
            f'stroke="{ink}" stroke-width="{f(width)}"/>\n')


def append_pin_row(out: List[str]) -> None:
    """The eight fields over the header, the paper's top corners rounding
    the first and the last, and the two 5V arrows."""
    x0, top, x1, _, r = PAPER_TOP
    top, r = top + EDGE, r - EDGE
    left, right = x0 + EDGE, x1 - EDGE
    edges = (left,) + PIN_EDGES[1:-1] + (right,)
    for i, fill in enumerate(PIN_FILLS):
        a, b = edges[i], edges[i + 1]
        if i == 0:
            out.append(f'<path d="M {f(a)} {f(PIN_BOTTOM)} V {f(top + r)} '
                       f'A {f(r)} {f(r)} 0 0 1 {f(a + r)} {f(top)} H {f(b)} '
                       f'V {f(PIN_BOTTOM)} Z" fill="{fill}"/>\n')
        elif i == len(PIN_FILLS) - 1:
            out.append(f'<path d="M {f(a)} {f(PIN_BOTTOM)} V {f(top)} H {f(b - r)} '
                       f'A {f(r)} {f(r)} 0 0 1 {f(b)} {f(top + r)} '
                       f'V {f(PIN_BOTTOM)} Z" fill="{fill}"/>\n')
        else:
            out.append(rect(a, top, b, PIN_BOTTOM, fill))
    # the left 5V's arrow points up, out of the header; the right one's down
    out.append(polygon([(4.74, 1.87), (5.46, 0.96), (6.18, 1.87)], PLUS1_YELLOW))
    out.append(rect(5.085, 1.82, 5.835, 2.68, PLUS1_YELLOW))
    out.append(rect(20.795, 0.8, 21.545, 1.66, PLUS1_WHITE))
    out.append(polygon([(20.47, 1.6), (21.87, 1.6), (21.17, 2.5)], PLUS1_WHITE))
    # the slash between G36 and G25
    out.append(line([(9.77, 2.86), (11.78, 3.62)], PLUS1_INK, 0.11))


def append_title(out: List[str]) -> None:
    """``M5STICK`` white on a blue field cut on a slant, ``CPlus 1.1`` black
    on the paper, both inside one blue rounded frame."""
    x0, y0, x1, y1, r = 1.98, 6.64, 21.95, 10.92, 0.45
    out.append(f'<path d="M {f(x0 + r)} {f(y0)} H 11.88 L 12.95 {f(y1)} '
               f'H {f(x0 + r)} A {f(r)} {f(r)} 0 0 1 {f(x0)} {f(y1 - r)} '
               f'V {f(y0 + r)} A {f(r)} {f(r)} 0 0 1 {f(x0 + r)} {f(y0)} Z" '
               f'fill="{PLUS1_BLUE}"/>\n')
    w = 0.16
    out.append(outline_box(x0 + w / 2, y0 + w / 2, x1 - w / 2, y1 - w / 2,
                           r - w / 2, PLUS1_BLUE, w))
    # the grey block between each end of the frame and the paper's edge
    out.append(rect(1.58, 7.47, 1.97, 10.15, PLUS1_TAB, 0.08))
    out.append(rect(21.97, 7.42, 22.33, 10.12, PLUS1_TAB, 0.08))


def append_fields(out: List[str]) -> None:
    """The colored fields under the title, each a rounded rectangle."""
    for x0, y0, x1, y1, r, fill in (
            (2.86, 11.02, 6.40, 13.94, 0.3, PLUS1_CYAN),
            (6.72, 11.02, 10.10, 13.94, 0.3, PLUS1_BLUE),
            (10.42, 11.02, 15.08, 13.94, 0.3, PLUS1_TAN),
            (15.37, 11.02, 17.48, 13.94, 0.3, PLUS1_MAGENTA),
            (17.77, 11.02, 21.22, 13.94, 0.3, PLUS1_SALMON),
            (2.18, 14.22, 12.75, 17.71, 0.4, PLUS1_ORANGE),
            (2.12, 17.94, 8.15, 20.25, 0.35, PLUS1_BATTERY),
            (8.40, 18.30, 8.80, 19.75, 0.2, PLUS1_BATTERY),
            (15.15, 21.28, 21.93, 24.13, 0.4, PLUS1_IMU),
            (15.15, 24.49, 21.93, 27.40, 0.4, PLUS1_GREEN),
            (15.15, 27.70, 19.16, 30.61, 0.4, PLUS1_RTC),
            (19.45, 27.70, 22.00, 29.01, 0.25, PLUS1_YELLOW),
            (19.45, 29.37, 22.00, 30.61, 0.25, PLUS1_WAKE),
            (7.06, 31.05, 22.00, 31.99, 0.1, PLUS1_GRAY),
            (7.94, 33.45, 16.17, 37.17, 0.3, PLUS1_GRAY),
            (8.18, 34.75, 10.02, 36.86, 0.0, PLUS1_INK),
            (10.12, 34.75, 12.00, 36.86, 0.0, PLUS1_ORANGE),
            (12.10, 34.75, 14.00, 36.86, 0.0, PLUS1_YELLOW),
            (14.10, 34.75, 15.92, 36.86, 0.0, PLUS1_WHITE)):
        out.append(rect(x0, y0, x1, y1, fill, r))


#: Espressif's mark, the white on the ESP32 tile: its thin outer arc, the
#: banded body cut by three red arcs about the dot, and the dot in its red
#: ring, as the rings of one even-odd shape. The Plus SE's traced mark
#: (``back_plus_se.ESPRESSIF_RINGS``) placed on this label by a similarity
#: fitted to both photos at once (least squares on their blurred green
#: inside the mark's disc: scale 1.0006, turned -0.14 deg; each photo alone
#: places it within 0.02 mm of the other).
ESPRESSIF_RINGS: Tuple[Tuple[Tuple[float, float], ...], ...] = (
    ((3.460, 15.487), (3.411, 15.565), (3.367, 15.667), (3.345, 15.770), (3.341, 15.898),
     (3.367, 16.026), (3.458, 16.178), (3.573, 16.282), (3.776, 16.374), (4.054, 16.433),
     (4.181, 16.506), (4.257, 16.592), (4.284, 16.636), (4.331, 16.764), (4.342, 16.891),
     (4.330, 17.019), (4.259, 17.199), (4.285, 17.254), (4.361, 17.321), (4.488, 17.382),
     (4.614, 17.407), (4.639, 17.401), (4.671, 17.377), (4.766, 17.172), (4.804, 16.992),
     (4.807, 16.762), (4.765, 16.558), (4.640, 16.329), (4.536, 16.209), (4.433, 16.115),
     (4.333, 16.049), (4.205, 15.989), (4.104, 15.961), (3.978, 15.943), (3.875, 15.902),
     (3.842, 15.870), (3.833, 15.820), (3.850, 15.785), (3.880, 15.769), (3.977, 15.761),
     (4.204, 15.810), (4.407, 15.895), (4.614, 16.047), (4.763, 16.223), (4.840, 16.333),
     (4.877, 16.405), (4.946, 16.584), (4.986, 16.788), (4.990, 16.890), (4.938, 17.197),
     (4.942, 17.257), (4.968, 17.288), (5.029, 17.324), (5.172, 17.358), (5.272, 17.342),
     (5.374, 17.287), (5.409, 17.222), (5.430, 17.120), (5.443, 16.787), (5.422, 16.556),
     (5.351, 16.327), (5.263, 16.122), (5.193, 16.008), (5.065, 15.842), (4.838, 15.626),
     (4.660, 15.505), (4.457, 15.399), (4.203, 15.316), (4.077, 15.298), (3.848, 15.293),
     (3.773, 15.304), (3.595, 15.372), (3.535, 15.411)),
    ((3.856, 14.874), (3.829, 14.924), (3.817, 14.976), (3.817, 15.026), (3.835, 15.079),
     (3.900, 15.113), (4.177, 15.152), (4.356, 15.199), (4.634, 15.305), (4.863, 15.444),
     (5.041, 15.586), (5.192, 15.743), (5.297, 15.866), (5.449, 16.122), (5.528, 16.300),
     (5.558, 16.404), (5.590, 16.582), (5.620, 16.838), (5.638, 16.888), (5.677, 16.908),
     (5.804, 16.906), (5.854, 16.892), (5.880, 16.874), (6.001, 16.734), (6.054, 16.607),
     (6.053, 16.504), (6.011, 16.299), (5.979, 16.198), (5.882, 15.967), (5.761, 15.737),
     (5.627, 15.533), (5.520, 15.392), (5.317, 15.197), (5.090, 15.035), (4.683, 14.812),
     (4.509, 14.745), (4.329, 14.697), (4.152, 14.691), (4.076, 14.711), (4.003, 14.746),
     (3.923, 14.803)),
    ((3.190, 15.336), (3.096, 15.694), (3.085, 15.822), (3.086, 16.103), (3.097, 16.255),
     (3.125, 16.383), (3.241, 16.690), (3.379, 16.920), (3.544, 17.124), (3.628, 17.200),
     (3.830, 17.354), (4.090, 17.505), (4.386, 17.614), (4.690, 17.653), (4.868, 17.656),
     (5.046, 17.639), (5.299, 17.584), (5.501, 17.504), (5.678, 17.418), (5.789, 17.349),
     (5.873, 17.271), (5.938, 17.194), (5.948, 17.143), (5.931, 17.110), (5.904, 17.095),
     (5.880, 17.092), (5.828, 17.117), (5.754, 17.187), (5.525, 17.344), (5.221, 17.464),
     (4.892, 17.514), (4.690, 17.514), (4.488, 17.492), (4.208, 17.407), (4.032, 17.333),
     (3.905, 17.259), (3.848, 17.199), (3.842, 17.175), (3.855, 17.148), (3.954, 17.111),
     (4.005, 17.079), (4.082, 16.998), (4.106, 16.943), (4.111, 16.867), (4.100, 16.791),
     (4.070, 16.739), (3.996, 16.663), (3.953, 16.643), (3.852, 16.629), (3.801, 16.633),
     (3.750, 16.653), (3.700, 16.688), (3.655, 16.740), (3.587, 16.893), (3.575, 16.903),
     (3.550, 16.903), (3.524, 16.888), (3.412, 16.716), (3.351, 16.588), (3.247, 16.255),
     (3.220, 16.050), (3.225, 15.667), (3.261, 15.515), (3.378, 15.233), (3.439, 15.155),
     (3.625, 14.875), (3.625, 14.823), (3.594, 14.786), (3.570, 14.779), (3.544, 14.785),
     (3.493, 14.821), (3.341, 15.029)),
    ((4.655, 14.539), (4.644, 14.565), (4.658, 14.611), (4.683, 14.634), (5.012, 14.790),
     (5.186, 14.895), (5.343, 15.004), (5.517, 15.150), (5.672, 15.327), (5.936, 15.687),
     (6.104, 16.043), (6.155, 16.071), (6.206, 16.046), (6.220, 16.019), (6.225, 15.966),
     (6.221, 15.787), (6.205, 15.673), (6.181, 15.584), (6.015, 15.200), (5.938, 15.073),
     (5.852, 14.971), (5.737, 14.869), (5.595, 14.767), (5.291, 14.592), (5.114, 14.540),
     (4.947, 14.512), (4.809, 14.501), (4.682, 14.517)),
)


def append_espressif(out: List[str]) -> None:
    """Espressif's mark on the ESP32 tile, white."""
    d = " ".join("M " + " L ".join(f"{f(x)} {f(y)}" for x, y in ring) + " Z"
                 for ring in ESPRESSIF_RINGS)
    out.append(f'<path d="{d}" fill="{PLUS1_WHITE}" fill-rule="evenodd"/>\n')


def append_marks(out: List[str]) -> None:
    """FCC, Japan's radio mark and its number, CE, the crossed-out bin and
    its bar, the maker's cube, the two button marks."""
    # FCC: an F, then two Cs one inside the other, open to the right
    out.append(line([(10.84, 18.27), (9.79, 18.27), (9.79, 20.02)], PLUS1_INK, 0.25))
    out.append(line([(9.79, 19.08), (10.68, 19.08)], PLUS1_INK, 0.24))
    out.append(arc(11.75, 19.05, 0.88, -42, -318, PLUS1_INK, 0.22))
    out.append(arc(11.75, 19.07, 0.46, -52, -308, PLUS1_INK, 0.2))
    # Japan's technical-conformity mark: a ring broken on its right by a
    # lightning stroke across its upper half, over two bars and a stem
    gx, gy, ring = 4.32, 23.37, 1.04
    start, end = math.radians(-24), math.radians(25)
    bolt = [(gx - 1.05, gy - 0.305), (gx - 0.034, gy - 0.50), (gx + 0.12, gy - 0.14),
            (gx + ring * math.cos(start), gy + ring * math.sin(start))]
    path = " L ".join(f"{f(px)} {f(py)}" for px, py in bolt)
    out.append(f'<path d="M {path} A {f(ring)} {f(ring)} 0 1 0 '
               f'{f(gx + ring * math.cos(end))} {f(gy + ring * math.sin(end))}" '
               f'fill="none" stroke="{PLUS1_INK}" stroke-width="0.14" '
               'stroke-linejoin="round"/>\n')
    out.append(f'<path d="M {f(gx - 0.59)} {f(gy + 0.18)} H {f(gx + 0.62)} '
               f'M {f(gx - 0.59)} {f(gy + 0.48)} H {f(gx + 0.62)} '
               f'M {f(gx + 0.03)} {f(gy + 0.48)} V {f(gy + 0.80)}" fill="none" '
               f'stroke="{PLUS1_INK}" stroke-width="0.12"/>\n')
    out.append(outline_box(5.62, 22.80, 6.90, 23.90, 0.12, PLUS1_MAKER, 0.12))
    # CE: two arcs of one radius, the E's middle bar
    out.append(arc(4.58, 28.1, 2.47, -86, -274, PLUS1_INK, 0.56))
    out.append(arc(9.27, 28.1, 2.47, -84, -276, PLUS1_INK, 0.56))
    out.append(rect(7.02, 27.63, 8.94, 28.43, PLUS1_INK))
    # WEEE: the wheelie bin (its lid and handle, the ear on its right, the
    # body on a foot and a wheel), crossed out, over its bar
    out.append(line([(9.33, 23.98), (13.90, 28.77)], PLUS1_INK, 0.13))
    out.append(line([(14.18, 23.88), (9.45, 28.80)], PLUS1_INK, 0.13))
    out.append(line([(10.70, 24.73), (11.0, 24.40), (12.73, 24.40), (13.13, 24.70)],
                    PLUS1_INK, 0.12))
    out.append(outline_box(11.53, 24.33, 12.20, 24.60, 0.12, PLUS1_INK, 0.1))
    out.append(line([(10.63, 24.80), (13.17, 24.80)], PLUS1_INK, 0.14))
    out.append(outline_box(12.72, 25.14, 13.10, 25.44, 0.08, PLUS1_INK, 0.12))
    out.append(line([(10.77, 24.86), (11.06, 28.33)], PLUS1_INK, 0.14))
    out.append(line([(11.03, 28.10), (12.28, 28.10)], PLUS1_INK, 0.14))
    out.append(line([(12.72, 24.86), (12.47, 27.62)], PLUS1_INK, 0.14))
    out.append(rect(11.50, 25.60, 12.32, 25.86, PLUS1_INK))
    out.append(fronts.circle(12.58, 27.93, 0.30, stroke=PLUS1_INK, stroke_w=0.13))
    out.append(fronts.circle(12.58, 27.93, 0.10, fill=PLUS1_INK))
    out.append(rect(9.75, 29.80, 13.77, 30.88, PLUS1_INK))
    # the maker's cube, its top face's left and bottom corners turned a
    # little left of its top corner, as both photos print it; and the dark 5
    # lying on that face: Inter Regular, its axes and place an affine fitted
    # to the 5 both photos print (M5Stack's own 5 is not Inter's)
    out.append(line([(3.31, 31.91), (4.77, 31.28), (6.23, 31.91), (4.73, 32.50), (3.31, 31.91)],
                    PLUS1_CUBE, 0.12, join="round"))
    out.append(line([(3.25, 32.14), (3.25, 32.90), (4.73, 33.50), (6.20, 32.90), (6.20, 32.02)],
                    PLUS1_CUBE, 0.12, join="round"))
    out.append('<text x="0" y="0.3637" font-size="1" font-weight="400" text-anchor="middle" '
               'transform="matrix(1.3613 -0.9236 1.44 0.4228 4.736 31.899)" '
               f'fill="{PLUS1_INK}">5</text>\n')
    out.append(rect(2.00, 35.21, 7.50, 35.27, PLUS1_MAKER))
    # the marks pointing at the two side keys
    out.append(line([(1.84, 11.52), (2.17, 12.04), (2.72, 12.56)], PLUS1_MAKER, 0.12,
                    join="round"))
    out.append(line([(20.92, 36.74), (21.68, 37.42)], PLUS1_MAKER, 0.11))


def append_m5stickc_plus1_back(out: List[str]) -> None:
    """The paper, then the label's one legend group on the plane ``label``."""
    for x0, y0, x1, y1, r in (PAPER_TOP, PAPER_BOTTOM):
        out.append(rect(x0, y0, x1, y1, PAPER, r))
    out.append(fronts.print_open("back-label", "label"))
    append_pin_row(out)
    append_title(out)
    append_fields(out)
    append_espressif(out)
    append_marks(out)
    for row in PLUS1_TEXTS:
        out.append(text_run(row))
    for content, center, size, length, ink in PLUS1_SLANTED:
        out.append(slanted_run(content, center, size, length, ink))
    out.append(fronts.LEGEND_CLOSE)
