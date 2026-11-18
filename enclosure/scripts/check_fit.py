#!/usr/bin/env python3
"""CAD-level fit check for the enclosure (pilink-7tm).

NOT the printed fit check (pilink-8hx.5). This renders every enclosure/*.scad
headlessly, builds a PCB envelope (board slab + per-component boxes) from
hardware/pico-link-hw.kicad_pcb, places everything in one "face frame" and
reports interference volumes / approximate minimum distances.

Run it through enclosure/scripts/check_fit.sh (docker, needs the preview image
for openscad + pcbnew + trimesh). Needs: openscad, pcbnew (KiCad python),
trimesh, numpy, manifold3d, scipy, rtree.

Face frame (the single mapping in enclosure/common.scad, read from there):
  X = board_x + MARGIN_X (2.5; left -> right)
  Q = QTOP - board_y     (QTOP 53; bottom of face = 0, top = FACE_H 56)
  Z = 0 at the outer face, increasing into the body (front shell 0..7.5,
      PCB 7.5..9.1, back shell outer face at Z = BODY_T = 14.1)
"""
import argparse
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import trimesh

# ---------------------------------------------------------------- scad utils


def scad_vars(path, env=None):
    """Evaluate top-level `NAME = expr;` numeric/list assignments (best effort),
    following `include <file.scad>` lines (relative to the including file) so
    constants from enclosure/common.scad are visible."""
    if env is None:
        env = {"max": max, "min": min, "tan": lambda d: math.tan(math.radians(d)),
               "cos": lambda d: math.cos(math.radians(d)),
               "sin": lambda d: math.sin(math.radians(d))}
    for line in open(path):
        inc = re.match(r"^include\s*<([^>]+)>", line)
        if inc:
            scad_vars(os.path.join(os.path.dirname(path), inc.group(1)), env)
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?);\s*(//.*)?$", line)
        if not m:
            continue
        name, expr = m.group(1), m.group(2)
        try:
            env[name] = eval(expr, {"__builtins__": {}}, env)
        except Exception:
            pass
    return env


def run_openscad(scad, out, defs=(), cwd=None):
    cmd = ["openscad", "-o", out]
    for d in defs:
        cmd += ["-D", d]
    cmd.append(scad)
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    log = p.stdout + p.stderr
    issues = [l for l in log.splitlines()
              if re.search(r"WARNING|ERROR|assert|Assertion|deprecated", l, re.I)]
    return p.returncode, issues, log


def strip_calls(src, dst, names):
    """Copy a .scad file without its top-level `name();` render calls so the
    module library can be included from a wrapper."""
    pat = re.compile(r"^(%s)\(\);\s*$" % "|".join(names))
    with open(src) as f, open(dst, "w") as g:
        for line in f:
            if not pat.match(line):
                g.write(line)


def load_stl(path):
    m = trimesh.load(path, force="mesh")
    m.merge_vertices()
    return m


# ------------------------------------------------------------------ geometry


def box(x0, x1, q0, q1, z0, z1):
    b = trimesh.creation.box(extents=[x1 - x0, q1 - q0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (q0 + q1) / 2, (z0 + z1) / 2])
    return b


def cyl(x, q, z0, z1, d, sections=32):
    c = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0, sections=sections)
    c.apply_translation([x, q, (z0 + z1) / 2])
    return c


def union(meshes):
    meshes = [m for m in meshes if m is not None]
    if not meshes:
        return None
    if len(meshes) == 1:
        return meshes[0]
    return trimesh.boolean.union(meshes, engine="manifold")


def mesh_volume(m):
    """|signed volume| from the divergence theorem, without trimesh's
    mass_properties: that also divides by the volume for center_mass, which
    raises a numpy divide-by-zero RuntimeWarning on a zero-volume mesh (e.g. an
    intersection that is only coincident faces on two perpendicular planes, so
    its bounding box is not flat)."""
    t = m.triangles
    return abs(float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum()) / 6.0)


def solid_bounds(m, min_vol=1e-3):
    """Bounds of the pieces of m that enclose real volume (boolean results can
    carry zero-volume coplanar-face sheets), or None if there are none."""
    if m is None or len(m.faces) == 0:
        return None
    pieces = [c for c in m.split(only_watertight=False) if mesh_volume(c) >= min_vol]
    if not pieces:
        return None
    return (np.min([c.bounds[0] for c in pieces], axis=0), np.max([c.bounds[1] for c in pieces], axis=0))


last_thickness = [0.0]
SLIVER_DEPTH_TOL = 0.02  # mm


def inter(a, b):
    """Return (volume, bbox-centre-or-None) of a intersect b."""
    if a is None or b is None:
        return 0.0, None
    lo = np.maximum(a.bounds[0], b.bounds[0])
    hi = np.minimum(a.bounds[1], b.bounds[1])
    if np.any(hi - lo <= 1e-6):
        return 0.0, None
    r = trimesh.boolean.intersection([a, b], engine="manifold")
    if r is None or len(r.faces) == 0:
        return 0.0, None
    # slivers thinner than 20 um are coincident-face / STL rounding contact, not overlap
    if np.min(r.bounds[1] - r.bounds[0]) < TOUCH_TOL:
        return 0.0, None
    v = mesh_volume(r)
    if v < 1e-6:
        return 0.0, None
    # penetration depth = smallest extent of the overlap's oriented bounding
    # box: ~the slab thickness for a flat sliver, ~the max depth for a wedge or
    # crescent (a mean thickness hides those; the 0.29mm PCB-corner overlap
    # had a 0.052mm mean)
    try:
        last_thickness[0] = float(r.bounding_box_oriented.primitive.extents.min())
    except Exception:
        last_thickness[0] = float(np.min(r.bounds[1] - r.bounds[0]))
    return v, ((r.bounds[0] + r.bounds[1]) / 2).round(1).tolist() + ["extent"] + (r.bounds[1] - r.bounds[0]).round(2).tolist()


def min_dist(a, b, n=20000):
    """Approximate minimum distance between two meshes (sampling-based, so it
    can overestimate by roughly the sample spacing; 0 => touching/overlap)."""
    from trimesh.proximity import closest_point
    pa = np.vstack([a.vertices, a.sample(n)])
    d1 = closest_point(b, pa)[1].min()
    lo, hi = a.bounds[0] - 6, a.bounds[1] + 6
    pb = np.vstack([b.vertices, b.sample(n * 10)])
    pb = pb[np.all((pb >= lo) & (pb <= hi), axis=1)]
    d2 = closest_point(a, pb)[1].min() if len(pb) else d1
    return float(min(d1, d2))


# --------------------------------------------------------------- PCB envelope

