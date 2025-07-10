#!/usr/bin/env python3
"""
Script to start the correct SmartGov bot with intent-based classification
"""
import time
import subprocess
import sys
import os

def main():
    print("🔄 Starting correct SmartGov bot with intent-based classification...")
    print("⏳ Waiting 3 seconds for any running processes to stop...")
    time.sleep(3)
    
    # Change to the correct directory
    os.chdir(r"C:\sikkim chat bot\Sikkim-chatbot")
    
    print("🚀 Starting SmartGov bot with LLM integration...")
    print("📱 This will show intent classifications in terminal")
    print("🧠 Expected bot behavior: Simple menu with Ex-Gratia options")
    print("="*50)
    
    # Start the correct bot
    subprocess.run([sys.executable, "smartgov_bot.py"])

if __name__ == "__main__":
    main() 