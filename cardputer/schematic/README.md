<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# M5Stack Cardputer-Adv (K132-Adv): schematic

Kleidos boards: the Cardputer-Adv's connectivity in KiCad, documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1 (sources below and in `netlist.yaml`): every part, pin and net of the carrier board and of the Stamp-S3A core module that sits on it, with the values the vendor documents, laid out with this project's own layout and symbols. It tells what connects where and how: pull-ups and pull-downs with their values, series parts, the filter and protection parts on each interface, every rail and what feeds it, and the ESP32-S3 GPIO of every signal.

[`cardputer.pdf`](cardputer.pdf) has the nine pages, made to be read on a screen and followed by clicking (below); the export also writes one SVG per page into `svg/`, which git does not keep. Both are drawn with the Kleidos KiCad kit ([`_shared/kicad/`](../../_shared/kicad/), copied from the brand repository): the dark theme (graphite ground, parts in light grey, connections in cyan) and the Kleidos drawing sheet, whose title block carries the Kleidos mark, the license and the source address. The pages are A2: the carrier's first sheet and the module's sheet each hold about sixty parts, more than an A3 page takes at this project's spacing.

| Page | Sheet | What is on it |
| --- | --- | --- |
| 1 | Contents | One box per page with what is on it and its main parts, how to read the drawing, the notes (values, DNP, numbering, zones), the Kleidos additions and corrections with their sources, and the revision history |
| 2 | Power, sockets and ports | Carrier sheet 1: the TP4057 charger, the battery connectors, the power switch and the MOSFET power path with its CN809J supervisor, the SY7088 5 V boost, the SY8089 3.3 V buck, the sockets the module plugs into, the reset and G0 buttons, the microSD socket, the Grove port and its supply switch, the FPC expansion connector, the IR emitter |
| 3 | Keyboard | Carrier sheet 2: the TCA8418RTWR key scanner and the 56 keys, drawn in the vendor's four rows of 14 |
| 4 | Motion sensor and audio | Carrier sheet 3: the BMI270, the ES8311 codec, the microphone, the NS4150B amplifier and speaker connector, the headphone jack and its detect transistor |
| 5 | EXT header | Carrier sheet 4: the 14-pin 2.54 mm header |
| 6 | Stamp-S3A module | The module's sheet: the ESP32-S3FN8 with its RF path, crystal and decoupling, the JW5712 3.3 V buck, the LCD FPC connectors and the backlight load switch, the RGB LED, the module's G0 button, the USB-C with its fuse and ESD parts, and the module's pins |
| 7 | Power tree and rails | How power flows from the USB-C and the battery to every rail, with each part's enable; then every rail's nominal voltage, source, enable and where it is drawn |
| 8 | Nets and signals | Every rail and every net drawn on more than one page with the page/zone of its labels; the ESP32-S3 GPIO map, the I2C addresses, the pads (J5, J6, JP102, JP103) and the plated hole PHD101, every pull-up and pull-down |
| 9 | Parts | Every part: its value as printed, what it is, its nets (two-pin parts), whether it is fitted, and where it is drawn |

Pages 7 to 9 are written by the generator from `netlist.yaml`, not drawn by hand: they cannot disagree with the drawing.

## What it is not

- Not the vendor's design files. The layout, the blocks and every symbol are this project's: the integrated circuits' and connectors' are each board's own (`cardputer.kicad_sym`), and the passive parts, the diodes, the transistors, the switches, the plain connectors, the pads and the ground symbols are this project's generic ones (`kleidos.kicad_sym`, drawn by `_shared/kicad_schematic.py`). No symbol of KiCad's libraries is in these files. No vendor document is in this repository; the sources are cited below.
- Not a PCB design: no footprints, no part numbers beyond the ones the vendor prints, nothing about placement or routing.
- Not a full datasheet of each part: pin names and values are as the vendor documents them (`10KΩ`, `10K/1%`, `22uF`, `NC` for a part not fitted).

## How to read it

Pins connect by net labels, not by wires. Two pins whose labels carry the same name are on one net, on any page. After a label, each `[6/B2]` names another page that carries the net and the zone of its label there (the border prints numbered columns and rows A-H, 50 mm apart): page 6, row B, column 2. Clicking it lands on that label, zoomed in; on a page where the net has several labels, it lands on the one at the part that feeds the rail (`rails.from` in `netlist.yaml`), or else on the first in reading order. A label with none is on its page only. Neighboring pins of one part on one net share a short bar and one label. A cross on a pin end means the pin is unconnected. Wires and pin lines are one color and one width, so a connection reads as one line from the part to its label.

