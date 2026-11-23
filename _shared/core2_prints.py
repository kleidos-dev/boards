# SPDX-License-Identifier: MIT
"""What the M5Stack Core2 v1.3 prints on its back and on its top side

The back carries a sticker of about 35 x 51 mm on the gray bottom cover: the
Espressif tile and the chip's name block, the M-BUS pin table (fifteen rows of
colored cells), and the board's parts with their pins (touch, vibration motor,
power key, LCD, RTC, USB bridge, PMIC, DC/DC, Port A, speaker amplifier, IMU,
microphone, microSD, reset, LED). The top side carries the rating label in its
recess: CE, the WEEE bin, FCC, Japan's radio mark, the Giteki number, the FCC
ID, the input rating and the model on a gray band.

Every position, size and ink was measured on M5Stack's product photos of the
board (reference only, never committed: the back straight on at 12.95 px/mm,
the top label at about 15 px/mm), on a millimeter grid of the face's own frame
(``board_faces.py``): the back in the back frame (x from the case's left edge
as seen from behind, y down from its top), the top in the top frame (x from the
case's left edge, y down from its back edge). Each text run is set in Inter,
the only face the models carry, with ``textLength`` pinning the run to the
width the photo prints it at: the label's own face is a narrower humanist sans
(close to Ubuntu), so most runs are squeezed: from 0.74 to 1.17 of Inter's width.
Each ink is the median of the photo's pixels inside a cell or over a stroke's
core; the photo's paper is white (#fffffd), so they are taken as they are.

Left out: the removable ``CORE2`` strip that covers the M-BUS slot as the
board ships (the model shows the slot open, the header in it). The four
black rubber feet beside the corner screws are no print: they are solids of
the model's spec (``feet``).
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from emit_front_svg import LEGEND_CLOSE, circle, f, print_open, rounded_rect, text

# ------------------------------------------------------------------ inks
BLACK = "#141414"  # GND/NC-less dark text, the black cells, PWR, RST, the USB plug, microSD
WHITE = "#ffffff"
GRAY = "#8e9191"  # D0WDQ6-V3, SYSTEM, the clock's ring, the speaker's magnet, thin leads
DARK_GRAY = "#555555"  # the dashed rules, M5STACK, DC/DC, AXP ExtEN
TEAL = "#2f6765"  # ADC, NS4168
LIGHT_GRAY = "#c9cbca"  # the RST cell
CYAN = "#0cadd4"  # MOSI, MISO, SCK, ILI9342C, the reset arrow
SALMON = "#fd6460"  # DAC, Port A's frame
DARK_RED = "#9a0202"  # ESP32, 3.3V, 5V, AXP192, 5V BUS, Port A's 5V, the curved arrow
GREEN = "#019630"  # RXD0/TXD0, RXD2/TXD2
LED_GREEN = "#37cc35"  # the LED's glass
ORANGE = "#f06b10"  # intSDA, intSCL, USB-C, the microphone, the vibration's waves
TERRACOTTA = "#c9673f"  # 3V3, 6S=OFF
RED = "#c91518"  # PA_SDA, PA_SCL, PWR:AXP_LDO2, AXP_LDO2
PINK = "#fcccc9"  # the GPIO cells
LIGHT_ORANGE = "#f59d3a"  # the I2S and PDM cells
PURPLE = "#650163"  # NC
YELLOW = "#fdcf06"  # BAT, Port A's G32, the microSD contacts
VERMILION = "#d03101"  # the Espressif tile, the power key's arrow
BLUE = "#0870b8"  # CAP.TOUCH, the LCD's line, the M5Stack cube, v1.3
MAGENTA = "#c62e60"  # BM8563, the battery, the clock's hand, AXP_LDO0 and its leads
OLIVE = "#2f3300"  # CH9102
LIGHT_BLUE = "#a6dcf4"  # BMI270
#: The back sticker's paper; the model's ``sticker`` material.
PAPER = "#fafaf8"

# ------------------------------------------------------------------ the back
#: The sticker's outline: the pocket the bottom cover holds it in, 0.2 mm deep
#: (the vendor's STL: x 17.67..52.61, y 1.40..52.60, the right part cut back
#: above y 8.90 and below y 45.10 round the corner screws and feet, every
#: corner R2), less 0.05 mm all round. The photo's paper is that outline to
#: 0.2 mm; its prints are measured on the photo and stretched along y by
#: ``PRINT_STRETCH_Y`` about the sticker's top so that the photo's paper fills
#: the pocket's height (the photo's vertical scale is 0.45 % short).
PAPER_LEFT, PAPER_RIGHT, PAPER_TOP, PAPER_BOTTOM = 17.72, 52.56, 1.45, 52.55
PAPER_NOTCH_X, PAPER_NOTCH_TOP, PAPER_NOTCH_BOTTOM = 37.82, 8.95, 45.05
PAPER_R, PAPER_NOTCH_R, PAPER_INNER_R = 1.95, 1.95, 2.05
PRINT_STRETCH_Y = 1.0045
PRINT_TOP_Y = 1.40

#: The M-BUS table: fifteen rows 1.831 mm apart, each cell 1.52 mm tall.
ROW0, PITCH, CELL_H = 12.06, 1.831, 1.52
L_FULL, L_NARROW, L_END = 18.38, 21.70, 26.93
R_START, R_END, R_WIDE = 27.26, 32.43, 35.82
#: (left cell's ink and whether it runs the full width, right cell's ink and
#: whether it runs wide), row by row; None where the row has no such cell.
CELLS = (
    ((BLACK, True), (TEAL, False)),
    ((BLACK, True), (TEAL, False)),
    ((BLACK, True), (LIGHT_GRAY, False)),
    ((CYAN, False), (SALMON, False)),
    ((CYAN, False), (SALMON, False)),
    ((CYAN, False), (DARK_RED, True)),
    ((GREEN, False), (GREEN, False)),
    ((GREEN, False), (GREEN, False)),
    ((ORANGE, False), (ORANGE, False)),
    ((RED, False), (RED, False)),
    ((PINK, False), (PINK, False)),
    ((LIGHT_ORANGE, False), (LIGHT_ORANGE, False)),
    ((PURPLE, True), (LIGHT_ORANGE, False)),
    ((PURPLE, True), (DARK_RED, True)),
    ((PURPLE, True), (YELLOW, True)),
)


# ------------------------------------------------------------------ the back's text
#: Every upright run: (x, baseline y, text, size, textLength, weight, ink), fitted on the
#: photo so that Inter's ink covers the run's ink (the M-BUS table's runs share one size
#: a column, the parts' pin lines one size, 0.93 mm). Weight 900 is the label's heavy face.
TEXT = (
    (20.97, 13.36, "GND", 1.55, 3.38, 700, WHITE),
    (28.42, 13.36, "ADC", 1.45, 2.97, 400, WHITE),
    (32.84, 13.34, "G35", 1.52, 2.96, 400, BLACK),
    (20.97, 15.21, "GND", 1.55, 3.38, 700, WHITE),
    (28.42, 15.21, "ADC", 1.45, 2.97, 400, WHITE),
    (32.84, 15.20, "G36", 1.52, 3.04, 400, BLACK),
    (20.97, 17.06, "GND", 1.55, 3.38, 700, WHITE),
    (28.56, 16.98, "RST", 1.45, 2.66, 400, BLACK),
    (32.88, 17.05, "EN", 1.52, 2.04, 400, BLACK),
    (18.32, 18.87, "G23", 1.52, 3.04, 400, BLACK),
    (22.37, 18.84, "MOSI", 1.45, 3.98, 400, BLACK),
    (28.41, 18.84, "DAC", 1.45, 2.98, 400, WHITE),
    (32.84, 18.87, "G25", 1.52, 2.96, 400, BLACK),
    (18.32, 20.68, "G38", 1.52, 3.04, 400, BLACK),
    (22.37, 20.69, "MISO", 1.45, 3.93, 400, BLACK),
    (28.41, 20.69, "DAC", 1.45, 2.98, 400, WHITE),
    (32.84, 20.68, "G26", 1.52, 3.04, 400, BLACK),
    (18.31, 22.53, "G18", 1.52, 3.06, 400, BLACK),
    (22.97, 22.51, "SCK", 1.45, 2.66, 400, BLACK),
    (30.01, 22.51, "3.3V", 1.45, 3.11, 700, WHITE),
    (19.33, 24.39, "G3", 1.52, 2.03, 400, BLACK),
    (22.53, 24.32, "RXD0", 1.45, 3.84, 400, WHITE),
    (28.15, 24.32, "TXD0", 1.45, 3.70, 400, WHITE),
    (32.83, 24.39, "G1", 1.52, 1.95, 400, BLACK),
    (18.31, 26.20, "G13", 1.52, 3.06, 400, BLACK),
    (22.46, 26.18, "RXD2", 1.45, 3.78, 400, WHITE),
    (28.08, 26.18, "TXD2", 1.45, 3.64, 400, WHITE),
    (32.83, 26.16, "G14", 1.52, 3.06, 400, BLACK),
    (18.55, 28.02, "G21", 1.52, 2.87, 400, BLACK),
    (21.95, 28.00, "intSDA", 1.45, 4.76, 400, WHITE),
    (27.67, 28.04, "intSCL", 1.45, 4.48, 400, WHITE),
    (32.84, 28.02, "G22", 1.52, 2.98, 400, BLACK),
    (18.32, 29.87, "G32", 1.52, 3.06, 400, BLACK),
    (21.96, 29.77, "PA_SDA", 1.45, 4.74, 700, WHITE),
    (27.68, 29.77, "PA_SCL", 1.45, 4.44, 700, WHITE),
    (32.84, 29.87, "G33", 1.52, 2.96, 400, BLACK),
    (18.32, 31.68, "G27", 1.52, 2.94, 400, BLACK),
    (22.57, 31.66, "GPIO", 1.45, 3.57, 400, BLACK),
    (28.13, 31.66, "GPIO", 1.45, 3.57, 400, BLACK),
    (32.83, 31.72, "G19", 1.52, 3.06, 400, BLACK),
    (19.25, 33.50, "G2", 1.52, 2.14, 400, BLACK),
    (21.88, 33.34, "I2S_DOUT", 1.10, 4.85, 400, BLACK),
    (32.84, 33.50, "G0", 1.52, 2.11, 400, BLACK),
    (21.64, 35.36, "NC", 1.55, 2.16, 700, WHITE),
    (27.52, 35.01, "PDM_DAT", 1.00, 4.77, 400, BLACK),
    (32.84, 35.35, "G34", 1.52, 3.03, 400, BLACK),
    (21.64, 37.18, "NC", 1.55, 2.16, 700, WHITE),
    (30.71, 37.13, "5V", 1.45, 1.79, 700, WHITE),
    (21.64, 38.99, "NC", 1.55, 2.16, 700, WHITE),
    (30.18, 38.99, "BAT", 1.45, 2.73, 400, BLACK),
    (27.30, 32.84, "I2S_LRCK", 0.85, 3.56, 400, BLACK),
    (28.61, 33.61, "PDM_CLK", 0.85, 3.72, 400, BLACK),
    (27.43, 4.68, "ESP32", 3.50, 8.79, 400, DARK_RED),
    (27.57, 6.28, "D0WDQ6-V3", 1.61, 7.83, 400, GRAY),
    (27.53, 8.25, "16M-FLASH", 1.85, 9.10, 400, BLACK),
    (27.35, 10.18, "8M-PSRAM", 1.96, 8.81, 400, BLACK),
    (37.44, 10.58, "CAP.TOUCH", 1.24, 5.74, 700, WHITE),
    (37.28, 12.05, "SDA:21", 0.93, 3.07, 400, BLACK),
    (37.28, 12.97, "SCL:22", 0.93, 2.89, 400, BLACK),
    (37.33, 13.90, "INT:39", 0.93, 2.83, 400, BLACK),
    (37.33, 14.91, "RST:AXP_IO4", 0.93, 5.53, 400, BLACK),
    (44.44, 14.09, "PWM:", 0.93, 2.22, 400, BLACK),
    (43.49, 15.03, "AXP_LDO3", 0.93, 4.16, 400, BLACK),
    (48.56, 12.98, "PWR", 2.02, 3.68, 900, BLACK),
    (48.63, 14.05, "6S=OFF", 0.93, 3.59, 400, TERRACOTTA),
    (48.59, 15.02, "AXP_PWR", 0.93, 3.67, 400, BLACK),
    (37.33, 16.38, 'IPS LCD 2"@320x240', 0.83, 9.01, 400, BLUE),
    (38.59, 18.22, "ILI9342C", 1.76, 6.31, 400, BLACK),
    (37.33, 19.35, "PWR:AXP_LDO2", 0.93, 6.78, 400, RED),
    (37.33, 20.32, "RST:AXP_IO4", 0.93, 5.53, 400, BLACK),
    (37.33, 21.28, "BL:AXP_DC3", 0.93, 5.22, 400, BLACK),
    (37.33, 22.24, "MO:23", 0.93, 2.83, 400, BLACK),
    (37.33, 23.17, "MI:38", 0.93, 2.45, 400, BLACK),
    (37.36, 24.09, "SCK:18", 0.93, 2.96, 400, BLACK),
    (37.33, 25.06, "DC:15", 0.93, 2.53, 400, BLACK),
    (37.28, 26.02, "CS:5", 0.93, 1.88, 400, BLACK),
    (48.67, 18.00, "BM", 1.70, 2.96, 400, WHITE),
    (48.54, 19.15, "8563", 1.35, 3.19, 400, WHITE),
    (49.17, 20.77, "SDA:21", 0.93, 2.99, 400, BLACK),
    (49.41, 21.70, "SCL:22", 0.93, 2.89, 400, BLACK),
    (46.29, 22.63, "INT:AXP_PWR", 0.93, 5.90, 400, BLACK),
    (41.48, 23.77, "CH", 2.27, 2.49, 400, WHITE),
    (41.05, 25.02, "9102", 1.44, 3.31, 700, WHITE),
    (41.62, 26.18, "TXD:3", 0.93, 2.48, 400, BLACK),
    (41.50, 27.07, "RXD:1", 0.93, 2.56, 400, BLACK),
    (41.06, 28.88, "SDA:21", 0.93, 3.07, 400, BLACK),
    (41.07, 29.81, "SCL:22", 0.93, 2.89, 400, BLACK),
    (41.60, 32.52, "AXP", 2.23, 4.50, 400, WHITE),
    (41.85, 34.74, "192", 2.27, 4.16, 400, WHITE),
    (47.05, 33.05, "M5STACK", 1.13, 5.06, 400, DARK_GRAY),
    (48.36, 34.67, "v1.3", 1.24, 2.47, 700, WHITE),
    (37.08, 35.80, "AXP_LDO0", 0.57, 3.38, 400, MAGENTA),
    (40.43, 37.22, "3V3", 1.34, 2.22, 400, TERRACOTTA),
    (44.82, 37.82, "DC/DC", 0.97, 2.99, 400, DARK_GRAY),
    (37.98, 38.84, "5V", 1.36, 1.46, 700, WHITE),
    (37.50, 40.14, "BUS", 1.45, 2.33, 700, WHITE),
    (42.22, 39.84, "SY7088", 1.55, 4.97, 700, WHITE),
    (44.36, 42.41, "AXP", 0.95, 1.95, 400, DARK_GRAY),
    (44.38, 43.78, "ExtEN", 1.16, 2.91, 400, DARK_GRAY),
    (49.67, 41.39, "5V", 1.47, 1.91, 400, WHITE),
    (49.99, 43.70, "G", 1.96, 1.32, 700, WHITE),
    (30.64, 41.40, "SPK_EN:AXP_IO2", 0.93, 7.22, 400, BLACK),
    (30.69, 42.51, "BCLK:12", 0.93, 3.54, 400, BLACK),
    (31.23, 43.44, "LRCK:0", 0.93, 2.98, 400, BLACK),
    (31.00, 44.41, "DATA:2", 0.93, 3.15, 400, BLACK),
    (35.15, 43.53, "NS", 2.27, 2.76, 400, WHITE),
    (35.18, 44.56, "4168", 1.14, 2.69, 400, WHITE),
    (20.99, 42.33, "BMI", 1.80, 3.57, 700, BLACK),
    (21.34, 43.47, "270", 1.45, 2.85, 700, BLACK),
    (24.92, 41.87, "SDA:21", 1.08, 3.63, 400, BLACK),
    (24.92, 42.99, "SCL:22", 1.08, 3.45, 400, BLACK),
    (23.42, 45.85, "DAT:G34", 1.08, 4.47, 400, BLACK),
    (23.37, 46.97, "CLK:G0", 1.08, 3.67, 400, BLACK),
    (30.41, 46.18, "CS:4", 0.93, 1.95, 400, BLACK),
    (30.00, 47.18, "MI:38", 0.93, 2.37, 400, BLACK),
    (30.01, 48.19, "MO:23", 0.93, 2.35, 400, BLACK),
    (29.80, 49.19, "SCK:18", 0.93, 2.56, 400, BLACK),
    (27.66, 50.09, "AXP_LDO2", 0.93, 4.72, 400, RED),
    (33.17, 47.65, "MICRO", 1.14, 3.67, 700, WHITE),
    (21.29, 49.34, "SYSTEM", 1.13, 4.40, 400, GRAY),
    (21.12, 51.69, "RST", 3.13, 4.64, 900, BLACK),
    (29.52, 51.90, "LED:AXP_IO1", 0.93, 6.60, 400, BLACK),
)

#: The runs that read bottom to top (rotate(-90) about their start).
TEXT_UP = (
    (48.12, 28.21, "USB-C", 1.86, 4.55, 900, ORANGE),
    (37.93, 34.63, "LiPo-500mAh", 1.32, 7.45, 400, BLACK),
    (39.73, 33.94, "BATTERY", 1.49, 5.62, 400, BLACK),
    (18.87, 44.70, "BASE", 0.93, 2.34, 700, BLACK),
    (19.95, 44.71, "BOARD", 0.93, 3.43, 700, BLACK),
    (49.37, 42.13, "PORT A", 1.34, 4.62, 400, WHITE),
)

# ------------------------------------------------------------------ helpers
Point = Tuple[float, float]


def _poly(points: Sequence[Point], fill: str) -> str:
    return (
        '<polygon points="' + " ".join(f"{f(x)},{f(y)}" for x, y in points) + f'" fill="{fill}"/>\n'
    )


def _line(
    points: Sequence[Point], ink: str, width: float, cap: str = "butt", join: str = "round"
) -> str:
    d = " L ".join(f"{f(x)} {f(y)}" for x, y in points)
    return (
        f'<path d="M {d}" fill="none" stroke="{ink}" stroke-width="{f(width)}" '
        f'stroke-linecap="{cap}" stroke-linejoin="{join}"/>\n'
    )


def _arc(
    cx: float, cy: float, r: float, a0: float, a1: float, ink: str, width: float, cap: str = "butt"
) -> str:
    """An arc about (cx, cy) from angle a0 to a1 (degrees, y down), the way the angle grows."""
    t0, t1 = math.radians(a0), math.radians(a1)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return (
        f'<path d="M {f(cx + r * math.cos(t0))} {f(cy + r * math.sin(t0))} '
        f'A {f(r)} {f(r)} 0 {large} 1 {f(cx + r * math.cos(t1))} {f(cy + r * math.sin(t1))}" '
        f'fill="none" stroke="{ink}" stroke-width="{f(width)}" stroke-linecap="{cap}"/>\n'
    )


def _dashes(
    points: Sequence[Point],
    ink: str,
    dash: float = 0.89,
    pitch: float = 1.12,
    width: float = 0.16,
    lead: float = 0.0,
) -> List[str]:
    """A dashed rule along a polyline: dashes ``dash`` long every ``pitch``, each cut at the vertex it
    reaches (the pattern itself carries on round the corner)."""
    out: List[str] = []
    s = lead
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        while s < length - 0.05:
            e = min(s + dash, length)
            out.append(_line([(x0 + ux * s, y0 + uy * s), (x0 + ux * e, y0 + uy * e)], ink, width))
            s += pitch
        s -= length
    return out


def _dashes_bent(
    points: Sequence[Point],
    ink: str,
    dash: float = 0.89,
    pitch: float = 1.12,
    width: float = 0.16,
    lead: float = 0.0,
) -> List[str]:
    """A dashed rule along a polyline whose dashes bend round its vertices: dashes ``dash`` long every
    ``pitch``.

    The first dash starts ``lead`` along the line; a negative lead cuts it short at the line's start.
    A dash that runs past a vertex goes on along the next segment, so a corner drawn as a run of short
    segments (``_corner``) bends the dash round it."""
    out: List[str] = []
    seg = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        seg.append(((x0, y0), (x1, y1), math.hypot(x1 - x0, y1 - y0)))
    total = sum(n for _, _, n in seg)

    def at(d: float) -> Point:
        for (x0, y0), (x1, y1), n in seg:
            if d <= n or (x1, y1) == points[-1]:
                t = min(d / n, 1.0)
                return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            d -= n
        return points[-1]

    s = lead
    while s < total - 0.05:
        a, b = max(s, 0.0), min(s + dash, total)
        if b > a:
            pts = [at(a)]
            run = 0.0
            for _, (x1, y1), n in seg:
                run += n
                if a < run < b:
                    pts.append((x1, y1))
            pts.append(at(b))
            out.append(_line(pts, ink, width))
        s += pitch
    return out


def _corner(start: Point, center: Point, end: Point, step_deg: float = 10.0) -> List[Point]:
    """A quarter-round corner from *start* to *end* about *center*, as points (start and end
    included), for a dashed rule."""
    a0 = math.atan2(start[1] - center[1], start[0] - center[0])
    a1 = math.atan2(end[1] - center[1], end[0] - center[0])
    while a1 - a0 > math.pi:
        a1 -= 2 * math.pi
    while a0 - a1 > math.pi:
        a1 += 2 * math.pi
    r = math.hypot(start[0] - center[0], start[1] - center[1])
    n = max(2, round(abs(math.degrees(a1 - a0)) / step_deg))
    return [
        (
            center[0] + r * math.cos(a0 + (a1 - a0) * k / n),
            center[1] + r * math.sin(a0 + (a1 - a0) * k / n),
        )
        for k in range(n + 1)
    ]


def _arrow_head(
    tip: Point, toward: Point, ink: str, length: float = 0.32, half: float = 0.17
) -> str:
    """A filled triangle with its point at *tip*, pointing away from *toward*."""
    dx, dy = tip[0] - toward[0], tip[1] - toward[1]
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    bx, by = tip[0] - ux * length, tip[1] - uy * length
    return _poly([tip, (bx - uy * half, by + ux * half), (bx + uy * half, by - ux * half)], ink)


def _block_arrow(
    tail: Point, tip: Point, ink: str, head: float, head_half: float, shaft_half: float
) -> str:
    """A filled arrow: a shaft from *tail* and a triangular head at *tip*."""
    dx, dy = tip[0] - tail[0], tip[1] - tail[1]
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    px, py = -uy, ux
    bx, by = tip[0] - ux * head, tip[1] - uy * head
    return _poly(
        [
            (tail[0] + px * shaft_half, tail[1] + py * shaft_half),
            (bx + px * shaft_half, by + py * shaft_half),
            (bx + px * head_half, by + py * head_half),
            tip,
            (bx - px * head_half, by - py * head_half),
            (bx - px * shaft_half, by - py * shaft_half),
            (tail[0] - px * shaft_half, tail[1] - py * shaft_half),
        ],
        ink,
    )


def _bulb(
    cx: float, cy: float, r: float, neck_half: float, neck_y: float, step_deg: float = 10.0
) -> List[Point]:
    """A bulb's outline: the circle about (cx, cy) from 40 degrees below its right
    side over the top to 40 below its left, then straight to a neck *neck_half*
    either side of cx at *neck_y*."""
    pts = [
        (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        for a in range(40, -221, -int(step_deg))
    ]
    return pts + [(cx - neck_half, neck_y), (cx + neck_half, neck_y)]


def _cell(
    x0: float, y0: float, x1: float, y1: float, top_r: float, bottom_r: float, fill: str
) -> str:
    """A filled cell whose top corners take *top_r* and bottom corners *bottom_r*."""
    t, b = top_r, bottom_r
    return (
        f'<path d="M {f(x0 + t)} {f(y0)} H {f(x1 - t)} A {f(t)} {f(t)} 0 0 1 {f(x1)} {f(y0 + t)} '
        f"V {f(y1 - b)} A {f(b)} {f(b)} 0 0 1 {f(x1 - b)} {f(y1)} H {f(x0 + b)} "
        f"A {f(b)} {f(b)} 0 0 1 {f(x0)} {f(y1 - b)} V {f(y0 + t)} "
        f'A {f(t)} {f(t)} 0 0 1 {f(x0 + t)} {f(y0)} Z" fill="{fill}"/>\n'
    )


def _text_up(
    x: float, y: float, content: str, size: float, length: float, weight: int, ink: str
) -> str:
    """A run reading bottom to top: its start at (x, y), its baseline on x."""
    return (
        f'<g transform="rotate(-90 {f(x)} {f(y)})">\n'
        + _run(x, y, content, size, length, weight, ink)
        + "</g>\n"
    )


#: The label's heavy condensed face (PWR, RST, USB-C, CORE2), heavier than Inter's boldest:
#: how far each stroke grows on every side, as a fraction of the run's size.
HEAVY_GROW = 0.03


def _heavy(x: float, y: float, content: str, size: float, length: float, ink: str) -> str:
    """A run in the heavy face (weight 900 in the tables): the bold run set *grow* inside its
    ink box on every side, then laid down again moved *grow* each way round a circle, so the
    union keeps the ink box and its strokes are 2 * *grow* wider."""
    grow = HEAVY_GROW * size
    inner = size - 2 * grow / 0.727  # Inter's cap height, in ems
    x0, y0, length0 = x + grow, y - grow, length - 2 * grow
    out = [
        text(x0, y0, content, size=inner, fill=ink, anchor="start", weight="700", length=length0)
    ]
    for k in range(12):
        a = math.radians(30 * k)
        out.append(
            text(
                x0 + grow * math.cos(a),
                y0 + grow * math.sin(a),
                content,
                size=inner,
                fill=ink,
                anchor="start",
                weight="700",
                length=length0,
            )
        )
    return "".join(out)


def _run(
    x: float, y: float, content: str, size: float, length: float, weight: int, ink: str
) -> str:
    """A run from a table: Inter at its weight, or the heavy face for weight 900."""
    if weight == 900:
        return _heavy(x, y, content, size, length, ink)
    return text(
        x, y, content, size=size, fill=ink, anchor="start", weight=str(weight), length=length
    )


def _text_turned(
    x: float,
    y: float,
    content: str,
    size: float,
    length: float,
    weight: int,
    ink: str,
    angle: float,
    anchor: str = "middle",
) -> str:
    return (
        f'<g transform="rotate({f(angle)} {f(x)} {f(y)})">\n'
        + text(x, y, content, size=size, fill=ink, anchor=anchor, weight=str(weight), length=length)
        + "</g>\n"
    )


def paper_path() -> str:
    """The sticker's outline as a path in the back frame."""
    x0, x1, y0, y1 = PAPER_LEFT, PAPER_RIGHT, PAPER_TOP, PAPER_BOTTOM
    nx, nt, nb = PAPER_NOTCH_X, PAPER_NOTCH_TOP, PAPER_NOTCH_BOTTOM
    r, rn, ri = PAPER_R, PAPER_NOTCH_R, PAPER_INNER_R
    return (
        f"M {f(x0 + r)} {f(y0)} H {f(nx - rn)} A {f(rn)} {f(rn)} 0 0 1 {f(nx)} {f(y0 + rn)} "
        f"V {f(nt - ri)} A {f(ri)} {f(ri)} 0 0 0 {f(nx + ri)} {f(nt)} "
        f"H {f(x1 - r)} A {f(r)} {f(r)} 0 0 1 {f(x1)} {f(nt + r)} "
        f"V {f(nb - r)} A {f(r)} {f(r)} 0 0 1 {f(x1 - r)} {f(nb)} "
        f"H {f(nx + ri)} A {f(ri)} {f(ri)} 0 0 0 {f(nx)} {f(nb + ri)} "
        f"V {f(y1 - rn)} A {f(rn)} {f(rn)} 0 0 1 {f(nx - rn)} {f(y1)} "
        f"H {f(x0 + r)} A {f(r)} {f(r)} 0 0 1 {f(x0)} {f(y1 - r)} "
        f"V {f(y0 + r)} A {f(r)} {f(r)} 0 0 1 {f(x0 + r)} {f(y0)} Z"
    )


