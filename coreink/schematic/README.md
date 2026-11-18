# M5Stack CoreInk (K048): schematic

Kleidos boards: the CoreInk's connectivity in KiCad, documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1 (sources below and in `netlist.yaml`): every part, pin and net, with the values the vendor documents, laid out with this project's own layout and symbols. It tells what connects where and how: pull-ups and pull-downs with their values, series parts, the filter and decoupling parts on each interface, every rail and what feeds it, and the ESP32-PICO-D4 GPIO of every signal.

[`coreink.pdf`](coreink.pdf) has the eight pages, made to be read on a screen and followed by clicking (below); the export also writes one SVG per page into `svg/`, which git does not keep. Both are drawn in the Kleidos dark theme ([`_shared/kicad-theme-kleidos-dark.json`](../../_shared/kicad-theme-kleidos-dark.json)): graphite ground, parts in light grey, connections in cyan.

| Page | Sheet | What is on it |
| --- | --- | --- |
| 1 | Contents | One box per page with what is on it and its main parts, how to read the drawing, the notes (values, numbering, zones), the Kleidos additions and corrections with their sources, and the revision history |
| 2 | ESP32-PICO-D4 and USB | The ESP32-PICO-D4 with its decoupling, the antenna's pi network, the antenna and the IPEX connector, the I2C pull-ups; the USB-C receptacle, the CP2104 USB to UART bridge and the auto-reset transistors |
| 3 | Power | The 5 V inputs and their diodes, the PTC fuse, the charger and its LED, the battery connector, the battery switch and power hold, the battery voltage divider, the SY7088 5 V boost and the SY8089 3.3 V buck |
| 4 | E-paper and expansion | The panel's 24-pin connector with its capacitors and the gate-voltage booster (VGG, VEE); the M5-Bus socket, the FPC to the HAT board, the Grove port, the ESD arrays and the 47R series resistors |
| 5 | Keys, RTC and buzzer | The power and reset keys, the three-way dial, the BM8563 with its crystal and alarm diodes, the buzzer and its driver |
| 6 | Power tree and rails | How power flows from the USB-C, the M5-Bus and HAT inputs and the battery to every rail, with each part's enable; then every rail's nominal voltage, source, enable and where it is drawn |
| 7 | Nets and signals | Every rail and every net drawn on more than one page with the page/zone of its labels; the ESP32-PICO-D4 GPIO map, the I2C address, every pull-up and pull-down |
| 8 | Parts | Every part: its value as printed, what it is, its nets (two-pin parts), whether it is fitted, and where it is drawn |

Pages 6 to 8 are written by the generator from `netlist.yaml`, not drawn by hand: they cannot disagree with the drawing. The vendor prints the whole board on one page in titled blocks; the four drawn pages group those blocks by function, and each block keeps the vendor's name in `netlist.yaml` (`block`).

## What it is not

- Not the vendor's design files. The layout, the blocks and every symbol are this project's: the integrated circuits' and connectors' are each board's own (`coreink.kicad_sym`), and the passive parts, the diodes, the transistors, the switches, the plain connectors, the pads and the ground symbols are this project's generic ones (`kleidos.kicad_sym`, drawn by `_shared/kicad_schematic.py`). No symbol of KiCad's libraries is in these files. No vendor document is in this repository; the sources are cited below.
- Not a PCB design: no footprints, no part numbers beyond the ones the vendor prints, nothing about placement or routing.
- Not a full datasheet of each part: pin names and values are as the vendor documents them (`10K/1%`, `105/6.3V`, `47UF/6.3V`); the datasheet facts the drawing adds are the Kleidos additions below, each marked.
- Not limited to what the vendor's print shows: where a primary source makes a detail certain that the print leaves out, the drawing adds it, marked by its id in amber and listed on page 1 ("Kleidos additions and corrections", below).

## How to read it

