"""Copper path length from GND pads to U101's exposed pad (pilink-93a).

Library, used by zones.py's gate and route.py's accept(); run directly to
print the table for a board:
    python3 scripts/gnd_paths.py [board.kicad_pcb] [--fill]

RP2350 DS 6.3.8.1: the regulator's high-current GND "must have a short as
possible, low impedance GND path back to the ... QFN GND pad", C_FILT's GND
likewise, and "the bottom layer under the regulator is a ground plane that
connects to the QFN GND central pad". A connectivity check passes a board
where that ground reaches the pad only through a few far vias, so this
measures it.

Method: both copper layers are rasterised at S px/mm (GND fills, GND
tracks, GND pads; GND vias and plated GND holes link the layers), and a
geodesic distance is grown out from the EP pad (8-neighbour chamfer, so a
path bends round signal tracks, not through them; a layer change costs
VIA_MM). The value for a pad is the shortest distance to any of its copper
cells. It is a path length along copper, not a resistance; a hairline neck
counts like a plane.
"""
import math
import os
import sys

import numpy as np
import pcbnew
from PIL import Image, ImageDraw

S = 10.0                 # raster, px/mm
O = 100.0                # board-local origin on the page (place.py)
BOARD_W, BOARD_H = 122.5, 50.0
VIA_MM = 0.0             # a layer change adds no length (it is reported as a count)
CAP_MM = 40.0            # stop growing past this (a value above it reads inf)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
# raster window: the board, cropped to CAP_MM round the EP when set_cap()
# allows (a path no longer than CAP_MM stays within CAP_MM of the EP)
X0, Y0, W, H = 0.0, 0.0, int(BOARD_W * S) + 1, int(BOARD_H * S) + 1


def set_window(cx, cy, cap):
    global X0, Y0, W, H, CAP_MM
    CAP_MM = cap
    x0, x1 = max(0.0, cx - cap), min(BOARD_W, cx + cap)
    y0, y1 = max(0.0, cy - cap), min(BOARD_H, cy + cap)
    X0, Y0, W, H = x0, y0, int((x1 - x0) * S) + 1, int((y1 - y0) * S) + 1

# what is measured, and the gate limits (mm along copper, vias)
EP = ("U101", "81")
# the regulator: PGND pin, C_IN, C_OUT, C_FILT GND pads (DS 6.3.8.1)
VREG_PADS = [("U101", "62"), ("C103", "2"), ("C104", "2"), ("C105", "2")]
VREG_MAX_MM, VREG_MAX_VIAS = 12.0, 1
# U101's decouplers next to the VREG block (the east column and C115):
# gated. C113/C115 land on the B.Cu the VREG strip joins to the EP. C111,
# C112, C118 sit between the east pin row's B.Cu escapes, the PSRAM_CS /
# GPIO41 B.Cu hops and the USB pair, which box their B.Cu in so it reaches
# the EP the long way round (~25mm on the committed routing; master
# 2b621ca: 7-10mm by this measure, via its 0.2mm GND traces; ebb6685:
# ~105mm). Their limit guards against that ebb6685-style failure; getting
# them back to master's figures is a follow-up bead.
DECOUPLERS = [("C113", "2"), ("C115", "2"), ("C111", "2"), ("C112", "2"), ("C118", "2")]
DECOUPLER_MAX_MM = {"C113.2": 15.0, "C115.2": 15.0,
                    "C111.2": 30.0, "C112.2": 30.0, "C118.2": 30.0}
# the rest: reported only. Most of them are as far on master (2b621ca): the
# B.Cu round U101 is cut by its own fan-out, so the plane they land on
# reaches the EP the long way round (pilink-93a follow-up).
OTHERS = [("C106", "2"), ("C107", "2"), ("C108", "2"), ("C109", "2"), ("C110", "2"),
          ("C114", "2"), ("C116", "2"), ("C117", "2")]


def _px(p):
    return ((pcbnew.ToMM(p.x) - O - X0) * S, (pcbnew.ToMM(p.y) - O - Y0) * S)


