#!/usr/bin/env python3
"""DC resistance of routed copper between two pads (pilink-yt5).

Usage (from hardware/):
    python3 scripts/net_resistance.py                 # the power-path report
    python3 scripts/net_resistance.py NET REF.PAD REF.PAD
    (either form takes --board PATH first to measure another board file)

Builds a resistor network from the net's tracks and vias (pads are treated
as ideal nodes; zones/pours are IGNORED, so a result is an upper bound where
a pour also carries the current) and solves it for the effective resistance
between the two pads. Copper: 1oz = 35um outer layers, rho 1.72e-8 Ohm.m
(0.49 mOhm/square); via barrel plating 18um (JLCPCB's IPC class 2 minimum
average is 20um), 1.6mm board.
"""
import math
import os
import sys

import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")
RHO = 1.72e-5        # Ohm.mm
T_CU = 0.035         # mm
PLATING = 0.018      # mm
BOARD_T = 1.6        # mm

# (label, net, from, to): the paths pilink-yt5 / pilink-fvz are about
REPORT = [
    ("VBUS_RAW  J401.B9 -> F401.2", "/USB-C/VBUS_RAW", "J401.B9", "F401.2"),
    ("VBUS_RAW  J401.A9 -> F401.2", "/USB-C/VBUS_RAW", "J401.A9", "F401.2"),
    ("+5V       F401.1  -> U1.3", "+5V", "F401.1", "U1.3"),
    ("+3V3      U1.2    -> U201.2", "+3V3", "U1.2", "U201.2"),
    ("+3V3      U1.2    -> U501.6", "+3V3", "U1.2", "U501.6"),
    ("+3V3      U1.2    -> U101.64", "+3V3", "U1.2", "U101.64"),
    ("+3V3      U201.2  -> C202.1", "+3V3", "U201.2", "C202.1"),
    ("+3V3      U201.2  -> C201.1", "+3V3", "U201.2", "C201.1"),
    ("EN        U201.3  -> C203.1", "ESP32_EN", "U201.3", "C203.1"),
]


def nm2mm(v):
    return v / 1e6


class Net:
    def __init__(self, board, net):
        self.board, self.net = board, net
        self.idx = {}
        self.edges = []          # (a, b, ohms)

    def node(self, layer, x, y):
        key = (layer, x, y) if layer == "PAD" else (layer, round(x, 3), round(y, 3))
        if key not in self.idx:
            self.idx[key] = len(self.idx)
        return self.idx[key]

    def build(self):
        b, net = self.board, self.net
        tracks = [t for t in b.GetTracks() if t.GetNetname() == net]
        segs = [t for t in tracks if t.Type() == pcbnew.PCB_TRACE_T]
        vias = [t for t in tracks if t.Type() == pcbnew.PCB_VIA_T]
        pads = [p for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetname() == net]
        layers = {pcbnew.F_Cu: "F", pcbnew.B_Cu: "B"}
        # points where something attaches to a segment's interior (T-joins)
        attach = {id(s): [] for s in segs}
        ends = [(s.GetLayer(), s.GetStart()) for s in segs] + [(s.GetLayer(), s.GetEnd()) for s in segs]
        ends += [(L, v.GetPosition()) for v in vias for L in layers]
        for s in segs:
            a, e = s.GetStart(), s.GetEnd()
            half = s.GetWidth() / 2
            for L, p in ends:
                if L != s.GetLayer() or p == a or p == e:
                    continue
                d, t = _proj(a, e, p)
                if d <= half and 0 < t < 1:
                    attach[id(s)].append((t, p))
        for s in segs:
            L = layers[s.GetLayer()]
            pts = [(0.0, s.GetStart())] + sorted(attach[id(s)], key=lambda q: q[0]) + [(1.0, s.GetEnd())]
            w = nm2mm(s.GetWidth())
            for (t0, p0), (t1, p1) in zip(pts, pts[1:]):
                length = nm2mm((p1 - p0).EuclideanNorm())
                if length <= 0:
                    continue
                r = RHO * length / (w * T_CU)
                self.edges.append((self.node(L, nm2mm(p0.x), nm2mm(p0.y)),
                                   self.node(L, nm2mm(p1.x), nm2mm(p1.y)), r))
        for v in vias:
            p = v.GetPosition()
            d = nm2mm(v.GetDrillValue())
            r = RHO * BOARD_T / (math.pi * (d + PLATING) * PLATING)
            self.edges.append((self.node("F", nm2mm(p.x), nm2mm(p.y)),
                               self.node("B", nm2mm(p.x), nm2mm(p.y)), r))
        # pads: ideal node, tied to every track end / via inside the pad
        self.pad_node = {}
        for p in pads:
            ref = p.GetParentFootprint().GetReference() + "." + p.GetNumber()
            pn = self.node("PAD", ref, 0)
            self.pad_node.setdefault(ref, []).append(pn)
            for key, i in list(self.idx.items()):
                L = key[0]
                if L == "PAD":
                    continue
                lay = pcbnew.F_Cu if L == "F" else pcbnew.B_Cu
                if not p.IsOnLayer(lay):
                    continue
                pos = pcbnew.VECTOR2I(int(round(key[1] * 1e6)), int(round(key[2] * 1e6)))
                if p.HitTest(pos):
                    self.edges.append((pn, i, 1e-7))

    def resistance(self, a_ref, b_ref):
        if a_ref not in self.pad_node or b_ref not in self.pad_node:
            return None
        n = len(self.idx)
        G = np.zeros((n, n))
        # pads with several copies (same number twice) are one node
        for refs in self.pad_node.values():
            for x in refs[1:]:
                self.edges.append((refs[0], x, 1e-7))
        for a, b, r in self.edges:
            g = 1.0 / r
            G[a, a] += g
            G[b, b] += g
            G[a, b] -= g
            G[b, a] -= g
        A, B = self.pad_node[a_ref][0], self.pad_node[b_ref][0]
        # restrict to the component containing A
        comp, stack = {A}, [A]
        adj = {}
        for a, b, _ in self.edges:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
        while stack:
            u = stack.pop()
            for v in adj.get(u, []):
                if v not in comp:
                    comp.add(v)
                    stack.append(v)
        if B not in comp:
            return float("inf")
        keep = sorted(comp - {B})
        Gs = G[np.ix_(keep, keep)]
        I = np.zeros(len(keep))
        I[keep.index(A)] = 1.0
        V = np.linalg.solve(Gs, I)
        return V[keep.index(A)]


def _proj(a, e, p):
    ax, ay, ex, ey, px, py = a.x, a.y, e.x, e.y, p.x, p.y
    dx, dy = ex - ax, ey - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay), 0.0
    t = ((px - ax) * dx + (py - ay) * dy) / L2
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy)), t


def main():
    args = sys.argv[1:]
    path = BOARD
    if args[:1] == ["--board"]:
        path, args = args[1], args[2:]
    board = pcbnew.LoadBoard(path)
    jobs = REPORT if not args else [(" ".join(args), args[0], args[1], args[2])]
    cache = {}
    for label, net, a, b in jobs:
        if net not in cache:
            cache[net] = Net(board, net)
            cache[net].build()
        r = cache[net].resistance(a, b)
        txt = "pad not on net" if r is None else ("NOT CONNECTED" if r == float("inf") else "%6.1f mOhm" % (r * 1e3))
        print(f"{label:34} {txt}")


if __name__ == "__main__":
    main()
