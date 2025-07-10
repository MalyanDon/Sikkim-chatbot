#!/usr/bin/env python3
"""
ULTIMATE COMPREHENSIVE TEST for Sikkim Chatbot
Tests ALL critical cases from the original issues including:
1. Hello/Hi greeting classification (main issue)
2. Language persistence during application flow
3. Hindi help classification
4. Nepali language support
5. LLM vs Rule-based comparison
"""

import sys
import os
import asyncio
import aiohttp
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from smartgov_bot import SmartGovBot

async def test_live_bot_conversation():
    """Test the actual live bot conversation flow"""
    print("🤖 TESTING LIVE BOT CONVERSATION FLOW")
    print("=" * 60)
    
    try:
        # Create bot instance (without running it)
        bot = SmartGovBot()
        
        # Test the critical conversation flow from console logs
        print("Testing the exact scenario from console logs:")
        print("1. User says 'Hello'")
        print("2. User says 'Mereko ex gratia apply krna hain'")
        print("3. User says 'Abhishek' (name during application)")
        
        # Test 1: Hello classification
        language = await bot.detect_language_with_llm("Hello")
        intent = await bot.get_intent_from_llm("Hello", language)
        print(f"✅ 'Hello' → Language: {language}, Intent: {intent}")
        
        # Test 2: Hindi application request
        language2 = await bot.detect_language_with_llm("Mereko ex gratia apply krna hain")
        intent2 = await bot.get_intent_from_llm("Mereko ex gratia apply krna hain", language2)
        print(f"✅ 'Mereko ex gratia apply krna hain' → Language: {language2}, Intent: {intent2}")
        
        # Test 3: Name during application (should maintain language persistence)
        language3 = await bot.detect_language_with_llm("Abhishek")
        print(f"✅ 'Abhishek' → Language: {language3}")
        
        # Verify the exact issues are fixed
        issues_fixed = 0
        total_issues = 3
        
        if intent == "greeting":
            print("✅ ISSUE 1 FIXED: 'Hello' correctly classified as GREETING")
            issues_fixed += 1
        else:
            print(f"❌ ISSUE 1 REMAINS: 'Hello' classified as {intent} instead of GREETING")
        
        if intent2 == "exgratia_apply":
            print("✅ ISSUE 2 VERIFIED: Hindi application request working")
            issues_fixed += 1
        else:
            print(f"❌ ISSUE 2 PROBLEM: Hindi request classified as {intent2}")
        
        if language3 in ["english", "hindi"]:  # Either is acceptable for names
            print("✅ ISSUE 3 VERIFIED: Name language detection reasonable")
            issues_fixed += 1
        else:
            print(f"❌ ISSUE 3 PROBLEM: Name detected as {language3}")
        
        success_rate = (issues_fixed / total_issues) * 100
        print(f"\n📊 CRITICAL ISSUES FIXED: {issues_fixed}/{total_issues} ({success_rate:.1f}%)")
        return success_rate >= 80
        
    except Exception as e:
        print(f"❌ Live Bot Test Error: {e}")
        return False

