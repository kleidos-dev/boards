# Checks of this repository

Run from the repository root, in its own virtual environment (Python 3.15, the version each model's `source.json` records):

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/reuse lint                                          # every file has its license
.venv/bin/python _shared/check_public_tree.py                 # no vendor file, nothing private
.venv/bin/python _shared/check_board_specs.py                 # every board.json
.venv/bin/python -m pytest -m "not models" tests              # the contracts (fast)
.venv/bin/python -m pytest -m "models and not selftest" tests # every model against what builds it
.venv/bin/python -m pytest -m selftest tests                  # the checkers' planted defects (slow)
.venv/bin/python _shared/emit_front_svg.py --contact-sheet    # regenerate every front; a second run changes nothing
.venv/bin/python _shared/kicad_schematic.py <board>           # a schematic from its netlist.yaml and layout.yaml
.venv/bin/python _shared/export_schematic.py <board>          # ERC, netlist, PDF, SVG pages (ignored by git) and links (needs kicad-cli 10.0.8)
.venv/bin/python -I _shared/build_board_glb.py <board>/model/spec.json --fetch --check   # a model, byte for byte
```

| Check | What it holds |
| --- | --- |
| `reuse lint` | Every file is covered by a `REUSE.toml` row or an SPDX header |
| `check_public_tree.py` | No vendor photo, render, overlay, traced silhouette, CAD file, schematic PDF or datasheet in the tree, tracked or untracked: the only raster is `models-contact-sheet.png`, the only PDF a board's own schematic export, the only OBJ and MTL a board's own (`<board>/model/<board>.obj` and `.mtl` beside its GLB and spec). And nothing private in a text file: no serial-port device path, MAC address, private IPv4 address, home-directory path or e-mail address other than the project's (`tests/test_public_tree.py` plants each) |
| `check_board_specs.py` | `board.json` against `_shared/board.schema.json`, plus what a schema cannot state: every source id resolves, every address is https, every date is real and not in the future, and the fields repeated in `measurements.json` agree |
| `pytest -m "not models" tests` | The front and back contracts (`screen-active`, `annotations`, `hotspots`, legend groups), the specifications, the vendor names spelled as the boards print them (`tests/test_vendor_names.py`: `LILYGO` outside addresses and identifiers), and the schematic generator's own tests; the ones that need KiCad's symbol libraries or kicad-cli skip where KiCad is not installed |
| `pytest -m "models and not selftest" tests` | Each model built from its drawings and spec as they are now, its legends where its drawings print them, its materials at separate depths, its web level the master less what a reader cannot see, its OBJ and MTL what its GLB gives and read back by trimesh as the GLB (`tests/test_board_model_obj.py`) |
| `pytest -m selftest tests` | The checkers catch the defects planted in a model or a drawing, and the face fixture rebuilds byte for byte |
| `emit_front_svg.py` | Regenerates the fronts; `git diff` after it must be empty unless the generator changed |
| `kicad_schematic.py` | Regenerates a schematic's KiCad files; the same inputs give the same bytes, and a malformed `kleidos` entry is refused |
| `export_schematic.py` | KiCad's ERC with no message, the drawn netlist pin for pin against `netlist.yaml` (`check_schematic.py`), every Kleidos entry marked and listed, the PDF and SVGs in the Kleidos theme, and every link of the PDF landing on the place it names (`check_schematic_links.py`); `--no-export` checks without writing, `--out DIR` writes elsewhere |
| `build_board_glb.py --fetch --check` | Rebuilds a model from the pinned vendor CAD file, downloaded into a cache outside the tree (`$KLEIDOS_CAD_CACHE`), and compares it with the committed bytes |
| `check_board_model.py <board directory>` | A model's silhouette, size, screen rectangle and legends against the drawings and `measurements.json`; its views go to a temporary directory, never the tree |

## What CI repeats, and what it does not

`.github/workflows/check.yml` (workflow `CI`), on every push to `main` and every pull request. `changes` and `check` start together; the three heavy jobs wait for `check` (`needs:`), so a red licence, tree or contract check skips them:

- `check` (`🧪 Tree checks and tests`, Python 3.15, the pinned `requirements.txt`): `reuse lint`, `check_public_tree.py`, `check_board_specs.py` and `pytest -m "not models" tests`. It has no KiCad, so the schematic tests that need it skip there and run in the `schematic` job.
- `models` (`🔨 Board models`), when a model's inputs changed (a board's `model/`, `svg/` or `measurements.json`, `_shared/`, `fonts/`, `requirements.txt`, the model tests): `pytest -m "models and not selftest" tests`.
- `selftests` (`🧪 Checker selftests`), when a checker or its fixtures changed, every Monday and on demand: `pytest -m selftest tests`.
- `schematic` (`🧫 Schematics`), unless the change touches only Markdown, the models' `model/` and `svg/` folders and the contact sheets, in the `kicad/kicad:10.0.8` container, which brings kicad-cli 10.0.8 (no KiCad library is read: every symbol is this project's): for every board with a `schematic/netlist.yaml`, the ERC and netlist check, the committed PDF's links, a fresh export to a temporary folder, and `tests/test_schematic.py`. The container has its own Python and PyYAML; the job installs only `pytest` and `pypdf` into it, at the versions `requirements.txt` pins.

Local only, never in CI:

- regenerating the fronts and the backs (`emit_front_svg.py`, `emit_back_svg.py`): run them after touching a generator and commit what they write;
- rebuilding a model from the vendor's CAD file (`build_board_glb.py --fetch --check`): it downloads a vendor file, which CI does not do; CI holds each model to its drawings, spec and records instead;
- `check_board_model.py` and `models_contact_sheet.py`, which draw views.

`.github/workflows/commit-check.yml` checks the commit messages of every pull request (72 columns, imperative subject, no attribution lines) with `.github/commit-check/check_commit_msg.py`; the same script is the `commit-msg` hook of `.pre-commit-config.yaml` (`pre-commit install --hook-type commit-msg`). Both are copies kept by `kleidos-dev/agents`: change them there.
