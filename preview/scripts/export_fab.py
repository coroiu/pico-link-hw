#!/usr/bin/env python3
"""Build the preview's "Files" downloads: JLCPCB fab files + enclosure STLs.

usage: export_fab.py PCB SCH BOM_MD STL_DIR OUT_DIR

Writes, under OUT_DIR (staged by the caller, then swapped in):
  <name>-gerbers.zip      Gerbers (Protel extensions) + Excellon drill (PTH/NPTH)
  <name>-bom-jlcpcb.csv   Comment, Designator, Footprint, LCSC Part #
  <name>-cpl-jlcpcb.csv   Designator, Mid X, Mid Y, Layer, Rotation
  stl/<part>.stl          copied from STL_DIR/stl (one per printed part)
  fab.json                manifest the page builds its Files section from

The schematic carries no LCSC field; the LCSC number per designator lives in
hardware/BOM.md's per-sheet tables, which are parsed here (ranges like
"C106-C117" and comma lists are expanded). DNP parts are excluded from the
BOM and CPL (kicad-cli --exclude-dnp), as hardware/BOM.md assembly flag 0
requires.
"""
import csv
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

# Footprint libraries that are project-local (hand-authored or vendor-copied),
# as opposed to KiCad's stock libraries -- see hardware/fp-lib-table.
CUSTOM_LIBS = {"RP2350_80QFN", "Connector_FPC", "Connector_USB_Custom"}
# Designator prefixes whose JLCPCB rotation convention commonly differs from
# KiCad's (polarised / orientation-dependent parts). Plain R/C are symmetric.
ROT_SENSITIVE = ("U", "Y", "J", "SW", "L", "D", "Q", "F")
GERBER_LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("%s failed:\n%s%s" % (cmd[:4], p.stdout, p.stderr))


def natkey(d):
    m = re.match(r"([A-Za-z]+)(\d+)", d)
    return (m.group(1), int(m.group(2))) if m else (d, 0)


def expand_refs(cell):
    refs = []
    for tok in re.split(r"[,\s]+", cell.replace("**", "").strip()):
        m = re.fullmatch(r"([A-Za-z]+)(\d+)-(?:\1)?(\d+)", tok)
        if m:
            refs += ["%s%d" % (m.group(1), n) for n in range(int(m.group(2)), int(m.group(3)) + 1)]
        elif re.fullmatch(r"[A-Za-z]+\d+", tok):
            refs.append(tok)
    return refs


def parse_bom_md(path):
    """designator -> LCSC number, from the BOM.md tables that have an LCSC column."""
    lcsc, col = {}, None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|"):
                col = None
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and cells[0] == "Ref":
                col = cells.index("LCSC") if "LCSC" in cells else None
                continue
            if col is None or col >= len(cells) or set(cells[0]) <= set("-: "):
                continue
            m = re.search(r"\bC\d{3,}\b", cells[col])
            if m:
                for r in expand_refs(cells[0]):
                    lcsc[r] = m.group(0)
    return lcsc


