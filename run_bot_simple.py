#!/usr/bin/env python3
"""
Simple script to run the Sikkim Chatbot directly
"""
import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from comprehensive_smartgov_bot import SajiloSewakBot
from telegram import Update

def main():
    """Main function to run the bot"""
    print("🚀 Starting Sikkim Chatbot...")
    
    try:
        # Initialize the bot
        bot = SajiloSewakBot()
        print("✅ Bot initialized successfully")
        
        # Create application manually
        application = Application.builder().token(bot.BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("language", bot.language_command))
        application.add_handler(CommandHandler("status", bot.handle_status_command))
        
        # Add handler for photo messages
        application.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo_message))
        
        # Add handler for location messages
        application.add_handler(MessageHandler(filters.LOCATION, bot.message_handler))
        
        # Add handler for text messages
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message_handler))
        
        application.add_handler(CallbackQueryHandler(bot.callback_handler))
        
        # Add error handler
        application.add_error_handler(bot.error_handler)
        
        # Start the bot
        print("🔄 Starting bot...")
        print("Ready to serve citizens!")
        print("Press Ctrl+C to stop the bot")
        
        # Run the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

