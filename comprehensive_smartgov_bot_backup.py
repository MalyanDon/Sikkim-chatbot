#!/usr/bin/env python3
"""
Enhanced SmartGov Assistant Bot
Features:
- Card-based UI for all services
- Multilingual support (English, Hindi, Nepali)
- LLM-based intent detection
- Rule-based workflow management
- MULTI-USER CONCURRENT SUPPORT
"""

import asyncio
import aiohttp
import json
import time
import logging
import nest_asyncio
import pandas as pd
import csv
import os
import re
import threading
from collections import defaultdict
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import Config
from PIL import Image, ImageDraw, ImageFont
import io

# Fix for Windows event loop issues
nest_asyncio.apply()

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartGovAssistantBot:
    def __init__(self):
        """Initialize bot with configuration"""
        # Load configuration
        self.BOT_TOKEN = Config.BOT_TOKEN
        self.LLM_ENDPOINT = "http://localhost:11434/api/generate"
        self.MODEL_NAME = "qwen2"
        
        # Initialize states with thread-safe locks for concurrent access
        self.user_states = {}
        self.user_languages = {}
        self._state_lock = threading.RLock()  # Reentrant lock for state operations
        
        # Load workflow data
        self._load_workflow_data()
        
        # Initialize multilingual responses
        self._initialize_responses()
        
        logger.info("🔒 MULTI-USER SUPPORT: Thread-safe state management initialized")

    def _load_workflow_data(self):
        """Load all necessary data files"""
        # Load emergency services data
        with open('data/emergency_services_text_responses.json', 'r', encoding='utf-8') as f:
            self.emergency_data = json.load(f)
            
        # Load homestay data
        self.homestay_df = pd.read_csv('data/homestays_by_place.csv')
        
        # Load CSC contacts
        self.csc_df = pd.read_csv('data/csc_contacts.csv')
        
        # Load application status data
        self.status_df = pd.read_csv('data/status.csv')

    def _initialize_responses(self):
        """Initialize multilingual response templates"""
        self.responses = {
            'english': {
                'welcome': "🏛️ **SmartGov Services** 🏛️\n\nHow can I help you today?",
                'select_language': "🌐 Please select your preferred language:",
                'language_set': "✅ Language set to English",
                'disaster_management': {
                    'title': "🚨 Disaster Management",
                    'description': "• Ex-gratia assistance\n• Status checking\n• Disaster reporting",
                },
                'emergency_services': {
                    'title': "🚑 Emergency Services",
                    'description': "• Ambulance (102)\n• Police (100)\n• Fire (101)\n• Women Helpline",
                },
                'tourism': {
                    'title': "🏔️ Tourism & Homestays",
                    'description': "• Search by location\n• View ratings & prices\n• Book accommodations",
                },
                'csc': {
                    'title': "🏢 Common Service Centers",
                    'description': "• Find nearest CSC\n• Contact operators\n• Check services",
                }
            },
            'hindi': {
                'welcome': "🏛️ **स्मार्टगव सेवाएं** 🏛️\n\nमैं आपकी कैसे मदद कर सकता हूं?",
                'select_language': "🌐 कृपया अपनी पसंदीदा भाषा चुनें:",
                'language_set': "✅ भाषा हिंदी में सेट की गई",
                'disaster_management': {
                    'title': "🚨 आपदा प्रबंधन",
                    'description': "• अनुग्रह सहायता\n• स्थिति जांच\n• आपदा रिपोर्टिंग",
                },
                'emergency_services': {
                    'title': "🚑 आपातकालीन सेवाएं",
                    'description': "• एम्बुलेंस (102)\n• पुलिस (100)\n• अग्निशमन (101)\n• महिला हेल्पलाइन",
                },
                'tourism': {
                    'title': "🏔️ पर्यटन और होमस्टे",
                    'description': "• स्थान द्वारा खोज\n• रेटिंग और कीमतें देखें\n• आवास बुक करें",
                },
                'csc': {
                    'title': "🏢 सामान्य सेवा केंद्र",
                    'description': "• निकटतम CSC खोजें\n• ऑपरेटरलाई सम्पर्क करें\n• सेवाएं जांचें",
                }
            },
            'nepali': {
                'welcome': "🏛️ **स्मार्टगभ सेवाहरू** 🏛️\n\nम तपाईंलाई कसरी मद्दत गर्न सक्छु?",
                'select_language': "🌐 कृपया आफ्नो मनपर्ने भाषा चयन गर्नुहोस्:",
                'language_set': "✅ भाषा नेपालीमा सेट गरियो",
                'disaster_management': {
                    'title': "🚨 विपद् व्यवस्थापन",
                    'description': "• अनुग्रह सहायता\n• स्थिति जाँच\n• विपद् रिपोर्टिङ",
                },
                'emergency_services': {
                    'title': "🚑 आपतकालीन सेवाहरू",
                    'description': "• एम्बुलेन्स (102)\n• प्रहरी (100)\n• दमकल (101)\n• महिला हेल्पलाइन",
                },
                'tourism': {
                    'title': "🏔️ पर्यटन र होमस्टे",
                    'description': "• स्थान अनुसार खोज\n• रेटिङ र मूल्य हेर्नुहोस्\n• बास बुक गर्नुहोस्",
                },
                'csc': {
                    'title': "🏢 सामान्य सेवा केन्द्रहरू",
                    'description': "• नजिकको CSC खोज्नुहोस्\n• अपरेटरलाई सम्पर्क गर्नुहोस्\n• सेवाहरू जाँच्नुहोस्",
                }
            }
        }

    async def create_service_card(self, service_type: str, language: str) -> InputMediaPhoto:
        """Create a card image for a service"""
        # Create a new image with a gradient background
        width = 600
        height = 400
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Load service data
        service_data = self.responses[language][service_type]
        
        # Draw service information
        title = service_data['title']
        description = service_data['description']
        
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return InputMediaPhoto(
            media=img_byte_arr,
            caption=f"{title}\n\n{description}",
            parse_mode='Markdown'
        )

    async def get_intent_from_llm(self, message: str, language: str) -> str:
        """Get intent using LLM"""
        prompt = f"""Classify the intent of this message. Only respond with one of these intents:
        - disaster_management: Related to disaster relief, ex-gratia, etc.
        - emergency_services: Need emergency help (medical, police, fire, etc.)
        - tourism: Tourism or homestay related
        - csc: Common Service Center related
        - help: General help request
        - language: Language selection/change
        - other: Any other intent

        Message: {message}
        Language: {language}
        Intent:"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.LLM_ENDPOINT, json={
                    "model": self.MODEL_NAME,
                    "prompt": prompt,
                    "stream": False
                }) as response:
                    result = await response.json()
                    intent = result['response'].strip().lower()
                    logger.info(f"🎯 INTENT DETECTION [LLM]: Message='{message}' → Intent={intent.upper()}")
                    return intent
        except Exception as e:
            logger.error(f"❌ INTENT DETECTION ERROR: {str(e)}")
            return 'help'

    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        return self._get_user_language(user_id)

    def set_user_language(self, user_id: int, language: str):
        """Set user's preferred language"""
        self._set_user_language(user_id, language)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Create language selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="lang_english"),
                InlineKeyboardButton("🇮🇳 हिंदी", callback_data="lang_hindi"),
                InlineKeyboardButton("🇳🇵 नेपाली", callback_data="lang_nepali")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🌐 Welcome! Please select your language:\n\n"
            "🌐 कृपया अपनी भाषा चुनें:\n\n"
            "🌐 कृपया आफ्नो भाषा चयन गर्नुहोस्:",
            reply_markup=reply_markup
        )

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu with service cards"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Create service cards
        disaster_card = await self.create_service_card('disaster_management', language)
        emergency_card = await self.create_service_card('emergency_services', language)
        tourism_card = await self.create_service_card('tourism', language)
        csc_card = await self.create_service_card('csc', language)
        
        # Create menu buttons
        keyboard = [
            [InlineKeyboardButton("🚨 Disaster Management", callback_data="disaster_management")],
            [InlineKeyboardButton("🚑 Emergency Services", callback_data="emergency_services")],
            [InlineKeyboardButton("🏔️ Tourism & Homestays", callback_data="tourism")],
            [InlineKeyboardButton("🏢 Common Service Centers", callback_data="csc")],
            [InlineKeyboardButton("🌐 Change Language", callback_data="change_language")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send welcome message with menu
        welcome_text = self.responses[language]['welcome']
        if update.callback_query:
            await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline buttons"""
        query = update.callback_query
        data = query.data
        user_id = update.effective_user.id
        
        if data.startswith('lang_'):
            language = data.replace('lang_', '')
            self.set_user_language(user_id, language)
            await query.answer(self.responses[language]['language_set'])
            await self.show_main_menu(update, context)
            
        elif data == 'disaster_management':
            await self.handle_disaster_management(update, context)
            
        elif data == 'emergency_services':
            await self.handle_emergency_services(update, context)
            
        elif data == 'tourism':
            await self.handle_tourism(update, context)
            
        elif data == 'csc':
            await self.handle_csc(update, context)
            
        elif data == 'change_language':
            await self.start_command(update, context)
            
        elif data == 'back_main':
            await self.show_main_menu(update, context)
            
        # Disaster Management callbacks
        elif data == 'exgratia_apply':
            await self.handle_exgratia_application(update, context)
            
        elif data == 'status_check':
            await self.handle_status_check(update, context)
            
        elif data == 'exgratia_norms':
            await self.show_exgratia_norms(update, context)
            
        elif data == 'application_process':
            await self.show_application_process(update, context)
            
        elif data == 'disaster_report':
            await self.handle_complaint_filing(update, context)
            
        # Emergency Services callbacks
        elif data.startswith('emergency_'):
            service_type = data.replace('emergency_', '')
            await self.handle_emergency_response(update, context, service_type)
            
        # Tourism callbacks
        elif data.startswith('place_'):
            place = data.replace('place_', '')
            await self.handle_place_selection(update, context, place)
            
        # CSC callbacks
        elif data == 'find_csc':
            await self.handle_csc_finder(update, context)
            
        elif data == 'contact_operators':
            await self.show_csc_operators(update, context)
            
        elif data == 'check_services':
            await self.show_csc_services(update, context)
            
        elif data == 'certificate_apply':
            await self.handle_certificate_application(update, context)
            
        elif data == 'cancel_workflow':
            await self.handle_cancel_workflow(update, context)
            
        await query.answer()

    async def handle_cancel_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle workflow cancellation via button"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Clear any existing user state
        self._clear_user_state(user_id)
        
        # Send cancellation message
        if language == 'hindi':
            cancel_msg = "❌ प्रक्रिया रद्द की गई। मुख्य मेनू पर वापस जा रहे हैं..."
        elif language == 'nepali':
            cancel_msg = "❌ प्रक्रिया रद्द गरियो। मुख्य मेनूमा फर्कदै..."
        else:
            cancel_msg = "❌ Process cancelled. Returning to main menu..."
        
        await update.callback_query.edit_message_text(cancel_msg)
        
        # Show main menu after a brief moment
        await asyncio.sleep(1)
        await self.show_main_menu(update, context)

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        message = update.message.text
        user_id = update.effective_user.id
        
        # Check for cancel/exit commands first (before any workflow processing)
        cancel_commands = [
            'cancel', 'exit', 'quit', 'stop', 'back', 'menu', 'home',
            'band karo', 'bandkaro', 'band kr', 'bandkar', 'cancel karo', 'cancel kar',
            'रद्द करो', 'बंद करो', 'रोको', 'छोड़ो', 'वापस', 'मेनू', 'घर',
            'रद्द गर्नुहोस्', 'बन्द गर्नुहोस्', 'रोक्नुहोस्', 'छोड्नुहोस्', 'फर्कनुहोस्', 'मेनु', 'घर'
        ]
        
        if any(cmd in message.lower() for cmd in cancel_commands):
            # Clear any existing user state
            self._clear_user_state(user_id)
            
            language = self.get_user_language(user_id)
            
            # Send cancellation confirmation message
            if language == 'hindi':
                cancel_msg = "❌ प्रक्रिया रद्द की गई। मुख्य मेनू पर वापस जा रहे हैं..."
            elif language == 'nepali':
                cancel_msg = "❌ प्रक्रिया रद्द गरियो। मुख्य मेनूमा फर्कदै..."
            else:
                cancel_msg = "❌ Process cancelled. Returning to main menu..."
            
            await update.message.reply_text(cancel_msg)
            
            # Return to main menu
            await self.show_main_menu(update, context)
            return
        
        # If user is in a workflow, handle it
        user_state = self._get_user_state(user_id)
        if user_state:
            await self.handle_workflow_input(update, context, message, user_state)
            return
        
        # Get intent using LLM
        intent = await self.get_intent_from_llm(message, self.get_user_language(user_id))
        
        # Handle intent
        if intent == 'disaster_management':
            await self.handle_disaster_management(update, context)
        elif intent == 'emergency_services':
            await self.handle_emergency_services(update, context)
        elif intent == 'tourism':
            await self.handle_tourism(update, context)
        elif intent == 'csc':
            await self.handle_csc(update, context)
        elif intent == 'language':
            await self.start_command(update, context)
        else:
            await self.show_main_menu(update, context)

    async def handle_workflow_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, state: dict):
        """Handle user input in workflows"""
        user_id = update.effective_user.id
        workflow_type = state['type']
        stage = state['stage']
        language = state['language']
        
        if workflow_type == 'exgratia':
            await self.handle_exgratia_workflow(update, context, message, state)
        elif workflow_type == 'status':
            await self.handle_status_workflow(update, context, message, state)
        elif workflow_type == 'csc':
            await self.handle_csc_workflow(update, context, message, state)
        elif workflow_type == 'complaint':
            await self.handle_complaint_workflow(update, context, message, state)

    async def handle_exgratia_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, state: dict):
        """Handle ex-gratia application workflow"""
        user_id = update.effective_user.id
        stage = state['stage']
        language = state['language']
        
        if stage == 'name':
            if len(message.strip()) < 2:
                await update.message.reply_text("❌ Please provide a valid name")
                return
            state['data']['name'] = message.strip()
            state['stage'] = 'father_name'
            
            if language == 'hindi':
                await update.message.reply_text("👨 आपके पिता का पूरा नाम क्या है?")
            elif language == 'nepali':
                await update.message.reply_text("👨 तपाईंको बुबाको पूरा नाम के हो?")
            else:
                await update.message.reply_text("👨 What is your father's full name?")
                
        elif stage == 'father_name':
            if len(message.strip()) < 2:
                await update.message.reply_text("❌ Please provide a valid father's name")
                return
            state['data']['father_name'] = message.strip()
            state['stage'] = 'village'
            
            if language == 'hindi':
                await update.message.reply_text("🏘️ आपका गांव/शहर का नाम क्या है?")
            elif language == 'nepali':
                await update.message.reply_text("🏘️ तपाईंको गाउँ/सहरको नाम के हो?")
            else:
                await update.message.reply_text("🏘️ What is your village/town name?")
                
        elif stage == 'village':
            if len(message.strip()) < 2:
                await update.message.reply_text("❌ Please provide a valid village/town name")
                return
            state['data']['village'] = message.strip()
            state['stage'] = 'contact'
            
            if language == 'hindi':
                await update.message.reply_text("📱 आपका संपर्क नंबर क्या है? (10 अंक)")
            elif language == 'nepali':
                await update.message.reply_text("📱 तपाईंको सम्पर्क नम्बर के हो? (10 अंक)")
            else:
                await update.message.reply_text("📱 What is your contact number? (10 digits)")
                
        elif stage == 'contact':
            # Validate phone number
            clean_phone = message.strip().replace(' ', '').replace('-', '').replace('+91', '')
            if not (len(clean_phone) == 10 and clean_phone.isdigit()):
                await update.message.reply_text("❌ Please provide a valid 10-digit phone number")
                return
            state['data']['contact'] = clean_phone
            state['stage'] = 'damage_type'
            
            if language == 'hindi':
                damage_text = """🌪️ कौन सी आपदा हुई?
1️⃣ बाढ़
2️⃣ भूस्खलन
3️⃣ भूकंप
4️⃣ आग
5️⃣ तूफान/चक्रवात
6️⃣ अन्य

कृपया 1-6 में से चुनें:"""
            elif language == 'nepali':
                damage_text = """🌪️ कुन प्रकारको विपद् भयो?
1️⃣ बाढी
2️⃣ पहिरो
3️⃣ भूकम्प
4️⃣ आगो
5️⃣ आँधी/चक्रवात
6️⃣ अन्य

कृपया 1-6 मध्ये छान्नुहोस्:"""
            else:
                damage_text = """🌪️ What type of damage occurred?
1️⃣ Flood
2️⃣ Landslide
3️⃣ Earthquake
4️⃣ Fire
5️⃣ Storm/Cyclone
6️⃣ Other

Please select 1-6:"""
            await update.message.reply_text(damage_text)
            
        elif stage == 'damage_type':
            if message not in ['1', '2', '3', '4', '5', '6']:
                await update.message.reply_text("❌ Please select a number between 1-6")
                return
            damage_types = {'1': 'Flood', '2': 'Landslide', '3': 'Earthquake', '4': 'Fire', '5': 'Storm/Cyclone', '6': 'Other'}
            state['data']['damage_type'] = damage_types[message]
            state['stage'] = 'damage_description'
            
            if language == 'hindi':
                await update.message.reply_text("📝 क्षति का विस्तृत विवरण दें:\n(घर की क्षति, संपत्ति की हानि, आदि)")
            elif language == 'nepali':
                await update.message.reply_text("📝 क्षतिको विस्तृत विवरण दिनुहोस्:\n(घरको क्षति, सम्पत्तिको हानि, आदि)")
            else:
                await update.message.reply_text("📝 Provide detailed description of damage:\n(House damage, property loss, etc.)")
                
        elif stage == 'damage_description':
            if len(message.strip()) < 10:
                await update.message.reply_text("❌ Please provide a detailed description (minimum 10 characters)")
                return
            state['data']['damage_description'] = message.strip()
            await self.complete_exgratia_application(update, context, state)

    async def complete_exgratia_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
        """Complete ex-gratia application and save data"""
        user_id = update.effective_user.id
        data = state['data']
        language = state['language']
        
        # Generate application ID
        import random
        app_id = f"24EXG{random.randint(10000, 99999)}"
        submission_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save to CSV
        application_data = {
            'Application_ID': app_id,
            'Name': data['name'],
            'Father_Name': data['father_name'],
            'Village': data['village'],
            'Contact': data['contact'],
            'Damage_Type': data['damage_type'],
            'Damage_Description': data['damage_description'],
            'Submission_Date': submission_date,
            'Language': language.upper(),
            'Status': 'Submitted'
        }
        
        # Append to exgratia applications CSV
        df = pd.DataFrame([application_data])
        try:
            df.to_csv('data/exgratia_applications.csv', mode='a', header=False, index=False)
        except:
            df.to_csv('data/exgratia_applications.csv', mode='w', header=True, index=False)
        
        # Success message
        if language == 'hindi':
            success_msg = f"""✅ **आवेदन सफलतापूर्वक जमा हुआ!**

🆔 **आवेदन आईडी:** `{app_id}`
📅 **जमा तिथि:** {submission_date}
👤 **आवेदक:** {data['name']}
📱 **संपर्क:** {data['contact']}

**📋 आवेदन विवरण:**
👨 **पिता का नाम:** {data['father_name']}
🏘️ **गांव:** {data['village']}
🌪️ **क्षति प्रकार:** {data['damage_type']}
📝 **क्षति विवरण:** {data['damage_description']}

📞 **सहायता संपर्क:** 1077
⏰ **प्रसंस्करण समय:** 7-15 कार्य दिवस"""
        elif language == 'nepali':
            success_msg = f"""✅ **आवेदन सफलतापूर्वक पेश गरियो!**

🆔 **आवेदन आईडी:** `{app_id}`
📅 **पेश मिति:** {submission_date}
👤 **आवेदक:** {data['name']}
📱 **सम्पर्क:** {data['contact']}

**📋 आवेदन विवरण:**
👨 **बुबाको नाम:** {data['father_name']}
🏘️ **गाउँ:** {data['village']}
🌪️ **क्षति प्रकार:** {data['damage_type']}
📝 **क्षति विवरण:** {data['damage_description']}

📞 **सहायता सम्पर्क:** 1077
⏰ **प्रसंस्करण समय:** 7-15 कार्य दिन"""
        else:
            success_msg = f"""✅ **Application Submitted Successfully!**

🆔 **Application ID:** `{app_id}`
📅 **Submission Date:** {submission_date}
👤 **Applicant:** {data['name']}
📱 **Contact:** {data['contact']}

**📋 Application Details:**
👨 **Father's Name:** {data['father_name']}
🏘️ **Village:** {data['village']}
🌪️ **Damage Type:** {data['damage_type']}
📝 **Damage Description:** {data['damage_description']}

📞 **Support Contact:** 1077
⏰ **Processing Time:** 7-15 working days"""
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(success_msg, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clear user state
        self._clear_user_state(user_id)

    async def handle_status_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, state: dict):
        """Handle status check workflow"""
        user_id = update.effective_user.id
        language = state['language']
        
        # Check if application ID exists in CSV
        try:
            df = pd.read_csv('data/status.csv')
            status_info = df[df['application_id'] == message.strip()]
            
            if not status_info.empty:
                row = status_info.iloc[0]
                status_msg = f"""✅ **Application Status Found**

🆔 **Application ID:** {row['application_id']}
👤 **Name:** {row['name']}
📅 **Date:** {row['date']}
📊 **Status:** {row['status']}
📝 **Details:** {row['details']}"""
            else:
                if language == 'hindi':
                    status_msg = "❌ इस आईडी के लिए कोई आवेदन नहीं मिला। कृपया आईडी की जांच करें।"
                elif language == 'nepali':
                    status_msg = "❌ यो आईडीको लागि कुनै आवेदन फेला परेन। कृपया आईडी जाँच गर्नुहोस्।"
                else:
                    status_msg = "❌ No application found for this ID. Please check your Application ID."
        except:
            status_msg = "❌ Unable to check status at the moment. Please try again later."
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(status_msg, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clear user state
        self._clear_user_state(user_id)

    async def handle_csc_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, state: dict):
        """Handle CSC finder workflow"""
        user_id = update.effective_user.id
        language = state['language']
        
        # Find CSC by GPU
        try:
            csc_info = self.csc_df[self.csc_df['gpu'] == message.strip()]
            
            if not csc_info.empty:
                row = csc_info.iloc[0]
                if language == 'hindi':
                    csc_msg = f"""✅ **CSC ऑपरेटर मिला!**

👤 **ऑपरेटर:** {row['operator_name']}
📞 **संपर्क:** {row['contact']}
🏛️ **GPU:** {row['gpu']}
⏰ **समय:** {row['timings']}"""
                elif language == 'nepali':
                    csc_msg = f"""✅ **CSC अपरेटर भेटियो!**

👤 **अपरेटर:** {row['operator_name']}
📞 **सम्पर्क:** {row['contact']}
🏛️ **GPU:** {row['gpu']}
⏰ **समय:** {row['timings']}"""
                else:
                    csc_msg = f"""✅ **CSC Operator Found!**

👤 **Operator:** {row['operator_name']}
📞 **Contact:** {row['contact']}
🏛️ **GPU:** {row['gpu']}
⏰ **Timings:** {row['timings']}"""
            else:
                if language == 'hindi':
                    csc_msg = "❌ इस GPU के लिए कोई CSC ऑपरेटर नहीं मिला।"
                elif language == 'nepali':
                    csc_msg = "❌ यो GPU को लागि कुनै CSC अपरेटर भेटिएन।"
                else:
                    csc_msg = "❌ No CSC operator found for this GPU."
        except:
            csc_msg = "❌ Unable to search CSC operators at the moment."
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(csc_msg, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clear user state
        self._clear_user_state(user_id)

    async def handle_complaint_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, state: dict):
        """Handle complaint filing workflow"""
        user_id = update.effective_user.id
        stage = state['stage']
        language = state['language']
        
        if stage == 'name':
            state['data']['name'] = message.strip()
            state['stage'] = 'mobile'
            
            if language == 'hindi':
                await update.message.reply_text("📱 कृपया अपना मोबाइल नंबर दें:")
            elif language == 'nepali':
                await update.message.reply_text("📱 कृपया आफ्नो मोबाइल नम्बर दिनुहोस्:")
            else:
                await update.message.reply_text("📱 Please provide your mobile number:")
                
        elif stage == 'mobile':
            # Validate mobile number
            clean_mobile = message.strip().replace(' ', '').replace('-', '').replace('+91', '')
            if not (len(clean_mobile) == 10 and clean_mobile.isdigit()):
                await update.message.reply_text("❌ Please provide a valid 10-digit mobile number")
                return
            state['data']['mobile'] = clean_mobile
            state['stage'] = 'complaint'
            
            if language == 'hindi':
                await update.message.reply_text("📝 कृपया अपनी शिकायत का विस्तृत विवरण दें:")
            elif language == 'nepali':
                await update.message.reply_text("📝 कृपया आफ्नो गुनासोको विस्तृत विवरण दिनुहोस्:")
            else:
                await update.message.reply_text("📝 Please provide detailed description of your complaint:")
                
        elif stage == 'complaint':
            if len(message.strip()) < 10:
                await update.message.reply_text("❌ Please provide a detailed complaint (minimum 10 characters)")
                return
            state['data']['complaint'] = message.strip()
            await self.complete_complaint_filing(update, context, state)

    async def complete_complaint_filing(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
        """Complete complaint filing"""
        user_id = update.effective_user.id
        data = state['data']
        language = state['language']
        
        # Generate complaint ID
        complaint_id = f"CMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Success message
        if language == 'hindi':
            success_msg = f"""✅ **शिकायत सफलतापूर्वक दर्ज!**

🆔 **शिकायत आईडी:** `{complaint_id}`
👤 **नाम:** {data['name']}
📱 **मोबाइल:** {data['mobile']}

आपकी शिकायत दर्ज कर दी गई है और जल्द ही इसकी समीक्षा की जाएगी।"""
        elif language == 'nepali':
            success_msg = f"""✅ **गुनासो सफलतापूर्वक दर्ता!**

🆔 **गुनासो आईडी:** `{complaint_id}`
👤 **नाम:** {data['name']}
📱 **मोबाइल:** {data['mobile']}

तपाईंको गुनासो दर्ता गरियो र चाँडै यसको समीक्षा गरिनेछ।"""
        else:
            success_msg = f"""✅ **Complaint Filed Successfully!**

🆔 **Complaint ID:** `{complaint_id}`
👤 **Name:** {data['name']}
📱 **Mobile:** {data['mobile']}

Your complaint has been registered and will be reviewed soon."""
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(success_msg, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clear user state
        self._clear_user_state(user_id)

    # Additional helper methods for CSC services
    async def show_csc_operators(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all CSC operators"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        operators_text = "📞 **CSC Operators Contact List**\n\n"
        for _, row in self.csc_df.iterrows():
            operators_text += f"*{row['operator_name']}*\n"
            operators_text += f"📞 Contact: {row['contact']}\n"
            operators_text += f"🏛️ GPU: {row['gpu']}\n"
            operators_text += f"⏰ Timings: {row['timings']}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="csc")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=operators_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_csc_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show CSC services information"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        if language == 'hindi':
            services_text = """📋 **CSC सेवाएं**

• आधार कार्ड सेवाएं
• पैन कार्ड आवेदन
• वोटर आईडी सेवाएं
• प्रमाणपत्र आवेदन
• ऑनलाइन फॉर्म भरना
• बैंकिंग सेवाएं
• बिल भुगतान
• इंटरनेट सेवाएं"""
        elif language == 'nepali':
            services_text = """📋 **CSC सेवाहरू**

• आधार कार्ड सेवाहरू
• पैन कार्ड आवेदन
• मतदाता परिचयपत्र सेवाहरू
• प्रमाणपत्र आवेदन
• अनलाइन फारम भर्ने
• बैंकिङ सेवाहरू
• बिल भुक्तानी
• इन्टरनेट सेवाहरू"""
        else:
            services_text = """📋 **CSC Services**

• Aadhaar Card Services
• PAN Card Application
• Voter ID Services
• Certificate Applications
• Online Form Filling
• Banking Services
• Bill Payments
• Internet Services"""
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="csc")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=services_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_certificate_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle certificate application information"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        if language == 'hindi':
            cert_text = """📜 **प्रमाणपत्र आवेदन प्रक्रिया**

सिक्किम SSO पोर्टल के माध्यम से सेवाओं के लिए आवेदन करने हेतु:

1. [सिक्किम SSO पोर्टल](https://sso.sikkim.gov.in) पर खाता बनाएं
2. अपनी SSO साख से लॉग इन करें
3. वांछित सेवा तक नेविगेट करें
4. आवेदन पत्र भरें
5. आवश्यक दस्तावेज अपलोड करें
6. ऑनलाइन आवेदन स्थिति ट्रैक करें

क्या आप CSC ऑपरेटर के माध्यम से आवेदन करना चाहते हैं?"""
        elif language == 'nepali':
            cert_text = """📜 **प्रमाणपत्र आवेदन प्रक्रिया**

सिक्किम SSO पोर्टल मार्फत सेवाहरूको लागि आवेदन गर्न:

1. [सिक्किम SSO पोर्टल](https://sso.sikkim.gov.in) मा खाता बनाउनुहोस्
2. आफ्नो SSO प्रमाणहरूसँग लग इन गर्नुहोस्
3. चाहिएको सेवा मा नेभिगेट गर्नुहोस्
4. आवेदन फारम भर्नुहोस्
5. आवश्यक कागजातहरू अपलोड गर्नुहोस्
6. अनलाइन आवेदन स्थिति ट्र्याक गर्नुहोस्

के तपाईं CSC अपरेटर मार्फत आवेदन गर्न चाहनुहुन्छ?"""
        else:
            cert_text = """📜 **Certificate Application Process**

To apply for services through Sikkim SSO portal:

1. Register at [Sikkim SSO Portal](https://sso.sikkim.gov.in)
2. Log in with your SSO credentials
3. Navigate to the desired service
4. Fill out the application form
5. Upload necessary documents
6. Track your application status online

Would you like to apply through a CSC operator?"""
        
        keyboard = [
            [InlineKeyboardButton("✅ Yes, find CSC", callback_data="find_csc")],
            [InlineKeyboardButton("🌐 Apply Online", url="https://sso.sikkim.gov.in")],
            [InlineKeyboardButton("🔙 Back", callback_data="csc")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=cert_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # Service-specific handlers
    async def handle_disaster_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle disaster management services"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        keyboard = [
            [InlineKeyboardButton("💰 Ex-gratia Assistance", callback_data="exgratia_apply")],
            [InlineKeyboardButton("🔍 Check Status", callback_data="status_check")],
            [InlineKeyboardButton("📝 Report Disaster", callback_data="disaster_report")],
            [InlineKeyboardButton("📋 Ex-gratia Norms", callback_data="exgratia_norms")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        service_card = await self.create_service_card('disaster_management', language)
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=f"{service_card.caption}\n\nSelect an option:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=f"{service_card.caption}\n\nSelect an option:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def handle_emergency_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle emergency services"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🚑 Ambulance (102)", callback_data="emergency_ambulance")],
            [InlineKeyboardButton("👮 Police (100)", callback_data="emergency_police")],
            [InlineKeyboardButton("🚒 Fire (101)", callback_data="emergency_fire")],
            [InlineKeyboardButton("👩 Women Helpline", callback_data="emergency_women")],
            [InlineKeyboardButton("⚠️ Suicide Prevention", callback_data="emergency_suicide")],
            [InlineKeyboardButton("🏥 Health Helpline", callback_data="emergency_health")],
            [InlineKeyboardButton("🚨 Report Disaster", callback_data="emergency_disaster")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        service_card = await self.create_service_card('emergency_services', language)
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=f"{service_card.caption}\n\nSelect emergency service:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=f"{service_card.caption}\n\nSelect emergency service:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def handle_tourism(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle tourism and homestay services"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Get unique places from homestay data
        places = self.homestay_df['place'].unique()
        
        keyboard = []
        for place in places:
            keyboard.append([InlineKeyboardButton(f"📍 {place}", callback_data=f"place_{place}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        service_card = await self.create_service_card('tourism', language)
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=f"{service_card.caption}\n\nSelect a destination:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=f"{service_card.caption}\n\nSelect a destination:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def handle_csc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Common Service Center services"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🔍 Find Nearest CSC", callback_data="find_csc")],
            [InlineKeyboardButton("📞 Contact Operators", callback_data="contact_operators")],
            [InlineKeyboardButton("📋 Check Services", callback_data="check_services")],
            [InlineKeyboardButton("📜 Certificate Applications", callback_data="certificate_apply")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        service_card = await self.create_service_card('csc', language)
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=f"{service_card.caption}\n\nSelect an option:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                text=f"{service_card.caption}\n\nSelect an option:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    # Detailed workflow implementations
    async def handle_exgratia_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start ex-gratia assistance application"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Initialize application state
        self._set_user_state(user_id, {
            'stage': 'name',
            'data': {},
            'language': language,
            'type': 'exgratia'
        })
        
        if language == 'hindi':
            message = """💰 **एक्स-ग्रेशिया सहायता आवेदन**

मैं आपका एक्स-ग्रेशिया सहायता आवेदन पूरा करने में मदद करूंगा।

👤 कृपया अपना पूरा नाम बताएं:
(आधिकारिक दस्तावेजों के अनुसार)

💡 टिप: किसी भी समय 'cancel' या 'रद्द करो' लिखकर मुख्य मेनू पर वापस जा सकते हैं।"""
        elif language == 'nepali':
            message = """💰 **एक्स-ग्रेसिया सहायता आवेदन**

म तपाईंको एक्स-ग्रेसिया सहायता आवेदन पूरा गर्न मद्दत गर्नेछु।

👤 कृपया आफ्नो पूरा नाम भन्नुहोस्:
(आधिकारिक कागजातअनुसार)

💡 सुझाव: कुनै पनि समयमा 'cancel' वा 'रद्द गर्नुहोस्' लेखेर मुख्य मेनूमा फर्कन सक्नुहुन्छ।"""
        else:
            message = """💰 **Ex-Gratia Assistance Application**

I'll help you complete your ex-gratia assistance application.

👤 Please provide your full name:
(As per official documents)

💡 Tip: Type 'cancel' or 'exit' anytime to return to main menu."""
        
        # Add cancel button
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_workflow")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_emergency_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service_type: str):
        """Handle specific emergency service"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Get emergency service data
        if service_type == 'ambulance':
            service_key = 'ambulance'
        elif service_type == 'police':
            service_key = 'police'
        elif service_type == 'fire':
            service_key = 'fire'
        elif service_type == 'women':
            service_key = 'women'
        elif service_type == 'suicide':
            service_key = 'suicide'
        elif service_type == 'health':
            service_key = 'health'
        else:
            service_key = 'disaster'
        
        # Get response from emergency data
        response_text = self.emergency_data.get(service_key, {}).get(language, "Service information not available")
        
        # Add emergency number to response text instead of button ( URLs don't work in Telegram)
        response_text += f"\n\n📞 **Emergency Contact:** {self.get_emergency_number(service_key)}"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Other Emergency", callback_data="emergency_services")],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    def get_emergency_number(self, service_type: str) -> str:
        """Get emergency contact number"""
        numbers = {
            'ambulance': '102',
            'police': '100',
            'fire': '101',
            'women': '1091',
            'suicide': '9152987821',
            'health': '104',
            'disaster': '1077'
        }
        return numbers.get(service_type, '100')

    async def handle_place_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, place: str):
        """Handle homestay place selection"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Filter homestays by place
        homestays = self.homestay_df[self.homestay_df['place'] == place]
        
        if homestays.empty:
            message = f"❌ No homestays found in {place}"
        else:
            if language == 'hindi':
                message = f"🏠 **{place} में होमस्टे**\n\n"
            elif language == 'nepali':
                message = f"🏠 **{place} मा होमस्टे**\n\n"
            else:
                message = f"🏠 **Homestays in {place}**\n\n"
            
            for _, row in homestays.iterrows():
                message += f"*{row['name']}*\n"
                message += f"⭐ Rating: {row['rating']}/5\n"
                message += f"💰 Price: ₹{row['price_per_night']}/night\n"
                message += f"📞 Contact: {row['contact']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🏔️ Search Another Place", callback_data="tourism")],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_csc_finder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle CSC finder functionality"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Initialize CSC search state
        self._set_user_state(user_id, {
            'stage': 'gpu',
            'data': {},
            'language': language,
            'type': 'csc'
        })
        
        if language == 'hindi':
            message = """🔍 **निकटतम CSC खोजें**

कृपया अपना GPU (ग्राम पंचायत इकाई) नंबर बताएं:

💡 टिप: 'cancel' लिखकर मुख्य मेनू पर वापस जा सकते हैं।"""
        elif language == 'nepali':
            message = """🔍 **नजिकको CSC खोज्नुहोस्**

कृपया आफ्नो GPU (ग्राम पंचायत इकाई) नम्बर भन्नुहोस्:

💡 सुझाव: 'cancel' लेखेर मुख्य मेनूमा फर्कन सक्नुहुन्छ।"""
        else:
            message = """🔍 **Find Nearest CSC**

Please provide your GPU (Gram Panchayat Unit) number:

💡 Tip: Type 'cancel' to return to main menu."""
        
        # Add cancel button
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_workflow")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_exgratia_norms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show ex-gratia assistance norms"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Load norms from file
        with open('data/info_opt1.txt', 'r', encoding='utf-8') as f:
            norms_text = f.read()
        
        keyboard = [
            [InlineKeyboardButton("💰 Apply Now", callback_data="exgratia_apply")],
            [InlineKeyboardButton("📋 Application Process", callback_data="application_process")],
            [InlineKeyboardButton("🔙 Back", callback_data="disaster_management")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=norms_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_application_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show application process information"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Load process from file
        with open('data/info_opt2.txt', 'r', encoding='utf-8') as f:
            process_text = f.read()
        
        keyboard = [
            [InlineKeyboardButton("💰 Apply Now", callback_data="exgratia_apply")],
            [InlineKeyboardButton("📋 Ex-gratia Norms", callback_data="exgratia_norms")],
            [InlineKeyboardButton("🔙 Back", callback_data="disaster_management")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=process_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_status_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle application status check"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Initialize status check state
        self._set_user_state(user_id, {
            'stage': 'application_id',
            'data': {},
            'language': language,
            'type': 'status'
        })
        
        if language == 'hindi':
            message = """🔍 **आवेदन स्थिति जांच**

कृपया अपना आवेदन आईडी दर्ज करें:
(उदाहरण: 24EXG12345)

💡 टिप: 'cancel' लिखकर मुख्य मेनू पर वापस जा सकते हैं।"""
        elif language == 'nepali':
            message = """🔍 **आवेदन स्थिति जाँच**

कृपया आफ्नो आवेदन आईडी प्रविष्ट गर्नुहोस्:
(उदाहरण: 24EXG12345)

💡 सुझाव: 'cancel' लेखेर मुख्य मेनूमा फर्कन सक्नुहुन्छ।"""
        else:
            message = """🔍 **Application Status Check**

Please enter your Application ID:
(Example: 24EXG12345)

💡 Tip: Type 'cancel' to return to main menu."""
        
        # Add cancel button
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_workflow")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_complaint_filing(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle complaint filing"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Initialize complaint state
        self._set_user_state(user_id, {
            'stage': 'name',
            'data': {},
            'language': language,
            'type': 'complaint'
        })
        
        if language == 'hindi':
            message = """📝 **शिकायत/गुनासो दर्ज करें**

मैं आपकी शिकायत दर्ज करने में मदद करूंगा।

👤 कृपया अपना पूरा नाम बताएं:

💡 टिप: 'cancel' लिखकर मुख्य मेनू पर वापस जा सकते हैं।"""
        elif language == 'nepali':
            message = """📝 **गुनासो दर्ता गर्नुहोस्**

म तपाईंको गुनासो दर्ता गर्न मद्दत गर्नेछु।

👤 कृपया आफ्नो पूरा नाम भन्नुहोस्:

💡 सुझाव: 'cancel' लेखेर मुख्य मेनूमा फर्कन सक्नुहुन्छ।"""
        else:
            message = """📝 **File a Complaint/Grievance**

I'll help you file your complaint.

👤 Please provide your full name:

💡 Tip: Type 'cancel' to return to main menu."""
        
        # Add cancel button
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_workflow")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

def main():
    """Main function to run the bot"""
    print("🚀 Starting Enhanced SmartGov Assistant Bot...")
    
    bot = SmartGovAssistantBot()
    application = Application.builder().token(bot.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message_handler))
    
    print("🤖 Enhanced SmartGov Assistant is running...")
    print("📱 Bot Link: https://t.me/smartgov_assistant_bot")
    print("✅ Ready to serve citizens!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 