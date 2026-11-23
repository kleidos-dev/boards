# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Build one board's ``.glb`` from its vendor CAD file and its ``model/spec.json``

The site lays real captures on the glass of a modeled board. Every board's model
is written by this one builder, driven by a per-board spec
(``<board>/model/spec.json``), as a glTF 2.0 binary
that needs no decoder. ``sticks3/model/spec.json`` rebuilds
``sticks3/model/sticks3.glb`` byte for byte (``--check``), which is the
builder's regression test: the realistic master, not published, that the
landing film's web model is cut from (the Kleidos repository's ``site/tools/build-web-model.mjs``).

The vendor file (an STL or a STEP) is not ours to redistribute and is never in
the repository: the spec pins its address and its SHA-256, the builder refuses
any other bytes, and ``--fetch`` downloads it into a cache outside the tree.
A board built with a module stacked on it (a battery base under a core) names
a second vendor file the same way, under ``modules``.

What the spec says, in the order the builder uses it (all lengths in mm):

``source``
    ``format`` (``stl`` or ``step``), ``url``, ``sha256``, ``file`` (the cache
    name), ``repository``, ``path``, ``commit``, ``license``, ``copyright``,
    ``license_note``. A STEP is tessellated by cascadio with ``tessellation``
    (``tol_linear``, ``tol_angular``), then scaled from meters to mm. A model
    built from no vendor file at all, every part of it a shape of the spec,
    says so with ``format`` ``none`` and only ``license``, ``copyright`` and
    ``license_note``: it has no ``transform``, ``split``, ``select`` or
    ``parts``, no ``center_mm`` of ``auto`` and nothing to fetch, and its
    ``source.json`` records the same three keys.
``transform``
    Operations that take the vendor geometry into the build frame, applied in
    order: ``{"rotate": {"axis": "x", "deg": 90}}``, ``{"translate": [x, y, z]}``,
    ``{"scale": s}``. The build frame is the model's frame before centering: +Y
    up the screen, +Z out of the screen, +X to the device's right.
``split``, ``select``, ``parts``
    The vendor geometry is cut into components (an STL's connected pieces, a
    STEP's named parts; ``split`` also cuts a STEP part into pieces;
    ``clean``, the default for a STEP, drops zero-area and repeated faces). A
    component outside ``select`` is dropped; each other one goes to the first
    ``parts`` rule it matches, and a rule's components are joined in order.
    Match keys (``null`` skips an axis): ``name`` (regex on a STEP part's
    names), ``min_ge`` / ``min_le`` / ``max_ge`` / ``max_le`` (the bounds),
    ``extent_gt`` / ``extent_lt``, ``faces_gt`` / ``faces_lt``. A rule may carry
    ``ops``, applied in order: ``{"slice": {"normal", "origin", "cap"}}`` (keeps
    the side the normal points to), ``{"decimate": {"face_count": n}}`` and
    ``{"cull": {"volumes", "margin", "same_box"}}`` (the cull below, on this part
    alone and at that point, so a part can lose its hidden faces before it is
    decimated).
