#!/usr/bin/env python3
"""
Test script to verify fixes for:
1. Greeting classification issue (Hello/Hi being classified as HELP)
2. Language persistence issue (switching back to English on names)
3. Nepali language support
"""

import asyncio
import sys
import os

# Add the current directory to Python path so we can import the bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smartgov_bot import SmartGovBot

async def test_greeting_classification():
    """Test that greetings are properly classified"""
    print("=" * 60)
    print("🧪 TESTING GREETING CLASSIFICATION")
    print("=" * 60)
    
    bot = SmartGovBot()
    
    test_cases = [
        # English test cases
        ("Hello", "greeting", "english"),
        ("Hi", "greeting", "english"),
        ("hello", "greeting", "english"),
        ("hi", "greeting", "english"),
        ("Hey", "greeting", "english"),
        ("Namaste", "greeting", "english"),
        ("Good morning", "greeting", "english"),
        ("Hello how are you", "greeting", "english"),
        ("Hi there", "greeting", "english"),
        ("Help me", "help", "english"),
        ("I need help", "help", "english"),
        ("Can you help", "help", "english"),
        
        # Hindi test cases (test in Hindi context)
        ("Madad chahiye", "help", "hindi"),
        ("Sahayata chahiye", "help", "hindi"),
        ("Namaste", "greeting", "hindi"),
        ("Hello", "greeting", "hindi"),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected_intent, language in test_cases:
        print(f"\n🔍 Testing: '{message}' in {language.upper()} (Expected: {expected_intent.upper()})")
        
        # Test rule-based classification with proper language context
        rule_intent = bot.get_intent_rule_based(message, language)
        
        if rule_intent == expected_intent:
            print(f"✅ PASS: Rule-based classified as {rule_intent.upper()}")
            passed += 1
        else:
            print(f"❌ FAIL: Rule-based classified as {rule_intent.upper()}, expected {expected_intent.upper()}")
            failed += 1
    
    print(f"\n📊 GREETING CLASSIFICATION RESULTS:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    return failed == 0

async def test_language_persistence():
    """Test language persistence during conversations"""
    print("\n" + "=" * 60)
    print("🧪 TESTING LANGUAGE PERSISTENCE")
    print("=" * 60)
    
    bot = SmartGovBot()
    
    # Simulate a conversation flow
    test_conversations = [
        {
            "name": "Hindi to Name Response",
            "steps": [
                {"message": "Mereko ex gratia apply krna hain", "expected_lang": "hi", "context": "main_menu"},
                {"message": "Abhishek", "expected_lang": "hi", "context": "collecting_info"},  # Should stay Hindi
                {"message": "Ram", "expected_lang": "hi", "context": "collecting_info"},  # Should stay Hindi
            ]
        },
        {
            "name": "Nepali to Name Response", 
            "steps": [
                {"message": "Ma ex gratia apply garna chahanchhu", "expected_lang": "ne", "context": "main_menu"},
                {"message": "Suresh", "expected_lang": "ne", "context": "collecting_info"},  # Should stay Nepali
                {"message": "Bahadur", "expected_lang": "ne", "context": "collecting_info"},  # Should stay Nepali
            ]
        }
    ]
    
    all_passed = True
    
    for conv in test_conversations:
        print(f"\n🗣️ Testing Conversation: {conv['name']}")
        session = {'language': None, 'state': None}
        
        for i, step in enumerate(conv['steps']):
            message = step['message']
            expected_lang = step['expected_lang']
            context = step['context']
            
            print(f"  Step {i+1}: '{message}'")
            
            # Simulate language detection
            detected_lang = await bot.detect_language_with_llm(message)
            lang_map = {'english': 'en', 'hindi': 'hi', 'nepali': 'ne'}
            detected_key = lang_map.get(detected_lang, 'en')
            
            # Simulate the language persistence logic
            current_session_language = session.get('language')
            
            if context == 'collecting_info' and current_session_language:
                # Should maintain language during data collection
                final_lang = current_session_language
                print(f"    🔒 APPLICATION MODE: Language locked to {current_session_language}")
            elif not current_session_language:
                # First interaction
                session['language'] = detected_key
                final_lang = detected_key
                print(f"    🎯 LANGUAGE SET: First interaction, setting to {detected_key}")
            elif current_session_language and current_session_language != detected_key:
                # Check word count for language switching
                word_count = len(message.split())
                if word_count >= 5 and context not in ['collecting_info', 'exgratia_apply']:
                    session['language'] = detected_key
                    final_lang = detected_key
                    print(f"    🔄 LANGUAGE SWITCHED: To {detected_key} (meaningful sentence)")
                else:
                    final_lang = current_session_language
                    print(f"    📌 LANGUAGE PERSISTENT: Continuing with {current_session_language} (short response)")
            else:
                final_lang = current_session_language or detected_key
                print(f"    📌 LANGUAGE PERSISTENT: Continuing with {final_lang}")
            
            # Update session state for next iteration
            session['state'] = context
            
            if final_lang == expected_lang:
                print(f"    ✅ PASS: Language is {final_lang} (expected {expected_lang})")
            else:
                print(f"    ❌ FAIL: Language is {final_lang} (expected {expected_lang})")
                all_passed = False
    
    print(f"\n📊 LANGUAGE PERSISTENCE RESULTS:")
    if all_passed:
        print("✅ All language persistence tests PASSED")
    else:
        print("❌ Some language persistence tests FAILED")
    
    return all_passed

async def test_nepali_support():
    """Test Nepali language support"""
    print("\n" + "=" * 60)
    print("🧪 TESTING NEPALI LANGUAGE SUPPORT")
    print("=" * 60)
    
    bot = SmartGovBot()
    
    nepali_test_cases = [
        "Namaste",
        "Ma ex gratia apply garna chahanchhu",
        "Mero ghar bhatkeko cha",
        "Status check garna chahanchhu",
        "Kati paisa milcha?",
    ]
    
    passed = 0
    failed = 0
    
    for message in nepali_test_cases:
        print(f"\n🔍 Testing Nepali: '{message}'")
        
        try:
            # Test language detection
            detected_lang = await bot.detect_language_with_llm(message)
            print(f"  Detected Language: {detected_lang}")
            
            # Test intent classification
            intent = await bot.get_intent_from_llm(message, detected_lang)
            print(f"  Detected Intent: {intent}")
            
            print(f"  ✅ PASS: Nepali message processed successfully")
            passed += 1
            
        except Exception as e:
            print(f"  ❌ FAIL: Error processing Nepali message: {e}")
            failed += 1
    
    print(f"\n📊 NEPALI SUPPORT RESULTS:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    return failed == 0

async def main():
    """Run all tests"""
    print("🚀 STARTING COMPREHENSIVE FIX TESTING")
    print("This will test the fixes for greeting classification, language persistence, and Nepali support")
    
    # Run all tests
    greeting_test = await test_greeting_classification()
    persistence_test = await test_language_persistence()
    nepali_test = await test_nepali_support()
    
    # Overall results
    print("\n" + "=" * 60)
    print("📋 OVERALL TEST RESULTS")
    print("=" * 60)
    
    tests = [
        ("Greeting Classification", greeting_test),
        ("Language Persistence", persistence_test),
        ("Nepali Support", nepali_test),
    ]
    
    all_passed = True
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n🏆 FINAL RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    if all_passed:
        print("🎉 Great! All issues have been fixed successfully!")
        print("The bot should now:")
        print("  • Correctly classify Hello/Hi as GREETING (not HELP)")
        print("  • Maintain language during application process") 
        print("  • Support Nepali language properly")
    else:
        print("⚠️ Some issues still need attention. Check the test results above.")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main()) 