Pins connect by net labels, not by wires. Two pins whose labels carry the same name are on one net, on any page. After a label, each `[3/C4]` names another page that carries the net and the zone of its label there (the border prints columns 1-8 and rows A-F, 50 mm apart): page 3, row C, column 4. Clicking it lands on that label, zoomed in; on a page where the net has several labels, it lands on the one at the part that feeds the rail (`rails.from` in `netlist.yaml`), or else on the first in reading order. A label with none is on its page only. Neighbouring pins of one part on one net share a short bar and one label. A cross on a pin end means the pin is unconnected. An amber `K1`... beside a pin, a label or a table row marks a Kleidos addition or correction and leads to its row on page 1; an added connection is drawn dotted (none of the CoreInk's 28 entries adds a wire). Wires and pin lines are one colour and one width, so a connection reads as one line from the part to its label.

No part on the vendor's print is marked not fitted, so no part carries KiCad's DNP mark.

In the PDF, each box on the contents page opens its page, and every page carries "Contents" and a row of page numbers above the title block. Each part's reference on the drawing is a link to its row in the parts list, and the row's reference and page/zone lead back to the part. Every place in the index pages (a page/zone, a box of the power tree, a reference in a table) is a link to it. The bookmarks list the pages and, under each, its parts or its tables, each at its place. `_shared/check_schematic_links.py` holds every one of those links (`--list` prints them all).

### In any PDF reader

KiCad can give each part a property pop-up, but it is a script that only Acrobat runs, so the export leaves the pop-ups out and the PDF holds no script at all. What they showed (reference, value) and more is in the parts list, which any reader, and paper, can use. The rest is plain PDF that every reader follows:

- a link leads to a page and a position: `/XYZ`, the target placed 30 mm from the window's left edge and 20 mm below its top, at zoom 2. KiCad links a text only to a whole page, so `_shared/schematic_pdf.py` sends each link to its place after the export, from the targets the generator writes into `links.json`;
- each link carries a `/Contents` saying where it leads, for screen readers;
- named destinations open the PDF at a part or at a net's label on a page, from a web page or another document: `coreink.pdf#nameddest=part-U1`, `coreink.pdf#nameddest=net-MCU_VDD-p3`.

Numbering and names, where they differ from the vendor's print:

- Reference designators are the vendor's; nothing is renumbered.
- The print gives many parts no pin numbers: the two-pin passives, the diodes, the transistors, the keys, the crystal, the fuse, the antennas, the buzzer, and the USB-C's VCC, GND and SHELL pins. Their pin names here are ours: `1`/`2` for a two-pin part, `A`/`K` for a diode, `B`/`C`/`E` and `G`/`S`/`D` for the transistors as their symbols draw them, `V`/`G`/`SH` for the USB-C's three unnumbered pins. Each part's `note` in `netlist.yaml` says which end is which where it matters.
- BZ1's symbol has three pins and no numbers: `1` is the one marked `+`, `2` the other end of the coil, `3` the pin drawn on the front of the symbol, which goes to GND.
- Nets the vendor left unnamed have names of ours (`U5_FB`, `EPD_SW`, `VBAT_SW`...); `netlist.yaml` lists each under `named_here` with where it is.
- ANT1 has no value on the print; it reads `(no value printed)`. S1's value on the print is Chinese text describing a side-press switch; it reads `SW (side, POWER)` here, POWER being the print's label beside it.

## Source

M5Stack, *CoreInk schematic*, one page, `coreink_sch.pdf` (no version or date on the sheet; the PDF was written on 2020-07-22), <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/schematic/Core/coreink/coreink_sch.pdf>, listed on <https://docs.m5stack.com/en/core/CoreInk>. The vendor's host did not answer from the machine that drew this, so the Internet Archive's copy of 2025-10-17 was read (<https://web.archive.org/web/20251017235233id_/https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/schematic/Core/coreink/coreink_sch.pdf>), SHA-256 `182ea9c6e90bdc7696aacb26db054a1f4125f7640aa505e3d9a2301163e334b5`, the same file `board.json` cites. The vendor's own CDN serves the same file, with the same SHA-256 (<https://static-cdn.m5stack.com/resource/docs/schematic/Core/coreink/coreink_sch.pdf>, checked 2026-11-17). It is the only schematic the vendor publishes for the CoreInk: the docs page's schematic section links this PDF and shows two images, the same sheet and a block diagram (<https://static-cdn.m5stack.com/resource/docs/products/core/coreink/coreink_sch_01.webp>), and the vendor's hardware repository holds only the case files for K048.

| Vendor block (page 1) | Drawn on |
| --- | --- |
| ESP32-PICO-D4 (untitled), USB TYPE-C, USB2UART | page 2 |
| PMU, CHARGER, PWR_SW&ADC, BATTERY PORT, 5V DC-DC, 3.3V DC-DC | page 3 |
| E-paper connector (untitled), EPD BOOST, BUS, FPC TO HAT, GROVE, ESD | page 4 |
| BUTTONS, RTC, BUZZER | page 5 |

The print is an Altium sheet printed to PDF, with no netlist in it. The connections were read off the page block by block, and each wire was followed on the page's vector drawing as well as by eye; every numbered pin of the integrated circuits, the M5-Bus, the Grove and the panel connector was then checked by script against the wire it touches on that drawing; J1, J2 and J4 (whose numbers sit inside or beside the body) and the two-pin parts were checked by following each wire to its label or port. The values come from the printed page. The docs page (read at Switch Science's mirror, `docs.m5stack.switch-science.com/en/core/CoreInk`) gave the roles of the dial, the user button, the LED, the buzzer and the power hold in its PinMap, the battery (390mAh @ 3.7V), the input (5V @ 500mA) and the two USB-UART versions. What the print does not show and a primary source makes certain is drawn as a Kleidos addition, listed below and on page 1. Those sources: Espressif's *ESP32-PICO Series Datasheet* v1.5 (<https://www.espressif.com/sites/default/files/documentation/esp32-pico_series_datasheet_en.pdf>, read 2026-11-17: Tables 2, 3 and 8, Section 3.2), the BM8563 datasheet V1.1 and the SY7088 datasheet as M5Stack hosts them (the Internet Archive's copies, as `board.json` cites them), the docs page above, ESP-IDF's *Sleep Modes* page for the ESP32 (which GPIOs can wake deep sleep), the Kleidos firmware repository, and the bench records in [`bench/`](bench/) (2026-11-17: the bench unit's USB descriptor, the LED and user-key pins read through the firmware's debug console).

