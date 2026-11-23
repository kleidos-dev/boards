# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""What a board prints is in its model, where its drawing prints it, and can be left out.

A board model holds no image, so the legends a board prints (its keys', its
stickers', the marks on its plates) are flat meshes of their own, built from
the ``<g class="legend">`` groups of the board's ``svg/front.svg`` and from
nothing typed a second time (``_shared``: ``legend_mesh.py``,
``build_board_glb.py``). Every reader of a model draws
them with no change, and a reader that shows the board too small to print on
leaves them out (``glb_legends.py``). This pins what those readers count on,
on the models as committed:

- a front that prints anything has a legends mesh for each surface it prints
  on, and the model was built from the spec as it is now and from what the
  drawing prints now: its legend groups and what places them, so a front
  changed anywhere else leaves its model as built, and one changed there
  does not;
- ``_legends_<rrggbb>`` at the end of a node's name finds the legend meshes
  and nothing else; each is one flat primitive facing the viewer, in its
  ink's own material, and says how thin its print is and which mesh it is
  printed on;
- the model without them is the rest of it byte for byte, and is the file
  ``source.json`` weighs;
- the legends lie three position steps over the faces under them, on the mesh
  they are printed on, and the check that says so fails a model where they do
  not;
- the checks read a model as a glTF reader draws it, each mesh where its node
  and the nodes above it place it, so a legend moved by a node's translation
  is a legend moved;
- in none of the nine models do two meshes of different materials cover one
  place at one depth, facing the same way less than a position step apart,
  where a depth test keeps either by rounding, and the check that holds this
  fails a model where it is planted;
- the Cardputer's two slanted grounds are the drawing's;
- every legend of the drawing is in the model within two position steps of
  where it is drawn, by a check that is itself tested against planted
  defects;
- and the four CAD libraries those checks read a drawing and a model with are
  pinned in ``requirements.txt`` at the versions the models were built
  with. Where one is missing the tests that need it skip and say what to
  install; in CI, which installs the pins, they fail instead, so a run cannot
  be green having held no legend to its drawing.

What the Kleidos site's renderer needs from a model (its material table,
its depth buffer) is held by the Kleidos repository's own tests.

Host-only: no build, no hardware, no network.
"""

from __future__ import annotations

import ast
import gzip
import hashlib
import importlib
import importlib.metadata
import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

import numpy.typing as npt
import pytest

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT
SHARED = ROOT / "_shared"
sys.path.insert(0, str(SHARED))
import board_faces  # noqa: E402  after the sys.path set-up above
import glb_legends  # noqa: E402  after the sys.path set-up above
import legend_source  # noqa: E402  after the sys.path set-up above
import media_meta  # noqa: E402  after the sys.path set-up above

if TYPE_CHECKING:
    import model_raster

#: Every test here reads a board model; the checkers' planted-defect selftests and
#: the fixture rebuild are ``selftest`` too (``tests/conftest.py``).
pytestmark = pytest.mark.models

SVG_NS = "http://www.w3.org/2000/svg"
#: The nine boards, and the legends meshes each model carries as
#: {mesh: (the drawing's plane, the mesh it is printed on, its inks)}. A plane
#: of the front's drawing is its name; a plane of another face's drawing is
#: ``<face>:<plane>`` (``back:label``).
BOARDS: dict[str, dict[str, tuple[str, str, set[str]]]] = {
    "sticks3": {
        "label_legends": (
            "back:label",
            "back_label",
            {
                "0283cc",
                "111113",
                "116d3c",
                "1d903f",
                "336594",
                "3a3a3a",
                "5b155d",
                "5d320b",
                "6464fc",
                "679667",
                "940606",
                "aed9ea",
                "b3b3b3",
                "bb3c68",
                "c88764",
                "cbcbcb",
                "cf3101",
                "e4e4e3",
                "ed6b96",
                "ee9c99",
                "f20461",
                "f86514",
                "fb6761",
                "fd98fc",
                "fdcd03",
                "ffffff",
            },
        ),
        "strip_legends": ("left:strip", "side_strip", {"0283cc", "ffffff"}),
    },
    "m5stickc-plus1": {
        "label_legends": (
            "back:label",
            "back_label",
            {
                "003f5f",
                "0d4f82",
                "111111",
                "118cd0",
                "1d95da",
                "309963",
                "3a3a3a",
                "3d6e8f",
                "5f5b58",
                "7ad7ed",
                "858585",
                "8a3a3a",
                "9da09e",
                "b0402a",
                "bcca9d",
                "c33161",
                "c48c4f",
                "c8320a",
                "cbcbc9",
                "e20e63",
                "e64824",
                "e6e7e7",
                "e8642f",
                "ef6968",
                "fa6665",
                "fcce0f",
                "ffffff",
            },
        ),
    },
    "m5stickc-plus2": {
        "label_legends": (
            "back:label",
            "back_label",
            {
                "01304d",
                "049a40",
                "0594de",
                "0a4c80",
                "141413",
                "3c7fb4",
                "4a4a48",
                "63d3e7",
                "a5ae85",
                "b8262b",
                "bd813e",
                "c1c2bf",
                "c8300a",
                "cd1457",
                "dadcd9",
                "e3551d",
                "ec5957",
                "ecc205",
                "eeeeea",
                "f0a247",
            },
        ),
    },
    "m5stickc-plus-se": {
        "label_legends": (
            "back:label",
            "back_label",
            {
                "008dd5",
                "03639b",
                "04a3e4",
                "141414",
                "1f74ad",
                "302e2c",
                "309965",
                "5c5c5c",
                "5f605f",
                "7bdaf5",
                "7c2a33",
                "7f807f",
                "9a5a06",
                "a0a0a0",
                "bac89b",
                "c78d52",
                "cbcbca",
                "cd3203",
                "e6e6e6",
                "e74924",
                "f3f4f3",
                "f80464",
                "f8622f",
                "fb6662",
                "fcce02",
                "fcfcfa",
                "fd8c26",
            },
        ),
    },
    "coreink": {
        "label_legends": (
            "back:label",
            "back_label",
            {
                "125d94",
                "141414",
                "18acd2",
                "20974a",
                "4f8fbf",
                "555553",
                "7a7a7a",
                "8e4e4d",
                "980404",
                "993263",
                "a3a3a3",
                "c6c6c6",
                "c71214",
                "cc3263",
                "cdcdcd",
                "cf3205",
                "d77c97",
                "e4e5e5",
                "f06a3c",
                "f1075e",
                "f66662",
                "fbcd12",
                "fcfe0e",
                "ffffff",
            },
        ),
        "side_legends": ("left:side", "side_label", {"141414", "18acd2"}),
    },
    "cores3-se": {
        "label_legends": ("top:rating", "top_label", {"111111", "969696"}),
        "port_tag_legends": (
            "top:port-tag",
            "base_port_tag",
            {"111111", "1a7fc0", "a9a49e", "dbdcdb"},
        ),
    },
    "m5stack-core2-v13": {
        "back_legends": (
            "back:sticker",
            "back_label",
            {
                "019630",
                "0870b8",
                "0cadd4",
                "141414",
                "2f3300",
                "2f6765",
                "37cc35",
                "555555",
                "650163",
                "8e9191",
                "9a0202",
                "a6dcf4",
                "c62e60",
                "c91518",
                "c9673f",
                "c9cbca",
                "d03101",
                "f06b10",
                "f59d3a",
                "fcccc9",
                "fd6460",
                "fdcf06",
                "ffffff",
            },
        ),
        "label_legends": ("top:rating", "label", {"141414", "555555", "8e9191", "c9cbca"}),
    },
    "cardputer": {
        "key_legends": ("keys", "legend_strips", {"111113", "2e6db0", "ff6633", "ffffff"}),
        "panel_legends": ("panel", "sticker", {"111113", "14c8ee", "1a1a1c", "ff6633"}),
        "stamp_legends": (
            "stamp",
            "stamp_label",
            {
                "06302d",
                "111113",
                "14c8ee",
                "2176ae",
                "2e6db0",
                "2f97cc",
                "44c294",
                "6f706e",
                "78a3f2",
                "9a1a96",
                "a8585c",
                "bcbcb9",
                "cbcb4a",
                "d2390c",
                "dfdfdc",
                "e22c34",
                "ea8f8d",
                "ee2f80",
                "f3a0ec",
                "f6cbc6",
                "f6e08a",
                "f8cf1d",
                "ff6633",
                "ffffff",
            },
        ),
        "back_legends": (
            "back:label",
            "back_label",
            {
                "111113",
                "14c8ee",
                "2176ae",
                "2f97cc",
                "44c294",
                "505050",
                "6f706e",
                "78a3f2",
                "9a1a96",
                "a6e2fb",
                "a7ac8f",
                "bcbcb9",
                "cbcb4a",
                "d2390c",
                "dfdfdc",
                "e22c34",
                "ea8f8d",
                "ee2f80",
                "f8cf1d",
                "fc659b",
                "ff6633",
                "ffffff",
            },
        ),
        "top_legends": (
            "top:strip",
            "top_label",
            {"111113", "2f97cc", "e22c34", "ea8f8d", "ee2f80", "ff6633", "ffffff"},
        ),
        "side_legends": (
            "left:side",
            "side_label",
            {"111113", "d2390c", "dfdfdc", "f8cf1d", "ffffff"},
        ),
    },
    "tdeck-plus": {
        "glass_legends": ("glass", "face", {"cfd2d8"}),
        "key_legends": ("keys", "keys", {"f2f3f5"}),
        "plate_legends": ("plate", "keyboard_plate", {"bcbfc5", "dcdde2", "e9eaed"}),
        "plate_mark_legends": ("plate-marks", "keyboard_plate", {"2f3033", "dcdde2"}),
        "frame_legends": ("back:frame", "case_shell", {"767b7f"}),
        "frame_line_legends": ("back:frame-line", "case_shell", {"767b7f"}),
        "badge_legends": ("back:badge", "case_shell", {"767b7f"}),
        "base_legends": ("back:base", "case_shell", {"767b7f"}),
    },
}
PRINTING = [board for board, meshes in BOARDS.items() if meshes]
#: The boards whose front prints: a plane of the front's drawing is bare
#: (``plane_key``). What changes a back's or a side's drawing is held on the
#: fixture's back (``legend_placement.py --selftest``), and a printing back's
#: own drawing by the back tests here too.
FRONT_PRINTING = [
    board
    for board, meshes in BOARDS.items()
    if any(":" not in plane for plane, _on, _inks in meshes.values())
]
#: The boards whose back prints: their records digest each back plane.
PRINTING_BACK = [
    board
    for board, meshes in BOARDS.items()
    if any(plane.startswith("back:") for plane, _on, _inks in meshes.values())
]
#: How many position steps a legends mesh lies over the highest face under it:
#: three, but for the T-Deck Plus's round marks, which keep the height of the
#: plate's print around them (three steps over the trackball's band) and lie
#: on the plate itself, five steps lower.
STEPS_OVER = 3
STEPS_OVER_ITS_OWN = {("tdeck-plus", "plate_mark_legends"): 8}
#: The CAD libraries the model checks read a drawing and a model with, as
#: {the module: the distribution ``requirements.txt`` pins it as}. The pins
#: are the model builder's (``build_board_glb.py``), which each model's
#: ``source.json`` records.
CAD_LIBRARIES = {
    "numpy": "numpy",
    "shapely": "shapely",
    "mapbox_earcut": "mapbox_earcut",
    "fontTools": "fonttools",
}
QA_REQUIREMENTS = ROOT / "requirements.txt"
#: What installs the checks' stack, the CAD libraries among it.
QA_INSTALL = "pip install -r requirements.txt"


# --- Helpers ---------------------------------------------------------------------


def builder_numbers() -> dict[str, int]:
    """The whole numbers ``build_board_glb.py`` names at its top level.

    Read from its source, because importing the builder needs every CAD
    library it pins. A value is a literal or a sum or difference of names
    already read (``MAX_MATERIALS = READER_SLOTS - READER_OWN``).
    """

    def value(node: ast.expr, known: dict[str, int]) -> int | None:
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.Name):
            return known.get(node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Sub):
            left, right = value(node.left, known), value(node.right, known)
            if left is None or right is None:
                return None
            return left + right if isinstance(node.op, ast.Add) else left - right
        return None

    known: dict[str, int] = {}
    tree = ast.parse((SHARED / "build_board_glb.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            got = value(node.value, known)
            if got is not None:
                known[node.targets[0].id] = got
    return known


def pins(path: Path) -> dict[str, str]:
    """{distribution: version} of every ``name==version`` line of a requirements file.

    Names are compared as pip compares them: lower case, with ``-`` and ``.``
    read as ``_``.
    """
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s#;]+)", line)
        if match:
            found[re.sub(r"[-.]", "_", match.group(1).lower())] = match.group(2)
    return found


def cad_library(module: str) -> ModuleType:
    """A CAD library ``requirements.txt`` pins, imported, at the version it is pinned at.

    Where it is missing, or installed at another version, the test skips and
    says what to install. In CI (``CI`` set, as GitHub Actions sets it) the
    workflow has installed the pins, so the same thing is a failure: a job
    that skips these tests is green having checked nothing, which is worse
    than not having them.
    """
    distribution = CAD_LIBRARIES[module]
    pinned = pins(QA_REQUIREMENTS)[distribution]
    try:
        library = importlib.import_module(module)
        installed = importlib.metadata.version(distribution)
        short = (
            None
            if installed == pinned
            else (f"{distribution} {installed} is installed, requirements.txt pins {pinned}")
        )
    except ImportError:
        library, short = None, f"{distribution} is not installed"
    if short is None and library is not None:
        return library
    reason = (
        f"{short}: the board-model checks read a drawing and a model with the CAD "
        f"libraries requirements.txt pins ({QA_INSTALL})"
    )
    if os.environ.get("CI"):
        pytest.fail(
            f"{reason}; in CI the pins are installed, so this is a broken install "
            "and not a reason to skip"
        )
    pytest.skip(reason)


def record(board: str) -> dict[str, Any]:
    """A board's ``model/source.json``."""
    loaded: dict[str, Any] = json.loads(
        (CAD / board / "model" / "source.json").read_text(encoding="utf-8")
    )
    return loaded


