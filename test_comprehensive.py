import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_language_detection(text: str) -> tuple:
    """Test language detection using Qwen. Returns (detected_lang, prompt, raw_response)"""
    try:
        async with aiohttp.ClientSession() as session:
            prompt = f"""You are the language detection system for SmartGov Assistant, a government services chatbot in Sikkim. Analyze this text and determine if it's English, Hindi, or Nepali.

Key Grammar Patterns:

1. Hindi Markers:
   - Verb endings: है, हैं, था, थी, होगा, करना है
   - Question words: क्या, कैसे, कहाँ
   - Common phrases: मुझे चाहिए, कृपया बताएं
   - Romanized: hai, hain, tha, thi, hoga, karna hai

2. Nepali Markers:
   - Verb endings: छ, छन्, हो, भयो, हुन्छ
   - Question words: के, कसरी, कहाँ
   - Common phrases: मलाई चाहिन्छ, कृपया भन्नुहोस्
   - Romanized: cha, chhan, ho, bhayo, hunchha

3. English Markers:
   - SVO structure
   - Auxiliary verbs: is, are, was, were
   - Question words: what, how, where

Rules:
- For mixed language, identify the dominant language
- Consider both Devanagari and Roman script
- Account for transliterated text
- Look for grammar patterns over individual words
- Handle informal and colloquial usage

Text to analyze: "{text}"

Respond with EXACTLY one word - either 'english', 'hindi', or 'nepali'."""
            
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

async def test_intent_classification(text: str, lang: str) -> tuple:
    """Test intent classification using Qwen. Returns (detected_intent, prompt, raw_response)"""
    try:
        async with aiohttp.ClientSession() as session:
            prompt = f"""You are an intent classifier for SmartGov Assistant, a government services chatbot in Sikkim. Given the user's message in {lang}, classify it into one of these intents:

Available intents:
1. ex_gratia: Compensation/financial assistance for disaster damage
2. check_status: Track application status
3. relief_norms: Questions about relief policies/eligibility
4. emergency: Need urgent help (medical, police, fire)
5. tourism: Tourism/homestay related
6. complaint: File complaint/grievance
7. certificate: Apply for certificates
8. csc: Common Service Center related
9. unknown: None of the above

Examples for each intent:

1. ex_gratia:
   English: "Need compensation for flood damage", "How to apply for ex-gratia"
   Hindi: "बाढ़ से नुकसान हुआ है", "मुआवजा के लिए आवेदन"
   Nepali: "बाढीले क्षति भयो", "क्षतिपूर्ति को लागि निवेदन"
   Romanized Hindi: "Baadh se nuksaan hua hai", "Muavza ke liye aavedan"
   Romanized Nepali: "Baadhi le kshiti bhayo", "Kshitipurti ko lagi nivedan"

2. check_status:
   English: "What's my application status", "Track my claim"
   Hindi: "मेरा आवेदन कहां है", "स्टेटस चेक करना है"
   Nepali: "मेरो निवेदन कहाँ छ", "स्टेटस हेर्नु छ"
   Romanized Hindi: "Mera aavedan kahan hai", "Status check karna hai"
   Romanized Nepali: "Mero nivedan kahan cha", "Status hernu cha"

3. relief_norms:
   English: "How much compensation will I get", "What documents needed"
   Hindi: "कितना मुआवजा मिलेगा", "कौन से दस्तावेज चाहिए"
   Nepali: "कति क्षतिपूर्ति पाउँछु", "कुन कागजात चाहिन्छ"
   Romanized Hindi: "Kitna muavza milega", "Kaun se dastaavez chahiye"
   Romanized Nepali: "Kati kshitipurti paunchhu", "Kun kagajat chahincha"

4. emergency:
   English: "Need ambulance", "Fire emergency"
   Hindi: "एम्बुलेंस चाहिए", "आग लगी है"
   Nepali: "एम्बुलेन्स चाहिन्छ", "आगलागी भयो"
   Romanized Hindi: "Ambulance chahiye", "Aag lagi hai"
   Romanized Nepali: "Ambulance chahincha", "Aaglagi bhayo"

5. tourism:
   English: "Book homestay in Pelling", "Tourist places in Sikkim"
   Hindi: "होमस्टे बुक करना है", "सिक्किम में घूमने की जगह"
   Nepali: "होमस्टे बुक गर्नु छ", "सिक्किमको पर्यटन स्थल"
   Romanized Hindi: "Homestay book karna hai", "Sikkim mein ghumne ki jagah"
   Romanized Nepali: "Homestay book garnu cha", "Sikkimko paryatan sthal"

6. complaint:
   English: "File complaint about road", "Register grievance"
   Hindi: "शिकायत दर्ज करनी है", "उजुरी दर्ज करना है"
   Nepali: "उजुरी दर्ता गर्नु छ", "शिकायत दर्ज गर्नु छ"
   Romanized Hindi: "Shikayat darj karni hai", "Ujuri darj karna hai"
   Romanized Nepali: "Ujuri darta garnu cha", "Shikayat darj garnu cha"

7. certificate:
   English: "Apply for birth certificate", "Need certificate"
   Hindi: "जन्म प्रमाणपत्र के लिए आवेदन", "सर्टिफिकेट चाहिए"
   Nepali: "जन्म प्रमाणपत्र को लागि आवेदन", "प्रमाणपत्र चाहिन्छ"
   Romanized Hindi: "Janm pramaanpatra ke liye aavedan", "Certificate chahiye"
   Romanized Nepali: "Janm pramaanpatra ko lagi aavedan", "Pramaanpatra chahincha"

8. csc:
   English: "Find CSC operator", "CSC office location"
   Hindi: "CSC ऑपरेटर ढूंढना है", "CSC ऑफिस कहाँ है"
   Nepali: "CSC कार्यकर्ता भेट्नु छ", "CSC कार्यालय कहाँ छ"
   Romanized Hindi: "CSC operator dhundna hai", "CSC office kahan hai"
   Romanized Nepali: "CSC karyakarta bhetnu cha", "CSC karyalaya kahan cha"

User message: "{text}"
Language: {lang}

Respond with EXACTLY one of: ex_gratia, check_status, relief_norms, emergency, tourism, complaint, certificate, csc, unknown"""
            
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
                detected_intent = result['response'].strip().lower()
                return detected_intent, prompt, result['response']
                
    except Exception as e:
        logger.error(f"Error in intent classification: {str(e)}")
        return None, None, None

