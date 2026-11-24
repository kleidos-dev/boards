# SPDX-FileCopyrightText: 2026 José M. Requena Plens
# SPDX-License-Identifier: MIT
"""Draw every board model side by side, at one scale: ``models-contact-sheet.png``

One column per board, in the fleet's order: a three-quarter view (from the
front, right and above) over a front view, both orthographic and at the same
pixels per mm for every board, so the sizes compare as they are. Each model is
the ``.glb`` its ``model/spec.json`` names as output (the StickS3's is the
unpublished master the film's web model is cut from,
``sticks3/model/sticks3.glb``), drawn by ``model_raster.py``; the
label under a column gives the board's name, its triangles and its gzip size
from ``model/source.json``.

The glass carries a test card through the ``screen`` mesh's UVs (blue quadrant
on the image's top-left, with a white corner mark), so the sheet also shows
that a capture would read upright on every board.

The PNG carries the sheet's embedded metadata (``media_meta.png_with_metadata``:
its title, author, description, copyright, license and address as text
chunks, and the same as an XMP packet, before the image data); Pillow is given
no text and no color profile. ``models-contact-sheet.json`` records the PNG's
digest beside the digests of the models it was drawn from, so a model rebuilt
since is a sheet to draw again (``tests/test_media_metadata.py``).

Needs numpy and Pillow (the builder's numpy, plus ``pip install pillow==13.0.0``).
The output is the same bytes for the same models and these versions.

Usage::

    python -I _shared/models_contact_sheet.py \\
        [--out models-contact-sheet.png] [--ppm 5] [--check]

``--check`` draws the sheet into a temporary file and exits 1 when it is not
the committed one, byte for byte.
"""

import argparse
import hashlib
import io
import json
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Every E402 below: the import follows the sys.path set-up above, which
# finds the sibling modules.
import media_meta  # noqa: E402
import model_raster  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

CAD = HERE.parent
from paths import ROOT as REPO  # noqa: E402  (the repository root)
from paths import OutsideError, in_tree, work_path  # noqa: E402  (beside this file)

BOARDS = (
    "sticks3",
    "m5stickc-plus1",
    "m5stickc-plus-se",
    "m5stickc-plus2",
    "coreink",
    "cores3-se",
    "m5stack-core2-v13",
    "cardputer",
    "tdeck-plus",
)
#: Model-to-viewer directions (glTF frame: +Y up the screen, +Z out of it).
VIEWS = (("three-quarter", (0.55, 0.36, 0.75)), ("front", (0.0, 0.0, 1.0)))
BACKGROUND = (244, 244, 241)
INK = (40, 40, 44)
MUTED = (110, 110, 116)
SUPERSAMPLE = 3
GAP_MM = 9.0
MARGIN_MM = 8.0
SHEET = "models-contact-sheet.png"
RECORD = "models-contact-sheet.json"


def board_entry(board: str) -> dict[str, Any]:
    spec = json.loads((CAD / board / "model" / "spec.json").read_text())
    meas = json.loads((CAD / board / "measurements.json").read_text())
    record = json.loads((CAD / board / "model" / "source.json").read_text())
    return {
        "board": board,
        "name": meas.get("display_name", board),
        "glb": in_tree(spec["output"]),
        "triangles": record["triangles"],
        "gzip": record["model_gzip_bytes"],
    }


def render(glb: Path, towards: Sequence[float], ppm: float) -> Image.Image:
    """An RGBA uint8 image of one view, cropped to the model."""
    meshes = model_raster.read_glb(glb)
    project, d = model_raster.orthographic(towards)
    img, _ = model_raster.rasterize(
        meshes, project, d, ppm, screen_card=True, supersample=SUPERSAMPLE
    )
    rgba = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    pic = Image.fromarray(rgba, "RGBA")
    return pic.crop(pic.getbbox())


