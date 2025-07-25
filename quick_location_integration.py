#!/usr/bin/env python3
"""
Quick Location Integration Script
This shows exactly what needs to be changed in your main bot
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

def show_integration_steps():
    """Show the exact steps to integrate the new location system"""
    
    print("🔧 LOCATION SYSTEM INTEGRATION STEPS")
    print("=" * 50)
    
    print("\n📋 STEP 1: Create Backup")
    print("   - Backup your current bot file")
    print("   - This script will create a backup automatically")
    
    print("\n📋 STEP 2: Add Import")
    print("   Add this line at the top of comprehensive_smartgov_bot.py:")
    print("   from simple_location_system import SimpleLocationSystem")
    
    print("\n📋 STEP 3: Initialize Location System")
    print("   In the __init__ method, add:")
    print("   self.location_system = SimpleLocationSystem()")
    print("   logger.info('📍 Location system initialized')")
    
    print("\n📋 STEP 4: Replace Message Handler")
    print("   Replace your current message_handler with the simplified version")
    print("   (See LOCATION_INTEGRATION_GUIDE.md for the exact code)")
    
    print("\n📋 STEP 5: Update Emergency/Complaint Handlers")
    print("   Replace start_emergency_workflow and start_complaint_workflow")
    print("   to use self.location_system.request_location()")
    
    print("\n📋 STEP 6: Remove Old Location Functions")
    print("   Remove these functions from your bot:")
    print("   - request_location()")
    print("   - handle_location_received()")
    print("   - handle_emergency_with_location()")
    print("   - handle_complaint_with_location()")
    print("   - handle_manual_location_workflow()")
    print("   - handle_manual_location_name_workflow()")
    print("   - handle_emergency_report_with_location()")
    print("   - handle_ex_gratia_with_location()")
    
    print("\n📋 STEP 7: Test the Integration")
    print("   - Run your main bot")
    print("   - Test location sharing")
    print("   - Check data/location_data.csv for captured coordinates")

def show_test_instructions():
    """Show how to test the location system"""
    
    print("\n🧪 TESTING INSTRUCTIONS")
    print("=" * 30)
    
    print("\n1. The test bot is currently running!")
    print("   Process ID: 6164")
    
    print("\n2. Open Telegram and find your bot")
    print("   Bot Token: 7641958089:AAH2UW5H0EX9pGfE6wZZaURCpkyMHtJK8zw")
    
    print("\n3. Send /start to the bot")
    print("   - You should see a location request keyboard")
    print("   - Click '📍 Share My Location'")
    print("   - Allow location permission if prompted")
    
    print("\n4. Check the results:")
    print("   - Bot should show your coordinates")
    print("   - Check data/location_data.csv for saved data")
    print("   - Check console logs for success messages")
    
    print("\n5. Test different scenarios:")
    print("   - Try 'Skip Location' button")
    print("   - Try 'Cancel' button")
    print("   - Try sending text instead of location")

def show_current_status():
    """Show current status of location system"""
    
    print("\n📊 CURRENT STATUS")
    print("=" * 20)
    
    # Check if location data file exists
    if os.path.exists("data/location_data.csv"):
        print("✅ Location data file exists")
        
        # Count lines in file
        with open("data/location_data.csv", 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) > 1:  # Has data beyond header
                print(f"📈 {len(lines)-1} location records captured")
            else:
                print("📈 No location records yet (file ready)")
    else:
        print("❌ Location data file not created yet")
    
    # Check if test bot is running
    import psutil
    python_processes = [p for p in psutil.process_iter(['pid', 'name']) if p.info['name'] == 'python.exe']
    
    if python_processes:
        print("✅ Python processes running (test bot active)")
        for proc in python_processes:
            print(f"   - Process ID: {proc.info['pid']}")
    else:
        print("❌ No Python processes running")

def main():
    """Main function"""
    
    print("🚀 LOCATION SYSTEM INTEGRATION HELPER")
    print("=" * 50)
    
    # Create backup
    backup_file = backup_original_bot()
    
    # Show current status
    show_current_status()
    
    # Show test instructions
    show_test_instructions()
    
    # Show integration steps
    show_integration_steps()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Test the location system with the running test bot")
    print("2. Follow the integration steps to update your main bot")
    print("3. Use the backup file if you need to revert changes")
    print("4. Check LOCATION_INTEGRATION_GUIDE.md for detailed instructions")
    
    print(f"\n📁 Files created:")
    print(f"   - test_location_simple.py (test bot)")
    print(f"   - simple_location_system.py (new location system)")
    print(f"   - LOCATION_INTEGRATION_GUIDE.md (detailed guide)")
    if backup_file:
        print(f"   - {backup_file} (backup of original bot)")

if __name__ == "__main__":
    main() 