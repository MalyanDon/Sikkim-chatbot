import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_llm_working():
    """Test if LLM is working properly"""
    
    test_cases = [
        ("How to apply for ex-gratia?", "english", "ex_gratia"),
        ("Mereko apply krna hain ex gratia", "hindi", "ex_gratia"),
        ("Need ambulance urgently", "english", "emergency"),
        ("Ambulance chahiye jaldi", "hindi", "emergency"),
        ("Book homestay in Pelling", "english", "tourism"),
        ("Pelling mein homestay book karna hai", "hindi", "tourism")
    ]
    
    print("🧪 TESTING LLM FUNCTIONALITY")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            for i, (text, expected_lang, expected_intent) in enumerate(test_cases, 1):
                print(f"\n🔍 Test #{i}: {text}")
                
                # Test language detection
                lang_prompt = f"""Analyze this text and determine if it's English, Hindi, or Nepali.
                Text to analyze: "{text}"
                Respond with EXACTLY one word - either 'english', 'hindi', or 'nepali'."""
                
                print(f"🌐 Language Detection Prompt: {lang_prompt}")
                
                async with session.post(
                    'http://localhost:11434/api/generate',
                    json={
                        "model": "qwen2.5:3b",
                        "prompt": lang_prompt,
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        detected_lang = result['response'].strip().lower()
                        print(f"🌐 Language Detection Response: {detected_lang}")
                        print(f"🌐 Expected: {expected_lang} | Detected: {detected_lang} | {'✅' if detected_lang == expected_lang else '❌'}")
                    else:
                        print(f"❌ Language detection failed: {response.status}")
                
                # Test intent classification
                intent_prompt = f"""You are an intent classifier for SmartGov Assistant. Classify this message into one intent:
                Available intents: ex_gratia, emergency, tourism, complaint, certificate, csc, check_status, relief_norms, unknown
                
                User message: "{text}"
                Language: {detected_lang if 'detected_lang' in locals() else expected_lang}
                
                Respond with EXACTLY one intent name."""
                
                print(f"🎯 Intent Classification Prompt: {intent_prompt}")
                
                async with session.post(
                    'http://localhost:11434/api/generate',
                    json={
                        "model": "qwen2.5:3b",
                        "prompt": intent_prompt,
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        detected_intent = result['response'].strip().lower()
                        print(f"🎯 Intent Classification Response: {detected_intent}")
                        print(f"🎯 Expected: {expected_intent} | Detected: {detected_intent} | {'✅' if detected_intent == expected_intent else '❌'}")
                    else:
                        print(f"❌ Intent classification failed: {response.status}")
                
                print("-" * 50)
                
    except Exception as e:
        print(f"❌ Error testing LLM: {str(e)}")
        return False
    
    print("\n✅ LLM Testing Complete!")
    return True

if __name__ == "__main__":
    asyncio.run(test_llm_working()) 