# Bill of Materials

Consolidated BOM for all six populated subsystem schematics (`power`,
`rp2350b_memory`, `esp32_bt`, `display`, `input`, `usb_c`), compiled for
`pilink-7el.8`. Every reference, value and footprint below was read
directly from the `.kicad_sch` files on `origin/master` at commit
`5fef711` (2026-11-15) — not from memory or the design docs — by grepping
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
ordering. Confirmed for at least one row: a later review queried JLCPCB's
real component-search API directly and found `C15850` (10uF/25V/0805,
used as C1/C119/C201/C501 below) is actually **Basic**, not Extended as
this tool reported — rows marked `†` below should be treated as unverified
either way, not assumed Extended. This same later check also surfaced that
this tool can give false negatives on catalog *presence*, not just
Basic/Extended status (see U103's history under flag 2) — so its "not
found" results shouldn't be read as proof a part is absent from JLCPCB's
real catalog either. The Basic/Extended calls that matter most for this
BOM (U501, D501, J401, J501, SW303 — all genuinely Extended per the prior,
separately human/bead-verified research in `hardware/README.md`) are
still believed correct, but given the above, treat that as a weaker
guarantee than this BOM's first draft claimed.

## Assembly-method flags (read this before ordering)

1. **RM2 vs ESP32-WROOM-32UE — this design does NOT use RM2.** The
   Bluetooth coprocessor is Espressif's **ESP32-WROOM-32UE-N4** (U201,
   LCSC `C701344`), a JLCPCB-catalog SMT module confirmed assemblable by
   JLCPCB's own pick-and-place line (see stock check below). Raspberry
   Pi's RM2 module is **not used anywhere in this design** — see
   `.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md`. Do
   not substitute RM2 or hand-place it; order U201 as a normal JLCPCB SMT
   line item.
2. **One part, L101, is NOT in JLCPCB's SMT parts catalog at all** (not
   just low stock — a `jlcpcb-search` lookup returns no match): Coilcraft
   `LPS4018-332xxx` (3.3uH), the RP2350B internal-VREG inductor. The exact
   Coilcraft `LPS4018` family is in JLCPCB's catalog, but only in other
   inductance values (1mH, 68uH, 180uH, 470uH, 18uH checked) — 3.3uH is not
   stocked by JLCPCB in this footprint. Source directly (Coilcraft/Digikey)
   and hand-place, or substitute a JLCPCB-catalog part at PCB-layout time
   (see flag 5 below). This is a bigger "don't hand-solder it by mistake"
   risk than the RM2/ESP32 question the bead named, since it's easy to miss
   when a BOM is skimmed for Basic/Extended status rather than catalog
   presence at all. Filed as follow-up `pilink-2wq`.

   (**U103 was also flagged here in an earlier draft of this BOM and is
   NOT a catalog gap — see its row below.** Three rounds of disputed
   claims on this one part: draft 1 said "not in catalog" via the
   `jlcpcb-search` MCP tool's local database; review round 1 said it IS
   catalog-listed (Extended, 1,268 units); draft 2 tried to adjudicate via
   a `jlcpcb.com` URL that turned out to be non-functional (returns "0
   Found" for every query, including parts already known in-catalog — a
   false negative, not a real check) and wrongly sided with "not in
   catalog" again; review round 2 settled it with a reproducible check
   against JLCPCB's actual component-search API
   (`POST /api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`)
   and its `partdetail` page (`jlcpcb.com/partdetail/APMemory-APS6404L_3SQRZR/C3040877`,
   loads, labelled "Extended"), both confirmed against known Basic/Extended
   controls. **U103 is a normal Extended JLCPCB catalog part.** The
   `jlcpcb-search` MCP tool's local database snapshot has at least this one
   false negative — treat "not found" results from it as inconclusive, not
   as confirmation of catalog absence, for any future BOM work.)
3. **SW303 (rotary encoder + switch, EC11E18244AU) is through-hole, not
   SMT.** JLCPCB's SMT assembly service only places SMT parts on one side;
   this part needs JLCPCB's THT assembly add-on (extra cost/lead time) or
   hand-soldering at order time — don't assume it rides along with the
   SMT line items below.
4. **Display panel (Crystalfontz CFAF240320A0-024SN) is not an SMT BOM
   line at all.** It connects via FPC into J501 and is bought directly
   from Crystalfontz — no LCSC listing exists for it (confirmed in
   `.planning/decisions/2026-11-15-display-panel-crystalfontz-cfaf240320a0.md`).
   It is a manual/mechanical assembly step, not a JLCPCB SMT part; don't
   look for it in the LCSC columns below.