``modules``
    Further vendor files the model is built from, each one an object with a
    ``name`` of its own and the keys above, which say what they say for the
    spec's own file: ``source``, ``tessellation``, ``transform``, ``split``,
    ``clean``, ``select`` and ``parts``. A module's transform takes its file
    into the same build frame (a battery base under a core: its top against
    the core's back). Its parts join the spec's: a mesh, a volume's ``cull``
    or ``center_from`` names them as it names the spec's own, so no part name
    is used twice. Each file is pinned by its digest, fetched into the cache
    by ``--fetch`` (or given with ``--module-source NAME=FILE``), and recorded
    in ``source.json`` under ``modules``.
``volumes``, ``cull``
    Named lists of boxes ``[x0, x1, y0, y1, z0, z1]`` in the build frame, or
    ``{"frame": "front", "boxes": [...]}`` for boxes whose x and y are written in
    the front frame of ``measurements.json`` (which then needs a numeric
    ``front_frame``). ``cull`` drops faces of the named ``parts`` that the named
    ``volumes`` hide: the inside of a shell behind an opaque filler. A face goes
    when each of its three corners sits inside a box of those volumes, not
    necessarily the same box, so two boxes that meet across a visible wall also
    take that wall; ``"same_box": true`` drops a face only when one box holds
    all three corners.
``center_mm``, ``front_frame``, ``face_frames``
    The model's origin in the build frame (``"auto"``: the center of the
    ``center_from`` parts' bounds), and where the front frame of
    ``measurements.json`` (x across from the case's left edge, y down from its
    top edge) sits in the build frame: ``left_x``, ``top_y`` (or ``"auto"``).
    ``face_frames`` places the drawing of another face of the board
    (``board_faces.py``: ``top``, ``bottom``, ``left``, ``right``, each under
    its own two keys, ``"top": {"left_x": 0, "back_z": -12.3}``). The back
    needs none unless it is given: its drawing is the front's mirrored, its
    ``right_x`` the front's ``left_x`` plus ``case.width`` and its ``top_y``
    the front's.
``measurements``
    The board's ``measurements.json``, relative to the spec. The ``screen``
    quad covers its display's active area.
``materials``
    In order: ``name``, ``rgb`` (sRGB 0-255) or ``hex``, ``rough``, ``metal``,
    ``alpha``, ``unlit``, ``double``. A material with ``alpha`` (above 0 and
    below 1) is core glTF ``alphaMode: BLEND`` with that ``baseColorFactor``
    alpha: no transmission or volume extension and no texture, so any glTF
    reader draws it, blended over what is behind it after everything opaque
    (three.js's ``GLTFLoader`` also turns its depth writes off).
``meshes``
    In order, each with a ``name`` and a ``material``, and one of: ``part``
    (a ``parts`` rule), ``shapes`` (joined), ``screen`` (``z``), ``glass``
    (``rect`` [x0, x1, y0, y1], ``z``), or, with no ``material``, ``legends``
    (below). ``smooth_deg`` shades smooth across
    edges up to that angle (flat otherwise); ``quantize: false`` keeps float
    positions. A ``part`` mesh may take only some of the part: ``inside``
    (a volume's name) keeps the faces one of that volume's boxes holds whole,
    ``outside`` the rest, so two meshes of one part, one ``inside`` and one
    ``outside`` the same volume, hold every face of it once (a shell whose
    front wall is blended and whose walls are not). No face is cut: a box
    drawn just past the edges the split should follow splits there. The part
    is shaded whole before it is split, so where the two meshes meet they
    carry the normals the part has there, and a fillet that runs on past the
    split stays smooth across it. A shape
    is ``{"box": [...]}``, ``{"volume": name}``,
    ``{"prism": {"axis", "range", "profile"}}`` (or ``"volume"`` for a one-box
    volume with ``profile: {"rounded": r}``) with a profile ``{"rect": [u0, u1,
    v0, v1]}``, ``{"rounded_rect": [u0, u1, v0, v1], "r", "res"}``,
    ``{"stadium": [cu, cv, w, h], "res", "inner": [w, h]}`` (w at least h; w
    equal to h is a disc) or ``{"polygon": [[u, v], ...], "holes": [[[u, v],
    ...], ...]}`` drawn in the two other axes in (x, y), (x, z) or (y, z) order
    (a prism's ``faces``, a list of ``top``, ``bottom``, ``outer`` and
    ``inner``, keeps only those: the caps facing +axis and -axis, the sides
    along the outline and those along the holes, for a lining inside a solid
    shell whose other faces no view reaches),
    ``{"cylinder": {"axis", "c": [u, v], "r", "range", "sections"}}``,
    ``{"loft": {"axis", "sections": [{"at", "polygon": [[u, v], ...]}, ...],
    "caps"}}`` (the side surface through two or more sections of one count
    of points, each point joined to the point of the same index in the next
    section: a chamfer, a slope or a taper no prism draws; ``caps`` lists
    ``first`` and ``last``, the flat ends at the first and the last section,
    none unless named),
    ``{"sphere": {"c": [x, y, z], "r", "subdivisions", "z_min"}}`` (an
    icosphere, cut below ``z_min`` when given), or ``{"quad_grid": {"axis": "y"
    or "z", "at", "facing", "u_center", "v_center", "cols", "rows", "pitch",
    "size"}}`` (a grid of flat squares, for header holes). A shape with
    ``"frame": "front"`` is written in the front frame of ``measurements.json``
    instead: x across, y down from the top, z unchanged. ``frame`` belongs to
    the shape, beside ``prism`` or ``box``, never inside them.

A ``legends`` mesh is what one of the board's drawings prints on one plane, as
geometry (``legend_mesh.py``): a surface, or that part of a surface's print
that a reader keeps or leaves out as one (the T-Deck Plus's plate is two
planes, because the discs of its two round marks are printed in the ink of
its hairline traces: on one plane the two were one mesh, with one
``stroke_mm``). Its ``name`` ends in ``legends``
(``key_legends``, ``panel_legends``), and it takes ``front`` (the
``front.svg``, relative to the spec, whose ``<g class="legend">`` groups are
read; the spec types no legend) or, for any face, ``drawing`` and ``face``
(``svg/back.svg`` and ``back``: the drawing of that face, in that face's frame,
``board_faces.py``; a drawing draws one face), ``plane`` (which of the
drawing's planes it draws: the groups' ``data-plane``, ``keys`` unless given),
``on`` (the mesh the legends are printed on), its height along the face's
normal, ``z`` on the front and the back, ``y`` on the top and the bottom and
``x`` on the sides (a whole number of position steps out from the face under
them: three on every board, but for the T-Deck Plus's round marks, which keep
the height of the plate's print around them, eight steps over the plate; on
the back three steps under the lowest face over them, which is the same three
steps out of the case), ``flatness`` (the most a flattened
curve strays from the drawn one,
0.004 mm unless given) and ``rough``. It writes one mesh for each ink color
of the plane, in the order of the colors, named ``<name>_<rrggbb>``, flat and
facing +Z, of one primitive (the web model's cutter reads a mesh's first
primitive and no other), with a material ``ink_<rrggbb>`` made from that
color and ``extras.legends``: ``fill`` (the ink), ``stroke_mm`` (how thin the
print is: twice the sheet's area over its outline's length) and ``on``. Its
sheets face out of their face (+Z on the front, -Z on the back), each wound
counterclockwise as that face's viewer sees it.

What a reader may count on, for any board:

- ``_legends_<rrggbb>`` at the end of a node's name finds every legend mesh
  and nothing else (the builder refuses any other mesh named so), and a
  material named ``ink_<rrggbb>`` belongs to legends alone.
- The model without those meshes is the model as it was built without them:
  ``glb_legends.py strip`` writes it from the file alone, and ``--check
  --without-legends`` builds it again from the vendor file and holds the two
  to the same bytes.
- A legend moves with the mesh it is printed ``on``: a reader that presses a
  key moves that key's part of the legend sheets with it, or leaves both.
- A print is worth drawing only where its strokes cover about a pixel. Leave
  a legend mesh out when ``stroke_mm`` times the pixels a millimeter is under
  1 with 4x multisampling, or under 1.5 with no antialiasing; decide it once
  for a shot, never frame by frame, so nothing pops.

What the builder refuses, so no print goes missing and none shimmers: a plane
of the drawing no ``legends`` mesh draws; a legend with no face of its ``on``
mesh under it; a face of another opaque mesh less than two quantization steps
under a legend, where a depth test may draw the two at one depth, or any such
face over one (``model_raster.legend_clearance``, on the written model read
back); and, of any two meshes, legends or not, faces of different materials
that face the same way and overlap less than one position step apart, which a
depth test keeps by rounding, differently in each renderer
(``model_raster.coplanar_overlaps``: a print is cut out of the print under it,
a solid starts where the one under it ends, a layer lies whole steps over the
other). The glyphs are outlines of Inter (``fonts/inter/``, SIL Open
Font License 1.1), which the model's ``copyright`` names.

What ties a model to its drawing: each legends mesh's entry in ``source.json``
records ``legends_sha256``, the digest of what the mesh read from its drawing
(``legend_source.py``: its plane's legend groups, element by
element, and what places them, the transforms of the groups around them and
the font family they inherit), beside the digests of the spec and of the font
files. A drawing that gives another digest is a model to rebuild; a drawing
changed anywhere else (a callout, a hotspot, the demo screen, a cap) is not.

A model holds at most 45 materials, the legends' inks counted: what the
strictest reader has room for. The landing film's renderer keeps a table of 48
and puts three of its own after the model's (the finger, the nail and the cover
glass).

Any number in the spec may be a string holding arithmetic (``"47.98 + 0.010"``),
evaluated in the order written, so a derived coordinate keeps the exact value
the expression gives. Every object takes a ``note``; any other key the builder
does not read is refused, so a misplaced one fails the build instead of being
ignored.

What the web model's cutter reads, and why every model is built to it, so any
board's model can be cut the way the StickS3's is: no ``images`` and no
``textures`` (the glass is a capture the page loads, never a picture inside the
model, and the web model has no place for one); ``extensionsRequired`` is
``KHR_mesh_quantization`` alone (the cutter keeps the quantized positions and
normals as they are, and has no Draco or Meshopt decoder);
``KHR_materials_unlit`` is used for the screen, not required; no URL anywhere
in the JSON chunk.

The ``screen`` mesh is the glass contract: float positions, its node unscaled,
``extras.resolution`` the panel's pixels in the front view's orientation, and
UVs in the glTF convention, (0, 0) at the image's top-left as the user holds
the board, so a capture uploaded with no vertical flip
(``UNPACK_FLIP_Y_WEBGL`` off) reads upright. Every face under the screen, and
every face over it (the glass), sits at least one quantization step
(``quant_mm``) off its plane once the model is quantized, so a depth test never
draws the two at one depth: the builder reads the written model back and
refuses it otherwise (``model_raster.screen_clearance``).

A board's master (a spec whose ``output`` is ``<board>/model/<board>.glb``)
is also written as Wavefront OBJ and MTL beside it, in millimeters, by
``export_obj.py`` from the GLB just written and from nothing else, and
``source.json`` records the two files under ``obj``; the GLB's bytes do not
change for it. The checks' fixture gets no OBJ.

The output is byte-for-byte reproducible with these libraries (cascadio only
for a STEP, fast-simplification only for ``decimate``, fonttools only for
``legends``), which are not in the QA environment::

    pip install numpy==2.5.5 shapely==2.2.0 trimesh==5.2.2 mapbox_earcut==2.1.0 \\
        scipy==1.18.1 networkx==3.7 rtree==1.4.1 cascadio==0.1.1 \\
        fast-simplification==0.2.0 fonttools==4.68.0

Usage::

    python -I _shared/build_board_glb.py \\
        <board>/model/spec.json [--source FILE] \\
        [--module-source NAME=FILE ...] [--cache DIR] [--fetch] [--out GLB] [--check] \\
        [--no-source-json] [--without-legends]

``--without-legends`` builds the model with no ``legends`` mesh, for a reader
that shows the board too small to print on: with ``--out`` it writes that
lighter model, and with ``--check`` it compares it, byte for byte, with the
spec's output less its legend meshes (``glb_legends.strip``).
"""

import argparse
import ast
import gzip
import hashlib
import importlib.metadata
import json
import operator
import os
import platform
import re
import shutil
import struct
import sys
import tempfile
import urllib.request
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import numpy as np
import numpy.typing as npt
import shapely
import shapely.geometry as sg
import trimesh
from shapely.geometry.base import BaseGeometry

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board_faces
import export_obj
import glb_legends
import legend_source
import media_meta
import model_raster

# trimesh ships these without annotations: the signatures this builder calls
# them with, so every call is checked like the rest (mypy's strict mode).
_rotation_matrix = cast(
    "Callable[[float, Sequence[float]], npt.NDArray[np.float64]]",
    trimesh.transformations.rotation_matrix,
)
_triangle_normals = cast(
    "Callable[[npt.NDArray[np.float64]], tuple[npt.NDArray[np.float64], npt.NDArray[np.bool_]]]",
    trimesh.triangles.normals,
)
_slice_mesh_plane = cast(
    "Callable[..., trimesh.Trimesh]",
    trimesh.intersections.slice_mesh_plane,
)


def _one_mesh(geometry: object, what: str) -> trimesh.Trimesh:
    """*geometry* as one mesh: what trimesh's loaders and concatenate give here."""
    if not isinstance(geometry, trimesh.Trimesh):
        raise SpecError(f"{what}: not one triangle mesh ({type(geometry).__name__})")
    return geometry


#: Bumped when the same spec and source would build different bytes, or when
#: the spec format gains a key (1.1.0: polygon and disc profiles, spheres,
#: front-frame volumes, the cull part op, strict keys; 1.2.0: a part mesh's
#: ``inside`` and ``outside``, a prism's ``faces``, and ``alpha`` held between
#: 0 and 1; 1.3.0: the ``legends`` mesh; 1.4.0: a ``legends`` mesh's ``plane``
#: and ``on``, its name ending in ``legends``, ``stroke_mm`` and ``on`` in its
#: ``extras``, a limit of materials, and ``--without-legends``; 1.4.1: that
#: limit is the strictest reader's, 29, where 1.4.0 let 31 through, and a
#: legends mesh's record holds the digest of what it reads from the drawing,
#: ``legends_sha256``, where 1.4.0 wrote the whole file's; 1.5.0: a legends
#: mesh's ``drawing``, ``face`` and a height along that face's normal, the
#: spec's ``face_frames`` and ``modules``, and ``--module-source``; 1.6.0: a
#: model of no vendor file, ``source`` ``format`` ``none``, and the ``loft``
#: shape; 1.7.0: the model's embedded metadata, ``asset`` with ``extras`` and the
#: ``KHR_xmp_json_ld`` packet, from ``media_meta.record``, the spec's
#: ``generator`` gone and its ``copyright`` the credits only). A refusal that
#: changes no byte of what the builder writes, as the one of two meshes of
#: different materials at one depth (``model_raster.coplanar_overlaps``), keeps
#: the version, and so does a limit that moves with its readers' table.
BUILDER_VERSION = "1.7.0"
#: How many materials the strictest reader of a model keeps a table of, and how
#: many of its own it puts there after the model's: the Kleidos site's renderer,
#: whose lit shader holds ``MATERIAL_SLOTS`` (the Kleidos repository's
#: ``site/src/scripts/film/gl/shaders.ts``).
#: Its landing film's scene added the finger, the nail and the cover glass; the fleet
#: scene that replaced the film (``site/src/scripts/fleet/scene.ts``) adds the cover glass
#: alone, so three is the stricter of the two. The Kleidos repository's own tests hold
#: the two numbers to that renderer; ``tests/test_board_model_legends.py`` here holds
#: every model to ``MAX_MATERIALS``.
READER_SLOTS = 48
READER_OWN = 3
#: How many materials a model may hold, the legends' inks counted.
MAX_MATERIALS = READER_SLOTS - READER_OWN
#: What the name of a legend's ink material starts with.
INK_PREFIX = glb_legends.INK_PREFIX
#: The web level of detail (``--web-px-per-mm``): a drawn element is kept when
#: its strokes (``legend_mesh.width_mm``) cover at least this many pixels at
#: the largest scale the site draws the board at, the line of a stroke drawn
#: with no antialiasing, which the site's canvas asks for at a ratio of two.
WEB_MIN_STROKE_PX = 1.5
#: And its curves are flattened to within this many pixels at that scale,
#: where the spec's own flatness is finer.
WEB_FLATNESS_PX = 0.25

from paths import ROOT as REPO  # noqa: E402  (the repository root)

MM = 0.001
DEFAULT_CACHE = Path(os.environ.get("KLEIDOS_CAD_CACHE", Path.home() / ".cache" / "kleidos-cad"))
PINNED = {
    "numpy": "2.5.5",
    "shapely": "2.2.0",
    "trimesh": "5.2.2",
    "mapbox_earcut": "2.1.0",
    "scipy": "1.18.1",
    "networkx": "3.7",
    "rtree": "1.4.1",
    "cascadio": "0.1.1",
    "fast-simplification": "0.2.0",
    "fonttools": "4.68.0",
}
#: The ``screen`` mesh's ``extras.uv``. Its words name three.js's switch for an
#: upload with no vertical flip (``UNPACK_FLIP_Y_WEBGL`` off); they stay as they
#: are because the StickS3 master carries them in its bytes, and the web model's
#: manifest row records that master's digest.
SCREEN_UV_NOTE = (
    "glTF convention: (0,0) is the image top-left; load the capture "
    "with texture.flipY = false so it reads upright"
)


class SpecError(ValueError):
    """The spec asks for something the builder cannot do."""


# ---------------------------------------------------------------- spec keys

#: Every key each kind of spec object may hold (``note`` is admitted anywhere).
KEYS = {
    "spec": {
        "schema",
        "board",
        "node_name",
        "output",
        "copyright",
        "source",
        "tessellation",
        "transform",
        "split",
        "clean",
        "select",
        "parts",
        "volumes",
        "cull",
        "center_mm",
        "center_from",
        "front_frame",
        "face_frames",
        "measurements",
        "quant_mm",
        "planar_min_area",
        "materials",
        "meshes",
        "notes",
        "modules",
    },
    "module": {"name", "source", "tessellation", "transform", "split", "clean", "select", "parts"},
    "source": {
        "vendor",
        "format",
        "url",
        "sha256",
        "file",
        "repository",
        "path",
        "commit",
        "bytes",
        "license",
        "copyright",
        "license_note",
    },
    "tessellation": {"tol_linear", "tol_angular"},
    "match": {
        "name",
        "min_ge",
        "min_le",
        "max_ge",
        "max_le",
        "extent_gt",
        "extent_lt",
        "faces_gt",
        "faces_lt",
    },
    "part": {"name", "match", "ops", "required", "merge"},
    "op": {"slice", "decimate", "cull"},
    "slice": {"normal", "origin", "cap"},
    "decimate": {"face_count"},
    "cull": {"parts", "volumes", "margin", "same_box"},
    "cull_op": {"volumes", "margin", "same_box"},
    "volume": {"frame", "boxes"},
    "front_frame": {"left_x", "top_y"},
    "material": {"name", "rgb", "hex", "rough", "metal", "alpha", "unlit", "double"},
    "mesh": {
        "name",
        "material",
        "part",
        "shapes",
        "screen",
        "glass",
        "legends",
        "smooth_deg",
        "quantize",
        "inside",
        "outside",
    },
    "legends": {"front", "drawing", "face", "plane", "on", "x", "y", "z", "flatness", "rough"},
    "screen": {"z"},
    "glass": {"rect", "z", "frame"},
    "shape": {"box", "volume", "prism", "cylinder", "sphere", "quad_grid", "loft", "frame"},
    "loft": {"axis", "sections", "caps"},
    "section": {"at", "polygon"},
    "prism": {"axis", "range", "profile", "volume", "faces"},
    "profile": {
        "rect",
        "rounded_rect",
        "stadium",
        "polygon",
        "rounded",
        "r",
        "res",
        "inner",
        "holes",
    },
    "cylinder": {"axis", "c", "r", "range", "sections"},
    "sphere": {"c", "r", "subdivisions", "z_min"},
    "quad_grid": {"axis", "at", "facing", "u_center", "v_center", "cols", "rows", "pitch", "size"},
}
GEOMETRY = ("box", "volume", "prism", "cylinder", "sphere", "quad_grid", "loft")
#: The ends of a loft, as its ``caps`` names them.
LOFT_CAPS = ("first", "last")
PROFILES = ("rect", "rounded_rect", "stadium", "polygon", "rounded")


def keys(obj: dict[str, Any], kind: str, where: str) -> None:
    """Refuse a key the builder would not read (``note`` is always admitted)."""
    if not isinstance(obj, dict):
        raise SpecError(f"{where}: expected an object, got {obj!r}")
    extra = sorted(set(obj) - KEYS[kind] - {"note"})
    if extra:
        raise SpecError(f"{where}: unknown key(s) {extra}; a {kind} takes {sorted(KEYS[kind])}")


def one_of(obj: dict[str, Any], names: Iterable[str], where: str) -> str:
    got = [k for k in names if k in obj]
    if len(got) != 1:
        raise SpecError(f"{where}: needs exactly one of {list(names)}, has {got}")
    return str(got[0])


def units(spec: dict[str, Any]) -> list[tuple[str | None, dict[str, Any]]]:
    """[(name, object)] of the vendor files a spec builds from: its own, then its modules'.

    The spec's own source is named ``None``; a module is named by its ``name``.
    Each object holds that file's ``source``, ``tessellation``, ``transform``,
    ``split``, ``clean``, ``select`` and ``parts``.
    """
    own = [] if own_model(spec) else [(None, spec)]
    return own + [(m.get("name"), m) for m in spec.get("modules", [])]


#: The only keys of the ``source`` of a model built from no vendor file.
OWN_SOURCE_KEYS = {"format", "license", "copyright", "license_note"}


def own_model(spec: dict[str, Any]) -> bool:
    """True for a spec built from no vendor file: ``source`` ``format`` ``none``."""
    return isinstance(spec.get("source"), dict) and spec["source"].get("format") == "none"


def _validate_own(spec: dict[str, Any]) -> None:
    """A model of no vendor file names nothing a vendor file would give."""
    extra = sorted(set(spec["source"]) - OWN_SOURCE_KEYS - {"note"})
    if extra:
        raise SpecError(
            f"source: a model of no vendor file (format none) takes only "
            f"{sorted(OWN_SOURCE_KEYS)}, not {extra}"
        )
    for need in ("license", "copyright"):
        if not spec["source"].get(need):
            raise SpecError(f"source: a model of no vendor file still states its {need}")
    vendor = [
        k for k in ("tessellation", "transform", "split", "clean", "select", "parts") if spec.get(k)
    ]
    if vendor:
        raise SpecError(
            f"a model of no vendor file has no {vendor}: there is nothing to cut into parts"
        )
    if spec.get("center_mm") == "auto" or "auto" in (spec.get("front_frame") or {}).values():
        raise SpecError("a model of no vendor file writes center_mm and front_frame in numbers")


def _validate_unit(unit: dict[str, Any], where: str) -> None:
    keys(unit["source"], "source", f"{where}source")
    if "tessellation" in unit:
        keys(unit["tessellation"], "tessellation", f"{where}tessellation")
    if "select" in unit:
        keys(unit["select"], "match", f"{where}select")
    for rule in unit["parts"]:
        at = f"{where}part {rule.get('name')!r}"
        keys(rule, "part", at)
        keys(rule.get("match", {}), "match", f"{at} match")
        for op in rule.get("ops", []):
            keys(op, "op", f"{at} op")
            kind = one_of(op, KEYS["op"], f"{at} op")
            keys(op[kind], "cull_op" if kind == "cull" else kind, f"{at} {kind}")


def legends_drawing(leg: dict[str, Any]) -> tuple[str, str]:
    """(the drawing a legends mesh reads, relative to the spec; the face it draws)."""
    return str(leg.get("drawing", leg.get("front"))), str(leg.get("face", "front"))


def validate(spec: dict[str, Any]) -> None:
    """Check every object of *spec* for keys the builder would not read."""
    keys(spec, "spec", "spec")
    modules = spec.get("modules", [])
    if not isinstance(modules, list):
        raise SpecError("modules: expected a list of objects")
    for i, module in enumerate(modules):
        keys(module, "module", f"module {i}")
        if not isinstance(module.get("name"), str) or not module["name"]:
            raise SpecError(f"module {i}: names itself (name)")
        for need in ("source", "parts"):
            if need not in module:
                raise SpecError(f"module {module['name']!r}: gives {need}")
    names = [m["name"] for m in modules]
    if len(set(names)) != len(names):
        raise SpecError(f"module names repeat: {sorted({n for n in names if names.count(n) > 1})}")
    if own_model(spec):
        _validate_own(spec)
    elif "source" not in spec:
        raise SpecError(
            "source: a spec names its vendor file, or format none for a model built from none"
        )
    part_names = []
    for name, unit in units(spec):
        _validate_unit(unit, "" if name is None else f"module {name!r} ")
        part_names += [rule.get("name") for rule in unit["parts"]]
    twice = sorted({str(n) for n in part_names if part_names.count(n) > 1})
    if twice:
        raise SpecError(
            f"part names repeat across the spec and its modules: {twice}; a mesh "
            f"names a part by its name alone"
        )
    for face, numbers in (spec.get("face_frames") or {}).items():
        if face == "note":
            continue
        if face == "front":
            raise SpecError("face_frames: the front is front_frame")
        try:
            board_faces.face_frame(face, {k: 0 for k in numbers if k != "note"})
        except ValueError as exc:
            raise SpecError(f"face_frames: {exc}") from None
    for name, vol in spec.get("volumes", {}).items():
        if name != "note" and isinstance(vol, dict):
            keys(vol, "volume", f"volume {name!r}")
    if "cull" in spec:
        keys(spec["cull"], "cull", "cull")
    if isinstance(spec.get("front_frame"), dict):
        keys(spec["front_frame"], "front_frame", "front_frame")
    for m in spec["materials"]:
        keys(m, "material", f"material {m.get('name')!r}")
        if m.get("alpha") is not None and not 0.0 < num(m["alpha"]) < 1.0:
            raise SpecError(
                f"material {m.get('name')!r}: alpha {m['alpha']!r} is not above 0 "
                f"and below 1 (an opaque material has no alpha)"
            )
        if str(m.get("name", "")).startswith(INK_PREFIX):
            raise SpecError(
                f"material {m.get('name')!r}: a name starting {INK_PREFIX!r} is a "
                f"legend ink's, which the builder makes from the drawing"
            )
    volume_names = set(spec.get("volumes", {})) - {"note"}
    names = [entry.get("name") for entry in spec["meshes"]]
    twice = sorted({n for n in names if names.count(n) > 1}, key=str)
    if twice:
        raise SpecError(f"mesh names repeat: {twice}")
    solid = {entry["name"] for entry in spec["meshes"] if "legends" not in entry}
    planes: dict[tuple[str, Any], Any] = {}
    faces_of: dict[str, set[str]] = {}  # drawing -> the faces legends meshes read it as
    for entry in spec["meshes"]:
        where = f"mesh {entry.get('name')!r}"
        keys(entry, "mesh", where)
        if "legends" in entry:
            leg = entry["legends"]
            if not isinstance(leg, dict) or "on" not in leg:
                raise SpecError(f"{where}: a legends mesh gives its drawing, on and its height")
            if ("front" in leg) == ("drawing" in leg):
                raise SpecError(
                    f"{where}: a legends mesh names its drawing once: drawing (any "
                    f"face), or front (the front.svg of the front face)"
                )
            face = leg.get("face", "front")
            if face not in board_faces.FACES:
                raise SpecError(f"{where}: face {face!r} is not one of {list(board_faces.FACES)}")
            if "front" in leg and face != "front":
                raise SpecError(
                    f"{where}: front names the front face's drawing; a drawing of "
                    f"the {face} face is given as drawing"
                )
            height = board_faces.height_key(face)
            given = [k for k in ("x", "y", "z") if k in leg]
            if given != [height]:
                raise SpecError(
                    f"{where}: legends on the {face} face lie at a height along "
                    f"{height} (give {height!r} alone), not {given}"
                )
            if not entry["name"].endswith("legends"):
                raise SpecError(
                    f'{where}: a legends mesh\'s name ends in "legends", so '
                    f'"_legends_<rrggbb>" finds its meshes in any model'
                )
            if leg["on"] not in solid:
                raise SpecError(f"{where}: on names no mesh {leg['on']!r} of this model")
            plane = (legends_drawing(leg)[0], leg.get("plane", "keys"))
            if plane in planes:
                raise SpecError(
                    f"{where}: {planes[plane]!r} already draws the plane {plane[1]!r} of {plane[0]}"
                )
            planes[plane] = entry["name"]
            faces_of.setdefault(plane[0], set()).add(face)
            if len(faces_of[plane[0]]) > 1:
                raise SpecError(
                    f"{where}: {plane[0]} is read as the drawing of "
                    f"{sorted(faces_of[plane[0]])}; a drawing draws one face"
                )
        elif glb_legends.is_legend(str(entry.get("name"))) or str(entry.get("name")).endswith(
            "legends"
        ):
            raise SpecError(f"{where}: only a legends mesh is named like one")
        clips = [k for k in ("inside", "outside") if k in entry]
        if clips:
            if len(clips) > 1 or "part" not in entry:
                raise SpecError(f"{where}: inside or outside takes one volume, on a part mesh")
            if entry[clips[0]] not in volume_names:
                raise SpecError(f"{where}: {clips[0]} names no volume {entry[clips[0]]!r}")
        for kind in ("screen", "glass", "legends"):
            if kind in entry:
                keys(entry[kind], kind, f"{where} {kind}")
        if ("legends" in entry) == ("material" in entry):
            raise SpecError(
                f"{where}: a mesh names its material, and a legends mesh none "
                f"(its inks are the drawing's)"
            )
        for i, shape in enumerate(entry.get("shapes", [])):
            swhere = f"{where} shape {i}"
            keys(shape, "shape", swhere)
            kind = one_of(shape, GEOMETRY, swhere)
            inner = shape[kind]
            if kind in ("prism", "cylinder", "sphere", "quad_grid", "loft"):
                keys(inner, kind, f"{swhere} {kind}")
            if kind == "loft":
                sections = inner.get("sections")
                if not isinstance(sections, list) or len(sections) < 2:
                    raise SpecError(f"{swhere} loft: two or more sections")
                for j, sec in enumerate(sections):
                    keys(sec, "section", f"{swhere} loft section {j}")
                if len({len(sec.get("polygon", [])) for sec in sections}) != 1:
                    raise SpecError(f"{swhere} loft: every section has one count of points")
                caps = inner.get("caps", [])
                if not isinstance(caps, list) or not set(caps) <= set(LOFT_CAPS):
                    raise SpecError(f"{swhere} loft: caps {caps!r} is a list of {list(LOFT_CAPS)}")
            if kind == "prism":
                keys(inner["profile"], "profile", f"{swhere} profile")
                one_of(inner["profile"], PROFILES, f"{swhere} profile")
                faces = inner.get("faces")
                if faces is not None and (
                    not isinstance(faces, list)
                    or not faces
                    or not set(faces) <= set(PRISM_FACES)
                    or len(set(faces)) != len(faces)
                ):
                    raise SpecError(
                        f"{swhere} prism: faces {faces!r} is not a list of "
                        f"{list(PRISM_FACES)}, each at most once"
                    )


# ---------------------------------------------------------------- numbers

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _arith(node: ast.AST) -> float:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = _arith(node.operand)
        return -v if isinstance(node.op, ast.USub) else +v
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return float(_BINOPS[type(node.op)](_arith(node.left), _arith(node.right)))
    raise SpecError(f"not arithmetic: {ast.dump(node)}")


def num(v: float | str) -> float:
    """A spec number: a JSON number, or a string of arithmetic."""
    if isinstance(v, str):
        return float(_arith(ast.parse(v, mode="eval").body))
    if type(v) not in (int, float):
        raise SpecError(f"not a number: {v!r}")
    return float(v)


def nums(seq: Sequence[float | str], n: int | None = None) -> list[float]:
    out = [num(v) for v in seq]
    if n is not None and len(out) != n:
        raise SpecError(f"expected {n} numbers, got {seq!r}")
    return out


def srgb_to_linear(c: npt.ArrayLike) -> npt.NDArray[np.float64]:
    """sRGB 0-255 to linear light 0-1, one channel at a time through the C library's pow.

    numpy's vectorised power runs a different routine on a CPU with AVX-512
    (SVML), whose last bit can differ, so the same spec would write different
    bytes on different machines; Python's float power is the C library's pow
    on every machine, and gives the same 256 values on macOS and glibc.
    """
    out = []
    for channel in np.asarray(c, dtype=float).ravel().tolist():
        v = channel / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return np.array(out, dtype=float).reshape(np.shape(c))


# ---------------------------------------------------------------- shading


def crease_normals(
    mesh: trimesh.Trimesh, crease_deg: float, planar_min_area: float
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]]:
    """Per-corner normals: flat on planar facets, smooth across fillets.

    A corner of a face that belongs to a large coplanar group keeps the face
    normal. A corner of any other face averages, weighted by corner angle,
    the faces around that vertex within the crease angle; when one of those
    is planar, it takes the planar normal instead, so a fillet meets its
    flat neighbor tangentially and the flat face shows no gradient. A face of
    zero area has no normal and covers nothing: it is left out.
    Returns (positions[N,3], normals[N,3], faces[M,3]) with welded corners.
    """
    mesh = mesh.copy()
    mesh.merge_vertices()
    fn = mesh.face_normals
    has_normal = np.abs(fn).sum(axis=1) > 0
    faces = mesh.faces
    planar = np.zeros(len(faces), dtype=bool)
    planar_normal = np.zeros_like(fn)
    areas = mesh.area_faces
    for group in mesh.facets:
        if areas[group].sum() >= planar_min_area:
            planar[group] = True
            n = fn[group].mean(axis=0)
            planar_normal[group] = n / np.linalg.norm(n)
    # single big triangles are planar too
    big = (~planar) & (areas >= planar_min_area)
    planar[big] = True
    planar_normal[big] = fn[big]

    corner_angles = mesh.face_angles  # (M,3)
    vf = mesh.vertex_faces  # padded with -1
    cos_crease = np.cos(np.radians(crease_deg))

    out_pos: list[Any] = []
    out_nrm: list[Any] = []
    out_faces: list[Any] = []
    index = {}
    for fi, face in enumerate(faces):
        if not has_normal[fi]:
            continue
        tri = []
        for v in face:
            if planar[fi]:
                n = planar_normal[fi]
            else:
                nbrs = vf[v][vf[v] >= 0]
                ok = nbrs[(fn[nbrs] @ fn[fi]) >= cos_crease]
                pl = ok[planar[ok]]
                if len(pl):
                    n = planar_normal[pl].sum(axis=0)
                else:
                    w = np.array([corner_angles[g][list(faces[g]).index(v)] for g in ok])
                    n = (fn[ok] * w[:, None]).sum(axis=0)
                ln = np.linalg.norm(n)
                n = n / ln if ln > 1e-9 else fn[fi]
            key = (int(v), tuple(np.round(n, 4)))
            if key not in index:
                index[key] = len(out_pos)
                out_pos.append(mesh.vertices[v])
                out_nrm.append(n)
            tri.append(index[key])
        out_faces.append(tri)
    return (np.array(out_pos), np.array(out_nrm), np.array(out_faces, dtype=np.int64))


def flat(
    mesh: trimesh.Trimesh, planar_min_area: float
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]]:
    """Flat-shaded arrays for small hard-edged primitives (boxes)."""
    m = mesh.copy()
    m.merge_vertices()
    return crease_normals(m, 1.0, planar_min_area)


