import asyncio
from comprehensive_smartgov_bot import SmartGovAssistantBot
import logging
import sys

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout  # Ensure logging goes to stdout
)

async def test_emergency_intents():
    """Test emergency intent classification with comprehensive scenarios"""
    print("\n=== Testing Emergency Intent Classification ===", flush=True)
    
    bot = SmartGovAssistantBot()
    all_passed = True
    
    # English tests - direct and indirect
    english_tests = [
        "I need an ambulance",
        "Can you help me get an ambulance",
        "My father is having chest pain",
        "There's been an accident",
        "Someone is unconscious",
        "Medical emergency",
        "Need urgent medical help",
        "How do I contact ambulance service",
        "Call ambulance please",
        "Emergency situation need ambulance"
    ]

    # Hindi tests - including romanized
    romanized_hindi_tests = [
        "Ambulance bhejo jaldi",
        "Emergency hai ambulance chahiye",
        "Mere papa ko heart attack aya hai",
        "Accident ho gaya hai",
        "Koi behosh ho gaya hai",
        "Medical emergency hai",
        "Ambulance kaise bulau",
        "Jaldi ambulance bhejiye",
        "Madad karo ambulance ki zarurat hai",
        "Bahut urgent hai ambulance chahiye"
    ]

    # Nepali tests - including romanized
    romanized_nepali_tests = [
        "Ambulance pathau na",
        "Emergency cha ambulance chaincha",
        "Mero buwa lai heart attack bhayo",
        "Accident bhayo",
        "Behosh bhayo koi",
        "Medical emergency cha",
        "Ambulance kasari bolaune",
        "Chito ambulance pathau",
        "Maddat garnus ambulance chahincha",
        "Dherai urgent cha ambulance chaincha"
    ]
    
    # Mixed language and edge cases
    mixed_tests = [
        "Ambulance emergency hai",
        "Need ambulance jaldi",
        "Emergency cha please help",
        "Ambulance service urgent chahiye",
        "Medical emergency ambulance chaincha",
        "Help ambulance bulao",
        "Quick ambulance chahincha",
        "Urgent ambulance zaroorat",
        "My friend is hurt ambulance chahiye",
        "Blood nikal raha hai please send ambulance",
        "Accident bhayo quick help",
        "Heart attack emergency hai",
        "Someone fainted ambulance pathau",
        "Bleeding ho raha hai help needed"
    ]

    print("\n=== Testing English Phrases ===", flush=True)
    for text in english_tests:
        try:
            lang = await bot.classify_language_with_llm(text)
            intent = await bot.classify_intent_with_llm(text)
            print(f"\nInput: {text}", flush=True)
            print(f"Detected Language: {lang}", flush=True)
            print(f"Detected Intent: {intent}", flush=True)
            if not intent.startswith('emergency_'):
                print(f"❌ FAIL: Failed to detect emergency in: {text}", flush=True)
                all_passed = False
            else:
                print("✅ PASS", flush=True)
        except Exception as e:
            print(f"❌ ERROR testing '{text}': {str(e)}", flush=True)
            all_passed = False

    print("\n=== Testing Romanized Hindi Phrases ===", flush=True)
    for text in romanized_hindi_tests:
        try:
            lang = await bot.classify_language_with_llm(text)
            intent = await bot.classify_intent_with_llm(text)
            print(f"\nInput: {text}", flush=True)
            print(f"Detected Language: {lang}", flush=True)
            print(f"Detected Intent: {intent}", flush=True)
            if not intent.startswith('emergency_'):
                print(f"❌ FAIL: Failed to detect emergency in: {text}", flush=True)
                all_passed = False
            else:
                print("✅ PASS", flush=True)
        except Exception as e:
            print(f"❌ ERROR testing '{text}': {str(e)}", flush=True)
            all_passed = False

    print("\n=== Testing Romanized Nepali Phrases ===", flush=True)
    for text in romanized_nepali_tests:
        try:
            lang = await bot.classify_language_with_llm(text)
            intent = await bot.classify_intent_with_llm(text)
            print(f"\nInput: {text}", flush=True)
            print(f"Detected Language: {lang}", flush=True)
            print(f"Detected Intent: {intent}", flush=True)
            if not intent.startswith('emergency_'):
                print(f"❌ FAIL: Failed to detect emergency in: {text}", flush=True)
                all_passed = False
            else:
                print("✅ PASS", flush=True)
        except Exception as e:
            print(f"❌ ERROR testing '{text}': {str(e)}", flush=True)
            all_passed = False

    print("\n=== Testing Mixed Language Phrases ===", flush=True)
    for text in mixed_tests:
        try:
            lang = await bot.classify_language_with_llm(text)
            intent = await bot.classify_intent_with_llm(text)
            print(f"\nInput: {text}", flush=True)
            print(f"Detected Language: {lang}", flush=True)
            print(f"Detected Intent: {intent}", flush=True)
            if not intent.startswith('emergency_'):
                print(f"❌ FAIL: Failed to detect emergency in: {text}", flush=True)
                all_passed = False
            else:
                print("✅ PASS", flush=True)
        except Exception as e:
            print(f"❌ ERROR testing '{text}': {str(e)}", flush=True)
            all_passed = False

    if all_passed:
        print("\n✅ All emergency intent tests passed!", flush=True)
    else:
        print("\n❌ Some emergency intent tests failed!", flush=True)
    return all_passed

