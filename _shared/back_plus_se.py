# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""The M5StickC Plus SE's back label, drawn in the back frame

The Plus SE's back carries one sticker, 21.06 x 37.25 mm, in the shell's
0.2 mm recess, its top edge at the header's top: the eight pin cells of the
HAT header across its top, the ``M5STICK CPlusSE`` banner, the BTN / BUZZER /
IR / LED fields, the ESP32 block with Espressif's mark, the LCD and microphone
lines, the battery, FCC, the model name and FCC ID, Japan's radio mark, CE and
the WEEE bin, the I2C pins, PMIC, RTC, SLEEP / WAKE, the baud rates,
M5Stack's cube and maker's lines, the HY2.0-4P port cells and PWR. Every
print is a legend group on the plane ``label``, which the model lays on its
``back_label`` paper (``m5stickc-plus-se/model/spec.json``,
``label_legends``).

Measured on one straight-on back photograph: M5Stack's documentation picture
(18.2 px/mm on the label). Pi Hut's back picture is the same photograph
cropped and rescaled (the case below the label correlates at r 0.998), so it
confirms nothing on its own. The photo was registered by a homography to a
provisional rectangle on the paper's four edges (``MEASURED``), and every
position, size and stroke below is a millimeter of that frame, x across from
the case's left edge as seen from behind, y down from its top. The paper's
real size and place (``PAPER``) come from the photo's case and from the
shell, and ``px`` / ``py`` carry each print from the measured frame onto it.
The paper's top edge carries about 0.3 mm of doubt: the photo's case
references disagree among themselves by that much.

**Type.** Inter is the only face a legend may be set in. The label's own
faces are a humanist sans for most lines, a heavy condensed one for the
banner and the LCD / MIC marks, and a geometric semibold for the model line;
each run is Inter at the weight nearest the print, its size taken from the
ink's height on the photo and its width pinned to the ink's (``textLength``),
so its box is the printed run's and its letterforms are Inter's.

