<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# USB-serial bridge identity (triage item B8)

Bench read of 2026-11-17 on the M5StickC Plus 1.1 (K016-P), USB connected to the Mac's hub, the case closed. It settles triage item B8 (`../improvements.md`). Read only: no serial port was opened, so the board was not reset or written.

## What was run and what it read

`ioreg -p IOUSB -l` (macOS's USB registry) lists two devices with the bridge's identity on the bench, the Plus 1.1 and the StickC Plus SE, both of which carry a CH552T bridge in their vendor prints (`../netlist.yaml`, U6; `../../../m5stickc-plus-se/schematic/netlist.yaml`). Both report the same:

| Field | Value |
| --- | --- |
| `idVendor` | 1027 (0x0403, FTDI's USB vendor ID) |
| `idProduct` | 24577 (0x6001, FTDI's FT232 product ID) |
| `USB Vendor Name` / `kUSBVendorString` | `Hades2001` |
| `USB Product Name` / `kUSBProductString` | `M5stack` |

No other device on the bench has these IDs. The serial numbers and locations the registry also lists are left out of this record.

## Result

- The Plus 1.1's bridge enumerates as an FTDI FT232 (VID 0x0403, PID 0x6001), manufacturer string `Hades2001`, product string `M5stack`. The part is the CH552T the print names (U6): a USB microcontroller whose firmware presents an FT232's identity, which is why the vendor's docs page points to the FTDI driver.
- The same read was made earlier the same day by the triage (`../improvements.md`, B8); this record writes it down.
