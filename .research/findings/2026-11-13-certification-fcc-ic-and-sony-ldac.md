# Certification notes: FCC/IC modular approval (ESP32-WROOM-32U) and Sony LDAC

## Question

If this project (or a commercial version of it) ever shipped assembled
units, what regulatory/licensing exposure exists beyond building it as a
one-off or as open-source-you-build-yourself?

## Findings: radio module modular certification

- ESP32-WROOM-32U carries its own modular certification (FCC Part 15C,
  Industry Canada/ISED) as a standalone module with its own FCC ID — this
  is the point of using a pre-certified module instead of a raw chip +
  custom antenna design.
- **Antenna is restricted, not open-ended.** The Industry Canada filing
  caps it at max 2.33 dBi gain at 2.4GHz. (A forum comment claiming "any
  antenna that fits is fine" contradicts the actual grant text — treat that
  as unreliable.) Swapping to a notably higher-gain antenna than what's
  certified would technically need its own testing/permissive change, even
  though the module itself is pre-certified. Staying with a similar-gain
  stub/whip/adhesive antenna keeps the board inside the existing grant.
- **Firmware:** modular grants cover RF/baseband behavior (TX power,
  frequency, modulation), which lives in Espressif's own closed radio
  firmware and calibration data, not the application code on top. Running
  their official "HCI-over-UART controller" firmware instead of Bluedroid
  shouldn't touch any of that — but nothing in the FCC filing explicitly
  states this specific firmware mode is covered, so this is an inference,
  not a documented guarantee.
- **The finished board** is a separate question from the radio module: as a
  "digital device" it would typically fall under FCC Part 15 Subpart B
  (unintentional radiator) if sold in the US, normally satisfied via a
  self-administered Supplier's Declaration of Conformity rather than lab
  certification — lighter weight, especially built from already-certified
  modules per their reference integration.

## Findings: Sony LDAC licensing

- **The firmware's `libldac` encoder is genuinely Apache-2.0**, released by
  Sony into AOSP — this is why building it from an open repo (as the
  firmware project already does) is fine.
- **But Sony's own `NOTICE` file in that same code explicitly requires a
  separate certification process to ship LDAC in "your products"**:
  inquiry → NDA → contract → provision of the licensed LDAC software →
  certification. This is layered on top of the Apache license, not
  something the Apache grant itself would normally impose — it's about
  Sony retaining control of the "LDAC" name and (likely) a patent
  cross-license outside the literal scope of what they open-sourced.
- Decoder-side (headphones receiving LDAC) has historically been fully
  proprietary/license-gated too — that's the headphone makers' problem, not
  this project's.

## Framing for this project

Both of the above are gates on *selling finished assembled units*
commercially, not on building/publishing an open-source,
build-it-yourself hardware design — which is what this repo already is,
same as the firmware repo it accompanies. Also worth noting: the firmware
repo's own license (PolyForm Noncommercial 1.0.0, copied into this repo's
`LICENSE.md`/`NOTICE`) already restricts commercial use on its own terms,
independently of either certification question above.

## Informs

`docs/plans/2026-11-13-custom-hardware-design.md` ("Out of scope / parked").
