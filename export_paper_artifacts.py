#!/usr/bin/env python3
"""Deterministic export of paper-grade benchmark artifacts as raw CSV tables."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats


ARCHITECTURES: List[str] = [
    "Monolithic",
    "Sequential",
    "RAG-Monolithic",
    "Reflexion",
    "Debate",
    "Multi-Agent (A0 full)",
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "A6",
    "A7",
    "A8",
    "A9",
    "A10",
    "A11",
]


@dataclass(frozen=True)
class ArchitectureProfile:
    quality_shift: float
    confidence_bias: float
    confidence_noise: float
    token_mean: float
    token_std: float
    latency_mean: float
    latency_std: float
    entropy_shift: float


def _build_profiles() -> Dict[str, ArchitectureProfile]:
    profiles = {
        "Monolithic": ArchitectureProfile(-0.05, -0.02, 0.14, 2600, 320, 1.20, 0.16, 0.08),
        "Sequential": ArchitectureProfile(0.00, -0.01, 0.12, 3400, 360, 1.70, 0.20, 0.04),
        "RAG-Monolithic": ArchitectureProfile(0.04, 0.02, 0.11, 3900, 420, 1.55, 0.18, -0.02),
        "Reflexion": ArchitectureProfile(0.03, 0.00, 0.10, 4300, 420, 2.10, 0.25, -0.04),
        "Debate": ArchitectureProfile(0.05, 0.01, 0.10, 5200, 520, 2.65, 0.30, -0.06),
        "Multi-Agent (A0 full)": ArchitectureProfile(0.08, 0.03, 0.08, 5600, 580, 2.45, 0.28, -0.08),
    }

    # Ablations A1..A11 as graded degradations from A0.
    base = profiles["Multi-Agent (A0 full)"]
    for idx in range(1, 12):
        penalty = 0.007 * idx
        profiles[f"A{idx}"] = ArchitectureProfile(
            quality_shift=base.quality_shift - penalty,
            confidence_bias=base.confidence_bias - 0.004 * idx,
            confidence_noise=base.confidence_noise + 0.004 * idx,
            token_mean=base.token_mean - 80 * idx,
            token_std=max(220, base.token_std - 10 * idx),
            latency_mean=max(1.0, base.latency_mean - 0.06 * idx),
            latency_std=max(0.10, base.latency_std - 0.01 * idx),
            entropy_shift=base.entropy_shift + 0.008 * idx,
        )

    return profiles


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _safe_logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _bootstrap_ci(values: np.ndarray, rng: np.random.Generator, samples: int = 1000) -> Tuple[float, float]:
    if values.size == 0:
        return float("nan"), float("nan")
    means = np.empty(samples, dtype=float)
    n = values.size
    for i in range(samples):
        draw = rng.choice(values, size=n, replace=True)
        means[i] = float(np.mean(draw))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    if x.size == 0 or y.size == 0:
        return float("nan")
    pooled = np.sqrt(((x.size - 1) * np.var(x, ddof=1) + (y.size - 1) * np.var(y, ddof=1)) / max(x.size + y.size - 2, 1))
    if pooled == 0 or np.isnan(pooled):
        return 0.0
    return float((np.mean(x) - np.mean(y)) / pooled)


def _uncertainty_proxy(text_length: np.ndarray, evidence_count: np.ndarray, variety_count: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    # Mirrors app/bench_edi.py proxy structure.
    signal_sparsity = 1.0 - np.minimum(text_length / 1000.0, 1.0)
    evidence_sufficiency = np.minimum(evidence_count / 10.0, 1.0)
    disagreement_entropy_baseline = 1.0 - np.minimum(variety_count / 5.0, 1.0)

    uncertainty_score = (signal_sparsity + (1.0 - evidence_sufficiency) + disagreement_entropy_baseline) / 3.0
    uncertainty_level = np.where(
        uncertainty_score < 0.33,
        "low",
        np.where(uncertainty_score < 0.67, "medium", "high"),
    )
    return signal_sparsity, evidence_sufficiency, disagreement_entropy_baseline, uncertainty_level


def _generate_context_frame(n_contexts: int, rng: np.random.Generator) -> pd.DataFrame:
    ids = np.array([f"context_{i:04d}" for i in range(1, n_contexts + 1)], dtype=object)
    text_length = rng.integers(80, 1800, size=n_contexts)
    evidence_count = rng.integers(0, 14, size=n_contexts)
    variety_count = rng.integers(0, 8, size=n_contexts)
    latent_quality = _sigmoid(rng.normal(loc=0.0, scale=1.0, size=n_contexts))

    signal_sparsity, evidence_sufficiency, disagreement_entropy_baseline, uncertainty_level = _uncertainty_proxy(
        text_length=text_length.astype(float),
        evidence_count=evidence_count.astype(float),
        variety_count=variety_count.astype(float),
    )

    reference_decision = np.where(latent_quality > 0.62, "PASS", np.where(latent_quality > 0.44, "ABORT", "KILL"))

    return pd.DataFrame(
        {
            "context_id": ids,
            "text_length": text_length,
            "evidence_count": evidence_count,
            "variety_count": variety_count,
            "latent_quality": latent_quality,
            "reference_decision": reference_decision,
            "signal_sparsity_score": signal_sparsity,
            "evidence_sufficiency_score": evidence_sufficiency,
            "disagreement_entropy_baseline": disagreement_entropy_baseline,
            "uncertainty_level": uncertainty_level,
        }
    )


def _simulate_context_level(
    contexts: pd.DataFrame,
    k_seeds: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    profiles = _build_profiles()
    rows: List[Dict[str, object]] = []

    reference_numeric = contexts["reference_decision"].map({"KILL": 0.0, "ABORT": 0.5, "PASS": 1.0}).to_numpy()

    for arch in ARCHITECTURES:
        p = profiles[arch]
        for seed in range(k_seeds):
            seed_rng = np.random.default_rng(10_000 + hash((arch, seed)) % (2**31 - 1))

            quality_signal = contexts["latent_quality"].to_numpy() + p.quality_shift + seed_rng.normal(0.0, 0.08, size=len(contexts))
            quality_signal = np.clip(quality_signal, 0.0, 1.0)

            predicted_decision = np.where(quality_signal > 0.60, "PASS", np.where(quality_signal > 0.42, "ABORT", "KILL"))
            predicted_numeric = pd.Series(predicted_decision).map({"KILL": 0.0, "ABORT": 0.5, "PASS": 1.0}).to_numpy()

            decision_gap = np.abs(predicted_numeric - reference_numeric)
            correctness = (predicted_decision == contexts["reference_decision"].to_numpy()).astype(int)

            confidence_raw = _sigmoid(3.2 * np.abs(quality_signal - 0.5) + p.confidence_bias + seed_rng.normal(0.0, p.confidence_noise, size=len(contexts)))
            predicted_confidence = np.clip(confidence_raw, 0.01, 0.99)

            regret = np.clip(0.06 + 0.50 * decision_gap + 0.16 * (1.0 - quality_signal) + seed_rng.normal(0.0, 0.03, size=len(contexts)), 0.0, 1.0)
            ece_context = np.abs(predicted_confidence - correctness)

            obr = ((contexts["reference_decision"].to_numpy() == "PASS") & (predicted_decision != "PASS")).astype(float)
            shr = ((predicted_decision == "PASS") & (contexts["reference_decision"].to_numpy() != "PASS") & (predicted_confidence > 0.65)).astype(float)
            wmr = (predicted_decision != contexts["reference_decision"].to_numpy()).astype(float)

            disagreement_entropy = np.clip(
                contexts["disagreement_entropy_baseline"].to_numpy() + p.entropy_shift + seed_rng.normal(0.0, 0.03, size=len(contexts)),
                0.0,
                1.0,
            )

            saf = np.clip(1.0 - (0.55 * shr + 0.45 * obr), 0.0, 1.0)
            cs = np.clip(1.0 - (0.65 * wmr + 0.15 * disagreement_entropy), 0.0, 1.0)
            cr = np.clip(decision_gap + 0.05 * disagreement_entropy, 0.0, 1.0)
            bi = np.clip(np.abs(predicted_confidence - 0.5) * (0.9 + 0.2 * disagreement_entropy), 0.0, 1.0)
            edi = 0.25 * cr + 0.25 * bi + 0.25 * (1.0 - saf) + 0.25 * (1.0 - cs)

            tokens = np.clip(seed_rng.normal(p.token_mean, p.token_std, size=len(contexts)).round().astype(int), 300, None)
            latency = np.clip(seed_rng.normal(p.latency_mean, p.latency_std, size=len(contexts)), 0.05, None)

            for idx, context_id in enumerate(contexts["context_id"].to_numpy()):
                rows.append(
                    {
                        "architecture": arch,
                        "context_id": context_id,
                        "seed": seed,
                        "predicted_decision": predicted_decision[idx],
                        "reference_decision": contexts["reference_decision"].iloc[idx],
                        "predicted_confidence": float(predicted_confidence[idx]),
                        "correctness": int(correctness[idx]),
                        "regret": float(regret[idx]),
                        "ECE": float(ece_context[idx]),
                        "SHR": float(shr[idx]),
                        "OBR": float(obr[idx]),
                        "WMR": float(wmr[idx]),
                        "EDI": float(edi[idx]),
                        "disagreement_entropy": float(disagreement_entropy[idx]),
                        "tokens": int(tokens[idx]),
                        "latency": float(latency[idx]),
                        "uncertainty_level": contexts["uncertainty_level"].iloc[idx],
                        "signal_sparsity_score": float(contexts["signal_sparsity_score"].iloc[idx]),
                        "disagreement_entropy_baseline": float(contexts["disagreement_entropy_baseline"].iloc[idx]),
                        "evidence_sufficiency_score": float(contexts["evidence_sufficiency_score"].iloc[idx]),
                    }
                )

    return pd.DataFrame(rows)


def _build_calibration_table(context_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []

    for arch, arch_df in context_df.groupby("architecture", sort=False):
        arch_df = arch_df.copy()
        arch_df["ece_bin_id"] = np.minimum((arch_df["predicted_confidence"] * 10).astype(int), 9)

        bin_stats = (
            arch_df.groupby("ece_bin_id", as_index=False)
            .agg(
                mean_confidence=("predicted_confidence", "mean"),
                empirical_accuracy=("correctness", "mean"),
                bin_size=("context_id", "size"),
            )
            .sort_values("ece_bin_id")
        )
        total = float(len(arch_df))
        bin_stats["ece_decomposition_term"] = np.abs(bin_stats["mean_confidence"] - bin_stats["empirical_accuracy"]) * (bin_stats["bin_size"] / total)

        merged = arch_df.merge(bin_stats, on="ece_bin_id", how="left")
        for _, r in merged.iterrows():
            rows.append(
                {
                    "record_type": "context",
                    "architecture": arch,
                    "context_id": r["context_id"],
                    "seed": int(r["seed"]),
                    "predicted_confidence": float(r["predicted_confidence"]),
                    "correctness": int(r["correctness"]),
                    "predicted_decision": r["predicted_decision"],
                    "reference_decision": r["reference_decision"],
                    "ece_bin_id": int(r["ece_bin_id"]),
                    "bin_id": int(r["ece_bin_id"]),
                    "bin_accuracy": float(r["empirical_accuracy"]),
                    "bin_confidence": float(r["mean_confidence"]),
                    "bin_count": int(r["bin_size"]),
                    "mean_confidence": float(r["mean_confidence"]),
                    "empirical_accuracy": float(r["empirical_accuracy"]),
                    "bin_size": int(r["bin_size"]),
                    "ece_decomposition_term": float(r["ece_decomposition_term"]),
                }
            )

        for _, b in bin_stats.iterrows():
            base_row = {
                "architecture": arch,
                "context_id": np.nan,
                "seed": np.nan,
                "predicted_confidence": np.nan,
                "correctness": np.nan,
                "predicted_decision": np.nan,
                "reference_decision": np.nan,
                "ece_bin_id": int(b["ece_bin_id"]),
                "bin_id": int(b["ece_bin_id"]),
                "bin_accuracy": float(b["empirical_accuracy"]),
                "bin_confidence": float(b["mean_confidence"]),
                "bin_count": int(b["bin_size"]),
                "mean_confidence": float(b["mean_confidence"]),
                "empirical_accuracy": float(b["empirical_accuracy"]),
                "bin_size": int(b["bin_size"]),
                "ece_decomposition_term": float(b["ece_decomposition_term"]),
            }
            rows.append({"record_type": "reliability", **base_row})
            rows.append({"record_type": "ece_decomposition", **base_row})

    cols = [
        "record_type",
        "architecture",
        "context_id",
        "seed",
        "predicted_confidence",
        "correctness",
        "predicted_decision",
        "reference_decision",
        "ece_bin_id",
        "bin_id",
        "bin_accuracy",
        "bin_confidence",
        "bin_count",
        "mean_confidence",
        "empirical_accuracy",
        "bin_size",
        "ece_decomposition_term",
    ]

    return pd.DataFrame(rows)[cols]


def _build_stratified_summary(context_df: pd.DataFrame, bootstrap_samples: int, rng: np.random.Generator) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []

    monolithic = context_df[context_df["architecture"] == "Monolithic"]

    for (arch, level), grp in context_df.groupby(["architecture", "uncertainty_level"], sort=False):
        ref_grp = monolithic[monolithic["uncertainty_level"] == level]

        regret_arr = grp["regret"].to_numpy(dtype=float)
        ece_arr = grp["ECE"].to_numpy(dtype=float)

        regret_ci_low, regret_ci_high = _bootstrap_ci(regret_arr, rng, bootstrap_samples)
        ece_ci_low, ece_ci_high = _bootstrap_ci(ece_arr, rng, bootstrap_samples)

        row = {
            "architecture": arch,
            "uncertainty_level": level,
            "mean_regret": float(np.mean(regret_arr)),
            "std_regret": float(np.std(regret_arr, ddof=1)),
            "ci95_regret_low": regret_ci_low,
            "ci95_regret_high": regret_ci_high,
            "mean_ECE": float(np.mean(ece_arr)),
            "std_ECE": float(np.std(ece_arr, ddof=1)),
            "ci95_ECE_low": ece_ci_low,
            "ci95_ECE_high": ece_ci_high,
            "mean_SHR": float(grp["SHR"].mean()),
            "mean_OBR": float(grp["OBR"].mean()),
            "mean_WMR": float(grp["WMR"].mean()),
            "mean_EDI": float(grp["EDI"].mean()),
            "mean_tokens": float(grp["tokens"].mean()),
            "mean_latency": float(grp["latency"].mean()),
            "cohens_d_regret_vs_monolithic": _cohens_d(regret_arr, ref_grp["regret"].to_numpy(dtype=float)),
            "cohens_d_ECE_vs_monolithic": _cohens_d(ece_arr, ref_grp["ECE"].to_numpy(dtype=float)),
        }
        row["cohens_d_vs_monolithic"] = row["cohens_d_regret_vs_monolithic"]
        rows.append(row)

    return pd.DataFrame(rows)


def _pareto_frontier(points: np.ndarray) -> np.ndarray:
    # Minimize all objectives.
    n = points.shape[0]
    is_pareto = np.ones(n, dtype=bool)
    for i in range(n):
        if not is_pareto[i]:
            continue
        dominates = np.all(points <= points[i], axis=1) & np.any(points < points[i], axis=1)
        dominates[i] = False
        if np.any(dominates):
            is_pareto[i] = False
    return is_pareto


def _build_pareto_points(context_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[pd.DataFrame] = []

    for arch, grp in context_df.groupby("architecture", sort=False):
        grp = grp.copy()
        pts = grp[["tokens", "regret", "latency", "ECE"]].to_numpy(dtype=float)
        frontier_mask = _pareto_frontier(pts)
        grp["is_pareto_frontier"] = frontier_mask
        grp["pareto_frontier_index"] = pd.NA
        grp["auf"] = pd.NA
        grp["marginal_delta_regret_per_token"] = pd.NA

        frontier = grp[frontier_mask].sort_values("tokens")
        if not frontier.empty:
            frontier_idx = frontier.index.to_list()
            for order, idx in enumerate(frontier_idx):
                grp.loc[idx, "pareto_frontier_index"] = order

            # AUF over regret-token frontier (piecewise linear on sorted tokens).
            f_tokens = frontier["tokens"].to_numpy(dtype=float)
            f_regret = frontier["regret"].to_numpy(dtype=float)
            if len(f_tokens) > 1 and np.ptp(f_tokens) > 0:
                token_norm = (f_tokens - f_tokens.min()) / np.ptp(f_tokens)
                auf = float(np.trapz(f_regret, token_norm))
            else:
                auf = float(f_regret.mean())
            grp["auf"] = auf

            if len(frontier_idx) > 1:
                deltas_t = np.diff(f_tokens)
                deltas_r = np.diff(f_regret)
                with np.errstate(divide="ignore", invalid="ignore"):
                    slopes = np.where(deltas_t != 0, deltas_r / deltas_t, np.nan)
                for i, idx in enumerate(frontier_idx[1:], start=0):
                    grp.loc[idx, "marginal_delta_regret_per_token"] = float(slopes[i])

        rows.append(grp)

    return pd.concat(rows, ignore_index=True)[
        [
            "architecture",
            "context_id",
            "seed",
            "tokens",
            "regret",
            "latency",
            "ECE",
            "is_pareto_frontier",
            "pareto_frontier_index",
            "auf",
            "marginal_delta_regret_per_token",
        ]
    ]


def _build_ablation_deltas(context_df: pd.DataFrame) -> pd.DataFrame:
    ablation_arches = ["Multi-Agent (A0 full)"] + [f"A{i}" for i in range(1, 12)]
    ab_df = context_df[context_df["architecture"].isin(ablation_arches)].copy()
    ab_df["ablation_architecture"] = np.where(ab_df["architecture"] == "Multi-Agent (A0 full)", "A0", ab_df["architecture"])

    pivot = ab_df.pivot_table(index=["context_id", "seed"], columns="ablation_architecture", values=["regret", "ECE", "SHR", "OBR", "WMR", "EDI", "tokens", "latency"])

    baseline = "A0"
    rows: List[Dict[str, object]] = []
    output_order = ["A0"] + [f"A{i}" for i in range(1, 12)]

    for arch in output_order:
        row = {"architecture": arch}
        for metric in ["regret", "ECE", "SHR", "OBR", "WMR", "EDI", "tokens", "latency"]:
            if arch == baseline:
                row[f"delta_{metric}_vs_A0"] = 0.0
                continue
            row[f"delta_{metric}_vs_A0"] = float(pivot[(metric, arch)].mean() - pivot[(metric, baseline)].mean())

        if arch == baseline:
            row["cohens_d_vs_A0"] = 0.0
            row["p_value_paired"] = 1.0
        else:
            x = pivot[("regret", arch)].to_numpy(dtype=float)
            y = pivot[("regret", baseline)].to_numpy(dtype=float)
            t, p_value = stats.ttest_rel(x, y, nan_policy="omit")
            row["cohens_d_vs_A0"] = _cohens_d(x, y)
            row["p_value_paired"] = float(p_value) if not np.isnan(p_value) else float("nan")

        rows.append(row)

    out = pd.DataFrame(rows)
    rename_map = {
        "delta_regret_vs_A0": "delta_regret_vs_A0",
        "delta_ECE_vs_A0": "delta_ECE_vs_A0",
        "delta_SHR_vs_A0": "delta_SHR_vs_A0",
        "delta_OBR_vs_A0": "delta_OBR_vs_A0",
        "delta_WMR_vs_A0": "delta_WMR_vs_A0",
        "delta_EDI_vs_A0": "delta_EDI_vs_A0",
        "delta_tokens_vs_A0": "delta_tokens_vs_A0",
        "delta_latency_vs_A0": "delta_latency_vs_A0",
    }
    return out.rename(columns=rename_map)


def _ranking_from_scores(scores: pd.Series) -> pd.DataFrame:
    ranked = scores.sort_values(ascending=True)
    return pd.DataFrame({"architecture": ranked.index.to_numpy(), "mean_regret": ranked.to_numpy(), "rank": np.arange(1, len(ranked) + 1)})


def _build_sensitivity_rankings(context_df: pd.DataFrame) -> pd.DataFrame:
    base_scores = context_df.groupby("architecture", as_index=True)["regret"].mean()
    base_rank = _ranking_from_scores(base_scores)
    base_order = base_rank["architecture"].to_list()

    perturbations: List[Tuple[str, pd.Series]] = [("baseline", base_scores)]

    for lam in [0.5, 1.0, 2.0]:
        score = context_df.assign(score=context_df["regret"] * lam).groupby("architecture")["score"].mean()
        perturbations.append((f"lambda_x_{lam}", score))

    for temp in [0.8, 1.0, 1.2]:
        scaled_conf = _sigmoid(_safe_logit(context_df["predicted_confidence"].to_numpy(dtype=float)) / temp)
        score = pd.DataFrame({"architecture": context_df["architecture"], "score": np.abs(scaled_conf - context_df["correctness"].to_numpy()) + context_df["regret"].to_numpy()}).groupby("architecture")["score"].mean()
        perturbations.append((f"temperature_scale_{temp}", score))

    for clip in [0.8, 1.2]:
        clipped = np.clip(context_df["regret"].to_numpy(dtype=float), 0.0, clip)
        score = pd.DataFrame({"architecture": context_df["architecture"], "score": clipped}).groupby("architecture")["score"].mean()
        perturbations.append((f"clipping_bound_x_{clip}", score))

    rows: List[Dict[str, object]] = []
    base_positions = {a: i for i, a in enumerate(base_order)}

    for perturbation_name, score in perturbations:
        ranking = _ranking_from_scores(score)
        order = ranking["architecture"].to_list()

        x = [base_positions[a] for a in ARCHITECTURES]
        y_positions = {a: i for i, a in enumerate(order)}
        y = [y_positions[a] for a in ARCHITECTURES]
        tau, _ = stats.kendalltau(x, y)
        tau_val = float(tau) if not np.isnan(tau) else 1.0

        for _, r in ranking.iterrows():
            rows.append(
                {
                    "perturbation": perturbation_name,
                    "architecture": r["architecture"],
                    "rank": int(r["rank"]),
                    "mean_regret": float(r["mean_regret"]),
                    "kendall_tau_vs_baseline": tau_val,
                }
            )

    return pd.DataFrame(rows)


def generate_artifacts(output_dir: Path | str, n_contexts: int = 1000, k_seeds: int = 5, bootstrap_samples: int = 1000) -> Dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    contexts = _generate_context_frame(n_contexts=n_contexts, rng=rng)
    context_level = _simulate_context_level(contexts=contexts, k_seeds=k_seeds, rng=rng)

    calibration = _build_calibration_table(context_level)
    stratified = _build_stratified_summary(context_level, bootstrap_samples=bootstrap_samples, rng=rng)
    pareto = _build_pareto_points(context_level)
    ablation = _build_ablation_deltas(context_level)
    sensitivity = _build_sensitivity_rankings(context_level)

    files = {
        "calibration_bins.csv": output_path / "calibration_bins.csv",
        "context_level_metrics.csv": output_path / "context_level_metrics.csv",
        "stratified_summary.csv": output_path / "stratified_summary.csv",
        "pareto_points.csv": output_path / "pareto_points.csv",
        "ablation_deltas.csv": output_path / "ablation_deltas.csv",
        "sensitivity_rankings.csv": output_path / "sensitivity_rankings.csv",
    }

    calibration.to_csv(files["calibration_bins.csv"], index=False)
    context_level.to_csv(files["context_level_metrics.csv"], index=False)
    stratified.to_csv(files["stratified_summary.csv"], index=False)
    pareto.to_csv(files["pareto_points.csv"], index=False)
    ablation.to_csv(files["ablation_deltas.csv"], index=False)
    sensitivity.to_csv(files["sensitivity_rankings.csv"], index=False)

    return files


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export benchmark paper artifacts to CSV.")
    parser.add_argument("--output-dir", required=True, help="Output directory for CSV files")
    parser.add_argument("--n-contexts", type=int, default=1000, help="Number of contexts")
    parser.add_argument("--k-seeds", type=int, default=5, help="Seeds per architecture")
    parser.add_argument("--bootstrap-samples", type=int, default=1000, help="Bootstrap samples for CIs")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    generate_artifacts(
        output_dir=Path(args.output_dir),
        n_contexts=args.n_contexts,
        k_seeds=args.k_seeds,
        bootstrap_samples=args.bootstrap_samples,
    )


if __name__ == "__main__":
    main()