async def run_comprehensive_tests():
    """Run comprehensive tests for all scenarios in all languages"""
    
    # Define test cases for each category
    test_cases = {
        "Ex-Gratia": {
            "english": [
                "How to apply for ex-gratia compensation?",
                "My house was damaged in floods, need help",
                "What is ex-gratia assistance?",
                "Need compensation for crop damage",
                "How much money will I get for flood damage?"
            ],
            "romanized_hindi": [
                "Ex-gratia ke liye kaise apply karna hai?",
                "Mere ghar mein baadh se nuksaan hua hai",
                "Ex-gratia kya hota hai?",
                "Fasal nuksaan ka muavza chahiye",
                "Baadh se kitna paisa milega?"
            ],
            "romanized_nepali": [
                "Ex-gratia ko lagi kasari apply garnu cha?",
                "Mero ghar ma baadhi le kshiti bhayo",
                "Ex-gratia ke ho?",
                "Fasal kshiti ko kshitipurti chahincha",
                "Baadhi le kati paisa paunchha?"
            ]
        },
        "Emergency": {
            "english": [
                "Need ambulance urgently",
                "Call police emergency",
                "Fire broke out in my house",
                "Medical emergency help",
                "Suicide prevention helpline"
            ],
            "romanized_hindi": [
                "Ambulance chahiye jaldi",
                "Police emergency bulao",
                "Mere ghar mein aag lag gayi hai",
                "Medical emergency hai",
                "Suicide prevention helpline"
            ],
            "romanized_nepali": [
                "Ambulance chahincha chito",
                "Police emergency bolaunu",
                "Mero ghar ma aag lagyo",
                "Medical emergency cha",
                "Suicide prevention helpline"
            ]
        },
        "Homestay/Tourism": {
            "english": [
                "Book homestay in Pelling",
                "Show me tourist places in Sikkim",
                "Need accommodation in Gangtok",
                "Best homestay recommendations",
                "Tourist guide services"
            ],
            "romanized_hindi": [
                "Pelling mein homestay book karna hai",
                "Sikkim mein tourist places dikhao",
                "Gangtok mein accommodation chahiye",
                "Best homestay recommendations",
                "Tourist guide services"
            ],
            "romanized_nepali": [
                "Pelling ma homestay book garnu cha",
                "Sikkim ma tourist places dekhaunu",
                "Gangtok ma accommodation chahincha",
                "Best homestay recommendations",
                "Tourist guide services"
            ]
        },
        "Complaints": {
            "english": [
                "File complaint about bad roads",
                "Register grievance against officer",
                "Complain about water supply",
                "Report corruption case",
                "Submit complaint online"
            ],
            "romanized_hindi": [
                "Sadak ki shikayat darj karni hai",
                "Officer ke khilaaf ujuri darj karna hai",
                "Paani supply ki shikayat",
                "Corruption case report karna hai",
                "Online complaint submit karna hai"
            ],
            "romanized_nepali": [
                "Sadak ko ujuri darta garnu cha",
                "Officer ko biruddha shikayat darj garnu cha",
                "Paani supply ko ujuri",
                "Corruption case report garnu cha",
                "Online complaint submit garnu cha"
            ]
        },
        "Certificates": {
            "english": [
                "Apply for birth certificate",
                "Need income certificate",
                "How to get caste certificate?",
                "Certificate verification process",
                "Duplicate certificate application"
            ],
            "romanized_hindi": [
                "Janm pramaanpatra ke liye apply karna hai",
                "Income certificate chahiye",
                "Caste certificate kaise milta hai?",
                "Certificate verification process",
                "Duplicate certificate application"
            ],
            "romanized_nepali": [
                "Janm pramaanpatra ko lagi apply garnu cha",
                "Income certificate chahincha",
                "Caste certificate kasari paunchha?",
                "Certificate verification process",
                "Duplicate certificate application"
            ]
        },
        "CSC Services": {
            "english": [
                "Find CSC operator near me",
                "CSC office timings",
                "CSC services available",
                "CSC operator contact number",
                "CSC center location"
            ],
            "romanized_hindi": [
                "Paas mein CSC operator dhundna hai",
                "CSC office ke timings",
                "CSC services available hain",
                "CSC operator ka contact number",
                "CSC center ka location"
            ],
            "romanized_nepali": [
                "Najik ma CSC operator bhetnu cha",
                "CSC office ko timings",
                "CSC services available cha",
                "CSC operator ko contact number",
                "CSC center ko location"
            ]
        },
        "Status Check": {
            "english": [
                "Check my application status",
                "Track complaint status",
                "Application number status",
                "Certificate status inquiry",
                "Payment status check"
            ],
            "romanized_hindi": [
                "Mere application ka status check karna hai",
                "Complaint ka status track karna hai",
                "Application number ka status",
                "Certificate status inquiry",
                "Payment status check"
            ],
            "romanized_nepali": [
                "Mero application ko status check garnu cha",
                "Complaint ko status track garnu cha",
                "Application number ko status",
                "Certificate status inquiry",
                "Payment status check"
            ]
        }
    }
    
    print(f"\n🤖 COMPREHENSIVE SMARTGOV BOT TESTING")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    total_tests = 0
    passed_lang = 0
    passed_intent = 0
    
    for category, languages in test_cases.items():
        print(f"\n📋 CATEGORY: {category}")
        print("-" * 50)
        
        for lang_type, queries in languages.items():
            print(f"\n🌐 Language Type: {lang_type.upper()}")
            print("-" * 30)
            
            for query in queries:
                total_tests += 1
                print(f"\n🔍 Test #{total_tests}")
                print(f"Query: {query}")
                
                # Test language detection
                detected_lang, lang_prompt, lang_response = await test_language_detection(query)
                expected_lang = "english" if lang_type == "english" else "hindi" if "hindi" in lang_type else "nepali"
                
                print(f"Language Detection:")
                print(f"  Expected: {expected_lang}")
                print(f"  Detected: {detected_lang}")
                print(f"  LLM Response: {lang_response}")
                print(f"  Result: {'✅' if detected_lang == expected_lang else '❌'}")
                
                if detected_lang == expected_lang:
                    passed_lang += 1
                
                # Test intent classification
                detected_intent, intent_prompt, intent_response = await test_intent_classification(query, detected_lang or expected_lang)
                
                print(f"Intent Classification:")
                print(f"  Detected Intent: {detected_intent}")
                print(f"  LLM Response: {intent_response}")
                
                # Validate intent based on category
                valid_intents = {
                    "Ex-Gratia": ["ex_gratia", "relief_norms"],
                    "Emergency": ["emergency"],
                    "Homestay/Tourism": ["tourism"],
                    "Complaints": ["complaint"],
                    "Certificates": ["certificate"],
                    "CSC Services": ["csc"],
                    "Status Check": ["check_status"]
                }
                
                is_valid_intent = detected_intent in valid_intents.get(category, [])
                print(f"  Valid for category: {'✅' if is_valid_intent else '❌'}")
                
                if is_valid_intent:
                    passed_intent += 1
                
                print("-" * 40)
    
    # Final results
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Language Detection Accuracy: {(passed_lang/total_tests)*100:.1f}% ({passed_lang}/{total_tests})")
    print(f"Intent Classification Accuracy: {(passed_intent/total_tests)*100:.1f}% ({passed_intent}/{total_tests})")
    print(f"Overall System Accuracy: {((passed_lang + passed_intent)/(total_tests*2))*100:.1f}%")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive SmartGov Bot Testing...")
    asyncio.run(run_comprehensive_tests()) 