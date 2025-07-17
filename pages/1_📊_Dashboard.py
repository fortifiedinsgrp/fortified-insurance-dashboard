"""
Main Dashboard Page - Real-time agency performance metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
try:
    from utils.google_sheets import (
        load_agency_stats, 
        load_agent_totals, 
        load_vendor_totals,
        get_agency_list
    )
except ImportError:
    # Fallback when Google Sheets is unavailable
    from utils.google_sheets_fallback import get_sheet_data_with_fallback
    
    def load_agency_stats(start_date, end_date):
        return get_sheet_data_with_fallback("Daily Agency Stats")
    
    def load_agent_totals(start_date, end_date):
        return get_sheet_data_with_fallback("Daily Agent Totals")
    
    def load_vendor_totals(start_date, end_date):
        return get_sheet_data_with_fallback("Daily Lead Vendor Totals")
    
    def get_agency_list():
        df = get_sheet_data_with_fallback("Daily Agency Stats")
        if 'Agency' in df.columns:
            return sorted(df['Agency'].unique().tolist())
        return ["Agency A", "Agency B", "Agency C"]
from utils.calculations import (
    calculate_agent_profitability,
    calculate_campaign_roas,
    aggregate_agency_stats,
    get_top_performers,
    get_at_risk_agents,
    get_campaign_performance
)

# Page config
st.set_page_config(
    page_title="Dashboard - Fortified Insurance",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Agency Performance Dashboard")

# Header controls
col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

with col1:
    # Get agency list
    try:
        agencies = get_agency_list()
        agency_options = ["All Agencies"] + agencies
    except:
        agency_options = ["All Agencies"]
    
    selected_agency = st.selectbox(
        "Select Agency",
        agency_options,
        key="agency_selector"
    )

with col2:
    date_preset = st.selectbox(
        "Date Range",
        ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "This Month", "Last Month", "Custom"],
        key="date_preset"
    )

# Calculate date range based on selection
if date_preset == "Today":
    start_date = end_date = date.today()
elif date_preset == "Yesterday":
    start_date = end_date = date.today() - timedelta(days=1)
elif date_preset == "Last 7 Days":
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
elif date_preset == "Last 30 Days":
    end_date = date.today()
    start_date = end_date - timedelta(days=29)
elif date_preset == "This Month":
    end_date = date.today()
    start_date = date(end_date.year, end_date.month, 1)
elif date_preset == "Last Month":
    today = date.today()
    first_day_this_month = date(today.year, today.month, 1)
    end_date = first_day_this_month - timedelta(days=1)
    start_date = date(end_date.year, end_date.month, 1)
else:  # Custom
    with col3:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=7))
    with col4:
        end_date = st.date_input("End Date", value=date.today())

# Display selected date range
st.markdown(f"**Showing data from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}**")

# Load data
try:
    with st.spinner("Loading data..."):
        # Load all data
        agency_df = load_agency_stats(start_date, end_date)
        agent_df = load_agent_totals(start_date, end_date)
        vendor_df = load_vendor_totals(start_date, end_date)
        
        # Filter by selected agency if not "All Agencies"
        if selected_agency != "All Agencies":
            # Check for both possible column names
            if not agency_df.empty:
                if 'Agency' in agency_df.columns:
                    agency_df = agency_df[agency_df['Agency'] == selected_agency]
                elif 'agency' in agency_df.columns:
                    agency_df = agency_df[agency_df['agency'] == selected_agency]
            
            if not agent_df.empty:
                if 'Agency' in agent_df.columns:
                    agent_df = agent_df[agent_df['Agency'] == selected_agency]
                elif 'agency' in agent_df.columns:
                    agent_df = agent_df[agent_df['agency'] == selected_agency]
            
            if not vendor_df.empty:
                if 'Agency' in vendor_df.columns:
                    vendor_df = vendor_df[vendor_df['Agency'] == selected_agency]
                elif 'agency' in vendor_df.columns:
                    vendor_df = vendor_df[vendor_df['agency'] == selected_agency]
        
        # Calculate aggregate stats
        stats = aggregate_agency_stats(agency_df, agent_df, vendor_df)
        
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Please ensure your Google Sheets connection is properly configured.")
    st.stop()

# Display key metrics
st.markdown("### 📈 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Revenue",
        value=f"${stats['totalRevenue']:,.0f}",
        delta=f"{stats['totalSales']} sales",
        help="Total revenue generated in the selected period"
    )

with col2:
    st.metric(
        label="Lead Spend",
        value=f"${stats['totalLeadSpend']:,.0f}",
        delta=f"{stats['totalLeads']} leads",
        help="Total amount spent on lead generation"
    )

with col3:
    st.metric(
        label="Profit",
        value=f"${stats['totalProfit']:,.0f}",
        delta=f"{(stats['totalProfit']/stats['totalRevenue']*100) if stats['totalRevenue'] > 0 else 0:.1f}% margin",
        delta_color="normal" if stats['totalProfit'] > 0 else "inverse",
        help="Revenue minus lead spend"
    )

with col4:
    st.metric(
        label="Avg ROAS",
        value=f"{stats['avgROAS']:.2f}x",
        delta=f"{stats['avgClosingRatio']:.1f}% close rate",
        help="Average Return on Ad Spend"
    )

st.markdown("---")

# Create two columns for agent and campaign data
left_col, right_col = st.columns(2)

with left_col:
    st.markdown("### 👥 Agent Performance")
    
    if not agent_df.empty:
        # Calculate agent metrics
        agent_metrics = calculate_agent_profitability(agent_df)
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Top Performers", "At Risk", "All Agents"])
        
        # Define column mappings once for all tabs
        column_mappings = {
            'agent': ['agent', 'Agent Name', 'Agent', 'agentName'],
            'totalSales': ['totalSales', 'Sales', 'Total Sales', 'sales'],
            'revenue': ['revenue', 'Revenue', 'Total Revenue', 'totalRevenue'],
            'agentProfitability': ['agentProfitability', 'Profit', 'profitability', 'Agent Profitability'],
            'closingRatio': ['closingRatio', 'Closing Ratio', 'Close Rate', 'closeRate']
        }
        
        with tab1:
            top_agents = get_top_performers(agent_metrics, n=10)
            if not top_agents.empty:
                
                # Find which columns actually exist
                display_cols = []
                display_names = []
                
                for desired_col, possible_names in column_mappings.items():
                    for col_name in possible_names:
                        if col_name in top_agents.columns:
                            display_cols.append(col_name)
                            if desired_col == 'agent':
                                display_names.append('Agent')
                            elif desired_col == 'totalSales':
                                display_names.append('Sales')
                            elif desired_col == 'revenue':
                                display_names.append('Revenue')
                            elif desired_col == 'agentProfitability':
                                display_names.append('Profit')
                            elif desired_col == 'closingRatio':
                                display_names.append('Close %')
                            break
                
                if display_cols:
                    display_df = top_agents[display_cols].copy()
                    display_df.columns = display_names
                    
                    # Format currency columns
                    if 'Revenue' in display_df.columns:
                        display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
                    if 'Profit' in display_df.columns:
                        display_df['Profit'] = display_df['Profit'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
                    if 'Close %' in display_df.columns:
                        display_df['Close %'] = display_df['Close %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Agent data structure not recognized. Available columns: " + ", ".join(top_agents.columns))
            else:
                # Check if we have agents but none are profitable
                if not agent_metrics.empty:
                    st.warning("⚠️ No agents with positive profitability in the selected period")
                    # Show the least negative performers instead
                    least_negative = agent_metrics.nlargest(5, 'agentProfitability')
                    if not least_negative.empty:
                        st.markdown("**Least Negative Performers:**")
                        display_cols = []
                        display_names = []
                        
                        for desired_col, possible_names in column_mappings.items():
                            for col_name in possible_names:
                                if col_name in least_negative.columns:
                                    display_cols.append(col_name)
                                    if desired_col == 'agent':
                                        display_names.append('Agent')
                                    elif desired_col == 'totalSales':
                                        display_names.append('Sales')
                                    elif desired_col == 'revenue':
                                        display_names.append('Revenue')
                                    elif desired_col == 'agentProfitability':
                                        display_names.append('Profit')
                                    elif desired_col == 'closingRatio':
                                        display_names.append('Close %')
                                    break
                        
                        if display_cols:
                            display_df = least_negative[display_cols].copy()
                            display_df.columns = display_names
                            
                            if 'Revenue' in display_df.columns:
                                display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
                            if 'Profit' in display_df.columns:
                                display_df['Profit'] = display_df['Profit'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
                            if 'Close %' in display_df.columns:
                                display_df['Close %'] = display_df['Close %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")
                            
                            st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No agent data available for the selected period")
        
        with tab2:
            at_risk = get_at_risk_agents(agent_metrics)
            if not at_risk.empty:
                st.warning(f"⚠️ {len(at_risk)} agents with profitability < ${200}")
                
                # Use same column mapping logic
                display_cols = []
                display_names = []
                
                for desired_col, possible_names in column_mappings.items():
                    for col_name in possible_names:
                        if col_name in at_risk.columns:
                            display_cols.append(col_name)
                            if desired_col == 'agent':
                                display_names.append('Agent')
                            elif desired_col == 'totalSales':
                                display_names.append('Sales')
                            elif desired_col == 'revenue':
                                display_names.append('Revenue')
                            elif desired_col == 'agentProfitability':
                                display_names.append('Profit')
                            elif desired_col == 'closingRatio':
                                display_names.append('Close %')
                            break
                
                if display_cols:
                    display_df = at_risk[display_cols].copy()
                    display_df.columns = display_names
                    
                    # Format columns
                    if 'Revenue' in display_df.columns:
                        display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
                    if 'Profit' in display_df.columns:
                        display_df['Profit'] = display_df['Profit'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
                    if 'Close %' in display_df.columns:
                        display_df['Close %'] = display_df['Close %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.success("✅ No at-risk agents!")
        
        with tab3:
            # Show all agents with search
            search = st.text_input("Search agents...", key="agent_search")
            
            display_df = agent_metrics.copy()
            
            # Find agent column name
            agent_col = None
            for col in ['agent', 'Agent Name', 'Agent', 'agentName']:
                if col in display_df.columns:
                    agent_col = col
                    break
            
            if search and agent_col:
                display_df = display_df[display_df[agent_col].str.contains(search, case=False, na=False)]
            
            if not display_df.empty:
                # Use same column mapping logic as above
                display_cols = []
                display_names = []
                
                for desired_col, possible_names in column_mappings.items():
                    for col_name in possible_names:
                        if col_name in display_df.columns:
                            display_cols.append(col_name)
                            if desired_col == 'agent':
                                display_names.append('Agent')
                            elif desired_col == 'totalSales':
                                display_names.append('Sales')
                            elif desired_col == 'revenue':
                                display_names.append('Revenue')
                            elif desired_col == 'agentProfitability':
                                display_names.append('Profit')
                            elif desired_col == 'closingRatio':
                                display_names.append('Close %')
                            break
                
                if display_cols:
                    display_df = display_df[display_cols].copy()
                    display_df.columns = display_names
                    
                    # Format columns
                    if 'Revenue' in display_df.columns:
                        display_df['Revenue'] = display_df['Revenue'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
                    if 'Profit' in display_df.columns:
                        display_df['Profit'] = display_df['Profit'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
                    if 'Close %' in display_df.columns:
                        display_df['Close %'] = display_df['Close %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No agents found matching your search")
    else:
        st.info("No agent data available for the selected period")

with right_col:
    st.markdown("### 📊 Campaign Performance")
    
    if not vendor_df.empty:
        # Calculate campaign metrics
        campaign_metrics = calculate_campaign_roas(vendor_df)
        
        # Sort by ROAS
        campaign_sorted = get_campaign_performance(campaign_metrics, sort_by='ROAS', ascending=False)
        
        if not campaign_sorted.empty:
            # Create a bar chart of top campaigns by ROAS
            top_campaigns = campaign_sorted.head(10)
            
            # Find vendor/campaign column
            vendor_col = None
            for col in ['vendor', 'Vendor', 'Campaign', 'campaign']:
                if col in top_campaigns.columns:
                    vendor_col = col
                    break
            
            if vendor_col and 'ROAS' in top_campaigns.columns:
                # Filter out campaigns with 0 ROAS
                top_campaigns = top_campaigns[top_campaigns['ROAS'] > 0]
                if not top_campaigns.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=top_campaigns[vendor_col],
                        y=top_campaigns['ROAS'],
                        marker_color=['green' if x >= 2 else 'orange' if x >= 1 else 'red' 
                                     for x in top_campaigns['ROAS']],
                        text=[f"{x:.2f}x" for x in top_campaigns['ROAS']],
                        textposition='outside'
                    ))
                    
                    fig.update_layout(
                        title="Top Campaigns by ROAS",
                        xaxis_title="Campaign/Vendor",
                        yaxis_title="ROAS",
                        height=400,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No campaigns with positive ROAS in the selected period")
            
            # Display detailed table with flexible column mapping
            column_mappings = {
                'vendor': ['vendor', 'Vendor', 'Campaign', 'campaign'],
                'leads': ['leads', 'Leads', 'Paid Calls', 'paidCalls'],
                'sales': ['sales', 'Sales', '# Unique Sales', 'uniqueSales'],
                'revenue': ['revenue', 'Revenue', 'Total Revenue'],
                'leadSpend': ['leadSpend', 'Lead Cost', 'Lead Spend', 'spend'],
                'ROAS': ['ROAS', 'roas'],
                'profit': ['profit', 'Profit', 'Net Profit']
            }
            
            display_cols = []
            display_names = []
            
            for desired_col, possible_names in column_mappings.items():
                for col_name in possible_names:
                    if col_name in campaign_sorted.columns:
                        display_cols.append(col_name)
                        if desired_col == 'vendor':
                            display_names.append('Vendor')
                        elif desired_col == 'leads':
                            display_names.append('Leads')
                        elif desired_col == 'sales':
                            display_names.append('Sales')
                        elif desired_col == 'revenue':
                            display_names.append('Revenue')
                        elif desired_col == 'leadSpend':
                            display_names.append('Spend')
                        elif desired_col == 'ROAS':
                            display_names.append('ROAS')
                        elif desired_col == 'profit':
                            display_names.append('Profit')
                        break
            
            if display_cols:
                display_df = campaign_sorted[display_cols].copy()
                display_df.columns = display_names
                
                # Format columns
                for col in ['Revenue', 'Spend', 'Profit']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
                if 'ROAS' in display_df.columns:
                    display_df['ROAS'] = display_df['ROAS'].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else "0.00x")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No campaign data available for analysis")
    else:
        st.info("No campaign data available for the selected period")

# Add a trends section
st.markdown("---")
st.markdown("### 📈 Trends Analysis")

if not agency_df.empty:
    # Find date column
    date_col = None
    for col in ['Date', 'date', 'DATE']:
        if col in agency_df.columns:
            date_col = col
            break
    
    # Find revenue column
    revenue_col = None
    for col in ['Total Rev', 'revenue', 'Revenue', 'Total Revenue']:
        if col in agency_df.columns:
            revenue_col = col
            break
    
    if date_col and revenue_col:
        # Create daily revenue trend
        agency_df[date_col] = pd.to_datetime(agency_df[date_col])
        # Clean revenue column if it contains strings with commas
        if agency_df[revenue_col].dtype == 'object':
            agency_df[revenue_col] = agency_df[revenue_col].astype(str).str.replace(',', '').str.replace('$', '')
        agency_df[revenue_col] = pd.to_numeric(agency_df[revenue_col], errors='coerce')
        daily_revenue = agency_df.groupby(date_col)[revenue_col].sum().reset_index()
        
        fig = px.line(
            daily_revenue, 
            x=date_col, 
            y=revenue_col,
            title="Daily Revenue Trend",
            labels={revenue_col: 'Revenue ($)', date_col: 'Date'}
        )
        
        fig.update_traces(mode='lines+markers')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data for trends analysis")
else:
    st.info("Insufficient data for trends analysis")

# Export functionality
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    if st.button("📥 Export to CSV"):
        # Combine all data for export
        export_data = {
            'Daily Agency Stats': agency_df,
            'Agent Performance': agent_df,
            'Campaign Performance': vendor_df
        }
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # For now, just show a message
        st.success(f"Export functionality coming soon! Data from {start_date} to {end_date}")

with col2:
    if st.button("📧 Email Report"):
        st.info("Email report functionality coming soon!")

# Refresh button
with col3:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()