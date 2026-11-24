# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""A path a script is given is checked where it comes in, and leads nowhere else.

``_shared/paths.py`` resolves a path and refuses it outside the folders it may
lie in. Every command that takes a file or a board is held to it here: a path
that leads out (by ``..``, by a link, by its own beginning) ends the command
with a usage error before anything is read or written.

Host-only: no build, no hardware, no network.
"""

from __future__ import annotations

import importlib
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))
import paths  # noqa: E402  after the sys.path set-up above

FIXTURE = ROOT / "_shared" / "fixtures" / "faces"
#: A path in none of the work folders, whatever the machine: it is never opened.
OUTSIDE = "/nowhere-of-kleidos/file"
#: The arguments of the cases below that must be refused, as they are written there.
_PLANTED = {"OUT", "base=OUT", "nothing", "../sticks3"}


def test_a_path_in_the_folder_is_given_back_resolved(tmp_path: Path) -> None:
    folder = tmp_path / "in"
    (folder / "sub").mkdir(parents=True)
    real = folder.resolve()
    assert paths.inside(folder / "a.txt", folder) == real / "a.txt"
    assert paths.inside(folder / "sub" / ".." / "b.txt", folder) == real / "b.txt"
    assert paths.inside(str(folder / "sub"), tmp_path / "other", folder) == real / "sub"
    assert paths.inside(folder, folder) == real
    assert paths.inside("/etc", "/") == Path("/etc").resolve()


def test_a_path_that_leads_out_is_refused(tmp_path: Path) -> None:
    folder = tmp_path / "in"
    folder.mkdir()
    (tmp_path / "in-a-sibling").mkdir()
    (folder / "link").symlink_to(tmp_path)
    for path in (
        folder / ".." / "file",  # up and out
        tmp_path / "in-a-sibling" / "file",  # a folder whose name only begins alike
        folder / "link" / "file",  # through a link
        Path("/"),
        Path(OUTSIDE),
    ):
        with pytest.raises(paths.OutsideError, match="which is not in"):
            paths.inside(path, folder)
    with pytest.raises(paths.OutsideError):
        paths.inside(folder / "file")  # no folder at all


def test_a_recorded_path_stays_in_the_repository() -> None:
    assert paths.in_tree("sticks3/model/sticks3.glb") == ROOT / "sticks3/model/sticks3.glb"
    assert paths.in_tree(ROOT / "README.md") == ROOT / "README.md"
    for path in ("../brand/README.md", "sticks3/../../x", OUTSIDE, tempfile.gettempdir()):
        with pytest.raises(paths.OutsideError):
            paths.in_tree(path)


def test_a_command_works_in_the_repository_its_folder_and_the_temporary_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert paths.work_folders() == (ROOT, Path.cwd(), Path(tempfile.gettempdir()))
    assert paths.work_path("out.glb") == tmp_path.resolve() / "out.glb"
    assert paths.work_path(ROOT / "README.md") == ROOT / "README.md"
    temporary = Path(tempfile.gettempdir()).resolve()
    assert paths.work_path(temporary / "x" / "y.pdf") == temporary / "x" / "y.pdf"
    with pytest.raises(paths.OutsideError):
        paths.work_path(OUTSIDE)


def test_what_a_data_file_names_lies_in_the_repository_or_with_its_board(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Not in the folder the command runs in, and not anywhere under the temporary one."""
    monkeypatch.chdir(tmp_path)
    board = tmp_path.resolve() / "board"
    spec = board / "model" / "spec.json"
    assert paths.beside(spec, "../svg/front.svg") == board / "svg" / "front.svg"
    assert paths.beside(spec, "faces-web.glb") == board / "model" / "faces-web.glb"
    assert paths.beside(spec, ROOT / "README.md") == ROOT / "README.md"
    assert paths.beside(board / "spec.json", "a.json") == board / "a.json"
    for file, path in (
        (spec, "../../front.svg"),
        (spec, tmp_path / "front.svg"),
        (spec, OUTSIDE),
        (board / "spec.json", "../front.svg"),
    ):
        with pytest.raises(paths.OutsideError):
            paths.beside(file, path)