def spec(board: str) -> dict[str, Any]:
    """A board's ``model/spec.json``."""
    loaded: dict[str, Any] = json.loads(
        (CAD / board / "model" / "spec.json").read_text(encoding="utf-8")
    )
    return loaded


def model_bytes(board: str) -> bytes:
    """The bytes of a board's committed model."""
    return (ROOT / str(record(board)["model"])).read_bytes()


def drawing_of(entry: dict[str, Any]) -> str:
    """The drawing a legends record was read from: ``front`` on the front, ``drawing`` elsewhere."""
    return str(entry.get("drawing") or entry["front"])


def plane_key(face: str, plane: str) -> str:
    """How a plane is named across a board's drawings: bare on the front, ``face:plane`` else."""
    return plane if face == "front" else f"{face}:{plane}"


def stale_planes(board: str, front: Path | None = None, face: str = "front") -> list[str]:
    """The planes of a board's model that its drawing no longer prints as built.

    Each legends mesh's record holds the digest of what the mesh read from the
    drawing (``legend_source.digest``); *front* stands in for the committed
    drawing of *face*.
    """
    return [
        entry["plane"]
        for entry in record(board)["legends"]
        if legend_source.digest(
            front if front and entry.get("face", "front") == face else ROOT / drawing_of(entry),
            entry["plane"],
        )
        != entry["legends_sha256"]
    ]


def changed_front(
    board: str, change: Callable[..., Any], tmp_path: Path, face: str = "front"
) -> Path:
    """A copy of a board's front drawing (or *face*'s) with *change* made to its parsed tree.

    *change* takes the root element and a map from each element to the one
    it lies in. The copy is written by another serializer than the
    generator's, which by itself changes nothing a model reads.
    """
    tree = ET.parse(CAD / board / "svg" / f"{face}.svg")  # noqa: S314  (this repository's own file)
    root = tree.getroot()
    change(root, {child: parent for parent in root.iter() for child in parent})
    out = tmp_path / f"{board}-{face}.svg"
    tree.write(out, encoding="utf-8", xml_declaration=True)
    return out


def _clearance(
    meshes: list[model_raster.Mesh], prefix: str, step: float, **where: Any
) -> dict[str, Any]:
    """``model_raster.legend_clearance`` of a model that has the legends to measure."""
    import model_raster

    found: dict[str, Any] | None = model_raster.legend_clearance(meshes, prefix, step, **where)
    assert found is not None, prefix
    return found


def legend_groups(root: ET.Element) -> list[ET.Element]:
    """A drawing's legend groups, in its order."""
    return [el for el in root.iter(f"{{{SVG_NS}}}g") if "legend" in (el.get("class") or "").split()]


def planes_of_front(board: str) -> dict[str, int]:
    """{plane: how many legend groups} of a board's drawings: one a face it draws.

    A plane of another face's drawing is named ``<face>:<plane>`` (``plane_key``).
    """
    planes: dict[str, int] = {}
    for face in board_faces.FACES:
        path = CAD / board / "svg" / f"{face}.svg"
        if not path.is_file():
            continue
        root = ET.fromstring(path.read_text(encoding="utf-8"))  # noqa: S314  (this repository's own file)
        for group in root.iter(f"{{{SVG_NS}}}g"):
            if "legend" in (group.get("class") or "").split():
                plane = plane_key(face, group.get("data-plane", "keys"))
                planes[plane] = planes.get(plane, 0) + 1
    return planes


