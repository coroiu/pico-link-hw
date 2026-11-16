# Enclosure

OpenSCAD source for the 3D-printed case goes here: two shells (top/bottom),
button plungers, internal antenna mount, rear USB-C cutout.

Not started yet — see "Enclosure" and "Deliverables" in
[`../docs/plans/2026-11-13-custom-hardware-design.md`](../docs/plans/2026-11-13-custom-hardware-design.md).

OpenSCAD isn't available in the agent environment this repo was scaffolded
in. A parametric `.scad` file can be authored as code, but rendering and
fit-checking need OpenSCAD installed on a machine that has it.

`cube.scad` is a trivial seed file for the `preview/` docker-compose
service — it proves the OpenSCAD -> STL -> GLB export pipeline end-to-end
before the real enclosure exists. Delete it once the real enclosure from
pilink-8hx lands; the preview pipeline picks up whatever `*.scad` file it
finds here.

## Front shell (`front_shell.scad`, `pilink-8hx.2`)

Parametric front shell (face plate + perimeter skirt) for the upright
desk-clock body — display window, knob/encoder opening, A/B/X/Y button
bores, top-edge BOOTSEL/RESET pinholes, and a debug-only visual marker
for the antenna zone whose real geometry is built separately in the
sibling bead `pilink-8hx.4`'s `antenna_mount.scad` (merged). Not
rendered — OpenSCAD isn't installed here (see above); every dimension
in the file is cited in a comment next to it, sourced from:

- `.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md` and
  `docs/plans/2026-11-15-product-layout-proposal.md` section 6c (face
  size, body thickness/depth stack, knob position rule);
- `hardware/README.md`'s "PCB layout (pilink-7el.12)" placement table
  (the real as-placed board coordinates everything else is derived
  from — knob/encoder centre, A/B/X/Y diamond, SW101/SW102 pinhole
  positions, the display panel-shadow rectangle);
- `enclosure/antenna_mount.scad` (`pilink-8hx.4`, merged) for the real
  antenna element/mount span, which `front_shell.scad`'s own debug-only
  antenna-zone marker is positioned to roughly match (not the stale
  ESP32 U.FL-pad edge the marker cited before `pilink-8hx.4` landed);
- `.planning/decisions/2026-11-15-display-panel-crystalfontz-cfaf240320a0.md`
  and the display FPC/off-centre finding
  (`.research/findings/2026-11-15-display-fpc-contact-side.md`) for the
  window size and its offset from the panel's own centre;
- `.research/findings/2026-11-15-encoder-ec11e18244au-specs.md` for the
  encoder's corrected (not the stale ~7.5mm) body height above the PCB;
