"""
Advanced Voice Interface and NLP for Asmblr
Voice commands, speech recognition, and natural language understanding
"""

import time
import asyncio
import logging
from datetime import datetime
from typing import Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import speech_recognition as sr
import pyttsx3
from io import BytesIO

logger = logging.getLogger(__name__)

class VoiceCommandType(Enum):
    """Voice command types"""
    CREATE_MVP = "create_mvp"
    EDIT_PROJECT = "edit_project"
    ANALYZE_METRICS = "analyze_metrics"
    COLLABORATE = "collaborate"
    SEARCH = "search"
    NAVIGATE = "navigate"
    HELP = "help"
    SETTINGS = "settings"
    EXIT = "exit"

class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"

class SpeechEngine(Enum):
    """Speech recognition engines"""
    GOOGLE = "google"
    SPHINX = "sphinx"
    WHISPER = "whisper"
    AZURE = "azure"
    AWS = "aws"

@dataclass
class VoiceCommand:
    """Voice command structure"""
    id: str
    command_type: VoiceCommandType
    transcript: str
    confidence: float
    intent: str
    entities: dict[str, Any]
    action: str
    parameters: dict[str, Any]
    timestamp: datetime
    language: Language
    processing_time: float

@dataclass
class NLPIntent:
    """NLP intent classification"""
    intent: str
    confidence: float
    entities: dict[str, Any]
    action_mapping: str
    required_parameters: list[str]
    optional_parameters: list[str]

@dataclass
class VoiceProfile:
    """User voice profile"""
    user_id: str
    name: str
    language: Language
    voice_speed: float
    voice_pitch: float
    preferred_engine: SpeechEngine
    custom_commands: dict[str, str]
    accuracy_score: float
    created_at: datetime
    last_used: datetime

