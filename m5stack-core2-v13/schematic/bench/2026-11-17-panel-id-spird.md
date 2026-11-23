<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# P06: the LCD controller's ID over SPI, attempted (2026-11-17)

Probe P06 of `../improvements.md`: read the panel controller's ID to tell an ILI9342C from an ILI9342E on the bench unit. The triage assumed no console command could do it; the Kleidos console has `SPIRD <cmd> [len]`, a genuine controller read over the display bus, so it was tried. Read only (no panel command is written); the case was not opened.

Firmware: Kleidos `core2_v13_debug`, the image already on the board (ELF SHA-256 prefix `a702778a98891b54`, built from the Kleidos firmware of 2026-11-17).

## Commands and results

Each read was repeated in a second session after a reset, with the same bytes.

| Command | Bytes returned | ILI9342 documented answer |
| --- | --- | --- |
| `SPIRD 0xD3 4` (RDID4) | `0x1f 0xff 0xff 0xff` | a dummy byte, then `0x00 0x93 0x42` |
| `SPIRD 0x04 4` (RDDID) | `0xe3 0x00 0x00 0x0f` | |
| `SPIRD 0xDA 2`, `0xDB 2`, `0xDC 2` | `0xc7 0xff`, `0x00 0x1f`, `0x00 0x1f` | |
| `SPIRD 0x09 5` (RDDST) | `0x84 0x53 0x24 0x00 0x0f` | |

## What it proves

Nothing about the controller. The bytes are repeatable but RDID4 does not return the `0x93 0x42` an ILI9342 answers, so the read path is not reading this panel correctly. The reason is in the firmware: the Core2 variant builds its display bus as 3-wire (`variants/core2_v13/variant.h`, `DISPLAY_SPI_3WIRE 1`), so `SpiPanelDriver::readPanelRegister()` reads back on the shared data line (`src/hal/display/spi_panel_driver.cpp` (`SpiPanelDriver::deviceConfig`)) with the ST7789's dummy-bit rule (`SpiPanelDriver::readPanelRegister`), while the board wires the panel's SDO to its own MISO line, GPIO38 (core sheet; `variants/core2_v13/variant.h` (`PIN_DISPLAY_MISO`)). P06 stays open until the read is made on GPIO38 with the ILI9342's framing (a throwaway probe build, or a fix to the console's read on this board). T02 stays a README note.
