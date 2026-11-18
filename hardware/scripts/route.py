#!/usr/bin/env python3
"""Autoroute pico-link-hw.kicad_pcb with Freerouting (pilink-7el.12).

Usage (from hardware/):
    python3 scripts/route.py [--passes N] [--tries N] [--seed N] [--jobs N] [--jar PATH]

Specctra round-trip: strip existing tracks/vias/zones (except the locked
tracks/vias scripts/preroute.py laid) -> export DSN -> Freerouting
(headless) -> import SES -> save. Run scripts/widen.py and scripts/zones.py
next.

Ground strategy (pilink-r1h). B.Cu cannot be kept free of signals with
this placement (see below), so the aim is one well-stitched GND net:
  * GND is not routed by Freerouting at all. preroute.py gives every SMD
    GND pad its own locked via (gnd_fanout.py), zones.py pours GND
    on both layers. edit_dsn() takes GND out of the DSN's netlist (GND pads
    become netless obstacles) and hands the locked GND copper to
    Freerouting as keepouts; after the import that copper is put back.
    (With GND left in the netlist, even under Freerouting's -inc "ignore
    net class" option, runs here never finished: it kept routing past the
    pass limit, joining the fixed GND fan-out pieces with traces.)
  * plane_keepout.py adds B.Cu track keepouts where the plane must stay
    whole (under the crystal; under the VREG hot loop and the strip under
    U101's top pin row down to the exposed pad, pilink-93a), exported like
    the antenna strip and the L101 area. Larger ones were tried and did
    not route: under U101 (whole body, ring, or only the exposed pad), the
    whole VREG block, and the VREG block plus a channel to the exposed pad
    (the ESP32 UART nets then stayed unrouted).
  * Per-layer trace costs do not keep signals off B.Cu: with the DSN's
    (autoroute_settings ...) B.Cu trace cost at 50 (vs 1 for F.Cu)
    Freerouting 2.0.1 still put ~52% of the signal track on B.Cu, the
    same as at 4. The block stays (edit_dsn) for its other settings.
Freerouting is deterministic per DSN, so each attempt gets its own net
order (shuffle_nets, seed = --seed + attempt) and --jobs attempts run at
once. An attempt is rejected when Freerouting writes no session or runs
OVERRUN_PASSES past --passes, the import fails, DRC reports any unconnected
non-GND item afterwards (pilink-dbu), or a trial pour (gnd_preview) leaves
GND copper that cannot be joined to the main ground, or (gnd_paths.gate,
pilink-93a) the regulator's ground or a nearby decoupler reaches U101's
exposed pad only by a long copper path. The seed of the accepted attempt is
printed. --seed N --tries 1 reproduces it only from a byte-identical
stripped board: a fresh place.py + preroute.py exports the items in another
order, and Freerouting then routes differently for the same seed. The
accepted session is kept as hardware/routing/accepted.ses so the committed
routing can be re-imported (pcbnew.ImportSpecctraSES on the stripped board).

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
import gnd_paths

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
BOARD = os.path.join(HW, "pico-link-hw.kicad_pcb")
WORK = os.path.join(HW, ".autoroute")
STRIPPED = os.path.join(WORK, "stripped.kicad_pcb")
SES_OUT = os.path.join(HW, "routing", "accepted.ses")   # the accepted session, committed


ROUTE_TIMEOUT = 900   # seconds; a normal run takes 3-6 minutes
# v2.0.1 does not stop at -mp while a connection is unrouted; a run that
# finishes does so within ~26 passes here, so one this far past the limit
# is abandoned
OVERRUN_PASSES = 5
# Freerouting autoroute settings written into the DSN (edit_dsn): its via
# cost (default 50) and the B.Cu trace cost relative to F.Cu
VIA_COST = 40
B_COST = 4.0
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


def edit_dsn(text):
    """GND out of the netlist (its locked copper as keepouts); +10um clearance."""
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
    # Freerouting's own autorouter settings. The per-layer trace costs had
    # no measurable effect (see the module docstring), but the runs that
    # finished were all made with this block, and the same DSN without it
    # did not finish (pilink-r1h), so it stays.
    settings = ("    (autoroute_settings\n"
                "      (fanout off) (autoroute on) (postroute on) (vias on)\n"
                f"      (via_costs {VIA_COST}) (plane_via_costs 5)\n"
                "      (start_ripup_costs 100) (start_pass_no 1)\n"
                "      (layer_rule F.Cu (active on) (preferred_direction horizontal)\n"
                "        (preferred_direction_trace_costs 1.0)\n"
                "        (against_preferred_direction_trace_costs 1.0))\n"
                "      (layer_rule B.Cu (active on) (preferred_direction vertical)\n"
                f"        (preferred_direction_trace_costs {B_COST})\n"
                f"        (against_preferred_direction_trace_costs {B_COST}))\n"
                "    )\n")
    # after the (layer ...) scopes: Freerouting resolves layer_rule names
    # against layers it has already read
    k = text.index("    (boundary", text.index("  (structure"))
    return text[:k] + settings + text[k:]


def shuffle_nets(text, seed):
    """The DSN with its (net ...) entries in a seeded random order (seed 0:
    unchanged). Freerouting is deterministic: the same DSN gives the same
    result every time, so re-running a DSN that did not finish is useless,
    while any change to the input (even only the order of items) gives a
    different routing. Shuffling the net order is a reproducible way to get
    another try (pilink-r1h)."""
    if seed == 0:
        return text
    import random
    key = "\n    (net "
    a = text.index(key, text.index("  (network"))
    b = text.index("\n    (class ", a)
    nets = [key + n for n in text[a:b].split(key)[1:]]
    random.Random(seed).shuffle(nets)
    return text[:a] + "".join(nets) + text[b:]


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


def gnd_preview(board_path):
    """Pour, stitch and join a copy of the routed board as zones.py will,
    and return the GND islands left (zones.gnd_islands). Freerouting never
    sees GND, so it can box a fan-out via or a B.Cu GND pad into a pocket
    of signal tracks; zones.py joins such a pocket to the main ground with a
    track (gnd_repair), and a routing where even that finds no legal path is
    retried rather than accepted."""
    import zones
    b = pcbnew.LoadBoard(board_path)
    zones.split_at_t_joins(b)
    zones.prune_dangling_locked(b)
    zones.add_pours(b)
    zones.pour_and_join(b)
    return zones.gnd_islands(b), b


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


class FreeroutingJob:
    """One Freerouting run on one DSN text in its own work dir under WORK
    (several can run at once: route.py --jobs)."""

    def __init__(self, args, dsn_text, seed):
        self.args, self.seed = args, seed
        self.work = os.path.join(WORK, f"seed{seed}")
        shutil.rmtree(self.work, ignore_errors=True)
        os.makedirs(self.work)
        with open(os.path.join(self.work, "board.dsn"), "w") as fh:
            fh.write(dsn_text)
        self.ses = os.path.join(self.work, "board.ses")
        self.logpath = os.path.join(self.work, "freerouting.log")
        fr_args = ["-de", "{w}/board.dsn", "-do", "{w}/board.ses",
                   "--gui.enabled=false", "-mp", str(args.passes)]
        self.container = self.docker = None
        if shutil.which("java"):
            cmd = ["java", "-jar", args.jar] + [a.format(w=self.work) for a in fr_args]
        else:
            self.docker = shutil.which("docker") or shutil.which("podman")
            if not self.docker:
                sys.exit("need java 21+ or docker/podman to run Freerouting")
            self.container = f"pilink-freerouting-{os.getpid()}-{seed}"
            cmd = [self.docker, "run", "--rm", "--name", self.container,
                   "-u", f"{os.getuid()}:{os.getgid()}",
                   "-e", "HOME=/work",
                   "-v", f"{self.work}:/work", "-v", f"{args.jar}:/app/freerouting.jar:ro",
                   "eclipse-temurin:21-jre", "java", "-jar", "/app/freerouting.jar"
                   ] + [a.format(w="/work") for a in fr_args]
        print(f"[seed {seed}] running:", " ".join(cmd), flush=True)
        self.log = open(self.logpath, "w")
        self.proc = subprocess.Popen(cmd, stdout=self.log, stderr=subprocess.STDOUT)
        self.t0 = time.time()

    def kill(self):
        self.proc.kill()
        # killing the docker CLI leaves the container running (and holding
        # the CPU): remove it explicitly
        if self.container:
            subprocess.run([self.docker, "rm", "-f", self.container],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.proc.wait()
        self.log.close()

    def poll(self):
        """None while running; else (ses path or None, message)."""
        if self.proc.poll() is None:
            with open(self.logpath) as fh:
                logtext = fh.read()
            # Freerouting can die in a worker thread and leave the JVM up
            # (e.g. a DSN it could not read: "board is null")
            if any(s in logtext for s in FATAL_LOG):
                self.kill()
                return None, "Freerouting crashed (see its log)"
            # v2.0.1 does not stop at -mp while a connection is unrouted
            passes = logtext.count("Auto-router pass #")
            if passes > self.args.passes + OVERRUN_PASSES:
                self.kill()
                return None, f"ran {passes} passes without finishing"
            if time.time() - self.t0 > ROUTE_TIMEOUT:
                self.kill()
                return None, f"did not finish within {ROUTE_TIMEOUT}s"
            return None
        self.log.close()
        if not os.path.isfile(self.ses) or os.path.getsize(self.ses) == 0:
            return None, "Freerouting wrote no session file"
        # ImportSpecctraSES aborts the whole import if any reference in the
        # session's (placement ...) block fails its lookup. A headless run
        # never moves parts, so drop the block.
        text = open(self.ses).read()
        start = text.find("(placement")
        if start >= 0:
            depth = 0
            for i in range(start, len(text)):
                depth += {"(": 1, ")": -1}.get(text[i], 0)
                if depth == 0:
                    text = text[:start] + text[i + 1:]
                    break
            with open(self.ses, "w") as fh:
                fh.write(text)
        passes = open(self.logpath).read().count("Auto-router pass #")
        return self.ses, f"finished after {passes} passes"


def accept(ses, seed):
    """Import a session into the stripped board; returns the board if it has
    no unconnected signal and no unjoinable GND island, else None."""
    board = pcbnew.LoadBoard(STRIPPED)
    # the session has no GND (it was not in the DSN's netlist), and the
    # import replaces all tracks: put the locked GND copper back
    gnd = [_clone_spec(t) for t in board.GetTracks()
           if t.GetNetname() == "GND" and t.IsLocked()]
    if not pcbnew.ImportSpecctraSES(board, ses):
        print(f"[seed {seed}] SES import failed")
        return None
    for t in [t for t in board.GetTracks() if t.GetNetname() == "GND"]:
        board.Remove(t)
    for spec in gnd:
        _restore(board, spec)
    out = os.path.join(os.path.dirname(ses), "routed.kicad_pcb")
    pcbnew.SaveBoard(out, board)
    bad = unconnected_signals(out)
    if bad:
        print(f"[seed {seed}] {len(bad)} unconnected non-GND item(s) after routing:")
        for b in bad[:10]:
            print("   ", b)
        return None
    islands, poured = gnd_preview(out)
    if islands:
        print(f"[seed {seed}] {len(islands)} GND island(s) left after a trial pour:")
        for s in islands:
            print("   ", s)
        return None
    # pilink-93a: connected is not enough; the regulator's ground and the
    # nearby decouplers must reach the EP by a short copper path
    far = gnd_paths.gate(poured)
    if far:
        print(f"[seed {seed}] {len(far)} GND path(s) to the U101 EP too long after a trial pour:")
        for s in far:
            print("   ", s)
        return None
    return board


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=30)
    ap.add_argument("--tries", type=int, default=8,
                    help="Freerouting attempts (net order seeds) before giving up")
    ap.add_argument("--seed", type=int, default=0,
                    help="net order seed of the first attempt (shuffle_nets)")
    ap.add_argument("--jobs", type=int, default=4,
                    help="Freerouting runs at once (each on its own seed)")
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

    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    dsn = os.path.join(WORK, "board.dsn")
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        sys.exit("DSN export failed")
    with open(dsn) as fh:
        dsn_text = edit_dsn(fh.read())
    remove_route_keepout(board)
    remove_l101_route_keepout(board)
    remove_plane_keepouts(board)
    # the stripped, pre-routed board goes to WORK: the real board is only
    # overwritten once an attempt is accepted
    pcbnew.SaveBoard(STRIPPED, board)
    # with the project file beside it, so a board loaded from there keeps
    # the net classes (and saving it over BOARD writes them back unchanged)
    shutil.copyfile(os.path.splitext(BOARD)[0] + ".kicad_pro",
                    os.path.splitext(STRIPPED)[0] + ".kicad_pro")

    # Freerouting is deterministic per DSN, so each attempt gets its own net
    # order (shuffle_nets); `--seed N --tries 1` reproduces attempt N.
    seeds = list(range(args.seed, args.seed + args.tries))
    running, result = [], None
    try:
        while (seeds or running) and result is None:
            while seeds and len(running) < args.jobs:
                s = seeds.pop(0)
                running.append(FreeroutingJob(args, shuffle_nets(dsn_text, s), s))
            time.sleep(5)
            for job in list(running):
                r = job.poll()
                if r is None:
                    continue
                running.remove(job)
                ses, msg = r
                print(f"[seed {job.seed}] {msg}", flush=True)
                if ses is None:
                    continue
                b = accept(ses, job.seed)
                if b is not None:
                    result = (b, job.seed, ses)
                    break
    finally:
        for job in running:
            job.kill()
    if result is None:
        sys.exit(f"route.py: no clean Freerouting result for seeds "
                 f"{args.seed}..{args.seed + args.tries - 1}; see {WORK}/seed*/freerouting.log")
    board, seed, ses = result
    pcbnew.SaveBoard(BOARD, board)
    os.makedirs(os.path.dirname(SES_OUT), exist_ok=True)
    shutil.copyfile(ses, SES_OUT)
    tracks = list(board.GetTracks())
    vias = sum(1 for t in tracks if t.Type() == pcbnew.PCB_VIA_T)
    length = {L: sum(t.GetLength() for t in tracks
                     if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == L) / 1e6
              for L in (pcbnew.F_Cu, pcbnew.B_Cu)}
    print(f"imported {len(tracks) - vias} track segments, {vias} vias; "
          f"F.Cu {length[pcbnew.F_Cu]:.0f}mm, B.Cu {length[pcbnew.B_Cu]:.0f}mm "
          f"of track (net order seed {seed}; reproduce with --seed {seed} --tries 1)")
    if not args.keep:
        shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    main()
