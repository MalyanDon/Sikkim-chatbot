import aiohttp
import asyncio
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_response(response: str) -> str:
    """Clean the LLM response to handle formatting issues"""
    # Remove any non-alphanumeric characters except underscores
    cleaned = response.strip().lower()
    
    # Remove common prefixes/suffixes
    prefixes = [
        "category:", "intent:", "response:", 
        "the category is", "the intent is",
        "category is", "intent is",
        "this is", "this falls under",
        "the user wants to"
    ]
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    
    # Remove numbers and punctuation
    cleaned = ''.join(c for c in cleaned if not c.isdigit() and c not in '.,!?()[]{}')
    cleaned = cleaned.strip()
    
    # Map similar responses
    mapping = {
        "complaint": "file_complaint",
        "emergency": "emergency_contact",
        "ambulance": "emergency_contact",
        "exgratia": "ex_gratia_apply",
        "ex-gratia": "ex_gratia_apply",
        "compensation": "ex_gratia_apply",
        "muavza": "ex_gratia_apply",
        "मुआवजा": "ex_gratia_apply",
        "क्षतिपूर्ति": "ex_gratia_apply",
        "शिकायत": "file_complaint",
        "उजुरी": "file_complaint",
        "एम्बुलेंस": "emergency_contact",
        "एम्बुलेन्स": "emergency_contact"
    }
    
    # Try exact match first
    if cleaned in ["ex_gratia_apply", "emergency_contact", "file_complaint", "check_status", "other"]:
        return cleaned
        
    # Try mapping
    cleaned_no_space = cleaned.replace("-", "").replace("_", "").replace(" ", "")
    for key, value in mapping.items():
        key_no_space = key.replace("-", "").replace("_", "").replace(" ", "")
        if key_no_space in cleaned_no_space:
            return value
            
    return "other"

async def test_llm_request(text: str) -> dict:
    """Make a request to Ollama LLM"""
    prompt = f"""You are a government services chatbot. Classify the user's request into ONE category.

    IMPORTANT: Look for these key patterns in ANY language (English/Hindi/Nepali):

    1. ex_gratia_apply = User wants compensation/ex-gratia
       Key patterns: compensation, muavza, ex-gratia, मुआवजा, क्षतिपूर्ति
       Examples:
       - "I want compensation for flood damage"
       - "बाढ़ से नुकसान हुआ है, मुआवजा चाहिए"
       - "Muavza chahiye"
       - "Ex-gratia ke liye apply karna hai"
       - "बाढीको क्षतिपूर्ति चाहियो"
    
    2. emergency_contact = User needs emergency numbers
       Key patterns: ambulance, emergency, एम्बुलेंस, एम्बुलेन्स
       Examples:
       - "Need ambulance number"
       - "एम्बुलेंस का नंबर चाहिए"
       - "Ambulance contact urgent"
       - "एम्बुलेन्स नम्बर चाहियो"
    
    3. file_complaint = User wants to file complaint
       Key patterns: complaint, shikayat, शिकायत, उजुरी
       Examples:
       - "File complaint about road"
       - "शिकायत दर्ज करनी है"
       - "Complaint karna hai"
       - "उजुरी दर्ता गर्नु छ"
    
    4. check_status = User wants application status
    5. other = None of the above

    Text: {text}
    
    Respond with ONLY the category name."""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={"model": "qwen", "prompt": prompt, "stream": False}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    result['response'] = clean_response(result['response'])
                    return result
                else:
                    logger.error(f"Request failed with status {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        return None

async def run_test(text: str, expected_category: str, language: str):
    """Run a single test case"""
    print(f"\n{'='*80}")
    print(f"Testing: {text}")
    print(f"Expected Category: {expected_category}")
    print(f"Language: {language}")
    
    result = await test_llm_request(text)
    detected = result['response'].strip().lower() if result else "error"
    
    print(f"\nResult:")
    print(f"✓ Detected: {detected}")
    print(f"✓ Expected: {expected_category}")
    print(f"✓ Match: {'✅' if detected == expected_category else '❌'}")

async def main():
    # Test cases with expected results
    test_cases = [
        # Ex-gratia Application Cases
        {
            "text": "I want to apply for flood damage compensation",
            "category": "ex_gratia_apply",
            "language": "English"
        },
        {
            "text": "बाढ़ से नुकसान हुआ है, मुआवजा चाहिए",
            "category": "ex_gratia_apply",
            "language": "Hindi"
        },
        {
            "text": "Baadh se nuksan hua hai, muavza chahiye",
            "category": "ex_gratia_apply",
            "language": "Romanized Hindi"
        },
        {
            "text": "बाढीको क्षतिपूर्ति को लागि आवेदन गर्न चाहन्छु",
            "category": "ex_gratia_apply",
            "language": "Nepali"
        },
        
        # Emergency Contact Cases
        {
            "text": "I need ambulance contact number urgently",
            "category": "emergency_contact",
            "language": "English"
        },
        {
            "text": "एम्बुलेंस का नंबर चाहिए, इमरजेंसी है",
            "category": "emergency_contact",
            "language": "Hindi"
        },
        {
            "text": "Ambulance ka number chahiye, emergency hai",
            "category": "emergency_contact",
            "language": "Romanized Hindi"
        },
        {
            "text": "एम्बुलेन्स नम्बर चाहियो, आपतकालीन छ",
            "category": "emergency_contact",
            "language": "Nepali"
        },
        
        # Complaint Filing Cases
        {
            "text": "I want to file a complaint about road damage",
            "category": "file_complaint",
            "language": "English"
        },
        {
            "text": "सड़क की खराब स्थिति की शिकायत करनी है",
            "category": "file_complaint",
            "language": "Hindi"
        },
        {
            "text": "Sadak ki kharab sthiti ki shikayat karni hai",
            "category": "file_complaint",
            "language": "Romanized Hindi"
        },
        {
            "text": "सडक बिग्रेको उजुरी दर्ता गर्नु छ",
            "category": "file_complaint",
            "language": "Nepali"
        },
        
        # Mixed Language Cases
        {
            "text": "Ex-gratia ke liye apply karna hai",
            "category": "ex_gratia_apply",
            "language": "Mixed Hindi-English"
        },
        {
            "text": "Ambulance का नंबर urgent चाहिए",
            "category": "emergency_contact",
            "language": "Mixed Hindi-English"
        },
        {
            "text": "Complaint दर्ज करना है road के बारे में",
            "category": "file_complaint",
            "language": "Mixed Hindi-English"
        }
    ]
    
    print("\n🔍 Starting Use Case Testing")
    print("Testing specific user scenarios in multiple languages")
    print(f"Total test cases: {len(test_cases)}")
    
    for test in test_cases:
        await run_test(test["text"], test["category"], test["language"])
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    asyncio.run(main()) 