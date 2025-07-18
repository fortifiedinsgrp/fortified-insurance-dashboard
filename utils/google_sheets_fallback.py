"""
Fallback data provider for when Google Sheets is unavailable
"""

import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
from typing import Optional
import json
import os

# Sample data for when Google Sheets is unavailable - includes last 30 days + some historical data
def _generate_date_range_data():
    """Generate sample data for a broader date range to support historical queries"""
    # Generate data for last 30 days plus some historical dates for common test scenarios
    dates = []
    
    # Last 30 days from today
    for i in range(30):
        dates.append((date.today() - timedelta(days=i)).strftime('%Y-%m-%d'))
    
    # Add some common historical test dates
    historical_dates = [
        '2024-07-16', '2024-07-15', '2024-07-14', '2024-07-13', '2024-07-12',
        '2024-06-15', '2024-06-14', '2024-06-13', '2024-06-12', '2024-06-11',
        '2024-05-15', '2024-05-14', '2024-05-13', '2024-05-12', '2024-05-11'
    ]
    dates.extend(historical_dates)
    
    # Remove duplicates and sort
    dates = sorted(list(set(dates)))
    
    agencies = ['Bonavita Insurance', 'Quality Insurance', 'Quality Insurance Agency', 'Your Health Group', 'Fortified Insurance Solutions']
    
    data = []
    for d in dates:
        for agency in agencies:
            # Vary data slightly by date and agency
            base_multiplier = 0.8 + (hash(d + agency) % 40) / 100  # 0.8 to 1.2
            data.append({
                'Date': d,
                'Agency': agency,
                'FE': int(15000 * base_multiplier),
                'Adroit': int(8000 * base_multiplier),
                'Total Rev': int(23000 * base_multiplier),
                'QW': int(2500 * base_multiplier),
                'QS': int(1800 * base_multiplier),
                'SF': int(2200 * base_multiplier),
                'Total Leads': int(6500 * base_multiplier)
            })
    return data

# This will be set after the function is defined
SAMPLE_AGENCY_DATA = None

def _generate_agent_date_range_data():
    """Generate sample agent data for a broader date range"""
    # Use the same date generation logic as agency data
    dates = []
    
    # Last 30 days from today
    for i in range(30):
        dates.append((date.today() - timedelta(days=i)).strftime('%Y-%m-%d'))
    
    # Add some common historical test dates
    historical_dates = [
        '2024-07-16', '2024-07-15', '2024-07-14', '2024-07-13', '2024-07-12',
        '2024-06-15', '2024-06-14', '2024-06-13', '2024-06-12', '2024-06-11',
        '2024-05-15', '2024-05-14', '2024-05-13', '2024-05-12', '2024-05-11'
    ]
    dates.extend(historical_dates)
    
    # Remove duplicates and sort
    dates = sorted(list(set(dates)))
    
    agents = ['John Smith', 'Sarah Johnson', 'Mike Wilson', 'Lisa Brown', 'Tom Davis']
    agencies = ['Bonavita Insurance', 'Quality Insurance', 'Quality Insurance Agency', 'Your Health Group', 'Bonavita Insurance']  # Distribute agents across agencies
    
    data = []
    for d in dates:
        for i, agent in enumerate(agents):
            # Vary data slightly by date and agent
            base_multiplier = 0.7 + (hash(d + agent) % 60) / 100  # 0.7 to 1.3
            data.append({
                'Date': d,
                'Agent Name': agent,
                'Agency': agencies[i],
                'Sales': max(1, int(15 * base_multiplier)),
                'Revenue': int(45000 * base_multiplier),
                'Count Paid Calls': int(125 * base_multiplier),
                'Agent Profitability': int(2500 * base_multiplier),
                'Closing Ratio': round(12.0 * base_multiplier, 2),
                'Total Calls': int(200 * base_multiplier),
                'Lead Spend': int(1800 * base_multiplier),
                'Profit': int(2500 * base_multiplier)
            })
    return data

# This will be set after the function is defined  
SAMPLE_AGENT_DATA = None

def _generate_vendor_date_range_data():
    """Generate sample vendor/campaign data for a broader date range"""
    # Use the same date generation logic as agency data
    dates = []
    
    # Last 30 days from today
    for i in range(30):
        dates.append((date.today() - timedelta(days=i)).strftime('%Y-%m-%d'))
    
    # Add some common historical test dates
    historical_dates = [
        '2024-07-16', '2024-07-15', '2024-07-14', '2024-07-13', '2024-07-12',
        '2024-06-15', '2024-06-14', '2024-06-13', '2024-06-12', '2024-06-11',
        '2024-05-15', '2024-05-14', '2024-05-13', '2024-05-12', '2024-05-11'
    ]
    dates.extend(historical_dates)
    
    # Remove duplicates and sort
    dates = sorted(list(set(dates)))
    
    campaigns = ['QuoteWizard', 'QuoteLab', 'SmartFinancial', 'LeadGenius', 'InsureMe']
    
    data = []
    for d in dates:
        for campaign in campaigns:
            # Vary data slightly by date and campaign
            base_multiplier = 0.8 + (hash(d + campaign) % 40) / 100  # 0.8 to 1.2
            data.append({
                'Date': d,
                'Campaign': campaign,
                'Paid Calls': int(450 * base_multiplier),
                '# Unique Sales': int(54 * base_multiplier),
                'Revenue': int(162000 * base_multiplier),
                'Lead Cost': int(9000 * base_multiplier),
                'ROAS': round(18.0 * base_multiplier, 2),
                'Profit': int(153000 * base_multiplier),
                '% Closing Ratio': round(12.0 * base_multiplier, 2)
            })
    return data

# This will be set after the function is defined
SAMPLE_VENDOR_DATA = None

# Initialize sample data after all functions are defined
def _initialize_sample_data():
    """Initialize sample data - called at module load"""
    global SAMPLE_AGENCY_DATA, SAMPLE_AGENT_DATA, SAMPLE_VENDOR_DATA
    SAMPLE_AGENCY_DATA = _generate_date_range_data()
    SAMPLE_AGENT_DATA = _generate_agent_date_range_data()
    SAMPLE_VENDOR_DATA = _generate_vendor_date_range_data()

# Initialize the data
_initialize_sample_data()

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
    
    # If no cache, generate fresh sample data
    st.warning(f"⚠️ Google Sheets unavailable. Using sample data for '{sheet_name}'")
    
    if 'Agency' in sheet_name or 'Daily Agency' in sheet_name:
        return pd.DataFrame(_generate_date_range_data())
    elif 'Agent' in sheet_name or 'Daily Agent' in sheet_name:
        return pd.DataFrame(_generate_agent_date_range_data())
    elif 'Vendor' in sheet_name or 'Lead' in sheet_name or 'Daily Lead' in sheet_name:
        return pd.DataFrame(_generate_vendor_date_range_data())
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