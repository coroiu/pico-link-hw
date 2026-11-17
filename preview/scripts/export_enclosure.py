#!/usr/bin/env python3
"""Render every enclosure part and build the preview's enclosure GLBs.

Called by export.sh. Writes, under <out_dir>:
  <part>.glb      one per printed part, each in its assembled pose
  assembly.glb    every part in place, plus the PCB model if available
  parts.json      manifest the web page builds its part picker from

Everything is placed in back_shell.scad's "world" frame (X = across the
face, left -> right seen from the front; Y = up; Z = forward, toward the
viewer), which is already glTF's Y-up convention, then scaled mm -> m to
match the kicad-cli PCB export.

Frames, as the .scad files define them (and as enclosure/scripts/check_fit.py
uses them):
  face frame (front_shell, knob, plungers, antenna mount):
      X = board_x + MARGIN_X (2.5), Q = QTOP (53) - board_y, Z = 0 at the outer face
      (MARGIN_X / QTOP come from enclosure/common.scad, the single shared
      board-to-face mapping)
      increasing into the body (PCB front surface at Z = FRONT_SHELL_DEPTH).
  back-shell local frame: same X/Q, bz = BODY_T - Z (0 at the back wall's
      outer surface), so face -> local is a mirror in Z.
  world frame: rotate([-LEAN_DEG, 0, 0]) applied to the local frame
      (back_shell.scad's PART="back_shell" output is already world).

The antenna mount has no real placement in the .scad files; like
check_fit.py it is put against the inner top wall at X = MOUNT_X_MIN,
centred in the cavity depth (ASSUMED) -- but rotated, never mirrored, since
it is a printed part.

The extra openscad renders are run in parallel; per-part failures are logged
and skipped so one broken file doesn't blank the whole view.
"""
import concurrent.futures as cf
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

# (key, label, colour RGBA 0-255). Order = order in the page's picker.
PARTS = [
    ("front_shell", "Front shell", (226, 226, 222, 255)),
    ("back_shell", "Back shell + legs + base strip", (88, 96, 110, 255)),
    ("knob", "Knob", (200, 48, 48, 255)),
    ("button_plunger", "Button plunger (x4)", (60, 130, 200, 255)),
    ("antenna_mount", "Antenna mount", (90, 170, 90, 255)),
]


