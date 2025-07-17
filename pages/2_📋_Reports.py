"""
Reports page for ad hoc report generation and scheduling
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, time
from typing import Dict, List

# Add the parent directory to sys.path to import utils
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.google_sheets import get_sheet_data
from utils.reports import ReportGenerator
from utils.calculations import get_weekly_summary
from utils.scheduler import report_scheduler
from utils.settings import settings_manager

def main():
    st.set_page_config(page_title="Reports", page_icon="📋", layout="wide")
    
    st.title("📋 Ad Hoc Reports & Scheduling")
    st.markdown("Generate custom reports and manage automated scheduling")
    
    # Sidebar for report configuration
    with st.sidebar:
        st.header("Report Configuration")
        
        # Report type selection
        report_type = st.selectbox(
            "Select Report Type",
            options=[
                "daily",
                "weekly", 
                "monthly",
                "agent_performance",
                "campaign_analysis",
                "executive_summary"
            ],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        # Date/Time period selection for ALL report types
        st.subheader("📅 Date Selection")
        
        if report_type == 'daily':
            # For daily reports, select a specific date
            report_date = st.date_input(
                "Report Date", 
                datetime.now().date(),
                help="Select the specific date for the daily report"
            )
            start_date = end_date = report_date
            
        elif report_type in ['weekly', 'monthly']:
            time_period = st.selectbox(
                "Time Period",
                options=['Current Period', 'Last 7 Days', 'Last 30 Days', 'Custom Range']
            )
            
            if time_period == 'Custom Range':
                start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
                end_date = st.date_input("End Date", datetime.now())
            elif time_period == 'Last 7 Days':
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=7)
            elif time_period == 'Last 30 Days':
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)
            else:  # Current Period
                if report_type == 'weekly':
                    # Current week
                    today = datetime.now().date()
                    start_date = today - timedelta(days=today.weekday())
                    end_date = start_date + timedelta(days=6)
                else:  # monthly
                    # Current month
                    today = datetime.now().date()
                    start_date = today.replace(day=1)
                    end_date = today
                    
        else:  # agent_performance, campaign_analysis, executive_summary
            time_period = st.selectbox(
                "Analysis Period",
                options=['Today', 'Yesterday', 'Last 7 Days', 'Last 30 Days', 'Custom Range']
            )
            
            if time_period == 'Custom Range':
                start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
                end_date = st.date_input("End Date", datetime.now())
            elif time_period == 'Today':
                start_date = end_date = datetime.now().date()
            elif time_period == 'Yesterday':
                start_date = end_date = datetime.now().date() - timedelta(days=1)
            elif time_period == 'Last 7 Days':
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=7)
            else:  # Last 30 Days
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)
        
        # Agency selection
        st.subheader("🏢 Agency Filter")
        try:
            from utils.google_sheets import get_agency_list
            agencies = get_agency_list()
            agency_options = ["All Agencies"] + agencies
        except:
            agency_options = ["All Agencies", "Agency A", "Agency B", "Agency C"]
        
        selected_agency = st.selectbox(
            "Select Agency",
            options=agency_options,
            help="Filter report data by specific agency"
        )
        
        # Show selected parameters
        st.markdown("---")
        st.markdown("**📋 Report Parameters:**")
        st.write(f"**Type:** {report_type.replace('_', ' ').title()}")
        st.write(f"**Date Range:** {start_date} to {end_date}")
        st.write(f"**Agency:** {selected_agency}")
        
        # Generate report button
        generate_report = st.button("Generate Report", type="primary")
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Generated Report", "⚙️ Settings", "📅 Scheduling", "👥 User Management"])
    
    with tab1:
        st.header("Generated Report")
        
        if generate_report:
            with st.spinner(f"Generating {report_type.replace('_', ' ').title()} report..."):
                try:
                    # Generate the report with date and agency filtering
                    if report_type:
                        report_html = report_generator.generate_report(
                            report_type,
                            start_date=start_date,
                            end_date=end_date,
                            agency=selected_agency if selected_agency != "All Agencies" else None
                        )
                    else:
                        st.error("Please select a report type")
                    
                    # Display the report
                    st.components.v1.html(report_html, height=800, scrolling=True)
                    
                    # Option to download report
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("📧 Email Report"):
                            show_email_dialog(report_html, report_type)
                    
                    with col2:
                        # Provide HTML download
                        st.download_button(
                            label="📥 Download HTML",
                            data=report_html,
                            file_name=f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                            mime="text/html"
                        )
                
                except Exception as e:
                    st.error(f"Error generating report: {e}")
        else:
            st.info("Select a report type and click 'Generate Report' to view the results.")
            
            # Show sample data if available
            try:
                with st.expander("📊 Data Preview"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.subheader("Agency Stats")
                        agency_data = get_sheet_data('Daily Agency Stats')
                        if not agency_data.empty:
                            st.dataframe(agency_data.head(), use_container_width=True)
                        else:
                            st.info("No agency data available")
                    
                    with col2:
                        st.subheader("Agent Totals")
                        agent_data = get_sheet_data('Daily Agent Totals')
                        if not agent_data.empty:
                            st.dataframe(agent_data.head(), use_container_width=True)
                        else:
                            st.info("No agent data available")
                    
                    with col3:
                        st.subheader("Vendor Totals")
                        vendor_data = get_sheet_data('Daily Lead Vendor Totals')
                        if not vendor_data.empty:
                            st.dataframe(vendor_data.head(), use_container_width=True)
                        else:
                            st.info("No vendor data available")
                            
                # Weekly aggregation demo
                if st.checkbox("Show Weekly Aggregation"):
                    st.subheader("Weekly Data Aggregation")
                    try:
                        agency_data = get_sheet_data('Daily Agency Stats')
                        if not agency_data.empty and 'Date' in agency_data.columns:
                            weekly_data = get_weekly_summary(agency_data)
                            st.dataframe(weekly_data, use_container_width=True)
                        else:
                            st.info("Weekly aggregation requires data with Date column")
                    except Exception as e:
                        st.error(f"Error creating weekly aggregation: {e}")
                        
            except Exception as e:
                st.error(f"Error loading data preview: {e}")
    
    with tab2:
        st.header("Settings & Configuration")
        
        # Email settings
        st.subheader("Email Configuration")
        col1, col2 = st.columns(2)
        
        with col1:
            email_sender = st.text_input(
                "Sender Email", 
                value=settings_manager.email_settings.sender_email,
                help="Gmail address for sending reports"
            )
            sender_name = st.text_input(
                "Sender Name",
                value=settings_manager.email_settings.sender_name
            )
            smtp_server = st.text_input(
                "SMTP Server",
                value=settings_manager.email_settings.smtp_server
            )
        
        with col2:
            email_password = st.text_input(
                "App Password", 
                type="password",
                help="Gmail app password (not your regular password)"
            )
            smtp_port = st.number_input(
                "SMTP Port",
                value=settings_manager.email_settings.smtp_port,
                min_value=1,
                max_value=65535
            )
            use_tls = st.checkbox(
                "Use TLS",
                value=settings_manager.email_settings.use_tls
            )
        
        if st.button("Save Email Settings"):
            success = settings_manager.update_email_settings(
                sender_email=email_sender,
                sender_password=email_password,
                sender_name=sender_name,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                use_tls=use_tls
            )
            if success:
                st.success("Email settings saved successfully!")
            else:
                st.error("Error saving email settings")
        
        if st.button("Test Email Settings"):
            if settings_manager.validate_email_settings():
                success = report_scheduler.test_email_settings()
                if success:
                    st.success("Test email sent successfully!")
                else:
                    st.error("Failed to send test email")
            else:
                st.error("Email settings are incomplete")
        
        # Report settings
        st.subheader("Report Configuration")
        col1, col2 = st.columns(2)
        
        with col1:
            currency_symbol = st.text_input(
                "Currency Symbol",
                value=settings_manager.report_settings.currency_symbol,
                max_chars=3
            )
        
        with col2:
            profitability_threshold = st.number_input(
                "Profitability Threshold ($)",
                value=settings_manager.report_settings.profitability_threshold,
                min_value=0.0,
                step=10.0
            )
            include_charts = st.checkbox(
                "Include Charts in Reports",
                value=settings_manager.report_settings.include_charts
            )
        
        if st.button("Save Report Settings"):
            success = settings_manager.update_report_settings(
                profitability_threshold=profitability_threshold,
                currency_symbol=currency_symbol,
                include_charts=include_charts
            )
            if success:
                st.success("Report settings saved successfully!")
            else:
                st.error("Error saving report settings")
    
    with tab3:
        st.header("Report Scheduling")
        
        # Scheduler status
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
        
        # Scheduler controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start Scheduler"):
                report_scheduler.start_scheduler()
                st.success("Scheduler started!")
                st.rerun()
        with col2:
            if st.button("⏹️ Stop Scheduler"):
                report_scheduler.stop_scheduler()
                st.success("Scheduler stopped!")
                st.rerun()
        
        st.divider()
        
        # Add new scheduled report
        st.subheader("Schedule New Report")
        
        with st.form("schedule_report_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                schedule_name = st.text_input("Report Name", placeholder="Daily Agency Report")
                schedule_type = st.selectbox(
                    "Report Type",
                    options=["daily_performance", "weekly_aggregated", "monthly_comprehensive", "agent_performance", "campaign_analysis", "executive_summary"],
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                frequency = st.selectbox("Frequency", options=["daily", "weekly", "monthly"])
                
                # Time selection
                report_time = st.time_input(
                    "Report Time",
                    value=time(8, 0),
                    help="When to send the report (your local time)"
                )
            
            with col2:
                # User role selection
                user_role = st.selectbox(
                    "User Role",
                    options=["agency_owner", "management", "admin"],
                    format_func=lambda x: x.replace('_', ' ').title(),
                    help="Determines data access level"
                )
                
                # Agency filter for agency owners
                agency_filter = None
                if user_role == "agency_owner":
                    # Get available agencies from the data
                    try:
                        agency_data = get_sheet_data('Daily Agency Stats')
                        if not agency_data.empty and 'Agency' in agency_data.columns:
                            agencies = sorted(agency_data['Agency'].dropna().unique())
                            agency_filter = st.selectbox(
                                "Agency",
                                options=agencies,
                                help="Select the specific agency for this report"
                            )
                        else:
                            agency_filter = st.text_input(
                                "Agency Name",
                                help="Enter the agency name for filtering"
                            )
                    except:
                        agency_filter = st.text_input(
                            "Agency Name",
                            help="Enter the agency name for filtering"
                        )
                else:
                    st.info("Management and Admin users see all agencies")
                
                # Campaign data inclusion
                include_campaigns = st.checkbox(
                    "Include Campaign Data",
                    value=(user_role in ["management", "admin"]),
                    disabled=(user_role == "agency_owner"),
                    help="Campaign data only available for Management and Admin roles"
                )
            
            with col3:
                # Get available email addresses
                agency_owners = settings_manager.get_agency_owners()
                management_team = settings_manager.get_management_team()
                
                all_users = agency_owners + management_team
                email_options = [user.email for user in all_users]
                
                if email_options:
                    selected_emails = st.multiselect(
                        "Recipients",
                        options=email_options,
                        help="Select users to receive this report"
                    )
                else:
                    st.warning("No users configured. Add users in the User Management tab.")
                    selected_emails = []
                
                enabled = st.checkbox("Enable Report", value=True)
                
                # Show preview of report schedule
                if frequency == "daily" and report_time:
                    st.info(f"📅 Will run daily at {report_time.strftime('%H:%M')} with yesterday's data")
                elif frequency == "weekly" and report_time:
                    st.info(f"📅 Will run weekly on Mondays at {report_time.strftime('%H:%M')} with previous week's data (Sun-Sat)")
                elif frequency == "monthly" and report_time:
                    st.info(f"📅 Will run monthly on the 1st at {report_time.strftime('%H:%M')} with previous month's data")
            
            submitted = st.form_submit_button("Schedule Report")
            
            if submitted and schedule_name and selected_emails and schedule_type and frequency and report_time:
                report_id = report_scheduler.add_scheduled_report(
                    name=schedule_name,
                    report_type=schedule_type,
                    frequency=frequency,
                    time=report_time.strftime('%H:%M'),
                    recipients=selected_emails,
                    user_role=user_role,
                    agency_filter=agency_filter,
                    include_campaigns=include_campaigns
                )
                st.success(f"Report scheduled successfully! ID: {report_id}")
                st.rerun()
        
        # Existing scheduled reports
        st.subheader("Scheduled Reports")
        
        if report_scheduler.scheduled_reports:
            for report in report_scheduler.scheduled_reports:
                with st.expander(f"📊 {report.name} ({report.frequency})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Type:** {report.report_type.replace('_', ' ').title()}")
                        st.write(f"**Recipients:** {', '.join(report.recipients)}")
                        st.write(f"**Status:** {'✅ Enabled' if report.enabled else '❌ Disabled'}")
                    
                    with col2:
                        if report.last_run:
                            last_run = datetime.fromisoformat(report.last_run)
                            st.write(f"**Last Run:** {last_run.strftime('%Y-%m-%d %H:%M')}")
                        else:
                            st.write("**Last Run:** Never")
                        
                        if report.next_run:
                            next_run = datetime.fromisoformat(report.next_run)
                            st.write(f"**Next Run:** {next_run.strftime('%Y-%m-%d %H:%M')}")
                    
                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{report.id}"):
                            if report_scheduler.remove_scheduled_report(report.id):
                                st.success("Report deleted!")
                                st.rerun()
                        
                        enable_disable = "Disable" if report.enabled else "Enable"
                        if st.button(f"⚡ {enable_disable}", key=f"toggle_{report.id}"):
                            if report_scheduler.update_scheduled_report(report.id, enabled=not report.enabled):
                                st.success(f"Report {enable_disable.lower()}d!")
                                st.rerun()
        else:
            st.info("No reports scheduled yet.")
    
    with tab4:
        st.header("User Management")
        
        # User summary
        user_summary = settings_manager.get_settings_summary()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", user_summary['total_users'])
        with col2:
            st.metric("Agency Owners", user_summary['agency_owners'])
        with col3:
            st.metric("Management Team", user_summary['management_team'])
        
        # Add new user
        st.subheader("Add New User")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                user_name = st.text_input("Name", placeholder="John Doe")
                user_email = st.text_input("Email", placeholder="john@example.com")
                user_phone = st.text_input("Phone (Optional)", placeholder="+1234567890")
            
            with col2:
                user_role = st.selectbox(
                    "Role",
                    options=["agency_owner", "management", "admin"],
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                user_agency = st.text_input("Agency (Optional)", placeholder="ABC Insurance")
                notifications = st.checkbox("Enable Notifications", value=True)
            
            submitted = st.form_submit_button("Add User")
            
            if submitted and user_name and user_email:
                success = settings_manager.add_user(
                    name=user_name,
                    email=user_email,
                    role=user_role,
                    phone=user_phone if user_phone else None,
                    agency=user_agency if user_agency else None
                )
                if success:
                    st.success("User added successfully!")
                    st.rerun()
                else:
                    st.error("Email already exists!")
        
        # Existing users
        st.subheader("Existing Users")
        
        if settings_manager.users:
            users_data = []
            for user in settings_manager.users:
                users_data.append({
                    'Name': user.name,
                    'Email': user.email,
                    'Role': user.role.replace('_', ' ').title(),
                    'Agency': user.agency or '-',
                    'Notifications': '✅' if user.notifications_enabled else '❌',
                    'Created': datetime.fromisoformat(user.created_at).strftime('%Y-%m-%d') if user.created_at else '-'
                })
            
            users_df = pd.DataFrame(users_data)
            st.dataframe(users_df, use_container_width=True)
            
            # User management actions
            st.subheader("User Actions")
            selected_email = st.selectbox(
                "Select User",
                options=[user.email for user in settings_manager.users],
                format_func=lambda email: f"{next(u.name for u in settings_manager.users if u.email == email)} ({email})"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Remove User"):
                    if settings_manager.remove_user(selected_email):
                        st.success("User removed successfully!")
                        st.rerun()
                    else:
                        st.error("Error removing user")
            
            with col2:
                user = settings_manager.get_user(selected_email)
                if user and st.button(f"{'🔕 Disable' if user.notifications_enabled else '🔔 Enable'} Notifications"):
                    if settings_manager.update_user(selected_email, notifications_enabled=not user.notifications_enabled):
                        st.success("Notifications updated!")
                        st.rerun()
        else:
            st.info("No users configured yet.")

def show_email_dialog(report_html, report_type):
    """Show email dialog for sending report"""
    if not settings_manager.validate_email_settings():
        st.error("Email settings not configured. Please configure email settings first.")
        return
    
    # Get available email addresses
    agency_owners = settings_manager.get_agency_owners()
    management_team = settings_manager.get_management_team()
    all_users = agency_owners + management_team
    email_options = [user.email for user in all_users]
    
    if not email_options:
        st.error("No users configured for email delivery.")
        return
    
    with st.form("email_report_form"):
        st.subheader("📧 Email Report")
        
        recipients = st.multiselect(
            "Recipients",
            options=email_options,
            default=email_options,
            help="Select recipients for this report"
        )
        
        custom_subject = st.text_input(
            "Subject (Optional)",
            placeholder=f"{report_type.replace('_', ' ').title()} Report - {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        send_email = st.form_submit_button("Send Email")
        
        if send_email and recipients:
            with st.spinner("Sending email..."):
                # Create a mock scheduled report for email sending
                from utils.scheduler import ScheduledReport
                mock_report = ScheduledReport(
                    id="temp",
                    name=custom_subject or f"{report_type.replace('_', ' ').title()} Report",
                    report_type=report_type,
                    frequency="manual",
                    recipients=recipients,
                    parameters={}
                )
                
                success = report_scheduler.email_service.send_report(mock_report, report_html)
                
                if success:
                    st.success(f"Report sent successfully to {len(recipients)} recipients!")
                else:
                    st.error("Failed to send email. Please check your email settings.")

if __name__ == "__main__":
    main() 