"""
Diagnostic tool to check Google Sheets structure
Run this to see what columns are actually in your sheets
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from utils.google_sheets import (
    load_agency_stats, 
    load_agent_totals, 
    load_vendor_totals
)

st.set_page_config(page_title="Sheet Diagnostics", page_icon="🔍")

st.title("🔍 Google Sheets Diagnostic Tool")
st.markdown("This tool helps identify the structure of your Google Sheets data.")

# Load yesterday's data as a test
yesterday = date.today() - timedelta(days=1)

st.markdown("### Loading data from yesterday...")

try:
    # Load each sheet
    agency_df = load_agency_stats(yesterday, yesterday)
    agent_df = load_agent_totals(yesterday, yesterday)
    vendor_df = load_vendor_totals(yesterday, yesterday)
    
    # Display Agency Stats
    st.markdown("---")
    st.markdown("### 📊 Daily Agency Stats Sheet")
    if not agency_df.empty:
        st.write(f"**Shape:** {agency_df.shape[0]} rows, {agency_df.shape[1]} columns")
        st.write("**Columns:**")
        for i, col in enumerate(agency_df.columns):
            dtype = str(agency_df[col].dtype)
            sample_val = agency_df[col].iloc[0] if len(agency_df) > 0 else "N/A"
            st.write(f"{i+1}. `{col}` - Type: {dtype} - Sample: {sample_val}")
        
        st.markdown("**First 5 rows:**")
        st.dataframe(agency_df.head())
        
        # Check for revenue columns
        st.markdown("**Potential Revenue Columns:**")
        for col in agency_df.columns:
            if any(keyword in col.lower() for keyword in ['rev', 'revenue', 'total']):
                total = pd.to_numeric(agency_df[col].astype(str).str.replace(',', '').str.replace('$', ''), errors='coerce').sum()
                st.write(f"- `{col}`: Total = ${total:,.2f}")
    else:
        st.warning("Agency stats sheet is empty!")
    
    # Display Agent Totals
    st.markdown("---")
    st.markdown("### 👥 Daily Agent Totals Sheet")
    if not agent_df.empty:
        st.write(f"**Shape:** {agent_df.shape[0]} rows, {agent_df.shape[1]} columns")
        st.write("**Columns:**")
        for i, col in enumerate(agent_df.columns):
            dtype = str(agent_df[col].dtype)
            sample_val = agent_df[col].iloc[0] if len(agent_df) > 0 else "N/A"
            st.write(f"{i+1}. `{col}` - Type: {dtype} - Sample: {sample_val}")
        
        st.markdown("**First 5 rows:**")
        st.dataframe(agent_df.head())
        
        # Check which agents have revenue
        if 'Revenue' in agent_df.columns and 'Agent Name' in agent_df.columns:
            st.markdown("**Agent Revenue Summary:**")
            agent_summary = agent_df[['Agent Name', 'Revenue']].copy()
            agent_summary['Revenue'] = pd.to_numeric(agent_summary['Revenue'].astype(str).str.replace(',', '').str.replace('$', ''), errors='coerce')
            agent_summary = agent_summary.sort_values('Revenue', ascending=False).head(10)
            st.dataframe(agent_summary)
    else:
        st.warning("Agent totals sheet is empty!")
    
    # Display Vendor Totals
    st.markdown("---")
    st.markdown("### 📊 Daily Lead Vendor Totals Sheet")
    if not vendor_df.empty:
        st.write(f"**Shape:** {vendor_df.shape[0]} rows, {vendor_df.shape[1]} columns")
        st.write("**Columns:**")
        for i, col in enumerate(vendor_df.columns):
            dtype = str(vendor_df[col].dtype)
            sample_val = vendor_df[col].iloc[0] if len(vendor_df) > 0 else "N/A"
            st.write(f"{i+1}. `{col}` - Type: {dtype} - Sample: {sample_val}")
        
        st.markdown("**First 5 rows:**")
        st.dataframe(vendor_df.head())
    else:
        st.warning("Vendor totals sheet is empty!")
    
    # Summary
    st.markdown("---")
    st.markdown("### 📋 Summary")
    st.success("Data loaded successfully!")
    
    # Provide mapping recommendations
    st.markdown("### 🔧 Recommended Column Mappings")
    
    st.markdown("**For calculations.py, update the column mappings to:**")
    code = "```python\n"
    
    # Agency mappings
    code += "# Agency Stats Columns\n"
    if not agency_df.empty:
        revenue_cols = [col for col in agency_df.columns if 'rev' in col.lower() or 'total' in col.lower()]
        if revenue_cols:
            code += f"revenue_column = '{revenue_cols[0]}'\n"
    
    # Agent mappings  
    code += "\n# Agent Columns\n"
    if not agent_df.empty:
        if 'Agent Name' in agent_df.columns:
            code += "agent_name_column = 'Agent Name'\n"
        if 'Revenue' in agent_df.columns:
            code += "agent_revenue_column = 'Revenue'\n"
        if 'Count Paid Calls' in agent_df.columns:
            code += "paid_calls_column = 'Count Paid Calls'\n"
        if 'Sales' in agent_df.columns:
            code += "sales_column = 'Sales'\n"
    
    # Vendor mappings
    code += "\n# Vendor/Campaign Columns\n"
    if not vendor_df.empty:
        if 'Campaign' in vendor_df.columns:
            code += "campaign_column = 'Campaign'\n"
        if 'Revenue' in vendor_df.columns:
            code += "vendor_revenue_column = 'Revenue'\n"
        if 'Lead Cost' in vendor_df.columns:
            code += "lead_cost_column = 'Lead Cost'\n"
    
    code += "```"
    st.markdown(code)
    
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.exception(e)