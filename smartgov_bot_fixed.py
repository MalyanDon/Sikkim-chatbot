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
        print("✅ Ready to serve!")
        self.application.run_polling()

if __name__ == "__main__":
    # Create and run bot
    bot = SmartGovBot()
    bot.run() 