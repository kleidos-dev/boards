# M5Stack CoreS3-SE (K128-SE): schematic

Kleidos boards: the CoreS3-SE's connectivity in KiCad, documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1 (sources below and in `netlist.yaml`): every part, pin and net of the SE's netlist, with the values the vendor documents, laid out with this project's own layout and symbols. It tells what connects where and how: pull-ups and pull-downs with their values, series parts, the filter and decoupling parts on each interface, every rail and what feeds it, the ESP32-S3 GPIO of every signal and the AW9523B expander pin of every control line.

[`cores3-se.pdf`](cores3-se.pdf) has the ten pages, made to be read on a screen and followed by clicking (below); the export also writes one SVG per page into `svg/`, which git does not keep. Both are drawn in the Kleidos dark theme ([`_shared/kicad-theme-kleidos-dark.json`](../../_shared/kicad-theme-kleidos-dark.json)): graphite ground, parts in light grey, connections in cyan.

| Page | Sheet | What is on it |
| --- | --- | --- |
| 1 | Contents | One box per page with what is on it and its main parts, how to read the drawing, the notes (values, DNP, numbering, zones) and the revision history |
| 2 | Power management | Vendor sheet 1: the AXP2101 with its DC-DC and LDO outputs, the reset and power keys, the charge LED, the 3.3 V clamp, the battery connector |
| 3 | Boot strap, USB-C, boost, RTC | Vendor sheet 2: the LMV331 comparator that holds GPIO0 at power-up, the USB-C receptacle and the 4-pin USB header, the SY7088 5 V boost, the BM8563 clock |
| 4 | ESP32-S3 | Vendor sheet 3: the ESP32-S3 with its flash and PSRAM, the 40 MHz crystal, the RF path to the chip antenna and the IPEX connector, the I2C pull-ups, the supply decoupling |
| 5 | Audio | Vendor sheet 4: the AW88298 amplifier, the ES7210 audio ADC, the two microphones, the echo reference taken from the speaker lines |
| 6 | Expander and connectors | Vendor sheet 5: the AW9523B I/O expander, the M5-Bus, the LCD and touch connectors, the microSD socket, Grove port A |
| 7 | Power path | Vendor sheet 6: the four ME1502 load switches between USB-C, the M5-Bus and the AXP2101, the bulk capacitors, the mounting holes |
| 8 | Power tree and rails | How power flows from USB-C, the M5-Bus and the battery to every rail, with each part's enable; then every rail's nominal voltage, source, enable and where it is drawn |
| 9 | Nets and signals | Every rail and every net drawn on more than one page with the page/zone of its labels; the ESP32-S3 GPIO map, the AW9523B pins, the I2C addresses, every pull-up and pull-down |
| 10 | Parts | Every part: its value as printed, what it is, its nets (two-pin parts), whether it is fitted, and where it is drawn |

Pages 2 to 7 are the vendor's sheets 1 to 6, one page each, in the vendor's order. Pages 8 to 10 are written by the generator from `netlist.yaml`, not drawn by hand: they cannot disagree with the drawing.

## What it is not

- Not the vendor's design files. The layout, the blocks and every symbol are this project's: the integrated circuits' and connectors' are each board's own (`cores3-se.kicad_sym`), and the passive parts, the diodes, the transistors, the switches, the plain connectors, the pads and the ground symbols are this project's generic ones (`kleidos.kicad_sym`, drawn by `_shared/kicad_schematic.py`). No symbol of KiCad's libraries is in these files. No vendor document is in this repository; the sources are cited below.
- Not a PCB design: no footprints, no part numbers beyond the ones the vendor prints, nothing about placement or routing.
- Not a full datasheet of each part: pin names and values are as the vendor documents them (`10K/1%`, `22uF 6.3V`, `NC` for a part not fitted).

## How to read it

