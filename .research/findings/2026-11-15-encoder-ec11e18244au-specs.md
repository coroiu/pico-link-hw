# Encoder EC11E18244AU: confirmed detent torque, push force, body height (`pilink-g8a`)

## Question

The upright desk-clock form factor ADR
(`.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md`) and the
layout proposal it's based on
(`docs/plans/2026-11-15-product-layout-proposal.md`, section 6c) used three
numbers for the encoder SW303 (Alps Alpine **EC11E18244AU**) that were not
confirmed against Alps' own data for this exact part number:

- Detent torque: "EC11E series 10±7 mN·m", used as 17 mN·m worst case in the
  knob-turning stability margin (single strut vs. two-leg frame).
- Push-switch operating force: "6 (+2.5/-2) N for 0.5mm-travel variants",
  used in the press-stability finding (knob press slides the body).
- Body height above PCB: "~7mm class, one distributor-hosted drawing showed
  '7.5 max', couldn't read it cleanly" — an input to the front-cavity depth
  at the knob location.

This spike confirms all three from Alps' own sources for EC11E18244AU
specifically, and checks LCSC for lower-force PTS645 variants as a
documented mitigation option for `pilink-8hx.6`'s physical press-stability
test.

## Sources

1. Alps Alpine's own product detail page for this exact part number:
   `tech.alpsalpine.com/e/products/detail/EC11E18244AU/` (fetched
   2026-11-15).
2. Alps Alpine's official **EC11 "11mm Size Metal Shaft Type" encoder
   catalogue PDF** (the same document Digikey, Avnet and other distributors
   mirror; this copy fetched via Digikey's hosted mirror of the Alps PDF,
   content verified as the genuine Alps catalogue by its `ALPSALPINE`
   branding on every page and cross-match with source 1). **EC11E18244AU**
   appears by name in the EC11E product-line table on p.261 (drawing No. 5),
   and the switch-spec and dimension tables that follow apply to that
   drawing number.
3. C&K's own **PTS645 series datasheet** (`ckswitches.com`, mirrored by
   LCSC), for the actuation-force ordering key, to decode PTS645 part-number
   suffixes.
4. LCSC/JLCPCB live component search (`jlcpcb-search` MCP), for stock and
   pricing on lower-force PTS645 variants, checked 2026-11-15.

## Findings

### Detent torque and push force: the placeholder numbers were already correct

Alps' own EC11E18244AU product page and the EC11 catalogue's product-line
table (p.261) both give, for this exact part number:

- **Detent torque: 10 ±7 mN·m** (range 3–17 mN·m). This is the literal row
  for `EC11E18244AU` (vertical, flat shaft, 20mm length, 36 detents/18
  pulses, push switch with 0.5mm travel) in the catalogue's product-line
  table — not a generic "EC11E series" figure read across variants. The ADR
  and proposal's "17 mN·m worst case" is this range's upper bound and needs
  no change.
- **Push-switch operating force: 6 (+2.5/−2) N at 0.5mm travel.** Confirmed
  both on the product page and in the catalogue's switch-specification
  table (p.270, "EC11E/EC11N/EC111 Series", travel 0.5±0.3mm row) and the
  cross-series summary table (p.253). No change needed.

So the detent-torque and push-force inputs to the ADR's stability math were
right already; they just hadn't been traced to Alps' own data for this
specific PN before. `pilink-g8a`'s value here is closing that citation gap,
not correcting a number.

### Body height above PCB: 7.5mm max, now from Alps' own drawing

The catalogue's dimensioned mechanical drawing for drawing No. 5 ("EC11E
Vertical with push-on switch, travel 0.5mm/1.5mm" — the style that covers
EC11E18244AU) gives **7.5mm max** as the body/bushing height above the PCB
mounting surface, separate from the 20mm shaft length above that. This
matches the number the layout proposal had already assumed from an
unreadable distributor drawing (`docs/plans/2026-11-15-product-layout-proposal.md`
line 69 and its "Conflict with the aesthetic ADR" paragraph, which already
treats the encoder body height as equal to the ~7.5mm face-to-PCB cavity
depth at the knob location). That assumption is now confirmed directly from
Alps' own catalogue, not a guess — no numeric change, same conclusion
(proud knob, ~12.5mm of shaft above the face).

