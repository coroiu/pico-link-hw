// =================================================================
// Pico Link -- encoder knob for Alps EC11E18244AU (SW303), 6mm D-shaft
// Bead: pilink-0ty (encoder part of pilink-8hx.3's acceptance criteria)
//
// NOT RENDERED, NOT DIMENSION-CHECKED. OpenSCAD is not installed in
// the authoring environment; arithmetic was checked in Python only.
// A human with OpenSCAD (and ideally a test print on a real encoder)
// must verify -- that is pilink-8hx.5/.6.
//
// Print orientation: upright as modeled (z=0 underside on the bed, thumb
// dish up). Do NOT print flipped: the dish would be unsupported. The
// bore/counterbore are vertical and need no supports.
//
// Z convention here: knob-local z=0 is the knob underside. In the
// assembled enclosure the underside sits KNOB_GAP above the outer face.
//
// ------------------------- Sources / provenance -------------------------
// [R] .research/findings/2026-11-15-encoder-ec11e18244au-specs.md:
//     shaft tip 24.5mm above PCB, bushing top 11.5mm above PCB,
//     housing 4.5mm, push force 6 (+2.5/-2) N, 0.5mm push travel.
// [F] enclosure/front_shell.scad: FACE_T 2.0, FRONT_SHELL_DEPTH 7.5
//     (face outer surface to PCB), shaft hole dia 8.5mm.
// [A] .planning/decisions/2026-11-15-upright-desk-clock-form-factor.md
//     and proposal 6c: knob cap dia ~18mm; proud knob accepted.
//
// Derived: shaft tip above outer face = 24.5 - 7.5 = 17.0 (matches
// front_shell.scad KNOB_PROUD_MM); bushing top above outer face =
// 11.5 - 7.5 = 4.0.
//
// [D2] Alps EC11E catalogue, Drawing No. 2 (EC11E18244AU), as read by
//     the PR reviewer: shaft dia 6, D-flat across-flats 4.5 (+0/-0.1),
//     flat length 10mm from the tip, overall 24.5mm.
// UNCONFIRMED: bushing OD 7mm (not on Drawing No. 2; same assumption
// as front_shell.scad). Only BUSHING_DIA / CB_DIA depend on it.
// Fit risk: 0.10mm radial clearance plus the shaft tolerance may run
// loose -- check on the test print and tighten CLEAR_RAD if needed.
// =================================================================

$fn = 96;

/* ----------------------------- Encoder shaft ----------------------------- */
SHAFT_DIA          = 6.0;   // Alps EC11E "6mm D-shaft" (ADR, proposal, bead)
SHAFT_FLAT_ACROSS  = 4.5;   // [D2] +0/-0.1 (flat to opposite round)
SHAFT_FLAT_LEN     = 10.0;  // [D2] from shaft tip
SHAFT_PROUD        = 17.0;  // [R]+[F] tip above outer face
BUSHING_DIA        = 7.0;   // UNCONFIRMED (matches front_shell.scad)
BUSHING_PROUD      = 4.0;   // [R]+[F] bushing top above outer face
PUSH_TRAVEL        = 0.5;   // [R] switch travel (nominal; +-0.3 tolerance)

/* --------------------------------- Knob --------------------------------- */
KNOB_DIA       = 18.0;  // [A]
KNOB_GAP       = 1.0;   // underside above the outer face; own choice:
                        // > PUSH_TRAVEL (0.5) + 0.3 tolerance, so the skirt
                        // never bottoms on the face when pressed
TOP_WALL       = 1.5;   // solid above the bore's blind end
TIP_CLEAR      = 0.0;   // shaft tip bottoms in the bore: stops the knob
                        // creeping down under repeated ~6N presses
CLEAR_RAD      = 0.10;  // FDM radial clearance on the D-bore (friction fit;
                        // house convention elsewhere is 0.15-0.2 for sliding
                        // parts -- tighter here because the knob must grip)
EDGE_R         = 1.2;   // top-edge fillet radius

// Counterbore on the underside so the knob clears the bushing and the
// face hole while the shaft is pressed.
CB_DIA   = 8.5 + 0.0;                       // = front_shell ENCODER_SHAFT_HOLE_DIA
CB_DEPTH = (BUSHING_PROUD - KNOB_GAP) + PUSH_TRAVEL + 0.5; // 4.0

