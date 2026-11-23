# SPDX-License-Identifier: MIT
"""What the Cardputer ADV prints on its back, its top and its left side

The ADV's bottom shell carries one sticker over its whole back, in the
shell's own 0.2 mm pocket: the board's block diagram (the EXT header's pins,
the audio chain, the power path, the I2C devices, the key matrix, the LCD's
pins), drawn by M5Stack in the colors of the StampS3A label. A second
sticker lies in the top shell's pocket along the top edge (the StampS3A's
name, the G0 and reset keys, the power switch, the microSD card's pins, the
IR LED) and a third in the pocket of the left side, round the Grove port
(PORT.A's pins and the 5 V direction switch).

Each is drawn here in its own face's frame (``board_faces.py``), 1 mm a
unit, seen straight on by someone looking at that face, from M5Stack's
product photos (reference only, never committed): the back from the straight
shot of the back at 9.9 px/mm, registered on the case's four edges; the top
and the left from the straight shots of those edges. The positions and sizes
are those photos'; the type is Inter, the only face the models carry, set to
each word's measured width (``textLength``), where the label's own face is a
geometric sans a little wider in its rounds (its M and W splay, its G has no
spur). The inks are the StampS3A label's (``emit_front_svg.STAMP_*``) where the
photo prints the same color, and four of their own where it does not: the
gray of the chip boxes, the pink of the DC/DC boxes, the khaki of the key
matrix's rows and the sky blue of the BMI270's box. Where the photo's color
has no ink of its own the nearest of those stands in: the red of S3A for the
EXT header's darker 5V IN, the periwinkle of the StampS3A's GPIO 43 for the
speaker's violet, the green of its GPIO 11 for the jack's brighter green, the
lime of its GPIO 39 for the jack's gold ring, the cyan of its GPIO 1-10 for
the gyroscope's disc. The back is drawn in the coordinates measured on the
photo and set on the sticker's paper by ``BACK_FRAME``.

``emit_back_svg.py`` calls ``back``, ``top`` and ``left``; nothing here is
drawn mirrored.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

import emit_front_svg as fronts  # noqa: E402  (beside this file)

f = fronts.f
INK = fronts.CARDPUTER_INK
WHITE = fronts.STAMP_WHITE
ORANGE = fronts.CARDPUTER_ORANGE  # the USB C, the microphone
VERMILION = fronts.STAMP_VERMILION  # the power traces and their names
RED = fronts.STAMP_RED  # S3A, 5V IN
MAGENTA = fronts.STAMP_MAGENTA  # the DC/DC headings, the battery's bar, the headphones
PURPLE = fronts.STAMP_PURPLE  # the I2S and audio lines
SALMON = fronts.STAMP_SALMON  # the charger's lower half
AZURE = fronts.STAMP_AZURE  # the data lines
M5_BLUE = fronts.STAMP_M5_BLUE  # the M5 logotype, the ADV flag, the switch
CYAN = fronts.STAMP_CYAN  # the switch's arrow, the BMI270's mark
GREEN = fronts.STAMP_GREEN  # G8 SDA, the audio jack's ground
YELLOW = fronts.STAMP_YELLOW  # G9 SCL, G2, the jack's tip
LIME = fronts.STAMP_LIME  # the jack's second ring
GRAY = fronts.STAMP_GRAY  # the pin table's frame
PALE_GRAY = fronts.STAMP_PALE_GRAY  # the pin table's shaded cells
DARK_GRAY = fronts.STAMP_DARK_GRAY  # the key matrix's columns, the jack's sleeve
PERIWINKLE = fronts.STAMP_PERIWINKLE  # the speaker
PALE_YELLOW = fronts.STAMP_PALE_YELLOW
# Inks of the back's own, white-balanced from the photo (its paper, #f2f3f0,
# made the model's #fcfcfa): the chip boxes (ES8311, NS4150, TCA8418, CN809),
# the lower half of the two DC/DC boxes, the key matrix's rows.
BOX_GRAY = "#505050"
PINK = "#fc659b"
KHAKI = "#a7ac8f"
SKY = "#a6e2fb"  # the BMI270's box and the ground of its gyroscope mark
#: Inter's cap height, in ems: a word whose capitals stand ``cap`` mm tall is
#: set at ``cap / CAP`` mm.
CAP = 0.727
PLANE = "label"
#: The width of the label's lines (its traces, the data lines, the arrows' shafts,
#: the key matrix's columns, the outline of the battery's box), measured on the photo.
TRACE = 0.2


def t(
    x: float,
    base: float,
    content: str,
    cap: float,
    ink: str,
    *,
    weight: str = "500",
    length: float | None = None,
    anchor: str = "start",
) -> str:
    """A run whose capitals stand ``cap`` mm tall, ``length`` mm wide."""
    return fronts.text(
        x, base, content, size=cap / CAP, fill=ink, anchor=anchor, weight=weight, length=length
    )


def rot(deg: float, cx: float, cy: float, body: str) -> str:
    return f'<g transform="rotate({f(deg)} {f(cx)} {f(cy)})">\n{body}</g>\n'


def box(x0: float, y0: float, x1: float, y1: float, fill: str, r: float = 0.0) -> str:
    return fronts.rounded_rect(x0, y0, x1 - x0, y1 - y0, r=r, fill=fill)


def line(points: Sequence[Tuple[float, float]], ink: str, width: float, cap: str = "butt") -> str:
    d = " L ".join(f"{f(x)} {f(y)}" for x, y in points)
    return (
        f'<path d="M {d}" fill="none" stroke="{ink}" '
        f'stroke-width="{f(width)}" stroke-linejoin="round" '
        f'stroke-linecap="{cap}"/>\n'
    )


def curve(d: str, ink: str, width: float) -> str:
    """A stroked path given as path data."""
    return (
        f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{f(width)}" '
        'stroke-linejoin="round" stroke-linecap="butt"/>\n'
    )


def head(x: float, y: float, deg: float, ink: str, length: float = 0.6, width: float = 0.55) -> str:
    """A filled arrowhead with its tip at (x, y), pointing ``deg`` degrees
    (0 to the right, 90 down)."""
    a = math.radians(deg)
    ux, uy = math.cos(a), math.sin(a)
    bx, by = x - ux * length, y - uy * length
    px, py = -uy * width / 2, ux * width / 2
    return (
        f'<polygon points="{f(x)},{f(y)} {f(bx + px)},{f(by + py)} '
        f'{f(bx - px)},{f(by - py)}" fill="{ink}"/>\n'
    )


def arc(cx: float, cy: float, r: float, a0: float, a1: float, ink: str, width: float) -> str:
    """A circular arc from ``a0`` to ``a1`` degrees, the angle growing (on the
    page, clockwise: 0 to the right, 90 down)."""
    p0 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
    p1 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return (
        f'<path d="M {f(p0[0])} {f(p0[1])} A {f(r)} {f(r)} 0 {large} 1 '
        f'{f(p1[0])} {f(p1[1])}" fill="none" stroke="{ink}" '
        f'stroke-width="{f(width)}" stroke-linecap="butt"/>\n'
    )


def ring(x0: float, y0: float, x1: float, y1: float, r: float, ink: str, width: float) -> str:
    """The outline of a rounded rectangle, ``width`` wide, inside its box."""
    h = width / 2
    return fronts.stamp_box(x0 + h, y0 + h, x1 - h, y1 - h, max(r - h, 0.0), ink, width)


def kv(
    x: float,
    base: float,
    key: str,
    value: str,
    cap: float,
    key_len: float,
    value_len: float,
    ink: str = INK,
    key_weight: str = "500",
) -> List[str]:
    """A pin's name in the label's medium weight and its GPIO in bold, each
    set to the width the photo gives it."""
    return [
        t(x, base, key, cap, ink, weight=key_weight, length=key_len),
        t(x + key_len, base, value, cap, ink, weight="700", length=value_len),
    ]


#: The back's coordinates were measured on the photo registered on the case's
#: outline (9.905 x 9.870 px/mm), which lies farther from the lens than the
#: sticker and reads about 0.7 % small. Registered on the sticker's own paper
#: edges (9.977 x 9.943 px/mm, the two screw bosses agreeing), the same photo
#: puts every print here: this matrix, inside each of the back's groups, takes
#: the measured coordinates onto the paper's.
BACK_FRAME = "matrix(0.99276 0 0 0.992695 0.231945 0.245457)"


def drawn(u: float, v: float) -> Tuple[float, float]:
    """A point read on the paper's registration, in the measured coordinates
    the back is drawn in (``BACK_FRAME`` undone)."""
    return (round((u - 0.231945) / 0.99276, 3), round((v - 0.245457) / 0.992695, 3))


def spline(points: Sequence[Tuple[float, float]], ink: str, width: float) -> str:
    """A smooth trace through *points*, read on the paper: each span a cubic
    whose tangents at its ends run from the point before to the point after
    (a Catmull-Rom curve)."""
    pts = [drawn(u, v) for u, v in points]
    d = [f"M {f(pts[0][0])} {f(pts[0][1])}"]
    for i in range(len(pts) - 1):
        a, b = pts[max(i - 1, 0)], pts[i]
        c, e = pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        d.append(
            f"C {f(b[0] + (c[0] - a[0]) / 6)} {f(b[1] + (c[1] - a[1]) / 6)} "
            f"{f(c[0] - (e[0] - b[0]) / 6)} {f(c[1] - (e[1] - b[1]) / 6)} "
            f"{f(c[0])} {f(c[1])}"
        )
    return curve(" ".join(d), ink, width)


def heavy(
    x: float, base: float, content: str, cap: float, ink: str, length: float, grow: float
) -> str:
    """A run in a heavier face than Inter's boldest, in the ink box ``t`` gives
    the same arguments: the bold run set ``grow`` inside that box on every
    side, then laid down again moved ``grow`` each way round a circle, so the
    union of the copies strokes ``2 * grow`` wider."""
    x0, base0, cap0, length0 = x + grow, base - grow, cap - 2 * grow, length - 2 * grow
    out = [t(x0, base0, content, cap0, ink, weight="700", length=length0)]
    for k in range(12):
        a = math.radians(30 * k)
        out.append(
            t(
                x0 + grow * math.cos(a),
                base0 + grow * math.sin(a),
                content,
                cap0,
                ink,
                weight="700",
                length=length0,
            )
        )
    return "".join(out)


def notches(out: List[str], polygons: Sequence[str]) -> None:
    """Close, in ``INK``, the tips of a heavy run's notches where they narrow
    below what the model's mesh holds (under about 0.06 mm), so the drawing
    and the print agree there."""
    for points in polygons:
        out.append(f'<polygon points="{points}" fill="{INK}"/>\n')


def open_print(out: List[str], name: str, plane: str = PLANE) -> None:
    out.append(fronts.print_open(name, plane))
    if plane == PLANE:
        out.append(f'<g transform="{BACK_FRAME}">\n')


def close_print(out: List[str], plane: str = PLANE) -> None:
    if plane == PLANE:
        out.append("</g>\n")
    out.append(fronts.LEGEND_CLOSE)


# ---------------------------------------------------------------- the back

#: The EXT header's cells: their left edges, 2.727 mm apart, from u 32.61.
EXT_X0, EXT_PITCH = 32.61, 2.727
EXT_ROWS = (1.92, 4.56, 7.29)


def _ext_header(out: List[str]) -> None:
    """The EXT 2.54-14P header's pin table, as the header is seen from behind."""
    open_print(out, "ext-table")
    x1 = EXT_X0 + 7 * EXT_PITCH
    out.append(
        f'<path d="M 32.35 1.65 H {f(x1 + 0.26)} V 7.55 H 32.35 Z '
        f"M {f(EXT_X0)} {f(EXT_ROWS[0])} V {f(EXT_ROWS[2])} H {f(x1)} "
        f'V {f(EXT_ROWS[0])} Z" fill="{GRAY}" fill-rule="evenodd"/>\n'
    )
    for i in (1, 3, 5):
        x = EXT_X0 + i * EXT_PITCH
        out.append(box(x, EXT_ROWS[0], x + EXT_PITCH, EXT_ROWS[1], PALE_GRAY))
    x = EXT_X0 + 6 * EXT_PITCH
    out.append(box(x, EXT_ROWS[1], x + EXT_PITCH, EXT_ROWS[2], PALE_GRAY))
    fills = (RED, INK, VERMILION, GREEN, YELLOW)
    for i, fill in enumerate(fills):
        x = EXT_X0 + i * EXT_PITCH
        out.append(box(x, EXT_ROWS[1], x + EXT_PITCH, EXT_ROWS[2], fill))
    close_print(out)
    open_print(out, "ext-names")
    top = ("G3", "G4", "G6", "G40", "G14", "G39", "G5")
    for i, name in enumerate(top):
        cx = EXT_X0 + (i + 0.5) * EXT_PITCH
        out.append(
            t(
                cx,
                3.72,
                name,
                1.0,
                INK,
                weight="700",
                anchor="middle",
                length=1.62 if len(name) == 2 else 2.42,
            )
        )
    two = (("5V", "IN", WHITE), ("5V", "OUT", WHITE), ("G8", "SDA", INK), ("G9", "SCL", INK))
    for (upper, lower, ink), i in zip(two, (0, 2, 3, 4)):
        cx = EXT_X0 + (i + 0.5) * EXT_PITCH
        out.append(t(cx, 5.72, upper, 0.86, ink, weight="700", anchor="middle", length=1.42))
        out.append(
            t(
                cx,
                6.98,
                lower,
                0.86,
                ink,
                weight="700",
                anchor="middle",
                length=2.42 if len(lower) == 3 else 1.3,
            )
        )
    gnd_cx, gnd_cy = EXT_X0 + 1.5 * EXT_PITCH, 5.93
    out.append(
        rot(
            -45,
            gnd_cx,
            gnd_cy,
            t(gnd_cx, gnd_cy + 0.43, "GND", 0.86, WHITE, weight="700", anchor="middle", length=2.3),
        )
    )
    for name, i in (("G13", 5), ("G15", 6)):
        cx = EXT_X0 + (i + 0.5) * EXT_PITCH
        out.append(t(cx, 6.42, name, 0.92, INK, weight="700", anchor="middle", length=2.22))
    close_print(out)


