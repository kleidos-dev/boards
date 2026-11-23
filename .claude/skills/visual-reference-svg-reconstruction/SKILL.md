---
name: visual-reference-svg-reconstruction
description: "Use when measuring a board face from real references (vendor photos, renders, dimension drawings, CAD) and drawing or correcting its true-scale SVG in this repository: a board's svg/front.svg, svg/back.svg or a side's drawing, always through the generator that writes it, with measurements.json kept in step. Covers finding and choosing references, calibrating pixels to millimeters, rendering PNG previews, overlaying and diffing the drawing against a reference kept outside the tree, and iterating on outline, screen, controls, keyboards, printed legends and case details. Do not use for schematics, board.json, icons or 3D models (see board-specs-and-schematics), or for a device's screen contents."
argument-hint: "board id and what to measure or correct (outline, screen, a control, a legend), or a reference to compare against"
---
<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# Visual reference SVG reconstruction

How a board's face is measured on real references and drawn at true scale. The result is not a decorative icon: it is a clean vector drawing, 1 SVG unit = 1 mm, that the Kleidos site composites screenshots into and that the board's 3D model reads its printed legends from.

## What this repository adds to the method

These rules come first; the method below works inside them.

1. **References stay outside the tree.** A vendor photo, render, dimension drawing, CAD file, a crop of one, an overlay on one and a silhouette traced from one are vendor material: cited by address, never committed (`AGENTS.md`, `NOTICE.md`). Work in a temporary directory outside the repository (for example `$TMPDIR/<board>-refs/`). `_shared/check_public_tree.py` fails a tree that holds a raster image, a CAD file, a `reference/`, `reference_candidates/`, `raw/` or `photos/` folder, a `*_reference.svg` or a `*-silhouette.svg`, tracked or not, and the bundled tool refuses to write inside the repository.
2. **The generator is the only writer of a drawing.** `<board>/svg/front.svg` is written by `_shared/emit_front_svg.py`; `svg/back.svg` and a side's `svg/<face>.svg` by `_shared/emit_back_svg.py`. A correction is a change to the board's drawing code or constants in the generator, then a run of it; never an edit of the SVG.
3. **Every front answers one contract** (`_shared/schema.md`): one `screen-active` rectangle over the bare panel, one hidden `hotspots` group with a press target per physical control, one `annotations` group, a `<g class="legend">` group around each thing the board prints, and no vendor demo screen: the panel is left bare. `tests/test_front_contract.py` and `tests/test_back_contract.py` hold it.
4. **`measurements.json` follows the drawing.** It is kept by hand to the schema in `_shared/schema.md` and must agree with the board's current front (case, display origin and active area, buttons, keyboard grid). A coordinate that was not measured is `null` with a note saying what is missing; an invented number reads as measured.
5. **Every figure keeps its source.** Each reference a figure came from is recorded by address with what it was used for: in `board.json` `sources`, and in a `<board>/sources.md` when a face was measured on particular drawings or photos (`m5stickc-plus-se/sources.md` is the example). A reference that was a mirror or a related SKU's file says so.
6. **A legend change is a model change.** A board's model builds its printed legends from the legend groups of its drawings. Changing what is inside a legend group, or what places it, means rebuilding the model (`_shared/build_board_glb.py <board>/model/spec.json`); a new callout, hotspot or cap does not (`docs/models-and-drawings.md`, "Printed legends").

## When to use

- A board's front, back or side drawing is missing, wrong or less faithful than the references allow: outline, corner radii, screen position, a control, a keyboard row, a printed legend, a color.
- A new board needs its first front and `measurements.json`.
- A drawing has to be checked against a new or better reference.

Do not use it for the schematic, `board.json`, the icon or the model (`board-specs-and-schematics`), or for what a screen shows.

## Principles

1. **Reference first, geometry second.** Never tune proportions from memory when a vendor drawing, CAD file or photo can be found.
2. **Outer dimensions anchor everything.** Calibrate the whole face from the known width and height before placing the screen, the controls and the details.
3. **Photos are evidence, not truth.** Perspective, reflections, shadows, screen content and lens distortion mislead. Prefer dimension drawings, orthographic renders and CAD for measurements; use photos to verify recognizable details and colors.
4. **The drawing is original.** Use vendor imagery as a reference; never trace a raster verbatim, embed an image in an SVG or redraw a vendor's demo screen.
5. **Variant details matter.** The Plus 1.1, the Plus2 and the Plus SE share a chassis and differ inside it; a related SKU's file is a proxy, and is recorded as one.
6. **One board or one family at a time.** Finish a board or a close family, review its overlays, then move on, so uncertainty does not mix.
7. **Metrics assist judgment.** A mean pixel difference ranks obvious mismatches, but a good drawing scores poorly against a glossy photo or a lit screen. The final acceptance is visual.

