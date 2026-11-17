# Shorter / lower-profile encoder options for a lower knob (`pilink-8hy`)

## Question

The current encoder, SW303 Alps Alpine **EC11E18244AU** (LCSC C202365), puts the
shaft tip 24.5mm above the PCB. Against the enclosure's 7.5mm face-to-PCB stack
that is 17.0mm of shaft proud of the face and a 17.5mm-tall knob
(`enclosure/knob.scad`: `SHAFT_PROUD` 17.0, `KNOB_H` 17.5; see
`2026-11-15-encoder-ec11e18244au-specs.md`). Are there JLCPCB-stocked
encoders that give a lower knob: (a) same EC11 family with a shorter shaft,
(b) a different or lower-profile family? Research only; nothing in
`hardware/` or `enclosure/` was changed.

Estimated knob height below uses the repo's own relation `KNOB_H = (tip above
face) - KNOB_GAP(1.0) + TOP_WALL(1.5) = tip above face + 0.5`
(17.0 -> 17.5). Face outer surface = 7.5mm above PCB (`front_shell.scad`).

## Sources

1. LCSC/JLCPCB live data via the `jlcpcb-search` MCP (`search_components`,
   `get_component_details`), 2026-11-17. All parts below are **Extended**.
2. Alps Alpine EC11E product pages (`tech.alpsalpine.com/e/products/detail/<MPN>/`,
   fetched 2026-11-17) for EC11E09244BS, EC11E09204A4, EC11E15204A3,
   EC11E1820402, EC11E15244B2, EC11E18244AU, and EC12E24204A2.
3. Alps' own EC11E series catalogue PDF
   (`tech.alpsalpine.com/cms.media/product_catalog_ec_01_ec11e_en_611f078659.pdf`,
   update code 2510). Its "Product List" table, text-extracted from the PDF,
   lists 9 variants (the same 9 MPNs LCSC stocks as EC11E09204A4,
   EC11E15204A3, EC11E1820402, EC11E09244BS, EC11E15244G1, EC11E18244AU,
   EC11E09244AQ, EC11E15244B2, EC11E18244A5), **every one with "Actuator
   length 20mm"**, with a note that "products other than those listed are
   also available, contact us".
4. Alps EC11E18244AU side-view drawing (`dim.gif`, the Alps product-page
   dimension image; viewed): housing 4.5, bushing 7, flat 10, total 24.5
   with the 20 measured from the housing top. Confirms the existing stack.
5. Bourns **PEC11R series datasheet** (LCSC-hosted copy for C143790,
   `datasheet.lcsc.com/datasheet/pdf/d03351e7540e40c99d70acd6e8986132.pdf`;
   same document family as the bourns.com PEC11R datasheet). Text was
   extracted from the PDF (no PDF renderer in this environment); the
   dimension drawings themselves were **not viewed**, only their numeric
   labels read out of the text layer. This is the main caveat below.
6. KiCad's stock Alps footprint
   `Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm` (also what
   `hardware/pico-link-hw.kicad_pcb` uses): A/C/B pads at x=0 (2.5 pitch),
   MP slots at x=7.5, S1/S2 at x=14.5.
7. One web-search snippet (datasheets.com page for the *knurled* sibling
   PEC11R-4215K-S0024: "21.5mm length, 12.5mm width, 13.4mm height"). The
   page itself returned 403 to fetch, so this is a **secondary, unverified**
   corroboration only.

## Findings

### (a) Same EC11 family, shorter shaft: no such Alps part is verified

- Alps' own EC11E catalogue lists **only 20mm actuators** across the whole
  series (9 variants), and each of the six EC11E product pages checked says
  actuator length 20mm. LCSC's other EC11E-looking MPNs differ by detent /
  pulse / switch-travel code only, not shaft length. In `EC11E15244B2` the
  `15` is 30 detents/15 pulses, not 15mm.
- So there is **no "EC11E with a 15mm shaft"** to swap in on the evidence
  available. Alps says shorter variants may exist "on request"
  (minimum order per the product pages: 1,200 pcs Japan / 2,400 pcs export),
  which is not a JLCPCB-stock option.
- The older combined Alps catalogue (the LCSC datasheet C470754, Chinese
  edition) shows other EC11 sub-series with 20 and 25mm lengths in the part of
  the table that text-extracted; no 15mm EC11E row was seen. The full table
  did not extract, so this is partial evidence.
- Unchecked leads on JLCPCB, listed so the next pass does not redo the search:
  C128930 `K1-1532SA-01`, C17702124 `GT-EVA01AA-L1`, C1322548 `EC11G1560418`
  (Alps EC11G, an unverified series), and the EC11 clone-looking
  `EC11N1520402` (C470704, stock 278). I did not open their datasheets.

### (b) Bourns PEC11R is the realistic shorter-shaft candidate

PEC11R ordering key (datasheet, ordering table): `PEC11R-4` (PC pins,
horizontal/rear-facing terminal config), then detent option digit (0 none,
1 = 18 detents, 2 = 24 detents, 3 = 12 detents), shaft length `15/20/25/30`,
shaft style `F` metal flatted / `K` metal knurled, `S` push momentary switch
or `N` none, then pulses `0012/0018/0024`. Knurled with switch exists only in
15 and 20mm.

Shaft dimension table (datasheet labels `L`, `LB`, `F`): L=15 -> LB 5.0,
F 7.0; L=20 -> LB 7.0, F 10.0; L=25 -> LB 7.0, F 12.0. Here `L` is shaft
length from the housing top (same convention as Alps' 20), `LB` the threaded
M7x0.5 bushing length, `F` the flat length. **The column-to-label mapping
is read from text order, not from a viewed drawing.** The Alps part has
bushing 7 and flat 10 at L=20, so the PEC11R 20mm row (7 / 10) matching the
Alps numbers exactly supports the mapping.

Body height: the PEC11R side-view numeric labels include a `6.5 (.256)`
dimension alongside `LB L F`. If that is housing height above the PCB (the
analogue of the Alps `4.5`), the 15mm part's tip is 6.5 + 15 = **21.5mm** above
the PCB, which matches the unverified third-party "21.5mm" snippet (source 7)
for the sibling K part. I rate this "probable, not confirmed by a viewed
drawing": a human should open the Bourns dimension drawing and confirm 6.5.
Note it is *taller by 2mm* than the Alps housing (4.5), which eats part of the
saving from the 5mm shorter shaft.

Switch: 0.5 +/-0.3mm travel, actuation 610 +/-306 gf (about 6.0N, +/-3N), the
same class as the Alps push (6 +2.5/-2 N), so the push-stability analysis in
`2026-11-15-encoder-ec11e18244au-specs.md` carries over without change.
Rotational life 30,000 cycles, switch 20,000. Detent-torque value did not
extract from the PEC11R text; the PEC12R datasheet quotes 30 to 90 gf-cm
(about 3 to 9 mN.m), a different part, so treat torque as **unverified** for PEC11R.

Footprint risk: the PEC11R drawing labels give a 5-pin row with 5.0mm
switch-pin spacing and 4.5mm flat, but a `14.0 (.551)` dimension where the
Alps footprint has 14.5 between the encoder-pin row and the switch-pin row.
If those are the same quantity, the Bourns footprint is **0.5mm different**
and the existing KiCad footprint would not accept it. Mounting-lug slot sizes
also differ in the numbers extracted (2.6 / 1.8 +0.2/-0 vs Alps 3.2 x 2.0
pad with 2.8 x 1.5 oval drill). I did not verify; assume a new footprint is
needed until a human compares the two drawings. KiCad's stock library has no
`PEC11R` footprint (only PEC12R/PEC09/PEL12D), so it would be custom.

### (c) Low-profile / other families

- **Alps EC12E24204A2** (C351238, 1,164 units): Alps page says actuator length
  15.0mm, 24 detents / 24 pulses, "insulated" (polycarbonate) shaft, and
  mentions no push switch. Not a push-switch part on the evidence; a
  polycarbonate shaft is also a poor fit for a press-fit D-shaft knob.
  Other EC12E MPNs in stock (EC12E2430404, EC12E24404A8, ...) were not
  checked for shaft length or switch.
- **Bourns PEC12R** (12mm body): `PEC12R-4215F-S0024` (C22385080) has only 28
  units and is a "Global Sourcing" listing; `PEC12R-4120F-S0012` (C143801,
  1,387 units) is 20mm. The PEC12R dimension drawing did not text-extract,
  so body height and footprint are unknown. Not pursued.
- **Short-body encoders** (EC10E, EC09, EC05E, PEL12D...): not verified for
  push switch, shaft length or height; the push-switch requirement and the
  D-shaft knob make most of the cheap JLCPCB 9-10mm parts unlikely fits, but
  that is **unchecked**.
- No JLCPCB-stocked genuinely low-profile (shorter-than-EC11-body) encoder
  with push switch and detents was confirmed in this pass.

### Knob geometry note

In every EC11-sized option the bushing top stays around 11.5mm above the PCB
(Alps 4.5 + 7; Bourns-15mm 6.5 + 5, if 6.5 is the housing height), i.e. about
4mm proud of the 7.5mm face regardless of shaft length. The saving is entirely
in the bare shaft above the bushing: Alps 13mm, Bourns-15mm 10mm. The D-flat
length also shrinks (F 10 -> 7mm), so the knob's D-bore engagement would
drop by 3mm; worth checking against the knob's grip.

## Comparison

| Option | MPN | LCSC | JLCPCB stock (2026-11-17) | B/E | Shaft | Tip above PCB | Proud of 7.5mm face | Est. knob height | Footprint change |
|---|---|---|---|---|---|---|---|---|---|
| Current | EC11E18244AU | C202365 | 3,520 | Ext | 20mm flat D, 36 det/18 pul, push | 24.5 (verified) | 17.0 | 17.5 | none |
| Same family, 15mm | none found (Alps EC11E is 20mm only) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Bourns 15mm | PEC11R-4215F-S0024 | C143790 | 3,816 | Ext | 15mm flatted, 24 det/24 pul, push 6N | ~21.5 (6.5 unconfirmed) | ~14.0 | ~14.5 (-3.0) | likely yes (14.0 vs 14.5 row, lug slots; unverified) |
| Bourns 15mm, 18 det | PEC11R-4115F-S0018 | C19192046 | 95 (thin) | Ext | 15mm flatted, 18/18, push | ~21.5 | ~14.0 | ~14.5 | likely yes |
| Bourns 15mm knurled | PEC11R-4215K-S0024 | C7275025 | 377 | Ext | 15mm knurled (not D), 24/24, push | ~21.5 | ~14.0 | ~14.5 | likely yes; knurled shaft needs a different knob bore |
| Alps EC12E 15mm | EC12E24204A2 | C351238 | 1,164 | Ext | 15.0mm insulated, 24/24, no push found | unknown (not read) | unknown | unknown | unknown; no push switch |

If housing height turned out to be 4.5 like Alps instead of 6.5, the Bourns
15mm tip would be 19.5mm, proud 12.0, knob about 12.5mm. The 6.5 reading is
the unverified assumption that matters most.

## Recommendation

- **Category (a), same EC11 family:** none. Alps EC11E is 20mm only in its
  catalogue and on LCSC; keep EC11E18244AU unless a shorter variant is
  ordered directly from Alps at their MOQ (not a JLCPCB stock path).
- **Category (b), other family / shorter shaft:** `PEC11R-4215F-S0024`
  (C143790, 3,816 in stock, Extended, 24/24, flatted 6mm shaft, push switch
  with the same 0.5mm/~6N feel). Expected saving about 3mm of knob height
  (17.5 -> about 14.5), for a roughly 3% price difference. Before committing:
  (1) a human opens the Bourns PEC11R dimension drawing to confirm the 6.5mm
  housing height and the footprint (row spacing 14.0 vs 14.5, lug slots), then a
  custom footprint is made; (2) firmware accepts 24 detents/24 pulses
  (1 pulse per detent) versus 36/18; (3) the knob's D-bore gets a shorter flat
  (F 7mm vs 10mm). This would be a PCB footprint change plus a knob change, so
  it needs its own beads (not filed here; the orchestrator decides).
- **Low-profile encoder (category c):** nothing verified; do not pursue
  without a datasheet-level check of a specific short-body push-switch part.
  The 3mm saving of the Bourns part is the best verified-in-part lever; going
  lower means also lowering the bushing (face depth) or recessing the knob
  skirt around the 4mm of bushing that stands proud of the face.

## Not verified

- Bourns PEC11R housing height 6.5mm (label read from PDF text, drawing not
  viewed; third-party 21.5mm snippet only).
- Bourns footprint vs the Alps footprint (14.0 vs 14.5, lug slots).
- PEC11R detent torque.
- Alps availability of 15mm EC11E variants other than "on request".
- Whether EC12E/PEC12R/other short-body parts have a push switch or what their
  heights are.
- All stock figures are a single 2026-11-17 reading and move daily.

## Informs

`pilink-8hy`. Feeds a possible follow-up: a PCB-footprint and knob bead for
the Bourns part, gated on a human reading the Bourns drawing. Does not change
any current hardware decision.