Parts documented as not fitted (value `NC`) carry KiCad's DNP mark: a red cross over the symbol. On this board that is C120, a shunt position in the module's RF path.

In the PDF, each box on the contents page opens its page, and every page carries "Contents" and a row of page numbers above the title block. Each part's reference on the drawing is a link to its row in the parts list, and the row's reference and page/zone lead back to the part. Every place in the index pages (a page/zone, a box of the power tree, a reference in a table) is a link to it. The bookmarks list the pages and, under each, its parts or its tables, each at its place. `_shared/check_schematic_links.py` holds every one of those links (`--list` prints them all).

### In any PDF reader

KiCad can give each part a property pop-up, but it is a script that only Acrobat runs, so the export leaves the pop-ups out and the PDF holds no script at all. What they showed (reference, value) and more is in the parts list. The rest is plain PDF that every reader follows:

- a link leads to a page and a position: `/XYZ`, the target placed 30 mm from the window's left edge and 20 mm below its top, at zoom 2. KiCad links a text only to a whole page, so `_shared/schematic_pdf.py` sends each link to its place after the export, from the targets the generator writes into `links.json`;
- each link carries a `/Contents` saying where it leads, for screen readers;
- named destinations open the PDF at a part or at a net's label on a page, from a web page or another document: `cardputer.pdf#nameddest=part-U101`, `cardputer.pdf#nameddest=net-VBAT_OUT-p2`.

### Two boards, one numbering

The product is two boards and the vendor publishes a schematic for each: the Cardputer-Adv carrier (four sheets) and the Stamp-S3A module (one sheet, the Stamp-S3 schematic v0.3.3 that both the Cardputer-Adv and the Stamp-S3A pages link). Each sheet is a page here, in the order the vendor's documentation page shows them: the carrier's four, then the module's.

- Both schematics number their parts from 1, so the module's parts are +100 here: its U1 (the ESP32-S3FN8) is U101, its M1 (the module's pins, STAMP-S3M) is M101, its JP2 is JP102, and so on. The carrier's designators are the vendor's.
- The module's pins land on the carrier's sockets P1 (Header 17) and P2 (Header 11). The carrier sheet draws both sockets wired pin for pin to the module's footprint M1 (STAMP-S3-DIP-1.27), whose pins are named as the module's: P1 pin n is module pin n (1-17) and P2 pin n is module pin 29 - n (28 down to 18). That footprint has no pins in the carrier's netlist, so it is not drawn; M101 stands in its place.
- A net the module and the carrier share takes the carrier's name: the module's `GPIO8` is `G8`, its `VDD_3V3` is `+3.3V`, its `VIN_5V` is `+5VIN`, its `TX` and `RX` are `G43` and `G44`. `netlist.yaml` lists each under `aliases`.
- `GI` and `GO` are the vendor's own names for the Grove pair (GPIO1 and GPIO2, with letters I and O), kept as printed.
- Nets the vendor left unnamed have names of ours (`U2_FB`, `SD_CS`, `BAT_SW`...); `netlist.yaml` lists each with the name Altium generated for it.
- The EXT header P3 is numbered as the vendor's schematic numbers it (1 RESET, 2 INT, 3 BUSY... 14 5VIN), which is not the order the vendor's documentation page lists its pins in.

## Sources

| Document | Version | Address | Read at | SHA-256 |
| --- | --- | --- | --- | --- |
| Cardputer-Adv schematic | v1.0 (Altium output 2025-06-12, file dated 2025-06-20), 4 sheets | <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1178/Sch_M5CardputerAdv_v1.0_2025_06_20_17_19_58.pdf>, listed on <https://docs.m5stack.com/en/core/Cardputer-Adv> | the Internet Archive's copy of 2026-07-17 | `9553f5ee22b6e5f29a385388192e42c5ff76f16281b6f7ea9418f7b62a2d48b0` |
| Stamp-S3 schematic (the Stamp-S3A module) | v0.3.3 (Altium output 2024-09-11), 1 sheet | <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1150/Sch_StampS3_v0.3.3.pdf>, listed on the Cardputer-Adv and Stamp-S3A pages | the Internet Archive's copy of 2026-10-30 | `2f9610aecc5a5d2ee51b33c75df31cf90c7639d2997e7a2bb147ba8d46b46966` |

The vendor's host did not answer from the machine that drew this on 2026-11-17, so the Internet Archive's copies (the addresses in `netlist.yaml`) were read; they are the files `board.json` cites.

