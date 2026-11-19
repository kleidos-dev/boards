#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate the committed ``svg/back.svg`` of every board that has a model

A board prints on its back too (a sticker of pin names and marks, a rating
label, a wordmark in the shell), and its model carries those prints as
geometry the way it carries the front's (``build_board_glb.py``, a
``legends`` mesh with ``face: back``). Each face's prints are drawn once, in
that face's drawing; this script is the only writer of the backs, as
``emit_front_svg.py`` is of the fronts.

Back frame
----------
1 SVG unit = 1 mm, seen from behind with the board's top up
(``board_faces.py``): x across from the case's left edge *as seen from
behind*, which is its right edge as the front is seen, and y down from its
top edge. A print is drawn as its viewer reads it; the builder lays it on the
model mirrored, so nothing here is drawn mirrored.

Back contract
-------------
Smaller than a front's (``schema.md``, "Back drawings"):

* the case outline, the first shape of the drawing: the front's outline
  mirrored across the case, which is what the case shows from behind (a
  silhouette seen along one axis is the same from either end);
* the legend groups, ``<g class="legend" data-mark="<name>"
  data-plane="<plane>">``, the same groups and the same rules as the front's
  (flat ink, no group in a group); a back has no keys, so no ``data-key``;
* ``<g id="annotations">``, last: the two mm dimensions and the title, in the
  margins.

