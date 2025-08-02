#!/usr/bin/env python3
"""
Data Manager for Sajilo Sewak Bot
Allows easy updating of bot data files including emergency contacts, CSC details, etc.
"""

import json
import csv
import os
import pandas as pd
from datetime import datetime
import sys

class DataManager:
    def __init__(self):
        self.data_dir = "data"
        self.backup_dir = "data/backups"
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def backup_file(self, filename):
        """Create a backup of a file before modifying it"""
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filename.replace('.', '_')}_{timestamp}.backup"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            with open(filepath, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            print(f"✅ Backup created: {backup_name}")
            return True
        return False
    
    def update_emergency_contacts(self):
        """Update emergency services contacts and responses"""
        print("\n🚨 EMERGENCY CONTACTS UPDATE")
        print("=" * 50)
        
        # Backup current file
        self.backup_file("emergency_services_text_responses.json")
        
        # Load current data
        filepath = os.path.join(self.data_dir, "emergency_services_text_responses.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("Current emergency services:")
        for service in data.keys():
            print(f"  - {service}")
        
        print("\nWhat would you like to do?")
        print("1. Add new emergency service")
        print("2. Update existing service")
        print("3. Add new contact to existing service")
        print("4. View current contacts")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            self._add_new_emergency_service(data)
        elif choice == "2":
            self._update_emergency_service(data)
        elif choice == "3":
            self._add_contact_to_service(data)
        elif choice == "4":
            self._view_emergency_contacts(data)
        else:
            print("❌ Invalid choice!")
            return
        
        # Save updated data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print("✅ Emergency contacts updated successfully!")
    
    def _add_new_emergency_service(self, data):
        """Add a new emergency service"""
        service_name = input("Enter service name (e.g., police, fire, medical): ").strip().lower()
        
        if service_name in data:
            print(f"❌ Service '{service_name}' already exists!")
            return
        
        print(f"\nEnter contact information for {service_name} service:")
        
        # Get contact details
        emergency_numbers = input("Emergency numbers (comma separated): ").strip()
        response_time = input("Response time (e.g., 10-15 minutes): ").strip()
        
        # Get locations/hospitals
        locations = []
        print("\nEnter emergency locations/hospitals (press Enter when done):")
        while True:
            location = input("Location name: ").strip()
            if not location:
                break
            contact = input("Contact number: ").strip()
            locations.append({"name": location, "contact": contact})
        
        # Create response templates
        english_text = f"""**{service_name.title()} Emergency Services**

**Emergency Numbers:**
{emergency_numbers}

**Emergency Locations:**
"""
        for loc in locations:
            english_text += f"{loc['name']}: {loc['contact']}\n"
        
        english_text += f"""
**Response Time**: {response_time}

**What to Share**:
- Your exact location
- Nature of emergency
- Contact number"""

        # Create multilingual responses
        data[service_name] = {
            "english": english_text,
            "hindi": f"**{service_name.title()} आपातकालीन सेवाएं**\n\n[Add Hindi translation here]",
            "nepali": f"**{service_name.title()} आपतकालीन सेवाहरू**\n\n[Add Nepali translation here]"
        }
        
        print(f"✅ Added new emergency service: {service_name}")
    
    def _update_emergency_service(self, data):
        """Update an existing emergency service"""
        service_name = input("Enter service name to update: ").strip().lower()
        
        if service_name not in data:
            print(f"❌ Service '{service_name}' not found!")
            return
        
        print(f"\nCurrent {service_name} service:")
        print(data[service_name]["english"][:200] + "...")
        
        print("\nWhat would you like to update?")
        print("1. Emergency numbers")
        print("2. Response time")
        print("3. Add new location")
        print("4. Update entire text")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            new_numbers = input("Enter new emergency numbers: ").strip()
            # Update the text (simplified - you might want to use regex for better parsing)
            data[service_name]["english"] = data[service_name]["english"].replace(
                "Emergency Numbers:", f"Emergency Numbers:\n{new_numbers}"
            )
        
        elif choice == "2":
            new_time = input("Enter new response time: ").strip()
            # Update response time in text
            data[service_name]["english"] = data[service_name]["english"].replace(
                "Response Time**:", f"Response Time**: {new_time}"
            )
        
        elif choice == "3":
            location_name = input("Enter location name: ").strip()
            contact = input("Enter contact number: ").strip()
            # Add to the text
            location_text = f"\n{location_name}: {contact}"
            data[service_name]["english"] = data[service_name]["english"].replace(
                "Emergency Locations:", f"Emergency Locations:{location_text}"
            )
        
        elif choice == "4":
            print("Enter new English text (press Enter twice to finish):")
            lines = []
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            
            new_text = "\n".join(lines[:-1])  # Remove the last empty line
            data[service_name]["english"] = new_text
        
        print(f"✅ Updated {service_name} service!")
    
    def _add_contact_to_service(self, data):
        """Add a new contact to an existing service"""
        service_name = input("Enter service name: ").strip().lower()
        
        if service_name not in data:
            print(f"❌ Service '{service_name}' not found!")
            return
        
        contact_name = input("Enter contact name: ").strip()
        contact_number = input("Enter contact number: ").strip()
        
        # Add to the text
        contact_text = f"\n{contact_name}: {contact_number}"
        data[service_name]["english"] = data[service_name]["english"].replace(
            "Emergency Numbers:", f"Emergency Numbers:{contact_text}"
        )
        
        print(f"✅ Added contact {contact_name} to {service_name} service!")
    
    def _view_emergency_contacts(self, data):
        """View all emergency contacts"""
        print("\n📞 CURRENT EMERGENCY CONTACTS")
        print("=" * 50)
        
        for service, info in data.items():
            print(f"\n🔴 {service.upper()}")
            print("-" * 30)
            print(info["english"][:300] + "...")
    
    def update_csc_details(self):
        """Update CSC (Common Service Center) details"""
        print("\n🏢 CSC DETAILS UPDATE")
        print("=" * 50)
        
        # Backup current file
        self.backup_file("csc_details.csv")
        
        filepath = os.path.join(self.data_dir, "csc_details.csv")
        df = pd.read_csv(filepath)
        
        print("Current CSC details:")
        print(f"Total CSC operators: {len(df)}")
        print(f"Blocks covered: {df['BLOCK'].unique()}")
        
        print("\nWhat would you like to do?")
        print("1. Add new CSC operator")
        print("2. Update existing CSC operator")
        print("3. Add new block")
        print("4. View all CSC operators")
        print("5. Export to Excel for editing")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            self._add_new_csc_operator(df)
        elif choice == "2":
            self._update_csc_operator(df)
        elif choice == "3":
            self._add_new_block(df)
        elif choice == "4":
            self._view_csc_operators(df)
        elif choice == "5":
            self._export_csc_to_excel(df)
        else:
            print("❌ Invalid choice!")
            return
        
        # Save updated data
        df.to_csv(filepath, index=False)
        print("✅ CSC details updated successfully!")
    
    def _add_new_csc_operator(self, df):
        """Add a new CSC operator"""
        print("\nEnter new CSC operator details:")
        
        # Get the next Sl number
        next_sl = len(df) + 1
        
        block = input("Block name: ").strip()
        gpu_name = input("GPU name: ").strip()
        operator_name = input("Operator name: ").strip()
        contact = input("Contact number: ").strip()
        block_window = input("Block Single Window (comma separated): ").strip()
        subdiv_window = input("SubDivision Single Window (comma separated): ").strip()
        
        new_row = {
            'Sl': next_sl,
            'BLOCK': block,
            'GPU Name': gpu_name,
            'Name': operator_name,
            'Contact No.': contact,
            'Block Single Window': block_window,
            'SubDivision Single Window': subdiv_window
        }
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        print(f"✅ Added new CSC operator: {operator_name}")
    
    def _update_csc_operator(self, df):
        """Update an existing CSC operator"""
        print("\nCurrent CSC operators:")
        for idx, row in df.iterrows():
            print(f"{idx+1}. {row['Name']} - {row['GPU Name']} ({row['BLOCK']})")
        
        try:
            choice = int(input("\nEnter operator number to update: ")) - 1
            if 0 <= choice < len(df):
                operator = df.iloc[choice]
                print(f"\nUpdating: {operator['Name']}")
                
                # Update fields
                new_name = input(f"Name ({operator['Name']}): ").strip() or operator['Name']
                new_contact = input(f"Contact ({operator['Contact No.']}): ").strip() or operator['Contact No.']
                new_block_window = input(f"Block Single Window ({operator['Block Single Window']}): ").strip() or operator['Block Single Window']
                new_subdiv_window = input(f"SubDivision Single Window ({operator['SubDivision Single Window']}): ").strip() or operator['SubDivision Single Window']
                
                df.at[choice, 'Name'] = new_name
                df.at[choice, 'Contact No.'] = new_contact
                df.at[choice, 'Block Single Window'] = new_block_window
                df.at[choice, 'SubDivision Single Window'] = new_subdiv_window
                
                print(f"✅ Updated CSC operator: {new_name}")
            else:
                print("❌ Invalid operator number!")
        except ValueError:
            print("❌ Please enter a valid number!")
    
    def _add_new_block(self, df):
        """Add a new block with multiple CSC operators"""
        block_name = input("Enter new block name: ").strip()
        
        print(f"\nAdding CSC operators for block: {block_name}")
        print("Enter GPU names and operator details (press Enter for GPU name to finish):")
        
        while True:
            gpu_name = input("\nGPU name (or press Enter to finish): ").strip()
            if not gpu_name:
                break
            
            operator_name = input("Operator name: ").strip()
            contact = input("Contact number: ").strip()
            block_window = input("Block Single Window: ").strip()
            subdiv_window = input("SubDivision Single Window: ").strip()
            
            next_sl = len(df) + 1
            new_row = {
                'Sl': next_sl,
                'BLOCK': block_name,
                'GPU Name': gpu_name,
                'Name': operator_name,
                'Contact No.': contact,
                'Block Single Window': block_window,
                'SubDivision Single Window': subdiv_window
            }
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            print(f"✅ Added CSC operator: {operator_name}")
        
        print(f"✅ Added new block: {block_name}")
    
    def _view_csc_operators(self, df):
        """View all CSC operators"""
        print("\n🏢 ALL CSC OPERATORS")
        print("=" * 80)
        
        for block in df['BLOCK'].unique():
            print(f"\n📍 BLOCK: {block}")
            print("-" * 50)
            block_df = df[df['BLOCK'] == block]
            
            for _, row in block_df.iterrows():
                print(f"  • {row['Name']} - {row['GPU Name']}")
                print(f"    Contact: {row['Contact No.']}")
                print(f"    Block Window: {row['Block Single Window']}")
                print(f"    SubDiv Window: {row['SubDivision Single Window']}")
                print()
    
    def _export_csc_to_excel(self, df):
        """Export CSC data to Excel for easy editing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = os.path.join(self.data_dir, f"csc_details_{timestamp}.xlsx")
        
        df.to_excel(excel_file, index=False)
        print(f"✅ Exported to Excel: {excel_file}")
        print("📝 Edit the Excel file and save it as CSV to update the data")
    
    def update_important_contacts(self):
        """Update important contacts like ambulance, police, etc."""
        print("\n📞 IMPORTANT CONTACTS UPDATE")
        print("=" * 50)
        
        # Create a new important contacts file
        contacts_file = os.path.join(self.data_dir, "important_contacts.json")
        
        if os.path.exists(contacts_file):
            with open(contacts_file, 'r', encoding='utf-8') as f:
                contacts = json.load(f)
        else:
            contacts = {
                "ambulance": {
                    "numbers": ["102", "108"],
                    "hospitals": [
                        {"name": "STNM Hospital, Gangtok", "contact": "03592-201158"},
                        {"name": "CRH Manipal, 5th Mile", "contact": "03592-270666"}
                    ]
                },
                "police": {
                    "numbers": ["100"],
                    "stations": [
                        {"name": "Gangtok Police Station", "contact": "03592-202022"}
                    ]
                },
                "fire": {
                    "numbers": ["101"],
                    "stations": [
                        {"name": "Gangtok Fire Station", "contact": "03592-202033"}
                    ]
                }
            }
        
        print("Current important contacts:")
        for category, info in contacts.items():
            print(f"  - {category}: {', '.join(info['numbers'])}")
        
        print("\nWhat would you like to do?")
        print("1. Add new contact category")
        print("2. Update existing contact")
        print("3. Add new number to category")
        print("4. View all contacts")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            self._add_contact_category(contacts)
        elif choice == "2":
            self._update_contact_category(contacts)
        elif choice == "3":
            self._add_number_to_category(contacts)
        elif choice == "4":
            self._view_important_contacts(contacts)
        else:
            print("❌ Invalid choice!")
            return
        
        # Save updated contacts
        with open(contacts_file, 'w', encoding='utf-8') as f:
            json.dump(contacts, f, indent=4, ensure_ascii=False)
        
        print("✅ Important contacts updated successfully!")
    
    def _add_contact_category(self, contacts):
        """Add a new contact category"""
        category = input("Enter category name (e.g., ambulance, police, fire): ").strip().lower()
        
        if category in contacts:
            print(f"❌ Category '{category}' already exists!")
            return
        
        numbers = input("Enter emergency numbers (comma separated): ").strip().split(',')
        numbers = [num.strip() for num in numbers]
        
        contacts[category] = {
            "numbers": numbers,
            "stations": []
        }
        
        print(f"Add stations/locations for {category} (press Enter when done):")
        while True:
            station_name = input("Station name: ").strip()
            if not station_name:
                break
            contact = input("Contact number: ").strip()
            contacts[category]["stations"].append({
                "name": station_name,
                "contact": contact
            })
        
        print(f"✅ Added new contact category: {category}")
    
    def _update_contact_category(self, contacts):
        """Update an existing contact category"""
        category = input("Enter category name to update: ").strip().lower()
        
        if category not in contacts:
            print(f"❌ Category '{category}' not found!")
            return
        
        print(f"\nCurrent {category} contacts:")
        print(f"Numbers: {', '.join(contacts[category]['numbers'])}")
        for station in contacts[category]['stations']:
            print(f"  {station['name']}: {station['contact']}")
        
        new_numbers = input("Enter new emergency numbers (comma separated): ").strip().split(',')
        new_numbers = [num.strip() for num in new_numbers]
        
        contacts[category]['numbers'] = new_numbers
        print(f"✅ Updated {category} contacts!")
    
    def _add_number_to_category(self, contacts):
        """Add a new number to an existing category"""
        category = input("Enter category name: ").strip().lower()
        
        if category not in contacts:
            print(f"❌ Category '{category}' not found!")
            return
        
        new_number = input("Enter new number: ").strip()
        contacts[category]['numbers'].append(new_number)
        
        print(f"✅ Added number {new_number} to {category}!")
    
    def _view_important_contacts(self, contacts):
        """View all important contacts"""
        print("\n📞 ALL IMPORTANT CONTACTS")
        print("=" * 50)
        
        for category, info in contacts.items():
            print(f"\n🔴 {category.upper()}")
            print(f"Numbers: {', '.join(info['numbers'])}")
            if info['stations']:
                print("Stations/Locations:")
                for station in info['stations']:
                    print(f"  • {station['name']}: {station['contact']}")
    
    def create_data_update_script(self):
        """Create a simple script for regular data updates"""
        script_content = '''#!/usr/bin/env python3
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
        print("\\nWhat would you like to update?")
        print("1. Emergency Contacts")
        print("2. CSC Details")
        print("3. Important Contacts")
        print("4. Exit")
        
        choice = input("\\nEnter your choice (1-4): ").strip()
        
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
'''
        
        with open("update_data.py", 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print("✅ Created update_data.py script!")
        print("📝 Run 'python update_data.py' to easily update your bot data")

def main():
    """Main function to run the data manager"""
    print("🔄 SAJILO SEWAK BOT - DATA MANAGER")
    print("=" * 50)
    
    dm = DataManager()
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Update Emergency Contacts")
        print("2. Update CSC Details")
        print("3. Update Important Contacts")
        print("4. Create Update Script")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            dm.update_emergency_contacts()
        elif choice == "2":
            dm.update_csc_details()
        elif choice == "3":
            dm.update_important_contacts()
        elif choice == "4":
            dm.create_data_update_script()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    main() 