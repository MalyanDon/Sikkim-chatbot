#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_smartgov_bot import SmartGovAssistantBot

def test_all_languages():
    bot = SmartGovAssistantBot()
    
    test_cases = {
        "ENGLISH": [
            ("Hello", "english"),
            ("I need help", "english"), 
            ("Can you help me?", "english"),
            ("How to apply?", "english"),
            ("Check my application status", "english")
        ],
        "HINDI": [
            ("Mujhe ex gratia ke baare main btayae", "hindi"),  # Critical failing case
            ("Mereko ex gratia apply krna hain", "hindi"),
            ("Madad chahiye", "hindi"),
            ("Sahayata", "hindi"),
            ("Kitna paisa milta hai?", "hindi"),
            ("मुझे एक्स ग्रेशिया के बारे में बताओ", "hindi"),
            ("मदद चाहिए", "hindi")
        ],
        "NEPALI": [
            ("Maddat chaincha", "nepali"),
            ("Kati paisa paincha?", "nepali"),
            ("Mero ghar badhi le bigaareko", "nepali"),
            ("Garna parcha", "nepali")
        ]
    }
    
    print("🔍 PROPER LANGUAGE DETECTION TEST")
    print("Using Our Bot's enhanced_language_detection Function")
    print("=" * 70)
    
    total_passed = 0
    total_failed = 0
    
    for language, cases in test_cases.items():
        print(f"\n🎯 TESTING {language}")
        print("-" * 50)
        
        language_passed = 0
        language_failed = 0
        
        for phrase, expected in cases:
            detected = bot.enhanced_language_detection(phrase)
            
            if detected.lower() == expected.lower():
                print(f"  ✅ '{phrase}' → {detected.upper()}")
                language_passed += 1
                total_passed += 1
            else:
                print(f"  ❌ '{phrase}' → Expected: {expected.upper()}, Got: {detected.upper()}")
                language_failed += 1
                total_failed += 1
        
        success_rate = (language_passed / (language_passed + language_failed)) * 100
        print(f"  📊 {language}: {language_passed}/{language_passed + language_failed} passed ({success_rate:.1f}%)")
    
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    
    total_tests = total_passed + total_failed
    overall_success = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {overall_success:.1f}%")
    
    if overall_success >= 95:
        print("🎉 EXCELLENT! Language detection working perfectly!")
    elif overall_success >= 80:
        print("✅ GOOD! Most issues resolved!")
    else:
        print("⚠️  MORE WORK NEEDED!")

if __name__ == "__main__":
    test_all_languages() 