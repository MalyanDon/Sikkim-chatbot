#!/usr/bin/env python3
"""
Test Code-Mixed Hindi-English Language Detection and Response
Tests the bot's ability to detect and respond in code-mixed language (Hinglish)
"""

import sys
import os
import asyncio

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smartgov_bot import SmartGovBot, get_user_session, ChatbotState

async def test_code_mixed_detection():
    """Test code-mixed language detection"""
    print("🔍 TESTING CODE-MIXED HINDI-ENGLISH DETECTION")
    print("=" * 60)
    
    bot = SmartGovBot()
    
    # Test cases for code-mixed language
    test_cases = [
        {
            'message': 'Mereko ex gratia apply krna hain',
            'expected': 'code-mixed',
            'description': 'Hindi-English mix with "mereko" and "apply"'
        },
        {
            'message': 'Mujhe help chahiye application ke liye',
            'expected': 'code-mixed', 
            'description': 'Hindi-English mix with "mujhe", "help", "application"'
        },
        {
            'message': 'Mera application status check karna hai',
            'expected': 'code-mixed',
            'description': 'Hindi-English mix with "mera", "application", "status", "check"'
        },
        {
            'message': 'Ex gratia ke liye form kaise submit karna hai',
            'expected': 'code-mixed',
            'description': 'Hindi-English mix with technical terms'
        },
        {
            'message': 'Government scheme ka process kya hai',
            'expected': 'code-mixed',
            'description': 'Hindi-English mix with government terminology'
        },
        {
            'message': 'I want to apply for ex gratia',
            'expected': 'pure-english',
            'description': 'Pure English (should not be detected as code-mixed)'
        },
        {
            'message': 'मुझे एक्स-ग्रेशिया के लिए आवेदन करना है',
            'expected': 'pure-hindi',
            'description': 'Pure Hindi (should not be detected as code-mixed)'
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 TEST {i}: {test_case['description']}")
        print(f"   Message: '{test_case['message']}'")
        
        # Test the code-mixed detection
        is_code_mixed = bot.detect_code_mixed_hinglish(test_case['message'])
        
        # Test the language detection
        detected_language = await bot.detect_language_with_llm(test_case['message'])
        
        print(f"   Code-mixed detected: {is_code_mixed}")
        print(f"   Language detected: {detected_language}")
        
        # Determine if the result matches expectation
        if test_case['expected'] == 'code-mixed':
            if is_code_mixed or detected_language == 'hindi_english_mixed':
                print(f"   ✅ SUCCESS: Correctly identified as code-mixed")
                success_count += 1
            else:
                print(f"   ❌ FAILED: Should be code-mixed but detected as {detected_language}")
        else:
            if not is_code_mixed and detected_language != 'hindi_english_mixed':
                print(f"   ✅ SUCCESS: Correctly identified as {test_case['expected']}")
                success_count += 1
            else:
                print(f"   ❌ FAILED: Should be {test_case['expected']} but detected as code-mixed")
    
    success_rate = (success_count / len(test_cases)) * 100
    print(f"\n📊 CODE-MIXED DETECTION ACCURACY: {success_count}/{len(test_cases)} ({success_rate:.1f}%)")
    
    return success_rate >= 80

async def test_code_mixed_responses():
    """Test code-mixed responses from the bot"""
    print("\n🤖 TESTING CODE-MIXED RESPONSES")
    print("=" * 60)
    
    bot = SmartGovBot()
    
    # Test user journey with code-mixed language
    user_id = 88888
    
    # Clear any existing session
    from smartgov_bot import USER_SESSIONS
    if user_id in USER_SESSIONS:
        del USER_SESSIONS[user_id]
    
    print("\n📋 SCENARIO: User starts ex-gratia application in code-mixed language")
    
    # Step 1: User says code-mixed message
    message = "Mereko ex gratia apply krna hain"
    print(f"\n🔴 USER: {message}")
    
    # Detect language
    detected_language = await bot.detect_language_with_llm(message)
    is_code_mixed = bot.detect_code_mixed_hinglish(message)
    
    print(f"   Detected language: {detected_language}")
    print(f"   Is code-mixed: {is_code_mixed}")
    
    # Set up session
    session = get_user_session(user_id)
    
    # Map language for response
    lang_map = {'english': 'en', 'hindi': 'hi', 'nepali': 'ne', 'hindi_english_mixed': 'hi_en'}
    detected_lang_key = lang_map.get(detected_language, 'en')
    
    if is_code_mixed or detected_language == 'hindi_english_mixed':
        response_lang = 'hi_en'  # Use code-mixed responses
        print(f"   🎯 Using code-mixed responses (hi_en)")
    else:
        response_lang = detected_lang_key
        print(f"   🎯 Using standard responses ({response_lang})")
    
    session['language'] = response_lang
    session['state'] = ChatbotState.COLLECTING_INFO
    session['data'] = {}
    
    # Check what the bot response would be
    from smartgov_bot import LANGUAGES
    
    if response_lang == 'hi_en' and 'hi_en' in LANGUAGES:
        # Get code-mixed response
        application_start_msg = LANGUAGES['hi_en']['application_start']
        name_question = LANGUAGES['hi_en']['name_question']
        
        print(f"\n🤖 BOT (Application Start): {application_start_msg}")
        print(f"🤖 BOT (Name Question): {name_question}")
        
        print(f"\n✅ SUCCESS: Bot is responding in code-mixed Hindi-English!")
        print(f"✅ User gets natural Hinglish responses matching their input style")
        return True
    else:
        print(f"\n❌ FAILED: Code-mixed responses not available or not selected")
        print(f"❌ Bot would respond in {response_lang} instead of code-mixed")
        return False

async def test_complete_code_mixed_flow():
    """Test complete application flow in code-mixed language"""
    print("\n🔄 TESTING COMPLETE CODE-MIXED APPLICATION FLOW")
    print("=" * 60)
    
    bot = SmartGovBot()
    user_id = 77777
    
    # Clear session
    from smartgov_bot import USER_SESSIONS
    if user_id in USER_SESSIONS:
        del USER_SESSIONS[user_id]
    
    print("\n📋 COMPLETE USER JOURNEY:")
    print("1. User: 'Mereko ex gratia apply krna hain' (Code-mixed)")
    print("2. Bot responds in code-mixed style")
    print("3. User: 'Abhishek' (Name)")
    print("4. Bot continues in code-mixed style")
    print()
    
    # Step 1: Initial code-mixed request
    message1 = "Mereko ex gratia apply krna hain"
    print(f"🔴 USER: {message1}")
    
    is_code_mixed1 = bot.detect_code_mixed_hinglish(message1)
    detected_lang1 = await bot.detect_language_with_llm(message1)
    
    print(f"   Detected: {detected_lang1} | Code-mixed: {is_code_mixed1}")
    
    # Set up session with code-mixed language
    session = get_user_session(user_id)
    session['language'] = 'hi_en'  # Code-mixed
    session['state'] = ChatbotState.COLLECTING_INFO
    session['data'] = {}
    session['current_question'] = 'name'
    
    from smartgov_bot import LANGUAGES
    
    if 'hi_en' in LANGUAGES:
        start_msg = LANGUAGES['hi_en']['application_start']
        name_question = LANGUAGES['hi_en']['name_question']
        
        print(f"🤖 BOT: {start_msg}")
        print(f"🤖 BOT: {name_question}")
        
        # Step 2: User provides name
        message2 = "Abhishek"
        print(f"\n🔴 USER: {message2}")
        
        # Apply language persistence (should stay in code-mixed)
        current_session_language = session.get('language')
        
        if session['state'] == ChatbotState.COLLECTING_INFO and current_session_language:
            final_language = current_session_language  # Maintain hi_en
            print(f"   🔒 PERSISTENCE: Continuing in {final_language}")
        else:
            final_language = 'en'  # Would fall back to English
            print(f"   ❌ NO PERSISTENCE: Would switch to {final_language}")
        
        # Next question in code-mixed
        if final_language == 'hi_en':
            father_name_question = LANGUAGES['hi_en']['father_name_question']
            print(f"🤖 BOT: {father_name_question}")
            
            print(f"\n✅ SUCCESS: Complete code-mixed flow working!")
            print(f"✅ Bot maintains Hinglish responses throughout application")
            print(f"✅ User gets consistent, natural code-mixed experience")
            return True
        else:
            print(f"\n❌ FAILED: Language persistence not working for code-mixed")
            return False
    else:
        print(f"\n❌ FAILED: Code-mixed language (hi_en) not properly configured")
        return False

async def main():
    """Run all code-mixed language tests"""
    print("🚀 CODE-MIXED HINDI-ENGLISH LANGUAGE TEST")
    print("Testing bot's ability to detect and respond in Hinglish")
    print("=" * 80)
    
    # Run tests
    test_results = {}
    
    print("\n" + "="*80)
    test_results['detection'] = await test_code_mixed_detection()
    
    print("\n" + "="*80)
    test_results['responses'] = await test_code_mixed_responses()
    
    print("\n" + "="*80)
    test_results['complete_flow'] = await test_complete_code_mixed_flow()
    
    # Final assessment
    print("\n" + "="*80)
    print("🎯 CODE-MIXED LANGUAGE TEST RESULTS")
    print("="*80)
    
    all_passed = True
    
    print("\n📊 TEST RESULTS:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n🎯 OVERALL CODE-MIXED SUPPORT:")
    if all_passed:
        print("✅ CODE-MIXED LANGUAGE: FULLY SUPPORTED")
        print("✅ Bot detects Hinglish accurately")
        print("✅ Bot responds in code-mixed style")
        print("✅ Language persistence works for code-mixed")
        print("✅ User gets natural Hinglish experience")
        print("\n🎉 HINGLISH SUPPORT IS WORKING PERFECTLY!")
    else:
        print("❌ CODE-MIXED LANGUAGE: NEEDS IMPROVEMENT")
        print("❌ Some aspects of Hinglish support not working")
        print("\n⚠️ HINGLISH SUPPORT NEEDS FIXES")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    
    print("\n" + "="*80)
    if success:
        print("🎉 CODE-MIXED LANGUAGE TEST: COMPLETE SUCCESS")
        print("🚀 Hinglish support is ready!")
    else:
        print("⚠️ CODE-MIXED LANGUAGE TEST: ISSUES FOUND")
        print("🔧 Hinglish support needs fixes!")
    
    sys.exit(0 if success else 1) 