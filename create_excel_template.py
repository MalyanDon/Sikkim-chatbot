#!/usr/bin/env python3
"""
Create Excel Templates for Sajilo Sewak Bot Data Updates
Generates user-friendly Excel templates for easy data management
"""

import pandas as pd
import os
from datetime import datetime

def create_csc_template():
    """Create Excel template for CSC details"""
    print("📋 Creating CSC Details Excel Template...")
    
    # Create template data
    template_data = {
        'Sl': [1, 2, 3],
        'BLOCK': ['Example Block', 'Example Block', 'New Block'],
        'GPU Name': ['Example GPU 1', 'Example GPU 2', 'New GPU'],
        'Name': ['Operator Name', 'Another Operator', 'New Operator'],
        'Contact No.': ['9876543210', '9876543211', '9876543212'],
        'Block Single Window': ['1234567890, 1234567891', '1234567892, 1234567893', '1234567894, 1234567895'],
        'SubDivision Single Window': ['0987654321, 0987654322', '0987654323, 0987654324', '0987654325, 0987654326']
    }
    
    df = pd.DataFrame(template_data)
    
    # Create Excel file with formatting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = f"data/CSC_Template_{timestamp}.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='CSC_Details', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['CSC_Details']
        
        # Add instructions
        instructions = [
            "CSC DETAILS UPDATE TEMPLATE",
            "",
            "INSTRUCTIONS:",
            "1. Replace example data with actual CSC operator details",
            "2. Add new rows for additional operators",
            "3. Ensure all required fields are filled",
            "4. Save as CSV file to update the bot",
            "",
            "FIELD DESCRIPTIONS:",
            "- Sl: Serial number (auto-increment)",
            "- BLOCK: Block name (e.g., Chongrang, Dentam)",
            "- GPU Name: Gram Panchayat Unit name",
            "- Name: CSC operator's full name",
            "- Contact No.: Operator's contact number",
            "- Block Single Window: Block office contact numbers (comma separated)",
            "- SubDivision Single Window: Sub-division office contact numbers (comma separated)",
            "",
            "IMPORTANT:",
            "- Keep the column headers exactly as shown",
            "- Use comma to separate multiple contact numbers",
            "- Save as CSV file named 'csc_details.csv' in the data folder"
        ]
        
        # Add instructions to a new sheet
        instruction_df = pd.DataFrame({'Instructions': instructions})
        instruction_df.to_excel(writer, sheet_name='Instructions', index=False)
    
    print(f"✅ Created CSC template: {excel_file}")
    return excel_file

def create_emergency_contacts_template():
    """Create Excel template for emergency contacts"""
    print("🚨 Creating Emergency Contacts Excel Template...")
    
    # Create template data
    template_data = {
        'Service_Type': ['medical', 'police', 'fire', 'disaster'],
        'Emergency_Numbers': ['102, 108', '100', '101', '1070, 1077'],
        'Response_Time': ['10-15 minutes', '5-10 minutes', '10-20 minutes', '15-30 minutes'],
        'Location_1_Name': ['STNM Hospital, Gangtok', 'Gangtok Police Station', 'Gangtok Fire Station', 'State Emergency Control'],
        'Location_1_Contact': ['03592-201158', '03592-202022', '03592-202033', '03592-204995'],
        'Location_2_Name': ['CRH Manipal, 5th Mile', 'District Police HQ', 'District Fire Station', 'District Control Room'],
        'Location_2_Contact': ['03592-270666', '03592-202024', '03592-202035', '03595-250888'],
        'English_Response': ['**Emergency Medical Services**...', '**Police Emergency Services**...', '**Fire Emergency Services**...', '**Disaster Emergency Services**...'],
        'Hindi_Response': ['**आपातकालीन चिकित्सा सेवाएं**...', '**पुलिस आपातकालीन सेवाएं**...', '**अग्निशमन आपातकालीन सेवाएं**...', '**आपदा आपातकालीन सेवाएं**...'],
        'Nepali_Response': ['**आपतकालीन चिकित्सा सेवाहरू**...', '**प्रहरी आपतकालीन सेवाहरू**...', '**दमकल आपतकालीन सेवाहरू**...', '**प्रकोप आपतकालीन सेवाहरू**...']
    }
    
    df = pd.DataFrame(template_data)
    
    # Create Excel file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = f"data/Emergency_Contacts_Template_{timestamp}.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Emergency_Contacts', index=False)
        
        # Add instructions
        instructions = [
            "EMERGENCY CONTACTS UPDATE TEMPLATE",
            "",
            "INSTRUCTIONS:",
            "1. Replace example data with actual emergency service details",
            "2. Add new rows for additional services",
            "3. Ensure all required fields are filled",
            "4. This data will be converted to JSON format",
            "",
            "FIELD DESCRIPTIONS:",
            "- Service_Type: Type of emergency service (medical, police, fire, disaster)",
            "- Emergency_Numbers: Emergency contact numbers (comma separated)",
            "- Response_Time: Expected response time",
            "- Location_1_Name: First emergency location name",
            "- Location_1_Contact: First location contact number",
            "- Location_2_Name: Second emergency location name",
            "- Location_2_Contact: Second location contact number",
            "- English_Response: Full English response text",
            "- Hindi_Response: Full Hindi response text",
            "- Nepali_Response: Full Nepali response text",
            "",
            "IMPORTANT:",
            "- Keep the column headers exactly as shown",
            "- Use comma to separate multiple contact numbers",
            "- Response text should be complete and formatted with markdown",
            "- This template will be converted to JSON format for the bot"
        ]
        
        instruction_df = pd.DataFrame({'Instructions': instructions})
        instruction_df.to_excel(writer, sheet_name='Instructions', index=False)
    
    print(f"✅ Created Emergency Contacts template: {excel_file}")
    return excel_file

