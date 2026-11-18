# M5Stack StickC-Plus SE (K016-P-SE): schematic

Kleidos boards: the StickC-Plus SE's connectivity in KiCad, documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1 (sources below and in `netlist.yaml`): every part, pin and net the vendor's schematic shows, with the values it prints, laid out with this project's own layout and symbols, plus 28 details the print leaves out or gets wrong, each settled by a datasheet, the vendor's docs page or a bench probe and marked where it is drawn (below, "Kleidos additions and corrections"). It tells what connects where and how: pull-ups and pull-downs with their values, series parts, the filter and decoupling parts on each interface, every rail and what feeds it, and the ESP32 GPIO of every signal.

[`m5stickc-plus-se.pdf`](m5stickc-plus-se.pdf) has the seven pages, made to be read on a screen and followed by clicking (below); the export also writes one SVG per page into `svg/`, which git does not keep. Both are drawn in the Kleidos dark theme ([`_shared/kicad-theme-kleidos-dark.json`](../../_shared/kicad-theme-kleidos-dark.json)): graphite ground, parts in light grey, connections in cyan.

| Page | Sheet | What is on it |
| --- | --- | --- |
| 1 | Contents | One box per page with what is on it and its main parts, how to read the drawing, the notes (values, DNP, numbering, crossings, zones), the Kleidos additions and corrections with their sources, and the revision history |
| 2 | Power, clock and boost | The AXP192 with its inputs, outputs and references, the cell and the backup cell, the SYS I2C pull-ups, the BM8563 clock and its crystal, the power key with the clock's wake path (R401, C401), the SGM6603 5 V boost |
| 3 | ESP32-PICO-D4 | The ESP32-PICO-D4 module, its supply decoupling, the antenna and its match, the strapping and button pull-ups, the unfitted IMU footprint, the ten pads and the series resistors and ESD diodes in front of three of them |
| 4 | USB, LCD and peripherals | The USB-C port, the CH552T USB-UART bridge, the auto-reset switches and UART resistors, the LCD, the microphone, the IR and red LEDs, the two keys, the Grove port |
| 5 | Power tree and rails | How power flows from the USB-C port, the VIN pad and the two cells through the AXP192 to every rail, then every rail's nominal voltage, source, enable and where it is drawn |
| 6 | Nets and signals | Every rail and every net drawn on more than one page with the page/zone of its labels; the ESP32-PICO-D4 and AXP192 GPIO maps, the I2C addresses, the pads, every pull-up and pull-down |
| 7 | Parts | Every part: its value as printed, what it is, its nets (two-pin parts), whether it is fitted, and where it is drawn |

Pages 5 to 7 are written by the generator from `netlist.yaml`, not drawn by hand: they cannot disagree with the drawing.

## What it is not

- Not the vendor's design files. The layout, the blocks and every symbol are this project's: the integrated circuits' and connectors' are each board's own (`m5stickc-plus-se.kicad_sym`), and the passive parts, the diodes, the transistors, the switches, the plain connectors, the pads and the ground symbols are this project's generic ones (`kleidos.kicad_sym`, drawn by `_shared/kicad_schematic.py`). No symbol of KiCad's libraries is in these files. No vendor document is in this repository; the source is cited below.
- Not a PCB design: no footprints, no part numbers beyond the ones the vendor documents, nothing about placement or routing.
- Not a full datasheet of each part: pin names and values are as the vendor prints them (`5.1K`, `100uF/4V`, `NC` for a part not fitted), except where a Kleidos correction names it otherwise (K1, K28).

## How to read it

Pins connect by net labels, not by wires. Two pins whose labels carry the same name are on one net, on any page. After a label, each `[3/B2]` names another page that carries the net and the zone of its label there (the border prints columns 1-8 and rows A-F, 50 mm apart): page 3, row B, column 2. Clicking it lands on that label, zoomed in; on a page where the net has several labels, it lands on the one at the part that feeds the rail (`rails.from` in `netlist.yaml`), or else on the first in reading order. A label with none is on its page only. Neighbouring pins of one part on one net share a short bar and one label. A cross on a pin end means the pin is unconnected. Wires and pin lines are one colour and one width, so a connection reads as one line from the part to its label.

Parts documented as not fitted (value `NC`: the IMU footprint U7 and C21, C28, C29) carry KiCad's DNP mark: a red cross over the symbol.

