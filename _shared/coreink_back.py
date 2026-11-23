# SPDX-License-Identifier: MIT
"""What the M5Stack CoreInk carries on its back, for ``svg/back.svg``

The CoreInk's back carries one printed sticker in the shell's recess: the HAT
pin strip along the top end, the maker's block, the dial's G37/G38/G39 disc,
the chips (ESP32-PICO-D4, BM8563, TP4057, SY7088, SY8089, CH9102) and the
power chain between them, the certification marks, the power key's block
(the sticker's words are ``Switch G27`` and ``POWER ON``) and USB-C, the
MI-BUS pin table and, between the two lower screws, the Ext.PORT tab.
``append_coreink_back`` draws it as one legend group on the plane ``label``,
in the back frame (``board_faces.py``: 1 mm a unit, x from the case's left edge
as seen from behind, y down from its top), which ``emit_back_svg.py`` lays in
the back drawing and the board's model builds as its ``label_legends`` meshes.

Measured on M5Stack's straight-on product photo of the back (the shop's
``6_2f1f124d-f916-4bdf-a943-d31436a702e8.webp``, 800 px, about 9.8 px/mm,
registered onto this frame through the centers of the four corner holes,
residual 0.07 mm), M5Stack's image, used as reference only. Every print is
drawn where that photo has it, at its size: each run of text is set in Inter
(the one face the model builder has) at the size and stretch that make its
ink cover the photo's. The sticker's own face is a condensed sans close to
DIN for the pin names and the chip names: Inter is wider and rounder, so its
runs are narrowed to the photo's lengths. The inks are the medians of the
photo's pixels on each print (its paper is clipped white, so they are taken as
they are), except the thin gray rules' (``LINE_GRAY``). Espressif's mark is
traced from the photo (``ESPRESSIF_MARK``).

Beside the sticker, where its ``SYSTEM RST`` arrow points, the back has the
board's reset key: a tongue molded into the back shell, flush with the back
(``RESET_*``, below). It is relief, not print, so it is drawn outside the
legend group, and it is the one control a back drawing carries: a target in
a ``hotspots`` group and its name in the margin (``schema.md``, "Back
drawings").
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import emit_front_svg as fronts  # beside this file

f = fronts.f

#: The plane the whole sticker is printed on, and the group's name.
PLANE = "label"
MARK = "back-label"

# Inks: each the median of the photo's pixels on the prints it names.
INK = "#141414"  # the text, the GND and CH9102 tiles, the marks
WHITE = "#ffffff"  # text on the colored cells
GRAY = "#7a7a7a"  # the maker's two lines, LiPo-390mAh, SYSTEM
RULE_GRAY = "#c6c6c6"  # the RST cell, the Ext.PORT tab
#: The thin gray rules (the dashed frames, the clock's ring, the maker's rule,
#: the buzzer's dash and first wave; also the speaker's back, solid at ~150):
#: a line one photo pixel wide pales to its paper, so this is the gray whose
#: line, blurred as the photo is, reads as dark as the photo's does beside the
#: black leads drawn the same way, not the median of its pixels.
LINE_GRAY = "#a3a3a3"
LIGHT_GRAY = "#e4e5e5"  # the G26 / G25 cells, the dial's disc
MID_GRAY = "#cdcdcd"  # the G36 cell
DARK_GRAY = "#555553"  # the two GPIO cells, the SY7088 / SY8089 tiles, the buzzer's middle wave
VERMILION = "#cf3205"  # the 5V cells (strip, Ext.PORT), the Espressif tile
DARK_RED = "#980404"  # the strip's second 5V cell, the 5VIN cell
RED = "#c71214"  # ON, 5VOUT, PWR, the power chain's red leads
MAGENTA = "#cc3263"  # the BAT cells, the clock's hands
HOT_PINK = "#f1075e"  # the power key's arrow (beside Switch), the arrows into and out of MOS
PINK = "#d77c97"  # BATTERY, BAT, the battery's leads, 5VIN's lead
MAUVE = "#8e4e4d"  # ESP32
YELLOW = "#fbcd12"  # the 3V3 cells, the G32 cell
ARROW_YELLOW = "#fcfe0e"  # the two 5V arrows on the strip
ORANGE = "#f06a3c"  # BTN, SCL, SDA, USB-C, the INK mark, the speaker
GREEN = "#20974a"  # LED, TXD2, RXD2, the lead to G35
PURPLE = "#993263"  # the TP4057 tile
BLUE = "#125d94"  # the BM8563 tile, RST, the dial's push arrow
CYAN = "#18acd2"  # the dial's ring and up/down arrow, MOSI/MISO/SCK, the leads into MOS
SALMON = "#f66662"  # ADC
CUBE_BLUE = "#4f8fbf"  # the M5STACK cube

# BEGIN TEXTS
TEXTS = (
    ("strip-gnd", "GND", 500, -6.892, 11.557, 2.396, 5.744, WHITE, "rotate(-90)"),  # widen 1.077
    ("strip-5v", "5V", 500, -7.065, 14.208, 2.279, 2.655, WHITE, "rotate(-90)"),  # widen 0.888
    ("strip-g26", "G26", 500, -6.36, 16.967, 2.396, 4.688, INK, "rotate(-90)"),  # widen 0.981
    ("strip-g36", "G36", 500, -6.359, 19.617, 2.396, 4.687, INK, "rotate(-90)"),  # widen 0.976
    ("strip-g25", "G25", 500, -6.362, 22.267, 2.396, 4.704, INK, "rotate(-90)"),  # widen 0.998
    ("strip-bat", "BAT", 500, -6.304, 24.94, 2.46, 4.615, WHITE, "rotate(-90)"),  # widen 0.929
    ("strip-3v3", "3V3", 500, -6.249, 27.567, 2.396, 4.486, INK, "rotate(-90)"),  # widen 0.954
    ("strip-5vb", "5V", 500, -7.164, 30.218, 2.279, 2.879, WHITE, "rotate(-90)"),  # widen 0.963
    (
        "ext",
        "ext.",
        500,
        -0.766,
        0.3,
        0.902,
        1.56,
        INK,
        "translate(8.25 7.15) rotate(-45)",
    ),  # widen 0.967
    ("maker-logo", "M5STACK", 700, 3.646, 12.051, 0.869, 4.195, INK, None),  # widen 0.95
    ("maker-1", "M5Stack", 400, 4.079, 13.541, 0.707, 3.352, GRAY, None),  # widen 1.144
    ("maker-2", "Technology Co.,Ltd.", 400, 2.033, 14.357, 0.755, 7.478, GRAY, None),  # widen 1.033
    ("dial-g37", "G37", 400, 1.864, 17.773, 1.713, 3.42, INK, None),  # widen 1.035
    ("dial-g39", "G39", 400, 1.887, 24.513, 1.713, 3.426, INK, None),  # widen 1.008
    (
        "dial-g38",
        "G38",
        400,
        -1.596,
        0.623,
        1.713,
        3.192,
        INK,
        "translate(7.47 21.62) rotate(-43)",
    ),  # widen 0.94
    ("esp32", "ESP32", 400, 9.966, 16.733, 2.12, 5.449, MAUVE, None),  # widen 0.827
    ("pico", "PICO-D4", 400, 10.121, 18.079, 1.165, 5.24, INK, None),  # widen 1.064
    ("lipo", "LiPo-390mAh", 400, 10.556, 19.769, 0.957, 4.719, GRAY, None),  # widen 0.755
    ("battery", "BATTERY", 400, 10.801, 21.15, 1.141, 4.081, INK, None),  # widen 0.785
    ("tp", "TP", 400, 11.681, 24.43, 2.062, 2.4, WHITE, None),  # widen 0.906
    ("tp-4057", "4057", 400, 10.962, 25.836, 1.446, 3.66, WHITE, None),  # widen 1.039
    ("bm", "BM", 400, 17.907, 10.43, 1.636, 2.717, WHITE, None),  # widen 1.066
    ("bm-8563", "8563", 400, 17.893, 11.44, 1.044, 2.754, WHITE, None),  # widen 1.077
    ("sda", "SDA:21", 400, 17.301, 12.957, 1.027, 3.469, INK, None),  # widen 1.006
    ("scl", "SCL:22", 400, 17.305, 13.907, 1.027, 3.344, INK, None),  # widen 0.945
    ("int", "INT:G19", 400, 17.263, 14.92, 1.031, 4.102, INK, None),  # widen 1.067
    ("btn", "BTN", 400, 23.392, 10.0, 1.168, 2.056, WHITE, None),  # widen 0.857
    ("btn-g5", "G5", 400, 23.937, 10.713, 0.696, 0.966, WHITE, None),  # widen 1.036
    ("led", "LED", 400, 27.25, 10.0, 1.1, 2.148, WHITE, None),  # widen 1.034
    ("led-g10", "G10", 400, 27.472, 10.792, 0.803, 1.725, WHITE, None),  # widen 1.204
    ("buzzer", "BUZZER", 400, 25.741, 12.09, 0.852, 3.527, INK, None),  # widen 1.061
    ("buzzer-g2", "G2", 400, 25.697, 13.589, 1.098, 1.217, INK, None),  # widen 0.818
    ("ink-icon", "INK", 700, -18.609, 17.15, 1.306, 2.372, ORANGE, "rotate(-90)"),  # widen 1.031
    ("epd-size", '200x200@1.54"', 400, 17.957, 16.755, 0.753, 7.422, INK, None),  # widen 1.288
    ("epd-part", "GDEW0154M09", 700, 17.933, 17.809, 0.988, 7.893, INK, None),  # widen 1.027
    ("epd-pins", "G4/0/15/9/18/23", 400, 17.934, 18.528, 0.654, 7.201, INK, None),  # widen 1.43
    ("system", "SYSTEM", 400, 27.035, 17.63, 0.813, 3.285, GRAY, None),  # widen 0.982
    ("rst", "RST", 700, 26.924, 19.496, 2.259, 3.491, BLUE, None),  # widen 0.781
    ("rtc", "RTC", 400, 17.516, 20.188, 1.178, 1.937, INK, None),  # widen 0.814
    ("mos", "MOS", 700, 19.337, 22.507, 1.203, 2.263, INK, None),  # widen 0.798
    ("g35", "G35", 400, 24.223, 20.043, 0.763, 1.555, INK, None),  # widen 1.041
    ("sy1", "SY", 400, 25.502, 21.237, 1.04, 1.12, WHITE, None),  # widen 0.815
    ("sy1-n", "7088", 400, 24.975, 22.171, 0.95, 2.281, WHITE, None),  # widen 0.986
    ("out-5v", "5V", 400, 27.868, 21.389, 1.085, 1.074, INK, None),  # widen 0.771
    ("out-out", "OUT", 400, 27.814, 22.189, 0.935, 2.01, INK, None),  # widen 0.998
    ("sy2", "SY", 400, 25.502, 24.287, 1.04, 1.12, WHITE, None),  # widen 0.815
    ("sy2-n", "8089", 400, 24.965, 25.141, 0.91, 2.29, WHITE, None),  # widen 1.011
    ("out-3v3", "3V3", 400, 27.865, 24.849, 1.165, 2.358, INK, None),  # widen 1.052
    ("g12", "G12", 400, 17.618, 26.099, 1.165, 2.117, INK, None),  # widen 1.031
    ("trig", "TRIG", 400, 20.97, 26.099, 1.165, 2.405, INK, None),  # widen 0.897
    ("pwr", "PWR", 400, 21.971, 24.95, 0.536, 1.277, RED, None),  # widen 1.05
    ("bat", "BAT", 400, 16.232, 21.73, 0.728, 1.535, PINK, None),  # widen 1.059
    ("model", "Model Name: M5CoreInk", 400, 1.934, 27.569, 0.88, 11.479, INK, None),  # widen 1.109
    ("fcc-id", "FCC-ID:2AN3WM5COREINK", 400, 1.939, 28.82, 1.004, 12.317, INK, None),  # widen 0.917
    ("giteki-r", "R", 400, 5.175, 30.52, 0.962, 0.551, INK, None),  # widen 0.89
    ("giteki-no", "211-200908", 400, 6.506, 30.359, 1.165, 7.049, INK, None),  # widen 1.076
    ("ch", "CH", 400, 11.51, 37.736, 1.472, 2.222, WHITE, None),  # widen 1.024
    ("ch-9102", "9102", 400, 11.491, 38.992, 0.87, 2.229, WHITE, None),  # widen 1.13
    ("txd", "TXD:1", 400, 11.985, 40.215, 0.777, 2.03, INK, None),  # widen 0.953
    ("rxd", "RXD:3", 400, 11.96, 41.113, 0.763, 2.031, INK, None),  # widen 0.902
    ("vin", "5VIN", 400, 12.754, 42.59, 0.99, 2.418, INK, None),  # widen 1.059
    ("switch", "Switch", 400, 3.681, 41.536, 1.086, 3.298, INK, None),  # widen 0.951
    ("switch-g27", "G27", 400, 4.31, 42.492, 0.843, 1.621, INK, None),  # widen 1.0
    ("power", "POWER", 400, 2.874, 44.111, 0.897, 3.132, INK, None),  # widen 0.961
    ("power-on", "ON", 700, 2.748, 46.789, 3.172, 3.398, RED, None),  # widen 0.699
    ("usb-c", "USB-C", 700, 9.266, 45.271, 1.778, 4.645, ORANGE, None),  # widen 0.802
    ("mibus", "MI-BUS", 700, 25.47, 27.158, 1.163, 4.531, INK, None),  # widen 1.045
    ("ext-port", "Ext.PORT", 400, 15.503, 51.561, 1.954, 9.469, INK, None),  # widen 1.088
    ("ext-g", "G", 400, 15.497, 54.028, 2.276, 1.542, WHITE, None),  # widen 0.908
    ("ext-5v", "5V", 400, 17.866, 53.724, 1.6, 1.932, WHITE, None),  # widen 0.941
    (
        "ext-g32",
        "G32",
        400,
        -1.171,
        0.463,
        1.272,
        2.356,
        INK,
        "translate(21.6 53.1) rotate(50)",
    ),  # widen 0.939
    (
        "ext-g33",
        "G33",
        400,
        -1.17,
        0.463,
        1.272,
        2.341,
        INK,
        "translate(24.2 53.15) rotate(50)",
    ),  # widen 0.929
    (
        "feedback",
        "feedback",
        400,
        -0.879,
        0.203,
        0.542,
        1.759,
        GREEN,
        "translate(22.4 19.9) rotate(-27)",
    ),  # widen 0.73
)
# END TEXTS


#: Espressif's mark: the white of it on its vermilion tile (the ball's three
#: bands, the dot and the arc round its left and bottom), traced from the
#: photo at its half-tone between the two inks; one outline a piece.
ESPRESSIF_MARK = (
    (
        (12.63, 9.85),
        (12.63, 9.89),
        (12.67, 9.93),
        (13.12, 10.15),
        (13.19, 10.21),
        (13.3, 10.26),
        (13.39, 10.33),
        (13.52, 10.4),
        (13.74, 10.61),
        (13.92, 10.79),
        (14.26, 11.26),
        (14.46, 11.63),
        (14.53, 11.78),
        (14.58, 11.82),
        (14.64, 11.8),
        (14.67, 11.71),
        (14.67, 11.41),
        (14.65, 11.28),
        (14.57, 11.03),
        (14.37, 10.61),
        (14.17, 10.36),
        (13.96, 10.18),
        (13.81, 10.08),
        (13.59, 9.95),
        (13.37, 9.86),
        (13.06, 9.78),
        (12.82, 9.75),
        (12.69, 9.78),
    ),
    (
        (11.52, 10.48),
        (11.54, 10.53),
        (11.59, 10.56),
        (11.89, 10.6),
        (12.12, 10.65),
        (12.54, 10.8),
        (12.69, 10.87),
        (12.89, 11),
        (13.13, 11.18),
        (13.45, 11.53),
        (13.55, 11.68),
        (13.74, 12.06),
        (13.86, 12.43),
        (13.88, 12.78),
        (13.92, 12.87),
        (13.99, 12.91),
        (14.12, 12.91),
        (14.24, 12.86),
        (14.32, 12.78),
        (14.44, 12.61),
        (14.46, 12.48),
        (14.44, 12.3),
        (14.35, 11.96),
        (14.14, 11.51),
        (14.02, 11.31),
        (13.79, 10.98),
        (13.62, 10.8),
        (13.35, 10.58),
        (13.09, 10.41),
        (12.67, 10.18),
        (12.32, 10.06),
        (12.09, 10.01),
        (11.99, 10.01),
        (11.92, 10.03),
        (11.8, 10.08),
        (11.72, 10.14),
        (11.55, 10.29),
        (11.53, 10.36),
    ),
    (
        (10.62, 11.13),
        (10.55, 11.58),
        (10.56, 11.93),
        (10.64, 12.33),
        (10.72, 12.56),
        (10.83, 12.76),
        (10.89, 12.84),
        (10.95, 12.96),
        (11.17, 13.21),
        (11.46, 13.46),
        (11.65, 13.58),
        (11.85, 13.68),
        (12.13, 13.81),
        (12.47, 13.9),
        (12.77, 13.92),
        (13.14, 13.89),
        (13.52, 13.79),
        (13.94, 13.6),
        (14.16, 13.46),
        (14.25, 13.38),
        (14.32, 13.29),
        (14.32, 13.25),
        (14.3, 13.21),
        (14.25, 13.18),
        (14.21, 13.18),
        (13.77, 13.51),
        (13.52, 13.61),
        (13.19, 13.71),
        (12.87, 13.74),
        (12.57, 13.73),
        (12.39, 13.7),
        (12.07, 13.61),
        (11.77, 13.48),
        (11.63, 13.38),
        (11.55, 13.31),
        (11.54, 13.27),
        (11.56, 13.24),
        (11.72, 13.19),
        (11.77, 13.16),
        (11.88, 13.03),
        (11.91, 12.96),
        (11.92, 12.86),
        (11.89, 12.77),
        (11.84, 12.68),
        (11.77, 12.62),
        (11.57, 12.57),
        (11.39, 12.62),
        (11.34, 12.66),
        (11.22, 12.91),
        (11.18, 12.92),
        (11.13, 12.9),
        (11.02, 12.73),
        (10.92, 12.53),
        (10.81, 12.26),
        (10.74, 11.83),
        (10.74, 11.38),
        (10.82, 10.98),
        (10.92, 10.78),
        (11.09, 10.53),
        (11.16, 10.41),
        (11.27, 10.28),
        (11.29, 10.21),
        (11.25, 10.15),
        (11.19, 10.14),
        (11.14, 10.16),
        (10.93, 10.41),
        (10.72, 10.83),
    ),
    (
        (10.91, 11.73),
        (10.94, 11.85),
        (11.04, 12),
        (11.24, 12.15),
        (11.49, 12.23),
        (11.81, 12.29),
        (12.04, 12.44),
        (12.16, 12.63),
        (12.23, 12.86),
        (12.21, 13.03),
        (12.11, 13.28),
        (12.12, 13.36),
        (12.17, 13.42),
        (12.25, 13.48),
        (12.49, 13.57),
        (12.54, 13.58),
        (12.62, 13.55),
        (12.72, 13.41),
        (12.82, 13.03),
        (12.83, 12.88),
        (12.81, 12.68),
        (12.72, 12.38),
        (12.56, 12.13),
        (12.37, 11.93),
        (12.2, 11.81),
        (12.07, 11.74),
        (11.62, 11.62),
        (11.55, 11.57),
        (11.54, 11.51),
        (11.57, 11.46),
        (11.62, 11.44),
        (11.74, 11.42),
        (11.87, 11.44),
        (12.07, 11.5),
        (12.44, 11.68),
        (12.62, 11.84),
        (12.72, 11.96),
        (12.84, 12.13),
        (12.96, 12.38),
        (13.04, 12.63),
        (13.07, 12.86),
        (13.05, 13.06),
        (12.99, 13.31),
        (13.02, 13.4),
        (13.12, 13.48),
        (13.22, 13.51),
        (13.29, 13.51),
        (13.47, 13.47),
        (13.54, 13.42),
        (13.6, 13.36),
        (13.62, 13.28),
        (13.64, 13.08),
        (13.64, 12.63),
        (13.62, 12.46),
        (13.54, 12.16),
        (13.33, 11.76),
        (13.13, 11.51),
        (12.92, 11.31),
        (12.72, 11.15),
        (12.42, 10.98),
        (12.15, 10.88),
        (11.79, 10.79),
        (11.62, 10.79),
        (11.51, 10.81),
        (11.27, 10.92),
        (11.16, 11.01),
        (11.1, 11.08),
        (10.94, 11.36),
        (10.91, 11.56),
    ),
)


def _text(
    text: str,
    weight: int,
    x: float,
    base: float,
    size: float,
    length: float,
    ink: str,
    transform: str | None,
) -> str:
    tr = f' transform="{transform}"' if transform else ""
    body = fronts._xml_escape(text)
    return (
        f'<text x="{f(x)}" y="{f(base)}" font-size="{f(size)}" font-weight="{weight}" '
        f'textLength="{f(length)}" lengthAdjust="spacingAndGlyphs" fill="{ink}"{tr}>'
        f"{body}</text>\n"
    )


def _rect(x0: float, y0: float, x1: float, y1: float, ink: str, r: float = 0.0) -> str:
    corner = f' rx="{f(r)}" ry="{f(r)}"' if r else ""
    return (
        f'<rect x="{f(x0)}" y="{f(y0)}" width="{f(x1 - x0)}" height="{f(y1 - y0)}"'
        f'{corner} fill="{ink}"/>\n'
    )


def _poly(points: Sequence[tuple[float, float]], ink: str) -> str:
    return f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in points)}" fill="{ink}"/>\n'


def _line(
    points: Sequence[tuple[float, float]],
    ink: str,
    width: float,
    cap: str = "butt",
    join: str = "round",
) -> str:
    d = " L ".join(f"{f(x)} {f(y)}" for x, y in points)
    return (
        f'<path d="M {d}" fill="none" stroke="{ink}" stroke-width="{f(width)}" '
        f'stroke-linecap="{cap}" stroke-linejoin="{join}"/>\n'
    )


def _path(d: str, ink: str, width: float | None = None, cap: str = "butt") -> str:
    if width is None:
        return f'<path d="{d}" fill="{ink}"/>\n'
    return (
        f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{f(width)}" '
        f'stroke-linecap="{cap}" stroke-linejoin="round"/>\n'
    )


def _runs(axis: str, at: float, runs: Sequence[tuple[float, float]]) -> list[str]:
    """Dashes measured one by one: along v = ``at`` (``h``) or u = ``at`` (``v``),
    each (start, end) one gray dash."""
    if axis == "h":
        return [_line([(a, at), (b, at)], LINE_GRAY, 0.09) for a, b in runs]
    return [_line([(at, a), (at, b)], LINE_GRAY, 0.09) for a, b in runs]


def _arrow_head(
    tip: tuple[float, float], toward: tuple[float, float], length: float, width: float, ink: str
) -> str:
    """A filled triangle with its tip at ``tip``, pointing away from ``toward``."""
    tx, ty = tip
    dx, dy = tip[0] - toward[0], tip[1] - toward[1]
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    bx, by = tx - dx * length, ty - dy * length
    return _poly(
        [
            (tx, ty),
            (bx - dy * width / 2, by + dx * width / 2),
            (bx + dy * width / 2, by - dx * width / 2),
        ],
        ink,
    )


def _arc_d(cx: float, cy: float, r: float, a0: float, a1: float) -> str:
    """Path data of an arc about (cx, cy) from angle a0 to a1 (degrees, page clockwise)."""
    p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
    p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M {f(p0[0])} {f(p0[1])} A {f(r)} {f(r)} 0 {large} 1 {f(p1[0])} {f(p1[1])}"


def _clipped_disc(cx: float, cy: float, r: float, cut: float) -> str:
    """Path data of a disc cut by the vertical line x = cut, the part right of it kept."""
    h = math.sqrt(r * r - (cut - cx) ** 2)
    return f"M {f(cut)} {f(cy - h)} A {f(r)} {f(r)} 0 1 1 {f(cut)} {f(cy + h)} Z"


def _clipped_ring(cx: float, cy: float, ri: float, ro: float, cut: float) -> str:
    """Path data of a ring cut by the vertical line x = cut, the part right of it kept."""
    ho = math.sqrt(ro * ro - (cut - cx) ** 2)
    hi = math.sqrt(ri * ri - (cut - cx) ** 2)
    return (
        f"M {f(cut)} {f(cy - ho)} A {f(ro)} {f(ro)} 0 1 1 {f(cut)} {f(cy + ho)} "
        f"L {f(cut)} {f(cy + hi)} A {f(ri)} {f(ri)} 0 1 0 {f(cut)} {f(cy - hi)} Z"
    )


def _half_ring(cx: float, cy: float, ri: float, ro: float) -> str:
    """Path data of the left half of a ring about (cx, cy): the CE mark's letters."""
    return (
        f"M {f(cx)} {f(cy - ro)} A {f(ro)} {f(ro)} 0 0 0 {f(cx)} {f(cy + ro)} "
        f"L {f(cx)} {f(cy + ri)} A {f(ri)} {f(ri)} 0 0 1 {f(cx)} {f(cy - ri)} Z"
    )


