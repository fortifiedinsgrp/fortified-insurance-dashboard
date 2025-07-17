"""
Status information and user guidance for Google Sheets issues
"""

import streamlit as st
from datetime import datetime
import requests


def show_google_sheets_status():
    """Display Google Sheets service status and guidance"""
    
    st.markdown("""
    ## 🔄 Google Sheets Service Status
    
    **Current Issue:** Google Sheets API is returning a 503 "Service Unavailable" error.
    
    ### What does this mean?
    - **503 Error**: The Google Sheets service is temporarily down or experiencing high load
    - **Not your fault**: This is a Google infrastructure issue, not a problem with your dashboard
    - **Temporary**: These issues typically resolve within minutes to hours
    
    ### What's happening now:
    ✅ **Your dashboard is still working** - We're using cached data or sample data  
    ✅ **Your settings are preserved** - All your configurations are safe  
    ✅ **Reports still generate** - Using the most recent available data  
    """)


def show_fallback_options():
    """Show available options when using fallback data"""
    
    st.markdown("""
    ### 🛡️ Fallback Data Options
    
    When Google Sheets is unavailable, your dashboard automatically:
    
    1. **Uses Cached Data** 📋 - Recent data from successful API calls
    2. **Shows Sample Data** 📊 - Realistic sample data for testing
    3. **Maintains Functionality** ⚙️ - All features continue to work
    
    ### What you can do:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Retry Connection", help="Try to reconnect to Google Sheets"):
            st.rerun()
    
    with col2:
        if st.button("📊 View Cache Info", help="See what cached data is available"):
            show_cache_status()
    
    with col3:
        if st.button("🆘 Get Help", help="Get additional support information"):
            show_troubleshooting_guide()


def show_cache_status():
    """Display cache status information"""
    try:
        from .google_sheets_fallback import get_cache_info
        cache_info = get_cache_info()
        
        if cache_info:
            st.success("📋 **Cached Data Available:**")
            for sheet_name, info in cache_info.items():
                st.write(f"- **{sheet_name}**: {info['size']} bytes, updated {info['modified']}")
        else:
            st.info("No cached data available. Using sample data.")
            
    except Exception as e:
        st.warning(f"Could not retrieve cache info: {e}")


def show_troubleshooting_guide():
    """Show detailed troubleshooting information"""
    
    st.markdown("""
    ## 🆘 Troubleshooting Guide
    
    ### Immediate Actions:
    1. **Wait 5-10 minutes** - Most 503 errors resolve automatically
    2. **Refresh the page** - Click the "🔄 Retry Connection" button
    3. **Check your internet** - Ensure you have a stable connection
    
    ### If the issue persists:
    
    #### Check Google's Status:
    - Visit [Google Workspace Status](https://www.google.com/appsstatus/dashboard/)
    - Look for "Google Sheets API" or "Google Drive API" issues
    
    #### Verify Your Setup:
    - Ensure your Google Sheets credentials are valid
    - Check that your spreadsheet ID is correct
    - Verify you have proper permissions to access the sheet
    
    #### Alternative Actions:
    - **Use the Reports feature** - Generate reports with available data
    - **Export your settings** - Back up your dashboard configuration
    - **Schedule reports** - Set up automated delivery for when service resumes
    
    ### When to Contact Support:
    - Error persists for more than 2 hours
    - You see permission or authentication errors
    - The dashboard stops working entirely
    """)


def show_api_rate_limit_info():
    """Show information about API rate limits"""
    
    st.warning("""
    ### ⏰ API Rate Limit Reached
    
    **What happened:** Your application has exceeded Google's API request limits.
    
    **Google Sheets API Limits:**
    - 300 requests per minute per project
    - 100 requests per 100 seconds per user
    
    **What to do:**
    1. **Wait 1-2 minutes** before trying again
    2. **Reduce refresh frequency** if you're manually refreshing often
    3. **Use cached data** in the meantime
    
    **Prevention:**
    - Avoid rapidly refreshing the dashboard
    - Use the built-in caching features
    - Schedule reports instead of manual generation
    """)


def show_permission_error_info():
    """Show information about permission errors"""
    
    st.error("""
    ### 🔒 Permission Error
    
    **What happened:** The dashboard doesn't have permission to access your Google Sheet.
    
    **Common causes:**
    - Service account email not added to the sheet
    - Sheet sharing settings changed
    - Incorrect spreadsheet ID
    
    **How to fix:**
    1. **Check sheet sharing** - Ensure the service account email has access
    2. **Verify spreadsheet ID** - Make sure it's correct in your settings
    3. **Re-share the sheet** if necessary
    
    **Need the service account email?** Check your Google Cloud Console.
    """)


def show_connection_status(error_message: str = None):
    """Show appropriate status message based on error type"""
    
    if not error_message:
        st.success("✅ **Google Sheets Connected** - All systems operational")
        return
    
    error_lower = error_message.lower()
    
    if "503" in error_message or "unavailable" in error_lower:
        show_google_sheets_status()
        show_fallback_options()
        
    elif "429" in error_message or "rate limit" in error_lower:
        show_api_rate_limit_info()
        
    elif "403" in error_message or "permission" in error_lower:
        show_permission_error_info()
        
    elif "404" in error_message or "not found" in error_lower:
        st.error("""
        ### 🔍 Sheet Not Found
        
        The specified Google Sheet could not be found. Please check:
        - Spreadsheet ID is correct
        - Sheet name is spelled correctly
        - Sheet hasn't been deleted or moved
        """)
        
    else:
        st.error(f"""
        ### ⚠️ Unexpected Error
        
        **Error:** {error_message}
        
        **Suggestions:**
        - Try refreshing the page
        - Check your internet connection
        - Verify your Google Sheets setup
        """)
        show_fallback_options()


def check_google_services_status():
    """Check if Google services are experiencing known issues"""
    try:
        # This is a simplified check - in production you might want to use Google's actual status API
        response = requests.get("https://www.googleapis.com/sheets/v4/", timeout=5)
        if response.status_code == 200:
            return "operational"
        else:
            return "issues"
    except:
        return "unknown"


def show_service_status_banner():
    """Show a banner with current service status"""
    status = check_google_services_status()
    
    if status == "operational":
        st.success("🟢 Google Sheets API: Operational")
    elif status == "issues":
        st.warning("🟡 Google Sheets API: Experiencing issues")
    else:
        st.info("🔵 Google Sheets API: Status unknown") 