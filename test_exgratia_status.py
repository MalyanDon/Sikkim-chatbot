#!/usr/bin/env python3
"""
Test script for NC Exgratia Status Checking
This script tests the status checking functionality with the NIC server
"""

import asyncio
import logging
from nc_exgratia_api import get_api_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_status_check():
    """Test the status checking functionality"""
    print("🧪 Testing NC Exgratia Status Checking")
    print("=" * 50)
    
    try:
        # Get API client
        api_client = await get_api_client()
        
        # Test reference numbers (from the logs)
        test_reference_numbers = [
            "SK2025MN0096",  # From the logs - this was successfully submitted
            "SK2025MN0007",  # From the logs - this was checked
            "SK2025MN0003",  # Example reference number
        ]
        
        for ref_num in test_reference_numbers:
            print(f"\n📋 Testing reference number: {ref_num}")
            print("-" * 40)
            
            # Check status
            result = await api_client.check_application_status(ref_num)
            
            if result.get("success"):
                print("✅ Status check successful!")
                data = result.get("data", {})
                application = data.get("application", {})
                
                print(f"   Applicant: {application.get('applicant_name', 'Unknown')}")
                print(f"   Status: {application.get('status', 'Unknown')}")
                print(f"   Created: {application.get('created_at', 'Unknown')}")
                print(f"   Reference: {application.get('application_refno', 'Unknown')}")
                
            else:
                print("❌ Status check failed!")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                print(f"   Details: {result.get('details', 'No details')}")
        
        # Close the API client
        await api_client.close()
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        logger.error(f"Test error: {str(e)}")

async def test_api_connection():
    """Test basic API connection and authentication"""
    print("\n🔗 Testing API Connection")
    print("=" * 30)
    
    try:
        api_client = await get_api_client()
        
        # Test authentication
        print("🔐 Testing authentication...")
        auth_result = await api_client.authenticate()
        
        if auth_result:
            print("✅ Authentication successful!")
            print(f"   Access Token: {api_client.access_token[:20]}..." if api_client.access_token else "   No access token")
            print(f"   Token Expiry: {api_client.token_expiry}")
        else:
            print("❌ Authentication failed!")
        
        await api_client.close()
        
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")

async def main():
    """Main test function"""
    print("🚀 NC Exgratia API Test Suite")
    print("=" * 50)
    
    # Test API connection first
    await test_api_connection()
    
    # Test status checking
    await test_status_check()
    
    print("\n✅ Test suite completed!")

if __name__ == "__main__":
    asyncio.run(main()) 