# ---------------------------------------------------------------- shapes


def box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> trimesh.Trimesh:
    b: trimesh.Trimesh = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b


def rounded_rect(
    x0: float, x1: float, y0: float, y1: float, r: float, res: int = 6
) -> BaseGeometry:
    core = sg.box(x0 + r, y0 + r, x1 - r, y1 - r)
    return core.buffer(r, quad_segs=res, join_style="round")


def stadium(cu: float, cv: float, w: float, h: float, res: int = 10) -> BaseGeometry:
    """A stadium (rounded slot) w wide and h tall centered on (cu, cv); w == h
    is a disc. A slot taller than wide is drawn in the other axis order."""
    if w < h:
        raise SpecError(f"stadium {w} wide and {h} tall: a stadium runs along u, so w >= h")
    r = h / 2
    core = sg.LineString([(cu - w / 2 + r, cv), (cu + w / 2 - r, cv)])
    return core.buffer(r, quad_segs=res)


def polygon(
    points: Sequence[Sequence[float]], holes: Sequence[Sequence[Sequence[float]]] = ()
) -> sg.Polygon:
    """A simple polygon from (u, v) points, holes optional, counter-clockwise."""
    poly = sg.Polygon(points, list(holes))
    if not poly.is_valid or poly.area <= 0:
        raise SpecError(f"polygon profile is not a simple polygon: {points!r}")
    return sg.polygon.orient(poly, 1.0)


def extrude(poly: sg.Polygon, axis: str, a0: float, a1: float) -> trimesh.Trimesh:
    """Extrude a polygon drawn in the two axes other than *axis* from a0 to a1.

    The polygon's (u, v) are (x, y) for axis z, (x, z) for axis y and (y, z)
    for axis x. Zero-area faces the triangulation leaves (a disc buffered
    from a zero-length line can leave a few) are dropped.
    """
    m = trimesh.creation.extrude_polygon(poly, height=a1 - a0)
    # read the triangles straight from the arrays: the mesh's cached normals
    # would follow it through the moves below and be reused downstream
    _, covers = _triangle_normals(np.asarray(m.vertices)[np.asarray(m.faces)])
    if not covers.all():
        m.update_faces(covers)
        m.remove_unreferenced_vertices()
    if axis == "z":
        m.apply_translation([0, 0, a0])
        return m
    v = m.vertices.copy()
    if axis == "y":
        # (u, v, h) -> (u, h, v): an axis swap mirrors the solid, so restore
        # outward winding
        m.vertices = np.column_stack([v[:, 0], v[:, 2] + a0, v[:, 1]])
        m.invert()
        return m
    if axis == "x":
        # (u, v, h) -> (h, u, v): a cyclic permutation, a rotation
        m.vertices = np.column_stack([v[:, 2] + a0, v[:, 0], v[:, 1]])
        return m
    raise SpecError(f"unknown axis {axis!r}")


#: A prism's faces, as its ``faces`` key names them.
PRISM_FACES = ("top", "bottom", "outer", "inner")