**Inks.** Sampled on the photo, each a
flat color. Thin strokes blur into the paper on a photo, so a thin line's ink
is taken from its darkest pixels, not its mean.
"""

from __future__ import annotations

import math
import sys
from itertools import pairwise
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_front_svg as fronts

f = fronts.f

#: The rectangle the photo was registered to (back frame): every position,
#: size and stroke written below is a millimeter of this frame, as measured.
MEASURED = (1.6, 1.3, 22.4, 37.75)
#: The paper's measured size. Its width comes from the photo's case: the two
#: brass inserts' flanges, which lie in the label's plane, stand 15.80 mm
#: apart in the measured frame where the case puts them 15.99 apart, and the
#: shell's recess, which holds the paper, is 21.1 mm wide. Its length is the
#: photo's own aspect, 1.7688, at that width.
PAPER_WIDTH = 21.06
PHOTO_ASPECT = 1.7688
#: The paper's top edge: the header's top (build y 23.7), where the photo
#: shows the pin cells as the top edge of the back, nothing of the header or
#: the case above them. The photo's case references put it 0.1 to 0.7 mm
#: under the top end; this is that range's middle.
PAPER_TOP = 0.3
#: The map from the measured frame onto the paper: a scale about the label's
#: center line across, and one from the top edge down.
SX = PAPER_WIDTH / (MEASURED[2] - MEASURED[0])
SY = PAPER_WIDTH * PHOTO_ASPECT / (MEASURED[3] - MEASURED[1])
CX = 0.5 * (MEASURED[0] + MEASURED[2])
#: The label paper in the back frame: the model's ``back_label`` prism
#: (build x -10.53..10.53, y -13.55..23.7), its two top corners square,
#: where the pin cells run off its top edge, and its two bottom ones round.
PAPER = (
    CX - PAPER_WIDTH / 2,
    PAPER_TOP,
    CX + PAPER_WIDTH / 2,
    PAPER_TOP + PAPER_WIDTH * PHOTO_ASPECT,
)
PAPER_R = 0.8
#: The paper's own color, which the white prints match.
PAPER_INK = "#fcfcfa"
#: How far a print that runs to the paper's edge stays inside it, so no
#: corner of a sheet overhangs the paper it lies on.
EDGE = 0.02
PLANE = "label"

WHITE = PAPER_INK
BLACK = "#141414"
DARK_GRAY = "#302e2c"  # CE, the model line, M5STACK, (6S=OFF)
TEXT_GRAY = "#5f605f"  # the maker's lines, the baud rates, G33
LINE_GRAY = "#7f807f"  # the rule under M5STACK, the two key marks
RED = "#cd3203"  # the left 5V, ESP32, the V cell, PWR
RED_LIGHT = "#e74924"  # the right 5V
PINK = "#fb6662"  # BAT, LED
LCD_ORANGE = "#f8622f"
GRAY_LIGHT = "#e6e6e6"  # G26, G0
GRAY = "#cbcbca"  # G36/G25, the HY2.0-4P box, the BPS bar
GRAY_PALE = "#f3f4f3"  # the baud rates' field, the G33 cell
YELLOW = "#fcce02"  # 3V3, SLEEP, G32, the 5V arrow, OUT
ORANGE = "#fd8c26"  # the banner, SE
SKY = "#7bdaf5"  # BTN G39
BLUE = "#04a3e4"  # BTN G37
RTC_BLUE = "#008dd5"
MIC_BLUE = "#03639b"
CUBE_BLUE = "#1f74ad"  # M5Stack's cube
TAN = "#c78d52"  # BUZZER
MAGENTA = "#f80464"  # IR
GREEN = "#309965"  # PMIC
KHAKI = "#bac89b"  # WAKE
BATTERY_GRAY = "#a0a0a0"
BAR_GRAY = "#5c5c5c"  # the two bars beside the banner
MAROON = "#7c2a33"  # D:G34/C:G0, SDA:G21/SCL:G22/INT:G35
OLIVE = "#9a5a06"  # G32

# --- texts (fitted) ---
#: Each run as (name, text, weight, ink, x, y, size, length, angle): Inter
#: at ``size`` mm with its run pinned to ``length`` mm, starting at (x, y) on
#: its baseline and turned ``angle`` degrees about that point (-90 reads
#: bottom to top). Each is fitted to the ink box of the printed run measured
#: on the photos: Inter's own ink box of the same string, scaled into it.
TEXTS: list[tuple[str, str, int, str, float, float, float, float, float]] = [
    ("pin-gnd", "GND", 400, WHITE, 3.766, 6.812, 2.191, 5.125, -90),
    ("pin-5v-in", "5V", 400, WHITE, 6.329, 6.655, 2.136, 2.671, -90),
    ("pin-g26", "G26", 400, BLACK, 8.953, 6.354, 2.209, 4.283, -90),
    ("pin-g36", "G36", 400, BLACK, 10.817, 7.031, 1.365, 2.692, -90),
    ("pin-g25", "G25", 400, BLACK, 11.660, 4.027, 1.057, 2.535, -90),
    ("pin-g0", "G0", 400, BLACK, 14.153, 5.702, 2.209, 2.942, -90),
    ("pin-bat", "BAT", 400, WHITE, 16.750, 6.335, 2.165, 4.199, -90),
    ("pin-3v3", "3V3", 400, BLACK, 19.378, 6.253, 2.209, 4.027, -90),
    ("pin-5v-out", "5V", 400, WHITE, 21.904, 6.719, 2.154, 2.684, -90),
    ("banner-m5stick", "M5STICK", 700, WHITE, 2.507, 10.545, 2.758, 9.142, 0),
    ("banner-cplus", "CPlus", 700, BLACK, 12.820, 10.546, 2.691, 5.754, 0),
    ("banner-se", "SE", 700, ORANGE, 18.726, 10.572, 2.573, 3.001, 0),
    ("field-btn39", "BTN", 400, BLACK, 3.226, 13.225, 1.443, 2.898, 0),
    ("field-g39", "G39", 400, BLACK, 3.611, 14.339, 1.104, 2.128, 0),
    ("field-btn37", "BTN", 400, BLACK, 6.925, 13.250, 1.478, 2.925, 0),
    ("field-g37", "G37", 400, BLACK, 7.336, 14.339, 1.104, 2.079, 0),
    ("field-buzzer", "BUZZER", 400, WHITE, 10.593, 13.064, 0.947, 4.201, 0),
    ("field-g2", "G2", 400, WHITE, 11.943, 14.364, 1.088, 1.578, 0),
    ("field-ir", "IR", 400, WHITE, 15.801, 13.087, 1.219, 1.163, 0),
    ("field-g9", "G9", 400, WHITE, 15.686, 14.365, 1.071, 1.479, 0),
    ("field-led", "LED", 400, WHITE, 18.341, 13.100, 1.237, 2.332, 0),
    ("field-g10", "G10", 400, WHITE, 18.326, 14.376, 1.087, 2.224, 0),
    ("esp-esp32", "ESP32", 500, WHITE, 7.088, 16.434, 1.301, 3.880, 0),
    ("esp-pico", "PICO(4M)", 500, WHITE, 7.106, 17.722, 1.033, 4.806, 0),
    ("lcdmic-lcd", "LCD", 700, LCD_ORANGE, 15.140, 18.177, 2.326, 3.149, -90),
    ("lcdmic-mic", "MIC", 700, MIC_BLUE, 15.152, 21.206, 2.342, 2.395, -90),
    ("line-tft", "1.14 TFT,135x240", 400, BLACK, 15.465, 15.625, 0.712, 6.180, 0),
    ("line-st7789", "ST7789V2", 400, BLACK, 15.431, 17.082, 1.433, 6.082, 0),
    ("line-pins", "G15/13/23/18/5", 400, BLACK, 15.407, 18.129, 0.876, 6.549, 0),
    ("line-spm", "SPM1423", 400, BLACK, 15.419, 19.902, 1.413, 6.391, 0),
    ("line-mic-pins", "D:G34/C:G0", 400, MAROON, 15.415, 20.948, 0.932, 6.401, 0),
    ("batt-battery", "BATTERY:", 700, WHITE, 2.767, 19.611, 1.018, 4.811, 0),
    ("batt-mah", "120mAh", 700, WHITE, 3.245, 20.510, 0.977, 3.966, 0),
    ("model-name", "Model Name: M5StickC Plus SE", 500, DARK_GRAY, 2.089, 21.766, 0.732, 11.357, 0),
    ("model-fccid", "FCCID: 2AN3WM5STICKCPLUS", 500, DARK_GRAY, 2.090, 22.481, 0.720, 11.374, 0),
    ("giteki-r", "R", 400, BLACK, 5.640, 24.113, 0.877, 0.535, 0),
    ("giteki-number", "211-251212", 400, BLACK, 6.845, 24.275, 1.289, 6.344, 0),
    ("i2c-pins", "SDA:G21/SCL:G22/INT:G35", 400, MAROON, 14.792, 31.178, 0.646, 9.258, -90),
    ("chip-pmic", "PMIC", 400, WHITE, 16.242, 23.944, 1.857, 4.582, 0),
    ("chip-axp192", "AXP192", 400, WHITE, 15.914, 25.311, 1.439, 5.227, 0),
    ("chip-rtc", "RTC", 400, WHITE, 15.884, 28.749, 1.355, 2.393, 0),
    ("chip-bm8563", "BM8563", 400, WHITE, 15.220, 29.632, 0.870, 3.654, 0),
    ("chip-sleep", "SLEEP", 700, BLACK, 19.507, 27.830, 0.634, 2.271, 0),
    ("chip-wake", "WAKE", 700, BLACK, 19.521, 30.137, 0.687, 2.256, 0),
    ("maker-m5stack", "M5STACK", 400, DARK_GRAY, 2.526, 34.728, 0.907, 4.650, 0),
    ("maker-line1", "M5Stack", 500, TEXT_GRAY, 3.051, 35.871, 0.760, 3.598, 0),
    ("maker-line2", "Technology", 500, TEXT_GRAY, 2.453, 36.574, 0.721, 4.837, 0),
    ("maker-line3", "Co.,Ltd.", 500, TEXT_GRAY, 3.314, 37.222, 0.599, 3.132, 0),
    ("bps-bps", "BPS", 400, BLACK, 13.306, 32.337, 1.000, 2.364, 0),
    (
        "bps-rates",
        "1200~115200/250K/500K/750K/1.5M",
        400,
        TEXT_GRAY,
        7.361,
        33.297,
        0.833,
        14.375,
        0,
    ),
    ("port-name", "HY2.0-4P", 700, BLACK, 9.315, 34.780, 1.057, 5.558, 0),
    ("port-g", "G", 400, WHITE, 8.611, 36.634, 1.657, 1.120, 0),
    ("port-v", "V", 400, WHITE, 10.497, 36.280, 1.636, 1.166, 0),
    ("port-out", "OUT", 700, YELLOW, 10.286, 36.932, 0.749, 1.601, 0),
    ("port-g32", "G32", 400, OLIVE, 12.494, 36.890, 0.857, 1.799, -42),
    ("port-g33", "G33", 400, TEXT_GRAY, 14.554, 36.887, 0.937, 1.894, -42),
    ("pwr-pwr", "PWR", 400, RED, 17.082, 35.550, 1.787, 4.600, 0),
    ("pwr-off", "(6S=OFF)", 400, DARK_GRAY, 16.840, 36.966, 1.349, 5.270, 0),
]
# --- end texts ---


#: A radius or a stroke width, which the map scales by both factors' mean.
K = math.sqrt(SX * SY)


def px(x: float) -> float:
    """A measured-frame x on the paper."""
    return CX + SX * (x - CX)


def py(y: float) -> float:
    """A measured-frame y on the paper."""
    return PAPER_TOP + SY * (y - MEASURED[1])


def pts(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{f(px(x))},{f(py(y))}" for x, y in points)


def run(
    text: str, weight: int, ink: str, x: float, y: float, size: float, length: float, angle: float
) -> str:
    """One text run, turned ``angle`` degrees about its start, all in the
    measured frame: its run scales along its direction, its size across it."""
    a = math.radians(angle)
    along = math.hypot(SX * math.cos(a), SY * math.sin(a))
    across = math.hypot(SX * math.sin(a), SY * math.cos(a))
    turned = math.degrees(math.atan2(SY * math.sin(a), SX * math.cos(a)))
    x, y = px(x), py(y)
    element = fronts.text(
        x,
        y,
        text,
        size=size * across,
        fill=ink,
        anchor="start",
        weight=str(weight),
        length=length * along,
    )
    if angle:
        return f'<g transform="rotate({f(turned)} {f(x)} {f(y)})">\n{element}</g>\n'
    return element


def rect(x0: float, y0: float, x1: float, y1: float, ink: str, r: float = 0.0) -> str:
    return fronts.rounded_rect(px(x0), py(y0), SX * (x1 - x0), SY * (y1 - y0), r=r * K, fill=ink)


def circle(cx: float, cy: float, r: float, **style: Any) -> str:
    if "stroke_w" in style:
        style["stroke_w"] *= K
    return fronts.circle(px(cx), py(cy), r * K, **style)


def polygon(points: list[tuple[float, float]], ink: str) -> str:
    return f'<polygon points="{pts(points)}" fill="{ink}"/>\n'


def line(points: list[tuple[float, float]], ink: str, width: float, cap: str = "round") -> str:
    d = " L ".join(f"{f(px(x))} {f(py(y))}" for x, y in points)
    return (
        f'<path d="M {d}" fill="none" stroke="{ink}" stroke-width="{f(width * K)}" '
        f'stroke-linecap="{cap}" stroke-linejoin="round"/>\n'
    )


def outline(x0: float, y0: float, x1: float, y1: float, ink: str, width: float) -> str:
    """A rectangle's outline, square cornered."""
    return (
        f'<path d="M {f(px(x0))} {f(py(y0))} H {f(px(x1))} V {f(py(y1))} '
        f'H {f(px(x0))} Z" fill="none" stroke="{ink}" stroke-width="{f(width * K)}" '
        f'stroke-linejoin="miter"/>\n'
    )


