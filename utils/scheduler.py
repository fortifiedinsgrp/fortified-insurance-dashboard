"""
Scheduling module for automated report generation and delivery
"""

import json
import os
import smtplib
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict, field
# Import email modules with fallback
import email.message
import base64
import threading
import time

from .settings import settings_manager, UserInfo

@dataclass
class ScheduledReport:
    """Represents a scheduled report configuration"""
    id: str
    name: str
    report_type: str  # daily_performance, weekly_aggregated, monthly_comprehensive, etc.
    frequency: str    # daily, weekly, monthly
    time: str        # HH:MM format
    recipients: List[str]
    enabled: bool = True
    next_run: Optional[str] = None
    created_by: Optional[str] = None  # User who created the report
    user_role: Optional[str] = None   # agency_owner, management, admin
    agency_filter: Optional[str] = None  # Specific agency for agency_owner role
    include_campaigns: bool = True    # Whether to include campaign data (management only)
    
    def __post_init__(self):
        if self.next_run is None:
            self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calculate the next run time based on frequency"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # Parse the time
        try:
            hour, minute = map(int, self.time.split(':'))
        except:
            hour, minute = 8, 0  # Default to 8 AM
        
        if self.frequency == 'daily':
            # Schedule for tomorrow at specified time
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif self.frequency == 'weekly':
            # Schedule for next Monday at specified time
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:  # Today is Monday
                days_until_monday = 7   # Schedule for next Monday
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=days_until_monday)
        
        elif self.frequency == 'monthly':
            # Schedule for first day of next month
            if now.month == 12:
                next_run = now.replace(year=now.year+1, month=1, day=1, hour=hour, minute=minute, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month+1, day=1, hour=hour, minute=minute, second=0, microsecond=0)
        
        else:
            # Default to daily
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
        
        self.next_run = next_run.isoformat()
    
    def get_report_date_range(self):
        """Calculate the appropriate date range for this report based on frequency"""
        from datetime import date, timedelta
        
        today = date.today()
        
        if self.frequency == 'daily':
            # Yesterday's data
            target_date = today - timedelta(days=1)
            return target_date, target_date
        
        elif self.frequency == 'weekly':
            # Previous week (Sunday through Saturday)
            # Find last Sunday
            days_since_sunday = (today.weekday() + 1) % 7  # Monday=0, Sunday=6 -> Sunday=0
            last_sunday = today - timedelta(days=days_since_sunday + 7)  # Previous week's Sunday
            last_saturday = last_sunday + timedelta(days=6)
            return last_sunday, last_saturday
        
        elif self.frequency == 'monthly':
            # Previous month
            first_of_this_month = today.replace(day=1)
            last_day_prev_month = first_of_this_month - timedelta(days=1)
            first_of_prev_month = last_day_prev_month.replace(day=1)
            return first_of_prev_month, last_day_prev_month
        
        else:
            # Default to yesterday
            target_date = today - timedelta(days=1)
            return target_date, target_date
    
    def get_report_parameters(self):
        """Get the parameters to pass to the report generator"""
        start_date, end_date = self.get_report_date_range()
        
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'user_role': self.user_role,
            'include_campaigns': self.include_campaigns
        }
        
        # Add agency filter for agency owners
        if self.user_role == 'agency_owner' and self.agency_filter:
            params['agency'] = self.agency_filter
        
        return params

class EmailService:
    """Email service for sending reports"""
    
    def __init__(self):
        self.settings = settings_manager.email_settings
    
    def send_email(self, to_emails: List[str], subject: str, body: str, 
                   attachments: Optional[List[str]] = None) -> bool:
        """Send email with optional attachments"""
        try:
            if not settings_manager.validate_email_settings():
                print("Email settings not configured")
                return False
            
            # Create simple email message
            msg = email.message.EmailMessage()
            msg['From'] = f"{self.settings.sender_name} <{self.settings.sender_email}>"
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject
            msg.set_content(body, subtype='html')
            
            # Add attachments (simplified - no attachments for now to avoid complexity)
            if attachments:
                print("Note: Attachments not supported in simplified email mode")
            
            # Send email
            server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)
            if self.settings.use_tls:
                server.starttls()
            server.login(self.settings.sender_email, self.settings.sender_password)
            
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_report(self, report: ScheduledReport, report_data: str, 
                   attachments: Optional[List[str]] = None) -> bool:
        """Send a scheduled report via email"""
        subject = f"{report.name} - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Create HTML email body
        body = f"""
        <html>
        <head></head>
        <body>
            <h2>{report.name}</h2>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Report Type: {report.report_type.title()}</p>
            
            <div style="margin: 20px 0;">
                {report_data}
            </div>
            
            <hr>
            <p style="font-size: 12px; color: #666;">
                This is an automated report from {settings_manager.app_settings.app_name}
            </p>
        </body>
        </html>
        """
        
        return self.send_email(report.recipients, subject, body, attachments)

