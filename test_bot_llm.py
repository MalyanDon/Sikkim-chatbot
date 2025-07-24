#!/usr/bin/env python3
"""
Test script to check LLM functionality within the bot
"""
import asyncio
from comprehensive_smartgov_bot import SmartGovAssistantBot

async def test_bot_llm():
    """Test LLM functionality within the bot"""
    print("🧪 Testing Bot LLM Functionality")
    print("=" * 40)
    
    try:
        # Initialize bot
        bot = SmartGovAssistantBot()
        print("✅ Bot initialized successfully")
        
        # Test 1: Intent classification
        print("\n1. Testing intent classification...")
        test_messages = [
            ("Hello", "english"),
            ("I need ambulance", "english"),
            ("File complaint", "english"),
            ("नमस्ते", "hindi"),
            ("मुझे एम्बुलेंस चाहिए", "hindi"),
            ("शिकायत दर्ज करें", "hindi")
        ]
        
        for message, lang in test_messages:
            try:
                intent = await bot.get_intent_from_llm(message, lang)
                print(f"   ✅ '{message}' → {intent}")
            except Exception as e:
                print(f"   ❌ '{message}' → Error: {str(e)}")
        
        # Test 2: Language detection
        print("\n2. Testing language detection...")
        test_texts = [
            "Hello, how are you?",
            "नमस्ते, कैसे हो आप?",
            "नमस्कार, तपाईं कसरी हुनुहुन्छ?"
        ]
        
        for text in test_texts:
            try:
                detected_lang = await bot.detect_language(text)
                print(f"   ✅ '{text}' → {detected_lang}")
            except Exception as e:
                print(f"   ❌ '{text}' → Error: {str(e)}")
        
        print("\n🎉 Bot LLM functionality test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing bot LLM: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bot_llm()) 