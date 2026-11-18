# LILYGO T-Deck Plus — sources

What `measurements.json` and `svg/front.svg` were measured on, and what the model's case figures were read off. The vendor files themselves are not kept here: product photos, drawings and CAD files stay the property of LILYGO and are cited by address only (`NOTICE.md`). The numbers taken from them are in `measurements.json`, in the T-Deck Plus block of `_shared/emit_front_svg.py` and in the docstring of `_shared/tdeck_plus_case.py`, which say which figure came from which view.

| Source | Address | Used for |
| --- | --- | --- |
| LILYGO's T-Deck Plus shell model, `T-Deck-Plus-Shell.stp` | <https://github.com/Xinyuan-LilyGO/T-Deck/blob/master/shell/T-Deck-Plus-Shell.stp> | The case: 73.14 x 114.98 x 20.40 mm, the outline (R12.2 top corners, the bottom edge one curve) and the side rails 0.1 mm proud (`board.json` `shell-step-measured`); the front's outline is drawn from it. The model is not built from it |
| LILYGO's T-Deck Plus PINMAP image, 3000 px (SHA-256 `a92a4c2a04825e73f4f77c8a23ae04a1680edab36660629f700eeee78656355b`) | <https://raw.githubusercontent.com/Xinyuan-LilyGO/documentation/master/public/products/t-deck-series/t-deck-plus/index/image/t-deck-plus-en.jpg> | The face: display window, glass and bevel, trackball and chevrons, the LILYGO print, the slot above the screen, the keyboard plate and keycaps, registered onto the STEP outline through a homography on the silhouette (0.08 mm rms); for the model, the straight-on back (registered on the back drawing's printed T-DECK and LILYGO at 15.9 px/mm) |
| LILYGO's shop front photo of the T-Deck Plus | not recorded | The same face features; it agrees with the PINMAP image within 0.05 mm |
| LILYGO's T-Deck Plus Specifications image (SHA-256 `61ed205e7eaacc57c0171f9f9e2cb8777329a91cc2b8336cf7f4e2c8b951adfb`) | <https://raw.githubusercontent.com/Xinyuan-LilyGO/documentation/master/public/products/t-deck-series/t-deck-plus/index/image/t-deck-info-en.jpg> | For the model, its four side views (about 15 px/mm): the back's slope, the seam round the sides, the side rails' depth, the microSD slot, the top end's knock-outs, the bottom holes' places |
| LILYGO's T-Deck Plus documentation page | <https://wiki.lilygo.cc/products/t-deck-series/t-deck-plus/> | The parts and their names; nothing there labels the slot above the screen (`board.json` `lilygo-wiki`) |
| The owner's own T-Deck Plus | — | The visible glass, 58 x 43 to 44 mm (2026-07-15); six holes on the lower edge and the speaker behind the PCB at the bottom-right corner (2026-11-17) |

The panel's active area, 57.60 x 43.20 mm, is the display datasheet's (`board.json`). The digests are those of the copies that were measured on, byte-identical to the files at those addresses on 2026-11-17.

Not established: the address of the shop front photo was not recorded when it was measured. The STEP file's digest was not recorded either, nor which commit of LILYGO's repository it was read at. The status table of `docs/models-and-drawings.md` also names LILYGO's PCB model (`shell/T-Deck-PCB-3D.stp`) and outline drawing (`shell/T-Deck.dxf`) of the same repository; no figure in `measurements.json` is traced to either. Edge-button and microphone positions are approximate, as `measurements.json` says.

Checked against the owner's physical unit on 2026-11-18: the model and the drawing match the real board. The original source of the measurement was not recorded.
