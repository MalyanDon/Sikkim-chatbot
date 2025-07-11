#!/usr/bin/env python3
"""
Multi-User Test Script for SmartGov Bot
Tests concurrent user interactions to ensure proper session isolation
"""

import asyncio
import aiohttp
import json
import time
from config import Config

class BotTester:
    def __init__(self):
        self.BOT_TOKEN = Config.BOT_TOKEN
        self.BASE_URL = f"https://api.telegram.org/bot{self.BOT_TOKEN}"
        
    async def simulate_user_interaction(self, user_id: int, chat_id: int, user_name: str):
        """Simulate a user interaction with the bot"""
        print(f"🤖 Starting simulation for User {user_name} (ID: {user_id})")
        
        async with aiohttp.ClientSession() as session:
            try:
                # Simulate /start command
                await self.send_message(session, chat_id, "/start", user_id, user_name)
                await asyncio.sleep(1)
                
                # Simulate language selection (different for each user)
                if user_id % 3 == 0:
                    await self.send_callback(session, chat_id, "lang_english", user_id, user_name)
                elif user_id % 3 == 1:
                    await self.send_callback(session, chat_id, "lang_hindi", user_id, user_name)
                else:
                    await self.send_callback(session, chat_id, "lang_nepali", user_id, user_name)
                
                await asyncio.sleep(1)
                
                # Simulate service selection (different for each user)
                if user_id % 4 == 0:
                    await self.send_callback(session, chat_id, "disaster_management", user_id, user_name)
                elif user_id % 4 == 1:
                    await self.send_callback(session, chat_id, "emergency_services", user_id, user_name)
                elif user_id % 4 == 2:
                    await self.send_callback(session, chat_id, "tourism", user_id, user_name)
                else:
                    await self.send_callback(session, chat_id, "csc", user_id, user_name)
                
                await asyncio.sleep(2)
                print(f"✅ User {user_name} simulation completed successfully")
                
            except Exception as e:
                print(f"❌ Error for User {user_name}: {str(e)}")

    async def send_message(self, session: aiohttp.ClientSession, chat_id: int, text: str, user_id: int, user_name: str):
        """Send a message to the bot"""
        url = f"{self.BASE_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "from": {
                "id": user_id,
                "first_name": user_name,
                "is_bot": False
            }
        }
        
        async with session.post(url, json=data) as response:
            if response.status == 200:
                print(f"📤 {user_name}: Sent message '{text}'")
            else:
                print(f"❌ {user_name}: Failed to send message")

    async def send_callback(self, session: aiohttp.ClientSession, chat_id: int, callback_data: str, user_id: int, user_name: str):
        """Send a callback query to the bot"""
        print(f"🔄 {user_name}: Sending callback '{callback_data}'")
        # Note: This is a simplified callback simulation
        # In real testing, you'd need actual message IDs from previous bot responses

async def main():
    """Run multi-user test"""
    print("🚀 Starting Multi-User Bot Test...")
    print("🎯 Testing concurrent user sessions...")
    
    tester = BotTester()
    
    # Create multiple concurrent user simulations
    users = [
        (12345, 12345, "TestUser1"),
        (12346, 12346, "TestUser2"), 
        (12347, 12347, "TestUser3"),
        (12348, 12348, "TestUser4"),
        (12349, 12349, "TestUser5"),
    ]
    
    # Run all user simulations concurrently
    tasks = [
        tester.simulate_user_interaction(user_id, chat_id, user_name)
        for user_id, chat_id, user_name in users
    ]
    
    await asyncio.gather(*tasks)
    print("🎉 Multi-user test completed!")

if __name__ == "__main__":
    print("📝 MULTI-USER TEST SUMMARY:")
    print("✅ Bot should handle multiple users simultaneously")
    print("✅ Each user should have independent session state")
    print("✅ No conflicts between different user workflows")
    print("\n" + "="*50)
    
    # Note: This is a simplified test. For real testing with your bot,
    # you would need to interact via actual Telegram clients
    print("🔍 ACTUAL TEST: Use 2+ phones/Telegram accounts simultaneously")
    print("📱 Try different workflows on each device at the same time")
    print("🎯 Verify no cross-user state interference") 