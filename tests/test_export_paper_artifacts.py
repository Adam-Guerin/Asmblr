import pandas as pd
from pathlib import Path

from export_paper_artifacts import generate_artifacts


EXPECTED_FILES = [
    "calibration_bins.csv",
    "context_level_metrics.csv",
    "stratified_summary.csv",
    "pareto_points.csv",
    "ablation_deltas.csv",
    "sensitivity_rankings.csv",
]


def test_generate_artifacts_outputs_files_and_core_columns(tmp_path: Path):
    out_dir = tmp_path / "paper_artifacts"
    generate_artifacts(output_dir=out_dir, n_contexts=30, k_seeds=2, bootstrap_samples=100)

    for file_name in EXPECTED_FILES:
        assert (out_dir / file_name).exists(), f"Missing {file_name}"

    calibration = pd.read_csv(out_dir / "calibration_bins.csv")
    context_metrics = pd.read_csv(out_dir / "context_level_metrics.csv")
    stratified = pd.read_csv(out_dir / "stratified_summary.csv")
    pareto = pd.read_csv(out_dir / "pareto_points.csv")
    ablation = pd.read_csv(out_dir / "ablation_deltas.csv")
    sensitivity = pd.read_csv(out_dir / "sensitivity_rankings.csv")

    assert {
        "architecture",
        "context_id",
        "seed",
        "predicted_confidence",
        "correctness",
        "predicted_decision",
        "reference_decision",
        "ece_bin_id",
        "bin_accuracy",
        "bin_confidence",
        "bin_count",
    }.issubset(set(calibration.columns))

    assert {
        "architecture",
        "context_id",
        "seed",
        "regret",
        "ECE",
        "SHR",
        "OBR",
        "WMR",
        "EDI",
        "disagreement_entropy",
        "tokens",
        "latency",
        "uncertainty_level",
        "signal_sparsity_score",
        "disagreement_entropy_baseline",
        "evidence_sufficiency_score",
    }.issubset(set(context_metrics.columns))

    assert {
        "architecture",
        "uncertainty_level",
        "mean_regret",
        "std_regret",
        "ci95_regret_low",
        "ci95_regret_high",
        "cohens_d_regret_vs_monolithic",
    }.issubset(set(stratified.columns))

    assert {
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
    }.issubset(set(pareto.columns))

    assert {
        "architecture",
        "delta_regret_vs_A0",
        "delta_ECE_vs_A0",
        "delta_SHR_vs_A0",
        "delta_OBR_vs_A0",
        "delta_WMR_vs_A0",
        "delta_EDI_vs_A0",
        "delta_tokens_vs_A0",
        "delta_latency_vs_A0",
        "cohens_d_vs_A0",
        "p_value_paired",
    }.issubset(set(ablation.columns))

    assert {
        "perturbation",
        "architecture",
        "rank",
        "mean_regret",
        "kendall_tau_vs_baseline",
    }.issubset(set(sensitivity.columns))


def test_architecture_coverage_and_expected_row_count(tmp_path: Path):
    out_dir = tmp_path / "paper_artifacts"
    n_contexts = 20
    k_seeds = 3
    generate_artifacts(output_dir=out_dir, n_contexts=n_contexts, k_seeds=k_seeds, bootstrap_samples=50)

    context_metrics = pd.read_csv(out_dir / "context_level_metrics.csv")

    expected_architectures = {
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
    }

    assert set(context_metrics["architecture"].unique()) == expected_architectures
    assert len(context_metrics) == len(expected_architectures) * n_contexts * k_seeds
