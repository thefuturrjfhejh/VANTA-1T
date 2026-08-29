# VANTA-1T launch kit

## Recommended release order

1. Publish the repository with a tagged `v0.1` release.
2. Upload that exact release archive and the preprint PDF to Zenodo. Reserve a
   DOI before publishing so the DOI can be added to the repository metadata.
3. Put the interactive HTML lab on a static host (GitHub Pages is sufficient).
4. Post the single X launch post with a 10-15 second screen recording of the
   lab. Add the technical details as replies over the next few minutes.
5. Share the DOI and demo in focused hardware/ML communities. Ask for failure
   analysis, not generic promotion.
6. Treat arXiv as the next milestone after the first quality experiment and an
   independent analytical reproduction. Submit to the category that actually
   matches the revised paper; `cs.AR` is the likely primary category for the
   architecture version.

TechRxiv currently says submissions are temporarily closed. Zenodo is the
cleanest immediate route to a citable DOI; OSF Preprints is a reasonable
secondary mirror. Neither should be described as peer review.

## Main X post

I tried to answer an aggressive hardware question:

Can a 1-trillion-parameter MoE fit in one accelerator package with more than
50% less resident weight memory?

My open VANTA-1T design study reaches **180.1 GB vs 563.7 GB** for a transparent
MXFP4-style baseline: **68.1% less**.

No fabricated chip. No fake benchmark. The compression quality is still the
main experiment to break.

Preprint + model + interactive lab: [PROJECT LINK]

Attach `launch/vanta-1t-social.png` to the main post. Use the graph images only in replies so the first post remains legible on a phone.

## X thread replies

### Reply 1 - what changed

The core idea is a 1-bit routed-expert backbone plus group scales and a small
structured 4-bit residual budget. Attention, routing, embeddings, the shared
expert, and the dense layer stay at higher precision.

That produces a modeled 1.325 effective bits per routed-expert weight.

### Reply 2 - where it runs

Binary expert work sits beside the weights on a proposed custom HBM4 logic
base die. Four compute chiplets handle residual correction, attention, routing,
and phase-aware scheduling.

Route first, then move only the selected expert work.

### Reply 3 - capacity

For the public Kimi K2.5-class 1T/32B-active configuration:

- VANTA stretch weights: 180.1 GB
- 4 x 48 GB HBM4: 192 GB
- 8K, one-user KV cache: 0.29 GB
- remaining modeled headroom: 11.7 GB

The four-stack version is a tight research target. Six stacks is the credible
serving option.

### Reply 4 - performance claim boundary

The first-order 8K batch-1 decode ceiling is 701.5 tok/s, but that assumes 35%
of raw memory bandwidth survives as end-to-end service bandwidth.

That is a modeled ceiling, **not a benchmark**. Physical area, thermals, timing,
yield, cost, and model quality are all unvalidated.

### Reply 5 - connection to Jalapeno

OpenAI's Jalapeno results sharpened the system principles: keep model and KV
state local, treat networking as part of the accelerator, and schedule prefill
and decode differently.

VANTA-1T explores a separate open architecture around those principles, with
an explicit binary-residual expert representation. No affiliation is implied.

### Reply 6 - the useful ask

The important next test is quality, not a prettier floorplan.

If you work on MoE quantization, HBM/PIM, chiplets, or architecture simulation,
please try to break the 1.325-bit assumption or improve the validation harness.
Failed results are useful results.

## Short alternate X post

Built an open 1T-MoE accelerator design study overnight.

Headline: 180.1 GB resident weights vs 563.7 GB MXFP4-style baseline - a 68.1%
modeled reduction, enough for a one-package capacity target.

It is not silicon and quality is not yet validated. Everything is exposed so
hardware and quantization people can attack the assumptions.

[PROJECT LINK]

## LinkedIn / longer community post

I have released VANTA-1T, an open analytical inference-accelerator design for a
one-trillion-parameter, 32-billion-active mixture-of-experts model.

The design combines a one-bit routed-expert backbone, group scaling, a small
structured 4-bit residual, near-memory binary compute, and four higher-precision
logic chiplets. On the public Kimi K2.5 configuration, the executable model
calculates a 180.1 GB resident weight image versus 563.7 GB for the stated
MXFP4-style baseline, or a 68.1 percent reduction. Four 48 GB HBM4 stacks make
single-package residency capacity-plausible; a six-stack version is the more
credible serving configuration.

The evidence boundary matters: there is no fabricated chip and no measured
throughput. The 701.5 token/s number in the paper is a bandwidth ceiling under
an explicit 35 percent service-efficiency assumption. The most important open
question is whether the binary plus residual representation preserves useful
model quality.