Pins connect by net labels, not by wires. Two pins whose labels carry the same name are on one net, on any page. After a label, each `[3/C4]` names another page that carries the net and the zone of its label there (the border prints columns 1-8 and rows A-F, 50 mm apart): page 3, row C, column 4. Clicking it lands on that label, zoomed in; on a page where the net has several labels, it lands on the one at the part that feeds the rail (`rails.from` in `netlist.yaml`), or else on the first in reading order. A label with none is on its page only. Neighbouring pins of one part on one net share a short bar and one label. A cross on a pin end means the pin is unconnected. Wires and pin lines are one colour and one width, so a connection reads as one line from the part to its label. An amber, bold `K3` marks a Kleidos addition or correction (below): it sits after the label of a pin or net, after the reference of a part, and at the end of a row of the index pages; clicking it leads to its row on page 1, and that row's id leads back to it.

Parts documented as not fitted (value `NC`) carry KiCad's DNP mark: a red cross over the symbol. They are D1, D2, R36, R41, R43, L9, C121 and BAT1.

In the PDF, each box on the contents page opens its page, and every page carries "Contents" and a row of page numbers above the title block. Each part's reference on the drawing is a link to its row in the parts list, and the row's reference and page/zone lead back to the part. Every place in the index pages (a page/zone, a box of the power tree, a reference in a table) is a link to it. The bookmarks list the pages and, under each, its parts or its tables, each at its place. `_shared/check_schematic_links.py` holds every one of those links (`--list` prints them all).

### In any PDF reader

KiCad can give each part a property pop-up, but it is a script that only Acrobat runs, so the export leaves the pop-ups out and the PDF holds no script at all. What they showed (reference, value) and more is in the parts list. The rest is plain PDF that every reader follows:

- a link leads to a page and a position: `/XYZ`, the target placed 30 mm from the window's left edge and 20 mm below its top, at zoom 2. KiCad links a text only to a whole page, so `_shared/schematic_pdf.py` sends each link to its place after the export, from the targets the generator writes into `links.json`;
- each link carries a `/Contents` saying where it leads, for screen readers;
- named destinations open the PDF at a part or at a net's label on a page: `cores3-se.pdf#nameddest=part-U1`, `cores3-se.pdf#nameddest=net-VDD_3V3-p2`.

Numbering and naming, where they differ from the vendor's documents:

- Reference designators are the vendor's. The one exception is the backup cell, printed `BAT1/NC`: it is `BAT1` here, with its value written `NC (XH414HG-IV01E)` so that it carries the DNP mark the "/NC" stands for.
- Nets the vendor left unnamed have names of ours (`AXP_LX1`, `BOOT_RC`, `RTC_BAT`...); `netlist.yaml` lists each under `renamed` with the name Altium generated for it.
- J6's value is printed "HDR4", then the Chinese word for connector, then "-2MM"; it is `HDR4-2MM` here. The ME1502 load switches carry a note in Chinese beside them, "EN active high" (U14, U17) or "EN active low" (U18, U19); the symbols say it in their description and the power tree shows each switch's enable net.
- J1 is drawn with the vendor's pin names (CC1, CC2, DP1, DP2, DN1, DN2) and the vendor's pin identifiers (`VBUS`, `A5`... `GND`, `SHELL`); the VBUS pin, printed `VCC` inside the symbol, shows only its identifier, which keeps the two from overprinting.
- J4, the IPEX connector, is drawn as a box with the vendor's pin names: `A` (pin 1) and `G` (pins 2, 3).

## Source

M5Stack, *CoreS3-SE schematic, Sch_M5_CoreS3_SE_v1.0* (Altium, seven A4 sheets, printed 2025-06-03), <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/498/Sch_M5_CoreS3_SE_v1.0.pdf>, listed on <https://docs.m5stack.com/en/core/CoreS3%20SE>. The vendor's host refused connections from the machine that drew this on 2026-11-17, so the copy the Wayback Machine captured on 2026-05-13 was read (<https://web.archive.org/web/20260513112150/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/498/Sch_M5_CoreS3_SE_v1.0.pdf>), SHA-256 `ff105808b6073ab487c63e0af776418a58bcf386c2b63f97e3083f5698847e2f`.

