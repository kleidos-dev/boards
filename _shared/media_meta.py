# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""The embedded metadata of every media file this repository publishes

Every drawing, model, schematic and picture here says what it is, who made
it, under which license and where it lives, inside the file itself, so the
facts travel with a copy and indexers read them: the Kleidos media metadata
standard, profile ``kleidos-media-meta/1`` (``docs/models-and-drawings.md``,
"Embedded metadata").

One record per file (:class:`MediaMeta`), derived by :func:`record` from the
file's path and the repository's own sources, never typed per file: the name,
vendor, SKU and revision from the board's ``board.json`` ``identity``, the
credits of a model from its ``model/spec.json`` ``copyright``, the license and
the copyright holders from ``REUSE.toml`` (:func:`reuse_truth`, e-mail
addresses removed). One writer per format turns a record into bytes:
:func:`stamp_svg`, :func:`gltf_metadata`, :func:`obj_header` /
:func:`mtl_header`, :func:`png_with_metadata`, :func:`pdf_info` and
:func:`xmp_packet`. The builders call them while they write a file, and
``check_metadata.py`` calls the same ones to hold every committed file to its
record, so a field has one source and one writer.

Deterministic by construction: fixed fields in a fixed order, no date but an
authored one (a schematic's title-block date), no machine name, path, user or
tool version, no random identifier, no XMP padding.

Needs the standard library only.
"""

from __future__ import annotations

import json
import os
import re
import struct
import tomllib
import zlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

#: The profile; it goes into nothing embedded, only into what records a build.
META_PROFILE = "kleidos-media-meta/1"

CREATOR = "José M. Requena Plens"
CREATOR_URL = "https://kleidos.dev"
PROJECT = "Kleidos"
PROJECT_URL = "https://kleidos.dev"
CREDIT = CREATOR
BASE_KEYWORDS = ("Kleidos", "hardware password manager", "open source")
TRADEMARK_NOTE_M5 = (
    "M5Stack and M5 are trademarks of their owner; Kleidos is not affiliated with M5Stack."
)
TRADEMARK_NOTE_LILYGO = (
    "LILYGO and T-Deck are trademarks of their owner; Kleidos is not affiliated with LILYGO."
)
TRADEMARK_BY_VENDOR = {"M5Stack": TRADEMARK_NOTE_M5, "LILYGO": TRADEMARK_NOTE_LILYGO}
TRADEMARK_NOTE_KLEIDOS = "The Kleidos name and logo are subject to the terms in TRADEMARKS.md."
#: Every schematic PDF's title block shows the Kleidos mark, from the KiCad kit's drawing sheet.
CREDIT_MARK = (
    "Title-block mark: the Kleidos mark, \u00a9 2026 Jos\u00e9 M. Requena Plens, GPL-3.0-or-later, "
    "placed unchanged under the press permission in brand's TRADEMARKS.md."
)

REPO = "boards"
REPO_URL = "https://github.com/kleidos-dev/boards"
RIGHTS_URL = f"{REPO_URL}/blob/main/NOTICE.md"
#: ``asset.generator`` of every model, and the PDF's ``/Producer``.
GLB_GENERATOR = "Kleidos build_board_glb.py"
PDF_PRODUCER = "kleidos-boards schematic_pdf.py"
#: The KiCad the schematics are exported with (``.github/workflows/check.yml``).
PDF_CREATOR = "KiCad 10.0.8 Eeschema"

DST_BASE = "http://cv.iptc.org/newscodes/digitalsourcetype/"
#: The IPTC digital source types a picture may state (the standard, 3.5).
DIGITAL_SOURCE_TYPES = (
    "digitalCapture",
    "screenCapture",
    "digitalCreation",
    "dataDrivenMedia",
    "composite",
    "trainedAlgorithmicMedia",
    "compositeWithTrainedAlgorithmicMedia",
    "compositeSynthetic",
)

#: The SPDX identifiers on the SPDX License List this repository uses.
SPDX_LISTED = {
    "MIT",
    "Apache-2.0",
    "OFL-1.1",
    "GPL-3.0-or-later",
    "BSD-3-Clause",
    "CC0-1.0",
    "CC-BY-4.0",
}

#: REUSE's ignore markers and tags, spelled in two halves so REUSE does not read this file's
#: own source as markers, tags or copyright notices.
REUSE_START = "REUSE-IgnoreStart"
REUSE_END = "REUSE-IgnoreEnd"
TAG_LICENSE = "SPDX-License-Identifier"
TAG_COPYRIGHT = "SPDX-FileCopyrightText"
COPYRIGHT_SIGN = "\u00a9"


class MetaError(ValueError):
    """A record the standard does not allow (a field over its limit, an unknown path)."""


# ---------------------------------------------------------------- licenses


def license_url(spdx_id: str) -> str:
    """The page of a license: SPDX's for a listed identifier, the
    text in ``LICENSES/`` otherwise."""
    if spdx_id in SPDX_LISTED:
        return f"https://spdx.org/licenses/{spdx_id}.html"
    if spdx_id.startswith("LicenseRef-") and (ROOT / "LICENSES" / f"{spdx_id}.txt").is_file():
        return f"{REPO_URL}/blob/main/LICENSES/{spdx_id}.txt"
    raise MetaError(f"{spdx_id}: no license page this repository can name")


def license_ids(expression: str) -> list[str]:
    """The identifiers of an SPDX expression, in its order, each once."""
    out = []
    for token in re.findall(r"[A-Za-z0-9.+-]+", expression):
        if token in ("AND", "OR", "WITH") or token in out:
            continue
        out.append(token)
    return out


def _glob(pattern: str) -> re.Pattern[str]:
    """A REUSE.toml path pattern: ``*`` stays inside a folder, ``**`` crosses them."""
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("\\*", i):
            out.append(re.escape("*"))
            i += 2
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def _without_email(text: str) -> str:
    return re.sub(r"\s*<[^>]*>", "", text).strip()


BINARY = {
    ".png",
    ".glb",
    ".pdf",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".stl",
    ".jpg",
    ".jpeg",
    ".webp",
    ".avif",
    ".gif",
    ".ico",
}
_TAG = re.compile(r"SPDX-(FileCopyrightText|License-Identifier)" r":\s*(.+?)\s*(?:-->|\*/)?\s*$")


def in_file_tags(path: Path) -> tuple[list[str], list[str]]:
    """(license expressions, copyright texts) a text file states outside its REUSE ignore blocks."""
    if path.suffix.lower() in BINARY or not path.is_file():
        return [], []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [], []
    licenses, holders, ignoring = [], [], False
    for line in text.splitlines():
        if REUSE_START in line:
            ignoring = True
        if not ignoring:
            m = _TAG.search(line)
            if m and m.group(1) == "License-Identifier":
                licenses.append(m.group(2))
            elif m:
                holders.append(m.group(2))
        if REUSE_END in line:
            ignoring = False
    return licenses, holders


def reuse_truth(path: str | Path) -> tuple[str, tuple[str, ...]]:
    """(SPDX expression, copyright holders without e-mail) REUSE states for *path*.

    ``REUSE.toml`` under REUSE 3.3: the last annotation whose path matches,
    with its precedence (``override`` its own values alone, ``closest`` the
    file's own tags when it has any, ``aggregate`` both), plus the file's own
    SPDX tags outside its REUSE ignore blocks.
    ``tests/test_media_metadata.py`` holds it to ``reuse spdx``.
    """
    rel = (
        Path(path).as_posix()
        if not Path(path).is_absolute()
        else Path(path).resolve().relative_to(ROOT).as_posix()
    )
    toml = tomllib.loads((ROOT / "REUSE.toml").read_text(encoding="utf-8"))
    found = None
    for ann in toml.get("annotations", []):
        paths = ann["path"] if isinstance(ann["path"], list) else [ann["path"]]
        if any(_glob(p).match(rel) for p in paths):
            found = ann
    file_licenses, file_holders = in_file_tags(ROOT / rel)
    toml_licenses, toml_holders = [], []
    precedence = "closest"
    if found is not None:
        precedence = found.get("precedence", "closest")
        lic = found.get("SPDX-License-Identifier")
        toml_licenses = [lic] if isinstance(lic, str) else list(lic or [])
        cop = found.get("SPDX-FileCopyrightText")
        toml_holders = [cop] if isinstance(cop, str) else list(cop or [])
    if precedence == "override":
        licenses, holders = toml_licenses, toml_holders
    elif precedence == "closest" and (file_licenses or file_holders):
        licenses = file_licenses or toml_licenses
        holders = file_holders or toml_holders
    else:
        licenses, holders = toml_licenses + file_licenses, toml_holders + file_holders
    expr = []
    for lic in licenses:
        if lic not in expr:
            expr.append(lic)
    clean = []
    for holder in holders:
        h = _without_email(holder)
        if h not in clean:
            clean.append(h)
    if not expr:
        raise MetaError(f"{rel}: REUSE states no license")
    return " AND ".join(expr), tuple(clean)


# ---------------------------------------------------------------- the record


@dataclass(frozen=True)
class MediaMeta:
    """Everything one file's metadata says (the standard, 2.5)."""

    path: str
    title: str
    description: str
    alt: str
    keywords: tuple[str, ...]
    digital_source_type: str | None
    spdx: str
    own_license: str
    holders: tuple[str, ...]
    credits: tuple[str, ...] = ()
    trademarks: tuple[str, ...] = ()
    source_url: str | None = None
    rights_url: str = RIGHTS_URL
    language: str = "en"
    content_date: str | None = None
    media_type: str = ""
    slug: str = ""
    extra: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    @property
    def identifier_url(self) -> str:
        return identifier_url(self.path)

    @property
    def license_url(self) -> str:
        return license_url(self.own_license)

    @property
    def copyright(self) -> str:
        """The copyright sign before each holder, then the SPDX expression (at most 128 UTF-8
        bytes, IIM's limit)."""
        sign = COPYRIGHT_SIGN
        text = f"{sign} " + f"; {sign} ".join(self.holders) + f". {self.spdx}."
        if len(text.encode("utf-8")) > 128:
            raise MetaError(f"{self.path}: the copyright line is over 128 bytes: {text}")
        return text

    @property
    def usage_terms(self) -> str:
        urls = ", ".join(license_url(i) for i in license_ids(self.spdx))
        return " ".join([f"Licensed under {self.spdx}: {urls}.", *self.credits, *self.trademarks])


def identifier_url(path: str) -> str:
    """The public address of a file of this repository."""
    return f"{REPO_URL}/blob/main/{PurePosixPath(path).as_posix()}"


def _check(meta: MediaMeta) -> MediaMeta:
    if len(meta.title.encode("utf-8")) > 64:
        raise MetaError(f"{meta.path}: the title is over 64 bytes: {meta.title}")
    if len(meta.description) > 300:
        raise MetaError(f"{meta.path}: the description is over 300 characters")
    if len(meta.alt) > 250:
        raise MetaError(f"{meta.path}: the alt text is over 250 characters")
    if len(meta.keywords) > 12 or any(len(k.encode("utf-8")) > 64 for k in meta.keywords):
        raise MetaError(f"{meta.path}: more than 12 keywords, or one over 64 bytes")
    if meta.own_license not in license_ids(meta.spdx):
        raise MetaError(f"{meta.path}: {meta.own_license} is not in {meta.spdx}")
    if (
        meta.digital_source_type is not None
        and meta.digital_source_type not in DIGITAL_SOURCE_TYPES
    ):
        raise MetaError(f"{meta.path}: {meta.digital_source_type} is no IPTC source type")
    meta.copyright  # noqa: B018  (raises over 128 bytes)
    return meta


def identity(board: str) -> dict[str, Any]:
    """A board's naming facts from its ``board.json``: name, vendor, SKU, revision, display name."""
    data = json.loads((ROOT / board / "board.json").read_text(encoding="utf-8"))["identity"]
    name = data["name"]
    revision = data.get("revision")
    if revision and revision.lower() not in name.lower():
        name = f"{name} {revision}"
    return {
        "name": data["name"],
        "vendor": data["vendor"],
        "sku": data["sku"],
        "display": f"{data['vendor']} {name}",
    }


def _board_keywords(ident: dict[str, Any], *kind: str) -> tuple[str, ...]:
    words = [*BASE_KEYWORDS, ident["vendor"], ident["name"], ident["sku"], *kind]
    out = []
    for w in words:
        if w not in out:
            out.append(w)
    return tuple(out)


def spec_credits(spec_path: Path) -> tuple[str, ...]:
    """The credit sentences of a model: its ``model/spec.json`` ``copyright``, one string."""
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    text = " ".join(str(spec["copyright"]).split())
    return (text,) if text else ()


def _from_reuse(path: str, own: str = "MIT") -> dict[str, Any]:
    spdx, holders = reuse_truth(path)
    return {"spdx": spdx, "own_license": own, "holders": holders}


def _slug(*parts: str) -> str:
    return "kl-" + "-".join(p for p in parts if p)


FIXTURE_GLB = "_shared/fixtures/faces/model/faces.glb"
BOARD_FILES = re.compile(
    r"(?P<board>[a-z0-9-]+)/(?:svg/(?P<face>front|back|left|right|top|bottom)\.svg"
    r"|(?P<icon>icon)\.svg"
    r"|model/(?P<model>[a-z0-9-]+?)(?P<web>-web)?\.(?P<ext>glb|obj|mtl)"
    r"|schematic/(?P<schematic>[a-z0-9-]+)\.pdf)\Z"
)


def record(path: str | Path) -> MediaMeta:
    """The metadata record of the media file at *path* (relative to the repository root)."""
    rel = PurePosixPath(Path(path).as_posix()).as_posix()
    if rel == "fronts-contact-sheet.svg":
        return _check(
            MediaMeta(
                path=rel,
                title="The nine Kleidos board front drawings at one scale",
                description=(
                    "The front drawings of the nine boards Kleidos runs on, side by side "
                    "at one scale. Part of Kleidos boards. "
                    f"{TRADEMARK_NOTE_M5} {TRADEMARK_NOTE_LILYGO}"
                ),
                alt="The front drawings of the nine boards Kleidos runs on, side by side.",
                keywords=(
                    *BASE_KEYWORDS,
                    "M5Stack",
                    "LILYGO",
                    "board drawings",
                    "contact sheet",
                    "SVG",
                ),
                digital_source_type="digitalCreation",
                media_type="image/svg+xml",
                slug=_slug("fronts", "sheet"),
                trademarks=(TRADEMARK_NOTE_M5, TRADEMARK_NOTE_LILYGO),
                **_from_reuse(rel),
            )
        )
    if rel == "models-contact-sheet.png":
        return _check(
            MediaMeta(
                path=rel,
                title="The nine Kleidos board 3D models at one scale",
                description=(
                    "The 3D models of the nine boards Kleidos runs on, rendered side by "
                    "side at one scale, a three-quarter view above a front view, with a "
                    "UV test card on each glass. Part of Kleidos boards."
                ),
                alt=(
                    "Nine board models side by side at one scale, each in a three-quarter view "
                    "above a front view."
                ),
                keywords=(*BASE_KEYWORDS, "M5Stack", "LILYGO", "3D models", "contact sheet"),
                digital_source_type="digitalCreation",
                media_type="image/png",
                credits=(
                    "Case geometry of the eight M5Stack boards: M5Stack M5_Hardware, MIT, "
                    f"{COPYRIGHT_SIGN} 2021 M5Stack.",
                ),
                trademarks=(TRADEMARK_NOTE_M5, TRADEMARK_NOTE_LILYGO),
                **_from_reuse(rel),
            )
        )
    if rel == FIXTURE_GLB:
        return _check(
            MediaMeta(
                path=rel,
                title="Kleidos boards face fixture 3D model",
                description=(
                    "Test board of the Kleidos boards model checks: two boxes printed on "
                    "their front and their back."
                ),
                alt="Two stacked boxes with printed marks on their front and back.",
                keywords=(*BASE_KEYWORDS, "test fixture", "3D model", "glTF"),
                digital_source_type="digitalCreation",
                media_type="model/gltf-binary",
                credits=spec_credits(ROOT / "_shared/fixtures/faces/model/spec.json"),
                slug=_slug("face", "fixture"),
                **_from_reuse(rel),
            )
        )
    m = BOARD_FILES.match(rel)
    if not m or m.group("board") not in _boards():
        raise MetaError(f"{rel}: no metadata record for this path")
    board = m.group("board")
    ident = identity(board)
    disp, sku = ident["display"], ident["sku"]
    who = f"{disp} ({sku})"
    tm = (TRADEMARK_BY_VENDOR[ident["vendor"]],)
    common = _from_reuse(rel)
    face = m.group("face")
    if face:
        kind = {"front": "front", "back": "back"}.get(face, f"{face} side")
        shows = {
            "front": (
                f"Front of the {who} drawn at 1:1 scale (1 SVG unit = 1 mm): case, "
                "screen, keys, ports and printed legends."
            ),
            "back": (
                f"Back of the {who} drawn at 1:1 scale (1 SVG unit = 1 mm), as seen from "
                "behind, with the labels and marks printed on it."
            ),
        }.get(
            face,
            f"{face.capitalize()} side of the {who} drawn at 1:1 scale "
            "(1 SVG unit = 1 mm), with what is printed on it.",
        )
        return _check(
            MediaMeta(
                path=rel,
                title=f"{who} {kind} drawing, 1:1 mm",
                description=f"{shows} Part of Kleidos boards. {tm[0]}",
                alt=f"{kind.capitalize()} drawing of the {who}.",
                keywords=_board_keywords(ident, f"{kind} drawing", "SVG"),
                digital_source_type="digitalCreation",
                media_type="image/svg+xml",
                slug=_slug(board, face),
                trademarks=tm,
                **common,
            )
        )
    if m.group("icon"):
        return _check(
            MediaMeta(
                path=rel,
                title=f"{who} icon",
                description=(
                    f"Small icon of the {who} for lists and menus. Part of Kleidos boards."
                ),
                alt=f"Icon of the {who}.",
                keywords=_board_keywords(ident, "icon", "SVG"),
                digital_source_type="digitalCreation",
                media_type="image/svg+xml",
                slug=_slug(board, "icon"),
                **common,
            )
        )
    if m.group("schematic"):
        if m.group("schematic") != board:
            raise MetaError(f"{rel}: no metadata record for this path")
        return _check(
            MediaMeta(
                path=rel,
                title=f"{who} schematic, Kleidos boards",
                description=(
                    f"Schematic of the {who}: its connectivity documented from the "
                    "vendor's public documentation, with Kleidos additions and corrections "
                    "listed on page 1."
                ),
                alt=f"Schematic of the {who}.",
                keywords=_board_keywords(ident, "schematic", "KiCad"),
                digital_source_type=None,
                media_type="application/pdf",
                credits=(CREDIT_MARK,),
                trademarks=(*tm, TRADEMARK_NOTE_KLEIDOS),
                content_date=schematic_date(board),
                **common,
            )
        )
    if m.group("model") != board:
        raise MetaError(f"{rel}: no metadata record for this path")
    ext, web = m.group("ext"), bool(m.group("web"))
    if web and ext != "glb":
        raise MetaError(f"{rel}: no metadata record for this path")
    credits = spec_credits(ROOT / board / "model" / "spec.json")
    if ext == "mtl":
        return _check(
            MediaMeta(
                path=rel,
                title=f"{who} 3D model materials, MTL",
                description=(
                    f"Materials of the {who} Wavefront OBJ model: the base color, alpha, "
                    "roughness and metalness of each part. Part of Kleidos boards."
                ),
                alt=f"Materials of the {who} 3D model.",
                keywords=_board_keywords(ident, "Wavefront MTL", "materials"),
                digital_source_type=None,
                media_type="model/mtl",
                **common,
            )
        )
    if ext == "obj":
        return _check(
            MediaMeta(
                path=rel,
                title=f"{who} 3D model, Wavefront OBJ",
                description=(
                    f"The {who} 3D model as Wavefront OBJ, in millimeters with Y up, "
                    "written from its glTF master: the same triangles, normals and parts. "
                    "Part of Kleidos boards."
                ),
                alt=f"3D model of the {who}.",
                keywords=_board_keywords(ident, "3D model", "Wavefront OBJ"),
                digital_source_type=None,
                media_type="model/obj",
                credits=credits,
                trademarks=tm,
                **common,
            )
        )
    if web:
        return _check(
            MediaMeta(
                path=rel,
                title=f"{who} web 3D model",
                description=(
                    f"Web level of detail of the {who} 3D model: its glTF master less the "
                    "printed legends too thin to see at the largest size the Kleidos site "
                    "draws it."
                ),
                alt=f"3D model of the {who}.",
                keywords=_board_keywords(ident, "3D model", "glTF", "web"),
                digital_source_type="digitalCreation",
                media_type="model/gltf-binary",
                credits=credits,
                trademarks=tm,
                extra={"scene": who},
                **common,
            )
        )
    return _check(
        MediaMeta(
            path=rel,
            title=f"{who} 3D model",
            description=(
                f"glTF 2.0 model of the {who} with its case, screen, keys, ports and "
                "printed legends, built by the Kleidos boards builder from its drawings "
                "and measurements."
            ),
            alt=f"3D model of the {who}.",
            keywords=_board_keywords(ident, "3D model", "glTF"),
            digital_source_type="digitalCreation",
            media_type="model/gltf-binary",
            credits=credits,
            trademarks=tm,
            extra={"scene": who},
            **common,
        )
    )


def _boards() -> tuple[str, ...]:
    from paths import BOARDS  # beside this file

    return BOARDS


def schematic_date(board: str) -> str:
    """The date a board's schematic title block states (``YYYY-MM-DD``): its only date."""
    text = (ROOT / board / "schematic" / f"{board}.kicad_sch").read_text(encoding="utf-8")
    m = re.search(r'\(title_block.*?\(date "(\d{4}-\d{2}-\d{2})"\)', text, re.S)
    if not m:
        raise MetaError(f"{board}: the schematic title block states no date")
    return m.group(1)


# ---------------------------------------------------------------- escaping


def xml_text(text: str) -> str:
    """XML-escaped: ``& < > "`` only."""
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


# ---------------------------------------------------------------- XMP


XMP_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "photoshop": "http://ns.adobe.com/photoshop/1.0/",
    "Iptc4xmpCore": "http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/",
    "Iptc4xmpExt": "http://iptc.org/std/Iptc4xmpExt/2008-02-29/",
    "plus": "http://ns.useplus.org/ldf/xmp/1.0/",
    "xmpRights": "http://ns.adobe.com/xap/1.0/rights/",
    "cc": "http://creativecommons.org/ns#",
    "pdf": "http://ns.adobe.com/pdf/1.3/",
    "xmp": "http://ns.adobe.com/xap/1.0/",
    "xmpMM": "http://ns.adobe.com/xap/1.0/mm/",
}
XPACKET_BEGIN = '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
XPACKET_END = '<?xpacket end="r"?>'


def _alt(tag: str, value: str, indent: str) -> str:
    return (
        f'{indent}<{tag}><rdf:Alt><rdf:li xml:lang="x-default">{xml_text(value)}'
        f"</rdf:li></rdf:Alt></{tag}>"
    )


def xmp_packet(meta: MediaMeta, profile: str = "full", pdf: dict[str, Any] | None = None) -> str:
    """The XMP packet of a record (the standard, 5.1): ``full``, ``short`` or, with *pdf*, a PDF's.

    *pdf* holds ``keywords``, ``producer``, ``creator_tool``, ``date``,
    ``document_id`` and ``instance_id``; a PDF's packet leaves out the alt
    text and the digital source type.
    """
    i = "      "
    lines = []
    short = profile == "short"
    if short:
        used = ["dc", "Iptc4xmpExt", "xmpRights", "cc"]
    elif pdf is not None:
        used = ["dc", "photoshop", "Iptc4xmpCore", "plus", "xmpRights", "cc", "pdf", "xmp", "xmpMM"]
    else:
        used = ["dc", "photoshop", "Iptc4xmpCore", "Iptc4xmpExt", "plus", "xmpRights", "cc"]
    if pdf is not None:
        lines.append(f"{i}<dc:format>{xml_text(meta.media_type)}</dc:format>")
    lines.append(_alt("dc:title", meta.title, i))
    if not short:
        lines.append(_alt("dc:description", meta.description, i))
    lines.append(
        f"{i}<dc:creator><rdf:Seq><rdf:li>{xml_text(CREATOR)}</rdf:li></rdf:Seq></dc:creator>"
    )
    lines.append(_alt("dc:rights", meta.copyright, i))
    if not short:
        lines.append(
            f"{i}<dc:subject><rdf:Bag>"
            + "".join(f"<rdf:li>{xml_text(k)}</rdf:li>" for k in meta.keywords)
            + "</rdf:Bag></dc:subject>"
        )
    lines.append(f"{i}<dc:identifier>{xml_text(meta.identifier_url)}</dc:identifier>")
    if meta.source_url and not short:
        lines.append(f"{i}<dc:source>{xml_text(meta.source_url)}</dc:source>")
    if not short:
        lines.append(f"{i}<photoshop:Credit>{xml_text(CREDIT)}</photoshop:Credit>")
        if pdf is None:
            lines.append(_alt("Iptc4xmpCore:AltTextAccessibility", meta.alt, i))
        lines.append(f'{i}<Iptc4xmpCore:CreatorContactInfo rdf:parseType="Resource">')
        lines.append(f"{i}  <Iptc4xmpCore:CiUrlWork>{CREATOR_URL}</Iptc4xmpCore:CiUrlWork>")
        lines.append(f"{i}</Iptc4xmpCore:CreatorContactInfo>")
    if pdf is None:
        if meta.digital_source_type is None:
            raise MetaError(f"{meta.path}: a picture states its digital source type")
        lines.append(
            f"{i}<Iptc4xmpExt:DigitalSourceType>{DST_BASE}"
            f"{meta.digital_source_type}</Iptc4xmpExt:DigitalSourceType>"
        )
    if not short:
        lines.append(f'{i}<plus:Licensor><rdf:Seq><rdf:li rdf:parseType="Resource">')
        lines.append(f"{i}  <plus:LicensorName>{xml_text(CREATOR)}</plus:LicensorName>")
        lines.append(f"{i}  <plus:LicensorURL>{xml_text(meta.rights_url)}</plus:LicensorURL>")
        lines.append(f"{i}</rdf:li></rdf:Seq></plus:Licensor>")
    lines.append(f"{i}<xmpRights:Marked>True</xmpRights:Marked>")
    lines.append(
        f"{i}<xmpRights:WebStatement>{xml_text(meta.license_url)}</xmpRights:WebStatement>"
    )
    if not short:
        lines.append(_alt("xmpRights:UsageTerms", meta.usage_terms, i))
    lines.append(f'{i}<cc:license rdf:resource="{xml_text(meta.license_url)}"/>')
    if pdf is not None:
        lines.append(f"{i}<pdf:Keywords>{xml_text(pdf['keywords'])}</pdf:Keywords>")
        lines.append(f"{i}<pdf:Producer>{xml_text(pdf['producer'])}</pdf:Producer>")
        lines.append(f"{i}<xmp:CreatorTool>{xml_text(pdf['creator_tool'])}</xmp:CreatorTool>")
        lines.extend(
            f"{i}<xmp:{tag}>{pdf['date']}</xmp:{tag}>"
            for tag in ("CreateDate", "ModifyDate", "MetadataDate")
        )
        lines.append(f"{i}<xmpMM:DocumentID>{pdf['document_id']}</xmpMM:DocumentID>")
        lines.append(f"{i}<xmpMM:InstanceID>{pdf['instance_id']}</xmpMM:InstanceID>")
    ns = "\n".join(f'        xmlns:{p}="{XMP_NS[p]}"' for p in used)
    return "\n".join(
        [
            XPACKET_BEGIN,
            '<x:xmpmeta xmlns:x="adobe:ns:meta/">',
            '  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">',
            '    <rdf:Description rdf:about=""',
            ns + ">",
            *lines,
            "    </rdf:Description>",
            "  </rdf:RDF>",
            "</x:xmpmeta>",
            XPACKET_END,
        ]
    )


# ---------------------------------------------------------------- SVG


def svg_block(meta: MediaMeta) -> str:
    """The ``<title>``, ``<desc>`` and Dublin Core + ccREL ``<metadata>`` of an SVG (5.7)."""
    s = meta.slug
    lines = [
        f'<title id="{s}-t">{xml_text(meta.title)}</title>',
        f'<desc id="{s}-d">{xml_text(meta.description)}</desc>',
        f"<!-- {REUSE_START} -->",
        f'<metadata id="{s}-m">',
        '  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"',
        '           xmlns:dc="http://purl.org/dc/elements/1.1/"',
        '           xmlns:cc="http://creativecommons.org/ns#"',
        '           xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/">',
        '    <cc:Work rdf:about="">',
        "      <dc:format>image/svg+xml</dc:format>",
        '      <dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage"/>',
        f"      <dc:title>{xml_text(meta.title)}</dc:title>",
        f"      <dc:description>{xml_text(meta.description)}</dc:description>",
        f"      <dc:creator><cc:Agent><dc:title>{xml_text(CREATOR)}</dc:title></cc:Agent>"
        "</dc:creator>",
        f"      <dc:publisher><cc:Agent><dc:title>{PROJECT}</dc:title></cc:Agent></dc:publisher>",
        f"      <dc:rights><cc:Agent><dc:title>{xml_text(meta.copyright)}</dc:title></cc:Agent>"
        "</dc:rights>",
        f"      <dc:identifier>{xml_text(meta.identifier_url)}</dc:identifier>",
    ]
    if meta.source_url:
        lines.append(f"      <dc:source>{xml_text(meta.source_url)}</dc:source>")
    lines += [
        f"      <dc:language>{meta.language}</dc:language>",
        "      <dc:subject><rdf:Bag>"
        + "".join(f"<rdf:li>{xml_text(k)}</rdf:li>" for k in meta.keywords)
        + "</rdf:Bag></dc:subject>",
        f'      <Iptc4xmpExt:DigitalSourceType rdf:resource="{DST_BASE}'
        f'{meta.digital_source_type}"/>',
        f'      <cc:license rdf:resource="{xml_text(meta.license_url)}"/>',
        "    </cc:Work>",
        "  </rdf:RDF>",
        "</metadata>",
        f"<!-- {REUSE_END} -->",
    ]
    return "\n".join(lines) + "\n"


_SVG_SPDX = re.compile(r"\A<!-- " + TAG_LICENSE + r": [^>]*-->\n")
_SVG_ROOT = re.compile(r"<svg\b[^>]*>\n?")
_ROOT_A11Y = re.compile(r'\s(?:role|aria-labelledby|lang)="[^"]*"')
_SVG_META = re.compile(
    r"(?:<title\b[^>]*>[^<]*</title>\n?)?(?:<desc\b[^>]*>[^<]*</desc>\n?)?"
    rf"(?:<!-- {REUSE_START} -->\n<metadata\b.*?</metadata>\n<!-- {REUSE_END} -->\n?)?",
    re.S,
)


def unstamp_svg(svg: str) -> str:
    """An SVG without what :func:`stamp_svg` writes: its SPDX
    comment, root title, desc, metadata."""
    svg = _SVG_SPDX.sub("", svg)
    m = _SVG_ROOT.search(svg)
    if not m:
        raise MetaError("no <svg> root")
    root = _ROOT_A11Y.sub("", m.group(0).rstrip("\n"))
    rest = svg[m.end() :]
    leading = _SVG_META.match(rest)
    if leading is None:
        raise MetaError("the <svg> root's leading title, desc and metadata do not parse")
    rest = rest[leading.end() :]
    return svg[: m.start()] + root + "\n" + rest


def stamp_svg(svg: str, meta: MediaMeta) -> str:
    """*svg* with its record: the SPDX comment first, the root's accessible name, the block (5.7).

    Only attributes of the root and the leading title, desc and metadata
    change; the drawing is left as it is. Stamping a stamped file again gives
    the same bytes, so the checker holds a file to ``stamp_svg(file) == file``.
    """
    bare = unstamp_svg(svg)
    m = _SVG_ROOT.search(bare)
    if m is None:
        raise MetaError("no <svg> root")
    root = m.group(0).rstrip("\n")
    root = root[:-1].rstrip() + (
        f' role="img" aria-labelledby="{meta.slug}-t {meta.slug}-d" lang="{meta.language}">'
    )
    return (
        f"<!-- {TAG_LICENSE}: {meta.spdx} -->\n"
        + bare[: m.start()]
        + root
        + "\n"
        + svg_block(meta)
        + bare[m.end() :]
    )


# ---------------------------------------------------------------- glTF


def gltf_metadata(meta: MediaMeta) -> tuple[dict[str, Any], dict[str, Any], str]:
    """(``asset``, the root ``extensions``, the scene's name) of a model (5.11)."""
    asset = {
        "version": "2.0",
        "generator": GLB_GENERATOR,
        "copyright": f"{meta.copyright} {meta.usage_terms}",
        "extensions": {"KHR_xmp_json_ld": {"packet": 0}},
        "extras": {
            "title": meta.title,
            "description": meta.description,
            "creator": CREATOR,
            "license": meta.own_license,
            "licenseUrl": meta.license_url,
            "copyrightHolders": list(meta.holders),
            "url": meta.identifier_url,
            "project": PROJECT_URL,
            "keywords": list(meta.keywords),
        },
    }

    def alt(value: str) -> dict[str, Any]:
        return {"@type": "rdf:Alt", "rdf:_1": {"@language": "x-default", "@value": value}}

    packet = {
        "@context": {
            "dc": XMP_NS["dc"],
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "xmpRights": XMP_NS["xmpRights"],
        },
        "@id": "",
        "dc:format": meta.media_type,
        "dc:title": alt(meta.title),
        "dc:description": alt(meta.description),
        "dc:creator": {"@list": [CREATOR]},
        "dc:rights": alt(meta.copyright),
        "dc:identifier": meta.identifier_url,
        "dc:subject": {"@set": list(meta.keywords)},
        "xmpRights:Marked": True,
        "xmpRights:WebStatement": meta.license_url,
        "xmpRights:UsageTerms": alt(meta.usage_terms),
    }
    return asset, {"KHR_xmp_json_ld": {"packets": [packet]}}, meta.extra.get("scene", meta.title)


GLTF_META_EXTENSION = "KHR_xmp_json_ld"


def gltf_without_metadata(js: dict[str, Any]) -> dict[str, Any]:
    """A model's JSON less what :func:`gltf_metadata` writes, for comparing two models' content."""
    out = dict(js)
    out["asset"] = {"version": js.get("asset", {}).get("version", "2.0")}
    ext = dict(out.get("extensions", {}))
    ext.pop(GLTF_META_EXTENSION, None)
    if ext:
        out["extensions"] = ext
    else:
        out.pop("extensions", None)
    if "extensionsUsed" in out:
        out["extensionsUsed"] = [e for e in out["extensionsUsed"] if e != GLTF_META_EXTENSION]
        if not out["extensionsUsed"]:
            del out["extensionsUsed"]
    out["scenes"] = [{k: v for k, v in s.items() if k != "name"} for s in out.get("scenes", [])]
    return out


# ---------------------------------------------------------------- OBJ and MTL


def _comment_block(meta: MediaMeta, title: str, with_terms: bool) -> list[str]:
    lines = [f"# {TAG_COPYRIGHT}: {h}" for h in meta.holders]
    lines.append(f"# {TAG_LICENSE}: {meta.spdx}")
    lines += [
        f"# {REUSE_START}",
        f"# Title: {title}",
        f"# Description: {meta.description}",
        f"# URL: {meta.identifier_url}",
        f"# Project: {PROJECT}, {PROJECT_URL}",
    ]
    if with_terms:
        lines.append(f"# Terms: {meta.usage_terms}")
    lines.append(f"# {REUSE_END}")
    return lines


def obj_header(meta: MediaMeta) -> list[str]:
    """The comment lines an OBJ opens with (5.12): REUSE's tags, then the record."""
    return _comment_block(meta, meta.title, True)


def mtl_header(meta: MediaMeta) -> list[str]:
    """The comment lines an MTL opens with: its materials are this project's alone."""
    return _comment_block(meta, meta.title, True)


# ---------------------------------------------------------------- PNG


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_TEXT_KEYS = ("Title", "Author", "Description", "Copyright", "License", "Comment")
PNG_SHORT_KEYS = ("Copyright", "License")
#: The chunks that may come before the text: as the encoder wrote them.
PNG_BEFORE_TEXT = {
    b"IHDR",
    b"gAMA",
    b"cHRM",
    b"sRGB",
    b"iCCP",
    b"PLTE",
    b"tRNS",
    b"pHYs",
    b"sBIT",
    b"bKGD",
}


def png_chunks_of(data: bytes) -> list[tuple[bytes, bytes]]:
    """[(type, data)] of a PNG, CRCs checked."""
    if not data.startswith(PNG_SIGNATURE):
        raise MetaError("not a PNG")
    out, i = [], 8
    while i < len(data):
        n, kind = struct.unpack(">I4s", data[i : i + 8])
        body = data[i + 8 : i + 8 + n]
        crc = struct.unpack(">I", data[i + 8 + n : i + 12 + n])[0]
        if zlib.crc32(kind + body) & 0xFFFFFFFF != crc:
            raise MetaError(f"a {kind.decode('latin-1')} chunk with a wrong CRC")
        out.append((kind, body))
        i += 12 + n
        if kind == b"IEND":
            break
    return out


def png_size(data: bytes) -> tuple[int, int]:
    return struct.unpack(">II", data[16:24])


def png_profile(data: bytes) -> str:
    """``short`` for a picture whose longer side is under 64 px, else ``full`` (3.3)."""
    return "short" if max(png_size(data)) < 64 else "full"


def png_text(meta: MediaMeta, profile: str) -> list[tuple[str, str]]:
    """The ``tEXt`` keywords and values of a record, in their order (5.2)."""
    values = {
        "Title": meta.title,
        "Author": CREATOR,
        "Description": meta.description,
        "Copyright": meta.copyright,
        "License": f"{meta.spdx} {meta.license_url}",
        "Comment": f"{PROJECT}, {PROJECT_URL}. {meta.identifier_url}",
    }
    keys = PNG_SHORT_KEYS if profile == "short" else PNG_TEXT_KEYS
    return [(k, values[k]) for k in keys]


def _chunk(kind: bytes, body: bytes) -> bytes:
    return (
        struct.pack(">I", len(body))
        + kind
        + body
        + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    )


def png_metadata_chunks(meta: MediaMeta, profile: str) -> list[tuple[bytes, bytes]]:
    out = []
    for key, value in png_text(meta, profile):
        try:
            out.append((b"tEXt", key.encode("latin-1") + b"\0" + value.encode("latin-1")))
        except UnicodeEncodeError as exc:
            raise MetaError(f"{meta.path}: the PNG {key} is not Latin-1: {value}") from exc
    packet = xmp_packet(meta, profile).encode("utf-8")
    out.append((b"iTXt", b"XML:com.adobe.xmp\0\0\0\0\0" + packet))
    return out


def png_with_metadata(data: bytes, meta: MediaMeta) -> bytes:
    """*data*, an encoder's PNG, with the record's chunks before the first IDAT (5.2).

    Text, time and EXIF chunks the encoder wrote are dropped; every other
    chunk, the image data included, is kept byte for byte.
    """
    chunks = [
        (k, b)
        for k, b in png_chunks_of(data)
        if k not in (b"tEXt", b"iTXt", b"zTXt", b"tIME", b"eXIf")
    ]
    at = next(i for i, (k, _) in enumerate(chunks) if k == b"IDAT")
    added = png_metadata_chunks(meta, png_profile(data))
    return PNG_SIGNATURE + b"".join(_chunk(k, b) for k, b in chunks[:at] + added + chunks[at:])


# ---------------------------------------------------------------- PDF


def pdf_date(date: str) -> tuple[str, str]:
    """(``D:YYYYMMDD000000Z``, ``YYYY-MM-DDT00:00:00Z``) of an authored ``YYYY-MM-DD``."""
    return f"D:{date.replace('-', '')}000000Z", f"{date}T00:00:00Z"


def _content_date(meta: MediaMeta) -> str:
    """The date a schematic's PDF states: its record's content date."""
    if meta.content_date is None:
        raise MetaError(f"{meta.path}: a schematic's record names its content date")
    return meta.content_date


def pdf_info(meta: MediaMeta) -> dict[str, str]:
    """The Info dictionary of a schematic PDF, in its order (5.8)."""
    pdf_d, _ = pdf_date(_content_date(meta))
    return {
        "/Title": meta.title,
        "/Author": CREATOR,
        "/Subject": meta.description,
        "/Keywords": ", ".join(meta.keywords),
        "/Creator": PDF_CREATOR,
        "/Producer": PDF_PRODUCER,
        "/CreationDate": pdf_d,
        "/ModDate": pdf_d,
    }


def pdf_xmp(meta: MediaMeta, document_id: str, instance_id: str) -> str:
    _, iso = pdf_date(_content_date(meta))
    return xmp_packet(
        meta,
        pdf={
            "keywords": ", ".join(meta.keywords),
            "producer": PDF_PRODUCER,
            "creator_tool": PDF_CREATOR,
            "date": iso,
            "document_id": document_id,
            "instance_id": instance_id,
        },
    )


# ---------------------------------------------------------------- privacy


DENY = (
    ("an e-mail address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    (
        "a local path",
        re.compile(
            r"/Users/|/home/|/private/|/var/folders/|/tmp/|/Volumes/"
            r"|file://|~/|[A-Za-z]:\\|\\Users\\"
        ),
    ),
    (
        "a host or network address",
        re.compile(
            r"\.local\b|\.lan\b|\.home\b|\blocalhost\b|\b192\.168\.\d+\.\d+\b"
            r"|\b10\.\d+\.\d+\.\d+\b|\b172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+\b|\bMacBook|\biMac\b"
            r"|-mbp\b"
        ),
    ),
    ("a machine date and time", re.compile(r"\d{4}[-:]\d{2}[-:]\d{2}[ T]\d{2}:\d{2}")),
    (
        "a tool or version string",
        re.compile(
            r"\bLavf\d|\bLavc\d|x264 - core|\blibx264\b|\bImageMagick\b|\bGIMP\b|\bInkscape\b"
            r"|sodipodi:|\bIllustrator\b|\bPillow\b|\bHeadlessChrome\b|Eeschema-SVG"
            r"|Image::ExifTool"
        ),
    ),
)
IDENTITY_FILE = Path(__file__).resolve().parent / "deny-local.txt"
IDENTITY_ENV = "KLEIDOS_DENY_EXTRA"


def identity_patterns() -> list[re.Pattern[str]] | None:
    """The identity patterns (one regex a line) from the untracked
    file or the CI secret, or None."""
    text = os.environ.get(IDENTITY_ENV, "")
    if not text.strip() and IDENTITY_FILE.is_file():
        text = IDENTITY_FILE.read_text(encoding="utf-8")
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return [re.compile(line, re.I) for line in lines] if lines else None


def deny_hits(
    value: str, identity: Sequence[re.Pattern[str]] | None = None, allow_dates: bool = False
) -> list[str]:
    """The classes of private data *value* holds (never the matched text of an identity hit)."""
    out = []
    for name, pattern in DENY:
        if allow_dates and name == "a machine date and time":
            continue
        if pattern.search(value):
            out.append(name)
    if identity and any(p.search(value) for p in identity):
        out.append("an identity pattern")
    return out
