import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_language_detection(text: str) -> str:
    """Test language detection using Qwen"""
    try:
        async with aiohttp.ClientSession() as session:
            prompt = f"""You are the language detection system for SmartGov Assistant. Analyze this text and determine if it's English, Hindi, or Nepali.

Key Grammar Patterns:
1. Hindi: hai, hain, tha, thi, hoga, karna hai
2. Nepali: cha, chhan, ho, bhayo, hunchha
3. English: SVO structure, auxiliary verbs

Text to analyze: "{text}"
Respond with EXACTLY one word - either 'english', 'hindi', or 'nepali'."""
            
            async with session.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": "qwen2.5:3b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                }
            ) as response:
                result = await response.json()
                return result['response'].strip().lower()
                
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None

async def test_intent_classification(text: str, lang: str) -> str:
    """Test intent classification using Qwen"""
    try:
        async with aiohttp.ClientSession() as session:
            prompt = f"""You are an intent classifier for SmartGov Assistant. Classify this message into one intent:

Available intents: ex_gratia, emergency, tourism, complaint, certificate, csc, check_status, unknown

Examples:
- ex_gratia: "compensation", "damage", "flood", "ex-gratia"
- emergency: "ambulance", "police", "fire", "urgent"
- tourism: "homestay", "tourist", "booking", "travel"
- complaint: "complaint", "grievance", "shikayat", "ujuri"
- certificate: "certificate", "document", "pramaanpatra"
- csc: "CSC", "operator", "center"
- check_status: "status", "track", "check"

User message: "{text}"
Language: {lang}

Respond with EXACTLY one intent name."""
            
            async with session.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": "qwen2.5:3b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                }
            ) as response:
                result = await response.json()
                return result['response'].strip().lower()
                
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None

async def run_focused_tests():
    """Run focused tests for key scenarios"""
    
    test_cases = [
        # Ex-Gratia scenarios
        ("How to apply for ex-gratia?", "english", "ex_gratia"),
        ("Ex-gratia ke liye kaise apply karna hai?", "hindi", "ex_gratia"),
        ("Ex-gratia ko lagi kasari apply garnu cha?", "nepali", "ex_gratia"),
        
        # Emergency scenarios
        ("Need ambulance urgently", "english", "emergency"),
        ("Ambulance chahiye jaldi", "hindi", "emergency"),
        ("Ambulance chahincha chito", "nepali", "emergency"),
        
        # Tourism scenarios
        ("Book homestay in Pelling", "english", "tourism"),
        ("Pelling mein homestay book karna hai", "hindi", "tourism"),
        ("Pelling ma homestay book garnu cha", "nepali", "tourism"),
        
        # Complaint scenarios
        ("File complaint about road", "english", "complaint"),
        ("Sadak ki shikayat darj karni hai", "hindi", "complaint"),
        ("Sadak ko ujuri darta garnu cha", "nepali", "complaint"),
        
        # Certificate scenarios
        ("Apply for birth certificate", "english", "certificate"),
        ("Janm certificate ke liye apply karna hai", "hindi", "certificate"),
        ("Janm certificate ko lagi apply garnu cha", "nepali", "certificate"),
        
        # CSC scenarios
        ("Find CSC operator", "english", "csc"),
        ("CSC operator dhundna hai", "hindi", "csc"),
        ("CSC operator bhetnu cha", "nepali", "csc"),
        
        # Status check scenarios
        ("Check my application status", "english", "check_status"),
        ("Mere application ka status check karna hai", "hindi", "check_status"),
        ("Mero application ko status check garnu cha", "nepali", "check_status")
    ]
    
    print("🤖 FOCUSED SMARTGOV BOT TESTING")
    print("=" * 60)
    
    passed_lang = 0
    passed_intent = 0
    total = len(test_cases)
    
    for i, (query, expected_lang, expected_intent) in enumerate(test_cases, 1):
        print(f"\n🔍 Test #{i}")
        print(f"Query: {query}")
        print(f"Expected Language: {expected_lang}")
        print(f"Expected Intent: {expected_intent}")
        
        # Test language detection
        detected_lang = await test_language_detection(query)
        lang_correct = detected_lang == expected_lang
        if lang_correct:
            passed_lang += 1
        
        print(f"Detected Language: {detected_lang} {'✅' if lang_correct else '❌'}")
        
        # Test intent classification
        detected_intent = await test_intent_classification(query, detected_lang or expected_lang)
        intent_correct = detected_intent == expected_intent
        if intent_correct:
            passed_intent += 1
        
        print(f"Detected Intent: {detected_intent} {'✅' if intent_correct else '❌'}")
        print("-" * 50)
    
    print(f"\n📊 RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Language Detection: {passed_lang}/{total} ({(passed_lang/total)*100:.1f}%)")
    print(f"Intent Classification: {passed_intent}/{total} ({(passed_intent/total)*100:.1f}%)")
    print(f"Overall Accuracy: {((passed_lang + passed_intent)/(total*2))*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(run_focused_tests()) 