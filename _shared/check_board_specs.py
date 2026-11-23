# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Hold every ``<board>/board.json`` to ``_shared/board.schema.json`` and to its sources.

A board's specification says what the board is made of, part by part, and
where each value comes from. This check enforces:

- the schema itself (a small validator for the subset of JSON Schema the
  schema uses, so the check needs nothing beyond the standard library);
- that the file's ``id`` is its folder's name;
- that every ``src`` id, every ``found_via`` and every connection's ``to``
  resolves (a connection reaches a component of the same file, or
  ``external``), and that component ids are unique;
- that every source is an ``https`` address with a real ``checked`` date not
  in the future, except a ``measured`` one, which may have no address and
  must then say how it was measured;
- that the fields ``measurements.json`` still repeats agree with it: the
  vendor, the SKU, and, once the display parts are listed, the display
  controller and the panel's resolution.

A source no value cites is reported, not failed: a file being filled lists
its sources before it cites them. A board folder with no ``board.json`` yet is
reported too.

Usage::

    python3 _shared/check_board_specs.py [BOARD ...]

Exit status 0 when every file checked passes, 1 otherwise.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "_shared" / "board.schema.json"
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

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


# ------------------------------------------------------------- the schema


def _is_type(value: object, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[name])


def _resolve(schema: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    while "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"unsupported $ref {ref}")
        node = root
        for part in ref[2:].split("/"):
            node = node[part]
        schema = {**node, **{k: v for k, v in schema.items() if k != "$ref"}}
    return schema


def validate(
    value: object, schema: dict[str, Any], root: dict[str, Any], where: str = "$"
) -> list[str]:
    """The ways *value* breaks *schema*, as ``path: problem`` lines.

    Supports what ``board.schema.json`` uses: ``$ref`` into ``$defs``,
    ``type``, ``enum``, ``required``, ``properties``, ``additionalProperties``
    (false or a schema), ``propertyNames``, ``items``, ``minItems``,
    ``pattern``, ``minLength``, ``minimum`` and ``exclusiveMinimum``.
    """
    schema = _resolve(schema, root)
    problems: list[str] = []
    kind = schema.get("type")
    if kind is not None:
        kinds = kind if isinstance(kind, list) else [kind]
        if not any(_is_type(value, k) for k in kinds):
            return [f"{where}: expected {' or '.join(kinds)}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        problems.append(f"{where}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            problems.append(f"{where}: empty string")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            problems.append(f"{where}: {value!r} does not match {schema['pattern']}")
    if _is_type(value, "number"):
        if "minimum" in schema and value < schema["minimum"]:
            problems.append(f"{where}: {value} < {schema['minimum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            problems.append(f"{where}: {value} <= {schema['exclusiveMinimum']}")
    if isinstance(value, dict):
        problems.extend(
            f"{where}: missing '{key}'" for key in schema.get("required", []) if key not in value
        )
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, item in value.items():
            if "propertyNames" in schema:
                problems += validate(key, schema["propertyNames"], root, f"{where}.{key}(name)")
            if key in props:
                problems += validate(item, props[key], root, f"{where}.{key}")
            elif extra is False:
                problems.append(f"{where}: unknown property '{key}'")
            elif isinstance(extra, dict):
                problems += validate(item, extra, root, f"{where}.{key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            problems.append(f"{where}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for index, item in enumerate(value):
                problems += validate(item, schema["items"], root, f"{where}[{index}]")
    return problems


def load_schema() -> dict[str, Any]:
    schema: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return schema


# ------------------------------------------------------- the source rules


def _walk_src(node: object, where: str) -> Iterator[tuple[str, list[Any]]]:
    """Every (path, src list) in a document, wherever a ``src`` sits."""
    if isinstance(node, dict):
        for key, item in node.items():
            if key == "src" and isinstance(item, list):
                yield where, item
            elif key != "sources":
                yield from _walk_src(item, f"{where}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from _walk_src(item, f"{where}[{index}]")


def _real_date(text: object) -> _dt.date | None:
    if not isinstance(text, str):
        return None
    try:
        return _dt.date.fromisoformat(text)
    except ValueError:
        return None


def source_problems(doc: dict[str, Any], today: _dt.date) -> tuple[list[str], list[str]]:
    """(problems, notices) of the file's sources and of what cites them."""
    problems: list[str] = []
    sources = doc.get("sources", {}) if isinstance(doc.get("sources"), dict) else {}
    cited: set[str] = set()
    for where, ids in _walk_src(doc, "$"):
        for source_id in ids:
            cited.add(source_id)
            if source_id not in sources:
                problems.append(f"{where}.src: '{source_id}' is not in sources")
    for source_id, source in sources.items():
        if not isinstance(source, dict):
            continue
        where = f"$.sources.{source_id}"
        url = source.get("url")
        if url is None and source.get("kind") != "measured":
            problems.append(f"{where}: no url (only a measured source may have none)")
        if url is not None and not str(url).startswith("https://"):
            problems.append(f"{where}: url is not https")
        if source.get("kind") == "measured" and not source.get("method"):
            problems.append(f"{where}: a measured source says how it was measured (method)")
        checked = _real_date(source.get("checked"))
        if checked is None:
            problems.append(f"{where}: checked {source.get('checked')!r} is not a real date")
        elif checked > today:
            problems.append(f"{where}: checked {checked} is in the future")
        via = source.get("found_via")
        if via is not None:
            if via not in sources:
                problems.append(f"{where}: found_via '{via}' is not in sources")
            elif via == source_id:
                problems.append(f"{where}: found_via names itself")
            else:
                cited.add(via)
    notices = [
        f"$.sources.{source_id}: not cited yet" for source_id in sources if source_id not in cited
    ]
    return problems, notices


def component_problems(doc: dict[str, Any]) -> list[str]:
    """Unique component ids, and every connection reaching one of them."""
    problems: list[str] = []
    components = [c for c in doc.get("components", []) if isinstance(c, dict)]
    ids = [str(c.get("id")) for c in components]
    problems.extend(
        f"$.components: id '{repeated}' is used twice"
        for repeated in sorted({i for i in ids if ids.count(i) > 1})
    )
    known = set(ids) | {"external"}
    for index, component in enumerate(components):
        for link_index, link in enumerate(component.get("connects_to", [])):
            if isinstance(link, dict) and link.get("to") not in known:
                problems.append(
                    f"$.components[{index}].connects_to[{link_index}]: "
                    f"'{link.get('to')}' is no component of this file"
                )
            if isinstance(link, dict) and link.get("to") == component.get("id"):
                problems.append(
                    f"$.components[{index}].connects_to[{link_index}]: "
                    "a component connected to itself"
                )
    return problems


# ------------------------------------------- what measurements.json repeats


def measurement_problems(doc: dict[str, Any], measured: dict[str, Any]) -> list[str]:
    """The fields both files hold must agree."""
    problems: list[str] = []
    identity = doc.get("identity", {})
    problems.extend(
        f"$.identity.{field}: {identity[field]!r} but measurements.json says {measured[field]!r}"
        for field in ("vendor", "sku")
        if field in identity and field in measured and identity[field] != measured[field]
    )
    display = measured.get("display", {})
    for component in doc.get("components", []):
        if not isinstance(component, dict):
            continue
        role = component.get("role")
        if (
            role == "display_controller"
            and "part" in component
            and display.get("controller")
            and component["part"].lower() != str(display["controller"]).lower()
        ):
            problems.append(
                f"display controller {component['part']!r} but "
                f"measurements.json says {display['controller']!r}"
            )
        if role == "display_panel":
            resolution = (component.get("specs") or {}).get("resolution_px")
            wanted = (display.get("resolution_w_px"), display.get("resolution_h_px"))
            if (
                resolution is not None
                and None not in wanted
                and sorted(resolution) != sorted(wanted)
            ):
                problems.append(
                    f"panel resolution {resolution} but measurements.json says {list(wanted)}"
                )
    return problems


# --------------------------------------------------------------- the check


def check_document(
    doc: dict[str, Any],
    board: str,
    measured: dict[str, Any] | None,
    schema: dict[str, Any] | None = None,
    today: _dt.date | None = None,
) -> tuple[list[str], list[str]]:
    """(problems, notices) of one board.json already parsed."""
    schema = schema or load_schema()
    today = today or _dt.datetime.now(_dt.UTC).date()
    problems = validate(doc, schema, schema)
    if doc.get("id") != board:
        problems.append(f"$.id: {doc.get('id')!r} is not the folder name {board!r}")
    found, notices = source_problems(doc, today)
    problems += found + component_problems(doc)
    if measured is not None:
        problems += measurement_problems(doc, measured)
    return problems, notices


def check_board(board: str, root: Path = ROOT) -> tuple[list[str], list[str]] | None:
    """(problems, notices) of ``<board>/board.json``, or None when it has none yet."""
    path = root / board / "board.json"
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"not JSON: {error}"], []
    measured_path = root / board / "measurements.json"
    measured = (
        json.loads(measured_path.read_text(encoding="utf-8")) if measured_path.is_file() else None
    )
    return check_document(doc, board, measured)


def main(argv: list[str]) -> int:
    boards = argv or list(BOARDS)
    unknown = [b for b in boards if b not in BOARDS]
    if unknown:
        print(f"unknown board(s): {', '.join(unknown)}", file=sys.stderr)
        return 2
    failed = False
    for board in boards:
        result = check_board(board)
        if result is None:
            print(f"--   {board}: no board.json yet")
            continue
        problems, notices = result
        print(f"{'FAIL' if problems else 'ok  '} {board}/board.json")
        for line in problems:
            print(f"       {line}")
        for line in notices:
            print(f"       note: {line}")
        failed = failed or bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
