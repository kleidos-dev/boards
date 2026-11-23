<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# RTC_INT: where the BM8563's interrupt goes (probe P2)

Bench probe of 2026-11-17 on the M5StickC Plus 1.1 (K016-P), USB connected (AXP192 `vbus_present=1`), the case closed. It settles triage items B5 and B6 (`../improvements.md`). The print draws U4 pin 3 (BM8563 INT) on RTC_INT: C401 (10 µF) to PWR_KEY (AXP192 pin 23, the power key S1), and R401 (10 kΩ) up to IPSOUT; it never reaches GPIO35.

## Firmware

- Part 1: the `m5stickc_plus1_debug` image found on the board (`VER?`: version 0.1.0, `elf_sha=281513197c795fd9`), stock console commands only.
- Part 2: the Kleidos firmware of 2026-11-17, env `m5stickc_plus1_debug`, built in a throwaway worktree with `rtcIntPowersOn = true` in `src/boards/board_plus1.cpp` (and the `PROBEPIN` command of the P5 record); never committed.

## Part 1: a BM8563 countdown with the board running

A script on the host wrote, over the console, BM8563 timer off (`I2CWR! 0x51 0x0E 0x03`), flags and interrupt enables clear (0x01 = 0x00), timer value N (0x0F), timer interrupt enable (0x01 = 0x01, TIE), then started the countdown (0x0E = 0x82: timer on, 1 Hz). From that write it polled `GPIO? 35 IN` every 0.2 s and printed every other line the board wrote, with the time since the start. The AXP192's power-key IRQ enables were as the firmware leaves them (`INTEN3` 0x42 = 0x3B, short and long press on); the firmware reads and clears the power-key latch every 50 ms and logs a click it reads.

| Run | N | TIE | Board log, time after the countdown started | GPIO35 | `CONTROL_STATUS2` after |
| --- | --- | --- | --- | --- | --- |
| a | 5 | 1 | `Lock key — locking device` (seen once, in a slower poll) | 1 throughout | 0x05 (TF, TIE) |
| b | 10 | 1 | 9.12 s: `Lock key — locking device` | 1 throughout | 0x05 |
| c | 7 | 1 | 5.83 s: `Lock key — locking device` | 1 throughout | 0x05 |
| control | 7 | 0 | nothing in 13 s | 1 throughout | 0x04 (TF only) |
| d (commit build) | 8 | 1 | 6.84 s: `Lock key — locking device` | 1 throughout | 0x05 |
| control (commit build) | 8 | 0 | nothing in 13 s | 1 throughout | 0x04 |

Runs a to c and the first control ran on the image found on the board, run d and the second control on the commit build. Each fire came about one second before N: the BM8563's first timer period runs short by up to one period of its 1 Hz source, and the host's times include the console's own latency, so these are the countdowns firing; the controls, where the countdown ran out with TIE off, latched nothing. The console's debug build ignores the lock's sleep request (`DEBUG: sleep/deep-sleep request ignored`), so the board stayed on. With TF and TIE both set the BM8563 holds its INT pin low, and it was left that way for seconds after each fire while GPIO35 read 1.

Before any of this the board was found with the BM8563 at `CONTROL_STATUS2` = 0x05 (INT asserted) and GPIO35 high, with the SYS_INT pull-up fitted (P1 record).

## Result of part 1

- The BM8563's INT does not reach GPIO35: GPIO35 stayed high with INT asserted, at rest and after every fire.
- The BM8563's INT presses the power key: each falling edge of INT, with TIE on, made the AXP192 latch a power-key short press, which the firmware read as a click; with TIE off the countdown ran out and nothing was latched. This is C401 coupling RTC_INT's falling edge into PWR_KEY, as the print draws it.

## Part 2: an RTC countdown powers the board on after a PMIC power-off

On the commit build with `rtcIntPowersOn = true`, the console's `PMICOFFTEST <s>` runs the production lock teardown and `PowerManager::enterDeepSleep()`, whose power-off sequence starts a BM8563 countdown of about <s> seconds as its last step before the AXP192 power-off command, and arms an ESP timer for <s> seconds as the fallback for a PMIC that stays on (`src/debug/debug_console.cpp` (`commandMatches`), `src/hal/common/power_manager_axp2101.cpp` (`PowerManagerAXP2101::switchOffAtPmic`)). USB stayed connected throughout (`vbus_present=1`). The host printed every line the board wrote, with the time since the command:

| `PMICOFFTEST` | Last line before silence | First boot line | ESP uptime in that line | Power-on, time after the command | `SYS?` after |
| --- | --- | --- | --- | --- | --- |
| 20 | 0.21 s: `Switching off at the PMIC — the RTC powers it back on in 20 s` | 20.62 s | 1,184 ms | ≈19.4 s | `reason=POWERON wake=NONE from_deep_sleep=0` |
| 35 | (log not kept) | (log not kept) | | board up again with 20 s of uptime when read | `reason=POWERON wake=NONE from_deep_sleep=0` |
| 30 | 0.20 s: `Switching off at the PMIC — the RTC powers it back on in 30 s` | 30.34 s | 1,662 ms | ≈28.7 s | `reason=POWERON wake=NONE from_deep_sleep=0` |

No run logged `Board still on` or `PMIC still on: ESP deep sleep fallback`, and every return was a power-on reset with no deep-sleep wake cause, so the ESP timer fallback never ran: the AXP192 cut the ESP32's supply and the BM8563's countdown switched it back on. The BM8563 read `CONTROL_STATUS2` = 0x05 (TF, TIE) after the first return, the countdown that had fired. The control, the same power-off with no countdown (`PMICOFFTEST <s> KEY`), was measured on this board before: it stays off with VBUS present, and EN pulses through the USB bridge bring no boot log back (Kleidos `docs/variants.md`, section "The USB PHY pads, on the four ESP32-S3 boards").

## Result

- RTC_INT does not reach GPIO35 (part 1).
- RTC_INT presses the AXP192's power key through C401, as the print draws it (part 1), and an RTC countdown powers the board back on from an AXP192 power-off with USB connected (part 2). The board can wake itself on an RTC alarm. Power-on on battery alone was not run: the power-on came from PWR_KEY, which the AXP192 honors on either supply, but that case is not measured here.

The board was left on its normal `m5stickc_plus1_debug` image (see `2026-11-17-buzzer-gpio2-load.md` for the reflash).
