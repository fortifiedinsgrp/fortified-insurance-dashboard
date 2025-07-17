"""
Google Sheets connection and data retrieval utilities
"""

import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import time
import numpy as np
import random


def excel_date_to_datetime(excel_date):
    """Convert Excel serial date to Python datetime"""
    if isinstance(excel_date, (int, float)):
        # Excel date serial number (days since 1900-01-01)
        # Note: Excel incorrectly treats 1900 as a leap year
        return datetime(1899, 12, 30) + timedelta(days=excel_date)
    return excel_date


def clean_numeric_value(value):
    """Clean numeric values by removing commas and converting to float"""
    if isinstance(value, str):
        # Remove commas and convert to float
        cleaned = value.replace(',', '')
        try:
            return float(cleaned)
        except ValueError:
            return value
    return value


class GoogleSheetsConnection:
    """Handle all Google Sheets operations"""
    
    def __init__(self, spreadsheet_id: Optional[str] = None):
        """Initialize Google Sheets connection
        
        Args:
            spreadsheet_id: Google Sheets ID. If None, uses st.secrets
        """
        self.spreadsheet_id = spreadsheet_id or st.secrets["SPREADSHEET_ID"]
        
        # Create credentials with required scopes
        self.creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
        )
        
        # Build the service
        self.service = build('sheets', 'v4', credentials=self.creds)
        
        # Cache for sheet metadata
        self._sheet_info = None
    
    def _execute_with_retry(self, request, max_retries=3, base_delay=1):
        """Execute a Google Sheets API request with retry logic for transient errors
        
        Args:
            request: The API request to execute
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds between retries
            
        Returns:
            The API response
            
        Raises:
            HttpError: If all retries are exhausted
        """
        for attempt in range(max_retries + 1):
            try:
                return request.execute()
            except HttpError as e:
                error_code = e.resp.status
                
                # Check if this is a retryable error
                if error_code in [500, 502, 503, 504, 429]:  # Server errors and rate limiting
                    if attempt < max_retries:
                        # Calculate exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        st.warning(f"Google Sheets temporarily unavailable (attempt {attempt + 1}/{max_retries + 1}). Retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        # All retries exhausted
                        st.error(f"Google Sheets service is currently unavailable after {max_retries + 1} attempts. Please try again later.")
                        raise e
                else:
                    # Non-retryable error (permissions, not found, etc.)
                    raise e
            except Exception as e:
                # Non-HTTP errors (network issues, etc.)
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    st.warning(f"Connection issue (attempt {attempt + 1}/{max_retries + 1}). Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    raise e
    
    def get_sheet_info(self) -> Dict[str, Any]:
        """Get spreadsheet metadata"""
        if not self._sheet_info:
            self._sheet_info = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
        return self._sheet_info
    
    def list_sheets(self) -> List[str]:
        """List all sheet names in the spreadsheet"""
        info = self.get_sheet_info()
        sheets = info.get('sheets', [])
        return [sheet['properties']['title'] for sheet in sheets]
    
    def read_sheet(self, sheet_name: str, range_name: str = "A:Z") -> pd.DataFrame:
        """Read data from a specific sheet and range
        
        Args:
            sheet_name: Name of the sheet
            range_name: A1 notation range (default: all columns)
            
        Returns:
            DataFrame with the sheet data
        """
        try:
            # For Daily Agency Stats, we need to handle the merged cells differently
            if sheet_name == "Daily Agency Stats":
                # Read with formatted values to handle merged cells better
                request = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{sheet_name}!A2:Z1000",  # Start from row 2, skip merged header row
                    valueRenderOption='FORMATTED_VALUE'
                )
                result = self._execute_with_retry(request)
                
                values = result.get('values', [])
                
                if not values or len(values) < 2:
                    return pd.DataFrame()
                
                # First row (A2:Z2) contains headers
                headers = values[0]
                # Data starts from second row
                data = values[1:]
                
                # Create DataFrame
                df = pd.DataFrame(data, columns=headers)
                
                # Clean column names
                df.columns = df.columns.str.strip()
                
                # Convert Date column from string to datetime
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                
                # Clean numeric columns (remove commas and dollar signs)
                numeric_columns = ['FE', 'Adroit', 'Total Rev', 'QW', 'QS', 'SF', 'Total Leads']
                for col in numeric_columns:
                    if col in df.columns:
                        # Replace commas
                        df[col] = df[col].astype(str).str.replace(',', '')
                        # Replace dollar signs
                        df[col] = df[col].str.replace('$', '')
                        # Convert to numeric
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
            
            else:
                # For other sheets, use the normal method
                full_range = f"{sheet_name}!{range_name}"
                
                # Get the data with unformatted values
                request = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=full_range,
                    valueRenderOption='UNFORMATTED_VALUE'
                )
                result = self._execute_with_retry(request)
                
                values = result.get('values', [])
                
                if not values or len(values) < 2:
                    return pd.DataFrame()
                
                # Normal sheets with headers in row 1
                df = pd.DataFrame(values[1:], columns=values[0])
                
                # Clean column names
                df.columns = df.columns.str.strip()
                
                # Convert Excel date columns
                date_columns = ['Date', 'date', 'DATE', 'Week of']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = df[col].apply(excel_date_to_datetime)
                
                return df
                
        except HttpError as e:
            error_code = e.resp.status if hasattr(e, 'resp') and hasattr(e.resp, 'status') else 'Unknown'
            
            if error_code == 503:
                st.error(f"Google Sheets service is temporarily unavailable. This usually resolves within a few minutes. Please try refreshing the page.")
            elif error_code == 429:
                st.error(f"API rate limit exceeded. Please wait a moment and try again.")
            elif error_code == 403:
                st.error(f"Access denied to sheet '{sheet_name}'. Please check your permissions.")
            elif error_code == 404:
                st.error(f"Sheet '{sheet_name}' not found. Please check the sheet name.")
            else:
                st.error(f"Error reading sheet '{sheet_name}': {str(e)}")
            
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Unexpected error reading sheet '{sheet_name}': {str(e)}")
            return pd.DataFrame()
    
    def read_sheet_with_date_filter(self, sheet_name: str, 
                                   start_date: date, 
                                   end_date: date,
                                   date_column: str = "date") -> pd.DataFrame:
        """Read sheet data filtered by date range
        
        Args:
            sheet_name: Name of the sheet
            start_date: Start date for filtering
            end_date: End date for filtering
            date_column: Name of the date column
            
        Returns:
            Filtered DataFrame
        """
        # Read all data
        df = self.read_sheet(sheet_name)
        
        if df.empty:
            return df
        
        # Find date column (case-insensitive)
        date_col = None
        for col in df.columns:
            if col.lower() == date_column.lower():
                date_col = col
                break
        
        if not date_col:
            # If exact match not found, look for columns containing 'date'
            for col in df.columns:
                if 'date' in col.lower():
                    date_col = col
                    break
        
        if not date_col:
            return df
        
        # The dates should already be converted from excel_date_to_datetime
        # But ensure they're datetime objects
        try:
            # If dates are already datetime objects, this will work
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Filter by date range
            mask = (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
            
            return df[mask].copy()
        except Exception as e:
            st.warning(f"Date filtering failed: {str(e)}. Returning all data.")
            return df
    
    def append_row(self, sheet_name: str, values: List[Any]) -> bool:
        """Append a row to a sheet
        
        Args:
            sheet_name: Name of the sheet
            values: List of values to append
            
        Returns:
            True if successful
        """
        try:
            body = {'values': [values]}
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:A",
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            return True
            
        except HttpError as e:
            st.error(f"Error appending to sheet '{sheet_name}': {str(e)}")
            return False
    
    def update_cell(self, sheet_name: str, cell: str, value: Any) -> bool:
        """Update a single cell
        
        Args:
            sheet_name: Name of the sheet
            cell: Cell reference (e.g., 'A1')
            value: Value to set
            
        Returns:
            True if successful
        """
        try:
            body = {'values': [[value]]}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!{cell}",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return True
            
        except HttpError as e:
            st.error(f"Error updating cell '{cell}' in sheet '{sheet_name}': {str(e)}")
            return False
    
    def batch_update(self, updates: List[Dict[str, Any]]) -> bool:
        """Perform batch updates to minimize API calls
        
        Args:
            updates: List of update dictionaries with 'range' and 'values' keys
            
        Returns:
            True if successful
        """
        try:
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': updates
            }
            
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            return True
            
        except HttpError as e:
            st.error(f"Error in batch update: {str(e)}")
            return False