def _cells(out: list[str]) -> None:
    """The colored cells and tiles, under every print that stands on them."""
    # The HAT pin strip: eight cells along the top end, its edges the paper's.
    for u0, u1, ink in (
        (9.5, 12.02, INK),
        (12.02, 14.8, VERMILION),
        (14.8, 17.43, LIGHT_GRAY),
        (17.43, 19.98, MID_GRAY),
        (19.98, 22.6, LIGHT_GRAY),
        (22.6, 25.25, MAGENTA),
        (25.25, 28.0, YELLOW),
        (28.0, 30.5, DARK_RED),
    ):
        out.append(_rect(u0, 0.1, u1, 8.2, ink))
    # The dial's disc and ring, cut by the sticker's left edge.
    out.append(_path(_clipped_disc(3.9, 20.53, 5.17, 1.65), LIGHT_GRAY))
    out.append(_path(_clipped_ring(3.9, 20.53, 5.39, 5.85, 1.65), CYAN))
    # Chip tiles.
    out.append(_rect(9.78, 8.92, 15.61, 14.84, VERMILION, 0.75))
    out.append(_rect(10.43, 22.51, 15.33, 26.28, PURPLE, 0.55))
    out.append(_rect(17.12, 8.92, 21.31, 11.77, BLUE, 0.5))
    out.append(_rect(22.85, 8.95, 26.05, 10.9, ORANGE, 0.35))
    out.append(_rect(26.45, 9.0, 30.1, 10.9, GREEN, 0.35))
    out.append(_rect(24.75, 20.33, 27.5, 22.38, DARK_GRAY, 0.35))
    out.append(_rect(24.75, 23.33, 27.5, 25.27, DARK_GRAY, 0.35))
    out.append(_rect(10.95, 36.3, 14.25, 39.41, INK, 0.35))
    # The MI-BUS table: five rows of two cells, three of two wide ones.
    tops = [27.55 + 2.586 * i for i in range(8)]
    for top, (left, right) in zip(
        tops[:5],
        ((DARK_GRAY, CYAN), (DARK_GRAY, CYAN), (SALMON, CYAN), (ORANGE, ORANGE), (GREEN, GREEN)),
        strict=True,
    ):
        out.append(_rect(19.15, top, 23.2, top + 2.27, left, 0.08))
        out.append(_rect(23.62, top, 27.76, top + 2.27, right, 0.08))
    for top, (left, right) in zip(
        tops[5:], ((YELLOW, RULE_GRAY), (RED, DARK_RED), (MAGENTA, INK)), strict=True
    ):
        out.append(_rect(17.12, top, 23.27, top + 2.27, left, 0.08))
        out.append(_rect(23.65, top, 29.73, top + 2.27, right, 0.08))
    # The Ext.PORT tab and its four cells.
    out.append(_rect(14.8, 49.62, 25.55, 54.75, RULE_GRAY, 0.35))
    for u0, u1, ink in (
        (15.07, 17.42, INK),
        (17.65, 20.0, VERMILION),
        (20.05, 22.75, YELLOW),
        (22.8, 25.3, WHITE),
    ):
        out.append(_rect(u0, 51.88, u1, 54.48, ink))


