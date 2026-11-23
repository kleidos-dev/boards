<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# M5Stack Core2 v1.3 (K010-V13): schematic

Kleidos boards: the Core2 v1.3's connectivity in KiCad, documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1 (sources below and in `netlist.yaml`): every part, pin and net of the two schematic sheets M5Stack publishes for this board, with the values printed there, laid out with this project's own layout and symbols, and 27 details the print leaves out or gets wrong, each settled by a datasheet, the vendor's own documents, the Kleidos firmware on this board or a bench probe, marked where it is drawn and listed below with its source. It tells what connects where and how: pull-ups and pull-downs with their values, series parts, the decoupling and filter parts on each interface, every rail and what feeds it, and the ESP32 GPIO of every signal.

[`m5stack-core2-v13.pdf`](m5stack-core2-v13.pdf) has the nine pages, made to be read on a screen and followed by clicking (below); the export also writes one SVG per page into `svg/`, which git does not keep. Both are drawn with the Kleidos KiCad kit ([`_shared/kicad/`](../../_shared/kicad/), copied from the brand repository): the dark theme (graphite ground, parts in light grey, connections in cyan) and the Kleidos drawing sheet, whose title block carries the Kleidos mark, the license and the source address.

| Page | Sheet | What is on it |
| --- | --- | --- |
| 1 | Contents | One box per page with what is on it and its main parts, how to read the drawing, the notes (values, DNP, numbering, zones), the Kleidos additions and corrections with their sources, and the revision history |
| 2 | Power management and inputs | The AXP192 with its DCDC1 (MCU_VDD) and DCDC3 (LCD backlight) inductors, the SY7088 5 V boost, the USB-C input with its fuse and the reserved USB header, the battery header, the two keys, the power LED, the vibration motor, the test points |
| 3 | ESP32 and memory | The ESP32-D0WDQ6-V3 with its supply decoupling, RF path (3D antenna; the IPEX socket, reached only through R2, which is not fitted), crystal and CAP1/CAP2 parts, the flash, the PSRAM, the internal I2C pull-ups |
| 4 | Display, card, clock, audio, UART | The LCD and touch panel connectors, the microSD socket, the BM8563 clock with its crystal and backup cell, the NS4168 amplifier and speaker pads, the USB to UART bridge U3 (the v1.3's CH9102F, drawn with the pins the core sheet prints for its CP2104) with its auto-reset |
| 5 | M5-Bus, ESD and Port A | The 30-pin M5-Bus, the 47R series resistors and SRV05-4 ESD arrays between it and the ESP32, the Grove port A with its pull-ups |
| 6 | Expansion board | The vendor's second sheet: the rear expansion board's M5-Bus, the BMI270 IMU and the SPM1423 PDM microphone |
| 7 | Power tree and rails | How power flows from the USB-C, the M5-Bus 5 V and the battery through the AXP192 to every rail; then every rail's nominal voltage, source, enable and where it is drawn |
| 8 | Nets and signals | Every rail and every net drawn on more than one page with the page/zone of its labels; the ESP32 and AXP192 GPIO maps, the I2C addresses, the test points, every pull-up and pull-down |
| 9 | Parts | Every part: its value as printed, what it is, its nets (two-pin parts), whether it is fitted, and where it is drawn |

The vendor prints the core board on one dense A4 sheet; here it takes pages 2 to 5, by function. The expansion sheet has page 6 to itself: no page mixes the two sheets. Pages 7 to 9 are written by the generator from `netlist.yaml`, not drawn by hand: they cannot disagree with the drawing.

## What it is not

- Not the vendor's design files. The layout, the blocks and every symbol are this project's: the integrated circuits' and connectors' are each board's own (`m5stack-core2-v13.kicad_sym`), and the passive parts, the diodes, the transistors, the switches, the plain connectors, the pads and the ground symbols are this project's generic ones (`kleidos.kicad_sym`, drawn by `_shared/kicad_schematic.py`). No symbol of KiCad's libraries is in these files. No vendor document is in this repository; the sources are cited below.
- Not a PCB design: no footprints, no part numbers beyond the ones the vendor prints and the ones the Kleidos corrections below give, nothing about placement or routing.
- Not a full datasheet of each part: pin names and values are as the vendor prints them, except where a Kleidos correction below says otherwise (`226/6.3V` is 22 uF, `105` is 1 uF, `104` is 100 nF; `DNP` and `RF_C(TBD:DNP)` for a part not fitted).

## How to read it

Pins connect by net labels, not by wires. Two pins whose labels carry the same name are on one net, on any page. After a label, each `[3/C4]` names another page that carries the net and the zone of its label there (the border prints columns 1-8 and rows A-F, 50 mm apart): page 3, row C, column 4. Clicking it lands on that label, zoomed in; on a page where the net has several labels, it lands on the one at the part that feeds the rail (`rails.from` in `netlist.yaml`), or else on the first in reading order. A label with none is on its page only. Neighboring pins of one part on one net share a short bar and one label. A cross on a pin end means the pin is unconnected. Wires and pin lines are one color and one width, so a connection reads as one line from the part to its label.

Parts documented as not fitted (`DNP`: R2, C1, C2) carry KiCad's DNP mark: a red cross over the symbol.

A bold amber id such as `K15` marks a Kleidos addition or correction: after a net's label and its `[page/zone]` links, after a part's reference, or at the end of a row of the rails, GPIO or I2C tables. Each leads to its row of the table "Kleidos additions and corrections" on page 1 (what it adds or corrects, the print's version for a correction, and its source), and the row's id leads back. None of the 27 adds a connection, so no wire is dotted.

In the PDF, each box on the contents page opens its page, and every page carries "Contents" and a row of page numbers above the title block. Each part's reference on the drawing is a link to its row in the parts list, and the row's reference and page/zone lead back to the part. Every place in the index pages (a page/zone, a box of the power tree, a reference in a table) is a link to it. The bookmarks list the pages and, under each, its parts or its tables, each at its place. `_shared/check_schematic_links.py` holds every one of those links (`--list` prints them all).

### In any PDF reader

The export leaves out KiCad's property pop-ups, a script only Acrobat runs, so the PDF holds no script at all; what they showed (reference, value) and more is in the parts list. The rest is plain PDF that every reader follows:

- a link leads to a page and a position: `/XYZ`, the target placed 30 mm from the window's left edge and 20 mm below its top, at zoom 2. KiCad links a text only to a whole page, so `_shared/schematic_pdf.py` sends each link to its place after the export, from the targets the generator writes into `links.json`;
- each link carries a `/Contents` saying where it leads, for screen readers;
- named destinations open the PDF at a part or at a net's label on a page: `m5stack-core2-v13.pdf#nameddest=part-U4`, `m5stack-core2-v13.pdf#nameddest=net-MCU_VDD-p2`.

A reader that ignores the position still opens the right page, and the printed page/zone says where to look.

Numbering, where it differs from the vendor's documents:

- The expansion sheet reuses designators the core sheet has, so its parts are +100 here: its BUS1 is BUS101, U1 (BMI270) is U101, U2 (SPM1423) is U102, R1 is R101, C1 to C3 are C101 to C103.
- The expansion sheet's own net names are drawn with the core's name of the M5-Bus net they reach: `SYS_P033` (bus pin 12) is `MCU_VDD`, `IMU_SDA`/`IMU_SCL` (17/18) are `EXT_G21`/`EXT_G22`, `MIC_CLK`/`MIC_DAT` (24/26) are `EXT_G0`/`EXT_G34`; `netlist.yaml` lists them under `aliases`. Page 6 says so too.
- Nets the vendor left unnamed have names of ours (`AXP_LX1`, `RF_MATCH`, `CP_DTR`, `BOOST_FB`...); `netlist.yaml` lists each under `renamed` with where it is.
- The sheets print no pin numbers for two-pin parts, diodes, transistors or the RTC cell: `netlist.yaml` numbers resistors, capacitors, inductors, keys, the 32.768 kHz crystal and the fuse 1 and 2 in an order of ours, names the diode and LED pins A and K and the transistor pins B, C and E, and gives the RTC cell 1 (+) and 2 (-). A pin the print names but does not number keeps its name in `netlist.yaml` (`EPAD`, `PAD`, `GND_PAD`, the USB-C `VCC`, `GND` and `SHELL`); its symbol numbers it with a short token of ours (`EP`, `P`, `GP`, `V`, `G`, `S`), mapped in `layout.yaml`. The antenna ANT1 and the IPEX socket ANT2 are numbered 1 (feed or center) and 2 (ground or shield), ours too.
- The AXP192's GPIO0 to GPIO4 are listed on page 8 as `AXP_IO0` to `AXP_IO4`, the names the docs page's pin map uses, so they do not read as the ESP32's GPIOs.

## Sources

Both sheets are linked from the Core2 v1.3 docs page, <https://docs.m5stack.com/en/core/Core2_v1.3>, under "Schematics". The vendor's file host did not answer from the machine that drew this on 2026-11-17, so the copies the Wayback Machine captured were read; each was read block by block at 450 dpi.

| Sheet | Vendor file | Read from | SHA-256 | Drawn on |
| --- | --- | --- | --- | --- |
| Core board, "Core2 v1.3 Core Section Schematics PDF": `CORE2_V1.0_SCH`, one A4 sheet printed 2020-07-07 | <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/644/CORE2_V1.0_SCH.pdf> | <https://web.archive.org/web/20260825073713/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/644/CORE2_V1.0_SCH.pdf> | `4a59d16291c7de9d9deda31fe154c8b5ac3c8f92209f6f8206d72f97afeea94f` | pages 2-5 |
| Expansion board, "Core2 v1.3 Expansion Board Section Schematics PDF": `core2_v1.3_SCH`, one A4 sheet printed 2025-11-14 | <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/486/core2_v1.3_SCH_2025_11_14_09_40_33.pdf> | <https://web.archive.org/web/20260717144432/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/486/core2_v1.3_SCH_2025_11_14_09_40_33.pdf> | `7b5def96336139b8ff3b91871ffa476c9b8cd845725263db82e4a8ad8881cea9` | page 6 |

Both are printed to PDF, so neither carries a netlist of its own: the connections were read off the drawings, block by block, and every part in `netlist.yaml` records its sheet and the zone of that sheet's border grid (columns 1-4, rows A-D) where its designator is printed. The values come from the printed sheets. The docs page was read at Switch Science's mirror (`docs.m5stack.switch-science.com/en/core/Core2_v1.3`) on 2026-11-17.

The Kleidos additions and corrections (next section) cite, besides the docs page:

- datasheets, read 2026-11-17: the ESP32 Series Datasheet v5.3 (Espressif), the AXP192 datasheet revision 1.1 (X-Powers, the copy in M5Stack's `M5-Schematic` repository), and the BM8563, BMI270 (BST-BMI270-DS000-05), NS4168, SY7088 and 1027RFN01-33d documents the docs page links (each listed under `sources` in [`../board.json`](../board.json));
- the Kleidos firmware repository (2026-11-17), for code that works on this board, cited by file and line;
- bench probes run on the Kleidos bench unit on 2026-11-17, nothing opened, each recorded under [`bench/`](bench/) with its commands, firmware and raw result: `2026-11-17-esptool-chip-flash-efuse.md` (chip, crystal, flash ID, VDD_SDIO eFuses), `2026-11-17-usb-descriptor.md` (the bridge's USB ID), `2026-11-17-touch-int-gpio39.md`, `2026-11-17-axp192-exten-vbus.md` and `2026-11-17-panel-id-spird.md` (the last three leave questions open, below).

[`improvements.md`](improvements.md) is the triage behind them: every candidate, its evidence and why it went in or stays open.

## Kleidos additions and corrections

Each is an entry of `kleidos` in `netlist.yaml`, marked where it is drawn and listed on page 1. Page 1 gives each source in short; here it is in full. A correction also says what the print shows; the four part corrections K3, K4, K5 and K7 fill in a part the print names only (marked by the reference, with no wire changed).

| Id | Kind | What | Source |
| --- | --- | --- | --- |
| K1 | correction | U3 is a CH9102F (the print: a CP2104-F03-GMR, on a sheet titled V1.0). Its pins, UART nets, 47R resistors and auto-reset pair stay as the sheet prints them for the CP2104 | Docs page specification table; the bench unit enumerates as USB `1a86:55d4` (WCH), `bench/2026-11-17-usb-descriptor.md`, as Kleidos recorded on 2026-06-02 |
| K2 | addition | SYS_VBAT carries the built-in 3.7 V, 500 mAh cell; where it connects is not drawn | Docs page specification table; the board runs on its own cell with USB cut (Kleidos `docs/research/consumption-self-measurement.md`, section "POWERRUN battery runs"); the AXP192 charges and draws it on its BAT pins 34/35, which the print puts on SYS_VBAT |
| K3 | correction | The vibration motor on PAD2 is a 1027RFN01-33d (the print: pads only) | 1027RFN01-33d specification 1.0, linked by the docs page (`board.json` source `motor-ds`) |
| K4 | correction | X2 is a 40 MHz crystal (the print: the part number X252040MMB4SC only) | `bench/2026-11-17-esptool-chip-flash-efuse.md`: esptool `chip_id` read "Crystal is 40MHz" |
| K5 | correction | ANT1 is a 2.4 GHz 3D antenna (the print: no value) | Docs page specification table |
| K6 | addition | RTC_BAT's cell BT1 is an MS412FE, 3 V (the print: BATTERY_RTC) | Docs page specification table |
| K7 | correction | Port A J4 is an HY2.0-4P (Grove) connector (the print: PORT-A) | Docs page specification table and pin map |
| K8 | correction | U7 is the ESP32-D0WDQ6-V3 (the print: ESP32-D0WDQ6); the bench unit is revision v3.1 | Docs page specification table; `bench/2026-11-17-esptool-chip-flash-efuse.md`: "Chip is ESP32-D0WDQ6-V3 (revision v3.1)" |
| K9 | addition | The AXP192 U4 answers at I2C address 0x34 | AXP192 datasheet rev 1.1, p. 31: device address 68H write, 69H read |
| K10 | addition | The touch panel's FT6336U answers at 0x38 | Kleidos `variants/core2_v13/variant.h` (`TOUCH_I2C_ADDR`), read on this board (`docs/hardware/introspection/ft6x36.md`, section "2. Register table": FocalTech ID 0x11, cipher 0x64); the docs page pin map agrees |
| K11 | addition | The BM8563 U5 answers at 0x51 | BM8563 datasheet V1.1, p. 1 (features): I2C slave address write 0A2H, read 0A3H |
| K12 | addition | The BMI270 U101 answers at 0x68 because R101 holds SDO low | BMI270 datasheet BST-BMI270-DS000-05, p. 138 ("Primary Interface I²C"): SDO pulled to GND selects 0x68 |
| K13 | addition | AXP_IO0 (BUS_PW_EN) drives the AXP192's N_VBUSEN (pin 6): high stops the AXP192 taking power from BUS_5V while REG30H[7] is 0 (its default; the bench read `0x42`, `bench/2026-11-17-axp192-exten-vbus.md`), so the boost can feed the bus; R5 holds it low | AXP192 datasheet rev 1.1, p. 17 (pin 6) and p. 23 (N_VBUSEN with REG30H[7]); M5Stack's driver sets it so, `m5stack/M5Core2` `src/AXP192.cpp:447-469` at `67099371` (`SetBusPowerMode()`) |
| K14 | addition | AXP_IO2 (SPK_EN) is the NS4168's CTRL: held low it shuts the amplifier down; left floating, R20's pull-up turns it on | NS4168 datasheet, Table 2 (pp. 6-7): CTRL below 0.4 V is shutdown, 1.5 V to VDD selects the right channel; measured on this board on 2026-11-11, GPIO2 held low 70.0 mA, floating 84.8 mA on the PIN screen (Kleidos `docs/hardware/introspection/axp192.md`, section "Outputs the board never uses") |
| K15 | addition | A BM8563 alarm or countdown switches the powered-off board back on: RTC_INT falls and C30 couples the edge onto PWR_KEY (the AXP192 PWRON) | Kleidos `src/boards/board_core2_v13.cpp` (mechanism: `docs/hardware/introspection/bm8563-rtc.md`, section "PMIC power-on input (core2_v13, cores3_se)"), and the board came back by itself after `PMICOFFTEST 6` (`docs/hardware/introspection/bmi270.md`, section "The NVM-backed registers"); AXP192 datasheet rev 1.1, p. 20: a timer signal on PWRON, low, acts as a key press |
| K16 | addition | PWR_KEY idles high: the AXP192 pulls PWRON (pin 23) up to APS (IPS_BUS) through 100 kohm inside the chip | AXP192 datasheet rev 1.1, p. 18, pin 23 |
| K17 | addition | VDD_SDIO (U7 pin 26, C44) is 3.3 V from VDD3P3_RTC: R15 holds MTDI low at reset, and no eFuse overrides the strap | `bench/2026-11-17-esptool-chip-flash-efuse.md`: `XPD_SDIO_FORCE` not burned, "Flash voltage set by a strapping pin to 3.3V"; ESP32 datasheet v5.3, section 3.2 (p. 24) |
| K18 | addition | GPIO12 is the MTDI strap: R15 holds it low at reset, which selects the 3.3 V VDD_SDIO | ESP32 datasheet v5.3, Table 3-1 (p. 22), section 3.2 (p. 24) |
| K19 | addition | GPIO2 is a boot strap: with GPIO0 low it must be low for download boot; R18 holds it low | ESP32 datasheet v5.3, Tables 3-1 and 3-3 (pp. 22-23) |
| K20 | addition | GPIO0 is the boot-mode strap: high (R10 and the internal pull-up) boots from flash, low enters download boot | ESP32 datasheet v5.3, Tables 3-1 and 3-3 (pp. 22-23) |
| K21 | addition | GPIO15 (MTDO, the LCD's D/C) is a strap (U0TXD printing at boot, SDIO slave timing) with an internal pull-up, default 1; the print draws no external pull on it. The level it samples at reset with the LCD attached is not measured (open, below) | ESP32 datasheet v5.3, Tables 3-1 and 3-4 (pp. 22, 25) |
| K22 | addition | GPIO5 (the LCD's CS) is a strap (SDIO slave timing) with an internal pull-up, default 1; the print draws no external pull on it. Its level at reset is open, as K21's | ESP32 datasheet v5.3, Tables 3-1 and 3-5 (pp. 22, 25) |
| K23 | addition | GPIO39 (the touch panel's INT) is input only with no internal pull, and the print draws none on the line | ESP32 datasheet v5.3, p. 61 (Table 6-1, note 2): GPIO34-39 have no output driver and no internal pull-up or pull-down |
| K24 | addition | GPIO34 is input only with no internal pull | ESP32 datasheet v5.3, p. 61 |
| K25 | addition | GPIO35 is input only with no internal pull | ESP32 datasheet v5.3, p. 61 |
| K26 | addition | GPIO36 is input only with no internal pull | ESP32 datasheet v5.3, p. 61 |
| K27 | addition | BUS_5V is 5.03 V: R30 15K and R31 4.7K on the SY7088's 1.2 V feedback reference (computed, not measured) | SY7088 datasheet (Silergy), p. 2 (FB pin): VOUT = 1.2 V x (1 + RH/RL); p. 3: VREF 1.182 to 1.218 V, so 4.95 to 5.11 V before the resistors' 1 % |

## Files

| File | What it is | Edited by |
| --- | --- | --- |
| `netlist.yaml` | The facts: every component, its value, the vendor sheet and zone, each pin and its net; rails (with their nominal voltage), I2C, ESP32 GPIO map, AXP192 GPIOs, every pull-up and pull-down; the Kleidos additions and corrections (`kleidos`) | hand (review here) |
| `improvements.md` | The triage of candidate additions and corrections: evidence and status of each | hand |
| `bench/` | One record per bench probe: commands, firmware, raw result | hand |
| `layout.yaml` | How it is drawn: our symbols, which symbol each part takes, the sheets, blocks and rows, the power tree's boxes and arrows, the revision history | hand |
| `m5stack-core2-v13.kicad_sch` + eight child `.kicad_sch`, `m5stack-core2-v13.kicad_sym`, `m5stack-core2-v13.kicad_pro`, `sym-lib-table` | The KiCad project | generated |
| `links.json` | Where each link of the PDF lands, the named destinations and the bookmarks, for `_shared/schematic_pdf.py` | generated |
| `m5stack-core2-v13.pdf` | The pages | generated |
| `svg/` | One SVG per page, written by the export when it runs; not kept in git | generated |

## Regenerate and check

```bash
.venv/bin/python _shared/kicad_schematic.py m5stack-core2-v13   # KiCad files from netlist.yaml + layout.yaml
.venv/bin/python _shared/export_schematic.py m5stack-core2-v13  # ERC, netlist check, PDF (+ links), SVGs, link check
.venv/bin/python _shared/check_schematic_links.py m5stack-core2-v13 --list   # every link of the PDF and where it lands
.venv/bin/python -m pytest tests/test_schematic.py
```

The export fails unless the ERC reports nothing (0 errors, 0 warnings), `check_schematic.py` finds every vendor pin on the net `netlist.yaml` names, every SVG has the theme's background and every wire-colored line the one width (6 mil), and `check_schematic_links.py` finds every link of the PDF leading where it should, with no script in the document.

## Open questions

What is still uncertain stays out of the drawing (`improvements.md` gives the evidence of each):

- **The CH9102F's pins.** U3 is a CH9102F (K1), but no CH9102F drawing of this board is published and the WCH CH9102 datasheet could not be read (wch-ic.com refused the connection on 2026-11-17), so whether its QFN24 is pin-compatible with the CP2104 the sheet draws is not checked. Its pins, UART nets, 47R series resistors and auto-reset pair are drawn as the sheet prints them.
- **The LCD controller.** The docs page names ILI9342C, then ILI9342E from 2026-08-07, inside the module. Reading the bench unit's ID failed on 2026-11-17 (`bench/2026-11-17-panel-id-spird.md`): the Kleidos console reads the panel as 3-wire on the shared data line, where the ILI9342 answers on MISO (GPIO38).
- **Where the built-in cell connects.** SYS_VBAT carries it (K2); the sheets draw only the reserved header J5 (EXT.BATT), and the expansion sheet leaves bus pin 30 unconnected.
- **The speaker and some part numbers.** No document gives the speaker on PAD1 (impedance, power), the keys S1 and S2 (TS_015 only), the USB-C receptacle J3 (TYPEC_16P only) or the flash U1's maker: the bench read JEDEC ID `0x46 0x40 0x18`, 16 MB as U1's capacity, but the XM25QH128B datasheet that would tie `0x46` to XMC was not found, so U1 keeps its printed part number.
- **The expansion board's other M5-Bus pins.** Its sheet connects only bus pins 1, 3, 5, 12, 17, 18, 24 and 26; whether the board passes the bus through to a stacked base is not shown. A probe at the M-BUS slot (removing the back strip, a multimeter) was not run.
- **TP6.** Its printed name is RTC_3V3, the same as TP5's, but it sits on the PWR_KEY net; one of the two is the print's error, and the test points are inside the case. It is drawn on PWR_KEY, as the sheet wires it.
- **RTC_VDD.** TP5 names it 3.3 V; the AXP192 datasheet gives LDO1 1.25 V typical, set at the factory per chip option. The rail keeps the print's 3.3 V; only a probe inside the case settles it.
- **The touch INT line's drive.** GPIO39 has no pull on the ESP32 side (K23); idle, it read high on 21 of 21 reads (`bench/2026-11-17-touch-int-gpio39.md`), but whether the panel drives it both ways needs reads with a finger on the glass.
- **BUS_5V measured, and the bit that gates EXTEN.** 5.03 V is computed (K27). After Kleidos's boot the boost is off (REG10H bit 2 and REG12H bit 6 both 0, no VBUS, `bench/2026-11-17-axp192-exten-vbus.md`). The AXP192 datasheet gives EXTEN as REG10H bit 2 (p. 36) and REG12H bits 7-4 as reserved, and M5Stack's own driver switches the boost with REG10H bit 2 (`m5stack/M5Core2` `src/AXP192.cpp:458-460` at `67099371`); measuring the rail with the boost on needs a multimeter and a register write not made.
- **The levels GPIO15 and GPIO5 sample at reset.** Both are straps with internal pull-ups and no external pull on the print (K21, K22), but they drive the LCD's D/C and CS inputs, so their level at reset (U0TXD printing, SDIO slave timing) depends on the module too; the ESP32's strap register, read on the bench (esptool `read_mem` of `GPIO_STRAP_REG`), would settle it.
