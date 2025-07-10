#!/usr/bin/env python3
"""
SajiloSewa Ex-Gratia Assistance Chatbot
Working load balanced version for disaster relief services
"""

import asyncio
import aiohttp
import json
import time
import logging
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Fix for Windows event loop issues
nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SajiloSewaBot:
    def __init__(self):
        # Bot configuration
        self.BOT_TOKEN = "7641958089:AAH2UW5H0EX9pGfE6wZZaURCpkyMHtJK8zw"
        
        # Model configuration - using the best performing model
        self.MODEL_NAME = "qwen2.5:3b"
        self.LLM_ENDPOINT = "http://localhost:11434/api/generate"
        
        # Optimized system prompt
        self.system_prompt = """Detect language and intent for Sikkim disaster relief bot.

Languages: English, Hindi, Nepali, Bengali, Assamese
Intents: apply_assistance, check_status, get_info, document_help, complaint, other

Respond in JSON: {"language": "detected_language", "intent": "detected_intent", "confidence": 0.95}"""
        
        # Performance tracking
        self.request_count = 0
        self.response_times = []
        
        # Session will be created when needed
        self.session = None

    async def get_session(self):
        """Get or create HTTP session"""
        if self.session is None:
            # Create connector without event loop dependency
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=50,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self.session

    async def detect_intent_language(self, message):
        """Detect intent and language using Qwen2.5:3B"""
        session = await self.get_session()
        
        full_prompt = f"{self.system_prompt}\n\nUser: {message}\nResponse:"
        
        payload = {
            "model": self.MODEL_NAME,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 50
            }
        }
        
        start_time = time.time()
        
        try:
            async with session.post(self.LLM_ENDPOINT, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    response_time = time.time() - start_time
                    
                    # Track performance
                    self.request_count += 1
                    self.response_times.append(response_time)
                    
                    # Parse response
                    return self.parse_llm_response(result.get('response', ''), response_time)
                else:
                    logger.error(f"LLM API returned status {response.status}")
                    return {"language": "Unknown", "intent": "other", "confidence": 0.0, "response_time": 0}
                    
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            return {"language": "Unknown", "intent": "other", "confidence": 0.0, "response_time": 0}

    def parse_llm_response(self, response_text, response_time):
        """Parse LLM response and extract language/intent"""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                parsed = json.loads(json_str)
                
                return {
                    "language": parsed.get("language", "Unknown"),
                    "intent": parsed.get("intent", "other"),
                    "confidence": parsed.get("confidence", 0.0),
                    "response_time": response_time
                }
            else:
                return self.simple_parse(response_text, response_time)
                
        except json.JSONDecodeError:
            return self.simple_parse(response_text, response_time)

    def simple_parse(self, response_text, response_time):
        """Simple parsing fallback"""
        response_lower = response_text.lower()
        
        # Language detection
        language = "Unknown"
        if any(word in response_lower for word in ["hindi", "हिंदी"]):
            language = "Hindi"
        elif any(word in response_lower for word in ["nepali", "नेपाली"]):
            language = "Nepali"
        elif any(word in response_lower for word in ["bengali", "বাংলা"]):
            language = "Bengali"
        elif any(word in response_lower for word in ["assamese", "অসমীয়া"]):
            language = "Assamese"
        elif any(word in response_lower for word in ["english"]):
            language = "English"
        
        # Intent detection
        intent = "other"
        if any(word in response_lower for word in ["apply", "assistance", "help"]):
            intent = "apply_assistance"
        elif any(word in response_lower for word in ["status", "check"]):
            intent = "check_status"
        elif any(word in response_lower for word in ["info", "information"]):
            intent = "get_info"
        elif any(word in response_lower for word in ["document", "documents"]):
            intent = "document_help"
        
        return {
            "language": language,
            "intent": intent,
            "confidence": 0.7,
            "response_time": response_time
        }

    def get_response_message(self, intent, language):
        """Get appropriate response based on intent and language"""
        responses = {
            "apply_assistance": {
                "English": "To apply for disaster relief assistance, please visit your nearest government office or call our helpline at 1800-XXX-XXXX. You'll need to provide identity proof, address proof, and damage assessment report.",
                "Hindi": "आपदा राहत सहायता के लिए आवेदन करने के लिए, कृपया अपने निकटतम सरकारी कार्यालय में जाएं या हमारी हेल्पलाइन 1800-XXX-XXXX पर कॉल करें। आपको पहचान प्रमाण, पता प्रमाण और क्षति मूल्यांकन रिपोर्ट प्रदान करनी होगी।",
                "Nepali": "प्रकोप राहत सहायताको लागि आवेदन गर्न, कृपया आफ्नो नजिकैको सरकारी कार्यालयमा जानुहोस् वा हाम्रो हेल्पलाइन 1800-XXX-XXXX मा कल गर्नुहोस्। तपाईंले पहिचान प्रमाण, ठेगाना प्रमाण र क्षति मूल्यांकन रिपोर्ट प्रदान गर्नुपर्छ।",
                "Bengali": "দুর্যোগ ত্রাণ সহায়তার জন্য আবেদন করতে, অনুগ্রহ করে আপনার নিকটতম সরকারি অফিসে যান বা আমাদের হেল্পলাইন 1800-XXX-XXXX এ কল করুন। আপনাকে पहचान प्रमाण, ঠিকানা প্রমাণ এবং ক্ষয়ক্ষতি মূল্যায়ন রিপোর্ট প্রদান করতে হবে।",
                "Assamese": "দুৰ্যোগ ত্ৰাণৰ বাবে আবেদন কৰিবলৈ, অনুগ্ৰহ কৰি আপোনাৰ ওচৰৰ চৰকাৰী কাৰ্যালয়লৈ যাওক বা আমাৰ হেল্পলাইন 1800-XXX-XXXX লৈ কল কৰক। আপুনি পৰিচয় প্ৰমাণ, ঠিকনা প্ৰমাণ আৰু ক্ষতি মূল্যায়ন প্ৰতিবেদন আগবঢ়াব লাগিব।"
            },
            "check_status": {
                "English": "To check your application status, please provide your application number or call our helpline at 1800-XXX-XXXX. You can also check online at our official website.",
                "Hindi": "अपने आवेदन की स्थिति जांचने के लिए, कृपया अपना आवेदन संख्या प्रदान करें या हमारी हेल्पलाइन 1800-XXX-XXXX पर कॉल करें। आप हमारी आधिकारिक वेबसाइट पर ऑनलाइन भी जांच सकते हैं।",
                "Nepali": "आफ्नो आवेदनको स्थिति जाँच गर्न, कृपया आफ्नो आवेदन नम्बर प्रदान गर्नुहोस् वा हाम्रो हेल्पलाइन 1800-XXX-XXXX मा कल गर्नुहोस्। तपाईं हाम्रो आधिकारिक वेबसाइटमा अनलाइन पनि जाँच गर्न सक्नुहुन्छ।",
                "Bengali": "আপনার আবেদনের অবস্থা জানতে, অনুগ্রহ করে আপনার আবেদন নম্বর প্রদান করুন বা আমাদের হেল্পলাইন 1800-XXX-XXXX এ কল করুন। আপনি আমাদের সরকারি ওয়েবসাইটে অনলাইনেও দেখতে পারেন।",
                "Assamese": "আপোনাৰ আবেদনৰ স্থিতি পৰীক্ষা কৰিবলৈ, অনুগ্ৰহ কৰি আপোনাৰ আবেদন নম্বৰ আগবঢ়াওক বা আমাৰ হেল্পলাইন 1800-XXX-XXXX লৈ কল কৰক। আপুনি আমাৰ চৰকাৰী ৱেবছাইটতো অনলাইনত পৰীক্ষা কৰিব পাৰে।"
            },
            "get_info": {
                "English": "The Sikkim Government Disaster Relief Ex-Gratia Assistance Program provides financial support to citizens affected by natural disasters. For more information, visit our official website or call 1800-XXX-XXXX.",
                "Hindi": "सिक्किम सरकार आपदा राहत अनुग्रह सहायता कार्यक्रम प्राकृतिक आपदाओं से प्रभावित नागरिकों को वित्तीय सहायता प्रदान करता है। अधिक जानकारी के लिए, हमारी आधिकारिक वेबसाइट पर जाएं या 1800-XXX-XXXX पर कॉल करें।",
                "Nepali": "सिक्किम सरकार प्रकोप राहत अनुग्रह सहायता कार्यक्रमले प्राकृतिक प्रकोपबाट प्रभावित नागरिकहरूलाई आर्थिक सहायता प्रदान गर्छ। थप जानकारीको लागि, हाम्रो आधिकारिक वेबसाइटमा जानुहोस् वा 1800-XXX-XXXX मा कल गर्नुहोस्।",
                "Bengali": "সিকিম সরকারের দুর্যোগ ত্রাণ অনুগ্রহ সহায়তা কর্মসূচি প্রাকৃতিক দুর্যোগে ক্ষতিগ্রস্ত নাগরিকদের আর্থিক সহায়তা প্রদান করে। আরও তথ্যের জন্য, আমাদের সরকারি ওয়েবসাইটে যান বা 1800-XXX-XXXX এ কল করুন।",
                "Assamese": "সিকিম চৰকাৰৰ দুৰ্যোগ ত্ৰাণ অনুগ্ৰহ সহায়তা কাৰ্যসূচীয়ে প্ৰাকৃতিক দুৰ্যোগত ক্ষতিগ্ৰস্ত নাগৰিকসকলক আৰ্থিক সহায়তা আগবঢ়ায়। অধিক তথ্যৰ বাবে, আমাৰ চৰকাৰী ৱেবছাইটলৈ যাওক বা 1800-XXX-XXXX লৈ কল কৰক।"
            },
            "document_help": {
                "English": "Required documents for disaster relief application: 1) Aadhaar Card, 2) Address Proof, 3) Damage Assessment Report, 4) Bank Account Details, 5) Photographs of damage. Please visit your nearest government office for assistance.",
                "Hindi": "आपदा राहत आवेदन के लिए आवश्यक दस्तावेज: 1) आधार कार्ड, 2) पता प्रमाण, 3) क्षति मूल्यांकन रिपोर्ट, 4) बैंक खाता विवरण, 5) क्षति की तस्वीरें। सहायता के लिए कृपया अपने निकटतम सरकारी कार्यालय में जाएं।",
                "Nepali": "प्रकोप राहत आवेदनको लागि आवश्यक कागजातहरू: 1) आधार कार्ड, 2) ठेगाना प्रमाण, 3) क्षति मूल्यांकन रिपोर्ट, 4) बैंक खाता विवरण, 5) क्षतिको तस्विरहरू। सहायताको लागि कृपया आफ्नो नजिकैको सरकारी कार्यालयमा जानुहोस्।",
                "Bengali": "দুর্যোগ ত্রাণ আবেদনের জন্য প্রয়োজনীয় নথি: 1) আধার কার্ড, 2) ঠিকানা প্রমাণ, 3) ক্ষয়ক্ষতি মূল্যায়ন রিপোর্ট, 4) ব্যাংক অ্যাকাউন্টের বিবরণ, 5) ক্ষতির ছবি। সাহায্যের জন্য অনুগ্রহ করে আপনার নিকটতম সরকারি অফিসে যান।",
                "Assamese": "দুৰ্যোগ ত্ৰাণ আবেদনৰ বাবে প্ৰয়োজনীয় নথি: 1) আধাৰ কাৰ্ড, 2) ঠিকনা প্ৰমাণ, 3) ক্ষতি মূল্যায়ন প্ৰতিবেদন, 4) বেংক একাউণ্টৰ বিবৰণ, 5) ক্ষতিৰ ছবি। সহায়তাৰ বাবে অনুগ্ৰহ কৰি আপোনাৰ ওচৰৰ চৰকাৰী কাৰ্যালয়লৈ যাওক।"
            }
        }
        
        # Get response for intent and language
        intent_responses = responses.get(intent, responses["get_info"])
        response = intent_responses.get(language, intent_responses["English"])
        
        return response

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        try:
            user_message = update.message.text
            user_id = update.message.from_user.id
            
            logger.info(f"Processing message from user {user_id}: {user_message[:50]}...")
            
            # Detect intent and language
            result = await self.detect_intent_language(user_message)
            
            # Get appropriate response
            response_message = self.get_response_message(result["intent"], result["language"])
            
            # Add performance info to response
            performance_info = f"\n\n⏱️ Response time: {result['response_time']:.2f}s"
            final_response = response_message + performance_info
            
            # Send response
            await update.message.reply_text(final_response)
            
            logger.info(f"Response sent to user {user_id} in {result['response_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text("Sorry, I'm experiencing technical difficulties. Please try again later.")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """🙏 **Welcome to SajiloSewa Ex-Gratia Assistance!**

I'm here to help you with disaster relief services. You can:

1️⃣ **Ex-Gratia Norms** - Learn about assistance amounts & eligibility
2️⃣ **Apply for Ex-Gratia** - Get help with application process
3️⃣ **Check Status** - Track your application status

💬 You can also just tell me what you need in your own words!

Please send me your message in any language (English, Hindi, Nepali, Bengali, Assamese).

/help - Show this message
/status - Check bot performance

How can I assist you today?"""
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🆘 **SajiloSewa Ex-Gratia Assistance Help**

**Available Commands:**
• `/start` - Start the bot and see main menu
• `/help` - Show this help message
• `/status` - Check bot performance

**How to Use:**
1️⃣ **Natural Language**: Just type what you need
2️⃣ **Direct Questions**: Ask specific questions

**Examples:**
• "How much money can I get for house damage?"
• "What documents do I need to apply?"
• "Help me apply for disaster relief"

**Support Contact:**
📞 Helpline: 1077
📞 Phone: +91-1234567890
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - show bot performance"""
        if self.response_times:
            avg_time = sum(self.response_times) / len(self.response_times)
            min_time = min(self.response_times)
            max_time = max(self.response_times)
            
            status_message = f"""🤖 **SajiloSewa Bot Performance Status:**

📊 Requests Processed: {self.request_count}
⏱️ Average Response Time: {avg_time:.2f}s
⚡ Fastest Response: {min_time:.2f}s
🐌 Slowest Response: {max_time:.2f}s
🎯 Model: {self.MODEL_NAME} (Qwen2.5:3B)
🏛️ Service: Ex-Gratia Disaster Relief"""
        else:
            status_message = "🤖 **SajiloSewa Ex-Gratia Assistant** is ready and waiting to help users!"
        
        await update.message.reply_text(status_message, parse_mode='Markdown')

    async def run(self):
        """Run the bot"""
        logger.info("Starting SajiloSewa Ex-Gratia Assistance Bot...")
        
        # Create application
        application = Application.builder().token(self.BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Start the bot
        logger.info("SajiloSewa Bot started successfully!")
        print("🤖 SajiloSewa Ex-Gratia Assistance Bot is running...")
        print("📱 Bot can be accessed via the provided Telegram link")
        print("✅ Bot is active and ready to help users!")
        
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main function"""
    bot = SajiloSewaBot()
    
    # Run the bot (nest_asyncio handles event loop issues)
    asyncio.run(bot.run())

if __name__ == "__main__":
    main() 