---
name: auto-run
description: Work autonomously until the board is empty - stop asking Andreas what to do next. Use when the user says auto-run, "keep going", "don't ask me", "work until you're done", or when auto-recovery wakes the session after a limit reset.
---

# auto-run

Andreas has turned this on deliberately. It is standing authorization: **work
until there is no more work.** Do not end a turn by asking which task to pick,
whether to proceed, or whether he wants you to continue. Pick, proceed, continue.

## The loop

1. `bd ready` — take the highest-priority unblocked bead. Ties: prefer the one
   that unblocks the most other work.
   - If beads are in progress (`bd list --status=in_progress`), resume those
     first.
2. Investigate before delegating (read the actual file/datasheet/decision doc,
   per CLAUDE.md), log `bd comments add {ID} "INVESTIGATION: ..."`.
3. Do the work directly, or dispatch the right agent. Verify claims yourself —
   check the source (datasheet, listing, computed dimension) rather than
   trusting a report.
4. Close the bead once the work is actually done and verified.
5. Go to 1. Do not stop to report between iterations beyond 1-5 terse lines.

When `bd ready` is empty and nothing is in progress: say so in one line, name
what you would do next, and stop. That is the only clean exit.

## What still stops you

Stop and ask **only** when:

- **Andreas must physically act** — solder something, check a printed part
  fits, measure a dimension on real hardware, make a product-priority call.
- **The decision is a product-priority call** that changes what gets built.
- **The action is irreversible or outward-facing** — a force-push, a history
  rewrite, publishing anything, deleting a remote.
- **Two readings of the request lead to materially different work** and you
  cannot pick one from the roadmap.

When you do stop, batch it: state everything blocked, what you need, and your
recommendation, in one message. Then keep working on anything not blocked by it.

## What is NOT a reason to stop

- "Which of these should I do first?" — pick the one that unblocks more.
- "Do you want me to fix this too?" — if it is in the bead's scope, fix it.
- "This took a while, should I continue?" — yes.
- A wrong assumption, a bad source, something that needs re-checking — that
  is work, not a blocker. Fix it or file a bead and move on.

## Reporting while auto-running: CAVEMAN

Nobody reads this. Spend no tokens on it. **Talk like a caveman.**

- **Max one line per unit of work.** Fragments, not sentences. Drop articles,
  pronouns, filler verbs.
- **Facts and numbers only.** Bead ID, verdict, next bead. Nothing else.
- **Zero explanation.** No why, no how, no trade-offs, no caveats.
- **No preamble, no recap, no closing offer.**
- **Failures get one line too:** what broke + what you did.

Full prose is allowed in exactly three cases, and only for the part that needs
it: a blocker needing Andreas (state it + recommendation), a correction to
something he believes, raw error/verification output. Everything else: caveman.