# Cached data loading functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_agency_stats(start_date: date, end_date: date) -> pd.DataFrame:
    """Load agency statistics with caching"""
    gs = GoogleSheetsConnection()
    return gs.read_sheet_with_date_filter("Daily Agency Stats", start_date, end_date)


@st.cache_data(ttl=300)
def load_agent_totals(start_date: date, end_date: date) -> pd.DataFrame:
    """Load agent totals with caching"""
    gs = GoogleSheetsConnection()
    return gs.read_sheet_with_date_filter("Daily Agent Totals", start_date, end_date)


@st.cache_data(ttl=300)
def load_vendor_totals(start_date: date, end_date: date) -> pd.DataFrame:
    """Load vendor totals with caching"""
    gs = GoogleSheetsConnection()
    return gs.read_sheet_with_date_filter("Daily Lead Vendor Totals", start_date, end_date)


def get_agency_list() -> List[str]:
    """Get unique list of agencies"""
    # Try to get from today's data first
    today = date.today()
    df = load_agency_stats(today, today)
    
    # Check for both possible column names
    agency_col = None
    if 'Agency' in df.columns:
        agency_col = 'Agency'
    elif 'agency' in df.columns:
        agency_col = 'agency'
    
    if df.empty or agency_col is None:
        # If no data today, look back 30 days
        from datetime import timedelta
        start_date = today - timedelta(days=30)
        df = load_agency_stats(start_date, today)
        
        # Check again for column names
        if 'Agency' in df.columns:
            agency_col = 'Agency'
        elif 'agency' in df.columns:
            agency_col = 'agency'
    
    if not df.empty and agency_col:
        return sorted(df[agency_col].unique().tolist())
    
    return []


def get_sheet_data(sheet_name: str) -> pd.DataFrame:
    """Simple wrapper function for getting sheet data
    
    Args:
        sheet_name: Name of the sheet to read
        
    Returns:
        DataFrame with sheet data
    """
    try:
        gs = GoogleSheetsConnection()
        return gs.read_sheet(sheet_name)
    except Exception as e:
        st.error(f"Error reading sheet '{sheet_name}': {e}")
        return pd.DataFrame()