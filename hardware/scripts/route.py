#!/usr/bin/env python3
"""Autoroute pico-link-hw.kicad_pcb with Freerouting (pilink-7el.12).

Usage (from hardware/):
    python3 scripts/route.py [--passes N] [--tries N] [--jar PATH]

Specctra round-trip: strip existing tracks/vias/zones (except the locked
tracks/vias scripts/preroute.py laid) -> export DSN -> Freerouting
(headless) -> import SES -> save. Run scripts/widen.py and scripts/zones.py
next.

Ground plane strategy (pilink-r1h): B.Cu is the board's ground plane, so
  * GND is not routed by Freerouting at all. preroute.py gives every F.Cu
    GND pad its own locked via to B.Cu (gnd_fanout.py), zones.py pours GND
    on both layers. edit_dsn() takes GND out of the DSN's netlist (GND pads
    become netless obstacles) and hands the locked GND copper to
    Freerouting as keepouts; after the import that copper is put back.
    (With GND left in the netlist, even under Freerouting's -inc "ignore
    net class" option, runs here never finished: it kept routing past the
    pass limit, joining the fixed GND fan-out pieces with traces.)
  * Freerouting's per-layer trace costs make B.Cu B_COST times as
    expensive as F.Cu, so signals stay on F.Cu and drop to B.Cu only for
    short jumps under F.Cu crossings.
  * plane_keepout.py adds B.Cu track keepouts where the plane must stay
    whole (crystal, under U101, ...), exported like the antenna strip and
    the L101 area.
A run is retried (up to --tries) when Freerouting writes no session, the
import fails, or DRC reports any unconnected non-GND item afterwards
(pilink-dbu).

Freerouting needs Java 21+. If no `java` is on PATH this falls back to
`docker run eclipse-temurin:21-jre`. The DSN/SES are staged in a work
directory beside the board (not the system temp dir: a snap-packaged Docker
cannot see the host's temp dir, so a bind mount from there arrives empty).
The jar defaults to $FREEROUTING_JAR or ~/.kicad-mcp/freerouting.jar
(https://github.com/freerouting/freerouting/releases). Use v2.0.1: v2.1.0
ignores the pass limit in headless mode and never writes a session file if
even one connection stays unrouted.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import pcbnew

from preroute import PREROUTE_NETS
from gnd_fanout import GND_STITCH_DRILL
from antenna_reroute import add_route_keepout, remove_route_keepout
from sw_keepout import add_sw_keepouts
from l101_keepout import add_l101_route_keepout, remove_l101_route_keepout
from plane_keepout import add_plane_keepouts, remove_plane_keepouts

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
BOARD = os.path.join(HW, "pico-link-hw.kicad_pcb")
WORK = os.path.join(HW, ".autoroute")


ROUTE_TIMEOUT = 900   # seconds; a normal run takes 1.5-3 minutes
# pilink-r1h: Freerouting trace cost per unit length, per layer. F.Cu 1.0 in
# both directions (no preferred direction); B.Cu B_COST times that, so the
# router only jumps to B.Cu where F.Cu is blocked. VIA_COST is Freerouting's
# own via cost (its default is 50); lower makes short B.Cu jumps cheaper
# than long F.Cu detours.
B_COST = 4.0
VIA_COST = 40
# Freerouting log lines that mean the run is dead even if the JVM is not
FATAL_LOG = ("HeadlessException", "\"this.board\" is null", "OutOfMemoryError")


def _poly(layer, pts):
    coords = "  ".join(f"{x:.1f} {y:.1f}" for x, y in pts + pts[:1])
    return f"    (keepout \"\" (polygon {layer} 0  {coords}))\n"


def _seg_poly(layer, x0, y0, x1, y1, hw):
    """Keepout for a track segment: its rectangle plus octagonal end caps
    (DSN units)."""
    import math
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L == 0:
        return _circle_poly(layer, x0, y0, hw)
    ux, uy = dx / L, dy / L
    pts = []
    for cx, cy, a0 in ((x1, y1, -90), (x0, y0, 90)):
        base = math.degrees(math.atan2(uy, ux))
        for k in range(5):        # half octagon round the end
            a = math.radians(base + a0 + 45 * k)
            pts.append((cx + hw / math.cos(math.pi / 8) * math.cos(a),
                        cy + hw / math.cos(math.pi / 8) * math.sin(a)))
    return _poly(layer, pts)


def _circle_poly(layer, x, y, r):
    import math
    R = r / math.cos(math.pi / 8)       # octagon circumscribing the circle
    return _poly(layer, [(x + R * math.cos(math.radians(22.5 + 45 * k)),
                          y + R * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)])


def edit_dsn(text, b_cost, via_cost):
    """GND into its own (ignored) class; per-layer costs; +10um clearance."""
    # Freerouting rounds to its own grid and can land a few um under the
    # clearance it was given; hand it +10um so KiCad's DRC sees no slivers.
    text = re.sub(r"\(clearance (\d+(?:\.\d+)?)\)",
                  lambda m: f"(clearance {float(m.group(1)) + 10:g})", text)
    # GND out of the netlist altogether: with GND in it (even with -inc)
    # Freerouting kept joining the separate pieces of fixed GND copper (each
    # fan-out via + stub) with traces and never finished. So the GND
    # net and its class entry go, GND pads become plain (netless)
    # obstacles, and the locked GND copper is handed over as keepouts of
    # its exact outline on each layer.
    for c in re.finditer(r"\(class [^(]*", text):
        body = c.group(0)
        new = re.sub(r"(?<=\s)GND(?=\s)", "", body)
        if new != body:
            text = text[:c.start()] + new + text[c.end():]
            break
    else:
        sys.exit("route.py: GND not found in any DSN net class")
    a = text.index("\n    (net GND\n")
    b = text.index(")", text.index("(pins", a))      # end of the pin list
    b = text.index(")", b + 1)                       # end of (net GND ...)
    text = text[:a] + text[b + 1:]
    keepouts = []
    lines = []
    for line in text.split("\n"):
        if "(net GND)" not in line:
            lines.append(line)
            continue
        m = re.search(r"\(path (\S+) (\d+(?:\.\d+)?)\s+([-\d.\s]+)\)", line)
        if m and line.lstrip().startswith("(wire"):
            layer, w = m.group(1), float(m.group(2))
            xy = [float(v) for v in m.group(3).split()]
            for (x0, y0), (x1, y1) in zip(zip(xy[0::2], xy[1::2]), zip(xy[2::2], xy[3::2])):
                keepouts.append(_seg_poly(layer, x0, y0, x1, y1, w / 2))
            continue
        m = re.search(r'\(via "Via\[0-1\]_(\d+):\d+_um"\s+([-\d.]+) ([-\d.]+)', line)
        if m:
            r, x, y = float(m.group(1)) / 2, float(m.group(2)), float(m.group(3))
            for layer in ("F.Cu", "B.Cu"):
                keepouts.append(_circle_poly(layer, x, y, r))
            continue
        sys.exit("route.py: cannot convert GND wiring line: " + line.strip())
    text = "\n".join(lines)
    k = text.index("    (boundary", text.index("  (structure"))
    k = text.index("\n", text.index("    )", k)) + 1   # after the boundary scope
    text = text[:k] + "".join(keepouts) + text[k:]
    settings = ("    (autoroute_settings\n"
                "      (fanout off) (autoroute on) (postroute on) (vias on)\n"
                f"      (via_costs {via_cost}) (plane_via_costs 5)\n"
                "      (start_ripup_costs 100) (start_pass_no 1)\n"
                "      (layer_rule F.Cu (active on) (preferred_direction horizontal)\n"
                "        (preferred_direction_trace_costs 1.0)\n"
                "        (against_preferred_direction_trace_costs 1.0))\n"
                "      (layer_rule B.Cu (active on) (preferred_direction vertical)\n"
                f"        (preferred_direction_trace_costs {b_cost})\n"
                f"        (against_preferred_direction_trace_costs {b_cost}))\n"
                "    )\n")
    # after the (layer ...) scopes: Freerouting resolves layer_rule names
    # against layers it has already read
    k = text.index("    (boundary", text.index("  (structure"))
    return text[:k] + settings + text[k:]


def unconnected_signals(board_path):
    """Unconnected items DRC reports on any net but GND (zones are not
    poured yet, so GND is expected to be open here)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "drc.json")
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "-o", out,
                        board_path], check=True, stdout=subprocess.DEVNULL)
        with open(out) as fh:
            rep = json.load(fh)
    bad = []
    for u in rep.get("unconnected_items", []):
        descs = [i["description"] for i in u.get("items", [])]
        if not any("[GND]" in d for d in descs):
            bad.append(" / ".join(descs))
    return bad