def arc(
    cx: float,
    cy: float,
    r: float,
    start_deg: float,
    end_deg: float,
    ink: str,
    width: float,
    cap: str = "butt",
) -> str:
    """A circular arc from ``start_deg`` to ``end_deg`` (page angles, y down),
    the way the angle falls: counterclockwise on the page."""
    a0, a1 = math.radians(start_deg), math.radians(end_deg)
    turn = (start_deg - end_deg) % 360
    cx, cy, r = px(cx), py(cy), r * K
    return (
        f'<path d="M {f(cx + r * math.cos(a0))} {f(cy + r * math.sin(a0))} '
        f"A {f(r)} {f(r)} 0 {1 if turn > 180 else 0} 0 "
        f'{f(cx + r * math.cos(a1))} {f(cy + r * math.sin(a1))}" fill="none" '
        f'stroke="{ink}" stroke-width="{f(width * K)}" stroke-linecap="{cap}"/>\n'
    )


def ring_c(cx: float, cy: float, outer: float, inner: float, cut_x: float, ink: str) -> str:
    """The CE mark's letter shape: a ring open to the right, its two ends cut
    upright at x = ``cut_x``."""
    cx, cy, outer, inner, cut_x = px(cx), py(cy), outer * K, inner * K, px(cut_x)
    do = math.sqrt(outer * outer - (cut_x - cx) ** 2)
    di = math.sqrt(inner * inner - (cut_x - cx) ** 2)
    return (
        f'<path d="M {f(cut_x)} {f(cy - do)} '
        f"A {f(outer)} {f(outer)} 0 1 0 {f(cut_x)} {f(cy + do)} "
        f"L {f(cut_x)} {f(cy + di)} "
        f'A {f(inner)} {f(inner)} 0 1 1 {f(cut_x)} {f(cy - di)} Z" '
        f'fill="{ink}"/>\n'
    )


