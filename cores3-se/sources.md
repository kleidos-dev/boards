<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# M5Stack CoreS3 SE — sources

What `measurements.json` and `svg/front.svg` were measured on. The vendor files themselves are not kept here: renders, drawings and CAD files stay the property of M5Stack and are cited by address only (`NOTICE.md`). The numbers taken from them are in `measurements.json` and in the Core shell and CoreS3 SE blocks of `_shared/emit_front_svg.py`, whose comments say which figure came from which view.

| Source | Address | Used for |
| --- | --- | --- |
| M5Stack's dimension drawing of the CoreS3 Lite, which the CoreS3 SE page links as its model size (Internet Archive copy) | <https://web.archive.org/web/20251018174855/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1162/cores3-lite.pdf> | The glass outline, the window and the panel in the shell's pocket (the pocket line 1.473 mm in, R3.53); the screen's origin, the active area centered in the window; the frame's 15.5 mm and 16.5 mm over the back cover (`board.json` `m5-size-drawing`) |
| M5Stack's CoreS3 SE documentation page | <https://docs.m5stack.com/en/core/CoreS3%20SE> | Product size 54.0 x 54.0 x 15.5 mm, the case depth (`board.json`) |
| M5Stack's CoreS3 SE model, `CoreS3-SE.stl` (M5_Hardware at `dccc8047`, SHA-256 `529349b80662f2bb83e87a3d59075d91ab54aa3e2d5356d72d69fded36767354`) | <https://raw.githubusercontent.com/m5stack/M5_Hardware/dccc804775037bb1c1457b7d31bf3ba583150d57/Products/K128-SE_CoreS3-SE/Structures/CoreS3-SE.stl> | The shell's face cut through: a 54.0 mm square, R5.0 corners, the face rounding off over its outer 1.0 mm, the pocket 1.474 mm in; the 3D model (`model/spec.json`) |
| M5Stack's Basic v2.7 middle frame, `Basic_v2.7_Middle_Frame.stl` in M5_Hardware | <https://github.com/m5stack/M5_Hardware> | The same shell's face, a cross-check (pocket 1.465 mm in) |
| Shop render, straight-on front | <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/9_b22bfa22-bb33-4e1a-af3b-99ede0aaacc3.webp?v=1765959078> | The red touch print under the window (the ring 2.58 mm across at 27.0, 46.40 mm, the chevrons), the two microphone holes 13.93 mm either side, the boot logo, the glare, the frame and badge colors; registered onto case millimeters through its glass outline |
| Shop renders, three-quarter views (the listing's first and third images) | <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/1_88c07c01-8c0b-449e-9d33-d9f31b3a3102.webp?v=1716532208>, <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/4_9974ef04-4ebe-43a4-97db-0b17c1d6053b.webp?v=1765959078> | The print's layout and height and the logo, checked against the front render (they place the print 0.8 mm further right; the front follows the front render) |
| The owner's own CoreS3 SE | — | The Power key on the left edge and Reset on the bottom edge, measured on 2026-07-15; neither shows from the front |
| Kleidos firmware, `variants/cores3_se/variant.h`: `TOUCH_ZONE_STRIP_BELOW_DISPLAY`; `src/hal/input/touch_zone_buttons.cpp`: `zoneForSample` | the Kleidos firmware repository | The three touch zones under the active area (40 rows below the 240-row display, three equal columns), with the owner's raw-Y reading |

The renders are identified by the views the generator's notes describe. The panel's active area, 40.80 x 30.60 mm, is the display datasheet's (`board.json`).

Not established: the commit and digest of the Basic v2.7 middle frame that was cut through were not recorded; it was read only to cross-check the CoreS3 SE's own file.

Checked against the owner's physical unit on 2026-11-18: the model and the drawing match the real board. The original source of the measurement was not recorded.
