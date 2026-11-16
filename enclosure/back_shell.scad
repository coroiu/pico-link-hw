// Pico Link enclosure -- back shell + rear legs (pilink-8hx.1)
//
// Scope of THIS file: the back shell (PCB-mounting bosses, the 3mm
// clearance cavity behind the PCB, the rear USB-C cutout + local boss, the
// horizontal base strip with feet, and the two leg-mounting bosses) plus
// the fixed two-leg A-frame itself. The front shell (face, display window,
// button/knob openings -- pilink-8hx.2) and the antenna mount
// (pilink-8hx.4) are separate beads/files worked in parallel; this file
// does not model them and only touches enclosure/README.md besides itself.
//
// *** OpenSCAD is NOT installed in this environment (confirmed in
// AGENTS.md) -- this file has never been opened, rendered, or
// dimension-checked. Every numeric constant below cites where it comes
// from; render + fit-check is pilink-8hx.5's job, on a machine that has
// OpenSCAD. The echo() statements at the bottom print the handful of
// numbers this bead's own NOTE asked to verify (USB-C vs. leg clearance)
// so a human can see them even via a headless `openscad -o /dev/null
// back_shell.scad` run, without a GUI. ***
//
// ---------------------------------------------------------------------
// Coordinate frames used in this file
// ---------------------------------------------------------------------
// 1. "Local" frame (back_shell_local() and everything it contains):
//      X = Pface  -- lateral position across the face, 0 at the face's
//                     left edge, FACE_W (122mm) at its right edge.
//      Y = Qface  -- position up the face, 0 at the face's bottom edge,
//                     FACE_H (56mm) at its top edge. This is exactly the
//                     "N mm up the face" quantity the ADR and
//                     hardware/README.md use.
//      Z = bz     -- depth, 0 at the back wall's OUTER (world-facing)
//                     surface, increasing toward the open front rim
//                     where this shell meets the front shell / the PCB's
//                     own front surface (bz = BACK_SHELL_DEPTH there).
//    This frame is NOT tilted -- it's the shell "unfolded" flat, which is
//    the natural frame for anything that has to line up with the PCB
//    (bosses, the USB-C cutout) since the PCB itself is flat.
// 2. "World" frame (base_strip(), leg(), and the top-level assembly):
//      X unchanged (lateral position is unaffected by the body's lean).
//      Y = height above an assumed table-level datum.
//      Z = how far forward (+) / back (-) of that same datum.
//    The two frames are related by the ADR's 15 degree lean, applied as
//    rotate([-LEAN_DEG, 0, 0]) to the local frame. The datum (world
//    Y=0, Z=0) is THIS file's own choice: the back wall's own
//    bottom-outer corner (local Qface=0, bz=0). That point is NOT
//    necessarily table height in the real assembled product -- the real
//    table contact comes from the base strip and the leg feet, whose own
//    exact height depends on the front shell's base profile, which
//    doesn't exist yet (pilink-8hx.2). Flagged wherever it matters below.
//
// ---------------------------------------------------------------------
// Source documents (every dimension below cites one of these)
// ---------------------------------------------------------------------
//   ADR   = .planning/decisions/2026-11-15-upright-desk-clock-form-factor.md
//   PROP  = docs/plans/2026-11-15-product-layout-proposal.md, section 6c
//   PCB   = hardware/README.md, "PCB layout (pilink-7el.12 ...)" section
//           (board-local coordinates, origin top-left, X right, Y down)
//   USBC  = .research/findings/2026-11-15-vertical-usb-c-receptacle-selection.md
//   ENC   = .research/findings/2026-11-15-encoder-ec11e18244au-specs.md
//   AES   = .planning/decisions/2026-11-15-enclosure-aesthetic-direction.md

// =====================================================================
// Constants
// =====================================================================

// --- Overall envelope (ADR "Decision", PROP 6c "Dimensions") ---
FACE_W      = 122.0;  // face width, ADR: "about 122 W x 56 H mm"
FACE_H      = 56.0;   // face height, same source
LEAN_DEG    = 15;      // ADR: body leans back ~15 deg (face ~75 deg to table)

// --- Board (PCB section of hardware/README.md, pilink-7el.12) ---
BOARD_W     = 118.0;  // Edge.Cuts: 118 x 50mm board
BOARD_H     = 50.0;

MARGIN_X    = (FACE_W - BOARD_W) / 2;  // = 2.0mm each side -- also reused
                                        // below as the generic side-wall
                                        // thickness, since it matches the
                                        // back wall's own 2.0mm (PROP 6c
                                        // thickness breakdown) and gives a
                                        // single consistent "2mm wall"
                                        // figure across the shell.
WALL_T      = MARGIN_X;  // = 2.0mm

// Lateral running clearance between the board's edge and the hollow
// cavity's inner wall (back_shell_shell() below) -- PR #52 review
// finding #1 (part 2): as originally written the 118mm board sat in a
// 118mm-wide cavity with zero clearance. Sibling front_shell.scad (#50)
// maps board X with board_to_x(bx) = WALL + bx -- also zero clearance,
// but that file only positions openings (window, knob/button holes),
// not a physical pocket the board has to be dropped into. This file's
// hollow cavity IS such a pocket, so zero clearance is a real assembly
// problem here even though front_shell.scad has no equivalent figure to
// match. 0.4mm/side is this file's own reasonable default (not a cited
// source figure): a common loose running-fit allowance for a rigid PCB
// dropped into a printed cavity, comfortably inside typical FDM
// dimensional tolerance (+/-0.1-0.2mm) stacked on both mating parts.
// Only widens the cavity cut below -- board_to_face() (hole/connector
// positions) is unaffected, since those must stay keyed to the real PCB
// coordinates regardless of cavity clearance.
BOARD_CLEARANCE_X = 0.4;

