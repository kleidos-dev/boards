# SPDX-License-Identifier: MIT
"""What the M5StickS3 prints on its back: the sticker in the back's recess

``emit_back_svg.py`` calls :func:`append_back` to draw the sticker's print in
``sticks3/svg/back.svg``, one legend group on the plane ``label``; the model
lays it on the sticker's paper (``sticks3/model/spec.json``, the
``back_label`` solid and the ``label_legends`` mesh).

Back frame (``board_faces.py``): 1 mm a unit, seen from behind with the HAT2
end up, x from the case's left edge as seen from behind, y down from its top
edge. The sticker covers x 1.66..22.34, y 0.28..37.38, and its print stops
0.02 mm inside that: its top edge lies
over the open HAT2 end, its bottom corners are rounded.

Every position, size and ink was measured on M5Stack's straight-on photo of
the back (the shop's gallery, 16.8 px a millimeter), where the paper prints
in a geometric sans: the runs here are set in Inter, the only face the model
carries, each stretched (``textLength``) so its ink covers the photo's. The
two rows of HAT2 cells are 2.58 mm wide, the header's pitch, from the paper's
left edge to its right.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import emit_front_svg as fronts

f = fronts.f

#: The sticker's paper, = the model's ``back_label`` solid (back frame).
PAPER = (1.66, 0.28, 22.34, 37.38)
PAPER_R = 1.2  # its two bottom corners
PAPER_INK = "#eeefee"  # the model's back_label material

# Inks, sampled on the photo's flat fields (the paper reads #eeefee there).
BLACK = "#111113"
WHITE = "#ffffff"
CELL_LIGHT = "#cbcbcb"  # the lighter HAT2 cells; the SW part's lower half
CELL_MID = "#b3b3b3"  # the darker HAT2 cells; the switch's disc
VERMILION = "#cf3101"  # the traces and their names, EXT 5V, Espressif, CHG-IC
DARK_RED = "#940606"  # 5VIN, G46, the LDOs' upper halves, the hand's arc
YELLOW = "#fdcd03"  # BAT, G9
MAGENTA = "#f20461"  # 3V3_L2, the battery's terminal
SALMON_RED = "#fb6761"  # IRTX, the battery
SALMON = "#ee9c99"  # the LDOs', CHG-IC's and SY7088's lower halves
BROWN = "#5d320b"  # the SY7088's upper half
CHIP = "#3a3a3a"  # the AW8737 and ES8311 tiles
BLUE = "#0283cc"  # the M5STICK-S3 banner, the M5 logotype, the S3 tile
PURPLE = "#6464fc"  # the LCD's frame and ST7789P3
STEEL = "#336594"  # KEY1:G11
PANEL = "#e4e4e3"  # the LCD's pin panel and PORT.A's
LILAC = "#fd98fc"  # KEY2:G12
GREEN = "#1d903f"  # the PM enables, the PM tile
DARK_GREEN = "#116d3c"  # G42
SAGE = "#679667"  # IRRX
ORANGE = "#f86514"  # the IR emitter's cone, the microphone, USB-C's pins
TAN = "#c88764"  # the IR emitter's beam
ROSE = "#bb3c68"  # the JW5712's upper half
PINK = "#ed6b96"  # the JW5712's lower half
SKY = "#aed9ea"  # the BMI270 tile
PLUM = "#5b155d"  # the triangle under OTG/DATA

TRACE = 0.12  # the traces' width
PITCH = 2.58  # a HAT2 cell, the header's 2.54 mm pitch as printed


# ---------------------------------------------------------------- shapes


def rect(u0: float, v0: float, u1: float, v1: float, ink: str, r: float = 0.0) -> str:
    corner = f' rx="{f(r)}" ry="{f(r)}"' if r else ""
    return (
        f'<rect x="{f(u0)}" y="{f(v0)}" width="{f(u1 - u0)}" height="{f(v1 - v0)}"'
        f'{corner} fill="{ink}"/>\n'
    )


def half_box(u0: float, v0: float, u1: float, v1: float, r: float, ink: str, top: bool) -> str:
    """A box with its two top (or two bottom) corners rounded."""
    if top:
        d = (
            f"M {f(u0)} {f(v1)} V {f(v0 + r)} A {f(r)} {f(r)} 0 0 1 {f(u0 + r)} {f(v0)} "
            f"H {f(u1 - r)} A {f(r)} {f(r)} 0 0 1 {f(u1)} {f(v0 + r)} V {f(v1)} Z"
        )
    else:
        d = (
            f"M {f(u0)} {f(v0)} H {f(u1)} V {f(v1 - r)} A {f(r)} {f(r)} 0 0 1 {f(u1 - r)} {f(v1)} "
            f"H {f(u0 + r)} A {f(r)} {f(r)} 0 0 1 {f(u0)} {f(v1 - r)} Z"
        )
    return f'<path d="{d}" fill="{ink}"/>\n'


def part(
    u0: float, u1: float, v0: float, vm: float, v1: float, r: float, upper: str, lower: str
) -> str:
    """A part's tile: its upper half in one ink over its lower half in another."""
    return half_box(u0, v0, u1, vm, r, upper, True) + half_box(u0, vm, u1, v1, r, lower, False)


def poly(points: Sequence[tuple[float, float]], ink: str) -> str:
    return f'<polygon points="{" ".join(f"{f(u)},{f(v)}" for u, v in points)}" fill="{ink}"/>\n'


def line(
    points: Sequence[tuple[float, float]], ink: str, width: float = TRACE, cap: str = "butt"
) -> str:
    d = " L ".join(f"{f(u)} {f(v)}" for u, v in points)
    return (
        f'<path d="M {d}" fill="none" stroke="{ink}" stroke-width="{f(width)}" '
        f'stroke-linejoin="round" stroke-linecap="{cap}"/>\n'
    )


def curve(d: str, ink: str, width: float = TRACE) -> str:
    return (
        f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{f(width)}" '
        'stroke-linejoin="round"/>\n'
    )


def spline(points: Sequence[tuple[float, float]], ink: str, width: float = TRACE) -> str:
    """A smooth trace through *points*, in order: each span a cubic whose tangents at its ends
    run from the point before to the point after (a Catmull-Rom curve), so a trace read off the
    photo point by point is drawn without corners."""
    pts = list(points)
    d = [f"M {f(pts[0][0])} {f(pts[0][1])}"]
    for i in range(len(pts) - 1):
        a, b = pts[max(i - 1, 0)], pts[i]
        c, e = pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        d.append(
            f"C {f(b[0] + (c[0] - a[0]) / 6)} {f(b[1] + (c[1] - a[1]) / 6)} "
            f"{f(c[0] - (e[0] - b[0]) / 6)} {f(c[1] - (e[1] - b[1]) / 6)} {f(c[0])} {f(c[1])}"
        )
    return curve(" ".join(d), ink, width)


