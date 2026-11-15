# Replace LEFT/RIGHT d-pad switches with a rotary encoder for volume

## Context

`.planning/decisions/2026-11-14-dpad-instead-of-joystick.md` settled on a
4-switch cross (UP/DOWN/LEFT/RIGHT) plus 4 face buttons (A/B/X/Y), and the
resulting schematic (`pilink-7el.6`, merged) wired exactly that: 8 discrete
tact switches, GPIO20-27.

Using the current prototype day to day, the user reports never using
LEFT/RIGHT. Pico Link is a USB-to-Bluetooth LDAC audio dongle — volume is
the single most frequently needed control on a device like this, and a
button-driven volume adjustment (hold/repeat on a tact switch) is worse
ergonomics than a dedicated rotary control.

## Decision

Replace the LEFT/RIGHT tact switches with a single rotary encoder
(EC11-class incremental quadrature encoder with integrated pushbutton),
dedicated to volume: rotate to adjust volume, press to mute/toggle. UP/DOWN
and A/B/X/Y are unchanged.

## Rationale

- User-reported usage data from the existing prototype: LEFT/RIGHT go
  unused. Removing them loses nothing in practice.
- Volume is the dominant interaction on an audio dongle. A knob gives
  immediate, analog-feeling control without entering a menu; a push-encoder
  adds mute/select for free via its integrated switch.
- Electrically cheap: an EC11-class encoder needs 3 GPIO (quadrature A/B +
  push) against the 2 GPIO freed by removing two tact switches — a net +1
  GPIO, trivial against RP2350B's available pins.
- Nothing is built yet on the enclosure side (`pilink-8hx.2`/`.3`, button
  plunger holes and plunger geometry, are not started) — this is the
  cheapest point in the project to make a mechanical input change, same
  reasoning as the d-pad decision itself.

## Alternatives considered

- **Keep LEFT/RIGHT as discrete buttons, add a separate volume knob
  elsewhere.** Adds a 9th/10th input and more enclosure area instead of
  reusing space already allocated to unused buttons. Rejected — no reason
  to keep inputs the user doesn't use.
- **Software-only volume via A/B/X/Y + a mode button.** Avoids hardware
  change entirely, but reintroduces the exact "hold a button to ramp
  volume" ergonomics problem a knob solves directly. Rejected.
- **Non-push encoder (rotation only, no integrated switch).** Saves one
  GPIO (2 instead of 3) but loses the free mute/select action. Rejected —
  push-encoders are commodity parts, the extra GPIO costs nothing here.

## Consequences

- `hardware/input.kicad_sch` (already merged, `pilink-7el.6`) needs
  amending: remove the LEFT/RIGHT switches + their pull resistors, add one
  rotary encoder footprint/symbol with 3 new net connections (quadrature
  A/B + push), reusing or reassigning GPIO as needed. Tracked as a new
  bead, not a reopening of the closed `pilink-7el.6` bead.
- Firmware (`../pico-link`, out of scope for this repo): `input.h`'s
  `PL_INPUT_PIN_LEFT`/`PL_INPUT_PIN_RIGHT` go away; a new quadrature-decode
  + push-button read path for the encoder is firmware work, tracked
  separately (not yet filed — the pin-remap bead `pilink-otf` already
  covers the broader GPIO-number mismatch and should be updated or
  superseded once the encoder's actual GPIO assignment is known).
- Enclosure (`pilink-8hx.2` top-shell bezel/holes, `pilink-8hx.3` button
  plungers — neither started yet): the two LEFT/RIGHT plunger holes become
  one round knob cutout with its own mechanical mounting approach (a panel-
  mount encoder, not a plunger) — affects those beads' scope before any
  work has been sunk into the old layout.
