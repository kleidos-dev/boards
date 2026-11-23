<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# M5Stack Cardputer ADV — sources

What `measurements.json` and `svg/front.svg` were measured on. The vendor files themselves are not kept here: product photos, drawings and CAD files stay the property of M5Stack and are cited by address only (`NOTICE.md`). The numbers taken from them are in `measurements.json` and in the Cardputer block of `_shared/emit_front_svg.py`, whose comments say which figure came from which view.

| Source | Address | Used for |
| --- | --- | --- |
| M5Stack's Cardputer-Adv dimension drawing, `K132-Adv-cardputer-ADV.pdf` (SHA-256 `6c937ca05e0894e54a3e47abb57e91de1b755dea032fd3f7438ea7a3e34550da`; read at the Internet Archive, <https://web.archive.org/web/20261030120518id_/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1178/K132-Adv-cardputer-ADV.pdf>, when M5Stack's host timed out; the address answered with the same file on 2026-11-18) | <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1178/K132-Adv-cardputer-ADV.pdf> | The size, 84 x 54 x 19.6 mm (`board.json` `model-size`) |
| Its page image, `K132-Adv-cardputer-ADV_page_01.png` (SHA-256 `0538542459779f6171cac09068e44c663c2a734976024731f275bd5b06b52d1d`; read at <https://web.archive.org/web/20261030141519id_/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1178/K132-Adv-cardputer-ADV_page_01.png>) | <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1178/K132-Adv-cardputer-ADV_page_01.png> | The same drawing, as an image |
| M5Stack's Cardputer-Adv documentation page | <https://docs.m5stack.com/en/core/Cardputer-Adv> | Product size and weight, the case material (`board.json` `m5-docs`) |
| M5Stack's straight-on front product photo of the Cardputer ADV | not recorded | The face: the glass's black window (the active area, x 20.75 to 45.66, y 2.93 to 17.79 mm), the M5 deboss, the CARDPUTER ADV panel, the screws, the ledge and tongue under the LCD, the StampS3A label (10.1 px/mm), the four keyboard rows and the 56 keys, the legend blocks' colors |
| The operation photo of M5Stack's product page, `Cardputer-Adv_operation_01.jpg` (SHA-256 `ed9a13a154edf0a7f26dd18226ebbc58d979f70526564175f7a2719e3ef1ba27`) | <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1178/Cardputer-Adv_operation_01.jpg> | Kept beside the drawing as a reference of the same kit |
| The Pin Sticker of M5Stack's Cardputer Accessory Kit v1.1, three shop images | <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/9_e979ae23-d47f-4037-9da6-5c3bc25e0362.webp>, <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/4_b49dc0d0-3bbd-4373-9424-594e06052cd0.webp>, <https://cdn.shopify.com/s/files/1/0056/7689/2250/files/1_1e50f491-80e1-4e4f-a47d-d1bd3f805838.webp> | A check of the StampS3A label's print and inks |
| M5Stack's Cardputer-Adv model, `Cardputer-Adv.stl` (M5_Hardware at `d99c537a`, SHA-256 `50c2b2a72694dd7461125489d99a2f863630bb0c224f86f98f95dda15ae45c00`) | <https://raw.githubusercontent.com/m5stack/M5_Hardware/d99c537a05aebb07eb4d28d6e3c3ac8d35b8b271/Products/K132-Adv_Cardputer-Adv/Structures/Cardputer-Adv.stl> | The 3D model (`model/spec.json`) |

The panel's active area, 24.91 x 14.86 mm, is the display datasheet's (`board.json`). The digests of the drawing, its page image and the operation photo are those of the copies that were read.

Not established: the address of the straight-on front product photo, and of the 1600 px three-quarter photo the StampS3A label was checked on, were not recorded when they were measured.

Checked against the owner's physical unit on 2026-11-18: the model and the drawing match the real board. The original source of the measurement was not recorded.
