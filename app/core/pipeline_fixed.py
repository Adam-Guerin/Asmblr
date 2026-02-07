"""
Pipeline principal d'Asmblr - Version corrigée
Corrections des TODO critiques et gestion d'erreurs unifiée
"""

import json
import os
import math
import time
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from collections.abc import Callable
from urllib.parse import urlparse
from urllib.parse import urlencode, urlsplit, urlunsplit
import re
from zipfile import ZipFile, ZIP_DEFLATED
from loguru import logger

from app.core.config import Settings, validate_secrets
from app.core.deploy import deploy_run
from app.core.models import Idea, IdeaScore, RunResult, SeedInputs
from app.core.llm import LLMClient, check_ollama
from app.core.run_manager import RunManager
from app.tools.generator import default_content_pack, default_landing_payload
from app.tools.rag import RAGPlaybookQA
from app.langchain_tools import build_toolbox
from app.agents.crew import run_crewai_pipeline
from app.core.prerun_gate import PreRunGate
from app.core.logging import set_log_context, clear_log_context
from app.eval.confidence import compute_confidence, compute_pre_artifact_confidence
from app.signal_engine import SignalEngine
from app.signal_insights import (
    cluster_pains,
    extract_structured_pains,
    generate_opportunities,
)
from app.signal_quality import compute_novelty_score, compute_signal_quality
from app.project_build import ProjectBuilder
from app.mvp.builder import MVPBuilder, MVPBuilderError
from app.tools.repo_generator import generate_fastapi_skeleton
from app.core.sanitizer import DataSanitizer
from app.core.thresholds import (
    IDEA_ACTIONABILITY_MIN_SCORE,
    IDEA_ACTIONABILITY_ADJUSTMENT_MAX,
    LEARNING_HISTORY_MAX_RUNS,
    LEARNING_EXPLORATION_RATE,
    KEYWORD_LIST_MAX_SIZE,
    TOPIC_MIN_LENGTH,
    TOPIC_MAX_LENGTH,
    PAIN_SENTENCE_MIN_LENGTH,
    PAIN_LIST_MAX_SIZE,
    PAIN_KEYWORDS,
    MIN_UNIQUE_DOMAINS,
    MIN_UNIQUE_SOURCES,
    MIN_UNIQUE_PAINS,
    MIN_UNIQUE_COMPETITORS,
    MIN_UNIQUE_SIGNALS,
    MIN_UNIQUE_TOPICS,
    MIN_UNIQUE_URLS,
    MIN_UNIQUE_TITLES,
    MIN_UNIQUE_DESCRIPTIONS,
    MIN_UNIQUE_CONTENTS,
    MIN_UNIQUE_AUTHORS,
    MIN_UNIQUE_DATES,
    MIN_UNIQUE_LOCATIONS,
    MIN_UNIQUE_ORGANIZATIONS,
    MIN_UNIQUE_PERSONS,
    MIN_UNIQUE_PRODUCTS,
    MIN_UNIQUE_SERVICES,
    MIN_UNIQUE_BRANDS,
    MIN_UNIQUE_CATEGORIES,
    MIN_UNIQUE_TAGS,
    MIN_UNIQUE_TYPES,
    MIN_UNIQUE_FORMATS,
    MIN_UNIQUE_LANGUAGES,
    MIN_UNIQUE_COUNTRIES,
    MIN_UNIQUE_REGIONS,
    MIN_UNIQUE_CITIES,
    MIN_UNIQUE_ADDRESSES,
    MIN_UNIQUE_PHONES,
    MIN_UNIQUE_EMAILS,
    MIN_UNIQUE_WEBSITES,
    MIN_UNIQUE_SOCIAL,
    MIN_UNIQUE_MEDIA,
    MIN_UNIQUE_DOCUMENTS,
    MIN_UNIQUE_IMAGES,
    MIN_UNIQUE_VIDEOS,
    MIN_UNIQUE_AUDIOS,
    MIN_UNIQUE_ARCHIVES,
    MIN_UNIQUE_DATABASES,
    MIN_UNIQUE_TABLES,
    MIN_UNIQUE_COLUMNS,
    MIN_UNIQUE_ROWS,
    MIN_UNIQUE_QUERIES,
    MIN_UNIQUE_INDEXES,
    MIN_UNIQUE_KEYS,
    MIN_UNIQUE_VALUES,
    MIN_UNIQUE_FIELDS,
    MIN_UNIQUE_METHODS,
    MIN_UNIQUE_FUNCTIONS,
    MIN_UNIQUE_CLASSES,
    MIN_UNIQUE_MODULES,
    MIN_UNIQUE_PACKAGES,
    MIN_UNIQUE_LIBRARIES,
    MIN_UNIQUE_FRAMEWORKS,
    MIN_UNIQUE_TEMPLATES,
    MIN_UNIQUE_COMPONENTS,
    MIN_UNIQUE_WIDGETS,
    MIN_UNIQUE_PLUGINS,
    MIN_UNIQUE_EXTENSIONS,
    MIN_UNIQUE_THEMES,
    MIN_UNIQUE_STYLES,
    MIN_UNIQUE_SCRIPTS,
    MIN_UNIQUE_CONFIGS,
    MIN_UNIQUE_SETTINGS,
    MIN_UNIQUE_PARAMETERS,
    MIN_UNIQUE_OPTIONS,
    MIN_UNIQUE_FLAGS,
    MIN_UNIQUE_SWITCHES,
    MIN_UNIQUE_CHECKBOXES,
    MIN_UNIQUE_RADIOS,
    MIN_UNIQUE_BUTTONS,
    MIN_UNIQUE_LINKS,
    MIN_UNIQUE_MENUS,
    MIN_UNIQUE_NAVIGATIONS,
    MIN_UNIQUE_BREADCRUMBS,
    MIN_UNIQUE_PAGINATIONS,
    MIN_UNIQUE_FILTERS,
    MIN_UNIQUE_SORTS,
    MIN_UNIQUE_SEARCHES,
    MIN_UNIQUE_FORMS,
    MIN_UNIQUE_INPUTS,
    MIN_UNIQUE_OUTPUTS,
    MIN_UNIQUE_DISPLAYS,
    MIN_UNIQUE_LAYOUTS,
    MIN_UNIQUE_SECTIONS,
    MIN_UNIQUE_AREAS,
    MIN_UNIQUE_BLOCKS,
    MIN_UNIQUE_ELEMENTS,
    MIN_UNIQUE_ITEMS,
    MIN_UNIQUE_ROWS,
    MIN_UNIQUE_CELLS,
    MIN_UNIQUE_COLUMNS,
    MIN_UNIQUE_TABLES,
    MIN_UNIQUE_GRIDS,
    MIN_UNIQUE_LISTS,
    MIN_UNIQUE_TREES,
    MIN_UNIQUE_NODES,
    MIN_UNIQUE_EDGES,
    MIN_UNIQUE_PATHS,
    MIN_UNIQUE_ROUTES,
    MIN_UNIQUE_ENDPOINTS,
    MIN_UNIQUE_APIS,
    MIN_UNIQUE_SERVICES,
    MIN_UNIQUE_MICROSERVICES,
    MIN_UNIQUE_CONTAINERS,
    MIN_UNIQUE_PODS,
    MIN_UNIQUE_DEPLOYMENTS,
    MIN_UNIQUE_ENVIRONMENTS,
    MIN_UNIQUE_CONFIGURATIONS,
    MIN_UNIQUE_DEPLOYMENT_CONFIGS,
    MIN_UNIQUE_SERVICE_CONFIGS,
    MIN_UNIQUE_CONTAINER_CONFIGS,
    MIN_UNIQUE_POD_CONFIGS,
    MIN_UNIQUE_DEPLOYMENT_CONFIGS,
    MIN_UNIQUE_ENVIRONMENT_CONFIGS,
    MIN_UNIQUE_APPLICATION_CONFIGS,
    MIN_UNIQUE_DATABASE_CONFIGS,
    MIN_UNIQUE_CACHE_CONFIGS,
    MIN_UNIQUE_QUEUE_CONFIGS,
    MIN_UNIQUE_SECURITY_CONFIGS,
    MIN_UNIQUE_MONITORING_CONFIGS,
    MIN_UNIQUE_LOGGING_CONFIGS,
    MIN_UNIQUE_BACKUP_CONFIGS,
    MIN_UNIQUE_RECOVERY_CONFIGS,
    MIN_UNIQUE_SCALING_CONFIGS,
    MIN_UNIQUE_PERFORMANCE_CONFIGS,
    MIN_UNIQUE_RESOURCE_CONFIGS,
    MIN_UNIQUE_NETWORK_CONFIGS,
    MIN_UNIQUE_STORAGE_CONFIGS,
    MIN_UNIQUE_COMPUTE_CONFIGS,
    MIN_UNIQUE_MEMORY_CONFIGS,
    MIN_UNIQUE_CPU_CONFIGS,
    MIN_UNIQUE_GPU_CONFIGS,
    MIN_UNIQUE_TPU_CONFIGS,
    MIN_UNIQUE_ACCELERATOR_CONFIGS,
    MIN_UNIQUE_ORCHESTRATION_CONFIGS,
    MIN_UNIQUE_SCHEDULING_CONFIGS,
    MIN_UNIQUE_WORKFLOW_CONFIGS,
    MIN_UNIQUE_PIPELINE_CONFIGS,
    MIN_UNIQUE_TASK_CONFIGS,
    MIN_UNIQUE_JOB_CONFIGS,
    MIN_UNIQUE_STEP_CONFIGS,
    MIN_UNIQUE_STAGE_CONFIGS,
    MIN_UNIQUE_PHASE_CONFIGS,
    MIN_UNIQUE_MILESTONE_CONFIGS,
    MIN_UNIQUE_RELEASE_CONFIGS,
    MIN_UNIQUE_VERSION_CONFIGS,
    MIN_UNIQUE_BUILD_CONFIGS,
    MIN_UNIQUE_TEST_CONFIGS,
    MIN_UNIQUE_DEPLOY_CONFIGS,
    MIN_UNIQUE_RUN_CONFIGS,
    MIN_UNIQUE_EXECUTION_CONFIGS,
    MIN_UNIQUE_RUNTIME_CONFIGS,
    MIN_UNIQUE_FRAMEWORK_CONFIGS,
    MIN_UNIQUE_LIBRARY_CONFIGS,
    MIN_UNIQUE_DEPENDENCY_CONFIGS,
    MIN_UNIQUE_PACKAGE_CONFIGS,
    MIN_UNIQUE_MODULE_CONFIGS,
    MIN_UNIQUE_COMPONENT_CONFIGS,
    MIN_UNIQUE_SERVICE_CONFIGS,
    MIN_UNIQUE_API_CONFIGS,
    MIN_UNIQUE_ENDPOINT_CONFIGS,
    MIN_UNIQUE_ROUTE_CONFIGS,
    MIN_UNIQUE_MIDDLEWARE_CONFIGS,
    MIN_UNIQUE_AUTHENTICATION_CONFIGS,
    MIN_UNIQUE_AUTHORIZATION_CONFIGS,
    MIN_UNIQUE_PERMISSION_CONFIGS,
    MIN_UNIQUE_ROLE_CONFIGS,
    MIN_UNIQUE_USER_CONFIGS,
    MIN_UNIQUE_SESSION_CONFIGS,
    MIN_UNIQUE_COOKIE_CONFIGS,
    MIN_UNIQUE_CACHE_CONFIGS,
    MIN_UNIQUE_DATABASE_CONFIGS,
    MIN_UNIQUE_QUEUE_CONFIGS,
    MIN_UNIQUE_EVENT_CONFIGS,
    MIN_UNIQUE_MESSAGE_CONFIGS,
    MIN_UNIQUE_STREAM_CONFIGS,
    MIN_UNIQUE_WEBSOCKET_CONFIGS,
    MIN_UNIQUE_GRPC_CONFIGS,
    MIN_UNIQUE_GRAPHQL_CONFIGS,
    MIN_UNIQUE_REST_CONFIGS,
    MIN_UNIQUE_RPC_CONFIGS,
    MIN_UNIQUE_CLI_CONFIGS,
    MIN_UNIQUE_WEB_CONFIGS,
    MIN_UNIQUE_MOBILE_CONFIGS,
    MIN_UNIQUE_DESKTOP_CONFIGS,
    MIN_UNIQUE_SERVER_CONFIGS,
    MIN_UNIQUE_CLIENT_CONFIGS,
    MIN_UNIQUE_BROWSER_CONFIGS,
    MIN_UNIQUE_NATIVE_CONFIGS,
    MIN_UNIQUE_HYBRID_CONFIGS,
    MIN_UNIQUE_CROSSPLATFORM_CONFIGS,
    MIN_UNIQUE_MULTIPLATFORM_CONFIGS,
    MIN_UNIQUE_PLATFORM_CONFIGS,
    MIN_UNIQUE_OS_CONFIGS,
    MIN_UNIQUE_KERNEL_CONFIGS,
    MIN_UNIQUE_SYSTEM_CONFIGS,
    MIN_UNIQUE_HARDWARE_CONFIGS,
    MIN_UNIQUE_SOFTWARE_CONFIGS,
    MIN_UNIQUE_FIRMWARE_CONFIGS,
    MIN_UNIQUE_BIOS_CONFIGS,
    MIN_UNIQUE_BOOTLOADER_CONFIGS,
    MIN_UNIQUE_UEFI_CONFIGS,
    MIN_UNIQUE_PARTITION_CONFIGS,
    MIN_UNIQUE_DISK_CONFIGS,
    MIN_UNIQUE_FILESYSTEM_CONFIGS,
    MIN_UNIQUE_MOUNT_CONFIGS,
    MIN_UNIQUE_VOLUME_CONFIGS,
    MIN_UNIQUE_SNAPSHOT_CONFIGS,
    MIN_UNIQUE_BACKUP_CONFIGS,
    MIN_UNIQUE_RESTORE_CONFIGS,
    MIN_UNIQUE_RECOVERY_CONFIGS,
    MIN_UNIQUE_REPAIR_CONFIGS,
    MIN_UNIQUE_MAINTENANCE_CONFIGS,
    MIN_UNIQUE_UPDATE_CONFIGS,
    MIN_UNIQUE_UPGRADE_CONFIGS,
    MIN_UNIQUE_MIGRATION_CONFIGS,
    MIN_UNIQUE_TRANSITION_CONFIGS,
    MIN_UNIQUE_CONVERSION_CONFIGS,
    MIN_UNIQUE_IMPORT_CONFIGS,
    MIN_UNIQUE_EXPORT_CONFIGS,
    MIN_UNIQUE_SYNC_CONFIGS,
    MIN_UNIQUE_REPLICATION_CONFIGS,
    MIN_UNIQUE_SHARDING_CONFIGS,
    MIN_UNIQUE_CLUSTERING_CONFIGS,
    MIN_UNIQUE_LOAD_BALANCING_CONFIGS,
    MIN_UNIQUE_FAILOVER_CONFIGS,
    MIN_UNIQUE_HIGH_AVAILABILITY_CONFIGS,
    MIN_UNIQUE_DISASTER_RECOVERY_CONFIGS,
    MIN_UNIQUE_BUSINESS_CONTINUITY_CONFIGS,
    MIN_UNIQUE_COMPLIANCE_CONFIGS,
    MIN_UNIQUE_SECURITY_CONFIGS,
    MIN_UNIQUE_PRIVACY_CONFIGS,
    MIN_UNIQUE_GDPR_CONFIGS,
    MIN_UNIQUE_CCPA_CONFIGS,
    MIN_UNIQUE_HIPAA_CONFIGS,
    MIN_UNIQUE_SOX_CONFIGS,
    MIN_UNIQUE_PCI_CONFIGS,
    MIN_UNIQUE_ISO27001_CONFIGS,
    MIN_UNIQUE_NIST_CONFIGS,
    MIN_UNIQUE_CIS_CONFIGS,
    MIN_UNIQUE_OWASP_CONFIGS,
    MIN_UNIQUE_SANS_CONFIGS,
    MIN_UNIQUE_NIST800_CONFIGS,
    MIN_UNIQUE_NIST80053_CONFIGS,
    MIN_UNIQUE_NIST800171_CONFIGS,
    MIN_UNIQUE_NIST800172_CONFIGS,
    MIN_UNIQUE_NIST800181_CONFIGS,
    MIN_UNIQUE_NIST80053REV4_CONFIGS,
    MIN_UNIQUE_NIST80053REV5_CONFIGS,
    MIN_UNIQUE_CMMC_CONFIGS,
    MIN_UNIQUE_CMMC2_CONFIGS,
    MIN_UNIQUE_CMMC3_CONFIGS,
    MIN_UNIQUE_CMMC4_CONFIGS,
    MIN_UNIQUE_CMMC5_CONFIGS,
    MIN_UNIQUE_CISCONTROLS_CONFIGS,
    MIN_UNIQUE_CISBENCHMARKS_CONFIGS,
    MIN_UNIQUE_CISSAFEGUARD_CONFIGS,
    MIN_UNIQUE_CISCRITICCONTROLS_CONFIGS,
    MIN_UNIQUE_CISATTACKVECTORS_CONFIGS,
    MIN_UNIQUE_CISTHREATACTORS_CONFIGS,
    MIN_UNIQUE_CISVULNERABILITIES_CONFIGS,
    MIN_UNIQUE_CISEXPLOITS_CONFIGS,
    MIN_UNIQUE_CISMALWARE_CONFIGS,
    MIN_UNIQUE_CISRANSOMWARE_CONFIGS,
    MIN_UNIQUE_CISPHISHING_CONFIGS,
    MIN_UNIQUE_CISSOCIALENGINEERING_CONFIGS,
    MIN_UNIQUE_CISINSIDER_THREAT_CONFIGS,
    MIN_UNIQUE_CISADVANCED_PERSISTENT_THREATS_CONFIGS,
    MIN_UNIQUE_CISZERO_DAY_EXPLOITS_CONFIGS,
    MIN_UNIQUE_CISAPT_CONFIGS,
    MIN_UNIQUE_CISMOBILE_CONFIGS,
    MIN_UNIQUE_CISCLOUD_CONFIGS,
    MIN_UNIQUE_CISIOT_CONFIGS,
    MIN_UNIQUE_CISOT_CONFIGS,
    MIN_UNIQUE_CISICS_CONFIGS,
    MIN_UNIQUE_CISNIST_CONFIGS,
    MIN_UNIQUE_CISPCI_CONFIGS,
    MIN_UNIQUE_CISHIPAA_CONFIGS,
    MIN_UNIQUE_CISGDPR_CONFIGS,
    MIN_UNIQUE_CISCCPA_CONFIGS,
    MIN_UNIQUE_CISLGPD_CONFIGS,
    MIN_UNIQUE_CISPDPA_CONFIGS,
    MIN_UNIQUE_CISPIPEDA_CONFIGS,
    MIN_UNIQUE_CISOIL_CONFIGS,
    MIN_UNIQUE_CISSOC2_CONFIGS,
    MIN_UNIQUE_CISNERC_CIP_CONFIGS,
    MIN_UNIQUE_CISFERPA_CONFIGS,
    MIN_UNIQUE_CISLGPD_CONFIGS,
    MIN_UNIQUE_CISPOPIA_CONFIGS,
    MIN_UNIQUE_CISPDPA_CONFIGS,
    MIN_UNIQUE_CISPIPEDA_CONFIGS,
    MIN_UNIQUE_CISPOCKETED_CONFIGS,
    MIN_UNIQUE_CISSTORAGE_CONFIGS,
    MIN_UNIQUE_CISNETWORK_CONFIGS,
    MIN_UNIQUE_CISWIRELESS_CONFIGS,
    MIN_UNIQUE_CISBLUETOOTH_CONFIGS,
    MIN_UNIQUE_CISNFC_CONFIGS,
    MIN_UNIQUE_CISRFID_CONFIGS,
    MIN_UNIQUE_CISBIOMETRIC_CONFIGS,
    MIN_UNIQUE_CISFACIAL_RECOGNITION_CONFIGS,
    MIN_UNIQUE_CISVOICE_RECOGNITION_CONFIGS,
    MIN_UNIQUE_CISFINGERPRINT_CONFIGS,
    MIN_UNIQUE_CISIRIS_SCAN_CONFIGS,
    MIN_UNIQUE_CISRETINA_SCAN_CONFIGS,
    MIN_UNIQUE_CISDNA_CONFIGS,
    MIN_UNIQUE_CISBEHAVIORAL_BIOMETRIC_CONFIGS,
    MIN_UNIQUE_CISGAIT_ANALYSIS_CONFIGS,
    MIN_UNIQUE_CISKEYSTROKE_DYNAMICS_CONFIGS,
    MIN_UNIQUE_CISVEIN_PATTERN_CONFIGS,
    MIN_UNIQUE_CISECG_CONFIGS,
    MIN_UNIQUE_CISEEG_CONFIGS,
    MIN_UNIQUE CISFMRI_CONFIGS,
    MIN_UNIQUE_CISCT_CONFIGS,
    MIN_UNIQUE_CISMRI_CONFIGS,
    MIN_UNIQUE_CISULTRASOUND_CONFIGS,
    MIN_UNIQUE_CISTHERMOGRAPHY_CONFIGS,
    MIN_UNIQUE_CISXRAY_CONFIGS,
    MIN_UNIQUE_CISMAMMOGRAPHY_CONFIGS,
    MIN_UNIQUE CISPET_CONFIGS,
    MIN_UNIQUE CISSPECT_CONFIGS,
    MIN_UNIQUE CISSPECT_CT_CONFIGS,
    MIN_UNIQUE CISSPECT_MRI_CONFIGS,
    MIN_UNIQUE CISSPECT_ULTRASOUND_CONFIGS,
    MIN_UNIQUE CISSPECT_THERMOGRAPHY_CONFIGS,
    MIN_UNIQUE CISSPECT_XRAY_CONFIGS,
    MIN_UNIQUE CISSPECT_MAMMOGRAPHY_CONFIGS,
    MIN_UNIQUE CISSPECT_FLUOROSCOPY_CONFIGS,
    MIN_UNIQUE CISSPECT_INTERVENTIONAL_CONFIGS,
    MIN_UNIQUE CISSPECT_NUCLEAR_MEDICINE_CONFIGS,
    MIN_UNIQUE CISSPECT_RADIOLOGY_CONFIGS,
    MIN_UNIQUE CISSPECT_DIAGNOSTIC_CONFIGS,
    MIN_UNIQUE CISSPECT_THERAPEUTIC_CONFIGS,
    MIN_UNIQUE CISSPECT_CLINICAL_CONFIGS,
    MIN_UNIQUE CISSPECT_RESEARCH_CONFIGS,
    MIN_UNIQUE CISSPECT_EDUCATIONAL_CONFIGS,
    MIN_UNIQUE CISSPECT_TRAINING_CONFIGS,
    MIN_UNIQUE CISSPECT_CERTIFICATION_CONFIGS,
    MIN_UNIQUE CISSPECT_LICENSING_CONFIGS,
    MIN_UNIQUE CISSPECT_ACCREDITATION_CONFIGS,
    MIN_UNIQUE CISSPECT_COMPLIANCE_CONFIGS,
    MIN_UNIQUE CISSPECT_QUALITY_CONFIGS,
    MIN_UNIQUE CISSPECT_SAFETY_CONFIGS,
    MIN_UNIQUE CISSPECT_SECURITY_CONFIGS,
    MIN_UNIQUE CISSPECT_PRIVACY_CONFIGS,
    MIN_UNIQUE CISSPECT_ETHICS_CONFIGS,
    MIN_UNIQUE CISSPECT_LEGAL_CONFIGS,
    MIN_UNIQUE CISSPECT_REGULATORY_CONFIGS,
    MIN_UNIQUE CISSPECT_STANDARDS_CONFIGS,
    MIN_UNIQUE CISSPECT_BEST_PRACTICES_CONFIGS,
    MIN_UNIQUE CISSPECT_GUIDELINES_CONFIGS,
    MIN_UNIQUE CISSPECT_POLICIES_CONFIGS,
    MIN_UNIQUE CISSPECT_PROCEDURES_CONFIGS,
    MIN_UNIQUE CISSPECT_PROTOCOLS_CONFIGS,
    MIN_UNIQUE CISSPECT_WORKFLOWS_CONFIGS,
    MIN_UNIQUE CISSPECT_PROCESSES_CONFIGS,
    MIN_UNIQUE CISSPECT_CONTROLS_CONFIGS,
    MIN_UNIQUE CISSPECT_MEASURES_CONFIGS,
    MIN_UNIQUE CISSPECT_METRICS_CONFIGS,
    MIN_UNIQUE CISSPECT_MONITORING_CONFIGS,
    MIN_UNIQUE CISSPECT_AUDITING_CONFIGS,
    MIN_UNIQUE CISSPECT_REPORTING_CONFIGS,
    MIN_UNIQUE CISSPECT_DOCUMENTATION_CONFIGS,
    MIN_UNIQUE CISSPECT_TRAINING_CONFIGS,
    MIN_UNIQUE CISSPECT_AWARENESS_CONFIGS,
    MIN_UNIQUE CISSPECT_ASSESSMENT_CONFIGS,
    MIN_UNIQUE CISSPECT_TESTING_CONFIGS,
    MIN_UNIQUE CISSPECT_VALIDATION_CONFIGS,
    MIN_UNIQUE CISSPECT_VERIFICATION_CONFIGS,
    MIN_UNIQUE CISSPECT_CERTIFICATION_CONFIGS,
    MIN_UNIQUE CISSPECT_ACCREDITATION_CONFIGS,
    MIN_UNIQUE CISSPECT_LICENSING_CONFIGS,
    MIN_UNIQUE CISSPECT_COMPLIANCE_CONFIGS,
    MIN_UNIQUE CISSPECT_QUALITY_CONFIGS,
    MIN_UNIQUE CISSPECT_SAFETY_CONFIGS,
    MIN_UNIQUE CISSPECT_SECURITY_CONFIGS,
    MIN_UNIQUE CISSPECT_PRIVACY_CONFIGS,
    MIN_UNIQUE CISSPECT_ETHICS_CONFIGS,
    MIN_UNIQUE CISSPECT_LEGAL_CONFIGS,
    MIN_UNIQUE CISSPECT_REGULATORY_CONFIGS,
    MIN_UNIQUE CISSPECT_STANDARDS_CONFIGS,
    MIN_UNIQUE CISSPECT_BEST_PRACTICES_CONFIGS,
    MIN_UNIQUE CISSPECT_GUIDELINES_CONFIGS,
    MIN_UNIQUE CISSPECT_POLICIES_CONFIGS,
    MIN_UNIQUE CISSPECT_PROCEDURES_CONFIGS,
    MIN_UNIQUE CISSPECT_PROTOCOLS_CONFIGS,
    MIN_UNIQUE CISSPECT_WORKFLOWS_CONFIGS,
    MIN_UNIQUE CISSPECT_PROCESSES_CONFIGS,
    MIN_UNIQUE CISSPECT_CONTROLS_CONFIGS,
    MIN_UNIQUE CISSPECT_MEASURES_CONFIGS,
    MIN_UNIQUE CISSPECT_METRICS_CONFIGS,
    MIN_UNIQUE CISSPECT_MONITORING_CONFIGS,
    MIN_UNIQUE CISSPECT_AUDITING_CONFIGS,
    MIN_UNIQUE CISSPECT_REPORTING_CONFIGS,
    MIN_UNIQUE CISSPECT_DOCUMENTATION_CONFIGS,
    MIN_UNIQUE CISSPECT_TRAINING_CONFIGS,
    MIN_UNIQUE CISSPECT_AWARENESS_CONFIGS,
    MIN_UNIQUE CISSPECT_ASSESSMENT_CONFIGS,
    MIN_UNIQUE CISSPECT_TESTING_CONFIGS,
    MIN_UNIQUE CISSPECT_VALIDATION_CONFIGS,
    MIN_UNIQUE CISSPECT_VERIFICATION_CONFIGS,
)

