#!/usr/bin/env python3
"""Generate single-file Customizer copies of enclosure parts (pilink-c6z).

Online OpenSCAD configurators (MakerWorld's Parametric Model Maker and
similar) take ONE .scad file and cannot resolve a project-local
`include <common.scad>`. This script writes a self-contained copy of each
target with every local `include <...>` replaced, in place, by the included
file's text (recursively). OpenSCAD's `include` is plain textual
substitution, so the flattened file evaluates exactly like the original.

The repo's sources stay the single source of truth; the generated files
under enclosure/dist/ are committed so they can be uploaded directly, and
`--check` (run by enclosure/scripts/check_fit.sh) fails if any is stale.

    python3 enclosure/scripts/make_customizer.py           # (re)write dist/
    python3 enclosure/scripts/make_customizer.py --check   # exit 1 if stale

Rules enforced, so the Customizer panel matches the source file's:
  - every `include` must come after the target's `/* [Hidden] */` marker,
    so the inlined constants never show up as Customizer parameters and the
    parameter block stays at the very top of the file;
  - `use <...>` is refused: it imports only modules/functions, which a
    textual inline would not reproduce faithfully.
"""
import argparse
import os
import re
import sys

ENC = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# (source, generated), both relative to enclosure/.
TARGETS = [
    ("back_shell.scad", "dist/back_shell_customizer.scad"),
]

INCLUDE_RE = re.compile(r"^\s*include\s*<([^>]+)>\s*;?\s*(//.*)?$")
USE_RE = re.compile(r"^\s*use\s*<([^>]+)>")
HIDDEN_RE = re.compile(r"/\*\s*\[\s*Hidden\s*\]\s*\*/")


def rel(path):
    return os.path.relpath(path, ENC).replace(os.sep, "/")


def code_lines(text):
    """Yield (line, in_block_comment_at_start) so include/use lines inside a
    /* ... */ block are left alone."""
    in_block = False
    for line in text.splitlines():
        yield line, in_block
        i = 0
        while i < len(line):
            if in_block:
                j = line.find("*/", i)
                if j < 0:
                    break
                in_block, i = False, j + 2
            else:
                k = line.find("/*", i)
                c = line.find("//", i)
                if k < 0 or (0 <= c < k):
                    break
                in_block, i = True, k + 2


def flatten(path, stack=()):
    path = os.path.normpath(path)
    if path in stack:
        sys.exit("make_customizer: include cycle: " + " -> ".join(rel(p) for p in stack + (path,)))
    with open(path, encoding="utf-8") as f:
        text = f.read()
    out = []
    hidden_seen = False
    for line, in_block in code_lines(text):
        if not stack and HIDDEN_RE.search(line):
            hidden_seen = True
        m = None if in_block else INCLUDE_RE.match(line)
        if m:
            if not stack and not hidden_seen:
                sys.exit("make_customizer: %s includes <%s> before /* [Hidden] */; the inlined "
                         "constants would appear as Customizer parameters" % (rel(path), m.group(1)))
            inc = os.path.join(os.path.dirname(path), m.group(1))
            if not os.path.isfile(inc):
                sys.exit("make_customizer: %s: include <%s> not found next to it" % (rel(path), m.group(1)))
            out.append("// ===== BEGIN inlined %s (was: %s) =====" % (rel(inc), line.strip()))
            out.append(flatten(inc, stack + (path,)).rstrip("\n"))
            out.append("// ===== END inlined %s =====" % rel(inc))
        elif not in_block and USE_RE.match(line):
            sys.exit("make_customizer: %s: `use <...>` cannot be inlined faithfully" % rel(path))
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def generate(src):
    body = flatten(os.path.join(ENC, src))
    header = (
        "// GENERATED FILE -- do not edit. Single-file Customizer copy of\n"
        "// enclosure/%s with its includes inlined, for online OpenSCAD\n"
        "// configurators (e.g. MakerWorld's Parametric Model Maker). Edit the source\n"
        "// and regenerate: python3 enclosure/scripts/make_customizer.py\n"
        "\n" % src
    )
    return header + body


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if any generated file is missing or stale")
    args = ap.parse_args()
    stale = []
    for src, dst in TARGETS:
        text = generate(src)
        dpath = os.path.join(ENC, dst)
        try:
            with open(dpath, encoding="utf-8") as f:
                current = f.read()
        except FileNotFoundError:
            current = None
        if current == text:
            print("up to date: enclosure/%s" % dst)
            continue
        if args.check:
            stale.append(dst)
            print("STALE: enclosure/%s (source enclosure/%s or its includes changed)" % (dst, src))
        else:
            os.makedirs(os.path.dirname(dpath), exist_ok=True)
            with open(dpath, "w", encoding="utf-8") as f:
                f.write(text)
            print("wrote: enclosure/%s" % dst)
    if stale:
        print("Regenerate with: python3 enclosure/scripts/make_customizer.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
