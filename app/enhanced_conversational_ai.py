# Enhanced Conversational AI Suite - PulseBridge.ai

import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import json
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import re

# Configure logging
logger = logging.getLogger(__name__)

class ConversationContext(Enum):
    GENERAL = "general"
    MARKETING = "marketing"
    SUPPORT = "support"
    SALES = "sales"
    TECHNICAL = "technical"
    ONBOARDING = "onboarding"

class MessageType(Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    FILE = "file"
    QUICK_REPLY = "quick_reply"

class Language(Enum):
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    JAPANESE = "ja"
    CHINESE = "zh"
    KOREAN = "ko"
    DUTCH = "nl"

class SentimentScore(Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

@dataclass
class ConversationMessage:
    message_id: str
    user_id: str
    content: str
    message_type: MessageType
    timestamp: datetime
    language: Language
    context: ConversationContext
    sentiment: SentimentScore
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class UserProfile:
    user_id: str
    preferred_language: Language
    communication_style: str
    interaction_history: List[str]
    preferences: Dict[str, Any]
    timezone: str
    created_at: datetime

@dataclass
class ConversationSession:
    session_id: str
    user_id: str
    context: ConversationContext
    messages: List[ConversationMessage]
    started_at: datetime
    last_activity: datetime
    is_active: bool
    metadata: Dict[str, Any]

class EnhancedConversationalAI:
    """
    Advanced conversational AI system with multi-language support,
    voice integration, sentiment analysis, and context awareness
    """
    
    def __init__(self):
        self.conversations: Dict[str, ConversationSession] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.language_models: Dict[Language, Dict] = {}
        self.voice_synthesis_cache: Dict[str, str] = {}
        self.context_memory: Dict[str, List[Dict]] = {}
        self.intent_classifiers: Dict[str, Any] = {}
        self.sentiment_analyzer = None
        
        # Initialize language support
        self._initialize_language_models()
        self._initialize_intent_classifiers()
        
    def _initialize_language_models(self):
        """Initialize language-specific models and configurations"""
        language_configs = {
            Language.ENGLISH: {
                "greetings": ["hello", "hi", "hey", "good morning", "good afternoon"],
                "farewells": ["goodbye", "bye", "see you", "take care"],
                "affirmations": ["yes", "yeah", "sure", "absolutely", "definitely"],
                "negations": ["no", "nope", "not really", "absolutely not"],
                "courtesy": ["please", "thank you", "thanks", "appreciate"]
            },
            Language.SPANISH: {
                "greetings": ["hola", "buenos días", "buenas tardes", "buenas noches"],
                "farewells": ["adiós", "hasta luego", "nos vemos", "cuídate"],
                "affirmations": ["sí", "claro", "por supuesto", "definitivamente"],
                "negations": ["no", "para nada", "de ninguna manera"],
                "courtesy": ["por favor", "gracias", "muchas gracias", "de nada"]
            },
            Language.FRENCH: {
                "greetings": ["bonjour", "salut", "bonsoir", "coucou"],
                "farewells": ["au revoir", "à bientôt", "salut", "bonne journée"],
                "affirmations": ["oui", "bien sûr", "absolument", "certainement"],
                "negations": ["non", "pas du tout", "absolument pas"],
                "courtesy": ["s'il vous plaît", "merci", "merci beaucoup", "de rien"]
            },
            Language.GERMAN: {
                "greetings": ["hallo", "guten tag", "guten morgen", "guten abend"],
                "farewells": ["auf wiedersehen", "bis bald", "tschüss", "schönen tag"],
                "affirmations": ["ja", "natürlich", "absolut", "definitiv"],
                "negations": ["nein", "überhaupt nicht", "absolut nicht"],
                "courtesy": ["bitte", "danke", "vielen dank", "gern geschehen"]
            }
        }
        
        self.language_models = language_configs
    
    def _initialize_intent_classifiers(self):
        """Initialize intent classification patterns"""
        self.intent_classifiers = {
            "get_help": [
                r"help", r"assist", r"support", r"problem", r"issue",
                r"ayuda", r"apoyo", r"problema",  # Spanish
                r"aide", r"assistance", r"problème",  # French
                r"hilfe", r"unterstützung", r"problem"  # German
            ],
            "pricing_inquiry": [
                r"price", r"cost", r"pricing", r"plan", r"subscription",
                r"precio", r"coste", r"plan",  # Spanish
                r"prix", r"coût", r"tarif",  # French
                r"preis", r"kosten", r"tarif"  # German
            ],
            "feature_request": [
                r"feature", r"functionality", r"capability", r"can you",
                r"función", r"funcionalidad", r"capacidad",  # Spanish
                r"fonctionnalité", r"fonction", r"capacité",  # French
                r"funktion", r"funktionalität", r"fähigkeit"  # German
            ],
            "complaint": [
                r"complain", r"unhappy", r"disappointed", r"frustrated",
                r"queja", r"infeliz", r"decepcionado",  # Spanish
                r"plainte", r"mécontent", r"déçu",  # French
                r"beschwerde", r"unglücklich", r"enttäuscht"  # German
            ]
        }
    
    async def detect_language(self, text: str) -> Tuple[Language, float]:
        """Detect the language of input text"""
        try:
            # Simple language detection based on common words
            text_lower = text.lower()
            
            language_indicators = {
                Language.SPANISH: ["es", "está", "que", "con", "una", "para", "por", "como", "más"],
                Language.FRENCH: ["est", "que", "avec", "une", "pour", "par", "comme", "plus", "très"],
                Language.GERMAN: ["ist", "das", "mit", "eine", "für", "von", "wie", "mehr", "sehr"],
                Language.ITALIAN: ["è", "che", "con", "una", "per", "da", "come", "più", "molto"],
                Language.PORTUGUESE: ["é", "que", "com", "uma", "para", "por", "como", "mais", "muito"]
            }
            
            scores = {}
            for lang, indicators in language_indicators.items():
                score = sum(1 for word in indicators if word in text_lower)
                if score > 0:
                    scores[lang] = score / len(indicators)
            
            if scores:
                detected_lang = max(scores, key=scores.get)
                confidence = scores[detected_lang]
                return detected_lang, min(confidence * 2, 1.0)  # Scale confidence
            
            # Default to English if no other language detected
            return Language.ENGLISH, 0.8
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return Language.ENGLISH, 0.5
    
    async def analyze_sentiment(self, text: str, language: Language) -> Tuple[SentimentScore, float]:
        """Analyze sentiment of the input text"""
        try:
            # Simple sentiment analysis based on keywords
            text_lower = text.lower()
            
            # Language-specific sentiment indicators
            positive_words = {
                Language.ENGLISH: ["good", "great", "excellent", "amazing", "love", "perfect", "wonderful"],
                Language.SPANISH: ["bueno", "excelente", "increíble", "amor", "perfecto", "maravilloso"],
                Language.FRENCH: ["bon", "excellent", "incroyable", "amour", "parfait", "merveilleux"],
                Language.GERMAN: ["gut", "ausgezeichnet", "erstaunlich", "liebe", "perfekt", "wunderbar"]
            }.get(language, ["good", "great", "excellent"])
            
            negative_words = {
                Language.ENGLISH: ["bad", "terrible", "awful", "hate", "horrible", "worst", "disappointed"],
                Language.SPANISH: ["malo", "terrible", "horrible", "odio", "peor", "decepcionado"],
                Language.FRENCH: ["mauvais", "terrible", "affreux", "déteste", "pire", "déçu"],
                Language.GERMAN: ["schlecht", "schrecklich", "furchtbar", "hasse", "schlimmste", "enttäuscht"]
            }.get(language, ["bad", "terrible", "awful"])
            
            positive_score = sum(1 for word in positive_words if word in text_lower)
            negative_score = sum(1 for word in negative_words if word in text_lower)
            
            if positive_score > negative_score * 1.5:
                sentiment = SentimentScore.POSITIVE if positive_score <= 2 else SentimentScore.VERY_POSITIVE
                confidence = min(positive_score * 0.3, 1.0)
            elif negative_score > positive_score * 1.5:
                sentiment = SentimentScore.NEGATIVE if negative_score <= 2 else SentimentScore.VERY_NEGATIVE
                confidence = min(negative_score * 0.3, 1.0)
            else:
                sentiment = SentimentScore.NEUTRAL
                confidence = 0.6
            
            return sentiment, confidence
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return SentimentScore.NEUTRAL, 0.5
    
    async def classify_intent(self, text: str, language: Language) -> Tuple[str, float]:
        """Classify the intent of the user message"""
        try:
            text_lower = text.lower()
            intent_scores = {}
            
            for intent, patterns in self.intent_classifiers.items():
                score = 0
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        score += 1
                
                if score > 0:
                    intent_scores[intent] = score / len(patterns)
            
            if intent_scores:
                detected_intent = max(intent_scores, key=intent_scores.get)
                confidence = intent_scores[detected_intent]
                return detected_intent, confidence
            
            return "general_inquiry", 0.5
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return "general_inquiry", 0.3
    
    async def start_conversation(self, user_id: str, context: str, 
                                language: Optional[str] = None) -> Dict[str, Any]:
        """Start a new conversation session"""
        try:
            session_id = f"conv_{uuid.uuid4().hex[:12]}"
            
            # Convert string context to enum
            context_enum = ConversationContext(context) if isinstance(context, str) else context
            language_enum = Language(language) if language else Language.ENGLISH
            
            # Get or create user profile
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = UserProfile(
                    user_id=user_id,
                    preferred_language=language_enum,
                    communication_style="friendly",
                    interaction_history=[],
                    preferences={},
                    timezone="UTC",
                    created_at=datetime.now(timezone.utc)
                )
            
            user_profile = self.user_profiles[user_id]
            session_language = language_enum or user_profile.preferred_language
            
            # Create conversation session
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                context=context_enum,
                messages=[],
                started_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                is_active=True,
                metadata={"language": session_language.value}
            )
            
            self.conversations[session_id] = session
            
            # Generate welcome message based on context and language
            welcome_message = await self._generate_welcome_message(context_enum, session_language)
            
            return {
                "success": True,
                "session_id": session_id,
                "user_id": user_id,
                "context": context_enum.value,
                "language": session_language.value,
                "welcome_message": welcome_message,
                "suggested_actions": await self._get_suggested_actions(context_enum, session_language),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Conversation start failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def process_message(self, session_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming message and generate response"""
        try:
            if session_id not in self.conversations:
                raise ValueError(f"Conversation session {session_id} not found")
            
            session = self.conversations[session_id]
            content = message_data.get("content", "")
            message_type = MessageType(message_data.get("type", "text"))
            
            # Detect language and sentiment
            detected_language, lang_confidence = await self.detect_language(content)
            sentiment, sentiment_confidence = await self.analyze_sentiment(content, detected_language)
            intent, intent_confidence = await self.classify_intent(content, detected_language)
            
            # Create message record
            message = ConversationMessage(
                message_id=f"msg_{uuid.uuid4().hex[:8]}",
                user_id=session.user_id,
                content=content,
                message_type=message_type,
                timestamp=datetime.now(timezone.utc),
                language=detected_language,
                context=session.context,
                sentiment=sentiment,
                confidence=lang_confidence,
                metadata={
                    "intent": intent,
                    "intent_confidence": intent_confidence,
                    "sentiment_confidence": sentiment_confidence
                }
            )
            
            session.messages.append(message)
            session.last_activity = datetime.now(timezone.utc)
            
            # Generate contextual response
            response = await self._generate_response(session, message, intent)
            
            # Update conversation context
            await self._update_conversation_context(session, message, intent)
            
            return {
                "success": True,
                "session_id": session_id,
                "message_id": message.message_id,
                "detected_language": detected_language.value,
                "sentiment": sentiment.value,
                "intent": intent,
                "response": response,
                "suggested_replies": await self._get_suggested_replies(session, intent, detected_language),
                "conversation_summary": await self._get_conversation_summary(session),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def generate_voice_response(self, text: str, language: str, 
                                    voice_style: str = "friendly") -> Dict[str, Any]:
        """Generate voice synthesis for text response"""
        try:
            # Convert string language to enum
            language_enum = Language(language) if isinstance(language, str) else language
            
            # In a real implementation, this would use a TTS service
            # For now, we'll simulate voice generation
            
            voice_id = f"voice_{hash(text + language_enum.value + voice_style)}"
            
            # Simulate voice parameters
            voice_config = {
                "text": text,
                "language": language_enum.value,
                "voice_style": voice_style,
                "speed": 1.0,
                "pitch": 1.0,
                "volume": 0.8,
                "format": "mp3"
            }
            
            # Cache voice response
            self.voice_synthesis_cache[voice_id] = f"https://voice.pulsebridge.ai/audio/{voice_id}.mp3"
            
            return {
                "success": True,
                "voice_id": voice_id,
                "audio_url": self.voice_synthesis_cache[voice_id],
                "config": voice_config,
                "duration_seconds": len(text) * 0.05,  # Estimated duration
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def translate_message(self, text: str, from_language: str, 
                              to_language: str) -> Dict[str, Any]:
        """Translate message between languages"""
        try:
            # Convert string languages to enums
            from_lang_enum = Language(from_language) if isinstance(from_language, str) else from_language
            to_lang_enum = Language(to_language) if isinstance(to_language, str) else to_language
            
            # Simple translation simulation - in production, use proper translation API
            translation_map = {
                (Language.ENGLISH, Language.SPANISH): {
                    "hello": "hola",
                    "goodbye": "adiós",
                    "thank you": "gracias",
                    "help": "ayuda",
                    "yes": "sí",
                    "no": "no"
                },
                (Language.ENGLISH, Language.FRENCH): {
                    "hello": "bonjour",
                    "goodbye": "au revoir",
                    "thank you": "merci",
                    "help": "aide",
                    "yes": "oui",
                    "no": "non"
                }
            }
            
            text_lower = text.lower()
            translation_dict = translation_map.get((from_lang_enum, to_lang_enum), {})
            
            translated_text = text
            for english_word, translated_word in translation_dict.items():
                translated_text = translated_text.replace(english_word, translated_word)
            
            return {
                "success": True,
                "original_text": text,
                "translated_text": translated_text,
                "from_language": from_lang_enum.value,
                "to_language": to_lang_enum.value,
                "confidence": 0.8,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_conversation_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a conversation session"""
        try:
            if session_id not in self.conversations:
                raise ValueError(f"Conversation session {session_id} not found")
            
            session = self.conversations[session_id]
            messages = session.messages
            
            if not messages:
                return {
                    "success": True,
                    "session_id": session_id,
                    "analytics": {"message_count": 0},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Calculate analytics
            language_distribution = {}
            sentiment_distribution = {}
            intent_distribution = {}
            
            for message in messages:
                # Language distribution
                lang = message.language.value
                language_distribution[lang] = language_distribution.get(lang, 0) + 1
                
                # Sentiment distribution
                sentiment = message.sentiment.value
                sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
                
                # Intent distribution
                intent = message.metadata.get("intent", "unknown")
                intent_distribution[intent] = intent_distribution.get(intent, 0) + 1
            
            # Calculate conversation metrics
            total_messages = len(messages)
            conversation_duration = (session.last_activity - session.started_at).total_seconds()
            avg_response_time = conversation_duration / max(total_messages - 1, 1)
            
            # Overall sentiment
            sentiment_scores = {
                SentimentScore.VERY_POSITIVE: 2,
                SentimentScore.POSITIVE: 1,
                SentimentScore.NEUTRAL: 0,
                SentimentScore.NEGATIVE: -1,
                SentimentScore.VERY_NEGATIVE: -2
            }
            
            overall_sentiment_score = sum(
                sentiment_scores.get(msg.sentiment, 0) for msg in messages
            ) / total_messages
            
            return {
                "success": True,
                "session_id": session_id,
                "analytics": {
                    "message_count": total_messages,
                    "conversation_duration_seconds": conversation_duration,
                    "average_response_time_seconds": avg_response_time,
                    "language_distribution": language_distribution,
                    "sentiment_distribution": sentiment_distribution,
                    "intent_distribution": intent_distribution,
                    "overall_sentiment_score": overall_sentiment_score,
                    "primary_language": max(language_distribution, key=language_distribution.get),
                    "dominant_sentiment": max(sentiment_distribution, key=sentiment_distribution.get),
                    "main_intent": max(intent_distribution, key=intent_distribution.get)
                },
                "insights": await self._generate_conversation_insights(session),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Conversation analytics failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    # Helper methods
    async def _generate_welcome_message(self, context: ConversationContext, 
                                       language: Language) -> str:
        """Generate context and language-appropriate welcome message"""
        welcome_messages = {
            (ConversationContext.GENERAL, Language.ENGLISH): "Hello! I'm your PulseBridge.ai assistant. How can I help you today?",
            (ConversationContext.MARKETING, Language.ENGLISH): "Welcome to PulseBridge.ai Marketing! I'm here to help you optimize your campaigns.",
            (ConversationContext.SUPPORT, Language.ENGLISH): "Hi! I'm your support assistant. What can I help you with?",
            (ConversationContext.GENERAL, Language.SPANISH): "¡Hola! Soy tu asistente de PulseBridge.ai. ¿Cómo puedo ayudarte hoy?",
            (ConversationContext.MARKETING, Language.SPANISH): "¡Bienvenido a PulseBridge.ai Marketing! Estoy aquí para ayudarte a optimizar tus campañas.",
            (ConversationContext.GENERAL, Language.FRENCH): "Bonjour ! Je suis votre assistant PulseBridge.ai. Comment puis-je vous aider aujourd'hui?",
            (ConversationContext.MARKETING, Language.FRENCH): "Bienvenue chez PulseBridge.ai Marketing ! Je suis là pour vous aider à optimiser vos campagnes."
        }
        
        return welcome_messages.get(
            (context, language),
            "Hello! I'm your PulseBridge.ai assistant. How can I help you today?"
        )
    
    async def _get_suggested_actions(self, context: ConversationContext, 
                                   language: Language) -> List[str]:
        """Get context-appropriate suggested actions"""
        suggestions = {
            ConversationContext.MARKETING: [
                "View campaign performance",
                "Create new campaign",
                "Optimize budget allocation",
                "Generate marketing insights"
            ],
            ConversationContext.SUPPORT: [
                "Report an issue",
                "Get help with features",
                "Contact human support",
                "View documentation"
            ],
            ConversationContext.SALES: [
                "View leads",
                "Track conversions",
                "Generate sales report",
                "Schedule follow-up"
            ]
        }
        
        return suggestions.get(context, [
            "Get started",
            "Learn about features",
            "Contact support",
            "View documentation"
        ])
    
    async def _generate_response(self, session: ConversationSession, 
                               message: ConversationMessage, intent: str) -> str:
        """Generate contextual response based on intent and conversation history"""
        
        # Response templates by intent and language
        response_templates = {
            ("get_help", Language.ENGLISH): [
                "I'd be happy to help you! What specific area do you need assistance with?",
                "Sure! Let me help you with that. Can you provide more details?",
                "I'm here to assist you. What would you like help with today?"
            ],
            ("pricing_inquiry", Language.ENGLISH): [
                "I can help you with pricing information. PulseBridge.ai offers flexible plans starting at $99/month.",
                "Great question about pricing! We have plans designed for businesses of all sizes.",
                "Let me share our pricing details with you. What's your use case?"
            ],
            ("get_help", Language.SPANISH): [
                "¡Estaré encantado de ayudarte! ¿En qué área específica necesitas asistencia?",
                "¡Por supuesto! Permíteme ayudarte con eso. ¿Puedes proporcionar más detalles?"
            ],
            ("pricing_inquiry", Language.SPANISH): [
                "Puedo ayudarte con información de precios. PulseBridge.ai ofrece planes flexibles desde $99/mes.",
                "¡Excelente pregunta sobre precios! Tenemos planes diseñados para empresas de todos los tamaños."
            ]
        }
        
        # Get appropriate response template
        templates = response_templates.get(
            (intent, message.language),
            response_templates.get(
                (intent, Language.ENGLISH),
                ["Thank you for your message. How can I assist you further?"]
            )
        )
        
        # Select response based on conversation context
        import random
        response = random.choice(templates)
        
        # Add personalization based on sentiment
        if message.sentiment == SentimentScore.VERY_NEGATIVE:
            response = f"I understand you're frustrated. {response}"
        elif message.sentiment == SentimentScore.VERY_POSITIVE:
            response = f"I'm glad you're excited! {response}"
        
        return response
    
    async def _get_suggested_replies(self, session: ConversationSession, 
                                   intent: str, language: Language) -> List[str]:
        """Get suggested quick replies based on intent"""
        suggestions = {
            "get_help": ["Yes, I need help", "Tell me more", "Contact support"],
            "pricing_inquiry": ["Show me plans", "Start free trial", "Contact sales"],
            "feature_request": ["Learn more", "Schedule demo", "Get started"]
        }
        
        return suggestions.get(intent, ["Continue", "Help", "More info"])
    
    async def _get_conversation_summary(self, session: ConversationSession) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        if not session.messages:
            return {"message_count": 0, "duration": 0}
        
        duration = (session.last_activity - session.started_at).total_seconds()
        
        return {
            "message_count": len(session.messages),
            "duration_seconds": duration,
            "context": session.context.value,
            "primary_language": session.messages[-1].language.value if session.messages else "en",
            "last_intent": session.messages[-1].metadata.get("intent") if session.messages else None
        }
    
    async def _update_conversation_context(self, session: ConversationSession, 
                                         message: ConversationMessage, intent: str):
        """Update conversation context based on message"""
        user_id = session.user_id
        
        if user_id not in self.context_memory:
            self.context_memory[user_id] = []
        
        self.context_memory[user_id].append({
            "timestamp": message.timestamp.isoformat(),
            "intent": intent,
            "sentiment": message.sentiment.value,
            "language": message.language.value,
            "context": session.context.value
        })
        
        # Keep only last 50 context entries
        self.context_memory[user_id] = self.context_memory[user_id][-50:]
        
        # Update user profile
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            profile.interaction_history.append(f"{intent}:{message.sentiment.value}")
            profile.interaction_history = profile.interaction_history[-100:]  # Keep last 100
    
    async def _generate_conversation_insights(self, session: ConversationSession) -> List[str]:
        """Generate insights about the conversation"""
        insights = []
        
        if not session.messages:
            return ["No messages in conversation yet"]
        
        # Analyze sentiment trend
        sentiments = [msg.sentiment for msg in session.messages]
        if len(sentiments) > 1:
            if sentiments[-1] in [SentimentScore.POSITIVE, SentimentScore.VERY_POSITIVE]:
                insights.append("User sentiment has improved throughout the conversation")
            elif sentiments[-1] in [SentimentScore.NEGATIVE, SentimentScore.VERY_NEGATIVE]:
                insights.append("User sentiment indicates frustration - may need human intervention")
        
        # Language consistency
        languages = [msg.language for msg in session.messages]
        if len(set(languages)) == 1:
            insights.append(f"Consistent language usage: {languages[0].value}")
        else:
            insights.append("Multiple languages detected in conversation")
        
        # Intent patterns
        intents = [msg.metadata.get("intent") for msg in session.messages]
        if "complaint" in intents:
            insights.append("Complaint detected - prioritize resolution")
        if "pricing_inquiry" in intents:
            insights.append("Sales opportunity - pricing interest shown")
        
        return insights