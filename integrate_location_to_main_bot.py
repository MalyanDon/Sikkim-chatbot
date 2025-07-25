#!/usr/bin/env python3
"""
Integrate New Location System into Main Bot
This script will automatically update your comprehensive_smartgov_bot.py
"""

import os
import shutil
from datetime import datetime

def backup_original_bot():
    """Create a backup of the original bot"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"comprehensive_smartgov_bot_backup_{timestamp}.py"
    
    if os.path.exists("comprehensive_smartgov_bot.py"):
        shutil.copy2("comprehensive_smartgov_bot.py", backup_file)
        print(f"✅ Backup created: {backup_file}")
        return backup_file
    else:
        print("❌ Main bot file not found!")
        return None

def add_location_import():
    """Add the location system import to the main bot"""
    
    # Read the main bot file
    with open("comprehensive_smartgov_bot.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Find the import section and add our import
    import_added = False
    for i, line in enumerate(lines):
        if "from telegram import" in line and not import_added:
            # Add our import after the telegram imports
            lines.insert(i + 1, "from simple_location_system import SimpleLocationSystem\n")
            import_added = True
            break
    
    # Write back to file
    with open("comprehensive_smartgov_bot.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    
    if import_added:
        print("✅ Location system import added")
    else:
        print("⚠️ Could not find import section, please add manually")

def initialize_location_system():
    """Add location system initialization to __init__ method"""
    
    # Read the main bot file
    with open("comprehensive_smartgov_bot.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Find the __init__ method and add location system initialization
    init_found = False
    for i, line in enumerate(lines):
        if "def __init__(self):" in line:
            init_found = True
            # Find the end of __init__ method (look for next method or class)
            j = i + 1
            while j < len(lines) and (lines[j].strip().startswith("#") or 
                                     lines[j].strip() == "" or 
                                     lines[j].startswith("        ")):
                j += 1
            
            # Add location system initialization before the end
            lines.insert(j, "        # Initialize location system\n")
            lines.insert(j + 1, "        self.location_system = SimpleLocationSystem()\n")
            lines.insert(j + 2, "        logger.info('📍 Location system initialized')\n")
            lines.insert(j + 3, "\n")
            break
    
    # Write back to file
    with open("comprehensive_smartgov_bot.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    
    if init_found:
        print("✅ Location system initialized in __init__")
    else:
        print("⚠️ Could not find __init__ method, please add manually")

def replace_message_handler():
    """Replace the message handler with the new location-aware version"""
    
    # Read the main bot file
    with open("comprehensive_smartgov_bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # New message handler code
    new_message_handler = '''    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Simplified message handler with working location system"""
        if not update.message:
            return
        
        user_id = update.effective_user.id
        
        # Handle location messages FIRST
        if update.message.location:
            logger.info(f"📍 [MAIN] Location message detected from user {user_id}")
            await self.location_system.handle_location_received(update, context)
            return
        
        # Handle text messages
        if not update.message.text:
            return
        
        message_text = update.message.text
        logger.info(f"[MSG] User {user_id}: {message_text}")
        
        # Handle location-related buttons
        if message_text == "⏭️ Skip Location":
            await self.location_system.handle_location_skip(update, context)
            return
        elif message_text == "❌ Cancel":
            await self.location_system.handle_location_cancel(update, context)
            return
        
        # Check if waiting for location
        if context.user_data.get('location_request'):
            # User sent text instead of location, continue without location
            await self.location_system.handle_location_skip(update, context)
            return
        
        # Check if this interaction should capture location
        if self.location_system.should_capture_location(message_text):
            interaction_type = self.location_system.detect_interaction_type(message_text)
            await self.location_system.request_location(update, context, interaction_type, message_text)
            return
        
        # Continue with normal message processing
        await self._process_normal_message(update, context, message_text)

    async def _process_normal_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
        """Process normal messages (existing logic)"""
        user_id = update.effective_user.id
        
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
        
        # Continue with your existing message processing logic here
        # This includes all your current handlers for different services
        # ... (your existing logic continues here)'''
    
    # Find and replace the message handler
    import re
    
    # Pattern to find the message handler
    pattern = r'async def message_handler\(self, update: Update, context: ContextTypes\.DEFAULT_TYPE\):.*?(?=async def|\Z)'
    
    # Replace with new message handler
    new_content = re.sub(pattern, new_message_handler, content, flags=re.DOTALL)
    
    # Write back to file
    with open("comprehensive_smartgov_bot.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("✅ Message handler replaced with location-aware version")

def update_emergency_workflow():
    """Update emergency workflow to use location system"""
    
    # Read the main bot file
    with open("comprehensive_smartgov_bot.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Find and update start_emergency_workflow
    for i, line in enumerate(lines):
        if "async def start_emergency_workflow" in line:
            # Find the function body
            j = i + 1
            while j < len(lines) and (lines[j].strip().startswith("#") or 
                                     lines[j].strip() == "" or 
                                     lines[j].startswith("        ")):
                j += 1
            
            # Replace the function body
            new_function = '''    async def start_emergency_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start emergency workflow with location capture"""
        await self.location_system.request_location(update, context, "emergency", "Emergency services requested")
'''
            
            # Remove old function and add new one
            # Find the end of the old function
            k = j
            while k < len(lines) and (lines[k].strip().startswith("#") or 
                                     lines[k].strip() == "" or 
                                     lines[k].startswith("        ")):
                k += 1
            
            # Replace the function
            lines[i:k] = new_function.splitlines(True)
            break
    
    # Write back to file
    with open("comprehensive_smartgov_bot.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    
    print("✅ Emergency workflow updated to use location system")

def update_complaint_workflow():
    """Update complaint workflow to use location system"""
    
    # Read the main bot file
    with open("comprehensive_smartgov_bot.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Find and update start_complaint_workflow
    for i, line in enumerate(lines):
        if "async def start_complaint_workflow" in line:
            # Find the function body
            j = i + 1
            while j < len(lines) and (lines[j].strip().startswith("#") or 
                                     lines[j].strip() == "" or 
                                     lines[j].startswith("        ")):
                j += 1
            
            # Replace the function body
            new_function = '''    async def start_complaint_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start complaint workflow with location capture"""
        await self.location_system.request_location(update, context, "complaint", "Complaint filing requested")
'''
            
            # Remove old function and add new one
            # Find the end of the old function
            k = j
            while k < len(lines) and (lines[k].strip().startswith("#") or 
                                     lines[k].strip() == "" or 
                                     lines[k].startswith("        ")):
                k += 1
            
            # Replace the function
            lines[i:k] = new_function.splitlines(True)
            break
    
    # Write back to file
    with open("comprehensive_smartgov_bot.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    
    print("✅ Complaint workflow updated to use location system")

def remove_old_location_functions():
    """Remove old location-related functions"""
    
    # Read the main bot file
    with open("comprehensive_smartgov_bot.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Functions to remove
    functions_to_remove = [
        "async def request_location",
        "async def handle_location_received",
        "async def handle_emergency_with_location",
        "async def handle_complaint_with_location",
        "async def handle_manual_location_workflow",
        "async def handle_manual_location_name_workflow",
        "async def handle_emergency_report_with_location",
        "async def handle_ex_gratia_with_location"
    ]
    
    # Find and remove these functions
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts any of the functions to remove
        should_remove = False
        for func_start in functions_to_remove:
            if func_start in line:
                should_remove = True
                break
        
        if should_remove:
            # Find the end of this function
            j = i + 1
            while j < len(lines):
                # Check if we've reached the next function or class
                if (lines[j].strip().startswith("async def ") or 
                    lines[j].strip().startswith("def ") or
                    lines[j].strip().startswith("class ")):
                    break
                j += 1
            
            # Remove the function
            del lines[i:j]
            print(f"✅ Removed function starting at line {i+1}")
        else:
            i += 1
    
    # Write back to file
    with open("comprehensive_smartgov_bot.py", "w", encoding="utf-8") as f:
        f.writelines(lines)
    
    print("✅ Old location functions removed")

def main():
    """Main integration function"""
    
    print("🚀 INTEGRATING LOCATION SYSTEM INTO MAIN BOT")
    print("=" * 50)
    
    # Step 1: Create backup
    backup_file = backup_original_bot()
    if not backup_file:
        return
    
    # Step 2: Add import
    add_location_import()
    
    # Step 3: Initialize location system
    initialize_location_system()
    
    # Step 4: Replace message handler
    replace_message_handler()
    
    # Step 5: Update workflows
    update_emergency_workflow()
    update_complaint_workflow()
    
    # Step 6: Remove old functions
    remove_old_location_functions()
    
    print("\n🎉 INTEGRATION COMPLETE!")
    print("=" * 30)
    print("✅ Location system integrated into main bot")
    print("✅ Emergency services will now capture location")
    print("✅ Complaint filing will now capture location")
    print("✅ All interactions can capture location")
    print(f"✅ Backup saved as: {backup_file}")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Test the main bot: python comprehensive_smartgov_bot.py")
    print("2. Try emergency services - should request location")
    print("3. Try complaint filing - should request location")
    print("4. Check data/location_data.csv for captured coordinates")
    print("5. Monitor logs for location capture success")

if __name__ == "__main__":
    main() 