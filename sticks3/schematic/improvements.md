# M5StickS3 schematic: improvements triage

Triage of 2026-11-17 under the owner's rule of that day (AGENTS.md, "Schematics"): a detail the vendor's print leaves out goes in when a primary source makes it certain, a drawing error of the print is corrected when the evidence settles it, and each one becomes an entry of `kleidos` in `netlist.yaml`. Firmware citations are to the Kleidos firmware repository.

Applied on 2026-11-17 as `kleidos` K1-K11 in `netlist.yaml` (README.md, "Kleidos additions and corrections"): D1 → K1 (a correction on the rail `5VIN_L0`); A3 → K2-K7 (`GPIO26`, `GPIO33` to `GPIO37`); F4 → K8 (`PYG0`, from bench B3); F1 → K9, F2 → K10, F3 → K11 (the three I2C addresses, with bench B1 as second citation). Also applied, with no entry because the drawing already agrees or the fact is printed: A1 and A2 (the CJ3439KDW and VSOP383.. datasheets now cited in `netlist.yaml` and README.md), A4 (U104's value now carries the rating printed on vendor page 1), A6 (J3's value is the print's `CON4`; HY2.0-4P is in the part's note and the README), the netlist note on LED1 (A5), E1 to E7 and F4, D6 in `board.json`. Not applied: everything marked no element fits, stays out or open (A5's colour, settled since by the owner's observation of 2026-11-17 but with no element to carry it, A7-A10, F9, the internal pull-ups of D4 and D6, D5's conflict, D8, D9), the optional D3 and D7, X2 (a README mention only), and W1-W5, which are for the Kleidos firmware repository; README.md, "Open questions", lists the open ones.

Status words: **K addition** / **K correction** (settled, ready to become an entry, with the element named); **no entry** (settled, nothing in the drawing differs from the print, at most a README or netlist text change); **no element fits** (settled, but every element kind the generator has would misdraw it, for example a `part` or `pin` addition dots wires the print does show); **needs bench** (a probe from the list at the end settles it); **stays out** (cannot be settled without opening the board, or no primary source exists); **board.json** / **Kleidos** (a disagreement to fix there, not in the drawing).

## Sources read for this triage

- Vendor print: K150 StickS3 schematic V0.6, the Wayback copy the README cites, SHA-256 `e5272c97…0226` (matches the README).
- Vendor docs page: docs.m5stack.com/en/core/StickS3, read at the Switch Science mirror on 2026-11-17 (PinMap, specifications, "Download Mode").
- M5PM1 Chip User Manual V1.9 (github.com/m5stack/M5PM1, docs/M5PM1_Datasheet_EN.pdf).
- ESP32-S3-PICO-1 Series Datasheet v1.2 (documentation.espressif.com/esp32-s3-pico-1_datasheet_en.pdf).
- Bosch BMI270 datasheet BST-BMI270-DS000-08, revision 1.6 (bosch-sensortec.com).
- Everest ES8311 datasheet, revision 10.0, January 2021 (read at files.waveshare.com/wiki/common/ES8311.DS.pdf).
- Awinic AW329XX (AW32901) datasheet V1.1, September 2018 (LCSC copy, C401023).
- Awinic AW8737A datasheet V1.2, July 2022 (awinic.com lists it; read at an ickey.cn copy).
- JCET CJ3439KDW datasheet, revision D, March 2016 (LCSC copy, C99824).
- Vishay VSOP383.. datasheet, document 82748, revision 1.6, 2026-02-09 (vishay.com/docs/82748/vsop383.pdf).
- Not found: an LGS4056 datasheet (only TP4056-family clones), a JW5712 datasheet.

No separate verifier notes for this board were found (boards history, scratch folders); the recorded doubts are the README's "What the schematic does not say", its firmware table and the notes in `netlist.yaml`.

## (a) Gaps and doubts the README and netlist record

| Id | Claim | Evidence | Status |
| --- | --- | --- | --- |
| A1 | Q2 CJ3439KDW: pins 1 S, 2 G, 6 D are the N-channel and pins 3 D, 4 S, 5 G the P-channel, as drawn | CJ3439KDW datasheet rev D p.1, equivalent circuit: N-ch CJ3134K on S1(1) G1(2) D1(6), P-ch CJ3139K on D2(3) S2(4) G2(5) (arrow directions read at 400 dpi) | no entry: the drawing already agrees; README line 136 drops "the datasheet was not read" and cites the sheet |
| A2 | U101 VSOP38338 is an 8-pin receiver IC with an IN pin for an external photodiode (U102), as the vendor draws it | VSOP383.. doc 82748 rev 1.6 p.1 ("for use ... together with a photo pin diode") and p.2 pinning: 1, 4, 5 N.C., 2 VS, 3 OUT, 6, 8 GND, 7 IN | no entry: drawing agrees; README line 135 cites the datasheet |
| A3 | GPIO26 (U20 pin 28, SPICS1) and GPIO33 to GPIO37 (pins 38 to 42) are wired inside the N8R8 package to its Octal PSRAM and are not available | ESP32-S3-PICO-1 datasheet v1.2, Table 2-1 note 4, p.13 ("For ESP32-S3-PICO-1-N8R8, SPICS1 and GPIO33 ∼ GPIO37 are connected to the Octal SPI PSRAM and are not available for other uses") | K addition ×6: `{gpio: GPIO26}`, `{gpio: GPIO33}` … `{gpio: GPIO37}`, source datasheet; README line 137 then names them |
| A4 | U104's rating: 8 Ω, 1 W | the print's own page 1: "SPK 扬声器8Ω @ 1W"; docs page "8Ω@1W 2011 cavity speaker" | no entry: printed on page 1, so it is a plain value for U104 in `netlist.yaml` (today "SPK (2-pin speaker connector)") |
| A5 | LED1 is green | docs page, "Download Mode": "Press and hold the power button until the green LED blinks"; the print names no colour; Kleidos `src/hal/common/power_manager_m5_pm1.cpp` (`PowerManagerM5PM1::init`) says green (a comment, not a test). **Settled 2026-11-17: green, and it sits inside the case (owner observed on his unit, 2026-11-17)** | colour settled (board.json `led-status`); still no element fits: a `part` addition would dot LED1's printed wires; needs a value-only marker in the generator, else README only; B2 on 2026-11-17 confirmed the M5PM1 switches it (POWER_CONFIG bit 4) (`bench/2026-11-17-pmic-rails-and-led.md`). For the regeneration step: LED1's note in `netlist.yaml` and schematic/README.md's two "LED1's colour" open items still say nobody looked; they can now cite the owner's observation |
| A6 | J3's part "HY2.0-4P" | the print says only "CON4"; the docs page says "HY2.0-4P interface"; `netlist.yaml` J3 value "CON4 (Grove, HY2.0-4P)" | no element fits: this is already a silent difference from the print; either keep the value to "CON4" and list HY2.0-4P in the README, or add the value-only marker A5 needs |
| A7 | Part numbers the print leaves out: J2, J4, L2, S1 to S3, Q101, U102 | no vendor document names them | stays out: listed open |
| A8 | TP7 is absent from the print's numbering | print | stays out: listed open |
| A9 | The second daughterboard, StickS3_PRJ_Lite_FPC_V1.0 (an LED in place of the IR parts), is in the PDF bookmarks only | vendor's Altium bookmark netlist; no printed page, no values | stays out unless the owner wants a bookmark-only board drawn; listed open |
| A10 | Which daughterboard a given unit carries | none | stays out, open: B4 on 2026-11-17 read GPIO42 low at idle with GROVE_5V at 5.1 V, which a fitted receiver (D6) and an absent one both give; settling it needs a meter on HAT2 pin 17 or a remote (`bench/2026-11-17-ir-rx-gpio42.md`) |

## (b) Facts the firmware relies on that the drawing lacks

| Id | Claim | Evidence | Status |
| --- | --- | --- | --- |
| F1 | The M5PM1 U16 answers at I2C 0x6E | M5PM1 manual V1.9 §I.2 (4), p.1 ("address 0x6E"); docs PinMap "M5PM1 (0x6e)"; Kleidos `variants/sticks3/variant.h` (`PMIC_I2C_ADDR`), read back on a StickS3 (`docs/hardware/introspection/m5pm1-py32.md`, section "5. Console usage") | K addition `{i2c: U16}`, source vendor-doc (manual) with the firmware as second citation; bench B1 confirmed it on 2026-11-17 (`bench/2026-11-17-i2c-scan-l3b.md`) |
| F2 | The BMI270 U17 answers at 0x68 and runs in I2C mode | BMI270 datasheet rev 1.6 §6.5 p.128 (0x68 with SDO to GND) and §6.3 p.123 with Table 17 p.122 (CSB tied to VDDIO selects I2C); the print has SDO (pin 1) on GND and CSB (pin 12) on 3V3_L1; `variants/sticks3/variant.h` (`IMU_I2C_ADDR`), measured on a StickS3 (`docs/hardware/introspection/bmi270.md`, section "The NVM-backed registers") | K addition `{i2c: U17}`, source datasheet; bench B1 confirmed it on 2026-11-17 (`bench/2026-11-17-i2c-scan-l3b.md`) |
| F3 | The ES8311 U18 answers at 0x18 | ES8311 datasheet rev 10.0 §5, p.8 ("The chip address must be 0011 00x, where x equals CE"); the print has CE (pin 20) on AGND; `variants/sticks3/variant.h` (`AUDIO_CODEC_I2C_ADDR`) | K addition `{i2c: U18}`, source datasheet; bench B1 confirmed 0x18 on 2026-11-17, and that it leaves the bus when PYG2 drops L3B and returns with it (`bench/2026-11-17-i2c-scan-l3b.md`) |
| F4 | PYG0 reads low while U15 charges the cell | Kleidos `src/drivers/power/py32_pmic.cpp` (`Py32Pmic::readCharging`) and `src/drivers/power/py32_pmic_regs.h` (`kGpio0ChargingStatusMask`) (0 = charging); no LGS4056 datasheet found | K addition `{gpio: PYG0, table: "M5PM1 GPIO (U16)"}`, source bench: B3 on 2026-11-17 read PYG0 = 0 in every charging window (cell voltage stepping up, VIN dipping) and 1 otherwise, with USB in (`bench/2026-11-17-charge-status-pyg0.md`) |
| F5 | GPIO13 (PYG1_IRQ) has no pull resistor; the firmware turns on the ESP32-S3's internal pull-up | `src/hal/common/power_manager_m5_pm1.cpp` (`PowerManagerM5PM1::init`); the print has no resistor on the net | no entry: firmware configuration, not connectivity; the README firmware table already says so |
| F6 | PYG2 enables L3B (the panel stays dark without it) | `src/hal/common/power_manager_m5_pm1.cpp` (`PowerManagerM5PM1::init`); print sheets 2 and 3, Altium netlist, docs PinMap | no entry: printed; see X2 for the print's page-1 label |
| F7 | BMI270 INT1 reaches GPIO13 through PYG4 and the M5PM1's IRQ line | `variants/sticks3/variant.h` (`HAS_IMU`, `IMU_TYPE_QMI8658`, `IMU_TYPE_BMI270`, `IMU_I2C_ADDR`); print | no entry: printed |
| F8 | The IR LED is driven active high from GPIO46 | `variants/sticks3/variant.h` (`PIN_IR_TX`, `IR_TX_ACTIVE_HIGH`); print (Q101, R101 10K gate pull-down) | no entry: printed |
| F9 | The panel on J6 is an ST7789P3, 1.14 inch, 135 × 240 | docs page specifications and PinMap; `variants/sticks3/variant.h` (`DISPLAY_TYPE_ST7789`, `DISPLAY_WIDTH`, `DISPLAY_HEIGHT`) drives it | no element fits: J6 is the connector and a `part` addition dots its printed wires; README note, or the value-only marker of A5 |
| F10 | J6 pins 6 and 8 carry the main I2C bus to the LCD flex; nothing known uses them | print | no entry: B1 on 2026-11-17 found no I2C device on the bus beyond 0x18, 0x68 and 0x6E (scan 0x08 to 0x77) with the panel's rail up (`bench/2026-11-17-i2c-scan-l3b.md`); what the flex does with the pins stays unknown; the drawing stays as printed |

## (c) Datasheet facts the print omits

| Id | Claim | Evidence | Status |
| --- | --- | --- | --- |
| D1 | U7 AW32901 with OVLO on GND (R8 0R, R7 not fitted) trips at its default 5.95 V (5.83 to 6.07 V rising, 130 mV hysteresis), not at 5 V | AW329XX datasheet V1.1, p.1 (default 5.95 V), p.2 table (VIN_OVLO), p.4 note 2 ("connect OVLO pin to GND directly or through a 0Ω resistor") | K correction `{rail: 5VIN_L0}`, vendor: "the print writes OVP = 5V", source datasheet; no bench (it needs more than 6 V on USB) |
| D2 | U19 AW8737A pin D3 PVDD is the charge-pump output, not a supply input | AW8737A datasheet V1.2, p.3 pin description | no entry: the drawing already has it on its own net (U19_PVDD, C37); see E2 |
| D3 | U19's ~SHDN is a one-wire pulse control (the pulse count selects the mode) | AW8737A datasheet V1.2, p.3 | no entry proposed: the printed net name PYG3_SPK_Pulse already says it; an optional `{gpio: PYG3}` addition carries little |
| D4 | The M5PM1 enables an internal pull-up on PWR_BTN (pin 7), beside R17 | M5PM1 manual V1.9, Table 1 p.2 and Table 2 p.3 | no element fits: an internal pull has no part, and a `pin` addition would dot a printed wire; README note, or a generator decision |
| D5 | The M5PM1 manual calls pin 1 BAT_ADC_EN a push-pull output; the print names it BAT_ADC_EN_OD | manual Table 1 p.2 against the print's symbol | stays as printed: two vendor documents disagree on a firmware-set pad; the README lists the conflict |
| D6 | VSOP38338's output has an internal 33 kΩ pull-up to VS; through R106 10K and R105 20K the idle level at GPIO42 is about 5 V × 20/63 ≈ 1.6 V, below the ESP32-S3's VIH of 0.75 × 3.3 V ≈ 2.5 V | VSOP383.. doc 82748 rev 1.6, p.1 block diagram; ESP32-S3-PICO-1 datasheet v1.2, Table 3-4, p.18 | the pull-up: no element fits (README note); its consequence on GPIO42: B4 on 2026-11-17 read the line low in 150 of 150 reads with GROVE_5V at 5.1 V, as predicted (`bench/2026-11-17-ir-rx-gpio42.md`); the 1.6 V itself is not measured |
| D7 | Strap defaults: GPIO45 has a weak pull-down that keeps VDD_SPI at 3.3 V (nothing on G45_LCD_RS pulls it up), GPIO46 a pull-down, GPIO3 floats | ESP32-S3-PICO-1 datasheet v1.2, Table 2-2 p.14 and Table 2-5 p.15 | not proposed: the print already marks each [strap]; optional `{gpio: GPIO45}` addition |
| D8 | LGS4056: CHRG is open-drain, TEMP on GND disables the thermistor, PROG 4.7K against the printed 190 mA | no LGS4056 datasheet found | stays out; F4's bench probe settles the one fact the drawing could use |
| D9 | JW5712: VSEL1 to VSEL3 tied high select 3.3 V | no datasheet found; the net name 3V3_L2 is printed | stays out (nothing to add); B5's meter reading of the HAT2 3V3 pin was not taken (no meter at the bench) and the firmware has no ADC path to 3V3_L2: open |

## (d) Drawing errors of the print

| Id | Claim | Evidence | Status |
| --- | --- | --- | --- |
| X1 | No junction dot missing, no net mislabelled on sheets 2 to 4 | README: the printed pages and the Altium netlist in the PDF's bookmarks agree everywhere | none found; a fresh visual junction pass of the four pages was not repeated here |
| X2 | The print's page 1 names PYG2 "SPK_EN" (and PYG1 L3B_EN) in its audio block and draws a PMOS for LCD_BL; sheets 2 and 3, the Altium netlist and the docs PinMap give PYG2 = L3B enable and Q6 N-channel | print p.1 against pp.2 and 3; Kleidos `src/hal/common/power_manager_m5_pm1.cpp` (`PowerManagerM5PM1::init`) | no correction: the drawing does not reproduce page 1; the README can mention the page-1 inconsistency |

## (e) Where board.json disagrees with the evidence

| Id | Claim in board.json | Evidence | Status |
| --- | --- | --- | --- |
| E1 | `load-switch-aw35122`: "U5 OUT (A1): 3V3_L3B (C7, C14 1 uF)" | `netlist.yaml`: C7 is on 3V3_L2 (U5's input side), C14 on 3V3_L3B | board.json was wrong; applied to `board.json` on 2026-11-17 (C14 on the output, C7 on the input) |
| E2 | `audio-amp`: supply "VBUS_L0 (VDD and PVDD; C36/C37 22 uF)" | PVDD is the charge-pump output (D2); only VDD (A3, B3) and C36 are on VBUS_L0, C37 is on U19_PVDD | board.json was wrong; applied to `board.json` on 2026-11-17 (VDD on VBUS_L0, PVDD on its own net) |
| E3 | `usb-ovp`: `"ovp_v": 5` | default threshold 5.95 V with OVLO grounded (D1); the vendor's "OVP = 5V" belongs in the notes | board.json was wrong; applied to `board.json` on 2026-11-17 (5.95 V, the vendor's figure in the notes) |
| E4 | `microphone`: "MIC1_N is tied to AGND through R26 0R" | `netlist.yaml`: AGND, R26, U21 pin 3, R49, MIC1_N: two 0R in series | board.json's wording; applied to `board.json` on 2026-11-17 |
| E5 | `pmic`: "BAT_ADC_EN_OD (pin 1)" | the manual says push-pull (D5) | applied to `board.json` on 2026-11-17 (the conflict is noted) |
| E6 | `mosfet-cj3439kdw`: "dual MOSFET (Q2A, Q2B)", no channel types | N + P per the datasheet (A1) | applied to `board.json` on 2026-11-17 (the types and pins) |
| E7 | The daughterboard parts use the vendor's designators (U1 to U4, R2 to R6, Q1, CN1, CN2) | the schematic numbers them +100 (README "Numbering") | applied to `board.json` on 2026-11-17 (a mapping note on each part) |

## Bench probes

All are read-only console commands over USB on an open StickS3 running `sticks3_debug` (never a `_secure` env, never a hardened unit), with the case closed; none needs the board opened.

| Id | Probe | Expected | Settles | Result (2026-11-17) |
| --- | --- | --- | --- | --- |
| B1 | `I2C?` at HOME (L3B up); then switch L3B off with `PERIPH OFF` on the role whose reply names PYG2, scan again, switch it back on | 0x18, 0x68, 0x6E and nothing else; 0x18 gone with L3B off | F1, F2, F3 (bench as second source), F10, the Q4/Q5 isolator | done: no `PERIPH` name drives PYG2, so L3B was dropped with `REGW! m5pm1 GPIO_OUTPUT 0x02` after `PERIPH OFF PANEL` (the firmware's own sleep-path write) and put back to the read `0x06`. L3B up: 0x18, 0x68, 0x6E only; L3B down: 0x68, 0x6E, bus still idle high; back up: all three. F1 to F3 confirmed, the codec is on L3B and does not hold the bus when unpowered, nothing else answers on J6's pins. `bench/2026-11-17-i2c-scan-l3b.md` |
| B2 | `PERIPH ON LED`, look at the front, `PERIPH OFF LED` | a green LED | A5 | done: the M5PM1 takes and holds the LED bit (POWER_CONFIG `0x17` on, `0x07` off), `bench/2026-11-17-pmic-rails-and-led.md`; the colour, which no one was at the bench to see, is green (owner observed on his unit, 2026-11-17), the LED inside the case |
| B3 | With a cell below full: USB in, `PMIC?` and `REGR m5pm1 GPIO_INPUT`; USB out, repeat | bit 0 = 0 and "charging" with USB in; bit 0 = 1 with USB out | F4 | done, USB-in half: the cell was run down to about 4.0 V with the hub's VBUS cut, then every window where PYG0 read 0 showed the cell voltage stepping up 30 to 40 mV and VIN dipping about 30 mV, and PYG0 read 1 when charging stopped (also at full). F4 settled (0 = charging). The USB-out read cannot be taken (the console goes with VBUS) and is not needed. `bench/2026-11-17-charge-status-pyg0.md` |
| B4 | `PERIPH ON EXT5V`; `GPIO? 42 IN` several times with no remote; again while holding a TV remote's key at the IR window; `PERIPH OFF EXT5V` | an idle level of 0 (D6's 1.6 V) or 1, and toggling under the remote if the IR daughterboard is fitted | A10, D6 | half done: GROVE_5V 5.10 V by the M5PM1's ADC with EXT5V on; GPIO42 read 0 in 150 of 150 reads, as D6 predicts. No remote at the bench, so A10 stays open (a fitted and an absent receiver both read 0). `bench/2026-11-17-ir-rx-gpio42.md` |
| B5 | Multimeter on the outside HAT2 header: 3V3 pin, BAT pin, and the 5V-out pin with `PERIPH ON EXT5V` | about 3.3 V, the cell voltage, about 5.0 V | D9 (3V3_L2), BOOST_OUT's printed 5.0 V divider | open: no multimeter at the bench. Through the M5PM1's own ADC and the printed dividers: GROVE_5V 5.10 V with EXT5V on, 5VIN_L0 5.2 V on USB, the cell 4.0 to 4.19 V; 3V3_L2 has no ADC path. `bench/2026-11-17-pmic-rails-and-led.md` |

Not probed on purpose: D1's 5.95 V threshold (it needs more than 6 V on the USB input).

Bench run of 2026-11-17: the StickS3 listed in the Kleidos QA inventory (open, unburned USB-JTAG), never the hardened bench unit; firmware Kleidos `sticks3_debug`, built from the firmware of 2026-11-17 (ELF SHA-256 prefix `13cf0d745130259a`), left flashed on the board, with the M5PM1's LED, 5 V output, charge enable and GPIO registers back at the values read before the probes. Side observation from B3, not part of any entry: the charger stopped more than once with the cell at about 4.03 to 4.05 V, below full; the cause needs the LGS4056 datasheet or a longer run.