def scad_vars(path, env=None):
    """Evaluate top-level `NAME = expr;` numeric/list assignments (best effort,
    same approach as check_fit.py), following `include <file>` lines so the
    constants in enclosure/common.scad are visible."""
    if env is None:
        env = {"max": max, "min": min,
               "tan": lambda d: math.tan(math.radians(d)),
               "cos": lambda d: math.cos(math.radians(d)),
               "sin": lambda d: math.sin(math.radians(d))}
    with open(path) as f:
        for line in f:
            inc = re.match(r"^include\s*<([^>]+)>", line)
            if inc:
                scad_vars(os.path.join(os.path.dirname(path), inc.group(1)), env)
                continue
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?);\s*(//.*)?$", line)
            if not m:
                continue
            try:
                env[m.group(1)] = eval(m.group(2), {"__builtins__": {}}, env)
            except Exception:
                pass
    return env


def strip_calls(src, dst, names):
    """Copy a .scad file minus its top-level `name();` render calls so its
    modules + constants can be included from a wrapper."""
    pat = re.compile(r"^(%s)\(\);\s*$" % "|".join(names))
    with open(src) as f, open(dst, "w") as g:
        for line in f:
            if not pat.match(line):
                g.write(line)


def run_openscad(scad, out, defs=()):
    cmd = ["openscad", "-o", out]
    for d in defs:
        cmd += ["-D", d]
    cmd.append(scad)
    p = subprocess.run(cmd, capture_output=True, text=True)
    ok = p.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 0
    return ok, (p.stdout + p.stderr)[-600:]


def edge_cuts_origin(pcb_file):
    """Min (x, y) in mm over every Edge.Cuts graphic's coordinates -- the
    board-local origin the .scad files' board_x/board_y are measured from."""
    with open(pcb_file) as f:
        text = f.read()
    xs, ys = [], []
    for block in re.split(r"\n\t\(", text):
        if not block.startswith("gr_") or '(layer "Edge.Cuts")' not in block:
            continue
        for x, y in re.findall(r"\((?:start|end|mid|center|xy) (-?[\d.]+) (-?[\d.]+)\)", block):
            xs.append(float(x))
            ys.append(float(y))
    if not xs:
        raise ValueError("no Edge.Cuts graphics in %s" % pcb_file)
    return min(xs), min(ys)


def rot_x(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
    return m


def translate(x, y, z):
    m = np.eye(4)
    m[:3, 3] = [x, y, z]
    return m


def mat3(rows, t=(0, 0, 0)):
    m = np.eye(4)
    m[:3, :3] = np.array(rows, dtype=float)
    m[:3, 3] = t
    return m


def main():
    # usage: export_enclosure.py ENCLOSURE_DIR OUT_DIR [PCB_RAW_GLB PCB_FILE]
    enc, out_dir = sys.argv[1], sys.argv[2]
    pcb_raw, pcb_file = (sys.argv[3], sys.argv[4]) if len(sys.argv) > 4 else ("", "")
    os.makedirs(out_dir, exist_ok=True)
    work = tempfile.mkdtemp(prefix="encl")

    def src(name):
        return os.path.join(enc, name + ".scad")

    fv = scad_vars(src("front_shell"))
    bv = scad_vars(src("back_shell"))
    kv = scad_vars(src("knob"))
    av = scad_vars(src("antenna_mount"))

    BODY_T, LEAN = bv["BODY_T"], bv["LEAN_DEG"]
    MARGIN_X = bv["MARGIN_X"]
    QTOP = bv["QTOP"]
    Z_PCB_FRONT = fv["FRONT_SHELL_DEPTH"]
    PCB_T = bv["PCB_T"]

    # Face frame -> world: mirror Z into the back shell's local frame, then lean.
    face_to_world = rot_x(-LEAN) @ mat3([[1, 0, 0], [0, 1, 0], [0, 0, -1]], (0, 0, BODY_T))
    local_to_world = rot_x(-LEAN)

    # ---- openscad jobs: key -> (scad, defs)
    def wrapper(key, file, strip, body):
        lib = os.path.join(work, "lib_%s.scad" % key)
        strip_calls(src(file), lib, strip)
        shutil.copy(src("common"), os.path.join(work, "common.scad"))
        w = os.path.join(work, "w_%s.scad" % key)
        with open(w, "w") as f:
            f.write("include <%s>\n%s\n" % (lib, body))
        return w

    jobs = {
        "front_shell": (src("front_shell"), []),
        "back_shell": (src("back_shell"), ['PART="back_shell"']),
        "knob": (src("knob"), []),
        "button_plunger": (wrapper("plunger", "button_plunger", ["button_plungers_x4"], "button_plunger();"), []),
        "antenna_mount": (wrapper("antenna", "antenna_mount", ["demo_assembly"], "antenna_mount();"), []),
    }

    def render(key):
        scad, defs = jobs[key]
        out = os.path.join(work, key + ".stl")
        ok, log = run_openscad(scad, out, defs)
        return key, ok, out, log

    meshes = {}
    with cf.ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 1)) as ex:
        for key, ok, out, log in ex.map(render, jobs):
            if not ok:
                print("[enclosure] WARNING: openscad render failed for %s:\n%s" % (key, log), file=sys.stderr)
                continue
            m = trimesh.load(out, force="mesh")
            m.merge_vertices()
            meshes[key] = m
            print("[enclosure] rendered %s (%d faces)" % (key, len(m.faces)))

    # ---- placements in world mm: key -> list of 4x4 transforms
    place = {
        "front_shell": [face_to_world],
        "back_shell": [np.eye(4)],
    }
    kx = fv["ENCODER_BOARD_CX"] + MARGIN_X
    kq = QTOP - fv["ENCODER_BOARD_CY"]
    # knob +z (up from its underside) -> face-frame -Z (outward), KNOB_GAP proud
    place["knob"] = [face_to_world @ mat3([[1, 0, 0], [0, 1, 0], [0, 0, -1]], (kx, kq, -kv["KNOB_GAP"]))]
    place["button_plunger"] = [
        face_to_world @ translate(fv[n][0] + MARGIN_X, QTOP - fv[n][1], 0)
        for n in ("BTN_Y", "BTN_X", "BTN_B", "BTN_A")]
    if "antenna_mount" in meshes:
        lo, hi = meshes["antenna_mount"].bounds
        wall_inner_q = fv["FACE_H"] - fv["WALL"]
        zmid = (fv["FACE_T"] + BODY_T - bv["BACK_WALL_T"]) / 2
        # local x -> X; local z (away from the land) -> down from the top wall;
        # local y -> centred in the cavity depth, reversed so the whole map is a
        # rotation (det +1 after the face->world mirror), not a reflection.
        place["antenna_mount"] = [face_to_world @ mat3(
            [[1, 0, 0], [0, 0, -1], [0, -1, 0]],
            (av["MOUNT_X_MIN"], wall_inner_q, zmid + (lo[1] + hi[1]) / 2))]

    MM = np.diag([0.001, 0.001, 0.001, 1.0])

    def coloured(mesh, rgba, T):
        m = mesh.copy()
        m.apply_transform(MM @ T)
        if m.volume < 0:
            m.invert()
        # glTF baseColorFactor is linear; convert from the sRGB picks above so
        # the viewer shows the intended colour rather than a washed-out one.
        linear = [(c / 255.0) ** 2.2 for c in rgba[:3]] + [rgba[3] / 255.0]
        m.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(
            baseColorFactor=linear, metallicFactor=0.0, roughnessFactor=0.6))
        return m

    manifest = {"assembly": None, "parts": []}
    assembly = trimesh.Scene()
    for key, label, rgba in PARTS:
        if key not in meshes:
            continue
        placed = [coloured(meshes[key], rgba, T) for T in place[key]]
        for i, m in enumerate(placed):
            assembly.add_geometry(m, node_name="%s_%d" % (key, i), geom_name="%s_%d" % (key, i))
        # Individual view: a single copy, same assembled pose.
        single = trimesh.Scene()
        single.add_geometry(placed[0], node_name=key, geom_name=key)
        path = os.path.join(out_dir, key + ".glb")
        single.export(path)
        manifest["parts"].append({"key": key, "label": label, "file": key + ".glb",
                                  "color": "#%02x%02x%02x" % rgba[:3]})

    # ---- PCB: kicad-cli GLB is metres, X = board x, Z = board y (KiCad
    # coordinates, board origin at the Edge.Cuts top-left), Y = up out of
    # F.Cu (bottom surface at Y = 0). Map to the back shell's local frame:
    #   X = bx + MARGIN_X, Q = QTOP - by, bz = BODY_T - Z_PCB_FRONT - PCB_T + h
    # (a proper rotation: F side faces forward, toward the viewer).
    with_pcb = False
    if pcb_raw and os.path.exists(pcb_raw) and meshes:
        try:
            pcb = trimesh.load(pcb_raw)
            ox, oz = edge_cuts_origin(pcb_file)
            board_to_local = mat3(
                [[1000, 0, 0], [0, 0, -1000], [0, 1000, 0]],
                (MARGIN_X - ox, QTOP + oz, BODY_T - Z_PCB_FRONT - PCB_T))
            T = MM @ local_to_world @ board_to_local
            for i, m in enumerate(pcb.dump(concatenate=False)):
                m.apply_transform(T)
                assembly.add_geometry(m, node_name="pcb_%d" % i, geom_name="pcb_%d" % i)
            with_pcb = True
            print("[enclosure] PCB placed in assembly (board origin %.1f, %.1f)" % (ox, oz))
        except Exception as e:  # keep the enclosure-only assembly
            print("[enclosure] WARNING: could not place PCB in assembly: %s" % e, file=sys.stderr)

    if meshes:
        assembly.export(os.path.join(out_dir, "assembly.glb"))
        manifest["assembly"] = {"key": "assembly", "label": "Assembly" + (" (with PCB)" if with_pcb else ""),
                                "file": "assembly.glb", "pcb": with_pcb}
    with open(os.path.join(out_dir, "parts.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print("[enclosure] wrote %d part GLBs + assembly to %s" % (len(manifest["parts"]), out_dir))
    return 0 if len(meshes) == len(jobs) else 1


if __name__ == "__main__":
    sys.exit(main())