def head(
    tip: tuple[float, float],
    toward: tuple[float, float],
    ink: str,
    length: float = 0.3,
    width: float = 0.3,
) -> str:
    """An arrowhead with its point at *tip*, pointing away from *toward*."""
    du, dv = tip[0] - toward[0], tip[1] - toward[1]
    n = math.hypot(du, dv)
    du, dv = du / n, dv / n
    bu, bv = tip[0] - du * length, tip[1] - dv * length
    return poly(
        [
            tip,
            (bu - dv * width / 2, bv + du * width / 2),
            (bu + dv * width / 2, bv - du * width / 2),
        ],
        ink,
    )


def dashes(
    a: tuple[float, float],
    b: tuple[float, float],
    ink: str,
    dash: float,
    gap: float,
    width: float = TRACE,
) -> list[str]:
    """A dashed straight line from *a* to *b*, each dash drawn (a legend has no dash pattern)."""
    n = math.hypot(b[0] - a[0], b[1] - a[1])
    du, dv = (b[0] - a[0]) / n, (b[1] - a[1]) / n
    out, s = [], 0.0
    while s < n:
        e = min(s + dash, n)
        out.append(
            line([(a[0] + du * s, a[1] + dv * s), (a[0] + du * e, a[1] + dv * e)], ink, width)
        )
        s += dash + gap
    return out


def arc(cu: float, cv: float, r: float, a0: float, a1: float, ink: str, width: float) -> str:
    """A circular arc about (cu, cv) from angle a0 round to a1, the angles in degrees with y
    down, so the arc turns clockwise on the page (0 is to the right, 90 below)."""
    p0, p1 = math.radians(a0), math.radians(a1)
    turn = (a1 - a0) % 360
    return (
        f'<path d="M {f(cu + r * math.cos(p0))} {f(cv + r * math.sin(p0))} '
        f"A {f(r)} {f(r)} 0 {1 if turn > 180 else 0} 1 "
        f'{f(cu + r * math.cos(p1))} {f(cv + r * math.sin(p1))}" '
        f'fill="none" stroke="{ink}" stroke-width="{f(width)}"/>\n'
    )


def ce_letter(cu: float, cv: float, cut: float, outer: float = 1.90, inner: float = 1.34) -> str:
    """One letter of the CE mark: a ring's band from *outer* to *inner* about (cu, cv), the part
    left of the vertical line u = *cut* (cut < cu), so its two ends are square."""
    ho = math.sqrt(outer**2 - (cu - cut) ** 2)
    hi = math.sqrt(inner**2 - (cu - cut) ** 2)
    return (
        f'<path d="M {f(cut)} {f(cv - ho)} A {f(outer)} {f(outer)} 0 0 0 {f(cut)} {f(cv + ho)} '
        f'L {f(cut)} {f(cv + hi)} A {f(inner)} {f(inner)} 0 0 1 {f(cut)} {f(cv - hi)} Z" '
        f'fill="{BLACK}"/>\n'
    )


def ring(cu: float, cv: float, r: float, ink: str, width: float) -> str:
    return fronts.circle(cu, cv, r, fill="none", stroke=ink, stroke_w=width)


def disc(cu: float, cv: float, r: float, ink: str) -> str:
    return fronts.circle(cu, cv, r, fill=ink)


def ellipse(cu: float, cv: float, ru: float, rv: float, angle: float, ink: str) -> str:
    """A filled ellipse turned by *angle* degrees."""
    a = math.radians(angle)
    pu, pv = cu + ru * math.cos(a), cv + ru * math.sin(a)
    qu, qv = cu - ru * math.cos(a), cv - ru * math.sin(a)
    return (
        f'<path d="M {f(pu)} {f(pv)} A {f(ru)} {f(rv)} {f(angle)} 1 1 {f(qu)} {f(qv)} '
        f'A {f(ru)} {f(rv)} {f(angle)} 1 1 {f(pu)} {f(pv)} Z" fill="{ink}"/>\n'
    )


def run(
    content: str, x: float, base: float, size: float, length: float, weight: int, ink: str
) -> str:
    return (
        f'<text x="{f(x)}" y="{f(base)}" font-size="{f(size)}" fill="{ink}" '
        f'font-weight="{weight}" textLength="{f(length)}" lengthAdjust="spacingAndGlyphs">'
        f"{fronts._xml_escape(content)}</text>\n"
    )


def heavy_run(
    content: str, x: float, base: float, size: float, length: float, ink: str, grow: float
) -> str:
    """A run in a heavier face than Inter's boldest: the bold run set *grow* inside the ink box
    on every side, then laid down again moved *grow* each way round a circle, so the union of
    the copies has the same ink box and strokes 2 * *grow* wider."""
    cap = 0.727  # Inter's cap height, in ems
    inner = size - 2 * grow / cap
    x0, base0, length0 = x + grow, base - grow, length - 2 * grow
    out = [run(content, x0, base0, inner, length0, 700, ink)]
    for k in range(12):
        a = math.radians(30 * k)
        out.append(
            run(
                content,
                x0 + grow * math.cos(a),
                base0 + grow * math.sin(a),
                inner,
                length0,
                700,
                ink,
            )
        )
    return "".join(out)


# ---------------------------------------------------------------- text