def _mic(out: List[str]) -> None:
    """The microphone beside the header, and its line to the codec."""
    open_print(out, "mic")
    out.append(t(29.8, 4.25, "Mic", 0.95, GRAY, weight="400", length=2.1))
    # the capsule sits in a heavy cradle, whose bottom runs into a short stem
    # and a foot a little wider than it
    out.append(box(30.51, 4.71, 31.22, 6.18, ORANGE, r=0.355))
    out.append(arc(30.875, 5.8, 0.63, 0, 180, INK, 0.33))
    out.append(box(30.65, 6.5, 31.11, 6.85, INK))
    out.append(box(30.56, 6.78, 31.19, 6.96, INK))
    close_print(out)


def _audio(out: List[str]) -> None:
    """The headphone jack, the codec, the amplifier and the speaker."""
    open_print(out, "jack")
    out.append(
        f'<path d="M 1.7 8.68 L 2.06 8.3 H 3.2 V 8.75 H 4.42 V 10.9 H 3.2 V 11.35 '
        f'H 1.7 Z" fill="{GREEN}"/>\n'
    )
    out.append(box(4.85, 8.8, 6.15, 10.9, DARK_GRAY, r=0.1))
    out.append(box(6.6, 8.8, 7.9, 10.9, LIME, r=0.1))
    out.append(
        f'<path d="M 8.3 8.75 H 9.05 V 9.2 H 11.15 A 0.65 0.65 0 0 1 '
        f'11.15 10.5 H 9.05 V 10.9 H 8.3 Z" fill="{YELLOW}"/>\n'
    )
    close_print(out)
    open_print(out, "jack-pins")
    # GND into the sleeve; OUT_LR's bracket into the ring and the tip
    out.append(line([(4.75, 12.56), (5.535, 12.56), (5.535, 11.85)], PURPLE, TRACE))
    out.append(head(5.535, 11.2, -90, PURPLE, 0.72, 0.56))
    out.append(line([(7.6, 11.85), (7.6, 12.56), (8.79, 12.56)], PURPLE, TRACE))
    out.append(line([(8.79, 11.85), (8.79, 12.92)], PURPLE, TRACE))
    out.append(head(7.6, 11.2, -90, PURPLE, 0.72, 0.56))
    out.append(head(8.79, 11.2, -90, PURPLE, 0.72, 0.56))
    out.append(t(2.07, 12.87, "GND", 0.82, INK, length=2.32))
    out.append(t(5.85, 14.23, "OUT_LR", 0.87, INK, length=4.59))
    out.append(t(9.73, 12.69, "HP_DET", 0.96, INK, length=5.25))
    close_print(out)
    open_print(out, "hp-det")
    # from the tip's switch, through an inverting buffer, down to the amplifier;
    # the line stops at the word and starts again under it
    out.append(head(12.06, 11.55, 72, AZURE, 0.75, 0.53))
    out.append(line([(12.28, 12.88), (12.28, 13.64)], AZURE, TRACE))
    out.append(
        f'<path d="M 11.6 13.64 H 12.97 L 12.28 14.75 Z" fill="none" '
        f'stroke="{INK}" stroke-width="0.16" stroke-linejoin="miter"/>\n'
    )
    out.append(fronts.circle(12.28, 15.04, 0.29, stroke=INK, stroke_w=0.15))
    out.append(line([(12.28, 15.33), (12.28, 17.4)], AZURE, TRACE))
    out.append(head(12.27, 17.95, 90, AZURE, 0.6, 0.5))
    close_print(out)
    open_print(out, "headphones")
    out.append(arc(3.55, 15.45, 1.18, 180, 360, MAGENTA, 0.16))
    # the cups: hollow D outlines, their flat sides facing each other
    for flat, rx, sweep in ((2.49, 0.55, 1), (4.74, 0.53, 0)):
        out.append(
            f'<path d="M {f(flat)} 15.8 V 16.89 A {f(rx)} 0.545 0 0 {sweep} '
            f'{f(flat)} 15.8 Z" fill="none" stroke="{INK}" stroke-width="0.26" '
            'stroke-linejoin="miter"/>\n'
        )
    out.append(t(5.92, 15.85, "Output", 0.78, MAGENTA, length=3.85))
    out.append(t(5.92, 16.95, "Only", 0.78, MAGENTA, length=2.55))
    close_print(out)
    open_print(out, "speaker")
    out.append(
        f'<path d="M 3.58 18.4 L 4.2 19.15 H 4.85 V 20.25 H 4.2 L 3.58 21.0 Z" '
        f'fill="{PERIWINKLE}"/>\n'
    )
    out.append(arc(3.55, 19.7, 0.75, 135, 225, DARK_GRAY, 0.14))
    out.append(arc(3.55, 19.7, 1.35, 140, 220, DARK_GRAY, 0.14))
    out.append(line([(4.85, 19.7), (8.5, 19.7)], PURPLE, TRACE))
    out.append(t(5.8, 21.56, "1W", 0.92, INK, length=2.13))
    out.append(t(3.18, 23.07, "SPEAKER", 0.82, INK, length=4.65))
    close_print(out)
    # the codec and the amplifier
    open_print(out, "es8311")
    out.append(box(15.25, 8.3, 20.55, 13.25, BOX_GRAY, r=0.55))
    out.append(t(17.9, 10.75, "ES", 1.85, WHITE, weight="400", anchor="middle", length=3.75))
    out.append(t(17.9, 12.7, "8311", 0.95, WHITE, weight="400", anchor="middle", length=3.65))
    close_print(out)
    open_print(out, "ns4150")
    out.append(box(8.55, 18.1, 12.95, 22.4, BOX_GRAY, r=0.5))
    out.append(t(10.86, 20.45, "NS", 1.72, WHITE, weight="400", anchor="middle", length=2.63))
    out.append(t(10.8, 21.76, "4150", 0.72, WHITE, weight="400", anchor="middle", length=2.93))
    close_print(out)
    open_print(out, "audio-lines")
    # the microphone into the codec
    out.append(line([(30.1, 6.25), (27.3, 9.3), (21.55, 9.3)], PURPLE, TRACE))
    out.append(head(20.85, 9.3, 180, PURPLE, 0.6, 0.5))
    # the codec into the amplifier
    out.append(curve("M 16.15 13.45 V 17.6 Q 16.15 18.7 15.0 18.7 H 13.75", PURPLE, TRACE))
    out.append(head(13.05, 18.7, 180, PURPLE, 0.75, 0.6))
    close_print(out)
    open_print(out, "audio-rails")
    out.append(head(13.2, 21.6, 180, VERMILION, 0.42, 0.36))
    out.append(t(13.75, 22.02, "3V3", 0.9, VERMILION, weight="700", length=2.75))
    out.append(head(21.0, 11.6, 180, VERMILION, 0.42, 0.36))
    out.append(t(21.6, 12.05, "3V3", 0.9, VERMILION, weight="700", length=2.6))
    close_print(out)
    open_print(out, "i2s-pins")
    for i, (name, pin, a, b) in enumerate(
        (
            ("ASDOUT:", "G46", 6.025, 2.755),
            ("LRCK:", "G43", 3.788, 2.672),
            ("SCK:", "G41", 2.943, 2.307),
            ("DSDIN:", "G42", 4.541, 2.729),
        )
    ):
        out.extend(kv(17.67, 14.94 + i * 1.67, name, pin, 0.9, a, b))
    close_print(out)


