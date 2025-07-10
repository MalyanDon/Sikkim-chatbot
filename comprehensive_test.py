#!/usr/bin/env python3
"""
Comprehensive test for both rule-based and LLM functionality
Tests all the critical cases we've been working on
"""

import sys
import os
import asyncio
import aiohttp
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

async def test_llm_connection():
    """Test if LLM is working properly"""
    print("🤖 TESTING LLM CONNECTION")
    print("=" * 40)
    
    try:
        llm_url = Config.OLLAMA_API_URL
        llm_model = Config.LLM_MODEL
        
        print(f"LLM URL: {llm_url}")
        print(f"LLM Model: {llm_model}")
        
        # Test basic LLM connection
        async with aiohttp.ClientSession() as session:
            async with session.post(
                llm_url,
                json={
                    "model": llm_model, 
                    "prompt": "Hello, are you working?",
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ LLM Connected Successfully")
                    print(f"Response: {result.get('response', 'No response')[:100]}")
                    return True
                else:
                    print(f"❌ LLM Connection Failed (Status: {response.status})")
                    return False
                    
    except Exception as e:
        print(f"❌ LLM Connection Error: {e}")
        return False

async def test_llm_language_detection():
    """Test LLM language detection specifically"""
    print("\n🌐 TESTING LLM LANGUAGE DETECTION")
    print("=" * 50)
    
    test_cases = [
        ("Hello", "english"),
        ("Mereko ex gratia apply krna hain", "hindi"),
        ("Ma ex gratia apply garna chahanchhu", "nepali"),
        ("Abhishek", "english"),
        ("Namaste", "hindi"),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    try:
        llm_url = Config.OLLAMA_API_URL
        llm_model = Config.LLM_MODEL
        
        for message, expected_lang in test_cases:
            try:
                prompt = f"""Detect the language of this text. Respond with exactly one word: "english", "hindi", or "nepali".

Text: "{message}"

Language:"""

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        llm_url,
                        json={
                            "model": llm_model, 
                            "prompt": prompt,
                            "stream": False
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            detected_lang = result.get("response", "").strip().lower()
                            
                            # Extract valid language
                            if "english" in detected_lang:
                                detected_lang = "english"
                            elif "hindi" in detected_lang:
                                detected_lang = "hindi"
                            elif "nepali" in detected_lang:
                                detected_lang = "nepali"
                            
                            status = "✅" if detected_lang == expected_lang else "❌"
                            print(f"{status} '{message}' → {detected_lang} (expected: {expected_lang})")
                            
                            if detected_lang == expected_lang:
                                success_count += 1
                        else:
                            print(f"❌ '{message}' → LLM Error (Status: {response.status})")
                            
            except Exception as e:
                print(f"❌ '{message}' → Error: {e}")
    
    except Exception as e:
        print(f"❌ LLM Language Detection Error: {e}")
    
    success_rate = (success_count / total_tests) * 100
    print(f"\n📊 LLM Language Detection: {success_count}/{total_tests} ({success_rate:.1f}%)")
    return success_rate >= 70

async def test_llm_intent_classification():
    """Test LLM intent classification specifically"""
    print("\n🎯 TESTING LLM INTENT CLASSIFICATION")
    print("=" * 50)
    
    test_cases = [
        ("Hello", "greeting"),
        ("Hi", "greeting"), 
        ("Namaste", "greeting"),
        ("Madad chahiye", "help"),
        ("Help me", "help"),
        ("I want to apply for ex gratia", "exgratia_apply"),
        ("Check my application status", "status_check"),
        ("How to apply?", "application_procedure"),
        ("What is ex gratia?", "exgratia_norms"),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    try:
        llm_url = Config.OLLAMA_API_URL
        llm_model = Config.LLM_MODEL
        
        for message, expected_intent in test_cases:
            try:
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

User message: "{message}"

Respond with ONLY the intent name (one word):"""

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        llm_url,
                        json={
                            "model": llm_model, 
                            "prompt": prompt,
                            "stream": False
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            intent = result.get("response", "").strip().lower()
                            
                            # Extract valid intent
                            valid_intents = ['greeting', 'status_check', 'application_procedure', 'exgratia_norms', 'exgratia_apply', 'help', 'other']
                            final_intent = "other"  # default
                            
                            # First check for exact match
                            if intent in valid_intents:
                                final_intent = intent
                            else:
                                # Then check for partial match
                                for valid_intent in valid_intents:
                                    if valid_intent in intent:
                                        final_intent = valid_intent
                                        break
                            
                            status = "✅" if final_intent == expected_intent else "❌"
                            print(f"{status} '{message}' → {final_intent} (expected: {expected_intent})")
                            
                            if final_intent == expected_intent:
                                success_count += 1
                        else:
                            print(f"❌ '{message}' → LLM Error (Status: {response.status})")
                            
            except Exception as e:
                print(f"❌ '{message}' → Error: {e}")
    
    except Exception as e:
        print(f"❌ LLM Intent Classification Error: {e}")
    
    success_rate = (success_count / total_tests) * 100
    print(f"\n📊 LLM Intent Classification: {success_count}/{total_tests} ({success_rate:.1f}%)")
    return success_rate >= 70

def test_rule_based_classification():
    """Test our improved rule-based classification"""
    print("\n🔧 TESTING RULE-BASED CLASSIFICATION")
    print("=" * 50)
    
    # Import the minimal test class we created
    from minimal_test import MinimalBotTest
    
    bot = MinimalBotTest()
    
    test_cases = [
        # Critical greeting tests (main issue we fixed)
        ("Hello", "greeting", "english"),
        ("Hi", "greeting", "english"),
        ("hello", "greeting", "english"),
        ("hi", "greeting", "english"),
        ("Namaste", "greeting", "english"),
        
        # Help classification tests
        ("Madad chahiye", "help", "hindi"),
        ("Help me", "help", "english"),
        ("I need help", "help", "english"),
        
        # Other tests
        ("Random text", "other", "english"),
        ("Some name", "other", "english"),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for message, expected_intent, language in test_cases:
        try:
            intent = bot.get_intent_rule_based(message, language)
            status = "✅" if intent == expected_intent else "❌"
            print(f"{status} '{message}' ({language}) → {intent} (expected: {expected_intent})")
            if intent == expected_intent:
                success_count += 1
        except Exception as e:
            print(f"❌ '{message}' → ERROR: {e}")
    
    success_rate = (success_count / total_tests) * 100
    print(f"\n📊 Rule-Based Classification: {success_count}/{total_tests} ({success_rate:.1f}%)")
    return success_rate >= 85

def test_language_fallback():
    """Test our improved language fallback detection"""
    print("\n🌐 TESTING LANGUAGE FALLBACK DETECTION")
    print("=" * 50)
    
    from minimal_test import MinimalBotTest
    
    bot = MinimalBotTest()
    
    test_cases = [
        # Hindi phrases
        ("Mereko ex gratia apply krna hain", "hindi"),
        ("Mujhe madad chahiye", "hindi"),
        ("Kya process hai", "hindi"),
        
        # Nepali phrases
        ("Ma ex gratia apply garna chahanchhu", "nepali"),
        ("Mero ghar bigreko cha", "nepali"),
        ("Kati paisa milcha", "nepali"),
        
        # English/unclear
        ("Abhishek", "english"),
        ("123456", "english"),
        ("Random text", "english"),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for message, expected_lang in test_cases:
        try:
            detected_lang = bot.detect_language_fallback(message)
            status = "✅" if detected_lang == expected_lang else "❌"
            print(f"{status} '{message}' → {detected_lang} (expected: {expected_lang})")
            if detected_lang == expected_lang:
                success_count += 1
        except Exception as e:
            print(f"❌ '{message}' → ERROR: {e}")
    
    success_rate = (success_count / total_tests) * 100
    print(f"\n📊 Language Fallback: {success_count}/{total_tests} ({success_rate:.1f}%)")
    return success_rate >= 80

async def comprehensive_test():
    """Run all comprehensive tests"""
    print("🚀 COMPREHENSIVE CHATBOT TESTING")
    print("=" * 60)
    print("Testing all components: LLM Connection, Language Detection, Intent Classification, and Rule-Based Fallbacks")
    print("=" * 60)
    
    results = {}
    
    # Test 1: LLM Connection
    results['llm_connection'] = await test_llm_connection()
    
    # Test 2: LLM Language Detection
    if results['llm_connection']:
        results['llm_language'] = await test_llm_language_detection()
    else:
        results['llm_language'] = False
        print("⚠️ Skipping LLM Language Detection (LLM not connected)")
    
    # Test 3: LLM Intent Classification
    if results['llm_connection']:
        results['llm_intent'] = await test_llm_intent_classification()
    else:
        results['llm_intent'] = False
        print("⚠️ Skipping LLM Intent Classification (LLM not connected)")
    
    # Test 4: Rule-Based Classification (Always works)
    results['rule_based'] = test_rule_based_classification()
    
    # Test 5: Language Fallback (Always works)
    results['language_fallback'] = test_language_fallback()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    overall_success = (total_passed / total_tests) * 100
    print(f"\n🎯 OVERALL SUCCESS RATE: {total_passed}/{total_tests} ({overall_success:.1f}%)")
    
    if overall_success >= 80:
        print("🎉 EXCELLENT! The chatbot is working well!")
    elif overall_success >= 60:
        print("✅ GOOD! Most components are working, minor issues remain.")
    else:
        print("⚠️ NEEDS ATTENTION: Several components need improvement.")
    
    # Specific recommendations
    print("\n💡 RECOMMENDATIONS:")
    if not results['llm_connection']:
        print("• Check LLM server (Ollama) is running on localhost:11434")
    if not results['llm_intent']:
        print("• LLM intent classification needs prompt improvements")
    if not results['rule_based']:
        print("• Rule-based classification patterns need refinement")
    
    return overall_success >= 70

if __name__ == "__main__":
    success = asyncio.run(comprehensive_test())
    sys.exit(0 if success else 1) 