<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# Cardputer-Adv: idle levels and pulls of G0, G1, G2, G11 (P02)

- Date: 2026-11-17.
- Unit: the bench Cardputer-Adv, case closed, on USB from the bench hub, power switch on, nothing known to be plugged into the Grove port or the EXT header.
- Firmware: the same `cardputer_debug` image as `2026-11-17-i2c-scan.md` (built from the Kleidos firmware of 2026-11-17).
- Tool: the debug console's `GPIO? <pin>`, which reads the pad's IO_MUX and GPIO-matrix state and its input level without changing a pad that already has its input buffer on. Run after a reset, so no earlier I2C scan had reconfigured a pad.
- Settles: T22 and T20 (confirmations).

## What came back

```text
GPIO pin=11 func=1 sig_out=256 plain=1 ie=1 oe=0 oe_periph=0 od=0 pu=1 pd=0 level=1
GPIO pin=1 func=0 sig_out=256 plain=1 ie=1 oe=0 oe_periph=1 od=0 pu=0 pd=0 level=1
GPIO pin=2 func=0 sig_out=256 plain=1 ie=1 oe=0 oe_periph=1 od=0 pu=0 pd=0 level=1
GPIO pin=0 func=1 sig_out=256 plain=1 ie=1 oe=0 oe_periph=0 od=0 pu=0 pd=0 level=1
```

Read in the same pass (the strap pins after boot, not their latched values; those are in `2026-11-17-boot-strap.md`):

```text
GPIO pin=46 func=0 sig_out=256 plain=1 ie=1 oe=0 oe_periph=1 od=0 pu=0 pd=1 level=0
GPIO pin=45 func=0 sig_out=256 plain=1 ie=1 oe=0 oe_periph=1 od=0 pu=0 pd=1 level=0
GPIO pin=3 func=0 sig_out=256 plain=1 ie=1 oe=0 oe_periph=1 od=0 pu=0 pd=0 level=0
```

## Result

- **G0 (T22):** input, neither internal pull on, reads high. The side key's line is held up by the board's own resistors (R18 on the carrier, R104 on the module), as the firmware assumes when it configures the key with no pull. Confirmed.
- **G0 held:** not run. It needs a person to hold the side key; no one was at the bench. Open.
- **G1, G2 (Grove GI / GO):** inputs, no internal pull, read high: R10 and R3 (10 kΩ to +3.3V) hold them up with nothing on the port. Confirms the print.
- **G11 (T20):** input, reads high, but the firmware also enables the ESP32's internal pull-up on it (`pu=1`, `src/drivers/keyboard/tca8418.cpp` (`Tca8418::init`)). So the reading shows that the TCA8418's ~INT idles released (no key events pending), not R37 on its own, and it cannot show the open-drain output. T20 stays settled by the TCA8418 datasheet alone.