def paper_polygon(step_deg: float = 10.0) -> List[Point]:
    """The sticker's outline as points (its arcs at *step_deg*), for the model's paper solid."""
    x0, x1, y0, y1 = PAPER_LEFT, PAPER_RIGHT, PAPER_TOP, PAPER_BOTTOM
    nx, nt, nb = PAPER_NOTCH_X, PAPER_NOTCH_TOP, PAPER_NOTCH_BOTTOM
    r, rn, ri = PAPER_R, PAPER_NOTCH_R, PAPER_INNER_R
    pts: List[Point] = []

    def corner(cx: float, cy: float, rad: float, a0: float, a1: float) -> None:
        n = max(2, round(abs(a1 - a0) / step_deg))
        for k in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * k / n)
            pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))

    corner(x0 + r, y0 + r, r, 180, 270)
    corner(nx - rn, y0 + rn, rn, 270, 360)
    corner(nx + ri, nt - ri, ri, 180, 90)
    corner(x1 - r, nt + r, r, 270, 360)
    corner(x1 - r, nb - r, r, 0, 90)
    corner(nx + ri, nb + ri, ri, 270, 180)
    corner(nx - rn, y1 - rn, rn, 0, 90)
    corner(x0 + r, y1 - r, r, 90, 180)
    return pts


