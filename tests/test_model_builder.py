# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""The model builder reads a spec it can trust, and its commands do what they say.

``_shared/build_board_glb.py`` builds a model from a spec and a pinned vendor
file. Held here, on the checks' own test board (``_shared/fixtures/faces``,
two boxes and two drawings) and on shapes written for the test:

- what a spec names is checked where the spec is read: the vendor file's name
  and digest, the address it is downloaded from, the model's path, how many of
  each thing a shape asks for;
- a vendor file comes from the address and no other, and only its pinned bytes
  are used;
- every shape a spec may write is the solid it says;
- the command builds, compares, weighs and records what its options say.

Host-only: no hardware, no network.
"""

from __future__ import annotations

import io
import json
import math
import shutil
import struct
import sys
import urllib.request
from collections.abc import Callable
from http.client import HTTPMessage
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))
import build_board_glb as builder  # noqa: E402  after the sys.path set-up above
import glb_legends  # noqa: E402  after the sys.path set-up above
import media_meta  # noqa: E402  after the sys.path set-up above
import model_raster  # noqa: E402  after the sys.path set-up above
import paths  # noqa: E402  after the sys.path set-up above

FIXTURE = ROOT / "_shared" / "fixtures" / "faces"


def written_spec() -> dict[str, Any]:
    """The test board's spec, as its file holds it."""
    spec: dict[str, Any] = json.loads((FIXTURE / "model" / "spec.json").read_text(encoding="utf-8"))
    return spec


# --- what a spec may name -----------------------------------------------------------


def _set(*keys: str, value: object) -> Callable[[dict[str, Any]], None]:
    def change(spec: dict[str, Any]) -> None:
        inner: Any = spec
        for key in keys[:-1]:
            inner = inner[int(key)] if isinstance(inner, list) else inner[key]
        inner[keys[-1]] = value

    return change


@pytest.mark.parametrize(
    ("change", "words"),
    [
        (_set("source", "file", value="../body.stl"), "is not the name of a file"),
        (_set("source", "file", value="/etc/passwd"), "is not the name of a file"),
        (_set("source", "file", value=".hidden"), "is not the name of a file"),
        (_set("source", "file", value=None), "is not the name of a file"),
        (_set("source", "sha256", value="../../etc"), "is not a SHA-256"),
        (_set("source", "sha256", value="A" * 64), "is not a SHA-256"),
        (_set("source", "sha256", value="a" * 63), "is not a SHA-256"),
        (_set("modules", "0", "source", "file", value="a/b.stl"), "module 'base' source: file"),
        (_set("modules", "0", "source", "sha256", value=""), "module 'base' source: sha256"),
    ],
)
def test_a_spec_that_names_its_vendor_file_by_a_path_is_refused(
    change: Callable[[dict[str, Any]], None], words: str
) -> None:
    spec = written_spec()
    builder.validate(spec)
    change(spec)
    with pytest.raises(builder.SpecError, match=words):
        builder.validate(spec)


def test_a_models_path_stays_in_the_repository(tmp_path: Path) -> None:
    spec = written_spec()
    assert builder.output_path(spec) == FIXTURE / "model" / "faces.glb"
    for output in ("../faces.glb", "/etc/faces.glb", "_shared/../../faces.glb"):
        with pytest.raises(paths.OutsideError):
            builder.output_path({**spec, "output": output})
    loaded = builder.load_spec(FIXTURE / "model" / "spec.json")
    assert builder.web_path(loaded) == FIXTURE / "model" / "faces-web.glb"
    assert builder.measurements({**loaded, "measurements": None}) is None
    with pytest.raises(paths.OutsideError):
        builder.measurements({**loaded, "measurements": "/etc/hosts"})
    other = tmp_path / "spec.json"
    other.write_text(json.dumps({"schema": 2}), encoding="utf-8")
    with pytest.raises(builder.SpecError, match="this builder reads 1"):
        builder.load_spec(other)


@pytest.mark.parametrize(
    "url",
    [
        "http://raw.githubusercontent.com/m5stack/a.stl",
        "https://example.com/a.stl",
        "https://raw.githubusercontent.com.example.com/a.stl",
        "https://user:" + "@" + "raw.githubusercontent.com/a.stl",
        "https://raw.githubusercontent.com:8443/a.stl",
        "file:///etc/passwd",
        "_shared/fixtures/faces/vendor/body.stl",
        "",
    ],
)
def test_a_vendor_file_is_fetched_from_its_hosts_alone(url: str) -> None:
    with pytest.raises(builder.SpecError, match="from https://raw.githubusercontent.com/ only"):
        builder.vendor_address(url)


