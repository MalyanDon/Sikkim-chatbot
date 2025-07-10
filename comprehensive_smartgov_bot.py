#!/usr/bin/env python3
"""
COMPREHENSIVE SmartGov Assistant Bot - COMPLETE Ex-Gratia Application
Collects ALL required information: Personal, Contact, Disaster, Financial, Banking Details
"""

import asyncio
import aiohttp
import json
import time
import logging
import nest_asyncio
import pandas as pd
import csv
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Fix for Windows event loop issues
nest_asyncio.apply()

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartGovAssistantBot:
    def __init__(self):
        self.BOT_TOKEN = "7641958089:AAH2UW5H0EX9pGfE6wZZaURCpkyMHtJK8zw"
        self.MODEL_NAME = "qwen2.5:3b"
        self.LLM_ENDPOINT = "http://localhost:11434/api/generate"
        
        self.request_count = 0
        self.response_times = []
        self.session = None
        
        # User states for COMPREHENSIVE data collection
        self.user_states = {}
        self.user_languages = {}
        
        # COMPREHENSIVE Application Stages - Updated to match user requirements
        self.application_stages = [
            'applicant_name', 'father_name', 'village', 'contact_number', 
            'ward', 'gpu', 'khatiyan_no', 'plot_no', 'damage_type', 
            'damage_description', 'confirmation'
        ]
        
        self._initialize_comprehensive_data_files()
        
        # Complete multilingual templates
        self.responses = {
            'english': {
                'welcome': "🏛️ **SmartGov Services** 🏛️\n\nHow can I help you today? Select a service:",
                'disaster_mgmt': '🚨 **Disaster Management Services**',
                'disaster_mgmt_desc': 'Available services:\n• Ex-gratia assistance application\n• Status checking\n• Information about norms\n\nSelect an option:',
                'exgratia_button': '💰 Apply for Ex-Gratia Assistance',
                'status_check': '🔍 Application Status Check',
                'exgratia_norms': '📋 Ex-Gratia Norms',
                'back_main': '🔙 Back to Main Menu',
                'understand_disaster': 'I understand you need disaster relief assistance. Available options:',
                'btn_disaster': '🚨 Disaster Management',
                'btn_land': '🏘️ Land Records',
                'btn_schemes': '📋 Schemes & Registration',
                'btn_certificates': '📜 Certificates',
                'btn_multi_scheme': '🔗 Multi-Scheme Apps',
                'btn_complaints': '📞 Complaints & Emergency',
                'btn_tourism': '🏔️ Tourism Assistance',
                'btn_other': '⚙️ Other Utilities',
                # COMPREHENSIVE APPLICATION QUESTIONS
                'app_header': '💰 **Ex-Gratia Assistance Application**\n\nI will collect ALL necessary information for your application.',
                'applicant_name_question': '👤 What is your full name?\n(As per official documents)',
                'father_name_question': '👨 What is your father\'s full name?',
                'village_question': '🏘️ What is your village/town name?',
                'contact_number_question': '📱 What is your contact number? (10 digits)',
                'ward_question': '🏠 What is your Ward number?',
                'gpu_question': '🏛️ What is your GPU (Gram Panchayat Unit) number?',
                'khatiyan_no_question': '📄 What is your Khatiyan number?\n(Land record number)',
                'plot_no_question': '🗺️ What is your Plot number?',
                'damage_type_question': '🌪️ What type of damage occurred?\n1️⃣ Flood\n2️⃣ Landslide\n3️⃣ Earthquake\n4️⃣ Fire\n5️⃣ Storm/Cyclone\n6️⃣ Other',
                'damage_description_question': '📝 Describe the damage in detail:\n(House damage, property loss, etc.)',
                'confirmation_question': '✅ Please review and confirm:\nType "CONFIRM" to submit or "EDIT" to modify',
                'phone_error': '❌ Please provide a valid 10-digit phone number.',
                'age_error': '❌ Please provide a valid age (18-100).',
                'pincode_error': '❌ Please provide a valid 6-digit PIN code.',
                'aadhar_error': '❌ Please provide a valid 12-digit Aadhar number.',
                'amount_error': '❌ Please provide a valid amount in numbers.',
                'application_success': '✅ **Application submitted successfully!**'
            },
            'hindi': {
                'welcome': "🏛️ **स्मार्टगव सेवाएं** 🏛️\n\nआज मैं आपकी कैसे मदद कर सकता हूं? एक सेवा चुनें:",
                'disaster_mgmt': '🚨 **आपदा प्रबंधन सेवाएं**',
                'disaster_mgmt_desc': 'उपलब्ध सेवाएं:\n• एक्स-ग्रेशिया सहायता आवेदन\n• स्थिति जांच\n• नियमों की जानकारी\n\nएक विकल्प चुनें:',
                'exgratia_button': '💰 एक्स-ग्रेशिया सहायता के लिए आवेदन',
                'status_check': '🔍 आवेदन स्थिति जांच',
                'exgratia_norms': '📋 एक्स-ग्रेशिया नियम',
                'back_main': '🔙 मुख्य मेनू पर वापस',
                'understand_disaster': 'मैं समझता हूं कि आपको आपदा राहत सहायता चाहिए। उपलब्ध विकल्प:',
                'btn_disaster': '🚨 आपदा प्रबंधन',
                'btn_land': '🏘️ भूमि रिकॉर्ड',
                'btn_schemes': '📋 योजनाएं और पंजीकरण',
                'btn_certificates': '📜 प्रमाणपत्र',
                'btn_multi_scheme': '🔗 बहु-योजना ऐप्स',
                'btn_complaints': '📞 शिकायतें और आपातकाल',
                'btn_tourism': '🏔️ पर्यटन सहायता',
                'btn_other': '⚙️ अन्य उपयोगिताएं',
                'app_header': '💰 **एक्स-ग्रेशिया सहायता आवेदन**\n\nमैं आपके आवेदन के लिए सभी आवश्यक जानकारी एकत्र करूंगा।',
                'applicant_name_question': '👤 आपका पूरा नाम क्या है?\n(आधिकारिक दस्तावेजों के अनुसार)',
                'father_name_question': '👨 आपके पिता का पूरा नाम क्या है?',
                'village_question': '🏘️ आपका गांव/शहर का नाम क्या है?',
                'contact_number_question': '📱 आपका संपर्क नंबर क्या है? (10 अंक)',
                'ward_question': '🏠 आपका वार्ड नंबर क्या है?',
                'gpu_question': '🏛️ आपका GPU (ग्राम पंचायत इकाई) नंबर क्या है?',
                'khatiyan_no_question': '📄 आपका खतियान नंबर क्या है?\n(भूमि रिकॉर्ड नंबर)',
                'plot_no_question': '🗺️ आपका प्लॉट नंबर क्या है?',
                'damage_type_question': '🌪️ कौन सी आपदा हुई?\n1️⃣ बाढ़\n2️⃣ भूस्खलन\n3️⃣ भूकंप\n4️⃣ आग\n5️⃣ तूफान/चक्रवात\n6️⃣ अन्य',
                'damage_description_question': '📝 अपनी हानि का विस्तृत विवरण दें:\n(घर की क्षति, संपत्ति की हानि, आदि)',
                'confirmation_question': '✅ कृपया समीक्षा करें और पुष्टि करें:\nसबमिट करने के लिए "CONFIRM" या संशोधन के लिए "EDIT" टाइप करें',
                'phone_error': '❌ कृपया 10 अंकों का सही फोन नंबर दें।',
                'age_error': '❌ कृपया सही उम्र दें (18-100)।',
                'pincode_error': '❌ कृपया 6 अंकों का सही पिन कोड दें।',
                'aadhar_error': '❌ कृपया 12 अंकों का सही आधार नंबर दें।',
                'amount_error': '❌ कृपया संख्या में सही राशि दें।',
                'application_success': '✅ **आवेदन सफलतापूर्वक जमा हो गया!**'
            },
            'nepali': {
                'welcome': "🏛️ **स्मार्टगभ सेवाहरू** 🏛️\n\nआज म तपाईंको कसरी मद्दत गर्न सक्छु? एक सेवा छान्नुहोस्:",
                'disaster_mgmt': '🚨 **विपद् व्यवस्थापन सेवाहरू**',
                'disaster_mgmt_desc': 'उपलब्ध सेवाहरू:\n• एक्स-ग्रेशिया सहायता आवेदन\n• स्थिति जाँच\n• नियमहरूको जानकारी\n\nएक विकल्प छान्नुहोस्:',
                'exgratia_button': '💰 एक्स-ग्रेशिया सहायताको लागि आवेदन',
                'status_check': '🔍 आवेदन स्थिति जाँच',
                'exgratia_norms': '📋 एक्स-ग्रेशिया नियमहरू',
                'back_main': '🔙 मुख्य मेनूमा फर्कनुहोस्',
                'understand_disaster': 'म बुझ्छु तपाईंलाई विपद् राहत सहायता चाहिएको छ। उपलब्ध विकल्पहरू:',
                'btn_disaster': '🚨 विपद् व्यवस्थापन',
                'btn_land': '🏘️ जग्गा रेकर्ड',
                'btn_schemes': '📋 योजनाहरू र दर्ता',
                'btn_certificates': '📜 प्रमाणपत्रहरू',
                'btn_multi_scheme': '🔗 बहु-योजना एप्स',
                'btn_complaints': '📞 गुनासो र आपतकाल',
                'btn_tourism': '🏔️ पर्यटन सहायता',
                'btn_other': '⚙️ अन्य उपयोगिताहरू',
                'app_header': '💰 **एक्स-ग्रेशिया सहायता आवेदन**\n\nम तपाईंको आवेदनका लागि सबै आवश्यक जानकारी सङ्कलन गर्नेछु।',
                'applicant_name_question': '👤 तपाईंको पूरा नाम के हो?\n(आधिकारिक कागजातअनुसार)',
                'father_name_question': '👨 तपाईंको बुबाको पूरा नाम के हो?',
                'village_question': '🏘️ तपाईंको गाउँ/सहरको नाम के हो?',
                'contact_number_question': '📱 तपाईंको सम्पर्क नम्बर के हो? (10 अंक)',
                'ward_question': '🏠 तपाईंको वार्ड नम्बर के हो?',
                'gpu_question': '🏛️ तपाईंको GPU (ग्राम पंचायत इकाई) नम्बर के हो?',
                'khatiyan_no_question': '📄 तपाईंको खतियान नम्बर के हो? (भूमि रेकर्ड नम्बर)',
                'plot_no_question': '🗺️ तपाईंको प्लॉट नम्बर के हो?',
                'damage_type_question': '🌪️ कुन प्रकारको विपद् भयो?\n1️⃣ बाढी\n2️⃣ पहिरो\n3️⃣ भूकम्प\n4️⃣ आगो\n5️⃣ आँधी/चक्रवात\n6️⃣ अन्य',
                'damage_description_question': '📝 आफ्नो हानिको विस्तृत विवरण दिनुहोस्:\n(घरको क्षति, सम्पत्तिको हानि, आदि)',
                'confirmation_question': '✅ कृपया समीक्षा गर्नुहोस् र पुष्टि गर्नुहोस्:\nपेश गर्न "CONFIRM" वा सम्पादन गर्न "EDIT" टाइप गर्नुहोस्',
                'phone_error': '❌ कृपया 10 अंकको सही फोन नम्बर दिनुहोस्।',
                'age_error': '❌ कृपया सही उमेर दिनुहोस् (18-100)।',
                'pincode_error': '❌ कृपया 6 अंकको सही पिन कोड दिनुहोस्।',
                'aadhar_error': '❌ कृपया 12 अंकको सही आधार नम्बर दिनुहोस्।',
                'amount_error': '❌ कृपया संख्यामा सही रकम दिनुहोस्।',
                'application_success': '✅ **आवेदन सफलतापूर्वक पेश गरियो!**'
            }
        }
        
    def _initialize_comprehensive_data_files(self):
        """Initialize COMPREHENSIVE CSV files for detailed data collection"""
        if not os.path.exists('data'):
            os.makedirs('data')
            
        # COMPREHENSIVE Ex-Gratia Application CSV with ALL necessary fields
        exgratia_file = 'data/exgratia_applications.csv'
        if not os.path.exists(exgratia_file):
            with open(exgratia_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'ApplicantName', 'FatherName', 'Village', 'ContactNumber', 
                    'Ward', 'GPU', 'KhatiyanNo', 'PlotNo', 'DamageType', 
                    'DamageDescription', 'SubmissionDate', 'Language', 'Status'
                ])
                
        # Keep basic submission.csv for other interactions
        if not os.path.exists('data/submission.csv'):
            with open('data/submission.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['submission_id', 'name', 'phone', 'submission_date', 'status', 'details', 'language'])

    def enhanced_language_detection(self, message: str) -> str:
        """Enhanced rule-based language detection with improved accuracy"""
        message_lower = message.lower()
        
        # English patterns - more comprehensive
        english_patterns = [
            'can you', 'help me', 'i want', 'how to', 'what is', 'apply for', 'application', 'please', 'thank you', 
            'hello', 'yes', 'no', 'where is', 'check my', 'my house', 'house got', 'damaged', 'assistance',
            'tell me', 'about', 'compensation', 'status check', 'flood', 'landslide', 'earthquake', 'fire', 'storm'
        ]
        english_score = sum(1 for pattern in english_patterns if pattern in message_lower)
        
        # Hindi-specific patterns (carefully avoiding Nepali overlap)
        hindi_patterns = [
            # Devanagari Hindi
            'मैं', 'आप', 'मेरा', 'करना', 'है', 'हूं', 'से', 'को', 'का', 'की', 'के', 'में', 'पर', 'नहीं', 'हां', 'जी', 'बताओ', 'चाहिए', 'अपना', 'उनका', 'यह', 'वह', 'कैसे', 'क्या', 'कहां', 'कब', 'किसका', 'किसको',
            # Romanized Hindi (EXCLUSIVE to Hindi - removed overlapping words)
            'mujhe', 'mereko', 'karna', 'hain', 'hai', 'hun', 'ho', 'kaise', 'kya', 'kahan', 'kab', 'chahiye', 'batao', 'btao', 'btayae', 'dijiye', 'dijye', 'krna', 'krdo', 'kro', 'baare', 'main', 'mein', 'banda', 'karo', 'nahin', 'nahi', 'haan', 'han', 'ji', 'sahab', 'sir', 'madam', 'aap', 'app', 'tum', 'tumhara', 'hamara', 'humara', 'wala', 'wale', 'wali', 'kitna', 'kitni'
        ]
        
        # Nepali-specific patterns (EXCLUSIVE to Nepali - removed Hindi overlaps)
        nepali_patterns = [
            # Devanagari Nepali (unique markers)
            'छ', 'हुन्छ', 'गर्छ', 'सक्छु', 'गर्नुहोस्', 'छैन', 'भन्नुहोस्', 'चाहिन्छ', 'पर्छ', 'सक्छ', 'गर्न', 'भन्न', 'हेर्न', 'सुन्न', 'रुपैयाँ', 'कति', 'कसरी', 'किन', 'कुन', 'राम्रो', 'नराम्रो', 'ठूलो', 'सानो', 'नयाँ', 'पुरानो',
            # Romanized Nepali (EXCLUSIVE - removed Hindi overlaps like mujhe, main, btayae)
            'cha', 'chha', 'chaina', 'chhaina', 'huncha', 'hunchha', 'garcha', 'garchha', 'lai', 'malai', 'sakchu', 'garna', 'parcha', 'parchha', 'chaincha', 'chaaincha', 'maddat', 'madaad', 'kaha', 'kati', 'kasari', 'kina', 'ke', 'kun', 'rupaiya', 'paani', 'khaana', 'ramro', 'naramro', 'thulo', 'sano', 'naya', 'purano', 'paincha', 'paaincha', 'bigaareko', 'bigareko', 'noksaan', 'noksan', 'badhi', 'baadhi', 'hernu', 'herna', 'bhanna', 'bhannu', 'garnuhos', 'gara', 'barema', 'ko barema', 'tapai', 'tapaii', 'mero', 'hamro', 'timro', 'unko', 'yo', 'tyo', 'ma', 'hami', 'timi'
        ]
        
        # Shared patterns that could be both (weighted lower)
        shared_patterns = ['tera', 'uska', 'ghar', 'paisa', 'rupee', 'rupaye', 'paise', 'sahayata', 'sahayta']
        
        # Count Devanagari characters
        devanagari_count = sum(1 for char in message if '\u0900' <= char <= '\u097F')
        
        # Calculate word match scores
        hindi_word_score = sum(1 for pattern in hindi_patterns if pattern in message_lower)
        shared_word_score = sum(1 for pattern in shared_patterns if pattern in message_lower)
        nepali_word_score = sum(1 for pattern in nepali_patterns if pattern in message_lower)
        
        # Calculate TOTAL scores (this is what should be compared)
        hindi_total_score = hindi_word_score + (shared_word_score * 0.5) + (devanagari_count * 1.5)
        nepali_total_score = nepali_word_score + (shared_word_score * 0.5) + (devanagari_count * 1.5)
        
        logger.info(f"🔍 LANGUAGE SCORES: English={english_score}, Hindi={hindi_total_score:.1f} (specific={hindi_word_score}, shared={shared_word_score}, devanagari={devanagari_count}), Nepali={nepali_total_score:.1f} (specific={nepali_word_score})")
        
        # FIXED Detection logic - compare TOTAL scores, not just word counts
        max_score = max(english_score, hindi_total_score, nepali_total_score)
        
        if max_score == 0:
            # No patterns matched, default to English
            detected = 'english'
        elif hindi_total_score == max_score and hindi_total_score > 0:
            # Hindi has highest score
            detected = 'hindi'
        elif nepali_total_score == max_score and nepali_total_score > 0:
            # Nepali has highest score
            detected = 'nepali'
        elif english_score == max_score and english_score > 0:
            # English has highest score
            detected = 'english'
        else:
            # Fallback to highest non-zero score
            if hindi_total_score >= nepali_total_score and hindi_total_score >= english_score:
                detected = 'hindi'
            elif nepali_total_score >= english_score:
                detected = 'nepali'
            else:
                detected = 'english'
        
        logger.info(f"🌐 ENHANCED DETECTION: '{message}' → {detected.upper()}")
        return detected

    def get_user_language(self, user_id):
        return self.user_languages.get(user_id, 'english')

    def set_user_language(self, user_id, language):
        self.user_languages[user_id] = language
        logger.info(f"🌐 USER LANGUAGE SET: User {user_id} → {language.upper()}")

    def get_response_text(self, key, user_id):
        language = self.get_user_language(user_id)
        return self.responses.get(language, self.responses['english']).get(key, key)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main service selection menu"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        keyboard = [
            [InlineKeyboardButton(self.get_response_text('btn_disaster', user_id), callback_data="disaster_management")],
            [InlineKeyboardButton(self.get_response_text('btn_land', user_id), callback_data="land_records")],
            [InlineKeyboardButton(self.get_response_text('btn_schemes', user_id), callback_data="schemes_registration")],
            [InlineKeyboardButton(self.get_response_text('btn_certificates', user_id), callback_data="certificates")],
            [InlineKeyboardButton(self.get_response_text('btn_multi_scheme', user_id), callback_data="multi_scheme_apps")],
            [InlineKeyboardButton(self.get_response_text('btn_complaints', user_id), callback_data="complaints_emergency")],
            [InlineKeyboardButton(self.get_response_text('btn_tourism', user_id), callback_data="tourism_assistance")],
            [InlineKeyboardButton(self.get_response_text('btn_other', user_id), callback_data="other_utilities")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = self.get_response_text('welcome', user_id)
        
        logger.info(f"🏠 START COMMAND: User {user_id} → Language: {language.upper()} → FULL MENU IN {language.upper()}")
        
        if update.callback_query:
            await update.callback_query.edit_message_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all button interactions"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        logger.info(f"🔘 BUTTON PRESSED: User {user_id} → {query.data}")
        
        if query.data == "disaster_management":
            await self.show_disaster_management(update, context)
        elif query.data == "back_to_main":
            await self.start_command(update, context)
        elif query.data == "exgratia_apply":
            await self.start_comprehensive_exgratia_application(update, context)
        elif query.data == "confirm_application":
            await self.complete_comprehensive_application(update, context)
        elif query.data == "reject_application":
            user_id = update.effective_user.id
            language = self.get_user_language(user_id)
            if user_id in self.user_states:
                del self.user_states[user_id]
            
            if language == 'hindi':
                reject_msg = "❌ आवेदन रद्द कर दिया गया। नया आवेदन शुरू करने के लिए /start टाइप करें।"
            elif language == 'nepali':
                reject_msg = "❌ आवेदन रद्द गरियो। नयाँ आवेदन सुरु गर्न /start टाइप गर्नुहोस्।"
            else:
                reject_msg = "❌ Application cancelled. Type /start to begin a new application."
            
            await update.callback_query.edit_message_text(reject_msg)
            logger.info(f"❌ APPLICATION REJECTED: User {user_id} → Cancelled by user")

    async def show_disaster_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show disaster management services"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        keyboard = [
            [InlineKeyboardButton(self.get_response_text('exgratia_button', user_id), callback_data="exgratia_apply")],
            [InlineKeyboardButton(self.get_response_text('status_check', user_id), callback_data="status_check")],
            [InlineKeyboardButton(self.get_response_text('exgratia_norms', user_id), callback_data="exgratia_norms")],
            [InlineKeyboardButton(self.get_response_text('back_main', user_id), callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        header = self.get_response_text('disaster_mgmt', user_id)
        description = self.get_response_text('disaster_mgmt_desc', user_id)
        message = f"{header}\n\n{description}"
        
        logger.info(f"🚨 DISASTER MGMT: User {user_id} → Language: {language.upper()} → FULLY CONSISTENT INTERFACE")
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def start_comprehensive_exgratia_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start COMPREHENSIVE ex-gratia application process"""
        user_id = update.effective_user.id
        language = self.get_user_language(user_id)
        
        self.user_states[user_id] = {
            'stage': 'applicant_name', 
            'data': {}, 
            'language': language,
            'total_stages': len(self.application_stages),
            'current_stage_index': 0
        }
        
        header = self.get_response_text('app_header', user_id)
        question = self.get_response_text('applicant_name_question', user_id)
        progress = f"📋 Step 1/{len(self.application_stages)}"
        
        message = f"""{header}

{progress}

{question}"""
        
        logger.info(f"📝 COMPREHENSIVE EXGRATIA APPLICATION STARTED: User {user_id} → Language: {language.upper()} → {len(self.application_stages)} stages")
        await update.callback_query.edit_message_text(message, parse_mode='Markdown')

    def validate_input(self, stage: str, input_text: str) -> tuple[bool, str]:
        """Validate user input based on current stage"""
        input_text = input_text.strip()
        
        if stage == 'applicant_name':
            return (len(input_text) >= 2), input_text if len(input_text) >= 2 else 'Please provide valid full name'
                
        elif stage == 'father_name':
            return (len(input_text) >= 2), input_text if len(input_text) >= 2 else 'Please provide valid father\'s name'
                
        elif stage == 'village':
            return (len(input_text) >= 2), input_text if len(input_text) >= 2 else 'Please provide valid village name'
                
        elif stage == 'contact_number':
            clean_phone = input_text.replace(' ', '').replace('-', '').replace('+91', '')
            return (len(clean_phone) == 10 and clean_phone.isdigit()), clean_phone if len(clean_phone) == 10 and clean_phone.isdigit() else 'Please provide valid 10-digit contact number'
                
        elif stage == 'ward':
            return (len(input_text) >= 1), input_text if len(input_text) >= 1 else 'Please provide valid ward number'
                
        elif stage == 'gpu':
            return (len(input_text) >= 1), input_text if len(input_text) >= 1 else 'Please provide valid GPU number'
                
        elif stage == 'khatiyan_no':
            return (len(input_text) >= 1), input_text if len(input_text) >= 1 else 'Please provide valid Khatiyan number'
                
        elif stage == 'plot_no':
            return (len(input_text) >= 1), input_text if len(input_text) >= 1 else 'Please provide valid Plot number'
                
        elif stage == 'damage_type':
            if input_text in ['1', '2', '3', '4', '5', '6']:
                damage_map = {'1': 'Flood', '2': 'Landslide', '3': 'Earthquake', '4': 'Fire', '5': 'Storm/Cyclone', '6': 'Other'}
                return True, damage_map[input_text]
            return False, 'Please select 1-6 for damage type'
                
        elif stage == 'damage_description':
            return (len(input_text) >= 10), input_text if len(input_text) >= 10 else 'Please provide a detailed description of the damage (minimum 10 characters)'
                
        else:
            return (len(input_text) >= 2), input_text if len(input_text) >= 2 else 'Please provide valid information'

    async def handle_comprehensive_application_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
        """Handle comprehensive application flow"""
        user_id = update.effective_user.id
        state = self.user_states[user_id]
        stage = state['stage']
        language = state['language']
        
        logger.info(f"📋 COMPREHENSIVE FLOW: User {user_id} → Stage: {stage.upper()}, Language: {language.upper()}, Input: '{message}'")
        
        # If we're at confirmation stage, we shouldn't handle text input (only button clicks)
        if stage == 'confirmation':
            if language == 'hindi':
                wait_msg = "कृपया ऊपर दिए गए बटन का उपयोग करें।"
            elif language == 'nepali':
                wait_msg = "कृपया माथि दिइएको बटन प्रयोग गर्नुहोस्।"
            else:
                wait_msg = "Please use the buttons above to confirm or reject."
            
            await update.message.reply_text(wait_msg)
            return
        
        is_valid, result = self.validate_input(stage, message)
        
        if not is_valid:
            if result in ['age_error', 'phone_error', 'pincode_error', 'aadhar_error', 'amount_error']:
                error_msg = self.get_response_text(result, user_id)
            else:
                error_msg = result
            
            question_key = f"{stage}_question"
            question = self.get_response_text(question_key, user_id)
            current_step = state['current_stage_index'] + 1
            progress = f"📋 Step {current_step}/{state['total_stages']}"
            
            await update.message.reply_text(f"{error_msg}\n\n{progress}\n\n{question}")
            logger.warning(f"❌ VALIDATION FAILED: User {user_id} → Stage: {stage.upper()}, Input: '{message}'")
            return
        
        state['data'][stage] = result
        logger.info(f"✅ DATA COLLECTED: User {user_id} → {stage.upper()}: '{result}' (continuing in {language.upper()})")
        
        current_index = state['current_stage_index']
        if current_index < len(self.application_stages) - 1:
            next_index = current_index + 1
            next_stage = self.application_stages[next_index]
            
            state['stage'] = next_stage
            state['current_stage_index'] = next_index
            
            progress = f"📋 Step {next_index + 1}/{state['total_stages']}"
            
            if next_stage == 'confirmation':
                await self.show_application_confirmation(update, context)
            else:
                question_key = f"{next_stage}_question"
                question = self.get_response_text(question_key, user_id)
                await update.message.reply_text(f"{progress}\n\n{question}")
        else:
            await self.complete_comprehensive_application(update, context)

    async def show_application_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show collected data for confirmation with inline buttons"""
        user_id = update.effective_user.id
        data = self.user_states[user_id]['data']
        language = self.user_states[user_id]['language']
        
        confirmation = f"""📋 **Application Review**

**Personal Details:**
👤 Name: {data.get('applicant_name', '')}
👨 Father's Name: {data.get('father_name', '')}
🏘️ Village: {data.get('village', '')}
📱 Contact Number: {data.get('contact_number', '')}

**Location Details:**
🏠 Ward: {data.get('ward', '')}
🏛️ GPU: {data.get('gpu', '')}
📄 Khatiyan No: {data.get('khatiyan_no', '')}
🗺️ Plot No: {data.get('plot_no', '')}

**Damage Details:**
🌪️ Damage Type: {data.get('damage_type', '')}
📝 Damage Description: {data.get('damage_description', '')}"""
        
        # Create inline keyboard buttons for confirmation
        if language == 'hindi':
            confirm_text = "✅ पुष्टि करें"
            reject_text = "❌ रद्द करें"
            question_text = "कृपया समीक्षा करें और पुष्टि करें:"
        elif language == 'nepali':
            confirm_text = "✅ पुष्टि गर्नुहोस्"
            reject_text = "❌ रद्द गर्नुहोस्"
            question_text = "कृपया समीक्षा गर्नुहोस् र पुष्टि गर्नुहोस्:"
        else:
            confirm_text = "✅ CONFIRM"
            reject_text = "❌ REJECT"
            question_text = "Please review and confirm your application:"
        
        keyboard = [
            [
                InlineKeyboardButton(confirm_text, callback_data="confirm_application"),
                InlineKeyboardButton(reject_text, callback_data="reject_application")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"{confirmation}\n\n{question_text}"
        
        logger.info(f"📋 CONFIRMATION SHOWN: User {user_id} → All data collected with buttons")
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def complete_comprehensive_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete comprehensive application"""
        user_id = update.effective_user.id
        data = self.user_states[user_id]['data']
        language = self.user_states[user_id]['language']
        
        import random
        import time
        app_id = f"24EXG{random.randint(10000, 99999)}"
        submission_date = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Add submission details to data
        data['submission_date'] = submission_date
        data['language'] = language.upper()
        data['application_id'] = app_id
        
        exgratia_file = 'data/exgratia_applications.csv'
        with open(exgratia_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                data.get('applicant_name', ''), data.get('father_name', ''), data.get('village', ''), 
                data.get('contact_number', ''), data.get('ward', ''), data.get('gpu', ''), 
                data.get('khatiyan_no', ''), data.get('plot_no', ''), data.get('damage_type', ''), 
                data.get('damage_description', ''), submission_date, language.upper(), 'Submitted'
            ])
        
        success_message = self.get_response_text('application_success', user_id)
        
        details = f"""📋 **Ex-Gratia Application Submitted Successfully!**

🆔 **Application ID:** `{app_id}`
📅 **Submission Date:** {submission_date}
🌐 **Language:** {language.upper()}
📱 **Contact:** {data.get('contact_number', '')}

**📄 Application Details:**
👤 **Applicant:** {data.get('applicant_name', '')}
👨 **Father's Name:** {data.get('father_name', '')}
🏘️ **Village:** {data.get('village', '')}
🏠 **Ward:** {data.get('ward', '')}
🏛️ **GPU:** {data.get('gpu', '')}
📄 **Khatiyan No:** {data.get('khatiyan_no', '')}
🗺️ **Plot No:** {data.get('plot_no', '')}
🌪️ **Damage Type:** {data.get('damage_type', '')}
📝 **Damage Description:** {data.get('damage_description', '')}

📞 **Support Contact:**
Helpline: 1077
Email: smartgov@sikkim.gov.in

🔍 **Keep your Application ID safe for status checking.**

⏰ **Expected Processing Time:** 7-15 working days
✅ **Status:** Under Review"""
        
        logger.info(f"✅ APPLICATION COMPLETED: User {user_id} → App ID: {app_id}, Language: {language.upper()}")
        
        # Handle both callback queries (from buttons) and regular messages
        if update.callback_query:
            await update.callback_query.edit_message_text(details, parse_mode='Markdown')
        else:
            await update.message.reply_text(details, parse_mode='Markdown')
        
        del self.user_states[user_id]

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages with LLM processing"""
        message = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"📩 MESSAGE RECEIVED: User {user_id} → '{message}'")
        
        # Check for cancel commands first
        cancel_commands = ['cancel', 'stop', 'band karo', 'bandkaro', 'band kr', 'bandkar', 'cancel karo', 'cancel kar', 'quit', 'exit', 'रद्द करो', 'बंद करो', 'रोको', 'छोड़ो', 'वापस']
        if any(cmd in message.lower() for cmd in cancel_commands):
            if user_id in self.user_states:
                del self.user_states[user_id]
            language = self.get_user_language(user_id)
            welcome_msg = self.get_response_text('welcome', user_id)
            
            keyboard = [
                [InlineKeyboardButton(self.get_response_text('btn_disaster', user_id), callback_data="disaster_mgmt")],
                [InlineKeyboardButton(self.get_response_text('btn_land', user_id), callback_data="land_records")],
                [InlineKeyboardButton(self.get_response_text('btn_schemes', user_id), callback_data="schemes")],
                [InlineKeyboardButton(self.get_response_text('btn_certificates', user_id), callback_data="certificates")],
                [InlineKeyboardButton(self.get_response_text('btn_multi_scheme', user_id), callback_data="multi_scheme")],
                [InlineKeyboardButton(self.get_response_text('btn_complaints', user_id), callback_data="complaints")],
                [InlineKeyboardButton(self.get_response_text('btn_tourism', user_id), callback_data="tourism")],
                [InlineKeyboardButton(self.get_response_text('btn_other', user_id), callback_data="other")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            cancel_msg = "❌ Process cancelled. " if language == 'english' else "❌ प्रक्रिया रद्द की गई। " if language == 'hindi' else "❌ प्रक्रिया रद्द गरियो। "
            await update.message.reply_text(f"{cancel_msg}\n\n{welcome_msg}", reply_markup=reply_markup, parse_mode='Markdown')
            logger.info(f"❌ PROCESS CANCELLED: User {user_id} → Returned to main menu")
            return
        
        # If user is in application flow, handle it
        if user_id in self.user_states:
            await self.handle_comprehensive_application_flow(update, context, message)
            return
        
        # Detect language and set user preference
        detected_language = self.enhanced_language_detection(message)
        self.set_user_language(user_id, detected_language)
        logger.info(f"🌐 USER LANGUAGE SET: User {user_id} → {detected_language.upper()}")
        
        # Show main menu
        await self.start_command(update, context)

    async def show_disaster_management_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direct access to disaster management"""
        user_id = update.effective_user.id
        
        keyboard = [
            [InlineKeyboardButton(self.get_response_text('exgratia_button', user_id), callback_data="exgratia_apply")],
            [InlineKeyboardButton(self.get_response_text('status_check', user_id), callback_data="status_check")],
            [InlineKeyboardButton(self.get_response_text('back_main', user_id), callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        header = self.get_response_text('disaster_mgmt', user_id)
        understanding = self.get_response_text('understand_disaster', user_id)
        message = f"{header}\n\n{understanding}"
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

def main():
    """Main function"""
    print("🚀 Starting COMPREHENSIVE SmartGov Assistant Bot...")
    print("📋 COMPREHENSIVE Ex-Gratia Application with ALL required fields!")
    print("📊 Comprehensive Data Collection:")
    stages = ['applicant_name', 'father_name', 'village', 'contact_number', 
              'ward', 'gpu', 'khatiyan_no', 'plot_no', 'damage_type', 
              'damage_description', 'confirmation']
    for i, stage in enumerate(stages, 1):
        print(f"   {i:2d}. {stage.replace('_', ' ').title()}")
    print("=" * 60)
    
    bot = SmartGovAssistantBot()
    application = Application.builder().token(bot.BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message_handler))
    
    print("🤖 COMPREHENSIVE SmartGov Assistant is running...")
    print("📱 Bot Link: https://t.me/smartgov_assistant_bot")
    print("✅ Ready to serve citizens with COMPREHENSIVE Ex-Gratia applications!")
    print("📋 COMPREHENSIVE APPLICATION: 16 stages of data collection!")
    print("=" * 60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 