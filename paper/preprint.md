# VANTA-1T: An Analytical Single-Package Inference Architecture for Trillion-Parameter Mixture-of-Experts Models

Mahee Monjur  
Independent Researcher  
Version 0.1 - 26 August 2026

## Abstract

This paper presents VANTA-1T, an inference-only accelerator concept for a
one-trillion-parameter sparse mixture-of-experts (MoE) language model with
approximately 32 billion parameters active per token. The objective is not to
claim fabricated hardware, but to test whether a trillion-parameter model can
be made resident in a single accelerator package while reducing its resident
weight image by more than 50 percent relative to a transparent MXFP4-style
baseline. VANTA-1T represents routed-expert matrices as a one-bit sign
backbone, group scales, and a structured 4-bit low-rank residual. Higher-risk
operations - attention, routing, embeddings, the shared expert, and the dense
layer - remain at higher precision. A custom HBM4 base die executes binary
dot-products near the weights; four logic chiplets apply residual corrections,
attention, routing, and scheduling. For the public Kimi K2.5 configuration,
the resulting analytical resident weight image is 180.1 GB, compared with
563.7 GB for the modeled MXFP4 baseline, a 68.1 percent reduction. Four 48 GB
HBM4 stacks provide 192 GB, leaving 11.7 GB after an 8K-context single-user
8-bit MLA KV cache. A first-order bandwidth model gives a 701.5 token/s
batch-1 decode ceiling at 8K context under an explicitly assumed 35 percent
service-efficiency factor. These are calculated capacities and ceilings, not
silicon measurements. The central gating experiment is whether the
binary-residual representation preserves model quality. Physical area,
timing, thermals, yield, cost, and end-to-end throughput remain unvalidated.

## 1. Scope and research question

Large sparse MoE models create a useful asymmetry: only a small fraction of
the weights participate in each token, yet the full expert population normally
remains resident somewhere in the serving system. The public Kimi K2.5 model
is a concrete example: Moonshot AI reports one trillion total parameters and
32 billion active parameters, with 384 routed experts and eight selected
experts per token. This makes capacity a system-level problem even when
per-token arithmetic is much smaller than the total model.

VANTA-1T asks a narrow engineering question:

> Under an aggressive but explicit weight representation, can the complete
> expert population of a 1T/32B-active MoE fit in one accelerator package, and
> can the resident weight image be at least 50 percent smaller than an
> MXFP4-style representation?

The paper answers only the analytical capacity question. It does not claim a
new trained model, tapeout-ready RTL, a manufacturing process, or measured
performance. The intended contribution is an auditable architecture target,
an executable first-order model, and a falsifiable validation plan.

## 2. Reference workload and public hardware facts

The workload parameters are taken from the public Kimi K2.5 configuration:
61 transformer layers, one dense layer, 384 routed experts, eight selected
experts, hidden width 7168, routed-expert intermediate width 2048, MLA latent
rank 512, and maximum context 262,144 tokens. Treating each routed SwiGLU
expert as gate, up, and down matrices gives:

P_routed = 60 x 384 x 3 x 7168 x 2048 = 1.014686 x 10^12 weights.

This derived routed-expert count is close to the published one-trillion total
parameter description. The small mismatch is expected because the public
total is rounded and the architecture contains non-expert parameters.

For the memory envelope, the research target uses four 48 GB HBM4 stacks and
2.8 TB/s per stack. These values follow Micron's public 48 GB 16-high sample
and greater-than-2.8-TB/s product statements; the analysis deliberately avoids
using a faster peak claim. For context, NVIDIA's preliminary Rubin data lists
288 GB HBM4 and 22 TB/s per Rubin GPU, and four Rubin GPUs in the NVL4 module.
Those public figures are references, not measured VANTA baselines.

OpenAI's Jalapeno report motivates three system principles used here: keep
model state and KV state close to compute, treat the network as part of the
accelerator, and activate resources differently for compute-heavy prefill and
bandwidth-heavy decode. VANTA-1T independently instantiates those principles
around an explicit binary-residual expert representation.

## 3. Architecture

### 3.1 Package organization

The research configuration contains one accelerator package, four compute
chiplets, four custom 48 GB HBM4 stacks, a silicon interconnect fabric, and a
target of 512 MB distributed SRAM. The raw capacity is 192 GB and the raw HBM
bandwidth is at least 11.2 TB/s under the conservative per-stack assumption.
The power target is 650 W, but no thermal proof is claimed.

