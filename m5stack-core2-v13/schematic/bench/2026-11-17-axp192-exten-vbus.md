# P04 (register half): EXTEN and the AXP192's VBUS after Kleidos's boot (2026-11-17)

Probe P04 of `../improvements.md` asks for a multimeter on Port A and an EXTEN write from the console. Neither was done: there was no one at the bench with a meter, and the write (`REGW!` on a critical register) needs the owner's go. This record is the read-only half that the console can do: what the AXP192 says about EXTEN and its VBUS input with the board on USB-C, after Kleidos's boot. Nothing was written; the case was not opened.

Firmware: Kleidos `core2_v13_debug`, the image already on the board (ELF SHA-256 prefix `a702778a98891b54`, built from the Kleidos firmware of 2026-11-17).

## Commands

`REGS? axp192` (decoded dump through the firmware's register map), `I2CRD 0x34 0x10 1` and `I2CRD 0x34 0x12 1` (raw reads; REG10H is not in the firmware's register map, so `REGR axp192 0x10` answers `unknown reg`), `POWER?`, `PMIC?`.

## Results

| Register | Value | Reading (AXP192 datasheet rev 1.1) |
| --- | --- | --- |
| REG10H | `0x01` | bit 2 (EXTEN, p. 36) = 0: EXTEN off |
| REG12H | `0x17` | bit 6 = 0 (the bit Kleidos's driver treats as EXTEN); DC-DC1, DC-DC3, LDO2 and DC-DC2 on, LDO3 off |
| REG00H | `0xC0` | ACIN present and usable; VBUS not present, not usable |
| REG30H | `0x42` | VBUS-IPSOUT path: VHOLD limit on, VBUS current limit on |
| REG5AH/5BH (VBUS voltage ADC) | `0x00 0x00` | 0 V, with the VBUS voltage ADC enabled (REG82H = `0xFF`) |
| REG90H (GPIO0) | `0x07` | floating: N_VBUSEN left to R5 |
| REG93H (GPIO2) | `0x05` | low output: the NS4168 held off |

`POWER?` gave 70.0 mA from USB on the PIN screen; `PMIC?` gave the cell at 4,117 mV, not charging.

## What it proves

After Kleidos's boot both candidate EXTEN bits read 0 (REG10H bit 2, the datasheet's EXTEN control, and REG12H bit 6), and the AXP192 sees no voltage on its VBUS input with its ADC on. So the 5 V boost is off after boot, whichever bit gates it; this does not show which of the two bits is the real gate (the Kleidos side note S4 stays a question until EXTEN is switched on and the bus measured). BUS_5V's value (5.03 V by the SY7088's divider, T32) is not measured: the multimeter half of P04 stays open.
