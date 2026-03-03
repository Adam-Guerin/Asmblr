#!/usr/bin/env python3
"""Build reproducible paper artifacts from repository data."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

MAIN_ARCHITECTURES = [
    "Monolithic",
    "Sequential",
    "RAG-Monolithic",
    "Reflexion",
    "Debate",
    "Multi-Agent (A0 full)",
]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _dataset_hash(dataset_files: list[Path]) -> str:
    h = hashlib.sha256()
    for path in sorted(dataset_files):
        h.update(path.name.encode("utf-8"))
        h.update(_hash_file(path).encode("utf-8"))
    return h.hexdigest()


def _safe_git_commit_for_file(path: Path, repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "log", "-n", "1", "--pretty=format:%H", "--", str(path)],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or "unknown"
    except Exception:
        return "unknown"


def _bootstrap_ci(values: np.ndarray, samples: int = 800, seed: int = 42) -> tuple[float, float]:
    if values.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    n = values.size
    means = np.empty(samples, dtype=float)
    for i in range(samples):
        means[i] = float(np.mean(rng.choice(values, size=n, replace=True)))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def _fleiss_kappa(counts: np.ndarray) -> float:
    if counts.size == 0:
        return float("nan")
    n_items, _ = counts.shape
    n_raters = int(np.sum(counts[0])) if n_items > 0 else 0
    if n_items == 0 or n_raters <= 1:
        return float("nan")
    p_j = np.sum(counts, axis=0) / (n_items * n_raters)
    p_i = (np.sum(counts * counts, axis=1) - n_raters) / (n_raters * (n_raters - 1))
    p_bar = float(np.mean(p_i))
    p_e = float(np.sum(p_j * p_j))
    return float((p_bar - p_e) / (1.0 - p_e)) if (1.0 - p_e) > 0 else float("nan")


def _holm(pvals: pd.Series) -> pd.Series:
    valid = pvals.dropna().sort_values()
    m = len(valid)
    out = pd.Series(np.nan, index=pvals.index, dtype=float)
    prev = 0.0
    for i, (idx, p) in enumerate(valid.items(), start=1):
        adj = min(1.0, (m - i + 1) * p)
        adj = max(adj, prev)
        out.loc[idx] = adj
        prev = adj
    return out


def _pareto_mask(points: np.ndarray) -> np.ndarray:
    n = points.shape[0]
    mask = np.ones(n, dtype=bool)
    for i in range(n):
        if not mask[i]:
            continue
        dominates = np.all(points <= points[i], axis=1) & np.any(points < points[i], axis=1)
        dominates[i] = False
        if np.any(dominates):
            mask[i] = False
    return mask


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _safe_logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _mask_sensitive_text(text: str) -> str:
    text = re.sub(r"https?://[^\s\)]+", "[URL_REDACTED]", text)
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL_REDACTED]", text)
    return text


def _load_context_dataset(dataset_dir: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(dataset_dir.glob("context_*.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        text = obj.get("raw_text", "") or ""
        pains = obj.get("extracted_pains", []) or []
        comps = obj.get("extracted_competitors", []) or []
        evidence = len(pains) + len(comps)
        variety = len(set([p.lower() for p in pains] + [c.lower() for c in comps]))
        signal_sparsity = 1.0 - min(len(text) / 1000.0, 1.0)
        evidence_sufficiency = min(evidence / 10.0, 1.0)
        disagreement = 1.0 - min(variety / 5.0, 1.0)
        uncertainty = (signal_sparsity + (1.0 - evidence_sufficiency) + disagreement) / 3.0
        level = "low" if uncertainty < 0.33 else ("medium" if uncertainty < 0.67 else "high")
        geo = obj.get("geographic_cluster", "global")
        country = {"north_america": "USA/Canada", "europe": "Europe", "asia_pacific": "APAC", "global": "Global"}.get(geo, geo)
        platform = (obj.get("metadata") or {}).get("platform", "unknown")
        rows.append(
            {
                "context_id": obj.get("id"),
                "industry": obj.get("industry_tag", "unknown"),
                "domain": urlparse(obj.get("source_url", "")).netloc or "unknown",
                "country_bucket": country,
                "uncertainty_level": level,
                "tokens": len(text.split()),
                "bundle_sources": 1,
                "bundle_claims": evidence,
                "is_synthetic": platform == "synthetic_realistic",
                "platform": platform,
                "raw_text": text,
                "timestamp": obj.get("timestamp"),
                "source_url": obj.get("source_url", ""),
                "pains": pains,
                "competitors": comps,
            }
        )
    return pd.DataFrame(rows)


def _seed_avg(cm: pd.DataFrame) -> pd.DataFrame:
    cm = cm.copy()
    cm["non_abort"] = (cm["predicted_decision"] != "ABORT").astype(float)
    return cm.groupby(["architecture", "context_id", "uncertainty_level"], as_index=False).agg(
        regret=("regret", "mean"),
        ECE=("ECE", "mean"),
        SHR=("SHR", "mean"),
        OBR=("OBR", "mean"),
        WMR=("WMR", "mean"),
        EDI=("EDI", "mean"),
        tokens=("tokens", "mean"),
        latency=("latency", "mean"),
        confidence_mean=("predicted_confidence", "mean"),
        non_abort_rate=("non_abort", "mean"),
    )

def _build_run_spec(repo_root: Path, out_path: Path) -> None:
    runs_dir = repo_root / "runs"
    completed = []
    for run_dir in sorted([p for p in runs_dir.iterdir() if p.is_dir()]):
        state_path = run_dir / "run_state.json"
        if not state_path.exists():
            continue
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if state.get("status") == "completed":
            completed.append(run_dir)
    models, budgets = [], []
    for run_dir in completed:
        sel = run_dir / "llm_model_selection.json"
        rb = run_dir / "run_budget.json"
        if sel.exists():
            models.append(json.loads(sel.read_text(encoding="utf-8")))
        if rb.exists():
            budgets.append(json.loads(rb.read_text(encoding="utf-8")))
    g_models = sorted({m.get("general_model", "unknown") for m in models})
    c_models = sorted({m.get("code_model", "unknown") for m in models})
    dataset_files = sorted((repo_root / "benchmark" / "dataset").glob("context_*.json"))
    run_budget = budgets[0] if budgets else {}
    lines = [
        "unit_of_analysis: context_level_seed_averaged_per_context",
        f"generated_at_utc: '{datetime.now(timezone.utc).isoformat()}'",
        f"completed_runs_count: {len(completed)}",
        f"models_general: {g_models}",
        f"models_code: {c_models}",
        "decoding:",
        "  temperature: 0.3",
        "  top_p: null",
        "  max_tokens: null",
        "  frequency_penalty: null",
        "  presence_penalty: null",
        "budgets:",
        f"  profile: '{run_budget.get('profile', 'quick')}'",
        f"  time_budget_sec: {((run_budget.get('budget') or {}).get('time_budget_sec', 720))}",
        f"  token_budget_est: {((run_budget.get('budget') or {}).get('token_budget_est', 18000))}",
        "timeouts:",
        "  request_timeout_sec: 20",
        "  mvp_install_timeout_sec: 600",
        "  mvp_build_timeout_sec: 300",
        "  mvp_test_timeout_sec: 300",
        "seeds:",
        "  benchmark_default_seed: 42",
        "  python_random: random.seed(seed)",
        "  numpy: numpy.random.seed(seed)",
        "  torch: torch.manual_seed(seed)",
        f"dataset_n_contexts: {len(dataset_files)}",
        f"dataset_version_hash_sha256: '{_dataset_hash(dataset_files)}'",
        f"scoring_version_hash_sha256: '{_hash_file(repo_root / 'export_paper_artifacts.py') if (repo_root / 'export_paper_artifacts.py').exists() else 'unknown'}'",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _collect_prompts(repo_root: Path, prompts_dir: Path) -> None:
    rows = []
    role_map = {
        "idea_generation.txt": "Research",
        "competitor_analysis.txt": "Analyst",
        "llm_judge_scoring.txt": "Calibrator",
        "prd_writer.txt": "Aggregator",
        "tech_spec_writer.txt": "Aggregator",
    }
    for src in sorted((repo_root / "app" / "prompts").rglob("*.txt")):
        rel = src.relative_to(repo_root)
        dst = prompts_dir / rel
        _ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        rows.append(
            {
                "role": role_map.get(src.name, "PipelinePrompt"),
                "prompt_file": str(rel).replace("\\", "/"),
                "sha256": _hash_file(src),
                "git_last_commit": _safe_git_commit_for_file(src, repo_root),
            }
        )
    critique = repo_root / "app" / "core" / "critique.py"
    if critique.exists():
        dst = prompts_dir / "extracted" / "devils_advocate_prompt_template.py"
        _ensure_dir(dst.parent)
        shutil.copy2(critique, dst)
        rows.append(
            {
                "role": "Devil",
                "prompt_file": "app/core/critique.py",
                "sha256": _hash_file(critique),
                "git_last_commit": _safe_git_commit_for_file(critique, repo_root),
            }
        )
    for src in sorted((repo_root / "benchmark" / "baselines").glob("*.py")):
        if src.name.startswith("__"):
            continue
        dst = prompts_dir / "baselines" / src.name
        _ensure_dir(dst.parent)
        shutil.copy2(src, dst)
        rows.append(
            {
                "role": "BaselineLogic",
                "prompt_file": str(src.relative_to(repo_root)).replace("\\", "/"),
                "sha256": _hash_file(src),
                "git_last_commit": _safe_git_commit_for_file(src, repo_root),
            }
        )
    pd.DataFrame(rows).sort_values(["role", "prompt_file"]).to_csv(prompts_dir / "prompt_manifest.csv", index=False)


def _build_data_stats(dataset_df: pd.DataFrame, cm: pd.DataFrame, out_dir: Path) -> None:
    rows = []
    for col in ["industry", "domain", "country_bucket", "uncertainty_level"]:
        for key, val in dataset_df[col].value_counts(dropna=False).items():
            rows.append({"metric_group": f"counts_by_{col}", "metric": str(key), "value": int(val)})
    rows.extend(
        [
            {"metric_group": "bundle_stats", "metric": "bundle_sources_mean", "value": float(dataset_df["bundle_sources"].mean())},
            {"metric_group": "bundle_stats", "metric": "bundle_tokens_mean", "value": float(dataset_df["tokens"].mean())},
            {"metric_group": "bundle_stats", "metric": "bundle_claims_mean", "value": float(dataset_df["bundle_claims"].mean())},
            {"metric_group": "bundle_stats", "metric": "pct_real", "value": float((1 - dataset_df["is_synthetic"].mean()) * 100)},
            {"metric_group": "bundle_stats", "metric": "pct_synthetic", "value": float(dataset_df["is_synthetic"].mean() * 100)},
            {"metric_group": "synthetic_generation_rules", "metric": "rule_1", "value": "Synthetic if metadata.platform == synthetic_realistic."},
            {"metric_group": "synthetic_generation_rules", "metric": "rule_2", "value": "Synthetic templates generated in benchmark/large_scale_validation.py."},
        ]
    )
    pd.DataFrame(rows).to_csv(out_dir / "dataset_summary.csv", index=False)

    agreement = []
    decision_map = {"KILL": 0, "ABORT": 1, "PASS": 2}
    for arch in MAIN_ARCHITECTURES:
        adf = cm[cm["architecture"] == arch]
        mats, ents = [], []
        for _, grp in adf.groupby("context_id"):
            votes = grp["predicted_decision"].map(decision_map).dropna().astype(int)
            if votes.empty:
                continue
            bc = np.bincount(votes.to_numpy(), minlength=3)
            mats.append(bc)
            p = bc / max(np.sum(bc), 1)
            ents.append(-float(np.sum([pi * math.log(pi + 1e-12, 2) for pi in p])))
        agreement.append(
            {
                "label_family": "decision_distribution",
                "architecture": arch,
                "agreement_metric": "fleiss_kappa",
                "agreement_value": _fleiss_kappa(np.array(mats, dtype=float)) if mats else np.nan,
                "disagreement_mean_entropy_bits": float(np.mean(ents)) if ents else np.nan,
                "handling_policy": "kept_as_soft_labels_across_seeds",
                "notes": "seed votes used as proxy raters",
            }
        )
    agreement.append(
        {
            "label_family": "descriptive_labels",
            "architecture": "all",
            "agreement_metric": "not_available",
            "agreement_value": np.nan,
            "disagreement_mean_entropy_bits": np.nan,
            "handling_policy": "not_computable_from_current_repo",
            "notes": "no multi-annotator files found",
        }
    )
    pd.DataFrame(agreement).to_csv(out_dir / "annotation_agreement.csv", index=False)

    for level in ["low", "high"]:
        ex = dataset_df[dataset_df["uncertainty_level"] == level].head(3)
        data = ex[["context_id", "industry", "domain", "country_bucket", "raw_text", "pains", "competitors", "source_url", "timestamp"]].to_dict(orient="records")
        (out_dir / f"examples_{level}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    adv = dataset_df[(dataset_df["uncertainty_level"] == "high") & (dataset_df["bundle_claims"] <= 1)].head(3)
    if adv.empty:
        adv = dataset_df.sort_values(["bundle_claims", "tokens"]).head(3)
    data = adv[["context_id", "industry", "domain", "country_bucket", "raw_text", "pains", "competitors", "source_url", "timestamp"]].to_dict(orient="records")
    (out_dir / "examples_adversarial.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _build_results_tables(seed_ctx: pd.DataFrame, out_dir: Path) -> None:
    overall_rows = []
    for arch, grp in seed_ctx.groupby("architecture"):
        row = {"architecture": arch}
        for metric in ["regret", "ECE", "SHR", "OBR", "WMR", "EDI", "tokens", "latency"]:
            arr = grp[metric].to_numpy(dtype=float)
            lo, hi = _bootstrap_ci(arr)
            row[f"mean_{metric}"] = float(np.mean(arr))
            row[f"ci95_{metric}_low"] = lo
            row[f"ci95_{metric}_high"] = hi
        overall_rows.append(row)
    overall = pd.DataFrame(overall_rows).sort_values("architecture")
    overall.to_csv(out_dir / "main_results_context_level.csv", index=False)
    (out_dir / "main_results_context_level.tex").write_text(overall.to_latex(index=False), encoding="utf-8")

    strat_rows = []
    for (arch, lvl), grp in seed_ctx.groupby(["architecture", "uncertainty_level"]):
        row = {"architecture": arch, "uncertainty_level": lvl}
        for metric in ["regret", "ECE", "SHR", "OBR", "WMR", "EDI"]:
            arr = grp[metric].to_numpy(dtype=float)
            lo, hi = _bootstrap_ci(arr)
            row[f"mean_{metric}"] = float(np.mean(arr))
            row[f"ci95_{metric}_low"] = lo
            row[f"ci95_{metric}_high"] = hi
        strat_rows.append(row)
    strat = pd.DataFrame(strat_rows).sort_values(["architecture", "uncertainty_level"])
    strat.to_csv(out_dir / "uncertainty_stratified_context_level.csv", index=False)
    (out_dir / "uncertainty_stratified_context_level.tex").write_text(strat.to_latex(index=False), encoding="utf-8")

def _build_reliability(cm: pd.DataFrame, figures_dir: Path, tables_dir: Path) -> None:
    rows = []
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharex=True, sharey=True)
    for idx, arch in enumerate(MAIN_ARCHITECTURES):
        ax = axes.flat[idx]
        adf = cm[cm["architecture"] == arch].copy()
        adf["bin"] = np.minimum((adf["predicted_confidence"] * 10).astype(int), 9)
        bdf = adf.groupby("bin", as_index=False).agg(mean_confidence=("predicted_confidence", "mean"), empirical_accuracy=("correctness", "mean"), n=("context_id", "size")).sort_values("bin")
        for _, r in bdf.iterrows():
            rows.append({"architecture": arch, "bin": int(r["bin"]), "mean_confidence": float(r["mean_confidence"]), "empirical_accuracy": float(r["empirical_accuracy"]), "count": int(r["n"])})
        ax.plot([0, 1], [0, 1], "k--", linewidth=1)
        ax.plot(bdf["mean_confidence"], bdf["empirical_accuracy"], marker="o")
        ax.set_title(arch)
        ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(figures_dir / "reliability_main_architectures.png", dpi=300)
    plt.savefig(figures_dir / "reliability_main_architectures.pdf")
    plt.close(fig)
    pd.DataFrame(rows).to_csv(tables_dir / "reliability_bins.csv", index=False)


def _build_distribution_figures(cm: pd.DataFrame, figures_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    data = [cm[cm["architecture"] == a]["regret"].to_numpy() for a in MAIN_ARCHITECTURES]
    ax.boxplot(data, labels=MAIN_ARCHITECTURES, showfliers=False)
    ax.tick_params(axis="x", rotation=20)
    ax.set_title("Regret Distributions by Architecture")
    plt.tight_layout()
    plt.savefig(figures_dir / "regret_distributions.png", dpi=300)
    plt.savefig(figures_dir / "regret_distributions.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for a in MAIN_ARCHITECTURES:
        ax.hist(cm[cm["architecture"] == a]["ECE"].to_numpy(), bins=30, alpha=0.35, density=True, label=a)
    ax.legend(fontsize=8, ncol=2)
    ax.set_title("ECE Histogram by Architecture")
    plt.tight_layout()
    plt.savefig(figures_dir / "ece_histogram_distributions.png", dpi=300)
    plt.savefig(figures_dir / "ece_histogram_distributions.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for a in MAIN_ARCHITECTURES:
        adf = cm[cm["architecture"] == a].copy()
        adf["bin"] = np.minimum((adf["predicted_confidence"] * 10).astype(int), 9)
        b = adf.groupby("bin", as_index=False).agg(conf=("predicted_confidence", "mean"), corr=("correctness", "mean"))
        ax.plot(b["conf"], b["corr"], marker="o", label=a)
    ax.plot([0, 1], [0, 1], "k--", linewidth=1)
    ax.legend(fontsize=8, ncol=2)
    ax.set_title("Confidence vs Correctness (Binned)")
    plt.tight_layout()
    plt.savefig(figures_dir / "confidence_vs_correctness_binned.png", dpi=300)
    plt.savefig(figures_dir / "confidence_vs_correctness_binned.pdf")
    plt.close(fig)


def _build_pareto(seed_ctx: pd.DataFrame, tables_dir: Path, figures_dir: Path) -> None:
    means = seed_ctx.groupby("architecture", as_index=False).agg(tokens=("tokens", "mean"), regret=("regret", "mean"), latency=("latency", "mean"), ECE=("ECE", "mean"))
    means["pareto_tokens_regret"] = _pareto_mask(means[["tokens", "regret"]].to_numpy(dtype=float))
    means["pareto_latency_ece"] = _pareto_mask(means[["latency", "ECE"]].to_numpy(dtype=float))
    means.to_csv(tables_dir / "pareto_points.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    axes[0].scatter(means["tokens"], means["regret"], c=np.where(means["pareto_tokens_regret"], "tab:red", "tab:blue"))
    for _, r in means.iterrows():
        axes[0].annotate(r["architecture"], (r["tokens"], r["regret"]), fontsize=7)
    axes[0].set_title("Pareto: Tokens -> Regret")
    axes[1].scatter(means["latency"], means["ECE"], c=np.where(means["pareto_latency_ece"], "tab:red", "tab:blue"))
    for _, r in means.iterrows():
        axes[1].annotate(r["architecture"], (r["latency"], r["ECE"]), fontsize=7)
    axes[1].set_title("Pareto: Latency -> ECE")
    plt.tight_layout()
    plt.savefig(figures_dir / "pareto_frontiers.png", dpi=300)
    plt.savefig(figures_dir / "pareto_frontiers.pdf")
    plt.close(fig)


def _build_risk_coverage(seed_ctx: pd.DataFrame, tables_dir: Path, figures_dir: Path) -> None:
    thresholds = np.linspace(0.0, 0.95, 20)
    rows = []
    for level, sdf in [("all", seed_ctx), ("high", seed_ctx[seed_ctx["uncertainty_level"] == "high"])]:
        for arch, adf in sdf.groupby("architecture"):
            covered = adf[adf["non_abort_rate"] > 0.5]
            rows.append({"architecture": arch, "uncertainty_level": level, "selection_rule": "non_abort_only", "threshold": 0.0, "coverage": len(covered) / len(adf) if len(adf) else 0.0, "risk_regret": float(covered["regret"].mean()) if len(covered) else np.nan, "conditional_ece": float(covered["ECE"].mean()) if len(covered) else np.nan})
            for t in thresholds:
                cov = adf[(adf["non_abort_rate"] > 0.5) & (adf["confidence_mean"] >= t)]
                rows.append({"architecture": arch, "uncertainty_level": level, "selection_rule": "confidence_and_non_abort", "threshold": float(t), "coverage": len(cov) / len(adf) if len(adf) else 0.0, "risk_regret": float(cov["regret"].mean()) if len(cov) else np.nan, "conditional_ece": float(cov["ECE"].mean()) if len(cov) else np.nan})
    rc = pd.DataFrame(rows)
    rc.to_csv(tables_dir / "risk_coverage_points.csv", index=False)
    line = rc[rc["selection_rule"] == "confidence_and_non_abort"]

    fig, ax = plt.subplots(figsize=(10, 6))
    for arch in MAIN_ARCHITECTURES:
        d = line[(line["architecture"] == arch) & (line["uncertainty_level"] == "all")].sort_values("coverage")
        if not d.empty:
            ax.plot(d["coverage"], d["risk_regret"], label=arch)
    ax.legend(fontsize=8, ncol=2)
    ax.set_title("Risk-Coverage (Regret)")
    plt.tight_layout()
    plt.savefig(figures_dir / "risk_coverage_regret.png", dpi=300)
    plt.savefig(figures_dir / "risk_coverage_regret.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    for arch in MAIN_ARCHITECTURES:
        d = line[(line["architecture"] == arch) & (line["uncertainty_level"] == "all")].sort_values("coverage")
        if not d.empty:
            ax.plot(d["coverage"], d["conditional_ece"], label=arch)
    ax.legend(fontsize=8, ncol=2)
    ax.set_title("Risk-Coverage (ECE)")
    plt.tight_layout()
    plt.savefig(figures_dir / "risk_coverage_ece.png", dpi=300)
    plt.savefig(figures_dir / "risk_coverage_ece.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    for arch in MAIN_ARCHITECTURES:
        d = line[(line["architecture"] == arch) & (line["uncertainty_level"] == "high")].sort_values("coverage")
        if not d.empty:
            ax.plot(d["coverage"], d["risk_regret"], label=arch)
    ax.legend(fontsize=8, ncol=2)
    ax.set_title("Risk-Coverage (Regret, High Uncertainty)")
    plt.tight_layout()
    plt.savefig(figures_dir / "risk_coverage_regret_high.png", dpi=300)
    plt.savefig(figures_dir / "risk_coverage_regret_high.pdf")
    plt.close(fig)


def _build_ablations(seed_ctx: pd.DataFrame, tables_dir: Path) -> None:
    tmp = seed_ctx.copy()
    tmp["ab"] = np.where(tmp["architecture"] == "Multi-Agent (A0 full)", "A0", tmp["architecture"])
    tmp = tmp[tmp["ab"].isin(["A0"] + [f"A{i}" for i in range(1, 12)])]
    base = tmp[tmp["ab"] == "A0"].set_index("context_id")
    rows = []
    for name in ["A0"] + [f"A{i}" for i in range(1, 12)]:
        row = {"architecture": name}
        if name == "A0":
            for m in ["regret", "ECE", "SHR", "OBR", "WMR", "EDI", "tokens", "latency"]:
                row[f"delta_{m}_vs_A0"] = 0.0
            row["p_regret"] = 1.0
            row["p_ECE"] = 1.0
            rows.append(row)
            continue
        cur = tmp[tmp["ab"] == name].set_index("context_id")
        common = sorted(set(base.index).intersection(set(cur.index)))
        if not common:
            continue
        b, c = base.loc[common], cur.loc[common]
        for m in ["regret", "ECE", "SHR", "OBR", "WMR", "EDI", "tokens", "latency"]:
            row[f"delta_{m}_vs_A0"] = float(c[m].mean() - b[m].mean())
        row["p_regret"] = float(stats.ttest_rel(c["regret"], b["regret"], nan_policy="omit").pvalue)
        row["p_ECE"] = float(stats.ttest_rel(c["ECE"], b["ECE"], nan_policy="omit").pvalue)
        rows.append(row)
    out = pd.DataFrame(rows)
    out["p_regret_holm"] = _holm(out["p_regret"])
    out["p_ECE_holm"] = _holm(out["p_ECE"])
    out.to_csv(tables_dir / "ablation_deltas_full.csv", index=False)
    (tables_dir / "ablation_deltas_full.tex").write_text(out.to_latex(index=False), encoding="utf-8")


def _build_hcr_taxonomy(cm: pd.DataFrame, tables_dir: Path) -> None:
    rows = []
    for level, df in [("all", cm), ("low", cm[cm["uncertainty_level"] == "low"]), ("medium", cm[cm["uncertainty_level"] == "medium"]), ("high", cm[cm["uncertainty_level"] == "high"])]:
        for arch, grp in df.groupby("architecture"):
            rows.append({"architecture": arch, "uncertainty_level": level, "n": len(grp), "shr_count": float(grp["SHR"].sum()), "obr_count": float(grp["OBR"].sum()), "wmr_count": float(grp["WMR"].sum()), "shr_rate": float(grp["SHR"].mean()), "obr_rate": float(grp["OBR"].mean()), "wmr_rate": float(grp["WMR"].mean())})
    pd.DataFrame(rows).sort_values(["architecture", "uncertainty_level"]).to_csv(tables_dir / "hcr_taxonomy.csv", index=False)


def _build_sensitivity(cm: pd.DataFrame, tables_dir: Path, figures_dir: Path) -> None:
    base = cm.groupby("architecture", as_index=True)["regret"].mean().sort_values()
    base_order = list(base.index)
    base_pos = {a: i for i, a in enumerate(base_order)}
    rows, tau_rows = [], []
    perturb = [("baseline", 1.0, 1.0, 1.0)]
    for lam in [0.5, 1.0, 2.0]:
        for clip in [0.8, 1.0, 1.2]:
            for temp in [0.8, 1.0, 1.2, 1.5]:
                perturb.append((f"lambda_{lam}_clip_{clip}_temp_{temp}", lam, clip, temp))
    for name, lam, clip, temp in perturb:
        reg = np.clip(cm["regret"].to_numpy(dtype=float), 0.0, clip)
        conf = cm["predicted_confidence"].to_numpy(dtype=float)
        corr = cm["correctness"].to_numpy(dtype=float)
        score = reg + lam * np.abs(_sigmoid(_safe_logit(conf) / temp) - corr)
        rank = pd.DataFrame({"architecture": cm["architecture"], "score": score}).groupby("architecture", as_index=True)["score"].mean().sort_values()
        order = list(rank.index)
        y = [order.index(a) for a in base_order]
        x = [base_pos[a] for a in base_order]
        tau, _ = stats.kendalltau(x, y)
        tau = float(1.0 if np.isnan(tau) else tau)
        tau_rows.append({"perturbation": name, "kendall_tau": tau, "lambda": lam, "clip": clip, "temp": temp})
        for idx, arch in enumerate(order, start=1):
            rows.append({"perturbation": name, "architecture": arch, "rank": idx, "mean_score": float(rank.loc[arch]), "kendall_tau_vs_baseline": tau, "lambda": lam, "clipping_bound": clip, "p_hat_temperature": temp})
    out = pd.DataFrame(rows)
    out.to_csv(tables_dir / "sensitivity_rankings.csv", index=False)
    tau_df = pd.DataFrame(tau_rows).sort_values("kendall_tau", ascending=False)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(range(len(tau_df)), tau_df["kendall_tau"])
    ax.set_xticks(range(len(tau_df)))
    ax.set_xticklabels(tau_df["perturbation"], rotation=90, fontsize=7)
    ax.set_title("Ranking Stability Under Sensitivity Sweeps")
    plt.tight_layout()
    plt.savefig(figures_dir / "sensitivity_tau.png", dpi=300)
    plt.savefig(figures_dir / "sensitivity_tau.pdf")
    plt.close(fig)


def _build_traces(repo_root: Path, traces_dir: Path, max_traces: int) -> int:
    completed = []
    for run_dir in sorted([p for p in (repo_root / "runs").iterdir() if p.is_dir()]):
        s = run_dir / "run_state.json"
        if not s.exists():
            continue
        try:
            state = json.loads(s.read_text(encoding="utf-8"))
        except Exception:
            continue
        if state.get("status") == "completed":
            completed.append((run_dir, state))
    lines = []
    for run_dir, state in completed[:max_traces]:
        crew = json.loads((run_dir / "crew_outputs.json").read_text(encoding="utf-8")) if (run_dir / "crew_outputs.json").exists() else {}
        pages = json.loads((run_dir / "raw_pages.json").read_text(encoding="utf-8")) if (run_dir / "raw_pages.json").exists() else {"pages": []}
        conf = json.loads((run_dir / "confidence.json").read_text(encoding="utf-8")) if (run_dir / "confidence.json").exists() else {}
        decision_txt = (run_dir / "decision.md").read_text(encoding="utf-8") if (run_dir / "decision.md").exists() else ""
        status = re.search(r"- Status:\s*([A-Z]+)", decision_txt)
        decision = status.group(1) if status else "ABORT"
        dd = {"PASS": 0.0, "ABORT": 0.0, "KILL": 0.0}
        if decision in dd:
            dd[decision] = 1.0
        provenance = []
        for p in (pages.get("pages") or [])[:10]:
            u = p.get("url") or ""
            provenance.append({"source_id": hashlib.sha1(u.encode("utf-8")).hexdigest()[:12], "source_name": p.get("source_name"), "published_at": p.get("published_at"), "url_anonymized": "[URL_REDACTED]" if u else ""})
        msg = {
            "Research": _mask_sensitive_text(json.dumps(crew.get("research", {}), ensure_ascii=False)[:1500]),
            "Analyst": _mask_sensitive_text(json.dumps(crew.get("analysis", {}), ensure_ascii=False)[:1500]),
            "Devil": {"present": False, "note": "No explicit role log found."},
            "Calibrator": {"present": False, "note": "No explicit role log found."},
            "Aggregator": _mask_sensitive_text(json.dumps({"product": crew.get("product", {}), "tech": crew.get("tech", {}), "growth": crew.get("growth", {})}, ensure_ascii=False)[:1500]),
        }
        rec = {"trace_id": run_dir.name, "run_id": run_dir.name, "topic": ((state.get("params") or {}).get("topic")), "execution_profile": ((state.get("params") or {}).get("execution_profile")), "provenance": provenance, "messages": msg, "final_decision_distribution": dd, "confidence_score_0_100": conf.get("score"), "case_note": "success_case" if decision == "PASS" else "failure_or_borderline_case"}
        lines.append(json.dumps(rec, ensure_ascii=False))
    (traces_dir / "anonymized_traces.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def _write_readme(out_root: Path, env: dict[str, Any], traces_count: int) -> None:
    text = f"""# Paper Artifacts

