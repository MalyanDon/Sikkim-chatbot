#!/usr/bin/env python3
"""
Comprehensive Sikkim SmartGov Assistant Bot
"""
import asyncio
import json
import logging
import pandas as pd
import threading
import sys
import os
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Location
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import Config
from datetime import datetime
import time
import random
from typing import Dict, Tuple
from google_sheets_service import GoogleSheetsService
from nc_exgratia_api import get_api_client, NCExgratiaAPI

# Force UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.system('chcp 65001')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class SmartGovAssistantBot:
    def __init__(self):
        """Initialize bot with configuration"""
        # Load configuration
        self.BOT_TOKEN = Config.BOT_TOKEN
        
        # Initialize states with thread-safe locks
        self.user_states = {}
        self.user_languages = {}
        self._state_lock = threading.RLock()
        
        # Load workflow data
        self._load_workflow_data()
        
        # Initialize multilingual responses
        self._initialize_responses()
        
        # Initialize aiohttp session for LLM calls
        self._session = None
        
        # Initialize Google Sheets service
        self._initialize_google_sheets()
        
        # Initialize NC Exgratia API client
        self.api_client = None
        if Config.NC_EXGRATIA_ENABLED:
            self.api_client = NCExgratiaAPI()
            logger.info("🔗 NC Exgratia API client initialized")
        else:
            logger.warning("⚠️ NC Exgratia API integration disabled")
        
        logger.info("🔒 MULTI-USER SUPPORT: Thread-safe state management initialized")

    def _load_workflow_data(self):
        """Load all required data files from Excel sheet only"""
        try:
            # Load ONLY data from "Details for Smart Govt Assistant.xlsx" (converted to CSV)
            self.csc_details_df = pd.read_csv('data/csc_details.csv')  # CSC operators by GPU
            self.blo_details_df = pd.read_csv('data/blo_details.csv')  # BLO by polling station
            self.scheme_df = pd.read_csv('data/scheme.csv')  # Schemes from Excel
            self.block_gpu_mapping_df = pd.read_csv('data/block_gpu_mapping.csv')  # Block-GPU mapping
            self.home_stay_df = pd.read_csv('data/home_stay.csv')  # Homestay details
            self.health_df = pd.read_csv('data/health.csv')  # Health services
            self.fair_price_shop_df = pd.read_csv('data/fair_price_shop.csv')  # Fair price shops
            self.single_window_staff_df = pd.read_csv('data/single_window_staff_details.csv')  # Single window staff
            self.sub_division_block_mapping_df = pd.read_csv('data/sub-division_block_mapping.csv')  # Sub-division mapping
            self.sheet12_df = pd.read_csv('data/sheet12.csv')  # Additional data
            
            logger.info("📚 Data files from Excel sheet loaded successfully")
        except Exception as e:
            logger.error(f"❌ Error loading data files: {str(e)}")
            raise

    def _initialize_google_sheets(self):
        """Initialize Google Sheets service"""
        try:
            if Config.GOOGLE_SHEETS_ENABLED and Config.GOOGLE_SHEETS_CREDENTIALS_FILE:
                self.sheets_service = GoogleSheetsService(
                    credentials_file=Config.GOOGLE_SHEETS_CREDENTIALS_FILE,
                    spreadsheet_id=Config.GOOGLE_SHEETS_SPREADSHEET_ID
                )
                logger.info("✅ Google Sheets service initialized successfully")
            else:
                self.sheets_service = None
                logger.warning("⚠️ Google Sheets integration disabled or credentials file not configured")
        except Exception as e:
            logger.error(f"❌ Error initializing Google Sheets service: {str(e)}")
            self.sheets_service = None

    def _initialize_responses(self):
        """Initialize multilingual response templates"""
        self.responses = {
            'english': {
                'welcome': "Welcome to SmartGov Assistant! How can I help you today?",
                'main_menu': """🏛️ *Welcome to SmartGov Assistant* 🏛️

Our services include:

1. *Book Homestay* 🏡
   • Search by tourist destinations
   • View ratings and prices
   • Direct contact with owners

2. *Emergency Services* 🚨
   • Ambulance (102/108)
   • Police Helpline
   • Suicide Prevention
   • Health Helpline
   • Women Helpline
   • Fire Emergency
   • Report Disaster

3. *Report a Complaint* 📝
   • Register your grievance
   • Get complaint tracking ID
   • 24/7 monitoring

4. *Apply for Certificate* 💻
   • CSC operator assistance
   • Sikkim SSO portal link
   • Track application status

5. *Disaster Management* 🆘
   • Apply for Ex-gratia
   • Check application status
   • View relief norms
   • Emergency contacts

6. *Government Schemes* 🏛️
   • Learn about schemes
   • Apply for benefits
   • Track applications

7. *Important Contacts* 📞
   • Find your CSC
   • Know your BLO
   • Aadhar Services

8. *Give Feedback* 📝
   • Share your experience
   • Suggest improvements
   • Help us serve better

Please select a service to continue:""",
                'button_homestay': "🏡 Book Homestay",
                'button_emergency': "🚨 Emergency Services",
                'button_complaint': "📝 Report a Complaint",
                'button_certificate': "💻 Apply for Certificate",
                'button_disaster': "🆘 Disaster Management",
                'button_schemes': "🏛️ Government Schemes",
                'button_contacts': "📞 Important Contacts",
                'button_feedback': "📝 Give Feedback",
                'error': "Sorry, I encountered an error. Please try again.",
                'unknown': "I'm not sure what you're asking for. Here are the available services:",
                'processing': "Processing your request...",
                'success': "Your request has been processed successfully.",
                'cancelled': "Operation cancelled. How else can I help you?",
                'emergency_ambulance': "🚑 *Ambulance Emergency*\nDial: 102 or 108\nControl Room: 03592-202033",
                'emergency_police': "👮 *Police Emergency*\nDial: 100\nControl Room: 03592-202022",
                'emergency_fire': "🚒 *Fire Emergency*\nDial: 101\nControl Room: 03592-202099",
                'emergency_suicide': "💭 *Suicide Prevention Helpline*\nDial: 9152987821",
                'emergency_women': "👩 *Women Helpline*\nDial: 1091\nState Commission: 03592-205607",
                'ex_gratia_intro': "You may be eligible if you've suffered losses due to:\n• Heavy rainfall, floods, or landslides\n• Earthquakes or other natural calamities\n• Crop damage from hailstorms\n• House damage from natural disasters\n• Loss of livestock\n\nWould you like to proceed with the application?",
                'ex_gratia_form': "Please enter your full name:",
                'ex_gratia_father': "What is your father's name?",
                'ex_gratia_village': "Which village are you from?",
                'ex_gratia_contact': "What is your contact number? (10 digits)",
                'ex_gratia_ward': "What is your Ward number or name?",
                'ex_gratia_gpu': "Which Gram Panchayat Unit (GPU) are you under?",
                'ex_gratia_khatiyan': "What is your Khatiyan Number? (Land record number)",
                'ex_gratia_plot': "What is your Plot Number?",
                'ex_gratia_damage': "Please provide a detailed description of the damage:",
                'certificate_info': "To apply for services through the Sikkim SSO portal:\n1. Register and create an account on the Sikkim SSO portal\n2. Log in using your Sikkim SSO credentials\n3. Navigate to the desired service\n4. Fill out the application form\n5. Upload necessary documents\n6. Track your application status online\n\nWould you like to apply through a CSC operator or Single Window operator?",
                'other_emergency': "🚨 Other Emergency Services",
                'back_main_menu': "🔙 Back to Main Menu",
                'language_menu': "🌐 *Language Selection*\n\nPlease select your preferred language:",
                'language_changed': "✅ Language changed to English successfully!",
                'language_button_english': "🇺🇸 English",
                'language_button_hindi': "🇮🇳 हिंदी",
                'complaint_title': "*Report a Complaint/Grievance* 📝",
                'complaint_name_prompt': "Please enter your full name:",
                'complaint_mobile_prompt': "Please enter your mobile number:",
                'complaint_mobile_error': "Please enter a valid 10-digit mobile number.",
                'complaint_description_prompt': "Please describe your complaint in detail:",
                'complaint_success': "✅ *Complaint Registered Successfully*\n\n🆔 Complaint ID: {complaint_id}\n👤 Name: {name}\n📱 Mobile: {mobile}\n🔗 Telegram: @{telegram_username}\n\nYour complaint has been registered and will be processed soon. Please save your Complaint ID for future reference.",
                'certificate_gpu_prompt': "Please enter your GPU (Gram Panchayat Unit):",
                'certificate_sso_message': "You can apply directly on the Sikkim SSO Portal: https://sso.sikkim.gov.in",
                'certificate_gpu_not_found': "Sorry, no CSC operator found for your GPU. Please check the GPU number and try again.",
                'certificate_csc_details': "*CSC Operator Details*\n\nName: {name}\nContact: {contact}\nTimings: {timings}",
                'certificate_error': "Sorry, there was an error processing your request. Please try again.",
                
                # New features responses
                'scheme_info': """🏛️ **Government Schemes & Applications**

Available schemes include:
• PM KISAN
• PM Fasal Bima
• PM Vishwakarma
• Fisheries Registration
• Kishan Credit Card
• And many more...

Select a scheme to learn more and apply:""",
                
                'contacts_info': """📞 **Important Contacts**

Choose the type of contact you need:
• **CSC (Common Service Center)** - Find your nearest CSC operator
• **BLO (Booth Level Officer)** - Electoral roll services
• **Aadhar Services** - Aadhar card related services

Select an option:""",
                
                'feedback_info': """📝 **Give Feedback**

We value your feedback to improve our services. Please provide:
• Your name
• Phone number
• Your feedback/suggestions

Let's start with your name:""",
                
                'feedback_name_prompt': "Please enter your name:",
                'feedback_phone_prompt': "Please enter your phone number:",
                'feedback_message_prompt': "Please share your feedback or suggestions:",
                'feedback_success': """✅ **Feedback Submitted Successfully!**

Thank you for your feedback. We will review it and work on improvements.

Your feedback ID: {feedback_id}""",
            },
            'hindi': {
                'welcome': "स्मार्टगव सहायक में आपका स्वागत है! मैं आपकी कैसे मदद कर सकता हूं?",
                'main_menu': """🏛️ *स्मार्टगव सहायक में आपका स्वागत है* 🏛️

हमारी सेवाएं शामिल हैं:

1. *होमस्टे बुक करें* 🏡
   • पर्यटन स्थलों के अनुसार खोजें
   • रेटिंग और कीमतें देखें
   • मालिकों से सीधा संपर्क

2. *आपातकालीन सेवाएं* 🚨
   • एम्बुलेंस (102/108)
   • पुलिस हेल्पलाइन
   • आत्महत्या रोकथाम
   • स्वास्थ्य हेल्पलाइन
   • महिला हेल्पलाइन
   • अग्निशमन आपातकाल
   • आपदा की रिपोर्ट करें

3. *शिकायत दर्ज करें* 📝
   • अपनी शिकायत पंजीकृत करें
   • शिकायत ट्रैकिंग आईडी प्राप्त करें
   • 24/7 निगरानी

4. *प्रमाणपत्र के लिए आवेदन करें* 💻
   • CSC ऑपरेटर सहायता
   • सिक्किम SSO पोर्टल लिंक
   • आवेदन स्थिति ट्रैक करें

5. *आपदा प्रबंधन* 🆘
   • एक्स-ग्रेटिया के लिए आवेदन करें
   • आवेदन स्थिति जांचें
   • राहत मानदंड देखें
   • आपातकालीन संपर्क

कृपया जारी रखने के लिए एक सेवा चुनें:""",
                'button_homestay': "🏡 होमस्टे बुक करें",
                'button_emergency': "🚨 आपातकालीन सेवाएं",
                'button_complaint': "📝 शिकायत दर्ज करें",
                'button_certificate': "💻 प्रमाणपत्र के लिए आवेदन",
                'button_disaster': "🆘 आपदा प्रबंधन",
                'button_schemes': "🏛️ सरकारी योजनाएं",
                'button_contacts': "📞 महत्वपूर्ण संपर्क",
                'button_feedback': "📝 प्रतिक्रिया दें",
                'error': "क्षमा करें, कोई त्रुटि हुई। कृपया पुनः प्रयास करें।",
                'unknown': "मुझे समझ नहीं आया। यहाँ उपलब्ध सेवाएं हैं:",
                'processing': "आपका अनुरोध प्रोसेस किया जा रहा है...",
                'success': "आपका अनुरोध सफलतापूर्वक प्रोसेस कर दिया गया है।",
                'cancelled': "प्रक्रिया रद्द कर दी गई। मैं और कैसे मदद कर सकता हूं?",
                'emergency_ambulance': "🚑 *एम्बुलेंस इमरजेंसी*\nडायल करें: 102 या 108\nकंट्रोल रूम: 03592-202033",
                'emergency_police': "👮 *पुलिस इमरजेंसी*\nडायल करें: 100\nकंट्रोल रूम: 03592-202022",
                'emergency_fire': "🚒 *अग्निशमन इमरजेंसी*\nडायल करें: 101\nकंट्रोल रूम: 03592-202099",
                'emergency_suicide': "💭 *आत्महत्या रोकथाम हेल्पलाइन*\nडायल करें: 9152987821",
                'emergency_women': "👩 *महिला हेल्पलाइन*\nडायल करें: 1091\nराज्य आयोग: 03592-205607",
                'ex_gratia_intro': "आप पात्र हो सकते हैं यदि आपको निम्नलिखित कारणों से नुकसान हुआ है:\n• भारी बारिश, बाढ़, या भूस्खलन\n• भूकंप या अन्य प्राकृतिक आपदाएं\n• ओलावृष्टि से फसल की क्षति\n• प्राकृतिक आपदाओं से घर की क्षति\n• पशुओं की हानि\n\nक्या आप आवेदन के साथ आगे बढ़ना चाहते हैं?",
                'ex_gratia_form': "कृपया अपना पूरा नाम दर्ज करें:",
                'ex_gratia_father': "आपके पिता का नाम क्या है?",
                'ex_gratia_village': "आप किस गाँव से हैं?",
                'ex_gratia_contact': "आपका संपर्क नंबर क्या है? (10 अंक)",
                'ex_gratia_ward': "आपका वार्ड नंबर या नाम क्या है?",
                'ex_gratia_gpu': "आप किस ग्राम पंचायत इकाई (GPU) के अंतर्गत हैं?",
                'ex_gratia_khatiyan': "आपका खतियान नंबर क्या है? (जमीन का रिकॉर्ड नंबर)",
                'ex_gratia_plot': "आपका प्लॉट नंबर क्या है?",
                'ex_gratia_damage': "कृपया क्षति का विस्तृत विवरण प्रदान करें:",
                'certificate_info': "सिक्किम SSO पोर्टल के माध्यम से सेवाओं के लिए आवेदन करने के लिए:\n1. सिक्किम SSO पोर्टल पर पंजीकरण करें और खाता बनाएं\n2. अपने सिक्किम SSO क्रेडेंशियल्स का उपयोग करके लॉगिन करें\n3. वांछित सेवा पर नेविगेट करें\n4. आवेदन फॉर्म भरें\n5. आवश्यक दस्तावेज अपलोड करें\n6. अपने आवेदन की स्थिति ऑनलाइन ट्रैक करें\n\nक्या आप CSC ऑपरेटर या सिंगल विंडो ऑपरेटर के माध्यम से आवेदन करना चाहते हैं?",
                'other_emergency': "🚨 अन्य आपातकालीन सेवाएं",
                'back_main_menu': "🔙 मुख्य मेनू पर वापस",
                'language_menu': "🌐 *भाषा चयन*\n\nकृपया अपनी पसंदीदा भाषा चुनें:",
                'language_changed': "✅ भाषा सफलतापूर्वक हिंदी में बदल दी गई!",
                'language_button_english': "🇺🇸 English",
                'language_button_hindi': "🇮🇳 हिंदी",
                'complaint_title': "*शिकायत/ग्रिवेंस दर्ज करें* 📝",
                'complaint_name_prompt': "कृपया अपना पूरा नाम दर्ज करें:",
                'complaint_mobile_prompt': "कृपया अपना मोबाइल नंबर दर्ज करें:",
                'complaint_mobile_error': "कृपया एक वैध 10-अंकीय मोबाइल नंबर दर्ज करें।",
                'complaint_description_prompt': "कृपया अपनी शिकायत का विस्तृत विवरण दें:",
                'complaint_success': "✅ *शिकायत सफलतापूर्वक दर्ज की गई*\n\n🆔 शिकायत आईडी: {complaint_id}\n👤 नाम: {name}\n📱 मोबाइल: {mobile}\n🔗 टेलीग्राम: @{telegram_username}\n\nआपकी शिकायत दर्ज कर दी गई है और जल्द ही प्रोसेस की जाएगी। कृपया भविष्य के संदर्भ के लिए अपनी शिकायत आईडी सहेजें।",
                'certificate_gpu_prompt': "कृपया अपना GPU (ग्राम पंचायत इकाई) दर्ज करें:",
                'certificate_sso_message': "आप सीधे सिक्किम SSO पोर्टल पर आवेदन कर सकते हैं: https://sso.sikkim.gov.in",
                'certificate_gpu_not_found': "क्षमा करें, आपके GPU के लिए कोई CSC ऑपरेटर नहीं मिला। कृपया GPU नंबर जांचें और पुनः प्रयास करें।",
                'certificate_csc_details': "*CSC ऑपरेटर विवरण*\n\nनाम: {name}\nसंपर्क: {contact}\nसमय: {timings}",
                'certificate_error': "क्षमा करें, आपके अनुरोध को प्रोसेस करने में त्रुटि हुई। कृपया पुनः प्रयास करें।",
                
                # New features responses
                'scheme_info': """🏛️ **सरकारी योजनाएं और आवेदन**

उपलब्ध योजनाएं:
• पीएम किसान
• पीएम फसल बीमा
• पीएम विश्वकर्मा
• मत्स्य पालन पंजीकरण
• किसान क्रेडिट कार्ड
• और भी बहुत कुछ...

अधिक जानने और आवेदन करने के लिए योजना चुनें:""",
                
                'contacts_info': """📞 **महत्वपूर्ण संपर्क**

आपको किस प्रकार का संपर्क चाहिए:
• **सीएससी (सामान्य सेवा केंद्र)** - अपना निकटतम सीएससी ऑपरेटर खोजें
• **बीएलओ (बूथ लेवल अधिकारी)** - मतदाता सूची सेवाएं
• **आधार सेवाएं** - आधार कार्ड संबंधित सेवाएं

एक विकल्प चुनें:""",
                
                'feedback_info': """📝 **प्रतिक्रिया दें**

हमारी सेवाओं को बेहतर बनाने के लिए आपकी प्रतिक्रिया महत्वपूर्ण है। कृपया प्रदान करें:
• आपका नाम
• फोन नंबर
• आपकी प्रतिक्रिया/सुझाव

आइए आपके नाम से शुरू करें:""",
                
                'feedback_name_prompt': "कृपया अपना नाम दर्ज करें:",
                'feedback_phone_prompt': "कृपया अपना फोन नंबर दर्ज करें:",
                'feedback_message_prompt': "कृपया अपनी प्रतिक्रिया या सुझाव साझा करें:",
                'feedback_success': """✅ **प्रतिक्रिया सफलतापूर्वक सबमिट की गई!**

आपकी प्रतिक्रिया के लिए धन्यवाद। हम इसे समीक्षा करेंगे और सुधारों पर काम करेंगे।

आपकी प्रतिक्रिया आईडी: {feedback_id}""",
            },
            'nepali': {
                'welcome': "स्मार्टगभ सहायकमा स्वागत छ! म तपाईंलाई कसरी मद्दत गर्न सक्छु?",
                'main_menu': """🏛️ *स्मार्टगभ सहायकमा स्वागत छ* 🏛️

हाम्रो सेवाहरू समावेश छन्:

1. *होमस्टे बुक गर्नुहोस्* 🏡
   • पर्यटन स्थलहरू अनुसार खोज्नुहोस्
   • रेटिङ र मूल्यहरू हेर्नुहोस्
   • मालिकहरूसँग सिधा सम्पर्क

2. *आकस्मिक सेवाहरू* 🚨
   • एम्बुलेन्स (102/108)
   • प्रहरी हेल्पलाइन
   • आत्महत्या रोकथाम
   • स्वास्थ्य हेल्पलाइन
   • महिला हेल्पलाइन
   • अग्निशमन आकस्मिक
   • आपदा रिपोर्ट गर्नुहोस्

3. *शिकायत दर्ता गर्नुहोस्* 📝
   • आफ्नो शिकायत दर्ता गर्नुहोस्
   • शिकायत ट्र्याकिङ आईडी प्राप्त गर्नुहोस्
   • 24/7 निगरानी

4. *प्रमाणपत्रको लागि आवेदन गर्नुहोस्* 💻
   • CSC सञ्चालक सहायता
   • सिक्किम SSO पोर्टल लिङ्क
   • आवेदन स्थिति ट्र्याक गर्नुहोस्

5. *आपदा व्यवस्थापन* 🆘
   • एक्स-ग्रेटियाको लागि आवेदन गर्नुहोस्
   • आवेदन स्थिति जाँच गर्नुहोस्
   • राहत मापदण्ड हेर्नुहोस्
   • आकस्मिक सम्पर्कहरू

कृपया जारी राख्न सेवा छान्नुहोस्:""",
                'button_homestay': "🏡 होमस्टे बुक गर्नुहोस्",
                'button_emergency': "🚨 आकस्मिक सेवाहरू",
                'button_complaint': "📝 शिकायत दर्ता गर्नुहोस्",
                'button_certificate': "💻 प्रमाणपत्रको लागि आवेदन",
                'button_disaster': "🆘 आपदा व्यवस्थापन",
                'button_schemes': "🏛️ सरकारी योजनाहरू",
                'button_contacts': "📞 महत्वपूर्ण सम्पर्कहरू",
                'button_feedback': "📝 प्रतिक्रिया दिनुहोस्",
                'error': "माफ गर्नुहोस्, त्रुटि भयो। कृपया पुन: प्रयास गर्नुहोस्।",
                'unknown': "मलाई बुझ्न सकिएन। यहाँ उपलब्ध सेवाहरू छन्:",
                'processing': "तपाईंको अनुरोध प्रशोधन गरिँदैछ...",
                'success': "तपाईंको अनुरोध सफलतापूर्वक प्रशोधन गरियो।",
                'cancelled': "प्रक्रिया रद्द गरियो। म अरु कसरी मद्दत गर्न सक्छु?",
                'emergency_ambulance': "🚑 *एम्बुलेन्स आकस्मिक*\nडायल गर्नुहोस्: 102 वा 108\nकन्ट्रोल रूम: 03592-202033",
                'emergency_police': "👮 *प्रहरी आकस्मिक*\nडायल गर्नुहोस्: 100\nकन्ट्रोल रूम: 03592-202022",
                'emergency_fire': "🚒 *अग्निशमन आकस्मिक*\nडायल गर्नुहोस्: 101\nकन्ट्रोल रूम: 03592-202099",
                'emergency_suicide': "💭 *आत्महत्या रोकथाम हेल्पलाइन*\nडायल गर्नुहोस्: 9152987821",
                'emergency_women': "👩 *महिला हेल्पलाइन*\nडायल गर्नुहोस्: 1091\nराज्य आयोग: 03592-205607",
                'ex_gratia_intro': "तपाईं पात्र हुन सक्नुहुन्छ यदि तपाईंलाई निम्न कारणहरूले क्षति भएको छ:\n• भारी वर्षा, बाढी, वा भूस्खलन\n• भूकम्प वा अन्य प्राकृतिक आपदाहरू\n• असिनाले फसलको क्षति\n• प्राकृतिक आपदाहरूले घरको क्षति\n• पशुहरूको हानि\n\nके तपाईं आवेदनसँग अगाडि बढ्न चाहनुहुन्छ?",
                'ex_gratia_form': "कृपया आफ्नो पूरा नाम प्रविष्ट गर्नुहोस्:",
                'ex_gratia_father': "तपाईंको बुबाको नाम के हो?",
                'ex_gratia_village': "तपाईं कुन गाउँबाट हुनुहुन्छ?",
                'ex_gratia_contact': "तपाईंको सम्पर्क नम्बर के हो? (10 अंक)",
                'ex_gratia_ward': "तपाईंको वार्ड नम्बर वा नाम के हो?",
                'ex_gratia_gpu': "तपाईं कुन ग्राम पंचायत इकाई (GPU) अन्तर्गत हुनुहुन्छ?",
                'ex_gratia_khatiyan': "तपाईंको खतियान नम्बर के हो? (जमिनको रेकर्ड नम्बर)",
                'ex_gratia_plot': "तपाईंको प्लट नम्बर के हो?",
                'ex_gratia_damage': "कृपया क्षतिको विस्तृत विवरण प्रदान गर्नुहोस्:",
                'certificate_info': "सिक्किम SSO पोर्टल मार्फत सेवाहरूको लागि आवेदन गर्न:\n1. सिक्किम SSO पोर्टलमा दर्ता गर्नुहोस् र खाता सिर्जना गर्नुहोस्\n2. आफ्ना सिक्किम SSO क्रेडेन्सियलहरू प्रयोग गरेर लगइन गर्नुहोस्\n3. इच्छित सेवामा नेविगेट गर्नुहोस्\n4. आवेदन फारम भर्नुहोस्\n5. आवश्यक कागजातहरू अपलोड गर्नुहोस्\n6. आफ्नो आवेदनको स्थिति अनलाइन ट्र्याक गर्नुहोस्\n\nके तपाईं CSC सञ्चालक वा सिङ्गल विन्डो सञ्चालक मार्फत आवेदन गर्न चाहनुहुन्छ?",
                'other_emergency': "🚨 अन्य आकस्मिक सेवाहरू",
                'back_main_menu': "🔙 मुख्य मेनुमा फिर्ता",
                'language_menu': "🌐 *भाषा चयन*\n\nकृपया तपाईंको मनपर्ने भाषा छान्नुहोस्:",
                'language_changed': "✅ भाषा सफलतापूर्वक नेपालीमा बदलियो!",
                'language_button_english': "🇺🇸 English",
                'language_button_hindi': "🇮🇳 हिंदी",
                'complaint_title': "*शिकायत/ग्रिवेंस दर्ता गर्नुहोस्* 📝",
                'complaint_name_prompt': "कृपया आफ्नो पूरा नाम प्रविष्ट गर्नुहोस्:",
                'complaint_mobile_prompt': "कृपया आफ्नो मोबाइल नम्बर प्रविष्ट गर्नुहोस्:",
                'complaint_mobile_error': "कृपया एक वैध 10-अंकीय मोबाइल नम्बर प्रविष्ट गर्नुहोस्।",
                'complaint_description_prompt': "कृपया आफ्नो शिकायतको विस्तृत विवरण दिनुहोस्:",
                'complaint_success': "✅ *शिकायत सफलतापूर्वक दर्ता गरियो*\n\n🆔 शिकायत आईडी: {complaint_id}\n👤 नाम: {name}\n📱 मोबाइल: {mobile}\n🔗 टेलीग्राम: @{telegram_username}\n\nतपाईंको शिकायत दर्ता गरियो र चाँडै प्रशोधन गरिनेछ। कृपया भविष्यको सन्दर्भको लागि आफ्नो शिकायत आईडी सुरक्षित गर्नुहोस्।",
                'certificate_gpu_prompt': "कृपया आफ्नो GPU (ग्राम पंचायत इकाई) प्रविष्ट गर्नुहोस्:",
                'certificate_sso_message': "तपाईं सिधै सिक्किम SSO पोर्टलमा आवेदन गर्न सक्नुहुन्छ: https://sso.sikkim.gov.in",
                'certificate_gpu_not_found': "माफ गर्नुहोस्, तपाईंको GPU को लागि कुनै CSC सञ्चालक फेला परेनन्। कृपया GPU नम्बर जाँच गर्नुहोस् र पुन: प्रयास गर्नुहोस्।",
                'certificate_csc_details': "*CSC सञ्चालक विवरण*\n\nनाम: {name}\nसम्पर्क: {contact}\nसमय: {timings}",
                'certificate_error': "माफ गर्नुहोस्, तपाईंको अनुरोध प्रशोधन गर्दा त्रुटि भयो। कृपया पुन: प्रयास गर्नुहोस्।",
                
                # New features responses
                'scheme_info': """🏛️ **सरकारी योजनाहरू र आवेदनहरू**

उपलब्ध योजनाहरू:
• पीएम किसान
• पीएम फसल बीमा
• पीएम विश्वकर्मा
• माछा पालन दर्ता
• किसान क्रेडिट कार्ड
• र धेरै अन्य...

थप जान्न र आवेदन गर्न योजना छान्नुहोस्:""",
                
                'contacts_info': """📞 **महत्वपूर्ण सम्पर्कहरू**

तपाईंलाई कुन प्रकारको सम्पर्क चाहिन्छ:
• **CSC (साझा सेवा केन्द्र)** - आफ्नो नजिकैको CSC सञ्चालक फेला पार्नुहोस्
• **बूथ लेवल अधिकारी)** - मतदाता सूची सेवाहरू
• **आधार सेवाहरू** - आधार कार्ड सम्बन्धित सेवाहरू

एउटा विकल्प छान्नुहोस्:""",
                
                'feedback_info': """📝 **प्रतिक्रिया दिनुहोस्**

हाम्रो सेवाहरू सुधार गर्न तपाईंको प्रतिक्रिया महत्वपूर्ण छ। कृपया प्रदान गर्नुहोस्:
• तपाईंको नाम
• फोन नम्बर
• तपाईंको प्रतिक्रिया/सुझावहरू

तपाईंको नामबाट सुरु गर्नुहोस्:""",
                
                'feedback_name_prompt': "कृपया आफ्नो नाम प्रविष्ट गर्नुहोस्:",
                'feedback_phone_prompt': "कृपया आफ्नो फोन नम्बर प्रविष्ट गर्नुहोस्:",
                'feedback_message_prompt': "कृपया आफ्नो प्रतिक्रिया वा सुझाव साझा गर्नुहोस्:",
                'feedback_success': """✅ **प्रतिक्रिया सफलतापूर्वक सबमिट गरियो!**

तपाईंको प्रतिक्रियाको लागि धन्यवाद। हामी यसलाई समीक्षा गर्नेछौं र सुधारहरूमा काम गर्नेछौं।

तपाईंको प्रतिक्रिया आईडी: {feedback_id}""",
            }
        }

    def _get_user_state(self, user_id: int) -> dict:
        """Safely get user state with locking"""
        with self._state_lock:
            return self.user_states.get(user_id, {})

    def _set_user_state(self, user_id: int, state: dict):
        """Safely set user state with locking"""
        with self._state_lock:
            self.user_states[user_id] = state
            logger.info(f"🔒 STATE UPDATE: User {user_id} → {state}")

    def _clear_user_state(self, user_id: int):
        """Safely clear user state with locking"""
        with self._state_lock:
            if user_id in self.user_states:
                del self.user_states[user_id]
                logger.info(f"🧹 STATE CLEARED: User {user_id}")

    def _get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        with self._state_lock:
            return self.user_languages.get(user_id, 'english')

    def _set_user_language(self, user_id: int, language: str):
        """Set user's preferred language"""
        with self._state_lock:
            self.user_languages[user_id] = language
            logger.info(f"🌐 LANGUAGE SET: User {user_id} → {language}")

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def request_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service_type: str = "emergency"):
        """Request user's location for emergency services or complaints"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Get current state to preserve existing data
        current_state = self._get_user_state(user_id)
        
        logger.info(f"🔒 [LOCATION] Current state before location request: {current_state}")
        
        # Set state to expect location while preserving existing data
        new_state = {
            "workflow": "location_request",
            "service_type": service_type,
            "stage": "waiting_location"
        }
        
        # Preserve existing application data if it exists
        if current_state.get("data"):
            new_state["data"] = current_state["data"]
            logger.info(f"🔒 [LOCATION] Preserved application data: {list(current_state['data'].keys())}")
        else:
            logger.warning(f"⚠️ [LOCATION] No application data found to preserve")
            logger.warning(f"⚠️ [LOCATION] Current state keys: {list(current_state.keys())}")
        
        self._set_user_state(user_id, new_state)
        logger.info(f"🔒 [LOCATION] New state after location request: {new_state}")
        
        # Create location request keyboard with fallback options
        location_button = KeyboardButton("📍 Share My Location", request_location=True)
        manual_location_button = KeyboardButton("📝 Type Location Name")
        skip_location_button = KeyboardButton("⏭️ Skip Location")
        cancel_button = KeyboardButton("❌ Cancel")
        keyboard = [[location_button], [manual_location_button], [skip_location_button], [cancel_button]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        # Get appropriate message based on service type
        if service_type == "emergency":
            if user_lang == "hindi":
                message = "🚨 **आपातकालीन सेवाओं के लिए आपका स्थान आवश्यक है**\n\nकृपया अपना स्थान साझा करें ताकि हम आपको निकटतम आपातकालीन सेवाएं प्रदान कर सकें।"
            elif user_lang == "nepali":
                message = "🚨 **आपतकालीन सेवाहरूको लागि तपाईंको स्थान आवश्यक छ**\n\nकृपया आफ्नो स्थान साझा गर्नुहोस् ताकि हामी तपाईंलाई नजिकको आपतकालीन सेवाहरू प्रदान गर्न सक्छौं।"
            else:
                message = "🚨 **Your location is required for emergency services**\n\nPlease share your location so we can provide you with the nearest emergency services."
        elif service_type == "complaint":
            if user_lang == "hindi":
                message = "📝 **शिकायत दर्ज करने के लिए आपका स्थान आवश्यक है**\n\nकृपया अपना स्थान साझा करें ताकि हम आपकी शिकायत को सही तरीके से दर्ज कर सकें।"
            elif user_lang == "nepali":
                message = "📝 **शिकायत दर्ता गर्नको लागि तपाईंको स्थान आवश्यक छ**\n\nकृपया आफ्नो स्थान साझा गर्नुहोस् ताकि हामी तपाईंको शिकायतलाई सही तरिकाले दर्ता गर्न सक्छौं।"
            else:
                message = "📝 **Your location is required to file a complaint**\n\nPlease share your location so we can properly register your complaint."
        elif service_type == "ex_gratia":
            if user_lang == "hindi":
                message = "🏛️ **एक्स-ग्रेटिया आवेदन के लिए आपका स्थान आवश्यक है**\n\nकृपया अपना स्थान साझा करें ताकि हम आपके आवेदन को सही तरीके से दर्ज कर सकें।"
            elif user_lang == "nepali":
                message = "🏛️ **एक्स-ग्रेटिया आवेदनको लागि तपाईंको स्थान आवश्यक छ**\n\nकृपया आफ्नो स्थान साझा गर्नुहोस् ताकि हामी तपाईंको आवेदनलाई सही तरिकाले दर्ता गर्न सक्छौं।"
            else:
                message = "🏛️ **Your location is required for NC Exgratia application**\n\nPlease share your location so we can properly register your application with the government."
        else:
            # Default message for any other service type
            if user_lang == "hindi":
                message = "📍 **कृपया अपना स्थान साझा करें**\n\nआपका स्थान हमारी सेवाओं को बेहतर बनाने में मदद करेगा।"
            elif user_lang == "nepali":
                message = "📍 **कृपया आफ्नो स्थान साझा गर्नुहोस्**\n\nतपाईंको स्थानले हाम्रो सेवाहरूलाई राम्रो बनाउन मद्दत गर्नेछ।"
            else:
                message = "📍 **Please share your location**\n\nYour location will help us provide better services."
        
        # Handle both callback queries and regular messages
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown')
            await update.callback_query.message.reply_text("📍 Please use the button below to share your location:", reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_location_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when user shares their location"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        location = update.message.location
        
        logger.info(f"📍 [LOCATION] Received location from user {user_id}")
        logger.info(f"📍 [LOCATION] Location object: {location}")
        
        # Check if location is actually provided
        if not location or location.latitude is None or location.longitude is None:
            logger.warning(f"📍 [LOCATION] No valid location received from user {user_id}")
            
            # Get current state
            state = self._get_user_state(user_id)
            service_type = state.get("service_type", "emergency")
            
            # Send error message
            if user_lang == "hindi":
                error_msg = "❌ स्थान प्राप्त नहीं हुआ। कृपया अपने फोन की सेटिंग्स जांचें और फिर से कोशिश करें।"
            elif user_lang == "nepali":
                error_msg = "❌ स्थान प्राप्त भएन। कृपया आफ्नो फोनको सेटिङहरू जाँच गर्नुहोस् र फेरि प्रयास गर्नुहोस्।"
            else:
                error_msg = "❌ Location not received. Please check your phone settings and try again."
            
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            return
        
        logger.info(f"📍 [LOCATION] Valid location received: {location.latitude}, {location.longitude}")
        
        # Get current state
        state = self._get_user_state(user_id)
        service_type = state.get("service_type", "emergency")
        
        logger.info(f"📍 [LOCATION] Service type: {service_type}, Current state: {state}")
        
        # Store location data
        location_data = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update state with location
        state["location"] = location_data
        self._set_user_state(user_id, state)
        
        # Log location to Google Sheets
        user_name = update.effective_user.first_name or "Unknown"
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="location_shared",
            query_text=f"Location shared for {service_type}",
            language=user_lang,
            bot_response=f"Lat: {location.latitude}, Long: {location.longitude}",
            latitude=location.latitude,
            longitude=location.longitude,
            service_type=service_type
        )
        
        # Provide appropriate response based on service type
        if service_type == "emergency":
            # Check if this is an emergency report workflow or emergency services
            if state.get("workflow") == "emergency_report":
                await self.handle_emergency_report_with_location(update, context, location_data)
            else:
                await self.handle_emergency_with_location(update, context, location_data)
            # Clear state for emergency services
            self._clear_user_state(user_id)
        elif service_type == "complaint":
            await self.handle_complaint_with_location(update, context, location_data)
            # Don't clear state for complaints - let the complaint workflow handle it
        elif service_type == "ex_gratia":
            # Handle ex-gratia application with location
            await self.handle_ex_gratia_with_location(update, context, location_data)

    async def handle_emergency_with_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location_data: dict):
        """Handle emergency services with user location"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Create normal keyboard
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get location display safely
        location_display = ""
        if location_data.get('latitude') and location_data.get('longitude'):
            location_display = f"{location_data['latitude']:.6f}, {location_data['longitude']:.6f}"
        elif location_data.get('location_name'):
            location_display = location_data['location_name']
        else:
            location_display = "Not provided"
        
        # Enhanced emergency response with location
        if user_lang == "hindi":
            message = f"""🚨 **आपातकालीन सेवाएं - स्थान प्राप्त** 🚨

📍 **आपका स्थान**: {location_display}

🚑 **निकटतम आपातकालीन सेवाएं**:
• एम्बुलेंस: 102
• पुलिस: 100  
• अग्निशमन: 101
• राज्य आपातकाल: 1070

⚡ **प्रतिक्रिया समय**: 10-15 मिनट

कृपया अपनी आपातकालीन सेवा का चयन करें:"""
        elif user_lang == "nepali":
            message = f"""🚨 **आपतकालीन सेवाहरू - स्थान प्राप्त** 🚨

📍 **तपाईंको स्थान**: {location_display}

🚑 **नजिकको आपतकालीन सेवाहरू**:
• एम्बुलेन्स: 102
• प्रहरी: 100
• दमकल: 101
• राज्य आपतकालीन: 1070

⚡ **प्रतिक्रिया समय**: 10-15 मिनेट

कृपया आफ्नो आपतकालीन सेवा छान्नुहोस्:"""
        else:
            message = f"""🚨 **Emergency Services - Location Received** 🚨

📍 **Your Location**: {location_display}

🚑 **Nearest Emergency Services**:
• Ambulance: 102
• Police: 100
• Fire: 101
• State Emergency: 1070

⚡ **Response Time**: 10-15 minutes

Please select your emergency service:"""
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_complaint_with_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location_data: dict):
        """Handle complaint filing with user location"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        
        # Generate complaint ID
        now = datetime.now()
        complaint_id = f"CMP{now.strftime('%Y%m%d')}{random.randint(100, 999)}"
        
        # Get complaint details from state
        entered_name = state.get('entered_name', '')
        mobile = state.get('mobile', '')
        complaint_description = state.get('complaint_description', '')
        
        # Save complaint to CSV with location
        latitude = location_data.get('latitude', '')
        longitude = location_data.get('longitude', '')
        location_name = location_data.get('location_name', '')
        
        complaint_data = {
            'submission_id': complaint_id,
            'name': entered_name,
            'phone': mobile,
            'submission_date': now.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Pending',
            'details': complaint_description,
            'language': user_lang,
            'latitude': latitude,
            'longitude': longitude,
            'location_name': location_name
        }
        
        df = pd.DataFrame([complaint_data])
        df.to_csv('data/submission.csv', mode='a', header=False, index=False)
        
                # Create success message with all details
        location_display = ""
        if 'latitude' in location_data and 'longitude' in location_data and location_data['latitude'] and location_data['longitude']:
            location_display = f"{location_data['latitude']:.6f}, {location_data['longitude']:.6f}"
        elif 'location_name' in location_data and location_data['location_name']:
            location_display = location_data['location_name']
        else:
            location_display = "Not provided"
        
        if user_lang == "hindi":
            success_message = f"""✅ **शिकायत सफलतापूर्वक दर्ज की गई!**
            
            📝 **रिपोर्ट विवरण:**
            • **नाम**: {entered_name}
            • **मोबाइल**: {mobile}
            • **समस्या**: {complaint_description}
            • **स्थान**: {location_display}
            • **रिपोर्ट ID**: #{complaint_id}
            
            🚨 आपातकालीन सेवाओं को सूचित कर दिया गया है।"""
        elif user_lang == "nepali":
            success_message = f"""✅ **शिकायत सफलतापूर्वक दर्ता गरियो!**
            
            📝 **रिपोर्ट विवरण:**
            • **नाम**: {entered_name}
            • **मोबाइल**: {mobile}
            • **समस्या**: {complaint_description}
            • **स्थान**: {location_display}
            • **रिपोर्ट ID**: #{complaint_id}
            
            🚨 आपतकालीन सेवाहरूलाई सूचित गरियो।"""
        else:
            success_message = f"""✅ **Report submitted successfully!**
            
            📝 **Report Details:**
            • **Name**: {entered_name}
            • **Mobile**: {mobile}
            • **Issue**: {complaint_description}
            • **Location**: {location_display}
            • **Report ID**: #{complaint_id}
            
            🚨 Emergency services have been notified."""
        
        # Create normal keyboard
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clear user state
        self._clear_user_state(user_id)
        
        # Log to Google Sheets
        user_name = update.effective_user.first_name or "Unknown"
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="complaint_submitted",
            query_text=f"Complaint submitted: {complaint_description}",
            language=user_lang,
            bot_response=success_message,
            complaint_id=complaint_id,
            latitude=location_data.get('latitude', ''),
            longitude=location_data.get('longitude', '')
        )

    async def handle_emergency_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the emergency workflow steps"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        text = update.message.text
        state = self._get_user_state(user_id)
        step = state.get("step")
        
        if step == "name":
            # Store both Telegram username and entered name
            telegram_username = update.effective_user.first_name or "Unknown"
            state["telegram_username"] = telegram_username
            state["entered_name"] = text
            state["name"] = f"{text} (@{telegram_username})"  # Combine both names
            state["step"] = "description"
            self._set_user_state(user_id, state)
            
            if user_lang == "hindi":
                message = "धन्यवाद। कृपया आपातकालीन स्थिति का वर्णन करें:"
            elif user_lang == "nepali":
                message = "धन्यवाद। कृपया आपतकालीन स्थितिको वर्णन गर्नुहोस्:"
            else:
                message = "Thank you. Please describe the emergency/issue:"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        
        elif step == "description":
            # Store emergency description and request location
            state["emergency_description"] = text
            state["step"] = "location"
            self._set_user_state(user_id, state)
            
            if user_lang == "hindi":
                message = "स्थान डिस्पैच के लिए आवश्यक है। कृपया अपना वर्तमान स्थान साझा करें 📍"
            elif user_lang == "nepali":
                message = "स्थान डिस्पैचको लागि आवश्यक छ। कृपया आफ्नो वर्तमान स्थान साझा गर्नुहोस् 📍"
            else:
                message = "Location is required for dispatch. Please share your current location 📍"
            
            # Request location for emergency
            await self.request_location(update, context, "emergency")
            return

    async def handle_manual_location_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle manual location input workflow"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        text = update.message.text
        state = self._get_user_state(user_id)
        step = state.get("step")
        
        if step == "latitude":
            try:
                latitude = float(text)
                if -90 <= latitude <= 90:
                    state["manual_latitude"] = latitude
                    state["step"] = "longitude"
                    self._set_user_state(user_id, state)
                    
                    if user_lang == "hindi":
                        message = "📍 अब कृपया देशांतर (Longitude) दर्ज करें:\n\nउदाहरण: 88.6065"
                    elif user_lang == "nepali":
                        message = "📍 अब कृपया देशान्तर (Longitude) दर्ता गर्नुहोस्:\n\nउदाहरण: 88.6065"
                    else:
                        message = "📍 Now please enter the longitude:\n\nExample: 88.6065"
                    
                    await update.message.reply_text(message, parse_mode='Markdown')
                else:
                    if user_lang == "hindi":
                        message = "❌ अमान्य अक्षांश। कृपया -90 से 90 के बीच का मान दर्ज करें।"
                    elif user_lang == "nepali":
                        message = "❌ अमान्य अक्षांश। कृपया -90 देखि 90 को बीचको मान दर्ता गर्नुहोस्।"
                    else:
                        message = "❌ Invalid latitude. Please enter a value between -90 and 90."
                    await update.message.reply_text(message, parse_mode='Markdown')
            except ValueError:
                if user_lang == "hindi":
                    message = "❌ कृपया एक वैध संख्या दर्ज करें।"
                elif user_lang == "nepali":
                    message = "❌ कृपया एक वैध संख्या दर्ता गर्नुहोस्।"
                else:
                    message = "❌ Please enter a valid number."
                await update.message.reply_text(message, parse_mode='Markdown')
        
        elif step == "longitude":
            try:
                longitude = float(text)
                if -180 <= longitude <= 180:
                    latitude = state.get("manual_latitude")
                    
                    # Create location data
                    location_data = {
                        "latitude": latitude,
                        "longitude": longitude,
                        "timestamp": datetime.now().isoformat(),
                        "source": "manual"
                    }
                    
                    # Process the location based on service type
                    service_type = state.get("service_type", "emergency")
                    
                    if service_type == "emergency":
                        if state.get("workflow") == "emergency_report":
                            await self.handle_emergency_report_with_location(update, context, location_data)
                        else:
                            await self.handle_emergency_with_location(update, context, location_data)
                    elif service_type == "complaint":
                        await self.handle_complaint_with_location(update, context, location_data)
                    
                    # Clear state
                    self._clear_user_state(user_id)
                else:
                    if user_lang == "hindi":
                        message = "❌ अमान्य देशांतर। कृपया -180 से 180 के बीच का मान दर्ज करें।"
                    elif user_lang == "nepali":
                        message = "❌ अमान्य देशान्तर। कृपया -180 देखि 180 को बीचको मान दर्ता गर्नुहोस्।"
                    else:
                        message = "❌ Invalid longitude. Please enter a value between -180 and 180."
                    await update.message.reply_text(message, parse_mode='Markdown')
            except ValueError:
                if user_lang == "hindi":
                    message = "❌ कृपया एक वैध संख्या दर्ज करें।"
                elif user_lang == "nepali":
                    message = "❌ कृपया एक वैध संख्या दर्ता गर्नुहोस्।"
                else:
                    message = "❌ Please enter a valid number."
                await update.message.reply_text(message, parse_mode='Markdown')

    async def handle_manual_location_name_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle manual location name input workflow"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        text = update.message.text
        state = self._get_user_state(user_id)
        step = state.get("step")
        
        if step == "location_name":
            # Validate location name (not empty and reasonable length)
            if len(text.strip()) < 2:
                if user_lang == "hindi":
                    message = "❌ कृपया एक वैध स्थान का नाम दर्ज करें (कम से कम 2 अक्षर)।"
                elif user_lang == "nepali":
                    message = "❌ कृपया एक वैध स्थानको नाम दर्ता गर्नुहोस् (कम्तिमा 2 अक्षर)।"
                else:
                    message = "❌ Please enter a valid location name (at least 2 characters)."
                await update.message.reply_text(message, parse_mode='Markdown')
                return
            
            # Create location data with name
            location_data = {
                "location_name": text.strip(),
                "timestamp": datetime.now().isoformat(),
                "source": "manual_name"
            }
            
            # Process the location based on service type
            service_type = state.get("service_type", "emergency")
            
            if service_type == "emergency":
                if state.get("workflow") == "emergency_report":
                    await self.handle_emergency_report_with_location(update, context, location_data)
                else:
                    await self.handle_emergency_with_location(update, context, location_data)
            elif service_type == "complaint":
                await self.handle_complaint_with_location(update, context, location_data)
            
            # Clear state
            self._clear_user_state(user_id)

    async def handle_emergency_report_with_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location_data: dict):
        """Handle emergency report with user location"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        
        # Generate emergency report ID
        now = datetime.now()
        emergency_id = f"ER{now.strftime('%Y%m%d')}{random.randint(100, 999)}"
        
        # Get emergency details from state
        entered_name = state.get('entered_name', '')
        emergency_description = state.get('emergency_description', '')
        
        # Create success message with all details
        location_display = ""
        if 'latitude' in location_data and 'longitude' in location_data:
            location_display = f"{location_data['latitude']:.6f}, {location_data['longitude']:.6f}"
        elif 'location_name' in location_data:
            location_display = location_data['location_name']
        else:
            location_display = "Not provided"
        
        if user_lang == "hindi":
            success_message = f"""✅ **रिपोर्ट सफलतापूर्वक प्रस्तुत की गई!**
            
            📝 **रिपोर्ट विवरण:**
            • **नाम**: {entered_name}
            • **समस्या**: {emergency_description}
            • **स्थान**: {location_display}
            • **रिपोर्ट ID**: #{emergency_id}
            
            🚨 आपातकालीन सेवाओं को सूचित कर दिया गया है।"""
        elif user_lang == "nepali":
            success_message = f"""✅ **रिपोर्ट सफलतापूर्वक प्रस्तुत गरियो!**
            
            📝 **रिपोर्ट विवरण:**
            • **नाम**: {entered_name}
            • **समस्या**: {emergency_description}
            • **स्थान**: {location_display}
            • **रिपोर्ट ID**: #{emergency_id}
            
            🚨 आपतकालीन सेवाहरूलाई सूचित गरियो।"""
        else:
            success_message = f"""✅ **Report submitted successfully!**
            
            📝 **Report Details:**
            • **Name**: {entered_name}
            • **Issue**: {emergency_description}
            • **Location**: {location_display}
            • **Report ID**: #{emergency_id}
            
            🚨 Emergency services have been notified."""
        
        # Create normal keyboard
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clear user state
        self._clear_user_state(user_id)
        
        # Log to Google Sheets
        user_name = update.effective_user.first_name or "Unknown"
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="emergency_report_submitted",
            query_text=f"Emergency report submitted: {emergency_description}",
            language=user_lang,
            bot_response=success_message,
            emergency_id=emergency_id,
            latitude=location_data.get('latitude', ''),
            longitude=location_data.get('longitude', '')
        )

    def _log_to_sheets(self, user_id: int, user_name: str, interaction_type: str, 
                      query_text: str, language: str, bot_response: str, **kwargs):
        """Log interaction to Google Sheets"""
        if not self.sheets_service:
            return
        
        try:
            if interaction_type == "complaint":
                self.sheets_service.log_complaint(
                    user_id=user_id,
                    user_name=user_name,
                    complaint_text=query_text,
                    complaint_type=kwargs.get('complaint_type', 'General'),
                    language=language,
                    status=kwargs.get('status', 'New')
                )
            elif interaction_type == "homestay":
                self.sheets_service.log_homestay_query(
                    user_id=user_id,
                    user_name=user_name,
                    place=kwargs.get('place', ''),
                    query_text=query_text,
                    language=language,
                    result=bot_response
                )
            elif interaction_type == "emergency":
                self.sheets_service.log_emergency_service(
                    user_id=user_id,
                    user_name=user_name,
                    service_type=kwargs.get('service_type', 'General'),
                    query_text=query_text,
                    language=language,
                    result=bot_response
                )
            elif interaction_type == "cab_booking":
                self.sheets_service.log_cab_booking_query(
                    user_id=user_id,
                    user_name=user_name,
                    destination=kwargs.get('destination', ''),
                    query_text=query_text,
                    language=language,
                    result=bot_response
                )
            elif interaction_type == "ex_gratia":
                self.sheets_service.log_ex_gratia_application(
                    user_id=user_id,
                    user_name=user_name,
                    application_data=kwargs.get('application_data', {}),
                    language=language,
                    status=kwargs.get('status', 'Submitted')
                )
            elif interaction_type == "certificate":
                self.sheets_service.log_certificate_query(
                    user_id=user_id,
                    user_name=user_name,
                    query_text=query_text,
                    certificate_type=kwargs.get('certificate_type', 'General'),
                    language=language,
                    result=bot_response
                )
            else:
                # Log general interaction
                self.sheets_service.log_general_interaction(
                    user_id=user_id,
                    user_name=user_name,
                    interaction_type=interaction_type,
                    query_text=query_text,
                    language=language,
                    bot_response=bot_response
                )
        except Exception as e:
            logger.error(f"❌ Error logging to Google Sheets: {str(e)}")

    async def detect_language(self, text: str) -> str:
        """
        Detect language using Qwen LLM exclusively.
        """
        if not text or not text.strip():
            return 'english'
            
        try:
            await self._ensure_session()
            
            # Craft a prompt that leverages Qwen's multilingual capabilities
            prompt = f"""Analyze this text and determine if it's English, Hindi, or Nepali.
            
            Text to analyze: "{text}"
            
            CRITICAL DETECTION RULES:
            
            HINDI INDICATORS (Romanized):
            - Key words: mereko, mujhe, main, aap, tum, karna, chahiye, hai, hain
            - Grammar: verb + hain/hai (karna hain, chahiye hai)
            - Pronouns: mereko, mujhe, main, aap, tum
            - Question words: kya, kaise, kahan, kab, kyun, kaun
            
            NEPALI INDICATORS (Romanized):
            - Key words: malai, ma, tapai, timi, garna, chahincha, chha, hun
            - Grammar: verb + chha/chhan (garna chha, chahincha)
            - Pronouns: malai, ma, tapai, timi
            - Question words: ke, kasari, kahaan, kahile, kina, ko
            
            ENGLISH INDICATORS:
            - Pure English vocabulary and grammar
            - No Hindi/Nepali words mixed in
            
            DECISION RULES:
            1. If text contains "mereko", "mujhe", "karna hain", "chahiye" → HINDI
            2. If text contains "malai", "garna chha", "chahincha" → NEPALI
            3. If text is pure English → ENGLISH
            4. For mixed text, identify the dominant language based on grammar patterns
            
            Examples:
            - "Mereko ex gratia apply karna hain" → HINDI (mereko + karna hain)
            - "Malai certificate apply garna chha" → NEPALI (malai + garna chha)
            - "I want to apply for ex gratia" → ENGLISH (pure English)
            
            Respond with EXACTLY one word: english, hindi, or nepali"""
            
            logger.info(f"🔍 [LLM] Language Detection Prompt: {prompt}")
            
            # Call Qwen through Ollama
            async with self._session.post(
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
                result = await response.json()
                detected_lang = result['response'].strip().lower()
                
                logger.info(f"🤖 [LLM] Language Detection Response: {detected_lang}")
                
                # Validate response
                if detected_lang in ['english', 'hindi', 'nepali']:
                    logger.info(f"✅ Language detected by Qwen: {detected_lang}")
                    return detected_lang
                else:
                    logger.warning(f"⚠️ Invalid language detection result: {detected_lang}, falling back to English")
                    return 'english'
                    
        except Exception as e:
            logger.error(f"❌ Language detection failed: {str(e)}")
            return 'english'  # Fallback to English on error

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        try:
            user_id = update.effective_user.id
            
            # Debug all message attributes
            logger.info(f"📍 [DEBUG] Message type: {type(update.message)}")
            logger.info(f"📍 [DEBUG] Message attributes: {dir(update.message)}")
            logger.info(f"📍 [DEBUG] Has location: {hasattr(update.message, 'location')}")
            logger.info(f"📍 [DEBUG] Has text: {hasattr(update.message, 'text')}")
            logger.info(f"📍 [DEBUG] Location value: {getattr(update.message, 'location', 'None')}")
            
            # Check if message contains location FIRST
            if update.message.location:
                logger.info(f"📍 [MESSAGE] Location message detected from user {user_id}")
                logger.info(f"📍 [MESSAGE] Location object: {update.message.location}")
                logger.info(f"📍 [MESSAGE] Location type: {type(update.message.location)}")
                logger.info(f"📍 [MESSAGE] Location attributes: {dir(update.message.location)}")
                
                # Check if coordinates exist
                if hasattr(update.message.location, 'latitude') and hasattr(update.message.location, 'longitude'):
                    latitude = update.message.location.latitude
                    longitude = update.message.location.longitude
                    logger.info(f"📍 [MESSAGE] Latitude: {latitude}")
                    logger.info(f"📍 [MESSAGE] Longitude: {longitude}")
                    
                    if latitude is not None and longitude is not None:
                        logger.info(f"📍 [SUCCESS] Valid coordinates received: {latitude}, {longitude}")
                        await self.handle_location_received(update, context)
                        return
                    else:
                        logger.warning(f"📍 [ERROR] Coordinates are None: lat={latitude}, lon={longitude}")
                else:
                    logger.warning(f"📍 [ERROR] Location object missing latitude/longitude attributes")
                
                # Send error message to user
                user_lang = self._get_user_language(user_id)
                if user_lang == "hindi":
                    message = """📍 **स्थान साझा करने में समस्या हुई**

कृपया निम्नलिखित जांच करें:
• 📱 GPS चालू है
• 🔐 Telegram को स्थान की अनुमति दी गई है
• 📶 इंटरनेट कनेक्शन स्थिर है

या "📝 Type Location Manually" बटन का उपयोग करें।"""
                elif user_lang == "nepali":
                    message = """📍 **स्थान साझा गर्नमा समस्या भयो**

कृपया निम्नलिखित जांच गर्नुहोस्:
• 📱 GPS सक्रिय छ
• 🔐 Telegram लाई स्थानको अनुमति दिइएको छ
• 📶 इन्टरनेट कनेक्सन स्थिर छ

या "📝 Type Location Manually" बटन प्रयोग गर्नुहोस्।"""
                else:
                    message = """📍 **Location sharing failed**

Please check:
• 📱 GPS is enabled
• 🔐 Telegram has location permission
• 📶 Internet connection is stable

Or use the "📝 Type Location Manually" button."""
                
                await update.message.reply_text(message, parse_mode='Markdown')
                return
            
            # Only process text messages if no location
            if not update.message.text:
                logger.info(f"📍 [MESSAGE] Non-text message received from user {user_id}")
                return
            
            message_text = update.message.text
            
            logger.info(f"[MSG] User {user_id}: {message_text}")
            
            # Handle direct commands
            if message_text.startswith('/'):
                command = message_text.lower().strip()
                if command in ['/emergency', '/complaint']:
                    if command == '/emergency':
                        await self.start_emergency_workflow(update, context)
                    elif command == '/complaint':
                        await self.start_complaint_workflow(update, context)
                    return
            
            # Get current user state
            user_state = self._get_user_state(user_id)
            
            # Handle location request buttons and natural language cancel
            cancel_keywords = [
                "❌ Cancel", "cancel", "band karo", "रद्द करें", "रद्द", "बंद करो", 
                "stop", "quit", "exit", "back", "home", "main menu", "मुख्य मेनू",
                "घर जाओ", "वापस जाओ", "बंद", "छोड़ो", "छोड़ दो"
            ]
            
            if message_text.lower().strip() in [kw.lower() for kw in cancel_keywords]:
                self._clear_user_state(user_id)
                await self.show_main_menu(update, context)
                return
            elif message_text == "📝 Type Location Name":
                # Set state for manual location name input
                state = self._get_user_state(user_id)
                state["workflow"] = "manual_location_name"
                state["step"] = "location_name"
                self._set_user_state(user_id, state)
                
                user_lang = self._get_user_language(user_id)
                if user_lang == "hindi":
                    message = "📍 कृपया अपने स्थान का नाम दर्ज करें:\n\nउदाहरण: गंगटोक, लाचेन, नामची, या आपका गाँव/शहर"
                elif user_lang == "nepali":
                    message = "📍 कृपया आफ्नो स्थानको नाम दर्ता गर्नुहोस्:\n\nउदाहरण: गंगटोक, लाचेन, नामची, वा तपाईंको गाउँ/शहर"
                else:
                    message = "📍 Please enter your location name:\n\nExample: Gangtok, Lachen, Namchi, or your village/city"
                
                await update.message.reply_text(message, parse_mode='Markdown')
                return
            elif message_text == "⏭️ Skip Location":
                # Skip location and complete the workflow
                state = self._get_user_state(user_id)
                service_type = state.get("service_type", "emergency")
                
                if service_type == "emergency":
                    if state.get("workflow") == "emergency_report":
                        await self.handle_emergency_report_with_location(update, context, {"location_name": "Not provided"})
                    else:
                        await self.handle_emergency_with_location(update, context, {"location_name": "Not provided"})
                elif service_type == "complaint":
                    await self.handle_complaint_with_location(update, context, {"location_name": "Not provided"})
                elif service_type == "ex_gratia":
                    # For ex-gratia, we need to restore the original application data
                    data = state.get("data", {})
                    
                    logger.info(f"🔒 [SKIP] Current state data keys: {list(data.keys()) if data else 'No data'}")
                    
                    if not data or len(data) < 5:  # Should have at least name, father_name, village, contact, etc.
                        # No data found, show error and go back to main menu
                        user_lang = self._get_user_language(user_id)
                        if user_lang == "hindi":
                            error_msg = "❌ आवेदन डेटा नहीं मिला। कृपया फिर से आवेदन शुरू करें।"
                        elif user_lang == "nepali":
                            error_msg = "❌ आवेदन डाटा फेला परेन। कृपया फेरि आवेदन सुरु गर्नुहोस्।"
                        else:
                            error_msg = "❌ Application data not found. Please start the application again."
                        
                        self._clear_user_state(user_id)
                        await update.message.reply_text(error_msg, parse_mode='Markdown')
                        await self.show_main_menu(update, context)
                        return
                    
                    # Add location data to application data
                    data["latitude"] = None
                    data["longitude"] = None
                    data["location_timestamp"] = None
                    data["location_name"] = "Not provided"
                    
                    logger.info(f"🔒 [SKIP] Final application data: {list(data.keys())}")
                    
                    # Update state with location data
                    state["data"] = data
                    self._set_user_state(user_id, state)
                    
                    # Show confirmation with all collected data
                    await self.show_ex_gratia_confirmation(update, context, data)
                else:
                    # Default case - just clear state and show main menu
                    self._clear_user_state(user_id)
                    await self.show_main_menu(update, context)
                
                return
            
            # Get user language - only detect language for new conversations, not during workflows
            user_lang = self._get_user_language(user_id)
            
            # Check for language change requests first
            language_change_keywords = {
                'english': ['english', 'अंग्रेजी', 'english language', 'change to english', 'switch to english'],
                'hindi': ['hindi', 'हिंदी', 'hindi language', 'change to hindi', 'switch to hindi', 'हिंदी में बात करें'],
                'nepali': ['nepali', 'नेपाली', 'nepali language', 'change to nepali', 'switch to nepali']
            }
            
            message_lower = message_text.lower().strip()
            language_changed = False
            
            for lang, keywords in language_change_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    self._set_user_language(user_id, lang)
                    user_lang = lang
                    language_changed = True
                    logger.info(f"[LANG] User {user_id} changed language to: {lang}")
                    
                    # Send confirmation message
                    confirmation_text = self.responses[lang]['language_changed']
                    await update.message.reply_text(confirmation_text, parse_mode='Markdown')
                    
                    # Wait a moment then show main menu
                    await asyncio.sleep(1.5)
                    await self.show_main_menu(update, context)
                    
                    # Log language change
                    user_name = update.effective_user.first_name or "Unknown"
                    self._log_to_sheets(
                        user_id=user_id,
                        user_name=user_name,
                        interaction_type="language_change",
                        query_text=message_text,
                        language=lang,
                        bot_response=confirmation_text
                    )
                    return
            
            # If user is in a workflow, don't change their language
            if not user_state.get("workflow"):
                # Only detect language for new conversations
                detected_lang = await self.detect_language(message_text)
                self._set_user_language(user_id, detected_lang)
                user_lang = detected_lang
                logger.info(f"[LANG] User {user_id} language detected: {detected_lang}")
            else:
                logger.info(f"[LANG] User {user_id} using existing language: {user_lang}")
            
            # If user is in a workflow, handle accordingly
            if user_state.get("workflow"):
                workflow = user_state.get("workflow")
                
                # Check for cancel intent using LLM even in workflows
                cancel_intent = await self.get_intent_from_llm(message_text, user_lang)
                if cancel_intent in ['cancel', 'back', 'home', 'main_menu']:
                    self._clear_user_state(user_id)
                    await self.show_main_menu(update, context)
                    return
                
                if workflow == "location_request":
                    # User is waiting to share location, remind them
                    user_lang = self._get_user_language(user_id)
                    if user_lang == "hindi":
                        message = "📍 कृपया अपना स्थान साझा करने के लिए ऊपर दिए गए बटन का उपयोग करें।"
                    elif user_lang == "nepali":
                        message = "📍 कृपया आफ्नो स्थान साझा गर्नको लागि माथिको बटन प्रयोग गर्नुहोस्।"
                    else:
                        message = "📍 Please use the button above to share your location."
                    await update.message.reply_text(message, parse_mode='Markdown')
                    return
                elif workflow == "ex_gratia":
                    await self.handle_ex_gratia_workflow(update, context, message_text)
                elif workflow == "complaint":
                    await self.handle_complaint_workflow(update, context)
                elif workflow == "emergency_report":
                    await self.handle_emergency_workflow(update, context)
                elif workflow == "manual_location":
                    await self.handle_manual_location_workflow(update, context)
                elif workflow == "manual_location_name":
                    await self.handle_manual_location_name_workflow(update, context)
                elif workflow == "certificate":
                    await self.handle_certificate_workflow(update, context, message_text)
                elif workflow == "status_check":
                    await self.process_status_check(update, context)
                elif workflow == "feedback":
                    await self.handle_feedback_workflow(update, context)
                elif workflow == "csc_search":
                    await self.handle_csc_search_workflow(update, context)
                elif workflow == "blo_search":
                    await self.handle_blo_search_workflow(update, context)
                elif workflow == "check_status_":
                    reference_number = workflow.replace("check_status_", "")
                    await self.check_nc_exgratia_status(update, context, reference_number)
                elif workflow == "emergency":
                    await self.handle_emergency_menu(update, context)
                else:
                    # Unknown workflow, clear state and show main menu
                    self._clear_user_state(user_id)
                    await self.show_main_menu(update, context)
            else:
                # New conversation - detect intent and route
                logger.info(f"[INTENT] Processing new message: {message_text}")
                
                # Get intent using LLM
                intent = await self.get_intent_from_llm(message_text, user_lang)
                logger.info(f"[INTENT] Detected intent: {intent}")
                
                # Route based on intent
                if intent == "greeting":
                    await self.handle_greeting(update, context)
                elif intent == "ex_gratia":
                    await self.handle_ex_gratia(update, context)
                elif intent == "check_status":
                    await self.handle_check_status(update, context)
                elif intent == "relief_norms":
                    await self.handle_relief_norms(update, context)
                elif intent == "emergency":
                    # Direct emergency response - don't show menu
                    await self.handle_emergency_direct(update, context, message_text)
                elif intent == "tourism":
                    await self.handle_tourism_menu(update, context)
                elif intent == "complaint":
                    await self.start_complaint_workflow(update, context)
                elif intent == "certificate":
                    await self.handle_certificate_info(update, context)
                elif intent == "csc":
                    await self.handle_csc_menu(update, context)
                elif intent == "cancel":
                    # Clear state and show main menu
                    self._clear_user_state(user_id)
                    await self.show_main_menu(update, context)
                else:
                    # Unknown intent, show main menu
                    await self.start(update, context)
                
                # Log general interaction to Google Sheets
                user_name = update.effective_user.first_name or "Unknown"
                self._log_to_sheets(
                    user_id=user_id,
                    user_name=user_name,
                    interaction_type="general",
                    query_text=message_text,
                    language=user_lang,
                    bot_response=f"Intent detected: {intent}"
                )
            
        except Exception as e:
            logger.error(f"❌ Error in message handler: {str(e)}")
            user_lang = self._get_user_language(update.effective_user.id) if update.effective_user else 'english'
            await update.message.reply_text(
                self.responses[user_lang]['error']
            )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        user_lang = self._get_user_language(user_id)
        logger.info(f"[USER] New conversation started by user {user_id}")
        self._clear_user_state(user_id)
        
        # Get the main menu text in user's selected language
        welcome_text = self.responses[user_lang]['main_menu']

        keyboard = [
            [InlineKeyboardButton(self.responses[user_lang]['button_homestay'], callback_data='tourism')],
            [InlineKeyboardButton(self.responses[user_lang]['button_emergency'], callback_data='emergency')],
            [InlineKeyboardButton(self.responses[user_lang]['button_complaint'], callback_data='complaint')],
            [InlineKeyboardButton(self.responses[user_lang]['button_certificate'], callback_data='certificate')],
            [InlineKeyboardButton(self.responses[user_lang]['button_disaster'], callback_data='disaster')],
            [InlineKeyboardButton(self.responses[user_lang]['button_schemes'], callback_data='schemes')],
            [InlineKeyboardButton(self.responses[user_lang]['button_contacts'], callback_data='contacts')],
            [InlineKeyboardButton(self.responses[user_lang]['button_feedback'], callback_data='feedback')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both regular messages and callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /language command to change language"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "User"
        
        # Get current language
        current_lang = self._get_user_language(user_id)
        
        # Create language selection menu
        keyboard = [
            [InlineKeyboardButton(self.responses['english']['language_button_english'], callback_data="lang_english")],
            [InlineKeyboardButton(self.responses['english']['language_button_hindi'], callback_data="lang_hindi")],
            [InlineKeyboardButton("🇳🇵 नेपाली (Nepali)", callback_data="lang_nepali")],
            [InlineKeyboardButton(self.responses['english']['back_main_menu'], callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Show language menu in current language
        text = self.responses[current_lang]['language_menu']
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Log interaction
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="language_change",
            query_text="/language",
            language=current_lang,
            bot_response=text
        )

    async def detect_language_with_scoring(self, text: str) -> str:
        """Deprecated: Use detect_language instead."""
        return await self.detect_language(text)

    async def get_intent_from_llm(self, text: str, lang: str) -> str:
        """Get intent using Qwen LLM."""
        try:
            await self._ensure_session()
            
            prompt = f"""You are an intent classifier for SmartGov Assistant, a government services chatbot in Sikkim. Given the user's message, classify it into one of these intents:

Available intents:
- greeting: User is saying hello, hi, namaste, or starting a conversation (hello, hi, namaste, good morning, etc.)
- ex_gratia: User wants to APPLY for ex-gratia assistance (action-oriented)
- check_status: User wants to check status of their application
- relief_norms: User asks about relief norms, policies, eligibility criteria, or general questions about ex-gratia
- emergency: User needs emergency help (ambulance, police, fire)
- tourism: User wants tourism/homestay services
- complaint: User wants to file a complaint
- certificate: User wants to apply for certificates
- csc: User wants CSC (Common Service Center) services
- cancel: User wants to cancel, stop, go back, or return to main menu (cancel, stop, quit, exit, back, home, band karo, रद्द करें, बंद करो)
- unknown: If none of the above match

Example messages for each intent:
- greeting: "Hello", "Hi", "Namaste", "Good morning", "Namaskar", "Kya haal hai", "K cha", "How are you"
- ex_gratia: "I want to apply for compensation", "Apply for ex gratia", "I need to file ex-gratia claim", "Start ex-gratia application"
- relief_norms: "What is ex gratia?", "How much compensation will I get?", "What are the eligibility criteria?", "Kya mujhe ex gratia milega?", "Ex gratia kya hain?"
- check_status: "What's the status of my application?", "Track my ex-gratia request", "Any update on my claim?"
- emergency: "Need ambulance", "Call police", "Fire emergency"
- tourism: "Book homestay", "Tourist places", "Accommodation"
- complaint: "File complaint", "Register grievance", "Report issue"
- certificate: "Apply for certificate", "Birth certificate", "Document"
- csc: "Find CSC", "CSC operator", "Common Service Center"

User message: {text}
Language: {lang}

Respond with ONLY one of the intent names listed above, nothing else."""

            logger.info(f"🎯 [LLM] Intent Classification Prompt: {prompt}")

            async with self._session.post(
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
                result = await response.json()
                intent = result['response'].strip().lower()
                logger.info(f"🎯 [LLM] Intent Classification Response: {intent}")
                
                # Validate intent
                valid_intents = ['greeting', 'ex_gratia', 'check_status', 'relief_norms', 'emergency', 'tourism', 'complaint', 'certificate', 'csc', 'cancel']
                return intent if intent in valid_intents else 'unknown'
                
        except Exception as e:
            logger.error(f"[LLM] Intent classification error: {str(e)}")
            return 'unknown'
        
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the main menu"""
        await self.start(update, context)

    async def handle_greeting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle greeting messages with language selection"""
        user_id = update.effective_user.id
        
        # Clear any existing state
        self._clear_user_state(user_id)
        
        greeting_text = """👋 *Welcome to SmartGov Assistant!*

नमस्ते! / नमस्कार! / Hello!

Please select your preferred language to continue:

कृपया अपनी पसंदीदा भाषा चुनें:

कृपया तपाईंको मनपर्ने भाषा छान्नुहोस्:"""

        keyboard = [
            [InlineKeyboardButton("🇮🇳 हिंदी (Hindi)", callback_data='lang_hindi')],
            [InlineKeyboardButton("🇳🇵 नेपाली (Nepali)", callback_data='lang_nepali')],
            [InlineKeyboardButton("🇬🇧 English", callback_data='lang_english')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(greeting_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        user_id = update.effective_user.id
        data = query.data
        logger.info(f"[CALLBACK] Received from {user_id}: {data}")

        try:
            # Always answer the callback query first
            await query.answer()

            if data == "main_menu":
                self._clear_user_state(user_id)
                await self.start(update, context)
            
            elif data == "tourism":
                await self.handle_tourism_menu(update, context)
            
            elif data.startswith("place_"):
                await self.handle_place_selection(update, context)
            
            elif data == "disaster":
                await self.handle_disaster_menu(update, context)
            
            elif data == "relief_norms":
                await self.handle_relief_norms(update, context)
            
            elif data == "check_status":
                await self.handle_check_status(update, context)
            
            elif data == "ex_gratia":
                await self.handle_ex_gratia(update, context)
            
            elif data == "ex_gratia_start":
                await self.start_ex_gratia_workflow(update, context)
            
            elif data == "ex_gratia_submit":
                await self.submit_ex_gratia_application(update, context)
            
            elif data == "ex_gratia_edit":
                await self.handle_ex_gratia_edit(update, context)
            
            elif data == "ex_gratia_cancel":
                await self.cancel_ex_gratia_application(update, context)
            
            elif data.startswith("damage_type_"):
                damage_type = data.replace("damage_type_", "")
                await self.handle_damage_type_selection(update, context, damage_type)
            
            elif data.startswith("district_"):
                district = data.replace("district_", "")
                district_mapping = {
                    "east": "East Sikkim",
                    "west": "West Sikkim", 
                    "north": "North Sikkim",
                    "south": "South Sikkim"
                }
                district_name = district_mapping.get(district, district)
                
                # Update user state with district
                user_state = self._get_user_state(user_id)
                if user_state.get("workflow") == "ex_gratia":
                    user_state["data"]["district"] = district_name
                    user_state["step"] = "khatiyan"
                    self._set_user_state(user_id, user_state)
                    
                    user_lang = self._get_user_language(user_id)
                    await query.edit_message_text(
                        self.responses[user_lang]['ex_gratia_khatiyan'],
                        parse_mode='Markdown'
                    )
            
            elif data == "emergency":
                await self.handle_emergency_menu(update, context)
            
            elif data.startswith("emergency_"):
                service = data.replace("emergency_", "")
                await self.handle_emergency_service(update, context, service)
            
            elif data == "csc":
                await self.handle_csc_menu(update, context)
            
            elif data.startswith("csc_"):
                district = data.replace("csc_", "")
                await self.handle_csc_selection(update, context, district)
            
            elif data == "certificate":
                await self.handle_certificate_info(update, context)
            
            elif data.startswith("cert_"):
                cert_type = data.replace("cert_", "")
                await self.handle_certificate_choice(update, context, cert_type)
            
            elif data == "complaint":
                await self.start_complaint_workflow(update, context)
            
            elif data.startswith("complaint_"):
                complaint_type = data.replace("complaint_", "")
                # Handle different complaint types
                if complaint_type in ["police", "govt", "emergency"]:
                    # Continue with complaint workflow
                    user_state = self._get_user_state(user_id)
                    if user_state.get("workflow") == "complaint":
                        user_state["complaint_type"] = complaint_type
                        user_state["step"] = "name"
                        self._set_user_state(user_id, user_state)
                        
                        user_lang = self._get_user_language(user_id)
                        text = f"{self.responses[user_lang]['complaint_title']}\n\n{self.responses[user_lang]['complaint_name_prompt']}"
                        
                        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            elif data == "certificate_csc":
                # Handle certificate CSC choice
                user_id = update.effective_user.id
                user_lang = self._get_user_language(user_id)
                self._set_user_state(user_id, {"workflow": "certificate", "stage": "gpu"})
                gpu_prompt = self.responses[user_lang]['certificate_gpu_prompt']
                await query.edit_message_text(gpu_prompt, parse_mode='Markdown')
            
            elif data == "certificate_sso":
                # Handle certificate SSO choice
                user_id = update.effective_user.id
                user_lang = self._get_user_language(user_id)
                sso_message = self.responses[user_lang]['certificate_sso_message']
                back_button = self.responses[user_lang]['back_main_menu']
                await query.edit_message_text(
                    f"{sso_message}\n\n🔙 {back_button}", 
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_button, callback_data="main_menu")]]),
                    parse_mode='Markdown'
                )
            
            elif data == "complaint":
                await self.start_complaint_workflow(update, context)
            
            elif data.startswith("lang_"):
                lang_choice = data.replace("lang_", "")
                self._set_user_language(user_id, lang_choice)
                
                # Show language change confirmation message
                confirmation_text = self.responses[lang_choice]['language_changed']
                await query.edit_message_text(confirmation_text, parse_mode='Markdown')
                
                # Wait a moment then show main menu
                await asyncio.sleep(1.5)
                await self.start(update, context)
            
            # New features callbacks
            elif data == "schemes":
                await self.handle_scheme_menu(update, context)
            
            elif data.startswith("scheme_"):
                scheme_id = data.replace("scheme_", "")
                await self.handle_scheme_selection(update, context, scheme_id)
            
            elif data == "contacts":
                await self.handle_contacts_menu(update, context)
            
            elif data == "contacts_csc":
                await self.handle_csc_search(update, context)
            
            elif data == "contacts_blo":
                await self.handle_blo_search(update, context)
            
            elif data == "contacts_aadhar":
                await self.handle_aadhar_services(update, context)
            
            elif data == "feedback":
                await self.start_feedback_workflow(update, context)
            
            elif data.startswith("check_status_"):
                reference_number = data.replace("check_status_", "")
                await self.check_nc_exgratia_status(update, context, reference_number)
            
            else:
                logger.warning(f"Unhandled callback data: {data}")
                await query.message.reply_text("Sorry, I couldn't process that request.")

        except Exception as e:
            logger.error(f"Error in callback handler: {str(e)}")
            await query.message.reply_text("Sorry, an error occurred. Please try again.")

    # --- Disaster Management ---
    async def handle_disaster_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle disaster management menu"""
        keyboard = [
            [InlineKeyboardButton("📝 Apply for Ex-gratia", callback_data="ex_gratia")],
            [InlineKeyboardButton("🔍 Check Application Status", callback_data="check_status")],
            [InlineKeyboardButton("ℹ️ View Relief Norms", callback_data="relief_norms")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Disaster Management Services* 🆘

Please select an option:

1. Apply for Ex-gratia assistance
2. Check your application status
3. View disaster relief norms"""

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_relief_norms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_lang = self._get_user_language(update.effective_user.id)
        text = self.responses[user_lang]['ex_gratia_intro']
        # Use reply_text if not a callback query
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, parse_mode='Markdown')

    async def handle_check_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle application status check"""
        user_id = update.effective_user.id
        self._set_user_state(user_id, {"workflow": "check_status"})
        
        text = """*Check Application Status* 🔍

Please enter your Application ID:
(Format: EX2025XXXXXXX)"""

        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="disaster")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def process_status_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process application status check"""
        application_id = update.message.text.strip().upper()
        
        try:
            # Read status from CSV
            df = pd.read_csv('data/exgratia_applications.csv')
            application = df[df['ApplicationID'] == application_id].iloc[0]
            
            status_text = f"""*Application Status* 📋

Application ID: {application_id}
Name: {application['ApplicantName']}
Village: {application['Village']}
Status: Processing
Submission Date: {application['SubmissionTimestamp']}

Your application is being reviewed by the district administration."""
        except:
            status_text = """❌ *Application Not Found*

Please check the Application ID and try again.
If the problem persists, contact support."""

        keyboard = [[InlineKeyboardButton("🔙 Back to Disaster Menu", callback_data="disaster")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Clear the workflow state
        self._clear_user_state(update.effective_user.id)

    async def handle_ex_gratia(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle ex-gratia application"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        text = f"*Ex-Gratia Assistance* 📝\n\n{self.responses[user_lang]['ex_gratia_intro']}"

        keyboard = [
            [InlineKeyboardButton("✅ Yes, Continue", callback_data="ex_gratia_start")],
            [InlineKeyboardButton("❌ No, Go Back", callback_data="disaster")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both regular messages and callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # --- Ex-Gratia Application ---
    async def start_ex_gratia_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the ex-gratia application workflow"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        self._set_user_state(user_id, {"workflow": "ex_gratia", "step": "name"})
        
        text = f"*Ex-Gratia Application Form* 📝\n\n{self.responses[user_lang]['ex_gratia_form']}"
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="disaster")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both regular messages and callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_ex_gratia_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle the ex-gratia application workflow"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        step = state.get("step")
        data = state.get("data", {})

        # Check for cancel commands first
        cancel_commands = ['cancel', 'exit', 'quit', 'stop', 'back', 'menu', 'home', 'रद्द', 'बंद', 'वापस', 'मेनू']
        if any(cmd in text.lower() for cmd in cancel_commands):
            self._clear_user_state(user_id)
            await update.message.reply_text(self.responses[user_lang]['cancelled'], parse_mode='Markdown')
            await self.show_main_menu(update, context)
            return

        # Check if user is asking a question instead of providing data
        question_indicators = ['kya', 'what', 'how', 'when', 'where', 'why', 'क्या', 'कैसे', 'कब', 'कहाँ', 'क्यों']
        if any(indicator in text.lower() for indicator in question_indicators):
            # User is asking a question, redirect to relief norms
            self._clear_user_state(user_id)
            await self.handle_relief_norms(update, context)
            return

        if step == "name":
            data["name"] = text
            state["step"] = "father_name"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_father'], parse_mode='Markdown')

        elif step == "father_name":
            data["father_name"] = text
            state["step"] = "village"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_village'], parse_mode='Markdown')

        elif step == "village":
            data["village"] = text
            state["step"] = "contact"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_contact'], parse_mode='Markdown')

        elif step == "contact":
            if not text.isdigit() or len(text) != 10:
                await update.message.reply_text("Please enter a valid 10-digit mobile number.", parse_mode='Markdown')
                return
            
            data["contact"] = text
            state["step"] = "voter_id"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text("🆔 Please enter your Voter ID number:", parse_mode='Markdown')

        elif step == "voter_id":
            data["voter_id"] = text
            state["step"] = "ward"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_ward'], parse_mode='Markdown')

        elif step == "ward":
            data["ward"] = text
            state["step"] = "gpu"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_gpu'], parse_mode='Markdown')

        elif step == "gpu":
            data["gpu"] = text
            state["step"] = "district"
            state["data"] = data
            self._set_user_state(user_id, state)
            
            # Show district options
            keyboard = [
                [InlineKeyboardButton("East Sikkim", callback_data="district_east")],
                [InlineKeyboardButton("West Sikkim", callback_data="district_west")],
                [InlineKeyboardButton("North Sikkim", callback_data="district_north")],
                [InlineKeyboardButton("South Sikkim", callback_data="district_south")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("🏛️ Please select your district:", reply_markup=reply_markup, parse_mode='Markdown')

        elif step == "district":
            data["district"] = text
            state["step"] = "khatiyan"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_khatiyan'], parse_mode='Markdown')

        elif step == "khatiyan":
            data["khatiyan_no"] = text
            state["step"] = "plot"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_plot'], parse_mode='Markdown')

        elif step == "plot":
            data["plot_no"] = text
            state["step"] = "nc_datetime"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text("📅 When did the natural calamity occur? (DD/MM/YYYY HH:MM)\n\nExample: 15/10/2023 14:30", parse_mode='Markdown')

        elif step == "nc_datetime":
            # Parse the datetime input
            try:
                # Try to parse the datetime
                datetime_str = text.strip()
                if '/' in datetime_str:
                    # Format: DD/MM/YYYY HH:MM
                    dt = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M")
                elif '-' in datetime_str:
                    # Format: YYYY-MM-DD HH:MM
                    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                else:
                    # Try other common formats
                    dt = datetime.strptime(datetime_str, "%d-%m-%Y %H:%M")
                
                data["nc_datetime"] = dt.isoformat()
                state["step"] = "damage_type"
                state["data"] = data
                self._set_user_state(user_id, state)
                await self.show_damage_type_options(update, context)
                
            except ValueError:
                await update.message.reply_text("❌ Please enter the date and time in the correct format.\n\nExample: 15/10/2023 14:30", parse_mode='Markdown')
                return

        elif step == "damage_type":
            data["damage_type"] = text
            state["step"] = "damage_description"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['ex_gratia_damage'], parse_mode='Markdown')

        elif step == "damage_description":
            data["damage_description"] = text
            state["step"] = "location"
            state["data"] = data
            self._set_user_state(user_id, state)
            
            # Request location
            await self.request_location(update, context, "ex_gratia")

        else:
            await update.message.reply_text(self.responses[user_lang]['error'], parse_mode='Markdown')
            self._clear_user_state(user_id)

    async def show_damage_type_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🏠 House Damage (₹4,000 - ₹25,000)", callback_data='damage_type_house')],
            [InlineKeyboardButton("🌾 Crop Loss (₹4,000 - ₹15,000)", callback_data='damage_type_crop')],
            [InlineKeyboardButton("🐄 Livestock Loss (₹2,000 - ₹15,000)", callback_data='damage_type_livestock')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both regular messages and callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text("Please select the type of damage:", reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text("Please select the type of damage:", reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_damage_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, damage_type: str):
        """Handle damage type selection in ex-gratia workflow"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        data = state.get("data", {})
        
        damage_types = {
            'house': '🏠 House Damage',
            'crop': '🌾 Crop Loss',
            'livestock': '🐄 Livestock Loss'
        }
        
        data['damage_type'] = damage_types[damage_type]
        state['step'] = 'damage_description'
        state['data'] = data
        self._set_user_state(user_id, state)
        
        text = f"""Selected: {damage_types[damage_type]}

Please provide detailed description of the damage:
(Include location, extent of damage, date of incident)"""

        await update.callback_query.edit_message_text(text, parse_mode='Markdown')

    async def show_ex_gratia_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
        """Show confirmation of collected data before submission"""
        
        # Format location display
        location_display = "Not provided"
        if data.get('latitude') and data.get('longitude'):
            location_display = f"{data['latitude']:.6f}, {data['longitude']:.6f}"
        
        # Format datetime display
        datetime_display = "Not provided"
        if data.get('nc_datetime'):
            try:
                dt = datetime.fromisoformat(data['nc_datetime'].replace('Z', '+00:00'))
                datetime_display = dt.strftime("%d/%m/%Y %H:%M")
            except:
                datetime_display = data.get('nc_datetime', 'Not provided')
        
        summary = f"""*Please Review Your NC Exgratia Application* 📋

*Personal Details:*
👤 **Name**: {data.get('name', 'N/A')}
👨‍👦 **Father's Name**: {data.get('father_name', 'N/A')}
🆔 **Voter ID**: {data.get('voter_id', 'N/A')}
📱 **Contact**: {data.get('contact', 'N/A')}

*Address Details:*
📍 **Village**: {data.get('village', 'N/A')}
🏘️ **Ward**: {data.get('ward', 'N/A')}
🏛️ **GPU**: {data.get('gpu', 'N/A')}
🏛️ **District**: {data.get('district', 'N/A')}

*Land Details:*
📄 **Khatiyan Number**: {data.get('khatiyan_no', 'N/A')}
🗺️ **Plot Number**: {data.get('plot_no', 'N/A')}

*Incident Details:*
📅 **Date & Time**: {datetime_display}
🏷️ **Damage Type**: {data.get('damage_type', 'N/A')}
📝 **Description**: {data.get('damage_description', 'N/A')}

*Location:*
📍 **Coordinates**: {location_display}

Please verify all details carefully. Would you like to:"""
        
        keyboard = [
            [InlineKeyboardButton("✅ Submit to NC Exgratia API", callback_data='ex_gratia_submit')],
            [InlineKeyboardButton("✏️ Edit Details", callback_data='ex_gratia_edit')],
            [InlineKeyboardButton("❌ Cancel", callback_data='ex_gratia_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Handle both regular messages and callbacks
        if update.callback_query:
            await update.callback_query.edit_message_text(summary, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')

    async def submit_ex_gratia_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Submit the ex-gratia application to NC Exgratia API"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        data = state.get("data", {})

        try:
            # Check if API client is available
            if not self.api_client:
                error_msg = "❌ NC Exgratia API is not configured. Please contact support."
                if update.callback_query:
                    await update.callback_query.edit_message_text(error_msg, parse_mode='Markdown')
                else:
                    await update.message.reply_text(error_msg, parse_mode='Markdown')
                return

            # Show processing message
            processing_msg = "🔄 Submitting your application to NC Exgratia API...\n\nPlease wait while we process your request."
            if update.callback_query:
                await update.callback_query.edit_message_text(processing_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text(processing_msg, parse_mode='Markdown')

            # Submit to NC Exgratia API
            api_result = await self.api_client.submit_application(data)
            
            if api_result.get("success"):
                # API submission successful
                reference_number = api_result.get("reference_number", "Unknown")
                api_status = api_result.get("status", "SUBMITTED")
                
                # Generate local application ID for backup
                now = datetime.now()
                local_app_id = f"EXG{now.strftime('%Y%m%d')}{random.randint(1000,9999)}"
                
                # Save to local CSV as backup
                df = pd.DataFrame([{
                    'ApplicationID': local_app_id,
                    'NCReferenceNumber': reference_number,
                    'ApplicantName': data.get('name'),
                    'FatherName': data.get('father_name'),
                    'VoterID': data.get('voter_id'),
                    'Village': data.get('village'),
                    'Contact': data.get('contact'),
                    'Ward': data.get('ward'),
                    'GPU': data.get('gpu'),
                    'District': data.get('district'),
                    'KhatiyanNo': data.get('khatiyan_no'),
                    'PlotNo': data.get('plot_no'),
                    'DamageDescription': data.get('damage_description'),
                    'SubmissionTimestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'Status': 'Pending'
                }])
                
                df.to_csv('data/exgratia_applications.csv', mode='a', header=False, index=False)
                
                # Success confirmation message
                confirmation = f"""✅ *NC Exgratia Application Submitted Successfully!*

🆔 **Reference Number**: `{reference_number}`
👤 **Applicant**: {data.get('name')}
📅 **Submitted**: {now.strftime('%d/%m/%Y %H:%M')}
📊 **Status**: {api_status}

*Important Information:*
• Save this reference number: `{reference_number}`
• Check status anytime: `/status {reference_number}`
• Contact support if needed: {Config.SUPPORT_PHONE}

*Next Steps:*
1. Your application will be reviewed by officials
2. You'll receive updates via SMS
3. Processing time: 7-10 working days

Thank you for using NC Exgratia service! 🏛️"""

                keyboard = [
                    [InlineKeyboardButton("🔍 Check Status", callback_data=f"check_status_{reference_number}")],
                    [InlineKeyboardButton("🔙 Back to Disaster Management", callback_data="disaster")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if update.callback_query:
                    await update.callback_query.edit_message_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await update.message.reply_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
                
                # Log to Google Sheets
                user_name = update.effective_user.first_name or "Unknown"
                application_data = {
                    'name': data.get('name'),
                    'phone': data.get('contact'),
                    'voter_id': data.get('voter_id'),
                    'address': f"{data.get('village')}, Ward: {data.get('ward')}, GPU: {data.get('gpu')}, District: {data.get('district')}",
                    'damage_type': data.get('damage_type', ''),
                    'damage_description': data.get('damage_description', ''),
                    'nc_datetime': data.get('nc_datetime', ''),
                    'reference_number': reference_number,
                    'api_status': api_status
                }
                self._log_to_sheets(
                    user_id=user_id,
                    user_name=user_name,
                    interaction_type="nc_exgratia_submission",
                    query_text=f"NC Exgratia application submitted",
                    language=user_lang,
                    bot_response=f"Reference: {reference_number}",
                    application_data=application_data,
                    status="Submitted to API"
                )
                
            else:
                # API submission failed
                error_details = api_result.get("details", "Unknown error")
                logger.error(f"❌ NC Exgratia API submission failed: {error_details}")
                
                error_msg = f"""❌ *Application Submission Failed*

The NC Exgratia API returned an error. Please try again later.

*Error Details:*
{error_details}

*What to do:*
1. Check your internet connection
2. Try again in a few minutes
3. Contact support if the problem persists: {Config.SUPPORT_PHONE}

Your data has been saved locally and will be retried."""
                
                keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data='ex_gratia_submit')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if update.callback_query:
                    await update.callback_query.edit_message_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await update.message.reply_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Clear user state
            self._clear_user_state(user_id)
            
        except Exception as e:
            logger.error(f"❌ Error submitting application: {str(e)}")
            error_msg = f"""❌ *Application Submission Error*

An unexpected error occurred. Please try again.

*Error:*
{str(e)}

Contact support: {Config.SUPPORT_PHONE}"""
            
            keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data='ex_gratia_submit')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await update.message.reply_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')

    async def cancel_ex_gratia_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self._clear_user_state(user_id)
        await update.callback_query.edit_message_text("Your application has been cancelled.")
        await self.show_main_menu(update, context)

    async def handle_ex_gratia_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle editing of ex-gratia application details"""
        keyboard = [
            [InlineKeyboardButton("👤 Name", callback_data="edit_name")],
            [InlineKeyboardButton("👨‍👦 Father's Name", callback_data="edit_father")],
            [InlineKeyboardButton("📍 Village", callback_data="edit_village")],
            [InlineKeyboardButton("📱 Contact", callback_data="edit_contact")],
            [InlineKeyboardButton("🏘️ Ward", callback_data="edit_ward")],
            [InlineKeyboardButton("🏛️ GPU", callback_data="edit_gpu")],
            [InlineKeyboardButton("📄 Khatiyan Number", callback_data="edit_khatiyan")],
            [InlineKeyboardButton("🗺️ Plot Number", callback_data="edit_plot")],
            [InlineKeyboardButton("📝 Damage Description", callback_data="edit_damage")],
            [InlineKeyboardButton("✅ Done Editing", callback_data="edit_done")],
            [InlineKeyboardButton("❌ Cancel", callback_data="ex_gratia_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Which information would you like to edit?* ✏️

Select the field you want to update:"""
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # --- Emergency Services ---
    async def handle_emergency_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle emergency services menu"""
        user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
        user_lang = self._get_user_language(user_id)
        
        # Request location first for emergency services
        if update.callback_query:
            await update.callback_query.answer()
            await self.request_location(update, context, "emergency")
        else:
            await self.request_location(update, context, "emergency")
        
        # Log to Google Sheets
        user_name = (update.effective_user.first_name if update.effective_user else update.callback_query.from_user.first_name) or "Unknown"
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="emergency",
            query_text="Emergency services menu accessed - location requested",
            language=user_lang,
            bot_response="Location request sent",
            emergency_type="menu"
        )

    async def handle_emergency_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
        """Handle emergency requests directly without showing menu"""
        try:
            user_id = update.effective_user.id
            user_lang = self._get_user_language(user_id)
            message_lower = message_text.lower()
            
            # Determine which emergency service is needed
            if any(word in message_lower for word in ['ambulance', 'ambulance', 'medical', 'doctor', 'hospital']):
                service_type = 'ambulance'
                response_text = self.responses[user_lang]['emergency_ambulance']
            elif any(word in message_lower for word in ['police', 'police', 'thief', 'robbery', 'crime']):
                service_type = 'police'
                response_text = self.responses[user_lang]['emergency_police']
            elif any(word in message_lower for word in ['fire', 'fire', 'burning', 'blaze']):
                service_type = 'fire'
                response_text = self.responses[user_lang]['emergency_fire']
            elif any(word in message_lower for word in ['suicide', 'suicide', 'helpline']):
                service_type = 'suicide'
                response_text = self.responses[user_lang]['emergency_suicide']
            elif any(word in message_lower for word in ['women', 'women', 'harassment']):
                service_type = 'women'
                response_text = self.responses[user_lang]['emergency_women']
            else:
                # Default to ambulance for general emergency
                service_type = 'ambulance'
                response_text = self.responses[user_lang]['emergency_ambulance']
            
            keyboard = [
                [InlineKeyboardButton(self.responses[user_lang]['other_emergency'], callback_data="emergency")],
                [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Log to Google Sheets
            user_name = update.effective_user.first_name or "Unknown"
            self._log_to_sheets(
                user_id=user_id,
                user_name=user_name,
                interaction_type="emergency",
                query_text=message_text,
                language=user_lang,
                bot_response=response_text,
                service_type=service_type
            )
        except Exception as e:
            logger.error(f"Error handling emergency direct: {str(e)}")
            user_lang = self._get_user_language(update.effective_user.id) if update.effective_user else 'english'
            await update.message.reply_text(self.responses[user_lang]['error'])

    async def handle_emergency_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service_type: str):
        """Handle specific emergency service selection"""
        query = update.callback_query
        
        # Default emergency numbers for all services
        response_text = {
                'police': "👮 *Police Emergency*\nDial: 100\nControl Room: 03592-202022",
                'fire': "🚒 *Fire Emergency*\nDial: 101\nControl Room: 03592-202099",
                'women': "👩 *Women Helpline*\nDial: 1091\nState Commission: 03592-205607",
                'health': "🏥 *Health Helpline*\nDial: 104\nToll Free: 1800-345-3049",
                'suicide': "💭 *Suicide Prevention Helpline*\nDial: 9152987821"
            }.get(service_type, "Please call 112 for any emergency assistance.")
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Emergency Services", callback_data="emergency")],
            [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Log to Google Sheets
        user_id = query.from_user.id
        user_name = query.from_user.first_name or "Unknown"
        user_lang = self._get_user_language(user_id)
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="emergency",
            query_text=f"Emergency service request: {service_type}",
            language=user_lang,
            bot_response=response_text,
            emergency_type=service_type
        )

    # --- Tourism & Homestays ---
    async def handle_tourism_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle homestay booking menu"""
        places = self.home_stay_df['Place'].unique()
        keyboard = []
        for place in places:
            keyboard.append([InlineKeyboardButton(f"🏡 {place}", callback_data=f"place_{place}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Book a Homestay* 🏡

Please select your destination:"""
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_place_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle specific place selection for homestays"""
        query = update.callback_query
        place = query.data.replace('place_', '')
        
        place_homestays = self.home_stay_df[self.home_stay_df['Place'] == place]
        
        text = f"*Available Homestays in {place}* 🏡\n\n"
        for _, row in place_homestays.iterrows():
            text += f"*{row['HomestayName']}*\n"
            text += f"📍 Address: {row['Address']}\n"
            text += f"💰 Price: {row['PricePerNight']}\n"
            text += f"📞 Contact: {row['ContactNumber']}\n"
            if pd.notna(row['Info']) and row['Info']:
                text += f"ℹ️ Info: {row['Info']}\n"
            text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("🔍 Search Another Place", callback_data="tourism")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Log to Google Sheets
        user_id = query.from_user.id
        user_name = query.from_user.first_name or "Unknown"
        user_lang = self._get_user_language(user_id)
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="homestay",
            query_text=f"Homestay search for {place}",
            language=user_lang,
            bot_response=text,
            place=place
        )

    # --- Common Service Centers ---
    async def handle_csc_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("Find Nearest CSC", callback_data='csc_find')],
            [InlineKeyboardButton("Apply for Certificate", callback_data='certificate')],
            [InlineKeyboardButton("Back to Main Menu", callback_data='main_menu')]
        ]
        text = """*Common Service Centers (CSC)* 💻

Please select an option:
1. Find nearest CSC
2. Apply for certificate
3. Return to main menu"""
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def handle_csc_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, district: str):
        # This will be used for finding nearest CSC
        self._set_user_state(update.effective_user.id, {"workflow": "certificate", "stage": "gpu"}) # piggybacking on certificate flow for now
        await update.callback_query.edit_message_text("Please enter your GPU (Gram Panchayat Unit):", parse_mode='Markdown')

    async def handle_certificate_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle certificate services information"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        text = f"*Apply for Certificate through Sikkim SSO* 💻\n\n{self.responses[user_lang]['certificate_info']}"

        keyboard = [
            [InlineKeyboardButton("✅ Yes, Connect with CSC", callback_data="certificate_csc")],
            [InlineKeyboardButton("🌐 No, I'll use SSO Portal", callback_data="certificate_sso")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_certificate_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str):
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        if choice == 'yes':
            self._set_user_state(user_id, {"workflow": "certificate", "stage": "gpu"})
            gpu_prompt = self.responses[user_lang]['certificate_gpu_prompt']
            await update.callback_query.edit_message_text(gpu_prompt, parse_mode='Markdown')
        else:
            sso_message = self.responses[user_lang]['certificate_sso_message']
            await update.callback_query.edit_message_text(sso_message, parse_mode='Markdown')
        
    async def handle_certificate_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle certificate application workflow with multilingual support"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        
        if state.get("stage") == "gpu":
            gpu = text.strip().upper()
            
            # Load CSC data if not already loaded
            try:
                csc_df = pd.read_csv('data/csc_contacts.csv')
                csc_info = csc_df[csc_df['GPU'].str.upper() == gpu]
                
                if csc_info.empty:
                    not_found_msg = self.responses[user_lang]['certificate_gpu_not_found']
                    await update.message.reply_text(not_found_msg, parse_mode='Markdown')
                else:
                    info = csc_info.iloc[0]
                    # Handle missing Timings column
                    timings = info.get('Timings', '9:00 AM - 5:00 PM (Mon-Fri)')
                    message = self.responses[user_lang]['certificate_csc_details'].format(
                        name=info['CSC_Operator_Name'],
                        contact=info['PhoneNumber'],
                        timings=timings
                    )
                    await update.message.reply_text(message, parse_mode='Markdown')
                    
                    # Log to Google Sheets
                    user_name = update.effective_user.first_name or "Unknown"
                    self._log_to_sheets(
                        user_id=user_id,
                        user_name=user_name,
                        interaction_type="certificate",
                        query_text=f"Certificate query for GPU: {gpu}",
                        language=user_lang,
                        bot_response=message,
                        certificate_type="CSC_Operator"
                    )
            except Exception as e:
                error_msg = self.responses[user_lang]['certificate_error']
                await update.message.reply_text(error_msg, parse_mode='Markdown')
                logger.error(f"Error in certificate workflow: {e}")
            
            self._clear_user_state(user_id)

    # --- Complaint ---
    async def start_emergency_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the emergency report workflow"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Set state for emergency workflow
        self._set_user_state(user_id, {
            "workflow": "emergency_report",
            "step": "name"
        })
        
        # Get appropriate message for emergency name request
        if user_lang == "hindi":
            message = "🚨 **आपातकालीन रिपोर्ट**\n\nकृपया अपना पूरा नाम दर्ज करें:"
        elif user_lang == "nepali":
            message = "🚨 **आपतकालीन रिपोर्ट**\n\nकृपया आफ्नो पूरा नाम दर्ता गर्नुहोस्:"
        else:
            message = "🚨 **Emergency Report**\n\nPlease provide your full name:"
        
        # Handle both callback queries and regular messages
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
        
        # Log to Google Sheets
        user_name = update.effective_user.first_name or "Unknown"
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="emergency_report",
            query_text="Emergency workflow started",
            language=user_lang,
            bot_response="Emergency workflow started",
            emergency_type="started"
        )

    async def start_complaint_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the complaint registration workflow"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Set state for complaint workflow
        self._set_user_state(user_id, {
            "workflow": "complaint",
            "step": "name"
        })
        
        # Get appropriate message for complaint name request
        if user_lang == "hindi":
            message = "📝 **शिकायत दर्ज करें**\n\nकृपया अपना पूरा नाम दर्ज करें:"
        elif user_lang == "nepali":
            message = "📝 **शिकायत दर्ता गर्नुहोस्**\n\nकृपया आफ्नो पूरा नाम दर्ता गर्नुहोस्:"
        else:
            message = "📝 **File a Complaint**\n\nPlease enter your full name:"
        
        # Handle both callback queries and regular messages
        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
        
        # Log to Google Sheets
        user_name = update.effective_user.first_name or "Unknown"
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="complaint",
            query_text="Complaint workflow started",
            language=user_lang,
            bot_response="Complaint workflow started",
            complaint_type="started"
        )

    async def handle_complaint_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the complaint workflow steps"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        text = update.message.text
        state = self._get_user_state(user_id)
        step = state.get("step")
        
        if step == "name":
            # Store both Telegram username and entered name
            telegram_username = update.effective_user.first_name or "Unknown"
            state["telegram_username"] = telegram_username
            state["entered_name"] = text
            state["name"] = f"{text} (@{telegram_username})"  # Combine both names
            state["step"] = "mobile"
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['complaint_mobile_prompt'], parse_mode='Markdown')
        
        elif step == "mobile":
            if not text.isdigit() or len(text) != 10:
                await update.message.reply_text(self.responses[user_lang]['complaint_mobile_error'], parse_mode='Markdown')
                return
            
            state["mobile"] = text
            state["step"] = "complaint"
            self._set_user_state(user_id, state)
            await update.message.reply_text(self.responses[user_lang]['complaint_description_prompt'], parse_mode='Markdown')
        
        elif step == "complaint":
            # Store complaint description and request location
            state["complaint_description"] = text
            state["step"] = "location"
            self._set_user_state(user_id, state)
            
            # Request location for complaint
            await self.request_location(update, context, "complaint")
            return
            
            # Send confirmation in user's language
            entered_name = state.get('entered_name', '')
            telegram_username = state.get('telegram_username', '')
            confirmation = self.responses[user_lang]['complaint_success'].format(
                complaint_id=complaint_id,
                name=entered_name,
                mobile=state.get('mobile'),
                telegram_username=telegram_username
            )
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Log to Google Sheets with both names and location
            telegram_username = state.get('telegram_username', update.effective_user.first_name or "Unknown")
            entered_name = state.get('entered_name', '')
            self._log_to_sheets(
                user_id=user_id,
                user_name=f"{entered_name} (@{telegram_username})",
                interaction_type="complaint",
                query_text=text,
                language=user_lang,
                bot_response=confirmation,
                complaint_type="General",
                status="New",
                latitude=latitude,
                longitude=longitude
            )
            
            # Clear user state
            self._clear_user_state(user_id)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the bot"""
        logger.error(f"[ERROR] {context.error}", exc_info=context.error)
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

    # New functionality methods
    async def handle_scheme_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle government schemes menu"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Create scheme selection keyboard from Excel data
        schemes = self.scheme_df['Farmer'].tolist()
        keyboard = []
        
        for i, scheme in enumerate(schemes):
            keyboard.append([InlineKeyboardButton(scheme, callback_data=f"scheme_{i+1}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton(
            self.responses[user_lang]['back_main_menu'],
            callback_data="main_menu"
        )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                self.responses[user_lang]['scheme_info'],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                self.responses[user_lang]['scheme_info'],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def handle_scheme_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, scheme_id: str):
        """Handle scheme selection and show details"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        try:
            scheme_index = int(scheme_id) - 1
            if 0 <= scheme_index < len(self.scheme_df):
                scheme_name = self.scheme_df.iloc[scheme_index]['Farmer']
                
                # Create scheme details message
                scheme_details = f"""🏛️ **{scheme_name}**

**How to Apply:**
1. Visit your nearest CSC center
2. Contact CSC operator for assistance
3. Submit required documents
4. Track application status

**Required Documents:**
• Aadhar Card
• Address Proof
• Income Certificate
• Other relevant documents

**Contact CSC Operator:**
Use the 'Important Contacts' section to find your nearest CSC operator.

Would you like to find your nearest CSC operator?"""
                
                keyboard = [
                    [InlineKeyboardButton("📞 Find CSC Operator", callback_data="contacts_csc")],
                    [InlineKeyboardButton("🔙 Back to Schemes", callback_data="schemes")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    scheme_details,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.callback_query.answer("Invalid scheme selection")
                
        except Exception as e:
            logger.error(f"❌ Error handling scheme selection: {str(e)}")
            await update.callback_query.answer("Error processing request")

    async def handle_contacts_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle important contacts menu"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🏛️ Find CSC Operator", callback_data="contacts_csc")],
            [InlineKeyboardButton("👤 Find BLO (Booth Level Officer)", callback_data="contacts_blo")],
            [InlineKeyboardButton("🆔 Aadhar Services", callback_data="contacts_aadhar")],
            [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                self.responses[user_lang]['contacts_info'],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                self.responses[user_lang]['contacts_info'],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def handle_csc_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle enhanced CSC search by GPU, ward, or constituency"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        self._set_user_state(user_id, {
            "workflow": "csc_search",
            "step": "gpu_input"
        })
        
        keyboard = [[InlineKeyboardButton(
            self.responses[user_lang]['back_main_menu'],
            callback_data="main_menu"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        search_prompt = """🔍 **Enhanced CSC Search**

You can search for CSC operators using:

**1. GPU Name** (e.g., "Karzi Mangnam GP")
**2. Ward Name** (e.g., "Mangder", "Tashiding")
**3. Constituency Name** (e.g., "KARZI MANGNAM")

Please enter your GPU name, ward name, or constituency name:"""
        
        await update.callback_query.edit_message_text(
            search_prompt,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_blo_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle BLO search by polling station"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        self._set_user_state(user_id, {
            "workflow": "blo_search",
            "step": "polling_station"
        })
        
        keyboard = [[InlineKeyboardButton(
            self.responses[user_lang]['back_main_menu'],
            callback_data="main_menu"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "Please enter your polling station name to find your BLO:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_aadhar_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Aadhar services information"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        aadhar_info = """🆔 **Aadhar Services**

**Available Services:**
• Aadhar Card Enrollment
• Aadhar Card Update
• Address Update
• Mobile Number Update
• Biometric Update
• Aadhar Card Reprint

**How to Apply:**
1. Visit your nearest CSC center
2. Contact CSC operator for assistance
3. Submit required documents
4. Pay applicable fees

**Required Documents:**
• Proof of Identity
• Proof of Address
• Date of Birth Certificate
• Mobile Number (for OTP)

**Contact:**
Use the CSC search to find your nearest operator."""
        
        keyboard = [
            [InlineKeyboardButton("📞 Find CSC Operator", callback_data="contacts_csc")],
            [InlineKeyboardButton("🔙 Back to Contacts", callback_data="contacts")],
            [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            aadhar_info,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def start_feedback_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the feedback workflow"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        self._set_user_state(user_id, {
            "workflow": "feedback",
            "step": "name"
        })
        
        keyboard = [[InlineKeyboardButton(
            self.responses[user_lang]['back_main_menu'],
            callback_data="main_menu"
        )]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                self.responses[user_lang]['feedback_info'],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                self.responses[user_lang]['feedback_info'],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def handle_feedback_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle feedback workflow steps"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        
        if not state or state.get('workflow') != 'feedback':
            return
        
        step = state.get('step')
        text = update.message.text
        
        if step == 'name':
            # Validate name
            if len(text.strip()) < 2:
                await update.message.reply_text(
                    self.responses[user_lang]['feedback_name_prompt'],
                    parse_mode='Markdown'
                )
                return
            
            self._set_user_state(user_id, {
                **state,
                'step': 'phone',
                'entered_name': text.strip()
            })
            
            await update.message.reply_text(
                self.responses[user_lang]['feedback_phone_prompt'],
                parse_mode='Markdown'
            )
            
        elif step == 'phone':
            # Validate phone number
            phone = text.strip()
            if not phone.isdigit() or len(phone) != 10:
                await update.message.reply_text(
                    "Please enter a valid 10-digit phone number:",
                    parse_mode='Markdown'
                )
                return
            
            self._set_user_state(user_id, {
                **state,
                'step': 'message',
                'phone': phone
            })
            
            await update.message.reply_text(
                self.responses[user_lang]['feedback_message_prompt'],
                parse_mode='Markdown'
            )
            
        elif step == 'message':
            # Generate feedback ID
            now = datetime.now()
            feedback_id = f"FB{now.strftime('%Y%m%d')}{random.randint(100, 999)}"
            
            # Save feedback to CSV
            feedback_data = {
                'Feedback_ID': feedback_id,
                'Name': state.get('entered_name', ''),
                'Phone': state.get('phone', ''),
                'Message': text,
                'Date': now.strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'New'
            }
            
            try:
                # Append to CSV file
                with open('data/feedback.csv', 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=feedback_data.keys())
                    writer.writerow(feedback_data)
                
                # Create confirmation message
                confirmation = self.responses[user_lang]['feedback_success'].format(
                    feedback_id=feedback_id
                )
                
                # Log to Google Sheets
                self._log_to_sheets(
                    user_id=user_id,
                    user_name=state.get('entered_name', ''),
                    interaction_type="feedback",
                    query_text=text,
                    language=user_lang,
                    bot_response=confirmation,
                    feedback_id=feedback_id
                )
                
                # Clear user state
                self._clear_user_state(user_id)
                
                # Send confirmation
                keyboard = [[InlineKeyboardButton(
                    self.responses[user_lang]['back_main_menu'],
                    callback_data="main_menu"
                )]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    confirmation,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"❌ Error saving feedback: {str(e)}")
                await update.message.reply_text(
                    self.responses[user_lang]['error'],
                    parse_mode='Markdown'
                )

    async def handle_csc_search_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle enhanced CSC search workflow using block-GPU mapping"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        text = update.message.text
        
        if state.get('step') == 'gpu_input':
            # Enhanced search for CSC by multiple criteria
            search_term = text.strip()
            
            # 1. First, try direct GPU name search in CSC details
            direct_gpu_match = self.csc_details_df[
                self.csc_details_df['GPU Name'].str.contains(search_term, case=False, na=False)
            ]
            
            if not direct_gpu_match.empty:
                # Direct GPU match found
                csc_info = direct_gpu_match.iloc[0]
                response = f"""🏛️ **CSC Operator Found**

**GPU:** {csc_info['GPU Name']}
**Block:** {csc_info['BLOCK']}
**Operator Name:** {csc_info['Name']}
**Contact:** {csc_info['Contact No.']}

**Block Single Window:** {csc_info['Block Single Window']}
**Sub Division Single Window:** {csc_info['SubDivision Single Window']}"""
                
                keyboard = [
                    [InlineKeyboardButton("🔙 Back to Contacts", callback_data="contacts")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
                self._clear_user_state(user_id)
                return
            
            # 2. Search by ward name in block-GPU mapping
            ward_matches = self.block_gpu_mapping_df[
                self.block_gpu_mapping_df['Name of Ward'].str.contains(search_term, case=False, na=False)
            ]
            
            if not ward_matches.empty:
                # Ward match found - find the corresponding GPU and CSC
                gpu_name = ward_matches.iloc[0]['Name of GPU']
                csc_match = self.csc_details_df[
                    self.csc_details_df['GPU Name'].str.contains(gpu_name, case=False, na=False)
                ]
                
                if not csc_match.empty:
                    csc_info = csc_match.iloc[0]
                    ward_name = ward_matches.iloc[0]['Name of Ward']
                    response = f"""🏛️ **CSC Operator Found (via Ward Search)**

**Ward:** {ward_name}
**GPU:** {csc_info['GPU Name']}
**Block:** {csc_info['BLOCK']}
**Operator Name:** {csc_info['Name']}
**Contact:** {csc_info['Contact No.']}

**Block Single Window:** {csc_info['Block Single Window']}
**Sub Division Single Window:** {csc_info['SubDivision Single Window']}"""
                    
                    keyboard = [
                        [InlineKeyboardButton("🔙 Back to Contacts", callback_data="contacts")],
                        [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
                    self._clear_user_state(user_id)
                    return
            
            # 3. Search by constituency name
            constituency_matches = self.block_gpu_mapping_df[
                self.block_gpu_mapping_df['Terrotorial Constituency Name'].str.contains(search_term, case=False, na=False)
            ]
            
            if not constituency_matches.empty:
                # Constituency match found - show all GPUs in that constituency
                constituency_name = constituency_matches.iloc[0]['Terrotorial Constituency Name']
                unique_gpus = constituency_matches['Name of GPU'].dropna().unique()
                
                response = f"""🏛️ **Constituency Found: {constituency_name}**

**Available GPUs in this constituency:**
"""
                
                for gpu in unique_gpus:
                    if pd.notna(gpu):
                        response += f"• {gpu}\n"
                
                response += f"\nPlease enter the specific GPU name from the list above to find the CSC operator."
                
                keyboard = [
                    [InlineKeyboardButton("�� Back to Contacts", callback_data="contacts")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
                self._clear_user_state(user_id)
                return
            
            # 4. No exact match found - provide suggestions
            # Get similar GPU names for suggestions
            all_gpu_names = self.csc_details_df['GPU Name'].dropna().tolist()
            suggestions = []
            
            for gpu_name in all_gpu_names:
                if search_term.lower() in gpu_name.lower() or gpu_name.lower() in search_term.lower():
                    suggestions.append(gpu_name)
            
            # Also check for similar ward names
            all_ward_names = self.block_gpu_mapping_df['Name of Ward'].dropna().tolist()
            for ward_name in all_ward_names:
                if search_term.lower() in ward_name.lower() or ward_name.lower() in search_term.lower():
                    suggestions.append(ward_name)
            
            # Remove duplicates and limit suggestions
            suggestions = list(set(suggestions))[:5]
            
            response = f"❌ **No exact match found for: {search_term}**\n\n"
            
            if suggestions:
                response += "**Did you mean one of these?**\n"
                for suggestion in suggestions:
                    response += f"• {suggestion}\n"
                response += "\nPlease try searching with one of the suggested names."
            else:
                response += "**Available GPUs in Sikkim:**\n"
                # Show first 10 GPUs as examples
                for i, gpu_name in enumerate(all_gpu_names[:10]):
                    response += f"• {gpu_name}\n"
                if len(all_gpu_names) > 10:
                    response += f"... and {len(all_gpu_names) - 10} more\n"
                response += "\nPlease enter the exact GPU name."
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Contacts", callback_data="contacts")],
                [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
            self._clear_user_state(user_id)

    async def handle_blo_search_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle enhanced BLO search workflow with better suggestions"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        text = update.message.text
        
        if state.get('step') == 'polling_station':
            # Enhanced search for BLO by polling station
            polling_station = text.strip()
            
            # Search in BLO details
            matching_blo = self.blo_details_df[
                self.blo_details_df['Polling Station'].str.contains(polling_station, case=False, na=False)
            ]
            
            if not matching_blo.empty:
                blo_info = matching_blo.iloc[0]
                response = f"""👤 **BLO (Booth Level Officer) Found**

**AC:** {blo_info['AC']}
**Polling Station:** {blo_info['Polling Station']}
**BLO Name:** {blo_info['BLO Details']}
**Mobile Number:** {blo_info['Mobile Number']}"""
                
                keyboard = [
                    [InlineKeyboardButton("🔙 Back to Contacts", callback_data="contacts")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                # No exact match found - provide suggestions
                all_polling_stations = self.blo_details_df['Polling Station'].dropna().tolist()
                suggestions = []
                
                for station in all_polling_stations:
                    if polling_station.lower() in station.lower() or station.lower() in polling_station.lower():
                        suggestions.append(station)
                
                # Remove duplicates and limit suggestions
                suggestions = list(set(suggestions))[:5]
                
                response = f"❌ **No BLO found for polling station: {polling_station}**\n\n"
                
                if suggestions:
                    response += "**Did you mean one of these polling stations?**\n"
                    for suggestion in suggestions:
                        response += f"• {suggestion}\n"
                    response += "\nPlease try searching with one of the suggested polling station names."
                else:
                    response += "**Available Polling Stations in Sikkim:**\n"
                    # Show first 10 polling stations as examples
                    for i, station in enumerate(all_polling_stations[:10]):
                        response += f"• {station}\n"
                    if len(all_polling_stations) > 10:
                        response += f"... and {len(all_polling_stations) - 10} more\n"
                    response += "\nPlease enter the exact polling station name."
                
                keyboard = [
                    [InlineKeyboardButton("🔙 Back to Contacts", callback_data="contacts")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Clear user state
            self._clear_user_state(user_id)

    def register_handlers(self):
        """Register message and callback handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("language", self.language_command))
        self.application.add_handler(CommandHandler("status", self.handle_status_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        self.application.add_error_handler(self.error_handler)  # Add error handler
        logger.info("✅ All handlers registered successfully")

    def run(self):
        """Run the bot"""
        try:
            # Create application
            self.application = Application.builder().token(self.BOT_TOKEN).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("language", self.language_command))
            self.application.add_handler(CommandHandler("status", self.handle_status_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
            self.application.add_handler(CallbackQueryHandler(self.callback_handler))
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            # Start the bot
            logger.info("🚀 Starting Enhanced SmartGov Assistant Bot...")
            print("🚀 Starting Enhanced SmartGov Assistant Bot...")
            print("✅ Ready to serve citizens!")
            
            # Run the bot until the user presses Ctrl-C
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {str(e)}")
            raise

    async def handle_ex_gratia_with_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location_data: dict):
        """Handle ex-gratia application with user location"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        data = state.get("data", {})
        
        # Add location data to application data
        data["latitude"] = location_data.get("latitude")
        data["longitude"] = location_data.get("longitude")
        data["location_timestamp"] = location_data.get("timestamp")
        
        # Update state with location data
        state["data"] = data
        self._set_user_state(user_id, state)
        
        # Show confirmation with all collected data
        await self.show_ex_gratia_confirmation(update, context, data)

    async def check_nc_exgratia_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, reference_number: str):
        """Check NC Exgratia application status using API"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        try:
            # Check if API client is available
            if not self.api_client:
                error_msg = "❌ NC Exgratia API is not configured. Please contact support."
                await update.message.reply_text(error_msg, parse_mode='Markdown')
                return
            
            # Show processing message
            processing_msg = f"🔍 Checking status for application: {reference_number}\n\nPlease wait..."
            await update.message.reply_text(processing_msg, parse_mode='Markdown')
            
            # Check status via API
            status_result = await self.api_client.check_application_status(reference_number)
            
            if status_result.get("success"):
                # Status retrieved successfully
                status_data = status_result.get("data", {})
                application_data = status_data.get("application", {})
                
                status = application_data.get("status", "Unknown")
                applicant_name = application_data.get("applicant_name", "Unknown")
                created_at = application_data.get("created_at", "Unknown")
                
                # Format created date
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    formatted_date = created_at
                
                status_msg = f"""📋 *NC Exgratia Application Status*

🆔 **Reference Number**: `{reference_number}`
👤 **Applicant**: {applicant_name}
📅 **Submitted**: {formatted_date}
📊 **Status**: {status}

*Status Information:*
• Your application is being processed
• You'll receive updates via SMS
• Contact support for any queries: {Config.SUPPORT_PHONE}"""
                
                keyboard = [
                    [InlineKeyboardButton("🔙 Back to Disaster Management", callback_data="disaster")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(status_msg, reply_markup=reply_markup, parse_mode='Markdown')
                
            else:
                # Status check failed
                error_details = status_result.get("details", "Unknown error")
                logger.error(f"❌ NC Exgratia status check failed: {error_details}")
                
                error_msg = f"""❌ *Status Check Failed*

Unable to retrieve status for application: {reference_number}

*Error Details:*
{error_details}

*What to do:*
1. Verify the reference number is correct
2. Try again in a few minutes
3. Contact support: {Config.SUPPORT_PHONE}"""
                
                keyboard = [[InlineKeyboardButton("🔙 Back to Disaster Management", callback_data="disaster")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"❌ Error checking application status: {str(e)}")
            error_msg = f"""❌ *Status Check Error*

An unexpected error occurred while checking status.

*Error:*
{str(e)}

Contact support: {Config.SUPPORT_PHONE}"""
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Disaster Management", callback_data="disaster")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')

    async def cancel_ex_gratia_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self._clear_user_state(user_id)
        await update.callback_query.edit_message_text("Your application has been cancelled.")
        await self.show_main_menu(update, context)

    async def handle_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command for checking NC Exgratia application status"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Check if reference number is provided
        if not context.args:
            help_msg = f"""📋 *NC Exgratia Status Check*

To check your application status, use:
`/status <reference_number>`

*Example:*
`/status SK2025MN0003`

*Or use the menu:*
Disaster Management → Check Status"""
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(help_msg, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Get reference number from command arguments
        reference_number = context.args[0].strip()
        
        # Check status
        await self.check_nc_exgratia_status(update, context, reference_number)

if __name__ == "__main__":
    # Initialize and run bot
    bot = SmartGovAssistantBot()
    bot.run() 