async def test_intent_classification():
    """Test intent classification with various scenarios"""
    print("\n=== Testing Intent Classification ===", flush=True)
    
    bot = SmartGovAssistantBot()
    
    test_cases = [
        # General help requests
        ("Can you help me", "help"),
        ("Kya aap meri help kr skte ho", "help"),
        ("Madad chahiye", "help"),
        ("Sahayata chahiye", "help"),
        ("I need assistance", "help"),
        ("Help karo", "help"),
        
        # Status checks
        ("Check my application status", "check_status"),
        ("Track my application", "check_status"),
        ("Mera application status kya hai", "check_status"),
        ("Application ki status batao", "check_status"),
        ("Mero application ko status ke cha", "check_status"),
        
        # Emergency services
        ("Need ambulance", "emergency_ambulance"),
        ("Ambulance bhejo", "emergency_ambulance"),
        ("Heart attack", "emergency_ambulance"),
        ("Someone is injured", "emergency_ambulance"),
        ("Call police", "emergency_police"),
        ("Fire emergency", "emergency_fire"),
        
        # Mixed language and indirect requests
        ("Can you help me get an ambulance", "emergency_ambulance"),
        ("Police ko contact kaise kare", "emergency_police"),
        ("Aag lag gayi hai", "emergency_fire"),
        ("Chest pain ho raha hai", "emergency_ambulance")
    ]
    
    passed = 0
    total = len(test_cases)
    
    for text, expected_intent in test_cases:
        try:
            print(f"\nTesting: '{text}'", flush=True)
            intent = await bot.classify_intent_with_llm(text)
            
            if intent == expected_intent:
                print(f"✅ PASS: Correctly classified as {intent.upper()}", flush=True)
                passed += 1
            else:
                print(f"❌ FAIL: Got {intent.upper()}, expected {expected_intent.upper()}", flush=True)
        except Exception as e:
            print(f"❌ ERROR testing '{text}': {str(e)}", flush=True)
    
    print(f"\n=== Intent Classification Results ===", flush=True)
    print(f"Total Tests: {total}", flush=True)
    print(f"Passed: {passed}", flush=True)
    print(f"Failed: {total - passed}", flush=True)
    print(f"Success Rate: {(passed/total)*100:.1f}%", flush=True)
    
    return passed == total

if __name__ == "__main__":
    try:
        emergency_passed = asyncio.run(test_emergency_intents())
        intent_passed = asyncio.run(test_intent_classification())
        if not emergency_passed or not intent_passed:
            sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {str(e)}", flush=True)
        sys.exit(1) 