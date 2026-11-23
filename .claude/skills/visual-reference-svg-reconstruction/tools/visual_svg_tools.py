# SPDX-License-Identifier: MIT
"""Render, crop, overlay and diff a board drawing against a reference image.

Helper of the visual-reference-svg-reconstruction skill. It reads a drawing of
this repository (``<board>/svg/front.svg``) and a reference image kept outside
it, and writes PNG previews, overlays, diffs and contact sheets.

Nothing it writes belongs in the repository: a vendor photo or render, a crop
of one and an overlay on one are vendor material (``NOTICE.md``), and
``_shared/check_public_tree.py`` fails a tree that holds a raster image. Every
output path must therefore lie outside the repository; the tool refuses one
inside it.

It needs Pillow (pinned in the repository's ``requirements.txt``) and one SVG
renderer: CairoSVG when it is installed, else ``rsvg-convert``, else Inkscape.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def _repository_root() -> Path | None:
    """The repository this skill lives in (``.claude/skills/<skill>/tools/``), or None elsewhere."""
    parents = Path(__file__).resolve().parents
    if len(parents) > 4 and (parents[4] / "_shared" / "check_public_tree.py").is_file():
        return parents[4]
    return None


REPOSITORY_ROOT = _repository_root()
OUTPUT_ARGUMENTS = ("output_dir", "output", "metadata", "metrics_json")
RGBA_WHITE = (255, 255, 255, 255)
RGBA_TRANSPARENT = (255, 255, 255, 0)
RGBA_SHEET_BG = (246, 247, 249, 255)
RGBA_LABEL = (28, 32, 38, 255)
RGBA_CYAN = (0, 210, 255, 120)
VIEWBOX_RE = re.compile(
    r"viewBox\s*=\s*['\"]\s*"
    r"(?P<x>-?\d+(?:\.\d+)?)\s+"
    r"(?P<y>-?\d+(?:\.\d+)?)\s+"
    r"(?P<width>\d+(?:\.\d+)?)\s+"
    r"(?P<height>\d+(?:\.\d+)?)\s*['\"]"
)


def load_pillow() -> tuple[Any, Any, Any, Any, Any, Any]:
    try:
        image_module = importlib.import_module("PIL.Image")
        image_chops_module = importlib.import_module("PIL.ImageChops")
        image_draw_module = importlib.import_module("PIL.ImageDraw")
        image_enhance_module = importlib.import_module("PIL.ImageEnhance")
        image_font_module = importlib.import_module("PIL.ImageFont")
        image_ops_module = importlib.import_module("PIL.ImageOps")
    except ImportError as error:
        raise SystemExit(
            "Pillow is required for this command. Install the repository's "
            "pinned stack: python3 -m pip install -r requirements.txt"
        ) from error
    return (
        image_module,
        image_chops_module,
        image_draw_module,
        image_enhance_module,
        image_font_module,
        image_ops_module,
    )


def default_label_from_path(path: Path) -> str:
    if path.stem == "front" and path.parent.name in {"svg", "reference", "renders"}:
        return path.parent.parent.name
    return path.stem


def parse_viewbox(svg_path: Path) -> tuple[float, float, float, float] | None:
    match = VIEWBOX_RE.search(svg_path.read_text(encoding="utf-8"))
    if not match:
        return None
    return (
        float(match.group("x")),
        float(match.group("y")),
        float(match.group("width")),
        float(match.group("height")),
    )


def run_checked(command: Sequence[str]) -> None:
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        quoted = " ".join(command)
        raise SystemExit(f"Command failed ({completed.returncode}): {quoted}")


def render_with_cairosvg(svg_path: Path, output_path: Path, scale: float) -> bool:
    try:
        import cairosvg
    except ImportError:
        return False
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(output_path),
        scale=scale,
        background_color=None,
    )
    return True


def render_with_rsvg(svg_path: Path, output_path: Path, scale: float) -> bool:
    executable = shutil.which("rsvg-convert")
    if not executable:
        return False
    run_checked(
        [
            executable,
            "--format",
            "png",
            "--zoom",
            f"{scale:.6g}",
            "--output",
            str(output_path),
            str(svg_path),
        ]
    )
    return True


def render_with_inkscape(svg_path: Path, output_path: Path, scale: float) -> bool:
    executable = shutil.which("inkscape")
    viewbox = parse_viewbox(svg_path)
    if not executable or not viewbox:
        return False
    output_width = max(1, round(viewbox[2] * scale))
    run_checked(
        [
            executable,
            str(svg_path),
            "--export-type=png",
            f"--export-filename={output_path}",
            f"--export-width={output_width}",
        ]
    )
    return True


def render_svg(svg_path: Path, output_path: Path, scale: float) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if render_with_cairosvg(svg_path, output_path, scale):
        return
    if render_with_rsvg(svg_path, output_path, scale):
        return
    if render_with_inkscape(svg_path, output_path, scale):
        return
    raise SystemExit("No SVG renderer found. Install cairosvg, rsvg-convert, or inkscape.")


def trim_transparent_png(png_path: Path, padding: int) -> None:
    image_module, _, _, _, _, _ = load_pillow()
    image = image_module.open(png_path).convert("RGBA")
    bbox = image.getbbox()
    if not bbox:
        return
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(image.width, bbox[2] + padding)
    bottom = min(image.height, bbox[3] + padding)
    image.crop((left, top, right, bottom)).save(png_path)


def flatten_rgba(image: Any, background: tuple[int, int, int, int] = RGBA_WHITE) -> Any:
    image_module, _, _, _, _, _ = load_pillow()
    base = image_module.new("RGBA", image.size, background)
    base.alpha_composite(image.convert("RGBA"))
    return base


def contain_image(image: Any, size: tuple[int, int]) -> Any:
    image_module, _, _, _, _, image_ops_module = load_pillow()
    resampling = getattr(image_module, "Resampling", image_module).LANCZOS
    return image_ops_module.contain(image, size, method=resampling)


def fit_to_reference(svg_image: Any, reference_image: Any) -> Any:
    image_module, _, _, _, _, _ = load_pillow()
    fitted = contain_image(svg_image.convert("RGBA"), reference_image.size)
    canvas = image_module.new("RGBA", reference_image.size, RGBA_TRANSPARENT)
    left = (reference_image.width - fitted.width) // 2
    top = (reference_image.height - fitted.height) // 2
    canvas.alpha_composite(fitted, (left, top))
    return canvas


def mean_luma_diff(left_image: Any, right_image: Any) -> float:
    _, image_chops_module, _, _, _, _ = load_pillow()
    diff = image_chops_module.difference(
        left_image.convert("RGB"),
        right_image.convert("RGB"),
    )
    histogram = diff.convert("L").histogram()
    total = sum(count * value for value, count in enumerate(histogram))
    return total / (left_image.width * left_image.height)


def draw_label(draw: Any, position: tuple[int, int], label: str) -> None:
    _, _, _, _, image_font_module, _ = load_pillow()
    try:
        font = image_font_module.truetype("DejaVuSans.ttf", 18)
    except OSError:
        font = image_font_module.load_default()
    draw.text(position, label, fill=RGBA_LABEL, font=font)


def make_contact_sheet(
    image_paths: Sequence[Path],
    output_path: Path,
    labels: Sequence[str] | None,
    columns: int,
    cell_width: int,
    cell_height: int,
    padding: int,
) -> None:
    image_module, _, image_draw_module, _, _, _ = load_pillow()
    if not image_paths:
        raise SystemExit("No input images for contact sheet")
    resolved_labels = list(labels or [default_label_from_path(path) for path in image_paths])
    if len(resolved_labels) != len(image_paths):
        raise SystemExit("Number of labels must match number of input images")
    rows = (len(image_paths) + columns - 1) // columns
    sheet_width = columns * cell_width
    sheet_height = rows * cell_height
    sheet = image_module.new("RGBA", (sheet_width, sheet_height), RGBA_SHEET_BG)
    draw = image_draw_module.Draw(sheet)
    content_size = (cell_width - 2 * padding, cell_height - 3 * padding - 22)
    for image_index, image_path in enumerate(image_paths):
        image = image_module.open(image_path).convert("RGBA")
        fitted = contain_image(image, content_size)
        column = image_index % columns
        row = image_index // columns
        origin_x = column * cell_width
        origin_y = row * cell_height
        left = origin_x + (cell_width - fitted.width) // 2
        top = origin_y + padding + 24 + (content_size[1] - fitted.height) // 2
        sheet.alpha_composite(fitted, (left, top))
        draw_label(draw, (origin_x + padding, origin_y + padding), resolved_labels[image_index])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(output_path)


def make_overlay_outputs(
    reference_path: Path,
    svg_render_path: Path,
    output_dir: Path,
    label: str,
    cell_width: int,
    cell_height: int,
) -> dict[str, Any]:
    image_module, image_chops_module, _, image_enhance_module, _, _ = load_pillow()
    output_dir.mkdir(parents=True, exist_ok=True)
    reference = image_module.open(reference_path).convert("RGBA")
    svg_render = image_module.open(svg_render_path).convert("RGBA")
    svg_fit = fit_to_reference(svg_render, reference)

    reference_flat = flatten_rgba(reference)
    svg_flat = image_module.new("RGBA", reference.size, RGBA_WHITE)
    svg_flat.alpha_composite(svg_fit)

    svg_mask = svg_fit.getchannel("A")
    tinted_svg = image_module.new("RGBA", reference.size, RGBA_TRANSPARENT)
    tinted_svg.paste(image_module.new("RGBA", reference.size, RGBA_CYAN), mask=svg_mask)
    overlay = flatten_rgba(reference)
    overlay.alpha_composite(tinted_svg)

    diff = image_chops_module.difference(
        reference_flat.convert("RGB"),
        svg_flat.convert("RGB"),
    )
    diff = image_enhance_module.Contrast(diff).enhance(2.5)
    mean_diff = mean_luma_diff(reference_flat, svg_flat)

    reference_out = output_dir / f"{label}.reference.png"
    svg_out = output_dir / f"{label}.svg.png"
    overlay_out = output_dir / f"{label}.overlay.png"
    diff_out = output_dir / f"{label}.diff.png"
    sheet_out = output_dir / f"{label}.sheet.png"
    reference_flat.convert("RGB").save(reference_out)
    svg_flat.convert("RGB").save(svg_out)
    overlay.convert("RGB").save(overlay_out)
    diff.save(diff_out)
    make_contact_sheet(
        [reference_out, svg_out, overlay_out, diff_out],
        sheet_out,
        ["reference", "svg", f"overlay diff={mean_diff:.2f}", "diff x2.5"],
        columns=4,
        cell_width=cell_width,
        cell_height=cell_height,
        padding=18,
    )
    return {
        "label": label,
        "mean_diff": mean_diff,
        "reference_png": str(reference_out),
        "svg_png": str(svg_out),
        "overlay_png": str(overlay_out),
        "diff_png": str(diff_out),
        "sheet_png": str(sheet_out),
    }


def parse_crop(value: str) -> tuple[int, int, int, int]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("crop must be left,top,right,bottom")
    try:
        left, top, right, bottom = (int(part) for part in parts)
    except ValueError as error:
        raise argparse.ArgumentTypeError("crop values must be integers") from error
    if right <= left or bottom <= top:
        raise argparse.ArgumentTypeError("crop right/bottom must exceed left/top")
    return left, top, right, bottom


def command_render(args: argparse.Namespace) -> None:
    for svg_path in args.svg:
        label = default_label_from_path(svg_path)
        output_path = args.output_dir / f"{label}.png"
        render_svg(svg_path, output_path, args.scale)
        if args.trim:
            trim_transparent_png(output_path, args.padding)
        print(f"ok render {svg_path} -> {output_path}")


def command_overlay(args: argparse.Namespace) -> None:
    label = args.label
    if not label:
        label = default_label_from_path(args.svg or args.svg_png or args.reference)
    if args.svg:
        rendered_path = args.output_dir / f"{label}.render.png"
        render_svg(args.svg, rendered_path, args.scale)
        if args.trim:
            trim_transparent_png(rendered_path, args.padding)
    else:
        rendered_path = args.svg_png
    if rendered_path is None:
        raise SystemExit("overlay requires --svg or --svg-png")
    result = make_overlay_outputs(
        args.reference,
        rendered_path,
        args.output_dir,
        label,
        args.cell_width,
        args.cell_height,
    )
    if args.metrics_json:
        args.metrics_json.parent.mkdir(parents=True, exist_ok=True)
        args.metrics_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"ok overlay {label} mean_diff={result['mean_diff']:.2f}")
    print(result["sheet_png"])


def command_sheet(args: argparse.Namespace) -> None:
    make_contact_sheet(
        args.images,
        args.output,
        args.labels,
        args.columns,
        args.cell_width,
        args.cell_height,
        args.padding,
    )
    print(f"ok sheet {args.output}")


def command_crop_reference(args: argparse.Namespace) -> None:
    image_module, _, _, _, _, _ = load_pillow()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image = image_module.open(args.input).convert("RGBA")
    cropped = image.crop(args.crop)
    cropped.save(args.output)
    metadata = {
        "source": args.source or str(args.input),
        "source_type": args.source_type,
        "license_or_usage_note": args.usage_note,
        "variant_note": args.variant_note,
        "crop_px": list(args.crop),
        "normalized_size_px": [cropped.width, cropped.height],
        "known_dimensions_mm": args.known_dimensions_mm or [0.0, 0.0],
        "rotation_degrees": args.rotation_degrees,
        "perspective_correction": args.perspective_correction,
        "assumptions": args.assumption,
    }
    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"ok crop {args.input} -> {args.output}")


def command_validate_svg(args: argparse.Namespace) -> None:
    for svg_path in args.svg:
        ET.parse(svg_path)
        viewbox = parse_viewbox(svg_path)
        if args.require_viewbox and not viewbox:
            raise SystemExit(f"missing viewBox: {svg_path}")
        root = ET.parse(svg_path).getroot()
        image_tags = [element for element in root.iter() if element.tag.endswith("image")]
        if args.reject_images and image_tags:
            raise SystemExit(f"embedded image elements are not allowed: {svg_path}")
        print(f"ok svg {svg_path}")


def add_render_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("render", help="render SVG files to PNG")
    parser.add_argument("svg", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scale", type=float, default=10.0)
    parser.add_argument("--trim", action="store_true")
    parser.add_argument("--padding", type=int, default=0)
    parser.set_defaults(func=command_render)


def add_overlay_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("overlay", help="make reference/svg overlay and diff sheet")
    parser.add_argument("--reference", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--svg", type=Path)
    group.add_argument("--svg-png", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--label", default="")
    parser.add_argument("--scale", type=float, default=10.0)
    parser.add_argument("--trim", action="store_true")
    parser.add_argument("--padding", type=int, default=0)
    parser.add_argument("--cell-width", type=int, default=320)
    parser.add_argument("--cell-height", type=int, default=360)
    parser.add_argument("--metrics-json", type=Path)
    parser.set_defaults(func=command_overlay)


def add_sheet_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("sheet", help="build a contact sheet from PNG files")
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--labels", nargs="*")
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--cell-width", type=int, default=280)
    parser.add_argument("--cell-height", type=int, default=320)
    parser.add_argument("--padding", type=int, default=16)
    parser.set_defaults(func=command_sheet)


def add_crop_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("crop-reference", help="crop a reference and write metadata")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--crop", type=parse_crop, required=True, help="left,top,right,bottom")
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--source", default="")
    parser.add_argument("--source-type", default="manufacturer-render")
    parser.add_argument("--usage-note", default="reference only; not embedded")
    parser.add_argument("--variant-note", default="")
    parser.add_argument("--known-dimensions-mm", nargs=2, type=float)
    parser.add_argument("--rotation-degrees", type=float, default=0.0)
    parser.add_argument("--perspective-correction", default="none")
    parser.add_argument("--assumption", action="append", default=[])
    parser.set_defaults(func=command_crop_reference)


def add_validate_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "validate-svg", help="parse SVG files and check basic portability"
    )
    parser.add_argument("svg", nargs="+", type=Path)
    parser.add_argument("--require-viewbox", action="store_true")
    parser.add_argument("--reject-images", action="store_true")
    parser.set_defaults(func=command_validate_svg)


def refuse_outputs_in_repository(args: argparse.Namespace) -> None:
    """Exit when an output path lies inside the repository: no raster or reference file enters it."""
    if REPOSITORY_ROOT is None:
        return
    for name in OUTPUT_ARGUMENTS:
        path = getattr(args, name, None)
        if path is not None and path.resolve().is_relative_to(REPOSITORY_ROOT):
            raise SystemExit(
                f"--{name.replace('_', '-')} {path} is inside the repository: previews, crops, "
                "overlays and reference metadata are written outside it (a temporary directory)"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_render_parser(subparsers)
    add_overlay_parser(subparsers)
    add_sheet_parser(subparsers)
    add_crop_parser(subparsers)
    add_validate_parser(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    refuse_outputs_in_repository(args)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
