import tomllib


def test_quality_gate_critical_lint_is_aligned_with_ci(monkeypatch):
    from scripts import test_all

    captured = []

    def fake_run(cmd, env=None):
        captured.append(list(cmd))
        return 0

    monkeypatch.setattr(test_all, "_run", fake_run)
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr("sys.argv", ["test_all.py", "--mode", "quick"])

    rc = test_all.main()

    assert rc == 0
    critical_cmd = captured[0]
    assert critical_cmd[:4] == [
        test_all.sys.executable,
        "-m",
        "ruff",
        "check",
    ]
    lint_targets = critical_cmd[4 : critical_cmd.index("--select")]
    assert lint_targets == ["app/core", "app/tools", "app/loop", "app/mvp", "scripts", "tests"]
    assert "--select" in critical_cmd
    assert critical_cmd[critical_cmd.index("--select") + 1] == "E9,F63,F7,F82"
    assert "--extend-ignore" in critical_cmd
    assert critical_cmd[critical_cmd.index("--extend-ignore") + 1] == "F821,F823"
    syntax_cmd = next(cmd for cmd in captured if cmd[1:3] == ["scripts/check_syntax.py", "--paths"])
    assert syntax_cmd[3:] == ["app/core", "app/tools", "app/loop", "scripts", "tests"]
    pytest_cmds = [cmd for cmd in captured if cmd[1:3] == ["-m", "pytest"]]
    assert pytest_cmds, "Expected pytest commands to be executed"
    assert all("--no-cov" in cmd for cmd in pytest_cmds)


def test_pyproject_ruff_excludes_noise_directories():
    with open("pyproject.toml", "rb") as fh:
        config = tomllib.load(fh)

    excludes = set(config["tool"]["ruff"]["exclude"])

    expected = {".tmp", "backups", "skills"}
    assert expected.issubset(excludes)


def test_ci_ruff_rules_are_aligned_with_local_gate():
    ci = open(".github/workflows/ci.yml", encoding="utf-8").read()

    assert 'ruff check app/core app/tools app/loop app/mvp scripts tests --select E9,F63,F7,F82 --extend-ignore F821,F823' in ci
    assert 'ruff check . --select F401,F841,E722,E711,E712,E721,UP,SIM,B || true' in ci
    assert "--fix" not in ci


def test_workflows_do_not_reference_missing_paths():
    ci = open(".github/workflows/ci.yml", encoding="utf-8").read()
    build = open(".github/workflows/build-matrix.yml", encoding="utf-8").read()
    security = open(".github/workflows/security.yml", encoding="utf-8").read()

    missing_refs = [
        "tests/smoke/",
        "scripts/health-check-staging.sh",
        "scripts/health-check-production.sh",
        "scripts/rollback-staging.sh",
        "scripts/rollback-production.sh",
        "./infrastructure",
        ".zap/rules/zap-rules.tsv",
        "scripts/generate_security_dashboard.py",
    ]

    combined = "\n".join([ci, build, security])
    for ref in missing_refs:
        assert ref not in combined


def test_build_matrix_has_resilient_base_image_and_valid_replacements():
    build = open(".github/workflows/build-matrix.yml", encoding="utf-8").read()

    assert "if: always() && needs.detect-changes.outputs[matrix.service] == 'true' && (needs.build-base.result == 'success' || needs.build-base.result == 'skipped')" in build
    assert "BASE_IMAGE=${{ needs.build-base.outputs.image-digest != ''" in build
    assert "format('{0}/{1}-base:latest', env.REGISTRY, env.IMAGE_NAME)" in build
    assert "sed -i 's|asmblr/asmblr-|${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-|g' docker-compose.test.yml" in build
    assert "sed -i 's|asmblr/asmblr-|${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-|g' docker-compose.staging.yml" in build
