# M5StickC Plus2 (K016-P2): schematic

Kleidos boards: the M5StickC Plus2's connectivity in KiCad, documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1 (sources below and in `netlist.yaml`): every part, pin and net of the vendor's published schematic, with the values the vendor prints, laid out with this project's own layout and symbols, plus fifteen details the print leaves out or gets wrong, each settled by a datasheet or a bench probe and marked where it is drawn (below, "Kleidos additions and corrections"). It tells what connects where and how: pull-ups and pull-downs with their values, series parts, the filter and decoupling parts, every rail and what feeds it, and the ESP32 GPIO of every signal.

[`m5stickc-plus2.pdf`](m5stickc-plus2.pdf) has the nine pages, made to be read on a screen and followed by clicking (below); the export also writes one SVG per page into `svg/`, which git does not keep. Both are drawn in the Kleidos dark theme ([`_shared/kicad-theme-kleidos-dark.json`](../../_shared/kicad-theme-kleidos-dark.json)): graphite ground, parts in light grey, connections in cyan.

| Page | Sheet | What is on it |
| --- | --- | --- |
| 1 | Contents | One box per page with what is on it and its main parts, how to read the drawing, the notes (values, DNP, numbering, zones), the Kleidos additions and corrections with their sources, and the revision history |
| 2 | ESP32-PICO-V3-02 | The module, its supply decoupling, the antenna and its matching, reset (EN), the boot strap and pull-ups, the I2C pull-ups, the UART and IR series resistors, buttons A and B |
| 3 | USB, display, buzzer, headers | USB-C with its fuse, CC resistors and ESD diodes, the CH9102F and the DTR/RTS auto-reset, the test pads, the LCD connector and backlight switch, the buzzer, the STICKIO and 4-pin headers, the Grove port, the rails' ESD diodes and bulk capacitors |
| 4 | Power path and charging | The TP4057 charger and the battery, the Q3 and Q4 P-MOSFET switches, the HOLD latch (Q7), the power key and the RTC wake, the battery divider, the red and IR LEDs |
| 5 | Regulators, power-off timer, RTC | The SY7088 5 V boost, the SY8089 3.3 V buck, the GS321 timer that drives the buck's enable, the RTC and its crystal |
| 6 | IMU and microphone | The MPU-6886 and the SPM1423 PDM microphone |
| 7 | Power tree and rails | How power flows from USB-C, the STICKIO 5VIN pin and the battery to every rail; then every rail's nominal voltage, source, enable and where it is drawn |
| 8 | Nets and signals | Every rail and every net drawn on more than one page with the page/zone of its labels; the ESP32 GPIO map, the I2C addresses, the test pads, every pull-up and pull-down |
| 9 | Parts | Every part: its value as printed, what it is, its nets (two-pin parts), whether it is fitted, and where it is drawn |

Pages 7 to 9 are written by the generator from `netlist.yaml`, not drawn by hand: they cannot disagree with the drawing. Pages 2 and 3 hold the vendor's first sheet (SoC), pages 4 and 5 its second (Power), page 6 its third (IMU_MIC).

## What it is not

- Not the vendor's design files. The layout, the blocks and every symbol are this project's: the integrated circuits' and connectors' are each board's own (`m5stickc-plus2.kicad_sym`), and the passive parts, the diodes, the transistors, the switches, the plain connectors, the pads and the ground symbols are this project's generic ones (`kleidos.kicad_sym`, drawn by `_shared/kicad_schematic.py`). No symbol of KiCad's libraries is in these files. No vendor document is in this repository; the sources are cited below.
- Not a PCB design: no footprints, no part numbers beyond the ones the vendor prints, nothing about placement or routing.
- Not more than its sources make certain. Beyond the vendor's print it carries only what a datasheet or a bench probe settles (K1-K15); what is still uncertain is listed under "Open questions" and stays out. The ESP32-PICO-V3-02's symbol carries the 42 pins the vendor draws; the package's other pins, which its datasheet lists as not connected (Table 4), are not drawn. The LCD panel behind the FPC connector, the battery and the 3D antenna are not drawn by the vendor and are not here.

