# SPDX-License-Identifier: MIT
"""Every board's ``README.md`` is what ``_shared/emit_board_readme.py`` writes from its
``board.json``.

The page is a reading of the specification and nothing else, one layout for
all nine boards: a page edited by hand, or a ``board.json`` changed without
the page being written again, fails here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))

import emit_board_readme  # noqa: E402

BOARDS = emit_board_readme.boards()


def test_every_board_folder_has_a_page() -> None:
    assert len(BOARDS) == 9
    for board in BOARDS:
        assert (ROOT / board / "README.md").is_file(), f"{board}: no README.md"


@pytest.mark.parametrize("board", BOARDS)
def test_the_page_is_what_board_json_writes(board: str) -> None:
    page = (ROOT / board / "README.md").read_text(encoding="utf-8")
    assert page == emit_board_readme.render(board), (
        f"{board}/README.md differs from what its board.json writes: "
        f"run python3 _shared/emit_board_readme.py {board}"
    )


@pytest.mark.parametrize("board", BOARDS)
def test_the_page_cites_every_source_and_names_every_part(board: str) -> None:
    data = json.loads((ROOT / board / "board.json").read_text(encoding="utf-8"))
    page = emit_board_readme.render(board)
    for n, sid in enumerate(data["sources"], start=1):
        assert f"\n{n}. " in page and f"(`{sid}`)" in page, f"{board}: source {sid} is not listed"
    for comp in data["components"]:
        if comp.get("part"):
            assert comp["part"] in page, f"{board}: {comp['part']} is not on the page"


def test_a_changed_board_json_changes_the_page() -> None:
    board = BOARDS[0]
    data = json.loads((ROOT / board / "board.json").read_text(encoding="utf-8"))
    data["identity"]["name"] = data["identity"]["name"] + " (planted)"
    page = "\n".join(emit_board_readme.Page(board, data).lines())
    assert "(planted)" in page
    assert page.rstrip("\n") + "\n" != (ROOT / board / "README.md").read_text(encoding="utf-8")


def test_the_check_mode_fails_a_stale_page(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    board = BOARDS[0]
    (tmp_path / board).mkdir()
    (tmp_path / board / "board.json").write_bytes((ROOT / board / "board.json").read_bytes())
    (tmp_path / board / "README.md").write_text("edited by hand\n", encoding="utf-8")
    monkeypatch.setattr(emit_board_readme, "ROOT", tmp_path)
    assert emit_board_readme.main(["--check", board]) == 1
    assert (tmp_path / board / "README.md").read_text(encoding="utf-8") == "edited by hand\n"
    assert emit_board_readme.main([board]) == 0
    assert emit_board_readme.main(["--check", board]) == 0
