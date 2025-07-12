import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_language_detection(text: str) -> str:
    """Test language detection using Qwen with domain-specific context. Returns (detected_lang, prompt, raw_response)"""
    try:
        async with aiohttp.ClientSession() as session:
            # Enhanced prompt with more domain examples and patterns
            prompt = f"""You are the language detection system for SmartGov Assistant, a government services chatbot in Sikkim. Your task is to identify whether user input is in English, Hindi, or Nepali.

Context: This is a citizen services chatbot. Users interact in all three languages, often mixing them. Focus on GRAMMAR PATTERNS over individual words, as many terms are shared or transliterated.

Key Grammar Patterns:

1. Hindi Sentence Structure:
   - Verb endings: है, हैं, था, थी, होगा, करना है, सकते हैं
   - Question format: क्या/कैसे/कहाँ + verb
   Example queries from our data:
   - "मुझे होमस्टे बुक करना है"
   - "एम्बुलेंस की जरूरत है"
   - "शिकायत दर्ज करनी है"
   - "सर्टिफिकेट कैसे बनवाएं"

2. Nepali Sentence Structure:
   - Verb endings: छ, छन्, हो, भयो, हुन्छ, गर्नु छ
   - Question format: के/कसरी/कहाँ + verb
   Example queries from our data:
   - "होमस्टे बुक गर्न चाहन्छु"
   - "एम्बुलेन्स चाहिन्छ"
   - "उजुरी दर्ता गर्नु छ"
   - "सर्टिफिकेट कसरी बनाउने"

3. English Patterns:
   - SVO order: "I want to book", "Please help me"
   - Question format: WH-word + verb/auxiliary
   - No Devanagari script
   Example queries from our data:
   - "Need ambulance urgently"
   - "How to apply for certificate"
   - "Want to file complaint"
   - "Looking for homestay in Pelling"

Special Cases from Our Data:

1. Place Names:
   - Treat place names (Pelling, Gyalshing, etc.) as neutral
   - Focus on sentence structure around them

2. Shared Terms:
   - होमस्टे/homestay
   - सर्टिफिकेट/certificate
   - एम्बुलेंस/ambulance
   - फॉर्म/form
   Focus on grammar structure, not these terms

3. Mixed Language:
   - If mixing English + Devanagari, check verb structure
   - "Form भरना है" = Hindi (है pattern)
   - "Form भर्नु छ" = Nepali (छ pattern)

Text to analyze: "{text}"

Analysis Steps:
1. Ignore shared/transliterated terms
2. Focus on verb endings and sentence structure
3. Look for definitive grammar patterns
4. For mixed text, prioritize the grammar of main verb

Respond with EXACTLY one word - either 'english', 'hindi', or 'nepali'."""
            
            # Call Qwen through Ollama with optimized parameters
            async with session.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": "qwen2.5:3b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "top_k": 10
                    }
                }
            ) as response:
                result = await response.json()
                detected_lang = result['response'].strip().lower()
                return detected_lang, prompt, result['response']
                
    except Exception as e:
        logger.error(f"Error in language detection: {str(e)}")
        return None, None, None

async def run_tests():
    """Run a series of language detection tests using real domain examples."""
    test_cases = [
        # Homestay Related
        ("पेल्लिंग में अच्छा होमस्टे बताइए", "hindi"),
        ("पेल्लिंग मा राम्रो होमस्टे छ?", "nepali"),
        ("Show me homestays in Pelling", "english"),
        
        # Emergency Services
        ("एम्बुलेंस की जरूरत है", "hindi"),
        ("एम्बुलेन्स चाहियो", "nepali"),
        ("Need urgent medical help", "english"),
        
        # Complaints/Grievances
        ("मेरी शिकायत सुनिए", "hindi"),
        ("मेरो उजुरी सुन्नुहोस्", "nepali"),
        ("I want to file a complaint", "english"),
        
        # Certificate Related
        ("सर्टिफिकेट के लिए कहाँ जाना होगा?", "hindi"),
        ("सर्टिफिकेट को लागि कहाँ जाने?", "nepali"),
        ("Where to apply for certificate?", "english"),
        
        # Ex-gratia Related
        ("बाढ़ से नुकसान हुआ है", "hindi"),
        ("बाढी ले क्षति भयो", "nepali"),
        ("Flood damaged my house", "english"),
        
        # Mixed Language Common in Our Domain
        ("CSC ऑफिस कहाँ है?", "hindi"),
        ("CSC कार्यालय कहाँ छ?", "nepali"),
        ("Form भरने में help चाहिए", "hindi"),
        ("Form भर्न सहयोग चाहिन्छ", "nepali"),
        ("Need help with सरकारी काम", "english")
    ]
    
    print("\n🔍 Testing Language Detection with Domain Data...")
    print("=" * 50)
    
    passed = 0
    total = len(test_cases)
    
    for text, expected in test_cases:
        print(f"\n==============================\nTest Input: {text}")
        detected, prompt, raw_response = await test_language_detection(text)
        print(f"Prompt sent to LLM:\n{prompt}\n")
        print(f"Raw LLM response: {raw_response}")
        print(f"Expected: {expected}")
        print(f"Detected: {detected}")
        result = '✅' if detected == expected else '❌'
        print(f"Result: {result}")
        passed += 1 if detected == expected else 0
    
    accuracy = (passed / total) * 100
    print("\n" + "=" * 50)
    print(f"\n📊 Results:")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Accuracy: {accuracy:.1f}%")

if __name__ == "__main__":
    print("🤖 Testing SmartGov Language Detection with Domain Data (with LLM prompt/response shown)")
    asyncio.run(run_tests()) 