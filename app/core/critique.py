from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.core.config import Settings, get_settings
from app.core.llm import LLMClient, check_ollama
from app.core.run_manager import RunManager


@dataclass
class CritiqueResult:
    run_id: str
    run_dir: Path
    verdict: str
    json_path: Path
    markdown_path: Path
    summary: str
    payload: Dict[str, Any]


class CritiqueException(Exception):
    pass


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as exc:
        logger.warning("Failed to read %s: %s", path, exc)
        return ""


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to parse JSON from %s: %s", path, exc)
        return {}


def _collect_directory_text(path: Path) -> str:
    if not path.exists():
        return ""
    snippets: List[str] = []
    for child in sorted(path.glob("*.md")):
        snippet = _read_text(child)
        if snippet:
            snippets.append(f"{child.name}: {snippet.splitlines()[0][:200]}")
    if not snippets:
        contents = "\n".join(str(child) for child in sorted(path.iterdir()))
        return contents[:400]
    return "\n".join(snippets)


def _split_json_and_markdown(raw: str) -> Tuple[str, str]:
    marker = "\n---\n"
    json_part = raw
    markdown = ""
    if "JSON:" in raw:
        json_part = raw.split("JSON:", 1)[1]
    if marker in json_part:
        json_str, markdown = json_part.split(marker, 1)
    else:
        json_str = json_part
    return json_str.strip(), markdown.strip()


def _build_context_snippets(run_dir: Path) -> Dict[str, str]:
    snippets: Dict[str, str] = {}
    candidates = [
        ("market_report.md", run_dir / "market_report.md"),
        ("prd.md", run_dir / "prd.md"),
        ("tech_spec.md", run_dir / "tech_spec.md"),
        ("decision.md", run_dir / "decision.md"),
    ]
    for label, path in candidates:
        text = _read_text(path)
        if text:
            snippets[label] = text
    landing_text = _collect_directory_text(run_dir / "landing_page")
    if landing_text:
        snippets["landing_page"] = landing_text
    content_text = _collect_directory_text(run_dir / "content_pack")
    if content_text:
        snippets["content_pack"] = content_text
    competitor = _read_json(run_dir / "competitor_analysis.json")
    if competitor:
        snippets["competitor_analysis.json"] = json.dumps(competitor, indent=2)
    confidence = _read_json(run_dir / "confidence.json")
    if confidence:
        snippets["confidence.json"] = json.dumps(confidence, indent=2)
    return snippets


def _build_prompt(
    run_id: str,
    mode: str,
    context: Dict[str, str],
    confidence_score: int,
    evidence_notes: List[str],
) -> str:
    lines = [
        "You are the Devil's Advocate for an internal Asmblr run. You only rely on the provided evidences.",
        f"Run ID: {run_id}",
        f"Mode: {mode}",
        f"Confidence score: {confidence_score}",
        "",
        "Context sections:",
    ]
    for label, text in context.items():
        snippet = text.splitlines()[0][:400]
        lines.append(f"- {label}: {snippet}")
    if not context:
        lines.append("- (no content available)")
    lines.append("")
    lines.append("Instructions:")
    lines.append(
        "Produce a strict JSON object first under the literal tag 'JSON:' with the following keys: "
        "verdict (GO|ITERATE|KILL), top_risks (list of {type,severity,evidence,how_to_test_fast}), "
        "contradictions (list), missing_data (list), one killer experiment ({hypothesis,method,success_metric,stop_metric})."
    )
    lines.append("Each evidence field must cite the file name or directory used above.")
    lines.append("After the JSON, add a separator line '---' and then craft a Markdown critique referencing as many cited files as possible.")
    if evidence_notes:
        lines.append("")
        lines.append("Note additional evidence:")
        lines.extend(f"- {note}" for note in evidence_notes)
    prompt = "\n".join(lines) + "\nJSON:"
    return prompt


