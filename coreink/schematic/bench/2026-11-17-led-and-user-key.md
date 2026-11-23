<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# P04 and P05: user LED (GPIO10) and user key (GPIO5), console half (2026-11-17)

Probes P04 and P05 of `../improvements.md`, the part that runs without a person at the bench. The board ran an `m5core_ink_debug` image (the Kleidos firmware of 2026-11-17; `VERSION?` reported `elf_sha=7f4f296e1960ad18`). The image was already on the board for another bench job, so it was not reflashed. Commands were sent over the debug serial console at 115200 baud, holding the port's bench lock. The case was not opened.

## Commands and replies

| Command | Reply (abridged) |
| --- | --- |
| `PERIPH?` | `PERIPH name=LED fitted=1 mech=gpio:10 ... awake_only=1`; `PERIPH_NOREADBACK names=PANEL,LED` |
| `GPIO? 10` | `func=2 plain=1 ie=0 oe=1 od=0 pu=0 pd=0 level=-` |
| `PERIPH ON LED` | `PERIPH LED ON OK mech=gpio:10` |
| `GPIO? 10` | `func=2 plain=1 ie=0 oe=1 od=0 pu=0 pd=0 level=-` |
| `PERIPH OFF LED` | `PERIPH LED OFF OK mech=gpio:10` |
| `GPIO? 10` | `func=2 plain=1 ie=0 oe=1 od=0 pu=0 pd=0 level=-` |
| `GPIO? 5` | `func=2 plain=1 ie=1 oe=0 od=0 pu=1 pd=0 level=1` |
| `GPIO? 5 IN` | `func=2 plain=1 ie=1 oe=0 od=0 pu=1 pd=0 level=1` (the pad was already an input, so `IN` changed nothing) |

## What it proves

- **GPIO10 (P04):** the firmware drives the LED pad as a plain push-pull GPIO output (no open drain, no pulls). With its input buffer off, the console cannot read back the level it drives, and the firmware itself reports the LED as having no readback. Whether the LED lights at the low level, and its color, need someone to look at the LED while `PERIPH ON LED` / `PERIPH OFF LED` run. Not settled by this half; settled by the look below. The LED was left off.
- **GPIO5 (P05), released:** the key's pad is an input with the ESP32's internal pull-up on and reads high with the key released. That matches the firmware's reading (active low, internal pull-up). Because the internal pull-up is on, the reading cannot show whether the HAT board also fits a pull-up. **Pressed half not run:** it needs someone to hold the top key while `GPIO? 5` runs. The expected low has not been observed.

## The look (owner, 2026-11-17)

The owner looked at his own CoreInk the same day and reported, by eye and with no instrument:

- **The LED (P04, the visual half):** it is green, it sits inside the case near the top, and it lit on the firmware's LED-on command. That command drives GPIO10 to the level the firmware declares as on: low (`STATUS_LED_ACTIVE_LOW 1`, `variants/m5core_ink/variant.h`, which `src/hal/common/peripheral_switch.cpp` (`makeBoardCaps`) takes as the off level being high). So the LED is lit when GPIO10 is low. **Settled:** color and polarity. Not shown: what parts sit between GPIO10 and the LED beyond J1.
- **The keys:** besides the dial the board has three plain keys: the user key on the top end (G5), the power key on the dial's side (G27), a push key and not a slide switch, and the reset key on the back. This places the keys; it is not the pressed half of P05 (no `GPIO? 5` was read with the top key held), which stays open.
