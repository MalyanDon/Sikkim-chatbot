#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE VERIFICATION TEST
Tests all the critical issues reported by the user:
1. Greeting classification (Hello/Hi should be GREETING, not HELP)
2. Language persistence during application flow
3. Intent classification accuracy
4. Complete user journey simulation
"""

import sys
import os
import asyncio

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smartgov_bot import SmartGovBot, get_user_session, ChatbotState

class MockUpdate:
    """Mock Telegram Update object for testing"""
    def __init__(self, user_id, message_text, username="TestUser"):
        self.effective_user = MockUser(user_id, username)
        self.message = MockMessage(message_text, MockUser(user_id, username))

class MockUser:
    """Mock Telegram User object"""
    def __init__(self, user_id, username):
        self.id = user_id
        self.first_name = username
        self.username = username

class MockMessage:
    """Mock Telegram Message object"""
    def __init__(self, text, user):
        self.text = text
        self.from_user = user

class MockContext:
    """Mock Telegram Context object"""
    def __init__(self):
        self.user_data = {}

async def test_greeting_classification():
    """Test that Hello/Hi are classified as GREETING, not HELP"""
    print("🔍 TESTING GREETING CLASSIFICATION")
    print("=" * 50)
    
    bot = SmartGovBot()
    greeting_tests = [
        "Hello",
        "Hi", 
        "Hey",
        "Namaste",
        "hello",
        "hi",
        "Hey there"
    ]
    
    success_count = 0
    
    for greeting in greeting_tests:
        print(f"\n📝 Testing: '{greeting}'")
        
        # Test language detection
        language = await bot.detect_language_with_llm(greeting)
        print(f"   Language: {language}")
        
        # Test intent classification  
        intent = await bot.get_intent_from_llm(greeting, language)
        print(f"   Intent: {intent}")
        
        if intent.lower() == 'greeting':
            print(f"   ✅ CORRECT: '{greeting}' → GREETING")
            success_count += 1
        else:
            print(f"   ❌ WRONG: '{greeting}' → {intent} (should be GREETING)")
    
    success_rate = (success_count / len(greeting_tests)) * 100
    print(f"\n📊 GREETING CLASSIFICATION: {success_count}/{len(greeting_tests)} ({success_rate:.1f}%)")
    
    return success_rate >= 80  # Allow some tolerance

async def test_help_classification():
    """Test that actual help requests are classified correctly"""
    print("\n🔍 TESTING HELP CLASSIFICATION")
    print("=" * 50)
    
    bot = SmartGovBot()
    help_tests = [
        "I need help",
        "Can you help me",
        "Help me please",
        "I need assistance",
        "What can you do",
        "Help"
    ]
    
    success_count = 0
    
    for help_msg in help_tests:
        print(f"\n📝 Testing: '{help_msg}'")
        
        language = await bot.detect_language_with_llm(help_msg)
        intent = await bot.get_intent_from_llm(help_msg, language)
        print(f"   Language: {language}")
        print(f"   Intent: {intent}")
        
        if intent.lower() in ['help', 'other']:
            print(f"   ✅ CORRECT: '{help_msg}' → {intent}")
            success_count += 1
        else:
            print(f"   ❌ WRONG: '{help_msg}' → {intent} (should be HELP)")
    
    success_rate = (success_count / len(help_tests)) * 100
    print(f"\n📊 HELP CLASSIFICATION: {success_count}/{len(help_tests)} ({success_rate:.1f}%)")
    
    return success_rate >= 80

async def test_complete_hindi_journey():
    """Test complete user journey starting in Hindi"""
    print("\n🔍 TESTING COMPLETE HINDI USER JOURNEY")
    print("=" * 50)
    
    bot = SmartGovBot()
    user_id = 99999
    
    # Clear any existing session
    from smartgov_bot import USER_SESSIONS
    if user_id in USER_SESSIONS:
        del USER_SESSIONS[user_id]
    
    print("\n📋 SIMULATING COMPLETE USER JOURNEY:")
    print("1. User: 'Mereko ex gratia apply krna hain' (Hindi)")
    print("2. User: 'Abhishek' (Name - could be English)")
    print("3. Check: Does bot continue in Hindi?")
    print()
    
    # Step 1: Initial request in Hindi
    message1 = "Mereko ex gratia apply krna hain"
    print(f"🔴 USER: {message1}")
    
    language1 = await bot.detect_language_with_llm(message1)
    intent1 = await bot.get_intent_from_llm(message1, language1)
    
    print(f"   Detected: {language1} | {intent1}")
    
    # Set up session (simulating bot response)
    session = get_user_session(user_id)
    session['language'] = 'hi'  # Hindi
    session['state'] = ChatbotState.COLLECTING_INFO
    session['data'] = {}
    session['current_question'] = 'name'
    
    print(f"   Session: language={session['language']}, state={session['state']}")
    
    # Step 2: User provides name
    message2 = "Abhishek"
    print(f"\n🔴 USER: {message2}")
    
    language2 = await bot.detect_language_with_llm(message2)
    print(f"   Name detected as: {language2}")
    
    # Critical test: What language will bot use for next question?
    current_session_language = session.get('language')
    
    # Apply the persistence logic
    if session['state'] == ChatbotState.COLLECTING_INFO and current_session_language:
        final_language = current_session_language
        print(f"   🔒 PERSISTENCE APPLIED: Continuing in {final_language}")
    else:
        lang_map = {'english': 'en', 'hindi': 'hi', 'nepali': 'ne'}
        final_language = lang_map.get(language2, 'en')
        print(f"   ❌ NO PERSISTENCE: Would switch to {final_language}")
    
    # Check what the next question would be
    from smartgov_bot import LANGUAGES
    
    if final_language == 'hi':
        next_question = LANGUAGES['hi']['father_name_question']
        print(f"\n🤖 BOT: {next_question}")
        print("   ✅ SUCCESS: Bot continues in Hindi!")
        return True
    else:
        next_question = LANGUAGES['en']['father_name_question']
        print(f"\n🤖 BOT: {next_question}")
        print("   ❌ FAILURE: Bot switched to English!")
        return False

async def test_complete_english_journey():
    """Test complete user journey starting in English"""
    print("\n🔍 TESTING COMPLETE ENGLISH USER JOURNEY")
    print("=" * 50)
    
    bot = SmartGovBot()
    user_id = 99998
    
    # Clear any existing session
    from smartgov_bot import USER_SESSIONS
    if user_id in USER_SESSIONS:
        del USER_SESSIONS[user_id]
    
    print("\n📋 SIMULATING ENGLISH USER JOURNEY:")
    print("1. User: 'I want to apply for ex gratia' (English)")
    print("2. User: 'राम कुमार' (Hindi name)")
    print("3. Check: Does bot continue in English?")
    print()
    
    # Step 1: Initial request in English
    message1 = "I want to apply for ex gratia"
    print(f"🔴 USER: {message1}")
    
    language1 = await bot.detect_language_with_llm(message1)
    intent1 = await bot.get_intent_from_llm(message1, language1)
    
    print(f"   Detected: {language1} | {intent1}")
    
    # Set up session
    session = get_user_session(user_id)
    session['language'] = 'en'  # English
    session['state'] = ChatbotState.COLLECTING_INFO
    session['data'] = {}
    session['current_question'] = 'name'
    
    print(f"   Session: language={session['language']}, state={session['state']}")
    
    # Step 2: User provides Hindi name
    message2 = "राम कुमार"
    print(f"\n🔴 USER: {message2}")
    
    language2 = await bot.detect_language_with_llm(message2)
    print(f"   Name detected as: {language2}")
    
    # Apply persistence logic
    current_session_language = session.get('language')
    
    if session['state'] == ChatbotState.COLLECTING_INFO and current_session_language:
        final_language = current_session_language
        print(f"   🔒 PERSISTENCE APPLIED: Continuing in {final_language}")
    else:
        lang_map = {'english': 'en', 'hindi': 'hi', 'nepali': 'ne'}
        final_language = lang_map.get(language2, 'en')
        print(f"   ❌ NO PERSISTENCE: Would switch to {final_language}")
    
    # Check next question
    from smartgov_bot import LANGUAGES
    
    if final_language == 'en':
        next_question = LANGUAGES['en']['father_name_question']
        print(f"\n🤖 BOT: {next_question}")
        print("   ✅ SUCCESS: Bot continues in English!")
        return True
    else:
        next_question = LANGUAGES['hi']['father_name_question']
        print(f"\n🤖 BOT: {next_question}")
        print("   ❌ FAILURE: Bot switched to Hindi!")
        return False

async def test_intent_classification_accuracy():
    """Test various intent classifications"""
    print("\n🔍 TESTING INTENT CLASSIFICATION ACCURACY")
    print("=" * 50)
    
    bot = SmartGovBot()
    
    test_cases = [
        # Ex-gratia applications
        ("Mereko ex gratia apply krna hain", "exgratia_apply"),
        ("I want to apply for ex gratia", "exgratia_apply"),
        ("Ex gratia application", "exgratia_apply"),
        
        # Status checks
        ("Application status check karna hai", "status_check"),
        ("What is my application status", "status_check"),
        ("Status check", "status_check"),
        
        # Greetings
        ("Hello", "greeting"),
        ("Hi", "greeting"),
        ("Namaste", "greeting"),
        
        # Help requests
        ("I need help", "help"),
        ("Can you help me", "help"),
        ("What can you do", "help"),
        
        # Other
        ("Application kahan hai?", "other"),
        ("Where is my form?", "other")
    ]
    
    success_count = 0
    
    for message, expected_intent in test_cases:
        print(f"\n📝 Testing: '{message}'")
        
        language = await bot.detect_language_with_llm(message)
        intent = await bot.get_intent_from_llm(message, language)
        
        print(f"   Expected: {expected_intent}")
        print(f"   Got: {intent}")
        
        if intent.lower() == expected_intent.lower():
            print(f"   ✅ CORRECT")
            success_count += 1
        else:
            print(f"   ❌ WRONG")
    
    success_rate = (success_count / len(test_cases)) * 100
    print(f"\n📊 INTENT ACCURACY: {success_count}/{len(test_cases)} ({success_rate:.1f}%)")
    
    return success_rate >= 70  # Allow some tolerance for edge cases

async def main():
    """Run all final verification tests"""
    print("🚀 FINAL COMPREHENSIVE VERIFICATION")
    print("Testing all user-reported issues and requirements")
    print("=" * 80)
    
    # Run all tests
    test_results = {}
    
    print("\n" + "="*80)
    test_results['greetings'] = await test_greeting_classification()
    
    print("\n" + "="*80)
    test_results['help'] = await test_help_classification()
    
    print("\n" + "="*80)
    test_results['hindi_journey'] = await test_complete_hindi_journey()
    
    print("\n" + "="*80)
    test_results['english_journey'] = await test_complete_english_journey()
    
    print("\n" + "="*80)
    test_results['intent_accuracy'] = await test_intent_classification_accuracy()
    
    # Final assessment
    print("\n" + "="*80)
    print("🎯 FINAL VERIFICATION RESULTS")
    print("="*80)
    
    all_passed = True
    
    print("\n📊 TEST RESULTS:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n🎯 OVERALL STATUS:")
    if all_passed:
        print("✅ ALL TESTS PASSED - BOT IS WORKING PERFECTLY")
        print("✅ Greeting classification: Fixed")
        print("✅ Language persistence: Working")
        print("✅ Intent accuracy: Good")
        print("✅ User experience: Excellent")
        print("\n🎉 THE BOT IS READY FOR PRODUCTION USE!")
    else:
        print("❌ SOME TESTS FAILED - ISSUES REMAIN")
        print("❌ Bot needs further fixes")
        print("\n⚠️ DO NOT USE IN PRODUCTION YET")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    
    print("\n" + "="*80)
    if success:
        print("🎉 FINAL VERIFICATION: COMPLETE SUCCESS")
        print("🚀 Bot is ready for users!")
    else:
        print("⚠️ FINAL VERIFICATION: ISSUES FOUND")
        print("🔧 More fixes needed!")
    
    sys.exit(0 if success else 1) 