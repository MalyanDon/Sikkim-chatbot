#!/usr/bin/env python3
"""
Complete SajiloSewa Chatbot - Comprehensive Government Services
Multi-service Telegram bot for all Sikkim government citizen services
"""

import asyncio
import json
import time
import logging
import nest_asyncio
import pandas as pd
import csv
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Fix for Windows event loop issues
nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ComprehensiveSajiloSewaBot:
    def __init__(self):
        # Bot configuration
        self.BOT_TOKEN = "7641958089:AAH2UW5H0EX9pGfE6wZZaURCpkyMHtJK8zw"
        
        # Data initialization
        self._initialize_data_files()
        
    def _initialize_data_files(self):
        """Initialize CSV files for different services"""
        if not os.path.exists('data'):
            os.makedirs('data')
            
        # Initialize ex-gratia data
        if not os.path.exists('data/submission.csv'):
            with open('data/submission.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['submission_id', 'name', 'phone', 'submission_date', 'status', 'details'])

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main menu with all SajiloSewa services"""
        keyboard = [
            [InlineKeyboardButton("🚨 Disaster Management", callback_data="disaster_mgmt")],
            [InlineKeyboardButton("📜 Document Services", callback_data="document_services")],
            [InlineKeyboardButton("🏥 Healthcare Services", callback_data="healthcare")],
            [InlineKeyboardButton("🎓 Education Services", callback_data="education")],
            [InlineKeyboardButton("💼 Employment Services", callback_data="employment")],
            [InlineKeyboardButton("🏛️ Civic Services", callback_data="civic_services")],
            [InlineKeyboardButton("ℹ️ Help & Support", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = """🙏 **Welcome to SajiloSewa - Complete Government Services!**

**Your one-stop solution for all Sikkim Government services:**

🚨 **Disaster Management** - Ex-gratia, relief assistance
📜 **Document Services** - Certificates, licenses  
🏥 **Healthcare Services** - Medical assistance, schemes
🎓 **Education Services** - Scholarships, admissions
💼 **Employment Services** - Job opportunities, schemes  
🏛️ **Civic Services** - Complaints, public utilities

**Choose a service category to get started:**"""
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all button interactions"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "disaster_mgmt":
            await self.show_disaster_management(update, context)
        elif query.data == "document_services":
            await self.show_document_services(update, context)
        elif query.data == "healthcare":
            await self.show_healthcare_services(update, context)
        elif query.data == "education":
            await self.show_education_services(update, context)
        elif query.data == "employment":
            await self.show_employment_services(update, context)
        elif query.data == "civic_services":
            await self.show_civic_services(update, context)
        elif query.data == "help":
            await self.help_command(update, context)
        elif query.data == "back_to_main":
            await self.start_command(update, context)
        # Disaster Management sub-options
        elif query.data == "exgratia_norms":
            await self.show_exgratia_norms(update, context)
        elif query.data == "exgratia_apply":
            await self.show_exgratia_application(update, context)
        elif query.data == "exgratia_status":
            await self.ask_for_application_id(update, context)
        elif query.data == "emergency_services":
            await self.show_emergency_services(update, context)
        elif query.data == "back_to_disaster":
            await self.show_disaster_management(update, context)

    async def show_disaster_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disaster Management sub-menu"""
        keyboard = [
            [InlineKeyboardButton("💰 Ex-Gratia Assistance", callback_data="exgratia_submenu")],
            [InlineKeyboardButton("🚨 Emergency Services", callback_data="emergency_services")],
            [InlineKeyboardButton("🏠 Relief Camps Info", callback_data="relief_camps")],
            [InlineKeyboardButton("📊 Disaster Reports", callback_data="disaster_reports")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """🚨 **Disaster Management Services**

**Available Services:**

💰 **Ex-Gratia Assistance** - Financial relief for disaster victims
🚨 **Emergency Services** - Contact emergency helplines
🏠 **Relief Camps Info** - Information about relief camps
📊 **Disaster Reports** - Current disaster status & alerts

**Select a service:**"""
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_exgratia_submenu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ex-Gratia specific sub-menu"""
        keyboard = [
            [InlineKeyboardButton("📋 Ex-Gratia Norms", callback_data="exgratia_norms")],
            [InlineKeyboardButton("📝 Apply for Ex-Gratia", callback_data="exgratia_apply")],
            [InlineKeyboardButton("🔍 Check Application Status", callback_data="exgratia_status")],
            [InlineKeyboardButton("🔙 Back to Disaster Mgmt", callback_data="back_to_disaster")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """💰 **Ex-Gratia Assistance Services**

**Available Options:**

📋 **Ex-Gratia Norms** - Learn about assistance amounts & eligibility
📝 **Apply for Ex-Gratia** - Start your application process  
🔍 **Check Status** - Track your application progress

**Choose an option:**"""
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_exgratia_norms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show ex-gratia norms information"""
        try:
            with open('data/info_opt1.txt', 'r', encoding='utf-8') as file:
                norms_content = file.read()
        except FileNotFoundError:
            norms_content = """**Ex-Gratia Assistance Norms:**

Financial assistance ranges from ₹4,000 to ₹25,000 depending on:

**House Damage:**
- Partial damage: ₹4,000 - ₹12,000
- Severe damage: ₹15,000 - ₹25,000

**Crop Loss:**
- Per hectare loss: ₹4,000 - ₹8,000
- Complete failure: Up to ₹15,000

**Livestock Loss:**
- Large animals: ₹10,000 - ₹15,000
- Small animals: ₹2,000 - ₹5,000

**Timeline:** Apply within 30 days of incident."""

        keyboard = [
            [InlineKeyboardButton("📝 Apply Now", callback_data="exgratia_apply")],
            [InlineKeyboardButton("🔍 Check Status", callback_data="exgratia_status")],
            [InlineKeyboardButton("🔙 Back", callback_data="exgratia_submenu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"📋 **Ex-Gratia Assistance Norms**\n\n{norms_content}", 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )

    async def show_exgratia_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show ex-gratia application procedure"""
        try:
            with open('data/info_opt2.txt', 'r', encoding='utf-8') as file:
                procedure_content = file.read()
        except FileNotFoundError:
            procedure_content = """**Application Procedure:**

**Step 1:** Immediate Documentation
- Take photos of damage
- Contact local authorities

**Step 2:** Visit Office
- Go to nearest Gram Panchayat or BDO

**Step 3:** Required Documents
- Aadhaar card/Voter ID
- Bank account details
- Damage photos
- Land documents (if applicable)

**Step 4:** Assessment
- Official will visit for damage assessment

**Step 5:** Tracking
- You'll receive Application ID for tracking"""

        keyboard = [
            [InlineKeyboardButton("📋 View Norms", callback_data="exgratia_norms")],
            [InlineKeyboardButton("🔍 Check Status", callback_data="exgratia_status")],
            [InlineKeyboardButton("🔙 Back", callback_data="exgratia_submenu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"📝 **How to Apply for Ex-Gratia**\n\n{procedure_content}", 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )

    async def ask_for_application_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ask user for application ID to check status"""
        message = """🔍 **Application Status Check**

Please share your Application ID to check the status.

**Format:** Usually 8-10 characters (e.g., 23LDM786)

**Find your Application ID in:**
📄 Application receipt
📱 SMS confirmation  
📧 Email confirmation

**Type your Application ID:**"""

        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="exgratia_submenu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        context.user_data['waiting_for_app_id'] = True

    async def show_document_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Document Services menu"""
        keyboard = [
            [InlineKeyboardButton("🆔 Identity Documents", callback_data="identity_docs")],
            [InlineKeyboardButton("🏠 Residential Certificates", callback_data="residential_certs")],
            [InlineKeyboardButton("👥 Caste Certificates", callback_data="caste_certs")],
            [InlineKeyboardButton("💑 Marriage Certificate", callback_data="marriage_cert")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """📜 **Document Services**

**Available Services:**

🆔 **Identity Documents** - Aadhaar, Voter ID applications
🏠 **Residential Certificates** - Domicile, residence proof
👥 **Caste Certificates** - ST/SC/OBC certificates  
💑 **Marriage Certificate** - Marriage registration

**Select a service:**"""
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_healthcare_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Healthcare Services menu"""
        keyboard = [
            [InlineKeyboardButton("🏥 Medical Schemes", callback_data="medical_schemes")],
            [InlineKeyboardButton("💊 Medicine Assistance", callback_data="medicine_help")],
            [InlineKeyboardButton("🩺 Health Check-ups", callback_data="health_checkups")],
            [InlineKeyboardButton("🚑 Emergency Medical", callback_data="emergency_medical")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """🏥 **Healthcare Services**

**Available Services:**

🏥 **Medical Schemes** - Government health insurance
💊 **Medicine Assistance** - Free medicine programs
🩺 **Health Check-ups** - Scheduled health camps
🚑 **Emergency Medical** - Emergency contact numbers

**Select a service:**"""
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_education_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Education Services menu"""
        keyboard = [
            [InlineKeyboardButton("🎓 Scholarships", callback_data="scholarships")],
            [InlineKeyboardButton("🏫 School Admissions", callback_data="school_admissions")],
            [InlineKeyboardButton("📚 Educational Loans", callback_data="edu_loans")],
            [InlineKeyboardButton("🖥️ Digital Learning", callback_data="digital_learning")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """🎓 **Education Services**

**Available Services:**

🎓 **Scholarships** - Merit & need-based scholarships
🏫 **School Admissions** - Admission procedures & forms
📚 **Educational Loans** - Government education loans
🖥️ **Digital Learning** - Online learning resources

**Select a service:**"""
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_employment_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Employment Services menu"""
        keyboard = [
            [InlineKeyboardButton("💼 Job Opportunities", callback_data="job_opportunities")],
            [InlineKeyboardButton("🏭 Skill Development", callback_data="skill_development")],
            [InlineKeyboardButton("🚜 MGNREGA", callback_data="mgnrega")],
            [InlineKeyboardButton("📝 Employment Exchange", callback_data="employment_exchange")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """💼 **Employment Services**

**Available Services:**

💼 **Job Opportunities** - Government job notifications
🏭 **Skill Development** - Training programs & courses
🚜 **MGNREGA** - Rural employment guarantee scheme
📝 **Employment Exchange** - Job registration & matching

**Select a service:**"""
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_civic_services(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Civic Services menu"""
        keyboard = [
            [InlineKeyboardButton("📞 Grievance Redressal", callback_data="grievances")],
            [InlineKeyboardButton("💡 Public Utilities", callback_data="utilities")],
            [InlineKeyboardButton("🚰 Water & Sanitation", callback_data="water_sanitation")],
            [InlineKeyboardButton("🛣️ Roads & Transport", callback_data="roads_transport")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = """🏛️ **Civic Services**

**Available Services:**

📞 **Grievance Redressal** - File complaints & feedback
💡 **Public Utilities** - Electricity, gas connections
🚰 **Water & Sanitation** - Water supply, sewage issues
🛣️ **Roads & Transport** - Road issues, transport info

**Select a service:**"""
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help and support information"""
        help_text = """🆘 **SajiloSewa Help & Support**

**How to Use:**
1️⃣ Choose a service category from main menu
2️⃣ Navigate through sub-menus for specific services
3️⃣ Follow the instructions for each service

**Available Service Categories:**
🚨 Disaster Management (Ex-gratia, emergency services)
📜 Document Services (Certificates, licenses)
🏥 Healthcare Services (Medical schemes, assistance)
🎓 Education Services (Scholarships, admissions)
💼 Employment Services (Jobs, skill development)
🏛️ Civic Services (Complaints, utilities)

**Support Contact:**
📞 **Helpline:** 1077
📞 **Phone:** +91-3592-202401
📧 **Email:** support@sajilosewa.gov.in

**Commands:**
• `/start` - Show main menu
• `/help` - Show this help message"""

        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        message = update.message.text
        logger.info(f"User message: {message}")
        
        # Check if waiting for application ID
        if context.user_data.get('waiting_for_app_id'):
            await self.check_application_status(update, context, message)
            return
        
        # For other messages, show main menu
        await self.start_command(update, context)

    async def check_application_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, app_id: str):
        """Check application status from CSV file"""
        try:
            # Read status data
            df = pd.read_csv('data/status.csv')
            result = df[df['ApplicationID'].str.upper() == app_id.upper()]
            
            if not result.empty:
                row = result.iloc[0]
                status_emoji = {'Approved': '✅', 'Pending': '⏳', 'Rejected': '❌'}.get(row['Status'], '📋')
                
                response = f"""
{status_emoji} **Application Found!**

🆔 **Application ID:** {row['ApplicationID']}
👤 **Applicant:** {row['ApplicantName']}
🏘️ **Village:** {row['Village']}
📊 **Status:** {row['Status']}
💰 **Amount:** ₹{row['Amount']:,}

📞 **For queries:** 1077"""
                
            else:
                response = f"""
❌ **Application Not Found**

🔍 Application ID: `{app_id}`

**Possible reasons:**
• Application ID might be incorrect
• Application not yet in system
• Check for typing errors

**What to do:**
1. Double-check your Application ID
2. Contact Gram Panchayat/Ward Office
3. Call helpline: 1077"""
            
            keyboard = [
                [InlineKeyboardButton("🔍 Check Another", callback_data="exgratia_status")],
                [InlineKeyboardButton("🔙 Back to Ex-Gratia", callback_data="exgratia_submenu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error checking application status: {e}")
            await update.message.reply_text("❌ Error checking status. Please try again later.")
        
        context.user_data.pop('waiting_for_app_id', None)

    async def run(self):
        """Run the comprehensive SajiloSewa bot"""
        logger.info("Starting Comprehensive SajiloSewa Bot...")
        
        # Create application
        application = Application.builder().token(self.BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        print("🤖 Comprehensive SajiloSewa Bot is running...")
        print("📱 Bot Link: https://t.me/smartgov_assistant_bot")
        print("✅ All 6 service categories available!")
        print("🚨 Disaster Management → Ex-Gratia available")
        
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main function"""
    bot = ComprehensiveSajiloSewaBot()
    asyncio.run(bot.run())

if __name__ == "__main__":
    main() 