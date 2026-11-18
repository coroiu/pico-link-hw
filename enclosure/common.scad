// =================================================================
// Pico Link enclosure -- shared board/face geometry (pilink-6lz)
//
// ONE definition of the board-to-face mapping, included by
// front_shell.scad, back_shell.scad and antenna_mount.scad
// (button_plunger.scad and knob.scad are board-independent and do not), and read (as plain `NAME = expr;`
// lines) by enclosure/scripts/check_fit.py and
// preview/scripts/export_enclosure.py. It contains no geometry, so it is
// not rendered on its own (check_fit.py skips it).
//
// KEEP EVERY ASSIGNMENT HERE ON ONE LINE (`NAME = expr;`, trailing
// `// comment` allowed): the Python scripts evaluate these with a
// line-based regex, not an OpenSCAD parser. Functions are fine (they are
// ignored by the scripts, which re-implement them from the constants).
//
// Frames (unchanged from the earlier shells):
//   board frame : origin = board top-left corner, x right, y DOWN.
//   face frame  : X = left -> right across the face (0 = left outer edge),
//                 Q = up the face (0 = bottom outer edge, FACE_H = top),
//                 Z = depth, 0 at the outer face surface.
//   X = board_x + MARGIN_X          (MARGIN_X = WALL + BOARD_CLEARANCE_X)
//   Q = QTOP - board_y              (QTOP = FACE_H - WALL - BOARD_CLEARANCE_Y)
// =================================================================

/* ============================ Board (as routed) ============================ */
// hardware/pico-link-hw.kicad_pcb Edge.Cuts, after pilink-4qc (PR #86).
BOARD_W = 122.5;
BOARD_H = 50.0;

/* ===================== Walls and board clearance ===================== */
// Shell wall / face-plate thickness (proposal 6c: "face 2.0 ... 2.0 mm back wall").
WALL = 2.0;

// Running clearance between the board's edge and the cavity wall, per side
// (pilink-6lz, supersedes pilink-mav). Budget the real tolerances: JLCPCB
// outline +/-0.2mm, FDM cavity wall +/-0.1-0.2mm, so +/-0.4mm worst case on
// each side; 0.5mm (X) / 1.0mm (Y) leaves >= 0.1mm worst case, i.e. the board
// never touches a wall even stacked at the extremes, and is not loose.
//  - X: 0.5mm/side widens the face from the earlier 122 to 127.5mm.
//  - Y: FACE_H stays 56mm (ADR/proposal figure, fin/USB-C numbers all
//    key off it), which leaves exactly 1.0mm/side; the old layout had 0.00mm at
//    the bottom and 2.00mm at the top.
BOARD_CLEARANCE_X = 0.5;
BOARD_CLEARANCE_Y = 1.0;

// Face outline: board + clearance + wall, so the board is centred in the
// cavity on both axes by construction.
FACE_W = BOARD_W + 2 * (WALL + BOARD_CLEARANCE_X); // 127.5
FACE_H = BOARD_H + 2 * (WALL + BOARD_CLEARANCE_Y); // 56.0

// Offsets of the board's top-left corner into the face frame.
MARGIN_X = WALL + BOARD_CLEARANCE_X;      // 2.5
QTOP = FACE_H - WALL - BOARD_CLEARANCE_Y; // 53.0 -- Q of board y = 0

function board_to_x(bx) = bx + MARGIN_X;
function board_to_q(by) = QTOP - by;
function board_to_face(bx, by) = [board_to_x(bx), board_to_q(by)];

/* ===================== Display panel (Crystalfontz CFAF240320A0) =====================
   Panel shadow, board-local, as placed by pilink-4qc: x 34.12..93.12, y 4..46
   (59 x 42), active area centred on the board's vertical centre and on the
   FACE's horizontal centre: board x 61.25 -> face X 63.75 = FACE_W / 2. */
