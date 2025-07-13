#!/usr/bin/env python3
"""
Comprehensive Sikkim SmartGov Assistant Bot
"""
import asyncio
import json
import logging
import pandas as pd
import threading
import sys
import os
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import Config
from datetime import datetime
import time
import random
from typing import Dict, Tuple

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.system('chcp 65001')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class SmartGovAssistantBot:
    def __init__(self):
        """Initialize bot with configuration"""
        # Load configuration
        self.BOT_TOKEN = Config.BOT_TOKEN
        
        # Initialize states with thread-safe locks
        self.user_states = {}
        self.user_languages = {}
        self._state_lock = threading.RLock()
        
        # Load workflow data
        self._load_workflow_data()
        
        # Initialize multilingual responses
        self._initialize_responses()
        
        # Initialize aiohttp session for LLM calls
        self._session = None
        
        logger.info("🔒 MULTI-USER SUPPORT: Thread-safe state management initialized")

    def _load_workflow_data(self):
        """Load all required data files"""
        try:
            # Load emergency services data
            with open('data/emergency_services_text_responses.json', 'r', encoding='utf-8') as f:
                self.emergency_data = json.load(f)
            
            # Load other CSV data
            self.homestay_df = pd.read_csv('data/homestays_by_place.csv')
            self.csc_df = pd.read_csv('data/csc_contacts.csv')
            self.status_df = pd.read_csv('data/status.csv')
            
            logger.info("📚 Data files loaded successfully")
        except Exception as e:
            logger.error(f"❌ Error loading data files: {str(e)}")
            raise

    def _initialize_responses(self):
        """Initialize multilingual response templates"""
        self.responses = {
            'english': {
                'welcome': "Welcome to SmartGov Assistant! How can I help you today?",
                'main_menu': """🏛️ *Welcome to SmartGov Assistant* 🏛️

Our services include:

1. *Book Homestay* 🏡
   • Search by tourist destinations
   • View ratings and prices
   • Direct contact with owners

2. *Emergency Services* 🚨
   • Ambulance (102/108)
   • Police Helpline
   • Suicide Prevention
   • Health Helpline
   • Women Helpline
   • Fire Emergency
   • Report Disaster

3. *Report a Complaint* 📝
   • Register your grievance
   • Get complaint tracking ID
   • 24/7 monitoring

4. *Apply for Certificate* 💻
   • CSC operator assistance
   • Sikkim SSO portal link
   • Track application status

5. *Disaster Management* 🆘
   • Apply for Ex-gratia
   • Check application status
   • View relief norms
   • Emergency contacts

Please select a service to continue:""",
                'button_homestay': "🏡 Book Homestay",
                'button_emergency': "🚨 Emergency Services",
                'button_complaint': "📝 Report a Complaint",
                'button_certificate': "💻 Apply for Certificate",
                'button_disaster': "🆘 Disaster Management",
                'error': "Sorry, I encountered an error. Please try again.",
                'unknown': "I'm not sure what you're asking for. Here are the available services:",
                'processing': "Processing your request...",
                'success': "Your request has been processed successfully.",
                'cancelled': "Operation cancelled. How else can I help you?",
                'emergency_ambulance': "🚑 *Ambulance Emergency*\nDial: 102 or 108\nControl Room: 03592-202033",
                'emergency_police': "👮 *Police Emergency*\nDial: 100\nControl Room: 03592-202022",
                'emergency_fire': "🚒 *Fire Emergency*\nDial: 101\nControl Room: 03592-202099",
                'emergency_suicide': "💭 *Suicide Prevention Helpline*\nDial: 9152987821",
                'emergency_women': "👩 *Women Helpline*\nDial: 1091\nState Commission: 03592-205607",
                'ex_gratia_intro': "You may be eligible if you've suffered losses due to:\n• Heavy rainfall, floods, or landslides\n• Earthquakes or other natural calamities\n• Crop damage from hailstorms\n• House damage from natural disasters\n• Loss of livestock\n\nWould you like to proceed with the application?",
                'ex_gratia_form': "Please enter your full name:",
                'ex_gratia_father': "What is your father's name?",
                'ex_gratia_village': "Which village are you from?",
                'ex_gratia_contact': "What is your contact number? (10 digits)",
                'ex_gratia_ward': "What is your Ward number or name?",
                'ex_gratia_gpu': "Which Gram Panchayat Unit (GPU) are you under?",
                'ex_gratia_khatiyan': "What is your Khatiyan Number? (Land record number)",
                'ex_gratia_plot': "What is your Plot Number?",
                'ex_gratia_damage': "Please provide a detailed description of the damage:",
                'certificate_info': "To apply for services through the Sikkim SSO portal:\n1. Register and create an account on the Sikkim SSO portal\n2. Log in using your Sikkim SSO credentials\n3. Navigate to the desired service\n4. Fill out the application form\n5. Upload necessary documents\n6. Track your application status online\n\nWould you like to apply through a CSC operator or Single Window operator?",
                'other_emergency': "🚨 Other Emergency Services",
                'back_main_menu': "🔙 Back to Main Menu"
            },
            'hindi': {
                'welcome': "स्मार्टगव सहायक में आपका स्वागत है! मैं आपकी कैसे मदद कर सकता हूं?",
                'main_menu': """🏛️ *स्मार्टगव सहायक में आपका स्वागत है* 🏛️

हमारी सेवाएं शामिल हैं:

1. *होमस्टे बुक करें* 🏡
   • पर्यटन स्थलों के अनुसार खोजें
   • रेटिंग और कीमतें देखें
   • मालिकों से सीधा संपर्क

2. *आपातकालीन सेवाएं* 🚨
   • एम्बुलेंस (102/108)
   • पुलिस हेल्पलाइन
   • आत्महत्या रोकथाम
   • स्वास्थ्य हेल्पलाइन
   • महिला हेल्पलाइन
   • अग्निशमन आपातकाल
   • आपदा की रिपोर्ट करें

3. *शिकायत दर्ज करें* 📝
   • अपनी शिकायत पंजीकृत करें
   • शिकायत ट्रैकिंग आईडी प्राप्त करें
   • 24/7 निगरानी

4. *प्रमाणपत्र के लिए आवेदन करें* 💻
   • CSC ऑपरेटर सहायता
   • सिक्किम SSO पोर्टल लिंक
   • आवेदन स्थिति ट्रैक करें

5. *आपदा प्रबंधन* 🆘
   • एक्स-ग्रेटिया के लिए आवेदन करें
   • आवेदन स्थिति जांचें
   • राहत मानदंड देखें
   • आपातकालीन संपर्क

कृपया जारी रखने के लिए एक सेवा चुनें:""",
                'button_homestay': "🏡 होमस्टे बुक करें",
                'button_emergency': "🚨 आपातकालीन सेवाएं",
                'button_complaint': "📝 शिकायत दर्ज करें",
                'button_certificate': "💻 प्रमाणपत्र के लिए आवेदन",
                'button_disaster': "🆘 आपदा प्रबंधन",
                'error': "क्षमा करें, कोई त्रुटि हुई। कृपया पुनः प्रयास करें।",
                'unknown': "मुझे समझ नहीं आया। यहाँ उपलब्ध सेवाएं हैं:",
                'processing': "आपका अनुरोध प्रोसेस किया जा रहा है...",
                'success': "आपका अनुरोध सफलतापूर्वक प्रोसेस कर दिया गया है।",
                'cancelled': "प्रक्रिया रद्द कर दी गई। मैं और कैसे मदद कर सकता हूं?",
                'emergency_ambulance': "🚑 *एम्बुलेंस इमरजेंसी*\nडायल करें: 102 या 108\nकंट्रोल रूम: 03592-202033",
                'emergency_police': "👮 *पुलिस इमरजेंसी*\nडायल करें: 100\nकंट्रोल रूम: 03592-202022",
                'emergency_fire': "🚒 *अग्निशमन इमरजेंसी*\nडायल करें: 101\nकंट्रोल रूम: 03592-202099",
                'emergency_suicide': "💭 *आत्महत्या रोकथाम हेल्पलाइन*\nडायल करें: 9152987821",
                'emergency_women': "👩 *महिला हेल्पलाइन*\nडायल करें: 1091\nराज्य आयोग: 03592-205607",
                'ex_gratia_intro': "आप पात्र हो सकते हैं यदि आपको निम्नलिखित कारणों से नुकसान हुआ है:\n• भारी बारिश, बाढ़, या भूस्खलन\n• भूकंप या अन्य प्राकृतिक आपदाएं\n• ओलावृष्टि से फसल की क्षति\n• प्राकृतिक आपदाओं से घर की क्षति\n• पशुओं की हानि\n\nक्या आप आवेदन के साथ आगे बढ़ना चाहते हैं?",
                'ex_gratia_form': "कृपया अपना पूरा नाम दर्ज करें:",
                'ex_gratia_father': "आपके पिता का नाम क्या है?",
                'ex_gratia_village': "आप किस गाँव से हैं?",
                'ex_gratia_contact': "आपका संपर्क नंबर क्या है? (10 अंक)",
                'ex_gratia_ward': "आपका वार्ड नंबर या नाम क्या है?",
                'ex_gratia_gpu': "आप किस ग्राम पंचायत इकाई (GPU) के अंतर्गत हैं?",
                'ex_gratia_khatiyan': "आपका खतियान नंबर क्या है? (जमीन का रिकॉर्ड नंबर)",
                'ex_gratia_plot': "आपका प्लॉट नंबर क्या है?",
                'ex_gratia_damage': "कृपया क्षति का विस्तृत विवरण प्रदान करें:",
                'certificate_info': "सिक्किम SSO पोर्टल के माध्यम से सेवाओं के लिए आवेदन करने के लिए:\n1. सिक्किम SSO पोर्टल पर पंजीकरण करें और खाता बनाएं\n2. अपने सिक्किम SSO क्रेडेंशियल्स का उपयोग करके लॉगिन करें\n3. वांछित सेवा पर नेविगेट करें\n4. आवेदन फॉर्म भरें\n5. आवश्यक दस्तावेज अपलोड करें\n6. अपने आवेदन की स्थिति ऑनलाइन ट्रैक करें\n\nक्या आप CSC ऑपरेटर या सिंगल विंडो ऑपरेटर के माध्यम से आवेदन करना चाहते हैं?",
                'other_emergency': "🚨 अन्य आपातकालीन सेवाएं",
                'back_main_menu': "🔙 मुख्य मेनू पर वापस"
            },
            'nepali': {
                'welcome': "स्मार्टगभ सहायकमा स्वागत छ! म तपाईंलाई कसरी मद्दत गर्न सक्छु?",
                'main_menu': """🏛️ *स्मार्टगभ सहायकमा स्वागत छ* 🏛️

हाम्रो सेवाहरू समावेश छन्:

1. *होमस्टे बुक गर्नुहोस्* 🏡
   • पर्यटन स्थलहरू अनुसार खोज्नुहोस्
   • रेटिङ र मूल्यहरू हेर्नुहोस्
   • मालिकहरूसँग सिधा सम्पर्क

2. *आकस्मिक सेवाहरू* 🚨
   • एम्बुलेन्स (102/108)
   • प्रहरी हेल्पलाइन
   • आत्महत्या रोकथाम
   • स्वास्थ्य हेल्पलाइन
   • महिला हेल्पलाइन
   • अग्निशमन आकस्मिक
   • आपदा रिपोर्ट गर्नुहोस्

3. *शिकायत दर्ता गर्नुहोस्* 📝
   • आफ्नो शिकायत दर्ता गर्नुहोस्
   • शिकायत ट्र्याकिङ आईडी प्राप्त गर्नुहोस्
   • 24/7 निगरानी

4. *प्रमाणपत्रको लागि आवेदन गर्नुहोस्* 💻
   • CSC सञ्चालक सहायता
   • सिक्किम SSO पोर्टल लिङ्क
   • आवेदन स्थिति ट्र्याक गर्नुहोस्

5. *आपदा व्यवस्थापन* 🆘
   • एक्स-ग्रेटियाको लागि आवेदन गर्नुहोस्
   • आवेदन स्थिति जाँच गर्नुहोस्
   • राहत मापदण्ड हेर्नुहोस्
   • आकस्मिक सम्पर्कहरू

कृपया जारी राख्न सेवा छान्नुहोस्:""",
                'button_homestay': "🏡 होमस्टे बुक गर्नुहोस्",
                'button_emergency': "🚨 आकस्मिक सेवाहरू",
                'button_complaint': "📝 शिकायत दर्ता गर्नुहोस्",
                'button_certificate': "💻 प्रमाणपत्रको लागि आवेदन",
                'button_disaster': "🆘 आपदा व्यवस्थापन",
                'error': "माफ गर्नुहोस्, त्रुटि भयो। कृपया पुन: प्रयास गर्नुहोस्।",
                'unknown': "मलाई बुझ्न सकिएन। यहाँ उपलब्ध सेवाहरू छन्:",
                'processing': "तपाईंको अनुरोध प्रशोधन गरिँदैछ...",
                'success': "तपाईंको अनुरोध सफलतापूर्वक प्रशोधन गरियो।",
                'cancelled': "प्रक्रिया रद्द गरियो। म अरु कसरी मद्दत गर्न सक्छु?",
                'emergency_ambulance': "🚑 *एम्बुलेन्स आकस्मिक*\nडायल गर्नुहोस्: 102 वा 108\nकन्ट्रोल रूम: 03592-202033",
                'emergency_police': "👮 *प्रहरी आकस्मिक*\nडायल गर्नुहोस्: 100\nकन्ट्रोल रूम: 03592-202022",
                'emergency_fire': "🚒 *अग्निशमन आकस्मिक*\nडायल गर्नुहोस्: 101\nकन्ट्रोल रूम: 03592-202099",
                'emergency_suicide': "💭 *आत्महत्या रोकथाम हेल्पलाइन*\nडायल गर्नुहोस्: 9152987821",
                'emergency_women': "👩 *महिला हेल्पलाइन*\nडायल गर्नुहोस्: 1091\nराज्य आयोग: 03592-205607",
                'ex_gratia_intro': "तपाईं पात्र हुन सक्नुहुन्छ यदि तपाईंलाई निम्न कारणहरूले क्षति भएको छ:\n• भारी वर्षा, बाढी, वा भूस्खलन\n• भूकम्प वा अन्य प्राकृतिक आपदाहरू\n• असिनाले फसलको क्षति\n• प्राकृतिक आपदाहरूले घरको क्षति\n• पशुहरूको हानि\n\nके तपाईं आवेदनसँग अगाडि बढ्न चाहनुहुन्छ?",
                'ex_gratia_form': "कृपया आफ्नो पूरा नाम प्रविष्ट गर्नुहोस्:",
                'ex_gratia_father': "तपाईंको बुबाको नाम के हो?",
                'ex_gratia_village': "तपाईं कुन गाउँबाट हुनुहुन्छ?",
                'ex_gratia_contact': "तपाईंको सम्पर्क नम्बर के हो? (10 अंक)",
                'ex_gratia_ward': "तपाईंको वार्ड नम्बर वा नाम के हो?",
                'ex_gratia_gpu': "तपाईं कुन ग्राम पंचायत इकाई (GPU) अन्तर्गत हुनुहुन्छ?",
                'ex_gratia_khatiyan': "तपाईंको खतियान नम्बर के हो? (जमिनको रेकर्ड नम्बर)",
                'ex_gratia_plot': "तपाईंको प्लट नम्बर के हो?",
                'ex_gratia_damage': "कृपया क्षतिको विस्तृत विवरण प्रदान गर्नुहोस्:",
                'certificate_info': "सिक्किम SSO पोर्टल मार्फत सेवाहरूको लागि आवेदन गर्न:\n1. सिक्किम SSO पोर्टलमा दर्ता गर्नुहोस् र खाता सिर्जना गर्नुहोस्\n2. आफ्ना सिक्किम SSO क्रेडेन्सियलहरू प्रयोग गरेर लगइन गर्नुहोस्\n3. इच्छित सेवामा नेविगेट गर्नुहोस्\n4. आवेदन फारम भर्नुहोस्\n5. आवश्यक कागजातहरू अपलोड गर्नुहोस्\n6. आफ्नो आवेदनको स्थिति अनलाइन ट्र्याक गर्नुहोस्\n\nके तपाईं CSC सञ्चालक वा सिङ्गल विन्डो सञ्चालक मार्फत आवेदन गर्न चाहनुहुन्छ?",
                'other_emergency': "🚨 अन्य आकस्मिक सेवाहरू",
                'back_main_menu': "🔙 मुख्य मेनुमा फिर्ता"
            }
        }

    def _get_user_state(self, user_id: int) -> dict:
        """Safely get user state with locking"""
        with self._state_lock:
            return self.user_states.get(user_id, {})

    def _set_user_state(self, user_id: int, state: dict):
        """Safely set user state with locking"""
        with self._state_lock:
            self.user_states[user_id] = state
            logger.info(f"🔒 STATE UPDATE: User {user_id} → {state}")

    def _clear_user_state(self, user_id: int):
        """Safely clear user state with locking"""
        with self._state_lock:
            if user_id in self.user_states:
                del self.user_states[user_id]
                logger.info(f"🧹 STATE CLEARED: User {user_id}")

    def _get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        with self._state_lock:
            return self.user_languages.get(user_id, 'english')

    def _set_user_language(self, user_id: int, language: str):
        """Set user's preferred language"""
        with self._state_lock:
            self.user_languages[user_id] = language
            logger.info(f"🌐 LANGUAGE SET: User {user_id} → {language}")

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def detect_language(self, text: str) -> str:
        """
        Detect language using Qwen LLM exclusively.
        """
        if not text or not text.strip():
            return 'english'
            
        try:
            await self._ensure_session()
            
            # Craft a prompt that leverages Qwen's multilingual capabilities
            prompt = f"""Analyze this text and determine if it's English, Hindi, or Nepali.
            
            Text to analyze: "{text}"
            
            CRITICAL DETECTION RULES:
            
            HINDI INDICATORS (Romanized):
            - Key words: mereko, mujhe, main, aap, tum, karna, chahiye, hai, hain
            - Grammar: verb + hain/hai (karna hain, chahiye hai)
            - Pronouns: mereko, mujhe, main, aap, tum
            - Question words: kya, kaise, kahan, kab, kyun, kaun
            
            NEPALI INDICATORS (Romanized):
            - Key words: malai, ma, tapai, timi, garna, chahincha, chha, hun
            - Grammar: verb + chha/chhan (garna chha, chahincha)
            - Pronouns: malai, ma, tapai, timi
            - Question words: ke, kasari, kahaan, kahile, kina, ko
            
            ENGLISH INDICATORS:
            - Pure English vocabulary and grammar
            - No Hindi/Nepali words mixed in
            
            DECISION RULES:
            1. If text contains "mereko", "mujhe", "karna hain", "chahiye" → HINDI
            2. If text contains "malai", "garna chha", "chahincha" → NEPALI
            3. If text is pure English → ENGLISH
            4. For mixed text, identify the dominant language based on grammar patterns
            
            Examples:
            - "Mereko ex gratia apply karna hain" → HINDI (mereko + karna hain)
            - "Malai certificate apply garna chha" → NEPALI (malai + garna chha)
            - "I want to apply for ex gratia" → ENGLISH (pure English)
            
            Respond with EXACTLY one word: english, hindi, or nepali"""
            
            logger.info(f"🔍 [LLM] Language Detection Prompt: {prompt}")
            
            # Call Qwen through Ollama
            async with self._session.post(
                Config.OLLAMA_API_URL,
                json={
                    "model": Config.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                }
            ) as response:
                result = await response.json()
                detected_lang = result['response'].strip().lower()
                
                logger.info(f"🤖 [LLM] Language Detection Response: {detected_lang}")
                
                # Validate response
                if detected_lang in ['english', 'hindi', 'nepali']:
                    logger.info(f"✅ Language detected by Qwen: {detected_lang}")
                    return detected_lang
                else:
                    logger.warning(f"⚠️ Invalid language detection result: {detected_lang}, falling back to English")
                    return 'english'
                    
        except Exception as e:
            logger.error(f"❌ Language detection failed: {str(e)}")
            return 'english'  # Fallback to English on error

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        try:
            user_id = update.effective_user.id
            message_text = update.message.text
            
            logger.info(f"[MSG] User {user_id}: {message_text}")
            
            # Get current user state
            user_state = self._get_user_state(user_id)
            
            # Detect language for each message to handle language switching
            detected_lang = await self.detect_language(message_text)
            self._set_user_language(user_id, detected_lang)
            logger.info(f"[LANG] User {user_id} language detected: {detected_lang}")
            
            # Get user language
            user_lang = self._get_user_language(user_id)
            
            # If user is in a workflow, handle accordingly
            if user_state.get("workflow"):
                workflow = user_state.get("workflow")
                
                if workflow == "ex_gratia":
                    await self.handle_ex_gratia_workflow(update, context, message_text)
                elif workflow == "complaint":
                    await self.handle_complaint_workflow(update, context)
                elif workflow == "certificate":
                    await self.handle_certificate_workflow(update, context, message_text)
                elif workflow == "status_check":
                    await self.process_status_check(update, context)
                else:
                    # Unknown workflow, clear state and show main menu
                    self._clear_user_state(user_id)
                    await self.show_main_menu(update, context)
            else:
                # New conversation - detect intent and route
                logger.info(f"[INTENT] Processing new message: {message_text}")
                
                # Get intent using LLM
                intent = await self.get_intent_from_llm(message_text, user_lang)
                logger.info(f"[INTENT] Detected intent: {intent}")
                
                # Route based on intent
                if intent == "greeting":
                    await self.handle_greeting(update, context)
                elif intent == "ex_gratia":
                    await self.handle_ex_gratia(update, context)
                elif intent == "check_status":
                    await self.handle_check_status(update, context)
                elif intent == "relief_norms":
                    await self.handle_relief_norms(update, context)
                elif intent == "emergency":
                    # Direct emergency response - don't show menu
                    await self.handle_emergency_direct(update, context, message_text)
                elif intent == "tourism":
                    await self.handle_tourism_menu(update, context)
                elif intent == "complaint":
                    await self.start_complaint_workflow(update, context)
                elif intent == "certificate":
                    await self.handle_certificate_info(update, context)
                elif intent == "csc":
                    await self.handle_csc_menu(update, context)
                else:
                    # Unknown intent, show main menu
                    await self.start(update, context)
            
        except Exception as e:
            logger.error(f"❌ Error in message handler: {str(e)}")
            user_lang = self._get_user_language(update.effective_user.id) if update.effective_user else 'english'
            await update.message.reply_text(
                self.responses[user_lang]['error']
            )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        user_lang = self._get_user_language(user_id)
        logger.info(f"[USER] New conversation started by user {user_id}")
        self._clear_user_state(user_id)
        
        # Get the main menu text in user's selected language
        welcome_text = self.responses[user_lang]['main_menu']

        keyboard = [
            [InlineKeyboardButton(self.responses[user_lang]['button_homestay'], callback_data='tourism')],
            [InlineKeyboardButton(self.responses[user_lang]['button_emergency'], callback_data='emergency')],
            [InlineKeyboardButton(self.responses[user_lang]['button_complaint'], callback_data='complaint')],
            [InlineKeyboardButton(self.responses[user_lang]['button_certificate'], callback_data='certificate')],
            [InlineKeyboardButton(self.responses[user_lang]['button_disaster'], callback_data='disaster')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both regular messages and callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def detect_language_with_scoring(self, text: str) -> str:
        """Deprecated: Use detect_language instead."""
        return await self.detect_language(text)

    async def get_intent_from_llm(self, text: str, lang: str) -> str:
        """Get intent using Qwen LLM."""
        try:
            await self._ensure_session()
            
            prompt = f"""You are an intent classifier for SmartGov Assistant, a government services chatbot in Sikkim. Given the user's message, classify it into one of these intents:

Available intents:
- greeting: User is saying hello, hi, namaste, or starting a conversation (hello, hi, namaste, good morning, etc.)
- ex_gratia: User wants to APPLY for ex-gratia assistance (action-oriented)
- check_status: User wants to check status of their application
- relief_norms: User asks about relief norms, policies, eligibility criteria, or general questions about ex-gratia
- emergency: User needs emergency help (ambulance, police, fire)
- tourism: User wants tourism/homestay services
- complaint: User wants to file a complaint
- certificate: User wants to apply for certificates
- csc: User wants CSC (Common Service Center) services
- unknown: If none of the above match

Example messages for each intent:
- greeting: "Hello", "Hi", "Namaste", "Good morning", "Namaskar", "Kya haal hai", "K cha", "How are you"
- ex_gratia: "I want to apply for compensation", "Apply for ex gratia", "I need to file ex-gratia claim", "Start ex-gratia application"
- relief_norms: "What is ex gratia?", "How much compensation will I get?", "What are the eligibility criteria?", "Kya mujhe ex gratia milega?", "Ex gratia kya hain?"
- check_status: "What's the status of my application?", "Track my ex-gratia request", "Any update on my claim?"
- emergency: "Need ambulance", "Call police", "Fire emergency"
- tourism: "Book homestay", "Tourist places", "Accommodation"
- complaint: "File complaint", "Register grievance", "Report issue"
- certificate: "Apply for certificate", "Birth certificate", "Document"
- csc: "Find CSC", "CSC operator", "Common Service Center"

User message: {text}
Language: {lang}

Respond with ONLY one of the intent names listed above, nothing else."""

            logger.info(f"🎯 [LLM] Intent Classification Prompt: {prompt}")

            async with self._session.post(
                Config.OLLAMA_API_URL,
                json={
                    "model": Config.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                }
            ) as response:
                result = await response.json()
                intent = result['response'].strip().lower()
                logger.info(f"🎯 [LLM] Intent Classification Response: {intent}")
                
                # Validate intent
                valid_intents = ['greeting', 'ex_gratia', 'check_status', 'relief_norms', 'emergency', 'tourism', 'complaint', 'certificate', 'csc']
                return intent if intent in valid_intents else 'unknown'
                
        except Exception as e:
            logger.error(f"[LLM] Intent classification error: {str(e)}")
            return 'unknown'
        
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the main menu"""
        await self.start(update, context)

    async def handle_greeting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle greeting messages with language selection"""
        user_id = update.effective_user.id
        
        # Clear any existing state
        self._clear_user_state(user_id)
        
        greeting_text = """👋 *Welcome to SmartGov Assistant!*

नमस्ते! / नमस्कार! / Hello!

Please select your preferred language to continue:

कृपया अपनी पसंदीदा भाषा चुनें:

कृपया तपाईंको मनपर्ने भाषा छान्नुहोस्:"""

        keyboard = [
            [InlineKeyboardButton("🇮🇳 हिंदी (Hindi)", callback_data='lang_hindi')],
            [InlineKeyboardButton("🇳🇵 नेपाली (Nepali)", callback_data='lang_nepali')],
            [InlineKeyboardButton("🇬🇧 English", callback_data='lang_english')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(greeting_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        user_id = update.effective_user.id
        data = query.data
        logger.info(f"[CALLBACK] Received from {user_id}: {data}")

        try:
            # Always answer the callback query first
            await query.answer()

            if data == "main_menu":
                self._clear_user_state(user_id)
                await self.start(update, context)
            
            elif data == "tourism":
                await self.handle_tourism_menu(update, context)
            
            elif data.startswith("place_"):
                await self.handle_place_selection(update, context)
            
            elif data == "disaster":
                await self.handle_disaster_menu(update, context)
            
            elif data == "relief_norms":
                await self.handle_relief_norms(update, context)
            
            elif data == "check_status":
                await self.handle_check_status(update, context)
            
            elif data == "ex_gratia":
                await self.handle_ex_gratia(update, context)
            
            elif data == "ex_gratia_start":
                await self.start_ex_gratia_workflow(update, context)
            
            elif data == "ex_gratia_submit":
                await self.submit_ex_gratia_application(update, context)
            
            elif data == "ex_gratia_edit":
                await self.handle_ex_gratia_edit(update, context)
            
            elif data == "ex_gratia_cancel":
                await self.cancel_ex_gratia_application(update, context)
            
            elif data.startswith("damage_type_"):
                damage_type = data.replace("damage_type_", "")
                await self.handle_damage_type_selection(update, context, damage_type)
            
            elif data == "emergency":
                await self.handle_emergency_menu(update, context)
            
            elif data.startswith("emergency_"):
                service = data.replace("emergency_", "")
                await self.handle_emergency_service(update, context, service)
            
            elif data == "csc":
                await self.handle_csc_menu(update, context)
            
            elif data.startswith("csc_"):
                district = data.replace("csc_", "")
                await self.handle_csc_selection(update, context, district)
            
            elif data == "certificate":
                await self.handle_certificate_info(update, context)
            
            elif data.startswith("cert_"):
                cert_type = data.replace("cert_", "")
                await self.handle_certificate_choice(update, context, cert_type)
            
            elif data == "certificate_csc":
                # Handle certificate CSC choice
                user_id = update.effective_user.id
                self._set_user_state(user_id, {"workflow": "certificate", "stage": "gpu"})
                await query.edit_message_text("Please enter your GPU (Gram Panchayat Unit):", parse_mode='Markdown')
            
            elif data == "certificate_sso":
                # Handle certificate SSO choice
                await query.edit_message_text(
                    "You can apply directly on the Sikkim SSO Portal: https://sso.sikkim.gov.in\n\n"
                    "🔙 Back to Main Menu", 
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]),
                    parse_mode='Markdown'
                )
            
            elif data == "complaint":
                await self.start_complaint_workflow(update, context)
            
            elif data.startswith("lang_"):
                lang_choice = data.replace("lang_", "")
                self._set_user_language(user_id, lang_choice)
                
                # Show language-specific welcome message
                welcome_messages = {
                    'english': "✅ Language set to English! Welcome to SmartGov Assistant!",
                    'hindi': "✅ भाषा हिंदी में सेट की गई! SmartGov Assistant में आपका स्वागत है!",
                    'nepali': "✅ भाषा नेपालीमा सेट गरियो! SmartGov Assistant मा तपाईंको स्वागत छ!"
                }
                
                welcome_text = welcome_messages.get(lang_choice, f"Language set to {lang_choice.capitalize()}!")
                await query.edit_message_text(welcome_text, parse_mode='Markdown')
                
                # Wait a moment then show main menu
                await asyncio.sleep(1.5)
                await self.start(update, context)
            
            else:
                logger.warning(f"Unhandled callback data: {data}")
                await query.message.reply_text("Sorry, I couldn't process that request.")

        except Exception as e:
            logger.error(f"Error in callback handler: {str(e)}")
            await query.message.reply_text("Sorry, an error occurred. Please try again.")

    # --- Disaster Management ---
    async def handle_disaster_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle disaster management menu"""
        keyboard = [
            [InlineKeyboardButton("📝 Apply for Ex-gratia", callback_data="ex_gratia")],
            [InlineKeyboardButton("🔍 Check Application Status", callback_data="check_status")],
            [InlineKeyboardButton("ℹ️ View Relief Norms", callback_data="relief_norms")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Disaster Management Services* 🆘

Please select an option:

1. Apply for Ex-gratia assistance
2. Check your application status
3. View disaster relief norms"""

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_relief_norms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_lang = self._get_user_language(update.effective_user.id)
        text = self.responses[user_lang]['ex_gratia_intro']
        # Use reply_text if not a callback query
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')

    async def handle_check_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle application status check"""
        user_id = update.effective_user.id
        self._set_user_state(user_id, {"workflow": "check_status"})
        
        text = """*Check Application Status* 🔍

Please enter your Application ID:
(Format: EX2025XXXXXXX)"""

        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="disaster")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def process_status_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process application status check"""
        application_id = update.message.text.strip().upper()
        
        try:
            # Read status from CSV
            df = pd.read_csv('data/exgratia_applications.csv')
            application = df[df['ApplicationID'] == application_id].iloc[0]
            
            status_text = f"""*Application Status* 📋

Application ID: {application_id}
Name: {application['ApplicantName']}
Village: {application['Village']}
Status: Processing
Submission Date: {application['SubmissionTimestamp']}

Your application is being reviewed by the district administration."""
        except:
            status_text = """❌ *Application Not Found*

Please check the Application ID and try again.
If the problem persists, contact support."""

        keyboard = [[InlineKeyboardButton("🔙 Back to Disaster Menu", callback_data="disaster")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clear the workflow state
        self._clear_user_state(update.effective_user.id)

    async def handle_ex_gratia(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle ex-gratia application"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        text = f"*Ex-Gratia Assistance* 📝\n\n{self.responses[user_lang]['ex_gratia_intro']}"

        keyboard = [
            [InlineKeyboardButton("✅ Yes, Continue", callback_data="ex_gratia_start")],
            [InlineKeyboardButton("❌ No, Go Back", callback_data="disaster")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both regular messages and callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # --- Ex-Gratia Application ---
    async def start_ex_gratia_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the ex-gratia application workflow"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        self._set_user_state(user_id, {"workflow": "ex_gratia", "step": "name"})
        
        text = f"*Ex-Gratia Application Form* 📝\n\n{self.responses[user_lang]['ex_gratia_form']}"
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="disaster")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both regular messages and callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_ex_gratia_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle the ex-gratia application workflow"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        step = state.get("step")
        data = state.get("data", {})

        # Check for cancel commands first
        cancel_commands = ['cancel', 'exit', 'quit', 'stop', 'back', 'menu', 'home', 'रद्द', 'बंद', 'वापस', 'मेनू']
        if any(cmd in text.lower() for cmd in cancel_commands):
            self._clear_user_state(user_id)
            await update.message.reply_text(self.responses[user_lang]['cancelled'], parse_mode='Markdown')
            await self.show_main_menu(update, context)
            return

        # Check if user is asking a question instead of providing data
        question_indicators = ['kya', 'what', 'how', 'when', 'where', 'why', 'क्या', 'कैसे', 'कब', 'कहाँ', 'क्यों']
        if any(indicator in text.lower() for indicator in question_indicators):
            # User is asking a question, redirect to relief norms
            self._clear_user_state(user_id)
            await self.handle_relief_norms(update, context)
            return

        if step == "name":
            data["name"] = text
            state["step"] = "father_name"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_father'], parse_mode='Markdown')

        elif step == "father_name":
            data["father_name"] = text
            state["step"] = "village"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_village'], parse_mode='Markdown')

        elif step == "village":
            data["village"] = text
            state["step"] = "contact"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_contact'], parse_mode='Markdown')

        elif step == "contact":
            if not text.isdigit() or len(text) != 10:
                await update.message.reply_text("Please enter a valid 10-digit mobile number.", parse_mode='Markdown')
                return
            
            data["contact"] = text
            state["step"] = "ward"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_ward'], parse_mode='Markdown')

        elif step == "ward":
            data["ward"] = text
            state["step"] = "gpu"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_gpu'], parse_mode='Markdown')

        elif step == "gpu":
            data["gpu"] = text
            state["step"] = "khatiyan"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_khatiyan'], parse_mode='Markdown')

        elif step == "khatiyan":
            data["khatiyan_no"] = text
            state["step"] = "plot"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_plot'], parse_mode='Markdown')

        elif step == "plot":
            data["plot_no"] = text
            state["step"] = "damage_type"
            state["data"] = data
            self._set_user_state(user_id, state)
            await self.show_damage_type_options(update, context)

        elif step == "damage_type":
            data["damage_type"] = text
            state["step"] = "damage_description"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_damage'], parse_mode='Markdown')

        elif step == "damage_description":
            data["damage_description"] = text
            state["data"] = data
            self._set_user_state(user_id, state)
            await self.show_ex_gratia_confirmation(update, context, data)

        else:
            await update.message.reply_text(self.responses[user_lang]['error'], parse_mode='Markdown')
            self._clear_user_state(user_id)

    async def show_damage_type_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🏠 House Damage (₹4,000 - ₹25,000)", callback_data='damage_type_house')],
            [InlineKeyboardButton("🌾 Crop Loss (₹4,000 - ₹15,000)", callback_data='damage_type_crop')],
            [InlineKeyboardButton("🐄 Livestock Loss (₹2,000 - ₹15,000)", callback_data='damage_type_livestock')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both regular messages and callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text("Please select the type of damage:", reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text("Please select the type of damage:", reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_damage_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, damage_type: str):
        """Handle damage type selection in ex-gratia workflow"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        data = state.get("data", {})
        
        damage_types = {
            'house': '🏠 House Damage',
            'crop': '🌾 Crop Loss',
            'livestock': '🐄 Livestock Loss'
        }
        
        data['damage_type'] = damage_types[damage_type]
        state['step'] = 'damage_description'
        state['data'] = data
        self._set_user_state(user_id, state)
        
        text = f"""Selected: {damage_types[damage_type]}

Please provide detailed description of the damage:
(Include location, extent of damage, date of incident)"""

        await update.callback_query.edit_message_text(text, parse_mode='Markdown')

    async def show_ex_gratia_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
        """Show confirmation of collected data before submission"""
        summary = """*Please Review Your Application* 📋

*Personal Details:*
👤 Name: {name}
👨‍👦 Father's Name: {father}
📍 Village: {village}
📱 Contact: {contact}

*Land Details:*
🏘️ Ward: {ward}
🏛️ GPU: {gpu}
📄 Khatiyan Number: {khatiyan}
🗺️ Plot Number: {plot}

*Damage Details:*
🏷️ Type: {damage_type}
📝 Description: {damage}

Please verify all details carefully. Would you like to:""".format(
            name=data.get('name', 'N/A'),
            father=data.get('father_name', 'N/A'),
            village=data.get('village', 'N/A'),
            contact=data.get('contact', 'N/A'),
            ward=data.get('ward', 'N/A'),
            gpu=data.get('gpu', 'N/A'),
            khatiyan=data.get('khatiyan_no', 'N/A'),
            plot=data.get('plot_no', 'N/A'),
            damage_type=data.get('damage_type', 'N/A'),
            damage=data.get('damage_description', 'N/A')
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Submit Application", callback_data='ex_gratia_submit')],
            [InlineKeyboardButton("✏️ Edit Details", callback_data='ex_gratia_edit')],
            [InlineKeyboardButton("❌ Cancel", callback_data='ex_gratia_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both regular messages and callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text(summary, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')

    async def submit_ex_gratia_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Submit the ex-gratia application"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        data = state.get("data", {})

        try:
            # Generate application ID
            now = datetime.now()
            app_id = f"EXG{now.strftime('%Y%m%d')}{random.randint(1000,9999)}"
            
            # Save to CSV
            df = pd.DataFrame([{
                'ApplicationID': app_id,
                'ApplicantName': data.get('name'),
                'FatherName': data.get('father_name'),
                'Village': data.get('village'),
                'Contact': data.get('contact'),
                'Ward': data.get('ward'),
                'GPU': data.get('gpu'),
                'KhatiyanNo': data.get('khatiyan_no'),
                'PlotNo': data.get('plot_no'),
                'DamageDescription': data.get('damage_description'),
                'SubmissionTimestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'Pending'
            }])
            
            df.to_csv('data/exgratia_applications.csv', mode='a', header=False, index=False)
            
            # Send confirmation
            confirmation = f"""✅ *Application Submitted Successfully!*

🆔 Application ID: {app_id}
👤 Name: {data.get('name')}

*Next Steps:*
1. Your data will be verified
2. Update in 7-10 days
3. SMS will be sent to your number

Support: +91-1234567890"""

            keyboard = [[InlineKeyboardButton("🔙 Back to Disaster Management", callback_data="disaster")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await update.message.reply_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Clear user state
            self._clear_user_state(user_id)
            
        except Exception as e:
            logger.error(f"Error submitting application: {str(e)}")
            error_msg = "Sorry, there was an error submitting your application. Please try again."
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text(error_msg, parse_mode='Markdown')

    async def cancel_ex_gratia_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self._clear_user_state(user_id)
        await update.callback_query.edit_message_text("Your application has been cancelled.")
        await self.show_main_menu(update, context)

    async def handle_ex_gratia_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle editing of ex-gratia application details"""
        keyboard = [
            [InlineKeyboardButton("👤 Name", callback_data="edit_name")],
            [InlineKeyboardButton("👨‍👦 Father's Name", callback_data="edit_father")],
            [InlineKeyboardButton("📍 Village", callback_data="edit_village")],
            [InlineKeyboardButton("📱 Contact", callback_data="edit_contact")],
            [InlineKeyboardButton("🏘️ Ward", callback_data="edit_ward")],
            [InlineKeyboardButton("🏛️ GPU", callback_data="edit_gpu")],
            [InlineKeyboardButton("📄 Khatiyan Number", callback_data="edit_khatiyan")],
            [InlineKeyboardButton("🗺️ Plot Number", callback_data="edit_plot")],
            [InlineKeyboardButton("📝 Damage Description", callback_data="edit_damage")],
            [InlineKeyboardButton("✅ Done Editing", callback_data="edit_done")],
            [InlineKeyboardButton("❌ Cancel", callback_data="ex_gratia_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Which information would you like to edit?* ✏️

Select the field you want to update:"""
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # --- Emergency Services ---
    async def handle_emergency_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle emergency services menu"""
        keyboard = [
            [InlineKeyboardButton("🚑 Ambulance", callback_data="emergency_medical")],
            [InlineKeyboardButton("👮 Police Helpline", callback_data="emergency_police")],
            [InlineKeyboardButton("💭 Suicide Prevention", callback_data="emergency_suicide")],
            [InlineKeyboardButton("🏥 Health Helpline", callback_data="emergency_health")],
            [InlineKeyboardButton("👩 Women Helpline", callback_data="emergency_women")],
            [InlineKeyboardButton("🚒 Fire Emergency", callback_data="emergency_fire")],
            [InlineKeyboardButton("🆘 Report Disaster", callback_data="emergency_disaster")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Emergency Services* 🚨

Select the type of emergency service you need:"""
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_emergency_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
        """Handle emergency requests directly without showing menu"""
        try:
            user_id = update.effective_user.id
            user_lang = self._get_user_language(user_id)
            message_lower = message_text.lower()
            
            # Determine which emergency service is needed
            if any(word in message_lower for word in ['ambulance', 'ambulance', 'medical', 'doctor', 'hospital']):
                service_type = 'ambulance'
                response_text = self.responses[user_lang]['emergency_ambulance']
            elif any(word in message_lower for word in ['police', 'police', 'thief', 'robbery', 'crime']):
                service_type = 'police'
                response_text = self.responses[user_lang]['emergency_police']
            elif any(word in message_lower for word in ['fire', 'fire', 'burning', 'blaze']):
                service_type = 'fire'
                response_text = self.responses[user_lang]['emergency_fire']
            elif any(word in message_lower for word in ['suicide', 'suicide', 'helpline']):
                service_type = 'suicide'
                response_text = self.responses[user_lang]['emergency_suicide']
            elif any(word in message_lower for word in ['women', 'women', 'harassment']):
                service_type = 'women'
                response_text = self.responses[user_lang]['emergency_women']
            else:
                # Default to ambulance for general emergency
                service_type = 'ambulance'
                response_text = self.responses[user_lang]['emergency_ambulance']
            
            keyboard = [
                [InlineKeyboardButton(self.responses[user_lang]['other_emergency'], callback_data="emergency")],
                [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error handling emergency direct: {str(e)}")
            user_lang = self._get_user_language(update.effective_user.id) if update.effective_user else 'english'
            await update.message.reply_text(self.responses[user_lang]['error'])

    async def handle_emergency_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service_type: str):
        """Handle specific emergency service selection"""
        query = update.callback_query
        
        if service_type in ['medical', 'disaster']:
            response_text = self.emergency_data[service_type]['english']
        else:
            # Default emergency numbers for other services
            response_text = {
                'police': "👮 *Police Emergency*\nDial: 100\nControl Room: 03592-202022",
                'fire': "🚒 *Fire Emergency*\nDial: 101\nControl Room: 03592-202099",
                'women': "👩 *Women Helpline*\nDial: 1091\nState Commission: 03592-205607",
                'health': "🏥 *Health Helpline*\nDial: 104\nToll Free: 1800-345-3049",
                'suicide': "💭 *Suicide Prevention Helpline*\nDial: 9152987821"
            }.get(service_type, "Please call 112 for any emergency assistance.")
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Emergency Services", callback_data="emergency")],
            [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')

    # --- Tourism & Homestays ---
    async def handle_tourism_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle homestay booking menu"""
        places = pd.read_csv('data/homestays_by_place.csv')['Place'].unique()
        keyboard = []
        for place in places:
            keyboard.append([InlineKeyboardButton(f"🏡 {place}", callback_data=f"place_{place}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Book a Homestay* 🏡

Please select your destination:"""
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_place_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle specific place selection for homestays"""
        query = update.callback_query
        place = query.data.replace('place_', '')
        
        homestays = pd.read_csv('data/homestays_by_place.csv')
        place_homestays = homestays[homestays['Place'] == place]
        
        text = f"*Available Homestays in {place}* 🏡\n\n"
        for _, row in place_homestays.iterrows():
            text += f"*{row['HomestayName']}*\n"
            text += f"⭐ Rating: {row['Rating']}\n"
            text += f"💰 Price per night: ₹{row['PricePerNight']}\n"
            text += f"📞 Contact: {row['ContactNumber']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔍 Search Another Place", callback_data="tourism")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # --- Common Service Centers ---
    async def handle_csc_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("Find Nearest CSC", callback_data='csc_find')],
            [InlineKeyboardButton("Apply for Certificate", callback_data='certificate')],
            [InlineKeyboardButton("Back to Main Menu", callback_data='main_menu')]
        ]
        text = """*Common Service Centers (CSC)* 💻

Please select an option:
1. Find nearest CSC
2. Apply for certificate
3. Return to main menu"""
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def handle_csc_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, district: str):
        # This will be used for finding nearest CSC
        self._set_user_state(update.effective_user.id, {"workflow": "certificate", "stage": "gpu"}) # piggybacking on certificate flow for now
        await update.callback_query.edit_message_text("Please enter your GPU (Gram Panchayat Unit):", parse_mode='Markdown')

    async def handle_certificate_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle certificate services information"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        text = f"*Apply for Certificate through Sikkim SSO* 💻\n\n{self.responses[user_lang]['certificate_info']}"

        keyboard = [
            [InlineKeyboardButton("✅ Yes, Connect with CSC", callback_data="certificate_csc")],
            [InlineKeyboardButton("🌐 No, I'll use SSO Portal", callback_data="certificate_sso")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_certificate_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle certificate application workflow"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        if state.get("stage") == "gpu":
            gpu = text.strip().upper()
            csc_info = self.csc_df[self.csc_df['GPU'].str.upper() == gpu]
            if csc_info.empty:
                await update.message.reply_text("Sorry, no CSC operator found for your GPU.")
            else:
                info = csc_info.iloc[0]
                message = f"CSC Operator Details:\n\nName: {info['CSC_Operator_Name']}\nContact: {info['PhoneNumber']}\nTimings: {info['Timings']}"
                await update.message.reply_text(message)
            self._clear_user_state(user_id)

    async def handle_certificate_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str):
        if choice == 'yes':
            self._set_user_state(update.effective_user.id, {"workflow": "certificate", "stage": "gpu"})
            await update.callback_query.edit_message_text("Please enter your GPU (Gram Panchayat Unit):", parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text("You can apply directly on the Sikkim SSO Portal: https://sso.sikkim.gov.in", parse_mode='Markdown')
        
    async def handle_certificate_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        if state.get("stage") == "gpu":
            gpu = text.strip().upper()
            csc_info = self.csc_df[self.csc_df['GPU'].str.upper() == gpu]
            if csc_info.empty:
                await update.message.reply_text("Sorry, no CSC operator found for your GPU.")
            else:
                info = csc_info.iloc[0]
                message = f"CSC Operator Details:\n\nName: {info['CSC_Operator_Name']}\nContact: {info['PhoneNumber']}\nTimings: {info['Timings']}"
                await update.message.reply_text(message)
            self._clear_user_state(user_id)

    # --- Complaint ---
    async def start_complaint_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the complaint registration workflow"""
        user_id = update.effective_user.id
        self._set_user_state(user_id, {"workflow": "complaint", "step": "name"})
        
        text = """*Report a Complaint/Grievance* 📝

Please enter your full name:"""
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_complaint_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the complaint workflow steps"""
        user_id = update.effective_user.id
        text = update.message.text
        state = self._get_user_state(user_id)
        step = state.get("step")
        
        if step == "name":
            state["name"] = text
            state["step"] = "mobile"
            self._set_user_state(user_id, state)
            await update.message.reply_text("Please enter your mobile number:", parse_mode='Markdown')
        
        elif step == "mobile":
            if not text.isdigit() or len(text) != 10:
                await update.message.reply_text("Please enter a valid 10-digit mobile number.", parse_mode='Markdown')
                return
            
            state["mobile"] = text
            state["step"] = "complaint"
            self._set_user_state(user_id, state)
            await update.message.reply_text("Please describe your complaint in detail:", parse_mode='Markdown')
        
        elif step == "complaint":
            # Generate complaint ID
            now = datetime.now()
            complaint_id = f"CMP{now.strftime('%Y%m%d')}{random.randint(100, 999)}"
            
            # Save complaint to CSV
            complaint_data = {
                'Complaint_ID': complaint_id,
                'Name': state.get('name'),
                'Mobile': state.get('mobile'),
                'Complaint': text,
                'Date': now.strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'Pending'
            }
            
            df = pd.DataFrame([complaint_data])
            df.to_csv('data/submission.csv', mode='a', header=False, index=False)
            
            # Send confirmation
            confirmation = f"""✅ *Complaint Registered Successfully*

🆔 Complaint ID: {complaint_id}
👤 Name: {state.get('name')}
📱 Mobile: {state.get('mobile')}

Your complaint has been registered and will be processed soon. Please save your Complaint ID for future reference."""
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Clear user state
            self._clear_user_state(user_id)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the bot"""
        logger.error(f"[ERROR] {context.error}", exc_info=context.error)
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

    def register_handlers(self):
        """Register message and callback handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        self.application.add_error_handler(self.error_handler)  # Add error handler
        logger.info("✅ All handlers registered successfully")

    def run(self):
        """Run the bot"""
        try:
            # Create application
            self.application = Application.builder().token(self.BOT_TOKEN).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
            self.application.add_handler(CallbackQueryHandler(self.callback_handler))
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            # Start the bot
            logger.info("🚀 Starting Enhanced SmartGov Assistant Bot...")
            print("🚀 Starting Enhanced SmartGov Assistant Bot...")
            print("✅ Ready to serve citizens!")
            
            # Run the bot until the user presses Ctrl-C
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {str(e)}")
            raise

if __name__ == "__main__":
    # Initialize and run bot
    bot = SmartGovAssistantBot()
    bot.run() 