def prism_faces(
    mesh: trimesh.Trimesh, poly: sg.Polygon, axis: str, which: Sequence[str] | None
) -> trimesh.Trimesh:
    """Only the named faces of *mesh*, the prism ``extrude`` built from *poly* along *axis*.

    ``top`` is the cap at the range's far end (facing +axis), ``bottom`` the
    cap at its near end, ``outer`` the sides along the profile's outline and
    ``inner`` those along its holes. A face nothing can see from where the
    prism sits (inside a solid shell, under a slab) need not be drawn; *which*
    None keeps the whole closed prism.
    """
    if which is None:
        return mesh
    if not isinstance(poly, sg.Polygon):
        raise SpecError(f"faces {which!r}: the profile is not one polygon")
    k = "xyz".index(axis)
    u, v = [i for i in range(3) if i != k]
    tri = np.asarray(mesh.vertices)[np.asarray(mesh.faces)]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    along = n[:, k] / np.linalg.norm(n, axis=1)
    mid = tri.mean(axis=1)
    pts = shapely.points(mid[:, u], mid[:, v])
    to_outline = shapely.distance(pts, poly.exterior)
    to_hole = np.full(len(pts), np.inf)
    if poly.interiors:
        to_hole = shapely.distance(pts, sg.MultiLineString([h.coords for h in poly.interiors]))
    kind = np.where(
        along > 0.5, 0, np.where(along < -0.5, 1, np.where(to_outline <= to_hole, 2, 3))
    )
    keep = np.isin(kind, [PRISM_FACES.index(w) for w in which])
    m = mesh.copy()
    m.update_faces(keep)
    m.remove_unreferenced_vertices()
    return m


def cylinder(
    axis: str, cu: float, cv: float, r: float, a0: float, a1: float, sections: int = 20
) -> trimesh.Trimesh:
    c: trimesh.Trimesh = trimesh.creation.cylinder(radius=r, height=a1 - a0, sections=sections)
    mid = (a0 + a1) / 2
    if axis == "z":
        c.apply_translation([cu, cv, mid])
    elif axis == "y":
        c.apply_transform(_rotation_matrix(-np.pi / 2, [1, 0, 0]))
        c.apply_translation([cu, mid, cv])
    elif axis == "x":
        c.apply_transform(_rotation_matrix(np.pi / 2, [0, 1, 0]))
        c.apply_translation([mid, cu, cv])
    else:
        raise SpecError(f"unknown axis {axis!r}")
    return c


def loft(
    axis: str, sections: Sequence[tuple[float, Sequence[Sequence[float]]]], caps: Sequence[str] = ()
) -> trimesh.Trimesh:
    """The side surface through *sections*, [(at, [(u, v), ...]), ...] along *axis*.

    Point i of a section is joined to point i of the next by two triangles;
    every section is turned counterclockwise in (u, v) first, so the sides
    face out. ``first`` and ``last`` in *caps* close the first and the last
    section with a flat cap facing away from the others.
    """
    k = "xyz".index(axis)
    u, v = [i for i in range(3) if i != k]
    rings = []
    for at, pts in sections:
        ring = np.asarray(pts, dtype=float)
        if sg.Polygon(ring).exterior.is_ccw is False:
            ring = ring[::-1]
        rings.append((at, ring))
    n = len(rings[0][1])
    verts, faces = [], []
    for at, ring in rings:
        p = np.zeros((n, 3))
        p[:, u], p[:, v], p[:, k] = ring[:, 0], ring[:, 1], at
        verts.append(p)
    rising = rings[-1][0] > rings[0][0]
    for s in range(len(rings) - 1):
        a, b = s * n, (s + 1) * n
        for i in range(n):
            j = (i + 1) % n
            quad = [(a + i, a + j, b + j), (a + i, b + j, b + i)]
            faces += quad if rising else [t[::-1] for t in quad]
    vertices = np.vstack(verts)
    for which, s in (("first", 0), ("last", len(rings) - 1)):
        if which not in caps:
            continue
        tri = trimesh.creation.triangulate_polygon(sg.Polygon(rings[s][1]))[1]
        base = s * n
        up = (which == "last") == rising  # this cap faces +axis
        for corners in np.asarray(tri):
            t = [base + int(x) for x in corners]
            a, b, c = t if up else t[::-1]
            faces.append((a, b, c))
    # in (u, v, axis) order counterclockwise is +axis; the axis order (u, v, k)
    # of y is a mirror of (x, y, z)
    m = trimesh.Trimesh(vertices, np.asarray(faces), process=False)
    if axis == "y":
        m.invert()
    m.merge_vertices()
    return m


def quad_xy(
    x0: float, x1: float, y0: float, y1: float, z: float, facing: int = 1
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]]:
    """Quad in the x-y plane at z, facing +Z (facing=1) or -Z."""
    pos = np.array([[x0, y1, z], [x1, y1, z], [x1, y0, z], [x0, y0, z]], dtype=float)
    nrm = np.tile([0.0, 0.0, float(facing)], (4, 1))
    faces = np.array([[0, 2, 1], [0, 3, 2]])
    a, b, c = pos[faces[0]]
    if np.sign(np.cross(b - a, c - a)[2]) != facing:
        faces = faces[:, [0, 2, 1]]
    return pos, nrm, faces


def quad_xz(
    x0: float, x1: float, z0: float, z1: float, y: float, facing: int = -1
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]]:
    """Quad in the x-z plane at y, facing -Y (facing=-1) or +Y."""
    pos = np.array([[x0, y, z1], [x1, y, z1], [x1, y, z0], [x0, y, z0]], dtype=float)
    nrm = np.tile([0.0, float(facing), 0.0], (4, 1))
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    a, b, c = pos[faces[0]]
    if np.sign(np.cross(b - a, c - a)[1]) != facing:
        faces = faces[:, [0, 2, 1]]
    return pos, nrm, faces


def quad_grid(
    axis: str,
    at: float,
    facing: int,
    uc: float,
    vc: float,
    cols: int,
    rows: int,
    pitch: float,
    size: float,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]]:
    """A rows x cols grid of flat squares centered on (uc, vc) in the plane
    normal to *axis* at *at*; rows run along v, columns along u."""
    qp: list[npt.NDArray[np.float64]] = []
    qn: list[npt.NDArray[np.float64]] = []
    qf: list[npt.NDArray[np.int64]] = []
    for row in range(rows):
        for col in range(cols):
            cu = uc + (col - (cols - 1) / 2) * pitch
            cv = vc + (row - (rows - 1) / 2) * pitch
            if axis == "y":
                p, n, f = quad_xz(
                    cu - size / 2, cu + size / 2, cv - size / 2, cv + size / 2, at, facing=facing
                )
            elif axis == "z":
                p, n, f = quad_xy(
                    cu - size / 2, cu + size / 2, cv - size / 2, cv + size / 2, at, facing=facing
                )
            else:
                raise SpecError(f"quad_grid: unsupported axis {axis!r}")
            qf.append(f + 4 * len(qp))
            qp.append(p)
            qn.append(n)
    return np.vstack(qp), np.vstack(qn), np.vstack(qf)


# ---------------------------------------------------------------- front frame


class Frame:
    """The front frame of measurements.json placed in the build frame."""

    def __init__(self, left_x: float, top_y: float) -> None:
        self.left_x = left_x
        self.top_y = top_y

    def x(self, fx: float) -> float:
        return self.left_x + fx

    def y(self, fy: float) -> float:
        return self.top_y - fy

    def xr(self, f0: float, f1: float) -> tuple[float, float]:
        return self.x(f0), self.x(f1)

    def yr(self, f0: float, f1: float) -> tuple[float, float]:
        # front y grows down, build y grows up: the range swaps ends
        return self.y(f1), self.y(f0)

    def u(self, axis: str, f0: float, f1: float) -> tuple[float, float]:
        """A (u0, u1) profile range of a prism along *axis*."""
        return self.xr(f0, f1) if axis in ("z", "y") else self.yr(f0, f1)

    def v(self, axis: str, f0: float, f1: float) -> tuple[float, float]:
        return self.yr(f0, f1) if axis == "z" else (f0, f1)

    def a(self, axis: str, f0: float, f1: float) -> tuple[float, float]:
        """The extrusion range along *axis*."""
        if axis == "x":
            return self.xr(f0, f1)
        if axis == "y":
            return self.yr(f0, f1)
        if axis == "z":
            return f0, f1
        raise KeyError(axis)

    def cu(self, axis: str, f: float) -> float:
        return self.x(f) if axis in ("z", "y") else self.y(f)

    def cv(self, axis: str, f: float) -> float:
        return self.y(f) if axis == "z" else f


# ---------------------------------------------------------------- GLB


class Glb:
    def __init__(self, root_name: str, center: npt.ArrayLike, quant_mm: float) -> None:
        self.center = np.asarray(center, dtype=float)
        self.quant_mm = quant_mm
        self.bin = bytearray()
        self.gltf: dict[str, Any] = {
            "asset": {"version": "2.0"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"name": root_name, "children": []}],
            "meshes": [],
            "materials": [],
            "accessors": [],
            "bufferViews": [],
            "buffers": [{"byteLength": 0}],
            "extensionsUsed": [],
        }
        self.mat_index: dict[str, int] = {}
        self.triangles = 0

    def _view(self, data: bytes, target: int | None, stride: int | None = None) -> int:
        while len(self.bin) % 4:
            self.bin.append(0)
        off = len(self.bin)
        self.bin += data
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if stride:
            bv["byteStride"] = stride
        if target:
            bv["target"] = target
        self.gltf["bufferViews"].append(bv)
        return len(self.gltf["bufferViews"]) - 1

    def _acc(
        self,
        arr: npt.NDArray[Any],
        ctype: int,
        typ: str,
        target: int | None,
        minmax: bool = False,
        normalized: bool = False,
        pad_to: int | None = None,
    ) -> int:
        data = arr
        stride = None
        if pad_to:
            # vertex elements must start on 4-byte boundaries: pad each one
            padded = np.zeros((arr.shape[0], pad_to), dtype=arr.dtype)
            padded[:, : arr.shape[1]] = arr
            data = padded
            stride = pad_to * arr.dtype.itemsize
        bv = self._view(data.tobytes(), target, stride)
        acc = {"bufferView": bv, "componentType": ctype, "count": int(arr.shape[0]), "type": typ}
        if normalized:
            acc["normalized"] = True
        if minmax:
            acc["min"] = arr.min(axis=0).tolist()
            acc["max"] = arr.max(axis=0).tolist()
        self.gltf["accessors"].append(acc)
        return len(self.gltf["accessors"]) - 1

    def _require(self, ext: str) -> None:
        for key in ("extensionsUsed", "extensionsRequired"):
            lst = self.gltf.setdefault(key, [])
            if ext not in lst:
                lst.append(ext)

    def material(
        self,
        name: str,
        rgb: Sequence[float],
        rough: float,
        metal: float = 0.0,
        alpha: float | None = None,
        unlit: bool = False,
        double: bool = False,
    ) -> int:
        if name in self.mat_index:
            return self.mat_index[name]
        lin = srgb_to_linear(rgb).tolist()
        m: dict[str, Any] = {
            "name": name,
            "pbrMetallicRoughness": {
                "baseColorFactor": lin + [1.0 if alpha is None else alpha],
                "metallicFactor": metal,
                "roughnessFactor": rough,
            },
        }
        if alpha is not None:
            m["alphaMode"] = "BLEND"
        if double:
            m["doubleSided"] = True
        if unlit:
            m["extensions"] = {"KHR_materials_unlit": {}}
            if "KHR_materials_unlit" not in self.gltf["extensionsUsed"]:
                self.gltf["extensionsUsed"].append("KHR_materials_unlit")
        self.gltf["materials"].append(m)
        self.mat_index[name] = len(self.gltf["materials"]) - 1
        return self.mat_index[name]

    def mesh(
        self,
        name: str,
        prims: list[tuple[Any, ...]],
        extras: dict[str, Any] | None = None,
        quantize: bool = True,
    ) -> None:
        """prims: list of (pos_mm, nrm, faces, uv_or_None, material_index).

        quantize: KHR_mesh_quantization. Positions become int16 in units of
        quant_mm (the node carries the scale back to meters) and normals
        int8. Meshes a page will read (screen, glass) stay float.
        """
        gl_prims = []
        for pos, nrm, faces, uv, mat in prims:
            n = np.asarray(nrm, dtype=np.float64)
            length = np.linalg.norm(n, axis=1, keepdims=True)
            if not (length > 0).all():
                raise SpecError(f"{name}: {int((length == 0).sum())} vertex normals of zero length")
            n /= length
            rel = np.asarray(pos, dtype=float) - self.center
            if quantize:
                self._require("KHR_mesh_quantization")
                q = np.round(rel / self.quant_mm)
                if np.abs(q).max() > 32767:
                    raise SpecError(f"{name}: a position overflows int16 at {self.quant_mm} mm")
                qp = q.astype(np.int16)
                qn = np.clip(np.round(n * 127), -127, 127).astype(np.int8)
                attrs = {
                    "POSITION": self._acc(qp, 5122, "VEC3", 34962, minmax=True, pad_to=4),
                    "NORMAL": self._acc(qn, 5120, "VEC3", 34962, normalized=True, pad_to=4),
                }
            else:
                p = (rel * MM).astype(np.float32)
                attrs = {
                    "POSITION": self._acc(p, 5126, "VEC3", 34962, minmax=True),
                    "NORMAL": self._acc(n.astype(np.float32), 5126, "VEC3", 34962),
                }
            if uv is not None:
                attrs["TEXCOORD_0"] = self._acc(
                    np.asarray(uv, dtype=np.float32), 5126, "VEC2", 34962
                )
            f = np.asarray(faces).reshape(-1)
            self.triangles += len(f) // 3
            if len(rel) < 65536:
                idx = self._acc(f.astype(np.uint16), 5123, "SCALAR", 34963)
            else:
                idx = self._acc(f.astype(np.uint32), 5125, "SCALAR", 34963)
            gl_prims.append({"attributes": attrs, "indices": idx, "material": mat})
        self.gltf["meshes"].append({"name": name, "primitives": gl_prims})
        node = {"name": name, "mesh": len(self.gltf["meshes"]) - 1}
        if quantize:
            node["scale"] = [self.quant_mm * MM] * 3
        if extras:
            node["extras"] = extras
        self.gltf["nodes"].append(node)
        self.gltf["nodes"][0]["children"].append(len(self.gltf["nodes"]) - 1)

    def write(self, path: str | Path) -> int:
        while len(self.bin) % 4:
            self.bin.append(0)
        self.gltf["buffers"][0]["byteLength"] = len(self.bin)
        for key in ("extensionsUsed", "extensionsRequired"):
            if not self.gltf.get(key):
                self.gltf.pop(key, None)
        js = json.dumps(self.gltf, separators=(",", ":"), ensure_ascii=False).encode()
        while len(js) % 4:
            js += b" "
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        with open(path, "wb") as fh:
            fh.write(struct.pack("<III", 0x46546C67, 2, total))
            fh.write(struct.pack("<II", len(js), 0x4E4F534A))
            fh.write(js)
            fh.write(struct.pack("<II", len(self.bin), 0x004E4942))
            fh.write(self.bin)
        return total