def _marks(out: list[str]) -> None:
    """Every drawn mark that is no letter."""
    # Strip: the two yellow arrows, 5V in (up) and 5V out (down).
    out.append(
        _poly(
            [
                (13.39, 0.85),
                (14.36, 2.0),
                (13.84, 2.0),
                (13.84, 3.48),
                (12.93, 3.48),
                (12.93, 2.0),
                (12.41, 2.0),
            ],
            ARROW_YELLOW,
        )
    )
    out.append(
        _poly(
            [
                (29.39, 3.38),
                (30.36, 2.22),
                (29.84, 2.22),
                (29.84, 0.86),
                (28.93, 0.86),
                (28.93, 2.22),
                (28.42, 2.22),
            ],
            ARROW_YELLOW,
        )
    )
    # The M5STACK cube: an isometric box, M5Stack's mark on its top face.
    out.append(
        _line(
            [(5.76, 8.97), (7.1, 9.55), (5.76, 10.13), (4.42, 9.55), (5.76, 8.97)], CUBE_BLUE, 0.12
        )
    )
    out.append(
        _line(
            [(4.42, 9.55), (4.42, 10.37), (5.76, 10.95), (7.1, 10.37), (7.1, 9.55)], CUBE_BLUE, 0.12
        )
    )
    out.append(_line([(5.76, 10.13), (5.76, 10.95)], CUBE_BLUE, 0.12))
    # The dark 5 lying on the cube's top face: Inter Bold, its axes the face's
    # two edges (the photo's mark is too small there to read its own face).
    out.append(
        '<text x="0" y="0.47" font-size="1.3" font-weight="700" text-anchor="middle" '
        f'transform="matrix(0.917 -0.397 0.917 0.397 5.7 9.55)" fill="{INK}">5</text>\n'
    )
    out.append(_line([(2.0, 12.6), (9.45, 12.6)], LINE_GRAY, 0.06))
    # The dial's up/down arrow and its push arrow.
    out.append(
        _poly(
            [
                (3.59, 18.45),
                (4.5, 19.5),
                (3.9, 19.5),
                (3.9, 21.55),
                (4.5, 21.55),
                (3.59, 22.6),
                (2.68, 21.55),
                (3.28, 21.55),
                (3.28, 19.5),
                (2.68, 19.5),
            ],
            CYAN,
        )
    )
    out.append(
        _poly(
            [
                (4.52, 20.2),
                (5.85, 20.2),
                (5.85, 19.67),
                (6.86, 20.52),
                (5.85, 21.37),
                (5.85, 20.84),
                (4.52, 20.84),
            ],
            BLUE,
        )
    )
    # Espressif's mark, white on its tile.
    rings = " ".join(
        "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in ring) + " Z" for ring in ESPRESSIF_MARK
    )
    out.append(f'<path d="{rings}" fill="{WHITE}" fill-rule="evenodd"/>\n')
    # BATTERY's frame, its red mark, and the leads from it and from TP4057
    # into MOS.
    out.append(
        _path(
            "M 10.67 20.03 H 15.0 A 0.3 0.3 0 0 1 15.3 20.33 V 21.1 "
            "A 0.3 0.3 0 0 1 15.0 21.4 H 10.67 A 0.3 0.3 0 0 1 10.37 21.1 "
            "V 20.33 A 0.3 0.3 0 0 1 10.67 20.03 Z",
            PINK,
            0.12,
        )
    )
    out.append(_rect(15.37, 20.36, 15.55, 21.06, MAGENTA))
    out.append(_line([(15.21, 21.31), (15.62, 21.55), (16.02, 22.12), (18.1, 22.12)], PINK, 0.1))
    out.append(_line([(15.33, 22.78), (15.62, 22.62), (16.02, 22.12)], PINK, 0.1))
    out.append(_arrow_head((18.38, 22.12), (17.5, 22.12), 0.36, 0.34, RED))
    # 5VIN's lead from USB-C up the MI-BUS frame's side into TP4057: a
    # diagonal broken round the 5VIN run, then up beside the frame.
    out.append(_line([(14.49, 41.78), (15.56, 40.51), (15.56, 27.3)], PINK, 0.1))
    out.append(_line([(13.58, 42.86), (13.24, 43.27)], PINK, 0.1))
    out.append(_arrow_head((15.56, 26.9), (15.56, 27.5), 0.55, 0.42, RED))
    # The clock: a gray ring, its hands; and the tick between BM8563 and BTN.
    out.append(fronts.circle(23.05, 13.35, 1.5, stroke=LINE_GRAY, stroke_w=0.12))
    out.append(
        _line([(23.075, 12.4), (23.075, 13.47), (23.66, 13.63)], MAGENTA, 0.19, "butt", "miter")
    )
    out.append(_path("M 21.98 9.27 Q 22.08 9.72 22.58 9.97", INK, 0.1))
    # The buzzer: a dash, the speaker (its back, a gap, its cone) and three
    # waves, light gray, dark gray and black; the outer two share a center.
    out.append(_rect(27.13, 13.1, 27.68, 13.27, LINE_GRAY))
    out.append(_rect(27.77, 12.78, 28.15, 13.59, LINE_GRAY))
    out.append(_poly([(28.33, 12.745), (28.87, 12.31), (28.87, 14.05), (28.33, 13.65)], ORANGE))
    out.append(_path(_arc_d(28.833, 13.196, 0.565, -41.0, 41.0), LINE_GRAY, 0.12))
    out.append(_path(_arc_d(28.614, 13.19, 1.13, -42.0, 42.0), DARK_GRAY, 0.17))
    out.append(_path(_arc_d(28.614, 13.19, 1.477, -47.0, 47.0), INK, 0.2))
    # RST: the dashed bracket round it, its top left corner cut, and its arrow.
    out.append(_line([(26.4, 15.36), (26.74, 14.68), (26.89, 14.68)], LINE_GRAY, 0.08))
    for v0, v1 in ((15.6, 16.42), (16.74, 17.54), (17.85, 18.65), (18.97, 19.75)):
        out.append(_line([(26.39, v0), (26.39, v1)], LINE_GRAY, 0.08))
    for u0, u1 in ((27.22, 28.0), (28.32, 29.12), (29.43, 30.23)):
        out.append(_line([(u0, 14.68), (u1, 14.68)], LINE_GRAY, 0.08))
    for u0, u1 in ((26.64, 27.39), (27.72, 28.52), (28.84, 29.64), (29.94, 30.38)):
        out.append(_line([(u0, 19.88), (u1, 19.88)], LINE_GRAY, 0.08))
    out.append(
        _poly(
            [
                (27.44, 15.6),
                (28.9, 15.6),
                (28.9, 15.14),
                (29.79, 15.86),
                (28.9, 16.57),
                (28.9, 16.12),
                (27.44, 16.12),
            ],
            CYAN,
        )
    )
    # MOS: its pill and the leads around it.
    out.append(
        _path(
            "M 19.2 21.5 H 21.75 A 0.62 0.62 0 0 1 21.75 22.74 H 19.2 "
            "A 0.62 0.62 0 0 1 19.2 21.5 Z",
            LIGHT_GRAY,
        )
    )
    out.append(
        _path(
            "M 19.2 21.5 H 21.75 A 0.62 0.62 0 0 1 21.75 22.74 H 19.2 "
            "A 0.62 0.62 0 0 1 19.2 21.5 Z",
            INK,
            0.1,
        )
    )
    out.append(_path("M 19.45 19.62 Q 20.25 19.75 20.4 20.85", CYAN, 0.09))
    out.append(_arrow_head((20.42, 21.15), (20.4, 20.7), 0.32, 0.28, CYAN))
    out.append(_line([(19.35, 25.05), (19.75, 23.25)], CYAN, 0.09))
    out.append(_arrow_head((19.82, 22.92), (19.72, 23.4), 0.32, 0.28, CYAN))
    out.append(_line([(21.35, 25.05), (21.05, 23.25)], CYAN, 0.09))
    out.append(_arrow_head((21.0, 22.92), (21.07, 23.4), 0.32, 0.28, CYAN))
    out.append(_path("M 21.6 21.4 Q 22.6 20.1 23.75 19.8", GREEN, 0.08))
    out.append(_arrow_head((24.1, 19.75), (23.6, 19.82), 0.3, 0.26, GREEN))
    out.append(_line([(22.55, 22.05), (24.05, 22.05)], HOT_PINK, 0.1))
    out.append(_arrow_head((24.55, 22.05), (23.9, 22.05), 0.4, 0.34, HOT_PINK))
    # The 5V OUT and 3V3 underlines, and the lead from 5V OUT to SY8089.
    out.append(_line([(27.82, 22.42), (29.92, 22.42)], RED, 0.12))
    out.append(_line([(27.82, 25.05), (30.18, 25.05)], RED, 0.12))
    out.append(
        _line(
            [(28.33, 22.48), (28.33, 22.97), (23.5, 22.97), (23.5, 24.05), (24.15, 24.05)], RED, 0.1
        )
    )
    out.append(_arrow_head((24.6, 24.05), (24.0, 24.05), 0.4, 0.34, RED))
    # Japan's radio-equipment mark: a ring open only at its right, where the
    # lightning stroke that crosses it from the left leaves it in a point and
    # turns back into the ring's top; under the stroke, two bars on a stem.
    gx, gy, gr = 3.19, 30.61, 1.195
    out.append(_path(_arc_d(gx, gy, gr, 20.0, 310.0), INK, 0.13))
    out.append(
        _line(
            [
                (1.99, 30.31),
                (3.22, 30.04),
                (3.27, 30.4),
                (4.3, 30.13),
                (gx + gr * math.cos(math.radians(310)), gy + gr * math.sin(math.radians(310))),
            ],
            INK,
            0.13,
            "butt",
            "miter",
        )
    )
    out.append(_rect(2.55, 30.74, 3.79, 30.84, INK))
    out.append(_rect(2.55, 30.99, 3.79, 31.09, INK))
    out.append(_rect(3.17, 31.09, 3.27, 31.47, INK))
    out.append(_path("M 4.79 29.53 H 6.205 V 30.78 H 4.79 Z", INK, 0.1))
    # WEEE: the crossed-out wheelie bin and the bar under it. The lid is a
    # dome over its rim, solid at the shoulders, with a window under the dome
    # and the handle standing in its top; the rear grip hangs from the rim's
    # right end; the body carries a bar, a foot at its left and a wheel (a
    # ring round a hub) at its right.
    out.append(_line([(1.84, 32.36), (6.51, 37.28)], INK, 0.14))
    out.append(_line([(6.83, 32.34), (2.0, 37.29)], INK, 0.14))
    dome = (
        "M 3.2 33.2 L 3.25 33.02 L 3.35 32.92 L 3.47 32.82 L 3.6 32.785 L 4.0 32.73 "
        "L 4.3 32.7 L 4.6 32.7 L 4.9 32.765 L 5.1 32.81 L 5.27 32.86 L 5.37 32.93 "
        "L 5.45 33.02 L 5.47 33.2 Z "
        "M 3.72 33.15 V 33.0 Q 3.72 32.94 3.78 32.94 H 5.15 Q 5.21 32.94 5.21 33.0 V 33.15 Z "
        "M 4.2 32.8 H 4.72 V 32.92 H 4.2 Z"
    )
    out.append(f'<path d="{dome}" fill="{INK}" fill-rule="evenodd"/>\n')
    out.append(_rect(4.1, 32.93, 4.82, 33.04, INK))
    out.append(_rect(3.08, 33.15, 5.78, 33.32, INK, 0.05))
    out.append(_line([(5.36, 33.955), (5.72, 33.955), (5.72, 33.3)], INK, 0.13, "butt", "miter"))
    out.append(_line([(3.265, 33.3), (3.545, 36.57)], INK, 0.15))
    out.append(_line([(5.44, 33.3), (5.2, 36.05)], INK, 0.15))
    out.append(_line([(3.47, 36.565), (4.85, 36.565)], INK, 0.16))
    out.append(_rect(3.53, 36.56, 3.82, 36.84, INK))
    out.append(_rect(4.06, 34.04, 4.95, 34.3, INK, 0.06))
    out.append(fronts.circle(5.165, 36.41, 0.335, stroke=INK, stroke_w=0.18))
    out.append(fronts.circle(5.165, 36.41, 0.11, fill=INK))
    out.append(_rect(2.27, 38.37, 6.37, 39.35, INK))
    # CE.
    out.append(_path(_half_ring(10.0, 33.42, 2.12, 2.87), INK))
    out.append(_path(_half_ring(14.85, 33.42, 2.12, 2.87), INK))
    out.append(_rect(12.45, 33.05, 14.55, 33.8, INK))
    # FCC: the F, its top left corner round and its middle bar running into
    # the outer C, then the outer C round the inner one.
    out.append(
        _path(
            "M 7.21 39.34 V 37.32 A 0.2 0.2 0 0 1 7.41 37.12 H 8.36 V 37.5 H 7.6 "
            "V 38.14 H 8.45 V 38.4 H 7.6 V 39.34 Z",
            INK,
        )
    )
    out.append(_path(_arc_d(9.37, 38.28, 0.91, 31.0, 329.0), INK, 0.3))
    out.append(_path(_arc_d(9.37, 38.28, 0.5, 35.0, 325.0), INK, 0.3))
    # CH9102's lead to the USB-C, and the arrow from Switch to the power key.
    out.append(_path("M 11.62 42.85 Q 11.3 41.2 11.45 39.85", INK, 0.08))
    out.append(_arrow_head((11.48, 39.45), (11.45, 39.9), 0.35, 0.3, INK))
    out.append(
        _poly(
            [
                (1.74, 42.0),
                (2.72, 41.14),
                (2.72, 41.64),
                (3.92, 41.68),
                (3.9, 42.36),
                (2.68, 42.35),
                (2.66, 42.84),
            ],
            HOT_PINK,
        )
    )
    # The dashed frames, each dash where the photo has it (its dashes are
    # about 0.87 mm long, 0.25 apart, but not evenly). Round the power key's
    # block: a top run, a corner of r 0.5, a right run.
    out.extend(_runs("h", 40.08, ((1.76, 2.62), (2.88, 3.74), (3.98, 4.86), (5.08, 5.97))))
    corner = _arc_d(6.72, 40.58, 0.5, -90.0, -55.3)
    out.append(_path("M 6.21 40.08 H 6.72 " + corner[corner.index("A") :], LINE_GRAY, 0.09))
    out.append(_path(f"{_arc_d(6.72, 40.58, 0.5, -12.6, 0.0)} V 41.31", LINE_GRAY, 0.09))
    out.extend(
        _runs(
            "v",
            7.22,
            (
                (41.58, 42.45),
                (42.67, 43.56),
                (43.81, 44.67),
                (44.92, 45.77),
                (46.03, 46.91),
                (47.16, 48.0),
            ),
        )
    )
    # Round the MI-BUS table: a top run, a cut top left corner, a left run, a
    # bottom left corner of r 1.2 and a bottom run.
    out.extend(
        _runs(
            "h",
            26.655,
            (
                (17.38, 18.27),
                (18.49, 19.39),
                (19.62, 20.51),
                (20.74, 21.62),
                (21.87, 22.74),
                (22.98, 23.84),
                (24.11, 24.98),
            ),
        )
    )
    out.append(_line([(16.48, 27.22), (17.09, 26.61)], LINE_GRAY, 0.09))
    out.extend(
        _runs(
            "v",
            16.24,
            (
                (27.36, 28.19),
                (28.46, 29.31),
                (29.57, 30.43),
                (30.69, 31.57),
                (31.82, 32.65),
                (32.94, 33.77),
                (34.04, 34.91),
                (35.17, 36.03),
                (36.3, 37.14),
                (37.41, 38.25),
                (38.52, 39.38),
                (39.65, 40.51),
                (40.75, 41.62),
                (41.84, 42.74),
                (42.98, 43.87),
                (44.13, 44.98),
                (45.23, 46.1),
                (46.31, 47.23),
            ),
        )
    )
    out.append(_path(_arc_d(17.44, 47.4, 1.2, 137.3, 177.0), LINE_GRAY, 0.09))
    corner = _arc_d(17.44, 47.4, 1.2, 90.0, 124.4)
    out.append(_path("M 17.55 48.6 H 17.44 " + corner[corner.index("A") :], LINE_GRAY, 0.09))
    out.extend(
        _runs(
            "h",
            48.6,
            (
                (17.79, 18.66),
                (18.93, 19.78),
                (20.04, 20.9),
                (21.16, 22.02),
                (22.24, 23.13),
                (23.38, 24.26),
                (24.51, 25.37),
                (25.61, 26.49),
                (26.73, 27.61),
                (27.84, 28.73),
                (28.97, 29.85),
            ),
        )
    )
    # USB-C: the receptacle's outline, its bottom corners bent round, and the
    # plug hanging from its bottom run, with its two contacts.
    out.append(
        _path(
            "M 8.705 43.24 V 45.585 A 0.65 0.65 0 0 0 9.355 46.235 H 13.78 "
            "A 0.65 0.65 0 0 0 14.43 45.585 V 43.24",
            INK,
            0.61,
        )
    )
    out.append(_line([(9.76, 46.235), (9.76, 49.005), (13.39, 49.005), (13.39, 46.235)], INK, 0.61))
    out.append(_rect(10.6, 47.6, 11.15, 48.15, INK, 0.04))
    out.append(_rect(12.0, 47.6, 12.54, 48.15, INK, 0.04))


