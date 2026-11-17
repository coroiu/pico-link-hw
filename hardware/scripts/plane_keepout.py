"""Ground-plane keepouts (pilink-r1h, pilink-2x7). Library, not run directly.

B.Cu is the board's ground plane; F.Cu carries the signals. Two kinds of
rule area keep it that way where it matters most:

* add_plane_keepouts() / remove_plane_keepouts(): B.Cu track keepouts that
  route.py exports to Freerouting (and removes again before saving), so
  no signal runs on B.Cu
    - under the VREG block (RP2350 DS 6.3.8.1: "the bottom layer under the
      regulator is a ground plane that connects to the QFN GND central
      pad"),
    - under the crystal (Y101, its load caps and R101).
  Vias stay allowed (GND fan-out / stitching vias are plane, not signal).
  Each area is cut back LOCKED_GAP from locked B.Cu tracks (the QSPI
  pre-route runs on B.Cu under U101): Freerouting does not finish when a
  keepout overlaps fixed wiring.
  Not under U101: any B.Cu keepout there, even one only over the exposed
  pad, made Freerouting run on without finishing in every trial (the
  chip's inner pin fan-out needs B.Cu), so whether the exposed pad's vias
  land on the main B.Cu plane is up to the routing; zones.py's gate checks
  that they at least join the main ground.
* add_pour_keepouts(): F.Cu no-fill areas zones.py adds, so the GND pour
  does not reach the VREG high-current ground island (PGND + C103.2 +
  C104.2, which must meet the main ground at its own two vias only) or the
  area between U101's pin ring and its exposed pad (where it would tie
  PGND's inner end straight to the EP).
Boxes are board-local mm (x0, y0, x1, y1); polygons are point lists.
"""
import pcbnew

O = 100.0          # keep in sync with place.py ORIGIN
NAME_B = "KO_PLANE_B_"
NAME_F = "KO_POUR_F_"
# VREG block: L101, C103/C104/C105, R104, the island vias, FB and the +1V1
# link (place.py / preroute.py geometry)
VREG_B = [(45.4, 10.8), (51.6, 10.8), (51.6, 19.3), (45.4, 19.3)]
# the same plus a channel under pins 68-71 down to the exposed pad's top
# edge, between the QSPI pre-route's B.Cu vias (x <= 43.4) and the USB
# R106/R107 corner (x >= 45.4), so the plane under the regulator meets the
# plane under the EP directly (RP2350 DS 6.3.8.1)
VREG_EP_B = [(45.4, 10.8), (51.6, 10.8), (51.6, 19.3), (45.0, 19.3), (45.0, 22.4),
             (43.7, 22.4), (43.7, 18.9), (45.4, 18.9)]
# What the router can live with: the hot loop only -- C103 (C_IN), C104
# (C_OUT), the PGND island and its two vias, from L101's bottom edge (the
# B.Cu under L101 itself is l101_keepout.py's) down to the pin ring. VREG_B
# and VREG_EP_B also close the B.Cu corridor between L101 and the pins that
# the ESP32 UART nets (U101 pins 1-4 -> U201) need: Freerouting then left
# ESP32_HCI_RXD/TXD/RTS/CTS unrouted on every seed tried.
VREG_LOOP_B = [(45.4, 16.3), (48.8, 16.3), (48.8, 19.3), (45.4, 19.3)]
CRYSTAL_B = [(39.5, 32.0), (48.6, 32.0), (48.6, 38.0), (39.5, 38.0)]
PLANE_B = {"VREG": VREG_LOOP_B, "XTAL": CRYSTAL_B}
# F.Cu no-fill: the VREG ground island (FB's west edge to the island vias'
# east edge, L101's pad 1 down to just above the pins) and U101's inside
VREG_F = [(45.75, 16.0), (48.75, 16.0), (48.75, 18.66), (45.75, 18.66)]
U101_F = [(39.4, 19.4), (48.6, 19.4), (48.6, 28.6), (39.4, 28.6)]
POUR_F = {"VREG": VREG_F, "U101": U101_F}


def _poly(pts):
    sp = pcbnew.SHAPE_POLY_SET()
    sp.NewOutline()
    for x, y in pts:
        sp.Append(pcbnew.FromMM(O + x), pcbnew.FromMM(O + y))
    return sp


def _minus_locked(board, sp, layer):
    """sp less the locked (pre-routed) non-GND tracks on `layer`, grown by
    LOCKED_GAP. Freerouting never finishes when a keepout overlaps fixed
    wiring (the QSPI pre-route runs on B.Cu under U101): it keeps trying to
    clear the violation. Each resulting piece is returned hole-free."""
    cut = pcbnew.SHAPE_POLY_SET()
    for t in board.GetTracks():
        if (t.Type() == pcbnew.PCB_TRACE_T and t.IsLocked() and t.GetLayer() == layer
                and t.GetNetname() != "GND"):
            t.TransformShapeToPolygon(cut, layer, pcbnew.FromMM(LOCKED_GAP), 5000,
                                      pcbnew.ERROR_OUTSIDE)
    out = pcbnew.SHAPE_POLY_SET(sp)
    if cut.OutlineCount():
        out.BooleanSubtract(cut)
    out.Fracture()
    return out


LOCKED_GAP = 0.3     # keepout edge to a locked track's edge, mm


def _area(board, name, layer, pts, tracks, fill, avoid_locked=False):
    sp = _poly(pts)
    if avoid_locked:
        sp = _minus_locked(board, sp, layer)
    for i in range(sp.OutlineCount()):
        src = sp.Outline(i)
        if src.PointCount() < 3:
            continue
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetIsRuleArea(True)
        z.SetZoneName(name if sp.OutlineCount() == 1 else f"{name}_{i}")
        z.SetDoNotAllowTracks(tracks)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowZoneFills(fill)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        o = z.Outline()
        o.NewOutline()
        for j in range(src.PointCount()):
            o.Append(src.CPoint(j))
        board.Add(z)


def remove_plane_keepouts(board):
    for z in list(board.Zones()):
        if z.GetZoneName().startswith(NAME_B):
            board.Remove(z)


def add_plane_keepouts(board):
    remove_plane_keepouts(board)
    for tag, pts in PLANE_B.items():
        _area(board, NAME_B + tag, pcbnew.B_Cu, pts, True, False, avoid_locked=True)


def add_pour_keepouts(board):
    for z in list(board.Zones()):
        if z.GetZoneName().startswith(NAME_F):
            board.Remove(z)
    for tag, pts in POUR_F.items():
        _area(board, NAME_F + tag, pcbnew.F_Cu, pts, False, True)