# ---------------------------------------------------------------- source


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cached_source(unit: dict[str, Any], cache: str | Path, fetch: bool) -> Path:
    """A vendor file from the cache, downloaded first when *fetch* is set.

    *unit* is the spec, for its own file, or one of its ``modules``."""
    src = unit["source"]
    path: Path = Path(cache) / src["sha256"][:12] / src["file"]
    if not path.is_file() and fetch:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".part")
        if not str(src["url"]).startswith("https://"):
            raise SpecError(f"{src['url']}: a vendor file is fetched over https only")
        print(f"fetching {src['url']}")
        # S310 asks for a checked scheme: it is checked just above (https only).
        with (
            urllib.request.urlopen(src["url"], timeout=120) as resp,  # noqa: S310
            open(tmp, "wb") as fh,
        ):
            while chunk := resp.read(1 << 20):
                fh.write(chunk)
        digest = sha256_file(tmp)
        if digest != src["sha256"]:
            tmp.unlink()
            raise SpecError(f"{src['url']} served sha256 {digest}, not {src['sha256']}")
        tmp.replace(path)
    return path


def apply_transform(mesh: trimesh.Trimesh, ops: list[dict[str, Any]]) -> trimesh.Trimesh:
    for op in ops:
        if "rotate" in op:
            r = op["rotate"]
            axis = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}[r["axis"]]
            mesh.apply_transform(_rotation_matrix(np.radians(num(r["deg"])), axis))
        elif "translate" in op:
            mesh.apply_translation(nums(op["translate"], 3))
        elif "scale" in op:
            scale = num(op["scale"])
            mesh.apply_transform(np.diag([scale, scale, scale, 1.0]))
        else:
            raise SpecError(f"unknown transform {op!r}")
    return mesh


def step_mesh_dir(spec: dict[str, Any], src_path: str | Path, cache: str | Path) -> Path:
    """Tessellate a STEP once into a GLB in the cache; return its path."""
    import cascadio  # only a STEP needs it

    tes = spec.get("tessellation", {})
    tl, ta = num(tes.get("tol_linear", 0.01)), num(tes.get("tol_angular", 0.5))
    out: Path = Path(cache) / spec["source"]["sha256"][:12] / f"step-{tl:g}-{ta:g}.glb"
    if not out.is_file():
        out.parent.mkdir(parents=True, exist_ok=True)
        rc = cascadio.step_to_glb(
            str(src_path), str(out), tol_linear=tl, tol_angular=ta, use_parallel=False
        )
        if rc != 0 or not out.is_file():
            raise SpecError(f"cascadio could not tessellate {src_path} (rc {rc})")
    return out


def clean(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Drop zero-area and repeated faces (a STEP tessellation has both)."""
    mesh.update_faces(mesh.nondegenerate_faces(height=1e-6))
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def load_components(
    spec: dict[str, Any], src_path: str | Path, cache: str | Path
) -> list[tuple[str, trimesh.Trimesh]]:
    """[(name, mesh)] in the build frame: STL pieces or STEP parts."""
    src = spec["source"]
    ops = spec.get("transform", [])
    if src["format"] == "stl":
        mesh = _one_mesh(trimesh.load(str(src_path), force="mesh"), str(src_path))
        if ops:
            apply_transform(mesh, ops)
        mesh.merge_vertices()
        if spec.get("clean", False):
            clean(mesh)
        pieces = mesh.split(only_watertight=False) if spec.get("split", True) else [mesh]
        return [(f"piece{i}", p) for i, p in enumerate(pieces)]
    if src["format"] == "step":
        scene = trimesh.load(str(step_mesh_dir(spec, src_path, cache)))
        if not isinstance(scene, trimesh.Scene):
            raise SpecError(f"{src_path}: the STEP tessellation is not a scene")
        out = []
        for node in scene.graph.nodes_geometry:
            transform, gname = scene.graph[node]
            m = scene.geometry[gname].copy()
            m.apply_transform(transform)
            m.apply_transform(np.diag([1000.0, 1000.0, 1000.0, 1.0]))  # cascadio writes meters
            if ops:
                apply_transform(m, ops)
            m.merge_vertices()
            if spec.get("clean", True):
                clean(m)
            label = f"{node} {gname}"
            if spec.get("split", False):
                out += [(f"{label} #{i}", p) for i, p in enumerate(m.split(only_watertight=False))]
            else:
                out.append((label, m))
        return out
    raise SpecError(f"unknown source format {src['format']!r}")


def matches(name: str, mesh: trimesh.Trimesh, rule: dict[str, Any]) -> bool:
    lo, hi = mesh.bounds
    ext = mesh.extents

    def axes(
        key: str, values: npt.NDArray[np.float64], test: Callable[[float, float], bool]
    ) -> bool:
        lim = rule.get(key)
        if lim is None:
            return True
        return all(lim[i] is None or test(values[i], num(lim[i])) for i in range(3))

    if "name" in rule and not re.search(rule["name"], name):
        return False
    if "faces_gt" in rule and not len(mesh.faces) > rule["faces_gt"]:
        return False
    if "faces_lt" in rule and not len(mesh.faces) < rule["faces_lt"]:
        return False
    return (
        axes("min_ge", lo, operator.ge)
        and axes("min_le", lo, operator.le)
        and axes("max_ge", hi, operator.ge)
        and axes("max_le", hi, operator.le)
        and axes("extent_gt", ext, operator.gt)
        and axes("extent_lt", ext, operator.lt)
    )


def part_ops(
    mesh: trimesh.Trimesh,
    ops: list[dict[str, Any]],
    volumes: dict[str, list[list[float]]],
    name: str = "?",
) -> trimesh.Trimesh:
    for op in ops:
        if "slice" in op:
            s = op["slice"]
            mesh = _slice_mesh_plane(
                mesh,
                plane_normal=nums(s["normal"], 3),
                plane_origin=nums(s["origin"], 3),
                cap=bool(s.get("cap", False)),
            )
        elif "decimate" in op:
            mesh = clean(
                mesh.simplify_quadric_decimation(face_count=int(op["decimate"]["face_count"]))
            )
        elif "cull" in op:
            c = op["cull"]
            mesh, n = drop_hidden(
                mesh,
                cull_boxes(volumes, c["volumes"]),
                num(c.get("margin", 0.06)),
                bool(c.get("same_box", False)),
            )
            print(f"culled hidden faces: {name} {n} (part op)")
        else:
            raise SpecError(f"unknown part op {op!r}")
    return mesh


def gather_parts(
    spec: dict[str, Any],
    components: list[tuple[str, trimesh.Trimesh]],
    volumes: dict[str, list[list[float]]],
) -> dict[str, trimesh.Trimesh]:
    select = spec.get("select", {})
    rules = spec["parts"]
    found: dict[str, list[trimesh.Trimesh]] = {r["name"]: [] for r in rules}
    for name, mesh in components:
        if not matches(name, mesh, select):
            continue
        for rule in rules:
            if matches(name, mesh, rule.get("match", {})):
                found[rule["name"]].append(mesh)
                break
    parts: dict[str, trimesh.Trimesh] = {}
    for rule in rules:
        got = found[rule["name"]]
        if not got:
            if rule.get("required", True):
                raise SpecError(f"part {rule['name']!r}: no component matches")
            continue
        if len(got) > 1 and not rule.get("merge", True):
            raise SpecError(f"part {rule['name']!r}: {len(got)} components match")
        mesh = got[0] if len(got) == 1 else _one_mesh(trimesh.util.concatenate(got), rule["name"])
        parts[rule["name"]] = part_ops(mesh, rule.get("ops", []), volumes, rule["name"])
    return parts


# ---------------------------------------------------------------- build


def inside_box(
    points: npt.NDArray[np.float64],
    box_: list[float],
    margin: float = 0.06,
) -> npt.NDArray[np.bool_]:
    x0, x1, y0, y1, z0, z1 = box_
    return (
        (points[:, 0] > x0 + margin)
        & (points[:, 0] < x1 - margin)
        & (points[:, 1] > y0 + margin)
        & (points[:, 1] < y1 - margin)
        & (points[:, 2] > z0 + margin)
        & (points[:, 2] < z1 - margin)
    )


def inside_any(
    points: npt.NDArray[np.float64],
    boxes: Sequence[list[float]],
    margin: float = 0.06,
) -> npt.NDArray[np.bool_]:
    inside = np.zeros(len(points), dtype=bool)
    for b in boxes:
        inside |= inside_box(points, b, margin)
    return inside


def drop_hidden(
    mesh: trimesh.Trimesh,
    solid_boxes: Sequence[list[float]],
    margin: float = 0.06,
    same_box: bool = False,
) -> tuple[trimesh.Trimesh, int]:
    """Remove the faces opaque filler boxes hide.

    A face goes when each of its three corners sits inside one of the boxes,
    not necessarily the same one (so a visible wall between two boxes that
    meet across it goes too); with *same_box*, only when one box holds all
    three.
    """
    if same_box:
        hidden = np.zeros(len(mesh.faces), dtype=bool)
        for b in solid_boxes:
            hidden |= inside_box(mesh.vertices, b, margin)[mesh.faces].all(axis=1)
        keep = ~hidden
    else:
        v_in = inside_any(mesh.vertices, solid_boxes, margin)
        keep = ~v_in[mesh.faces].all(axis=1)
    m = mesh.copy()
    m.update_faces(keep)
    m.remove_unreferenced_vertices()
    return m, int((~keep).sum())


def split_by_boxes(
    arrays: tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]],
    boxes: Sequence[list[float]],
    name: str = "?",
) -> tuple[
    tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]],
    tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]],
]:
    """(inside, outside): the faces of shaded *arrays* one box holds whole, and the rest.

    *arrays* is (positions, normals, faces) as ``crease_normals`` gives them
    for the whole part, so both meshes keep the normals the part has where
    they meet, and a fillet that runs on past the split stays smooth across
    it. A face is inside when one of the boxes holds its three corners; no
    face is cut, so the split follows the part's own edges, and the two
    meshes meet edge to edge and hold every face once. A box drawn just past
    the edges a split should follow (where a flat face meets its fillet)
    splits there; a face with corners on both sides of a box's side stays
    outside, and the count of them is printed.
    """
    pos, nrm, faces = arrays
    corners = pos[faces].reshape(-1, 3)
    inside = np.zeros(len(faces), dtype=bool)
    touched = np.zeros(len(faces), dtype=bool)
    for box_ in boxes:
        held = inside_box(corners, box_, 0.0).reshape(-1, 3)
        inside |= held.all(axis=1)
        touched |= held.any(axis=1)
    print(
        f"split {name}: {int(inside.sum())} faces inside, {int((~inside).sum())} outside, "
        f"{int((touched & ~inside).sum())} of them across a box side"
    )
    out = []
    for keep in (inside, ~inside):
        kept = faces[keep]
        used = np.unique(kept)
        remap = np.full(len(pos), -1, dtype=np.int64)
        remap[used] = np.arange(len(used))
        out.append((pos[used], nrm[used], remap[kept]))
    return out[0], out[1]


def cull_boxes(volumes: dict[str, list[list[float]]], names: Sequence[str]) -> list[list[float]]:
    try:
        return [b for name in names for b in volumes[name]]
    except KeyError as exc:
        raise SpecError(f"cull: no volume {exc.args[0]!r}") from None


def _polygon(geom: BaseGeometry) -> sg.Polygon:
    """A profile as the one polygon a prism is extruded from."""
    if not isinstance(geom, sg.Polygon):
        raise SpecError(f"a prism profile is one polygon, not a {geom.geom_type}")
    return geom


def _front(frame: Frame | None) -> Frame:
    """The spec's front frame, for a value written in it: refused when the spec sets none."""
    if frame is None:
        raise SpecError("a value is written in the front frame, but the spec has no front_frame")
    return frame


def shape_meshes(
    shape: dict[str, Any],
    volumes: dict[str, list[list[float]]],
    frame: Frame | None,
) -> (
    list[trimesh.Trimesh]
    | tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]]
):
    """A spec shape as a list of trimesh solids, or one (pos, nrm, faces)."""
    front = shape.get("frame") == "front"
    if front and frame is None:
        raise SpecError("a front-frame shape needs front_frame and measurements")
    if "box" in shape:
        x0, x1, y0, y1, z0, z1 = nums(shape["box"], 6)
        if front:
            (x0, x1), (y0, y1) = _front(frame).xr(x0, x1), _front(frame).yr(y0, y1)
        return [box(x0, x1, y0, y1, z0, z1)]
    if "volume" in shape:
        return [box(*b) for b in volumes[shape["volume"]]]
    if "prism" in shape:
        p = shape["prism"]
        axis = p["axis"]
        prof = p["profile"]
        if "volume" in p:
            (b,) = volumes[p["volume"]]
            span = {"x": (0, 1), "y": (2, 3), "z": (4, 5)}
            uv = {"z": ("x", "y"), "y": ("x", "z"), "x": ("y", "z")}[axis]
            u0, u1 = (b[i] for i in span[uv[0]])
            v0, v1 = (b[i] for i in span[uv[1]])
            a0, a1 = (b[i] for i in span[axis])
            if "rounded" in prof:
                poly = rounded_rect(u0, u1, v0, v1, num(prof["rounded"]), int(prof.get("res", 6)))
            else:
                poly = sg.box(u0, v0, u1, v1)
            solid = _polygon(poly)
            return [prism_faces(extrude(solid, axis, a0, a1), solid, axis, p.get("faces"))]
        a0, a1 = nums(p["range"], 2)
        if front:
            a0, a1 = _front(frame).a(axis, a0, a1)
        if "rect" in prof:
            u0, u1, v0, v1 = nums(prof["rect"], 4)
            if front:
                (u0, u1), (v0, v1) = _front(frame).u(axis, u0, u1), _front(frame).v(axis, v0, v1)
            poly = sg.box(u0, v0, u1, v1)
        elif "rounded_rect" in prof:
            u0, u1, v0, v1 = nums(prof["rounded_rect"], 4)
            if front:
                (u0, u1), (v0, v1) = _front(frame).u(axis, u0, u1), _front(frame).v(axis, v0, v1)
            poly = rounded_rect(u0, u1, v0, v1, num(prof["r"]), int(prof.get("res", 6)))
        elif "stadium" in prof:
            cu, cv, w, h = nums(prof["stadium"], 4)
            if front:
                cu, cv = _front(frame).cu(axis, cu), _front(frame).cv(axis, cv)
            res = int(prof.get("res", 10))
            poly = stadium(cu, cv, w, h, res)
            if "inner" in prof:
                iw, ih = nums(prof["inner"], 2)
                poly = poly.difference(stadium(cu, cv, iw, ih, res))
        elif "polygon" in prof:

            def ring(points: Sequence[Sequence[float | str]]) -> list[tuple[float, float]]:
                pts = [(u, v) for u, v in (nums(p, 2) for p in points)]
                if front:
                    pts = [(_front(frame).cu(axis, u), _front(frame).cv(axis, v)) for u, v in pts]
                return pts

            poly = polygon(ring(prof["polygon"]), [ring(h) for h in prof.get("holes", [])])
        else:
            raise SpecError(f"unknown profile {prof!r}")
        solid = _polygon(poly)
        return [prism_faces(extrude(solid, axis, a0, a1), solid, axis, p.get("faces"))]
    if "sphere" in shape:
        s = shape["sphere"]
        cx, cy, cz = nums(s["c"], 3)
        if front:
            cx, cy = _front(frame).x(cx), _front(frame).y(cy)
        sph = trimesh.creation.icosphere(
            subdivisions=int(s.get("subdivisions", 2)), radius=num(s["r"])
        )
        sph.apply_translation([cx, cy, cz])
        if "z_min" in s:
            sph = _slice_mesh_plane(
                sph, plane_normal=[0, 0, 1], plane_origin=[0, 0, num(s["z_min"])]
            )
        return [sph]
    if "cylinder" in shape:
        c = shape["cylinder"]
        axis = c["axis"]
        cu, cv = nums(c["c"], 2)
        a0, a1 = nums(c["range"], 2)
        if front:
            cu, cv = _front(frame).cu(axis, cu), _front(frame).cv(axis, cv)
            a0, a1 = _front(frame).a(axis, a0, a1)
        return [cylinder(axis, cu, cv, num(c["r"]), a0, a1, int(c.get("sections", 20)))]
    if "loft" in shape:
        lf = shape["loft"]
        axis = lf["axis"]
        sections = []
        for sec in lf["sections"]:
            at = num(sec["at"])
            pts = [(u, v) for u, v in (nums(p, 2) for p in sec["polygon"])]
            if front:
                (at, _) = _front(frame).a(axis, at, at)
                pts = [(_front(frame).cu(axis, a), _front(frame).cv(axis, b)) for a, b in pts]
            sections.append((at, pts))
        return [loft(axis, sections, lf.get("caps", []))]
    if "quad_grid" in shape:
        q = shape["quad_grid"]
        axis = q["axis"]
        at, uc, vc = num(q["at"]), num(q["u_center"]), num(q["v_center"])
        if front:
            uc = _front(frame).cu(axis, uc)
            vc = _front(frame).cv(axis, vc)
            if axis == "y":
                at = _front(frame).y(at)
        return quad_grid(
            axis,
            at,
            int(q.get("facing", 1)),
            uc,
            vc,
            int(q["cols"]),
            int(q["rows"]),
            num(q["pitch"]),
            num(q["size"]),
        )
    raise SpecError(f"unknown shape {shape!r}")


