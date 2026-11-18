# LILYGO T-Deck Plus: schematic

Kleidos boards: the T-Deck Plus's connectivity in KiCad, documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1 (sources below and in `netlist.yaml`): every part, pin and net of the mainboard and of the two GPS daughterboards LilyGO publishes, with the values the vendor documents, laid out with this project's own layout and symbols. It tells what connects where and how: pull-ups and pull-downs with their values, series parts, the filter and decoupling parts on each interface, every rail and what feeds it, and the ESP32-S3 and ESP32-C3 GPIO of every signal. Where the vendor's print leaves a detail out or gets one wrong and a primary source settles it, the drawing adds or corrects it, marked in amber by its id (K1 to K20) and listed on page 1 and below; what is still uncertain stays out and is listed under "Open questions".

[`tdeck-plus.pdf`](tdeck-plus.pdf) has the nine pages, made to be read on a screen and followed by clicking (below); the export also writes one SVG per page into `svg/`, which git does not keep. Both are drawn in the Kleidos dark theme ([`_shared/kicad-theme-kleidos-dark.json`](../../_shared/kicad-theme-kleidos-dark.json)): graphite ground, parts in light grey, connections in cyan.

| Page | Sheet | What is on it |
| --- | --- | --- |
| 1 | Contents | One box per page with what is on it and its main parts, how to read the drawing, the notes (values, DNP, numbering, zones), the Kleidos additions and corrections and the revision history |
| 2 | Power input, charging and rails | USB-C, the TP4065B charger and the battery, the power path (D1, Q5) and the power switch SW1, the SY8089AAC buck (VDD3V3), the V3V and BAT switches PWR_EN controls, the battery divider |
| 3 | ESP32-S3, TF card, trackball and LoRa | The ESP32-S3-WROOM-1 with reset and the trackball key on IO0, the four-pin header P8, the TF card, the four Hall sensors of the trackball, the HPD16A LoRa module and its antenna |
| 4 | Keyboard controller, display and touch | The ESP32-C3 that scans the keyboard, its flash, crystal and UART header J1; the keyboard connector JP1 and its backlight switch Q3; the LCD connector P2 and the AW9364 backlight driver; the touch connector P4 |
| 5 | Microphones, audio ADC and speaker | The four MEMS microphones and the ES7210, the BSS123 I2C level shifter, the MAX98357A amplifier with its filter and the speaker connector |
| 6 | GPS daughterboards | The MIA-M10Q board (T-Deck-GPS V1.0, parts +100) and the L76K board (T-Deck-L76K V1.0, parts +200) |
| 7 | Power tree and rails | How power flows from the USB-C input and the battery to every rail, with each part's enable; then every rail's nominal voltage, source, enable and where it is drawn |
| 8 | Nets and signals | Every rail and every net drawn on more than one page with the page/zone of its labels; the ESP32-S3 and ESP32-C3 GPIO maps, the I2C addresses, every pull-up and pull-down |
| 9 | Parts | Every part: its value as printed, what it is, its nets (two-pin parts), whether it is fitted, and where it is drawn |

Pages 7 to 9 are written by the generator from `netlist.yaml`, not drawn by hand: they cannot disagree with the drawing.

## What it is not

- Not the vendor's design files. The layout, the blocks and every symbol are this project's: the integrated circuits' and connectors' are each board's own (`tdeck-plus.kicad_sym`), and the passive parts, the diodes, the transistors, the switches, the plain connectors, the pads and the ground symbols are this project's generic ones (`kleidos.kicad_sym`, drawn by `_shared/kicad_schematic.py`). No symbol of KiCad's libraries is in these files. No vendor document is in this repository; the sources are cited below.
- Not a PCB design: no footprints, no part numbers beyond the ones the vendor prints, nothing about placement or routing.
- Not a full datasheet of each part: pin names and values are as the vendor documents them (`100K%1`, `1uF/6.3V`, `NC` for a part not fitted), but where a correction (K9, K10, K17) names a pin after the chip's datasheet.

## How to read it

Pins connect by net labels, not by wires. Two pins whose labels carry the same name are on one net, on any page. After a label, each `[3/C4]` names another page that carries the net and the zone of its label there (the border prints columns 1-8 and rows A-F, 50 mm apart): page 3, row C, column 4. Clicking it lands on that label, zoomed in; on a page where the net has several labels, it lands on the one at the part that feeds the rail (`rails.from` in `netlist.yaml`), or else on the first in reading order. A label with none is on its page only. Neighbouring pins of one part on one net share a short bar and one label. A cross on a pin end means the pin is unconnected. Wires and pin lines are one colour and one width, so a connection reads as one line from the part to its label.

