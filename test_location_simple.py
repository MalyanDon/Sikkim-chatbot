#!/usr/bin/env python3
"""
Simple test to verify Telegram location sharing works
"""
import asyncio
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleLocationTest:
    def __init__(self):
        self.token = "7641958089:AAH2UW5H0EX9pGfE6wZZaURCpkyMHtJK8zw"  # Your bot token
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command - request location immediately"""
        logger.info(f"📍 [TEST] Start command from user {update.effective_user.id}")
        
        # Create location request keyboard
        keyboard = [
            [KeyboardButton("📍 Share My Location", request_location=True)],
            [KeyboardButton("❌ Cancel")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "📍 **Location Test**\n\nPlease share your location to test if it works:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location message"""
        user_id = update.effective_user.id
        location = update.message.location
        
        logger.info(f"📍 [TEST] Location received from user {user_id}")
        logger.info(f"📍 [TEST] Location object: {location}")
        logger.info(f"📍 [TEST] Location type: {type(location)}")
        
        if location:
            logger.info(f"📍 [TEST] Latitude: {location.latitude}")
            logger.info(f"📍 [TEST] Longitude: {location.longitude}")
            
            # Remove keyboard
            remove_keyboard = ReplyKeyboardRemove()
            
            await update.message.reply_text(
                f"✅ **Location Captured Successfully!**\n\n"
                f"📍 **Coordinates**: {location.latitude:.6f}, {location.longitude:.6f}\n"
                f"👤 **User ID**: {user_id}\n"
                f"📱 **User**: {update.effective_user.first_name}",
                reply_markup=remove_keyboard,
                parse_mode='Markdown'
            )
            
            logger.info(f"📍 [SUCCESS] Location test completed for user {user_id}")
        else:
            await update.message.reply_text("❌ No location received")
            logger.error(f"📍 [ERROR] No location object received from user {user_id}")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        logger.info(f"📍 [TEST] Text message from user {user_id}: {message_text}")
        
        if message_text == "❌ Cancel":
            remove_keyboard = ReplyKeyboardRemove()
            await update.message.reply_text(
                "❌ Location test cancelled",
                reply_markup=remove_keyboard
            )
        else:
            await update.message.reply_text(
                f"📝 You sent: {message_text}\n\nUse /start to test location sharing."
            )
    
    async def handle_other(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle other message types"""
        user_id = update.effective_user.id
        logger.info(f"📍 [TEST] Other message type from user {user_id}: {type(update.message)}")
        await update.message.reply_text("Please use /start to test location sharing.")
    
    def run(self):
        """Run the test bot"""
        # Create application
        application = Application.builder().token(self.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.LOCATION, self.handle_location))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        application.add_handler(MessageHandler(filters.ALL, self.handle_other))
        
        # Start the bot
        logger.info("📍 [TEST] Starting location test bot...")
        application.run_polling()

if __name__ == "__main__":
    test_bot = SimpleLocationTest()
    test_bot.run() 