def load_spec(spec_path: str | Path) -> dict[str, Any]:
    spec_path = Path(spec_path)
    spec = json.loads(spec_path.read_text())
    if spec.get("schema") != 1:
        raise SpecError(f"{spec_path}: schema {spec.get('schema')!r}, this builder reads 1")
    validate(spec)
    spec["_dir"] = spec_path.parent
    spec["_path"] = spec_path
    out: dict[str, Any] = spec
    return out


def measurements(spec: dict[str, Any]) -> dict[str, Any] | None:
    rel = spec.get("measurements")
    if not rel:
        return None
    meas: dict[str, Any] = json.loads((spec["_dir"] / rel).read_text())
    return meas


def numeric_frame(spec: dict[str, Any], why: str) -> Frame:
    """The front Frame of a spec whose front_frame is written in numbers."""
    ff = spec.get("front_frame")
    if ff is None or "auto" in (ff.get("left_x"), ff.get("top_y")):
        raise SpecError(f"{why} needs a front_frame written in numbers")
    return Frame(float(num(ff["left_x"])), float(num(ff["top_y"])))


def resolve_volumes(
    spec: dict[str, Any],
) -> dict[str, list[list[float]]]:
    """{name: [box, ...]} in the build frame (a front-frame volume moved there)."""
    out = {}
    for name, vol in spec.get("volumes", {}).items():
        if name == "note":
            continue
        if isinstance(vol, dict):
            if vol.get("frame") != "front":
                raise SpecError(
                    f'volume {name!r}: an object volume is {{"frame": "front", "boxes": [...]}}'
                )
            frame = numeric_frame(spec, f"front-frame volume {name!r}")
            boxes = []
            for b in vol["boxes"]:
                x0, x1, y0, y1, z0, z1 = nums(b, 6)
                (x0, x1), (y0, y1) = _front(frame).xr(x0, x1), _front(frame).yr(y0, y1)
                boxes.append([x0, x1, y0, y1, z0, z1])
            out[name] = boxes
        else:
            out[name] = [nums(b, 6) for b in vol]
    return out


