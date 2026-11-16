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

0. **JLCPCB BOM/position exports MUST use `--exclude-dnp`.** J101 is DNP
   (`pilink-cto`), but `kicad-cli` only drops DNP parts when told to, so
   JLCPCB would otherwise place it. Verified against `--help` for this
   KiCad install: `kicad-cli sch export bom --exclude-dnp ...` and
   `kicad-cli pcb export pos --exclude-dnp ...` (both flags exist).
   Check that J101 is absent from both generated files before upload.
   See `hardware/README.md` fab-output notes.

1. **RM2 vs ESP32-WROOM-32UE — this design does NOT use RM2.** The
   Bluetooth coprocessor is Espressif's **ESP32-WROOM-32UE-N4** (U201,
   LCSC `C701344`), a JLCPCB-catalog SMT module confirmed assemblable by
   JLCPCB's own pick-and-place line (see stock check below). Raspberry
   Pi's RM2 module is **not used anywhere in this design** — see
   `.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md`. Do
   not substitute RM2 or hand-place it; order U201 as a normal JLCPCB SMT
   line item.
2. **L101 (VREG inductor) is now a normal JLCPCB catalog part** (`pilink-2wq`):
   the original Coilcraft LPS4018-332 was not stocked by JLCPCB, so L101 was
   swapped to Cenker `CKCS4018-3.3uH/M` (`C354572`, Extended, 2,180 units
   live 2026-11-16; Isat 2.45A, Irms 1.23A, DCR 70mOhm, shielded) -- the
   same CKCS4018 family/footprint as L501. **Not verified:** the RP2350
   datasheet's explicit VREG inductor requirements (DCR/Isat/recommended
   part) could not be text-extracted in the agent environment -- a human
   should confirm 3.3uH/70mOhm/2.45A against the datasheet's VREG section
   before fab. The PCB footprint was swapped in place (same position and
   nets; pads 1.7x3.7mm at +/-1.35mm vs the old 0.87x2.79mm at
   +/-1.765mm, same 4.4mm overall length); one GND track segment was
   rerouted around the larger pad and zones refilled.

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
| L101 | 1 | 3.3uH, Isat 2.45A, DCR 70mOhm (RP2350B internal VREG inductor) | `Inductor_SMD:L_Cenker_CKCS4018`, 4.0x4.0x1.8mm | C354572 | CKCS4018-3.3uH/M | Extended | 2,180 |
| C103, C104, C105, C118 | 4 | 4.7uF, X5R, 6.3V | 0402 | C380302 | TCC0402X5R475M6R3AT | Extended† | 1,333,700 |
| R104 | 1 | 33R | 0402 | C25105 | 0402WGF330JTCE | Extended† | 78,400 |
| C106-C117 | 12 | 100nF, X7R, 16V | 0402 | C880604 | TCC0402X7R104M160AT | Extended† | 4,086,850 |
| C119 | 1 | 10uF, X5R, 25V | 0805 | C15850 | CL21A106KAYNNNE | **Basic (confirmed via JLCPCB API)** | 1,999,860 |
| U102 | 1 | W25Q128JVSIQ (16MB QSPI flash) | SOIC-8 208mil | C97521 | W25Q128JVSIQ | Extended | 1,387 |
| C120 | 1 | 100nF, X7R, 16V | 0402 | C880604 | TCC0402X7R104M160AT | Extended† | 4,086,850 |
| U103 | 1 | APS6404L-3SQR-ZR (8MB QSPI PSRAM) | USON-8L | C3040877 | APS6404L-3SQR-ZR | Extended (confirmed via JLCPCB's own API + partdetail page — see flag 2 note) | 1,268 |
| C121 | 1 | 2.2uF, X5R, 50V | 0603 | C7432769 | HGC0603R5225K500NTHJ | Extended† | 417,960 |
| R105 | 1 | 100k | 0402 | C25530 | 0402WGJ0104TCE | Extended† | 9,817,600 |
| J101 | 1 | **DNP (pilink-cto: do not assemble; footprint/pads only)** SWD debug header, 3-pin, 2.54mm pitch (`pilink-2ar` — SWCLK/GND/SWDIO; pitch corrected in PR #43 review — 1.27mm doesn't match any cable Raspberry Pi's Debug Probe actually ships with) | THT vertical, 1x3P | C32713269 | Hanxia HX PZ2.54-1x3P ZZ | Extended | 59,160 (single snapshot: `jlcpcb-search` MCP, 2026-11-16; earlier 60,450 / 59,380 figures superseded; not re-checked against the rest of this BOM's 2026-11-15 13:12 snapshot) |

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
| J501 | 1 | FC-05B40P21H20 (40-pos 0.5mm FPC ZIF connector, dual-contact/top-and-bottom-entry — swapped from bottom-contact-only AFC01-S40FCA-00 by pilink-4b6, REQUIRED pre-fab fix; pin-1 numbers from the OPPOSITE end vs. the old part — footprint/symbol pin numbers corrected to match, net assignments unchanged, see display.kicad_sch notes and this file's pilink-4b6 addendum; cable-entry-side vs. the old part still unconfirmed) | SMT | C23398824 | FC-05B40P21H20 | Extended | 2,635 (checked 2026-11-16 via `jlcpcb-search` MCP, same session as the swap — not part of this table's 2026-11-15 snapshot) |
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

## Hand-fitted parts (not on a schematic, not PCBA-assembled)

These have no reference designator and are not in the `.kicad_sch` counts
below. LCSC sells the part, but it is a cable-and-connector antenna with no
SMD pads, so JLCPCB's pick-and-place line cannot place it: order it from
LCSC separately and mate it by hand to U201's U.FL receptacle. This is the
part the enclosure design assumes (`enclosure/antenna_mount.scad`,
`enclosure/back_shell.scad`).

| Ref | Qty | Value / Part | Package | LCSC | Mfr P/N | Basic/Ext† | Stock |
|---|---|---|---|---|---|---|---|
| — | 1 | 2.4GHz adhesive FPC antenna with Ø1.13mm coax pigtail and IPEX/U.FL-class (IPEX gen. 1) plug, ~2dBi (under the 2.33dBi cert-safe ceiling), 45.8x6.5mm element, 3M adhesive backing. **Hand-fitted, not PCBA-assembled.** Cable length: ~240mm by part number and the datasheet's table ("L=240 MM"), but the same datasheet's drawing says 100+-2mm — measure on receipt (`pilink-bl2`) | Hand-fit, mates to U201's U.FL | C4943394 | Kinghelm KH-FPC2.4G-1.13IPEX-240 | n/a — not a JLCPCB-catalog (PCBA) part | ~86 units at the 2026-11-15 research snapshot (`.research/findings/2026-11-15-ufl-antenna-selection.md`); LCSC's live counter is client-side, so recheck on LCSC before ordering |

Fallback (not on the build): MyAntenna AIWF026, LCSC `C49242188`, 100mm
pigtail, but its 2.4GHz in-band peak gain (2.35dBi) is 0.02dB over
Espressif's 2.33dBi ceiling — see the research finding above.

## Totals

Counted directly from the six `.kicad_sch` files (every non-`#PWR`/`#FLG`
reference designator, re-verified on master at commit `5fef711`,
2026-11-15): power 4, rp2350b_memory 33, esp32_bt 6, display 7, input 12,
usb_c 6 (J401, F401, R401-R404 — `pilink-1sj`'s R403/R404 CC-sense taps,
commit `5fef711`, are now on master) — **68 real components on current
master**. Of those, 67 are ordinary JLCPCB SMT line items (U103 included —
it's a normal catalog part, not a gap, see flag 2) and L101 (now C354572) is likewise a normal catalog part, so there are no catalog gaps. The display panel itself is a 69th physical part that
was never a schematic symbol (it connects via J501, which *is* counted
above) and is sourced outside LCSC/JLCPCB entirely (flag 4).

Both PRs this BOM previously tracked as pending have merged: `pilink-2wq`'s
L501 footprint fix (commit `ce6e0e1`) and `pilink-1sj`'s R403/R404 CC-sense
taps (commit `5fef711`) are both reflected directly in the counts and rows
above — there is no more pending-PR state to track for either. The only
remaining "pending" item in this BOM is L101's unresolved JLCPCB catalog
status (flag 2/assembly flag 2 above), which is a sourcing question, not a
merge-status one.

**Update (`pilink-2ar`, on top of this BOM's `5fef711` snapshot):** one new
component, `J101` (the new SWD debug header — see `hardware/README.md`'s
`pilink-2ar` update), added to `rp2350b_memory.kicad_sch`'s table above —
**34** real components on that sheet now, **69 total** project-wide. Only
`J101`'s own row was freshly checked (live via `jlcpcb-search` MCP,
2026-11-15, same session as this bead); the rest of this file's rows are
still the `5fef711`-commit snapshot described above, not re-verified by
this bead.

**Update (PR #43 review fix):** `J101` swapped from the 1.27mm-pitch part
(LCSC `C22438100`) to a 2.54mm-pitch part (LCSC `C32713269`, same Hanxia
`HX PZ...-1x3P ZZ` family) after review found the 1.27mm pitch didn't
match any cable Raspberry Pi's Debug Probe actually ships with (checked
against the `raspberrypi/documentation` repo, not just the original
claim) — see `hardware/README.md`'s `J101` bullet for the full rationale.
Re-checked live via `jlcpcb-search` MCP, 2026-11-16.

**Update (`pilink-cto`):** `J101` is now **DNP** (schematic `dnp`, PCB
footprint `dnp` attribute; pads kept). The Hanxia `PZ2.54-1x3P ZZ` (LCSC
`C32713269`, 59,160 in stock 2026-11-16) really is 2.5mm plastic + 6mm
mating pin + 3mm solder tail (LCSC spec table), so 8.5mm above the PCB
face -- 3mm taller than the 5.5mm front cavity, i.e. the pins would pierce
the 2mm face plate. A short/low-profile 2.54mm header can't work either
(a Dupont/Debug Probe cable needs ~6mm of pin) and a right-angle one
points at an enclosure wall. Pads-only keeps SWD reachable for bring-up:
hand-solder a 3-pin header (or three wires) into J101's holes before
closing the shell; leave DNP in the JLCPCB assembly order. A
face-plate/bottom-wall access cutout is an enclosure call for a later
bead. "Populated parts" count stays 69 on the schematic, 68 assembled.

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

## Addendum: `pilink-4b6` (J501 dual-contact FPC connector swap, 2026-11-16)

- **Required pre-fab fix, not an optional evaluation**: under this
  project's back-face FPC-contact-side working assumption
  (`.research/findings/2026-11-15-display-fpc-contact-side.md`), the
  previously-specified bottom-contact-only AFC01-S40FCA-00 (C262674) does
  NOT correctly mate the display FPC's J-fold geometry that
  `pilink-7el.12` already built into the PCB layout. Swapped to the
  dual-contact FC-05B40P21H20 (C23398824, BXCONN) — mates either contact
  orientation, removing the dependency on resolving contact side at all,
  with no change to the proven J-fold geometry (the finding's preferred
  fix).
- Live stock reconfirmed this session via `jlcpcb-search` MCP:
  FC-05B40P21H20 (C23398824) — **2,635 units**, consistent with the
  finding's 2026-11-15 reading. Comfortable for a small build; recheck
  before a bulk order.
- J501's symbol (`pico_link_custom:CFAF240320A0_FPC40`) and footprint
  (`Connector_FPC:FC-05B40P21H20`,
  `hardware/footprints/Connector_FPC.pretty/`, registered in the existing
  `Connector_FPC` entry in `hardware/fp-lib-table`; the old
  `AFC01-S40FCA-00` footprint file is left in place for history but no
  longer referenced) were both corrected in a follow-up fix round
  (2026-11-16, review of this PR) — see the next two bullets. Pitch
  (0.5mm) and the full 40-position span (19.5mm, pins at -9.75..+9.75mm)
  are sourced directly from the new part's own CAD drawing (recovered in
  this environment by hand-decompressing the datasheet PDF's content
  stream and replaying its vector path/bezier operators — no PDF
  rasterizer was installed) and cross-checked against JLCPCB's own
  assembly-library footprint data for the part (see below). Its
  body/courtyard Y-profile is still a reused placeholder from the prior
  footprint (same connector class/similar overall size per the new part's
  own DIMB formula), not independently measured — flag for a human
  KiCad-GUI pass before fab, same caveat class as every other
  hand-authored footprint in this project.
- **PIN-1 — RESOLVED.** The two parts number pin 1 from **opposite**
  physical ends. Confirmed independently (not just transcribed from a
  review) via `easyeda.com/api/products/<LCSC>/components` — a plain
  `curl GET` against this endpoint returns JLCPCB's own assembly-library
  footprint data (real pad coordinates) with no WAF block, unlike the
  easyeda.com website itself, which blocked the previous round. With both
  parts' footprints read in the same canonical orientation (signal-pad
  row at the front edge, mounting tabs/body behind): FC-05B40P21H20's
  (C23398824) pad 1 and its silkscreen pin-1 dot sit at its **right** end;
  AFC01-S40FCA-00's (C262674) pad 1 sits at its **left** end. This agrees
  with the BXCONN drawing's own NO.1 marker (right end in its view 1).
  Fix applied: since ZIF contacts are straight-through, each physical pad
  position keeps the net it always had (physical net assignment was
  already correct and unchanged) — only the pad/pin *number labels* were
  wrong. The footprint's pads 1-40 were mirror-renumbered (physical
  position x=+9.75 is now pad "1", matching the real part; was mislabeled
  "40"), and the symbol's 40 signal pins were mirror-renumbered in
  lockstep (pin k -> 41-k) so every signal (DB17-0, SDA, DOTCLK,
  HSYNC/VSYNC, RD/WR, RS, CS, RESET, IMx, power/ground) still lands on the
  same physical pad position as before. Verified via an exported-netlist
  diff: J501's physical pin-to-net mapping is identical before and after
  the renumbering — see this bead's PR body for the diff result.
  **Cable-entry-side caveat (separate from pin-1, still open):** whether
  the two parts' FPC cables insert from the same side relative to the pad
  row could not be confirmed — the EasyEDA footprint data, LCSC product
  photos, and JLC parametric fields all show identical "Flip-Top"/"Right
  Angle" conventions for both parts with no explicit entry-side field, and
  C262674's datasheet has no dimensioned drawing to check against. Flag
  for a human with physical samples before fab.
- **Dimension fixes** (also EasyEDA-API-verified, cross-checked against
  the BXCONN drawing's PCB-layout view): mounting tabs (MP1/MP2) are
  1.5mm wide x 2.5mm tall, centered at X=±11.45mm, 3.10mm from the signal
  pad row (was a 2.0x1.6mm placeholder at 2.68mm); signal pads are 1.5mm
  long (was 1.3mm).
- `kicad-cli sch erc --severity-all --exit-code-violations` was re-run
  after both the original swap and this fix round on the root sheet — see
  this bead's PR body for the actual before/after counts.
- **Not done by this bead**: no PCB placement or routing change — this is
  schematic/BOM scope only. `pilink-7el.12`'s existing J501 PCB placement
  (insertion-face inset, vertical offset, rotation) was not touched; its
  assumptions should be re-checked against the new footprint's actual pad
  geometry (close to, but not identical to, the old footprint's) before
  fab. No PCB re-placement was found to be strictly required by this
  swap, but it was not independently re-verified in a live board context
  either — flag as a follow-up if a human KiCad pass finds otherwise.