5. **L501 (display backlight inductor)'s footprint fix has merged to
   master** (`pilink-2wq`, commit `ce6e0e1`). `display.kicad_sch` now
   carries the matching `Inductor_SMD:L_Cenker_CKCS4018` footprint
   directly — no placeholder remains. For context: no 4.7uH
   JLCPCB-catalog part in the old placeholder footprint
   (`Inductor_SMD:L_1210_3225Metric`, EIA 1210, 3.2x2.5mm) with adequate
   saturation current was found (the one 4.7uH catalog hit in an 0805
   package, `C356840`, is rated only 700mA — fails the bead's own gotcha
   below). The part picked instead, `C354574` (Cenker `CKCS4018-4.7uH/M`),
   meets the current/Isat gotcha; its real package is 4.0x4.0x1.8mm —
   **larger** than the old 1210 placeholder. This is now just a PCB
   area/placement note for `pilink-7el.9`: budget the correct, larger
   4x4mm footprint.
6. **Extended-part handling fees apply** to every row marked "Extended"
   below (JLCPCB charges a per-part extended-component fee in addition to
   placement cost) — already called out for U501/D501 by the bead's own
   carried-over note, but it applies project-wide to every other
   Extended-flagged row too (subject to the caveat above about this
   tool's Basic/Extended reporting).
7. **J401 (USB-C receptacle, `pilink-7el.11`) is through-hole, mounted on
   the PCB's BACK side, not SMT.** Swapped from a horizontal SMD part
   (TYPE-C-31-M-12) to a vertical through-hole part (TYPE-C-31-D-09) per
   the upright-desk-clock form factor decision — the connector now needs
   to exit the rear of the enclosure perpendicular to the PCB. Per
   `pilink-0do`'s assembly-approach research
   (`.research/findings/2026-11-15-vertical-usb-c-receptacle-selection.md`),
   the recommendation is **JLCPCB double-sided PCBA** (machine-populate
   both sides; J401 is the only back-side part) rather than hand-soldering
   a THT part onto the back after a front-only PCBA run — this connector
   takes the one repeated mechanical load on the whole board (plug
   insertion/removal, rated 3.57kgf insertion / 1.02kgf min removal), where
   a machine-soldered joint is materially more reliable than a hand-
   soldered one. No live JLCPCB PCBA quote exists yet (needs real
   Gerbers/CPL/BOM from PCB layout, not yet done — `pilink-7el.9`/
   `pilink-7el.12`); ordering assembly is the user's call per `AGENTS.md`,
   not decided here.

## Power (`power.kicad_sch`, refs 1-99)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| U1 | 1 | AP2114H-3.3TRG1 (LDO) | SOT-223-3 | C150716 | AP2114H-3.3TRG1 | Extended | 10,090 |
| C1 | 1 | 10uF, X5R, 25V | 0805 | C15850 | CL21A106KAYNNNE | **Basic (confirmed via JLCPCB API)** | 1,999,860 |
| C2 | 1 | 22uF, X5R, 10V | 0805 | C7432777 | HGC0805R5226K100NSLJ | Extended† | 111,910 |
| C3 | 1 | 100nF, X7R, 16V | 0402 | C880604 | TCC0402X7R104M160AT | Extended† | 4,086,850 |

## RP2350B + Memory (`rp2350b_memory.kicad_sch`, refs 100-199)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| U101 | 1 | RP2350B (MCU) | QFN-80 | C42415655 | RP2350B | Extended | 3,065 |
| Y101 | 1 | 12MHz crystal | 3.2x2.5mm (3225-4Pin) | C20625731 | ABM8-272-T3 | Extended | **365 — low, recheck before ordering build quantity** |
| C101, C102 | 2 | 15pF, C0G/NPO, 50V | 0402 | C1548 | 0402CG150J500NT | Extended† | 307,300 |
| R101, R102, R103 | 3 | 1k | 0402 | C11702 | 0402WGF1001TCE | Extended† | 18,224,200 |
| SW101, SW102 | 2 | Side-actuated tactile switch (`pilink-7el.10`, swapped from PTS645) | SMD, right-angle, 4.5x3.4x3.3mm | C110293 | SKRTLAE010 | Extended | 42,775 |
| L101 | 1 | 3.3uH (RP2350B internal VREG inductor) | Coilcraft LPS4018 footprint | **not in JLCPCB catalog** | Coilcraft LPS4018-332xxx (exact suffix TBD) | n/a | n/a — see assembly flag 2 |
| C103, C104, C105, C118 | 4 | 4.7uF, X5R, 6.3V | 0402 | C380302 | TCC0402X5R475M6R3AT | Extended† | 1,333,700 |
| R104 | 1 | 33R | 0402 | C25105 | 0402WGF330JTCE | Extended† | 78,400 |
| C106-C117 | 12 | 100nF, X7R, 16V | 0402 | C880604 | TCC0402X7R104M160AT | Extended† | 4,086,850 |
| C119 | 1 | 10uF, X5R, 25V | 0805 | C15850 | CL21A106KAYNNNE | **Basic (confirmed via JLCPCB API)** | 1,999,860 |
| U102 | 1 | W25Q128JVSIQ (16MB QSPI flash) | SOIC-8 208mil | C97521 | W25Q128JVSIQ | Extended | 1,387 |
| C120 | 1 | 100nF, X7R, 16V | 0402 | C880604 | TCC0402X7R104M160AT | Extended† | 4,086,850 |
| U103 | 1 | APS6404L-3SQR-ZR (8MB QSPI PSRAM) | USON-8L | C3040877 | APS6404L-3SQR-ZR | Extended (confirmed via JLCPCB's own API + partdetail page — see flag 2 note) | 1,268 |
| C121 | 1 | 2.2uF, X5R, 50V | 0603 | C7432769 | HGC0603R5225K500NTHJ | Extended† | 417,960 |
| R105 | 1 | 100k | 0402 | C25530 | 0402WGJ0104TCE | Extended† | 9,817,600 |

## ESP32 BT coprocessor (`esp32_bt.kicad_sch`, refs 200-299)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| U201 | 1 | ESP32-WROOM-32UE-N4 (BT coprocessor — **not RM2**, see flag 1) | SMD module | C701344 | ESP32-WROOM-32UE-N4 | Extended | **1,878 — down from the ~3,321 recorded at pilink-wot's 2026-11-14 research time; still comfortable for a small build but recheck before a bulk order** |
| R201, R202 | 2 | 10k | 0603 | C15401 | 0603WAJ0103T5E | Extended† | 2,175,700 |
| C203 | 1 | 1uF, X5R, 16V | 0603 | C696901 | TCC0603X5R105K160CT | Extended† | 837,750 |
| C201 | 1 | 10uF, X5R, 25V | 0805 | C15850 | CL21A106KAYNNNE | **Basic (confirmed via JLCPCB API)** | 1,999,860 |
| C202 | 1 | 100nF, X7R, 16V | 0402 | C880604 | TCC0402X7R104M160AT | Extended† | 4,086,850 |

## Display (`display.kicad_sch`, refs 500-599)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| — | 1 | Crystalfontz CFAF240320A0-024SN (display panel) | 40-pin FPC cable, bonded to panel | **no LCSC listing — buy direct from Crystalfontz** | CFAF240320A0-024SN | n/a — not an SMT part, see assembly flag 4 | n/a |
| J501 | 1 | AFC01-S40FCA-00 (40-pos 0.5mm FPC ZIF connector) | SMT | C262674 | AFC01-S40FCA-00 | Extended | 60,445 |
| U501 | 1 | AP3031KTR-G1 (backlight boost driver) | SOT-23-6 | C82636 | AP3031KTR-G1 | **Extended (confirmed — bead-carried gotcha)** | 11,130 |
| R501 | 1 | 5.1R | 0402 | C25174 | 0402WGJ051JTCE | Extended† | 119,600 |
| C501 | 1 | 10uF, X5R, 25V | 0805 | C15850 | CL21A106KAYNNNE | **Basic (confirmed via JLCPCB API)** | 1,999,860 |
| L501 | 1 | 4.7uH, Isat 1.7A (≥ AP3031's 1.2-1.4A switch current — bead-carried gotcha, **satisfied**) | `Inductor_SMD:L_Cenker_CKCS4018`, 4.0x4.0x1.8mm (merged, see flag 5) | C354574 | CKCS4018-4.7uH/M | Extended† | 7,420 |
| C502 | 1 | 0.47uF, X7R, **50V** (≥25V bead-carried gotcha, **satisfied** — OVP clamp is 15.5-19.5V) | 0805 | C49955 | 0805B474K500NT | Extended† | 109,200 |
| D501 | 1 | B5819W (Schottky) | SOD-123 | C64885 | B5819W | **Extended (confirmed — bead-carried gotcha)** | 525,050 |

## Input (`input.kicad_sch`, refs 300-399)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| R303, R304, R309 | 3 | 3.3k | 0402 | C25890 | 0402WGF3301TCE | Extended† | 221,600 |
| SW303 | 1 | EC11E18244AU (rotary encoder + switch) | **Through-hole**, vertical, 20mm shaft | C202365 | EC11E18244AU | Extended (confirmed) | **2,482 — a live-changing figure per pilink-3rm's own note; recheck at order time** |
| R305, R306, R307, R308 | 4 | 10k | 0402 | C60489 | RC0402JR-0710KL | Extended† | 21,253,700 |
| SW305, SW306, SW307, SW308 | 4 | Tactile switch (PTS645 family) | SMD 6x6mm | C221872 | PTS645SK50SMTR92LFS | Extended† | 8,950 |

## USB-C (`usb_c.kicad_sch`, refs 400-499)

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock (checked 2026-11-15) |
|---|---|---|---|---|---|---|---|
| J401 | 1 | TYPE-C-31-D-09 (USB-C receptacle, vertical-mount, swapped from horizontal SMD TYPE-C-31-M-12 in `pilink-7el.11` per the upright-desk-clock form factor) | **Through-hole**, vertical, back-of-PCB mount, 6.50mm body height | C7463258 | TYPE-C-31-D-09 | Extended (confirmed) | 5,651 (live JLCPCB API, 2026-11-15; the `jlcpcb-search` MCP tool's own local snapshot reads 5,490 — known stale-cache gap, recheck before ordering) |
| F401 | 1 | SMD0805B100TFT (1A hold PTC fuse) | 0805 | C269106 | SMD0805B100TFT | Extended† | 5,460 |
| R401, R402 | 2 | 5.1k | 0402 | C25905 | 0402WGF5101TCE | Extended† | 704,500 |
| R403, R404 | 2 | 10k (CC1/CC2 ADC voltage-sense series-protection, `pilink-1sj` — merged, commit `5fef711`) | 0402 | C60489 | RC0402JR-0710KL | Extended† | 21,253,700 |

† See "Known limitation of this stock check" above — this tool reported
every generic 0402/0603/0805 R/C jellybean part as `Extended`, which
contradicts real-world JLCPCB categorization for most of them. Confirm
Basic-vs-Extended for these rows directly on JLCPCB's site before
ordering; it changes the assembly-fee total but not sourcing feasibility.

## Totals

Counted directly from the six `.kicad_sch` files (every non-`#PWR`/`#FLG`
reference designator, re-verified on master at commit `5fef711`,
2026-11-15): power 4, rp2350b_memory 33, esp32_bt 6, display 7, input 12,
usb_c 6 (J401, F401, R401-R404 — `pilink-1sj`'s R403/R404 CC-sense taps,
commit `5fef711`, are now on master) — **68 real components on current
master**. Of those, 67 are ordinary JLCPCB SMT line items (U103 included —
it's a normal catalog part, not a gap, see flag 2) and L101 is the one
catalog-gap part. The display panel itself is a 69th physical part that
was never a schematic symbol (it connects via J501, which *is* counted
above) and is sourced outside LCSC/JLCPCB entirely (flag 4).

Both PRs this BOM previously tracked as pending have merged: `pilink-2wq`'s
L501 footprint fix (commit `ce6e0e1`) and `pilink-1sj`'s R403/R404 CC-sense
taps (commit `5fef711`) are both reflected directly in the counts and rows
above — there is no more pending-PR state to track for either. The only
remaining "pending" item in this BOM is L101's unresolved JLCPCB catalog
status (flag 2/assembly flag 2 above), which is a sourcing question, not a
merge-status one.

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

## Addendum: `pilink-7el.11` (J401 vertical-mount swap, 2026-11-15)

- J401's symbol/pinout is unchanged (same `Connector:USB_C_Receptacle_USB2.0_16P`,
  same nets) — only its `Value`/`Footprint`/`Datasheet` properties on
  `usb_c.kicad_sch` and this BOM's J401 row changed, per the swap documented
  above and in that sheet's own notes.
- A new hand-authored footprint,
  `Connector_USB_Custom:USB_C_Receptacle_HRO_TYPE-C-31-D-09`
  (`hardware/footprints/Connector_USB_Custom.pretty/`, registered in
  `hardware/fp-lib-table`), was added — no stock KiCad footprint matches
  this exact manufacturer part. See that footprint's own `descr` for full
  datasheet-dimension sourcing. PR #41 review caught the shell/peg slots'
  X offset mis-measured as ~3.30mm; fixed to the correct ±2.50mm
  (5.00mm slot-centerline spacing per the datasheet's own PCB-layout
  drawing), along with a minor silkscreen-clearance tweak and removal of
  an erroneous `pad_prop_heatsink` property on the S1 pads.
- `kicad-cli sch erc --severity-all --exit-code-violations` was re-run
  after the swap on the root sheet: 0 errors / 26 warnings (unchanged from
  the pre-swap baseline, since this is a footprint-geometry-only fix — no
  symbol/net/pin behavior changed).
- **Not done by this bead**: no PCB placement or routing (board has no
  real layout yet — `hardware/placeholder.kicad_pcb`), so no
  `kicad-cli pcb drc` was run and the footprint's exact pad geometry was
  not checked in a live board context. That's `pilink-7el.12`'s job.