// Face<->board Y mapping -- REVISED per PR #52 review finding #1 (NOT
// APPROVED on 31c5f16): the original formula (Qface = BOARD_H - by) put
// the board's bottom edge flush with the face's bottom edge, leaving no
// room for this shell's own WALL_T (2mm) bottom wall -- the PCB's own
// slab (bz 5.0..6.6) overlapped the wall that should sit behind it.
// Sibling PR #50 (front_shell.scad)'s board_to_y() instead derives a
// slack margin from the real 52mm inner-cavity height (FACE_H -
// 2*WALL_T) minus the board's own 50mm height, and puts that 2mm of
// slack above the board (board bottom edge sits WALL_T, not 0, above
// the face's own bottom edge). This file now uses that same derivation,
// so the two shells agree -- they previously disagreed by exactly 2mm.
// (The old comment's "knob (16,31) -> ~19mm confirms the mapping"
// argument is dropped: the review correctly called it circular, since
// place.py generated 31 from this same unchecked formula to begin with,
// so the match proved nothing either way.)
TOP_SLACK_Y = (FACE_H - 2*WALL_T) - BOARD_H;  // = 2.0mm

function board_to_face(bx, by) = [bx + MARGIN_X, FACE_H - (WALL_T + TOP_SLACK_Y + by)];

// --- Body thickness stack-up (PROP 6c: "about 14mm. That's face 2.0,
// 5.5mm to the PCB (5.0 switches, 3.3 panel stack, J501 ~2mm), PCB 1.6,
// 3mm behind the PCB for the encoder's leads, and a 2.0mm back wall.")
// Only the last three terms belong to the BACK shell; the first two
// (face wall + front cavity) are pilink-8hx.2's (front shell) to build.
FACE_T          = 2.0;   // front shell's own face wall -- not built here,
FRONT_CAVITY    = 5.5;   // ...nor the front cavity -- both only used here
                           // for the BODY_T sanity check below and for
                           // the base-strip/leg "front edge" reference
                           // further down, so the two shells can be
                           // designed to meet correctly later.
PCB_T           = 1.6;   // PCB thickness, matches hardware/README.md
REAR_CLEARANCE  = 3.0;   // ADR: "3mm clearance behind the PCB for the
                           // encoder's through-hole leads"
BACK_WALL_T     = 2.0;   // ADR: "a 2.0mm back wall"

BACK_SHELL_DEPTH = PCB_T + REAR_CLEARANCE + BACK_WALL_T;  // = 6.6mm --
                    // this file's own depth, back-wall-outer (bz=0) to
                    // open front rim (bz=BACK_SHELL_DEPTH), where the PCB
                    // front surface / front shell's rim meets it.
BODY_T = FACE_T + FRONT_CAVITY + PCB_T + REAR_CLEARANCE + BACK_WALL_T;
// Sanity check against the ADR's own "about 14mm": BODY_T = 14.1mm. OK.

CORNER_R = 3.0;  // style choice (AES: "deliberate but not aggressive
                  // corner radii"), not a dimensioned source figure.

// =====================================================================
// PCB mounting bosses (heat-set inserts carrying the PCB parallel to the
// face, per the bead description)
// =====================================================================
// Positions: hardware/README.md, "Mounting holes for back-shell bosses"
// row -- 4 M2 holes at board-local (10,44), (112,6), (112,44), (59,4).
PCB_MOUNT_HOLES_BOARD = [[10,44], [112,6], [112,44], [59,4]];
PCB_MOUNT_HOLES_FACE  = [ for (p = PCB_MOUNT_HOLES_BOARD) board_to_face(p[0], p[1]) ];
// -> [[12,8], [114,46], [114,8], [61,48]] in (Pface, Qface) -- updated
// per the board_to_face() mapping fix above (each +2 in Qface vs. the
// pre-fix values).
//
// H4 (board-local (59,4), -> face (61,48)) known gap: hardware/README.md
// flags this hole's screw HEAD (driven in from the FRONT, through the
// PCB, per pcb_mount_insert_pockets()'s own comment below) as coming
// within ~0.9mm of the display panel's top edge / bezel on the FRONT
// side. That's front_shell.scad's (pilink-8hx.2) geometry to check, not
// this file's -- this file only models the BACK-side boss/insert the
// screw lands in, not the front-side bezel it passes under. Left as a
// known gap here, not resolved in this PR.

// Heat-set insert sizing: no bead/finding pins an exact insert down for
// this project, so this is this file's own reasonable-default choice,
// NOT a cited source figure -- flagged for the human assembling the real
// part to confirm against whatever insert is actually bought. Common M2
// brass heat-set inserts for 3D printing run ~2.8-3.5mm OD x 3-6mm long
// (e.g. Bambu Lab's M2x3.5x4 insert); this file uses the middle of that
// range.
INSERT_OD   = 3.5;
INSERT_LEN  = 4.0;
BOSS_OD     = 7.0;   // insert OD + ~1.75mm wall each side