PANEL_W = 59.0;
PANEL_H = 42.0;
PANEL_BOARD_X0 = 34.12;
PANEL_BOARD_X1 = PANEL_BOARD_X0 + PANEL_W; // 93.12
PANEL_BOARD_Y0 = 4.0;
PANEL_BOARD_Y1 = PANEL_BOARD_Y0 + PANEL_H; // 46.0

/* ===================== Input parts (board-local) ===================== */
// Alps EC11E18244AU shaft/knob centre (pilink-4qc): (14.25, 25).
ENCODER_BOARD_CX = 14.25;
ENCODER_BOARD_CY = 25.0;

// A/B/X/Y diamond (C&K PTS645), centre (108.25, 25), 8mm pitch.
BTN_Y = [108.25, 17]; // top
BTN_X = [100.25, 25]; // left
BTN_B = [116.25, 25]; // right
BTN_A = [108.25, 33]; // bottom

// SW101 / SW102 (BOOTSEL / RESET) side-actuated tact switches at the top edge.
SW101_BOARD = [42, 2.7];
SW102_BOARD = [52, 2.7];

// M2 mounting holes H1..H4 (pilink-4qc): NPTH 2.2mm. Each carries one shell
// screw (pilink-8hx.7): back-shell boss -> PCB -> front-shell standoff insert.
PCB_MOUNT_HOLES_BOARD = [[10, 44], [116.5, 6], [116.5, 44], [29, 2.5]];

/* ===================== Body stack along the face normal (face-frame Z) =====================
   Proposal 6c "Body thickness": face 2.0, 5.5mm to the PCB (5.0 switches, 3.3
   panel stack, J501 ~2mm), PCB 1.6, then the rear cavity and a 2.0mm back wall.
   Shared by both shells since pilink-8hx.7 (the screw stack crosses both); the
   rear-cavity envelope table that sets REAR_CLEARANCE stays in back_shell.scad. */
FRONT_CAVITY = 5.5;     // front shell inner face -> PCB front surface
PCB_T = 1.6;            // PCB thickness, hardware/README.md
REAR_CLEARANCE = 7.0;   // PCB back surface -> back wall inner face (pilink-9i4, see back_shell.scad)
BACK_WALL_T = WALL;     // ADR: "a 2.0mm back wall"
Z_PCB_FRONT = WALL + FRONT_CAVITY;                  // 7.5: PCB front = front-shell standoff tops
Z_PCB_BACK = Z_PCB_FRONT + PCB_T;                   // 9.1: PCB back = back-shell boss tops
BODY_T = Z_PCB_BACK + REAR_CLEARANCE + BACK_WALL_T; // 18.1: outer face -> back wall outer face

/* ===================== Shell fasteners (pilink-8hx.7) =====================
   User decision 2026-11-18: one M2 screw per PCB mounting hole H1..H4, driven
   from the BACK through a counterbored back-shell boss and the PCB into a brass
   heat-set insert in a front-shell standoff; the PCB is clamped between the
   boss and the standoff, nothing shows on the face. Hardware is what the user
   already has (photos 2026-11-18), not a generic assumption:
     - inserts "M2x4x3.2": M2 thread, 4.0mm long, 3.2mm knurl OD;
     - M2 socket head cap screws (ISO 4762 / DIN 912: head 3.80 max dia x 2.00
       max high), lengths 4/6/8/12/16/20/25mm.
   The axis stack (face-frame Z, measured from the outer face):
     head bearing face  SCREW_SEAT_Z = BODY_T - counterbore depth   = 15.9
     tip                SCREW_TIP_Z  = SCREW_SEAT_Z - SCREW_LEN       =  3.9
     insert             Z_PCB_FRONT - INSERT_LEN .. Z_PCB_FRONT       = 3.5 .. 7.5
     engagement         Z_PCB_FRONT - SCREW_TIP_Z                     =  3.6
   M2x12 is the only length on hand that works: x8 ends 0.4mm short of the
   insert (tip Z 7.9, inside the PCB), x16 would end at Z -0.1, through the
   insert pocket floor and out of the face.
   front_shell.scad / back_shell.scad assert each side of this. */
