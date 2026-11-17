"""Join stray GND islands to the main ground with a short track (pilink-r1h).

Library, called by zones.py after the pours are filled and stitched.

Freerouting never sees GND (route.py), so it can box a fan-out via, a B.Cu
GND pad or a small pour fragment into a pocket of signal tracks on both
layers. zones.gnd_islands() finds such pockets; repair() then looks for the
shortest legal GND path from each one to the main ground on a 0.05mm raster
of both layers (a maze search: every non-GND pad, track, via, hole, the
board edge, the no-copper rule areas and the VREG/U101 pour keepouts are
obstacles, grown by CLEAR plus half the track width; a layer change needs
room for a via on both layers) and lays it as GND_W tracks plus vias.
The added copper is unlocked: nothing else on the board makes unlocked GND
items (GND is not routed), so zones.py removes them first on a re-run.
"""
import numpy as np
import pcbnew
from PIL import Image, ImageDraw

S = 20.0                 # raster, px/mm
O = 100.0                # board-local origin on the page (place.py)
BOARD_W, BOARD_H = 122.5, 50.0
GND_W = 0.25             # repair track width
VIA_D, VIA_DRILL = 0.6, 0.3
CLEAR = 0.23             # to foreign copper (net class clearance 0.2 + raster margin)
EDGE = 0.5               # to the board edge
VIA_COST = 30            # px of track a layer change is worth
F, B = pcbnew.F_Cu, pcbnew.B_Cu
W, H = int(BOARD_W * S), int(BOARD_H * S)


def _px(p):
    return ((pcbnew.ToMM(p.x) - O) * S, (pcbnew.ToMM(p.y) - O) * S)


def _draw(d, sp, fill):
    for i in range(sp.OutlineCount()):
        o = sp.Outline(i)
        pts = [_px(o.CPoint(j)) for j in range(o.PointCount())]
        if len(pts) > 2:
            d.polygon(pts, fill=fill)
        for h in range(sp.HoleCount(i)):
            ho = sp.Hole(i, h)
            pts = [_px(ho.CPoint(j)) for j in range(ho.PointCount())]
            if len(pts) > 2:
                d.polygon(pts, fill=255 - fill)


def _free(board, layer, grow):
    """True where a GND track centreline may run on `layer` (copper of any
    other net at least `grow` mm away)."""
    im = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(im)
    e = int((EDGE + grow) * S)
    d.rectangle([0, 0, W, e], fill=0)
    d.rectangle([0, H - e, W, H], fill=0)
    d.rectangle([0, 0, e, H], fill=0)
    d.rectangle([W - e, 0, W, H], fill=0)
    g = pcbnew.FromMM(grow)
    for z in board.Zones():
        if not z.IsOnLayer(layer):
            continue
        name = z.GetZoneName()
        block = (z.GetIsRuleArea() and (z.GetDoNotAllowTracks()
                                        or name.startswith(("KO_POUR_F_", "KO_L101"))))
        if not z.GetIsRuleArea() and z.GetNetname() != "GND":
            block = True          # another net's pour (U1's +3V3 spreader)
        if block:
            sp = pcbnew.SHAPE_POLY_SET()
            if z.GetIsRuleArea():
                sp = pcbnew.SHAPE_POLY_SET(z.Outline())
            else:
                sp = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(layer))
            sp.Inflate(g, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, 5000)
            _draw(d, sp, 0)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            npth = p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
            if p.GetNetname() == "GND" and not npth:
                continue
            if not (p.IsOnLayer(layer) or npth):
                continue
            sp = pcbnew.SHAPE_POLY_SET()
            if npth:
                c = p.GetPosition()
                r = p.GetDrillSizeX() / 2 + g
                x, y = _px(c)
                rp = r / 1e6 * S
                d.ellipse([x - rp, y - rp, x + rp, y + rp], fill=0)
                continue
            p.TransformShapeToPolygon(sp, layer, g, 5000, pcbnew.ERROR_OUTSIDE)
            _draw(d, sp, 0)
    for t in board.GetTracks():
        if t.GetNetname() == "GND":
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = _px(t.GetPosition())
            r = (pcbnew.ToMM(t.GetWidth(F)) / 2 + grow) * S
            d.ellipse([x - r, y - r, x + r, y + r], fill=0)
        elif t.GetLayer() == layer:
            a, c = _px(t.GetStart()), _px(t.GetEnd())
            r = (pcbnew.ToMM(t.GetWidth()) / 2 + grow) * S
            d.line([a, c], fill=0, width=max(1, int(2 * r)))
            for q in (a, c):
                d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=0)
    return np.array(im) > 0


def _mask(shapes):
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    for sp in shapes:
        _draw(d, sp, 255)
    return np.array(im) > 0


def _dil(m):
    r = m.copy()
    r[1:, :] |= m[:-1, :]
    r[:-1, :] |= m[1:, :]
    r[:, 1:] |= m[:, :-1]
    r[:, :-1] |= m[:, 1:]
    r[1:, 1:] |= m[:-1, :-1]
    r[:-1, :-1] |= m[1:, 1:]
    r[1:, :-1] |= m[:-1, 1:]
    r[:-1, 1:] |= m[1:, :-1]
    return r