Parts documented as not fitted (value `NC`, `NC(100K)`) carry KiCad's DNP mark: a red cross over the symbol.

An amber `K<n>` beside a label, a reference, a not-connected cross or a table row is a Kleidos addition or correction: it leads to its row on page 1, and the row's id leads back. No connection is added, so no wire on this board is dotted.

In the PDF, each box on the contents page opens its page, and every page carries "Contents" and a row of page numbers above the title block. Each part's reference on the drawing is a link to its row in the parts list, and the row's reference and page/zone lead back to the part. Every place in the index pages (a page/zone, a box of the power tree, a reference in a table) is a link to it. The bookmarks list the pages and, under each, its parts or its tables, each at its place. `_shared/check_schematic_links.py` holds every one of those links (`--list` prints them all).

### In any PDF reader

The PDF holds no script: the property pop-ups KiCad can add only open in Acrobat, so the export leaves them out, and the parts list carries what they showed. The rest is plain PDF that every reader follows:

- a link leads to a page and a position: `/XYZ`, the target placed 30 mm from the window's left edge and 20 mm below its top, at zoom 2. KiCad links a text only to a whole page, so `_shared/schematic_pdf.py` sends each link to its place after the export, from the targets the generator writes into `links.json`;
- each link carries a `/Contents` saying where it leads, for screen readers;
- named destinations open the PDF at a part or at a net's label on a page: `tdeck-plus.pdf#nameddest=part-U1`, `tdeck-plus.pdf#nameddest=net-V3V-p3`.

A reader that ignores the position of a destination still opens the right page, and the printed page/zone says where to look.

Numbering, where it differs from the vendor's documents:

- The two GPS daughterboards reuse designators the mainboard already has, so their parts are +100 (MIA-M10Q board: its U1 is U101, J2 is J102) and +200 (L76K board: its U1 is U201).
- Their nets carry the prefixes `M10_` and `L76K_`. The vendor names them as the mainboard names some of its own (VDD3V3, GND, PPS, GPS_TX...), but publishes no cable between a daughterboard's 5-pin connector J2 and the mainboard's 4-pin header P8, so none of them is joined to the mainboard here. `netlist.yaml` says so under `aliases`. What P8 carries to the GPS board is known by function, and is marked on the mainboard's side: K3 (VDD3V3), K7 (UAR0_TX) and K8 (UAR0_RX).
- Nets the vendor left unnamed have names of ours (`U8_FB`, `PWR_GATE`, `SW1_IN`, `SPK_P`...); `netlist.yaml` lists each under `renamed` with the pins it joins.
- `ESP_LCD_D/C` is written `ESP_LCD_DC` (KiCad reads a `/` in a net name as a sheet path).
- The print's `D2(NC)` and `R3Y(NC)` are D2 and R3Y here, with the values `NC(1N4148)` and `NC(100K)` that mark them as not fitted.
- Pin numbers of the two-pin parts of the GPS sheets are not printed; 1 and 2 are ours (on the diodes, 1 is the cathode).

## Sources

LilyGO publishes the T-Deck schematics in its T-Deck repository on GitHub, and its T-Deck Plus documentation page links the mainboard sheet. They were read on 2026-11-17:

| Document | Address | Version | SHA-256 | Its facts are on |
| --- | --- | --- | --- | --- |
| T-Deck mainboard schematic (Altium, one sheet) | <https://github.com/Xinyuan-LilyGO/T-Deck/blob/master/schematic/schematic.pdf> | title block dated 2023-06-01; commit 80921c8, unchanged since | `c3dcd1de8cc7966c69c5bff182deb41c776ee36d4c3a1e32afbc2a5164269ff4` | pages 2 to 5 |
| T-Deck-GPS V1.0 (MIA-M10Q daughterboard) | <https://github.com/Xinyuan-LilyGO/T-Deck/blob/master/schematic/T-Deck-GPS%20V1.0%20%2024-03-29.pdf> | V1.0, 24-03-29; commit ba38554 | `94ba05c69f9fc28634a4dbe56d1bf22c6e0380800ceb0620af8d3448d61add18` | page 6 |
| T-Deck-L76K V1.0 (L76K daughterboard) | <https://github.com/Xinyuan-LilyGO/T-Deck/blob/master/schematic/T-Deck-L76K%20V1.0%20%2024-08-12.pdf> | V1.0, 24-08-12; commit ba38554 | `f3fdca3c64ccd8edfd9e29e2cf875e24b592e8407db1100c5f38fa811a81ecc2` | page 6 |
| T-Deck Plus documentation (source of wiki.lilygo.cc) and its specifications image | <https://github.com/Xinyuan-LilyGO/documentation/blob/master/en/products/t-deck-series/t-deck-plus/index.md> | read 2026-11-17 | | links the mainboard sheet; K1, K6; with the firmware, K3 (the Grove pins go to the GPS) and K11 |

