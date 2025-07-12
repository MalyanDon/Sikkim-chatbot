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
    cleaned = ''.join(c.lower() for c in response if c.isalnum() or c == '_')
    
    # Handle cases where response includes explanation
    if "\n" in cleaned:
        cleaned = cleaned.split("\n")[0]
    
    # Map variations to standard format
    intent_mapping = {
        "checkstatus": "check_status",
        "exgratia": "ex_gratia",
        "reliefnorms": "relief_norms",
        "check.status": "check_status",
        "ex.gratia": "ex_gratia",
        "relief.norms": "relief_norms",
        "check-status": "check_status",
        "ex-gratia": "ex_gratia",
        "relief-norms": "relief_norms",
        "reliefnorms": "relief_norms",
        "reliefnorm": "relief_norms",
        "relief_norm": "relief_norms",
        "relief_": "relief_norms",
        "relief": "relief_norms"
    }
    
    # Try exact match first
    if cleaned in ["english", "hindi", "ex_gratia", "check_status", "relief_norms"]:
        return cleaned
        
    # Try mapping without spaces/underscores
    no_space = cleaned.replace(" ", "").replace("_", "")
    for key, value in intent_mapping.items():
        if no_space == key.replace("_", ""):
            return value
            
    return cleaned

async def test_llm_request(text: str, test_type: str = "language") -> dict:
    """Make a request to Ollama LLM"""
    if test_type == "language":
        prompt = f"""Detect language: English or Hindi?
        Rules:
        - If ANY Hindi words (Devanagari or Roman) -> 'hindi'
        - If ONLY English words -> 'english'
        - If unsure -> 'english'
        
        Text: {text}
        
        Respond: 'english' or 'hindi' only."""
    else:
        prompt = f"""Classify intent as: ex_gratia, check_status, or relief_norms
        
        - ex_gratia = apply for/get compensation
        - check_status = check application status
        - relief_norms = ask about compensation rules/amounts
        
        Text: {text}
        
        Respond with EXACT match: ex_gratia, check_status, or relief_norms"""

    print(f"\nDEBUG: Sending to LLM:")
    print(f"Text: {text}")
    print(f"Prompt: {prompt}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={"model": "qwen", "prompt": prompt, "stream": False}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"DEBUG: Raw LLM Response: {result}")
                    result['response'] = clean_response(result['response'])
                    print(f"DEBUG: Cleaned Response: {result['response']}")
                    return result
                else:
                    logger.error(f"Request failed with status {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        return None

async def run_test(text: str, expected_lang: str, expected_intent: str):
    """Run a single test case"""
    print(f"\n{'='*80}")
    print(f"Testing: {text}")
    print(f"Expected: Language={expected_lang}, Intent={expected_intent}")
    
    # Test language detection
    lang_result = await test_llm_request(text, "language")
    detected_lang = lang_result['response'].strip().lower() if lang_result else "error"
    print(f"\nLanguage Detection:")
    print(f"✓ Detected: {detected_lang}")
    print(f"✓ Expected: {expected_lang}")
    print(f"✓ Match: {'✅' if detected_lang == expected_lang else '❌'}")
    
    # Test intent detection
    intent_result = await test_llm_request(text, "intent")
    detected_intent = intent_result['response'].strip().lower() if intent_result else "error"
    print(f"\nIntent Detection:")
    print(f"✓ Detected: {detected_intent}")
    print(f"✓ Expected: {expected_intent}")
    print(f"✓ Match: {'✅' if detected_intent == expected_intent else '❌'}")

async def main():
    # Test cases with expected results
    test_cases = [
        # English tests
        {
            "text": "I want to apply for flood damage compensation",
            "lang": "english",
            "intent": "ex_gratia"
        },
        {
            "text": "What is the status of my application EX202412345",
            "lang": "english",
            "intent": "check_status"
        },
        {
            "text": "How much compensation will I get for house damage",
            "lang": "english",
            "intent": "relief_norms"
        },
        
        # Hindi tests (Devanagari)
        {
            "text": "बाढ़ से नुकसान के लिए मुआवजा चाहिए",
            "lang": "hindi",
            "intent": "ex_gratia"
        },
        {
            "text": "मेरे आवेदन की स्थिति क्या है",
            "lang": "hindi",
            "intent": "check_status"
        },
        {
            "text": "मकान के नुकसान के लिए कितना मुआवजा मिलेगा",
            "lang": "hindi",
            "intent": "relief_norms"
        },
        
        # Romanized Hindi tests
        {
            "text": "Mujhe muavza chahiye ghar ke nuksan ke liye",
            "lang": "hindi",
            "intent": "ex_gratia"
        },
        {
            "text": "Mera application status kya hai",
            "lang": "hindi",
            "intent": "check_status"
        },
        {
            "text": "Kitna paisa milega crop damage ke liye",
            "lang": "hindi",
            "intent": "relief_norms"
        },
        
        # Mixed language tests
        {
            "text": "Status check karna hai application ka",
            "lang": "hindi",
            "intent": "check_status"
        },
        {
            "text": "Ex-gratia के लिए apply करना है",
            "lang": "hindi",
            "intent": "ex_gratia"
        },
        {
            "text": "Relief norms क्या हैं damage के लिए",
            "lang": "hindi",
            "intent": "relief_norms"
        }
    ]
    
    print("\n🔍 Starting Comprehensive Bot Testing")
    print("Testing language detection and intent classification")
    print(f"Total test cases: {len(test_cases)}")
    
    for test in test_cases:
        await run_test(test["text"], test["lang"], test["intent"])
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    asyncio.run(main()) 