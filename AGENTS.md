# Agent Instructions

Shared project instructions for Claude Code (via `CLAUDE.md`, which imports
this file) and other agents. Edit them here, outside the bd-managed blocks
(`bd` rewrites those).

## Project

Custom PCB and 3D-printed enclosure for [Pico Link](https://github.com/coroiu/pico-link),
a USB-to-Bluetooth LDAC audio dongle with a screen. This repo replaces the
project's two stacked off-the-shelf dev boards with one purpose-built board,
designed for JLCPCB fab + assembly, plus a printed enclosure.

**No firmware lives here.** That's the separate pico-link repo, assumed to
sit next to this one (`../pico-link`). This repo only tracks the physical
design: schematic, PCB, BOM, enclosure.

Full design rationale: [`docs/plans/2026-11-13-custom-hardware-design.md`](docs/plans/2026-11-13-custom-hardware-design.md).
Settled component/architecture decisions: `.planning/decisions/`.
Current status and next steps: `.planning/roadmap.md`.

## Hardware (target architecture — not yet built)

- **RP2350B** — USB Audio Class device, display/UI, app logic. Same flash
  (16MB QSPI NOR) and PSRAM (8MB QSPI) parts as the Pimoroni Pico Plus 2 W
  this replaces.
- **ESP32-WROOM-32UE** — dedicated Bluetooth Classic coprocessor (U.FL
  antenna), running Espressif's HCI-over-UART controller firmware; BTstack
  on RP2350 stays the host. See
  `.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md` for why,
  instead of Raspberry Pi's RM2 module, and
  `.planning/decisions/2026-11-15-esp32-wroom-32ue-swap.md` for the -32U to
  -32UE swap.
- **Display** — Crystalfontz CFAF240320A0-024SN, ST7789V, 240x320 native
  rotated to 320x240, SPI, 800:1 contrast (up from the current 240x240
  panel). See
  `.planning/decisions/2026-11-15-display-panel-crystalfontz-cfaf240320a0.md`.
- **Input** — rotary encoder (sole directional control, double-duty by
  firmware context) + tact buttons, same logical layout as today minus the
  d-pad. See
  `.planning/decisions/2026-11-15-rotary-encoder-replaces-full-dpad.md`.
- **USB-C** exits the rear of the enclosure (vertical-mount receptacle on
  the PCB back, since the board stands upright).
- **Form factor** — upright desk-clock body (~75° from the table) on two
  splayed rear legs; knob left, screen middle, buttons right on one face;
  PCB parallel to the face. See
  `.planning/decisions/2026-11-15-upright-desk-clock-form-factor.md` and
  `docs/plans/2026-11-15-product-layout-proposal.md` (section 6c).

## Roadmap

The roadmap lives in `.planning/roadmap.md` plus beads. `bd ready` shows
what can be started now: KiCad schematic/BOM, the OpenSCAD enclosure, and a
few verification tasks (ESP32 HCI controller firmware-patch question,
Ezurio fallback doc, USB-C/antenna/FPC placement check).

## This repo has no build/test automation

There's no `cargo build`, no CI, no code to compile. "Quality gates" here
mean DRC/ERC in KiCad and dimension/fit checks in OpenSCAD — what's actually
available for these differs by tool, and an agent should say plainly which
checks it could and couldn't run rather than lumping both under one blanket
disclaimer:

- **KiCad**: `kicad-cli` is installed on this machine and runs headlessly —
  no GUI needed. `kicad-cli sch erc --severity-all --exit-code-violations`
  and `kicad-cli pcb drc` are real, runnable checks (as is
  `kicad-cli sch export netlist` for cross-sheet collision checks); run the
  relevant one after any schematic/PCB change and report the actual
  violation count, don't claim "no DRC/ERC possible here." What genuinely
  still needs a human with the GUI: visual/placement sign-off and anything
  `kicad-cli` doesn't check (silkscreen legibility, visual footprint
  sanity, final review before fab).
- **OpenSCAD**: installed on this machine (2021.01, user-level, as
  `openscad` on PATH). `openscad -o out.stl enclosure/<file>.scad` renders
  headlessly — run it after any enclosure change and report warnings,
  failed asserts and whether the result is a simple (manifold) solid. The
  preview Docker image also ships OpenSCAD. What still needs a human: a
  printed test fit, and anything a render can't show (feel, print quality).

