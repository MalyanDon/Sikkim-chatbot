#!/usr/bin/env python3
"""
Enhanced SmartGov Assistant Bot with LLM Integration
"""
import asyncio
import aiohttp
import json
import logging
import pandas as pd
import threading
import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import Config
from google_sheets_service import GoogleSheetsService
from datetime import datetime
import time
import random

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SmartGovBot:
    def __init__(self):
        """Initialize the bot"""
        # Initialize state management
        self._user_states = {}
        self._state_lock = threading.Lock()
        
        # Initialize bot configuration
        self.config = Config()
        self.application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        
        # Initialize Google Sheets service
        self.sheets_service = None
        if self.config.GOOGLE_SHEETS_ENABLED and self.config.GOOGLE_SHEETS_SPREADSHEET_ID:
            try:
                self.sheets_service = GoogleSheetsService(
                    self.config.GOOGLE_SHEETS_CREDENTIALS_FILE,
                    self.config.GOOGLE_SHEETS_SPREADSHEET_ID
                )
                logger.info("✅ Google Sheets service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Google Sheets service: {str(e)}")
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_error_handler(self.handle_error)
        
        logger.info("✅ Bot initialized with state management and handlers")

    def _get_state(self, user_id: int) -> dict:
        """Get user state"""
        with self._state_lock:
            return self._user_states.get(user_id, {})

    def _set_state(self, user_id: int, state: dict):
        """Set user state"""
        with self._state_lock:
            self._user_states[user_id] = state

    def _clear_state(self, user_id: int):
        """Clear user state"""
        with self._state_lock:
            if user_id in self._user_states:
                del self._user_states[user_id]

    async def detect_language(self, text: str) -> str:
        """Detect language using Ollama"""
        try:
            prompt = f"""You are a language detector. Given the text, detect if it's in English or Hindi.
            Text: {text}
            Respond with ONLY 'english' or 'hindi', nothing else."""
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "qwen", "prompt": prompt, "stream": False}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        detected = result['response'].strip().lower()
                        logger.info(f"[LLM] Language detected: {detected}")
                        return detected
                    else:
                        logger.error(f"[LLM] Language detection failed: {response.status}")
                        return 'english'
        except Exception as e:
            logger.error(f"[LLM] Language detection error: {str(e)}")
            return 'english'

    async def get_intent(self, text: str, lang: str) -> str:
        """Get intent using Ollama"""
        try:
            prompt = f"""You are an intent classifier for a government services chatbot.
            Classify the text into: ex_gratia, check_status, relief_norms, or unknown.
            
            Text: {text}
            Language: {lang}
            
            Respond with ONLY the intent name."""
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "qwen", "prompt": prompt, "stream": False}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        intent = result['response'].strip().lower()
                        logger.info(f"[LLM] Intent detected: {intent}")
                        return intent
                    else:
                        logger.error(f"[LLM] Intent detection failed: {response.status}")
                        return 'unknown'
        except Exception as e:
            logger.error(f"[LLM] Intent detection error: {str(e)}")
            return 'unknown'

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        self._clear_state(user_id)
        
        text = """🏛️ *Welcome to SmartGov Assistant* 🏛️
        
I can help you with:
• Ex-gratia assistance
• Application status
• Relief norms
• And more...

Send me a message in English or Hindi!"""

        await update.message.reply_text(text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        try:
            user_id = update.effective_user.id
            text = update.message.text
            logger.info(f"[MSG] From {user_id}: {text}")
            
            # Get current state
            state = self._get_state(user_id)
            
            if state and state.get("workflow"):
                # Handle ongoing conversation
                await self.handle_conversation(update, context, state)
            else:
                # New conversation - detect language and intent
                logger.info(f"[LLM] Processing text: {text}")
                lang = await self.detect_language(text)
                logger.info(f"[LLM] Language detected: {lang}")
                
                intent = await self.get_intent(text, lang)
                logger.info(f"[LLM] Intent detected: {intent}")
                
                # Log complaint if intent is unknown (could be a complaint)
                if intent == "unknown" and self.sheets_service:
                    user_name = update.effective_user.first_name or "Unknown"
                    self.sheets_service.log_complaint(
                        user_id, user_name, text, "General Query", lang
                    )
                
                # Set state with detected info
                self._set_state(user_id, {
                    "language": lang,
                    "intent": intent,
                    "workflow": intent if intent != "unknown" else None
                })
                
                # Handle the intent
                await self.handle_intent(update, context, intent)
                
        except Exception as e:
            logger.error(f"[ERROR] Message handling: {str(e)}")
            await update.message.reply_text(
                "Sorry, I encountered an error. Please try again.",
                parse_mode='Markdown'
            )

    async def handle_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
        """Handle ongoing conversation based on state"""
        workflow = state.get("workflow")
        
        if workflow == "ex_gratia":
            await self.handle_ex_gratia_flow(update, context, state)
        elif workflow == "check_status":
            await self.handle_status_check_flow(update, context, state)
        elif workflow == "relief_norms":
            await self.handle_relief_norms_flow(update, context, state)
        else:
            await self.handle_unknown(update, context)

    async def handle_ex_gratia_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
        """Handle ex-gratia application flow"""
        user_id = update.effective_user.id
        text = update.message.text
        step = state.get("step", "name")
        
        if step == "name":
            # Store name and ask for phone
            state["name"] = text
            state["step"] = "phone"
            self._set_state(user_id, state)
            await update.message.reply_text("Please enter your phone number:", parse_mode='Markdown')
            
        elif step == "phone":
            # Store phone and ask for address
            state["phone"] = text
            state["step"] = "address"
            self._set_state(user_id, state)
            await update.message.reply_text("Please enter your address:", parse_mode='Markdown')
            
        elif step == "address":
            # Store address and ask for damage type
            state["address"] = text
            state["step"] = "damage_type"
            self._set_state(user_id, state)
            
            keyboard = [
                [InlineKeyboardButton("🏠 House Damage", callback_data="damage_house")],
                [InlineKeyboardButton("🌾 Crop Damage", callback_data="damage_crop")],
                [InlineKeyboardButton("🐄 Livestock Loss", callback_data="damage_livestock")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("What type of damage did you suffer?", reply_markup=reply_markup, parse_mode='Markdown')
            
        elif step == "damage_description":
            # Store damage description and complete application
            state["damage_description"] = text
            self._set_state(user_id, state)
            
            # Log to Google Sheets
            if self.sheets_service:
                user_name = update.effective_user.first_name or "Unknown"
                application_data = {
                    'name': state.get('name', ''),
                    'phone': state.get('phone', ''),
                    'address': state.get('address', ''),
                    'damage_type': state.get('damage_type', ''),
                    'damage_description': text
                }
                self.sheets_service.log_ex_gratia_application(
                    user_id, user_name, application_data, 
                    state.get('language', 'english')
                )
            
            # Generate application ID
            application_id = f"EXG{user_id}{int(time.time())}"
            
            await update.message.reply_text(
                f"✅ *Application Submitted Successfully!*\n\n"
                f"📋 **Application ID:** {application_id}\n"
                f"👤 **Name:** {state.get('name', '')}\n"
                f"📞 **Phone:** {state.get('phone', '')}\n"
                f"🏠 **Address:** {state.get('address', '')}\n"
                f"💥 **Damage Type:** {state.get('damage_type', '')}\n\n"
                f"Your application has been logged and will be processed within 7-10 working days.",
                parse_mode='Markdown'
            )
            
            self._clear_state(user_id)

    async def handle_status_check_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
        """Handle status check flow"""
        user_id = update.effective_user.id
        text = update.message.text
        application_id = text.strip()
        
        # Log status check to Google Sheets
        if self.sheets_service:
            user_name = update.effective_user.first_name or "Unknown"
            status_result = "Application not found"  # Default result
            
            # Here you would typically check against your database
            # For now, we'll simulate a status check
            if application_id.startswith("EXG"):
                status_result = "Under Review"
            elif application_id.startswith("CERT"):
                status_result = "Certificate Ready"
            else:
                status_result = "Invalid Application ID"
            
            self.sheets_service.log_status_check(
                user_id, user_name, application_id, 
                status_result, state.get('language', 'english')
            )
        
        await update.message.reply_text(
            f"📋 **Status Check Result**\n\n"
            f"🔍 **Application ID:** {application_id}\n"
            f"📊 **Status:** Under Review\n"
            f"⏰ **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Your application is being processed. You'll receive updates via SMS.",
            parse_mode='Markdown'
        )
        
        self._clear_state(user_id)

    async def handle_relief_norms_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
        """Handle relief norms flow"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Log as certificate query if it's a specific question
        if self.sheets_service and any(keyword in text.lower() for keyword in ['certificate', 'document', 'paper']):
            user_name = update.effective_user.first_name or "Unknown"
            self.sheets_service.log_certificate_query(
                user_id, user_name, text, "Relief Norms", 
                state.get('language', 'english'), "Information provided"
            )
        
        await update.message.reply_text(
            "📋 **Relief Norms Information**\n\n"
            "🏠 **House Damage:** Up to ₹25,000\n"
            "🌾 **Crop Loss:** Up to ₹15,000 per hectare\n"
            "🐄 **Livestock Loss:** Up to ₹15,000 per animal\n"
            "🏥 **Medical Expenses:** Up to ₹10,000\n\n"
            "For more details, contact your local administration office.",
            parse_mode='Markdown'
        )
        
        self._clear_state(user_id)

    async def handle_intent(self, update: Update, context: ContextTypes.DEFAULT_TYPE, intent: str):
        """Handle detected intent"""
        if intent == "ex_gratia":
            text = """*Ex-Gratia Assistance* 📝
            
You may be eligible if you've suffered losses due to:
• Natural disasters
• Crop damage
• Property damage

Would you like to apply?"""
            
            keyboard = [
                [InlineKeyboardButton("✅ Yes, Apply Now", callback_data="apply_ex_gratia")],
                [InlineKeyboardButton("❌ No, Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif intent == "check_status":
            await update.message.reply_text(
                "Please enter your application ID to check status:",
                parse_mode='Markdown'
            )
            
        elif intent == "relief_norms":
            text = """*Relief Norms* ℹ️

The Government provides:
• House Damage: Up to ₹25,000
• Crop Loss: Up to ₹15,000
• Livestock Loss: Up to ₹15,000

Need more details?"""
            
            keyboard = [
                [InlineKeyboardButton("📝 Apply Now", callback_data="apply_ex_gratia")],
                [InlineKeyboardButton("❌ Close", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        else:
            await self.handle_unknown(update, context)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "apply_ex_gratia":
            user_id = update.effective_user.id
            self._set_state(user_id, {
                "workflow": "ex_gratia",
                "step": "name"
            })
            await query.message.reply_text("Please enter your full name:", parse_mode='Markdown')
            
        elif query.data.startswith("damage_"):
            user_id = update.effective_user.id
            state = self._get_state(user_id)
            
            # Map callback data to damage type
            damage_map = {
                "damage_house": "House Damage",
                "damage_crop": "Crop Damage", 
                "damage_livestock": "Livestock Loss"
            }
            
            damage_type = damage_map.get(query.data, "Unknown")
            state["damage_type"] = damage_type
            state["step"] = "damage_description"
            self._set_state(user_id, state)
            
            await query.message.reply_text(
                f"Please describe the {damage_type.lower()} in detail:",
                parse_mode='Markdown'
            )
            
        elif query.data == "cancel":
            user_id = update.effective_user.id
            self._clear_state(user_id)
            await query.message.reply_text("Operation cancelled. How else can I help?", parse_mode='Markdown')

    async def handle_unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown intents"""
        text = """I'm not sure what you're asking for. I can help with:

• Ex-gratia assistance
• Application status
• Relief norms

Please try rephrasing your request."""
        
        await update.message.reply_text(text, parse_mode='Markdown')

    async def handle_error(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"[ERROR] {context.error}", exc_info=context.error)
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again.",
                parse_mode='Markdown'
            )

    def run(self):
        """Start the bot"""
        logger.info("🚀 Starting SmartGov Bot with LLM...")
        print("🚀 Starting SmartGov Bot...")
        print("🤖 LLM Integration: Active")
        if self.sheets_service:
            print("📊 Google Sheets Integration: Active")
        else:
            print("📊 Google Sheets Integration: Disabled")
        print("✅ Ready to serve!")
        self.application.run_polling()

if __name__ == "__main__":
    # Create and run bot
    bot = SmartGovBot()
    bot.run() 