One reading needs saying: the GND symbol on BUS1 pin 1 is drawn with its longest bar touching the wire of pin 3 (5VIN). A power symbol connects only at its own end, and pin 3 carries the EXT_5VI port, so pin 3 is drawn on EXT_5VI, as `board.json` has it. It is not yet marked as a correction: a bench reading of pin 3 settles it (Open questions).

## Kleidos additions and corrections

The drawing improves on the vendor's print where a primary source makes a detail certain (AGENTS.md, "Schematics"). Each entry is in `kleidos` in `netlist.yaml`, marked on the drawing by its id in amber and listed with its source on page 1; the triage of every candidate, settled or not, is [`improvements.md`](improvements.md). There are 29, all additions; no drawing error of the print is corrected yet (the one candidate, BUS1 pin 3, waits for the bench).

| Ids | What is added | Source |
| --- | --- | --- |
| K1-K4 | U1 pins 44 (XTAL_N_NC), 45 (XTAL_P_NC), 47 (CAP2_NC) and 48 (CAP1_NC), which the vendor's symbol leaves out, drawn unconnected | ESP32-PICO Series Datasheet v1.5 (Espressif), Table 2, p. 15: each "NC" |
| K5, K6, K13 | GPIO0, GPIO2 and GPIO15 (MTDO) are strapping pins: pulled up, down and up at reset | the same datasheet, Table 8, p. 23 |
| K7 | GPIO5 (the user key, beyond J1) is a strapping pin: pulled up at reset | the same datasheet, Table 8, p. 23 |
| K8-K11, K14, K15 | GPIO6 (CLK), GPIO7 (SD0), GPIO8 (SD1), GPIO11 (CMD), GPIO16 and GPIO17, crossed on the print, are the in-package flash's CLK, WP/SIO2, SI/SIO0, HOLD/SIO3, CS and SO/SIO1 | datasheet, Table 3, p. 16 |
| K12 | GPIO12 is the MTDI strap: pulled down at reset, which feeds VDD_SDIO (the in-package flash's supply) straight from VDD3P3_RTC, here MCU_VDD; D14's anode on GPIO12 keeps the USB hold path off the strap | datasheet, Table 8, p. 23 and Section 3.2, p. 25 |
| K16 | GPIO19 (the RTC alarm) is not an RTC GPIO, so the alarm cannot wake the ESP32 from deep sleep; on battery it switches the board on through D13 instead | datasheet, Table 2, p. 15 (no RTC_GPIO function); ESP-IDF *Sleep Modes* (Espressif, <https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/sleep_modes.html>): the ext0 and ext1 deep-sleep wake sources take RTC GPIOs only; firmware `variants/m5core_ink/variant.h` (the comment above `BOARD_SLEEP_MODE`) |
| K17 | GPIO23 (EPD MOSI) also carries the panel's reads: the SSD1681 answers register and RAM reads on SDA, half-duplex three-wire (shown for the SSD1681 panel; the earlier GDEW0154M09 was not read) | Kleidos firmware `src/hal/display/epaper_panel_driver.cpp` (`EpaperPanelDriver::makePanelReadDevice`, `EpaperPanelDriver::readPanelRegister`), `src/hal/display/display_hal_epaper.cpp` (`readPanelRegister`); the panel RAM read back over SDA on the board (the Kleidos firmware, 2026-07-14) and the controller's identity, SSD1681, on 2026-07-15 |
| K18 | GPIO27 (power key) is RTC_GPIO17, so it can wake the ESP32 from deep sleep (the firmware arms it as EXT0 on USB power) | datasheet, Table 2, p. 14; ESP-IDF *Sleep Modes* (ext0 takes an RTC GPIO); firmware `src/hal/common/power_manager_core_ink.cpp` (`PowerManagerCoreInk::enterDeepSleep`) |
| K19-K24 | GPIO34 to GPIO39 are input only, with no internal pull (GPIO35 is ADC1_CH7) | datasheet, Table 2, pp. 13-14, and its notes |
| K25 | The BM8563 U4 answers at I2C address 0x51 | BM8563 datasheet V1.1 (write A2h, read A3h); firmware `src/drivers/rtc/bm8563_regs.h` (`kI2cAddress`) |
| K26 | SYS_P050 is 5.03 V: 1.2 V x (1 + 15K / 4.7K) | SY7088 datasheet, VOUT equation (computed; P03 would confirm it at EXT_5VO) |
| K27, K28 | USB_5V is the 5 V @ 500 mA input, SYS_BAT the 390 mAh 3.7 V cell | the docs page's specification table |
| K29 | The status LED GPIO10 drives through J1 pin 1 is green and lit when GPIO10 is low (the LED and its resistor, beyond J1, are not drawn) | bench record [`bench/2026-11-17-led-and-user-key.md`](bench/2026-11-17-led-and-user-key.md): the firmware's LED-on command drives GPIO10 low (`variants/m5core_ink/variant.h` (`PIN_STATUS_LED`, `STATUS_LED_ACTIVE_LOW`), `src/hal/common/peripheral_switch.cpp` (`makeBoardCaps`)) and the owner saw the LED lit, green, on his unit, 2026-11-17 |

Firmware citations are the Kleidos firmware repository (2026-11-17), code that runs on the CoreInk.

## Files

| File | What it is | Edited by |
| --- | --- | --- |
| `netlist.yaml` | The facts: every component, its value, the vendor's block, each pin and its net; rails (with their nominal voltage), I2C, the ESP32 GPIO map, every pull-up and pull-down; the Kleidos additions (`kleidos`) with their sources | hand (review here) |
| `improvements.md` | The triage of every candidate addition or correction, with its evidence and status, and the bench probes | hand |
| `bench/` | The bench records the entries and the open questions cite | hand |
| `layout.yaml` | How it is drawn: our symbols, which symbol each part takes, the sheets, blocks and rows, the power tree's boxes and arrows, the revision history | hand |
| `coreink.kicad_sch` + seven child `.kicad_sch`, `coreink.kicad_sym`, `coreink.kicad_pro`, `sym-lib-table` | The KiCad project | generated |
| `links.json` | Where each link of the PDF lands, the named destinations and the bookmarks, for `_shared/schematic_pdf.py` | generated |
| `coreink.pdf` | The pages | generated |
| `svg/` | One SVG per page, written by the export when it runs; not kept in git | generated |

## Regenerate and check

```bash
.venv/bin/python _shared/kicad_schematic.py coreink   # KiCad files from netlist.yaml + layout.yaml
.venv/bin/python _shared/export_schematic.py coreink  # ERC, netlist check, PDF (+ links), SVGs, link check
.venv/bin/python _shared/check_schematic_links.py coreink --list   # every link of the PDF and where it lands
.venv/bin/python -m pytest tests/test_schematic.py
```

The export fails unless the ERC reports nothing (0 errors, 0 warnings), `check_schematic.py` finds every vendor pin on the net `netlist.yaml` names with no pin missing and no net split or joined, every SVG has the theme's background and one width for every line in the wire colour, and `check_schematic_links.py` finds every link of the PDF leading where it should and no script in the document. [The StickS3's schematic README](../../sticks3/schematic/README.md) describes each check in more detail.

