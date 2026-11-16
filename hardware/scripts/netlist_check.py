#!/usr/bin/env python3
"""Diff the board's pad->net map pin-for-pin against the schematic netlist.

Usage (from hardware/):  python3 scripts/netlist_check.py

Exports a fresh netlist from the root schematic with kicad-cli and compares
every (ref, pin) -> net against the pads in pico-link-hw.kicad_pcb. Also
lists nets that reach only one pad (legal for ERC, but each one is either a
deliberately spare pin or a connection somebody forgot).
Exits non-zero on any pin mismatch.
"""
import collections
import os
import re
import subprocess
import sys
import tempfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
BOARD = os.path.join(HW, "pico-link-hw.kicad_pcb")
SCH = os.path.join(HW, "pico-link-hw.kicad_sch")


def schematic_nets():
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "netlist.net")
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "-o", out, SCH],
                       check=True, stdout=subprocess.DEVNULL)
        text = open(out).read()
    pins = {}
    nets = text[text.index("(nets"):]
    for block in re.split(r"\(net\s+\(code", nets)[1:]:
        name = re.search(r'\(name "([^"]*)"\)', block).group(1)
        for n in re.finditer(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', block):
            pins[(n.group(1), n.group(2))] = name
    return pins


def main():
    sch = schematic_nets()
    board = pcbnew.LoadBoard(BOARD)
    brd = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNumber():
                brd.setdefault((fp.GetReference(), pad.GetNumber()), set()).add(pad.GetNetname())

    bad = 0
    for key, net in sorted(sch.items()):
        got = brd.get(key)
        if got is None:
            print(f"MISSING PAD  {key[0]}.{key[1]} (schematic net {net})")
            bad += 1
        elif got != {net}:
            print(f"NET MISMATCH {key[0]}.{key[1]}: schematic {net!r} board {sorted(got)}")
            bad += 1
    for key, nets in sorted(brd.items()):
        if key not in sch and nets != {""}:
            print(f"EXTRA NET    {key[0]}.{key[1]}: board {sorted(nets)} not in schematic")
            bad += 1
    print(f"{len(sch)} schematic pins compared, {bad} mismatches")

    by_net = collections.defaultdict(set)
    for (ref, pin), net in sch.items():
        by_net[net].add(f"{ref}.{pin}")
    single = sorted(n for n, p in by_net.items()
                    if len(p) == 1 and not n.startswith("unconnected-"))
    print(f"{len(single)} single-pad nets (not marked no-connect):")
    print("  " + " ".join(single))

    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