def _usb_imu_stamp(out: List[str]) -> None:
    """USB-C, the BMI270, the StampS3A, the TCA8418 and their lines."""
    open_print(out, "usb")
    out.append(heavy(2.07, 25.75, "USB", 1.17, INK, 3.58, 0.015))
    notches(
        out,
        (
            "5.362,25.148 5.406,25.165 5.414,25.164 5.416,25.155 5.403,25.144 "
            "5.398,25.132 5.4,25.12 5.409,25.109 5.409,25.1 5.401,25.097 5.385,25.108 "
            "5.328,25.127 5.323,25.131 5.323,25.137 5.326,25.142",
        ),
    )
    out.append(heavy(2.2, 29.2, "C", 3.07, ORANGE, 3.25, 0.04))
    # the plug: a bracket whose back is the left wall of the receptacle's box
    out.append(
        curve(
            "M 5.86 24.975 H 6.735 A 0.48 0.48 0 0 1 7.215 25.455 V 28.49 "
            "A 0.48 0.48 0 0 1 6.735 28.97 H 5.86",
            INK,
            0.44,
        )
    )
    out.append(
        f'<path d="M 7.215 25.695 H 9.135 V 28.255 H 7.215 Z" fill="none" '
        f'stroke="{INK}" stroke-width="0.44" stroke-linejoin="round"/>\n'
    )
    out.append(fronts.circle(8.365, 26.505, 0.22, stroke=ORANGE, stroke_w=0.2))
    out.append(fronts.circle(8.365, 27.45, 0.22, stroke=ORANGE, stroke_w=0.2))
    out.append(t(4.6, 30.55, "OTG", 0.85, INK, weight="400", length=2.57))
    out.extend(kv(4.6, 32.4, "D-:", "G19", 0.85, 1.72, 2.12))
    out.extend(kv(4.6, 33.7, "D+:", "G20", 0.85, 1.98, 2.41))
    out.append(line([(3.6, 30.6), (3.6, 33.6)], AZURE, TRACE))
    out.append(head(3.6, 29.95, -90, AZURE, 0.62, 0.5))
    out.append(head(3.6, 34.25, 90, AZURE, 0.62, 0.5))
    close_print(out)
    open_print(out, "bmi270")
    out.append(box(13.05, 27.47, 17.29, 31.18, SKY, r=0.35))
    # the gyroscope: a ring on the box's edge, a disc seen tilted on its axle
    out.append(fronts.circle(12.0, 28.6, 1.2, fill=SKY))
    out.append(fronts.circle(12.0, 28.6, 1.31, stroke=INK, stroke_w=0.26))
    out.append(line([(11.3, 27.95), (11.85, 28.45)], INK, 0.24))
    disc = "M 11.23 28.52 A 0.74 0.38 0 1 0 12.71 28.52 A 0.74 0.38 0 1 0 11.23 28.52 Z"
    out.append(
        rot(
            -40,
            11.97,
            28.52,
            f'<path d="{disc}" fill="{CYAN}"/>\n'
            f'<path d="{disc}" fill="none" stroke="{INK}" stroke-width="0.12"/>\n',
        )
    )
    out.append(line([(11.97, 28.52), (12.72, 29.22)], INK, 0.24))
    for x, ch, length in ((13.484, "B", 1.124), (14.702, "M", 1.454), (16.165, "I", 0.646)):
        out.append(heavy(x, 29.389, ch, 1.602, INK, length, 0.05))
    notches(
        out,
        (
            "15.121,28.881 15.129,28.868 15.141,28.863 15.158,28.869 15.169,28.885 "
            "15.175,28.886 15.18,28.879 15.121,28.639 15.114,28.633 15.107,28.635 "
            "15.105,28.641 15.105,28.888 15.11,28.893 15.116,28.893 15.12,28.889",
            "15.69,28.887 15.703,28.87 15.718,28.868 15.731,28.877 15.738,28.895 "
            "15.743,28.897 15.75,28.892 15.751,28.641 15.746,28.634 15.739,28.634 "
            "15.735,28.639 15.676,28.883 15.679,28.889 15.684,28.89",
            "15.453,28.517 15.442,28.534 15.429,28.537 15.415,28.531 15.405,28.515 "
            "15.396,28.516 15.393,28.521 15.422,28.677 15.429,28.684 15.435,28.683 "
            "15.438,28.677 15.467,28.521 15.464,28.516 15.458,28.514",
            "14.402,28.56 14.389,28.542 14.39,28.532 14.396,28.518 14.39,28.511 "
            "14.382,28.514 14.352,28.543 14.355,28.551 14.394,28.573 14.4,28.571 "
            "14.403,28.566",
        ),
    )
    out.append(t(13.83, 31.03, "270", 1.34, BOX_GRAY, weight="400", length=2.62))
    out.extend(kv(12.32, 32.4, "SCL:", "G9", 0.85, 2.67, 1.67))
    out.extend(kv(12.32, 33.7, "SDA:", "G8", 0.85, 2.92, 1.72))
    out.append(line([(11.8, 30.3), (11.25, 31.4), (11.25, 33.65)], AZURE, TRACE))
    out.append(head(11.25, 34.3, 90, AZURE, 0.65, 0.5))
    close_print(out)
    open_print(out, "stamp-s3a")
    out.append(box(2.42, 35.0, 15.64, 38.44, INK, r=0.9))
    out.append(box(2.42, 37.4, 15.64, 38.44, INK))
    out.append(ring(2.42, 35.0, 15.64, 46.77, 0.9, INK, 0.4))
    out.append(t(3.74, 37.81, "STAMP", 2.12, WHITE, weight="700", length=10.58))
    # each letter set to the ink box the photo gives it (its 3's top is flat,
    # where Inter's is round)
    for x, ch, length in ((3.225, "S", 3.91), (7.015, "3", 3.822), (10.437, "A", 4.294)):
        out.append(t(x, 44.55, ch, 4.473, RED, weight="700", length=length))
    out.append(t(2.42, 49.04, "ESP32", 1.56, VERMILION, weight="400", length=6.51))
    out.append(t(8.76, 49.04, "S3FN8", 1.56, VERMILION, weight="700", length=6.8))
    out.append(box(21.6, 48.15, 23.3, 48.65, RED, r=0.1))
    close_print(out)
    open_print(out, "tca8418")
    out.append(box(17.95, 36.0, 23.75, 41.45, BOX_GRAY, r=0.55))
    out.append(t(20.85, 38.45, "TCA", 1.45, WHITE, weight="400", anchor="middle", length=4.15))
    out.append(t(20.85, 40.4, "8418", 1.05, WHITE, weight="400", anchor="middle", length=4.2))
    out.extend(kv(21.5, 43.05, "SCL:", "G9", 0.8, 2.49, 1.55))
    out.extend(kv(21.5, 44.42, "SDA:", "G8", 0.8, 2.54, 1.5))
    out.extend(kv(21.4, 45.94, "INT:", "G11", 0.8, 2.28, 1.86))
    out.append(line([drawn(24.06, 36.05), drawn(27.4, 31.2)], INK, TRACE))
    out.append(head(*drawn(27.95, 30.42), -55.4, INK, 0.72, 0.5))
    out.append(line([(24.1, 40.6), (27.2, 41.1)], INK, TRACE))
    out.append(head(27.95, 41.22, 9, INK, 0.75, 0.5))
    close_print(out)
    open_print(out, "i2c-lines")
    out.append(curve("M 20.25 42.7 V 45.0 Q 20.25 45.55 19.7 45.55 H 16.75", AZURE, TRACE))
    out.append(head(20.25, 41.95, -90, AZURE, 0.75, 0.55))
    out.append(head(16.05, 45.55, 180, AZURE, 0.75, 0.55))
    close_print(out)
    open_print(out, "rails-3v3")
    for x, base, tip in ((15.14, 26.25, (16.3, 26.85)), (21.3, 34.53, (22.46, 35.15))):
        out.append(t(x, base, "3V3", 0.8, VERMILION, weight="700", length=2.33))
        out.append(head(tip[0], tip[1], 90, VERMILION, 0.4, 0.34))
    close_print(out)


