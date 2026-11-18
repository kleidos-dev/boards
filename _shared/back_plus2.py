# SPDX-License-Identifier: MIT
"""The M5StickC Plus2's back label, drawn for ``emit_back_svg.py``

The label is the sticker in the back shell's recess, 20.8 x 37.18 mm, its
paper the model's ``back_label`` solid, its top 1.07 mm under the case's top
end. Everything printed on it is one legend
group on the plane ``label``, in the back frame (``board_faces.py``: 1 mm a
unit, x across from the case's left edge as seen from behind, y down from its
top), so the builder lays it on the label's face with nothing typed twice.

Every position and size was measured on M5Stack's straight-on back photo
(the Pi Hut's copy of it, 800 px, 13.8 px/mm across the label) in the
measured frame: the photo registered on the label's four edges as the paper
x 1.6..22.4, y 1.4..38.25. The photo's paper is 1.787 times as long as it is
wide, and the black header band above it is 1.07 mm deep, so the paper the
model holds keeps the frame's width and bottom and starts 1.07 mm under the
top end; one transform inside the group stretches the frame onto it (0.9 %
down its length). Each ink was sampled on the photo and white-balanced so the
photo's paper is the model's. The label's face is a condensed grotesque; Inter
is the only face the builder has, so each run is drawn at the photo's cap height
and squeezed (``textLength``) to the length it prints at: the letters are
Inter's, wider-set and rounder than the label's, and the runs cover what the
label's runs cover.

What the label prints, top to bottom: the HAT header's eight pin cells (GND,
5V out, G26, G36/G25, G0, BAT, 3V3, 5V in), the M5StickC PLUS2 banner, the
BTN G39 / BTN G37 / BUZZER G2 / IR G19 / LED G19 chips, the ESP32-PICO-V3-02
block with Espressif's mark, the LCD (ST7789V2) and microphone (SPM1423)
lines, the 200 mAh battery, FCC, the model name and FCC ID, Japan's radio mark
and Giteki number, CE, the WEEE bin, the IMU (MPU6886) and RTC (BM8563) blocks,
the SLEEP / WAKE / HOLD tags, the I2C pins, M5Stack's cube and maker's lines,
the HY2.0-4P port's four cells, and the power key's PWR (6S=OFF).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_front_svg as fronts  # noqa: E402

f = fronts.f

#: The label's paper in the measured frame, where every position below is
#: given, its corners r 0.3. Prints that reach its edge stop 0.02 mm inside
#: it, so every one has paper under it.
PAPER = (1.6, 1.4, 22.4, 38.25)
PAPER_R = 0.3
EDGE = 0.02
#: The paper as the model holds it: the model's ``back_label`` prism mirrored
#: into the back frame (x 1.6..22.4, y 1.07..38.25).
MODEL_PAPER = (1.6, 1.07, 22.4, 38.25)
#: The measured frame onto the model's paper: y stretched about the paper's
#: bottom edge, x as it is.
STRETCH_Y = (MODEL_PAPER[3] - MODEL_PAPER[1]) / (PAPER[3] - PAPER[1])
SHIFT_Y = MODEL_PAPER[3] - STRETCH_Y * PAPER[3]

# Inks, sampled on the photo and white-balanced (its paper #fdfdfb is the
# model's #eeeeea).
BLACK = "#141413"  # text, the GND and G cells, CE, FCC, the WEEE bin and bar
GRAY = "#4a4a48"  # the small print: TFT line, LCD pins, ADC, I2C, maker, G35
WHITE = "#eeeeea"  # white print on a field (and the G33 cell): the paper's color
RED = "#c8300a"  # the 5V cells, the ESP32 block, the port's 5V OUT cell
ORANGE = "#e3551d"  # LCD
SALMON = "#ec5957"  # BAT, the LED chip
YELLOW = "#ecc205"  # 3V3, the banner, the up arrow, SLEEP, G32
LIGHT = "#dadcd9"  # the G26 and G0 cells
SILVER = "#c1c2bf"  # the G36/G25 cell, the HY2.0-4P block
CYAN = "#63d3e7"  # BTN G39
BLUE = "#0594de"  # BTN G37, RTC
NAVY = "#01304d"  # the BTN chips' text, BUTTON.B / BUTTON.A
BROWN = "#bd813e"  # BUZZER
MAGENTA = "#cd1457"  # IR, the IMU block
GREEN = "#049a40"  # the battery
MIC_BLUE = "#0a4c80"  # MIC
TEXT_RED = "#b8262b"  # PWR, D: G34/C: G0
OLIVE = "#a5ae85"  # WAKE, HOLD
AMBER = "#f0a247"  # the port's OUT
CUBE_BLUE = "#3c7fb4"  # M5Stack's cube

#: The pin cells' edges across, as the back shows them (GND on the left),
#: and their top and bottom.
CELL_X = (PAPER[0] + EDGE, 4.30, 6.87, 9.45, 12.05, 14.70, 17.30, 19.90, PAPER[2] - EDGE)
CELL_Y = (PAPER[1] + EDGE, 7.30)
CELL_INKS = (BLACK, RED, LIGHT, SILVER, LIGHT, SALMON, YELLOW, RED)

# Horizontal runs: (text, x of the run's start, baseline y, size, drawn
# length, weight, ink).
RUNS: Tuple[Tuple[str, float, float, float, float, str, str], ...] = (
    ("M5StickC", 2.92, 10.51, 2.26, 10.12, "700", BLACK),
    ("PLUS2", 14.66, 10.44, 2.16, 6.56, "700", BLACK),
    ("BTN", 3.42, 13.37, 1.38, 2.62, "700", NAVY),
    ("G39", 3.42, 14.48, 1.3, 2.62, "700", NAVY),
    ("BTN", 7.11, 13.37, 1.38, 2.7, "700", NAVY),
    ("G37", 7.11, 14.48, 1.3, 2.62, "700", NAVY),
    ("BUZZER", 10.58, 13.3, 1.09, 4.33, "700", WHITE),
    ("G2", 12.03, 14.45, 1.09, 1.45, "700", WHITE),
    ("IR", 16.08, 13.23, 1.18, 1.36, "700", WHITE),
    ("G19", 15.58, 14.45, 1.12, 2.34, "700", WHITE),
    ("LED", 18.83, 13.23, 1.18, 2.49, "700", WHITE),
    ("G19", 18.83, 14.45, 1.12, 2.48, "700", WHITE),
    ("BUTTON.B", 3.03, 15.38, 0.55, 3.35, "700", NAVY),
    ("BUTTON.A", 6.71, 15.38, 0.55, 3.42, "700", NAVY),
    ("ESP32-", 5.83, 17.31, 1.28, 3.45, "600", WHITE),
    ("PICO-V3-02", 5.83, 18.52, 1.2, 6.58, "600", WHITE),
    ("1.14 TFT,135X240", 15.12, 16.42, 0.7, 6.95, "400", GRAY),
    ("ST7789V2", 15.12, 17.95, 1.92, 6.95, "400", BLACK),
    ("G27/15/14/13/12/5", 15.16, 18.9, 0.8, 6.98, "400", GRAY),
    ("BATTERY", 2.86, 20.39, 0.98, 4.38, "700", WHITE),
    ("200mAh", 2.96, 21.37, 0.98, 4.2, "700", WHITE),
    ("BAT/2 ADC:G38", 2.0, 22.45, 0.76, 6.2, "600", GRAY),
    ("SPM1423", 15.12, 20.66, 1.57, 6.52, "400", BLACK),
    ("D: G34/C: G0", 15.13, 21.88, 1.18, 6.5, "400", TEXT_RED),
    ("Model Name: StickC PLUS2", 4.24, 23.6, 1.17, 15.67, "400", BLACK),
    ("FCC ID:2AN3WSTICKCPLUSV11", 2.78, 24.8, 1.2, 18.5, "400", BLACK),
    ("211-230606", 7.2, 26.44, 1.2, 6.35, "400", BLACK),
    ("6-Axis IMU", 15.62, 26.64, 1.1, 5.98, "600", WHITE),
    ("MPU6886", 15.56, 27.79, 1.13, 6.05, "600", WHITE),
    ("RTC", 15.95, 30.13, 1.35, 2.38, "600", WHITE),
    ("BM8563", 15.41, 30.95, 0.91, 3.54, "600", WHITE),
    ("SLEEP", 19.63, 29.31, 0.69, 2.3, "800", BLACK),
    ("WAKE", 19.63, 30.46, 0.69, 2.22, "800", BLACK),
    ("G35", 19.82, 31.6, 0.96, 1.86, "400", GRAY),
    ("HOLD", 19.7, 32.6, 0.69, 2.16, "800", BLACK),
    ("SDA: G21", 15.07, 32.67, 1.07, 4.12, "400", GRAY),
    ("SCL: G22", 15.07, 33.68, 1.07, 4.12, "400", GRAY),
    ("G4", 20.08, 33.63, 0.96, 1.33, "400", GRAY),
    ("M5STACK", 2.93, 36.38, 0.88, 3.93, "500", GRAY),
    ("M5Stack", 3.62, 37.1, 0.58, 2.57, "800", BLACK),
    ("Technology Co.,Ltd.", 1.95, 37.62, 0.57, 5.9, "800", BLACK),
    ("HY2.0-4P", 9.42, 35.14, 1.27, 5.43, "600", BLACK),
    ("G", 8.53, 36.96, 1.76, 1.27, "600", WHITE),
    ("5V", 10.15, 36.5, 1.51, 1.86, "700", WHITE),
    ("OUT", 10.3, 37.19, 0.74, 1.6, "800", AMBER),
    ("PWR", 17.22, 35.32, 1.97, 4.12, "400", TEXT_RED),
    ("(6S=OFF)", 16.97, 36.3, 1.05, 4.72, "400", GRAY),
    ("BUTTON.C", 17.18, 37.18, 0.89, 4.24, "700", BLACK),
    ("G35", 18.48, 37.89, 0.88, 1.62, "400", GRAY),
)

# Runs reading bottom to top (the pin cells, LCD, MIC): (text, x of the
# baseline, y where the run starts, size, drawn length, weight, ink).
UP_RUNS: Tuple[Tuple[str, float, float, float, float, str, str], ...] = (
    ("GND", 3.8, 6.64, 2.08, 4.5, "500", WHITE),
    ("5V", 6.33, 6.57, 1.98, 2.42, "500", WHITE),
    ("G26", 9.0, 6.3, 2.08, 3.8, "400", BLACK),
    ("G0", 14.2, 5.72, 2.08, 2.72, "400", BLACK),
    ("BAT", 16.73, 6.2, 1.98, 3.62, "500", WHITE),
    ("3V3", 19.4, 6.14, 2.08, 3.56, "400", BLACK),
    ("5V", 21.93, 6.57, 2.09, 2.49, "500", WHITE),
    ("G36", 10.85, 7.19, 1.57, 2.73, "400", BLACK),
    ("G25", 11.9, 4.24, 1.51, 2.63, "400", BLACK),
    ("LCD", 14.85, 19.08, 2.48, 3.3, "800", ORANGE),
    ("MIC", 14.85, 22.0, 2.48, 2.56, "800", MIC_BLUE),
)

# The port's two right cells print their pin names at an angle: (text, x and
# y of the run's middle, its angle, size, length).
SLANT_RUNS = (("G32", 13.09, 36.25, -45.0, 1.15, 2.0),
              ("G33", 15.11, 36.21, -45.0, 1.15, 2.0))

# Fields: (x0, y0, x1, y1, corner radius, ink).
FIELDS = (
    (3.01, 12.02, 6.48, 14.9, 0.25, CYAN),
    (6.69, 12.02, 10.16, 14.9, 0.25, BLUE),
    (10.38, 12.02, 15.14, 14.9, 0.25, BROWN),
    (15.36, 12.02, 18.1, 14.9, 0.25, MAGENTA),
    (18.32, 12.02, 21.79, 14.9, 0.25, SALMON),
    (2.07, 15.73, 12.76, 19.24, 0.35, RED),
    (2.07, 19.45, 8.04, 21.67, 0.3, GREEN),
    (8.35, 19.8, 8.8, 21.25, 0.12, GREEN),
    (15.14, 25.38, 22.0, 28.31, 0.3, MAGENTA),
    (15.14, 28.53, 19.19, 31.6, 0.3, BLUE),
    (19.48, 28.53, 22.0, 29.53, 0.05, YELLOW),
    (19.55, 29.89, 22.0, 30.9, 0.05, OLIVE),
    (19.48, 31.89, 22.0, 32.95, 0.05, OLIVE),
    (8.0, 34.02, 16.19, 37.68, 0.35, SILVER),
    (8.22, 35.29, 10.0, 37.27, 0.0, BLACK),
    (10.09, 35.29, 12.0, 37.27, 0.0, RED),
    (12.12, 35.29, 14.08, 37.27, 0.0, YELLOW),
    (14.14, 35.29, 15.99, 37.27, 0.0, WHITE),
    (10.45, 32.42, 14.42, 33.37, 0.0, BLACK),
    (PAPER[0] + EDGE + 0.03, 8.37, 2.07, 11.0, 0.0, SILVER),
    (22.1, 8.37, PAPER[2] - EDGE, 11.0, 0.0, SILVER),
)

#: The banner: a yellow band with rounded ends, the white panel on its right
#: cut out of it, its left edge leaning to the right going down.
BANNER = (2.14, 7.65, 22.0, 11.66, 0.45)
BANNER_PANEL = ((13.42, 7.92), (21.76, 7.92), (21.76, 11.34), (14.22, 11.34))
BANNER_PANEL_R = 0.3


def run(content: str, x: float, y: float, size: float, length: float,
        weight: str, ink: str) -> str:
    return fronts.text(x, y, content, size=size, fill=ink, anchor="start",
                       weight=weight, length=length)


def run_up(content: str, x: float, y: float, size: float, length: float,
           weight: str, ink: str) -> str:
    return fronts.cardputer_label_up(x, y, content, size=size, fill=ink,
                                     weight=weight, length=length)


def run_slant(content: str, cx: float, cy: float, angle: float, size: float,
              length: float) -> str:
    """A run centered on (cx, cy), its cap height's middle on that point."""
    body = fronts.text(cx, cy + 0.3635 * size, content, size=size, fill=BLACK,
                       anchor="middle", length=length)
    return fronts.cardputer_rotated(angle, cx, cy, body)


