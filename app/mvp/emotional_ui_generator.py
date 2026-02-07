"""Emotional UI Generator for creating delightful, feeling-evoking interfaces."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmotionalElement:
    """Represents an emotional design element."""
    emotion: str
    trigger: str
    visual_style: Dict[str, Any]
    animation: Dict[str, Any]
    feedback: Dict[str, Any]
    sound: Optional[str] = None


class EmotionalUIGenerator:
    """Generates emotionally resonant UI components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.emotional_palette = self._initialize_emotional_palette()
        self.animation_library = self._initialize_animation_library()
        self.celebration_systems = self._initialize_celebration_systems()
    
    def _initialize_emotional_palette(self) -> Dict[str, Any]:
        """Initialize emotion-based color and design palette."""
        return {
            'joy': {
                'colors': ['#FFD700', '#FFA500', '#FF6B6B', '#FFE66D'],
                'animations': ['bounce', 'pulse', 'shake'],
                'shapes': ['rounded', 'circles', 'stars'],
                'sounds': ['chime', 'sparkle', 'celebration']
            },
            'trust': {
                'colors': ['#4A90E2', '#7B68EE', '#6495ED', '#87CEEB'],
                'animations': ['fade', 'slide', 'glow'],
                'shapes': ['squares', 'shields', 'checkmarks'],
                'sounds': ['gentle', 'reassuring', 'calm']
            },
            'delight': {
                'colors': ['#FF69B4', '#DA70D6', '#FF1493', '#FFB6C1'],
                'animations': ['wiggle', 'flip', 'morph'],
                'shapes': ['hearts', 'sparkles', 'confetti'],
                'sounds': ['magical', 'whimsical', 'surprise']
            },
            'pride': {
                'colors': ['#FFD700', '#FFA500', '#FF8C00', '#FF6347'],
                'animations': ['scale', 'rotate', 'shine'],
                'shapes': ['trophies', 'medals', 'ribbons'],
                'sounds': ['triumphant', 'victory', 'achievement']
            },
            'connection': {
                'colors': ['#32CD32', '#228B22', '#008000', '#006400'],
                'animations': ['connect', 'link', 'merge'],
                'shapes': ['links', 'chains', 'networks'],
                'sounds': ['harmony', 'together', 'community']
            },
            'comfort': {
                'colors': ['#F5DEB3', '#DEB887', '#D2691E', '#BC8F8F'],
                'animations': ['breathe', 'float', 'settle'],
                'shapes': ['clouds', 'waves', 'pillows'],
                'sounds': ['soothing', 'warm', 'gentle']
            }
        }
    
    def _initialize_animation_library(self) -> Dict[str, Any]:
        """Initialize emotion-specific animation library."""
        return {
            'celebration': {
                'confetti': {
                    'duration': 2000,
                    'particle_count': 50,
                    'colors': ['joy', 'delight'],
                    'physics': {'gravity': 0.1, 'spread': 120}
                },
                'sparkles': {
                    'duration': 1500,
                    'particle_count': 30,
                    'colors': ['delight', 'pride'],
                    'physics': {'gravity': 0.05, 'spread': 90}
                },
                'fireworks': {
                    'duration': 3000,
                    'particle_count': 100,
                    'colors': ['joy', 'pride', 'delight'],
                    'physics': {'gravity': 0.2, 'spread': 360}
                }
            },
            'micro_interactions': {
                'button_press': {
                    'scale': [1, 0.95, 1.05, 1],
                    'duration': 200,
                    'easing': 'easeOutElastic'
                },
                'hover_lift': {
                    'y': [0, -4, 0],
                    'shadow': [0, 8, 0],
                    'duration': 150,
                    'easing': 'easeOutQuad'
                },
                'success_pulse': {
                    'scale': [1, 1.1, 1],
                    'opacity': [1, 0.8, 1],
                    'duration': 300,
                    'easing': 'easeInOutSine'
                },
                'error_shake': {
                    'x': [0, -5, 5, -5, 5, 0],
                    'duration': 400,
                    'easing': 'easeOutQuad'
                }
            },
            'page_transitions': {
                'warm_welcome': {
                    'type': 'fade_scale',
                    'duration': 800,
                    'easing': 'easeOutBack',
                    'stagger': 0.1
                },
                'delightful_discover': {
                    'type': 'slide_bounce',
                    'duration': 600,
                    'easing': 'easeOutBounce',
                    'direction': 'up'
                },
                'comforting_return': {
                    'type': 'fade_slide',
                    'duration': 1000,
                    'easing': 'easeInOutQuad',
                    'direction': 'right'
                }
            }
        }
    
    def _initialize_celebration_systems(self) -> Dict[str, Any]:
        """Initialize celebration and achievement systems."""
        return {
            'first_time': {
                'animations': ['confetti', 'sparkles'],
                'message': 'Welcome! 🎉 Your journey begins now!',
                'badge': 'first_step',
                'color_theme': 'joy'
            },
            'milestone': {
                'animations': ['fireworks', 'sparkles'],
                'message': 'Amazing milestone reached! 🏆',
                'badge': 'milestone_achieved',
                'color_theme': 'pride'
            },
            'streak': {
                'animations': ['confetti'],
                'message': '{days} day streak! You\'re on fire! 🔥',
                'badge': 'streak_keeper',
                'color_theme': 'delight'
            },
            'mastery': {
                'animations': ['fireworks', 'sparkles'],
                'message': 'Mastery unlocked! You\'re incredible! ⭐',
                'badge': 'master_level',
                'color_theme': 'pride'
            },
            'community': {
                'animations': ['confetti'],
                'message': 'Community hero! Thank you for helping others! 🤝',
                'badge': 'community_star',
                'color_theme': 'connection'
            }
        }
    
    def generate_emotional_hero(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate emotionally resonant hero section."""
        emotional_theme = product_data.get('emotional_theme', 'joy')
        emotion_config = self.emotional_palette[emotional_theme]
        
        return {
            'component': 'EmotionalHero',
            'props': {
                'className': f'bg-gradient-to-br from-{emotion_config["colors"][0]} to-{emotion_config["colors"][1]}',
                'emotion': emotional_theme,
                'animations': emotion_config['animations']
            },
            'elements': [
                {
                    'type': 'welcome_message',
                    'content': self._generate_welcome_message(product_data),
                    'animation': 'warm_welcome',
                    'emotion': 'trust'
                },
                {
                    'type': 'value_proposition',
                    'content': self._generate_emotional_value_prop(product_data),
                    'animation': 'delightful_discover',
                    'emotion': 'delight'
                },
                {
                    'type': 'social_proof',
                    'content': self._generate_emotional_social_proof(product_data),
                    'animation': 'connection',
                    'emotion': 'connection'
                },
                {
                    'type': 'primary_cta',
                    'content': product_data.get('cta_text', 'Start Your Journey'),
                    'animation': 'button_press',
                    'emotion': 'joy',
                    'celebration': 'first_time'
                }
            ]
        }
    
    def generate_celebration_component(self, achievement_type: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate celebration component for achievements."""
        celebration_config = self.celebration_systems[achievement_type]
        emotion_config = self.emotional_palette[celebration_config['color_theme']]
        
        return {
            'component': 'CelebrationModal',
            'props': {
                'trigger': achievement_type,
                'autoShow': True,
                'duration': 3000,
                'closable': True
            },
            'elements': [
                {
                    'type': 'celebration_animation',
                    'animation': celebration_config['animations'],
                    'colors': emotion_config['colors'],
                    'particles': 50
                },
                {
                    'type': 'achievement_badge',
                    'badge': celebration_config['badge'],
                    'animation': 'success_pulse'
                },
                {
                    'type': 'celebration_message',
                    'message': celebration_config['message'].format(**user_data),
                    'emotion': celebration_config['color_theme']
                },
                {
                    'type': 'share_buttons',
                    'platforms': ['twitter', 'linkedin', 'facebook'],
                    'message': f"I just achieved {achievement_type} in this amazing app!"
                }
            ]
        }
    
    def generate_emotional_form(self, form_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate form with emotional feedback."""
        return {
            'component': 'EmotionalForm',
            'props': {
                'emotion': 'comfort',
                'validation_style': 'gentle',
                'success_celebration': 'sparkles'
            },
            'elements': [
                {
                    'type': 'welcome_field',
                    'placeholder': 'Let\'s get started on your journey...',
                    'animation': 'warm_welcome',
                    'emotion': 'trust'
                },
                {
                    'type': 'smart_fields',
                    'fields': form_config.get('fields', []),
                    'validation': {
                        'style': 'encouraging',
                        'error_animation': 'gentle_shake',
                        'success_animation': 'success_pulse'
                    }
                },
                {
                    'type': 'progress_celebration',
                    'milestones': form_config.get('milestones', []),
                    'animation': 'progress_joy'
                },
                {
                    'type': 'submit_button',
                    'text': form_config.get('submit_text', 'Begin Your Adventure'),
                    'animation': 'button_press',
                    'celebration': 'first_time'
                }
            ]
        }
    
    def generate_emotional_dashboard(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dashboard with emotional elements."""
        return {
            'component': 'EmotionalDashboard',
            'props': {
                'emotion': 'pride',
                'personalization': True,
                'celebrations': True
            },
            'elements': [
                {
                    'type': 'personalized_welcome',
                    'message': self._generate_personalized_welcome(dashboard_data),
                    'animation': 'warm_welcome',
                    'emotion': 'trust'
                },
                {
                    'type': 'achievement_showcase',
                    'achievements': dashboard_data.get('achievements', []),
                    'animation': 'pride_pulse'
                },
                {
                    'type': 'progress_visualization',
                    'progress': dashboard_data.get('progress', {}),
                    'animation': 'growth_celebration',
                    'emotion': 'pride'
                },
                {
                    'type': 'community_connection',
                    'community_data': dashboard_data.get('community', {}),
                    'animation': 'connection',
                    'emotion': 'connection'
                },
                {
                    'type': 'delightful_quick_actions',
                    'actions': dashboard_data.get('quick_actions', []),
                    'animation': 'hover_lift'
                }
            ]
        }
    
    def _generate_welcome_message(self, product_data: Dict[str, Any]) -> str:
        """Generate personalized welcome message."""
        user_name = product_data.get('user_name', 'Explorer')
        time_of_day = self._get_time_of_day()
        
        welcome_messages = {
            'morning': f"Good morning, {user_name}! ☀️ Ready to create something amazing today?",
            'afternoon': f"Hello {user_name}! 🌤 Let's make this afternoon productive!",
            'evening': f"Good evening, {user_name}! 🌙 Time to reflect and grow.",
            'night': f"Working late, {user_name}? 🌟 Your dedication inspires us!"
        }
        
        return welcome_messages.get(time_of_day, welcome_messages['morning'])
    
    def _generate_emotional_value_prop(self, product_data: Dict[str, Any]) -> str:
        """Generate emotionally resonant value proposition."""
        base_value = product_data.get('value_proposition', '')
        
        emotional_enhancers = {
            'joy': 'Experience the joy of',
            'trust': 'Trust in the power of',
            'delight': 'Delight in the magic of',
            'pride': 'Feel proud of your',
            'connection': 'Connect through',
            'comfort': 'Feel comfortable with'
        }
        
        emotion = product_data.get('emotional_theme', 'joy')
        enhancer = emotional_enhancers.get(emotion, 'Experience')
        
        return f"{enhancer} {base_value.lower()}"
    
    def _generate_emotional_social_proof(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate emotionally resonant social proof."""
        return {
            'testimonials': [
                {
                    'name': 'Sarah Chen',
                    'role': 'Creative Director',
                    'message': 'This product changed how I create. I feel inspired every day!',
                    'emotion': 'joy',
                    'avatar': '/api/avatars/sarah'
                },
                {
                    'name': 'Marcus Rodriguez',
                    'role': 'Entrepreneur',
                    'message': 'Finally, a tool that understands my needs. I feel truly supported.',
                    'emotion': 'trust',
                    'avatar': '/api/avatars/marcus'
                }
            ],
            'community_stats': [
                {
                    'label': 'Happy Creators',
                    'value': '10,000+',
                    'emotion': 'connection'
                },
                {
                    'label': 'Projects Completed',
                    'value': '50,000+',
                    'emotion': 'pride'
                },
                {
                    'label': 'Success Rate',
                    'value': '98%',
                    'emotion': 'trust'
                }
            ]
        }
    
    def _generate_personalized_welcome(self, dashboard_data: Dict[str, Any]) -> str:
        """Generate personalized dashboard welcome."""
        user_name = dashboard_data.get('user_name', 'Creator')
        achievement_count = len(dashboard_data.get('achievements', []))
        days_active = dashboard_data.get('days_active', 1)
        
        if achievement_count == 0:
            return f"Welcome back, {user_name}! 🌟 Ready to unlock your first achievement?"
        elif days_active == 1:
            return f"Amazing first day, {user_name}! 🎉 You're already making progress!"
        elif achievement_count > 5:
            return f"Incredible work, {user_name}! 🏆 You're a true master!"
        else:
            return f"Great to see you, {user_name}! 💪 Ready to continue your journey?"
    
    def _get_time_of_day(self) -> str:
        """Get current time of day for personalization."""
        from datetime import datetime
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def generate_emotional_component_code(self, component: Dict[str, Any]) -> str:
        """Generate React/TypeScript code for emotional components."""
        if component['component'] == 'EmotionalHero':
            return self._generate_emotional_hero_code(component)
        elif component['component'] == 'CelebrationModal':
            return self._generate_celebration_code(component)
        elif component['component'] == 'EmotionalForm':
            return self._generate_emotional_form_code(component)
        elif component['component'] == 'EmotionalDashboard':
            return self._generate_emotional_dashboard_code(component)
        else:
            return self._generate_generic_emotional_code(component)
    
    def _generate_emotional_hero_code(self, component: Dict[str, Any]) -> str:
        """Generate emotional hero component code."""
        return f"""
import {{ motion }} from 'framer-motion'
import {{ useState, useEffect }} from 'react'

export function EmotionalHero() {{
  const [isLoaded, setIsLoaded] = useState(false)
  
  useEffect(() => {{
    const timer = setTimeout(() => setIsLoaded(true), 100)
    return () => clearTimeout(timer)
  }}, [])
  
  return (
    <motion.div
      initial={{{{ opacity: 0, y: 20 }}}}
      animate={{{{ opacity: 1, y: 0 }}}}
      transition={{{{ duration: 0.8, ease: "easeOutBack" }}}}
      className="{component['props']['className']} relative overflow-hidden py-20 lg:py-32"
    >
      {/* Animated background elements */}
      <div className="absolute inset-0">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            initial={{{{ opacity: 0, scale: 0 }}}}
            animate={{{{ opacity: 0.1, scale: 1 }}}}
            transition={{{{ 
              delay: i * 0.1, 
              duration: 1.5,
              ease: "easeInOut" 
            }}}}
            className="absolute rounded-full bg-white opacity-10"
            style={{
              width: `${{Math.random() * 100 + 50}}px`,
              height: `${{Math.random() * 100 + 50}}px`,
              left: `${{Math.random() * 100}}%`,
              top: `${{Math.random() * 100}}%`,
            }}
          />
        ))}
      </div>
      
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{{{ opacity: 0, y: 30 }}}}
          animate={{{{ opacity: 1, y: 0 }}}}
          transition={{{{ delay: 0.3, duration: 0.8 }}}}
          className="text-center"
        >
          <h1 className="text-4xl font-bold text-white sm:text-6xl lg:text-7xl">
            Welcome to Your Journey
          </h1>
          <motion.p 
            initial={{{{ opacity: 0 }}}}
            animate={{{{ opacity: 1 }}}}
            transition={{{{ delay: 0.6, duration: 0.8 }}}}
            className="mt-6 text-xl text-white/90 max-w-3xl mx-auto"
          >
            Where amazing experiences await
          </motion.p>
          
          <motion.button
            initial={{{{ opacity: 0, scale: 0.8 }}}}
            animate={{{{ opacity: 1, scale: 1 }}}}
            whileHover={{{{ scale: 1.05 }}}}
            whileTap={{{{ scale: 0.95 }}}}
            transition={{{{ type: "spring", stiffness: 400, damping: 17 }}}}
            className="mt-10 px-8 py-4 bg-white text-blue-600 rounded-full font-semibold text-lg shadow-lg hover:shadow-xl"
          >
            Begin Your Adventure
          </motion.button>
        </motion.div>
      </div>
    </motion.div>
  )
}}
"""
    
    def _generate_celebration_code(self, component: Dict[str, Any]) -> str:
        """Generate celebration modal component code."""
        return f"""
