---
name: session-resume
description: Pick up work at the start of a session - load the handoff, verify it still matches reality, then dispatch the next task. Use when the user says session-resume, "let's continue", "where were we", "what's next", or opens a fresh context expecting work to carry on. The companion to session-close. Runs on the main thread; do NOT dispatch it to a subagent.
---

# Session Resume

The companion to `session-close`. That skill wrote a handoff for a competent
stranger; you are that stranger. Your job is to load it, **check it is still
true**, and then **get the next task moving**.

Work through all five steps in one turn. Keep steps 1-3 cheap: they are
orientation, not investigation.

## 1. Read the handoff first

Start with the memory index and the handoff memory it points to.

**Treat memory as dated, not authoritative.** If it names a file, a part
number, or a bead, verify that still exists/is still accurate before
recommending anything built on it.

## 2. Check the board against it

```bash
bd ready
bd list --json --status open     # never bare `bd list` — it can truncate silently
bd show <the bead the handoff names>
```

Confirm the named next bead still exists, is still open, and is still
unblocked. If the handoff and the board disagree, **the board wins** — say
so in your report.

Read that bead's comments before anything else.

## 3. Verify the workspace matches the story

```bash
git status --short
git log --oneline -5
git worktree list
```

Look for the gap between what the handoff claims and what is actually here.

Also skim the newest ADR in `.planning/decisions/`. When a decision has
changed recently, older docs and older beads describe a world that no
longer exists.

## 4. Decide the next action

Name **one** thing to do next and why, with the bead ID. Prefer what the
handoff named unless step 2 or 3 contradicted it.

Before acting, restate: what is already banked and must not be
re-investigated, with where it lives; any constraint that must not be
quietly undone.

## 5. Act, then report

**Default to acting.** Do not stop to ask "shall I start?" — if steps 1-4
produced a clear next action, create the bead if one is needed and start (or
dispatch) it in this same turn, then report.

Report after acting. Lead with: where things stand in two or three lines,
what you did and why, then anything that genuinely needs the user's
decision.

**Stop and ask instead** only when: the choice is a product-priority call
that changes what gets built; it is irreversible or outward-facing; it
needs a physical action only the user can take; or two readings of the
situation lead to materially different work.

If the user's own message arrived with a different priority than the
handoff assumed, **their message wins** — resume against that.

## Rules

- **Never invent progress.** Check the bead, do not infer from an
  optimistic-sounding summary.
- **Do not re-run design work already recorded in a bead or decision doc.**
- Keep orientation small.