Also confirmed from the same catalogue, not previously recorded: **push-pull
(axial) strength 100N**, operating life 15,000 cycles for the encoder and
20,000 for the integrated switch, and the part's drawing number is 5 (useful
if anyone needs to re-derive other dimensions from the catalogue PDF later).

### Lower-force PTS645 mitigation options, with live LCSC/JLCPCB stock

C&K's PTS645 ordering key encodes actuation force in one letter (checked
against the current BOM part `PTS645SK50SMTR92LFS`, SW305–SW308): `L` =
130gf (1.3N), `M` = 160gf (1.6N), `H` = 200gf (2.0N), `K` = 260gf (2.6N,
**the current part**). The digits after the force letter (`50`) are the
5.0mm actuator height, matching the current footprint/courtyard exactly —
these are drop-in alternatives, same package, same PCB footprint.

| LCSC PN | Part number | Force | Stock (checked 2026-11-15) | Price (1+) |
|---|---|---|---|---|
| C221872 | PTS645SK50SMTR92LFS | 2.6N (current part) | 8,950 | $0.34 |
| C221881 | PTS645SM50SMTR92LFS | **1.6N** (the bead's target) | **44** | $0.54 |
| C221877 | PTS645SL50SMTR92LFS | 1.3N (lower still) | **4,043** | $0.29 |

Both are "Extended" parts (JLCPCB assembly surcharge applies, same as the
current K-force part). The ~1.6N part the bead asked about (`C221881`,
`PTS645SM50SMTR92LFS`) exists and matches the footprint, but **its live
stock is only 44 units** at the time of this check — JLCPCB stock numbers
move daily and this is too thin to treat as a dependable mitigation without
rechecking at order time. The 1.3N part (`C221877`,
`PTS645SL50SMTR92LFS`) has much healthier stock (4,043 units) and is an
available fallback-of-the-fallback if 1.6N parts dry up, at the cost of an
even lower (and unverified against the press-force finding) force margin.

Per the proposal's own framing (section 6c, mitigation list item (d)),
either of these is "a partial help only" against the ~2.5N (buttons) and
~5.8N (knob press, different switch) sliding-force problem — a 1.6N or
1.3N button lowers the *button*-press force but doesn't touch the knob
press (that's the encoder's own push-switch, EC11E18244AU, confirmed above
at 6N nominal, not a PTS645). Swapping A/B/X/Y to a lower-force PTS645 does
not by itself fix the knob-press instability.

## Conclusion / what changes

- **No stability-math numbers change.** Detent torque (10±7 mN·m, 17 mN·m
  worst case) and push force (6 +2.5/−2 N) were already correct for
  EC11E18244AU specifically; this finding adds the citation. Body height
  (7.5mm) was already assumed correctly; this finding removes the "not
  confirmed" caveat.
- **Documentation updated** (confirmation status only, not values) in:
  - `.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md`
    (Rationale section, knob-turning torque paragraph).
  - `docs/plans/2026-11-15-product-layout-proposal.md` (encoder spec table,
    row "Body height above PCB"; and the stability-inputs list under
    section 6c).
- **New mitigation data point for `pilink-8hx.6`** (the physical press-test,
  not run here): if that test shows the A/B/X/Y buttons need a lower-force
  part, `PTS645SM50SMTR92LFS` (LCSC C221881, 1.6N, same footprint) is the
  direct swap, but **recheck its stock before committing** — 44 units is
  thin. `PTS645SL50SMTR92LFS` (LCSC C221877, 1.3N, same footprint, 4,043
  units in stock) is the better-stocked fallback if 1.6N proves
  insufficient or unavailable at order time. Neither addresses the
  knob-press instability, which is a separate (encoder) switch.

## Informs

`pilink-g8a` (this spike). Feeds `pilink-8hx` (OpenSCAD enclosure epic) as a
confirmed body-height input, and `pilink-8hx.6` (physical press-stability
test, not run here) as a documented PTS645 fallback option if default parts
fail that test.
