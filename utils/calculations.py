"""
Business calculations for insurance agency metrics
Updated to work with actual Google Sheets column names
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import date, datetime

# Constants
PROFITABILITY_THRESHOLD = 200  # Agents below this are considered "at risk"

def safe_divide(numerator: Union[pd.Series, float], denominator: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """Safely divide two series, returning 0 for division by zero"""
    if isinstance(numerator, pd.Series) and isinstance(denominator, pd.Series):
        return pd.Series(np.where(denominator != 0, numerator / denominator, 0), index=numerator.index)
    elif isinstance(numerator, pd.Series):
        return pd.Series(np.where(denominator != 0, numerator / denominator, 0), index=numerator.index)
    elif isinstance(denominator, pd.Series):
        return pd.Series(np.where(denominator != 0, numerator / denominator, 0), index=denominator.index)
    else:
        return numerator / denominator if denominator != 0 else 0

def calculate_agent_profitability(df: pd.DataFrame) -> pd.DataFrame:
    """Process agent data - using existing calculations from the sheet
    
    Args:
        df: DataFrame with agent data
        
    Returns:
        DataFrame with agent metrics
    """
    if df.empty:
        return df
    
    # Create a copy to avoid modifying original
    result = df.copy()
    
    # The sheet already has most calculations, so we'll use them if available
    # First, check if we have the pre-calculated columns
    if 'Agent Profitability' in result.columns:
        # Use existing calculations
        numeric_cols = ['Sales', 'Revenue', 'Count Paid Calls', 'Agent Profitability', 
                       'Closing Ratio', 'Profit', 'Lead Spend']
        
        for col in numeric_cols:
            if col in result.columns:
                # Convert to numeric and fill NaN values
                result[col] = pd.to_numeric(result[col], errors='coerce')
                if isinstance(result[col], pd.Series):
                    result.loc[:, col] = result[col].fillna(0)
        
        # Rename columns for consistency with the dashboard
        result.rename(columns={
            'Agent Name': 'agent',
            'Sales': 'totalSales',
            'Revenue': 'revenue',
            'Count Paid Calls': 'paidCalls',
            'Closing Ratio': 'closingRatio',
            'Agent Profitability': 'agentProfitability',
            'Total Calls': 'totalCalls',
            'Lead Spend': 'leadSpend'
        }, inplace=True)
    else:
        # Fallback: calculate from scratch if pre-calculated columns don't exist
        # Map column names to expected names
        column_mapping = {
            'Agent Name': 'agent',
            'Total Calls': 'totalCalls',
            'Count Paid Calls': 'paidCalls',
            'Sales': 'totalSales',
            'Revenue': 'revenue'
        }
        
        # Rename columns if they exist
        result.rename(columns=column_mapping, inplace=True)
        
        # Convert numeric columns - handle both numeric and string values
        numeric_cols = ['totalCalls', 'paidCalls', 'totalSales', 'revenue']
        for col in numeric_cols:
            if col in result.columns:
                # If column contains strings with commas, clean them first
                if result[col].dtype == 'object':
                    result[col] = result[col].astype(str).str.replace(',', '').str.replace('$', '')
                numeric_series = pd.to_numeric(result[col], errors='coerce')
                if isinstance(numeric_series, pd.Series):
                    result[col] = numeric_series.fillna(0)
        
        # Calculate closing ratio (sales / paid calls * 100)
        if 'totalSales' in result.columns and 'paidCalls' in result.columns:
            total_sales = result['totalSales'] if isinstance(result['totalSales'], pd.Series) else pd.Series([result['totalSales']])
            paid_calls = result['paidCalls'] if isinstance(result['paidCalls'], pd.Series) else pd.Series([result['paidCalls']])
            result['closingRatio'] = safe_divide(total_sales, paid_calls) * 100
            if isinstance(result['closingRatio'], pd.Series):
                result['closingRatio'] = result['closingRatio'].round(2)
        
        # Calculate agent profitability only if lead spend is available in the data
        if 'revenue' in result.columns and 'leadSpend' in result.columns:
            # Use lead spend from spreadsheet
            result['agentProfitability'] = result['revenue'] - result['leadSpend']
        elif 'revenue' in result.columns and 'Lead Spend' in result.columns:
            # Alternative column name
            result['agentProfitability'] = result['revenue'] - result['Lead Spend']
    
    # Add at-risk flag
    if 'agentProfitability' in result.columns:
        result['isAtRisk'] = result['agentProfitability'] < PROFITABILITY_THRESHOLD
    
    # Calculate revenue per call if not present
    if 'revenue' in result.columns and 'paidCalls' in result.columns and 'revenuePerCall' not in result.columns:
        revenue = result['revenue'] if isinstance(result['revenue'], pd.Series) else pd.Series([result['revenue']])
        paid_calls = result['paidCalls'] if isinstance(result['paidCalls'], pd.Series) else pd.Series([result['paidCalls']])
        rev_per_call = safe_divide(revenue, paid_calls)
        if isinstance(rev_per_call, pd.Series):
            result['revenuePerCall'] = rev_per_call.round(2)
        else:
            result['revenuePerCall'] = round(rev_per_call, 2)
    
    return result

def calculate_campaign_roas(df: pd.DataFrame) -> pd.DataFrame:
    """Process campaign data - using existing calculations where available
    
    Args:
        df: DataFrame with campaign data
        
    Returns:
        DataFrame with campaign metrics
    """
    if df.empty:
        return df
    
    result = df.copy()
    
    # Check if we have pre-calculated ROAS
    if 'ROAS' in result.columns:
        # Use existing calculations
        numeric_cols = ['Paid Calls', '# Unique Sales', 'Revenue', 'Lead Cost', 
                       'ROAS', 'Profit', '% Closing Ratio']
        
        for col in numeric_cols:
            if col in result.columns:
                if result[col].dtype == 'object':
                    result[col] = result[col].astype(str).str.replace(',', '').str.replace('$', '')
                numeric_series = pd.to_numeric(result[col], errors='coerce')
                result[col] = numeric_series.fillna(0)
        
        # Rename for consistency
        result.rename(columns={
            'Campaign': 'vendor',
            'Paid Calls': 'leads',
            '# Unique Sales': 'sales',
            'Revenue': 'revenue',
            'Lead Cost': 'leadSpend',
            'ROAS': 'ROAS',
            'Profit': 'profit',
            '% Closing Ratio': 'closingRatio'
        }, inplace=True)
    else:
        # Fallback: calculate from scratch
        # Map column names to expected names
        column_mapping = {
            'Paid Calls': 'leads',
            '# Unique Sales': 'sales',
            'Revenue': 'revenue',
            'Lead Cost': 'leadSpend',
            'Campaign': 'vendor'
        }
        
        # Rename columns if they exist
        result.rename(columns=column_mapping, inplace=True)
        
        # Convert numeric columns
        numeric_cols = ['leads', 'sales', 'revenue', 'leadSpend']
        for col in numeric_cols:
            if col in result.columns:
                if result[col].dtype == 'object':
                    result[col] = result[col].astype(str).str.replace(',', '').str.replace('$', '')
                numeric_series = pd.to_numeric(result[col], errors='coerce')
                result[col] = numeric_series.fillna(0)
        
        # Calculate ROAS (revenue / spend)
        if 'revenue' in result.columns and 'leadSpend' in result.columns:
            result['ROAS'] = safe_divide(result['revenue'], result['leadSpend']).round(2)
        
        # Calculate closing ratio
        if 'sales' in result.columns and 'leads' in result.columns:
            result['closingRatio'] = safe_divide(result['sales'], result['leads']) * 100
            result['closingRatio'] = result['closingRatio'].round(2)
        
        # Calculate profit
        if 'revenue' in result.columns and 'leadSpend' in result.columns:
            result['profit'] = result['revenue'] - result['leadSpend']
    
    # Calculate additional metrics if not present
    if 'costPerLead' not in result.columns and 'leadSpend' in result.columns and 'leads' in result.columns:
        result['costPerLead'] = safe_divide(result['leadSpend'], result['leads']).round(2)
    
    if 'costPerSale' not in result.columns and 'leadSpend' in result.columns and 'sales' in result.columns:
        result['costPerSale'] = safe_divide(result['leadSpend'], result['sales']).round(2)
    
    if 'profitMargin' not in result.columns and 'profit' in result.columns and 'revenue' in result.columns:
        result['profitMargin'] = safe_divide(result['profit'], result['revenue']) * 100
        result['profitMargin'] = result['profitMargin'].round(2)
    
    return result

def aggregate_agency_stats(agency_df: pd.DataFrame, 
                         agent_df: pd.DataFrame,
                         vendor_df: pd.DataFrame) -> Dict[str, Union[int, float]]:
    """Aggregate statistics across all data sources
    
    Args:
        agency_df: Agency stats DataFrame
        agent_df: Agent totals DataFrame
        vendor_df: Vendor totals DataFrame
        
    Returns:
        Dictionary with aggregated metrics
    """
    stats: Dict[str, Union[int, float]] = {
        'totalRevenue': 0.0,
        'totalLeadSpend': 0.0,
        'totalProfit': 0.0,
        'totalLeads': 0,
        'totalSales': 0,
        'avgClosingRatio': 0.0,
        'avgROAS': 0.0,
        'totalAgents': 0,
        'atRiskAgents': 0
    }
    
    # Agency stats
    if not agency_df.empty:
        # Total Rev column contains revenue
        if 'Total Rev' in agency_df.columns:
            total_rev = agency_df['Total Rev']
            if total_rev.dtype == 'object':
                total_rev = total_rev.astype(str).str.replace(',', '').str.replace('$', '')
            numeric_rev = pd.to_numeric(total_rev, errors='coerce')
            stats['totalRevenue'] = float(numeric_rev.sum())
        
        # Total Leads column contains lead spend (based on diagnostic results)
        if 'Total Leads' in agency_df.columns:
            total_leads = agency_df['Total Leads']
            if total_leads.dtype == 'object':
                total_leads = total_leads.astype(str).str.replace(',', '').str.replace('$', '')
            numeric_leads = pd.to_numeric(total_leads, errors='coerce')
            stats['totalLeadSpend'] = float(numeric_leads.sum())
        
        # Alternative: sum individual vendor columns if present
        vendor_cols = ['QW', 'QS', 'SF']
        if all(col in agency_df.columns for col in vendor_cols) and stats['totalLeadSpend'] == 0:
            total_vendor_spend = 0.0
            for col in vendor_cols:
                col_data = agency_df[col]
                if col_data.dtype == 'object':
                    col_data = col_data.astype(str).str.replace(',', '').str.replace('$', '')
                numeric_col = pd.to_numeric(col_data, errors='coerce')
                total_vendor_spend += float(numeric_col.sum())
            if total_vendor_spend > 0:
                stats['totalLeadSpend'] = total_vendor_spend
    
    # Agent stats
    if not agent_df.empty:
        # Process agent data
        agent_calc = calculate_agent_profitability(agent_df)
        stats['totalAgents'] = len(agent_calc)
        
        # Count at-risk agents
        if 'isAtRisk' in agent_calc.columns:
            stats['atRiskAgents'] = int(agent_calc['isAtRisk'].sum())
        
        # Get total sales from agents
        if 'totalSales' in agent_calc.columns:
            stats['totalSales'] = int(agent_calc['totalSales'].sum())
        elif 'Sales' in agent_df.columns:
            sales_data = pd.to_numeric(agent_df['Sales'], errors='coerce')
            stats['totalSales'] = int(sales_data.sum())
        
        # Calculate average closing ratio (exclude zeros)
        closing_col = 'closingRatio' if 'closingRatio' in agent_calc.columns else 'Closing Ratio'
        if closing_col in agent_calc.columns:
            non_zero_ratio = agent_calc[agent_calc[closing_col] > 0][closing_col]
            if len(non_zero_ratio) > 0:
                stats['avgClosingRatio'] = float(non_zero_ratio.mean())
    
    # Vendor stats (campaigns)
    if not vendor_df.empty:
        vendor_calc = calculate_campaign_roas(vendor_df)
        
        # Get total leads (paid calls)
        if 'leads' in vendor_calc.columns:
            stats['totalLeads'] = int(vendor_calc['leads'].sum())
        elif 'Paid Calls' in vendor_df.columns:
            leads_data = pd.to_numeric(vendor_df['Paid Calls'], errors='coerce')
            stats['totalLeads'] = int(leads_data.sum())
        
        # Get lead spend from vendor data if not already set
        if stats['totalLeadSpend'] == 0:
            if 'leadSpend' in vendor_calc.columns:
                stats['totalLeadSpend'] = float(vendor_calc['leadSpend'].sum())
            elif 'Lead Cost' in vendor_df.columns:
                lead_cost = vendor_df['Lead Cost']
                if lead_cost.dtype == 'object':
                    lead_cost = lead_cost.astype(str).str.replace(',', '').str.replace('$', '')
                numeric_cost = pd.to_numeric(lead_cost, errors='coerce')
                stats['totalLeadSpend'] = float(numeric_cost.sum())
        
        # Calculate average ROAS (exclude zeros)
        if 'ROAS' in vendor_calc.columns:
            non_zero_roas = vendor_calc[vendor_calc['ROAS'] > 0]['ROAS']
            if len(non_zero_roas) > 0:
                stats['avgROAS'] = float(non_zero_roas.mean())
    
    # Calculate profit
    stats['totalProfit'] = stats['totalRevenue'] - stats['totalLeadSpend']
    
    # Round all values
    for key in stats:
        if isinstance(stats[key], (int, float)):
            if key in ['totalLeads', 'totalSales', 'totalAgents', 'atRiskAgents']:
                stats[key] = int(stats[key])
            else:
                stats[key] = round(float(stats[key]), 2)
    
    return stats

def get_top_performers(agent_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Get top performing agents by profitability
    
    Args:
        agent_df: DataFrame with agent data
        n: Number of top performers to return
        
    Returns:
        DataFrame with top performers (positive profitability only)
    """
    if agent_df.empty:
        return pd.DataFrame()
    
    df_calc = calculate_agent_profitability(agent_df)
    
    if 'agentProfitability' in df_calc.columns:
        # Filter to only positive profitability and sort descending
        positive_performers = df_calc[df_calc['agentProfitability'] > 0]
        if len(positive_performers) > 0:
            return positive_performers.nlargest(n, 'agentProfitability')
        else:
            # If no positive performers, return empty DataFrame
            return pd.DataFrame()
    
    return pd.DataFrame()

