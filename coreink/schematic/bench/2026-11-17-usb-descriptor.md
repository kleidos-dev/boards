# P06: USB descriptor of the USB-UART bridge (2026-11-17)

Probe P06 of `../improvements.md`. Read only, on the host: the macOS I/O Registry entry of the device the CoreInk enumerates when its USB-C is plugged into the bench hub (`ioreg -p IOUSB -l`), matched to the board by its serial number (private, left out of this record). No firmware was involved and the case was not opened.

## Results

| Field | Value |
| --- | --- |
| `idVendor` | 6790 (`0x1a86`, QinHeng Electronics / WCH) |
| `idProduct` | 21972 (`0x55d4`) |
| `bcdDevice` | 1092 (`0x0444`) |
| `USB Product Name` | `USB Single Serial` |

## What it proves

The bench unit's USB-UART bridge enumerates as WCH `1a86:55d4`, the ID of WCH's CH9102 family, the same reading Kleidos recorded for this board (`docs/device-identifiers.md`, section "List every cu.* serial node with its USB serial number / MAC"). The bench unit therefore carries a CH9102, not the CP2104 the vendor print draws; it is one of the later units the vendor's docs page mentions (T06). This is a fact about one unit, for the README only: the print documents the CP2104 version, and no CH9102 version of the circuit is published, so the drawing keeps the print's CP2104.