def test_every_board_is_fetched_from_one_of_those_hosts() -> None:
    addresses = [
        unit["source"]["url"]
        for path in sorted(ROOT.glob("*/model/spec.json"))
        for _, unit in builder.units(builder.load_spec(path))
    ]
    assert len(addresses) >= 9
    for address in addresses:
        assert builder.vendor_address(address) == address


def test_a_redirect_leads_to_one_of_those_hosts_or_nowhere() -> None:
    follow = builder.VendorRedirects()
    asked = urllib.request.Request("https://raw.githubusercontent.com/a.stl")
    elsewhere = "https://raw.githubusercontent.com/b.stl"
    again = follow.redirect_request(asked, io.BytesIO(), 302, "Found", HTTPMessage(), elsewhere)
    assert again is not None and again.full_url == elsewhere
    with pytest.raises(builder.SpecError, match="a vendor file is fetched"):
        follow.redirect_request(
            asked, io.BytesIO(), 302, "Found", HTTPMessage(), "https://example.com/b.stl"
        )


class _Opener:
    """What ``urllib.request.build_opener`` gives, answering with *data* and no network."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.asked: list[str] = []

    def open(self, url: str, timeout: float) -> io.BytesIO:
        assert timeout > 0
        self.asked.append(url)
        return io.BytesIO(self.data)


def test_a_fetched_file_is_kept_only_with_its_pinned_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unit = written_spec()
    unit["source"]["url"] = "https://raw.githubusercontent.com/kleidos-dev/body.stl"
    where = tmp_path / unit["source"]["sha256"][:12] / "body.stl"
    opener = _Opener(b"other bytes")
    monkeypatch.setattr(urllib.request, "build_opener", lambda *_: opener)
    assert builder.cached_source(unit, tmp_path, fetch=False) == where.resolve()
    assert opener.asked == []
    with pytest.raises(builder.SpecError, match="served sha256"):
        builder.cached_source(unit, tmp_path, fetch=True)
    assert list(where.parent.iterdir()) == []
    opener.data = (FIXTURE / "vendor" / "body.stl").read_bytes()
    assert builder.cached_source(unit, tmp_path, fetch=True) == where.resolve()
    assert where.read_bytes() == opener.data
    assert opener.asked == [unit["source"]["url"]] * 2
    builder.cached_source(unit, tmp_path, fetch=True)
    assert len(opener.asked) == 2  # in the cache: not fetched again
    unit["source"]["file"] = "../../body.stl"
    with pytest.raises(paths.OutsideError):
        builder.cached_source(unit, tmp_path, fetch=True)


def test_a_vendor_file_given_by_its_path_holds_the_pinned_bytes(tmp_path: Path) -> None:
    spec = builder.load_spec(FIXTURE / "model" / "spec.json")
    base = FIXTURE / "vendor" / "base.stl"
    assert builder.module_paths(spec, tmp_path, given={"base": base}) == {"base": base}
    with pytest.raises(builder.SpecError, match="no such file"):
        builder.module_paths(spec, tmp_path)
    with pytest.raises(builder.SpecError, match="not the pinned vendor file"):
        builder.module_paths(spec, tmp_path, given={"base": FIXTURE / "vendor" / "body.stl"})
    with pytest.raises(builder.SpecError, match="names no module"):
        builder.module_paths(spec, tmp_path, given={"lid": base})


# --- what a spec's shapes are -------------------------------------------------------


def solid(shape: dict[str, Any], frame: builder.Frame | None = None) -> trimesh.Trimesh:
    """A shape of a spec as one mesh."""
    made = builder.shape_meshes(
        shape, {"one": [[0, 2, 0, 3, 0, 4]], "two": [[0, 1, 0, 1, 0, 1], [2, 3, 2, 3, 2, 3]]}, frame
    )
    assert isinstance(made, list)
    joined = made[0] if len(made) == 1 else trimesh.util.concatenate(made)
    assert isinstance(joined, trimesh.Trimesh)
    return joined


@pytest.mark.parametrize(
    ("shape", "extents", "volume"),
    [
        ({"box": [0, 1, 0, 2, 0, "1 + 2"]}, (1, 2, 3), 6.0),
        ({"volume": "one"}, (2, 3, 4), 24.0),
        ({"volume": "two"}, (3, 3, 3), 2.0),
        (
            {"prism": {"axis": "z", "range": [0, 2], "profile": {"rect": [0, 3, 0, 4]}}},
            (3, 4, 2),
            24.0,
        ),
        (
            {"prism": {"axis": "y", "range": [0, 2], "profile": {"rect": [0, 3, 0, 4]}}},
            (3, 2, 4),
            24.0,
        ),
        (
            {"prism": {"axis": "x", "range": [0, 2], "profile": {"rect": [0, 3, 0, 4]}}},
            (2, 3, 4),
            24.0,
        ),
        (
            {"prism": {"axis": "z", "volume": "one", "profile": {"rounded": 0.5, "res": 8}}},
            (2, 3, 4),
            24.0 - (1 - math.pi / 4) * 4,
        ),
        ({"prism": {"axis": "z", "volume": "one", "profile": {"rect": []}}}, (2, 3, 4), 24.0),
        (
            {
                "prism": {
                    "axis": "z",
                    "range": [0, 1],
                    "profile": {"rounded_rect": [0, 4, 0, 4], "r": 1, "res": 16},
                }
            },
            (4, 4, 1),
            16 - (4 - math.pi),
        ),
        (
            {
                "prism": {
                    "axis": "z",
                    "range": [0, 1],
                    "profile": {"stadium": [0, 0, 4, 2], "inner": [3, 1], "res": 24},
                }
            },
            (4, 2, 1),
            (4 + math.pi) - (2 + math.pi / 4),
        ),
        (
            {
                "prism": {
                    "axis": "z",
                    "range": [0, 1],
                    "profile": {
                        "polygon": [[0, 0], [4, 0], [4, 4], [0, 4]],
                        "holes": [[[1, 1], [2, 1], [2, 2], [1, 2]]],
                    },
                }
            },
            (4, 4, 1),
            15.0,
        ),
        (
            {"cylinder": {"axis": "x", "c": [0, 0], "r": 1, "range": [0, 3], "sections": 64}},
            (3, 2, 2),
            3 * math.pi,
        ),
        ({"sphere": {"c": [0, 0, 0], "r": 1, "subdivisions": 4}}, (2, 2, 2), 4 * math.pi / 3),
    ],
)
def test_a_shape_is_the_solid_it_says(
    shape: dict[str, Any], extents: tuple[float, ...], volume: float
) -> None:
    mesh = solid(shape)
    assert mesh.extents == pytest.approx(extents, rel=0.01)
    assert abs(mesh.volume) == pytest.approx(volume, rel=0.02)


def test_a_sphere_is_cut_below_its_plane_and_a_loft_joins_its_sections() -> None:
    dome = solid({"sphere": {"c": [0, 0, 0], "r": 1, "z_min": 0.5}})
    assert dome.bounds[0][2] == pytest.approx(0.5) and dome.bounds[1][2] == pytest.approx(1.0)
    square = [[0, 0], [2, 0], [2, 2], [0, 2]]
    sections = [{"at": 0, "polygon": square}, {"at": 3, "polygon": square}]
    assert len(solid({"loft": {"axis": "z", "sections": sections}}).faces) == 8
    closed = solid({"loft": {"axis": "z", "sections": sections, "caps": ["first", "last"]}})
    assert abs(closed.volume) == pytest.approx(12.0)


def test_a_shape_in_the_front_frame_is_drawn_down_from_the_top() -> None:
    """x across from the left edge, y down from the top edge, z as it is."""
    frame = builder.Frame(-10.0, 20.0)
    mesh = solid({"box": [1, 3, 2, 5, 0, 1], "frame": "front"}, frame)
    assert mesh.bounds.tolist() == [[-9.0, 15.0, 0.0], [-7.0, 18.0, 1.0]]
    for shape in (
        {"prism": {"axis": "z", "range": [0, 1], "profile": {"rect": [1, 3, 2, 5]}}},
        {
            "prism": {
                "axis": "z",
                "range": [0, 1],
                "profile": {"rounded_rect": [1, 3, 2, 5], "r": 0.1},
            }
        },
        {
            "prism": {
                "axis": "z",
                "range": [0, 1],
                "profile": {"polygon": [[1, 2], [3, 2], [3, 5], [1, 5]]},
            }
        },
        {"prism": {"axis": "z", "range": [0, 1], "profile": {"stadium": [2, 3.5, 2, 2]}}},
        {"cylinder": {"axis": "z", "c": [2, 3.5], "r": 1, "range": [0, 1]}},
        {"sphere": {"c": [2, 3.5, 0.5], "r": 1}},
        {
            "loft": {
                "axis": "z",
                "sections": [
                    {"at": 0, "polygon": [[1, 2], [3, 2], [3, 5]]},
                    {"at": 1, "polygon": [[1, 2], [3, 2], [3, 5]]},
                ],
            }
        },
    ):
        placed = solid({**shape, "frame": "front"}, frame)
        assert placed.bounds.mean(axis=0)[:2] == pytest.approx((-8.0, 16.5), abs=0.01)
        with pytest.raises(builder.SpecError, match="needs front_frame"):
            builder.shape_meshes({**shape, "frame": "front"}, {}, None)


def _grid(**changes: object) -> dict[str, Any]:
    grid = {
        "axis": "z",
        "at": 1,
        "u_center": 0,
        "v_center": 0,
        "cols": 3,
        "rows": 2,
        "pitch": 2,
        "size": 1,
    }
    return {"quad_grid": {**grid, **changes}}


def test_a_grid_of_squares_has_the_rows_and_columns_it_asks_for() -> None:
    frame = builder.Frame(0.0, 10.0)
    for shape, facing in (
        (_grid(facing=-1), (0, 0, -1)),
        (_grid(axis="y", facing=1), (0, 1, 0)),
        ({**_grid(axis="y"), "frame": "front"}, (0, 1, 0)),
    ):
        made = builder.shape_meshes(shape, {}, frame)
        assert not isinstance(made, list)
        positions, normals, faces = made
        assert len(positions) == 24 and len(faces) == 12
        assert set(map(tuple, normals.tolist())) == {facing}
    with pytest.raises(builder.SpecError, match="unsupported axis"):
        builder.shape_meshes(_grid(axis="x"), {}, None)


@pytest.mark.parametrize(
    ("shape", "words"),
    [
        (_grid(cols=10**9), "cols 1000000000: a shape asks for 1 to 100"),
        (_grid(rows=10**9), "rows 1000000000: a shape asks for 1 to 100"),
        (_grid(cols=0), "cols 0"),
        (_grid(rows=-1), "rows -1"),
        ({"sphere": {"c": [0, 0, 0], "r": 1, "subdivisions": 30}}, "subdivisions 30"),
        (
            {"cylinder": {"axis": "z", "c": [0, 0], "r": 1, "range": [0, 1], "sections": 10**9}},
            "sections",
        ),
        (
            {"prism": {"axis": "z", "volume": "one", "profile": {"rounded": 0.5, "res": 10**9}}},
            "res",
        ),
        (
            {
                "prism": {
                    "axis": "z",
                    "range": [0, 1],
                    "profile": {"rounded_rect": [0, 1, 0, 1], "r": 0.1, "res": 0},
                }
            },
            "res 0",
        ),
        (
            {
                "prism": {
                    "axis": "z",
                    "range": [0, 1],
                    "profile": {"stadium": [0, 0, 2, 1], "res": 10**9},
                }
            },
            "res",
        ),
        ({"prism": {"axis": "z", "range": [0, 1], "profile": {}}}, "unknown profile"),
        ({"torus": {}}, "unknown shape"),
    ],
)
def test_a_shape_that_asks_for_too_much_is_refused(shape: dict[str, Any], words: str) -> None:
    with pytest.raises(builder.SpecError, match=words):
        builder.shape_meshes(shape, {"one": [[0, 2, 0, 3, 0, 4]]}, None)


def test_every_board_asks_for_what_a_shape_may() -> None:
    """The bounds leave every committed spec as it is."""
    for path in sorted(ROOT.glob("*/model/spec.json")):
        spec = builder.load_spec(path)
        volumes = builder.resolve_volumes(spec)
        for entry in spec["meshes"]:
            for shape in entry.get("shapes", []):
                if "quad_grid" in shape and shape.get("frame") != "front":
                    assert not isinstance(builder.shape_meshes(shape, volumes, None), list)


def stl(mesh: object) -> bytes:
    """A mesh as a binary STL: what a vendor file is."""
    assert isinstance(mesh, trimesh.Trimesh)
    records = np.zeros(len(mesh.faces), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    records["v"] = mesh.vertices[mesh.faces]
    return bytes(80) + struct.pack("<I", len(records)) + records.tobytes()


# --- the vendor geometry ------------------------------------------------------------


def test_a_part_is_matched_by_its_name_whole() -> None:
    """``*`` stands for any text, and nothing is a regular expression."""
    mesh = trimesh.creation.box((1, 1, 1))
    for pattern, name, matched in (
        ("Case*", "Case Shell", True),
        ("Shell", "Case Shell", False),
        ("*Shell", "Case Shell", True),
        ("case*", "Case Shell", False),
        ("Pin?", "Pin1", True),
        (".*", "Case Shell", False),
        ("(a+)+$", "aaaa", False),
    ):
        assert builder.matches(name, mesh, {"name": pattern}) is matched, (pattern, name)
    assert builder.matches("any", mesh, {})


def test_a_part_is_matched_by_its_bounds_and_its_faces() -> None:
    mesh = trimesh.creation.box((2, 4, 6))  # 12 faces, from -1, -2, -3 to 1, 2, 3
    for rule, matched in (
        ({"min_ge": [-1, None, None]}, True),
        ({"min_ge": [-0.5, None, None]}, False),
        ({"min_le": [None, -2, None]}, True),
        ({"max_ge": [None, None, 3.5]}, False),
        ({"max_le": [1, 2, 3]}, True),
        ({"extent_gt": [None, 3.9, None]}, True),
        ({"extent_lt": [None, 3.9, None]}, False),
        ({"faces_gt": 11, "faces_lt": 13}, True),
        ({"faces_gt": 12}, False),
        ({"faces_lt": 12}, False),
    ):
        assert builder.matches("any", mesh, rule) is matched, rule


def test_the_parts_of_a_spec_are_its_components_by_rule() -> None:
    left, right = trimesh.creation.box((1, 1, 1)), trimesh.creation.box((1, 1, 1))
    right.apply_translation([5, 0, 0])
    components = [("left", left), ("right", right)]
    spec: dict[str, Any] = {"parts": [{"name": "both", "match": {}}]}
    parts = builder.gather_parts(spec, components, {})
    assert len(parts["both"].faces) == 24
    spec = {"select": {"max_le": [3, None, None]}, "parts": [{"name": "one", "match": {}}]}
    assert len(builder.gather_parts(spec, components, {})["one"].faces) == 12
    missing: dict[str, Any] = {"name": "none", "match": {"faces_gt": 99}}
    with pytest.raises(builder.SpecError, match="no component matches"):
        builder.gather_parts({"parts": [missing]}, components, {})
    assert builder.gather_parts({"parts": [{**missing, "required": False}]}, components, {}) == {}
    with pytest.raises(builder.SpecError, match="2 components match"):
        builder.gather_parts(
            {"parts": [{"name": "one", "match": {}, "merge": False}]}, components, {}
        )


def test_a_parts_operations_cut_thin_and_hide(capsys: pytest.CaptureFixture[str]) -> None:
    cut = builder.part_ops(
        trimesh.creation.box((2, 2, 2)),
        [{"slice": {"normal": [0, 0, 1], "origin": [0, 0, 0], "cap": True}}],
        {},
    )
    assert cut.bounds[0][2] == pytest.approx(0.0)
    thinner = builder.part_ops(
        trimesh.creation.icosphere(subdivisions=3), [{"decimate": {"face_count": 200}}], {}
    )
    assert 0 < len(thinner.faces) <= 200
    outer = trimesh.creation.box((10, 10, 10))
    inner = trimesh.creation.box((1, 1, 1))
    both = trimesh.util.concatenate([outer, inner])
    assert isinstance(both, trimesh.Trimesh)
    hide = {"cull": {"volumes": ["fill"], "same_box": True}}
    shown = builder.part_ops(both, [hide], {"fill": [[-2, 2, -2, 2, -2, 2]]}, "shell")
    assert len(shown.faces) == 12
    assert "culled hidden faces: shell 12" in capsys.readouterr().out
    with pytest.raises(builder.SpecError, match="no volume 'other'"):
        builder.cull_boxes({}, ["other"])
    with pytest.raises(builder.SpecError, match="unknown part op"):
        builder.part_ops(outer, [{"bend": {}}], {})


def test_a_transform_takes_the_file_into_the_build_frame() -> None:
    mesh = trimesh.creation.box((2, 4, 6))
    moved = builder.apply_transform(
        mesh,
        [{"rotate": {"axis": "x", "deg": 90}}, {"translate": [1, 0, 0]}, {"scale": "1 / 2"}],
    )
    assert moved.extents == pytest.approx((1.0, 3.0, 2.0))
    assert moved.bounds[0][0] == pytest.approx(0.0)
    with pytest.raises(builder.SpecError, match="unknown transform"):
        builder.apply_transform(mesh, [{"shear": 1}])


def test_a_file_is_split_into_its_pieces(tmp_path: Path) -> None:
    left, right = trimesh.creation.box((1, 1, 1)), trimesh.creation.box((2, 2, 2))
    right.apply_translation([5, 0, 0])
    both = trimesh.util.concatenate([left, right])
    path = tmp_path / "two.stl"
    path.write_bytes(stl(both))
    spec: dict[str, Any] = {"source": {"format": "stl"}, "transform": [{"scale": 2}], "clean": True}
    pieces = builder.load_components(spec, path, tmp_path)
    assert sorted(round(float(m.extents[0])) for _, m in pieces) == [2, 4]
    assert len(builder.load_components({**spec, "split": False}, path, tmp_path)) == 1
    with pytest.raises(builder.SpecError, match="unknown source format"):
        builder.load_components({"source": {"format": "obj"}}, path, tmp_path)


# --- the command --------------------------------------------------------------------


@pytest.fixture
def board(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A copy of the test board in a repository of its own, where the command may write."""
    root = tmp_path / "repo"
    copy = root / FIXTURE.relative_to(ROOT)
    shutil.copytree(FIXTURE, copy)
    monkeypatch.setattr(paths, "ROOT", root.resolve())
    monkeypatch.setattr(builder, "REPO", root.resolve())
    monkeypatch.chdir(root)
    return copy