def _clone_spec(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        return ("via", pcbnew.VECTOR2I(t.GetPosition()), t.GetWidth(pcbnew.F_Cu), t.GetDrillValue())
    return ("trk", pcbnew.VECTOR2I(t.GetStart()), pcbnew.VECTOR2I(t.GetEnd()), t.GetWidth(), t.GetLayer())


def _restore(board, spec):
    net = board.FindNet("GND")
    if spec[0] == "via":
        _, pos, d, drill = spec
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pos)
        v.SetWidth(pcbnew.F_Cu, d)
        v.SetDrill(drill)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(net)
        v.SetLocked(True)
        board.Add(v)
    else:
        _, a, b, w, layer = spec
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(a)
        t.SetEnd(b)
        t.SetWidth(w)
        t.SetLayer(layer)
        t.SetNet(net)
        t.SetLocked(True)
        board.Add(t)


def run_freerouting(args, dsn_text):
    """One Freerouting run in a fresh WORK dir. Returns the SES path, or
    None (with the reason printed) when it wrote no usable session."""
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    with open(os.path.join(WORK, "board.dsn"), "w") as fh:
        fh.write(dsn_text)
    ses = os.path.join(WORK, "board.ses")
    fr_args = ["-de", "{w}/board.dsn", "-do", "{w}/board.ses",
               "--gui.enabled=false", "-mp", str(args.passes)]
    container = docker = None
    if shutil.which("java"):
        cmd = ["java", "-jar", args.jar] + [a.format(w=WORK) for a in fr_args]
    else:
        docker = shutil.which("docker") or shutil.which("podman")
        if not docker:
            sys.exit("need java 21+ or docker/podman to run Freerouting")
        container = f"pilink-freerouting-{os.getpid()}"
        cmd = [docker, "run", "--rm", "--name", container,
               "-u", f"{os.getuid()}:{os.getgid()}",
               "-e", "HOME=/work",
               "-v", f"{WORK}:/work", "-v", f"{args.jar}:/app/freerouting.jar:ro",
               "eclipse-temurin:21-jre", "java", "-jar", "/app/freerouting.jar"
               ] + [a.format(w="/work") for a in fr_args]
    print("running:", " ".join(cmd), flush=True)
    logpath = os.path.join(WORK, "freerouting.log")

    def kill(proc):
        proc.kill()
        # killing the docker CLI leaves the container running (and holding
        # the CPU): remove it explicitly
        if container:
            subprocess.run([docker, "rm", "-f", container],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc.wait()

    with open(logpath, "w") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        t0 = time.time()
        while proc.poll() is None:
            time.sleep(5)
            # Freerouting can die in a worker thread and leave the JVM up
            # (e.g. a DSN it could not read: "board is null"); stop waiting
            with open(logpath) as fh:
                logtext = fh.read()
            if any(s in logtext for s in FATAL_LOG):
                kill(proc)
                print("Freerouting crashed (see its log)")
                return None
            # v2.0.1 does not stop at -mp while a connection is unrouted (it
            # stops by itself once everything is routed, normally within
            # ~15 passes here): give up well past the limit instead of
            # waiting for ROUTE_TIMEOUT
            passes = logtext.count("Auto-router pass #")
            if passes > args.passes + 10:
                kill(proc)
                print(f"Freerouting ran {passes} passes without finishing "
                      "(a connection it cannot route)")
                return None
            if time.time() - t0 > ROUTE_TIMEOUT:
                kill(proc)
                print(f"Freerouting did not finish within {ROUTE_TIMEOUT}s "
                      "(it can loop past -mp when a connection is unroutable)")
                return None
    if not os.path.isfile(ses) or os.path.getsize(ses) == 0:
        print("Freerouting wrote no session file")
        return None
    # ImportSpecctraSES aborts the whole import if any reference in the
    # session's (placement ...) block fails its lookup. A headless run never
    # moves parts, so drop the block.
    text = open(ses).read()
    start = text.find("(placement")
    if start >= 0:
        depth = 0
        for i in range(start, len(text)):
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            if depth == 0:
                text = text[:start] + text[i + 1:]
                break
        with open(ses, "w") as fh:
            fh.write(text)
    return ses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=30)
    ap.add_argument("--tries", type=int, default=4,
                    help="Freerouting attempts before giving up (pilink-dbu)")
    ap.add_argument("--b-cost", type=float, default=B_COST)
    ap.add_argument("--via-cost", type=int, default=VIA_COST)
    ap.add_argument("--jar", default=os.environ.get(
        "FREEROUTING_JAR", os.path.expanduser("~/.kicad-mcp/freerouting.jar")))
    ap.add_argument("--keep", action="store_true", help="keep the DSN/SES work dir")
    args = ap.parse_args()
    if not os.path.isfile(args.jar):
        sys.exit(f"freerouting jar not found: {args.jar}")

    board = pcbnew.LoadBoard(BOARD)
    # Keep scripts/preroute.py's locked tracks and vias (exported as fixed
    # wiring, incl. the GND fan-out vias); drop everything else, including
    # zones.py's locked GND stitching vias (zones.py re-creates them).
    for t in list(board.GetTracks()):
        keep = t.IsLocked() and t.GetNetname() in PREROUTE_NETS
        if (keep and t.GetNetname() == "GND" and t.Type() == pcbnew.PCB_VIA_T
                and t.GetDrillValue() == pcbnew.FromMM(GND_STITCH_DRILL)):
            keep = False
        if not keep:
            board.Remove(t)
    for z in list(board.Zones()):
        board.Remove(z)
    # Alps SKRTLAE010 no-copper areas: Freerouting exports rule areas as
    # keepouts, so tracks route around the switch bodies (pilink-ge9).
    add_sw_keepouts(board)
    # Antenna strip (pilink-kiw): no tracks/vias there. Freerouting-only; it
    # is removed again before the board is saved (zones.py adds the pour-only
    # KO_ANT_* areas).
    add_route_keepout(board)
    # L101 (pilink-2wq): no B.Cu track/via under the regulator inductor.
    add_l101_route_keepout(board)
    # Ground-plane areas (pilink-r1h): no B.Cu tracks there.
    add_plane_keepouts(board)

    os.makedirs(WORK, exist_ok=True)
    dsn = os.path.join(WORK, "board.dsn")
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        sys.exit("DSN export failed")
    with open(dsn) as fh:
        dsn_text = edit_dsn(fh.read(), args.b_cost, args.via_cost)
    remove_route_keepout(board)
    remove_l101_route_keepout(board)
    remove_plane_keepouts(board)
    pcbnew.SaveBoard(BOARD, board)      # the stripped, pre-routed board

    for attempt in range(1, args.tries + 1):
        print(f"-- Freerouting attempt {attempt}/{args.tries}", flush=True)
        ses = run_freerouting(args, dsn_text)
        if ses is None:
            continue
        board = pcbnew.LoadBoard(BOARD)
        # the session has no GND (it was not in the DSN's netlist), and the
        # import replaces all tracks: put the locked GND copper back
        gnd = [_clone_spec(t) for t in board.GetTracks()
               if t.GetNetname() == "GND" and t.IsLocked()]
        if not pcbnew.ImportSpecctraSES(board, ses):
            print("SES import failed")
            continue
        for t in [t for t in board.GetTracks() if t.GetNetname() == "GND"]:
            board.Remove(t)
        for spec in gnd:
            _restore(board, spec)
        out = os.path.join(WORK, "routed.kicad_pcb")
        pcbnew.SaveBoard(out, board)
        bad = unconnected_signals(out)
        if bad:
            print(f"{len(bad)} unconnected non-GND item(s) after routing:")
            for b in bad[:10]:
                print("   ", b)
            continue
        pcbnew.SaveBoard(BOARD, board)
        tracks = list(board.GetTracks())
        vias = sum(1 for t in tracks if t.Type() == pcbnew.PCB_VIA_T)
        length = {L: sum(t.GetLength() for t in tracks
                         if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == L) / 1e6
                  for L in (pcbnew.F_Cu, pcbnew.B_Cu)}
        print(f"imported {len(tracks) - vias} track segments, {vias} vias; "
              f"F.Cu {length[pcbnew.F_Cu]:.0f}mm, B.Cu {length[pcbnew.B_Cu]:.0f}mm "
              f"of track (attempt {attempt})")
        if not args.keep:
            shutil.rmtree(WORK, ignore_errors=True)
        return
    sys.exit(f"route.py: no clean Freerouting result in {args.tries} attempts; "
             f"see {WORK}/freerouting.log")


if __name__ == "__main__":
    main()