def _search(free, via_ok, src, dst, max_iter=3000):
    """Breadth-first wave from src over free cells of both layers (layer
    change where via_ok, costing VIA_COST steps). Returns the cell path
    [(layer index, row, col), ...] from a dst cell back to src, or None."""
    INF = np.iinfo(np.int32).max
    dist = [np.full((H, W), INF, np.int32) for _ in (0, 1)]
    front = [src[i] & free[i] for i in (0, 1)]
    pending = []                       # (step it lands, layer, mask) via hops
    for i in (0, 1):
        dist[i][front[i]] = 0
    hit = None
    for step in range(1, max_iter):
        new = [None, None]
        for i in (0, 1):
            n = _dil(front[i]) & free[i] & (dist[i] == INF)
            dist[i][n] = step
            new[i] = n
        # layer changes found this step land VIA_COST steps later
        for i in (0, 1):
            j = 1 - i
            hop = front[i] & via_ok & (dist[j] == INF)
            if hop.any():
                pending.append((step - 1 + VIA_COST, j, hop))
        keep = []
        for s, j, m in pending:
            if s == step:
                m = m & (dist[j] == INF)
                dist[j][m] = step
                new[j] |= m
            else:
                keep.append((s, j, m))
        pending = keep
        front = new
        for i in (0, 1):
            h = new[i] & dst[i]
            if h.any():
                r, c = np.argwhere(h)[0]
                hit = (i, r, c)
                break
        if hit or (not new[0].any() and not new[1].any() and not pending):
            break
    if hit is None:
        return None
    path = [hit]
    i, r, c = hit
    while dist[i][r, c] > 0:
        d0 = dist[i][r, c]
        best = None
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (dr or dc) and 0 <= rr < H and 0 <= cc < W and dist[i][rr, cc] == d0 - 1:
                    best = (i, rr, cc)
                    break
            if best:
                break
        if best is None:
            j = 1 - i
            if via_ok[r, c] and dist[j][r, c] == d0 - VIA_COST:
                best = (j, r, c)
        if best is None:
            return None
        path.append(best)
        i, r, c = best
    return path


def _simplify(pts, tol=0.7):
    """Douglas-Peucker on raster points (px)."""
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    L = (dx * dx + dy * dy) ** 0.5 or 1.0
    k, dm = 0, -1.0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        dd = abs(dy * (x - x0) - dx * (y - y0)) / L
        if dd > dm:
            k, dm = i, dd
    if dm <= tol:
        return [pts[0], pts[-1]]
    return _simplify(pts[:k + 1], tol)[:-1] + _simplify(pts[k:], tol)


def _pt(col, row):
    return pcbnew.VECTOR2I(pcbnew.FromMM(float(O + (col + 0.5) / S)),
                           pcbnew.FromMM(float(O + (row + 0.5) / S)))


def _lay(board, path):
    """Tracks and vias along a cell path; returns (track mm, vias)."""
    net = board.FindNet("GND")
    runs, cur = [], [path[0]]
    for p in path[1:]:
        if p[0] != cur[-1][0]:
            runs.append(cur)
            cur = [p]
        else:
            cur.append(p)
    runs.append(cur)
    length, vias = 0.0, 0
    for k, run in enumerate(runs):
        layer = (F, B)[run[0][0]]
        pts = _simplify([(c, r) for _, r, c in run])
        for (c0, r0), (c1, r1) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(_pt(c0, r0))
            t.SetEnd(_pt(c1, r1))
            t.SetWidth(pcbnew.FromMM(GND_W))
            t.SetLayer(layer)
            t.SetNet(net)
            board.Add(t)
            length += ((c1 - c0) ** 2 + (r1 - r0) ** 2) ** 0.5 / S
        if k + 1 < len(runs):
            _, r, c = run[-1]
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(_pt(c, r))
            v.SetWidth(F, pcbnew.FromMM(VIA_D))
            v.SetDrill(pcbnew.FromMM(VIA_DRILL))
            v.SetLayerPair(F, B)
            v.SetNet(net)
            board.Add(v)
            vias += 1
    return length, vias


def remove_repairs(board):
    for t in list(board.GetTracks()):
        if t.GetNetname() == "GND" and not t.IsLocked():
            board.Remove(t)


def repair(board, components):
    """components: zones.gnd_components(board) -> (main, strays), each a
    dict {layer: [SHAPE_POLY_SET, ...]}. Joins each stray to the main
    ground; returns one line per stray."""
    main, strays = components
    if not strays:
        return []
    grow = CLEAR + GND_W / 2
    free = [_free(board, L, grow) for L in (F, B)]
    vg = int(round((VIA_D / 2 - GND_W / 2) * S)) + 1
    via_ok = free[0] & free[1]
    for _ in range(vg):            # erode: the via is wider than the track
        e = via_ok.copy()
        e[1:, :] &= via_ok[:-1, :]
        e[:-1, :] &= via_ok[1:, :]
        e[:, 1:] &= via_ok[:, :-1]
        e[:, :-1] &= via_ok[:, 1:]
        via_ok = e
    dst = [_mask(main[L]) for L in (F, B)]
    out = []
    for label, shapes in strays:
        src = [_mask(shapes[L]) for L in (F, B)]
        path = _search(free, via_ok, src, dst)
        if path is None:
            out.append(f"no legal path for {label}")
            continue
        mm, nv = _lay(board, path)
        out.append(f"joined {label}: {mm:.1f}mm of {GND_W}mm track, {nv} via(s)")
    return out
