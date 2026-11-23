<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

<img src="icon.svg" width="96" height="96" alt="StickC-Plus icon"> <a href="svg/front.svg"><img src="svg/front.svg" width="226" height="320" alt="StickC-Plus front drawing, true to scale: the case, the screen, the controls and the printed legends"></a>

# StickC-Plus

M5Stack · SKU **K016-P** · revision v1.1 · also sold as M5StickC PLUS, M5StickC Plus [1] [2]

Every value below comes from [`board.json`](board.json), where each one carries the id of its source; the numbers in brackets point to the sources listed at the end of this page. This page is written from that file by [`_shared/emit_board_readme.py`](../_shared/emit_board_readme.py): change the file, then run the script.

Vendor links: [docs](https://docs.m5stack.com/en/core/StickC-Plus)

## Dimensions

| Width | Height | Depth | Weight |
| --- | --- | --- | --- |
| 24.0 mm | 48.0 mm | 13.5 mm | 16.9 g |

The vendor's current page gives 48.0 x 24.0 x 13.5 mm and 16.9 g, a plastic (PC) shell and 0 to 60 °C operation. The 2021 printout of the same page (before v1.1) gave 48.2 x 25.5 x 13.7 mm, 15 g net and 21 g gross. [1] [2] [18]

## Components

24 entries (36 parts counting quantities).

### Processing and memory

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| ESP32-PICO-D4 (Espressif) | soc | — | 1 | type: System-in-Package based on the ESP32 SoC; cpu: Xtensa dual-core 32-bit LX6, up to 240 MHz; dmips: 600; rom kb: 448; sram kb: 520; rtc sram kb: 16; in package flash: 4 MB, Quad SPI; in package psram: none; in package crystal: a crystal oscillator, with the filter capacitors and the RF matching circuit, inside the package; wifi: 802.11 b/g/n, 1T1R up to 150 Mbps, 2412 to 2484 MHz; bluetooth: v4.2 BR/EDR and Bluetooth LE; chip revision: v1.0 or v1.1 (Espressif PCN20220901 moved the ESP32-PICO-D4 from v1.0 to v1.1; the revision of a given board is not stated); package mm: 7.0 x 7.0 x 0.94; supply v: 3.0 to 3.6; operating temp c: -40 to 85; status: Not Recommended for New Designs (NRND) — The schematic leaves the part unannotated (U?) and marks IO4, IO6, IO7, IO8, IO11, IO12, IO14, IO16, IO17 and IO19 as not connected. The vendor's flash note lists the supported download rates as 1200 to 115200, 250K, 500K, 750K and 1500K baud. | [4] [1] [3] |
| — | flash | — | 1 | capacity mb: 4; interface: Quad SPI; location: inside the ESP32-PICO-D4 package | [1] [4] |
| — | crystal | Y1 | 1 | frequency: 32.768 kHz; load capacitance pf: 6; load capacitors: C12 and C9, 6 pF each — The ESP32's main crystal is inside the ESP32-PICO-D4 package. | [3] |

### Power

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| AXP192 (X-Powers) | pmic | U2 | 1 | interface: TWSI (I2C); i2c address: 0x34 (7-bit; the datasheet gives 68H to write and 69H to read); operating voltage v: 2.9 to 6.3; charger: integrated, up to 1.4 A with internal MOSFET, target 4.1 / 4.15 / 4.2 / 4.36 V; fuel gauge: integrated coulomb counter and 12-bit ADC (16 channels); backup battery: BACKUP pin powers the RTC block from a backup cell and charges it; dcdc1: 0.7 to 3.5 V, 25 mV steps, 1.2 A, 3.3 V typical default (defaults are set per order); on this board VESP_3V3 through L2 2.2 µH, C5 10 µF and CX1 100 µF / 4 V, its DC1OUT_VOL register reading 0x68 (3.30 V), which the Kleidos firmware never writes (bench, 2026-11-17); dcdc2: unused (LX2 and DCDC2 not connected); dcdc3: unused (LX3 and DCDC3 not connected); ldo1: 30 mA, always on; on this board RTC_VDD; ldo2: 1.8 to 3.3 V, 200 mA; on this board LCD_BL_VCC (display backlight); ldo3: 1.8 to 3.3 V, 200 mA; on this board LCD_LOGIC_VCC (display logic); ldoio0: GPIO0 as an LDO, 1.8 to 3.3 V, 50 mA; on this board MIC_VCC; ipsout: the system rail, fed to the SGM6603 boost, the RTC interrupt pull-up and APS; off mode current ua: 27 typical at BAT = 3.8 V; pwron: internal 100 kΩ pull-up to APS; unused pins: GPIO1, GPIO2, GPIO3, GPIO4, CHGLED, N_RSTO, PWREN and NC are not connected; TS is tied to GND — Vendor rail table: LDOio0 microphone, LDO1 RTC, LDO2 TFT backlight, LDO3 TFT IC, DC-DC1 ESP32/3.3 V and MPU6886, IPSOUT 5 V Grove. The schematic draws the 5 V Grove through the SGM6603 boost (EXTEN), which IPSOUT feeds. N_OE (pin 4) is tied to GND (outputs on), BIAS has R5 200 kΩ to GND, VREF and VINT carry C16 and C10 (1 µF), and APS carries C13 (220 nF) on IPSOUT. IPSOUT is decoupled by C24, C30 (100 nF), C23 (10 µF) and CX2 (10 µF / 6.3 V). Current power key behavior (vendor): a single click powers on or resets, a double click powers off. | [3] [1] [5] [6] [15] |
| SGM6603-5.0 (SG Micro) | regulator | U8 | 1 | type: synchronous boost converter, 1.1 A switch; input v: 0.9 to 5.5; output v: 5.0 fixed; quiescent current ua: 30; shutdown current ua max: 1; shutdown: load disconnected: the output goes to 0 V without drawing from the input; package: SOT-23-6; operating temp c: -40 to 85; inductor: L4 4.7 µH; output capacitors: C36 100 nF, C45 10 µF, C46 10 µF — IN (pin 6) is IPSOUT; EN (pin 3) is the AXP192's EXTEN. | [3] [11] |
| — | battery | Li_Ion | 1 | capacity mah: 120; nominal v: 3.7; chemistry: lithium (vendor wording); connection: two-pin connector Li_Ion: pin 1 VBAT_Li_Ion, pin 2 GND — The 2021 description: battery capacity raised from 95 mAh (M5StickC) to 120 mAh. | [1] [2] [3] |
| — | battery | BAT1 | 1 | schematic value: DMS_3R3; connection: pin 1 VBAT_RTC, pin 2 GND — The schematic gives only the value DMS_3R3 for BAT1; it does not name the cell's type or maker. | [3] |

### Display and touch

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| — | display panel | U5 | 1 | technology: TFT LCD, IPS (the schematic names the block IPS_LCD); diagonal in: 1.14; resolution px: 135 / 240; connector pins: LEDA, GND, RESET, RS, MOSI, SCK, VDD, CS and a ground pad — The vendor page states the panel as 1.14 inch, 135 x 240 colorful TFT LCD, 18.7 % more display area than the 0.96-inch screen of the M5StickC. | [1] [3] |
| ST7789v2 (Sitronix) | display controller | — | 1 | frame memory: 240 x 320 x 18 bit (the ST7789V datasheet the vendor links); max resolution: 240 RGB x 320; colors: up to 262K; location: in the display module — The vendor names the controller ST7789v2 and links the ST7789V datasheet (Sitronix, version 1.0, 2013-10). | [1] [10] |

### Sensors and timekeeping

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| BM8563 | rtc | U4 | 1 | interface: I2C, up to 400 kbit/s; i2c address: 0x51 (7-bit; the datasheet gives A2h to write and A3h to read); supply v: 1.5 to 5.5; sleep current ua: 0.25 typical at VDD = 3.0 V, 25 °C; interrupt output: open drain; clock output: programmable 32.768 kHz, 1024 Hz, 32 Hz, 1 Hz (open drain); unconnected on this board; oscillator load capacitance pf: 6; operating temp c: -40 to 85 — VDD (pin 8) is RTC_VDD from the AXP192's LDO1, decoupled by C11 (1 µF). CLKOUT (pin 7) is not connected. | [3] [1] [7] |
| MPU-6886 (TDK InvenSense) | imu | U7 | 1 | axes: 3-axis gyroscope and 3-axis accelerometer; gyro full scale dps: ±250, ±500, ±1000, ±2000; accel full scale g: ±2, ±4, ±8, ±16; adc bits: 16; fifo: 1 kB; i2c address: 0x68 with AD0 low (0x69 with AD0 high); vdd v: 1.71 to 3.45; vddio v: 1.71 to 3.45; interrupt output: INT1, configurable push-pull or open drain, active high or low; package: LGA-24, 3 x 3 x 0.75 mm | [3] [1] [8] |

### Audio

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| SPM1423HM4H-B (Knowles) | microphone | U3 | 1 | type: digital MEMS microphone (Knowles SiSonic); operating temp c: -40 to 100 — GPIO0 is also the ESP32's boot strap: R12 (1 kΩ) pulls it up to VESP_3V3, MOS1 drives it from the USB bridge, and it leaves on PAD5 through R106 (22 Ω). | [3] [1] [9] |
| — | buzzer | — | 1 | type: passive buzzer — The schematic does not draw the buzzer: it shows GPIO2 only on PAD2. Bench, 2026-11-17: GPIO2 held high draws no DC current the AXP192's VBUS reading resolves (62.0 vs 58.0 mA, about 5 mA standard error over 80 readings each way), which rules out a buzzer switched through a transistor and fits a piezo; whether it sounds was not checked. | [1] [2] [17] |

### Input and indicators

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| — | led | LED2 | 1 | color: red; drive: anode on VESP_3V3, cathode on GPIO10 (on when GPIO10 is low) | [3] [1] |
| — | ir led | LED1 | 1 | function: infrared transmitter; drive: anode on VESP_3V3, cathode on GPIO9 (on when GPIO9 is low) | [3] [1] |
| — | button | S3 | 1 | schematic value: PTS_820; function: Button A (the front key); logic: closes to GND | [3] [1] |
| — | button | S1, S2 | 2 | schematic value: TS_015; functions: S1 power key, S2 Button B; logic: both close to GND — Power key (vendor, current page): single click powers on or resets, double click powers off. The 2021 page read: hold 2 s to power on, 6 s to power off. | [3] [1] [2] |

### Radio and positioning

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| — | antenna | E1 | 1 | type: 2.4G 3D antenna; matching: pi network: C2 1.5 pF to GND, L1 1.8 nH (HQ) in series, C1 1.2 pF to GND | [1] [3] |

### Connectors, storage and USB

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| CH552T | usb uart bridge | U6 | 1 | supply: VBUS_USB on pins 1 and 19 (the bridge is powered only from USB), VCC (pin 19) decoupled by C27 (100 nF); V33 (pin 20), its internal regulator's output, decoupled by C25 (100 nF); usb identity: enumerates as an FTDI FT232: VID 0x0403, PID 0x6001, manufacturer string Hades2001, product string M5stack (bench, 2026-11-17) — The vendor's driver section directs users to the FTDI driver for this port: the CH552T's firmware presents an FT232's USB identity. The schematic prints pin 10 as P3.2, the name of pin 1; the CH552 datasheet names it P3.0 (RXD). | [3] [1] [12] [16] |
| — | connector | J2 | 1 | type: USB Type-C; input: 5 V at 500 mA; vbus range v: 4.8 to 5.5; cc: CC1 (A5) and CC2 (B5) each pulled down by 5.1 kΩ (R13, R19); data: DP1/DP2 (A6/B6) joined to USB_DP, DN1/DN2 (A7/B7) joined to USB_DM; vbus capacitor: C4 10 µF | [3] [1] |
| — | connector | J1 | 1 | type: HY2.0-4P (Grove); vendor function: GROVE (I2C + I/O + UART), labeled PORT.CUSTOM; pinout: 1 GND (black), 2 5 V (red), 3 G32 (yellow), 4 G33 (white); decoupling: C37 10 µF on the 5 V pin — The vendor's 2021 pin table calls GPIO32 SDA and GPIO33 SCL on this port. | [3] [1] [2] |
| — | connector | PAD1 to PAD10 | 1 | vendor external pins: G0, G25/G26, G36, G32, G33 (current page); G0, G25/G36, G26, G32, G33 (2021 page); pads: PAD1 3V3 (VESP_3V3), PAD2 GPIO2, PAD3 GPIO38, PAD4 GPIO36 (GPIO36_EXT), PAD5 GPIO0 (GPIO0_EXT), PAD6 VIN (VBUS_VIN), PAD7 5VOUT (EXT_VDD), PAD8 GND, PAD9 GPIO26 (GPIO26_EXT), PAD10 GPIO25 — The vendor: G36 and G25 share the same port; when one is used, set the other as a floating input. The schematic draws ten pads; which pads reach the HAT header's pins is not stated. | [3] [1] [2] |

### Protection

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| — | esd | D1, D2, D3, D4, D6, D7, D8, D13, D14, D15, D16 | 11 | schematic value: ESD/3.3V; placement: D1 GPIO32, D2 GPIO33, D3 USB_DP, D4 USB_DM, D6 GPIO9, D7 GPIO10, D8 GPIO39, D13 PWR_KEY, D14 GPIO26, D15 GPIO0, D16 GPIO36; each to GND | [3] |

### Other parts

| Part | Role | Ref. | Qty | Key facts | Src |
| --- | --- | --- | --- | --- | --- |
| CJ2302 | other | MOS1, MOS2 | 2 | type: N-channel MOSFET; function: auto-program switches between the USB bridge and the ESP32's EN and GPIO0 — Both gates are biased from VBUS_USB, so the switches conduct only while USB power is present. | [3] |

## Connections

Each row is one fact of wiring, read from the component in the first column; a row without sources of its own takes its component's.

| From | To | Bus | Address | Pins | Pulls | Notes | Src |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ESP32-PICO-D4 | antenna E1 | RF |  | LNA_IN (pin 2) → E1 through the matching network L1 1.8 nH, C2 1.5 pF, C1 1.2 pF |  |  | [3] |
| ESP32-PICO-D4 | AXP192 | power |  | VDDA, VDDA3P3, VDD3P3_CPU (pins 1, 3, 37, 43, 46) → VESP_3V3 (AXP192 DCDC1) |  | Decoupled by C38, C39, C41 and C42 (100 nF each) and C44 (10 µF). C40 (100 nF) sits on VDD3P3_RTC (pin 19) and C43 (100 nF) on the second VDDA3P3 (pin 4), each on a net of its own in the print. VDD_SDIO (pin 26) is left unconnected on the board; it is an output, the in-package flash's supply, taken from VDD3P3_RTC with MTDI (GPIO12, internal pull-down) low at reset unless an eFuse overrides the strap. | [3] [4] |
| AXP192 | ESP32-PICO-D4 | I2C (SYS_SDA / SYS_SCL) | 0x34 | SDA (pin 1) → GPIO21<br>SCK (pin 2) → GPIO22 | SYS_SDA: up 2.2k to VESP_3V3 (R4)<br>SYS_SCL: up 2.2k to VESP_3V3 (R3) |  | [3] [1] [5] [6] [15] |
| AXP192 | ESP32-PICO-D4 | interrupt (SYS_INT) |  | IRQ (pin 48) → GPIO35 | SYS_INT: up 2.2k to VESP_3V3 (R2) | The MPU6886's INT pin shares this net. IRQ is open drain, active low. Bench, 2026-11-17: with the AXP192's IRQs masked and cleared and the MPU6886's INT released, GPIO35 (no internal pull) reads high, so R2 is fitted; an AXP192 IRQ latch left set holds the net low until it is cleared. | [3] [6] [13] |
| AXP192 | ESP32-PICO-D4 | reset |  | PWROK (pin 5) → EN (ESP32_EN) | ESP32_EN: up 5.1k to VESP_3V3 (R8) | PWROK holds the ESP32 in reset until the AXP192's outputs are up. | [3] [6] |
| AXP192 | ESP32-PICO-D4 | GPIO |  | N_VBUSEN (pin 6) → GPIO27 | GPIO27 / N_VBUSEN: down 10k to GND (R21) | N_VBUSEN low lets IPSOUT take power from VBUS; high stops it. The pull-down keeps VBUS selected until GPIO27 drives it. | [3] [1] [5] [6] [15] |
| AXP192 | connector J2 | power |  | VBUS (pin 31) → VBUS_USB |  |  | [3] [1] [5] [6] [15] |
| AXP192 | connector PAD1 to PAD10 | power |  | ACIN (pins 32, 33) → VBUS_VIN (PAD6, VIN) |  | The vendor limits VBUS_VIN and VBUS_USB to 4.8 to 5.5 V; on VBUS the AXP192 charges the internal battery. | [3] [1] [5] [6] [15] |
| AXP192 | battery Li_Ion | power |  | BAT (pins 34, 35) → VBAT_Li_Ion |  | C3 (10 µF) on the battery line; TS (pin 37) is tied to GND. | [3] [1] [5] [6] [15] |
| AXP192 | battery BAT1 | power |  | BACKUP (pin 30) → VBAT_RTC |  |  | [3] [1] [5] [6] [15] |
| AXP192 | SGM6603-5.0 | enable |  | EXTEN (pin 40) → EXT_BOOST_EN<br>IPSOUT (pins 38, 39) → SGM6603 IN (pin 6) | EXT_BOOST_EN: down 100k to GND (R18) |  | [3] [1] [5] [6] [15] |
| AXP192 | BM8563 | power |  | LDO1 (pin 28) → RTC_VDD<br>SYSEN (pin 29) → RTC_VDD |  |  | [3] [1] [5] [6] [15] |
| AXP192 | display panel U5 | power |  | LDO2 (pin 12) → LCD_BL_VCC (LEDA)<br>LDO3 (pin 11) → LCD_LOGIC_VCC (VDD) |  | C15 (1 µF) on LDO2, C20 (1 µF) on LDO3. | [3] [1] [5] [6] [15] |
| AXP192 | SPM1423HM4H-B | power |  | GPIO0 / LDOio0 (pin 19) → MIC_VCC |  | C8 (1 nF) at the PMIC, C7 (1 µF) at the microphone. | [3] [1] [5] [6] [15] |
| AXP192 | button S1, S2 | power key |  | PWRON (pin 23) → PWR_KEY (S1 to GND) |  |  | [3] [1] [5] [6] [15] |
| SGM6603-5.0 | connector J1 | power |  | OUT (pin 5) → EXT_VDD (Grove pin 2) |  |  | [3] [11] |
| SGM6603-5.0 | connector PAD1 to PAD10 | power |  | OUT (pin 5) → EXT_VDD (PAD7, 5VOUT) |  |  | [3] [11] |
| BM8563 | ESP32-PICO-D4 | I2C (SYS_SDA / SYS_SCL) | 0x51 | SDA (pin 5) → GPIO21<br>SCL (pin 6) → GPIO22 |  | Pull-ups R4 and R3 (2.2 kΩ) are shared with the AXP192 entry. | [3] [1] [7] |
| BM8563 | button S1, S2 | wake (RTC_INT) |  | INT (pin 3) → RTC_INT, then C401 (106 = 10 µF, 6.3 V) to PWR_KEY (AXP192 PWRON) | RTC_INT: up 10k to IPSOUT (R401) | The RTC interrupt is coupled to the power key net, not to an ESP32 GPIO. The vendor's change log for v1.1 (2021-12) reads "Added sleep and wake-up functions". Bench, 2026-11-17: GPIO35 stays high with INT asserted (INT does not reach it); each RTC countdown with the timer interrupt on makes the AXP192 latch a power-key short press, and on a build that powers the board off at the AXP192 an RTC countdown powered it back on after about 19.4 s and 28.7 s (a power-on reset, USB connected; on battery alone not run). | [3] [7] [14] |
| BM8563 | crystal Y1 | oscillator |  | OSCI (pin 1) → Y1<br>OSCO (pin 2) → Y1 |  |  | [3] [1] [7] |
| MPU-6886 | ESP32-PICO-D4 | I2C (SYS_SDA / SYS_SCL) | 0x68 | SCL (pin 23) → GPIO22<br>SDA (pin 24) → GPIO21<br>AD0 (pin 9) → GND<br>nCS (pin 22) → VESP_3V3 |  | Pull-ups R4 and R3 (2.2 kΩ) are shared with the AXP192 entry. | [3] [1] [8] |
| MPU-6886 | ESP32-PICO-D4 | interrupt (SYS_INT) |  | INT (pin 12) → GPIO35 |  | Shared with the AXP192's IRQ; R2 (2.2 kΩ) pulls the net up to VESP_3V3. INT is push-pull, active high at reset; to share the net it must be set open drain, active low (INT_PIN_CFG, register 55, bits 7 and 6). Bench, 2026-11-17: so set, its data-ready interrupt pulls GPIO35 low. | [3] [8] [13] |
| MPU-6886 | AXP192 | power |  | VDD (pin 13) → VESP_3V3 (DCDC1)<br>VDDIO (pin 8) → VESP_3V3 (DCDC1) |  | C28 (100 nF) on VDD, C21 (1 µF) on VDDIO, C29 (100 nF) beside nCS. | [3] [1] [8] |
| SPM1423HM4H-B | ESP32-PICO-D4 | digital microphone (schematic block I2S_MIC) |  | CLK (pin 4) → GPIO0<br>DATA (pin 5) → GPIO34<br>SELECT (pin 2) → GND |  |  | [3] [1] [9] |
| SPM1423HM4H-B | AXP192 | power |  | VCC (pin 6) → MIC_VCC (AXP192 LDOio0) |  |  | [3] [1] [9] |
| display panel U5 | ESP32-PICO-D4 | SPI, write only (SCK, MOSI, D/C, CS); no read line |  | SCK (pin 6) → GPIO13<br>MOSI (pin 5) → GPIO15<br>RS (D/C, pin 4) → GPIO23<br>CS (pin 8) → GPIO5<br>RESET (pin 3) → GPIO18 | LCD_RST: up 5.1k to VESP_3V3 (R14) |  | [1] [3] |
| display panel U5 | AXP192 | power |  | LEDA (pin 1) → LCD_BL_VCC (LDO2)<br>VDD (pin 7) → LCD_LOGIC_VCC (LDO3) |  | C15 and C18 (1 µF each) on LCD_BL_VCC (LEDA); C20 (1 µF) on LCD_LOGIC_VCC (VDD). | [1] [3] |
| CH552T | connector J2 | USB 2.0 |  | pin 14 (P3.6) → USB_DP<br>pin 15 (P3.7) → USB_DM |  |  | [3] [1] [12] [16] |
| CH552T | ESP32-PICO-D4 | UART0 |  | CH552_TXD (pin 9, P3.1) → U0RXD (pin 40) through R24 100 Ω<br>CH552_RXD (pin 10, P3.0; printed P3.2) → U0TXD (pin 41) through R25 100 Ω |  |  | [3] [1] [12] [16] |
| CH552T | CJ2302 | auto-program |  | CH552_EN_CTRL (pin 7, P1.0) → MOS2 source<br>CH552_GP0_CTRL (pin 5, P1.7) → MOS1 source |  |  | [3] [1] [12] [16] |
| CJ2302 | ESP32-PICO-D4 | reset |  | MOS2 drain → EN (ESP32_EN) through R109 2.2 kΩ<br>MOS2 gate → VBUS_USB divider R101 1 kΩ / R102 1 kΩ to GND |  |  | [3] |
| CJ2302 | ESP32-PICO-D4 | boot strap |  | MOS1 drain → GPIO0 through R108 22 Ω<br>MOS1 gate → VBUS_USB divider R103 1 kΩ / R104 1 kΩ to GND |  |  | [3] |
| connector J2 | CH552T | USB 2.0 |  | DP → USB_DP<br>DM → USB_DM |  | ESD diodes D3 and D4 on the data lines. | [3] [1] |
| connector J2 | AXP192 | power |  | VBUS → VBUS_USB (AXP192 VBUS, pin 31) |  |  | [3] [1] |
| connector J2 | external | USB |  | receptacle → host or charger |  |  | [3] [1] |
| connector J1 | ESP32-PICO-D4 | GPIO |  | pin 3 → GPIO32<br>pin 4 → GPIO33 |  | ESD diodes D1 (GPIO32) and D2 (GPIO33). | [3] [1] [2] |
| connector J1 | SGM6603-5.0 | power |  | pin 2 → EXT_VDD (SGM6603 OUT) |  |  | [3] [1] [2] |
| connector J1 | external | Grove |  | cable → a Unit |  |  | [3] [1] [2] |
| connector PAD1 to PAD10 | ESP32-PICO-D4 | GPIO |  | PAD2 → GPIO2<br>PAD3 → GPIO38<br>PAD4 → GPIO36 through R107 22 Ω<br>PAD5 → GPIO0 through R106 22 Ω<br>PAD9 → GPIO26 through R105 22 Ω<br>PAD10 → GPIO25 |  | ESD diodes D16 (GPIO36), D15 (GPIO0) and D14 (GPIO26) sit on the ESP32 side of the series resistors. | [3] [1] [2] |
| connector PAD1 to PAD10 | external | HAT |  | pads → HAT and Unit accessories |  |  | [3] [1] [2] |
| battery Li_Ion | AXP192 | power |  | + → VBAT_Li_Ion (AXP192 BAT, pins 34 and 35) |  |  | [1] [2] [3] |
| battery BAT1 | AXP192 | power |  | pin 1 → VBAT_RTC (AXP192 BACKUP, pin 30) |  |  | [3] |
| buzzer | ESP32-PICO-D4 | GPIO |  | buzzer → GPIO2 |  |  | [1] [2] |
| led LED2 | ESP32-PICO-D4 | GPIO |  | cathode → GPIO10 |  | ESD diode D7 on GPIO10. The schematic draws no series resistor. | [3] [1] |
| ir led LED1 | ESP32-PICO-D4 | GPIO |  | cathode → GPIO9 |  | ESD diode D6 on GPIO9. The schematic draws no series resistor. | [3] [1] |
| button S3 | ESP32-PICO-D4 | GPIO |  | S3 → GPIO37 | GPIO37: up 10k to VESP_3V3 (R20) | No ESD diode on GPIO37 in the schematic. | [3] [1] |
| button S1, S2 | AXP192 | power key |  | S1 → PWR_KEY (AXP192 PWRON, pin 23) |  | PWRON has the AXP192's internal 100 kΩ pull-up to APS; ESD diode D13 on PWR_KEY. | [3] [6] |
| button S1, S2 | ESP32-PICO-D4 | GPIO |  | S2 → GPIO39 | GPIO39: up 5.1k to VESP_3V3 (R11) | ESD diode D8 on GPIO39. | [3] [1] [2] |

## Not on this board

| Role | Notes | Src |
| --- | --- | --- |
| psram | The ESP32-PICO-D4 has no in-package PSRAM, and the schematic shows none on the board. | [4] [3] |
| touch controller | The specifications list no touch panel and the schematic shows no touch controller. | [1] [3] |
| sd slot | Not in the specifications or the schematic. | [1] [3] |
| gps | Not in the specifications or the schematic. | [1] [3] |
| lora | Not in the specifications or the schematic. | [1] [3] |
| keyboard controller | Two custom buttons and a power key; no keyboard. | [1] [3] |
| magnetometer | The IMU is 6-axis (gyroscope and accelerometer). | [1] [8] |
| audio codec | The microphone reaches the ESP32 directly; the schematic shows no codec. | [3] |
| io expander | The schematic shows no I/O expander. | [3] |

## Notes

Wiring and passive values come from the vendor's K016-P schematic (one Altium page, exported 2025-11-04), read at the Wayback Machine because the vendor's file host did not answer on 2026-11-16. Rail names follow the schematic: VESP_3V3 (AXP192 DCDC1), IPSOUT (the AXP192 system rail), RTC_VDD (LDO1), LCD_BL_VCC (LDO2), LCD_LOGIC_VCC (LDO3), MIC_VCC (LDOio0), EXT_VDD (the SGM6603 5 V output), VBUS_USB and VBUS_VIN. The schematic draws the VDDA3P3 (pin 4) and VDD3P3_RTC (pin 19) supply lines of the ESP32-PICO-D4 with crossing hops onto the 3.3 V bus, and its net list keeps those two pins apart from VESP_3V3; this file does not record them as connected. Pin 19 is certainly supplied (the board boots from its in-package flash, fed through VDD_SDIO from VDD3P3_RTC); which rail feeds it has not been measured.

## Sources

1. [StickC-Plus (K016-P), M5Stack documentation](https://docs.m5stack.switch-science.com/en/core/StickC-Plus) — vendor docs, checked 2026-11-16 (`m5-docs`); read at a mirror of <https://docs.m5stack.com/en/core/StickC-Plus>. Read at Switch Science's mirror of docs.m5stack.com: the original host timed out from the machine that wrote this file on 2026-11-16. The mirror redirects /en/core/m5stickc_plus to this page. Gives the specifications table, the pin map, the AXP192 rail table, the external pins, the input range note and the change log (2021.12: version changed to v1.1).
2. [M5StickC PLUS (SKU K016-P), M5Stack documentation page printed to PDF on 2021-08-25, hosted by Digi-Key](https://media.digikey.com/pdf/Data%20Sheets/M5Stack%20PDFs/K016-P.pdf) — vendor docs, checked 2026-11-16 (`digikey-k016p`). A print of the vendor's page from before v1.1 (December 2021). Cited for values the current page also states and for the 2021 values it changed.
3. [StickC-Plus (K016-P) schematic, one page, Altium export of 2025-11-04](https://web.archive.org/web/20260421142825/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/669/k016-p-StickC-Plus-sche.pdf) — schematic, checked 2026-11-16 (`k016p-schematic`); read at a mirror of <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/669/k016-p-StickC-Plus-sche.pdf>; found through [1]. Read at the Wayback Machine capture of 2026-04-21: the vendor's file host did not answer on 2026-11-16. SHA-256 of the file read: da0717dc357e0480f0eb4e174f2a93db6a3d00b2e0b70deed5f295a9757943cb. Net memberships were read from the PDF's embedded net list and the drawing.
4. [ESP32-PICO Series Datasheet v1.1 (Espressif), as M5Stack hosts it](https://web.archive.org/web/20261002190414/https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/669/esp32-pico_series_datasheet_en.pdf) — datasheet, checked 2026-11-16 (`esp32-pico-datasheet`); read at a mirror of <https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/669/esp32-pico_series_datasheet_en.pdf>; found through [1]. Read at the Wayback Machine capture of 2026-10-02.
5. [AXP192 datasheet, revision 1.0, four-page summary (X-Powers), as M5Stack hosts it](https://web.archive.org/web/20261031011628/https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/AXP192_datasheet_en.pdf) — datasheet, checked 2026-11-16 (`axp192-datasheet`); read at a mirror of <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/AXP192_datasheet_en.pdf>; found through [1]. Read at the Wayback Machine capture of 2026-10-31.
6. [AXP192 datasheet, revision 1.1, English draft (X-Powers), in M5Stack's M5-Schematic repository](https://github.com/m5stack/M5-Schematic/blob/master/Core/AXP192%20Datasheet_v1.1_en_draft_2211.pdf) — datasheet, checked 2026-11-16 (`axp192-datasheet-full`). The pin table, the TWSI address, the OFF mode current and the PWRON pull-up come from this edition.
7. [BM8563 real-time clock datasheet V1.1 (Chinese), as M5Stack hosts it](https://web.archive.org/web/20261031011628/https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/BM8563_V1.1_cn.pdf) — datasheet, checked 2026-11-16 (`bm8563-datasheet`); read at a mirror of <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/BM8563_V1.1_cn.pdf>; found through [1]. Read at the Wayback Machine capture of 2026-10-31. The datasheet does not name its maker in text.
8. [MPU-6886 datasheet, document DS-000193 v1.1 (TDK InvenSense), as M5Stack hosts it](https://web.archive.org/web/20261031011628/https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/MPU-6886-000193%2Bv1.1_GHIC_en.pdf) — datasheet, checked 2026-11-16 (`mpu6886-datasheet`); read at a mirror of <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/MPU-6886-000193%2Bv1.1_GHIC_en.pdf>; found through [1]. Read at the Wayback Machine capture of 2026-10-31.
9. [SPM1423HM4H-B Digital "Mini" High SNR SiSonic Microphone specification, revision A (Knowles), as M5Stack hosts it](https://web.archive.org/web/20260917142323/https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/SPM1423HM4H-B_datasheet_en.pdf) — datasheet, checked 2026-11-16 (`spm1423-datasheet`); read at a mirror of <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/SPM1423HM4H-B_datasheet_en.pdf>; found through [1]. Read at the Wayback Machine capture of 2026-09-17. Its acoustic and electrical table is an image and is not transcribed here.
10. [ST7789V datasheet, version 1.0, 2013-10 (Sitronix), as M5Stack hosts it](https://web.archive.org/web/20261022024740/https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/ST7789V.pdf) — datasheet, checked 2026-11-16 (`st7789v-datasheet`); read at a mirror of <https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/datasheet/core/ST7789V.pdf>; found through [1]. Read at the Wayback Machine capture of 2026-10-22.
11. [SGM6603 90% efficient synchronous boost converter with 1.1 A switch, product page and datasheet (SG Micro)](https://www.sg-micro.com/product/SGM6603) — datasheet, checked 2026-11-16 (`sgm6603-datasheet`). The datasheet was read through the product page's download link, which carries a session token.
12. [CH552/CH551 datasheet V1G (WCH)](https://web.archive.org/web/20240404213535/https://wch-ic.com/downloads/file/309.html) — datasheet, checked 2026-11-17 (`ch552-datasheet`); read at a mirror of <https://wch-ic.com/downloads/file/309.html>. Read at the Wayback Machine capture of 2024-04-04, SHA-256 fcccd350a578416d189bdbee175609dae03210261a5c4491b9b17b71d0a7a5d2. Section 4, pin definitions: TSSOP20 pin 10 is P3.0 (RXD), pin 1 P3.2/VBUS1.
13. SYS_INT pull-up and drivers on the owner's StickC-Plus 1.1 (Kleidos boards bench record m5stickc-plus1/schematic/bench/2026-11-17-sys-int-pull-up-and-drivers.md) — measured, checked 2026-11-17 (`bench-sys-int`). Over the board's USB-C port, case closed: stock console commands of the Kleidos m5stickc_plus1_debug image (I2CWR!, REGR, GPIO?) on two images; AXP192 IRQs masked and cleared, the MPU6886's INT set open drain, GPIO35 read, then each driver enabled alone.
14. RTC interrupt to the power key on the owner's StickC-Plus 1.1 (Kleidos boards bench record m5stickc-plus1/schematic/bench/2026-11-17-rtc-int-to-power-key.md) — measured, checked 2026-11-17 (`bench-rtc-int`). Over the board's USB-C port, case closed, USB connected: BM8563 countdowns armed over I2C with GPIO35 and the AXP192's power-key latch read; then PMICOFFTEST 20, 30 and 35 on a bench-only build with rtcIntPowersOn = true (never committed).
15. DC-DC1 setpoint on the owner's StickC-Plus 1.1 (Kleidos boards bench record m5stickc-plus1/schematic/bench/2026-11-17-dcdc1-setpoint.md) — measured, checked 2026-11-17 (`bench-dcdc1`). Over the board's USB-C port, case closed: REGR axp192 0x26 on the Kleidos m5stickc_plus1_debug image; no voltmeter reading.
16. USB-serial bridge identity of the owner's StickC-Plus 1.1 (Kleidos boards bench record m5stickc-plus1/schematic/bench/2026-11-17-usb-bridge-identity.md) — measured, checked 2026-11-17 (`bench-usb-identity`). Read only, from the host's USB registry (macOS ioreg -p IOUSB), with the board connected and no serial port opened.
17. GPIO2 load on the owner's StickC-Plus 1.1 (Kleidos boards bench record m5stickc-plus1/schematic/bench/2026-11-17-buzzer-gpio2-load.md) — measured, checked 2026-11-17 (`bench-buzzer`). Over the board's USB-C port, case closed: GPIO2 held high and low on a bench-only build, 80 readings each way of the AXP192's VBUS current; nobody listened.
18. Verified against the owner's physical unit, 2026-11-18 — measured, checked 2026-11-18 (`owner-unit-verified`). The owner compared his own StickC-Plus with this repository's front drawing (svg/front.svg) and 3D model (model/) on 2026-11-18: the model and the drawing match the real board. A check by eye, no instrument. The original source of the measurement was not recorded (sources.md).

## In this folder

- [`board.json`](board.json): every part on the board, each value with its source ([`_shared/board.schema.json`](../_shared/board.schema.json)); this page is written from it.
- [`measurements.json`](measurements.json): the case, display, button and keyboard geometry the front is drawn against ([`_shared/schema.md`](../_shared/schema.md)).
- [`sources.md`](sources.md): the vendor drawings, photos and CAD files the measurements were taken on.
- [`icon.svg`](icon.svg): a 64 px pictogram of the board.
- [`svg/front.svg`](svg/front.svg): the front at 1 unit = 1 mm: the screen's active area, a press target for every control and each printed legend as a group of its own.
- [`svg/back.svg`](svg/back.svg): the back, seen from behind, with what it prints.
- [`model/m5stickc-plus1.glb`](model/m5stickc-plus1.glb): the 3D model, glTF 2.0 binary in meters (glTF's unit), every print kept: the format for the web and most viewers.
- [`model/m5stickc-plus1-web.glb`](model/m5stickc-plus1-web.glb): its web level of detail.
- [`model/m5stickc-plus1.obj`](model/m5stickc-plus1.obj): the same model as Wavefront OBJ, in millimeters, Y up, one object per part: the format for most other 3D tools (Blender, FreeCAD, Fusion, MeshLab, slicers); written from the master by [`_shared/export_obj.py`](../_shared/export_obj.py).
- [`model/m5stickc-plus1.mtl`](model/m5stickc-plus1.mtl): the OBJ's materials: each part's color, transparency, roughness and metalness.
- [`model/spec.json`](model/spec.json): the recipe the master and its web level are built from.
- [`model/source.json`](model/source.json): the master's provenance.
- [`model/web.json`](model/web.json): the web level's record.
- [`schematic/m5stickc-plus1.pdf`](schematic/m5stickc-plus1.pdf): the connectivity schematic, made to be followed by clicking.
- [`schematic/README.md`](schematic/README.md): the schematic's sources, its Kleidos additions and corrections, and its open questions.
- [`schematic/netlist.yaml`](schematic/netlist.yaml): every part, pin and net of the schematic with its source.
- [`schematic/improvements.md`](schematic/improvements.md): the triage behind the additions and corrections.
- [`schematic/bench/`](schematic/bench/): the bench probe records.

How the drawings, models and schematics are made, and which script writes each file: [`docs/models-and-drawings.md`](../docs/models-and-drawings.md).
