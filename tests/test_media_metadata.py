# SPDX-License-Identifier: MIT
"""Every published media file carries its embedded-metadata record, and the checker catches what is planted.

``_shared/media_meta.py`` derives one record per media file and writes it in
each format; the builders call it, and ``_shared/check_metadata.py`` holds
every committed file to it. This holds:

- every tracked drawing, model, schematic and picture passes the checker;
- the license and holders a record states are what ``reuse spdx`` states for
  the file, and the metadata adds no copyright notice REUSE would read;
- the writers give the golden bytes in ``tests/fixtures/meta/`` for one fixed
  record (the standard's shared fixtures), with no machine date, path or
  tool version in them;
- each rule finds the defect planted for it;
- the models' contact sheet was drawn from the models as they are.

Host-only: no build, no hardware, no network.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))
import check_metadata  # noqa: E402
import media_meta as mm  # noqa: E402
from paths import BOARDS  # noqa: E402

GOLDEN = ROOT / "tests" / "fixtures" / "meta"


def library(name: str):
    try:
        return __import__(name)
    except ImportError:
        if os.environ.get("CI"):
            pytest.fail(f"{name} is not installed: a broken install of requirements.txt")
        pytest.skip(f"{name} is not installed: pip install -r requirements.txt")


def media_files() -> list[str]:
    return [
        rel for rel in check_metadata.tracked() if Path(rel).suffix.lower() in check_metadata.MEDIA
    ]


# --- the committed files ------------------------------------------------------------


def test_every_media_file_carries_its_record() -> None:
    """The checker finds nothing in the tree as committed."""
    library("pypdf")
    found = {rel: check_metadata.check(rel, mm.identity_patterns()) for rel in media_files()}
    assert {rel: f for rel, f in found.items() if f} == {}


def test_every_media_file_has_a_record_or_a_reason() -> None:
    """A media file the checker would not know is one a builder forgot."""
    for rel in media_files():
        if check_metadata.exemption(rel):
            continue
        mm.record(rel)  # raises for a path with no record


def test_every_kind_of_file_is_checked() -> None:
    kinds = {Path(rel).suffix for rel in media_files() if not check_metadata.exemption(rel)}
    assert kinds <= set(check_metadata.CHECKS), kinds - set(check_metadata.CHECKS)
    assert kinds == {".svg", ".glb", ".obj", ".mtl", ".png", ".pdf"}


def _reuse_spdx() -> dict[str, tuple[set[str], set[str]]]:
    """{path: (license identifiers, copyright texts without e-mail)} as ``reuse spdx`` states them."""
    if shutil.which("reuse") is None and not (Path(sys.executable).parent / "reuse").exists():
        if os.environ.get("CI"):
            pytest.fail("reuse is not installed: a broken install of requirements.txt")
        pytest.skip("reuse is not installed: pip install -r requirements.txt")
    exe = shutil.which("reuse") or str(Path(sys.executable).parent / "reuse")
    out = subprocess.run([exe, "spdx"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    files: dict[str, tuple[set[str], set[str]]] = {}
    for block in out.split("\n\n"):
        name = re.search(r"^FileName: \./(.+)$", block, re.M)
        if not name:
            continue
        licenses = set(re.findall(r"^LicenseInfoInFile: (.+)$", block, re.M))
        text = re.search(r"^FileCopyrightText: <text>(.*?)</text>", block, re.M | re.S)
        holders = set()
        for line in text.group(1).splitlines() if text else []:
            line = re.sub(rf"^{mm.TAG_COPYRIGHT}:\s*", "", line.strip())
            holders.add(re.sub(r"\s*<[^>]*>", "", line).strip())
        files[name.group(1)] = (licenses, holders)
    return files


def test_the_records_state_what_reuse_states() -> None:
    """License and holders per file are REUSE's, and REUSE reads no notice out of the metadata."""
    spdx = _reuse_spdx()
    for rel in media_files():
        if check_metadata.exemption(rel):
            continue
        meta = mm.record(rel)
        licenses, holders = spdx[rel]
        assert set(mm.license_ids(meta.spdx)) == licenses, rel
        assert set(meta.holders) == holders, f"{rel}: REUSE reads {holders}"


