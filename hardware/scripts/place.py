#!/usr/bin/env python3
"""Headless placement for pico-link-hw.kicad_pcb (pilink-7el.9).

Usage (from hardware/):  python3 scripts/place.py

Sets the board outline, mounting holes, design-rule minimums and every
footprint position. Idempotent: outline/holes it created earlier are removed
before being re-added, so re-running never duplicates them. It does NOT
touch tracks/vias/zones -- see the README's "PCB layout" section for the
scripts to run after it.

All coordinates below are millimetres relative to the board's top-left
corner (x right, y down); ORIGIN shifts that onto the page.
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
# track cannot enter J501's 0.3mm pads at 0.5mm pitch.
POWER_NETS = ["+5V", "/USB-C/VBUS_RAW", "Net-(D501-A)"]

ORIGIN = (100.0, 60.0)
BOARD_W, BOARD_H = 100.0, 55.0
HOLE_D = 2.2  # M2 clearance, NPTH
HOLES = [(3, 3), (97, 3), (3, 52), (97, 52)]

MM = pcbnew.FromMM


def pt(x, y):
    return pcbnew.VECTOR2I(MM(ORIGIN[0] + x), MM(ORIGIN[1] + y))


# --- RP2350B and its ring of decoupling -----------------------------------
CX, CY = 45.0, 29.0  # U101 centre
RING = 7.6  # decoupling cap centre distance from U101 centre

# ref: (x, y, rot) ; rot None => auto-orient so pad 1 faces `face`
P = {
    "U101": (CX, CY, 0),
    # left side: no routed signals on this edge (GPIO4-20 are spare)
    "C106": (CX - RING, CY - 2.2, "chip"),   # IOVDD pin 5
    "C116": (CX - RING, CY - 0.2, "chip"),   # DVDD pin 10
    "C107": (CX - RING, CY + 1.8, "chip"),   # IOVDD pin 15
    "C108": (CX - RING, CY + 3.8, "chip"),
    "C119": (CX - 10.6, CY + 0.8, 90),       # 10uF bulk
    # bottom
    "C109": (CX - 2.6, CY + RING, "chip"),   # IOVDD pin 24
    "C110": (CX - 0.8, CY + RING, "chip"),   # IOVDD pin 29
    "C117": (CX + 0.8, CY + RING, "chip"),   # DVDD pin 32
    # right
    "C111": (CX + RING, CY + 3.8, "chip"),   # IOVDD pin 41
    "C112": (CX + RING, CY + 0.75, "chip"),  # IOVDD pin 50
    "C118": (CX + RING, CY - 0.75, "chip"),  # DVDD pin 51 (4.7uF)
    "C113": (CX + RING, CY - 3.6, "chip"),   # QSPI_IOVDD/IOVDD pins 59/60
    # top
    "C114": (CX - 2.4, CY - RING, "chip"),   # pin 76
    "C115": (CX + 0.7, CY - RING, "chip"),   # USB_OTP_VDD / ADC pins 68/69
    "C103": (CX + 2.85, CY - RING, "chip"),  # VREG_VIN pin 64 (4.7uF)
    # core regulator, top-right corner
    "C105": (CX + 6.6, CY - 5.4, "chip"),    # VREG_AVDD pin 61
    "R104": (CX + 6.6, CY - 6.7, 0),
    "L101": (CX + 6.5, CY - 10.6, "chip"),   # pad 1 = VREG_LX
    "C104": (CX + 10.0, CY - 10.6, "l101"),  # 1V1 output cap
    # crystal
    "Y101": (CX, CY + 11.5, 0),
    "C101": (CX - 3.5, CY + 11.5, 90),
    "C102": (CX + 3.5, CY + 11.5, 90),
    "R101": (CX + 2.0, CY + 9.3, 180),     # pad 2 (XOUT) towards the chip
    # QSPI flash + PSRAM, above-left of the QSPI pins
    "U102": (36.0, 16.5, 0),
    "C120": (36.0, 12.4, 0),
    "U103": (43.5, 18.7, 0),
    "C121": (43.2, 16.0, 0),
    "R105": (40.5, 21.6, 0),
    # BOOTSEL / RESET
    "SW101": (8.0, 31.0, 0),
    "SW102": (8.0, 40.0, 0),
    "R102": (15.0, 31.0, 0),
    "R103": (15.0, 40.0, 0),
    # --- USB-C at the rear (top) edge -------------------------------------
    "J401": (46.6, 3.7, 180),
    "R402": (42.3, 10.6, 0),
    "R404": (42.3, 12.0, 0),
    "R401": (51.0, 10.6, 0),
    "R403": (51.0, 12.0, 0),
    "F401": (55.0, 7.5, 0),
    # --- 3V3 LDO ----------------------------------------------------------
    "C1": (57.0, 12.2, 0),
    "U1": (64.0, 7.5, 0),
    "C2": (62.5, 13.6, 0),
    "C3": (66.5, 13.3, 0),
    # --- ESP32 ------------------------------------------------------------
    "U201": (14.0, 14.5, 0),
    "C201": (2.3, 8.5, 90),
    "C202": (2.3, 12.0, 90),
    "R201": (2.3, 15.0, 90),
    "C203": (2.3, 18.6, 90),
    "R202": (22.5, 27.0, 0),
    # --- display FPC + backlight boost ------------------------------------
    "J501": (47.0, 50.0, 0),
    "C501": (20.0, 44.0, 0),
    "L501": (20.0, 48.3, 180),   # pad 1 (SW) towards U501
    "D501": (25.6, 45.2, 180),   # anode (SW) left, cathode right
    "U501": (25.6, 49.5, 0),     # SW pin top-left, FB pin bottom-left
    "C502": (30.6, 45.2, 0),
    "R501": (25.6, 52.6, 0),     # FB/sense resistor: south, away from SW
    # --- user controls ----------------------------------------------------
    "SW303": (75.5, 10.0, 0),    # encoder (shaft centre at +7.5,+2.5)
    "SW308": (83.0, 29.0, 0),    # Y (top)
    "SW307": (75.0, 37.0, 0),    # X (left)
    "SW306": (91.0, 37.0, 0),    # B (right)
    "SW305": (83.0, 45.0, 0),    # A (bottom)
    "R304": (68.0, 22.0, 0),
    "R303": (68.0, 23.4, 0),
    "R309": (68.0, 24.8, 0),
    "R305": (68.0, 26.2, 0),
    "R306": (68.0, 27.6, 0),
    "R307": (68.0, 29.0, 0),
    "R308": (68.0, 30.4, 0),
}

FACE = {"chip": (CX, CY), "l101": (CX + 6.5, CY - 10.6)}


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
    print(f"placed {len(P)} footprints, {len(HOLES)} holes, outline {BOARD_W}x{BOARD_H}mm")


if __name__ == "__main__":
    main()
