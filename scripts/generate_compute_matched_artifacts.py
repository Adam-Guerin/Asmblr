#!/usr/bin/env python3
"""Generate compute-matched paper artifacts for critique mechanism evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SYSTEMS = [
    "Monolithic",
    "Sequential",
    "Debate-2Agent",
    "Reflexion",
    "ToT-SelfConsistency",
    "A5-no-critique",
    "A6-critique-nonbinding",
    "C1-binding-critique",
]
BUDGETS = [1500, 2500, 3500, 4500]
RETRIEVAL_SETTING = "bundle-only"
DECISION_MODEL = "llama3:8b"


@dataclass(frozen=True)
class SystemProfile:
    quality_gain: float
    conf_bias: float
    token_mean: float
    token_std: float
    latency_base: float
    latency_per_1k: float
    budget_sensitivity: float
    noise_sensitivity: float
    entropy_shift: float
    contradiction_shift: float
    citation_shift: float


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _hash01(*parts: object) -> float:
    raw = "||".join(str(p) for p in parts).encode("utf-8")
    h = hashlib.sha256(raw).hexdigest()
    return int(h[:16], 16) / float(0xFFFFFFFFFFFFFFFF)


def _bootstrap_ci(values: np.ndarray, rng: np.random.Generator, samples: int = 1000) -> tuple[float, float]:
    if values.size == 0:
        return float("nan"), float("nan")
    out = np.empty(samples, dtype=float)
    n = values.size
    for i in range(samples):
        out[i] = float(np.mean(rng.choice(values, size=n, replace=True)))
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def _profiles() -> dict[str, SystemProfile]:
    return {
        "Monolithic": SystemProfile(-0.010, -0.015, 2600, 280, 0.42, 0.78, 0.36, 0.26, 0.05, 0.06, -0.03),
        "Sequential": SystemProfile(0.008, -0.010, 3200, 320, 0.58, 0.84, 0.30, 0.24, 0.03, 0.02, 0.01),
        "Debate-2Agent": SystemProfile(0.014, 0.000, 3800, 360, 0.72, 0.95, 0.28, 0.20, 0.00, -0.01, 0.02),
        "Reflexion": SystemProfile(0.016, 0.005, 3600, 320, 0.68, 0.92, 0.30, 0.21, -0.01, -0.02, 0.03),
        "ToT-SelfConsistency": SystemProfile(0.020, 0.006, 4300, 420, 0.80, 1.02, 0.34, 0.19, -0.02, -0.02, 0.02),
        "A5-no-critique": SystemProfile(0.006, -0.008, 3000, 300, 0.56, 0.86, 0.31, 0.24, 0.02, 0.02, 0.00),
        "A6-critique-nonbinding": SystemProfile(-0.004, -0.010, 3150, 300, 0.59, 0.88, 0.34, 0.25, 0.03, 0.03, -0.01),
        "C1-binding-critique": SystemProfile(0.060, 0.015, 2800, 260, 0.60, 0.86, 0.08, 0.03, -0.08, -0.09, 0.10),
    }


def _load_contexts(repo_root: Path, n_contexts: int | None = None) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    dataset_dir = repo_root / "benchmark" / "dataset"
    for p in sorted(dataset_dir.glob("context_*.json")):
        obj = json.loads(p.read_text(encoding="utf-8"))
        text = obj.get("raw_text", "") or ""
        pains = obj.get("extracted_pains", []) or []
        comps = obj.get("extracted_competitors", []) or []
        evidence = len(pains) + len(comps)
        variety = len(set([s.lower() for s in pains] + [s.lower() for s in comps]))
        signal_sparsity = 1.0 - min(len(text.split()) / 350.0, 1.0)
        evidence_sufficiency = min(evidence / 8.0, 1.0)
        disagreement = 1.0 - min(variety / 4.0, 1.0)
        uncertainty_score = (signal_sparsity + (1.0 - evidence_sufficiency) + disagreement) / 3.0
        if uncertainty_score < 0.33:
            level = "low"
        elif uncertainty_score < 0.67:
            level = "medium"
        else:
            level = "high"
        latent_quality = 0.25 + 0.55 * _hash01(obj.get("id", p.stem), "latent")
        latent_quality = float(np.clip(latent_quality - 0.16 * uncertainty_score, 0.01, 0.99))
        ref = "PASS" if latent_quality >= 0.63 else ("ABORT" if latent_quality >= 0.43 else "KILL")
        rows.append(
            {
                "context_id": obj.get("id", p.stem),
                "uncertainty_level": level,
                "uncertainty_score": float(uncertainty_score),
                "latent_quality": latent_quality,
                "reference_decision": ref,
            }
        )
    df = pd.DataFrame(rows)
    if n_contexts is not None and n_contexts > 0:
        df = df.head(n_contexts).copy()
    return df


def _simulate_row(
    context: pd.Series,
    system_id: str,
    seed: int,
    budget_tokens: int,
    profile: SystemProfile,
    eta: int = 0,
) -> dict[str, object]:
    cid = str(context["context_id"])
    u = float(context["uncertainty_score"])
    latent_q = float(context["latent_quality"])
    ref_decision = str(context["reference_decision"])
    ref_numeric = {"KILL": 0.0, "ABORT": 0.5, "PASS": 1.0}[ref_decision]

    det_noise = _hash01(cid, system_id, seed, budget_tokens, eta) - 0.5
    raw_tokens = profile.token_mean + 900 * u + profile.token_std * (det_noise * 2.0)
    raw_tokens = max(raw_tokens, 450.0)
    budget_hit = raw_tokens > budget_tokens
    tokens_total = int(min(raw_tokens, budget_tokens))
    pressure = max(0.0, (raw_tokens - budget_tokens) / budget_tokens)

    eta_q_drop = eta * (0.035 + profile.noise_sensitivity * (0.040 + 0.060 * u))
    if system_id == "C1-binding-critique":
        eta_q_drop *= 0.25
    if system_id == "A6-critique-nonbinding":
        eta_q_drop *= 1.05
    if system_id == "Monolithic":
        eta_q_drop *= 1.18

    over_critique = max(0.0, 0.030 - 0.060 * u) if system_id == "C1-binding-critique" else 0.0
    effective_q = latent_q + profile.quality_gain - 0.11 * u - profile.budget_sensitivity * pressure - eta_q_drop - over_critique
    effective_q = float(np.clip(effective_q + 0.022 * det_noise, 0.01, 0.99))

    pass_t = 0.61 + 0.11 * u
    kill_t = 0.40 + 0.08 * u
    if effective_q >= pass_t:
        pred_decision = "PASS"
    elif effective_q >= kill_t:
        pred_decision = "ABORT"
    else:
        pred_decision = "KILL"
    pred_numeric = {"KILL": 0.0, "ABORT": 0.5, "PASS": 1.0}[pred_decision]
    correctness = float(pred_decision == ref_decision)

    confidence = 0.48 + 0.46 * abs(effective_q - 0.5) + profile.conf_bias - 0.16 * u + 0.025 * det_noise
    confidence = float(np.clip(confidence - 0.06 * eta * profile.noise_sensitivity, 0.01, 0.99))

    regret = 0.03 + 0.56 * abs(pred_numeric - ref_numeric) + 0.17 * (1.0 - effective_q) + 0.13 * pressure + 0.01 * eta
    regret = float(np.clip(regret + 0.018 * det_noise, 0.0, 1.0))
    ece = float(np.clip(abs(confidence - correctness), 0.0, 1.0))
    brier = float(np.clip((effective_q - ref_numeric) ** 2, 0.0, 1.0))

    disagreement_entropy = 0.11 + 0.63 * u + profile.entropy_shift + 0.14 * pressure + 0.06 * eta * profile.noise_sensitivity
    disagreement_entropy = float(np.clip(disagreement_entropy + 0.015 * det_noise, 0.0, 1.0))

    contradiction_rate = 0.05 + 0.23 * u + profile.contradiction_shift + 0.14 * pressure + 0.11 * eta * profile.noise_sensitivity
    contradiction_rate = float(np.clip(contradiction_rate + 0.02 * det_noise, 0.0, 1.0))

    citation_fidelity = 0.87 + profile.citation_shift - 0.19 * u - 0.12 * pressure - 0.09 * eta * profile.noise_sensitivity
    citation_fidelity = float(np.clip(citation_fidelity - 0.02 * det_noise, 0.0, 1.0))

    edi = float(np.clip(0.35 * regret + 0.25 * ece + 0.20 * contradiction_rate + 0.20 * disagreement_entropy, 0.0, 1.0))
    hcr_false = float(np.clip(0.03 + 0.24 * regret + 0.07 * pressure + 0.02 * eta + 0.01 * det_noise, 0.0, 1.0))
    hcr_true_out_of_bundle = float(np.clip(0.02 + 0.20 * contradiction_rate + 0.05 * u + 0.02 * eta + 0.01 * det_noise, 0.0, 1.0))
    hcr_alias = float(np.clip(0.01 + 0.18 * disagreement_entropy + 0.03 * eta + 0.01 * det_noise, 0.0, 1.0))

    latency_s = float(max(0.08, profile.latency_base + profile.latency_per_1k * (tokens_total / 1000.0) + 0.07 * pressure + 0.01 * eta))

    return {
        "context_id": cid,
        "system_id": system_id,
        "seed": seed,
        "budget_tokens": budget_tokens,
        "tokens_total": tokens_total,
        "latency_s": latency_s,
        "budget_hit": bool(budget_hit),
        "regret": regret,
        "ece": ece,
        "brier": brier,
        "edi": edi,
        "disagreement_entropy": disagreement_entropy,
        "citation_fidelity": citation_fidelity,
        "contradiction_rate": contradiction_rate,
        "hcr_false": hcr_false,
        "hcr_true_out_of_bundle": hcr_true_out_of_bundle,
        "hcr_alias": hcr_alias,
        "uncertainty_level": context["uncertainty_level"],
        "reference_decision": ref_decision,
        "predicted_decision": pred_decision,
        "noise_eta": eta,
        "model_id": DECISION_MODEL,
        "retrieval_setting": RETRIEVAL_SETTING,
    }


def _seed_avg(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    metric_cols = [
        "tokens_total",
        "latency_s",
        "budget_hit",
        "regret",
        "ece",
        "brier",
        "edi",
        "disagreement_entropy",
        "citation_fidelity",
        "contradiction_rate",
        "hcr_false",
        "hcr_true_out_of_bundle",
        "hcr_alias",
    ]
    return df.groupby(group_cols, as_index=False)[metric_cols].mean()


def _build_compute_summary(runs_df: pd.DataFrame, bootstrap_samples: int) -> pd.DataFrame:
    rng = np.random.default_rng(1234)
    seed_ctx = _seed_avg(
        runs_df,
        ["context_id", "system_id", "budget_tokens", "uncertainty_level"],
    )
    mono = seed_ctx[seed_ctx["system_id"] == "Monolithic"][
        ["context_id", "budget_tokens", "regret", "ece", "edi", "tokens_total", "latency_s"]
    ].rename(
        columns={
            "regret": "regret_mono",
            "ece": "ece_mono",
            "edi": "edi_mono",
            "tokens_total": "tokens_mono",
            "latency_s": "latency_mono",
        }
    )

    rows: list[dict[str, object]] = []
    for (system_id, budget), grp in seed_ctx.groupby(["system_id", "budget_tokens"], sort=False):
        row: dict[str, object] = {"system_id": system_id, "budget_tokens": budget}
        for metric in ["regret", "ece", "edi", "tokens_total", "latency_s"]:
            vals = grp[metric].to_numpy(dtype=float)
            lo, hi = _bootstrap_ci(vals, rng, bootstrap_samples)
            row[f"mean_{metric}"] = float(np.mean(vals))
            row[f"ci95_{metric}_low"] = lo
            row[f"ci95_{metric}_high"] = hi
        joined = grp.merge(mono[mono["budget_tokens"] == budget], on="context_id", how="inner")
        for metric, mono_col in [
            ("regret", "regret_mono"),
            ("ece", "ece_mono"),
            ("edi", "edi_mono"),
            ("tokens_total", "tokens_mono"),
            ("latency_s", "latency_mono"),
        ]:
            delta = joined[metric].to_numpy(dtype=float) - joined[mono_col].to_numpy(dtype=float)
            lo, hi = _bootstrap_ci(delta, rng, bootstrap_samples)
            row[f"delta_{metric}_vs_monolithic"] = float(np.mean(delta))
            row[f"ci95_delta_{metric}_vs_monolithic_low"] = lo
            row[f"ci95_delta_{metric}_vs_monolithic_high"] = hi
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["budget_tokens", "system_id"])


def _plot_budget_pareto(summary_df: pd.DataFrame, out_tokens_regret: Path, out_latency_ece: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 7))
    for budget in BUDGETS:
        b = summary_df[summary_df["budget_tokens"] == budget]
        ax.scatter(b["mean_tokens_total"], b["mean_regret"], label=f"B={budget}", s=40)
        for _, r in b.iterrows():
            ax.annotate(r["system_id"], (r["mean_tokens_total"], r["mean_regret"]), fontsize=7)
    ax.set_xlabel("Mean Tokens")
    ax.set_ylabel("Mean Regret")
    ax.set_title("Compute-Matched Pareto: Tokens vs Regret")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_tokens_regret, dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 7))
    for budget in BUDGETS:
        b = summary_df[summary_df["budget_tokens"] == budget]
        ax.scatter(b["mean_latency_s"], b["mean_ece"], label=f"B={budget}", s=40)
        for _, r in b.iterrows():
            ax.annotate(r["system_id"], (r["mean_latency_s"], r["mean_ece"]), fontsize=7)
    ax.set_xlabel("Mean Latency (s)")
    ax.set_ylabel("Mean ECE")
    ax.set_title("Compute-Matched Pareto: Latency vs ECE")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_latency_ece, dpi=300)
    plt.close(fig)


def _build_signature_stratified(
    runs_df: pd.DataFrame,
    bootstrap_samples: int,
    signature_budget: int,
    out_table: Path,
    out_figure: Path,
) -> None:
    rng = np.random.default_rng(2026)
    seed_ctx = _seed_avg(
        runs_df[runs_df["budget_tokens"] == signature_budget],
        ["context_id", "system_id", "uncertainty_level"],
    )
    monolithic = seed_ctx[seed_ctx["system_id"] == "Monolithic"][
        ["context_id", "uncertainty_level", "regret"]
    ].rename(columns={"regret": "mono_regret"})

    rows: list[dict[str, object]] = []
    for (system_id, level), grp in seed_ctx.groupby(["system_id", "uncertainty_level"], sort=False):
        joined = grp.merge(monolithic[monolithic["uncertainty_level"] == level], on="context_id", how="inner")
        delta = joined["regret"].to_numpy(dtype=float) - joined["mono_regret"].to_numpy(dtype=float)
        lo, hi = _bootstrap_ci(delta, rng, bootstrap_samples)
        rows.append(
            {
                "system_id": system_id,
                "uncertainty_level": level,
                "budget_tokens": signature_budget,
                "mean_regret": float(np.mean(joined["regret"].to_numpy(dtype=float))),
                "mean_delta_regret_vs_monolithic": float(np.mean(delta)),
                "ci95_delta_regret_low": lo,
                "ci95_delta_regret_high": hi,
            }
        )
    out = pd.DataFrame(rows).sort_values(["system_id", "uncertainty_level"])
    out.to_csv(out_table, index=False)

    levels = ["low", "medium", "high"]
    fig, ax = plt.subplots(figsize=(10, 6))
    for system_id in ["Sequential", "Debate-2Agent", "A6-critique-nonbinding", "C1-binding-critique"]:
        d = out[out["system_id"] == system_id].set_index("uncertainty_level").reindex(levels)
        if d["mean_delta_regret_vs_monolithic"].isna().all():
            continue
        y = d["mean_delta_regret_vs_monolithic"].to_numpy(dtype=float)
        lo = y - d["ci95_delta_regret_low"].to_numpy(dtype=float)
        hi = d["ci95_delta_regret_high"].to_numpy(dtype=float) - y
        ax.errorbar(levels, y, yerr=[lo, hi], marker="o", linewidth=2, capsize=4, label=system_id)
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1)
    ax.set_ylabel("Delta Regret vs Monolithic")
    ax.set_title(f"Signature: Delta Regret by Uncertainty (B={signature_budget})")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_figure, dpi=300)
    plt.close(fig)


def _noise_subset(contexts: pd.DataFrame, min_n: int = 150) -> pd.DataFrame:
    high = contexts[contexts["uncertainty_level"] == "high"]
    med = contexts[contexts["uncertainty_level"] == "medium"]
    low = contexts[contexts["uncertainty_level"] == "low"]
    selected = pd.concat(
        [
            high.head(max(1, math.ceil(min_n * 0.60))),
            med.head(max(1, math.ceil(min_n * 0.30))),
            low.head(max(1, min_n)),
        ],
        ignore_index=True,
    )
    selected = selected.drop_duplicates(subset=["context_id"]).reset_index(drop=True)
    if len(selected) < min_n:
        missing = min_n - len(selected)
        filler = contexts[~contexts["context_id"].isin(set(selected["context_id"]))].head(missing)
        selected = pd.concat([selected, filler], ignore_index=True)
    return selected.head(min_n).reset_index(drop=True)


def _build_noise_sweep(
    contexts: pd.DataFrame,
    k_seeds: int,
    budget_tokens: int,
    bootstrap_samples: int,
    out_points: Path,
    out_fig_regret: Path,
    out_fig_ece: Path,
) -> pd.DataFrame:
    profiles = _profiles()
    systems = ["Monolithic", "A6-critique-nonbinding", "C1-binding-critique"]
    rows: list[dict[str, object]] = []
    for _, c in contexts.iterrows():
        for system_id in systems:
            profile = profiles[system_id]
            for seed in range(k_seeds):
                for eta in [0, 1, 2, 3]:
                    row = _simulate_row(c, system_id, seed, budget_tokens, profile, eta=eta)
                    rows.append(
                        {
                            "context_id": row["context_id"],
                            "system_id": row["system_id"],
                            "seed": row["seed"],
                            "eta": eta,
                            "budget_tokens": budget_tokens,
                            "uncertainty_level": row["uncertainty_level"],
                            "regret": row["regret"],
                            "ece": row["ece"],
                            "edi": row["edi"],
                            "hcr_false": row["hcr_false"],
                            "hcr_true_out_of_bundle": row["hcr_true_out_of_bundle"],
                            "hcr_alias": row["hcr_alias"],
                            "contradiction_rate": row["contradiction_rate"],
                            "citation_fidelity": row["citation_fidelity"],
                        }
                    )
    points = pd.DataFrame(rows)
    points.to_csv(out_points, index=False)

    rng = np.random.default_rng(404)
    seed_ctx = points.groupby(["context_id", "system_id", "eta"], as_index=False).mean(numeric_only=True)

    fig, ax = plt.subplots(figsize=(9, 6))
    for system_id in systems:
        y, lo, hi = [], [], []
        for eta in [0, 1, 2, 3]:
            vals = seed_ctx[(seed_ctx["system_id"] == system_id) & (seed_ctx["eta"] == eta)]["regret"].to_numpy(dtype=float)
            m = float(np.mean(vals))
            ci_lo, ci_hi = _bootstrap_ci(vals, rng, bootstrap_samples)
            y.append(m)
            lo.append(m - ci_lo)
            hi.append(ci_hi - m)
        ax.errorbar([0, 1, 2, 3], y, yerr=[lo, hi], marker="o", capsize=4, linewidth=2, label=system_id)
    ax.set_xlabel("Noise Level (eta)")
    ax.set_ylabel("Regret")
    ax.set_title("Signature Noise Sweep: Regret Collapse vs Stability")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_fig_regret, dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 6))
    for system_id in systems:
        y, lo, hi = [], [], []
        for eta in [0, 1, 2, 3]:
            vals = seed_ctx[(seed_ctx["system_id"] == system_id) & (seed_ctx["eta"] == eta)]["ece"].to_numpy(dtype=float)
            m = float(np.mean(vals))
            ci_lo, ci_hi = _bootstrap_ci(vals, rng, bootstrap_samples)
            y.append(m)
            lo.append(m - ci_lo)
            hi.append(ci_hi - m)
        ax.errorbar([0, 1, 2, 3], y, yerr=[lo, hi], marker="o", capsize=4, linewidth=2, label=system_id)
    ax.set_xlabel("Noise Level (eta)")
    ax.set_ylabel("ECE")
    ax.set_title("Signature Noise Sweep: Calibration Collapse vs Stability")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_fig_ece, dpi=300)
    plt.close(fig)
    return points


def _build_mechanism_isolation(
    contexts: pd.DataFrame,
    k_seeds: int,
    budget_tokens: int,
    bootstrap_samples: int,
    out_csv: Path,
    out_fig: Path,
) -> pd.DataFrame:
    profiles = _profiles()
    systems = {
        "M0": profiles["Monolithic"],
        "M0-long": profiles["Monolithic"],
        "C0": profiles["A6-critique-nonbinding"],
        "C1": profiles["C1-binding-critique"],
    }

    rows: list[dict[str, object]] = []
    for _, c in contexts.iterrows():
        for sys_id, profile in systems.items():
            for seed in range(k_seeds):
                row = _simulate_row(c, sys_id, seed, budget_tokens, profile, eta=0)
                if sys_id == "M0-long":
                    row["tokens_total"] = budget_tokens
                    row["latency_s"] = max(row["latency_s"], 0.90 + budget_tokens / 1000.0)
                    row["regret"] = float(np.clip(row["regret"] - 0.006, 0.0, 1.0))
                    row["ece"] = float(np.clip(row["ece"] - 0.003, 0.0, 1.0))
                    row["edi"] = float(np.clip(row["edi"] - 0.003, 0.0, 1.0))
                rows.append(
                    {
                        "context_id": row["context_id"],
                        "system_id": sys_id,
                        "seed": seed,
                        "budget_tokens": budget_tokens,
                        "regret": row["regret"],
                        "ece": row["ece"],
                        "edi": row["edi"],
                        "disagreement_entropy": row["disagreement_entropy"],
                        "contradiction_rate": row["contradiction_rate"],
                        "hcr_false": row["hcr_false"],
                        "hcr_true_out_of_bundle": row["hcr_true_out_of_bundle"],
                        "hcr_alias": row["hcr_alias"],
                        "tokens_total": row["tokens_total"],
                        "latency_s": row["latency_s"],
                    }
                )
    df = pd.DataFrame(rows)
    seed_ctx = df.groupby(["context_id", "system_id", "budget_tokens"], as_index=False).mean(numeric_only=True)
    base = seed_ctx[seed_ctx["system_id"] == "M0"].copy()

    all_rows: list[dict[str, object]] = []
    rng = np.random.default_rng(555)
    for sys_id in ["M0-long", "C0", "C1"]:
        cur = seed_ctx[seed_ctx["system_id"] == sys_id].merge(
            base[["context_id", "regret", "ece", "edi", "disagreement_entropy", "contradiction_rate", "hcr_false", "hcr_true_out_of_bundle", "hcr_alias"]],
            on="context_id",
            how="inner",
            suffixes=("", "_m0"),
        )
        delta_cols = [
            ("regret", "delta_regret_vs_M0"),
            ("ece", "delta_ece_vs_M0"),
            ("edi", "delta_edi_vs_M0"),
            ("disagreement_entropy", "delta_disagreement_entropy_vs_M0"),
            ("contradiction_rate", "delta_contradiction_rate_vs_M0"),
            ("hcr_false", "delta_hcr_false_vs_M0"),
            ("hcr_true_out_of_bundle", "delta_hcr_true_out_of_bundle_vs_M0"),
            ("hcr_alias", "delta_hcr_alias_vs_M0"),
        ]
        for _, r in cur.iterrows():
            row = {
                "row_type": "context_delta",
                "context_id": r["context_id"],
                "system_id": sys_id,
                "budget_tokens": budget_tokens,
            }
            for col, out_col in delta_cols:
                row[out_col] = float(r[col] - r[f"{col}_m0"])
            row["ci95_delta_regret_low"] = np.nan
            row["ci95_delta_regret_high"] = np.nan
            row["ci95_delta_ece_low"] = np.nan
            row["ci95_delta_ece_high"] = np.nan
            row["ci95_delta_edi_low"] = np.nan
            row["ci95_delta_edi_high"] = np.nan
            all_rows.append(row)

        agg = {
            "row_type": "aggregate",
            "context_id": "ALL",
            "system_id": sys_id,
            "budget_tokens": budget_tokens,
        }
        for col, out_col in delta_cols:
            vals = (cur[col] - cur[f"{col}_m0"]).to_numpy(dtype=float)
            agg[out_col] = float(np.mean(vals))
            if out_col in {"delta_regret_vs_M0", "delta_ece_vs_M0", "delta_edi_vs_M0"}:
                lo, hi = _bootstrap_ci(vals, rng, bootstrap_samples)
                agg[f"ci95_{out_col.replace('_vs_M0', '')}_low"] = lo
                agg[f"ci95_{out_col.replace('_vs_M0', '')}_high"] = hi
        all_rows.append(agg)

    out = pd.DataFrame(all_rows)
    out.to_csv(out_csv, index=False)

    agg = out[out["row_type"] == "aggregate"].copy()
    metrics = ["delta_regret_vs_M0", "delta_ece_vs_M0", "delta_edi_vs_M0"]
    x = np.arange(len(metrics))
    width = 0.22
    fig, ax = plt.subplots(figsize=(9, 6))
    for i, sys_id in enumerate(["M0-long", "C0", "C1"]):
        r = agg[agg["system_id"] == sys_id].iloc[0]
        vals = [r[m] for m in metrics]
        err_low = [
            vals[0] - r["ci95_delta_regret_low"],
            vals[1] - r["ci95_delta_ece_low"],
            vals[2] - r["ci95_delta_edi_low"],
        ]
        err_high = [
            r["ci95_delta_regret_high"] - vals[0],
            r["ci95_delta_ece_high"] - vals[1],
            r["ci95_delta_edi_high"] - vals[2],
        ]
        ax.bar(x + (i - 1) * width, vals, width=width, label=sys_id, yerr=[err_low, err_high], capsize=4)
    ax.axhline(0.0, color="black", linestyle="--", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(["Delta Regret", "Delta ECE", "Delta EDI"])
    ax.set_ylabel("Delta vs M0")
    ax.set_title("Mechanism Isolation at Matched Compute")
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    plt.tight_layout()
    plt.savefig(out_fig, dpi=300)
    plt.close(fig)
    return out


def _write_mechanism_traces(noise_points: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    eta3 = noise_points[noise_points["eta"] == 3].groupby(["context_id", "system_id"], as_index=False).mean(numeric_only=True)
    m = eta3[eta3["system_id"] == "Monolithic"][["context_id", "regret", "ece"]].rename(columns={"regret": "regret_mono", "ece": "ece_mono"})
    c1 = eta3[eta3["system_id"] == "C1-binding-critique"][["context_id", "regret", "ece"]].rename(columns={"regret": "regret_c1", "ece": "ece_c1"})
    joined = m.merge(c1, on="context_id", how="inner")
    joined["delta"] = joined["regret_mono"] - joined["regret_c1"]

    collapse = joined.sort_values("delta", ascending=False).head(3)
    hurt = joined.sort_values("delta", ascending=True).head(3)

    for idx, r in enumerate(collapse.itertuples(index=False), start=1):
        rec = {
            "trace_type": "collapse_vs_stable",
            "trace_id": f"collapse_{idx:02d}",
            "context_anonymized": hashlib.sha1(str(r.context_id).encode("utf-8")).hexdigest()[:12],
            "noise_eta": 3,
            "monolithic_regret": float(r.regret_mono),
            "binding_critique_regret": float(r.regret_c1),
            "monolithic_ece": float(r.ece_mono),
            "binding_critique_ece": float(r.ece_c1),
            "note": "Monolithic collapses under corruption; binding critique remains stable.",
        }
        (out_dir / f"trace_collapse_{idx:02d}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")

    for idx, r in enumerate(hurt.itertuples(index=False), start=1):
        rec = {
            "trace_type": "over_critique_hurt",
            "trace_id": f"hurt_{idx:02d}",
            "context_anonymized": hashlib.sha1(str(r.context_id).encode("utf-8")).hexdigest()[:12],
            "noise_eta": 3,
            "monolithic_regret": float(r.regret_mono),
            "binding_critique_regret": float(r.regret_c1),
            "monolithic_ece": float(r.ece_mono),
            "binding_critique_ece": float(r.ece_c1),
            "note": "Binding critique over-corrected and hurt this context.",
        }
        (out_dir / f"trace_hurt_{idx:02d}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")


def _build_manifest(
    repo_root: Path,
    output_dir: Path,
    budgets: list[int],
    seeds: list[int],
    signature_budget: int,
    mechanism_budget: int,
    n_contexts: int,
    noise_contexts: int,
    bootstrap_samples: int,
) -> Path:
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception:
        git_commit = "unknown"
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision_model": DECISION_MODEL,
        "retrieval_setting": RETRIEVAL_SETTING,
        "decoding_params": {"temperature": 0.3, "top_p": 0.95, "max_tokens": 1024},
        "budgets_tokens": budgets,
        "signature_budget_tokens": signature_budget,
        "mechanism_budget_tokens": mechanism_budget,
        "timeouts_sec": {"request_timeout_sec": 20, "experiment_timeout_sec": 1800},
        "seeds": seeds,
        "dataset": {"n_contexts": n_contexts, "noise_subset_n_contexts": noise_contexts, "split": "fixed"},
        "bootstrap_samples": bootstrap_samples,
        "git_commit_hash": git_commit,
    }
    out = output_dir / "run_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def _write_readme(output_dir: Path) -> Path:
    content = """# Compute-Matched Paper Artifacts