#: Every horizontal run: (text, x, baseline, size, length, weight, ink). Each
#: line's runs share one size and one stretch, laid end to end, so the line's
#: ink spans what the photo prints.
TEXT = [
    # BEGIN TEXT
    ("G5", 2.080, 2.065, 1.270, 1.915, 700, BLACK),  # g5
    ("G4", 4.516, 2.065, 1.270, 2.163, 700, BLACK),  # g4
    ("G6", 7.140, 2.065, 1.270, 2.039, 700, BLACK),  # g6
    ("G7", 9.759, 2.065, 1.270, 1.969, 700, BLACK),  # g7
    ("G2", 17.504, 2.065, 1.270, 1.991, 700, BLACK),  # g2
    ("G3", 20.068, 2.065, 1.270, 1.913, 700, BLACK),  # g3
    ("G0", 7.141, 4.675, 1.349, 2.037, 700, BLACK),  # g0
    ("G1", 9.945, 4.675, 1.349, 1.578, 700, BLACK),  # g1
    ("G8", 12.321, 4.675, 1.349, 2.039, 700, BLACK),  # g8
    ("EXT", 4.423, 4.039, 1.111, 2.358, 700, WHITE),  # ext
    ("5V", 4.831, 4.941, 0.949, 1.485, 700, WHITE),  # ext5
    ("3V3", 17.275, 4.026, 1.033, 2.374, 700, WHITE),  # v33
    ("_L2", 17.510, 4.986, 1.047, 2.033, 700, WHITE),  # l2
    ("IRTX", 4.551, 6.760, 0.935, 2.455, 700, WHITE),  # irtx
    ("G46", 4.546, 7.891, 0.964, 2.427, 700, WHITE),  # g46
    ("IRRX", 16.928, 6.760, 0.935, 2.549, 700, WHITE),  # irrx
    ("G42", 17.047, 7.891, 0.964, 2.397, 700, WHITE),  # g42
    ("EXT5V", 5.193, 9.015, 0.644, 2.448, 700, VERMILION),  # ext5v_l
    ("EXT5V", 19.845, 6.107, 0.644, 2.448, 700, VERMILION),  # ext5v_r
    ("int5V", 19.872, 8.189, 1.081, 2.269, 700, VERMILION),  # int5v_r
    ("AW", 2.150, 9.560, 1.182, 2.261, 700, WHITE),  # aw
    ("8737", 2.168, 10.701, 0.910, 2.266, 700, WHITE),  # aw8737
    ("ES", 5.453, 10.407, 1.257, 1.858, 700, WHITE),  # es
    ("8311", 5.273, 11.600, 0.949, 2.204, 700, WHITE),  # es8311
    ("MCLK:", 7.838, 9.012, 0.874, 2.982, 400, BLACK),  # mclk+g18
    ("G18", 10.820, 9.012, 0.874, 1.730, 700, BLACK),  # mclk+g18
    ("DOUT:", 7.837, 9.841, 0.952, 3.007, 400, BLACK),  # dout+g14
    ("G14", 10.844, 9.841, 0.952, 1.766, 700, BLACK),  # dout+g14
    ("BCLK:", 7.837, 10.614, 0.874, 2.782, 400, BLACK),  # bclk+g17
    ("G17", 10.619, 10.614, 0.874, 1.685, 700, BLACK),  # bclk+g17
    ("LRCK:", 7.839, 11.445, 0.953, 2.722, 400, BLACK),  # lrck+g15
    ("G15", 10.560, 11.445, 0.953, 1.693, 700, BLACK),  # lrck+g15
    ("DIN:", 7.835, 12.217, 0.874, 1.979, 400, BLACK),  # din+g16
    ("G16", 9.815, 12.217, 0.874, 1.784, 700, BLACK),  # din+g16
    ('1.14" IPS-LCD', 13.406, 9.899, 1.111, 7.970, 700, BLACK),  # lcd
    ("ST7789P3", 13.892, 11.487, 1.228, 7.153, 700, WHITE),  # st7789
    ("MOSI:", 13.197, 12.748, 0.945, 2.717, 400, BLACK),  # mosi+g39
    ("G39", 15.914, 12.748, 0.945, 1.939, 700, BLACK),  # mosi+g39
    ("RST:", 18.150, 12.749, 0.867, 2.009, 400, BLACK),  # rst+g21
    ("G21", 20.159, 12.749, 0.867, 1.640, 700, BLACK),  # rst+g21
    ("SCK:", 13.645, 13.638, 0.949, 2.213, 400, BLACK),  # sck+g40
    ("G40", 15.858, 13.638, 0.949, 1.994, 700, BLACK),  # sck+g40
    ("CS:", 18.171, 13.638, 0.949, 1.515, 400, BLACK),  # cs+g41
    ("G41", 19.686, 13.638, 0.949, 1.696, 700, BLACK),  # cs+g41
    ("RS:", 14.390, 14.469, 0.949, 1.478, 400, BLACK),  # rs+g45
    ("G45", 15.868, 14.469, 0.949, 1.924, 700, BLACK),  # rs+g45
    ("BL:", 18.141, 14.472, 0.953, 1.444, 400, BLACK),  # bl+g38
    ("G38", 19.585, 14.472, 0.953, 1.960, 700, BLACK),  # bl+g38
    ("LDO", 9.647, 13.049, 0.715, 1.890, 700, WHITE),  # ldo1
    ("SSP7615", 8.901, 13.998, 0.714, 3.405, 700, BLACK),  # ssp1
    ("PM_", 2.084, 12.159, 0.809, 1.746, 700, GREEN),  # pm_spk
    ("SPK", 1.987, 12.929, 0.794, 1.848, 700, GREEN),  # spk
    ("_EN", 1.981, 13.717, 0.738, 1.720, 700, GREEN),  # spk_en
    ("VBUS", 3.906, 13.582, 0.794, 2.807, 700, VERMILION),  # vbus1
    ("BMI", 1.904, 14.718, 0.979, 1.731, 700, BLACK),  # bmi
    ("270", 2.072, 15.659, 0.874, 1.738, 400, BLACK),  # b270
    ("SCL:", 5.365, 15.008, 0.960, 2.177, 400, BLACK),  # scl+g48
    ("G48", 7.542, 15.008, 0.960, 2.033, 700, BLACK),  # scl+g48
    ("SDA:", 5.364, 15.898, 0.960, 2.316, 400, BLACK),  # sda+g47
    ("G47", 7.680, 15.898, 0.960, 1.986, 700, BLACK),  # sda+g47
    ("3V3_L1", 3.462, 16.917, 0.648, 2.770, 700, VERMILION),  # v33l1
    ("PM", 6.611, 16.530, 0.778, 1.428, 700, GREEN),  # pm_l3b
    ("L3B_EN", 6.613, 17.358, 0.812, 3.275, 700, GREEN),  # l3b_en
    ("3V3_L3B", 10.201, 17.140, 0.628, 3.889, 700, VERMILION),  # v33l3b
    ("LDO", 4.054, 17.857, 0.716, 1.763, 700, WHITE),  # ldo2
    ("SSP7615", 3.302, 18.804, 0.793, 3.345, 700, BLACK),  # ssp2
    ("R", 16.595, 16.080, 0.756, 0.478, 400, BLACK),  # rmark
    ("219-259730", 17.449, 16.134, 0.794, 4.695, 400, BLACK),  # r219
    ("SW", 10.002, 18.851, 0.815, 1.976, 700, WHITE),  # sw
    ("AW35122", 9.273, 19.914, 0.629, 3.386, 700, BLACK),  # aw35122
    ("PM", 2.058, 21.170, 1.374, 1.966, 400, WHITE),  # pm
    ("PM_3V3", 4.274, 20.219, 0.718, 2.858, 700, GREEN),  # pm3v3
    ("_L1_EN", 4.467, 20.980, 0.777, 2.796, 700, GREEN),  # l1en
    ("3V3_L2", 8.534, 21.761, 0.699, 3.308, 700, VERMILION),  # v33l2
    ("3V3_L0", 4.068, 22.295, 0.699, 3.237, 700, VERMILION),  # v33l0
    ("LDO", 4.469, 23.375, 0.795, 1.826, 700, WHITE),  # ldo3
    ("SSP7615", 3.779, 24.264, 0.793, 3.345, 700, BLACK),  # ssp3
    ("ALWAYS_ON", 3.320, 25.041, 0.559, 4.168, 700, BLACK),  # always
    ("PM_", 7.984, 22.591, 0.707, 1.784, 700, GREEN),  # pm_l2
    ("3V3_", 7.881, 23.363, 0.698, 2.066, 700, GREEN),  # v3_l2
    ("L2_EN", 7.984, 24.083, 0.628, 2.614, 700, GREEN),  # l2en
    ("ESP32", 12.520, 22.401, 0.733, 2.834, 400, BLACK),  # esp32+s3r8
    ("S3R8", 15.354, 22.401, 0.733, 2.377, 700, BLACK),  # esp32+s3r8
    ("Model Name: M5STICKS3", 11.478, 23.490, 0.869, 10.551, 400, BLACK),  # model
    ("FCC ID:2AN3W", 15.708, 24.679, 0.873, 6.232, 400, BLACK),  # fccid
    ("M5STICKS3", 17.138, 25.627, 0.871, 4.891, 400, BLACK),  # fccid2
    ("DC/DC", 9.948, 25.311, 0.819, 2.895, 700, WHITE),  # dcdc1
    ("JW5712", 9.860, 26.401, 0.794, 3.107, 700, BLACK),  # jw5712
    ("VBUS", 3.546, 26.636, 1.032, 3.111, 700, VERMILION),  # vbus2
    ("250", 2.226, 27.648, 0.795, 1.319, 700, BLACK),  # b250
    ("mAh", 2.038, 28.309, 0.816, 1.701, 700, BLACK),  # mah
    ("MOS", 5.389, 29.103, 0.668, 1.456, 700, BLACK),  # mos
    ("PM_ADC_EN", 5.492, 27.763, 0.628, 4.322, 700, GREEN),  # adc_en
    ("DC/DC", 11.783, 28.671, 1.022, 3.449, 700, WHITE),  # dcdc2
    ("SY7088", 11.756, 29.901, 0.952, 3.532, 700, BLACK),  # sy7088
    ("ST", 16.393, 30.651, 1.277, 1.817, 700, BLACK),  # stack
    ("CK", 19.546, 30.653, 1.278, 2.028, 700, BLACK),  # stack
    ("CHG-IC", 1.952, 30.303, 0.736, 3.083, 700, WHITE),  # chg
    ("LGS4056", 1.857, 31.267, 0.794, 3.418, 700, BLACK),  # lgs
    ("PM_ADC", 5.424, 30.315, 0.628, 3.545, 700, GREEN),  # pm_adc
    ("KEY1:G11", 14.387, 32.330, 1.430, 6.962, 400, WHITE),  # key1
    ("DM:", 3.634, 32.713, 0.694, 1.648, 400, BLACK),  # dm+g19
    ("G19", 5.282, 32.713, 0.694, 1.577, 700, BLACK),  # dm+g19
    ("DP:", 3.633, 33.433, 0.696, 1.436, 400, BLACK),  # dp+g20
    ("G20", 5.070, 33.433, 0.696, 1.790, 700, BLACK),  # dp+g20
    ("SW", 9.435, 33.403, 0.793, 1.425, 700, BLACK),  # sw2
    ("PM_EXT5V_EN", 11.209, 33.934, 0.635, 5.277, 700, GREEN),  # ext5v_en
    ("HOLD:", 16.594, 33.583, 0.795, 2.898, 400, BLACK),  # hold+boot
    ("BOOT", 19.492, 33.583, 0.795, 2.698, 700, BLACK),  # hold+boot
    ("USB", 2.774, 34.162, 0.735, 1.749, 700, BLACK),  # usb
    ("C", 4.497, 34.114, 0.643, 0.534, 700, VERMILION),  # usb_c
    ("OTG/", 5.466, 34.320, 0.893, 2.282, 400, BLACK),  # otg
    ("DATA", 5.340, 35.252, 0.898, 2.485, 400, BLACK),  # data
    ("Double:", 16.890, 34.471, 0.872, 3.458, 400, BLACK),  # double+off
    ("OFF", 20.348, 34.471, 0.872, 1.848, 700, BLACK),  # double+off
    ("PORT.A", 9.595, 35.300, 1.272, 4.732, 400, BLACK),  # porta
    ("Press:", 19.570, 35.303, 0.804, 2.839, 400, BLACK),  # press
    ("ON", 20.683, 36.075, 0.794, 1.477, 700, BLACK),  # on
    ("MIC", 5.129, 36.018, 0.636, 1.577, 700, BLACK),  # mic
    ("EXT", 10.125, 36.142, 0.734, 1.820, 700, WHITE),  # pext
    ("5V", 10.380, 36.848, 0.726, 1.256, 700, WHITE),  # p5v
    ("G9", 12.342, 36.548, 0.951, 1.402, 700, BLACK),  # g9
    ("G10", 14.135, 36.579, 1.053, 1.828, 700, BLACK),  # g10    # END TEXT
]