def _enforce_caps(
    payload: Dict[str, Any],
    confidence_score: int,
    context: Dict[str, str],
) -> Tuple[Dict[str, Any], List[str]]:
    caps: List[str] = []
    if confidence_score < 50:
        caps.append(f"Confidence {confidence_score} < 50 forces non-GO verdict")
        if payload.get("verdict") == "GO":
            payload["verdict"] = "ITERATE"
    if "competitor_analysis.json" not in context:
        caps.append("Missing competitor_analysis.json evidence")
        payload.setdefault("missing_data", []).append("competitor_analysis.json absent")
    prd_text = context.get("prd.md", "").lower()
    tech_text = context.get("tech_spec.md", "").lower()
    if "fallback" in prd_text or "fallback" in tech_text:
        caps.append("PRD/Tech spec fallback content flagged as invalid")
        payload.setdefault("missing_data", []).append("fallback placeholder in PRD/tech spec")
        if payload.get("verdict") == "GO":
            payload["verdict"] = "KILL"
    return payload, caps


def run_devils_advocate(settings: Settings, run_id: str, mode: str = "standard") -> CritiqueResult:
    run_manager = RunManager(settings.runs_dir, settings.data_dir)
    run = run_manager.get_run(run_id)
    if not run:
        raise CritiqueException(f"Run {run_id} not found")
    if run.get("status") != "completed":
        raise CritiqueException("Critique requires a completed run")
    run_dir = Path(run["output_dir"])
    if not run_dir.exists():
        raise CritiqueException(f"Run directory {run_dir} missing")

    check_ollama(settings.ollama_base_url, [settings.general_model, settings.code_model])
    llm = LLMClient(settings.ollama_base_url, settings.general_model)
    if not llm.available():
        raise CritiqueException("LLM unavailable for critique")

    confidence_data = _read_json(run_dir / "confidence.json")
    confidence_score = confidence_data.get("score", 0)
    context = _build_context_snippets(run_dir)
    evidence_notes: List[str] = []
    if (run_dir / "landing_page").exists():
        evidence_notes.append("Landing page directory present")
    if (run_dir / "content_pack").exists():
        evidence_notes.append("Content pack directory present")

    prompt = _build_prompt(run_id, mode, context, confidence_score, evidence_notes)
    raw = llm.generate(prompt)
    json_str, markdown = _split_json_and_markdown(raw)
    try:
        payload = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise CritiqueException(f"LLM returned invalid JSON: {exc}")

    payload["verdict"] = payload.get("verdict", "ITERATE").upper()
    payload, caps = _enforce_caps(payload, confidence_score, context)

    json_path = run_dir / "devils_advocate.json"
    md_path = run_dir / "devils_advocate.md"
    md_lines = [
        f"# Devil's Advocate ({mode})",
        f"- Run: {run_id}",
        f"- Verdict: {payload['verdict']}",
        f"- Confidence score: {confidence_score}",
        "",
        "## Evidence snippets",
    ]
    for label, text in context.items():
        snippet = text.splitlines()[0][:200]
        md_lines.append(f"- `{label}`: {snippet}")
    if evidence_notes:
        md_lines.append("")
        md_lines.append("## Supplemental evidence")
        md_lines.extend(f"- {note}" for note in evidence_notes)
    if markdown:
        md_lines.append("")
        md_lines.append("## LLM critique summary")
        md_lines.append(markdown)
    if caps:
        md_lines.append("")
        md_lines.append("## Caps & penalties")
        md_lines.extend(f"- {cap}" for cap in caps)
    md_lines.append("")
    md_lines.append("## JSON payload")
    md_lines.append("```json")
    md_lines.append(json.dumps(payload, indent=2))
    md_lines.append("```")
    md_content = "\n".join(md_lines)
    md_path.write_text(md_content, encoding="utf-8")

    payload_with_meta = {
        "run_id": run_id,
        "mode": mode,
        "confidence_score": confidence_score,
        "verdict": payload["verdict"],
        "payload": payload,
        "caps": caps,
    }
    json_path.write_text(json.dumps(payload_with_meta, indent=2), encoding="utf-8")

    return CritiqueResult(
        run_id=run_id,
        run_dir=run_dir,
        verdict=payload["verdict"],
        json_path=json_path,
        markdown_path=md_path,
        summary=markdown or "No markdown summary provided",
        payload=payload_with_meta,
    )
