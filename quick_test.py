#!/usr/bin/env python3
"""
Quick test for Google Sheets integration
"""
import os
import logging
from google_sheets_service import GoogleSheetsService
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_google_sheets():
    """Quick test of Google Sheets integration"""
    print("🧪 Testing Google Sheets Integration...")
    print(f"Credentials File: {'✅ Found' if os.path.exists(Config.GOOGLE_SHEETS_CREDENTIALS_FILE) else '❌ Not Found'}")
    print(f"Spreadsheet ID: {'✅ Set' if Config.GOOGLE_SHEETS_SPREADSHEET_ID else '❌ Not Set'}")
    print(f"Enabled: {'✅ Yes' if Config.GOOGLE_SHEETS_ENABLED else '❌ No'}")
    
    if not os.path.exists(Config.GOOGLE_SHEETS_CREDENTIALS_FILE):
        print("\n⚠️  IMPORTANT: You need to download credentials.json!")
        print("1. Go to Google Cloud Console > APIs & Services > Credentials")
        print("2. Find your service account: sikkimbot@nomadic-buffer-466007-g1.iam.gserviceaccount.com")
        print("3. Create a new key (JSON format)")
        print("4. Download and save as 'credentials.json' in this folder")
        return False
    
    if not Config.GOOGLE_SHEETS_SPREADSHEET_ID:
        print("\n⚠️  IMPORTANT: You need to set your spreadsheet ID!")
        print("1. Go to https://sheets.google.com")
        print("2. Create a new spreadsheet")
        print("3. Copy the ID from the URL")
        print("4. Update config.py with your spreadsheet ID")
        return False
    
    try:
        # Initialize service
        service = GoogleSheetsService(
            credentials_file=Config.GOOGLE_SHEETS_CREDENTIALS_FILE,
            spreadsheet_id=Config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        
        if service.service:
            print("✅ Google Sheets service initialized successfully")
            
            # Test creating a test sheet
            test_sheet = "Test_Integration"
            headers = ["Timestamp", "Test", "Status"]
            
            success = service.create_sheet_if_not_exists(test_sheet, headers)
            if success:
                print("✅ Test sheet created successfully")
                
                # Test logging a complaint
                complaint_success = service.log_complaint(
                    user_id=12345,
                    user_name="Test User",
                    complaint_text="This is a test complaint",
                    complaint_type="Test",
                    language="english"
                )
                
                if complaint_success:
                    print("✅ Test complaint logged successfully")
                    print(f"\n📊 Check your Google Sheet: https://docs.google.com/spreadsheets/d/{Config.GOOGLE_SHEETS_SPREADSHEET_ID}/edit")
                    print("   Look for the 'Complaints' sheet")
                    return True
                else:
                    print("❌ Test complaint logging failed")
            else:
                print("❌ Test sheet creation failed")
        else:
            print("❌ Google Sheets service initialization failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    return False

if __name__ == "__main__":
    success = test_google_sheets()
    if success:
        print("\n🎉 Google Sheets integration is working!")
        print("You can now run your bot and see data in Google Sheets.")
    else:
        print("\n❌ Google Sheets integration needs configuration.")
        print("Please follow the setup instructions in GOOGLE_SHEETS_SETUP.md") 