def _draw(d, sp, fill):
    for i in range(sp.OutlineCount()):
        o = sp.Outline(i)
        pts = [_px(o.CPoint(j)) for j in range(o.PointCount())]
        if len(pts) > 2:
            d.polygon(pts, fill=fill, outline=fill)
        for h in range(sp.HoleCount(i)):
            ho = sp.Hole(i, h)
            pts = [_px(ho.CPoint(j)) for j in range(ho.PointCount())]
            if len(pts) > 2:
                d.polygon(pts, fill=0)


def _pad_mask(pad, layer):
    im = Image.new("L", (W, H), 0)
    sp = pcbnew.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(sp, layer, 0, 5000, pcbnew.ERROR_INSIDE)
    _draw(ImageDraw.Draw(im), sp, 255)
    return np.array(im) > 0


def _masks(board):
    cu = {}
    for L in (F, B):
        im = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(im)
        for z in board.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() == "GND" and z.IsOnLayer(L):
                _draw(d, z.GetFilledPolysList(L), 255)
        for fp in board.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() == "GND" and p.IsOnLayer(L):
                    sp = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(sp, L, 0, 5000, pcbnew.ERROR_INSIDE)
                    _draw(d, sp, 255)
        for t in board.GetTracks():
            if t.GetNetname() != "GND":
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                x, y = _px(t.GetPosition())
                r = pcbnew.ToMM(t.GetWidth(F)) / 2 * S
                d.ellipse([x - r, y - r, x + r, y + r], fill=255)
            elif t.GetLayer() == L:
                a, c = _px(t.GetStart()), _px(t.GetEnd())
                r = pcbnew.ToMM(t.GetWidth()) / 2 * S
                d.line([a, c], fill=255, width=max(1, int(round(2 * r))))
                for q in (a, c):
                    d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=255)
        cu[L] = np.array(im) > 0
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    holes = [(t.GetPosition(), t.GetDrillValue()) for t in board.GetTracks()
             if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"]
    holes += [(p.GetPosition(), p.GetDrillSizeX()) for fp in board.GetFootprints()
              for p in fp.Pads()
              if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for pos, drill in holes:
        x, y = _px(pos)
        r = max(pcbnew.ToMM(drill) / 2 * S, 0.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    via = np.array(im) > 0
    return cu, via & cu[F] & cu[B]


def _shift(a, dy, dx, fillv):
    out = np.full_like(a, fillv)
    ys = slice(max(dy, 0), H + min(dy, 0))
    yd = slice(max(-dy, 0), H + min(-dy, 0))
    xs = slice(max(dx, 0), W + min(dx, 0))
    xd = slice(max(-dx, 0), W + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


def distance_field(board, cap=None):
    """(dist {layer: mm array}, vias {layer: count array}) from U101's EP,
    grown out to `cap` mm (default CAP_MM)."""
    fp = board.FindFootprintByReference(EP[0])
    c = fp.GetPosition()
    set_window(pcbnew.ToMM(c.x) - O, pcbnew.ToMM(c.y) - O, cap or CAP_MM)
    cu, via = _masks(board)
    src = np.zeros((H, W), bool)
    srcB = np.zeros((H, W), bool)
    for p in fp.Pads():       # the pad and its thermal vias' lands, both layers
        if p.GetNumber() == EP[1]:
            if p.IsOnLayer(F):
                src |= _pad_mask(p, F)
            if p.IsOnLayer(B):
                srcB |= _pad_mask(p, B)
    inf = np.float32(np.inf)
    D = {F: np.where(src & cu[F], 0, inf).astype(np.float32),
         B: np.where(srcB & cu[B], 0, inf).astype(np.float32)}
    V = {F: np.zeros((H, W), np.int16), B: np.zeros((H, W), np.int16)}
    steps = [(dy, dx, math.hypot(dy, dx) / S) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
             if dy or dx]
    for it in range(int(CAP_MM * S * 1.5)):
        changed = False
        for L in (F, B):
            d, v, m = D[L], V[L], cu[L]
            for dy, dx, w in steps:
                cand = _shift(d, dy, dx, inf) + np.float32(w)
                better = m & (cand < d - 1e-6) & (cand <= CAP_MM)
                if better.any():
                    changed = True
                    d[better] = cand[better]
                    v[better] = _shift(v, dy, dx, 0)[better]
        for a, c in ((F, B), (B, F)):
            cand = D[a] + np.float32(VIA_MM)
            better = via & (cand < D[c] - 1e-6)
            if better.any():
                changed = True
                D[c][better] = cand[better]
                V[c][better] = V[a][better] + 1
        if not changed:
            break
    return D, V


def pad_paths(board, pads, field=None):
    """{"REF.PIN": (mm, vias)} for each (ref, pin) in pads: the shortest
    copper path from that pad to the EP (inf if none within CAP_MM)."""
    D, V = field or distance_field(board)
    out = {}
    for ref, num in pads:
        fp = board.FindFootprintByReference(ref)
        best = (math.inf, 0)
        for p in fp.Pads():
            if p.GetNumber() != num:
                continue
            for L in (F, B):
                if not p.IsOnLayer(L):
                    continue
                m = _pad_mask(p, L)
                if not m.any():
                    continue
                d = np.where(m, D[L], np.inf)
                i = np.unravel_index(np.argmin(d), d.shape)
                if d[i] < best[0]:
                    best = (float(d[i]), int(V[L][i]))
        out[f"{ref}.{num}"] = best
    return out


def island_vias(board):
    """The VREG ground island's single-point vias (inside
    plane_keepout.VREG_F, the island's pour keepout)."""
    from plane_keepout import VREG_F
    xs, ys = [p[0] for p in VREG_F], [p[1] for p in VREG_F]
    out = []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND":
            x, y = pcbnew.ToMM(t.GetX()) - O, pcbnew.ToMM(t.GetY()) - O
            if min(xs) - 0.5 <= x <= max(xs) + 0.5 and min(ys) - 0.5 <= y <= max(ys) + 0.5:
                out.append((x, y))
    return out


def via_paths(board, field=None):
    """{"via (x, y)": (mm, vias)} for the island vias, measured on B.Cu."""
    D, V = field or distance_field(board)
    out = {}
    for x, y in island_vias(board):
        i, j = int(round((y - Y0) * S)), int(round((x - X0) * S))
        win = (slice(max(i - 2, 0), i + 3), slice(max(j - 2, 0), j + 3))
        d = D[B][win]
        k = np.unravel_index(np.argmin(d), d.shape)
        out[f"via ({x:.2f}, {y:.2f})"] = (float(d[k]), int(V[B][win][k]))
    return out


def table(board, field=None):
    field = field or distance_field(board)
    out = via_paths(board, field)
    out.update(pad_paths(board, VREG_PADS + DECOUPLERS + OTHERS, field))
    return out


def gate(board, field=None):
    """Problems (empty = pass): a VREG pad over VREG_MAX_MM / VREG_MAX_VIAS,
    or a decoupler over DECOUPLER_MAX_MM, from the EP along copper."""
    field = field or distance_field(board, max(VREG_MAX_MM, *DECOUPLER_MAX_MM.values()) + 5)
    problems = []
    for k, (mm, n) in pad_paths(board, VREG_PADS, field).items():
        if mm > VREG_MAX_MM or n > VREG_MAX_VIAS:
            problems.append(f"{k}: GND path to the U101 EP {mm:.1f}mm / {n} via(s) "
                            f"(limit {VREG_MAX_MM}mm / {VREG_MAX_VIAS})")
    for k, (mm, n) in pad_paths(board, DECOUPLERS, field).items():
        if mm > DECOUPLER_MAX_MM[k]:
            problems.append(f"{k}: GND path to the U101 EP {mm:.1f}mm / {n} via(s) "
                            f"(limit {DECOUPLER_MAX_MM[k]}mm)")
    return problems


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else os.path.join(here, "..", "pico-link-hw.kicad_pcb")
    b = pcbnew.LoadBoard(path)
    if "--fill" in sys.argv:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    cap = [float(a.split("=")[1]) for a in sys.argv if a.startswith("--cap=")]
    field = distance_field(b, cap[0] if cap else None)
    for k, (mm, n) in table(b, field).items():
        print(f"{k:20} {mm:6.1f} mm  {n} via(s)")
    probs = gate(b, field)
    for p in probs:
        print("FAIL:", p)
    print("gate", "failed" if probs else "passed")