def get_at_risk_agents(agent_df: pd.DataFrame) -> pd.DataFrame:
    """Get agents with profitability below threshold
    
    Args:
        agent_df: DataFrame with agent data
        
    Returns:
        DataFrame with at-risk agents
    """
    if agent_df.empty:
        return pd.DataFrame()
    
    df_calc = calculate_agent_profitability(agent_df)
    
    if 'agentProfitability' in df_calc.columns:
        # Get agents below threshold
        at_risk = df_calc[df_calc['agentProfitability'] < PROFITABILITY_THRESHOLD]
        return at_risk.sort_values('agentProfitability', ascending=True)
    
    return pd.DataFrame()

def get_campaign_performance(vendor_df: pd.DataFrame, 
                           sort_by: str = 'ROAS',
                           ascending: bool = False) -> pd.DataFrame:
    """Get campaign performance sorted by metric
    
    Args:
        vendor_df: DataFrame with vendor/campaign data
        sort_by: Column to sort by
        ascending: Sort order
        
    Returns:
        DataFrame sorted by specified metric
    """
    if vendor_df.empty:
        return pd.DataFrame()
    
    df_calc = calculate_campaign_roas(vendor_df)
    
    # Filter out campaigns with zero ROAS if sorting by ROAS
    if sort_by == 'ROAS' and 'ROAS' in df_calc.columns:
        df_calc = df_calc[df_calc['ROAS'] > 0]
    
    if sort_by in df_calc.columns:
        return df_calc.sort_values(sort_by, ascending=ascending)
    
    return df_calc

