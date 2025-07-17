"""
System Status page - Google Sheets connectivity and troubleshooting
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to sys.path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.status_info import (
    show_google_sheets_status,
    show_fallback_options, 
    show_cache_status,
    show_troubleshooting_guide,
    show_connection_status,
    check_google_services_status
)

def main():
    st.set_page_config(page_title="System Status", page_icon="🔧", layout="wide")
    
    st.title("🔧 System Status & Troubleshooting")
    st.markdown("Monitor Google Sheets connectivity and manage fallback data")
    
    # Main status banner
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        overall_status = check_google_services_status()
        if overall_status == "✅ Online":
            st.success("**System Status:** All services operational")
        elif overall_status == "⚠️ Limited":
            st.warning("**System Status:** Limited functionality (using cache)")
        else:
            st.error("**System Status:** Service disruption detected")
    
    with col2:
        # Show scheduler status
        try:
            from utils.scheduler import report_scheduler
            scheduler_status = report_scheduler.get_schedule_summary()
            
            if scheduler_status['running'] and scheduler_status['email_configured']:
                st.success("**Scheduler:** ✅ Active")
            elif scheduler_status['running']:
                st.warning("**Scheduler:** ⚠️ Running (Email not configured)")
            else:
                st.error("**Scheduler:** ❌ Stopped")
                
        except Exception as e:
            st.error("**Scheduler:** ❌ Error")
    
    with col3:
        st.info(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
    
    with col4:
        if st.button("🔄 Refresh Status"):
            st.rerun()
    
    st.markdown("---")
    
    # Scheduler Status Section
    st.subheader("📅 Automated Reports Scheduler")
    
    try:
        from utils.scheduler import report_scheduler
        scheduler_summary = report_scheduler.get_schedule_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Reports", scheduler_summary['total_reports'])
        
        with col2:
            st.metric("Enabled Reports", scheduler_summary['enabled_reports'])
        
        with col3:
            st.metric("Due Reports", scheduler_summary['due_reports'])
        
        with col4:
            status_color = "🟢" if scheduler_summary['running'] else "🔴"
            st.metric("Scheduler Status", f"{status_color} {'Running' if scheduler_summary['running'] else 'Stopped'}")
        
        # Show scheduled reports
        if len(report_scheduler.scheduled_reports) > 0:
            st.subheader("📋 Scheduled Reports")
            
            schedule_data = []
            for report in report_scheduler.scheduled_reports:
                schedule_data.append({
                    "Report Name": report.name,
                    "Type": report.report_type.replace('_', ' ').title(),
                    "Frequency": report.frequency.title(),
                    "Next Run": report.next_run if report.next_run else "Not scheduled",
                    "Recipients": ", ".join(report.recipients),
                    "Status": "✅ Enabled" if report.enabled else "⏸️ Disabled"
                })
            
            df = pd.DataFrame(schedule_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No reports currently scheduled. Visit the Reports page to set up automated reports.")
        
        # Scheduler controls
        st.subheader("🎛️ Scheduler Controls")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if not scheduler_summary['running']:
                if st.button("▶️ Start Scheduler"):
                    report_scheduler.start_scheduler()
                    st.success("Scheduler started!")
                    st.rerun()
            else:
                if st.button("⏹️ Stop Scheduler"):
                    report_scheduler.stop_scheduler()
                    st.success("Scheduler stopped!")
                    st.rerun()
        
        with col2:
            if st.button("📧 Test Email Settings"):
                if report_scheduler.test_email_settings():
                    st.success("Email test successful!")
                else:
                    st.error("Email test failed. Check your email settings.")
        
        with col3:
            if st.button("🔄 Reload Schedules"):
                report_scheduler.load_schedules()
                st.success("Schedules reloaded!")
                st.rerun()
                
    except Exception as e:
        st.error(f"Error loading scheduler status: {e}")
    
    st.markdown("---")
    
    # Tabs for different status sections
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Data Status", "🔧 Cache Management", "📊 Sheet Info", "🆘 Help"])
    
    with tab1:
        show_data_status_tab()
    
    with tab2:
        show_cache_management_tab()
    
    with tab3:
        show_sheet_info_tab()
    
    with tab4:
        show_help_tab()

def test_google_sheets_connection():
    """Test the connection to Google Sheets"""
    try:
        from utils.google_sheets import get_sheet_data
        
        # Try to read a small amount of data
        with st.spinner("Testing Google Sheets connection..."):
            test_data = get_sheet_data('Daily Agency Stats')
            
        if not test_data.empty:
            return {
                'connected': True,
                'rows': len(test_data),
                'last_test': datetime.now().isoformat()
            }
        else:
            return {
                'connected': False,
                'error': 'No data returned from Google Sheets',
                'last_test': datetime.now().isoformat()
            }
            
    except Exception as e:
        error_msg = str(e)
        return {
            'connected': False,
            'error': error_msg,
            'last_test': datetime.now().isoformat()
        }

def show_working_system_info():
    """Show information when system is working normally"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🟢 Google Sheets", "Connected", delta="Operational")
    
    with col2:
        st.metric("📊 Data Source", "Live Data", delta="Real-time")
    
    with col3:
        st.metric("🔄 Last Update", "Just now", delta="Fresh")
    
    st.info("""
    **✅ All systems operational!**
    
    - Google Sheets API is responding normally
    - Data is being loaded in real-time
    - All dashboard features are fully functional
    """)