def rounded_path(x0: float, y0: float, x1: float, y1: float, r: float) -> str:
    """Path data of a rounded rectangle, clockwise on the page."""
    if r <= 0:
        return f"M {f(x0)} {f(y0)} H {f(x1)} V {f(y1)} H {f(x0)} Z"
    return (f"M {f(x0 + r)} {f(y0)} H {f(x1 - r)} "
            f"A {f(r)} {f(r)} 0 0 1 {f(x1)} {f(y0 + r)} V {f(y1 - r)} "
            f"A {f(r)} {f(r)} 0 0 1 {f(x1 - r)} {f(y1)} H {f(x0 + r)} "
            f"A {f(r)} {f(r)} 0 0 1 {f(x0)} {f(y1 - r)} V {f(y0 + r)} "
            f"A {f(r)} {f(r)} 0 0 1 {f(x0 + r)} {f(y0)} Z")


def field(x0: float, y0: float, x1: float, y1: float, r: float, ink: str) -> str:
    return f'<path d="{rounded_path(x0, y0, x1, y1, r)}" fill="{ink}"/>\n'


def cells() -> List[str]:
    """The pin cells, the two outer ones rounded with the paper's corners."""
    out = []
    top, bottom = CELL_Y
    r = PAPER_R - EDGE
    for i, ink in enumerate(CELL_INKS):
        x0, x1 = CELL_X[i], CELL_X[i + 1]
        if i == 0:
            d = (f"M {f(x0)} {f(bottom)} V {f(top + r)} "
                 f"A {f(r)} {f(r)} 0 0 1 {f(x0 + r)} {f(top)} H {f(x1)} V {f(bottom)} Z")
        elif i == len(CELL_INKS) - 1:
            d = (f"M {f(x0)} {f(top)} H {f(x1 - r)} "
                 f"A {f(r)} {f(r)} 0 0 1 {f(x1)} {f(top + r)} V {f(bottom)} H {f(x0)} Z")
        else:
            d = f"M {f(x0)} {f(top)} H {f(x1)} V {f(bottom)} H {f(x0)} Z"
        out.append(f'<path d="{d}" fill="{ink}"/>\n')
    return out