def _table_texts(out: list[str]) -> None:
    """The MI-BUS table's pin names and cell names, centered in their rows."""
    tops = [27.55 + 2.586 * i for i in range(8)]
    rows = (
        ("G25", "GPIO", "MOSI", "G23", 3.37, 3.62),
        ("G26", "GPIO", "MISO", "G34", 3.37, 3.62),
        ("G36", "ADC", "SCK", "G18", 2.87, 2.62),
        ("G22", "SCL", "SDA", "G21", 2.62, 2.75),
        ("G14", "TXD2", "RXD2", "G13", 3.8, 3.88),
    )
    for top, (pl, cl, cr, pr, wl, wr) in zip(tops[:5], rows, strict=True):
        mid = top + 1.135
        out.append(_centered(pl, 400, 18.04, mid, 1.74, 0.71, INK))
        out.append(_centered(pr, 400, 28.84, mid, 1.74, 0.71, INK))
        out.append(_centered(cl, 400, 21.17, mid, wl, 1.12, WHITE))
        out.append(_centered(cr, 400, 25.69, mid, wr, 1.12, WHITE))
    wide = (
        ("3V3", "RST", 2.86, 3.1, INK, INK),
        ("5VOUT", "5VIN", 5.3, 3.88, WHITE, WHITE),
        ("BAT", "GND", 3.25, 4.0, WHITE, WHITE),
    )
    for top, (cl, cr, wl, wr, il, ir) in zip(tops[5:], wide, strict=True):
        mid = top + 1.135
        out.append(_centered(cl, 400, 20.2, mid, wl, 1.3, il))
        out.append(_centered(cr, 400, 26.69, mid, wr, 1.3, ir))


