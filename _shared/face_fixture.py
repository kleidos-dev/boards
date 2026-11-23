# SPDX-License-Identifier: MIT
"""A board of two boxes that prints on its front and its back, for the checks' own tests

No committed board prints on a face other than its front yet, and none is
built from two vendor files, so the paths that do both are held to a board of
their own: ``fixtures/faces/``, a 20 x 30 x 8 mm body with a 4 mm base
stacked under it, which this script writes in full (two binary STLs it draws
itself, a front and a back drawing with one legend group each, a
``measurements.json`` and a spec), and which ``build_board_glb.py`` builds
like any board:

- the body is the spec's own vendor file and the base a ``modules`` entry,
  moved under the body by its own ``transform``;
- the front prints ``AB`` and a bar on the body (``front.svg``, the plane
  ``name``);
- the back prints an ``F`` and ``K1`` on the base (``back.svg``, the face
  ``back``, the plane ``label``), drawn as the back's viewer sees it. The F
  has no mirror symmetry, so a print laid on the back the wrong way round is
  a print in another place, which the placement check must find.

The model and its ``source.json`` are committed beside the spec, so the
checks that read a model (``legend_placement.py``, ``model_raster.py``, the QA
suite) run on it with no builder; ``--check`` rebuilds it byte for byte where
the builder's libraries are installed. The STLs are ours (they are two boxes)
and are committed with it: the spec pins them by digest like a vendor's.

Needs the standard library only.

Usage::

    python -I _shared/face_fixture.py [--check]
"""

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "faces"
#: The body: x across, y up, z out of its front, mm (the build frame).
BODY = (0.0, 20.0, 0.0, 30.0, -8.0, 0.0)
#: The base, in its own file's frame; its module's transform moves it under the body.
BASE = (0.0, 20.0, 0.0, 30.0, 0.0, 4.0)
BASE_SHIFT = [0.0, 0.0, -12.0]
STL_HEADER = b"kleidos face_fixture.py: a box, binary STL".ljust(80, b" ")

FRONT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -2 24 34" width="24mm" \
height="34mm" font-family="Inter, Helvetica, Arial, sans-serif">
<title>face fixture: front (1 SVG unit = 1 mm)</title>
<rect x="0" y="0" width="20" height="30" fill="#5a5a5e"/>
<g class="legend" data-mark="front-name" data-plane="name">
<text x="10" y="9" font-size="4" font-weight="700" text-anchor="middle" fill="#ffffff">AB</text>
<rect x="4" y="12" width="12" height="1.2" fill="#ffffff"/>
</g>
<g id="annotations">
<text x="10" y="31.6" font-size="1.4" text-anchor="middle" fill="#666666">front</text>
</g>
</svg>
"""

BACK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -2 24 34" width="24mm" \
height="34mm" font-family="Inter, Helvetica, Arial, sans-serif">
<title>face fixture: back (1 SVG unit = 1 mm, as seen from behind)</title>
<rect x="0" y="0" width="20" height="30" fill="#2e8f8a"/>
<g class="legend" data-mark="back-flag" data-plane="label">
<polygon points="3,3 10,3 10,5 5,5 5,7 9,7 9,9 5,9 5,15 3,15" fill="#111113"/>
<text x="3" y="22" font-size="3" fill="#d2390c">K1</text>
</g>
<g id="annotations">
<text x="10" y="31.6" font-size="1.4" text-anchor="middle" fill="#666666">back</text>
</g>
</svg>
"""

MEASUREMENTS = {
    "device_id": "faces",
    "display_name": "Face fixture",
    "vendor": "Kleidos",
    "case": {
        "width": 20.0,
        "height": 30.0,
        "depth": 12.0,
        "corner_radius": 0.0,
        "color": "#5A5A5E",
        "material": "none",
    },
    "display": {
        "tech": "none",
        "active_w_mm": 10.0,
        "active_h_mm": 10.0,
        "resolution_w_px": 100,
        "resolution_h_px": 100,
        "origin_x_mm": 5.0,
        "origin_y_mm": 16.0,
    },
    "notes": "A test fixture written by _shared/face_fixture.py: two boxes, no device.",
}


