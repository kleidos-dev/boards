<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# M5StickC Plus 1.1 — sources

What `measurements.json` and `svg/front.svg` were measured on. The vendor files themselves are not kept here: product photos, drawings and CAD files stay the property of their owners and are cited by address only (`NOTICE.md`). The numbers taken from them are in `measurements.json` and in the Plus block of `_shared/emit_front_svg.py`, whose comments say which figure came from which view.

| Source | Address | Used for |
| --- | --- | --- |
| M5Stack's dimension drawing of the M5StickC Plus (its docs page's dimension image) | <https://static-cdn.m5stack.com/resource/docs/products/core/m5stickc_plus/%E5%B0%BA%E5%AF%B8%E5%9B%BE.jpg> | The case outline (24 x 48 mm, R3), the window, the active rectangle (14.8 x 24.86 mm), the BtnA flex slot and the debossed "M5", both side keys: front view registered on its 24 x 48 mm outline at 23.58 px/mm, line centers from profiles |
| M5Stack's documentation page | <https://docs.m5stack.com/en/core/StickC-Plus> | Product size 48.0 x 24.0 x 13.5 mm, the case depth and material (`board.json`) |
| Shop photo, straight-on front | <https://cdn.shopify.com/s/files/1/0056/7689/2250/products/6.webp?v=1766826019> | Checks the drawing's features within 0.15 mm; the lit area's place (3.39 to 3.46 mm at the top); the face and wall colors |
| M5Stack's dimension drawing of the M5StickC Plus SE (`K016-P-SE`, `model-size_page_01`) | <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1234/K016-P-SE-model-size_page_01.png> | The same mold: its active rectangle agrees with this drawing's within 0.02 mm, which set the screen's top (`PLUS_SCREEN_Y`) for the three Plus-chassis boards |
| M5Stack's StickC-Plus model, `StickC-Plus.stl` (M5_Hardware at `48baa75a`, SHA-256 `56dcfd382032d177ea049f890f59db965a56c161a8db588e80dd45e66576685a`) | <https://raw.githubusercontent.com/m5stack/M5_Hardware/48baa75a9476f4070dd5f107c1c28e2c9f383a96/Products/K016-P_StickC-Plus/Structures/StickC-Plus.stl> | The 3D model's case (`model/spec.json`) |

The shop photo is identified by the view the generator's notes describe. The panel's active area, 14.86 x 24.91 mm, is the display datasheet's (`board.json`).

The Plus2 and the Plus SE share this chassis: `m5stickc-plus2/sources.md` and `m5stickc-plus-se/sources.md` list what their own fronts add.

Not established: the notes say the lit-area check used two Plus 1.1 shop images, and name only the view; the second of the two is not recorded. M5Stack's documentation page shows a straight-on picture of the same kind (<https://static-cdn.m5stack.com/resource/docs/products/core/m5stickc_plus/m5stickc_plus_05.webp>), so it may be that one.

Checked against the owner's physical unit on 2026-11-18: the model and the drawing match the real board. The original source of the measurement was not recorded.
