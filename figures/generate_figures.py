#!/usr/bin/env python3
"""Generate publication-ready VANTA-1T figures from the executable model."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "model"))

from vanta_model import (  # noqa: E402
    HardwareSpec,
    ModelSpec,
    MXFP4,
    VANTA_BALANCED,
    VANTA_STRETCH,
    PrecisionProfile,
    kv_cache_gb,
    resident_weight_gb,
    single_stream_decode_tps,
)


OUTPUT = Path(__file__).resolve().parent
COLORS = {
    "reference": "#64748b",
    "baseline": "#2563eb",
    "balanced": "#7c3aed",
    "stretch": "#ea580c",
    "capacity": "#0f766e",
    "grid": "#cbd5e1",
    "ink": "#172033",
}


def setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": COLORS["ink"],
            "axes.labelcolor": COLORS["ink"],
            "axes.titlecolor": COLORS["ink"],
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "xtick.color": COLORS["ink"],
            "ytick.color": COLORS["ink"],
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "legend.frameon": False,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
            "svg.hashsalt": "vanta-1t",
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    fig.savefig(OUTPUT / f"{stem}.svg", metadata={"Date": None})
    fig.savefig(OUTPUT / f"{stem}.png", dpi=200, metadata={"Software": "VANTA-1T"})
    plt.close(fig)


def fp8_profile() -> PrecisionProfile:
    return PrecisionProfile(
        name="FP8 reference",
        core_bits=8.0,
        scale_bits_per_weight=0.0,
        residual_bits_per_weight=0.0,
        metadata_bits_per_weight=0.0,
        quality_status="Reference only",
    )


def resident_memory_figure(model: ModelSpec, hardware: HardwareSpec) -> None:
    profiles = [fp8_profile(), MXFP4, VANTA_BALANCED, VANTA_STRETCH]
    labels = ["FP8\nreference", "MXFP4-style\nbaseline", "VANTA\nbalanced", "VANTA\nstretch"]
    values = [resident_weight_gb(model, p, hardware.nonexpert_resident_gb) for p in profiles]
    colors = [COLORS["reference"], COLORS["baseline"], COLORS["balanced"], COLORS["stretch"]]

    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    bars = ax.bar(labels, values, color=colors, width=0.66)
    ax.axhline(
        hardware.hbm_capacity_gb,
        color=COLORS["capacity"],
        linewidth=2,
        linestyle="--",
        label="4 × 48 GB HBM4 capacity (192 GB)",
    )
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 22,
            f"{value:,.1f} GB",
            ha="center",
            va="bottom",
            fontweight="bold",
            color=COLORS["ink"],
        )
    ax.annotate(
        "68.1% below baseline\nquality unvalidated",
        xy=(3, values[-1]),
        xytext=(2.25, 470),
        arrowprops={"arrowstyle": "->", "color": COLORS["stretch"], "linewidth": 1.7},
        color=COLORS["stretch"],
        fontweight="bold",
    )
    ax.set_title("Resident weight memory: capacity path, not a silicon result", loc="left")
    ax.set_ylabel("Resident weight image (decimal GB)")
    ax.set_ylim(0, max(values) * 1.16)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.01,
        0.01,
        "Calculated from the published equations. VANTA compression quality and physical implementation are unvalidated.",
        color=COLORS["ink"],
        fontsize=8.5,
    )
    save_figure(fig, "resident-memory")


def capacity_envelope_figure(model: ModelSpec) -> None:
    contexts = np.array([8_192, 32_768, 65_536, 131_072, 262_144])
    labels = ["8K", "32K", "64K", "128K", "256K"]
    weights = resident_weight_gb(model, VANTA_STRETCH, 12.0)
    four_stack = HardwareSpec(hbm_stacks=4)
    six_stack = HardwareSpec(hbm_stacks=6, target_package_power_w=780.0)

    def max_sequences(capacity: float, context: int) -> int:
        one_kv = kv_cache_gb(model, context, 1, 8)
        return max(0, int((capacity - weights) // one_kv))

    four = [max_sequences(four_stack.hbm_capacity_gb, int(c)) for c in contexts]
    six = [max_sequences(six_stack.hbm_capacity_gb, int(c)) for c in contexts]

    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    x = np.arange(len(contexts))
    width = 0.36
    bars_four = ax.bar(x - width / 2, four, width, label="4 stacks / 192 GB", color=COLORS["stretch"])
    bars_six = ax.bar(x + width / 2, six, width, label="6 stacks / 288 GB", color=COLORS["capacity"])
    for bars in (bars_four, bars_six):
        for bar in bars:
            value = int(bar.get_height())
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + max(six) * 0.012,
                str(value),
                ha="center",
                va="bottom",
                color=COLORS["ink"],
                fontsize=9,
            )
    ax.set_title("Modeled 8-bit MLA KV-cache concurrency after resident weights", loc="left")
    ax.set_xlabel("Context length per sequence")
    ax.set_ylabel("Whole concurrent sequences that fit")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, max(six) * 1.14)
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.01,
        0.01,
        "Excludes allocator fragmentation, activations, workspaces, prefix metadata, and operational reserve.",
        color=COLORS["ink"],
        fontsize=8.5,
    )
    save_figure(fig, "capacity-envelope")


def decode_ceiling_figure(model: ModelSpec, hardware: HardwareSpec) -> None:
    contexts = np.geomspace(2_048, 262_144, 80)
    series = [
        (MXFP4, "MXFP4-style baseline", COLORS["baseline"]),
        (VANTA_BALANCED, "VANTA balanced", COLORS["balanced"]),
        (VANTA_STRETCH, "VANTA stretch", COLORS["stretch"]),
    ]
    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    for profile, label, color in series:
        values = [single_stream_decode_tps(model, profile, hardware, int(c), 8) for c in contexts]
        ax.plot(contexts, values, label=label, color=color, linewidth=2.4)
    ax.axvline(8_192, color=COLORS["grid"], linewidth=1.0)
    stretch_8k = single_stream_decode_tps(model, VANTA_STRETCH, hardware, 8_192, 8)
    ax.scatter([8_192], [stretch_8k], color=COLORS["stretch"], s=42, zorder=3)
    ax.annotate(
        "701.5 tok/s at 8K\nmodeled ceiling",
        xy=(8_192, stretch_8k),
        xytext=(2_750, 610),
        arrowprops={"arrowstyle": "->", "color": COLORS["stretch"]},
        color=COLORS["stretch"],
        fontweight="bold",
    )
    ax.set_xscale("log", base=2)
    ax.set_xticks([2_048, 8_192, 32_768, 131_072, 262_144], ["2K", "8K", "32K", "128K", "256K"])
    ax.set_title("Single-stream decode ceiling under one bandwidth scenario", loc="left")
    ax.set_xlabel("Context length (tokens)")
    ax.set_ylabel("Modeled ceiling (tokens/s)")
    ax.grid(color=COLORS["grid"], linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.01,
        0.01,
        "Assumes 35% of 11.2 TB/s raw HBM bandwidth is usable end to end. This is not a benchmark or forecast.",
        color=COLORS["ink"],
        fontsize=8.5,
    )
    save_figure(fig, "decode-ceiling")


def social_card() -> None:
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 675)
    ax.axis("off")
    background = "#0b1020"
    panel = "#151d32"
    white = "#f8fafc"
    muted = "#a9b5cc"
    orange = "#ff6b24"
    teal = "#23c9b8"
    blue = "#5794ff"
    fig.patch.set_facecolor(background)
    ax.set_facecolor(background)

    ax.text(62, 610, "VANTA-1T", color=white, fontsize=31, fontweight="bold", va="top")
    ax.text(
        62,
        565,
        "OPEN ANALYTICAL ACCELERATOR STUDY",
        color=teal,
        fontsize=11,
        fontweight="bold",
        va="top",
    )
    ax.text(62, 470, "68.1%", color=orange, fontsize=72, fontweight="bold", va="top")
    ax.text(62, 392, "less resident weight memory", color=white, fontsize=25, fontweight="bold", va="top")
    ax.text(62, 350, "180.1 GB vs 563.7 GB MXFP4-style baseline", color=muted, fontsize=16, va="top")
    ax.text(62, 307, "1T total / 32B active MoE  •  single-package capacity target", color=muted, fontsize=14, va="top")

    caveat = FancyBboxPatch(
        (62, 177),
        610,
        78,
        boxstyle="round,pad=0.02,rounding_size=12",
        linewidth=1.5,
        edgecolor=orange,
        facecolor="#211a23",
    )
    ax.add_patch(caveat)
    ax.text(84, 231, "MODELED, NOT MEASURED", color=orange, fontsize=13, fontweight="bold", va="top")
    ax.text(84, 201, "No silicon benchmark. Compression quality is still unvalidated.", color=white, fontsize=13, va="top")

    x0 = 745
    ax.text(x0, 560, "Route first. Move less.", color=white, fontsize=21, fontweight="bold", va="top")
    blocks = [
        ("TOP-K ROUTER", blue, 500),
        ("1-BIT HBM-SIDE BACKBONE", teal, 390),
        ("4-BIT STRUCTURED RESIDUAL", orange, 280),
        ("CORRECTED EXPERT OUTPUT", blue, 170),
    ]
    for index, (label, color, y) in enumerate(blocks):
        rect = FancyBboxPatch(
            (x0, y - 55),
            385,
            68,
            boxstyle="round,pad=0.02,rounding_size=12",
            linewidth=1.8,
            edgecolor=color,
            facecolor=panel,
        )
        ax.add_patch(rect)
        ax.text(x0 + 192.5, y - 20, label, color=white, fontsize=13, fontweight="bold", ha="center", va="center")
        if index < len(blocks) - 1:
            ax.annotate(
                "",
                xy=(x0 + 192.5, y - 86),
                xytext=(x0 + 192.5, y - 57),
                arrowprops={"arrowstyle": "-|>", "color": muted, "linewidth": 1.5},
            )

    ax.plot([62, 1135], [112, 112], color="#2b3550", linewidth=1)
    ax.text(62, 74, "Mahee Monjur  •  Independent Researcher", color=white, fontsize=13, va="center")
    ax.text(1135, 74, "capacity-plausible  •  quality-unproven", color=muted, fontsize=12, ha="right", va="center")

    fig.savefig(ROOT / "launch" / "vanta-1t-social.png", dpi=160, facecolor=background, metadata={"Software": "VANTA-1T"})
    plt.close(fig)


def main() -> None:
    setup_style()
    model = ModelSpec()
    hardware = HardwareSpec()
    resident_memory_figure(model, hardware)
    capacity_envelope_figure(model)
    decode_ceiling_figure(model, hardware)
    social_card()
    print("Generated three analytical figures and the launch card.")


if __name__ == "__main__":
    main()