# ------------------------------------------------------------------ the back's marks
#: Espressif's mark on its tile: the white the tile prints, as the rings of one
#: even-odd shape, the tile's vermilion showing between them: the thin outer
#: ring round its left and bottom, the bold bands about the dot low on its
#: left, and the dot with its hook. The project's trace of the mark (the Plus
#: SE's, as the Plus2 places it: ``back_plus2.ESPRESSIF_RINGS``) fitted to this
#: photo by a scale (1.995), a turn (-0.11 degrees) and a shift, by
#: least squares on the photo's green channel blurred as the photo is; the
#: points are in the drawing's own frame (inside ``PRINT_STRETCH_Y``).
ESP_TILE = (18.37, 2.09, 26.84, 10.51, 1.2)
ESPRESSIF_RINGS: Tuple[Tuple[Point, ...], ...] = (
    (
        (20.270, 5.134),
        (20.181, 5.279),
        (20.097, 5.468),
        (20.058, 5.661),
        (20.050, 5.899),
        (20.099, 6.138),
        (20.269, 6.419),
        (20.487, 6.613),
        (20.866, 6.786),
        (21.387, 6.894),
        (21.625, 7.028),
        (21.769, 7.189),
        (21.819, 7.270),
        (21.907, 7.508),
        (21.927, 7.747),
        (21.906, 7.985),
        (21.775, 8.321),
        (21.823, 8.422),
        (21.967, 8.547),
        (22.205, 8.660),
        (22.440, 8.705),
        (22.486, 8.695),
        (22.548, 8.651),
        (22.723, 8.268),
        (22.794, 7.932),
        (22.799, 7.503),
        (22.720, 7.124),
        (22.484, 6.697),
        (22.288, 6.473),
        (22.096, 6.298),
        (21.906, 6.176),
        (21.667, 6.065),
        (21.479, 6.014),
        (21.242, 5.980),
        (21.050, 5.903),
        (20.988, 5.846),
        (20.970, 5.752),
        (21.002, 5.687),
        (21.059, 5.655),
        (21.241, 5.641),
        (21.666, 5.731),
        (22.046, 5.889),
        (22.435, 6.171),
        (22.713, 6.498),
        (22.857, 6.702),
        (22.929, 6.837),
        (23.058, 7.171),
        (23.134, 7.552),
        (23.142, 7.740),
        (23.046, 8.313),
        (23.054, 8.426),
        (23.102, 8.481),
        (23.216, 8.551),
        (23.483, 8.612),
        (23.671, 8.582),
        (23.862, 8.478),
        (23.928, 8.359),
        (23.967, 8.168),
        (23.988, 7.548),
        (23.949, 7.117),
        (23.815, 6.690),
        (23.648, 6.309),
        (23.516, 6.095),
        (23.278, 5.788),
        (22.851, 5.385),
        (22.519, 5.162),
        (22.135, 4.964),
        (21.660, 4.810),
        (21.427, 4.776),
        (20.998, 4.769),
        (20.856, 4.789),
        (20.523, 4.917),
        (20.410, 4.991),
    ),
    (
        (21.008, 3.989),
        (20.961, 4.082),
        (20.937, 4.179),
        (20.937, 4.273),
        (20.971, 4.370),
        (21.093, 4.433),
        (21.612, 4.506),
        (21.947, 4.593),
        (22.466, 4.788),
        (22.898, 5.046),
        (23.229, 5.309),
        (23.515, 5.603),
        (23.711, 5.833),
        (23.998, 6.307),
        (24.146, 6.640),
        (24.204, 6.833),
        (24.265, 7.164),
        (24.321, 7.641),
        (24.356, 7.734),
        (24.427, 7.772),
        (24.665, 7.767),
        (24.761, 7.739),
        (24.806, 7.707),
        (25.033, 7.445),
        (25.133, 7.208),
        (25.130, 7.016),
        (25.050, 6.634),
        (24.989, 6.446),
        (24.809, 6.017),
        (24.581, 5.589),
        (24.329, 5.210),
        (24.129, 4.948),
        (23.747, 4.583),
        (23.319, 4.282),
        (22.558, 3.868),
        (22.231, 3.744),
        (21.895, 3.657),
        (21.562, 3.646),
        (21.421, 3.684),
        (21.285, 3.750),
        (21.136, 3.857),
    ),
    (
        (19.765, 4.851),
        (19.591, 5.521),
        (19.569, 5.759),
        (19.572, 6.282),
        (19.595, 6.566),
        (19.647, 6.804),
        (19.866, 7.375),
        (20.126, 7.804),
        (20.436, 8.185),
        (20.594, 8.323),
        (20.971, 8.611),
        (21.459, 8.892),
        (22.014, 9.093),
        (22.583, 9.166),
        (22.918, 9.169),
        (23.249, 9.137),
        (23.724, 9.034),
        (24.100, 8.883),
        (24.433, 8.721),
        (24.639, 8.592),
        (24.798, 8.446),
        (24.917, 8.303),
        (24.937, 8.208),
        (24.903, 8.148),
        (24.855, 8.118),
        (24.809, 8.113),
        (24.711, 8.160),
        (24.572, 8.292),
        (24.146, 8.585),
        (23.578, 8.810),
        (22.961, 8.903),
        (22.582, 8.905),
        (22.205, 8.864),
        (21.680, 8.709),
        (21.350, 8.570),
        (21.113, 8.434),
        (21.005, 8.323),
        (20.993, 8.277),
        (21.019, 8.227),
        (21.204, 8.157),
        (21.298, 8.098),
        (21.441, 7.946),
        (21.487, 7.843),
        (21.494, 7.702),
        (21.476, 7.559),
        (21.418, 7.462),
        (21.278, 7.323),
        (21.198, 7.285),
        (21.009, 7.258),
        (20.915, 7.266),
        (20.819, 7.306),
        (20.726, 7.372),
        (20.642, 7.467),
        (20.515, 7.753),
        (20.493, 7.771),
        (20.445, 7.772),
        (20.397, 7.744),
        (20.187, 7.422),
        (20.073, 7.184),
        (19.876, 6.565),
        (19.823, 6.184),
        (19.832, 5.469),
        (19.899, 5.185),
        (20.116, 4.660),
        (20.229, 4.515),
        (20.575, 3.991),
        (20.577, 3.896),
        (20.519, 3.825),
        (20.473, 3.811),
        (20.425, 3.823),
        (20.330, 3.891),
        (20.047, 4.279),
    ),
    (
        (22.503, 3.360),
        (22.484, 3.410),
        (22.510, 3.495),
        (22.556, 3.537),
        (23.175, 3.828),
        (23.498, 4.022),
        (23.794, 4.226),
        (24.120, 4.495),
        (24.412, 4.824),
        (24.908, 5.495),
        (25.224, 6.157),
        (25.320, 6.209),
        (25.414, 6.163),
        (25.440, 6.111),
        (25.449, 6.014),
        (25.441, 5.680),
        (25.410, 5.468),
        (25.366, 5.301),
        (25.054, 4.587),
        (24.908, 4.351),
        (24.746, 4.160),
        (24.530, 3.972),
        (24.264, 3.782),
        (23.695, 3.457),
        (23.363, 3.360),
        (23.050, 3.309),
        (22.793, 3.290),
        (22.555, 3.320),
    ),
)


