# SPDX-License-Identifier: MIT
"""Build ``sticks3.glb``: the M5StickS3 case for the landing film, with a ``screen`` mesh

The landing film lays real captures on the glass of one modeled StickS3. This
writes that model, as a glTF 2.0 binary: the realistic master the film's web
model is cut from (the Kleidos repository's ``site/tools/build-web-model.mjs``, which reads it with no
decoder). The master itself is not published. The model is described by
``model/spec.json`` beside this file and written by the fleet's one builder,
``../_shared/build_board_glb.py``; this script keeps the command line the
StickS3 model was first built with.

Case geometry comes from M5Stack's own structure file (``m5stack/M5_Hardware``,
MIT License, Copyright (c) 2021 M5Stack),
``Products/K150_StickS3/Structures/StickS3.stl`` at commit ``48baa75a``; the
builder refuses any other file (the spec's ``source.sha256``), because the
model's ``asset.copyright`` names that one. The STL holds the assembled device
three times over (one assembly plus an exploded copy); only the assembly at
x = 0..24 mm is kept: front cap, back shell, BtnA pill. The STL is not ours to
redistribute and is not in the repository: its pinned address and digest go in
the model's manifest row, never in the model itself.

The STL is a shell only: no display, no connectors, an open back and an empty
inside. Everything else is added from ``measurements.json`` and the vendor
photos: the LCD slab, the ``screen`` quad over the 135 x 240 active area, a
``glass`` overlay, a dark interior filler behind every opening, the USB-C
receptacle, the HY2.0-4P (Grove) housing, the 2x8 HAT2 header, the two IR
parts, the back label plate and the four screws and inserts.

What the web model's cutter reads, and why the model is built to it:

- no ``images`` and no ``textures``: the glass is a capture the page loads,
  never a picture inside the model, and the web model has no place for one;
- ``extensionsRequired`` is ``KHR_mesh_quantization`` alone (the cutter keeps
  the quantized positions and normals as they are, and has no Draco or Meshopt
  decoder); ``KHR_materials_unlit`` is used for the screen, not required;
- no external resource in the JSON chunk (no ``uri``): the addresses in its
  embedded metadata (``asset``, the ``KHR_xmp_json_ld`` packet) are text.

The ``screen`` mesh is the glass contract: float positions, its node unscaled,
``extras.resolution`` ``[135, 240]``, and UVs in the glTF convention, (0, 0) at
the image's top-left as the user holds the stick (HAT2 end up, BtnA below), so
a capture uploaded with no vertical flip (``UNPACK_FLIP_Y_WEBGL`` off) reads
upright.

Frame (output, glTF): meters, +Y up the device (towards the HAT2 end, above
the screen), +Z out of the screen, +X to the device's right (the BtnB side).
Origin at the center of the 24 x 48 x 14 mm body (the pill stands 1 mm proud).

The output is byte-for-byte reproducible with the libraries it was first built
with (measured: these seven alone rebuild the same bytes), which are not in the
QA environment::

    pip install numpy==2.5.4 shapely==2.2.0 trimesh==5.2.0 mapbox_earcut==2.1.0 \\
        scipy==1.18.1 networkx==3.7 rtree==1.4.1

Usage::

    python -I sticks3/build_sticks3_glb.py \\
        <StickS3.stl> sticks3/model/sticks3.glb

The same model, checked against the committed file without writing it::

    python -I _shared/build_board_glb.py \\
        sticks3/model/spec.json --source <StickS3.stl> --check
"""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / '_shared'))

import build_board_glb  # noqa: E402  (the path above makes it importable)

SPEC = HERE / 'model' / 'spec.json'


def main(argv=None):
    """Build the model from the command line; return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("stl", type=Path, help="M5Stack's StickS3.stl at 48baa75a")
    parser.add_argument("out", type=Path, help="the .glb to write")
    args = parser.parse_args(argv)
    return build_board_glb.main([str(SPEC), '--source', str(args.stl), '--out', str(args.out)])


if __name__ == '__main__':
    sys.exit(main())
