from __future__ import annotations

import json
import re
from pathlib import Path


ALLOWED_SPACING = {
    "0",
    "0.5",
    "1",
    "1.5",
    "2",
    "2.5",
    "3",
    "3.5",
    "4",
    "5",
    "6",
    "8",
    "10",
    "12",
    "14",
    "16",
    "20",
    "24",
    "28",
    "32",
    "36",
    "40",
    "44",
    "48",
    "52",
    "56",
    "60",
    "64",
    "72",
    "80",
    "96",
}
ALLOWED_BUTTON_VARIANTS = {"primary", "secondary", "ghost"}
NEUTRAL_COLORS = {"slate", "gray", "zinc", "neutral", "stone"}
BANNED_WORDS = {"todo", "lorem", "placeholder"}
JARGON_WORDS = {
    "synergy",
    "leverage",
    "paradigm",
    "disrupt",
    "enterprise-grade",
    "best-in-class",
    "world-class",
    "next-gen",
}
CTA_VERBS = {
    "start",
    "get",
    "join",
    "view",
    "see",
    "request",
    "book",
    "save",
    "continue",
    "create",
    "build",
}
TRUST_KEYWORDS = {
    "trusted",
    "proof",
    "secure",
    "privacy",
    "compliance",
    "reliable",
    "customers",
    "founders",
}
LOW_CONTRAST_CLASSES = {
    "text-slate-200",
    "text-slate-300",
    "text-slate-400",
    "text-gray-200",
    "text-gray-300",
    "text-gray-400",
    "text-zinc-200",
    "text-zinc-300",
    "text-zinc-400",
    "text-neutral-200",
    "text-neutral-300",
    "text-neutral-400",
    "text-stone-200",
    "text-stone-300",
    "text-stone-400",
    "text-white/50",
    "text-white/60",
    "text-black/40",
    "text-black/50",
}