#: Inter's cap height and the tops and bottoms of the strings the table sets,
#: as fractions of the size (all caps and digits: cap height on the baseline).
CAP = 0.727


def _centered(
    text: str, weight: int, cx: float, cy: float, width: float, cap: float, ink: str
) -> str:
    """An all-caps run centered on (cx, cy): ``cap`` tall, ``width`` long (its advance)."""
    size = cap / CAP
    return (
        f'<text x="{f(cx)}" y="{f(cy + cap / 2)}" font-size="{f(size)}" '
        f'font-weight="{weight}" text-anchor="middle" textLength="{f(width)}" '
        f'lengthAdjust="spacingAndGlyphs" fill="{ink}">{text}</text>\n'
    )


#: The reset key, in the back frame: a tongue molded into the back shell
#: beside the sticker's SYSTEM RST arrow, hinged at its lower end, its free
#: end flush with the back. Read off M5Stack's CoreInk.stl (M5_Hardware
#: Products/K048_CoreInk/Structures, the file the board's model is built
#: from), the assembly's back shell: the opening is a stadium, x
#: 30.94..37.06, y 11.98..22.02; the tongue is 4.13 mm wide at its face (4.44
#: at the foot of its chamfer), round at the top (y 12.97), flat down to a
#: crease at y 16.38, where it slopes 1 mm into the shell and runs on as the
#: hinge's arm to its root at y 20.35. M5Stack's straight-on photo of the
#: back (the one the sticker is measured on) shows the same key: registered
#: through the four corner holes, the slot's top is at y 11.94, its arms end
#: at y 20.19 and its middle is at x 34.3, which is x 34.0 counted from the
#: sticker's RST arrow (that registration puts the arrow's tip 0.25 mm right
#: of where this file draws it).
RESET_CX = 34.0
RESET_OPENING = (30.94, 11.98, 37.06, 22.02)  # x0, y0, x1, y1: a stadium
RESET_ROUND_CY = 15.03  # the center of the tongue's round end
RESET_TONGUE_HALF = 2.22  # half the tongue's width at the foot of its chamfer
RESET_PAD_HALF = 2.066  # half its width at its face, and its round end's radius
RESET_PAD_CREASE = 16.379
RESET_ARM_TOP = 18.2  # where the slope reaches the arm, 1 mm under the back
RESET_ROOT = 20.35
RESET_SLOT = "#2a2a2d"  # the gap round the tongue: the inside of the case
RESET_SUNK = "#e3e3df"  # the arm and the opening's floor, 1 mm under the back
RESET_SLOPE = "#ecece8"  # the slope between the pad and the arm
RESET_PAD = "#f7f7f5"  # the case's own white
RESET_EDGE = "#bcbcb8"  # the case outline's stroke


