#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_smartgov_bot import SmartGovAssistantBot

def test_hindi_detection():
    bot = SmartGovAssistantBot()
    
    test_phrases = [
        'Mujhe ex gratia ke baare main btayae',  # This was failing in logs
        'मुझे एक्स ग्रेशिया के बारे में बताओ',
        'Maddat chahiye',
        'Mujhe paisa chahiye',
        'मदद चाहिए',
        'Kya kar sakte hain'
    ]
    
    print("🔍 DEBUGGING HINDI DETECTION")
    print("=" * 50)
    
    for phrase in test_phrases:
        print(f"\n📝 Testing: '{phrase}'")
        detected = bot.enhanced_language_detection(phrase)
        print(f"🎯 Result: {detected.upper()}")
        if phrase == 'Mujhe ex gratia ke baare main btayae':
            print("⚠️  THIS IS THE FAILING PHRASE FROM LOGS!")

if __name__ == "__main__":
    test_hindi_detection() 