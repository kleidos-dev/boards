# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Hold every published media file to its embedded-metadata record

Each tracked image, drawing, model and schematic carries the metadata
``media_meta.record`` derives for its path, written by the builder that
writes the file (``docs/models-and-drawings.md``, "Embedded metadata"). This
check reads every one back and fails on:

- ``M001`` a required field missing; ``M002`` a field other than the record
  gives; ``M003`` a license or holder other than ``REUSE.toml`` states;
- ``M004`` private data in a metadata value (an e-mail address, a local path,
  a host or network address, a machine date, a tool or version string, an
  identity pattern); the matched text of an identity pattern is never printed;
- ``M005`` a container, chunk, key or namespace outside the profile;
  ``M006`` a format or order error; ``M007`` two slots of one fact that
  disagree (a PNG text chunk and its XMP, a PDF's Info and its XMP, a model's
  extras and its packet);
- ``M008`` a media file with neither a record nor an exemption below;
  ``M009`` the wrong profile for a picture's size; ``M010`` a Spanish file
  without its Spanish values, or with a banned term; ``M011`` a text file's
  metadata outside REUSE's ignore markers; ``M012`` a picture with no IPTC
  digital source type.

The identity patterns are not in this public file: they are read from
``_shared/deny-local.txt`` (untracked) or from the ``KLEIDOS_DENY_EXTRA``
environment variable (CI's comes from the repository secret of that name),
one regular expression a line. With ``--require-identity`` a missing list is
a failure; otherwise a warning.

Needs the standard library, and pypdf for the PDFs.

Usage::

    python -I _shared/check_metadata.py [--json] [--require-identity] [PATH ...]

Exit 0 clean, 1 on a finding, 2 on a usage or internal error.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import struct
import subprocess
import sys
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_meta as mm

ROOT = mm.ROOT
MEDIA = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".avif",
    ".gif",
    ".svg",
    ".pdf",
    ".mp4",
    ".webm",
    ".mkv",
    ".glb",
    ".gltf",
    ".obj",
    ".mtl",
    ".ico",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".stl",
    ".ksm",
    ".wav",
    ".mp3",
    ".vtt",
    ".srt",
}
#: Media files that carry no record, each with the reason.
EXEMPT = (
    (
        "fonts/inter/*",
        "third-party font, unmodified and pinned by SHA-256 in "
        "fonts/VERSIONS.md; its own name table states its copyright and license",
    ),
    (
        "_shared/fixtures/faces/vendor/*.stl",
        "test data: the checks' two boxes, written byte for byte by face_fixture.py",
    ),
    (
        "_shared/fixtures/faces/svg/*.svg",
        "test data: the checks' drawings, written byte for byte by face_fixture.py",
    ),
)
GLTF_ASSET_KEYS = {"version", "generator", "copyright", "extensions", "extras"}
PNG_ALLOWED = {
    b"IHDR",
    b"PLTE",
    b"tRNS",
    b"gAMA",
    b"cHRM",
    b"sRGB",
    b"iCCP",
    b"pHYs",
    b"sBIT",
    b"bKGD",
    b"tEXt",
    b"iTXt",
    b"IDAT",
    b"IEND",
}
ES_BANNED = re.compile(r"b[oó]veda|\bvault\b", re.I)
#: The vendor's name in any spelling; only the one the boards print passes.
VENDOR_ANY_CASE = re.compile("lilygo", re.I)


def tracked() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout
        return [n for n in out.decode("utf-8").split("\0") if n]
    except OSError, subprocess.CalledProcessError:
        return [
            p.relative_to(ROOT).as_posix()
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.parts
        ]


def exemption(rel: str) -> str | None:
    for pattern, reason in EXEMPT:
        if fnmatch.fnmatchcase(rel, pattern):
            return reason
    return None


class Findings(list[Any]):
    def add(self, rule: str, message: str) -> None:
        self.append((rule, message))


def deny(
    found: Findings,
    where: str,
    values: Iterable[object],
    identity: Sequence[re.Pattern[str]] | None,
    allow_dates: bool = False,
) -> None:
    for value in values:
        for name in mm.deny_hits(str(value), identity, allow_dates):
            found.add("M004", f"{where} holds {name}")


# ---------------------------------------------------------------- SVG

_BLOCK = re.compile(rf"<!-- {mm.REUSE_START} -->\n(.*?)<!-- {mm.REUSE_END} -->", re.S)


