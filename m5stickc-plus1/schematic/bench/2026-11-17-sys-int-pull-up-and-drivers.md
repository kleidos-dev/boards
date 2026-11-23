<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# SYS_INT (GPIO35): pull-up and the two drivers on the net (probe P1)

Bench probe of 2026-11-17 on the M5StickC Plus 1.1 (K016-P), USB connected (AXP192 `POWER_STATUS` 0x00 = 0x38, `vbus_present=1`), the case closed. It settles triage items B4 and C3 (`../improvements.md`).

## Firmware

Two images, the same commands and the same results on both:

- Run 1: the `m5stickc_plus1_debug` image found on the board (`VER?`: version 0.1.0, `elf_sha=281513197c795fd9`).
- Run 2: the Kleidos firmware of 2026-11-17, env `m5stickc_plus1_debug`, built in a throwaway worktree with two bench-only changes that P1 does not use (the `PROBEPIN` console command and `rtcIntPowersOn = true`, see the P2 and P5 records); never committed.

Every command is a stock debug-console command (`I2CRD`, `I2CWR!`, `REGR`, `GPIO? <pin> IN`). `GPIO? 35 IN` makes GPIO35 an input and reports its pad: `pu=0 pd=0` on every read (GPIO35 has no internal pull).

## What was run and what it read

1. **Every open-drain driver released.** AXP192 IRQ enables masked (`I2CWR! 0x34` 0x40, 0x41, 0x42, 0x43, 0x4A = 0x00, read back 0x00), every IRQ latch cleared (0xFF to 0x44-0x47 and 0x4D, read back 0x00). MPU-6886 INT set open drain, active low, latched (`I2CWR! 0x68 0x37 0xE0`, read back 0xE0) with no interrupt enabled (`0x38` = 0x00, `INT_STATUS` 0x3A = 0x00). `GPIO? 35 IN` three times: **level=1** each time.
2. **The MPU-6886 pulls the net.** Data-ready interrupt enabled (`I2CWR! 0x68 0x38 0x01`): `GPIO? 35 IN` twice, **level=0**. Interrupt disabled and its status read (0x38 = 0x00, 0x3A read): **level=1**. INT_PIN_CFG put back to its earlier 0xC0.
3. **The AXP192 pulls the net, with no key press.** Only the AXP192's timer IRQ enabled (`INTEN5` 0x4A = 0x80), its timer set to one minute (`TIMER_CTL` 0x8A = 0x80 to clear, then 0x01), GPIO35, `INTSTS5` (0x4D) and `TIMER_CTL` read every ~7 s:

   | Time after arming | GPIO35 | 0x4D | 0x8A |
   | --- | --- | --- | --- |
   | 0 to 54 s | 1 | 0x00 | 0x01 |
   | 61 s to 117 s | 0 | 0x80 (timer timeout) | 0x81 |

   Timer status and latch cleared (0x8A = 0x80 then 0x00, 0x4D = 0xFF, 0x4A = 0x00): **level=1**. The IRQ enables were written back to the values read before step 1 (0x40-0x43 = 0xD8, 0xFF, 0x3B, 0xC1).

The same rest reading held before any write: with the AXP192's latches already clear and the MPU-6886's INT open drain with nothing enabled, GPIO35 read 1, while the BM8563 had its timer flag and timer interrupt enable both set (`CONTROL_STATUS2` 0x01 = 0x05), so its INT pin was asserted (see the P2 record).

## Result

- With every open-drain driver on SYS_INT released and no internal pull on GPIO35, the net sits high: a pull-up is fitted on the board, as the print's R2 (2.2 kΩ to VESP_3V3) says. The value of the resistor is not measured.
- The AXP192's IRQ output (pin 48) is on SYS_INT: its timer IRQ latch pulled GPIO35 low for as long as the latch was set, and releasing it gave the net back.
- The MPU-6886's INT output (pin 12) is on SYS_INT, and drives it low when set open drain and active low.
- The earlier Kleidos reading of GPIO35 low (`docs/research/imu-tuning.md`, section "Plus 1.1: GPIO35", "nothing pulls the net up") is explained by an AXP192 IRQ latch left set: any set latch with its enable on holds the net low until it is cleared.
- The BM8563's INT, asserted during the rest reading, did not pull GPIO35 low.