Generated by `scripts/build_paper_artifacts.py` from repository data.

## Reproduction
```bash
{sys.executable} scripts/build_paper_artifacts.py --output-dir paper_artifacts
```

## Notes
- Unit of analysis: context-level seed-averaged per context.
- Missing descriptive multi-annotator labels are documented in `data_stats/annotation_agreement.csv`.
- Devil/Calibrator traces are not explicitly logged in current run artifacts; placeholders are included.

## Environment
- Python: `{env.get('python', 'unknown')}`
- Platform: `{env.get('platform', 'unknown')}`
- Git commit: `{env.get('git_commit', 'unknown')}`
- Trace count: `{traces_count}`
"""
    (out_root / "README.md").write_text(text, encoding="utf-8")


def build_paper_artifacts(output_dir: Path | str, quick: bool = False, max_traces: int = 8) -> dict[str, Path]:
    repo_root = Path(__file__).resolve().parents[1]
    out_root = Path(output_dir)
    dirs = {"root": out_root, "configs": out_root / "configs", "prompts": out_root / "prompts", "data_stats": out_root / "data_stats", "tables": out_root / "tables", "figures": out_root / "figures", "traces": out_root / "traces", "scripts": out_root / "scripts"}
    for d in dirs.values():
        _ensure_dir(d)
    cm = pd.read_csv(repo_root / "context_level_metrics.csv")
    if quick:
        cm = cm.head(min(len(cm), 12000)).copy()
    dataset_df = _load_context_dataset(repo_root / "benchmark" / "dataset")
    seed_ctx = _seed_avg(cm)

    _build_run_spec(repo_root, dirs["configs"] / "run_spec.yaml")
    _collect_prompts(repo_root, dirs["prompts"])
    _build_data_stats(dataset_df, cm, dirs["data_stats"])
    _build_results_tables(seed_ctx, dirs["tables"])
    _build_reliability(cm, dirs["figures"], dirs["tables"])
    _build_distribution_figures(cm, dirs["figures"])
    _build_pareto(seed_ctx, dirs["tables"], dirs["figures"])
    _build_risk_coverage(seed_ctx, dirs["tables"], dirs["figures"])
    _build_ablations(seed_ctx, dirs["tables"])
    _build_hcr_taxonomy(cm, dirs["tables"])
    _build_sensitivity(cm, dirs["tables"], dirs["figures"])
    traces_count = _build_traces(repo_root, dirs["traces"], max_traces=max_traces)

    env = {"python": sys.version.replace("\n", " "), "platform": sys.platform, "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    try:
        env["git_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception:
        env["git_commit"] = "unknown"
    (dirs["configs"] / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    shutil.copy2(Path(__file__), dirs["scripts"] / Path(__file__).name)
    _write_readme(out_root, env, traces_count)
    return dirs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build paper artifacts package.")
    parser.add_argument("--output-dir", default="paper_artifacts")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--max-traces", type=int, default=8)
    args = parser.parse_args()
    build_paper_artifacts(Path(args.output_dir), quick=args.quick, max_traces=args.max_traces)


if __name__ == "__main__":
    main()
