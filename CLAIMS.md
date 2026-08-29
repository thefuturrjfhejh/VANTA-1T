# Public claim ledger

Use this page before writing about VANTA-1T. It separates executable arithmetic from hypotheses and measurements that do not yet exist.

## Safe claims

- The executable model calculates a 180.06 GB resident weight image for the VANTA stretch profile.
- The stated MXFP4-style analytical baseline is 563.74 GB.
- The calculated reduction is 68.06%.
- Four assumed 48 GB HBM4 stacks provide 192 GB of raw capacity.
- The 8K, one-sequence scenario leaves 11.66 GB before runtime reservations.
- The 701.5 tok/s result is a first-order bandwidth ceiling under a 35% service-efficiency assumption.

## Claims that are not supported

- “VANTA is 68% physically smaller than Rubin or Jalapeño.”
- “VANTA is faster or more efficient than Rubin or Jalapeño.”
- “VANTA runs Kimi K2.5 at production quality.”
- “The package fits within a particular reticle, interposer, rack, or thermal envelope.”
- “The RTL is tapeout-ready, synthesizable at a target clock, or formally verified.”
- “The design is novel or patentable.”

## Evidence labels

| Label | Meaning in this project |
| --- | --- |
| Measured | Observed on real hardware or a real trained model. None yet. |
| Calculated | Direct output of the published equations and assumptions. |
| Estimated | A scenario or engineering target without physical validation. |
| Unvalidated | A required property for which no experiment currently exists. |

## Recommended one-sentence description

> VANTA-1T is an open analytical accelerator study proposing a single-package capacity path for a 1T-total / 32B-active MoE, with a calculated 68.1% smaller resident weight image than its stated MXFP4-style baseline, contingent on an unvalidated binary-residual quality hypothesis.
