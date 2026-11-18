# CoreS3 SE bench record: eFuses, strapping latch, flash ID, PSRAM (2026-11-17)

Probes P1 and P2 of `../improvements.md`. One CoreS3 SE (the owner's unit), over its USB-C port on the bench hub, case closed, nothing written to eFuse or flash. Port, MAC and the chip's unique ID are left out of this record.

## Setup

- Tools: `espefuse` and `esptool` v5.3.1 (read-only commands only: `summary`, `flash-id`, `read-mem`). Each connection resets the chip into ROM download mode through the USB-Serial/JTAG controller; `esptool` hard-resets it back afterwards.
- Firmware running before and after: the Kleidos `cores3_se_debug` image built from the firmware of 2026-11-17 (ELF SHA-256 `21e6a668298d8db0...`, ESP-IDF 6.0.3). It was left on the board unchanged.

## Results

| Read | Result |
| --- | --- |
| `espefuse summary`, Vdd fuses | `VDD_SPI_FORCE` = 0, `VDD_SPI_TIEH` = 0, `VDD_SPI_XPD` = 0: VDD_SPI is not forced by eFuse, so the GPIO45 strap decides it. |
| `espefuse summary`, other relevant fuses | `PKG_VERSION` = 0 (QFN56, no in-package flash or PSRAM), `FLASH_CAP` / `PSRAM_CAP` none, `SECURE_BOOT_EN` = 0, `SPI_BOOT_CRYPT_CNT` = 0, `DIS_USB_JTAG` = 1 (already burned before this probe), `UART_PRINT_CONTROL` = enable. |
| `esptool flash-id` | Chip ESP32-S3 (QFN56) revision v0.2. Flash JEDEC ID: manufacturer `0x46`, device `0x4018` (memory type `0x40`, density `0x18` = 128 Mbit); detected size 16 MB; "Flash voltage set by a strapping pin: 3.3V". |
| `esptool read-mem 0x60004038` (GPIO_STRAP_REG) | `0x00000020`. |
| `esptool read-mem 0x6000807C` (RTC_CNTL_SDIO_CONF_REG) | `0x0AB0BE0A`: bit 22 `SDIO_FORCE` = 0, so the regulator is not under software force either. |
| Boot log of the debug image | `esp_psram: Found 8MB PSRAM device`, `Speed: 80MHz`, `SPI SRAM memory test OK`, `Adding pool of 8192K of PSRAM memory`; the image is built with `CONFIG_SPIRAM_MODE_QUAD=y`. `spi_flash: detected chip: generic` although the image carries ESP-IDF's GigaDevice and Winbond chip drivers (`CONFIG_SPI_FLASH_SUPPORT_GD_CHIP`, `..._WINBOND_CHIP`), whose probes accept manufacturer `0xC8` and `0xEF` only. |
| Console `HEAP?` | `psram_total=8388608`. |
| Console `GPIO? 45`, `GPIO? 46` | Both `pu=0 pd=1 level=0`: the pad sits low on the chip's weak pull-down alone, so nothing on the board pulls it up. |
| Console `GPIO? 3`, `GPIO? 0` | GPIO3 `level=1` (in use by the firmware), GPIO0 `pu=1 level=1`. |

## What it proves

- **C1, C2, J1 (VDD_SPI and FLASH_VCC = 3.3 V):** confirmed. The eFuses do not force VDD_SPI, GPIO45 reads 0 on its internal pull-down with no external pull, and esptool reports the strap selects 3.3 V. On the bit layout: esptool v5.3.1 (`targets/esp32s3.py`) takes GPIO_STRAP_REG bit 4 as the VDD_SPI strap, as the ESP32-S2 register description does (bits 4..2 = GPIO45, GPIO0, GPIO46), and bit 4 reads 0; ESP-IDF 6.0.3 `esp_hw_support/port/esp32s3/rtc_init.c:232` reads bit 5 instead, which is set here. Bit 5 cannot be GPIO45 on this board: the pad has no pull-up and the 3.3 V flash runs. It is consistent with GPIO3, which R49 pulls up. The ROM banner's `boot:0x..` word was not captured (the USB-Serial/JTAG port re-enumerates during the reset, so the ROM's lines are lost); the latched register above replaces it.
- **B3 (U7 is 8 MB quad PSRAM):** confirmed by the device: 8 MB found and tested in quad mode at 80 MHz, all 8,192 KiB on the heap. With no PSRAM in the package, the 8 MB is the external U7.
- **U6 (new finding):** the flash on this unit is 128 Mbit / 16 MB, as printed, but its manufacturer byte is `0x46`, which is neither of the two parts the print names (GigaDevice GD25Q128 = `0xC8`, Winbond W25Q128 = `0xEF`). ESP-IDF's own probe agrees (it fell back to the generic driver). The vendor of `0x46` was not identified here; the part's marking would need the case opened, so U6's part number stays as printed and the unit's ID is only recorded.
