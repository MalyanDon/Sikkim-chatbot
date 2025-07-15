#!/usr/bin/env python3
"""
Test script for Google Sheets integration with Comprehensive SmartGov Bot
"""
import asyncio
import logging
from comprehensive_smartgov_bot import SmartGovAssistantBot
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_google_sheets_integration():
    """Test the Google Sheets integration"""
    try:
        print("🧪 Testing Google Sheets Integration...")
        
        # Initialize the bot
        bot = SmartGovAssistantBot()
        
        # Test if Google Sheets service is initialized
        if bot.sheets_service:
            print("✅ Google Sheets service initialized successfully")
            
            # Test creating a test sheet
            test_sheet_name = "Test_Integration"
            headers = ["Timestamp", "Test", "Status"]
            
            success = bot.sheets_service.create_sheet_if_not_exists(test_sheet_name, headers)
            if success:
                print("✅ Test sheet creation successful")
                
                # Test appending a row
                test_data = ["2024-01-01 12:00:00", "Integration Test", "Passed"]
                success = bot.sheets_service.append_row(test_sheet_name, test_data)
                if success:
                    print("✅ Test row append successful")
                else:
                    print("❌ Test row append failed")
            else:
                print("❌ Test sheet creation failed")
        else:
            print("❌ Google Sheets service not initialized")
            print("Please check your configuration:")
            print(f"  - GOOGLE_SHEETS_ENABLED: {Config.GOOGLE_SHEETS_ENABLED}")
            print(f"  - GOOGLE_SHEETS_API_KEY: {'Set' if Config.GOOGLE_SHEETS_API_KEY else 'Not Set'}")
            print(f"  - GOOGLE_SHEETS_SPREADSHEET_ID: {'Set' if Config.GOOGLE_SHEETS_SPREADSHEET_ID else 'Not Set'}")
        
        print("\n📋 Google Sheets Integration Test Complete!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")

def test_logging_methods():
    """Test the logging methods directly"""
    try:
        print("\n🧪 Testing Logging Methods...")
        
        from google_sheets_service import GoogleSheetsService
        
        # Initialize service
        service = GoogleSheetsService(
            api_key=Config.GOOGLE_SHEETS_API_KEY,
            spreadsheet_id=Config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        
        if service.service:
            print("✅ Google Sheets service created successfully")
            
            # Test different logging methods
            test_methods = [
                ("log_complaint", service.log_complaint(123, "Test User", "Test complaint", "General", "english")),
                ("log_emergency_service", service.log_emergency_service(123, "Test User", "ambulance", "Test emergency", "english", "Test response")),
                ("log_homestay_query", service.log_homestay_query(123, "Test User", "Gangtok", "Test homestay query", "english", "Test response")),
                ("log_cab_booking_query", service.log_cab_booking_query(123, "Test User", "Gangtok", "Test cab query", "english", "Test response")),
                ("log_general_interaction", service.log_general_interaction(123, "Test User", "test", "Test interaction", "english", "Test response"))
            ]
            
            for method_name, result in test_methods:
                if result:
                    print(f"✅ {method_name} successful")
                else:
                    print(f"❌ {method_name} failed")
        else:
            print("❌ Google Sheets service creation failed")
            
    except Exception as e:
        logger.error(f"❌ Logging methods test failed: {str(e)}")
        print(f"❌ Logging methods test failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Google Sheets Integration Tests...")
    
    # Test logging methods
    test_logging_methods()
    
    # Test bot integration
    asyncio.run(test_google_sheets_integration())
    
    print("\n✨ All tests completed!") 