# SPDX-License-Identifier: MIT
"""Fail when the tree holds a file or a line this repository may not publish.

Vendor files never enter this repository (``NOTICE.md``): no product photos,
renders, reference overlays, silhouettes traced from community CAD files,
STL / STEP files, schematic PDFs or datasheets. They are cited by address
instead. This guard reads every file git tracks (or, outside a git checkout,
every file under the root) and fails on:

- a raster image other than ``models-contact-sheet.png`` (ours, rendered from
  our models), a PDF other than a board's own schematic export
  (``<board>/schematic/<board>.pdf`` beside its ``<board>.kicad_sch``), or a
  CAD file (``.stl``, ``.step``, ``.stp``, ``.obj``, ``.mtl``,
  ``.3mf``, ``.f3d``, ``.zip``) other than the two boxes of the checks' own
  test board (``_shared/fixtures/faces/vendor/*.stl``), admitted only while
  their bytes are the ones ``_shared/face_fixture.py`` writes, and a board's
  own OBJ and MTL (``<board>/model/<board>.obj`` and ``.mtl``, beside the
  ``<board>.glb`` and ``spec.json`` ``_shared/export_obj.py`` writes them
  from; ``tests/test_board_model_obj.py`` holds their bytes to that GLB);
- a path under a ``reference/``, ``reference_candidates/``, ``raw/`` or
  ``photos/`` folder, a ``*_reference.svg`` or a ``*-silhouette.svg``;
- an SVG that embeds an image (``<image``, ``data:image``) or draws a vendor
  demo screen (``id="screen-demo"``). The README banner, which carries the
  Kleidos firmware's own unlock screens on these fronts, is not in this tree:
  the README reads it from the social repository by its address;
- a text file (prose, data, code, KiCad sources) that names something private
  (``AGENTS.md``, "Nothing private"): a serial-port device path, a MAC
  address, a private IPv4 address, a home-directory path, or an e-mail address
  other than the project's. A bench record says "the board's USB port", never
  the port it had on the bench. The drawings (``.svg``) are generated from the
  files read here and are not read again.

Path patterns and markers only: nothing here measures a size.

Usage: ``python3 _shared/check_public_tree.py [ROOT]``; exit 1 on a finding.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_RASTERS = {"models-contact-sheet.png"}
RASTER = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp", ".tif", ".tiff", ".heic"}
VENDOR = {".pdf", ".stl", ".step", ".stp", ".obj", ".mtl", ".3mf", ".f3d", ".zip", ".dxf", ".dwg"}
FOLDERS = {"reference", "reference_candidates", "raw", "photos"}
SVG_MARKERS = (
    re.compile(r"<image\b"),
    re.compile(r"data:image"),
    re.compile(r"""id=["']screen-demo["']"""),
)
TEXT = {
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".toml",
    ".txt",
    ".cfg",
    ".ini",
    ".sh",
    ".kicad_sch",
    ".kicad_pro",
    ".kicad_sym",
    "",
}
PROJECT_EMAIL = "jmrplens@kleidos.dev"
PRIVATE = (
    ("a serial-port device path", re.compile(r"/dev/(?:cu|tty)\.[\w-]+|/dev/tty(?:USB|ACM|S)\d+")),
    (
        "a MAC address",
        re.compile(r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f:])"),
    ),
    (
        "a private IPv4 address",
        re.compile(
            r"(?<![\w.])(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))"
            r"\.\d{1,3}\.\d{1,3}(?![\w.])"
        ),
    ),
    ("a home-directory path", re.compile(r"/(?:Users|home)/[\w.-]+|[A-Za-z]:\\Users\\")),
    (
        "an e-mail address other than the project's",
        re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b"),
    ),
)


