<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# P01: ESP32, crystal, flash ID and VDD_SDIO eFuses (2026-11-17)

Probe P01 of `../improvements.md`. Read only, over the board's own USB-C, through the ROM download mode that esptool enters by the bridge's DTR/RTS lines; nothing was written to flash or eFuse, and the case was not opened. The bench unit is the Core2 v1.3 of the Kleidos bench (private identifiers, such as its MAC, are left out of this record).

Tools: esptool.py v4.11.0 and espefuse.py v4.11.0 (`esptool==4.11.0` and `bitstring==4.2.3` from PyPI, in a throwaway virtual environment). Commands, each with `--chip esp32 -p <port>` (and `-b 115200` for esptool): `esptool.py chip_id`, `esptool.py flash_id`, `espefuse.py summary`. The running firmware does not matter to these reads (the ROM answers them); after the reads the board was reset back into its Kleidos `core2_v13_debug` image.

## Results

| Read | Output (verbatim, identifiers removed) |
| --- | --- |
| Chip | `Chip is ESP32-D0WDQ6-V3 (revision v3.1)` |
| Features | `WiFi, BT, Dual Core, 240MHz, VRef calibration in efuse, Coding Scheme None` |
| Crystal | `Crystal is 40MHz` |
| Flash JEDEC ID | `Manufacturer: 46`, `Device: 4018` |
| Flash size | `Detected flash size: 16MB` |
| Flash voltage (from the strap register at reset) | `Flash voltage set by a strapping pin to 3.3V` |
| eFuse `XPD_SDIO_FORCE` | `False` ("Ignore MTDI pin (GPIO12) for VDD_SDIO on reset") |
| eFuse `XPD_SDIO_REG` | `False` |
| eFuse `XPD_SDIO_TIEH` | `1.8V (0b0)`, which applies only with `XPD_SDIO_FORCE` set |
| espefuse's verdict | `Flash voltage (VDD_SDIO) determined by GPIO12 on reset (High for 1.8V, Low/NC for 3.3V)` |
| eFuse `CHIP_VER_REV1`, `CHIP_VER_REV2`, `WAFER_VERSION_MAJOR`/`MINOR` | `True`, `True`, `3`, `1` (revision v3.1) |
| eFuse `CHIP_PACKAGE`, `CHIP_PACKAGE_4BIT` (`PKG_VERSION`) | `0`, `False` (`0`: the D0WDQ6 package) |

## What it proves

- The ESP32 U7 is an ESP32-D0WDQ6-V3, revision v3.1, read from the chip itself (T11).
- The crystal X2 is 40 MHz, measured by the ROM against its internal clock (T06).
- VDD_SDIO is set by the MTDI strap, not by an eFuse: `XPD_SDIO_FORCE` is not burned, and the strap was sampled low at reset, so VDD_SDIO is the 3.3 V supply from VDD3P3_RTC (T24, T25).
- The flash answers JEDEC ID `0x46 0x40 0x18`, a 16 MB (128 Mbit) part, which matches U1's capacity. Whether `0x46` is the manufacturer byte of the XM25QH128BHIQ the print names is not settled here: the XM25QH128B datasheet was not found on 2026-11-17 (its sibling XMC parts list their IDs in a "Manufacturer and Device Identification" table), so U1's part number stays as printed.