class ReportScheduler:
    """Report scheduler for managing automated reports"""
    
    def __init__(self, schedules_file: str = "config/scheduled_reports.json"):
        self.schedules_file = schedules_file
        self.scheduled_reports: List[ScheduledReport] = []
        self.email_service = EmailService()
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.report_generators: Dict[str, Callable] = {}
        self.load_schedules()
    
    def load_schedules(self):
        """Load scheduled reports from JSON file"""
        if os.path.exists(self.schedules_file):
            try:
                with open(self.schedules_file, 'r') as f:
                    data = json.load(f)
                
                if 'scheduled_reports' in data:
                    self.scheduled_reports = [
                        ScheduledReport(**report) for report in data['scheduled_reports']
                    ]
            except Exception as e:
                print(f"Error loading schedules: {e}")
    
    def save_schedules(self):
        """Save scheduled reports to JSON file and sync to GitHub"""
        try:
            # Save locally first
            data = {
                'scheduled_reports': [asdict(report) for report in self.scheduled_reports],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.schedules_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Sync to GitHub if running in Streamlit
            try:
                import streamlit as st
                from .github_sync import github_sync
                
                if github_sync.is_configured():
                    github_sync.update_scheduled_reports(
                        self.scheduled_reports,
                        "Auto-sync: Update scheduled reports from Streamlit interface"
                    )
                    print("✅ Synced scheduled reports to GitHub")
                else:
                    print("ℹ️  GitHub sync not configured (this is normal for local/GitHub Actions)")
            except ImportError:
                # Not running in Streamlit environment
                print("ℹ️  Not syncing to GitHub (not in Streamlit environment)")
            except Exception as e:
                print(f"⚠️  Failed to sync to GitHub: {e}")
            
            return True
        except Exception as e:
            print(f"Error saving schedules: {e}")
            return False
    
    def register_report_generator(self, report_type: str, generator_func: Callable):
        """Register a report generator function"""
        self.report_generators[report_type] = generator_func
    
    def add_scheduled_report(self, name: str, report_type: str, frequency: str,
                           recipients: List[str], time: str = "08:00", 
                           user_role: str = "management", agency_filter: Optional[str] = None,
                           include_campaigns: bool = True) -> str:
        """Add a new scheduled report"""
        import uuid
        
        report_id = str(uuid.uuid4())
        
        report = ScheduledReport(
            id=report_id,
            name=name,
            report_type=report_type,
            frequency=frequency,
            time=time,
            recipients=recipients,
            user_role=user_role,
            agency_filter=agency_filter,
            include_campaigns=include_campaigns
        )
        
        self.scheduled_reports.append(report)
        self.save_schedules()
        return report_id
    
    def update_scheduled_report(self, report_id: str, **kwargs) -> bool:
        """Update a scheduled report"""
        for report in self.scheduled_reports:
            if report.id == report_id:
                for key, value in kwargs.items():
                    if hasattr(report, key):
                        setattr(report, key, value)
                
                # Recalculate next run if frequency or time changed
                if 'frequency' in kwargs or 'time' in kwargs:
                    report._calculate_next_run()
                
                return self.save_schedules()
        return False
    
    def remove_scheduled_report(self, report_id: str) -> bool:
        """Remove a scheduled report"""
        self.scheduled_reports = [
            report for report in self.scheduled_reports if report.id != report_id
        ]
        return self.save_schedules()
    
    def get_scheduled_report(self, report_id: str) -> Optional[ScheduledReport]:
        """Get a scheduled report by ID"""
        for report in self.scheduled_reports:
            if report.id == report_id:
                return report
        return None
    
    def get_due_reports(self) -> List[ScheduledReport]:
        """Get reports that are due to run"""
        now = datetime.now()
        due_reports = []
        
        for report in self.scheduled_reports:
            if report.enabled and report.next_run:
                next_run = datetime.fromisoformat(report.next_run)
                if next_run <= now:
                    due_reports.append(report)
        
        return due_reports
    
    def run_report(self, report: ScheduledReport) -> bool:
        """Run a single report"""
        try:
            if report.report_type not in self.report_generators:
                print(f"No generator registered for report type: {report.report_type}")
                return False
            
            # Generate report
            generator_func = self.report_generators[report.report_type]
            report_data = generator_func(**report.get_report_parameters())
            
            # Send report
            success = self.email_service.send_report(report, report_data)
            
            if success:
                # Calculate next run for the next occurrence
                report._calculate_next_run()
                self.save_schedules()
                print(f"Report '{report.name}' sent successfully")
            else:
                print(f"Failed to send report '{report.name}'")
            
            return success
            
        except Exception as e:
            print(f"Error running report '{report.name}': {e}")
            return False
    
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("Report scheduler started")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        print("Report scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                due_reports = self.get_due_reports()
                for report in due_reports:
                    self.run_report(report)
                
                # Sleep for 60 seconds before checking again
                time.sleep(60)
                
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def test_email_settings(self) -> bool:
        """Test email settings by sending a test email"""
        if not settings_manager.validate_email_settings():
            return False
        
        test_email = settings_manager.email_settings.sender_email
        subject = "Test Email - Insurance Dashboard"
        body = """
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email to verify your email settings are working correctly.</p>
            <p>If you receive this email, your email configuration is set up properly.</p>
        </body>
        </html>
        """
        
        return self.email_service.send_email([test_email], subject, body)
    
    def get_schedule_summary(self) -> Dict:
        """Get a summary of all scheduled reports"""
        enabled_reports = [r for r in self.scheduled_reports if r.enabled]
        due_reports = self.get_due_reports()
        
        return {
            'total_reports': len(self.scheduled_reports),
            'enabled_reports': len(enabled_reports),
            'due_reports': len(due_reports),
            'running': self.running,
            'email_configured': settings_manager.validate_email_settings()
        }

# Global scheduler instance
report_scheduler = ReportScheduler() 