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
// Face<->board mapping: this bead ADOPTS the mapping place.py's own
// coordinates already assume (hardware/README.md flagged this as
// unconfirmed and left it for pilink-8hx.1/.2 to settle): board bottom
// edge flush with face bottom edge, i.e. Qface = BOARD_H - y_board. The
// real placed coordinates (e.g. knob centre "(16, 31)" for the ADR's
// "~19mm up the face") were already generated with exactly this formula,
// so adopting it keeps the enclosure consistent with the board that's
// actually built, rather than re-deriving a different mapping now.
MARGIN_X    = (FACE_W - BOARD_W) / 2;  // = 2.0mm each side -- also reused
                                        // below as the generic side-wall
                                        // thickness, since it matches the
                                        // back wall's own 2.0mm (PROP 6c
                                        // thickness breakdown) and gives a
                                        // single consistent "2mm wall"
                                        // figure across the shell.
WALL_T      = MARGIN_X;  // = 2.0mm

function board_to_face(bx, by) = [bx + MARGIN_X, BOARD_H - by];

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
// -> [[12,6], [114,44], [114,6], [61,46]] in (Pface, Qface).

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
J401_FACE = board_to_face(59, 45.5);  // -> (61, 4.5) in (Pface, Qface)
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

// Foot product (bead: "feet pockets sized for a NAMED rubber/gel pad
// product"): picked a 10mm (diameter) x 3mm (thick) self-adhesive
// round rubber/polyurethane foot. This is not one single SKU but a size
// that recurs, essentially unchanged, across multiple distributors'
// catalogues -- Delock 18309 (10 x 3mm self-adhesive round feet),
// Essentra RBS-10 (9.9mm dia x 3mm), Multicomp Pro PD.2010C (10mm dia x
// 3.1mm), Ettinger 17-52-108 (10mm dia x 3.2mm) -- which is itself good
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
        // (bz = WALL_T) out past the open front rim, inset by WALL_T on
        // every side.
        translate([WALL_T, WALL_T, WALL_T])
            rounded_box(FACE_W - 2*WALL_T, FACE_H - 2*WALL_T,
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

module usbc_local_boss_pad() {
    // Solid pad added on the OUTSIDE of the back wall (bz < 0) around
    // J401, to accommodate the connector's 1.5mm overhang past the
    // nominal 5.0mm back cavity (see USBC_BOSS_RISE above).
    translate([USBC_PFACE - USBC_BOSS_PAD_W/2,
               USBC_QFACE - USBC_BOSS_PAD_H/2,
               -USBC_BOSS_RISE])
        cube([USBC_BOSS_PAD_W, USBC_BOSS_PAD_H, USBC_BOSS_RISE + BACK_WALL_T]);
}

module usbc_cutout() {
    translate([USBC_PFACE - USBC_CUTOUT_W/2,
               USBC_QFACE - USBC_CUTOUT_H/2,
               -USBC_BOSS_RISE - 0.5])
        cube([USBC_CUTOUT_W, USBC_CUTOUT_H,
              USBC_BOSS_RISE + BACK_SHELL_DEPTH + 1.0]);
}

module leg_mount_boss_solids() {
    // Boss protrudes toward bz < 0 (outward, away from the shell, where
    // the leg itself sits).
    for (x = [LEG_PFACE_LEFT, LEG_PFACE_RIGHT])
        translate([x, LEG_MOUNT_Q, -LEG_MOUNT_BOSS_LEN])
            boss_solid(height = LEG_MOUNT_BOSS_LEN);
}

module leg_mount_insert_pockets() {
    // Bored from the boss's outward tip (bz = -LEG_MOUNT_BOSS_LEN,
    // where the leg's long screw enters -- see LEG_MOUNT_BOSS_LEN
    // comment above) inward by INSERT_LEN. Here the boss (6.0mm) is
    // taller than the insert (4.0mm), so the pocket stays fully inside
    // the boss with ~2mm of solid boss material left between the
    // pocket's inner end and the shell's own back wall -- no
    // dip-into-neighbouring-material trick needed here, unlike the PCB
    // bosses above.
    for (x = [LEG_PFACE_LEFT, LEG_PFACE_RIGHT])
        translate([x, LEG_MOUNT_Q, -LEG_MOUNT_BOSS_LEN])
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
// re-check leg/strip placement once the front shell exists.
front_edge_y = 0*cos(LEAN_DEG) + BACK_SHELL_DEPTH*sin(LEAN_DEG);
front_edge_z = -0*sin(LEAN_DEG) + BACK_SHELL_DEPTH*cos(LEAN_DEG);

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
    }
}

