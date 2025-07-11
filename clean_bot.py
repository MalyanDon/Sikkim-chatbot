#!/usr/bin/env python3
"""
Sikkim SmartGov Assistant Bot
"""
import asyncio
import aiohttp
import json
import logging
import pandas as pd
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import Config

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartGovAssistantBot:
    def __init__(self):
        self.BOT_TOKEN = Config.BOT_TOKEN
        self.LLM_ENDPOINT = "http://localhost:11434/api/generate"
        self.MODEL_NAME = "qwen2"
        self.user_states = {}
        self.user_languages = {}
        self._state_lock = threading.RLock()
        self._load_data()
        self._initialize_responses()
        logger.info("Bot initialized")

    def _load_data(self):
        with open('data/emergency_services_text_responses.json', 'r', encoding='utf-8') as f:
            self.emergency_data = json.load(f)
        self.homestay_df = pd.read_csv('data/homestays_by_place.csv')
        self.csc_df = pd.read_csv('data/csc_contacts.csv')
        self.status_df = pd.read_csv('data/status.csv')

    def _initialize_responses(self):
        self.responses = {
            'hindi': {'main_menu': "नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ?", 'cancel_msg': "प्रक्रिया रद्द की गई।"},
            'nepali': {'main_menu': "नमस्ते! म तपाईंलाई कसरी मद्दत गर्न सक्छु?", 'cancel_msg': "प्रक्रिया रद्द गरियो।"},
            'english': {'main_menu': "Hello! How can I help you?", 'cancel_msg': "Process cancelled."}
        }

    def _get_user_state(self, user_id):
        with self._state_lock:
            return self.user_states.get(user_id, {})

    def _set_user_state(self, user_id, state):
        with self._state_lock:
            self.user_states[user_id] = state

    def _clear_user_state(self, user_id):
        with self._state_lock:
            if user_id in self.user_states:
                del self.user_states[user_id]

    def _get_user_language(self, user_id):
        with self._state_lock:
            return self.user_languages.get(user_id, 'english')

    def _set_user_language(self, user_id, language):
        with self._state_lock:
            self.user_languages[user_id] = language

    async def get_intent_from_llm(self, text, lang):
        prompt = f"Intent for '{text}' in {lang}:"
        payload = {"model": self.MODEL_NAME, "prompt": prompt, "stream": False}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.LLM_ENDPOINT, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        intent = data.get('response', '').strip().lower()
                        return intent if intent in ['disaster_management', 'emergency_services', 'tourism', 'csc', 'language'] else 'unknown'
        except Exception as e:
            logger.error(f"LLM error: {e}")
        return 'unknown'

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._clear_user_state(update.effective_user.id)
        keyboard = [[InlineKeyboardButton("English", callback_data='lang_english'),
                     InlineKeyboardButton("हिन्दी", callback_data='lang_hindi'),
                     InlineKeyboardButton("नेपाली", callback_data='lang_nepali')]]
        await update.message.reply_text("Choose language:", reply_markup=InlineKeyboardMarkup(keyboard))

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        message_text = update.message.text
        lang = self._get_user_language(user_id)

        if "cancel" in message_text.lower():
            self._clear_user_state(user_id)
            await update.message.reply_text(self.responses[lang]['cancel_msg'])
            await self.show_main_menu(update, context)
            return

        user_state = self._get_user_state(user_id)
        if user_state:
            # Handle workflow input here if needed
            pass
        else:
            intent = await self.get_intent_from_llm(message_text, lang)
            if intent == 'tourism':
                await self.handle_tourism(update, context)
            else:
                await self.show_main_menu(update, context)

    async def handle_tourism(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = self._get_user_language(update.effective_user.id)
        text = "Select a place:" if lang == 'english' else "एक जगह चुनें:"
        keyboard = [[InlineKeyboardButton("Gangtok", callback_data='place_Gangtok')],
                    [InlineKeyboardButton("Pelling", callback_data='place_Pelling')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

    async def handle_place_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        place = query.data.split('_')[1]
        homestays = self.homestay_df[self.homestay_df['Place'] == place]
        
        if homestays.empty:
            await query.edit_message_text("No homestays found.")
            return

        message = ""
        for _, row in homestays.iterrows():
            message += f"*{row['HomestayName']}*\nRating: {row['Rating']}/5\nPrice: ₹{row['PricePerNight']}\n\n"

        await query.edit_message_text(message, parse_mode='Markdown')

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        if query.data.startswith('lang_'):
            lang = query.data.split('_')[1]
            self._set_user_language(user_id, lang)
            await self.show_main_menu(update, context)
        elif query.data.startswith('place_'):
            await self.handle_place_selection(update, context)
        elif query.data == 'tourism':
            await self.handle_tourism(update, context)
        else:
            await self.show_main_menu(update, context)

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        lang = self._get_user_language(update.effective_user.id)
        keyboard = [[InlineKeyboardButton("Tourism", callback_data='tourism')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = self.responses[lang]['main_menu']
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

    def run(self):
        app = Application.builder().token(self.BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        app.add_handler(CallbackQueryHandler(self.callback_query_handler))
        app.run_polling()

if __name__ == '__main__':
    bot = SmartGovAssistantBot()
    bot.run() 