An amber, bold `K5` beside a part's reference, a pin's cross, a net label or at the end of a row of an index page marks a Kleidos addition or correction (below); in the PDF it leads to the entry's row on page 1, and the row's id leads back. None of the 28 adds a connection, so no wire is drawn dotted.

In the PDF, each box on the contents page opens its page, and every page carries "Contents" and a row of page numbers above the title block. Each part's reference on the drawing is a link to its row in the parts list, and the row's reference and page/zone lead back to the part. Every place in the index pages (a page/zone, a box of the power tree, a reference in a table) is a link to it. The bookmarks list the pages and, under each, its parts or its tables, each at its place. `_shared/check_schematic_links.py` holds every one of those links (`--list` prints them all).

### In any PDF reader

The PDF holds no script: KiCad's property pop-ups only run in Acrobat, so the export leaves them out, and what they showed (reference, value) and more is in the parts list. The rest is plain PDF that every reader follows:

- a link leads to a page and a position: `/XYZ`, the target placed 30 mm from the window's left edge and 20 mm below its top, at zoom 2. KiCad links a text only to a whole page, so `_shared/schematic_pdf.py` sends each link to its place after the export, from the targets the generator writes into `links.json`;
- each link carries a `/Contents` saying where it leads, for screen readers;
- named destinations open the PDF at a part or at a net's label on a page, from a web page or another document: `m5stickc-plus-se.pdf#nameddest=part-U2`, `m5stickc-plus-se.pdf#nameddest=net-VESP_3V3-p3`.

### Numbering, where it differs from the vendor's print

- The print leaves the ESP32-PICO-D4's designator unassigned ("U?"); it is U1 here. The battery connector carries only the label "Li_Ion" and no designator; it is J3 here.
- The print's ESP32-PICO-D4 symbol leaves out four of the package's 49 pins (44, 45, 47, 48); they are drawn here, unconnected, with their datasheet names (K9). The print numbers the unfitted IMU footprint U7's pins only; they carry the MPU-6886 datasheet's names here (K28). The print names U6 pin 10 "P3.2", as it names pin 1; it is named P3.0, the CH552 datasheet's name, here (K1).
- The print numbers no pin of a resistor, capacitor, inductor, diode, LED, crystal, key, MOSFET or two-pin connector. Here two-pin parts take pins 1 and 2 (for the diodes and LEDs, 1 is the cathode and 2 the anode, as KiCad numbers them; for the polarised CX1 and CX2, 1 is the + terminal), and the MOSFETs take G, D and S. Pins the print names but does not number keep their name as their key in `netlist.yaml` (J2's VCC, GND and SHELL; U5's PAD).
- J2 is drawn with its pin numbers hidden: the print numbers only its CC and data pins, and those numbers are in the pin names (`CC1(A5)`). U5's GND (pin 2) and PAD are drawn as one pin, `GND/PAD`, since both are on GND.
- Nets the print leaves unnamed have names of ours (`AXP_LX1`, `MOS1_G`, `RTC_OSCI`...); `netlist.yaml` lists each under `unnamed_nets` with where it is.
- The AXP192's GPIOs are listed as `AXP GPIO0` to `AXP GPIO4` in the nets page, to keep them apart from the ESP32's GPIO nets.

## Source

M5Stack, *StickC-Plus SE schematic (K016-P-SE-SCH)*, one A4 sheet, <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1234/K016-P-SE-SCH_StickC-Plus-SE_SCH.pdf>, listed on <https://docs.m5stack.com/en/core/StickC-Plus_SE>. The print states no revision or date of its own: its PDF was printed on 2025-11-04 (the file's metadata, "Microsoft: Print To PDF"), and it carries the revision note "IMU (MPU6886) was removed in version SE and only exists in versions V1.1 and earlier". The vendor's host timed out from the machine that drew this on 2026-11-17, so the copy the Wayback Machine captured on 2026-08-31 was read (<https://web.archive.org/web/20260831122432/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1234/K016-P-SE-SCH_StickC-Plus-SE_SCH.pdf>), SHA-256 `49be11fda8fa216cdd316a16db4a2eca30b6654f284c0aca52a465cbdea6c46f`.

The print is a printer's PDF and carries no netlist, so every connection was read off the printed page, at 450 to 2400 dpi, block by block. Where two wires cross without a junction dot, they are read as not connected, the way the print draws every other crossing (for instance the Grove port's GPIO32 and GPIO33 across EXT_VDD). The values come from the printed page. Everything else on the drawing is a Kleidos addition or correction (below), each from one of these, cited in full under `source.also_read` in `netlist.yaml`:

- the vendor's docs page, read at Switch Science's mirror (`docs.m5stack.switch-science.com/en/core/StickC-Plus_SE`) on 2026-11-17: the LCD, the HY2.0-4P port, the cell, the VIN input range;
- Espressif's *ESP32-PICO Series Datasheet* v1.5, SHA-256 `177eb1517274eea5056ce725951091ebe8e2bce1d8635f064081fdad1cec0918`;
- WCH's *CH552 datasheet* V1G (the Wayback Machine's capture of 2024-04-04 of `wch-ic.com/downloads/file/309.html`), SHA-256 `fcccd350a578416d189bdbee175609dae03210261a5c4491b9b17b71d0a7a5d2`;
- Belling's *BM8563 datasheet* V1.1 as M5Stack hosts it, SHA-256 `a847c85a8d00121c1338c62797039fa1412d70588873313bd1759c80d4da44ed`;
- X-Powers' AXP192 four-page summary (revision 1.0) as M5Stack hosts it, and its full datasheet v1.1 (English draft, in M5Stack's M5-Schematic repository), SHA-256 `b15b800222b91480ab3ab9a73dacdea1ef2643598d11358913532cf02e0183f0`;
- TDK InvenSense's *MPU-6886 datasheet* DS-000193 v1.1 as M5Stack hosts it, SHA-256 `6751256f22f10afc7bbd1cdfd2c2d20ecffedddad364cea4973f8a84b13634bb`;
- the bench records in [`bench/`](bench/), all of 2026-11-17, run on one unit with its case closed: three are cited by entries, the fourth (GPIO2) left its item open;
- M5Stack's M5Unified driver library at commit 96576a1 and the Kleidos firmware, as second sources only.

| Vendor block | Its parts are on |
| --- | --- |
| PMU, the battery and backup-cell connectors, RTC, 5VOUT_BOOST, the keys' power switch S1 with D13, R401 and C401 | page 2 |
| ESP32-PICO, IMU, the pads, the series resistors and ESD diodes of the pads | page 3 |
| USB TYPE-C, CH552, GP0/EN/UART, IPS_LCD, I2S_MIC, LED/IR, the keys S2 and S3 with D8, GROVE | page 4 |

## Kleidos additions and corrections

The drawing improves on the vendor's print where a primary source makes a detail certain (`AGENTS.md`, "Schematics"). Each entry is `kleidos` in `netlist.yaml`, marked in amber where it is drawn and listed on page 1 with its source; [`improvements.md`](improvements.md) is the triage that weighed each candidate (its item in the last column), and [`bench/`](bench/) holds the probe records. Page 1 gives one source per entry; the second sources are here.