def texts(prefix: str) -> list[str]:
    """The fitted runs whose names start with ``prefix``."""
    return [
        run(t, w, ink, x, y, s, n, a)
        for name, t, w, ink, x, y, s, n, a in TEXTS
        if name.startswith(prefix)
    ]


def group(out: list[str], name: str, body: list[str]) -> None:
    out.append(fronts.print_open(name, PLANE))
    out.extend(body)
    out.append(fronts.LEGEND_CLOSE)


def paper_path() -> str:
    """The paper's outline: square at the top, round at the bottom."""
    x0, y0, x1, y1 = PAPER
    r = PAPER_R
    return (
        f"M {f(x0)} {f(y0)} H {f(x1)} V {f(y1 - r)} "
        f"A {f(r)} {f(r)} 0 0 1 {f(x1 - r)} {f(y1)} H {f(x0 + r)} "
        f"A {f(r)} {f(r)} 0 0 1 {f(x0)} {f(y1 - r)} Z"
    )


# Pin cells: their edges across the label, on the photo's color changes.
# (measured frame; the two outer edges and the top are the paper's own, EDGE
# inside it once mapped)
PIN_EDGES = (
    MEASURED[0] + EDGE / SX,
    4.19,
    6.82,
    9.47,
    12.02,
    14.66,
    17.26,
    19.87,
    MEASURED[2] - EDGE / SX,
)
PIN_TOP, PIN_BOTTOM = MEASURED[1] + EDGE / SY, 7.19
PIN_INKS = (BLACK, RED, GRAY_LIGHT, GRAY, GRAY_LIGHT, PINK, YELLOW, RED_LIGHT)