def show_data_status_tab():
    """Show data status and availability"""
    
    st.subheader("📋 Data Source Status")
    
    # Test each data source
    data_sources = [
        ('Daily Agency Stats', 'Agency performance data'),
        ('Daily Agent Totals', 'Individual agent metrics'),
        ('Daily Lead Vendor Totals', 'Campaign and vendor data')
    ]
    
    for sheet_name, description in data_sources:
        with st.expander(f"📊 {sheet_name}"):
            try:
                # Try to get data from fallback system
                from utils.google_sheets_fallback import get_sheet_data_with_fallback
                df = get_sheet_data_with_fallback(sheet_name)
                
                if not df.empty:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Rows", len(df))
                    with col2:
                        st.metric("Columns", len(df.columns))
                    with col3:
                        # Determine data source
                        if hasattr(df, '_cached_data'):
                            st.metric("Source", "Cache")
                        else:
                            st.metric("Source", "Sample/Live")
                    
                    st.write(f"**Description:** {description}")
                    st.write(f"**Columns:** {', '.join(df.columns.tolist())}")
                    
                    # Show preview
                    if st.checkbox(f"Show data preview", key=f"preview_{sheet_name}"):
                        st.dataframe(df.head(), use_container_width=True)
                else:
                    st.warning(f"No data available for {sheet_name}")
                    
            except Exception as e:
                st.error(f"Error accessing {sheet_name}: {e}")

def show_cache_management_tab():
    """Show cache management options"""
    
    st.subheader("🔧 Cache Management")
    
    try:
        from utils.google_sheets_fallback import get_cache_info, clear_cache
        
        cache_info = get_cache_info()
        
        if cache_info:
            st.success("📋 **Cached Data Available:**")
            
            # Display cache information in a table
            cache_data = []
            for sheet_name, info in cache_info.items():
                cache_data.append({
                    'Sheet Name': sheet_name,
                    'Size (bytes)': info['size'],
                    'Last Modified': info['modified'],
                    'Age': calculate_cache_age(info['modified'])
                })
            
            if cache_data:
                cache_df = pd.DataFrame(cache_data)
                st.dataframe(cache_df, use_container_width=True)
                
                # Cache management actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🗑️ Clear All Cache"):
                        clear_cache()
                        st.rerun()
                
                with col2:
                    if st.button("📊 View Cache Details"):
                        show_detailed_cache_info(cache_info)
                
                with col3:
                    max_age = st.selectbox("Cache Max Age", [1, 6, 12, 24, 48], index=3)
                    st.write(f"Cache expires after {max_age} hours")
        else:
            st.info("No cached data available.")
            st.write("Cache will be created when Google Sheets data is successfully loaded.")
            
    except Exception as e:
        st.error(f"Error accessing cache system: {e}")

def calculate_cache_age(modified_time: str) -> str:
    """Calculate how old cached data is"""
    try:
        modified_dt = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))
        age = datetime.now() - modified_dt.replace(tzinfo=None)
        
        if age.days > 0:
            return f"{age.days} days"
        elif age.seconds > 3600:
            hours = age.seconds // 3600
            return f"{hours} hours"
        elif age.seconds > 60:
            minutes = age.seconds // 60
            return f"{minutes} minutes"
        else:
            return "< 1 minute"
    except:
        return "Unknown"

def show_detailed_cache_info(cache_info):
    """Show detailed cache information"""
    st.subheader("📊 Detailed Cache Information")
    
    for sheet_name, info in cache_info.items():
        with st.expander(f"Cache Details: {sheet_name}"):
            st.write(f"**File Size:** {info['size']} bytes")
            st.write(f"**Last Modified:** {info['modified']}")
            st.write(f"**Age:** {calculate_cache_age(info['modified'])}")

def show_sheet_info_tab():
    """Show Google Sheets information and configuration"""
    
    st.subheader("📊 Google Sheets Configuration")
    
    try:
        # Show spreadsheet info
        st.write("**Expected Sheet Names:**")
        expected_sheets = [
            "Daily Agency Stats",
            "Daily Agent Totals", 
            "Daily Lead Vendor Totals"
        ]
        
        for sheet in expected_sheets:
            st.write(f"- {sheet}")
        
        # Connection test
        st.subheader("🔌 Connection Test")
        
        if st.button("Test Connection"):
            result = test_google_sheets_connection()
            
            if result['connected']:
                st.success(f"✅ Connected successfully! Found {result['rows']} rows of data.")
            else:
                st.error(f"❌ Connection failed: {result['error']}")
        
        # Service status
        st.subheader("🌐 Google Services Status")
        
        status = check_google_services_status()
        if status == "operational":
            st.success("🟢 Google Sheets API: Operational")
        elif status == "issues":
            st.warning("🟡 Google Sheets API: Experiencing issues")
        else:
            st.info("🔵 Google Sheets API: Status unknown")
            
    except Exception as e:
        st.error(f"Error getting sheet information: {e}")

