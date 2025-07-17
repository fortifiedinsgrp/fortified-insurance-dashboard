#!/usr/bin/env python3
"""
Test script for the insurance dashboard reporting system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported successfully"""
    try:
        print("Testing imports...")
        
        from utils.settings import settings_manager
        print("✅ Settings module imported")
        
        from utils.scheduler import report_scheduler
        print("✅ Scheduler module imported")
        
        from utils.reports import report_generator
        print("✅ Reports module imported")
        
        print("✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_settings():
    """Test settings functionality"""
    try:
        from utils.settings import settings_manager
        
        print("\nTesting settings...")
        
        # Test getting settings summary
        summary = settings_manager.get_settings_summary()
        print(f"✅ Settings summary: {summary}")
        
        # Test adding a user
        success = settings_manager.add_user(
            name="Test User",
            email="test@example.com",
            role="admin"
        )
        print(f"✅ Add user result: {success}")
        
        # Test getting users
        users = settings_manager.users
        print(f"✅ Total users: {len(users)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def test_reports():
    """Test report generation"""
    try:
        from utils.reports import report_generator
        
        print("\nTesting report generation...")
        
        # Test generating a simple report
        daily_report = report_generator.generate_daily_report()
        print(f"✅ Daily report generated ({len(daily_report)} characters)")
        
        weekly_report = report_generator.generate_weekly_report()
        print(f"✅ Weekly report generated ({len(weekly_report)} characters)")
        
        return True
        
    except Exception as e:
        print(f"❌ Report generation error: {e}")
        return False

def test_scheduler():
    """Test scheduler functionality"""
    try:
        from utils.scheduler import report_scheduler
        
        print("\nTesting scheduler...")
        
        # Test getting scheduler summary
        summary = report_scheduler.get_schedule_summary()
        print(f"✅ Scheduler summary: {summary}")
        
        # Test adding a scheduled report
        report_id = report_scheduler.add_scheduled_report(
            name="Test Daily Report",
            report_type="daily",
            frequency="daily",
            recipients=["test@example.com"]
        )
        print(f"✅ Added scheduled report: {report_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Insurance Dashboard Reporting System")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_settings,
        test_reports,
        test_scheduler
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\n📋 Next steps:")
        print("1. Run 'streamlit run app.py' to start the dashboard")
        print("2. Navigate to the '📋 Reports' page")
        print("3. Configure email settings in the Settings tab")
        print("4. Add users in the User Management tab")
        print("5. Generate ad hoc reports or schedule automated ones")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    main() 