// =====================================================================
// Rear USB-C opening (J401, vertical-mount receptacle on the PCB back)
// =====================================================================
// Position: hardware/README.md PCB table + the pilink-5g8 ADR
// verification section -- board-local (59, 45.5), B.Cu, rot 0.
J401_FACE = board_to_face(59, 45.5);  // -> (61, 6.5) in (Pface, Qface) --
                                        // updated per the board_to_face()
                                        // mapping fix above (+2 in Qface)
USBC_PFACE = J401_FACE[0];
USBC_QFACE = J401_FACE[1];

// Connector geometry, all from USBC finding (TYPE-C-31-D-09, LCSC
// C7463258), datasheet-confirmed there:
USBC_SHELL_W          = 9.0;  // shell outer body, long axis
USBC_SHELL_H          = 3.2;  // shell outer body, short axis
USBC_PAD_EXTENT_W     = 8.6;  // copper/pad+peg extent (PCB-side only;
USBC_PAD_EXTENT_H     = 5.3;  // not needed for the enclosure cutout, kept
                               // here only so the two "~9x~5" figures in
                               // the finding aren't conflated)
USBC_HEIGHT_ABOVE_PCB = 6.5;  // component height above the PCB back
                               // surface -- this is the number that
                               // drives the local boss below.

// Footprint orientation, VERIFIED against hardware/pico-link-hw.kicad_pcb
// (PR #52 review minor item): J401's footprint instance is
// `(at 159 145.5)` with no rotation field -- KiCad omits the angle when
// it's 0, so this is rot 0, matching this file's own J401_FACE comment
// above ("rot 0") and hardware/README.md's placement table, not a
// 270 deg rotation. The footprint's own pad geometry (A1..A12 signal pads span
// local X -3.85..+3.85 = 7.70mm, local Y only +/-0.675mm) confirms the
// long axis (matching the ~9.0mm shell width) is local X, which maps
// directly onto board/face X at rot 0. Being mounted on the back
// (B.Cu) mirrors X (KiCad auto-mirrors back-layer footprints) but a
// mirror doesn't swap which axis is long -- so "long axis horizontal"
// is a confirmed fact here, not an open assumption.

// The bare back cavity here is only BACK_WALL_T + REAR_CLEARANCE = 5.0mm
// deep (PCB back surface to back wall outer face), but the connector is
// 6.5mm tall -- it overhangs by 1.5mm. USBC finding's own recommendation:
// "add a ~1.5-2mm boss around the connector cutout". This file uses the
// upper end of that range for a bit of margin.
USBC_BOSS_RISE = 2.0;  // boss_outer_face sits 2.0mm beyond the back
                        // wall's nominal outer surface; leaves the bare
                        // connector (which needs 1.5mm) 0.5mm of margin.

// Clear opening through the back wall / boss: sized to pass the
// connector's own shell (9.0 x 3.2mm) with margin. NOTE: this does NOT
// account for the mated USB-C PLUG's own molded cable boot, whose width
// varies a lot by cable and isn't confirmed against any datasheet in
// this project -- flagged as an open item, not resolved here. The figure
// below is this file's own reasonable allowance, not a cited spec.
USBC_CUTOUT_W   = 10.0;
USBC_CUTOUT_H   = 5.0;
USBC_BOSS_PAD_W = 18.0;  // raised-boss footprint around the cutout
USBC_BOSS_PAD_H = 12.0;  // (generous, own choice -- not a cited figure)

// =====================================================================
// Rear legs / A-frame mounting bosses
// =====================================================================
// ADR: "fixed (non-hinged) printed two-leg A-frame (legs ~+/-40mm from
// centre, feet ~45-50mm behind the front edge) screwed to back-shell
// bosses ~40mm up the face ... hidden fasteners (feet cover screw
// heads)."
LEG_OFFSET      = 40;   // +/- from face centre (FACE_W/2), lateral
LEG_MOUNT_Q     = 40;   // "~40mm up the face" -- directly a Qface value
LEG_FOOT_SETBACK = 47;  // midpoint of the ADR's "45-50mm behind the
                         // front edge" range

// Cross-check against the PCB: leg lateral positions (Pface 21, 101) map
// back to board-local X = 19 and 99 (board_to_face inverse: x = Pface -
// MARGIN_X), exactly matching the figure hardware/README.md's own ADR
// verification section already used ("legs at x 19/99", since board
// centre/J401 is x=59, 59+/-40=19/99). Confirms this file's leg
// positions agree with the already-placed board, not a fresh guess.
LEG_PFACE_LEFT  = FACE_W/2 - LEG_OFFSET;   // = 21
LEG_PFACE_RIGHT = FACE_W/2 + LEG_OFFSET;   // = 101

// "Hidden fasteners (feet cover screw heads)" -- this file's reading:
// each leg is attached to its back-shell mounting boss by a single long
// screw driven in from the FOOT end (through a channel bored the length
// of the leg strut) into a heat-set insert at the boss, ~40mm up the
// face. The rubber foot pad then glues over the screw's access hole at
// the foot, hiding it -- the only construction that actually makes a
// foot "cover" a screw head for THIS leg's own fastener (the mount point
// and the foot are ~45mm apart, so a foot pad at the mount point itself
// isn't geometrically sensible). Flagged as this bead's own design
// choice, not spelled out verbatim in the ADR.
LEG_MOUNT_BOSS_LEN = 6.0;  // boss protrudes this far behind the back
                            // wall's outer surface -- own choice.

