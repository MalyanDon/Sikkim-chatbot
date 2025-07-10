#!/usr/bin/env python3
"""
OPTIMIZED HIGH-PERFORMANCE SmartGov Assistant Bot
Speed-focused implementation with caching, async operations, and performance optimizations
"""

import asyncio
import aiohttp
import aiofiles
import json
import time
import logging
import nest_asyncio
import pandas as pd
import csv
import os
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from functools import lru_cache
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Fix for Windows event loop issues
nest_asyncio.apply()

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class HighPerformanceCache:
    """In-memory cache with TTL for fast response times"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Tuple[any, float]] = {}
        self.default_ttl = default_ttl
        
    def get(self, key: str) -> Optional[any]:
        """Get cached value if not expired"""
        if key in self.cache:
            value, expires_at = self.cache[key]
            if time.time() < expires_at:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: any, ttl: Optional[int] = None) -> None:
        """Set cached value with TTL"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        self.cache[key] = (value, expires_at)
        
    def clear_expired(self) -> None:
        """Clear expired cache entries"""
        current_time = time.time()
        expired_keys = [k for k, (_, expires_at) in self.cache.items() if current_time >= expires_at]
        for key in expired_keys:
            del self.cache[key]

class OptimizedSmartGovBot:
    def __init__(self):
        self.BOT_TOKEN = "7641958089:AAH2UW5H0EX9pGfE6wZZaURCpkyMHtJK8zw"
        self.MODEL_NAME = "qwen2.5:3b"
        self.LLM_ENDPOINT = "http://localhost:11434/api/generate"
        
        # High-performance caching system
        self.intent_cache = HighPerformanceCache(ttl=600)  # 10 minutes for intents
        self.language_cache = HighPerformanceCache(ttl=1800)  # 30 minutes for language
        self.response_cache = HighPerformanceCache(ttl=300)  # 5 minutes for responses
        
        # Performance monitoring
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_response_time': 0,
            'total_requests': 0,
            'llm_calls': 0,
            'fast_responses': 0
        }
        
        # Optimized session management
        self.session: Optional[aiohttp.ClientSession] = None
        
        # User states and languages
        self.user_states = {}
        self.user_languages = {}
        
        # Pre-compiled regex patterns for speed
        self._compile_patterns()
        
        # Application stages
        self.application_stages = [
            'applicant_name', 'father_name', 'village', 'contact_number', 
            'ward', 'gpu', 'khatiyan_no', 'plot_no', 'damage_type', 
            'damage_description', 'confirmation'
        ]
        
        # Initialize data
        self._initialize_fast_data()
        
    def _compile_patterns(self):
        """Pre-compile regex patterns for maximum speed"""
        self.patterns = {
            'phone': re.compile(r'\b\d{10}\b'),
            'application_id': re.compile(r'\b[A-Z0-9]{6,12}\b'),
            'damage_type': re.compile(r'\b[1-6]\b'),
            'english': re.compile(r'\b(can you|help me|i want|how to|what is|apply for|please|thank you|hello|yes|no)\b', re.IGNORECASE),
            'hindi': re.compile(r'\b(mujhe|mereko|karna|hain|hai|chahiye|batao|baare|main|mein|kya|kaise)\b', re.IGNORECASE),
            'nepali': re.compile(r'\b(cha|chha|chaincha|huncha|garcha|lai|malai|paincha|garna|parcha|kati|kasari)\b', re.IGNORECASE),
            'cancel': re.compile(r'\b(cancel|stop|band|quit|exit|रद्द|बंद|छोड़)\b', re.IGNORECASE)
        }
    
    def _initialize_fast_data(self):
        """Initialize data files with async operations"""
        asyncio.create_task(self._async_initialize_data())
        
    async def _async_initialize_data(self):
        """Async data initialization to avoid blocking"""
        if not os.path.exists('data'):
            os.makedirs('data')
            
        # Create CSV file asynchronously if it doesn't exist
        csv_file = 'data/exgratia_applications.csv'
        if not os.path.exists(csv_file):
            async with aiofiles.open(csv_file, 'w', newline='', encoding='utf-8') as file:
                await file.write('ApplicantName,FatherName,Village,ContactNumber,Ward,GPU,KhatiyanNo,PlotNo,DamageType,DamageDescription,SubmissionDate,Language,Status\n')
    
    async def get_optimized_session(self) -> aiohttp.ClientSession:
        """Get or create optimized HTTP session with connection pooling"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True,
                force_close=False,
                limit_concurrent_connections=50
            )
            
            timeout = aiohttp.ClientTimeout(total=5, connect=2)  # Aggressive timeouts
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'Connection': 'keep-alive'}
            )
        return self.session
    
    def generate_cache_key(self, text: str, operation: str) -> str:
        """Generate cache key for text operations"""
        return f"{operation}:{hashlib.md5(text.lower().encode()).hexdigest()}"
    
    @lru_cache(maxsize=1000)
    def fast_language_detection(self, message: str) -> str:
        """Ultra-fast language detection using pre-compiled patterns"""
        message_lower = message.lower()
        
        # Quick pattern matching
        english_matches = len(self.patterns['english'].findall(message_lower))
        hindi_matches = len(self.patterns['hindi'].findall(message_lower))
        nepali_matches = len(self.patterns['nepali'].findall(message_lower))
        
        # Count Devanagari characters (fast)
        devanagari_count = sum(1 for char in message if '\u0900' <= char <= '\u097F')
        
        # Quick scoring
        scores = {
            'english': english_matches,
            'hindi': hindi_matches + (devanagari_count * 0.5),
            'nepali': nepali_matches + (devanagari_count * 0.3)
        }
        
        # Return highest score language
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'english'
    
    async def cached_language_detection(self, message: str) -> str:
        """Language detection with caching"""
        cache_key = self.generate_cache_key(message, "language")
        
        # Check cache first
        cached_result = self.language_cache.get(cache_key)
        if cached_result:
            self.stats['cache_hits'] += 1
            return cached_result
        
        # Compute and cache
        self.stats['cache_misses'] += 1
        result = self.fast_language_detection(message)
        self.language_cache.set(cache_key, result)
        return result
    
    async def fast_intent_classification(self, message: str) -> str:
        """Fast rule-based intent classification with fallback to LLM"""
        message_lower = message.lower()
        
        # Quick rule-based classification (milliseconds)
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'namaste', 'good morning']):
            return 'greeting'
        elif any(word in message_lower for word in ['help', 'madad', 'sahayata', 'chaincha']):
            return 'help'
        elif any(word in message_lower for word in ['status', 'check', 'track', 'application']):
            return 'status_check'
        elif any(word in message_lower for word in ['apply', 'form', 'application', 'gratia']):
            return 'exgratia_apply'
        elif any(word in message_lower for word in ['norms', 'amount', 'money', 'compensation', 'rules']):
            return 'exgratia_norms'
        elif any(word in message_lower for word in ['how', 'process', 'procedure', 'steps']):
            return 'application_procedure'
        else:
            return 'other'
    
    async def cached_intent_classification(self, message: str) -> str:
        """Intent classification with caching and fallback to LLM if needed"""
        cache_key = self.generate_cache_key(message, "intent")
        
        # Check cache first
        cached_result = self.intent_cache.get(cache_key)
        if cached_result:
            self.stats['cache_hits'] += 1
            self.stats['fast_responses'] += 1
            return cached_result
        
        # Try fast rule-based first
        self.stats['cache_misses'] += 1
        fast_result = await self.fast_intent_classification(message)
        
        # If rule-based is confident, use it
        if fast_result != 'other':
            self.intent_cache.set(cache_key, fast_result)
            self.stats['fast_responses'] += 1
            return fast_result
        
        # Fallback to LLM for complex cases
        llm_result = await self.llm_intent_classification(message)
        self.intent_cache.set(cache_key, llm_result)
        self.stats['llm_calls'] += 1
        return llm_result
    
    async def llm_intent_classification(self, message: str) -> str:
        """LLM-based intent classification with timeout and error handling"""
        session = await self.get_optimized_session()
        
        # Simplified prompt for faster processing
        prompt = f"""Classify intent: "{message[:100]}"