def arrow(cx: float, tip: float, neck: float, tail: float, head_w: float,
          stem_w: float, ink: str) -> str:
    """A block arrow along y: its tip at ``tip``, the head's back at ``neck``,
    the stem's end at ``tail``."""
    pts = [(cx, tip), (cx + head_w / 2, neck), (cx + stem_w / 2, neck),
           (cx + stem_w / 2, tail), (cx - stem_w / 2, tail),
           (cx - stem_w / 2, neck), (cx - head_w / 2, neck)]
    return fronts.cardputer_polygon(pts, ink)


def banner() -> str:
    """The banner band, its white panel left as paper (even-odd)."""
    x0, y0, x1, y1, r = BANNER
    pr = BANNER_PANEL_R
    (a, top), (b, _), (_, bottom), (c, _) = BANNER_PANEL
    panel = (f"M {f(a)} {f(top)} H {f(b - pr)} "
             f"A {f(pr)} {f(pr)} 0 0 1 {f(b)} {f(top + pr)} V {f(bottom - pr)} "
             f"A {f(pr)} {f(pr)} 0 0 1 {f(b - pr)} {f(bottom)} H {f(c)} Z")
    return (f'<path d="{rounded_path(x0, y0, x1, y1, r)} {panel}" '
            f'fill="{YELLOW}" fill-rule="evenodd"/>\n')


