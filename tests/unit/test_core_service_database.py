import ast
from pathlib import Path


def test_core_service_database_declares_uuid_and_updated_at_column() -> None:
    module_path = Path(__file__).parents[2] / "asmblr-core" / "database.py"
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_names = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "uuid" in imported_names

    pipeline = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Pipeline"
    )
    updated_at = next(
        node
        for node in pipeline.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "updated_at" for target in node.targets)
    )
    assert isinstance(updated_at.value, ast.Call)
    assert isinstance(updated_at.value.func, ast.Name)
    assert updated_at.value.func.id == "Column"


def test_core_service_entrypoint_uses_its_local_contract_modules() -> None:
    service_dir = Path(__file__).parents[2] / "asmblr-core"
    main_source = (service_dir / "main.py").read_text(encoding="utf-8")
    pipeline_source = (service_dir / "pipeline_service.py").read_text(encoding="utf-8")

    assert "from database import get_db" in main_source
    assert "from models import PipelineCreate" in main_source
    assert "from pipeline_service import PipelineService" in main_source
    assert "from database import Pipeline, PipelineExecution" in pipeline_source
    assert "from app.core.database" not in pipeline_source
    assert "from models import (" in pipeline_source
