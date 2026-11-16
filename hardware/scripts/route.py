#!/usr/bin/env python3
"""Autoroute pico-link-hw.kicad_pcb with Freerouting (pilink-7el.12).

Usage (from hardware/):
    python3 scripts/route.py [--passes N] [--jar PATH]

Specctra round-trip: strip existing tracks/vias/zones (except the locked
tracks/vias scripts/preroute.py laid for USB D+/D- and the crystal) -> export DSN ->
Freerouting (headless) -> import SES -> save. Run scripts/widen.py and
scripts/zones.py next.

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
import os
import re
import shutil
import subprocess
import sys

import pcbnew

from preroute import PREROUTE_NETS
from sw_keepout import add_sw_keepouts

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
BOARD = os.path.join(HW, "pico-link-hw.kicad_pcb")
WORK = os.path.join(HW, ".autoroute")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=30)
    ap.add_argument("--jar", default=os.environ.get(
        "FREEROUTING_JAR", os.path.expanduser("~/.kicad-mcp/freerouting.jar")))
    ap.add_argument("--keep", action="store_true", help="keep the DSN/SES work dir")
    args = ap.parse_args()
    if not os.path.isfile(args.jar):
        sys.exit(f"freerouting jar not found: {args.jar}")

    board = pcbnew.LoadBoard(BOARD)
    # Keep scripts/preroute.py's locked tracks and vias (exported as fixed
    # wiring); drop everything else, including zones.py's locked stitching
    # vias (those are not on a pre-routed net).
    for t in list(board.GetTracks()):
        keep = t.IsLocked() and t.GetNetname() in PREROUTE_NETS
        if not keep:
            board.Remove(t)
    for z in list(board.Zones()):
        board.Remove(z)
    # Alps SKRTLAE010 no-copper areas: Freerouting exports rule areas as
    # keepouts, so tracks route around the switch bodies (pilink-ge9).
    add_sw_keepouts(board)

    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    dsn = os.path.join(WORK, "board.dsn")
    ses = os.path.join(WORK, "board.ses")
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        sys.exit("DSN export failed")

    # Freerouting rounds to its own grid and can land a few um under the
    # clearance it was given; hand it +10um so KiCad's DRC sees no slivers.
    text = open(dsn).read()
    text = re.sub(r"\(clearance (\d+(?:\.\d+)?)\)",
                  lambda m: f"(clearance {float(m.group(1)) + 10:g})", text)
    with open(dsn, "w") as fh:
        fh.write(text)

    fr_args = ["-de", "{w}/board.dsn", "-do", "{w}/board.ses",
               "--gui.enabled=false", "-mp", str(args.passes)]
    if shutil.which("java"):
        cmd = ["java", "-jar", args.jar] + [a.format(w=WORK) for a in fr_args]
    else:
        docker = shutil.which("docker") or shutil.which("podman")
        if not docker:
            sys.exit("need java 21+ or docker/podman to run Freerouting")
        cmd = [docker, "run", "--rm", "-u", f"{os.getuid()}:{os.getgid()}",
               "-e", "HOME=/work",
               "-v", f"{WORK}:/work", "-v", f"{args.jar}:/app/freerouting.jar:ro",
               "eclipse-temurin:21-jre", "java", "-jar", "/app/freerouting.jar"
               ] + [a.format(w="/work") for a in fr_args]
    print("running:", " ".join(cmd), flush=True)
    with open(os.path.join(WORK, "freerouting.log"), "w") as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=False)
    if not os.path.isfile(ses):
        sys.exit(f"Freerouting produced no SES; see {WORK}/freerouting.log")

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

    if not pcbnew.ImportSpecctraSES(board, ses):
        sys.exit("SES import failed")
    pcbnew.SaveBoard(BOARD, board)
    tracks = [t for t in board.GetTracks()]
    vias = sum(1 for t in tracks if t.Type() == pcbnew.PCB_VIA_T)
    print(f"imported {len(tracks) - vias} track segments, {vias} vias")
    if not args.keep:
        shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    main()
