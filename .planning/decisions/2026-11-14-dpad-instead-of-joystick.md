# D-pad instead of a 5-way joystick switch

## Context

The original design (`docs/plans/2026-11-13-custom-hardware-design.md`)
kept the Waveshare board's input layout as-is: a single 5-way joystick
switch (UP/DOWN/LEFT/RIGHT/PRESS in one mechanical part) plus 4 discrete
tact buttons (A/B/X/Y). The user prefers a d-pad-style cross of discrete
direction buttons over the joystick's tilting-nub feel.

## Decision

Replace the 5-way joystick switch with 4 discrete tact switches arranged
in a cross (UP/DOWN/LEFT/RIGHT), each with its own individually-printed
button plunger/cap — same mechanical approach already used for A/B/X/Y,
not a single unified rocker cap. No center-press switch; PRESS is dropped
as a dedicated physical input.

## Rationale

- User preference: d-pad feel over a joystick switch.
- Individual plungers per switch (vs. a single pivoting rocker cross) keeps
  the d-pad consistent with how every other button on this board is
  designed — simpler to print reliably with FDM tolerances, no pivot
  geometry to tune.

## Alternatives considered

- **4 direction switches + a 5th center-press switch**, preserving the
  current functional set (UP/DOWN/LEFT/RIGHT/PRESS) with zero firmware
  remapping needed. Rejected by the user in favor of the simpler 4-switch
  layout.
- **Single pivoting rocker cap over 4 switches** (classic SNES-style
  d-pad). Mechanically nicer feel but a harder printable part (needs a
  center pivot post and even actuation on all 4 sides); not worth the
  print-tuning risk over individual plungers.

## Consequences

- One fewer physical switch and GPIO than the original design (4 instead
  of 5 for directional input).
- **Firmware must remap PRESS/select** onto one of the existing A/B/X/Y
  buttons — there's no dedicated center-press input anymore. Firmware
  territory, tracked separately; does not block the hardware design.
- Affects `pilink-7el.6` (input subsystem schematic) and `pilink-8hx.2`/
  `pilink-8hx.3` (enclosure button holes and plunger design) — updated to
  reflect the 4-switch cross layout.
