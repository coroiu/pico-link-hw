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
    "F401": (84.0, 36.0, 0),
    "R401": (84.0, 32.0, 0),
    "R402": (84.0, 30.0, 0),
    "R403": (88.0, 32.0, 0),
    "R404": (88.0, 30.0, 0),
    # --- 3V3 LDO + bulk caps, free pocket below the button diamond -------
    "C1": (90.0, 42.0, 0),
    "U1": (100.0, 42.0, 0),
    "C2": (100.0, 47.5, 0),
    "C3": (106.0, 42.0, 0),
    # --- ESP32: upper-left, U.FL antenna end toward the top edge ---------
    # (confirmed from the stock footprint's own F.Fab outline: the antenna
    # end is the short edge beyond pins 1/38, at local y=-9.6, opposite the
    # single row of edge pads 15-24 at y=+9.35 -- rotation 0 puts that end
    # toward y=0, the board's top edge, exactly as the ADR wants.)
    "U201": (14.0, 12.5, 0),
    "C201": (2.2, 5.0, 0),
    "C202": (2.2, 8.0, 0),
    "R201": (2.3, 11.0, 0),
    "C203": (2.3, 14.0, 0),
    "R202": (26.0, 12.0, 0),
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
    # circle, centred at local (7.5,2.5), radius 3mm). Anchor below is
    # solved backwards from the ADR's shaft-centre target (16, 19mm up the
    # face -> board y = 50-19 = 31).
    "SW303": (8.5, 28.5, 0),
    "R304": (34.0, 30.0, 0),   # encoder A pull-up (GPIO22)
    "R303": (34.0, 32.0, 0),   # encoder B pull-up (GPIO23)
    "R309": (34.0, 34.0, 0),   # encoder push-switch pull-up (GPIO28)
    # A/B/X/Y diamond, button zone (x>86): caps Ø8mm, +/-8mm centres around
    # (102,25) -- standard gamepad layout (Y top/X left/B right/A bottom),
    # matching the proposal's own diagram annotation order. The exact
    # SW305-308 <-> physical-position mapping is a layout choice, not
    # schematic-constrained (firmware maps GPIO24-27 to logical buttons
    # separately, see pilink-otf); documented here, not inferred.
    "SW308": (102.0, 17.0, 0),  # Y (top)
    "SW307": (94.0, 25.0, 0),   # X (left)
    "SW306": (110.0, 25.0, 0),  # B (right)
    "SW305": (102.0, 33.0, 0),  # A (bottom)
    "R308": (90.0, 6.0, 0),
    "R307": (90.0, 7.6, 0),
    "R306": (90.0, 9.2, 0),
    "R305": (90.0, 10.8, 0),
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
