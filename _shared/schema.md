<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# Device measurements schema

Each device folder contains a `measurements.json` following this schema. All distances are in **millimeters**. The coordinate origin is the **top-left corner of the front face**, X to the right, Y downwards (same convention as SVG).

```jsonc
{
  "device_id": "m5stickc-plus2",
  "display_name": "M5StickC Plus2",
  "vendor": "M5Stack",
  "sku": "K016-P2",
  "revision": "2023-09",
  "sources": [
    { "kind": "datasheet", "url": "..." },
    { "kind": "step",      "url": "..." },
    { "kind": "schematic", "url": "..." },
    { "kind": "photo",     "url": "..." }
  ],

  "case": {
    "width": 24.0,
    "height": 48.0,
    "depth": 13.5,
    "corner_radius": 3.0,
    "color": "#FEB722",
    "material": "PC"
  },

  "display": {
    "tech": "TFT-IPS",
    "controller": "ST7789v2",
    "active_w_mm": 14.86,
    "active_h_mm": 24.91,
    "resolution_w_px": 135,
    "resolution_h_px": 240,
    "origin_x_mm": 4.57,
    "origin_y_mm": 3.535,
    "native_orientation": "portrait",
    "firmware_rotation_deg": 180
  },

  "buttons": [
    {
      "id": "BtnA",
      "logical": "primary",
      "gpio": 37,
      "active": "low",
      "face": "front",
      "shape": "circle",
      "diameter_mm": 7.0,
      "center_x_mm": 12.05,
      "center_y_mm": 38.81,
      "label_on_case": "M5"
    },
    {
      "id": "BtnB",
      "logical": "secondary",
      "gpio": 39,
      "active": "low",
      "face": "right",
      "shape": "rect",
      "width_mm": 3.5,
      "height_mm": 3.69,
      "center_x_mm": 24.0,
      "center_y_mm": 15.805
    }
  ],

  "extras": [
    { "type": "led",        "face": "front", "color": "red" },
    { "type": "microphone", "face": "front" },
    { "type": "usb-c",      "face": "bottom" }   // center_x_mm / center_y_mm once measured
  ],

  "notes": "Free-form text. Cite exact source pages used."
}
```

## Field rules