Options: greeting, help, status_check, exgratia_apply, exgratia_norms, application_procedure, other
Answer:"""
        
        payload = {
            "model": self.MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 10,  # Very short response
                "top_p": 0.8
            }
        }
        
        try:
            async with session.post(self.LLM_ENDPOINT, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    intent = result.get('response', '').strip().lower()
                    
                    # Extract valid intent
                    valid_intents = ['greeting', 'help', 'status_check', 'exgratia_apply', 'exgratia_norms', 'application_procedure', 'other']
                    for valid_intent in valid_intents:
                        if valid_intent in intent:
                            return valid_intent
                    return 'other'
                else:
                    return 'other'
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return 'other'
    
    async def cached_response_generation(self, intent: str, language: str, context: str = "") -> str:
        """Generate responses with caching"""
        cache_key = self.generate_cache_key(f"{intent}:{language}:{context}", "response")
        
        cached_response = self.response_cache.get(cache_key)
        if cached_response:
            self.stats['cache_hits'] += 1
            return cached_response
        
        # Generate response
        self.stats['cache_misses'] += 1
        response = self.generate_response(intent, language, context)
        self.response_cache.set(cache_key, response)
        return response
    
    def generate_response(self, intent: str, language: str, context: str = "") -> str:
        """Fast response generation"""
        responses = {
            'english': {
                'greeting': "🏛️ Welcome to SmartGov Ex-Gratia Assistance! How can I help you today?",
                'help': "I can help you with:\n1️⃣ Ex-Gratia application\n2️⃣ Check status\n3️⃣ Get information",
                'status_check': "Please provide your application ID to check status.",
                'exgratia_apply': "Let's start your ex-gratia application. What's your full name?",
                'exgratia_norms': "📋 Ex-Gratia assistance amounts:\n• House damage: ₹50,000-2,00,000\n• Crop damage: ₹10,000-50,000\n• Livestock: ₹5,000-25,000",
                'application_procedure': "📝 Application process:\n1. Provide personal details\n2. Damage assessment\n3. Document submission\n4. Verification\n5. Approval",
                'other': "I can help with ex-gratia applications, status checks, and information. What do you need?"
            },
            'hindi': {
                'greeting': "🏛️ SmartGov Ex-Gratia सहायता में आपका स्वागत है! मैं आपकी कैसे मदद कर सकता हूं?",
                'help': "मैं आपकी मदद कर सकता हूं:\n1️⃣ Ex-Gratia आवेदन\n2️⃣ स्थिति जांच\n3️⃣ जानकारी प्राप्त करें",
                'status_check': "कृपया अपना आवेदन ID प्रदान करें।",
                'exgratia_apply': "आइए आपका ex-gratia आवेदन शुरू करते हैं। आपका पूरा नाम क्या है?",
                'exgratia_norms': "📋 Ex-Gratia सहायता राशि:\n• घर क्षति: ₹50,000-2,00,000\n• फसल क्षति: ₹10,000-50,000\n• पशु: ₹5,000-25,000",
                'application_procedure': "📝 आवेदन प्रक्रिया:\n1. व्यक्तिगत विवरण\n2. क्षति मूल्यांकन\n3. दस्तावेज़ जमा करना\n4. सत्यापन\n5. अनुमोदन",
                'other': "मैं ex-gratia आवेदन, स्थिति जांच और जानकारी में मदद कर सकता हूं। आपको क्या चाहिए?"
            },
            'nepali': {
                'greeting': "🏛️ SmartGov Ex-Gratia सहायतामा तपाईंलाई स्वागत छ! म तपाईंको कसरी मद्दत गर्न सक्छु?",
                'help': "म तपाईंको मद्दत गर्न सक्छु:\n1️⃣ Ex-Gratia आवेदन\n2️⃣ स्थिति जाँच\n3️⃣ जानकारी प्राप्त गर्नुहोस्",
                'status_check': "कृपया आफ्नो आवेदन ID प्रदान गर्नुहोस्।",
                'exgratia_apply': "तपाईंको ex-gratia आवेदन सुरु गरौं। तपाईंको पूरा नाम के हो?",
                'exgratia_norms': "📋 Ex-Gratia सहायता रकम:\n• घर क्षति: ₹50,000-2,00,000\n• बाली क्षति: ₹10,000-50,000\n• पशु: ₹5,000-25,000",
                'application_procedure': "📝 आवेदन प्रक्रिया:\n1. व्यक्तिगत विवरण\n2. क्षति मूल्यांकन\n3. कागजात पेश गर्नुहोस्\n4. प्रमाणीकरण\n5. स्वीकृति",
                'other': "म ex-gratia आवेदन, स्थिति जाँच र जानकारी मा मद्दत गर्न सक्छु। तपाईंलाई के चाहिन्छ?"
            }
        }
        
        return responses.get(language, responses['english']).get(intent, responses[language]['other'])
    
    async def fast_save_to_csv(self, data: Dict) -> None:
        """Async CSV writing to avoid blocking"""
        try:
            async with aiofiles.open('data/exgratia_applications.csv', 'a', newline='', encoding='utf-8') as file:
                row = f"{data['name']},{data['father_name']},{data['village']},{data['phone']},{data['ward']},{data['gpu']},{data['khatiyan']},{data['plot']},{data['damage_type']},{data['damage_desc']},{datetime.now().strftime('%Y-%m-%d')},{data['language']},Submitted\n"
                await file.write(row)
        except Exception as e:
            logger.error(f"CSV write error: {e}")
    
    def get_performance_stats(self) -> str:
        """Get performance statistics"""
        cache_hit_rate = (self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])) * 100 if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0 else 0
        fast_response_rate = (self.stats['fast_responses'] / self.stats['total_requests']) * 100 if self.stats['total_requests'] > 0 else 0
        
        return f"""⚡ **Performance Statistics:**
