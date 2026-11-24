# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""What the scripts read out of a drawing's text: its numbers, its tags, what lies between marks

Every reader here takes time in proportion to the text it is given, whatever
the text holds.
"""

from __future__ import annotations

import re
from collections.abc import Iterator

#: One number of a path, a list of points or a transform, as SVG writes them.
NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def numbers(text: str) -> list[float]:
    """Every number *text* holds, in order."""
    return [float(found) for found in re.findall(NUMBER, text)]


def tags(text: str, *names: str) -> Iterator[str]:
    """Every start tag of an element named one of *names*, in the order of *text*."""
    for found in re.finditer(rf"<(?:{'|'.join(names)})\b[^<>]*>", text):
        yield found.group(0)


def attributes(tag: str) -> dict[str, str]:
    """The attributes of a start tag.

    Between one double quote and the next the tag alternates a name with its
    ``=`` and a value. A tag that reads otherwise (a single-quoted value, a
    value never closed) is refused, since part of it would be lost.
    """
    pieces = tag.split('"')
    if len(pieces) % 2 == 0:
        raise ValueError(f"a tag whose last value is not closed: {tag[:60]!r}")
    found = {}
    for head, value in zip(pieces[0:-1:2], pieces[1::2], strict=True):
        words = head.rstrip().removesuffix("=").split()
        if not head.rstrip().endswith("=") or not words:
            raise ValueError(f"a tag that holds {head[-60:]!r} where an attribute's name goes")
        found[words[-1]] = value
    return found


def _spans(text: str, opening: str, closing: str) -> Iterator[tuple[int, int]]:
    """Where each piece of *text* from *opening* to the next *closing* starts and ends."""
    end = 0
    while (start := text.find(opening, end)) >= 0:
        end = text.find(closing, start + len(opening))
        if end < 0:
            return
        end += len(closing)
        yield start, end


def between(text: str, opening: str, closing: str) -> list[str]:
    """What lies from each *opening* to the next *closing* after it, the two left out."""
    return [
        text[start + len(opening) : end - len(closing)]
        for start, end in _spans(text, opening, closing)
    ]


def without(text: str, opening: str, closing: str) -> str:
    """*text* less every piece from *opening* to the next *closing* after it."""
    kept, done = [], 0
    for start, end in _spans(text, opening, closing):
        kept.append(text[done:start])
        done = end
    return "".join(kept) + text[done:]


def element_text(text: str, name: str, start: int = 0) -> tuple[str, int] | None:
    """(what the first element named *name* from *start* holds, where it ends), or None."""
    opened = re.compile(rf"<{name}\b[^<>]*>").search(text, start)
    if opened is None:
        return None
    closing = f"</{name}>"
    end = text.find(closing, opened.end())
    if end < 0:
        return None
    return text[opened.end() : end], end + len(closing)
