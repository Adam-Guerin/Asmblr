"""
Tests d'intégration pour la pipeline complète Asmblr
Couvre les flux de travail end-to-end avec tous les composants
"""

import pytest
import asyncio
import json
from unittest.mock import patch

from app.core.pipeline import VenturePipeline
from app.core.config import Settings
from app.mvp.builder import MVPBuilder


class TestPipelineIntegration:
    """Tests d'intégration pour la pipeline complète"""

    @pytest.fixture
    def settings(self, temp_dir):
        """Configuration pour les tests d'intégration"""
        return Settings(
            runs_dir=temp_dir / "runs",
            data_dir=temp_dir / "data",
            config_dir=temp_dir / "configs",
            knowledge_dir=temp_dir / "knowledge"
        )

    @pytest.fixture
    def pipeline(self, settings):
        """Pipeline pour les tests"""
        return VenturePipeline(settings)

    @pytest.mark.integration
    @pytest.mark.slow
    async def test_full_pipeline_success(self, pipeline, sample_market_data, sample_ideas):
        """Test complet de la pipeline avec succès"""
        # Mock des composants externes
        with patch('app.core.pipeline.LLMClient') as mock_llm:
            mock_llm.return_value.available.return_value = True
            mock_llm.return_value.generate.return_value = "Mock response"
            
            with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
                mock_crew.return_value = {
                    "research": sample_market_data,
                    "analysis": {
                        "ideas": sample_ideas,
                        "scores": [
                            {"name": "AI Compliance Checker", "score": 85, "rationale": "Strong market need"},
                            {"name": "Compliance Chatbot", "score": 75, "rationale": "Good fit"}
                        ],
                        "top_idea": sample_ideas[0]
                    },
                    "prd": {"prd_markdown": "# PRD\n\n## Product Overview"},
                    "tech": {"tech_spec_markdown": "# Tech Spec\n\n## Architecture"},
                    "growth": {
                        "landing_dir": "landing_page",
                        "content_dir": "content_pack"
                    }
                }
                
                # Création et exécution
                run_id = pipeline.create_run("AI Compliance Platform")
                result = pipeline.run(run_id)
                
                # Vérifications
                assert result["success"] is True
                assert pipeline.status == "completed"
                
                # Vérification des artefacts
                artifacts = pipeline.get_run_artifacts(run_id)
                assert "prd.md" in artifacts
                assert "tech_spec.md" in artifacts
                assert "market_report.md" in artifacts
                
                # Vérification des métriques
                metrics = pipeline.get_run_metrics(run_id)
                assert metrics["total_ideas"] == 2
                assert metrics["confidence_score"] > 0

    @pytest.mark.integration
    async def test_pipeline_with_mvp_build(self, settings, sample_ideas):
        """Test l'intégration pipeline + build MVP"""
        pipeline = VenturePipeline(settings)
        
        # Mock de la pipeline
        with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
            mock_crew.return_value = {
                "research": {"ideas": sample_ideas},
                "analysis": {"top_idea": sample_ideas[0]},
                "prd": {"prd_markdown": "# PRD"},
                "tech": {"tech_spec_markdown": "# Tech Spec"},
                "growth": {"landing_dir": "landing", "content_dir": "content"}
            }
            
            # Exécution de la pipeline
            run_id = pipeline.create_run("Test MVP Integration")
            pipeline_result = pipeline.run(run_id)
            
            assert pipeline_result["success"] is True
            
            # Build MVP
            builder = MVPBuilder(settings)
            
            with patch('app.mvp.builder.check_ollama', return_value={}):
                mvp_result = builder.build_from_run(run_id, max_fix_iter=1)
                
                assert mvp_result.success
                assert mvp_result.run_dir.exists()
                assert (mvp_result.run_dir / "mvp_repo").exists()
                assert (mvp_result.run_dir / "mvp_build_summary.md").exists()

    @pytest.mark.integration
    async def test_pipeline_error_recovery(self, pipeline):
        """Test la récupération d'erreur dans la pipeline"""
        run_id = pipeline.create_run("Error Recovery Test")
        
        # Simulation d'une erreur temporaire
        with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
            mock_crew.side_effect = [
                Exception("Temporary failure"),  # Premier appel échoue
                {  # Deuxième appel réussit
                    "research": {"ideas": [{"name": "Test Idea"}]},
                    "analysis": {"top_idea": {"name": "Test Idea"}},
                    "prd": {"prd_markdown": "# PRD"},
                    "tech": {"tech_spec_markdown": "# Tech"},
                    "growth": {"landing_dir": "landing", "content_dir": "content"}
                }
            ]
            
            # Tentative de récupération
            result = pipeline.resume(run_id)
            
            assert result["success"] is True
            assert pipeline.status == "completed"

    @pytest.mark.integration
    async def test_pipeline_insufficient_data_abort(self, pipeline):
        """Test l'arrêt pour données insuffisantes"""
        run_id = pipeline.create_run("Insufficient Data Test")
        
        with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
            mock_crew.return_value = {
                "research": {"ideas": [], "sources": []},  # Données insuffisantes
                "analysis": {},
                "prd": {},
                "tech": {},
                "growth": {}
            }
            
            result = pipeline.run(run_id)
            
            assert result["success"] is False
            assert "insufficient" in result["error"].lower()
            assert pipeline.status == "aborted"
            
            # Vérification qu'aucun artefact de produit n'a été créé
            run_dir = pipeline.settings.runs_dir / run_id
            assert not (run_dir / "prd.md").exists()
            assert not (run_dir / "tech_spec.md").exists()

    @pytest.mark.integration
    async def test_pipeline_concurrent_runs(self, settings):
        """Test l'exécution concurrente de multiples pipelines"""
        pipelines = [VenturePipeline(settings) for _ in range(3)]
        
        async def run_pipeline(pipeline, topic):
            with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
                mock_crew.return_value = {
                    "research": {"ideas": [{"name": f"Idea for {topic}"}]},
                    "analysis": {"top_idea": {"name": f"Top Idea for {topic}"}},
                    "prd": {"prd_markdown": f"# PRD for {topic}"},
                    "tech": {"tech_spec_markdown": f"# Tech for {topic}"},
                    "growth": {"landing_dir": "landing", "content_dir": "content"}
                }
                
                run_id = pipeline.create_run(topic)
                return pipeline.run(run_id)
        
        # Exécution concurrente
        tasks = [
            run_pipeline(pipeline, f"Topic {i}")
            for i, pipeline in enumerate(pipelines)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Vérifications
        assert len(results) == 3
        assert all(result["success"] for result in results)
        
        # Vérification que les runs sont distincts
        run_ids = [pipeline.current_run_id for pipeline in pipelines]
        assert len(set(run_ids)) == 3

    @pytest.mark.integration
    async def test_pipeline_quality_gates(self, pipeline, sample_ideas):
        """Test les portes de qualité de la pipeline"""
        run_id = pipeline.create_run("Quality Gates Test")
        
        with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
            # Simulation d'une réponse avec faible confiance
            mock_crew.return_value = {
                "research": {"ideas": sample_ideas, "sources": []},  # Peu de sources
                "analysis": {
                    "ideas": sample_ideas,
                    "scores": [
                        {"name": "AI Compliance Checker", "score": 25, "rationale": "Weak signal"}  # Score faible
                    ],
                    "top_idea": sample_ideas[0]
                },
                "prd": {"prd_markdown": "# PRD"},
                "tech": {"tech_spec_markdown": "# Tech"},
                "growth": {"landing_dir": "landing", "content_dir": "content"}
            }
            
            result = pipeline.run(run_id)
            
            # La pipeline devrait échouer à cause du faible score
            assert result["success"] is False
            assert "confidence" in result["error"].lower() or "quality" in result["error"].lower()

    @pytest.mark.integration
    async def test_pipeline_data_source_tracking(self, pipeline):
        """Test le suivi des sources de données"""
        run_id = pipeline.create_run("Data Source Tracking Test")
        
        with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
            mock_crew.return_value = {
                "research": {
                    "ideas": [{"name": "Test Idea"}],
                    "sources": [{"name": "Real Source", "url": "https://real.com"}],
                    "data_source": "real"  # Marquage de source réelle
                },
                "analysis": {"top_idea": {"name": "Test Idea"}},
                "prd": {"prd_markdown": "# PRD"},
                "tech": {"tech_spec_markdown": "# Tech"},
                "growth": {"landing_dir": "landing", "content_dir": "content"}
            }
            
            result = pipeline.run(run_id)
            
            assert result["success"] is True
            
            # Vérification du tracking des sources
            run_dir = pipeline.settings.runs_dir / run_id
            data_source_file = run_dir / "data_source.json"
            assert data_source_file.exists()
            
            data_source = json.loads(data_source_file.read_text())
            assert data_source["data_source"] == "real"

    @pytest.mark.integration
    async def test_pipeline_run_integrity_validation(self, pipeline):
        """Test la validation d'intégrité des exécutions"""
        run_id = pipeline.create_run("Integrity Validation Test")
        
        with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
            mock_crew.return_value = {
                "research": {"ideas": [{"name": "Test Idea"}]},
                "analysis": {"top_idea": {"name": "Test Idea"}},
                "prd": {"prd_markdown": "# PRD"},
                "tech": {"tech_spec_markdown": "# Tech"},
                "growth": {"landing_dir": "landing", "content_dir": "content"}
            }
            
            result = pipeline.run(run_id)
            assert result["success"] is True
            
            # Validation de l'intégrité
            integrity = pipeline.validate_run_integrity(run_id)
            assert integrity["valid"] is True
            assert len(integrity["missing_artifacts"]) == 0

    @pytest.mark.integration
    async def test_pipeline_metrics_collection(self, pipeline):
        """Test la collection de métriques détaillées"""
        run_id = pipeline.create_run("Metrics Collection Test")
        
        with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
            mock_crew.return_value = {
                "research": {
                    "ideas": [{"name": "Idea 1"}, {"name": "Idea 2"}],
                    "sources": [{"name": "Source 1"}, {"name": "Source 2"}],
                    "processing_time": 1200
                },
                "analysis": {
                    "top_idea": {"name": "Idea 1"},
                    "scoring_time": 300
                },
                "prd": {"prd_markdown": "# PRD", "generation_time": 600},
                "tech": {"tech_spec_markdown": "# Tech", "generation_time": 400},
                "growth": {"landing_dir": "landing", "content_dir": "content", "generation_time": 500}
            }
            
            result = pipeline.run(run_id)
            assert result["success"] is True
            
            # Vérification des métriques
            metrics = pipeline.get_run_metrics(run_id)
            assert "total_ideas" in metrics
            assert "processing_time" in metrics
            assert "confidence_score" in metrics
            assert metrics["total_ideas"] == 2

    @pytest.mark.integration
    async def test_pipeline_export_import(self, pipeline, temp_dir):
        """Test l'export et import des données de pipeline"""
        run_id = pipeline.create_run("Export Import Test")
        
        with patch('app.core.pipeline.run_crewai_pipeline') as mock_crew:
            mock_crew.return_value = {
                "research": {"ideas": [{"name": "Test Idea"}]},
                "analysis": {"top_idea": {"name": "Test Idea"}},
                "prd": {"prd_markdown": "# PRD"},
                "tech": {"tech_spec_markdown": "# Tech"},
                "growth": {"landing_dir": "landing", "content_dir": "content"}
            }
            
            result = pipeline.run(run_id)
            assert result["success"] is True
            
            # Export
            export_file = temp_dir / "export.zip"
            pipeline.export_run_data(run_id, export_file)
            assert export_file.exists()
            
            # Import dans une nouvelle pipeline
            new_pipeline = VenturePipeline(pipeline.settings)
            import_result = new_pipeline.import_run_data(export_file)
            
            assert import_result["success"] is True
            assert new_pipeline.current_run_id != run_id  # Nouveau run ID
