from pathlib import Path
from app.core.run_manager import RunManager


def test_run_manager_creates_run(tmp_path: Path):
    runs_dir = tmp_path / "runs"
    data_dir = tmp_path / "data"
    manager = RunManager(runs_dir, data_dir)
    run_id = manager.create_run("test topic")
    run = manager.get_run(run_id)
    assert run is not None
    assert Path(run["output_dir"]).exists()