// ---------------------------------------------------------------------
// Leg axis geometry (world frame) -- PR #52 review findings #2, #3, #6.
// Computed here, early, so both the back-shell boss/insert modules
// below (which need the tilt, in LOCAL frame) and the leg() module
// further down (which needs the mount/foot points, in WORLD frame)
// read from one single derivation instead of two that can disagree.
// ---------------------------------------------------------------------
// This file's own front-edge stand-in (see the Base strip section
// below for why it's a stand-in, not the real front-shell edge) and
// the leg mount/foot points, in WORLD (y = height above table datum,
// z = forward(+)/back(-)) coordinates -- the header's own
// rotate([-LEAN_DEG,0,0]) transform: world y = Q*cos(LEAN)+bz*sin(LEAN),
// world z = -Q*sin(LEAN)+bz*cos(LEAN).
front_edge_y = 0*cos(LEAN_DEG) + BACK_SHELL_DEPTH*sin(LEAN_DEG);
front_edge_z = -0*sin(LEAN_DEG) + BACK_SHELL_DEPTH*cos(LEAN_DEG);

// Original mount point: the back wall's own OUTER surface (bz=0),
// Qface=LEG_MOUNT_Q -- i.e. where the leg-mount boss's BASE sits (the
// boss itself then protrudes LEG_MOUNT_BOSS_LEN further outward, along
// the tilted axis derived below, not straight out along local Z).
leg_mount_y = LEG_MOUNT_Q*cos(LEAN_DEG);
leg_mount_z = -LEG_MOUNT_Q*sin(LEAN_DEG);

// Foot point: table level (world Y=0, flagged assumption -- see header),
// LEG_FOOT_SETBACK behind this file's own front-edge stand-in.
leg_foot_y = 0;
leg_foot_z = front_edge_z - LEG_FOOT_SETBACK;

LEG_DY = leg_foot_y - leg_mount_y;  // world Y, wall-mount point -> foot
LEG_DZ = leg_foot_z - leg_mount_z;  // world Z, wall-mount point -> foot
leg_length = sqrt(LEG_DY*LEG_DY + LEG_DZ*LEG_DZ);

// Review finding #2: a single straight screw has to run the leg's full
// length, from the foot into the mount boss's own insert -- so the
// boss itself must be tilted to point along this same mount->foot
// line, not straight out from the (near-vertical) back wall (the
// original bug: those two axes were ~37 deg apart, and the channel
// stopped at the boss's base instead of reaching the insert at its
// tip). Deriving the LOCAL (pre-lean-rotation) tilt that achieves this:
// rotating a cylinder (default +Z) by angle theta about local X, then
// applying this shell's own global rotate([-LEAN_DEG,0,0]), composes
// to one net rotation of (theta - LEAN_DEG) about world X (both share
// the X axis). Solving for the local theta whose net rotation points
// along the world mount->foot direction (LEG_DY, LEG_DZ) -- i.e.
// (-sin(theta-LEAN_DEG), cos(theta-LEAN_DEG)) proportional to
// (LEG_DY, LEG_DZ) -- gives:
LEG_BOSS_TILT = atan2(-LEG_DY, LEG_DZ) + LEAN_DEG;

// The boss's tip (where the leg attaches) then lies exactly on the
// mount->foot line, LEG_MOUNT_BOSS_LEN out from the wall -- used as the
// leg's own mount point below (review finding #6: the leg now mates
// flush with the boss along its own axis, instead of a same-point
// sphere overlapping the boss/shell at the wrong angle).
leg_mount_tip_y = leg_mount_y + LEG_MOUNT_BOSS_LEN * LEG_DY/leg_length;
leg_mount_tip_z = leg_mount_z + LEG_MOUNT_BOSS_LEN * LEG_DZ/leg_length;

// Axis for the foot-end screw-head counterbore (review finding #2's
// last point -- the counterbore was modelled vertical, ~38 deg off the
// screw axis). Rotating a cylinder by this angle about world X points
// it from the foot back toward the mount, along the leg's own straight
// axis -- what the counterbore needs, since the screw HEAD sits where
// the screw travels, not where the rubber foot (a separate, genuinely
// vertical feature) sits.
LEG_AXIS_TILT = atan2(LEG_DY, -LEG_DZ);

echo(str("Leg mount boss tilt (local frame, deg): ", LEG_BOSS_TILT));
echo(str("Leg axis tilt (world frame, deg, foot->mount): ", LEG_AXIS_TILT));

// Leg structural cross-section: no bead/finding sizes this -- own
// choice, sized generously for a small printed PETG/PLA strut under the
// ADR's own ~110g body weight and knob-torque reaction loads (ADR,
// PROP 6c stability section), but NOT load-calculated. Flagged for a
// human to verify once a real print exists.
LEG_STRUT_D      = 8.0;
SCREW_CHANNEL_D  = 2.6;  // common M2 clearance-hole size
SCREW_HEAD_D     = 4.2;  // common M2 pan/socket-head clearance, generic
FOOT_PAD_D       = 12.0; // flat pad the rubber foot sticks to
FOOT_PAD_T       = 2.5;
FOOT_RECESS_D    = 10.4; // registration pocket for the rubber foot,
FOOT_RECESS_T    = 1.0;  // sized for the chosen foot product (below)