| Vendor page | Sheet | Its facts are on |
| --- | --- | --- |
| 1 | A2-AXP | page 2 |
| 2 | A3-PSU | page 3 |
| 3 | A4-ESP32S3 | page 4 |
| 4 | A5-AUDIO | page 5 |
| 5 | A6-GPIO | page 6 |
| 6 | A7-POWER_PATH | page 7 |
| 7 | A8-ETC | nothing: every part on it is greyed out (below) |

The connections were taken, pin by pin, from the netlist Altium writes into the same PDF's bookmarks (per sheet: Components with their pins, and Nets with their pins and labels), and checked against the printed sheets; nets with one name on several sheets are one net, as the print's labels make them. The values come from the printed sheets. The I2C addresses of the AXP2101 (0x34), AW88298 (0x36), ES7210 (0x40) and AW9523B (0x58) are printed on the sheets; those of the BM8563 (0x51) and the touch panel's FT6336U (0x38), which the schematic does not print, are additions K1 and K2 (below), also given by the vendor's documentation page as printed on 2024-05-24 (<https://media.distrelec.com/Web/Downloads/_t/ds/K128-SE_eng_tds.pdf>). The GPIO map agrees with the pin map of the vendor's documentation page (read at Switch Science's mirror, `docs.m5stack.switch-science.com/en/core/CoreS3%20SE`, on 2026-11-16).

## Kleidos additions and corrections

The drawing improves on the vendor's print rather than following it to the letter: a detail the print does not show is added when a primary source makes it certain, each one an entry of `kleidos` in `netlist.yaml`, marked on the drawing and listed on page 1. There are 19, all additions; no drawing error of the print was found (every supply and ground pin of every IC is on a net, and the netlist matches the print pin for pin), so there is no correction. The sources in full:

| Id | What the drawing adds | Where it is marked | Source |
| --- | --- | --- | --- |
| K1 | The BM8563 U4 answers at I2C address 0x51. | nets page, I2C table | BM8563 datasheet (as M5Stack hosts it, `board.json` `bm8563-ds`), features list: slave address write A2h, read A3h; the vendor's docs page (2024-05-24 print), p. 8; bench scan [`bench/2026-11-17-i2c-scan.md`](bench/2026-11-17-i2c-scan.md), 2026-11-17 |
| K2 | The touch panel's FT6336U answers at 0x38. | nets page, I2C table | Bench scan [`bench/2026-11-17-i2c-scan.md`](bench/2026-11-17-i2c-scan.md), 2026-11-17; identity registers (FOCALTECH_ID 0x20, CIPHER 0x64) read on a CoreS3 SE on 2026-11-11, Kleidos repository `docs/hardware/introspection/ft6x36.md`, section "2. Register table"; the vendor's docs page (2024-05-24 print), p. 8 |
| K3 | LCD1 carries a 2.0-inch 320x240 IPS panel driven by an ILI9342C (the print shows only the connector). | after LCD1's reference; its parts-list row says so | The vendor's docs page (2024-05-24 print, `m5-docs-2024`): p. 1 ("2.0-inch capacitive touch IPS screen"), p. 5 specifications table (`2.0"@320*240 ILI9342C,SPI Communication`), p. 9 pin map (ILI9342C); the Kleidos firmware drives it as an ILI9342 on this board (`variants/cores3_se/variant.h` (`DISPLAY_TYPE_ILI9342`, `DISPLAY_WIDTH`, `DISPLAY_HEIGHT`)) |
| K4 | LCD1 pin 7, on SPI_MISO (GPIO35), is the panel's D/C input: GPIO35 is both the bus's MISO and the panel's D/C. | after the label of LCD1 pin 7 | The vendor's docs page (2024-05-24 print), pp. 8-9: ILI9342C "DC" on GPIO35, beside the card's SPI_MISO; ILI9342C datasheet 7.5.2 (D/CX); the firmware drives GPIO35 as D/C only while it holds the bus, and the panel renders (`variants/cores3_se/variant.h` (`PIN_DISPLAY_MISO`, `PIN_DISPLAY_CS`, `PIN_DISPLAY_DC`)) |
| K5 | An RTC alarm or countdown on AXP_WAKEUP (the BM8563 INT on the AXP2101 IRQ, both open drain) holds the IRQ low and switches the board on; the line reaches no ESP32-S3 pin. | after every AXP_WAKEUP label | Bench, 2026-10-07: after a soft power-off woken by the BM8563 countdown (`PMICOFFTEST`), the AXP2101 power-on source register 0x20 read 0x02 (IRQ pin), recorded in the Kleidos firmware repository, `docs/hardware/introspection/axp2101.md`, "Power-on and power-off source (`0x20`, `0x21`)"; AXP2101 datasheet V1.0, 6.5.4.2 (IRQ low for more than 16 ms powers on) |
| K6 | U7 (printed "ESPSRAM") is 8 MB (64 Mbit) quad-SPI PSRAM. | after U7's reference; its parts-list row says so | The vendor's docs page (2024-05-24 print), p. 1 and specifications ("16MB FLASH and 8MB PSRAM"); bench [`bench/2026-11-17-efuse-strap-flash-psram.md`](bench/2026-11-17-efuse-strap-flash-psram.md), 2026-11-17: 8 MB found and tested in quad mode at 80 MHz, and the eFuses show no PSRAM in the package |
| K7 | FLASH_VCC is 3.3 V (the print allows 3.3 or 1.8 V): the GPIO45 strap reads 0 and no eFuse forces VDD_SPI. | power page, rails table | Bench [`bench/2026-11-17-efuse-strap-flash-psram.md`](bench/2026-11-17-efuse-strap-flash-psram.md), 2026-11-17: `VDD_SPI_FORCE` 0, `VDD_SPI_TIEH` 0, GPIO45 low on its pull-down alone, esptool "Flash voltage set by a strapping pin: 3.3V"; ESP32-S3 datasheet v2.2, Table 3-1 and 3.2 |
| K8 | GPIO45 has no external pull: the chip's weak pull-down makes the VDD_SPI strap 0 (3.3 V). | nets page, ESP32-S3 GPIO table | ESP32-S3 datasheet v2.2, Table 3-1 and 3.2; the print draws no pull on it; bench as K7 (`pu=0 pd=1 level=0`) |
| K9 | GPIO46 has no external pull: the weak pull-down holds the strap at 0, as download boot (GPIO0 low) needs. | nets page, ESP32-S3 GPIO table | ESP32-S3 datasheet v2.2, Table 3-1 and 3.1; bench as K7 (`pu=0 pd=1 level=0`) |
| K10 | GPIO0 also has the chip's weak pull-up beside R4; high at reset boots from flash. | nets page, ESP32-S3 GPIO table | ESP32-S3 datasheet v2.2, Table 3-1 and 3.1 |
| K11 | GPIO3 (LCD_CS, R49 pull-up) is the JTAG-source strap, read only when the STRAP_JTAG_SEL eFuse is set. | nets page, ESP32-S3 GPIO table | ESP32-S3 datasheet v2.2, Table 3-1 and 3.4 |
| K12 | U10 RSTN (pin 23, on AXP_PG) resets the AW9523B while low and has an internal 100 kohm pull-down: the expander is reset whenever the ESP32-S3 is (power-up, reset key). | after the label of U10 pin 23 | AW9523B datasheet V1.5, pin description, pin 23 |
| K13 | VCC_BL (DLDO1) is fed inside the AXP2101 from DC-DC 1 (VDD_3V3), 0.5 to 3.3 V set over I2C. | power page, rails table | AXP2101 datasheet V1.0, features list ("DLDO1/2 ... 0.5~3.3V") and the DLDO1 electrical table ("VIN input is DCDC1") |
| K14 | BUS_5V is 5.03 V: R11 15K over R12 4.7K on the SY7088's 1.2 V feedback. | power page, rails table | SY7088 datasheet, FB pin description (VOUT = 1.2 V x (RH/RL + 1)) and VREF 1.182-1.218 V |
| K15 | U14's current limit is about 1 A (60 kohm / R17 60K). | after U14's reference; its parts-list and power-tree box say so | ME1502 datasheet V02, pin 3 (Ioc = 60K/Rset) |
| K16 | U17's current limit is about 1 A (60 kohm / R44 60K). | after U17's reference | as K15 |
| K17 | U18's current limit is about 2 A (60 kohm / R45 30K). | after U18's reference | as K15 |
| K18 | U19's current limit is about 2 A (60 kohm / R46 30K). | after U19's reference | as K15 |
| K19 | U2's output is open collector: it can only pull ESP_BOOT low, R4 10K pulls it up, and LED2 lights while it pulls. | after the label of U2 pin 4 | Texas Instruments LMV331 datasheet SLCS136V (revised May 2025), 1 Features ("Open-collector output") and Table 4-1 (OUT is pin 4 of the 5-pin package) |

## Open questions

What no primary source settles yet stays out of the drawing:

- **FB1, FB2:** the ferrite beads' value; nothing in the vendor's documents, and the beads carry no marking. Needs the board opened.
- **RTC_VDD (AXP2101 VRTC):** its voltage. The datasheet gives RTC-LDO1 a 1.8 V default but lets it be customized to 1.8, 2.5, 3 or 3.3 V in the factory, so M5Stack's part may differ. Needs a probe at C16 or R15 with the board opened.
- **U6's maker:** the owner's unit answers with JEDEC manufacturer 0x46, device 0x4018 (128 Mbit, as printed), which is neither GigaDevice (0xC8) nor Winbond (0xEF), the two parts the print names; ESP-IDF's probe agrees ([`bench/2026-11-17-efuse-strap-flash-psram.md`](bench/2026-11-17-efuse-strap-flash-psram.md)). The connections do not change (same capacity, pins and supply), so U6 keeps the printed value; which part is fitted needs the case opened to read its marking.
- **What the power path does before the firmware runs:** the AW9523B's power-on state is settled by its datasheet V1.5 (`board.json` `io-expander`): with AD0 and AD1 on GND every pin starts as an output at 0 (Table 1), and P0 starts open drain (Table 10, GCR bit 4 = 0), so it drives that 0 low; P0_0, P0_1, P0_2 and P0_5 have no pull on the board. Read against the ME1502 enables, that leaves U18 and U19 (EN active low) on and U14, U17 and the SY7088 (enable high) off until the firmware's first write. It is not drawn: the power tree states no default, and bench probe P4 (BUS_OUT on Grove pin 3 with the reset key held) has not been run to confirm it.
- **The AXP2101's powered-off current:** the datasheet V1.0 cited here gives two figures, under 20 uA in its features list (BATFET off, RTCLDO on) and typically 40 uA in 6.5.4 (off, only a battery present); the Kleidos firmware cites "V1.4, 6.5.4" for under 40 uA, the second figure, under another revision label. Which applies to this board needs a measurement at the cell; neither is drawn.
- **Part numbers:** the keys S1, S2, the battery behind J5, and the LCD and touch modules behind LCD1 and CTP1.
- **The strapping register's layout (not a drawing question):** on this board GPIO_STRAP_REG reads 0x20. esptool v5.3.1 takes bit 4 as the VDD_SPI strap (0 here), ESP-IDF 6.0.3 `esp_hw_support/port/esp32s3/rtc_init.c:232` bit 5 (set here, which on this board cannot be GPIO45 and fits GPIO3 pulled up by R49). K7 and K8 rest on the eFuses, the pad's reading and esptool's flash-voltage report, not on that bit.

## What is left out, and why

- **The greyed-out parts.** The print greys out, with Altium's compile mask, the camera connector J2 (AFC34-S24FIA-00) with its oscillator X2 and C101, C114, C115, R31, R37, C77, C78 (vendor page 5); the MPU6886 IMU U16 with C80, C98, C100 (page 2); and the whole of page 7: the BMI270 U15, the BMM150 U20, R50, C40, C43, C47, C79 and two 15K resistors printed without a designator. None of them is in the bookmark netlist: they are not part of the SE's compiled design, and they are not drawn. The vendor's documentation page agrees: its comparison table gives the SE no camera, no IMU and no magnetometer.
- **What the camera's nets leave behind.** The ESP32-S3 pins the print labels `CAM_D2` to `CAM_D9`, `CAM_HREF`, `CAM_PCLK`, `CAM_VSYNC` (GPIO15, 16, 38 to 42, 45 to 48) and the AW9523B pin labelled `CAM_RST` (P1_0) keep their labels here, each on one pin with nothing else on it, as the SE's netlist has them. The rails `VDDCAM_3V3`, `AVDD` and `DVDD` keep only their capacitors. KiCad's ERC warns on a label that reaches one pin, so that check (`isolated_pin_label`) is switched off for this board in `layout.yaml` (`erc_ignore`); the labels are the vendor's.
- **The speaker.** The amplifier's outputs end at the ferrite beads FB1 and FB2 (nets `SPK_VON`, `SPK_VOP`); the print shows no speaker and no speaker connector, so neither is drawn.
- **Values the print leaves out.** FB1 and FB2 carry no value (`not printed`). The output voltages of the AXP2101's BLDO1 (`AVDD`), BLDO2 (`DVDD`) and VRTC (`RTC_VDD`), of the AW88298 boost (`AW_PVDD`) and of the ES7210's microphone bias are not printed and are given as `not printed`: all but VRTC are set over I2C by the host, so they have no fixed nominal, and VRTC's is open (below). DLDO1 (`VCC_BL`) carries its datasheet range (K13). Part numbers the print leaves out: the keys S1, S2 (only their footprint names), the battery behind J5, and the panel modules behind LCD1 and CTP1, whose driver and touch controller are additions K3 and K2.
- **The print's own notes.** Beside the AXP2101's IRQ, SDA and SCL the sheet prints "I2C NEED REVERSED"; the connections are drawn as the netlist has them (SDA on pin 39, SCL on pin 40), which the AXP2101 datasheet's pin table agrees with (Table 4-1: 38 IRQ, 39 SDA, 40 SCK), and the note is recorded in `netlist.yaml`. Beside GPIO45 it prints "VSPI: 0=3.3V 1=1.8V" and beside U0TXD/U0RXD "UART_PRINT"; both are recorded there too (on this board the GPIO45 strap reads 0, so VDD_SPI is 3.3 V: K7, K8).
- **The battery.** The vendor's comparison table gives the SE no battery; J5 and M5-Bus pin 30 carry `VBAT` for one, and that is what is drawn.
- **Inside the parts.** The AXP2101's charger, regulators and power path, the ESP32-S3's internals and the touch panel's controller are not on the schematic; only their pins are.

## Files

| File | What it is | Edited by |
| --- | --- | --- |
| `netlist.yaml` | The facts: every component, its value, the vendor's page, each pin and its net; rails (with their nominal voltage), I2C, ESP32-S3 GPIO map, AW9523B pins (`pmic_gpio`), every pull-up and pull-down | hand (review here) |
| `layout.yaml` | How it is drawn: our symbols, which symbol each part takes, the sheets, blocks and rows, the power tree's boxes and arrows, the revision history | hand |
| `cores3-se.kicad_sch` + nine child `.kicad_sch`, `cores3-se.kicad_sym`, `cores3-se.kicad_pro`, `sym-lib-table` | The KiCad project | generated |
| `links.json` | Where each link of the PDF lands, the named destinations and the bookmarks, for `_shared/schematic_pdf.py` | generated |
| `cores3-se.pdf` | The pages | generated |
| `svg/` | One SVG per page, written by the export when it runs; not kept in git | generated |

## Regenerate and check

```bash
.venv/bin/python _shared/kicad_schematic.py cores3-se   # KiCad files from netlist.yaml + layout.yaml
.venv/bin/python _shared/export_schematic.py cores3-se  # ERC, netlist check, PDF (+ links), SVGs, link check
.venv/bin/python _shared/check_schematic_links.py cores3-se --list   # every link of the PDF and where it lands
.venv/bin/python -m pytest tests/test_schematic.py
```

The export fails unless the ERC reports nothing (0 errors, 0 warnings; besides the two library checks every board switches off, this board switches off `isolated_pin_label`, above), `check_schematic.py` finds every vendor pin on the net `netlist.yaml` names, every SVG has the theme's background and the one line width, and `check_schematic_links.py` finds every link of the PDF leading where it should.