KiCad and OpenSCAD were each previously documented here as "not
installed" after they had been added. Keep this note current if that
changes again, and if a needed tool is missing, ask the user to install
it rather than just noting the gap.

## Optional: KiCad MCP server (machine-specific, not assumed)

On machines where it's been set up, a `mixelpixx/KiCAD-MCP-Server`
installation lives outside this repo (under `~/mcp-servers/KiCAD-MCP-Server`)
and is registered with Claude Code as a **local-scope** MCP server named
`kicad` — local scope deliberately, since its config embeds this machine's
absolute paths (Node binary, Python venv) and writing that to the repo's own
`.mcp.json` (project scope) would violate the no-absolute-paths rule above.
It needs Node.js 18+ (this machine uses `nvm` for that, since its system
default was older) and a Python venv built with `--system-site-packages` so
it can import the system's `pcbnew`.

Its `KICAD_MCP_OPERATING_MODE` env var gates capability: `readonly` exposes
only inspection/validation tools (board/schematic info, ERC/DRC, nets,
clearance checks — tools outside the allow-list are hidden from the list
entirely, not just rejected on call); `write` (or unset) exposes everything,
including footprint placement and routing. Check `claude mcp list` for
whether it's configured and which mode it's in — don't assume either. A
newly-added or reconfigured MCP server's tools only become callable in a
**new** session; registering or reconfiguring it mid-conversation doesn't
make the change usable in that same conversation.

This is additional capability, not a dependency — `pilink-7el.9` (PCB
layout)'s own plan (headless `pcbnew` scripting + Freerouting, verified with
plain `kicad-cli pcb drc`) needs none of it and already works with zero
extra installs.

## Development workflow

- **Work comes from beads.** Pick from `bd ready` and claim with
  `bd update <id> --claim` before starting. One bead = one branch = one PR.
  File follow-up work you discover as new beads
  (`--deps discovered-from:<id>`).
- **Branches:** never commit to `main`. Name branches `<type>/<bead-id>-<slug>`.
- **Commits:** Conventional Commits (`feat`, `fix`, `chore`, `docs`,
  `refactor`). The bead ID goes in the PR body, not in commit messages.
- **The main session orchestrates:** it picks ready beads, claims them, and
  spawns a `bead-worker` for each, then a `code-reviewer` on each PR before
  merging. Workers don't claim — the orchestrator already did, which avoids
  races.
- **Review before merging:** run `code-reviewer` on bead PRs before merging
  and fix what it finds. Trivial changes (typos, docs-only tweaks) can skip
  it.
- **Done = bead closed.** Close a bead when its PR is merged. If the PR is
  waiting on the user, leave the bead `in_progress` and record the PR link
  with `bd note`.
- **Money and physical actions:** ordering PCBs, buying parts, or anything
  else that spends real money is the user's call, always — flag it, don't
  do it. Same for anything that needs a physical action only the user can
  take (soldering, measuring a printed part, plugging something in).

## Subagents

Most work on this repo — reading a datasheet, writing a design doc, editing
a KiCad/OpenSCAD file — doesn't need a specialized persona; just do it. The
roles below exist for when a task genuinely benefits from a narrower pass:

- **`architect`** (Opus): breaks an epic down into child beads with
  dependencies, acceptance criteria and design notes. Read-only on
  `hardware/`/`enclosure/`; only writes design docs and beads. Run it on an
  epic before implementation starts.
- **`cad-worker`** (Opus, effort high, `isolation: worktree`): like
  `bead-worker`, but for any bead that changes CAD geometry: OpenSCAD
  enclosure modelling or the KiCad schematic/PCB. Use it instead of
  `bead-worker` for that work.
- **`bead-worker`** (Sonnet, `isolation: worktree`): implements one claimed
  bead end to end and opens a PR.
- **`code-reviewer`** (Opus): reviews one PR — re-verifies every claimed
  fact (part numbers, datasheet specs, stock status, dimensions) before
  checking spec compliance and quality — and posts its verdict as a PR
  comment. Read-only.

Only run beads in parallel when they touch different files; otherwise run
them in sequence.

## Planning & Research Conventions

This project keeps durable knowledge in version-controlled markdown,
separate from the ephemeral beads board.

- `.planning/roadmap.md` — current status, next steps, live risks.
- `.planning/decisions/` — one ADR per file, `YYYY-MM-DD-short-title.md`,
  indexed in `INDEX.md`. Format: Context / Decision / Rationale /
  Alternatives / Consequences.
