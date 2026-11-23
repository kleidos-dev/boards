<!--
SPDX-FileCopyrightText: 2026 José M. Requena Plens
SPDX-License-Identifier: MIT
-->

# Improving the vendor's print: Kleidos entries and bench records

The rule (owner, 2026-11-17; `AGENTS.md`, "Schematics"): the drawing improves on the vendor's print rather than following it to the letter, and every place where it does is an entry of `kleidos` in the board's `schematic/netlist.yaml`, marked on the drawing and listed with its source on page 1. Nothing silently differs from the print. The format and what the checks hold are in `docs/models-and-drawings.md`, "Kleidos additions and corrections"; this page is how to get from a doubt to an entry.

## What counts as evidence

An entry needs a primary source that makes the fact certain. Four kinds, the `source.type` of the entry:

| Type | What it is | How it is cited |
| --- | --- | --- |
| `datasheet` | The chip's own datasheet: a pin's function, an I2C address, an internal pull, a connection the chip requires | Document, version, page or table |
| `vendor-doc` | The vendor's other documents: a pin map, a manual, the product page | Document and section; the address goes in the README's sources |
| `firmware` | The Kleidos firmware's verified behavior on that board: code that works on the real board | "Kleidos firmware", the file's repository path and the symbol (function, constant or macro); never a commit or a line number, which will not survive the firmware's squash at publication |
| `bench` | A probe run for it on the board | The bench record's path under the board's `schematic/` folder and the date of the probe |

Anything else is not a primary source: a forum post, a community schematic, the datasheet of a similar part standing in for one whose own was not found, what such chips usually do. A fact that rests on one of those stays out and is listed as open.

## From a doubt to an entry

1. **Triage it** in `<board>/schematic/improvements.md`: one row per candidate with the claim, the evidence read (document, page) and a status: K addition or K correction (settled, with the element named), no entry (settled, the drawing already agrees or the print gives the fact), no element fits (settled, but every element kind would misdraw it), needs bench, stays out (cannot be settled without opening the board, or no primary source exists), or a disagreement to fix in `board.json` or in the firmware repository. The file also lists the sources read and the probes that would settle what is open.
2. **Probe what a probe can settle**, on the bench, and write the record (below) before the entry that cites it. A probe that cannot be run from the board's console (a meter on a header, a look at an LED's color, an opened case) stays "needs bench" with what it needs, and the record says what the console could read instead.
3. **Write the entry** in `netlist.yaml`:

   ```yaml
   kleidos:
     - id: K1
       kind: addition                   # addition | correction
       what: "The RTC U9 answers at I2C address 0x51."
       element: {i2c: U9}               # pin: U9.5 | part: R99 | net: SDA | gpio: GPIO21 | i2c: U9 | pull: R13 | rail: "+3.3V"
       source:
         type: datasheet                # datasheet | vendor-doc | firmware | bench
         cite: "BM8563 datasheet V1.1, <page or table>: write address A2h"
     - id: K2
       kind: correction
       what: "U1 pin 19 (VDD3P3_RTC) is on VESP_3V3."
       vendor: "the wire crosses the VESP_3V3 bar with no junction dot"   # a correction says what the print shows
       element: {pin: U1.19}
       source: {type: bench, cite: "bench/<date>-<what>.md, <date of the probe>"}
   ```

   Ids run `K1`, `K2`... in order. One entry per element; a correction carries `vendor`, an addition does not; no citation is empty. A `pin` or `part` addition draws the wires dotted, as an added connection, so a fact about a connection the print does show (a GPIO's function, an address, a pull, a rail's value) goes on its row of the nets or power page (`gpio`, `i2c`, `pull`, `rail`) and not on the pin.
4. **Regenerate and export**: `_shared/kicad_schematic.py <board>`, then `_shared/export_schematic.py <board>` (ERC, the netlist pin for pin, each entry marked and listed, its marker repeated on every index row and power-tree box that shows the element again, the PDF and its links). The generator refuses a malformed entry; the checks refuse a marker or a row with no entry behind it.
5. **Update the board's `schematic/README.md`** in the same change: the "Kleidos additions and corrections" table (id, kind, what, where it is marked, source), and "Open questions" (what stays uncertain and what would settle it). A firmware statement the evidence contradicts is reported to the owner and fixed in the firmware repository; this repository keeps no firmware errata.

## Wording

- With entries, the notes on page 1 and the README say "connectivity documented from the vendor's public documentation, with Kleidos additions and corrections listed on page 1". A board with no entry must not say it.
- Never describe a schematic as the vendor's "redrawn" or "copied". It documents connectivity: facts of what connects where, with the values the vendor documents, in this project's own layout and symbols.
- A value changed with no entry because the print itself gives it (a rating printed on another page of the print) is said in the README, so the difference is still visible.

## Bench records

A probe is written up in `<board>/schematic/bench/<date>-<what>.md`, one file per probe or per run of related probes. It holds:

- which probe of `improvements.md` it is and the question it answers;
- the board's state: which board, case closed or open, how it was powered, what was connected;
- the firmware image it ran on: the env, the commit it was built from and the ELF's SHA-256 prefix (an image found on the board is said to be so);
- what was run, command by command, with every register written put back to its read value and said so;
- the results, as a table where there are several readings;
- what it proves, and what it does not: a probe that settles half a question says which half, and an observation that no claim uses is marked as a side observation.

No serial number, port path, IP or MAC address, lab hostname or home-directory path goes into a record.

## What stays out

- A detail no primary source settles. It goes in the README's "Open questions" with what would settle it.
- Anything about placement, routing, footprints or part numbers the vendor does not print: this is not a PCB design.
- Vendor documents themselves. A datasheet or a schematic PDF is read where it is published (or from the Internet Archive's copy, cited with its capture date and SHA-256) and never kept in the tree.
