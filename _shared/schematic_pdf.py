# SPDX-License-Identifier: MIT
"""Finish a schematic PDF kicad-cli wrote: links that land on a place, no script.

kicad-cli links a text only to a whole page (``#n`` gives ``/FitB``), writes a
property pop-up per symbol that only Acrobat's scripting opens, and keeps the
script that pop-up calls in the document even when the pop-ups are left out.
This step reads ``links.json`` (written by ``kicad_schematic.py`` beside the
schematic) and, with ``pypdf``:

- sends every link it lists (a ``[page/zone]`` after a net label, a place in
  an index table, a box of the power tree) to its place: ``/XYZ left top
  zoom``, the target ``VIEW_LEFT`` mm from the window's left edge and
  ``VIEW_TOP`` mm below its top, at ``VIEW_ZOOM``. Every reader that follows a
  link honours a page and a position; that is PDF 1.0;
- adds a link on every part's reference, to its row in the parts list;
- gives every link a ``/Contents`` (what it leads to, for screen readers);
- writes the named destinations (``part-U16``, ``net-VBUS_L0-p3``), so a web
  page can open the PDF at a part or a net (``sticks3.pdf#nameddest=part-U16``);
- replaces KiCad's bookmarks (which give ``/FitR`` boxes with top and bottom
  swapped) with one entry per page and, under it, its parts or its tables,
  each at its place;
- removes every script: the document's ``/JavaScript`` name tree and any
  action that runs one;
- writes the document's metadata from its record (``media_meta.record``): the
  Info dictionary (title, author, subject, keywords, creator, producer and
  the title block's date as both dates, never the export's clock), the same
  facts as an uncompressed XMP stream, ``/Lang`` and ``/DisplayDocTitle``,
  and a file identifier derived from the schematic's sources rather than a
  random one (``metadata()``).

Usage: ``python3 _shared/schematic_pdf.py <board> <pdf>`` (rewrites the PDF in
place). ``export_schematic.py`` runs it after kicad-cli.
"""
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, BooleanObject, ByteStringObject, DecodedStreamObject,
                           DictionaryObject, Fit, FloatObject, NameObject, NumberObject,
                           TextStringObject)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_meta  # noqa: E402  (beside this file; -I leaves it off the path)
from paths import ROOT  # noqa: E402

#: The theme the PDF is drawn in, one of the sources its identifier is derived from.
THEME_FILE = ROOT / "_shared" / "kicad-theme-kleidos-dark.json"

PT = 72 / 25.4


def xyz(spot: dict, view: dict, height_pt: float) -> tuple[float, float, float]:
    """The /XYZ left, top (points) and zoom that put ``spot`` (mm, y down) in view."""
    left = (spot["x"] - view["left"]) * PT
    top = height_pt - (spot["y"] - view["top"]) * PT
    return round(left, 3), round(top, 3), view["zoom"]


def inside(rect, x, y, slack=0.6) -> bool:
    return rect[0] - slack <= x <= rect[2] + slack and rect[1] - slack <= y <= rect[3] + slack


def rect_mm(annot, height_pt: float) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = (float(v) for v in annot["/Rect"])
    return (min(x0, x1) / PT, (height_pt - max(y0, y1)) / PT,
            max(x0, x1) / PT, (height_pt - min(y0, y1)) / PT)


def strip_scripts(writer: PdfWriter) -> int:
    """Remove every JavaScript the document holds; return how many went."""
    gone = 0
    root = writer._root_object
    names = root.get("/Names")
    if names is not None:
        names = names.get_object()
        if "/JavaScript" in names:
            del names["/JavaScript"]
            gone += 1
        if not names:
            del root["/Names"]
    for key in ("/OpenAction", "/AA"):
        if key in root:
            del root[key]
            gone += 1
    for page in writer.pages:
        if "/AA" in page:
            del page["/AA"]
            gone += 1
        annots = page.get("/Annots")
        if annots is None:
            continue
        keep = ArrayObject()
        for ref in annots:
            a = ref.get_object()
            act = a.get("/A")
            if act is not None and act.get_object().get("/S") == "/JavaScript":
                gone += 1
                continue
            keep.append(ref)
        page[NameObject("/Annots")] = keep
    return gone


def link(rect_pt, dest, alt: str) -> DictionaryObject:
    return DictionaryObject({
        NameObject("/Type"): NameObject("/Annot"),
        NameObject("/Subtype"): NameObject("/Link"),
        NameObject("/Rect"): ArrayObject([FloatObject(round(v, 3)) for v in rect_pt]),
        NameObject("/Border"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)]),
        NameObject("/Dest"): dest,
        NameObject("/Contents"): TextStringObject(alt),
    })


def sources_digest(board: str) -> hashlib._Hash:
    """SHA-256 of what the PDF is drawn from: every sheet of the schematic, then the theme."""
    digest = hashlib.sha256()
    for sheet in sorted((ROOT / board / "schematic").glob("*.kicad_sch")):
        digest.update(sheet.read_bytes())
    digest.update(THEME_FILE.read_bytes())
    return digest


