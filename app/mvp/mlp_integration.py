"""MLP Integration - Integration of Most Lovable Product systems into existing pipeline."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .mlp_builder import MLPBuilder, MLPBuildResult
from ..core.llm import LLMClient

logger = logging.getLogger(__name__)


class MLPIntegrator:
    """Integrates MLP systems into existing MVP pipeline."""
    
    def __init__(self, config: Dict[str, Any], llm_client: LLMClient):
        self.config = config
        self.llm_client = llm_client
        self.mlp_builder = MLPBuilder(config, llm_client)
        
        # Check if MLP features are enabled
        self.mlp_enabled = config.get('MLP_ENABLED', False)
        self.emotional_design_enabled = config.get('EMOTIONAL_DESIGN_ENABLED', True)
        self.loveability_enabled = config.get('LOVEABILITY_ENABLED', True)
    
    def integrate_into_pipeline(self, existing_crew_config: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate MLP agents and tasks into existing CrewAI pipeline."""
        
        if not self.mlp_enabled:
            logger.info("MLP features disabled, returning original config")
            return existing_crew_config
        
        logger.info("Integrating MLP systems into existing pipeline")
        
        # Import MLP agents
        try:
            from ..agents.loveability_engineer import LoveabilityEngineerAgent
            from ..agents.ux_specialist import UXSpecialistAgent
            from ..agents.emotional_designer import EmotionalDesignerAgent
            
            # Create MLP agents
            loveability_engineer = LoveabilityEngineerAgent(self.llm_client)
            ux_specialist = UXSpecialistAgent(self.llm_client)
            emotional_designer = EmotionalDesignerAgent(self.llm_client)
            
            # Add MLP agents to existing crew
            enhanced_config = existing_crew_config.copy()
            
            # Add agents
            if 'agents' not in enhanced_config:
                enhanced_config['agents'] = []
            
            enhanced_config['agents'].extend([
                loveability_engineer.agent,
                ux_specialist.agent,
                emotional_designer.agent
            ])
            
            # Add MLP-specific tasks
            if 'tasks' not in enhanced_config:
                enhanced_config['tasks'] = []
            
            # Create MLP tasks
            mlp_tasks = self._create_mlp_tasks(
                loveability_engineer,
                ux_specialist,
                emotional_designer,
                enhanced_config.get('tasks', [])
            )
            
            enhanced_config['tasks'].extend(mlp_tasks)
            
            # Update process to include MLP stages
            enhanced_config['process'] = 'hierarchical'
            
            logger.info(f"MLP integration complete: {len(enhanced_config['agents'])} agents, {len(enhanced_config['tasks'])} tasks")
            
            return enhanced_config
            
        except ImportError as e:
            logger.error(f"Failed to import MLP agents: {e}")
            return existing_crew_config
    
    def _create_mlp_tasks(self, loveability_engineer, ux_specialist, emotional_designer, existing_tasks):
        """Create MLP-specific tasks."""
        mlp_tasks = []
        
        # Find existing product and tech tasks for context
        product_task = None
        tech_task = None
        
        for task in existing_tasks:
            if hasattr(task, 'agent') and hasattr(task.agent, 'role'):
                if 'Product' in task.agent.role:
                    product_task = task
                elif 'Tech' in task.agent.role or 'Lead' in task.agent.role:
                    tech_task = task
        
        # Create loveability strategy task
        loveability_task = loveability_engineer.create_loveability_strategy_task({
            'product_type': 'mlp',
            'emotional_theme': self.config.get('PRIMARY_EMOTIONAL_THEME', 'joy'),
            'target_audience': 'users seeking emotional connection'
        })
        
        # Create UX specialist task
        ux_task = ux_specialist.create_seamless_userflow_task(
            product_task.output if product_task else {},
            tech_task.output if tech_task else {}
        )
        
        # Create emotional design task
        emotional_task = emotional_designer.create_emotional_onboarding_task({
            'emotional_theme': self.config.get('PRIMARY_EMOTIONAL_THEME', 'joy'),
            'celebration_system': self.config.get('ENABLE_CELEBRATION_SYSTEM', True),
            'personalization': self.config.get('ENABLE_EMOTIONAL_PERSONALIZATION', True)
        })
        
        # Set task dependencies
        if product_task:
            loveability_task.context_tasks = [product_task]
            ux_task.context_tasks = [product_task]
            emotional_task.context_tasks = [product_task]
        
        if tech_task:
            ux_task.context_tasks = ux_task.context_tasks + [tech_task]
        
        mlp_tasks.extend([loveability_task, ux_task, emotional_task])
        
        return mlp_tasks
    
    def enhance_mvp_build(self, tech_spec: Dict[str, Any], prd_data: Dict[str, Any], 
                         output_path: Path) -> MLPBuildResult:
        """Enhance existing MVP build with MLP features."""
        
        if not self.mlp_enabled:
            logger.info("MLP disabled, skipping enhancement")
            # Return basic MVP result
            from .enhanced_builder import EnhancedMVPBuilder
            builder = EnhancedMVPBuilder(self.config)
            mvp_result = builder.build_enhanced_mvp(tech_spec, prd_data, output_path)
            
            # Convert to MLP result format
            return MLPBuildResult(
                success=mvp_result.success,
                mlp_path=mvp_result.mvp_path,
                loveability_score=60,  # Basic MVP score
                emotional_attachment_score=50,
                habit_formation_score=40,
                community_culture_score=30,
                build_time=mvp_result.build_time,
                loveability_features=[],
                magical_moments=[],
                identity_systems=[],
                community_features=[],
                error_message=mvp_result.error_message
            )
        
        logger.info("Building MLP with emotional addiction systems")
        return self.mlp_builder.build_mlp(tech_spec, prd_data, output_path)
    
    def get_mlp_configuration(self) -> Dict[str, Any]:
        """Get current MLP configuration."""
        return {
            'mlp_enabled': self.mlp_enabled,
            'emotional_design_enabled': self.emotional_design_enabled,
            'loveability_enabled': self.loveability_enabled,
            'emotional_theme': self.config.get('PRIMARY_EMOTIONAL_THEME', 'joy'),
            'celebration_system': self.config.get('ENABLE_CELEBRATION_SYSTEM', True),
            'personalization': self.config.get('ENABLE_EMOTIONAL_PERSONALIZATION', True),
            'community_features': self.config.get('ENABLE_COMMUNITY_FEATURES', True),
            'haptic_feedback': self.config.get('ENABLE_HAPTIC_FEEDBACK', True),
            'emotional_sounds': self.config.get('ENABLE_EMOTIONAL_SOUNDS', True),
            'celebration_sensitivity': self.config.get('CELEBRATION_SENSITIVITY', 'medium'),
            'learning_rate': self.config.get('EMOTIONAL_LEARNING_RATE', 0.15),
            'delight_frequency': self.config.get('DELIGHT_INTERACTION_FREQUENCY', 0.3)
        }
    
    def validate_mlp_setup(self) -> Dict[str, Any]:
        """Validate MLP setup and dependencies."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check required configuration
        required_configs = [
            'PRIMARY_EMOTIONAL_THEME',
            'EMOTIONAL_DESIGN_ENABLED',
            'ENABLE_CELEBRATION_SYSTEM'
        ]
        
        for config in required_configs:
            if config not in self.config:
                validation_result['errors'].append(f"Missing required config: {config}")
                validation_result['valid'] = False
        
        # Check optional but recommended configs
        recommended_configs = [
            'ENABLE_EMOTIONAL_PERSONALIZATION',
            'ENABLE_COMMUNITY_FEATURES',
            'EMOTIONAL_LEARNING_RATE'
        ]
        
        for config in recommended_configs:
            if config not in self.config:
                validation_result['warnings'].append(f"Missing recommended config: {config}")
        
        # Check agent availability
        try:
            from ..agents.loveability_engineer import LoveabilityEngineerAgent
            from ..agents.ux_specialist import UXSpecialistAgent
            from ..agents.emotional_designer import EmotionalDesignerAgent
        except ImportError as e:
            validation_result['errors'].append(f"MLP agent import failed: {e}")
            validation_result['valid'] = False
        
        # Recommendations
        if validation_result['valid']:
            validation_result['recommendations'].extend([
                "Enable all MLP features for maximum loveability",
                "Set emotional theme based on target audience",
                "Configure celebration sensitivity appropriately",
                "Enable community features for tribal bonding"
            ])
        
        return validation_result