def append_reset_key(out: list[str]) -> None:
    """The reset key as the back shows it: its opening, the gap, the tongue."""
    x0, y0, x1, y1 = RESET_OPENING
    r = (x1 - x0) / 2
    half, pad = RESET_TONGUE_HALF, RESET_PAD_HALF
    cx, cy = RESET_CX, RESET_ROUND_CY
    out.append('<g id="reset-key">\n')
    # The opening, down to its floor: the stadium the shell is cut to.
    out.append(
        f'<path d="M {f(x0)} {f(y0 + r)} A {f(r)} {f(r)} 0 0 1 {f(x1)} {f(y0 + r)} '
        f'V {f(y1 - r)} A {f(r)} {f(r)} 0 0 1 {f(x0)} {f(y1 - r)} Z" '
        f'fill="{RESET_SUNK}" stroke="{RESET_EDGE}" stroke-width="0.12"/>\n'
    )
    # The gap round the tongue, open to the inside: a U down to the root.
    out.append(
        f'<path d="M {f(x0)} {f(RESET_ROOT)} V {f(y0 + r)} '
        f"A {f(r)} {f(r)} 0 0 1 {f(x1)} {f(y0 + r)} V {f(RESET_ROOT)} "
        f"H {f(cx + half)} V {f(cy)} "
        f"A {f(half)} {f(half)} 0 0 0 {f(cx - half)} {f(cy)} "
        f'V {f(RESET_ROOT)} Z" fill="{RESET_SLOT}"/>\n'
    )
    # The slope from the pad down to the arm.
    out.append(
        f'<rect x="{f(cx - pad)}" y="{f(RESET_PAD_CREASE)}" width="{f(2 * pad)}" '
        f'height="{f(RESET_ARM_TOP - RESET_PAD_CREASE)}" fill="{RESET_SLOPE}"/>\n'
    )
    # The pad: the tongue's free end, flush with the back.
    out.append(
        f'<path d="M {f(cx - pad)} {f(RESET_PAD_CREASE)} V {f(cy)} '
        f"A {f(pad)} {f(pad)} 0 0 1 {f(cx + pad)} {f(cy)} "
        f'V {f(RESET_PAD_CREASE)} Z" fill="{RESET_PAD}" stroke="{RESET_EDGE}" '
        'stroke-width="0.1"/>\n'
    )
    out.append("</g>\n")


