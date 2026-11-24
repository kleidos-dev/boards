<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# AGENTS.md — boards

The rules every coding agent follows in this repository (the [AGENTS.md](https://agents.md/) format). `CLAUDE.md` imports this file for Claude Code.

This repository, `kleidos-dev/boards`, is the one place the boards the Kleidos firmware runs on are documented: a true-scale SVG drawing of each face, hand-kept measurements, a sourced component-level specification (`board.json`), a KiCad schematic of each board's connectivity and a 3D model at two levels of detail, with the Python builders and checks that keep them consistent. Its readers are the Kleidos site (built in the firmware repository, `kleidos-dev/kleidos`), the `brand` and `social` repositories, and anyone who needs an accurate drawing or model of one of these boards. It is public. Everything this project writes is MIT (`LICENSE`); the few third-party files and their licenses are listed in `REUSE.toml` and `NOTICE.md`. The boards are M5Stack's and LILYGO's designs: they are documented here from the vendors' public material, cited by address, and no vendor file is ever copied in. `README.md` is the page for people; [`docs/models-and-drawings.md`](docs/models-and-drawings.md) is the working detail (which script writes each file, how drawings, models and schematics are made) to read before changing any of them.

## What is where

- `<board>/`: one folder per board. `svg/front.svg` (written only by `_shared/emit_front_svg.py`, contract in `_shared/schema.md`); `svg/back.svg` and a printing side's `svg/<face>.svg` (written only by `_shared/emit_back_svg.py`); `measurements.json` and `board.json` (by hand, every value with its source, schema `_shared/board.schema.json`); `README.md` (written from `board.json` by `_shared/emit_board_readme.py`); `sources.md` (by hand: the vendor files the front and measurements were taken on, by address); `icon.svg` (drawn by hand, its metadata stamped by `_shared/stamp_icon_meta.py`); `model/` (the recipe `spec.json` by hand; the master and web models and their records written by `_shared/build_board_glb.py`, which also writes the master as Wavefront OBJ and MTL through `_shared/export_obj.py`); `schematic/` (`netlist.yaml` and `layout.yaml` by hand; the KiCad files by `_shared/kicad_schematic.py`; the PDF by `_shared/export_schematic.py`, which also writes one SVG per page into `schematic/svg/`, ignored by git; `bench/` holds the probe records).
- `fronts-contact-sheet.svg` (`_shared/emit_front_svg.py --contact-sheet`) and `models-contact-sheet.png` with its `.json` (`_shared/models_contact_sheet.py`): every board side by side.
- `_shared/`: the builders and checks, Python; `_shared/fixtures/`: the checks' own test board; `_shared/kicad/`: the KiCad kit, copies of brand's (see "Other repositories"). `tests/`: the tests, by marker (`tests/conftest.py`): none for the contracts, `models` for the board models, `selftest` for the checkers' planted defects. `typings/`: type stubs for what ships none. `fonts/`: Inter, unmodified.
- Licensing: `LICENSE` (the MIT License, the same text as `LICENSES/MIT.txt`), `LICENSES/`, `REUSE.toml`, `NOTICE.md`.
- `.claude/skills/`: this repository's agent skills, of which this folder is the source. Load the one that covers the work before starting it:
  - `board-specs-and-schematics`: what a board folder holds and who writes each file, the schematics' Kleidos entries and bench records, the checks.
  - `visual-reference-svg-reconstruction`: measuring a board face on references kept outside the tree and drawing it through the generators, with its overlay tool.
- CI: `.github/workflows/check.yml` (workflow `CI`), its `changes` job deciding which heavy jobs run; SonarQube Cloud settings in `sonar-project.properties` and `.coveragerc`; the review bots in `.coderabbit.yaml` and `.greptile/`, which review against this file.

## Commands

From a fresh clone, with the Python `.python-version` names and, for schematics, KiCad's `kicad-cli` at the version of the image `.github/workflows/check.yml` pins (pip does not install it). The quality kit's hooks install themselves from the release tag `.pre-commit-config.yaml` names; its `kleidos-mypy` hook runs mypy from this environment, so the kit's hashed tools go in it from a checkout of `kleidos-dev/.github` at its branch `v3` beside this clone.

```bash
"python$(cat .python-version)" -m venv .venv && . .venv/bin/activate
pip install --require-hashes -r requirements.txt
git clone --branch v3 https://github.com/kleidos-dev/.github.git ../.github
pip install --require-hashes -r ../.github/quality/requirements-tools.txt
pre-commit install                     # the pre-commit and commit-msg hooks
```

Before a commit, with the environment active (CI runs the same checks):

```bash
pre-commit run --all-files             # the kit's hooks: kit check, agent docs, no-wrap, header lines, ruff, mypy, typos, gitleaks, reuse, markdownlint, actionlint, zizmor
python _shared/check_public_tree.py    # no vendor file, nothing private
python _shared/check_board_specs.py    # every board.json against its schema
python -I _shared/check_metadata.py    # every media file carries its embedded metadata
python -m pytest -m "not models" tests # the contracts: what CI's tests job runs
python -m pytest -m "models and not selftest" tests   # when a model's inputs changed (slow)
python -m pytest -m selftest tests     # when a checker or _shared/fixtures/ changed (slower)
python _shared/export_schematic.py <board> --no-export   # ERC and netlist, when a schematic or the KiCad kit changed
```

Regenerate what a script owns instead of editing it, and commit the regenerated files with the change that caused them: `python _shared/emit_front_svg.py [<board> ...]` then `--contact-sheet`, `python _shared/emit_back_svg.py <board>`, `python _shared/emit_board_readme.py`, `python _shared/stamp_icon_meta.py`, `python _shared/kicad_schematic.py <board>`, `python _shared/export_schematic.py <board>` (the PDF; CI requires it byte for byte a fresh export in its KiCad container), `python _shared/build_board_glb.py <board>/model/spec.json` (`--fetch` downloads the pinned vendor file; `--web-px-per-mm` for the web level, `docs/models-and-drawings.md`), `python _shared/export_obj.py [<board> ...]`, `python _shared/models_contact_sheet.py`. `emit_board_readme.py`, `stamp_icon_meta.py`, `build_board_glb.py`, `export_obj.py` and `models_contact_sheet.py` take `--check`, which writes nothing and fails on a stale file; after any of the others, `git status` shows only what the change meant to change.

## Rules of this repository

- **No vendor file, ever.** Photos, renders, vendor drawings, schematic PDFs, datasheets and CAD files are cited by address and never copied into the tree; the only PDF allowed is a board's own schematic export. `_shared/check_public_tree.py` enforces it.
- **Every value has a source.** A part, pin, value or dimension says where it came from (a vendor page, a datasheet, a measurement); never guess one. What is still uncertain stays out and the board's README lists it as open.
- **Licenses** (owner, 2026-11-17): everything this project writes (code, drawings, data, models, schematics, prose, skills) is MIT, inside OSI-approved licenses and never Creative Commons; Inter is OFL-1.1, the Khronos tone-mapping function Apache-2.0, M5Stack's case geometry MIT with their notice. A new kind of file gets its row in `REUSE.toml` in the same change; a new third-party source gets its notice in `NOTICE.md`.
- **Header lines** (owner, 2026-11-22): the `SPDX-FileCopyrightText` line with the year git first added the file and José M. Requena Plens, no e-mail, then the `SPDX-License-Identifier` line with `MIT` (or the file's own license). A file that cannot carry a comment (JSON, SVG, KiCad files, binaries) and a third-party file get both from a `REUSE.toml` annotation, never a `.license` file. The kit's `kleidos-kit` hook checks them, and a script that writes a file with a header writes both lines.
- **Embedded metadata.** Every media file carries its title, description, author, copyright line, license, address and keywords, written by the script that writes the file from `_shared/media_meta.py` `record()`, never by hand or by exiftool; `_shared/check_metadata.py` holds every file to it. A new kind of media file gets its record in `media_meta.py` (or an exemption with its reason in the checker) in the same change. Nothing of a machine goes in: no clock, path, user, host, e-mail or tool version. The checker's identity patterns live in the git-ignored `_shared/deny-local.txt` (CI reads them from the `KLEIDOS_DENY_EXTRA` secret); never commit that file.
- **Schematics** (owner, 2026-11-17). Describe them as the board's connectivity documented from the vendor's public documentation, never as the vendor's schematic "redrawn" or "copied". Every value in `netlist.yaml` names its source (the vendor's published schematic, its page and version). The drawing improves on the vendor's print: a detail the print does not show goes in when a primary source makes it certain (the chip's datasheet, the vendor's other documents, the Kleidos firmware's verified behavior on that board cited by its repository path and symbol with no commit or line, since the firmware's history will be squashed, or a bench probe), and a drawing error of the print is corrected when the evidence settles it; each is a `kleidos` entry in `netlist.yaml`, marked on the drawing and listed with its source on page 1. One wire width for wires and pin lines. Every cross-reference in the PDF (contents boxes, page links, the `[page/zone]` after a net label, each part's reference and its parts-list row, the index pages, bookmarks) is clickable and lands on the place it names; the PDF holds no script. `_shared/check_schematic.py` and `_shared/check_schematic_links.py` hold them; the format is in `docs/models-and-drawings.md`, "Schematics".
- **Vendor names as the boards print them** (owner, 2026-11-17): `LILYGO`, never a mixed-case form, in prose, data, drawings and schematics; an address, the vendor organization's own name, a vendor file's name and this project's lowercase identifiers (`lilygo-wiki`) keep theirs. `tests/test_vendor_names.py` fails on any other spelling.
- **US spelling** (the kit's typos check); a vendor's pin or net name stays as printed and is listed in `.typos.toml`.
- **Python is typed**: every function annotated, mypy strict with no error and no baseline; a library that ships no types gets a stub under `typings/` or, when it is optional, an `ignore_missing_imports` override in `pyproject.toml` with its reason. Every CI job runs the code on the Python `.python-version` names, the schematic job too (uv installs it beside the KiCad image's own), and ruff's `target-version` in `pyproject.toml` is that version's.
- **A path given is a path checked.** A file or a board that the command line of a script of `_shared/`, or a data file it reads (a spec, a record), names goes through `_shared/paths.py` where it comes in (`work_path`, `in_tree`, `beside`, `board_id`, `inside`) and is used as checked: a command's files lie in this repository, the folder it runs in or the folder for temporary files, a recorded path in this repository, what a spec names from its own folder in this repository or its board's folder, a vendor file also in its cache. The folder a command runs in is trusted, so run it from this repository, never from `/` or a home folder. No argument names a program to run (`KICAD_CLI` in the environment does), a vendor file comes over https from one of the builder's `VENDOR_ADDRESSES`, a count a spec asks for has a bound, and what a script of `_shared/` (the KiCad kit is brand's) reads out of a drawing or a file's text is read in linear time (`_shared/svg_read.py`). `tests/test_paths.py` plants a path that leads out in every argument, `tests/test_svg_read.py` times what reads a text on hostile ones. The overlay tool of the `visual-reference-svg-reconstruction` skill is the one command that works outside the tree: it writes only there and refuses an output inside it.
- **The formats are contracts.** Brand and the site read `<board>/svg/front.svg` (its glass, annotations, hotspots and legend groups, `_shared/schema.md`), `measurements.json`, `_shared/graphite.json` and the models with their `web.json` by their paths from this repository's root. A change to a path or a format is a change for every reader: say so in the pull request. The digests readers pin the models by are in `docs/models-and-drawings.md`, "Model digests".
- **The quality kit is run, not held**: CI calls its entry workflows at `@v3` and the hooks take it at a release tag; the base configurations under `.github/quality/` (but `waivers.toml`), `.gitleaks-mac.toml` and `.github/zizmor.yml` are recorded in `.github/quality/SOURCE.json` and never edited here. A weakening of a kit rule needs an entry in `.github/quality/waivers.toml`.
- **SonarQube Cloud is secretless** (OIDC, no `SONAR_TOKEN`); a setting the scanner can read goes in `sonar-project.properties`, never in its web interface.
- **What `_shared/check_public_tree.py` cannot see.** It fails on a serial-port path, a MAC address, a private IPv4 address, a home-directory path and an e-mail address other than the project's; a hostname or a secret it cannot know, so read a bench record before committing it.

## Organization rules

The rules every kleidos-dev repository shares are the [organization rules](https://github.com/kleidos-dev/.github/blob/main/quality/agents/block.md): read them before changing anything here.

## Other repositories

Nothing here is a submodule and nothing mounts this repository; the links are copies pinned by commit and digest, and files read by address.

| Repository | Link | Kept in step by |
| --- | --- | --- |
| `kleidos-dev/.github` | The quality kit: every CI job but this repository's own, through its entry workflows called at `@v3`; its hooks at a release tag; the base configurations recorded in `.github/quality/SOURCE.json` | A kit release moves `v3`, and the next run takes it; Dependabot moves the hooks' `rev`; `kleidos-dev/.github/tools/ecosystem.py refresh` writes newer base configurations; a new major is a pull request here |
| `kleidos-dev/brand` | Gives `_shared/kicad/` (the KiCad style: drawing sheets, themes, `style.json`, `kleidos_kicad.py`), byte copies held to `_shared/kicad/KIT.json` by `tests/test_kicad_kit.py`. Takes the fronts into its own `boards/` | Never edit `_shared/kicad/`: change brand, run its `kleidos-dev/brand/tools/sync_kicad.py --copy <this checkout>/_shared/kicad`, then generate and export every schematic again. Brand takes fronts with its `kleidos-dev/brand/tools/sync_from_boards.py --copy` |
| `kleidos-dev/brand`, `social/` (the social pack, the `kleidos-dev/social` repository until 2026-11-24) | The README banner: the block at the top of `README.md` reads `social/svg/readme/boards/banner-{dark,light}.svg` from brand's `main` by address, so no banner file is here | Change the banner there; `kleidos-dev/brand/social/tools/sync_readme_banners.py --print boards` prints the block and `--check <this checkout>` checks it. `_shared/check_public_tree.py` refuses any SVG here that embeds a picture, a banner copy included |
| `kleidos-dev/kleidos` (the firmware and the site) | Takes byte copies of the fronts, the measurements and `_shared/graphite.json` for the site, pinned to a commit of this repository's `main` with each file's digest, and reads the models from a checkout when it cuts its web models | The firmware's own copy script; here, only the formats above |
| `kleidos-dev/agents` | The `kleidos-boards` plugin holds copies of the two skills under `.claude/skills/`, which are the source | A change to a skill here is copied there in the same work item |