def test_a_checked_path_is_written_as_given(tmp_path: Path) -> None:
    out = tmp_path / "out"
    paths.write_file(out, b"\x00\r\n")
    assert out.read_bytes() == b"\x00\r\n"
    paths.write_file(out, "José\n")
    assert out.read_bytes() == "José\n".encode()


def test_a_board_is_one_of_the_boards() -> None:
    for board in paths.BOARDS:
        assert paths.board_id(board) == board
    for name in ("", "Sticks3", "../sticks3", "sticks3/", "--help"):
        with pytest.raises(paths.OutsideError, match="is no board"):
            paths.board_id(name)


@pytest.mark.parametrize(
    ("module", "argv"),
    [
        ("check_metadata", ["OUT"]),
        ("build_board_glb", ["OUT"]),
        ("build_board_glb", ["SPEC", "--source", "OUT"]),
        ("build_board_glb", ["SPEC", "--module-source", "base=OUT", "--source", "STL"]),
        ("build_board_glb", ["SPEC", "--cache", "OUT"]),
        ("build_board_glb", ["SPEC", "--out", "OUT"]),
        ("check_board_model", ["OUT"]),
        ("check_board_model", ["FIXTURE", "--glb", "OUT"]),
        ("check_board_model", ["FIXTURE", "--out", "OUT"]),
        ("legend_placement", ["OUT"]),
        ("legend_placement", ["FIXTURE", "--glb", "OUT"]),
        ("legend_placement", ["FIXTURE", "--json", "OUT"]),
        ("glb_legends", ["list", "OUT"]),
        ("glb_legends", ["strip", "GLB", "OUT"]),
        ("legend_source", ["OUT"]),
        ("models_contact_sheet", ["--out", "OUT"]),
        ("check_schematic", ["nothing"]),
        ("check_schematic", ["sticks3", "--netlist", "OUT"]),
        ("check_schematic_links", ["nothing"]),
        ("check_schematic_links", ["sticks3", "--pdf", "OUT"]),
        ("export_schematic", ["nothing"]),
        ("export_schematic", ["sticks3", "--out", "OUT"]),
        ("kicad_schematic", ["../sticks3"]),
        ("schematic_pdf", ["../sticks3", "PDF"]),
        ("schematic_pdf", ["sticks3", "OUT"]),
        ("export_obj", ["../sticks3"]),
        ("emit_board_readme", ["../sticks3"]),
        ("stamp_icon_meta", ["../sticks3"]),
        ("emit_front_svg", ["../sticks3"]),
        ("emit_back_svg", ["../sticks3"]),
    ],
)
def test_a_command_refuses_a_path_or_a_board_that_leads_out(
    module: str, argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Every argument that names a file or a board, planted one at a time."""
    given = {
        "OUT": OUTSIDE,
        "SPEC": str(FIXTURE / "model" / "spec.json"),
        "STL": str(FIXTURE / "vendor" / "body.stl"),
        "GLB": str(FIXTURE / "model" / "faces.glb"),
        "FIXTURE": str(FIXTURE),
        "PDF": str(ROOT / "sticks3" / "schematic" / "sticks3.pdf"),
        "base=OUT": f"base={OUTSIDE}",
    }
    command = importlib.import_module(module)
    try:
        code = command.main([given.get(arg, arg) for arg in argv])
    except SystemExit as stop:
        code = stop.code
    assert code in (1, 2)
    said = "".join(capsys.readouterr())
    planted = next(given.get(arg, arg).removeprefix("base=") for arg in argv if arg in _PLANTED)
    assert planted in said
    # refused for where it leads, before anything looks for the file
    words = ["which is not in"] if planted == OUTSIDE else ["board", "device id"]
    assert any(word in said for word in words), said
    assert not Path(OUTSIDE).parent.exists()
