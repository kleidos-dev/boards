# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
#
# fontTools.ttLib.TTFont as _shared/legend_mesh.py reads a font: its character
# map, its glyph set (each glyph drawn into a pen) and its tables by tag.

from collections.abc import Mapping
from os import PathLike
from typing import Any

from fontTools.pens.basePen import BasePen

class _Glyph:
    width: int
    def draw(self, pen: BasePen) -> None: ...

class TTFont:
    def __init__(self, file: str | PathLike[str], *args: Any, **kwargs: Any) -> None: ...
    def getBestCmap(self) -> dict[int, str] | None: ...
    def getGlyphSet(self) -> Mapping[str, _Glyph]: ...
    def __getitem__(self, tag: str) -> Any: ...
