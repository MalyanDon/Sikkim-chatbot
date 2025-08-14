#!/usr/bin/env python3
"""
Simple script to run the Sikkim Chatbot
"""
import asyncio
from comprehensive_smartgov_bot import SajiloSewakBot

def main():
    """Main function to run the bot"""
    print("🚀 Starting Sikkim Chatbot...")
    
    try:
        # Initialize the bot
        bot = SajiloSewakBot()
        print("✅ Bot initialized successfully")
        
        # Run the bot
        print("🔄 Starting bot...")
        bot.run()
        
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