def tracked(root: Path) -> list[Path]:
    """The files git tracks or would add, else every file under *root*."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout
        return [root / name for name in out.decode("utf-8").split("\0") if name]
    except OSError, subprocess.CalledProcessError:
        return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def own_schematic_pdf(root: Path, rel: Path) -> bool:
    """True for ``<board>/schematic/<board>.pdf`` next to the KiCad
    schematic it was exported from."""
    parts = rel.parts
    return (
        len(parts) == 3
        and parts[1] == "schematic"
        and rel.name == f"{parts[0]}.pdf"
        and (root / parts[0] / "schematic" / f"{parts[0]}.kicad_sch").is_file()
    )


def own_model_export(root: Path, rel: Path) -> bool:
    """True for ``<board>/model/<board>.obj`` or ``.mtl`` beside that board's own GLB and spec.

    The two files are written from the board's master model by
    ``_shared/export_obj.py``; anywhere else an OBJ or an MTL is a CAD file
    from somewhere else, and is refused.
    """
    parts = rel.parts
    return (
        len(parts) == 3
        and parts[1] == "model"
        and rel.suffix.lower() in {".obj", ".mtl"}
        and rel.stem == parts[0]
        and (root / parts[0] / "model" / f"{parts[0]}.glb").is_file()
        and (root / parts[0] / "model" / "spec.json").is_file()
    )


def own_fixture_stl(root: Path, rel: Path) -> bool:
    """True for an STL of the face fixture whose bytes are the ones ``face_fixture.py`` writes.

    The fixture's two boxes are ours, drawn by ``_shared/face_fixture.py`` and
    pinned by its spec like a vendor's file. A file at that place with any
    other bytes is not admitted.
    """
    parts = rel.parts
    if not (
        len(parts) == 5
        and parts[:3] == ("_shared", "fixtures", "faces")
        and parts[3] == "vendor"
        and rel.suffix.lower() == ".stl"
    ):
        return False
    shared = str(root / "_shared")
    sys.path.insert(0, shared)
    try:
        import face_fixture

        written = face_fixture.files()
    except ImportError, OSError:
        return False
    finally:
        sys.path.remove(shared)
    data = written.get(Path(*parts[3:]).as_posix())
    return data is not None and (root / rel).read_bytes() == data


def private_lines(rel: Path, text: str) -> list[str]:
    """Every line of *text* that names something private, as ``path:line: what``.

    The match itself is not printed: a finding in a CI log must not repeat it.
    """
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        for what, pattern in PRIVATE:
            if any(match.group(0) != PROJECT_EMAIL for match in pattern.finditer(line)):
                found.append(f"{rel}:{number}: {what}")
    return found


def findings(root: Path) -> list[str]:
    """Every file the repository may not publish, with why."""
    found = []
    for path in sorted(tracked(root)):
        rel = path.relative_to(root)
        parts = set(rel.parts[:-1])
        suffix = rel.suffix.lower()
        name = rel.name
        if parts & FOLDERS:
            found.append(f"{rel}: under a vendor reference folder")
        elif suffix in RASTER and name not in ALLOWED_RASTERS:
            found.append(f"{rel}: a raster image")
        elif (
            suffix in VENDOR
            and not own_schematic_pdf(root, rel)
            and not own_fixture_stl(root, rel)
            and not own_model_export(root, rel)
        ):
            found.append(f"{rel}: a vendor file type ({suffix})")
        elif name.endswith(("_reference.svg", "-silhouette.svg")):
            found.append(f"{rel}: a reference overlay or a traced silhouette")
        elif suffix == ".svg" and path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            found.extend(
                f"{rel}: holds {marker.pattern!r}" for marker in SVG_MARKERS if marker.search(text)
            )
        elif suffix in TEXT and path.is_file() and "LICENSES" not in parts:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            found.extend(private_lines(rel, text))
    return found


def main(argv: list[str]) -> int:
    root = Path(argv[0]).resolve() if argv else ROOT
    found = findings(root)
    for line in found:
        print(f"FAIL {line}")
    if not found:
        print("ok   no vendor file and nothing private in the tree")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