def resolve_frame(
    spec: dict[str, Any], parts: dict[str, trimesh.Trimesh]
) -> tuple[npt.NDArray[np.float64], Frame | None]:
    """center (build-frame mm) and the front Frame, auto values filled in."""

    def union_bounds(
        names: Sequence[str],
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        b = np.array([parts[n].bounds for n in names])
        return b[:, 0].min(axis=0), b[:, 1].max(axis=0)

    c = spec["center_mm"]
    if c == "auto":
        lo, hi = union_bounds(spec["center_from"])
        center = (lo + hi) / 2
    else:
        center = np.array(nums(c, 3))
    ff = spec.get("front_frame")
    frame = None
    if ff is not None:
        left, top = ff["left_x"], ff["top_y"]
        if left == "auto" or top == "auto":
            lo, hi = union_bounds(spec["center_from"])
        left = lo[0] if left == "auto" else num(left)
        top = hi[1] if top == "auto" else num(top)
        frame = Frame(float(left), float(top))
    return center, frame


def pinned_file(unit: dict[str, Any], path: str | Path) -> Path:
    """*path*, refused unless it holds the bytes *unit*'s source pins."""
    src = unit["source"]
    if not Path(path).is_file():
        raise SpecError(f"{path}: no such file (pass it, or --fetch to download {src['url']})")
    digest = sha256_file(path)
    if digest != src["sha256"]:
        raise SpecError(
            f"{path} is not the pinned vendor file (sha256 {digest}, not "
            f"{src['sha256']}); the model's copyright names that file"
        )
    return Path(path)


def module_paths(
    spec: dict[str, Any],
    cache: str | Path = DEFAULT_CACHE,
    fetch: bool = False,
    given: dict[str, str | Path] | None = None,
) -> dict[str, Path]:
    """{module name: its vendor file}: the one *given* names, or the cache's, each checked."""
    given = dict(given or {})
    names = [m["name"] for m in spec.get("modules", [])]
    unknown = sorted(set(given) - set(names))
    if unknown:
        raise SpecError(
            f"--module-source names no module of this spec: {unknown}; it has {names or 'none'}"
        )
    return {
        module["name"]: pinned_file(
            module, given.get(module["name"]) or cached_source(module, cache, fetch)
        )
        for module in spec.get("modules", [])
    }


def face_frames(
    spec: dict[str, Any], frame: Frame | None, meas: dict[str, Any] | None
) -> dict[str, board_faces.FaceFrame]:
    """{face: board_faces.FaceFrame} of every face a drawing of the spec may draw.

    The front's is ``front_frame``. Another face's is the spec's
    ``face_frames`` entry for it, under that face's own keys
    (``board_faces.FACES``); the back, which the front's outline mirrors,
    needs none: its ``right_x`` is the front's ``left_x`` plus the case's
    width in ``measurements.json`` and its ``top_y`` the front's.
    """
    out = {}
    if frame is not None:
        out["front"] = board_faces.FaceFrame("front", frame.x(0.0), frame.y(0.0))
        if meas is not None:
            out["back"] = board_faces.FaceFrame(
                "back", frame.left_x + float(meas["case"]["width"]), frame.top_y
            )
    for face, numbers in (spec.get("face_frames") or {}).items():
        if face == "note":
            continue
        out[face] = board_faces.face_frame(
            face, {k: num(v) for k, v in numbers.items() if k != "note"}
        )
    return out


def build(
    spec: dict[str, Any],
    src_path: str | Path | None,
    out_path: str | Path,
    cache: str | Path = DEFAULT_CACHE,
    with_legends: bool = True,
    modules: Mapping[str, str | Path] | None = None,
    web_ppm: float | None = None,
) -> dict[str, Any]:
    """Build the model of *spec* from the vendor file at *src_path* into
    *out_path*; return a summary dict for source.json.

    *modules* is ``{module name: its vendor file}`` for a spec with
    ``modules`` (``module_paths``, which by default finds them in *cache*).
    With *with_legends* false the ``legends`` meshes are left out: the model
    as it is with nothing printed on it. With *web_ppm*, the largest pixels a
    millimeter the site draws the board at, it is the web level of detail:
    every mesh as the master has it but the legends, which keep only the
    elements whose strokes cover ``WEB_MIN_STROKE_PX`` there, flattened to
    ``WEB_FLATNESS_PX`` where the spec's flatness is finer; a legends mesh
    left with nothing is left out, its plane on record."""
    planar_min_area = num(spec.get("planar_min_area", 1.5))
    quant_mm = num(spec.get("quant_mm", 0.01))

    volumes = resolve_volumes(spec)
    parts: dict[str, trimesh.Trimesh] = {}
    if not own_model(spec):
        if src_path is None:
            raise SpecError(f"{spec['board']}: a model of a vendor file needs that file")
        parts = gather_parts(spec, load_components(spec, src_path, cache), volumes)
    if spec.get("modules"):
        found = module_paths(spec, cache) if modules is None else modules
        for module in spec["modules"]:
            path = found.get(module["name"])
            if path is None:
                raise SpecError(f"module {module['name']!r}: no vendor file given")
            parts.update(
                gather_parts(
                    module, load_components(module, pinned_file(module, path), cache), volumes
                )
            )

    cull = spec.get("cull")
    if cull:
        boxes = cull_boxes(volumes, cull["volumes"])
        report = []
        for name in cull["parts"]:
            parts[name], n = drop_hidden(
                parts[name], boxes, num(cull.get("margin", 0.06)), bool(cull.get("same_box", False))
            )
            report.append(f"{name} {n}")
        print("culled hidden faces: " + ", ".join(report))

    center, frame = resolve_frame(spec, parts)
    meas = measurements(spec)

    g = Glb(spec["node_name"], center, quant_mm)
    # what the model says it is, who made it, its license: the record of the
    # file this build is written as (the master, or its web level of detail)
    meta = media_meta.record(rel(web_path(spec)) if web_ppm is not None else spec["output"])
    asset, packets, scene_name = media_meta.gltf_metadata(meta)
    g.gltf["asset"] = asset
    g.gltf["scenes"][0]["name"] = scene_name

    for m in spec["materials"]:
        rgb = m.get("rgb")
        if rgb is None:
            hx = m["hex"].lstrip("#")
            rgb = [int(hx[i : i + 2], 16) for i in (0, 2, 4)]
        g.material(
            m["name"],
            tuple(int(v) for v in rgb),
            num(m["rough"]),
            metal=num(m.get("metal", 0.0)),
            alpha=None if m.get("alpha") is None else num(m["alpha"]),
            unlit=bool(m.get("unlit", False)),
            double=bool(m.get("double", False)),
        )

    screen: dict[str, Any] | None = None
    if meas is not None and frame is not None:
        d = meas["display"]
        aw, ah = float(d["active_w_mm"]), float(d["active_h_mm"])
        sx0 = frame.x(float(d["origin_x_mm"]))
        sx1 = sx0 + aw
        sy_top = frame.y(float(d["origin_y_mm"]))
        sy_bot = sy_top - ah
        screen = {
            "x0": sx0,
            "x1": sx1,
            "y_top": sy_top,
            "y_bot": sy_bot,
            "w": aw,
            "h": ah,
            "resolution": [int(d["resolution_w_px"]), int(d["resolution_h_px"])],
        }

    def shade(
        name: str, mesh: trimesh.Trimesh, smooth_deg: float | None
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]]:
        if len(mesh.faces) == 0:
            raise SpecError(f"{name}: no faces left (culled or sliced away)")
        if smooth_deg:
            return crease_normals(mesh, smooth_deg, planar_min_area)
        return flat(mesh, planar_min_area)

    def add(
        name: str,
        mesh_or_arrays: trimesh.Trimesh
        | tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]],
        mat: int | None,
        smooth_deg: float | None = None,
        uv: npt.NDArray[np.float64] | None = None,
        extras: dict[str, Any] | None = None,
        quantize: bool = True,
    ) -> None:
        if mat is None:
            raise SpecError(f"{name}: a mesh of no material")
        if isinstance(mesh_or_arrays, trimesh.Trimesh):
            arr = shade(name, mesh_or_arrays, smooth_deg)
            g.mesh(name, [(arr[0], arr[1], arr[2], None, mat)], extras, quantize)
        else:
            pos, nrm, faces = mesh_or_arrays[:3]
            if len(faces) == 0:
                raise SpecError(f"{name}: no faces left (its split gave it none)")
            g.mesh(name, [(pos, nrm, faces, uv, mat)], extras, quantize)

    legends = []
    drawings = {}  # (drawing, flatness) -> (its legends, the faces they were read with)
    drawn: dict[Path, set[str]] = {}  # drawing -> the planes of it some legends mesh draws
    frames = face_frames(spec, frame, meas)
    for entry in spec["meshes"]:
        name = entry["name"]
        if "legends" in entry and not with_legends:
            continue
        mat = None if "legends" in entry else g.mat_index[entry["material"]]
        smooth_deg = num(entry["smooth_deg"]) if entry.get("smooth_deg") else None
        quantize = bool(entry.get("quantize", True))
        if "part" in entry:
            if entry["part"] not in parts:
                continue  # an optional part that matched nothing
            mesh = parts[entry["part"]]
            clips = [(k, i) for i, k in enumerate(("inside", "outside")) if k in entry]
            if clips:
                # shaded whole, then split: each half keeps the part's normals at the seam
                ((clip, keep),) = clips
                half = split_by_boxes(shade(name, mesh, smooth_deg), volumes[entry[clip]], name)[
                    keep
                ]
                add(name, half, mat, smooth_deg=smooth_deg, quantize=quantize)
            else:
                add(name, mesh, mat, smooth_deg=smooth_deg, quantize=quantize)
        elif "screen" in entry:
            if screen is None:
                raise SpecError("a screen needs measurements and front_frame")
            pos, nrm, faces = quad_xy(
                screen["x0"],
                screen["x1"],
                screen["y_bot"],
                screen["y_top"],
                num(entry["screen"]["z"]),
            )
            # glTF UVs: (0,0) = image top-left = the screen's top-left as the
            # user holds the board.
            uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
            add(
                name,
                (pos, nrm, faces),
                mat,
                uv=uv,
                extras={
                    "resolution": screen["resolution"],
                    "activeAreaMm": [screen["w"], screen["h"]],
                    "uv": SCREEN_UV_NOTE,
                },
                quantize=False,
            )
        elif "glass" in entry:
            if screen is None:
                raise SpecError("a glass needs a screen")
            x0, x1, y0, y1 = nums(entry["glass"]["rect"], 4)
            if entry["glass"].get("frame") == "front":
                (x0, x1), (y0, y1) = _front(frame).xr(x0, x1), _front(frame).yr(y0, y1)
            gpos, gnrm, gfaces = quad_xy(x0, x1, y0, y1, num(entry["glass"]["z"]))
            guv = np.column_stack(
                [
                    (gpos[:, 0] - screen["x0"]) / screen["w"],
                    (screen["y_top"] - gpos[:, 1]) / screen["h"],
                ]
            )
            add(name, (gpos, gnrm, gfaces), mat, uv=guv, quantize=False)
        elif "legends" in entry:
            if frame is None:
                raise SpecError(f"{name}: legends need front_frame")
            import legend_mesh  # only a model with legends needs fontTools

            leg = entry["legends"]
            drawing, face = legends_drawing(leg)
            if face not in frames:
                raise SpecError(
                    f"{name}: the {face} face has no frame; give face_frames.{face} "
                    f"({', '.join(board_faces.FACES[face][2])})"
                )
            face_frame = frames[face]
            height = board_faces.height_key(face)
            axis = board_faces.AXES.index(height)
            z = num(leg[height])
            if abs(round((z - center[axis]) / quant_mm) * quant_mm - (z - center[axis])) > 1e-9:
                raise SpecError(f"{name}: {height} {z} is not on the model's {quant_mm} mm grid")
            front = (spec["_dir"] / drawing).resolve()
            flatness = num(leg.get("flatness", 0.004))
            legible: Callable[[BaseGeometry], bool] | None = None
            if web_ppm is not None:
                ppm = web_ppm
                flatness = max(flatness, WEB_FLATNESS_PX / web_ppm)

                def keep_legible(geom: BaseGeometry, ppm: float = ppm) -> bool:
                    return legend_mesh.width_mm(geom) * ppm >= WEB_MIN_STROKE_PX

                legible = keep_legible

            plane = leg.get("plane", legend_mesh.KEYS_PLANE)
            rough = num(leg.get("rough", 0.55))
            try:
                if (front, flatness) not in drawings:
                    faces_read = legend_mesh.Faces()
                    drawings[front, flatness] = (
                        legend_mesh.read_legends(front, flatness, faces_read, legible),
                        faces_read,
                    )
                read, faces_read = drawings[front, flatness]
                sheet_arrays, record = legend_mesh.sheets(
                    read, plane, face_frame, center, z, quant_mm, faces_read
                )
            except legend_mesh.LegendError as exc:
                raise SpecError(f"{name}: {exc}") from None
            if not sheet_arrays and web_ppm is not None and plane in legend_mesh.planes(read):
                # the web level of detail left nothing of this plane to draw
                drawn.setdefault(front, set()).add(plane)
                legends.append(
                    {
                        "mesh": name,
                        "plane": plane,
                        "on": leg["on"],
                        "flatness_mm": flatness,
                        "groups": len(record["groups"]),
                        "shapes": 0,
                        "sheets": [],
                        "dropped": record.get("dropped"),
                    }
                )
                print(f"legends {name}: plane {plane!r}, nothing left at {web_ppm} px/mm")
                continue
            if not sheet_arrays:
                raise SpecError(
                    f"{name}: {drawing} holds no legend group on the plane "
                    f"{plane!r}; it has {legend_mesh.planes(read) or 'none'}"
                )
            drawn.setdefault(front, set()).add(plane)
            for sheet, (fill, pos, nrm, faces, stroke) in zip(
                record["sheets"], sheet_arrays, strict=True
            ):
                ink_name = f"{INK_PREFIX}{fill}"
                known = g.mat_index.get(ink_name)
                if (
                    known is not None
                    and g.gltf["materials"][known]["pbrMetallicRoughness"]["roughnessFactor"]
                    != rough
                ):
                    raise SpecError(
                        f"{name}: the ink #{fill} is already in the model with "
                        f"another rough; one ink is one material"
                    )
                ink = g.material(
                    ink_name, tuple(int(fill[i : i + 2], 16) for i in (0, 2, 4)), rough
                )
                sheet["mesh"] = f"{name}_{fill}"
                add(
                    sheet["mesh"],
                    (pos, nrm, faces),
                    ink,
                    extras={"legends": {"fill": f"#{fill}", "stroke_mm": stroke, "on": leg["on"]}},
                )
            # a front's record keeps the keys it always had; another face's names its face
            placed = (
                {"front": rel(front)} if face == "front" else {"face": face, "drawing": rel(front)}
            )
            legends.append(
                {
                    "mesh": name,
                    "plane": plane,
                    "on": leg["on"],
                    **placed,
                    "legends_sha256": legend_source.digest(front, plane),
                    f"{height}_mm": z,
                    "flatness_mm": flatness,
                    "groups": len(record["groups"]),
                    "keys": record["keys"],
                    "shapes": record["shapes"],
                    "fonts": record["fonts"],
                    "sheets": record["sheets"],
                    **({"dropped": record["dropped"]} if "dropped" in record else {}),
                }
            )
            print(
                f"legends {name}: plane {plane!r}, {len(record['groups'])} groups "
                f"({record['keys']} keys), "
                + ", ".join(
                    f"#{c['fill'][1:]} {c['triangles']} triangles, stroke {c['stroke_mm']:.3f} mm"
                    for c in record["sheets"]
                )
            )
        elif "shapes" in entry:
            solids: list[list[trimesh.Trimesh]] = []
            arrays: list[
                tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.int64]]
            ] = []
            for shape in entry["shapes"]:
                got = shape_meshes(shape, volumes, frame)
                if isinstance(got, tuple):
                    arrays.append(got)
                else:
                    solids.append(got)
            if solids and arrays:
                raise SpecError(f"{name}: solids and quad grids in one mesh")
            if arrays:
                pos = np.vstack([a[0] for a in arrays])
                nrm = np.vstack([a[1] for a in arrays])
                offs = np.cumsum(np.array([0] + [len(a[0]) for a in arrays[:-1]], dtype=np.int64))
                faces = np.vstack([a[2] + o for a, o in zip(arrays, offs, strict=True)])
                add(name, (pos, nrm, faces), mat, quantize=quantize)
            else:
                flat_list = [m for group in solids for m in group]
                mesh = (
                    flat_list[0]
                    if len(flat_list) == 1
                    else _one_mesh(trimesh.util.concatenate(flat_list), name)
                )
                add(name, mesh, mat, smooth_deg=smooth_deg, quantize=quantize)
        else:
            raise SpecError(f"{name}: no part, screen, glass, legends or shapes")

    # every plane a drawing prints on is drawn by some legends mesh
    for (front, _flatness), (read, _faces) in drawings.items():
        missing = [p for p in legend_mesh.planes(read) if p not in drawn[front]]
        if missing:
            raise SpecError(
                f"{rel(front)} prints on the plane(s) {missing}, which no legends "
                f"mesh of this model draws; a print never goes missing quietly"
            )
    if len(g.gltf["materials"]) > MAX_MATERIALS:
        raise SpecError(
            f"{len(g.gltf['materials'])} materials, over the {MAX_MATERIALS} the "
            f"strictest reader has room for (the landing film's shader table "
            f"holds {READER_SLOTS}, and its scene puts {READER_OWN} of its own "
            f"after the model's: the finger, the nail and the cover glass)"
        )

    if any(entry.get("fonts") for entry in legends) and "Inter" not in spec["copyright"]:
        raise SpecError(
            "copyright: the legends are glyphs of Inter, and the credits name no "
            "Inter (its copyright and the SIL Open Font License 1.1)"
        )
    g.gltf["extensionsUsed"].append(media_meta.GLTF_META_EXTENSION)
    g.gltf["extensions"] = packets

    out_path = Path(out_path)
    staged = out_path.with_name(out_path.name + ".part")
    size = g.write(staged)
    clearance = model_raster.screen_clearance(model_raster.read_glb(staged), quant_mm)
    if clearance is not None and not clearance["ok"]:
        staged.unlink()
        side = min(
            ("behind", "in_front"),
            key=lambda s: (clearance[f"{s}_mm"] is None, clearance[f"{s}_mm"]),
        )
        raise SpecError(
            f"screen: the {clearance[f'{side}_mesh']} face nearest the screen "
            f"{'under' if side == 'behind' else 'over'} it is {clearance[f'{side}_mm']:.4f} mm "
            f"off its plane, under one quantization step ({quant_mm} mm), so a depth-tested "
            f"renderer can draw the two at one depth; move the screen or that face"
        )
    written = model_raster.read_glb(staged)
    shared = model_raster.coplanar_overlaps(written, quant_mm)
    if not shared["ok"]:
        staged.unlink()
        listed = "; ".join(
            f"{p['meshes'][0]} and {p['meshes'][1]} ({p['area_mm2']:.3f} mm2 "
            f"facing {p['facing']}, {p['gap_mm']:.4f} mm apart, near "
            f"{p['at_mm']})"
            for p in shared["pairs"][:6]
        )
        more = len(shared["pairs"]) - 6
        raise SpecError(
            f"{len(shared['pairs'])} pair(s) of meshes of different materials cover one place "
            f"at one depth, facing the same way less than one position step ({quant_mm} mm) "
            f"apart, where a depth test keeps either by rounding: {listed}"
            f"{f'; and {more} more' if more > 0 else ''}. Cut one out of the other, start a "
            f"solid where the one under it ends, or lay a layer a whole step over the other"
        )
    for entry in legends:
        if not entry["sheets"]:
            continue  # a plane the web level of detail left empty
        gap = model_raster.legend_clearance(
            written, entry["mesh"] + "_", quant_mm, on=entry["on"], face=entry.get("face", "front")
        )
        if gap is None:
            raise SpecError(f"{entry['mesh']}: no legend mesh of it is in the written model")
        if not gap["ok"]:
            staged.unlink()
            if gap["over_mm"] is not None:
                raise SpecError(
                    f"{entry['mesh']}: a face of {gap['over_mesh']} lies "
                    f"{gap['over_mm']:.4f} mm over a legend and hides it"
                )
            if gap["under_mm"] is None:
                raise SpecError(
                    f"{entry['mesh']}: no face lies under the legends; they are printed on nothing"
                )
            if gap["off"] != 0:
                raise SpecError(
                    f"{entry['mesh']}: {gap['off']} of its {gap['triangles']} "
                    f"triangles have no face of {entry['on']!r} under them; the "
                    f"legends are printed on that mesh, all of them"
                )
            raise SpecError(
                f"{entry['mesh']}: the {gap['under_mesh']} face nearest under a legend is "
                f"{gap['under_mm']:.4f} mm from it, under {gap['least_mm']:g} mm (two "
                f"quantization steps), so a depth-tested renderer can draw the two at one "
                f"depth; raise the legends' z"
            )
        entry["clearance"] = {k: gap[k] for k in ("under_mm", "under_mesh", "least_mm")}
    os.replace(staged, out_path)
    print(
        f"wrote {out_path}: {size} bytes, meshes {len(g.gltf['meshes'])}, "
        f"materials {len(g.gltf['materials'])}, triangles {g.triangles}"
    )
    for entry in (e for e in legends if e["sheets"]):
        print(
            f"{entry['mesh']} clearance: {entry['clearance']['under_mm']:.3f} mm over "
            f"{entry['clearance']['under_mesh']}, nothing over them, every triangle over "
            f"{entry['on']}; at least {entry['clearance']['least_mm']:g} mm"
        )
    if clearance is not None:
        gaps = ", ".join(
            f"{clearance[f'{s}_mm']:.3f} mm {s.replace('_', ' ')} ({clearance[f'{s}_mesh']})"
            for s in ("behind", "in_front")
            if clearance[f"{s}_mm"] is not None
        )
        print(f"screen clearance: {gaps}; at least {quant_mm} mm each")
    return {
        "triangles": g.triangles,
        "meshes": len(g.gltf["meshes"]),
        "materials": len(g.gltf["materials"]),
        "center_mm": [float(v) for v in center],
        "front_frame": None if frame is None else {"left_x": frame.left_x, "top_y": frame.top_y},
        # the frames of the other faces a drawing was read on, for the checks
        "face_frames": {e["face"]: frames[e["face"]].record() for e in legends if "face" in e},
        "screen": screen,
        "legends": legends,
    }


