<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# M5StickS3 (K150): schematic

Kleidos boards: the M5StickS3's connectivity in KiCad, documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1 (sources below and in `netlist.yaml`): every part, pin and net of the vendor's published schematic, with the values the vendor documents, laid out with this project's own layout and symbols, plus eleven details the print leaves out or gets wrong, each settled by a datasheet, the vendor's own manual or a bench probe and marked where it is drawn (below, "Kleidos additions and corrections"). It tells what connects where and how: pull-ups and pull-downs with their values, series parts, the filter and decoupling parts on each interface, every rail and what feeds it, and the ESP32-S3 GPIO of every signal.

[`sticks3.pdf`](sticks3.pdf) has the nine pages, made to be read on a screen and followed by clicking (below); the export also writes one SVG per page into `svg/`, which git does not keep. Both are drawn with the Kleidos KiCad kit ([`_shared/kicad/`](../../_shared/kicad/), copied from the brand repository): the dark theme (graphite ground, parts in light grey, connections in cyan) and the Kleidos drawing sheet, whose title block carries the Kleidos mark, the license and the source address.

| Page | Sheet | What is on it |
| --- | --- | --- |
| 1 | Contents | One box per page with what is on it and its main parts, how to read the drawing, the notes (values, DNP, numbering, zones), the Kleidos additions and corrections with their sources, and the revision history |
| 2 | Power input and charging | USB-C, over-voltage switch, charger, battery, the ideal-diode power path, the ADC dividers, the power key and the status LED |
| 3 | Rails and power management | The 3.3 V rails L0, L1, L2, L3B and L3B_AU, the 5 V boost for Grove, the M5PM1 |
| 4 | ESP32-S3 | The ESP32-S3-PICO-1-N8R8, its supply and RF path, reset, boot strap, USB, I2C pull-ups, keys, test points |
| 5 | Display, IMU and audio | The LCD connector and backlight switch, the BMI270, the I2C isolator, the ES8311, the microphone, the amplifier |
| 6 | Connectors and HAT2 daughterboard | The HAT2 socket and the Grove port; the daughterboard with its plug, the HAT2 header, the IR receiver and transmitter, the speaker |
| 7 | Power tree and rails | How power flows from the USB-C, HAT2 and Grove inputs and the battery to every rail, with each part's enable; then every rail's nominal voltage, source, enable and where it is drawn |
| 8 | Nets and signals | Every rail and every net drawn on more than one page with the page/zone of its labels; the ESP32-S3 and M5PM1 GPIO maps, the I2C addresses, the test points, every pull-up and pull-down |
| 9 | Parts | Every part: its value as printed, what it is, its nets (two-pin parts), whether it is fitted, and where it is drawn |

Pages 7 to 9 are written by the generator from `netlist.yaml`, not drawn by hand: they cannot disagree with the drawing.

## What it is not

- Not the vendor's design files. The layout, the blocks and every symbol are this project's: the integrated circuits' and connectors' are each board's own (`sticks3.kicad_sym`), and the passive parts, the diodes, the transistors, the switches, the plain connectors, the pads and the ground symbols are this project's generic ones (`kleidos.kicad_sym`, drawn by `_shared/kicad_schematic.py`). No symbol of KiCad's libraries is in these files. No vendor document is in this repository; the sources are cited below.
- Not a PCB design: no footprints, no part numbers beyond the ones the vendor prints, nothing about placement or routing.
- Not a full datasheet of each part: pin names and values are as the vendor documents them (`10K/1%`, `22uF/10V`, `NC` for a part not fitted).

## How to read it

Pins connect by net labels, not by wires. Two pins whose labels carry the same name are on one net, on any page. After a label, each `[3/C4]` names another page that carries the net and the zone of its label there (the border prints columns 1-8 and rows A-F, 50 mm apart): page 3, row C, column 4. Clicking it lands on that label, zoomed in; on a page where the net has several labels, it lands on the one at the part that feeds the rail (`rails.from` in `netlist.yaml`), or else on the first in reading order. A label with none is on its page only. Neighboring pins of one part on one net share a short bar and one label. A cross on a pin end means the pin is unconnected. An amber `K3` beside a label, a reference, a crossed pin or a table row marks a Kleidos addition or correction; it leads to its row on page 1, and the row back to it. Wires and pin lines are one color and one width, so a connection reads as one line from the part to its label.