// Derived
SHAFT_TIP_Z = SHAFT_PROUD - KNOB_GAP;       // 16.0 in knob coords
BORE_TOP_Z  = SHAFT_TIP_Z + TIP_CLEAR;      // 16.0
KNOB_H      = BORE_TOP_Z + TOP_WALL;        // 17.5
D_FROM_Z    = SHAFT_TIP_Z - SHAFT_FLAT_LEN; // 6.0: D profile above, round below
D_BORE_FROM = CB_DEPTH;                     // bore shared with counterbore top
ENGAGE_LEN  = SHAFT_TIP_Z - CB_DEPTH;       // 12.0 mm of shaft in the D-bore
// The flat is only 10mm long, so z=4..6 is the round (non-flat) shaft
// section and gets a round bore; the D profile is used for z=6..16.

/* ------------------------------ Grip features ------------------------------ */
RIB_COUNT   = 30;    // knurl grooves around the rim
RIB_R       = 0.6;   // groove radius (cylindrical cut)
RIB_DEPTH   = 0.5;   // how far the groove axis sits inside the rim
RIB_Z0      = 1.5;   // grooves span z RIB_Z0 .. KNOB_H - EDGE_R
DISH_DIA    = 11.0;  // shallow concave thumb dish on the top
DISH_DEPTH  = 0.8;   // keeps the ~6N press from sliding off

module d_profile(dia, flat_across, clr) {
    // 2D D-shaft cross-section; clr grows the profile radially.
    intersection() {
        circle(d = dia + 2 * clr);
        translate([-dia, -(dia / 2) - clr * 2])
            // flat on +x side: round side at -x, flat at x = flat_across - dia/2 + clr
            square([dia + (flat_across - dia / 2) + clr, dia + 4 * clr]);
    }
}

module knob_body() {
    r = KNOB_DIA / 2;
    rotate_extrude()
        polygon(concat(
            [[0, 0], [r, 0], [r, KNOB_H - EDGE_R]],
            [for (a = [0 : 10 : 90])
                [r - EDGE_R + EDGE_R * cos(a), KNOB_H - EDGE_R + EDGE_R * sin(a)]],
            [[0, KNOB_H]]));
}

module knob() {
    difference() {
        knob_body();
        // underside counterbore
        translate([0, 0, -0.01]) cylinder(d = CB_DIA, h = CB_DEPTH + 0.01);
        // round bore for the non-flat shaft section
        translate([0, 0, D_BORE_FROM - 0.01])
            cylinder(d = SHAFT_DIA + 2 * CLEAR_RAD, h = D_FROM_Z - D_BORE_FROM + 0.02);
        // D-bore (flat on +x), blind
        translate([0, 0, D_FROM_Z])
            linear_extrude(height = BORE_TOP_Z - D_FROM_Z)
                d_profile(SHAFT_DIA, SHAFT_FLAT_ACROSS, CLEAR_RAD);
        // knurl grooves
        for (i = [0 : RIB_COUNT - 1])
            rotate([0, 0, i * 360 / RIB_COUNT])
                translate([KNOB_DIA / 2 - RIB_DEPTH + RIB_R, 0, RIB_Z0])
                    cylinder(r = RIB_R, h = KNOB_H - RIB_Z0 - EDGE_R, $fn = 16);
        // thumb dish (spherical cap)
        translate([0, 0, KNOB_H + (DISH_DIA * DISH_DIA / 4 + DISH_DEPTH * DISH_DEPTH) / (2 * DISH_DEPTH) - DISH_DEPTH])
            sphere(r = (DISH_DIA * DISH_DIA / 4 + DISH_DEPTH * DISH_DEPTH) / (2 * DISH_DEPTH), $fn = 96);
    }
}

knob();

// Preview-only reference: encoder shaft + bushing (non-manifold ghost).
%translate([0, 0, -KNOB_GAP])
    union() {
        cylinder(d = BUSHING_DIA, h = BUSHING_PROUD);
        linear_extrude(height = SHAFT_PROUD) d_profile(SHAFT_DIA, SHAFT_FLAT_ACROSS, 0);
    }