def node_bytes(js: dict[str, Any], bin_: bytes) -> dict[str, tuple[Any, ...]]:
    """{node name: everything its mesh draws}, the accessors as their own bytes."""

    def data(index: int) -> tuple[Any, ...]:
        accessor = js["accessors"][index]
        view = js["bufferViews"][accessor["bufferView"]]
        start = view.get("byteOffset", 0)
        described = {k: v for k, v in accessor.items() if k != "bufferView"}
        return (
            json.dumps(described, sort_keys=True),
            view.get("byteStride"),
            view.get("target"),
            bin_[start : start + view["byteLength"]],
        )

    out = {}
    for node in js["nodes"]:
        if "mesh" not in node:
            continue
        mesh = js["meshes"][node["mesh"]]
        prims: list[tuple[Any, ...]] = []
        prims.extend(
            (
                tuple((name, data(index)) for name, index in sorted(prim["attributes"].items())),
                data(prim["indices"]),
                json.dumps(js["materials"][prim["material"]], sort_keys=True),
            )
            for prim in mesh["primitives"]
        )
        described = {k: v for k, v in node.items() if k != "mesh"}
        out[node["name"]] = (json.dumps(described, sort_keys=True), mesh["name"], tuple(prims))
    return out


def srgb(linear: float) -> int:
    """A linear channel as its sRGB byte."""
    value = linear * 12.92 if linear <= 0.0031308 else 1.055 * linear ** (1 / 2.4) - 0.055
    return round(value * 255)


# --- The drawing and the model agree on what is printed --------------------------


@pytest.mark.parametrize("board", sorted(BOARDS))
def test_a_model_draws_every_plane_its_front_prints_on(board: str) -> None:
    """A print in the drawing is a legends mesh in the spec and in the record.

    The builder refuses a model that leaves out a plane of a drawing it reads;
    this holds the other half, a front that gains its first legend group while
    its spec still reads no drawing at all.
    """
    planes = planes_of_front(board)
    declared = {
        plane_key(
            entry["legends"].get("face", "front"), entry["legends"].get("plane", "keys")
        ): entry
        for entry in spec(board)["meshes"]
        if "legends" in entry
    }
    recorded = {
        plane_key(entry.get("face", "front"), entry["plane"]): entry
        for entry in record(board).get("legends", [])
    }
    expected = {plane: mesh for mesh, (plane, _on, _inks) in BOARDS[board].items()}
    assert set(planes) == set(declared) == set(recorded) == set(expected), board
    for plane, mesh in expected.items():
        assert declared[plane]["name"] == mesh == recorded[plane]["mesh"]
        assert declared[plane]["name"].endswith("legends")
        assert recorded[plane]["groups"] == planes[plane], (board, plane)
        assert recorded[plane]["on"] == declared[plane]["legends"]["on"] == BOARDS[board][mesh][1]


@pytest.mark.parametrize("board", PRINTING)
def test_the_model_was_built_from_the_drawing_and_the_spec_as_they_are(board: str) -> None:
    """A legend or a spec edited after the build is a model that no longer shows it."""
    rec = record(board)
    data = model_bytes(board)
    assert hashlib.sha256(data).hexdigest() == rec["model_sha256"]
    assert len(data) == rec["model_bytes"]
    spec_path = ROOT / rec["builder"]["spec"]
    assert hashlib.sha256(spec_path.read_bytes()).hexdigest() == rec["builder"]["spec_sha256"], (
        f"{spec_path.name} changed since {rec['model']} was built: rebuild the model"
    )
    assert stale_planes(board) == [], (
        f"what {drawing_of(rec['legends'][0])} prints on these planes changed since "
        f"{rec['model']} was built: rebuild the model"
    )
    for entry in rec["legends"]:
        assert "front_sha256" not in entry, "the whole drawing's digest is no longer recorded"
        for font, digest in entry["fonts"].items():
            assert hashlib.sha256((ROOT / font).read_bytes()).hexdigest() == digest, font


# --- What a model reads from its drawing, and what it does not --------------------


def _by_id(root: ET.Element, name: str) -> ET.Element:
    (found,) = [el for el in root.iter() if el.get("id") == name]
    return found