The mainboard's connections were taken from the PDF itself, which carries its drawing as vectors: its wires and junction dots, the pin and net markers Altium writes into the page for its search pop-ups (`PI<part>0<pin>` over each pin, `NL<net>` once per net), the printed net labels and power ports. Each block was then checked against the printed page, at 600 dpi, part by part. The values come from the print and from the parts' property pop-ups in the same PDF; where the two differ, the print wins and `netlist.yaml` notes it (Q3, R19, JP1). The two GPS sheets are printed from Windows and carry no such markers: their connections were read off the page. The I2C addresses are additions K18 to K20.

The Kleidos additions and corrections rest on these sources besides LilyGO's, read on 2026-11-17 (none is kept in this repository):

| Source | Address or place | Version | Used for |
| --- | --- | --- | --- |
| ESP32-S3-WROOM-1 & WROOM-1U datasheet (Espressif) | <https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf> | v1.8 | K4: Table 1-1, p. 3 |
| ESP32-S3 Series datasheet (Espressif) | <https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf> | v2.2 | K5: Table 3-1 p. 32, Table 3-4 p. 34 |
| ESP32-C3 Series datasheet (Espressif) | <https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf> | v2.5 | K9, K10: Table 2-1 p. 16, Table 2-6 p. 21 |
| ES7210 datasheet (Everest Semiconductor), as Waveshare hosts it | <https://files.waveshare.com/wiki/common/ES7210_DS.pdf> | revision 21.0, January 2023 | K13, K14: pin description p. 4; K18: chip address p. 6 |
| MAX98357A/MAX98357B datasheet (Maxim Integrated), as Adafruit hosts it | <https://cdn-shop.adafruit.com/product-files/3006/MAX98357A-MAX98357B.pdf> | 19-6779 Rev 7 | K15: SD_MODE trip points B0-B2 and RPD (Electrical Characteristics), Table 5; K16: gain AV; K17: Pin Description |
| TP4065 datasheet (Nanjing Top Power ASIC, Chinese), as a forum attachment | <https://hobbielektronika.hu/forum/getfile.php?id=342341> | Rev 1.2 | K2: pin 1 CHRG p. 4, the charge status indicator p. 9 |
| GT911 datasheet (Goodix), as Waveshare hosts it | <https://files.waveshare.com/wiki/common/GT911_Datasheet.pdf> | Rev.10 | K20: the address latched from INT at power-up |
| The Kleidos firmware, run on the owner's T-Deck Plus | Kleidos firmware repository (2026-11-17) | `tdeck_debug` | K3, K4, K7, K8, K11, K12, K19, K20, K21 to K24 (path and symbol below) |
| Bench records | [`bench/`](bench/) | 2026-11-17 | K5; the TP_EN edge detector and the GPIO46 strap (below) |

## Kleidos additions and corrections

The drawing improves on the vendor's print rather than following it to the letter: a detail the print does not show is added when a primary source makes it certain, and a drawing error of the print is corrected when the evidence settles it. Each is an entry of `kleidos` in `netlist.yaml`, marked on the drawing in amber by its id and listed on page 1. There are 24: 21 additions and 3 corrections. None adds a connection: the GPS cable is known by function only, so the GPS board's nets stay apart and the facts are marked on the mainboard's side. The sources in full (firmware paths are in the Kleidos repository; `improvements.md` holds the triage, T01 to T35):

