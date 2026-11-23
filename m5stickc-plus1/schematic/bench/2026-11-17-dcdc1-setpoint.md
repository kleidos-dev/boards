<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# DC-DC1 (VESP_3V3) setpoint (probe P6, register half)

Bench probe of 2026-11-17 on the M5StickC Plus 1.1 (K016-P), USB connected, the case closed. It addresses triage item C6 (`../improvements.md`).

## Firmware

The `m5stickc_plus1_debug` image found on the board (`VER?`: version 0.1.0, `elf_sha=281513197c795fd9`); stock console command `REGR`.

## What was run and what it read

- `REGR axp192 0x26` (`DC1OUT_VOL`): 0x68. At 0.7 V plus 25 mV per step (AXP192 datasheet, DCDC1 output 0.7-3.5 V), 0x68 = 104 steps is 3.30 V.
- `REGR axp192 0x12` (`OUTPUT_ENABLE`): 0x1F, DC-DC1 on.
- The Kleidos firmware never writes register 0x26 on this board (no write to it in `src/drivers/power/axp192.cpp` or `src/hal/common/power_manager_axp2101.cpp`; the regmap lists it as `DC1OUT_VOL`, `src/drivers/power/axp192_regmap.h`), so 0x68 is the value the AXP192 came up with.

## Result

- DC-DC1, the rail the print names VESP_3V3, is set to 3.30 V, the datasheet's default; nothing in the firmware changes it.
- Not run: the voltmeter reading of the 3V3 header pin (no meter on this board's header; it needs a person with a meter, without opening the case).