A production-capacity option expands to six 48 GB stacks, 288 GB capacity,
16.8 TB/s raw bandwidth, and a 780 W package target. This option is intended
for practical concurrency and runtime reserve, not to improve the headline
weight-compression ratio.

### 3.2 Split execution path

Each routed expert is decomposed into two computational paths:

1. Binary backbone. The sign bit of each expert weight remains adjacent to the
   weight's HBM channel. XNOR/popcount-like dot-product lanes on a custom base
   die form a coarse expert output.
2. Residual correction. Structured low-rank residual factors, stored at 4-bit
   precision, are prefetched into chiplet SRAM and applied on conventional
   vector/matrix tiles.

The attention blocks, router, embeddings, shared expert, and dense layer stay
at higher precision inside a separate 12 GB resident allowance. This prevents
the most routing- and activation-sensitive operations from being forced into
the binary path.

The base-die computation is a research proposal. It may require a custom HBM
logic die or a tightly coupled memory-side companion die and should not be
interpreted as a feature of commodity HBM4.

### 3.3 Route before movement

The router produces top-k expert identifiers before expert data movement. A
compiler places experts from an observed traffic matrix rather than from
numeric expert IDs. The objective is to minimize cross-domain traffic while
avoiding HBM-channel hot spots. Recently used residual factors occupy a small
victim cache. A worst-case network path remains mandatory because average
locality can fail under adversarial prompts or distribution shift.

### 3.4 Prefill and decode

During prefill, token blocks are spread over the four compute chiplets.
Attention and router logits execute on matrix/vector tiles; expert IDs are
multicast to the appropriate memory sectors; binary backbones run beside the
resident weights; and residual corrections overlap with the next expert
prefetch.

During decode, a latency-oriented scheduler pins a request, its hot MLA KV
blocks, and its likely experts to one locality domain. Binary backbone,
residual correction, and attention are pipelined. The same physical tiles
change scheduling mode between prefill and decode instead of requiring two
separate accelerator classes.

## 4. Weight representation

The stretch profile assigns the routed experts:

| Term | Effective bits per routed weight |
| --- | ---: |
| One-bit sign backbone | 1.000 |
| One 8-bit scale per 64 values | 0.125 |
| 4-bit residual over 4 percent equivalent parameters | 0.160 |
| Packing and control metadata allowance | 0.040 |
| Total | 1.325 |

The 4 percent residual budget is an architecture allocation, not evidence that
4 percent is sufficient. It can be implemented by low-rank factors, sparse
outliers, or a hybrid chosen per expert. An expert-sensitive compiler may
assign different residual ranks while preserving the global budget.

The MXFP4-style comparison uses 4.0 payload bits, one 8-bit scale per 32
weights (0.25 bit/weight), and a 0.10 bit/weight metadata allowance, for 4.35
effective bits. Both representations add the same 12 GB non-expert allowance.
This makes the comparison reproducible, but it is not a claim about the exact
in-memory layout of every deployed MXFP4 implementation.

## 5. Analytical model

### 5.1 Resident weights

For routed parameter count P, effective expert precision b, and non-expert
allowance M_other:

M_weights = P b / 8 + M_other.

Using P = 1.014686 x 10^12 and M_other = 12 GB gives 563.736 GB for 4.35 bits
and 180.057 GB for 1.325 bits.

### 5.2 KV cache

The simplified 8-bit MLA cache model stores the latent vector and RoPE
component per layer, token, and sequence:

M_KV = L T S (r_KV + d_RoPE) b_KV / 8.

For 61 layers, rank 512, RoPE dimension 64, 128K tokens, and one sequence, the
cache is 4.605 GB. The model excludes allocator fragmentation, temporary
activations, prefix metadata, and runtime workspaces.

### 5.3 Decode ceiling

The single-stream bandwidth ceiling is:

tokens/s <= eta B_raw / (M_active_weights_per_token + M_KV_read_per_token),

where eta is the end-to-end service-efficiency assumption. The default eta is
0.35. It absorbs protocol overhead, imbalance, bubbles, non-HBM operations,
and imperfect overlap. It is a scenario parameter, not a measurement.

## 6. Results