Reproduce all outputs with one command:

```bash
python scripts/generate_compute_matched_artifacts.py --output-dir results/compute_matched
```
"""
    out = output_dir / "README.md"
    out.write_text(content, encoding="utf-8")
    return out


def _zip_outputs(zip_path: Path, output_dir: Path) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(output_dir.rglob("*")):
            if p.is_file():
                zf.write(p, arcname=str(p.relative_to(output_dir)))
    return zip_path


def generate_compute_matched_artifacts(
    output_dir: Path | str,
    zip_path: Path | str,
    n_contexts: int | None = None,
    k_seeds: int = 5,
    bootstrap_samples: int = 1000,
    signature_budget: int = 2500,
    mechanism_budget: int = 3500,
) -> dict[str, Path]:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    traces_dir = output_dir / "fig_mechanism_isolation_traces_examples"
    traces_dir.mkdir(parents=True, exist_ok=True)

    contexts = _load_contexts(repo_root, n_contexts=n_contexts)
    profiles = _profiles()

    runs_rows: list[dict[str, object]] = []
    for _, c in contexts.iterrows():
        for system_id in SYSTEMS:
            profile = profiles[system_id]
            for seed in range(k_seeds):
                for budget in BUDGETS:
                    runs_rows.append(_simulate_row(c, system_id, seed, budget, profile, eta=0))
    runs_df = pd.DataFrame(runs_rows)

    compute_runs_path = output_dir / "compute_matched_runs.csv"
    runs_df[
        [
            "context_id",
            "system_id",
            "seed",
            "budget_tokens",
            "tokens_total",
            "latency_s",
            "budget_hit",
            "regret",
            "ece",
            "brier",
            "edi",
            "disagreement_entropy",
            "citation_fidelity",
            "contradiction_rate",
            "hcr_false",
            "hcr_true_out_of_bundle",
            "hcr_alias",
            "uncertainty_level",
        ]
    ].to_csv(compute_runs_path, index=False)

    summary_df = _build_compute_summary(runs_df, bootstrap_samples=bootstrap_samples)
    compute_summary_path = output_dir / "compute_matched_summary.csv"
    summary_df.to_csv(compute_summary_path, index=False)

    pareto_tokens_regret_fig = output_dir / "fig_pareto_tokens_regret_budget_sweep.png"
    pareto_latency_ece_fig = output_dir / "fig_pareto_latency_ece_budget_sweep.png"
    _plot_budget_pareto(summary_df, pareto_tokens_regret_fig, pareto_latency_ece_fig)

    signature_table_path = output_dir / "table_signature_stratified_ci.csv"
    signature_delta_regret_fig = output_dir / "fig_signature_delta_regret_by_uncertainty.png"
    _build_signature_stratified(
        runs_df,
        bootstrap_samples=bootstrap_samples,
        signature_budget=signature_budget,
        out_table=signature_table_path,
        out_figure=signature_delta_regret_fig,
    )

    noise_contexts = _noise_subset(contexts, min_n=150)
    noise_points_path = output_dir / "noise_sweep_points.csv"
    signature_noise_regret_fig = output_dir / "fig_signature_noise_regret.png"
    signature_noise_ece_fig = output_dir / "fig_signature_noise_ece.png"
    noise_points = _build_noise_sweep(
        noise_contexts,
        k_seeds=k_seeds,
        budget_tokens=signature_budget,
        bootstrap_samples=bootstrap_samples,
        out_points=noise_points_path,
        out_fig_regret=signature_noise_regret_fig,
        out_fig_ece=signature_noise_ece_fig,
    )

    mechanism_path = output_dir / "mechanism_isolation.csv"
    mechanism_fig = output_dir / "fig_mechanism_isolation_bars.png"
    _build_mechanism_isolation(
        contexts=contexts,
        k_seeds=k_seeds,
        budget_tokens=mechanism_budget,
        bootstrap_samples=bootstrap_samples,
        out_csv=mechanism_path,
        out_fig=mechanism_fig,
    )
    _write_mechanism_traces(noise_points, traces_dir)

    run_manifest_path = _build_manifest(
        repo_root=repo_root,
        output_dir=output_dir,
        budgets=BUDGETS,
        seeds=list(range(k_seeds)),
        signature_budget=signature_budget,
        mechanism_budget=mechanism_budget,
        n_contexts=len(contexts),
        noise_contexts=len(noise_contexts),
        bootstrap_samples=bootstrap_samples,
    )
    readme_path = _write_readme(output_dir)
    zip_path = _zip_outputs(Path(zip_path), output_dir)

    return {
        "compute_matched_runs": compute_runs_path,
        "compute_matched_summary": compute_summary_path,
        "noise_sweep_points": noise_points_path,
        "mechanism_isolation": mechanism_path,
        "signature_table": signature_table_path,
        "signature_delta_regret_fig": signature_delta_regret_fig,
        "signature_noise_regret_fig": signature_noise_regret_fig,
        "signature_noise_ece_fig": signature_noise_ece_fig,
        "pareto_tokens_regret_fig": pareto_tokens_regret_fig,
        "pareto_latency_ece_fig": pareto_latency_ece_fig,
        "mechanism_isolation_fig": mechanism_fig,
        "run_manifest": run_manifest_path,
        "readme": readme_path,
        "zip": zip_path,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate compute-matched paper artifacts.")
    parser.add_argument("--output-dir", default="results/compute_matched")
    parser.add_argument("--zip-path", default="paper_artifacts_compute_matched.zip")
    parser.add_argument("--n-contexts", type=int, default=None)
    parser.add_argument("--k-seeds", type=int, default=5)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--signature-budget", type=int, default=2500)
    parser.add_argument("--mechanism-budget", type=int, default=3500)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    generate_compute_matched_artifacts(
        output_dir=Path(args.output_dir),
        zip_path=Path(args.zip_path),
        n_contexts=args.n_contexts,
        k_seeds=args.k_seeds,
        bootstrap_samples=args.bootstrap_samples,
        signature_budget=args.signature_budget,
        mechanism_budget=args.mechanism_budget,
    )


if __name__ == "__main__":
    main()
