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

    def _get_user_state(self, user_id: int) -> dict:
        """Safely get user state with locking"""
        with self._state_lock:
            return self.user_states.get(user_id, {})

    def _set_user_state(self, user_id: int, state: dict):
        """Safely set user state with locking"""
        with self._state_lock:
            self.user_states[user_id] = state
            logger.info(f"🔒 STATE UPDATE: User {user_id} → {state.get('type', 'unknown')} stage {state.get('stage', 'unknown')}")

    def _clear_user_state(self, user_id: int):
        """Safely clear user state with locking"""
        with self._state_lock:
            if user_id in self.user_states:
                del self.user_states[user_id]
                logger.info(f"🧹 STATE CLEARED: User {user_id}")

    def get_user_state(self, user_id: int) -> dict:
        """Get user state"""
        return self._get_user_state(user_id)

    def set_user_state(self, user_id: int, state: dict):
        """Set user state"""
        self._set_user_state(user_id, state)

    def clear_user_state(self, user_id: int):
        """Clear user state"""
        self._clear_user_state(user_id)

    def _get_user_language(self, user_id: int) -> str:
        """Safely get user language with locking"""
        with self._state_lock:
            return self.user_languages.get(user_id, 'english')

    def _set_user_language(self, user_id: int, language: str):
        """Safely set user language with locking"""
        with self._state_lock:
            self.user_languages[user_id] = language
            logger.info(f"🌐 LANGUAGE SET: User {user_id} → {language.upper()}")

    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        return self._get_user_language(user_id)

    def set_user_language(self, user_id: int, language: str):
        """Set user's preferred language"""
        self._set_user_language(user_id, language)

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
        """Initialize multilingual responses"""
        self.responses = {
            'hindi': {
                'main_menu': "नमस्ते! मैं स्मार्टगॉव असिस्टेंट हूँ। मैं आपकी कैसे मदद कर सकता हूँ?",
                'cancel_msg': "❌ प्रक्रिया रद्द की गई। मुख्य मेनू पर वापस जा रहे हैं..."
            },
            'nepali': {
                'main_menu': "नमस्ते! म स्मार्टगभ असिस्टेन्ट हुँ। म तपाईंलाई कसरी मद्दत गर्न सक्छु?",
                'cancel_msg': "❌ प्रक्रिया रद्द गरियो। मुख्य मेनूमा फर्कदै..."
            },
            'english': {
                'main_menu': "Hello! I'm the SmartGov Assistant. How can I help you?",
                'cancel_msg': "❌ Process cancelled. Returning to main menu..."
            }
        }

    async def get_intent_from_llm(self, message: str, language: str) -> str:
        """Get intent from LLM"""
        prompt = f"""
        Analyze the user's message and determine the intent.
        The possible intents are: 'disaster_management', 'emergency_services', 'tourism', 'csc', 'language', 'unknown'.
        User message: "{message}"
        Language: {language}
        Intent:
        """
        
        payload = {
            "model": self.MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.LLM_ENDPOINT, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        intent = data.get('response', '').strip().lower()
                        if intent in ['disaster_management', 'emergency_services', 'tourism', 'csc', 'language']:
                            return intent
        except Exception as e:
            logger.error(f"Error getting intent from LLM: {e}")
        return 'unknown'

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
            self.clear_user_state(user_id)
            
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
        user_state = self.get_user_state(user_id)
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
        workflow_type = state['type']
        
        if workflow_type == 'exgratia':
            await self.handle_exgratia_workflow(update, context, message, state)
        elif workflow_type == 'status':
            await self.handle_status_workflow(update, context, message, state)
        elif workflow_type == 'csc':
            await self.handle_csc_workflow(update, context, message, state)
        elif workflow_type == 'complaint':
            await self.handle_complaint_workflow(update, context, message, state)

    async def handle_place_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, place: str):
        """Handle homestay place selection"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        # Filter homestays by place
        homestays = self.homestay_df[self.homestay_df['Place'] == place]
        
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
                message += f"*{row['HomestayName']}*\n"
                message += f"⭐ Rating: {row['Rating']}/5\n"
                message += f"💰 Price: ₹{row['PricePerNight']}/night\n"
                message += f"📞 Contact: {row['ContactNumber']}\n\n"
        
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

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        self.clear_user_state(user_id)
        
        keyboard = [
            [InlineKeyboardButton("English 🇬🇧", callback_data="lang_english")],
            [InlineKeyboardButton("हिन्दी 🇮🇳", callback_data="lang_hindi")],
            [InlineKeyboardButton("नेपाली 🇳🇵", callback_data="lang_nepali")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Welcome to the SmartGov Assistant! Please select your language:",
            reply_markup=reply_markup
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data.startswith("lang_"):
            language = data.split("_")[1]
            self.set_user_language(user_id, language)
            await self.show_main_menu(update, context)
        elif data == "back_main":
            await self.show_main_menu(update, context)
        elif data == "disaster_management":
            await self.handle_disaster_management(update, context)
        elif data == "emergency_services":
            await self.handle_emergency_services(update, context)
        elif data == "tourism":
            await self.handle_tourism(update, context)
        elif data == "csc":
            await self.handle_csc(update, context)
        elif data.startswith("place_"):
            place = data.split("_")[1]
            await self.handle_place_selection(update, context, place)
        elif data.startswith("emergency_"):
            service = data.split("_")[1]
            await self.handle_emergency_response(update, context, service)

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the main menu"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        if language == 'hindi':
            text = "मुख्य मेनू:"
            keyboard = [
                [InlineKeyboardButton("आपदा प्रबंधन 🌪️", callback_data="disaster_management")],
                [InlineKeyboardButton("आपातकालीन सेवाएं 🚑", callback_data="emergency_services")],
                [InlineKeyboardButton("पर्यटन और होमस्टे 🏔️", callback_data="tourism")],
                [InlineKeyboardButton("सामान्य सेवा केंद्र (CSC) 💻", callback_data="csc")],
                [InlineKeyboardButton("भाषा बदलें 🌐", callback_data="lang_english")]
            ]
        elif language == 'nepali':
            text = "मुख्य मेनु:"
            keyboard = [
                [InlineKeyboardButton("विपद् व्यवस्थापन 🌪️", callback_data="disaster_management")],
                [InlineKeyboardButton("आपतकालीन सेवाहरू 🚑", callback_data="emergency_services")],
                [InlineKeyboardButton("पर्यटन र होमस्टे 🏔️", callback_data="tourism")],
                [InlineKeyboardButton("साझा सेवा केन्द्र (CSC) 💻", callback_data="csc")],
                [InlineKeyboardButton("भाषा परिवर्तन गर्नुहोस् 🌐", callback_data="lang_english")]
            ]
        else:
            text = "Main Menu:"
            keyboard = [
                [InlineKeyboardButton("Disaster Management 🌪️", callback_data="disaster_management")],
                [InlineKeyboardButton("Emergency Services 🚑", callback_data="emergency_services")],
                [InlineKeyboardButton("Tourism & Homestays 🏔️", callback_data="tourism")],
                [InlineKeyboardButton("Common Service Centers (CSC) 💻", callback_data="csc")],
                [InlineKeyboardButton("Change Language 🌐", callback_data="lang_english")]
            ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

    async def handle_disaster_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle disaster management"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        if language == 'hindi':
            text = "आपदा प्रबंधन सेवाएं:"
            keyboard = [
                [InlineKeyboardButton("एक्स-ग्रेशिया सहायता के लिए आवेदन करें", callback_data="exgratia_apply")],
                [InlineKeyboardButton("आवेदन की स्थिति जांचें", callback_data="status_check")],
                [InlineKeyboardButton("आपदा की रिपोर्ट करें", callback_data="report_disaster")],
                [InlineKeyboardButton("🔙 मुख्य मेनू", callback_data="back_main")]
            ]
        elif language == 'nepali':
            text = "विपद् व्यवस्थापन सेवाहरू:"
            keyboard = [
                [InlineKeyboardButton("एक्स-ग्रेशिया सहायताको लागि आवेदन दिनुहोस्", callback_data="exgratia_apply")],
                [InlineKeyboardButton("आवेदन स्थिति जाँच गर्नुहोस्", callback_data="status_check")],
                [InlineKeyboardButton("विपद् रिपोर्ट गर्नुहोस्", callback_data="report_disaster")],
                [InlineKeyboardButton("🔙 मुख्य मेनु", callback_data="back_main")]
            ]
        else:
            text = "Disaster Management Services:"
            keyboard = [
                [InlineKeyboardButton("Apply for Ex-gratia Assistance", callback_data="exgratia_apply")],
                [InlineKeyboardButton("Check Application Status", callback_data="status_check")],
                [InlineKeyboardButton("Report a Disaster", callback_data="report_disaster")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

    async def handle_emergency_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle emergency services"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        if language == 'hindi':
            text = "आपातकालीन सेवाएं:"
            keyboard = [
                [InlineKeyboardButton("पुलिस 🚓", callback_data="emergency_police")],
                [InlineKeyboardButton("एम्बुलेंस 🚑", callback_data="emergency_ambulance")],
                [InlineKeyboardButton("फायर ब्रिगेड 🚒", callback_data="emergency_fire")],
                [InlineKeyboardButton("आपदा प्रतिक्रिया बल 🌪️", callback_data="emergency_disaster")],
                [InlineKeyboardButton("🔙 मुख्य मेनू", callback_data="back_main")]
            ]
        elif language == 'nepali':
            text = "आपतकालीन सेवाहरू:"
            keyboard = [
                [InlineKeyboardButton("पुलिस 🚓", callback_data="emergency_police")],
                [InlineKeyboardButton("एम्बुलेन्स 🚑", callback_data="emergency_ambulance")],
                [InlineKeyboardButton("दमकल 🚒", callback_data="emergency_fire")],
                [InlineKeyboardButton("विपद् प्रतिक्रिया बल 🌪️", callback_data="emergency_disaster")],
                [InlineKeyboardButton("🔙 मुख्य मेनु", callback_data="back_main")]
            ]
        else:
            text = "Emergency Services:"
            keyboard = [
                [InlineKeyboardButton("Police 🚓", callback_data="emergency_police")],
                [InlineKeyboardButton("Ambulance 🚑", callback_data="emergency_ambulance")],
                [InlineKeyboardButton("Fire Brigade 🚒", callback_data="emergency_fire")],
                [InlineKeyboardButton("Disaster Response Force 🌪️", callback_data="emergency_disaster")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

    async def handle_tourism(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle tourism"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        if language == 'hindi':
            text = "पर्यटन और होमस्टे:"
            keyboard = [
                [InlineKeyboardButton("गंगटोक", callback_data="place_Gangtok")],
                [InlineKeyboardButton("पेलिंग", callback_data="place_Pelling")],
                [InlineKeyboardButton("लाचुंग", callback_data="place_Lachung")],
                [InlineKeyboardButton("🔙 मुख्य मेनू", callback_data="back_main")]
            ]
        elif language == 'nepali':
            text = "पर्यटन र होमस्टे:"
            keyboard = [
                [InlineKeyboardButton("गान्तोक", callback_data="place_Gangtok")],
                [InlineKeyboardButton("पेलिङ", callback_data="place_Pelling")],
                [InlineKeyboardButton("लाचुङ", callback_data="place_Lachung")],
                [InlineKeyboardButton("🔙 मुख्य मेनु", callback_data="back_main")]
            ]
        else:
            text = "Tourism & Homestays:"
            keyboard = [
                [InlineKeyboardButton("Gangtok", callback_data="place_Gangtok")],
                [InlineKeyboardButton("Pelling", callback_data="place_Pelling")],
                [InlineKeyboardButton("Lachung", callback_data="place_Lachung")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

    async def handle_csc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle CSC"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        if language == 'hindi':
            text = "सामान्य सेवा केंद्र (CSC):"
            keyboard = [
                [InlineKeyboardButton("निकटतम सीएससी खोजें", callback_data="csc_finder")],
                [InlineKeyboardButton("सेवाओं की सूची", callback_data="csc_services")],
                [InlineKeyboardButton("🔙 मुख्य मेनू", callback_data="back_main")]
            ]
        elif language == 'nepali':
            text = "साझा सेवा केन्द्र (CSC):"
            keyboard = [
                [InlineKeyboardButton("नजिकको सीएससी खोज्नुहोस्", callback_data="csc_finder")],
                [InlineKeyboardButton("सेवाहरूको सूची", callback_data="csc_services")],
                [InlineKeyboardButton("🔙 मुख्य मेनु", callback_data="back_main")]
            ]
        else:
            text = "Common Service Centers (CSC):"
            keyboard = [
                [InlineKeyboardButton("Find Nearest CSC", callback_data="csc_finder")],
                [InlineKeyboardButton("List of Services", callback_data="csc_services")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
            
    def run(self):
        """Run the bot"""
        async def main():
            app = Application.builder().token(self.BOT_TOKEN).build()

            # Command handlers
            app.add_handler(CommandHandler("start", self.start_command))

            # Message handlers
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))

            # Callback query handlers
            app.add_handler(CallbackQueryHandler(self.handle_callback_query))

            print("🚀 Starting Enhanced SmartGov Assistant Bot...")
            logger.info("🤖 Enhanced SmartGov Assistant is running...")
            
            # Initialize the bot
            await app.initialize()
            
            print(f"📱 Bot Link: https://t.me/{app.bot.username}")
            print("✅ Ready to serve citizens!")
            
            # Start the bot
            await app.run_polling()

        asyncio.run(main())

if __name__ == '__main__':
    bot = SmartGovAssistantBot()
    bot.run() 