def stroke(points: Sequence[Tuple[float, float]], ink: str, width: float,
           join: str = "round", cap: str = "butt") -> str:
    d = " L ".join(f"{f(x)} {f(y)}" for x, y in points)
    return (f'<path d="M {d}" fill="none" stroke="{ink}" stroke-width="{f(width)}" '
            f'stroke-linejoin="{join}" stroke-linecap="{cap}"/>\n')


def arc(cx: float, cy: float, r: float, a0: float, a1: float, ink: str,
        width: float) -> str:
    """A stroked arc about (cx, cy) from ``a0`` to ``a1`` degrees, clockwise on
    the page (the angle grows towards +y)."""
    p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
    p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return (f'<path d="M {f(p0[0])} {f(p0[1])} A {f(r)} {f(r)} 0 {large} 1 '
            f'{f(p1[0])} {f(p1[1])}" fill="none" stroke="{ink}" '
            f'stroke-width="{f(width)}"/>\n')


def ring_cut(cx: float, cy: float, outer: float, inner: float, cut_x: float,
             ink: str) -> str:
    """The part of a ring left of ``x = cut_x``: CE's C and the E's arc."""
    def ang(r: float) -> float:
        return math.degrees(math.acos((cut_x - cx) / r))
    ao, ai = ang(outer), ang(inner)
    po0 = (cut_x, cy - outer * math.sin(math.radians(ao)))
    po1 = (cut_x, cy + outer * math.sin(math.radians(ao)))
    pi0 = (cut_x, cy + inner * math.sin(math.radians(ai)))
    pi1 = (cut_x, cy - inner * math.sin(math.radians(ai)))
    return (f'<path d="M {f(po0[0])} {f(po0[1])} '
            f'A {f(outer)} {f(outer)} 0 1 0 {f(po1[0])} {f(po1[1])} '
            f'L {f(pi0[0])} {f(pi0[1])} '
            f'A {f(inner)} {f(inner)} 0 1 1 {f(pi1[0])} {f(pi1[1])} Z" '
            f'fill="{ink}"/>\n')