| Vendor sheet | What is on it | Its facts are on |
| --- | --- | --- |
| Cardputer-Adv 1 (M5CardputerAdv) | Power, the module's sockets, buttons, microSD, Grove, IR, FPC1 | page 2 |
| Cardputer-Adv 2 (KeyScan) | Key scanner and keys | page 3 |
| Cardputer-Adv 3 (IMU) | Motion sensor, codec, microphone, amplifier, jack | page 4 |
| Cardputer-Adv 4 (HAT) | EXT header | page 5 |
| Stamp-S3 1 (StampS3_v0.3.3) | ESP32, DCDC, LCD, RGB LED, BTN-USER, USB, module pins | page 6 |

The connections were read off the printed pages and then taken, pin by pin, from the netlist Altium writes into each PDF's bookmarks (Nets → Pins, per sheet); the two agree everywhere. The carrier's four sheets join by net name (the bookmarks list `G3` on P1 of sheet 1 and on P3 of sheet 4, and so on). The values come from the printed pages. The TCA8418's 0x34 and the BMI270's 0x69 are printed on carrier sheets 2 and 3.

What the sheets do not show and a primary source makes certain is drawn as a Kleidos addition, and the two places where the drawing differs from the print are Kleidos corrections; each is listed below and on page 1. Those sources, read on 2026-11-17 unless noted, each cited in full under `source.also_read` in `netlist.yaml`:

- the vendor's other documents: the Cardputer-Adv and Stamp-S3A documentation pages (read at Switch Science's mirror on 2026-11-16) and the vendor's M5Unified library (`src/M5Unified.inl` at 96576a1, the ES8311's address, which `board.json` also records);
- datasheets: Espressif's *ESP32-S3 Series Datasheet* v2.2 (Tables 1-1, 3-1, 3-3, 3-4) and its *Technical Reference Manual* v1.8 (Register 6.15, the strapping register's bits; Table 7.1-1 and Section 8.1, when the straps latch); LP3218DT1G Rev.B (Leshan Radio); CN803/809/810 Rev 0 (Consonance); TP4057 (NanJing Top Power); AN_SY8089/SY8089A Rev 0.9A (Silergy); TCA8418 SCPS215G (Texas Instruments); the NS4150 user manual V1.0 (Nsiway) and the ES8311 datasheet Revision 7.0 (Everest), both as Espressif hosts them;
- the bench records in [`bench/`](bench/), taken on 2026-11-17 on the bench unit with its case closed, over its USB-C: the internal I2C scan and chip identities ([`2026-11-17-i2c-scan.md`](bench/2026-11-17-i2c-scan.md)), the idle levels and pulls of G0, G1, G2 and G11 ([`2026-11-17-gpio-levels.md`](bench/2026-11-17-gpio-levels.md)) and the ROM's boot line with the latched straps ([`2026-11-17-boot-strap.md`](bench/2026-11-17-boot-strap.md)).

## Kleidos additions and corrections

The drawing improves on the vendor's print where a primary source makes a detail certain (AGENTS.md, "Schematics"). Each entry is in `kleidos` in `netlist.yaml`, marked on the drawing by its id in amber and listed with its source on page 1; the triage of every candidate, settled or not, is [`improvements.md`](improvements.md) (its T-ids below). There are 19: 17 additions and 2 corrections. No connection is added, so no wire is dotted; a fact about a part the print already draws is marked where its net, rail or table row carries it.

