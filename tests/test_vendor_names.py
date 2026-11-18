# SPDX-License-Identifier: MIT
"""Vendor names spelled as the boards print them.

The T-Deck Plus's vendor is written ``LILYGO``, as its case prints it
(``LILYGO®``), in every file of the tree (owner, 2026-11-17): prose, data,
drawings, schematics, models. What is not ours to spell keeps its own form:
an address (``https://wiki.lilygo.cc/...``, the GitHub organization in
``https://github.com/<org>/...``), the organization's name itself, and this
project's lowercase identifiers (``lilygo-wiki``, ``lilygo-glass``). Any other
mixed-case spelling fails. The planted spellings are assembled here from
pieces, so this file holds none of them itself.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))

import check_public_tree

#: The vendor's name in its two allowed forms: as printed, and as an identifier.
ALLOWED = {"LILYGO", "lilygo"}
#: The GitHub organization that publishes the vendor's repositories, a third-party name.
ORGANIZATION = "Xinyuan-" + "Lily" + "GO"
NAME = re.compile(r"lilygo", re.IGNORECASE)
ADDRESS = re.compile(r"(?:https?://|www\.)[^\s<>()\"'`|\]]+")


def misspellings(text: str) -> list[str]:
    """Every vendor name in *text* outside an address or the organization's name, spelled neither way allowed."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        bare = ADDRESS.sub(" ", line).replace(ORGANIZATION, " ")
        found += [f"line {number}: {m.group(0)}" for m in NAME.finditer(bare) if m.group(0) not in ALLOWED]
    return found


def test_the_tree_spells_the_vendor_as_the_board_prints_it():
    found = []
    for path in check_public_tree.tracked(ROOT):
        if not path.is_file():
            continue
        # latin-1 reads every byte, so a binary's embedded strings (a GLB's JSON chunk) are read too
        text = path.read_bytes().decode("latin-1")
        found += [f"{path.relative_to(ROOT)}: {hit}" for hit in misspellings(text)]
    assert found == []


@pytest.mark.parametrize("spelling", ["Lily" + "GO", "Lily" + "go", "Lily" + "Go", "lily" + "GO"])
def test_a_mixed_case_spelling_is_caught(spelling):
    assert len(misspellings(f"Measured on {spelling}'s photo.\n")) == 1


@pytest.mark.parametrize("line", [
    "LILYGO T-Deck Plus, as printed: LILYGO®.",
    "[docs](https://wiki.lilygo.cc/products/t-deck-series/t-deck-plus/)",
    "<https://github.com/" + ORGANIZATION + "/T-Deck/blob/master/shell/T-Deck-Plus-Shell.stp>",
    '"url": "https://raw.githubusercontent.com/' + ORGANIZATION + '/documentation/master/x.jpg"',
    "The vendor's organization on GitHub is " + ORGANIZATION + ".",
    '"src": ["lilygo-wiki", "lilygo-spec-image"]',
    '<g class="legend" data-mark="lilygo-glass" data-plane="glass">',
])
def test_an_address_an_identifier_and_the_printed_name_pass(line):
    assert misspellings(line) == []
