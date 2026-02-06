from pathlib import Path
from app.core.llm import LLMClient
from app.langchain_tools import LandingGeneratorTool, ContentGeneratorTool, RepoGeneratorTool


def test_landing_generator_creates_html_files(tmp_path: Path, monkeypatch):
    llm = LLMClient("http://localhost:11434", "llama3.1:8b")
    monkeypatch.setattr(llm, "available", lambda: False)
    tool = LandingGeneratorTool(llm)
    output_dir = tmp_path / "landing"
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    tool.run(
        {
            "product_name": "TestProduct",
            "output_dir": str(output_dir),
            "template_dir": str(template_dir),
            "prompt": None,
            "fast_mode": True,
        }
    )
    assert (output_dir / "index.html").exists()
    assert (output_dir / "style.css").exists()
    html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert "value-prop" in html
    assert "Objections" in html
    assert "page_view" in html
    assert "js-primary-cta" in html


def test_content_generator_creates_pack_files(tmp_path: Path, monkeypatch):
    llm = LLMClient("http://localhost:11434", "llama3.1:8b")
    monkeypatch.setattr(llm, "available", lambda: False)
    tool = ContentGeneratorTool(llm)
    output_dir = tmp_path / "content"
    tool.run(
        {
            "product_name": "TestProduct",
            "output_dir": str(output_dir),
            "prompt": None,
            "fast_mode": True,
        }
    )
    assert (output_dir / "posts.md").exists()
    assert (output_dir / "ads.md").exists()
    assert (output_dir / "hooks.md").exists()
    assert (output_dir / "analytics_plan.md").exists()


def test_repo_generator_creates_buildable_structure(tmp_path: Path):
    tool = RepoGeneratorTool()
    output_dir = tmp_path / "repo"
    tool.run({"project_name": "TestProduct", "output_dir": str(output_dir), "fast_mode": True})
    assert (output_dir / "app" / "main.py").exists()
    assert (output_dir / "requirements.txt").exists()
