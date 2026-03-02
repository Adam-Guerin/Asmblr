"""Loveability Engineer Agent for creating Most Lovable Products (MLP)."""

from typing import Any
from crewai import Agent, Task
from langchain.tools import Tool
from ..core.llm import LLMClient
import logging

logger = logging.getLogger(__name__)


class LoveabilityEngineerAgent:
    """Specialized agent for creating Most Lovable Products with emotional addiction."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create loveability engineer agent."""
        return Agent(
            role="Loveability Engineer & Product Craftsman",
            goal="Create products that users ADORE and can't imagine living without",
            backstory="""You are a legendary product creator who has built products that achieved 
            cult-like followings and passionate user communities. You specialize in:
            
            - Loveability psychology and emotional addiction engineering
            - Creating magical user experiences that feel impossible
            - Building tribal communities around products
            - Identity integration and self-expression features
            - Habit formation and daily ritual creation
            - Unforgettable details and delightful surprises
            - Community culture and tribal knowledge systems
            
            Your products consistently achieve 90%+ emotional attachment scores and create 
            users who become passionate evangelists. You understand that great products 
            aren't just used - they're LOVED, integrated into identity, and become 
            part of users' life stories.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_client
        )
    
    def create_loveability_strategy_task(self, product_data: dict[str, Any]) -> Task:
        """Create task for developing loveability strategy."""
        return Task(
            description=f"""
            Develop a comprehensive loveability strategy for creating emotional addiction.
            
            Product Data:
            {product_data}
            
            Loveability Strategy Requirements:
            1. Design emotional addiction patterns with dopamine loops
            2. Create magical moments that feel impossible
            3. Build identity integration and self-expression systems
            4. Engineer community culture and tribal bonding
            5. Design habit formation with meaningful rituals
            6. Create unforgettable details and surprise delights
            7. Implement anticipation and withdrawal avoidance systems
            
            Emotional Addiction Framework:
            - VARIABLE REWARDS: Unpredictable delight moments
            - ANTICIPATION BUILDING: Hint at future possibilities
            - CELEBRATION SPECTACLES: Over-the-top achievement recognition
            - WITHDRAWAL MINIMIZATION: Comfort when away from product
            - RITUAL CREATION: Daily meaningful interactions
            - IDENTITY MERGING: Product becomes part of self-image
            
            Magical Experience Engineering:
            - SERENDIPITOUS TIMING: Perfect "just what I needed" moments
            - PREDICTIVE ASSISTANCE: Anticipate needs before awareness
            - CONTEXTUAL MAGIC: Adapt to situation/location/time perfectly
            - SURPRISE EVOLUTION: Product grows and reveals new capabilities
            - PERSONAL RITUALS: Daily interactions become traditions
            - EMOTIONAL INTELLIGENCE: Respond to mood and state
            
            Deliverable:
            Complete loveability strategy with emotional addiction framework and magical experience design
            """,
            agent=self.agent,
            expected_output="Comprehensive loveability strategy with emotional addiction patterns and magical experiences"
        )
    
    def create_identity_integration_task(self, user_psychology: dict[str, Any]) -> Task:
        """Create task for identity integration systems."""
        return Task(
            description=f"""
            Design identity integration systems that merge product with user self-image.
            
            User Psychology:
            {user_psychology}
            
            Identity Integration Requirements:
            1. Create visual status symbols and achievement badges
            2. Design skill progression and mastery trees
            3. Build personal narrative and story crafting tools
            4. Implement exclusive access and special recognition
            5. Create achievement showcases and accomplishment displays
            6. Design custom avatars and identity expression
            7. Build "product user" identity and community belonging
            
            Identity Systems Design:
            - VISUAL BADGES: Display achievements, status, expertise levels
            - SKILL TREES: Show progression paths and mastery journey
            - PERSONAL STORIES: Help users craft their product narrative
            - EXCLUSIVE REWARDS: Unlock special features and recognition
            - CUSTOM AVATARS: Express identity through visual representation
            - ACHIEVEMENT SHOWCASES: Beautiful displays of accomplishments
            - IDENTITY METRICS: Track growth and integration over time
            
            Psychological Integration:
            - SELF-EXPRESSION: Tools for users to show uniqueness
            - SOCIAL STATUS: Visible indicators of expertise and achievements
            - PERSONAL GROWTH: Clear progression and development paths
            - COMMUNITY IDENTITY: "We are [product] users" tribal feeling
            - EXCLUSIVE ACCESS: Make users feel special and chosen
            - ACHIEVEMENT PRIDE: Celebrate accomplishments beautifully
            - NARRATIVE OWNERSHIP: Help users tell their product story
            
            Implementation Requirements:
            - Achievement tracking and unlocking system
            - Visual badge and status display components
            - Personal profile and narrative tools
            - Skill progression visualization
            - Custom avatar and identity customization
            - Social sharing for achievements and stories
            - Analytics for identity integration metrics
            
            Expected Psychological Impact:
            - IDENTITY MERGER: "This product is part of who I am"
            - STATUS PRIDE: "My achievements show my expertise"
            - COMMUNITY BELONGING: "I belong to this special group"
            - SELF-EXPRESSION: "This product lets me be myself"
            - GROWTH SATISFACTION: "I can see my progress and development"
            
            Deliverable:
            Complete identity integration system with badges, progression, and narrative tools
            """,
            agent=self.agent,
            expected_output="Identity integration system with visual badges, skill progression, and personal narrative tools"
        )
    
    def create_community_culture_task(self, social_dynamics: dict[str, Any]) -> Task:
        """Create task for building community culture and tribal bonding."""
        return Task(
            description=f"""
            Design community culture systems that create passionate tribal bonding.
            
            Social Dynamics:
            {social_dynamics}
            
            Community Culture Requirements:
            1. Create shared language and insider terminology
            2. Build mentorship networks and knowledge sharing
            3. Design collaborative rituals and community activities
            4. Implement shared stories and cultural artifacts
            5. Create cultural celebrations and community milestones
            6. Build tribal knowledge and expertise systems
            7. Design inclusive onboarding for community culture
            
            Tribal Culture Design:
            - SHARED LANGUAGE: Insider jokes, terminology, and communication style
            - MENTORSHIP NETWORKS: Connect experienced users with newcomers
            - COLLABORATIVE RITUALS: Community activities and challenges
            - SHARED STORIES: User narratives and experience sharing platforms
            - CULTURAL CELEBRATIONS: Community achievements and milestones
            - TRIBAL KNOWLEDGE: Collective wisdom and expertise sharing
            - CULTURAL ARTIFACTS: Memes, stories, and shared symbols
            - RITUAL PARTICIPATION: Regular community bonding activities
            
            Community Bonding Psychology:
            - INGROUP IDENTITY: "We are [product] users" exclusivity
            - SHARED EXPERTISE: Collective knowledge and wisdom systems
            - RITUAL PARTICIPATION: Regular bonding activities and traditions
            - MENTORSHIP PRIDE: Experienced users guide and celebrate newcomers
            - CULTURAL CONTINUITY: Evolving traditions and shared history
            - COLLABORATIVE IDENTITY: Group achievements and collective success
            - EXCLUSIVE KNOWLEDGE: Insider information and expertise sharing
            
            Implementation Features:
            - Community forums and discussion platforms
            - Mentorship matching and guidance systems
            - Collaborative challenges and activities
            - Story sharing and narrative platforms
            - Cultural celebration and milestone systems
            - Knowledge base and expertise sharing
            - Community onboarding and cultural education
            - Social analytics and community health tracking
            
            Expected Community Impact:
            - TRIBAL BONDING: Strong sense of belonging and identity
            - KNOWLEDGE SHARING: Collective expertise and wisdom development
            - MENTORSHIP CULTURE: Experienced users guide and support newcomers
            - CULTURAL CONTINUITY: Evolving traditions and shared history
            - COLLABORATIVE PRIDE: Group achievements and collective success
            - INGROUP LOYALTY: Passionate advocacy and community defense
            
            Deliverable:
            Complete community culture system with tribal bonding, mentorship, and cultural features
            """,
            agent=self.agent,
            expected_output="Community culture system with tribal bonding, mentorship networks, and shared knowledge"
        )
    
    def create_habit_formation_task(self, behavioral_psychology: dict[str, Any]) -> Task:
        """Create task for habit formation and daily ritual engineering."""
        return Task(
            description=f"""
            Design habit formation systems that make product usage meaningful and essential.
            
            Behavioral Psychology:
            {behavioral_psychology}
            
            Habit Formation Requirements:
            1. Create daily rituals that users look forward to
            2. Design streak celebrations and over-the-top recognition
            3. Build progression joy and meaningful advancement
            4. Implement anticipation systems for tomorrow's possibilities
            5. Create gentle withdrawal discomfort when not used
            6. Design return celebrations and welcome back rituals
            7. Build meaningful routine integration patterns
            
            Habit Engineering Framework:
            - DAILY RITUALS: Meaningful interactions users anticipate daily
            - STREAK CELEBRATIONS: Over-the-top daily/weekly recognition
            - PROGRESSION JOY: Make advancement feel magical and rewarding
            - ANTICIPATION BUILDING: Tomorrow's possibilities revealed today
            - WITHDRAWAL SENSATION: Create gentle discomfort when away
            - RETURN CELEBRATIONS: Welcome back with excitement and recognition
            - ROUTINE INTEGRATION: Product becomes part of daily life patterns
            
            Behavioral Psychology Integration:
            - DOPAMINE LOOPING: Variable rewards + anticipation + celebration
            - ROUTINE ANCHORING: Connect product to existing daily habits
            - PROGRESS SATISFACTION: Clear advancement and growth visibility
            - SOCIAL ACCOUNTABILITY: Community support for habit maintenance
            - PERSONAL MEANING: Connect usage to personal values and goals
            - ANTICIPATION DOPAMINE: Build excitement for future interactions
            - MISSING SENSATION: Create gentle pull to return to product
            
            Implementation Systems:
            - Daily ritual tracking and celebration systems
            - Streak monitoring and over-the-top recognition
            - Progress visualization and achievement displays
            - Anticipation and future possibility reveals
            - Usage pattern analysis and habit insights
            - Social accountability and community support
            - Personal meaning and goal integration tools
            - Return celebration and welcome back systems
            
            Expected Habit Formation Impact:
            - DAILY ENGAGEMENT: 80%+ users return daily voluntarily
            - HABIT INTEGRATION: 85%+ product part of daily routine
            - ANTICIPATION EXCITEMENT: Users look forward to product interactions
            - WITHDRAWAL AVOIDANCE: Users miss product when away
            - PROGRESSION SATISFACTION: Clear growth and advancement feeling
            - MEANINGFUL ROUTINES: Product connected to personal values and goals
            
            Deliverable:
            Complete habit formation system with daily rituals, streak celebrations, and meaningful routine integration
            """,
            agent=self.agent,
            expected_output="Habit formation system with daily rituals, streak celebrations, and meaningful routine integration"
        )
    
    def create_magical_experiences_task(self, experience_design: dict[str, Any]) -> Task:
        """Create task for engineering magical user experiences."""
        return Task(
            description=f"""
            Design magical experiences that create "how does it do that?" moments.
            
            Experience Design:
            {experience_design}
            
            Magical Experience Requirements:
            1. Create serendipitous timing and perfect moments
            2. Implement predictive assistance and anticipatory features
            3. Design contextual magic based on situation and time
            4. Create surprise evolution and product growth
            5. Build personal rituals and meaningful traditions
            6. Implement emotional intelligence and mood responsiveness
            7. Create discoverable magic and hidden delightful features
            
            Magical Experience Engineering:
            - SERENDIPITOUS TIMING: Features appear exactly when needed
            - PREDICTIVE ASSISTANCE: Anticipate user needs before awareness
            - CONTEXTUAL MAGIC: Adapt to situation/location/time perfectly
            - SURPRISE EVOLUTION: Product grows and reveals new capabilities
            - PERSONAL RITUALS: Daily interactions become meaningful traditions
            - EMOTIONAL INTELLIGENCE: Respond to mood and state
            - DISCOVERABLE MAGIC: Hidden features users find and share
            
            Magic Psychology Principles:
            - IMPOSSIBLE PERCEPTION: Features seem to defy normal limitations
            - PERFECT TIMING: "Just what I needed" moments throughout experience
            - CONTEXTUAL AWARENESS: Product understands situation without being told
            - PERSONAL CONNECTION: Magic feels uniquely tailored to individual user
            - EVOLUTIONARY DELIGHT: Product continuously improves and surprises
            - EMOTIONAL RESPONSIVENESS: Adapts to user mood and emotional state
            - DISCOVERABLE WONDERS: Hidden features create sharing and delight
            
            Implementation Features:
            - Predictive analytics and anticipatory systems
            - Context-aware adaptation and personalization
            - Surprise feature reveals and evolution systems
            - Emotional intelligence and mood detection
            - Personal ritual and tradition creation tools
            - Hidden feature discovery and sharing systems
            - Magical moment tracking and celebration
            - Contextual assistance and just-in-time help
            
            Expected Magical Impact:
            - WONDER EXPERIENCE: "How does it do that?" moments throughout use
            - PERSONAL MAGIC: Features feel uniquely tailored and intelligent
            - SURPRISE DELIGHT: Continuous discovery of new capabilities
            - EMOTIONAL CONNECTION: Product responds to user's emotional state
            - CONTEXTUAL MASTERY: Perfect adaptation to situation and needs
            - EVOLUTIONARY EXCITEMENT: Product grows and improves continuously
            - SHARABLE MAGIC: Users share discoveries with community
            
            Deliverable:
            Complete magical experience system with predictive assistance, contextual magic, and delightful surprises
            """,
            agent=self.agent,
            expected_output="Magical experience system with predictive assistance, contextual magic, and delightful surprises"
        )
    
    def get_loveability_tools(self) -> list[Tool]:
        """Get loveability engineering tools for the agent."""
        return [
            Tool(
                name="emotional_addiction_designer",
                description="Design emotional addiction patterns with dopamine loops",
                func=lambda: "Emotional addiction designer for creating user craving and attachment"
            ),
            Tool(
                name="magical_experience_engineer",
                description="Create magical moments that feel impossible and delightful",
                func=lambda: "Magical experience engineer for serendipitous timing and predictive assistance"
            ),
            Tool(
                name="identity_integration_builder",
                description="Build identity merging systems and self-expression tools",
                func=lambda: "Identity integration builder for product-self image merger and status symbols"
            ),
            Tool(
                name="tribal_culture_designer",
                description="Create community culture and tribal bonding systems",
                func=lambda: "Tribal culture designer for community rituals and shared language"
            ),
            Tool(
                name="habit_formation_engineer",
                description="Design habit formation systems with meaningful daily rituals",
                func=lambda: "Habit formation engineer for daily routines and meaningful integration"
            ),
            Tool(
                name="loveability_metrics_tracker",
                description="Track emotional attachment and user love metrics",
                func=lambda: "Loveability metrics tracker for measuring user addiction and advocacy"
            ),
            Tool(
                name="unforgettable_detail_crafter",
                description="Create small delightful details users treasure and share",
                func=lambda: "Unforgettable detail crafter for surprise moments and hidden delights"
            )
        ]