# ---------------------------------------------------------------- outputs


def package_versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in PINNED:
        try:
            out[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            out[name] = None
    return out


def rel(path: str | Path) -> str:
    path = Path(path)
    path = Path(path).resolve()
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()


def without_legends_record(data: bytes) -> dict[str, Any]:
    """What a model weighs with its legend meshes taken out (``glb_legends.strip``)."""
    bare = glb_legends.strip(data)
    js, _ = glb_legends.read(bare)
    return {
        "bytes": len(bare),
        "gzip_bytes": len(gzip.compress(bare, compresslevel=9, mtime=0)),
        "sha256": hashlib.sha256(bare).hexdigest(),
        "meshes": len(js["meshes"]),
        "materials": len(js["materials"]),
    }


SOURCE_KEYS = (
    "vendor",
    "format",
    "url",
    "repository",
    "path",
    "commit",
    "sha256",
    "bytes",
    "license",
    "copyright",
    "license_note",
)


def source_json(
    spec: dict[str, Any],
    out_path: str | Path,
    summary: dict[str, Any],
    obj: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The provenance record written beside a board's model.

    A spec with ``modules`` records each module's vendor file and transform
    under ``modules``; a spec whose legends lie on another face than the front
    records that face's frame under ``parameters.face_frames``. A spec with
    neither writes the record it always wrote. *obj*, the record of the OBJ
    and MTL written from a board's master (``export_obj.record``), goes last,
    under ``obj``."""
    data = Path(out_path).read_bytes()
    src = spec["source"]
    printed = (
        {"legends": summary["legends"], "without_legends": without_legends_record(data)}
        if summary.get("legends")
        else {}
    )
    stacked = (
        {
            "modules": [
                {
                    "name": m["name"],
                    "source": {k: m["source"][k] for k in SOURCE_KEYS if k in m["source"]},
                    "tessellation": m.get("tessellation"),
                    "transform": m.get("transform", []),
                }
                for m in spec["modules"]
            ]
        }
        if spec.get("modules")
        else {}
    )
    faces = {"face_frames": summary["face_frames"]} if summary.get("face_frames") else {}
    return {
        "board": spec["board"],
        "model": rel(out_path),
        "model_sha256": hashlib.sha256(data).hexdigest(),
        "model_bytes": len(data),
        "model_gzip_bytes": len(gzip.compress(data, compresslevel=9, mtime=0)),
        "triangles": summary["triangles"],
        "meshes": summary["meshes"],
        "materials": summary["materials"],
        "source": (
            {k: src[k] for k in ("format", "license", "copyright", "license_note") if k in src}
            if own_model(spec)
            else {k: src[k] for k in SOURCE_KEYS if k in src}
        ),
        **stacked,
        "builder": {
            "script": rel(Path(__file__)),
            "version": BUILDER_VERSION,
            "spec": rel(spec["_path"]),
            "spec_sha256": sha256_file(spec["_path"]),
            "python": platform.python_version(),
            "packages": package_versions(),
        },
        "parameters": {
            "quant_mm": num(spec.get("quant_mm", 0.01)),
            "planar_min_area_mm2": num(spec.get("planar_min_area", 1.5)),
            "tessellation": spec.get("tessellation"),
            "transform": spec.get("transform", []),
            "center_mm": summary["center_mm"],
            "front_frame": summary["front_frame"],
            **faces,
            "screen": None
            if summary["screen"] is None
            else {
                k: (round(v, 4) if isinstance(v, float) else v)
                for k, v in summary["screen"].items()
            },
        },
        **printed,
        **({"obj": obj} if obj else {}),
    }


def web_path(spec: dict[str, Any]) -> Path:
    """Where a board's web level of detail is written: beside its spec, named after its model."""
    return Path(spec["_dir"]) / f"{Path(spec['output']).stem}-web.glb"


def web_json(
    spec: dict[str, Any], out_path: str | Path, summary: dict[str, Any], ppm: float
) -> dict[str, Any]:
    """The record of a board's web level of detail, written beside its spec as ``web.json``.

    It names the master it was built beside (its path and bytes, as the
    master's ``source.json`` records them), the scale it was built for and the
    two rules, and, for each legends mesh, what was kept and what left out.
    """
    data = Path(out_path).read_bytes()
    master = REPO / spec["output"]
    return {
        "board": spec["board"],
        "level": "web",
        "model": rel(out_path),
        "model_sha256": hashlib.sha256(data).hexdigest(),
        "model_bytes": len(data),
        "model_gzip_bytes": len(gzip.compress(data, compresslevel=9, mtime=0)),
        "triangles": summary["triangles"],
        "meshes": summary["meshes"],
        "materials": summary["materials"],
        "master": {"model": spec["output"], "model_sha256": sha256_file(master)},
        "px_per_mm": ppm,
        "min_stroke_px": WEB_MIN_STROKE_PX,
        "flatness_px": WEB_FLATNESS_PX,
        "builder": {
            "script": rel(Path(__file__)),
            "version": BUILDER_VERSION,
            "spec": rel(spec["_path"]),
            "spec_sha256": sha256_file(spec["_path"]),
        },
        "legends": [
            {
                k: entry[k]
                for k in ("mesh", "plane", "flatness_mm", "groups", "shapes", "sheets", "dropped")
                if entry.get(k) is not None
            }
            for entry in summary["legends"]
        ],
    }


def describe_glb(path: str | Path) -> tuple[dict[str, Any], dict[str, npt.NDArray[np.float64]]]:
    """(json, {mesh name: positions in mm}) of a GLB this builder wrote."""
    raw = Path(path).read_bytes()
    jlen = struct.unpack_from("<I", raw, 12)[0]
    js = json.loads(raw[20 : 20 + jlen])
    bin_ = raw[20 + jlen + 8 :]
    comp = {
        5120: np.int8,
        5121: np.uint8,
        5122: np.int16,
        5123: np.uint16,
        5125: np.uint32,
        5126: np.float32,
    }
    out = {}
    for node in js["nodes"][1:]:
        mesh = js["meshes"][node["mesh"]]
        acc = js["accessors"][mesh["primitives"][0]["attributes"]["POSITION"]]
        bv = js["bufferViews"][acc["bufferView"]]
        dt = np.dtype(comp[acc["componentType"]])
        stride = bv.get("byteStride", 3 * dt.itemsize) // dt.itemsize
        arr = np.frombuffer(
            bin_, dtype=dt, count=acc["count"] * stride, offset=bv["byteOffset"]
        ).reshape(-1, stride)[:, :3]
        scale = node.get("scale", [1.0, 1.0, 1.0])
        out[node["name"]] = arr.astype(float) * np.array(scale) / MM
    return js, out


def compare_glb(built: str | Path, reference: str | Path, tolerance_mm: float) -> bool:
    """True when *built* matches *reference*: the same bytes, or (with a
    tolerance) the same meshes with every position within it."""
    a, b = Path(built).read_bytes(), Path(reference).read_bytes()
    if a == b:
        print(
            f"PASS: {built} is byte-identical to {reference} "
            f"(sha256 {hashlib.sha256(a).hexdigest()})"
        )
        return True
    print(f"DIFFER: {len(a)} bytes against {len(b)}")
    ja, pa = describe_glb(built)
    jb, pb = describe_glb(reference)
    ok = list(pa) == list(pb)
    if not ok:
        print(f"  meshes differ: {list(pa)} against {list(pb)}")
    for name in pa:
        if name not in pb:
            continue
        if pa[name].shape != pb[name].shape:
            print(f"  {name}: {len(pa[name])} vertices against {len(pb[name])}")
            ok = False
            continue
        dev = float(np.abs(pa[name] - pb[name]).max()) if len(pa[name]) else 0.0
        if dev > 0:
            print(f"  {name}: max position deviation {dev:.4f} mm")
        ok = ok and dev <= tolerance_mm
    if ja.get("materials") != jb.get("materials"):
        print("  materials differ")
        ok = False
    print(("PASS" if ok and tolerance_mm > 0 else "FAIL") + f" (tolerance {tolerance_mm} mm)")
    return ok and tolerance_mm > 0


def main(argv: list[str] | None = None) -> int:
    """Build a board model from the command line; return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("spec", type=Path, help="<board>/model/spec.json")
    parser.add_argument("--source", type=Path, help="the vendor file (default: from the cache)")
    parser.add_argument(
        "--module-source",
        action="append",
        default=[],
        metavar="NAME=FILE",
        help="a module's vendor file (default: from the cache); once a module",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=DEFAULT_CACHE,
        help=f"vendor-file cache (default {DEFAULT_CACHE}, or $KLEIDOS_CAD_CACHE)",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="download the vendor file into the cache when it is missing",
    )
    parser.add_argument("--out", type=Path, help="the .glb to write (default: the spec's output)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="build into a temporary file and compare it with the spec's output",
    )
    parser.add_argument(
        "--tolerance-mm",
        type=float,
        default=0.0,
        help="with --check: accept a rebuild whose positions differ by at most "
        "this much (default 0: the same bytes)",
    )
    parser.add_argument(
        "--no-source-json",
        action="store_true",
        help="do not write source.json beside the spec (it is written only "
        "for the spec's own output)",
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="with --check: when the rebuild is byte-identical to the spec's "
        "output, write its source.json",
    )
    parser.add_argument(
        "--without-legends",
        action="store_true",
        help="build the model with no legends mesh: with --out, write that "
        "lighter model; with --check, compare it with the spec's output "
        "less its legend meshes (never writes source.json)",
    )
    parser.add_argument(
        "--web-px-per-mm",
        type=float,
        metavar="PPM",
        help="build the web level of detail for a board the site draws at "
        "most PPM pixels a millimeter (the Kleidos repository's node "
        "site/tools/build-web-model.mjs "
        "--scales prints each board's): write <model>-web.glb and web.json "
        "beside the spec, or with --check compare it with them",
    )
    args = parser.parse_args(argv)
    if args.web_px_per_mm is not None and (
        args.without_legends or args.record or args.out or args.no_source_json
    ):
        parser.error(
            "--web-px-per-mm writes the web level of detail and its record, and takes "
            "only --check besides the vendor files"
        )
    if args.web_px_per_mm is not None and not args.web_px_per_mm > 0:
        parser.error("--web-px-per-mm takes a scale over 0")
    if args.without_legends and not (args.check or args.out):
        parser.error(
            "--without-legends needs --out (the spec's output is the whole model) or --check"
        )
    if args.without_legends and args.record:
        parser.error("--record is for the whole model")

    try:
        spec = load_spec(args.spec)
        if own_model(spec):
            if args.source:
                parser.error("--source: this spec builds from no vendor file (format none)")
            src_path = None
        else:
            src_path = args.source or cached_source(spec, args.cache, args.fetch)
        if src_path is None:
            pass
        elif not Path(src_path).is_file():
            print(
                f"FAILED: {src_path}: no such file (pass --source, or --fetch to download "
                f"{spec['source']['url']})",
                file=sys.stderr,
            )
            return 1
        elif sha256_file(src_path) != spec["source"]["sha256"]:
            digest = sha256_file(src_path)
            print(
                f"FAILED: {src_path} is not the pinned vendor file (sha256 {digest}, not "
                f"{spec['source']['sha256']}); the model's copyright names that file",
                file=sys.stderr,
            )
            return 1
        given: dict[str, str | Path] = {}
        for item in args.module_source:
            name, sep, path = item.partition("=")
            if not sep or not name or not path:
                parser.error(f"--module-source {item!r}: give NAME=FILE")
            given[name] = Path(path)
        modules = module_paths(spec, args.cache, args.fetch, given)
        target = REPO / spec["output"]

        def record(model: str | Path, summary: dict[str, Any]) -> None:
            # a board's master is also written as OBJ and MTL, from the GLB itself
            obj = (
                export_obj.write(model, spec["board"])
                if export_obj.applies(spec["output"])
                else None
            )
            data = source_json(spec, model, summary, obj)
            dest = spec["_dir"] / "source.json"
            dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
            print(f"wrote {rel(dest)}: gzip {data['model_gzip_bytes']} bytes")
            if obj:
                print(f"wrote {obj['obj']} ({obj['obj_bytes']} bytes) and {obj['mtl']}")

        if args.web_px_per_mm is not None:
            ppm = args.web_px_per_mm
            web = web_path(spec)
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / web.name
                summary = build(spec, src_path, out, args.cache, modules=modules, web_ppm=ppm)
                if args.check:
                    return 0 if compare_glb(out, web, 0.0) else 1
                shutil.copyfile(out, web)
            data = web_json(spec, web, summary, ppm)
            (spec["_dir"] / "web.json").write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n"
            )
            print(
                f"wrote {rel(web)} and its web.json: {data['model_bytes']} bytes, "
                f"{data['triangles']} triangles"
            )
            return 0
        if args.check:
            reference = args.out or target
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / target.name
                if args.without_legends:
                    # the model built with nothing printed on it, against the
                    # whole model less its legend meshes
                    stripped = Path(tmp) / f"{target.stem}-stripped.glb"
                    stripped.write_bytes(glb_legends.strip(Path(reference).read_bytes()))
                    build(spec, src_path, out, args.cache, with_legends=False, modules=modules)
                    return 0 if compare_glb(out, stripped, 0.0) else 1
                summary = build(spec, src_path, out, args.cache, modules=modules)
                same = compare_glb(out, reference, args.tolerance_mm)
                identical = Path(out).read_bytes() == Path(reference).read_bytes()
            if identical and args.record and Path(reference).resolve() == target.resolve():
                record(target, summary)
            return 0 if same else 1
        out = args.out or target
        if args.without_legends and Path(out).resolve() == target.resolve():
            print(
                f"FAILED: {out} is the spec's output, the whole model; give the lighter "
                f"one another name",
                file=sys.stderr,
            )
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        summary = build(
            spec, src_path, out, args.cache, with_legends=not args.without_legends, modules=modules
        )
        if args.no_source_json or args.without_legends:
            pass
        elif Path(out).resolve() == target.resolve():
            record(out, summary)
        else:
            print(f"source.json not written: {out} is not the spec's output {spec['output']}")
    except SpecError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
