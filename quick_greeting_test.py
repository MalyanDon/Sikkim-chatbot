#!/usr/bin/env python3
"""
Quick test for greeting intent classification
"""

import asyncio
import aiohttp

LLM_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen2.5:3b"

async def test_greeting_intent(message):
    """Test if greeting messages are correctly classified"""
    
    prompt = f"""You are an AI assistant for Sikkim government's disaster relief ex-gratia program. 

Classify this user message into exactly ONE of these intents:
- greeting: for hello, hi, namaste, hey, good morning (simple greetings only)
- help: for explicit help requests like "I need help", "madad chahiye", "sahayata"
- other: for anything else

CRITICAL EXAMPLES:

GREETING (simple social interaction):
- "Hello" → greeting
- "Hi" → greeting  
- "Namaste" → greeting
- "Hey" → greeting
- "Good morning" → greeting

HELP (explicit help request):
- "I need help" → help
- "Can you help me?" → help
- "Madad chahiye" → help
- "Sahayata" → help

User message: "{message}"

Respond with ONLY the intent name (one word):"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                LLM_URL,
                json={
                    "model": LLM_MODEL, 
                    "prompt": prompt,
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    intent = result.get("response", "").strip().lower()
                    
                    # Extract valid intent
                    if 'greeting' in intent:
                        return 'greeting'
                    elif 'help' in intent:
                        return 'help'
                    else:
                        return 'other'
                else:
                    return "ERROR"
    except Exception as e:
        return f"ERROR: {e}"

async def run_greeting_test():
    """Test greeting classification"""
    print("🎯 QUICK GREETING INTENT TEST")
    print("=" * 40)
    
    test_cases = [
        ("Hello", "greeting"),
        ("Hi", "greeting"),
        ("Hey", "greeting"),
        ("Namaste", "greeting"),
        ("Good morning", "greeting"),
        ("I need help", "help"),
        ("Can you help me?", "help"),
        ("Madad chahiye", "help"),
        ("Sahayata", "help")
    ]
    
    for message, expected in test_cases:
        result = await test_greeting_intent(message)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' → Expected: {expected}, Got: {result}")
        await asyncio.sleep(0.3)
    
    print("\n🏁 Quick test completed!")

if __name__ == "__main__":
    asyncio.run(run_greeting_test()) 