def append_pins(out: list[str]) -> None:
    """The eight header pins, GND at the left as the back is seen."""
    cells = [
        rect(x0, PIN_TOP, x1, PIN_BOTTOM, ink)
        for (x0, x1), ink in zip(pairwise(PIN_EDGES), PIN_INKS, strict=True)
    ]
    group(out, "pin-cells", cells)
    # 5V in: an arrow up beside the left 5V; 5V out: an arrow down.
    up_arrow = polygon(
        [
            (5.525, 1.75),
            (6.312, 2.62),
            (5.83, 2.62),
            (5.83, 3.45),
            (5.22, 3.45),
            (5.22, 2.62),
            (4.737, 2.62),
        ],
        YELLOW,
    )
    down_arrow = polygon(
        [
            (20.89, 1.79),
            (21.49, 1.79),
            (21.49, 2.63),
            (21.975, 2.63),
            (21.188, 3.463),
            (20.4, 2.63),
            (20.89, 2.63),
        ],
        WHITE,
    )
    group(
        out,
        "pin-names",
        texts("pin-") + [up_arrow, down_arrow, line([(9.83, 3.78), (11.77, 4.49)], BLACK, 0.12)],
    )


# The banner: a frame round both words, filled orange up to a slanted edge.
BANNER = (2.12, 7.53, 21.97, 11.63)
BANNER_STROKE = 0.2
BANNER_R = 0.45
BANNER_SLANT = ((11.95, 7.63), (12.85, 11.53))


def append_banner(out: list[str]) -> None:
    (tx, ty), (bx, by) = BANNER_SLANT
    # the slanted edge carried out to the frame's outer edges
    k = (bx - tx) / (by - ty)
    top_x, bottom_x = px(tx + k * (BANNER[1] - ty)), px(tx + k * (BANNER[3] - ty))
    x0, y0, x1, y1 = px(BANNER[0]), py(BANNER[1]), px(BANNER[2]), py(BANNER[3])
    h = BANNER_STROKE * K / 2
    r = BANNER_R * K
    fill = (
        f'<path d="M {f(top_x)} {f(y0)} L {f(bottom_x)} {f(y1)} H {f(x0 + r)} '
        f"A {f(r)} {f(r)} 0 0 1 {f(x0)} {f(y1 - r)} V {f(y0 + r)} "
        f'A {f(r)} {f(r)} 0 0 1 {f(x0 + r)} {f(y0)} Z" fill="{ORANGE}"/>\n'
    )
    ri = r - h
    frame = (
        f'<path d="M {f(top_x)} {f(y0 + h)} H {f(x1 - h - ri)} '
        f"A {f(ri)} {f(ri)} 0 0 1 {f(x1 - h)} {f(y0 + h + ri)} "
        f"V {f(y1 - h - ri)} A {f(ri)} {f(ri)} 0 0 1 {f(x1 - h - ri)} {f(y1 - h)} "
        f'H {f(bottom_x)}" fill="none" stroke="{ORANGE}" '
        f'stroke-width="{f(BANNER_STROKE * K)}" stroke-linecap="butt" '
        f'stroke-linejoin="round"/>\n'
    )
    group(
        out,
        "banner-bars",
        [
            rect(1.7, 8.17, BANNER[0], 10.87, BAR_GRAY),
            rect(BANNER[2] + 0.02, 8.18, MEASURED[2] - EDGE / SX, 10.82, BAR_GRAY),
        ],
    )
    group(out, "banner", [fill, frame] + texts("banner-"))


#: The four fields under the banner, and BUZZER's: (x0, y0, x1, y1, ink).
FIELDS = (
    (2.95, 11.84, 6.40, 14.70, SKY),
    (6.675, 11.875, 10.075, 14.675, BLUE),
    (10.39, 11.875, 15.075, 14.70, TAN),
    (15.40, 11.90, 17.46, 14.70, MAGENTA),
    (17.775, 11.90, 21.175, 14.725, PINK),
)
FIELD_R = 0.3


def append_fields(out: list[str]) -> None:
    group(
        out,
        "fields",
        [rect(x0, y0, x1, y1, ink, FIELD_R) for x0, y0, x1, y1, ink in FIELDS] + texts("field-"),
    )
    # BtnB's mark beside BTN G39: a short curved stroke from the label's edge.
    group(
        out,
        "btn-b-mark",
        [
            f'<path d="M {f(px(1.98))} {f(py(12.27))} Q {f(px(2.18))} {f(py(12.95))} '
            f'{f(px(2.72))} {f(py(13.22))}" fill="none" '
            f'stroke="{LINE_GRAY}" stroke-width="{f(0.13 * K)}" stroke-linecap="round"/>\n'
        ],
    )