SCREW_LENGTHS_ON_HAND = [4, 6, 8, 12, 16, 20, 25];
SCREW_LEN = 12;          // M2x12 ISO 4762, length under the head
SCREW_D = 2.0;           // M2 nominal (shank model in check_fit.py)
SCREW_HEAD_D = 3.8;      // ISO 4762 M2 dk max
SCREW_HEAD_H = 2.0;      // ISO 4762 M2 k max
SCREW_HEAD_RECESS = 0.2; // head top sits this far below the back wall's outer face
SCREW_MIN_ENGAGEMENT = 3.0; // 1.5 x d, the usual minimum thread engagement in brass
INSERT_OD = 3.2;         // "M2x4x3.2" knurl OD (melt-in hole: front_shell.scad INSERT_HOLE_D)
INSERT_LEN = 4.0;        // "M2x4x3.2" length
CBORE_DEPTH = SCREW_HEAD_H + SCREW_HEAD_RECESS;     // 2.2, from the back wall's outer face
SCREW_SEAT_Z = BODY_T - CBORE_DEPTH;                // 15.9
SCREW_TIP_Z = SCREW_SEAT_Z - SCREW_LEN;             // 3.9
SCREW_ENGAGEMENT = Z_PCB_FRONT - SCREW_TIP_Z;       // 3.6 (insert top flush with the standoff top)

/* ===================== Seam lip (pilink-8hx.7) =====================
   Assembly is face-down (front shell on its face -> plungers -> PCB onto the
   standoffs -> back shell -> screws), so the FRONT shell has to locate the PCB
   laterally before the back shell goes on. Its rim used to stop exactly at the
   PCB front surface (Z_PCB_FRONT), i.e. it never reached the board edge. The
   inner LIP_T of its wall now carries on past the seam as a lip, LIP_H deep,
   flush with the cavity wall, so the board edges sit inside it with the same
   BOARD_CLEARANCE_X/Y as the cavity, and it lifts straight out. The back shell
   has the matching rabbet (inner LIP_T + LIP_CLEARANCE of its wall removed
   over the lip's depth + LIP_Z_CLEARANCE), which also registers the shells. */
LIP_T = 0.85;            // lip thickness (2 perimeters at 0.4mm)
LIP_CLEARANCE = 0.15;    // radial gap lip -> back-shell rabbet (leaves the back rim WALL - 1.0 = 1.0mm)
LIP_H = 2.5;             // lip depth past the seam: covers the 1.6mm PCB edge + 0.9mm lead-in
LIP_Z_CLEARANCE = 0.2;   // lip tip -> rabbet floor

/* ===================== Pigtail notch (top wall) =====================
   The gap between the board's top edge (Q = QTOP = 53) and the top wall's inner
   surface (Q = FACE_H - WALL = 54) is BOARD_CLEARANCE_Y = 1.0mm, under the
   Ø1.13mm U.FL coax plus the antenna mount's lip/element (0.7mm) -- so the
   pigtail cannot cross the PCB plane at the board edge without a local relief.
   A notch is cut into the top wall of BOTH shells, in FACE-frame coordinates
   (face X, Q, Z from the outer face), just right of the antenna mount's land
   (which ends at face X 106.05) and clear of H3's boss (Q <= 50.5). */
PIGTAIL_NOTCH_X0 = 107.0;    // face X
PIGTAIL_NOTCH_X1 = 114.0;    // face X
PIGTAIL_NOTCH_DEPTH = 1.0;   // mm into the top wall (Q 54 -> 55), 1.0mm of wall left
PIGTAIL_NOTCH_Z0 = 6.0;      // face-frame Z: PCB slab is Z 7.5..9.1, +/- 1.5mm
PIGTAIL_NOTCH_Z1 = 10.6;
