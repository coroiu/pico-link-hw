# Bill of Materials

Consolidated BOM for all six populated subsystem schematics (`power`,
`rp2350b_memory`, `esp32_bt`, `display`, `input`, `usb_c`), compiled for
`pilink-7el.8`. Every reference, value and footprint below was read
directly from the `.kicad_sch` files on `origin/master` at commit
`8c9b2d4` (2026-11-15) — not from memory or the design docs — by grepping
every placed `(symbol (lib_id ...))` instance and its `Reference`/`Value`/
`Footprint` properties in each sheet. LCSC part numbers and stock were
checked **live** on 2026-11-15 via the `jlcpcb-search` MCP server (local
JLCPCB parts database, downloaded 2026-11-15 13:12, 390,031 components) —
not the LCSC website directly, but the same JLCPCB/LCSC catalog data the
earlier subsystem beads used. Where a part's LCSC number was already
pinned down and verified by an earlier bead (documented in
`hardware/README.md`), that number was re-checked for current stock here
rather than re-derived.

**Known limitation of this stock check:** the `jlcpcb-search` tool's local
database reports *every* part looked up for this BOM — including
jellybean 0402/0603 resistors and capacitors that are unambiguously
JLCPCB **Basic** parts in real life — as `Extended`. This looks like a
dataset/tool defect, not reality; JLCPCB's own site should be the
tie-breaker for Basic-vs-Extended on the generic passives below before
ordering. The Basic/Extended calls that matter most for this BOM (U501,
D501, J401, J501, SW303 — all genuinely Extended per the prior, separately
human/bead-verified research in `hardware/README.md`) are **not** in
doubt; it's only the jellybean R/C rows where this tool's label should be
distrusted.

## Assembly-method flags (read this before ordering)

1. **RM2 vs ESP32-WROOM-32UE — this design does NOT use RM2.** The
   Bluetooth coprocessor is Espressif's **ESP32-WROOM-32UE-N4** (U201,
   LCSC `C701344`), a JLCPCB-catalog SMT module confirmed assemblable by
   JLCPCB's own pick-and-place line (see stock check below). Raspberry
   Pi's RM2 module is **not used anywhere in this design** — see
   `.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md`. Do
   not substitute RM2 or hand-place it; order U201 as a normal JLCPCB SMT
   line item.
2. **Two parts are NOT in JLCPCB's SMT parts catalog at all** (not just
   low stock — a `jlcpcb-search` lookup for either returns no match):
   - **U103, APS6404L-3SQR-ZR** (8MB PSRAM, USON-8). LCSC lists it as a
     distributor part (`C3040877`, per `rp2350b_memory.kicad_sch`'s own
     notes) but it is not in JLCPCB's assembly catalog — JLCPCB cannot
     place it for you. It must be bought separately (LCSC/Digikey) and
     either hand-soldered or added as a manual placement line at order
     time.
   - **L101, Coilcraft LPS4018-332xxx (3.3uH)**, the RP2350B internal-VREG
     inductor. The exact Coilcraft `LPS4018` family is in JLCPCB's
     catalog, but only in other inductance values (1mH, 68uH, 180uH,
     470uH, 18uH checked) — 3.3uH is not stocked by JLCPCB in this
     footprint. Same consequence as U103: source directly (Coilcraft/
     Digikey) and hand-place, or substitute a JLCPCB-catalog part at
     PCB-layout time (see flag 4 below).
   This is a bigger "don't hand-solder it by mistake" risk than the
   RM2/ESP32 question the bead named, since these two are easy to miss
   when a BOM is skimmed for Basic/Extended status rather than
   catalog presence at all. Filed as follow-up `pilink-2wq`.
3. **Display panel (Crystalfontz CFAF240320A0-024SN) is not an SMT BOM
   line at all.** It connects via FPC into J501 and is bought directly
   from Crystalfontz — no LCSC listing exists for it (confirmed in
   `.planning/decisions/2026-11-15-display-panel-crystalfontz-cfaf240320a0.md`).
   It is a manual/mechanical assembly step, not a JLCPCB SMT part; don't
   look for it in the LCSC columns below.