# --- the writers --------------------------------------------------------------------


def golden_record() -> mm.MediaMeta:
    """One fixed record, the shape the standard's shared fixtures are written from."""
    return mm.MediaMeta(
        path="sample/model/sample.glb",
        title="Sample board (S-1) 3D model",
        description="A fixed record for the writers' golden files.",
        alt="A sample board.",
        keywords=("Kleidos", "hardware password manager", "open source", "sample"),
        digital_source_type="digitalCreation",
        spdx="MIT",
        own_license="MIT",
        holders=("2026 José M. Requena Plens", "2021 M5Stack"),
        credits=("Case geometry: a sample & a <test>, MIT, \u00a9 2021 M5Stack.",),
        trademarks=(mm.TRADEMARK_NOTE_M5,),
        media_type="model/gltf-binary",
        slug="kl-sample",
        extra={"scene": "Sample board (S-1)"},
    )


def golden_outputs() -> dict[str, bytes]:
    meta = golden_record()
    asset, packets, scene = mm.gltf_metadata(meta)
    chunks = b"".join(k + b"\0" + b + b"\n" for k, b in mm.png_metadata_chunks(meta, "full"))
    return {
        "sample.xmp": mm.xmp_packet(meta).encode("utf-8"),
        "sample-short.xmp": mm.xmp_packet(meta, "short").encode("utf-8"),
        "sample.png-chunks": chunks,
        "sample.svg-block": mm.svg_block(meta).encode("utf-8"),
        "sample.gltf.json": (
            json.dumps(
                {"asset": asset, "extensions": packets, "scene": scene},
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        ).encode("utf-8"),
        "sample.obj.txt": ("\n".join(mm.obj_header(meta)) + "\n").encode("utf-8"),
    }


@pytest.mark.parametrize("name", sorted(golden_outputs()))
def test_the_writers_give_the_golden_bytes(name: str) -> None:
    assert (GOLDEN / name).read_bytes() == golden_outputs()[name], (
        f"{name}: the writer changed; bump META_PROFILE and rewrite tests/fixtures/meta/"
    )


def test_the_golden_bytes_hold_nothing_private_and_no_machine_trace() -> None:
    for name, data in golden_outputs().items():
        text = data.decode("latin-1" if name.endswith(".png-chunks") else "utf-8")
        assert mm.deny_hits(text) == [], name
        assert "xmptk" not in text and "CreatorTool" not in text, name
        assert '<?xpacket end="r"?>' in text or not name.endswith(".xmp")


def test_the_xmp_structure_is_not_mistaken_for_tool_noise() -> None:
    """Namespace URIs and prefixes (ns.adobe.com, photoshop:) are structure, never a deny hit."""
    packet = mm.xmp_packet(golden_record())
    assert re.search(r'xmlns:photoshop="http://ns\.adobe\.com/photoshop/1\.0/"', packet)
    assert re.search(r"<photoshop:Credit>", packet)
    assert mm.deny_hits(packet) == []


def test_a_title_over_its_limit_and_a_long_copyright_are_refused() -> None:
    import dataclasses

    with pytest.raises(mm.MetaError, match="over 64 bytes"):
        mm._check(dataclasses.replace(golden_record(), title="x" * 65))
    with pytest.raises(mm.MetaError, match="over 128 bytes"):
        mm._check(dataclasses.replace(golden_record(), holders=("y" * 130,)))


def test_reuse_truth_strips_the_email_and_follows_precedence() -> None:
    spdx, holders = mm.reuse_truth("sticks3/model/sticks3.glb")
    assert spdx == "MIT" and holders == ("2026 José M. Requena Plens", "2021 M5Stack")
    assert mm.reuse_truth("fonts/inter/Inter-Bold.ttf") == (
        "OFL-1.1",
        ("2016 The Inter Project Authors",),
    )
    assert mm.reuse_truth("_shared/model_raster.py")[0] == "MIT AND Apache-2.0"
    assert not any("@" in h for b in BOARDS for h in mm.reuse_truth(f"{b}/svg/front.svg")[1])


def test_stamping_is_idempotent_and_leaves_the_drawing() -> None:
    """Stamped twice is stamped once; unstamped, a file is its drawing as the builder drew it."""
    for rel in media_files():
        if not rel.endswith(".svg") or check_metadata.exemption(rel):
            continue
        text = (ROOT / rel).read_text(encoding="utf-8")
        meta = mm.record(rel)
        assert mm.stamp_svg(text, meta) == text, rel
        bare = mm.unstamp_svg(text)
        assert "<metadata" not in bare.split(">", 2)[1] and mm.REUSE_START not in bare, rel
        assert bare.count("\n") == text.count("\n") - mm.svg_block(meta).count("\n") - 1, rel


# --- each rule catches what is planted ----------------------------------------------


def rules(found) -> set[str]:
    return {rule for rule, _ in found}


@pytest.fixture(scope="module")
def front() -> tuple[str, str, mm.MediaMeta]:
    rel = "sticks3/svg/front.svg"
    return rel, (ROOT / rel).read_text(encoding="utf-8"), mm.record(rel)


def test_svg_plants(front) -> None:
    rel, text, meta = front
    assert check_metadata.check_svg(rel, text.encode(), meta, None) == []
    changed = text.replace(meta.title, "Another title", 1)
    assert "M002" in rules(check_metadata.check_svg(rel, changed.encode(), meta, None))
    unmarked = text.replace(f"<!-- {mm.REUSE_START} -->\n", "", 1)
    assert "M011" in rules(check_metadata.check_svg(rel, unmarked.encode(), meta, None))
    mailed = text.replace("Part of Kleidos boards.", "Write to someone" + "@example.com.", 1)
    assert "M004" in rules(check_metadata.check_svg(rel, mailed.encode(), meta, None))
    edited = text.replace('lang="en">', 'lang="en" xmlns:sodipodi="x">', 1)
    assert "M005" in rules(check_metadata.check_svg(rel, edited.encode(), meta, None))
    gpl = text.replace(f"{mm.TAG_LICENSE}: MIT", f"{mm.TAG_LICENSE}: GPL-3.0-or-later", 1)
    assert "M003" in rules(check_metadata.check_svg(rel, gpl.encode(), meta, None))


def test_an_identity_pattern_is_found_and_never_printed(front) -> None:
    rel, text, meta = front
    pattern = [re.compile("kleidos boards", re.I)]
    found = check_metadata.check_svg(rel, text.encode(), meta, pattern)
    assert "M004" in rules(found)
    assert all("kleidos boards" not in message.lower() for _, message in found)


def _glb(rel: str, change) -> bytes:
    data = (ROOT / rel).read_bytes()
    n = struct.unpack_from("<I", data, 12)[0]
    js = json.loads(data[20 : 20 + n])
    change(js)
    text = json.dumps(js, separators=(",", ":"), ensure_ascii=False).encode()
    while len(text) % 4:
        text += b" "
    rest = data[20 + n :]
    return (
        struct.pack("<III", 0x46546C67, 2, 20 + len(text) + len(rest))
        + struct.pack("<II", len(text), 0x4E4F534A)
        + text
        + rest
    )


def test_glb_plants() -> None:
    rel = "sticks3/model/sticks3.glb"
    meta = mm.record(rel)
    assert check_metadata.check_glb(rel, (ROOT / rel).read_bytes(), meta, None) == []
    found = check_metadata.check_glb(
        rel, _glb(rel, lambda js: js["asset"].__setitem__("copyright", "Someone else")), meta, None
    )
    assert "M002" in rules(found)
    found = check_metadata.check_glb(rel, _glb(rel, lambda js: js.pop("extensions")), meta, None)
    assert "M001" in rules(found)
    found = check_metadata.check_glb(
        rel, _glb(rel, lambda js: js["asset"].__setitem__("minVersion", "2.0")), meta, None
    )
    assert "M005" in rules(found)
    found = check_metadata.check_glb(
        rel, _glb(rel, lambda js: js["asset"]["extras"].__setitem__("title", "x")), meta, None
    )
    assert {"M002", "M007"} <= rules(found)


def test_obj_plants() -> None:
    rel = "tdeck-plus/model/tdeck-plus.obj"
    meta = mm.record(rel)
    data = (ROOT / rel).read_bytes()
    assert check_metadata.check_obj(rel, data, meta, None) == []
    changed = data.replace(b"# Title: ", b"# Title: not ", 1)
    assert "M002" in rules(check_metadata.check_obj(rel, changed, meta, None))
    moved = data.replace(f"# {mm.REUSE_START}\n".encode(), b"", 1)
    assert "M011" in rules(check_metadata.check_obj(rel, moved, meta, None))
    other = data.replace(
        b"Requena Plens\n", f"Requena Plens\n# {mm.TAG_COPYRIGHT}: 2025 X\n".encode(), 1
    )
    assert "M003" in rules(check_metadata.check_obj(rel, other, meta, None))


def _png(chunks) -> bytes:
    return mm.PNG_SIGNATURE + b"".join(mm._chunk(k, b) for k, b in chunks)


def test_png_plants() -> None:
    rel = "models-contact-sheet.png"
    meta = mm.record(rel)
    data = (ROOT / rel).read_bytes()
    assert check_metadata.check_png(rel, data, meta, None) == []
    chunks = mm.png_chunks_of(data)
    timed = chunks[:1] + [(b"tIME", b"\x07\xea\x0b\x13\x0c\x00\x00")] + chunks[1:]
    assert "M005" in rules(check_metadata.check_png(rel, _png(timed), meta, None))
    no_xmp = [c for c in chunks if c[0] != b"iTXt"]
    assert "M002" in rules(check_metadata.check_png(rel, _png(no_xmp), meta, None))
    texts = [c for c in chunks if c[0] in (b"tEXt", b"iTXt")]
    late = [c for c in chunks if c[0] not in (b"tEXt", b"iTXt", b"IEND")] + texts + chunks[-1:]
    assert "M006" in rules(check_metadata.check_png(rel, _png(late), meta, None))
    short = [c for c in chunks if c[0] not in (b"tEXt", b"iTXt")]
    at = next(i for i, c in enumerate(short) if c[0] == b"IDAT")
    short = short[:at] + mm.png_metadata_chunks(meta, "short") + short[at:]
    assert "M009" in rules(check_metadata.check_png(rel, _png(short), meta, None))


def test_pdf_plants() -> None:
    pypdf = library("pypdf")
    rel = "m5stickc-plus2/schematic/m5stickc-plus2.pdf"
    meta = mm.record(rel)
    data = (ROOT / rel).read_bytes()
    assert check_metadata.check_pdf(rel, data, meta, None) == []
    writer = pypdf.PdfWriter(clone_from=pypdf.PdfReader(io.BytesIO(data)))
    writer.add_metadata({"/Title": "Another title", "/Trapped": "/False"})
    out = io.BytesIO()
    writer.write(out)
    found = rules(check_metadata.check_pdf(rel, out.getvalue(), meta, None))
    assert {"M002", "M005", "M007"} <= found


def test_a_media_file_without_a_record_is_found() -> None:
    assert rules(check_metadata.check("sticks3/svg/new-view.png", None)) == {"M008"}
    assert check_metadata.check("fonts/inter/Inter-Bold.ttf", None) == []


def test_the_checker_fails_closed_when_ci_asks_for_identity(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(mm.IDENTITY_ENV, "")
    monkeypatch.setattr(mm, "IDENTITY_FILE", tmp_path / "none.txt")
    assert check_metadata.main(["--require-identity", str(ROOT / "sticks3/icon.svg")]) == 1
    assert check_metadata.main([str(ROOT / "sticks3/icon.svg")]) == 0


# --- the models' contact sheet ------------------------------------------------------


def test_the_contact_sheet_was_drawn_from_the_models_as_they_are() -> None:
    rec = json.loads((ROOT / "models-contact-sheet.json").read_text(encoding="utf-8"))
    data = (ROOT / rec["sheet"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == rec["sha256"] and len(data) == rec["bytes"]
    for board, model in rec["models"].items():
        digest = hashlib.sha256((ROOT / model["model"]).read_bytes()).hexdigest()
        assert digest == model["model_sha256"], (
            f"{model['model']} changed since the sheet was drawn: "
            "run python -I _shared/models_contact_sheet.py"
        )
    assert set(rec["models"]) == set(BOARDS)