## The bundled tool

`tools/visual_svg_tools.py` renders, crops, overlays and diffs. It needs Pillow, which the repository's `requirements.txt` pins, and one SVG renderer: CairoSVG when it is installed, else `rsvg-convert`, else Inkscape. Use one renderer through a whole pass. Every output goes to a directory outside the repository.

```bash
TOOL=.claude/skills/visual-reference-svg-reconstruction/tools/visual_svg_tools.py
WORK="${TMPDIR:-/tmp}/<board>-refs"          # outside the repository

# Parse a drawing and refuse an embedded image.
.venv/bin/python -I "$TOOL" validate-svg <board>/svg/front.svg --require-viewbox --reject-images

# Render a preview at 10 px per mm.
.venv/bin/python -I "$TOOL" render <board>/svg/front.svg --output-dir "$WORK/renders" --scale 10 --trim

# Crop a downloaded reference to the case and record how.
.venv/bin/python -I "$TOOL" crop-reference --input "$WORK/vendor.png" --output "$WORK/front.png" \
  --crop 120,80,720,680 --metadata "$WORK/front.json" --source "<address>" \
  --known-dimensions-mm 24 48 --variant-note "front, orthographic render"

# Reference, drawing, overlay and diff on one sheet, with the mean difference.
.venv/bin/python -I "$TOOL" overlay --reference "$WORK/front.png" --svg <board>/svg/front.svg \
  --output-dir "$WORK/overlays" --label <board> --metrics-json "$WORK/<board>.json"

# A contact sheet of several previews.
.venv/bin/python -I "$TOOL" sheet "$WORK"/renders/*.png --output "$WORK/sheet.png" --columns 4
```

A front carries its mm callouts and its title in the `annotations` group, in the margins around the case, and `--trim` removes only transparent margins. An overlay aligns by the case, so crop the rendered preview to the case outline first (`crop-reference` crops any PNG) and give it to `overlay` as `--svg-png` instead of `--svg`.

## Phase 1: gather references

Search broadly, then narrow to the most trustworthy.

- Preferred: the vendor's dimension drawings, CAD (STEP, STL, DXF), product and documentation pages, shop galleries, manuals and datasheets; then a vendor image on a plain background, near-orthographic and front-on.
- Secondary: community CAD, only when the vendor publishes none, and recorded as secondary.
- A photo of a board on the bench, when the owner has one, for what no vendor image shows.

Useful queries: `"<board>" dimensions`, `"<board>" mechanical drawing`, `"<board>" STEP STL`, `"<vendor>" "<board>" schematic pdf`, with the exact variant (`v1.1`, `v1.3`, `Plus`, `SE`, `ADV`) when it matters.

Prefer a reference that is front-on with little perspective, high resolution with sharp edges, of the exact variant, consistent with the known dimensions, and clear about whether its screen content is illustrative. Do not take geometry from a tilted, wide-angle, occluded or hand-held shot, or from another hardware revision.

For each reference kept, record its address, what it is (dimension drawing, render, photo, CAD), the variant it shows, the crop and any rotation or rectification applied, and the known dimensions it was registered to. `crop-reference --metadata` writes that record beside the crop, outside the tree; the address and what it was used for go into `board.json` and `sources.md`.

## Phase 2: calibrate

1. Take the vendor's width and height in millimeters.
2. Crop the reference to the case, without shadow or margin. Turn it to a true front view first if it is rotated; rectify the front plane if the perspective is mild.
3. Compute `px_per_mm_x = cropped_width_px / width_mm` and `px_per_mm_y = cropped_height_px / height_mm`. If they differ noticeably, the crop, the perspective or the dimensions are wrong.
4. Place every feature relative to the case: screen, bezel, buttons, screws, keyboard rows, ports, labels.

A photo that is not cropped exactly to the case is registered before anything is measured on it: the Core2's is turned 0.4° inside a margin and registers through its glass outline onto the glass; the CoreInk's front face is 1.2 % larger than the case outline, so it maps through the four hole centers. A dimension drawing registers off its own extension lines (the Plus SE's at 23.624 px/mm off its `24` and `48`). With no vendor dimension at hand, a USB-C opening (8.94 × 3.26 mm) is a known length.

When only one dimension is known, keep the reference's aspect ratio and record the other as inferred. A screen's active area is the datasheet's size, centered where the registered photo shows the lit pixels.

## Phase 3: draw, through the generator

Change the board's code and constants in `_shared/emit_front_svg.py` (or the board's prints for `_shared/emit_back_svg.py`), then run it for that board: `.venv/bin/python _shared/emit_front_svg.py <board>`.