def _power(out: List[str]) -> None:
    """The charger, the switch, the battery, the two MOSFETs and the regulators."""
    open_print(out, "usb-5vin")
    # from a gap after the plug, under the word, up to the azure line, where
    # it breaks to pass under it; then a shallow wave into a broad head
    out.append(
        spline(
            [
                (10.05, 26.35),
                (11.15, 26.34),
                (12.15, 26.15),
                (13.15, 25.73),
                (14.15, 25.21),
                (15.15, 24.67),
                (16.15, 24.33),
                (16.72, 24.26),
            ],
            VERMILION,
            TRACE,
        )
    )
    out.append(
        spline(
            [
                (17.58, 24.16),
                (18.15, 24.09),
                (18.65, 24.11),
                (19.15, 24.21),
                (19.65, 24.32),
                (20.15, 24.35),
                (20.78, 24.33),
            ],
            VERMILION,
            TRACE,
        )
    )
    tip, base_top, base_bottom = drawn(22.25, 24.29), drawn(21.07, 23.85), drawn(21.07, 24.73)
    out.append(
        f'<polygon points="{f(tip[0])},{f(tip[1])} {f(base_top[0])},{f(base_top[1])} '
        f'{f(base_bottom[0])},{f(base_bottom[1])}" fill="{VERMILION}"/>\n'
    )
    out.append(
        rot(-4.5, 9.84, 25.77, t(9.84, 25.77, "5VIN", 0.95, VERMILION, weight="700", length=3.2))
    )
    close_print(out)
    open_print(out, "chg-ic")
    out.append(box(22.66, 21.75, 28.45, 23.4, VERMILION, r=0.3))
    out.append(box(22.66, 23.1, 28.45, 25.45, SALMON, r=0.3))
    out.append(box(22.66, 23.1, 28.45, 23.5, SALMON))
    out.append(t(25.43, 22.85, "CHG-IC", 0.82, WHITE, weight="700", anchor="middle", length=4.55))
    out.append(t(25.55, 24.95, "TP4057", 0.98, INK, weight="500", anchor="middle", length=4.85))
    close_print(out)
    open_print(out, "bat-in")
    out.append(
        rot(-5, 28.9, 22.55, t(28.9, 22.55, "BAT-IN", 0.95, VERMILION, weight="700", length=4.5))
    )
    out.append(
        line(
            [
                (28.7, 23.12),
                (31.5, 23.08),
                (32.0, 23.03),
                (33.0, 22.88),
                (34.0, 22.67),
                (35.0, 22.33),
                (35.5, 22.05),
                (36.0, 21.74),
                (36.5, 21.32),
                (37.0, 20.78),
                (37.5, 20.23),
                (38.0, 19.8),
                (38.5, 19.41),
                (39.0, 19.19),
                (39.4, 19.09),
                (40.1, 18.95),
            ],
            VERMILION,
            TRACE,
        )
    )
    out.append(head(40.88, 18.93, 0, VERMILION, 0.85, 0.8))
    # the divider's top lead leaves the trace here
    out.append(line([(37.96, 19.84), (38.85, 21.05)], VERMILION, TRACE))
    close_print(out)
    open_print(out, "switch")
    out.append(t(30.1, 8.6, "SWITCH", 0.75, INK, weight="700", length=4.5))
    out.append(box(29.1, 8.9, 35.4, 12.75, M5_BLUE, r=1.92))
    out.append(fronts.circle(33.75, 10.82, 1.45, fill=WHITE))
    out.append(t(33.72, 11.38, "ON", 1.12, INK, weight="700", anchor="middle", length=2.55))
    out.append(
        f'<polygon points="29.95,10.45 30.95,10.45 30.95,10.05 31.7,10.8 '
        f'30.95,11.55 30.95,11.15 29.95,11.15" fill="{CYAN}"/>\n'
    )
    out.append(line([(35.95, 11.7), (37.95, 11.7), (37.95, 13.25)], AZURE, TRACE))
    out.append(head(37.95, 13.95, 90, AZURE, 0.65, 0.5))
    close_print(out)
    open_print(out, "battery")
    out.append(box(43.6, 8.9, 44.55, 11.0, MAGENTA))
    out.append(ring(45.15, 8.1, 53.2, 11.8, 0.65, SALMON, TRACE))
    out.append(t(46.06, 10.95, "BAT", 2.0, INK, weight="700", length=6.31))
    out.append(t(45.7, 13.25, "1500mAh", 0.95, INK, weight="400", length=6.9))
    out.append(t(46.8, 14.85, "*INSIDE", 0.8, INK, weight="400", length=4.8))
    close_print(out)
    open_print(out, "mosfets")
    out.append(ring(35.685, 14.01, 40.375, 16.445, 1.2, INK, 0.2))
    # each letter of both MOS set to the ink box the photo gives it, heavy
    for x, ch, length, grow in (
        (36.422, "M", 1.278, 0.05),
        (37.718, "O", 0.903, 0.09),
        (38.674, "S", 0.854, 0.07),
    ):
        out.append(heavy(x, 15.891, ch, 1.38, INK, length, grow))
    out.append(ring(41.065, 17.545, 46.33, 20.26, 1.33, INK, 0.2))
    for x, ch, length, grow in (
        (41.903, "M", 1.395, 0.05),
        (43.352, "O", 1.018, 0.09),
        (44.405, "S", 1.027, 0.07),
    ):
        out.append(heavy(x, 19.618, ch, 1.501, INK, length, grow))
    close_print(out)
    open_print(out, "battery-lines")
    out.append(curve("M 39.3 13.45 Q 40.2 11.2 42.6 10.35", VERMILION, TRACE))
    out.append(head(43.4, 10.1, -18, VERMILION, 0.7, 0.55))
    out.append(head(39.05, 14.05, 110, VERMILION, 0.7, 0.55))
    out.append(curve("M 35.75 16.95 Q 34.3 18.6 34.44 21.3", VERMILION, TRACE))
    out.append(head(36.05, 16.5, -55, VERMILION, 0.7, 0.55))
    out.append(head(34.57, 22.15, 82, VERMILION, 0.9, 0.75))
    close_print(out)
    open_print(out, "divider")
    # its leads in the trace's ink down to the ground (the top one, joined to
    # the trace, is drawn with it under "bat-in")
    out.append(line([(38.97, 23.1), (38.97, 23.9)], VERMILION, TRACE))
    out.append(line([(38.97, 25.95), (38.97, 26.62)], VERMILION, TRACE))
    out.append(ring(38.2, 20.96, 39.77, 23.24, 0.1, INK, 0.24))
    out.append(ring(38.2, 23.79, 39.77, 26.06, 0.1, INK, 0.24))
    for y, x0, x1 in ((27.09, 38.15, 39.79), (27.62, 38.42, 39.54), (28.18, 38.7, 39.26)):
        out.append(line([(x0, y), (x1, y)], DARK_GRAY, 0.2))
    close_print(out)
    open_print(out, "vbat-sense")
    out.append(line([(38.9, 23.565), (33.2, 23.565), (16.75, 35.84)], AZURE, TRACE))
    out.append(head(16.15, 36.29, 143.3, AZURE, 0.7, 0.55))
    out.append(rot(-34, 20.7, 32.0, t(20.7, 32.0, "1/2VBAT:", 0.82, INK, weight="500", length=5.2)))
    out.append(rot(-34, 20.7, 32.0, t(25.9, 32.0, "G10", 0.82, INK, weight="700", length=2.3)))
    close_print(out)
    open_print(out, "codec-data")
    out.append(
        line([(17.2, 14.1), (17.2, 24.6), (18.2, 25.6), (18.2, 32.4), (16.45, 34.6)], AZURE, TRACE)
    )
    out.append(head(17.2, 13.4, -90, AZURE, 0.75, 0.55))
    out.append(head(15.95, 35.15, 128, AZURE, 0.75, 0.55))
    close_print(out)
    open_print(out, "cn809")
    out.append(head(43.69, 20.6, -90, AZURE, 1.15, 1.0))
    out.append(box(42.05, 22.0, 45.35, 25.3, BOX_GRAY, r=0.4))
    out.append(t(43.7, 23.85, "CN", 1.3, WHITE, weight="400", anchor="middle", length=2.6))
    out.append(t(43.7, 25.0, "809", 0.72, PALE_GRAY, weight="400", anchor="middle", length=2.0))
    out.append(head(43.69, 25.48, -90, VERMILION, 1.22, 1.0))
    out.append(t(41.88, 28.21, "5VIN", 1.16, VERMILION, weight="700", length=3.83))
    close_print(out)
    open_print(out, "bat-out")
    out.append(t(46.64, 18.27, "BAT_OUT", 0.8, VERMILION, weight="700", length=6.16))
    out.append(line([(46.25, 18.85), (55.1, 18.85)], VERMILION, TRACE))
    out.append(head(55.85, 18.85, 0, VERMILION, 0.75, 0.6))
    # the riser to the SY8089 leaves just above the line and bends in one long arc
    out.append(
        spline(
            [
                (53.22, 18.55),
                (53.25, 17.5),
                (53.34, 16.8),
                (53.47, 15.9),
                (53.64, 15.3),
                (53.82, 14.7),
                (54.07, 14.1),
                (54.43, 13.5),
                (54.92, 12.9),
                (55.71, 12.3),
                (56.5, 11.98),
                (57.5, 11.77),
                (58.5, 11.68),
                (60.62, 11.68),
            ],
            VERMILION,
            TRACE,
        )
    )
    out.append(head(61.6, 11.5, 0, VERMILION, 0.75, 0.6))
    out.append(curve("M 46.12 27.38 H 49.6 Q 51.75 27.38 51.75 25.0 V 20.0", VERMILION, TRACE))
    out.append(head(51.75, 19.3, -90, VERMILION, 0.75, 0.6))
    apex, left_, right_ = drawn(51.62, 22.38), drawn(51.0, 23.85), drawn(52.25, 23.85)
    out.append(
        f'<polygon points="{f(apex[0])},{f(apex[1])} {f(left_[0])},{f(left_[1])} '
        f'{f(right_[0])},{f(right_[1])}" fill="{INK}"/>\n'
    )
    out.append(line([drawn(50.92, 22.2), drawn(52.22, 22.2)], INK, 0.25))
    close_print(out)
    for name, (x0, y0, x1, y1, split), (top_len, bottom, bottom_len) in (
        ("dcdc-sy8089", (61.95, 9.2, 69.4, 13.9, 11.6), (5.65, "SY8089", 6.4)),
        ("dcdc-sy7088", (56.15, 16.85, 63.55, 21.65, 19.2), (5.7, "SY7088", 6.3)),
    ):
        open_print(out, name)
        out.append(box(x0, y0, x1, split + 0.4, MAGENTA, r=0.35))
        out.append(box(x0, split, x1, y1, PINK, r=0.35))
        out.append(box(x0, split, x1, split + 0.4, PINK))
        cx = (x0 + x1) / 2
        out.append(
            t(cx, split - 0.62, "DC/DC", 1.0, WHITE, weight="700", anchor="middle", length=top_len)
        )
        out.append(
            t(cx, y1 - 0.68, bottom, 1.08, INK, weight="500", anchor="middle", length=bottom_len)
        )
        close_print(out)
    open_print(out, "rails-out")
    out.append(head(64.55, 19.2, 0, VERMILION, 0.55, 0.55))
    out.append(t(65.4, 19.4, "5V", 1.15, VERMILION, weight="700", length=2.0))
    out.append(t(64.9, 20.85, "OUT", 1.15, VERMILION, weight="700", length=3.25))
    out.append(head(70.6, 11.45, 0, VERMILION, 0.55, 0.55))
    out.append(t(70.75, 11.9, "3V3", 1.0, VERMILION, weight="700", length=3.55))
    out.append(t(62.7, 25.3, "3V3", 1.0, VERMILION, weight="700", length=2.7))
    out.append(head(66.5, 24.85, 0, VERMILION, 0.55, 0.42))
    close_print(out)


