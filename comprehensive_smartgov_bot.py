#!/usr/bin/env python3
"""
Comprehensive Sikkim Sajilo Sewak Bot
"""
import asyncio
import csv
import json
import logging
import pandas as pd
import threading
import sys
import os
import aiohttp
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Location
from simple_location_system import SimpleLocationSystem
from enhanced_conversation_system import EnhancedConversationSystem
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

class SajiloSewakBot:
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
            logger.info(" NC Exgratia API client initialized")
        else:
            logger.warning(" NC Exgratia API integration disabled")
        
        logger.info(" MULTI-USER SUPPORT: Thread-safe state management initialized")

        # Initialize location system with main bot reference
        self.location_system = SimpleLocationSystem()
        self.location_system.main_bot = self  # Pass main bot reference
        logger.info('Location system initialized')

        # Initialize enhanced conversation system
        self.conversation_system = EnhancedConversationSystem()
        logger.info('Enhanced conversation system initialized')

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
            
            logger.info(" Data files from Excel sheet loaded successfully")
        except Exception as e:
            logger.error(f"Error loading data files: {str(e)}")
            raise

    def _initialize_google_sheets(self):
        """Initialize Google Sheets service"""
        try:
            if Config.GOOGLE_SHEETS_ENABLED and Config.GOOGLE_SHEETS_CREDENTIALS_FILE:
                self.sheets_service = GoogleSheetsService(
                    credentials_file=Config.GOOGLE_SHEETS_CREDENTIALS_FILE,
                    spreadsheet_id=Config.GOOGLE_SHEETS_SPREADSHEET_ID
                )
                logger.info("Google Sheets service initialized successfully")
            else:
                self.sheets_service = None
                logger.warning(" Google Sheets integration disabled or credentials file not configured")
        except Exception as e:
            logger.error(f"Error initializing Google Sheets service: {str(e)}")
            self.sheets_service = None

    def _initialize_responses(self):
        """Initialize multilingual response templates"""
        self.responses = {
            'english': {
                        'welcome': "Welcome to Sajilo Sewak! How can I help you today?",
        'main_menu': """ *Welcome to Sajilo Sewak* 

Our services include:

        1. *Book Homestay*
   • Search by tourist destinations
   • View ratings and prices
   • Direct contact with owners

        2. *Emergency Services*
   • Ambulance (102/108)
   • Police Helpline
   • Suicide Prevention
   • Health Helpline
   • Women Helpline
   • Fire Emergency
   • Report Disaster

        3. *Report a Complaint*
   • Register your grievance
   • Get complaint tracking ID
   • 24/7 monitoring

4. *Apply for Certificate* 
   • CSC operator assistance
   • Sikkim SSO portal link
   • Track application status

5. *Disaster Management* 
   • Apply for Ex-gratia
   • Check application status
   • View relief norms
   • Emergency contacts

6. *Government Schemes* 
   • Learn about schemes
   • Apply for benefits
   • Track applications

7. *Important Contacts* 
   • Find your CSC
   • Know your BLO
   • Aadhar Services

        8. *Give Feedback*
   • Share your experience
   • Suggest improvements
   • Help us serve better

Please select a service to continue:""",
                'button_homestay': "Book Homestay",
                'button_emergency': "Emergency Services",
                'button_complaint': "Report a Complaint",
                'button_certificate': "Apply for Certificate",
                'button_disaster': "Disaster Management",
                'button_schemes': "Government Schemes",
                'button_contacts': "Important Contacts",
                'button_feedback': "Give Feedback",
                'error': "Sorry, I encountered an error. Please try again.",
                'unknown': "I'm not sure what you're asking for. Here are the available services:",
                'processing': "Processing your request...",
                'success': "Your request has been processed successfully.",
                'cancelled': "Operation cancelled. How else can I help you?",
                'emergency_ambulance': "*Ambulance Emergency*\nDial: 102 or 108\nControl Room: 03592-202033",
                'emergency_police': "*Police Emergency*\nDial: 100\nControl Room: 03592-202022",
                'emergency_fire': "*Fire Emergency*\nDial: 101\nControl Room: 03592-202099",
                'emergency_suicide': "*Suicide Prevention Helpline*\nDial: 9152987821",
                'emergency_women': "*Women Helpline*\nDial: 1091\nState Commission: 03592-205607",
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
                'certificate_info': "You can apply for certificates in two ways:\n\n1. **Apply Online** - Use the Sikkim SSO portal directly\n2. **Apply via CSC** - Get assistance from your nearest Common Service Centre\n\nWhich method would you prefer?",
                'other_emergency': "Other Emergency Services",
                'back_main_menu': "Back to Main Menu",
                'language_menu': "*Language Selection*\n\nPlease select your preferred language:",
                'language_changed': "Language changed to English successfully!",
                'language_button_english': " English",
                'language_button_hindi': " हिंदी",
                'complaint_title': "*Report a Complaint/Grievance* ",
                'complaint_name_prompt': "Please enter your full name:",
                'complaint_mobile_prompt': "Please enter your mobile number:",
                'complaint_mobile_error': "Please enter a valid 10-digit mobile number.",
                'complaint_description_prompt': "Please describe your complaint in detail:",
                'complaint_success': " *Complaint Registered Successfully*\n\n Complaint ID: {complaint_id}\n Name: {name}\n Mobile: {mobile}\n Telegram: @{telegram_username}\n\nYour complaint has been registered and will be processed soon. Please save your Complaint ID for future reference.",
                'certificate_gpu_prompt': "Please enter your GPU (Gram Panchayat Unit):",
                'certificate_sso_message': "You can apply directly on the Sikkim SSO Portal: https://sso.sikkim.gov.in",
                'certificate_gpu_not_found': "Sorry, no CSC operator found for your GPU. Please check the GPU number and try again.",
                'certificate_csc_details': "*CSC Operator Details*\n\nName: {name}\nContact: {contact}\nTimings: {timings}",
                'certificate_error': "Sorry, there was an error processing your request. Please try again.",
                
                # New features responses
                'scheme_info': """ **Government Schemes & Applications**

Available schemes include:
• PM KISAN
• PM Fasal Bima
• PM Vishwakarma
• Fisheries Registration
• Kishan Credit Card
• And many more...

Select a scheme to learn more and apply:""",
                
                'contacts_info': """ **Important Contacts**

Choose the type of contact you need:
• **CSC (Common Service Center)** - Find your nearest CSC operator
• **BLO (Booth Level Officer)** - Electoral roll services
• **Aadhar Services** - Aadhar card related services

Select an option:""",
                
                'feedback_info': """ **Give Feedback**

We value your feedback to improve our services. Please provide:
• Your name
• Phone number
• Your feedback/suggestions

Let's start with your name:""",
                
                'feedback_name_prompt': "Please enter your name:",
                'feedback_phone_prompt': "Please enter your phone number:",
                'feedback_message_prompt': "Please share your feedback or suggestions:",
                'feedback_success': """ **Feedback Submitted Successfully!**

Thank you for your feedback. We will review it and work on improvements.

Your feedback ID: {feedback_id}""",
                'emergency_type_prompt': " *Emergency Services*\n\nPlease select the type of emergency:",
                'emergency_details_prompt': " *{service_type} Emergency*\n\nPlease provide details about your emergency situation:",
                'complaint_location_prompt': " *Location Information*\n\nTo help us respond better, would you like to share your location?",
                'error_message': " Sorry, something went wrong. Please try again.",
            },
            'hindi': {
                'welcome': "स्मार्टगव सहायक में आपका स्वागत है! मैं आपकी कैसे मदद कर सकता हूं?",
                'main_menu': """ *स्मार्टगव सहायक में आपका स्वागत है* 

हमारी सेवाएं शामिल हैं:

1. *होमस्टे बुक करें* 
   • पर्यटन स्थलों के अनुसार खोजें
   • रेटिंग और कीमतें देखें
   • मालिकों से सीधा संपर्क

2. *आपातकालीन सेवाएं* 
   • एम्बुलेंस (102/108)
   • पुलिस हेल्पलाइन
   • आत्महत्या रोकथाम
   • स्वास्थ्य हेल्पलाइन
   • महिला हेल्पलाइन
   • अग्निशमन आपातकाल
   • आपदा की रिपोर्ट करें

3. *शिकायत दर्ज करें* 
   • अपनी शिकायत पंजीकृत करें
   • शिकायत ट्रैकिंग आईडी प्राप्त करें
   • 24/7 निगरानी

4. *प्रमाणपत्र के लिए आवेदन करें* 
   • CSC ऑपरेटर सहायता
   • सिक्किम SSO पोर्टल लिंक
   • आवेदन स्थिति ट्रैक करें

5. *आपदा प्रबंधन* 
   • एक्स-ग्रेटिया के लिए आवेदन करें
   • आवेदन स्थिति जांचें
   • राहत मानदंड देखें
   • आपातकालीन संपर्क

कृपया जारी रखने के लिए एक सेवा चुनें:""",
                'button_homestay': " होमस्टे बुक करें",
                'button_emergency': " आपातकालीन सेवाएं",
                'button_complaint': " शिकायत दर्ज करें",
                'button_certificate': " प्रमाणपत्र के लिए आवेदन",
                'button_disaster': " आपदा प्रबंधन",
                'button_schemes': " सरकारी योजनाएं",
                'button_contacts': " महत्वपूर्ण संपर्क",
                'button_feedback': " प्रतिक्रिया दें",
                'error': "क्षमा करें, कोई त्रुटि हुई। कृपया पुनः प्रयास करें।",
                'unknown': "मुझे समझ नहीं आया। यहाँ उपलब्ध सेवाएं हैं:",
                'processing': "आपका अनुरोध प्रोसेस किया जा रहा है...",
                'success': "आपका अनुरोध सफलतापूर्वक प्रोसेस कर दिया गया है।",
                'cancelled': "प्रक्रिया रद्द कर दी गई। मैं और कैसे मदद कर सकता हूं?",
                'emergency_ambulance': " *एम्बुलेंस इमरजेंसी*\nडायल करें: 102 या 108\nकंट्रोल रूम: 03592-202033",
                'emergency_police': " *पुलिस इमरजेंसी*\nडायल करें: 100\nकंट्रोल रूम: 03592-202022",
                'emergency_fire': " *अग्निशमन इमरजेंसी*\nडायल करें: 101\nकंट्रोल रूम: 03592-202099",
                'emergency_suicide': " *आत्महत्या रोकथाम हेल्पलाइन*\nडायल करें: 9152987821",
                'emergency_women': " *महिला हेल्पलाइन*\nडायल करें: 1091\nराज्य आयोग: 03592-205607",
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
                'certificate_info': "आप प्रमाणपत्र के लिए दो तरीकों से आवेदन कर सकते हैं:\n\n1. **ऑनलाइन आवेदन** - सिक्किम SSO पोर्टल का सीधा उपयोग करें\n2. **CSC के माध्यम से आवेदन** - अपने निकटतम कॉमन सर्विस सेंटर से सहायता प्राप्त करें\n\nआप कौन सा तरीका पसंद करेंगे?",
                'other_emergency': " अन्य आपातकालीन सेवाएं",
                'back_main_menu': " मुख्य मेनू पर वापस",
                'language_menu': " *भाषा चयन*\n\nकृपया अपनी पसंदीदा भाषा चुनें:",
                'language_changed': " भाषा सफलतापूर्वक हिंदी में बदल दी गई!",
                'language_button_english': " English",
                'language_button_hindi': " हिंदी",
                'complaint_title': "*शिकायत/ग्रिवेंस दर्ज करें* ",
                'complaint_name_prompt': "कृपया अपना पूरा नाम दर्ज करें:",
                'complaint_mobile_prompt': "कृपया अपना मोबाइल नंबर दर्ज करें:",
                'complaint_mobile_error': "कृपया एक वैध 10-अंकीय मोबाइल नंबर दर्ज करें।",
                'complaint_description_prompt': "कृपया अपनी शिकायत का विस्तृत विवरण दें:",
                'complaint_success': " *शिकायत सफलतापूर्वक दर्ज की गई*\n\n शिकायत आईडी: {complaint_id}\n नाम: {name}\n मोबाइल: {mobile}\n टेलीग्राम: @{telegram_username}\n\nआपकी शिकायत दर्ज कर दी गई है और जल्द ही प्रोसेस की जाएगी। कृपया भविष्य के संदर्भ के लिए अपनी शिकायत आईडी सहेजें।",
                'certificate_gpu_prompt': "कृपया अपना GPU (ग्राम पंचायत इकाई) दर्ज करें:",
                'certificate_sso_message': "आप सीधे सिक्किम SSO पोर्टल पर आवेदन कर सकते हैं: https://sso.sikkim.gov.in",
                'certificate_gpu_not_found': "क्षमा करें, आपके GPU के लिए कोई CSC ऑपरेटर नहीं मिला। कृपया GPU नंबर जांचें और पुनः प्रयास करें।",
                'certificate_csc_details': "*CSC ऑपरेटर विवरण*\n\nनाम: {name}\nसंपर्क: {contact}\nसमय: {timings}",
                'certificate_error': "क्षमा करें, आपके अनुरोध को प्रोसेस करने में त्रुटि हुई। कृपया पुनः प्रयास करें।",
                
                # New features responses
                'scheme_info': """ **सरकारी योजनाएं और आवेदन**

उपलब्ध योजनाएं:
• पीएम किसान
• पीएम फसल बीमा
• पीएम विश्वकर्मा
• मत्स्य पालन पंजीकरण
• किसान क्रेडिट कार्ड
• और भी बहुत कुछ...

अधिक जानने और आवेदन करने के लिए योजना चुनें:""",
                
                'contacts_info': """ **महत्वपूर्ण संपर्क**

आपको किस प्रकार का संपर्क चाहिए:
• **सीएससी (सामान्य सेवा केंद्र)** - अपना निकटतम सीएससी ऑपरेटर खोजें
• **बीएलओ (बूथ लेवल अधिकारी)** - मतदाता सूची सेवाएं
• **आधार सेवाएं** - आधार कार्ड संबंधित सेवाएं

एक विकल्प चुनें:""",
                
                'feedback_info': """ **प्रतिक्रिया दें**

हमारी सेवाओं को बेहतर बनाने के लिए आपकी प्रतिक्रिया महत्वपूर्ण है। कृपया प्रदान करें:
• आपका नाम
• फोन नंबर
• आपकी प्रतिक्रिया/सुझाव

आइए आपके नाम से शुरू करें:""",
                
                'feedback_name_prompt': "कृपया अपना नाम दर्ज करें:",
                'feedback_phone_prompt': "कृपया अपना फोन नंबर दर्ज करें:",
                'feedback_message_prompt': "कृपया अपनी प्रतिक्रिया या सुझाव साझा करें:",
                'feedback_success': """ **प्रतिक्रिया सफलतापूर्वक सबमिट की गई!**

आपकी प्रतिक्रिया के लिए धन्यवाद। हम इसे समीक्षा करेंगे और सुधारों पर काम करेंगे।

आपकी प्रतिक्रिया आईडी: {feedback_id}""",
                'emergency_type_prompt': " *Emergency Services*\n\nPlease select the type of emergency:",
                'emergency_details_prompt': " *{service_type} Emergency*\n\nPlease provide details about your emergency situation:",
                'complaint_location_prompt': " *Location Information*\n\nTo help us respond better, would you like to share your location?",
                'error_message': " Sorry, something went wrong. Please try again.",
            },
            'nepali': {
                'welcome': "स्मार्टगभ सहायकमा स्वागत छ! म तपाईंलाई कसरी मद्दत गर्न सक्छु?",
                'main_menu': """ *स्मार्टगभ सहायकमा स्वागत छ* 

हाम्रो सेवाहरू समावेश छन्:

1. *होमस्टे बुक गर्नुहोस्* 
   • पर्यटन स्थलहरू अनुसार खोज्नुहोस्
   • रेटिङ र मूल्यहरू हेर्नुहोस्
   • मालिकहरूसँग सिधा सम्पर्क

2. *आकस्मिक सेवाहरू* 
   • एम्बुलेन्स (102/108)
   • प्रहरी हेल्पलाइन
   • आत्महत्या रोकथाम
   • स्वास्थ्य हेल्पलाइन
   • महिला हेल्पलाइन
   • अग्निशमन आकस्मिक
   • आपदा रिपोर्ट गर्नुहोस्

3. *शिकायत दर्ता गर्नुहोस्* 
   • आफ्नो शिकायत दर्ता गर्नुहोस्
   • शिकायत ट्र्याकिङ आईडी प्राप्त गर्नुहोस्
   • 24/7 निगरानी

4. *प्रमाणपत्रको लागि आवेदन गर्नुहोस्* 
   • CSC सञ्चालक सहायता
   • सिक्किम SSO पोर्टल लिङ्क
   • आवेदन स्थिति ट्र्याक गर्नुहोस्

5. *आपदा व्यवस्थापन* 
   • एक्स-ग्रेटियाको लागि आवेदन गर्नुहोस्
   • आवेदन स्थिति जाँच गर्नुहोस्
   • राहत मापदण्ड हेर्नुहोस्
   • आकस्मिक सम्पर्कहरू

कृपया जारी राख्न सेवा छान्नुहोस्:""",
                'button_homestay': " होमस्टे बुक गर्नुहोस्",
                'button_emergency': " आकस्मिक सेवाहरू",
                'button_complaint': " शिकायत दर्ता गर्नुहोस्",
                'button_certificate': " प्रमाणपत्रको लागि आवेदन",
                'button_disaster': " आपदा व्यवस्थापन",
                'button_schemes': " सरकारी योजनाहरू",
                'button_contacts': " महत्वपूर्ण सम्पर्कहरू",
                'button_feedback': " प्रतिक्रिया दिनुहोस्",
                'error': "माफ गर्नुहोस्, त्रुटि भयो। कृपया पुन: प्रयास गर्नुहोस्।",
                'unknown': "मलाई बुझ्न सकिएन। यहाँ उपलब्ध सेवाहरू छन्:",
                'processing': "तपाईंको अनुरोध प्रशोधन गरिँदैछ...",
                'success': "तपाईंको अनुरोध सफलतापूर्वक प्रशोधन गरियो।",
                'cancelled': "प्रक्रिया रद्द गरियो। म अरु कसरी मद्दत गर्न सक्छु?",
                'emergency_ambulance': " *एम्बुलेन्स आकस्मिक*\nडायल गर्नुहोस्: 102 वा 108\nकन्ट्रोल रूम: 03592-202033",
                'emergency_police': " *प्रहरी आकस्मिक*\nडायल गर्नुहोस्: 100\nकन्ट्रोल रूम: 03592-202022",
                'emergency_fire': " *अग्निशमन आकस्मिक*\nडायल गर्नुहोस्: 101\nकन्ट्रोल रूम: 03592-202099",
                'emergency_suicide': " *आत्महत्या रोकथाम हेल्पलाइन*\nडायल गर्नुहोस्: 9152987821",
                'emergency_women': " *महिला हेल्पलाइन*\nडायल गर्नुहोस्: 1091\nराज्य आयोग: 03592-205607",
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
                'certificate_info': "तपाईंले प्रमाणपत्रको लागि दुई तरिकाले आवेदन गर्न सक्नुहुन्छ:\n\n1. **अनलाइन आवेदन** - सिक्किम SSO पोर्टल सिधै प्रयोग गर्नुहोस्\n2. **CSC मार्फत आवेदन** - आफ्नो नजिकैको कमन सर्भिस सेन्टरबाट सहायता लिनुहोस्\n\nतपाईं कुन तरिका रोज्नुहुन्छ?",
                'other_emergency': " अन्य आकस्मिक सेवाहरू",
                'back_main_menu': " मुख्य मेनुमा फिर्ता",
                'language_menu': " *भाषा चयन*\n\nकृपया तपाईंको मनपर्ने भाषा छान्नुहोस्:",
                'language_changed': " भाषा सफलतापूर्वक नेपालीमा बदलियो!",
                'language_button_english': " English",
                'language_button_hindi': " हिंदी",
                'complaint_title': "*शिकायत/ग्रिवेंस दर्ता गर्नुहोस्* ",
                'complaint_name_prompt': "कृपया आफ्नो पूरा नाम प्रविष्ट गर्नुहोस्:",
                'complaint_mobile_prompt': "कृपया आफ्नो मोबाइल नम्बर प्रविष्ट गर्नुहोस्:",
                'complaint_mobile_error': "कृपया एक वैध 10-अंकीय मोबाइल नम्बर प्रविष्ट गर्नुहोस्।",
                'complaint_description_prompt': "कृपया आफ्नो शिकायतको विस्तृत विवरण दिनुहोस्:",
                'complaint_success': " *शिकायत सफलतापूर्वक दर्ता गरियो*\n\n शिकायत आईडी: {complaint_id}\n नाम: {name}\n मोबाइल: {mobile}\n टेलीग्राम: @{telegram_username}\n\nतपाईंको शिकायत दर्ता गरियो र चाँडै प्रशोधन गरिनेछ। कृपया भविष्यको सन्दर्भको लागि आफ्नो शिकायत आईडी सुरक्षित गर्नुहोस्।",
                'certificate_gpu_prompt': "कृपया आफ्नो GPU (ग्राम पंचायत इकाई) प्रविष्ट गर्नुहोस्:",
                'certificate_sso_message': "तपाईं सिधै सिक्किम SSO पोर्टलमा आवेदन गर्न सक्नुहुन्छ: https://sso.sikkim.gov.in",
                'certificate_gpu_not_found': "माफ गर्नुहोस्, तपाईंको GPU को लागि कुनै CSC सञ्चालक फेला परेनन्। कृपया GPU नम्बर जाँच गर्नुहोस् र पुन: प्रयास गर्नुहोस्।",
                'certificate_csc_details': "*CSC सञ्चालक विवरण*\n\nनाम: {name}\nसम्पर्क: {contact}\nसमय: {timings}",
                'certificate_error': "माफ गर्नुहोस्, तपाईंको अनुरोध प्रशोधन गर्दा त्रुटि भयो। कृपया पुन: प्रयास गर्नुहोस्।",
                
                # New features responses
                'scheme_info': """ **सरकारी योजनाहरू र आवेदनहरू**

उपलब्ध योजनाहरू:
• पीएम किसान
• पीएम फसल बीमा
• पीएम विश्वकर्मा
• माछा पालन दर्ता
• किसान क्रेडिट कार्ड
• र धेरै अन्य...

थप जान्न र आवेदन गर्न योजना छान्नुहोस्:""",
                
                'contacts_info': """ **महत्वपूर्ण सम्पर्कहरू**

तपाईंलाई कुन प्रकारको सम्पर्क चाहिन्छ:
• **CSC (साझा सेवा केन्द्र)** - आफ्नो नजिकैको CSC सञ्चालक फेला पार्नुहोस्
• **बूथ लेवल अधिकारी)** - मतदाता सूची सेवाहरू
• **आधार सेवाहरू** - आधार कार्ड सम्बन्धित सेवाहरू

एउटा विकल्प छान्नुहोस्:""",
                
                'feedback_info': """ **प्रतिक्रिया दिनुहोस्**

हाम्रो सेवाहरू सुधार गर्न तपाईंको प्रतिक्रिया महत्वपूर्ण छ। कृपया प्रदान गर्नुहोस्:
• तपाईंको नाम
• फोन नम्बर
• तपाईंको प्रतिक्रिया/सुझावहरू

तपाईंको नामबाट सुरु गर्नुहोस्:""",
                
                'feedback_name_prompt': "कृपया आफ्नो नाम प्रविष्ट गर्नुहोस्:",
                'feedback_phone_prompt': "कृपया आफ्नो फोन नम्बर प्रविष्ट गर्नुहोस्:",
                'feedback_message_prompt': "कृपया आफ्नो प्रतिक्रिया वा सुझाव साझा गर्नुहोस्:",
                'feedback_success': """ **प्रतिक्रिया सफलतापूर्वक सबमिट गरियो!**

तपाईंको प्रतिक्रियाको लागि धन्यवाद। हामी यसलाई समीक्षा गर्नेछौं र सुधारहरूमा काम गर्नेछौं।

तपाईंको प्रतिक्रिया आईडी: {feedback_id}""",
                'emergency_type_prompt': " *Emergency Services*\n\nPlease select the type of emergency:",
                'emergency_details_prompt': " *{service_type} Emergency*\n\nPlease provide details about your emergency situation:",
                'complaint_location_prompt': " *Location Information*\n\nTo help us respond better, would you like to share your location?",
                'error_message': " Sorry, something went wrong. Please try again.",
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
            logger.info(f" STATE UPDATE: User {user_id} → {state}")

    def _clear_user_state(self, user_id: int):
        """Safely clear user state with locking"""
        with self._state_lock:
            if user_id in self.user_states:
                del self.user_states[user_id]
                logger.info(f" STATE CLEARED: User {user_id}")

    def _get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        with self._state_lock:
            return self.user_languages.get(user_id, 'english')

    def _set_user_language(self, user_id: int, language: str):
        """Set user's preferred language"""
        with self._state_lock:
            self.user_languages[user_id] = language
            logger.info(f" LANGUAGE SET: User {user_id} → {language}")

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None:
            self._session = aiohttp.ClientSession()

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
                message = "स्थान डिस्पैच के लिए आवश्यक है। कृपया अपना वर्तमान स्थान साझा करें "
            elif user_lang == "nepali":
                message = "स्थान डिस्पैचको लागि आवश्यक छ। कृपया आफ्नो वर्तमान स्थान साझा गर्नुहोस् "
            else:
                message = "Location is required for dispatch. Please share your current location "
            
            # Request location for emergency
            await self.location_system.request_location(update, context, "emergency")
            return

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
            elif interaction_type == "csc_scheme_application":
                # Log CSC scheme application to dedicated sheet
                self.sheets_service.log_scheme_application(
                    user_id=user_id,
                    user_name=user_name,
                    scheme_name=kwargs.get('scheme_name', ''),
                    applicant_name=kwargs.get('applicant_name', ''),
                    father_name=kwargs.get('father_name', ''),
                    phone=kwargs.get('phone', ''),
                    village=kwargs.get('village', ''),
                    ward=kwargs.get('ward', ''),
                    gpu=kwargs.get('gpu', ''),
                    block=kwargs.get('block', ''),
                    reference_number=kwargs.get('reference_number', ''),
                    application_status=kwargs.get('application_status', ''),
                    submission_date=kwargs.get('submission_date', ''),
                    language=language
                )
            elif interaction_type == "certificate_application":
                # Log certificate application to dedicated sheet
                self.sheets_service.log_certificate_application(
                    user_id=user_id,
                    user_name=user_name,
                    certificate_type=kwargs.get('certificate_type', ''),
                    applicant_name=kwargs.get('applicant_name', ''),
                    father_name=kwargs.get('father_name', ''),
                    phone=kwargs.get('phone', ''),
                    village=kwargs.get('village', ''),
                    gpu=kwargs.get('gpu', ''),
                    block=kwargs.get('block', ''),
                    reference_number=kwargs.get('reference_number', ''),
                    application_status=kwargs.get('application_status', ''),
                    submission_date=kwargs.get('submission_date', ''),
                    language=language
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
            
            return True  # Return True on successful logging
        except Exception as e:
            logger.error(f" Error logging to Google Sheets: {str(e)}")
            return False  # Return False on error

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
            
            logger.info(f" [LLM] Language Detection Prompt: {prompt}")
            
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
                
                logger.info(f" [LLM] Language Detection Response: {detected_lang}")
                
                # Validate response
                if detected_lang in ['english', 'hindi', 'nepali']:
                    logger.info(f" Language detected by Qwen: {detected_lang}")
                    return detected_lang
                else:
                    logger.warning(f" Invalid language detection result: {detected_lang}, falling back to English")
                    return 'english'
                    
        except Exception as e:
            logger.error(f" Language detection failed: {str(e)}")
            return 'english'  # Fallback to English on error

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Simplified message handler with working location system"""
        if not update.message:
            return
        
        user_id = update.effective_user.id
        
        # Debug logging for all message types
        logger.info(f" [DEBUG] Message type: {type(update.message)}")
        logger.info(f" [DEBUG] Has location: {hasattr(update.message, 'location') and update.message.location}")
        logger.info(f" [DEBUG] Has text: {hasattr(update.message, 'text') and update.message.text}")
        
        # Handle location messages FIRST
        if update.message.location:
            logger.info(f" [MAIN] Location message detected from user {user_id}")
            # Pass the user state to the location system
            user_state = self._get_user_state(user_id)
            context.user_data['user_state'] = user_state
            await self.location_system.handle_location_received(update, context)
            return
        
        # Handle text messages
        if not update.message.text:
            return
        
        message_text = update.message.text
        logger.info(f"[MSG] User {user_id}: {message_text}")
        
        # Handle location-related buttons
        if message_text == "⏭ Skip Location":
            await self.location_system.handle_location_skip(update, context)
            return
        elif message_text == " Cancel":
            await self.location_system.handle_location_cancel(update, context)
            return
        
        # Check if waiting for location
        if context.user_data.get('location_request'):
            # User sent text instead of location, continue without location
            await self.location_system.handle_location_skip(update, context)
            return
        
        # Check if this interaction should capture location
        # BUT skip for emergency messages that should go to call buttons
        if self.location_system.should_capture_location(message_text):
            interaction_type = self.location_system.detect_interaction_type(message_text)
            
            # For emergency messages, let them go to normal processing for call buttons
            if interaction_type == "emergency":
                # Let emergency messages go to normal processing for call buttons
                logger.info(f" [MAIN] Emergency message detected, bypassing location system for call buttons")
            else:
                # For non-emergency messages, request location as usual
                user_state = self._get_user_state(user_id)
                context.user_data['user_state'] = user_state
                await self.location_system.request_location(update, context, interaction_type, message_text)
                return
        
        # Continue with normal message processing
        await self._process_normal_message(update, context, message_text)

    async def _process_normal_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
        """Process normal messages (existing logic)"""
        user_id = update.effective_user.id
        
        try:
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
            
            # Handle natural language cancel
            cancel_keywords = [
                "cancel", "band karo", "रद्द करें", "रद्द", "बंद करो", 
                "stop", "quit", "exit", "back", "home", "main menu", "मुख्य मेनू",
                "घर जाओ", "वापस जाओ", "बंद", "छोड़ो", "छोड़ दो"
            ]
            
            if message_text.lower().strip() in [kw.lower() for kw in cancel_keywords]:
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
                
                if workflow == "ex_gratia":
                    await self.handle_ex_gratia_workflow(update, context, message_text)
                elif workflow == "complaint":
                    await self.handle_complaint_workflow(update, context)
                elif workflow == "emergency_report":
                    await self.handle_emergency_workflow(update, context)
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
                elif workflow == "scheme_csc_application":
                    print(f"DEBUG: Routing message to scheme_csc_application_workflow")
                    await self.handle_scheme_csc_application_workflow(update, context, message_text)
                elif workflow == "certificate_csc_application":
                    await self.handle_certificate_application_workflow(update, context, message_text)
                elif workflow == "emergency":
                    await self.handle_emergency_menu(update, context)
                elif workflow == "emergency_details":
                    # Store emergency details and request location
                    state["emergency_details"] = message_text
                    state["step"] = "location_request"
                    self._set_user_state(user_id, state)
                    
                    # Ask if user wants to share location
                    keyboard = [
                        [InlineKeyboardButton(" Share My Location", callback_data="emergency_share_location")],
                        [InlineKeyboardButton(" Enter Location Manually", callback_data="emergency_manual_location")],
                        [InlineKeyboardButton("⏭ Skip Location", callback_data="emergency_skip_location")],
                        [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        self.responses[user_lang]['complaint_location_prompt'],
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                elif workflow == "manual_location":
                    # Handle manual location input for complaint
                    state["manual_location"] = message_text
                    self._set_user_state(user_id, state)
                    
                    # Complete complaint with manual location
                    await self._complete_complaint_with_manual_location(update, context)
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
                
                # Generate human-like response using enhanced conversation system
                try:
                    user_name = update.effective_user.first_name or "Unknown"
                    logger.info(f" [CONVERSATION] Generating human-like response for user {user_id} ({user_name})")
                    logger.info(f" [CONVERSATION] Message: '{message_text}' | Intent: {intent} | Language: {user_lang}")
                    
                    human_response = await self.conversation_system.process_user_message(
                        user_id, message_text, intent, user_lang, 
                        context={"user_name": user_name}
                    )
                    
                    logger.info(f" [CONVERSATION] Bot Response: '{human_response[:100]}{'...' if len(human_response) > 100 else ''}'")
                    
                    # Send the human-like response first
                    await update.message.reply_text(human_response)
                    
                except Exception as e:
                    logger.error(f"[CONVERSATION] Error generating human-like response: {e}")
                    # Fallback to original behavior
                
                # Route based on intent
                if intent == "greeting":
                    logger.info(f" [INTENT] Handling greeting for user {user_id}")
                    await self.handle_greeting(update, context)
                elif intent == "ex_gratia":
                    logger.info(f" [INTENT] Handling ex-gratia for user {user_id}")
                    await self.handle_ex_gratia(update, context)
                elif intent == "check_status":
                    logger.info(f" [INTENT] Handling status check for user {user_id}")
                    await self.handle_check_status(update, context)
                elif intent == "relief_norms":
                    logger.info(f" [INTENT] Handling relief norms for user {user_id}")
                    await self.handle_relief_norms(update, context)
                elif intent == "emergency":
                    logger.info(f" [INTENT] Handling emergency for user {user_id}")
                    # Direct emergency response - don't show menu
                    await self.handle_emergency_direct(update, context, message_text)
                elif intent == "tourism":
                    logger.info(f" [INTENT] Handling tourism for user {user_id}")
                    await self.handle_tourism_menu(update, context)
                elif intent == "complaint":
                    logger.info(f" [INTENT] Handling complaint for user {user_id}")
                    await self.start_complaint_workflow(update, context)
                elif intent == "certificate":
                    logger.info(f" [INTENT] Handling certificate for user {user_id}")
                    # Route to certificate workflow instead of just showing info
                    await self.handle_certificate_info(update, context)
                elif intent == "csc":
                    logger.info(f" [INTENT] Handling CSC intent for user {user_id}")
                    await self.handle_csc_menu(update, context)
                elif intent == "scheme":
                    logger.info(f" [INTENT] Handling scheme for user {user_id}")
                    await self.handle_scheme_menu(update, context)
                elif intent == "cancel":
                    logger.info(f" [INTENT] Handling cancel for user {user_id}")
                    # Clear state and show main menu
                    self._clear_user_state(user_id)
                    await self.show_main_menu(update, context)
                else:
                    logger.info(f" [INTENT] Unknown intent '{intent}' for user {user_id}, showing main menu")
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
            logger.error(f" Error in message handler: {str(e)}")
            user_lang = self._get_user_language(update.effective_user.id) if update.effective_user else 'english'
            await update.message.reply_text(
                self.responses[user_lang]['error_message'],
                parse_mode='Markdown'
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
            [InlineKeyboardButton(" नेपाली (Nepali)", callback_data="lang_nepali")],
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
            
            prompt = f"""You are an intent classifier for Sajilo Sewak, a government services chatbot in Sikkim. Given the user's message, classify it into one of these intents:

Available intents:
- greeting: User is saying hello, hi, namaste, or starting a conversation (hello, hi, namaste, good morning, etc.)
- ex_gratia: User wants to APPLY for ex-gratia assistance (action-oriented)
- check_status: User wants to check status of their application
- relief_norms: User asks about relief norms, policies, eligibility criteria, or general questions about ex-gratia
- emergency: User needs emergency help (ambulance, police, fire)
- tourism: User wants tourism/homestay services
- complaint: User wants to file a complaint
- certificate: User wants to apply for certificates (apply for certificate, certificate application, birth certificate, income certificate, etc.)
- csc: User wants CSC (Common Service Center) services
- scheme: User wants to apply for government schemes (PM-KISAN, scholarships, youth schemes, health schemes, etc.)
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
- certificate: "Apply for certificate", "Apply for certificates", "Birth certificate", "Income certificate", "Document", "Certificate application"
- csc: "Find CSC", "CSC operator", "Common Service Center"
- scheme: "I want to apply for PM-KISAN", "Apply for scholarship", "Government schemes", "PM-KISAN scheme", "Youth scheme", "Health scheme", "Farmer scheme"

User message: {text}
Language: {lang}

Respond with ONLY one of the intent names listed above, nothing else."""

            logger.info(f" [LLM] Intent Classification Prompt: {prompt}")

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
                logger.info(f" [LLM] Intent Classification Response: {intent}")
                
                # Validate intent
                valid_intents = ['greeting', 'ex_gratia', 'check_status', 'relief_norms', 'emergency', 'tourism', 'complaint', 'certificate', 'csc', 'scheme', 'cancel']
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
        
        greeting_text = """ *Welcome to Sajilo Sewak!*

नमस्ते! / नमस्कार! / Hello!

Please select your preferred language to continue:

कृपया अपनी पसंदीदा भाषा चुनें:

कृपया तपाईंको मनपर्ने भाषा छान्नुहोस्:"""

        keyboard = [
            [InlineKeyboardButton(" हिंदी (Hindi)", callback_data='lang_hindi')],
            [InlineKeyboardButton(" नेपाली (Nepali)", callback_data='lang_nepali')],
            [InlineKeyboardButton(" English", callback_data='lang_english')]
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
                    "east": "Gangtok",  # East Sikkim -> Gangtok (GT)
                    "west": "Gyalshing",  # West Sikkim -> Gyalshing (GY)
                    "north": "Mangan",  # North Sikkim -> Mangan (MN)
                    "south": "Namchi",  # South Sikkim -> Namchi (NM)
                    "pakyong": "Pakyong",  # Add Pakyong (PK)
                    "soreng": "Soreng"  # Add Soreng (SR)
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
            
            elif data.startswith("relationship_"):
                relationship = data.replace("relationship_", "")
                
                # Update user state with relationship
                user_state = self._get_user_state(user_id)
                if user_state.get("workflow") == "ex_gratia":
                    user_state["data"]["relationship"] = relationship
                    
                    # Set the appropriate label and prompt
                    if relationship == "son":
                        user_state["data"]["relationship_label"] = "Father's Name"
                        prompt = " Please enter your Father's Name:"
                    elif relationship == "daughter":
                        user_state["data"]["relationship_label"] = "Father's Name"
                        prompt = " Please enter your Father's Name:"
                    elif relationship == "wife":
                        user_state["data"]["relationship_label"] = "Husband's Name"
                        prompt = " Please enter your Husband's Name:"
                    
                    user_state["step"] = "father_name"
                    self._set_user_state(user_id, user_state)
                    
                    await query.edit_message_text(prompt, parse_mode='Markdown')
            
            elif data == "emergency":
                await self.handle_emergency_menu(update, context)
            
            elif data.startswith("emergency_"):
                service = data.replace("emergency_", "")
                if service == "share_location":
                    # Request location for emergency
                    # Pass the user state to the location system
                    user_state = self._get_user_state(user_id)
                    context.user_data['user_state'] = user_state
                    await self.location_system.request_location(update, context, "emergency", "Emergency services")
                elif service == "manual_location":
                    # Handle manual location input for emergency
                    state = self._get_user_state(user_id)
                    state["step"] = "manual_location"
                    self._set_user_state(user_id, state)
                    await query.edit_message_text(" Please enter your location (e.g., Gangtok, Lachen, Namchi):")
                elif service == "skip_location":
                    # Complete emergency without location
                    await self._complete_emergency_without_location(update, context)
                elif service.startswith("health_"):
                    # Handle health emergency location selection
                    location = service.replace("health_", "")
                    await self.handle_emergency_health_location(update, context, location)
                else:
                    await self.handle_emergency_service(update, context, service)
            
            elif data.startswith("call_"):
                # Handle call button clicks
                phone_number = data.replace("call_", "")
                user_lang = self._get_user_language(user_id)
                
                # Create a message with the phone number for easy copying
                call_message = f""" **Emergency Call Information**

 **Phone Number**: `{phone_number}`

 **To call this number**:
1. Copy the number above
2. Open your phone app
3. Paste and dial the number

 **Emergency Response**: Help is on the way!

 **Important**: Stay calm and provide clear information about your emergency."""
                
                # Create keyboard with copy button and back options
                keyboard = [
                    [InlineKeyboardButton(" Back to Emergency", callback_data="emergency")],
                    [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(call_message, reply_markup=reply_markup, parse_mode='Markdown')
                
                # Log the call attempt
                user_name = update.effective_user.first_name or "Unknown"
                self._log_to_sheets(
                    user_id=user_id,
                    user_name=user_name,
                    interaction_type="emergency_call",
                    query_text=f"Call button clicked for {phone_number}",
                    language=user_lang,
                    bot_response=f"Call information provided for {phone_number}",
                    phone_number=phone_number
                )
            
            elif data == "csc":
                await self.handle_csc_menu(update, context)
            
            elif data == "csc_submit_application":
                print(f"DEBUG: csc_submit_application callback triggered")
                await self.handle_csc_submit_application(update, context)
            
            elif data == "certificate":
                await self.handle_certificate_info(update, context)
            
            # Certificate type handlers - MUST come before generic csc_ handler
            elif data.startswith("cert_type_"):
                print(f"DEBUG: cert_type_ callback triggered: {data}")
                try:
                    cert_type = data.replace("cert_type_", "").upper()
                    print(f"DEBUG: Extracted cert_type: {cert_type}")
                    await self.handle_certificate_type_selection(update, context, cert_type)
                    print(f"DEBUG: handle_certificate_type_selection completed successfully")
                except Exception as e:
                    print(f"DEBUG: Error in cert_type_ handler: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Certificate workflow handlers - MUST BE BEFORE generic cert_ handler
            elif data.startswith("cert_block_"):
                print(f"DEBUG: cert_block_ callback triggered: {data}")
                block_index = data.replace("cert_block_", "")
                print(f"DEBUG: Extracted block_index: {block_index}")
                print(f"DEBUG: About to call handle_certificate_block_selection")
                await self.handle_certificate_block_selection(update, context, block_index)
                print(f"DEBUG: handle_certificate_block_selection completed")
            
            elif data.startswith("cert_gpu_"):
                gpu_index = data.replace("cert_gpu_", "")
                await self.handle_certificate_gpu_selection(update, context, gpu_index)
            
            elif data == "cert_apply_now":
                await self.handle_certificate_apply_now(update, context)
            
            elif data.startswith("cert_"):
                cert_type = data.replace("cert_", "")
                await self.handle_certificate_choice(update, context, cert_type)
            
            # CSC Contacts workflow handlers - MUST BE BEFORE generic csc_ handler
            elif data.startswith("csc_block_"):
                try:
                    print(f" [DEBUG] ENTERING csc_block_ handler with data: {data}")
                    block_index = data.replace("csc_block_", "")
                    print(f" [DEBUG] About to call simple_csc_block_to_gpu with block_index: {block_index}")
                    await self.simple_csc_block_to_gpu(update, context, block_index)
                    print(f" [DEBUG] simple_csc_block_to_gpu completed successfully")
                except Exception as e:
                    print(f" [DEBUG] Exception in csc_block_ handler: {e}")
                    import traceback
                    traceback.print_exc()
                    await update.callback_query.answer("Error occurred. Please try again.")
            
            elif data.startswith("csc_gpu_"):
                try:
                    print(f" [DEBUG] ENTERING csc_gpu_ handler with data: {data}")
                    gpu_index = data.replace("csc_gpu_", "")
                    print(f" [DEBUG] About to call handle_csc_gpu_selection with gpu_index: {gpu_index}")
                    await self.handle_csc_gpu_selection(update, context, gpu_index)
                    print(f" [DEBUG] handle_csc_gpu_selection completed successfully")
                except Exception as e:
                    print(f" [DEBUG] Exception in csc_gpu_ handler: {e}")
                    import traceback
                    traceback.print_exc()
                    await update.callback_query.answer("Error occurred. Please try again.")
            
            elif data.startswith("csc_"):
                # This is handled by the new CSC functionality in contacts
                await update.callback_query.answer("Please use the 'Know Key Contact' option for CSC services")
                return
            
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
                        
                        keyboard = [[InlineKeyboardButton(" Cancel", callback_data="main_menu")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                elif complaint_type == "share_location":
                    # Request location for complaint
                    # Pass the user state to the location system
                    user_state = self._get_user_state(user_id)
                    context.user_data['user_state'] = user_state
                    await self.location_system.request_location(update, context, "complaint", "Complaint filing")
                elif complaint_type == "manual_location":
                    # Handle manual location input
                    state = self._get_user_state(user_id)
                    state["step"] = "manual_location"
                    self._set_user_state(user_id, state)
                    await query.edit_message_text(" Please enter your location (e.g., Gangtok, Lachen, Namchi):")
                elif complaint_type == "skip_location":
                    # Complete complaint without location
                    await self._complete_complaint_without_location(update, context)
            
            elif data == "certificate_csc":
                # Handle certificate CSC choice - show certificate types
                user_id = update.effective_user.id
                user_lang = self._get_user_language(user_id)
                
                text = f""" **Select Certificate Type**

Please select the certificate you want to apply for:

**You can apply online at sso.sikkim.gov.in (Apply online)**
**or**
**Apply through your nearest CSC (Common Service Centre).**"""

                keyboard = [
                    [InlineKeyboardButton(" SC Certificate", callback_data="cert_type_sc")],
                    [InlineKeyboardButton(" ST Certificate", callback_data="cert_type_st")],
                    [InlineKeyboardButton(" OBC Certificate", callback_data="cert_type_obc")],
                    [InlineKeyboardButton(" Income Certificate", callback_data="cert_type_income")],
                    [InlineKeyboardButton(" Employment Card", callback_data="cert_type_employment")],
                    [InlineKeyboardButton(" Primitive Tribe Certificate", callback_data="cert_type_primitive")],
                    [InlineKeyboardButton(" Back", callback_data="certificate_info")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            elif data == "certificate_sso":
                # Handle certificate SSO choice
                user_id = update.effective_user.id
                user_lang = self._get_user_language(user_id)
                sso_message = self.responses[user_lang]['certificate_sso_message']
                back_button = self.responses[user_lang]['back_main_menu']
                await query.edit_message_text(
                    f"{sso_message}\n\n {back_button}", 
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(back_button, callback_data="main_menu")]]),
                    parse_mode='Markdown'
                )
            

            
            # Certificate application choice handlers - REMOVED (going directly to block selection)
            
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
            
            # Scheme category handlers
            elif data == "scheme_category_farmer":
                await self.handle_scheme_category_farmer(update, context)
            
            elif data == "scheme_category_student":
                await self.handle_scheme_category_student(update, context)
            
            elif data == "scheme_category_youth":
                await self.handle_scheme_category_youth(update, context)
            
            elif data == "scheme_category_health":
                await self.handle_scheme_category_health(update, context)
            
            elif data == "scheme_category_other":
                await self.handle_scheme_category_other(update, context)
            
            # Individual scheme handlers
            elif data == "scheme_pmkisan":
                await self.handle_scheme_pmkisan(update, context)
            
            elif data == "scheme_pmfasal":
                await self.handle_scheme_pmfasal(update, context)
            
            elif data == "scheme_scholarships":
                await self.handle_scheme_scholarships(update, context)
            
            elif data == "scheme_sikkim_mentor":
                await self.handle_scheme_sikkim_mentor(update, context)
            
            elif data == "scheme_sikkim_youth":
                await self.handle_scheme_sikkim_youth(update, context)
            
            elif data == "scheme_pmegp":
                await self.handle_scheme_pmegp(update, context)
            
            elif data == "scheme_pmfme":
                await self.handle_scheme_pmfme(update, context)
            
            elif data == "scheme_ayushman":
                await self.handle_scheme_ayushman(update, context)
            
            # Scheme application handlers
            elif data.startswith("scheme_apply_online_"):
                scheme_name = data.replace("scheme_apply_online_", "").replace("_", " ").title()
                # Handle online application - show website links
                await self.handle_scheme_apply_online(update, context, scheme_name)
            
            elif data.startswith("scheme_apply_csc_"):
                scheme_name = data.replace("scheme_apply_csc_", "").replace("_", " ").title()
                # Start CSC application process
                await self.handle_scheme_csc_application(update, context, scheme_name)
            
            # CSC Application workflow callbacks
            elif data.startswith("scheme_csc_block_"):
                block_index = data.replace("scheme_csc_block_", "")
                await self.handle_csc_block_selection(update, context, block_index)
            

            
            elif data.startswith("scheme_csc_gpu_"):
                gpu_index = data.replace("scheme_csc_gpu_", "")
                await self.handle_csc_gpu_selection(update, context, gpu_index)
            
            elif data == "scheme_csc_back_to_blocks":
                # Go back to block selection
                user_id = update.effective_user.id
                state = self._get_user_state(user_id)
                if state.get("workflow") == "scheme_csc_application":
                    scheme_name = state.get("scheme", "Unknown Scheme")
                    await self.handle_scheme_csc_application(update, context, scheme_name)
            
            # Handle old back button pattern for backward compatibility
            elif data == "csc_back_to_blocks":
                # Go back to block selection
                user_id = update.effective_user.id
                state = self._get_user_state(user_id)
                if state.get("workflow") == "scheme_csc_application":
                    scheme_name = state.get("scheme", "Unknown Scheme")
                    await self.handle_scheme_csc_application(update, context, scheme_name)
                else:
                    # If not in scheme workflow, go back to main menu
                    await self.show_main_menu(update, context)
            
            elif data.startswith("csc_back_to_gpus_"):
                # This handler is deprecated - use csc_back_to_blocks instead
                await update.callback_query.answer("Please use the Back to Blocks button")
            
            elif data == "contacts":
                await self.handle_contacts_menu(update, context)
            
            elif data == "contacts_csc":
                await self.handle_contacts_csc_menu(update, context)
            
            elif data == "csc_search_retry":
                # Handle CSC search retry
                user_id = update.effective_user.id
                user_lang = self._get_user_language(user_id)
                state = self._get_user_state(user_id)
                
                # Get the last search term if available
                last_search = state.get("last_search", "")
                
                retry_message = f""" **CSC Search - Try Again**

Please enter your GPU name, ward name, or constituency name to search for CSC operators.

**Examples:**
• GPU: "Karzi Mangnam GP"
• Ward: "Mangder", "Tashiding"
• Constituency: "KARZI MANGNAM"

{f"**Last search:** {last_search}" if last_search else ""}"""
                
                keyboard = [
                    [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(retry_message, reply_markup=reply_markup, parse_mode='Markdown')
            
            elif data == "certificate_retry":
                # Handle certificate retry
                user_id = update.effective_user.id
                user_lang = self._get_user_language(user_id)
                state = self._get_user_state(user_id)
                
                # Get the last GPU if available
                last_gpu = state.get("last_gpu", "")
                
                retry_message = f""" **Certificate Search - Try Again**

Please enter your GPU (Gram Panchayat Unit) name to find the CSC operator.

**Examples:**
• "Karzi Mangnam GP"
• "Gangtok Municipal Corporation"
• "Namchi Municipal Council"

{f"**Last search:** {last_gpu}" if last_gpu else ""}"""
                
                keyboard = [
                    [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(retry_message, reply_markup=reply_markup, parse_mode='Markdown')
            
            elif data == "contacts_blo":
                await self.handle_blo_search(update, context)
            
            elif data == "contacts_aadhar":
                await self.handle_aadhar_services(update, context)
            
            elif data.startswith("contacts_csc_gpu_"):
                gpu_index = data.replace("contacts_csc_gpu_", "")
                await self.handle_csc_contacts_gpu_selection(update, context, gpu_index)
            
            elif data.startswith("blo_constituency_"):
                constituency_index = data.replace("blo_constituency_", "")
                await self.handle_blo_constituency_selection(update, context, constituency_index)
            
            elif data.startswith("blo_booth_"):
                booth_index = data.replace("blo_booth_", "")
                await self.handle_blo_booth_selection(update, context, booth_index)
            
            elif data.startswith("call_blo_"):
                phone = data.replace("call_blo_", "")
                await update.callback_query.answer(f"Calling BLO at {phone}")
                # In a real implementation, this could initiate a call or show contact info
            
            elif data.startswith("call_csc_"):
                phone = data.replace("call_csc_", "")
                await update.callback_query.answer(f"Calling CSC Operator at {phone}")
                # In a real implementation, this could initiate a call or show contact info
            
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
            [InlineKeyboardButton(" Apply for Ex-gratia", callback_data="ex_gratia")],
            [InlineKeyboardButton(" Check Application Status", callback_data="check_status")],
            [InlineKeyboardButton("ℹ View Relief Norms", callback_data="relief_norms")],
            [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Disaster Management Services* 

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
        
        text = """*Check Application Status* 

Please enter your NC Exgratia Application Reference Number.

**Format:** SK2025XXXXXXX
**Example:** SK2025MN0002

**How to find your reference number:**
• Check your SMS after application submission
• Look for format: SK2025 + District Code + Number
• District codes: MN (Mangan), GT (Gangtok), etc.

**Note:** This will check the real-time status from the NIC server."""

        keyboard = [[InlineKeyboardButton(" Cancel", callback_data="disaster")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def process_status_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process application status check for ex-gratia, scheme, and certificate applications"""
        reference_number = update.message.text.strip().upper()
        
        # Check if it's an ex-gratia reference number (format: SK2025MN0002)
        if reference_number.startswith("SK") and len(reference_number) == 12 and reference_number[6:8] in ["MN", "PK", "GN", "SN"]:
            # Ex-gratia application - use NIC API
            await self.check_nc_exgratia_status(update, context, reference_number)
        elif reference_number.startswith("CERT"):
            # Certificate application - check Google Sheets
            await self.check_certificate_application_status(update, context, reference_number)
        else:
            # Scheme application - check Google Sheets
            await self.check_scheme_application_status(update, context, reference_number)
        
        # Clear the workflow state
        self._clear_user_state(update.effective_user.id)

    async def check_scheme_application_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, reference_number: str):
        """Check scheme application status from Google Sheets"""
        try:
            # Get the Google Sheets service
            service = self.sheets_service
            if not service:
                await update.message.reply_text(" **Error:** Unable to access application database. Please try again later.", parse_mode='Markdown')
                return
            
            # Search for the application in Google Sheets
            spreadsheet_id = self.config['GOOGLE_SHEETS']['SPREADSHEET_ID']
            range_name = 'Scheme_Applications!A:Z'  # Look in the dedicated scheme applications sheet
            
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # Search for the reference number
            application_data = None
            for row in values:
                if len(row) > 11 and row[11] == reference_number:  # Reference number is in column L (index 11)
                    application_data = row
                    break
            
            if application_data:
                # Extract application details based on new sheet structure
                scheme_name = application_data[3] if len(application_data) > 3 else "Unknown"  # Column D
                applicant_name = application_data[4] if len(application_data) > 4 else "Unknown"  # Column E
                phone = application_data[6] if len(application_data) > 6 else "Unknown"  # Column G
                gpu = application_data[9] if len(application_data) > 9 else "Unknown"  # Column J
                block = application_data[10] if len(application_data) > 10 else "Unknown"  # Column K
                status = application_data[12] if len(application_data) > 12 else "Submitted"  # Column M
                submission_date = application_data[13] if len(application_data) > 13 else "Unknown"  # Column N
                
                # Create status message
                status_emoji = {
                    "Submitted": "",
                    "Under Review": "",
                    "Approved": "",
                    "Rejected": "",
                    "In Progress": "⏳",
                    "Completed": ""
                }.get(status, "")
                
                text = f""" **Application Status**

**Reference Number:** `{reference_number}`
**Scheme:** {scheme_name}
**Applicant:** {applicant_name}
**Phone:** {phone}
**GPU:** {gpu}
**Block:** {block}
**Submission Date:** {submission_date}

{status_emoji} **Status:** {status}

**Next Steps:**
• CSC operator will contact you for verification
• Visit the CSC center with required documents
• Keep this reference number for future updates

**Need Help?** Contact your CSC operator using the 'Important Contacts' section."""
                
                keyboard = [
                    [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")],
                    [InlineKeyboardButton(" Contact CSC", callback_data="contacts")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                
            else:
                # Application not found
                text = f""" **Application Not Found**

**Reference Number:** `{reference_number}`

Sorry, we couldn't find an application with this reference number.

**Possible reasons:**
• Reference number is incorrect
• Application was submitted recently and not yet processed
• Application was submitted through a different channel

**Please check:**
• Verify the reference number is correct
• Try again in a few minutes if recently submitted
• Contact support if the issue persists"""
                
                keyboard = [
                    [InlineKeyboardButton(" Try Again", callback_data="check_status")],
                    [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error checking scheme application status: {str(e)}")
            await update.message.reply_text(" **Error:** Unable to check application status. Please try again later.", parse_mode='Markdown')
    
    async def check_certificate_application_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, reference_number: str):
        """Check certificate application status from Google Sheets"""
        try:
            # Get Google Sheets service
            service = self.sheets_service.service
            if not service:
                await update.message.reply_text(" **Error:** Google Sheets service not available.", parse_mode='Markdown')
                return
            
            # Search for the application in Google Sheets
            spreadsheet_id = self.config['GOOGLE_SHEETS']['SPREADSHEET_ID']
            range_name = 'Certificate_Applications!A:Z'  # Look in the dedicated certificate applications sheet
            
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                await update.message.reply_text(" **Error:** No certificate applications found.", parse_mode='Markdown')
                return
            
            # Search for the reference number
            application_data = None
            for row in values:
                if len(row) > 10 and row[10] == reference_number:  # Reference number is in column K (index 10)
                    application_data = row
                    break
            
            if application_data:
                # Extract application details based on new sheet structure
                certificate_type = application_data[3] if len(application_data) > 3 else "Unknown"  # Column D
                applicant_name = application_data[4] if len(application_data) > 4 else "Unknown"  # Column E
                phone = application_data[6] if len(application_data) > 6 else "Unknown"  # Column G
                gpu = application_data[8] if len(application_data) > 8 else "Unknown"  # Column I
                block = application_data[9] if len(application_data) > 9 else "Unknown"  # Column J
                status = application_data[11] if len(application_data) > 11 else "Submitted"  # Column L
                submission_date = application_data[12] if len(application_data) > 12 else "Unknown"  # Column M
                
                # Create status message
                text = f""" **Certificate Application Status**

**Reference Number:** `{reference_number}`
**Certificate Type:** {certificate_type}
**Applicant Name:** {applicant_name}
**Phone:** {phone}
**Block:** {block}
**GPU:** {gpu}

** Current Status:** {status}
** Submitted On:** {submission_date}

** Next Steps:**
• CSC operator will contact you within 24-48 hours
• Keep your reference number safe for tracking
• Contact your block office if no response within 48 hours

** Status Updates:**
CSC operators update status in our system. Check back later for updates."""
                
                keyboard = [[InlineKeyboardButton(" Main Menu", callback_data="main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                text = f""" **Application Not Found**

**Reference Number:** `{reference_number}`

This reference number was not found in our certificate applications database.

**Possible reasons:**
• Reference number is incorrect
• Application was submitted recently (may take a few minutes to appear)
• Application was submitted through a different channel

** What to do:**
• Double-check your reference number
• Try again in a few minutes
• Contact support if the issue persists"""
                
                keyboard = [[InlineKeyboardButton(" Main Menu", callback_data="main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error checking certificate application status: {str(e)}")
            await update.message.reply_text(" **Error:** Unable to check application status. Please try again later.", parse_mode='Markdown')

    async def handle_ex_gratia(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle ex-gratia application"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        text = f"*Ex-Gratia Assistance* \n\n{self.responses[user_lang]['ex_gratia_intro']}"

        keyboard = [
            [InlineKeyboardButton(" Yes, Continue", callback_data="ex_gratia_start")],
            [InlineKeyboardButton(" No, Go Back", callback_data="disaster")]
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
        
        text = f"*Ex-Gratia Application Form* \n\n{self.responses[user_lang]['ex_gratia_form']}"
        
        keyboard = [[InlineKeyboardButton(" Cancel", callback_data="disaster")]]
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
            state["step"] = "relationship"
            state["data"] = data
            self._set_user_state(user_id, state)
            
            # Show relationship options
            keyboard = [
                [InlineKeyboardButton(" Son of (S/O)", callback_data="relationship_son")],
                [InlineKeyboardButton(" Daughter of (D/O)", callback_data="relationship_daughter")],
                [InlineKeyboardButton(" Wife of (W/O)", callback_data="relationship_wife")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("‍‍‍ Please select your relationship:", reply_markup=reply_markup, parse_mode='Markdown')

        elif step == "relationship":
            # Store the relationship type
            data["relationship"] = text
            if text == "son":
                data["relationship_label"] = "Father's Name"
                prompt = " Please enter your Father's Name:"
            elif text == "daughter":
                data["relationship_label"] = "Father's Name"
                prompt = " Please enter your Father's Name:"
            elif text == "wife":
                data["relationship_label"] = "Husband's Name"
                prompt = " Please enter your Husband's Name:"
            
            state["step"] = "father_name"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text(prompt, parse_mode='Markdown')

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
            await update.message.reply_text(" Please enter your Voter ID number:", parse_mode='Markdown')

        elif step == "voter_id":
            # Validate voter ID - minimum 5 characters
            if len(text.strip()) < 5:
                await update.message.reply_text(" Voter ID must be at least 5 characters long. Please enter a valid Voter ID:", parse_mode='Markdown')
                return
            
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
            
            # Show district options - Updated with correct Sikkim district names
            keyboard = [
                [InlineKeyboardButton("Gangtok (East Sikkim)", callback_data="district_east")],
                [InlineKeyboardButton("Gyalshing (West Sikkim)", callback_data="district_west")],
                [InlineKeyboardButton("Mangan (North Sikkim)", callback_data="district_north")],
                [InlineKeyboardButton("Namchi (South Sikkim)", callback_data="district_south")],
                [InlineKeyboardButton("Pakyong", callback_data="district_pakyong")],
                [InlineKeyboardButton("Soreng", callback_data="district_soreng")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(" Please select your district:", reply_markup=reply_markup, parse_mode='Markdown')

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
            await update.message.reply_text(" When did the natural calamity occur? (DD/MM/YYYY HH:MM)\n\nExample: 15/10/2023 14:30", parse_mode='Markdown')

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
                await update.message.reply_text(" Please enter the date and time in the correct format.\n\nExample: 15/10/2023 14:30", parse_mode='Markdown')
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
            await self.location_system.request_location(update, context, "ex_gratia")

        else:
            await update.message.reply_text(self.responses[user_lang]['error'], parse_mode='Markdown')
            self._clear_user_state(user_id)

    async def show_damage_type_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton(" House Damage (₹4,000 - ₹25,000)", callback_data='damage_type_house')],
            [InlineKeyboardButton(" Crop Loss (₹4,000 - ₹15,000)", callback_data='damage_type_crop')],
            [InlineKeyboardButton(" Livestock Loss (₹2,000 - ₹15,000)", callback_data='damage_type_livestock')],
            [InlineKeyboardButton(" Land Damage (₹4,000 - ₹20,000)", callback_data='damage_type_land')]
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
            'house': ' House Damage',
            'crop': ' Crop Loss',
            'livestock': ' Livestock Loss',
            'land': ' Land Damage'
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
        
        # Get relationship information
        relationship_info = ""
        if data.get('relationship'):
            if data['relationship'] == 'son':
                relationship_info = f" **Son of**: {data.get('father_name', 'N/A')}"
            elif data['relationship'] == 'daughter':
                relationship_info = f" **Daughter of**: {data.get('father_name', 'N/A')}"
            elif data['relationship'] == 'wife':
                relationship_info = f" **Wife of**: {data.get('father_name', 'N/A')}"
        else:
            relationship_info = f"‍ **Father's Name**: {data.get('father_name', 'N/A')}"

        summary = f"""*Please Review Your NC Exgratia Application* 

*Personal Details:*
 **Name**: {data.get('name', 'N/A')}
{relationship_info}
 **Voter ID**: {data.get('voter_id', 'N/A')}
 **Contact**: {data.get('contact', 'N/A')}

*Address Details:*
 **Village**: {data.get('village', 'N/A')}
 **Ward**: {data.get('ward', 'N/A')}
 **GPU**: {data.get('gpu', 'N/A')}
 **District**: {data.get('district', 'N/A')}

*Land Details:*
 **Khatiyan Number**: {data.get('khatiyan_no', 'N/A')}
 **Plot Number**: {data.get('plot_no', 'N/A')}

*Incident Details:*
 **Date & Time**: {datetime_display}
 **Damage Type**: {data.get('damage_type', 'N/A')}
 **Description**: {data.get('damage_description', 'N/A')}

*Location:*
 **Coordinates**: {location_display}

Please verify all details carefully. Would you like to:"""
        
        keyboard = [
            [InlineKeyboardButton(" Submit to NC Exgratia API", callback_data='ex_gratia_submit')],
            [InlineKeyboardButton(" Edit Details", callback_data='ex_gratia_edit')],
            [InlineKeyboardButton(" Cancel", callback_data='ex_gratia_cancel')]
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
                error_msg = " NC Exgratia API is not configured. Please contact support."
                if update.callback_query:
                    await update.callback_query.edit_message_text(error_msg, parse_mode='Markdown')
                else:
                    await update.message.reply_text(error_msg, parse_mode='Markdown')
                return

            # Show processing message
            processing_msg = " Submitting your application to NC Exgratia API...\n\nPlease wait while we process your request."
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
                confirmation = f""" *NC Exgratia Application Submitted Successfully!*

 **Reference Number**: `{reference_number}`
 **Applicant**: {data.get('name')}
 **Submitted**: {now.strftime('%d/%m/%Y %H:%M')}
 **Status**: {api_status}

*Important Information:*
• Save this reference number: `{reference_number}`
• Check status anytime: `/status {reference_number}`
• Contact support if needed: {Config.SUPPORT_PHONE}

*Next Steps:*
1. Your application will be reviewed by officials
2. You'll receive updates via SMS
3. Processing time: 7-10 working days

Thank you for using NC Exgratia service! """

                keyboard = [
                    [InlineKeyboardButton(" Check Status", callback_data=f"check_status_{reference_number}")],
                    [InlineKeyboardButton(" Back to Disaster Management", callback_data="disaster")]
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
                error_type = api_result.get("error", "Unknown error")
                retry_attempts = api_result.get("retry_attempts", 0)
                logger.error(f" NC Exgratia API submission failed: {error_details}")
                
                # Check if this is a server-wide outage
                if "NIC API Server Outage" in error_type:
                    error_msg = f""" *NIC API Server Outage Detected*

The NIC API server is currently experiencing a major outage.

*What happened:*
• Your application was retried {retry_attempts} times
• All attempts failed due to server-side issues
• This is a server-wide outage affecting all districts

*What to do:*
1. **Try again later** - The server may be restored soon
2. **Contact support** - {Config.SUPPORT_PHONE}
3. **Alternative**: Visit your nearest CSC center for manual submission

*Your data is safe:*
 All your information has been saved locally
 You can retry when the server is back online

*Support Contact:*
 {Config.SUPPORT_PHONE}
 Visit nearest CSC center

*Status:*
 NIC API Server: **DOWN**
 All ex-gratia submissions: **TEMPORARILY UNAVAILABLE**"""
                # Check if this is a PK district specific issue
                elif "PK District API Issue" in error_type:
                    error_msg = f""" *PK District API Issue Detected*

The NIC API is currently experiencing issues with PK district submissions.

*What happened:*
• Your application was retried {retry_attempts} times
• All attempts failed due to server-side issues
• This is a known issue with the NIC API

*What to do:*
1. **Try again later** - The issue may be temporary
2. **Contact support** - {Config.SUPPORT_PHONE}
3. **Alternative**: Visit your nearest CSC center for manual submission

*Your data is safe:*
 All your information has been saved locally
 You can retry when the API is working again

*Support Contact:*
 {Config.SUPPORT_PHONE}
 Visit nearest CSC center"""
                else:
                    error_msg = f""" *Application Submission Failed*

The NC Exgratia API returned an error. Please try again later.

*Error Details:*
{error_details}

*What to do:*
1. Check your internet connection
2. Try again in a few minutes
3. Contact support if the problem persists: {Config.SUPPORT_PHONE}

Your data has been saved locally and will be retried."""
                
                keyboard = [[InlineKeyboardButton(" Try Again", callback_data='ex_gratia_submit')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if update.callback_query:
                    await update.callback_query.edit_message_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await update.message.reply_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Clear user state
            self._clear_user_state(user_id)
            
        except Exception as e:
            logger.error(f" Error submitting application: {str(e)}")
            error_msg = f""" *Application Submission Error*

An unexpected error occurred. Please try again.

*Error:*
{str(e)}

Contact support: {Config.SUPPORT_PHONE}"""
            
            keyboard = [[InlineKeyboardButton(" Try Again", callback_data='ex_gratia_submit')]]
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
            [InlineKeyboardButton(" Name", callback_data="edit_name")],
            [InlineKeyboardButton("‍ Father's Name", callback_data="edit_father")],
            [InlineKeyboardButton(" Village", callback_data="edit_village")],
            [InlineKeyboardButton(" Contact", callback_data="edit_contact")],
            [InlineKeyboardButton(" Ward", callback_data="edit_ward")],
            [InlineKeyboardButton(" GPU", callback_data="edit_gpu")],
            [InlineKeyboardButton(" Khatiyan Number", callback_data="edit_khatiyan")],
            [InlineKeyboardButton(" Plot Number", callback_data="edit_plot")],
            [InlineKeyboardButton(" Damage Description", callback_data="edit_damage")],
            [InlineKeyboardButton(" Done Editing", callback_data="edit_done")],
            [InlineKeyboardButton(" Cancel", callback_data="ex_gratia_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Which information would you like to edit?* 

Select the field you want to update:"""
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # --- Emergency Services ---
    async def handle_emergency_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle emergency services menu - first request location, then show emergency options"""
        user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
        user_lang = self._get_user_language(user_id)
        
        # Set emergency workflow state
        state = self._get_user_state(user_id)
        state["workflow"] = "emergency"
        state["step"] = "location"
        self._set_user_state(user_id, state)
        
        # Request location first
        location_text = """ **Emergency Services** 

 **Location Required for Emergency Response**

To provide you with the most accurate emergency assistance, we need your current location.

**Please share your location:**"""
        
        keyboard = [
            [InlineKeyboardButton(" Share My Location", callback_data="emergency_share_location")],
            [InlineKeyboardButton(" Enter Location Manually", callback_data="emergency_manual_location")],
            [InlineKeyboardButton("⏭ Skip Location", callback_data="emergency_skip_location")],
            [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(location_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(location_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Log to Google Sheets
        user_name = (update.effective_user.first_name if update.effective_user else update.callback_query.from_user.first_name) or "Unknown"
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="emergency",
            query_text="Emergency services menu accessed",
            language=user_lang,
            bot_response="Emergency location request shown",
            emergency_type="location_request"
        )

    async def show_emergency_services_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show emergency services menu after location is collected"""
        user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
        user_lang = self._get_user_language(user_id)
        
        # Get user state to check if location was collected
        state = self._get_user_state(user_id)
        location_info = state.get("location", "Location not provided")
        
        # Show comprehensive emergency services menu
        emergency_text = f""" **Emergency Services** 

 **Your Location:** {location_info}

Please select the type of emergency you need help with:

 **Fire**
 **Ambulance** 
 **Health Emergency**
 **Police Helpline**
 **Mental Health Helpline**
 **District Control Room**
‍ **Women/Child Helpline**
 **Tourism Assistance**

Select an option below:"""
        
        keyboard = [
            [InlineKeyboardButton(" Fire", callback_data="emergency_fire")],
            [InlineKeyboardButton(" Ambulance", callback_data="emergency_ambulance")],
            [InlineKeyboardButton(" Health Emergency", callback_data="emergency_health")],
            [InlineKeyboardButton(" Police Helpline", callback_data="emergency_police")],
            [InlineKeyboardButton(" Mental Health Helpline", callback_data="emergency_mental_health")],
            [InlineKeyboardButton(" District Control Room", callback_data="emergency_control_room")],
            [InlineKeyboardButton("‍ Women/Child Helpline", callback_data="emergency_women_child")],
            [InlineKeyboardButton(" Tourism Assistance", callback_data="emergency_tourism")],
            [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(emergency_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(emergency_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Log to Google Sheets
        user_name = (update.effective_user.first_name if update.effective_user else update.callback_query.from_user.first_name) or "Unknown"
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="emergency",
            query_text="Emergency services menu shown after location",
            language=user_lang,
            bot_response="Emergency menu shown",
            emergency_type="menu",
            location=location_info
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
                # Create clickable call buttons for ambulance
                keyboard = [
                    [InlineKeyboardButton(" Call Ambulance (102)", callback_data="call_102")],
                    [InlineKeyboardButton(" Call Ambulance (108)", callback_data="call_108")],
                    [InlineKeyboardButton(" Control Room", callback_data="call_03592202033")],
                    [InlineKeyboardButton(" Share Location for Dispatch", callback_data="emergency_share_location")],
                    [InlineKeyboardButton(self.responses[user_lang]['other_emergency'], callback_data="emergency")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
            elif any(word in message_lower for word in ['police', 'police', 'thief', 'robbery', 'crime']):
                service_type = 'police'
                response_text = self.responses[user_lang]['emergency_police']
                # Create clickable call buttons for police
                keyboard = [
                    [InlineKeyboardButton(" Call Police (100)", callback_data="call_100")],
                    [InlineKeyboardButton(" Control Room", callback_data="call_03592202022")],
                    [InlineKeyboardButton(" Share Location for Dispatch", callback_data="emergency_share_location")],
                    [InlineKeyboardButton(self.responses[user_lang]['other_emergency'], callback_data="emergency")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
            elif any(word in message_lower for word in ['fire', 'fire', 'burning', 'blaze']):
                service_type = 'fire'
                response_text = self.responses[user_lang]['emergency_fire']
                # Create clickable call buttons for fire
                keyboard = [
                    [InlineKeyboardButton(" Call Fire (101)", callback_data="call_101")],
                    [InlineKeyboardButton(" Control Room", callback_data="call_03592202099")],
                    [InlineKeyboardButton(" Share Location for Dispatch", callback_data="emergency_share_location")],
                    [InlineKeyboardButton(self.responses[user_lang]['other_emergency'], callback_data="emergency")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
            elif any(word in message_lower for word in ['suicide', 'suicide', 'helpline']):
                service_type = 'suicide'
                response_text = self.responses[user_lang]['emergency_suicide']
                # Create clickable call buttons for suicide helpline
                keyboard = [
                    [InlineKeyboardButton(" Call Suicide Helpline", callback_data="call_9152987821")],
                    [InlineKeyboardButton(" Share Location for Support", callback_data="emergency_share_location")],
                    [InlineKeyboardButton(self.responses[user_lang]['other_emergency'], callback_data="emergency")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
            elif any(word in message_lower for word in ['women', 'women', 'harassment']):
                service_type = 'women'
                response_text = self.responses[user_lang]['emergency_women']
                # Create clickable call buttons for women helpline
                keyboard = [
                    [InlineKeyboardButton(" Call Women Helpline (1091)", callback_data="call_1091")],
                    [InlineKeyboardButton(" State Commission", callback_data="call_03592205607")],
                    [InlineKeyboardButton(" Share Location for Support", callback_data="emergency_share_location")],
                    [InlineKeyboardButton(self.responses[user_lang]['other_emergency'], callback_data="emergency")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
            else:
                # Default to ambulance for general emergency
                service_type = 'ambulance'
                response_text = self.responses[user_lang]['emergency_ambulance']
                keyboard = [
                    [InlineKeyboardButton(" Call Ambulance (102)", callback_data="call_102")],
                    [InlineKeyboardButton(" Call Ambulance (108)", callback_data="call_108")],
                    [InlineKeyboardButton(" Share Location for Dispatch", callback_data="emergency_share_location")],
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
        """Handle comprehensive emergency service selection"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Store emergency type
        state = self._get_user_state(user_id)
        state["emergency_type"] = service_type
        self._set_user_state(user_id, state)
        
        if service_type == "fire":
            response_text = """ **FIRE EMERGENCY**

**Fire Helpline:** 101
**Gyalshing Fire Station:** 03595-257372

Call immediately in case of any fire incident. Avoid elevators and stay low under smoke.

**Emergency Instructions:**
• Call 101 immediately
• Evacuate the building
• Use stairs, not elevators
• Stay low under smoke
• Meet at designated assembly point"""
            
            keyboard = [
                [InlineKeyboardButton(" Call Fire (101)", callback_data="call_101")],
                [InlineKeyboardButton(" Gyalshing Fire Station", callback_data="call_03595257372")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        elif service_type == "ambulance":
            response_text = """ **AMBULANCE SERVICES**

**Emergency Ambulance Numbers:** 102, 103, 108, 03595-250823

**District Hospital Ambulance Drivers:**
• Raj Kr Chettri – 96478-80775
• Ganesh Subedi – 99326-27198
• Rajesh Gurung – 97334-73753
• Bikram Rai – 74785-83708

**PHC Ambulance Services:**
• **Dentam PHC (102):** Uttam Basnett – 77973-79779
• **Yuksom PHC (102):** Prem Gurung – 74793-56022
• **Tashiding PHC:** Chogyal Tshering Bhutia – 95933-76420

**For immediate medical emergency, call 102 or 108**"""
            
            keyboard = [
                [InlineKeyboardButton(" Call Ambulance (102)", callback_data="call_102")],
                [InlineKeyboardButton(" Call Ambulance (108)", callback_data="call_108")],
                [InlineKeyboardButton(" District Hospital", callback_data="call_03595250823")],
                [InlineKeyboardButton(" Health Emergency Details", callback_data="emergency_health")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        elif service_type == "health":
            response_text = """ **HEALTH RELATED SERVICES**

Please select your location to get the right health emergency contact:

**Available Locations:**
• District Hospital (Gyalshing HQ)
• Yuksom PHC
• Dentam PHC
• Tashiding PHC

Select your location for specific contact details:"""
            
            keyboard = [
                [InlineKeyboardButton(" District Hospital (Gyalshing HQ)", callback_data="emergency_health_district")],
                [InlineKeyboardButton(" Yuksom PHC", callback_data="emergency_health_yuksom")],
                [InlineKeyboardButton(" Dentam PHC", callback_data="emergency_health_dentam")],
                [InlineKeyboardButton(" Tashiding PHC", callback_data="emergency_health_tashiding")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        elif service_type == "police":
            response_text = """ **POLICE HELPLINE**

** Police Emergency:** 100
** Police Control Room (Gyalshing):** 03595-251074, 77978-82838

For complaints of theft, assault, threat, missing person, or any criminal activity. Quick dispatch of nearest patrol vehicle.

**Local Police Stations:**
• Geyzing Police Station: 81458-87528
• Dentam Police Station: 97759-79366
• Uttarey Police Station: 79081-18656

Call respective stations for area-based incidents or verification needs."""
            
            keyboard = [
                [InlineKeyboardButton(" Call Police (100)", callback_data="call_100")],
                [InlineKeyboardButton(" Control Room", callback_data="call_03595251074")],
                [InlineKeyboardButton(" Geyzing Police Station", callback_data="call_8145887528")],
                [InlineKeyboardButton(" Dentam Police Station", callback_data="call_9775979366")],
                [InlineKeyboardButton(" Uttarey Police Station", callback_data="call_7908118656")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        elif service_type == "mental_health":
            response_text = """ **MENTAL HEALTH HELPLINE**

** Tele-MANAS Toll-Free Helpline:** 14416
Free, 24x7 government counselling for stress, anxiety, depression, substance use, or suicidal thoughts. Available in 20+ languages.

** Sikkim Suicide Prevention & Mental Health Helpline**
• 1800-345-3225
• 03592-20211

Trained counsellors provide confidential emotional support. No registration or ID needed.

**Ideal for students, youth, women, or anyone in emotional distress.**"""
            
            keyboard = [
                [InlineKeyboardButton(" Tele-MANAS (14416)", callback_data="call_14416")],
                [InlineKeyboardButton(" Suicide Prevention (1800-345-3225)", callback_data="call_18003453225")],
                [InlineKeyboardButton(" Sikkim Helpline (03592-20211)", callback_data="call_0359220211")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        elif service_type == "control_room":
            response_text = """ **DISTRICT CONTROL ROOM (DISASTER MANAGEMENT)**

** Disaster Reporting – Gyalshing HQ:** 03595-250633
** Nodal Officer – Ganesh Rai:** 96093-45119

For reporting landslides, blocked roads, floods, house collapses, or requesting evacuation/shelter. Staffed 24x7 during monsoon and alerts.

**Emergency Response Services:**
• Disaster reporting and coordination
• Evacuation assistance
• Shelter arrangements
• Road clearance coordination
• Emergency supplies distribution"""
            
            keyboard = [
                [InlineKeyboardButton(" Disaster Reporting", callback_data="call_03595250633")],
                [InlineKeyboardButton(" Nodal Officer", callback_data="call_9609345119")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        elif service_type == "women_child":
            response_text = """‍ **WOMEN / CHILD HELPLINE**

** Women in Distress Helpline (One Stop Centre):** 181 (24x7)
** Childline (Emergency for Minors):** 1098
** Police Emergency (Women & Children):** 100

For reporting domestic violence, child abuse, harassment, abandonment, trafficking, or family disputes.

**Services Available:**
• 24x7 emergency response
• Legal assistance
• Medical support
• Shelter arrangements
• Counselling services"""
            
            keyboard = [
                [InlineKeyboardButton(" Women Helpline (181)", callback_data="call_181")],
                [InlineKeyboardButton(" Childline (1098)", callback_data="call_1098")],
                [InlineKeyboardButton(" Police Emergency (100)", callback_data="call_100")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        elif service_type == "tourism":
            response_text = """ **TOURISM ASSISTANCE**

** Pelling Tourist Information Centre:** 73187-14900

For help with local travel issues, missing items, safety concerns, medical assistance for tourists, or guidance on trekking/routing.

**Services Available:**
• Tourist information and guidance
• Emergency assistance for tourists
• Lost and found services
• Safety and security support
• Medical assistance coordination
• Trekking and routing guidance"""
            
            keyboard = [
                [InlineKeyboardButton(" Tourist Information Centre", callback_data="call_7318714900")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        else:
            # Default to ambulance for general emergency
            response_text = """ **EMERGENCY SERVICES**

**For immediate medical emergency:**
• Call 102 or 108 for ambulance
• Call 100 for police
• Call 101 for fire

**District Hospital:** 03595-250823

Please select a specific emergency service from the menu above."""
            
            keyboard = [
                [InlineKeyboardButton(" Call Ambulance (102)", callback_data="call_102")],
                [InlineKeyboardButton(" Call Police (100)", callback_data="call_100")],
                [InlineKeyboardButton(" Call Fire (101)", callback_data="call_101")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def handle_emergency_health_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE, location: str):
        """Handle health emergency location selection"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        if location == "district":
            response_text = """ **District Hospital (Gyalshing HQ)**

 **District Hospital, Gyalshing**

‍ **Chief Medical Officer:** Dr. Namgay Bhutia –  94341-84389
‍ **District Medical Superintendent:** Dr. Nim Norbu Bhuatia –  95939-86069

 **Ambulance Drivers (HQ)**
• Raj Kr Chettri –  96478-80775
• Ganesh Subedi –  99326-27198
• Rajesh Gurung –  97334-73753
• Bikram Rai –  74785-83708

 Call for urgent medical emergencies, admissions, or ambulance transport."""
            
            keyboard = [
                [InlineKeyboardButton(" CMO Office", callback_data="call_9434184389")],
                [InlineKeyboardButton(" DMS Office", callback_data="call_9593986069")],
                [InlineKeyboardButton(" District Hospital", callback_data="call_03595250823")],
                [InlineKeyboardButton(" Back to Health Emergency", callback_data="emergency_health")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        elif location == "yuksom":
            response_text = """ **Yuksom PHC**

 **Yuksom PHC**

‍ **Medical Officer In-Charge:** Dr. Biswas Basnet –  70296-52289 / 81169-05440
 **Ambulance Driver (102):** Prem Gurung –  74793-56022

‍ **Health Workers (HWC/SC - Yuksom PHC region):**
• Nisha Hangma Limboo – Gerethang HWC-SC –  83378-58563
• Tonzy Hangma Limboo – Thingling HWC-SC –  97330-76496
• Doma Lepcha – Melli Aching HWC-SC –  76248-84889
• Mingma Doma Bhutia – Darap HWC-SC –  75850-04972
• Tenzing Bhutia – Pelling HWC-SC –  76022-39073
• Wynee Rai – Nambu HWC-SC –  93826-80108
• Kaveri Rai – Rimbi HWC-SC –  81452-74136
• Yanki Bhutia – Yuksom HWC-SC –  96470-78918

 You may contact your nearest health worker or ambulance driver for any local emergency."""
            
            keyboard = [
                [InlineKeyboardButton(" Medical Officer", callback_data="call_7029652289")],
                [InlineKeyboardButton(" Ambulance Driver", callback_data="call_7479356022")],
                [InlineKeyboardButton(" Back to Health Emergency", callback_data="emergency_health")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        elif location == "dentam":
            response_text = """ **Dentam PHC**

 **Dentam PHC**

‍ **Medical Officer In-Charge:** Dr. Ashim Basnett –  74077-77138
 **Ambulance (102) Driver:** Uttam Basnett –  77973-79779

‍ **Health Workers (HWC/SC - Dentam PHC region):**
• Sangita Chettri – Yangsum HWC-SC –  95933-78780
• Chamdra Maya Rai – Bermiok HWC-SC –  74775-24613
• Dukmit Lepcha – Hee HWC-SC –  77970-03965
• Manita Subba – Khandu HWC-SC –  76027-61162
• Palmu Bhutia – Lingchom HWC-SC –  81010-77806
• Panita Rai – Uttarey HWC-SC –  99162-92835

 Dial the ambulance or nearest CHO/MLHP for assistance in the Dentam area."""
            
            keyboard = [
                [InlineKeyboardButton(" Medical Officer", callback_data="call_7407777138")],
                [InlineKeyboardButton(" Ambulance Driver", callback_data="call_7797379779")],
                [InlineKeyboardButton(" Back to Health Emergency", callback_data="emergency_health")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        elif location == "tashiding":
            response_text = """ **Tashiding PHC**

 **Tashiding PHC**

‍ **Medical Officer In-Charge:** Dr. Neelam –  81458-17453
 **Ambulance Driver:** Chogyal Tshering Bhutia –  95933-76420

‍ **Health Workers (HWC/SC - Tashiding area):**
• Kawshila Subba – Karzee HWC-SC –  97323-14036
• Mingma Doma Bhutia – Kongri HWC-SC –  96791-94237
• Dechen Ongmu Bhutia – Gangyap HWC-SC –  74329-94864
• Pema Choden Lepcha – Legship HWC-SC –  83728-34849
• Smriti Rai – Sakyong HWC-SC –  77193-17484
• Wangchuk Bhutia – Naku Chumbung HWC-SC –  62974-22751
• Pema Choden Bhutia – Naku Chumbung HWC-SC –  79088-30759

 For remote areas, directly call the health worker responsible for your HWC or SC."""
            
            keyboard = [
                [InlineKeyboardButton(" Medical Officer", callback_data="call_8145817453")],
                [InlineKeyboardButton(" Ambulance Driver", callback_data="call_9593376420")],
                [InlineKeyboardButton(" Back to Health Emergency", callback_data="emergency_health")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            
        else:
            response_text = """ **Health Emergency**

Please select a specific health facility location for detailed contact information."""
            
            keyboard = [
                [InlineKeyboardButton(" Back to Health Emergency", callback_data="emergency_health")],
                [InlineKeyboardButton(" Back to Emergency Menu", callback_data="emergency")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # --- Tourism & Homestays ---
    async def handle_tourism_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle homestay booking menu"""
        places = self.home_stay_df['Place'].unique()
        keyboard = []
        for place in places:
            keyboard.append([InlineKeyboardButton(f" {place}", callback_data=f"place_{place}")])
        keyboard.append([InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Book a Homestay* 

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
        
        text = f"*Available Homestays in {place}* \n\n"
        for _, row in place_homestays.iterrows():
            text += f"*{row['HomestayName']}*\n"
            text += f" Address: {row['Address']}\n"
            text += f" Price: {row['PricePerNight']}\n"
            text += f" Contact: {row['ContactNumber']}\n"
            if pd.notna(row['Info']) and row['Info']:
                text += f"ℹ Info: {row['Info']}\n"
            text += "\n"
        
        keyboard = [
            [InlineKeyboardButton(" Search Another Place", callback_data="tourism")],
            [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]
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
        text = """*Common Service Centers (CSC)* 

Please select an option:
1. Find nearest CSC
2. Apply for certificate
3. Return to main menu"""
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    # Removed old handle_csc_selection function - now handled by contacts menu

    async def handle_certificate_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle certificate services information"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        text = f"*Apply for Certificate through Sikkim SSO* \n\n{self.responses[user_lang]['certificate_info']}"

        keyboard = [
            [InlineKeyboardButton(" Yes, Connect with CSC", callback_data="certificate_csc")],
            [InlineKeyboardButton(" No, I'll use SSO Portal", callback_data="certificate_sso")],
            [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]
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
            await self.handle_certificate_info(update, context)
        else:
            sso_message = self.responses[user_lang]['certificate_sso_message']
            await update.callback_query.edit_message_text(sso_message, parse_mode='Markdown')
        
    async def handle_certificate_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle certificate application workflow - DEPRECATED, use new certificate workflow"""
        await update.message.reply_text("Please use the new certificate workflow from the main menu.", parse_mode='Markdown')

    # --- Complaint ---
    async def start_emergency_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start emergency workflow - ask questions first, location at end"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Initialize emergency workflow state
        state = {
            "workflow": "emergency",
            "step": "emergency_type"
        }
        self._set_user_state(user_id, state)
        
        # Show emergency type options
        keyboard = [
            [InlineKeyboardButton(" Ambulance", callback_data="emergency_ambulance")],
            [InlineKeyboardButton(" Police", callback_data="emergency_police")],
            [InlineKeyboardButton(" Fire", callback_data="emergency_fire")],
            [InlineKeyboardButton(" General Emergency", callback_data="emergency_general")],
            [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            # Handle callback query
            await update.callback_query.edit_message_text(
                self.responses[user_lang]['emergency_type_prompt'],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            # Handle regular message
            await update.message.reply_text(
                self.responses[user_lang]['emergency_type_prompt'],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def start_complaint_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start complaint workflow - ask questions first, location at end"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Initialize complaint workflow state
        state = {
            "workflow": "complaint",
            "step": "name"
        }
        self._set_user_state(user_id, state)
        
        # Start with asking for name
        if hasattr(update, 'callback_query') and update.callback_query:
            # Handle callback query
            await update.callback_query.edit_message_text(
                self.responses[user_lang]['complaint_name_prompt'],
                parse_mode='Markdown'
            )
        else:
            # Handle regular message
            await update.message.reply_text(
                self.responses[user_lang]['complaint_name_prompt'],
                parse_mode='Markdown'
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
            # Store complaint description and request location at the end
            state["complaint_description"] = text
            state["step"] = "location_request"
            self._set_user_state(user_id, state)
            
            # Ask if user wants to share location
            keyboard = [
                [InlineKeyboardButton(" Share My Location", callback_data="complaint_share_location")],
                [InlineKeyboardButton(" Enter Location Manually", callback_data="complaint_manual_location")],
                [InlineKeyboardButton("⏭ Skip Location", callback_data="complaint_skip_location")],
                [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                self.responses[user_lang]['complaint_location_prompt'],
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the bot"""
        logger.error(f"[ERROR] {context.error}", exc_info=context.error)
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

    # New functionality methods
    async def handle_scheme_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle comprehensive government schemes menu"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        text = """ **MAIN MENU – "Scheme – Know & Apply"**

 Please select your category:"""

        keyboard = [
            [InlineKeyboardButton("‍ I am a Farmer", callback_data="scheme_category_farmer")],
            [InlineKeyboardButton(" I am a Student", callback_data="scheme_category_student")],
            [InlineKeyboardButton("‍ I am Youth / Entrepreneur / SHG", callback_data="scheme_category_youth")],
            [InlineKeyboardButton(" Health Related", callback_data="scheme_category_health")],
            [InlineKeyboardButton(" Other Schemes via CSC", callback_data="scheme_category_other")],
            [InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # Scheme Category Handlers
    async def handle_scheme_category_farmer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle farmer schemes category"""
        text = """‍ **I am a Farmer**

Please select a scheme:"""

        keyboard = [
            [InlineKeyboardButton("PM-KISAN", callback_data="scheme_pmkisan")],
            [InlineKeyboardButton("PM Fasal Bima Yojana", callback_data="scheme_pmfasal")],
            [InlineKeyboardButton(" Back to Categories", callback_data="schemes")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_category_student(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle student schemes category"""
        text = """ **I am a Student**

Please select a scheme:"""

        keyboard = [
            [InlineKeyboardButton("Scholarships", callback_data="scheme_scholarships")],
            [InlineKeyboardButton("Sikkim Mentor", callback_data="scheme_sikkim_mentor")],
            [InlineKeyboardButton(" Back to Categories", callback_data="schemes")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_category_youth(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle youth/entrepreneur schemes category"""
        text = """‍ **I am Youth / Entrepreneur / SHG**

Please select a scheme:"""

        keyboard = [
            [InlineKeyboardButton("Sikkim Skilled Youth Startup Yojana", callback_data="scheme_sikkim_youth")],
            [InlineKeyboardButton("PMEGP", callback_data="scheme_pmegp")],
            [InlineKeyboardButton("PM FME", callback_data="scheme_pmfme")],
            [InlineKeyboardButton("Mentorship", callback_data="scheme_mentorship")],
            [InlineKeyboardButton(" Back to Categories", callback_data="schemes")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_category_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle health schemes category"""
        text = """ **Health Related Schemes**

Please select a scheme:"""

        keyboard = [
            [InlineKeyboardButton("Ayushman Bharat", callback_data="scheme_ayushman")],
            [InlineKeyboardButton(" Back to Categories", callback_data="schemes")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_category_other(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle other schemes via CSC category"""
        text = """ **Other Useful Public Services (Available at CSC / GPK)**

You can get help from your local CSC operator or apply online.

** Work & Identity**
• PM Vishwakarma – Support for traditional artisans
• e-Shram Registration – National database for unorganised workers
• Kisan Credit Card – Easy credit for farmers

** Transport**
• Token Tax, HPT, HPA
• DL Renewal, DOB Correction
• Duplicate RC, Change of Address
• Learner's Licence, Permanent Licence

** Insurance**
• LIC Premium Payment
• Health Insurance (incl. Ayushman Bharat)
• Cattle Insurance
• Motor Insurance
• Life Insurance

** Pension & Proof**
• Jeevan Pramaan – Life certificate for pensioners
• National Pension Scheme (NPS)

** Utility & Travel**
• Bill Payments (Electricity, DTH, Mobile Recharge)
• Flight & Train Tickets – IRCTC, airline booking support
• PAN Card / Passport Application

** Finance & Tax**
• GST Filing / ITR Filing
• Digipay / Micro ATM Services

** Education & Scholarships**
• NIOS/BOSSE Open Schooling Registration
• Olympiad / National Scholarships Biometric Authentication

⏩ **Where to Apply?**
 Visit nearest CSC (Common Service Centre) or GPK (Gram Panchayat Kendra)"""

        keyboard = [
            [InlineKeyboardButton(" Contact your CSC Operator", callback_data="contacts_csc")],
            [InlineKeyboardButton(" Back to Categories", callback_data="schemes")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # Individual Scheme Handlers
    async def handle_scheme_pmkisan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PM-KISAN scheme"""
        text = """ **About PM-KISAN**
Get ₹6,000 per year (₹2,000 every 4 months) directly into your bank account.

 **How to Apply**
Apply online at https://pmkisan.gov.in
OR visit your nearest CSC (Common Service Centre)

 **Contact**
Agriculture Department or your local CSC Operator

Would you like to:"""

        keyboard = [
            [InlineKeyboardButton(" Apply Online", url="https://pmkisan.gov.in")],
            [InlineKeyboardButton(" Apply via CSC", callback_data="scheme_apply_csc_pmkisan")],
            [InlineKeyboardButton(" Back to Farmer Schemes", callback_data="scheme_category_farmer")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_pmfasal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PM Fasal Bima Yojana scheme"""
        text = """ **About PM Fasal Bima Yojana**
Get insurance cover for crop damage due to natural calamities.

 **How to Apply**
Apply at https://pmfby.gov.in
OR visit nearest CSC

 **Contact**
Agriculture Department / CSC Operator

Would you like to:"""

        keyboard = [
            [InlineKeyboardButton(" Apply Online", url="https://pmfby.gov.in")],
            [InlineKeyboardButton(" Apply via CSC", callback_data="scheme_apply_csc_pmfasal")],
            [InlineKeyboardButton(" Back to Farmer Schemes", callback_data="scheme_category_farmer")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_scholarships(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle scholarships scheme"""
        text = """ **Scholarships**

1⃣ **CENTRAL GOVERNMENT SCHOLARSHIPS**
 Apply at: https://scholarships.gov.in

**A. Pre-Matric Scholarships**
Target: SC/ST/OBC/Minority students studying in Class 1–10
Eligibility: Parental income < ₹1 lakh (varies by scheme)
Benefits: ₹1,000–5,000 per year + additional allowance

**B. Post-Matric Scholarships**
Target: Class 11 to PG-level students from SC/ST/OBC/EBC/Minority communities
Eligibility: Varies by category (usually income < ₹2.5 lakh)
Benefits: Tuition fees, maintenance, allowances (₹7,000–₹25,000+)

**C. Merit Cum Means Scholarships**
Target: Professional and Technical Courses
Eligibility: Minority students with income < ₹2.5 lakh/year
Benefits: ₹20,000/year + maintenance

**D. Top Class Education for SC/ST Students**
Fully funded scholarship for top institutions (IITs, IIMs, AIIMS)
Includes tuition, boarding, laptop, etc.

**E. National Means-cum-Merit Scholarship (NMMS)**
Target: Class 8 students with 55%+ marks
Benefit: ₹12,000 per year from Class 9 to 12

2⃣ **SIKKIM STATE SCHOLARSHIPS**
 Apply at: https://scholarships.sikkim.gov.in

**A. Post-Matric State Scholarship (Sikkim Subject/COI holders)**
Eligibility: SC/ST/OBC/MBC/EWS students
Courses: Class 11 to PG, professional courses
Benefit: ₹5,000 to ₹35,000/year depending on level

**B. Chief Minister's Merit Scholarship**
Target: Class 5+ students scoring high marks in government exams
Benefit: Full residential school fee, coaching support

**C. EBC State Scholarship**
Target: Economically Backward Class (non-SC/ST/OBC)
Eligibility: Parental income < ₹2.5 lakh/year
Courses: Class 11–PG
Benefit: ₹6,000–₹15,000/year

**D. Scholarship for Indigenous Students**
Target: Lepcha, Bhutia, Limboo, and other notified communities
Benefit: ₹10,000–₹25,000/year

**Contact:** Education Department, Or CSC Operator to Apply"""

        keyboard = [
            [InlineKeyboardButton(" Central Scholarships", url="https://scholarships.gov.in")],
            [InlineKeyboardButton(" State Scholarships", url="https://scholarships.sikkim.gov.in")],
            [InlineKeyboardButton(" Apply via CSC", callback_data="scheme_apply_csc_scholarships")],
            [InlineKeyboardButton(" Back to Student Schemes", callback_data="scheme_category_student")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_sikkim_mentor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Sikkim Mentor scheme"""
        text = """‍ **Sikkim Mentor**

**What it is:**
Sikkim Mentor is a free mentorship platform that connects students, job seekers, and entrepreneurs with experienced professionals from fields like civil services, education, business, mental health, sports, and more.

**How it works:**
• Offers one-on-one and group sessions, both online (Zoom/Google Meet) and in-person
• Organized community events—marathons, quizzes, mental health seminars—have already served 400+ students over 20,000+ counseling minutes
• Totally free; mentors include professionals and volunteers across sectors

**Who can benefit:**
• Students needing academic or career guidance
• Youth seeking entrepreneurship or startup support
• Individuals looking for personal or mental wellness mentoring

**How to join:**
1. Visit https://sikkimmentor.com
2. Click "Sign Up" and fill in details (name, email, DOB, mobile, interests)
3. Log in and connect with mentors based on your goals."""

        keyboard = [
            [InlineKeyboardButton(" Visit Website", url="https://sikkimmentor.com")],
            [InlineKeyboardButton(" Back to Student Schemes", callback_data="scheme_category_student")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_sikkim_youth(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Sikkim Skilled Youth Startup Yojana"""
        text = """‍ **Sikkim Skilled Youth Startup Yojana**

**About the Scheme**
• Launched in 2020 by Sikkim's Department of Commerce & Industries
• Aims to support educated but unemployed youth to start businesses (manufacturing, services, agriculture, tourism, retail, food processing, IT, homestays, etc.)

**Financial Benefits**
• BPL applicants: 50% subsidy on project cost
• Other applicants: 35% subsidy on project cost
• Applicant must contribute 5–15%; remaining cost is covered by bank loan
• Eligible project cost ranges from ₹3 lakh up to ₹20 lakh

**Eligibility**
• Age: 18–45 years
• Sikkim subject with COI
• Minimum education: 5th pass + technical training/certificate if required
• Family income under ₹8 lakh per annum

**How to Apply**
1. Visit the Department of Commerce & Industries office (Udyog Bhawan, Upper Tadong)
2. Obtain the application form free of cost
3. Fill it out with your business plan and attach required documents
4. Submit it to the GM's office
5. If selected, attend a 5-day Entrepreneur Training Programme
6. Bank disburses loan; subsidy is released after bank finalizes your loan

**Project Examples & Limits**
Small businesses like dairy, poultry, food processing, tourism, IT, retail, service units, homestays, workshops—with segments up to ₹20 lakh

**Contact & Support**
• Scheme Helplines: 09775979806, 09609876534
• Dept. Commerce & Industries (Gangtok): 03592‑202318
• Email: sikkimindustries@gmail.com

**Want to Apply?**"""

        keyboard = [
            [InlineKeyboardButton(" Apply Online", callback_data="scheme_apply_online_sikkim_youth")],
            [InlineKeyboardButton(" Apply via CSC", callback_data="scheme_apply_csc_sikkim_youth")],
            [InlineKeyboardButton(" Back to Youth Schemes", callback_data="scheme_category_youth")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_pmegp(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PMEGP scheme"""
        text = """ **PMEGP (Prime Minister's Employment Generation Programme)**

**What it is:**
A central government credit-linked subsidy to help youth and artisans start micro-enterprises in urban & rural areas via KVIC and banks.

**Key Benefits:**
• Subsidy up to 35% of project cost (rural special category), 15–25% for general applicants
• Loan for remaining cost through PSUs, RRBs, cooperatives, SIDBI
• No income ceiling—eligible to all ages 18+, with basic education requirement for larger projects
• Project cost range: up to ₹25 L (manufacturing), ₹10 L (services)

**Eligibility:**
Individuals, SHGs, societies, trusts starting new enterprises (not previously availing subsidy)

**How to Apply:**
1. Register & apply online via KVIC portal
2. Submit business plan & documents
3. Attend mandatory training (EDP)
4. Project evaluated & loan disbursed by bank
5. Subsidy released into bank account post-verification

**Want to Apply?**"""

        keyboard = [
            [InlineKeyboardButton(" Apply Online", callback_data="scheme_apply_online_pmegp")],
            [InlineKeyboardButton(" Apply via CSC", callback_data="scheme_apply_csc_pmegp")],
            [InlineKeyboardButton(" Back to Youth Schemes", callback_data="scheme_category_youth")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_pmfme(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PM FME scheme"""
        text = """ **PM FME – Pradhan Mantri Formalisation of Micro Food Processing Enterprises**

**What it is**
A Government of India initiative to modernize small food processing units, integrating unorganized enterprises into the formal market and boosting capacity with training and support.

**Key Benefits**
• Up to 35% subsidy on project cost (max ₹10 lakh/unit)
• ₹40,000 seed capital grants for SHGs to buy tools & working capital
• Marketing/branding support and infrastructure aid
• Training, handholding, capacity building, and quality compliance

**Who can apply**
• Micro food processors: Individuals, FPOs, SHGs, Cooperatives
• Must register and upgrade existing / new units
• Scheme period: 2020–2025, ₹10,000 cr funding

** How to Apply**
1. Visit https://pmfme.mofpi.gov.in
2. Register and log in
3. Complete the online application
4. Upload necessary docs (project details, SHG info, etc.)
5. Upon approval, receive subsidy and support
6. For SHGs, register on NULM portal for ₹40k seed capital

**Contact:** District Industries Centre- GM DIC - For More Information

**Want to Apply?**"""

        keyboard = [
            [InlineKeyboardButton(" Apply Online", url="https://pmfme.mofpi.gov.in")],
            [InlineKeyboardButton(" Apply via CSC", callback_data="scheme_apply_csc_pmfme")],
            [InlineKeyboardButton(" Back to Youth Schemes", callback_data="scheme_category_youth")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_ayushman(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Ayushman Bharat scheme"""
        text = """ **Ayushman Bharat Card (PM-JAY Card)**

The Ayushman Bharat card gives eligible families access to free health insurance up to ₹5 lakh per year for secondary and tertiary care at empanelled hospitals.

 **Key Benefits:**
• Cashless treatment at government & private hospitals
• Covers surgery, ICU, diagnostics, medicines
• No age or family size limit
• Portable across India

 **Eligibility:**
• Families listed in SECC 2011 database
• Also includes construction workers, street vendors, domestic workers, etc.

 **How to Get Your Ayushman Card:**
1. Visit: https://pmjay.gov.in
2. Check eligibility using mobile/Aadhaar
3. Visit nearest CSC or empanelled hospital to register and generate your card
4. Carry Aadhaar and ration card while visiting

 **Where to Apply in Gyalshing District?**
• District Hospital – Gyalshing
• Yuksom PHC
• Dentam PHC
• Tashiding PHC
• You can also apply through the nearest Common Service Centre (CSC)

For help, call Ayushman Helpline: 14555.

**Want to Apply?**"""

        keyboard = [
            [InlineKeyboardButton(" Apply Online", url="https://pmjay.gov.in")],
            [InlineKeyboardButton(" Apply via CSC", callback_data="scheme_apply_csc_ayushman")],
            [InlineKeyboardButton(" Back to Health Schemes", callback_data="scheme_category_health")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_scheme_apply_online(self, update: Update, context: ContextTypes.DEFAULT_TYPE, scheme_name: str):
        """Handle online scheme application"""
        # Define website URLs for different schemes
        scheme_urls = {
            "Sikkim Youth": "https://sikkimindustries.gov.in",
            "Pmegp": "https://pmegp.kvic.org.in",
            "Pmfme": "https://pmfme.mofpi.gov.in",
            "Ayushman": "https://pmjay.gov.in"
        }
        
        url = scheme_urls.get(scheme_name, "https://sikkim.gov.in")
        
        text = f""" **Apply Online - {scheme_name}**

You can apply online for this scheme by visiting the official website.

**Website:** {url}

**Steps to apply online:**
1. Visit the website above
2. Register/Login to your account
3. Fill in the application form
4. Upload required documents
5. Submit your application
6. Track your application status

**Alternative:** You can also visit your nearest CSC for assistance with online application."""

        keyboard = [
            [InlineKeyboardButton(" Visit Website", url=url)],
            [InlineKeyboardButton(" Apply via CSC", callback_data="contacts_csc")],
            [InlineKeyboardButton(" Back to Schemes", callback_data="schemes")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # CSC Application Workflow for Schemes
    async def handle_scheme_csc_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE, scheme_name: str):
        """Start CSC application process for schemes"""
        user_id = update.effective_user.id
        
        # Set user state for CSC application
        self._set_user_state(user_id, {
            "workflow": "scheme_csc_application",
            "scheme": scheme_name,
            "step": "block_selection"
        })
        
        # Get unique blocks from the data
        blocks = sorted(self.sub_division_block_mapping_df['NAME OF BLOCK / Officer Incharge'].dropna().unique().tolist())
        
        text = f""" **{scheme_name} - Apply via CSC**

Please select your block to find the nearest CSC operator:"""
        
        # Create keyboard with blocks - use shorter callback data
        keyboard = []
        for i, block in enumerate(blocks):
            # Use index-based callback data to avoid length issues
            keyboard.append([InlineKeyboardButton(block, callback_data=f"scheme_csc_block_{i}")])
        
        # Store blocks in user state for later reference
        state = self._get_user_state(user_id)
        state["available_blocks"] = blocks
        self._set_user_state(user_id, state)
        
        keyboard.append([InlineKeyboardButton(" Back to Schemes", callback_data="schemes")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')



    async def handle_csc_block_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, block_index: str):
        """Handle block selection and show GPUs"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        print(f"DEBUG: handle_csc_block_selection called with block_index: {block_index}")
        print(f"DEBUG: User state: {state}")
        
        # Check if this is for scheme application or contacts search
        workflow = state.get("workflow")
        print(f"DEBUG: Workflow: {workflow}")
        
        if workflow == "scheme_csc_application":
            print(f"DEBUG: Calling _handle_scheme_csc_block_selection")
            await self._handle_scheme_csc_block_selection(update, context, block_index)
        elif workflow == "csc_search":
            print(f"DEBUG: Calling _handle_contacts_csc_block_selection")
            await self._handle_contacts_csc_block_selection(update, context, block_index)
        else:
            print(f"DEBUG: Invalid workflow: {workflow}")
            await update.callback_query.answer("Invalid workflow")
            return

    async def _handle_scheme_csc_block_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, block_index: str):
        """Handle block selection for scheme CSC application"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        # Get the actual block name from the index
        available_blocks = state.get("available_blocks", [])
        try:
            block_index = int(block_index)
            block_name = available_blocks[block_index]
        except (ValueError, IndexError):
            await update.callback_query.answer("Invalid block selection")
            return
        
        # Update state with selected block
        state["block"] = block_name
        state["step"] = "gpu_selection"
        self._set_user_state(user_id, state)
        
        # Get GPUs for the selected block from CSC details
        # First, extract the block name without the contact info
        block_name_clean = block_name.split('\n')[0].strip() if '\n' in block_name else block_name.strip()
        
        # Map block names from bot format to CSC details format
        block_mapping = {
            '(BAC CHONGRANG)': 'Chongrang',
            '(BAC DENTAM)': 'Dentam', 
            '(BAC GYALSHING)': 'Gyalshing',
            '(BAC YUKSAM)': 'Yuksam',
            'BAC - Hee Martam': 'Hee Martam'
        }
        
        # Get the correct block name for CSC details
        csc_block_name = block_mapping.get(block_name_clean, block_name_clean)
        
        # Debug: Print the block name being searched
        print(f"DEBUG: Original block name: {block_name_clean}")
        print(f"DEBUG: Mapped block name: {csc_block_name}")
        print(f"DEBUG: Available blocks in CSV: {self.csc_details_df['BLOCK'].unique()}")
        
        # Get GPUs from CSC details for this block - use case-insensitive matching
        print(f"DEBUG: Looking for block: '{csc_block_name}'")
        print(f"DEBUG: Available blocks in CSV: {self.csc_details_df['BLOCK'].unique()}")
        
        # Try exact match first (case-insensitive)
        block_gpus = self.csc_details_df[
            self.csc_details_df['BLOCK'].str.lower() == csc_block_name.lower()
        ]['GPU Name'].dropna().unique().tolist()
        
        print(f"DEBUG: Found {len(block_gpus)} GPUs with exact match")
        
        # If no exact match found, try partial matching
        if not block_gpus:
            block_gpus = self.csc_details_df[
                self.csc_details_df['BLOCK'].str.contains(csc_block_name, case=False, na=False, regex=False)
            ]['GPU Name'].dropna().unique().tolist()
            print(f"DEBUG: Found {len(block_gpus)} GPUs with partial match")
        
        # Clean GPU names by removing leading digits and dots
        cleaned_gpus = []
        for gpu in block_gpus:
            # Remove leading digits and dots (e.g., "19. SARDONG LUNGZICK" -> "SARDONG LUNGZICK")
            cleaned_gpu = re.sub(r'^\d+\.\s*', '', gpu.strip())
            cleaned_gpus.append(cleaned_gpu)
        
        block_gpus = sorted(cleaned_gpus)
        
        text = f""" **Block: {block_name}**

Please select your GPU (Gram Panchayat Unit):"""
        
        # Create keyboard with GPUs - use shorter callback data
        keyboard = []
        for i, gpu in enumerate(block_gpus):
            # Use index-based callback data to avoid length issues
            keyboard.append([InlineKeyboardButton(gpu, callback_data=f"scheme_csc_gpu_{i}")])
        
        # Store GPUs in user state for later reference
        state["available_gpus"] = block_gpus
        self._set_user_state(user_id, state)
        
        keyboard.append([InlineKeyboardButton(" Back to Schemes", callback_data="schemes")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_contacts_csc_block_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, block_index: str):
        """Handle contacts CSC block selection and show GPU selection"""
        print(f"DEBUG: handle_contacts_csc_block_selection called with block_index: {block_index}")
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        print(f"DEBUG: User ID: {user_id}")
        print(f"DEBUG: Current state: {state}")
        
        # Available blocks for CSC search
        available_blocks = [
            "Yuksam",
            "Gyalshing", 
            "Dentam",
            "Hee Martam",
            "Arithang Chongrang",
            "Gyalshing Municipal Council"
        ]
        
        try:
            block_index = int(block_index)
            block_name = available_blocks[block_index]
        except (ValueError, IndexError):
            await update.callback_query.answer("Invalid block selection")
            return
        
        # Update state with selected block
        state["block"] = block_name
        state["step"] = "gpu_selection"
        self._set_user_state(user_id, state)
        
        # Get GPUs for the selected block from CSC details
        # Map block names from bot format to CSC details format
        block_mapping = {
            'Arithang Chongrang': 'Chongrang',
            'Dentam': 'Dentam', 
            'Gyalshing': 'Gyalshing',
            'Yuksam': 'Yuksam',
            'Hee Martam': 'Hee Martam',
            'Gyalshing Municipal Council': 'Gyalshing Municipal Council'
        }
        
        # Get the correct block name for CSC details
        csc_block_name = block_mapping.get(block_name, block_name)
        
        # Get GPUs from CSC details for this block - use case-insensitive matching
        block_gpus = self.csc_details_df[
            self.csc_details_df['BLOCK'].str.lower() == csc_block_name.lower()
        ]['GPU Name'].dropna().unique().tolist()
        
        # If no exact match found, try partial matching
        if not block_gpus:
            block_gpus = self.csc_details_df[
                self.csc_details_df['BLOCK'].str.contains(csc_block_name, case=False, na=False, regex=False)
            ]['GPU Name'].dropna().unique().tolist()
        
        # Clean GPU names by removing leading digits and dots
        cleaned_gpus = []
        for gpu in block_gpus:
            # Remove leading digits and dots (e.g., "19. SARDONG LUNGZICK" -> "SARDONG LUNGZICK")
            cleaned_gpu = re.sub(r'^\d+\.\s*', '', gpu.strip())
            cleaned_gpus.append(cleaned_gpu)
        
        block_gpus = sorted(cleaned_gpus)
        
        if not block_gpus:
            text = f""" **No GPUs Found**

No GPUs found for block: **{block_name}**

Please try a different block or contact support."""
            keyboard = [
                [InlineKeyboardButton(" Back to Blocks", callback_data="contacts_csc")],
                [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        text = f""" **Know Your CSC Operator**

**Selected Block:** {block_name}

**Step 2: GPU Selection**
                
Please select your GPU (Gram Panchayat Unit):"""
        
        # Create keyboard with GPUs
        keyboard = []
        for i, gpu in enumerate(block_gpus):
            keyboard.append([InlineKeyboardButton(gpu, callback_data=f"contacts_csc_gpu_{i}")])
        
        # Store GPUs in user state for later reference
        state["available_gpus"] = block_gpus
        self._set_user_state(user_id, state)
        
        keyboard.append([InlineKeyboardButton(" Back to Blocks", callback_data="contacts_csc")])
        keyboard.append([InlineKeyboardButton(" Back to Contacts", callback_data="contacts")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_contacts_csc_gpu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, gpu_index: str):
        """Handle GPU selection for contacts CSC search and show CSC operator details"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        # Get the actual GPU name from the index
        available_gpus = state.get("available_gpus", [])
        print(f"DEBUG: Available GPUs: {available_gpus}")
        print(f"DEBUG: GPU index: {gpu_index}")
        
        try:
            gpu_index = int(gpu_index)
            gpu_name = available_gpus[gpu_index]
            print(f"DEBUG: Selected GPU: {gpu_name}")
        except (ValueError, IndexError) as e:
            print(f"DEBUG: Error in GPU selection: {e}")
            await update.callback_query.answer("Invalid GPU selection")
            return
        
        # Get block name from state
        block_name = state.get("block", "Unknown")
        
        # Get CSC operator details from CSC details dataframe
        # First, try to find the GPU in the dataframe
        csc_operator = None
        
        # Map block names for CSC details lookup
        block_mapping = {
            'Arithang Chongrang': 'Chongrang',
            'Dentam': 'Dentam', 
            'Gyalshing': 'Gyalshing',
            'Yuksam': 'Yuksam',
            'Hee Martam': 'Hee Martam',
            'Gyalshing Municipal Council': 'Gyalshing Municipal Council'
        }
        
        csc_block_name = block_mapping.get(block_name, block_name)
        
        # Search for the GPU in the CSC details
        gpu_matches = self.csc_details_df[
            (self.csc_details_df['BLOCK'].str.lower() == csc_block_name.lower()) &
            (self.csc_details_df['GPU Name'].str.contains(gpu_name, case=False, na=False, regex=False))
        ]
        
        if not gpu_matches.empty:
            # Get the first match
            csc_operator = gpu_matches.iloc[0]
        
        # Display CSC operator details
        if csc_operator is not None:
            operator_name = csc_operator.get('Name', 'Not Available')
            operator_phone = csc_operator.get('Contact No.', 'Not Available')
            single_window = csc_operator.get('Block Single Window', 'Not Available')
            subdivision = csc_operator.get('SubDivision Single Window', 'Not Available')
            
            text = f""" **CSC Operator Details**

**Block:** {block_name}
**GPU:** {gpu_name}

 **Name:** {operator_name}
 **Phone:** {operator_phone}
 **Single Window:** {single_window}
 **Subdivision:** {subdivision}

**He/She will assist you with online services and certificates.**

**Services Available:**
• Certificate applications
• Government scheme applications
• Document verification
• Online service assistance
• Payment processing"""
            
            keyboard = [
                [InlineKeyboardButton(" Call CSC Operator", callback_data=f"call_csc_{operator_phone}")],
                [InlineKeyboardButton(" Back to GPUs", callback_data="contacts_csc")],
                [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")]
            ]
        else:
            text = f""" **CSC Operator Not Found**

**Block:** {block_name}
**GPU:** {gpu_name}

Sorry, we couldn't find CSC operator details for this GPU. Please try selecting a different GPU or contact the block office directly."""
            
            keyboard = [
                [InlineKeyboardButton(" Back to GPUs", callback_data="contacts_csc")],
                [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        keyboard.append([InlineKeyboardButton(" Back to Blocks", callback_data="scheme_csc_back_to_blocks")])
        keyboard.append([InlineKeyboardButton(" Back to Schemes", callback_data="schemes")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_csc_gpu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, gpu_index: str):
        """Handle GPU selection and show CSC info directly"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        if state.get("workflow") != "scheme_csc_application":
            return
        
        # Get the actual GPU name from the index
        available_gpus = state.get("available_gpus", [])
        try:
            gpu_index = int(gpu_index)
            gpu_name = available_gpus[gpu_index]
        except (ValueError, IndexError):
            await update.callback_query.answer("Invalid GPU selection")
            return
        
        # Update state with selected GPU
        state["gpu"] = gpu_name
        state["step"] = "csc_info"
        self._set_user_state(user_id, state)
        
        # Get subdivision info for the selected block
        block_name = state.get("block", "")
        subdivision_info = self.sub_division_block_mapping_df[
            self.sub_division_block_mapping_df['NAME OF BLOCK / Officer Incharge'] == block_name
        ]['Sub Division / Officer Incharge'].dropna().unique()
        
        subdivision_name = subdivision_info[0] if len(subdivision_info) > 0 else "N/A"
        state["subdivision"] = subdivision_name
        self._set_user_state(user_id, state)
        
        # Get CSC info for the selected GPU - try multiple matching strategies
        print(f"DEBUG: Looking for GPU: '{gpu_name}'")
        print(f"DEBUG: Available GPUs in CSV: {self.csc_details_df['GPU Name'].unique()}")
        
        # Try exact match first
        csc_info = self.csc_details_df[
            self.csc_details_df['GPU Name'].str.strip() == gpu_name.strip()
        ]
        
        # If no exact match, try case-insensitive match
        if csc_info.empty:
            csc_info = self.csc_details_df[
                self.csc_details_df['GPU Name'].str.lower() == gpu_name.lower()
            ]
        
        # If still no match, try partial match
        if csc_info.empty:
            csc_info = self.csc_details_df[
                self.csc_details_df['GPU Name'].str.contains(gpu_name, case=False, na=False, regex=False)
            ]
        
        # If still no match, try matching cleaned version
        if csc_info.empty:
            csc_info = self.csc_details_df[
                self.csc_details_df['GPU Name'].apply(lambda x: re.sub(r'^\d+\.\s*', '', x.strip()) if pd.notna(x) else '') == gpu_name.strip()
            ]
        
        print(f"DEBUG: Found {len(csc_info)} CSC entries for GPU '{gpu_name}'")
        
        # Get ward information from block_gpu_mapping
        ward_info = self.block_gpu_mapping_df[
            (self.block_gpu_mapping_df['Name of GPU'].str.contains(gpu_name, case=False, na=False)) |
            # Also try matching the cleaned version against the original
            (self.block_gpu_mapping_df['Name of GPU'].apply(lambda x: re.sub(r'^\d+\.\s*', '', x.strip()) if pd.notna(x) else '') == gpu_name.strip())
        ]['Name of Ward'].dropna().unique().tolist()
        
        if not csc_info.empty:
            info = csc_info.iloc[0]
            
            # Get block single window and subdivision single window contacts
            block_contacts = info.get('Block Single Window', 'N/A')
            subdivision_contacts = info.get('SubDivision Single Window', 'N/A')
            
            # Truncate long contact strings to avoid message length issues
            if len(block_contacts) > 50:
                block_contacts = block_contacts[:50] + "..."
            if len(subdivision_contacts) > 50:
                subdivision_contacts = subdivision_contacts[:50] + "..."
            
            text = f""" **CSC Operator Information**

**Subdivision:** {subdivision_name}
**Block:** {info.get('BLOCK', 'N/A')}
**GPU:** {info.get('GPU Name', gpu_name)}
**Wards:** {', '.join(ward_info) if ward_info else 'N/A'}

**CSC Operator Details:**
• **Name:** {info.get('Name', 'N/A')}
• **Contact:** {info.get('Contact No.', 'N/A')}

**Block Single Window:** {block_contacts}
**Subdivision Single Window:** {subdivision_contacts}

**Scheme:** {state.get('scheme', 'N/A')}

Would you like to submit your application details to this CSC operator?"""
            
            keyboard = [
                [InlineKeyboardButton(" Yes, Submit Application", callback_data="csc_submit_application")],
                [InlineKeyboardButton(" Back to GPUs", callback_data="scheme_csc_back_to_blocks")],
                [InlineKeyboardButton(" Back to Schemes", callback_data="schemes")]
            ]
        else:
            text = f""" **CSC Operator Not Found**

**Subdivision:** {subdivision_name}
**Block:** {block_name}
**GPU:** {gpu_name}

No CSC operator found for this GPU. Please try another GPU or contact support."""
            
            keyboard = [
                [InlineKeyboardButton(" Back to GPUs", callback_data="scheme_csc_back_to_blocks")],
                [InlineKeyboardButton(" Back to Schemes", callback_data="schemes")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')



    async def handle_csc_submit_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start application details collection"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        print(f"DEBUG: handle_csc_submit_application called")
        print(f"DEBUG: Current workflow: {state.get('workflow')}")
        print(f"DEBUG: Current state: {state}")
        
        if state.get("workflow") != "scheme_csc_application":
            print(f"DEBUG: Wrong workflow, returning")
            return
        
        # Update state to start collecting details
        state["step"] = "name"
        self._set_user_state(user_id, state)
        
        print(f"DEBUG: State updated to step: name")
        
        text = f""" **Application Details**

Please provide your details for **{state.get('scheme', 'Unknown Scheme')}**.

**Step 1: Please enter your full name**"""
        
        keyboard = [[InlineKeyboardButton(" Cancel", callback_data="schemes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        print(f"DEBUG: About to send message asking for name")
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        print(f"DEBUG: Message sent successfully")

    async def handle_scheme_csc_application_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle CSC application workflow"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        if state.get("workflow") != "scheme_csc_application":
            return
        
        step = state.get("step")
        scheme_name = state.get("scheme", "Unknown Scheme")
        
        if step == "name":
            state["name"] = text
            state["step"] = "father_name"
            self._set_user_state(user_id, state)
            
            await update.message.reply_text("**Step 2: Please enter your father's name**", parse_mode='Markdown')
            
        elif step == "father_name":
            state["father_name"] = text
            state["step"] = "phone"
            self._set_user_state(user_id, state)
            
            await update.message.reply_text("**Step 3: Please enter your phone number**", parse_mode='Markdown')
            
        elif step == "phone":
            state["phone"] = text
            state["step"] = "village"
            self._set_user_state(user_id, state)
            
            await update.message.reply_text("**Step 4: Please enter your village name**", parse_mode='Markdown')
            
        elif step == "village":
            state["village"] = text
            self._set_user_state(user_id, state)
            
            # Submit application
            await self.submit_csc_application(update, context, state)

    async def submit_csc_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
        """Submit CSC application to Google Sheets with reference number"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Unknown"
        scheme_name = state.get("scheme", "Unknown")
        applicant_name = state.get("name", "Unknown")
        father_name = state.get("father_name", "Unknown")
        phone = state.get("phone", "Unknown")
        village = state.get("village", "Unknown")
        ward = state.get("ward", "Unknown")
        gpu = state.get("gpu", "Unknown")
        block = state.get("block", "Unknown")
        
        # Generate unique reference number
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        reference_number = f"SK{timestamp}{user_id % 1000:03d}"
        
        # Log to Google Sheets with reference number
        success = self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="csc_scheme_application",
            query_text=f"CSC application: {scheme_name}",
            language="english",
            bot_response=f"Application submitted for {scheme_name} via CSC",
            scheme_name=scheme_name,
            applicant_name=applicant_name,
            father_name=father_name,
            phone=phone,
            village=village,
            ward=ward,
            gpu=gpu,
            block=block,
            reference_number=reference_number,
            application_status="Submitted",
            submission_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        if success:
            text = f""" **Application Submitted Successfully!**

**Scheme:** {scheme_name}
**Name:** {applicant_name}
**Father's Name:** {father_name}
**Phone:** {phone}
**Village:** {village}
**Ward:** {ward}
**GPU:** {gpu}
**Block:** {block}

 **Reference Number:** `{reference_number}`

Your application has been submitted to the CSC operator. You will be contacted soon for further processing.

**What happens next:**
• CSC operator will review your application
• You'll receive a call/SMS for verification
• Visit the CSC center with required documents
• Track your application status using your reference number

** How to track your application:**
• Use the 'Check Status of My Application' option
• Enter your reference number: `{reference_number}`
• CSC operator will update the status in our system

**CSC Contact:** Use the 'Important Contacts' section to find your CSC operator.

Thank you for using Sajilo Sewak Bot! """
        else:
            text = f""" **Application Submission Failed**

Sorry, there was an error submitting your application. Please try again or contact support.

**Scheme:** {scheme_name}
**Name:** {applicant_name}
**Phone:** {phone}
**Reference Number:** {reference_number}"""
        
        keyboard = [[InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        self._clear_user_state(user_id)

    async def handle_contacts_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Know Key Contact menu"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        contacts_text = """ **Know Key Contact**

Select one of the options below to get contact details:

 **1. Know Your CSC Operator**
Details for Smart Govt Assistant
→ Show BLOCK MENU
→ Show GPU MENU
Output: Name – [CSC Operator Name], Phone – [Contact Number]
He/She will assist you with online services and certificates.

 **2. Know Your BLO (Booth Level Officer)**
Details for Smart Govt Assistant
Find the BLO responsible for your polling booth to help with voter ID, electoral roll queries, etc.
Show: Select your Assembly Constituency
Then: Display Polling Booth list from Database
Output: YOUR BOOTH LEVEL OFFICER DETAILS ARE
Name – [BLO Name], Phone – [Contact Number]
Contact for voter-related services, corrections, additions.

 **3. Know Aadhar Operator**
Get your Aadhaar-related services such as:
 New Aadhaar Enrollment (Age 5+ & Adults)
 Update Name, Address, DOB, Mobile
 Biometric Updates (Photo, Fingerprint, Iris)
 Reprint / Download Aadhaar PDF
 Link Aadhaar with Mobile Number / Bank Account

 Aadhaar Kendras and Contacts:
 Yuksam SDM Office
‍ Contact Person: Pema
 Phone: 9564442624
 Dentam SDM Office
‍ Contact Person: Rajen Sharma
 Phone: 9733140036"""
        
        keyboard = [
            [InlineKeyboardButton(" Know Your CSC", callback_data="contacts_csc")],
            [InlineKeyboardButton(" Know Your BLO", callback_data="contacts_blo")],
            [InlineKeyboardButton(" Know Aadhar Operator", callback_data="contacts_aadhar")],
            [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(contacts_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(contacts_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_csc_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle CSC search - show block menu first"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Set state for CSC search workflow
        self._set_user_state(user_id, {
            "workflow": "csc_search",
            "step": "block_selection"
        })
        
        # Available blocks for CSC search
        available_blocks = [
            "Yuksam",
            "Gyalshing", 
            "Dentam",
            "Hee Martam",
            "Arithang Chongrang",
            "Gyalshing Municipal Council"
        ]
        
        text = """ **Know Your CSC Operator**

**Step 1: Block Selection**
                
Please choose your block:"""
        
        # Create keyboard with blocks
        keyboard = []
        for i, block in enumerate(available_blocks):
            keyboard.append([InlineKeyboardButton(block, callback_data=f"csc_block_{i}")])
        
        keyboard.append([InlineKeyboardButton(" Back to Contacts", callback_data="contacts")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_blo_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle BLO search - show assembly constituency selection"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Set state for BLO search workflow
        self._set_user_state(user_id, {
            "workflow": "blo_search",
            "step": "constituency_selection"
        })
        
        # Available assembly constituencies
        constituencies = [
            "1-YUKSOM TASHIDING",
            "02-YANGTHANG",
            "03-Maneybong Dentam", 
            "04-Gyalshing Bernyak"
        ]
        
        text = """ **Know Your BLO (Booth Level Officer)**

**Step 1: Assembly Constituency Selection**
                
Please select your Assembly Constituency:"""
        
        # Create keyboard with constituencies
        keyboard = []
        for i, constituency in enumerate(constituencies):
            keyboard.append([InlineKeyboardButton(constituency, callback_data=f"blo_constituency_{i}")])
        
        keyboard.append([InlineKeyboardButton(" Back to Contacts", callback_data="contacts")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_blo_constituency_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, constituency_index: str):
        """Handle BLO constituency selection and show polling booth list"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Available assembly constituencies
        constituencies = [
            "1-YUKSOM TASHIDING",
            "02-YANGTHANG",
            "03-Maneybong Dentam", 
            "04-Gyalshing Bernyak"
        ]
        
        try:
            constituency_index = int(constituency_index)
            selected_constituency = constituencies[constituency_index]
        except (ValueError, IndexError):
            await update.callback_query.answer("Invalid constituency selection")
            return
        
        # Set state for BLO search workflow
        state = self._get_user_state(user_id)
        state["selected_constituency"] = selected_constituency
        state["step"] = "polling_booth_selection"
        self._set_user_state(user_id, state)
        
        # Mock polling booth data - in real implementation, this would come from database
        polling_booths = {
            "1-YUKSOM TASHIDING": [
                "Yuksom Primary School",
                "Tashiding Monastery",
                "Pelling Higher Secondary School",
                "Geyzing Senior Secondary School"
            ],
            "02-YANGTHANG": [
                "Yangthang Primary School",
                "Dentam Secondary School",
                "Hee Martam Primary School",
                "Arithang Chongrang School"
            ],
            "03-Maneybong Dentam": [
                "Maneybong Primary School",
                "Dentam Higher Secondary",
                "Bermiok Primary School",
                "Hee Primary School"
            ],
            "04-Gyalshing Bernyak": [
                "Gyalshing Senior Secondary",
                "Bernyak Primary School",
                "Gyalshing Municipal Council",
                "Gyalshing Police Station"
            ]
        }
        
        booths = polling_booths.get(selected_constituency, ["No polling booths found"])
        
        text = f""" **Know Your BLO (Booth Level Officer)**

**Selected Constituency:** {selected_constituency}

**Step 2: Polling Booth Selection**
                
Please select your polling booth:"""
        
        # Create keyboard with polling booths
        keyboard = []
        for i, booth in enumerate(booths):
            keyboard.append([InlineKeyboardButton(booth, callback_data=f"blo_booth_{i}")])
        
        keyboard.append([InlineKeyboardButton(" Back to Constituencies", callback_data="contacts_blo")])
        keyboard.append([InlineKeyboardButton(" Back to Contacts", callback_data="contacts")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_blo_booth_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, booth_index: str):
        """Handle BLO polling booth selection and show BLO details"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Get state to retrieve selected constituency
        state = self._get_user_state(user_id)
        selected_constituency = state.get("selected_constituency", "Unknown")
        
        # Mock BLO data - in real implementation, this would come from database
        blo_data = {
            "1-YUKSOM TASHIDING": {
                "Yuksom Primary School": {"name": "Dorjee Bhutia", "phone": "9876543210"},
                "Tashiding Monastery": {"name": "Pema Wangchuk", "phone": "9876543211"},
                "Pelling Higher Secondary School": {"name": "Sonam Lepcha", "phone": "9876543212"},
                "Geyzing Senior Secondary School": {"name": "Tenzin Bhutia", "phone": "9876543213"}
            },
            "02-YANGTHANG": {
                "Yangthang Primary School": {"name": "Karma Sherpa", "phone": "9876543214"},
                "Dentam Secondary School": {"name": "Mingma Tamang", "phone": "9876543215"},
                "Hee Martam Primary School": {"name": "Dawa Bhutia", "phone": "9876543216"},
                "Arithang Chongrang School": {"name": "Pemba Sherpa", "phone": "9876543217"}
            },
            "03-Maneybong Dentam": {
                "Maneybong Primary School": {"name": "Rinzing Bhutia", "phone": "9876543218"},
                "Dentam Higher Secondary": {"name": "Tashi Wangdi", "phone": "9876543219"},
                "Bermiok Primary School": {"name": "Karma Dorjee", "phone": "9876543220"},
                "Hee Primary School": {"name": "Sonam Gyatso", "phone": "9876543221"}
            },
            "04-Gyalshing Bernyak": {
                "Gyalshing Senior Secondary": {"name": "Pema Dorjee", "phone": "9876543222"},
                "Bernyak Primary School": {"name": "Tenzin Wangchuk", "phone": "9876543223"},
                "Gyalshing Municipal Council": {"name": "Karma Tshering", "phone": "9876543224"},
                "Gyalshing Police Station": {"name": "Dawa Sherpa", "phone": "9876543225"}
            }
        }
        
        # Get polling booth name from state or use index
        polling_booths = {
            "1-YUKSOM TASHIDING": [
                "Yuksom Primary School",
                "Tashiding Monastery",
                "Pelling Higher Secondary School",
                "Geyzing Senior Secondary School"
            ],
            "02-YANGTHANG": [
                "Yangthang Primary School",
                "Dentam Secondary School",
                "Hee Martam Primary School",
                "Arithang Chongrang School"
            ],
            "03-Maneybong Dentam": [
                "Maneybong Primary School",
                "Dentam Higher Secondary",
                "Bermiok Primary School",
                "Hee Primary School"
            ],
            "04-Gyalshing Bernyak": [
                "Gyalshing Senior Secondary",
                "Bernyak Primary School",
                "Gyalshing Municipal Council",
                "Gyalshing Police Station"
            ]
        }
        
        try:
            booth_index = int(booth_index)
            booths = polling_booths.get(selected_constituency, [])
            selected_booth = booths[booth_index]
            
            # Get BLO details
            constituency_blo_data = blo_data.get(selected_constituency, {})
            blo_details = constituency_blo_data.get(selected_booth, {"name": "Not Available", "phone": "Not Available"})
            
        except (ValueError, IndexError):
            await update.callback_query.answer("Invalid booth selection")
            return
        
        # Display BLO details
        text = f""" **YOUR BOOTH LEVEL OFFICER DETAILS ARE**

**Constituency:** {selected_constituency}
**Polling Booth:** {selected_booth}

 **Name:** {blo_details['name']}
 **Phone:** {blo_details['phone']}

**Contact for voter-related services, corrections, additions.**

**Services Available:**
• Voter ID card issues
• Electoral roll corrections
• New voter registration
• Address updates
• Polling booth information"""
        
        keyboard = [
            [InlineKeyboardButton(" Call BLO", callback_data=f"call_blo_{blo_details['phone']}")],
            [InlineKeyboardButton(" Back to Booths", callback_data="blo_constituency_0")],
            [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_aadhar_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Aadhar services information"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        aadhar_info = """ **Know Aadhar Operator**

Get your Aadhaar-related services such as:
 New Aadhaar Enrollment (Age 5+ & Adults)
 Update Name, Address, DOB, Mobile
 Biometric Updates (Photo, Fingerprint, Iris)
 Reprint / Download Aadhaar PDF
 Link Aadhaar with Mobile Number / Bank Account

 **Aadhaar Kendras and Contacts:**
 Yuksam SDM Office
‍ Contact Person: Pema
 Phone: 9564442624

 Dentam SDM Office
‍ Contact Person: Rajen Sharma
 Phone: 9733140036

**How to Apply:**
1. Visit your nearest Aadhaar Kendra
2. Contact the operator for assistance
3. Submit required documents
4. Pay applicable fees

**Required Documents:**
• Proof of Identity
• Proof of Address
• Date of Birth Certificate
• Mobile Number (for OTP)"""
        
        keyboard = [
            [InlineKeyboardButton(" Find CSC Operator", callback_data="contacts_csc")],
            [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")],
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
                logger.error(f" Error saving feedback: {str(e)}")
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
                response = f""" **CSC Operator Found**

**GPU:** {csc_info['GPU Name']}
**Block:** {csc_info['BLOCK']}
**Operator Name:** {csc_info['Name']}
**Contact:** {csc_info['Contact No.']}

**Block Single Window:** {csc_info['Block Single Window']}
**Sub Division Single Window:** {csc_info['SubDivision Single Window']}"""
                
                keyboard = [
                    [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")],
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
                    response = f""" **CSC Operator Found (via Ward Search)**

**Ward:** {ward_name}
**GPU:** {csc_info['GPU Name']}
**Block:** {csc_info['BLOCK']}
**Operator Name:** {csc_info['Name']}
**Contact:** {csc_info['Contact No.']}

**Block Single Window:** {csc_info['Block Single Window']}
**Sub Division Single Window:** {csc_info['SubDivision Single Window']}"""
                    
                    keyboard = [
                        [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")],
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
                
                response = f""" **Constituency Found: {constituency_name}**

**Available GPUs in this constituency:**
"""
                
                for gpu in unique_gpus:
                    if pd.notna(gpu):
                        response += f"• {gpu}\n"
                
                response += f"\nPlease enter the specific GPU name from the list above to find the CSC operator."
                
                keyboard = [
                    [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")],
                    [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
                self._clear_user_state(user_id)
                return
            
            # 4. No exact match found - provide suggestions with retry mechanism
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
            
            response = f" **No exact match found for: {search_term}**\n\n"
            
            if suggestions:
                response += "**Did you mean one of these?**\n"
                for suggestion in suggestions:
                    response += f"• {suggestion}\n"
                response += "\n**Please try again with one of the suggested names above.**"
            else:
                response += "**Available GPUs in Sikkim:**\n"
                # Show first 10 GPUs as examples
                for i, gpu_name in enumerate(all_gpu_names[:10]):
                    response += f"• {gpu_name}\n"
                if len(all_gpu_names) > 10:
                    response += f"... and {len(all_gpu_names) - 10} more\n"
                response += "\n**Please try again with the exact GPU name.**"
            
            # Add retry button and keep user in search state
            keyboard = [
                [InlineKeyboardButton(" Try Again", callback_data="csc_search_retry")],
                [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")],
                [InlineKeyboardButton(self.responses[user_lang]['back_main_menu'], callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Keep user in search state for retry instead of clearing
            state["step"] = "gpu_input"
            state["last_search"] = search_term
            self._set_user_state(user_id, state)
            
            await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')

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
                response = f""" **BLO (Booth Level Officer) Found**

**AC:** {blo_info['AC']}
**Polling Station:** {blo_info['Polling Station']}
**BLO Name:** {blo_info['BLO Details']}
**Mobile Number:** {blo_info['Mobile Number']}"""
                
                keyboard = [
                    [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")],
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
                
                response = f" **No BLO found for polling station: {polling_station}**\n\n"
                
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
                    [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")],
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
        
        # Add handler for location messages FIRST (higher priority)
        self.application.add_handler(MessageHandler(filters.LOCATION, self.message_handler))
        
        # Add handler for text messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        self.application.add_error_handler(self.error_handler)  # Add error handler
        logger.info(" All handlers registered successfully")

    def run(self):
        """Run the bot"""
        try:
            # Create application
            self.application = Application.builder().token(self.BOT_TOKEN).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("language", self.language_command))
            self.application.add_handler(CommandHandler("status", self.handle_status_command))
            
            # Add handler for location messages FIRST (higher priority)
            self.application.add_handler(MessageHandler(filters.LOCATION, self.message_handler))
            
            # Add handler for text messages
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
            
            self.application.add_handler(CallbackQueryHandler(self.callback_handler))
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            # Start the bot
            logger.info("Starting Sajilo Sewak Bot...")
            print("Starting Sajilo Sewak Bot...")
            print("Ready to serve citizens!")
            
            # Run the bot until the user presses Ctrl-C
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except KeyboardInterrupt:
            logger.info("Shutting down bot...")
            if hasattr(self, 'conversation_system'):
                self.conversation_system.cleanup_session()
            print("Bot stopped gracefully.")
            
        except Exception as e:
            logger.error(f" Failed to start bot: {str(e)}")
            raise

    async def check_nc_exgratia_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, reference_number: str):
        """Check NC Exgratia application status using API"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Determine if this is a callback query or regular message
        is_callback = hasattr(update, 'callback_query') and update.callback_query is not None
        
        try:
            # Check if API client is available
            if not self.api_client:
                error_msg = " NC Exgratia API is not configured. Please contact support."
                if is_callback:
                    await update.callback_query.edit_message_text(error_msg, parse_mode='Markdown')
                else:
                    await update.message.reply_text(error_msg, parse_mode='Markdown')
                return
            
            # Show processing message
            processing_msg = f" Checking status for application: {reference_number}\n\nPlease wait..."
            if is_callback:
                await update.callback_query.edit_message_text(processing_msg, parse_mode='Markdown')
            else:
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
                
                status_msg = f""" *NC Exgratia Application Status*

 **Reference Number**: `{reference_number}`
 **Applicant**: {applicant_name}
 **Submitted**: {formatted_date}
 **Status**: {status}

*Status Information:*
• Your application is being processed
• You'll receive updates via SMS
• Contact support for any queries: {Config.SUPPORT_PHONE}"""
                
                keyboard = [
                    [InlineKeyboardButton(" Back to Disaster Management", callback_data="disaster")],
                    [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if is_callback:
                    await update.callback_query.edit_message_text(status_msg, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await update.message.reply_text(status_msg, reply_markup=reply_markup, parse_mode='Markdown')
                
            else:
                # Status check failed
                error_details = status_result.get("details", "Unknown error")
                logger.error(f" NC Exgratia status check failed: {error_details}")
                
                error_msg = f""" *Status Check Failed*

Unable to retrieve status for application: {reference_number}

*Error Details:*
{error_details}

*What to do:*
1. Verify the reference number is correct
2. Try again in a few minutes
3. Contact support: {Config.SUPPORT_PHONE}"""
                
                keyboard = [
                    [InlineKeyboardButton(" Try Again", callback_data="check_status")],
                    [InlineKeyboardButton(" Back to Disaster Management", callback_data="disaster")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if is_callback:
                    await update.callback_query.edit_message_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await update.message.reply_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f" Error checking application status: {str(e)}")
            error_msg = f""" *Status Check Error*

An unexpected error occurred while checking status.

*Error:*
{str(e)}

Contact support: {Config.SUPPORT_PHONE}"""
            
            keyboard = [
                [InlineKeyboardButton(" Try Again", callback_data="check_status")],
                [InlineKeyboardButton(" Back to Disaster Management", callback_data="disaster")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if is_callback:
                await update.callback_query.edit_message_text(error_msg, reply_markup=reply_markup, parse_mode='Markdown')
            else:
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
            help_msg = f""" *NC Exgratia Status Check*

To check your application status, use:
`/status <reference_number>`

*Example:*
`/status SK2025MN0003`

*Or use the menu:*
Disaster Management → Check Status"""
            
            keyboard = [[InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(help_msg, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Get reference number from command arguments
        reference_number = context.args[0].strip()
        
        # Check status
        await self.check_nc_exgratia_status(update, context, reference_number)

    async def _complete_complaint_without_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete complaint workflow without location"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        
        # Generate complaint ID
        complaint_id = f"CMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Send confirmation
        entered_name = state.get('entered_name', '')
        telegram_username = state.get('telegram_username', '')
        confirmation = self.responses[user_lang]['complaint_success'].format(
            complaint_id=complaint_id,
            name=entered_name,
            mobile=state.get('mobile'),
            telegram_username=telegram_username
        )
        
        keyboard = [[InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Log to Google Sheets
        user_name = f"{entered_name} (@{telegram_username})"
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="complaint",
            query_text=state.get('complaint_description', ''),
            language=user_lang,
            bot_response=confirmation,
            complaint_type="General",
            status="New",
            latitude=None,
            longitude=None
        )
        
        # Clear user state
        self._clear_user_state(user_id)

    async def _complete_emergency_without_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete emergency report without location and show emergency services menu"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        
        # Set location as "Not provided" in state
        state = self._get_user_state(user_id)
        state["location"] = "Location not provided"
        self._set_user_state(user_id, state)
        
        # Show emergency services menu
        await self.show_emergency_services_menu(update, context)

    async def _complete_complaint_with_manual_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete complaint workflow with manual location"""
        user_id = update.effective_user.id
        user_lang = self._get_user_language(user_id)
        state = self._get_user_state(user_id)
        
        # Generate complaint ID
        complaint_id = f"CMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Send confirmation
        entered_name = state.get('entered_name', '')
        telegram_username = state.get('telegram_username', '')
        manual_location = state.get('manual_location', 'Not provided')
        confirmation = self.responses[user_lang]['complaint_success'].format(
            complaint_id=complaint_id,
            name=entered_name,
            mobile=state.get('mobile'),
            telegram_username=telegram_username
        )
        
        # Add location info
        confirmation += f"\n **Location**: {manual_location}"
        
        keyboard = [[InlineKeyboardButton(" Back to Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Log to Google Sheets
        user_name = f"{entered_name} (@{telegram_username})"
        self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="complaint",
            query_text=state.get('complaint_description', ''),
            language=user_lang,
            bot_response=confirmation,
            complaint_type="General",
            status="New",
            latitude=None,
            longitude=None,
            location_name=manual_location
        )
        
        # Clear user state
        self._clear_user_state(user_id)

    # New Certificate Workflow Functions
    async def handle_certificate_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, cert_type: str):
        """Handle certificate type selection and show block selection directly"""
        print(f"DEBUG: handle_certificate_type_selection called with cert_type: {cert_type}")
        try:
            user_id = update.effective_user.id
            print(f"DEBUG: User ID: {user_id}")
            
            # Set state for certificate application
            self._set_user_state(user_id, {
                "workflow": "certificate_csc_application",
                "certificate_type": cert_type,
                "step": "block_selection"
            })
            print(f"DEBUG: State set for user {user_id}: certificate_csc_application")
            
            # Available blocks for certificate application (from Details for Smart Govt Assistant)
            available_blocks = [
                "Yuksam",
                "Gyalshing", 
                "Dentam",
                "Hee Martam",
                "Arithang Chongrang",
                "Gyalshing Municipal Council"
            ]
            
            text = f""" **CSC Application Flow**

**Certificate:** {cert_type}

**Step 1: Block Selection**
                
Please choose your block:"""
            
            # Create keyboard with blocks
            keyboard = []
            for i, block in enumerate(available_blocks):
                keyboard.append([InlineKeyboardButton(block, callback_data=f"cert_block_{i}")])
            
            # Store available blocks in user state
            state = self._get_user_state(user_id)
            state["available_blocks"] = available_blocks
            self._set_user_state(user_id, state)
            
            keyboard.append([InlineKeyboardButton(" Back", callback_data="certificate_csc")])
            keyboard.append([InlineKeyboardButton(" Main Menu", callback_data="main_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            print(f"DEBUG: About to edit message with text length: {len(text)}")
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            print(f"DEBUG: Message edited successfully")
            print(f"DEBUG: handle_certificate_type_selection completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_certificate_type_selection: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: send a new message
            try:
                await update.callback_query.answer("Error occurred, please try again")
                await update.callback_query.message.reply_text(" Error occurred. Please try again from the main menu.", parse_mode='Markdown')
            except:
                pass

    async def handle_certificate_block_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, block_index: str):
        """Handle certificate block selection and show GPU selection"""
        print(f"DEBUG: handle_certificate_block_selection called with block_index: {block_index}")
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        print(f"DEBUG: User ID: {user_id}")
        print(f"DEBUG: Current state: {state}")
        
        if state.get("workflow") != "certificate_csc_application":
            return
        
        # Get the actual block name from the index
        available_blocks = state.get("available_blocks", [])
        try:
            block_index = int(block_index)
            block_name = available_blocks[block_index]
        except (ValueError, IndexError):
            await update.callback_query.answer("Invalid block selection")
            return
        
        # Update state with selected block
        state["block"] = block_name
        state["step"] = "gpu_selection"
        self._set_user_state(user_id, state)
        
        # Get GPUs for the selected block from CSC details
        print(f"DEBUG: Looking for GPUs for block: {block_name}")
        print(f"DEBUG: Available blocks in CSV: {self.csc_details_df['BLOCK'].unique()}")
        
        block_gpus = self.csc_details_df[
            self.csc_details_df['BLOCK'].str.lower() == block_name.lower()
        ]['GPU Name'].dropna().unique().tolist()
        
        print(f"DEBUG: Found GPUs (exact match): {block_gpus}")
        
        # If no exact match found, try partial matching
        if not block_gpus:
            block_gpus = self.csc_details_df[
                self.csc_details_df['BLOCK'].str.contains(block_name, case=False, na=False, regex=False)
            ]['GPU Name'].dropna().unique().tolist()
            print(f"DEBUG: Found GPUs (partial match): {block_gpus}")
        
        # If still no GPUs found, show error message
        if not block_gpus:
            text = f""" **No GPUs Found**

Sorry, no GPUs were found for the block: **{block_name}**

Please try selecting a different block or contact support."""
            
            keyboard = [
                [InlineKeyboardButton(" Back to Blocks", callback_data="certificate_csc")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Clean GPU names by removing leading digits and dots
        cleaned_gpus = []
        for gpu in block_gpus:
            cleaned_gpu = re.sub(r'^\d+\.\s*', '', gpu.strip())
            cleaned_gpus.append(cleaned_gpu)
        
        block_gpus = sorted(cleaned_gpus)
        
        text = f""" **CSC Application Flow**

**Certificate:** {state.get('certificate_type', 'Unknown')}
**Block:** {block_name}

**Step 2: GPU Selection**

Select your GPU:
(Options populate based on selected block)

Please choose your GPU:"""
        
        # Create keyboard with GPUs
        keyboard = []
        for i, gpu in enumerate(block_gpus):
            keyboard.append([InlineKeyboardButton(gpu, callback_data=f"cert_gpu_{i}")])
        
        # Store GPUs in user state
        state["available_gpus"] = block_gpus
        self._set_user_state(user_id, state)
        
        keyboard.append([InlineKeyboardButton(" Back to Blocks", callback_data="certificate_csc")])
        keyboard.append([InlineKeyboardButton(" Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_certificate_gpu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, gpu_index: str):
        """Handle certificate GPU selection and show CSC info"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        if state.get("workflow") != "certificate_csc_application":
            return
        
        # Get the actual GPU name from the index
        available_gpus = state.get("available_gpus", [])
        try:
            gpu_index = int(gpu_index)
            gpu_name = available_gpus[gpu_index]
        except (ValueError, IndexError):
            await update.callback_query.answer("Invalid GPU selection")
            return
        
        # Update state with selected GPU
        state["gpu"] = gpu_name
        state["step"] = "csc_info"
        self._set_user_state(user_id, state)
        
        # Get CSC info for the selected GPU
        csc_info = self.csc_details_df[
            self.csc_details_df['GPU Name'].str.strip() == gpu_name.strip()
        ]
        
        # If no exact match, try case-insensitive match
        if csc_info.empty:
            csc_info = self.csc_details_df[
                self.csc_details_df['GPU Name'].str.lower() == gpu_name.lower()
            ]
        
        # If still no match, try partial match
        if csc_info.empty:
            csc_info = self.csc_details_df[
                self.csc_details_df['GPU Name'].str.contains(gpu_name, case=False, na=False, regex=False)
            ]
        
        # If still no match, try matching cleaned version
        if csc_info.empty:
            csc_info = self.csc_details_df[
                self.csc_details_df['GPU Name'].apply(lambda x: re.sub(r'^\d+\.\s*', '', x.strip()) if pd.notna(x) else '') == gpu_name.strip()
            ]
        
        if not csc_info.empty:
            info = csc_info.iloc[0]
            
            # Get block single window and subdivision single window contacts
            block_contacts = info.get('Block Single Window', 'N/A')
            subdivision_contacts = info.get('SubDivision Single Window', 'N/A')
            
            # Truncate long contact strings to avoid message length issues
            if len(block_contacts) > 50:
                block_contacts = block_contacts[:50] + "..."
            if len(subdivision_contacts) > 50:
                subdivision_contacts = subdivision_contacts[:50] + "..."
            
            text = f""" **Step 3: CSC Operator Details**

**Certificate:** {state.get('certificate_type', 'Unknown')}
**Block:** {info.get('BLOCK', 'N/A')}
**GPU:** {info.get('GPU Name', gpu_name)}

**You may contact your CSC Operator:**
• **Name:** {info.get('Name', 'N/A')}
• **Phone:** {info.get('Contact No.', 'N/A')}
• **GPU:** {info.get('GPU Name', gpu_name)}

**Alternative Contacts:**
If CSC Operator not responding, contact:
• **Block Single Window Office:** {block_contacts}
• **Subdivision Single Window Office:** {subdivision_contacts}

**Step 4: Application Confirmation**
Would you like to apply from here?"""
            
            keyboard = [
                [InlineKeyboardButton(" Yes, Apply Now", callback_data="cert_apply_now")],
                [InlineKeyboardButton(" Back to GPUs", callback_data="certificate_csc")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
        else:
            text = f""" **CSC Operator Not Found**

**Certificate:** {state.get('certificate_type', 'Unknown')}
**Block:** {state.get('block', 'N/A')}
**GPU:** {gpu_name}

No CSC operator found for this GPU. Please try another GPU or contact support."""
            
            keyboard = [
                [InlineKeyboardButton(" Back to GPUs", callback_data="certificate_csc")],
                [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_certificate_apply_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start certificate application details collection"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        print(f"DEBUG: handle_certificate_apply_now called")
        print(f"DEBUG: User ID: {user_id}")
        print(f"DEBUG: Current state: {state}")
        print(f"DEBUG: Expected workflow: certificate_csc_application, Got: {state.get('workflow')}")
        
        if state.get("workflow") != "certificate_csc_application":
            print(f"DEBUG: Invalid workflow state in apply_now - returning early")
            return
        
        # Update state to start collecting details
        state["step"] = "name"
        self._set_user_state(user_id, state)
        
        text = f""" **Step 5: Basic Details Collection**

**Certificate:** {state.get('certificate_type', 'Unknown')}
**Block:** {state.get('block', 'N/A')}
**GPU:** {state.get('gpu', 'N/A')}

**Please share your:**

**Name:**"""
        
        keyboard = [[InlineKeyboardButton(" Cancel", callback_data="certificate_csc")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_certificate_application_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle certificate application workflow"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        print(f"DEBUG: handle_certificate_application_workflow called")
        print(f"DEBUG: User ID: {user_id}")
        print(f"DEBUG: Current state: {state}")
        print(f"DEBUG: User input text: {text}")
        print(f"DEBUG: Expected workflow: certificate_csc_application, Got: {state.get('workflow')}")
        
        if state.get("workflow") != "certificate_csc_application":
            print(f"DEBUG: Invalid workflow state - returning early")
            return
        
        step = state.get("step")
        cert_type = state.get("certificate_type", "Unknown")
        print(f"DEBUG: Current step: {step}, Certificate type: {cert_type}")
        
        if step == "name":
            state["name"] = text
            state["step"] = "father_name"
            self._set_user_state(user_id, state)
            
            await update.message.reply_text("**Father's Name:**", parse_mode='Markdown')
            
        elif step == "father_name":
            state["father_name"] = text
            state["step"] = "phone"
            self._set_user_state(user_id, state)
            
            await update.message.reply_text("**Phone Number (WhatsApp):**", parse_mode='Markdown')
            
        elif step == "phone":
            state["phone"] = text
            state["step"] = "village"
            self._set_user_state(user_id, state)
            
            await update.message.reply_text("**Village:**", parse_mode='Markdown')
            
        elif step == "village":
            state["village"] = text
            self._set_user_state(user_id, state)
            
            # Submit certificate application
            await self.submit_certificate_application(update, context, state)

    async def submit_certificate_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict):
        """Submit certificate application to Google Sheets"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Unknown"
        cert_type = state.get("certificate_type", "Unknown")
        applicant_name = state.get("name", "Unknown")
        father_name = state.get("father_name", "Unknown")
        phone = state.get("phone", "Unknown")
        village = state.get("village", "Unknown")
        gpu = state.get("gpu", "Unknown")
        block = state.get("block", "Unknown")
        
        # Generate reference number (similar to schemes)
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        reference_number = f"CERT{timestamp}{user_id % 1000:03d}"
        
        # Log to Google Sheets using new structure
        success = self._log_to_sheets(
            user_id=user_id,
            user_name=user_name,
            interaction_type="certificate_application",
            query_text=f"Certificate application: {cert_type}",
            language="english",
            bot_response=f"Application submitted for {cert_type} via CSC",
            certificate_type=cert_type,
            applicant_name=applicant_name,
            father_name=father_name,
            phone=phone,
            village=village,
            gpu=gpu,
            block=block,
            reference_number=reference_number,
            application_status="Submitted",
            submission_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        if success:
            text = f""" **Application Submitted Successfully!**

**Certificate:** {cert_type}
**Name:** {applicant_name}
**Father's Name:** {father_name}
**Phone:** {phone}
**Village:** {village}
**Block:** {block}
**GPU:** {gpu}

 **Reference Number:** `{reference_number}`

** How to track your application:**
• Use the 'Check Status of My Application' option
• Enter your reference number: `{reference_number}`
• CSC operator will update the status in our system

**Status:** Application Received
**Next Step:** CSC Operator will contact you within 24-48 hours"""
            
            keyboard = [[InlineKeyboardButton(" Main Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            text = f""" **Application Submission Failed**

**Reference Number:** {reference_number}

Please try again or contact support. Your reference number has been saved for tracking."""
            
            keyboard = [[InlineKeyboardButton(" Main Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_certificate_online_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE, cert_type: str):
        """Handle certificate online application - redirect to sso.sikkim.gov.in"""
        text = f""" **Apply for the Certificates**

**Certificate:** {cert_type}

**To apply for any certificate online:**
 **Visit: sso.sikkim.gov.in**

**Steps to Apply Online:**
1. Create your account (one-time)
2. Log in using your mobile number and OTP
3. Select the certificate you want to apply for
4. Fill in details and upload required documents
5. You can track your application status anytime

**Ready to apply?**"""
        
        keyboard = [
            [InlineKeyboardButton("Apply Now", url="https://sso.sikkim.gov.in")],
            [InlineKeyboardButton("Need Help? Apply via CSC", callback_data=f"cert_csc_{cert_type}")],
            [InlineKeyboardButton(" Back", callback_data="certificate_csc")],
            [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_certificate_csc_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE, cert_type: str):
        """Handle certificate CSC application - start the CSC workflow"""
        user_id = update.effective_user.id
        
        # Set state for certificate CSC application
        self._set_user_state(user_id, {
            "workflow": "certificate_csc_application",
            "certificate_type": cert_type,
            "step": "block_selection"
        })
        
        # Available blocks for certificate application (from Details for Smart Govt Assistant)
        available_blocks = [
            "Yuksam",
            "Gyalshing", 
            "Dentam",
            "Hee Martam",
            "Arithang Chongrang",
            "Gyalshing Municipal Council"
        ]
        
        text = f""" **CSC Application Flow**

**Certificate:** {cert_type}

**Step 1: Block Selection**

Please choose your block:"""
        
        # Create keyboard with blocks
        keyboard = []
        for i, block in enumerate(available_blocks):
            keyboard.append([InlineKeyboardButton(block, callback_data=f"cert_block_{i}")])
        
        # Store available blocks in user state
        state = self._get_user_state(user_id)
        state["available_blocks"] = available_blocks
        self._set_user_state(user_id, state)
        
        keyboard.append([InlineKeyboardButton(" Back", callback_data="certificate_csc")])
        keyboard.append([InlineKeyboardButton(" Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # NEW SIMPLE CSC CONTACTS FUNCTIONS
    async def handle_contacts_csc_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Simple CSC contacts menu - show block selection"""
        user_id = update.effective_user.id
        
        # Available blocks
        available_blocks = [
            "Yuksam",
            "Gyalshing", 
            "Dentam",
            "Hee Martam",
            "Arithang Chongrang",
            "Gyalshing Municipal Council"
        ]
        
        # Set state exactly like certificates
        self._set_user_state(user_id, {
            "workflow": "certificate_csc_application", 
            "step": "block_selection",
            "available_blocks": available_blocks
        })
        
        text = """ **Know Your CSC Operator**

**Step 1: Block Selection**

Please choose your block:"""
        
        # Create keyboard with blocks
        keyboard = []
        for i, block in enumerate(available_blocks):
            keyboard.append([InlineKeyboardButton(block, callback_data=f"csc_block_{i}")])
        
        keyboard.append([InlineKeyboardButton(" Back to Contacts", callback_data="contacts")])
        keyboard.append([InlineKeyboardButton(" Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_contacts_csc_block_selection_simple(self, update: Update, context: ContextTypes.DEFAULT_TYPE, block_index: str):
        """Simple block selection for CSC contacts"""
        print(f" [DEBUG] handle_contacts_csc_block_selection_simple called with block_index: {block_index}")
        
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        # Available blocks
        available_blocks = [
            "Yuksam",
            "Gyalshing", 
            "Dentam",
            "Hee Martam",
            "Arithang Chongrang",
            "Gyalshing Municipal Council"
        ]
        
        try:
            block_index = int(block_index)
            block_name = available_blocks[block_index]
            print(f" [DEBUG] Selected block: {block_name}")
        except (ValueError, IndexError):
            print(f" [DEBUG] Invalid block_index: {block_index}")
            await update.callback_query.answer("Invalid block selection")
            return
        
        # Update state
        state["block"] = block_name
        state["step"] = "gpu_selection"
        self._set_user_state(user_id, state)
        
        # Map block names
        block_mapping = {
            'Arithang Chongrang': 'Chongrang',
            'Dentam': 'Dentam',
            'Gyalshing': 'Gyalshing',
            'Yuksam': 'Yuksam',
            'Hee Martam': 'Hee Martam',
            'Gyalshing Municipal Council': 'Gyalshing Municipal Council'
        }
        
        csc_block_name = block_mapping.get(block_name, block_name)
        print(f" [DEBUG] Mapped block name: {csc_block_name}")
        
        # Get GPUs from CSV
        block_gpus = self.csc_details_df[
            self.csc_details_df['BLOCK'].str.lower() == csc_block_name.lower()
        ]['GPU Name'].dropna().unique().tolist()
        
        print(f" [DEBUG] Found {len(block_gpus)} GPUs with exact match")
        
        # If no exact match, try partial matching
        if not block_gpus:
            block_gpus = self.csc_details_df[
                self.csc_details_df['BLOCK'].str.contains(csc_block_name, case=False, na=False, regex=False)
            ]['GPU Name'].dropna().unique().tolist()
            print(f" [DEBUG] Found {len(block_gpus)} GPUs with partial match")
        
        # Clean GPU names
        cleaned_gpus = []
        for gpu in block_gpus:
            cleaned_gpu = re.sub(r'^\d+\.\s*', '', gpu.strip())
            cleaned_gpus.append(cleaned_gpu)
        
        block_gpus = sorted(cleaned_gpus)
        print(f" [DEBUG] Final GPUs: {block_gpus}")
        
        if not block_gpus:
            print(f" [DEBUG] No GPUs found for block: {block_name}")
            text = f""" **No GPUs Found**

No GPUs found for block: **{block_name}**

Please try a different block."""
            keyboard = [
                [InlineKeyboardButton(" Back to Blocks", callback_data="contacts_csc")],
                [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        text = f""" **Know Your CSC Operator**

**Selected Block:** {block_name}

**Step 2: GPU Selection**

Please select your GPU (Gram Panchayat Unit):"""
        
        # Create keyboard with GPUs
        keyboard = []
        for i, gpu in enumerate(block_gpus):
            keyboard.append([InlineKeyboardButton(gpu, callback_data=f"contacts_csc_gpu_{i}")])
        
        # Store GPUs in state
        state["available_gpus"] = block_gpus
        self._set_user_state(user_id, state)
        
        keyboard.append([InlineKeyboardButton(" Back to Blocks", callback_data="contacts_csc")])
        keyboard.append([InlineKeyboardButton(" Back to Contacts", callback_data="contacts")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        print(f" [DEBUG] Sending GPU selection menu with {len(block_gpus)} GPUs")
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_csc_contacts_block_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, block_index: str):
        """Handle CSC contacts block selection - using exact same pattern as certificates"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        # Available blocks
        available_blocks = [
            "Yuksam",
            "Gyalshing", 
            "Dentam",
            "Hee Martam",
            "Arithang Chongrang",
            "Gyalshing Municipal Council"
        ]
        
        try:
            block_index = int(block_index)
            block_name = available_blocks[block_index]
        except (ValueError, IndexError):
            await update.callback_query.answer("Invalid block selection")
            return
        
        # Update state
        state["block"] = block_name
        state["step"] = "gpu_selection"
        self._set_user_state(user_id, state)
        
        # Map block names to CSV format
        block_mapping = {
            'Arithang Chongrang': 'Chongrang',
            'Dentam': 'Dentam',
            'Gyalshing': 'Gyalshing',
            'Yuksam': 'Yuksam',
            'Hee Martam': 'Hee Martam',
            'Gyalshing Municipal Council': 'Gyalshing Municipal Council'
        }
        
        csc_block_name = block_mapping.get(block_name, block_name)
        
        # Get GPUs from CSV
        block_gpus = self.csc_details_df[
            self.csc_details_df['BLOCK'].str.lower() == csc_block_name.lower()
        ]['GPU Name'].dropna().unique().tolist()
        
        # If no exact match, try partial matching
        if not block_gpus:
            block_gpus = self.csc_details_df[
                self.csc_details_df['BLOCK'].str.contains(csc_block_name, case=False, na=False, regex=False)
            ]['GPU Name'].dropna().unique().tolist()
        
        # Clean GPU names
        cleaned_gpus = []
        for gpu in block_gpus:
            cleaned_gpu = re.sub(r'^\d+\.\s*', '', gpu.strip())
            cleaned_gpus.append(cleaned_gpu)
        
        block_gpus = sorted(cleaned_gpus)
        
        if not block_gpus:
            text = f""" **No GPUs Found**

No GPUs found for block: **{block_name}**

Please try a different block."""
            keyboard = [
                [InlineKeyboardButton(" Back to Blocks", callback_data="contacts_csc")],
                [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        text = f""" **Know Your CSC Operator**

**Selected Block:** {block_name}

**Step 2: GPU Selection**

Please select your GPU (Gram Panchayat Unit):"""
        
        # Create keyboard with GPUs
        keyboard = []
        for i, gpu in enumerate(block_gpus):
            keyboard.append([InlineKeyboardButton(gpu, callback_data=f"contacts_csc_gpu_{i}")])
        
        # Store GPUs in state
        state["available_gpus"] = block_gpus
        self._set_user_state(user_id, state)
        
        keyboard.append([InlineKeyboardButton(" Back to Blocks", callback_data="contacts_csc")])
        keyboard.append([InlineKeyboardButton(" Back to Contacts", callback_data="contacts")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_csc_contacts_gpu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, gpu_index: str):
        """Handle CSC contacts GPU selection - using exact same pattern as certificates"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        try:
            gpu_index = int(gpu_index)
            available_gpus = state.get("available_gpus", [])
            gpu_name = available_gpus[gpu_index]
        except (ValueError, IndexError):
            await update.callback_query.answer("Invalid GPU selection")
            return
        
        # Update state
        state["gpu"] = gpu_name
        state["step"] = "show_csc_info"
        self._set_user_state(user_id, state)
        
        # Get CSC details from CSV
        csc_info = self.csc_details_df[
            (self.csc_details_df['GPU Name'].str.contains(gpu_name, case=False, na=False, regex=False)) &
            (self.csc_details_df['BLOCK'].str.contains(state["block"], case=False, na=False, regex=False))
        ]
        
        if csc_info.empty:
            text = f""" **No CSC Information Found**

No CSC operator information found for:
- **Block:** {state["block"]}
- **GPU:** {gpu_name}

Please try a different GPU or block."""
            keyboard = [
                [InlineKeyboardButton(" Back to GPUs", callback_data="contacts_csc")],
                [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Get the first CSC operator info
        csc_row = csc_info.iloc[0]
        
        text = f""" **CSC Operator Information**

**Selected Block:** {state["block"]}
**Selected GPU:** {gpu_name}

**CSC Operator Details:**
• **Name:** {csc_row.get('Name', 'N/A')}
• **Contact:** {csc_row.get('Contact No.', 'N/A')}
• **Block Single Window:** {csc_row.get('Block Single Window', 'N/A')}
• **SubDivision Single Window:** {csc_row.get('SubDivision Single Window', 'N/A')}

You can contact this CSC operator for any government services."""
        
        keyboard = [
            [InlineKeyboardButton(" Back to GPUs", callback_data="contacts_csc")],
            [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")],
            [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def simple_csc_block_to_gpu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, block_index: str):
        """Simple function to map block names to GPUs"""
        print(f" [DEBUG] simple_csc_block_to_gpu called with block_index: {block_index}")
        
        # Available blocks
        available_blocks = [
            "Yuksam",
            "Gyalshing", 
            "Dentam",
            "Hee Martam",
            "Arithang Chongrang",
            "Gyalshing Municipal Council"
        ]
        
        try:
            block_index = int(block_index)
            block_name = available_blocks[block_index]
        except (ValueError, IndexError):
            await update.callback_query.answer("Invalid block selection")
            return
        
        # Map block names to CSV format
        block_mapping = {
            'Arithang Chongrang': 'Chongrang',
            'Dentam': 'Dentam',
            'Gyalshing': 'Gyalshing',
            'Yuksam': 'Yuksam',
            'Hee Martam': 'Hee Martam',
            'Gyalshing Municipal Council': 'Gyalshing Municipal Council'
        }
        
        csc_block_name = block_mapping.get(block_name, block_name)
        
        # Get GPUs from CSV
        block_gpus = self.csc_details_df[
            self.csc_details_df['BLOCK'].str.lower() == csc_block_name.lower()
        ]['GPU Name'].dropna().unique().tolist()
        
        # If no exact match, try partial matching
        if not block_gpus:
            block_gpus = self.csc_details_df[
                self.csc_details_df['BLOCK'].str.contains(csc_block_name, case=False, na=False, regex=False)
            ]['GPU Name'].dropna().unique().tolist()
        
        # Clean GPU names
        cleaned_gpus = []
        for gpu in block_gpus:
            cleaned_gpu = re.sub(r'^\d+\.\s*', '', gpu.strip())
            cleaned_gpus.append(cleaned_gpu)
        
        block_gpus = sorted(cleaned_gpus)
        
        if not block_gpus:
            text = f""" **No GPUs Found**

No GPUs found for block: **{block_name}**

Please try a different block."""
            keyboard = [
                [InlineKeyboardButton(" Back to Blocks", callback_data="contacts_csc")],
                [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        text = f""" **Know Your CSC Operator**

**Selected Block:** {block_name}

**Step 2: GPU Selection**

Select your GPU to see CSC operator details:

Please choose your GPU:"""
        
        # Create keyboard with GPUs as clickable buttons
        keyboard = []
        for i, gpu in enumerate(block_gpus):
            keyboard.append([InlineKeyboardButton(gpu, callback_data=f"csc_gpu_{i}")])
        
        keyboard.append([InlineKeyboardButton(" Back to Blocks", callback_data="contacts_csc")])
        keyboard.append([InlineKeyboardButton(" Back to Contacts", callback_data="contacts")])
        
        # Store GPUs in user state for GPU selection
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        state["available_gpus"] = block_gpus
        state["block"] = block_name
        self._set_user_state(user_id, state)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_csc_gpu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, gpu_index: str):
        """Handle CSC GPU selection and show CSC operator details"""
        print(f"DEBUG: handle_csc_gpu_selection called with gpu_index: {gpu_index}")
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        
        # Get the actual GPU name from the index
        available_gpus = state.get("available_gpus", [])
        print(f"DEBUG: Available GPUs from state: {available_gpus}")
        print(f"DEBUG: GPU index: {gpu_index}")
        try:
            gpu_index = int(gpu_index)
            gpu_name = available_gpus[gpu_index]
            print(f"DEBUG: Selected GPU name: {gpu_name}")
        except (ValueError, IndexError) as e:
            print(f"DEBUG: Error getting GPU name: {e}")
            await update.callback_query.answer("Invalid GPU selection")
            return
        
        # Get block name from state
        block_name = state.get("block", "Unknown")
        
        # Get CSC operator details for this GPU
        print(f"DEBUG: Looking for CSC details for GPU: {gpu_name}")
        
        # Find CSC operator details from CSV
        print(f"DEBUG: Searching CSV for GPU: {gpu_name}")
        csc_details = self.csc_details_df[
            (self.csc_details_df['GPU Name'].str.contains(gpu_name, case=False, na=False, regex=False)) |
            (self.csc_details_df['GPU Name'].str.lower() == gpu_name.lower())
        ]
        
        print(f"DEBUG: Found {len(csc_details)} matching records in CSV")
        
        if csc_details.empty:
            text = f""" **No CSC Details Found**

Sorry, no CSC operator details were found for GPU: **{gpu_name}**

Please try selecting a different GPU or contact support."""
            
            keyboard = [
                [InlineKeyboardButton(" Back to GPUs", callback_data="contacts_csc")],
                [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Get the first matching CSC operator
        csc_operator = csc_details.iloc[0]
        
        text = f""" **CSC Operator Details**

**Block:** {block_name}
**GPU:** {gpu_name}

**CSC Operator Information:**
• **Name:** {csc_operator.get('Name', 'Not Available')}
• **Contact:** {csc_operator.get('Contact No.', 'Not Available')}
• **Block Single Window:** {csc_operator.get('Block Single Window', 'Not Available')}
• **SubDivision Single Window:** {csc_operator.get('SubDivision Single Window', 'Not Available')}

You can contact this CSC operator for assistance with government services."""
        
        keyboard = [
            [InlineKeyboardButton(" Back to GPUs", callback_data="contacts_csc")],
            [InlineKeyboardButton(" Back to Contacts", callback_data="contacts")],
            [InlineKeyboardButton(" Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

if __name__ == "__main__":
    # Initialize and run bot
    bot = SajiloSewakBot()
    bot.run() 