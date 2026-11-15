# Rotary encoder replaces the whole d-pad, not just LEFT/RIGHT

## Context

`.planning/decisions/2026-11-15-rotary-encoder-for-volume.md` replaced only
the LEFT/RIGHT tact switches with a rotary encoder, keeping UP/DOWN as two
dedicated tact switches — based on the user's literal statement at the time
("I don't ever use left/right"). The resulting schematic (`pilink-cmn`,
merged) wired exactly that: UP/DOWN (SW301/SW302, GPIO20/21) unchanged,
LEFT/RIGHT replaced by the encoder.

On review, the user clarified their actual intent was broader: replace the
*entire* d-pad (UP/DOWN/LEFT/RIGHT) with the rotary encoder, not just
LEFT/RIGHT. UP/DOWN were never meant to survive as separate hardware.

## Decision

Remove the UP/DOWN tact switches and their pull-up resistors from
`hardware/input.kicad_sch`. The rotary encoder becomes the device's only
directional/analog control, serving double duty by firmware context:
rotate = volume in normal/playback use, rotate = menu up/down while a menu
is open; press = mute/toggle or select, depending on context. A/B/X/Y are
still unchanged.

This supersedes the "UP/DOWN unchanged" part of
`2026-11-15-rotary-encoder-for-volume.md` only — that ADR's reasoning for
replacing LEFT/RIGHT, and its alternatives-considered discussion, still
holds and is not re-litigated here.

## Rationale

- A single rotary control already has exactly the right shape (increment/
  decrement) for list/menu navigation — adding separate UP/DOWN buttons next
  to it is redundant hardware, not a safety net.
- A rotary knob doubling as both a volume control and a menu scroller,
  gated by firmware UI context, is a standard, well-understood pattern on
  small-screen embedded devices (e.g. iPod click-wheel-era volume/scroll
  knobs) — not a novel or risky UX bet.
- Removes 2 more tact switches, 2 pull-up resistors, and frees 2 more GPIO
  (GPIO20/21), simplifying the board further at essentially zero cost: the
  encoder hardware already exists on this sheet regardless.
- Same timing argument as both prior input ADRs: nothing is built on the
  enclosure side yet (`pilink-8hx.2`/`.3` still not started), so this is
  still the cheapest point to make the change.

## Alternatives considered

- **Keep UP/DOWN as dedicated switches for menu nav, encoder for volume
  only (the status quo from the prior ADR).** Simpler firmware (no
  context-dependent meaning for encoder rotation), but keeps hardware the
  user explicitly doesn't want. Rejected — this is the thing being
  corrected.
- **Repurpose UP/DOWN's freed GPIOs for a new function (e.g. a dedicated
  back/home button).** No such function has been identified yet. Not
  rejected outright, but not adopted here — the GPIOs simply return to the
  RP2350B sheet's generic free-pin pool until a concrete need exists.

## Consequences

- `hardware/input.kicad_sch` (merged via `pilink-cmn`) needs a second
  amendment: remove SW301, SW302, R301, R302, and their associated
  `#PWR` symbols; re-verify via `kicad-cli sch export netlist` on the root
  that nothing collides project-wide, same check as every prior schematic
  change on this project. Tracked as a new bead, not a reopening of the
  closed `pilink-cmn` bead.
- `hardware/README.md` input description changes from "7 inputs: UP/DOWN +
  A/B/X/Y + 1 rotary encoder" to "5 inputs: A/B/X/Y + 1 rotary encoder."
- Firmware (`../pico-link`, out of scope for this repo): needs a
  context-aware input layer where the encoder's rotation events mean
  "volume" or "menu navigation" depending on current UI state. The pin-remap
  bead `pilink-otf` already needs updating for the encoder's GPIO
  assignment (per the prior ADR) and now also drops
  `PL_INPUT_PIN_UP`/`PL_INPUT_PIN_DOWN` entirely, same as it already drops
  `PL_INPUT_PIN_LEFT`/`PL_INPUT_PIN_RIGHT`.
- Enclosure (`pilink-8hx.2`/`.3`, neither started): the UP/DOWN plunger
  holes go away entirely — final external input surface is 4 button
  plungers (A/B/X/Y) + 1 knob cutout, down from the original 8-switch
  layout.
