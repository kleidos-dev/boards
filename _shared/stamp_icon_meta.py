# SPDX-License-Identifier: MIT
"""Write each board's ``icon.svg`` metadata from its record, or check it

The icons are drawn by hand, so no builder writes them; this script owns the
one part of them that is not drawing: the SPDX comment, the root's accessible
name and the leading ``<title>``, ``<desc>`` and ``<metadata>`` block, written
from the board's ``board.json`` identity and ``REUSE.toml`` by
``media_meta.stamp_svg``. The drawing is never touched.

Usage::

    python -I _shared/stamp_icon_meta.py [BOARD ...] [--check]

With no board, all nine. ``--check`` writes nothing and exits 1 when an icon
is not what its record gives.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_meta
from paths import BOARDS, ROOT


def stamped(board: str) -> tuple[Path, str, str]:
    """(path, the icon as it is, the icon as its record gives it)."""
    path = ROOT / board / "icon.svg"
    text = path.read_text(encoding="utf-8")
    return path, text, media_meta.stamp_svg(text, media_meta.record(f"{board}/icon.svg"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("boards", nargs="*", help="board ids (default: all nine)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 when an icon differs from its record",
    )
    args = parser.parse_args(argv)
    unknown = [b for b in args.boards if b not in BOARDS]
    if unknown:
        parser.error(f"not a board: {', '.join(unknown)}")
    failed = False
    for board in args.boards or BOARDS:
        path, text, want = stamped(board)
        if args.check:
            if text != want:
                print(f"FAIL {board}/icon.svg: its metadata is not what its record gives")
                failed = True
            else:
                print(f"ok   {board}/icon.svg")
            continue
        if text != want:
            path.write_text(want, encoding="utf-8")
        print(f"wrote {board}/icon.svg")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