#: The turned runs: (text, x, baseline, size, length, weight, ink, cu, cv,
#: angle): set as above, then turned by angle degrees about (cu, cv), the
#: center of the line's ink.
ROT = [
    # BEGIN ROT
    ("G43", 12.061, 2.064, 1.111, 2.459, 700, BLACK, 13.29, 1.66, -45),  # g43
    ("G44", 14.573, 2.010, 1.111, 2.613, 700, BLACK, 15.88, 1.606, -45),  # g44
    ("GND", 1.627, 4.565, 1.031, 2.826, 700, WHITE, 3.04, 4.19, -45),  # gnd
    ("BAT", 14.710, 4.585, 1.086, 2.504, 700, BLACK, 15.98, 4.19, -45),  # bat
    ("5VIN", 19.565, 4.580, 1.058, 2.936, 700, WHITE, 21.02, 4.2, -45),  # v5in
    ("KEY2:", 0.288, 24.833, 1.191, 2.821, 700, BLACK, 2.55, 24.4, -90),  # key2
    ("G12", 3.110, 24.833, 1.191, 1.691, 700, BLACK, 2.55, 24.4, -90),  # key2
    ("IMU_INT:", 0.407, 17.703, 0.595, 3.620, 700, BLACK, 2.21, 17.52, -90),  # imu
    ("PMG4", 1.535, 18.043, 0.669, 2.492, 700, BLACK, 2.79, 17.8, -90),  # pmg4
    ("int5V", 7.313, 32.790, 1.003, 2.227, 700, VERMILION, 8.44, 32.41, -15),  # int5v_l
    ("GND", 8.222, 36.502, 0.830, 1.616, 700, WHITE, 9.03, 36.2, -45),  # pgnd    # END ROT
]


# ---------------------------------------------------------------- the print


def append_cells(out: list[str]) -> None:
    """The two rows of HAT2 cells across the paper's top, the pins as the back shows them."""
    x0, top, mid, bottom = 1.68, 0.30, 2.88, 5.49
    out.extend(
        rect(
            x0 + i * PITCH,
            top,
            x0 + (i + 1) * PITCH,
            mid,
            CELL_LIGHT if i % 2 == 0 else CELL_MID,
        )
        for i in range(8)
    )
    for i, ink in enumerate(
        (BLACK, VERMILION, CELL_MID, CELL_LIGHT, CELL_MID, YELLOW, MAGENTA, DARK_RED)
    ):
        out.append(rect(x0 + i * PITCH, mid, x0 + (i + 1) * PITCH, bottom, ink))
    # EXT and 5V, each underlined in white
    out.append(rect(4.45, 4.09, 6.50, 4.16, WHITE))
    out.append(rect(4.66, 5.07, 6.48, 5.14, WHITE))