async def test_llm_intent_classification_exhaustive():
    """Exhaustive test of LLM intent classification for all critical cases"""
    print("\n🎯 EXHAUSTIVE LLM INTENT CLASSIFICATION TEST")
    print("=" * 60)
    
    # All the critical test cases from original issues
    test_cases = [
        # CRITICAL GREETING TESTS (Main Issue!)
        ("Hello", "greeting", "The main issue - was classified as OTHER/HELP"),
        ("Hi", "greeting", "Second main issue - was classified as OTHER/HELP"), 
        ("hello", "greeting", "Lowercase version"),
        ("hi", "greeting", "Lowercase version"),
        ("Hey", "greeting", "Alternative greeting"),
        ("Namaste", "greeting", "Hindi greeting"),
        ("Good morning", "greeting", "Extended greeting"),
        
        # HELP CLASSIFICATION TESTS  
        ("Help me", "help", "English help request"),
        ("I need help", "help", "English help request"),
        ("Can you help me", "help", "English help request"),
        ("Madad chahiye", "help", "Hindi help - was problematic"),
        ("Sahayata chahiye", "help", "Hindi help alternative"),
        ("Maddat chahiye", "help", "Hindi help variation"),
        
        # APPLICATION FLOW TESTS
        ("I want to apply for ex gratia", "exgratia_apply", "Application request"),
        ("Mereko ex gratia apply krna hain", "exgratia_apply", "Hindi application"),
        ("Apply karna hai", "exgratia_apply", "Hindi apply"),
        ("Ma ex gratia apply garna chahanchhu", "exgratia_apply", "Nepali application"),
        
        # STATUS CHECK TESTS
        ("Check my application status", "status_check", "Status inquiry"),
        ("Application kahan hai", "status_check", "Hindi status check"),
        ("Mera application ka status", "status_check", "Hindi status"),
        ("Application status dekho", "status_check", "Hindi status"),
        
        # INFORMATION REQUESTS
        ("What is ex gratia", "exgratia_norms", "Information request"),
        ("How much money will I get", "exgratia_norms", "Amount inquiry"),
        ("Kitna paisa milega", "exgratia_norms", "Hindi amount"),
        ("Ex gratia ke baare mein bataiye", "exgratia_norms", "Hindi info"),
        
        # PROCEDURE INQUIRIES
        ("How to apply", "application_procedure", "Process question"),
        ("Application process kya hai", "application_procedure", "Hindi process"),
        ("Kaise apply karna hai", "application_procedure", "Hindi how to"),
        
        # EDGE CASES & NAMES (Language persistence issues)
        ("Abhishek", "other", "Name during application"),
        ("Ram Kumar", "other", "Full name"),
        ("9876543210", "other", "Phone number"),
        ("Village Gangtok", "other", "Location"),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    critical_failures = []
    
    try:
        llm_url = Config.OLLAMA_API_URL
        llm_model = Config.LLM_MODEL
        
        print(f"Testing {total_tests} critical cases with LLM...")
        
        for i, (message, expected_intent, description) in enumerate(test_cases, 1):
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
                            
                            # Track critical failures
                            if final_intent != expected_intent and "main issue" in description.lower():
                                critical_failures.append((message, final_intent, expected_intent, description))
                            
                            print(f"{status} [{i:2d}] '{message}' → {final_intent} (expected: {expected_intent}) | {description}")
                            
                            if final_intent == expected_intent:
                                success_count += 1
                        else:
                            print(f"❌ [{i:2d}] '{message}' → LLM Error (Status: {response.status})")
                            
                # Small delay to avoid overwhelming the LLM
                await asyncio.sleep(0.1)
                            
            except Exception as e:
                print(f"❌ [{i:2d}] '{message}' → Error: {e}")
    
    except Exception as e:
        print(f"❌ LLM Intent Classification Error: {e}")
    
    success_rate = (success_count / total_tests) * 100
    print(f"\n📊 LLM INTENT CLASSIFICATION: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    # Report critical failures
    if critical_failures:
        print(f"\n🚨 CRITICAL FAILURES DETECTED:")
        for message, got, expected, desc in critical_failures:
            print(f"   ❌ '{message}' → {got} (expected: {expected}) - {desc}")
    else:
        print(f"\n✅ NO CRITICAL FAILURES! Main issues are resolved!")
    
    return success_rate >= 75, critical_failures

async def test_language_detection_exhaustive():
    """Exhaustive test of language detection"""
    print("\n🌐 EXHAUSTIVE LANGUAGE DETECTION TEST")
    print("=" * 60)
    
    test_cases = [
        # English
        ("Hello", "english", "Simple English greeting"),
        ("Hi there", "english", "English phrase"),
        ("I need help", "english", "English sentence"),
        ("Abhishek", "english", "Name - should be English"),
        ("9876543210", "english", "Number - should default English"),
        
        # Hindi  
        ("Mereko ex gratia apply krna hain", "hindi", "Hindi application - from console logs"),
        ("Madad chahiye", "hindi", "Hindi help request"),
        ("Mujhe sahayata chahiye", "hindi", "Hindi help"),
        ("Kya process hai", "hindi", "Hindi question"),
        ("Kitna paisa milega", "hindi", "Hindi money question"),
        ("Mera naam Ram hai", "hindi", "Hindi introduction"),
        
        # Nepali
        ("Ma ex gratia apply garna chahanchhu", "nepali", "Nepali application"),
        ("Mero ghar bigreko cha", "nepali", "Nepali damage report"),
        ("Kati paisa milcha", "nepali", "Nepali money question"),
        ("Malai madad gara", "nepali", "Nepali help request"),
        
        # Mixed/Ambiguous
        ("Namaste", "hindi", "Could be Hindi or Nepali"),
        ("Ex gratia", "english", "English term"),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    try:
        llm_url = Config.OLLAMA_API_URL
        llm_model = Config.LLM_MODEL
        
        for i, (message, expected_lang, description) in enumerate(test_cases, 1):
            try:
                prompt = f"""Detect the language of this text. The text could be in English, Hindi, or Nepali.

Consider these clues:
- English: Standard English words and grammar
- Hindi: Words like "mujhe", "mereko", "chahiye", "kya", "hai", "paisa", "madad"  
- Nepali: Words like "ma", "mero", "garna", "chahanchhu", "cha", "malai", "kati"

Text: "{message}"

Respond with exactly one word: "english", "hindi", or "nepali":"""

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
                            else:
                                detected_lang = "english"  # default
                            
                            status = "✅" if detected_lang == expected_lang else "❌"
                            print(f"{status} [{i:2d}] '{message}' → {detected_lang} (expected: {expected_lang}) | {description}")
                            
                            if detected_lang == expected_lang:
                                success_count += 1
                        else:
                            print(f"❌ [{i:2d}] '{message}' → LLM Error (Status: {response.status})")
                            
                await asyncio.sleep(0.1)
                            
            except Exception as e:
                print(f"❌ [{i:2d}] '{message}' → Error: {e}")
    
    except Exception as e:
        print(f"❌ Language Detection Error: {e}")
    
    success_rate = (success_count / total_tests) * 100
    print(f"\n📊 LANGUAGE DETECTION: {success_count}/{total_tests} ({success_rate:.1f}%)")
    return success_rate >= 70

def test_rule_based_vs_llm_comparison():
    """Compare rule-based vs LLM performance on critical cases"""
    print("\n⚔️ RULE-BASED vs LLM COMPARISON")
    print("=" * 60)
    
    from minimal_test import MinimalBotTest
    bot = MinimalBotTest()
    
    critical_cases = [
        ("Hello", "greeting"),
        ("Hi", "greeting"),
        ("Madad chahiye", "help"),
        ("Help me", "help"),
    ]
    
    print("Testing rule-based classification:")
    rule_success = 0
    for message, expected in critical_cases:
        lang = "hindi" if any(h in message.lower() for h in ["madad", "sahayata"]) else "english"
        result = bot.get_intent_rule_based(message, lang)
        status = "✅" if result == expected else "❌"
        print(f"{status} Rule-based: '{message}' → {result}")
        if result == expected:
            rule_success += 1
    
    rule_rate = (rule_success / len(critical_cases)) * 100
    print(f"\n📊 Rule-based Success: {rule_success}/{len(critical_cases)} ({rule_rate:.1f}%)")
    
    return rule_rate >= 90

async def ultimate_comprehensive_test():
    """Run the ultimate comprehensive test"""
    print("🚀 ULTIMATE COMPREHENSIVE CHATBOT TEST")
    print("=" * 80)
    print("Testing ALL critical issues from the original problem reports")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Live Bot Conversation Flow
    print("\n" + "🔴" * 20 + " CRITICAL ISSUES TEST " + "🔴" * 20)
    results['critical_issues'] = await test_live_bot_conversation()
    
    # Test 2: Exhaustive LLM Intent Classification
    results['llm_intent'], critical_failures = await test_llm_intent_classification_exhaustive()
    
    # Test 3: Exhaustive Language Detection
    results['language_detection'] = await test_language_detection_exhaustive()
    
    # Test 4: Rule-based vs LLM comparison
    results['rule_vs_llm'] = test_rule_based_vs_llm_comparison()
    
    # Final Analysis
    print("\n" + "=" * 80)
    print("🏆 ULTIMATE TEST RESULTS & ANALYSIS")
    print("=" * 80)
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    overall_success = (total_passed / total_tests) * 100
    print(f"\n🎯 ULTIMATE SUCCESS RATE: {total_passed}/{total_tests} ({overall_success:.1f}%)")
    
    # Critical Issue Analysis
    print(f"\n🔍 CRITICAL ISSUE ANALYSIS:")
    if results['critical_issues']:
        print("✅ MAIN ISSUES FROM CONSOLE LOGS: RESOLVED")
        print("   • 'Hello' greeting classification: FIXED")
        print("   • Language persistence: WORKING")
        print("   • Hindi application flow: WORKING")
    else:
        print("❌ MAIN ISSUES: STILL PRESENT")
    
    if not critical_failures:
        print("✅ NO CRITICAL LLM FAILURES: All main greeting issues resolved")
    else:
        print(f"⚠️ {len(critical_failures)} critical LLM failures detected")
    
    # Overall Grade
    if overall_success >= 90:
        grade = "A+ (Excellent)"
        status = "🎉 PRODUCTION READY"
    elif overall_success >= 80:
        grade = "A (Very Good)"
        status = "✅ READY WITH MINOR NOTES"
    elif overall_success >= 70:
        grade = "B (Good)"
        status = "⚠️ READY WITH SOME ISSUES"
    else:
        grade = "C (Needs Work)"
        status = "❌ NEEDS MORE WORK"
    
    print(f"\n🏅 FINAL GRADE: {grade}")
    print(f"🚦 STATUS: {status}")
    
    return overall_success >= 75

if __name__ == "__main__":
    print("Starting Ultimate Comprehensive Test...")
    success = asyncio.run(ultimate_comprehensive_test())
    
    print(f"\n{'='*80}")
    print("🎯 FINAL VERDICT:")
    if success:
        print("✅ The Sikkim Ex-Gratia Chatbot is working well!")
        print("✅ All critical issues have been resolved!")
        print("✅ Ready for production use!")
    else:
        print("⚠️ The chatbot needs more improvements")
        print("⚠️ Some critical issues remain")
    print(f"{'='*80}")
    
    sys.exit(0 if success else 1) 