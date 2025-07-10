"""
Test Ex-Gratia Application Form - Comprehensive Test
Tests all required fields: ApplicantName, FatherName, Village, ContactNumber, Ward, GPU, KhatiyanNo, PlotNo, DamageType, DamageDescription, SubmissionDate, Language, Status
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.getcwd())

from comprehensive_smartgov_bot import SmartGovAssistantBot
import pandas as pd

def test_application_stages():
    """Test that all required application stages are present"""
    bot = SmartGovAssistantBot()
    
    print("🧪 TESTING EX-GRATIA APPLICATION FORM")
    print("=" * 50)
    
    # Check application stages
    expected_stages = [
        'applicant_name', 'father_name', 'village', 'contact_number', 
        'ward', 'gpu', 'khatiyan_no', 'plot_no', 'damage_type', 
        'damage_description', 'confirmation'
    ]
    
    print("📋 Expected Application Stages:")
    for i, stage in enumerate(expected_stages, 1):
        print(f"   {i:2d}. {stage.replace('_', ' ').title()}")
    
    print(f"\n✅ Bot has {len(bot.application_stages)} stages configured")
    print(f"✅ Expected {len(expected_stages)} stages")
    
    if bot.application_stages == expected_stages:
        print("✅ ALL STAGES MATCH PERFECTLY!")
    else:
        print("❌ STAGE MISMATCH!")
        print(f"   Bot stages: {bot.application_stages}")
        print(f"   Expected:   {expected_stages}")
    
    return bot.application_stages == expected_stages

def test_validation_logic():
    """Test validation for each field type"""
    bot = SmartGovAssistantBot()
    
    print("\n🔍 TESTING VALIDATION LOGIC")
    print("=" * 30)
    
    test_cases = [
        # Valid cases
        ('applicant_name', 'Rajesh Kumar', True),
        ('father_name', 'Mohan Singh', True),
        ('village', 'Gangtok', True),
        ('contact_number', '9876543210', True),
        ('ward', '5', True),
        ('gpu', 'GP001', True),
        ('khatiyan_no', 'KH123', True),
        ('plot_no', 'P456', True),
        ('damage_type', '1', True),  # Flood
        ('damage_description', 'House damaged due to heavy rainfall and flooding', True),
        
        # Invalid cases
        ('applicant_name', 'R', False),  # Too short
        ('contact_number', '123', False),  # Too short
        ('damage_type', '7', False),  # Invalid option
        ('damage_description', 'Short', False),  # Too short
    ]
    
    passed = 0
    total = len(test_cases)
    
    for stage, input_text, expected_valid in test_cases:
        is_valid, result = bot.validate_input(stage, input_text)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"   {status} {stage}: '{input_text}' → {is_valid} (expected {expected_valid})")
        if is_valid == expected_valid:
            passed += 1
    
    print(f"\n📊 Validation Results: {passed}/{total} tests passed")
    return passed == total

def test_damage_type_options():
    """Test damage type options"""
    bot = SmartGovAssistantBot()
    
    print("\n🌪️ TESTING DAMAGE TYPE OPTIONS")
    print("=" * 30)
    
    damage_types = {
        '1': 'Flood',
        '2': 'Landslide', 
        '3': 'Earthquake',
        '4': 'Fire',
        '5': 'Storm/Cyclone',
        '6': 'Other'
    }
    
    all_valid = True
    for option, expected_type in damage_types.items():
        is_valid, result = bot.validate_input('damage_type', option)
        status = "✅" if is_valid and result == expected_type else "❌"
        print(f"   {status} Option {option}: '{result}' (expected '{expected_type}')")
        if not (is_valid and result == expected_type):
            all_valid = False
    
    # Test invalid option
    is_valid, result = bot.validate_input('damage_type', '7')
    status = "✅" if not is_valid else "❌"
    print(f"   {status} Option 7: Invalid (expected invalid)")
    if is_valid:
        all_valid = False
    
    return all_valid

def test_csv_structure():
    """Test CSV file structure"""
    print("\n📄 TESTING CSV STRUCTURE")
    print("=" * 25)
    
    expected_headers = [
        'ApplicantName', 'FatherName', 'Village', 'ContactNumber', 
        'Ward', 'GPU', 'KhatiyanNo', 'PlotNo', 'DamageType', 
        'DamageDescription', 'SubmissionDate', 'Language', 'Status'
    ]
    
    csv_file = 'data/exgratia_applications.csv'
    
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            actual_headers = list(df.columns)
            
            print("📋 Expected CSV Headers:")
            for i, header in enumerate(expected_headers, 1):
                print(f"   {i:2d}. {header}")
            
            print(f"\n📋 Actual CSV Headers ({len(actual_headers)}):")
            for i, header in enumerate(actual_headers, 1):
                print(f"   {i:2d}. {header}")
            
            if actual_headers == expected_headers:
                print("\n✅ CSV HEADERS MATCH PERFECTLY!")
                return True
            else:
                print("\n❌ CSV HEADERS MISMATCH!")
                return False
                
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return False
    else:
        print(f"❌ CSV file not found: {csv_file}")
        return False

def main():
    """Run all tests"""
    print("🧪 COMPREHENSIVE EX-GRATIA FORM TESTING")
    print("=" * 60)
    
    tests = [
        ("Application Stages", test_application_stages),
        ("Validation Logic", test_validation_logic),
        ("Damage Type Options", test_damage_type_options),
        ("CSV Structure", test_csv_structure),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 RUNNING: {test_name}")
        try:
            result = test_func()
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   Result: {status}")
            if result:
                passed += 1
        except Exception as e:
            print(f"   Result: ❌ ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Ex-Gratia form is ready!")
        print("\n📋 FORM FEATURES VERIFIED:")
        print("   ✅ All required fields present")
        print("   ✅ Damage type options working")
        print("   ✅ Validation logic correct")
        print("   ✅ CSV structure matches requirements")
        print("   ✅ Submission confirmation available")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main() 