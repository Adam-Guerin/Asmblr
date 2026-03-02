from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class SkillSpec:
    name: str
    description: str
    instructions: list[str]
    source_path: Path


def _normalize_name(value: str) -> str:
    return (value or "").strip().lower().replace("_", "-")


def _extract_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    raw_meta = parts[1]
    body = parts[2].strip()
    metadata: dict[str, str] = {}
    for line in raw_meta.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip().strip("'\"")
    return metadata, body


def _extract_instruction_lines(body: str, max_lines: int = 6) -> list[str]:
    lines: list[str] = []
    in_code_block = False
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not line:
            continue
        if line.startswith("#"):
            continue
        line = re.sub(r"^[\-\*\u2022]\s+", "", line)
        line = re.sub(r"^\d+\.\s+", "", line)
        if len(line) < 20:
            continue
        lines.append(line)
        if len(lines) >= max_lines:
            break
    return lines


def _parse_skill_file(skill_md_path: Path) -> SkillSpec | None:
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.debug("Unable to read skill file {path}: {err}", path=str(skill_md_path), err=exc)
        return None
    metadata, body = _extract_frontmatter(content)
    default_name = skill_md_path.parent.name
    name = metadata.get("name") or default_name
    description = metadata.get("description") or "No description provided."
    instructions = _extract_instruction_lines(body)
    return SkillSpec(
        name=name,
        description=description,
        instructions=instructions,
        source_path=skill_md_path,
    )


def _resolve_skill_dirs(settings: Any) -> list[Path]:
    raw_dirs = getattr(settings, "agent_skills_dirs", "") or ""
    base_dir = Path(__file__).resolve().parents[2]
    resolved: list[Path] = []
    for chunk in raw_dirs.split(","):
        token = chunk.strip()
        if not token:
            continue
        path = Path(token).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        resolved.append(path)
    return resolved


def _load_skill_catalog(settings: Any) -> dict[str, SkillSpec]:
    catalog: dict[str, SkillSpec] = {}
    for root in _resolve_skill_dirs(settings):
        if not root.exists():
            continue
        for skill_md_path in root.rglob("SKILL.md"):
            spec = _parse_skill_file(skill_md_path)
            if not spec:
                continue
            key = _normalize_name(spec.name)
            if key and key not in catalog:
                catalog[key] = spec
            folder_key = _normalize_name(skill_md_path.parent.name)
            if folder_key and folder_key not in catalog:
                catalog[folder_key] = spec
    return catalog


def _parse_role_skill_map(settings: Any) -> dict[str, list[str]]:
    raw_map = getattr(settings, "agent_skill_role_map", "") or ""
    role_map: dict[str, list[str]] = {}
    for block in raw_map.split(";"):
        if "=" not in block:
            continue
        role, skills = block.split("=", 1)
        role_key = _normalize_name(role)
        names = [_normalize_name(item) for item in skills.split("|") if item.strip()]
        if role_key and names:
            role_map[role_key] = names
    return role_map


def build_agent_skill_guidance(role: str, settings: Any) -> str:
    if not getattr(settings, "enable_agent_skills", False):
        return ""

    role_key = _normalize_name(role)
    role_map = _parse_role_skill_map(settings)
    skill_names = role_map.get(role_key, [])
    if not skill_names:
        return ""

    catalog = _load_skill_catalog(settings)
    chunks: list[str] = ["SKILL GUIDANCE (from SKILL.md files):"]
    for skill_name in skill_names:
        spec = catalog.get(_normalize_name(skill_name))
        if not spec:
            logger.debug("Skill not found for role {role}: {skill}", role=role, skill=skill_name)
            continue
        tips = spec.instructions[:3]
        chunks.append(f"- {spec.name}: {spec.description}")
        for idx, tip in enumerate(tips, start=1):
            chunks.append(f"  {idx}. {tip}")

    if len(chunks) == 1:
        return ""

    text = "\n".join(chunks)
    max_chars = int(getattr(settings, "agent_skill_prompt_max_chars", 2200) or 2200)
    if len(text) > max_chars:
        text = text[: max_chars - 3].rstrip() + "..."
    return text
