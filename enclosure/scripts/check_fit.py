#!/usr/bin/env python3
"""CAD-level fit check for the enclosure (pilink-7tm).

NOT the printed fit check (pilink-8hx.5). This renders every enclosure/*.scad
headlessly, builds a PCB envelope (board slab + per-component boxes) from
hardware/pico-link-hw.kicad_pcb, places everything in one "face frame" and
reports interference volumes / approximate minimum distances.

Run it through enclosure/scripts/check_fit.sh (docker, needs the preview image
for openscad + pcbnew + trimesh). Needs: openscad, pcbnew (KiCad python),
trimesh, numpy, manifold3d, scipy, rtree.

Face frame (matches front_shell.scad / back_shell.scad's own mapping):
  X = board_x + 2        (left -> right)
  Q = 52 - board_y       (bottom of face = 0, top = 56)
  Z = 0 at the outer face, increasing into the body (front shell 0..7.5,
      PCB 7.5..9.1, back shell outer face at Z = BODY_T = 14.1)
"""
import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
import trimesh

# ---------------------------------------------------------------- scad utils


def scad_vars(path):
    """Evaluate top-level `NAME = expr;` numeric/list assignments (best effort)."""
    env = {"max": max, "min": min, "tan": lambda d: math.tan(math.radians(d)),
           "cos": lambda d: math.cos(math.radians(d)),
           "sin": lambda d: math.sin(math.radians(d))}
    for line in open(path):
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


last_thickness = [0.0]


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
    v = abs(r.volume)
    if v < 1e-6:
        return 0.0, None
    # mean thickness of the overlap region (slab approximation: V / (A/2)); a
    # bbox extent is useless for a diagonal sliver, this is not
    last_thickness[0] = 2.0 * v / max(r.area, 1e-9)
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
    QTOP = ev["QTOP"]              # Q of board y=0 (52)
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

    # Display module stack: panel shadow x[28,87] y[5,47] (hardware/README.md),
    # 3.3mm above the PCB front (proposal 6c "3.3 panel stack").
    add_box("DISPLAY", 28.0, 87.0, 5.0, 47.0, 3.3, "F", "panel shadow x28-87 y5-47 x 3.3 stack (README / proposal 6c)")
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
        if n == "back_shell":
            jobs += [("back_shell[assembly]", scad, [], "bs_asm"),
                     ("back_shell[PART=back_shell]", scad, ['PART="back_shell"'], "bs_back"),
                     ("back_shell[PART=leg_left]", scad, ['PART="leg_left"'], "bs_legl"),
                     ("back_shell[PART=leg_right]", scad, ['PART="leg_right"'], "bs_legr")]
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
    plunger = wrapper("plunger", "button_plunger.scad", ["button_plungers_x4"], "button_plunger();")
    plunger_pr = wrapper("plunger_pressed", "button_plunger.scad", ["button_plungers_x4"], "button_plunger();", ["PREVIEW_PRESSED=true"])
    knob = wrapper("knob", "knob.scad", ["knob"], "knob();")
    ant = wrapper("antenna", "antenna_mount.scad", ["demo_assembly"], "antenna_mount();")
    for nm, m in (("front (face frame)", front), ("back (face frame, mirrored in Z)", back), ("pigtail spool", spool),
                  ("plunger", plunger), ("knob", knob), ("antenna mount", ant)):
        if m is not None:
            print("  %-34s vol=%8.1f bbox lo=%s hi=%s" % (nm, m.volume, m.bounds[0].round(2).tolist(), m.bounds[1].round(2).tolist()))
    if back is not None and back.volume < 0:
        back.invert()

    # ------------------------------------------------------------ 3. envelope
    print("\n=== 3. PCB envelope ===")
    ev = {
        "MARGIN_X": bv["MARGIN_X"],
        "QTOP": bv["FACE_H"] - (bv["WALL_T"] + bv["TOP_SLACK_Y"]),
        "Z_PCB_FRONT": fv["FRONT_SHELL_DEPTH"],
        "U201_BODY_X": bv["U201_BODY_X"], "U201_BODY_Y": bv["U201_BODY_Y"],
        "U201_MODULE_H": bv["U201_MODULE_H"], "UFL_PLUG_TOP_H": bv["UFL_PLUG_TOP_H"],
        "U201_UFL": bv["U201_UFL_BOARD_ASSUMED"],
        "ENCODER_BOARD": (fv["ENCODER_BOARD_CX"], fv["ENCODER_BOARD_CY"]),
        "PCB_MOUNT_HOLES_BOARD": bv["PCB_MOUNT_HOLES_BOARD"], "INSERT_LEN": bv["INSERT_LEN"],
    }
    parts, meta, unknown = build_envelope(os.path.abspath(args.pcb), ev)
    print("  board outline %.2f x %.2f x %.2f mm (from Edge.Cuts)" % (meta["board_w"], meta["board_h"], meta["board_t"]))
    print("  %d envelope bodies; PCB at Z %.1f..%.1f; frame: X=bx+%.0f, Q=%.0f-by" % (
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
        # < 0.25 mm3 AND a mean thickness (2V/A) of at most 0.05mm (about the
        # STL/coincident-face noise class). A thicker overlap, however small
        # in volume, is a real interference and FAILs.
        thk = last_thickness[0]
        if v > 1e-3 and contact_ok and v < 0.25 and thk <= 0.05:
            rec(pair, "INFO", "contact only (%.3f mm3 sliver, mean %.3fmm thick, mating faces by design) %s" % (v, thk, note))
            return 0.0
        if v > 1e-3:
            rec(pair, "FAIL" if expect_zero else "INFO", "overlap %.3f mm3 (mean %.3fmm thick) at (X,Q,Z)~%s %s" % (v, last_thickness[0], loc, note))
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
              note="(board 118 wide vs back cavity %.1f)" % (bv["FACE_W"] - 2 * (bv["WALL_T"] - bv["BOARD_CLEARANCE_X"])))
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
    # --- board bottom edge vs back-shell bottom wall
    if back is not None:
        bottom_q = ev["QTOP"] - meta["board_h"]          # Q of the board's bottom edge
        wall_q = bv["WALL_T"]                             # Q of the back cavity's bottom inner wall
        gap = bottom_q - wall_q
        rec("board bottom edge vs back-shell bottom wall", "OK" if gap >= 0.1 else "WARN",
            "%.2f mm clearance (board edge Q=%.2f, cavity wall Q=%.2f)%s" % (
                gap, bottom_q, wall_q, "" if gap >= 0.1 else " -- zero running clearance, no tolerance margin on Y"))
    # --- legs
    lt, lb = renders.get("bs_legl"), renders.get("bs_back")
    if lt is not None and lb is not None:
        check("left leg vs back shell + base strip (world frame)", lt, lb, dist=True, contact_ok=True)
        if renders.get("bs_legr") is not None:
            check("right leg vs back shell + base strip (world frame)", renders["bs_legr"], lb, dist=True, contact_ok=True)
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
