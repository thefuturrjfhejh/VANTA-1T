# RTL status

These modules make the core idea inspectable:

- `topk_router.sv` selects a small top-k expert set.
- `binary_residual_mac.sv` evaluates a one-bit expert backbone and optional
  signed low-bit correction.

They are pedagogical RTL, not production IP. The current environment does not
include Verilator, Icarus Verilog, Yosys, or a commercial simulator, so the RTL
has not received an HDL compile or synthesis pass here. The executable Python
model and its tests are the currently verified portion of the project.
