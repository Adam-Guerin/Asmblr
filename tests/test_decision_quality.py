import json
from pathlib import Path

from app.cli import run_golden_topic
from app.core.config import Settings
from app.core.models import SeedInputs, Idea, IdeaScore
from app.core.pipeline import VenturePipeline
from app.signal_engine import SignalEngineResult

DEFAULT_PAGE = [
    {
        "url": "https://example.com/report",
        "text": "Operations teams struggle to prioritize suppliers when market noise spikes in Q1.",
    }
]


def _prepare_settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"
    settings.min_pages = 0
    settings.min_pains = 0
    settings.min_competitors = 0
    settings.min_avg_text_len = 0
    settings.min_unique_domains = 0
    settings.signal_quality_threshold = 0
    return settings


def _patch_common(monkeypatch, page_payload):
    monkeypatch.setattr("app.core.pipeline.check_ollama", lambda *args, **kwargs: {"models": [{"name": "llama"}]})
    monkeypatch.setattr("app.core.pipeline.LLMClient.available", lambda self: True)
    monkeypatch.setattr("app.core.pipeline.LLMClient.generate", lambda self, prompt: "ok")
    monkeypatch.setattr("app.core.pipeline.LLMClient.generate_json", lambda self, prompt: {"ok": True})

    def fake_web_run(self, *args, **kwargs):
        return json.dumps(page_payload)

    monkeypatch.setattr("app.langchain_tools.WebSearchAndSummarizeTool._run", fake_web_run)

    def fake_signal_run(self, sources):
        page = {
            "url": "https://example.com/pain",
            "title": "Signal Page",
            "source_name": sources[0]["name"] if sources else "signal",
            "text": "Operations teams struggle to coordinate compliance during audits.",
            "pass_type": "recent",
            "published_at": None,
            "upvotes": None,
            "comments_count": None,
            "signal_score": 12,
            "fingerprint": 1234,
        }
        group = {"group_id": 1, "fingerprint": 1234, "canonical": page, "duplicates": []}
        return SignalEngineResult(raw_pages=[page], deduped_pages=[page], groups=[group])

    monkeypatch.setattr("app.core.pipeline.SignalEngine.run", fake_signal_run)


def _fake_crewai_success(repo_dir, landing_dir, content_dir, idea_payload=None):
    default = {
        "name": "Signal Ops",
        "one_liner": "Automate launch signals.",
        "target_user": "Operators",
        "problem": "Operators struggle to keep launch artifacts in sync.",
        "solution": "SignalOps hub",
        "key_features": ["signals", "automations"],
        "pain_ids": ["pain_1"],
        "sources": ["https://example.com/report"],
        "hypotheses": ["Seed pain verified"],
    }
    idea_payload = idea_payload or default
    score_entry = {"name": idea_payload["name"], "score": 75, "rationale": "validated", "risks": [], "signals": {}}
    return {
        "research": {"pain_statements": ["Teams struggle to coordinate launches."], "pages": DEFAULT_PAGE},
        "analysis": {
            "ideas": [idea_payload],
            "scores": [score_entry],
            "top_idea": {"name": idea_payload["name"], "score": 75, "rationale": "validated"},
            "competitors": [],
        },
        "product": {"prd_markdown": "# PRD"},
        "tech": {"tech_spec_markdown": "# Tech Spec", "repo_dir": str(repo_dir)},
        "growth": {"landing_dir": str(landing_dir), "content_dir": str(content_dir)},
    }


def test_seed_inputs_tagged(tmp_path, monkeypatch):
    settings = _prepare_settings(tmp_path)
    settings.market_signal_threshold = 0
    _patch_common(monkeypatch, DEFAULT_PAGE)

    repo_dir = tmp_path / "stub_repo"
    landing_dir = tmp_path / "stub_landing"
    content_dir = tmp_path / "stub_content"
    repo_dir.mkdir(parents=True)
    landing_dir.mkdir(parents=True)
    content_dir.mkdir(parents=True)

    def fake_crewai(topic, settings_, llm, run_id, n_ideas, fast_mode, **kwargs):
        return _fake_crewai_success(repo_dir, landing_dir, content_dir)

    monkeypatch.setattr("app.core.pipeline.run_crewai_pipeline", fake_crewai)

    pipeline = VenturePipeline(settings)
    seeds = SeedInputs(
        icp="SMB founders",
        pains=["Need better compliance tools"],
        competitors=["Competitor A"],
        context="Contextual note",
    )
    result = pipeline.run("test-topic", n_ideas=1, fast_mode=True, seed_inputs=seeds)
    run_dir = settings.runs_dir / result.run_id
    seed_context = json.loads((run_dir / "seed_context.json").read_text())
    assert seed_context["data_source"] == "seed"
    assert seed_context["icp"] == "SMB founders"

    data_source = json.loads((run_dir / "data_source.json").read_text())
    assert data_source["critical"]["seeds"] == "seed"


