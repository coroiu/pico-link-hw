// Internal mount for the adhesive U.FL 2.4GHz antenna (pilink-8hx.4).
//
// NOT RENDERED/FIT-CHECKED. OpenSCAD is not installed in the environment
// this file was authored in (see ../enclosure/README.md and AGENTS.md
// "This repo has no build/test automation") -- every dimension below is
// transcribed from a cited source or marked as this file's own assumption.
// A human with OpenSCAD (or a later pass with it installed) still needs to
// actually render this and check it against the real back-shell geometry
// from pilink-8hx.1, once that lands.
//
// Scope: this file models only the antenna mount feature itself (a flat
// adhesive-land + retention lip + cable strain relief + a reference cable
// channel), not a full top-wall shell. pilink-8hx.1 (back shell) and
// pilink-8hx.2 (front shell) are being built in parallel on separate
// branches and own the real top-wall geometry; antenna_mount() is meant to
// be instantiated (translated/rotated onto the real wall) from whichever of
// those ends up owning the top wall's inner surface. demo_assembly() below
// is a self-contained preview only -- its "stand-in top wall" slab is NOT
// the real enclosure wall and must not be unioned into either shell.

// ---------------------------------------------------------------------------
// Antenna part -- Kinghelm KH-FPC2.4G-1.13IPEX-240, LCSC C4943394. Selected
// (over the AIWF026 alternate) in
// .research/findings/2026-11-15-ufl-antenna-selection.md and closed out in
// bd pilink-8wx ("primary Kinghelm KH-FPC2.4G-1.13IPEX-240, alternate
// MyAntenna AIWF026 flagged as fractionally over cert-safe gain ceiling").
// ---------------------------------------------------------------------------

// Element footprint, confirmed directly on LCSC's C4943394 product page
// (packaging field "SMD, 45.8x6.5mm") per the research finding.
ANTENNA_ELEMENT_LENGTH = 45.8;   // mm, long axis
ANTENNA_ELEMENT_WIDTH  = 6.5;    // mm

// Element thickness is NOT given anywhere in the finding or on the LCSC
// listing -- this is this file's own nominal placeholder for a thin
// adhesive-backed FPC, used only so the 3D preview has a visible element;
// it is not a verified dimension and should not drive any clearance math.
ANTENNA_ELEMENT_THICKNESS_NOMINAL = 0.3; // mm, UNVERIFIED placeholder

// Pigtail: Ø1.13mm coax, IPEX/U.FL-class plug. The "-240" part-number
// suffix implies a 240mm cable but the finding is explicit this is
// INFERRED from the part number, not a confirmed datasheet/listing field
// -- confirm before ordering. Not used for any geometry below beyond the
// cable-channel's nominal width.
ANTENNA_CABLE_DIAMETER = 1.13; // mm

// Clearance guidance (.research/findings/2026-11-15-ufl-antenna-selection.md,
// "Clearance / ground-plane guidance"): the 32UE's own datasheet carries no
// keepout for an external antenna (that keepout only applied to the
// on-module antenna variant). The finding instead cites general adhesive-FPC
// practice: "keep the flexible element itself clear of metal/ground
// plane/battery within roughly its own element length on the radiating
// side". Modeled here as a single symmetric reference zone equal to the
// element's own length -- a simplification of what the source guidance
// describes as one-sided/radiating-direction-specific, since neither the
// finding nor any datasheet in this repo states which end of this specific
// part radiates. Shown with `%` (OpenSCAD non-manifold preview modifier) so
// it never affects a boolean/union result -- it is a visual "keep metal
// clear of this" marker for a human reviewing the render, not a solid.
ANTENNA_KEEPOUT_FROM_METAL = ANTENNA_ELEMENT_LENGTH; // mm, see note above

