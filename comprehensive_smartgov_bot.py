#!/usr/bin/env python3
"""
Comprehensive Sikkim SmartGov Assistant Bot
"""
import asyncio
import aiohttp
import json
import logging
import pandas as pd
import threading
import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import Config
from datetime import datetime
import time
import random # Added for complaint ID generation

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
        """Initialize the bot with configuration"""
        self.config = Config()
        self.application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        
        # Initialize user state storage
        self._user_states = {}
        logger.info("🔒 MULTI-USER SUPPORT: Thread-safe state management initialized")
        
        # Load data files
        self._load_data()
        
        # Register handlers
        self.register_handlers()

    def _load_data(self):
        """Load all required data files"""
        try:
            # Load emergency services data
            with open('data/emergency_services_text_responses.json', 'r', encoding='utf-8') as f:
                self.emergency_data = json.load(f)
            
            # Load homestay data
            self.homestay_df = pd.read_csv('data/homestays_by_place.csv')
            
            # Load CSC data
            self.csc_df = pd.read_csv('data/csc_contacts.csv')
            
            # Load ex-gratia info
            with open('data/info_opt1.txt', 'r', encoding='utf-8') as f:
                self.info_opt1 = f.read()
            with open('data/info_opt2.txt', 'r', encoding='utf-8') as f:
                self.info_opt2 = f.read()
            
            logger.info("✅ All data files loaded successfully")
        except Exception as e:
            logger.error(f"Error loading data files: {e}")
            raise

    def _initialize_responses(self):
        pass  # Removed responses dictionary

    def _get_user_state(self, user_id: int) -> dict:
        """Get user state from storage"""
        if not hasattr(self, '_user_states'):
            self._user_states = {}
        return self._user_states.get(user_id, {})

    def _set_user_state(self, user_id: int, state: dict):
        """Set user state in storage"""
        if not hasattr(self, '_user_states'):
            self._user_states = {}
        self._user_states[user_id] = state

    def _clear_user_state(self, user_id: int):
        """Clear user state from storage"""
        if not hasattr(self, '_user_states'):
            self._user_states = {}
        if user_id in self._user_states:
            del self._user_states[user_id]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"[USER] New conversation started by user {user.id}")
        self._clear_user_state(user.id)
        
        welcome_text = """🏛️ *Welcome to SmartGov Assistant* 🏛️

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

Please select a service to continue:"""

        keyboard = [
            [InlineKeyboardButton("🏡 Book Homestay", callback_data='tourism')],
            [InlineKeyboardButton("🚨 Emergency Services", callback_data='emergency')],
            [InlineKeyboardButton("📝 Report a Complaint", callback_data='complaint')],
            [InlineKeyboardButton("💻 Apply for Certificate", callback_data='certificate')],
            [InlineKeyboardButton("🆘 Disaster Management", callback_data='disaster')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        user_id = update.effective_user.id
        text = update.message.text
        logger.info(f"[MSG] Received from {user_id}: {text}")
        
        state = self._get_user_state(user_id)
        logger.info(f"[STATE] Current for user {user_id}: {state}")

        if not state or text.lower() in ['hello', 'hi', 'start', '/start']:
            # First interaction or greeting, show all services
            await self.start(update, context)
            return

        if state.get("workflow"):
            # Handle ongoing workflows
            workflow = state.get("workflow")
            logger.info(f"[WORKFLOW] Continuing {workflow} for user {user_id}")
            
            if workflow == "complaint":
                await self.handle_complaint_workflow(update, context)
            elif workflow == "certificate":
                await self.handle_certificate_workflow(update, context, text)
            elif workflow == "check_status":
                await self.process_status_check(update, context)
            elif workflow == "ex_gratia":
                await self.handle_ex_gratia_workflow(update, context, text)
            else:
                await self.show_main_menu(update, context)
        else:
            # For new requests, show main menu
            await self.show_main_menu(update, context)

    async def detect_language(self, text: str) -> str:
        """Detect language using the LLM."""
        return 'english'

    async def get_intent_from_llm(self, text: str, lang: str) -> str:
        """Get intent from LLM."""
        return 'unknown'
        
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the main menu"""
        await self.start(update, context)

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
        """Show disaster relief norms"""
        text = """*Disaster Relief Norms* ℹ️

The Government of Sikkim provides relief assistance for:

1. House Damage
   • Fully Damaged: Up to ₹25,000
   • Severely Damaged: Up to ₹15,000
   • Partially Damaged: Up to ₹4,000

2. Crop Loss
   • Above 2 hectares: Up to ₹15,000
   • 1-2 hectares: Up to ₹10,000
   • Below 1 hectare: Up to ₹4,000

3. Livestock Loss
   • Large animals: Up to ₹15,000
   • Small animals: Up to ₹2,000

For more details, please visit your nearest District Administration office."""

        keyboard = [
            [InlineKeyboardButton("📝 Apply Now", callback_data="ex_gratia")],
            [InlineKeyboardButton("🔙 Back to Disaster Menu", callback_data="disaster")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

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
        text = """*Ex-Gratia Assistance* 📝

You may be eligible if you've suffered losses due to:
• Heavy rainfall, floods, or landslides
• Earthquakes or other natural calamities
• Crop damage from hailstorms
• House damage from natural disasters
• Loss of livestock

Would you like to proceed with the application?"""

        keyboard = [
            [InlineKeyboardButton("✅ Yes, Continue", callback_data="ex_gratia_start")],
            [InlineKeyboardButton("❌ No, Go Back", callback_data="disaster")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # --- Ex-Gratia Application ---
    async def start_ex_gratia_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the ex-gratia application workflow"""
        user_id = update.effective_user.id
        self._set_user_state(user_id, {"workflow": "ex_gratia", "step": "name"})
        
        text = """*Ex-Gratia Application Form* 📝

Please enter your full name:"""
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="disaster")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_ex_gratia_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle the ex-gratia application workflow"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        step = state.get("step")
        data = state.get("data", {})

        if step == "name":
            data["name"] = text
            state["step"] = "father_name"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text("What is your father's name?", parse_mode='Markdown')

        elif step == "father_name":
            data["father_name"] = text
            state["step"] = "village"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text("Which village are you from?", parse_mode='Markdown')

        elif step == "village":
            data["village"] = text
            state["step"] = "contact"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text("What is your contact number? (10 digits)", parse_mode='Markdown')

        elif step == "contact":
            if not text.isdigit() or len(text) != 10:
                await update.message.reply_text("Please enter a valid 10-digit mobile number.", parse_mode='Markdown')
                return
            
            data["contact"] = text
            state["step"] = "ward"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text("What is your Ward number or name?", parse_mode='Markdown')

        elif step == "ward":
            data["ward"] = text
            state["step"] = "gpu"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text("Which Gram Panchayat Unit (GPU) are you under?", parse_mode='Markdown')

        elif step == "gpu":
            data["gpu"] = text
            state["step"] = "khatiyan"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text("What is your Khatiyan Number? (Land record number)", parse_mode='Markdown')

        elif step == "khatiyan":
            data["khatiyan_no"] = text
            state["step"] = "plot"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text("What is your Plot Number?", parse_mode='Markdown')

        elif step == "plot":
            data["plot_no"] = text
            state["step"] = "damage_type"
            state["data"] = data
            self._set_user_state(user_id, state)
            await self.show_damage_type_options(update, context)

        elif step == "damage_type":
            data["damage_type"] = text
            state["step"] = "damage_description"
            state["data"] = data
            self._set_user_state(user_id, state)
            await update.message.reply_text("Please provide a detailed description of the damage:", parse_mode='Markdown')

        elif step == "damage_description":
            data["damage_description"] = text
            state["data"] = data
            self._set_user_state(user_id, state)
            await self.show_ex_gratia_confirmation(update, context, data)

        else:
            await update.message.reply_text("An error occurred. Please start over.", parse_mode='Markdown')
            self._clear_user_state(user_id)

    async def show_damage_type_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🏠 House Damage (₹4,000 - ₹25,000)", callback_data='damage_type_house')],
            [InlineKeyboardButton("🌾 Crop Loss (₹4,000 - ₹15,000)", callback_data='damage_type_crop')],
            [InlineKeyboardButton("🐄 Livestock Loss (₹2,000 - ₹15,000)", callback_data='damage_type_livestock')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Please select the type of damage:", reply_markup=reply_markup)

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
        summary = """*Please Review Your Application* 📋

*Personal Details:*
👤 Name: {name}
👨‍👦 Father's Name: {father}
📍 Village: {village}
📱 Contact: {contact}

*Land Details:*
🏘️ Ward: {ward}
🏛️ GPU: {gpu}
📄 Khatiyan Number: {khatiyan}
🗺️ Plot Number: {plot}

*Damage Details:*
🏷️ Type: {damage_type}
📝 Description: {damage}

Please verify all details carefully. Would you like to:""".format(
            name=data.get('name', 'N/A'),
            father=data.get('father_name', 'N/A'),
            village=data.get('village', 'N/A'),
            contact=data.get('contact', 'N/A'),
            ward=data.get('ward', 'N/A'),
            gpu=data.get('gpu', 'N/A'),
            khatiyan=data.get('khatiyan_no', 'N/A'),
            plot=data.get('plot_no', 'N/A'),
            damage_type=data.get('damage_type', 'N/A'),
            damage=data.get('damage_description', 'N/A')
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Submit Application", callback_data='ex_gratia_submit')],
            [InlineKeyboardButton("✏️ Edit Details", callback_data='ex_gratia_edit')],
            [InlineKeyboardButton("❌ Cancel", callback_data='ex_gratia_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')

    async def submit_ex_gratia_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Submit the ex-gratia application"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        data = state.get("data", {})

        try:
            # Generate application ID
            now = datetime.now()
            app_id = f"EXG{now.strftime('%Y%m%d')}{random.randint(1000,9999)}"
            
            # Save to CSV
            df = pd.DataFrame([{
                'ApplicationID': app_id,
                'ApplicantName': data.get('name'),
                'FatherName': data.get('father_name'),
                'Village': data.get('village'),
                'Contact': data.get('contact'),
                'Ward': data.get('ward'),
                'GPU': data.get('gpu'),
                'KhatiyanNo': data.get('khatiyan_no'),
                'PlotNo': data.get('plot_no'),
                'DamageDescription': data.get('damage_description'),
                'SubmissionTimestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'Pending'
            }])
            
            df.to_csv('data/exgratia_applications.csv', mode='a', header=False, index=False)
            
            # Send confirmation
            confirmation = f"""✅ *Application Submitted Successfully!*

🆔 Application ID: {app_id}
👤 Name: {data.get('name')}

*Next Steps:*
1. Your data will be verified
2. Update in 7-10 days
3. SMS will be sent to your number

Support: +91-1234567890"""

            keyboard = [[InlineKeyboardButton("🔙 Back to Disaster Management", callback_data="disaster")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await update.message.reply_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Clear user state
            self._clear_user_state(user_id)
            
        except Exception as e:
            logger.error(f"Error submitting application: {str(e)}")
            error_msg = "Sorry, there was an error submitting your application. Please try again."
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text(error_msg, parse_mode='Markdown')

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
        keyboard = [
            [InlineKeyboardButton("🚑 Ambulance", callback_data="emergency_medical")],
            [InlineKeyboardButton("👮 Police Helpline", callback_data="emergency_police")],
            [InlineKeyboardButton("💭 Suicide Prevention", callback_data="emergency_suicide")],
            [InlineKeyboardButton("🏥 Health Helpline", callback_data="emergency_health")],
            [InlineKeyboardButton("👩 Women Helpline", callback_data="emergency_women")],
            [InlineKeyboardButton("🚒 Fire Emergency", callback_data="emergency_fire")],
            [InlineKeyboardButton("🆘 Report Disaster", callback_data="emergency_disaster")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """*Emergency Services* 🚨

Select the type of emergency service you need:"""
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_emergency_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service_type: str):
        """Handle specific emergency service selection"""
        query = update.callback_query
        
        if service_type in ['medical', 'disaster']:
            response_text = self.emergency_data[service_type]['english']
        else:
            # Default emergency numbers for other services
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

    # --- Tourism & Homestays ---
    async def handle_tourism_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle homestay booking menu"""
        places = pd.read_csv('data/homestays_by_place.csv')['Place'].unique()
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
        
        homestays = pd.read_csv('data/homestays_by_place.csv')
        place_homestays = homestays[homestays['Place'] == place]
        
        text = f"*Available Homestays in {place}* 🏡\n\n"
        for _, row in place_homestays.iterrows():
            text += f"*{row['HomestayName']}*\n"
            text += f"⭐ Rating: {row['Rating']}\n"
            text += f"💰 Price per night: ₹{row['PricePerNight']}\n"
            text += f"📞 Contact: {row['ContactNumber']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔍 Search Another Place", callback_data="tourism")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

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
        text = """*Apply for Certificate through Sikkim SSO* 💻

To apply for services through the Sikkim SSO portal:
1. Register and create an account on the Sikkim SSO portal
2. Log in using your Sikkim SSO credentials
3. Navigate to the desired service
4. Fill out the application form
5. Upload necessary documents
6. Track your application status online

Would you like to apply through a CSC operator or Single Window operator?"""

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

    async def handle_certificate_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle certificate application workflow"""
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        if state.get("stage") == "gpu":
            gpu = text.strip().upper()
            csc_info = self.csc_df[self.csc_df['GPU'].str.upper() == gpu]
            if csc_info.empty:
                await update.message.reply_text("Sorry, no CSC operator found for your GPU.")
            else:
                info = csc_info.iloc[0]
                message = f"CSC Operator Details:\n\nName: {info['CSC_Operator_Name']}\nContact: {info['PhoneNumber']}\nTimings: {info['Timings']}"
                await update.message.reply_text(message)
            self._clear_user_state(user_id)

    async def handle_certificate_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str):
        if choice == 'yes':
            self._set_user_state(update.effective_user.id, {"workflow": "certificate", "stage": "gpu"})
            await update.callback_query.edit_message_text("Please enter your GPU (Gram Panchayat Unit):", parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text("You can apply directly on the Sikkim SSO Portal: https://sso.sikkim.gov.in", parse_mode='Markdown')
        
    async def handle_certificate_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        user_id = update.effective_user.id
        state = self._get_user_state(user_id)
        if state.get("stage") == "gpu":
            gpu = text.strip().upper()
            csc_info = self.csc_df[self.csc_df['GPU'].str.upper() == gpu]
            if csc_info.empty:
                await update.message.reply_text("Sorry, no CSC operator found for your GPU.")
            else:
                info = csc_info.iloc[0]
                message = f"CSC Operator Details:\n\nName: {info['CSC_Operator_Name']}\nContact: {info['PhoneNumber']}\nTimings: {info['Timings']}"
                await update.message.reply_text(message)
            self._clear_user_state(user_id)

    # --- Complaint ---
    async def start_complaint_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the complaint registration workflow"""
        user_id = update.effective_user.id
        self._set_user_state(user_id, {"workflow": "complaint", "step": "name"})
        
        text = """*Report a Complaint/Grievance* 📝

Please enter your full name:"""
        
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_complaint_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the complaint workflow steps"""
        user_id = update.effective_user.id
        text = update.message.text
        state = self._get_user_state(user_id)
        step = state.get("step")
        
        if step == "name":
            state["name"] = text
            state["step"] = "mobile"
            self._set_user_state(user_id, state)
            await update.message.reply_text("Please enter your mobile number:", parse_mode='Markdown')
        
        elif step == "mobile":
            if not text.isdigit() or len(text) != 10:
                await update.message.reply_text("Please enter a valid 10-digit mobile number.", parse_mode='Markdown')
                return
            
            state["mobile"] = text
            state["step"] = "complaint"
            self._set_user_state(user_id, state)
            await update.message.reply_text("Please describe your complaint in detail:", parse_mode='Markdown')
        
        elif step == "complaint":
            # Generate complaint ID
            now = datetime.now()
            complaint_id = f"CMP{now.strftime('%Y%m%d')}{random.randint(100, 999)}"
            
            # Save complaint to CSV
            complaint_data = {
                'Complaint_ID': complaint_id,
                'Name': state.get('name'),
                'Mobile': state.get('mobile'),
                'Complaint': text,
                'Date': now.strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'Pending'
            }
            
            df = pd.DataFrame([complaint_data])
            df.to_csv('data/submission.csv', mode='a', header=False, index=False)
            
            # Send confirmation
            confirmation = f"""✅ *Complaint Registered Successfully*

🆔 Complaint ID: {complaint_id}
👤 Name: {state.get('name')}
📱 Mobile: {state.get('mobile')}

Your complaint has been registered and will be processed soon. Please save your Complaint ID for future reference."""
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(confirmation, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Clear user state
            self._clear_user_state(user_id)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the bot"""
        logger.error(f"[ERROR] {context.error}", exc_info=context.error)
        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again later."
            )

    def register_handlers(self):
        """Register message and callback handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        self.application.add_handler(CallbackQueryHandler(self.callback_handler))
        self.application.add_error_handler(self.error_handler)  # Add error handler
        logger.info("✅ All handlers registered successfully")

    def run(self):
        """Start the bot"""
        logger.info("🚀 Starting Enhanced SmartGov Assistant Bot...")
        self.application.run_polling()
        logger.info("🤖 Enhanced SmartGov Assistant is running...")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    # Create and run bot
    bot = SmartGovAssistantBot()
    print("🚀 Starting Enhanced SmartGov Assistant Bot...")
    print("🤖 Enhanced SmartGov Assistant is running...")
    print("📱 Bot Link: https://t.me/smartgov_assistant_bot")
    print("✅ Ready to serve citizens!")
    bot.run() 