def test_market_signal_score_blocks_low_signal(tmp_path, monkeypatch):
    settings = _prepare_settings(tmp_path)
    settings.market_signal_threshold = 90
    _patch_common(monkeypatch, DEFAULT_PAGE)

    repo_dir = tmp_path / "stub_repo"
    landing_dir = tmp_path / "stub_landing"
    content_dir = tmp_path / "stub_content"
    repo_dir.mkdir(parents=True)
    landing_dir.mkdir(parents=True)
    content_dir.mkdir(parents=True)

    def fake_crewai(topic, settings_, llm, run_id, n_ideas, fast_mode, **kwargs):
        return _fake_crewai_success(repo_dir, landing_dir, content_dir)

    monkeypatch.setattr("app.core.pipeline.run_crewai_pipeline", fake_crewai)

    pipeline = VenturePipeline(settings)
    result = pipeline.run("low-signal", n_ideas=1, fast_mode=True)
    run_dir = settings.runs_dir / result.run_id
    score = json.loads((run_dir / "market_signal_score.json").read_text())
    assert score["score"] < settings.market_signal_threshold
    decision = (run_dir / "decision.md").read_text()
    assert "ABORT" in decision


def test_pain_validation_rejects_generic(tmp_path):
    settings = _prepare_settings(tmp_path)
    pipeline = VenturePipeline(settings)
    generic_pains = [
        "We want to save time.",
        "We want to increase productivity.",
    ]
    validated = pipeline._validate_pains(generic_pains)
    assert validated["validated"] == []
    assert all("generic" in entry["reason"] for entry in validated["rejected"])


def test_idea_actionability_scores_specific_higher_than_generic(tmp_path):
    settings = _prepare_settings(tmp_path)
    pipeline = VenturePipeline(settings)
    specific = Idea(
        name="Founder Interview Sprint",
        one_liner="Run a 7-day founder outreach sprint with a waitlist landing page.",
        target_user="B2B SaaS founders with 2-10 employees",
        problem="Founders struggle to validate positioning before building.",
        solution="Generate outreach copy, launch landing page, and track interview-to-signup conversion.",
        key_features=["linkedin outreach", "waitlist landing", "interview tracker"],
    )
    generic = Idea(
        name="Productivity Booster",
        one_liner="Save time and improve efficiency for everyone.",
        target_user="unknown",
        problem="Teams are not productive.",
        solution="All-in-one AI workflow.",
        key_features=["automation"],
    )
    specific_score = pipeline._score_idea_actionability(specific)
    generic_score = pipeline._score_idea_actionability(generic)
    assert specific_score["score"] > generic_score["score"]


def test_actionability_adjusts_scores_and_marks_blocked(tmp_path):
    settings = _prepare_settings(tmp_path)
    settings.idea_actionability_min_score = 60
    settings.idea_actionability_adjustment_max = 12
    pipeline = VenturePipeline(settings)
    ideas = [
        Idea(
            name="Specific",
            one_liner="Validate with 7-day waitlist test.",
            target_user="B2B SaaS founders",
            problem="Founders cannot prioritize which pain to validate first.",
            solution="Launch interview + waitlist workflow in one week.",
            key_features=["waitlist", "interviews", "outreach"],
        ),
        Idea(
            name="Generic",
            one_liner="Improve efficiency for teams.",
            target_user="unknown",
            problem="Productivity is low.",
            solution="All-in-one AI tool.",
            key_features=["automation"],
        ),
    ]
    scores = [
        IdeaScore(name="Specific", score=70, rationale="base", risks=[], signals={}),
        IdeaScore(name="Generic", score=70, rationale="base", risks=[], signals={}),
    ]
    adjusted, report = pipeline._apply_actionability_to_scores(scores, ideas)
    specific = next(item for item in adjusted if item.name == "Specific")
    generic = next(item for item in adjusted if item.name == "Generic")
    assert specific.score > generic.score
    assert "Generic" in report["blocked"]
    assert "actionability" in generic.signals


