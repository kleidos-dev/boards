<img src="icon.svg" width="96" height="96" alt="StickS3 icon"> <a href="svg/front.svg"><img src="svg/front.svg" width="226" height="320" alt="StickS3 front drawing, true to scale: the case, the screen, the controls and the printed legends"></a>

# StickS3

M5Stack · SKU **K150** [1]

Every value below comes from [`board.json`](board.json), where each one carries the id of its source; the numbers in brackets point to the sources listed at the end of this page. This page is written from that file by [`_shared/emit_board_readme.py`](../_shared/emit_board_readme.py): change the file, then run the script.

Vendor links: [docs](https://docs.m5stack.com/en/core/StickS3)

## Dimensions

| Width | Height | Depth | Weight |
| --- | --- | --- | --- |
| 24.0 mm | 48.0 mm | 15.0 mm | 20.0 g |

The vendor gives the product size as 48.0 x 24.0 x 15.0 mm, the package as 65.0 x 25.0 x 15.0 mm and the gross weight as 22.4 g. The back is magnetic. Operating temperature 0 to 40 °C. [1] [12]

## Components

40 entries (60 parts counting quantities).

### Processing and memory

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| ESP32-S3-PICO-1-N8R8 (Espressif) | soc | U20 | 1 | type: system in package; package: LGA56, 7 x 7 mm; cpu: Xtensa dual-core 32-bit LX7 with single-precision FPU, up to 240 MHz; rom kb: 384; sram kb: 512; rtc sram kb: 16; flash: 8 MB Quad SPI, in package; psram: 8 MB Octal SPI, in package; crystal: 40 MHz, in package; wifi: IEEE 802.11b/g/n, 2.4 GHz, 2412 to 2484 MHz; bluetooth: Bluetooth 5 (LE), Bluetooth mesh; usb: USB 1.1 OTG and USB Serial/JTAG controller; supply v: 3.0 to 3.6; ambient temp c: -40 to 65 — CHIP_PU (pin 4) is the net SOC_RESET: an RC reset of R40 10k pull-up to 3V3_L2 and C50 1 uF to GND, also brought to test point TP6. GPIO0 (pin 5) is G0_BOOT_OUT, pulled up by R46 10k to 3V3_L2 and driven by the PMIC. Pins without a net on the board: GPIO26/SPICS1 (pin 28), GPIO33 to GPIO37 (pins 38 to 42) and the SPI flash pins 29 to 35; on the N8R8 the datasheet gives SPICS1 and GPIO33 to GPIO37 to the in-package Octal PSRAM. XTAL_P/XTAL_N (pins 53, 54) are unconnected. VDD3P3 (pins 2, 3) is fed from 3V3_L2 through L4 2 nH; VDDA, VDD3P3_RTC and VDD3P3_CPU are on 3V3_L2. GPIO15/GPIO16, the 32 kHz crystal pins, carry I2S, so no 32 kHz crystal is fitted. | [2] [3] [1] |
| — | flash | — | 1 | capacity mb: 8; interface: Quad SPI; location: inside the ESP32-S3-PICO-1-N8R8 package; spi voltage v: 3.3 | [3] [1] |
| — | psram | — | 1 | capacity mb: 8; interface: Octal SPI; location: inside the ESP32-S3-PICO-1-N8R8 package; uses pins: SPICS1, GPIO33 to GPIO37 — With the PSRAM ECC function enabled the maximum ambient temperature rises to 85 °C and the usable PSRAM shrinks by 1/16. | [3] [1] |

### Power

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| PY32L020F15U6 | pmic | U16 | 1 | name: M5PM1; type: microcontroller running M5Stack's power-management firmware; package pins: 20; supply: 3V3_L0 (always on); i2c address: 0x6E; i2c speed: 100 kHz (default) or 400 kHz; gpio: 5 (PYG0 to PYG4): 2 usable as 12-bit ADC, 2 as PWM, 1 as LED (NeoPixel) output; adc inputs: 5VIN_ADC, 5VOUT_ADC, BAT_ADC; power levels: L0 shipping, L1 standby, L2 deep sleep, L3A core active, L3B all active — The schematic's power-mode diagram: power-up turns L1 on; a single click of the power key or the IMU interrupt makes the PMIC turn L2 on (L3A); a double click or an I2C command from the ESP32-S3 turns L2, L3A and L3B off again (back to L1), and an I2C L0 command drops to L0; PYG2 turns L3B on and off (the LCD SPI off first); the ESP32-S3 goes from L3A to L2 by entering sleep in software, and comes back on its own IO, its RTC, or the PMIC pulling the IRQ line low, the diagram listing as triggers a single click of KEY1/KEY2, the IMU interrupt and a CHG_STAT change; a double click of the power key also turns L2 off. Vendor power figures at 4.2 V: power off 14.02 uA, L1 52.47 uA, L2 102.40 uA, L3A 36.69 mA, full load 519.02 mA. A single click of the power key powers on or resets, a double click powers off, holding it until the green LED blinks enters download mode. The page-1 audio block of the schematic names PYG2 as SPK_EN and PYG1 as L3B_EN; the detailed sheets and the vendor PinMap give PYG2 = L3B enable and PYG3 = speaker pulse, which this file follows. Test points: TP1 GND, TP2 PY_STATUS_LED, TP4 3V3_L2, TP5 3V3_L0. | [2] [1] [4] |
| LGS4056 | charger | U15 | 1 | charge current ma: 190; prog resistor: R12 4.7k/1 %; input: Internal_5V (VCC, C22 22 uF); output: VBAT_L0 (BAT) — DONE (pin 6) is unconnected; TEMP (pin 1) is tied to GND. The schematic notes the charge current as 190 mA. | [2] |
| CM1801F33 | regulator | U1, U3, U4 | 3 | type: LDO; output v: 3.3; max current ma: 500; quiescent current ua: 0.8; input: VBUS_L0 | [2] |
| JW5712 | regulator | U2 | 1 | type: DC-DC buck; output v: 3.3; max current ma: 600; input: VBUS_L0 (C2/C3 22 uF); output: 3V3_L2 (C11/C12 22 uF); inductor: L1 2.2 uH FTC121065S2R2MBCA — VSEL1 to VSEL3 are tied to VBUS_L0. C9 1 nF/50 V on the switch node side. | [2] |
| SY7088 | regulator | U9 | 1 | type: DC-DC boost; input: VBUS_L0 (C16/C17/C18 22 uF); input current max a: 1; output: BOOST_OUT (C23/C24 22 uF); output current max a: 0.6; inductor: L2 2.2 uH; feedback: R13 147k/1 % over R14 46.4k/1 % — The schematic gives the divider rule Rd = 1.2 V / (Vout - 1.2) x Ru; with R13 147k and R14 46.4k that is Vout = 1.2 x (1 + 147/46.4) = 5.0 V. The vendor states the Grove load capacity as 5 V with no load and 4.88 V at 0.38 A. | [2] [1] |
| — | battery | — | 1 | chemistry: lithium; capacity mah: 250 | [2] [1] |

### Display and touch

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| — | display panel | — | 1 | technology: IPS TFT LCD; diagonal in: 1.14; resolution px: 135 / 240; supply: 3V3_L3B | [2] [1] |
| ST7789P3 | display controller | — | 1 | interface: SPI, write only (no MISO line), with a separate RS (data/command) line; resolution px: 135 / 240 — The controller sits on the panel. The backlight is lit from 3V3_L3B through R27 10R into LCD connector pin 10 and sunk by Q6 (2N7002T) on pin 12, so GPIO38 switches or dims it only while L3B is on. The schematic's page-1 overview draws a PMOS for LCD_BL; the detailed sheet has the N-channel Q6. | [2] [1] |

### Sensors and timekeeping

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| BMI270 | imu | U17 | 1 | axes: 6 (3-axis accelerometer + 3-axis gyroscope); interface: I2C; i2c address: 0x68; supply: 3V3_L1 (VDD and VDDIO, C33/C35 100 nF) — CSB (pin 12) is tied to 3V3_L1 (I2C mode) and SDO (pin 1) to GND; INT2, ASDx, ASCx, OCSB and OSDO are unconnected. INT1 does not reach an ESP32-S3 pin directly: the PMIC can pass it on as its IRQ line. | [2] [1] |

### Audio

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| ES8311 | audio codec | U18 | 1 | channels: mono; resolution bits: 24; interface: I2S + I2C; i2c address: 0x18; supply: 3V3_L3B_AU (PVDD, DVDD, AVDD; C32/C34 10 uF, C44 1 uF) — CE (pin 20) is tied to AGND. VMID, ADCVREF and DACVREF are decoupled with 1 uF to AGND (C40, C41, C42). AGND joins GND at one point through R35 0R. | [2] [1] |
| MSM381A3729H9BPC | microphone | U21 | 1 | type: MEMS, analog output; snr db: 65; supply: 3V3_L3B_AU through R52 100R, C65 100 nF — MIC1_N reaches AGND through two 0R in series: R49 from MIC1_N to the microphone's GND pin 3 (net U21_GND3), and R26 from there to AGND. | [2] [1] |
| AW8737A | audio amp | U19 | 1 | supply: VBUS_L0 (VDD, A3 and B3; C36 22 uF); pvdd: D3 PVDD is the charge pump's output, on its own net U19_PVDD with C37 22 uF (AW8737A datasheet V1.2, p. 3); charge pump caps: C46, C47 2.2 uF; inputs: differential, DAC_L_P/DAC_L_N through R31/R32 10k — The M5PM1 manual describes PWM-based AW8737A control of the signal amplitude on the SHDN line. The vendor recommends staying below 75 % volume on battery to avoid an unexpected reboot, and the speaker amplifier must be off for the IR receiver to work. | [2] [1] [4] [7] |
| — | speaker | U4 (IR/speaker board) | 1 | impedance ohm: 8; power w: 1; type: 2011 cavity speaker — Connects to SPK_P (pin 2) and SPK_N (pin 1) of U4 on the IR/speaker board. The schematic in this repository numbers the IR/speaker board's parts +100 (U4 is U104 there), and the vendor's page 1 prints the rating, SPK 8 ohm @ 1 W. | [2] [1] |

### Input and indicators

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| IR928-6C/F1(6-1) | ir led | U3 (IR/speaker board) | 1 | supply: 5V_VBUS (the GROVE_5V / EXT_5V rail); series resistor: R2 10R — Needs the 5 V port powered, either from EXT_5V_EN output mode or from an external 5 V input. The schematic in this repository numbers the IR/speaker board's parts +100: U3 is U103, Q1 Q101, R1 R101, R2 R102, R3 R103. | [2] [1] |
| — | led | LED1 | 1 | color: green; location: inside the case; driver: Q3 2N7002T low side; series resistor: R25 1k from 3V3_L0 — Driven by the PMIC, not by an ESP32-S3 GPIO. The vendor docs call it a green LED (it blinks when the power key is held into download mode); the schematic prints no color. On the owner's unit it is green and sits inside the case (owner observed on his unit, 2026-11-17). | [2] [1] [4] [11] |
| — | button | S1 | 1 | function: power key; active: low (to GND) — Read by the PMIC only. Single click: power on / reset; double click: power off; hold until the green LED blinks: download mode. | [2] [1] |
| — | button | S2 | 1 | function: KEY1; active: low (to GND); debounce cap: C52 1 nF/25 V | [2] [1] |
| — | button | S3 | 1 | function: KEY2; active: low (to GND); debounce cap: C53 1 nF/25 V | [2] [1] |

### Radio and positioning

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| — | antenna | J5 (ANT_PAD) | 1 | band: 2.4 GHz; feed: 50 ohm line to LNA_IN; matching: L3, L5 0R (TBD) in series; C56, C69, C60, C63 not fitted (TBD) to GND — The antenna attaches at a two-pad feed (pin 1 RF, pin 2 GND). The vendor warns that opening the enclosure can damage the antenna's flexible circuit. | [2] [1] |

### Connectors, storage and USB

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| AXE512127D | connector | — | 1 | type: board-to-board, 12 signal pins + 4 mounting pins; pinout: 1: G41_LCD_CS; 2: GND; 3: 3V3_L3B; 4: not connected; 5: G40_SCK; 6: G48_SCL; 7: G39_MOSI; 8: G47_SDA; 9: G45_LCD_RS; 10: 3V3_L3B through R27 10R (backlight anode); 11: G21_LCD_RST; 12: Q6 drain (backlight cathode); 13-16: mounting pins, GND — The connector also carries the main I2C bus (pins 6 and 8). C51 1 uF on 3V3_L3B. | [2] |
| — | connector | J4 | 1 | pins: 2; pinout: 1: VBAT_L0; 2: GND — C26 22 uF/16 V across the battery. | [2] |
| USB_C_16P_Horizontal | connector | J1 | 1 | type: USB Type-C receptacle, 16 pins, horizontal; input: DC 5 V; data: USB 2.0 D+/D- to the ESP32-S3 native USB; sbu: not connected — The vendor's PinMap and labels call it the download port as well as the power input. | [2] [1] |
| HY2.0-4P | connector | J3 | 1 | name: PORT.A (vendor label PORT.CUSTOM); pinout: 1: GND (black); 2: GROVE_5V (red); 3: GPIO9 (yellow); 4: GPIO10 (white); load capacity: 5 V no load, 4.88 V at 0.38 A — GROVE_5V is an output while the PMIC drives EXT_5V_EN high (boost U9 through U8) and an input while it is low (through U12 and D10 to the charger). The vendor's default library initialization leaves it in input mode. In output mode power may only come in over USB or the Hat2 bus 5V_IN pin. | [2] [1] |
| — | connector | J2 (main board), CN1 AXE524124 (IR/speaker board) | 1 | type: board-to-board, 24 signal pins + 4 mounting pins, between the main board and the IR/speaker board; pinout j2: 1, 3: VBAT_L0; 2, 4: HAT2_5VIN; 5, 7: GND; 6, 8: GROVE_5V; 9: 3V3_L2; 10: G0_BOOT_OUT; 11: SPK_P; 12: EXT_GPIO4; 13: SPK_N; 14: EXT_GPIO5; 15: G46_IR_TX; 16: EXT_GPIO6; 17: G42_IR_RX; 18: EXT_GPIO7; 19: EXT_GPIO1; 20: EXT_GPIO8; 21: EXT_GPIO2; 22: EXT_GPIO43; 23: EXT_GPIO3; 24: EXT_GPIO44; 25-28: mounting pins, GND — On the IR/speaker board the same nets are named EXT_BAT (VBAT_L0), 5V_IN (HAT2_5VIN), 5V_VBUS (GROVE_5V), SYS_3V3 (3V3_L2), BOOT_OUT, LED_TX and LED_RX. The schematic in this repository numbers the IR/speaker board's parts +100: CN1 is CN101 there. | [2] |
| — | connector | CN2 (IR/speaker board) | 1 | name: Hat2-Bus; type: 2 x 8 female header, 2.54 mm pitch, 8.5 mm plastic height; pinout: 1: GND; 2: GPIO5; 3: EXT_5V; 4: GPIO4; 5: Boot (GPIO0, G0_BOOT_OUT); 6: GPIO6; 7: GPIO1; 8: GPIO7; 9: GPIO8; 10: GPIO43; 11: BAT; 12: GPIO44; 13: 3V3_L2; 14: GPIO2; 15: 5V_IN; 16: GPIO3; gpio count: 11 — Pin numbers follow the vendor's PinMap (odd pins in the left column, even in the right); the schematic numbers the same header 1 to 8 down one side and 9 to 16 up the other (schematic 1 GND, 2 5V_VBUS, 3 BOOT_OUT, 4 EXT_GPIO1, 5 EXT_GPIO8, 6 EXT_BAT, 7 SYS_3V3, 8 5V_IN, 9 EXT_GPIO3, 10 EXT_GPIO2, 11 EXT_GPIO44, 12 EXT_GPIO43, 13 EXT_GPIO7, 14 EXT_GPIO6, 15 EXT_GPIO4, 16 EXT_GPIO5). The schematic's feature table describes it as a 2 x 8 female header with 11 GPIO, 5V in, 5V out and 3V3. The vendor states the StickS3 is structurally incompatible with Hat Mini JoyC (U156), Hat Mini EncoderC (U157) and Hat 18650C (U080). The schematic in this repository numbers the IR/speaker board's parts +100: CN2 is CN102 there. | [2] [1] |

### Protection

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| ESD5311 | esd | D1, D2, TVS1, TVS2 | 4 | function: ESD protection diodes to GND — D1 on USB_N and D2 on USB_P at the USB-C receptacle; TVS1 on GROVE_G10 and TVS2 on GROVE_G9 at the Grove port. | [2] |

### Other parts

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| AW32901FCR | other | U7 | 1 | function: input over-voltage protection switch; ovp v: 5.95; input: VUSBIN_L0 (C13 22 uF); output: 5VIN_L0 (C19 22 uF) — nEN is tied to GND (always enabled); OVLO goes to GND through R8 0R and R7, from IN to OVLO, is not fitted; nACOK is unconnected. With OVLO on GND the AW32901 uses its internal threshold, 5.95 V rising (5.83 to 6.07 V, 130 mV hysteresis; datasheet V1.1, p. 1, p. 2 and p. 4 note 2); the schematic writes OVP = 5V. | [2] [5] |
| CH213K | other | U6, U11, U13, U14 | 4 | function: power-path diode (VIN to VOUT), drawn as a diode on the power network — U6: 5VIN_L0 (USB) to Internal_5V. U11: HAT2_5VIN (Hat2 bus 5V_IN) to Internal_5V. U13: Internal_5V to VBUS_L0. U14: VBAT_L0 to VBUS_L0. VBUS_L0, the system rail every regulator draws from, is fed from either the 5 V input or the battery. | [2] |
| RB162VAM-20TR | other | D10 | 1 | function: diode from the U12 output to Internal_5V — Lets 5 V brought in on the Grove port or the Hat2 EXT_5V pin reach Internal_5V (the charger input) through U12; C25 22 uF on the anode side. | [2] |
| TPS22916CNYFPR | other | U8 | 1 | function: load switch, BOOST_OUT to GROVE_5V (C15/C20 22 uF) — Output mode of the 5 V port: with EXT_5V_EN high the boost and this switch drive GROVE_5V, which feeds the Grove port, the Hat2 EXT_5V pin and the IR emitter and receiver. | [2] [1] |
| AW35122FDR | other | U5, U12 | 2 | function: load switch | [2] [1] |
| 2N7002T | other | Q1, Q3, Q6 | 3 | type: N-channel MOSFET — Q1 pulls U12's EN low when EXT_5V_EN is high. Q3 sinks the status LED (gate PY_STATUS_LED through R29 0R, R28 10k gate pull-down). Q6 sinks the LCD backlight (gate G38_LCD_BL, R43 5.1k gate pull-down). The IR emitter's driver on the IR/speaker board is also called Q1 (Q101 in this repository's schematic) but its part is not named. | [2] |
| CJ3439KDW | other | Q2 | 1 | type: dual MOSFET: Q2A N-channel (pins 1 S, 2 G, 6 D), Q2B P-channel (pins 3 D, 4 S, 5 G) — Battery-voltage sampling switch: Q2A, driven by VBAT_ADC_EN, turns Q2B on to connect VBAT_L0 to the R23/R24 divider. The channels and pins are the CJ3439KDW datasheet's (rev D, p. 1, equivalent circuit), which the schematic agrees with. | [2] [6] |
| 2N7002DW | other | Q4, Q5 | 2 | type: dual N-channel MOSFET; function: I2C hot-plug isolation between the main bus (3V3_L2) and the audio bus (3V3_L3B_AU) — One gate of each pair is on 3V3_L3B_AU and the other on 3V3_L2, so the codec's bus is cut from the main bus while the L3B audio rail is off. | [2] |
| VSOP38338 | other | U1 (IR/speaker board) | 1 | function: infrared receiver; supply: 5V_VBUS (VCC, C2 10 uF) — The schematic draws a part U2 with a photodiode symbol between U1's IN (pin 7) and GND; it names no part number. The VSOP383.. datasheet describes the part for use with an outside photo PIN diode on IN (pin 7), and gives pins 1, 4 and 5 as N.C., 2 VS, 3 OUT, 6 and 8 GND, as drawn. The schematic in this repository numbers the IR/speaker board's parts +100: U1 is U101, U2 U102, R5 R105, R6 R106, C2 C102. The vendor states the receiver must be decoded with the ESP32 RMT peripheral, needs the speaker amplifier off, and needs at least 30 cm to the transmitter. | [2] [1] |
| SDMM0806H-2-900T | other | FT1 | 1 | function: common-mode filter on the USB data pair | [2] |
| — | other | TP1-TP9 | 9 | nets: TP1: GND; TP2: PY_STATUS_LED; TP3: G0_BOOT_OUT; TP4: 3V3_L2; TP5: 3V3_L0; TP6: SOC_RESET; TP8: EXT_GPIO43; TP9: EXT_GPIO44 — TP7 does not appear on the schematic. | [2] |

## Connections

Each row is one fact of wiring, read from the component in the first column; a row without sources of its own takes its component's.

| From | To | Bus | Address | Pins | Pulls | Notes | Src |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ESP32-S3-PICO-1-N8R8 | USB_C_16P_Horizontal | USB |  | GPIO19 (pin 25) → G19_DM -> FT1 -> R45 -> USB_N (J1 A7/B7)<br>GPIO20 (pin 26) → G20_DP -> FT1 -> R44 -> USB_P (J1 A6/B6) |  | The native USB pins reach the USB-C receptacle through the common-mode filter FT1 and the series resistors R44/R45 (22R/1 % each). | [2] |
| ESP32-S3-PICO-1-N8R8 | antenna J5 (ANT_PAD) | RF |  | LNA_IN (pin 1) → J5 ANT_PAD pin 1 through the matching network L3/L5 |  | 50 ohm line. | [2] |
| ESP32-S3-PICO-1-N8R8 | connector J2 (main board), CN1 AXE524124 (IR/speaker board) |  |  | GPIO1 (pin 6) → EXT_GPIO1<br>GPIO2 (pin 7) → EXT_GPIO2<br>GPIO3 (pin 8) → EXT_GPIO3<br>GPIO4 (pin 9) → EXT_GPIO4<br>GPIO5 (pin 10) → EXT_GPIO5<br>GPIO6 (pin 11) → EXT_GPIO6<br>GPIO7 (pin 12) → EXT_GPIO7<br>GPIO8 (pin 13) → EXT_GPIO8<br>GPIO43/U0TXD (pin 49) → EXT_GPIO43 through R50 499R<br>GPIO44/U0RXD (pin 50) → EXT_GPIO44 |  | EXT_GPIO43 and EXT_GPIO44 also reach test points TP8 and TP9. | [2] |
| PY32L020F15U6 | ESP32-S3-PICO-1-N8R8 | I2C | 0x6E | I2C_SCL_OD (pin 9) → GPIO48<br>I2C_SDA_OD (pin 8) → GPIO47 | SCL: up 2.2k to 3V3_L2 (R38)<br>SDA: up 2.2k to 3V3_L2 (R39) |  | [2] [1] [4] |
| PY32L020F15U6 | ESP32-S3-PICO-1-N8R8 |  |  | G1_IRQout_ADC (pin 17, PYG1_IRQ) → GPIO13 |  | No pull resistor on this line. | [2] [1] |
| PY32L020F15U6 | ESP32-S3-PICO-1-N8R8 |  |  | BOOT_OUT_OD (pin 15) → GPIO0 (G0_BOOT_OUT) | G0_BOOT_OUT: up 10k to 3V3_L2 (R46) | Open-drain output that holds the strapping pin GPIO0 low to enter download mode. G0_BOOT_OUT also reaches the Hat2 bus (Boot) and test point TP3. | [2] [4] |
| PY32L020F15U6 | CM1801F33 |  |  | LDO3V3_EN_PP (pin 18) → 3V3_L1_EN (U4 EN)<br>G2_WAKEin_IRQout_ADC (pin 20, PYG2_L3B_EN) → U1 EN |  |  | [2] |
| PY32L020F15U6 | JW5712 |  |  | DCDC3V3_EN_PP (pin 14) → 3V3_L2_EN (U2 EN) |  |  | [2] |
| PY32L020F15U6 | SY7088 |  |  | BOOST5V_EN_PP (pin 10) → EXT_5V_EN (U9 EN, U8 EN, Q1 gate) |  |  | [2] |
| PY32L020F15U6 | AW35122FDR |  |  | G2_WAKEin_IRQout_ADC (pin 20, PYG2_L3B_EN) → U5 EN |  |  | [2] |
| PY32L020F15U6 | LGS4056 |  |  | CHG_EN_PP (pin 2) → CHG_EN (U15 CE)<br>G0_WAKEin_IRQout_NEOPIXEL (pin 3, PYG0_CHG_STAT) → U15 CHRG | PYG0_CHG_STAT: up 100k to 3V3_L0 (R16) |  | [2] [1] |
| PY32L020F15U6 | BMI270 |  |  | G4_WAKEin_IRQout_PWM (pin 12, PYG4_IMU_INT) → BMI270 INT1 |  |  | [2] [1] |
| PY32L020F15U6 | AW8737A |  |  | G3_WAKEin_IRQout_PWM (pin 13, PYG3_SPK_Pulse) → AW8737A SHDN |  |  | [2] [1] |
| PY32L020F15U6 | led LED1 |  |  | LED_EN_PP (pin 5, PY_STATUS_LED) → Q3 gate through R29 0R |  |  | [2] |
| PY32L020F15U6 | button S1 |  |  | BTN_PU (pin 7) → PWR_BTN | PWR_BTN: up 10k to 3V3_L0 (R17) | C27 10 nF/50 V from PWR_BTN to GND. | [2] |
| PY32L020F15U6 | battery |  |  | BAT_ADC_IN (pin 11) → VBAT_ADC<br>BAT_ADC_EN_OD (pin 1) → VBAT_ADC_EN |  | VBAT_ADC_EN drives Q2A, which switches Q2B (CJ3439KDW) to connect VBAT_L0 to the R23/R24 1k/1k divider (C30 100 nF), so the divider draws nothing while sampling is off. R15 100k sits between VBAT_L0 and Q2B's gate, R9 10k from VBAT_ADC_EN to GND. The schematic names pin 1 BAT_ADC_EN_OD (open drain); the M5PM1 manual V1.9 (Table 1, p. 2) calls it a push-pull output. The two vendor documents disagree; this file keeps both. | [2] [4] |
| PY32L020F15U6 | HY2.0-4P |  |  | 5VOUT_ADC_IN (pin 19) → EXT_5V_ADC: GROVE_5V through R21/R22 10k/10k, C28 100 nF<br>5VIN_ADC_IN (pin 16) → 5VIN_ADC: 5VIN_L0 through R19/R20 10k/10k, C29 100 nF |  |  | [2] |
| LGS4056 | battery |  |  | BAT (pin 5) → VBAT_L0 |  |  | [2] |
| LGS4056 | PY32L020F15U6 |  |  | CHRG (pin 7) → PYG0_CHG_STAT<br>CE (pin 8) → CHG_EN | CHRG: up 100k to 3V3_L0 (R16)<br>CE: down 1M (R18) | PYG0 reads 0 while U15 charges and 1 when it does not (charging stopped, or the cell full), measured with USB in. | [2] [9] |
| AW32901FCR | USB_C_16P_Horizontal |  |  | IN (B3, C2, C3) → VUSBIN_L0 (VBUS) |  |  | [2] [5] |
| CM1801F33 | PY32L020F15U6 |  |  | U3 OUT → 3V3_L0<br>U3 EN → tied to VIN (always on) |  | L0 rail: powers the PMIC, the power-key and LED pull-ups and the charge-status pull-up. C5/C10 1 uF. | [2] |
| CM1801F33 | BMI270 |  |  | U4 OUT → 3V3_L1<br>U4 EN → 3V3_L1_EN | 3V3_L1_EN: down 1M (R5) | L1 rail: the BMI270 only. C4/C8 1 uF. | [2] |
| CM1801F33 | ES8311 |  |  | U1 OUT → 3V3_L3B_AU<br>U1 EN → PYG2_L3B_EN | PYG2_L3B_EN: down 100k (R1) | L3B audio rail: the ES8311, the microphone and the audio-side I2C pull-ups. C1/C6 1 uF. | [2] |
| JW5712 | ESP32-S3-PICO-1-N8R8 |  |  | VOS/SW → 3V3_L2 |  | L2 rail: the ESP32-S3, its keys, reset and I2C pull-ups, the U5 LCD switch and the Hat2 bus 3V3 pin. | [2] |
| JW5712 | PY32L020F15U6 |  |  | EN (B1) → 3V3_L2_EN | 3V3_L2_EN: down 1M (R2) |  | [2] |
| SY7088 | PY32L020F15U6 |  |  | EN (pin 3) → EXT_5V_EN | EXT_5V_EN: down 100k (R10) |  | [2] [1] |
| SY7088 | TPS22916CNYFPR |  |  | OUT (pins 7, 8) → BOOST_OUT |  |  | [2] [1] |
| TPS22916CNYFPR | SY7088 |  |  | IN (A2) → BOOST_OUT |  |  | [2] [1] |
| TPS22916CNYFPR | HY2.0-4P |  |  | OUT (A1) → GROVE_5V |  |  | [2] [1] |
| TPS22916CNYFPR | PY32L020F15U6 |  |  | EN (B2) → EXT_5V_EN |  |  | [2] [1] |
| AW35122FDR | display panel |  |  | U5 IN (A2) → 3V3_L2<br>U5 OUT (A1) → 3V3_L3B (C14 1 uF; C7 1 uF is on the input, 3V3_L2)<br>U5 EN (B2) → PYG2_L3B_EN |  | L3B LCD rail. | [2] [1] |
| AW35122FDR | HY2.0-4P |  |  | U12 IN (A2) → GROVE_5V<br>U12 OUT (A1) → D10 anode<br>U12 EN (B2) → R11 100k to GROVE_5V, pulled low by Q1 (2N7002T) when EXT_5V_EN is high | U12 EN: up 100k to GROVE_5V (R11) | Input mode of the 5 V port: with EXT_5V_EN low, 5 V applied to GROVE_5V reaches Internal_5V through U12 and D10. C21 22 uF on GROVE_5V. | [2] [1] |
| 2N7002DW | ES8311 | I2C |  | Q4A/Q4B → G48_SCL <-> AUDIO_I2C_SCL<br>Q5A/Q5B → G47_SDA <-> AUDIO_I2C_SDA | AUDIO_I2C_SCL: up 2.2k to 3V3_L3B_AU (R33)<br>AUDIO_I2C_SDA: up 2.2k to 3V3_L3B_AU (R34) |  | [2] |
| display panel | AXE512127D |  |  |  |  | The panel plugs into the 12-pin board-to-board connector. | [2] [1] |
| ST7789P3 | ESP32-S3-PICO-1-N8R8 | SPI |  | MOSI → GPIO39<br>SCK → GPIO40 through R51 22R<br>RS → GPIO45<br>CS → GPIO41<br>RST → GPIO21<br>BL → GPIO38 (gate of Q6) | CS: up 10k to 3V3_L3B (R41)<br>BL (Q6 gate): down 5.1k (R43) |  | [2] [1] |
| BMI270 | ESP32-S3-PICO-1-N8R8 | I2C | 0x68 | SCx (pin 13) → GPIO48<br>SDx (pin 14) → GPIO47 |  |  | [2] [1] |
| BMI270 | PY32L020F15U6 |  |  | INT1 (pin 4) → PYG4_IMU_INT | INT1: up 100k to 3V3_L1 (R6) |  | [2] [1] |
| ES8311 | ESP32-S3-PICO-1-N8R8 | I2S |  | MCLK (pin 2) → GPIO18 through R47 22R<br>SCLK (pin 6) → GPIO17<br>LRCK (pin 8) → GPIO15<br>ASDOUT (pin 7) → GPIO16 (I2S_DADC, codec to ESP32-S3)<br>DSDIN (pin 9) → GPIO14 (I2S_DDAC, ESP32-S3 to codec) |  |  | [2] [1] |
| ES8311 | 2N7002DW | I2C | 0x18 | CCLK (pin 1) → AUDIO_I2C_SCL<br>CDATA (pin 19) → AUDIO_I2C_SDA |  | Reaches the ESP32-S3's GPIO48/GPIO47 through the isolation MOSFETs. | [2] [1] |
| ES8311 | MSM381A3729H9BPC |  |  | MIC1P (pin 18) → MIC1_P through C38 1 uF<br>MIC1N (pin 17) → MIC1_N through C39 1 uF |  |  | [2] |
| ES8311 | AW8737A |  |  | OUTN (pin 13) → DAC_L_N through C43 33 nF<br>OUTP (pin 12) → DAC_L_P through C45 33 nF |  |  | [2] |
| MSM381A3729H9BPC | ES8311 |  |  | OUT (pin 4) → MIC1_P through R48 0R<br>GND (pin 3) → MIC1_N through R49 0R |  |  | [2] |
| AW8737A | PY32L020F15U6 |  |  | SHDN (A4) → PYG3_SPK_Pulse | SHDN: down 100k (R30) |  | [2] |
| AW8737A | speaker U4 (IR/speaker board) |  |  | VOP (B4) → SPK_P through FB1 120R@100MHz<br>VON (D4) → SPK_N through FB2 120R@100MHz |  | C48/C49 100 pF/50 V to GND after the ferrites. SPK_P/SPK_N cross to the IR/speaker board on the J2 board-to-board connector (pins 11, 13). | [2] |
| IR928-6C/F1(6-1) | ESP32-S3-PICO-1-N8R8 |  |  | LED_TX (driver Q1 gate through R3 22R) → GPIO46 (G46_IR_TX, J2 pin 15) | Q1 gate: down 10k (R1 (IR/speaker board)) | Active high: GPIO46 high turns Q1 on and the emitter conducts from 5V_VBUS through R2 to GND. | [2] [1] |
| VSOP38338 | ESP32-S3-PICO-1-N8R8 |  |  | OUT (pin 3) → GPIO42 (G42_IR_RX, J2 pin 17) through R6 10k, with R5 20k to GND |  | R6 10k and R5 20k divide the 5 V output down for the 3.3 V GPIO. The VSOP38338's output has an internal pull-up of about 33 kohm to VS (datasheet doc 82748 rev 1.6, p. 1), so its idle high reaches GPIO42 at about 5 V x 20/63, about 1.6 V, below the ESP32-S3's input-high threshold of 0.75 x 3.3 V; on the bench GPIO42 read low in 150 of 150 reads at idle with GROVE_5V at 5.1 V, which a fitted receiver and an absent one both give. | [2] [1] [8] [3] [10] |
| led LED1 | PY32L020F15U6 |  |  | Q3 gate → PY_STATUS_LED (LED_EN_PP, pin 5) through R29 0R | Q3 gate: down 10k (R28) |  | [2] |
| button S1 | PY32L020F15U6 |  |  | S1 → PWR_BTN (BTN_PU, pin 7) | PWR_BTN: up 10k to 3V3_L0 (R17) |  | [2] [1] |
| button S2 | ESP32-S3-PICO-1-N8R8 |  |  | S2 → GPIO11 (G11_KEY1) | G11_KEY1: up 10k to 3V3_L2 (R37) |  | [2] [1] |
| button S3 | ESP32-S3-PICO-1-N8R8 |  |  | S3 → GPIO12 (G12_KEY2) | G12_KEY2: up 10k to 3V3_L2 (R36) |  | [2] [1] |
| battery | connector J4 |  |  | + → VBAT_L0 (J4 pin 1)<br>- → GND (J4 pin 2) |  |  | [2] [1] |
| USB_C_16P_Horizontal | AW32901FCR |  |  | VBUS (A4/B9, B4/A9) → VUSBIN_L0 | CC1: down 5.1k (R3)<br>CC2: down 5.1k (R4) | 5.1k on each CC line: the board presents itself as a sink. | [2] [1] |
| USB_C_16P_Horizontal | ESD5311 |  |  | DP1/DP2 (USB_P) → D2 ESD5311<br>DM1/DM2 (USB_N) → D1 ESD5311 |  |  | [2] [1] |
| HY2.0-4P | ESP32-S3-PICO-1-N8R8 |  |  | 3 → GPIO9 (GROVE_G9)<br>4 → GPIO10 (GROVE_G10) |  |  | [2] [1] |
| connector CN2 (IR/speaker board) | connector J2 (main board), CN1 AXE524124 (IR/speaker board) |  |  |  |  | Every pin reaches the main board through CN1/J2. | [2] [1] |

## Not on this board

| Role | Notes | Src |
| --- | --- | --- |
| rtc | No RTC chip on the schematic; no 32 kHz crystal either (GPIO15/GPIO16 carry I2S). | [2] |
| crystal | No discrete crystal: XTAL_P/XTAL_N are unconnected and the SiP integrates a 40 MHz crystal. | [2] [3] |
| fuel gauge | The battery is read as a voltage by the PMIC's ADC through a switched divider; no gauge IC. | [2] [4] |
| touch controller |  | [2] |
| keyboard controller |  | [2] |
| io expander |  | [2] |
| usb uart bridge | USB goes straight to the ESP32-S3's native USB pins. | [2] |
| sd slot |  | [2] |
| gps |  | [2] |
| lora |  | [2] |
| magnetometer |  | [2] |
| buzzer | Sound comes from the speaker through the codec and amplifier. | [2] |

## Notes

Power rails, by the schematic's names: VUSBIN_L0 (USB VBUS) -> U7 OVP -> 5VIN_L0 -> U6 -> Internal_5V (also from HAT2_5VIN through U11, and from GROVE_5V through U12 and D10); Internal_5V feeds the charger and, through U13, VBUS_L0; the battery VBAT_L0 also feeds VBUS_L0 through U14. From VBUS_L0: 3V3_L0 (U3, always on: PMIC), 3V3_L1 (U4: IMU), 3V3_L2 (U2 buck: ESP32-S3), 3V3_L3B_AU (U1: codec, microphone), the AW8737A and the boost U9 (BOOST_OUT -> U8 -> GROVE_5V); 3V3_L3B (LCD) is switched from 3V3_L2 by U5. The main I2C bus (GPIO47 SDA, GPIO48 SCL) carries the M5PM1 (0x6E), the BMI270 (0x68) and, through the isolation MOSFETs, the ES8311 (0x18); it also reaches the LCD connector. The IR emitter and receiver, the speaker and the Hat2 header are on a second board joined to the main board by a 24-pin board-to-board connector.

## Sources

1. [StickS3 (K150), M5Stack documentation](https://docs.m5stack.switch-science.com/en/core/StickS3) — vendor docs, checked 2026-11-16 (`m5-docs`); read at a mirror of <https://docs.m5stack.com/en/core/StickS3>. Read at Switch Science's mirror of docs.m5stack.com: the original host refused or timed out from the machine that wrote this file on 2026-11-16.
2. [K150 StickS3 schematic, project V0.6, dated 2025-11-11 (4 pages: functions and power network, power, core, IR/speaker board)](https://web.archive.org/web/20260308045411/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1207/K150_Stick_S3_PRJ_V0.6_20251111_2025_11_17_16_10_24.pdf) — schematic, checked 2026-11-16 (`k150-schematic`); read at a mirror of <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1207/K150_Stick_S3_PRJ_V0.6_20251111_2025_11_17_16_10_24.pdf>; found through [1]. The address the docs page links timed out from the machine that wrote this file; the file was read from the Internet Archive's capture of 2026-03-08 of that address.
3. [ESP32-S3-PICO-1 Series Datasheet v1.2 (Espressif)](https://documentation.espressif.com/esp32-s3-pico-1_datasheet_en.pdf) — datasheet, checked 2026-11-16 (`esp32-s3-pico-1-datasheet`).
4. [M5PM1 Chip User Manual V1.9, 2026-01-22 (M5Stack)](https://github.com/m5stack/M5PM1/blob/main/docs/M5PM1_Datasheet_EN.pdf) — datasheet, checked 2026-11-16 (`m5pm1-manual`).
5. [Awinic AW329XX (AW32901) over-voltage protection switch datasheet V1.1, September 2018](https://datasheet.lcsc.com/datasheet/pdf/a6e12bc064a50d5a017e9740df82b571.pdf) — datasheet, checked 2026-11-17 (`aw32901-datasheet`). LCSC's copy (part C401023); SHA-256 of the file read e44d055edf7a46f6a3fe935f898637785299c64036838fe64fd448f3c4c17e48.
6. [JCET CJ3439KDW dual MOSFET datasheet, revision D, March 2016](https://datasheet.lcsc.com/datasheet/pdf/1300ae41d9efc3741e3098a9a42c762d.pdf) — datasheet, checked 2026-11-17 (`cj3439kdw-datasheet`). LCSC's copy (part C99824); SHA-256 of the file read 41cb3b3374616678b096dfab449a544e165c1878e2b6d7b2f0fbf1c70effcb66.
7. [Awinic AW8737A audio amplifier datasheet V1.2, July 2022](https://www.ickey.cn/static-pf/datasheet/32/b8/e731/32b8e731bcfd31639095bdc5f4bfa1d4.pdf) — datasheet, checked 2026-11-17 (`aw8737a-datasheet`). A distributor's copy; Awinic lists the datasheet at https://www.awinic.com/en/productDetail/AW8737AFCR.
8. [Vishay VSOP383.. IR receiver modules datasheet, document 82748, revision 1.6, 2026-02-09](https://www.vishay.com/docs/82748/vsop383.pdf) — datasheet, checked 2026-11-17 (`vsop383-datasheet`).
9. PYG0 against the charge state on an open StickS3 (probe B3, 2026-11-17) — measured, checked 2026-11-17 (`bench-charge-status`). Kleidos sticks3_debug console over USB, case closed: the cell run down to about 4.0 V with VBUS cut at the hub, then USB in and the M5PM1's GPIO_INPUT register read against its own ADC's cell and VIN readings; recorded in schematic/bench/2026-11-17-charge-status-pyg0.md.
10. GPIO42 idle level with GROVE_5V up on an open StickS3 (probe B4, 2026-11-17) — measured, checked 2026-11-17 (`bench-ir-rx`). Kleidos sticks3_debug console over USB, case closed: EXT_5V_EN on, GROVE_5V read by the M5PM1's ADC, GPIO42 read as an input 150 times with no remote; recorded in schematic/bench/2026-11-17-ir-rx-gpio42.md.
11. Owner observed on his unit, 2026-11-17 — measured, checked 2026-11-17 (`owner-unit`). Seen by the owner on his own StickS3 and reported on 2026-11-17: the status LED's color and where it sits. By eye, no instrument.
12. Verified against the owner's physical unit, 2026-11-18 — measured, checked 2026-11-18 (`owner-unit-verified`). The owner compared his own StickS3 with this repository's front drawing (svg/front.svg) and 3D model (model/) on 2026-11-18: the model and the drawing match the real board. A check by eye, no instrument. The original source of the measurement was not recorded (sources.md).

## In this folder

- [`board.json`](board.json): every part on the board, each value with its source ([`_shared/board.schema.json`](../_shared/board.schema.json)); this page is written from it.
- [`measurements.json`](measurements.json): the case, display, button and keyboard geometry the front is drawn against ([`_shared/schema.md`](../_shared/schema.md)).
- [`sources.md`](sources.md): the vendor drawings, photos and CAD files the measurements were taken on.
- [`icon.svg`](icon.svg): a 64 px pictogram of the board.
- [`svg/front.svg`](svg/front.svg): the front at 1 unit = 1 mm: the screen's active area, a press target for every control and each printed legend as a group of its own.
- [`svg/back.svg`](svg/back.svg): the back, seen from behind, with what it prints.
- [`svg/left.svg`](svg/left.svg): the left face and what it prints.
- [`model/sticks3.glb`](model/sticks3.glb): the 3D model, glTF 2.0 at 1 unit = 1 mm, every print kept.
- [`model/sticks3-web.glb`](model/sticks3-web.glb): its web level of detail.
- [`model/spec.json`](model/spec.json): the recipe both are built from.
- [`model/source.json`](model/source.json): the master's provenance.
- [`model/web.json`](model/web.json): the web level's record.
- [`schematic/sticks3.pdf`](schematic/sticks3.pdf): the connectivity schematic, made to be followed by clicking.
- [`schematic/README.md`](schematic/README.md): the schematic's sources, its Kleidos additions and corrections, and its open questions.
- [`schematic/netlist.yaml`](schematic/netlist.yaml): every part, pin and net of the schematic with its source.
- [`schematic/improvements.md`](schematic/improvements.md): the triage behind the additions and corrections.
- [`schematic/bench/`](schematic/bench/): the bench probe records.

How the drawings, models and schematics are made, and which script writes each file: [`docs/models-and-drawings.md`](../docs/models-and-drawings.md).
