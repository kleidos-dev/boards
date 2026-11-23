# SPDX-License-Identifier: MIT
"""The repository root every script resolves its paths against.

A path recorded in a file of this repository (``model/source.json``'s
``model``, ``spec`` and ``builder.script``, a spec's ``output``) is relative to
``ROOT``, so a consumer that mounts the repository elsewhere prefixes its own
mount path and nothing here changes.
"""

from __future__ import annotations

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
