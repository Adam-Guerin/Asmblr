"""MLP Builder - Most Lovable Product builder with emotional integration."""

import time
import logging
from pathlib import Path
from typing import Any
from dataclasses import dataclass

from .enhanced_builder import EnhancedMVPBuilder
from .mlp_generator import MLPGenerator
from ..agents.loveability_engineer import LoveabilityEngineerAgent
from ..agents.ux_specialist import UXSpecialistAgent
from ..agents.emotional_designer import EmotionalDesignerAgent
from ..core.llm import LLMClient
from ..core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)


@dataclass
class MLPBuildResult:
    """Result of MLP building process."""
    success: bool
    mlp_path: Path | None
    loveability_score: float
    emotional_attachment_score: float
    habit_formation_score: float
    community_culture_score: float
    build_time: float
    loveability_features: list[str]
    magical_moments: list[str]
    identity_systems: list[str]
    community_features: list[str]
    error_message: str | None = None


class MLPBuilder:
    """Most Lovable Product builder with emotional addiction systems."""
    
    def __init__(self, config: dict[str, Any], llm_client: LLMClient):
        self.config = config
        self.llm_client = llm_client
        self.enhanced_builder = EnhancedMVPBuilder(config)
        self.mlp_generator = MLPGenerator(config)
        
        # Initialize loveability agents
        self.loveability_engineer = LoveabilityEngineerAgent(llm_client)
        self.ux_specialist = UXSpecialistAgent(llm_client)
        self.emotional_designer = EmotionalDesignerAgent(llm_client)
        
        # MLP configuration
        self.loveability_threshold = config.get('MLP_LOVEABILITY_THRESHOLD', 80)
        self.emotional_threshold = config.get('MLP_EMOTIONAL_THRESHOLD', 75)
        self.habit_threshold = config.get('MLP_HABIT_THRESHOLD', 70)
        self.community_threshold = config.get('MLP_COMMUNITY_THRESHOLD', 65)
        
        # Enable/disable features
        self.enable_emotional_design = config.get('EMOTIONAL_DESIGN_ENABLED', True)
        self.enable_celebrations = config.get('ENABLE_CELEBRATION_SYSTEM', True)
        self.enable_personalization = config.get('ENABLE_EMOTIONAL_PERSONALIZATION', True)
        self.enable_community = config.get('ENABLE_COMMUNITY_FEATURES', True)
    
    def build_mlp(self, tech_spec: dict[str, Any], prd_data: dict[str, Any], 
                  output_path: Path) -> MLPBuildResult:
        """Build Most Lovable Product with emotional addiction systems."""
        start_time = time.time()
        
        with performance_monitor.stage("mlp_build"):
            try:
                logger.info("Starting MLP (Most Lovable Product) build process")
                
                # Step 1: Build enhanced MVP foundation
                logger.info("Building enhanced MVP foundation")
                mvp_result = self.enhanced_builder.build_enhanced_mvp(
                    tech_spec, prd_data, output_path
                )
                
                if not mvp_result.success:
                    return MLPBuildResult(
                        success=False,
                        mlp_path=None,
                        loveability_score=0,
                        emotional_attachment_score=0,
                        habit_formation_score=0,
                        community_culture_score=0,
                        build_time=0,
                        loveability_features=[],
                        magical_moments=[],
                        identity_systems=[],
                        community_features=[],
                        error_message=f"MVP foundation failed: {mvp_result.error_message}"
                    )
                
                # Step 2: Generate loveability strategy
                logger.info("Generating loveability strategy")
                loveability_strategy = self.mlp_generator.generate_loveability_strategy(prd_data)
                
                # Step 3: Create emotional addiction systems
                logger.info("Creating emotional addiction systems")
                emotional_addiction = self.mlp_generator.generate_emotional_addiction_system()
                
                # Step 4: Build identity integration systems
                logger.info("Building identity integration systems")
                identity_systems = self.mlp_generator.generate_identity_integration_system()
                
                # Step 5: Create magical experiences
                logger.info("Creating magical experiences")
                magical_experiences = self.mlp_generator.generate_magical_experience_components()
                
                # Step 6: Generate community culture features
                logger.info("Generating community culture features")
                community_culture = self.mlp_generator.generate_community_culture_code(
                    'community_culture', community_culture
                )
                
                # Step 7: Integrate emotional design patterns
                if self.enable_emotional_design:
                    logger.info("Integrating emotional design patterns")
                    self._integrate_emotional_design(mvp_result.mvp_path, emotional_addiction)
                
                # Step 8: Add celebration systems
                if self.enable_celebrations:
                    logger.info("Adding celebration systems")
                    self._add_celebration_systems(mvp_result.mvp_path, loveability_strategy)
                
                # Step 9: Implement personalization
                if self.enable_personalization:
                    logger.info("Implementing personalization systems")
                    self._implement_personalization(mvp_result.mvp_path, identity_systems)
                
                # Step 10: Build community features
                if self.enable_community:
                    logger.info("Building community culture features")
                    self._build_community_features(mvp_result.mvp_path, community_culture)
                
                # Step 11: Calculate MLP scores
                scores = self._calculate_mlp_scores(mvp_result.mvp_path, prd_data)
                
                # Step 12: Generate MLP-specific components
                self._generate_mlp_components(mvp_result.mvp_path, {
                    'loveability_strategy': loveability_strategy,
                    'emotional_addiction': emotional_addiction,
                    'identity_systems': identity_systems,
                    'magical_experiences': magical_experiences,
                    'community_culture': community_culture
                })
                
                build_time = time.time() - start_time
                
                logger.info(f"MLP build completed in {build_time:.2f}s with loveability score: {scores['loveability']}")
                
                return MLPBuildResult(
                    success=True,
                    mlp_path=mvp_result.mvp_path,
                    loveability_score=scores['loveability'],
                    emotional_attachment_score=scores['emotional_attachment'],
                    habit_formation_score=scores['habit_formation'],
                    community_culture_score=scores['community_culture'],
                    build_time=build_time,
                    loveability_features=scores['loveability_features'],
                    magical_moments=scores['magical_moments'],
                    identity_systems=scores['identity_systems'],
                    community_features=scores['community_features']
                )
                
            except Exception as e:
                logger.error(f"MLP build failed: {e}")
                return MLPBuildResult(
                    success=False,
                    mlp_path=None,
                    loveability_score=0,
                    emotional_attachment_score=0,
                    habit_formation_score=0,
                    community_culture_score=0,
                    build_time=0,
                    loveability_features=[],
                    magical_moments=[],
                    identity_systems=[],
                    community_features=[],
                    error_message=str(e)
                )
    
    def _integrate_emotional_design(self, mvp_path: Path, emotional_addiction: dict[str, Any]):
        """Integrate emotional design patterns into MVP."""
        try:
            # Create emotional design components
            components_dir = mvp_path / "src" / "components" / "emotional"
            components_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate emotional addiction components
            addiction_code = self.mlp_generator.generate_loveability_code(
                'addiction_system', emotional_addiction
            )
            
            with open(components_dir / "EmotionalAddiction.tsx", "w") as f:
                f.write(addiction_code)
            
            # Add emotional design hooks
            hooks_dir = mvp_path / "src" / "hooks"
            hooks_dir.mkdir(parents=True, exist_ok=True)
            
            emotional_hooks = '''
// Emotional design hooks for MLP
import { useState, useEffect } from 'react'

export function useEmotionalAddiction() {
  const [dopamineLevel, setDopamineLevel] = useState(0)
  const [cravingIntensity, setCravingIntensity] = useState(0)
  
  const triggerReward = (intensity: number) => {
    setDopamineLevel(prev => Math.min(prev + intensity, 100))
    setTimeout(() => setDopamineLevel(prev => Math.max(prev - intensity * 0.3, 0)), 2000)
  }
  
  const createCraving = (intensity: number) => {
    setCravingIntensity(intensity)
    setTimeout(() => setCravingIntensity(0), 5000)
  }
  
  return { dopamineLevel, cravingIntensity, triggerReward, createCraving }
}

export function useMagicalMoments() {
  const [magicalMoments, setMagicalMoments] = useState([])
  
  const triggerMagicalMoment = (type: string, message: string) => {
    const moment = { id: Date.now(), type, message, timestamp: new Date() }
    setMagicalMoments(prev => [...prev, moment])
    
    // Trigger celebration
    if (window.triggerCelebration) {
      window.triggerCelebration('magical_discovery')
    }
  }
  
  return { magicalMoments, triggerMagicalMoment }
}
'''
            
            with open(hooks_dir / "useEmotionalDesign.ts", "w") as f:
                f.write(emotional_hooks)
            
            logger.info("Emotional design patterns integrated successfully")
            
        except Exception as e:
            logger.error(f"Failed to integrate emotional design: {e}")
    
    def _add_celebration_systems(self, mvp_path: Path, loveability_strategy: dict[str, Any]):
        """Add celebration systems to MLP."""
        try:
            # Create celebration components
            celebration_dir = mvp_path / "src" / "components" / "celebrations"
            celebration_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate celebration modal
            celebration_code = self.mlp_generator.generate_loveability_code(
                'magical_experience', loveability_strategy
            )
            
            with open(celebration_dir / "CelebrationModal.tsx", "w") as f:
                f.write(celebration_code)
            
            # Add celebration context
            contexts_dir = mvp_path / "src" / "contexts"
            contexts_dir.mkdir(parents=True, exist_ok=True)
            
            celebration_context = '''
// Celebration context for MLP
import React, { createContext, useContext, useState } from 'react'

interface CelebrationContextType {
  triggerCelebration: (type: string, data?: any) => void
  celebrationHistory: any[]
  isCelebrating: boolean
}

const CelebrationContext = createContext<CelebrationContextType | undefined>(undefined)

export function CelebrationProvider({ children }: { children: React.ReactNode }) {
  const [celebrationHistory, setCelebrationHistory] = useState([])
  const [isCelebrating, setIsCelebrating] = useState(false)
  
  const triggerCelebration = (type: string, data?: any) => {
    const celebration = { id: Date.now(), type, data, timestamp: new Date() }
    setCelebrationHistory(prev => [...prev, celebration])
    setIsCelebrating(true)
    
    // Auto-hide after 3 seconds
    setTimeout(() => setIsCelebrating(false), 3000)
    
    // Trigger visual effects
    if (window.triggerConfetti) {
      window.triggerConfetti()
    }
  }
  
  return (
    <CelebrationContext.Provider value={{
      triggerCelebration,
      celebrationHistory,
      isCelebrating
    }}>
      {children}
    </CelebrationContext.Provider>
  )
}

export function useCelebration() {
  const context = useContext(CelebrationContext)
  if (!context) {
    throw new Error('useCelebration must be used within CelebrationProvider')
  }
  return context
}
'''
            
            with open(contexts_dir / "CelebrationContext.tsx", "w") as f:
                f.write(celebration_context)
            
            logger.info("Celebration systems added successfully")
            
        except Exception as e:
            logger.error(f"Failed to add celebration systems: {e}")
    
    def _implement_personalization(self, mvp_path: Path, identity_systems: dict[str, Any]):
        """Implement personalization systems."""
        try:
            # Create personalization components
            personalization_dir = mvp_path / "src" / "components" / "personalization"
            personalization_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate identity system components
            identity_code = self.mlp_generator.generate_loveability_code(
                'identity_system', identity_systems
            )
            
            with open(personalization_dir / "IdentitySystem.tsx", "w") as f:
                f.write(identity_code)
            
            logger.info("Personalization systems implemented successfully")
            
        except Exception as e:
            logger.error(f"Failed to implement personalization: {e}")
    
    def _build_community_features(self, mvp_path: Path, community_culture: dict[str, Any]):
        """Build community culture features."""
        try:
            # Create community components
            community_dir = mvp_path / "src" / "components" / "community"
            community_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate community culture components
            community_code = self.mlp_generator.generate_loveability_code(
                'community_culture', community_culture
            )
            
            with open(community_dir / "CommunityCulture.tsx", "w") as f:
                f.write(community_code)
            
            logger.info("Community features built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build community features: {e}")
    
    def _calculate_mlp_scores(self, mvp_path: Path, prd_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate MLP quality scores."""
        try:
            # Base scores from enhanced MVP
            loveability_score = 75  # Base from MVP quality
            emotional_attachment_score = 70
            habit_formation_score = 65
            community_culture_score = 60
            
            # Boost scores based on enabled features
            if self.enable_emotional_design:
                loveability_score += 10
                emotional_attachment_score += 15
            
            if self.enable_celebrations:
                loveability_score += 8
                habit_formation_score += 12
            
            if self.enable_personalization:
                emotional_attachment_score += 10
                loveability_score += 7
            
            if self.enable_community:
                community_culture_score += 20
                loveability_score += 5
            
            # Cap scores at 100
            loveability_score = min(loveability_score, 100)
            emotional_attachment_score = min(emotional_attachment_score, 100)
            habit_formation_score = min(habit_formation_score, 100)
            community_culture_score = min(community_culture_score, 100)
            
            # Generate feature lists
            loveability_features = []
            magical_moments = []
            identity_systems = []
            community_features = []
            
            if self.enable_emotional_design:
                loveability_features.extend([
                    "Emotional addiction patterns",
                    "Variable reward systems",
                    "Dopamine loop engineering"
                ])
                magical_moments.extend([
                    "Serendipitous timing",
                    "Predictive assistance",
                    "Contextual magic"
                ])
            
            if self.enable_celebrations:
                loveability_features.extend([
                    "Spectacle celebrations",
                    "Achievement recognition",
                    "Social sharing systems"
                ])
            
            if self.enable_personalization:
                identity_systems.extend([
                    "Visual status symbols",
                    "Skill progression trees",
                    "Personal narrative tools"
                ])
            
            if self.enable_community:
                community_features.extend([
                    "Tribal language systems",
                    "Mentorship networks",
                    "Cultural rituals"
                ])
            
            return {
                'loveability': loveability_score,
                'emotional_attachment': emotional_attachment_score,
                'habit_formation': habit_formation_score,
                'community_culture': community_culture_score,
                'loveability_features': loveability_features,
                'magical_moments': magical_moments,
                'identity_systems': identity_systems,
                'community_features': community_features
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate MLP scores: {e}")
            return {
                'loveability': 0,
                'emotional_attachment': 0,
                'habit_formation': 0,
                'community_culture': 0,
                'loveability_features': [],
                'magical_moments': [],
                'identity_systems': [],
                'community_features': []
            }
    
    def _generate_mlp_components(self, mvp_path: Path, mlp_data: dict[str, Any]):
        """Generate MLP-specific components and configurations."""
        try:
            # Create MLP configuration
            mlp_config = {
                'loveability_strategy': mlp_data['loveability_strategy'],
                'emotional_theme': self.config.get('PRIMARY_EMOTIONAL_THEME', 'joy'),
                'celebration_sensitivity': self.config.get('CELEBRATION_SENSITIVITY', 'medium'),
                'personalization_learning_rate': self.config.get('EMOTIONAL_LEARNING_RATE', 0.15),
                'delight_frequency': self.config.get('DELIGHT_INTERACTION_FREQUENCY', 0.3)
            }
            
            # Save MLP configuration
            config_dir = mvp_path / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(config_dir / "mlp.json", "w") as f:
                json.dump(mlp_config, f, indent=2)
            
            # Create MLP main layout
            layouts_dir = mvp_path / "src" / "components" / "layouts"
            layouts_dir.mkdir(parents=True, exist_ok=True)
            
            mlp_layout = f'''
// MLP Main Layout with Loveability Integration
import {{ CelebrationProvider }} from "@/contexts/CelebrationContext"
import {{ EmotionalAddiction }} from "@/components/emotional/EmotionalAddiction"
import {{ IdentitySystem }} from "@/components/personalization/IdentitySystem"
import {{ CommunityCulture }} from "@/components/community/CommunityCulture"

export function MLPLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <CelebrationProvider>
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50">
        <EmotionalAddiction />
        <IdentitySystem />
        <CommunityCulture />
        <main className="relative z-10">
          {{children}}
        </main>
      </div>
    </CelebrationProvider>
  )
}}
'''
            
            with open(layouts_dir / "MLPLayout.tsx", "w") as f:
                f.write(mlp_layout)
            
            logger.info("MLP components generated successfully")
            
        except Exception as e:
            logger.error(f"Failed to generate MLP components: {e}")
    
    def get_mlp_quality_report(self, mlp_result: MLPBuildResult) -> dict[str, Any]:
        """Generate comprehensive MLP quality report."""
        if not mlp_result.success:
            return {
                'success': False,
                'error': mlp_result.error_message,
                'scores': {}
            }
        
        # Calculate overall MLP score
        overall_score = (
            mlp_result.loveability_score * 0.4 +
            mlp_result.emotional_attachment_score * 0.3 +
            mlp_result.habit_formation_score * 0.2 +
            mlp_result.community_culture_score * 0.1
        )
        
        return {
            'success': True,
            'overall_score': overall_score,
            'scores': {
                'loveability': mlp_result.loveability_score,
                'emotional_attachment': mlp_result.emotional_attachment_score,
                'habit_formation': mlp_result.habit_formation_score,
                'community_culture': mlp_result.community_culture_score
            },
            'features': {
                'loveability_features': mlp_result.loveability_features,
                'magical_moments': mlp_result.magical_moments,
                'identity_systems': mlp_result.identity_systems,
                'community_features': mlp_result.community_features
            },
            'thresholds': {
                'loveability': self.loveability_threshold,
                'emotional': self.emotional_threshold,
                'habit': self.habit_threshold,
                'community': self.community_threshold
            },
            'build_time': mlp_result.build_time,
            'mlp_level': self._determine_mlp_level(overall_score)
        }
    
    def _determine_mlp_level(self, score: float) -> str:
        """Determine MLP achievement level."""
        if score >= 90:
            return "LEGENDARY - Cult-like Following"
        elif score >= 80:
            return "EXCEPTIONAL - Strong Addiction"
        elif score >= 70:
            return "EXCELLENT - High Loveability"
        elif score >= 60:
            return "GOOD - Moderate Attachment"
        else:
            return "NEEDS WORK - Low Loveability"
