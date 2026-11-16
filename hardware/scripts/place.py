#!/usr/bin/env python3
"""Headless placement for pico-link-hw.kicad_pcb (pilink-7el.12, upright
desk-clock form factor).

Usage (from hardware/):  python3 scripts/place.py

Sets the board outline, mounting holes, design-rule minimums and every
footprint position. Idempotent: outline/holes it created earlier are removed
before being re-added, so re-running never duplicates them. It does NOT
touch tracks/vias/zones -- see the README's "PCB layout" section for the
scripts to run after it.

All coordinates below are millimetres in BOARD-LOCAL space: x increases
RIGHT, y increases DOWN THE FACE (y=0 is the board's top edge, y=BOARD_H is
the bottom edge -- so "Nmm up the face" in the ADR/proposal means
y = BOARD_H - N). ORIGIN shifts board-local (0,0) onto the KiCad page.

Supersedes PR #33 (pilink-7el.9)'s 100x55mm flat-slab placement, which is
incompatible with the upright desk-clock form factor decided in
.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md: wrong
outline, encoder on the wrong side, wrong J501 orientation, no panel-shadow
keep-out. This script re-derives every position from that ADR and
docs/plans/2026-11-15-product-layout-proposal.md section 6c, cross-checked
against each footprint's own real pads/courtyard (queried from the board
pcbnew produced via create_board_from_schematic) rather than the ASCII
diagrams' approximate grid.
"""
import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")
PROJECT = os.path.join(HERE, "..", "pico-link-hw.kicad_pro")

# Net classes. Default clearance must stay below the RP2350B QFN-80's
# 0.18mm pad-to-pad gap, or every adjacent pin pair is a DRC error.
# "Power" is only for nets that never touch the 0.4mm-pitch QFN (the router
# cannot neck a wide track down into a 0.2mm pad).
DEFAULT_CLASS = {"clearance": 0.15, "track_width": 0.2,
                 "via_diameter": 0.6, "via_drill": 0.3}
POWER_CLASS = {"clearance": 0.2, "track_width": 0.5,
               "via_diameter": 0.8, "via_drill": 0.4}
# Net-(D501-K) (backlight anode rail, 40mA) is deliberately not here: a 0.5mm
# track cannot enter J501's 0.3mm pads at 0.5mm pitch. /USB-C/VBUS_RAW is
# also deliberately not here (unlike PR #33's flat-slab layout): J401's
# back-side flip puts its VBUS pads in a pocket already dense with
# CC1/CC2/USB_DP/USB_DM crossings, and Freerouting could not complete a
# 0.5mm VBUS_RAW connection there in any tested placement. Routed at the
# default 0.2mm width instead and widened post-route wherever DRC allows
# (scripts/widen.py), same as the QFN power-rail necking problem below.
POWER_NETS = ["+5V", "Net-(D501-A)"]

ORIGIN = (100.0, 100.0)
BOARD_W, BOARD_H = 118.0, 50.0
HOLE_D = 2.2  # M2 clearance, NPTH
# Back-shell boss mounting holes. Not at the board's bare corners: the
# ESP32 (upper-left) and encoder (lower-left) courtyards already claim the
# whole left edge, so holes are placed in the genuinely free pockets --
# top-right and bottom-right of the button zone, the bottom-left strip
# below the encoder, and the gap between the top-edge switches and J501.
HOLES = [(10, 44), (112, 6), (112, 44), (59, 4)]

# Display panel shadow, per the ADR/proposal 6c panel-shadow rule: 59x42mm,
# centred on the face window. Derived from J501's own anchor math below (not
# the other way round): J501's insertion face sits 24mm in from the panel's
# RIGHT edge, and its anchor x=59.4 puts that face at x=63 (anchor + half the
# footprint's 7.25mm-wide courtyard), so the panel's right edge is x=87 and
# (width 59mm) its left edge is x=28 -- i.e. x:[28,87], NOT x:[27,86] (an
# earlier draft of this comment had the off-by-one that README.md's own
# table never had; this constant is now the single source either way).
# y:[5,47] (height 42mm) centred on y=26, matching J501's own target
# centreline.
PANEL = {"x": (28.0, 87.0), "y": (5.0, 47.0)}

MM = pcbnew.FromMM


