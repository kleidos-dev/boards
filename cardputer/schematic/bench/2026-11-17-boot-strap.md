# Cardputer-Adv: the ROM's boot line and the latched straps (P06)

- Date: 2026-11-17.
- Unit: the bench Cardputer-Adv, case closed, on USB from the bench hub, power switch on, nothing known to be plugged into the headphone jack, Grove port or EXT header.
- Firmware: irrelevant to the first line (printed by the chip's ROM before any firmware runs); the image on the board is the one named in `2026-11-17-i2c-scan.md`.
- Tool: the board's USB Serial/JTAG port opened with a reset (the control-line transition the ESP32-S3 reads as a reset request), capturing what arrives in the first six seconds.
- Settles: T32 (optional probe), and gives T11 a bench reading.

## What came back

```text
ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x15 (USB_UART_CHIP_RESET),boot:0x2b (SPI_FAST_FLASH_BOOT)
```

## How the value reads

`boot:` prints the GPIO strapping register (`GPIO_STRAP_REG`, 0x60004038). The *ESP32-S3 Technical Reference Manual* v1.8, Register 6.15 (p. 506), gives its bits: bits 0 and 1 reserved, bit 2 GPIO46, bit 3 GPIO0, bit 4 GPIO45, bit 5 GPIO3. Two other Espressif sources agree: esptool's `esp32s3.py` (`GPIO_STRAP_SPI_BOOT_MASK = 1 << 3`, "not download mode", tested as "GPIO0 low" when clear; `GPIO_STRAP_VDDSPI_MASK = 1 << 4`) and ESP-IDF's `components/soc/esp32s3/include/soc/boot_mode.h` (`1xxx` SPI boot, `00xx` joint download boot).

0x2b = 0b10_1011: bit 5 = 1 (GPIO3 high), bit 4 = 0 (GPIO45 low), bit 3 = 1 (GPIO0 high), bit 2 = 0 (GPIO46 low).

Reset 0x15, the USB Serial/JTAG reset, is a Core Reset (TRM Table 7.1-1, p. 528), and the strapping latches sample only at a Chip Reset (TRM Section 8.1, p. 534; datasheet Section 3). So the value is what the pins latched at the board's last power-up, not at this reset.

## Result

- GPIO0 latched high: SPI boot, from the board's pull-ups (R18, R104) with the side key released.
- GPIO46 latched low with the ES8311's ASDOUT attached to it: the codec does not hold the strap high at power-up, so holding G0 while the board powers up selects download boot, as the vendor's procedure says (T32).
- GPIO45 latched low: the VDD_SPI strap selects 3.3 V for the flash supply unless an eFuse forces VDD_SPI (datasheet Table 3-4), and 3.3 V is the FN8's VDD_SPI (Table 1-1), which is what T11 states.
- GPIO3 latched high. It is floating on this board (EXT P3 pin 1 only, nothing plugged in) and has no internal pull (datasheet Section 3.4), so this reading says nothing lasting; it matters only if the eFuse that hands JTAG to the strap is burnt.
- **Not run:** the second half of P06 (G0 held, expecting a download-boot line). It needs a person to hold the side key, and a Chip Reset (a power-up: the reset key BTN1 holds EN, the chip's CHIP_PU through L107, low), not the USB reset used here, because a Core Reset does not re-latch the straps; no one was at the bench. Open, and no longer needed for T32: the latched GPIO46 = 0 above is what that half was meant to show.
- Reviewed on 2026-11-17: the bit meanings first came from esptool and ESP-IDF, with bit 2 deduced; the TRM register description above now states them, and agrees.