// ---------------------------------------------------------------------------
// Board / face coordinate assumptions.
//
// hardware/README.md "PCB layout (pilink-7el.12, upright desk-clock form
// factor)" gives the real 118 x 50mm board's placement table in board-local
// mm (origin top-left, x right, y down). That same section already flags,
// in its own words, that mapping board-local coordinates onto the ~122 x
// 56mm face is NOT yet settled -- "that assumption was never checked against
// the actual back-shell boss/standoff design (which doesn't exist yet)...
// Flagged for pilink-8hx.1/.2 to confirm". This file inherits that same
// unconfirmed convention rather than inventing a different one, so all
// three enclosure beads stay comparable:
//   - board centered left-right in the face: offset = (FACE_W-BOARD_W)/2
//   - board bottom edge flush with the face's bottom edge: offset =
//     FACE_H-BOARD_H, all of the difference taken up above the board's own
//     top edge (hardware/README.md's own "y = 50 - N" rule)
// X is the one axis that matters for this file: left-right position is
// unaffected by the body's 15-degree lean, so board-local X and face-local
// X are directly comparable to pilink-8hx.2's SW101/SW102 pinhole X values
// via this same offset.
// ---------------------------------------------------------------------------

BOARD_W = 118.0; // mm, hardware/README.md
BOARD_H = 50.0;  // mm, hardware/README.md
FACE_W  = 122.0; // mm, .planning/decisions/2026-11-15-upright-desk-clock-form-factor.md ("Face about 122 W x 56 H mm")
FACE_H  = 56.0;  // mm, same ADR

BOARD_TO_FACE_X_OFFSET = (FACE_W - BOARD_W) / 2; // = 2.0mm, ASSUMPTION, see note above
BOARD_TO_FACE_Y_OFFSET = FACE_H - BOARD_H;       // = 6.0mm, ASSUMPTION, see note above

// U201 (ESP32-WROOM-32UE) antenna-connector-end edge, board-local, from
// .planning/decisions/2026-11-15-upright-desk-clock-form-factor.md's
// "Verification: rear USB-C / antenna / FPC clearance check (pilink-5g8)":
// "that module edge sits at board-local Y ~= 2.65-2.9, X ~= 5-23
// (centered X=14)". The connector's exact position along that edge wasn't
// confirmed from a rendered datasheet drawing there either -- same caveat
// carried forward here.
U201_ANTENNA_X_MIN = 5.0;
U201_ANTENNA_X_MAX = 23.0;
U201_ANTENNA_X_CENTER = 14.0;
U201_ANTENNA_Y_MIN = 2.65;
U201_ANTENNA_Y_MAX = 2.9;

// Face-local X center of U201's U.FL connector, used below to keep the
// antenna mount's cable run short per the ADR ("ESP32 upper-left, U.FL
// toward the top edge ... with the ESP32 directly below").
U201_ANTENNA_FACE_X_CENTER = U201_ANTENNA_X_CENTER + BOARD_TO_FACE_X_OFFSET; // 16.0mm

// SW101/SW102 (BOOTSEL/RESET) top-edge pinhole X positions, board-local,
// from hardware/README.md's placement table: "SW101 (42, 2.7), SW102
// (52, 2.7) -- in the 5mm strip above the panel". This is pilink-8hx.2's
// own geometry (front shell, top-edge pinhole channels) -- NOT duplicated
// here, only read for the conflict check below.
SW101_X_BOARD_LOCAL = 42.0;
SW102_X_BOARD_LOCAL = 52.0;
SW101_X_FACE_LOCAL = SW101_X_BOARD_LOCAL + BOARD_TO_FACE_X_OFFSET; // 44.0mm
SW102_X_FACE_LOCAL = SW102_X_BOARD_LOCAL + BOARD_TO_FACE_X_OFFSET; // 54.0mm

// ---------------------------------------------------------------------------
// This file's own choices (not sourced from any ADR/finding -- stated so a
// reviewer knows exactly which numbers are mine to argue with).
// ---------------------------------------------------------------------------

ASSEMBLY_CLEARANCE = 1.0;     // mm, margin added around the element footprint so an installer can place the adhesive antenna by eye, not a datasheet figure
WALL_THICKNESS = 2.0;         // mm, nominal FDM shell wall -- pilink-8hx.1 may land on a different value; parameterized so it's a one-line change here
LEFT_WALL_CLEARANCE = 3.0;    // mm, assumed minimum distance from the body's left inner wall to the mount's land, pending pilink-8hx.1's real wall geometry
LIP_WIDTH = 0.8;              // mm, width of the raised locating lip around the land
LIP_HEIGHT = 0.4;             // mm, height of the raised locating lip
CABLE_CHANNEL_WIDTH = 2.0;    // mm, clear of ANTENNA_CABLE_DIAMETER (1.13mm) with margin for the IPEX plug body
CABLE_CHANNEL_DEPTH = 1.5;    // mm
STRAIN_RELIEF_CLIP_ID = 1.6;  // mm, snug over the 1.13mm coax
STRAIN_RELIEF_CLIP_HEIGHT = 2.0; // mm

