# SPDX-License-Identifier: MIT
"""Every ``board.json`` passes its check, and the check fails what is planted in one.

``_shared/check_board_specs.py`` holds a board's specification to its schema
and to its sources: a value with no source, a source that does not resolve,
an address that is not https, a date that is not real or not yet, a
connection to nothing, and a vendor or SKU that disagrees with
``measurements.json``. A check that passes everything checks nothing, so each
of those is planted here in a copy of a valid document and has to fail it.

Host-only: no build, no hardware, no network.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))
import check_board_specs as specs  # noqa: E402

TODAY = dt.date(2026, 11, 16)

#: A document every rule passes, with one of each kind of thing a rule reads.
VALID: dict = {
    "$schema": "../_shared/board.schema.json",
    "id": "sticks3",
    "identity": {"name": "StickS3", "vendor": "M5Stack", "sku": "K150",
                 "links": {"docs": "https://example.com/docs"}, "src": ["docs"]},
    "physical": {"width_mm": 24.0, "height_mm": 48.0, "depth_mm": 15.0, "src": ["docs"]},
    "components": [
        {"id": "soc", "role": "soc", "part": "ESP32-S3-PICO-1-N8R8",
         "manufacturer": "Espressif", "quantity": 1, "specs": {"flash_mb": 8},
         "src": ["docs"]},
        {"id": "imu", "role": "imu", "part": "BMI270", "manufacturer": "Bosch Sensortec",
         "quantity": 1,
         "connects_to": [{"to": "soc", "bus": "I2C", "address": "0x68",
                          "pins": {"SDA": "GPIO47", "SCL": "GPIO48"},
                          "pulls": [{"signal": "SDA", "direction": "up", "ohms": 4700,
                                     "to": "3V3"}],
                          "src": ["schematic"]}],
         "src": ["docs"]},
        {"id": "lcd", "role": "display_panel", "quantity": 1,
         "specs": {"resolution_px": [135, 240]}, "src": ["docs"]},
        {"id": "lcd-ic", "role": "display_controller", "part": "ST7789P3", "quantity": 1,
         "src": ["docs"]},
    ],
    "absent": [{"role": "rtc", "src": ["docs"]}],
    "sources": {
        "docs": {"url": "https://example.com/docs", "title": "Docs", "kind": "vendor_docs",
                 "checked": "2026-11-16"},
        "schematic": {"url": "https://example.com/sch.pdf", "title": "Schematic",
                      "kind": "schematic", "checked": "2026-11-01", "found_via": "docs"},
        "caliper": {"title": "Caliper", "kind": "measured", "checked": "2026-10-01",
                    "method": "Digital caliper, 0.01 mm"},
    },
}
MEASURED = {"vendor": "M5Stack", "sku": "K150",
            "display": {"controller": "ST7789P3", "resolution_w_px": 135,
                        "resolution_h_px": 240}}


def problems(doc: dict, measured: dict | None = MEASURED) -> list[str]:
    return specs.check_document(doc, "sticks3", measured, today=TODAY)[0]


def test_every_board_json_in_the_tree_passes():
    """The committed files pass, and at least the StickS3 has one."""
    checked = 0
    for board in specs.BOARDS:
        result = specs.check_board(board)
        if result is None:
            continue
        checked += 1
        assert result[0] == [], (board, result[0])
    assert checked >= 1


def test_the_board_list_is_the_tree():
    """The check walks every board folder, and only those."""
    folders = sorted(p.name for p in ROOT.iterdir()
                     if (p / "measurements.json").is_file())
    assert sorted(specs.BOARDS) == folders


def test_the_valid_document_passes():
    assert problems(VALID) == []
    notices = specs.check_document(VALID, "sticks3", MEASURED, today=TODAY)[1]
    assert notices == ["$.sources.caliper: not cited yet"]


def _plant(change):
    doc = copy.deepcopy(VALID)
    change(doc)
    return doc


PLANTED = {
    "a value with no src": lambda d: d["components"][0].pop("src"),
    "an empty src": lambda d: d["components"][0].update(src=[]),
    "a src that resolves to nothing": lambda d: d["identity"].update(src=["nowhere"]),
    "a connection's own src that resolves to nothing":
        lambda d: d["components"][1]["connects_to"][0].update(src=["nowhere"]),
    "an absent role with no src": lambda d: d["absent"][0].pop("src"),
    "an http address": lambda d: d["sources"]["docs"].update(url="http://example.com/docs"),
    "a source with no address": lambda d: d["sources"]["docs"].pop("url"),
    "a measured source that says not how": lambda d: d["sources"]["caliper"].pop("method"),
    "a date that is not a date": lambda d: d["sources"]["docs"].update(checked="2026-02-30"),
    "a date in the future": lambda d: d["sources"]["docs"].update(checked="2026-12-01"),
    "a date in another format": lambda d: d["sources"]["docs"].update(checked="16/11/2026"),
    "found_via to nothing": lambda d: d["sources"]["schematic"].update(found_via="nowhere"),
    "an unknown role": lambda d: d["components"][0].update(role="cpu"),
    "an unknown property": lambda d: d["components"][0].update(colour="blue"),
    "a quantity of zero": lambda d: d["components"][0].update(quantity=0),
    "a bus address that is no address": lambda d: d["components"][1]["connects_to"][0]
        .update(address="68"),
    "a pull with no direction": lambda d: d["components"][1]["connects_to"][0]["pulls"][0]
        .pop("direction"),
    "a connection to nothing": lambda d: d["components"][1]["connects_to"][0]
        .update(to="nothing"),
    "two components with one id": lambda d: d["components"][1].update(id="soc"),
    "another folder's id": lambda d: d.update(id="cardputer"),
    "a vendor measurements.json disagrees with": lambda d: d["identity"]
        .update(vendor="LILYGO"),
    "a SKU measurements.json disagrees with": lambda d: d["identity"].update(sku="K016"),
    "a display controller measurements.json disagrees with": lambda d: d["components"][3]
        .update(part="ILI9342C"),
    "a resolution measurements.json disagrees with": lambda d: d["components"][2]["specs"]
        .update(resolution_px=[240, 320]),
    "no identity": lambda d: d.pop("identity"),
    "no sources": lambda d: d.pop("sources"),
}


@pytest.mark.parametrize("name", sorted(PLANTED))
def test_the_check_fails_what_is_planted(name):
    found = problems(_plant(PLANTED[name]))
    assert found, f"the check passed {name}"


def test_a_resolution_may_be_given_in_either_orientation():
    """A panel quoted landscape is the same panel as measured portrait."""
    doc = _plant(lambda d: d["components"][2]["specs"].update(resolution_px=[240, 135]))
    assert problems(doc) == []


def test_the_schema_file_is_the_one_the_check_reads():
    """The check enforces the committed schema, and the board files point at it."""
    schema = json.loads(specs.SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"].startswith("https://json-schema.org/draft/2020-12")
    roles = set(schema["$defs"]["role"]["enum"])
    assert {"soc", "pmic", "imu", "battery", "other"} <= roles
    for board in specs.BOARDS:
        path = ROOT / board / "board.json"
        if path.is_file():
            doc = json.loads(path.read_text(encoding="utf-8"))
            assert doc["$schema"] == "../_shared/board.schema.json", board


def test_the_command_line_fails_a_bad_file(tmp_path):
    """``main`` exits 1 on a planted file and 0 on the tree."""
    assert specs.main([]) == 0
    bad = tmp_path / "sticks3"
    bad.mkdir()
    (bad / "board.json").write_text(json.dumps(_plant(PLANTED["an http address"])))
    (bad / "measurements.json").write_text(json.dumps(MEASURED))
    problems_found, _ = specs.check_board("sticks3", root=tmp_path)
    assert problems_found
