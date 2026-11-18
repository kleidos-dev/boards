# M5Stack Core2 v1.3 — sources

What `measurements.json` and `svg/front.svg` were measured on. The vendor files themselves are not kept here: product photos, drawings and CAD files stay the property of their owners and are cited by address only (`NOTICE.md`). The numbers taken from them are in `measurements.json` and in the Core2 block of `_shared/emit_front_svg.py`, whose comments say which figure came from which view.

| Source | Address | Used for |
| --- | --- | --- |
| M5Stack's K010-V13 dimension drawing, the model-size image of the Core2 v1.3 page | <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1231/K010-V13_Core2_v1.3_model-size_page_01.png> | The case outline's R5 corners, concentric with the glass corners around the 1.5 mm frame |
| M5Stack's Core2 v1.3 documentation page | <https://docs.m5stack.com/en/core/Core2_v1.3> | Product size 54 x 54 x 16.5 mm, the case depth and material (`board.json`) |
| M5Stack's straight-on front photo of the Core2 v1.3 (black glass, framed with a margin) | not recorded | Every value on the glass: the window in the glass print (6.71, 11.72, 40.86 x 30.6 mm), the three touch rings (2.08 mm across, 0.19 mm line), the glass's R3.6 corners; registered through its glass outline onto the 51 x 51 mm glass |
| A front product photo of the same shot, the white frame's outer edge showing as a faint shadow line | not recorded | The frame round the glass, 1.47 to 1.52 mm, drawn an even 1.5 mm; the glass values above land within 0.15 mm of it |
| M5Stack's Core2 v1.3 model, `Core2_v1.3.stl` (M5_Hardware at `dccc8047`, SHA-256 `223b148fc19892a77d84aaaa6940c9fce1667d393259bd75316d3b6f85052424`) | <https://raw.githubusercontent.com/m5stack/M5_Hardware/dccc804775037bb1c1457b7d31bf3ba583150d57/Products/K010-V13_Core2_v1.3/Structures/Core2_v1.3.stl> | The microSD slit in the bottom wall (12.56 x 1.73 mm, 14.12 to 26.68 mm from the left edge, 7.09 to 8.81 mm behind the front), checked against a photo of that face; the 3D model (`model/spec.json`) |
| The owner's own Core2 v1.3 | — | The Power key on the left edge and Reset on the bottom edge, measured on 2026-07-15; neither shows from the front |

The panel's active area, 40.80 x 30.60 mm, is the display datasheet's (`board.json`); its origin is the window's centre, photo-measured on 2026-10-18.

Not established: the addresses of the two front photos and of the photo of the bottom face were not recorded when they were measured. The images M5Stack's Core2 v1.3 page shows now (<https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1231/K010-V13-Core2-v1.3-main-pictures_01.webp> and the following ones) are not byte-identical to the copies that were measured on, so which of M5Stack's images they were cannot be said.

Checked against the owner's physical unit on 2026-11-18: the model and the drawing match the real board. The original source of the measurement was not recorded.