# --- Espressif mark (traced) ---
#: Espressif's mark, the white the print shows on the ESP32 block: its outer
#: arc, the banded body cut by three red arcs about the dot, and the dot in
#: its red ring, as the rings of one even-odd shape (measured frame). Traced
#: on the documentation picture as the half-way isoline between the block's
#: red and the white, smoothed by 0.025 mm and simplified to 0.006 mm.
ESPRESSIF_RINGS: list[list[tuple[float, float]]] = [
    [
        (3.888, 15.908),
        (3.712, 15.974),
        (3.652, 16.012),
        (3.578, 16.087),
        (3.530, 16.163),
        (3.486, 16.262),
        (3.464, 16.363),
        (3.460, 16.488),
        (3.485, 16.613),
        (3.574, 16.762),
        (3.688, 16.864),
        (3.888, 16.955),
        (4.162, 17.013),
        (4.287, 17.085),
        (4.362, 17.169),
        (4.389, 17.212),
        (4.435, 17.337),
        (4.445, 17.462),
        (4.433, 17.587),
        (4.363, 17.763),
        (4.388, 17.817),
        (4.463, 17.882),
        (4.588, 17.942),
        (4.713, 17.967),
        (4.737, 17.961),
        (4.769, 17.938),
        (4.863, 17.738),
        (4.901, 17.562),
        (4.905, 17.337),
        (4.864, 17.137),
        (4.741, 16.913),
        (4.638, 16.795),
        (4.537, 16.703),
        (4.438, 16.638),
        (4.312, 16.579),
        (4.213, 16.552),
        (4.088, 16.534),
        (3.987, 16.493),
        (3.954, 16.462),
        (3.945, 16.413),
        (3.962, 16.379),
        (3.992, 16.363),
        (4.088, 16.356),
        (4.312, 16.404),
        (4.512, 16.488),
        (4.716, 16.637),
        (4.862, 16.809),
        (4.938, 16.917),
        (4.975, 16.988),
        (5.042, 17.163),
        (5.081, 17.363),
        (5.085, 17.462),
        (5.033, 17.762),
        (5.037, 17.821),
        (5.062, 17.851),
        (5.122, 17.887),
        (5.263, 17.920),
        (5.362, 17.905),
        (5.463, 17.851),
        (5.498, 17.788),
        (5.519, 17.688),
        (5.532, 17.363),
        (5.512, 17.137),
        (5.443, 16.913),
        (5.356, 16.712),
        (5.287, 16.600),
        (5.162, 16.438),
        (4.938, 16.226),
        (4.763, 16.107),
        (4.562, 16.003),
        (4.312, 15.921),
        (4.188, 15.903),
        (3.962, 15.898),
    ],
    [
        (4.188, 15.329),
        (4.116, 15.363),
        (4.037, 15.419),
        (3.970, 15.488),
        (3.944, 15.537),
        (3.932, 15.588),
        (3.932, 15.637),
        (3.949, 15.688),
        (4.013, 15.722),
        (4.287, 15.761),
        (4.463, 15.807),
        (4.737, 15.911),
        (4.963, 16.048),
        (5.138, 16.187),
        (5.287, 16.341),
        (5.390, 16.462),
        (5.540, 16.712),
        (5.617, 16.887),
        (5.647, 16.988),
        (5.678, 17.163),
        (5.707, 17.413),
        (5.725, 17.462),
        (5.763, 17.482),
        (5.888, 17.480),
        (5.938, 17.466),
        (5.963, 17.449),
        (6.083, 17.312),
        (6.136, 17.188),
        (6.135, 17.087),
        (6.094, 16.887),
        (6.063, 16.788),
        (5.968, 16.562),
        (5.849, 16.337),
        (5.717, 16.137),
        (5.612, 15.999),
        (5.412, 15.807),
        (5.188, 15.648),
        (4.787, 15.429),
        (4.615, 15.363),
        (4.438, 15.316),
        (4.263, 15.310),
    ],
    [
        (3.612, 15.435),
        (3.462, 15.638),
        (3.312, 15.938),
        (3.218, 16.288),
        (3.207, 16.413),
        (3.207, 16.688),
        (3.218, 16.837),
        (3.245, 16.962),
        (3.359, 17.262),
        (3.495, 17.488),
        (3.657, 17.688),
        (3.740, 17.762),
        (3.939, 17.913),
        (4.195, 18.062),
        (4.487, 18.169),
        (4.787, 18.208),
        (4.963, 18.211),
        (5.138, 18.195),
        (5.388, 18.142),
        (5.588, 18.064),
        (5.763, 17.980),
        (5.872, 17.913),
        (5.956, 17.837),
        (6.020, 17.762),
        (6.030, 17.712),
        (6.013, 17.680),
        (5.987, 17.665),
        (5.963, 17.662),
        (5.912, 17.686),
        (5.838, 17.755),
        (5.612, 17.908),
        (5.312, 18.024),
        (4.987, 18.072),
        (4.787, 18.072),
        (4.588, 18.050),
        (4.312, 17.966),
        (4.138, 17.893),
        (4.013, 17.821),
        (3.957, 17.762),
        (3.951, 17.738),
        (3.964, 17.712),
        (4.062, 17.676),
        (4.112, 17.645),
        (4.188, 17.566),
        (4.212, 17.512),
        (4.217, 17.438),
        (4.207, 17.363),
        (4.177, 17.312),
        (4.104, 17.238),
        (4.062, 17.218),
        (3.962, 17.204),
        (3.912, 17.208),
        (3.862, 17.228),
        (3.812, 17.262),
        (3.768, 17.312),
        (3.700, 17.462),
        (3.688, 17.472),
        (3.663, 17.472),
        (3.638, 17.457),
        (3.528, 17.288),
        (3.468, 17.163),
        (3.366, 16.837),
        (3.340, 16.637),
        (3.346, 16.262),
        (3.382, 16.113),
        (3.498, 15.838),
        (3.558, 15.762),
        (3.742, 15.488),
        (3.743, 15.438),
        (3.712, 15.401),
        (3.688, 15.394),
        (3.663, 15.400),
    ],
    [
        (4.787, 15.141),
        (4.760, 15.162),
        (4.749, 15.188),
        (4.763, 15.233),
        (4.787, 15.255),
        (5.112, 15.409),
        (5.283, 15.512),
        (5.438, 15.619),
        (5.609, 15.762),
        (5.762, 15.935),
        (6.022, 16.288),
        (6.187, 16.637),
        (6.237, 16.664),
        (6.287, 16.640),
        (6.301, 16.613),
        (6.306, 16.562),
        (6.303, 16.387),
        (6.287, 16.275),
        (6.264, 16.188),
        (6.101, 15.812),
        (6.025, 15.688),
        (5.940, 15.588),
        (5.827, 15.488),
        (5.687, 15.388),
        (5.388, 15.216),
        (5.213, 15.164),
        (5.048, 15.137),
        (4.912, 15.126),
    ],
]
# --- end Espressif mark ---


