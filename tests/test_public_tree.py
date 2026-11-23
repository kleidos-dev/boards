# SPDX-License-Identifier: MIT
"""``_shared/check_public_tree.py`` on the tree and on planted private lines.

The tree itself must pass. Each kind of private line (``AGENTS.md``, "Nothing
private") is then planted in an empty scratch folder and must be caught,
and the things that look like one and are not must pass. The planted strings
are assembled here from pieces, so this file holds none of them itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))

import check_public_tree


def glue(separator: str, *pieces: str) -> str:
    """*pieces* joined, so that no planted value is written out in this file."""
    return separator.join(pieces)


PLANTED = {
    "a serial-port device path (macOS)": glue("/", "", "dev", "cu.usbserial-5A7A0123"),
    "a serial-port device path (Linux)": glue("/", "", "dev", "ttyACM0"),
    "a MAC address": glue(":", "3C", "8A", "1F", "0B", "22", "E4"),
    "a private IPv4 address (192.168)": glue(".", "192", "168", "1", "37"),
    "a private IPv4 address (10)": glue(".", "10", "0", "0", "12"),
    "a private IPv4 address (172.16)": glue(".", "172", "20", "3", "4"),
    "a home-directory path (macOS)": glue("/", "", "Users", "someone", "boards"),
    "a home-directory path (Linux)": glue("/", "", "home", "someone", "boards"),
    "an e-mail address other than the project's": glue("@", "someone", "example.org"),
}
HARMLESS = [
    f"Signed as {check_public_tree.PROJECT_EMAIL}.",
    "KiCad 10.0.7, numpy 2.3.4, a part rated 10.5 V.",
    "SHA-256 20ef9043e2ff0bc7814d2ba48481561116109880569b35a2ca9cff18b745467f.",
    "The port is found by its USB ID, 0403:6001; the time read 12:34:56.",
    glue("@", "uses: actions/checkout", "0123456789abcdef0123456789abcdef01234567  # v7.0.1"),
    "The cache is ~/.cache/kleidos-cad/ unless $KLEIDOS_CAD_CACHE names another.",
    "A public address, 8.8.8.8, and a version, 1.2.3.4.",
]


def test_the_tree_holds_nothing_private_and_no_vendor_file():
    assert check_public_tree.findings(ROOT) == []


@pytest.mark.parametrize("kind", sorted(PLANTED))
@pytest.mark.parametrize(
    "name", ["bench/2026-11-17-probe.md", "board.json", "netlist.yaml", "tool.py"]
)
def test_a_planted_private_line_is_caught(tmp_path, kind, name):
    path = tmp_path / "board" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"first line\nread on {PLANTED[kind]} today\n", encoding="utf-8")
    found = check_public_tree.findings(tmp_path)
    assert len(found) == 1, found
    assert found[0].startswith(f"board/{name}:2: ")
    assert found[0].endswith(kind.split(" (")[0])
    assert PLANTED[kind] not in found[0], "a finding must not repeat the private value"


def test_what_only_looks_private_passes(tmp_path):
    (tmp_path / "notes.md").write_text("\n".join(HARMLESS) + "\n", encoding="utf-8")
    assert check_public_tree.findings(tmp_path) == []


def test_license_texts_and_drawings_are_not_read_for_private_lines(tmp_path):
    line = "contact " + glue("@", "someone", "example.org") + "\n"
    (tmp_path / "LICENSES").mkdir()
    (tmp_path / "LICENSES" / "Some-License.txt").write_text(line, encoding="utf-8")
    (tmp_path / "front.svg").write_text(f"<svg><!-- {line} --></svg>\n", encoding="utf-8")
    assert check_public_tree.findings(tmp_path) == []


def test_root_license_is_the_mit_text():
    """``LICENSE``, the file GitHub reads a repository's license from, is the
    MIT text ``REUSE.toml`` points at, byte for byte."""
    assert (ROOT / "LICENSE").read_bytes() == (ROOT / "LICENSES" / "MIT.txt").read_bytes()


def test_a_board_model_obj_and_mtl_pass_only_beside_its_own_glb(tmp_path):
    """``<board>/model/<board>.obj`` and ``.mtl`` beside its GLB and spec: ours; any other OBJ: not."""
    model = tmp_path / "board" / "model"
    model.mkdir(parents=True)
    for name in ("board.obj", "board.mtl"):
        (model / name).write_text("# exported\n", encoding="utf-8")
    # no GLB and no spec beside them yet: a CAD file from somewhere else
    assert sorted(check_public_tree.findings(tmp_path)) == [
        "board/model/board.mtl: a vendor file type (.mtl)",
        "board/model/board.obj: a vendor file type (.obj)",
    ]
    (model / "board.glb").write_bytes(b"glTF")
    (model / "spec.json").write_text("{}\n", encoding="utf-8")
    assert check_public_tree.findings(tmp_path) == []
    # another name, another folder, or a vendor folder are still refused
    (model / "case.obj").write_text("# vendor\n", encoding="utf-8")
    (tmp_path / "board" / "case.mtl").write_text("# vendor\n", encoding="utf-8")
    (tmp_path / "board" / "board.obj").write_text("# vendor\n", encoding="utf-8")
    assert sorted(check_public_tree.findings(tmp_path)) == [
        "board/board.obj: a vendor file type (.obj)",
        "board/case.mtl: a vendor file type (.mtl)",
        "board/model/case.obj: a vendor file type (.obj)",
    ]


def test_a_banner_copy_with_embedded_screens_is_refused(tmp_path):
    """The README banner is read from social by its address: a copy in the tree that embeds pictures is refused, wherever it lands."""
    readme = tmp_path / ".github" / "readme"
    readme.mkdir(parents=True)
    (readme / "banner-dark.svg").write_text(
        '<svg><image href="data:image/png;base64,AA=="/></svg>\n', encoding="utf-8"
    )
    assert check_public_tree.findings(tmp_path) == [
        ".github/readme/banner-dark.svg: holds '<image\\\\b'",
        ".github/readme/banner-dark.svg: holds 'data:image'",
    ]