- All coordinates measured from the front-face top-left, even for elements on other faces (use `face` to disambiguate; on side faces, X spans 0..width, Y is along the depth axis when relevant — document in `notes`).
- `firmware_rotation_deg` is the rotation the Kleidos firmware applies to the panel (its `DISPLAY_ROTATION` build flag), so a screenshot composited into the drawing matches what the user sees.
- A coordinate that has not been measured is `null`, with a `note` saying what is missing and how to get it. An invented number is worse than a gap: it reads as measured. The CoreInk's status LED, which sits inside the case, is the one such entry today.
- Sources must be reproducible: prefer official vendor URLs. A source is cited by its address and never copied into this repository (vendor photos, renders, schematics, datasheets and CAD files stay with their owners; `NOTICE.md`).
- A keyboard board adds a `keyboard` block, which is geometry and wiring only: `rows`, `cols`, `origin_x_mm`, `origin_y_mm`, `key_w_mm`, `key_h_mm`, `gap_mm` (the grid of its regular rows, which the Kleidos site's schematic of the board draws), `controller`, `i2c_addr` and `notes`. It does not list what the keys print. The legends have one source, the generator's own tables, and one place a reader finds them: the board's `svg/front.svg`, whose `hs-key-<slug>` hotspots carry each key's legend as `data-label` and whose legend groups draw everything printed for it ("Legends", below). The `keyboard.matrix` lists these files once held were a second, hand-kept copy that had drifted from the fronts (a T-Deck Plus bottom row of four keys for the five the board has, the Cardputer's block colors) and that nothing read; they were removed on 2026-11-12.

## SVG output convention

Each device with a model has `svg/front.svg`, written by `_shared/emit_front_svg.py`, and `svg/back.svg`, written by `_shared/emit_back_svg.py` ("Back drawings", below). The SVG viewBox uses **1 mm = 1 unit** so it can be scaled freely. Each drawing is of one face of the board, seen straight on by someone looking at that face, in that face's frame (`_shared/board_faces.py`).

### Screen contract (`front.svg`)

Every `front.svg` written by `_shared/emit_front_svg.py` exposes its display the same way, so a compositor can drop a firmware screenshot into it:

| Element | Meaning |
| --- | --- |
| `<rect id="screen-active" x y width height data-resolution="WxH"/>` | Exactly one per file. The panel's active pixel area in mm: the datasheet size (`display.active_w_mm` × `active_h_mm`, in the front view's orientation), centered where the vendor's front photo shows the lit pixels. A photo not cropped exactly to the case is registered onto it first: the Core2's (turned 0.4°, framed with a margin) through its glass outline onto the glass, the CoreInk's (front face 1.2 % larger than the case, 0.4 mm off center) through its four hole centers. `data-resolution` is the pixel grid in that orientation (Sticks `135x240`, Cardputer `240x135`, Core2 / CoreS3 SE / T-Deck `320x240`, CoreInk `200x200`). No fill, no stroke: a geometry marker drawn over the bare panel (dark glass on the LCDs, blank paper on the CoreInk). |
| `screen-demo` | None in any file. A vendor's demo screen is the vendor's artwork, so no front draws one; the panel is left bare for a screenshot. |
| `<g id="annotations">` | Exactly one per file, last in the document. Everything the drawing says about itself and nothing the device shows: the two mm dimensions in the margins, the title under it, on the Sticks the two side-key names beside their marks, and on the CoreInk the names of its power key and its top key beside the edge each is in. Removing it leaves the device alone in its margins. The legends printed on the hardware (`M5`, `LILYGO`, `CARDPUTER`, the keycaps) are part of the face and stay. |
| `<g id="hotspots" display="none">` | Exactly one per file, just before the annotations. One `<circle id="hs-<id>" cx cy r data-face data-w data-h [data-label]/>` per physical control, in the same front-view mm as `screen-active`. It draws nothing (`display="none"`): it is where a finger goes. |

### Hotspots (`front.svg`)

A hotspot is a press target, not artwork: it says where a fingertip lands on one control, so an overlay never has to measure the drawing again. The generator emits them from the same constants it draws each control with, which is what keeps the two together — the Sticks are drawn portrait while their case is quoted landscape, so a consumer deriving points from `measurements.json` would have to repeat that turn and would drift from it.

| Attribute | Meaning |
| --- | --- |
| `id` | `hs-` plus the control's id: `hs-BtnA`, `hs-TouchB`, `hs-DialUp`, `hs-Power`, `hs-BtnEXT`, `hs-Trackball`, or `hs-key-<slug>` for a keycap. The slug is the printed legend where that is a word, a letter or a digit, and a name where it is not (`slash`, `comma`, `lbracket`, `backslash`, `quote`, `underscore`, `equal`, `dollar`, `semicolon`, `period`, `rbracket`); the T-Deck's two shift keys are `shift-left` and `shift-right`. |
| `cx`, `cy` | The control's center in front-view mm, the same frame as `screen-active`. A control on another face sits on the mark the front draws for it: on the case edge for the Sticks' two side keys, on the wheel itself for the CoreInk's dial, which shows in a pocket. The CoreInk's power key and top key are flush with their walls and show no mark from the front: each sits on the edge its wall meets, centered on the key. |
| `r` | Half the control's shorter side: the largest fingertip ring that stays on it. |
| `data-face` | `front`, `left`, `right`, `top` or `bottom`: which face carries the control, so an overlay knows to come in from that side. `back` on a back drawing's own target ("Back drawings", below). |
| `data-w`, `data-h` | The control's box in mm. On a side key this is the mark the front draws for it (its depth) by its span along the edge; the CoreInk's two wall keys, which have no mark, take the same depth and the width of their pad. |
| `data-label` | What is printed on the control, when anything is: a keycap's legend, `M5`, `OK`. |

What each front carries:

| Device | Hotspots |
| --- | --- |
| Plus 1.1 / Plus2 / Plus SE / StickS3 | `BtnA` (front: the debossed `M5`, or the StickS3's blue pill), `BtnB` (right edge), `Power` (left edge) |
| Core2 v1.3 / CoreS3 SE | `TouchA` `TouchB` `TouchC` |
| CoreInk | `DialUp` `DialMid` `DialDown` on the wheel, `Power` under its pocket (right edge), `BtnEXT` (top edge); its `Reset` is on its `back.svg` |
| Cardputer ADV | 56 `hs-key-*`, one per button under its legend |
| T-Deck Plus | 35 `hs-key-*` and `Trackball` |

The two touch boards have no printed target to take: their A/B/C zones are bands of the sensor, which reaches 40 rows below the last screen row, and a contact there routes to one of three equal columns of the panel's width (the Kleidos firmware's `zoneForSample`, `src/hal/common/m5_touch_button_input.cpp`; `kTouchZoneTopY`, `src/config/device_config.h`). So the three targets are computed from `screen-active`, in the same mm a screenshot is composited into. On the Core2 that lands within 0.25 mm of the three printed rings, which is the cross-check; on the CoreS3 SE the printed `< < O > >` is decoration, and its two inner chevrons sit across a band boundary.

A reset has no hotspot on a front: it is not an input a flow presses, and it is seldom on a face the front can show. The CoreInk's is a key on its back, which its back drawing draws and carries as a target ("Back drawings", below).

### Legends (`front.svg`)

What a board prints (on its keys, on a sticker, on a plate, on its glass) is drawn inside groups of its own, so the board's 3D model can carry the same print as geometry with nothing typed a second time (`_shared/legend_mesh.py`, the `legends` meshes of `_shared/build_board_glb.py`). A front that prints anything carries the groups; a front that prints nothing has none.

| Element | Meaning |
| --- | --- |
| `<g class="legend" data-key="<slug>">` | One per key, where the paint order puts it. Its children are everything printed on that key, or beside it for that key: the legend, its shifted and fn legends, the arrow behind it. `<slug>` is the slug of the key's hotspot (`hs-key-<slug>`). The cap, the strip and a colored block under a legend stay outside it. A key's group is on the plane `keys`. |
| `<g class="legend" data-mark="<name>" data-plane="<plane>">` | One per print that is no key's: a sticker's marks, a wordmark, the traces printed on a plate. `<name>` is its own (letters and digits joined by hyphens, no two groups of a front alike); `<plane>` names the surface it is printed on, and every group of one plane lies at one height in the model. A plane is also what a reader of the model keeps or leaves out, ink by ink, by how thin its print is (below), so two prints of one ink on one surface that are not as thin as each other go on two planes: the T-Deck Plus's plate is `plate` (its traces, chevrons, rings and wordmark) and `plate-marks` (the discs of its two round marks, which are printed in the traces' ink and are no hairlines). |

