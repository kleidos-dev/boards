<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# GPIO2 held high: is there a DC load on it? (probe P5, partial)

Bench probe of 2026-11-17 on the M5StickC Plus 1.1 (K016-P), USB connected, the case closed. It addresses triage item A1 (`../improvements.md`): the vendor's docs page puts the passive buzzer on G2, while the print draws GPIO2 (U1 pin 22) to PAD2 only.

## Firmware

The Kleidos firmware of 2026-11-17, env `m5stickc_plus1_debug`, built in a throwaway worktree with a bench-only console command `PROBEPIN <pin> H|L|Z` (resets the pad, makes it a plain GPIO output and drives it high or low; `Z` resets it) and `rtcIntPowersOn = true` (the P2 record); never committed. The variant builds no buzzer driver (`HAS_BUZZER 0`, `variants/m5stickc_plus1/variant.h`), so nothing else drives GPIO2.

## What was run

A host script drove GPIO2 low, then high, eight times in turn (`GPIO? 2` read back `oe=1` and the level asked for each time), waited 1.5 s after each change, and read the AXP192's VBUS input current ten times with `RES?` (`vbus_ma`, the AXP192's own ADC). A first, shorter run did the same four times with six readings.

| GPIO2 | Readings | Mean | Median | Spread (sd) |
| --- | --- | --- | --- | --- |
| low | 80 | 58.0 mA | 52.5 mA | 23.7 mA |
| high | 80 | 62.0 mA | 55.3 mA | 24.8 mA |

The first run gave 55.8 mA low and 66.3 mA high (24 readings each, sd 22 and 31 mA). The board's own load moves the reading by tens of milliamps from one read to the next, so the comparison rests on the means: the difference is 4 mA with a standard error of about 5 mA, no step.

## Result

- Driving GPIO2 high draws no direct current of tens of milliamps that this reading would show (a step of 15 mA or more would stand at three standard errors). A magnetic transducer switched by a transistor from GPIO2 would draw such a current while GPIO2 is held high; a piezo element, driven directly or through a capacitor, would not. The result fits the vendor's "passive buzzer" being a piezo, but does not show that a buzzer is on GPIO2.
- Not settled: whether anything sounds on GPIO2 (no one listened; the bench has no microphone on it), and the buzzer's part and drive circuit, which need the board opened. A1 stays as the triage has it: the GPIO's function from the vendor's docs page, the part and circuit open.

## Board left as found

After the probes the board was flashed with the stock `m5stickc_plus1_debug` image built from the Kleidos firmware of 2026-11-17 with no change (`VER?`: version 0.1.0, `elf_sha=bbe102553550dfde`; `PROBEPIN` unknown, `PMICOFFTEST 20` refused as on any stock build), and it booted to PIN entry. The BM8563's timer and interrupt flags were cleared (`CONTROL_STATUS2` 0x00, timer off), the AXP192's IRQ enables were back at 0xD8, 0xFF, 0x3B, 0xC1 with every latch clear, and the MPU6886's INT_PIN_CFG at 0xC0.