def append_top_blocks(out: list[str]) -> None:
    """IRTX/G46, the banner, IRRX/G42, the IR emitter and the two EXT5V / int5V notes."""
    # the IR emitter: its beam over its cone, its lead below
    out.append(arc(2.85, 7.70, 1.33, 237.0, 303.0, TAN, 0.2))
    out.append(poly([(2.22, 7.00), (3.58, 7.00), (3.16, 7.78), (2.64, 7.78)], ORANGE))
    out.append(rect(2.90, 7.95, 3.02, 8.55, BLACK))
    out.append(part(4.35, 7.07, 5.80, 6.98, 8.27, 0.3, SALMON_RED, DARK_RED))
    out.append(rect(7.56, 5.88, 16.50, 8.13, BLUE))
    out.append(part(16.82, 19.70, 5.80, 6.98, 8.28, 0.3, SAGE, DARK_GREEN))
    # EXT5V under IRTX, the arrow from it
    out.append(head((4.83, 8.45), (4.83, 8.80), VERMILION, 0.24, 0.24))
    out.append(rect(5.10, 9.10, 7.66, 9.17, VERMILION))
    # EXT5V, the diode, int5V at the top right
    out.append(rect(19.85, 6.20, 22.20, 6.26, VERMILION))
    out.append(head((19.92, 6.60), (20.40, 6.60), VERMILION, 0.33, 0.30))
    out.append(rect(21.82, 6.26, 21.90, 6.46, VERMILION))
    out.append(poly([(21.60, 6.46), (22.10, 6.46), (21.85, 6.88)], BLACK))
    out.append(rect(21.60, 6.88, 22.10, 6.96, BLACK))
    out.append(rect(21.82, 6.96, 21.90, 7.16, VERMILION))
    out.append(head((21.86, 7.42), (21.86, 7.0), VERMILION, 0.27, 0.28))
    out.append(rect(19.85, 8.27, 22.20, 8.33, VERMILION))


def append_audio(out: list[str]) -> None:
    """The amplifier and codec tiles, their arrows, and the I2S pins."""
    out.append(rect(2.04, 8.53, 4.51, 10.78, CHIP, r=0.25))
    out.append(rect(4.66, 10.27, 4.99, 10.41, BLACK))
    out.append(rect(5.10, 9.31, 7.75, 11.85, CHIP, r=0.3))
    out.append(head((2.88, 11.07), (2.88, 11.5), GREEN, 0.3, 0.28))
    out.append(line([(5.27, 12.80), (4.71, 11.96)], VERMILION, 0.16))
    out.append(head((4.25, 11.24), (4.71, 11.96), VERMILION, 0.62, 0.46))
    out.append(line([(8.90, 12.95), (8.15, 12.95), (6.90, 11.92)], VERMILION))
    out.append(head((6.72, 11.76), (7.60, 12.50), VERMILION, 0.34, 0.32))


def append_lcd(out: list[str]) -> None:
    """The LCD's block: its framed name, ST7789P3 on purple, its pins on a gray panel."""
    out.append(
        f'<path d="M 12.93 8.48 H 21.33 L 22.04 9.12 V 10.22 H 12.93 Z '
        f'M 13.07 8.62 V 10.22 H 21.90 V 9.18 L 21.27 8.62 Z" '
        f'fill="{PURPLE}" fill-rule="evenodd"/>\n'
    )
    out.append(rect(12.93, 10.22, 22.04, 11.58, PURPLE))
    out.append(half_box(12.93, 11.58, 22.04, 14.55, 0.3, PANEL, False))


def append_power_top(out: list[str]) -> None:
    """The first LDO, the speaker enable, VBUS, the IMU and its pins, the second LDO."""
    out.append(part(8.90, 12.34, 12.33, 12.97, 14.18, 0.15, DARK_RED, SALMON))
    out.append(rect(3.93, 13.62, 6.68, 13.68, VERMILION))
    out.append(rect(1.99, 13.87, 3.99, 15.53, SKY, r=0.12))
    # the IMU's mark: a ringed disc, an outlined orbit across it and the axle through both
    out.append(disc(4.53, 14.93, 0.68, SKY))
    out.append(ring(4.53, 14.93, 0.65, BLACK, 0.1))
    out.append(ellipse(4.51, 14.95, 0.36, 0.21, -43, BLACK))
    out.append(ellipse(4.51, 14.95, 0.28, 0.13, -43, BLUE))
    out.append(line([(4.19, 14.61), (4.87, 15.28)], BLACK, 0.08))
    out.append(rect(2.58, 15.95, 2.70, 16.80, BLUE))
    out.append(head((2.47, 19.88), (2.47, 19.20), BLUE, 0.66, 0.38))
    out.append(head((4.74, 16.29), (4.48, 16.01), VERMILION, 0.38, 0.29))
    out.append(part(3.27, 6.66, 17.10, 18.10, 19.07, 0.15, DARK_RED, SALMON))
    # LDO -> 3V3_L3B, and its enable from PM_L3B_EN
    # the LDO's output down past 3V3_L3B and round under PM_L3B_EN to the switch, one trace
    out.append(
        spline(
            [
                (11.15, 14.18),
                (10.66, 15.58),
                (10.27, 16.62),
                (10.06, 17.10),
                (9.85, 17.42),
                (9.60, 17.65),
                (9.30, 17.80),
                (8.98, 17.96),
                (8.65, 18.15),
                (8.45, 18.42),
                (8.40, 18.80),
                (8.40, 19.50),
                (8.48, 19.85),
                (8.53, 20.15),
                (8.61, 20.42),
                (8.66, 20.70),
                (8.76, 20.95),
            ],
            VERMILION,
        )
    )
    # PM_L3B_EN's arrowhead at that bend, pointing up to its name
    out.append(poly([(8.45, 17.47), (8.12, 17.92), (8.86, 18.30)], GREEN))
    out.append(rect(7.93, 16.55, 8.40, 16.69, GREEN))
    out.append(line([(9.67, 16.50), (10.05, 15.24)], GREEN, 0.14))
    out.append(poly([(10.29, 14.45), (9.88, 15.25), (10.48, 15.22)], GREEN))
    out.append(curve("M 11.95 16.55 C 11.90 15.40 12.30 14.60 13.05 14.30", VERMILION))
    out.append(head((13.36, 14.16), (12.90, 14.38), VERMILION, 0.34, 0.32))
    # LDO -> its enable line back to the second LDO, and down the left
    # down to VBUS's hook, with a straight branch off it to the first DC/DC
    out.append(
        curve(
            "M 6.66 18.10 L 7.30 18.10 Q 7.69 18.10 7.69 18.50 L 7.69 25.80 "
            "Q 7.69 26.23 7.30 26.23 L 6.86 26.23",
            VERMILION,
        )
    )
    out.append(head((6.70, 18.10), (7.10, 18.10), VERMILION, 0.4, 0.34))
    out.append(line([(7.69, 25.16), (9.12, 25.16)], VERMILION))
    out.append(head((9.62, 25.14), (9.10, 25.14), VERMILION, 0.52, 0.40))


