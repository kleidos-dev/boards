<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# P2: the BM8563's INT reaches the AXP192's power key, not GPIO35 (2026-11-17)

Probe P2 of `../improvements.md` (item T24, `board.json` B7). The case was not opened, nothing was touched by hand, and no button was pressed during any run.

Firmware: Kleidos `m5stickc_plus_se_debug`, the image found on the board (ELF SHA-256 prefix `bed9d07ebe90eefd`, built from the Kleidos firmware of 2026-11-17). Its board wiring sets `rtcIntPowersOn = true`, so `PMICOFFTEST <s>` starts a BM8563 countdown as the last step before the AXP192 power-off (on a build without it the command refuses on this board).

BM8563 registers used: `0x01` control/status 2 (bit 0 TIE, timer interrupt enable; bit 2 TF, timer flag; bit 4 TI_TP = 0, so INT is a level held while TF and TIE are set), `0x0E` timer control (bit 7 TE; bits 1:0 the source), `0x0F` timer value.

## (a) Running: where INT goes when the countdown ends

Commands, twice (USB in): `I2CWR! 0x51 0x0E 0x02`, `I2CWR! 0x51 0x0F 10`, `I2CWR! 0x51 0x01 0x01` (TIE on, TF cleared), `I2CWR! 0x51 0x0E 0x82` (start), then `I2CRD 0x51 0x01` and `GPIO? 35 IN` about once a second, and `I2CRD 0x34 0x44 4` (the AXP192's IRQ latches). Afterwards the countdown was stopped and the interrupt disabled (`I2CWR! 0x51 0x0E 0x03`, `I2CWR! 0x51 0x01 0x00`).

| Run | Before TF | When TF set | After TF (INT held) |
| --- | --- | --- | --- |
| 1 | `0x01` = `0x01`, GPIO35 = 1 | firmware log `Lock key — locking device` (no key was pressed) | `0x01` = `0x05` (TF and TIE), GPIO35 = 1 at every read; IRQ latches `0x00` (the firmware's power-key poll had already read and cleared its latch) |
| 2 | `0x01` = `0x01`, GPIO35 = 1 at four reads | the same single log line | `0x01` = `0x05`, GPIO35 = 1 at four reads over 4 s |

TF set about 5 s after the start, not 10 s; the timer's rate was not investigated and does not change the result. The firmware's lock-key path reads the AXP192's power-key IRQ latch (Kleidos `src/main.cpp` (`readLockKeys`), `ctx().power.wasPowerButtonClicked()`), so the AXP192 registered one power-key press at the moment TF set, and only then (the countdown reloads without a new edge). GPIO35 stayed high throughout, with INT held asserted.

## (b) Off: the countdown powers the board on

Run 1 cut VBUS at the hub before the command: the USB-UART bridge loses power with VBUS on this board, so the command never arrived; nothing happened (uptime continued). Not counted.

Run 2 (USB in throughout): `PMICOFFTEST 30`. The log ends at `PowerMgr: Switching off at the PMIC — the RTC powers it back on in 30 s`, with no `Board still on` warning (the line the firmware prints when the AXP192 does not switch off), so the AXP192 cut its outputs. A cold boot followed 30.5 s later. `SYS?`: `reason=WDT wake=NONE from_deep_sleep=0` (not a timer wake from the deep-sleep fallback; the ESP32 often reports its RTC watchdog reset at a slow supply ramp); BM8563 `0x01` = `0x05` (the countdown had fired); AXP192 REG00H = `0x38`, bit 0 = 0 (the power-on source was not ACIN/VBUS).

Run 3 (VBUS cut 2 s after the command, while the board was already off, and restored 57 s later): `PMICOFFTEST 30` at host time 3.2 s, hub off at 5.1 s, hub on at 62.2 s. At 71.1 s `CLOCK?` gave `uptime_ms=38064`, so the board had booted at about 33 s host time, on its battery, with no VBUS and no insertion edge, 30 s after the power-off. `SYS?` and the BM8563 read as in run 2.

## What it proves

The BM8563's INT reaches the AXP192's power key (PWR_KEY, through C401 as the print draws it), not ESP32 GPIO35: the end of a countdown registers as one power-key press while the board runs, leaves GPIO35 high while INT is held, and powers the board on from an AXP192 power-off on battery alone. The print and the back label's "SLEEP WAKE" are right; M5Unified's `_rtcIntPin = GPIO_NUM_35` for this board is wrong. GPIO35 is the AXP192's IRQ line (SYS_INT) as printed.