// =====================================================================
// Base strip + feet (front contact patch, separate from the leg feet)
// =====================================================================
// ADR / PROP 6c: "The body's own bottom is a horizontal strip about
// 14.5mm deep with feet, so it doesn't stand on its front edge." This is
// a SEPARATE ground-contact patch from the rear leg feet (confirmed by
// the proposal's own side-profile ASCII diagram, which draws two
// distinct "o" foot regions with a gap between them -- one long strip
// under the main body, one short cluster under each leg).
BASE_STRIP_DEPTH = 14.5;  // ADR figure
BASE_STRIP_T     = WALL_T;  // = 2.0mm, matches the shell's own wall
BASE_STRIP_FOOT_OFFSET_X = 30;  // lateral spacing of the strip's own 2
                                  // feet -- own choice, not a cited
                                  // figure (chosen to sit well inside
                                  // FACE_W/2=61 on each side).

// Ballast reserve (PR #52 review finding #5): the bead description
// says to "leave room for a later ballast insert (weighted-base
// fallback, not committed)" -- this was missing entirely from the
// first version of this file. This is a shallow pocket cut into the
// base strip's TOP face (the side facing into the assembled interior,
// not the table-facing underside), reserving genuine volume without
// committing to any specific ballast part/shape -- NOT a finished
// ballast design, just reserved space, consistent with the bead's own
// "not committed" wording.
BALLAST_RESERVE_W = 40.0;  // own choice -- centred, comfortably inside
                            // the two foot recesses (at FACE_W/2 +/-30
                            // = 31/91, each FOOT_RECESS_D=10.4mm wide,
                            // so their outer edges sit at ~25.8/96.2 --
                            // this leaves >4mm clearance on each side).
BALLAST_RESERVE_D = 10.0;  // own choice -- leaves >2mm margin on the
                            // strip's own 14.5mm depth, front and back.
BALLAST_RESERVE_T = 1.0;   // shallow -- half of the strip's own 2.0mm
                            // thickness (BASE_STRIP_T), leaving a 1.0mm
                            // floor so the table-facing underside is
                            // never breached.

// Foot product (bead: "feet pockets sized for a NAMED rubber/gel pad
// product"): picked a 10mm (diameter) x 3mm (thick) self-adhesive
// round rubber/polyurethane foot. This is not one single SKU but a size
// that recurs, essentially unchanged, across multiple distributors'
// catalogues -- Delock 18309 (10 x 3mm self-adhesive round feet),
// Essentra RBS-10 (9.9mm dia x 3mm), Multicomp Pro MP2010-CL1-48 (10mm
// dia x 3.1mm -- the same-size listed replacement for Multicomp's own
// PD.2010C, which element14 lists as no longer manufactured; PR #52
// review minor item), Ettinger 17-52-108 (10mm dia x 3.2mm) -- which is itself good
// evidence this is a genuinely standard, widely-stocked size rather than
// one vendor's quirk, satisfying "high-friction rubber/gel feet" (ADR)
// without betting on a single hard-to-source part. FOOT_RECESS_D above
// (10.4mm) gives the 10mm pad a shallow registration pocket with 0.4mm
// clearance; FOOT_RECESS_T (1.0mm) is intentionally shallow relative to
// the pad's own ~3mm thickness so most of the compliant material stays
// proud of the shell and actually grips the table, per the ADR's
// friction/shear argument.

// =====================================================================
// Helper modules
// =====================================================================

module rounded_rect(w, h, r) {
    hull() {
        translate([r, r])     circle(r = r, $fn = 48);
        translate([w - r, r]) circle(r = r, $fn = 48);
        translate([r, h - r]) circle(r = r, $fn = 48);
        translate([w - r, h - r]) circle(r = r, $fn = 48);
    }
}

module rounded_box(w, h, depth, r) {
    linear_extrude(height = depth) rounded_rect(w, h, r);
}

// A plain boss cylinder (no pocket of its own). Insert pockets are cut
// separately, in one difference() at the back_shell_local() level, not
// inside this module -- see the comment on pcb_mount_insert_pockets()
// below for why: INSERT_LEN (4.0mm) is deeper than the PCB bosses are
// tall (REAR_CLEARANCE, 3.0mm) by design (the pocket is meant to dip
// slightly into the back wall below), and subtracting a pocket that
// deep from just the boss cylinder in isolation would delete the whole
// boss rather than leave a blind pocket.
module boss_solid(height, boss_d = BOSS_OD) {
    cylinder(h = height, d = boss_d, $fn = 32);
}

// =====================================================================
// Back shell (local frame)
// =====================================================================

module back_shell_shell() {
    difference() {
        rounded_box(FACE_W, FACE_H, BACK_SHELL_DEPTH, CORNER_R);
        // Hollow it out: a through-cut from just above the back wall
        // (bz = WALL_T) out past the open front rim. Inset by WALL_T on
        // Y (top/bottom) and Z (the back wall itself), but by
        // WALL_T - BOARD_CLEARANCE_X on X, so the 118mm board gets real
        // running clearance instead of a zero-clearance exact fit (see
        // BOARD_CLEARANCE_X above -- PR #52 review finding #1). This
        // thins the X side wall from WALL_T to WALL_T - BOARD_CLEARANCE_X
        // (1.6mm); that side-wall thickness was always this file's own
        // default choice, not an ADR-cited figure (only the back wall's
        // 2.0mm Z thickness is ADR-specified), so trading a little of it
        // for real clearance is a reasonable choice.
        translate([WALL_T - BOARD_CLEARANCE_X, WALL_T, WALL_T])
            rounded_box(FACE_W - 2*(WALL_T - BOARD_CLEARANCE_X), FACE_H - 2*WALL_T,
                        BACK_SHELL_DEPTH, max(CORNER_R - WALL_T, 0.5));
    }
}

