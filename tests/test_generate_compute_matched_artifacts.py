from pathlib import Path

import pandas as pd

from scripts.generate_compute_matched_artifacts import generate_compute_matched_artifacts


def test_generate_compute_matched_artifacts_outputs_required_files(tmp_path: Path) -> None:
    out_dir = tmp_path / "compute_matched"
    zip_path = tmp_path / "paper_artifacts_compute_matched.zip"

    files = generate_compute_matched_artifacts(
        output_dir=out_dir,
        zip_path=zip_path,
        n_contexts=80,
        k_seeds=3,
        bootstrap_samples=200,
    )

    expected = {
        "compute_matched_runs",
        "compute_matched_summary",
        "noise_sweep_points",
        "mechanism_isolation",
        "signature_table",
        "signature_delta_regret_fig",
        "signature_noise_regret_fig",
        "signature_noise_ece_fig",
        "pareto_tokens_regret_fig",
        "pareto_latency_ece_fig",
        "mechanism_isolation_fig",
        "run_manifest",
        "readme",
        "zip",
    }
    assert expected.issubset(set(files.keys()))
    assert zip_path.exists()


def test_compute_matched_schema_and_required_systems(tmp_path: Path) -> None:
    out_dir = tmp_path / "compute_matched"
    files = generate_compute_matched_artifacts(
        output_dir=out_dir,
        zip_path=tmp_path / "paper_artifacts_compute_matched.zip",
        n_contexts=60,
        k_seeds=2,
        bootstrap_samples=100,
    )

    runs = pd.read_csv(files["compute_matched_runs"])
    required_columns = {
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
    }
    assert required_columns.issubset(set(runs.columns))

    required_systems = {
        "Monolithic",
        "Sequential",
        "Debate-2Agent",
        "Reflexion",
        "ToT-SelfConsistency",
        "A5-no-critique",
        "A6-critique-nonbinding",
        "C1-binding-critique",
    }
    assert required_systems.issubset(set(runs["system_id"].unique()))
    assert set(runs["budget_tokens"].unique()) == {1500, 2500, 3500, 4500}


def test_noise_and_mechanism_outputs_have_required_columns(tmp_path: Path) -> None:
    out_dir = tmp_path / "compute_matched"
    files = generate_compute_matched_artifacts(
        output_dir=out_dir,
        zip_path=tmp_path / "paper_artifacts_compute_matched.zip",
        n_contexts=90,
        k_seeds=2,
        bootstrap_samples=100,
    )

    noise = pd.read_csv(files["noise_sweep_points"])
    assert {
        "context_id",
        "system_id",
        "seed",
        "eta",
        "regret",
        "ece",
        "edi",
        "hcr_false",
        "hcr_true_out_of_bundle",
        "hcr_alias",
        "contradiction_rate",
        "citation_fidelity",
    }.issubset(set(noise.columns))
    assert set(noise["eta"].unique()) == {0, 1, 2, 3}

    mechanism = pd.read_csv(files["mechanism_isolation"])
    assert {
        "system_id",
        "budget_tokens",
        "delta_regret_vs_M0",
        "delta_ece_vs_M0",
        "delta_edi_vs_M0",
        "delta_disagreement_entropy_vs_M0",
        "delta_contradiction_rate_vs_M0",
        "delta_hcr_false_vs_M0",
        "delta_hcr_true_out_of_bundle_vs_M0",
        "delta_hcr_alias_vs_M0",
        "ci95_delta_regret_low",
        "ci95_delta_regret_high",
    }.issubset(set(mechanism.columns))
from pathlib import Path

import json

from scripts.generate_compute_matched_artifacts import generate_compute_matched_artifacts


def test_run_manifest_records_actual_run_configuration(tmp_path: Path) -> None:
    out_dir = tmp_path / "compute_matched"
    zip_path = tmp_path / "paper_artifacts_compute_matched.zip"

    files = generate_compute_matched_artifacts(
        output_dir=out_dir,
        zip_path=zip_path,
        n_contexts=40,
        k_seeds=2,
        bootstrap_samples=123,
        signature_budget=2500,
        mechanism_budget=3500,
    )

    manifest = json.loads(Path(files["run_manifest"]).read_text(encoding="utf-8"))
    assert manifest["bootstrap_samples"] == 123
    assert manifest["decision_model"] == "llama3:8b"
    assert manifest["retrieval_setting"] in {"bundle-only", "no-retrieval"}
