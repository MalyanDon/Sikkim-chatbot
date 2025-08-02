"""
Configuration management for Sajilo Sewak Chatbot

This module handles all configuration settings for the bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Sajilo Sewak chatbot"""
    
    # Telegram Bot Token
    BOT_TOKEN = "7641958089:AAH2UW5H0EX9pGfE6wZZaURCpkyMHtJK8zw"
    TELEGRAM_BOT_TOKEN = BOT_TOKEN
    
    # Qwen LLM Configuration
    OLLAMA_API_URL = 'http://localhost:11434/api/generate'
    LLM_MODEL = 'qwen2.5:3b'
    USE_LLM = True  # Always use Qwen for language detection
    
    # NC Exgratia API Configuration
    NC_EXGRATIA_API_URL = "https://ncapi.testwebdevcell.pw"
    NC_EXGRATIA_USERNAME = "testbot"
    NC_EXGRATIA_PASSWORD = "testbot123"
    NC_EXGRATIA_ENABLED = True
    
    # Support Information
    SUPPORT_PHONE = os.getenv('SUPPORT_PHONE', '+91-1234567890')
    
    # Google Sheets Configuration
    GOOGLE_SHEETS_API_KEY = "AIzaSyDOGeGFOwaLeRuVEQmbOE4E-YgHsh3OgV0"
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '1-CjYt8jSyK_Id2q4Wn91gZ8cpaH2a2cXdFXFXO5Veus')
    GOOGLE_SHEETS_ENABLED = os.getenv('GOOGLE_SHEETS_ENABLED', 'true').lower() == 'true'  # Enabled
    
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
         **Welcome to Sajilo Sewak Assistance!**

I'm here to help you with disaster relief services. You can:

1⃣ **Ex-Gratia Norms** - Learn about assistance amounts & eligibility
2⃣ **Apply for Ex-Gratia** - Get help with application process
3⃣ **Check Status** - Track your application status

 You can also just tell me what you need in your own words!

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
        
        print(" Configuration validated successfully")
        print(f" Using Qwen ({cls.LLM_MODEL}) for language detection")
        print(f" NC Exgratia API: {' Enabled' if cls.NC_EXGRATIA_ENABLED else ' Disabled'}") 