| Ids | What | Source |
| --- | --- | --- |
| K1-K3 (T04) | Q1-Q3 are 12 V P-channel MOSFETs; their pins are named on the drawing: 1, 2, 5, 6 and 8 drain, 3 gate, 4 and 7 source. Q1 joins VBAT_IN (drain) to VBAT_OUT (source); Q2 (drain on BAT, gate on GND) and Q3 (drain on VBAT_IN) meet source to source on BAT_SW, back to back. Marked on Q1_GATE, BAT_SW and Q3_GATE | LP3218DT1G datasheet Rev.B, p. 1 (DFN2020-6S: 1, 2, 5, 6 drain, 3 gate, 4 source). Pins 8 and 7 are the package's drain and source pads: on every one of the three parts the print puts 8 with 1, 2, 5, 6 and 7 with 4, the one assignment that fits |
| K4 (T26) | VBAT_OUT takes the cell through Q1 only while +5VIN is under 4.00 V: the CN809J U3 holds RESET low there, push-pull, and for at least 140 ms after +5VIN rises; with USB present VBAT_OUT comes through D1 | CN803/809/810 datasheet Rev 0, pp. 1, 2, 4 |
| K5 (T28) | R5 3.3KΩ sets the TP4057's charge current, about 0.30 A, to a float of 4.2 V | TP4057 datasheet, p. 7 (RPROG = 1000 / IBAT, 3 kΩ for 300 mA) and its electrical table |
| K6 (T29) | +3.3V from U4 SY8089 is 0.6 V × (1 + 68K / 15K) = 3.32 V | AN_SY8089/SY8089A Rev 0.9A, p. 2 (pin table: Vout = 0.6 × (1 + R1/R2); EN pulled high to turn on) and p. 4 (VREF 0.6 V) |
| K7 (T33) | U9 TCA8418's ROW0-7 and COL0-9 have 105 kΩ internal pull-ups, enabled from reset; they hold the unconnected ROW7 (pin 1, where it is marked), COL8 and COL9 | TCA8418 SCPS215G, pp. 3, 5, 34; bench: GPIO_PULL1-3 read 0x00 (all enabled) and ROW7, COL8, COL9 read high ([`bench/2026-11-17-i2c-scan.md`](bench/2026-11-17-i2c-scan.md)); the Kleidos firmware never writes GPIO_PULL (`src/drivers/keyboard/tca8418.cpp` (`Tca8418::writeRegister`)) |
| K8 (T25) | AMP_EN high runs the NS4150B U5, low shuts it down: with R23 up and Q4 pulling it low only while a plug is in, the amplifier runs whenever +3.3V is up and the jack is empty, deep sleep included | NS4150 user manual V1.0, Section 9.6, Table 4, p. 11 (VIH 1.2 V minimum); the manual names the NS4150, and no B-specific document was found. That a plug in the jack disables the amplifier is the vendor's own statement, on the Cardputer-Adv documentation page ("Speaker Feature Note") |
| K9 (T14) | The ES8311 U6 answers at I2C address 0x18 | ES8311 datasheet Rev 7.0, p. 5 (0011 00x, x = CE; CE on AGND); bench: only 0x18, 0x34 and 0x69 answer on G8/G9, 0x19 does not, and registers 0xFD/0xFE read the ES8311's 0x83 0x11 ([`bench/2026-11-17-i2c-scan.md`](bench/2026-11-17-i2c-scan.md)); M5Unified `es8311_i2c_addr0 = 0x18` |
| K10, K11 (T02) | ANT101 is a 2.4 GHz 3D antenna; U103 is a WS2812B-2020 (the sheet prints no value and `WS2812`). Marked on ANT_FEED and GPIO21 | the Stamp-S3A documentation page, specifications |
| K12 (T15) | Correction: J102's block is a USB-C port. The print titles the block "Type-A USB"; the part in it is `USB-TYPEC`, with CC1/CC2 and the 5.1K pull-downs R101, R102 | the Cardputer-Adv and Stamp-S3A documentation pages (USB Type-C); the sheet's own part |
| K13, K14, K16, K17 (T32) | The ESP32-S3 straps: GPIO0 weak pull-up (low at reset, with GPIO46 low, selects download boot), GPIO3 floating (JTAG signal source), GPIO45 weak pull-down (VDD_SPI voltage: low selects 3.3 V unless an eFuse forces it), GPIO46 weak pull-down (with GPIO0, the boot mode). GPIO46 carries the codec's ASDOUT, and it latches low with the codec attached | ESP32-S3 datasheet v2.2, Tables 3-1 (p. 32), 3-3 (p. 33), 3-4 (p. 34); bench: the ROM printed `boot:0x2b (SPI_FAST_FLASH_BOOT)`, decoded with the ESP32-S3 TRM v1.8's Register 6.15 (p. 506): GPIO0 latched 1, GPIO45 and GPIO46 latched 0 ([`bench/2026-11-17-boot-strap.md`](bench/2026-11-17-boot-strap.md)) |
| K15 (T20) | GPIO11, the TCA8418's ~INT, is an open-drain, active-low output; R37 3.3KΩ holds it up | TCA8418 SCPS215G, p. 3, pin 24. The bench reading (G11 idles high) cannot isolate R37 or show the open drain, because the firmware turns on the ESP32's own pull-up there (`src/drivers/keyboard/tca8418.cpp` (`Tca8418::init`)), so this entry rests on the datasheet |
| K18 (T11) | FLASH_VCC (VDD_SPI) is 3.3 V, the FN8's VDD_SPI voltage, from VDD3P3_RTC through RSPI; GPIO45, unconnected, latches low, which selects that unless an eFuse forces VDD_SPI | ESP32-S3 datasheet v2.2, Table 1-1 (p. 13, the FN8's VDD_SPI 3.3 V) and Table 3-4 (p. 34); bench: GPIO45 latched 0 ([`bench/2026-11-17-boot-strap.md`](bench/2026-11-17-boot-strap.md)) |
| K19 (T07) | Correction: C114 is 12pF, X101's second load capacitor. The print writes its value twice, `12pF 12pF` | the Stamp-S3 schematic v0.3.3 itself: C109, the load capacitor on the crystal's other pin, reads 12pF |