def append_esp32(out: list[str]) -> None:
    """The ESP32 block: Espressif's mark in white, ESP32 PICO(4M)."""
    d = " ".join(
        "M " + " L ".join(f"{f(px(x))} {f(py(y))}" for x, y in ring) + " Z"
        for ring in ESPRESSIF_RINGS
    )
    mark = f'<path d="{d}" fill="{WHITE}" fill-rule="evenodd"/>\n'
    group(out, "esp32", [rect(2.2, 14.99, 12.79, 18.375, RED, 0.35), mark] + texts("esp-"))


def append_display_and_mic(out: list[str]) -> None:
    group(out, "lcd-mic", texts("lcdmic-"))
    group(out, "lcd-mic-lines", texts("line-"))


def append_battery(out: list[str]) -> None:
    group(
        out,
        "battery",
        [
            rect(2.14, 18.6, 8.2, 20.82, BATTERY_GRAY, 0.3),
            rect(8.38, 18.98, 8.9, 20.45, BATTERY_GRAY, 0.15),
        ]
        + texts("batt-"),
    )


def append_fcc(out: list[str]) -> None:
    """FCC's mark: the F, then the outer C round the inner one, both open to
    the right."""
    group(
        out,
        "fcc",
        [
            rect(9.79, 18.75, 10.11, 20.7, BLACK),
            rect(9.79, 18.75, 10.8, 19.1, BLACK),
            rect(9.79, 19.65, 10.9, 19.89, BLACK),
            arc(11.655, 19.775, 0.8, 332, 28, BLACK, 0.25),
            arc(11.67, 19.77, 0.45, 323, 37, BLACK, 0.25),
        ],
    )


def append_model(out: list[str]) -> None:
    group(out, "model-name", texts("model-"))


def append_giteki(out: list[str]) -> None:
    """Japan's radio mark: a ring broken on its right by a lightning stroke,
    over a stem with two bars; then the R in its box and the number."""
    cx, cy, r = 4.05, 23.79, 1.025
    bolt = [(3.06, 23.6), (4.1, 23.34), (4.12, 23.72), (4.85, 23.45)]
    body = [
        arc(cx, cy, r, -22, 25, BLACK, 0.1),
        line(bolt, BLACK, 0.1),
        line([(3.45, 23.98), (4.6, 23.98)], BLACK, 0.1, "butt"),
        line([(3.45, 24.27), (4.6, 24.27)], BLACK, 0.1, "butt"),
        line([(4.02, 24.27), (4.02, 24.56)], BLACK, 0.1, "butt"),
        outline(5.32, 23.24, 6.56, 24.36, BLACK, 0.08),
    ]
    group(out, "giteki", body + texts("giteki-"))


