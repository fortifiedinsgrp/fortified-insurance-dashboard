"""
Diagnose data reading issues from Google Sheets
"""

import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd

# Load credentials
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
)

service = build('sheets', 'v4', credentials=credentials)
spreadsheet_id = st.secrets["SPREADSHEET_ID"]

# Focus on the problematic Agency Stats sheet
sheet_name = "Daily Agency Stats"
print(f"Diagnosing issues with: {sheet_name}")
print("="*60)

# Get raw data without any processing
range_name = f"{sheet_name}!A1:Z10"
result = service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=range_name,
    valueRenderOption='UNFORMATTED_VALUE'  # Get raw values
).execute()

values = result.get('values', [])

print(f"\nRaw data from first 10 rows:")
for i, row in enumerate(values):
    print(f"\nRow {i+1} ({len(row)} columns):")
    for j, cell in enumerate(row):
        print(f"  Column {chr(65+j)}: Type={type(cell).__name__}, Value='{cell}'")
    print()

# Try different read methods
print("\n" + "="*60)
print("Testing different read approaches:")

# Method 1: Read with formatted values
result_formatted = service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range=f"{sheet_name}!A1:Z5",
    valueRenderOption='FORMATTED_VALUE'
).execute()

print("\n1. With FORMATTED_VALUE:")
formatted_values = result_formatted.get('values', [])
for i, row in enumerate(formatted_values[:3]):
    print(f"   Row {i+1}: {row[:5]}...")

# Method 2: Try reading specific ranges
print("\n2. Reading specific columns:")
for col in ['A', 'B', 'C', 'D', 'E', 'F']:
    result_col = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!{col}1:{col}5"
    ).execute()
    col_values = result_col.get('values', [])
    print(f"   Column {col}: {[v[0] if v else 'EMPTY' for v in col_values]}")

# Check for any special formatting or merged cells
print("\n" + "="*60)
print("Checking sheet properties:")

# Get spreadsheet metadata
spreadsheet = service.spreadsheets().get(
    spreadsheetId=spreadsheet_id,
    includeGridData=False
).execute()

# Find the sheet
for sheet in spreadsheet.get('sheets', []):
    if sheet['properties']['title'] == sheet_name:
        props = sheet['properties']
        print(f"Sheet ID: {props['sheetId']}")
        print(f"Grid Properties: {props.get('gridProperties', {})}")
        
# Create a simple dataframe test
print("\n" + "="*60)
print("Testing pandas DataFrame creation:")

if len(values) > 2:
    # Try with row 2 as headers (as we discovered earlier)
    try:
        df = pd.DataFrame(values[2:], columns=values[1])
        print(f"DataFrame created successfully with shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"\nFirst row data types:")
        for col in df.columns[:5]:
            if len(df) > 0:
                print(f"  {col}: {type(df.iloc[0][col])}")
    except Exception as e:
        print(f"Error creating DataFrame: {e}")
        print(f"Header row (row 2): {values[1]}")
        print(f"First data row (row 3): {values[2] if len(values) > 2 else 'No data'}")