### 6.1 Memory footprint

| Representation | Effective expert bits | Resident weights | Change vs MXFP4 |
| --- | ---: | ---: | ---: |
| FP8 reference | 8.00 | 1,026.7 GB | +82.1 percent |
| MXFP4-style baseline | 4.35 | 563.7 GB | baseline |
| VANTA balanced | 2.325 | 306.9 GB | -45.6 percent |
| VANTA stretch | 1.325 | 180.1 GB | -68.1 percent |

The balanced profile does not meet the 50 percent target. The binary-residual
stretch profile exceeds it by 18.1 percentage points. The conclusion is
capacity-plausible only if its quality hypothesis survives evaluation.

### 6.2 Representative serving cases

| Configuration | Weight GB | KV GB | Total GB | Capacity GB | Headroom GB | Single-stream ceiling (a) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 stacks, 8K, 1 user | 180.057 | 0.288 | 180.345 | 192 | 11.655 | 701.5 tok/s |
| 4 stacks, 128K, 1 user | 180.057 | 4.605 | 184.663 | 192 | 7.337 | 395.7 tok/s |
| 6 stacks, 128K, 8 users | 180.057 | 36.843 | 216.900 | 288 | 71.100 | 593.6 tok/s |

The four-stack target demonstrates residency but leaves little operational
margin. The six-stack option is the more credible serving system. The decode
figures are bandwidth ceilings under the 35 percent assumption and should not
be presented as benchmark results.

(a) The eight-user row still reports the one-stream equation at that context and
bandwidth. The first-order model does not predict per-user or aggregate
throughput under batching, expert reuse, or bandwidth sharing.

### 6.3 Footprint claim boundary

The result supports one strong, narrow claim: the analytical resident weight
image is 68.1 percent smaller than the stated MXFP4-style baseline. It does not
show 68.1 percent smaller silicon or rack area.

As a secondary count comparison, VANTA uses one accelerator package while
NVIDIA describes four Rubin GPUs in NVL4, a 75 percent reduction in accelerator
package count. This is not an area, power, cost, or performance comparison.
One Rubin GPU also has enough published capacity to hold the VANTA weight
image, so the package-count comparison should never replace the primary memory
representation result.

## 7. Validation plan

The following gates turn the proposal into an engineering result:

1. Quality gate. Quantize a smaller open MoE proxy with the same binary plus
   residual method. Compare perplexity, task accuracy, reasoning, routing
   stability, and vision quality against BF16, INT4, and MXFP4.
2. Scaling gate. Fit residual-rank allocation and distillation on a larger MoE.
   Report the Pareto curve of quality versus effective bits, including failed
   runs.
3. Traffic gate. Implement a cycle-accurate simulator with token traces,
   expert imbalance, HBM channels, SRAM banks, NoC contention, and prefill/
   decode transitions.
4. RTL gate. Compile and formally check the router and binary-residual datapath.
   The included RTL is pedagogical and has not yet passed a production HDL
   toolchain.
5. Physical gate. Use a real PDK for synthesis, place-and-route, package escape,
   signal integrity, power delivery, thermals, yield, and cost.
6. System gate. Measure end-to-end request traces with batching, speculative
   decoding, prefix reuse, failures, and service-level objectives.

Failure of Gate 1 falsifies the 1.325-bit profile, but not the framework: the
executable model exposes precision as a parameter so a higher-quality point
can be substituted. The balanced 2.325-bit point, for example, reduces memory
by 45.6 percent and therefore misses the project's stated stretch target.

## 8. Related work and position

Recent work makes clear that the components of VANTA-1T have active research
precedent. Expert-wise mixed precision uses router-derived sensitivity to
allocate quantization precision. MoBiE studies binarization of MoE models and
uses low-rank structure and routing-stability objectives. Expert Streaming
examines on-chip expert streaming across chiplets, while Sieve studies dynamic
GPU and HBM-PIM scheduling. Work on phase-disaggregated inference argues that
prefill and decode benefit from different precision and datapath choices, and
ELDR reports structured expert reuse.

VANTA-1T is therefore positioned as an open architectural synthesis and a
specific trillion-parameter capacity target, not as a claim that binarization,
low-rank residuals, near-memory compute, or phase-aware scheduling were
individually invented here. Its useful novelty, if validated, would be the
co-designed combination and its demonstrated quality-capacity-performance
operating point.

