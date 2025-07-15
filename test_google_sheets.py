#!/usr/bin/env python3
"""
Test script for Google Sheets integration
"""
import os
import sys
from dotenv import load_dotenv
from google_sheets_service import GoogleSheetsService

# Load environment variables
load_dotenv()

def test_google_sheets():
    """Test Google Sheets integration"""
    print("🧪 Testing Google Sheets Integration...")
    
    # Check configuration
    credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '')
    
    if not spreadsheet_id:
        print("❌ GOOGLE_SHEETS_SPREADSHEET_ID not set in .env file")
        return False
    
    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file not found: {credentials_file}")
        print("Please download credentials.json from Google Cloud Console")
        return False
    
    try:
        # Initialize service
        print("🔐 Initializing Google Sheets service...")
        sheets_service = GoogleSheetsService(credentials_file, spreadsheet_id)
        
        if not sheets_service.service:
            print("❌ Failed to initialize Google Sheets service")
            return False
        
        print("✅ Google Sheets service initialized successfully")
        
        # Test creating a test sheet
        print("📝 Testing sheet creation...")
        test_headers = ["Test Column 1", "Test Column 2", "Test Column 3"]
        if sheets_service.create_sheet_if_not_exists("Test_Sheet", test_headers):
            print("✅ Test sheet created/verified successfully")
        else:
            print("❌ Failed to create test sheet")
            return False
        
        # Test appending a row
        print("📊 Testing row append...")
        test_row = ["Test Data 1", "Test Data 2", "Test Data 3"]
        if sheets_service.append_row("Test_Sheet", test_row):
            print("✅ Test row appended successfully")
        else:
            print("❌ Failed to append test row")
            return False
        
        # Test logging functions
        print("📋 Testing logging functions...")
        
        # Test complaint logging
        if sheets_service.log_complaint(12345, "Test User", "Test complaint", "Test Type", "english"):
            print("✅ Complaint logging works")
        else:
            print("❌ Complaint logging failed")
        
        # Test certificate query logging
        if sheets_service.log_certificate_query(12345, "Test User", "Test query", "Test Certificate", "english", "Test result"):
            print("✅ Certificate query logging works")
        else:
            print("❌ Certificate query logging failed")
        
        # Test application logging
        app_data = {
            'name': 'Test User',
            'phone': '1234567890',
            'address': 'Test Address',
            'damage_type': 'Test Damage',
            'damage_description': 'Test Description'
        }
        if sheets_service.log_ex_gratia_application(12345, "Test User", app_data, "english"):
            print("✅ Application logging works")
        else:
            print("❌ Application logging failed")
        
        # Test status check logging
        if sheets_service.log_status_check(12345, "Test User", "TEST123", "Test Status", "english"):
            print("✅ Status check logging works")
        else:
            print("❌ Status check logging failed")
        
        print("\n🎉 All Google Sheets tests passed!")
        print("✅ Integration is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_google_sheets()
    sys.exit(0 if success else 1) 