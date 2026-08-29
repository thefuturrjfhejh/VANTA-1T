# Contributing

VANTA-1T benefits most from attempts to falsify it.

Useful contributions include:

- reproducing the analytical outputs from a clean checkout;
- testing the binary-plus-residual representation on an open MoE proxy;
- replacing first-order bandwidth math with cycle-level traffic simulation;
- compiling, linting, or formally checking the pedagogical RTL;
- challenging package, HBM, power, or thermal assumptions with sourced data;
- correcting a claim that crosses the boundary in `CLAIMS.md`.

Before opening a pull request:

```bash
python3 -m pip install -r requirements.txt
make verify
```

Please include the command, input data, hardware or simulator version, and full output needed to reproduce a measured result. Failed experiments are welcome when documented clearly.