# Heights above the PCB surface, mm. Sources are noted; "assumed" = typical
# datasheet class value, not read from this project's own research.
HEIGHTS = [
    (r"C_0402|R_0402", 0.55),                 # 0402 cap/res typical max
    (r"0603", 0.95),                          # 0603 max
    (r"0805", 1.4),                           # 0805 cap/fuse, conservative
    (r"SOT-23-6", 1.45),
    (r"SOD-123", 1.35),
    (r"SOT-223", 1.8),
    (r"SOIC-8", 1.75),
    (r"USON-8", 0.6),
    (r"Crystal_SMD_3225", 0.9),
    (r"RP2350-QFN-80", 0.9),
    (r"LPS4018|CKCS4018", 1.8),               # 4x4x1.8 power inductors (assumed for Cenker)
    (r"SKRTL", 2.0),                          # Alps side-actuated SMD tact, assumed
    (r"FC-05B40P21H20", 2.0),                 # FPC connector, "H20" + proposal 6c "J501 ~2mm"
]
DEFAULT_H = 1.0
# EC11E18244AU terminal length measured from the mounting face to the tip:
# 3.5mm, the "3.5" dimension at the terminal end of the side view in Alps'
# EC11E Series catalogue, Drawing No.2 (tech.alpsalpine.com
# product_catalog_ec_01_ec11e_en_611f078659.pdf, update 2510). It starts at
# the housing's PCB-mounting face, so the protrusion past the board's back
# surface is 3.5 - board thickness (1.9 at 1.6mm).
ENCODER_LEAD_LEN = 3.5
# 2.54mm pin-header pin tail below the PCB: standard 3.0mm (assumed
# catalogue-class value, pilink-1x5; no J101 part drawing in this repo).
HEADER_TAIL_LEN = 3.0
TOUCH_TOL = 0.02  # mm

# pilink-s98: (LEAN_DEG, FLOAT_GAP, FRONT_FOOT_OFFSET) combinations the fin
# stand is re-rendered at; None = the file's default offset (front pads flush
# behind the rear-bottom edge). Below LEAN ~23 those pads would tip forward
# (back_shell.scad asserts), so the lower leans move them forward, which also
# exercises the fin toe running on under the bottom wall.
FIN_SWEEP = [(15, 0, 6), (15, 5, 6), (20, 0, 3), (25, 0, None), (25, 5, None),
             (30, 0, None), (30, 5, None), (40, 0, None)]


def sweep_key(lean, gap, off):
    return "bs_L%g_G%g" % (lean, gap) + ("" if off is None else "_F%g" % off)


def sweep_label(lean, gap, off):
    return "LEAN %g FLOAT %g" % (lean, gap) + ("" if off is None else " FRONT_FOOT_OFFSET %g" % off)

# Mass model for the tip-over estimate (pilink-s98). Printed parts are taken
# as solid (2mm walls are mostly perimeters); envelope boxes over-fill their
# components, hence the lower effective densities. g/cm3 == 1e-3 g/mm3.
DENSITY_PRINT = 1.24      # PLA (PETG 1.27)
DENSITY_FR4 = 1.85        # PCB slab
DENSITY_COMPONENT = 1.0   # courtyard x height boxes (mostly air around small parts)
DENSITY_DISPLAY = 0.9     # 59 x 42 x 3.3 stack box -> ~7.4 g, a 2.4" TFT module class figure (assumed)
DENSITY_SCREW = 7.8       # M2 steel
# EC11E18244AU detent torque, N.mm: 10 +/- 7 mN.m (Alps datasheet, pilink-g8a;
# .research/findings/2026-11-15-encoder-ec11e18244au-specs.md) -> nominal, worst.
KNOB_DETENT_TORQUE_NMM = (10.0, 17.0)


