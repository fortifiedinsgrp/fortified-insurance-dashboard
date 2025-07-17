"""
Startup initialization for the insurance dashboard
"""

from .scheduler import report_scheduler
from .reports import report_generator

def initialize_system():
    """Initialize the dashboard system"""
    
    # Register all report generators with the scheduler
    for report_type, generator_func in report_generator.report_types.items():
        report_scheduler.register_report_generator(report_type, generator_func)
    
    print("✅ Report generators registered with scheduler")
    
    # Start the scheduler if there are enabled reports
    if report_scheduler.scheduled_reports:
        enabled_count = len([r for r in report_scheduler.scheduled_reports if r.enabled])
        if enabled_count > 0:
            report_scheduler.start_scheduler()
            print(f"✅ Scheduler started with {enabled_count} enabled reports")
    
    print("🚀 System initialization complete")

# Auto-initialize when module is imported
initialize_system() 