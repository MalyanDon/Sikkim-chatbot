#!/usr/bin/env python3
"""
Working script to run the Sikkim Chatbot
"""
import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from comprehensive_smartgov_bot import SajiloSewakBot
from telegram import Update

def main():
    """Main function to run the bot"""
    # Disable unnecessary logging
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
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
        application.add_handler(MessageHandler(filters.LOCATION, bot.message_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message_handler))
        application.add_handler(CallbackQueryHandler(bot.callback_handler))
        application.add_error_handler(bot.error_handler)
        
        # Start the bot
        print("🔄 Starting bot...")
        print("Bot is running! Press Ctrl+C to stop")
        
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