def box_triangles(x0, x1, y0, y1, z0, z1):
    """The twelve triangles of a box, each wound counterclockwise seen from outside."""
    c = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    quads = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    out = []
    for a, b, d, e in quads:
        out += [(c[a], c[b], c[d]), (c[a], c[d], c[e])]
    return out


def stl(triangles):
    """A binary STL of *triangles*, each with its own unit normal."""
    out = bytearray(STL_HEADER + struct.pack("<I", len(triangles)))
    for a, b, c in triangles:
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        size = sum(k * k for k in n) ** 0.5
        out += struct.pack("<12fH", *[k / size for k in n], *a, *b, *c, 0)
    return bytes(out)


def source(name, data, note):
    return {
        "vendor": "Kleidos",
        "format": "stl",
        "file": name,
        "url": f"_shared/fixtures/faces/vendor/{name}",
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "license": "MIT",
        "copyright": "Kleidos",
        "license_note": note,
    }


def spec(body, base):
    """The fixture's spec: the body as its own source, the base as a module."""
    return {
        "schema": 1,
        "board": "faces",
        "node_name": "FaceFixture",
        "output": "_shared/fixtures/faces/model/faces.glb",
        "copyright": "Kleidos test fixture: two boxes and Inter glyph outlines (SIL Open "
        "Font License 1.1).",
        "notes": "Written by _shared/face_fixture.py. A body and a base stacked under it, a "
        "print on the front and one on the back, for the checks of the faces and "
        "modules paths.",
        "source": source("body.stl", body, "A box written by face_fixture.py."),
        "transform": [],
        "split": True,
        "parts": [{"name": "body", "match": {}}],
        "modules": [
            {
                "name": "base",
                "note": "Its own file draws it from z 0; the transform stands it under the body.",
                "source": source("base.stl", base, "A box written by face_fixture.py."),
                "transform": [{"translate": BASE_SHIFT}],
                "split": True,
                "parts": [{"name": "base", "match": {}}],
            }
        ],
        "center_mm": [10.0, 15.0, -6.0],
        "front_frame": {"left_x": 0.0, "top_y": 30.0},
        "measurements": "../measurements.json",
        "quant_mm": 0.01,
        "materials": [
            {"name": "case", "rgb": [90, 90, 94], "rough": 0.6},
            {"name": "base_plastic", "rgb": [46, 143, 138], "rough": 0.6},
        ],
        "meshes": [
            {"name": "case", "part": "body", "material": "case"},
            {"name": "base", "part": "base", "material": "base_plastic"},
            {
                "name": "name_legends",
                "legends": {
                    "front": "../svg/front.svg",
                    "plane": "name",
                    "on": "case",
                    "z": "0.0 + 0.03",
                },
            },
            {
                "name": "label_legends",
                "legends": {
                    "drawing": "../svg/back.svg",
                    "face": "back",
                    "plane": "label",
                    "on": "base",
                    "z": "-12.0 - 0.03",
                    "note": "three steps out of the base's bottom, towards its viewer",
                },
            },
        ],
    }


def files():
    """{path under the fixture: bytes} of everything this script writes."""
    body = stl(box_triangles(*BODY))
    base = stl(box_triangles(*BASE))
    return {
        "vendor/body.stl": body,
        "vendor/base.stl": base,
        "svg/front.svg": FRONT_SVG.encode(),
        "svg/back.svg": BACK_SVG.encode(),
        "measurements.json": (json.dumps(MEASUREMENTS, indent=2) + "\n").encode(),
        "model/spec.json": (json.dumps(spec(body, base), indent=2) + "\n").encode(),
    }


def main(argv=None):
    """Write the fixture, or with --check say whether the committed one is what it writes."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when a committed file is not what this script writes",
    )
    args = parser.parse_args(argv)
    stale = []
    for name, data in files().items():
        path = FIXTURE / name
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                stale.append(name)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"wrote {path.relative_to(HERE)}")
    if stale:
        print(f"stale: {stale}; run face_fixture.py, then rebuild the model", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