def identifiers(board: str, meta: media_meta.MediaMeta) -> tuple[bytes, str, str]:
    """(trailer /ID, XMP DocumentID, XMP InstanceID): derived, never random.

    The /ID is the first 16 bytes of the sources' digest; the document's id
    is a name-based UUID of its address, its instance's one of its address
    and the sources' digest, so a new schematic is a new instance of the
    same document.
    """
    digest = sources_digest(board)
    document = "uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, meta.identifier_url))
    instance = "uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL,
                                        f"{meta.identifier_url}#{digest.hexdigest()}"))
    return digest.digest()[:16], document, instance


def metadata(writer: PdfWriter, board: str) -> None:
    """Write the document's metadata from its record (``media_meta``, the standard's 5.8)."""
    meta = media_meta.record(f"{board}/schematic/{board}.pdf")
    file_id, document, instance = identifiers(board, meta)
    writer.metadata = {NameObject(k): TextStringObject(v)
                       for k, v in media_meta.pdf_info(meta).items()}
    stream = DecodedStreamObject()
    stream.set_data(media_meta.pdf_xmp(meta, document, instance).encode("utf-8"))
    stream[NameObject("/Type")] = NameObject("/Metadata")
    stream[NameObject("/Subtype")] = NameObject("/XML")
    root = writer._root_object
    root[NameObject("/Metadata")] = writer._add_object(stream)
    root[NameObject("/Lang")] = TextStringObject(meta.language)
    root[NameObject("/ViewerPreferences")] = DictionaryObject(
        {NameObject("/DisplayDocTitle"): BooleanObject(True)})
    writer._ID = ArrayObject([ByteStringObject(file_id), ByteStringObject(file_id)])


def finish(board: str, pdf: Path, links_file: Path | None = None) -> list[str]:
    """Rewrite ``pdf`` in place; return the errors (a listed link not found)."""
    links_file = links_file or ROOT / board / "schematic" / "links.json"
    spec = json.loads(links_file.read_text(encoding="utf-8"))
    view = spec["view"]
    writer = PdfWriter(clone_from=PdfReader(pdf))
    pages = writer.pages
    height = float(pages[0].mediabox.height)
    errors = []
    strip_scripts(writer)

    def dest(spot: dict) -> ArrayObject:
        left, top, zoom = xyz(spot, view, height)
        return ArrayObject([pages[spot["page"] - 1].indirect_reference, NameObject("/XYZ"),
                            FloatObject(left), FloatObject(top), FloatObject(zoom)])

    # KiCad's own links: the page row and the contents boxes keep their page;
    # every one links.json lists goes to its place
    by_page: dict[int, list] = {}
    for j in spec["jumps"]:
        by_page.setdefault(j["page"], []).append(j)
    for i, page in enumerate(pages, start=1):
        annots = page.get("/Annots") or []
        rects = []
        for ref in annots:
            a = ref.get_object()
            if a.get("/Subtype") == "/Link":
                rects.append((rect_mm(a, height), a))
        for j in by_page.get(i, []):
            x, y = j["at"]
            hits = [a for r, a in rects if inside(r, x + 0.3, y)]
            if len(hits) != 1:
                errors.append(f"page {i}: {len(hits)} links at ({x:.1f}, {y:.1f}) mm for {j['alt']!r}")
                continue
            a = hits[0]
            for key in ("/A", "/Dest"):
                if key in a:
                    del a[key]
            a[NameObject("/Dest")] = dest(j["to"])
            a[NameObject("/Contents")] = TextStringObject(j["alt"])
        for r, a in rects:      # the rest go to a page: say which
            if "/Contents" not in a and isinstance(a.get("/Dest"), ArrayObject):
                target = next((k for k, p in enumerate(pages, start=1)
                               if p.indirect_reference.idnum == a["/Dest"][0].idnum), None)
                if target:
                    a[NameObject("/Contents")] = TextStringObject(f"Page {target}")

    # a link on every part's reference, to its row in the parts list
    for add in spec["added"]:
        x0, y0, x1, y1 = add["rect"]
        rect_pt = (x0 * PT, height - y1 * PT, x1 * PT, height - y0 * PT)
        writer.add_annotation(add["page"] - 1, link(rect_pt, dest(add["to"]), add["alt"]))

    # named destinations
    for name, spot in sorted(spec["marks"].items()):
        left, top, zoom = xyz(spot, view, height)
        writer.add_named_destination(name, spot["page"] - 1, Fit.xyz(left, top, zoom))

    # bookmarks: one per page, its parts or tables under it
    if "/Outlines" in writer._root_object:
        del writer._root_object["/Outlines"]
    for entry in spec["outline"]:
        top_item = writer.add_outline_item(title=entry["title"], page_number=entry["page"] - 1,
                                           fit=Fit.fit(), is_open=False)
        for kid in entry["kids"]:
            left, top, zoom = xyz(kid["to"], view, height)
            writer.add_outline_item(title=kid["title"], page_number=kid["to"]["page"] - 1,
                                    parent=top_item, fit=Fit.xyz(left, top, zoom))
    writer._root_object[NameObject("/PageMode")] = NameObject("/UseOutlines")
    metadata(writer, board)
    with open(pdf, "wb") as fh:
        writer.write(fh)
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.split("\n\n")[-2])
        return 2
    errors = finish(argv[0], Path(argv[1]))
    for e in errors:
        print(f"FAIL {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