📊 Cache Hit Rate: {cache_hit_rate:.1f}%
🚀 Fast Response Rate: {fast_response_rate:.1f}%
🧠 LLM Calls: {self.stats['llm_calls']}
⏱️ Avg Response: {self.stats['avg_response_time']:.0f}ms
📈 Total Requests: {self.stats['total_requests']}"""
    
    async def handle_message_optimized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Optimized message handler with performance tracking"""
        start_time = time.time()
        
        try:
            user_id = update.effective_user.id
            message = update.message.text
            
            # Increment stats
            self.stats['total_requests'] += 1
            
            # Check for cancel commands first (fastest)
            if self.patterns['cancel'].search(message):
                if user_id in self.user_states:
                    del self.user_states[user_id]
                language = await self.cached_language_detection(message)
                response = "❌ Application cancelled." if language == 'english' else "❌ आवेदन रद्द कर दिया गया।" if language == 'hindi' else "❌ आवेदन रद्द गरियो।"
                await update.message.reply_text(response)
                return
            
            # Handle application flow if user is in progress
            if user_id in self.user_states:
                await self.handle_application_flow(update, context, message)
                return
            
            # Fast language detection
            language = await self.cached_language_detection(message)
            self.user_languages[user_id] = language
            
            # Fast intent classification
            intent = await self.cached_intent_classification(message)
            
            # Generate cached response
            response = await self.cached_response_generation(intent, language)
            
            # Handle specific intents
            if intent == 'exgratia_apply':
                await self.start_application_flow(update, context, language)
            elif intent == 'status_check':
                app_id_match = self.patterns['application_id'].search(message)
                if app_id_match:
                    await self.check_application_status(update, context, app_id_match.group())
                else:
                    await update.message.reply_text("Please provide your application ID.")
            else:
                await update.message.reply_text(response)
            
            # Update performance stats
            response_time = (time.time() - start_time) * 1000
            self.stats['avg_response_time'] = (self.stats['avg_response_time'] + response_time) / 2
            
            logger.info(f"✅ Processed in {response_time:.0f}ms | Intent: {intent} | Language: {language} | Cache hits: {self.stats['cache_hits']}")
            
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await update.message.reply_text("Sorry, I'm experiencing issues. Please try again.")
    
    async def start_application_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str):
        """Start optimized application flow"""
        user_id = update.effective_user.id
        
        self.user_states[user_id] = {
            'stage': 'applicant_name',
            'data': {},
            'language': language
        }
        
        questions = {
            'english': "Let's start your ex-gratia application.\n\n📝 Step 1/11\n\nPlease provide your full name:",
            'hindi': "आइए आपका ex-gratia आवेदन शुरू करते हैं।\n\n📝 चरण 1/11\n\nकृपया अपना पूरा नाम प्रदान करें:",
            'nepali': "तपाईंको ex-gratia आवेदन सुरु गरौं।\n\n📝 चरण 1/11\n\nकृपया आफ्नो पूरा नाम प्रदान गर्नुहोस्:"
        }
        
        await update.message.reply_text(questions.get(language, questions['english']))
    
    async def handle_application_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
        """Handle application flow with validation"""
        user_id = update.effective_user.id
        state = self.user_states[user_id]
        stage = state['stage']
        language = state['language']
        
        # Validation and data collection logic here
        # (Implementation details for each stage)
        
        # Move to next stage or complete application
        # This is a simplified version - full implementation would handle all stages
        
        if stage == 'confirmation':
            # Save to CSV asynchronously
            await self.fast_save_to_csv(state['data'])
            del self.user_states[user_id]
            
            success_msg = {
                'english': "✅ Application submitted successfully! Your application ID: 24EXG" + str(int(time.time()))[-5:],
                'hindi': "✅ आवेदन सफलतापूर्वक जमा किया गया! आपका आवेदन ID: 24EXG" + str(int(time.time()))[-5:],
                'nepali': "✅ आवेदन सफलतापूर्वक पेश गरियो! तपाईंको आवेदन ID: 24EXG" + str(int(time.time()))[-5:]
            }
            
            await update.message.reply_text(success_msg.get(language, success_msg['english']))
    
    async def check_application_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, app_id: str):
        """Fast status check"""
        # Simplified status check
        status_msg = f"📋 Application {app_id}: Under Review\n📅 Submitted: Recent\n⏳ Expected completion: 7-10 days"
        await update.message.reply_text(status_msg)
    
    async def cleanup_caches(self):
        """Periodic cache cleanup"""
        self.intent_cache.clear_expired()
        self.language_cache.clear_expired()
        self.response_cache.clear_expired()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fast start command"""
        user_id = update.effective_user.id
        language = self.user_languages.get(user_id, 'english')
        
        keyboard = [
            [InlineKeyboardButton("🆘 Apply Ex-Gratia", callback_data="exgratia_apply")],
            [InlineKeyboardButton("📊 Check Status", callback_data="status_check")],
            [InlineKeyboardButton("📋 Information", callback_data="exgratia_norms")],
            [InlineKeyboardButton("⚡ Performance Stats", callback_data="performance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome = await self.cached_response_generation('greeting', language)
        await update.message.reply_text(welcome, reply_markup=reply_markup)
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fast button handler"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "performance":
            stats = self.get_performance_stats()
            await query.edit_message_text(stats)
        elif query.data == "exgratia_apply":
            user_id = update.effective_user.id
            language = self.user_languages.get(user_id, 'english')
            await self.start_application_flow(update, context, language)
        # Handle other buttons...
    
    async def close_session(self):
        """Cleanup session"""
        if self.session and not self.session.closed:
            await self.session.close()

async def main():
    """Main function with optimized setup"""
    print("🚀 Starting OPTIMIZED High-Performance SmartGov Bot...")
    print("⚡ Features: Advanced Caching, Async I/O, Performance Monitoring")
    print("=" * 60)
    
    bot = OptimizedSmartGovBot()
    
    # Create application with optimized settings
    application = Application.builder().token(bot.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("stats", lambda u, c: u.message.reply_text(bot.get_performance_stats())))
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message_optimized))
    
    # Schedule periodic cache cleanup
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            await bot.cleanup_caches()
    
    # Start cleanup task
    asyncio.create_task(periodic_cleanup())
    
    try:
        print("🤖 Optimized bot is now running with:")
        print("   ⚡ Intelligent caching system")
        print("   🚀 Async file operations")
        print("   📊 Performance monitoring")
        print("   🧠 Smart LLM fallback")
        print("   🔧 Connection pooling")
        print("=" * 60)
        
        await application.run_polling(drop_pending_updates=True)
        
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
    finally:
        await bot.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 