def calculate_period_comparison(current_df: pd.DataFrame,
                              previous_df: pd.DataFrame,
                              metric_col: str) -> Tuple[float, float]:
    """Calculate period-over-period comparison
    
    Args:
        current_df: Current period DataFrame
        previous_df: Previous period DataFrame
        metric_col: Column name to compare
        
    Returns:
        Tuple of (change_value, change_percentage)
    """
    if current_df.empty or previous_df.empty:
        return (0.0, 0.0)
    
    if metric_col not in current_df.columns or metric_col not in previous_df.columns:
        return (0.0, 0.0)
    
    # Convert to numeric, handling string values
    current_data = current_df[metric_col]
    previous_data = previous_df[metric_col]
    
    if current_data.dtype == 'object':
        current_data = current_data.astype(str).str.replace(',', '').str.replace('$', '')
    if previous_data.dtype == 'object':
        previous_data = previous_data.astype(str).str.replace(',', '').str.replace('$', '')
    
    current_numeric = pd.to_numeric(current_data, errors='coerce')
    previous_numeric = pd.to_numeric(previous_data, errors='coerce')
    
    current_val = float(current_numeric.sum())
    previous_val = float(previous_numeric.sum())
    
    change_val = current_val - previous_val
    change_pct = safe_divide(change_val, previous_val) * 100
    
    return (round(change_val, 2), round(float(change_pct), 2))