def create_important_contacts_template():
    """Create Excel template for important contacts"""
    print("📞 Creating Important Contacts Excel Template...")
    
    # Create template data
    template_data = {
        'Category': ['ambulance', 'police', 'fire', 'disaster', 'custom'],
        'Emergency_Numbers': ['102, 108', '100', '101', '1070, 1077', 'custom_number'],
        'Station_1_Name': ['STNM Hospital, Gangtok', 'Gangtok Police Station', 'Gangtok Fire Station', 'State Emergency Control', 'Custom Station 1'],
        'Station_1_Contact': ['03592-201158', '03592-202022', '03592-202033', '03592-204995', 'custom_contact_1'],
        'Station_2_Name': ['CRH Manipal, 5th Mile', 'District Police HQ', 'District Fire Station', 'District Control Room', 'Custom Station 2'],
        'Station_2_Contact': ['03592-270666', '03592-202024', '03592-202035', '03595-250888', 'custom_contact_2'],
        'Description': ['Medical emergency services', 'Police emergency services', 'Fire emergency services', 'Disaster management services', 'Custom emergency service']
    }
    
    df = pd.DataFrame(template_data)
    
    # Create Excel file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = f"data/Important_Contacts_Template_{timestamp}.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Important_Contacts', index=False)
        
        # Add instructions
        instructions = [
            "IMPORTANT CONTACTS UPDATE TEMPLATE",
            "",
            "INSTRUCTIONS:",
            "1. Replace example data with actual contact details",
            "2. Add new rows for additional contact categories",
            "3. Ensure all required fields are filled",
            "4. This data will be converted to JSON format",
            "",
            "FIELD DESCRIPTIONS:",
            "- Category: Contact category (ambulance, police, fire, disaster, custom)",
            "- Emergency_Numbers: Emergency contact numbers (comma separated)",
            "- Station_1_Name: First station/location name",
            "- Station_1_Contact: First station contact number",
            "- Station_2_Name: Second station/location name",
            "- Station_2_Contact: Second station contact number",
            "- Description: Brief description of the service",
            "",
            "IMPORTANT:",
            "- Keep the column headers exactly as shown",
            "- Use comma to separate multiple contact numbers",
            "- Category names should be lowercase and simple",
            "- This template will be converted to JSON format for the bot"
        ]
        
        instruction_df = pd.DataFrame({'Instructions': instructions})
        instruction_df.to_excel(writer, sheet_name='Instructions', index=False)
    
    print(f"✅ Created Important Contacts template: {excel_file}")
    return excel_file

def create_all_templates():
    """Create all Excel templates"""
    print("📋 Creating All Excel Templates for Data Updates")
    print("=" * 60)
    
    # Ensure data directory exists
    if not os.path.exists("data"):
        os.makedirs("data")
    
    templates = []
    
    # Create all templates
    templates.append(create_csc_template())
    templates.append(create_emergency_contacts_template())
    templates.append(create_important_contacts_template())
    
    print("\n🎉 All templates created successfully!")
    print("\n📁 Template files created:")
    for template in templates:
        print(f"  • {template}")
    
    print("\n📝 HOW TO USE THESE TEMPLATES:")
    print("1. Open the Excel files in Microsoft Excel or Google Sheets")
    print("2. Replace example data with actual information")
    print("3. Follow the instructions in the 'Instructions' sheet")
    print("4. Save as CSV files in the 'data' folder")
    print("5. Restart the bot to load updated data")
    
    print("\n🔄 NEXT STEPS:")
    print("• Edit the templates with your actual data")
    print("• Save CSC template as 'csc_details.csv'")
    print("• Emergency contacts will be converted to JSON format")
    print("• Important contacts will be converted to JSON format")
    
    return templates

def main():
    """Main function"""
    print("🔄 SAJILO SEWAK BOT - EXCEL TEMPLATE GENERATOR")
    print("=" * 60)
    
    print("\nThis tool creates Excel templates for easy data updates.")
    print("These templates can be used by non-technical users to update bot data.")
    
    choice = input("\nCreate all templates? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        create_all_templates()
    else:
        print("❌ Template creation cancelled.")

if __name__ == "__main__":
    main() 