def append_ce_weee(out: list[str]) -> None:
    group(
        out,
        "ce",
        [
            ring_c(4.64, 28.4, 2.65, 1.9, 4.9, DARK_GRAY),
            ring_c(9.25, 28.4, 2.65, 1.9, 9.55, DARK_GRAY),
            rect(7.2, 28.07, 9.0, 28.77, DARK_GRAY),
        ],
    )
    # The bin: its body down to the wheel, its domed lid in outline over the
    # lid's bar, the outlined handle on the lid and the hinge box at its
    # right end, the bar on the body, the foot and the wheel (a thick ring
    # round a dot).
    bin_body = [(10.83, 25.3), (11.04, 28.415), (12.25, 28.415)]
    group(
        out,
        "weee",
        [
            line([(9.45, 24.4), (13.88, 29.12)], BLACK, 0.1),
            line([(14.12, 24.5), (9.5, 29.15)], BLACK, 0.1),
            line(bin_body, BLACK, 0.12),
            line([(12.81, 25.3), (12.6, 27.95)], BLACK, 0.12),
            line(
                [
                    (10.56, 25.27),
                    (11.0, 24.84),
                    (12.25, 24.84),
                    (12.65, 24.92),
                    (12.9, 25.05),
                    (12.9, 25.27),
                ],
                BLACK,
                0.11,
            ),
            line([(10.56, 25.27), (12.9, 25.27)], BLACK, 0.15),
            outline(11.67, 24.79, 12.17, 25.02, BLACK, 0.1),
            outline(12.94, 25.05, 13.14, 25.97, BLACK, 0.07),
            rect(11.575, 26.01, 12.39, 26.3, BLACK),
            circle(12.6, 28.33, 0.3, fill="none", stroke=BLACK, stroke_w=0.165),
            circle(12.6, 28.33, 0.115, fill=BLACK),
            rect(11.05, 28.42, 11.3, 28.7, BLACK),
            rect(9.82, 30.18, 13.78, 31.08, BLACK),
        ],
    )


def append_i2c(out: list[str]) -> None:
    group(out, "i2c", texts("i2c-"))


def append_pmic_rtc(out: list[str]) -> None:
    group(
        out,
        "pmic-rtc",
        [
            rect(15.05, 21.79, 21.92, 26.09, GREEN, 0.3),
            rect(15.03, 26.47, 19.13, 30.93, RTC_BLUE, 0.3),
            rect(19.33, 26.47, 21.94, 28.62, YELLOW, 0.15),
            rect(19.33, 28.86, 21.94, 30.95, KHAKI, 0.15),
        ]
        + texts("chip-"),
    )


def append_maker(out: list[str]) -> None:
    """M5Stack's cube with its 5, the M5STACK line, its rule and the
    maker's three lines."""
    top = [(3.42, 32.02), (4.96, 31.42), (6.36, 32.0), (4.98, 32.62)]
    group(
        out,
        "cube",
        [
            line(top + [top[0]], CUBE_BLUE, 0.1),
            line(
                [(3.42, 32.22), (3.42, 33.0), (4.98, 33.58), (6.36, 33.0), (6.36, 32.0)],
                CUBE_BLUE,
                0.1,
            ),
            line([(4.98, 32.62), (4.98, 32.62)], CUBE_BLUE, 0.1),
            line(
                [
                    (4.62, 31.72),
                    (4.06, 31.95),
                    (4.32, 32.08),
                    (4.94, 31.86),
                    (5.34, 32.02),
                    (5.3, 32.18),
                    (4.7, 32.42),
                ],
                BLACK,
                0.08,
            ),
        ],
    )
    group(
        out,
        "maker",
        [line([(2.13, 34.98), (7.63, 34.98)], LINE_GRAY, 0.09, "butt")] + texts("maker-"),
    )


def append_bps(out: list[str]) -> None:
    group(
        out,
        "bps",
        [rect(7.1, 31.1, 21.9, 32.4, GRAY, 0.1), rect(7.06, 32.44, 21.96, 33.7, GRAY_PALE, 0.1)]
        + texts("bps-"),
    )


def append_port(out: list[str]) -> None:
    """The HY2.0-4P port: its name over four cells, G, V OUT, G32, G33."""
    body = [
        rect(8.01, 33.75, 16.14, 37.31, GRAY, 0.3),
        rect(8.23, 35.06, 10.05, 36.98, BLACK),
        rect(10.19, 35.06, 12.01, 36.98, RED),
        rect(12.11, 35.06, 13.95, 36.98, YELLOW),
        rect(14.12, 35.06, 15.96, 36.98, GRAY_PALE),
    ]
    group(out, "port", body + texts("port-"))


def append_power(out: list[str]) -> None:
    group(out, "power", texts("pwr-") + [line([(20.62, 36.95), (21.34, 37.6)], LINE_GRAY, 0.13)])


def append_back(out: list[str]) -> None:
    """The label paper, then every print on it, in paint order."""
    out.append(f'<path id="label-paper" d="{paper_path()}" fill="{PAPER_INK}"/>\n')
    for part in (
        append_pins,
        append_banner,
        append_fields,
        append_esp32,
        append_display_and_mic,
        append_battery,
        append_fcc,
        append_model,
        append_giteki,
        append_ce_weee,
        append_i2c,
        append_pmic_rtc,
        append_maker,
        append_bps,
        append_port,
        append_power,
    ):
        part(out)
