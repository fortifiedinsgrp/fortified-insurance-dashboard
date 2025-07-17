"""
Test script to verify Google Sheets connection
Run this first to ensure everything is set up correctly
"""

import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd

def test_connection():
    """Test the Google Sheets connection and display results"""
    
    print("Testing Google Sheets Connection...")
    print("-" * 50)
    
    try:
        # Load credentials from secrets
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        
        # Build the service
        service = build('sheets', 'v4', credentials=credentials)
        
        # Get spreadsheet ID
        spreadsheet_id = st.secrets["SPREADSHEET_ID"]
        print(f"Spreadsheet ID: {spreadsheet_id}")
        
        # Test 1: Get spreadsheet metadata
        print("\n1. Testing spreadsheet access...")
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        print(f"✓ Spreadsheet Title: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
        
        # Test 2: List all sheets
        print("\n2. Available sheets:")
        sheets = spreadsheet.get('sheets', [])
        for sheet in sheets:
            sheet_name = sheet.get('properties', {}).get('title', 'Unknown')
            print(f"   - {sheet_name}")
        
        # Test 3: Read sample data from each expected sheet
        expected_sheets = [
            "Daily Agency Stats",
            "Daily Agent Totals", 
            "Daily Lead Vendor Totals"
        ]
        
        print("\n3. Testing data access from each sheet:")
        for sheet_name in expected_sheets:
            try:
                # Read first 5 rows
                range_name = f"{sheet_name}!A1:Z5"
                result = service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                if values:
                    print(f"\n   ✓ {sheet_name}: Found {len(values)} rows")
                    print(f"     Columns: {', '.join(values[0][:5])}...")  # Show first 5 columns
                else:
                    print(f"\n   ⚠ {sheet_name}: No data found")
                    
            except Exception as e:
                print(f"\n   ✗ {sheet_name}: Error - {str(e)}")
        
        print("\n" + "="*50)
        print("✓ Connection test PASSED! You're ready to build the dashboard.")
        print("="*50)
        
        # Return True for success
        return True
        
    except Exception as e:
        print("\n" + "="*50)
        print("✗ Connection test FAILED!")
        print(f"Error: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Check that your service account JSON is correctly pasted in .streamlit/secrets.toml")
        print("2. Verify you've shared the Google Sheet with the service account email")
        print("3. Ensure the Google Sheets API is enabled in your Google Cloud project")
        print("="*50)
        return False

if __name__ == "__main__":
    # Run the test
    success = test_connection()
    
    # If running in Streamlit, show results in the UI
    if hasattr(st, '_is_running_with_streamlit'):
        if success:
            st.success("✓ Google Sheets connection successful!")
        else:
            st.error("✗ Connection failed. Check the console for details.")