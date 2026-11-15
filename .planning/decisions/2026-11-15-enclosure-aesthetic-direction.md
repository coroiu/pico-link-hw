# Enclosure aesthetic direction: minimalist, hidden fasteners, single color, flush controls

## Context

The enclosure design (`docs/plans/2026-11-13-custom-hardware-design.md`,
`.planning/roadmap.md`'s `pilink-8hx` epic) had no aesthetic direction
recorded — only function: two-shell, screwed with heat-set inserts, display
bezel cutout, button plungers, rear USB-C cutout, internal antenna mount.
Before any OpenSCAD modelling starts (including a possible first pass by a
different model, "Fable," per the user's suggestion), the look needs to be
settled so modelling work doesn't have to guess or get redone.

## Decision

- **Aesthetic:** minimalist tech gadget (Teenage-Engineering-adjacent) —
  flat-ish faces, deliberate but not aggressive corner radii, nothing that
  reads as "unstyled" or bolted-together. Explicitly not a bare-minimum
  "function only, skip the styling pass" approach.
- **Fasteners:** hidden. Heat-set inserts recessed/countersunk so screws
  don't show on an outward face.
- **Material/color:** single neutral color throughout both shells (e.g.
  matte black or similar) — no two-tone split between top and bottom.
- **Controls:** flush, low-profile buttons (A/B/X/Y) and encoder knob —
  subtle travel, reinforcing the flat/minimalist look over a chunky
  "obviously a gadget you grip" feel.

## Rationale

These were explicit user choices (asked directly, not inferred): minimalist
over retro-handheld or pure-utility, hidden fasteners over visible,
single-color over two-tone, flush controls over raised/tactile. Recorded
here so every enclosure bead (`pilink-8hx.*`) and any model/agent doing the
OpenSCAD work shares the same target without re-litigating it per bead.

## Alternatives considered

- **Retro handheld** (Game Boy-style, chunkier curves, two-tone) — rejected,
  user wants minimalist.
- **Pure utility** (smallest enclosure that fits, no styling pass) —
  explicitly rejected; the user distinguished this from "minimalist" when
  asked, wanting real design intent, not just absence of effort.
- **Visible fasteners** — simpler to design, reads more "tool-like," but
  rejected in favor of hidden inserts for the cleaner minimalist look.
- **Two-tone shells / raised tactile controls** — both considered and
  rejected in favor of the single-color, flush-control combination.

## Consequences

- **OpenSCAD work** (`pilink-8hx.1`-`.5`): wall thickness, corner radii,
  boss/insert placement, and button-plunger profile should all target this
  look — e.g. heat-set insert bosses need to sit in a blind/counterbored
  pocket rather than a through-hole visible from outside; button plungers
  need a shallow/flush cap profile rather than a tall mushroom cap.
- **Material choice for the actual print**: single-color filament, no
  dual-extrusion or multi-color plan needed — simplifies the print setup
  whenever a real print happens.
- **Does not yet unblock modelling**: this ADR fixes the *style*, not the
  *dimensions*. The actual shell/bezel/plunger geometry still needs real
  PCB layout data (see `pilink-8hx.2`'s dependency on `pilink-7el.9`,
  "Route PCB layout (requires KiCad GUI)") before hole positions and board
  envelope are known. A style-exploration pass (corner/edge treatment,
  fastener boss detail, a sample flush-button profile) could reasonably
  start before that, using placeholder dimensions, but the final fitted
  shells cannot.
