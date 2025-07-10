#!/usr/bin/env python3
"""
Focused test for 'Hi' intent classification issue
"""

import asyncio
import aiohttp

async def test_hi_classification():
    """Test why 'Hi' is being classified as 'help' instead of 'greeting'"""
    
    llm_url = "http://localhost:11434/api/generate"
    
    prompt = """You are an AI assistant for Sikkim government's disaster relief ex-gratia program. 

IMPORTANT: Ex-gratia assistance is ONLY for natural disaster-related damages (floods, landslides, earthquakes, storms, hailstorms, etc.) affecting:
- Houses/buildings
- Agricultural crops  
- Livestock (animals)
- Death due to natural disasters

Classify this user message into exactly ONE of these intents:
- greeting: for hello, hi, namaste, hey, good morning (simple greetings only)
- help: for explicit help requests like "I need help", "madad chahiye", "sahayata"
- status_check: for checking application status, tracking
- application_procedure: for how to apply, application process
- exgratia_norms: for asking ABOUT ex-gratia (what is, how much money, eligibility, rules)
- exgratia_apply: ONLY when user wants to APPLY and mentions actual disaster damage
- other: for anything else including non-disaster damages

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

The user message is in English.
User message: "Hi"

Respond with ONLY the intent name (one word):"""

    async with aiohttp.ClientSession() as session:
        async with session.post(
            llm_url,
            json={"model": "qwen2.5:3b", "prompt": prompt, "stream": False}
        ) as response:
            if response.status == 200:
                result = await response.json()
                intent = result.get("response", "").strip().lower()
                print(f"🔍 RAW LLM RESPONSE: '{intent}'")
                
                # Test the validation logic
                valid_intents = ['greeting', 'status_check', 'application_procedure', 'exgratia_norms', 'exgratia_apply', 'help', 'other']
                final_intent = "other"  # default
                
                # First check for exact match
                if intent in valid_intents:
                    final_intent = intent
                    print(f"✅ EXACT MATCH: {intent} → {final_intent}")
                else:
                    # Then check for partial match
                    for valid_intent in valid_intents:
                        if valid_intent in intent:
                            final_intent = valid_intent
                            print(f"✅ PARTIAL MATCH: {intent} contains {valid_intent} → {final_intent}")
                            break
                    
                    if final_intent == "other":
                        print(f"❌ NO MATCH FOUND: '{intent}' → defaulting to 'other'")
                
                print(f"🎯 FINAL RESULT: 'Hi' → {final_intent}")
            else:
                print(f"❌ LLM Request Failed: Status {response.status}")

if __name__ == "__main__":
    asyncio.run(test_hi_classification()) 