module pcb_mount_boss_solids() {
    for (p = PCB_MOUNT_HOLES_FACE)
        translate([p[0], p[1], BACK_WALL_T])
            boss_solid(height = REAR_CLEARANCE);
            // Boss spans bz = BACK_WALL_T .. BACK_WALL_T+REAR_CLEARANCE
            // (= 5.0mm = exactly the PCB's back surface, see the
            // BACK_SHELL_DEPTH stack-up above).
}

module pcb_mount_insert_pockets() {
    // Bored from the PCB-facing top (bz = BACK_WALL_T+REAR_CLEARANCE,
    // the PCB's own back surface -- screw comes from the front, through
    // the PCB's mounting hole, down into this insert) downward by
    // INSERT_LEN. INSERT_LEN (4.0mm) is deeper than the boss alone
    // (REAR_CLEARANCE, 3.0mm), so this deliberately dips ~1mm into the
    // solid back wall below -- it stays blind (BACK_WALL_T=2.0mm, so
    // the pocket bottom at bz=1.0 is still 1.0mm short of the back
    // wall's own outer face at bz=0).
    for (p = PCB_MOUNT_HOLES_FACE)
        translate([p[0], p[1], BACK_WALL_T + REAR_CLEARANCE - INSERT_LEN])
            cylinder(h = INSERT_LEN + 0.1, d = INSERT_OD, $fn = 32);
}

// PR #52 review finding #4: the boss pad's lowest corner (lowest Qface,
// lowest/most-negative bz) must not dip below the shell's own
// world-Y=0 bottom-edge datum once the lean rotation is applied -- i.e.
// Q*cos(LEAN_DEG) + (-USBC_BOSS_RISE)*sin(LEAN_DEG) >= 0, which solves
// to Q >= USBC_BOSS_RISE*tan(LEAN_DEG). Clamping the pad's own bottom
// edge to this value (instead of letting it float at
// USBC_QFACE - USBC_BOSS_PAD_H/2, which the mapping fix above already
// moves to a safe 0.5mm but not safe ENOUGH once the rotation's own
// small additional dip is accounted for) makes this hold for any future
// retuning of these constants, not just the current numbers. Does NOT
// address the mated-plug/cable-vs-table clearance question raised in
// the same review finding -- that's tracked separately in pilink-8ry.
usbc_boss_pad_q_min = USBC_BOSS_RISE * tan(LEAN_DEG);
usbc_boss_pad_q0    = max(usbc_boss_pad_q_min, USBC_QFACE - USBC_BOSS_PAD_H/2);
usbc_boss_pad_q1    = USBC_QFACE + USBC_BOSS_PAD_H/2;

module usbc_local_boss_pad() {
    // Solid pad added on the OUTSIDE of the back wall (bz < 0) around
    // J401, to accommodate the connector's 1.5mm overhang past the
    // nominal 5.0mm back cavity (see USBC_BOSS_RISE above).
    translate([USBC_PFACE - USBC_BOSS_PAD_W/2,
               usbc_boss_pad_q0,
               -USBC_BOSS_RISE])
        cube([USBC_BOSS_PAD_W, usbc_boss_pad_q1 - usbc_boss_pad_q0,
              USBC_BOSS_RISE + BACK_WALL_T]);
}

module usbc_cutout() {
    translate([USBC_PFACE - USBC_CUTOUT_W/2,
               USBC_QFACE - USBC_CUTOUT_H/2,
               -USBC_BOSS_RISE - 0.5])
        cube([USBC_CUTOUT_W, USBC_CUTOUT_H,
              USBC_BOSS_RISE + BACK_SHELL_DEPTH + 1.0]);
}

module leg_mount_boss_solids() {
    // PR #52 review finding #2: tilted along LEG_BOSS_TILT (derived
    // above) instead of straight out along local Z, so the boss points
    // along the SAME axis as the leg's own strut/screw channel. Base
    // flush with the wall at bz=0, protruding LEG_MOUNT_BOSS_LEN along
    // that tilted axis (toward the foot).
    for (x = [LEG_PFACE_LEFT, LEG_PFACE_RIGHT])
        translate([x, LEG_MOUNT_Q, 0])
            rotate([LEG_BOSS_TILT, 0, 0])
                boss_solid(height = LEG_MOUNT_BOSS_LEN);
}

module leg_mount_insert_pockets() {
    // Same tilted axis as the boss above (LEG_BOSS_TILT), bored from
    // its outward tip inward by INSERT_LEN. The boss (6.0mm long) is
    // still taller than the insert (4.0mm), so the pocket stays fully
    // inside the boss with ~2mm of solid boss material left between the
    // pocket's inner end and the shell's own back wall -- same
    // structural margin as before, just along the corrected axis so
    // the leg's screw channel can actually reach it (review finding #2).
    for (x = [LEG_PFACE_LEFT, LEG_PFACE_RIGHT])
        translate([x, LEG_MOUNT_Q, 0])
            rotate([LEG_BOSS_TILT, 0, 0])
                translate([0, 0, LEG_MOUNT_BOSS_LEN - INSERT_LEN])
                    cylinder(h = INSERT_LEN + 0.1, d = INSERT_OD, $fn = 32);
}

