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
bores, top-edge BOOTSEL/RESET pinholes, and a reserved (not yet cut)
antenna zone for the sibling bead `pilink-8hx.4`. Not rendered — OpenSCAD
isn't installed here (see above); every dimension in the file is cited
in a comment next to it, sourced from:

- `.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md` and
  `docs/plans/2026-11-15-product-layout-proposal.md` section 6c (face
  size, body thickness/depth stack, knob position rule);
- `hardware/README.md`'s "PCB layout (pilink-7el.12)" placement table
  (the real as-placed board coordinates everything else is derived
  from — knob/encoder centre, A/B/X/Y diamond, SW101/SW102 pinhole
  positions, the display panel-shadow rectangle, the ESP32/antenna-end
  edge);
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

**Open items, not resolved in this bead** (also in the file's own
footer comment): the encoder bushing diameter is an unconfirmed 7mm
assumption; the board-to-face vertical mapping inherits
`hardware/README.md`'s own flagged, unconfirmed assumption about where
the 6mm board/face height slack sits; the display window's derived
centre lands about 3.9mm off the face's exact horizontal centre
(expected, but unresolved against the original "center the window"
design rule); the shell is modeled flat, not with the ADR's real
~15-degree lean or a final corner/edge styling pass; and front-to-back
shell fastener bosses aren't modeled yet, pending `pilink-8hx.1`'s own
mating geometry. All of this needs a human with OpenSCAD — ideally
once `pilink-8hx.1` (back shell) also exists — per `pilink-8hx.5`.
