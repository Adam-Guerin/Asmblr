"""
Tests unitaires pour le module core.pipeline
Couvre la pipeline de génération MVP, les étapes et la gestion des erreurs
"""

import pytest
import json
from unittest.mock import patch

from app.core.pipeline import VenturePipeline
from app.core.config import Settings


class TestVenturePipeline:
    """Tests complets pour la classe VenturePipeline"""

    @pytest.fixture
    def settings(self, tmp_path):
        """Fixture pour les paramètres de test"""
        return Settings(
            runs_dir=tmp_path / "runs",
            data_dir=tmp_path / "data",
            config_dir=tmp_path / "configs",
            knowledge_dir=tmp_path / "knowledge"
        )

    @pytest.fixture
    def pipeline(self, settings):
        """Fixture pour la pipeline de test"""
        return VenturePipeline(settings)

    def test_pipeline_initialization(self, pipeline, settings):
        """Test l'initialisation de la pipeline"""
        assert pipeline.settings == settings
        assert pipeline.current_run_id is None
        assert pipeline.status == "idle"

    def test_create_run(self, pipeline):
        """Test la création d'une nouvelle exécution"""
        topic = "AI compliance for SMBs"
        run_id = pipeline.create_run(topic)
        
        assert run_id is not None
        assert pipeline.current_run_id == run_id
        assert pipeline.status == "created"
        
        # Vérification des fichiers créés
        run_dir = pipeline.settings.runs_dir / run_id
        assert run_dir.exists()
        assert (run_dir / "run_state.json").exists()
        assert (run_dir / "progress.log").exists()

    def test_create_run_with_metadata(self, pipeline):
        """Test la création avec métadonnées personnalisées"""
        topic = "Test topic"
        metadata = {"n_ideas": 5, "fast_mode": True}
        
        run_id = pipeline.create_run(topic, **metadata)
        
        run_dir = pipeline.settings.runs_dir / run_id
        state = json.loads((run_dir / "run_state.json").read_text())
        
        assert state["topic"] == topic
        assert state["n_ideas"] == 5
        assert state["fast_mode"] is True

    def test_update_status(self, pipeline):
        """Test la mise à jour du statut"""
        run_id = pipeline.create_run("test")
        
        pipeline.update_status("running")
        assert pipeline.status == "running"
        
        # Vérification dans le fichier d'état
        run_dir = pipeline.settings.runs_dir / run_id
        state = json.loads((run_dir / "run_state.json").read_text())
        assert state["status"] == "running"

    def test_get_run_state(self, pipeline):
        """Test la récupération de l'état d'exécution"""
        run_id = pipeline.create_run("test")
        pipeline.update_status("running")
        
        state = pipeline.get_run_state(run_id)
        
        assert state["topic"] == "test"
        assert state["status"] == "running"
        assert "created_at" in state
        assert "updated_at" in state

    def test_get_run_state_nonexistent(self, pipeline):
        """Test la récupération d'état pour une exécution inexistante"""
        state = pipeline.get_run_state("nonexistent")
        assert state is None

    @patch('app.core.pipeline.WebSearchAndSummarizeTool')
    @patch('app.core.pipeline.CompetitorExtractorTool')
    def test_run_pipeline_success(self, mock_comp_tool, mock_web_tool, pipeline):
        """Test l'exécution réussie de la pipeline"""
        # Mock des outils
        mock_web_tool.return_value._run.return_value = json.dumps([{
            "name": "Test Source",
            "url": "https://example.com",
            "text": "Teams struggle with compliance",
            "summary": "Compliance challenges"
        }])
        
        mock_comp_tool.return_value._run.return_value = json.dumps([{
            "product_name": "Competitor",
            "pricing": "$50/month"
        }])
        
        # Mock du LLM
        with patch('app.core.pipeline.LLMClient') as mock_llm:
            mock_llm.return_value.available.return_value = True
            mock_llm.return_value.generate.return_value = "Mock response"
            
            run_id = pipeline.create_run("AI compliance")
            
            with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
                mock_crew.return_value = {
                    "research": {"ideas": [{"name": "Idea 1"}]},
                    "analysis": {"top_idea": {"name": "Idea 1"}},
                    "prd": {"prd_markdown": "# PRD"},
                    "tech": {"tech_spec_markdown": "# Tech Spec"},
                    "growth": {"landing_dir": "landing", "content_dir": "content"}
                }
                
                result = pipeline.run(run_id)
                
                assert result["success"] is True
                assert pipeline.status == "completed"

    def test_run_pipeline_with_ollama_unavailable(self, pipeline):
        """Test le comportement quand Ollama n'est pas disponible"""
        run_id = pipeline.create_run("test")
        
        with patch('app.core.pipeline.LLMClient') as mock_llm:
            mock_llm.return_value.available.return_value = False
            
            result = pipeline.run(run_id)
            
            assert result["success"] is False
            assert "Ollama unavailable" in result["error"]
            assert pipeline.status == "failed"

    def test_run_pipeline_insufficient_data(self, pipeline):
        """Test le comportement avec des données insuffisantes"""
        run_id = pipeline.create_run("test")
        
        with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
            mock_crew.return_value = {
                "research": {"ideas": []},  # Pas d'idées
                "analysis": {},
                "prd": {},
                "tech": {},
                "growth": {}
            }
            
            result = pipeline.run(run_id)
            
            assert result["success"] is False
            assert "insufficient data" in result["error"].lower()
            assert pipeline.status == "aborted"

    def test_run_pipeline_timeout(self, pipeline):
        """Test le timeout de la pipeline"""
        run_id = pipeline.create_run("test")
        
        with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
            mock_crew.side_effect = TimeoutError("Pipeline timeout")
            
            result = pipeline.run(run_id, timeout=1)
            
            assert result["success"] is False
            assert "timeout" in result["error"].lower()
            assert pipeline.status == "failed"

    def test_resume_run(self, pipeline):
        """Test la reprise d'une exécution interrompue"""
        run_id = pipeline.create_run("test")
        pipeline.update_status("running")
        
        # Simulation d'interruption
        pipeline.status = "interrupted"
        
        with patch.object(pipeline, 'run') as mock_run:
            mock_run.return_value = {"success": True}
            
            result = pipeline.resume(run_id)
            
            assert result["success"] is True
            mock_run.assert_called_once_with(run_id)

    def test_abort_run(self, pipeline):
        """Test l'arrêt d'une exécution"""
        run_id = pipeline.create_run("test")
        pipeline.update_status("running")
        
        result = pipeline.abort(run_id)
        
        assert result["success"] is True
        assert pipeline.status == "aborted"
        
        # Vérification du fichier d'arrêt
        run_dir = pipeline.settings.runs_dir / run_id
        assert (run_dir / "abort_reason.md").exists()

    def test_get_run_artifacts(self, pipeline):
        """Test la récupération des artefacts d'une exécution"""
        run_id = pipeline.create_run("test")
        run_dir = pipeline.settings.runs_dir / run_id
        
        # Création d'artefacts de test
        (run_dir / "prd.md").write_text("# PRD Content")
        (run_dir / "tech_spec.md").write_text("# Tech Spec")
        (run_dir / "market_report.md").write_text("# Market Report")
        
        artifacts = pipeline.get_run_artifacts(run_id)
        
        assert "prd.md" in artifacts
        assert "tech_spec.md" in artifacts
        assert "market_report.md" in artifacts
        assert artifacts["prd.md"] == "# PRD Content"

    def test_list_runs(self, pipeline):
        """Test la liste des exécutions"""
        # Création de plusieurs exécutions
        run_ids = []
        for i in range(3):
            run_id = pipeline.create_run(f"test_{i}")
            run_ids.append(run_id)
            if i == 1:
                pipeline.update_status("completed")
        
        runs = pipeline.list_runs()
        
        assert len(runs) == 3
        assert all(run["run_id"] in run_ids for run in runs)
        assert any(run["status"] == "completed" for run in runs)

    def test_cleanup_old_runs(self, pipeline):
        """Test le nettoyage des anciennes exécutions"""
        # Création d'exécutions avec différentes dates
        old_run = pipeline.create_run("old")
        pipeline.update_status("completed")
        
        # Modification de la date de création
        run_dir = pipeline.settings.runs_dir / old_run
        state = json.loads((run_dir / "run_state.json").read_text())
        state["created_at"] = "2020-01-01T00:00:00"
        (run_dir / "run_state.json").write_text(json.dumps(state))
        
        new_run = pipeline.create_run("new")
        
        # Nettoyage des exécutions de plus de 1 jour
        cleaned = pipeline.cleanup_old_runs(days=1)
        
        assert old_run in cleaned
        assert new_run not in cleaned
        assert not (pipeline.settings.runs_dir / old_run).exists()
        assert (pipeline.settings.runs_dir / new_run).exists()

    def test_validate_run_integrity(self, pipeline):
        """Test la validation de l'intégrité d'une exécution"""
        run_id = pipeline.create_run("test")
        run_dir = pipeline.settings.runs_dir / run_id
        
        # Exécution complète - devrait être valide
        pipeline.update_status("completed")
        (run_dir / "prd.md").write_text("# PRD")
        (run_dir / "tech_spec.md").write_text("# Tech")
        
        integrity = pipeline.validate_run_integrity(run_id)
        assert integrity["valid"] is True
        assert integrity["missing_artifacts"] == []

    def test_validate_run_integrity_missing_files(self, pipeline):
        """Test la validation avec des fichiers manquants"""
        run_id = pipeline.create_run("test")
        pipeline.update_status("completed")
        
        # Pas de fichiers d'artefacts créés
        
        integrity = pipeline.validate_run_integrity(run_id)
        assert integrity["valid"] is False
        assert len(integrity["missing_artifacts"]) > 0

    def test_get_run_metrics(self, pipeline):
        """Test la récupération des métriques d'une exécution"""
        run_id = pipeline.create_run("test")
        run_dir = pipeline.settings.runs_dir / run_id
        
        # Création de métriques
        metrics = {
            "total_ideas": 10,
            "processing_time": 3600,
            "sources_found": 5,
            "confidence_score": 85
        }
        (run_dir / "metrics.json").write_text(json.dumps(metrics))
        
        run_metrics = pipeline.get_run_metrics(run_id)
        
        assert run_metrics["total_ideas"] == 10
        assert run_metrics["processing_time"] == 3600
        assert run_metrics["sources_found"] == 5
        assert run_metrics["confidence_score"] == 85

    def test_export_run_data(self, pipeline, tmp_path):
        """Test l'export des données d'une exécution"""
        run_id = pipeline.create_run("test")
        run_dir = pipeline.settings.runs_dir / run_id
        
        # Création de données
        (run_dir / "prd.md").write_text("# PRD")
        (run_dir / "tech_spec.md").write_text("# Tech")
        
        export_file = tmp_path / "export.zip"
        
        pipeline.export_run_data(run_id, export_file)
        
        assert export_file.exists()
        assert export_file.stat().st_size > 0