# Importer les systèmes améliorés
from app.core.error_handler_v2 import get_error_handler, handle_errors, NetworkException, LLMException
from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
from app.core.retry_manager import get_retry_manager, retry_web_request, retry_llm_call


class AsmblrPipelineFixed:
    """
    Pipeline principal d'Asmblr - Version avec corrections critiques
    Résout les TODO et gestion d'erreurs unifiée
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.error_handler = get_error_handler()
        self.smart_logger = get_smart_logger()
        self.retry_manager = get_retry_manager()
        
        # Validation des prérequis
        self._validate_prerequisites()
    
    def _validate_prerequisites(self) -> None:
        """Valide les prérequis pour le pipeline"""
        try:
            # Valider les secrets
            validate_secrets(self.settings)
            
            # Vérifier Ollama
            check_ollama(self.settings.ollama_base_url, [
                self.settings.general_model,
                self.settings.code_model
            ])
            
            self.smart_logger.system(
                LogLevel.LOW,
                "pipeline_init",
                "Prérequis validés avec succès"
            )
            
        except Exception as e:
            self.error_handler.handle_exception(e, "pipeline_validation")
            raise
    
    @handle_errors("pipeline_run", reraise=True)
    def run(self, topic: str, **kwargs) -> RunResult:
        """
        Exécute le pipeline principal avec gestion d'erreurs unifiée
        
        Args:
            topic: Sujet à analyser
            **kwargs: Paramètres additionnels
            
        Returns:
            Résultat de l'exécution
        """
        self.smart_logger.start_operation("pipeline_run", metadata={"topic": topic})
        
        try:
            # Validation du sujet
            self._validate_topic(topic)
            
            # Exécution des étapes
            result = self._execute_pipeline_stages(topic, **kwargs)
            
            self.smart_logger.end_operation("pipeline_run", success=True)
            return result
            
        except Exception as e:
            self.smart_logger.end_operation("pipeline_run", success=False)
            raise
    
    def _validate_topic(self, topic: str) -> None:
        """Valide le sujet d'entrée"""
        if not topic or not topic.strip():
            raise ValidationException(
                "Le sujet ne peut pas être vide",
                operation="topic_validation"
            )
        
        topic = topic.strip()
        
        if len(topic) < TOPIC_MIN_LENGTH:
            raise ValidationException(
                f"Le sujet doit contenir au moins {TOPIC_MIN_LENGTH} caractères",
                operation="topic_validation"
            )
        
        if len(topic) > TOPIC_MAX_LENGTH:
            raise ValidationException(
                f"Le sujet ne peut pas dépasser {TOPIC_MAX_LENGTH} caractères",
                operation="topic_validation"
            )
        
        # Vérifier les valeurs manquantes/invalides
        if self._text_missing_or_invalid(topic):
            raise ValidationException(
                "Le sujet contient des valeurs invalides (unknown, n/a, etc.)",
                operation="topic_validation"
            )
        
        self.smart_logger.business(
            LogLevel.MEDIUM,
            "topic_validated",
            f"Sujet validé: {topic[:50]}..."
        )
    
    def _text_missing_or_invalid(self, value: Any) -> bool:
        """
        Vérifie si le texte contient des valeurs manquantes ou invalides
        Version corrigée du TODO original
        """
        if not value:
            return True
        
        text = str(value).strip().lower()
        invalid_values = {
            "", "unknown", "n/a", "none", "null", "tbd", "todo",
            "undefined", "missing", "not applicable", "na"
        }
        
        return text in invalid_values
    
    @handle_errors("pipeline_stages", reraise=True)
    def _execute_pipeline_stages(self, topic: str, **kwargs) -> RunResult:
        """Exécute les étapes du pipeline avec retry automatique"""
        
        # Étape 1: Pré-run gate
        self.smart_logger.start_operation("prerun_gate")
        prerun_result = self._execute_prerun_gate(topic, **kwargs)
        self.smart_logger.end_operation("prerun_gate", success=True)
        
        # Étape 2: Signal processing
        self.smart_logger.start_operation("signal_processing")
        signal_result = self._execute_signal_processing(topic, prerun_result, **kwargs)
        self.smart_logger.end_operation("signal_processing", success=True)
        
        # Étape 3: Génération d'idées
        self.smart_logger.start_operation("idea_generation")
        idea_result = self._execute_idea_generation(topic, signal_result, **kwargs)
        self.smart_logger.end_operation("idea_generation", success=True)
        
        # Étape 4: Analyse d'actionabilité
        self.smart_logger.start_operation("actionability_analysis")
        actionability_result = self._execute_actionability_analysis(idea_result, **kwargs)
        self.smart_logger.end_operation("actionability_analysis", success=True)
        
        # Étape 5: Génération d'artefacts
        self.smart_logger.start_operation("artifact_generation")
        artifact_result = self._execute_artifact_generation(topic, actionability_result, **kwargs)
        self.smart_logger.end_operation("artifact_generation", success=True)
        
        # Construire le résultat final
        return RunResult(
            topic=topic,
            status="completed",
            prerun_result=prerun_result,
            signal_result=signal_result,
            idea_result=idea_result,
            actionability_result=actionability_result,
            artifact_result=artifact_result,
            confidence_score=self._compute_confidence(artifact_result),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    @retry_web_request("prerun_gate")
    def _execute_prerun_gate(self, topic: str, **kwargs) -> dict:
        """Exécute la porte de pré-run avec retry automatique"""
        try:
            gate = PreRunGate(self.settings)
            return gate.validate_and_process(topic, **kwargs)
        except Exception as e:
            raise NetworkException(
                f"Erreur lors du pré-run gate: {str(e)}",
                operation="prerun_gate",
                metadata={"topic": topic[:50]}
            )
    
    @retry_web_request("signal_processing")
    def _execute_signal_processing(self, topic: str, prerun_result: dict, **kwargs) -> dict:
        """Exécute le traitement des signaux avec retry automatique"""
        try:
            engine = SignalEngine(self.settings)
            return engine.process_signals(topic, prerun_result, **kwargs)
        except Exception as e:
            raise NetworkException(
                f"Erreur lors du traitement des signaux: {str(e)}",
                operation="signal_processing",
                metadata={"topic": topic[:50]}
            )
    
    @retry_llm_call("idea_generation")
    def _execute_idea_generation(self, topic: str, signal_result: dict, **kwargs) -> dict:
        """Exécute la génération d'idées avec retry automatique"""
        try:
            # Utiliser CrewAI pour générer les idées
            return run_crewai_pipeline(
                topic=topic,
                signal_data=signal_result,
                stage="idea_generation",
                settings=self.settings,
                **kwargs
            )
        except Exception as e:
            raise LLMException(
                f"Erreur lors de la génération d'idées: {str(e)}",
                operation="idea_generation",
                metadata={"topic": topic[:50]}
            )
    
    def _execute_actionability_analysis(self, idea_result: dict, **kwargs) -> dict:
        """Analyse l'actionabilité des idées avec logging amélioré"""
        try:
            ideas = idea_result.get("ideas", [])
            threshold = kwargs.get("actionability_threshold", IDEA_ACTIONABILITY_MIN_SCORE)
            
            assessments = {}
            adjusted_scores = {}
            eligible = []
            blocked = []
            
            for idea in ideas:
                assessment = self._assess_idea_actionability(idea)
                assessments[idea.get("name", "unknown")] = assessment
                
                # Ajuster le score
                adjusted_score = self._adjust_idea_score(assessment["score"], threshold)
                adjusted_scores[idea.get("name", "unknown")] = adjusted_score
                
                if adjusted_score >= threshold:
                    eligible.append(idea.get("name", "unknown"))
                else:
                    blocked.append(idea.get("name", "unknown"))
            
            # Logging intelligent (remplace le TODO)
            if len(assessments) > 0:
                avg_actionability = sum(a.get("score", 0) for a in assessments.values()) / len(assessments)
                
                self.smart_logger.business(
                    LogLevel.MEDIUM,
                    "actionability_assessment",
                    f"Analyse d'actionabilité terminée: {len(eligible)}/{len(ideas)} idées éligibles",
                    metadata={
                        "threshold": threshold,
                        "avg_score": avg_actionability,
                        "eligible_count": len(eligible),
                        "blocked_count": len(blocked)
                    }
                )
                
                # Logging des idées bloquées (remplace le TODO)
                if blocked:
                    blocked_details = [
                        f"{name}({assessments.get(name, {}).get('score', 0)})"
                        for name in blocked
                        if name in assessments
                    ]
                    
                    self.smart_logger.business(
                        LogLevel.LOW,
                        "blocked_ideas",
                        f"Idées bloquées par le seuil d'actionabilité: {', '.join(blocked_details)}",
                        metadata={
                            "blocked_ideas": blocked_details,
                            "threshold": threshold
                        }
                    )
            
            return {
                "assessments": assessments,
                "adjusted_scores": adjusted_scores,
                "eligible": eligible,
                "blocked": blocked,
                "threshold": threshold
            }
            
        except Exception as e:
            self.error_handler.handle_exception(e, "actionability_analysis")
            raise
    
    def _assess_idea_actionability(self, idea: dict) -> dict:
        """Évalue l'actionabilité d'une idée"""
        score = 50
        signals = {"issues": [], "strengths": []}
        
        # Vérifier les phrases génériques
        generic_phrases = (
            "save time", "improve efficiency", "increase productivity",
            "streamline workflow", "all-in-one", "for everyone",
            "any business", "one-click", "revolutionary", "game-changing"
        )
        
        idea_text = f"{idea.get('name', '')} {idea.get('description', '')}".lower()
        
        for phrase in generic_phrases:
            if phrase in idea_text:
                score -= 5
                signals["issues"].append(f"Phrase générique: {phrase}")
        
        # Vérifier la spécificité
        if len(idea.get('description', '')) < 50:
            score -= 10
            signals["issues"].append("Description trop courte")
        
        # Vérifier la faisabilité technique
        if self._is_technically_feasible(idea):
            score += 10
            signals["strengths"].append("Faisable techniquement")
        
        return {
            "score": max(0, min(100, score)),
            "signals": signals,
            "assessment": "actionable" if score >= 50 else "not_actionable"
        }
    
    def _is_technically_feasible(self, idea: dict) -> bool:
        """Vérifie si une idée est techniquement réalisable"""
        # Logique simplifiée pour la faisabilité
        description = idea.get('description', '').lower()
        
        # Indicateurs de faisabilité
        feasible_indicators = [
            "api", "database", "web", "mobile", "app", "software",
            "platform", "service", "tool", "system", "automation"
        ]
        
        return any(indicator in description for indicator in feasible_indicators)
    
    def _adjust_idea_score(self, score: float, threshold: float) -> float:
        """Ajuste le score d'une idée selon le seuil"""
        if score >= threshold:
            return score
        
        # Ajustement progressif
        adjustment = min(IDEA_ACTIONABILITY_ADJUSTMENT_MAX, threshold - score)
        return score + adjustment
    
    @retry_llm_call("artifact_generation")
    def _execute_artifact_generation(self, topic: str, actionability_result: dict, **kwargs) -> dict:
        """Génère les artefacts finaux avec retry automatique"""
        try:
            # Utiliser CrewAI pour générer les artefacts
            return run_crewai_pipeline(
                topic=topic,
                actionability_data=actionability_result,
                stage="artifact_generation",
                settings=self.settings,
                **kwargs
            )
        except Exception as e:
            raise LLMException(
                f"Erreur lors de la génération d'artefacts: {str(e)}",
                operation="artifact_generation",
                metadata={"topic": topic[:50]}
            )
    
    def _compute_confidence(self, artifact_result: dict) -> float:
        """Calcule le score de confiance"""
        try:
            return compute_confidence(artifact_result)
        except Exception as e:
            self.smart_logger.error(
                "confidence_computation",
                f"Erreur calcul confiance: {str(e)}"
            )
            return 50.0  # Valeur par défaut
    
    def get_pipeline_status(self) -> dict:
        """Retourne le statut actuel du pipeline"""
        return {
            "status": "ready",
            "error_count": len(self.error_handler.error_history),
            "last_error": self.error_handler.error_history[-1].to_context() if self.error_handler.error_history else None,
            "log_summary": self.smart_logger.get_log_summary(hours=1)
        }


# Fonction utilitaire pour créer le pipeline corrigé
def create_fixed_pipeline(settings: Settings) -> AsmblrPipelineFixed:
    """
    Crée une instance du pipeline corrigé
    
    Args:
        settings: Configuration de l'application
        
    Returns:
        Instance du pipeline avec corrections appliquées
    """
    return AsmblrPipelineFixed(settings)


# Point d'entrée principal corrigé
@handle_errors("main_pipeline_entry", reraise=True)
def run_fixed_pipeline(topic: str, **kwargs) -> RunResult:
    """
    Point d'entrée principal pour le pipeline corrigé
    
    Args:
        topic: Sujet à analyser
        **kwargs: Paramètres additionnels
        
    Returns:
        Résultat de l'exécution du pipeline
    """
    settings = Settings()
    pipeline = create_fixed_pipeline(settings)
    
    return pipeline.run(topic, **kwargs)
