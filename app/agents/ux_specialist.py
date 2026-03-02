"""UX Specialist Agent for creating seamless user experiences."""

from typing import Any
from crewai import Agent, Task
from langchain.tools import Tool
from ..core.llm import LLMClient
import logging

logger = logging.getLogger(__name__)


class UXSpecialistAgent:
    """Specialized agent for UX/UI design and seamless user flows."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the UX specialist agent."""
        return Agent(
            role="UX/UI Design Specialist",
            goal="Create seamless, conversion-optimized user experiences that delight users and drive business results",
            backstory="""You are a world-class UX/UI designer with 15+ years of experience creating 
            user experiences for startups and Fortune 500 companies. You specialize in:
            
            - Seamless user flows that eliminate friction
            - Conversion psychology that drives action
            - Mobile-first responsive design
            - Accessibility-first inclusive design
            - Micro-interactions that create delight
            - Design systems that ensure consistency
            
            You've helped dozens of startups achieve product-market fit through exceptional UX.
            Your designs consistently achieve 90%+ user satisfaction and industry-leading conversion rates.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_client
        )
    
    def create_seamless_userflow_task(self, prd_data: dict[str, Any], 
                                   tech_spec: dict[str, Any]) -> Task:
        """Create task for designing seamless user flows."""
        return Task(
            description=f"""
            Design a seamless user flow for this MVP based on the PRD and technical specifications.
            
            PRD Data:
            {prd_data}
            
            Technical Specifications:
            {tech_spec}
            
            Requirements:
            1. Map complete user journey from landing to power user
            2. Identify and eliminate every friction point
            3. Design conversion-optimized interface patterns
            4. Create mobile-first responsive design
            5. Implement accessibility best practices (WCAG 2.1 AA+)
            6. Design micro-interactions for user delight
            7. Create consistent design system
            8. Optimize for conversion metrics
            
            Deliverables:
            - User flow diagrams with step-by-step journey
            - Wireframes for key screens
            - Design system specifications
            - Conversion optimization recommendations
            - Mobile responsiveness plan
            - Accessibility compliance checklist
            """,
            agent=self.agent,
            expected_output="Comprehensive UX design package with user flows, wireframes, and conversion optimization strategy"
        )
    
    def create_ui_components_task(self, userflow_design: dict[str, Any], 
                               tech_stack: dict[str, Any]) -> Task:
        """Create task for implementing UI components."""
        return Task(
            description=f"""
            Create production-ready UI components based on the user flow design.
            
            User Flow Design:
            {userflow_design}
            
            Technology Stack:
            {tech_stack}
            
            Requirements:
            1. Implement shadcn/ui components with TypeScript
            2. Create reusable component library
            3. Ensure consistent design tokens (spacing, colors, typography)
            4. Add micro-interactions with Framer Motion
            5. Implement loading states and error boundaries
            6. Optimize for performance (lazy loading, bundle splitting)
            7. Ensure mobile responsiveness
            8. Add accessibility features (ARIA labels, keyboard navigation)
            
            Components to create:
            - Navigation and layout components
            - Form components with validation
            - Data display components (tables, cards, charts)
            - Interactive components (buttons, modals, dropdowns)
            - Loading and skeleton components
            - Error and success state components
            
            Technical Requirements:
            - Next.js App Router with TypeScript
            - Tailwind CSS for styling
            - Proper TypeScript typing throughout
            - Component documentation with Storybook stories
            - Unit tests for critical components
            """,
            agent=self.agent,
            expected_output="Complete UI component library with TypeScript, styling, and documentation"
        )
    
    def create_conversion_optimization_task(self, ui_components: dict[str, Any], 
                                      business_goals: dict[str, Any]) -> Task:
        """Create task for conversion optimization."""
        return Task(
            description=f"""
            Optimize the UI for maximum conversion based on business goals.
            
            UI Components:
            {ui_components}
            
            Business Goals:
            {business_goals}
            
            Conversion Optimization Requirements:
            1. Implement psychology-driven design patterns
            2. Add social proof throughout the user journey
            3. Create urgency and scarcity elements
            4. Optimize call-to-action placement and messaging
            5. Implement trust signals and credibility builders
            6. Reduce friction in signup/onboarding flows
            7. Add progressive profiling to reduce form abandonment
            8. Implement A/B testing framework
            
            Specific Optimizations:
            - Hero section with clear value proposition
            - Social proof integration (testimonials, user counts)
            - Pricing page optimization with highlighted plans
            - Signup flow with minimal friction
            - Onboarding that delivers immediate value
            - Exit-intent popups and email capture
            - Referral and sharing mechanisms
            
            Analytics Implementation:
            - Conversion funnel tracking
            - User behavior analytics
            - A/B test setup
            - Heat mapping integration
            - Session recording setup
            
            Expected Output:
            Conversion-optimized UI with analytics tracking and A/B testing capability
            """,
            agent=self.agent,
            expected_output="Conversion-optimized UI with analytics implementation and testing framework"
        )
    
    def create_mobile_optimization_task(self, desktop_ui: dict[str, Any]) -> Task:
        """Create task for mobile optimization."""
        return Task(
            description=f"""
            Optimize the UI for exceptional mobile experience.
            
            Desktop UI:
            {desktop_ui}
            
            Mobile Optimization Requirements:
            1. Implement thumb-friendly navigation (44px minimum targets)
            2. Design for various screen sizes and orientations
            3. Optimize touch interactions and gestures
            4. Implement mobile-specific patterns (bottom sheets, swipe actions)
            5. Ensure fast loading on mobile networks
            6. Optimize images and assets for mobile
            7. Implement mobile-first responsive design
            8. Add mobile-specific features (push notifications, offline mode)
            
            Mobile UX Patterns:
            - Bottom navigation for easy thumb access
            - Swipe gestures for common actions
            - Pull-to-refresh for content updates
            - Infinite scroll for content feeds
            - Floating action buttons for primary actions
            - Mobile-optimized forms with appropriate keyboards
            - Touch-friendly dropdowns and selects
            
            Performance Optimization:
            - Lazy loading for images and content
            - Service worker for offline capability
            - Optimized images (WebP format, responsive sizing)
            - Minimal JavaScript for fast loading
            - Efficient CSS with critical path optimization
            
            Testing Requirements:
            - Test on various devices and screen sizes
            - Ensure accessibility with screen readers
            - Validate touch interactions
            - Test offline functionality
            """,
            agent=self.agent,
            expected_output="Mobile-optimized UI with exceptional touch experience and performance"
        )
    
    def create_accessibility_task(self, ui_design: dict[str, Any]) -> Task:
        """Create task for accessibility compliance."""
        return Task(
            description=f"""
            Ensure the UI meets WCAG 2.1 AA+ accessibility standards.
            
            UI Design:
            {ui_design}
            
            Accessibility Requirements:
            1. Implement proper semantic HTML structure
            2. Add comprehensive ARIA labels and roles
            3. Ensure keyboard navigation for all interactive elements
            4. Provide sufficient color contrast (4.5:1 minimum)
            5. Add screen reader compatibility
            6. Implement focus management and skip links
            7. Provide alternative text for images
            8. Ensure resizable text without loss of functionality
            
            Specific Implementation:
            - Semantic HTML5 elements (header, nav, main, section, etc.)
            - ARIA landmarks for screen reader navigation
            - Focus indicators for keyboard navigation
            - High contrast mode support
            - Reduced motion preferences
            - Screen reader announcements for dynamic content
            - Voice control compatibility
            
            Testing Requirements:
            - Screen reader testing (NVDA, JAWS, VoiceOver)
            - Keyboard-only navigation testing
            - Color contrast validation
            - Voice control testing
            - Mobile accessibility testing
            
            Documentation:
            - Accessibility statement
            - Keyboard shortcuts guide
            - Screen reader instructions
            """,
            agent=self.agent,
            expected_output="Fully accessible UI compliant with WCAG 2.1 AA+ standards"
        )
    
    def get_ux_tools(self) -> list[Tool]:
        """Get UX-specific tools for the agent."""
        return [
            Tool(
                name="analyze_user_flow",
                description="Analyze and optimize user flows for conversion and usability",
                func=lambda: "User flow analysis tool for identifying friction points and optimization opportunities"
            ),
            Tool(
                name="design_system_validator",
                description="Validate design system consistency and best practices",
                func=lambda: "Design system validation tool for checking spacing, colors, typography consistency"
            ),
            Tool(
                name="accessibility_checker",
                description="Check accessibility compliance with WCAG standards",
                func=lambda: "Accessibility checker for WCAG 2.1 AA+ compliance validation"
            ),
            Tool(
                name="conversion_optimizer",
                description="Optimize UI elements for maximum conversion rates",
                func=lambda: "Conversion optimization tool for psychology-driven design improvements"
            ),
            Tool(
                name="mobile_responsiveness_tester",
                description="Test and validate mobile responsiveness across devices",
                func=lambda: "Mobile responsiveness testing tool for various screen sizes and devices"
            )
        ]