| Id | Kind | What | Marked at | Source | Item |
| --- | --- | --- | --- | --- | --- |
| K1 | correction | U6 pin 10 is P3.0 (UART0 RXD); the print names it P3.2, like pin 1. Its net, CH552_RXD, is unchanged. | page 4, the `CH552_RXD` label | CH552 datasheet V1G, section 4 (pin definitions), p. 4, TSSOP20 pin 10 | T04 |
| K2 | correction | U5, printed "LCD", is a 1.14-inch 135 x 240 colour TFT with an ST7789V2 driver. | page 4, U5's reference | the docs page (2026-11-17), specifications, LCD; the vendor's back label ("LCD 1.14 TFT,135x240 ST7789V2") | T11 |
| K3 | correction | J1, printed "GROVE", is an HY2.0-4P port: 1 GND, 2 5V, 3 G32, 4 G33. | page 4, J1's reference | the docs page (2026-11-17), HY2.0-4P table; the back label ("HY2.0-4P G V OUT G32 G33") | T12 |
| K4 | addition | The cell on J3 is the built-in 3.7 V 120 mAh lithium cell. | page 5, the `VBAT_Li_Ion` row | the docs page (2026-11-17), specifications, Battery; the back label ("BATTERY: 120mAh"); Kleidos `BATTERY_CAPACITY_MAH 120` (`variants/m5stickc_plus_se/variant.h`) | T13 |
| K5 | addition | `VBUS_VIN` (pad PAD6, the AXP192's ACIN) takes 5 V; the docs page limits it, like `VBUS_USB`, to 4.8-5.5 V. | page 5, the `VBUS_VIN` row | the docs page (2026-11-17), Hat-Bus notes | T14 |
| K6 | addition | `LCD_BL_VCC` (LDO2) is set over I2C, 1.8-3.3 V in 100 mV steps; its voltage sets the backlight. | page 5, the `LCD_BL_VCC` row | AXP192 summary rev 1.0, p. 1, features; Kleidos varies it between 2.5 and 3.3 V (`src/drivers/power/axp192.h`, `BacklightConfig::minMv`, `maxMv`) | T15 |
| K7 | addition | `LCD_LOGIC_VCC` (LDO3) is set over I2C, 1.8-3.3 V in 100 mV steps. Both firmwares set 3.0 V, which is not a fixed value of the board. | page 5, the `LCD_LOGIC_VCC` row | AXP192 summary rev 1.0, p. 1; M5Unified `src/utility/Power_Class.inl:1238` at 96576a1 and Kleidos `src/drivers/power/axp192.cpp` (`Axp192::prepareDisplay`) set 3000 mV | T15 |
| K8 | addition | `MIC_VCC` (the AXP192's GPIO0 as LDOIO0) is set over I2C, 1.8-3.3 V in 100 mV steps. | page 5, the `MIC_VCC` row | AXP192 summary rev 1.0, p. 1; AXP192 v1.1, p. 17, pin 19 (GPIO0, "Low noise LDO", REG90H); Kleidos switches it off (`variants/m5stickc_plus_se/variant.h` (`PMIC_AXP192_UNUSED_GPIO0`)) | T15 |
| K9 | correction | U1's pins 44 (XTAL_N_NC), 45 (XTAL_P_NC), 47 (CAP2_NC) and 48 (CAP1_NC) are drawn, unconnected; the vendor's symbol omits them. | page 3, U1's reference | ESP32-PICO Series Datasheet v1.5, Table 2, p. 15 ("No connection") | T17 |
| K10 | addition | IO6 (CLK, pin 31) is the in-package flash's CLK. | page 3, beside the pin's cross | ESP32-PICO v1.5, Table 3, p. 16 | T18 |
| K11 | addition | IO7 (SD0, pin 32) is the in-package flash's WP/SIO2. | page 3, beside the pin's cross | as K10 | T18 |
| K12 | addition | IO8 (SD1, pin 33) is the in-package flash's SI/SIO0. | page 3, beside the pin's cross | as K10 | T18 |
| K13 | addition | IO11 (CMD, pin 30) is the in-package flash's HOLD/SIO3. | page 3, beside the pin's cross | as K10 | T18 |
| K14 | addition | IO16 (pin 25) is the in-package flash's CS. | page 3, beside the pin's cross | as K10 | T18 |
| K15 | addition | IO17 (pin 27) is the in-package flash's SO/SIO1. GPIO9 and GPIO10 (SD2, SD3) are not flash lines on the PICO-D4, which is why the LEDs can use them. | page 3, beside the pin's cross | as K10 | T18 |
| K16 | addition | GPIO0 is a boot strap with an internal pull-up (beside R12); low at reset, with GPIO2 low, enters download boot; high, SPI boot. | page 6, GPIO table | ESP32-PICO v1.5, Table 8, p. 23; Table 10, p. 24 | T19 |
| K17 | addition | GPIO2 is a boot strap with an internal pull-down; it must be low (or floating) with GPIO0 low for download boot. | page 6, GPIO table | as K16 | T19 |
| K18 | addition | GPIO5 (`LCD_CS`) is a strap with an internal pull-up (SDIO slave timing). | page 6, GPIO table | ESP32-PICO v1.5, Table 8, p. 23 | T19 |
| K19 | addition | IO12 (pin 18, unconnected) is the MTDI strap: its internal pull-down holds it at 0 at reset, which powers VDD_SDIO (pin 26, the in-package flash's supply) directly from VDD3P3_RTC rather than from the internal 1.8 V LDO, unless the eFuse EFUSE_SDIO_FORCE overrides the strap. | page 3, beside the pin's cross | ESP32-PICO v1.5, Table 8, p. 23; section 3.2, p. 25; Table 17 note 2, p. 37 (VDD_SDIO from VDD3P3_RTC "for 3.3 V flash") | T19 |
| K20 | addition | GPIO15 (`LCD_MOSI`) is the MTDO strap, with an internal pull-up; low at reset silences the boot log. | page 6, GPIO table | ESP32-PICO v1.5, Table 8, p. 23 | T19 |
| K21 | addition | GPIO36 is input only with no internal pull, and no resistor on the board pulls it (R107 is in series, D16 is an ESD diode). Whether GPIO25 meets it at the Hat-Bus header, as the docs page says, is open (T08). | page 6, GPIO table | ESP32-PICO v1.5, notes to Table 2, p. 13; the netlist (D16, R107, U1 pin 5 only) | T20 |
| K22 | addition | GPIO38 is input only with no internal pull, and nothing on the board pulls it: pad PAD3 floats unless something is attached. | page 6, GPIO table | as K21; the netlist (PAD3, U1 pin 7 only) | T20 |
| K23 | addition | The AXP192 U2 answers at I2C address 0x34. | page 6, I2C table | bench, [`bench/2026-11-17-i2c-scan.md`](bench/2026-11-17-i2c-scan.md) (2026-11-17); M5Unified `AXP192_Class.hpp` `DEFAULT_ADDRESS` at 96576a1; AXP192 v1.1, p. 31 (write 68H) | T21 |
| K24 | addition | The BM8563 U4 answers at I2C address 0x51 (write A2h, read A3h). | page 6, I2C table | BM8563 datasheet V1.1, p. 1; the same bench scan | T22 |
| K25 | addition | R401 is the pull-up the BM8563's open-drain INT needs. | page 6, pull table | BM8563 V1.1, p. 2, pin 3 ("interrupt output, open drain") | T23 |
| K26 | addition | `RTC_INT`: when the BM8563 asserts INT, C401 couples the edge onto `PWR_KEY` and the AXP192 sees one power-key press. It powers the board on from an AXP192 power-off, on battery alone. GPIO35 is not on it: GPIO35 is `SYS_INT`, the AXP192's IRQ, and stayed high throughout. | page 2, the `RTC_INT` labels | bench, [`bench/2026-11-17-rtc-int-power-key.md`](bench/2026-11-17-rtc-int-power-key.md) (2026-11-17): twice running, twice from an AXP192 power-off (once with VBUS cut) | T24 |
| K27 | addition | GPIO27 drives the AXP192's N_VBUSEN, active low while REG30H bit 7 is 0 (as Kleidos leaves it): low (R21's default) lets VBUS in, high shuts it out and the board runs from its cell. With bit 7 set, as M5Unified sets it on the StickC Plus (`src/utility/Power_Class.inl:1236` at 96576a1), VBUS stays in whatever GPIO27 does. | page 6, GPIO table | bench, [`bench/2026-11-17-gpio27-n-vbusen.md`](bench/2026-11-17-gpio27-n-vbusen.md) (2026-11-17), with REG30H bit 7 = 0; AXP192 v1.1, p. 17, pin 6, and p. 23 (the N_VBUSEN / REG30H[7] table) | T27 |
| K28 | correction | The unfitted footprint U7's pins carry the MPU-6886's names (8 VDDIO, 9 AD0/SDO, 10 REGOUT, 11 FSYNC, 12 INT, 13 VDD, 18 GND, 19 and 20 RESV, 22 nCS, 23 SCL/SCLK, 24 SDA/SDI, the rest NC); the print numbers them only. | page 3, U7's reference | MPU-6886 datasheet DS-000193 v1.1, Table 9, p. 17; the print's revision note names the MPU6886 | T28 |

Four entries describe a part the print does draw (K2, K3, K9, K28). They are corrections rather than additions so that the drawing marks the part without drawing its printed connections as added; none of the 28 adds a wire.

## Open questions

What is still uncertain stays out of the drawing; [`improvements.md`](improvements.md) gives the evidence of each item and the probes that would settle it.

- **U1 pin 19, VDD3P3_RTC (T01).** The print draws its wire across the `VESP_3V3` bar with no junction dot, so it is drawn on its own net (`U1_VDD3P3_RTC`, with C40). The pin is certainly supplied: the board boots from the in-package flash, whose VDD_SDIO comes from VDD3P3_RTC (K19), and the LCD runs on GPIO13 and GPIO15, RTC IOs. That the supply is `VESP_3V3` is what the print's geometry suggests; probe P1 (a multimeter on the header's G26 and 3V3 cells while DCDC1 steps) did not run, since no one was at the bench.
- **U1 pin 4, VDDA3P3 (T02).** The same crossing without a dot as pin 19; pin 3, the other VDDA3P3, is on `VESP_3V3`, so the chip works either way and no firmware behaviour tells them apart. It cannot be settled without opening the board.
- **The buzzer on GPIO2 (T06).** The docs page and the back label list a passive buzzer on G2; the print draws none (GPIO2 reaches only PAD2). Bench P4 found no DC load on GPIO2 and no change in draw with a 2.7 kHz tone on it, which fits a piezo element, a MOSFET gate or nothing ([`bench/2026-11-17-gpio2-buzzer.md`](bench/2026-11-17-gpio2-buzzer.md)); no one listened. Whether GPIO2 drives a sounder needs a listener (or the board's own microphone in a probe image); its circuit cannot be settled without opening the board. Neither is drawn.
- **The Hat-Bus header (T07, T08, T09).** The docs page and the back label give an 8-pin 2.54 mm header (GND, 5V_OUT, G26, G36/G25, G0, BAT, 3V3, 5V_IN); the print draws only the pads PAD1-PAD10. Seven cells match a pad by name, G36 and G25 share one cell (which would join `GPIO36_EXT` and `GPIO25`), and the BAT cell has no pad. Probe P3 (a multimeter, a current-limited supply on 5V_IN, 1 kohm ties on the header) did not run. The header is not drawn.
- **RTC_VDD's voltage (T16).** LDO1 is "30 mA, always on" in the AXP192 summary; the full datasheet's table does not give it unambiguously. It stays "not printed"; measuring at C11 needs the board open.
- **U8 pin 4, NC/FB (T29)** and **the microphone's SELECT edge (T30).** The SGM6603 datasheet was not readable (HTTP 403) and the SPM1423's edge is in its image tables; both stay as printed.
- **Part numbers the print leaves out (T32).** The ESD diodes ("ESD/3.3V"), the LEDs ("LED_IR", "LED_RED"), the inductors, the 32.768 kHz crystal, the antenna ("ANT"), J2 ("TYPEC"), J3 ("Li_Ion") and the backup cell BAT1 ("DMS_3R3", no chemistry or capacity). No primary source names them; they need the part markings.

Settled with no change to the drawing: U6 pin 20 (V33) on its own net with C25, as the CH552 datasheet requires at a 5 V VCC (T03); D3 on `USB_DP` and D4 on `USB_DM` (T05); the docs page's "reset button" is the power key S1, a single click of which powers on or resets: the print and the case show three keys only (T10); GPIO32 and GPIO33 cross `EXT_VDD` without joining it (T31).

## Files

| File | What it is | Edited by |
| --- | --- | --- |
| `netlist.yaml` | The facts: every component, its value, the vendor's block, each pin and its net; the unnamed nets, the rails (with their nominal voltage), I2C, the ESP32 GPIO map, the AXP192 GPIOs, every pull-up and pull-down, and the Kleidos additions and corrections (`kleidos`) | hand (review here) |
| `layout.yaml` | How it is drawn: our symbols, which symbol each part takes, the sheets, blocks and rows, the power tree's boxes and arrows, the revision history | hand |
| `m5stickc-plus-se.kicad_sch` + six child `.kicad_sch`, `m5stickc-plus-se.kicad_sym`, `m5stickc-plus-se.kicad_pro`, `sym-lib-table` | The KiCad project | generated |
| `improvements.md` | The triage behind the additions and corrections: every candidate (T01-T33, B1-B7), its evidence, its status, and the bench probes (P1-P6) with their results | hand |
| `bench/` | The bench records the entries cite, one per probe | hand |
| `links.json` | Where each link of the PDF lands, the named destinations and the bookmarks, for `_shared/schematic_pdf.py` | generated |
| `m5stickc-plus-se.pdf` | The pages | generated |
| `svg/` | One SVG per page, written by the export when it runs; not kept in git | generated |

## Regenerate and check

```bash
.venv/bin/python _shared/kicad_schematic.py m5stickc-plus-se   # KiCad files from netlist.yaml + layout.yaml
.venv/bin/python _shared/export_schematic.py m5stickc-plus-se  # ERC, netlist check, PDF (+ links), SVGs, link check
.venv/bin/python _shared/check_schematic_links.py m5stickc-plus-se --list   # every link of the PDF and where it lands
.venv/bin/python -m pytest tests/test_schematic.py
```

The export fails unless the ERC reports nothing (0 errors, 0 warnings), `check_schematic.py` finds every vendor pin on the net `netlist.yaml` names with no net split or joined and every Kleidos entry marked and listed, every SVG has the theme's background and every wire and pin line the one width (6 mil), and `check_schematic_links.py` finds every link of the PDF leading where it should, with no script in the document.