def pt(x, y):
    return pcbnew.VECTOR2I(MM(ORIGIN[0] + x), MM(ORIGIN[1] + y))


# --- RP2350B and its ring of decoupling -----------------------------------
# Cluster sits under the display panel shadow (see PANEL above, x:[28,87]
# y:[5,47]): every part in this ring is a QFN/0402/SOIC/USON/crystal, all
# comfortably <=2.5mm tall, so it's allowed under the glass per the
# panel-shadow rule. Shifted left of J501's column (x:[56,63]) to leave it
# clear.
CX, CY = 44.0, 24.0
RING = 7.2  # decoupling cap centre distance from U101 centre

# ref: (x, y, rot) ; rot None/str => auto-orient so pad 1 faces `face`
P = {
    "U101": (CX, CY, 0),
    "C106": (CX - RING, CY - 2.2, "chip"),
    "C116": (CX - RING, CY - 0.2, "chip"),
    "C107": (CX - RING, CY + 1.8, "chip"),
    "C108": (CX - RING, CY + 3.8, "chip"),
    "C119": (CX - 10.6, CY + 0.8, 90),
    "C109": (CX - 2.6, CY + RING, "chip"),
    "C110": (CX - 0.8, CY + RING, "chip"),
    "C117": (CX + 0.8, CY + RING, "chip"),
    "C111": (CX + RING, CY + 3.8, "chip"),
    "C112": (CX + RING, CY + 0.75, "chip"),
    "C118": (CX + RING, CY - 0.75, "chip"),
    "C113": (CX + RING, CY - 3.6, "chip"),
    "C114": (CX - 2.4, CY - RING, "chip"),
    "C115": (CX + 0.7, CY - RING, "chip"),
    "C103": (CX + 2.85, CY - RING, "chip"),
    "C105": (CX + 6.6, CY - 5.4, "chip"),
    "R104": (CX + 6.6, CY - 6.7, 0),
    "L101": (CX + 6.5, CY - 10.6, "chip"),
    "C104": (CX + 10.0, CY - 10.6, "l101"),
    "Y101": (CX, CY + 11.5, 0),
    "C101": (CX - 3.5, CY + 11.5, 90),
    "C102": (CX + 3.5, CY + 11.5, 90),
    "R101": (CX + 2.0, CY + 9.0, 180),
    # QSPI flash + PSRAM, above-left of the QSPI pins
    "U102": (35.0, 11.5, 0),
    "C120": (35.0, 7.4, 0),
    "U103": (42.5, 13.7, 0),
    "C121": (42.2, 11.0, 0),
    "R105": (39.5, 16.6, 0),
    # --- BOOTSEL / RESET: side-actuated SMD tacts at the TOP edge ---------
    # (pilink-7el.10/ADR consequence #4) -- the ~5mm strip between the
    # board's top edge and the panel's top edge (panel starts y=5), laid
    # out laterally over the RP2350B/flash cluster above, clear of the
    # ESP32 (x<24) and the button zone (x>86). Pull-ups follow to keep the
    # QSPI_SS/RUN stubs short.
    "SW101": (42.0, 2.7, 0),
    "SW102": (52.0, 2.7, 0),
    "R102": (42.0, 8.0, 0),
    "R103": (52.0, 8.0, 0),
    # --- USB-C: vertical receptacle on the BACK side, low, centred -------
    # between the rear legs (board-centre x=59, legs at +/-40mm -> x=19/99).
    # Flipped to B.Cu in main() (pcbnew FOOTPRINT.Flip, not expressible as
    # a plain (x,y,rot) tuple).
    "J401": (59.0, 45.5, 0),
    # F401/R401-404 moved off J401's own crowded pad forest (CC1/CC2/
    # USB_DP/USB_DM/+5V all cross within a couple mm of the connector) into
    # the clear pocket right of the backlight cluster -- Freerouting
    # repeatedly left F401's own VBUS_RAW stub unrouted when these sat
    # directly above J401; here there is room for a clean path.
    # Shifted +9mm in Y vs the original pilink-7el.12 placement (pilink-2yw):
    # the A/B/X/Y diamond below moved down by the same 9mm to make room for
    # U201's relocation, and this pocket sits directly above the diamond's
    # own left/bottom buttons, so it moved with it to stay clear.
    "F401": (84.0, 45.0, 0),
    "R401": (84.0, 41.0, 0),
    "R402": (84.0, 39.0, 0),
    "R403": (88.0, 41.0, 0),
    "R404": (88.0, 39.0, 0),
    # --- 3V3 LDO + bulk caps -----------------------------------------------
    # pilink-2yw: relocated from the free pocket below the button diamond
    # (90-106,42-47.5) into the column U201 vacated at the top-left (see
    # U201 below) -- the diamond's own old pocket is now needed for U201
    # itself (nothing else here was free/big enough; see the README PCB
    # layout section for the full free-space accounting). Anchors keep the
    # same internal geometry as the original cluster (U1 as the reference
    # point, C1/C2/C3 at their original offsets from it), just translated
    # as a rigid group to (14,10). Sits above the recentred encoder (SW303
    # below), comfortably clear of its courtyard (>=1.3mm gap).
    "C1": (4.0, 10.0, 0),
    "U1": (14.0, 10.0, 0),
    "C2": (14.0, 15.5, 0),
    "C3": (20.0, 10.0, 0),
    # --- ESP32: top-right, above the A/B/X/Y diamond ------------------------
    # pilink-2yw: relocated off the knob column (Andreas, 2026-11-16 --
    # seeing the knob sit low in the preview, decided to move U201 rather
    # than widen the board or leave the knob off-centre). Originally
    # upper-left (14,12.5) with U.FL toward the top edge; the encoder below
    # it could then only centre around y=31 (lower third), not y=25 (true
    # board-vertical-centre), because both had to share the ~26mm-wide left
    # column.
    #
    # Real free-space check (not assumed -- measured every footprint's own
    # F.CrtYd bounding box from the board, see the README PCB-layout table):
    # U201's courtyard is ~19.6 x 20.3mm (local x:[-9.78,9.78]
    # y:[-9.88,10.38]). Column (a), x<28 (left of the display-panel shadow),
    # is the only place U201 fits *without* moving anything else, but that's
    # exactly the column the knob needs to itself -- the bead's premise.
    # Column (b), x>87 (right of the panel shadow), is 31mm wide and 50mm
    # tall, which is plenty of *area*, but the A/B/X/Y diamond's real
    # courtyard (not the bead's approximate 94-110/17-33 box -- the actual
    # SW305-308 F.CrtYd union is x:[88.93,115.07] y:[13.58,36.43]) sits
    # across the middle of it, leaving only ~13.6mm clear above and ~13.6mm
    # clear below. Both the bead's suggested first candidates -- directly
    # above the diamond, and to its right -- were checked geometrically and
    # ruled out: 13.6mm of clear height is less than U201's ~19.6-20.3mm
    # minimum footprint dimension in *either* orientation, and the gap to
    # the board's right edge past SW306 is only ~2.9mm. There is no 90-deg
    # rotation or margin trim that closes a 6mm shortfall.
    # Fix applied (more disruptive than a pure U201 move, flagged as such):
    # the whole A/B/X/Y diamond group (SW305-308, rigid, same internal
    # +/-8mm geometry) shifted DOWN 9mm, from centre (102,25) to (102,34).
    # That opens ~22.6mm clear above it -- enough for U201 unrotated, with
    # a top-edge margin (~1.75mm, nudged from an initial 1.15mm once DRC
    # flagged U201's silkscreen reference field clipping the board edge --
    # the ref text sits 10.5mm beyond the footprint's own anchor, outside
    # its courtyard) and a diamond-clearance margin (~0.6mm) left over. The
    # diamond's own pull-up resistors (R305-308) and the
    # F401/R401-404 USB pocket moved with it (see their own entries) so
    # nothing is left stranded; the LDO cluster that used to sit in the
    # diamond's old lower pocket moved into U201's old column instead (see
    # above). SW101/SW102, J501, J401 and all 4 mounting holes are
    # untouched -- confirmed clear of every new anchor below.
    #
    # Antenna orientation unchanged (rot=0, U.FL end still toward y=0): the
    # original "RF-ideal: highest point, away from the table, above ground
    # plane" reasoning (ADR) still applies at this new spot -- U201 is still
    # within ~1mm of the board's top edge, just in the right-hand column
    # instead of the left. What that reasoning did NOT anticipate is being
    # directly above the diamond rather than directly above the encoder;
    # whether the U.FL->antenna-mount cable run is still short/clean from
    # here is pilink-8hx.4's own geometry to re-check now that U201 moved,
    # not re-derived here.
    "U201": (99.0, 11.6, 0),
    # Decoupling/strap passives moved with U201, same relative offsets from
    # its anchor as the original placement (just translated into column b;
    # no decoupling network was re-routed internally, only moved as a rigid
    # group). R202 relocated to U201's other side (toward the mounting hole
    # H2/board edge, not toward the display-panel shadow) -- the panel-edge
    # side only has ~2.2mm of clearance in the new spot, too tight for 5
    # stacked 0402s; H2's side has ~9mm clear instead.
    "C201": (87.2, 4.1, 0),
    "C202": (87.2, 7.1, 0),
    "R201": (87.3, 10.1, 0),
    "C203": (87.3, 13.1, 0),
    "R202": (111.0, 11.1, 0),
    # --- display FPC + backlight boost, under the panel (all <=2.5mm) ----
    # J501 rotated 270 deg: puts the 40-pin row (local y=-9.75..9.75) along
    # board Y (long axis vertical, per the ADR) and the pad-row/insertion
    # side (local offset +2.68 after this rotation) toward +X, i.e. facing
    # the panel's right edge the FPC folds in from. Anchor x=59.4 puts the
    # insertion-face edge (courtyard max x = anchor+3.625) at x=63, 24mm in
    # from the panel's right edge at x=87 (pilink-0o2's concrete rule).
    # Anchor y=19 puts J501's centre 7.0mm up from the panel's own vertical
    # centreline (y=26, from PANEL above) -- matching the ADR's "~7mm"
    # summary figure exactly; pilink-0o2's own refined measurement was
    # 7.2mm, so this placement is 0.2mm off that figure, right at the edge
    # of (not inside) the finding's own +/-0.2mm tolerance band. Not
    # re-tuned here: the difference is sub-pad-pitch and doesn't change any
    # DRC/netlist result, but say the real built number rather than quoting
    # the finding's number as if it were hit exactly.
    "J501": (59.4, 19.0, 270),
    "C501": (70.0, 37.0, 0),
    # L501 shifted 1.5mm further from U501 than a naive mirror of the old
    # layout would put it: at (70,41) its own pin 1 (SW node) landed only
    # 1.0mm from U501 pin 3 (FB), short of the custom DRU keepout below
    # (1.2mm) -- caught by DRC, not assumed.
    "L501": (68.5, 41.0, 180),
    "D501": (75.0, 38.0, 180),
    "U501": (75.0, 41.0, 0),
    "C502": (80.0, 38.0, 0),
    "R501": (75.0, 44.0, 0),
    # --- user controls -----------------------------------------------------
    # Knob (SW303): the footprint's anchor is pad A (the solder side), NOT
    # the shaft -- the shaft/knob centre sits at local (+7.5,+2.5) from the
    # anchor (confirmed from the footprint's own F.Fab/silkscreen shaft
    # circle, centred at local (7.5,2.5), radius 3mm).
    # pilink-2yw: re-centred now that U201 no longer shares this column
    # (see U201 above). Anchor solved backwards from the TRUE board-
    # vertical-centre shaft target (16, board y=25) -- not the ADR's old
    # "19mm up the face" figure (board y=31, lower third), which was itself
    # only a consequence of U201 stacking above the encoder, not a target
    # worth preserving. Achieved shaft centre: board y=25 EXACTLY (anchor
    # (8.5, 22.5) = (16,25) - (7.5,2.5)) -- no compromise was needed to
    # clear a real courtyard this time (U201 is gone from the column, the
    # LDO cluster placed above it leaves >=1.3mm clearance).
    # Re the README's own board-to-face mapping caveat: under its stated
    # (unverified) assumption that the board's bottom edge lines up with
    # the face's bottom edge, "N mm up the face" = 50-25 = 25mm. The face
    # is ~56mm tall, so if it were centred on the board instead (6mm of
    # slack split evenly top/bottom) the face's own vertical centre would
    # read as board y=28, not 25 -- i.e. this placement is exactly centred
    # on the BOARD, which may read as up to ~3mm below the FACE's visual
    # centre depending on which alignment the back shell actually uses.
    # Still flagged for pilink-8hx.1/.2 to confirm against the real
    # boss/standoff geometry, same as before -- just with a much smaller
    # residual (3mm, down from the old 12mm-ish low-third offset) and a
    # known cause (the 6mm board/face height delta) rather than an unknown
    # one.
    "SW303": (8.5, 22.5, 0),
    "R304": (34.0, 30.0, 0),   # encoder A pull-up (GPIO22)
    "R303": (34.0, 32.0, 0),   # encoder B pull-up (GPIO23)
    "R309": (34.0, 34.0, 0),   # encoder push-switch pull-up (GPIO28)
    # A/B/X/Y diamond, button zone (x>86): caps Ø8mm, +/-8mm centres,
    # standard gamepad layout (Y top/X left/B right/A bottom), matching the
    # proposal's own diagram annotation order. The exact SW305-308 <->
    # physical-position mapping is a layout choice, not schematic-
    # constrained (firmware maps GPIO24-27 to logical buttons separately,
    # see pilink-otf); documented here, not inferred.
    # pilink-2yw: the whole group shifted DOWN 9mm as a rigid block, centre
    # (102,25) -> (102,34), to open enough clear height above it for U201
    # (see U201's own comment above for the full free-space accounting --
    # this was the only change found that let U201 leave the knob's column
    # without widening the board or touching the panel-shadow/J501/J401/
    # mounting-hole zones the bead listed as fixed). This is a real,
    # visible shift of the physical button cluster -- flagged in the PR/
    # bead for pilink-8hx.2 (front shell) and pilink-8hx.4 (antenna mount)
    # to re-check their own geometry against it, not just U201's move.
    "SW308": (102.0, 26.0, 0),  # Y (top)
    "SW307": (94.0, 34.0, 0),   # X (left)
    "SW306": (110.0, 34.0, 0),  # B (right)
    "SW305": (102.0, 42.0, 0),  # A (bottom)
    # Pull-ups moved off their old spot (90,6-10.8), now inside U201's new
    # footprint, to the only other clear sliver nearby: right of U201,
    # between it and the board's right edge (U201's right courtyard edge
    # is x=108.78; these sit past it with >=1mm clearance each side).
    # Longer GPIO stubs to the diamond than before -- not routing-critical
    # (pull-ups, not a high-speed net) and left for Freerouting like every
    # other net in this layout.
    "R308": (115.5, 5.0, 0),
    "R307": (115.5, 7.0, 0),
    "R306": (115.5, 9.0, 0),
    "R305": (115.5, 11.0, 0),
    # --- SWD debug header (pilink-2ar), free pocket below the encoder ----
    # Rotated 180 so the pin-1-anchored courtyard extends UP from the
    # anchor instead of down -- lets it clear both the board's bottom edge
    # and the encoder's courtyard above it in the same ~12mm-tall pocket.
    "J101": (20.0, 46.0, 180),
}

