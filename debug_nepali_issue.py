#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_smartgov_bot import SmartGovAssistantBot

def test_nepali_issue():
    bot = SmartGovAssistantBot()
    
    failing_phrases = [
        'Maddat chaincha',      # Expected: nepali, Got: hindi
        'Kati paisa paincha?',  # Expected: nepali, Got: hindi
        'Mero ghar badhi le bigaareko',  # Expected: nepali, Got: hindi
        'Garna parcha'          # Working correctly
    ]
    
    print("🔍 DEBUGGING NEPALI DETECTION ISSUES")
    print("=" * 60)
    
    for phrase in failing_phrases:
        print(f"\n📝 Testing: '{phrase}'")
        detected = bot.enhanced_language_detection(phrase)
        if phrase in ['Maddat chaincha', 'Kati paisa paincha?', 'Mero ghar badhi le bigaareko']:
            if detected.upper() == 'HINDI':
                print("❌ INCORRECTLY DETECTED AS HINDI!")
            else:
                print(f"✅ Correctly detected as {detected.upper()}")
        else:
            print(f"🎯 Result: {detected.upper()}")

if __name__ == "__main__":
    test_nepali_issue() 