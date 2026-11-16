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
