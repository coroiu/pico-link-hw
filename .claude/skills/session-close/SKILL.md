---
name: session-close
description: Close out a work session cleanly - tidy the workspace, commit and record what happened, write durable memory for the next session, and name the next task. Use when the user says session-close, "clean up and record everything", "wrap up", "I'm going to clear your context", or is otherwise ending a stretch of work. Runs on the main thread; do NOT dispatch it to a subagent.
---

# Session Close

Run this on the **main thread**. It is a handoff ritual: the next session starts
with an empty context and only what you wrote down. Assume the reader is a
competent stranger who was not here.

Work through all five steps. Report a short summary at the end — not a
narration of each step.

## 1. Tidy the workspace

```bash
git status --short
git worktree list
git branch --list "bd-*"
```

- **Commit any uncommitted work that is a real deliverable** (docs, ADRs,
  design files the session produced). Losing it to a context clear or a
  crash is the bigger risk than an untidy history. Leave alone:
  `.beads/*.jsonl` churn and anything the user owns.
- **Remove finished worktrees** with `git worktree remove <path>`. Check each
  is clean first. This keeps the branch — nothing is lost.
- **Check every `bd-*` branch has an upstream** (if a remote is configured):
  `git rev-parse --abbrev-ref @{u}`. A report of "pushed" is not evidence it
  pushed.
- **If a Dolt remote is configured for this repo's beads board**
  (`bd dolt remote list`), back it up with `bd dolt push` and verify it
  landed (`git ls-remote origin | grep dolt`). If none is configured yet,
  say so plainly rather than silently skipping it — it's a real gap, not a
  non-issue.
- Delete scratch files the session created.

## 2. Reconcile the beads board

- Close what is genuinely done, with a `--reason` that says why.
- Close what is **overtaken** — beads whose approach died even if their goal
  survives — and say where the goal went.
- Move banked evidence (measurements, verified facts, dead ends) **into the
  surviving bead's description**, not just a comment on a closed one.
- `bd list --json`, never bare `bd list` — it can silently truncate.

## 3. Write durable memory

Memory is for what the repo does **not** already record. Do not duplicate
file content, git history, or CLAUDE.md.

Write or update:
- **A handoff memory** naming where work stands, what is unblocked, and
  anything that must not be quietly undone.
- **Lessons** worth carrying: a wrong assumption that cost real time, a
  correction the user made, a sourcing gotcha. Include the *why*.
- Update any memory this session made **stale or wrong**.

Then add the one-line pointer to `MEMORY.md`.

## 4. Name the next task — required

Do not end without this. State explicitly:

- **The next bead ID**, and that it is unblocked.
- Why it is next, in one line.
- Anything the implementer must not re-derive, with a pointer to where the
  evidence lives.

If several things are ready, name **one** and say why it wins.

## 5. Report

Lead with workspace state and the next task. Then, briefly: what was
committed, what was closed, what was written to memory. Flag anything you
could **not** finish or that needs the user's decision.

## Rules

- **Do not push** without explicit authority. Report the branch and the exact
  command instead.
- **Never invent progress.** If a milestone was not reached, the handoff says
  so.