## Open questions

What is still uncertain stays off the drawing. Each item names what would settle it; the ids are those of [`improvements.md`](improvements.md).

- **BUS1 pin 3 (T12, T31).** The GND symbol of pin 1 touches pin 3's wire on the print; pin 3 is drawn on EXT_5VI, which the bench unit's charging and enumerating on USB already argues for. A multimeter on the back M5-Bus socket (P01: about 4.5-4.8 V on pin 3 with USB in, no short to pin 1 unpowered) would make it a marked correction. Not run on 2026-11-17: it needs a person with a meter at the bench.
- **MCU_VDD's value (T25).** 0.6 V x (1 + 22K / 5.1K) = 3.19 V if the SY8089's feedback reference is 0.6 V; the SY8089 datasheet was not read, and P02 (M5-Bus pin 6 to pin 1) did not run. The drawing keeps the print's block title, 3.3 V.
- **EXT_5VO on the bench (T26).** K26 is computed from the SY7088 datasheet; P03 (M5-Bus pin 4 on battery, about 4.6-4.8 V after D11) did not run.
- **The charger (T03).** The print writes "TP40P57", the vendor's block diagram "TP4057". Once the TP4057 datasheet's SOT-23-6 pinout is read against the print's pin names it becomes a correction, with the charge current R45 sets; the drawing keeps the print's name until then.
- **The user LED's own parts (T04).** The LED's colour and polarity are settled and drawn (K29, on the GPIO10 row). The LED and its resistor sit beyond J1, on the HAT board, off the print: which parts they are, and which rail feeds the LED, is not shown anywhere and stays out.
- **The user key beyond J1 (T05).** The firmware reads it active low on the ESP32's internal pull-up (`src/boards/board_m5core_ink.cpp` (`s_btnLock`)), and on 2026-11-17 the pad read high with the key released and the internal pull-up on (P05, [`bench/2026-11-17-led-and-user-key.md`](bench/2026-11-17-led-and-user-key.md)); no record shows it read low with the key held, so "active low" is not drawn. The pressed half of P05 (someone holding the top key while `GPIO? 5` runs) would make it an addition. Whether the HAT board fits a pull of its own cannot show while the internal pull-up is on.
- **The USB to UART bridge (T06).** The docs say later units carry a CH9102; the bench unit enumerates as WCH `1a86:55d4`, a CH9102 ([`bench/2026-11-17-usb-descriptor.md`](bench/2026-11-17-usb-descriptor.md)). No circuit for the CH9102 version is published, so the drawing keeps the print's CP2104.
- **U2 pin 10 (T24).** The CP2104's pin 10 is not on the vendor's symbol; the CP2104 datasheet (not read in this pass) would make it an addition.
- **The panel (T07, T08, T30).** The connector's symbol is named EPD_SPI and names no panel; the docs say M5Stack changed the panel from GDEW0154M09 to GDEY0154D67 on 2024-10-25, after this PDF was written. The symbol has no pin 1: the GDEY0154D67's pin 1 is NC on the panel, but what the board's pad 1 carries is not shown, so it is not drawn. The symbol's VGL and VGH (pins 4, 5) are NC and VSH2 on the GDEY0154D67.
- **Part numbers the print leaves out (T09).** ANT1 (no value), the USB-C receptacle J2 (only "TYPEC"), J1 (only "CON10"), J4 (only "CON2"), the inductors (values only), the keys S1 and S2 beyond S2's "PTS_820_H2.5mm", the fuse FU1 ("PTC 1A") and the crystal X1 ("32.768K"). They need the board opened.
- **ANT1 and ANT2 (T10).** The print draws the antenna and the IPEX connector on one feed and marks neither not fitted; whether a unit carries both is not known.
- **Which version of the board a unit is (T11).** The vendor gives two changes (USB-UART, panel) and no revision mark; the drawing shows the one the vendor prints.
- **Crossings without a dot (T32).** The print was not re-read in this pass for wires that cross a bar or a rail with no junction dot.
- **The GPIO roles from the docs (T27).** The roles the docs' PinMap gives (dial up, press and down on GPIO37 to GPIO39, the power hold on GPIO12) are in the GPIO rows unmarked, as before; whether such vendor-document facts are marked on every board is one decision for all nine. The rails' facts from the docs are marked (K27, K28).
- **Facts with no element to mark (T28, T29).** The BM8563 ~INT is open drain, active low, and EPD1 BS1 on GND selects 4-wire SPI; both are datasheet facts about a pin whose net the print already shows, and `board.json` carries them.
