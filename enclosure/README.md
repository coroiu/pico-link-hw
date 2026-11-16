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
