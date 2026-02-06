import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import BASE_DIR, Settings
from app.core.llm import LLMClient, check_ollama


@dataclass
class DoctorResult:
    ok: bool
    report: str


def _env_info() -> Dict[str, Any]:
    return {
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "venv": os.getenv("VIRTUAL_ENV") or "none",
    }


def _check_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        test = path / ".write_test"
        test.write_text("ok", encoding="utf-8")
        test.unlink()
        return True
    except Exception:
        return False


def _env_file_status() -> str:
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        return f"found ({env_path})"
    return f"missing (copy .env.example to {env_path})"


def _format_fix_steps(system: str, settings: Settings) -> List[str]:
    lines: List[str] = []
    if system.lower().startswith("win"):
        lines.append("### Fix commands (Windows PowerShell)")
        lines.append("```powershell")
        lines.append("# Install (run as admin if needed)")
        lines.append("Invoke-WebRequest -Uri https://ollama.com/download -OutFile $env:TEMP\\ollama-installer.exe")
        lines.append("Start-Process -FilePath $env:TEMP\\ollama-installer.exe -Wait")
        lines.append("")
        lines.append("# Start Ollama")
        lines.append("Start-Process -FilePath ollama -ArgumentList \"serve --port 11434\" -NoNewWindow -PassThru")
        lines.append("")
        lines.append("# Pull required models")
        lines.append(f"ollama pull {settings.general_model}")
        lines.append(f"ollama pull {settings.code_model}")
        lines.append("")
        lines.append("# Verify service")
        lines.append(f"Invoke-RestMethod \"{settings.ollama_base_url}/api/tags\" | Out-Null")
        lines.append("```")
    else:
        lines.append("### Fix commands (macOS/Linux)")
        lines.append("```bash")
        lines.append("# Install Ollama")
        lines.append("curl -fsSL https://ollama.com/install.sh | sh")
        lines.append("")
        lines.append("# Start Ollama")
        lines.append("ollama serve --port 11434 --listen http://localhost:11434 >/tmp/ollama.log 2>&1 &")
        lines.append("")
        lines.append("# Pull required models")
        lines.append(f"ollama pull {settings.general_model}")
        lines.append(f"ollama pull {settings.code_model}")
        lines.append("")
        lines.append("# Verify service")
        lines.append(f"curl -fsSL {settings.ollama_base_url}/api/tags")
        lines.append("```")
    return lines


def run_doctor(settings: Settings) -> DoctorResult:
    lines: List[str] = ["# Doctor Report", ""]
    info = _env_info()
    lines.append("## Environment")
    lines.append(f"- OS: {info['os']}")
    lines.append(f"- Python: {info['python']}")
    lines.append(f"- Virtual env: {info['venv']}")
    lines.append("")

    env_checks = [
        ("OLLAMA_BASE_URL", settings.ollama_base_url),
        ("GENERAL_MODEL", settings.general_model),
        ("CODE_MODEL", settings.code_model),
    ]
    for key, default_value in env_checks:
        env_value = os.getenv(key)
        if env_value:
            lines.append(f"- {key}: {env_value} (env)")
        else:
            lines.append(f"- {key}: {default_value} (default)")
    lines.append(f"- .env file: {_env_file_status()}")

    ok = True

    lines.append("")
    lines.append("## Ollama")
    try:
        tags = check_ollama(
            settings.ollama_base_url,
            [settings.general_model, settings.code_model],
        )
        models = [m.get("name") for m in tags.get("models", []) if isinstance(m, dict)]
        lines.append("- Ollama reachable: yes")
        lines.append(f"- Models available: {', '.join(models) if models else 'none'}")
    except Exception as exc:
        ok = False
        lines.append(f"- Ollama reachable: no ({exc})")
        lines.append("- Fix: install/start Ollama and pull required models:")
        lines.extend(_format_fix_steps(platform.system(), settings))

    lines.append("")
    lines.append("## LLM ping")
    llm_client = LLMClient(settings.ollama_base_url, settings.general_model)
    text_ok = False
    json_ok = False
    llm_errors: List[str] = []
    if not llm_client.available():
        llm_errors.append("LLM client not initialized (langchain community dependency missing)")
    try:
        text_resp = llm_client.generate("Return a short sentence: ok.")
        text_ok = bool(text_resp and isinstance(text_resp, str))
    except Exception as exc:
        llm_errors.append(f"text ping failed: {exc}")
    try:
        json_resp = llm_client.generate_json("Return strict JSON: {\"ok\": true}")
        json_ok = isinstance(json_resp, dict) and json_resp.get("ok") is True
        if not json_ok:
            llm_errors.append("JSON response did not include {\"ok\": true}")
    except Exception as exc:
        llm_errors.append(f"JSON ping failed: {exc}")

    lines.append(f"- Client available: {'yes' if llm_client.available() else 'no'}")
    lines.append(f"- Text prompt: {'ok' if text_ok else 'fail'}")
    lines.append(f"- JSON prompt: {'ok' if json_ok else 'fail'}")
    if llm_errors:
        for error in llm_errors:
            lines.append(f"  - {error}")
        ok = False

    lines.append("")
    lines.append("## Write permissions")
    diag_dir = settings.runs_dir / "_diagnostics"
    runs_ok = _check_writable(diag_dir)
    data_ok = _check_writable(settings.data_dir)
    lines.append(f"- {diag_dir}: {'writable' if runs_ok else 'not writable'}")
    lines.append(f"- {settings.data_dir}: {'writable' if data_ok else 'not writable'}")
    if not runs_ok or not data_ok:
        ok = False

    report = "\n".join(lines) + "\n"
    return DoctorResult(ok=ok, report=report)