def check_svg(
    rel: str, data: bytes, meta: mm.MediaMeta, identity: Sequence[re.Pattern[str]] | None
) -> Findings:
    found = Findings()
    text = data.decode("utf-8")
    blocks = _BLOCK.findall(text)
    inside = sum(b.count("<metadata") for b in blocks)
    if text.count("<metadata") != inside:
        found.add("M011", "a <metadata> block outside the REUSE ignore markers")
    if not blocks:
        found.add("M001", "no metadata block")
    if re.search(r"\b(?:sodipodi|inkscape):", text) or "xmlns:sodipodi" in text:
        found.add("M005", "an editor namespace (sodipodi or inkscape)")
    m = re.match(r"<!-- " + mm.TAG_LICENSE + r": ([^>]*?) -->\n", text)
    if not m:
        found.add("M001", "no SPDX comment first")
    elif m.group(1) != meta.spdx:
        found.add("M003", f"its SPDX comment says {m.group(1)}, REUSE {meta.spdx}")
    if meta.digital_source_type and mm.DST_BASE not in text[:20000]:
        found.add("M012", "no IPTC digital source type")
    head = re.search(r"<title\b[^>]*>(.*?)</title>.*?<desc\b[^>]*>(.*?)</desc>", text, re.S)
    values = list(blocks) + (list(head.groups()) if head else [])
    deny(found, "its metadata", values, identity)
    if meta.language == "es" and any(
        ES_BANNED.search(v) or any(m.group(0) != "LILYGO" for m in VENDOR_ANY_CASE.finditer(v))
        for v in values
    ):
        found.add("M010", "a banned term in a Spanish value")
    if mm.stamp_svg(text, meta) != text:
        found.add(
            "M002",
            "its root attributes, title, desc or metadata are not what its record "
            "gives (rewrite it with its builder)",
        )
    return found


# ---------------------------------------------------------------- glTF


