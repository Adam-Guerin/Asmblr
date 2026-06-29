from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]


def test_ci_uses_existing_dependency_and_test_runner_paths() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    assert "pip install -r requirements/requirements.txt" in workflow
    assert "pip install -r requirements/requirements-test.txt" in workflow
    assert "python scripts/run_tests.py" in workflow
    assert "API_KEY=${{ secrets.API_KEY }}" in workflow
    assert "SERVICE_API_KEY=${{ secrets.SERVICE_API_KEY }}" in workflow


def test_build_matrix_uses_existing_docker_and_compose_paths() -> None:
    workflow = (
        REPO_ROOT / ".github" / "workflows" / "build-matrix.yml"
    ).read_text(encoding="utf-8")
    assert "file: ./deployment/Dockerfile" in workflow
    assert "deployment/docker-compose.optimized.yml" in workflow
    assert "deployment/docker-compose.staging.yml" in workflow
    assert "docker-compose --project-directory ." in workflow
    assert "service: [api-gateway, asmblr-core]" in workflow


def test_deployment_manifests_require_gateway_and_service_secrets() -> None:
    for filename in (
        "docker-compose.microservices.yml",
        "docker-compose.staging.yml",
        "docker-compose.production.yml",
    ):
        compose = (REPO_ROOT / "deployment" / filename).read_text(encoding="utf-8")
        assert "API_KEY=${API_KEY:?API_KEY is required}" in compose
        assert "SERVICE_API_KEY=${SERVICE_API_KEY:?SERVICE_API_KEY is required}" in compose