| Id | Kind | What the drawing adds or corrects | Where it is marked | Source |
| --- | --- | --- | --- | --- |
| K1 | addition | VBAT is a 2000 mAh lithium-polymer cell, plugged into P3 (make and part number unpublished). | power tree page, rails table, VBAT | LilyGO's T-Deck Plus documentation page and its specifications image (`board.json` `battery`) |
| K2 | addition | LED1 hangs on UP1's CHRG, an open-drain output low only while the cell charges: LED1 lights while charging and blinks with no cell connected. | after every UP1_CHRG label | TP4065 datasheet Rev 1.2, p. 4 (pin 1 CHRG) and p. 9 (charge status indicator) |
| K3 | addition | VDD3V3 also feeds the GPS board, through P8 pin 2: the receiver is on the always-on rail. | power tree page, rails table, VDD3V3 | The firmware runs the receiver over IO43 and IO44 (`variants/tdeck/variant.h` (`PIN_GPS_TX`, `PIN_GPS_RX`, `GPS_BAUD_RATE`), the verified GPS park in `docs/research/peripheral-parking.md` section 11), whose only other ends are P8 pins 3 and 4 (print); LilyGO's documentation page gives the Grove pins (P8) to the GPS module; the GPS board's one connector J102 brings its supply (GPS print), and P8's only supply pin is VDD3V3 (print) |
| K4 | addition | U1 is the ESP32-S3-WROOM-1-N16R8 (16 MB Quad SPI flash, 8 MB Octal SPI PSRAM); IO35 to IO37 serve its PSRAM. | beside the not-connected cross of U1 pin 28 (IO35) | Firmware run on this board with 16 MB flash and octal PSRAM (`variants/tdeck/tdeck.ini` (`board_upload.flash_size`, `board_build.flash_size`, `board_build.partitions`), `variants/tdeck/sdkconfig.tdeck`); ESP32-S3-WROOM-1 datasheet v1.8, Table 1-1 p. 3 (the one WROOM-1 part number with 16 MB flash and 8 MB Octal PSRAM, beside the print's note "ESP32-S3R8") |
| K5 | addition | GPIO45, the VDD_SPI strap, latched 0 at every power-up and reset tried; 0 selects 3.3 V unless an eFuse forces VDD_SPI. | nets page, ESP32-S3 GPIO table, GPIO45 | Bench [`bench/2026-11-17-gpio46-strap.md`](bench/2026-11-17-gpio46-strap.md), 2026-11-17 (`GPIO_STRAP_REG` `0x0008` in eight cases); ESP32-S3 datasheet v2.2, Table 3-1 p. 32 and Table 3-4 p. 34 |
| K6 | addition | U0 (HPD16A) carries a Semtech SX1262; U0_ANT is its RF port. | after every U0_ANT label | LilyGO's T-Deck Plus documentation page and specifications image |
| K7 | addition | UAR0_TX reaches the GPS board's GPS_RX (J102.3) through P8 pin 3. | after every UAR0_TX label | Firmware: UBX commands sent on IO43 take effect (`variants/tdeck/variant.h` (`PIN_GPS_TX`, `PIN_GPS_RX`, `GPS_BAUD_RATE`), the verified GPS park in `docs/research/peripheral-parking.md` section 11) |
| K8 | addition | UAR0_RX comes from the GPS board's GPS_TX (J102.2) through P8 pin 4; PPS (J102.1) is not carried, since P8 has four pins. | after every UAR0_RX label | Firmware: NMEA and UBX read on IO44 (`variants/tdeck/variant.h` (`PIN_GPS_TX`, `PIN_GPS_RX`, `GPS_BAUD_RATE`), `peripheral-parking.md` section 11) |
| K9 | correction | U5 pin 4 is XTAL_32K_P (GPIO0), used as ROW1; the print names it XTAL_OUT. The symbol takes the datasheet's name. | after the ROW1 label at U5 | ESP32-C3 datasheet v2.5, Table 2-1 p. 16 and Table 2-6 p. 21 |
| K10 | correction | U5 pin 5 is XTAL_32K_N (GPIO1), used as COL1; the print names it XTAL_IN. | after the COL1 label at U5 | as K9 |
| K11 | addition | P2's panel is a 2.8-inch 320x240 LCD driven by an ST7789; ESP_LCD_DC is its D/C input. | after every ESP_LCD_DC label | Firmware drives it as an ST7789 on this board (`variants/tdeck/variant.h` (`DISPLAY_TYPE_ST7789`, `DISPLAY_WIDTH`, `DISPLAY_HEIGHT`)); LilyGO's documentation page names the 2.8-inch 320 x 240 ST7789 |
| K12 | addition | P4's touch controller is a Goodix GT911; ESP_TP_INT is its INT. | after every ESP_TP_INT label | Firmware accepts an address only on a GT9xx product id (`src/drivers/touch/gt911.h`, `Gt911::begin`), and `TOUCH?` answers `model=GT911` (`docs/research/peripheral-parking.md` section 12.2) |
| K13 | addition | ES7210_INT is U2's interrupt output; nothing else on the board takes it. | after the ES7210_INT label | ES7210 datasheet revision 21.0, pin description p. 4 (INT, pin 13, O) |
| K14 | addition | DMIC_CLK is U2's digital-microphone clock output; nothing else on the board takes it. | after the DMIC_CLK label | ES7210 datasheet revision 21.0, pin description p. 4 (DMIC_CLK, pin 14, O) |
| K15 | addition | R22 100K to V3V against U6's internal 100 kohm pull-down holds SD_MODE near 1.65 V on a 3.3 V rail, above the B2 trip point (1.4 V typical, 1.5 V at most): U6 plays the left channel. (At the extremes, RPD at 92 kohm and R22 5 % high give 1.54 V; the print gives R22 no tolerance.) | nets page, pull table, R22 | MAX98357A/B datasheet 19-6779 Rev 7, Electrical Characteristics (B2 1.245-1.5 V, RPD 92-108 kohm) and Table 5 |
| K16 | addition | GAIN_SLOT on AGND through R20 0R sets U6's gain to 12 dB. | nets page, pull table, R20 | MAX98357A/B datasheet 19-6779 Rev 7, Electrical Characteristics, gain AV (GAIN_SLOT = GND: 12 dB) |
| K17 | correction | U6 pin 10 is OUTN, the negative speaker output; the print names pins 9 and 10 both OUTP. | after the U6_OUTN label | MAX98357A/B datasheet 19-6779 Rev 7, Pin Description (TQFN 9 OUTP, 10 OUTN) |
| K18 | addition | The ES7210 U2 answers at I2C address 0x40: `1000 0 AD1 AD0`, AD1 and AD0 held low by R1 and R2. | nets page, I2C table | ES7210 datasheet revision 21.0, p. 6; firmware `variants/tdeck/variant.h` (`ES7210_I2C_ADDR`) and its boot log `ES7210 powered down (0x40)` (`src/drivers/audio/es7210.cpp` (`powerDownEs7210`)) |
| K19 | addition | The ESP32-C3 U5 answers at I2C address 0x55, under its stock keyboard firmware. | nets page, I2C table | Firmware `variants/tdeck/variant.h` (`KEYBOARD_I2C_ADDR`), `src/drivers/keyboard/lilygo_keyboard.h` (its file comment, address 0x55), boot scan `I2C device at 0x55 <-- KEYBOARD`; LilyGO's Keyboard_ESP32C3 sketch |
| K20 | addition | The GT911 behind P4 answers at 0x5D or 0x14, latched from INT at each power-up of VDD3V3, which no GPIO drives then. | nets page, I2C table | Firmware `variants/tdeck/variant.h` (`PIN_TOUCH_INT`), `src/drivers/touch/gt911.h` (`Gt911::begin`: both addresses probed, and both seen on one unit, `docs/research/peripheral-parking.md` section 12.3); GT911 datasheet Rev.10 |
| K21 | addition | IO3 (`G_S1`, Hall sensor UZ3) reads the trackball rolled up. | nets page, ESP32-S3 GPIO table, GPIO3 | Firmware `variants/tdeck/variant.h` (`PIN_TRACKBALL_UP 3`); with that map each direction acted as the ball was rolled on the owner's unit, 2026-11-17 (`board.json` `trackball`) |
| K22 | addition | IO15 (`G_S3`, Hall sensor UZ1) reads the trackball rolled down. | nets page, ESP32-S3 GPIO table, GPIO15 | Firmware `variants/tdeck/variant.h` (`PIN_TRACKBALL_DOWN 15`); with that map each direction acted as the ball was rolled on the owner's unit, 2026-11-17 (`board.json` `trackball`) |
| K23 | addition | IO1 (`G_S4`, Hall sensor UZ4) reads the trackball rolled left. | nets page, ESP32-S3 GPIO table, GPIO1 | Firmware `variants/tdeck/variant.h` (`PIN_TRACKBALL_LEFT 1`); with that map each direction acted as the ball was rolled on the owner's unit, 2026-11-17 (`board.json` `trackball`) |
| K24 | addition | IO2 (`G_S2`, Hall sensor UZ2) reads the trackball rolled right. | nets page, ESP32-S3 GPIO table, GPIO2 | Firmware `variants/tdeck/variant.h` (`PIN_TRACKBALL_RIGHT 2`); with that map each direction acted as the ball was rolled on the owner's unit, 2026-11-17 (`board.json` `trackball`) |

The print's own note on GPIO46 ("pulled down by default; GPIO46 high with GPIO0 low is not usable") is carried in the GPIO46 row, and its note on IO35 to IO37 in theirs; both are the print's, not additions.

Two bench probes on 2026-11-17 settle questions without adding anything to the drawing:

- **The TP_EN edge detector does nothing on the owner's unit** ([`bench/2026-11-17-tp-en-edge-detector.md`](bench/2026-11-17-tp-en-edge-detector.md)). With V3V dead and the pads that back-feed it released, eight falling edges on IO16 switched V3V on in none of the 40 ms after them (IO46 through R12 read 0 in all 40,900 samples). The masked network is therefore not drawn as an addition: on this unit it is not fitted as printed, and whether a part is absent or differs needs the board opened. With V3V dead, SDA and SCL stayed high against the S3's pull-downs: that is RC4 and RC2, 4.7K to the always-on VDD3V3 on the S3's side of the level shifter, as the print draws them.
- **GPIO46 never latched high** ([`bench/2026-11-17-gpio46-strap.md`](bench/2026-11-17-gpio46-strap.md)): `GPIO_STRAP_REG` read `0x0008` after two cold power-ups (cell first and USB first), a USB Serial/JTAG core reset and two system resets with IO10 holding V3V on, and three software restarts. R12 to V3V does not reach the strap; the drawing carries only the print's note. The low latch at cold power-up also fits the masked power-on coupling through D4 doing nothing.

## Open questions

What no primary source settles yet stays out of the drawing:

- **Whether RD1 is fitted** (T32): the print shows RD1 100K%1 across VBAT. Bench probe B2 (cell current with SW1 slid off: about 41 uA with RD1, a few uA without) needs SW1 moved by hand, which the meter's relays cannot do; RD1 stays as printed.
- **The masked networks** (T01): which parts of the TP_EN edge detector (Q25, D30, R49, R70, R74, C73, D4) and of the other compile-masked networks (D48, D49, C79, R67; D4, D9, R68 and a 22uF) are absent needs the board opened; another production batch may differ.
- **The GPS cable** (T02): drawing it as a part (a cable joining J102 to P8, which would merge the `M10_` nets into the mainboard's) needs the owner's decision on the form; its physical pin order needs the board opened; the L76K board shares J102's pinout on its print but was never run.
- **U0 pin 6** (T05): named NC on the vendor's symbol but carrying `Lora_P1.01_GPIO2`; HopeRF's HPD16A datasheet was not found, so it stays as printed.
- **The MIA-M10Q board's A5 and D2-E2** (T12): A5 (RTC_O) drawn to GND and D2 joined to E2, both RESERVED; the u-blox MIA-M10Q data sheet's pin table (its download was refused on 2026-11-17) would settle whether these are required straps or a print error. Kept as printed.
- **KEY1 pin 4** (T13): on GND in the print, on a net of its own in the PDF's markers; the TS-1187A datasheet (pins 3 and 4 joined inside the switch) would close it. Kept on GND, as printed.
- **VDD3V3's set point** (T31): 0.6 V x (1 + R23 100K / R24 22K) = 3.33 V if the SY8089's feedback reference is 0.6 V; its datasheet has not been read for it.
- **USB-C CC pull-downs** (T33): RC5 and RC6 5.1K make the port a sink by the USB Type-C specification; whether a specification counts as a source for an entry is the owner's call.
- **The charge current** (T34): R25 2K%1 on PROG gives about 500 mA, but 2 kohm is not a point of the TP4065's table; it needs a measurement.
- **Part numbers** (T09): the speaker, the antenna XX2 (printed TIAN), the crystal U4, the LED beyond "Blue", the keyboard board behind JP1, and the LCD and touch panels behind P2 and P4 (whose controllers are K11 and K12).

## Files

| File | What it is | Edited by |
| --- | --- | --- |
| `netlist.yaml` | The facts: every component, its value, the sheet it is on, each pin and its net; rails (with their nominal voltage), I2C, the GPIO maps, every pull-up and pull-down | hand (review here) |
| `layout.yaml` | How it is drawn: our symbols, which symbol each part takes, the sheets, blocks and rows, the power tree's boxes and arrows, the revision history | hand |
| `tdeck-plus.kicad_sch` + eight child `.kicad_sch`, `tdeck-plus.kicad_sym`, `tdeck-plus.kicad_pro`, `sym-lib-table` | The KiCad project | generated |
| `links.json` | Where each link of the PDF lands, the named destinations and the bookmarks, for `_shared/schematic_pdf.py` | generated |
| `tdeck-plus.pdf` | The pages | generated |
| `svg/` | One SVG per page, written by the export when it runs; not kept in git | generated |

## Regenerate and check

```bash
.venv/bin/python _shared/kicad_schematic.py tdeck-plus   # KiCad files from netlist.yaml + layout.yaml
.venv/bin/python _shared/export_schematic.py tdeck-plus  # ERC, netlist check, PDF (+ links), SVGs, link check
.venv/bin/python _shared/check_schematic_links.py tdeck-plus --list   # every link of the PDF and where it lands
.venv/bin/python -m pytest tests/test_schematic.py
```

The export fails unless the ERC reports nothing, `check_schematic.py` finds every vendor pin on the net `netlist.yaml` names, every SVG has the theme's background and one line width, and `check_schematic_links.py` finds every link leading where it should. Besides the two library checks every board switches off, `layout.yaml` switches off one ERC check for this board (`erc_ignore`): "label connected to only one pin", because the vendor's print hangs a net label on a single pin for `ES7210_INT`, `DMIC_CLK` and `Lora_P1.01_GPIO2`, and the drawing keeps those labels.

## What the schematic does not say

- Three networks on the mainboard sheet sit inside compile-mask frames, which Altium leaves out of the design (the PDF carries no part marker for them): two TP_EN networks at the right of the sheet (D48, D49, C79, R67; D4, D9, R68 and a 22uF/6.3V capacitor), a third below them (Q25 PMBT3906, D30, R49, R70, R74, C73), and a framed D4 1N4148 from TP_EN beside D3. They are not drawn; on the owner's unit the TP_EN edge detector does nothing (bench, above), and which parts are absent is open.
- Which GPS daughterboard a given unit carries (the owner's carries the MIA-M10Q board: the firmware finds a u-blox M10 answering UBX at 38400 baud), and the cable between its J2 (5 pins: PPS, GPS_TX, GPS_RX, VDD3V3, GND) and the mainboard's P8 (4 pins: GND, VDD3V3, UAR0_TX, UAR0_RX): none is published. The daughterboards are drawn as LilyGO prints them, on their own nets; what P8 carries to them is K3, K7 and K8.
- `ES7210_INT`, `DMIC_CLK` and `Lora_P1.01_GPIO2` end at a single pin: the print gives each a net label and nothing else on it. The first two are outputs of the ES7210 (K13, K14). U0 pin 6, named NC on the vendor symbol, is the pin `Lora_P1.01_GPIO2` sits on (open).
- Part numbers the print leaves out: the battery (its capacity is K1), the speaker, the LCD and touch panels behind P2 and P4 (their controllers are K11 and K12), the keyboard board behind JP1, the antenna XX2 (printed TIAN), the LED colour beyond "Blue", and the crystal U4's part.
- The ESP32-S3 module's internals (flash, PSRAM, crystal) are inside U1 and not on the schematic; its part number is K4. IO35, IO36 and IO37 are left unconnected, as the sheet's note says they serve the in-package PSRAM.
- On the MIA-M10Q board the print draws A5 (RTC_O) to GND and joins D2 to E2 (both RESERVED); the drawing keeps both as printed (open).
- KEY1 pin 4 (B1) is drawn wired to GND in the print, and is on GND here. The PDF's net markers, which the other connections agree with pin for pin, list it on a net of its own: the wire drawn to it ends about 0.05 pt short of the pin's end. `netlist.yaml` notes it on KEY1.
- The mainboard sheet shows no test points, so the nets page has no test-point table.
