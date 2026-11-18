# M5StickS3 — sources

What `measurements.json` and `svg/front.svg` were measured on. The vendor files themselves are not kept here: product photos, drawings and CAD files stay the property of M5Stack and are cited by address only (`NOTICE.md`). The numbers taken from them are in `measurements.json` and in the StickS3 block of `_shared/emit_front_svg.py`, whose comments say which figure came from which view.

| Source | Address | Used for |
| --- | --- | --- |
| M5Stack's StickS3 documentation page | <https://docs.m5stack.com/en/core/StickS3> | Product size 48.0 x 24.0 x 15.0 mm, the case depth and material (`board.json` `m5-docs`) |
| Shop photo, straight-on front with the lit "STICK S3" boot screen | <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/8_6cc19914-4f8e-4b79-8bff-9d5d62110aa9.webp?v=1770176878> | Window opening, visible glass, BtnA pill, the flat face below it, the face and wall colours; the screen's origin (its lit boot screen) |
| Shop photo, straight-on front with the screen off (the lower-left view of the composite) | <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/1920x2260_1c598967-82f0-449a-98d1-399e85dc56ed.webp?v=1770111242> | The same face features, checked against the lit photo (both agree within 0.05 mm) |
| Shop photo, straight view of the right side | <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/11_3ca2bce7-c796-4712-8cda-6e150b79c0fd.webp?v=1770176878> | KEY2 (BtnB) cap, 19.64 to 28.22 mm along the case |
| Shop photos, two angled front views | <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/1_f50b328d-f753-4bef-92ec-6f0e8a69e5c0.webp?v=1769049123>, <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/4_e5191b04-4dbf-4212-af94-1de732541a92.webp?v=1770176878> | The power key on the left side near the USB end, 39.5 to 44.5 mm, about 0.5 mm uncertain |
| M5Stack's K150 dimension drawing | not recorded | Cross-check of the corner radius: the drawing gives R3, the photos 3.1, the front draws R3.2 |
| M5Stack's StickS3 model, `StickS3.stl` (M5_Hardware at `48baa75a`, SHA-256 `cadfa88716cb74a85d0d76dc866d83dbd627d6f5c310b528d43e588dab37ecec`) | <https://raw.githubusercontent.com/m5stack/M5_Hardware/48baa75a9476f4070dd5f107c1c28e2c9f383a96/Products/K150_StickS3/Structures/StickS3.stl> | The 3D model's case (`model/spec.json`); the front is not measured on it |

The photos are named here by the view the generator's comments describe; which of M5Stack's shop images each one is was read off the shop listing, by that view. The panel's active area, 14.86 x 24.91 mm, is the display datasheet's (`board.json`).

Not established: the address of the K150 dimension drawing was not recorded when its corner radius was read, and no copy of it was kept to recover it from.

Checked against the owner's physical unit on 2026-11-18: the model and the drawing match the real board. The original source of the measurement was not recorded.
