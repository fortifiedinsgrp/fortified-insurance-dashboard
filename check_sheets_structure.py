"""
Script to check the actual structure of your Google Sheets
"""

import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load credentials
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
)

service = build('sheets', 'v4', credentials=credentials)
spreadsheet_id = st.secrets["SPREADSHEET_ID"]

# Check each sheet
sheets_to_check = [
    "Daily Agency Stats",
    "Daily Agent Totals", 
    "Daily Lead Vendor Totals"
]

for sheet_name in sheets_to_check:
    print(f"\n{'='*60}")
    print(f"Sheet: {sheet_name}")
    print('='*60)
    
    # Get first 10 rows to see structure
    range_name = f"{sheet_name}!A1:Z10"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    
    values = result.get('values', [])
    
    if not values:
        print("No data found!")
        continue
    
    # Show headers (first row)
    print(f"\nHeaders (Row 1): {len(values[0])} columns")
    for i, header in enumerate(values[0]):
        print(f"  Column {chr(65+i)}: '{header}'")
    
    # Show a few data rows
    print(f"\nData rows (showing first 3):")
    for i, row in enumerate(values[1:4]):
        if i >= 3:
            break
        print(f"  Row {i+2}: {row[:5]}..." if len(row) > 5 else f"  Row {i+2}: {row}")
    
    # Check for column count consistency
    if len(values) > 1:
        header_count = len(values[0])
        data_counts = [len(row) for row in values[1:]]
        if any(count != header_count for count in data_counts):
            print(f"\n⚠️  WARNING: Inconsistent column counts!")
            print(f"  Headers: {header_count} columns")
            print(f"  Data rows: {set(data_counts)} columns")