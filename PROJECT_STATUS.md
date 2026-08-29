# VANTA-1T v0.1 status

## Result

The stretch profile calculates a 180.06 GB resident weight image for the
public Kimi K2.5-class 1T/32B-active configuration. The stated MXFP4-style
baseline is 563.74 GB. The modeled reduction is 68.06 percent.

This exceeds the project's 50 percent resident weight-memory target. It does
not establish a smaller physical die or package.

## Verified in this artifact

- Six Python tests pass, including a stable-headline regression check.
- `results.json` and `CITATION.cff` parse successfully.
- Three publication figures and the launch card regenerate from checked-in code.
- Both visualization source and standalone HTML have valid JavaScript syntax.
- The interactive lab's initial state and primary token-run interaction were
  exercised with a minimal DOM harness.
- The PDF was text-checked, rendered page by page, and visually inspected.

## Not verified

- Binary-residual model quality.
- SystemVerilog compilation or synthesis; no HDL toolchain was available.
- Cycle-level traffic, NoC contention, or expert imbalance.
- Physical area, timing, power, thermals, signal integrity, yield, and cost.
- Any performance number on fabricated silicon.

## First next experiment

Implement the same sign-backbone plus structured 4-bit residual on a smaller
open MoE proxy. Produce a quality-versus-effective-bits curve against BF16,
INT4, and MXFP4. If the 1.325-bit point fails, record the failure and move up the
precision sweep rather than changing the public claim after the fact.
