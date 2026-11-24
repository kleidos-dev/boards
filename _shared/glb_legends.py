# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""List a board model's legend meshes, or write the model without them

What is printed on a board is, in its model, a set of flat meshes of their own
(``build_board_glb.py``, ``legend_mesh.py``): every node whose name ends in
``_legends_<rrggbb>``, one an ink color, with its ink's material
``ink_<rrggbb>`` and ``extras.legends`` (``fill``, ``stroke_mm``, ``on``). A
print is geometry, so it has no smaller version of itself: where a board is
drawn so small that a stroke covers less than a pixel, the legends only add
speckle, and a reader leaves them out. This module is that cut, made from the
file alone, with the standard library and nothing else.

``strip`` rewrites the model the way the builder writes one (the same order of
views, the same padding, the same JSON), so the model less its legend meshes
is, byte for byte, the model built without them: ``build_board_glb.py --check
--without-legends`` builds that one from the vendor file and compares.

**The rule.** A legend mesh is worth drawing where its strokes cover about a
pixel: leave it out when ``stroke_mm`` times the pixels a millimeter is under
1 with 4x multisampling, or under 1.5 with no antialiasing. ``--px-per-mm``
applies it mesh by mesh (the Cardputer ADV's black legends hold to a board
about 280 px wide, its blue shifted ones to about 450); with no scale given,
every legend mesh goes. Decide it once for a shot, never frame by frame.

Usage::

    python -I _shared/glb_legends.py list MODEL.glb
    python -I _shared/glb_legends.py strip MODEL.glb OUT.glb \\
        [--px-per-mm N] [--no-antialias]
"""

import argparse
import json
import re
import struct
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import OutsideError, work_path

GLB_MAGIC, JSON_CHUNK, BIN_CHUNK = 0x46546C67, 0x4E4F534A, 0x004E4942
#: A legend mesh's node name ends so; no other node's does.
LEGEND_NODE = re.compile(r"_legends_[0-9a-f]{6}$")
#: What the name of a legend's ink material starts with.
INK_PREFIX = "ink_"
#: The least a stroke must cover, in pixels, for its mesh to be drawn.
MIN_STROKE_PX = {"msaa4": 1.0, "none": 1.5}


def is_legend(name: str) -> bool:
    """True for the name of a legend mesh's node."""
    return bool(LEGEND_NODE.search(name or ""))


def read(data: bytes) -> tuple[dict[str, Any], bytes]:
    """(the JSON chunk as a dict, the binary chunk) of a GLB's bytes."""
    magic, version, total = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC or version != 2 or total != len(data):
        raise ValueError("not a glTF 2.0 binary of the length its header gives")
    jlen, jtype = struct.unpack_from("<II", data, 12)
    if jtype != JSON_CHUNK:
        raise ValueError("the first chunk is not JSON")
    js = json.loads(data[20 : 20 + jlen])
    at = 20 + jlen
    blen, btype = struct.unpack_from("<II", data, at)
    if btype != BIN_CHUNK:
        raise ValueError("the second chunk is not binary")
    return js, bytes(data[at + 8 : at + 8 + blen])


def write(js: dict[str, Any], bin_: bytes | bytearray) -> bytes:
    """A GLB's bytes from its JSON and its binary chunk, laid out as the builder's are."""
    body = bytearray(bin_)
    while len(body) % 4:
        body.append(0)
    text = json.dumps(js, separators=(",", ":"), ensure_ascii=False).encode()
    while len(text) % 4:
        text += b" "
    total = 12 + 8 + len(text) + 8 + len(body)
    return (
        struct.pack("<III", GLB_MAGIC, 2, total)
        + struct.pack("<II", len(text), JSON_CHUNK)
        + text
        + struct.pack("<II", len(body), BIN_CHUNK)
        + bytes(body)
    )


