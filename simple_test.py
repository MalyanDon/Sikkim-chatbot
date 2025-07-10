#!/usr/bin/env python3
"""
Simple test for rule-based language detection and greeting classification
"""

import sys
import os

# Add the current directory to Python path so we can import the bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smartgov_bot import SmartGovBot

def simple_test():
    print("🧪 SIMPLE TEST: Rule-Based Classification")
    print("=" * 50)
    
    bot = SmartGovBot()
    
    test_cases = [
        # Test greeting classification
        ("Hello", "greeting", "english"),
        ("Hi", "greeting", "english"),
        ("Namaste", "greeting", "english"),
        
        # Test help classification
        ("Madad chahiye", "help", "hindi"),
        ("Help me", "help", "english"),
        
        # Test language fallback detection  
        ("Mereko ex gratia apply krna hain", "hindi"),
        ("Ma ex gratia apply garna chahanchhu", "nepali"),
        ("Abhishek", "english"),  # Name should stay English
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    print("\n🔍 TESTING GREETING & HELP CLASSIFICATION:")
    for message, expected_intent, language in test_cases[:5]:
        try:
            intent = bot.get_intent_rule_based(message, language)
            status = "✅" if intent == expected_intent else "❌"
            print(f"{status} '{message}' ({language}) → {intent} (expected: {expected_intent})")
            if intent == expected_intent:
                success_count += 1
        except Exception as e:
            print(f"❌ '{message}' → ERROR: {e}")
    
    print("\n🌐 TESTING LANGUAGE FALLBACK DETECTION:")
    for message, expected_lang in test_cases[5:]:
        try:
            detected_lang = bot.detect_language_fallback(message)
            status = "✅" if detected_lang == expected_lang else "❌"
            print(f"{status} '{message}' → {detected_lang} (expected: {expected_lang})")
            if detected_lang == expected_lang:
                success_count += 1
        except Exception as e:
            print(f"❌ '{message}' → ERROR: {e}")
    
    success_rate = (success_count / total_tests) * 100
    print(f"\n📊 OVERALL RESULTS:")
    print(f"✅ Success: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 85:
        print("🎉 EXCELLENT! Our fixes are working well!")
        return True
    elif success_rate >= 70:
        print("✅ GOOD! Most fixes are working, minor issues remain.")
        return True
    else:
        print("⚠️ NEEDS WORK: Several issues still need to be addressed.")
        return False

if __name__ == "__main__":
    success = simple_test()
    sys.exit(0 if success else 1) 