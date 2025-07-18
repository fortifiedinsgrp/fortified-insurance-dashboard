"""
Settings module for managing user information and application configuration
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class UserInfo:
    """User information data class"""
    name: str
    email: str
    role: str  # 'agency_owner', 'management', 'admin'
    phone: Optional[str] = None
    agency: Optional[str] = None
    notifications_enabled: bool = True
    created_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class EmailSettings:
    """Email configuration settings"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    use_tls: bool = True
    sender_email: str = ""
    sender_password: str = ""  # Should be app password for Gmail
    sender_name: str = "Insurance Dashboard"

@dataclass
class ReportSettings:
    """Report generation settings"""
    profitability_threshold: float = 200.0
    currency_symbol: str = "$"
    date_format: str = "%Y-%m-%d"
    include_charts: bool = True
    logo_path: Optional[str] = None

@dataclass
class AppSettings:
    """Main application settings"""
    app_name: str = "Fortified Insurance Dashboard"
    version: str = "1.0.0"
    timezone: str = "UTC"
    data_refresh_interval: int = 3600  # seconds
    max_file_size: int = 10485760  # 10MB in bytes
    allowed_file_types: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.allowed_file_types is None:
            self.allowed_file_types = ['.xlsx', '.xls', '.csv']

class SettingsManager:
    """Manages application settings and user information"""
    
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.users: List[UserInfo] = []
        self.email_settings = EmailSettings()
        self.report_settings = ReportSettings()
        self.app_settings = AppSettings()
        self.load_settings()
    
    def load_settings(self):
        """Load settings from JSON file, environment variables, and Streamlit secrets"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                
                # Load users
                if 'users' in data:
                    self.users = [UserInfo(**user) for user in data['users']]
                
                # Load email settings
                if 'email_settings' in data:
                    self.email_settings = EmailSettings(**data['email_settings'])
                
                # Load report settings
                if 'report_settings' in data:
                    self.report_settings = ReportSettings(**data['report_settings'])
                
                # Load app settings
                if 'app_settings' in data:
                    self.app_settings = AppSettings(**data['app_settings'])
                    
            except Exception as e:
                print(f"Error loading settings file: {e}")
        
        # Override email settings with environment variables (for GitHub Actions)
        self._load_email_from_env()
        
        # Override email settings with Streamlit secrets (for Streamlit Cloud)
        self._load_email_from_streamlit_secrets()
    
    def _load_email_from_env(self):
        """Load email settings from environment variables"""
        import os
        
        if os.getenv('SMTP_SERVER'):
            self.email_settings.smtp_server = os.getenv('SMTP_SERVER', self.email_settings.smtp_server)
        
        if os.getenv('SMTP_PORT'):
            self.email_settings.smtp_port = int(os.getenv('SMTP_PORT', self.email_settings.smtp_port))
        
        if os.getenv('SMTP_USERNAME'):
            self.email_settings.sender_email = os.getenv('SMTP_USERNAME', self.email_settings.sender_email)
        
        if os.getenv('SMTP_PASSWORD'):
            self.email_settings.sender_password = os.getenv('SMTP_PASSWORD', self.email_settings.sender_password)
        
        if os.getenv('SENDER_EMAIL'):
            self.email_settings.sender_email = os.getenv('SENDER_EMAIL', self.email_settings.sender_email)
    
    def _load_email_from_streamlit_secrets(self):
        """Load email settings from Streamlit secrets"""
        try:
            import streamlit as st
            
            # Check if we're in a Streamlit context
            if hasattr(st, 'secrets'):
                # Load from email section in secrets
                if 'email' in st.secrets:
                    email_secrets = st.secrets['email']
                    
                    if 'smtp_server' in email_secrets:
                        self.email_settings.smtp_server = email_secrets['smtp_server']
                    
                    if 'smtp_port' in email_secrets:
                        self.email_settings.smtp_port = int(email_secrets['smtp_port'])
                    
                    if 'smtp_username' in email_secrets:
                        self.email_settings.sender_email = email_secrets['smtp_username']
                    
                    if 'smtp_password' in email_secrets:
                        self.email_settings.sender_password = email_secrets['smtp_password']
                    
                    if 'sender_email' in email_secrets:
                        self.email_settings.sender_email = email_secrets['sender_email']
                
        except Exception:
            # Not in Streamlit context or secrets not available
            pass
    
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            data = {
                'users': [asdict(user) for user in self.users],
                'email_settings': asdict(self.email_settings),
                'report_settings': asdict(self.report_settings),
                'app_settings': asdict(self.app_settings),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def _create_default_settings(self):
        """Create default settings"""
        # Add default admin user
        admin_user = UserInfo(
            name="System Admin",
            email="admin@example.com",
            role="admin",
            agency="System"
        )
        self.users = [admin_user]
        self.save_settings()
    
    def add_user(self, name: str, email: str, role: str, phone: Optional[str] = None, agency: Optional[str] = None) -> bool:
        """Add a new user"""
        # Check if email already exists
        if any(user.email == email for user in self.users):
            return False
        
        new_user = UserInfo(
            name=name,
            email=email,
            role=role,
            phone=phone,
            agency=agency
        )
        
        self.users.append(new_user)
        return self.save_settings()
    
    def update_user(self, email: str, **kwargs) -> bool:
        """Update user information"""
        for user in self.users:
            if user.email == email:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                return self.save_settings()
        return False
    
    def remove_user(self, email: str) -> bool:
        """Remove a user"""
        self.users = [user for user in self.users if user.email != email]
        return self.save_settings()
    
    def get_user(self, email: str) -> Optional[UserInfo]:
        """Get user by email"""
        for user in self.users:
            if user.email == email:
                return user
        return None
    
    def get_users_by_role(self, role: str) -> List[UserInfo]:
        """Get all users with specific role"""
        return [user for user in self.users if user.role == role]
    
    def get_agency_owners(self) -> List[UserInfo]:
        """Get all agency owners"""
        return self.get_users_by_role('agency_owner')
    
    def get_management_team(self) -> List[UserInfo]:
        """Get all management team members"""
        return self.get_users_by_role('management')
    
    def get_notification_emails(self, role: Optional[str] = None) -> List[str]:
        """Get emails for users with notifications enabled"""
        users = self.users if role is None else self.get_users_by_role(role)
        return [user.email for user in users if user.notifications_enabled]
    
    def update_email_settings(self, **kwargs) -> bool:
        """Update email settings"""
        for key, value in kwargs.items():
            if hasattr(self.email_settings, key):
                setattr(self.email_settings, key, value)
        return self.save_settings()
    
    def update_report_settings(self, **kwargs) -> bool:
        """Update report settings"""
        for key, value in kwargs.items():
            if hasattr(self.report_settings, key):
                setattr(self.report_settings, key, value)
        return self.save_settings()
    
    def update_app_settings(self, **kwargs) -> bool:
        """Update application settings"""
        for key, value in kwargs.items():
            if hasattr(self.app_settings, key):
                setattr(self.app_settings, key, value)
        return self.save_settings()
    
    def validate_email_settings(self) -> bool:
        """Validate that email settings are properly configured"""
        return (
            bool(self.email_settings.smtp_server) and
            bool(self.email_settings.smtp_port) and
            bool(self.email_settings.sender_email) and
            bool(self.email_settings.sender_password) and
            '@' in self.email_settings.sender_email
        )
    
    def get_settings_summary(self) -> Dict:
        """Get a summary of all settings"""
        return {
            'total_users': len(self.users),
            'agency_owners': len(self.get_agency_owners()),
            'management_team': len(self.get_management_team()),
            'email_configured': self.validate_email_settings(),
            'app_name': self.app_settings.app_name,
            'version': self.app_settings.version
        }

# Global settings instance
settings_manager = SettingsManager() 