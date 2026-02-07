import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.models import SeedInputs
from app.core.critique import CritiqueException, run_devils_advocate
from app.core.llm import LLMClient
from app.core.logging import setup_logging
from app.loop.errors import LoopException
from app.loop.rollback import run_loop_rollback
from app.loop.runner import LoopConfig, LoopRunner
from app.mvp.builder import MVPBuilder, MVPBuilderError
from app.ralph_loop import RalphConfig, RalphLoopError, run_ralph_loop
from app.core.deploy import deploy_run


def _copy_run_to_golden(run_info: dict, golden_root: Path, topic: str) -> Path:
    golden_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_name = f"{timestamp}_{run_info['id']}"
    golden_dir = golden_root / base_name
    suffix = 1
    while golden_dir.exists():
        golden_dir = golden_root / f"{base_name}_{suffix}"
        suffix += 1
    shutil.copytree(Path(run_info["output_dir"]), golden_dir)
    latest_path = golden_root / "latest.json"
    metadata = {"run_id": run_info["id"], "topic": topic, "date": datetime.utcnow().isoformat()}
    latest_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return golden_dir


def run_golden_topic(topic: str, settings: Settings) -> Path | None:
    from app.core.pipeline import VenturePipeline

    pipeline = VenturePipeline(settings)
    result = pipeline.run(topic, n_ideas=settings.default_n_ideas, fast_mode=settings.fast_mode)
    run_info = pipeline.manager.get_run(result.run_id)
    if not run_info:
        return None
    if run_info["status"] not in ("completed", "killed"):
        return None
    golden_root = settings.runs_dir / "_golden"
    return _copy_run_to_golden(run_info, golden_root, topic)


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="AI Venture Factory")
    sub = parser.add_subparsers(dest="command")

    run_cmd = sub.add_parser("run", help="Run the venture pipeline")
    run_cmd.add_argument("--topic", required=True)
    run_cmd.add_argument("--n_ideas", type=int, default=None)
    run_cmd.add_argument("--fast", action="store_true")
    run_cmd.add_argument("--seed-icp", help="Seed ICP description")
    run_cmd.add_argument("--seed-pains", help="Comma-separated seed pain statements")
    run_cmd.add_argument("--seed-competitors", help="Comma-separated competitor hints")
    run_cmd.add_argument("--seed-context", help="Additional context or hypotheses")
    run_cmd.add_argument("--theme", help="Theme to bias idea generation")
    run_cmd.add_argument("--deploy", action="store_true", help="Trigger deployment after MVP build")
    run_cmd.add_argument("--deploy-live", action="store_true", help="Run deployment without dry-run")
    run_cmd.add_argument("--profile", choices=["quick", "standard", "deep"], help="Execution profile with time/token budget")

    ship_cmd = sub.add_parser("ship", help="Run full pipeline and attempt deploy")
    ship_cmd.add_argument("--topic", required=True)
    ship_cmd.add_argument("--n_ideas", type=int, default=None)
    ship_cmd.add_argument("--fast", action="store_true")
    ship_cmd.add_argument("--seed-icp", help="Seed ICP description")
    ship_cmd.add_argument("--seed-pains", help="Comma-separated seed pain statements")
    ship_cmd.add_argument("--seed-competitors", help="Comma-separated competitor hints")
    ship_cmd.add_argument("--seed-context", help="Additional context or hypotheses")
    ship_cmd.add_argument("--theme", help="Theme to bias idea generation")
    ship_cmd.add_argument("--live", action="store_true", help="Run deployment without dry-run")
    ship_cmd.add_argument("--profile", choices=["quick", "standard", "deep"], help="Execution profile with time/token budget")

    sub.add_parser("doctor", help="Run environment diagnostics")

    loop_cmd = sub.add_parser("loop", help="Run the Asmblr autonomous loop")
    loop_cmd.add_argument("--goal", required=True)
    loop_cmd.add_argument("--max-iter", type=int, default=3)
    loop_cmd.add_argument("--time-minutes", type=int)
    loop_cmd.add_argument("--tests", default="pytest -q")
    loop_cmd.add_argument("--dry-run", action="store_true")
    loop_cmd.add_argument("--approve-mode", choices=["auto", "manual"], default="auto")

    build_cmd = sub.add_parser("build-mvp", help="Build MVP artifacts without a market run")
    build_group = build_cmd.add_mutually_exclusive_group(required=True)
    build_group.add_argument("--run-id", help="Existing run to seed the MVP builder")
    build_group.add_argument("--brief", help="One-line brief used to bootstrap the prototype")
    build_cmd.add_argument("--output", help="Target directory under runs/ when using --brief")
    build_cmd.add_argument("--force", action="store_true", help="Overwrite existing mvp_repo/mvp_cycles")
    build_cmd.add_argument("--cycles", help="Comma-separated subset of cycles to run")
    build_cmd.add_argument("--max-fix-iter", type=int, default=5, help="Max auto-fix iterations per cycle")
    build_cmd.add_argument(
        "--frontend-style",
        default="startup_clean",
        help="Frontend style preset (default: startup_clean)",
    )

    golden_cmd = sub.add_parser("golden-run", help="Capture a reproducible golden run")
    golden_cmd.add_argument("--topic", required=True)

    critique_cmd = sub.add_parser("critique", help="Run the Devil's Advocate critique")
    critique_cmd.add_argument("--run-id", required=True)
    critique_cmd.add_argument("--mode", choices=["strict", "standard"], default="standard")

    resume_cmd = sub.add_parser("resume", help="Resume a run after crash")
    resume_cmd.add_argument("--run-id", required=True)

    cleanup_cmd = sub.add_parser("cleanup", help="Purge/compress old runs")
    cleanup_cmd.add_argument("--retention-days", type=int, default=None)
    cleanup_cmd.add_argument("--max-count", type=int, default=None)
    cleanup_cmd.add_argument("--compress-after-days", type=int, default=None)
    cleanup_cmd.add_argument("--archive-dirs", default=None, help="Comma-separated run subdirs to zip")

    backup_cmd = sub.add_parser("backup", help="Create a local snapshot of app.db and runs/")
    backup_cmd.add_argument("--output", default=None, help="Backup root directory")
    backup_cmd.add_argument("--retention-days", type=int, default=None)

    rollback_cmd = sub.add_parser("loop-rollback", help="Rollback to a loop iteration")
    rollback_cmd.add_argument("--run-id", required=True)
    rollback_cmd.add_argument("--to-iter", type=int, required=True)

    deploy_cmd = sub.add_parser("deploy", help="Deploy an MVP run using hosting plan")
    deploy_cmd.add_argument("--run-id", required=True)
    deploy_cmd.add_argument("--dry-run", action="store_true", help="Override deploy dry-run behavior")

    ralph_cmd = sub.add_parser("ralph-loop", help="Run the Ralph loop against prd.json")
    ralph_cmd.add_argument("--max-iter", type=int, default=5)
    ralph_cmd.add_argument("--tests", default="pytest -q")
    ralph_cmd.add_argument("--dry-run", action="store_true")
    ralph_cmd.add_argument("--approve-mode", choices=["auto", "manual"], default="auto")
    ralph_cmd.add_argument("--prd-path", default="prd.json")
    ralph_cmd.add_argument("--progress-path", default="progress.txt")
    ralph_cmd.add_argument("--tail-lines", type=int, default=60)

    args = parser.parse_args()
    if args.command == "run":
        topic = (args.topic or "").strip()
        if len(topic) < 3 or len(topic) > 200:
            print("Invalid topic: must be between 3 and 200 characters.")
            raise SystemExit(1)
        if any(ord(ch) < 32 for ch in topic):
            print("Invalid topic: control characters are not allowed.")
            raise SystemExit(1)
        settings = get_settings()
        if args.deploy:
            settings.enable_deploy = True
        if args.deploy_live:
            settings.deploy_dry_run = False
        from app.core.pipeline import VenturePipeline

        pipeline = VenturePipeline(settings)
        seed_inputs = SeedInputs(
            icp=args.seed_icp,
            pains=_split_csv(args.seed_pains),
            competitors=_split_csv(args.seed_competitors),
            context=args.seed_context,
            theme=args.theme,
        )
        n_ideas = args.n_ideas or settings.default_n_ideas
        pipeline.run(topic, n_ideas, fast_mode=args.fast, seed_inputs=seed_inputs, execution_profile=args.profile)
    elif args.command == "ship":
        topic = (args.topic or "").strip()
        if len(topic) < 3 or len(topic) > 200:
            print("Invalid topic: must be between 3 and 200 characters.")
            raise SystemExit(1)
        if any(ord(ch) < 32 for ch in topic):
            print("Invalid topic: control characters are not allowed.")
            raise SystemExit(1)
        settings = get_settings()
        settings.enable_deploy = True
        if args.live:
            settings.deploy_dry_run = False
        from app.core.pipeline import VenturePipeline

        pipeline = VenturePipeline(settings)
        seed_inputs = SeedInputs(
            icp=args.seed_icp,
            pains=_split_csv(args.seed_pains),
            competitors=_split_csv(args.seed_competitors),
            context=args.seed_context,
            theme=args.theme,
        )
        n_ideas = args.n_ideas or settings.default_n_ideas
        pipeline.run(topic, n_ideas, fast_mode=args.fast, seed_inputs=seed_inputs, execution_profile=args.profile)
    elif args.command == "doctor":
        settings = get_settings()
        from app.core.doctor import run_doctor

        result = run_doctor(settings)
        report_dir = settings.runs_dir / "_diagnostics"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "doctor_report.md"
        report_path.write_text(result.report, encoding="utf-8")
        print(result.report)
        raise SystemExit(0 if result.ok else 1)
    elif args.command == "loop":
        settings = get_settings()
        config = LoopConfig(
            goal=args.goal,
            max_iter=args.max_iter,
            time_minutes=args.time_minutes,
            tests_command=args.tests,
            dry_run=args.dry_run,
            approve_mode=args.approve_mode,
        )
        plan_llm = LLMClient(settings.ollama_base_url, settings.general_model)
        patch_llm = LLMClient(settings.ollama_base_url, settings.code_model)
        runner = LoopRunner(settings, config, plan_llm=plan_llm, patch_llm=patch_llm)
        try:
            result = runner.run()
            print(f"Loop {result.run_id} completed with status {result.status} (iterations: {result.iterations})")
            raise SystemExit(0 if result.status == "completed" else 1)
        except LoopException as exc:
            print(f"Loop failed: {exc}")
            raise SystemExit(1)
    elif args.command == "build-mvp":
        settings = get_settings()
        builder = MVPBuilder(settings)
        cycle_keys = _split_csv(args.cycles)
        try:
            if args.run_id:
                result = builder.build_from_run(
                    args.run_id,
                    cycle_keys=cycle_keys,
                    max_fix_iter=args.max_fix_iter,
                    force=args.force,
                    frontend_style=args.frontend_style,
                )
            else:
                output_dir = Path(args.output) if args.output else settings.runs_dir / "_adhoc" / datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
                result = builder.build_from_brief(
                    args.brief,
                    output_dir,
                    cycle_keys=cycle_keys,
                    max_fix_iter=args.max_fix_iter,
                    force=args.force,
                    frontend_style=args.frontend_style,
                )
            print(f"MVP repo ready at {result.run_dir / 'mvp_repo'}")
            print(f"Summary available at {result.run_dir / 'mvp_build_summary.md'}")
            print(f"Data source: {result.data_source.get('data_source')}")
            raise SystemExit(0 if result.success else 1)
        except MVPBuilderError as exc:
            print(f"build-mvp failed: {exc}")
            raise SystemExit(1)
    elif args.command == "golden-run":
        settings = get_settings()
        try:
            golden_dir = run_golden_topic(args.topic, settings)
            if golden_dir:
                print(f"Golden run saved to {golden_dir}")
                raise SystemExit(0)
            print("Run did not complete (ABORT). Golden run not created.")
            raise SystemExit(1)
        except Exception as exc:
            print(f"Golden run failed: {exc}")
            raise SystemExit(1)
    elif args.command == "critique":
        settings = get_settings()
        try:
            result = run_devils_advocate(settings, args.run_id, mode=args.mode)
            print(f"Critique verdict {result.verdict} written to {result.markdown_path} and {result.json_path}")
            raise SystemExit(0)
        except CritiqueException as exc:
            print(f"Critique failed: {exc}")
            raise SystemExit(1)
    elif args.command == "resume":
        settings = get_settings()
        from app.core.pipeline import VenturePipeline

        pipeline = VenturePipeline(settings)
        run_info = pipeline.manager.get_run(args.run_id)
        if not run_info:
            print("Run not found.")
            raise SystemExit(1)
        pipeline.run(
            run_info["topic"],
            settings.default_n_ideas,
            fast_mode=settings.fast_mode,
            run_id=args.run_id,
            resume=True,
        )
    elif args.command == "cleanup":
        settings = get_settings()
        from app.core.run_manager import RunManager

        manager = RunManager(settings.runs_dir, settings.data_dir)
        archive_dirs = _split_csv(args.archive_dirs) if args.archive_dirs else _split_csv(settings.run_archive_dirs)
        result = manager.run_maintenance(
            retention_days=args.retention_days,
            max_count=args.max_count,
            compress_after_days=args.compress_after_days,
            archive_dirs=archive_dirs,
        )
        print(json.dumps(result, indent=2))
    elif args.command == "backup":
        settings = get_settings()
        from app.core.backup import create_snapshot, prune_backups

        backup_root = Path(args.output) if args.output else Path(settings.backup_dir)
        snapshot_dir = create_snapshot(settings.data_dir, settings.runs_dir, backup_root=backup_root)
        retention = args.retention_days if args.retention_days is not None else settings.backup_retention_days
        removed = prune_backups(backup_root, retention)
        print(json.dumps({"snapshot": str(snapshot_dir), "pruned": removed}, indent=2))
    elif args.command == "loop-rollback":
        settings = get_settings()
        run_loop_rollback(settings, args.run_id, args.to_iter)
        print(f"Rolled back {args.run_id} to iteration {args.to_iter}")
    elif args.command == "ralph-loop":
        settings = get_settings()
        config = RalphConfig(
            prd_path=Path(args.prd_path),
            progress_path=Path(args.progress_path),
            max_iter=args.max_iter,
            tests_command=args.tests,
            dry_run=args.dry_run,
            approve_mode=args.approve_mode,
            tail_lines=args.tail_lines,
        )
        try:
            status = run_ralph_loop(settings, config)
            raise SystemExit(status)
        except RalphLoopError as exc:
            print(f"Ralph loop failed: {exc}")
            raise SystemExit(1)
    elif args.command == "deploy":
        settings = get_settings()
        try:
            result = deploy_run(settings, args.run_id, dry_run=True if args.dry_run else None)
            print(f"Deploy result: {result.message}")
            print(f"Deploy log: {result.deploy_log}")
            if result.deployed_url:
                print(f"Deployed URL: {result.deployed_url}")
            raise SystemExit(0 if result.ok else 1)
        except Exception as exc:
            print(f"Deploy failed: {exc}")
            raise SystemExit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