def command(board: Path, *options: str) -> list[str]:
    vendor = board / "vendor"
    return [
        str(board / "model" / "spec.json"),
        "--source",
        str(vendor / "body.stl"),
        "--module-source",
        f"base={vendor / 'base.stl'}",
        *options,
    ]


def test_the_command_writes_the_model_and_its_record(
    board: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    model, record = board / "model" / "faces.glb", board / "model" / "source.json"
    built, recorded = model.read_bytes(), json.loads(record.read_text(encoding="utf-8"))
    model.unlink()
    record.unlink()
    assert builder.main(command(board)) == 0
    assert model.read_bytes() == built
    again = json.loads(record.read_text(encoding="utf-8"))
    for where in (recorded, again):
        # the builder's path and versions are this run's, not the copy's
        for key in ("script", "python", "packages"):
            del where["builder"][key]
    assert again == recorded
    assert "and its" not in capsys.readouterr().out


def test_the_command_compares_a_rebuild_with_the_model(
    board: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    model, record = board / "model" / "faces.glb", board / "model" / "source.json"
    record.unlink()
    assert builder.main(command(board, "--check")) == 0
    assert not record.exists()
    assert builder.main(command(board, "--check", "--record")) == 0
    assert record.is_file()
    assert builder.main(command(board, "--check", "--without-legends")) == 0
    assert capsys.readouterr().out.count("is byte-identical to") == 3
    # a model whose case stands elsewhere differs, by as much as it was moved
    js, body = glb_legends.read(model.read_bytes())
    node = next(n for n in js["nodes"] if n.get("name") == "case")
    node["scale"] = [2 * v for v in node["scale"]]
    js["materials"][0]["name"] = "other"
    model.write_bytes(glb_legends.write(js, body))
    assert builder.main(command(board, "--check")) == 1
    assert builder.main(command(board, "--check", "--tolerance-mm", "0.01")) == 1
    said = capsys.readouterr().out
    assert "case: max position deviation" in said and "materials differ" in said


def test_a_rebuild_within_the_tolerance_passes(
    board: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    model = board / "model" / "faces.glb"
    js, body = glb_legends.read(model.read_bytes())
    node = next(n for n in js["nodes"] if n.get("name") == "case")
    node["scale"] = [1.0001 * v for v in node["scale"]]
    model.write_bytes(glb_legends.write(js, body))
    assert builder.main(command(board, "--check")) == 1
    assert builder.main(command(board, "--check", "--tolerance-mm", "0.01")) == 0
    assert "PASS (tolerance 0.01 mm)" in capsys.readouterr().out
    other = board / "model" / "less.glb"
    other.write_bytes(glb_legends.strip(model.read_bytes()))
    assert not builder.compare_glb(model, other, 0.01)
    assert "meshes differ" in capsys.readouterr().out


def test_the_command_writes_another_file_without_a_record(
    board: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    record = board / "model" / "source.json"
    before = record.read_bytes()
    out = tmp_path / "new" / "light.glb"
    assert builder.main(command(board, "--out", str(out))) == 0
    assert out.read_bytes() == (board / "model" / "faces.glb").read_bytes()
    assert "source.json not written" in capsys.readouterr().out
    assert builder.main(command(board, "--out", str(out), "--without-legends")) == 0
    assert not glb_legends.legends(glb_legends.read(out.read_bytes())[0])
    model = board / "model" / "faces.glb"
    assert builder.main(command(board, "--out", str(model), "--without-legends")) == 1
    assert "the whole model" in capsys.readouterr().err
    assert builder.main(command(board, "--no-source-json")) == 0
    assert record.read_bytes() == before


def test_the_command_writes_the_level_the_site_draws(
    board: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every mesh but the prints a reader cannot see at that scale, and the record of both."""
    whole = media_meta.record(f"{FIXTURE.relative_to(ROOT).as_posix()}/model/faces.glb")
    monkeypatch.setattr(media_meta, "record", lambda _path: whole)
    assert builder.main(command(board, "--web-px-per-mm", "2")) == 0
    web = board / "model" / "faces-web.glb"
    written = json.loads((board / "model" / "web.json").read_text(encoding="utf-8"))
    assert written["px_per_mm"] == 2.0 and written["model_bytes"] == web.stat().st_size
    assert written["master"]["model"] == "_shared/fixtures/faces/model/faces.glb"
    names = {m.name for m in model_raster.read_glb(web)}
    everything = {m.name for m in model_raster.read_glb(board / "model" / "faces.glb")}
    assert names < everything and {"case", "base"} <= names
    assert builder.main(command(board, "--web-px-per-mm", "2", "--check")) == 0
    web.write_bytes(web.read_bytes()[:-4] + b"\0\0\0\1")
    assert builder.main(command(board, "--web-px-per-mm", "2", "--check")) == 1
    assert "DIFFER" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("options", "words"),
    [
        (["--web-px-per-mm", "5", "--record"], "takes only --check"),
        (["--web-px-per-mm", "0"], "takes a scale over 0"),
        (["--without-legends"], "needs --out"),
        (["--check", "--without-legends", "--record"], "--record is for the whole model"),
        (["--module-source", "base"], "give NAME=FILE"),
        (["--module-source", "=x"], "give NAME=FILE"),
    ],
)
def test_the_command_refuses_options_that_do_not_go_together(
    board: Path, options: list[str], words: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as stop:
        builder.main(command(board, *options))
    assert stop.value.code == 2
    assert words in capsys.readouterr().err


def test_the_command_takes_only_the_pinned_vendor_file(
    board: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = str(board / "model" / "spec.json")
    assert builder.main([spec, "--source", str(board / "vendor" / "base.stl")]) == 1
    assert "is not the pinned vendor file" in capsys.readouterr().err
    assert builder.main([spec, "--source", str(board / "vendor" / "none.stl")]) == 1
    assert "no such file" in capsys.readouterr().err
    assert builder.main([spec, "--cache", str(board / "cache")]) == 1
    assert "no such file" in capsys.readouterr().err
    assert builder.main([spec, "--cache", str(board / "cache"), "--fetch"]) == 1
    assert "a vendor file is fetched from https" in capsys.readouterr().err


# --- a model of no vendor file ------------------------------------------------------


def own_spec(tmp_path: Path) -> dict[str, Any]:
    """A spec of one block with a screen set in a window, its glass over it, and a blended lid."""
    (tmp_path / "measurements.json").write_text(
        json.dumps(
            {
                "case": {"width": 20, "height": 30, "depth": 5},
                "display": {
                    "active_w_mm": 10,
                    "active_h_mm": 10,
                    "origin_x_mm": 5,
                    "origin_y_mm": 5,
                    "resolution_w_px": 100,
                    "resolution_h_px": 100,
                },
            }
        ),
        encoding="utf-8",
    )
    spec = written_spec()
    for key in ("modules", "transform", "split", "parts"):
        del spec[key]
    spec |= {
        "source": {"format": "none", "license": "MIT", "copyright": "Kleidos"},
        "measurements": "measurements.json",
        "materials": [
            {"name": "case", "hex": "#5a5a5e", "rough": 0.6, "metal": 0.5},
            {"name": "screen", "rgb": [8, 8, 10], "rough": 1.0, "unlit": True},
            {"name": "glass", "rgb": [0, 0, 0], "rough": 0.04, "alpha": 0.06, "double": True},
        ],
        "meshes": [
            {"name": "case", "shapes": [{"box": [0, 20, 0, 30, -5, 0]}], "material": "case"},
            {"name": "screen", "screen": {"z": 0.1}, "material": "screen"},
            {
                "name": "glass",
                "glass": {"rect": [2, 18, 2, 18], "z": 0.2, "frame": "front"},
                "material": "glass",
            },
            {
                "name": "knob",
                "shapes": [{"cylinder": {"axis": "x", "c": [15, -2], "r": 1, "range": [20, 22]}}],
                "material": "case",
                "smooth_deg": 40,
            },
            {
                "name": "holes",
                "shapes": [_grid(at=-5.02, facing=-1, u_center=10, v_center=5)],
                "material": "screen",
            },
        ],
    }
    return spec


def build_own(spec: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return builder.build(builder.load_spec(path), None, tmp_path / "own.glb")


def test_a_model_of_no_vendor_file_is_built_from_its_shapes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    summary = build_own(own_spec(tmp_path), tmp_path)
    assert summary["screen"]["resolution"] == [100, 100] and summary["legends"] == []
    meshes = {m.name: m for m in model_raster.read_glb(tmp_path / "own.glb")}
    assert list(meshes) == ["case", "screen", "glass", "knob", "holes"]
    assert meshes["glass"].alpha == pytest.approx(0.06) and meshes["screen"].unlit
    assert np.ptp(meshes["screen"].positions, axis=0) == pytest.approx((10, 10, 0), abs=1e-6)
    assert "screen clearance: 0.100 mm behind (case), 0.100 mm in front (glass)" in (
        capsys.readouterr().out
    )


@pytest.mark.parametrize(
    ("change", "words"),
    [
        (_set("meshes", "1", "screen", value={"z": 0.004}), "is under|under one quantization step"),
        (_set("meshes", "1", "material", value="none"), "none"),
        (_set("materials", "2", "alpha", value=1.0), "is not above 0"),
        (_set("materials", "0", "name", value="ink_000000"), "is a legend ink's"),
        (_set("source", "file", value="a.stl"), "takes only"),
        (_set("source", "license", value=""), "still states its license"),
        (_set("split", value=True), "there is nothing to cut"),
        (_set("center_mm", value="auto"), "in numbers"),
        (_set("meshes", "4", "name", value="knob"), "mesh names repeat"),
        (_set("unknown", value=1), "unknown key"),
    ],
)
def test_a_spec_that_cannot_be_built_is_refused(
    change: Callable[[dict[str, Any]], None], words: str, tmp_path: Path
) -> None:
    spec = own_spec(tmp_path)
    change(spec)
    with pytest.raises((builder.SpecError, KeyError), match=words):
        build_own(spec, tmp_path)
    assert not (tmp_path / "own.glb").exists()


def test_two_materials_at_one_depth_are_refused(tmp_path: Path) -> None:
    spec = own_spec(tmp_path)
    spec["meshes"].append(
        {"name": "label", "shapes": [{"box": [1, 3, 1, 3, -1, 0]}], "material": "screen"}
    )
    with pytest.raises(builder.SpecError, match="cover one place at one depth"):
        build_own(spec, tmp_path)
    assert not (tmp_path / "own.glb").exists()