## How to read it

Pins connect by net labels, not by wires. Two pins whose labels carry the same name are on one net, on any page. After a label, each `[3/C4]` names another page that carries the net and the zone of its label there (the border prints columns 1-8 and rows A-F, 50 mm apart): page 3, row C, column 4. Clicking it lands on that label, zoomed in; on a page where the net has several labels, it lands on the one at the part that feeds the rail (`rails.from` in `netlist.yaml`), or else on the first in reading order. A label with none is on its page only. Neighbouring pins of one part on one net share a short bar and one label. A cross on a pin end means the pin is unconnected. An amber `K3` beside a label, a reference, a crossed pin or a table row marks a Kleidos addition or correction; it leads to its row on page 1, and the row back to it. Wires and pin lines are one colour and one width, so a connection reads as one line from the part to its label.

Parts documented as not fitted (value `NC`: C10) carry KiCad's DNP mark: a red cross over the symbol.

In the PDF, each box on the contents page opens its page, and every page carries "Contents" and a row of page numbers above the title block. Each part's reference on the drawing is a link to its row in the parts list, and the row's reference and page/zone lead back to the part. Every place in the index pages (a page/zone, a box of the power tree, a reference in a table) is a link to it. The bookmarks list the pages and, under each, its parts or its tables, each at its place. `_shared/check_schematic_links.py` holds every one of those links (`--list` prints them all).

### In any PDF reader

The PDF holds no script, so it works the same in every reader: a link leads to a page and a position (`/XYZ` at zoom 2), each link carries a `/Contents` saying where it leads, and named destinations open the PDF at a part or at a net's label on a page (`m5stickc-plus2.pdf#nameddest=part-U7`, `m5stickc-plus2.pdf#nameddest=net-VBAT_OUT-p4`). [`sticks3/schematic/README.md`](../../sticks3/schematic/README.md) says how each reader treats them.

Names and numbering, where they differ from the vendor's print:

- Nets the vendor left unnamed have names of ours (`LNA_IN`, `Q4_G`, `BOOST_OUT`...); `netlist.yaml` lists each under `unnamed` with what it is. The vendor's PDF carries no netlist, so there is no machine name to give beside them.
- Five nets carry two vendor labels each, and are drawn under one: `GPI36` (also `GPIO25`: the vendor joins IO25 and IO36 at STICKIO pin 4), `GPIO4` (also `HOLD`), `UTX` (also `RXD`), `URX` (also `TXD`) and `+3.3V` (also the off-page port `+3V3OUT`). `netlist.yaml` lists them under `aliases`.
- U8 keeps the print's pin numbers, which the Gainsil GS321 datasheet V2 (Figure 1, SOT23-5) confirms: 1 IN+, 2 VSS, 3 IN-, 4 OUT, 5 VDD. Its GS321Y variant numbers them otherwise (OUT on pin 1); the print names the GS321.
- Q3 and Q4 are drawn with the generic three-pin P-MOSFET; its D stands for the vendor's pins 1, 2, 5, 6 and 8, its S for pins 4 and 7, its G for pin 3, as the LRC LP3218DT1G datasheet Rev.B (p. 1, pin configuration) numbers the DFN2020-6S: 1, 2, 5, 6 and the drain pad drain, 4 and the source pad source, 3 gate; the print's 8 and 7 are the two pads.
- U2's pins carry the CH9102F's names from its datasheet (K3); the print gives them the CP2104's (6 VDD, 7 REGIN, 10 NC, 11-14 GPIO.3-GPIO.0, 16 VPP, 3 and 4 D+ and D-). Pin numbers and connections are the print's. Q1's two transistors are drawn as two units, A (pins 3, 4, 5) and B (pins 1, 2, 6).
- No value is printed for the test pads JP1-JP5 and for D24; they read `test pad` and `red LED 0603` here (the PDF's part properties call them `test_p` and `红灯 0603`, "red light").
- U4 prints two part numbers, `SGM2578` and below it `WS4622C-4/TR`; the drawing carries `SGM2578` as its value and `netlist.yaml` notes the second.

## Source

M5Stack, *M5StickC Plus2 schematic v0.5* (Altium, three sheets: SoC, Power, IMU_MIC; the PDF's creation date is 2025-10-31), <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/512/Sch_M5StickC_Plus2_v0.5.pdf>, listed on <https://docs.m5stack.com/en/core/StickC-Plus2>. The vendor's host timed out from the machine that drew this on 2026-11-17, so the copy the Wayback Machine captured on 2026-03-18 was read (<https://web.archive.org/web/20260318085629/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/512/Sch_M5StickC_Plus2_v0.5.pdf>), SHA-256 `75017af5c47c7e56904469f032e7d71a63803651a6e8af070d427f125e88e6cd`, the file `board.json` cites as `plus2-schematic`.

| Vendor page | Sheet | Its facts are on |
| --- | --- | --- |
| 1 | SoC | pages 2, 3 |
| 2 | Power | pages 4, 5 |
| 3 | IMU_MIC | page 6 |

Unlike the StickS3's, this PDF carries no netlist: its bookmarks list each part and its pins, not the nets. The connections were read off the printed pages, from the drawing itself: every wire, junction, net label and power port, each pin at the place the PDF's own pin markers put it, and every one of the 438 pins the bookmarks list is on a net here, none left out and none added. The values come from the printed pages, which agree with the PDF's part properties for every part that prints one.

The vendor's documentation page (read at Switch Science's mirror, `docs.m5stack.switch-science.com/en/core/StickC-Plus2`, on 2026-11-17) gives the PinMap the schematic agrees with: buttons A, B and C on G37, G39 and G35, the IR emitter and the red LED on G19, the buzzer on G2, the display on G15, G13, G14, G12, G5 and G27, the microphone on G0 and G34, the IMU and the RTC on G21 and G22. The MPU-6886's I2C address, 0x68, is printed on vendor page 3; the RTC's, 0x51, is not printed anywhere in the vendor's material: it comes from the BM8563 datasheet V1.1 (write address A2h), the RTC the vendor's docs name (the schematic labels it RTC8563), and is K1. A bench scan of 2026-11-17 found only 0x51 and 0x68 on the bus (`bench/2026-11-17-i2c-scan.md`).

Left out, and why: nothing the vendor's schematic draws. What it does not draw stays out unless a primary source makes it certain (the next section); the LCD panel, the battery cell, the antenna's shape and the module's undrawn pins stay out.

## Kleidos additions and corrections

The drawing improves on the vendor's print where a primary source makes a detail certain (AGENTS.md, "Schematics"). Each entry is `kleidos` in `netlist.yaml`, marked in amber where it is drawn and listed on page 1 with its source; `improvements.md` is the triage that weighed each candidate, and `bench/` holds the probe records.

| Id | Kind | What | Marked at | Source |
| --- | --- | --- | --- | --- |
| K1 | addition | The RTC U9 answers at I2C address 0x51 (write A2h, read A3h). | page 8, I2C table | BM8563 datasheet V1.1, p. 1; seen on the bus by `bench/2026-11-17-i2c-scan.md` |
| K2 | addition | `+VDD` is 3.3 V: the CH9102F's own regulator output V3 (pin 6), which also feeds its VIO (pin 5); it is up only while USB feeds VDD5 through D29. | page 7, rails table | CH9102 datasheet 1C, p. 2 pin table and pp. 4-5, power and supply schemes |
| K3 | correction | U2's pins carry the CH9102F's QFN24 names: 3 UD+, 4 UD-, 6 V3, 7 VDD5, 10 ACT#, 11 WAKEUP/GPIO3, 12 TNOW/GPIO2, 13 RXS/GPIO1, 14 TXS/GPIO0, 15 SUSPEND#, 16 GPIO4. The print gives them the CP2104's names on a part labelled CH9102F. | page 3, U2's reference | CH9102 datasheet 1C, pp. 2-4, pin definitions |
| K4 | addition | U2 RST (pin 9) has a built-in pull-up, beside R14. | page 3, `CH9102_RST` labels | CH9102 datasheet 1C, p. 3 |
| K5 | addition | U2 RXD (pin 20, net `UTX`) has a built-in pull-up. | pages 2 and 3, `UTX` labels | CH9102 datasheet 1C, p. 3 |
| K6 | addition | U2 VBUS (pin 8) has a built-in pull-down. | page 3, `CH9102_VBUS` labels | CH9102 datasheet 1C, p. 3 |
| K7 | addition | `VDD_SDIO` (U1 pin 26) is an output: VDD3P3_RTC through about 6 ohm, 3.3 V, for the in-package flash and PSRAM, which are 3.3 V parts. | page 2, `VDD_SDIO` labels | ESP32-PICO Series Datasheet v1.5, Table 4 p. 19, Table 17 note p. 37, Figure 12 note p. 53 |
| K8 | addition | U1 pin 28 (SD2/IO9) is the in-package PSRAM's CS. | page 2, beside the pin's cross | ESP32-PICO Series Datasheet v1.5, Table 5 p. 21 |
| K9 | addition | U1 pin 29 (SD3/IO10) is the in-package PSRAM's CLK. | page 2, beside the pin's cross | as K8 |
| K10 | addition | U1 pin 30 (CMD/IO11) is the in-package flash's CS. | page 2, beside the pin's cross | as K8 |
| K11 | addition | U1 pin 31 (CLK/IO6) is the in-package flash's CLK. | page 2, beside the pin's cross | as K8 |
| K12 | addition | GPIO12 is the MTDI strap, with an internal pull-down; it must be low at reset so that VDD_SDIO comes up at 3.3 V for the in-package flash and PSRAM. | page 8, GPIO table | ESP32-PICO Series Datasheet v1.5, Table 8 p. 23, §3.2 p. 25, Figure 12 note p. 53 |
| K13 | addition | GPIO36 is input only with no internal pull, and no resistor on the board pulls `GPI36` (STICKIO pin 4, joined with GPIO25). | page 8, GPIO table | ESP32-PICO Series Datasheet v1.5, notes to Table 4 p. 18; the netlist (D6, P1.4, U1.5, U1.14 only) |
| K14 | addition | `INT` is the RTC's open-drain, active-low output; R23 pulls it up to `+VIN`. | pages 4 and 5, `INT` labels | BM8563 datasheet V1.1, p. 2 pin table (pin 3) |
| K15 | addition | `GPIO15` (LCD connector pin 4, printed MOSI) is the panel's bidirectional data line: the panel answers register reads on it. | pages 2 and 3, `GPIO15` labels | bench, `bench/2026-11-17-panel-readback-spird.md` (2026-11-17): ST7789 IDs `0x85 0x85 0x52`, RDDPM `0x9C`, MADCTL `0x08` read back on that line, each byte one bit late |

Facts that are pins or nets the print already connects are marked on their labels (an element `net`), not on the pin, so no printed wire is drawn dotted as if it were added. The datasheets read for them are cited in full under `source.also_read` in `netlist.yaml` and in `improvements.md`, each with the SHA-256 of the file read.

## Open questions

What is still uncertain stays out of the drawing (`improvements.md` gives the evidence of each item, I1-I27):

- **What holds MTDI low at reset (I8).** The datasheet requires MTDI (GPIO12) low at reset for the 3.3 V in-package flash and PSRAM (K12), and the board boots from them, so VDD_SDIO does come up at 3.3 V. Whether the strap's own pull-down does it alone is not settled: GPIO12 reaches only the LCD's RST pin, and what the panel puts on that input is not documented; an eFuse could also set VDD_SDIO. The ROM's boot line (`boot:0x..`), or the strap register read on the bench, would settle it.
- **U4's EN pull-down (I12).** The SGM2578 has an internal pull-down on EN (560 kohm typical) and a discharge on VOUT; the print also names a WS4622C-4/TR under it, whose datasheet was not read, and which one is fitted is not printed. Not added.
- **The rails' measured values (I17).** `+3.3V` from the SY8089's feedback divider (R32 68K / R33 15K) is about 3.32 V if its reference is 0.6 V, which the SY8089 datasheet was not read for; `+5VOUT` is the boost's printed 5.3 V less D20's drop. Probe B3 (a multimeter at the STICKIO header) did not run: no instrument on the bench is wired to this board.
- **The charge current (I18).** R26 3.3 kohm on the TP4057's PROG gives about 300 mA by the common TP4057 formula, but the print names no maker and TP4057 datasheets differ. Probe B6 (a USB power meter) did not run.
- **The board switched off (I21, I24).** That `+5VOUT` falls with `VBAT_OUT`, and that the GPI38 divider R40 / R41 draws about 18 µA from the cell with the board off, rest on the print only; probe B4 (switched off on battery, header pins on a meter) and B5 (the 6 s hold of the power key) did not run.
- **The P1 pin 1 ground symbol (I22).** The print draws it over the pin 2 (`+5VOUT`) wire with no junction; the netlist reads them apart, as a working 5 V output on the header requires. Probe B3 would corroborate it; it did not run.
- **The MPU-6886's undrawn pads (I14).** Its datasheet disagrees with itself on pins 19-21, and the pads sit under the LGA. Not drawn.
- **The microphone's SELECT (I16).** Which clock edge SELECT low picks is in the SPM1423 datasheet's image tables, not its text. Not added.
- **Q1's pinout (I26).** The print's numbering matches the usual SOT-363 dual NPN, but the LRC LMBT3904DW1T1G datasheet was not read. The print's numbers stand, unmarked.
- **The LCD panel, the cell and the antenna's shape (I27).** In no vendor document read.
- **The package's no-connect pins (I7).** The ESP32-PICO datasheet lists pins 25, 35, 36, 44, 45, 47 and 48 as not connected; the vendor's symbol leaves them out and so does this one (settled, low value, not drawn).

## Files

| File | What it is | Edited by |
| --- | --- | --- |
| `netlist.yaml` | The facts: every component, its value, the vendor's page, each pin and its net; rails (with their nominal voltage), I2C, ESP32 GPIO map, every pull-up and pull-down | hand (review here) |
| `layout.yaml` | How it is drawn: our symbols, which symbol each part takes, the sheets, blocks and rows, the power tree's boxes and arrows, the revision history | hand |
| `m5stickc-plus2.kicad_sch` + eight child `.kicad_sch`, `m5stickc-plus2.kicad_sym`, `m5stickc-plus2.kicad_pro`, `sym-lib-table` | The KiCad project | generated |
| `links.json` | Where each link of the PDF lands, the named destinations and the bookmarks, for `_shared/schematic_pdf.py` | generated |
| `m5stickc-plus2.pdf` | The pages | generated |
| `svg/` | One SVG per page, written by the export when it runs; not kept in git | generated |

## Regenerate and check

```bash
.venv/bin/python _shared/kicad_schematic.py m5stickc-plus2   # KiCad files from netlist.yaml + layout.yaml
.venv/bin/python _shared/export_schematic.py m5stickc-plus2  # ERC, netlist check, PDF (+ links), SVGs, link check
.venv/bin/python _shared/check_schematic_links.py m5stickc-plus2 --list   # every link of the PDF and where it lands
.venv/bin/python -m pytest tests/test_schematic.py
```

The export fails unless the ERC reports nothing, `check_schematic.py` finds every vendor pin on the net `netlist.yaml` names, every SVG has the theme's background and one line width for wires and pin lines, and `check_schematic_links.py` finds every link of the PDF leading where it should ([`sticks3/schematic/README.md`](../../sticks3/schematic/README.md) says each check in full).