#: Espressif's mark: the white the ESP32 block prints, as the rings of one
#: even-odd shape, the block's red showing between them: the thin outer ring
#: round its left and bottom, the bold bands about the dot low on its left,
#: and the dot with its hook. Traced on the Plus SE's documentation picture
#: (the same mark, larger: ``back_plus_se.ESPRESSIF_RINGS``) and fitted to
#: this photo by a scale (0.939), a turn (-0.17 degrees) and a shift, by least
#: squares on the photo's green channel blurred as the photo is.
ESPRESSIF_RINGS: Tuple[Tuple[Tuple[float, float], ...], ...] = (
    ((2.825, 16.940), (2.780, 17.013), (2.738, 17.108), (2.718, 17.205), (2.714, 17.325),
     (2.738, 17.445), (2.823, 17.587), (2.932, 17.685), (3.122, 17.772), (3.383, 17.827),
     (3.502, 17.895), (3.574, 17.976), (3.599, 18.017), (3.643, 18.137), (3.653, 18.257),
     (3.642, 18.377), (3.576, 18.546), (3.600, 18.597), (3.672, 18.660), (3.791, 18.717),
     (3.909, 18.740), (3.932, 18.735), (3.963, 18.713), (4.051, 18.520), (4.087, 18.351),
     (4.090, 18.135), (4.051, 17.944), (3.933, 17.729), (3.835, 17.616), (3.739, 17.528),
     (3.644, 17.466), (3.524, 17.410), (3.430, 17.384), (3.311, 17.367), (3.215, 17.328),
     (3.184, 17.299), (3.175, 17.252), (3.191, 17.219), (3.220, 17.203), (3.311, 17.196),
     (3.524, 17.242), (3.714, 17.322), (3.909, 17.464), (4.048, 17.629), (4.120, 17.732),
     (4.156, 17.800), (4.220, 17.968), (4.258, 18.160), (4.262, 18.255), (4.213, 18.543),
     (4.217, 18.600), (4.241, 18.628), (4.298, 18.663), (4.432, 18.694), (4.526, 18.679),
     (4.622, 18.627), (4.655, 18.567), (4.675, 18.471), (4.686, 18.159), (4.667, 17.942),
     (4.600, 17.727), (4.517, 17.535), (4.451, 17.427), (4.332, 17.272), (4.118, 17.069),
     (3.952, 16.956), (3.760, 16.856), (3.522, 16.778), (3.405, 16.761), (3.190, 16.757),
     (3.119, 16.767), (2.952, 16.831), (2.895, 16.868)),
    ((3.196, 16.364), (3.172, 16.411), (3.160, 16.460), (3.160, 16.507), (3.177, 16.556),
     (3.238, 16.588), (3.498, 16.625), (3.666, 16.669), (3.926, 16.768), (4.142, 16.898),
     (4.308, 17.031), (4.451, 17.179), (4.549, 17.295), (4.692, 17.534), (4.766, 17.702),
     (4.795, 17.799), (4.825, 17.966), (4.853, 18.206), (4.870, 18.253), (4.906, 18.272),
     (5.025, 18.270), (5.073, 18.256), (5.096, 18.240), (5.210, 18.108), (5.260, 17.989),
     (5.259, 17.892), (5.219, 17.700), (5.189, 17.605), (5.099, 17.389), (4.985, 17.173),
     (4.859, 16.982), (4.759, 16.850), (4.568, 16.666), (4.354, 16.514), (3.973, 16.305),
     (3.809, 16.242), (3.641, 16.198), (3.474, 16.192), (3.403, 16.211), (3.335, 16.244),
     (3.260, 16.298)),
    ((2.572, 16.797), (2.484, 17.134), (2.473, 17.254), (2.474, 17.517), (2.485, 17.660),
     (2.511, 17.780), (2.620, 18.068), (2.750, 18.284), (2.905, 18.476), (2.984, 18.546),
     (3.173, 18.691), (3.417, 18.833), (3.695, 18.935), (3.980, 18.972), (4.148, 18.974),
     (4.314, 18.958), (4.552, 18.907), (4.741, 18.831), (4.908, 18.750), (5.011, 18.685),
     (5.091, 18.612), (5.151, 18.540), (5.161, 18.492), (5.144, 18.462), (5.120, 18.447),
     (5.097, 18.444), (5.048, 18.468), (4.978, 18.534), (4.764, 18.681), (4.479, 18.794),
     (4.170, 18.840), (3.980, 18.841), (3.791, 18.820), (3.528, 18.741), (3.363, 18.671),
     (3.244, 18.602), (3.190, 18.546), (3.184, 18.523), (3.197, 18.498), (3.290, 18.463),
     (3.337, 18.433), (3.409, 18.357), (3.432, 18.305), (3.436, 18.234), (3.427, 18.162),
     (3.398, 18.113), (3.328, 18.043), (3.288, 18.024), (3.193, 18.010), (3.146, 18.014),
     (3.098, 18.034), (3.051, 18.067), (3.009, 18.115), (2.945, 18.259), (2.934, 18.268),
     (2.910, 18.268), (2.886, 18.254), (2.781, 18.092), (2.724, 17.972), (2.626, 17.660),
     (2.600, 17.468), (2.605, 17.108), (2.639, 16.965), (2.748, 16.701), (2.805, 16.628),
     (2.979, 16.365), (2.980, 16.317), (2.951, 16.281), (2.928, 16.274), (2.904, 16.280),
     (2.856, 16.314), (2.714, 16.509)),
    ((3.946, 16.049), (3.936, 16.074), (3.949, 16.117), (3.972, 16.138), (4.282, 16.285),
     (4.444, 16.383), (4.592, 16.486), (4.755, 16.622), (4.901, 16.788), (5.149, 17.126),
     (5.307, 17.460), (5.355, 17.486), (5.402, 17.463), (5.415, 17.437), (5.420, 17.388),
     (5.416, 17.220), (5.401, 17.113), (5.379, 17.029), (5.223, 16.669), (5.150, 16.550),
     (5.069, 16.454), (4.961, 16.359), (4.828, 16.263), (4.543, 16.099), (4.377, 16.050),
     (4.220, 16.024), (4.091, 16.014), (3.972, 16.029)),
)