def _port_a(out: List[str]) -> None:
    """PORT.A's pins as the right column prints them, and the 5 V switch."""
    open_print(out, "port-a")
    out.append(
        f'<polygon points="79.33,8.08 82.16,8.08 82.51,8.43 82.51,9.98 79.33,9.98" fill="{INK}"/>\n'
    )
    out.append(box(79.33, 9.98, 82.51, 11.77, VERMILION))
    out.append(box(79.33, 11.77, 82.51, 13.53, YELLOW))
    out.append(box(79.33, 13.53, 82.51, 15.3, PALE_GRAY))
    out.append(t(80.92, 9.5, "GND", 0.75, WHITE, weight="700", anchor="middle", length=2.45))
    out.append(t(80.92, 11.32, "*5V", 0.95, WHITE, weight="700", anchor="middle", length=2.4))
    out.append(t(80.92, 13.22, "G2", 1.15, INK, weight="700", anchor="middle", length=2.12))
    out.append(t(80.92, 14.94, "G1", 1.15, INK, weight="700", anchor="middle", length=1.82))
    close_print(out)
    open_print(out, "port-a-switch")
    out.append(heavy(77.61, 16.7, "5VOUT", 1.02, VERMILION, 4.67, 0.04))
    out.append(t(79.36, 23.3, "5VIN", 0.9, VERMILION, weight="700", length=3.0))
    out.append(t(80.05, 19.95, "SW", 0.9, INK, weight="700", length=2.15))
    out.append(f'<polygon points="81.15,18.15 82.05,18.15 81.6,17.55" fill="{DARK_GRAY}"/>\n')
    out.append(f'<polygon points="81.15,20.8 82.05,20.8 81.6,21.4" fill="{DARK_GRAY}"/>\n')
    out.append(f'<polygon points="79.72,17.3 80.28,17.3 80.0,17.8" fill="{VERMILION}"/>\n')
    out.append(
        curve(
            "M 80.0 17.75 V 18.45 Q 80.0 19.2 79.25 19.2 H 78.2 Q 76.9 19.2 76.9 17.8 "
            "V 12.9 Q 76.9 11.4 78.8 11.4",
            VERMILION,
            TRACE,
        )
    )
    out.append(head(79.25, 11.4, 0, VERMILION, 0.65, 0.5))
    out.append(
        curve(
            "M 78.8 10.65 Q 76.35 10.65 76.35 12.8 V 18.3 Q 76.35 20.1 78.2 20.1 "
            "H 79.1 Q 80.0 20.1 80.0 20.9 V 21.35",
            VERMILION,
            TRACE,
        )
    )
    out.append(head(79.25, 10.65, 0, VERMILION, 0.65, 0.5))
    out.append(head(80.0, 22.0, 90, VERMILION, 0.65, 0.5))
    close_print(out)