A group draws as its children do, so a front renders the same pixels with the wrappers or without them. Inside one, the generator writes only what the model builder can turn into geometry, and the builder refuses anything else rather than drop it: `<text>` (one plain run, with `x`, `y`, `font-size`, `text-anchor`, `font-weight`, a `transform`, and `textLength` only with `lengthAdjust="spacingAndGlyphs"`), `<polygon>`, `<rect>`, `<circle>` (filled, or stroked with `fill="none"`) and `<path>` (`M L H V Q C A Z`; filled, by the even-odd rule with `fill-rule="evenodd"`; or stroked with `fill="none"`, with `stroke-linecap` and `stroke-linejoin`, a miter no longer than SVG's default limit of 4), each in one flat `#rrggbb` color: no opacity, gradient, filter or clip, and no group inside a group.

A model's spec draws each plane with one `legends` mesh, and the builder refuses a model that leaves a plane of its drawing out, so a new group cannot go missing from the model quietly. What each front carries:

| Device | Legend groups | Planes |
| --- | --- | --- |
| Cardputer ADV | 56 keys; `brand-panel` (the CARDPUTER ADV sticker's ten marks); `stamp-label` (everything printed on the StampS3A's label) | `keys` (the legend strips), `panel` (the sticker), `stamp` (the StampS3A's label) |
| T-Deck Plus | 35 keys; `lilygo-glass` (the wordmark over the screen); `band-print` and `bottom-print` (the traces and chevrons beside the trackball, the rings of the two round marks, the wordmark under the keys); `round-marks` (the two round marks' discs, each split by a dark bar); on its back (`back.svg`), `tdeck-frame` (T-DECK in the top frame), `tdeck-frame-line` (the outline round it), `tdeck-badge` (the mascot and the small T-DECK on the trapezoid) and `lilygo-base` (LILYGO® at the bottom end) | `keys` (the caps), `glass`, `plate` (the keyboard plate), `plate-marks` (the same plate: the marks' discs, kept apart from the traces of their ink); `frame`, `frame-line`, `badge` and `base` (the back's one face, a plane a print, so each print keeps its own thinness) |
| The other seven | none: the Sticks' `M5`, the CoreInk's and the Cardputer's debossed `M5` are relief in the vendor's own shell, and the Core2's rings and the CoreS3 SE's `< < O > >` are solids of their models' specs | |

The groups of one plane are one layer: where two of its shapes of different inks overlap, the later cuts the earlier out, as a print is, and the sheets share every edge. Two planes on one surface may lie at one height (the T-Deck Plus's `plate` and `plate-marks` do), and nothing cuts one out of the other, so the drawing never lays an ink of one over an ink of the other: the model builder refuses any two meshes of different materials that cover one place at one depth, a legend's or a solid's (`model_raster.coplanar_overlaps`; `docs/models-and-drawings.md`, "No two materials at one depth"). A print over a solid of the spec lies whole position steps above it, never on its face.

Not in any group of a front, and so not from the front in a model: what a board prints on its back, which its `back.svg` draws ("Back drawings", below), and on its sides, which a drawing of that side draws (`svg/<face>.svg`).

In the model a plane's groups are flat meshes of their own, one an ink, named `<mesh>_<rrggbb>` with `<mesh>` ending in `legends`, so `_legends_<rrggbb>` at the end of a node's name finds them all. A print is geometry and has no smaller version of itself, so a reader that shows the board small leaves those meshes out: when a mesh's `stroke_mm` (in its `extras.legends`) times the pixels a millimeter is under 1 with 4x multisampling, or under 1.5 with no antialiasing, decided once for a shot and never frame by frame. The rule, what else a reader may count on and the tool that writes a model without them (`_shared/glb_legends.py`) are in `docs/models-and-drawings.md`, "Printed legends".

To composite a screenshot, place an `<image>` at the `screen-active` x / y / width / height with `preserveAspectRatio="none"`. The 1.14" glass of the Sticks and the Cardputer has non-square pixels (0.110 × 0.104 mm), so the screenshot fills the rect rather than keeping its pixel aspect.

`emit_front_svg.py` regenerates every front; `emit_front_svg.py <device_id> …` regenerates only the named ones; `--contact-sheet` also rebuilds `fronts-contact-sheet.svg`. It is the only writer of either file, and the `measurements.json` files are maintained by hand against them.

Every drawing opens with its embedded metadata, which `media_meta.stamp_svg` writes as the emitter writes the file: the SPDX comment, `role="img"`, `aria-labelledby` and `lang` on the root, the descriptive `<title>` and `<desc>`, and a Dublin Core and ccREL `<metadata>` block between REUSE's ignore markers (`docs/models-and-drawings.md`, "Embedded metadata"). None of it is drawing: a reader that composites or strips a front leaves it or drops it, and the legend digests do not read it.

### Back drawings (`back.svg`)

What a board prints on its back (a sticker of pin names and marks, a rating label, a wordmark) is drawn in its `svg/back.svg`, seen from behind with the board's top up, so a print reads there as it reads on the hardware. Its frame is the **back frame** (`_shared/board_faces.py`): 1 mm a unit, x across from the case's left edge *as seen from behind* (its right edge as the front is seen), y down from its top edge. Nothing is drawn mirrored: the model builder lays the back's prints on the model's back through that frame.

| Element | Meaning |
| --- | --- |
| `<rect\|path\|polygon id="case-outline">` | Exactly one, the first shape of the drawing: the front's case outline mirrored across the case's width (a silhouette seen along one axis is the same from either end), filled flat with `case.color`. `check_board_model.py` holds the model's back silhouette to it. |
| `<g class="legend" data-mark="<name>" data-plane="<plane>">` | One per print, as on a front ("Legends", above), with the same rules: flat ink, no group inside a group. A back has no keys, so no `data-key`. A plane of the back is named by the back's drawing alone: the front's planes and the back's never meet. |
| `<path id="label-paper">` | Optional, after the outline and before the legend groups: the paper a label is printed on, so the drawing shows its white prints as the hardware does. Not a legend: the model's paper is a solid of its spec, the mesh the prints lie `on`. |
| `<g id="reset-key">` | Only on the CoreInk's back, after the outline and before the legend groups: its reset key as the back shows it (the opening in the shell, the gap round the key's tongue, the pad). Relief of the vendor's shell, not print, so no legend and nothing the model builds from the drawing: the model's shell already holds it. |
| `<g id="hotspots" display="none">` | Only on a back with a control on it, just before the annotations: one `<circle id="hs-<id>" cx cy r data-face="back" data-w data-h/>` a control, as on a front ("Hotspots", above) but in the back frame. The CoreInk's back has one, `hs-Reset`, on the reset key's pad; no other back has the group. |
| `<g id="annotations">` | Exactly one, last: the two mm dimensions and the title, in the margins, and beside a control the back carries its name (the CoreInk's `Reset`). |

No `screen-active`: a back has no screen. A model draws a back plane with a `legends` mesh that names `drawing: ../svg/back.svg` and `face: back`, at a `z` three position steps out from the face under it (`docs/models-and-drawings.md`, "Prints on other faces"). A back with nothing in `emit_back_svg.BACK_PRINTS` draws its outline alone: the frame its prints will be drawn in. The Core2 v1.3's back prints its sticker: one group, `back-label`, on the plane `sticker`; the StickS3's, `back-label` on the plane `label` (`_shared/sticks3_back.py`). The T-Deck Plus's back prints four groups, `tdeck-frame`, `tdeck-frame-line`, `tdeck-badge` and `lilygo-base`, a plane each (`back_tdeck_plus.py`). The Cardputer ADV's prints its whole sticker: forty-three groups on the plane `label` (`_shared/cardputer_faces.py`). The Plus SE's prints its whole label: twenty-two groups on the plane `label` (`_shared/back_plus_se.py`). The M5StickC Plus 1.1's draws its label: one group, `back-label`, on the plane `label` (`_shared/back_m5stickc_plus1.py`). The CoreInk's prints its sticker, one group, `back-label`, on the plane `label`, and draws its reset key beside it (`_shared/coreink_back.py`).

The other faces have frames too (`top`, `bottom`, `left`, `right`, each a viewer's left-to-right and top-down, `_shared/board_faces.py`), and a model lays a drawing of any of them the same way, placed by its spec's `face_frames`. `emit_back_svg.py` writes them to `svg/<face>.svg` from its `FACE_PRINTS`, to the back's contract (the case outline first, here the face's rectangle; the legend groups; the annotations last). The Core2 v1.3's `svg/top.svg` prints its rating label: `rating-label`, on the plane `rating`; the StickS3's `svg/left.svg` its STICK S3 strip: `stick-s3`, on the plane `strip`. In a top drawing the front lies at the bottom, so a print its user reads from the keyboard side reads upside down there; in a left drawing the front lies on the right, so a line of the side's print reads down. The Cardputer ADV's `svg/top.svg` prints the sticker along its top edge (plane `strip`) and its `svg/left.svg` the one round its Grove port (plane `side`). The CoreS3 SE's `svg/top.svg` prints two: `rating-label` on the plane `rating` and `port-tag` (its battery base's tag) on the plane `port-tag`.