def _smooth_ring(ring: Sequence[Point], steps: int = 4) -> List[Point]:
    """A closed ring through every one of its points on a centripetal Catmull-Rom spline,
    *steps* points a span, so its curves read round however near they are seen."""
    n = len(ring)
    out: List[Point] = []
    for i in range(n):
        p0, p1, p2, p3 = (ring[(i + k) % n] for k in (-1, 0, 1, 2))
        t1 = math.dist(p0, p1) ** 0.5
        t2 = t1 + math.dist(p1, p2) ** 0.5
        t3 = t2 + math.dist(p2, p3) ** 0.5
        for j in range(steps):
            t = t1 + (t2 - t1) * j / steps
            a1 = [((t1 - t) * p0[c] + t * p1[c]) / t1 for c in (0, 1)]
            a2 = [((t2 - t) * p1[c] + (t - t1) * p2[c]) / (t2 - t1) for c in (0, 1)]
            a3 = [((t3 - t) * p2[c] + (t - t2) * p3[c]) / (t3 - t2) for c in (0, 1)]
            b1 = [((t2 - t) * a1[c] + t * a2[c]) / t2 for c in (0, 1)]
            b2 = [((t3 - t) * a2[c] + (t - t1) * a3[c]) / (t3 - t1) for c in (0, 1)]
            out.append(tuple(((t2 - t) * b1[c] + (t - t1) * b2[c]) / (t2 - t1) for c in (0, 1)))
    return out