def main():
    pcb, sch, bom_md, stl_dir, out = sys.argv[1:6]
    name = os.path.splitext(os.path.basename(pcb))[0]
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="fab")
    files = []

    def add(path, label, desc, **extra):
        files.append(dict(file=os.path.relpath(path, out), label=label, desc=desc,
                          size=os.path.getsize(path), **extra))

    # ---- Gerbers + drill -> zip. Protel extensions (kicad-cli default),
    # soldermask subtracted from silkscreen, zones refilled, no job file;
    # drill is Excellon, mm, decimal zeros, PTH and NPTH in separate files --
    # the settings JLCPCB's KiCad guide asks for.
    gdir = os.path.join(tmp, "gerber")
    os.makedirs(gdir)
    run(["kicad-cli", "pcb", "export", "gerbers", "--layers", GERBER_LAYERS,
         "--subtract-soldermask", "--check-zones", "--no-x2", "-o", gdir, pcb])
    run(["kicad-cli", "pcb", "export", "drill", "--format", "excellon",
         "--excellon-units", "mm", "--excellon-zeros-format", "decimal",
         "--excellon-separate-th", "--drill-origin", "absolute", "-o", gdir, pcb])
    for junk in glob.glob(os.path.join(gdir, "*.gbrjob")):
        os.remove(junk)
    zpath = os.path.join(out, name + "-gerbers.zip")
    layer_files = sorted(os.listdir(gdir))
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in layer_files:
            z.write(os.path.join(gdir, fn), fn)
    add(zpath, "Gerbers + drill (zip)",
        "%d files: 2-layer copper, mask, silkscreen, paste, edge cuts (Protel "
        "extensions) + Excellon PTH/NPTH drill. Upload to JLCPCB as-is." % len(layer_files),
        contents=layer_files)

    # ---- BOM: one kicad-cli row per placed designator, regrouped here so the
    # LCSC number (from BOM.md) is part of the grouping key.
    raw_bom = os.path.join(tmp, "bom.csv")
    run(["kicad-cli", "sch", "export", "bom", "--exclude-dnp",
         "--fields", "Reference,Value,Footprint", "--labels", "Designator,Value,Footprint",
         "--group-by", "", "-o", raw_bom, sch])
    lcsc = parse_bom_md(bom_md)
    with open(raw_bom, newline="", encoding="utf-8") as f:
        placed = [r for r in csv.DictReader(f) if r["Designator"]]
    groups, order = {}, []
    for r in placed:
        key = (r["Value"], r["Footprint"].split(":", 1)[-1], lcsc.get(r["Designator"], ""))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r["Designator"])
    bpath = os.path.join(out, name + "-bom-jlcpcb.csv")
    with open(bpath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for key in sorted(order, key=lambda k: min(natkey(d) for d in groups[k])):
            w.writerow([key[0], ",".join(sorted(groups[key], key=natkey)), key[1], key[2]])
    missing = sorted((r["Designator"] for r in placed if r["Designator"] not in lcsc), key=natkey)
    add(bpath, "BOM (JLCPCB CSV)",
        "%d placed parts in %d lines; DNP excluded. Columns: Comment, Designator, "
        "Footprint, LCSC Part #. LCSC numbers come from hardware/BOM.md." % (len(placed), len(order)))

    # ---- CPL, top and bottom in one file.
    raw_pos = os.path.join(tmp, "pos.csv")
    run(["kicad-cli", "pcb", "export", "pos", "--exclude-dnp", "--format", "csv",
         "--units", "mm", "--side", "both", "-o", raw_pos, pcb])
    with open(raw_pos, newline="", encoding="utf-8") as f:
        pos = list(csv.DictReader(f))
    cpath = os.path.join(out, name + "-cpl-jlcpcb.csv")
    with open(cpath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in sorted(pos, key=lambda r: natkey(r["Ref"])):
            w.writerow([r["Ref"], "%.4f" % float(r["PosX"]), "%.4f" % float(r["PosY"]),
                        "Top" if r["Side"] == "top" else "Bottom", "%g" % float(r["Rot"])])
    nbot = sum(1 for r in pos if r["Side"] != "top")
    add(cpath, "CPL / pick-and-place (JLCPCB CSV)",
        "%d parts (%d top, %d bottom); DNP excluded. Columns: Designator, Mid X, "
        "Mid Y, Layer, Rotation." % (len(pos), len(pos) - nbot, nbot))

    # ---- Parts worth a second look in JLCPCB's placement preview.
    fp_of = {r["Designator"]: r["Footprint"] for r in placed}
    side_of = {r["Ref"]: r["Side"] for r in pos}
    flagged = []
    for d in sorted(fp_of, key=natkey):
        sensitive = d.startswith(ROT_SENSITIVE)
        why = []
        if fp_of[d].split(":")[0] in CUSTOM_LIBS:
            why.append("custom/project-local footprint (pad geometry and 3D origin not from KiCad's stock library)")
        if d not in lcsc:
            why.append("no LCSC number (BOM.md lists it as not in JLCPCB's catalog)")
        if sensitive:
            why.append("orientation-dependent part: JLCPCB's reference rotation may differ from KiCad's")
            if side_of.get(d, "top") != "top":
                why.append("bottom side: mirrored rotation convention")
        if why:
            flagged.append(dict(ref=d, footprint=fp_of[d], reasons=why))

    # ---- Enclosure STLs, one per printed part: whatever export_enclosure.py
    # rendered (the part list is not duplicated here).
    labels = {}
    parts_json = os.path.join(stl_dir, "parts.json")
    if os.path.exists(parts_json):
        with open(parts_json) as f:
            labels = {p["key"]: p["label"] for p in json.load(f).get("parts", [])}
    os.makedirs(os.path.join(out, "stl"), exist_ok=True)
    for src in sorted(glob.glob(os.path.join(stl_dir, "stl", "*.stl"))):
        key = os.path.splitext(os.path.basename(src))[0]
        dst = os.path.join(out, "stl", key + ".stl")
        shutil.copyfile(src, dst)
        add(dst, "STL: " + labels.get(key, key),
            "OpenSCAD render in the part's own frame (not the assembled pose).", group="stl")

    manifest = dict(
        generated=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        commit=os.environ.get("FAB_SOURCE_COMMIT", "unknown"), files=files,
        missing_lcsc=missing, flagged=flagged, placed=len(placed), cpl_rows=len(pos))
    with open(os.path.join(out, "fab.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    shutil.rmtree(tmp, ignore_errors=True)
    print("[fab] %d files; BOM %d parts (%d without LCSC), CPL %d rows, %d flagged"
          % (len(files), len(placed), len(missing), len(pos), len(flagged)))


if __name__ == "__main__":
    main()