// =====================================================================
// Leg (world frame)
// =====================================================================
// Mount point: on the back wall's outer surface (bz=0), Qface=LEG_MOUNT_Q
// -- i.e. where leg_mount_boss_solids() has its BASE (the boss itself
// then protrudes a further LEG_MOUNT_BOSS_LEN=6mm outward from here, in
// local -bz). This model's leg strut starts its capsule right at that
// base point, not at the boss's outward tip -- a simplification that
// leaves the leg's own mounting lug/socket (where it slides over the
// boss) unmodeled; a human should add that interface feature once this
// is actually rendered and fitted, rather than relying on the capsule
// hull alone to represent it.
leg_mount_y = LEG_MOUNT_Q*cos(LEAN_DEG) + 0*sin(LEAN_DEG);
leg_mount_z = -LEG_MOUNT_Q*sin(LEAN_DEG) + 0*cos(LEAN_DEG);
// Foot point: table level (world Y=0, flagged assumption -- see header),
// LEG_FOOT_SETBACK behind this file's own front-edge stand-in.
leg_foot_y = 0;
leg_foot_z = front_edge_z - LEG_FOOT_SETBACK;
leg_length = sqrt(pow(leg_mount_y - leg_foot_y, 2) + pow(leg_mount_z - leg_foot_z, 2));

module leg(side) {
    x = FACE_W/2 + side*LEG_OFFSET;
    p_mount = [x, leg_mount_y, leg_mount_z];
    p_foot  = [x, leg_foot_y,  leg_foot_z];
    difference() {
        union() {
            // Strut: a capsule (hull of two spheres) between the mount
            // and foot points -- avoids needing an arbitrary-axis
            // cylinder rotation, which this file can't test-render to
            // verify.
            hull() {
                translate(p_mount) sphere(d = LEG_STRUT_D, $fn = 24);
                translate(p_foot)  sphere(d = LEG_STRUT_D, $fn = 24);
            }
            // Flat pad at the foot end for the rubber foot to stick to.
            // (cylinder() is already centred in X/Z by the rotate below,
            // so the translate only needs the foot's own X/Z position,
            // same pattern as the counterbore block below.)
            translate([p_foot[0], p_foot[1] - 0.1, p_foot[2]])
                rotate([-90, 0, 0])
                    cylinder(h = FOOT_PAD_T, d = FOOT_PAD_D, $fn = 32);
        }
        // Screw channel: another capsule, hidden-fastener design (see
        // LEG_MOUNT_BOSS_LEN comment above) -- a single long screw runs
        // from the foot end up into the back-shell's insert.
        hull() {
            translate(p_mount) sphere(d = SCREW_CHANNEL_D, $fn = 16);
            translate(p_foot)  sphere(d = SCREW_CHANNEL_D, $fn = 16);
        }
        // Screw-head counterbore + foot-pad registration recess at the
        // foot end, so the rubber foot pad covers the screw head.
        translate([p_foot[0], p_foot[1] - 0.1, p_foot[2]])
            rotate([-90, 0, 0]) {
                cylinder(h = 3.0, d = SCREW_HEAD_D, $fn = 16);
                translate([0, 0, 3.0]) cylinder(h = FOOT_RECESS_T, d = FOOT_RECESS_D, $fn = 32);
            }
    }
}

// =====================================================================
// USB-C vs. rear-leg clearance check (this bead's own NOTE)
// =====================================================================
// J401's shell long axis is assumed horizontal (board/face X), matching
// the usual USB-C receptacle footprint convention (wider than tall) --
// an assumption, since no finding states the footprint's rotation
// explicitly; flagged.
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
