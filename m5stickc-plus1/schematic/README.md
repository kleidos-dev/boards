# M5StickC Plus 1.1 (K016-P): schematic

Kleidos boards: the M5StickC Plus 1.1's connectivity in KiCad, documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1 (sources below and in `netlist.yaml`): every part, pin and net, with the values the vendor documents, laid out with this project's own layout and symbols. Where a datasheet, the vendor's docs page or a bench probe makes a detail certain that the print leaves out or gets wrong, the drawing carries it, marked and sourced ([below](#kleidos-additions-and-corrections)); what is still uncertain is listed under [Open questions](#open-questions). It tells what connects where and how: pull-ups and pull-downs with their values, series parts, the decoupling and ESD parts on each interface, every rail and what feeds it, and the ESP32 GPIO of every signal.

[`m5stickc-plus1.pdf`](m5stickc-plus1.pdf) has the eight pages, made to be read on a screen and followed by clicking (below); the export also writes one SVG per page into `svg/`, which git does not keep. Both are drawn in the Kleidos dark theme ([`_shared/kicad-theme-kleidos-dark.json`](../../_shared/kicad-theme-kleidos-dark.json)): graphite ground, parts in light grey, connections in cyan.

| Page | Sheet | What is on it |
| --- | --- | --- |
| 1 | Contents | One box per page with what is on it and its main parts, how to read the drawing, the notes (values, numbering, zones), the Kleidos additions and corrections with their sources, and the revision history |
| 2 | Power management | The AXP192 with its inputs (USB-C VBUS, the VIN pad, the battery, the backup cell) and its DC-DC and LDO outputs; the power key with the RTC wake-up coupling; the SGM6603 5 V boost for the Grove port and the 5VOUT pad |
| 3 | ESP32-PICO-D4 | The ESP32-PICO-D4 with its supply decoupling, RF path and antenna, the enable and GPIO0 pull-ups, the I2C and interrupt pull-ups, buttons A and B, the IR and red LEDs |
| 4 | USB and serial bridge | The USB-C receptacle with its CC resistors and ESD diodes, the CH552T USB-serial bridge, the UART series resistors, the two MOSFETs that drive EN and GPIO0 |
| 5 | Sensors, display and connectors | The MPU6886, the BM8563 and its crystal, the LCD panel's connection, the microphone, the Grove port, the ten pads with their series resistors and ESD diodes |
| 6 | Power tree and rails | How power flows from the USB-C, the VIN pad, the battery and the backup cell through the AXP192 to every rail; then every rail's nominal voltage, source, enable and where it is drawn |
| 7 | Nets and signals | Every rail and every net drawn on more than one page with the page/zone of its labels; the ESP32-PICO-D4 and AXP192 GPIO maps, the I2C addresses, the ten pads with their printed names, every pull-up and pull-down |
| 8 | Parts | Every part: its value as printed, what it is, its nets (two-pin parts) and where it is drawn |

Pages 6 to 8 are written by the generator from `netlist.yaml`, not drawn by hand: they cannot disagree with the drawing.

## What it is not

- Not the vendor's design files. The layout, the blocks and every symbol are this project's: the integrated circuits' and connectors' are each board's own (`m5stickc-plus1.kicad_sym`), and the passive parts, the diodes, the transistors, the switches, the plain connectors, the pads and the ground symbols are this project's generic ones (`kleidos.kicad_sym`, drawn by `_shared/kicad_schematic.py`). No symbol of KiCad's libraries is in these files. No vendor document is in this repository; the sources are cited below.
- Not a PCB design: no footprints, no part numbers beyond the ones the vendor prints, nothing about placement or routing.
- Not a full datasheet of each part: pin names and values are as the vendor documents them (`5.1K`, `100uF/4V`, `ESD/3.3V`).

## How to read it

