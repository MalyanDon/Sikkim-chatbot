#!/usr/bin/env python3
"""
Enhanced Conversation System for Sajilo Sewak Bot
Makes the bot more human-like with better LLM integration and natural responses
"""

import asyncio
import json
import logging
import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import aiohttp
from config import Config

logger = logging.getLogger(__name__)

class EnhancedConversationSystem:
    """Enhanced conversation system for more human-like bot responses"""
    
    def __init__(self):
        self._session = None
        self.conversation_history = {}
        self.user_personalities = {}
        self.response_templates = self._load_response_templates()
        self.contextual_responses = self._load_contextual_responses()
        
    def _load_response_templates(self) -> Dict:
        """Load human-like response templates"""
        return {
            "greeting": {
                "hindi": [
                    "नमस्ते! कैसे हैं आप? मैं आपकी कैसे मदद कर सकता हूं?",
                    "स्वागत है! आज आपको किस सेवा की जरूरत है?",
                    "नमस्कार! मैं सजिलो सेवक हूं, आपकी सहायता के लिए तैयार हूं।",
                    "हैलो! क्या हाल है? कैसे मदद करूं?"
                ],
                "nepali": [
                    "नमस्ते! तपाईं कसरी छन्? म तपाईंको कसरी सहयोग गर्न सक्छु?",
                    "स्वागत छ! आज तपाईंलाई कुन सेवाको आवश्यकता छ?",
                    "नमस्कार! म सजिलो सेवक हुँ, तपाईंको सहायताको लागि तयार छु।",
                    "हैलो! कस्तो छ? कसरी मद्दत गर्ने?"
                ],
                "english": [
                    "Hello! How are you doing today? How can I help you?",
                    "Welcome! What service do you need today?",
                    "Hi there! I'm Sajilo Sewak, ready to assist you.",
                    "Hello! How's it going? What can I help you with?"
                ]
            },
            "understanding": {
                "hindi": [
                    "मैं समझ गया। आपको {} की जरूरत है।",
                    "ठीक है, मैं समझ रहा हूं कि आप {} चाहते हैं।",
                    "हाँ, मैं समझ गया। आप {} के बारे में पूछ रहे हैं।",
                    "बिल्कुल सही! आप {} की जानकारी चाहते हैं।"
                ],
                "nepali": [
                    "म बुझेँ। तपाईंलाई {} को आवश्यकता छ।",
                    "ठीक छ, म बुझ्दैछु कि तपाईं {} चाहनुहुन्छ।",
                    "हो, म बुझेँ। तपाईं {} को बारेमा सोधिरहनुहुन्छ।",
                    "एकदम सही! तपाईं {} को जानकारी चाहनुहुन्छ।"
                ],
                "english": [
                    "I understand. You need {}.",
                    "Alright, I see you're looking for {}.",
                    "Yes, I understand. You're asking about {}.",
                    "Exactly! You want information about {}."
                ]
            },
            "helpful": {
                "hindi": [
                    "चलिए मैं आपको {} के बारे में बताता हूं।",
                    "मैं आपकी मदद करूंगा {} के साथ।",
                    "बिल्कुल! मैं आपको {} की जानकारी दे सकता हूं।",
                    "ठीक है, मैं आपको {} के बारे में सब कुछ बताऊंगा।"
                ],
                "nepali": [
                    "चलो म तपाईंलाई {} को बारेमा बताउँछु।",
                    "म तपाईंको सहयोग गर्नेछु {} सँग।",
                    "एकदम! म तपाईंलाई {} को जानकारी दिन सक्छु।",
                    "ठीक छ, म तपाईंलाई {} को बारेमा सबै बताउँछु।"
                ],
                "english": [
                    "Let me help you with {}.",
                    "I'll assist you with {}.",
                    "Absolutely! I can provide you information about {}.",
                    "Sure, I'll tell you everything about {}."
                ]
            },
            "confirmation": {
                "hindi": [
                    "क्या यह सही है?",
                    "क्या मैं आगे बढ़ सकता हूं?",
                    "क्या यह जानकारी सही है?",
                    "क्या आप इससे सहमत हैं?"
                ],
                "nepali": [
                    "के यो सही छ?",
                    "के म अगाडि बढ्न सक्छु?",
                    "के यो जानकारी सही छ?",
                    "के तपाईं यससँग सहमत हुनुहुन्छ?"
                ],
                "english": [
                    "Is this correct?",
                    "Should I proceed?",
                    "Is this information right?",
                    "Do you agree with this?"
                ]
            },
            "error": {
                "hindi": [
                    "माफ़ करें, मैं समझ नहीं पाया। क्या आप दोबारा बता सकते हैं?",
                    "क्षमा करें, मुझे स्पष्ट नहीं हुआ। कृपया फिर से बताएं।",
                    "माफ़ कीजिए, मैं समझ नहीं सका। क्या आप और स्पष्ट कर सकते हैं?",
                    "क्षमा करें, मुझे यह समझ में नहीं आया। कृपया दोबारा कहें।"
                ],
                "nepali": [
                    "माफ गर्नुहोस्, म बुझ्न सकिनँ। के तपाईं फेरि बताउन सक्नुहुन्छ?",
                    "क्षमा गर्नुहोस्, मलाई स्पष्ट भएन। कृपया फेरि बताउनुहोस्।",
                    "माफ गर्नुहोस्, म बुझ्न सकिनँ। के तपाईं थप स्पष्ट गर्न सक्नुहुन्छ?",
                    "क्षमा गर्नुहोस्, मलाई यो बुझिएन। कृपया फेरि भन्नुहोस्।"
                ],
                "english": [
                    "Sorry, I didn't understand. Could you please repeat that?",
                    "Excuse me, I'm not clear. Please tell me again.",
                    "I apologize, I couldn't understand. Could you be more specific?",
                    "Sorry, I didn't get that. Please say it again."
                ]
            },
            "success": {
                "hindi": [
                    "बहुत अच्छा! आपका {} सफलतापूर्वक पूरा हो गया है।",
                    "शानदार! आपका {} सफल रहा।",
                    "बधाई हो! आपका {} पूरा हो गया।",
                    "एकदम सही! आपका {} सफलतापूर्वक हुआ।"
                ],
                "nepali": [
                    "धेरै राम्रो! तपाईंको {} सफलतापूर्वक पूरा भयो।",
                    "शानदार! तपाईंको {} सफल भयो।",
                    "बधाई छ! तपाईंको {} पूरा भयो।",
                    "एकदम सही! तपाईंको {} सफलतापूर्वक भयो।"
                ],
                "english": [
                    "Excellent! Your {} has been completed successfully.",
                    "Great! Your {} was successful.",
                    "Congratulations! Your {} is complete.",
                    "Perfect! Your {} has been done successfully."
                ]
            }
        }
    
    def _load_contextual_responses(self) -> Dict:
        """Load contextual response patterns"""
        return {
            "emergency": {
                "hindi": "मैं समझ रहा हूं कि यह एक आपातकालीन स्थिति है। चिंता न करें, मैं आपकी तुरंत मदद करूंगा।",
                "nepali": "म बुझ्दैछु कि यो एक आकस्मिक अवस्था हो। चिन्ता नगर्नुहोस्, म तपाईंको तुरुन्तै सहयोग गर्नेछु।",
                "english": "I understand this is an emergency situation. Don't worry, I'll help you immediately."
            },
            "frustration": {
                "hindi": "मैं समझ सकता हूं कि यह निराशाजनक हो सकता है। चिंता न करें, मैं आपकी मदद करूंगा।",
                "nepali": "म बुझ्न सक्छु कि यो निराशाजनक हुन सक्छ। चिन्ता नगर्नुहोस्, म तपाईंको सहयोग गर्नेछु।",
                "english": "I can understand this might be frustrating. Don't worry, I'm here to help."
            },
            "confusion": {
                "hindi": "कोई बात नहीं, मैं आपको स्पष्ट रूप से समझाऊंगा।",
                "nepali": "कुनै समस्या छैन, म तपाईंलाई स्पष्ट रूपमा बुझाउँछु।",
                "english": "No problem, I'll explain it clearly to you."
            }
        }
    
    async def _ensure_session(self):
        """Ensure aiohttp session is available"""
        if self._session is None:
            self._session = aiohttp.ClientSession()
    
    def _get_user_personality(self, user_id: int) -> Dict:
        """Get or create user personality profile"""
        if user_id not in self.user_personalities:
            self.user_personalities[user_id] = {
                "formality_level": random.choice(["formal", "casual", "friendly"]),
                "response_length": random.choice(["brief", "detailed", "conversational"]),
                "language_preference": "english",  # Will be updated based on usage
                "interaction_count": 0,
                "last_interaction": None
            }
        return self.user_personalities[user_id]
    
    def _update_user_personality(self, user_id: int, language: str, message_length: int):
        """Update user personality based on interaction"""
        personality = self._get_user_personality(user_id)
        personality["language_preference"] = language
        personality["interaction_count"] += 1
        personality["last_interaction"] = datetime.now()
        
        # Adjust formality based on message length and content
        if message_length > 50:
            personality["response_length"] = "detailed"
        elif message_length < 20:
            personality["response_length"] = "brief"
    
    def _detect_emotion(self, text: str) -> str:
        """Detect emotional context from text"""
        text_lower = text.lower()
        
        # Emergency indicators
        if any(word in text_lower for word in ["emergency", "urgent", "help", "sos", "danger", "critical"]):
            return "emergency"
        
        # Frustration indicators
        if any(word in text_lower for word in ["frustrated", "angry", "upset", "annoyed", "tired", "fed up"]):
            return "frustration"
        
        # Confusion indicators
        if any(word in text_lower for word in ["confused", "don't understand", "unclear", "not sure", "what do you mean"]):
            return "confusion"
        
        # Positive indicators
        if any(word in text_lower for word in ["thank", "thanks", "good", "great", "excellent", "happy"]):
            return "positive"
        
        return "neutral"
    
    def _get_contextual_response(self, emotion: str, language: str) -> str:
        """Get contextual response based on emotion"""
        if emotion in self.contextual_responses:
            return self.contextual_responses[emotion].get(language, self.contextual_responses[emotion]["english"])
        return ""
    
    def _get_random_template(self, category: str, language: str) -> str:
        """Get a random response template"""
        templates = self.response_templates.get(category, {}).get(language, [])
        if templates:
            return random.choice(templates)
        # Fallback to English
        english_templates = self.response_templates.get(category, {}).get("english", [])
        return random.choice(english_templates) if english_templates else ""
    
    async def generate_human_like_response(self, user_id: int, user_message: str, 
                                         intent: str, language: str, context: Dict = None) -> str:
        """Generate a human-like response using LLM and templates"""
        
        # Update user personality
        self._update_user_personality(user_id, language, len(user_message))
        
        # Detect emotion
        emotion = self._detect_emotion(user_message)
        
        # Get user personality
        personality = self._get_user_personality(user_id)
        
        # Build context for LLM
        llm_context = {
            "user_message": user_message,
            "intent": intent,
            "language": language,
            "emotion": emotion,
            "personality": personality,
            "context": context or {}
        }
        
        # Generate response using LLM
        llm_response = await self._generate_llm_response(llm_context)
        
        # If LLM fails, fall back to template-based response
        if not llm_response:
            llm_response = self._generate_template_response(intent, language, emotion, context)
        
        # Add contextual response if needed
        if emotion != "neutral":
            contextual = self._get_contextual_response(emotion, language)
            if contextual:
                llm_response = f"{contextual}\n\n{llm_response}"
        
        return llm_response
    
    async def _generate_llm_response(self, context: Dict) -> str:
        """Generate response using LLM"""
        try:
            await self._ensure_session()
            
            prompt = self._build_llm_prompt(context)
            
            # Debug logging
            logger.info(f"[LLM DEBUG] User message: {context.get('user_message', 'N/A')}")
            logger.info(f"[LLM DEBUG] Intent: {context.get('intent', 'N/A')}")
            logger.info(f"[LLM DEBUG] Language: {context.get('language', 'N/A')}")
            logger.info(f"[LLM DEBUG] Emotion: {context.get('emotion', 'N/A')}")
            logger.info(f"[LLM DEBUG] Prompt length: {len(prompt)} characters")
            
            async with self._session.post(
                Config.OLLAMA_API_URL,
                json={
                    "model": Config.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,  # Slightly more creative
                        "top_p": 0.9,
                        "max_tokens": 200
                    }
                }
            ) as response:
                result = await response.json()
                llm_response = result.get('response', '').strip()
                logger.info(f"[LLM DEBUG] Raw LLM response: {llm_response}")
                return llm_response
                
        except Exception as e:
            logger.error(f"[LLM] Response generation error: {str(e)}")
            return ""
    
    def _build_llm_prompt(self, context: Dict) -> str:
        """Build LLM prompt for human-like response generation"""
        
        user_message = context["user_message"]
        intent = context["intent"]
        language = context["language"]
        emotion = context["emotion"]
        personality = context["personality"]
        
        # Language-specific instructions
        lang_instructions = {
            "hindi": "Respond in Hindi using natural, conversational language. Be helpful and empathetic.",
            "nepali": "Respond in Nepali using natural, conversational language. Be helpful and empathetic.",
            "english": "Respond in English using natural, conversational language. Be helpful and empathetic."
        }
        
        # Personality-based instructions
        personality_instructions = {
            "formal": "Use formal language and respectful tone.",
            "casual": "Use casual, friendly language.",
            "friendly": "Use warm, friendly language with appropriate greetings."
        }
        
        # Response length instructions
        length_instructions = {
            "brief": "Keep response concise and to the point.",
            "detailed": "Provide detailed, comprehensive response.",
            "conversational": "Use conversational tone with natural flow."
        }
        
        prompt = f"""You are Sajilo Sewak, a helpful government services chatbot in Sikkim. 

{lang_instructions.get(language, lang_instructions["english"])}
{personality_instructions.get(personality["formality_level"], "")}
{length_instructions.get(personality["response_length"], "")}

User's message: "{user_message}"
Detected intent: {intent}
User's emotion: {emotion}

Generate a natural, human-like response that:
1. Acknowledges the user's message appropriately
2. Provides helpful information or assistance
3. Maintains a warm, empathetic tone
4. Uses the detected language naturally
5. Addresses the user's emotional state if relevant

Response:"""

        return prompt
    
    def _generate_template_response(self, intent: str, language: str, emotion: str, context: Dict = None) -> str:
        """Generate response using templates as fallback"""
        
        # Get appropriate template based on intent
        if intent == "greeting":
            return self._get_random_template("greeting", language)
        elif intent in ["ex_gratia", "complaint", "certificate", "scheme"]:
            service_name = intent.replace("_", " ")
            understanding = self._get_random_template("understanding", language).format(service_name)
            helpful = self._get_random_template("helpful", language).format(service_name)
            return f"{understanding}\n\n{helpful}"
        elif intent == "emergency":
            return self.contextual_responses["emergency"].get(language, self.contextual_responses["emergency"]["english"])
        else:
            return self._get_random_template("helpful", language).format("government services")
    
    def _add_conversation_memory(self, user_id: int, user_message: str, bot_response: str):
        """Add conversation to memory for context"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 10 conversations for context
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
    
    def get_conversation_context(self, user_id: int) -> List[Dict]:
        """Get conversation history for context"""
        return self.conversation_history.get(user_id, [])
    
    async def process_user_message(self, user_id: int, user_message: str, 
                                 intent: str, language: str, context: Dict = None) -> str:
        """Main method to process user message and generate human-like response"""
        
        # Generate response
        response = await self.generate_human_like_response(user_id, user_message, intent, language, context)
        
        # Add to conversation memory
        self._add_conversation_memory(user_id, user_message, response)
        
        return response
    
    def cleanup_session(self):
        """Clean up aiohttp session"""
        if self._session:
            asyncio.create_task(self._session.close())
            self._session = None

# Test the enhanced conversation system
if __name__ == "__main__":
    import asyncio
    
    async def test_system():
        system = EnhancedConversationSystem()
        
        # Test different scenarios
        test_cases = [
            ("Hello", "greeting", "english"),
            ("मुझे ex-gratia के बारे में जानकारी चाहिए", "ex_gratia", "hindi"),
            ("I need emergency help", "emergency", "english"),
            ("मैं बहुत परेशान हूं", "complaint", "hindi"),
        ]
        
        for message, intent, language in test_cases:
            response = await system.process_user_message(123, message, intent, language)
            print(f"User: {message}")
            print(f"Bot: {response}")
            print("-" * 50)
        
        system.cleanup_session()
    
    asyncio.run(test_system()) 