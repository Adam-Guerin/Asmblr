from pathlib import Path

import pandas as pd

from scripts.build_paper_artifacts import build_paper_artifacts


def test_build_paper_artifacts_generates_required_structure(tmp_path: Path) -> None:
    out_dir = tmp_path / "paper_artifacts"
    build_paper_artifacts(output_dir=out_dir, quick=True, max_traces=5)

    required_dirs = [
        "configs",
        "prompts",
        "data_stats",
        "tables",
        "figures",
        "traces",
        "scripts",
    ]
    for rel in required_dirs:
        assert (out_dir / rel).is_dir(), f"missing directory: {rel}"

    required_files = [
        "README.md",
        "configs/run_spec.yaml",
        "data_stats/dataset_summary.csv",
        "data_stats/annotation_agreement.csv",
        "tables/main_results_context_level.csv",
        "tables/risk_coverage_points.csv",
        "tables/ablation_deltas_full.csv",
        "tables/sensitivity_rankings.csv",
        "figures/reliability_main_architectures.png",
        "figures/risk_coverage_regret.png",
        "figures/sensitivity_tau.png",
        "traces/anonymized_traces.jsonl",
        "scripts/build_paper_artifacts.py",
    ]
    for rel in required_files:
        assert (out_dir / rel).exists(), f"missing file: {rel}"

    risk_cov = pd.read_csv(out_dir / "tables" / "risk_coverage_points.csv")
    assert {"architecture", "coverage", "risk_regret", "conditional_ece"}.issubset(set(risk_cov.columns))

    hcr = pd.read_csv(out_dir / "tables" / "hcr_taxonomy.csv")
    assert {"architecture", "uncertainty_level", "shr_rate", "obr_rate", "wmr_rate"}.issubset(set(hcr.columns))
