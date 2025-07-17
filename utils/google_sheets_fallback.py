"""
Fallback data provider for when Google Sheets is unavailable
"""

import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
from typing import Optional
import json
import os

# Sample data for when Google Sheets is unavailable
SAMPLE_AGENCY_DATA = {
    'Date': [date.today().strftime('%Y-%m-%d')] * 3,
    'Agency': ['Agency A', 'Agency B', 'Agency C'],
    'FE': [15000, 12000, 18000],
    'Adroit': [8000, 6000, 9000],
    'Total Rev': [23000, 18000, 27000],
    'QW': [2500, 2000, 3000],
    'QS': [1800, 1500, 2200],
    'SF': [2200, 1800, 2500],
    'Total Leads': [6500, 5300, 7700]
}

SAMPLE_AGENT_DATA = {
    'Agent Name': ['John Smith', 'Sarah Johnson', 'Mike Wilson', 'Lisa Brown', 'Tom Davis'],
    'Sales': [15, 12, 18, 8, 22],
    'Revenue': [45000, 36000, 54000, 24000, 66000],
    'Count Paid Calls': [125, 110, 140, 95, 155],
    'Agent Profitability': [2500, 1800, 2700, 900, 3100],
    'Closing Ratio': [12.0, 10.9, 12.9, 8.4, 14.2],
    'Total Calls': [180, 165, 195, 145, 220],
    'Lead Spend': [2500, 2200, 2800, 1900, 3100]
}

SAMPLE_VENDOR_DATA = {
    'Campaign': ['QuoteWizard', 'QuoteLab', 'SmartFinancial', 'LeadGenius', 'InsureMe'],
    'Paid Calls': [450, 380, 520, 290, 410],
    '# Unique Sales': [54, 42, 67, 29, 51],
    'Revenue': [162000, 126000, 201000, 87000, 153000],
    'Lead Cost': [9000, 7600, 10400, 5800, 8200],
    'ROAS': [18.0, 16.6, 19.3, 15.0, 18.7],
    'Profit': [153000, 118400, 190600, 81200, 144800],
    '% Closing Ratio': [12.0, 11.1, 12.9, 10.0, 12.4]
}

class DataCache:
    """Simple file-based cache for Google Sheets data"""
    
    def __init__(self, cache_dir: str = "data_cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def get_cache_file(self, sheet_name: str) -> str:
        """Get cache file path for a sheet"""
        safe_name = sheet_name.replace(' ', '_').replace('/', '_')
        return os.path.join(self.cache_dir, f"{safe_name}.json")
    
    def save_data(self, sheet_name: str, df: pd.DataFrame) -> bool:
        """Save DataFrame to cache"""
        try:
            cache_file = self.get_cache_file(sheet_name)
            data = {
                'timestamp': datetime.now().isoformat(),
                'data': df.to_dict('records'),
                'columns': df.columns.tolist()
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f, default=str)
            return True
        except Exception as e:
            st.warning(f"Failed to cache data for {sheet_name}: {e}")
            return False
    
    def load_data(self, sheet_name: str, max_age_hours: int = 24) -> Optional[pd.DataFrame]:
        """Load DataFrame from cache if it exists and is recent"""
        try:
            cache_file = self.get_cache_file(sheet_name)
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Check cache age
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                return None
            
            # Reconstruct DataFrame
            df = pd.DataFrame(cached_data['data'])
            if not df.empty and 'columns' in cached_data:
                df = df.reindex(columns=cached_data['columns'])
            
            return df
            
        except Exception as e:
            st.warning(f"Failed to load cached data for {sheet_name}: {e}")
            return None

# Global cache instance
data_cache = DataCache()

def get_fallback_data(sheet_name: str) -> pd.DataFrame:
    """Get fallback data when Google Sheets is unavailable"""
    
    # First, try to load from cache
    cached_df = data_cache.load_data(sheet_name)
    if cached_df is not None and not cached_df.empty:
        st.info(f"📋 Using cached data for '{sheet_name}' (Google Sheets unavailable)")
        return cached_df
    
    # If no cache, provide sample data
    st.warning(f"⚠️ Google Sheets unavailable. Using sample data for '{sheet_name}'")
    
    if 'Agency' in sheet_name or 'Daily Agency' in sheet_name:
        return pd.DataFrame(SAMPLE_AGENCY_DATA)
    elif 'Agent' in sheet_name or 'Daily Agent' in sheet_name:
        return pd.DataFrame(SAMPLE_AGENT_DATA)
    elif 'Vendor' in sheet_name or 'Lead' in sheet_name or 'Daily Lead' in sheet_name:
        return pd.DataFrame(SAMPLE_VENDOR_DATA)
    else:
        # Generic empty DataFrame
        return pd.DataFrame()

def get_sheet_data_with_fallback(sheet_name: str) -> pd.DataFrame:
    """Get sheet data with automatic fallback to cached or sample data"""
    try:
        # Try to import and use the main Google Sheets module
        from .google_sheets import GoogleSheetsConnection
        
        # Try to read from Google Sheets
        gs = GoogleSheetsConnection()
        df = gs.read_sheet(sheet_name)
        
        # If successful, cache the data
        if not df.empty:
            data_cache.save_data(sheet_name, df)
            return df
        else:
            # Empty result, use fallback
            return get_fallback_data(sheet_name)
            
    except Exception as e:
        # Google Sheets failed, use fallback
        error_msg = str(e)
        if "503" in error_msg or "unavailable" in error_msg.lower():
            st.error("🔄 Google Sheets is temporarily unavailable. Using cached or sample data.")
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            st.error("⏰ API rate limit reached. Using cached or sample data.")
        else:
            st.error(f"📊 Google Sheets error: {error_msg}. Using fallback data.")
        
        return get_fallback_data(sheet_name)

def clear_cache():
    """Clear all cached data"""
    try:
        import shutil
        if os.path.exists(data_cache.cache_dir):
            shutil.rmtree(data_cache.cache_dir)
            os.makedirs(data_cache.cache_dir)
        st.success("🗑️ Data cache cleared successfully")
    except Exception as e:
        st.error(f"Failed to clear cache: {e}")

def get_cache_info() -> dict:
    """Get information about cached data"""
    cache_info = {}
    try:
        if os.path.exists(data_cache.cache_dir):
            for filename in os.listdir(data_cache.cache_dir):
                if filename.endswith('.json'):
                    sheet_name = filename.replace('.json', '').replace('_', ' ')
                    file_path = os.path.join(data_cache.cache_dir, filename)
                    stat = os.stat(file_path)
                    cache_info[sheet_name] = {
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
    except Exception as e:
        st.warning(f"Error getting cache info: {e}")
    
    return cache_info 