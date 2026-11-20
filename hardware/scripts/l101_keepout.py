"""L101 (VREG inductor) copper keepouts (pilink-2wq).

RP2350 datasheet 6.3.8.1: cut away copper under the inductor on the top
layer and keep the bottom layer as an unbroken ground plane under the
regulator. Shared by route.py and zones.py. Not run on its own.

* add_l101_route_keepout(): B.Cu track/via keepout over the L101 footprint
  plus F.Cu track/via keepouts over the body area between/beside the pads,
  exported to Freerouting by route.py (removed again before the board is
  saved). The pads themselves stay reachable from outside the body.
* add_l101_pour_keepout(): pour-only rule area (F.Cu), added by zones.py so
  GND_F does not fill under or between the L101 pads, nor within
  POUR_MARGIN of them.
The rectangle is the footprint's body+pad extent plus MARGIN, taken through
the footprint transform so a rotated L101 still gets the right area. Since
pilink-7sb (Abracon AOTA-B201610) the extents are read from the footprint's
own pads and F.Fab body outline, not hard-coded, so a footprint change
carries through.
"""
import math

import pcbnew

MM = pcbnew.FromMM
REF = "L101"
MARGIN = 0.1        # route keepouts, beyond the pads/body
POUR_MARGIN = 1.0   # F.Cu GND pour cut-out, beyond the pads/body
NAME_RT = "KO_L101_RT_B"
# B.Cu region (board-local mm, x0,y0,x1,y1) kept free of routed copper.
# pilink-2wq had one box here so the GND_B plane under L101 joined the VREG
# GND vias; since pilink-2x7 the whole VREG block is plane_keepout.py's
# PLANE_B['VREG'] area, so nothing is added here.
PLANE_B = []
NAME_RT_F = "KO_L101_RT_F"
NAME_F = "KO_L101_F"


def _local(fp):
    """(pads, body) in footprint-local mm: each pad as (x0, x1, y0, y1)
    sorted west to east, and the F.Fab body outline's (x0, x1, y0, y1)."""
    pads = []
    for p in fp.Pads():
        c, s = p.GetFPRelativePosition(), p.GetSize()
        pads.append(((c.x - s.x / 2) / 1e6, (c.x + s.x / 2) / 1e6,
                     (c.y - s.y / 2) / 1e6, (c.y + s.y / 2) / 1e6))
    pads.sort()
    body = [g for g in fp.GraphicalItems()
            if g.GetLayer() == pcbnew.F_Fab and g.GetClass() == "PCB_SHAPE"
            and g.GetShape() == pcbnew.SHAPE_T_RECT]
    if not body:
        return pads, (pads[0][0], pads[-1][1],
                      min(p[2] for p in pads), max(p[3] for p in pads))
    # a footprint shape's start/end are board coordinates: undo the
    # footprint transform (the inverse of _rect's rotation)
    a = math.radians(fp.GetOrientationDegrees())
    c = fp.GetPosition()
    xs, ys = [], []
    for q in (body[0].GetStart(), body[0].GetEnd()):
        rx, ry = (q.x - c.x) / 1e6, (q.y - c.y) / 1e6
        xs.append(rx * math.cos(a) - ry * math.sin(a))
        ys.append(rx * math.sin(a) + ry * math.cos(a))
    return pads, (min(xs), max(xs), min(ys), max(ys))


def extent(fp):
    """Local (x0, x1, y0, y1) covering the pads and the body."""
    pads, bd = _local(fp)
    return (min(bd[0], pads[0][0]), max(bd[1], pads[-1][1]),
            min([bd[2]] + [p[2] for p in pads]), max([bd[3]] + [p[3] for p in pads]))


def f_rects(fp):
    """F.Cu track keepout = body minus the two pads (local coords): the
    strip between the pads, plus the body's side strips beside each pad
    where the body is wider than the pads (the DMBJ part had four; the
    Abracon part's pads are as wide as its body, so it has none). Tracks may
    still reach the pads from outside the body."""
    pads, (bx0, bx1, by0, by1) = _local(fp)
    (w0, w1, wy0, wy1), (e0, e1, ey0, ey1) = pads[0], pads[-1]
    rects = [(w1, e0, by0, by1)]
    for x0, x1, py0, py1 in ((bx0, w1, wy0, wy1), (e0, bx1, ey0, ey1)):
        if by1 > py1 + 1e-6:
            rects.append((x0, x1, py1, by1))
        if by0 < py0 - 1e-6:
            rects.append((x0, x1, by0, py0))
    return rects


def _rect(board, box=None):
    fp = board.FindFootprintByReference(REF)
    a = math.radians(fp.GetOrientationDegrees())
    c = fp.GetPosition()
    pts = []
    if box is None:
        x0, x1, y0, y1 = extent(fp)
        bx0, bx1, by0, by1 = x0 - MARGIN, x1 + MARGIN, y0 - MARGIN, y1 + MARGIN
    else:
        bx0, bx1, by0, by1 = box
    for x, y in ((bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)):
        rx = x * math.cos(a) + y * math.sin(a)
        ry = -x * math.sin(a) + y * math.cos(a)
        pts.append((c.x + MM(rx), c.y + MM(ry)))
    return pts


def _add(board, name, layer, tracks_vias, pour, box=None):
    for z in list(board.Zones()):
        if z.GetZoneName() == name:
            board.Remove(z)
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(tracks_vias)
    z.SetDoNotAllowVias(tracks_vias)
    z.SetDoNotAllowZoneFills(pour)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in _rect(board, box):
        o.Append(int(x), int(y))
    board.Add(z)


def _add_abs(board, name, layer, box):
    x0, y0, x1, y1 = box
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(pcbnew.FromMM(100.0 + x), pcbnew.FromMM(100.0 + y))
    board.Add(z)


def add_l101_route_keepout(board):
    _add(board, NAME_RT, pcbnew.B_Cu, True, False)
    for i, box in enumerate(PLANE_B):
        _add_abs(board, NAME_RT + "P" + str(i), pcbnew.B_Cu, box)
    for i, box in enumerate(f_rects(board.FindFootprintByReference(REF))):
        _add(board, NAME_RT_F + str(i), pcbnew.F_Cu, True, False, box)


def remove_l101_route_keepout(board):
    for z in list(board.Zones()):
        if z.GetZoneName().startswith("KO_L101_RT_"):
            board.Remove(z)


def add_l101_pour_keepout(board):
    # DS 6.3.8.1 also says to cut copper back near VREG_LX. The DMBJ part's
    # 4.4 x 4.2mm body kept the pour ~1mm off its LX pad; the 2.0 x 1.6mm
    # Abracon part would let it fill to within the zone clearance of that
    # pad, so the pour cut-out is POUR_MARGIN beyond the pads (pilink-7sb).
    x0, x1, y0, y1 = extent(board.FindFootprintByReference(REF))
    m = POUR_MARGIN
    _add(board, NAME_F, pcbnew.F_Cu, False, True, (x0 - m, x1 + m, y0 - m, y1 + m))
