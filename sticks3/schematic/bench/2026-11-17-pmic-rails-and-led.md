<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# B2 and B5, the halves the console can do: the LED switch and the M5PM1's rail readings (2026-11-17)

Probes B2 and B5 of `../improvements.md` both need a person at the bench: B2 a look at the LED's color, B5 a multimeter on the HAT2 header. Neither was available. This record is what the firmware can read instead, on an open StickS3 on the bench hub's USB, case closed, nothing opened.

Firmware: Kleidos `sticks3_debug`, built from the firmware of 2026-11-17 (ELF SHA-256 prefix `13cf0d745130259a`). Register meanings: the regmap in Kleidos `src/drivers/power/py32_pmic_regmap.h` for POWER_CONFIG, and the vendor library for the ADC (m5stack/M5PM1, `src/M5PM1.h:225-230`, commit `315d2899c`: VBAT 0x22/0x23, VIN 0x24/0x25, 5VINOUT 0x26/0x27, all in mV).

## B2: the LED switch

`PERIPH! ON LED` then `REGR m5pm1 POWER_CONFIG` read `0x17` (`led_enable_level=1`); `PERIPH! OFF LED` then the same read gave `0x07`. The M5PM1 takes and holds the LED bit. The color was not seen: the Mac's only cameras face the user, not the board.

## B5: the rails the M5PM1 measures

| PMIC pin (net on the print) | Divider on the print | ADC register | Reading |
| --- | --- | --- | --- |
| 11 `VBAT_ADC` | R23/R24 | VBAT 0x22/0x23 | 3,990 to 4,194 mV over the session (the cell; `PMIC?` agrees) |
| 16 `5VIN_ADC` (from `5VIN_L0`) | R19/R20 10K/10K | VIN 0x24/0x25 | 5,178 to 5,220 mV with USB in |
| 19 `EXT_5V_ADC` (from `GROVE_5V`) | R21/R22 10K/10K | 5VINOUT 0x26/0x27 | 5,102 to 5,108 mV with EXT5V on; 904 to 970 mV with it off |

## What it proves

- B2: the LED is switched by the M5PM1's POWER_CONFIG bit 4, as the print has LED1 driven from the M5PM1 (pin 5, through Q3), not from an ESP32-S3 pin (improvements.md W3). A5's color stays as the vendor's docs page gives it; the bench adds nothing to it.
- B5, partly: with EXT5V on, GROVE_5V (the HAT2 5 V pins J2.6 and J2.8, and the Grove port) sits at about 5.1 V by the M5PM1's own ADC, so the boost and U8 deliver the printed 5 V. `5VIN_L0` sits at about 5.2 V with USB in. These are readings through the board's own dividers and the M5PM1's ADC, not a meter on the header.
- Still open: the 3V3 pin of the HAT2 header (D9, 3V3_L2) has no ADC path the firmware can read, and the multimeter readings B5 asks for were not taken.