def append_espressif(out: List[str]) -> None:
    x0, y0, x1, y1, r = ESP_TILE
    out.append(rounded_rect(x0, y0, x1 - x0, y1 - y0, r, fill=VERMILION))
    d = " ".join(
        "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in _smooth_ring(ring)) + " Z"
        for ring in ESPRESSIF_RINGS
    )
    out.append(f'<path d="{d}" fill="{WHITE}" fill-rule="evenodd"/>\n')


def append_table(out: List[str]) -> None:
    """The M-BUS table's cells (their text is ``TEXT``) and its dashed frame and name."""
    for i, (left, right) in enumerate(CELLS):
        y = ROW0 + PITCH * i
        if left:
            x0 = L_FULL if left[1] else L_NARROW
            out.append(
                f'<rect x="{f(x0)}" y="{f(y)}" width="{f(L_END - x0)}" '
                f'height="{f(CELL_H)}" fill="{left[0]}"/>\n'
            )
        if right:
            x1 = R_WIDE if right[1] else R_END
            out.append(
                f'<rect x="{f(R_START)}" y="{f(y)}" width="{f(x1 - R_START)}" '
                f'height="{f(CELL_H)}" fill="{right[0]}"/>\n'
            )
    # the dashed frame: above the table to M-BUS, then from it down the right side
    # to the rule under the table (its dashes bend round the corners; the pitch and
    # phase of each rule are the photo's)
    out.extend(_dashes([(18.03, 11.28), (30.95, 11.28)], DARK_GRAY))
    out.extend(
        _dashes_bent(
            [
                (35.05, 11.28),
                (35.7, 11.28),
                (36.5, 12.5),
                (36.5, 38.75),
                (35.68, 40.04),
                (18.0, 40.04),
            ],
            DARK_GRAY,
            pitch=1.105,
            lead=0.159,
        )
    )
    # M-BUS, bold and slanted (Inter has no italic: its Bold sheared 12 degrees)
    out.append(
        '<text x="0" y="0" font-size="0.88" fill="' + BLACK + '" text-anchor="start" '
        'font-weight="700" textLength="3.36" lengthAdjust="spacingAndGlyphs" '
        'transform="translate(31.3 11.68) matrix(1 0 -0.2126 1 0 0)">M-BUS</text>\n'
    )