// Land (adhesive mounting area) footprint, element + clearance on all sides.
MOUNT_LAND_LENGTH = ANTENNA_ELEMENT_LENGTH + 2 * ASSEMBLY_CLEARANCE; // 47.8mm
MOUNT_LAND_WIDTH  = ANTENNA_ELEMENT_WIDTH + 2 * ASSEMBLY_CLEARANCE;  // 8.5mm

// Mount position in the top wall's own local X (= face-local X, left-right,
// unaffected by the lean -- see coordinate note above). Hugs the left inner
// wall so the cable run up to U201 stays short, per the ADR.
MOUNT_X_MIN = LEFT_WALL_CLEARANCE;                     // 3.0mm
MOUNT_X_MAX = MOUNT_X_MIN + MOUNT_LAND_LENGTH;         // 50.8mm
MOUNT_X_CENTER = (MOUNT_X_MIN + MOUNT_X_MAX) / 2;      // 26.9mm

// *** OPEN CONFLICT -- flagging, not resolving (see PR body) ***
// MOUNT_X_MAX (50.8mm) overlaps SW101_X_FACE_LOCAL (44.0mm, pilink-8hx.2's
// BOOTSEL pinhole). A 45.8mm-long element started anywhere near the left
// inner wall reaches into the low-40s/50s no matter how LEFT_WALL_CLEARANCE
// is tuned; moving the whole mount clear of both pinholes (past
// SW102_X_FACE_LOCAL = 54.0mm) would fix the X overlap but costs a ~60mm+
// lateral cable run back to U201 at face X=16, defeating the ADR's reason
// for putting the antenna upper-left in the first place. This file picks
// the short-cable-run placement and surfaces the number instead of silently
// picking a resolution that's really pilink-8hx.2's and this bead's to
// reconcile together (e.g. shifting SW101 a few mm right within its own "5mm
// strip above the panel", or confirming the pinhole's actual channel is
// narrow enough that it only clips the antenna land's unused margin, not the
// element itself).

module antenna_element_reference() {
  // Non-manifold preview of the antenna element itself, for visual
  // reference only -- never unioned into a shell.
  %color("DarkOliveGreen")
    cube([ANTENNA_ELEMENT_LENGTH, ANTENNA_ELEMENT_WIDTH, ANTENNA_ELEMENT_THICKNESS_NOMINAL]);
}

module antenna_keepout_reference() {
  // Non-manifold preview of the "keep metal clear" zone from the finding's
  // clearance guidance (see ANTENNA_KEEPOUT_FROM_METAL above). Centered on
  // the element, inflated symmetrically in all directions as the
  // simplification noted above.
  k = ANTENNA_KEEPOUT_FROM_METAL;
  %color("Yellow", 0.15)
    translate([-( k - ANTENNA_ELEMENT_LENGTH) / 2, -(k - ANTENNA_ELEMENT_WIDTH) / 2, 0])
      cube([k, k, 0.1]);
}

