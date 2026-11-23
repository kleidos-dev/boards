<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# P03: the touch panel's INT on GPIO39, idle half (2026-11-17)

Probe P03 of `../improvements.md`. Run through the Kleidos debug serial console, without opening the case and without touching the glass.

Firmware: Kleidos `core2_v13_debug`, the image already on the board (ELF SHA-256 prefix `a702778a98891b54`, built from the Kleidos firmware of 2026-11-17). The image was not replaced.

## Commands

1. `REGS? ft6x36`: a decoded read of the touch controller's registers over I2C (address 0x38).
2. `GPIO? 39 IN`: the pad state of GPIO39; `IN` turns on the pad's input buffer with no pull, because the Core2 firmware does not use the line (`variants/core2_v13/variant.h` (`IDLE_WAKE_PINS`, `IDLE_WAIT_MAX_MS`): the loop polls the panel over I2C and its interrupt line is not an input).
3. `GPIO? 39`, twenty times over about 30 s, nothing on the glass.
4. `TOUCH?`.

## Results

- FT6336U: `G_MODE` (0xA4) = `0x01`, interrupt in trigger mode (a pulse per report while touched, per FocalTech's register map); `CTRL` (0x86) = `0x01`, the panel enters its monitor mode when idle; `FOCALTECH_ID` (0xA8) = `0x11`, `CIPHER` (0xA3) = `0x64`; `TD_STATUS` = 0 points.
- GPIO39, every read: `func=2 plain=1 ie=1 oe=0 od=0 pu=0 pd=0 level=1`. The ESP32 enables no pull on the pad (it has none: ESP32 datasheet, GPIO34-39 have no pull-up or pull-down), and the line read high on all 21 reads.
- `TOUCH available=1 model=FT6x36 touched=0`.

## What it proves

With no touch the line sits steadily high with no pull on the ESP32 side, so something on the panel's side holds it high while idle (its INT output, or a pull inside the touch module). A floating CMOS input can also hold a stale level, so the idle reads alone do not prove the line is driven. The second half of P03, the same reads while a finger is held on the glass (a driven line falls on each report in trigger mode), needs a person at the bench and was not run: it stays open. T30's ESP32-side fact (input-only, no internal pull, none drawn) is unchanged.