def append_marks(out: list[str]) -> None:
    """Japan's radio mark and its number, FC, CE, the Espressif tile,
    the WEEE bin, the M5 logotype."""
    gu, gv, gr = 15.14, 15.93, 1.05
    # the ring, broken on its right where the lightning stroke leaves it
    out.append(arc(gu, gv, gr, 26.0, 339.0, BLACK, 0.1))
    out.append(
        line(
            [
                (gu - gr + 0.02, 15.72),
                (15.17, 15.52),
                (15.22, 15.79),
                (gu + gr * math.cos(math.radians(-21)), gv + gr * math.sin(math.radians(-21))),
            ],
            BLACK,
            0.12,
        )
    )
    out.append(line([(14.60, 16.125), (15.78, 16.125)], BLACK, 0.12))
    out.append(line([(14.60, 16.405), (15.78, 16.405)], BLACK, 0.11))
    out.append(line([(15.185, 16.40), (15.185, 16.78)], BLACK, 0.11))
    out.append(fronts.stamp_box(16.36, 15.36, 17.37, 16.30, 0.0, BLACK, 0.08))
    # FC: the F's stem and arms, then the two Cs, open to the right
    out.append(rect(18.54, 16.40, 18.80, 18.61, BLACK))
    out.append(rect(18.54, 16.40, 19.62, 16.64, BLACK))
    out.append(rect(18.54, 17.33, 19.33, 17.57, BLACK))
    out.append(arc(20.33, 17.50, 0.98, 40.0, 320.0, BLACK, 0.24))
    out.append(arc(20.33, 17.50, 0.56, 45.0, 315.0, BLACK, 0.2))
    # CE: two equal rings cut square just left of their centers, the E's bar shorter than its arms
    out.append(ce_letter(19.56, 20.65, 19.42))
    out.append(ce_letter(22.06, 20.65, 21.86))
    out.append(rect(20.60, 20.39, 21.68, 20.95, BLACK))
    # Espressif: a white disc cut by vermilion arcs about a point low on its left
    out.append(rect(13.11, 17.47, 17.04, 21.40, VERMILION, r=0.45))
    ex, ev, er = 15.12, 19.33, 1.28
    out.append(disc(ex, ev, er, WHITE))
    au, av = ex - 0.62, ev + 0.82
    for radius in (0.42, 0.88, 1.34, 1.80):
        d = math.hypot(ex - au, ev - av)
        along = (radius**2 - er**2 + d**2) / (2 * d)
        across = math.sqrt(max(radius**2 - along**2, 0.0))
        ux, uy = (ex - au) / d, (ev - av) / d
        mx, my = au + ux * along, av + uy * along
        tp = math.degrees(math.atan2(my + ux * across - av, mx - uy * across - au))
        tq = math.degrees(math.atan2(my - ux * across - av, mx + uy * across - au))
        tu = math.degrees(math.atan2(uy, ux))
        if (tp - tu) % 360 > (tp - tq) % 360:
            tp, tq = tq, tp
        out.append(arc(au, av, radius, tq, tp, VERMILION, 0.16))
    out.append(disc(au + 0.05, av - 0.05, 0.2, WHITE))
    # the crossed-out wheelie bin (its domed lid and handle, its tapered body, the wheel at the
    # back and the foot at the front) and the bar under it
    out.append(
        curve(
            "M 14.13 24.50 C 14.13 24.36 14.25 24.32 14.45 24.32 H 14.95 "
            "C 15.15 24.32 15.27 24.36 15.27 24.50 Z",
            BLACK,
            0.07,
        )
    )
    out.append(line([(14.55, 24.32), (14.59, 24.24), (14.80, 24.24), (14.84, 24.32)], BLACK, 0.06))
    out.append(line([(14.55, 24.85), (14.83, 24.85)], BLACK, 0.06))
    out.append(line([(15.22, 24.62), (15.33, 24.62), (15.30, 24.76), (15.20, 24.76)], BLACK, 0.06))
    out.append(line([(14.20, 24.55), (14.33, 25.90), (14.90, 25.90)], BLACK, 0.07))
    out.append(line([(15.20, 24.55), (15.08, 25.70)], BLACK, 0.07))
    out.append(ring(15.03, 25.82, 0.13, BLACK, 0.06))
    out.append(disc(14.37, 25.93, 0.05, BLACK))
    out.append(line([(13.62, 24.07), (15.59, 26.18)], BLACK, 0.06))
    out.append(line([(15.70, 24.10), (13.66, 26.18)], BLACK, 0.06))
    out.append(rect(13.77, 26.63, 15.52, 27.04, BLACK))
    # M5: a geometric M (square tops, its V meeting between the stems) and a 5 whose bowl
    # reaches just past its top bar, outlines traced from the photo
    out.append(
        poly(
            [
                (16.40, 26.19),
                (16.83, 26.19),
                (17.785, 27.37),
                (18.74, 26.19),
                (19.17, 26.19),
                (19.17, 29.50),
                (18.74, 29.50),
                (18.74, 27.20),
                (17.785, 28.34),
                (16.83, 27.20),
                (16.83, 29.50),
                (16.40, 29.50),
            ],
            BLUE,
        )
    )
    out.append(
        f'<path d="M 19.50 26.18 H 21.58 V 26.62 H 19.95 V 27.36 H 20.575 '
        f"A 1.075 1.075 0 0 1 20.575 29.51 H 19.50 V 29.07 H 20.575 "
        f'A 0.635 0.635 0 0 0 20.575 27.80 H 19.50 Z" fill="{BLUE}"/>\n'
    )


def append_parts(out: list[str]) -> None:
    """The switch, the third LDO, the PM tile, KEY2, the DC/DCs, the charger, the battery."""
    out.append(part(9.12, 12.73, 18.10, 18.88, 19.93, 0.18, BLACK, CELL_LIGHT))
    out.append(head((11.20, 17.54), (11.20, 18.0), VERMILION, 0.42, 0.40))
    out.append(rect(1.99, 19.93, 4.27, 21.41, GREEN, r=0.25))
    out.append(head((5.40, 19.10), (5.40, 19.51), GREEN, 0.38, 0.27))
    out.append(line([(4.83, 21.19), (4.83, 21.52), (5.38, 21.52)], GREEN, 0.1))
    out.append(line([(3.77, 22.36), (3.77, 21.85)], VERMILION))
    out.append(head((3.77, 21.63), (3.77, 22.0), VERMILION, 0.3, 0.3))
    out.append(part(3.66, 7.16, 22.52, 23.47, 24.41, 0.15, DARK_RED, SALMON))
    out.append(rect(1.77, 21.97, 3.27, 26.78, LILAC, r=0.4))
    out.append(head((8.85, 24.80), (8.85, 24.35), GREEN, 0.45, 0.33))
    out.append(part(9.79, 12.96, 24.58, 25.40, 26.61, 0.18, ROSE, PINK))
    out.append(part(11.67, 15.42, 27.75, 28.58, 29.92, 0.18, BROWN, SALMON))
    out.append(part(1.88, 5.30, 29.53, 30.48, 31.48, 0.15, VERMILION, SALMON))
    out.append(rect(1.93, 28.47, 3.88, 29.40, SALMON_RED, r=0.15))
    out.append(rect(3.99, 28.72, 4.16, 29.11, MAGENTA))