- `.planning/decisions/2026-11-15-enclosure-aesthetic-direction.md` for
  the minimalist/flush/hidden-fastener styling intent (not yet modeled
  as a styling pass — see the file's own "Open items" footer).

Key numbers (all re-derivable from the file's own named constants):
face 122 x 56mm, 2.0mm wall/face thickness, 7.5mm outer-face-to-PCB
depth; display window 48.96 x 36.72mm (active area), recessed 1.2mm
below the outer face; knob/encoder opening with an 8.5mm through-hole
(assumed 7mm bushing + clearance — **not confirmed**, flagged in the
file) plus an 18mm x 1.2mm inner-face countersink; four Ø8.4mm button
bores on the A/B/X/Y diamond; two Ø1.5mm top-edge pinholes at x=44/54mm
aligned onto SW101/SW102.

The board-to-face vertical mapping is settled, not an open item:
`Qface = 52 - by` (`FACE_H` 56mm minus `WALL_T` 2mm minus `TOP_SLACK_Y`
2mm, i.e. 52 = `FACE_H - WALL_T - TOP_SLACK_Y`), derived from the real
inner-cavity height rather than assumed, and cross-confirmed against
`back_shell.scad`'s own independently-derived `board_to_face()`
formula — both shells land on the identical mapping. See
`front_shell.scad`'s `board_to_y()` comment for the full derivation.

**Open items, not resolved in this bead** (also in the file's own
footer comment): the encoder bushing diameter is an unconfirmed 7mm
assumption; the display window's derived centre lands about 3.9mm off
the face's exact horizontal centre
(expected, but unresolved against the original "center the window"
design rule); the shell is modeled flat, not with the ADR's real
~15-degree lean or a final corner/edge styling pass; and front-to-back
shell fastener bosses aren't modeled yet, pending `pilink-8hx.1`'s own
mating geometry. All of this needs a human with OpenSCAD — ideally
once `pilink-8hx.1` (back shell) also exists — per `pilink-8hx.5`.

## A/B/X/Y button plunger/cap (`button_plunger.scad`, pilink-8hx.3)

The part that sits IN the four Ø8.4mm button bores `front_shell.scad`
(`pilink-8hx.2`, merged) already cuts for A/B/X/Y -- not the bores
themselves, which are out of scope here. Not rendered -- OpenSCAD isn't
installed here (see above); every dimension cites its source in the
file's own comments.

**The real switch:** SW305-SW308 are C&K `PTS645SK50SMTR92LFS` (LCSC
`C221872`), confirmed from `hardware/BOM.md`'s BOM table. Per C&K's
own PTS645 ordering key, decoded against this exact part number in
[`.research/findings/2026-11-15-encoder-ec11e18244au-specs.md`](../.research/findings/2026-11-15-encoder-ec11e18244au-specs.md)'s
"Lower-force PTS645 mitigation options" section, the trailing `50`
encodes a **5.0mm overall height above the PCB** at rest -- this
file's `SWITCH_HEIGHT_ABOVE_PCB`. Switch **travel (0.25mm)** and the
actuator's own contact-button diameter (assumed 3.5mm) are NOT
confirmed against this exact SKU's own dimensioned drawing in this
repo's research -- both flagged as this file's assumptions, using
generic published PTS645-family figures.

**Depth budget, genuinely tight:** combining `front_shell.scad`'s own
`FACE_T` (2.0mm plate) and `FRONT_SHELL_DEPTH` (7.5mm outer-face-to-PCB)
with the switch's 5.0mm height above the PCB leaves only **0.5mm**
of spare depth between the plate's inner face and the switch
actuator's resting top -- not a bug, but a deliberate consequence of
the proposal's own stack-up (section 6c: "5.5mm to the PCB (5.0mm
switches...)" = 0.5mm spare). This file's working clearance (0.1mm)
and stem (0.4mm) split that same 0.5mm on-axis budget -- flagged as
the single highest-risk dimension in this file for a real FDM print,
more so than the general "not rendered" caveat that applies everywhere
in this directory. See the file's own "Open items" footer for the
documented mitigation if a real print shows this doesn't hold up.

**Cap/bore fit:** cap Ø8.0mm (matching `front_shell.scad`'s
`BUTTON_CAP_DIA`) inside the existing Ø8.4mm bore -- 0.2mm/side
clearance, within the bead's own suggested 0.15-0.2mm/side FDM
clearance range. Retention is a flange *ring* wider than the bore
(Ø9.0mm = `BORE_DIA` + 0.6mm, 0.3mm radial overlap each side), which
cannot pass out through the bore. It only stops *outward* travel;
inward travel is stopped by the switch, and before the back shell is
fitted nothing stops the cap falling into the cavity. Ledge clearance
at the X button is 0.5mm nominal / 0.3mm worst case (incl. the 0.2mm
radial bore play); diagonal gap to the next flange is ~2.3mm nominal.
The 0.4mm stem is now just a short boss inside a deeper ring -- flagged
for the test print: check whether it is needed at all. Cap must be dropped in from inside the shell cavity before the two
shells are joined (an assembly-order note, not modeled).

**Review fixes (PR #56, round 2):** the first version used a Ø11mm
solid flange. That both intruded ~0.5mm into `front_shell.scad`'s
`panel_ledge()` at the X button's position (only 5.0mm of clearance
there, board x 94 vs. the ledge's edge at board x 89) and left only
0.31mm between adjacent flanges on the diamond's 11.31mm diagonal
pitch -- less than the caps' own 0.4mm of bore play, so adjacent
flanges could touch/bind. `FLANGE_DIA` is now `BORE_DIA` + 0.6mm
(9.0mm as of round 3), clearing both. The flange is also now a 1.2mm-thick ring with
a Ø4.5mm relief pocket over the actuator, instead of a 0.2mm
single-layer disc: off-axis (beside the actuator, over the switch's
own housing) there's more real clearance than directly over the
actuator -- the switch housing sits an assumed 1.5mm lower there, per
the review -- so the ring's thickness draws on that off-axis budget
(2.0mm) instead of the tight 0.5mm on-axis one, while the stem passes
through the pocket to reach the actuator using the full 0.5mm on-axis
budget itself (minus only the 0.1mm working clearance).

**Not covered by this file:** the encoder's (SW303, EC11E18244AU) own
knob/shaft treatment, which `pilink-8hx.3`'s acceptance criteria also
names -- filed as a separate follow-up bead (`pilink-0ty`) rather than
addressed here; `pilink-8hx.3` stays open (not closed on this PR
alone) until `pilink-0ty` also lands, and `pilink-8hx.5` (fit
verification) now depends on `pilink-0ty` too. A straight-cut
(non-chamfered) bore in the already-merged `front_shell.scad` is also
flagged as a discrepancy against the original bead text's "chamfered
bores" phrasing -- filed as its own follow-up (`pilink-ci0`) per code
review rather than fixed here (out of this file's scope, different
file's established geometry).

## Back shell + rear legs (`back_shell.scad`, pilink-8hx.1)

Covers the back half of the enclosure: PCB-mounting bosses (heat-set
inserts), the 3mm clearance cavity behind the PCB for the encoder's
through-hole leads, the rear USB-C cutout (with a local raised boss, since
the chosen connector is taller than the bare back cavity), a horizontal
base strip with feet pockets, and the fixed two-leg A-frame that screws to
this shell. The front shell (face, display window, button/knob openings)
is `pilink-8hx.2`'s separate file; the antenna mount is `pilink-8hx.4`'s.

Every dimension is pulled from, and cites, one of: the upright
desk-clock-form-factor ADR
(`../.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md`),
the product layout proposal's section 6c
(`../docs/plans/2026-11-15-product-layout-proposal.md`), the real placed
PCB coordinates (`../hardware/README.md`'s "PCB layout" section), the
vertical USB-C receptacle finding
(`../.research/findings/2026-11-15-vertical-usb-c-receptacle-selection.md`),
and the enclosure aesthetic ADR
(`../.planning/decisions/2026-11-15-enclosure-aesthetic-direction.md`). The
file's own header comment explains its coordinate frames and lists a few
assumptions this bead had to make where no source doc pins a number down
yet (notably: the face/board vertical-offset mapping it adopts, and
treating this shell's own open rim as a stand-in "front edge" reference
for leg/base-strip placement, since the front shell's real base profile
doesn't exist yet).

**Not verified**: OpenSCAD isn't installed in the agent environment this
was authored in, so this file has never been rendered or dimension-checked
— that's `pilink-8hx.5`'s job on a machine that has OpenSCAD. It does
include `echo()` statements with the clearance numbers this bead's own
NOTE asked for (whether the rear USB-C port and its mating plug clear the
two rear legs), computed analytically rather than rendered; see the
file's own comments for the numbers and reasoning.

## `antenna_mount.scad` (pilink-8hx.4)

Internal mount for the adhesive U.FL 2.4GHz antenna, for the top wall of
the upright desk-clock body
([`.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md`](../.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md)).
Not rendered or fit-checked — OpenSCAD still isn't installed in this
environment (see the note above); every dimension in the file cites its
source (hardware/README.md's PCB placement table, the ADR, or
[`.research/findings/2026-11-15-ufl-antenna-selection.md`](../.research/findings/2026-11-15-ufl-antenna-selection.md))
or is marked as this file's own assumption.

- **Part:** Kinghelm KH-FPC2.4G-1.13IPEX-240 (LCSC `C4943394`), the primary
  selected in `pilink-8wx` — 45.8 x 6.5mm adhesive-backed FPC monopole,
  Ø1.13mm IPEX/U.FL-class pigtail. (The AIWF026 alternate from the same
  finding was not chosen: its in-band gain sits fractionally over
  Espressif's cert-safe ceiling.)
- **What's modeled:** a flat adhesive land sized to the element plus a 1mm
  assembly margin (47.8 x 8.5mm), a raised locating lip around three sides,
  a short cable channel + strain-relief clip stub toward the cavity below,
  and non-manifold (`%`) preview markers for the element itself and the
  clearance-guidance keepout zone from the research finding. It is a mount
  feature only, not a full top-wall shell — `pilink-8hx.1`/`pilink-8hx.2`
  own the real top-wall geometry this feature gets instantiated onto; the
  file's own `demo_assembly()` stand-in slab is for local preview only and
  must not be unioned into either shell.
- **Position:** face-local X 57.75-105.55mm, clear of both SW101 (X=44mm)
  and SW102 (X=54mm) top-edge pinholes by construction (3mm margin past
  each pinhole's own ~1.5mm channel diameter). A left-of-SW101 placement
  doesn't fit (only 38.25mm of clear width there, less than the 45.8mm
  element) — fixed per a code-reviewer's NOT APPROVED verdict on the first
  version (PR #48), which had the element physically colliding with
  SW101's pinhole channel. The resulting cable run to U201's U.FL connector
  (face-local X-center ~16mm) is ~48mm, well within the part's ~240mm
  (inferred) pigtail. Board-to-face coordinate mapping (board centered
  left-right, bottom-flush in the face) is the same unconfirmed convention
  hardware/README.md's own placement table already flags as pending
  `pilink-8hx.1`/`.2` confirmation — carried here unchanged rather than
  inventing a different one.
- **Display/ground clearance guidance is NOT met — real RF trade-off, not
  pending:** a second review round found the governing number here is the
  face-Y distance (not a Z gap, as an earlier revision wrongly framed it),
  and it *is* derivable from this file's own constants: the element sits
  roughly **4mm from the board's top edge and roughly 9mm from the display
  panel's frame** (both estimates, same unconfirmed board-to-face mapping
  as the X-axis numbers), against general adhesive-FPC-antenna practice
  cited in the research finding (not a figure from any datasheet — the
  32UE's own datasheet carries no such keepout, and no antenna datasheet
  in this repo states one either) of keeping metal/ground clear within
  roughly the element's own length (~46mm). With only ~11mm of face above
  the panel in total, **no position
  in the top wall can meet that guidance** — this is a real RF-performance
  risk (reduced range/link reliability), not a modeling gap. It's tracked
  as its own product decision in `pilink-58z` (P1, discovered from this
  bead); see that bead for the options (accept + empirical range test,
  flip the element's radiating end, move to the rear wall, trim PCB copper
  near the top edge, or grow the enclosure) rather than re-litigated here.
  The mount's X position is unchanged by this — that's `pilink-58z`'s call.
  Separately, the mount's own X range still overlaps the display-panel
  shadow's face-local X range (30-89mm) by 31.25mm, unavoidably, for the
  same reason the left-of-SW101 placement didn't fit.
- **Mount depth vs. available wall-cavity depth — tight, not fully
  resolved:** the same review found the land/lip/channel/clip stack-up
  modeled at ~19mm deep against a top-wall inner cavity of only ~10mm
  (front-to-back, per the back-shell ADR numbers). Shortening the lip width,
  the default cable-channel stub length, and the strain-relief clip's own
  thickness brings this down to **~11mm — still ~1mm (~10%) over the
  ~10mm budget**, because the land+lip alone (~9mm) already consumes
  nearly the whole depth before any room is left for the channel/clip. Not
  silently forced to fit: flagged plainly as a tight, not-fully-resolved
  constraint for `pilink-8hx.1`/`.2` to re-check once real 3D wall geometry
  exists, possibly by routing the strain-relief clip off this straight-line
  axis instead.
