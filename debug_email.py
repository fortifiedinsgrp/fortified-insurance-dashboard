#!/usr/bin/env python3
"""
Debug email settings to identify the exact issue
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_email_settings():
    print("🔍 Debugging Email Settings...")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Variables:")
    env_vars = ['SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'SENDER_EMAIL']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask password
            if 'PASSWORD' in var:
                print(f"  ✅ {var}: {'*' * len(value)}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    print("\n🔧 Testing Settings Manager...")
    try:
        from utils.settings import settings_manager
        print("  ✅ Settings manager imported")
        
        email_settings = settings_manager.email_settings
        print(f"  📧 SMTP Server: {email_settings.smtp_server}")
        print(f"  📧 SMTP Port: {email_settings.smtp_port}")
        print(f"  📧 Username: {email_settings.sender_email}")
        print(f"  📧 Sender: {email_settings.sender_email}")
        print(f"  📧 Password: {'*' * len(email_settings.sender_password) if email_settings.sender_password else 'NOT SET'}")
        
        # Test validation
        is_valid = settings_manager.validate_email_settings()
        print(f"  ✅ Email settings valid: {is_valid}")
        
    except Exception as e:
        print(f"  ❌ Settings manager error: {e}")
        return False
    
    print("\n📧 Testing Email Service...")
    try:
        # Test SMTP connection
        import smtplib
        
        print("  🔌 Testing SMTP connection...")
        
        # Get settings
        smtp_server = email_settings.smtp_server
        smtp_port = int(email_settings.smtp_port)
        username = email_settings.sender_email
        password = email_settings.sender_password
        
        print(f"  📡 Connecting to {smtp_server}:{smtp_port}")
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        print("  ✅ TLS connection established")
        
        server.login(username, password)
        print("  ✅ SMTP login successful")
        
        # Send test email
        from email.mime.text import MimeText
        from email.mime.multipart import MimeMultipart
        
        msg = MimeMultipart()
        msg['From'] = email_settings.sender_email
        msg['To'] = email_settings.sender_email  # Send to self
        msg['Subject'] = "Test Email - Debug"
        
        body = "This is a test email from the debug script."
        msg.attach(MimeText(body, 'plain'))
        
        text = msg.as_string()
        server.sendmail(email_settings.sender_email, [email_settings.sender_email], text)
        server.quit()
        
        print("  ✅ Test email sent successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Email service error: {e}")
        print(f"  📋 Error type: {type(e).__name__}")
        
        # Check specific error types
        if "authentication failed" in str(e).lower():
            print("  💡 Solution: Check Gmail app password")
        elif "connection refused" in str(e).lower():
            print("  💡 Solution: Check SMTP server/port")
        elif "timeout" in str(e).lower():
            print("  💡 Solution: Network connectivity issue")
        
        return False

if __name__ == "__main__":
    success = test_email_settings()
    if success:
        print("\n🎉 Email settings are working correctly!")
    else:
        print("\n❌ Email settings have issues that need to be fixed.")
        sys.exit(1) 