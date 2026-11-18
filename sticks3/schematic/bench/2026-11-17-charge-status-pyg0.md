# B3: what PYG0 reads while the cell charges (2026-11-17)

Probe B3 of `../improvements.md`: does the M5PM1's PYG0 input (U16 pin 3, net `PYG0_CHG_STAT`, from the LGS4056 U15) read 0 while the cell charges? An open StickS3 on the bench hub, case closed. USB was taken away and given back with the hub's per-port VBUS switch (`qa/tools/hub_power.py off|on --dut sticks3` in the Kleidos repository), never by hand. The M5PM1's ADC was read raw at 0x22 to 0x27, whose meaning is the vendor's own: `M5PM1_REG_VBAT_L/H` 0x22/0x23, `M5PM1_REG_VIN_L/H` 0x24/0x25 and `M5PM1_REG_5VINOUT_L/H` 0x26/0x27, all in mV (m5stack/M5PM1, `src/M5PM1.h:225-230`, commit `315d2899c`).

Firmware: the discharge and the first two observations ran on the `sticks3_debug` image found on the board (ELF SHA-256 prefix `55ad934550a7662f`); the last one on Kleidos `sticks3_debug`, built from the firmware of 2026-11-17 (ELF prefix `13cf0d745130259a`). Both read PYG0 the same way: `REGR m5pm1 GPIO_INPUT` (register 0x12, bit 0) and `I2CRD 0x6E 0x22 6`.

## What was run

1. With the cell full (4,192 mV) and USB in: `PMIC?`, `REGR m5pm1 GPIO_INPUT`, `REGR m5pm1 GPIO_MODE` (PYG0 is an input, mode bit 0 = 0).
2. VBUS cut for 15 min and then for 40 min (the panel light, the LED and the 5 V output on during the second cut to load the cell); the board kept running on its cell (uptime continuous, no reboot).
3. VBUS restored; `GPIO_INPUT` bit 0 and the three ADC readings sampled about every 0.7 s.
4. `REGW! m5pm1 POWER_CONFIG 0x06` (charge enable off), 3 s, `REGW! m5pm1 POWER_CONFIG 0x07` (back to the read value, readback `0x07`), then 90 s of samples.
5. After the flash to the Kleidos firmware of 2026-11-17: `HALDIAG`, `PMIC?`, `GPIO_INPUT`, ADC.

## Results

| When | Cell (VBAT) | VIN | PYG0 | Firmware's `charging` |
| --- | --- | --- | --- | --- |
| Before the cuts, USB in, cell full | 4,190 to 4,194 mV | 5,208 mV | 1 | 0 |
| After the 40 min cut, USB in, not charging | 4,010 to 4,022 mV | 5,210 to 5,220 mV | 1 (340 samples over 4 min) | 0 |
| Same, in a 16 s window seen right after the restore | 4,050 to 4,060 mV | 5,178 to 5,182 mV | 0 | — |
| After charge enable 0 then 1: samples up to 49.4 s | 3,990 to 4,002 mV (mean 3,996) | 5,210 to 5,220 mV | 1 | — |
| Same, from 50.1 s to the end at 90.4 s | 4,026 rising to 4,054 mV | 5,180 to 5,186 mV | 0 (58 samples) | — |
| After the flash to the Kleidos firmware of 2026-11-17 | 4,068 to 4,080 mV | 5,182 mV | 0 | 1 |
| About 5 min later, charging stopped | 4,030 to 4,036 mV | 5,212 mV | 1 | 0 |

At every edge PYG0 and the two analog readings moved together: when PYG0 fell to 0, the cell's terminal voltage stepped up 30 to 40 mV at once and VIN dropped about 30 mV (more current drawn through the USB input's path); when PYG0 went back to 1, both stepped back.

## What it proves

- F4: PYG0 reads 0 while the charger is charging and 1 while it is not, with USB in. The terminal-voltage step and the VIN dip are independent evidence of charge current in each PYG0 = 0 window, so the polarity does not rest on the firmware's own `charging` flag (which is derived from the same bit).
- The "USB out" half of the probe (bit 0 with no USB) could not be read: with VBUS cut the USB console is gone. It adds nothing to the polarity, which the USB-in windows settle in both directions.
- Not settled, and not drawn: the charger stopped with the cell at about 4.03 to 4.05 V, below full, several times, and restarted on its own or after a charge-enable toggle. Whether that is the LGS4056's own behaviour or the M5PM1's charge control needs the LGS4056 datasheet or a longer run; it is noted here only because it was seen.
