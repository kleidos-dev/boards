# SPDX-License-Identifier: MIT
"""What a board model reads from its drawings, and the digest of it

A board's printed legends are the ``<g class="legend">`` groups of its
``svg/front.svg`` and of the drawings of its other faces (``svg/back.svg``)
(``emit_front_svg.py`` and ``emit_back_svg.py`` write them, ``legend_mesh.py``
turns them into the model's ``*_legends_*`` meshes). The rest of the drawing (the
case, the caps, the demo screen, the hotspots, the callouts) is nothing to the
model: a front regenerated with a new callout builds the same legends, and a
model is stale only when what it reads has changed.

What it reads, and nothing else, is found here once, for the builder
(``legend_mesh.read_legends`` walks the drawing with ``groups``) and for the
checks that hold a model to its drawing (``digest``):

- every legend group, in the drawing's order, which is the paint order: its
  own attributes and, inside it, every element with its attributes, the
  characters of a ``<text>``, and the order of them all;
- what places a group: the ``transform`` of each ``<g>`` it lies in, from the
  outermost in, and the ``font-family`` it inherits, from the nearest element
  around it that names one.

``build_board_glb.py`` writes the digest of each plane into the model's
``source.json`` (``legends_sha256``), beside the digests of the spec and of the
fonts, and ``legend_placement.py`` and
``tests/test_board_model_legends.py`` fail a model whose drawing gives
another. The digest is taken over the attributes as they are written, not over
the numbers they spell, so ``0.50`` for ``0.5`` inside a group counts as a
change: the generator writes one spelling, and a false alarm there costs a
rebuild, where a missed change would leave a model that is not its drawing.

Needs the standard library only, so the QA environment runs it.

Usage::

    python -I _shared/legend_source.py FRONT.svg [--plane NAME]
"""

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = '{http://www.w3.org/2000/svg}'
#: The plane of a key's group that names none.
KEYS_PLANE = 'keys'


def is_legend(el):
    """True for a ``<g>`` whose class list holds ``legend``."""
    return el.tag == SVG + 'g' and 'legend' in (el.get('class') or '').split()


def groups(root):
    """[(a legend group, the elements it lies in, outermost first)] in the drawing's order.

    A legend group is not looked into for more: one inside another is the
    reader's to refuse.
    """
    out = []

    def walk(el, around):
        if is_legend(el):
            out.append((el, around))
            return
        inside = (*around, el)
        for child in el:
            walk(child, inside)

    walk(root, ())
    return out


def plane_of(group):
    """The plane a legend group is printed on, as it names it or as a key's defaults."""
    return group.get('data-plane', KEYS_PLANE)


def placed(around):
    """(the transforms of the ``<g>`` elements around a group, outermost first; the
    ``font-family`` the group inherits, or None)."""
    transforms = [el.get('transform') for el in around
                  if el.tag == SVG + 'g' and el.get('transform') is not None]
    family = None
    for el in around:
        family = el.get('font-family', family)
    return transforms, family


def _described(el):
    """One element of a legend as the reader reads it: tag, attributes, characters, children."""
    tag = el.tag.removeprefix(SVG)
    out = {'tag': tag, 'attributes': dict(el.attrib),
           'children': [_described(child) for child in el]}
    if tag == 'text':
        out['characters'] = el.text or ''
    return out


def described(front_svg, plane=None):
    """What a model reads from a front drawing: its legend groups and what places each.

    A list in the drawing's order of ``{'placed': [transform, ...], 'family':
    name or None, 'group': {tag, attributes, children}}``; with *plane*, only
    the groups printed on it.
    """
    out = []
    for group, around in groups(ET.parse(front_svg).getroot()):
        if plane is not None and plane_of(group) != plane:
            continue
        transforms, family = placed(around)
        out.append({'placed': transforms, 'family': family, 'group': _described(group)})
    return out


def digest(front_svg, plane=None):
    """The SHA-256 of what a model reads from a front drawing (of one *plane*, or of all)."""
    text = json.dumps(described(front_svg, plane), sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True)
    return hashlib.sha256(text.encode('ascii')).hexdigest()


def main(argv=None):
    """Print a drawing's legend digest from the command line; return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    parser.add_argument('front', type=Path, help='<board>/svg/front.svg')
    parser.add_argument('--plane', help='only the groups printed on this plane')
    args = parser.parse_args(argv)
    found = described(args.front, args.plane)
    print(f'{digest(args.front, args.plane)}  {len(found)} legend group(s)'
          + (f' on the plane {args.plane!r}' if args.plane else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