def _matrix(out: List[str]) -> None:
    """The keyboard's 8 x 7 matrix as the label draws it, under its name."""
    rows = (30.49, 32.03, 33.54, 35.07, 36.58, 38.09, 39.62, 41.1)
    cols = (32.38, 37.6, 42.85, 48.05, 53.35, 58.55, 63.85)
    open_print(out, "key-matrix")
    for y in rows:
        out.append(line([(30.7, y), (65.5, y)], KHAKI, 0.2))
    for x in cols:
        out.append(line([(x, 30.15), (x, 41.4)], DARK_GRAY, TRACE))
    close_print(out)
    open_print(out, "key-matrix-names")
    for i, x in enumerate(cols):
        out.append(t(x, 29.78, f"C{i}", 1.0, INK, weight="400", anchor="middle", length=1.3))
    for i, y in enumerate(rows):
        out.append(t(28.5, y + 0.48, f"Y{i}", 0.95, INK, weight="400", length=1.28))
    out.append(t(35.74, 42.9, "KEY MATRIX : 4x14", 1.0, INK, weight="400", length=14.64))
    close_print(out)


def _lcd(out: List[str]) -> None:
    """The LCD's name block and its pins."""
    open_print(out, "lcd")
    out.append(curve("M 67.72 31.9 V 24.37 H 79.88 L 80.98 25.47 V 31.9", BOX_GRAY, 0.2))
    # each character set apart to the ink box the photo gives it, in the
    # label's heavier face
    for x, ch, length in (
        (69.697, "1", 1.586),
        (71.222, ".", 1.434),
        (72.424, "1", 1.519),
        (74.077, "4", 3.008),
        (76.861, '"', 1.994),
    ):
        out.append(heavy(x, 28.271, ch, 2.841, INK, length, 0.05))
    out.append(t(68.4, 30.95, "IPS-LCD", 1.8, INK, weight="700", length=11.6))
    out.append(box(67.65, 31.85, 81.05, 34.6, INK))
    out.append(t(68.4, 34.0, "ST7789V2", 1.6, WHITE, weight="700", length=12.0))
    close_print(out)
    open_print(out, "lcd-pins")
    for x, base, key, value, a, b in (
        (67.66, 36.5, "DATA:", "G35", 3.98, 2.59),
        (75.1, 36.5, "RST:", "G33", 2.78, 2.52),
        (68.67, 38.15, "SCK:", "G36", 2.98, 2.58),
        (75.57, 38.15, "CS:", "G37", 1.95, 2.29),
        (69.55, 39.75, "RS:", "G34", 1.98, 2.57),
        (75.24, 39.75, "BL:", "G38", 1.94, 2.6),
    ):
        out.extend(kv(x, base, key, value, 0.9, a, b))
    close_print(out)