#: The microSD card's ``SD``: the label sets it in a condensed heavy grotesque
#: that no width of Inter comes near (its D's counter is a slit 0.2 mm wide),
#: so it is traced from the photo instead of set: the white over the card,
#: half-way between the card's black and the white, blurred by 1.8 px of the
#: photo's resampling, smoothed by 0.05 mm and simplified to 0.006 mm; the S,
#: then the D and its counter, as the rings of one even-odd shape (drawing
#: frame).
MICROSD_SD: Tuple[Tuple[Point, ...], ...] = (
    (
        (33.449, 48.326),
        (33.450, 48.500),
        (33.468, 48.649),
        (33.497, 48.748),
        (33.551, 48.850),
        (33.611, 48.924),
        (33.718, 49.023),
        (33.813, 49.090),
        (33.959, 49.174),
        (34.165, 49.337),
        (34.224, 49.425),
        (34.247, 49.545),
        (34.246, 49.648),
        (34.224, 49.725),
        (34.178, 49.774),
        (34.147, 49.784),
        (34.113, 49.781),
        (34.071, 49.750),
        (34.043, 49.699),
        (34.028, 49.619),
        (34.016, 49.419),
        (34.000, 49.377),
        (33.975, 49.349),
        (33.915, 49.326),
        (33.837, 49.320),
        (33.590, 49.324),
        (33.513, 49.347),
        (33.476, 49.392),
        (33.463, 49.444),
        (33.469, 49.645),
        (33.501, 49.818),
        (33.569, 49.967),
        (33.638, 50.038),
        (33.756, 50.118),
        (33.913, 50.182),
        (34.013, 50.206),
        (34.162, 50.212),
        (34.339, 50.197),
        (34.486, 50.154),
        (34.613, 50.089),
        (34.688, 50.036),
        (34.738, 49.987),
        (34.790, 49.895),
        (34.816, 49.818),
        (34.831, 49.670),
        (34.834, 49.446),
        (34.825, 49.321),
        (34.801, 49.221),
        (34.737, 49.085),
        (34.637, 48.965),
        (34.512, 48.862),
        (34.224, 48.676),
        (34.086, 48.563),
        (34.037, 48.479),
        (34.021, 48.348),
        (34.034, 48.283),
        (34.057, 48.242),
        (34.097, 48.217),
        (34.137, 48.215),
        (34.163, 48.226),
        (34.191, 48.261),
        (34.228, 48.453),
        (34.248, 48.496),
        (34.279, 48.523),
        (34.364, 48.540),
        (34.636, 48.541),
        (34.716, 48.526),
        (34.750, 48.504),
        (34.773, 48.471),
        (34.790, 48.375),
        (34.772, 48.176),
        (34.753, 48.101),
        (34.718, 48.026),
        (34.656, 47.954),
        (34.564, 47.883),
        (34.362, 47.815),
        (34.162, 47.788),
        (33.962, 47.792),
        (33.864, 47.806),
        (33.763, 47.842),
        (33.661, 47.892),
        (33.611, 47.930),
        (33.546, 48.002),
        (33.510, 48.054),
        (33.480, 48.126),
    ),
    (
        (35.135, 49.993),
        (35.144, 50.065),
        (35.161, 50.108),
        (35.193, 50.139),
        (35.235, 50.155),
        (35.313, 50.162),
        (35.938, 50.161),
        (36.162, 50.144),
        (36.286, 50.114),
        (36.388, 50.057),
        (36.476, 49.967),
        (36.524, 49.843),
        (36.543, 49.671),
        (36.548, 48.899),
        (36.541, 48.352),
        (36.522, 48.203),
        (36.487, 48.110),
        (36.416, 48.002),
        (36.336, 47.936),
        (36.186, 47.875),
        (35.962, 47.843),
        (35.264, 47.835),
        (35.194, 47.850),
        (35.156, 47.883),
        (35.136, 47.931),
        (35.131, 48.002),
    ),
    (
        (35.769, 49.706),
        (35.749, 49.664),
        (35.741, 49.594),
        (35.743, 48.378),
        (35.751, 48.321),
        (35.767, 48.288),
        (35.788, 48.269),
        (35.824, 48.260),
        (35.869, 48.275),
        (35.897, 48.307),
        (35.917, 48.355),
        (35.928, 48.425),
        (35.935, 48.699),
        (35.929, 49.520),
        (35.913, 49.640),
        (35.880, 49.702),
        (35.825, 49.730),
        (35.790, 49.724),
    ),
)


