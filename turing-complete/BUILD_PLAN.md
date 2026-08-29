# Optional Turing Complete demonstrator

VANTA-1T does not require a connection to the game Turing Complete. The real
design work is expressed as equations, executable Python, and SystemVerilog.
The game is useful as a visual, educational implementation of a reduced
datapath, not as evidence for trillion-parameter capacity, HBM behavior,
timing, power, thermals, or model quality.

Angel's public experiment used Codex to make functional circuits in Turing
Complete and then pushed toward a full CPU and game workload:
https://x.com/Angaisb_/status/2091180927082692953

## Recommended in-game scope

Build a `VANTA-MINI` token pipeline with 8-bit activations, 16 tiny experts,
and top-2 routing. This preserves the interesting control and dataflow while
remaining debuggable in a game environment.

## Block order

1. `dot8_binary`
   - Inputs: eight signed 8-bit activations, eight sign bits, one 8-bit scale.
   - Operation: conditionally negate each activation from the sign bit, sum the
     eight values, then multiply by the fixed-point scale.
   - Test: all-positive signs returns the activation sum; flipping one sign
     subtracts twice that activation from the all-positive result.
2. `top2_router16`
   - Inputs: sixteen unsigned 8-bit scores.
   - Outputs: largest expert ID, second-largest expert ID, and their scores.
   - Tie rule: lower expert ID wins. Make this explicit so every test is stable.
3. `residual4`
   - Inputs: the binary result plus four signed 4-bit residual contributions.
   - Operation: sign-extend and accumulate the residuals into the coarse result.
4. `expert_lane`
   - Combine `dot8_binary` and `residual4` behind an enable signal.
   - Non-selected experts must hold their output at zero.
5. `token_pipeline`
   - Cycle 0: latch sixteen router scores.
   - Cycles 1-4: tournament-select top two experts.
   - Cycle 5: dispatch activation vectors.
   - Cycles 6-8: binary dot and residual correction.
   - Cycle 9: sum the two expert outputs and assert `valid`.

## Minimum test vectors

| Test | Expected behavior |
| --- | --- |
| All router scores zero | Experts 0 and 1 selected by tie rule |
| Score 15 highest, score 3 second | IDs 15 and 3 |
| Negative activation with positive sign | Signed arithmetic preserved |
| One expert disabled | Its lane contributes zero |
| Residual values all zero | Output equals scaled binary backbone |
| Back-to-back tokens | One output per pipeline interval after fill |

## What a successful demo proves

- The route-before-execute control path is logically coherent.
- The binary backbone and residual correction can be pipelined.
- The top-k tie rule and selected-expert gating are testable.

## What it does not prove

- That 1.325 effective bits preserves Kimi K2.5 quality.
- That custom HBM4 base-die logic is manufacturable.
- That the 650 W target, 701.5 token/s ceiling, or package layout is achievable.
- That the design is smaller than a current accelerator in physical area.

The most honest social use is to label this a "logic-scale VANTA-MINI demo"
and link it to the analytical paper rather than treating the game build as a
hardware benchmark.
