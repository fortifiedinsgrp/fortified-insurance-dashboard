"""
Fortified Insurance Solutions - Agency Reporting Dashboard
Main application entry point
"""

import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Fortified Insurance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #555;
    }
    div[data-testid="metric-container"] > div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'selected_agency' not in st.session_state:
    st.session_state.selected_agency = "All Agencies"
if 'date_range' not in st.session_state:
    st.session_state.date_range = "Today"
if 'start_date' not in st.session_state:
    st.session_state.start_date = date.today()
if 'end_date' not in st.session_state:
    st.session_state.end_date = date.today()

# Initialize automated report scheduler
# This ensures reports are sent automatically without manual intervention
if 'scheduler_initialized' not in st.session_state:
    try:
        from utils.scheduler import report_scheduler
        from utils.reports import ReportGenerator
        
        # Register report generators with the scheduler
        report_generator = ReportGenerator()
        
        # Register all report types
        report_scheduler.register_report_generator('daily_performance', report_generator.generate_daily_report)
        report_scheduler.register_report_generator('weekly_aggregated', report_generator.generate_weekly_report)
        report_scheduler.register_report_generator('monthly_comprehensive', report_generator.generate_monthly_report)
        report_scheduler.register_report_generator('agent_performance', report_generator.generate_agent_performance_report)
        report_scheduler.register_report_generator('campaign_analysis', report_generator.generate_campaign_analysis_report)
        report_scheduler.register_report_generator('executive_summary', report_generator.generate_executive_summary)
        
        # Start the scheduler background thread
        if not report_scheduler.running:
            report_scheduler.start_scheduler()
            st.session_state.scheduler_initialized = True
            
    except Exception as e:
        st.error(f"Failed to initialize automated scheduler: {e}")
        st.session_state.scheduler_initialized = False

# Main app header
st.title("🏢 Fortified Insurance Solutions")
st.markdown("### Agency Performance Dashboard")

# Sidebar navigation
with st.sidebar:
    st.markdown("# 🏢 Fortified Insurance")
    st.markdown("---")
    
    st.markdown("### 📍 Navigation")
    
    # Navigation links to actual pages
    st.markdown("**📊 Dashboard**")
    st.page_link("pages/1_📊_Dashboard.py", label="View Live Dashboard", icon="📊")
    
    st.markdown("**📋 Reports**")
    st.page_link("pages/2_📋_Reports.py", label="Generate Reports", icon="📋")
    
    st.markdown("**🔧 System Status**")
    st.page_link("pages/3_🔧_System_Status.py", label="Check System Status", icon="🔧")
    
    st.markdown("---")
    st.markdown("### 📧 Support")
    st.markdown("For assistance, contact:")
    st.markdown("**support@fortified.com**")
    
    # Add user info if available
    st.markdown("---")
    st.markdown("### 👤 User")
    st.markdown("**Marc** - CEO")
    st.markdown("*Fortified LaunchLab*")

# Main landing page content
st.markdown("## 👋 Welcome to Fortified Insurance Dashboard")

# Feature overview
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📊 Dashboard
    **Real-time Performance Metrics**
    - Agency profitability tracking
    - Agent performance analysis
    - Campaign ROAS monitoring
    - At-risk agent identification
    """)
    st.page_link("pages/1_📊_Dashboard.py", label="Open Dashboard →", icon="📊")

with col2:
    st.markdown("""
    ### 📋 Reports
    **Automated Report Generation**
    - 6 types of detailed reports
    - Date and agency filtering
    - Email scheduling & delivery
    - Settings management
    """)
    st.page_link("pages/2_📋_Reports.py", label="Generate Reports →", icon="📋")

with col3:
    st.markdown("""
    ### 🔧 System Status
    **Monitoring & Troubleshooting**
    - Google Sheets connectivity
    - Cache management
    - Error handling status
    - Troubleshooting guides
    """)
    st.page_link("pages/3_🔧_System_Status.py", label="Check Status →", icon="🔧")

st.markdown("---")

# Quick status overview
st.markdown("### 🎯 Quick Status Overview")

# Test connection status
try:
    from utils.google_sheets_fallback import get_sheet_data_with_fallback
    
    # Quick data test
    test_data = get_sheet_data_with_fallback('Daily Agency Stats')
    
    if not test_data.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Data Source", "Available", delta="✅ Ready")
        
        with col2:
            st.metric("📋 Report System", "Operational", delta="✅ Ready")
        
        with col3:
            st.metric("🔧 Monitoring", "Active", delta="✅ Ready")
        
        with col4:
            st.metric("📈 Analytics", "Live", delta="✅ Ready")
        
        st.success("🎉 All systems operational! Click any navigation link above to get started.")
    else:
        st.warning("⚠️ System initializing... Please check System Status page for details.")

except Exception as e:
    st.error("❌ System check failed. Please check System Status page for troubleshooting.")

# Quick start guide
with st.expander("🚀 Quick Start Guide", expanded=False):
    st.markdown("""
    **Getting Started with Your Dashboard:**
    
    1. **📊 Dashboard Page**: View real-time performance metrics
       - Select agency and date range
       - Monitor agent profitability
       - Track campaign performance
    
    2. **📋 Reports Page**: Generate and schedule reports
       - Choose from 6 report types
       - Filter by date and agency
       - Set up automated email delivery
    
    3. **🔧 System Status**: Monitor system health
       - Check Google Sheets connectivity
       - Manage data cache
       - Access troubleshooting tools
    
    **Need Help?** Contact support@fortified.com
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        <p>Fortified Insurance Dashboard v1.0 | Built with ❤️ by Fortified LaunchLab</p>
    </div>
    """,
    unsafe_allow_html=True
)