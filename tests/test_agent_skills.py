from types import SimpleNamespace

from app.agents.skills import build_agent_skill_guidance


def _mk_settings(tmp_path, role_map: str, max_chars: int = 2200):
    return SimpleNamespace(
        enable_agent_skills=True,
        agent_skills_dirs=str(tmp_path / "skills"),
        agent_skill_prompt_max_chars=max_chars,
        agent_skill_role_map=role_map,
    )


def test_build_agent_skill_guidance_loads_skill_md(tmp_path):
    skill_dir = tmp_path / "skills" / "startup-analyst"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: startup-analyst
description: Analyze startup opportunities quickly.
---
# Startup Analyst

- Validate market pain with concrete evidence.
- Prioritize opportunities by urgency and frequency.
- Document assumptions before scoring.
""",
        encoding="utf-8",
    )

    settings = _mk_settings(tmp_path, "researcher=startup-analyst")
    guidance = build_agent_skill_guidance("Researcher", settings)

    assert "SKILL GUIDANCE" in guidance
    assert "startup-analyst" in guidance
    assert "Analyze startup opportunities quickly." in guidance
    assert "Validate market pain with concrete evidence." in guidance


def test_build_agent_skill_guidance_respects_max_chars(tmp_path):
    skill_dir = tmp_path / "skills" / "prompt-engineering"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: prompt-engineering
description: Improve prompt structure and reliability.
---
- Use structured sections for role, context, and constraints.
- Add explicit output formats and validation checks.
- Request assumptions and confidence for ambiguous inputs.
""",
        encoding="utf-8",
    )

    settings = _mk_settings(tmp_path, "product=prompt-engineering", max_chars=120)
    guidance = build_agent_skill_guidance("Product", settings)

    assert len(guidance) <= 120
    assert guidance.endswith("...")


def test_build_agent_skill_guidance_empty_when_missing_skill(tmp_path):
    settings = _mk_settings(tmp_path, "brand=unknown-skill")
    guidance = build_agent_skill_guidance("Brand", settings)
    assert guidance == ""
