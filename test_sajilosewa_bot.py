#!/usr/bin/env python3
"""
Simple test for the renamed SajiloSewa Bot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sajilosewa_bot import SajiloSewaBot, get_user_session, ChatbotState

def test_bot_initialization():
    """Test that the SajiloSewa bot can be initialized properly"""
    print("🚀 Testing SajiloSewa Bot Initialization...")
    
    try:
        bot = SajiloSewaBot()
        print("✅ SajiloSewa Bot initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return False

def test_welcome_message():
    """Test that welcome messages contain the new SajiloSewa name"""
    print("🧪 Testing SajiloSewa Welcome Messages...")
    
    bot = SajiloSewaBot()
    
    # Test English welcome message
    welcome_en = bot.get_language_text("en", "welcome")
    if "SajiloSewa" in welcome_en:
        print("✅ English welcome message contains SajiloSewa")
    else:
        print("❌ English welcome message missing SajiloSewa")
        return False
    
    # Test Hindi welcome message
    welcome_hi = bot.get_language_text("hi", "welcome")
    if "SajiloSewa" in welcome_hi:
        print("✅ Hindi welcome message contains SajiloSewa")
    else:
        print("❌ Hindi welcome message missing SajiloSewa")
        return False
    
    # Test Nepali welcome message
    welcome_ne = bot.get_language_text("ne", "welcome")
    if "SajiloSewa" in welcome_ne:
        print("✅ Nepali welcome message contains SajiloSewa")
    else:
        print("❌ Nepali welcome message missing SajiloSewa")
        return False
    
    return True

def test_greeting_classification():
    """Test that greetings are still classified correctly after rename"""
    print("🔍 Testing Greeting Classification...")
    
    bot = SajiloSewaBot()
    
    # Test basic greetings
    greetings = ["hello", "hi", "hey", "namaste"]
    
    for greeting in greetings:
        intent = bot.get_intent_rule_based(greeting, "en")
        if intent == "GREETING":
            print(f"✅ '{greeting}' correctly classified as GREETING")
        else:
            print(f"❌ '{greeting}' incorrectly classified as {intent}")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🎯 SajiloSewa Bot Rename Verification Test")
    print("=" * 50)
    
    tests = [
        test_bot_initialization,
        test_welcome_message,
        test_greeting_classification
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print()
    
    print("📊 Test Results:")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! SajiloSewa bot is working correctly!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 