---
name: board-specs-and-schematics
description: "Conventions of this repository (kleidos-dev/boards): one folder per board named by its hyphenated board id, a board.json whose every value cites its source, a hand-kept measurements.json, drawings written only by their generators, a KiCad schematic generated from netlist.yaml that documents the board's connectivity from the vendor's public documentation and improves on the vendor's print with sourced Kleidos entries (K1, K2...) and bench records, 64 px icons, 3D models at two levels built from pinned vendor CAD (the master also as Wavefront OBJ and MTL), REUSE licensing, and no vendor file in the tree. Use when adding a board or changing its specification, measurements, schematic, Kleidos entries, bench records, icon, model or provenance, or when answering a hardware question from the repository's sourced facts. Do not use for measuring a board face from photos, renders or CAD (see visual-reference-svg-reconstruction) or for the firmware's board support code, which lives in the Kleidos firmware repository."
---

# Board specifications and schematics

This repository holds, for every board Kleidos runs on, its drawings, measurements, sourced specification, schematic and 3D model, and the builders and checks that keep them consistent. `AGENTS.md` has the rules, `README.md` what a board folder holds, `_shared/schema.md` the drawing and measurement contract and `docs/models-and-drawings.md` which script writes each file. This skill is the part an agent must not get wrong.

## When to use

- Adding a board, or changing a value in a board's `board.json` or `measurements.json`.
- Drawing or correcting a board's schematic: a part, pin or net of `netlist.yaml`, its layout, a Kleidos addition or correction, a bench record, an open question.
- Changing a board's icon, 3D model or provenance records.
- Answering a question about a board's hardware (chip, pins, rails, display, input) from the repository's own sourced facts.

## When not to use

- Measuring a board face from photos, renders, dimension drawings or CAD before the generator draws it: `visual-reference-svg-reconstruction`.
- Firmware board support (`variants/`, `src/boards/`, drivers): the Kleidos firmware repository and its own instructions. This repository cites the firmware by repository path and symbol ("Kleidos firmware, `variants/tdeck/variant.h`, `PIN_TRACKBALL_UP`": no commit, no line, since its history will be squashed when it is published) and never edits it.

## Non-negotiables

