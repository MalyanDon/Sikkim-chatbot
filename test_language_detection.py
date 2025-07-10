"""
Test Language Detection - Quick Test
"""

import sys
import os
sys.path.append(os.getcwd())

from comprehensive_smartgov_bot import SmartGovAssistantBot

def test_language_detection():
    """Test the enhanced language detection"""
    bot = SmartGovAssistantBot()
    
    print("🔍 TESTING ENHANCED LANGUAGE DETECTION")
    print("=" * 50)
    
    test_messages = [
        # Hindi tests
        ("Mujhe ex gratia ke baare main btayae", "hindi"),
        ("मुझे एक्स ग्रेशिया के बारे में बताओ", "hindi"),
        ("Kya hai ye exgratia scheme", "hindi"),
        ("Mera ghar flood mein damage ho gaya", "hindi"),
        ("Madad chahiye", "hindi"),
        ("Aap kaise ho", "hindi"),
        ("Band karo ye process", "hindi"),
        
        # English tests
        ("Can you help me with ex-gratia application", "english"),
        ("Hello, I want to apply for assistance", "english"),
        ("What is this scheme about", "english"),
        ("Please help me", "english"),
        ("Thank you", "english"),
        
        # Nepali tests
        ("म तपाईंलाई सहायता चाहिन्छ", "nepali"),
        ("कसरी आवेदन दिने", "nepali"),
    ]
    
    correct = 0
    total = len(test_messages)
    
    for message, expected in test_messages:
        detected = bot.enhanced_language_detection(message)
        status = "✅" if detected == expected else "❌"
        print(f"{status} '{message}' → {detected.upper()} (expected {expected.upper()})")
        if detected == expected:
            correct += 1
    
    print(f"\n📊 RESULTS: {correct}/{total} ({correct/total*100:.1f}%) correct")
    
    if correct >= total * 0.8:  # 80% accuracy threshold
        print("🎉 Language detection is working well!")
    else:
        print("⚠️ Language detection needs improvement")
    
    return correct >= total * 0.8

if __name__ == "__main__":
    test_language_detection() 