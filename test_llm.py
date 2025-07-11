import aiohttp
import asyncio
import json

async def test_llm():
    # Test language detection
    lang_prompt = """Detect the language of this message. Only respond with 'english', 'hindi', or 'nepali'.
    Message: Need ambulance
    Language:"""
    
    # Test intent detection
    intent_prompt = """Classify the intent of this message. Only respond with one of these intents:
    - help: General help request
    - exgratia_apply: Want to apply for ex-gratia assistance
    - status_check: Want to check application status
    - exgratia_norms: Want to know about ex-gratia norms/rules
    - emergency_medical: Medical emergency (ambulance, etc.)
    - emergency_disaster: Disaster emergency (flood, fire, etc.)
    - other: Any other intent

    Message: Need ambulance
    Language: english
    Intent:"""
    
    async with aiohttp.ClientSession() as session:
        # Test language detection
        print("\nTesting Language Detection:")
        async with session.post('http://localhost:11434/api/generate', 
                              json={'model': 'qwen2', 'prompt': lang_prompt, 'stream': False}) as response:
            result = await response.json()
            print(f"Full Response: {json.dumps(result, indent=2)}")
        
        # Test intent detection
        print("\nTesting Intent Detection:")
        async with session.post('http://localhost:11434/api/generate', 
                              json={'model': 'qwen2', 'prompt': intent_prompt, 'stream': False}) as response:
            result = await response.json()
            print(f"Full Response: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_llm()) 