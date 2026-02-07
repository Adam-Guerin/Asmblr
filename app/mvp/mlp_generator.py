"""MLP Generator for creating Most Lovable Products with emotional addiction."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LoveabilityFeature:
    """Represents a loveability feature with emotional impact."""
    name: str
    psychological_trigger: str
    addiction_potential: float
    identity_integration: float
    community_value: float
    habit_formation: float
    magical_factor: float


class MLPGenerator:
    """Generates Most Lovable Products with emotional addiction systems."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.loveability_framework = self._initialize_loveability_framework()
        self.addiction_patterns = self._initialize_addiction_patterns()
        self.magical_systems = self._initialize_magical_systems()
    
    def _initialize_loveability_framework(self) -> Dict[str, Any]:
        """Initialize loveability psychology framework."""
        return {
            'emotional_addiction': {
                'dopamine_loops': 'variable_rewards + anticipation + celebration',
                'withdrawal_minimization': 'comfort_when_away',
                'ritual_creation': 'daily_meaningful_interactions',
                'identity_merging': 'product_part_of_self_image'
            },
            'magical_experiences': {
                'serendipitous_timing': 'perfect_just_when_needed',
                'predictive_assistance': 'anticipate_needs_before_awareness',
                'contextual_magic': 'adapt_to_situation_perfectly',
                'surprise_evolution': 'product_grows_and_reveals',
                'emotional_intelligence': 'respond_to_mood_and_state'
            },
            'identity_integration': {
                'visual_badges': 'display_achievements_and_status',
                'skill_progression': 'show_mastery_journey',
                'personal_narratives': 'craft_product_story',
                'exclusive_access': 'special_recognition',
                'achievement_showcases': 'beautiful_accomplishment_displays'
            },
            'community_culture': {
                'shared_language': 'insider_terminology',
                'mentorship_networks': 'experienced_guide_newcomers',
                'collaborative_rituals': 'community_activities',
                'cultural_celebrations': 'community_milestones',
                'tribal_knowledge': 'collective_wisdom'
            },
            'habit_formation': {
                'daily_rituals': 'meaningful_interactions',
                'streak_celebrations': 'over_the_top_recognition',
                'progression_joy': 'magical_advancement',
                'anticipation_building': 'tomorrow_possibilities',
                'withdrawal_sensation': 'gentle_discomfort_when_away'
            }
        }
    
    def _initialize_addiction_patterns(self) -> Dict[str, Any]:
        """Initialize emotional addiction patterns."""
        return {
            'variable_rewards': {
                'timing': 'unpredictable_delight_moments',
                'types': ['surprise_features', 'unexpected_bonuses', 'serendipitous_discoveries'],
                'frequency': '3-5_times_per_session',
                'intensity': 'moderate_to_high'
            },
            'anticipation_systems': {
                'teaser_campaigns': 'hint_future_possibilities',
                'progressive_reveals': 'gradual_feature_unlocking',
                'countdown_timers': 'build_excitement_for_releases',
                'sneak_peeks': 'exclusive_previews'
            },
            'celebration_spectacles': {
                'achievement_types': ['milestone', 'streak', 'mastery', 'community'],
                'visual_effects': ['confetti', 'fireworks', 'sparkles', 'light_effects'],
                'social_sharing': 'automatic_celebration_broadcasts',
                'personal_messages': 'customized_congratulations'
            },
            'withdrawal_avoidance': {
                'comfort_features': ['offline_access', 'background_presence', 'memory_triggers'],
                'return_celebrations': 'welcome_back_rituals',
                'missing_notifications': 'gentle_reminders_and_fomo',
                'community_connection': 'stay_connected_when_away'
            }
        }
    
    def _initialize_magical_systems(self) -> Dict[str, Any]:
        """Initialize magical experience systems."""
        return {
            'serendipity_engine': {
                'timing_algorithms': 'predictive_need_detection',
                'context_awareness': 'situation_location_time_adaptation',
                'perfect_timing': 'just_what_i_needed_moments',
                'surprise_elements': 'unexpected_delightful_features'
            },
            'predictive_assistance': {
                'anticipatory_features': 'needs_before_user_awareness',
                'smart_suggestions': 'contextual_recommendations',
                'automation_triggers': 'proactive_help',
                'learning_systems': 'continuous_pattern_improvement'
            },
            'evolution_systems': {
                'feature_unlocking': 'gradual_capability_reveals',
                'product_growth': 'continuous_improvement_and_surprise',
                'personal_adaptation': 'learns_and_adapts_individually',
                'community_evolution': 'grows_with_user_feedback'
            }
        }
    
    def generate_loveability_strategy(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive loveability strategy."""
        return {
            'framework': 'Most Lovable Product (MLP)',
            'core_pillars': [
                'Emotional Addiction Engineering',
                'Magical Experience Creation',
                'Identity Integration Systems',
                'Community Culture Building',
                'Habit Formation Engineering'
            ],
            'loveability_metrics': {
                'emotional_attachment_target': 90,
                'daily_engagement_target': 80,
                'net_promoter_target': 70,
                'habit_integration_target': 85,
                'community_participation_target': 60,
                'feature_discovery_target': 75
            },
            'implementation_phases': [
                {
                    'phase': 'Foundation',
                    'focus': 'Core magical experiences and addiction patterns',
                    'duration': '2_weeks',
                    'deliverables': ['serendipity_engine', 'variable_rewards_system']
                },
                {
                    'phase': 'Identity',
                    'focus': 'Self-expression and status systems',
                    'duration': '2_weeks',
                    'deliverables': ['badge_system', 'skill_progression', 'personal_narratives']
                },
                {
                    'phase': 'Community',
                    'focus': 'Tribal culture and mentorship',
                    'duration': '2_weeks',
                    'deliverables': ['shared_language', 'mentorship_networks', 'cultural_rituals']
                },
                {
                    'phase': 'Habits',
                    'focus': 'Daily rituals and meaningful integration',
                    'duration': '2_weeks',
                    'deliverables': ['daily_rituals', 'streak_celebrations', 'anticipation_systems']
                }
            ]
        }
    
    def generate_emotional_addiction_system(self) -> Dict[str, Any]:
        """Generate emotional addiction system components."""
        return {
            'dopamine_loop_design': {
                'variable_reward_schedule': {
                    'micro_rewards': 'every_3-5_interactions',
                    'medium_rewards': 'daily_achievements',
                    'large_rewards': 'weekly_milestones',
                    'epic_rewards': 'monthly_community_celebrations'
                },
                'anticipation_mechanics': {
                    'teaser_campaigns': 'hint_future_features',
                    'countdown_timers': 'build_excitement',
                    'exclusive_previews': 'special_access_early_looks',
                    'progressive_reveals': 'gradual_feature_unlocking'
                },
                'celebration_spectacles': {
                    'visual_effects': 'confetti_fireworks_sparkles',
                    'social_broadcasting': 'automatic_achievement_sharing',
                    'personal_recognition': 'customized_celebration_messages',
                    'community_involvement': 'tribal_celebration_participation'
                }
            },
            'withdrawal_minimization': {
                'comfort_features': 'offline_access_background_presence',
                'return_rituals': 'welcome_back_celebrations',
                'missing_sensations': 'gentle_fomo_inducing_reminders',
                'community_connection': 'stay_connected_when_away'
            }
        }
    
    def generate_identity_integration_system(self) -> Dict[str, Any]:
        """Generate identity integration system."""
        return {
            'visual_status_system': {
                'achievement_badges': 'visual_display_of_accomplishments',
                'skill_indicators': 'mastery_level_visualization',
                'status_symbols': 'exclusive_recognition_displays',
                'progress_bars': 'beautiful_advancement_tracking'
            },
            'personal_narrative_tools': {
                'story_crafting': 'help_users_tell_product_journey',
                'milestone_markers': 'significant_moment_highlighting',
                'achievement_showcases': 'beautiful_accomplishment_displays',
                'personal_goals': 'custom_objective_setting'
            },
            'community_identity_features': {
                'tribal_membership': 'exclusive_user_group_indicators',
                'mentorship_status': 'guide_mentee_relationships',
                'cultural_participation': 'ritual_and_tradition_involvement',
                'knowledge_sharing': 'expertise_contribution_systems'
            }
        }
    
    def generate_magical_experience_components(self) -> Dict[str, Any]:
        """Generate magical experience components."""
        return {
            'serendipity_engine': {
                'predictive_timing': 'perfect_just_when_needed_moments',
                'context_awareness': 'situation_adaptation',
                'surprise_discoveries': 'hidden_feature_reveals',
                'personal_magic': 'individualized_experiences'
            },
            'anticipatory_systems': {
                'smart_suggestions': 'contextual_recommendations',
                'proactive_assistance': 'needs_before_awareness',
                'learning_adaptation': 'continuous_improvement',
                'personalization_depth': 'deep_individual_understanding'
            },
            'evolution_mechanics': {
                'feature_unlocking': 'gradual_capability_reveals',
                'product_growth': 'continuous_improvement',
                'surprise_elements': 'unexpected_delightful_features',
                'community_evolution': 'user_driven_development'
            }
        }
    
    def generate_loveability_code(self, component_type: str, config: Dict[str, Any]) -> str:
        """Generate React/TypeScript code for loveability components."""
        if component_type == 'magical_experience':
            return self._generate_magical_experience_code(config)
        elif component_type == 'identity_system':
            return self._generate_identity_system_code(config)
        elif component_type == 'addiction_system':
            return self._generate_addiction_system_code(config)
        elif component_type == 'community_culture':
            return self._generate_community_culture_code(config)
        else:
            return self._generate_generic_loveability_code(config)
    
    def _generate_magical_experience_code(self, config: Dict[str, Any]) -> str:
        """Generate magical experience component code."""
        return f"""
import {{ useState, useEffect }} from 'react'
import {{ motion, AnimatePresence }} from 'framer-motion'

export function MagicalExperience() {{
  const [magicalMoments, setMagicalMoments] = useState([])
  const [isDiscovering, setIsDiscovering] = useState(false)
  
  const triggerMagicalMoment = () => {{
    const moments = [
      "How did it know I needed that?",
      "This feels like magic!",
      "Impossible but it's happening!",
      "Perfect timing!",
      "It read my mind!"
    ]
    
    const moment = moments[Math.floor(Math.random() * moments.length)]
    setMagicalMoments(prev => [...prev, {{ 
      id: Date.now(), 
      message: moment,
      timestamp: new Date()
    }}])
    
    // Trigger celebration
    if (window.triggerCelebration) {{
      window.triggerCelebration('magical_discovery')
    }}
  }}
  
  return (
    <div className="relative">
      {/* Magical background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            initial={{{{ opacity: 0, scale: 0, rotate: 0 }}}}
            animate={{{{ 
              opacity: [0, 0.3, 0],
              scale: [1, 1.2, 1],
              rotate: [0, 180, 360]
            }}}}
            transition={{{{ 
              duration: 10 + i * 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}}}
            className="absolute rounded-full bg-gradient-to-r from-purple-400 to-pink-400 opacity-20"
            style={{
              width: `${{100 + i * 30}}px`,
              height: `${{100 + i * 30}}px`,
              left: `${{Math.random() * 80}}%`,
              top: `${{Math.random() * 80}}%`,
            }}
          />
        ))}
      </div>
      
      {/* Magical discovery button */}
      <motion.button
        whileHover={{{{ 
          scale: 1.05,
          boxShadow: "0 10px 30px rgba(147, 51, 234, 0.3)"
        }}}}
        whileTap={{{{ scale: 0.95 }}}}
        onClick={triggerMagicalMoment}
        className="relative z-10 px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-full font-semibold shadow-lg hover:shadow-xl transition-all duration-300"
      >
        <motion.span
          animate={{{{ rotate: isDiscovering ? 360 : 0 }}}}
          transition={{{{ duration: 0.5 }}}}
          className="inline-block mr-2"
        >
          ✨
        </motion.span>
        Discover Magic
      </motion.button>
      
      {/* Magical moments display */}
      <AnimatePresence>
        {magicalMoments.slice(-3).map((moment) => (
          <motion.div
            key={moment.id}
            initial={{{{ opacity: 0, y: 50, scale: 0.8 }}}}
            animate={{{{ opacity: 1, y: 0, scale: 1 }}}}
            exit={{{{ opacity: 0, y: -50, scale: 0.8 }}}}
            className="fixed top-4 right-4 bg-white rounded-lg shadow-2xl p-4 max-w-sm z-50 border border-purple-200"
          >
            <div className="flex items-center gap-2 mb-2">
              <motion.div
                animate={{{{ rotate: 360 }}}}
                transition={{{{ duration: 2, repeat: Infinity, ease: "linear" }}}}
                className="text-2xl"
              >
                🎩
              </motion.div>
              <span className="font-semibold text-purple-600">Magical Moment!</span>
            </div>
            <p className="text-gray-700 text-sm">{moment.message}</p>
            <p className="text-gray-500 text-xs mt-1">
              {new Date(moment.timestamp).toLocaleTimeString()}
            </p>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}}
"""
    
    def _generate_identity_system_code(self, config: Dict[str, Any]) -> str:
        """Generate identity system component code."""
        return f"""
import {{ useState }} from 'react'
import {{ motion }} from 'framer-motion'

export function IdentitySystem() {{
  const [userLevel, setUserLevel] = useState(7)
  const [achievements, setAchievements] = useState([
    {{ id: 1, name: 'First Magical Moment', icon: '✨', unlocked: true }},
    {{ id: 2, name: 'Week Streak', icon: '🔥', unlocked: true }},
    {{ id: 3, name: 'Community Helper', icon: '🤝', unlocked: true }},
    {{ id: 4, name: 'Master Magician', icon: '🎩', unlocked: false }}
  ])
  
  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-8">
      {/* Status Badge Display */}
      <motion.div
        initial={{{{ opacity: 0, scale: 0.9 }}}}
        animate={{{{ opacity: 1, scale: 1 }}}}
        className="bg-white rounded-2xl shadow-xl p-6 mb-8"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Identity Status</h2>
            <p className="text-gray-600">Level {userLevel} Magic User</p>
          </div>
          <motion.div
            animate={{{{ rotate: 360 }}}}
            transition={{{{ duration: 3, repeat: Infinity, ease: "linear" }}}}
            className="text-6xl"
          >
            🏆
          </motion.div>
        </div>
        
        {/* Achievement Badges */}
        <div className="grid grid-cols-2 gap-4">
          {achievements.map((achievement) => (
            <motion.div
              key={achievement.id}
              whileHover={{{{ scale: 1.05, y: -5 }}}}
              className={`
                relative p-4 rounded-lg border-2 transition-all
                ${achievement.unlocked 
                  ? 'bg-gradient-to-r from-purple-100 to-pink-100 border-purple-300' 
                  : 'bg-gray-100 border-gray-300 opacity-50'
                }
              `}
            >
              <div className="text-3xl mb-2 text-center">
                {achievement.unlocked ? achievement.icon : '🔒'}
              </div>
              <h3 className="font-semibold text-center text-sm">
                {achievement.name}
              </h3>
              {achievement.unlocked && (
                <motion.div
                  initial={{{{ scale: 0 }}}}
                  animate={{{{ scale: [1, 1.2, 1] }}}}
                  transition={{{{ duration: 0.5, repeat: 2 }}}}
                  className="absolute -top-1 -right-1 bg-yellow-400 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center"
                >
                  ✨
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </motion.div>
      
      {/* Skill Progression */}
      <motion.div
        initial={{{{ opacity: 0, y: 20 }}}}
        animate={{{{ opacity: 1, y: 0 }}}}
        transition={{{{ delay: 0.2 }}}}
        className="bg-white rounded-2xl shadow-xl p-6"
      >
        <h3 className="text-xl font-bold text-gray-900 mb-4">Magic Mastery Journey</h3>
        <div className="space-y-4">
          {[
            {{ name: 'Novice Magician', level: 1, progress: 100 }},
            {{ name: 'Apprentice Wizard', level: 2, progress: 100 }},
            {{ name: 'Master Sorcerer', level: 3, progress: 60 }}
          ].map((skill) => (
            <div key={skill.name} className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-medium">{skill.name}</span>
                <span className="text-sm text-gray-600">Level {skill.level}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <motion.div
                  initial={{{{ width: 0 }}}}
                  animate={{{{ width: `${skill.progress}%` }}}}
                  transition={{{{ duration: 1, delay: 0.5 }}}}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full"
                />
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}}
"""
    
    def _generate_addiction_system_code(self, config: Dict[str, Any]) -> str:
        """Generate addiction system component code."""
        return f"""
import {{ useState, useEffect }} from 'react'
import {{ motion, AnimatePresence }} from 'framer-motion'

export function AddictionSystem() {{
  const [streak, setStreak] = useState(7)
  const [lastVisit, setLastVisit] = useState(new Date())
  const [showCelebration, setShowCelebration] = useState(false)
  
  useEffect(() => {{
    // Check streak and trigger celebration
    const today = new Date().toDateString()
    const lastVisitDate = lastVisit.toDateString()
    
    if (today !== lastVisitDate) {{
      setStreak(prev => prev + 1)
      setShowCelebration(true)
      setLastVisit(new Date())
      
      // Auto-hide celebration after 5 seconds
      setTimeout(() => setShowCelebration(false), 5000)
    }}
  }}, [lastVisit])
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50">
      {/* Streak Celebration */}
      <AnimatePresence>
        {showCelebration && (
          <motion.div
            initial={{{{ opacity: 0, scale: 0.5 }}}}
            animate={{{{ opacity: 1, scale: 1 }}}}
            exit={{{{ opacity: 0, scale: 0.5 }}}}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          >
            <motion.div
              initial={{{{ rotate: 0 }}}}
              animate={{{{ rotate: [0, 10, -10, 0] }}}}
              transition={{{{ duration: 0.5, repeat: 3, repeatDelay: 0.2 }}}}
              className="bg-white rounded-2xl p-8 max-w-md mx-4 text-center shadow-2xl"
            >
              <div className="text-6xl mb-4">🔥</div>
              <h2 className="text-3xl font-bold text-orange-600 mb-2">
                {streak} Day Streak!
              </h2>
              <p className="text-gray-600 mb-4">
                You're on fire! Keep it going!
              </p>
              <div className="flex justify-center gap-2">
                {[...Array(5)].map((_, i) => (
                  <motion.div
                    key={i}
                    animate={{{{ 
                      scale: [1, 0, 1],
                      opacity: [1, 0.5, 1]
                    }}}}
                    transition={{{{ 
                      delay: i * 0.1,
                      duration: 0.6
                    }}}}
                    className="w-3 h-3 bg-orange-400 rounded-full"
                  />
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Daily Ritual Interface */}
      <div className="max-w-4xl mx-auto p-8">
        <motion.div
          initial={{{{ opacity: 0, y: 20 }}}}
          animate={{{{ opacity: 1, y: 0 }}}}
          className="bg-white rounded-2xl shadow-xl p-8"
        >
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Daily Magic Ritual
            </h1>
            <p className="text-gray-600">
              Complete your daily ritual to maintain the streak!
            </p>
          </div>
          
          {/* Ritual Steps */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {{ step: 1, title: 'Morning Magic', icon: '🌅', completed: true }},
              {{ step: 2, title: 'Afternoon Wonder', icon: '✨', completed: true }},
              {{ step: 3, title: 'Evening Reflection', icon: '🌙', completed: false }}
            ].map((ritual) => (
              <motion.div
                key={ritual.step}
                whileHover={{{{ scale: 1.02, y: -5 }}}}
                className={`
                  relative p-6 rounded-xl border-2 transition-all cursor-pointer
                  ${ritual.completed 
                    ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200' 
                    : 'bg-gray-50 border-gray-200'
                  }
                `}
              >
                {ritual.completed && (
                  <motion.div
                    initial={{{{ scale: 0 }}}}
                    animate={{{{ scale: [1, 1.2, 1] }}}}
                    transition={{{{ duration: 0.5, repeat: 2 }}}}
                    className="absolute -top-2 -right-2 bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm"
                  >
                    ✓
                  </motion.div>
                )}
                
                <div className="text-center">
                  <div className="text-3xl mb-2">{ritual.icon}</div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    {ritual.title}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {ritual.completed ? 'Completed!' : 'Pending'}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
          
          {/* Streak Counter */}
          <div className="mt-8 text-center">
            <motion.div
              animate={{{{ 
                scale: [1, 1.1, 1],
                textShadow: [
                  "0 0 20px rgba(251, 146, 60, 0)",
                  "0 0 40px rgba(251, 146, 60, 0.5)",
                  "0 0 60px rgba(251, 146, 60, 0)"
                ]
              }}}}
              transition={{{{ duration: 2, repeat: Infinity }}}}
              className="inline-block"
            >
              <div className="text-6xl font-bold text-orange-600">
                {streak}
              </div>
              <div className="text-2xl text-orange-500">Day Streak!</div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}}
"""
    
    def _generate_community_culture_code(self, config: Dict[str, Any]) -> str:
        """Generate community culture component code."""
        return f"""
import {{ useState }} from 'react'
import {{ motion }} from 'framer-motion'

export function CommunityCulture() {{
  const [tribalMembers, setTribalMembers] = useState(1247)
  const [sharedLanguage, setSharedLanguage] = useState([
    "Keep the magic alive!",
    "Spread the wonder!",
    "Level up your wizardry!",
    "Community first!"
  ])
  
  return (
    <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-8">
      {/* Tribal Identity Display */}
      <motion.div
        initial={{{{ opacity: 0, scale: 0.95 }}}}
        animate={{{{ opacity: 1, scale: 1 }}}}
        className="bg-white rounded-2xl shadow-xl p-6 mb-8"
      >
        <div className="text-center mb-6">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            ✨ The Magic Tribe ✨
          </h1>
          <p className="text-gray-600">
            {tribalMembers} fellow wizards spreading wonder together
          </p>
        </div>
        
        {/* Shared Language Display */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sharedLanguage.map((phrase, index) => (
            <motion.div
              key={index}
              initial={{{{ opacity: 0, x: -20 }}}}
              animate={{{{ opacity: 1, x: 0 }}}}
              transition={{{{ delay: index * 0.1 }}}}
              whileHover={{{{ scale: 1.05, y: -3 }}}}
              className="bg-gradient-to-r from-purple-100 to-blue-100 p-4 rounded-lg border border-purple-200"
            >
              <div className="flex items-center gap-2 mb-2">
                <motion.div
                  animate={{{{ rotate: 360 }}}}
                  transition={{{{ 
                    duration: 3 + index,
                    repeat: Infinity, 
                    ease: "linear" 
                  }}}}
                  className="text-2xl"
                >
                  🗣️
                </motion.div>
                <span className="font-semibold text-purple-700">Tribe Language</span>
              </div>
              <p className="text-gray-700 italic">"{phrase}"</p>
            </motion.div>
          ))}
        </div>
      </motion.div>
      
      {/* Community Rituals */}
      <motion.div
        initial={{{{ opacity: 0, y: 20 }}}}
        animate={{{{ opacity: 1, y: 0 }}}}
        transition={{{{ delay: 0.3 }}}}
        className="bg-white rounded-2xl shadow-xl p-6"
      >
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Community Rituals</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {{
              title: "Daily Magic Circle",
              time: "9:00 PM",
              participants: 342,
              description: "Share today's magical discoveries",
              icon: "🔮"
            }},
            {{
              title: "Weekly Wonder Gathering",
              time: "Saturdays 3:00 PM", 
              participants: 567,
              description: "Showcase amazing achievements",
              icon: "✨"
            }},
            {{
              title: "Monthly Mastery Summit",
              time: "First Sunday",
              participants: 89,
              description: "Advanced magic techniques workshop",
              icon: "🎓"
            }}
          ].map((ritual, index) => (
            <motion.div
              key={index}
              whileHover={{{{ 
                scale: 1.02,
                boxShadow: "0 10px 30px rgba(147, 51, 234, 0.2)"
              }}}}
              className="bg-gradient-to-br from-indigo-50 to-purple-50 p-6 rounded-xl border border-indigo-100"
            >
              <div className="text-center mb-4">
                <div className="text-4xl mb-2">{ritual.icon}</div>
                <h3 className="font-bold text-gray-900 mb-1">
                  {ritual.title}
                </h3>
                <p className="text-sm text-indigo-600 font-medium">
                  {ritual.time}
                </p>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Participants</span>
                  <span className="font-bold text-indigo-600">{ritual.participants}</span>
                </div>
                <p className="text-sm text-gray-700">{ritual.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}}
"""
    
    def _generate_generic_loveability_code(self, config: Dict[str, Any]) -> str:
        """Generate generic loveability component code."""
        return f"""
import {{ motion }} from 'framer-motion'

export function LoveabilityComponent() {{
  return (
    <motion.div
      initial={{{{ opacity: 0, scale: 0.9 }}}}
      animate={{{{ opacity: 1, scale: 1 }}}}
      whileHover={{{{ scale: 1.02 }}}}
      transition={{{{ type: "spring", stiffness: 300, damping: 30 }}}}
      className="bg-gradient-to-br from-purple-50 to-pink-50 p-8 rounded-2xl shadow-xl"
    >
      <div className="text-center">
        <div className="text-6xl mb-4">💜</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Most Lovable Experience
        </h2>
        <p className="text-gray-600">
          Creating products users can't live without
        </p>
      </div>
    </motion.div>
  )
}}
"""