def _strings(obj: object) -> Iterator[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(k)
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def check_glb(
    rel: str, data: bytes, meta: mm.MediaMeta, identity: Sequence[re.Pattern[str]] | None
) -> Findings:
    found = Findings()
    if data[:4] != b"glTF":
        found.add("M006", "not a GLB")
        return found
    n = struct.unpack_from("<I", data, 12)[0]
    js = json.loads(data[20 : 20 + n].decode("utf-8"))
    asset, packets, scene = mm.gltf_metadata(meta)
    got = js.get("asset", {})
    extra_keys = sorted(set(got) - GLTF_ASSET_KEYS)
    if extra_keys:
        found.add("M005", f"asset keys outside the profile: {extra_keys}")
    for key in ("generator", "copyright", "extras"):
        if key not in got:
            found.add("M001", f"no asset.{key}")
    if got != asset:
        found.add("M002", "asset is not what its record gives (rebuild the model)")
    packet = js.get("extensions", {}).get(mm.GLTF_META_EXTENSION)
    if packet is None:
        found.add("M001", f"no {mm.GLTF_META_EXTENSION} packet")
    elif packet != packets[mm.GLTF_META_EXTENSION]:
        found.add("M002", f"the {mm.GLTF_META_EXTENSION} packet is not what its record gives")
    if mm.GLTF_META_EXTENSION not in js.get("extensionsUsed", []):
        found.add("M006", f"{mm.GLTF_META_EXTENSION} is not in extensionsUsed")
    if mm.GLTF_META_EXTENSION in js.get("extensionsRequired", []):
        found.add("M006", f"{mm.GLTF_META_EXTENSION} is required, not only used")
    if [s.get("name") for s in js.get("scenes", [])][:1] != [scene]:
        found.add("M002", "the scene's name is not the record's")
    if packet:
        extras = got.get("extras", {})
        inner = (packet.get("packets") or [{}])[0]
        title = inner.get("dc:title", {}).get("rdf:_1", {}).get("@value")
        if extras.get("title") != title or extras.get("url") != inner.get("dc:identifier"):
            found.add("M007", "asset.extras and the packet disagree")
    deny(found, "asset", list(_strings(got)) + list(_strings(packet or {})), identity)
    return found


# ---------------------------------------------------------------- OBJ and MTL


def check_obj(
    rel: str, data: bytes, meta: mm.MediaMeta, identity: Sequence[re.Pattern[str]] | None
) -> Findings:
    found = Findings()
    lines = data.decode("utf-8").split("\n")
    want = mm.obj_header(meta) if rel.endswith(".obj") else mm.mtl_header(meta)
    if lines[: len(want)] != want:
        found.add("M002", "its metadata header is not what its record gives (export it again)")
    tags = [ln for ln in lines if ln.startswith("# SPDX-")]
    holders = tuple(t.split(": ", 1)[1] for t in tags if "FileCopyrightText" in t)
    licenses = [t.split(": ", 1)[1] for t in tags if "License-Identifier" in t]
    spdx, reuse_holders = mm.reuse_truth(rel)
    if holders != reuse_holders or licenses != [spdx]:
        found.add("M003", "its SPDX lines are not what REUSE states")
    try:
        start = lines.index(f"# {mm.REUSE_START}")
        end = lines.index(f"# {mm.REUSE_END}")
    except ValueError:
        found.add("M011", "its metadata is not between the REUSE ignore markers")
    else:
        if any(ln.startswith(("# Title:", "# Terms:")) for ln in lines[:start] + lines[end:]):
            found.add("M011", "a metadata line outside the REUSE ignore markers")
    deny(found, "its comments", [ln for ln in lines[:40] if ln.startswith("#")], identity)
    return found


# ---------------------------------------------------------------- PNG


def check_png(
    rel: str, data: bytes, meta: mm.MediaMeta, identity: Sequence[re.Pattern[str]] | None
) -> Findings:
    found = Findings()
    try:
        chunks = mm.png_chunks_of(data)
    except mm.MetaError as exc:
        found.add("M006", str(exc))
        return found
    kinds = [k for k, _ in chunks]
    if kinds[:1] != [b"IHDR"] or kinds[-1:] != [b"IEND"]:
        found.add("M006", "IHDR is not first or IEND not last")
    for k in kinds:
        if k not in PNG_ALLOWED:
            found.add("M005", f"a {k.decode('latin-1')} chunk")
    first_data = kinds.index(b"IDAT") if b"IDAT" in kinds else len(kinds)
    texts = [(k, b) for k, b in chunks if k in (b"tEXt", b"iTXt")]
    for i, k in enumerate(kinds):
        if k in (b"tEXt", b"iTXt") and (
            i > first_data or any(kk in (b"PLTE", b"tRNS") for kk in kinds[i + 1 : first_data])
        ):
            found.add("M006", "a text chunk after the palette or the image data begins")
            break
    profile = mm.png_profile(data)
    want = mm.png_metadata_chunks(meta, profile)
    if not texts:
        found.add("M001", "no text chunks and no XMP")
    elif texts != want:
        other = mm.png_metadata_chunks(meta, "short" if profile == "full" else "full")
        if texts == other:
            found.add(
                "M009",
                f"the {'short' if profile == 'full' else 'full'} profile on a "
                f"picture that takes the {profile} one",
            )
        else:
            found.add("M002", "its text chunks or XMP are not what its record gives")
    values = []
    xmp = ""
    for k, b in texts:
        if k == b"tEXt":
            key, _, value = b.partition(b"\0")
            values.append(value.decode("latin-1"))
            if key.decode("latin-1") == "Title" and mm.xml_text(
                value.decode("latin-1")
            ) not in xmp_of(texts):
                found.add("M007", "the Title chunk and the XMP title disagree")
        else:
            xmp = b.split(b"\0", 5)[-1].decode("utf-8", "replace")
            values.append(xmp)
    if xmp and mm.DST_BASE not in xmp:
        found.add("M012", "no IPTC digital source type")
    deny(found, "its metadata", values, identity)
    return found


def xmp_of(texts: Sequence[tuple[bytes, bytes]]) -> str:
    for k, b in texts:
        if k == b"iTXt" and b.startswith(b"XML:com.adobe.xmp\0"):
            return b.split(b"\0", 5)[-1].decode("utf-8", "replace")
    return ""


# ---------------------------------------------------------------- PDF


def check_pdf(
    rel: str, data: bytes, meta: mm.MediaMeta, identity: Sequence[re.Pattern[str]] | None
) -> Findings:
    import io

    import schematic_pdf
    from pypdf import PdfReader
    from pypdf.generic import DictionaryObject

    found = Findings()
    reader = PdfReader(io.BytesIO(data))
    info = {k: str(v) for k, v in (reader.metadata or {}).items()}
    want = mm.pdf_info(meta)
    for key, value in want.items():
        if key not in info:
            found.add("M001", f"no Info {key}")
        elif info[key] != value:
            found.add("M002", f"Info {key} is not what its record gives")
    extra = sorted(set(info) - set(want))
    if extra:
        found.add("M005", f"Info keys outside the profile: {extra}")
    root = reader.trailer["/Root"].get_object()
    if not isinstance(root, DictionaryObject):
        raise mm.MetaError(f"{rel}: the catalog is not a dictionary")
    board = rel.split("/", 1)[0]
    file_id, document, instance = schematic_pdf.identifiers(board, meta)
    stream = root.get("/Metadata")
    if stream is None:
        found.add("M001", "no XMP metadata stream")
        xmp = ""
    else:
        stream = stream.get_object()
        if "/Filter" in stream:
            found.add("M006", "the XMP stream is compressed")
        xmp = stream.get_data().decode("utf-8", "replace")
        if xmp != mm.pdf_xmp(meta, document, instance):
            found.add("M002", "its XMP is not what its record gives")
        if (
            f'<rdf:li xml:lang="x-default">{mm.xml_text(info.get("/Title", ""))}</rdf:li>'
            not in xmp
        ):
            found.add("M007", "Info /Title and the XMP title disagree")
    if str(root.get("/Lang", "")) != meta.language:
        found.add("M001", "no /Lang")
    prefs = root.get("/ViewerPreferences")
    if not prefs or not bool(prefs.get_object().get("/DisplayDocTitle", False)):
        found.add("M001", "no /DisplayDocTitle")
    ids = reader.trailer.get("/ID")
    if (
        not ids
        or bytes(ids[0].original_bytes) != file_id
        or bytes(ids[1].original_bytes) != file_id
    ):
        found.add("M002", "its /ID is not derived from its sources")
    deny(found, "its metadata", list(info.values()) + [xmp], identity, allow_dates=True)
    return found


CHECKS = {
    ".svg": check_svg,
    ".glb": check_glb,
    ".obj": check_obj,
    ".mtl": check_obj,
    ".png": check_png,
    ".pdf": check_pdf,
}


def check(rel: str, identity: Sequence[re.Pattern[str]] | None) -> Findings:
    """The findings for one tracked file (relative to the repository root)."""
    found = Findings()
    suffix = Path(rel).suffix.lower()
    if suffix not in MEDIA or exemption(rel):
        return found
    try:
        meta = mm.record(rel)
    except mm.MetaError as exc:
        found.add("M008", f"no record and no exemption ({exc})")
        return found
    if meta.own_license not in mm.license_ids(mm.reuse_truth(rel)[0]):
        found.add("M003", f"{meta.own_license} is not in what REUSE states")
    checker = CHECKS.get(suffix)
    if checker is None:
        found.add("M008", f"no check for {suffix} files")
        return found
    found += checker(rel, (ROOT / rel).read_bytes(), meta, identity)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("paths", nargs="*", help="files to check (default: every tracked one)")
    parser.add_argument("--json", action="store_true", help="print [{path, rule, message}]")
    parser.add_argument(
        "--require-identity",
        action="store_true",
        help="fail when no identity pattern list is found (CI)",
    )
    args = parser.parse_args(argv)
    identity = mm.identity_patterns()
    if identity is None:
        if args.require_identity:
            print(
                f"FAIL: no identity patterns ({mm.IDENTITY_ENV} or "
                f"{mm.IDENTITY_FILE.name}); the check fails closed",
                file=sys.stderr,
            )
            return 1
        print(
            f"warning: no identity patterns ({mm.IDENTITY_ENV} or {mm.IDENTITY_FILE.name}); "
            "checking the generic classes only",
            file=sys.stderr,
        )
    files = [Path(p).resolve().relative_to(ROOT).as_posix() for p in args.paths] or tracked()
    results = []
    checked = 0
    try:
        for rel in sorted(files):
            if Path(rel).suffix.lower() in MEDIA and not exemption(rel):
                checked += 1
            for rule, message in check(rel, identity):
                results.append({"path": rel, "rule": rule, "message": message})
    except Exception as exc:  # noqa: BLE001  (an internal error is exit 2, never a pass)
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print(f"{r['path']}: {r['rule']}: {r['message']}")
        print(f"{checked} media files checked, {len(results)} finding(s)")
    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
