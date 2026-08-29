#!/usr/bin/env python3
"""Analytical design-space model for the VANTA-1T inference accelerator.

This is deliberately a transparent upper-bound/first-order model. It predicts
capacity and bandwidth ceilings; it does not claim silicon measurements or
model-quality preservation after quantization.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path


DECIMAL_GB = 1_000_000_000
DECIMAL_TB = 1_000_000_000_000


@dataclass(frozen=True)
class ModelSpec:
    name: str = "Kimi K2.5-class MoE"
    total_parameters_published: int = 1_000_000_000_000
    active_parameters: int = 32_000_000_000
    hidden_size: int = 7_168
    layers: int = 61
    dense_layers: int = 1
    routed_experts: int = 384
    selected_experts: int = 8
    expert_intermediate_size: int = 2_048
    kv_lora_rank: int = 512
    qk_rope_head_dim: int = 64
    context_length: int = 262_144

    @property
    def moe_layers(self) -> int:
        return self.layers - self.dense_layers

    @property
    def routed_parameter_estimate(self) -> int:
        # SwiGLU expert: gate, up, and down matrices.
        return (
            self.moe_layers
            * self.routed_experts
            * 3
            * self.hidden_size
            * self.expert_intermediate_size
        )


@dataclass(frozen=True)
class PrecisionProfile:
    name: str
    core_bits: float
    scale_bits_per_weight: float
    residual_bits_per_weight: float
    metadata_bits_per_weight: float
    quality_status: str

    @property
    def effective_bits(self) -> float:
        return (
            self.core_bits
            + self.scale_bits_per_weight
            + self.residual_bits_per_weight
            + self.metadata_bits_per_weight
        )


@dataclass(frozen=True)
class HardwareSpec:
    name: str = "VANTA-1T research target"
    hbm_stacks: int = 4
    hbm_capacity_gb_per_stack: float = 48.0
    hbm_bandwidth_tb_s_per_stack: float = 2.8
    service_efficiency: float = 0.35
    nonexpert_resident_gb: float = 12.0
    target_package_power_w: float = 650.0

    @property
    def hbm_capacity_gb(self) -> float:
        return self.hbm_stacks * self.hbm_capacity_gb_per_stack

    @property
    def hbm_bandwidth_tb_s(self) -> float:
        return self.hbm_stacks * self.hbm_bandwidth_tb_s_per_stack


MXFP4 = PrecisionProfile(
    name="MXFP4 baseline",
    core_bits=4.0,
    scale_bits_per_weight=0.25,  # one 8-bit scale per 32 values
    residual_bits_per_weight=0.0,
    metadata_bits_per_weight=0.10,
    quality_status="Public deployment format; metadata term is an analytical allowance.",
)

VANTA_BALANCED = PrecisionProfile(
    name="VANTA balanced",
    core_bits=2.0,
    scale_bits_per_weight=0.125,  # one 8-bit scale per 64 values
    residual_bits_per_weight=0.16,  # 4% equivalent parameters at 4-bit
    metadata_bits_per_weight=0.04,
    quality_status="Requires model-specific calibration or QAT; not validated on Kimi K2.5.",
)

VANTA_STRETCH = PrecisionProfile(
    name="VANTA binary-residual stretch",
    core_bits=1.0,
    scale_bits_per_weight=0.125,
    residual_bits_per_weight=0.16,
    metadata_bits_per_weight=0.04,
    quality_status="Research hypothesis only; quality preservation is unmeasured.",
)


def resident_weight_gb(
    model: ModelSpec,
    profile: PrecisionProfile,
    nonexpert_resident_gb: float,
) -> float:
    expert_gb = model.routed_parameter_estimate * profile.effective_bits / 8 / DECIMAL_GB
    return expert_gb + nonexpert_resident_gb


def kv_cache_gb(
    model: ModelSpec,
    context_tokens: int,
    concurrent_sequences: int,
    kv_bits: int,
) -> float:
    # MLA stores a latent vector plus the RoPE component per token per layer.
    elements = (
        model.layers
        * context_tokens
        * concurrent_sequences
        * (model.kv_lora_rank + model.qk_rope_head_dim)
    )
    return elements * kv_bits / 8 / DECIMAL_GB


def single_stream_decode_tps(
    model: ModelSpec,
    profile: PrecisionProfile,
    hardware: HardwareSpec,
    context_tokens: int,
    kv_bits: int,
) -> float:
    active_weight_bytes = model.active_parameters * profile.effective_bits / 8
    kv_read_bytes = (
        model.layers
        * context_tokens
        * (model.kv_lora_rank + model.qk_rope_head_dim)
        * kv_bits
        / 8
    )
    usable_bandwidth = hardware.hbm_bandwidth_tb_s * DECIMAL_TB * hardware.service_efficiency
    return usable_bandwidth / (active_weight_bytes + kv_read_bytes)


def evaluate(
    model: ModelSpec,
    hardware: HardwareSpec,
    profile: PrecisionProfile,
    context_tokens: int,
    concurrent_sequences: int,
    kv_bits: int,
) -> dict:
    weights_gb = resident_weight_gb(model, profile, hardware.nonexpert_resident_gb)
    kv_gb = kv_cache_gb(model, context_tokens, concurrent_sequences, kv_bits)
    total_gb = weights_gb + kv_gb
    baseline_gb = resident_weight_gb(model, MXFP4, hardware.nonexpert_resident_gb)
    return {
        "profile": profile.name,
        "effective_expert_bits": round(profile.effective_bits, 4),
        "resident_weights_gb": round(weights_gb, 3),
        "kv_cache_gb": round(kv_gb, 3),
        "total_hbm_demand_gb": round(total_gb, 3),
        "hbm_capacity_gb": round(hardware.hbm_capacity_gb, 3),
        "hbm_headroom_gb": round(hardware.hbm_capacity_gb - total_gb, 3),
        "fits": total_gb <= hardware.hbm_capacity_gb,
        "weight_reduction_vs_mxfp4_pct": round((1 - weights_gb / baseline_gb) * 100, 2),
        "single_stream_decode_ceiling_tps": round(
            single_stream_decode_tps(model, profile, hardware, context_tokens, kv_bits), 1
        ),
        "quality_status": profile.quality_status,
    }


def sweep_rows(model: ModelSpec, hardware: HardwareSpec) -> list[dict]:
    rows: list[dict] = []
    profiles = [MXFP4, VANTA_BALANCED, VANTA_STRETCH]
    for profile in profiles:
        for context in (8_192, 32_768, 131_072, 262_144):
            for users in (1, 2, 4, 8):
                rows.append(evaluate(model, hardware, profile, context, users, 8))
                rows[-1]["context_tokens"] = context
                rows[-1]["concurrent_sequences"] = users
                rows[-1]["kv_bits"] = 8
    return rows


def build_report() -> dict:
    model = ModelSpec()
    target = HardwareSpec()
    production = HardwareSpec(
        name="VANTA-1T production-capacity option",
        hbm_stacks=6,
        target_package_power_w=780.0,
    )
    baseline_weights = resident_weight_gb(model, MXFP4, target.nonexpert_resident_gb)
    stretch_weights = resident_weight_gb(model, VANTA_STRETCH, target.nonexpert_resident_gb)
    fp8_reference_gb = model.routed_parameter_estimate / DECIMAL_GB + target.nonexpert_resident_gb
    return {
        "status": "analytical research target; no silicon or quality measurements",
        "model": {
            **asdict(model),
            "moe_layers": model.moe_layers,
            "routed_parameter_estimate": model.routed_parameter_estimate,
        },
        "hardware": {
            "research_target": asdict(target),
            "production_capacity_option": asdict(production),
        },
        "headline": {
            "mxfp4_resident_weight_gb": round(baseline_weights, 2),
            "vanta_stretch_resident_weight_gb": round(stretch_weights, 2),
            "weight_reduction_vs_mxfp4_pct": round(
                (1 - stretch_weights / baseline_weights) * 100, 2
            ),
            "weight_reduction_vs_fp8_pct": round(
                (1 - stretch_weights / fp8_reference_gb) * 100, 2
            ),
            "hbm_capacity_gb": target.hbm_capacity_gb,
            "hbm_stack_count": target.hbm_stacks,
            "rubin_nvl4_gpu_count_reference": 4,
            "accelerator_package_count_reduction_vs_nvl4_pct": 75.0,
            "package_count_note": (
                "Package-count comparison is not a die-area measurement; NVIDIA lists four "
                "Rubin GPUs for NVL4, while VANTA is a one-package research target."
            ),
        },
        "representative_cases": {
            "research_8k_one_user": evaluate(
                model, target, VANTA_STRETCH, 8_192, 1, 8
            ),
            "research_128k_one_user": evaluate(
                model, target, VANTA_STRETCH, 131_072, 1, 8
            ),
            "production_128k_eight_users": evaluate(
                model, production, VANTA_STRETCH, 131_072, 8, 8
            ),
            "same_bandwidth_mxfp4_8k": evaluate(
                model, target, MXFP4, 8_192, 1, 8
            ),
        },
        "assumptions": [
            "HBM capacity uses four or six 48 GB stacks.",
            "HBM bandwidth uses 2.8 TB/s per stack, not the faster 3.3 TB/s peak claim.",
            "The 35% service-efficiency factor is a scenario assumption, not a measurement.",
            "Binary-residual accuracy on Kimi K2.5 is unknown and is the main gating experiment.",
            "KV cache uses 8-bit MLA latents and is modeled without allocator fragmentation.",
            "Physical package area and thermal feasibility require foundry/EDA validation.",
        ],
    }


def write_outputs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_report()
    (output_dir / "results.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    rows = sweep_rows(ModelSpec(), HardwareSpec())
    with (output_dir / "sweep.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "output")
    parser.add_argument("--print", action="store_true", dest="print_report")
    args = parser.parse_args()
    write_outputs(args.output_dir)
    if args.print_report:
        print(json.dumps(build_report(), indent=2))


if __name__ == "__main__":
    main()
