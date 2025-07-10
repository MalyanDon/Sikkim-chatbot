#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_smartgov_bot import SmartGovAssistantBot

def test_nepali_detection():
    bot = SmartGovAssistantBot()
    
    test_phrases = [
        'Maddat chaincha',
        'Kati paisa paincha?', 
        'Mero ghar badhi le bigaareko',
        'Garna parcha'
    ]
    
    print("🔍 DEBUGGING NEPALI DETECTION")
    print("=" * 50)
    
    for phrase in test_phrases:
        print(f"\n📝 Testing: '{phrase}'")
        detected = bot.enhanced_language_detection(phrase)
        print(f"🎯 Result: {detected.upper()}")

if __name__ == "__main__":
    test_nepali_detection() 