"""
GitHub API integration for automatically syncing scheduled reports configuration
"""

import json
import base64
import requests
from typing import Dict, Any, Optional
import streamlit as st
from datetime import datetime

class GitHubSync:
    """Handle automatic synchronization of scheduled reports to GitHub repository"""
    
    def __init__(self):
        self.api_base = "https://api.github.com"
        self.repo_owner = "fortifiedinsgrp"  # Your GitHub username/org
        self.repo_name = "fortified-insurance-dashboard"
        self.config_path = "config/scheduled_reports.json"
        
    def _get_github_token(self) -> Optional[str]:
        """Get GitHub token from Streamlit secrets"""
        try:
            # Try to get from Streamlit secrets
            if hasattr(st, 'secrets') and 'github_token' in st.secrets:
                return st.secrets['github_token']
            
            # Fallback: try environment variable
            import os
            return os.getenv('GITHUB_TOKEN')
        except:
            return None
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to GitHub API"""
        token = self._get_github_token()
        if not token:
            raise Exception("GitHub token not configured. Please add 'github_token' to Streamlit secrets.")
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.api_base}{endpoint}"
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code not in [200, 201]:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def get_file_content(self) -> tuple[Dict[str, Any], Optional[str]]:
        """Get current content of scheduled_reports.json and its SHA"""
        try:
            endpoint = f"/repos/{self.repo_owner}/{self.repo_name}/contents/{self.config_path}"
            response = self._make_request('GET', endpoint)
            
            # Decode base64 content
            content = base64.b64decode(response['content']).decode('utf-8')
            config = json.loads(content)
            
            return config, response['sha']
        except Exception as e:
            # If file doesn't exist, return empty config
            if "404" in str(e):
                return {"scheduled_reports": [], "last_updated": datetime.now().isoformat()}, None
            raise e
    
    def update_scheduled_reports(self, scheduled_reports: list, commit_message: str = None) -> bool:
        """Update scheduled reports configuration in GitHub repository"""
        try:
            # Get current file SHA
            _, current_sha = self.get_file_content()
            
            # Prepare new content
            new_config = {
                "scheduled_reports": [
                    {
                        "id": report.id,
                        "name": report.name,
                        "report_type": report.report_type,
                        "frequency": report.frequency,
                        "time": report.time,
                        "recipients": report.recipients,
                        "enabled": report.enabled,
                        "agency_filter": report.agency_filter,
                        "user_role": report.user_role,
                        "created_by": getattr(report, 'created_by', None),
                        "include_campaigns": getattr(report, 'include_campaigns', True),
                        "next_run": report.next_run
                    }
                    for report in scheduled_reports
                ],
                "last_updated": datetime.now().isoformat()
            }
            
            # Convert to JSON and encode
            content_json = json.dumps(new_config, indent=2)
            content_base64 = base64.b64encode(content_json.encode('utf-8')).decode('utf-8')
            
            # Prepare commit data
            if not commit_message:
                commit_message = f"Update scheduled reports configuration - {len(scheduled_reports)} reports"
            
            data = {
                "message": commit_message,
                "content": content_base64,
                "branch": "main"
            }
            
            # Include SHA if file exists (for updates)
            if current_sha is not None:
                data["sha"] = current_sha
            
            # Make the commit
            endpoint = f"/repos/{self.repo_owner}/{self.repo_name}/contents/{self.config_path}"
            self._make_request('PUT', endpoint, data)
            
            return True
            
        except Exception as e:
            st.error(f"Failed to sync with GitHub: {str(e)}")
            return False
    
    def is_configured(self) -> bool:
        """Check if GitHub sync is properly configured"""
        return self._get_github_token() is not None
    
    def test_connection(self) -> tuple[bool, str]:
        """Test GitHub API connection"""
        try:
            token = self._get_github_token()
            if not token:
                return False, "GitHub token not configured"
            
            # Test basic API access
            endpoint = f"/repos/{self.repo_owner}/{self.repo_name}"
            response = self._make_request('GET', endpoint)
            
            return True, f"Connected to repository: {response['full_name']}"
            
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

# Global instance
github_sync = GitHubSync() 