"""
Configuration management for SmartGov Ex-Gratia Chatbot

This module handles all configuration settings for the bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the SmartGov chatbot"""
    
    # Telegram Bot Token
    BOT_TOKEN = "7641958089:AAH2UW5H0EX9pGfE6wZZaURCpkyMHtJK8zw"
    TELEGRAM_BOT_TOKEN = BOT_TOKEN  # Use the token directly instead of env var
    
    # Ollama LLM Configuration
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
    USE_LLM = os.getenv('USE_LLM', 'false').lower() == 'true'
    LLM_MODEL = os.getenv('LLM_MODEL', 'qwen2.5:3b')
    
    # Support Information
    SUPPORT_PHONE = os.getenv('SUPPORT_PHONE', '+91-1234567890')
    
    # Debug Mode
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Data Paths
    DATA_DIR = 'data'
    EXGRATIA_NORMS_FILE = os.path.join(DATA_DIR, 'info_opt1.txt')
    APPLICATION_PROCEDURE_FILE = os.path.join(DATA_DIR, 'info_opt2.txt')
    STATUS_CSV_FILE = os.path.join(DATA_DIR, 'status.csv')
    SUBMISSION_CSV_FILE = os.path.join(DATA_DIR, 'submission.csv')
    
    # Bot Messages
    WELCOME_MESSAGE = """
🏛️ **Welcome to SmartGov Ex-Gratia Assistance!**

I'm here to help you with disaster relief services. You can:

1️⃣ **Ex-Gratia Norms** - Learn about assistance amounts & eligibility
2️⃣ **Apply for Ex-Gratia** - Get help with application process
3️⃣ **Check Status** - Track your application status

💬 You can also just tell me what you need in your own words!

How can I assist you today?
"""
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required in .env file")
        
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR)
            print(f"Created data directory: {cls.DATA_DIR}")
        
        print("✅ Configuration validated successfully")
        if cls.USE_LLM:
            print(f"🤖 Running in LLM mode with {cls.LLM_MODEL}") 