def legends(js: dict[str, Any]) -> list[dict[str, Any]]:
    """What a model's legend meshes are, in its order.

    A list of ``{'node', 'name', 'fill', 'stroke_mm', 'on', 'triangles',
    'material'}``, ``node`` being the node's index and ``material`` its ink's
    name; ``fill``, ``stroke_mm`` and ``on`` are None in a model built before
    they were written.
    """
    out = []
    for index, node in enumerate(js.get("nodes", [])):
        if "mesh" not in node or not is_legend(node.get("name")):
            continue
        prims = js["meshes"][node["mesh"]]["primitives"]
        said = (node.get("extras") or {}).get("legends") or {}
        out.append(
            {
                "node": index,
                "name": node["name"],
                "fill": said.get("fill"),
                "stroke_mm": said.get("stroke_mm"),
                "on": said.get("on"),
                "triangles": sum(js["accessors"][p["indices"]]["count"] // 3 for p in prims),
                "material": js["materials"][prims[0]["material"]].get("name"),
            }
        )
    return out


def too_thin(stroke_mm: float, px_per_mm: float, antialias: bool = True) -> bool:
    """True when a print of this stroke width covers too little of a pixel to draw.

    *px_per_mm* is how many pixels of the frame a millimeter of the board
    covers; *antialias* says whether the frame is multisampled (4x).
    """
    return stroke_mm * px_per_mm < MIN_STROKE_PX["msaa4" if antialias else "none"]


def strip(data: bytes, drop: Callable[[dict[str, Any]], bool] | None = None) -> bytes:
    """The bytes of a model without its legend meshes.

    *drop* picks the meshes that go, given each entry of ``legends``; left
    out, every legend mesh goes. What is left is rewritten as the builder
    writes a model: the kept nodes, meshes, accessors and buffer views in
    their order, each view on a 4-byte boundary, and the materials less those
    only the dropped meshes used.
    """
    js, bin_ = read(data)
    gone_nodes = {entry["node"] for entry in legends(js) if drop is None or drop(entry)}
    if not gone_nodes:
        return bytes(data)
    nodes = js["nodes"]
    for index, node in enumerate(nodes):
        if index in gone_nodes and node.get("children"):
            raise ValueError(f"the legend node {node.get('name')!r} has children")
    kept_nodes = [i for i in range(len(nodes)) if i not in gone_nodes]
    node_at = {old: new for new, old in enumerate(kept_nodes)}
    gone_meshes = {nodes[i]["mesh"] for i in gone_nodes}
    kept_meshes = [i for i in range(len(js["meshes"])) if i not in gone_meshes]
    if any(nodes[i].get("mesh") in gone_meshes for i in kept_nodes):
        raise ValueError("a legend mesh is shared with a node that is not a legend")
    mesh_at = {old: new for new, old in enumerate(kept_meshes)}

    def used(mesh_indices: Iterable[int]) -> tuple[set[int], set[int]]:
        acc, mat = set(), set()
        for i in mesh_indices:
            for prim in js["meshes"][i]["primitives"]:
                acc.update(prim["attributes"].values())
                if "indices" in prim:
                    acc.add(prim["indices"])
                if "material" in prim:
                    mat.add(prim["material"])
        return acc, mat

    kept_acc, kept_mat = used(kept_meshes)
    gone_acc, gone_mat = used(gone_meshes)
    if kept_acc & gone_acc:
        raise ValueError("a legend mesh shares an accessor with another mesh")
    accessors = [i for i in range(len(js["accessors"])) if i not in gone_acc]
    acc_at = {old: new for new, old in enumerate(accessors)}
    gone_views = {js["accessors"][i]["bufferView"] for i in gone_acc}
    if gone_views & {js["accessors"][i]["bufferView"] for i in accessors}:
        raise ValueError("a legend mesh shares a buffer view with another mesh")
    views = [i for i in range(len(js["bufferViews"])) if i not in gone_views]
    view_at = {old: new for new, old in enumerate(views)}
    # an ink only the dropped meshes used goes with them
    materials = [i for i in range(len(js["materials"])) if i not in (gone_mat - kept_mat)]
    mat_at = {old: new for new, old in enumerate(materials)}

    body = bytearray()
    new_views = []
    for i in views:
        view = dict(js["bufferViews"][i])
        start = view.get("byteOffset", 0)
        while len(body) % 4:
            body.append(0)
        view["byteOffset"] = len(body)
        body += bin_[start : start + view["byteLength"]]
        new_views.append(view)
    while len(body) % 4:
        body.append(0)

    new_nodes = []
    for i in kept_nodes:
        node = dict(nodes[i])
        if "children" in node:
            node["children"] = [node_at[c] for c in node["children"] if c not in gone_nodes]
        if "mesh" in node:
            node["mesh"] = mesh_at[node["mesh"]]
        new_nodes.append(node)
    new_meshes = []
    for i in kept_meshes:
        mesh = dict(js["meshes"][i])
        mesh["primitives"] = [
            {
                **prim,
                "attributes": {k: acc_at[v] for k, v in prim["attributes"].items()},
                **({"indices": acc_at[prim["indices"]]} if "indices" in prim else {}),
                **({"material": mat_at[prim["material"]]} if "material" in prim else {}),
            }
            for prim in mesh["primitives"]
        ]
        new_meshes.append(mesh)
    out = dict(js)
    out["nodes"] = new_nodes
    out["meshes"] = new_meshes
    out["materials"] = [js["materials"][i] for i in materials]
    out["accessors"] = [
        {**js["accessors"][i], "bufferView": view_at[js["accessors"][i]["bufferView"]]}
        for i in accessors
    ]
    out["bufferViews"] = new_views
    out["buffers"] = [{**js["buffers"][0], "byteLength": len(body)}]
    for scene in out.get("scenes", []):
        if any(n in gone_nodes for n in scene.get("nodes", [])):
            raise ValueError("a legend node is a root of the scene")
    out["scenes"] = [
        {**scene, "nodes": [node_at[n] for n in scene.get("nodes", [])]}
        for scene in js.get("scenes", [])
    ]
    return write(out, body)


def main(argv: list[str] | None = None) -> int:
    """List or strip a model's legends from the command line; return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="print the model's legend meshes")
    listing.add_argument("model", type=Path)
    cut = sub.add_parser("strip", help="write the model without its legend meshes")
    cut.add_argument("model", type=Path)
    cut.add_argument("out", type=Path)
    cut.add_argument(
        "--px-per-mm",
        type=float,
        help="leave out only the meshes too thin to draw at this many pixels a "
        "millimeter of the board (default: every legend mesh)",
    )
    cut.add_argument(
        "--no-antialias",
        action="store_true",
        help="with --px-per-mm: the frame is not multisampled",
    )
    args = parser.parse_args(argv)
    try:
        model = work_path(args.model)
        out_path = work_path(args.out) if args.command == "strip" else None
    except OutsideError as exc:
        parser.error(str(exc))
    data = model.read_bytes()
    js, _ = read(data)
    found = legends(js)
    if out_path is None:
        for entry in found:
            width = entry["stroke_mm"]
            reach = (
                ""
                if width is None
                else f", drawn from {MIN_STROKE_PX['msaa4'] / width:.2f} px/mm multisampled, "
                f"{MIN_STROKE_PX['none'] / width:.2f} px/mm not"
            )
            print(
                f"{entry['name']}: ink {entry['fill']}, on {entry['on']}, "
                f"{entry['triangles']} triangles, stroke {width} mm{reach}"
            )
        print(f"{len(found)} legend meshes, {sum(e['triangles'] for e in found)} triangles")
        return 0
    if out_path == model:
        print("FAILED: the output is the model itself", file=sys.stderr)
        return 1
    drop = None
    if args.px_per_mm is not None:
        if any(entry["stroke_mm"] is None for entry in found):
            print(
                "FAILED: this model was built before its legends carried stroke_mm; "
                "rebuild it, or strip every legend",
                file=sys.stderr,
            )
            return 1

        def drop(entry: dict[str, Any]) -> bool:
            return too_thin(entry["stroke_mm"], args.px_per_mm, not args.no_antialias)

    out = strip(data, drop)
    with open(out_path, "wb") as fh:
        fh.write(out)
    left = legends(read(out)[0])
    print(
        f"wrote {args.out}: {len(out)} bytes ({len(data)} with every legend), "
        f"{len(found) - len(left)} of {len(found)} legend meshes left out"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