Pins connect by net labels, not by wires. Two pins whose labels carry the same name are on one net, on any page. After a label, each `[3/A2]` names another page that carries the net and the zone of its label there (the border prints columns 1-8 and rows A-F, 50 mm apart): page 3, row A, column 2. Clicking it lands on that label, zoomed in; on a page where the net has several labels, it lands on the one at the part that feeds the rail (`rails.from` in `netlist.yaml`), or else on the first in reading order. A label with none is on its page only. Neighbouring pins of one part on one net share a short bar and one label. A cross on a pin end means the pin is unconnected. Wires and pin lines are one colour and one width, so a connection reads as one line from the part to its label. An amber `K5` beside a label, a crossed pin or a row of the nets page marks a Kleidos addition or correction; it leads to its row on page 1, and the row's id leads back. Every entry here marks a fact about a connection the print already draws (or a pin it leaves unconnected), so no wire is dotted as an added connection.

The schematic documents no part as not fitted, so no part carries KiCad's DNP mark.

In the PDF, each box on the contents page opens its page, and every page carries "Contents" and a row of page numbers above the title block. Each part's reference on the drawing is a link to its row in the parts list, and the row's reference and page/zone lead back to the part. Every place in the index pages (a page/zone, a box of the power tree, a reference in a table) is a link to it. The bookmarks list the pages and, under each, its parts or its tables, each at its place. `_shared/check_schematic_links.py` holds every one of those links (`--list` prints them all).

### In any PDF reader

The PDF holds no script: KiCad's property pop-ups are a script only Acrobat runs, so the export leaves them out; the parts list holds what they showed. The rest is plain PDF that every reader follows:

- a link leads to a page and a position: `/XYZ`, the target placed 30 mm from the window's left edge and 20 mm below its top, at zoom 2. KiCad links a text only to a whole page, so `_shared/schematic_pdf.py` sends each link to its place after the export, from the targets the generator writes into `links.json`;
- each link carries a `/Contents` saying where it leads, for screen readers;
- named destinations open the PDF at a part or at a net's label on a page, from a web page or another document: `m5stickc-plus1.pdf#nameddest=part-U2`, `m5stickc-plus1.pdf#nameddest=net-VESP_3V3-p3`.

Numbering and names, where they differ from the vendor's print:

- The print leaves the ESP32-PICO-D4 unannotated (`U?`, value `PICO_D4`); it is U1 here, its value kept as printed (`PICO_D4`) and its symbol named after the docs page (`ESP32-PICO-D4`). The battery connector carries no designator (only the label `Li_Ion`); it is J3 here.
- The USB-C receptacle's pins VBUS, GND and SHELL are drawn as V, G and SH, so the pin numbers fit beside the body; `layout.yaml` maps them back and the netlist check holds them to the vendor's.
- Nets the vendor left unnamed have names of ours (`ANT_FEED`, `AXP_LX1`, `USB_CC1`...); `netlist.yaml` lists each under `renamed` with the name Altium generated for it.
- The print gives the MPU6886 (U7) pin numbers only; its pin names here are the MPU-6886 datasheet's (DS-000193 v1.1, page 17, Table 9 and Figure 3), which the vendor's docs page links, shortened where the datasheet gives several: `INT` for INT1/DRDY/TP2 (pin 12), `FSYNC` for FSYNC / NC (pin 11), `RESV` for RESV (INT/TP0) (pin 19) and RESV (VPP) (pin 20). Page 1's notes say so, and the symbol's description in the parts list.
- The print names the CH552T's pin 10 `P3.2`, the same name as pin 1; it is `P3.0` here, the CH552 datasheet's name (K15).
- The AXP192's GPIO0 is listed as `GPIO0/LDOio0` in the nets page, apart from the ESP32's net `GPIO0`.

## Source

M5Stack, *StickC-Plus (K016-P) schematic*, one page, Altium sheet `StickC_SCH_Rebuild_V3010.SchDoc` exported 2025-11-04, <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/669/k016-p-StickC-Plus-sche.pdf>, listed on <https://docs.m5stack.com/en/core/StickC-Plus>. The vendor's host did not answer from the machine that drew this on 2026-11-17, so the copy the Wayback Machine captured on 2026-04-21 was read (<https://web.archive.org/web/20260421142825/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/669/k016-p-StickC-Plus-sche.pdf>), SHA-256 `da0717dc357e0480f0eb4e174f2a93db6a3d00b2e0b70deed5f295a9757943cb`, the same file `../board.json` cites. It is the only schematic the docs page lists.

