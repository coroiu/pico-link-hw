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

**Update (`pilink-3ym`, 2026-11-16): re-checked against `pilink-hdl`
(PR #60).** U201 moved to the back of the board and the A/B/X/Y diamond
was restored to centre (102, 25), so `front_shell.scad`'s four button
bores are back at board (102,17) / (94,25) / (110,25) / (102,33) (the
pilink-2yw-era (102,34) figures in the paragraphs above are history). Knob
(16,25) and the SW101/SW102 pinholes (42,2.7)/(52,2.7) are unchanged;
coordinates cross-checked against `hardware/pico-link-hw.kicad_pcb`.
U201 is no longer on the front, so the old "U201 vs diamond" proximity
note is obsolete. J501's FPC fold (courtyard bottom y=31.53) is not
modelled in this file. Not rendered (no OpenSCAD).

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
for the test print: check whether it is needed at all. Cap must be dropped
in from inside the shell cavity before the two shells are joined (an
assembly-order note, not modeled).

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
verification) now depends on `pilink-0ty` too. The bores' missing
entry chamfer (original bead text's "chamfered bores") was filed as
`pilink-ci0` and is now added in `front_shell.scad` (0.4mm x 45-degree
on the outer face only; see the `pilink-ci0` update below).

**Update (`pilink-ci0`): bore entry chamfer, fit math unchanged.**
`front_shell.scad`'s `button_cutouts()` now adds a 0.4mm x 45-degree
chamfer on the *outer* face (Z=0..0.4) of each bore: mouth Ø9.2mm,
straight Ø8.4mm bore from Z=0.4 on. The flange (Ø9.0, Z >= FACE_T = 2.0)
and `panel_ledge()` (Z >= FACE_T) both sit on the inner side, and the
display pocket is cut from the inner face (Z >= 1.2), so none overlap the
chamfer in Z; bore Ø8.4, flange Ø9.0 and the 0.3mm worst-case
flange-to-ledge margin at X are unchanged. Adjacent chamfer mouths
(diagonal pitch 11.31mm) stay 11.31 - 9.2 = 2.11mm apart. Not rendered
(OpenSCAD not installed).

**Update (`pilink-3ym`): flange-vs-ledge math re-checked, unchanged.**
The `panel_ledge()` clearance at the X button depends only on X button
x=94 (ledge edge at board x=89 -> 5.0mm, flange radius 4.5mm, 0.5mm
nominal / 0.3mm worst case) and the 8mm diamond pitch (11.31mm diagonal,
~2.3mm flange-to-flange). Both are identical for the restored diamond
(x unchanged, pitch unchanged, and board y 17..33 still lies inside the
ledge's y span 2..50). Only a stale `(94,34)` comment in
`button_plunger.scad` was updated.

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

### U201 back-side relief and J401 raise (`pilink-3ym`)

`pilink-hdl` (PR #60) put U201 on B.Cu at board (99, 11.6) and raised
J401 from (59, 45.5) to (59, 37). `back_shell.scad` now carries both.
Not rendered (no OpenSCAD); arithmetic checked in Python.

**J401.** `J401_FACE = board_to_face(59, 37)` = face (61, 15), plug
centreline Qface 15.0 (was 6.5). Boss pad: `usbc_boss_pad_q0/q1` = 9.0 /
21.0 (the `USBC_BOSS_RISE*tan(15)` = 0.54mm clamp is now inactive); cutout
Q 12.5..17.5. Lateral X is unchanged, so the leg clearance echoes (~31.5mm
each side) hold. The four PCB mounting holes did not move (re-read from
the board: (10,44), (112,6), (112,44), (59,4)).

**U201 relief (not a 0.2mm boss).** Envelope above the host PCB back
surface: module 3.2mm; mated U.FL-LP-066 plug 0.8 (module PCB top,
INFERRED, measure it) + 2.5 (Hirose max) = 3.3mm; plus 0.5mm own margin =
3.8mm, versus `REAR_CLEARANCE` 3.0mm. Pocket floor at bz = 5.0 - 3.8 =
1.2mm, i.e. 0.8mm cut into the 2.0mm back wall, with a 0.8mm raised pad on
the outside (J401-boss style) so the wall stays 2.0mm. Pocket footprint:
module body (F.Fab x 90..108, y 2.0..21.2, +0.3mm) out to the board's top
edge, so the U.FL end and the cable's bend/exit are inside it: face X
91.7..110.3, Q 30.5..52.0 (18.6 x 21.5mm). Pad: face X 90.2..111.8, Q
29.0..53.5. The courtyard-based range from the bead (x 89.22..108.78)
would clip the H2 mounting boss (left edge face X 110.5), so the module
body is used instead. H2 keeps the standard 7.0mm boss (`pilink-i72`; `pilink-3ym` had trimmed
it to 6.0mm): the pocket edge (face X 110.3) is 0.2mm short of the boss's
left edge (110.5), so they never overlap, and the pocket only cuts the
back wall below the boss (bz 1.2..2.0), not the boss itself. The pad overlaps the
right leg boss base (x=101, Q=40) -- a plain union, leg geometry unchanged.
**U.FL receptacle position (verified, `pilink-bl2`).** Not in the KiCad
footprint; read off Espressif's ESP32-WROOM-32E/32UE datasheet v2.1,
Figure 11 (32UE top view; Figure 12 gives the receptacle itself,
2.6 x 2.6mm body, 1.25+-0.15mm tall): centre **3.07mm in from the
antenna-end edge and 3.27mm in from the long edge on the pin 25-38 side**,
beside the antenna notch, not at module-centre X. On U201's B.Cu placement
that is board (93.27, 5.07) = face (95.27, Q 46.9); the earlier assumed
(99, 5.0) was 5.73mm off in X (Y was fine). The pocket (x 89.7..108.3) still
contains it, 3.57mm from the pocket's left edge, and does not depend on it.
The datasheet drawing also gives the module PCB as 0.8mm thick, which
confirms the 0.8 used in the relief envelope. Not obtained from a primary
drawing: the plug's cable-exit direction and the plug cable-centre height
(no Hirose U.FL-LP-066 drawing could be opened; the plug mates on a round
socket so the exit direction is picked at assembly) and the coax minimum
bend radius. Bend check: the 3.3mm plug-top and 3.8mm envelope stand, so
the vertical constraint (cable centre bz <= ~2.9) is unchanged and still
unverified. In-plane, the U.FL is 5.07mm from the board top edge (room
for a >=4.5mm bend toward the mount) and 3.27mm from the module's left
edge / 3.57mm from the pocket's left wall (toward the spool, the first
bend starts at the plug; a 4.5-5mm bend lands beyond the pocket wall, in
the 3.0mm cavity, so the cable must have come down to fit under 3.0mm above the PCB by then). Spool
capacity is unaffected; the U.FL-to-spool run got shorter (about 12mm of
free run to the spool's lug circle, was about 17mm).

### Pigtail slack stowage (`pilink-phg`)

The antenna pigtail is ~240mm per the part number
KH-FPC2.4G-1.13IPEX-240 and the "CABLE RF-1.13-L=240 MM" row of Kinghelm's
datasheet table (LCSC `C4943394`), against an ~18-30mm run from U201's
back-side U.FL to the top-wall mount: ~210mm of excess. It can't be
trimmed (no crimp tooling). **Caution (`pilink-bl2`):** the same Kinghelm
datasheet page's drawing dimensions the cable as "100+-2MM", contradicting
its own table and part number; the real length is unresolved until a unit
is measured. The spool is sized for the 240mm worst case; if the cable is
~100mm it is simply under-filled (excess ~70mm, about 1.5 turns).

**Shorter part: not swapped.** Facts as listed on LCSC (not independently
verified): C709378 (`-100`) lists no cable length, element size, gain or
stock; C709379 (`-100-3239`) lists a 49mm length; C709381 (`KH-FPC4G-...-6417`)
is a 4G (cellular) antenna with 2dBi listed, so not a 2.4GHz candidate;
AIWF026 (C49242188, 100mm cable) is 0.02dB over the 2.33dBi cert-safe
ceiling. None of the shorter parts has confirmed cable length, 2.4GHz band,
size and in-ceiling gain together, so the 240mm part with a coil stays. BOM
unchanged (the antenna now has a BOM row, `C4943394`, added in PR #75). If a
verified short part is found, it removes the spool.

**Stowage.** B.Cu is nearly empty left of U201 and the cavity behind the
PCB is 3.0mm deep, so a flat spiral is wound on a printed post there
(`pigtail_spool()` in `back_shell.scad`): O10mm post (first turn centreline
R 5.57 >= the 5mm coax minimum bend radius, TE UMCC 5mm / Data Alliance
4.5mm), three O2 lugs at R 12, centre board (73,18) = face (75,34). Both
cable ends are fixed, so the inner end crosses back over the turns: the
stack is 2 x 1.13 = 2.26mm, under the 2.6mm post/lug height and the 3.0mm
cavity. Capacity: 4 turns = 182mm gross, ~160mm after crossover and
entry/exit; a 5th turn (245.8mm gross) is tight and not counted on. So
~160mm of the ~210mm excess is coiled and ~50mm stays a loose >=5mm-radius
loop along the route (not yet designed). The spool is 4.7mm short of the
U201 relief's left edge and clear of H4 (59,4). Per the PR #64 review, the
plug-side bend fits inside the relief only if the cable centre starts at
bz <= ~2.9 against the relief's top wall.

**Not verified:** no render (no OpenSCAD); J401's real body outline vs the
spool (assumed >= ~15mm away); actual plug cable-exit direction and mated
height; whether the cable can really be routed spool -> top-wall mount
without kinking at the board edge; the 240mm cable length itself.

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
further `FACE_T + FRONT_CAVITY = 7.5mm` forward **along bz
(depth)**). Correcting that stand-in — a known, already-flagged
simplification, not something this bead's own scope allows fixing
(`back_shell.scad`'s geometry isn't touched here) — would shift the whole
base-strip + leg assembly forward by `7.5mm x cos(15°) = 7.24mm` in world
Z (not 7.5mm — the shift is along the *local*, pre-rotation bz depth
axis, and world Z is the rotated projection of it), away from the back wall and the
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
zero-droop, straight-line simplification — now just given thickness). The
axis points along -bz, i.e. 15° *below horizontal*, heading backward. The
cylinder's lower edge is the axis offset by `r = D/2` perpendicular to
it, which sits `r x cos(15°)` below the axis in world Y at the same `s`.

**Result.** Two strip positions matter, because the one in
`back_shell.scad` is a flagged stand-in (see Step 1's last paragraph):

- **Placeholder** (as built: back edge world Z = -8.125mm). The boot's
  lower edge touches the strip's back-edge corner once its *radius*
  exceeds the corner's 2.465mm perpendicular clearance from the axis, so
  the strip-vs-table crossover is **D = 4.93mm** (not ~5.7mm, an earlier
  draft's error). Every boot in the 5.0-6.5mm range hits the strip.
- **Design-decision position** (back edge Z = -0.88mm, the position the
  ADR's front-edge reference implies). That edge is 2.25mm *in front of*
  the plug's mating face (Z = -3.13mm), so the strip is never under the
  cable, and no boot in the range can hit it. The **table** is the only
  obstacle.

"Along" is measured along the axis from the connector's mating face;
"horizontal" is the table-plane distance from that face (the axis points
15 degrees below horizontal, so horizontal is a little less than along).
Strip-hit distance is where the boot's lower edge reaches strip-top
height (Y = 2.0mm); table-hit is where it reaches Y = 0.

| Boot `D` | Placeholder strip (Z=-8.125) | Design-decision strip (Z=-0.88) |
|---|---|---|
| 5.0mm | **strip**, ~5.7mm along | **table**, ~13.4mm along (~12.3 horiz.) |
| 5.5mm | **strip**, ~4.8mm along | **table**, ~12.5mm along (~11.4 horiz.) |
| 6.0mm | **strip**, ~3.8mm along | **table**, ~11.6mm along (~10.4 horiz.) |
| 6.3mm (Anker 515) | **strip**, ~3.3mm along | **table**, ~11.0mm along (~9.8 horiz.) |
| 6.5mm | **strip**, ~2.9mm along | **table**, ~10.6mm along (~9.4 horiz.) |

Below D = 4.93mm the placeholder strip is also cleared and the table is
again the first contact (e.g. D = 4.5mm: ~14.4mm along), but that is
outside the 5.0-6.5mm range used here. Method: boot = 2D offset of the
axis by `r = D/2`, perpendicular to it. With axis direction
`(dy, dz) = (-sin15, -cos15)` from the face `(5.890, -3.131)`, the boot's
lower edge sits `r cos15` below the axis, so table contact is at
`s = (5.890 - r cos15) / sin15`. This simplified method ignores the small
sideways (`r sin15`) shift of the lowest point, which is accounted for
only in the "horiz." column. Both strip positions follow from the file's
own numbers; no extra modelling was needed for the second.

**Which strip position ships.** The design-decision one (Z = -0.88) is
the intended geometry; the placeholder exists only because the front
shell's real base profile did not exist when `back_shell.scad` was
authored. If the placeholder ships unchanged, the strip is the first
obstacle for every boot at or above ~4.93mm and a relief notch helps
with *that* contact only.

**Table contact does not depend on a strip notch.** At the
design-decision strip position (or with a notch cut anywhere), a 6.3mm
boot's rigid end still reaches the table about 11mm along the axis
(~9.8mm horizontal). A notch changes nothing about this; only geometry
that moves the connector relative to the table does.

- **How short would the rigid end have to be?** The rigid moulded end
  (plug shell + overmold, before the flexible jacket) must end before
  the table-contact distance: **under ~11mm for the 6.3mm Anker boot**
  (under ~10.6mm at 6.5mm, ~13.4mm at 5.0mm), measured from the
  receptacle's mating face. The Anker page gives no head length, so this
  is unsourced; a real cable's overmold length is the deciding unknown.
- **Option (a), raise the body / lengthen the feet.** For a 6.3mm boot
  with a rigid end of length `L` along the axis, the lift needed is
  `L sin15 + r cos15 - 5.89`: ~0 for L <= 11mm, ~1.0mm for L = 15mm,
  ~2.3mm for L = 20mm, ~3.6mm for L = 25mm, ~4.9mm for L = 30mm. (The
  strip is 2.0mm tall and the connector face is 5.89mm up, so the body
  would have to sit on feet/strip that add this much height.)
- **Option (b), move J401 higher on the PCB** stays open: it raises the
  face height by ~cos15 (0.97mm) per mm moved, without touching the
  enclosure's resting height, and nothing here argues against it.

**Boot vs. the cutout/boss itself.** Separately from table/strip
clearance, `back_shell.scad:229-230`'s `USBC_CUTOUT_W/H = 10.0 x 5.0mm`
tunnel runs from the boss's outer face (`bz=-2.0`, `USBC_BOSS_RISE`) to
past the receptacle's own mating face (`bz=-1.5`), a 0.5mm-deep recess
the plug has to clear to fully seat. A boot wider than 10mm or thicker
than 5mm can't pass through that tunnel at all. The file's own comment at
`back_shell.scad:223-228` already flags this as open. What matters is how
much bare, un-overmolded metal shell is still *outside the receptacle*
when the plug is fully mated, and whether that exceeds the 0.5mm recess
(it is much less than the plug's total bare length, which is partly
inside the receptacle). That figure isn't sourced for any real cable
here, so this is open, not settled, and is in `pilink-q03`'s scope.

**Conclusion: not resolved, and no longer pointing at the strip alone.**
Table contact at ~10-13mm along the axis is the primary finding for the
intended strip position, and it is the bead's original (a)-vs-(b)
question: it only goes away if the cable's rigid end is shorter than
~11mm (6.3mm boot), or the face is raised (option (a): body/feet lift,
estimate above) or J401 is moved higher (option (b)). Neither is chosen
here and no PCB re-placement is ruled out. The placeholder strip adds a
second, earlier contact (~3-6mm along) that only exists while the
placeholder position ships. This bead is investigation only;
`back_shell.scad` is intentionally not touched. `pilink-q03` carries the
physical check: with a printed prototype and a real cable, check table
contact first, the strip only if the placeholder strip position ships,
and the cutout-tunnel entry above.

### USB-C cable-vs-table clearance, recomputed for Qface 15 (`pilink-3ym`)

The `pilink-8ry` figures above are for the old Qface 6.5 and are kept as
history. Same method and boot range (5.0-6.5mm, Anker 515 6.3mm as the
sourced point; boot = 2D offset of the mating axis by D/2, axis 15 deg below
horizontal heading -bz, mating face at bz = -1.5, `horiz` = along x cos15 -
r x sin15 as before). Mating face world (Y, Z) = (14.10, -5.33) (was
(5.89, -3.13)); clearance over the strip top at the face 12.10mm (was 3.89).

| Boot D | Table contact, along axis (horiz.) | Was (Qface 6.5) |
|---|---|---|
| 5.0mm | ~45.2mm (~43.0) | ~13.4 (~12.3) |
| 5.5mm | ~44.2mm (~42.0) | ~12.5 (~11.4) |
| 6.0mm | ~43.3mm (~41.0) | ~11.6 (~10.4) |
| 6.3mm (Anker 515) | ~42.7mm (~40.4) | ~11.0 (~9.8) |
| 6.5mm | ~42.4mm (~40.1) | ~10.6 (~9.4) |

Zero-thickness line reaches the table ~54.5mm along (was 22.8). The
placeholder strip (back edge Z = -8.125, 2.89mm along the axis, rechecked) is now
cleared by 10.97mm perpendicular (was 2.465), so a boot would have to be
~21.9mm thick to touch it; the strip is no longer an obstacle at either
position. Option (a) lift needed for a rigid end `L`: negative (no lift
needed) for L up to 30mm at every D in the range (e.g. 6.3mm boot, L=30:
-3.3mm). **Result: table contact now needs a rigid moulded end longer than
~40mm along the axis, which no real USB-C overmold approaches, so the
table/strip concern is effectively retired by the J401 raise.** The
cutout-tunnel entry question (boot vs. the 10 x 5mm cutout) is unchanged
and stays in `pilink-q03`. `pilink-q03`'s description was updated with
this result.

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
  SW101's pinhole channel. U201 is now on the back of the board (`pilink-hdl`), so the cable run
  from its U.FL to the mount is only ~18-30mm against the part's ~240mm
  pigtail (240mm per its table, 100mm per its drawing, see `pilink-bl2`); the ~210mm excess is stowed per the pigtail
  stowage section above. Board-to-face coordinate mapping is settled
  (`face_x = board_x + 2`, `Qface = 52 - board_y`), shared with the front
  and back shells.
- **Display/ground clearance guidance is NOT met — real RF trade-off, not
  pending:** a second review round found the governing number here is the
  face-Y distance (not a Z gap, as an earlier revision wrongly framed it),
  and it *is* derivable from this file's own constants: the element sits
  roughly **2mm from the board's top edge and roughly 7mm from the display
  panel's frame** (both estimates; the board-to-face mapping itself is
  settled), against general adhesive-FPC-antenna practice
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

## Encoder knob (`knob.scad`, `pilink-0ty`)

- **What it is:** a printed knob for SW303 (Alps EC11E18244AU, 6mm D-shaft),
  covering the encoder part of `pilink-8hx.3`'s acceptance criteria. Not
  rendered or fit-checked (OpenSCAD isn't installed here); arithmetic was
  checked in Python.
- **Geometry (knob-local, z=0 = underside):** Ø18mm x 17.5mm tall (ADR's
  ~18mm cap); underside sits 1.0mm above the outer face (> 0.5mm push travel
  + 0.3mm tolerance); a Ø8.5 x 4.0mm counterbore clears the ~4mm-proud
  bushing and the face's Ø8.5 shaft hole; round bore z=4..6.3 (non-flat shaft
  section) then a blind D-bore z=6.3..16 matching the 10mm flat; the shaft tip
  bottoms in the bore (no tip clearance, so the knob can't creep down under
  ~6N presses); 12mm engagement, 1.5mm top wall; 0.10mm radial FDM
  clearance on the D-bore (friction fit). The D-bore starts 0.3mm above the
  nominal flat start (z=6.3, `D_FLAT_MARGIN`) in case the real flat is short.
  Grip: 30 knurl grooves (Ø1.2, 0.5mm deep) on the rim, 1.2mm top fillet, and
  a shallow Ø11 x 0.8mm thumb dish so the ~6N press does not slip off.
  Print upright (dish up), no supports.
- **Sources:** shaft/bushing heights from the encoder research finding
  (24.5 - 7.5 = 17mm; 11.5 - 7.5 = 4mm); Ø18 from the ADR/proposal 6c; face
  hole from `front_shell.scad`. Only `knob.scad` is new; `front_shell.scad`
  is unchanged. The Ø8.5 face hole is fully covered by the Ø18 skirt (4.75mm
  overlap per side), so no face change is needed.
- **Shaft dims** are from Alps' EC11E catalogue Drawing No. 2 (EC11E18244AU):
  Ø6, D-flat across-flats 4.5 (+0/-0.1), flat 10mm long from the tip, 24.5mm
  overall. **Unconfirmed:** bushing OD 7mm (not on the drawing). The 0.10mm
  radial clearance plus shaft tolerance may run loose; check on the test
  print.
- **Open:** the knob is tall (17.5mm) because the shaft is 17mm proud; trimming
  the shaft would allow a shorter knob but is a product call, not made here.

### Re-derived for a back-side U201 (`pilink-3ym`, supersedes `pilink-adt` / PR #54)

U201's U.FL is now on the BACK of the board, so the earlier "cable run to
U201 at face X ~16" and any "U201 under the mount" wording above are stale.
Changes in `antenna_mount.scad` (not rendered, arithmetic in Python):

- **Pigtail exit** moved from 6mm in from the land's left end to 6mm in
  from its right end: face X 99.55. `pilink-bl2` then verified the U.FL
  at face X 95.27 (Qface 46.9), so the lateral run is 4.28mm, not the 1.45mm
  first computed against the assumed (101, 47); the exit was not moved.
- **Route and length:** plug -> along the back cavity toward the board's
  top edge (5mm, inside the U201 relief) -> over the edge through the 2mm
  top-slack gap (2mm) -> into the mount (<= ~10mm of front-to-back travel,
  the top-wall cavity depth) + 4.28mm lateral = ~21mm, ~30mm with bend
  slack. The pigtail (~240mm per Kinghelm's table and part number, possibly 100mm per its drawing; unresolved, see `pilink-bl2`) leaves ~210mm to stow; where is not
  designed yet (new bead).
- **Clearances:** SW101/SW102 pinholes (X 44/54) >45mm from the cable;
  restored diamond (courtyard y 13.58..36.43, front side) 8.6mm in Y and on
  the opposite board face; H2 boss >=11mm (cable at X <= 99.55, `pilink-bl2`).
- **`pilink-58z` RF numbers:** the element and mount X span did not move,
  but this file's Y mapping assumed the board bottom-flush (top edge 6mm
  below the face top); the shells use Qface = 52 - by (4mm). Corrected,
  the element is **~2mm (was ~4) from the board top edge and ~7mm (was ~9)
  from the display panel frame**, against the same ~46mm guidance. The
  PCB change itself does not alter them; the correction is the new part.
  U201's metal shield is now behind the board, not beside the diamond; its
  RF effect is unquantified.
- **Coax bend radius (sourced, review follow-up):** no Hirose figure found;
  a TE UMCC datasheet for U.FL-compatible 1.13mm assemblies gives 5mm
  minimum single bend, and Data Alliance's table lists 4.5mm. The pigtail
  turns from running up the back cavity (Q) to heading forward (bz) at the
  top wall, with only ~2mm of Qface between the board edge (Q 52) and the
  top wall's inner surface (Q 54). A 4.5-5mm radius does not fit in that
  2mm gap; the turn has to be made earlier, inside the U201 relief (3.8mm
  deep) or the cable stowed with a gentler route. Tracked in `pilink-phg`.
