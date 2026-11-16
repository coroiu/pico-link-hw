#!/usr/bin/env python3
"""RETIRED (pilink-xzs, PR #72): the script aborts on run and must not be used. Historical record of the one-off local reroute of SW101/SW102 around the Alps no-copper area
(pilink-ge9). Usage (from hardware/):  python3 scripts/sw_reroute.py

Freerouting had run pad-2 GND and the pad-1 BOOTSEL/RESET net straight
through the SKRTLAE010 "prohibited area of copper tracks" (see
sw_keepout.py). This script does NOT re-run the router; it removes just
those segments and replaces them, leaving every other track alone:

  * GND (pad 2): pad 2 is boxed in on F.Cu (pads 1 either side, the
    keepout below), so it leaves through a via just above its top edge to
    the B.Cu GND pour.
  * BOOTSEL/RESET (the two pad-1 lands): a via beside each land, tied
    together by a B.Cu bar at pad level, with a B.Cu trunk straight down
    to a via next to the pull-up resistor's pad 2, then a short F.Cu stub.

Idempotent: it removes everything it adds (matched by position) first. A
full place/route/zones re-run supersedes it, since route.py now loads the
keepouts before Freerouting.
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")
MM = pcbnew.FromMM
TOL = 0.02  # mm

# ref, resistor ref, signal net, GND segments to drop (abs mm endpoints)
SWITCHES = {
    "SW101": dict(r="R102", net="/RP2350B + Memory/BOOTSEL_NODE", gnd_drop=[
        ((142.0, 101.8), (142.0, 104.794)),
        ((142.0, 104.794), (143.095, 105.889)),
        ((143.095, 105.889), (143.095, 110.88)),
    ]),
    "SW102": dict(r="R103", net="/RP2350B + Memory/RESET_NODE", gnd_drop=[
        ((152.0, 101.8), (152.0, 106.608)),
        ((152.0, 106.608), (150.958, 107.65)),
        ((150.958, 107.65), (150.958, 109.878)),
    ]),
}
W = 0.2
VIA_D, VIA_DRILL = 0.6, 0.3


def near(a, b):
    return abs(a[0] - b[0]) < TOL and abs(a[1] - b[1]) < TOL


def xy(v):
    return (pcbnew.ToMM(v.x), pcbnew.ToMM(v.y))


def seg_match(t, a, b):
    s, e = xy(t.GetStart()), xy(t.GetEnd())
    return (near(s, a) and near(e, b)) or (near(s, b) and near(e, a))


def pt(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def add_track(board, layer, net, a, b):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(*a))
    t.SetEnd(pt(*b))
    t.SetLayer(layer)
    t.SetWidth(MM(W))
    t.SetNet(net)
    board.Add(t)


def add_via(board, net, p):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(*p))
    v.SetWidth(pcbnew.F_Cu, MM(VIA_D))
    v.SetDrill(MM(VIA_DRILL))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net)
    board.Add(v)


def main():
    sys.exit("sw_reroute.py is retired (pilink-xzs): it causes shorts on the "
             "current routing. route.py already loads the sw_keepout.py rule "
             "areas before Freerouting, so fresh runs avoid the keepout.")
    board = pcbnew.LoadBoard(BOARD)
    for ref, cfg in SWITCHES.items():
        sw = board.FindFootprintByReference(ref)
        cx, cy = xy(sw.GetPosition())
        rp = board.FindFootprintByReference(cfg["r"])
        r2 = next(p for p in rp.Pads() if p.GetNumber() == "2")
        rx, ry = xy(r2.GetPosition())
        sig = board.FindNet(cfg["net"])
        gnd = board.FindNet("GND")

        g_via = (cx, cy - 2.05)
        v_l, v_r = (cx - 2.2, cy - 1.2), (cx + 2.2, cy - 1.2)
        v_low = (cx, ry - 1.1)

        # --- remove: old routing + anything this script added before ----
        for t in list(board.GetTracks()):
            if t.Type() == pcbnew.PCB_VIA_T:
                if any(near(xy(t.GetPosition()), p)
                       for p in (g_via, v_l, v_r, v_low)):
                    board.Remove(t)
                continue
            if t.GetNetCode() == sig.GetNetCode():
                board.Remove(t)   # whole signal net is local to this cluster
                continue
            if t.GetNetCode() == gnd.GetNetCode() and any(
                    seg_match(t, a, b) for a, b in
                    cfg["gnd_drop"] + [((cx, cy - 0.9), g_via)]):
                board.Remove(t)

        # --- add ----------------------------------------------------------
        add_via(board, gnd, g_via)
        add_track(board, pcbnew.F_Cu, gnd, (cx, cy - 0.9), g_via)
        for v, px in ((v_l, cx - 1.225), (v_r, cx + 1.225)):
            add_via(board, sig, v)
            add_track(board, pcbnew.F_Cu, sig, (px, v[1]), v)
        add_track(board, pcbnew.B_Cu, sig, v_l, (cx, v_l[1]))
        add_track(board, pcbnew.B_Cu, sig, (cx, v_l[1]), v_r)
        add_track(board, pcbnew.B_Cu, sig, (cx, v_l[1]), v_low)
        add_via(board, sig, v_low)
        add_track(board, pcbnew.F_Cu, sig, v_low, (rx, ry))
        print(f"{ref}: rerouted GND + {cfg['net']}")
    pcbnew.SaveBoard(BOARD, board)


if __name__ == "__main__":
    main()