The print states no board revision. It carries R401 and C401 (numbered apart from the rest), which couple the BM8563's interrupt to the power key, and the docs page's change log dates the sleep and wake-up functions to 2021.12, "version changed to v1.1". The docs page publishes no other schematic, and this drawing takes the print as the v1.1 design.

| Vendor block | Its facts are on |
| --- | --- |
| PMU, 5VOUT_BOOST, POWER (S1), Li_Ion, BAT1, R401/C401 | page 2 |
| ESP32-PICO, BUTTONA/BUTTONB, LED/IR | page 3 |
| USB TYPE-C, CH552, GP0/EN/UART | page 4 |
| IMU, RTC, IPS_LCD, I2S_MIC, GROVE, the pads | page 5 |

The connections were read off the printed page and then taken, pin by pin, from the netlist Altium writes into the same PDF's bookmarks (Components and Nets → Pins); the two agree everywhere. The values come from the printed page. The docs page (read at Switch Science's mirror, `docs.m5stack.switch-science.com/en/core/StickC-Plus`, on 2026-11-17) gave the part names and the PinMap (Button A G37, Button B G39, red LED G10, IR G9, passive buzzer G2), which the schematic agrees with.

The Kleidos additions and corrections come from these sources, each cited in full under `source.also_read` in `netlist.yaml`:

- AXP192 datasheet, revision 1.1, English draft (X-Powers), in M5Stack's M5-Schematic repository (`../board.json` `axp192-datasheet-full`).
- BM8563 datasheet V1.1, as M5Stack hosts it (`bm8563-datasheet`).
- MPU-6886 datasheet DS-000193 v1.1 (TDK InvenSense), as M5Stack hosts it (`mpu6886-datasheet`).
- ESP32-PICO Series Datasheet v1.1 (Espressif), as M5Stack hosts it (`esp32-pico-datasheet`).
- WCH CH552 datasheet V1G, read at the Wayback Machine's capture of 2024-04-04 (<https://web.archive.org/web/20240404213535/https://wch-ic.com/downloads/file/309.html>), SHA-256 `fcccd350a578416d189bdbee175609dae03210261a5c4491b9b17b71d0a7a5d2`.
- The vendor's docs page (above).
- Bench records in [`bench/`](bench/), all of 2026-11-17 on one M5StickC Plus 1.1 with the case closed and USB connected: [`sys-int-pull-up-and-drivers`](bench/2026-11-17-sys-int-pull-up-and-drivers.md), [`rtc-int-to-power-key`](bench/2026-11-17-rtc-int-to-power-key.md), [`dcdc1-setpoint`](bench/2026-11-17-dcdc1-setpoint.md), [`usb-bridge-identity`](bench/2026-11-17-usb-bridge-identity.md) and [`buzzer-gpio2-load`](bench/2026-11-17-buzzer-gpio2-load.md) (the last one settles nothing on the drawing).

[`improvements.md`](improvements.md) is the triage that weighed every candidate (ids A1-E6) and lists the bench probes, run and not run.

## Kleidos additions and corrections

The drawing improves on the vendor's print where a primary source makes a detail certain (AGENTS.md, "Schematics"). Each entry is in `kleidos` in `netlist.yaml`, marked on the drawing by its id in amber and listed with its source on page 1. There are 23: 22 additions and one correction.