def espressif(out: List[str]) -> None:
    """Espressif's mark in white on the ESP32 block."""
    d = " ".join("M " + " L ".join(f"{f(x)} {f(y)}" for x, y in ring) + " Z"
                 for ring in ESPRESSIF_RINGS)
    out.append(f'<path d="{d}" fill="{WHITE}" fill-rule="evenodd"/>\n')


def fcc(out: List[str]) -> None:
    """FCC's mark: an F, then two C's about one center, each open to the right."""
    out.append(fronts.cardputer_polygon(
        [(9.37, 19.62), (10.51, 19.62), (10.51, 19.98), (9.77, 19.98), (9.77, 20.59),
         (10.47, 20.59), (10.47, 20.95), (9.77, 20.95), (9.77, 21.89), (9.37, 21.89)], BLACK))
    out.append(arc(11.59, 20.8, 0.95, 35, 325, BLACK, 0.31))
    out.append(arc(11.59, 20.8, 0.54, 42, 318, BLACK, 0.29))


def giteki(out: List[str]) -> None:
    """Japan's technical-conformity mark: a ring broken on its upper right by a
    lightning stroke, over two bars and a stem; then the R box."""
    gx, gy, ring = 4.16, 26.08, 1.0
    start, end = math.radians(-14), math.radians(22)
    bolt = [(gx - 0.95, gy - 0.3), (gx - 0.03, gy - 0.46), (gx + 0.1, gy - 0.16),
            (gx + ring * math.cos(start), gy + ring * math.sin(start))]
    path = " L ".join(f"{f(px)} {f(py)}" for px, py in bolt)
    out.append(f'<path d="M {path} A {f(ring)} {f(ring)} 0 1 0 '
               f'{f(gx + ring * math.cos(end))} {f(gy + ring * math.sin(end))}" '
               f'fill="none" stroke="{BLACK}" stroke-width="0.1" stroke-linejoin="round"/>\n')
    out.append(f'<path d="M {f(gx - 0.55)} {f(gy + 0.14)} H {f(gx + 0.6)} '
               f'M {f(gx - 0.55)} {f(gy + 0.39)} H {f(gx + 0.6)} '
               f'M {f(gx)} {f(gy + 0.39)} V {f(gy + 0.76)}" fill="none" '
               f'stroke="{BLACK}" stroke-width="0.09"/>\n')
    out.append(f'<path d="{rounded_path(5.56, 25.52, 6.78, 26.54, 0.0)}" fill="none" '
               f'stroke="{GRAY}" stroke-width="0.1"/>\n')
    out.append(run("R", 5.86, 26.33, 0.9, 0.62, "400", GRAY))