module back_shell_local() {
    difference() {
        union() {
            back_shell_shell();
            usbc_local_boss_pad();
            pcb_mount_boss_solids();
            leg_mount_boss_solids();
        }
        usbc_cutout();
        pcb_mount_insert_pockets();
        leg_mount_insert_pockets();
    }
}

// =====================================================================
// Base strip (world frame -- built flat/level directly, see header note)
// =====================================================================
// Reference point: this file's own open-rim bottom edge (local Qface=0,
// bz=BACK_SHELL_DEPTH) is treated as a stand-in for the ADR's "front
// edge" (the real front edge is the front shell's own face surface,
// further forward still by FACE_T+FRONT_CAVITY=7.5mm -- that's
// pilink-8hx.2's geometry, not built here). Using this file's own edge
// is a conservative, explicitly-flagged simplification; a human should
// re-check leg/strip placement once the front shell exists. (PR #52
// review: left as-is, not re-derived against BODY_T, since doing so
// here risks drifting out of sync with the leg-axis geometry above,
// which was computed and hand-verified against THIS same stand-in --
// a human re-deriving one should re-check the other.)
// front_edge_y/z, leg_mount_y/z and leg_foot_y/z are now computed once,
// earlier in the file (the "Leg axis geometry" block, Rear legs
// section) so this module and leg() below read the same values.

module base_strip() {
    z0 = front_edge_z;
    z1 = front_edge_z - BASE_STRIP_DEPTH;
    difference() {
        // cube([x,y,z]) = [FACE_W, BASE_STRIP_T, z0-z1]: lateral width,
        // then the strip's own small vertical thickness (Y, sitting on
        // the table at Y=0..BASE_STRIP_T), then its 14.5mm depth (Z,
        // from z1 up to z0).
        translate([0, 0, z1])
            cube([FACE_W, BASE_STRIP_T, z0 - z1]);
        // feet recesses, cut from the strip's bottom (table-facing) face
        for (side = [-1, 1])
            translate([FACE_W/2 + side*BASE_STRIP_FOOT_OFFSET_X,
                       -0.1, (z0 + z1)/2])
                rotate([-90, 0, 0])
                    cylinder(h = FOOT_RECESS_T + 0.1, d = FOOT_RECESS_D, $fn = 32);
        // Ballast reserve (review finding #5): shallow pocket cut from
        // the strip's TOP (interior-facing) face, centred, well clear
        // of both foot recesses -- see BALLAST_RESERVE_* above. Not a
        // committed ballast design, just reserved room.
        translate([FACE_W/2 - BALLAST_RESERVE_W/2,
                   BASE_STRIP_T - BALLAST_RESERVE_T,
                   (z0 + z1)/2 - BALLAST_RESERVE_D/2])
            cube([BALLAST_RESERVE_W, BALLAST_RESERVE_T + 0.1, BALLAST_RESERVE_D]);
    }
}

// =====================================================================
// Leg (world frame)
// =====================================================================
// Mount point: PR #52 review finding #6 -- previously this was the back
// wall's own outer surface (bz=0), which made the leg's mount-end
// sphere (r=4) overlap the boss/shell by ~4mm since the capsule started
// AT the wall rather than at the boss's own tip. Now uses
// leg_mount_tip_y/z (derived above, in the "Leg axis geometry" block),
// the point LEG_MOUNT_BOSS_LEN out from the wall ALONG THE SAME tilted
// axis the boss itself now uses (LEG_BOSS_TILT) -- the leg's strut
// mates flush with, and continues the same axis as, the boss, instead
// of overlapping it at a mismatched angle. This still leaves the exact
// mounting lug/socket interface geometry (where the leg physically
// registers onto the boss, beyond just the screw) unmodelled -- a
// human should add that once this is actually rendered and fitted.

