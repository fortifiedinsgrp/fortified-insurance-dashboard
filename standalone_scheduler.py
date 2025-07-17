#!/usr/bin/env python3
"""
Standalone Report Scheduler
Runs independently of the Streamlit app to ensure reports are sent even when the web interface is closed.

Usage:
    python standalone_scheduler.py           # Run once and check for due reports
    python standalone_scheduler.py --daemon  # Run continuously in background
    python standalone_scheduler.py --test    # Test email settings and exit
"""

import sys
import os
import time
import argparse
import signal
from datetime import datetime
from pathlib import Path

# Add the current directory to sys.path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class StandaloneScheduler:
    """Standalone scheduler that runs independent of Streamlit"""
    
    def __init__(self):
        self.running = False
        self.report_scheduler = None
        self.report_generator = None
        
    def initialize(self):
        """Initialize the scheduler and report generator"""
        try:
            from utils.scheduler import report_scheduler
            from utils.reports import ReportGenerator
            
            self.report_scheduler = report_scheduler
            self.report_generator = ReportGenerator()
            
            # Register all report generators
            self.register_generators()
            
            print("✅ Scheduler initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize scheduler: {e}")
            return False
    
    def register_generators(self):
        """Register all report generator functions"""
        generators = {
            'daily_performance': self.report_generator.generate_daily_report,
            'weekly_aggregated': self.report_generator.generate_weekly_report,
            'monthly_comprehensive': self.report_generator.generate_monthly_report,
            'agent_performance': self.report_generator.generate_agent_performance_report,
            'campaign_analysis': self.report_generator.generate_campaign_analysis_report,
            'executive_summary': self.report_generator.generate_executive_summary,
        }
        
        for report_type, generator_func in generators.items():
            self.report_scheduler.register_report_generator(report_type, generator_func)
        
        print(f"✅ Registered {len(generators)} report generators")
    
    def check_and_send_reports(self):
        """Check for due reports and send them"""
        try:
            due_reports = self.report_scheduler.get_due_reports()
            
            if not due_reports:
                print(f"ℹ️  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No reports due")
                return True
            
            print(f"📧 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Found {len(due_reports)} due reports")
            
            success_count = 0
            for report in due_reports:
                print(f"   🔄 Processing: {report.name}")
                
                if self.report_scheduler.run_report(report):
                    print(f"   ✅ Sent: {report.name}")
                    success_count += 1
                else:
                    print(f"   ❌ Failed: {report.name}")
            
            print(f"📊 Successfully sent {success_count}/{len(due_reports)} reports")
            return success_count == len(due_reports)
            
        except Exception as e:
            print(f"❌ Error checking/sending reports: {e}")
            return False
    
    def test_email_settings(self):
        """Test email configuration"""
        print("🧪 Testing email settings...")
        
        try:
            if self.report_scheduler.test_email_settings():
                print("✅ Email test successful!")
                return True
            else:
                print("❌ Email test failed!")
                return False
        except Exception as e:
            print(f"❌ Email test error: {e}")
            return False
    
    def run_once(self):
        """Run once and check for due reports"""
        if not self.initialize():
            return False
        
        print(f"🚀 Checking for due reports at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get summary
        summary = self.report_scheduler.get_schedule_summary()
        print(f"📋 Status: {summary['enabled_reports']} enabled reports, {summary['due_reports']} due")
        
        if not summary['email_configured']:
            print("⚠️  Warning: Email not configured. Reports will be generated but not sent.")
        
        return self.check_and_send_reports()
    
    def run_daemon(self, check_interval=300):  # Check every 5 minutes
        """Run continuously as a daemon"""
        if not self.initialize():
            return False
        
        self.running = True
        
        print(f"🔄 Starting daemon mode (checking every {check_interval} seconds)")
        print("   Press Ctrl+C to stop")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(signum, frame):
            print("\n🛑 Received shutdown signal, stopping scheduler...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while self.running:
                self.check_and_send_reports()
                
                # Sleep in small intervals so we can respond to signals
                for _ in range(check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        
        print("✅ Scheduler stopped")
        return True
    
    def get_status(self):
        """Get current scheduler status"""
        if not self.initialize():
            return
        
        summary = self.report_scheduler.get_schedule_summary()
        
        print("📊 Scheduler Status:")
        print(f"   Total Reports: {summary['total_reports']}")
        print(f"   Enabled Reports: {summary['enabled_reports']}")
        print(f"   Due Reports: {summary['due_reports']}")
        print(f"   Email Configured: {'✅' if summary['email_configured'] else '❌'}")
        
        # Show scheduled reports
        if len(self.report_scheduler.scheduled_reports) > 0:
            print("\n📋 Scheduled Reports:")
            for report in self.report_scheduler.scheduled_reports:
                status = "✅" if report.enabled else "⏸️"
                next_run = report.next_run if report.next_run else "Not scheduled"
                print(f"   {status} {report.name} ({report.frequency}) - Next: {next_run}")
        else:
            print("\n📋 No reports scheduled")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Standalone Report Scheduler")
    parser.add_argument('--daemon', '-d', action='store_true', 
                       help='Run continuously in background')
    parser.add_argument('--test', '-t', action='store_true',
                       help='Test email settings and exit')
    parser.add_argument('--status', '-s', action='store_true',
                       help='Show scheduler status and exit')
    parser.add_argument('--interval', '-i', type=int, default=300,
                       help='Check interval in seconds for daemon mode (default: 300)')
    
    args = parser.parse_args()
    
    scheduler = StandaloneScheduler()
    
    if args.test:
        if scheduler.initialize():
            success = scheduler.test_email_settings()
            sys.exit(0 if success else 1)
        else:
            sys.exit(1)
    
    elif args.status:
        scheduler.get_status()
        sys.exit(0)
    
    elif args.daemon:
        print("🚀 Starting Fortified Insurance Report Scheduler (Daemon Mode)")
        success = scheduler.run_daemon(args.interval)
        sys.exit(0 if success else 1)
    
    else:
        print("🚀 Running Fortified Insurance Report Scheduler (Single Check)")
        success = scheduler.run_once()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 