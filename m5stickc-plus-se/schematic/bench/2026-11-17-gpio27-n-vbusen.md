<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# P6: GPIO27 high shuts VBUS out of the AXP192 (2026-11-17)

Probe P6 of `../improvements.md` (item T27). The case was not opened; the board was on USB with its battery fitted (4.16 V, full, not charging).

Firmware: a throwaway probe image, never committed: the Kleidos firmware of 2026-11-17, env `m5stickc_plus_se_debug`, plus one debug console command, `PROBEPIN <pin> HI|LO|IN|TONE <hz>` (drive a pin, release it as an input with no pull, or play a 50 % LEDC tone), and `rtcIntPowersOn = true` in the board wiring (unused by this probe). ELF SHA-256 prefix `ed568ff5f7d1ac4b`. The board was re-flashed with the plain debug image of the same firmware afterwards.

AXP192 registers read: REG00H (input power status: bit 5 VBUS present, bit 4 VBUS usable, bit 3 VBUS above V_HOLD), REG5CH/5DH (VBUS current ADC, 0.375 mA/LSB), REG7AH-7DH (battery charge and discharge current ADCs, 0.5 mA/LSB). REG30H read `0x42`: bit 7 = 0, so the VBUS-IPSOUT path is left to the N_VBUSEN pin. Each state: 25 reads of each register, about one per 0.75 s.

## Result

| GPIO27 | REG00H | VBUS current (mean, min-max) | Battery discharge (mean) |
| --- | --- | --- | --- |
| released (R21 holds it low; GPIO27 read 0, as Kleidos leaves it) | `0x38` | 65.8 mA (25.1-135.4) | 0 mA |
| driven high (`PROBEPIN 27 HI`) | `0x20` | 0.0 mA at every read | 68.4 mA |
| released again (`PROBEPIN 27 IN`, reads 0) | `0x38` | 58.1 mA (18.4-132.0) | 0 mA |

With GPIO27 high the battery fell from 4,161 to 4,116 mV under the load (`PMIC?`) and came back once released.

## What it proves

GPIO27 drives the AXP192's N_VBUSEN as the print draws it (U2 pin 6, R21 10K to GND): low, its default through R21, lets VBUS supply the board; high shuts VBUS out (REG00H keeps "VBUS present" but drops "usable", VBUS current goes to zero) and the board runs from its cell. The polarity is the pin name's: N_VBUSEN is active low.