Firmware citations are the Kleidos firmware repository (2026-11-17), code that runs on the Cardputer-Adv. The bench unit ran a `cardputer_debug` image of the same day.

## Files

| File | What it is | Edited by |
| --- | --- | --- |
| `netlist.yaml` | The facts: every component, its value, the vendor's sheet, each pin and its net; aliases, rails (with their nominal voltage), I2C, ESP32 GPIO map, every pull-up and pull-down; the Kleidos additions and corrections (`kleidos`) with their sources | hand (review here) |
| `improvements.md` | The triage of every candidate addition or correction, with its evidence and status, and the bench probes | hand |
| `bench/` | The bench records the entries and the open questions cite | hand |
| `layout.yaml` | How it is drawn: our symbols, which symbol each part takes, the sheets, blocks and rows, the power tree's boxes and arrows, the revision history | hand |
| `cardputer.kicad_sch` + eight child `.kicad_sch`, `cardputer.kicad_sym`, `cardputer.kicad_pro`, `sym-lib-table` | The KiCad project | generated |
| `links.json` | Where each link of the PDF lands, the named destinations and the bookmarks, for `_shared/schematic_pdf.py` | generated |
| `cardputer.pdf` | The pages | generated |
| `svg/` | One SVG per page, written by the export when it runs; not kept in git | generated |

## Regenerate and check

```bash
.venv/bin/python _shared/kicad_schematic.py cardputer   # KiCad files from netlist.yaml + layout.yaml
.venv/bin/python _shared/export_schematic.py cardputer  # ERC, netlist check, PDF (+ links), SVGs, link check
.venv/bin/python _shared/check_schematic_links.py cardputer --list   # every link of the PDF and where it lands
.venv/bin/python -m pytest tests/test_schematic.py
```

The export fails unless the ERC reports nothing (0 errors, 0 warnings), `check_schematic.py` finds every vendor pin on the net `netlist.yaml` names (no pin missing, no net split or joined, nothing drawn that the netlist lacks), every SVG has the theme's background and one width for every line in the wire color (6 mil), and `check_schematic_links.py` finds every link of the PDF leading where it should and no script in it. The generator needs the `gpio_title` and `pin_length` options of `_shared/kicad_schematic.py` (the nets page's GPIO table is U101's, and the USB-C's pin numbers `VBUS` and `SHELL` need pins longer than 2.54 mm).

## What the schematic does not say

- Part numbers the print leaves out: the antenna ANT101, the USB choke L105, the pads J5, J6, JP102 and JP103, the keys S1-S56 and the buttons BTN1 and BTN2 (`SW-PB`), the slide switches SW1 and SW2 (`SW-SPDT`), the battery and speaker connectors (`Header 2`), the ferrite beads FB1-FB3 (`FB`) and the IR emitter (`IR`).
- The module's antenna and RGB LED parts are named from the Stamp-S3A documentation page (K10, K11); the sheet's symbols read only `ANT1` and `WS2812`. The Stamp-S3A page lists the module's DC-DC as MUN3CAD01-SC; the sheet draws U4 as JW5712, and that is what is drawn (Open questions).
- The LCD FPC connectors J101 (12 contacts) and J103 (8 contacts) are both printed with a `/NC` suffix; the sheet does not say what it means, so neither is marked not fitted.
- C119 is a capacitor symbol whose value reads `4.3nH`, kept as printed (Open questions). C114's value is printed twice (`12pF 12pF`); it is drawn as `12pF`, Kleidos correction K19.
- The microphone U8's pin 3, named GND on the vendor's symbol, is wired to `MIC_N`, and pin 2 to AGND: drawn as the vendor wires them.
- Carrier sheet 1 also holds a greyed-out R3 (1KΩ) and D3 (an LED) on VBAT_OUT. Altium's netlist leaves them out (their designators belong to the Grove pull-up R3 and the headphone-detect diode D3), so they are not drawn.
- The WS2812's DO carries a label, `SK_DOUT`, that reaches no other pin: it is drawn unconnected, as are the other pins the vendor connects to nothing, among them the TP4057's ~CHRG and ~STDBY (no charge-status signal reaches the ESP32), the TCA8418's ROW7, COL8 and COL9, the jack's pin 6 and the module button's pin 3.
- The ESP32-S3FN8's flash is inside its package and not on the schematic; FLASH_VCC is its VDD_SPI pin, 3.3 V (K18).
- The LCD panel, its controller and the keyboard's key caps are not on the schematic: the panel reaches the module through J101 / J103, which is where the drawing stops.
- The battery's capacity and chemistry: the connectors carry no value.

