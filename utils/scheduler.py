"""
Scheduling module for automated report generation and delivery
"""

import json
import os
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
# Import email modules with fallback
import email.message
import base64
import threading
import time

from .settings import settings_manager, UserInfo

@dataclass
class ScheduledReport:
    """Scheduled report configuration"""
    id: str
    name: str
    report_type: str  # 'daily', 'weekly', 'monthly', 'custom'
    frequency: str  # 'daily', 'weekly', 'monthly'
    recipients: List[str]  # Email addresses
    parameters: Dict  # Report-specific parameters
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    created_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.next_run is None:
            self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calculate next run time based on frequency"""
        now = datetime.now()
        
        if self.frequency == 'daily':
            # Run at 8 AM next day
            next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif self.frequency == 'weekly':
            # Run on Monday at 8 AM
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=8, minute=0, second=0, microsecond=0)
        elif self.frequency == 'monthly':
            # Run on 1st of next month at 8 AM
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1, hour=8, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month + 1, day=1, hour=8, minute=0, second=0, microsecond=0)
        else:
            # Default to daily
            next_run = now + timedelta(days=1)
            next_run = next_run.replace(hour=8, minute=0, second=0, microsecond=0)
        
        self.next_run = next_run.isoformat()

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
    
    def __init__(self, schedules_file: str = "schedules.json"):
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
        """Save scheduled reports to JSON file"""
        try:
            data = {
                'scheduled_reports': [asdict(report) for report in self.scheduled_reports],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.schedules_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving schedules: {e}")
            return False
    
    def register_report_generator(self, report_type: str, generator_func: Callable):
        """Register a report generator function"""
        self.report_generators[report_type] = generator_func
    
    def add_scheduled_report(self, name: str, report_type: str, frequency: str,
                           recipients: List[str], parameters: Optional[Dict] = None) -> str:
        """Add a new scheduled report"""
        import uuid
        
        report_id = str(uuid.uuid4())
        if parameters is None:
            parameters = {}
        
        report = ScheduledReport(
            id=report_id,
            name=name,
            report_type=report_type,
            frequency=frequency,
            recipients=recipients,
            parameters=parameters
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
                
                # Recalculate next run if frequency changed
                if 'frequency' in kwargs:
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
            report_data = generator_func(**report.parameters)
            
            # Send report
            success = self.email_service.send_report(report, report_data)
            
            if success:
                # Update last run and calculate next run
                report.last_run = datetime.now().isoformat()
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