def show_help_tab():
    """Show help and troubleshooting information"""
    
    st.subheader("🆘 Help & Troubleshooting")
    
    # Quick actions
    st.write("**Quick Actions:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Retry Connection"):
            st.rerun()
    
    with col2:
        if st.button("📋 View Troubleshooting"):
            show_troubleshooting_guide()
    
    with col3:
        if st.button("🔧 System Tests"):
            run_system_tests()
    
    # Common issues and solutions
    st.subheader("❓ Common Issues")
    
    with st.expander("🔴 503 Service Unavailable"):
        st.markdown("""
        **What it means:** Google Sheets service is temporarily down
        
        **What to do:**
        1. Wait 5-10 minutes and try again
        2. Use cached data (automatic)
        3. Check Google's service status
        
        **This is normal and temporary!**
        """)
    
    with st.expander("⏰ 429 Rate Limit Exceeded"):
        st.markdown("""
        **What it means:** Too many API requests in a short time
        
        **What to do:**
        1. Wait 1-2 minutes
        2. Avoid refreshing rapidly
        3. Use scheduled reports instead
        """)
    
    with st.expander("🔒 403 Permission Denied"):
        st.markdown("""
        **What it means:** Dashboard doesn't have access to your sheet
        
        **What to do:**
        1. Check sheet sharing settings
        2. Verify service account email
        3. Confirm spreadsheet ID is correct
        """)
    
    with st.expander("🔍 400 Bad Request / Range Parse Error"):
        st.markdown("""
        **What it means:** Invalid sheet name or range specification
        
        **What to do:**
        1. Verify sheet names match exactly
        2. Check for special characters in sheet names
        3. Ensure sheets exist in your spreadsheet
        """)

def run_system_tests():
    """Run comprehensive system tests"""
    
    st.subheader("🧪 System Tests")
    
    with st.spinner("Running system tests..."):
        
        tests = []
        
        # Test 1: Import modules
        try:
            from utils.google_sheets_fallback import get_sheet_data_with_fallback
            from utils.reports import report_generator
            from utils.settings import settings_manager
            from utils.scheduler import report_scheduler
            tests.append(("✅ Module Imports", "All modules imported successfully"))
        except Exception as e:
            tests.append(("❌ Module Imports", f"Import error: {e}"))
        
        # Test 2: Fallback data
        try:
            test_data = get_sheet_data_with_fallback('Daily Agency Stats')
            if not test_data.empty:
                tests.append(("✅ Fallback Data", f"Sample data available ({len(test_data)} rows)"))
            else:
                tests.append(("⚠️ Fallback Data", "No sample data available"))
        except Exception as e:
            tests.append(("❌ Fallback Data", f"Error: {e}"))
        
        # Test 3: Report generation
        try:
            report = report_generator.generate_daily_report()
            if len(report) > 100:
                tests.append(("✅ Report Generation", f"Report generated ({len(report)} chars)"))
            else:
                tests.append(("⚠️ Report Generation", "Report too short"))
        except Exception as e:
            tests.append(("❌ Report Generation", f"Error: {e}"))
        
        # Test 4: Settings system
        try:
            summary = settings_manager.get_settings_summary()
            tests.append(("✅ Settings System", f"Settings loaded ({summary['total_users']} users)"))
        except Exception as e:
            tests.append(("❌ Settings System", f"Error: {e}"))
        
        # Test 5: Scheduler system
        try:
            scheduler_summary = report_scheduler.get_schedule_summary()
            tests.append(("✅ Scheduler System", f"Scheduler loaded ({scheduler_summary['total_reports']} reports)"))
        except Exception as e:
            tests.append(("❌ Scheduler System", f"Error: {e}"))
    
    # Display test results
    st.write("**Test Results:**")
    for test_name, result in tests:
        if "✅" in test_name:
            st.success(f"{test_name}: {result}")
        elif "⚠️" in test_name:
            st.warning(f"{test_name}: {result}")
        else:
            st.error(f"{test_name}: {result}")
    
    # Overall status
    passed = len([t for t in tests if "✅" in t[0]])
    total = len(tests)
    
    if passed == total:
        st.balloons()
        st.success(f"🎉 All {total} tests passed! System is fully operational.")
    elif passed >= total * 0.8:
        st.info(f"✅ {passed}/{total} tests passed. System is mostly operational.")
    else:
        st.warning(f"⚠️ Only {passed}/{total} tests passed. Some issues detected.")

if __name__ == "__main__":
    main() 