## 9. Threats to validity

- Quantization quality is entirely unmeasured on Kimi K2.5.
- A one-trillion-weight training or distillation run may be economically
  inaccessible to an independent project.
- The non-expert 12 GB allowance is a coarse estimate and may be too small.
- Four HBM stacks leave insufficient reserve for a robust runtime.
- The 35 percent service efficiency can overstate or understate real systems.
- Expert imbalance and network contention are not represented in the simple
  bandwidth equation.
- Custom logic under HBM changes thermals, yield, verification, and supplier
  constraints.
- No PDK-backed physical area exists, so the user's original physical-space
  ambition remains unproven.

## 10. Claim ledger

| Claim | Status | Required evidence |
| --- | --- | --- |
| 68.1 percent smaller resident weight image than modeled MXFP4 | Calculated | Public config plus executable equations |
| Fits 4 x 48 GB HBM at 8K, one user | Calculated | Capacity model; runtime reserve omitted |
| 701.5 token/s at 8K | Modeled ceiling | Cycle simulator and silicon benchmark |
| Preserves useful model quality | Unvalidated | QAT/distillation and evaluation suite |
| 650 W package | Target | Power and thermal implementation |
| More than 50 percent smaller physical package | Unknown | PDK floorplan and package study |
| Cheaper than current accelerators | Unknown | Yield, packaging, memory, and system BOM |

## 11. Conclusion

VANTA-1T provides a falsifiable path to resident single-package inference for a
1T/32B-active MoE. Its stretch representation reduces the calculated resident
weight image from 563.7 GB to 180.1 GB, exceeding the 50 percent memory target
with a 68.1 percent reduction. Four 48 GB stacks are sufficient only as a tight
research configuration; six stacks are the practical capacity option. The
design's most important next step is not a louder hardware claim but a quality
experiment. If a binary backbone plus a 4 percent 4-bit residual budget cannot
preserve useful model behavior, the headline point fails. If it does, the
combination of route-before-movement, near-memory binary compute, and
phase-aware chiplet scheduling becomes a serious candidate for deeper
cycle-level and physical design.

## References

1. Moonshot AI. Kimi K2.5 model card and configuration. 2026.
   https://github.com/MoonshotAI/Kimi-K2.5
2. OpenAI. Jalapeno: First results. 2026.
   https://openai.com/index/jalapeno-first-results/
3. NVIDIA. Vera Rubin NVL72 platform specifications. 2026.
   https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/
4. Micron. HBM4 product page. 2026.
   https://www.micron.com/products/memory/hbm/hbm4
5. Samsung Semiconductor. HBM4 product page. 2026.
   https://semiconductor.samsung.com/dram/hbm/hbm4/
6. Efficient Quantization of Mixture-of-Experts Models. arXiv:2604.06515, 2026.
   https://arxiv.org/abs/2604.06515
7. Expert Streaming: Multi-Chiplet MoE Inference. arXiv:2603.27624, 2026.
   https://arxiv.org/abs/2603.27624
8. Sieve: Dynamic GPU and HBM-PIM Scheduling for MoE Inference.
   arXiv:2605.11277, 2026. https://arxiv.org/abs/2605.11277
9. MoBiE: Mixture-of-Experts Binarization. arXiv:2604.06798, 2026.
   https://arxiv.org/abs/2604.06798
10. HBM Is Not All You Need: Efficient Disaggregated LLM Serving across
    Memory-heterogeneous Accelerators.
    arXiv:2606.29986, 2026. https://arxiv.org/abs/2606.29986
11. ELDR: Expert-Locality-Aware Decode Routing for PD-Disaggregated MoE
    Serving. arXiv:2607.00466, 2026.
    https://arxiv.org/abs/2607.00466

## Authorship and AI assistance

Mahee Monjur is the author and accepts responsibility for all claims. OpenAI
models assisted with source discovery, architecture exploration, analytical
modeling, implementation, checking, visualization, and drafting. AI systems
are not authors.

## Artifact availability

The accompanying artifact contains the executable Python model, generated JSON
and CSV outputs, tests, reproducible figures, pedagogical SystemVerilog blocks,
the interactive HTML architecture lab, and the publication materials. Code is
released under the MIT license; the paper and figures are released under CC BY
4.0.