def ce(out: List[str]) -> None:
    """CE: two rings of one size cut on their right, the E's bar inside."""
    out.append(ring_cut(4.83, 30.66, 2.69, 1.92, 5.11, BLACK))
    out.append(ring_cut(9.48, 30.66, 2.69, 1.92, 9.8, BLACK))
    out.append(fronts.rounded_rect(7.5, 30.29, 1.72, 0.73, r=0.0, fill=BLACK))


def weee(out: List[str]) -> None:
    """The crossed-out wheelie bin: its lid in outline (a raised handle in the
    middle, a short upright on its left), the lid's bar, the body on a foot,
    the ear on its right and the wheel."""
    out.append(stroke([(11.41, 27.42), (11.62, 30.66), (13.3, 30.66)], BLACK, 0.115))
    out.append(stroke([(13.5, 27.42), (13.36, 30.2)], BLACK, 0.115))
    out.append(stroke([(11.25, 27.42), (13.75, 27.42)], BLACK, 0.12))
    out.append(stroke([(11.3, 27.38), (11.49, 27.22), (11.66, 27.06), (12.29, 27.06)],
                      BLACK, 0.1))
    out.append(stroke([(11.71, 27.06), (11.71, 27.38)], BLACK, 0.1))
    out.append(f'<path d="{rounded_path(12.29, 26.93, 12.86, 27.14, 0.0)}" fill="none" '
               f'stroke="{BLACK}" stroke-width="0.1"/>\n')
    out.append(stroke([(12.86, 27.06), (13.0, 27.06), (13.35, 27.12), (13.66, 27.23),
                       (13.75, 27.38)], BLACK, 0.1))
    out.append(stroke([(13.52, 27.7), (13.84, 27.7), (13.84, 28.1), (13.48, 28.1)], BLACK, 0.09))
    out.append(fronts.rounded_rect(12.23, 28.2, 0.77, 0.24, r=0.0, fill=BLACK))
    out.append(fronts.circle(13.24, 30.51, 0.27, fill="none", stroke=BLACK, stroke_w=0.11))
    out.append(fronts.circle(13.24, 30.51, 0.07, fill=BLACK))
    out.append(fronts.rounded_rect(11.58, 30.66, 0.2, 0.22, r=0.0, fill=BLACK))
    out.append(stroke([(10.0, 26.54), (14.56, 31.35)], BLACK, 0.09))
    out.append(stroke([(14.9, 26.54), (10.14, 31.38)], BLACK, 0.09))


