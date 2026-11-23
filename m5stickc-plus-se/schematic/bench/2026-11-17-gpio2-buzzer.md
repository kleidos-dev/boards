<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# P4: a tone on GPIO2, and what GPIO2 is loaded with (2026-11-17)

Probe P4 of `../improvements.md` (item T06). The case was not opened. No one was at the bench, so no one listened for the tone: the half of P4 that needs a listener was not done.

Firmware: the throwaway probe image of `2026-11-17-gpio27-n-vbusen.md` (the Kleidos firmware of 2026-11-17 plus the console command `PROBEPIN`, never committed; ELF SHA-256 prefix `ed568ff5f7d1ac4b`). The board was re-flashed with the plain debug image of the same firmware afterwards.

The board was on USB with a full cell (not charging), so the AXP192's VBUS current ADC (REG5CH/5DH, 0.375 mA/LSB) reads the whole board's draw; the battery current ADCs read 0 throughout. The board draws 18-135 mA from read to read on the PIN screen, so each state is a mean of 30 or 40 reads, good to about ±5 mA.

## Current

| GPIO2 | VBUS current, mean of 40 reads |
| --- | --- |
| idle (Kleidos leaves it an input with its internal pull-down) | 62.1 mA |
| 2.7 kHz, 50 % duty (`PROBEPIN 2 TONE 2700`; `GPIO? 2` showed the LEDC signal routed to the pad) | 68.4 mA |
| released | 61.5 mA |
| 2.7 kHz again | 56.6 mA |
| driven low | 62.0 mA |

Static levels, 30 reads each: low 65.9, high 64.2, low 61.5, high 65.7 mA.

## Load on the pin

Released as an input with no pull (`PROBEPIN 2 IN` after driving it), GPIO2 kept the level it had been driven to: high at 0, 2 and 7 s after a high, low at 0 and 5 s after a low. As a control, GPIO26 released after a high read low within 2 s.

## What it proves, and what it does not

Neither the tone nor a static high raises the board's draw beyond the ±5 mA the ADC average resolves, and GPIO2 holds a released level for at least 7 s either way, so nothing on GPIO2 has a DC path to either rail: not a magnetic transducer to a rail, not a bipolar transistor's base, not a pull resistor. That fits a piezo element (a capacitor to the pin) or a MOSFET gate with no gate resistor to ground, and equally fits nothing at all. Whether GPIO2 drives a sounder is still open: it needs someone to listen while `PROBEPIN 2 TONE 2700` plays (or a microphone at the case; the board's own SPM1423, powered from LDOio0 and read as PDM on GPIO0/GPIO34, could serve in a further probe image), and the circuit stays unknown without opening the board.