The preprint, Python design-space model, tests, pedagogical RTL, claim ledger,
and interactive architecture lab are available here: [PROJECT LINK]

I would especially value falsification attempts from people working on MoE
quantization, near-memory compute, HBM, chiplets, and cycle-level simulation.

## GitHub release description

### VANTA-1T v0.1

VANTA-1T is an open analytical architecture study for inference on a
one-trillion-total, 32-billion-active MoE model.

This release includes:

- a reproducible Python capacity and bandwidth model;
- the full assumption and claim ledger;
- a design sweep over precision, context, and concurrency;
- pedagogical SystemVerilog for the router and binary-residual MAC;
- a standalone interactive architecture lab; and
- a designed preprint PDF plus source.

Headline analytical result: 180.1 GB resident weights for the stretch profile,
68.1 percent below the modeled 563.7 GB MXFP4-style baseline.

Status: capacity-plausible, quality-unproven. No silicon measurements are
claimed.

## GitHub About description

Open analytical 1T-MoE accelerator study: 68.1% smaller modeled weight image, executable equations, figures, RTL, preprint, and interactive lab.

Suggested topics: `ai-hardware`, `accelerator`, `mixture-of-experts`, `hbm4`, `chiplets`, `quantization`, `computer-architecture`, `llm-inference`.

## Zenodo metadata

- Title: VANTA-1T: Open Analytical Architecture and Executable Model
- Upload type: Software
- Version: 0.1.0
- Creator: Monjur, Mahee
- Affiliation: Independent Researcher
- License: MIT for code; CC BY 4.0 for paper and figures
- Keywords: mixture of experts; inference accelerator; HBM4; near-memory
  computing; quantization; chiplets; large language models
- Related identifier: add the repository release URL after publication
- Description: use the GitHub release description above, followed by the exact
  evidence boundary.

## arXiv plan after the ghosted endorsement email

Do not wait indefinitely on one cold email. The endorsement requirement is
category-specific and is separate from account verification. Build a citable
record first, then make a concise request to an eligible endorser who has a
real topical connection to the work.

Before submitting this paper to arXiv:

1. Add at least one measured quality experiment on an open MoE proxy.
2. Have a second person reproduce `results.json` from a clean checkout.
3. Compile the RTL with a real HDL toolchain and report failures honestly.
4. Add a DOI and stable repository commit to the artifact-availability section.
5. Narrow or expand the novelty claim after a full related-work search.
6. Use the official arXiv endorsement workflow for the chosen category; ask one
   relevant researcher at a time with the PDF and DOI attached.

Suggested endorsement note:

Subject: arXiv cs.AR endorsement request - open 1T-MoE accelerator study

Hello Dr. [Name],

I am an independent researcher preparing an arXiv submission in cs.AR. The
paper is an open analytical architecture study for single-package inference on
a 1T/32B-active MoE. Its main result is a reproducible 68.1 percent resident
weight-memory reduction versus a stated MXFP4-style baseline; it explicitly
labels model quality and physical implementation as unvalidated.

Preprint: [DOI LINK]
Repository and reproducibility instructions: [REPOSITORY LINK]

If the topic is within your area and the paper appears appropriate for cs.AR,
would you be willing to use arXiv's endorsement link? I understand endorsement
does not imply agreement with the paper.

Thank you,
Mahee Monjur

## Posting tactics for a 733-follower / 100K-impression account

- Lead with the interactive motion, not a dense block diagram. Record one click
  of "Run one token" and the memory bar changing between MXFP4 and VANTA.
- Put 68.1 percent in the first post and put "modeled, not measured" in the same
  screenful. Credibility is the growth lever here.
- Use one main link. Link to a landing page that contains the demo, PDF, code,
  and DOI instead of splitting attention across four links.
- Avoid tagging a crowd. Mention the OpenAI Jalapeno report in a reply with a
  direct source link; do not imply collaboration or endorsement.
- Ask a technical question in the last reply: "Which assumption breaks first?"
  That invites useful quote-posts without engagement bait.
- Pin the launch post for one week and reply to substantive critiques with a
  versioned issue or model change.
- A small audience can still work: your existing impression-to-follower ratio
  means the launch should optimize for saves, technical replies, and reposts by
  a few relevant researchers, not raw follower count.

## Exact claim language

Safe headline:

> An open analytical design study finds a single-package capacity path for a
> 1T/32B-active MoE, with a 68.1 percent smaller resident weight image than its
> stated MXFP4-style baseline, contingent on an unvalidated binary-residual
> quantization hypothesis.

Do not say yet:

- "68 percent smaller chip"
- "faster than Rubin"
- "runs Kimi K2.5 at 701 tok/s"
- "production ready"
- "first trillion-parameter chip"
