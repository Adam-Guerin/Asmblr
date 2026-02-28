"""
Intelligent AI Assistant for Asmblr
Advanced conversational AI with context awareness and business intelligence
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import re
from enum import Enum
import openai
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.utilities import SearchAPIWrapper
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """User intent types"""
    CREATE_MVP = "create_mvp"
    ANALYZE_MARKET = "analyze_market"
    OPTIMIZE_BUSINESS = "optimize_business"
    GET_INSIGHTS = "get_insights"
    COLLABORATE = "collaborate"
    LEARN = "learn"
    HELP = "help"

@dataclass
class ConversationContext:
    """Conversation context and state"""
    user_id: str
    session_id: str
    intent: Optional[IntentType]
    project_context: Optional[Dict[str, Any]]
    previous_interactions: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    business_domain: Optional[str]
    expertise_level: str  # beginner, intermediate, advanced
    current_mvp_state: Optional[Dict[str, Any]]
    collaboration_mode: bool = False

@dataclass
class AIResponse:
    """AI assistant response"""
    content: str
    intent: IntentType
    confidence: float
    suggested_actions: List[str]
    follow_up_questions: List[str]
    resources: List[Dict[str, str]]
    execution_plan: Optional[Dict[str, Any]] = None
    collaboration_invites: List[str] = None

class IntentClassifier:
    """Classify user intents using ML"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.intent_patterns = {
            IntentType.CREATE_MVP: [
                "create mvp", "build product", "develop app", "start business",
                "launch startup", "make prototype", "build minimum viable product"
            ],
            IntentType.ANALYZE_MARKET: [
                "analyze market", "market research", "competitor analysis",
                "market size", "target audience", "customer segments"
            ],
            IntentType.OPTIMIZE_BUSINESS: [
                "optimize business", "improve processes", "efficiency",
                "reduce costs", "increase revenue", "business strategy"
            ],
            IntentType.GET_INSIGHTS: [
                "get insights", "analytics", "metrics", "performance",
                "data analysis", "business intelligence"
            ],
            IntentType.COLLABORATE: [
                "collaborate", "team up", "work together", "partner",
                "share project", "invite team", "collaboration"
            ],
            IntentType.LEARN: [
                "learn", "tutorial", "how to", "guide", "explain",
                "teach me", "show me", "help me understand"
            ],
            IntentType.HELP: [
                "help", "assist", "support", "guidance", "what can you do"
            ]
        }
        
        # Train the classifier
        self._train_classifier()
    
    def _train_classifier(self):
        """Train the intent classifier"""
        texts = []
        labels = []
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                texts.append(pattern)
                labels.append(intent.value)
        
        if texts:
            self.vectorizer.fit(texts)
            self.intent_vectors = self.vectorizer.transform(texts)
            self.intent_labels = labels
    
    def classify_intent(self, text: str) -> Tuple[IntentType, float]:
        """Classify user intent"""
        if not hasattr(self, 'intent_vectors'):
            return IntentType.HELP, 0.5
        
        text_vector = self.vectorizer.transform([text])
        similarities = cosine_similarity(text_vector, self.intent_vectors)
        
        if similarities.size > 0:
            max_sim_idx = np.argmax(similarities)
            max_similarity = similarities[0, max_sim_idx]
            
            if max_similarity > 0.3:  # Threshold
                intent_value = self.intent_labels[max_sim_idx]
                intent = IntentType(intent_value)
                return intent, float(max_similarity)
        
        return IntentType.HELP, 0.5