def run_ui_lint(repo_dir: Path, cycle_dir: Path, accent_color: str | None = None) -> dict:
    resolved_accent = accent_color or _resolve_accent_color()
    targets = [
        repo_dir / "app",
        repo_dir / "components",
    ]
    files: list[Path] = []
    for root in targets:
        if not root.exists():
            continue
        files.extend(root.rglob("*.tsx"))
        files.extend(root.rglob("*.ts"))

    errors: list[dict] = []
    accent_found: set[str] = set()
    files_scanned = 0

    for path in sorted(set(files)):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        files_scanned += 1
        rel_path = path.relative_to(repo_dir).as_posix()

        class_strings = _extract_class_strings(text)
        class_tokens = _flatten_class_tokens(class_strings)

        spacing_errors = _check_spacing(class_tokens)
        if spacing_errors:
            errors.extend(
                {
                    "rule": "spacing_scale",
                    "file": rel_path,
                    "detail": item,
                }
                for item in spacing_errors
            )

        low_contrast = [token for token in class_tokens if token in LOW_CONTRAST_CLASSES]
        if low_contrast:
            errors.append(
                {
                    "rule": "contrast",
                    "file": rel_path,
                    "detail": f"Low-contrast classes: {', '.join(sorted(set(low_contrast)))}",
                }
            )

        accent_found.update(_extract_accent_colors(class_tokens, resolved_accent))

        heading_violations = _check_heading_lengths(text)
        for item in heading_violations:
            errors.append({"rule": "heading_length", "file": rel_path, "detail": item})

        paragraph_violations = _check_paragraph_lengths(text)
        for item in paragraph_violations:
            errors.append({"rule": "paragraph_length", "file": rel_path, "detail": item})

        copy_violations = _check_banned_copy(text)
        for item in copy_violations:
            errors.append({"rule": "banned_copy", "file": rel_path, "detail": item})

        microcopy_violations = _check_microcopy_rubric(text, rel_path)
        for item in microcopy_violations:
            errors.append({"rule": "microcopy_rubric", "file": rel_path, "detail": item})

        variant_violations = _check_button_variants(text)
        for item in variant_violations:
            errors.append({"rule": "button_variants", "file": rel_path, "detail": item})

    if accent_found and accent_found != {resolved_accent}:
        errors.append(
            {
                "rule": "accent_color",
                "file": "global",
                "detail": f"Accent colors detected: {', '.join(sorted(accent_found))}",
            }
        )

    landing_errors = _check_landing_sections(repo_dir)
    for item in landing_errors:
        errors.append({"rule": "landing_sections", "file": item["file"], "detail": item["detail"]})

    state_errors = _check_required_states(repo_dir)
    for item in state_errors:
        errors.append({"rule": "required_states", "file": item["file"], "detail": item["detail"]})

    toast_errors = _check_toaster_usage(repo_dir)
    for item in toast_errors:
        errors.append({"rule": "toaster_usage", "file": item["file"], "detail": item["detail"]})

    ok = len(errors) == 0
    result = {
        "ok": ok,
        "status": "pass" if ok else "fail",
        "errors": errors,
        "metrics": {
            "files_scanned": files_scanned,
            "accent_colors": sorted(accent_found),
            "allowed_accent": resolved_accent,
        },
    }
    cycle_dir.mkdir(parents=True, exist_ok=True)
    (cycle_dir / "ui_lint.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def count_pages(repo_dir: Path) -> int:
    app_dir = repo_dir / "app"
    if not app_dir.exists():
        return 0
    return len([p for p in app_dir.rglob("page.tsx") if p.is_file()])


def count_components(repo_dir: Path) -> int:
    comp_dir = repo_dir / "components"
    if not comp_dir.exists():
        return 0
    return len([p for p in comp_dir.rglob("*.tsx") if p.is_file()])


def _extract_class_strings(text: str) -> list[str]:
    class_strings = []
    for match in re.finditer(r"className=(['\"])(.*?)\\1", text, re.S):
        class_strings.append(match.group(2))
    for match in re.finditer(r"className=\\{[^}]*?['\"]([^'\"]+)['\"][^}]*\\}", text, re.S):
        class_strings.append(match.group(1))
    return class_strings


def _flatten_class_tokens(class_strings: list[str]) -> list[str]:
    tokens: list[str] = []
    for block in class_strings:
        for raw in block.split():
            token = raw.strip()
            if not token:
                continue
            tokens.append(token)
    return tokens


def _strip_variants(token: str) -> str:
    while ":" in token:
        token = token.split(":", 1)[1]
    return token


def _check_spacing(tokens: list[str]) -> list[str]:
    violations: list[str] = []
    for token in tokens:
        core = _strip_variants(token)
        match = re.match(
            r"^(p|px|py|pt|pr|pb|pl|m|mx|my|mt|mr|mb|ml|gap|gap-x|gap-y|space-x|space-y)-(-?\\d+(?:\\.5)?)$",
            core,
        )
        if not match:
            continue
        value = match.group(2)
        if value not in ALLOWED_SPACING:
            violations.append(core)
    return violations


def _extract_accent_colors(tokens: list[str], accent_color: str) -> set[str]:
    accents: set[str] = set()
    for token in tokens:
        core = _strip_variants(token)
        match = re.match(
            r"^(text|bg|border|ring|from|to|via|fill|stroke)-([a-z]+)(?:-\\d{2,3})?(?:/\\d{2})?$",
            core,
        )
        if not match:
            continue
        color = match.group(2)
        if color in NEUTRAL_COLORS or color in {"white", "black", "transparent", "current", "gradient"}:
            continue
        accents.add(color)
    return accents


def _check_heading_lengths(text: str) -> list[str]:
    violations: list[str] = []
    for match in re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", text, re.S):
        value = _normalize_copy(match)
        if value and len(value) > 60:
            violations.append(value)
    return violations


def _check_paragraph_lengths(text: str) -> list[str]:
    violations: list[str] = []
    for match in re.findall(r"<p[^>]*>(.*?)</p>", text, re.S):
        value = _normalize_copy(match)
        if value and len(value) > 120:
            violations.append(value)
    return violations


def _normalize_copy(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", text)
    without_expr = re.sub(r"\\{[^}]*\\}", "", without_tags)
    return " ".join(without_expr.split()).strip()


def _check_banned_copy(text: str) -> list[str]:
    violations: list[str] = []
    for value in _extract_string_literals(text):
        lowered = value.lower()
        if any(word in lowered for word in BANNED_WORDS):
            violations.append(value)
    return violations


def _extract_string_literals(text: str) -> list[str]:
    literals: list[str] = []
    for match in re.finditer(r"(['\"])([^\\n]*?)\\1", text):
        value = match.group(2)
        if not value or len(value) < 3:
            continue
        snippet = text[max(0, match.start() - 20) : match.start()]
        if "className" in snippet:
            continue
        if _looks_like_class_list(value):
            continue
        if value.startswith("/") or value.startswith("./") or value.startswith("@/"):
            continue
        literals.append(value)
    return literals


def _looks_like_class_list(value: str) -> bool:
    indicators = ["bg-", "text-", "border-", "shadow-", "rounded", "px-", "py-", "mx-", "my-", "gap-"]
    return any(indicator in value for indicator in indicators)


def _check_button_variants(text: str) -> list[str]:
    violations: list[str] = []
    for match in re.finditer(r"variant=(['\"])([^'\"]+)\\1", text):
        value = match.group(2)
        if value not in ALLOWED_BUTTON_VARIANTS:
            violations.append(value)
    for match in re.finditer(r"variant=\\{([^}]+)\\}", text):
        for literal in re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)):
            if literal not in ALLOWED_BUTTON_VARIANTS:
                violations.append(literal)
    return violations


def _check_microcopy_rubric(text: str, rel_path: str) -> list[str]:
    violations: list[str] = []
    literals = _extract_string_literals(text)
    for value in literals:
        lowered = value.lower()
        if any(word in lowered for word in JARGON_WORDS):
            violations.append(f"Jargon detected: '{value}'")
            break

    if rel_path == "app/page.tsx":
        if not _has_trust_signal(text):
            violations.append("Trust signal missing on landing page.")
        cta_issues = _check_cta_strength(text)
        violations.extend(cta_issues)
    return violations