def append_parts(out: List[str]) -> None:
    """Every mark of the board's parts beside the table: cells, icons, arrows, rules."""
    # capacitive touch, vibration motor, power key
    out.append(rounded_rect(37.2, 9.45, 6.1, 1.4, 0.3, fill=BLUE))
    # the touch icon: a hand pointing up, an arc over its finger and two ticks beside
    out.append(
        f'<path d="M 42.18 13.13 V 12.0 Q 42.18 11.88 42.36 11.88 Q 42.54 11.88 42.54 12.0 '
        f"V 12.55 L 43.05 12.7 Q 43.15 12.72 43.14 12.82 L 43.11 13.35 Q 43.11 13.42 43.03 13.42 "
        f"H 42.3 Q 42.23 13.42 42.18 13.36 L 41.68 12.87 Q 41.63 12.79 41.72 12.77 H 41.92 "
        f'Q 42.01 12.79 42.18 12.99" fill="none" stroke="{BLACK}" stroke-width="0.16" '
        'stroke-linejoin="round" stroke-linecap="round"/>\n'
    )
    out.append(_arc(42.375, 12.14, 0.53, 170, 370, BLACK, 0.15, cap="round"))
    out.append(_arc(42.375, 12.14, 0.84, 160, 200, GRAY, 0.07))
    out.append(_arc(42.375, 12.14, 0.84, -20, 20, GRAY, 0.07))
    # the motor's two waves, mirror images: the left one sets off to the right, the right one
    # to the left, five and a half swings each
    for x, a in ((43.81, 0.13), (47.285, -0.13)):
        wave = [(x + a * math.sin(k * math.pi / 2), 10.41 + 0.193 * k) for k in range(12)]
        out.append(_line(wave, ORANGE, 0.13))
    out.append(
        f'<path d="M 44.42 9.653 H 46.67 V 13.202 H 44.42 Z" fill="none" stroke="{BLACK}" '
        'stroke-width="0.18" stroke-linejoin="miter"/>\n'
    )
    out.append(_text_turned(45.746, 11.465, "VIBRATION", 0.6, 3.51, 700, BLACK, -63))
    out.append(circle(45.53, 12.749, 0.165, fill=BLACK))
    # the power key's rule: straight dashes down its left, then one dash that turns the corner
    # (round, 0.6 mm, entered at 47 degrees) and the dashes along under AXP_PWR
    out.extend(
        _dashes_bent([(47.94, 9.14), (47.94, 15.27)], DARK_GRAY, dash=0.89, pitch=1.10, lead=-0.25)
    )
    turn = math.radians(47)
    out.extend(
        _dashes_bent(
            _corner(
                (48.54 - 0.6 * math.cos(turn), 15.0 + 0.6 * math.sin(turn)),
                (48.54, 15.0),
                (48.54, 15.6),
            )
            + [(52.31, 15.6)],
            DARK_GRAY,
            dash=0.89,
            pitch=1.10,
        )
    )
    out.append(_block_arrow((49.77, 10.28), (51.82, 10.28), VERMILION, 1.05, 0.62, 0.35))
    # LCD, RTC
    out.append(rounded_rect(37.24, 16.76, 9.03, 1.62, 0.32, fill=CYAN))
    out.append(rounded_rect(47.81, 16.41, 4.56, 3.09, 0.55, fill=MAGENTA))
    out.append(circle(46.38, 20.12, 1.25, stroke=GRAY, stroke_w=0.11))
    out.append(_line([(46.4, 19.38), (46.46, 20.28), (46.98, 20.33)], MAGENTA, 0.13, cap="round"))
    # USB bridge and the USB-C plug
    out.append(rounded_rect(40.71, 21.9, 3.86, 3.3, 0.42, fill=OLIVE))
    out.append(
        f'<path d="M 45.82 25.511 Q 45.45 25.014 44.98 24.815" fill="none" stroke="{BLACK}" '
        'stroke-width="0.09"/>\n'
    )
    out.append(_arrow_head((44.73, 24.666), (45.2, 24.95), BLACK, 0.34, 0.15))
    out.append(
        f'<path d="M 46.0 23.177 H 48.305 A 0.7 0.7 0 0 1 49.005 23.877 V 28.127 '
        f'A 0.7 0.7 0 0 1 48.305 28.827 H 46.0" fill="none" stroke="{BLACK}" '
        'stroke-width="0.61"/>\n'
    )
    out.append(
        f'<path d="M 49.005 24.192 H 51.74 V 27.801 H 49.005" fill="none" '
        f'stroke="{BLACK}" stroke-width="0.6" stroke-linejoin="miter"/>\n'
    )
    out.append(f'<rect x="50.35" y="25.044" width="0.53" height="0.538" fill="{BLACK}"/>\n')
    out.append(f'<rect x="50.35" y="26.398" width="0.53" height="0.557" fill="{BLACK}"/>\n')
    out.append(
        f'<path d="M 46.02 27.12 Q 44.86 27.75 44.82 29.6" fill="none" '
        f'stroke="{DARK_RED}" stroke-width="0.08"/>\n'
    )
    out.append(_arrow_head((44.82, 29.95), (44.82, 29.5), DARK_RED, 0.36, 0.15))
    # battery, PMIC, M5Stack
    out.append(
        f'<path d="M 38.69 27.53 H 39.73 A 0.4 0.4 0 0 1 40.13 27.93 V 34.0 '
        f"A 0.4 0.4 0 0 1 39.73 34.4 H 38.69 A 0.4 0.4 0 0 1 38.29 34.0 V 27.93 "
        f'A 0.4 0.4 0 0 1 38.69 27.53 Z" fill="none" stroke="{MAGENTA}" '
        'stroke-width="0.09"/>\n'
    )
    out.append(rounded_rect(38.63, 27.25, 1.07, 0.25, 0.1, fill=MAGENTA))
    out.append(_line([(40.4, 31.52), (40.72, 31.52)], BLACK, 0.07))
    out.append(rounded_rect(41.06, 30.1, 5.42, 5.45, 0.55, fill=DARK_RED))
    # M5Stack's cube: an open isometric box with a 5 on its top face
    out.append(
        f'<path d="M 48.04 29.99 L 49.56 29.33 L 50.86 29.87 M 48.04 29.99 L 49.59 30.65 '
        f'L 51.13 29.99 V 30.99 L 49.59 31.7 L 48.01 30.99 V 30.3" fill="none" stroke="{BLUE}" '
        'stroke-width="0.12" stroke-linejoin="round"/>\n'
    )
    out.append(
        f'<path d="M 49.53 29.63 L 48.84 29.97 Q 48.75 30.1 48.98 30.13 L 50.0 29.95 '
        f'Q 50.4 29.98 50.1 30.22 L 49.64 30.32" fill="none" stroke="{DARK_GRAY}" '
        'stroke-width="0.1" stroke-linejoin="round"/>\n'
    )
    out.append(rounded_rect(47.97, 33.43, 3.09, 1.47, 0.42, fill=BLUE))
    # the power tree: AXP_LDO0 to the 5V row and 5V BUS, 3V3, DC/DC, SY7088
    out.append(_line([(36.2, 36.32), (39.02, 36.32), (39.02, 37.35)], MAGENTA, 0.07))
    out.append(_arrow_head((35.95, 36.32), (36.6, 36.32), MAGENTA, 0.3, 0.13))
    out.append(_arrow_head((39.02, 37.68), (39.02, 37.2), MAGENTA, 0.3, 0.13))
    out.append(_line([(38.17, 37.63), (38.17, 36.86), (36.2, 36.86)], GRAY, 0.07))
    out.append(_arrow_head((35.95, 36.86), (36.6, 36.86), MAGENTA, 0.3, 0.13))
    # 5V BUS: its top corners round, its bottom ones all but square
    out.append(_cell(37.12, 37.71, 40.10, 40.24, 0.5, 0.06, DARK_RED))
    out.append(_line([(43.8, 35.75), (43.8, 36.78), (43.08, 36.78)], GRAY, 0.07))
    out.append(_arrow_head((42.8, 36.78), (43.3, 36.78), MAGENTA, 0.3, 0.13))
    out.append(_line([(44.34, 35.75), (44.34, 37.35)], GRAY, 0.07))
    out.append(_arrow_head((44.34, 37.66), (44.34, 37.2), MAGENTA, 0.3, 0.13))
    out.append(rounded_rect(42.03, 38.02, 5.33, 2.32, 0.4, fill=BLACK))
    out.append(_line([(42.0, 39.07), (40.5, 39.07)], GRAY, 0.07))
    out.append(_arrow_head((40.18, 39.07), (40.7, 39.07), MAGENTA, 0.3, 0.13))
    out.append(_line([(45.5, 40.5), (45.5, 41.34)], GRAY, 0.07))
    # AXP_'s underscore: the label sets it low, a bar over ExtEN's EN
    out.append(_line([(46.39, 42.714), (47.13, 42.714)], DARK_GRAY, 0.08))
    # Port A: a salmon frame round four cells, the frame's name up its side
    out.append(rounded_rect(47.98, 35.39, 3.96, 8.84, 0.3, fill=SALMON))
    for y0, y1, ink in (
        (35.63, 37.63, WHITE),
        (37.71, 39.8, YELLOW),
        (39.87, 41.88, DARK_RED),
        (42.03, 43.97, BLACK),
    ):
        out.append(
            f'<rect x="49.45" y="{f(y0)}" width="2.12" height="{f(y1 - y0)}" fill="{ink}"/>\n'
        )
    out.append(_text_turned(50.685, 36.816, "G33", 1.03, 2.02, 400, BLACK, -44.75))
    out.append(_text_turned(50.735, 38.946, "G32", 1.03, 2.02, 400, BLACK, -45.25))
    # audio
    out.append(rounded_rect(34.71, 41.67, 3.59, 3.05, 0.35, fill=TEAL))
    out.append(_line([(38.55, 42.77), (39.2, 42.77)], GRAY, 0.08))
    out.append(f'<rect x="39.32" y="42.19" width="0.55" height="1.16" fill="{GRAY}"/>\n')
    out.append(_poly([(40.08, 42.19), (40.95, 41.65), (40.95, 44.04), (40.08, 43.35)], BLACK))
    # three waves, each about a center of its own: gray, dark gray, black
    out.append(_arc(40.95, 42.85, 0.72, -45, 45, GRAY, 0.12))
    out.append(_arc(40.85, 42.85, 1.30, -52, 52, DARK_GRAY, 0.16))
    out.append(_arc(40.66, 42.85, 1.97, -51, 51, BLACK, 0.18))
    # IMU, microphone, the base board's arrow
    out.append(rounded_rect(20.98, 40.51, 3.58, 3.47, 0.4, fill=LIGHT_BLUE))
    out.append(_block_arrow((20.3, 46.68), (18.02, 45.08), BLACK, 1.15, 0.72, 0.385))
    out.append(rounded_rect(21.39, 44.68, 0.78, 1.54, 0.39, fill=ORANGE))
    out.append(_arc(21.78, 45.92, 0.82, 0, 180, BLACK, 0.2))
    out.append(f'<rect x="21.69" y="46.72" width="0.18" height="0.28" fill="{BLACK}"/>\n')
    out.append(_poly([(21.45, 47.12), (21.78, 46.94), (22.11, 47.12)], BLACK))
    # the rule round the audio and the IMU: down from the table, a steep bend and a shallow
    # one to the junction over the microSD's rule, then left under the IMU
    out.extend(
        _dashes_bent(
            [
                (29.49, 40.35),
                (29.49, 44.86),
                (29.33, 45.0),
                (28.95, 45.70),
                (28.30, 46.85),
                (28.10, 47.06),
                (26.45, 47.95),
            ],
            DARK_GRAY,
            pitch=1.11,
            lead=-0.70,
        )
    )
    out.extend(
        _dashes_bent(
            [(26.45, 47.95), (26.2, 47.84), (18.36, 47.84)], DARK_GRAY, pitch=1.113, lead=-0.57
        )
    )
    out.extend(
        _dashes_bent(
            [(26.18, 47.94), (26.52, 48.33), (26.52, 51.95)], DARK_GRAY, pitch=1.085, lead=-0.048
        )
    )
    # microSD
    out.append(
        _poly(
            [
                (33.06, 45.22),
                (36.62, 45.22),
                (37.38, 45.98),
                (37.38, 50.2),
                (37.03, 50.55),
                (33.06, 50.55),
                (32.71, 50.2),
                (32.71, 45.57),
            ],
            BLACK,
        )
    )
    for x in (33.13, 34.13, 35.14):
        out.append(f'<rect x="{f(x)}" y="45.6" width="0.7" height="0.93" fill="{YELLOW}"/>\n')
    sd = " ".join(
        "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in ring) + " Z" for ring in MICROSD_SD
    )
    out.append(f'<path d="{sd}" fill="{WHITE}" fill-rule="evenodd"/>\n')
    # reset arrow, LED
    out.append(_block_arrow((20.40, 49.70), (18.28, 51.25), CYAN, 1.25, 0.75, 0.41))
    out.append(_poly(_bulb(28.07, 51.19, 0.45, 0.25, 51.79), BLACK))
    out.append(_cell(27.88, 51.7, 28.26, 52.13, 0.0, 0.12, BLACK))
    out.append(_poly(_bulb(28.07, 51.19, 0.35, 0.15, 51.74), LED_GREEN))
    for a in (-180, -150, -120, -90, -60, -30, 0, 30, 150):
        t = math.radians(a)
        out.append(
            _line(
                [
                    (28.07 + 0.68 * math.cos(t), 51.19 + 0.68 * math.sin(t)),
                    (28.07 + 0.88 * math.cos(t), 51.19 + 0.88 * math.sin(t)),
                ],
                DARK_GRAY,
                0.11,
            )
        )


def append_back(out: List[str]) -> None:
    """The back sticker: its paper (outside the legend group, a solid of the model) and
    everything printed on it, one legend group on the plane ``sticker``."""
    out.append(f'<path d="{paper_path()}" fill="{PAPER}" stroke="#bdbdc1" stroke-width="0.1"/>\n')
    k = PRINT_STRETCH_Y
    out.append(print_open("back-label", "sticker"))
    out.append(f'<g transform="matrix(1 0 0 {f(k)} 0 {f(PRINT_TOP_Y * (1 - k))})">\n')
    append_espressif(out)
    append_table(out)
    append_parts(out)
    for x, y, content, size, length, weight, ink in TEXT:
        out.append(_run(x, y, content, size, length, weight, ink))
    for x, y, content, size, length, weight, ink in TEXT_UP:
        out.append(_text_up(x, y, content, size, length, weight, ink))
    out.append("</g>\n")
    out.append(LEGEND_CLOSE)


