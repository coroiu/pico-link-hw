#!/usr/bin/env python3
"""Run kicad-cli DRC on the board and print a per-type summary.

Usage (from hardware/):  python3 scripts/drc_summary.py [-v]
Exits non-zero if there is any error-severity violation or unconnected item.
"""
import collections
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "..", "pico-link-hw.kicad_pcb")


def main():
    verbose = "-v" in sys.argv
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "drc.json")
        subprocess.run(
            ["kicad-cli", "pcb", "drc", "--severity-all", "--schematic-parity",
             "--format", "json", "-o", out, BOARD],
            check=True, stdout=subprocess.DEVNULL)
        with open(out) as fh:
            rep = json.load(fh)
    viol = rep.get("violations", [])
    unconnected = rep.get("unconnected_items", [])
    parity = rep.get("schematic_parity", [])
    counts = collections.Counter((v["severity"], v["type"]) for v in viol)
    for (sev, typ), n in sorted(counts.items()):
        print(f"{sev:8} {typ:28} {n}")
    errors = sum(n for (sev, _), n in counts.items() if sev == "error")
    print(f"violations: {len(viol)} ({errors} errors), "
          f"unconnected: {len(unconnected)}, schematic parity: {len(parity)}")
    if verbose:
        for v in viol + unconnected + parity:
            if v["severity"] == "error" or v in unconnected or v in parity:
                items = " / ".join(i["description"] for i in v.get("items", []))
                print(f"  {v['type']}: {v['description']} | {items}")
    sys.exit(1 if errors or unconnected else 0)


if __name__ == "__main__":
    main()
