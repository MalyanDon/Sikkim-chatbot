import asyncio
import logging
from comprehensive_smartgov_bot import SmartGovAssistantBot

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_intents():
    """Test all intents with various test cases"""
    bot = SmartGovAssistantBot()
    all_passed = True
    
    test_cases = [
        # Homestay booking
        ("I want to book a homestay in Pelling", "homestay_book"),
        ("Homestay booking in Yuksom", "homestay_book"),
        ("Show me homestays in Gyalshing", "homestay_book"),
        ("मैं होमस्टे बुक करना चाहता हूं", "homestay_book"),
        ("होमस्टे खोज्नु छ", "homestay_book"),
        
        # Emergency services
        ("Need ambulance", "emergency_medical"),
        ("Call police", "emergency_police"),
        ("Suicide helpline", "emergency_suicide"),
        ("Women's helpline", "emergency_women"),
        ("Fire emergency", "emergency_disaster"),
        ("एम्बुलेन्स चाहिन्छ", "emergency_medical"),
        ("पुलिस को बुलाओ", "emergency_police"),
        
        # Complaints
        ("I want to file a complaint", "complaint_file"),
        ("Register complaint", "complaint_file"),
        ("शिकायत दर्ज करनी है", "complaint_file"),
        ("उजुरी दर्ता गर्नु छ", "complaint_file"),
        
        # Certificates
        ("Apply for certificate", "certificate_apply"),
        ("Need birth certificate", "certificate_apply"),
        ("सर्टिफिकेट के लिए अप्लाई करना है", "certificate_apply"),
        ("प्रमाणपत्र को लागि आवेदन", "certificate_apply"),
        
        # CSC Services
        ("Find CSC operator", "csc_contact"),
        ("CSC near me", "csc_contact"),
        ("नजदीकी CSC", "csc_contact"),
        ("CSC अपरेटर खोज्नु छ", "csc_contact"),
        
        # Ex-gratia
        ("Apply for ex-gratia", "exgratia_apply"),
        ("Ex gratia assistance", "exgratia_apply"),
        ("एक्स-ग्रेशिया के लिए अप्लाई", "exgratia_apply"),
        ("एक्स-ग्रेसिया सहायता", "exgratia_apply"),
        
        # Status check
        ("Check application status", "status_check"),
        ("Track my application", "status_check"),
        ("स्टेटस चेक करना है", "status_check"),
        ("आवेदन स्थिति हेर्नु छ", "status_check"),
        
        # Help
        ("Help me", "help"),
        ("What services do you offer", "help"),
        ("मदद चाहिए", "help"),
        ("सहयोग चाहिन्छ", "help")
    ]
    
    print("\n=== Testing All Intents ===")
    for text, expected_intent in test_cases:
        try:
            # First detect language
            language = await bot.detect_language_with_llm(text)
            # Then get intent
            intent = await bot.get_intent_from_llm(text, language)
            
            print(f"\nInput: {text}")
            print(f"Language: {language}")
            print(f"Detected Intent: {intent}")
            print(f"Expected Intent: {expected_intent}")
            
            if intent == expected_intent:
                print("✅ PASS")
            else:
                print("❌ FAIL")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR testing '{text}': {str(e)}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All intent tests passed!")
    else:
        print("\n❌ Some intent tests failed!")
    return all_passed

if __name__ == "__main__":
    asyncio.run(test_intents()) 