def m5_cube(out: List[str]) -> None:
    """M5Stack's cube: a hexagon in outline, open on the upper right and below
    its left corner, the top face's two front edges, and the 5 on that face."""
    out.append(stroke([(5.81, 33.9), (4.9, 33.54), (3.79, 34.02), (4.9, 34.52),
                       (6.06, 34.03), (6.08, 34.8), (4.9, 35.32), (3.71, 34.8),
                       (3.71, 34.24)], CUBE_BLUE, 0.1))
    out.append(stroke([(4.84, 33.74), (4.51, 33.9)], BLACK, 0.1))
    out.append(stroke([(4.34, 33.99), (4.56, 34.12), (5.11, 33.88), (5.39, 33.96),
                       (5.38, 34.06), (4.94, 34.27)], BLACK, 0.1))


def append_plus2_back(out: List[str]) -> None:
    """Every print of the Plus2's back label: one legend group on ``label``."""
    out.append(fronts.print_open("back-label", "label"))
    out.append(f'<g transform="matrix(1 0 0 {STRETCH_Y:.6f} 0 {SHIFT_Y:.6f})">\n')
    out.extend(cells())
    out.append(arrow(5.645, 1.94, 2.75, 3.58, 1.37, 0.69, YELLOW))
    out.append(arrow(21.21, 3.51, 2.7, 1.86, 1.44, 0.7, WHITE))
    out.append(banner())
    for spec in FIELDS:
        out.append(field(*spec))
    for spec in RUNS:
        out.append(run(*spec))
    for spec in UP_RUNS:
        out.append(run_up(*spec))
    out.append(stroke([(10.12, 4.09), (11.53, 4.55)], BLACK, 0.12))
    for spec in SLANT_RUNS:
        out.append(run_slant(*spec))
    out.append('<path d="M 1.99 12.46 Q 2.3 13.3 2.78 13.45" fill="none" '
               f'stroke="{GRAY}" stroke-width="0.13" stroke-linecap="round"/>\n')
    out.append(stroke([(21.12, 37.42), (21.6, 37.8)], GRAY, 0.08))
    espressif(out)
    fcc(out)
    giteki(out)
    ce(out)
    weee(out)
    m5_cube(out)
    out.append("</g>\n")
    out.append(fronts.LEGEND_CLOSE)