def get_weekly_summary(df: pd.DataFrame, 
                      date_col: str = 'Date',
                      metric_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """Aggregate data by week
    
    Args:
        df: DataFrame with daily data
        date_col: Name of date column
        metric_cols: List of columns to aggregate
        
    Returns:
        DataFrame with weekly aggregates
    """
    if df.empty or date_col not in df.columns:
        return pd.DataFrame()
    
    # Convert date column
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Group by week
    df['Week'] = df[date_col].dt.to_period('W')
    
    if metric_cols is None:
        # Automatically detect numeric columns
        metric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Aggregate
    weekly = df.groupby('Week')[metric_cols].sum().reset_index()
    weekly['Week'] = weekly['Week'].astype(str)
    
    return weekly

def get_monthly_summary(df: pd.DataFrame,
                       date_col: str = 'Date',
                       metric_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """Aggregate data by month
    
    Args:
        df: DataFrame with daily data
        date_col: Name of date column
        metric_cols: List of columns to aggregate
        
    Returns:
        DataFrame with monthly aggregates
    """
    if df.empty or date_col not in df.columns:
        return pd.DataFrame()
    
    # Convert date column
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Group by month
    df['Month'] = df[date_col].dt.to_period('M')
    
    if metric_cols is None:
        # Automatically detect numeric columns
        metric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Aggregate
    monthly = df.groupby('Month')[metric_cols].sum().reset_index()
    monthly['Month'] = monthly['Month'].astype(str)
    
    return monthly