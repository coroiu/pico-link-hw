# pico-link-hw

## Project Overview

Custom PCB and 3D-printed enclosure for [Pico Link](https://github.com/coroiu/pico-link),
a USB-to-Bluetooth LDAC audio dongle with a screen. This repo replaces the
project's two stacked off-the-shelf dev boards with one purpose-built board,
designed for JLCPCB fab + assembly, plus a printed enclosure.

**No firmware lives here.** That's the separate pico-link repo. This repo
only tracks the physical design: schematic, PCB, BOM, enclosure.

Full design rationale: [`docs/plans/2026-11-13-custom-hardware-design.md`](docs/plans/2026-11-13-custom-hardware-design.md).
Settled component/architecture decisions: `.planning/decisions/`.
Current status and next steps: `.planning/roadmap.md`.

## Hardware (target architecture — not yet built)

- **RP2350B** — USB Audio Class device, display/UI, app logic. Same flash
  (16MB QSPI NOR) and PSRAM (8MB QSPI) parts as the Pimoroni Pico Plus 2 W
  this replaces.
- **ESP32-WROOM-32U** — dedicated Bluetooth Classic coprocessor (U.FL
  antenna), running Espressif's HCI-over-UART controller firmware; BTstack
  on RP2350 stays the host. See
  `.planning/decisions/2026-11-13-esp32-bt-coprocessor-not-rm2.md` for why,
  instead of Raspberry Pi's RM2 module.
- **Display** — 1.9" ST7789V IPS, 320x170, SPI (up from the current 240x240
  panel).
- **Input** — 5-way joystick + 4 tact buttons, same logical layout as today.
- **USB-C** exits the rear of the enclosure.

## This repo has no build/test automation

There's no `cargo build`, no CI, no code to compile. "Quality gates" here
mean: DRC/ERC in KiCad and dimension/fit checks in OpenSCAD, done by a human
with those GUI tools — neither is installed in a bare agent environment, so
an agent writing schematic/PCB/enclosure files should say so plainly rather
than claiming something was verified that wasn't.

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
history rewrite, publishing something); it needs a physical action only the
user can take (soldering, measuring a printed part, plugging something in);
or two readings of the request lead to materially different work.

**Verify before you believe** — including your own claims. "DRC clean" is
not true unless DRC was actually run in KiCad by someone who has it
installed; "fits the enclosure" is not true unless the physical dimensions
were actually checked against the printed part.

## Reporting (terseness)

Default to short reports: what happened, what it means, what's next. Save
length for a decision the user has to make, a physical action only they can
take, or a correction to something they believe.

## Team (roles, when work is delegated to subagents)

Most work on this repo — reading a datasheet, writing a design doc, editing
a KiCad/OpenSCAD file — doesn't need a specialized persona; just do it. The
roles below exist for when a task genuinely benefits from a narrower,
report-only advisory pass before changing files:

| Role | Agent | What they own |
|------|-------|----------------|
| Architect | `architect` | System-level design/implementation planning (component choices, interfaces between hardware and firmware) — report-only, doesn't implement. |
| Scout | `scout` | Fast file/code discovery across the repo. |
| Scribe | `scribe` | Documentation, READMEs, keeping docs in sync. |
| Task manager | `task-manager` | Audits the beads board for status hygiene — report-only. |
| Code reviewer | `code-reviewer` | Adversarial review before anything gets merged. |
| Detective | `detective` | Root-cause analysis for something that's wrong (a bad footprint, a dimension mismatch) — report-only. |
| Merge supervisor | `merge-supervisor` | Git merge conflict resolution. |
| Discovery | `discovery` | Bootstraps a new specialist supervisor agent if this repo ever needs one for a new area of work. |

Advisory agents (architect, task-manager, detective) are report-only — they
write their findings to `.planning/design/` or `.planning/decisions/` and to
bead comments, not directly to `hardware/` or `enclosure/`.

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
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->

