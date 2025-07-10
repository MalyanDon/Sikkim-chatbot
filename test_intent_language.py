#!/usr/bin/env python3
"""
Comprehensive Test Script for Intent Classification and Language Detection
Tests across English, Hindi, and Nepali languages
"""

import asyncio
import aiohttp
import time

# Test cases for different intents and languages
TEST_CASES = {
    "GREETING": {
        "english": ["Hello", "Hi", "Hey", "Good morning"],
        "hindi": ["Namaste", "Namaskar", "Hello", "Hi"],
        "nepali": ["Namaste", "Namaskar", "Hello"]
    },
    "HELP": {
        "english": ["I need help", "Can you help me?", "Help me please"],
        "hindi": ["Madad chahiye", "Sahayata", "Help karo"],
        "nepali": ["Maddat chaincha", "Sahayata", "Help"]
    },
    "EXGRATIA_NORMS": {
        "english": ["What is ex gratia?", "How much money?", "Tell me about compensation"],
        "hindi": ["Ex gratia kya hai?", "Kitna paisa milta hai?", "Compensation ke baare mein bataiye"],
        "nepali": ["Ex gratia k ho?", "Kati paisa paincha?", "Compensation ko barema"]
    },
    "EXGRATIA_APPLY": {
        "english": ["My house got damaged in flood, I want to apply", "Apply for ex gratia", "House damaged by rain"],
        "hindi": ["Mera ghar flood mein tut gaya, apply karna hai", "Ex gratia ke liye apply karna hai", "Ghar barish mein kharab ho gaya"],
        "nepali": ["Mero ghar badhi le bigaareko, apply garna parcha", "Ex gratia apply garna", "Ghar paani le noksaan"]
    },
    "STATUS_CHECK": {
        "english": ["Check my application status", "Where is my application?", "Status check"],
        "hindi": ["Mera application ka status kya hai?", "Application kahan hai?", "Status check karo"],
        "nepali": ["Mero application ko status k cha?", "Application kaha cha?", "Status hernu"]
    }
}

# LLM configuration
LLM_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen2.5:3b"

async def test_language_detection(message):
    """Test language detection for a message"""
    prompt = f"""You are a language detection expert. Analyze this message and detect the language.

IMPORTANT: Many Hindi/Nepali speakers write in Roman letters (English alphabet) but the words are Hindi/Nepali.

Examples:
- "mujhe madad chaahiye" = HINDI (written in Roman letters)
- "mera status kya hai" = HINDI (written in Roman letters) 
- "hello how are you" = ENGLISH
- "namaste kaise ho" = HINDI/NEPALI (written in Roman letters)

Message to analyze: "{message}"

Look for Hindi/Nepali words like: mujhe, mera, kya, hai, chaahiye, status, madad, kaise, namaste, etc.

Respond with only ONE word:
- "hindi" if it's Hindi (including romanized Hindi)
- "nepali" if it's Nepali (including romanized Nepali)
- "english" if it's pure English

Response:"""

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
                    language = result.get("response", "").strip().lower()
                    
                    # Extract language
                    if 'hindi' in language:
                        return 'hindi'
                    elif 'nepali' in language:
                        return 'nepali'
                    else:
                        return 'english'
                else:
                    return "ERROR"
    except Exception as e:
        return f"ERROR: {e}"

async def test_intent_classification(message, language):
    """Test intent classification for a message"""
    lang_context = "English" if language == 'english' else "Hindi/Nepali"
    
    prompt = f"""You are an AI assistant for Sikkim government's disaster relief ex-gratia program. 

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

EXGRATIA_NORMS (information about ex-gratia):
- "What is ex gratia?" → exgratia_norms
- "Ex gratia ke baare mein bataiye" → exgratia_norms
- "Kitna paisa milta hai?" → exgratia_norms
- "What are the eligibility criteria?" → exgratia_norms

EXGRATIA_APPLY (actual application with damage):
- "My house got damaged in rain, I want to apply" → exgratia_apply
- "Mera ghar flood mein tut gaya, apply karna hai" → exgratia_apply
- "Crops destroyed by hail, need compensation" → exgratia_apply

OTHER (non-eligible):
- "Laptop broken" → other
- "Car tire damaged" → other

The user message is in {lang_context}.
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
                    valid_intents = ['greeting', 'status_check', 'application_procedure', 'exgratia_norms', 'exgratia_apply', 'help', 'other']
                    for valid_intent in valid_intents:
                        if valid_intent in intent:
                            return valid_intent
                    return "other"
                else:
                    return "ERROR"
    except Exception as e:
        return f"ERROR: {e}"

async def run_comprehensive_test():
    """Run comprehensive tests for all intents and languages"""
    print("🚀 COMPREHENSIVE INTENT & LANGUAGE DETECTION TEST")
    print("=" * 60)
    
    # Test LLM connection first
    print("🔗 Testing LLM connection...")
    test_result = await test_language_detection("Hello")
    if "ERROR" in str(test_result):
        print(f"❌ LLM Connection Failed: {test_result}")
        return
    else:
        print(f"✅ LLM Connected: Test detection = {test_result}")
    
    print("\n" + "=" * 60)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for expected_intent, languages in TEST_CASES.items():
        print(f"\n🎯 TESTING INTENT: {expected_intent}")
        print("-" * 40)
        
        for lang, messages in languages.items():
            print(f"\n📝 Language: {lang.upper()}")
            
            for message in messages:
                total_tests += 1
                
                # Test language detection
                detected_lang = await test_language_detection(message)
                
                # Test intent classification
                detected_intent = await test_intent_classification(message, detected_lang)
                
                # Check results
                lang_correct = detected_lang == lang
                intent_correct = detected_intent == expected_intent.lower()
                
                if lang_correct and intent_correct:
                    print(f"  ✅ '{message}' → Lang: {detected_lang} | Intent: {detected_intent}")
                    passed_tests += 1
                else:
                    status = "❌"
                    if not lang_correct:
                        status += f" Lang: Expected {lang}, Got {detected_lang}"
                    if not intent_correct:
                        status += f" Intent: Expected {expected_intent.lower()}, Got {detected_intent}"
                    
                    print(f"  {status}")
                    print(f"    Message: '{message}'")
                    failed_tests.append({
                        'message': message,
                        'expected_lang': lang,
                        'detected_lang': detected_lang,
                        'expected_intent': expected_intent.lower(),
                        'detected_intent': detected_intent
                    })
                
                # Small delay to avoid overwhelming the LLM
                await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
        print("-" * 40)
        for i, fail in enumerate(failed_tests, 1):
            print(f"{i}. '{fail['message']}'")
            print(f"   Expected: {fail['expected_lang']} | {fail['expected_intent']}")
            print(f"   Got:      {fail['detected_lang']} | {fail['detected_intent']}")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test()) 