def reset_pad() -> tuple[float, float, float, float]:
    """The pad's box: its center and its size, (cx, cy, w, h) in the back frame."""
    top = RESET_ROUND_CY - RESET_PAD_HALF
    return (RESET_CX, (top + RESET_PAD_CREASE) / 2, 2 * RESET_PAD_HALF, RESET_PAD_CREASE - top)


def back_hotspots() -> list[fronts.Hotspot]:
    """The back's one control: the reset key, a target on its pad."""
    cx, cy, w, h = reset_pad()
    return [fronts.Hotspot("Reset", cx, cy, w, h, face="back")]


def back_callouts() -> list[str]:
    """The reset key's name, in the right margin level with its pad."""
    _cx, cy, _w, _h = reset_pad()
    return [fronts.text(40.0 + 1.2, cy + 0.5, "Reset", size=1.4, fill="#7d7d80", anchor="start")]


def append_coreink_back(out: list[str]) -> None:
    """The reset key, then the back sticker as one legend group on the plane ``label``."""
    append_reset_key(out)
    out.append(fronts.print_open(MARK, PLANE))
    _cells(out)
    _marks(out)
    for _name, text, weight, x, base, size, length, ink, transform in TEXTS:
        out.append(_text(text, weight, x, base, size, length, ink, transform))
    _table_texts(out)
    out.append(fronts.LEGEND_CLOSE)


