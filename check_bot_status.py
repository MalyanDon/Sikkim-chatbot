#!/usr/bin/env python3
"""
Quick Bot Status Check
Check if the main bot is running with location system
"""

import os
import psutil
import time

def check_bot_status():
    """Check if the main bot is running"""
    
    print("🔍 BOT STATUS CHECK")
    print("=" * 30)
    
    # Check if Python processes are running
    python_processes = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) if p.info['name'] == 'python.exe']
    
    if python_processes:
        print("✅ Python processes running:")
        for proc in python_processes:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else 'Unknown'
            print(f"   - PID: {proc.info['pid']}, Command: {cmdline}")
            
            # Check if it's the main bot
            if 'comprehensive_smartgov_bot.py' in cmdline:
                print("   🎯 This is the MAIN SmartGov bot with location system!")
            elif 'test_location_simple.py' in cmdline:
                print("   🧪 This is the TEST bot (should be stopped)")
    else:
        print("❌ No Python processes running")
    
    # Check location data file
    if os.path.exists("data/location_data.csv"):
        print("✅ Location data file exists")
        with open("data/location_data.csv", 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) > 1:
                print(f"📊 {len(lines)-1} location records captured")
            else:
                print("📊 Location file ready (no records yet)")
    else:
        print("❌ Location data file not found")
    
    # Check backup files
    backup_files = [f for f in os.listdir('.') if f.startswith('comprehensive_smartgov_bot_backup_')]
    if backup_files:
        print(f"✅ {len(backup_files)} backup files created")
    
    print("\n📱 TELEGRAM BOT STATUS:")
    print("   - Bot Token: 7641958089:AAH2UW5H0EX9pGfE6wZZaURCpkyMHtJK8zw")
    print("   - Main bot should be running with location system")
    print("   - Test bot should be stopped")
    
    print("\n🧪 TO TEST LOCATION SYSTEM:")
    print("1. Open Telegram and find your bot")
    print("2. Send: 'I need emergency help'")
    print("3. Bot should request location")
    print("4. Click '📍 Share My Location'")
    print("5. Check data/location_data.csv for captured coordinates")

if __name__ == "__main__":
    check_bot_status() 