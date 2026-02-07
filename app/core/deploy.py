from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, validate_secrets
from app.core.run_manager import RunManager


@dataclass
class DeployResult:
    ok: bool
    message: str
    deploy_log: Path
    deployed_url: Path | None


def deploy_run(settings: Settings, run_id: str, dry_run: bool | None = None) -> DeployResult:
    manager = RunManager(settings.runs_dir, settings.data_dir)
    run = manager.get_run(run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found.")
    run_dir = Path(run["output_dir"])
    hosting_plan = run_dir / "hosting" / "deploy_plan.json"
    if not hosting_plan.exists():
        raise ValueError("hosting/deploy_plan.json not found. Generate hosting assets first.")

    try:
        plan = json.loads(hosting_plan.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid deploy plan: {exc}") from exc

    if dry_run is None:
        dry_run = settings.deploy_dry_run

    deploy_log = run_dir / "deploy_log.md"
    deployed_url_path = run_dir / "deployed_url.txt"
    deployed_url = plan.get("subdomain") or ""
    deployed_url_path.write_text(deployed_url, encoding="utf-8")

    provider = plan.get("provider")
    command = plan.get("deploy_command") or ""
    deploy_script = run_dir / "hosting" / "deploy.sh"
    supported = bool(plan.get("supported"))
    secrets_report = validate_secrets(settings)
    missing = [
        item for item in secrets_report.get("checks", [])
        if item.get("enabled") and not item.get("ok") and item.get("name", "").startswith("hosting_")
    ]

    if deploy_script.exists():
        command = f"bash {deploy_script.as_posix()}"

    lines = [
        "# Deploy Log",
        "",
        f"Provider: {provider}",
        f"Supported: {supported}",
        f"Dry run: {dry_run}",
        f"Command: {command or 'n/a'}",
        f"Deployed URL: {deployed_url or 'n/a'}",
    ]
    if missing:
        lines.append("")
        lines.append("## Missing credentials")
        for item in missing:
            lines.append(f"- {item.get('name')}: missing {', '.join(item.get('missing') or [])}")

    if not supported:
        lines.append("")
        lines.append("Deploy aborted: unsupported provider.")
        deploy_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return DeployResult(False, "Unsupported provider", deploy_log, deployed_url_path if deployed_url else None)

    if missing:
        lines.append("")
        lines.append("Deploy aborted: missing credentials.")
        deploy_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return DeployResult(False, "Missing credentials", deploy_log, deployed_url_path if deployed_url else None)

    if dry_run:
        lines.append("")
        lines.append("Dry run: no deployment executed.")
        deploy_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return DeployResult(True, "Dry run", deploy_log, deployed_url_path if deployed_url else None)

    if not command:
        lines.append("")
        lines.append("Deploy aborted: command not specified.")
        deploy_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return DeployResult(False, "Missing deploy command", deploy_log, deployed_url_path if deployed_url else None)

    if "<" in command and ">" in command:
        lines.append("")
        lines.append("Deploy aborted: command contains placeholder tokens.")
        deploy_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return DeployResult(False, "Placeholder deploy command", deploy_log, deployed_url_path if deployed_url else None)

    try:
        proc = subprocess.run(
            command,
            cwd=run_dir,
            shell=True,
            capture_output=True,
            text=True,
            timeout=settings.deploy_timeout_s,
            check=False,
        )
    except Exception as exc:
        lines.append("")
        lines.append(f"Deploy failed: {exc}")
        deploy_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return DeployResult(False, f"Deploy failed: {exc}", deploy_log, deployed_url_path if deployed_url else None)

    lines.append("")
    lines.append(f"Return code: {proc.returncode}")
    if proc.stdout:
        lines.append("stdout:")
        lines.append(proc.stdout.strip())
    if proc.stderr:
        lines.append("stderr:")
        lines.append(proc.stderr.strip())
    deploy_log.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ok = proc.returncode == 0
    return DeployResult(ok, "Deploy succeeded" if ok else "Deploy failed", deploy_log, deployed_url_path if deployed_url else None)