1. **One folder per board, named by its board id**: the lowercase, hyphenated product name, with the vendor prefix only where the name alone is ambiguous (`sticks3`, `cardputer`, `coreink`, `tdeck-plus`, `cores3-se`, `m5stack-core2-v13`, `m5stickc-plus1`, `m5stickc-plus2`, `m5stickc-plus-se`). It is the name the Kleidos site uses, not the firmware variant (`tdeck`, `cores3_se`, `core2_v13`); the map from firmware variant to board id lives in the site's data, never here.
2. **Every value is sourced.** `board.json` follows `_shared/board.schema.json`: sources are a keyed `sources` object (`url` over https, `title`, `kind`, `checked` date, and `mirror_of` or `found_via` when the address read was not the vendor's own), and every block cites them by id in `src`. A fact with no source is left out, never guessed; a role the board lacks goes in `absent` with the source that says so. In `measurements.json` an unmeasured coordinate is `null` with a note, never an invented number. The board's `README.md` is written from `board.json`: change the file first, then the page.
3. **Generated files have one writer.** Edit the input and run the writer, never the output:

   | Output | Writer | Input kept by hand |
   | --- | --- | --- |
   | `<board>/README.md` | `_shared/emit_board_readme.py` (`--check` reports a stale page; `tests/test_board_readme.py` fails on one) | `board.json` |
   | `<board>/svg/front.svg`, `fronts-contact-sheet.svg` | `_shared/emit_front_svg.py` (`--contact-sheet`) | the board's drawing code in the generator |
   | `<board>/svg/back.svg`, a side's `svg/<face>.svg` | `_shared/emit_back_svg.py` | the board's prints (`_shared/board_faces.py` and the per-board modules beside it) |
   | `<board>/schematic/*.kicad_sch`, `<board>.kicad_sym`, `<board>.kicad_pro`, `sym-lib-table`, `links.json` | `_shared/kicad_schematic.py <board>` | `schematic/netlist.yaml`, `schematic/layout.yaml` |
   | `<board>/schematic/<board>.pdf` (and `schematic/svg/`, one SVG per page, ignored by git) | `_shared/export_schematic.py <board>` (kicad-cli 10.0.8) | the generated KiCad files |
   | `_shared/kicad/` (the Kleidos KiCad kit: drawing sheets, themes, `style.json`, `kleidos_kicad.py`, `KIT.json`) | brand's `tools/sync_kicad.py --copy` | brand's `kicad/` |
   | `<board>/model/<board>.glb`, `model/source.json` | `_shared/build_board_glb.py <board>/model/spec.json` | `model/spec.json`, the legend groups of the board's drawings |
   | `<board>/model/<board>.obj`, `<board>/model/<board>.mtl` (and `obj` in `source.json`) | `_shared/export_obj.py`, run by the builder whenever it writes the master, or on its own (`--check` reports a stale file) | the master GLB |
   | `<board>/model/<board>-web.glb`, `model/web.json` | the same builder with `--web-px-per-mm` | the master and the scale the site draws the board at |
   | `models-contact-sheet.png`, `models-contact-sheet.json` | `_shared/models_contact_sheet.py` | the nine models |
   | the metadata block of each `<board>/icon.svg` | `_shared/stamp_icon_meta.py` (`--check`) | `board.json` `identity`, `REUSE.toml` |

   `measurements.json`, `board.json`, `icon.svg`, `netlist.yaml`, `layout.yaml`, `spec.json` and the Markdown pages are kept by hand.
4. **A schematic documents the board's connectivity from the vendor's public documentation.** Say it in those words: never the vendor's schematic "redrawn" or "copied". Every part, pin and net of `netlist.yaml` names its source (the vendor's published schematic, its page and version, cited by address and SHA-256); the layout and the symbols of the integrated circuits and connectors are each board's own and the generic ones (passives, diodes, transistors, switches, plain connectors, grounds) this project's `kleidos` library; no KiCad library symbol is used or embedded.
5. **The drawing improves on the vendor's print, and says where** (owner, 2026-11-17). A detail the print does not show goes in when a primary source makes it certain; a drawing error of the print is corrected when the evidence settles it. Each is an entry of `kleidos` in `netlist.yaml` (`K1`, `K2`...), marked on the drawing and listed with its source on page 1, so nothing silently differs from the print. What is still uncertain stays out and the board's `schematic/README.md` lists it as open; measure on the bench when in doubt. With entries, the notes say "connectivity documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1"; without any they must not. The procedure is in [references/kleidos-entries.md](references/kleidos-entries.md).
6. **No vendor file in the tree.** Datasheets, vendor schematics, photos, renders, reference overlays, STEP or STL files, community models and vendor demo-screen art are cited by address and digest, never committed; `_shared/check_public_tree.py` fails a tree that holds one, tracked or not. What is committed is derived work: the models re-meshed from M5Stack's MIT-licensed `m5stack/M5_Hardware` files, which carry M5Stack's MIT notice beside this project's copyright, and the T-Deck Plus model, built from no vendor file (`_shared/tdeck_plus_case.py`). The build fetches each CAD file by pinned SHA-256 into a cache outside the tree (`$KLEIDOS_CAD_CACHE`).
7. **Licensing is per file in `REUSE.toml`**: everything this project writes is MIT (code, drawings, data, models, schematics, documents, these skills); M5Stack's case geometry MIT with their notice; the Khronos tone-mapping function Apache-2.0; Inter OFL-1.1. No Creative Commons license anywhere (owner, 2026-11-17). A new kind of file gets its row and a new third-party source its notice in `NOTICE.md`, in the same change; `reuse lint` must pass.
8. **Icons are 64 px pictograms on one canvas** (`width="64" height="64" viewBox="2.75 2.75 58.5 58.5"`), so they line up side by side; their SPDX comment, `<title>`, `<desc>` and `<metadata>` are written by `_shared/stamp_icon_meta.py`, never by hand.
9. **Every media file carries its embedded metadata**, written from `_shared/media_meta.py` `record()` by the script that writes the file, and `_shared/check_metadata.py` must pass; a new kind of media file gets its record or an exemption with its reason in the same change.
10. **Nothing private.** No serial number, port path, IP or MAC address, lab hostname or home-directory path in any file, a bench record included.

## Steps

1. Read the board's folder and the part of `_shared/schema.md` (fronts, hotspots, legends) or `docs/models-and-drawings.md` (who writes what, models, schematics) that the change touches.
2. Make the change in the input and run its writer (non-negotiable 3), citing a source for every new value. Commit the regenerated files with the change that caused them.
3. For a schematic, follow [references/kleidos-entries.md](references/kleidos-entries.md) whenever the drawing would differ from the vendor's print.
4. Run the checks in [references/checks.md](references/checks.md) and fix what they report.
5. Keep the pages current in the same change: the board's `README.md` and `schematic/README.md`, and `docs/models-and-drawings.md` or the root `README.md` when a statement there stops being true.

| Load | When |
| --- | --- |
| [references/kleidos-entries.md](references/kleidos-entries.md) | Adding to or correcting a vendor's print: what counts as evidence, the entry format, bench records, the triage file, the README's sections |
| [references/checks.md](references/checks.md) | Before committing: the commands, what each one holds, and what CI repeats |