No ``screen-active`` or ``screen-demo``: a back has no screen. A back with a
control on it (the CoreInk's reset key, the only one) also carries the
front's ``<g id="hotspots" display="none">``, just before the annotations,
with one target a control (``data-face="back"``, in the back frame), from
``BACK_HOTSPOTS``, and the control's name among the annotations
(``BACK_CALLOUTS``); every other back has neither. What a back prints is
added to ``BACK_PRINTS`` as a function that appends its legend groups (and,
before them, what else the face shows that is no print: a label's paper, the
CoreInk's reset key); a board with none there draws its outline alone, the
frame its prints will be drawn in.

Usage: ``emit_back_svg.py`` regenerates every back; ``emit_back_svg.py
<device_id> ...`` only the named ones.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_front_svg as fronts  # noqa: E402  (beside this file; -I leaves it off the path)
import media_meta  # noqa: E402
import back_plus_se  # noqa: E402
import cardputer_faces  # noqa: E402
import coreink_back  # noqa: E402
import core2_prints  # noqa: E402
import sticks3_back  # noqa: E402
import cores3_prints  # noqa: E402
import back_tdeck_plus  # noqa: E402
import back_m5stickc_plus1  # noqa: E402
import back_plus2  # noqa: E402

ROOT = fronts.ROOT
#: The boards that have a model, and so a back drawing.
BOARDS = ('sticks3', 'm5stickc-plus1', 'm5stickc-plus2', 'm5stickc-plus-se', 'coreink',
          'cores3-se', 'm5stack-core2-v13', 'cardputer', 'tdeck-plus')
#: What each back prints: a function that appends its legend groups, in the
#: back frame (``fronts.print_open`` ... ``fronts.LEGEND_CLOSE``).
BACK_PRINTS: Dict[str, Callable[[List[str]], None]] = {
    'cardputer': cardputer_faces.back,
    'coreink': coreink_back.append_coreink_back,
    'm5stack-core2-v13': core2_prints.append_back,
    'm5stickc-plus-se': back_plus_se.append_back,
    'sticks3': sticks3_back.append_back,
    'tdeck-plus': back_tdeck_plus.append_tdeck_plus_back,
    'm5stickc-plus1': back_m5stickc_plus1.append_m5stickc_plus1_back,
    'm5stickc-plus2': back_plus2.append_plus2_back,
}
#: The controls on a back, as {board: a function that returns its targets, in
#: the back frame}: only the CoreInk has one, its reset key.
BACK_HOTSPOTS: Dict[str, Callable[[], List[fronts.Hotspot]]] = {
    'coreink': coreink_back.back_hotspots,
}
#: The names of those controls, as {board: a function that returns the margin
#: callouts the annotations carry beside the dimensions}.
BACK_CALLOUTS: Dict[str, Callable[[], List[str]]] = {
    'coreink': coreink_back.back_callouts,
}
#: What a board prints on another face than its back, as {(board, face): a
#: function that appends its legend groups in that face's frame}; each is
#: written to ``svg/<face>.svg`` (``build_face``).
FACE_PRINTS: Dict[Tuple[str, str], Callable[[List[str]], None]] = {
    ('cardputer', 'left'): cardputer_faces.left,
    ('cardputer', 'top'): cardputer_faces.top,
    ('coreink', 'left'): coreink_back.append_coreink_left,
    ('m5stack-core2-v13', 'top'): core2_prints.append_top,
    ('sticks3', 'left'): sticks3_back.append_left,
    ('cores3-se', 'top'): cores3_prints.append_top,
}
#: A side face whose outline is not the case's own, as {(board, face): (across,
#: along) in mm}: the CoreS3 SE stands on its battery base, so its top side
#: runs 23.5 mm from the base's floor to the front, not the case's 15.
FACE_EXTENT: Dict[Tuple[str, str], Tuple[float, float]] = {
    ('cores3-se', 'top'): (54.0, 23.5),
}
_NUMBER = r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?'
_PATH_TOKEN = re.compile(rf'[A-Za-z]|{_NUMBER}')
#: How many numbers each path command takes, and which of them are x (0) or
#: y (1) coordinates, an arc's radii and angle (r), or its flags (f).
_PATH_ARGS = {'M': 'xy', 'L': 'xy', 'T': 'xy', 'H': 'x', 'V': 'y', 'C': 'xyxyxy',
              'S': 'xyxy', 'Q': 'xyxy', 'A': 'rrafsxy', 'Z': ''}


def mirror_path(d: str, width: float) -> str:
    """A path's data mirrored across x = width / 2: what its shape is seen from behind.

    An absolute x becomes ``width - x`` and a relative one changes sign; an
    arc's sweep flag flips and its rotation changes sign. Every ring is wound
    the other way, all alike, so the fill a rule gives is the mirror's.
    """
    tokens = _PATH_TOKEN.findall(d)
    if ''.join(tokens) != re.sub(r'[\s,]+', '', d):
        raise ValueError(f'a path this mirror does not read: {d!r}')
    out: List[str] = []
    i, cmd = 0, None
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            out.append(cmd)
            if cmd.upper() == 'Z':
                continue
        elif cmd is None or cmd.upper() == 'Z':
            raise ValueError(f'a number with no command in {d!r}')
        args = _PATH_ARGS[cmd.upper()]
        values = [float(t) for t in tokens[i:i + len(args)]]
        if len(values) != len(args):
            raise ValueError(f'{cmd} short of numbers in {d!r}')
        i += len(args)
        absolute = cmd.isupper()
        for kind, value in zip(args, values):
            if kind == 'x':
                value = width - value if absolute else -value
            elif kind == 'a':
                value = -value if value else 0.0
            elif kind == 's':
                value = 1.0 - value
            out.append(fronts.f(value))
        if cmd in 'Mm':
            cmd = 'L' if cmd == 'M' else 'l'
    return ' '.join(out)


def mirror_points(points: str, width: float) -> str:
    """A polygon's points mirrored across x = width / 2."""
    v = [float(t) for t in re.findall(_NUMBER, points)]
    return ' '.join(f'{fronts.f(width - x)},{fronts.f(y)}' for x, y in zip(v[0::2], v[1::2]))


def front_outline(svg: str) -> str:
    """The case outline of a front: its first shape outside ``<defs>``."""
    body = re.sub(r'<defs>.*?</defs>', '', svg, flags=re.S)
    found = re.search(r'<(rect|path|polygon)\b[^>]*>', body)
    if not found:
        raise ValueError('the front has no case outline')
    return found.group(0)


def back_outline(outline: str, width: float, fill: str) -> str:
    """The front's case outline as the back shows it, filled with the case's color.

    Its stroke is the front's; its fill is flat (the front's gradient and
    shadow belong to the front's light).
    """
    tag = re.match(r'<(\w+)', outline).group(1)
    attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', outline))
    stroke = (f' stroke="{attrs["stroke"]}" stroke-width="{attrs["stroke-width"]}"'
              if 'stroke' in attrs and 'stroke-width' in attrs else '')
    if tag == 'rect':
        x, w = float(attrs.get('x', 0)), float(attrs['width'])
        corner = ''.join(f' {k}="{attrs[k]}"' for k in ('rx', 'ry') if k in attrs)
        return (f'<rect id="case-outline" x="{fronts.f(width - x - w)}" y="{attrs.get("y", "0")}" '
                f'width="{attrs["width"]}" height="{attrs["height"]}"{corner} '
                f'fill="{fill}"{stroke}/>\n')
    if tag == 'polygon':
        return (f'<polygon id="case-outline" points="{mirror_points(attrs["points"], width)}" '
                f'fill="{fill}"{stroke}/>\n')
    rule = f' fill-rule="{attrs["fill-rule"]}"' if 'fill-rule' in attrs else ''
    return (f'<path id="case-outline" d="{mirror_path(attrs["d"], width)}" fill="{fill}"'
            f'{rule}{stroke}/>\n')


def device(device_id: str) -> fronts.DeviceSpec:
    for spec in fronts.DEVICES:
        if spec.device_id == device_id:
            return spec
    raise KeyError(device_id)


def build_back(device_id: str) -> str:
    """One board's back drawing, from its front's outline and its ``BACK_PRINTS``."""
    spec = device(device_id)
    front = spec.builder(spec.device_id, spec.name, spec.body_w, spec.body_h,
                         **spec.builder_kwargs)
    case = json.loads((ROOT / device_id / 'measurements.json').read_text(encoding='utf-8'))
    fill = str(case['case']['color']).lower()
    vb_w = spec.body_w + fronts.MARGIN_LEFT_MM + fronts.MARGIN_RIGHT_MM
    vb_h = spec.body_h + fronts.MARGIN_TOP_MM + fronts.MARGIN_BOTTOM_MM
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{-fronts.MARGIN_LEFT_MM} {-fronts.MARGIN_TOP_MM} {fronts.f(vb_w)} '
        f'{fronts.f(vb_h)}" width="{fronts.f(vb_w)}mm" height="{fronts.f(vb_h)}mm" '
        'shape-rendering="geometricPrecision" '
        'font-family="Inter, Helvetica, Arial, sans-serif">\n',
        f'<title>{spec.name}: back mockup, seen from behind (1 SVG unit = 1 mm)</title>\n',
        back_outline(front_outline(front), spec.body_w, fill),
    ]
    prints = BACK_PRINTS.get(device_id)
    if prints is not None:
        prints(out)
    spots = BACK_HOTSPOTS.get(device_id)
    if spots is not None:
        out.append(fronts.hotspots_block(spots()))
    callouts = BACK_CALLOUTS.get(device_id)
    out.append(fronts.caption_block(f'{spec.name} (back)', spec.body_w, spec.body_h,
                                    callouts() if callouts is not None else None))
    out.append(fronts.SVG_CLOSE)
    return ''.join(out)


#: How wide and how tall each side face's drawing is: (the case's width,
#: height or depth along its ``u``, along its up), ``board_faces.FACES``.
_FACE_SIZE = {'top': ('width', 'depth'), 'bottom': ('width', 'depth'),
              'left': ('depth', 'height'), 'right': ('depth', 'height')}


def build_face(device_id: str, face: str) -> str:
    """One board's drawing of a side face, in that face's frame (``board_faces.py``).

    Its contract is the back's: the case outline first (the face's
    rectangle, the case's width, height or depth across it, or its
    ``FACE_EXTENT``, filled with the case's color), the legend groups of
    ``FACE_PRINTS``, the annotations last.
    """
    spec = device(device_id)
    case = json.loads((ROOT / device_id / 'measurements.json').read_text(encoding='utf-8'))
    across, along = FACE_EXTENT.get((device_id, face),
                                    tuple(float(case['case'][k]) for k in _FACE_SIZE[face]))
    fill = str(case['case']['color']).lower()
    vb_w = across + fronts.MARGIN_LEFT_MM + fronts.MARGIN_RIGHT_MM
    vb_h = along + fronts.MARGIN_TOP_MM + fronts.MARGIN_BOTTOM_MM
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{-fronts.MARGIN_LEFT_MM} {-fronts.MARGIN_TOP_MM} {fronts.f(vb_w)} '
        f'{fronts.f(vb_h)}" width="{fronts.f(vb_w)}mm" height="{fronts.f(vb_h)}mm" '
        'shape-rendering="geometricPrecision" '
        'font-family="Inter, Helvetica, Arial, sans-serif">\n',
        f'<title>{spec.name}: {face} side mockup (1 SVG unit = 1 mm)</title>\n',
        f'<rect id="case-outline" x="0" y="0" width="{fronts.f(across)}" '
        f'height="{fronts.f(along)}" fill="{fill}" stroke="#a8a8ac" stroke-width="0.2"/>\n',
    ]
    FACE_PRINTS[(device_id, face)](out)
    out.append(fronts.caption_block(f'{spec.name} ({face})', across, along))
    out.append(fronts.SVG_CLOSE)
    return ''.join(out)


def stamped(path: Path, svg: str) -> str:
    """*svg* with the metadata of the file it is written to (``media_meta.stamp_svg``)."""
    return media_meta.stamp_svg(svg, media_meta.record(path.relative_to(ROOT).as_posix()))


def main(argv: List[str]) -> int:
    unknown = [d for d in argv if d not in BOARDS]
    if unknown:
        print(f"unknown device id(s): {', '.join(unknown)}; known: {', '.join(BOARDS)}",
              file=sys.stderr)
        return 2
    for device_id in BOARDS:
        if argv and device_id not in argv:
            continue
        path = ROOT / device_id / 'svg' / 'back.svg'
        path.write_text(stamped(path, build_back(device_id)), encoding='utf-8')
        for board, face in FACE_PRINTS:
            if board == device_id:
                path = ROOT / board / 'svg' / f'{face}.svg'
                path.write_text(stamped(path, build_face(board, face)), encoding='utf-8')
        print(f'ok  {device_id}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