import {{ motion, AnimatePresence }} from 'framer-motion'
import {{ useEffect, useState }} from 'react'
import Confetti from 'react-confetti'

export function CelebrationModal({{ trigger, achievement }}) {{
  const [showConfetti, setShowConfetti] = useState(false)
  
  useEffect(() => {{
    if (trigger) {{
      setShowConfetti(true)
      const timer = setTimeout(() => setShowConfetti(false), 3000)
      return () => clearTimeout(timer)
    }}
  }}, [trigger])
  
  return (
    <AnimatePresence>
      {trigger && (
        <motion.div
          initial={{{{ opacity: 0 }}}
          animate={{{{ opacity: 1 }}}
          exit={{{{ opacity: 0 }}}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        >
          {showConfetti && <Confetti />}
          
          <motion.div
            initial={{{{ scale: 0.5, opacity: 0 }}}
            animate={{{{ scale: 1, opacity: 1 }}}
            exit={{{{ scale: 0.8, opacity: 0 }}}
            transition={{{{ type: "spring", damping: 20, stiffness: 300 }}}}
            className="bg-white rounded-2xl p-8 max-w-md mx-4 text-center shadow-2xl"
          >
            <motion.div
              initial={{{{ rotate: 0 }}}
              animate={{{{ rotate: [0, 10, -10, 0] }}}
              transition={{{{ duration: 0.5, repeat: 3, repeatDelay: 0.2 }}}}
              className="text-6xl mb-4"
            >
              🎉
            </motion.div>
            
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Achievement Unlocked!
            </h2>
            
            <p className="text-gray-600 mb-6">
              {{achievement?.message || 'You are amazing!'}}
            </p>
            
            <motion.button
              whileHover={{{{ scale: 1.05 }}}}
              whileTap={{{{ scale: 0.95 }}}}
              onClick={() => {/* close modal */}}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Continue
            </motion.button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}}
"""
    
    def _generate_emotional_form_code(self, component: Dict[str, Any]) -> str:
        """Generate emotional form component code."""
        return f"""
import {{ motion }} from 'framer-motion'
import {{ useState }} from 'react'

export function EmotionalForm() {{
  const [formData, setFormData] = useState({{})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState({{})
  
  const handleSubmit = async (e) => {{
    e.preventDefault()
    setIsSubmitting(true)
    
    // Simulate submission with emotional feedback
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Trigger celebration
    if (window.triggerCelebration) {{
      window.triggerCelebration('first_time')
    }}
    
    setIsSubmitting(false)
  }}
  
  const handleInputChange = (field, value) => {{
    setFormData(prev => ({{ ...prev, [field]: value }}))
    // Clear error when user starts typing
    if (errors[field]) {{
      setErrors(prev => ({{ ...prev, [field]: null }}))
    }}
  }}
  
  return (
    <motion.form
      initial={{{{ opacity: 0, y: 20 }}}}
      animate={{{{ opacity: 1, y: 0 }}}}
      onSubmit={handleSubmit}
      className="max-w-md mx-auto p-8 bg-white rounded-2xl shadow-xl"
    >
      <motion.div
        initial={{{{ opacity: 0 }}}
        animate={{{{ opacity: 1 }}}
        transition={{{{ delay: 0.2 }}}}
        className="text-center mb-8"
      >
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Let's Begin Your Journey ✨
        </h2>
        <p className="text-gray-600">
          We're excited to have you here!
        </p>
      </motion.div>
      
      <div className="space-y-6">
        <motion.div
          initial={{{{ x: -20, opacity: 0 }}}
          animate={{{{ x: 0, opacity: 1 }}}
          transition={{{{ delay: 0.3 }}}}
        >
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Name
          </label>
          <motion.input
            whileFocus={{{{ scale: 1.02 }}}}
            transition={{{{ type: "spring", stiffness: 300 }}}
            type="text"
            value={formData.name || ''}
            onChange={(e) => handleInputChange('name', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            placeholder="What should we call you?"
          />
        </motion.div>
        
        <motion.div
          initial={{{{ x: -20, opacity: 0 }}}
          animate={{{{ x: 0, opacity: 1 }}}
          transition={{{{ delay: 0.4 }}}}
        >
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email
          </label>
          <motion.input
            whileFocus={{{{ scale: 1.02 }}}}
            transition={{{{ type: "spring", stiffness: 300 }}}
            type="email"
            value={formData.email || ''}
            onChange={(e) => handleInputChange('email', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            placeholder="your@email.com"
          />
        </motion.div>
      </div>
      
      <motion.button
        initial={{{{ y: 20, opacity: 0 }}}
        animate={{{{ y: 0, opacity: 1 }}}
        transition={{{{ delay: 0.5 }}}}
        whileHover={{{{ scale: 1.05, y: -2 }}}}
        whileTap={{{{ scale: 0.95 }}}}
        disabled={isSubmitting}
        type="submit"
        className="w-full py-3 px-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        {isSubmitting ? (
          <motion.span
            animate={{{{ rotate: 360 }}}}
            transition={{{{ duration: 1, repeat: Infinity, ease: "linear" }}}}
          >
            ⏳
          </motion.span>
        ) : (
          "Start Your Adventure 🚀"
        )}
      </motion.button>
    </motion.form>
  )
}}
"""
    
    def _generate_emotional_dashboard_code(self, component: Dict[str, Any]) -> str:
        """Generate emotional dashboard component code."""
        return f"""
import {{ motion }} from 'framer-motion'
import {{ useState, useEffect }} from 'react'

export function EmotionalDashboard() {{
  const [streak, setStreak] = useState(7)
  const [achievements, setAchievements] = useState([])
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Emotional Welcome Header */}
      <motion.div
        initial={{{{ y: -20, opacity: 0 }}}}
        animate={{{{ y: 0, opacity: 1 }}}
        className="bg-white shadow-sm border-b border-gray-100"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <motion.div
            initial={{{{ scale: 0.9, opacity: 0 }}}}
            animate={{{{ scale: 1, opacity: 1 }}}
            transition={{{{ type: "spring", damping: 20, stiffness: 300 }}}}
            className="flex items-center justify-between"
          >
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Welcome back, Creator! 🌟
              </h1>
              <p className="text-gray-600">
                You're on a {{streak}} day streak! 🔥
              </p>
            </div>
            
            <motion.div
              animate={{{{ rotate: [0, 5, -5, 0] }}}
              transition={{{{ duration: 2, repeat: Infinity, repeatDelay: 0 }}}}
              className="text-4xl"
            >
              ⭐
            </motion.div>
          </motion.div>
        </div>
      </motion.div>
      
      {/* Achievement Showcase */}
      <motion.div
        initial={{{{ opacity: 0, y: 20 }}}}
        animate={{{{ opacity: 1, y: 0 }}}
        transition={{{{ delay: 0.2 }}}}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      >
        <h2 className="text-xl font-bold text-gray-900 mb-6">
          Your Achievements 🏆
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {achievements.map((achievement, index) => (
            <motion.div
              key={achievement.id}
              initial={{{{ opacity: 0, scale: 0.8 }}}}
              animate={{{{ opacity: 1, scale: 1 }}}
              transition={{{{ delay: index * 0.1 }}}}
              whileHover={{{{ y: -5, shadow: "0 10px 30px rgba(0,0,0,0.15)" }}}}
              className="bg-white rounded-xl p-6 shadow-lg border border-gray-100"
            >
              <div className="text-3xl mb-3">{achievement.icon}</div>
              <h3 className="font-semibold text-gray-900 mb-2">
                {achievement.name}
              </h3>
              <p className="text-gray-600 text-sm">
                {achievement.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}}
"""
    
    def _generate_generic_emotional_code(self, component: Dict[str, Any]) -> str:
        """Generate generic emotional component code."""
        return f"""
import {{ motion }} from 'framer-motion'

export function {component.get('name', 'EmotionalComponent')}() {{
  return (
    <motion.div
      initial={{{{ opacity: 0, scale: 0.9 }}}}
      animate={{{{ opacity: 1, scale: 1 }}}
      whileHover={{{{ scale: 1.05 }}}}
      transition={{{{ type: "spring", stiffness: 300, damping: 30 }}}}
      className="{component.get('props', {}).get('className', '')}"
    >
      {component.get('content', '')}
    </motion.div>
  )
}}
"""