def main(argv: list[str] | None = None) -> int:
    """Draw the sheet; return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--out", type=Path, default=CAD / "models-contact-sheet.png")
    parser.add_argument("--ppm", type=float, default=5.0, help="pixels per mm (default 5)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="draw into a temporary file and compare it with the committed sheet",
    )
    args = parser.parse_args(argv)
    try:
        out_path = work_path(args.out)
    except OutsideError as exc:
        parser.error(str(exc))
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / SHEET
            code = main(["--out", str(out), "--ppm", str(args.ppm)])
            same = code == 0 and out.read_bytes() == (CAD / SHEET).read_bytes()
        print(
            ("PASS: " if same else "FAIL: ")
            + f"{SHEET} is "
            + ("" if same else "not ")
            + "what the models give"
        )
        return 0 if same else 1
    ppm = args.ppm
    entries = [board_entry(b) for b in BOARDS]
    for e in entries:
        e["views"] = [render(e["glb"], t, ppm) for _, t in VIEWS]
        print(
            f"{e['board']}: {e['triangles']} triangles, "
            + ", ".join(f"{v.size[0]}x{v.size[1]}" for v in e["views"])
        )

    px = round
    gap, margin = px(GAP_MM * ppm), px(MARGIN_MM * ppm)
    title_font = ImageFont.load_default(size=px(5.2 * ppm))
    name_font = ImageFont.load_default(size=px(3.4 * ppm))
    small_font = ImageFont.load_default(size=px(2.8 * ppm))
    col_w = [max(v.size[0] for v in e["views"]) for e in entries]
    row_h = [max(e["views"][i].size[1] for e in entries) for i in range(len(VIEWS))]
    label_h = px(10 * ppm)
    title_h = px(16 * ppm)
    width = 2 * margin + sum(col_w) + gap * (len(entries) - 1)
    height = (
        title_h
        + margin
        + sum(row_h)
        + gap * (len(VIEWS) - 1)
        + px(4 * ppm)
        + label_h
        + px(12 * ppm)
        + margin
    )
    sheet = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, margin), "Kleidos board models", font=title_font, fill=INK)
    draw.text(
        (margin, margin + px(7 * ppm)),
        f"{len(entries)} boards at one scale ({ppm:g} px per mm), orthographic: "
        "three-quarter view over front view",
        font=small_font,
        fill=MUTED,
    )

    x = margin
    for e, w in zip(entries, col_w, strict=True):
        y = title_h + margin
        for i, (pic, h) in enumerate(zip(e["views"], row_h, strict=True)):
            # each row stands its models on one baseline, centered in the column
            sheet.paste(pic, (x + (w - pic.size[0]) // 2, y + h - pic.size[1]), pic)
            y += h + (gap if i < len(VIEWS) - 1 else 0)
        y += px(4 * ppm)
        draw.text((x + w // 2, y), e["name"], font=name_font, fill=INK, anchor="ma")
        draw.text(
            (x + w // 2, y + px(4.8 * ppm)),
            f"{e['triangles']:,} triangles, {e['gzip'] / 1024:.0f} KiB gzip",
            font=small_font,
            fill=MUTED,
            anchor="ma",
        )
        x += w + gap

    # 10 mm scale bar and the test card's key
    y = height - margin - px(4 * ppm)
    bar = px(10 * ppm)
    draw.rectangle((margin, y, margin + bar, y + max(2, px(0.5 * ppm))), fill=INK)
    draw.text((margin + bar + px(2 * ppm), y - px(1.2 * ppm)), "10 mm", font=small_font, fill=INK)
    key_x = margin + bar + px(16 * ppm)
    sw = px(3 * ppm)
    for k, color in enumerate(model_raster.CARD_COLORS):
        c = tuple(int(v * 255 + 0.5) for v in color)
        draw.rectangle(
            (key_x + k * sw, y - px(1 * ppm), key_x + (k + 1) * sw - 1, y + px(2 * ppm)), fill=c
        )
    draw.text(
        (key_x + 4 * sw + px(2 * ppm), y - px(1.2 * ppm)),
        "glass: UV test card (top-left, top-right, bottom-left, bottom-right "
        "quadrants of the image; the white mark is its top-left corner)",
        font=small_font,
        fill=INK,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    sheet.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(
        buffer, format="PNG", optimize=True
    )
    data = media_meta.png_with_metadata(buffer.getvalue(), media_meta.record(SHEET))
    out_path.write_bytes(data)
    if out_path == (CAD / SHEET).resolve():
        (CAD / RECORD).write_text(
            json.dumps(sheet_record(data, entries, ppm), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(f"wrote {args.out}: {sheet.size[0]}x{sheet.size[1]}, {len(data)} bytes")
    return 0


def sheet_record(data: bytes, entries: list[dict[str, Any]], ppm: float) -> dict[str, Any]:
    """What ``models-contact-sheet.json`` records: the PNG and the models it was drawn from."""
    return {
        "sheet": SHEET,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "ppm": ppm,
        "models": {
            e["board"]: {
                "model": str(e["glb"].relative_to(REPO).as_posix()),
                "model_sha256": hashlib.sha256(e["glb"].read_bytes()).hexdigest(),
            }
            for e in entries
        },
    }


if __name__ == "__main__":
    sys.exit(main())
