# M5StickC Plus2 — sources

What `measurements.json` and `svg/front.svg` were measured on. The vendor files themselves are not kept here: product photos, drawings and CAD files stay the property of their owners and are cited by address only (`NOTICE.md`). The numbers taken from them are in `measurements.json` and in the Plus block of `_shared/emit_front_svg.py`, whose comments say which figure came from which view.

The Plus2 is the Plus 1.1's chassis with a different interior, and M5Stack publishes no drawing or model of its own for it: its geometry is the Plus 1.1's (`m5stickc-plus1/sources.md`), checked on photos of the Plus2.

| Source | Address | Used for |
| --- | --- | --- |
| M5Stack's dimension drawing of the M5StickC Plus (also linked from the Plus2's page) | <https://static-cdn.m5stack.com/resource/docs/products/core/m5stickc_plus/%E5%B0%BA%E5%AF%B8%E5%9B%BE.jpg> | The case outline (24 x 48 mm, R3), the window, the active rectangle, the BtnA slot and "M5", both side keys |
| M5Stack's Plus2 documentation page | <https://docs.m5stack.com/en/core/StickC-Plus2> | Product size 48.0 x 24.0 x 13.5 mm, the case depth and material (`board.json`) |
| Shop photo, straight-on front | <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/6_52d0fe45-7cc0-4d6a-b6d1-fd243c9426fb.webp?v=1766829643> | Confirms the drawing's features on a Plus2 within 0.15 mm; the lit area's place; the case colours (#feb722 to #fbb31f) |
| Adafruit's photo of a Plus2, straight-on front with the screen off | <https://cdn-shop.adafruit.com/original/4289-13.jpg> | The same check on a real unit with a dark screen |
| M5Stack's StickC-Plus model, `StickC-Plus.stl` (M5_Hardware at `48baa75a`, SHA-256 `56dcfd382032d177ea049f890f59db965a56c161a8db588e80dd45e66576685a`) | <https://raw.githubusercontent.com/m5stack/M5_Hardware/48baa75a9476f4070dd5f107c1c28e2c9f383a96/Products/K016-P_StickC-Plus/Structures/StickC-Plus.stl> | The 3D model's case (`model/spec.json`): the Plus 1.1's file, since the chassis is one |

The photos are identified by the views the generator's notes describe. The panel's active area, 14.86 x 24.91 mm, is the display datasheet's (`board.json`).

Not established: the notes say the lit-area check used two Plus2 shop images, and name only the view; the second of the two is not recorded. M5Stack's documentation page shows the same straight-on picture as the shop photo above (<https://static-cdn.m5stack.com/resource/docs/products/core/M5StickC%20PLUS2/6.webp>), so it may be that one.

Checked against the owner's physical unit on 2026-11-18: the model and the drawing match the real board. The original source of the measurement was not recorded.
