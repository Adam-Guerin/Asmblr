from pathlib import Path


def generate_fastapi_skeleton(target_dir: Path, project_name: str, minimal: bool = False) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    if not minimal:
        (target_dir / "README.md").write_text(
            f"# {project_name}\n\nGenerated skeleton with FastAPI + SQLite.\n",
            encoding="utf-8",
        )
    app_dir = target_dir / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "__init__.py").write_text("", encoding="utf-8")
    (app_dir / "main.py").write_text(
        """
from fastapi import FastAPI

app = FastAPI(title="Generated MVP")

@app.get("/")
def read_root():
    return {"status": "ok"}
""".lstrip(),
        encoding="utf-8",
    )
    (target_dir / "requirements.txt").write_text(
        "fastapi\nuvicorn\n",
        encoding="utf-8",
    )
    (target_dir / "env.example").write_text(
        "APP_ENV=development\nPORT=8000\n",
        encoding="utf-8",
    )
    if not minimal:
        (target_dir / "run.sh").write_text(
            "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000\n",
            encoding="utf-8",
        )
