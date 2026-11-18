# T-Deck Plus: does a falling edge on ESP_TP_INT switch V3V on? (B3)

- Date: 2026-11-17.
- Unit: the bench T-Deck Plus, case closed, slide switch SW1 on, on USB from the bench hub and its cell.
- Firmware: Kleidos `tdeck_debug`, built from the firmware of 2026-11-17 plus a throwaway probe that was never committed: a console command `PROBETPEDGE <n> [PARK]`. Run 1 on image `elf_sha=cbc9ea85b81904e5`, run 2 on `elf_sha=d5453f6f49c0ddd4` (the same probe with the `PARK` option added).
- Settles: T01, for the TP_EN edge detector only (Q25, D30, R49, R70, R74, C73, with D4 to Q7's base).

## The circuit the print draws, and what a fitted one does

`ESP_TP_INT` (S3 IO16) is AC-coupled by C73 100 nF to a node held at VDD3V3 by R70 100K; that node drives Q25 (PNP, emitter on VDD3V3) through R49, and Q25's collector is `TP_EN`, which reaches Q7's base through D4, the same base IO10 (`PWR_EN`) drives. A falling edge on IO16 pulls the node below VDD3V3, turns Q25 on and Q7 with it, and V3V comes on for about R70·C73 ≈ 10 ms. The print frames these parts in a compile mask.

## Sensor

V3V is read through IO46 (`C3_INT`), which the print ties to V3V through R12 4.7K. The probe makes IO46 a plain input with the internal pull-down (about 45 kΩ) and the pull-up off, so it reads 1 whenever V3V is up and 0 when V3V is dead. It samples IO46 every 8 µs or so (5,100 to 5,400 samples per 40 ms window).

## Procedure

1. `PERIPH OFF TOUCH`: the GT911 is sent to its own Sleep with INT held low by the S3, so the touch controller does not drive the line.
2. `PERIPH! OFF PERIPHRAIL`: IO10 driven low, the rail cut by the firmware's own path.
3. `PROBETPEDGE 8 [PARK]`: IO16 driven high for 200 ms, then eight cycles of: drive IO16 low and sample IO46 for 40 ms (the falling edge), wait 160 ms, sample 40 ms (steady low), drive IO16 high and sample 40 ms (the rising edge, a control), wait 160 ms. The probe refuses to run while IO10 is driven high.

## Run 1: the rail cut but back-fed

After `PERIPH! OFF PERIPHRAIL` the firmware leaves the I2C pads (IO18, IO8) attached to the I2C peripheral with their internal pull-ups on, the backlight enable (IO42), the SPI lines and the SD and LoRa selects driven. IO46 read 1 in every sample of every window, falling edges, steady low and rising edges alike (5,380 of 5,380 in the baseline). V3V was held up by back-feed from those pads, so this run cannot see a pulse. It does show the sensor: with the pull-down on, IO46 reads 1 while V3V is up.

## Run 2: the back-feeding pads released (`PARK`)

The probe first made IO18, IO8, IO42, IO38, IO41, IO40, IO39, IO9 and IO17 plain inputs with the internal pull-down. Then:

```text
PROBE_TPEDGE parked pads 18 8 42 38 41 40 39 9 17 as pulled-down inputs
PROBE_TPEDGE io10_en=1 io10_out=0 baseline_io16_high io46_highs=0/5120
PROBE_TPEDGE cycle=0 fall: io46_highs=0/5116 | low_steady: io46_highs=0/5120 | rise: io46_highs=0/5120
PROBE_TPEDGE cycle=1 fall: io46_highs=0/5112 | low_steady: io46_highs=0/5120 | rise: io46_highs=0/5121
...
PROBE_TPEDGE cycle=7 fall: io46_highs=0/5111 | low_steady: io46_highs=0/5120 | rise: io46_highs=0/5121
GPIO pin=16 ... ie=1 oe=1 ... level=1
GPIO pin=46 ... ie=1 oe=0 ... pu=0 pd=1 level=0
```

(Each `cycle` line abridged: `first_us=-1 last_us=-1` in every window, no sample high.)

## Result

- With V3V dead, eight falling edges on IO16, each after 200 ms high, raised V3V in none of the 40 ms windows that followed: IO46 stayed at 0 in all 40,900 samples taken after a falling edge. A fitted detector would have held V3V up for about 10 ms after each one. **On this unit the TP_EN edge detector does nothing**: some part of that path (Q25, D4 or another) is not fitted. The masked network cannot be drawn as an addition; it can be marked not fitted on the examined unit with this record as the source. Which of its parts are absent needs the board opened, and another production batch may differ.
- IO16 read back high at the end, so the pad itself toggled; the GT911 was asleep, so nothing else drove the line.
- Side observation, not a probe target: in run 2 IO18 (SDA) and IO8 (SCL) read 1 against the S3's internal pull-down while IO46 read 0, so something pulls the I2C lines up while V3V is dead. The print puts the C3's I2C pull-ups R11 to R14 on V3V; a pull-up on an always-on supply elsewhere on the bus (or a part on VDD3V3 holding the lines) is not identified here. Open; nothing is drawn from it. (Read against the print afterwards, the same day: IO18 and IO8 are `II2C_SDA` and `II2C_SCL`, the S3's side of the BSS123 level shifter, pulled up by RC4 and RC2 4.7K to the always-on VDD3V3, so the print explains the high lines and nothing is open.)
- Afterwards the board was flashed with the plain `tdeck_debug` image of the same firmware, no probe (`elf_sha=ca66bc84d47e9af1`), which restores every pad and the rail at boot.
