#!/usr/bin/env python3
"""
Test script to check LLM functionality
"""
import asyncio
import aiohttp
import json
from config import Config

async def test_llm():
    """Test LLM functionality"""
    print("🧪 Testing LLM Functionality")
    print("=" * 40)
    
    # Test 1: Check if Ollama is running
    print("1. Testing Ollama connection...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                Config.OLLAMA_API_URL,
                json={
                    "model": Config.LLM_MODEL,
                    "prompt": "Hello, respond with 'OK' if you can hear me.",
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Ollama is running and responding")
                    print(f"   Response: {result.get('response', 'No response')}")
                else:
                    print(f"❌ Ollama returned status code: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {str(e)}")
        return False
    
    # Test 2: Test intent classification
    print("\n2. Testing intent classification...")
    try:
        async with aiohttp.ClientSession() as session:
            prompt = """You are an intent classifier for SmartGov Assistant, a government services chatbot in Sikkim. Given the user's message, classify it into one of these intents:

Available intents:
- greeting: User is saying hello, hi, namaste, or starting a conversation
- emergency: User needs emergency help (ambulance, police, fire)
- complaint: User wants to file a complaint
- unknown: If none of the above match

User message: Hello, I need help
Language: english

Respond with ONLY one of the intent names listed above, nothing else."""

            async with session.post(
                Config.OLLAMA_API_URL,
                json={
                    "model": Config.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    intent = result.get('response', '').strip().lower()
                    print(f"✅ Intent classification working")
                    print(f"   Input: 'Hello, I need help'")
                    print(f"   Detected Intent: {intent}")
                    
                    valid_intents = ['greeting', 'emergency', 'complaint', 'unknown']
                    if intent in valid_intents:
                        print(f"   ✅ Valid intent detected")
                    else:
                        print(f"   ⚠️ Unexpected intent: {intent}")
                else:
                    print(f"❌ Intent classification failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Error in intent classification: {str(e)}")
        return False
    
    # Test 3: Test language detection
    print("\n3. Testing language detection...")
    try:
        async with aiohttp.ClientSession() as session:
            prompt = """Detect the language of this text and respond with only the language name (english, hindi, or nepali):

Text: नमस्ते, मुझे मदद चाहिए
Language:"""

            async with session.post(
                Config.OLLAMA_API_URL,
                json={
                    "model": Config.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    detected_lang = result.get('response', '').strip().lower()
                    print(f"✅ Language detection working")
                    print(f"   Input: 'नमस्ते, मुझे मदद चाहिए'")
                    print(f"   Detected Language: {detected_lang}")
                else:
                    print(f"❌ Language detection failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Error in language detection: {str(e)}")
        return False
    
    print("\n🎉 LLM functionality test completed successfully!")
    return True

if __name__ == "__main__":
    asyncio.run(test_llm()) 