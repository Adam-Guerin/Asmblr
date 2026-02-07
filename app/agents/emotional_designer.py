"""Emotional Design Agent for creating products that evoke powerful feelings."""

from typing import Dict, Any, List, Optional
from crewai import Agent, Task
from langchain.tools import Tool
from ..core.llm import LLMClient
import logging

logger = logging.getLogger(__name__)


class EmotionalDesignerAgent:
    """Specialized agent for emotional design and user experience psychology."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the emotional design agent."""
        return Agent(
            role="Emotional Design & Psychology Specialist",
            goal="Create products that evoke powerful emotions and build deep user connections",
            backstory="""You are a world-class emotional designer with deep expertise in psychology, 
            neuroscience, and human-computer interaction. You specialize in:
            
            - Emotional design psychology and user behavior
            - Creating delight, trust, and connection through interfaces
            - Micro-interactions that spark positive emotions
            - Building products users LOVE, not just use
            - Celebration systems and achievement recognition
            - Personalization that makes users feel understood
            - Community features that create belonging
            
            You've helped create products that users describe as "magical," "delightful," 
            and "life-changing." Your designs consistently achieve 90%+ emotional engagement 
            and create passionate user communities.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_client
        )
    
    def create_emotional_onboarding_task(self, product_data: Dict[str, Any]) -> Task:
        """Create task for designing emotionally resonant onboarding."""
        return Task(
            description=f"""
            Design an emotionally captivating onboarding experience that creates immediate user connection.
            
            Product Data:
            {product_data}
            
            Emotional Onboarding Requirements:
            1. Create "wow" moment within first 3 seconds
            2. Build immediate trust and comfort
            3. Establish emotional connection and belonging
            4. Generate excitement for product possibilities
            5. Celebrate user's decision to join
            6. Personalize experience from first interaction
            
            Specific Emotional Elements:
            - WARM WELCOME: Personalized greeting that feels human
            - VISUAL DELIGHT: Beautiful animations and transitions
            - PROGRESS CELEBRATION: Acknowledge each step completed
            - ANTICIPATION BUILDING: Hint at amazing features ahead
            - SOCIAL CONNECTION: Show they're joining a community
            - ACHIEVEMENT UNLOCK: First milestone celebration
            
            Technical Implementation:
            - Framer Motion for smooth, emotional animations
            - Personalized content based on user context
            - Progress indicators with emotional feedback
            - Celebration animations with confetti/effects
            - Sound design for key moments (optional)
            - Mobile-optimized touch interactions
            
            Expected Emotional Journey:
            Curiosity → Excitement → Trust → Pride → Belonging → Anticipation
            
            Deliverable:
            Complete onboarding flow with emotional design specifications and implementation code
            """,
            agent=self.agent,
            expected_output="Emotionally resonant onboarding experience with celebration system and personalization"
        )
    
    def create_delightful_interactions_task(self, ui_components: Dict[str, Any]) -> Task:
        """Create task for designing delightful micro-interactions."""
        return Task(
            description=f"""
            Design delightful micro-interactions that spark joy throughout the user experience.
            
            UI Components:
            {ui_components}
            
            Delightful Interaction Requirements:
            1. Add emotional feedback to every user action
            2. Create surprise moments and hidden delights
            3. Implement smooth, physics-based animations
            4. Design celebration moments for achievements
            5. Add personality through motion and feedback
            6. Create emotional responses to user input
            
            Specific Interaction Patterns:
            - BUTTON DELIGHT: Satisfying click animations with spring physics
            - FORM CELEBRATION: Confetti or animation on successful submission
            - PROGRESS JOY: Animated progress that feels rewarding
            - ERROR COMFORT: Gentle, reassuring error recovery
            - DISCOVERY SURPRISE: Hidden features and Easter eggs
            - LOADING DELIGHT: Beautiful loading states that build anticipation
            
            Emotional Animation Specifications:
            - Spring physics with custom tension/friction
            - Stagger animations for natural movement
            - Morphing transitions between states
            - Particle effects for celebrations
            - Haptic feedback on mobile devices
            - Sound design for emotional enhancement
            
            Implementation Requirements:
            - Framer Motion with custom animation presets
            - Performance optimization for 60fps animations
            - Reduced motion preferences support
            - Accessibility considerations for animations
            - Mobile gesture support
            - Cross-browser compatibility
            
            Expected Emotional Impact:
            Joy → Delight → Surprise → Pride → Connection → Motivation
            
            Deliverable:
            Complete micro-interaction system with animation library and emotional feedback
            """,
            agent=self.agent,
            expected_output="Delightful micro-interaction system with emotional animations and celebrations"
        )
    
    def create_celebration_system_task(self, user_journey: Dict[str, Any]) -> Task:
        """Create task for designing achievement celebration system."""
        return Task(
            description=f"""
            Design a comprehensive celebration system that acknowledges every user achievement.
            
            User Journey:
            {user_journey}
            
            Celebration System Requirements:
            1. Identify meaningful milestones and achievements
            2. Create unique celebrations for different achievement types
            3. Implement progressive celebration tiers
            4. Add social sharing for achievements
            5. Build streak and habit celebrations
            6. Create personal best and improvement celebrations
            
            Achievement Categories:
            - FIRST MILESTONES: First login, first action, first completion
            - HABIT FORMATION: Daily/weekly streaks, consistent usage
            - MASTERY MOMENTS: Complex tasks completed, skills developed
            - SOCIAL CONTRIBUTIONS: Helping others, community participation
            - PERSONAL GROWTH: Improvement over time, new capabilities
            - CREATIVE EXPRESSION: Personalization, content creation
            
            Celebration Design Elements:
            - VISUAL SPECTACLE: Confetti, particles, light effects
            - ANIMATION VARIETY: Different styles for achievement types
            - SOUND DESIGN: Celebration audio (optional, user-controlled)
            - HAPTIC FEEDBACK: Mobile vibration patterns
            - SOCIAL RECOGNITION: Shareable celebration moments
            - PROGRESSION VISIBILITY: Clear advancement indicators
            
            Technical Implementation:
            - Achievement tracking and unlocking system
            - Animation library with celebration presets
            - Social media integration for sharing
            - Analytics for celebration effectiveness
            - Personalization options for celebration style
            - Performance optimization for smooth animations
            
            Emotional Impact Goals:
            - PRIDE: Feel accomplished and skilled
            - BELONGING: Feel part of community
            - MOTIVATION: Excited for next achievement
            - RECOGNITION: Feel seen and valued
            - JOY: Pure delight in achievement
            
            Deliverable:
            Complete celebration system with achievement tracking, animations, and social features
            """,
            agent=self.agent,
            expected_output="Comprehensive celebration system with emotional rewards and social recognition"
        )
    
    def create_emotional_personalization_task(self, user_data: Dict[str, Any]) -> Task:
        """Create task for emotional personalization."""
        return Task(
            description=f"""
            Design emotional personalization that makes users feel understood and valued.
            
            User Data:
            {user_data}
            
            Emotional Personalization Requirements:
            1. Adapt interface based on user emotional preferences
            2. Personalize communication tone and style
            3. Customize celebration and feedback styles
            4. Adapt content based on emotional responses
            5. Create sense of individual recognition
            6. Build emotional intelligence over time
            
            Personalization Dimensions:
            - VISUAL PREFERENCES: Color schemes, animation intensity, layout density
            - COMMUNICATION TONE: Formal/casual, enthusiastic/calm, direct/gentle
            - CELEBRATION STYLE: Subtle/expressive, quiet/audible, simple/elaborate
            - FEEDBACK SENSITIVITY: High/low responsiveness, encouragement level
            - SOCIAL COMFORT: Private/shared achievements, community visibility
            - LEARNING PACE: Fast/slow feature introduction, complexity progression
            
            Emotional Adaptation System:
            - MOOD DETECTION: Adapt based on interaction patterns
            - PREFERENCE LEARNING: Remember user choices and reactions
            - CONTEXT AWARENESS: Time of day, usage patterns, goals
            - EMOTIONAL RESPONSE: Adjust based on user emotional state
            - GROWTH ACCOMPANIMENT: Support user development journey
            - COMFORT OPTIMIZATION: Create safe, trusted experience
            
            Implementation Features:
            - User preference profiles with emotional settings
            - Adaptive UI that learns from user behavior
            - Personalized content recommendations
            - Customizable celebration and feedback systems
            - Emotional analytics and insights
            - Privacy-respecting personalization
            
            Expected Emotional Outcomes:
            - UNDERSTOOD: "This product gets me"
            - VALUED: "My preferences matter here"
            - COMFORTABLE: "This feels like my space"
            - SUPPORTED: "This helps me grow"
            - CONNECTED: "This is part of my life"
            
            Deliverable:
            Complete emotional personalization system with adaptive intelligence and user controls
            """,
            agent=self.agent,
            expected_output="Emotional personalization system that makes users feel understood and valued"
        )
    
    def create_community_belonging_task(self, social_features: Dict[str, Any]) -> Task:
        """Create task for designing community and belonging features."""
        return Task(
            description=f"""
            Design community features that create deep sense of belonging and connection.
            
            Social Features:
            {social_features}
            
            Community Belonging Requirements:
            1. Create spaces for user interaction and connection
            2. Facilitate meaningful relationships between users
            3. Celebrate community achievements and milestones
            4. Design for both extroverted and introverted users
            5. Create mentorship and knowledge sharing opportunities
            6. Build shared identity and purpose
            
            Community Design Elements:
            - SHARED SPACES: Community areas, forums, discussion boards
            - SOCIAL PRESENCE: See other users, activity indicators
            - COLLABORATIVE FEATURES: Work together, create together
            - MENTORSHIP SYSTEMS: Connect experienced with new users
            - COMMUNITY STORIES: Highlight user journeys and successes
            - SHARED CELEBRATIONS: Group achievements and milestones
            
            Emotional Connection Patterns:
            - WELCOME WAGON: New user integration and support
            - BUDDY SYSTEM: Pair users for mutual support
            - COMMUNITY CHALLENGES: Goals that unite users
            - SUCCESS SHARING: Celebrate each other's achievements
            - KNOWLEDGE EXCHANGE: Help and learn from each other
            - COLLECTIVE IDENTITY: Build shared purpose and values
            
            Implementation Requirements:
            - User profiles with social features
            - Real-time chat and messaging systems
            - Community content creation and sharing
            - Social notification systems
            - Moderation and safety features
            - Analytics for community health
            
            Emotional Safety Features:
            - INCLUSIVE DESIGN: Welcome diverse users and perspectives
            - CONFLICT RESOLUTION: Healthy disagreement handling
            - PRIVACY CONTROLS: User control over social visibility
            - SUPPORT SYSTEMS: Help for users in distress
            - BOUNDARY RESPECT: Clear social guidelines and enforcement
            - ACCESSIBILITY: Social features usable by all users
            
            Expected Emotional Impact:
            - BELONGING: "I'm part of something special"
            - SUPPORTED: "People here have my back"
            - VALUED: "My contributions matter"
            - CONNECTED: "I have meaningful relationships"
            - INSPIRED: "Others motivate me to grow"
            
            Deliverable:
            Complete community system with social features, safety measures, and emotional connection design
            """,
            agent=self.agent,
            expected_output="Community belonging system that creates deep user connection and emotional safety"
        )
    
    def get_emotional_design_tools(self) -> List[Tool]:
        """Get emotional design-specific tools for the agent."""
        return [
            Tool(
                name="emotional_journey_mapper",
                description="Map emotional journey through user experience",
                func=lambda: "Emotional journey mapping tool for identifying key emotional touchpoints"
            ),
            Tool(
                name="delight_moment_designer",
                description="Design micro-delight moments and surprise interactions",
                func=lambda: "Delight moment designer for creating joyful user interactions"
            ),
            Tool(
                name="celebration_system_builder",
                description="Build achievement celebration and recognition systems",
                func=lambda: "Celebration system builder for emotional reward mechanisms"
            ),
            Tool(
                name="emotional_personalizer",
                description="Create personalized emotional experiences",
                func=lambda: "Emotional personalizer for adaptive user experiences"
            ),
            Tool(
                name="community_belonging_designer",
                description="Design features that create community connection",
                func=lambda: "Community belonging designer for social connection features"
            ),
            Tool(
                name="emotional_analytics_tracker",
                description="Track emotional engagement and satisfaction",
                func=lambda: "Emotional analytics tracker for measuring user emotional responses"
            )
        ]