#: The left side's label: CORE, a cyan dot, INK, read from the HAT end to the
#: USB-C end with the front up. Measured on M5Stack's photo of that side (the
#: shop gallery's seventh picture of the board, 800 px), scaled
#: to the label's paper (33.6 x 11.9 mm, 11.1 px/mm along it and 10.2 across).
#: The label sets CORE in a light condensed face and INK in a bold one: here
#: Inter Regular narrowed to CORE's length, and Inter Bold. INK leans forward
#: 3.3 degrees (its I and K stems on that photo; CORE's E stands upright), so
#: Inter Bold is slanted by that much about the middle of its cap height.
INK_SLANT = "matrix(1 0 -0.0577 1 -0.456 0)"
LEFT_PLANE = "side"
LEFT_MARK = "side-label"


def append_coreink_left(out: list[str]) -> None:
    """The CoreInk's left-side label, in the left frame (u along +Z from the back, v down)."""
    out.append(fronts.print_open(LEFT_MARK, LEFT_PLANE))
    for text, weight, x, base, size, length, transform in (
        ("CORE", 400, 13.536, -5.75, 6.184, 13.066, "rotate(90)"),
        ("INK", 700, 30.268, -5.59, 6.35, 11.809, f"rotate(90) {INK_SLANT}"),
    ):
        out.append(_text(text, weight, x, base, size, length, INK, transform))
    out.append(fronts.circle(8.0, 28.5, 0.6, fill=CYAN))
    out.append(fronts.LEGEND_CLOSE)