- Coordinates are case millimeters from the top-left of the face; strokes are in millimeters and thin enough not to change a perceived size.
- Simple primitives: rounded rectangles with measured radii before freehand paths; gradients only for a material or the glass.
- No external image, font file, stylesheet or script. The generator escapes its text.
- Each hotspot comes from the same constants the control is drawn with, so the two cannot drift.
- Inside a legend group, only what the model builder can turn into geometry: one flat `#rrggbb` ink, no opacity, gradient, filter or clip, no group in a group (`_shared/schema.md`, "Legends").
- A fix shared by a family (the three Plus-chassis boards, the two Cores) goes in the shared helper, not in one board.

Audit explicitly: the case's width, height, corner radii, bevels and recesses; the screen's active area, bezel and offset; each button's shape, size, spacing and whether it is a cap, a dome, a touch zone or a printed mark; a keyboard's rows, pitch, stagger, special keys and every legend, with where it is printed; ports, slots, holes, LEDs and sensors seen on that face; the wordmarks and printed text; the materials (black glass, matte plastic, translucent shell, white ink).

## Phase 4: overlay and iterate

Render the drawing and overlay it on the registered reference with the tool, at one scale for a family. Work in passes and regenerate the drawing, the preview and the overlay after each:

1. Outline and true aspect ratio.
2. Screen and bezel.
3. Main controls: buttons, keyboard block, trackball, touch zones.
4. Variant hardware: side keys, ports, slots.
5. Printed text, legends, arrows, symbols.
6. Small details: screws, LEDs, speaker holes, seams.
7. Materials and colors.

Do not tune small details before the outline and the screen are right. On a keyboard, validate the row geometry and the special keys early: a small pitch error accumulates across the face.

Reading a diff: a large outline mismatch means dimensions, rotation or crop are wrong; a screen mismatch is expected, since the drawing leaves the panel bare; highlights and shadows never drive geometry; button, key and legend mismatches matter, because they are what a person recognizes.

Ask at each review: does the silhouette match at a glance; is the display physically plausible; are the controls the real object and not generic shapes; are the legends on the right surface; is this the exact variant; would someone who owns the board recognize it without the caption.

## Before handoff

1. Bring `measurements.json` in line with the new drawing, and record every new source.
2. Rebuild the contact sheet: `.venv/bin/python _shared/emit_front_svg.py --contact-sheet` (a second run changes nothing).
3. If a legend group changed, rebuild the board's model and its web level, and check it: `_shared/check_board_model.py <board directory>`.
4. Run the repository's checks: `.venv/bin/reuse lint`, `.venv/bin/python _shared/check_public_tree.py`, `.venv/bin/python -m pytest tests` (`board-specs-and-schematics`, `references/checks.md`).
5. Review the final overlay once more after the last edit. The working directory stays outside the tree; what it gave is kept in `measurements.json`, the drawing and the sources.
6. Update `docs/models-and-drawings.md` ("Status", "Case sizes") when a board's reference or a figure there changed.

Report in this form:

```markdown
Corrected `<board>/svg/front.svg` through `_shared/emit_front_svg.py`.

References (outside the tree):
- `<address>`: `<what it is, variant>`, used for `<what>`

Checks:
- Front contract and repository checks: OK
- Overlay reviewed after the last edit: mean difference `<n>`
- Model rebuilt: `<yes, why | not needed>`
- Still uncertain: `<none | what, and what would settle it>`

What changed: `<outline / screen / controls / keyboard / legends / colors>`
```

## Common mistakes

- Matching the outline while the screen, the buttons and the legends stay generic.
- Measuring on a perspective marketing render.
- Mixing variants or revisions, or using a related SKU's file without recording it as a proxy.
- Drawing a printed legend as a raised keycap, or leaving out special keys, arrows and secondary legends.
- Fitting the drawing to screen content, reflections or shadows.
- Editing an SVG by hand, embedding a reference image in one, or leaving a render, a crop or an overlay in the tree.
- Writing a number into `measurements.json` that was not measured.
- Correcting one board of a family and leaving the shared helper, or its siblings, inconsistent.
- Changing a legend and not rebuilding the model that reads it.
