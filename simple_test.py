#!/usr/bin/env python3
"""
Simple test for Google Sheets integration using API key
"""
import logging
from google_sheets_service_simple import SimpleGoogleSheetsService
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_google_sheets():
    """Test the simplified Google Sheets integration"""
    print("🧪 Testing Simplified Google Sheets Integration...")
    print(f"API Key: {'✅ Set' if Config.GOOGLE_SHEETS_API_KEY else '❌ Not Set'}")
    print(f"Spreadsheet ID: {'✅ Set' if Config.GOOGLE_SHEETS_SPREADSHEET_ID else '❌ Not Set'}")
    print(f"Enabled: {'✅ Yes' if Config.GOOGLE_SHEETS_ENABLED else '❌ No'}")
    
    # Service account email
    service_account_email = "sikkimbot@nomadic-buffer-466007-g1.iam.gserviceaccount.com"
    print(f"Service Account: {service_account_email}")
    
    try:
        # Initialize service
        service = SimpleGoogleSheetsService(
            api_key=Config.GOOGLE_SHEETS_API_KEY,
            spreadsheet_id=Config.GOOGLE_SHEETS_SPREADSHEET_ID,
            service_account_email=service_account_email
        )
        
        if service.service:
            print("✅ Google Sheets service initialized successfully")
            
            # Test logging a complaint
            complaint_success = service.log_complaint(
                user_id=12345,
                user_name="Test User",
                complaint_text="This is a test complaint from simplified service",
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
            print("❌ Google Sheets service initialization failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    return False

if __name__ == "__main__":
    success = test_simple_google_sheets()
    if success:
        print("\n🎉 Simplified Google Sheets integration is working!")
        print("You can now run your bot and see data in Google Sheets.")
    else:
        print("\n❌ Simplified Google Sheets integration failed.")
        print("This might be due to permissions or API restrictions.") 