# ------------------------------------------------------------------ the top side
#: The rating label's paper is the model's ``label`` solid in the top side's
#: recess (x 10.92..26.98, z -14.18..-1.82). Its prints are measured on the
#: photo of the top side, which shows the label upright with the back edge
#: down: the frame ``(U, W)`` below is that photo's, U across from the
#: photo's left edge of the case (the case's right edge as the front is seen),
#: W up from the back edge, negative. The photo's label is 16.3 x 12.47 mm
#: and the model's recess 16.06 x 12.36; the prints are scaled to the model's
#: (0.982 across, 0.986 along) about the label's center and turned half round
#: into the top frame (u = 54 - U, v = -W).
TOP_PHOTO_CENTER = (35.17, -8.395)
TOP_MODEL_CENTER = (35.06, -8.5)
TOP_SCALE = (0.9816, 0.986)
TOP_BAND = GRAY  # the model's band behind CORE2 v1.3
TOP_TEXT = (
    (31.63, -5.34, "211-260310", 1.39, 8.02, 400, BLACK),
    (27.36, -4.09, "FCC ID: 2AN3WM5CORE2V11", 0.99, 15.69, 400, BLACK),
    (30.0, -2.59, "INPUT DC 5V/1A", 1.18, 10.25, 500, DARK_GRAY),
    (33.76, -7.3, "R", 0.58, 0.47, 400, BLACK),
)
TOP_TEXT_UP = (
    (42.93, -5.17, "CORE2", 2.46, 6.62, 900, BLACK),
    (42.94, -11.81, "v1.3", 1.0, 2.35, 700, BLACK),
)


def _ring_cut(cx: float, cy: float, outer: float, inner: float, cut_x: float, ink: str) -> str:
    """The part of a ring about (cx, cy) left of the vertical ``x = cut_x``: a CE letter's
    arc, its ends cut square to the line."""

    def half(r: float) -> float:
        return math.sqrt(r * r - (cut_x - cx) ** 2)

    ho, hi = half(outer), half(inner)
    return (
        f'<path d="M {f(cut_x)} {f(cy - ho)} A {f(outer)} {f(outer)} 0 1 0 {f(cut_x)} {f(cy + ho)} '
        f'L {f(cut_x)} {f(cy + hi)} A {f(inner)} {f(inner)} 0 1 1 {f(cut_x)} {f(cy - hi)} Z" '
        f'fill="{ink}"/>\n'
    )


def append_ce(out: List[str]) -> None:
    """The CE mark: two rings 0.8 mm thick, each cut by a vertical just right of its
    center, and the E's middle bar running out of its ring (half-max edges of the photo)."""
    out.append(_ring_cut(30.275, -11.15, 2.83, 2.02, 30.51, BLACK))
    out.append(_ring_cut(35.105, -11.15, 2.83, 2.02, 35.32, BLACK))
    out.append(f'<rect x="32.75" y="-11.57" width="1.98" height="0.84" fill="{BLACK}"/>\n')


def append_weee(out: List[str]) -> None:
    """The crossed-out wheelie bin (EN 50419) and the bar under it: a domed lid with its
    grip on top and a knob at its rear right, the lid's rim, a handle box on the rear
    wall, the tapered body with a slot, a foot at its front and the wheel at its back,
    crossed by two lines (half-max centerlines and widths of the photo)."""
    out.append(_line([(35.65, -13.93), (40.42, -8.88)], BLACK, 0.12))
    out.append(_line([(40.77, -13.93), (35.84, -8.90)], BLACK, 0.12))
    out.append(_line([(36.89, -12.97), (39.42, -12.97)], BLACK, 0.16))
    out.append(_line([(37.08, -12.97), (37.42, -13.37), (38.0, -13.37)], BLACK, 0.14))
    out.append(_line([(38.6, -13.37), (38.9, -13.37), (39.36, -13.12)], BLACK, 0.14))
    out.append(
        f'<path d="M 38.12 -13.45 H 38.5 A 0.1 0.1 0 0 1 38.6 -13.35 '
        f"A 0.1 0.1 0 0 1 38.5 -13.25 H 38.12 A 0.1 0.1 0 0 1 38.02 -13.35 "
        f'A 0.1 0.1 0 0 1 38.12 -13.45 Z" fill="none" stroke="{BLACK}" stroke-width="0.16"/>\n'
    )
    out.append(circle(39.45, -13.08, 0.16, fill=BLACK))
    out.append(
        f'<path d="M 39.36 -12.8 H 39.6 V -12.31 H 39.36 Z" fill="none" stroke="{BLACK}" '
        'stroke-width="0.12" stroke-linejoin="miter"/>\n'
    )
    out.append(_line([(37.13, -12.97), (37.40, -9.62)], BLACK, 0.16))
    out.append(_line([(39.33, -12.97), (39.06, -10.03)], BLACK, 0.16))
    out.append(_line([(37.40, -9.62), (38.80, -9.62)], BLACK, 0.18))
    out.append(f'<rect x="37.39" y="-9.62" width="0.29" height="0.29" fill="{BLACK}"/>\n')
    out.append(f'<rect x="37.92" y="-12.18" width="0.88" height="0.29" fill="{BLACK}"/>\n')
    out.append(circle(39.06, -9.76, 0.27, stroke=BLACK, stroke_w=0.18))
    out.append(circle(39.06, -9.76, 0.1, fill=BLACK))
    out.append(f'<rect x="36.09" y="-7.84" width="4.21" height="0.96" fill="{BLACK}"/>\n')


def append_fcc(out: List[str]) -> None:
    """FCC: an F whose arms run into two C's, one in the other, open to the right."""
    out.append(
        f'<path d="M 27.68 -5.48 V -7.77 H 29.6 V -7.25 H 28.07 V -6.81 H 29.1 V -6.37 '
        f'H 28.07 V -5.48 Z" fill="{BLACK}"/>\n'
    )
    out.append(_arc(30.02, -6.62, 0.95, 40, 320, BLACK, 0.42))
    out.append(_arc(30.02, -6.62, 0.38, 50, 310, BLACK, 0.34))


def append_giteki(out: List[str]) -> None:
    """Japan's radio mark: a ring broken on its right by a lightning stroke, two bars and a
    stem, and the boxed R beside it."""
    gx, gy, ring = 32.55, -7.25, 0.68
    start, end = math.radians(-18), math.radians(24)
    bolt = [
        (gx - 0.65, gy - 0.19),
        (gx - 0.02, gy - 0.31),
        (gx + 0.07, gy - 0.09),
        (gx + ring * math.cos(start), gy + ring * math.sin(start)),
    ]
    path = " L ".join(f"{f(px)} {f(py)}" for px, py in bolt)
    out.append(
        f'<path d="M {path} A {f(ring)} {f(ring)} 0 1 0 '
        f'{f(gx + ring * math.cos(end))} {f(gy + ring * math.sin(end))}" fill="none" '
        f'stroke="{BLACK}" stroke-width="0.08" stroke-linejoin="round"/>\n'
    )
    out.append(
        f'<path d="M {f(gx - 0.36)} {f(gy + 0.13)} H {f(gx + 0.39)} M {f(gx - 0.36)} '
        f'{f(gy + 0.3)} H {f(gx + 0.39)} M {f(gx + 0.02)} {f(gy + 0.3)} V {f(gy + 0.54)}" '
        f'fill="none" stroke="{BLACK}" stroke-width="0.07"/>\n'
    )
    out.append(
        f'<path d="M 33.58 -7.84 H 34.47 V -7.18 H 33.58 Z" fill="none" stroke="{BLACK}" '
        'stroke-width="0.06"/>\n'
    )


def append_top(out: List[str]) -> None:
    """The top side's rating label: one legend group on the plane ``rating``, drawn upright
    as the photo shows it and turned into the top frame by the transform just inside it."""
    (pu, pw), (mu, mw), (sx, sy) = TOP_PHOTO_CENTER, TOP_MODEL_CENTER, TOP_SCALE
    out.append(print_open("rating-label", "rating"))
    out.append(
        f'<g transform="rotate(180 27 0) translate({f(mu)} {f(mw)}) scale({f(sx)} {f(sy)}) '
        f'translate({f(-pu)} {f(-pw)})">\n'
    )
    out.append(f'<rect x="40.81" y="-14.48" width="2.42" height="9.29" fill="{TOP_BAND}"/>\n')
    out.append(
        f'<rect x="27.12" y="-3.93" width="16.1" height="1.71" rx="0.15" ry="0.15" '
        f'fill="{LIGHT_GRAY}"/>\n'
    )
    append_ce(out)
    append_weee(out)
    append_fcc(out)
    append_giteki(out)
    for x, y, content, size, length, weight, ink in TOP_TEXT:
        out.append(
            text(
                x,
                y,
                content,
                size=size,
                fill=ink,
                anchor="start",
                weight=str(weight),
                length=length,
            )
        )
    for x, y, content, size, length, weight, ink in TOP_TEXT_UP:
        out.append(_text_up(x, y, content, size, length, weight, ink))
    out.append("</g>\n")
    out.append(LEGEND_CLOSE)