def append_traces(out: list[str]) -> None:
    """The power tree's traces and arrows, and the enables' green arrows."""
    # 3V3_L2 up to the Espressif tile, and from the switch down to 3V3_L2
    out.extend(dashes((11.97, 21.47), (12.38, 21.04), VERMILION, 0.2, 0.12, 0.15))
    out.append(head((12.80, 20.66), (12.38, 21.04), VERMILION, 0.54, 0.58))
    out.append(head((10.36, 20.36), (10.36, 21.0), VERMILION, 0.83, 0.57))
    out.append(line([(10.98, 24.35), (10.98, 22.47)], VERMILION))
    out.append(head((10.98, 21.97), (10.98, 22.47), VERMILION, 0.5, 0.42))
    out.append(curve("M 11.10 23.75 Q 13.30 23.75 13.38 25.40 L 13.38 27.10", VERMILION))
    out.append(head((13.36, 27.72), (13.36, 27.10), VERMILION, 0.62, 0.52))
    # VBUS: up to ALWAYS_ON, its diode from the battery, and out to the right
    out.append(head((4.71, 25.17), (4.71, 25.72), VERMILION, 0.55, 0.46))
    out.append(head((4.71, 26.82), (4.71, 27.29), VERMILION, 0.47, 0.40))
    out.append(line([(4.71, 27.25), (4.71, 29.45)], VERMILION))
    out.append(line([(4.32, 28.83), (5.27, 28.83)], VERMILION))
    out.append(poly([(4.40, 28.28), (5.04, 28.28), (4.72, 27.72)], BLACK))
    out.append(rect(4.40, 27.60, 5.04, 27.72, BLACK))
    out.append(rect(3.54, 26.69, 6.66, 26.76, VERMILION))
    # the loop from the charger's output round the second DC/DC and back to VBUS, one trace:
    # the wave across under the charger, up round the right and in to its arrowhead at VBUS
    out.append(
        spline(
            [
                (8.22, 26.33),
                (8.55, 26.47),
                (8.90, 26.60),
                (9.28, 26.74),
                (9.62, 26.92),
                (9.94, 27.09),
                (10.23, 27.32),
                (10.49, 27.56),
                (10.72, 27.95),
                (10.87, 28.42),
                (10.92, 28.90),
                (10.89, 29.35),
                (10.80, 29.78),
                (10.65, 30.18),
                (10.42, 30.62),
                (10.22, 30.95),
                (9.98, 31.19),
                (9.75, 31.40),
                (9.50, 31.60),
                (9.22, 31.77),
                (8.90, 31.91),
                (8.50, 32.05),
                (8.05, 32.15),
                (7.55, 32.17),
                (7.10, 32.13),
                (6.70, 32.04),
                (6.30, 31.92),
                (5.90, 31.82),
                (5.40, 31.77),
                (4.90, 31.79),
                (4.40, 31.84),
                (4.00, 31.93),
                (3.60, 32.06),
                (3.25, 32.16),
                (2.67, 32.17),
            ],
            VERMILION,
        )
    )
    out.append(poly([(7.73, 26.18), (8.30, 26.18), (8.15, 26.58)], VERMILION))
    # the branch off it to the switch's diode
    out.append(line([(10.20, 30.98), (10.42, 31.26)], VERMILION))
    out.append(poly([(10.42, 27.65), (11.20, 28.10), (10.60, 28.50)], BLACK))
    out.append(line([(10.30, 27.90), (10.90, 27.55)], BLACK, 0.1))
    # MOS and the sense resistor, the ADC enables
    out.append(fronts.stamp_box(5.31, 28.48, 6.89, 29.24, 0.34, BLACK, 0.08))
    out.append(line([(6.93, 28.87), (7.58, 28.87)], VERMILION))
    out.append(fronts.stamp_box(7.655, 28.465, 8.955, 29.285, 0.0, BLACK, 0.13))
    out.append(head((6.02, 28.33), (6.02, 27.83), GREEN, 0.35, 0.28))
    out.append(curve("M 8.94 28.87 Q 9.95 28.95 9.95 29.95 Q 9.95 30.95 8.84 31.05", VERMILION))
    out.append(line([(8.70, 29.95), (9.73, 29.95)], GREEN))
    out.append(head((8.68, 29.95), (9.20, 29.95), GREEN, 0.34, 0.3))
    # the battery's three bars, each taller than the last, and its lead to the resistor
    out.append(rect(5.89, 30.98, 6.05, 31.33, CHIP))
    out.append(rect(6.26, 30.80, 6.43, 31.51, CHIP))
    out.append(rect(6.625, 30.60, 6.78, 31.66, CHIP))
    out.append(line([(6.78, 31.19), (7.235, 31.19)], VERMILION))
    out.append(fronts.stamp_box(7.31, 30.695, 8.625, 31.555, 0.0, BLACK, 0.15))
    # the charger's output up, and the wave across to int5V
    out.append(line([(2.67, 33.50), (2.67, 31.85)], VERMILION))
    out.append(head((2.67, 31.55), (2.67, 31.9), VERMILION, 0.32, 0.3))
    out.append(poly([(2.39, 33.21), (2.89, 33.21), (2.64, 32.80)], BLACK))
    out.append(rect(2.39, 32.69, 2.89, 32.80, BLACK))
    # the thin rule under the lower int5V, slanted with it
    out.append(line([(7.45, 33.15), (9.47, 32.61)], DARK_RED, 0.06))
    # the second DC/DC down to the switch's disc; the switch and its enable
    out.extend(dashes((12.45, 30.15), (12.17, 30.80), VERMILION, 0.25, 0.12))
    out.append(head((11.98, 31.42), (12.20, 30.90), VERMILION, 0.48, 0.42))
    out.append(disc(11.40, 31.87, 0.89, CELL_MID))
    out.append(poly([(10.30, 31.25), (11.05, 31.55), (10.55, 32.0)], BLACK))
    out.append(line([(10.18, 31.62), (10.70, 31.15)], BLACK, 0.12))
    out.append(
        spline(
            [
                (10.96, 31.90),
                (11.05, 32.08),
                (11.14, 32.26),
                (11.16, 32.50),
                (11.15, 33.00),
                (11.12, 33.50),
                (11.10, 33.95),
            ],
            VERMILION,
        )
    )
    out.extend(dashes((12.30, 33.45), (12.05, 32.55), GREEN, 0.25, 0.12))
    out.append(head((11.98, 32.14), (12.10, 32.6), GREEN, 0.42, 0.3))
    out.append(line([(12.87, 33.31), (12.87, 30.70)], GREEN))
    out.append(head((12.87, 30.31), (12.87, 30.7), GREEN, 0.42, 0.32))