FACE = {"chip": (CX, CY), "l101": (CX + 6.5, CY - 10.6)}

# Footprints that must end up on the back side (B.Cu): vertical-mount J401
# mates perpendicular to the PCB and exits the rear wall, so it is a
# back-side part (pilink-7el.11 / pilink-0do).
BACK_SIDE = {"J401"}


def auto_orient(fp, target):
    """Rotate fp (0/90/180/270) so its pad 1 is the pad nearest target."""
    best = None
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        pad = next(p for p in fp.Pads() if p.GetNumber() == "1")
        d = (pad.GetPosition() - target).EuclideanNorm()
        if best is None or d < best[0]:
            best = (d, rot)
    fp.SetOrientationDegrees(best[1])


def main():
    board = pcbnew.LoadBoard(BOARD)

    # -- design-rule minimums (JLCPCB, checked 2026-11-15; see README) -----
    ds = board.GetDesignSettings()
    ds.m_MinClearance = MM(0.127)
    ds.m_TrackMinWidth = MM(0.127)
    ds.m_ViasMinSize = MM(0.45)
    ds.m_MinThroughDrill = MM(0.2)
    ds.m_ViasMinAnnularWidth = MM(0.1)
    ds.m_HoleToHoleMin = MM(0.25)
    ds.m_HoleClearance = MM(0.2)
    ds.m_CopperEdgeClearance = MM(0.3)

    # -- outline + holes (remove earlier ones first: never duplicate) ------
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts:
            board.Remove(d)
    for fp in list(board.GetFootprints()):
        if fp.GetReference().startswith("H") and fp.GetReference()[1:].isdigit():
            board.Remove(fp)

    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(pt(0, 0))
    rect.SetEnd(pt(BOARD_W, BOARD_H))
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(MM(0.1))
    board.Add(rect)

    # -- panel-shadow rectangle (documentation graphic, not a keepout rule) -
    # Drawn on User.Comments so it's a single authoritative, queryable
    # record of where the 59x42mm display-panel window sits on THIS board,
    # instead of only living in README/place.py prose that can drift out of
    # sync with each other (as the x:[27,86] vs x:[28,87] mismatch this
    # fixed did). Remove any earlier copy first so re-running this script
    # never duplicates it.
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.Cmts_User:
            board.Remove(d)
    panel = pcbnew.PCB_SHAPE(board)
    panel.SetShape(pcbnew.SHAPE_T_RECT)
    panel.SetStart(pt(PANEL["x"][0], PANEL["y"][0]))
    panel.SetEnd(pt(PANEL["x"][1], PANEL["y"][1]))
    panel.SetLayer(pcbnew.Cmts_User)
    panel.SetWidth(MM(0.1))
    board.Add(panel)

    for i, (x, y) in enumerate(HOLES, 1):
        fp = pcbnew.FOOTPRINT(board)
        fp.SetReference(f"H{i}")
        fp.SetValue("MountingHole_M2")
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        fp.SetAttributes(pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM
                         | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        pad = pcbnew.PAD(fp)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(pcbnew.VECTOR2I(MM(HOLE_D), MM(HOLE_D)))
        pad.SetDrillSize(pcbnew.VECTOR2I(MM(HOLE_D), MM(HOLE_D)))
        pad.SetLayerSet(pcbnew.PAD.UnplatedHoleMask())
        fp.Add(pad)
        cy = pcbnew.PCB_SHAPE(fp)
        cy.SetShape(pcbnew.SHAPE_T_CIRCLE)
        cy.SetCenter(pcbnew.VECTOR2I(0, 0))
        cy.SetEnd(pcbnew.VECTOR2I(MM(HOLE_D / 2 + 0.6), 0))
        cy.SetLayer(pcbnew.F_CrtYd)
        cy.SetWidth(MM(0.05))
        fp.Add(cy)
        board.Add(fp)
        fp.SetPosition(pt(x, y))

    # -- footprints --------------------------------------------------------
    refs = {fp.GetReference() for fp in board.GetFootprints()}
    missing = sorted(r for r in refs if r not in P and not r.startswith("H"))
    extra = sorted(r for r in P if r not in refs)
    if missing or extra:
        sys.exit(f"placement table out of sync: unplaced={missing} unknown={extra}")

    for ref, (x, y, rot) in P.items():
        fp = board.FindFootprintByReference(ref)
        fp.SetPosition(pt(x, y))
        if isinstance(rot, str):
            fx, fy = FACE[rot]
            auto_orient(fp, pt(fx, fy))
        else:
            fp.SetOrientationDegrees(rot)
        if ref in BACK_SIDE and fp.GetLayer() == pcbnew.F_Cu:
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)

    pcbnew.SaveBoard(BOARD, board)

    # -- net classes (project file; SaveBoard has just rewritten it) -------
    with open(PROJECT) as fh:
        pro = json.load(fh)
    ns = pro["net_settings"]
    default = next(c for c in ns["classes"] if c["name"] == "Default")
    default.update(DEFAULT_CLASS)
    power = dict(default, name="Power", **POWER_CLASS)
    ns["classes"] = [default, power]
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in POWER_NETS]
    with open(PROJECT, "w") as fh:
        json.dump(pro, fh, indent=2)
        fh.write("\n")
    print(f"placed {len(P)} footprints, {len(HOLES)} holes, outline {BOARD_W}x{BOARD_H}mm, "
          f"panel shadow x:{PANEL['x']} y:{PANEL['y']} on User.Comments")


if __name__ == "__main__":
    main()