module leg(side) {
    x = FACE_W/2 + side*LEG_OFFSET;
    p_mount = [x, leg_mount_tip_y, leg_mount_tip_z];
    p_foot  = [x, leg_foot_y,      leg_foot_z];
    // PR #52 review finding #3(b): the strut capsule's own foot-end
    // sphere (r = LEG_STRUT_D/2) was centred AT p_foot (world Y=0, the
    // table datum), so it reached 4mm BELOW the table -- the leg would
    // have stood on this sphere, not on the modelled rubber foot. A
    // sphere's lowest point is simply (centre Y - radius) regardless of
    // its other coordinates, so raising the centre to Y=LEG_STRUT_D/2
    // puts its lowest point exactly at Y=0; the flat foot pad below
    // (still built at the true p_foot) fills the small remaining gap
    // down to the table, and is what actually contacts it.
    p_foot_strut = [p_foot[0], LEG_STRUT_D/2, p_foot[2]];
    difference() {
        union() {
            // Strut: a capsule (hull of two spheres) between the mount
            // and (raised) foot points -- avoids needing an
            // arbitrary-axis cylinder rotation, which this file can't
            // test-render to verify.
            hull() {
                translate(p_mount)      sphere(d = LEG_STRUT_D, $fn = 24);
                translate(p_foot_strut) sphere(d = LEG_STRUT_D, $fn = 24);
            }
            // Flat pad at the foot end for the rubber foot to stick to.
            // Genuinely vertical (unlike the counterbore below): this
            // is the part that must sit flat against the horizontal
            // table regardless of the leg's own angle.
            // (cylinder() is already centred in X/Z by the rotate below,
            // so the translate only needs the foot's own X/Z position,
            // same pattern as the counterbore block below.)
            translate([p_foot[0], p_foot[1] - 0.1, p_foot[2]])
                rotate([-90, 0, 0])
                    cylinder(h = FOOT_PAD_T, d = FOOT_PAD_D, $fn = 32);
        }
        // Screw channel: another capsule, hidden-fastener design (see
        // LEG_MOUNT_BOSS_LEN comment above) -- a single long screw runs
        // from the foot end up into the back-shell's insert, now along
        // the SAME axis as that insert (review finding #2), since
        // p_mount is the boss's own tip.
        hull() {
            translate(p_mount) sphere(d = SCREW_CHANNEL_D, $fn = 16);
            translate(p_foot)  sphere(d = SCREW_CHANNEL_D, $fn = 16);
        }
        // Foot-pad registration recess: genuinely vertical (same axis
        // as the pad above, not the screw) -- PR #52 review finding
        // #3(a): previously stacked ABOVE the counterbore in the same
        // (wrong) vertical frame, landing inside the strut above the
        // pad instead of at the bottom. Now cut first, directly from
        // the bottom (y ~ -0.1..0.9), where the rubber foot actually
        // sits, within the FOOT_PAD_D=12mm pad (FOOT_RECESS_D=10.4mm
        // fits inside it with margin).
        translate([p_foot[0], p_foot[1] - 0.1, p_foot[2]])
            rotate([-90, 0, 0])
                cylinder(h = FOOT_RECESS_T + 0.1, d = FOOT_RECESS_D, $fn = 32);
        // Screw-head counterbore: review finding #2's last point -- was
        // vertical (~38 deg off the screw axis), now aligned to
        // LEG_AXIS_TILT (derived above), the same straight line as the
        // screw channel and the boss's own insert. Starts just past the
        // foot recess (so the two don't have to share one frame) and
        // extends up into the strut along the real screw path.
        translate([p_foot[0], p_foot[1] - 0.1, p_foot[2]])
            rotate([LEG_AXIS_TILT, 0, 0])
                translate([0, 0, FOOT_RECESS_T])
                    cylinder(h = 3.0, d = SCREW_HEAD_D, $fn = 16);
    }
}

// =====================================================================
// USB-C vs. rear-leg clearance check (this bead's own NOTE)
// =====================================================================
// J401's shell long axis is horizontal (board/face X) -- confirmed
// against the real footprint instance in hardware/pico-link-hw.kicad_pcb
// (rot 0, pad geometry), see the USBC_HEIGHT_ABOVE_PCB comment above.
usbc_edge_left  = USBC_PFACE - USBC_SHELL_W/2;
usbc_edge_right = USBC_PFACE + USBC_SHELL_W/2;
leg_surface_left  = LEG_PFACE_LEFT  + LEG_STRUT_D/2;
leg_surface_right = LEG_PFACE_RIGHT - LEG_STRUT_D/2;
clearance_left  = usbc_edge_left  - leg_surface_left;
clearance_right = leg_surface_right - usbc_edge_right;

echo(str("BODY_T (sanity check vs. ADR ~14mm): ", BODY_T));
echo(str("Leg length (mount to foot, derived): ", leg_length, " mm"));
echo(str("Leg mount point (world y,z): (", leg_mount_y, ", ", leg_mount_z, ")"));
echo(str("Leg foot point (world y,z): (", leg_foot_y, ", ", leg_foot_z, ")"));
echo(str("USB-C port lateral centre (Pface): ", USBC_PFACE,
         " -- legs at Pface ", LEG_PFACE_LEFT, " / ", LEG_PFACE_RIGHT));
echo(str("USB-C-to-leg clearance, left: ", clearance_left, " mm"));
echo(str("USB-C-to-leg clearance, right: ", clearance_right, " mm"));
// Both come out to ~31.5mm in this model (40mm leg offset minus the
// connector's own 4.5mm shell half-width minus the leg's own 4mm strut
// half-width) -- the legs run at a constant lateral (Pface) position
// top to bottom in this model, so this clearance holds at every height
// along the leg, not just at one cross-section. No clearance conflict
// found between J401 and the rear legs.

// =====================================================================
// Top-level assembly / render selection
// =====================================================================
// PART: "assembly" (default, for visual review once OpenSCAD is
// available), "back_shell" or "leg_left" / "leg_right" (for individual
// STL export -- these are 3 separately-printed parts).
PART = "assembly";

if (PART == "assembly") {
    color("dimgray")
        rotate([-LEAN_DEG, 0, 0]) back_shell_local();
    color("gray") base_strip();
    color("slategray") leg(-1);
    color("slategray") leg(1);
} else if (PART == "back_shell") {
    rotate([-LEAN_DEG, 0, 0]) back_shell_local();
    base_strip();
} else if (PART == "leg_left") {
    leg(-1);
} else if (PART == "leg_right") {
    leg(1);
}
