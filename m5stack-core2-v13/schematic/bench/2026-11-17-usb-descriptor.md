<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# P02: USB descriptor of the USB-UART bridge (2026-11-17)

Probe P02 of `../improvements.md`. Read only, on the host: the macOS I/O Registry entry of the device the Core2 v1.3 enumerates when its USB-C is plugged into the bench hub (`ioreg -p IOUSB -l`), matched to the board by its serial number (private, left out of this record). The case was not opened.

## Results

| Field | Value |
| --- | --- |
| `idVendor` | 6790 (`0x1a86`, QinHeng Electronics / WCH) |
| `idProduct` | 21972 (`0x55d4`) |
| `bcdDevice` | 1092 (`0x0444`) |
| `USB Product Name` | `USB Single Serial` |

## What it proves

The board's USB-UART bridge enumerates as WCH `1a86:55d4`, the ID of WCH's CH9102 family, the same reading Kleidos recorded on 2026-06-02 (`docs/device-identifiers.md`, section "List every cu.* serial node with its USB serial number / MAC"). With the docs page and the back label it settles that U3 is a CH9102F, not the CP2104 the core sheet draws (T01). It says nothing about the CH9102F's pinout, which still needs its datasheet.