def _has_trust_signal(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in TRUST_KEYWORDS)


def _check_cta_strength(text: str) -> list[str]:
    issues: list[str] = []
    for label in _extract_cta_labels(text):
        words = [w for w in re.split(r"\s+", label.strip()) if w]
        if not words:
            continue
        if len(words) > 4:
            issues.append(f"CTA too long: '{label}'")
            continue
        if words[0].lower() not in CTA_VERBS:
            issues.append(f"CTA should start with a verb: '{label}'")
    return issues


def _extract_cta_labels(text: str) -> list[str]:
    labels: list[str] = []
    for match in re.finditer(r"<Button[^>]*>(.*?)</Button>", text, re.S):
        value = re.sub(r"<[^>]+>", "", match.group(1))
        clean = " ".join(value.split()).strip()
        if not clean or "{" in clean or "}" in clean:
            continue
        labels.append(clean)
    for match in re.finditer(r"(primaryCta|secondaryCta):\s*['\"]([^'\"]+)['\"]", text):
        labels.append(match.group(2))
    return labels


def _resolve_accent_color() -> str:
    theme_path = Path(__file__).resolve().parent / "frontend_kit" / "theme.ts"
    default = "sky"
    if not theme_path.exists():
        return default
    try:
        content = theme_path.read_text(encoding="utf-8")
    except Exception:
        return default
    match = re.search(r"accentName:\s*['\"]([a-z]+)['\"]", content)
    if match:
        return match.group(1).lower()
    match = re.search(r"accent:\s*['\"](#[0-9a-fA-F]{6})['\"]", content)
    if not match:
        return default
    hex_value = match.group(1).lower()
    hex_map = {
        "#0ea5e9": "sky",
        "#2563eb": "blue",
        "#14b8a6": "teal",
        "#22c55e": "green",
        "#f97316": "orange",
    }
    return hex_map.get(hex_value, default)


def _check_landing_sections(repo_dir: Path) -> list[dict]:
    landing = repo_dir / "app" / "page.tsx"
    required = {"Hero", "Features", "HowItWorks", "SocialProof", "Pricing", "FAQ", "CTA", "Footer"}
    if not landing.exists():
        return [{"file": "app/page.tsx", "detail": "Landing page not found."}]
    try:
        text = landing.read_text(encoding="utf-8")
    except Exception:
        return [{"file": "app/page.tsx", "detail": "Landing page could not be read."}]
    order = _extract_section_order(text)
    data_sections = _extract_data_sections(text)
    if not order and not data_sections:
        return [{"file": "app/page.tsx", "detail": "Landing section order is missing."}]
    missing = required - set(data_sections or order)
    if missing:
        return [
            {
                "file": "app/page.tsx",
                "detail": f"Missing sections: {', '.join(sorted(missing))}",
            }
        ]
    return []


def _extract_section_order(text: str) -> list[str]:
    match = re.search(r"const\s+sectionOrder\s*=\s*\[(.*?)\]", text, re.S)
    if not match:
        return []
    raw = match.group(1)
    return re.findall(r"['\"]([A-Za-z]+)['\"]", raw)


def _extract_data_sections(text: str) -> list[str]:
    return re.findall(r"data-section=['\"]([A-Za-z]+)['\"]", text)


def _check_required_states(repo_dir: Path) -> list[dict]:
    errors: list[dict] = []
    required_paths = [
        ("app/loading.tsx", repo_dir / "app" / "loading.tsx"),
        ("app/app/loading.tsx", repo_dir / "app" / "app" / "loading.tsx"),
        ("components/ui/empty-state.tsx", repo_dir / "components" / "ui" / "empty-state.tsx"),
        ("app/error.tsx", repo_dir / "app" / "error.tsx"),
        ("app/not-found.tsx", repo_dir / "app" / "not-found.tsx"),
        ("app/global-error.tsx", repo_dir / "app" / "global-error.tsx"),
    ]
    has_loading = (repo_dir / "app" / "loading.tsx").exists() or (
        repo_dir / "app" / "app" / "loading.tsx"
    ).exists()
    if not has_loading:
        errors.append({"file": "app/loading.tsx|app/app/loading.tsx", "detail": "Loading state missing."})
    for label, path in required_paths[2:]:
        if not path.exists():
            errors.append({"file": label, "detail": "Required UI state missing."})
    return errors


def _check_toaster_usage(repo_dir: Path) -> list[dict]:
    layout = repo_dir / "app" / "layout.tsx"
    if not layout.exists():
        return [{"file": "app/layout.tsx", "detail": "Root layout missing for toast check."}]
    try:
        text = layout.read_text(encoding="utf-8")
    except Exception:
        return [{"file": "app/layout.tsx", "detail": "Root layout could not be read."}]
    has_toaster = "Toaster" in text
    has_provider = "ToastProvider" in text
    if not (has_toaster and has_provider):
        return [{"file": "app/layout.tsx", "detail": "Toaster or ToastProvider is missing."}]
    return []