def _legend_and_logo(out: List[str]) -> None:
    """The POWER / DATA key, the M5 STACK logotype and the ADV flag."""
    open_print(out, "line-key")
    pts = []
    x0, y0, x1, y1, r = 62.55, 42.9, 73.05, 47.0, 0.85
    corner = lambda cx, cy, a0: [
        (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        for a in range(a0, a0 + 91, 15)
    ]
    pts += corner(x1 - r, y0 + r, -90) + corner(x1 - r, y1 - r, 0)
    pts += corner(x0 + r, y1 - r, 90) + corner(x0 + r, y0 + r, 180)
    pts.append(pts[0])
    out.extend(fronts.stamp_dashes(pts, INK, pitch=0.42, dash=0.24, width=0.12, lead=0.2))
    out.append(
        curve(
            "M 63.05 44.35 C 63.6 43.35 64.4 43.55 64.9 44.3 C 65.4 45.05 66.3 45.25 66.9 44.3",
            VERMILION,
            TRACE,
        )
    )
    out.append(line([(63.0, 46.0), (66.9, 46.0)], AZURE, TRACE))
    out.append(t(67.25, 44.68, "POWER", 0.85, VERMILION, weight="500", length=5.15))
    out.append(t(67.25, 46.3, "DATA", 0.72, PERIWINKLE, weight="500", length=3.65))
    close_print(out)
    open_print(out, "m5-stack")
    # the M flat-topped, its diagonals leaving the stems' inner top corners
    out.append(
        f'<polygon points="74.47,47.33 74.47,42.7 75.1,42.7 76.43,44.42 77.77,42.7 '
        f"78.37,42.7 78.37,47.33 77.74,47.33 77.74,43.94 76.43,45.78 75.1,43.94 "
        f'75.1,47.33" fill="{M5_BLUE}"/>\n'
    )
    out.append(
        f'<path d="M 81.72 43.0 H 79.085 V 44.685 H 80.31 '
        f'A 1.165 1.165 0 0 1 80.31 47.015 H 78.77" '
        f'fill="none" stroke="{M5_BLUE}" stroke-width="0.63" '
        'stroke-linejoin="miter" stroke-linecap="butt"/>\n'
    )
    out.append(t(74.41, 49.03, "ST", 1.42, INK, weight="700", length=2.7))
    # STACK's A is a lambda: no bar, a flat top level with the S and T
    out.append(
        f'<polygon points="76.95,49.02 77.62,47.63 78.23,47.63 78.71,49.02 '
        f'78.17,49.02 77.9,48.09 77.49,49.02" fill="{INK}"/>\n'
    )
    out.append(t(78.7, 49.03, "CK", 1.42, INK, weight="700", length=3.06))
    close_print(out)
    open_print(out, "adv-flag")
    out.append(
        f'<polygon points="53.68,43.55 57.95,43.55 64.71,49.84 60.21,49.84" fill="{AZURE}"/>\n'
    )
    # set along the band (x) and across it (y, up being -y): each letter to the
    # ink box the photo gives it
    out.append(
        rot(
            45,
            0,
            0,
            "".join(
                t(x, -8.088, ch, 1.722, WHITE, weight="700", length=length)
                for x, ch, length in (
                    (71.962, "A", 1.916),
                    (73.984, "D", 2.253),
                    (76.425, "V", 1.604),
                )
            ),
        )
    )
    close_print(out)


def back(out: List[str]) -> None:
    """Every print of the ADV's back sticker, in the back frame."""
    _ext_header(out)
    _mic(out)
    _audio(out)
    _usb_imu_stamp(out)
    _power(out)
    _port_a(out)
    _matrix(out)
    _lcd(out)
    _legend_and_logo(out)


# ---------------------------------------------------------------- the top and the left


def turned(
    deg: int,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    parts: Sequence[Tuple[str, str, float]],
    ink: str,
) -> str:
    """A run of one or more weights set in the box (x0, y0)-(x1, y1) of the
    drawing, turned ``deg`` degrees about the box's center: 180 for a print
    that reads upside down in its face's frame (its baseline at y0, its run
    from x1 back to x0), 90 for one that reads down the frame (its baseline
    at x0, its run from y0 to y1). ``parts`` are (text, weight, length) in
    reading order; the capitals stand across the box."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if deg == 180:
        cap = y1 - y0
    elif deg == 90:
        cap = x1 - x0
    else:
        raise ValueError(deg)
    total = sum(length for _, _, length in parts)
    x = cx - total / 2
    body = []
    for content, weight, length in parts:
        body.append(t(x, cy + cap / 2, content, cap, ink, weight=weight, length=length))
        x += length
    return rot(deg, cx, cy, "".join(body))


def _press_mark(x: float, y: float, arc_ink: str) -> str:
    """The label's press mark: a finger pointing left into a ring open on
    its right, seen as the top's frame turns it (x, y: the ring's center)."""
    return (
        arc(x, y, 0.55, 45, 315, arc_ink, 0.2)
        + f'<path d="M {f(x + 0.05)} {f(y - 0.22)} H {f(x + 1.25)} V {f(y - 0.75)} '
        f"H {f(x + 2.15)} L {f(x + 2.3)} {f(y - 0.55)} V {f(y + 0.55)} "
        f"L {f(x + 1.6)} {f(y + 1.0)} L {f(x + 1.15)} {f(y + 0.5)} "
        f'L {f(x + 1.15)} {f(y + 0.22)} H {f(x + 0.05)} Z" fill="none" '
        f'stroke="{INK}" stroke-width="0.14" stroke-linejoin="round"/>\n'
    )


def top(out: List[str]) -> None:
    """The top edge's sticker, in the top frame: the front at the bottom, so
    every print the board's user reads from the keyboard side reads upside
    down here."""
    open_print(out, "ir-led", "strip")
    out.append(f'<path d="M 6.3 9.45 L 6.82 10.6 A 0.58 0.58 0 1 1 5.78 10.6 Z" fill="{RED}"/>\n')
    for a in (0, 40, 90, 140, 180):
        r0, r1 = 1.0, 1.45
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        out.append(
            line([(6.3 + r0 * ca, 10.75 + r0 * sa), (6.3 + r1 * ca, 10.75 + r1 * sa)], SALMON, 0.12)
        )
    out.append(
        turned(180, 3.61, 12.58, 10.46, 13.75, (("IR", "400", 1.6), ("G44", "700", 5.25)), INK)
    )
    close_print(out, "strip")
    open_print(out, "btn-rst", "strip")
    out.append(_press_mark(20.15, 13.85, MAGENTA))
    out.append(
        turned(180, 18.86, 16.03, 26.56, 17.38, (("Btn", "400", 2.85), ("Rst", "700", 4.85)), INK)
    )
    close_print(out, "strip")
    open_print(out, "micro-sd", "strip")
    out.append(f'<polygon points="28.32,13.4 30.85,13.4 29.58,14.7" fill="{ORANGE}"/>\n')
    out.append(
        f'<path d="M 32.3 12.6 H 35.85 Q 36.15 12.6 36.15 12.9 V 17.04 '
        f'Q 36.15 17.34 35.85 17.34 H 32.75 L 32.0 16.6 V 12.9 Q 32.0 12.6 32.3 12.6 Z" '
        f'fill="{INK}"/>\n'
    )
    out.append(turned(180, 32.75, 13.1, 35.4, 15.5, (("SD", "700", 2.65),), WHITE))
    out.append(turned(180, 32.65, 15.65, 35.3, 16.33, (("MICRO", "700", 2.65),), WHITE))
    for y0, key, key_len, value in (
        (9.97, "CS:", 2.2, "G12"),
        (11.41, "MOSI:", 4.74, "G14"),
        (12.92, "MISO:", 4.91, "G39"),
        (14.44, "SCK:", 4.06, "G40"),
    ):
        x1 = 37.09 + 3.38 + key_len
        out.append(
            turned(
                180, 37.09, y0, x1, y0 + 0.92, ((key, "500", key_len), (value, "700", 3.38)), INK
            )
        )
    close_print(out, "strip")
    open_print(out, "switch-g0", "strip")
    out.append(turned(180, 46.95, 16.0, 55.85, 17.4, (("OFF/ON", "700", 8.9),), INK))
    out.append(
        turned(180, 58.78, 16.03, 65.8, 17.38, (("Btn", "400", 3.45), ("G0", "700", 3.57)), INK)
    )
    close_print(out, "strip")
    open_print(out, "stamp-name", "strip")
    out.append(_press_mark(67.15, 11.35, AZURE))
    out.append(turned(180, 71.1, 11.03, 80.12, 14.48, (("S3A", "700", 9.02),), RED))
    out.append(turned(180, 71.24, 15.1, 80.29, 16.55, (("STAMP", "700", 9.05),), INK))
    out.append(f'<polygon points="68.25,17.0 70.85,17.0 69.55,15.85" fill="{ORANGE}"/>\n')
    close_print(out, "strip")


def left(out: List[str]) -> None:
    """The left side's sticker round the Grove port, in the left frame: the
    back on the left, the front on the right, so its words read down."""
    open_print(out, "grove-pins", "side")
    for y0, y1, fill in (
        (3.0, 4.95, INK),
        (4.95, 8.0, VERMILION),
        (8.0, 10.6, YELLOW),
        (10.6, 12.95, PALE_GRAY),
    ):
        out.append(box(14.65, y0, 16.95, y1, fill))
    for y0, y1, name, ink in (
        (3.4, 4.65, "G", WHITE),
        (5.3, 7.7, "5V", WHITE),
        (8.3, 10.25, "G2", INK),
        (10.9, 12.65, "G1", INK),
    ):
        out.append(turned(90, 15.05, y0, 16.5, y1, ((name, "700", y1 - y0),), ink))
    out.append(turned(90, 15.52, 13.7, 16.38, 17.95, (("PORT.A", "700", 4.25),), VERMILION))
    close_print(out, "side")
    open_print(out, "five-volt-switch", "side")
    out.append(f'<polygon points="13.75,15.3 14.7,15.3 14.22,16.0" fill="{INK}"/>\n')
    out.append(turned(90, 13.78, 16.05, 14.73, 19.7, (("5VIN", "400", 3.65),), INK))
    out.append(turned(90, 12.17, 14.95, 13.27, 19.95, (("5VOUT", "400", 5.0),), INK))
    out.append(f'<polygon points="12.2,20.8 13.15,20.8 12.68,20.1" fill="{INK}"/>\n')
    close_print(out, "side")
