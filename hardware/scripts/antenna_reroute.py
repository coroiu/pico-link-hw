#!/usr/bin/env python3
"""Local reroute of GPIO25 and ESP32_HCI_TXD out of the antenna keepout strip
(pilink-a4u). Not run on its own: zones.py calls apply() on every run.

Freerouting ran both nets along the board's top edge (GPIO25 on B.Cu at
y=1.19, x 59.4..102.9; ESP32_HCI_TXD on B.Cu at y=1.82, x 64.5..94.2), right
under the U.FL antenna element. F.Cu between y 3.0 and 4.2 is empty there, so
each net is moved to a straight F.Cu lane just below the GND pull-back strip
(zones.py ANT_KO, y 0..3.0):

  * GPIO25: new via at (57.298, 3.289), F.Cu lane y=3.289 east to x=102.889,
    where it joins the existing F.Cu drop to the net's lower via.
  * ESP32_HCI_TXD: existing B.Cu run ends at (61.429, 4.851); new via there,
    F.Cu diagonal to y=3.78, lane east to x=94.17, then down to the existing
    via at (94.17, 4.103).

Idempotent: matches the old Freerouting segments by position, and adds the
new ones only if the old ones were found (or the new ones are absent).
"""
import pcbnew

MM = pcbnew.FromMM
O = 100.0            # keep in sync with place.py ORIGIN
TOL = 0.02
W = 0.2
VIA_D, VIA_DRILL = 0.6, 0.3


def _xy(v):
    return (pcbnew.ToMM(v.x) - O, pcbnew.ToMM(v.y) - O)


def _near(a, b):
    return abs(a[0] - b[0]) < TOL and abs(a[1] - b[1]) < TOL


def _seg(t, layer, a, b):
    if t.Type() == pcbnew.PCB_VIA_T or t.GetLayer() != layer:
        return False
    s, e = _xy(t.GetStart()), _xy(t.GetEnd())
    return (_near(s, a) and _near(e, b)) or (_near(s, b) and _near(e, a))


def _pt(p):
    return pcbnew.VECTOR2I(MM(O + p[0]), MM(O + p[1]))


def _track(board, layer, net, a, b):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(_pt(a))
    t.SetEnd(_pt(b))
    t.SetLayer(layer)
    t.SetWidth(MM(W))
    t.SetNet(net)
    board.Add(t)


def _via(board, net, p):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(_pt(p))
    v.SetWidth(pcbnew.F_Cu, MM(VIA_D))
    v.SetDrill(MM(VIA_DRILL))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net)
    board.Add(v)


def apply(board):
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    # (net, via positions to drop, [(layer, a, b) segments to drop])
    jobs = [
        ("GPIO25", [(102.8895, 1.1862)], [
            (B, (102.889, 1.186), (59.401, 1.186)),
            (B, (59.401, 1.186), (56.098, 4.489)),
        ]),
        ("ESP32_HCI_TXD", [(94.1701, 1.8243)], [
            (B, (94.17, 1.824), (64.455, 1.824)),
            (B, (64.455, 1.824), (61.429, 4.851)),
            (F, (94.17, 4.103), (94.17, 1.824)),
        ]),
    ]
    found = 0
    for net, vias, segs in jobs:
        for t in list(board.GetTracks()):
            if t.GetNetname() != net:
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                if any(_near(_xy(t.GetPosition()), v) for v in vias):
                    board.Remove(t)
                    found += 1
            elif any(_seg(t, l, a, b) for l, a, b in segs):
                board.Remove(t)
                found += 1
    if not found:
        return False   # already applied (or the router moved things)

    g = board.FindNet("GPIO25")
    # F.Cu drop (102.889, 1.186)-(102.889, 6.696): shorten its top end
    for t in board.GetTracks():
        if (t.Type() != pcbnew.PCB_VIA_T and t.GetNetname() == "GPIO25"
                and _seg(t, F, (102.889, 1.186), (102.889, 6.696))):
            board.Remove(t)
            break
    _track(board, F, g, (102.889, 3.289), (102.889, 6.696))
    _track(board, B, g, (56.098, 4.489), (57.298, 3.289))
    _via(board, g, (57.298, 3.289))
    _track(board, F, g, (57.298, 3.289), (102.889, 3.289))

    h = board.FindNet("ESP32_HCI_TXD")
    _via(board, h, (61.429, 4.851))
    _track(board, F, h, (61.429, 4.851), (62.499, 3.781))
    _track(board, F, h, (62.499, 3.781), (94.17, 3.781))
    _track(board, F, h, (94.17, 3.781), (94.17, 4.103))
    return True
