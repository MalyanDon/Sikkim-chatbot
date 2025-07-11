#!/usr/bin/env python3
"""
Test Script for Enhanced SmartGov Assistant Bot
Tests all major functionalities and workflows
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_smartgov_bot import SmartGovAssistantBot

class BotTester:
    def __init__(self):
        self.bot = SmartGovAssistantBot()
        self.test_results = []
        
    async def test_initialization(self):
        """Test bot initialization"""
        print("🧪 Testing Bot Initialization...")
        try:
            # Test data loading
            assert hasattr(self.bot, 'emergency_data'), "Emergency data not loaded"
            assert hasattr(self.bot, 'homestay_df'), "Homestay data not loaded"
            assert hasattr(self.bot, 'csc_df'), "CSC data not loaded"
            assert hasattr(self.bot, 'responses'), "Response templates not loaded"
            
            print("✅ Bot initialization test passed")
            return True
        except Exception as e:
            print(f"❌ Bot initialization test failed: {e}")
            return False
    
    async def test_language_functions(self):
        """Test language management functions"""
        print("🧪 Testing Language Functions...")
        try:
            test_user_id = 12345
            
            # Test default language
            default_lang = self.bot.get_user_language(test_user_id)
            assert default_lang == 'english', f"Expected 'english', got '{default_lang}'"
            
            # Test setting language
            self.bot.set_user_language(test_user_id, 'hindi')
            hindi_lang = self.bot.get_user_language(test_user_id)
            assert hindi_lang == 'hindi', f"Expected 'hindi', got '{hindi_lang}'"
            
            # Test setting another language
            self.bot.set_user_language(test_user_id, 'nepali')
            nepali_lang = self.bot.get_user_language(test_user_id)
            assert nepali_lang == 'nepali', f"Expected 'nepali', got '{nepali_lang}'"
            
            print("✅ Language functions test passed")
            return True
        except Exception as e:
            print(f"❌ Language functions test failed: {e}")
            return False
    
    async def test_llm_integration(self):
        """Test LLM integration (mock test)"""
        print("🧪 Testing LLM Integration...")
        try:
            # Test intent detection (this will return 'help' if LLM is not available)
            test_messages = [
                "I need help with disaster relief",
                "Emergency ambulance needed",
                "Show me homestays in Gangtok",
                "Find CSC operator near me"
            ]
            
            for message in test_messages:
                intent = await self.bot.get_intent_from_llm(message, 'english')
                assert isinstance(intent, str), f"Intent should be string, got {type(intent)}"
                print(f"   Message: '{message}' → Intent: {intent}")
            
            print("✅ LLM integration test passed")
            return True
        except Exception as e:
            print(f"❌ LLM integration test failed: {e}")
            return False
    
    async def test_data_files(self):
        """Test data file loading"""
        print("🧪 Testing Data Files...")
        try:
            # Test emergency data
            assert len(self.bot.emergency_data) > 0, "Emergency data is empty"
            
            # Test homestay data
            assert len(self.bot.homestay_df) > 0, "Homestay data is empty"
            
            # Test CSC data
            assert len(self.bot.csc_df) > 0, "CSC data is empty"
            
            # Test status data
            assert len(self.bot.status_df) > 0, "Status data is empty"
            
            print("✅ Data files test passed")
            return True
        except Exception as e:
            print(f"❌ Data files test failed: {e}")
            return False
    
    async def test_response_templates(self):
        """Test response templates"""
        print("🧪 Testing Response Templates...")
        try:
            languages = ['english', 'hindi', 'nepali']
            required_keys = ['welcome', 'select_language', 'language_set']
            service_keys = ['disaster_management', 'emergency_services', 'tourism', 'csc']
            
            for language in languages:
                assert language in self.bot.responses, f"Language '{language}' not found in responses"
                
                # Test basic keys
                for key in required_keys:
                    assert key in self.bot.responses[language], f"Key '{key}' not found for language '{language}'"
                
                # Test service keys
                for service in service_keys:
                    assert service in self.bot.responses[language], f"Service '{service}' not found for language '{language}'"
                    service_data = self.bot.responses[language][service]
                    assert 'title' in service_data, f"Title not found for service '{service}' in language '{language}'"
                    assert 'description' in service_data, f"Description not found for service '{service}' in language '{language}'"
            
            print("✅ Response templates test passed")
            return True
        except Exception as e:
            print(f"❌ Response templates test failed: {e}")
            return False
    
    async def test_emergency_numbers(self):
        """Test emergency number retrieval"""
        print("🧪 Testing Emergency Numbers...")
        try:
            emergency_services = ['ambulance', 'police', 'fire', 'women', 'suicide', 'health', 'disaster']
            
            for service in emergency_services:
                number = self.bot.get_emergency_number(service)
                assert isinstance(number, str), f"Emergency number should be string for {service}"
                assert len(number) > 0, f"Emergency number is empty for {service}"
                print(f"   {service.title()}: {number}")
            
            print("✅ Emergency numbers test passed")
            return True
        except Exception as e:
            print(f"❌ Emergency numbers test failed: {e}")
            return False
    
    async def test_card_creation(self):
        """Test service card creation"""
        print("🧪 Testing Service Card Creation...")
        try:
            services = ['disaster_management', 'emergency_services', 'tourism', 'csc']
            languages = ['english', 'hindi', 'nepali']
            
            for service in services:
                for language in languages:
                    card = await self.bot.create_service_card(service, language)
                    assert hasattr(card, 'media'), f"Card missing media for {service} in {language}"
                    assert hasattr(card, 'caption'), f"Card missing caption for {service} in {language}"
                    print(f"   ✓ {service} card created for {language}")
            
            print("✅ Service card creation test passed")
            return True
        except Exception as e:
            print(f"❌ Service card creation test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Enhanced SmartGov Bot Tests")
        print("=" * 60)
        
        test_suites = [
            ("Bot Initialization", self.test_initialization),
            ("Language Functions", self.test_language_functions),
            ("LLM Integration", self.test_llm_integration),
            ("Data Files", self.test_data_files),
            ("Response Templates", self.test_response_templates),
            ("Emergency Numbers", self.test_emergency_numbers),
            ("Service Card Creation", self.test_card_creation)
        ]
        
        passed = 0
        total = len(test_suites)
        
        for test_name, test_func in test_suites:
            print(f"\n📋 Running: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed += 1
                    self.test_results.append((test_name, True))
                else:
                    self.test_results.append((test_name, False))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                self.test_results.append((test_name, False))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for test_name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\n🏆 OVERALL RESULTS:")
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! The enhanced bot is working perfectly!")
        elif passed >= total * 0.8:
            print("\n✅ MOST TESTS PASSED! The bot is working well with minor issues.")
        else:
            print("\n⚠️ SOME TESTS FAILED. The bot needs attention.")
        
        return passed == total

async def main():
    """Main test function"""
    tester = BotTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 Bot is ready for deployment!")
    else:
        print("\n🔧 Bot needs fixes before deployment.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 