def test_idea_traceability_required(tmp_path, monkeypatch):
    settings = _prepare_settings(tmp_path)
    settings.market_signal_threshold = 0
    _patch_common(monkeypatch, DEFAULT_PAGE)

    repo_dir = tmp_path / "stub_repo"
    landing_dir = tmp_path / "stub_landing"
    content_dir = tmp_path / "stub_content"
    repo_dir.mkdir(parents=True)
    landing_dir.mkdir(parents=True)
    content_dir.mkdir(parents=True)

    idea = {
        "name": "Signal Ops",
        "one_liner": "",
        "target_user": "",
        "problem": "",
        "solution": "",
        "key_features": [],
    }

    def fake_crewai(topic, settings_, llm, run_id, n_ideas, fast_mode, **kwargs):
        data = _fake_crewai_success(repo_dir, landing_dir, content_dir, idea_payload=idea)
        data["analysis"]["scores"] = [{"name": idea["name"], "score": 30, "rationale": "low", "risks": [], "signals": {}}]
        return data

    monkeypatch.setattr("app.core.pipeline.run_crewai_pipeline", fake_crewai)

    pipeline = VenturePipeline(settings)
    result = pipeline.run("trace", n_ideas=1, fast_mode=True)
    run_path = settings.runs_dir / result.run_id
    assert (run_path / "abort_reason.md").exists()
    decision = (run_path / "decision.md").read_text()
    assert "traceability" in decision.lower()


def test_decision_file_written(tmp_path, monkeypatch):
    settings = _prepare_settings(tmp_path)
    settings.market_signal_threshold = 0
    _patch_common(monkeypatch, DEFAULT_PAGE)

    repo_dir = tmp_path / "stub_repo"
    landing_dir = tmp_path / "stub_landing"
    content_dir = tmp_path / "stub_content"
    repo_dir.mkdir(parents=True)
    landing_dir.mkdir(parents=True)
    content_dir.mkdir(parents=True)

    monkeypatch.setattr("app.core.pipeline.run_crewai_pipeline", lambda *args, **kwargs: _fake_crewai_success(repo_dir, landing_dir, content_dir))

    pipeline = VenturePipeline(settings)
    result = pipeline.run("decision", n_ideas=1, fast_mode=True)
    decision = (settings.runs_dir / result.run_id / "decision.md").read_text()
    assert "Status: PASS" in decision
    assert "market_signal" in decision


def test_theme_is_applied_before_scraping(tmp_path, monkeypatch):
    settings = _prepare_settings(tmp_path)
    settings.market_signal_threshold = 0
    settings.enable_progressive_cycles = False
    settings.enable_distribution = False
    _patch_common(monkeypatch, DEFAULT_PAGE)

    repo_dir = tmp_path / "stub_repo_theme"
    landing_dir = tmp_path / "stub_landing_theme"
    content_dir = tmp_path / "stub_content_theme"
    repo_dir.mkdir(parents=True)
    landing_dir.mkdir(parents=True)
    content_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "app.core.pipeline.run_crewai_pipeline",
        lambda *args, **kwargs: _fake_crewai_success(repo_dir, landing_dir, content_dir),
    )

    captured = {"topic": None}
    class CaptureSignalEngine:
        def __init__(self, settings, output_dir, topic, fast_mode=False):
            captured["topic"] = topic

        def run(self, sources):
            page = {
                "url": "https://example.com/pain",
                "title": "Signal Page",
                "source_name": sources[0]["name"] if sources else "signal",
                "text": "Operations teams struggle to coordinate compliance during audits.",
                "pass_type": "recent",
                "published_at": None,
                "upvotes": None,
                "comments_count": None,
                "signal_score": 12,
                "fingerprint": 1234,
            }
            group = {"group_id": 1, "fingerprint": 1234, "canonical": page, "duplicates": []}
            return SignalEngineResult(raw_pages=[page], deduped_pages=[page], groups=[group])

    monkeypatch.setattr("app.core.pipeline.SignalEngine", CaptureSignalEngine)

    pipeline = VenturePipeline(settings)
    seeds = SeedInputs(theme="fintech compliance")
    result = pipeline.run("assistant", n_ideas=1, fast_mode=True, seed_inputs=seeds)
    run_dir = settings.runs_dir / result.run_id

    assert captured["topic"] == "assistant fintech compliance"
    assert (run_dir / "theme_scope.md").exists()
    scope = (run_dir / "theme_scope.md").read_text(encoding="utf-8")
    assert "Applied to scraping query: assistant fintech compliance" in scope


