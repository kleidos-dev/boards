# B2: the LCD panel answers on its data line, pin 4 of the LCD connector (2026-11-17)

Probe B2 of `../improvements.md` (item I19 and `board.json` B-4). Read only: no panel command is written. The case was not opened; the board was on USB with its battery fitted.

Firmware: Kleidos `m5stickc_plus2_debug`, the image found on the board (ELF SHA-256 prefix `b1635f8975dd32f8`, built from the Kleidos firmware of 2026-11-17). The variant runs the panel bus 3-wire (`DISPLAY_SPI_3WIRE 1`), with no MISO pin: the command goes out on GPIO15 (`PIN_DISPLAY_MOSI 15`) and the read clocks the answer back in on the same line, in half-duplex, at 15 MHz (`DISPLAY_FREQ_READ_HZ`). Multi-byte reads skip one dummy clock first; single-byte reads skip none (`src/hal/display/spi_panel_driver.cpp` (`SpiPanelDriver::readPanelRegister`)).

## Commands and results

Every read except `SPIRD 0x04 4` was run in three sessions, each after a fresh reset, with the same bytes every time; `SPIRD 0x04 4` was run once.

| Command | Bytes returned | Value expected from the ST7789 and the firmware's own setup | Returned byte, one bit later |
| --- | --- | --- | --- |
| `SPIRD 0xDA` (RDID1) | `0xc2` | `0x85` (ST7789 ID1) | `0x85` |
| `SPIRD 0xDB` (RDID2) | `0xc2` | `0x85` (ST7789 ID2) | `0x85` |
| `SPIRD 0xDC` (RDID3) | `0x29` | `0x52` (ST7789 ID3) | `0x52` |
| `SPIRD 0x0A` (RDDPM) | `0xce` | `0x9C`: booster on, sleep out, normal mode, display on | `0x9C` |
| `SPIRD 0x0B` (RDDMADCTL) | `0x04` | `0x08`: rotation 2 sets no MY/MX/MV bit, and the panel is BGR (`variant.h` `DISPLAY_ROTATION 2`, `DISPLAY_COLOR_ORDER_BGR 1`; `src/drivers/display/st7789.cpp` (`St7789::madctl`)) | `0x08` |
| `SPIRD 0x0C` (RDDCOLMOD) | `0x02` | the driver sets COLMOD `0x55`, 16-bit (`src/drivers/display/st7789.cpp`); the control-interface field D2-D0 then reads `101` | `0x04` or `0x05` (the last bit is not read) |
| `SPIRD 0x04 3` (RDDID) | `0x42 0xc2 0xc2` | `0x85 0x85 0x52`, the example in Kleidos `docs/testing/serial-debug-commands.md` | `0x85 0x85 0x85` |
| `SPIRD 0x04 4` | `0x42 0xc2 0xc2 0xa9` | | `0x85 0x85 0x85 0x52` |
| `SPIRD 0x09 4` (RDDST) | `0x42 0x42 0x29 0x92` | | `0x84 0x84 0x53 0x24` |

The last column is the returned bit stream read one bit later. Every single-byte read is the expected value shifted one bit to the right: the host takes its first sample one bit before the panel's first data bit. The multi-byte reads show the same offset, with the first byte repeated once.

## What it proves

- The panel drives data back on pin 4 of the LCD connector, GPIO15's net, which the print labels MOSI. Five single-byte reads return exact known values, the ST7789's fixed IDs (`0x85 0x85 0x52`) and the state the firmware set (display on, out of sleep, rotation 2 in BGR), and RDDCOLMOD agrees with the 16-bit format in the bits it returns. A line nothing drives back could not return those values, so pin 4 is the panel's bidirectional SDA (I19 settled). `board.json`'s "write only on this board" is wrong (B-4).
- The controller answers with the ST7789's ID bytes, so the panel is an ST7789 or a part that reports its IDs. The probe cannot tell an ST7789V from an ST7789V2.
- The one-bit offset was not investigated (the read's framing or its 15 MHz clock on this board are the places to look); each value is unambiguous all the same. It is a Kleidos firmware note: `docs/testing/serial-debug-commands.md` gives `SPIRD 0x04 3` → `0x85 0x85 0x52` as the expected answer, and this board does not print that.