class BusinessKnowledgeBase:
    """Business knowledge and insights"""
    
    def __init__(self):
        self.business_models = {
            "saas": {
                "description": "Software as a Service subscription model",
                "key_metrics": ["MRR", "ARR", "Churn Rate", "LTV", "CAC"],
                "typical_mvp_features": ["User authentication", "Dashboard", "Billing", "API"],
                "success_factors": ["Product-market fit", "Scalability", "Customer support"]
            },
            "marketplace": {
                "description": "Platform connecting buyers and sellers",
                "key_metrics": ["GMV", "Take rate", "Active users", "Transaction volume"],
                "typical_mvp_features": ["User profiles", "Search", "Reviews", "Payments"],
                "success_factors": ["Network effects", "Trust", "Liquidity"]
            },
            "ecommerce": {
                "description": "Online retail business",
                "key_metrics": ["Conversion rate", "AOV", "Cart abandonment", "Customer lifetime value"],
                "typical_mvp_features": ["Product catalog", "Shopping cart", "Checkout", "Inventory"],
                "success_factors": ["Product selection", "User experience", "Logistics"]
            },
            "fintech": {
                "description": "Financial technology services",
                "key_metrics": ["Transaction volume", "Active users", "Revenue per user", "Compliance"],
                "typical_mvp_features": ["Account management", "Transactions", "Security", "Compliance"],
                "success_factors": ["Regulatory compliance", "Security", "User trust"]
            }
        }
        
        self.market_insights = {
            "ai_tools": {
                "trend": "Growing rapidly with 40% YoY growth",
                "key_players": ["OpenAI", "Anthropic", "Hugging Face"],
                "opportunities": ["Vertical AI", "Edge AI", "AI automation"],
                "challenges": ["Competition", "API costs", "Regulation"]
            },
            "sustainability": {
                "trend": "Increasing consumer and regulatory focus",
                "key_players": ["Patagonia", "Tesla", "Beyond Meat"],
                "opportunities": ["Green tech", "Circular economy", "ESG reporting"],
                "challenges": ["Greenwashing", "Complex supply chains"]
            },
            "remote_work": {
                "trend": "Hybrid models becoming standard",
                "key_players": ["Zoom", "Slack", "Notion"],
                "opportunities": ["Collaboration tools", "Remote onboarding", "Digital nomad services"],
                "challenges": ["Team cohesion", "Security", "Time zone management"]
            }
        }
    
    def get_business_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get business model information"""
        return self.business_models.get(model_type.lower(), {})
    
    def get_market_insights(self, sector: str) -> Dict[str, Any]:
        """Get market insights for sector"""
        return self.market_insights.get(sector.lower(), {})
    
    def suggest_mvp_features(self, business_type: str, target_market: str) -> List[str]:
        """Suggest MVP features based on business type and market"""
        base_features = ["User authentication", "Dashboard", "Analytics"]
        
        model_info = self.get_business_model_info(business_type)
        if model_info and "typical_mvp_features" in model_info:
            base_features.extend(model_info["typical_mvp_features"])
        
        # Add market-specific features
        if "mobile" in target_market.lower():
            base_features.extend(["Mobile app", "Push notifications"])
        
        if "enterprise" in target_market.lower():
            base_features.extend(["SSO", "Admin panel", "Audit logs"])
        
        return list(set(base_features))  # Remove duplicates

class IntelligentAssistant:
    """Main intelligent assistant"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key
        self.intent_classifier = IntentClassifier()
        self.knowledge_base = BusinessKnowledgeBase()
        self.conversation_history: Dict[str, ConversationContext] = {}
        self.active_collaborations: Dict[str, List[str]] = {}
        
        # Initialize LangChain components
        self._initialize_langchain()
        
        # Define tools for the agent
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _initialize_langchain(self):
        """Initialize LangChain components"""
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.llm = OpenAI(temperature=0.7, openai_api_key=self.openai_api_key)
        else:
            # Use local Ollama
            from langchain.llms import Ollama
            self.llm = Ollama(model="llama3.1", base_url="http://localhost:11434")
        
        # Create conversation memory
        self.memory = ConversationBufferMemory()
        
        # Create prompt template
        self.template = """You are Asmblr AI, an intelligent assistant for building MVPs and startups. 
        You are helpful, creative, and business-savvy. You help users:
        - Create and optimize MVPs
        - Analyze markets and competition
        - Provide business insights
        - Suggest strategies and tactics
        - Enable collaboration
        
        Current conversation:
        {history}
        
        Human: {input}
        AI Assistant:"""
        
        self.prompt = PromptTemplate(
            input_variables=["history", "input"],
            template=self.template
        )
        
        self.conversation_chain = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=self.prompt
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        tools = [
            Tool(
                name="MarketAnalyzer",
                description="Analyze market trends and competition for a given business idea",
                func=self._analyze_market
            ),
            Tool(
                name="MVPGenerator",
                description="Generate MVP features and roadmap for a business idea",
                func=self._generate_mvp_plan
            ),
            Tool(
                name="BusinessOptimizer",
                description="Optimize business processes and suggest improvements",
                func=self._optimize_business
            ),
            Tool(
                name="InsightGenerator",
                description="Generate business insights and recommendations",
                func=self._generate_insights
            ),
            Tool(
                name="CollaborationManager",
                description="Manage team collaboration and project sharing",
                func=self._manage_collaboration
            ),
            Tool(
                name="KnowledgeBase",
                description="Access business knowledge and best practices",
                func=self._access_knowledge_base
            )
        ]
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Create the agent with tools"""
        agent_prompt = """
        You are Asmblr AI, an intelligent assistant for building MVPs and startups.
        You have access to the following tools:
        {tools}
        
        Use the following format:
        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question
        
        Question: {input}
        Thought: {agent_scratchpad}
        """
        
        agent = create_react_agent(self.llm, self.tools, agent_prompt)
        return AgentExecutor.from_agent_and_tools(agent, self.tools, verbose=True)
    
    async def process_message(self, user_id: str, message: str, session_id: str = None) -> AIResponse:
        """Process user message and generate response"""
        try:
            # Get or create conversation context
            context = self._get_or_create_context(user_id, session_id)
            
            # Classify intent
            intent, confidence = self.intent_classifier.classify_intent(message)
            context.intent = intent
            
            # Update conversation history
            context.previous_interactions.append({
                "timestamp": datetime.now(),
                "message": message,
                "intent": intent.value
            })
            
            # Generate response based on intent
            if intent == IntentType.CREATE_MVP:
                response = await self._handle_create_mvp(message, context)
            elif intent == IntentType.ANALYZE_MARKET:
                response = await self._handle_analyze_market(message, context)
            elif intent == IntentType.OPTIMIZE_BUSINESS:
                response = await self._handle_optimize_business(message, context)
            elif intent == IntentType.GET_INSIGHTS:
                response = await self._handle_get_insights(message, context)
            elif intent == IntentType.COLLABORATE:
                response = await self._handle_collaborate(message, context)
            elif intent == IntentType.LEARN:
                response = await self._handle_learn(message, context)
            else:
                response = await self._handle_help(message, context)
            
            # Update context
            self.conversation_history[context.session_id] = context
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return AIResponse(
                content="I apologize, but I encountered an error processing your request. Please try again.",
                intent=IntentType.HELP,
                confidence=0.1,
                suggested_actions=["Try rephrasing your question", "Contact support"],
                follow_up_questions=["How can I help you today?"],
                resources=[]
            )
    
    def _get_or_create_context(self, user_id: str, session_id: str = None) -> ConversationContext:
        """Get or create conversation context"""
        if not session_id:
            session_id = f"{user_id}_{int(time.time())}"
        
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = ConversationContext(
                user_id=user_id,
                session_id=session_id,
                intent=None,
                project_context=None,
                previous_interactions=[],
                user_preferences={},
                business_domain=None,
                expertise_level="intermediate",
                current_mvp_state=None,
                collaboration_mode=False
            )
        
        return self.conversation_history[session_id]
    
    async def _handle_create_mvp(self, message: str, context: ConversationContext) -> AIResponse:
        """Handle MVP creation requests"""
        # Extract business idea from message
        business_idea = self._extract_business_idea(message)
        
        # Generate MVP plan using agent
        agent_response = self.agent.run(f"Generate an MVP plan for: {business_idea}")
        
        # Extract key information
        suggested_features = self.knowledge_base.suggest_mvp_features(
            business_idea.get("type", "saas"),
            business_idea.get("market", "general")
        )
        
        # Create execution plan
        execution_plan = {
            "phases": [
                {
                    "name": "Research & Validation",
                    "duration": "2 weeks",
                    "tasks": ["Market research", "User interviews", "Competitor analysis"]
                },
                {
                    "name": "MVP Development",
                    "duration": "4-6 weeks",
                    "tasks": suggested_features[:5]  # Top 5 features
                },
                {
                    "name": "Launch & Iteration",
                    "duration": "2 weeks",
                    "tasks": ["Beta testing", "Feedback collection", "Iteration"]
                }
            ],
            "resources_needed": ["Development team", "Design resources", "Cloud infrastructure"],
            "estimated_cost": "$10,000 - $50,000",
            "success_metrics": ["User acquisition", "Engagement rate", "Revenue generation"]
        }
        
        return AIResponse(
            content=agent_response,
            intent=IntentType.CREATE_MVP,
            confidence=0.8,
            suggested_actions=[
                "Start market research",
                "Create user personas",
                "Define MVP scope",
                "Build prototype"
            ],
            follow_up_questions=[
                "What's your target market?",
                "Who are your main competitors?",
                "What's your budget constraint?",
                "What's your timeline?"
            ],
            resources=[
                {"title": "MVP Development Guide", "url": "/docs/mvp-guide"},
                {"title": "Market Research Template", "url": "/templates/market-research"},
                {"title": "Business Model Canvas", "url": "/tools/business-canvas"}
            ],
            execution_plan=execution_plan
        )
    
    async def _handle_analyze_market(self, message: str, context: ConversationContext) -> AIResponse:
        """Handle market analysis requests"""
        # Extract market/sector from message
        sector = self._extract_sector(message)
        
        # Get market insights
        market_insights = self.knowledge_base.get_market_insights(sector)
        
        # Generate analysis using agent
        agent_response = self.agent.run(f"Analyze the market for {sector} business")
        
        return AIResponse(
            content=agent_response,
            intent=IntentType.ANALYZE_MARKET,
            confidence=0.85,
            suggested_actions=[
                "Conduct competitor analysis",
                "Survey target customers",
                "Analyze market size",
                "Identify opportunities"
            ],
            follow_up_questions=[
                "Who are your target customers?",
                "What's your unique value proposition?",
                "How big is the addressable market?",
                "What are the barriers to entry?"
            ],
            resources=[
                {"title": "Market Analysis Framework", "url": "/docs/market-analysis"},
                {"title": "Competitor Analysis Tool", "url": "/tools/competitor-analysis"},
                {"title": "Market Size Calculator", "url": "/tools/market-size"}
            ]
        )
    
    async def _handle_optimize_business(self, message: str, context: ConversationContext) -> AIResponse:
        """Handle business optimization requests"""
        # Generate optimization recommendations
        agent_response = self.agent.run(f"Provide business optimization recommendations for: {message}")
        
        return AIResponse(
            content=agent_response,
            intent=IntentType.OPTIMIZE_BUSINESS,
            confidence=0.8,
            suggested_actions=[
                "Analyze current processes",
                "Identify bottlenecks",
                "Implement automation",
                "Measure improvements"
            ],
            follow_up_questions=[
                "What are your current pain points?",
                "What metrics are you tracking?",
                "What's your current team size?",
                "What's your budget for improvements?"
            ],
            resources=[
                {"title": "Business Process Optimization", "url": "/docs/process-optimization"},
                {"title": "Automation Tools Guide", "url": "/docs/automation"},
                {"title": "KPI Dashboard", "url": "/tools/kpi-dashboard"}
            ]
        )
    
    async def _handle_get_insights(self, message: str, context: ConversationContext) -> AIResponse:
        """Handle insights requests"""
        # Generate business insights
        agent_response = self.agent.run(f"Generate business insights for: {message}")
        
        return AIResponse(
            content=agent_response,
            intent=IntentType.GET_INSIGHTS,
            confidence=0.75,
            suggested_actions=[
                "Review analytics data",
                "Identify trends",
                "Create reports",
                "Share insights with team"
            ],
            follow_up_questions=[
                "What metrics are most important?",
                "What time period should we analyze?",
                "Who are the stakeholders?",
                "What decisions need to be made?"
            ],
            resources=[
                {"title": "Analytics Dashboard", "url": "/analytics"},
                {"title": "Business Intelligence Guide", "url": "/docs/bi-guide"},
                {"title": "Data Visualization Tools", "url": "/tools/data-viz"}
            ]
        )
    
    async def _handle_collaborate(self, message: str, context: ConversationContext) -> AIResponse:
        """Handle collaboration requests"""
        # Extract collaboration details
        collab_details = self._extract_collaboration_details(message)
        
        # Generate collaboration plan
        agent_response = self.agent.run(f"Create a collaboration plan for: {message}")
        
        # Set up collaboration
        if collab_details.get("invite_users"):
            context.collaboration_mode = True
            if context.session_id not in self.active_collaborations:
                self.active_collaborations[context.session_id] = []
            self.active_collaborations[context.session_id].extend(collab_details["invite_users"])
        
        return AIResponse(
            content=agent_response,
            intent=IntentType.COLLABORATE,
            confidence=0.9,
            suggested_actions=[
                "Invite team members",
                "Set up project workspace",
                "Define roles and responsibilities",
                "Establish communication channels"
            ],
            follow_up_questions=[
                "Who should be on the team?",
                "What are the project goals?",
                "What's the timeline?",
                "How will you communicate?"
            ],
            resources=[
                {"title": "Collaboration Guide", "url": "/docs/collaboration"},
                {"title": "Team Management Tools", "url": "/tools/team-management"},
                {"title": "Project Workspace", "url": "/workspace"}
            ],
            collaboration_invites=collab_details.get("invite_users", [])
        )
    
    async def _handle_learn(self, message: str, context: ConversationContext) -> AIResponse:
        """Handle learning requests"""
        # Generate educational content
        agent_response = self.agent.run(f"Provide educational content about: {message}")
        
        return AIResponse(
            content=agent_response,
            intent=IntentType.LEARN,
            confidence=0.85,
            suggested_actions=[
                "Explore tutorials",
                "Read documentation",
                "Join community",
                "Practice with examples"
            ],
            follow_up_questions=[
                "What's your current skill level?",
                "What do you want to learn first?",
                "How do you prefer to learn?",
                "What's your timeline?"
            ],
            resources=[
                {"title": "Learning Path", "url": "/learn"},
                {"title": "Tutorials", "url": "/tutorials"},
                {"title": "Community Forum", "url": "/community"}
            ]
        )
    
    async def _handle_help(self, message: str, context: ConversationContext) -> AIResponse:
        """Handle help requests"""
        help_content = """
        I'm Asmblr AI, your intelligent assistant for building MVPs and startups! I can help you with:
        
        🚀 **MVP Creation**
        - Generate MVP features and roadmaps
        - Create development plans
        - Suggest technologies and architectures
        
        📊 **Market Analysis**
        - Analyze market trends and competition
        - Identify opportunities and threats
        - Provide market sizing and segmentation
        
        💡 **Business Optimization**
        - Improve processes and efficiency
        - Suggest growth strategies
        - Optimize costs and revenue
        
        📈 **Business Insights**
        - Generate analytics and reports
        - Provide data-driven recommendations
        - Create dashboards and visualizations
        
        👥 **Collaboration**
        - Set up team workspaces
        - Manage project collaboration
        - Coordinate team activities
        
        📚 **Learning**
        - Provide tutorials and guides
        - Explain concepts and best practices
        - Share industry insights
        
        Just tell me what you'd like to work on, and I'll guide you through the process!
        """
        
        return AIResponse(
            content=help_content,
            intent=IntentType.HELP,
            confidence=0.95,
            suggested_actions=[
                "Start creating an MVP",
                "Analyze your market",
                "Optimize your business",
                "Learn something new"
            ],
            follow_up_questions=[
                "What would you like to build?",
                "What's your business idea?",
                "What challenges are you facing?",
                "How can I help you today?"
            ],
            resources=[
                {"title": "Getting Started Guide", "url": "/docs/getting-started"},
                {"title": "Feature Overview", "url": "/features"},
                {"title": "API Documentation", "url": "/docs/api"}
            ]
        )
    
    def _extract_business_idea(self, message: str) -> Dict[str, str]:
        """Extract business idea from message"""
        # Simple extraction - in production, use NLP
        idea = {"type": "saas", "market": "general", "description": message}
        
        # Try to identify business type
        if any(word in message.lower() for word in ["app", "software", "platform"]):
            idea["type"] = "saas"
        elif any(word in message.lower() for word in ["marketplace", "platform", "connect"]):
            idea["type"] = "marketplace"
        elif any(word in message.lower() for word in ["store", "shop", "retail"]):
            idea["type"] = "ecommerce"
        elif any(word in message.lower() for word in ["finance", "fintech", "payments"]):
            idea["type"] = "fintech"
        
        return idea
    
    def _extract_sector(self, message: str) -> str:
        """Extract sector from message"""
        sectors = ["ai_tools", "sustainability", "remote_work", "healthcare", "education", "fintech"]
        
        for sector in sectors:
            if sector.replace("_", " ") in message.lower():
                return sector
        
        return "general"
    
    def _extract_collaboration_details(self, message: str) -> Dict[str, Any]:
        """Extract collaboration details from message"""
        # Simple extraction - in production, use NLP
        details = {"invite_users": []}
        
        # Look for email addresses or user mentions
        import re
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
        details["invite_users"] = emails
        
        return details
    
    # Tool implementations
    def _analyze_market(self, query: str) -> str:
        """Market analysis tool"""
        sector = self._extract_sector(query)
        insights = self.knowledge_base.get_market_insights(sector)
        
        if insights:
            return f"Market analysis for {sector}: {json.dumps(insights, indent=2)}"
        return f"No specific insights available for {sector}. Please provide more details."
    
    def _generate_mvp_plan(self, query: str) -> str:
        """MVP generation tool"""
        business_idea = self._extract_business_idea(query)
        features = self.knowledge_base.suggest_mvp_features(
            business_idea.get("type", "saas"),
            business_idea.get("market", "general")
        )
        
        return f"Suggested MVP features: {', '.join(features[:10])}"
    
    def _optimize_business(self, query: str) -> str:
        """Business optimization tool"""
        return "Business optimization recommendations: 1) Automate repetitive tasks, 2) Improve customer experience, 3) Optimize pricing strategy, 4) Expand to new markets"
    
    def _generate_insights(self, query: str) -> str:
        """Insights generation tool"""
        return "Key insights: Focus on user retention, monitor churn rate, optimize conversion funnel, track customer lifetime value"
    
    def _manage_collaboration(self, query: str) -> str:
        """Collaboration management tool"""
        return "Collaboration setup: Create shared workspace, define roles, establish communication channels, set up project timeline"
    
    def _access_knowledge_base(self, query: str) -> str:
        """Knowledge base access tool"""
        return "Knowledge base: Contains business models, market insights, best practices, and industry trends"

# Global assistant instance
intelligent_assistant = IntelligentAssistant()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/assistant", tags=["intelligent-assistant"])

class MessageRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None

class MessageResponse(BaseModel):
    content: str
    intent: str
    confidence: float
    suggested_actions: List[str]
    follow_up_questions: List[str]
    resources: List[Dict[str, str]]
    execution_plan: Optional[Dict[str, Any]] = None
    collaboration_invites: List[str] = None

@router.post("/chat", response_model=MessageResponse)
async def chat_with_assistant(request: MessageRequest):
    """Chat with intelligent assistant"""
    try:
        response = await intelligent_assistant.process_message(
            request.user_id,
            request.message,
            request.session_id
        )
        
        return MessageResponse(
            content=response.content,
            intent=response.intent.value,
            confidence=response.confidence,
            suggested_actions=response.suggested_actions,
            follow_up_questions=response.follow_up_questions,
            resources=response.resources,
            execution_plan=response.execution_plan,
            collaboration_invites=response.collaboration_invites or []
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context/{user_id}")
async def get_user_context(user_id: str):
    """Get user conversation context"""
    try:
        user_contexts = {
            session_id: context for session_id, context in intelligent_assistant.conversation_history.items()
            if context.user_id == user_id
        }
        
        return {
            "active_sessions": len(user_contexts),
            "contexts": {
                session_id: {
                    "session_id": context.session_id,
                    "intent": context.intent.value if context.intent else None,
                    "business_domain": context.business_domain,
                    "expertise_level": context.expertise_level,
                    "collaboration_mode": context.collaboration_mode,
                    "interaction_count": len(context.previous_interactions)
                }
                for session_id, context in user_contexts.items()
            }
        }
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaborate/{session_id}")
async def invite_to_collaborate(session_id: str, user_emails: List[str]):
    """Invite users to collaborate"""
    try:
        if session_id not in intelligent_assistant.conversation_history:
            raise HTTPException(status_code=404, detail="Session not found")
        
        context = intelligent_assistant.conversation_history[session_id]
        context.collaboration_mode = True
        
        if session_id not in intelligent_assistant.active_collaborations:
            intelligent_assistant.active_collaborations[session_id] = []
        
        intelligent_assistant.active_collaborations[session_id].extend(user_emails)
        
        return {
            "session_id": session_id,
            "invited_users": user_emails,
            "collaboration_active": True
        }
    except Exception as e:
        logger.error(f"Error inviting to collaborate: {e}")
        raise HTTPException(status_code=500, detail=str(e))