def test_kill_path_triggers_on_low_confidence(tmp_path, monkeypatch):
    settings = _prepare_settings(tmp_path)
    settings.market_signal_threshold = 0
    settings.kill_threshold = 55
    _patch_common(monkeypatch, DEFAULT_PAGE)

    repo_dir = tmp_path / "stub_repo"
    landing_dir = tmp_path / "stub_landing"
    content_dir = tmp_path / "stub_content"
    repo_dir.mkdir(parents=True)
    landing_dir.mkdir(parents=True)
    content_dir.mkdir(parents=True)

    def fake_crewai(topic, settings_, llm, run_id, n_ideas, fast_mode, **kwargs):
        return _fake_crewai_success(repo_dir, landing_dir, content_dir)

    monkeypatch.setattr("app.core.pipeline.run_crewai_pipeline", fake_crewai)
    monkeypatch.setattr(
        "app.core.pipeline.compute_pre_artifact_confidence",
        lambda run_dir, settings=None: {"score": 30, "breakdown": {}, "reasons": []},
    )

    seeds = SeedInputs(icp="Operators")
    pipeline = VenturePipeline(settings)
    result = pipeline.run("kill-topic", n_ideas=1, fast_mode=True, seed_inputs=seeds)
    run_path = settings.runs_dir / result.run_id
    run_info = pipeline.manager.get_run(result.run_id)
    assert run_info["status"] == "killed"
    assert (run_path / "kill_reason.md").exists()
    assert not (run_path / "prd.md").exists()
    assert not (run_path / "content_pack").exists()
    assert not (run_path / "landing_page").exists()
    decision = (run_path / "decision.md").read_text()
    assert "Status: KILL" in decision


def test_golden_run_copies_artifacts(tmp_path, monkeypatch):
    settings = _prepare_settings(tmp_path)
    settings.market_signal_threshold = 0
    _patch_common(monkeypatch, DEFAULT_PAGE)

    repo_dir = tmp_path / "stub_repo"
    landing_dir = tmp_path / "stub_landing"
    content_dir = tmp_path / "stub_content"
    repo_dir.mkdir(parents=True)
    landing_dir.mkdir(parents=True)
    content_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "app.core.pipeline.run_crewai_pipeline",
        lambda *args, **kwargs: _fake_crewai_success(repo_dir, landing_dir, content_dir),
    )

    golden_dir = run_golden_topic("golden-topic", settings)
    assert golden_dir is not None
    assert (golden_dir / "decision.md").exists()
    latest = settings.runs_dir / "_golden" / "latest.json"
    metadata = json.loads(latest.read_text())
    assert metadata["run_id"] in golden_dir.name
    assert (settings.runs_dir / "_golden").exists()


def test_golden_not_created_on_abort(tmp_path, monkeypatch):
    settings = _prepare_settings(tmp_path)
    settings.market_signal_threshold = 100
    _patch_common(monkeypatch, DEFAULT_PAGE)

    repo_dir = tmp_path / "stub_repo"
    landing_dir = tmp_path / "stub_landing"
    content_dir = tmp_path / "stub_content"
    repo_dir.mkdir(parents=True)
    landing_dir.mkdir(parents=True)
    content_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "app.core.pipeline.run_crewai_pipeline",
        lambda *args, **kwargs: _fake_crewai_success(repo_dir, landing_dir, content_dir),
    )

    golden_dir = run_golden_topic("golden-abort", settings)
    assert golden_dir is None
    assert not (settings.runs_dir / "_golden").exists()