4. **L501 (display backlight inductor) is a value+footprint compromise,
   not a confirmed exact match.** The schematic draws `Inductor_SMD:
   L_1210_3225Metric` (EIA 1210, 3.2x2.5mm). No 4.7uH JLCPCB-catalog part
   in that exact footprint with adequate saturation current was found
   (the one true-1210 4.7uH catalog hit, `C356840`, is rated only 700mA —
   fails the bead's own gotcha below). The part picked instead,
   `C354574` (Cenker `CKCS4018-4.7uH/M`), meets the current/Isat gotcha
   but is a smaller 4.0x1.8mm package — a footprint change the PCB-layout
   bead (`pilink-7el.9`) needs to make deliberately, not something this
   BOM-only bead should silently rewrite into the schematic. Flagged on
   `pilink-2wq` too.
5. **Extended-part handling fees apply** to every row marked "Extended"
   below (JLCPCB charges a per-part extended-component fee in addition to
   placement cost) — already called out for U501/D501 by the bead's own
   carried-over note, but it applies project-wide to every other
   Extended-flagged row too (subject to the caveat above about this
   tool's Basic/Extended reporting).

## Power (`power.kicad_sch`, refs 1-99)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| U1 | 1 | AP2114H-3.3TRG1 (LDO) | SOT-223-3 | C150716 | AP2114H-3.3TRG1 | Extended | 10,090 |
| C1 | 1 | 10uF, X5R, 25V | 0805 | C15850 | CL21A106KAYNNNE | Extended† | 1,999,860 |
| C2 | 1 | 22uF, X5R, 10V | 0805 | C7432777 | HGC0805R5226K100NSLJ | Extended† | 111,910 |
| C3 | 1 | 100nF, X7R, 16V | 0402 | C880604 | TCC0402X7R104M160AT | Extended† | 4,086,850 |

## RP2350B + Memory (`rp2350b_memory.kicad_sch`, refs 100-199)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| U101 | 1 | RP2350B (MCU) | QFN-80 | C42415655 | RP2350B | Extended | 3,065 |
| Y101 | 1 | 12MHz crystal | 3.2x2.5mm (3225-4Pin) | C20625731 | ABM8-272-T3 | Extended | **365 — low, recheck before ordering build quantity** |
| C101, C102 | 2 | 15pF, C0G/NPO, 50V | 0402 | C1548 | 0402CG150J500NT | Extended† | 307,300 |
| R101, R102, R103 | 3 | 1k | 0402 | C11702 | 0402WGF1001TCE | Extended† | 18,224,200 |
| SW101, SW102 | 2 | Tactile switch (PTS645 family) | SMD 6x6mm | C221872 | PTS645SK50SMTR92LFS | Extended† | 8,950 |
| L101 | 1 | 3.3uH (RP2350B internal VREG inductor) | Coilcraft LPS4018 footprint | **not in JLCPCB catalog** | Coilcraft LPS4018-332xxx (exact suffix TBD) | n/a | n/a — see assembly flag 2 |
| C103, C104, C105, C118 | 4 | 4.7uF, X5R, 6.3V | 0402 | C380302 | TCC0402X5R475M6R3AT | Extended† | 1,333,700 |
| R104 | 1 | 33R | 0402 | C25105 | 0402WGF330JTCE | Extended† | 78,400 |
| C106-C117 | 12 | 100nF, X7R, 16V | 0402 | C880604 | TCC0402X7R104M160AT | Extended† | 4,086,850 |
| C119 | 1 | 10uF, X5R, 25V | 0805 | C15850 | CL21A106KAYNNNE | Extended† | 1,999,860 |
| U102 | 1 | W25Q128JVSIQ (16MB QSPI flash) | SOIC-8 208mil | C97521 | W25Q128JVSIQ | Extended | 1,387 |
| C120 | 1 | 100nF, X7R, 16V | 0402 | C880604 | TCC0402X7R104M160AT | Extended† | 4,086,850 |
| U103 | 1 | APS6404L-3SQR-ZR (8MB QSPI PSRAM) | USON-8L | C3040877 (LCSC distributor listing) | APS6404L-3SQR-ZR | **n/a — not in JLCPCB assembly catalog** | n/a — see assembly flag 2 |
| C121 | 1 | 2.2uF, X5R, 50V | 0603 | C7432769 | HGC0603R5225K500NTHJ | Extended† | 417,960 |
| R105 | 1 | 100k | 0402 | C25530 | 0402WGJ0104TCE | Extended† | 9,817,600 |

## ESP32 BT coprocessor (`esp32_bt.kicad_sch`, refs 200-299)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| U201 | 1 | ESP32-WROOM-32UE-N4 (BT coprocessor — **not RM2**, see flag 1) | SMD module | C701344 | ESP32-WROOM-32UE-N4 | Extended | **1,878 — down from the ~3,321 recorded at pilink-wot's 2026-11-14 research time; still comfortable for a small build but recheck before a bulk order** |
| R201, R202 | 2 | 10k | 0603 | C15401 | 0603WAJ0103T5E | Extended† | 2,175,700 |
| C203 | 1 | 1uF, X5R, 16V | 0603 | C696901 | TCC0603X5R105K160CT | Extended† | 837,750 |
| C201 | 1 | 10uF, X5R, 25V | 0805 | C15850 | CL21A106KAYNNNE | Extended† | 1,999,860 |
| C202 | 1 | 100nF, X7R, 16V | 0402 | C880604 | TCC0402X7R104M160AT | Extended† | 4,086,850 |

## Display (`display.kicad_sch`, refs 500-599)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| — | 1 | Crystalfontz CFAF240320A0-024SN (display panel) | 40-pin FPC cable, bonded to panel | **no LCSC listing — buy direct from Crystalfontz** | CFAF240320A0-024SN | n/a — not an SMT part, see assembly flag 3 | n/a |
| J501 | 1 | AFC01-S40FCA-00 (40-pos 0.5mm FPC ZIF connector) | SMT | C262674 | AFC01-S40FCA-00 | Extended | 60,445 |
| U501 | 1 | AP3031KTR-G1 (backlight boost driver) | SOT-23-6 | C82636 | AP3031KTR-G1 | **Extended (confirmed — bead-carried gotcha)** | 11,130 |
| R501 | 1 | 5.1R | 0402 | C25174 | 0402WGJ051JTCE | Extended† | 119,600 |
| C501 | 1 | 10uF, X5R, 25V | 0805 | C15850 | CL21A106KAYNNNE | Extended† | 1,999,860 |
| L501 | 1 | 4.7uH, Isat 1.7A (≥ AP3031's 1.2-1.4A switch current — bead-carried gotcha, **satisfied**) | 4.0x1.8mm — **not the schematic's drawn 1210/3225mm footprint**, see assembly flag 4 | C354574 | CKCS4018-4.7uH/M | Extended† | 7,420 |
| C502 | 1 | 0.47uF, X7R, **50V** (≥25V bead-carried gotcha, **satisfied** — OVP clamp is 15.5-19.5V) | 0805 | C49955 | 0805B474K500NT | Extended† | 109,200 |
| D501 | 1 | B5819W (Schottky) | SOD-123 | C64885 | B5819W | **Extended (confirmed — bead-carried gotcha)** | 525,050 |

## Input (`input.kicad_sch`, refs 300-399)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| R303, R304, R309 | 3 | 3.3k | 0402 | C25890 | 0402WGF3301TCE | Extended† | 221,600 |
| SW303 | 1 | EC11E18244AU (rotary encoder + switch) | Vertical, 20mm shaft | C202365 | EC11E18244AU | Extended (confirmed) | **2,482 — a live-changing figure per pilink-3rm's own note; recheck at order time** |
| R305, R306, R307, R308 | 4 | 10k | 0402 | C60489 | RC0402JR-0710KL | Extended† | 21,253,700 |
| SW305, SW306, SW307, SW308 | 4 | Tactile switch (PTS645 family) | SMD 6x6mm | C221872 | PTS645SK50SMTR92LFS | Extended† | 8,950 |

## USB-C (`usb_c.kicad_sch`, refs 400-499)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| J401 | 1 | TYPE-C-31-M-12 (USB-C receptacle) | SMT 16P | C165948 | TYPE-C-31-M-12 | Extended (confirmed) | 513,950 |
| F401 | 1 | SMD0805B100TFT (1A hold PTC fuse) | 0805 | C269106 | SMD0805B100TFT | Extended† | 5,460 |
| R401, R402 | 2 | 5.1k | 0402 | C25905 | 0402WGF5101TCE | Extended† | 704,500 |

† See "Known limitation of this stock check" above — this tool reported
every generic 0402/0603/0805 R/C jellybean part as `Extended`, which
contradicts real-world JLCPCB categorization for most of them. Confirm
Basic-vs-Extended for these rows directly on JLCPCB's site before
ordering; it changes the assembly-fee total but not sourcing feasibility.

## Totals

Counted directly from the six `.kicad_sch` files (every non-`#PWR`/`#FLG`
reference designator, 2026-11-15): power 4, rp2350b_memory 33, esp32_bt 6,
display 7, input 12, usb_c 4 — **66 real components project-wide**. Of
those, 64 are ordinary JLCPCB SMT line items; U103 and L101 are the two
catalog-gap parts in assembly flag 2 above, and the display panel itself
is a 67th physical part that was never a schematic symbol (it connects via
J501, which *is* counted above) and is sourced outside LCSC/JLCPCB
entirely (flag 3).

## Not verified by this bead

- **DRC/ERC were not re-run** — no schematic or footprint files were
  edited by this bead, only this new BOM document, so the existing
  per-sheet ERC results documented in `hardware/README.md` still apply
  unchanged.
- **Live stock figures are a point-in-time snapshot** (2026-11-15,
  `jlcpcb-search`'s local database downloaded the same day) — several
  rows above are explicitly flagged as worth rechecking closer to order
  time (Y101, U201, SW303, U102, L501, F401).
- **Basic-vs-Extended status for the jellybean passives** could not be
  confirmed through this tool (see the limitation note above) — spot-check
  on JLCPCB's own site before finalizing assembly cost.
- **No money was spent and no order was placed** — this is a sourcing
  document only.