## Open questions

What is still uncertain stays off the drawing. Each item names what would settle it; the ids are those of [`improvements.md`](improvements.md). The bench pass of 2026-11-17 ran the three probes that need no hands on the board (P01, P02 and P06); P02 and P06 are half done, because their other half needs someone holding the side key G0, and P03, P04 and P05 did not run because no one was at the bench.

- **The rails on the bench (T29, P03).** K6 (+3.3V, 3.32 V) is computed from the SY8089 datasheet and BOOST_OUT's 5.29 V from the printed formula; neither is measured. P03 (a multimeter on a microSD breakout's VDD, and on EXT P3 pins 12 and 14 against 13, on battery and on USB) needs a person with a meter.
- **The charge current on the bench (T28, P04).** K5 (about 0.30 A) is from the TP4057 datasheet; P04 (an inline USB-C meter at two charge states) needs a person to read it.
- **The EXT header's physical positions (T39, P05).** The drawing numbers P3 as the sheet does; the vendor's pin map numbers it otherwise, and its 2026-04-07 page swapped UART_TX and UART_RX on G13 and G15. P05 (each position tied to GND through 1 kΩ in turn while the debug console reads the GPIOs) needs someone to tie them.
- **G0 held (P02, P06).** Pressing the side key should read G0 low, and a power-up with it held (the reset key BTN1, not the USB reset, which does not re-latch the straps) should print the download-boot value; both need someone at the key. Neither is needed by an entry: K13 and K17 rest on the datasheet and the released reading.
- **R37 alone on G11 (T20).** The bench reading of G11 could not isolate R37 or show the open drain, because the firmware turns on the ESP32's pull-up there; K15 rests on the TCA8418 datasheet.
- **The backlight switch U102 (T24).** The Awinic product page gives the AW35122FDR an active-high EN with an internal pull-down and quick output discharge, which would explain why BL_3V3 stays off while G38 floats; its datasheet (DS_AW35122_EN_V1.0, with the B1/B2 pin table) was not read, so nothing is added.
- **The BMI270's interface (T19).** CSB (pin 12) on VDDIO selects I2C; Bosch's datasheet section on the interface selection was not read for the cite.
- **The ES8311 without MCLK (T34).** The vendor's library runs the codec with its clock taken from SCLK (register 0x01 = 0xB5 / 0xBA); the ES8311 user guide's register map was not read, so U6 pin 2 stays as printed, unconnected, with no note on the drawing.
- **The module's DC-DC U104 (T03, T30).** The sheet draws a JW5712, the Stamp-S3A page lists a MUN3CAD01-SC; reading the part needs the module out of the case. The JW5712's VSEL1-3 coding stays out until then (no datasheet found).
- **The LCD connectors J101 and J103 (T05).** Both are printed with a `/NC` suffix; which one carries the panel needs the module out of the case.
- **C119 (T06).** A capacitor symbol valued `4.3nH`: either the symbol or the value is wrong, and settling it needs the part off the board and an LCR meter. Kept as printed.
- **The microphone's pin 3 (T08).** Named GND on the vendor's symbol and wired to MIC_N, a pseudo-differential input; the MSM381A3729H9BPC datasheet was not read to name the pin.
- **Part numbers the print leaves out (T01).** ANT101's maker, L105, the pads J5, J6, JP102, JP103, the keys and buttons, SW1, SW2, J1, J4, J8, FB1-FB3 and IR1: they need the board opened, and most carry no marking.
- **Crossings without a dot (T35).** Every connection was taken from the netlist Altium wrote into each PDF's bookmarks and agrees with the printed pages; the printed pages were not re-rendered in this pass to look for a wire crossing a bar with no junction dot.
