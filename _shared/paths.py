# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""The repository root every script resolves its paths against, and the check of a path given to one

A path recorded in a file of this repository (``model/source.json``'s
``model``, ``spec`` and ``builder.script``, a spec's ``output``) is relative to
``ROOT``, so a consumer that mounts the repository elsewhere prefixes its own
mount path and nothing here changes.

A path that comes from a command line or from a file that a script reads (a
spec, a record) is checked once, where it comes in, and used as checked:

- ``inside`` resolves it, links included, and refuses it outside the folders
  it may lie in;
- ``in_tree`` is ``inside`` the repository, for a path recorded in one of its
  files;
- ``work_path`` is ``inside`` the repository, the folder the command runs in
  or the folder for temporary files, for a file that a command is given. The
  folder a command runs in is trusted: whoever starts it there means its
  files, and a command started in ``/`` or in a home folder takes any file
  under it. What a data file names is never looked for there;
- ``beside`` is ``inside`` the repository or the board a data file belongs to,
  for a file that it names from its own folder;
- ``board_id`` is one of ``BOARDS``, for a board named on a command line.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

#: The repository root: the folder that holds ``_shared/`` and the boards.
ROOT = Path(__file__).resolve().parents[1]
#: The pinned fonts a legend may be set in (``fonts/VERSIONS.md``).
FONTS = ROOT / "fonts"
#: Every board folder, by its id.
BOARDS = (
    "sticks3",
    "m5stickc-plus2",
    "m5stickc-plus1",
    "m5stickc-plus-se",
    "coreink",
    "cores3-se",
    "m5stack-core2-v13",
    "cardputer",
    "tdeck-plus",
)


class OutsideError(ValueError):
    """A path that leads out of the folders it may lie in, or a board that is none of ``BOARDS``."""


def inside(path: str | os.PathLike[str], *folders: str | os.PathLike[str]) -> Path:
    """*path* with every link resolved, refused unless it lies in one of *folders*."""
    real = os.path.realpath(path)
    tops = list(dict.fromkeys(os.path.realpath(folder) for folder in folders))
    for top in tops:
        # join adds the separator the root folder already ends in
        if real == top or real.startswith(os.path.join(top, "")):
            return Path(real)
    raise OutsideError(f"{path}: leads to {real}, which is not in {' or '.join(tops)}")


def in_tree(path: str | os.PathLike[str]) -> Path:
    """*path*, relative to the repository's root or absolute, refused outside the repository."""
    return inside(ROOT / path, ROOT)


def work_folders() -> tuple[Path, ...]:
    """Where a file that a command is given may lie."""
    return ROOT, Path.cwd(), Path(tempfile.gettempdir())


def work_path(path: str | os.PathLike[str]) -> Path:
    """*path* as a command is given it, refused outside ``work_folders``."""
    return inside(path, *work_folders())


def beside(file: str | os.PathLike[str], path: str | os.PathLike[str]) -> Path:
    """*path* as the data file *file* names it from its own folder.

    Refused outside the repository and the folder of the board *file* belongs
    to: the one that holds ``model/`` when *file* lies in there, its own
    folder otherwise.
    """
    folder = Path(file).parent
    return inside(folder / path, ROOT, folder.parent if folder.name == "model" else folder)


def write_file(path: str | os.PathLike[str], content: bytes | str) -> None:
    """Write *content* to *path*, a path already checked; a text as UTF-8.

    Through an open file, not ``Path.write_bytes`` or ``Path.write_text``:
    SonarCloud's S2083 takes the argument of those two for a path, and what
    was read from a checked model for an unchecked one.
    """
    data = content.encode("utf-8") if isinstance(content, str) else content
    with open(path, "wb") as fh:
        fh.write(data)


def board_id(name: str) -> str:
    """The board of ``BOARDS`` that *name* is, refused when it is none."""
    for board in BOARDS:
        if board == name:
            return board
    raise OutsideError(f"{name!r} is no board; the boards are {', '.join(BOARDS)}")