| Id | Kind | What | Marked at | Source |
| --- | --- | --- | --- | --- |
| K1 | addition | `PWR_KEY`: the AXP192's PWRON (pin 23) has a built-in 100 kohm pull-up to APS. | page 2, `PWR_KEY` labels | AXP192 datasheet v1.1, p. 18, pin 23 |
| K2 | addition | `RTC_INT` is the BM8563's open-drain INT (pin 3), pulled up by R401 to IPSOUT; its falling edge presses `PWR_KEY` through C401, so an RTC countdown or alarm powers the board on from an AXP192 power-off. Each countdown with the RTC's timer interrupt on made the AXP192 latch a power-key short press, and on a build that powers off at the AXP192 the RTC switched the board back on after 19.4 s and 28.7 s (a power-on reset). Run with USB connected; on battery alone not run. | pages 2 and 5, `RTC_INT` labels | bench, `bench/2026-11-17-rtc-int-to-power-key.md` (2026-11-17); BM8563 datasheet V1.1, pp. 1-2 (open-drain INT) |
| K3 | addition | `VESP_3V3` is DC-DC1 set to 3.30 V: the board's `DC1OUT_VOL` register (26H) reads 0x68, 0.7 V plus 104 steps of 25 mV, and the Kleidos firmware never writes it. The datasheet's typical default is 3.3 V, but its defaults are set per order (section 9.6), so the register read settles it, not the datasheet. | page 6, rails table | bench, `bench/2026-11-17-dcdc1-setpoint.md` (2026-11-17); AXP192 datasheet v1.1, p. 37 (REG26H) |
| K4 | addition | `SYS_INT` (GPIO35) is a shared open-drain, active-low line: the AXP192's IRQ and the MPU6886's INT, which is push-pull active high at reset and must be set open drain, active low (INT_PIN_CFG bits 7 and 6) to share it. With both released the net reads high and GPIO35 has no internal pull, so R2 is fitted as drawn; each chip pulled it low on the bench, and an AXP192 IRQ latch left set holds it low. The BM8563's INT is not on it. | pages 2, 3 and 5, `SYS_INT` labels | bench, `bench/2026-11-17-sys-int-pull-up-and-drivers.md` (2026-11-17); AXP192 datasheet v1.1, p. 31, section 9.10; MPU-6886 datasheet v1.1, p. 41, register 55 |
| K5 | addition | `ESP32_EN`: the AXP192's PWROK (pin 5) holds the ESP32 in reset until its outputs are up. | pages 2, 3 and 4, `ESP32_EN` labels | AXP192 datasheet v1.1, p. 17 (pin 5) and p. 21 |
| K6 | addition | U1 pin 26 (VDD_SDIO), unconnected on the board, is an output: the in-package flash's supply, taken from VDD3P3_RTC while MTDI is low at reset (unless an eFuse overrides the strap). Its voltage follows VDD3P3_RTC's rail, which is open (below). | page 3, beside the pin's cross | ESP32-PICO Series Datasheet v1.1, p. 14 (pin 26) and p. 25, section 3.2 |
| K7 | addition | U1 pin 18 (IO12, MTDI), unconnected, is the strapping pin that selects VDD_SDIO's source; its internal pull-down holds it low at reset, which takes VDD_SDIO from VDD3P3_RTC rather than the internal 1.8 V LDO (unless an eFuse overrides the strap). | page 3, beside the pin's cross | ESP32-PICO Series Datasheet v1.1, Table 8, p. 23, and section 3.2, p. 25 |
| K8-K13 | addition | U1 pins 25 (IO16), 27 (IO17), 30 (IO11), 31 (IO6), 32 (IO7) and 33 (IO8), crossed on the print, are the in-package flash's CS, SO/SIO1, HOLD/SIO3, CLK, WP/SIO2 and SI/SIO0. | page 3, beside each pin's cross | ESP32-PICO Series Datasheet v1.1, Table 3, p. 16 |
| K14 | addition | The CH552T (U6) enumerates on USB as an FTDI FT232: VID 0x0403, PID 0x6001, manufacturer `Hades2001`, product `M5stack`; its firmware presents that identity, which is why the docs page points to the FTDI driver. | page 4, `USB_DP` labels | bench, `bench/2026-11-17-usb-bridge-identity.md` (2026-11-17) |
| K15 | correction | U6 pin 10 is P3.0 (RXD), the pin that receives the ESP32's U0TXD through R25. The print names it P3.2, as it names pin 1. | page 4, beside `CH552_RXD` at pin 10 | WCH CH552 datasheet V1G, section 4, p. 4 (TSSOP20 pin 10) |
| K16 | addition | The AXP192 (U2) answers at I2C address 0x34 (write 68H, read 69H). | page 7, I2C table | AXP192 datasheet v1.1, p. 11 and p. 31, section 9.10 |
| K17 | addition | The BM8563 (U4) answers at I2C address 0x51 (write A2h, read A3h). | page 7, I2C table | BM8563 datasheet V1.1, p. 1 |
| K18 | addition | The MPU6886 (U7) answers at I2C address 0x68, its AD0 (pin 9) being on GND; its nCS (pin 22) high on VESP_3V3 selects the I2C interface. | page 7, I2C table | MPU-6886 datasheet v1.1, section 6.2 and Table 13, p. 25 |
| K19 | addition | GPIO0 is a strapping pin with an internal pull-up (and R12 here); low at reset, with GPIO2 low, enters download boot. | page 7, GPIO table | ESP32-PICO Series Datasheet v1.1, Table 8, p. 23, and Table 10, p. 24 |
| K20 | addition | GPIO2 also drives the passive buzzer, whose part and drive circuit are not documented; it is a strapping pin with an internal pull-down, low or floating at reset for download boot. | page 7, GPIO table | the vendor's docs page, PinMap (Passive Buzzer, G2) and specifications ("Integrated passive buzzer"); ESP32-PICO Series Datasheet v1.1, Table 8, p. 23, and Table 10, p. 24 |
| K21 | addition | GPIO5 (`LCD_CS`) is a strapping pin with an internal pull-up (SDIO slave timing). | page 7, GPIO table | ESP32-PICO Series Datasheet v1.1, Table 8, p. 23, and Table 12, p. 26 |
| K22 | addition | GPIO15 (`LCD_MOSI`) is the MTDO strap, with an internal pull-up; low at reset silences the ROM's boot log. | page 7, GPIO table | ESP32-PICO Series Datasheet v1.1, Table 8, p. 23, and Table 11, p. 26 |
| K23 | addition | GPIO27 drives the AXP192's N_VBUSEN (pin 6), which R21 holds low. Low lets IPSOUT take VBUS; high stops it only while REG30H bit 7 is 0 (with the bit set, VBUS is used either way). | page 7, GPIO table | AXP192 datasheet v1.1, p. 17 (pin 6) and p. 23 (the N_VBUSEN and REG30H[7] table) |