def _nothing(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> None:
    """The drawing as it is, written by another serializer."""


def _a_new_callout(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> None:
    ET.SubElement(
        _by_id(root, "annotations"), f"{{{SVG_NS}}}text", {"x": "0", "y": "0", "font-size": "2"}
    ).text = "new"


def _a_new_hotspot(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> None:
    ET.SubElement(
        _by_id(root, "hotspots"),
        f"{{{SVG_NS}}}circle",
        {"id": "hs-Planted", "cx": "1", "cy": "1", "r": "1", "data-face": "front"},
    )


def _the_screen_marker_moved(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> None:
    glass = _by_id(root, "screen-active")
    glass.set("x", str(float(glass.get("x", "0")) + 3.0))


def _every_cap_repainted_and_moved(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> None:
    printed = {el for group in legend_groups(root) for el in group.iter()}
    caps = [el for el in root.iter(f"{{{SVG_NS}}}rect") if el not in printed and el.get("fill")]
    assert len(caps) > 20
    for cap in caps:
        cap.set("fill", "#123456")
        cap.set("x", str(float(cap.get("x", "0")) + 0.4))


def _other_margins(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> None:
    root.set("viewBox", "-20 -20 200 200")
    root.set("width", "200mm")
    root.set("data-generator", "another")


#: What regenerating a front changes when its legends did not: nothing a model reads.
OUTSIDE = (
    _nothing,
    _a_new_callout,
    _a_new_hotspot,
    _the_screen_marker_moved,
    _every_cap_repainted_and_moved,
    _other_margins,
)


@pytest.mark.parametrize("board", FRONT_PRINTING)
@pytest.mark.parametrize("change", OUTSIDE, ids=lambda change: change.__name__.strip("_"))
def test_a_front_changed_outside_its_legends_leaves_its_model_as_built(
    board: str, change: Callable[..., Any], tmp_path: Path
) -> None:
    """A new callout, a hotspot, a cap or the screen marker is no reason to rebuild a model.

    The record digests what the model reads from the drawing, not the file.
    With the whole file's digest, any regeneration of a front failed this
    suite until its model was rebuilt from the vendor's CAD file.
    """
    record(board)
    front = changed_front(board, change, tmp_path)
    (tmp_path / "rewritten").mkdir()
    rewritten = changed_front(board, _nothing, tmp_path / "rewritten")
    assert rewritten.read_bytes() != (CAD / board / "svg" / "front.svg").read_bytes()
    assert (front.read_bytes() == rewritten.read_bytes()) == (change is _nothing), (
        "the change did not change the drawing"
    )
    assert stale_planes(board, front) == []


def _first_key(root: ET.Element) -> ET.Element:
    return next(group for group in legend_groups(root) if group.get("data-key"))


def _a_character_changed(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> set[str]:
    text = next(
        el
        for group in legend_groups(root)
        if group.get("data-key")
        for el in group.iter(f"{{{SVG_NS}}}text")
    )
    text.text = "W" if text.text != "W" else "V"
    return {"keys"}


def _a_legend_moved(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> set[str]:
    child = _first_key(root)[0]
    child.set("transform", "translate(0.05 0)")
    return {"keys"}


def _an_ink_changed(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> set[str]:
    child = next(el for el in _first_key(root).iter() if el.get("fill", "none") != "none")
    child.set("fill", "#ff0000")
    return {"keys"}


def _shapes_in_a_legend(root: ET.Element, differing: bool = False) -> tuple[ET.Element, ET.Element]:
    """The first legend group holding an element of two or more shapes (the
    group itself, or a group inside it), and that element."""
    return next(
        (group, el)
        for group in legend_groups(root)
        for el in group.iter()
        if len(el) > 1 and (not differing or ET.tostring(el[0]) != ET.tostring(el[1]))
    )


def _a_shape_taken_out(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> set[str]:
    group, shapes = _shapes_in_a_legend(root)
    shapes.remove(shapes[0])
    return {legend_source.plane_of(group)}


def _two_shapes_painted_in_the_other_order(
    root: ET.Element, parents: dict[ET.Element, ET.Element]
) -> set[str]:
    group, shapes = _shapes_in_a_legend(root, differing=True)
    first = shapes[0]
    shapes.remove(first)
    shapes.insert(1, first)
    return {legend_source.plane_of(group)}


def _two_groups_painted_in_the_other_order(
    root: ET.Element, parents: dict[ET.Element, ET.Element]
) -> set[str]:
    first, second = [g for g in legend_groups(root) if g.get("data-key")][:2]
    parent = parents[first]
    assert parents[second] is parent
    at_first, at_second = list(parent).index(first), list(parent).index(second)
    parent.remove(second)
    parent.remove(first)
    parent.insert(at_first, second)
    parent.insert(at_second, first)
    return {"keys"}


def _a_group_moved_to_another_plane(
    root: ET.Element, parents: dict[ET.Element, ET.Element]
) -> set[str]:
    _first_key(root).set("data-plane", "lid")
    return {"keys"}


def _a_new_group(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> set[str]:
    group = ET.SubElement(root, f"{{{SVG_NS}}}g", {"class": "legend", "data-key": "planted"})
    ET.SubElement(
        group,
        f"{{{SVG_NS}}}rect",
        {"x": "1", "y": "1", "width": "1", "height": "1", "fill": "#111113"},
    )
    return {"keys"}


def _a_transform_around_a_group(
    root: ET.Element, parents: dict[ET.Element, ET.Element]
) -> set[str]:
    group = _first_key(root)
    parent = parents[group]
    at = list(parent).index(group)
    parent.remove(group)
    around = ET.Element(f"{{{SVG_NS}}}g", {"transform": "translate(0.05 0)"})
    around.append(group)
    parent.insert(at, around)
    return {"keys"}


def _another_family_handed_down(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> None:
    root.set("font-family", "Helvetica, Arial, sans-serif")


#: What a model reads from its drawing: each of these is a model to rebuild. A
#: change returns the planes it touches, or None for all of them.
INSIDE = (
    _a_character_changed,
    _a_legend_moved,
    _an_ink_changed,
    _a_shape_taken_out,
    _two_shapes_painted_in_the_other_order,
    _two_groups_painted_in_the_other_order,
    _a_group_moved_to_another_plane,
    _a_new_group,
    _a_transform_around_a_group,
    _another_family_handed_down,
)


@pytest.mark.parametrize("board", FRONT_PRINTING)
@pytest.mark.parametrize("change", INSIDE, ids=lambda change: change.__name__.strip("_"))
def test_a_front_changed_inside_its_legends_is_a_model_to_rebuild(
    board: str, change: Callable[..., Any], tmp_path: Path
) -> None:
    """A legend's characters, place, ink or paint order, or what places its group.

    Each change is caught on the plane it touches and on no other, so the
    record says which legends mesh no longer shows its drawing.
    """
    record(board)
    touched: list[set[str] | None] = []
    front = changed_front(
        board, lambda root, parents: touched.append(change(root, parents)), tmp_path
    )
    (tmp_path / "rewritten").mkdir()
    rewritten = changed_front(board, _nothing, tmp_path / "rewritten")
    assert front.read_bytes() != rewritten.read_bytes(), "the change did not change the drawing"
    every = {
        entry["plane"]
        for entry in record(board)["legends"]
        if entry.get("face", "front") == "front"
    }
    expected = every if touched[0] is None else touched[0] & every
    assert expected, "the change touches no plane this model draws"
    assert set(stale_planes(board, front)) == expected


def changed_back(board: str, change: Callable[..., Any], tmp_path: Path) -> Path:
    """A copy of a board's back drawing with *change* made to its parsed tree."""
    tree = ET.parse(CAD / board / "svg" / "back.svg")  # noqa: S314  (this repository's own file)
    root = tree.getroot()
    change(root, {child: parent for parent in root.iter() for child in parent})
    out = tmp_path / f"{board}-back.svg"
    tree.write(out, encoding="utf-8", xml_declaration=True)
    return out


def stale_back_planes(board: str, back: Path) -> list[str]:
    """The back planes of a board's model that *back* no longer prints as built."""
    return [
        entry["plane"]
        for entry in record(board)["legends"]
        if entry.get("face") == "back"
        and legend_source.digest(back, entry["plane"]) != entry["legends_sha256"]
    ]


def _a_mark_inked_otherwise(root: ET.Element, parents: dict[ET.Element, ET.Element]) -> set[str]:
    group = legend_groups(root)[0]
    child = next(el for el in group.iter() if el.get("fill", "none") != "none")
    child.set("fill", "#ff0000")
    return {legend_source.plane_of(group)}


@pytest.mark.parametrize("board", PRINTING_BACK)
@pytest.mark.parametrize(
    "change", (_nothing, _a_new_callout), ids=lambda change: change.__name__.strip("_")
)
def test_a_back_changed_outside_its_legends_leaves_its_model_as_built(
    board: str, change: Callable[..., Any], tmp_path: Path
) -> None:
    """The back's record digests its prints, not the file: a callout is no reason to rebuild."""
    assert stale_back_planes(board, changed_back(board, change, tmp_path)) == []


@pytest.mark.parametrize("board", PRINTING_BACK)
@pytest.mark.parametrize(
    "change",
    (
        _a_shape_taken_out,
        _two_shapes_painted_in_the_other_order,
        _a_mark_inked_otherwise,
        _another_family_handed_down,
    ),
    ids=lambda change: change.__name__.strip("_"),
)
def test_a_back_changed_inside_its_legends_is_a_model_to_rebuild(
    board: str, change: Callable[..., Any], tmp_path: Path
) -> None:
    """A back print taken out, repainted, reordered or set in another face: caught on its plane."""
    touched: list[set[str] | None] = []
    back = changed_back(
        board, lambda root, parents: touched.append(change(root, parents)), tmp_path
    )
    every = {entry["plane"] for entry in record(board)["legends"] if entry.get("face") == "back"}
    expected = every if touched[0] is None else touched[0] & every
    assert expected, "the change touches no back plane this model draws"
    assert set(stale_back_planes(board, back)) == expected


# --- What a reader counts on -----------------------------------------------------


@pytest.mark.parametrize("board", sorted(BOARDS))
def test_the_legend_meshes_are_named_and_described_as_the_contract_says(board: str) -> None:
    """The name finds them, and each says its ink, how thin it is and what it is printed on."""
    js, _ = glb_legends.read(model_bytes(board))
    assert "images" not in js and "textures" not in js, "a model holds no image"
    assert len(js["materials"]) <= builder_numbers()["MAX_MATERIALS"]
    found = glb_legends.legends(js)
    names = {node["name"] for node in js["nodes"] if "mesh" in node}
    expected = {
        f"{mesh}_{ink}": (mesh, on)
        for mesh, (_plane, on, inks) in BOARDS[board].items()
        for ink in inks
    }
    assert {entry["name"] for entry in found} == set(expected), board
    recorded = {
        sheet["mesh"]: sheet
        for entry in record(board).get("legends", [])
        for sheet in entry["sheets"]
    }
    assert set(recorded) == set(expected)
    for entry in found:
        mesh, on = expected[entry["name"]]
        ink = entry["name"].rsplit("_", 1)[1]
        node = js["nodes"][entry["node"]]
        prims = js["meshes"][node["mesh"]]["primitives"]
        # the web model's cutter reads a mesh's first primitive and no other
        assert len(prims) == 1, entry["name"]
        assert entry["fill"] == f"#{ink}" == recorded[entry["name"]]["fill"]
        assert entry["on"] == on and on in names and not glb_legends.is_legend(on)
        assert isinstance(entry["stroke_mm"], float) and entry["stroke_mm"] > 0
        assert entry["stroke_mm"] == recorded[entry["name"]]["stroke_mm"]
        assert entry["triangles"] == recorded[entry["name"]]["triangles"]
        material = js["materials"][prims[0]["material"]]
        assert material["name"] == f"{glb_legends.INK_PREFIX}{ink}" == entry["material"]
        assert "alphaMode" not in material, "ink is opaque"
        color = material["pbrMetallicRoughness"]["baseColorFactor"]
        assert "".join(f"{srgb(c):02x}" for c in color[:3]) == ink and color[3] == 1.0
    legend_names = {entry["name"] for entry in found}
    for node in js["nodes"]:
        if "mesh" not in node or node["name"] in legend_names:
            continue
        assert not node["name"].endswith("legends"), node["name"]
        for prim in js["meshes"][node["mesh"]]["primitives"]:
            assert not js["materials"][prim["material"]]["name"].startswith(
                glb_legends.INK_PREFIX
            ), f"{node['name']} wears an ink"


def test_a_name_is_a_legend_meshs_only_when_it_ends_as_one() -> None:
    """The colored grounds under the Cardputer's legends are not legends."""
    assert glb_legends.is_legend("key_legends_111113")
    assert glb_legends.is_legend("panel_legends_ff6633")
    for name in (
        "legend_orange",
        "legend_strips",
        "key_legends",
        "key_legends_11111",
        "key_legends_1111134",
        "key_legends_GGGGGG",
        "legends_111113_top",
        "",
    ):
        assert not glb_legends.is_legend(name), name


# --- The model without its legends -----------------------------------------------


@pytest.mark.parametrize("board", sorted(BOARDS))
def test_a_model_without_its_legends_is_the_rest_of_it_byte_for_byte(board: str) -> None:
    """Leaving the legends out changes nothing else, and is the file the record weighs.

    ``build_board_glb.py --check --without-legends`` holds the same bytes to a
    build from the vendor file with no legends mesh at all; that needs the
    vendor file and the CAD libraries, so it is run where a model is rebuilt.
    """
    data = model_bytes(board)
    bare = glb_legends.strip(data)
    if not BOARDS[board]:
        assert bare == data, "a model that prints nothing is left as it is"
        assert "without_legends" not in record(board)
        return
    js, bin_ = glb_legends.read(data)
    bare_js, bare_bin = glb_legends.read(bare)
    magic, version, total = struct.unpack_from("<III", bare, 0)
    assert (magic, version, total) == (glb_legends.GLB_MAGIC, 2, len(bare))
    assert glb_legends.legends(bare_js) == []
    assert not [m for m in bare_js["materials"] if m["name"].startswith(glb_legends.INK_PREFIX)]
    whole, left = node_bytes(js, bin_), node_bytes(bare_js, bare_bin)
    assert list(left) == [name for name in whole if not glb_legends.is_legend(name)]
    for name, drawn in left.items():
        assert drawn == whole[name], f"{name} changed when the legends were left out"
    assert bare_js["asset"] == js["asset"]
    assert bare_js.get("extensionsRequired") == js.get("extensionsRequired")
    assert len(bare_bin) == bare_js["buffers"][0]["byteLength"]
    assert sum(view["byteLength"] for view in bare_js["bufferViews"]) <= len(bare_bin)
    # every index the rewritten JSON holds points at something
    root = bare_js["nodes"][bare_js["scenes"][0]["nodes"][0]]
    assert sorted(root["children"]) == list(range(1, len(bare_js["nodes"])))
    assert glb_legends.strip(bare) == bare
    # its gzip size is the build machine's zlib's, so it is held loosely
    weighed = record(board)["without_legends"]
    assert weighed["sha256"] == hashlib.sha256(bare).hexdigest(), "source.json weighs another file"
    assert weighed["bytes"] == len(bare) < len(data)
    assert (
        weighed["meshes"]
        == len(bare_js["meshes"])
        == len(js["meshes"]) - len(glb_legends.legends(js))
    )
    assert weighed["materials"] == len(bare_js["materials"])
    packed = len(gzip.compress(bare, compresslevel=9, mtime=0))
    assert abs(weighed["gzip_bytes"] - packed) <= packed // 50


def test_a_reader_leaves_out_only_the_legends_too_thin_to_draw() -> None:
    """A stroke under a pixel is speckle; a chunky mark still reads.

    The rule is the builder's: a legend mesh goes when its ``stroke_mm`` times
    the pixels a millimeter is under 1 with 4x multisampling, or under 1.5
    with none.
    """
    assert glb_legends.too_thin(0.305, 3.2) and not glb_legends.too_thin(0.305, 3.3)
    assert glb_legends.too_thin(0.305, 4.9, antialias=False)
    assert not glb_legends.too_thin(0.305, 5.0, antialias=False)
    data = model_bytes("tdeck-plus")
    js, bin_ = glb_legends.read(data)
    # the board 73 px wide: a pixel a millimeter
    cut = glb_legends.strip(data, lambda entry: glb_legends.too_thin(entry["stroke_mm"], 1.0))
    cut_js, cut_bin = glb_legends.read(cut)
    kept = [entry["name"] for entry in glb_legends.legends(cut_js)]
    assert kept == ["plate_legends_bcbfc5", "frame_legends_767b7f"], (
        "only the chevrons and the back's large T-DECK are over a pixel thick"
    )
    whole, left = node_bytes(js, bin_), node_bytes(cut_js, cut_bin)
    for name, drawn in left.items():
        assert drawn == whole[name], name
    assert [
        m["name"] for m in cut_js["materials"] if m["name"].startswith(glb_legends.INK_PREFIX)
    ] == ["ink_bcbfc5", "ink_767b7f"]
    # the board 183 px wide, multisampled: the hairlines go, and with them the
    # rings of the two round marks, but not the marks' 2 mm discs, which are
    # meshes of their own that say how thin they are, not how thin the traces are;
    # the back's name, badge and wordmark, each on a plane of its own, stay;
    # the 0.3 mm outline round the name goes with the hairlines
    cut = glb_legends.strip(data, lambda entry: glb_legends.too_thin(entry["stroke_mm"], 2.5))
    cut_js, cut_bin = glb_legends.read(cut)
    assert [entry["name"] for entry in glb_legends.legends(cut_js)] == [
        "plate_legends_bcbfc5",
        "plate_mark_legends_dcdde2",
        "frame_legends_767b7f",
        "badge_legends_767b7f",
        "base_legends_767b7f",
    ]
    left = node_bytes(cut_js, cut_bin)
    assert left["plate_mark_legends_dcdde2"] == whole["plate_mark_legends_dcdde2"]
    strokes = {entry["name"]: entry["stroke_mm"] for entry in glb_legends.legends(js)}
    assert strokes["plate_mark_legends_dcdde2"] > 1.5 * strokes["plate_legends_dcdde2"]
    # drawn large, nothing goes and the file is the model itself
    assert (
        glb_legends.strip(data, lambda entry: glb_legends.too_thin(entry["stroke_mm"], 20.0))
        == data
    )


# --- Two levels of detail: the master and the web's ------------------------------


def web_record(board: str) -> dict[str, Any]:
    """A board's ``model/web.json``: the record of its web level of detail."""
    loaded: dict[str, Any] = json.loads(
        (CAD / board / "model" / "web.json").read_text(encoding="utf-8")
    )
    return loaded


def builder_float(name: str) -> float:
    """A number ``build_board_glb.py`` names at its top level, read from its source."""
    tree = ast.parse((SHARED / "build_board_glb.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == name
            and isinstance(node.value, ast.Constant)
        ):
            value = node.value.value
            if isinstance(value, (int, float)):
                return float(value)
    raise AssertionError(f"build_board_glb.py names no number {name}")


def content(data: bytes) -> bytes:
    """A model less its own metadata (each file's record names that file), laid out as the builder's
    are."""
    js, bin_ = glb_legends.read(data)
    return glb_legends.write(media_meta.gltf_without_metadata(js), bin_)


@pytest.mark.parametrize("board", sorted(BOARDS))
def test_a_board_has_two_levels_of_detail_the_master_and_the_webs(board: str) -> None:
    """The master keeps every print; the web's is the master with only the prints a reader sees.

    The master (``source.json``) is what the videos draw: every print of the
    drawings. The web level (``web.json``, ``<board>-web.glb``) is built by
    the same builder from the same spec with ``--web-px-per-mm``, the largest
    scale the site draws the board at (the Kleidos repository's
    ``site/tools/build-web-model.mjs --scales``), and is what the site's web model is cut from. It
    was built
    beside the master as it is, under the builder's two rules (a print whose
    strokes cover fewer than ``WEB_MIN_STROKE_PX`` pixels at that scale is
    left out, curves flattened to ``WEB_FLATNESS_PX`` there); less its prints
    it is the master less its prints, byte for byte once each file's own
    metadata (its title and address) is set aside; and it holds no ink, no
    print mesh and no triangle of print the master does not.
    """
    web, master_record = web_record(board), record(board)
    assert web["level"] == "web" and web["board"] == board
    assert web["master"] == {
        "model": master_record["model"],
        "model_sha256": master_record["model_sha256"],
    }, "the web level was built beside another master: build it again"
    assert web["model"] == f"{board}/model/{board}-web.glb"
    lighter = (ROOT / web["model"]).read_bytes()
    assert hashlib.sha256(lighter).hexdigest() == web["model_sha256"]
    assert len(lighter) == web["model_bytes"]
    assert web["min_stroke_px"] == builder_float("WEB_MIN_STROKE_PX") == 1.5
    assert web["flatness_px"] == builder_float("WEB_FLATNESS_PX") == 0.25
    assert web["px_per_mm"] > 0
    master = model_bytes(board)
    assert content(glb_legends.strip(lighter)) == content(glb_legends.strip(master)), (
        "the web level differs from its master in more than its prints"
    )
    js, _ = glb_legends.read(master)
    web_js, _ = glb_legends.read(lighter)
    kept, whole = glb_legends.legends(web_js), glb_legends.legends(js)
    assert {e["name"] for e in kept} <= {e["name"] for e in whole}
    inks = {m["name"] for m in js["materials"] if m["name"].startswith(glb_legends.INK_PREFIX)}
    assert {
        m["name"] for m in web_js["materials"] if m["name"].startswith(glb_legends.INK_PREFIX)
    } <= inks
    assert sum(e["triangles"] for e in kept) <= sum(e["triangles"] for e in whole)
    assert web["triangles"] <= master_record["triangles"]


def test_the_web_level_drops_the_prints_its_rule_says_and_keeps_the_rest() -> None:
    """The web rule reads a print's strokes, whatever its shape; a web level says what it left.

    ``legend_mesh.width_mm`` is the shorter side of the rectangle of a
    polygon's area and outline: a stroke's width whatever its length, a dot's
    or a square's side, about 0.79 of a disc's diameter; an element's width is
    its polygons' weighed by area. The Cardputer ADV's StampS3A label, whose
    micro-print is the finest the fleet carries, is where the web level leaves
    most out, and its record says so; a board none of whose prints is that
    thin at its scale leaves nothing out.
    """
    shapely = cad_library("shapely")
    import legend_mesh

    box = shapely.geometry.box
    assert legend_mesh.width_mm(box(0, 0, 0.1, 10)) == pytest.approx(0.1, rel=1e-6)
    assert legend_mesh.width_mm(box(0, 0, 0.3, 0.3)) == pytest.approx(0.3, rel=1e-6)
    disc = shapely.geometry.Point(0, 0).buffer(0.5, quad_segs=64)
    assert legend_mesh.width_mm(disc) == pytest.approx(0.785, abs=0.01)
    ring = box(0, 0, 4, 4).difference(box(0.2, 0.2, 3.8, 3.8))
    assert legend_mesh.width_mm(ring) == pytest.approx(0.2, rel=0.05)
    two = shapely.geometry.MultiPolygon([box(0, 0, 0.1, 5), box(1, 0, 1.4, 0.4)])
    assert 0.1 < legend_mesh.width_mm(two) < 0.4
    dropped = {
        entry["mesh"]: entry.get("dropped", {}).get("shapes", 0)
        for entry in web_record("cardputer")["legends"]
    }
    assert dropped["stamp_legends"] > 100, "the StampS3A's micro-print is the web level's to leave"
    assert all(not entry.get("dropped") for entry in web_record("tdeck-plus")["legends"])


# --- The legends lie where a depth test keeps them -------------------------------


@pytest.mark.parametrize("board", PRINTING)
def test_the_legends_lie_three_steps_over_the_mesh_they_are_printed_on(board: str) -> None:
    """Flat, facing the viewer, three position steps up, with nothing over them.

    Three steps over the highest face under a legends mesh (``STEPS_OVER``; the
    one mesh that lies higher is named in ``STEPS_OVER_ITS_OWN``, with why).

    The planted defects are the two a spec can make: a height one step over
    the face under a legend, where a depth buffer starts drawing that face
    through it, and a legend moved off the mesh it is printed on.
    """
    np = cad_library("numpy")
    import dataclasses

    import model_raster

    rec = record(board)
    step = rec["parameters"]["quant_mm"]
    meshes = model_raster.read_glb(ROOT / rec["model"])
    for entry in rec["legends"]:
        prefix = entry["mesh"] + "_"
        face = entry.get("face", "front")
        axis, sign = board_faces.normal(face)
        key = board_faces.AXES[axis]
        sheets = [m for m in meshes if m.name.startswith(prefix)]
        assert sheets
        for sheet in sheets:
            height = entry[f"{key}_mm"] - rec["parameters"]["center_mm"][axis]
            assert np.allclose(sheet.positions[:, axis], height, atol=1e-6), sheet.name
            assert np.allclose(sheet.normals, board_faces.basis(face)[2], atol=1e-6), sheet.name
        gap = _clearance(meshes, prefix, step, on=entry["on"], face=face)
        assert gap["ok"] and gap["off"] == 0 and gap["over_mm"] is None, (board, entry["mesh"])
        steps = STEPS_OVER_ITS_OWN.get((board, entry["mesh"]), STEPS_OVER)
        assert gap["under_mm"] == pytest.approx(steps * step, abs=1e-6), (board, entry["mesh"])
        assert entry["clearance"]["under_mm"] == pytest.approx(gap["under_mm"], abs=1e-6)

        def moved(
            across: float = 0.0, down: float = 0.0, prefix: str = prefix, face: str = face
        ) -> list[Any]:
            # along the face's u and in along its normal, in the build frame
            shift = across * board_faces.basis(face)[0] - down * board_faces.basis(face)[2]
            return [
                dataclasses.replace(m, positions=m.positions + shift)
                if m.name.startswith(prefix)
                else m
                for m in meshes
            ]

        low = _clearance(moved(down=(steps - 1) * step), prefix, step, on=entry["on"], face=face)
        assert not low["ok"] and low["under_mm"] == pytest.approx(step, abs=1e-6)
        off = _clearance(moved(across=200.0), prefix, step, on=entry["on"], face=face)
        assert not off["ok"] and off["off"] == off["triangles"]


# --- The checks read a model as a glTF reader draws it ---------------------------


def test_the_model_reader_places_a_mesh_where_its_nodes_place_it(tmp_path: Path) -> None:
    """A node's translation, rotation, scale or matrix moves its mesh, and so does its parent's.

    The builder gives a mesh node a scale and nothing else, and the checks
    once read only that: a legend moved 0.06 mm by its node's translation
    passed every one of them, where any reader of the model drew it moved.
    """
    np = cad_library("numpy")
    import model_raster

    data = model_bytes("cardputer")
    plain = {mesh.name: mesh for mesh in model_raster.read_glb(ROOT / record("cardputer")["model"])}
    legend = glb_legends.legends(glb_legends.read(data)[0])[0]["name"]

    def read(change: Callable[..., Any]) -> dict[str, Any]:
        js, bin_ = glb_legends.read(data)
        change(
            js,
            next(node for node in js["nodes"] if node.get("name") == legend),
            js["nodes"][js["scenes"][0]["nodes"][0]],
        )
        path = tmp_path / "planted.glb"
        path.write_bytes(glb_legends.write(js, bin_))
        return {mesh.name: mesh for mesh in model_raster.read_glb(path)}

    def moved(got: dict[str, Any], name: str) -> npt.NDArray[Any]:
        moved_by: npt.NDArray[Any] = got[name].positions - plain[name].positions
        return moved_by

    # the legend's own node, 0.06 mm across: that mesh moves and no other
    got = read(lambda js, node, root: node.update(translation=[0.06e-3, 0.0, 0.0]))
    assert np.allclose(moved(got, legend), [0.06, 0.0, 0.0], atol=1e-9)
    assert all(
        np.array_equal(mesh.positions, plain[name].positions)
        for name, mesh in got.items()
        if name != legend
    )
    # the root, up and out: every mesh moves, its normals as they were
    got = read(lambda js, node, root: root.update(translation=[0.0, 1e-3, 2e-3]))
    assert all(np.allclose(moved(got, name), [0.0, 1.0, 2.0], atol=1e-9) for name in plain)
    assert np.allclose(got[legend].normals, plain[legend].normals, atol=1e-12)
    # the root turned a quarter about +Z: x goes to y, y to -x, and the normals turn with it
    half = 0.5**0.5
    got = read(lambda js, node, root: root.update(rotation=[0.0, 0.0, half, half]))
    was = plain["screen"]
    assert np.allclose(got["screen"].positions[:, 0], -was.positions[:, 1], atol=1e-9)
    assert np.allclose(got["screen"].positions[:, 1], was.positions[:, 0], atol=1e-9)
    assert np.allclose(got[legend].normals, [0.0, 0.0, 1.0], atol=1e-9)
    side = next(mesh for mesh in plain.values() if abs(mesh.normals[:, 0]).max() > 0.9)
    assert np.allclose(got[side.name].normals[:, 1], side.normals[:, 0], atol=1e-6)
    # the same turn and a shift written as a matrix (stored by columns) read the same
    turned = read(
        lambda js, node, root: root.update(
            rotation=[0.0, 0.0, half, half], translation=[1e-3, 0.0, 0.0]
        )
    )
    as_matrix = read(
        lambda js, node, root: root.update(
            matrix=[
                0.0,
                1.0,
                0.0,
                0.0,
                -1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                1e-3,
                0.0,
                0.0,
                1.0,
            ]
        )
    )
    assert all(
        np.allclose(as_matrix[name].positions, turned[name].positions, atol=1e-9) for name in plain
    )
    # a node's own scale twice over: its mesh twice as large, about the origin
    got = read(lambda js, node, root: node.update(scale=[v * 2 for v in node["scale"]]))
    assert np.allclose(got[legend].positions, plain[legend].positions * 2, atol=1e-9)


# --- No two materials at one depth -----------------------------------------------


@pytest.mark.parametrize("board", sorted(BOARDS))
def test_no_two_materials_cover_one_place_at_one_depth(board: str) -> None:
    """No two meshes of different materials overlap, facing one way, on one plane.

    Two such faces draw the same pixels at the same depth, and a depth test
    keeps one or the other by rounding: the T-Deck Plus's round marks, a light
    dot and the dark disc under it at one height in an earlier model,
    came out a dark pinwheel on a CPU rasterizer and a light disc on a GPU.
    One position step apart is a plane of its own (sized in the next test);
    nearer, on the grid or off it, is the same plane (``model_raster``:
    ``coplanar_overlaps``, which the builder also runs on what it writes).
    """
    cad_library("numpy")
    import model_raster

    rec = record(board)
    got = model_raster.coplanar_overlaps(
        model_raster.read_glb(ROOT / rec["model"]), rec["parameters"]["quant_mm"]
    )
    assert got["ok"], [(pair["meshes"], pair["facing"], pair["area_mm2"]) for pair in got["pairs"]]


@pytest.mark.selftest
def test_the_depth_check_catches_what_is_planted() -> None:
    """A check that passes everything checks nothing: each planted tie fails it.

    The two printing models pass as committed; each tie planted in them is
    found and named (a print on its face, a solid on another's top, a print
    half a step up off the grid, a block's sides on its strip's, a node's
    translation in the file, a double-sided material over the face it rests
    on), and a print a whole step up passes.
    """
    cad_library("numpy")
    import model_raster

    clean, results, controls = model_raster.coplanar_selftest(CAD)
    for board, got in clean.items():
        assert got["ok"], (board, got["pairs"])
    assert len(results) >= 6
    for what, caught, how in results:
        assert caught, f"{what}: {how}"
    planted = " | ".join(what for what, _caught, _how in results)
    for words in (
        "an earlier model lay",
        "off the grid",
        "its sides on the strip's",
        "in the file",
        "double-sided",
    ):
        assert words in planted, f"the selftest no longer plants: {words}"
    assert controls
    for what, passed, how in controls:
        assert passed, f"{what}: {how}"


# --- The grounds under two of the Cardputer's legends ----------------------------


def test_the_cardputers_slanted_grounds_are_the_drawings() -> None:
    """The flag under ``esc`` and the split under ``del`` keep the drawing's corners.

    The colored blocks are solids of the spec, typed there in the drawing's
    numbers. These two are not rectangles: the flag's four corners are the
    drawing's own, and ``del``'s two halves meet along the drawing's diagonal,
    each ending at the model's strip above and below.
    """
    front = (CAD / "cardputer" / "svg" / "front.svg").read_text(encoding="utf-8")
    drawn: dict[str, list[list[tuple[float, ...]]]] = {}
    for points, fill in re.findall(r'<polygon points="([^"]+)" fill="(#[0-9a-f]{6})"/>', front):
        corners = [tuple(float(v) for v in pair.split(",")) for pair in points.split()]
        drawn.setdefault(fill, []).append(corners)
    grounds = {
        entry["name"]: [
            shape["prism"]["profile"]["polygon"]
            for shape in entry["shapes"]
            if "polygon" in shape["prism"]["profile"]
        ]
        for entry in spec("cardputer")["meshes"]
        if entry["name"] in ("legend_orange", "legend_black")
    }
    flag, upper = ([tuple(corner) for corner in poly] for poly in grounds["legend_orange"])
    (lower,) = ([tuple(corner) for corner in poly] for poly in grounds["legend_black"])
    assert flag in drawn["#ff6633"], "the esc flag is not the drawing's polygon"
    drawn_upper = next(p for p in drawn["#ff6633"] if (76.98, 22.27) in p)
    drawn_lower = next(p for p in drawn["#111113"] if (76.98, 22.27) in p and len(p) == 4)
    diagonal = {(76.98, 22.27), (81.7, 24.14)}
    assert diagonal <= set(upper) & set(lower) & set(drawn_upper) & set(drawn_lower)
    # off the diagonal, each half keeps the drawing's sides and ends at the model's strip
    for half, drawn_half in ((upper, drawn_upper), (lower, drawn_lower)):
        assert {x for x, _ in half} == {x for x, _ in drawn_half} == {76.98, 81.7}
        (edge,) = {y for _, y in set(half) - diagonal}
        (drawn_edge,) = {y for _, y in set(drawn_half) - diagonal}
        assert abs(edge - drawn_edge) <= 0.3, "a strip edge far from the drawing's"


# --- Every legend, where the drawing prints it (with the CAD libraries) ----------


def placement_module() -> ModuleType:
    """``legend_placement``, with the four CAD libraries it reads through (``cad_library``)."""
    for module in CAD_LIBRARIES:
        cad_library(module)
    import legend_placement

    return legend_placement


def test_the_check_stack_installs_the_pinned_libraries() -> None:
    """CI installs the checks' stack from ``requirements.txt``, every CAD library pinned.

    ``legend_placement.py`` and ``model_raster.py`` read through numpy,
    shapely, mapbox_earcut and fontTools; an unpinned one would let CI read
    a drawing with another version than the models were built with. Needs no
    library itself, so it runs wherever the suite does.
    """
    required = pins(QA_REQUIREMENTS)
    for distribution in CAD_LIBRARIES.values():
        assert distribution in required, f"requirements.txt does not pin {distribution}"
    install = (ROOT / ".github" / "workflows" / "check.yml").read_text(encoding="utf-8")
    assert f"run: {QA_INSTALL}" in install, (
        "the check job no longer installs the stack from requirements.txt"
    )


@pytest.mark.parametrize("board", PRINTING)
def test_requirements_pin_the_libraries_the_models_were_built_with(board: str) -> None:
    """A builder moved to another version moves these pins with the rebuilt models."""
    required = pins(QA_REQUIREMENTS)
    built_with = {
        re.sub(r"[-.]", "_", name.lower()): version
        for name, version in record(board)["builder"]["packages"].items()
    }
    for distribution in CAD_LIBRARIES.values():
        assert required.get(distribution) == built_with[distribution], (
            f"requirements.txt pins {distribution} at {required.get(distribution)}; "
            f"the {board} model was built with {built_with[distribution]}"
        )


def test_a_missing_cad_library_fails_in_ci_and_skips_anywhere_else(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A skip is for a developer's machine; CI installed the pins, so there it is a failure."""
    monkeypatch.setitem(CAD_LIBRARIES, "no_such_cad_library", "numpy")
    monkeypatch.delenv("CI", raising=False)
    with pytest.raises(pytest.skip.Exception, match="numpy is not installed.*pip install -r"):
        cad_library("no_such_cad_library")
    monkeypatch.setenv("CI", "true")
    with pytest.raises(pytest.fail.Exception, match="numpy is not installed.*broken install"):
        cad_library("no_such_cad_library")
    # installed, but not at the pin: the same two answers
    monkeypatch.setitem(CAD_LIBRARIES, "json", "numpy")
    monkeypatch.setattr(importlib.metadata, "version", lambda distribution: "0.0.1")
    with pytest.raises(
        pytest.fail.Exception, match="numpy 0.0.1 is installed, requirements.txt pins"
    ):
        cad_library("json")
    monkeypatch.delenv("CI")
    with pytest.raises(pytest.skip.Exception, match="numpy 0.0.1 is installed"):
        cad_library("json")
    # at the pin: the library itself
    pinned = pins(QA_REQUIREMENTS)["numpy"]
    monkeypatch.setattr(importlib.metadata, "version", lambda distribution: pinned)
    assert cad_library("json") is json


@pytest.mark.parametrize("board", PRINTING)
def test_every_legend_is_in_the_model_where_the_drawing_prints_it(board: str) -> None:
    """Each key's legend and each other print, within two position steps of the drawing."""
    record(board)
    report = placement_module().check(CAD / board)
    assert report["ok"], report["problems"]
    assert report["groups"] == sum(planes_of_front(board).values())
    assert report["worst_mm"] <= report["tolerance_mm"] == 0.02


@pytest.mark.selftest
def test_the_placement_check_catches_what_is_planted() -> None:
    """A check that passes everything checks nothing: each planted defect fails it."""
    clean, results, controls = placement_module().selftest()
    assert clean["ok"], clean["problems"]
    assert len(results) >= 10
    for what, caught, how in results:
        assert caught, f"{what}: {how}"
    # the two a review found the check blind to, written into the file itself, are among them
    planted = " | ".join(what for what, _caught, _how in results)
    for words in (
        "by its node's translation",
        "by its root node's translation",
        "material turned red",
        "in the drawing after the build",
    ):
        assert words in planted, f"the selftest no longer plants: {words}"
    # and what is no defect passes: a drawing changed only where no model reads
    assert controls
    for what, passed, how in controls:
        assert passed, f"{what}: {how}"


# --- Prints on the other faces, and a module stacked under a board ---------------

#: The board of two boxes that prints on its front and its back, built from two
#: vendor files (``_shared/face_fixture.py``): no committed board does either
#: yet, so the paths are held to it.
FIXTURE = SHARED / "fixtures" / "faces"


def fixture_record() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(
        (FIXTURE / "model" / "source.json").read_text(encoding="utf-8")
    )
    return loaded


def test_every_face_lays_its_drawing_as_its_viewer_reads_it() -> None:
    """Each face's frame: u to the viewer's right, v down, the normal towards the viewer.

    The basis is right-handed (u times up is the outward normal), so a sheet
    wound counterclockwise in the drawing faces its viewer; a point drawn at
    the drawing's origin lies at the face's two origin keys; and the back's
    u runs from the case's right edge as the front is seen, so a back print is
    never laid mirrored.
    """
    np = cad_library("numpy")
    for face, ((u_axis, _u_sign), (up_axis, _up_sign), keys) in board_faces.FACES.items():
        basis = board_faces.basis(face)
        assert np.allclose(np.cross(basis[0], basis[1]), basis[2]), face
        assert len(keys) == 2 and board_faces.height_key(face) not in (
            board_faces.AXES[u_axis],
            board_faces.AXES[up_axis],
        ), face
        frame = board_faces.FaceFrame(face, 3.0, 40.0)
        center = np.array([10.0, 20.0, -5.0])
        du, dv = frame.offsets(center)
        corner = frame.embed(np.array([[du, dv]]), center, 7.0)[0]
        assert corner[u_axis] == pytest.approx(3.0) and corner[up_axis] == pytest.approx(40.0), face
        # a drawing's (u, v) lies at a = u + du, b = dv - v, and reads back as (u, v)
        drawn = np.array([[2.0, 5.0]])
        placed = frame.embed(np.column_stack([drawn[:, 0] + du, dv - drawn[:, 1]]), center, 7.0)
        read = board_faces.to_drawing(placed - center, frame, center)
        assert np.allclose(read[:, :2], drawn), face
        assert placed[0][board_faces.normal(face)[0]] == 7.0, face
    back = board_faces.FaceFrame("back", 24.0, 48.0)
    center = np.array([12.0, 24.0, -7.0])
    du, dv = back.offsets(center)
    # one millimeter across a back drawing is one millimeter towards the front's left
    near, far = back.embed(np.array([[du, dv], [du + 1.0, dv]]), center, 0.0)
    assert near[0] == pytest.approx(24.0) and far[0] == pytest.approx(23.0)
    assert board_faces.height_key("back") == "z" and board_faces.normal("back") == (2, -1)
    assert board_faces.height_key("top") == "y" and board_faces.height_key("left") == "x"


def test_the_face_fixture_is_what_its_writer_writes() -> None:
    """The two boxes, the two drawings and the spec are ``face_fixture.py``'s, byte for byte."""
    import face_fixture

    for name, data in face_fixture.files().items():
        assert (FIXTURE / name).read_bytes() == data, f"{name}: run face_fixture.py"


def test_the_face_fixture_model_is_built_from_both_files_and_both_drawings() -> None:
    """Its record names the module's file, the back's drawing and frame, and is current."""
    rec = fixture_record()
    data = (ROOT / rec["model"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == rec["model_sha256"], "rebuild the fixture"
    assert (
        hashlib.sha256((ROOT / rec["builder"]["spec"]).read_bytes()).hexdigest()
        == (rec["builder"]["spec_sha256"])
    ), "the fixture's spec changed since its model was built"
    for unit in [rec["source"], *(m["source"] for m in rec["modules"])]:
        vendor = ROOT / unit["url"]
        assert hashlib.sha256(vendor.read_bytes()).hexdigest() == unit["sha256"], vendor.name
    assert [m["name"] for m in rec["modules"]] == ["base"]
    assert rec["modules"][0]["transform"] == [{"translate": [0.0, 0.0, -12.0]}]
    faces = {entry.get("face", "front"): entry for entry in rec["legends"]}
    assert set(faces) == {"front", "back"}
    assert "front" in faces["front"] and "drawing" not in faces["front"]
    assert faces["back"]["drawing"].endswith("svg/back.svg") and "front" not in faces["back"]
    assert rec["parameters"]["face_frames"] == {"back": {"right_x": 20.0, "top_y": 30.0}}
    for entry in rec["legends"]:
        assert (
            legend_source.digest(ROOT / drawing_of(entry), entry["plane"])
            == (entry["legends_sha256"])
        ), entry["mesh"]


def test_a_back_print_faces_out_of_the_back_three_steps_out_of_its_mesh() -> None:
    """Normals -Z, every triangle wound towards the back's viewer, 0.03 mm under the base."""
    np = cad_library("numpy")
    import model_raster

    rec = fixture_record()
    step = rec["parameters"]["quant_mm"]
    meshes = model_raster.read_glb(ROOT / rec["model"])
    back = next(entry for entry in rec["legends"] if entry.get("face") == "back")
    sheets = [m for m in meshes if m.name.startswith(back["mesh"] + "_")]
    assert {m.name for m in sheets} == {"label_legends_111113", "label_legends_d2390c"}
    for sheet in sheets:
        assert np.allclose(sheet.normals, [0.0, 0.0, -1.0], atol=1e-6), sheet.name
        tri = sheet.positions[sheet.faces]
        turn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])[:, 2]
        assert (turn < 0).all(), f"{sheet.name}: a triangle wound towards the front"
        assert np.allclose(sheet.positions[:, 2], back["z_mm"] - rec["parameters"]["center_mm"][2])
    gap = _clearance(meshes, back["mesh"] + "_", step, on=back["on"], face="back")
    assert gap["ok"] and gap["under_mm"] == pytest.approx(3 * step, abs=1e-6)
    assert gap["under_mesh"] == "base"
    assert model_raster.coplanar_overlaps(meshes, step)["ok"]


def test_every_print_of_the_face_fixture_is_where_its_drawings_put_it() -> None:
    """The front's and the back's, each read in its own drawing's frame."""
    report = placement_module().check(FIXTURE)
    assert report["ok"], report["problems"]
    assert report["groups"] == 2 and report["worst_mm"] <= 0.02
    assert report["meshes"]["label_legends"]["face"] == "back"


@pytest.mark.selftest
def test_the_placement_check_catches_what_is_planted_on_a_back() -> None:
    """A back print mirrored, moved, lifted, wound inwards or turned is a defect found."""
    clean, results, controls = placement_module().faces_selftest()
    assert clean["ok"], clean["problems"]
    planted = " | ".join(what for what, _caught, _how in results)
    for words in (
        "mirrored across the case",
        "wound to face into the case",
        "normals turned to the front",
        "laid on the face it is printed on",
        "looked for from the front",
        "back drawing moved",
    ):
        assert words in planted, f"the selftest no longer plants: {words}"
    for what, caught, how in results:
        assert caught, f"{what}: {how}"
    for what, passed, how in controls:
        assert passed, f"{what}: {how}"


def builder_module() -> ModuleType:
    """``build_board_glb``, where the builder's own libraries are installed (not the QA stack's)."""
    for module in ("trimesh", "scipy", "networkx", "rtree"):
        pytest.importorskip(module, reason="the model builder's libraries (build_board_glb.py)")
    for module in CAD_LIBRARIES:
        cad_library(module)
    import build_board_glb

    return build_board_glb


@pytest.mark.selftest
def test_the_face_fixture_rebuilds_byte_for_byte(tmp_path: Path) -> None:
    """Two vendor files and two drawings build the committed fixture, and nothing else does."""
    builder = builder_module()
    spec_ = builder.load_spec(FIXTURE / "model" / "spec.json")
    vendor = FIXTURE / "vendor"
    out = tmp_path / "faces.glb"
    builder.build(
        spec_,
        vendor / "body.stl",
        out,
        modules=builder.module_paths(spec_, given={"base": vendor / "base.stl"}),
    )
    assert out.read_bytes() == (ROOT / fixture_record()["model"]).read_bytes()
    # a module's file is pinned like the spec's own
    with pytest.raises(builder.SpecError, match="not the pinned vendor file"):
        builder.module_paths(spec_, given={"base": vendor / "body.stl"})
    with pytest.raises(builder.SpecError, match="names no module"):
        builder.module_paths(spec_, given={"lid": vendor / "base.stl"})


def _back_read_as_the_front_too(s: dict[str, Any]) -> None:
    s["meshes"].append(
        {
            "name": "other_legends",
            "legends": {"drawing": "../svg/back.svg", "plane": "other", "on": "case", "z": 0.03},
        }
    )


def _back_height_on_y(s: dict[str, Any]) -> None:
    legends = s["meshes"][3]["legends"]
    legends["y"] = legends.pop("z")


def _front_named_on_the_back(s: dict[str, Any]) -> None:
    s["meshes"][2]["legends"]["face"] = "back"


def _no_such_face(s: dict[str, Any]) -> None:
    s["meshes"][3]["legends"]["face"] = "side"


def _drawing_named_twice(s: dict[str, Any]) -> None:
    s["meshes"][3]["legends"]["front"] = "../svg/back.svg"


def _part_named_twice(s: dict[str, Any]) -> None:
    s["modules"][0]["parts"][0]["name"] = "body"


def _module_named_twice(s: dict[str, Any]) -> None:
    s["modules"].append(dict(s["modules"][0]))


def _top_frame_short_of_a_key(s: dict[str, Any]) -> None:
    s["face_frames"] = {"top": {"left_x": 0}}


def _front_given_as_a_face_frame(s: dict[str, Any]) -> None:
    s["face_frames"] = {"front": {"left_x": 0, "top_y": 0}}


@pytest.mark.parametrize(
    ("change", "words"),
    [
        (_back_read_as_the_front_too, "a drawing draws one face"),
        (_back_height_on_y, "lie at a height along z"),
        (_front_named_on_the_back, "given as drawing"),
        (_no_such_face, "is not one of"),
        (_drawing_named_twice, "names its drawing once"),
        (_part_named_twice, "part names repeat"),
        (_module_named_twice, "module names repeat"),
        (_top_frame_short_of_a_key, "the top frame takes"),
        (_front_given_as_a_face_frame, "front_frame"),
    ],
    ids=lambda value: value.__name__.strip("_") if callable(value) else None,
)
def test_the_builder_refuses_a_face_or_a_module_it_cannot_place(
    change: Callable[..., Any], words: str
) -> None:
    """A print on an unnamed face, at a height on the wrong axis, or a part named twice."""
    builder = builder_module()
    spec_ = json.loads((FIXTURE / "model" / "spec.json").read_text(encoding="utf-8"))
    change(spec_)
    with pytest.raises(builder.SpecError, match=words):
        builder.validate(spec_)