def append_bottom(out: list[str]) -> None:
    """KEY1, USB-C, the microphone, PORT.A and its cells, the power key's hand."""
    out.append(rect(13.84, 30.98, 21.97, 32.53, STEEL, r=0.25))
    # USB-C: the receptacle's mouth, its shoulders curving into the body, the two pins
    out.append(
        '<path d="M 1.99 33.42 H 2.32 V 34.17 Q 2.32 34.29 2.44 34.29 H 4.96 '
        "Q 5.08 34.29 5.08 34.17 V 33.66 H 5.40 V 34.15 Q 5.40 34.42 5.15 34.53 "
        "Q 4.98 34.61 4.86 34.63 V 35.97 Q 4.86 36.09 4.74 36.09 H 2.67 "
        "Q 2.55 36.09 2.55 35.97 V 34.63 Q 2.40 34.60 2.22 34.48 Q 1.99 34.33 1.99 34.10 Z "
        f'M 2.89 34.61 H 4.52 V 35.77 H 2.89 Z" fill="{BLACK}" fill-rule="evenodd"/>\n'
    )
    out.append(rect(3.10, 35.07, 3.53, 35.43, ORANGE, r=0.05))
    out.append(rect(3.89, 35.07, 4.31, 35.43, ORANGE, r=0.05))
    out.append(rect(2.67, 33.55, 2.79, 34.07, VERMILION))
    # the microphone
    out.append(rect(6.81, 35.40, 7.35, 36.48, ORANGE, r=0.27))
    out.append(arc(7.07, 36.22, 0.50, 0.0, 180.0, BLACK, 0.17))
    out.append(rect(7.00, 36.66, 7.12, 36.94, BLACK))
    out.append(rect(6.88, 36.92, 7.24, 37.04, BLACK))
    out.append(poly([(5.56, 37.05), (6.21, 36.80), (5.85, 36.52)], PLUM))
    # PORT.A on its panel, and its four cells
    out.append(half_box(8.00, 34.05, 15.62, 37.30, 0.3, PANEL, False))
    for u0, u1, ink in (
        (8.10, 9.96, BLACK),
        (10.07, 11.96, VERMILION),
        (12.12, 13.96, YELLOW),
        (14.01, 15.62, WHITE),
    ):
        out.append(rect(u0, 35.48, u1, 36.92, ink))
    out.append(rect(10.22, 36.18, 11.80, 36.24, WHITE))
    # the power key's hand, pressing, and its rings
    out.append(arc(18.47, 36.00, 0.6, -70.0, 135.0, DARK_RED, 0.15))
    out.append(arc(18.47, 36.00, 0.86, -75.0, -30.0, SALMON, 0.08))
    out.append(arc(18.47, 36.00, 0.86, 95.0, 135.0, SALMON, 0.08))
    hand = [
        (16.93, 36.21),
        (17.19, 35.21),
        (17.71, 35.33),
        (17.79, 35.50),
        (18.43, 35.86),
        (18.57, 36.04),
        (18.43, 36.24),
        (17.86, 36.00),
        (17.79, 36.43),
        (17.36, 36.57),
        (16.93, 36.21),
    ]
    out.append(line(hand, BLACK, 0.13))


def append_text(out: list[str]) -> None:
    for content, x, base, size, length, weight, ink in TEXT:
        out.append(run(content, x, base, size, length, weight, ink))
    # the banner, in a face heavier than Inter's bold, as the label prints it
    out.append(heavy_run("M5STICK·S3", 7.833, 7.695, 1.904, 8.370, WHITE, 0.05))
    # the M's two notches between its stems and its V close where they narrow under 0.045 mm,
    # a sliver no mesh of the print keeps
    out.append(poly([(8.214, 7.05), (8.262, 7.25), (8.214, 7.25)], WHITE))
    out.append(poly([(8.783, 7.05), (8.735, 7.25), (8.783, 7.25)], WHITE))
    # STACK's A is a lambda: no bar, its flat top level with the S and T
    out.append(
        poly(
            [
                (18.20, 30.665),
                (18.62, 29.71),
                (19.05, 29.71),
                (19.44, 30.665),
                (19.04, 30.665),
                (18.84, 30.00),
                (18.56, 30.665),
            ],
            BLACK,
        )
    )
    for content, x, base, size, length, weight, ink, cu, cv, angle in ROT:
        out.append(
            f'<g transform="rotate({f(angle)} {f(cu)} {f(cv)})">\n'
            + run(content, x, base, size, length, weight, ink)
            + "</g>\n"
        )


def append_back(out: list[str]) -> None:
    """The sticker's print, one legend group on the plane ``label``, over its paper."""
    u0, v0, u1, v1 = PAPER
    r = PAPER_R
    out.append(
        f'<path d="M {f(u0)} {f(v0)} H {f(u1)} V {f(v1 - r)} '
        f"A {f(r)} {f(r)} 0 0 1 {f(u1 - r)} {f(v1)} H {f(u0 + r)} "
        f'A {f(r)} {f(r)} 0 0 1 {f(u0)} {f(v1 - r)} Z" fill="{PAPER_INK}"/>\n'
    )
    out.append(fronts.print_open("back-label", "label"))
    append_cells(out)
    append_top_blocks(out)
    append_audio(out)
    append_lcd(out)
    append_power_top(out)
    append_marks(out)
    append_parts(out)
    append_traces(out)
    append_bottom(out)
    append_text(out)
    out.append(fronts.LEGEND_CLOSE)


# ---------------------------------------------------------------- the left side

#: The strip in the front cap's pocket on the left side (left frame,
#: ``board_faces.py``: seen from the left with the HAT2 end up, x from the back
#: towards the front, y down from the top edge), 0.05 mm inside the pocket the
#: vendor's file cuts (z -5.68..-1.48, y 14.66..34.86): the model's
#: ``side_strip`` solid.
STRIP = (8.45, 13.25, 12.55, 33.35)
#: Where the blue S3 tile begins along the strip, from M5Stack's oblique
#: photo of the left side (the strip read along its length, 23.6 px a
#: millimeter there).
S3_TILE_V = 26.55
#: STICK's letters: each centered across the strip and at its own place along
#: it, reading from the top end down with their tops towards the front, in a
#: light face spaced wide. (letter, x, baseline) are its run before the
#: quarter turn about (10.5, center).
STICK_SIZE = 2.751
STICK = (
    ("S", -0.883, 0.997, 14.927),
    ("T", -0.888, 1.001, 17.698),
    ("I", -0.369, 1.001, 19.870),
    ("C", -1.011, 1.001, 22.134),
    ("K", -1.007, 1.001, 25.035),
)


def append_left(out: list[str]) -> None:
    """STICK in white on the black strip, then S3 in white on its blue tile, one legend group
    on the plane ``strip``."""
    u0, v0, u1, v1 = STRIP
    cu = (u0 + u1) / 2
    out.append(rect(u0, v0, u1, v1, "#1a1a1c"))
    out.append(fronts.print_open("stick-s3", "strip"))
    out.append(rect(u0, S3_TILE_V, u1, v1, BLUE))
    for letter, dx, dy, cv in STICK:
        out.append(
            f'<g transform="rotate(90 {f(cu)} {f(cv)})">\n'
            f'<text x="{f(cu + dx)}" y="{f(cv + dy)}" font-size="{f(STICK_SIZE)}" '
            f'fill="{WHITE}" font-weight="400">{letter}</text>\n</g>\n'
        )
    cv = (S3_TILE_V + v1) / 2
    out.append(
        f'<g transform="rotate(90 {f(cu)} {f(cv)})">\n'
        + run("S3", cu - 1.923, cv + 1.199, 3.301, 3.859, 700, WHITE)
        + "</g>\n"
    )
    out.append(fronts.LEGEND_CLOSE)
