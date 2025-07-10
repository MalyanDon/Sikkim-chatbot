#!/usr/bin/env python3
"""
Final Comprehensive Test Suite - All Fixes Validation
Tests greeting classification, language detection, and intent classification
"""

import asyncio
import aiohttp

LLM_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen2.5:3b"

# Critical test cases based on identified issues
CRITICAL_TESTS = {
    "GREETING_CLASSIFICATION": [
        ("Hello", "greeting"),
        ("Hi", "greeting"), 
        ("Hey", "greeting"),
        ("Namaste", "greeting"),
        ("Good morning", "greeting")
    ],
    "HELP_VS_GREETING": [
        ("I need help", "help"),
        ("Can you help me?", "help"),
        ("Madad chahiye", "help"),
        ("Hello", "greeting"),  # Should NOT be help
        ("Hi", "greeting")       # Should NOT be help
    ],
    "STATUS_VS_PROCEDURE": [
        ("Check my application status", "status_check"),
        ("Where is my application?", "status_check"),
        ("Application kahan hai?", "status_check"),
        ("How to apply?", "application_procedure"),
        ("Application process kya hai?", "application_procedure"),
        ("Kaise apply karna hai?", "application_procedure")
    ],
    "LANGUAGE_DETECTION_HINDI": [
        ("Mereko ex gratia apply krna hain", "hindi"),
        ("Madad chahiye", "hindi"),
        ("Sahayata", "hindi"),
        ("Kitna paisa milta hai?", "hindi")
    ],
    "LANGUAGE_DETECTION_NEPALI": [
        ("Maddat chaincha", "nepali"),
        ("Kati paisa paincha?", "nepali"),
        ("Mero ghar badhi le bigaareko", "nepali"),
        ("Garna parcha", "nepali")
    ]
}

async def test_intent_classification(message, expected_intent):
    """Test intent classification with improved prompt"""
    
    prompt = f"""You are an AI assistant for Sikkim government's disaster relief ex-gratia program. 

IMPORTANT: Ex-gratia assistance is ONLY for natural disaster-related damages (floods, landslides, earthquakes, storms, hailstorms, etc.) affecting:
- Houses/buildings
- Agricultural crops  
- Livestock (animals)
- Death due to natural disasters

Classify this user message into exactly ONE of these intents:
- greeting: for hello, hi, namaste, hey, good morning (simple greetings only)
- help: for explicit help requests like "I need help", "madad chahiye", "sahayata"
- status_check: for checking EXISTING application status, tracking submitted applications
- application_procedure: for asking HOW TO apply, application process, steps to apply
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

STATUS_CHECK (checking existing application):
- "Check my application status" → status_check
- "Where is my application?" → status_check
- "Application kahan hai?" → status_check
- "Mera application ka status" → status_check

APPLICATION_PROCEDURE (how to apply):
- "How to apply?" → application_procedure
- "Application process kya hai?" → application_procedure
- "Kaise apply karna hai?" → application_procedure

The user message is in English.
User message: "{message}"

Respond with ONLY the intent name (one word):"""

    async with aiohttp.ClientSession() as session:
        async with session.post(
            LLM_URL,
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False}
        ) as response:
            if response.status == 200:
                result = await response.json()
                intent = result.get("response", "").strip().lower()
                
                # Extract valid intent
                valid_intents = ['greeting', 'status_check', 'application_procedure', 'exgratia_norms', 'exgratia_apply', 'help', 'other']
                final_intent = "other"
                
                if intent in valid_intents:
                    final_intent = intent
                else:
                    for valid_intent in valid_intents:
                        if valid_intent in intent:
                            final_intent = valid_intent
                            break
                
                return final_intent
            else:
                return "error"

async def test_language_detection(message, expected_language):
    """Test language detection"""
    
    prompt = f"""Detect the language of this text. Respond with exactly one word:
- english (for English text)
- hindi (for Hindi/Hinglish text) 
- nepali (for Nepali text)

Text: "{message}"

Language:"""

    async with aiohttp.ClientSession() as session:
        async with session.post(
            LLM_URL,
            json={"model": LLM_MODEL, "prompt": prompt, "stream": False}
        ) as response:
            if response.status == 200:
                result = await response.json()
                language = result.get("response", "").strip().lower()
                return language
            else:
                return "error"

async def run_comprehensive_test():
    """Run all critical tests"""
    
    print("🚀 FINAL COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    all_passed = 0
    all_failed = 0
    
    for test_category, test_cases in CRITICAL_TESTS.items():
        print(f"\n🎯 TESTING: {test_category}")
        print("-" * 40)
        
        category_passed = 0
        category_failed = 0
        
        for message, expected in test_cases:
            if test_category.startswith("LANGUAGE_DETECTION"):
                result = await test_language_detection(message, expected)
                test_type = "Language"
            else:
                result = await test_intent_classification(message, expected)
                test_type = "Intent"
            
            if result == expected:
                print(f"  ✅ '{message}' → {test_type}: {result}")
                category_passed += 1
                all_passed += 1
            else:
                print(f"  ❌ '{message}' → Expected: {expected}, Got: {result}")
                category_failed += 1
                all_failed += 1
        
        success_rate = (category_passed / (category_passed + category_failed)) * 100
        print(f"  📊 {test_category}: {category_passed}/{category_passed + category_failed} passed ({success_rate:.1f}%)")
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    
    total_tests = all_passed + all_failed
    overall_success = (all_passed / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {all_passed}")
    print(f"Failed: {all_failed}")
    print(f"Success Rate: {overall_success:.1f}%")
    
    if overall_success >= 90:
        print("🎉 EXCELLENT! All critical issues resolved!")
    elif overall_success >= 80:
        print("✅ GOOD! Most issues resolved, minor improvements needed")
    elif overall_success >= 70:
        print("⚠️ MODERATE: Several issues remain")
    else:
        print("❌ POOR: Major issues still present")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test()) 