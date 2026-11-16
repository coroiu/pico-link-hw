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

### USB-C cable-vs-table clearance (`pilink-8ry`)

PR #52's review flagged, but left unresolved (out of that bead's own
scoping call), a real concern: J401 sits low on the board (board-local
(59, 45.5), only ~4.5mm from the board's bottom edge) — well short of the
product-layout proposal's "~15mm up" intent (section 6c) — and the
back-shell's own base strip, directly below it, might force a mated
cable's molded boot to hit the table or the strip before it can exit
cleanly. This bead investigated the *current* merged geometry (not the
placement question itself) analytically, since OpenSCAD still isn't
available here.

**Numbers used** (all read directly from the current `back_shell.scad`,
not re-derived): `USBC_QFACE = 6.5mm` (J401's position in the shell's own
"height up the face" convention — already reflects the `board_to_face()`
Y-mapping fix merged in `pilink-8hx.1` (PR #52), not in this bead, +2mm
over the original, pre-fix figure); connector height above the PCB back surface
`USBC_HEIGHT_ABOVE_PCB = 6.5mm` (so its outer mating face actually
overhangs 1.5mm *past* the back wall's own outer surface, at local
`bz = -1.5mm`, not `bz = 0` — the connector height exceeds the bare
5.0mm cavity by design, per the USB-C finding); base strip `BASE_STRIP_DEPTH
= 14.5mm`, `BASE_STRIP_T = 2.0mm` (its table-facing thickness/top-surface
height); shell lean `LEAN_DEG = 15`.

### Step 1: idealized zero-thickness line (first pass, numbers corrected)

Projecting the connector's own mating axis outward (the direction a
plugged-in cable's body would run, straight-line/worst-case, ignoring any
droop, modeled with **zero thickness** — just the axis itself) through the
shell's `rotate([-LEAN_DEG,0,0])` world transform:

- The connector's outer mating face sits at world `(Y, Z) = (5.89mm,
  -3.13mm)` relative to the file's own table-level datum (Y=0).
- Clearance above the base strip's top surface (Y=2.0mm) **right at the
  connector face** is **3.89mm**.
- That clearance *shrinks* as the straight-line path runs outward (down
  and back, per the 15-degree lean), reaching a **vertical minimum of
  ~2.55mm** about **5.2mm out from the connector's own mating face** —
  exactly the point where the path crosses the base strip's own back edge
  (world Z=-8.12mm, using the strip's `front_edge_z` stand-in reference).
  The *true* clearance a zero-thickness line leaves at that pinch point,
  measured perpendicular to the cable's own axis (the direction a round
  cable boot's surface would actually approach that corner from) rather
  than straight up, is smaller: **2.465mm**, not ~2.5mm/2.55mm (2.552mm is
  the vertical gap; 2.552mm x cos(15°) = 2.465mm is the perpendicular
  one — correction from a code-reviewer's NOT APPROVED verdict on this
  bead's first PR). Beyond the strip's back edge the strip no longer
  exists underneath the path at all; the zero-thickness line itself
  reaches table level (Y=0) about 22.8mm out from the connector face.
- **No point along this idealized, zero-thickness line dips below the
  strip or the table** — a real improvement over the stale number quoted
  in `pilink-8ry`'s own description (~2.4mm *into* collision), which
  predates the `board_to_face()` Y-mapping fix (`pilink-8hx.1`, +2mm) and
  the USB-C boss-pad clamp fix already merged here.

This zero-thickness result is **not, by itself, a basis for any
conclusion about real cables** — see Step 2.

The base strip's own Z position is keyed off this file's documented
`front_edge_z` approximation (`BACK_SHELL_DEPTH = 6.6mm`, *not* the real
front-shell edge, which the file's own `BODY_T` stack-up says sits a
further `FACE_T + FRONT_CAVITY = 7.5mm` forward **along the local Q
axis**). Correcting that stand-in — a known, already-flagged
simplification, not something this bead's own scope allows fixing
(`back_shell.scad`'s geometry isn't touched here) — would shift the whole
base-strip + leg assembly forward by `7.5mm x cos(15°) = 7.24mm` in world
Z (not 7.5mm — the shift is along the *local*, pre-rotation axis, and
world Z is the rotated projection of it), away from the back wall and the
connector, moving the strip's back edge from Z=-8.12mm to about
**Z=-0.88mm** (not -0.6mm as an earlier draft of this section had it;
correction from the same review). This stand-in-correction argument only
ever applied to the **strip-crossing** pinch point above — it says
nothing about table clearance, since the table (world Y=0) is a fixed
datum the `front_edge_z` stand-in doesn't move. See Step 2 for why that
distinction now matters.

### Step 2: redone with a real cable boot, not a zero-thickness line

A real mated USB-C cable is not a line — right at the plug, a molded
"boot"/overmold (strain relief + shielding) adds real thickness around
the bare connector shell before the flexible cable jacket begins. This is
the check the bead's own description asked for ("plug dimensions, typical
cable boot size, actual achievable clearance") and the first version of
this PR skipped — flagged as the review's blocking finding.

**Sourced boot thickness.** No cable is chosen for this product, and the
USB Type-C Cable and Connector Specification doesn't fix a boot
envelope (it's a manufacturer choice, not a compliance dimension), so
there's no single "correct" number. One real, sourced data point: Anker's
own FAQ for the Anker 515 USB-C-to-USB-C cable (model A8487) states its
"USB-C head cover is 6.3mm thick" and 12.15mm wide
([source](https://service.anker.com/article-description/Anker-515-USB-C-to-USB-C-cable-FAQ)).
That's used below as the centre of a **5.0-6.5mm conservative range**
(bracketing the sourced 6.3mm figure), not a survey of the market.

**Model.** The boot is modeled as a rigid cylinder of diameter `D`
centred on the same idealized mating axis used in Step 1 (same
zero-droop, straight-line simplification — now just given thickness). At
a point `s` mm out along that axis, the lowest point on the cylinder's
surface sits `D/2 x cos(15°)` below the axis itself (the perpendicular
offset of a circle's lowest point on a line tilted 15° from vertical,
derived directly, not assumed — see the git history of this file's
companion analysis for the derivation if it needs rechecking).

**Result — and the governing obstacle changes, not just the distance:**

| Boot diameter `D` | Governing obstacle | Contact point |
|---|---|---|
| 5.0mm | table (strip is already behind it) | ~13.4mm out |
| 5.5mm | table | ~12.5mm out |
| ~5.7mm | **crossover** — see below | ~4-8mm out |
| 6.0mm | **base strip itself** | ~3.8mm out |
| 6.3mm (sourced, Anker 515) | **base strip itself** | ~3.3mm out |
| 6.5mm | **base strip itself** | ~2.9mm out |

For boots thinner than about 5.7mm diameter, the boot's underside dips
below the strip's top height (Y=2.0mm) only *after* it has already
passed the strip's back edge in Z — so it clears the strip (consistent
with Step 1's zero-thickness pinch point) and the open table beyond is
what it eventually touches, at roughly 12.5-16mm out depending on exact
diameter — much sooner than the zero-thickness line's 22.8mm, but still
past the strip.

For boots at or above about 5.7mm diameter — which includes the one
sourced real product above (6.3mm) — the boot's underside drops below
the strip's own top surface **while it is still over the strip**, not
past it: the governing collision is with the **raised base strip itself**,
only about **3-4mm out from the connector's own mating face**. This is a
materially worse result than either this PR's original "~22.8mm,
comfortable margin" claim or the "~10mm out" ballpark the review used to
flag the finding — both of those numbers are table-contact distances;
neither accounts for the boot hitting the strip itself first, which this
corrected model shows happens for boots at or above the sourced real
diameter.

The Step 1 "front_edge_z stand-in is conservative, so real clearance is
probably better" argument does **not** rescue this: it only shifts the
*strip's* position (potentially out of the way, forward, away from the
connector) once the real front-shell edge exists — it doesn't change
where the boot's underside drops below Y=2.0mm relative to the
connector, so a thinner boot might still clear a shifted strip, but a
thick one crossing the strip at only ~3mm out is not obviously rescued by
a strip that may end up ~7mm further forward; that interaction isn't
modeled here and would need the real front-shell geometry to check.

**Boot vs. the cutout/boss itself (review finding #2).** Separately from
table/strip clearance, `back_shell.scad:229-230`'s `USBC_CUTOUT_W/H =
10.0 x 5.0mm` tunnel runs from the boss's outer face (`bz=-2.0`,
`USBC_BOSS_RISE`) to past the receptacle's own mating face (`bz=-1.5`) —
a 0.5mm-deep recess the plug has to clear to fully seat. A boot wider
than 10mm or thicker than 5mm can't pass through that tunnel at all. This
file's own comment at `back_shell.scad:223-228` already flags this as
open. Reasoning, not a confirmed resolution: USB-C plugs expose several
millimetres of bare, un-overmolded metal shell beyond the mating contacts
before the boot/overmold begins (standard mechanical convention for
depth-of-insertion and compliance-test-fixture engagement, not a specific
datasheet figure found for this bead) — almost certainly more than this
tunnel's 0.5mm depth, so the overmold most likely never has to enter the
tunnel at all; it would rest against the boss's outer face once the bare
shell bottoms out in the receptacle. This is plausible, not verified, and
is added to `pilink-q03`'s scope below rather than asserted as settled.

**Conclusion: do not treat this as resolved/"comfortable margin."** The
original "~22.8mm out, comfortable margin" claim does not hold for any
realistic cable — once the boot has real thickness, the contact point
moves to somewhere between ~3mm and ~16mm out depending on boot diameter,
and for boots at or above the one sourced real diameter checked here
(6.3mm), the governing obstacle is the **base strip itself**, not the
table, at only ~3mm out. This is a real, elevated-probability physical
interference for many real cables at the current geometry — not a
confirmed collision (no cable is chosen, and boot shapes/lengths vary
enough that a thin-boot cable could still clear), but no longer a case
that supports "accept as comfortable margin" either.

This bead's own scope is investigation, not a geometry fix, and nothing
in this analysis — zero-thickness or real-boot alike — points to J401's
*placement* (option (b), a PCB re-route) as the problem; the issue is the
back-shell base-strip geometry built around a confirmed-good connector
position, which is option (a)'s territory. `pilink-q03` (discovered from
`pilink-8ry`) is updated to carry this forward as the decisive check: once
a back-shell prototype and a real cable both exist (both a physical
action only a human can take), verify (1) whether the mated cable's boot
actually foul the strip or the table at J401's current position, now
checking the strip explicitly, not just the table, and (2) whether the
boot can physically enter the 10x5mm cutout/boss tunnel per the reasoning
above. Given how little margin this analysis finds for any boot at or
above the sourced real diameter, a small local relief/notch cut into the
base strip under J401 (pilink-q03's own stated fallback, bounded, not a
full redesign) looks like the *likely* needed fix, not just a remote
possibility — but that's `pilink-q03`'s call once real parts exist, not
resolved here, and `back_shell.scad` itself is intentionally not touched
by this docs-only bead.

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