def rot_x(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    return m


def face_to_world(lean, body_t):
    """Face frame (Z into the body from the outer face) -> back_shell.scad's
    world frame: mirror Z into the back-shell local frame (bz = BODY_T - Z),
    then rotate([-LEAN_DEG, 0, 0])."""
    mz = np.eye(4)
    mz[2, 2], mz[2, 3] = -1.0, body_t
    return rot_x(-lean) @ mz


def body_shadow(bv, lean):
    """Everything a straight-on (horizontal, along -Z) front view cannot see
    because the body is in front of it: the body box (local [0,FACE_W] x
    [0,FACE_H] x [0,BODY_T], rounded corners ignored), leaned, swept 300mm
    back. Fin/pad material outside it is visible from the front."""
    # Grown by TOUCH_TOL so the shell's own outer faces sit strictly inside
    # it: coplanar faces otherwise leave zero-volume slivers in the difference
    # that spoil its bounds.
    t = TOUCH_TOL
    corners = np.array([[x, q, bz] for x in (-t, bv["FACE_W"] + t) for q in (-t, bv["FACE_H"] + t)
                        for bz in (-t, bv["BODY_T"] + t)])
    a = math.radians(lean)
    w = np.column_stack([corners[:, 0],
                         corners[:, 1] * math.cos(a) + corners[:, 2] * math.sin(a),
                         -corners[:, 1] * math.sin(a) + corners[:, 2] * math.cos(a)])
    return trimesh.convex.convex_hull(np.vstack([w, w - [0, 0, 300]]))


def height_for(fpid):
    for pat, h in HEIGHTS:
        if re.search(pat, fpid):
            return h, True
    return DEFAULT_H, False


def build_envelope(pcb_path, ev):
    """Return dict name -> (mesh, side, note) in the face frame + metadata."""
    import pcbnew
    b = pcbnew.LoadBoard(pcb_path)
    pts = []
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            pts += [(d.GetStart().x / 1e6, d.GetStart().y / 1e6), (d.GetEnd().x / 1e6, d.GetEnd().y / 1e6)]
    ox, oy = min(p[0] for p in pts), min(p[1] for p in pts)
    bw = max(p[0] for p in pts) - ox
    bh = max(p[1] for p in pts) - oy
    thick = b.GetDesignSettings().GetBoardThickness() / 1e6
    meta = {"board_w": bw, "board_h": bh, "board_t": thick, "origin": [ox, oy]}

    X0 = ev["MARGIN_X"]
    QTOP = ev["QTOP"]              # Q of board y=0 (53)
    ZF = ev["Z_PCB_FRONT"]         # 7.5
    ZB = ZF + thick                # PCB back surface (9.1)

    def fx(bx):
        return bx + X0

    def fq(by):
        return QTOP - by

    parts = {}
    parts["PCB"] = (box(fx(0), fx(bw), fq(bh), fq(0), ZF, ZB), "PCB", "board slab")

    def add_box(name, bx0, bx1, by0, by1, h, side, note):
        if side == "F":
            m = box(fx(bx0), fx(bx1), fq(by1), fq(by0), ZF - h, ZF)
        else:
            m = box(fx(bx0), fx(bx1), fq(by1), fq(by0), ZB, ZB + h)
        parts[name] = (m, side, note)

    unknown = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        fpid = f.GetFPIDAsString().split(":")[-1]
        side = "B" if f.IsFlipped() else "F"
        cy = f.GetCourtyard(f.GetLayer())
        if cy.OutlineCount():
            bb = cy.BBox()
            bx0, bx1 = bb.GetX() / 1e6 - ox, (bb.GetX() + bb.GetWidth()) / 1e6 - ox
            by0, by1 = bb.GetY() / 1e6 - oy, (bb.GetY() + bb.GetHeight()) / 1e6 - oy
        else:
            bx0 = bx1 = by0 = by1 = None
        cx, cy_ = f.GetX() / 1e6 - ox, f.GetY() / 1e6 - oy
        if ref == "SW303":
            cx, cy_ = ev["ENCODER_BOARD"]  # footprint origin is not the shaft axis; use front_shell.scad's shaft centre

        if ref.startswith("H"):
            continue  # mounting holes: screws modelled separately
        if ref.startswith("SW30") and "PTS645" in fpid:
            # Body 6.2x6.2 up to (5.0 - 1.5) = 3.5 (PR #56 review's off-axis
            # relief, assumed) + actuator d3.5 to 5.0 (SWITCH_HEIGHT_ABOVE_PCB).
            add_box(ref + ".body", cx - 3.1, cx + 3.1, cy_ - 3.1, cy_ + 3.1, 3.5, side, "PTS645 body (assumed 6.2x6.2x3.5)")
            parts[ref + ".actuator"] = (cyl(fx(cx), fq(cy_), ZF - 5.0, ZF, 3.5), side, "PTS645 actuator d3.5 to 5.0")
            # pad/courtyard area (flat, 0.3 high) so neighbouring checks see the SMD footprint
            add_box(ref + ".pads", bx0, bx1, by0, by1, 0.3, side, "PTS645 courtyard, flat")
            continue
        if ref == "SW303":
            # Alps EC11E18244AU: body 12.0x11.6, housing 4.5, bushing d7 to 11.5,
            # shaft d6 to 24.5 (front_shell.scad constants / encoder finding).
            add_box(ref + ".housing", cx - 6.0, cx + 6.0, cy_ - 5.8, cy_ + 5.8, 4.5, side, "EC11 housing 12.0x11.6x4.5")
            parts[ref + ".bushing"] = (cyl(fx(cx), fq(cy_), ZF - 11.5, ZF, 7.0), side, "EC11 bushing d7 to 11.5 (d7 UNCONFIRMED)")
            shaft = cyl(fx(cx), fq(cy_), ZF - 24.5, ZF, 6.0, 64)
            # D-flat on +X, 4.5 across, over the last 10mm from the tip (knob.scad / encoder finding)
            flat = box(fx(cx) + 1.5, fx(cx) + 4, fq(cy_) - 4, fq(cy_) + 4, ZF - 24.5 - 1, ZF - 24.5 + 10)
            shaft = trimesh.boolean.difference([shaft, flat], engine="manifold")
            parts[ref + ".shaft"] = (shaft, side, "EC11 D-shaft d6, flat 4.5 across x 10mm from tip, to 24.5")
            # THT leads on the back: pad bbox, protrusion = ENCODER_LEAD_LEN - board thickness
            pb = [p.GetBoundingBox() for p in f.Pads() if p.GetDrillSize().x > 0]
            if pb:
                x0 = min(p.GetX() for p in pb) / 1e6 - ox
                x1 = max(p.GetX() + p.GetWidth() for p in pb) / 1e6 - ox
                y0 = min(p.GetY() for p in pb) / 1e6 - oy
                y1 = max(p.GetY() + p.GetHeight() for p in pb) / 1e6 - oy
                lead_out = ENCODER_LEAD_LEN - thick
                parts[ref + ".leads"] = (box(fx(x0), fx(x1), fq(y1), fq(y0), ZB, ZB + lead_out), "B",
                                         "EC11 THT leads, %.1f protrusion (Alps drawing 3.5 terminal length - %.1f board)" % (lead_out, thick))
            continue
        if ref == "J101" and f.IsDNP():
            # pilink-cto: J101 is DNP (pads only; the 8.5mm-tall header would
            # pierce the 2mm face plate). Nothing is populated, so nothing to
            # check; the header is hand-fitted for bring-up with the shell open.
            continue
        if ref == "J101":
            add_box(ref + ".plastic", bx0, bx1, by0, by1, 2.5, side, "2.54 header plastic 2.5")
            for k, pad in enumerate(sorted(f.Pads(), key=lambda p: p.GetNumber())):
                px, py = pad.GetPosition().x / 1e6 - ox, pad.GetPosition().y / 1e6 - oy
                parts["%s.pin%d" % (ref, k + 1)] = (
                    box(fx(px - 0.32), fx(px + 0.32), fq(py + 0.32), fq(py - 0.32), ZF - 8.5, ZF),
                    side, "header pin, ASSUMED 6.0 above plastic (8.5 total) -- UNVERIFIED")
                parts["%s.tail%d" % (ref, k + 1)] = (
                    box(fx(px - 0.32), fx(px + 0.32), fq(py + 0.32), fq(py - 0.32), ZB, ZB + HEADER_TAIL_LEN),
                    "B", "header pin tail, assumed %.1f" % HEADER_TAIL_LEN)
            continue
        if ref == "U201":
            bx, by = ev["U201_BODY_X"], ev["U201_BODY_Y"]
            add_box(ref + ".module", bx[0], bx[1], by[0], by[1], ev["U201_MODULE_H"], side, "ESP32 module body 18x19.2x3.2 (F.Fab, not courtyard)")
            ux, uy = ev["U201_UFL"]
            add_box(ref + ".ufl_plug", ux - 1.3, ux + 1.3, uy - 1.3, uy + 1.3, ev["UFL_PLUG_TOP_H"], side, "mated U.FL plug 2.6x2.6 to 3.3 above host PCB")
            continue
        if ref == "J401":
            # Shell 9.0 x 3.2 centred on the anchor (what the back shell's cutout
            # is sized for), 6.5 tall. The 9.1x5.4 courtyard is wider than the body.
            add_box(ref, cx - 4.5, cx + 4.5, cy_ - 1.6, cy_ + 1.6, 6.5, side, "USB-C shell 9.0x3.2x6.5 (courtyard 9.1x5.4 not used)")
            continue
        if bx0 is None:
            unknown.append(ref + " (no courtyard)")
            continue
        h, known = height_for(fpid)
        if not known:
            unknown.append("%s %s -> default %.1f" % (ref, fpid, DEFAULT_H))
        add_box(ref, bx0, bx1, by0, by1, h, side, "courtyard x %.2fmm%s" % (h, "" if known else " (DEFAULT height)"))

    # Mounting screws: M2 pan head d4.0 x 1.6 on the front, shank d2 down into
    # the insert pocket (INSERT_LEN 4.0 below the PCB back surface). Assumed.
    for i, (hx, hy) in enumerate(ev["PCB_MOUNT_HOLES_BOARD"]):
        parts["screw_H%d.head" % (i + 1)] = (cyl(fx(hx), fq(hy), ZF - 1.6, ZF, 4.0), "F", "M2 pan head d4.0x1.6 (assumed)")
        parts["screw_H%d.shank" % (i + 1)] = (cyl(fx(hx), fq(hy), ZF, ZB + ev["INSERT_LEN"], 2.0), "S", "M2 shank into insert (assumed length)")

    # Display module stack: panel shadow (common.scad PANEL_BOARD_*, pilink-4qc:
    # x[34.12,93.12] y[4,46]), 3.3mm above the PCB front (proposal 6c "3.3
    # panel stack").
    px0, px1, py0, py1 = ev["PANEL_BOX"]
    add_box("DISPLAY", px0, px1, py0, py1, 3.3, "F", "panel shadow x%.2f-%.2f y%.0f-%.0f x 3.3 stack (common.scad / proposal 6c)" % (px0, px1, py0, py1))
    return parts, meta, unknown


# ----------------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--enclosure", default="enclosure")
    ap.add_argument("--pcb", default="hardware/pico-link-hw.kicad_pcb")
    ap.add_argument("--work", default=None)
    ap.add_argument("--json", help="write results to this JSON file")
    ap.add_argument("--reuse", action="store_true", help="reuse STLs already in --work (dev speed-up)")
    ap.add_argument("--keep-stl", action="store_true", help="(informational) STLs stay in --work")
    args = ap.parse_args()
    enc = os.path.abspath(args.enclosure)
    import tempfile
    work = os.path.abspath(args.work or tempfile.mkdtemp(prefix="fitcheck"))
    os.makedirs(work, exist_ok=True)
    results = []   # (pair, status, detail)
    failed = []

    def rec(pair, status, detail=""):
        results.append((pair, status, detail))
        print("%-5s %-58s %s" % (status, pair, detail), flush=True)

    # ---------------------------------------------------- 1. render all scad
    print("\n=== 1. OpenSCAD render of every enclosure/*.scad ===")
    renders = {}
    jobs = []
    for scad in sorted(glob.glob(os.path.join(enc, "*.scad"))):
        n = os.path.basename(scad)[:-5]
        if n == "common":      # shared constants/functions only, no geometry
            continue
        if n == "back_shell":
            jobs += [("back_shell[assembly]", scad, [], "bs_asm"),
                     ("back_shell[PART=back_shell]", scad, ['PART="back_shell"'], "bs_back")]
            # pilink-s98: the fin stand must regenerate from LEAN_DEG / FLOAT_GAP
            for lean, gap, off in FIN_SWEEP:
                defs = ['PART="back_shell"', "LEAN_DEG=%g" % lean, "FLOAT_GAP=%g" % gap]
                if off is not None:
                    defs.append("FRONT_FOOT_OFFSET=%g" % off)
                jobs.append(("back_shell[PART=back_shell %s]" % sweep_label(lean, gap, off), scad, defs,
                             sweep_key(lean, gap, off)))
        else:
            jobs.append((n, scad, [], n))
    render_fail = False
    for label, scad, defs, key in jobs:
        out = os.path.join(work, key + ".stl")
        rc, issues, log = (0, [], "") if (args.reuse and os.path.exists(out)) else run_openscad(scad, out, defs)
        ok = rc == 0 and os.path.exists(out)
        info = ""
        if ok:
            m = load_stl(out)
            info = "watertight=%s vol=%.1f mm3 bbox=%s" % (m.is_watertight, m.volume, (m.bounds[1] - m.bounds[0]).round(1).tolist())
            renders[key] = m
        rec("render " + label, "OK" if ok and not issues else ("FAIL" if not ok else "WARN"), info)
        for l in issues:
            print("      !", l[:200])
            render_fail = True
        if not ok:
            render_fail = True
            failed.append("render " + label)

    # ------------------------------------- 2. component-frame renders (wrappers)
    print("\n=== 2. Per-part renders in the face frame ===")
    fv = scad_vars(os.path.join(enc, "front_shell.scad"))
    bv = scad_vars(os.path.join(enc, "back_shell.scad"))
    kv = scad_vars(os.path.join(enc, "knob.scad"))
    pv = scad_vars(os.path.join(enc, "button_plunger.scad"))
    av = scad_vars(os.path.join(enc, "antenna_mount.scad"))
    BODY_T = bv["BODY_T"]

    def wrapper(name, src, calls, body, defs=()):
        lib = os.path.join(work, "lib_" + name + ".scad")
        strip_calls(os.path.join(enc, src), lib, calls)
        shutil.copy(os.path.join(enc, "common.scad"), os.path.join(work, "common.scad"))
        w = os.path.join(work, "w_" + name + ".scad")
        open(w, "w").write("include <%s>\n%s\n" % (lib, body))
        out = os.path.join(work, "w_" + name + ".stl")
        rc, issues, log = (0, [], "") if (args.reuse and os.path.exists(out)) else run_openscad(w, out, defs)
        if rc != 0 or not os.path.exists(out):
            print("      wrapper render failed:", name, log[-400:])
            failed.append("wrapper " + name)
            return None
        for l in issues:
            print("      !", name, l[:200])
        return load_stl(out)

    front = renders.get("front_shell")
    back = wrapper("back", "back_shell.scad", [], "translate([0,0,BODY_T]) mirror([0,0,1]) back_shell_local();", ['PART="none"'])
    spool = wrapper("spool", "back_shell.scad", [], "translate([0,0,BODY_T]) mirror([0,0,1]) pigtail_spool();", ['PART="none"'])
    # pilink-s98: the fins (+ pads) alone, world frame -> face frame
    fins = wrapper("fins", "back_shell.scad", [], "translate([0,0,BODY_T]) mirror([0,0,1]) rotate([LEAN_DEG,0,0]) fins();", ['PART="none"'])
    if fins is not None and fins.volume < 0:
        fins.invert()
    plunger = wrapper("plunger", "button_plunger.scad", ["button_plungers_x4"], "button_plunger();")
    plunger_pr = wrapper("plunger_pressed", "button_plunger.scad", ["button_plungers_x4"], "button_plunger();", ["PREVIEW_PRESSED=true"])
    knob = wrapper("knob", "knob.scad", ["knob"], "knob();")
    ant = wrapper("antenna", "antenna_mount.scad", ["demo_assembly"], "antenna_mount();")
    for nm, m in (("front (face frame)", front), ("back (face frame, mirrored in Z)", back), ("pigtail spool", spool), ("fins (face frame)", fins),
                  ("plunger", plunger), ("knob", knob), ("antenna mount", ant)):
        if m is not None:
            print("  %-34s vol=%8.1f bbox lo=%s hi=%s" % (nm, m.volume, m.bounds[0].round(2).tolist(), m.bounds[1].round(2).tolist()))
    if back is not None and back.volume < 0:
        back.invert()

    # ------------------------------------------------------------ 3. envelope
    print("\n=== 3. PCB envelope ===")
    ev = {
        "MARGIN_X": bv["MARGIN_X"],
        "QTOP": bv["QTOP"],
        "PANEL_BOX": (fv["PANEL_BOARD_X0"], fv["PANEL_BOARD_X1"], fv["PANEL_BOARD_Y0"], fv["PANEL_BOARD_Y1"]),
        "Z_PCB_FRONT": fv["FRONT_SHELL_DEPTH"],
        "U201_BODY_X": bv["U201_BODY_X"], "U201_BODY_Y": bv["U201_BODY_Y"],
        "U201_MODULE_H": bv["U201_MODULE_H"], "UFL_PLUG_TOP_H": bv["UFL_PLUG_TOP_H"],
        "U201_UFL": bv["U201_UFL_BOARD_ASSUMED"],
        "ENCODER_BOARD": (fv["ENCODER_BOARD_CX"], fv["ENCODER_BOARD_CY"]),
        "PCB_MOUNT_HOLES_BOARD": bv["PCB_MOUNT_HOLES_BOARD"], "INSERT_LEN": bv["INSERT_LEN"],
    }
    parts, meta, unknown = build_envelope(os.path.abspath(args.pcb), ev)
    print("  board outline %.2f x %.2f x %.2f mm (from Edge.Cuts)" % (meta["board_w"], meta["board_h"], meta["board_t"]))
    print("  %d envelope bodies; PCB at Z %.1f..%.1f; frame: X=bx+%.1f, Q=%.1f-by" % (
        len(parts), ev["Z_PCB_FRONT"], ev["Z_PCB_FRONT"] + meta["board_t"], ev["MARGIN_X"], ev["QTOP"]))
    for u in unknown:
        print("  note: default/missing height ->", u)
    if abs(meta["board_w"] - bv["BOARD_W"]) > 0.01 or abs(meta["board_h"] - bv["BOARD_H"]) > 0.01:
        rec("board outline vs scad BOARD_W/H", "FAIL", "pcb %.2fx%.2f vs scad %.2fx%.2f" % (meta["board_w"], meta["board_h"], bv["BOARD_W"], bv["BOARD_H"]))
    else:
        rec("board outline vs scad BOARD_W/H", "OK", "%.0f x %.0f" % (meta["board_w"], meta["board_h"]))

    def group(pred):
        return union([m for n, (m, s, _) in parts.items() if pred(n, s)])

    # structured sub-groups
    pcb = parts["PCB"][0]
    enc_parts = [n for n in parts if n.startswith("SW303")]
    non_screw = lambda n: not n.startswith("screw_") and n != "PCB"
    env_all = group(lambda n, s: non_screw(n))
    env_front_side = group(lambda n, s: non_screw(n) and s == "F")
    env_back_side = group(lambda n, s: non_screw(n) and s == "B")

    def check(pair, a, b, mode="vol", note="", expect_zero=True, dist=False, contact_ok=False):
        v, loc = inter(a, b)
        # Mating-face contact is only excused when the overlap is a real sliver:
        # < 0.25 mm3 AND a penetration depth (min oriented-bbox extent) of at
        # most 0.02mm (STL/coincident-face noise class; real mating slivers
        # measure ~0.005mm). Anything deeper, however small in volume, is a
        # real interference and FAILs.
        thk = last_thickness[0]
        if v > 1e-3 and contact_ok and v < 0.25 and thk <= SLIVER_DEPTH_TOL:
            rec(pair, "INFO", "contact only (%.3f mm3 sliver, depth %.3fmm, mating faces by design) %s" % (v, thk, note))
            return 0.0
        if v > 1e-3:
            rec(pair, "FAIL" if expect_zero else "INFO", "overlap %.3f mm3 (depth %.3fmm) at (X,Q,Z)~%s %s" % (v, last_thickness[0], loc, note))
            if expect_zero:
                failed.append(pair)
            return v
        d = ""
        if dist:
            try:
                d = "min dist ~%.2f mm" % min_dist(a, b)
            except Exception as e:  # pragma: no cover
                d = "(dist n/a: %s)" % e
        rec(pair, "OK", ("no overlap; " + d + " " + note).strip())
        return 0.0

    print("\n=== 4. Interference checks (face frame) ===")
    # --- envelope vs shells
    if front is not None and back is not None:
        check("PCB slab vs front shell", pcb, front, dist=True)
        check("PCB slab vs back shell", pcb, back, dist=True,
              note="(board %.1f wide vs back cavity %.1f)" % (meta["board_w"], bv["FACE_W"] - 2 * bv["WALL_T"]))
        check("front shell vs back shell", front, back, note="(butt joint at Z=7.5)")
        # per-component, only report overlaps
        bad = 0
        for n, (m, s, note) in parts.items():
            if n == "PCB":
                continue
            for sh_name, sh in (("front", front), ("back", back)):
                v, loc = inter(m, sh)
                if v > 1e-3:
                    bad += 1
                    rec("%s vs %s shell" % (n, sh_name), "FAIL", "overlap %.3f mm3 at ~%s  [%s]" % (v, loc, note))
                    failed.append("%s vs %s shell" % (n, sh_name))
        if not bad:
            rec("all %d envelope bodies vs front+back shell" % (len(parts) - 1), "OK", "no overlaps")
        # minimum clearances worth knowing
        for label, grp, sh in (("B-side components", env_back_side, back),):
            try:
                rec("min clearance: " + label + " to own shell", "INFO", "~%.2f mm" % min_dist(grp, sh, 8000))
            except Exception as e:
                rec("min clearance: " + label, "INFO", "n/a %s" % e)
        # specific named items
        def part(n):
            return parts[n][0]
        encs = union([parts[n][0] for n in enc_parts])
        check("encoder (housing+bushing+shaft) vs front shell", encs, front, dist=True, note="(through the 8.5 hole)")
        screws = {i: union([part("screw_H%d.head" % i), part("screw_H%d.shank" % i)]) for i in (1, 2, 3, 4)}
        for i in (1, 2, 3, 4):
            check("screw H%d vs front shell" % i, screws[i], front, dist=True)
            check("screw H%d vs back shell (bosses/inserts)" % i, screws[i], back, dist=True)
            check("screw H%d vs envelope components" % i, screws[i], env_all)
        check("display stack vs front shell (pocket/ledge)", part("DISPLAY"), front, dist=True)
        check("U201 module+plug vs back shell (relief pocket)", union([part("U201.module"), part("U201.ufl_plug")]), back, dist=True)
        check("J401 body vs back shell (cutout/boss)", part("J401"), back, dist=True)
        if "J101.pin1" in parts:   # absent when J101 is DNP (pilink-cto)
            check("J101 header pins vs front shell", union([part("J101.pin%d" % k) for k in (1, 2, 3)]), front, dist=True,
                  note="(pin height ASSUMED, see envelope notes)")
    # --- spool
    if spool is not None:
        env_back_all = union([env_back_side, pcb])
        check("pigtail spool vs PCB back + B-side components", spool, env_back_all, dist=True)
    # --- plungers
    pl = {}
    if plunger is not None and front is not None:
        BTN = [("Y", fv["BTN_Y"]), ("X", fv["BTN_X"]), ("B", fv["BTN_B"]), ("A", fv["BTN_A"])]
        for nm, (bx, by) in BTN:
            m = plunger.copy()
            m.apply_translation([bx + ev["MARGIN_X"], ev["QTOP"] - by, 0])
            pl[nm] = m
        switches_body = group(lambda n, s: n.startswith("SW30") and n.endswith(".body"))
        switches_all = group(lambda n, s: n.startswith("SW30") and (n.endswith(".body") or n.endswith(".actuator")))
        others = group(lambda n, s: non_screw(n) and not n.startswith("SW30") and s == "F")
        for nm in "YXBA":
            check("plunger %s vs front shell (bore / panel ledge)" % nm, pl[nm], front, dist=True, note="(rest position)")
        check("plungers vs each other", union([pl["Y"]]), union([pl["X"], pl["B"], pl["A"]]), dist=True)
        check("plungers (rest) vs switches body+actuator", union(list(pl.values())), switches_all,
              note="(stem stops WORKING_CLEARANCE short of the actuator)", dist=True)
        check("plungers (rest) vs other F-side components", union(list(pl.values())), union([others, part("DISPLAY"), screws[1], screws[2], screws[3], screws[4]]))
        if plunger_pr is not None:
            plp = []
            for nm, (bx, by) in BTN:
                m = plunger_pr.copy()
                m.apply_translation([bx + ev["MARGIN_X"], ev["QTOP"] - by, 0])
                plp.append(m)
            allp = union(plp)
            check("plungers (fully pressed) vs front shell", allp, front, note="(PREVIEW_PRESSED=true)")
            check("plungers (fully pressed) vs switch bodies (flange ring)", allp, switches_body)
            rec("plungers (fully pressed) vs actuators", "INFO",
                "contact intended (overlap %.3f mm3 = actuator travel)" % inter(allp, group(lambda n, s: n.endswith(".actuator") and n.startswith("SW30")))[0])
    # --- knob
    k = None
    if knob is not None and front is not None:
        kx, ky = fv["ENCODER_BOARD_CX"] + ev["MARGIN_X"], ev["QTOP"] - fv["ENCODER_BOARD_CY"]
        kg = kv["KNOB_GAP"]
        T = np.eye(4)
        T[2, 2] = -1.0           # knob +z (up from underside) -> face-frame -Z (outward)
        T[:3, 3] = [kx, ky, -kg]
        k = knob.copy()
        k.apply_transform(T)
        if k.volume < 0:
            k.invert()
        check("knob vs front shell (face)", k, front, dist=True, note="(knob gap %.1f)" % kg)
        encs2 = union([parts[n][0] for n in enc_parts if n.endswith((".bushing", ".shaft"))])
        check("knob vs encoder bushing/shaft model", k, encs2, dist=True, note="(shaft tip bottoms in bore: touching expected)")
        if plunger is not None:
            check("knob vs plungers", k, union(list(pl.values())), dist=True)
    # --- antenna mount
    a = None
    if ant is not None and front is not None and back is not None:
        lo, hi = ant.bounds
        wall_inner_q = fv["FACE_H"] - fv["WALL"]            # 54
        win0, win1 = fv["FACE_T"], BODY_T - bv["BACK_WALL_T"]  # inner face .. inner back wall
        span = hi[1] - lo[1]
        d0 = (win0 + win1) / 2 - (lo[1] + hi[1]) / 2
        T = np.array([[1, 0, 0, av["MOUNT_X_MIN"]], [0, 0, -1, wall_inner_q], [0, 1, 0, d0], [0, 0, 0, 1.0]])
        a = ant.copy()
        a.apply_transform(T)
        print("  antenna mount: local Y span %.1f mm vs top-wall cavity window %.1f mm (Z %.1f..%.1f), centred; placed at X +%.2f (MOUNT_X_MIN)" % (
            span, win1 - win0, win0, win1, av["MOUNT_X_MIN"]))
        print("  (placement ASSUMED: local Z -> down from inner top wall Q=%.0f, local Y centred in the cavity depth; the scad has no real placement)" % wall_inner_q)
        rec("antenna mount depth span fits top-wall cavity", "OK" if span <= win1 - win0 else "FAIL",
            "%.2f mm span vs %.2f mm available" % (span, win1 - win0))
        if span > win1 - win0:
            failed.append("antenna mount depth span")
        check("antenna mount vs front shell", a, front, dist=True, note="(touches top-wall inner surface by design)")
        check("antenna mount vs back shell", a, back, dist=True)
        check("antenna mount vs PCB envelope (slab+components)", a, union([pcb, env_all]), dist=True)
    # --- board clearance to the cavity walls, all four sides (pilink-6lz)
    # Edge.Cuts tolerance (JLCPCB +/-0.2mm) and the FDM wall tolerance
    # (+/-0.1-0.2mm) are stacked below; the nominal clearance must exceed it.
    CLEAR_MIN = 0.3   # mm nominal required per side (0.2 JLCPCB outline + ~0.1 FDM, one-sided)
    CLEAR_WORST = 0.4  # mm: JLCPCB 0.2 + FDM 0.2 on the same side
    if back is not None:
        inner = {
            "left":   bv["WALL_T"],
            "right":  bv["FACE_W"] - bv["WALL_T"],
            "bottom": bv["WALL_T"],
            "top":    bv["FACE_H"] - bv["WALL_T"],
        }
        gaps = {
            "left":   ev["MARGIN_X"] - inner["left"],
            "right":  inner["right"] - (ev["MARGIN_X"] + meta["board_w"]),
            "bottom": (ev["QTOP"] - meta["board_h"]) - inner["bottom"],
            "top":    inner["top"] - ev["QTOP"],
        }
        for side, g in gaps.items():
            rec("board edge vs cavity wall, " + side, "OK" if g >= CLEAR_MIN else "WARN",
                "%.2f mm nominal clearance (%.2f mm worst case after the +/-0.2 JLCPCB outline + FDM wall tolerance)" % (g, g - CLEAR_WORST))
        # centred in the shell, both axes
        rec("board centred in cavity (X)", "OK" if abs(gaps["left"] - gaps["right"]) < 0.01 else "FAIL",
            "left %.2f / right %.2f" % (gaps["left"], gaps["right"]))
        rec("board centred in cavity (Y)", "OK" if abs(gaps["bottom"] - gaps["top"]) < 0.01 else "FAIL",
            "bottom %.2f / top %.2f" % (gaps["bottom"], gaps["top"]))
        if abs(gaps["left"] - gaps["right"]) >= 0.01:
            failed.append("board centred X")
        if abs(gaps["bottom"] - gaps["top"]) >= 0.01:
            failed.append("board centred Y")

    # --- face-centring of window / knob / diamond (pilink-4qc / pilink-6lz)
    def fxq(bx, by):
        return bx + ev["MARGIN_X"], ev["QTOP"] - by
    wx, wq = fxq(fv["AA_BOARD_CX"], fv["AA_BOARD_CY"])
    ok_w = abs(wx - fv["FACE_W"] / 2) < 0.01 and abs(wq - fv["FACE_H"] / 2) < 0.01
    rec("display window centred on the face", "OK" if ok_w else "FAIL",
        "window (%.2f, %.2f) vs face centre (%.2f, %.2f)" % (wx, wq, fv["FACE_W"] / 2, fv["FACE_H"] / 2))
    if not ok_w:
        failed.append("window centring")
    ky = fxq(fv["ENCODER_BOARD_CX"], fv["ENCODER_BOARD_CY"])[1]
    dy = fxq(*fv["BTN_X"])[1]
    ok_l = abs(ky - fv["FACE_H"] / 2) < 0.01 and abs(dy - fv["FACE_H"] / 2) < 0.01 and abs(fxq(*fv["BTN_B"])[1] - dy) < 0.01
    rec("knob and diamond on the face horizontal centreline", "OK" if ok_l else "FAIL",
        "knob Q %.2f, diamond X/B Q %.2f, face centre Q %.2f" % (ky, dy, fv["FACE_H"] / 2))
    if not ok_l:
        failed.append("knob/diamond centreline")
    # --- pigtail crossing (pilink-6lz): a straight d1.13 probe through the
    # notch across the PCB plane, centred in the notch.
    if front is not None and back is not None:
        cable_d = av["ANTENNA_CABLE_DIAMETER"]
        gap_plain = (fv["FACE_H"] - fv["WALL"]) - ev["QTOP"]
        qmid = (ev["QTOP"] + fv["FACE_H"] - fv["WALL"] + fv["PIGTAIL_NOTCH_DEPTH"]) / 2.0  # centre of board edge .. notch top
        xmid = (fv["PIGTAIL_NOTCH_X0"] + fv["PIGTAIL_NOTCH_X1"]) / 2.0
        probe = cyl(xmid, qmid, fv["PIGTAIL_NOTCH_Z0"] + 0.1, fv["PIGTAIL_NOTCH_Z1"] - 0.1, cable_d, 16)
        # centre the probe vertically in the notch+gap crossing region
        probe_ok = True
        for nm, other in (("front", front), ("back", back), ("PCB", pcb)):
            v, _ = inter(probe, other)
            if v > 1e-3:
                probe_ok = False
                rec("pigtail probe d%.2f vs %s" % (cable_d, nm), "FAIL", "overlap %.3f mm3" % v)
                failed.append("pigtail probe vs " + nm)
        rec("pigtail d%.2f probe crosses PCB plane via top-wall notch" % cable_d, "OK" if probe_ok else "FAIL",
            "plain top-edge gap %.2f mm (< d%.2f, so the notch is needed); notch crossing height %.2f mm at face X %.1f" % (
                gap_plain, cable_d, gap_plain + fv["PIGTAIL_NOTCH_DEPTH"], xmid))
        # the unnotched gap really is too small (sanity: why the notch exists)
        rec("plain top-edge gap vs mount stack + coax", "INFO",
            "gap %.2f mm vs lip %.1f + element %.1f + coax %.2f = %.2f mm" % (
                gap_plain, av["LIP_HEIGHT"], av["ANTENNA_ELEMENT_THICKNESS_NOMINAL"], cable_d,
                av["LIP_HEIGHT"] + av["ANTENNA_ELEMENT_THICKNESS_NOMINAL"] + cable_d))
    # --- fin stand (pilink-s98)
    LEAN = bv["LEAN_DEG"]
    F2W = face_to_world(LEAN, BODY_T)
    pad_r = bv["FOOT_PAD_D"] / 2
    if fins is not None:
        cav = box(bv["WALL_T"], bv["FACE_W"] - bv["WALL_T"], bv["WALL_T"], bv["FACE_H"] - bv["WALL_T"],
                  BODY_T - bv["BACK_SHELL_DEPTH"], BODY_T - bv["WALL_T"])
        check("fins vs back-shell cavity (must stay outside)", fins, cav, dist=True)
        if front is not None:
            check("fins vs front shell", fins, front, dist=True)
        check("fins vs PCB slab + all envelope bodies", fins, union([pcb, env_all]), dist=True)
        # USB-C: a max-spec plug overmould (USB-IF Type-C rev 1.2: 12.35 x 6.5)
        # straight back out of the opening, then the cable dropping to the
        # table between the fins (world frame). Centre from the J401 envelope.
        jb = parts["J401"][0].bounds
        jx, jq = (jb[0][0] + jb[1][0]) / 2, (jb[0][1] + jb[1][1]) / 2
        plug = box(jx - 6.175, jx + 6.175, jq - 3.25, jq + 3.25, BODY_T - bv["USBC_MATING_BZ"], BODY_T + 60)
        check("USB-C plug overmould 12.35x6.5, 60mm straight back, vs fins", plug, fins, dist=True)
        fins_w = fins.copy()
        fins_w.apply_transform(F2W)
        a_ = math.radians(LEAN)
        ey = jq * math.cos(a_) + bv["USBC_MATING_BZ"] * math.sin(a_)
        ez = -jq * math.sin(a_) + bv["USBC_MATING_BZ"] * math.cos(a_)
        drop = trimesh.creation.box(extents=[12.35, ey + bv["FLOAT_GAP"] + 5, 100])
        drop.apply_translation([jx, (ey - bv["FLOAT_GAP"] - 5) / 2, ez - 50])
        check("USB-C cable corridor 12.35 wide, exit -> table, 100mm back, vs fins (world)", drop, fins_w, dist=True)
        notch = box(bv["PIGTAIL_NOTCH_X0"], bv["PIGTAIL_NOTCH_X1"], bv["FACE_H"] - bv["WALL_T"],
                    bv["FACE_H"] - bv["WALL_T"] + bv["PIGTAIL_NOTCH_DEPTH"], bv["PIGTAIL_NOTCH_Z0"], bv["PIGTAIL_NOTCH_Z1"])
        check("antenna pigtail notch (top wall) vs fins", notch, fins, dist=True)
    # LEAN_DEG x FLOAT_GAP sweep: the fin bottoms land at Y = -FLOAT_GAP, the
    # rear end at the same Z, and the only material a straight-on front view
    # can see at FLOAT_GAP 0 is the front pads' lip under the bottom edge.
    for lean, gap, off in FIN_SWEEP:
        m = renders.get(sweep_key(lean, gap, off))
        ffz = bv["FRONT_FOOT_Z"] if off is None else off - pad_r   # this render's front foot centre
        if m is None:
            continue
        lo, hi = m.bounds
        rear_z = bv["REAR_FOOT_Z"] - pad_r
        geo_ok = abs(lo[1] + gap) < 0.02 and abs(lo[2] - rear_z) < 0.05 and lo[0] > -1e-6 and hi[0] < bv["FACE_W"] + 1e-6
        vis = trimesh.boolean.difference([m, body_shadow(bv, lean)], engine="manifold")
        vb = solid_bounds(vis)
        if vb is None:
            vdesc, vis_ok = "nothing visible from the front", True
        else:
            vlo, vhi = vb
            # The front pads also hide what is directly behind them
            # (e.g. the fin's front tip under the bottom edge when the front
            # pad sits forward of it): remove each pad's front-view shadow,
            # pad_d wide x FOOT_PAD_T (its upright side) tall, from the foot axis back.
            occl = union([box(x - pad_r, x + pad_r, -gap - 0.01, -gap + bv["FOOT_PAD_T"],
                              -300, ffz) for x in bv["FIN_X"]])
            resid = trimesh.boolean.difference([vis, occl], engine="manifold")
            rb = solid_bounds(resid)
            in_front_pads = rb is None or rb[0][2] > ffz - pad_r - 0.05
            vis_ok = in_front_pads if gap == 0 else True
            vdesc = "visible from the front: %.1f mm3, Y %.2f..%.2f (%.2f above the fin bottom), Z %.2f..%.2f%s" % (
                mesh_volume(vis), vlo[1], vhi[1], vhi[1] + gap, vlo[2], vhi[2],
                " (front pads only)" if in_front_pads else " (includes fin/rear pad: float gap)")
        ok = geo_ok and vis_ok and m.is_watertight
        rec("fin stand " + sweep_label(lean, gap, off), "OK" if ok else "FAIL",
            "watertight=%s, bottom Y %.2f (want %.2f), rear Z %.2f (want %.2f); %s" % (
                m.is_watertight, lo[1], -gap, lo[2], rear_z, vdesc))
        if not ok:
            failed.append("fin stand " + sweep_label(lean, gap, off))
    # Tip-over (static): CoG vs the four feet's contact rectangle, front/back.
    if front is not None and back is not None and fins is not None:
        bodies = [(front, DENSITY_PRINT), (back, DENSITY_PRINT), (pcb, DENSITY_FR4)]
        bodies += [(m, DENSITY_PRINT) for m in [k, a] + list(pl.values()) if m is not None]
        for n, (m, s, _) in parts.items():
            if n == "PCB":
                continue
            if n.startswith("screw_"):
                bodies.append((m, DENSITY_SCREW))
            else:
                bodies.append((m, DENSITY_DISPLAY if n == "DISPLAY" else DENSITY_COMPONENT))
        mass = sum(abs(m.volume) * d for m, d in bodies) * 1e-3
        cog = sum(abs(m.volume) * d * m.center_mass for m, d in bodies) * 1e-3 / mass
        fin_mass = abs(fins.volume) * DENSITY_PRINT * 1e-3
        cog_all = (cog * mass + fins.center_mass * fin_mass) / (mass + fin_mass)
        q, bz = cog[1], BODY_T - cog[2]
        a_ = math.radians(LEAN)
        cz = -q * math.sin(a_) + bz * math.cos(a_)
        cy = q * math.cos(a_) + bz * math.sin(a_)
        cz_all = (F2W @ np.append(cog_all, 1.0))[2]
        front_edge = bv["FRONT_FOOT_Z"] + bv["FOOT_DIA"] / 2
        rear_edge = bv["REAR_FOOT_Z"] - bv["FOOT_DIA"] / 2
        m_front, m_back = front_edge - cz, cz_all - rear_edge
        m_front_all = front_edge - cz_all
        h = cy + bv["FLOAT_GAP"] + bv["FOOT_H"] - bv["FOOT_RECESS_DEPTH"]   # CoG above the table (FOOT_H display value)
        ok = m_front > 0 and m_back > 0
        rec("tip-over: CoG inside the feet contact (LEAN %g, FLOAT %g)" % (LEAN, bv["FLOAT_GAP"]), "OK" if ok else "FAIL",
            "body %.0f g + fins %.1f g; CoG world Z %.2f (no fins) / %.2f (with), %.1f mm above the table; "
            "feet contact Z %.2f..%.2f -> margin front %.2f mm (tilt %.1f deg; %.2f mm with fins), back %.2f mm (tilt %.1f deg)" % (
                mass, fin_mass, cz, cz_all, h, rear_edge, front_edge, m_front,
                math.degrees(math.atan2(m_front, h)), m_front_all, m_back, math.degrees(math.atan2(m_back, h))))
        if not ok:
            failed.append("tip-over")
        drift = max(abs(q - bv["COG_Q"]), abs(bz - bv["COG_BZ"]))
        rec("tip-over: back_shell.scad COG_Q/COG_BZ vs mass model", "OK" if drift <= 0.5 else "WARN",
            "model Q %.2f, bz %.2f (no fins) vs scad %.2f, %.2f" % (q, bz, bv["COG_Q"], bv["COG_BZ"]))
        # Button press tipping it back over the rear feet: press at the
        # A/B/X/Y diamond centre, along the face normal (face frame +Z).
        bx_, by_ = fv["BTN_X"][0] + 8.0, fv["BTN_X"][1]   # diamond centre = X button + pitch
        p = F2W @ np.array([bx_ + ev["MARGIN_X"], ev["QTOP"] - by_, 0.0, 1.0])
        d = F2W[:3, :3] @ np.array([0.0, 0.0, 1.0])
        piv_y = -(bv["FLOAT_GAP"] + bv["FOOT_H"] - bv["FOOT_RECESS_DEPTH"])
        rz, ry = p[2] - rear_edge, p[1] - piv_y
        tip_arm = abs(rz * d[1] - ry * d[2])          # moment arm of a unit press about the rear feet edge
        w_n = (mass + fin_mass) * 1e-3 * 9.81
        rec("tip-over: button press force to tip back over the rear feet", "INFO",
            "%.2f N (weight %.2f N x %.1f mm / %.1f mm arm; ADR estimates a ~2.5 N press, friction permitting)" % (
                w_n * m_back / tip_arm, w_n, m_back, tip_arm))
        # Knob detent torque rolling it sideways over one fin's feet (ADR
        # Rationale, "Two legs, not one strut"). The torque acts about the
        # shaft (face normal, LEAN_DEG above horizontal); its component about
        # the fore-aft roll axis through a fin's feet is T cos(LEAN). Restoring
        # moment = weight x lateral CoG-to-feet-outer-edge distance.
        cx = (F2W @ np.append(cog_all, 1.0))[0]
        feet_l = bv["FACE_W"] / 2 - bv["FIN_OFFSET_X"] - bv["FOOT_DIA"] / 2
        feet_r = bv["FACE_W"] / 2 + bv["FIN_OFFSET_X"] + bv["FOOT_DIA"] / 2
        roll_arm = min(cx - feet_l, feet_r - cx)
        restoring = w_n * roll_arm
        t_nom, t_max = KNOB_DETENT_TORQUE_NMM
        rec("tip-over: knob detent torque roll margin over one fin's feet", "INFO",
            "%.1f N.mm restoring (%.2f N x %.2f mm, CoG X %.2f vs face centre %.2f) vs detent T cos(LEAN): %.1f N.mm nominal / %.1f worst -> %.2fx / %.2fx" % (
                restoring, w_n, roll_arm, cx, bv["FACE_W"] / 2, t_nom * math.cos(a_), t_max * math.cos(a_),
                restoring / (t_nom * math.cos(a_)), restoring / (t_max * math.cos(a_))))
    # --- rim profile mismatch
    if front is not None and back is not None:
        rec("shell corner radii front vs back", "INFO" if fv.get("CORNER_RADIUS") == bv.get("CORNER_R") else "WARN",
            "front %.1f mm vs back %.1f mm (outer rim steps at the joint if different)" % (fv.get("CORNER_RADIUS", 0), bv.get("CORNER_R", 0)))

    # ---------------------------------------------------------------- summary
    print("\n=== Summary ===")
    n_ok = sum(1 for r in results if r[1] == "OK")
    print("%d OK, %d FAIL, %d WARN, %d INFO" % (n_ok, sum(1 for r in results if r[1] == "FAIL"),
                                                 sum(1 for r in results if r[1] == "WARN"), sum(1 for r in results if r[1] == "INFO")))
    for f in failed:
        print("  FAIL:", f)
    if args.json:
        json.dump([{"pair": p, "status": s, "detail": d} for p, s, d in results], open(args.json, "w"), indent=1)
    print("\nCAD-level check only: not the printed fit check (pilink-8hx.5).")
    return 1 if (failed or render_fail) else 0


if __name__ == "__main__":
    sys.exit(main())
