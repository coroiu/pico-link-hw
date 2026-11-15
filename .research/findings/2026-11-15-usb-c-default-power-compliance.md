# USB-C default-power compliance for the ~0.65A worst-case peak draw (pilink-1sj)

## Question

`power.kicad_sch`'s own budget derivation (re-stated on `usb_c.kicad_sch`'s
F401 note) puts worst-case peak draw at ~0.6-0.65A (RP2350B tens of mA +
ESP32-WROOM-32U up to 500mA TX-burst peak + display/backlight ~50-100mA).
`usb_c.kicad_sch`'s J401 only has passive 5.1k Rd pulldowns on CC1/CC2 — no
PD sink controller, no BC1.2 detection. Is drawing 0.65A spec-compliant from
that connection, and can firmware ever legitimately know it's allowed to?

## Findings

- **The device's default-tier entitlement is 500mA, not 900mA**, regardless
  of host type. USB Type-C Rev 2.x's "Default USB Power" current tier is
  900mA only for USB 3.x-speed devices; a USB 2.0-only device (confirmed
  true here — `usb_c.kicad_sch`'s own on-sheet text: "USB 2.0 only --
  RP2350B has no USB3 PHY") gets the USB 2.0-legacy default: 100mA
  unconfigured / 500mA after a compliant descriptor-based enumeration
  requests it. A native Type-C host port and a legacy Type-C-to-A cable
  (which carries its own fixed Rp inside the captive cable, per spec,
  precisely so a Type-C sink sees a valid default-tier CC voltage through
  a legacy connection) both land on this same 500mA ceiling for a USB
  2.0-speed device — there's no path to the higher 1.5A/3A Type-C tiers
  without being a USB 3.x device, which this isn't.
- **0.65A exceeds that 500mA ceiling outright — this isn't close.** Drawing
  above what's been negotiated/advertised is a real spec violation even
  though many real-world host ports tolerate it in practice (most USB
  silicon doesn't enforce the budget it advertises).
- **Firmware has no way to even detect a higher tier if one existed**:
  CC1/CC2 are wired with *local* schematic labels only (`usb_c.kicad_sch:1464,1469`,
  confirmed via `grep` — not hierarchical/global labels), so the CC nets
  never leave this sheet. They terminate at J401's CC pins and the R401/R402
  pulldowns and go nowhere else — not to any RP2350B ADC-capable GPIO. Even
  setting aside the 500mA-ceiling finding above, there is currently no
  hardware path for firmware to read the CC voltage and determine what's
  actually been advertised (PD, or a higher Type-C current tier on a
  hypothetical future USB3 revision). This is a sensing gap, not just a
  budget question.
- BC1.2 (charger detection via D+/D- voltage) is a real path to more current
  on a port that supports it, but needs either a dedicated BC1.2 detect IC
  or firmware-driven D+/D- signaling support — neither exists here, and
  BC1.2 support is itself optional on the host side (can't be assumed).
- USB-PD is the other real path (explicit negotiation over CC via BMC
  signaling) but needs a PD sink controller chip and real CC
  transmit/receive hardware, a much bigger change than this bead's scope.

## Conclusion

The current hardware has a real headroom gap: ~0.65A peak vs. a hard 500mA
default-tier ceiling, with no sensing path to ever legitimately claim more.
This needs one of (not mutually exclusive):

1. **Reduce real-world peak under 500mA in firmware** — e.g. never let
   ESP32 TX-burst peak (500mA alone) coincide with max-brightness backlight
   and RP2350B's own draw; out of this repo's scope (firmware), but worth
   flagging there.
2. **Add CC voltage sensing in this design** — route one CC line (CC1 or
   CC2; Type-C allows sensing either) to a spare RP2350B ADC-capable GPIO,
   so firmware could at least detect a *real* PD/BC1.2 negotiation if one
   is added later. By itself this doesn't fix the 500mA ceiling (no PD/BC1.2
   hardware exists to negotiate anything higher yet) — it only makes a
   future fix possible without another schematic respin.
3. **Accept the risk and ship as-is** — document that this draws above its
   advertised default on most ports today (common in low-cost USB
   peripherals, tolerated by nearly all real silicon) and treat it as a
   known, accepted non-compliance rather than a blocking defect.

No hardware change is strictly required to keep moving — current PCB
layout/BOM work does not depend on this — but (2) is cheap only *before*
layout is routed (a GPIO assignment + one net), and expensive after. This
is a product-priority call (ship with a known spec gap vs. spend a GPIO
and a trace now vs. push a firmware-side throttling fix) that needs
Andreas's decision, not an agent's.

## Informs

`pilink-1sj` — this finding answers its question; the three options above
are the decision `pilink-1sj` should resolve to once Andreas picks one.