// The mount itself: a locating lip (raised frame) around the land, plus a
// cable channel and strain-relief clip running toward -Y (i.e. toward
// wherever the integrating shell's cavity continues down to U201 -- this
// file does not know that path in 3D, since pilink-8hx.1's internal
// standoff/cavity geometry above the board's top edge doesn't exist yet;
// the channel below is a short straight stub to hand off to).
//
// Local frame: X = left-right (= face-local X), Y = into the top wall's own
// shallow depth (toward the cavity/cable exit), Z = wall-normal (thickness).
// Origin (0,0,0) is the land's own bottom-left-front corner on the wall's
// inner surface.
module antenna_mount(
  land_length = MOUNT_LAND_LENGTH,
  land_width = MOUNT_LAND_WIDTH,
  lip_width = LIP_WIDTH,
  lip_height = LIP_HEIGHT,
  channel_width = CABLE_CHANNEL_WIDTH,
  channel_depth = CABLE_CHANNEL_DEPTH,
  channel_length = 8.0, // mm, short stub -- real length depends on pilink-8hx.1's cavity geometry
  clip_id = STRAIN_RELIEF_CLIP_ID,
  clip_height = STRAIN_RELIEF_CLIP_HEIGHT
) {
  // Locating lip: a thin rectangular frame standing LIP_HEIGHT proud of the
  // wall's inner surface, outer edge at the land footprint, so an installer
  // seats the adhesive-backed element against its inside face. Left open on
  // the -Y edge (cable exit side).
  module lip_frame() {
    difference() {
      translate([-lip_width, -lip_width, 0])
        cube([land_length + 2 * lip_width, land_width + lip_width, lip_height]);
      translate([0, 0, -0.1])
        cube([land_length, land_width + lip_width + 0.1, lip_height + 0.2]);
    }
  }

  color("SlateGray") lip_frame();

  // Cable channel stub: shallow groove from the land's cable-exit edge
  // (center of the -Y edge, under the connector end of the element) running
  // further in -Y, toward the cavity. Rounded-rectangle cross-section via a
  // hull of two cylinders so a 1.13mm coax plus its IPEX plug body has room.
  module channel() {
    hull() {
      translate([land_length / 2, 0, channel_depth / 2])
        rotate([90, 0, 0])
          cylinder(h = 0.01, d = channel_width, $fn = 24);
      translate([land_length / 2, -channel_length, channel_depth / 2])
        rotate([90, 0, 0])
          cylinder(h = 0.01, d = channel_width, $fn = 24);
    }
  }

  color("SlateGray")
    translate([0, 0, 0])
      channel();

  // Strain-relief clip: a C-shaped boss near the channel's far end so the
  // coax doesn't transmit pull-force to the U.FL plug on U201.
  module strain_relief_clip() {
    difference() {
      cylinder(h = clip_height, d = clip_id + 2 * lip_width, $fn = 32);
      translate([0, 0, -0.1])
        cylinder(h = clip_height + 0.2, d = clip_id, $fn = 32);
      // open the C on one side so the cable can be pressed in
      translate([-(clip_id + 2 * lip_width), -(clip_id + 2 * lip_width) / 2, -0.1])
        cube([clip_id + 2 * lip_width, clip_id + 2 * lip_width, clip_height + 0.2]);
    }
  }

  translate([land_length / 2, -channel_length, channel_depth])
    rotate([0, 0, 90])
      color("DimGray") strain_relief_clip();
}

// Self-contained preview assembly: places antenna_mount() at
// MOUNT_X_MIN/MOUNT_X_CENTER on a STAND-IN slab representing the top wall's
// local area, with the element + keepout reference shown in place, and a
// marker for U201's connector X-center plus the two sibling pinhole X
// positions so the X-range conflict above is visible in one render. The
// slab is explicitly NOT the real top wall (pilink-8hx.1/.2 own that) --
// only wide/deep enough locally to host this feature for review.
module demo_assembly() {
  slab_length = 60; // mm, local preview only, not FACE_W
  slab_depth = 16;  // mm, local preview only, not BODY_THICKNESS
  slab_thickness = WALL_THICKNESS;

  color("LightGray", 0.3)
    cube([slab_length, slab_depth, slab_thickness]);

  translate([MOUNT_X_MIN, slab_depth - MOUNT_LAND_WIDTH - 2, slab_thickness]) {
    antenna_mount();
    translate([ASSEMBLY_CLEARANCE, ASSEMBLY_CLEARANCE, 0])
      antenna_element_reference();
    translate([ASSEMBLY_CLEARANCE, ASSEMBLY_CLEARANCE, 0])
      antenna_keepout_reference();
  }

  // U201 U.FL connector X-center marker (short red peg dropping toward
  // where the PCB sits, well below this local slab).
  translate([U201_ANTENNA_FACE_X_CENTER - MOUNT_X_MIN, 0, 0])
    color("Red") cylinder(h = 0.5, d = 1.0, $fn = 12);

  // SW101/SW102 pinhole X markers (pilink-8hx.2's geometry, not drawn here
  // -- just the X position, to make the overlap with MOUNT_X_MAX visible).
  translate([SW101_X_FACE_LOCAL - MOUNT_X_MIN, slab_depth, 0])
    color("Blue") cylinder(h = 0.5, d = 1.0, $fn = 12);
  translate([SW102_X_FACE_LOCAL - MOUNT_X_MIN, slab_depth, 0])
    color("Blue") cylinder(h = 0.5, d = 1.0, $fn = 12);
}

demo_assembly();