class SpeechRecognizer:
    """Advanced speech recognition"""
    
    def __init__(self, engine: SpeechEngine = SpeechEngine.GOOGLE):
        self.engine = engine
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_listening = False
        
        # Initialize speech recognition
        self._initialize_recognizer()
        
        # Initialize text-to-speech
        self._initialize_tts()
    
    def _initialize_recognognizer(self):
        """Initialize speech recognition engine"""
        try:
            if self.engine == SpeechEngine.GOOGLE:
                # Google Web Speech API (default)
                pass
            elif self.engine == SpeechEngine.SPHINX:
                # CMU Sphinx (offline)
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
            elif self.engine == SpeechEngine.WHISPER:
                # OpenAI Whisper (if available)
                try:
                    import whisper
                    self.whisper_model = whisper.load_model("base")
                except ImportError:
                    logger.warning("Whisper not available, falling back to Google")
                    self.engine = SpeechEngine.GOOGLE
            
            logger.info(f"Initialized speech recognition with {self.engine.value}")
            
        except Exception as e:
            logger.error(f"Error initializing speech recognizer: {e}")
            self.engine = SpeechEngine.GOOGLE
    
    def _initialize_tts(self):
        """Initialize text-to-speech"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            
            # Set default voice
            if voices:
                self.tts_engine.setProperty('voice', voices[0].id)
            
            # Set default properties
            self.tts_engine.setProperty('rate', 200)  # Words per minute
            self.tts_engine.setProperty('volume', 0.9)
            
            logger.info("Initialized text-to-speech engine")
            
        except Exception as e:
            logger.error(f"Error initializing TTS: {e}")
            self.tts_engine = None
    
    async def start_listening(self) -> bool:
        """Start listening for voice commands"""
        try:
            if self.is_listening:
                return False
            
            self.microphone = sr.Microphone()
            self.is_listening = True
            
            logger.info("Started listening for voice commands")
            return True
            
        except Exception as e:
            logger.error(f"Error starting listening: {e}")
            return False
    
    async def stop_listening(self):
        """Stop listening for voice commands"""
        try:
            if self.microphone:
                self.microphone = None
            self.is_listening = False
            
            logger.info("Stopped listening for voice commands")
            
        except Exception as e:
            logger.error(f"Error stopping listening: {e}")
    
    async def recognize_speech(self, audio_data: bytes = None, language: str = "en-US") -> dict[str, Any]:
        """Recognize speech from audio data"""
        try:
            if audio_data:
                # Use provided audio data
                audio_file = BytesIO(audio_data)
                with sr.AudioFile(audio_file) as source:
                    audio = self.recognizer.record(source)
            else:
                # Use microphone
                if not self.microphone:
                    self.microphone = sr.Microphone()
                
                with self.microphone as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Listen for audio
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Recognize speech
            start_time = time.time()
            
            if self.engine == SpeechEngine.GOOGLE:
                try:
                    text = self.recognizer.recognize_google(audio, language=language)
                    confidence = 0.9  # Google doesn't provide confidence
                except sr.UnknownValueError:
                    return {"success": False, "error": "Could not understand audio"}
                except sr.RequestError as e:
                    return {"success": False, "error": f"Google API error: {e}"}
            
            elif self.engine == SpeechEngine.SPHINX:
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    confidence = 0.7  # Estimated for Sphinx
                except sr.UnknownValueError:
                    return {"success": False, "error": "Could not understand audio"}
            
            elif self.engine == SpeechEngine.WHISPER and hasattr(self, 'whisper_model'):
                try:
                    # Convert audio to format expected by Whisper
                    audio_data = audio.get_wav_data()
                    result = self.whisper_model.transcribe(audio_data)
                    text = result['text'].strip()
                    confidence = 0.95  # High confidence for Whisper
                except Exception as e:
                    return {"success": False, "error": f"Whisper error: {e}"}
            
            else:
                # Fallback to Google
                try:
                    text = self.recognizer.recognize_google(audio, language=language)
                    confidence = 0.9
                except sr.UnknownValueError:
                    return {"success": False, "error": "Could not understand audio"}
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "text": text,
                "confidence": confidence,
                "processing_time": processing_time,
                "engine": self.engine.value
            }
            
        except Exception as e:
            logger.error(f"Error recognizing speech: {e}")
            return {"success": False, "error": str(e)}
    
    async def speak_text(self, text: str, speed: float = None, pitch: float = None) -> bool:
        """Convert text to speech"""
        try:
            if not self.tts_engine:
                logger.warning("TTS engine not available")
                return False
            
            # Adjust voice properties if provided
            if speed:
                self.tts_engine.setProperty('rate', speed * 200)
            if pitch:
                # Pitch adjustment (simplified)
                voices = self.tts_engine.getProperty('voices')
                if voices and len(voices) > 1:
                    self.tts_engine.setProperty('voice', voices[1].id)
            
            # Speak text
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            
            logger.info(f"Spoke text: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
            return False

class NLPProcessor:
    """Natural Language Processing for voice commands"""
    
    def __init__(self):
        self.intent_classifier = None
        self.entity_extractor = None
        self.command_patterns = self._initialize_command_patterns()
        self.intent_mappings = self._initialize_intent_mappings()
        
        # Train intent classifier
        self._train_intent_classifier()
    
    def _initialize_command_patterns(self) -> dict[str, list[str]]:
        """Initialize voice command patterns"""
        return {
            "create_mvp": [
                "create a new mvp",
                "start a new project",
                "build an mvp",
                "make a minimum viable product",
                "launch a startup",
                "create a new app",
                "build a software product",
                "start a business"
            ],
            "edit_project": [
                "edit my project",
                "modify the project",
                "update the mvp",
                "change the app",
                "edit the code",
                "modify features",
                "update functionality"
            ],
            "analyze_metrics": [
                "show me the metrics",
                "analyze the data",
                "show performance",
                "display analytics",
                "check the kpis",
                "show business metrics",
                "analyze performance"
            ],
            "collaborate": [
                "invite team members",
                "share the project",
                "collaborate with team",
                "add collaborators",
                "share with others",
                "work together",
                "team collaboration"
            ],
            "search": [
                "search for templates",
                "find examples",
                "look for projects",
                "search the marketplace",
                "find resources",
                "search documentation",
                "find help"
            ],
            "navigate": [
                "go to dashboard",
                "open templates",
                "show analytics",
                "go to settings",
                "navigate to",
                "open the",
                "show me the"
            ],
            "help": [
                "help me",
                "what can you do",
                "how do i",
                "show help",
                "i need help",
                "assist me",
                "guide me"
            ],
            "settings": [
                "open settings",
                "change settings",
                "configure",
                "preferences",
                "setup",
                "configure the app"
            ],
            "exit": [
                "exit",
                "quit",
                "close",
                "goodbye",
                "stop listening",
                "end session"
            ]
        }
    
    def _initialize_intent_mappings(self) -> dict[str, str]:
        """Initialize intent to action mappings"""
        return {
            "create_mvp": "create_new_mvp",
            "edit_project": "modify_existing_project",
            "analyze_metrics": "display_analytics_dashboard",
            "collaborate": "manage_collaboration",
            "search": "search_resources",
            "navigate": "navigate_to_page",
            "help": "provide_help",
            "settings": "open_settings",
            "exit": "end_session"
        }
    
    def _train_intent_classifier(self):
        """Train intent classification model"""
        try:
            # Prepare training data
            training_texts = []
            training_labels = []
            
            for intent, patterns in self.command_patterns.items():
                for pattern in patterns:
                    training_texts.append(pattern)
                    training_labels.append(intent)
            
            if len(training_texts) > 0:
                # Create and train classifier
                self.intent_classifier = Pipeline([
                    ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
                    ('classifier', MultinomialNB())
                ])
                
                self.intent_classifier.fit(training_texts, training_labels)
                logger.info("Trained intent classifier")
            
        except Exception as e:
            logger.error(f"Error training intent classifier: {e}")
    
    def classify_intent(self, text: str) -> NLPIntent:
        """Classify intent from text"""
        try:
            if self.intent_classifier:
                # Use trained classifier
                prediction = self.intent_classifier.predict([text])[0]
                probabilities = self.intent_classifier.predict_proba([text])[0]
                confidence = max(probabilities)
                
                # Get probability for predicted intent
                intent_index = list(self.intent_classifier.classes_).index(prediction)
                confidence = probabilities[intent_index]
            else:
                # Fallback to pattern matching
                prediction, confidence = self._pattern_match_intent(text)
            
            # Extract entities
            entities = self._extract_entities(text, prediction)
            
            # Get action mapping
            action_mapping = self.intent_mappings.get(prediction, "")
            
            # Get required parameters
            required_params = self._get_required_parameters(prediction)
            optional_params = self._get_optional_parameters(prediction)
            
            return NLPIntent(
                intent=prediction,
                confidence=confidence,
                entities=entities,
                action_mapping=action_mapping,
                required_parameters=required_params,
                optional_parameters=optional_params
            )
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return NLPIntent(
                intent="unknown",
                confidence=0.0,
                entities={},
                action_mapping="",
                required_parameters=[],
                optional_parameters=[]
            )
    
    def _pattern_match_intent(self, text: str) -> tuple[str, float]:
        """Pattern matching fallback for intent classification"""
        text_lower = text.lower()
        best_match = "unknown"
        best_score = 0.0
        
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                # Calculate similarity score
                pattern_lower = pattern.lower()
                
                # Simple word overlap scoring
                pattern_words = set(pattern_lower.split())
                text_words = set(text_lower.split())
                
                overlap = len(pattern_words.intersection(text_words))
                total_words = len(pattern_words)
                
                if total_words > 0:
                    score = overlap / total_words
                    if score > best_score:
                        best_score = score
                        best_match = intent
        
        return best_match, best_score
    
    def _extract_entities(self, text: str, intent: str) -> dict[str, Any]:
        """Extract entities from text"""
        entities = {}
        
        try:
            # Common entity patterns
            if intent == "create_mvp":
                # Extract project type
                project_types = ["saas", "ecommerce", "marketplace", "fintech", "healthcare"]
                for ptype in project_types:
                    if ptype in text.lower():
                        entities["project_type"] = ptype
                
                # Extract project name (simplified)
                words = text.lower().split()
                for i, word in enumerate(words):
                    if word in ["called", "named", "name"] and i + 1 < len(words):
                        entities["project_name"] = words[i + 1].title()
                        break
            
            elif intent == "collaborate":
                # Extract email addresses
                import re
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                if emails:
                    entities["emails"] = emails
            
            elif intent == "navigate":
                # Extract page names
                pages = ["dashboard", "templates", "analytics", "settings", "projects"]
                for page in pages:
                    if page in text.lower():
                        entities["page"] = page
            
            # Extract numbers
            numbers = re.findall(r'\b\d+\b', text)
            if numbers:
                entities["numbers"] = [int(n) for n in numbers]
            
            # Extract time expressions
            time_expressions = ["today", "yesterday", "tomorrow", "week", "month"]
            for expr in time_expressions:
                if expr in text.lower():
                    entities["time"] = expr
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
        
        return entities
    
    def _get_required_parameters(self, intent: str) -> list[str]:
        """Get required parameters for intent"""
        required_params = {
            "create_mvp": ["project_type"],
            "collaborate": ["emails"],
            "navigate": ["page"]
        }
        
        return required_params.get(intent, [])
    
    def _get_optional_parameters(self, intent: str) -> list[str]:
        """Get optional parameters for intent"""
        optional_params = {
            "create_mvp": ["project_name", "features"],
            "edit_project": ["feature", "change"],
            "analyze_metrics": ["timeframe", "metric_type"],
            "search": ["query", "category"],
            "settings": ["setting", "value"]
        }
        
        return optional_params.get(intent, [])

class VoiceInterface:
    """Main voice interface manager"""
    
    def __init__(self):
        self.speech_recognizer = SpeechRecognizer()
        self.nlp_processor = NLPProcessor()
        self.voice_profiles: dict[str, VoiceProfile] = {}
        self.command_history: list[VoiceCommand] = []
        self.is_active = False
        
        # Start background tasks
        asyncio.create_task(self._continuous_listening())
    
    async def create_voice_profile(self, user_id: str, name: str, 
                                language: Language = Language.ENGLISH,
                                voice_speed: float = 1.0,
                                voice_pitch: float = 1.0) -> VoiceProfile:
        """Create voice profile for user"""
        try:
            profile = VoiceProfile(
                user_id=user_id,
                name=name,
                language=language,
                voice_speed=voice_speed,
                voice_pitch=voice_pitch,
                preferred_engine=SpeechEngine.GOOGLE,
                custom_commands={},
                accuracy_score=0.0,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            
            self.voice_profiles[user_id] = profile
            
            logger.info(f"Created voice profile for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating voice profile: {e}")
            raise
    
    async def process_voice_command(self, user_id: str, audio_data: bytes = None) -> VoiceCommand:
        """Process voice command from user"""
        try:
            start_time = time.time()
            
            # Get user profile
            profile = self.voice_profiles.get(user_id)
            if not profile:
                raise ValueError(f"No voice profile found for user {user_id}")
            
            # Recognize speech
            language_code = self._get_language_code(profile.language)
            recognition_result = await self.speech_recognizer.recognize_speech(
                audio_data, language_code
            )
            
            if not recognition_result["success"]:
                return VoiceCommand(
                    id=str(uuid.uuid4()),
                    command_type=VoiceCommandType.HELP,
                    transcript="",
                    confidence=0.0,
                    intent="speech_recognition_failed",
                    entities={},
                    action="provide_help",
                    parameters={"error": recognition_result["error"]},
                    timestamp=datetime.now(),
                    language=profile.language,
                    processing_time=time.time() - start_time
                )
            
            # Process with NLP
            nlp_intent = self.nlp_processor.classify_intent(recognition_result["text"])
            
            # Map to command type
            command_type = self._map_intent_to_command_type(nlp_intent.intent)
            
            # Create voice command
            command = VoiceCommand(
                id=str(uuid.uuid4()),
                command_type=command_type,
                transcript=recognition_result["text"],
                confidence=recognition_result["confidence"],
                intent=nlp_intent.intent,
                entities=nlp_intent.entities,
                action=nlp_intent.action_mapping,
                parameters=nlp_intent.entities,
                timestamp=datetime.now(),
                language=profile.language,
                processing_time=time.time() - start_time
            )
            
            # Update profile
            profile.last_used = datetime.now()
            profile.accuracy_score = (profile.accuracy_score * 0.9) + (recognition_result["confidence"] * 0.1)
            
            # Store in history
            self.command_history.append(command)
            
            # Keep only last 100 commands
            if len(self.command_history) > 100:
                self.command_history = self.command_history[-100:]
            
            return command
            
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            raise
    
    def _get_language_code(self, language: Language) -> str:
        """Get language code for speech recognition"""
        language_codes = {
            Language.ENGLISH: "en-US",
            Language.SPANISH: "es-ES",
            Language.FRENCH: "fr-FR",
            Language.GERMAN: "de-DE",
            Language.CHINESE: "zh-CN",
            Language.JAPANESE: "ja-JP",
            Language.KOREAN: "ko-KR"
        }
        
        return language_codes.get(language, "en-US")
    
    def _map_intent_to_command_type(self, intent: str) -> VoiceCommandType:
        """Map NLP intent to command type"""
        mapping = {
            "create_mvp": VoiceCommandType.CREATE_MVP,
            "edit_project": VoiceCommandType.EDIT_PROJECT,
            "analyze_metrics": VoiceCommandType.ANALYZE_METRICS,
            "collaborate": VoiceCommandType.COLLABORATE,
            "search": VoiceCommandType.SEARCH,
            "navigate": VoiceCommandType.NAVIGATE,
            "help": VoiceCommandType.HELP,
            "settings": VoiceCommandType.SETTINGS,
            "exit": VoiceCommandType.EXIT
        }
        
        return mapping.get(intent, VoiceCommandType.HELP)
    
    async def execute_command(self, command: VoiceCommand) -> dict[str, Any]:
        """Execute voice command"""
        try:
            if command.command_type == VoiceCommandType.CREATE_MVP:
                return await self._execute_create_mvp(command)
            elif command.command_type == VoiceCommandType.EDIT_PROJECT:
                return await self._execute_edit_project(command)
            elif command.command_type == VoiceCommandType.ANALYZE_METRICS:
                return await self._execute_analyze_metrics(command)
            elif command.command_type == VoiceCommandType.COLLABORATE:
                return await self._execute_collaborate(command)
            elif command.command_type == VoiceCommandType.SEARCH:
                return await self._execute_search(command)
            elif command.command_type == VoiceCommandType.NAVIGATE:
                return await self._execute_navigate(command)
            elif command.command_type == VoiceCommandType.HELP:
                return await self._execute_help(command)
            elif command.command_type == VoiceCommandType.SETTINGS:
                return await self._execute_settings(command)
            elif command.command_type == VoiceCommandType.EXIT:
                return await self._execute_exit(command)
            else:
                return {"success": False, "error": "Unknown command type"}
                
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_create_mvp(self, command: VoiceCommand) -> dict[str, Any]:
        """Execute create MVP command"""
        try:
            project_type = command.entities.get("project_type", "general")
            project_name = command.entities.get("project_name", "New Project")
            
            # Simulate MVP creation
            result = {
                "success": True,
                "action": "create_mvp",
                "project_name": project_name,
                "project_type": project_type,
                "project_id": str(uuid.uuid4()),
                "message": f"Created {project_type} MVP: {project_name}"
            }
            
            # Speak confirmation
            await self.speak_response(f"I've created a {project_type} MVP called {project_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating MVP: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_edit_project(self, command: VoiceCommand) -> dict[str, Any]:
        """Execute edit project command"""
        try:
            feature = command.entities.get("feature", "general")
            
            result = {
                "success": True,
                "action": "edit_project",
                "feature": feature,
                "message": f"Edited project {feature}"
            }
            
            await self.speak_response(f"I've edited the {feature} in your project")
            
            return result
            
        except Exception as e:
            logger.error(f"Error editing project: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_analyze_metrics(self, command: VoiceCommand) -> dict[str, Any]:
        """Execute analyze metrics command"""
        try:
            timeframe = command.entities.get("timeframe", "last_30_days")
            
            # Simulate metrics analysis
            metrics = {
                "revenue": 15000,
                "users": 1250,
                "conversion_rate": 0.05,
                "churn_rate": 0.03
            }
            
            result = {
                "success": True,
                "action": "analyze_metrics",
                "timeframe": timeframe,
                "metrics": metrics,
                "message": f"Here are your metrics for {timeframe}"
            }
            
            await self.speak_response(f"Your revenue is ${metrics['revenue']:,} with {metrics['users']} users")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing metrics: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_collaborate(self, command: VoiceCommand) -> dict[str, Any]:
        """Execute collaboration command"""
        try:
            emails = command.entities.get("emails", [])
            
            result = {
                "success": True,
                "action": "collaborate",
                "invited_emails": emails,
                "message": f"Invited {len(emails)} collaborators"
            }
            
            if emails:
                await self.speak_response(f"I've invited {len(emails)} team members to collaborate")
            else:
                await self.speak_response("Please provide email addresses to invite collaborators")
            
            return result
            
        except Exception as e:
            logger.error(f"Error collaborating: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_search(self, command: VoiceCommand) -> dict[str, Any]:
        """Execute search command"""
        try:
            query = command.entities.get("query", "")
            
            # Simulate search
            results = [
                {"title": "SaaS Template", "category": "template"},
                {"title": "Analytics Guide", "category": "documentation"},
                {"title": "Team Collaboration", "category": "feature"}
            ]
            
            result = {
                "success": True,
                "action": "search",
                "query": query,
                "results": results,
                "message": f"Found {len(results)} results for {query}"
            }
            
            await self.speak_response(f"I found {len(results)} results for {query}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_navigate(self, command: VoiceCommand) -> dict[str, Any]:
        """Execute navigation command"""
        try:
            page = command.entities.get("page", "dashboard")
            
            result = {
                "success": True,
                "action": "navigate",
                "page": page,
                "url": f"/{page}",
                "message": f"Navigated to {page}"
            }
            
            await self.speak_response(f"I've navigated to the {page}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error navigating: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_help(self, command: VoiceCommand) -> dict[str, Any]:
        """Execute help command"""
        try:
            help_text = """
            I can help you with:
            - Creating MVPs
            - Editing projects
            - Analyzing metrics
            - Collaborating with team
            - Searching resources
            - Navigating pages
            - Changing settings
            Just say what you'd like to do!
            """
            
            result = {
                "success": True,
                "action": "help",
                "help_text": help_text,
                "message": "Here's how I can help you"
            }
            
            await self.speak_response("I can help you create MVPs, analyze metrics, collaborate with your team, and much more. Just tell me what you'd like to do!")
            
            return result
            
        except Exception as e:
            logger.error(f"Error providing help: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_settings(self, command: VoiceCommand) -> dict[str, Any]:
        """Execute settings command"""
        try:
            setting = command.entities.get("setting", "")
            value = command.entities.get("value", "")
            
            result = {
                "success": True,
                "action": "settings",
                "setting": setting,
                "value": value,
                "message": f"Updated {setting} to {value}"
            }
            
            await self.speak_response(f"I've updated your {setting} setting")
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_exit(self, command: VoiceCommand) -> dict[str, Any]:
        """Execute exit command"""
        try:
            result = {
                "success": True,
                "action": "exit",
                "message": "Voice session ended"
            }
            
            await self.speak_response("Goodbye! I'll stop listening now.")
            
            # Stop listening
            await self.speech_recognizer.stop_listening()
            self.is_active = False
            
            return result
            
        except Exception as e:
            logger.error(f"Error exiting: {e}")
            return {"success": False, "error": str(e)}
    
    async def speak_response(self, text: str):
        """Speak response to user"""
        try:
            await self.speech_recognizer.speak_text(text)
        except Exception as e:
            logger.error(f"Error speaking response: {e}")
    
    async def _continuous_listening(self):
        """Background continuous listening"""
        while True:
            try:
                if self.is_active:
                    # Listen for voice command
                    recognition_result = await self.speech_recognizer.recognize_speech()
                    
                    if recognition_result["success"]:
                        # Process command (without user_id for now)
                        command = VoiceCommand(
                            id=str(uuid.uuid4()),
                            command_type=VoiceCommandType.HELP,
                            transcript=recognition_result["text"],
                            confidence=recognition_result["confidence"],
                            intent="continuous_listening",
                            entities={},
                            action="process_command",
                            parameters={},
                            timestamp=datetime.now(),
                            language=Language.ENGLISH,
                            processing_time=0.0
                        )
                        
                        # Process with NLP
                        nlp_intent = self.nlp_processor.classify_intent(command.transcript)
                        command.intent = nlp_intent.intent
                        command.action = nlp_intent.action_mapping
                        command.entities = nlp_intent.entities
                        command.command_type = self._map_intent_to_command_type(nlp_intent.intent)
                        
                        # Execute command
                        await self.execute_command(command)
                
                # Wait before next listen
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in continuous listening: {e}")
                await asyncio.sleep(5)
    
    async def start_voice_session(self, user_id: str) -> bool:
        """Start voice session for user"""
        try:
            if user_id not in self.voice_profiles:
                raise ValueError(f"No voice profile found for user {user_id}")
            
            self.is_active = True
            await self.speech_recognizer.start_listening()
            
            await self.speak_response(f"Hello {self.voice_profiles[user_id].name}! I'm listening for your commands.")
            
            logger.info(f"Started voice session for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting voice session: {e}")
            return False
    
    async def stop_voice_session(self, user_id: str) -> bool:
        """Stop voice session for user"""
        try:
            self.is_active = False
            await self.speech_recognizer.stop_listening()
            
            await self.speak_response("Voice session ended. Goodbye!")
            
            logger.info(f"Stopped voice session for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping voice session: {e}")
            return False
    
    def get_voice_commands_history(self, user_id: str, limit: int = 50) -> list[VoiceCommand]:
        """Get voice command history for user"""
        user_commands = [cmd for cmd in self.command_history if cmd.parameters.get("user_id") == user_id]
        return user_commands[-limit:]
    
    def get_voice_profile(self, user_id: str) -> VoiceProfile | None:
        """Get voice profile for user"""
        return self.voice_profiles.get(user_id)

# Global voice interface instance
voice_interface = VoiceInterface()

# API endpoints
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

router = APIRouter(prefix="/voice", tags=["voice"])

class VoiceProfileRequest(BaseModel):
    user_id: str
    name: str
    language: str = "en"
    voice_speed: float = 1.0
    voice_pitch: float = 1.0

class VoiceCommandRequest(BaseModel):
    user_id: str
    audio_data: str | None = None  # Base64 encoded

@router.post("/profile/create")
async def create_voice_profile(request: VoiceProfileRequest):
    """Create voice profile"""
    try:
        language = Language(request.language.lower())
        
        profile = await voice_interface.create_voice_profile(
            request.user_id,
            request.name,
            language,
            request.voice_speed,
            request.voice_pitch
        )
        
        return asdict(profile)
    except Exception as e:
        logger.error(f"Error creating voice profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{user_id}")
async def get_voice_profile(user_id: str):
    """Get voice profile"""
    try:
        profile = voice_interface.get_voice_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Voice profile not found")
        
        return asdict(profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/command")
async def process_voice_command(request: VoiceCommandRequest):
    """Process voice command"""
    try:
        # Decode audio data if provided
        audio_data = None
        if request.audio_data:
            import base64
            audio_data = base64.b64decode(request.audio_data)
        
        command = await voice_interface.process_voice_command(request.user_id, audio_data)
        return asdict(command)
    except Exception as e:
        logger.error(f"Error processing voice command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/start")
async def start_voice_session(user_id: str):
    """Start voice session"""
    try:
        success = await voice_interface.start_voice_session(user_id)
        return {"success": success, "user_id": user_id}
    except Exception as e:
        logger.error(f"Error starting voice session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/stop")
async def stop_voice_session(user_id: str):
    """Stop voice session"""
    try:
        success = await voice_interface.stop_voice_session(user_id)
        return {"success": success, "user_id": user_id}
    except Exception as e:
        logger.error(f"Error stopping voice session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_voice_commands_history(user_id: str, limit: int = 50):
    """Get voice command history"""
    try:
        commands = voice_interface.get_voice_commands_history(user_id, limit)
        return [asdict(command) for command in commands]
    except Exception as e:
        logger.error(f"Error getting command history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recognize")
async def recognize_speech(audio_file: UploadFile = File(...), language: str = "en-US"):
    """Recognize speech from audio file"""
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        # Recognize speech
        result = await voice_interface.speech_recognizer.recognize_speech(audio_data, language)
        return result
    except Exception as e:
        logger.error(f"Error recognizing speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/speak")
async def speak_text(text: str, speed: float = 1.0, pitch: float = 1.0):
    """Convert text to speech"""
    try:
        success = await voice_interface.speech_recognizer.speak_text(text, speed, pitch)
        return {"success": success, "text": text}
    except Exception as e:
        logger.error(f"Error speaking text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_voice_interface_status():
    """Get voice interface status"""
    try:
        return {
            "is_active": voice_interface.is_active,
            "speech_engine": voice_interface.speech_recognizer.engine.value,
            "total_profiles": len(voice_interface.voice_profiles),
            "total_commands": len(voice_interface.command_history),
            "nlp_classifier_trained": voice_interface.nlp_processor.intent_classifier is not None
        }
    except Exception as e:
        logger.error(f"Error getting voice status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
