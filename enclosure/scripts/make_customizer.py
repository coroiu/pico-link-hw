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
    textual inline would not reproduce faithfully;
  - after inlining, any `include <` / `use <` left in code (outside comments
    and strings, e.g. a mid-line include) is refused.

The only intended difference from the source is an explicit per-target
override of a Customizer default (see TARGETS): back_shell's copy defaults
to PART = "back_shell" so a published file downloads the printable part.
"""
import argparse
import os
import re
import sys

ENC = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# (source, generated, default overrides), paths relative to enclosure/.
# Overrides change the DEFAULT of a Customizer parameter in the generated
# copy only (the source keeps its own): {NAME: new value expression}. The
# parameter must be a top-level assignment above /* [Hidden] */, appear
# exactly once, and, for a dropdown, the new value must be one of its
# options; the annotation (and so every option) is kept.
#   back_shell PART: the source defaults to "assembly" (shell + display-only
#   rubber feet) for working in the repo; a published Customizer file should
#   download the printable part by default.
TARGETS = [
    ("back_shell.scad", "dist/back_shell_customizer.scad", {"PART": '"back_shell"'}),
]

INCLUDE_RE = re.compile(r"^\s*include\s*<([^>]+)>\s*;?\s*(//.*)?$")
USE_RE = re.compile(r"^\s*use\s*<([^>]+)>")
# Anchored: the marker must start its line (a mention inside a // comment,
# as in back_shell.scad's header, does not count).
HIDDEN_RE = re.compile(r"^\s*/\*\s*\[\s*Hidden\s*\]\s*\*/")


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
        if not stack and not in_block and HIDDEN_RE.search(line):
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


def code_only(text):
    """`text` with comments and string literals blanked (newlines kept), for
    scanning what OpenSCAD would actually parse."""
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("\n" * text.count("\n", i, j))
            i = j
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            out.append('""')
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


LEFTOVER_RE = re.compile(r"\b(include|use)\s*<")


def refuse_leftover_includes(src, body):
    """After inlining, no include/use may remain in code (e.g. a mid-line one
    the line-based inliner did not touch)."""
    for lineno, line in enumerate(code_only(body).split("\n"), 1):
        m = LEFTOVER_RE.search(line)
        if m:
            sys.exit("make_customizer: %s: `%s <...>` left in the flattened code at line %d "
                     "(put each include on its own line)" % (src, m.group(1), lineno))


def apply_overrides(src, body, overrides):
    lines = body.split("\n")
    try:
        hidden = next(i for i, l in enumerate(lines) if HIDDEN_RE.search(l))
    except StopIteration:
        sys.exit("make_customizer: %s has no /* [Hidden] */ marker" % src)
    for name, value in overrides.items():
        pat = re.compile(r"^(%s\s*=\s*)([^;]+)(;.*)$" % re.escape(name))
        hits = [i for i in range(hidden) if pat.match(lines[i])]
        if len(hits) != 1:
            sys.exit("make_customizer: %s: override %s matched %d Customizer lines (want 1)"
                     % (src, name, len(hits)))
        m = pat.match(lines[hits[0]])
        ann = re.search(r"//\s*\[([^\]]*)\]", m.group(3))
        if ann and ":" not in ann.group(1):
            opts = [o.strip() for o in ann.group(1).split(",")]
            if value.strip('"') not in opts:
                sys.exit("make_customizer: %s: override %s = %s is not one of %s"
                         % (src, name, value, opts))
        lines[hits[0]] = m.group(1) + value + m.group(3)
    return "\n".join(lines)


def generate(src, overrides):
    body = flatten(os.path.join(ENC, src))
    refuse_leftover_includes(src, body)
    body = apply_overrides(src, body, overrides)
    notes = "".join("//   %s defaults to %s here (see TARGETS in the script).\n" % (n, v)
                    for n, v in overrides.items())
    header = (
        "// GENERATED FILE -- do not edit. Single-file Customizer copy of\n"
        "// enclosure/%s with its includes inlined, for online OpenSCAD\n"
        "// configurators (e.g. MakerWorld's Parametric Model Maker). Edit the source\n"
        "// and regenerate: python3 enclosure/scripts/make_customizer.py\n"
        "%s"
        "\n" % (src, ("// Default overrides vs. the source:\n" + notes) if notes else "")
    )
    return header + body


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if any generated file is missing or stale")
    args = ap.parse_args()
    stale = []
    for src, dst, overrides in TARGETS:
        text = generate(src, overrides)
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