Parts documented as not fitted (value `NC`, `NC(TBD)`) carry KiCad's DNP mark: a red cross over the symbol.

In the PDF, each box on the contents page opens its page, and every page carries "Contents" and a row of page numbers above the title block. Each part's reference on the drawing is a link to its row in the parts list, and the row's reference and page/zone lead back to the part. Every place in the index pages (a page/zone, a box of the power tree, a reference in a table) is a link to it. The bookmarks list the pages and, under each, its parts or its tables, each at its place. `_shared/check_schematic_links.py` holds every one of those links (`--list` prints them all).

### In any PDF reader

KiCad can give each part a property pop-up, but it is a script that only Acrobat runs (Firefox's pdf.js, Chrome and Edge, Preview and the Poppler readers have no such menu), so the export leaves the pop-ups out and the PDF holds no script at all. What they showed (reference, value) and more is in the parts list, which any reader, and paper, can use. The rest is plain PDF that every reader follows:

- a link leads to a page and a position: `/XYZ`, the target placed 30 mm from the window's left edge and 20 mm below its top, at zoom 2 (the 1.27 mm text then reads at about 7 pt). KiCad links a text only to a whole page, so `_shared/schematic_pdf.py` sends each link to its place after the export, from the targets the generator writes into `links.json`;
- each link carries a `/Contents` saying where it leads, for screen readers (most readers show no tooltip);
- named destinations open the PDF at a part or at a net's label on a page, from a web page or another document: `sticks3.pdf#nameddest=part-U16`, `sticks3.pdf#nameddest=net-VBUS_L0-p3` (Acrobat, Firefox and Chrome honor the `#nameddest=` address).

Acrobat, pdf.js and PDFium honor the position and zoom of an `/XYZ` destination by their documentation and source code. Preview, iOS, Okular, Evince and Android's viewer have not been tried by hand; a reader that ignores the position still opens the right page, and the printed page/zone says where to look.

Numbering, where it differs from the vendor's documents:

- The daughterboard (page 4 of the vendor's PDF) reuses designators the main board already has, so its parts are +100 here: its U1 is U101, CN1 is CN101, R5 is R105, and so on.
- The LCD board-to-board connector carries no designator in the print; J6 is ours.
- Nets the vendor left unnamed have names of ours (`U12_EN`, `SCL_ISO`...); `netlist.yaml` lists each with the name Altium generated for it.
- The daughterboard's own net names (`5V_VBUS`, `LED_TX`, `SYS_3V3`...) are drawn with the main board's name of the net they mate with through J2/CN101; `netlist.yaml` lists them under `aliases`.

## Source

M5Stack, *K150 StickS3 schematic, project V0.6 (2025-11-11)*,
<https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1207/K150_Stick_S3_PRJ_V0.6_20251111_2025_11_17_16_10_24.pdf>,
listed on <https://docs.m5stack.com/en/core/StickS3>. The vendor's host did not answer from the machine that drew this on 2026-11-16, so the copy the Wayback Machine captured on 2026-03-08 was read (<https://web.archive.org/web/20260308045411/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1207/K150_Stick_S3_PRJ_V0.6_20251111_2025_11_17_16_10_24.pdf>), SHA-256 `e5272c97bbe52d6937bde89c9c85bfddb7d1d076145e4d2b960ff596c20d0226`.

| Vendor page | Sheet | Its facts are on |
| --- | --- | --- |
| 1 | Block diagram, power network, power modes, I/O map | (read for the part names U15 LGS4056, U16 PY32L020F15U6, U20 ESP32-S3-PICO-1-N8R8) |
| 2 | 03_Power_Management | pages 2, 3, 6 |
| 3 | 04_MUC_Core and Function | pages 4, 5 |
| 4 | StickS3_PRJ_FPC_V1.0_20251125 (daughterboard) | page 6 |

The connections were read off the printed pages and then taken, pin by pin, from the netlist Altium writes into the same PDF's bookmarks (Nets → Pins, per sheet); the two agree everywhere. The values come from the printed pages; U104's rating, 8 ohm at 1 W, is printed on vendor page 1 (`SPK 扬声器8Ω @ 1W`). The vendor's documentation page (read at Switch Science's mirror, `docs.m5stack.switch-science.com/en/core/StickS3`, on 2026-11-16 and 2026-11-17) gives the I2C addresses, the HAT2 header's pinout and the Grove wire colors that the schematic agrees with, J3's part (an HY2.0-4P interface; the print says only `CON4`, which is J3's value here) and LED1's color (green: "hold the power button until the green LED blinks"; the print gives none).

The print does not print the I2C addresses; K9 to K11 take them from the chips' own documents (the M5PM1 manual, the BMI270 and ES8311 datasheets), each against the pins the print ties (the BMI270's SDO and the ES8311's CE), and a bench scan of 2026-11-17 found exactly those three on the bus (`bench/2026-11-17-i2c-scan-l3b.md`).

Other documents read, in full under `source.also_read` in `netlist.yaml` (with the SHA-256 of the file read where it was kept):

- M5PM1 Chip User Manual V1.9 (M5Stack, `github.com/m5stack/M5PM1`, `docs/M5PM1_Datasheet_EN.pdf`): K9.
- ESP32-S3-PICO-1 Series Datasheet v1.2 (Espressif): K2 to K7.
- Bosch BMI270 datasheet BST-BMI270-DS000-08, revision 1.6: K10.
- Everest ES8311 datasheet, revision 10.0: K11.
- Awinic AW329XX (AW32901) datasheet V1.1 (LCSC's copy): K1.
- JCET CJ3439KDW datasheet, revision D (LCSC's copy): Q2's channels and pins, which the drawing agrees with (Q2A N-channel on pins 1 S, 2 G, 6 D; Q2B P-channel on 3 D, 4 S, 5 G).
- Awinic AW8737A datasheet V1.2 (a distributor's copy): U19's D3 PVDD is the charge pump's output (on its own net `U19_PVDD`, as drawn) and A4 ~SHDN a one-wire pulse control, which the printed net name `PYG3_SPK_Pulse` already says.
- Vishay VSOP383.. datasheet, document 82748, revision 1.6: U101's pinning (1, 4, 5 N.C., 2 VS, 3 OUT, 6, 8 GND, 7 IN for an outside photodiode), which the drawing agrees with.
- The bench records in [`bench/`](bench/), from probes run on 2026-11-17 on an open StickS3 (case closed, Kleidos `sticks3_debug` firmware over USB).

## Kleidos additions and corrections

The drawing improves on the vendor's print where a primary source makes a detail certain (AGENTS.md, "Schematics"). Each entry is `kleidos` in `netlist.yaml`, marked in amber where it is drawn and listed on page 1 with its source; [`improvements.md`](improvements.md) is the triage that weighed each candidate, and [`bench/`](bench/) holds the probe records.

| Id | Kind | What | Marked at | Source |
| --- | --- | --- | --- | --- |
| K1 | correction | U7 AW32901FCR trips at its default threshold, 5.95 V rising (5.83 to 6.07 V, 130 mV hysteresis), because OVLO goes to GND through R8 0R and R7 is not fitted. The print writes "OVP = 5V". | page 7, rails table (`5VIN_L0`) | AW329XX datasheet V1.1, p. 1 (default 5.95 V), p. 2 (VIN_OVLO), p. 4 note 2 (OVLO to GND directly or through 0 ohm for the default threshold); not probed (it needs more than 6 V on USB) |
| K2 | addition | GPIO26 (SPICS1, U20 pin 28) is wired inside the N8R8 package to its Octal PSRAM and is not available for other uses. | page 8, ESP32-S3 GPIO table | ESP32-S3-PICO-1 Series Datasheet v1.2, Table 2-1 note 4, p. 13 |
| K3 to K7 | addition | GPIO33 to GPIO37 (U20 pins 38 to 42), the same: in-package Octal PSRAM, not available. One entry each. | page 8, ESP32-S3 GPIO table | as K2 |
| K8 | addition | PYG0 (`PYG0_CHG_STAT`, U15's CHRG with R16 100K up to 3V3_L0) reads 0 while U15 charges the cell and 1 while it does not, with USB in (with no USB in it was not read: the console goes with VBUS). | page 8, M5PM1 GPIO table | bench, [`bench/2026-11-17-charge-status-pyg0.md`](bench/2026-11-17-charge-status-pyg0.md) (2026-11-17): with USB in, PYG0 read 0 in every window where the cell voltage stepped up 30 to 40 mV and VIN dipped about 30 mV, and 1 when charging stopped and at full; no LGS4056 datasheet was found |
| K9 | addition | The M5PM1 U16 answers at I2C address 0x6E. | page 8, I2C table | M5PM1 Chip User Manual V1.9, section I.2 (4), p. 1; seen on the bus by [`bench/2026-11-17-i2c-scan-l3b.md`](bench/2026-11-17-i2c-scan-l3b.md) |
| K10 | addition | The BMI270 U17 answers at 0x68 (SDO, pin 1, on GND) and runs in I2C mode (CSB, pin 12, on 3V3_L1, its VDDIO). | page 8, I2C table | BMI270 datasheet rev 1.6, section 6.5 p. 128, section 6.3 p. 123 and Table 17 p. 122; seen on the bus by the same bench record |
| K11 | addition | The ES8311 U18 answers at 0x18 (CE, pin 20, on AGND), and only while 3V3_L3B_AU is up: it leaves the bus when PYG2 drops L3B and returns with it, and the unpowered codec side does not hold the bus low. | page 8, I2C table | ES8311 datasheet rev 10.0, section 5, p. 8; the same bench record |

GPIO and I2C facts are marked on their row of the nets page, not on a pin, because a `pin` addition draws the pin's wire dotted, as an added connection, and these connections (or the pins' crosses) are printed. Two values also changed with no entry, because the print itself gives them: U104's value carries the rating printed on vendor page 1, and J3's value is the print's `CON4` (it was "CON4 (Grove, HY2.0-4P)", a silent difference from the print).

## Files

| File | What it is | Edited by |
| --- | --- | --- |
| `netlist.yaml` | The facts: every component, its value, the vendor's page, each pin and its net; rails (with their nominal voltage), I2C, ESP32 GPIO map, M5PM1 GPIOs, every pull-up and pull-down; the Kleidos additions and corrections (`kleidos`) and the documents read (`source.also_read`) | hand (review here) |
| `improvements.md` | The triage of every candidate addition or correction, with its evidence and what became of it | hand |
| `bench/` | The records of the bench probes the entries and open questions cite | hand |
| `layout.yaml` | How it is drawn: our symbols, which symbol each part takes, the sheets, blocks and rows, the power tree's boxes and arrows, the revision history | hand |
| `sticks3.kicad_sch` + eight child `.kicad_sch`, `sticks3.kicad_sym`, `sticks3.kicad_pro`, `sym-lib-table` | The KiCad project | generated |
| `links.json` | Where each link of the PDF lands, the named destinations and the bookmarks, for `_shared/schematic_pdf.py` | generated |
| `sticks3.pdf` | The pages | generated |
| `svg/` | One SVG per page, written by the export when it runs; not kept in git | generated |

## Regenerate and check

```bash
.venv/bin/python _shared/kicad_schematic.py sticks3   # KiCad files from netlist.yaml + layout.yaml
.venv/bin/python _shared/export_schematic.py sticks3  # ERC, netlist check, PDF (+ links), SVGs, link check
.venv/bin/python _shared/check_schematic_links.py sticks3 --list   # every link of the PDF and where it lands
.venv/bin/python -m pytest tests/test_schematic.py
```

The generator reads no KiCad library and writes the same files byte for byte from the same inputs. The export needs `kicad-cli` (KiCad 9 or later; drawn with 10.0.8) and runs it with English settings, so the report and the PDF read the same on every machine. It fails unless:

- the ERC reports nothing: 0 errors, 0 warnings. Two checks are switched off in `sticks3.kicad_pro` because the drawing does not depend on them: whether a library is configured for each symbol, and whether a library's symbol differs from the copy the files embed. The drawing carries its own copy of every symbol;
- `check_schematic.py` finds every vendor pin on the net `netlist.yaml` names, no pin missing, no net split or joined, and nothing drawn that the netlist lacks;
- every SVG has the theme's background (kicad-cli falls back to its default theme without a word when it cannot find the one it is given) and every line in the wire color, wires and pin lines alike, has the one width the project sets (6 mil: kicad-cli draws pins at its fixed symbol line width, whatever the project says, so the wires take that width too);
- `check_schematic_links.py` finds every link of the PDF leading where it should: the contents boxes and the page row to their page; every `[page/zone]` within 5 mm of a label of its net on that page, in the zone it prints; every place in the index pages on the part or net its row names; every part's reference to its row in the parts list and the row back to it; every bookmark and named destination on its part or label. Nothing else is clickable, every link says where it leads, and the document holds no script.

## Left out, and why

- Part numbers no vendor document gives: the HAT2 socket J2, the battery connector J4, inductor L2 (only "2.2uH"), the keys S1-S3, the daughterboard's MOSFET Q101, photodiode U102 and speaker U104. J3's part, HY2.0-4P, comes from the docs page and stays in its note and above: no element of the generator can mark a part's value without drawing its printed wires as added.
- LED1's color: the print gives none, the vendor's docs page says green, and the owner saw it green on his unit (2026-11-17; the LED sits inside the case); it stays in LED1's note, not on the drawing, for the same reason as J3's part.
- The panel on J6 (an ST7789P3, 1.14 inch, 135 × 240 by the docs page): J6 is the connector, and the panel is not on the print.
- Internal pull-ups with no part: the M5PM1 enables one on PWR_BTN (pin 7) beside R17 (manual V1.9, Table 1 p. 2 and Table 2 p. 3); U101's output has one to VS (VSOP383.. datasheet, p. 1). No element of the generator draws a pull that has no resistor without dotting a printed wire.
- The ESP32-S3 module's internals (flash, PSRAM, crystal) are inside U20; its SPI flash pins are left unconnected, and GPIO26 and GPIO33-37 are marked as the PSRAM's (K2-K7).
- The vendor PDF's bookmarks also hold a second daughterboard, `StickS3_PRJ_Lite_FPC_V1.0_20251105` (an LED in place of the IR parts), that no page prints; it is not drawn.
- The print's page 1 (its block diagram) names PYG2 "SPK_EN" and PYG1 "L3B_EN" in its audio block and draws a P-channel MOSFET for LCD_BL; its detailed sheets 2 and 3, the Altium netlist and the docs PinMap give PYG2 = the L3B enable, PYG3 = the speaker pulse and Q6 an N-channel 2N7002T. The drawing follows the detailed sheets and does not reproduce page 1, so there is nothing to correct on it.

## Open questions

What is still uncertain stays out of the drawing ([`improvements.md`](improvements.md) gives the evidence of each item by its id):

- **Which daughterboard a unit carries (A10).** B4 read GPIO42 low at idle with GROVE_5V at 5.1 V, which a fitted IR receiver (D6) and the Lite board both give; a TV remote at the IR window, or a meter on HAT2 pin 17, would settle it. The drawing shows the board the vendor prints.
- **LED1's color on the drawing (A5).** The M5PM1 switches it (B2) and it is green, inside the case (the owner's unit, 2026-11-17, in `board.json`); the color is still not marked on the drawing, since no element carries a part's value without dotting its printed wires.
- **3V3_L2's voltage (D9).** No JW5712 datasheet was found to confirm that VSEL1-3 tied high select 3.3 V (the net name says 3V3), and the firmware has no ADC path to the rail; B5 (a multimeter on the HAT2 3V3 pin) did not run. Through the M5PM1's own ADC and the printed dividers, GROVE_5V read 5.10 V with EXT5V on, 5VIN_L0 about 5.2 V on USB and the cell 4.0 to 4.19 V (`bench/2026-11-17-pmic-rails-and-led.md`); BOOST_OUT's printed 5.0 V and the 1.6 V idle level at GPIO42 are not measured.
- **The charger (D8).** No LGS4056 datasheet was found: CHRG's output type, TEMP on GND, and the charge current R12 4.7K sets against the printed 190 mA rest on the print. B3 also saw the charger stop more than once at about 4.03 to 4.05 V, below full; the cause is not known (`bench/2026-11-17-charge-status-pyg0.md`).
- **U16 pin 1 (D5).** The print names it BAT_ADC_EN_OD (open drain); the M5PM1 manual V1.9 calls it a push-pull output (Table 1, p. 2). Two vendor documents disagree on a pad the firmware sets; the drawing keeps the print's name.
- **J6 pins 6 and 8 (F10).** They carry the main I2C bus to the LCD flex. B1 found no device answering there (0x08 to 0x77, panel rail up), but what the flex connects them to is not known.
- **Part numbers and TP7 (A7, A8).** No vendor document names the parts listed under "Left out", and the print's test-point numbering skips TP7.
