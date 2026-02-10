import json
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader

from app.core.llm import LLMClient


def render_landing(template_dir: Path, payload: dict[str, Any], output_dir: Path) -> None:
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    html_template = env.get_template("landing.html.j2")
    css_template = env.get_template("landing.css")
    html = html_template.render(**payload)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    (output_dir / "style.css").write_text(css_template.render(), encoding="utf-8")


def generate_landing_copy(llm: LLMClient, prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
    if llm.available():
        try:
            raw = llm.generate(prompt)
            data = json.loads(raw)
            return data
        except Exception:
            return fallback
    return fallback


def generate_content_pack(llm: LLMClient, prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
    if llm.available():
        try:
            raw = llm.generate(prompt)
            data = json.loads(raw)
            return data
        except Exception:
            return fallback
    return fallback


def write_content_pack(output_dir: Path, pack: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "posts.md").write_text("\n\n".join(pack.get("posts", [])), encoding="utf-8")
    (output_dir / "hooks.md").write_text("\n".join(pack.get("hooks", [])), encoding="utf-8")
    (output_dir / "ads.md").write_text("\n\n".join(pack.get("ads", [])), encoding="utf-8")
    (output_dir / "video_script.md").write_text(pack.get("video_script", ""), encoding="utf-8")
    (output_dir / "calendar.md").write_text(pack.get("calendar", ""), encoding="utf-8")
    analytics_plan = pack.get("analytics_plan") or {}
    if analytics_plan:
        lines = [
            "# Analytics Plan",
            "",
            f"- Primary conversion: {analytics_plan.get('primary_conversion', 'unknown')}",
            f"- Events: {', '.join(analytics_plan.get('events', []))}",
            f"- UTM template: {analytics_plan.get('utm_template', '')}",
        ]
        (output_dir / "analytics_plan.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def default_landing_payload(product_name: str, fast_mode: bool = False) -> dict[str, Any]:
    if fast_mode:
        return {
            "product_name": product_name,
            "logo_src": "./logo.svg",
            "logo_alt": f"{product_name} logo",
            "hero_headline": f"{product_name} helps teams test new ideas quickly",
            "hero_subhead": "A short, practical path from signals to a testable MVP.",
            "value_prop_5s": f"For small teams: clarify the MVP test in one page, then launch a simple demand check.",
            "cta_primary": "Join the early access list",
            "cta_intent": "early_access",
            "category": "MVP Validation",
            "problem": "Teams collect ideas but struggle to decide what to test next.",
            "solution_summary": "A lightweight workflow that turns real pains into a clear MVP test plan.",
            "solution_does": [
                "Collect pains from a few trusted sources",
                "Summarize the core problem in plain language",
            ],
            "solution_does_not": [
                "Promise outcomes without evidence",
                "Replace customer interviews",
            ],
            "why_now": "",
            "differentiation": [],
            "social_proof_title": "Early proof",
            "social_proof_items": [
                {
                    "quote": "Design partner interviews in progress with early-stage operators.",
                    "who": "Founding team",
                    "source": "Internal discovery notes",
                }
            ],
            "objections": [
                {
                    "objection": "Is this replacing customer interviews?",
                    "response": "No. It helps structure faster tests before interviews.",
                }
            ],
            "cta_heading": "Want a simple MVP test plan?",
            "cta_subhead": "Join early access and share your feedback.",
            "faq": [
                {"q": "Is this a finished product?", "a": "No, it is an early MVP for feedback."},
            ],
            "analytics": {
                "provider": "default_js",
                "events": ["page_view", "cta_click", "waitlist_submit"],
                "cta_event_name": "cta_click",
                "primary_conversion": "waitlist_submit",
            },
        }
    return {
        "product_name": product_name,
        "logo_src": "./logo.svg",
        "logo_alt": f"{product_name} logo",
        "hero_headline": f"{product_name} helps teams validate MVPs with less guesswork",
        "hero_subhead": "Turn specific pains into a testable MVP plan you can explain in minutes.",
        "value_prop_5s": "For early-stage founders: turn one painful workflow into one testable MVP offer this week.",
        "cta_primary": "Request early access",
        "cta_intent": "early_access",
        "category": "MVP Validation",
        "problem": "Early teams lose time debating ideas without clear, testable assumptions.",
        "solution_summary": "A focused workflow that distills pain points into a lean MVP scope and launch materials.",
        "solution_does": [
            "Summarize real pain points into a clear problem statement",
            "Outline MVP scope and what's excluded",
            "Produce a simple landing page and test content",
        ],
        "solution_does_not": [
            "Guarantee results or market traction",
            "Replace discovery interviews with customers",
        ],
        "why_now": "Teams can run smaller, faster tests, but need clearer MVP scope and messaging.",
        "differentiation": [
            "Focuses on MVP scope clarity, not growth at scale",
            "Outputs are designed for early validation only",
        ],
        "social_proof_title": "Proof before scale",
        "social_proof_items": [
            {
                "quote": "Built for teams running design-partner interviews before writing full product specs.",
                "who": "Founding team",
                "source": "Current validation process",
            },
            {
                "quote": "Landing and messaging are intentionally framed as test assets, not launch claims.",
                "who": "Product lead",
                "source": "Internal GTM guideline",
            },
        ],
        "objections": [
            {
                "objection": "Will this guarantee traction?",
                "response": "No. It improves test clarity; demand still needs real customer validation.",
            },
            {
                "objection": "Do we need paid ads immediately?",
                "response": "No. Start with one conversion CTA and organic feedback loops first.",
            },
        ],
        "cta_heading": "Ready to test demand?",
        "cta_subhead": "Join early access to try the MVP and give feedback.",
        "faq": [
            {"q": "What does the MVP include?", "a": "A basic scope, landing copy, and content pack."},
            {"q": "What does it not include?", "a": "Paid ads management, analytics, or growth automation."},
            {"q": "Is this production-ready?", "a": "No, it is an early MVP meant for feedback."},
        ],
        "analytics": {
            "provider": "default_js",
            "events": ["page_view", "cta_click", "waitlist_submit"],
            "cta_event_name": "cta_click",
            "primary_conversion": "waitlist_submit",
        },
    }


def default_content_pack(product_name: str, fast_mode: bool = False) -> dict[str, Any]:
    if fast_mode:
        return {
            "posts": [
                f"{product_name} helps founders turn a vague idea into a testable MVP outline.",
                "If you're stuck debating ideas, a short MVP plan can unblock your next step.",
                "Early-stage teams need clarity on what to test, not more features.",
            ],
            "hooks": [
                "Still debating which idea to test first?",
                "A 1-page MVP plan beats a month of guessing.",
            ],
            "ads": [
                "Turn pains into a testable MVP plan. Join early access.",
            ],
            "video_script": "Hook: Still debating MVP scope?\nProblem: Teams waste weeks without a clear test plan.\nSolution: AI Venture Factory drafts a focused MVP outline.\nCTA: Join early access.",
            "calendar": "Day 1: Problem-first post.\nDay 3: MVP scope example.\nDay 5: Early access CTA.\nDay 7: Ask for feedback.",
            "cta_primary": "Join early access",
            "cta_intent": "early_access",
            "analytics_plan": {
                "primary_conversion": "waitlist_submit",
                "events": ["page_view", "cta_click", "waitlist_submit"],
                "utm_template": "utm_source={source}&utm_medium={medium}&utm_campaign={campaign}",
            },
        }
    return {
        "posts": [
            f"{product_name} helps founders turn fuzzy ideas into a clear MVP test plan.",
            "If you're stuck in idea debates, a one-page MVP scope helps you move.",
            "An early MVP needs a clear problem statement and what not to build.",
            "Stop guessing: write the smallest test that proves demand.",
            "Most teams overbuild before validating the pain.",
            "A simple landing page can be enough to test interest.",
            "Clear scope reduces wasted build time.",
            "Validation starts with a concrete pain, not a big vision.",
            "Get feedback on the MVP before you write code.",
            "Early access is a better CTA than a full launch.",
        ],
        "hooks": [
            "What if your MVP plan fit on one page?",
            "Are you building too much before testing demand?",
            "A clear 'does not do' list saves months.",
            "How to test demand with a simple landing page.",
            "What does your MVP explicitly exclude?",
        ],
        "ads": [
            "Turn pains into a testable MVP outline. Join early access.",
            "Stop debating ideas. Get a clear MVP scope in one run.",
            "A simple MVP plan is the fastest way to test demand.",
        ],
        "video_script": "Hook: Still debating MVP scope?\nProblem: Teams lose time without a testable plan.\nSolution: AI Venture Factory drafts a lean MVP outline and launch copy.\nCTA: Request early access.",
        "calendar": "Day 1: Pain-focused post.\nDay 2: MVP scope example.\nDay 4: 'Does not do' list.\nDay 6: Landing page test CTA.\nDay 8: Founder question post.\nDay 11: Short demo clip.\nDay 14: Feedback request.",
        "cta_primary": "Request early access",
        "cta_intent": "early_access",
        "analytics_plan": {
            "primary_conversion": "waitlist_submit",
            "events": ["page_view", "cta_click", "waitlist_submit"],
            "utm_template": "utm_source={source}&utm_medium={medium}&utm_campaign={campaign}",
        },
    }
