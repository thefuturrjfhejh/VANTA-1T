# VANTA-1T architecture specification

Version 0.1 - analytical concept

## 1. Scope

VANTA-1T targets autoregressive inference for sparse MoE language models. It is
not a training accelerator and it is not intended to accelerate arbitrary CUDA
workloads. The reference workload is the public Kimi K2.5 configuration.

## 2. Package organization

### Research target

- One accelerator package.
- Four logic chiplets on a silicon interconnect fabric.
- Four 48 GB HBM4 stacks: 192 GB total.
- At least 11.2 TB/s aggregate raw HBM bandwidth, using 2.8 TB/s per stack.
- 512 MB shared SRAM target, distributed across the logic chiplets.
- 650 W package target, pending thermal and physical-design validation.

### Production-capacity option

- Six 48 GB HBM4 stacks: 288 GB total.
- At least 16.8 TB/s aggregate raw HBM bandwidth.
- 780 W package target.
- Enough modeled headroom for the compressed weights plus eight 128K-context
  8-bit MLA KV caches, before allocator and runtime reservations.

## 3. Weight representation

The stretch profile uses three terms for routed-expert weights:

1. A one-bit sign backbone.
2. One 8-bit scale per group of 64 values (0.125 bit/weight).
3. A structured low-rank residual budget equivalent to 4% of the original
   parameters at 4-bit precision (0.16 bit/weight).

Packing and control metadata receive a 0.04 bit/weight allowance. The effective
routed-expert representation is therefore 1.325 bits/weight. Attention,
routing, embeddings, the shared expert, and the dense layer receive a separate
12 GB resident allowance and remain at higher precision.

This is a capacity hypothesis. It is not evidence of acceptable perplexity,
reasoning quality, vision quality, or routing stability.

## 4. Dataflow

### Prefill

1. Token blocks are mapped across four chiplets.
2. Attention and router logits execute on conventional vector/matrix tiles.
3. Top-k expert identifiers are multicast to the HBM sectors.
4. Binary backbones run beside the resident weights in the HBM logic base dies.
5. Residual factors stream into the chiplet SRAM and are applied while the next
   expert group is prefetched.

### Decode

1. A latency schedule pins the request, its hot MLA KV blocks, and its likely
   expert groups to one locality domain.
2. Binary backbone, residual correction, and attention are pipelined.
3. The network is used only when an expert or KV block misses its home domain.
4. The same compute tiles change scheduling mode rather than handing the request
   to a separate accelerator class.

## 5. Router and placement

- Physical expert placement is optimized from a traffic matrix, not expert ID.
- Experts with correlated activation are separated when that avoids HBM hot
  spots and co-located when it improves residual reuse.
- A small victim cache holds recently used residual factors.
- The compiler must retain a worst-case path for adversarial or distribution-
  shifted routing; average locality cannot be treated as guaranteed.

## 6. Memory accounting

For an MLA cache, the model uses:

`layers x tokens x sequences x (kv_lora_rank + qk_rope_head_dim) x bits / 8`

With 61 layers, rank 512, RoPE dimension 64, 128K tokens, and 8-bit cache values,
one sequence requires approximately 4.61 GB. This omits allocator fragmentation,
temporary activations, and runtime workspaces.

## 7. Performance model

The batch-1 decode ceiling is:

`usable_HBM_bandwidth / (active_weight_bytes + KV_read_bytes)`

The public model lists 32B active parameters. The default model uses 35% of raw
HBM bandwidth as the end-to-end service-efficiency factor. At 8K context, this
produces a 701.5 tok/s ceiling for the stretch profile. This is an analytical
scenario, not a forecast and not a benchmark.

## 8. Footprint claims

Three different meanings must remain separate:

- **Weight-memory footprint:** 68.1% below the MXFP4-style analytical baseline.
- **Accelerator package count:** one package versus four Rubin GPUs in NVIDIA's
  NVL4 configuration, a 75% count reduction. This is not an area comparison.
- **Physical silicon/package area:** unknown until a PDK-backed floorplan and
  package escape study exist.

Do not turn package count into a claim of 75% less rack volume. Cooling, power,
CPU memory, NICs, switches, and service redundancy remain system-level costs.

## 9. Required validation gates

1. Quantize a smaller open MoE proxy and measure quality versus MXFP4/INT4.
2. Train or distill the binary-residual representation on the full model.
3. Build a cycle-accurate tile and HBM-traffic simulator.
4. Compile the pedagogical RTL with a production HDL tool and add formal checks.
5. Perform PDK-backed synthesis, place-and-route, package escape, signal-
   integrity, thermal, yield, and cost studies.
6. Benchmark full request traces, not only matrix kernels.

Until gates 1-2 pass, the compression is a hypothesis. Until gates 3-5 pass,
the hardware is an architecture proposal.