- `.research/findings/` — one research finding per file,
  `YYYY-MM-DD-topic.md`, indexed in `INDEX.md`. Keep research separate from
  the decisions it informs.
- Rule of thumb: **research** goes in `.research/`, **decisions** based on
  it go in `.planning/decisions/`, **status** in `roadmap.md`. Update the
  relevant `INDEX.md` whenever a file is added. Don't delete superseded
  entries — mark them Deprecated/Superseded.
- `docs/plans/` holds the original design docs this project started from —
  broader and less structured than an ADR; `.planning/decisions/` is where
  specific, hard-to-reverse choices get recorded going forward.

## No absolute local filesystem paths

This repo is published on GitHub. Never commit an absolute path from the
machine or sandbox a change was made in (`/home/...`, `/Users/...`,
`/tmp/...`) into any tracked file — README, docs, hooks, skills, `.codex`
config, anything. Hooks/scripts that need a path should discover it
(`git rev-parse --show-toplevel`, `$CLAUDE_PROJECT_DIR`, etc.), not hardcode
one. Before committing, `git grep -n "/home/\|/Users/\|/tmp/"` across what's
staged and fix anything that turns up.

## Orchestrator Autonomy

**Default to acting.** Decide without asking when: a decision has a
conventional right answer; a claim can be verified with a command; the work
is reversible (a branch, a doc, a bead). Say what you decided and why —
don't present a menu for routine calls.

**Ask** only when: the decision is a product-priority call that changes
what gets built; it's irreversible or outward-facing (a push, a force, a
history rewrite, publishing something, spending money); it needs a physical
action only the user can take (soldering, measuring a printed part,
plugging something in); or two readings of the request lead to materially
different work.

**Verify before you believe** — including your own claims. "DRC clean" is
not true unless DRC was actually run in KiCad by someone who has it
installed; "fits the enclosure" is not true unless the physical dimensions
were actually checked against the printed part.

## Reporting (terseness)

Default to short reports: what happened, what it means, what's next. Save
length for a decision the user has to make, a physical action only they can
take, or a correction to something they believe.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work atomically
bd close <id>         # Complete work
bd dolt push          # Push beads data to remote
```

## Non-Interactive Shell Commands

**ALWAYS use non-interactive flags** with file operations to avoid hanging on confirmation prompts.

Shell commands like `cp`, `mv`, and `rm` may be aliased to include `-i` (interactive) mode on some systems, causing the agent to hang indefinitely waiting for y/n input.

**Use these forms instead:**
```bash
# Force overwrite without prompting
cp -f source dest           # NOT: cp source dest
mv -f source dest           # NOT: mv source dest
rm -f file                  # NOT: rm file

# For recursive operations
rm -rf directory            # NOT: rm -r directory
cp -rf source dest          # NOT: cp -r source dest
```

**Other commands that may prompt:**
- `scp` - use `-o BatchMode=yes` for non-interactive
- `ssh` - use `-o BatchMode=yes` to fail instead of prompting
- `apt-get` - use `-y` flag
- `brew` - use `HOMEBREW_NO_AUTO_UPDATE=1` env var

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:1105d646 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/core-concepts/sync-concepts.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   bd dolt push
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->

<!-- BEGIN BEADS CODEX SETUP: generated by bd setup codex -->
## Beads Issue Tracker

Use Beads (`bd`) for durable task tracking in repositories that include it. Use the `beads` skill at `.agents/skills/beads/SKILL.md` (project install) or `~/.agents/skills/beads/SKILL.md` (global install) for Beads workflow guidance, then use the `bd` CLI for issue operations.

### Quick Reference

```bash
bd ready                # Find available work
bd show <id>            # View issue details
bd update <id> --claim  # Claim work
bd close <id>           # Complete work
bd prime                # Refresh Beads context
```

### Rules

- Use `bd` for all task tracking; do not create markdown TODO lists.
- Run `bd prime` when Beads context is missing or stale. Codex 0.129.0+ can load Beads context automatically through native hooks; use `/hooks` to inspect or toggle them.
- Keep persistent project memory in Beads via `bd remember`; do not create ad hoc memory files.

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/core-concepts/sync-concepts.md for details and anti-patterns.
<!-- END BEADS CODEX SETUP -->
