#!/usr/bin/env python3
"""
Simple Data Update Script for Sajilo Sewak Bot
Run this script to easily update bot data
"""

from data_manager import DataManager

def main():
    print("🔄 SAJILO SEWAK BOT - DATA UPDATE TOOL")
    print("=" * 50)
    
    dm = DataManager()
    
    while True:
        print("\nWhat would you like to update?")
        print("1. Emergency Contacts")
        print("2. CSC Details")
        print("3. Important Contacts")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            dm.update_emergency_contacts()
        elif choice == "2":
            dm.update_csc_details()
        elif choice == "3":
            dm.update_important_contacts()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    main() 