Facts about pins or nets the print already connects are marked on their labels (an element `net`) or on a row of the nets page, not on the pin itself, so no printed wire is drawn as an added one.

## Open questions

What is still uncertain stays out of the drawing (`improvements.md` gives the evidence of each item):

- **VDD3P3_RTC and VDDA3P3 (D1, D2, E3).** The print draws U1 pins 19 and 4 hopping over the 3.3 V line, and Altium's netlist keeps each on its own capacitor (C40, C43), apart from `VESP_3V3`. Pin 19 is certainly supplied (the board boots from its in-package flash, fed through VDD_SDIO from VDD3P3_RTC, and its RTC pads work), but which rail feeds it is not settled: probe P4, a voltmeter on the HAT header's G26 and 3V3 pins while DC-DC1 steps from 3.3 to 3.0 V, was not run (it needs a person with a meter). Pin 4 needs the board opened. Both are drawn as the print has them.
- **The HAT header (A2, E5).** Which header pin each pad is, and whether G36 and G25 share one pin as the docs page says (the print draws PAD4 and PAD10 apart, and the vendor's two pages list the pins differently), is not settled: probe P3 (each header pin tied through a resistor to 3V3 and GND) was not run.
- **The buzzer (A1).** The docs page puts a passive buzzer on G2 (K20), but the print draws none. On the bench, GPIO2 held high drew no DC current the AXP192's VBUS reading could see (about ±5 mA over 80 readings each way), which rules out a buzzer switched by a transistor and fits a piezo; no one listened, so its sounding on GPIO2 is not bench-confirmed. Its part and drive circuit need the board opened. Not drawn.
- **A power-on from the RTC on battery alone (B6).** K2's power-on was run with USB connected; on battery alone it was not run.
- **The 3V3 pin's voltage (C6).** K3 rests on the register read; the voltmeter half of probe P6 was not run.
- **LDO1's voltage (C7).** `RTC_VDD` reaches only C11, U2 and U4; the datasheet's LDO1 figure cannot be this board's, and the factory option is not documented.
- **The MPU-6886's REGOUT capacitor (C12, D4).** The datasheet requires 0.1 µF on REGOUT (pin 10), which the print leaves unwired with no cross; where the board carries it needs the board opened.
- **The SGM6603's EN (C16).** That EN is active high and R18 keeps the boost off until EXTEN rises waits for the datasheet's page to be re-read.
- **The microphone's SELECT (C15).** Which channel SELECT on GND picks is in the SPM1423 datasheet's image tables, not re-read.
- **Part numbers (A4).** J1, J2, J3, BAT1, the LEDs, the ESD diodes and the antenna carry no part number in any vendor document read.
- **Settled but not drawn.** The ESP32-PICO-D4's pins 44, 45, 47 and 48 (XTAL_N_NC, XTAL_P_NC, CAP2_NC, CAP1_NC, datasheet Table 2, A7) are not on the vendor's symbol and are not added; the AXP192's N_OE (pin 4) on GND keeps its outputs on (datasheet p. 17, C5) and the CH552T's pin 1 is also VBUS1, its USB bus-voltage detect input (CH552 datasheet section 4, C14): both pins are already drawn on their nets, and a pin entry would draw their printed wires as added ones. The LCD panel's ST7789v2 controller (A3) is named in the parts list from the docs page, as before. Each is low value.

## Files

| File | What it is | Edited by |
| --- | --- | --- |
| `netlist.yaml` | The facts: every component, its value, each pin and its net; rails (with their nominal voltage), I2C, the ESP32 GPIO map, the AXP192 GPIOs, every pull-up and pull-down | hand (review here) |
| `layout.yaml` | How it is drawn: our symbols, which symbol each part takes, the sheets, blocks and rows, the power tree's boxes and arrows, the revision history | hand |
| `m5stickc-plus1.kicad_sch` + seven child `.kicad_sch`, `m5stickc-plus1.kicad_sym`, `m5stickc-plus1.kicad_pro`, `sym-lib-table` | The KiCad project | generated |
| `links.json` | Where each link of the PDF lands, the named destinations and the bookmarks, for `_shared/schematic_pdf.py` | generated |
| `m5stickc-plus1.pdf` | The pages | generated |
| `svg/` | One SVG per page, written by the export when it runs; not kept in git | generated |

## Regenerate and check

```bash
.venv/bin/python _shared/kicad_schematic.py m5stickc-plus1   # KiCad files from netlist.yaml + layout.yaml
.venv/bin/python _shared/export_schematic.py m5stickc-plus1  # ERC, netlist check, PDF (+ links), SVGs, link check
.venv/bin/python _shared/check_schematic_links.py m5stickc-plus1 --list   # every link of the PDF and where it lands
.venv/bin/python -m pytest tests/test_schematic.py
```

The export fails unless the ERC reports nothing (0 errors, 0 warnings), `check_schematic.py` finds every vendor pin on the net `netlist.yaml` names, every SVG has the theme's background and the one line width, and `check_schematic_links.py` finds every link of the PDF leading where it should. The sticks3 schematic's README says what each of those checks holds.

## What the schematic does not say

- The HAT header itself: the print draws ten pads (PAD1-PAD10) with their names; which pin of the top header each pad is, is not printed (see [Open questions](#open-questions)).
- The LCD panel: only its connection is drawn (U5, block IPS_LCD); its ST7789v2 controller, named on the docs page, is inside the panel.
- Part numbers the print leaves out: the battery connector J3 (only `Li_Ion`), the backup cell BAT1 (`DMS_3R3`, no type or maker), the Grove connector J1 (`GROVE`), the USB-C receptacle J2 (`TYPEC`), the LEDs (`LED_IR`, `LED_RED`), the ESD diodes (`ESD/3.3V`), the antenna E1 (`ANT`). The output voltages of the AXP192's LDOs, which are set over I2C, are not printed.
- The antenna E1 is a graphic in the print, with no pin in Altium's netlist; it is drawn on the node of L1 and C1 where the print draws it (`ANT_FEED`).
- The ESP32-PICO-D4's in-package flash and crystal are not drawn; the pins that carry the flash are marked (K6-K13).
- No earlier (pre-v1.1) schematic of the StickC Plus is published on the docs page; nothing older is drawn.
