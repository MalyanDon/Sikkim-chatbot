"""
LLM interaction handler for the SmartGov chatbot
"""
import aiohttp
import logging
from typing import Optional, Dict, Any
from prompts import (
    LANGUAGE_DETECTION_PROMPT,
    INTENT_CLASSIFICATION_PROMPT,
    RESPONSE_GENERATION_PROMPT
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMHandler:
    """Handles all LLM interactions for the chatbot"""
    
    def __init__(self, endpoint: str = "http://localhost:11434/api/generate", model: str = "qwen"):
        """Initialize the LLM handler
        
        Args:
            endpoint: Ollama API endpoint
            model: Model name to use
        """
        self.endpoint = endpoint
        self.model = model
        logger.info(f"🤖 LLM Handler initialized with model: {model}")

    async def _make_llm_request(self, prompt: str) -> Optional[str]:
        """Make a request to the LLM
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM's response or None if request failed
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '').strip().lower()
                    else:
                        logger.error(f"LLM request failed with status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error making LLM request: {str(e)}")
            return None

    def _clean_response(self, response: str) -> str:
        """Clean and validate LLM response
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned response string
        """
        if not response:
            return ''
            
        # Remove any explanations or additional text
        response = response.split('\n')[0].strip().lower()
        
        # Remove punctuation and special characters
        response = ''.join(c for c in response if c.isalnum() or c in ['_', '-'])
        
        return response

    async def detect_language(self, text: str) -> str:
        """Detect the language of the input text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Detected language ('english', 'hindi', or 'nepali')
        """
        prompt = LANGUAGE_DETECTION_PROMPT.format(text=text)
        response = await self._make_llm_request(prompt)
        
        if not response:
            logger.warning("Language detection failed, defaulting to 'english'")
            return 'english'
            
        cleaned = self._clean_response(response)
        
        # Validate response
        if cleaned in ['english', 'hindi', 'nepali']:
            logger.info(f"Language detected: {cleaned}")
            return cleaned
        else:
            logger.warning(f"Invalid language detection response: {cleaned}, defaulting to 'english'")
            return 'english'

    async def classify_intent(self, text: str, lang: str) -> str:
        """Classify the intent of the input text
        
        Args:
            text: Input text to analyze
            lang: Detected language of the text
            
        Returns:
            Classified intent
        """
        prompt = INTENT_CLASSIFICATION_PROMPT.format(text=text, lang=lang)
        response = await self._make_llm_request(prompt)
        
        if not response:
            logger.warning("Intent classification failed, defaulting to 'unknown'")
            return 'unknown'
            
        cleaned = self._clean_response(response)
        
        # Validate response
        valid_intents = ['ex_gratia', 'check_status', 'relief_norms', 'emergency', 'tourism', 'unknown']
        if cleaned in valid_intents:
            logger.info(f"Intent classified: {cleaned}")
            return cleaned
        else:
            logger.warning(f"Invalid intent classification response: {cleaned}, defaulting to 'unknown'")
            return 'unknown'

    async def generate_response(
        self,
        intent: str,
        lang: str,
        workflow: str = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate a natural language response
        
        Args:
            intent: Classified intent
            lang: User's language
            workflow: Current workflow state (optional)
            context: Additional context (optional)
            
        Returns:
            Generated response text
        """
        prompt = RESPONSE_GENERATION_PROMPT.format(
            intent=intent,
            lang=lang,
            workflow=workflow or 'none',
            context=str(context or {})
        )
        
        response = await self._make_llm_request(prompt)
        
        if not response:
            logger.warning("Response generation failed, using fallback response")
            # Return a simple fallback response in the appropriate language
            if lang == 'hindi':
                return "क्षमा करें, मैं अभी उत्तर नहीं दे सकता। कृपया मेनू से चुनें।"
            elif lang == 'nepali':
                return "क्षमा गर्नुहोस्, म अहिले जवाफ दिन सक्दिन। कृपया मेनुबाट चयन गर्नुहोस्।"
            else:
                return "Sorry, I couldn't generate a response. Please select from the menu."
                
        return response  # No cleaning needed for generated responses

    def is_available(self) -> bool:
        """Check if LLM service is available
        
        Returns:
            True if LLM is available, False otherwise
        """
        try:
            import requests
            response = requests.get(self.endpoint.replace('/api/generate', '/api/tags'))
            return response.status_code == 200
        except:
            return False 