"""
Report generation module for creating different types of reports
"""

import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
import base64
import numpy as np

from .calculations import (
    calculate_agent_profitability, 
    calculate_campaign_roas,
    aggregate_agency_stats,
    get_top_performers,
    get_at_risk_agents,
    get_campaign_performance,
    get_weekly_summary,
    get_monthly_summary
)
try:
    from .google_sheets import get_sheet_data
except ImportError:
    # Fallback if google_sheets module doesn't exist
    try:
        from .google_sheets_fallback import get_sheet_data_with_fallback as get_sheet_data
    except ImportError:
        def get_sheet_data(sheet_name):
            import pandas as pd
            return pd.DataFrame()

class ReportGenerator:
    """Generate various types of reports"""
    
    def __init__(self):
        self.report_types = {
            'daily': self.generate_daily_report,
            'weekly': self.generate_weekly_report,
            'monthly': self.generate_monthly_report,
            'agent_performance': self.generate_agent_performance_report,
            'campaign_analysis': self.generate_campaign_analysis_report,
            'executive_summary': self.generate_executive_summary
        }
    
    def _aggregate_date_range_data(self, data: pd.DataFrame, 
                                  groupby_cols: Optional[List[str]] = None) -> pd.DataFrame:
        """Aggregate data across multiple dates for date range reports"""
        if data.empty:
            return data
            
        # Default groupby columns for different data types
        if groupby_cols is None:
            # Try to identify the type of data and group accordingly
            if 'Agent Name' in data.columns or 'agent' in data.columns:
                groupby_cols = ['Agent Name'] if 'Agent Name' in data.columns else ['agent']
            elif 'Campaign' in data.columns or 'vendor' in data.columns:
                groupby_cols = ['Campaign'] if 'Campaign' in data.columns else ['vendor']
            else:
                # For agency data, we'll sum everything
                groupby_cols = []
        
        # If no grouping columns, just sum all numeric columns
        if not groupby_cols:
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            result = pd.DataFrame([data[numeric_cols].sum()]) if len(numeric_cols) > 0 else data.head(1)
            # Keep first row's non-numeric data
            for col in data.columns:
                if col not in numeric_cols and not data[col].empty:
                    result[col] = data[col].iloc[0] if len(data) > 0 else ''
            return result
        
        # Group by specified columns and sum numeric columns
        try:
            # Identify numeric columns to sum
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            # Remove Date column from numeric if it exists
            numeric_cols = [col for col in numeric_cols if 'Date' not in col]
            
            if len(numeric_cols) == 0:
                # No numeric columns to aggregate, just return unique values
                return data.drop_duplicates(subset=groupby_cols)
            
            # Create aggregation dictionary
            agg_dict = {col: 'sum' for col in numeric_cols}
            
            # Add first value for text columns
            text_cols = [col for col in data.columns 
                        if col not in groupby_cols and col not in numeric_cols and 'Date' not in col]
            for col in text_cols:
                agg_dict[col] = 'first'
            
            # Group and aggregate
            result = data.groupby(groupby_cols).agg(agg_dict).reset_index()
            return result
            
        except Exception as e:
            print(f"Error aggregating data: {e}")
            # Fallback: return original data
            return data

    def _load_filtered_data(self, sheet_name: str, start_date=None, end_date=None, agency=None) -> pd.DataFrame:
        """Load and filter data from Google Sheets with proper aggregation for date ranges"""
        try:
            # Try to use fallback system first for reliability
            from .google_sheets_fallback import get_sheet_data_with_fallback
            data = get_sheet_data_with_fallback(sheet_name)
            
        except ImportError:
            # Fallback to basic data loading with manual filtering
            data = get_sheet_data(sheet_name)
        
        # Ensure we have a DataFrame
        if not isinstance(data, pd.DataFrame):
            return pd.DataFrame()
            
        # Apply date filtering if possible
        if start_date and end_date and not data.empty:
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
                data = data[(data['Date'] >= pd.to_datetime(start_date)) & 
                           (data['Date'] <= pd.to_datetime(end_date))]
        
        # Apply agency filtering
        if agency and not data.empty:
            agency_col = None
            for col in ['Agency', 'agency', 'Agent Agency', 'Vendor Agency']:
                if col in data.columns:
                    agency_col = col
                    break
            
            if agency_col:
                data = data[data[agency_col] == agency]
        
        # IMPORTANT: Aggregate data if we have a date range (multiple days)
        if start_date and end_date and start_date != end_date and isinstance(data, pd.DataFrame) and not data.empty:
            # Check if we have multiple dates in the result
            if 'Date' in data.columns:
                unique_dates = data['Date'].nunique()
                if unique_dates > 1:
                    # Aggregate across dates
                    if 'Agent Name' in data.columns:
                        # Agent data - group by agent
                        data = self._aggregate_date_range_data(data, ['Agent Name'])
                    elif 'Campaign' in data.columns:
                        # Campaign/vendor data - group by campaign
                        data = self._aggregate_date_range_data(data, ['Campaign'])
                    else:
                        # Agency data - sum everything
                        data = self._aggregate_date_range_data(data, [])
        
        return data
    
    def generate_report(self, report_type: str, **kwargs) -> str:
        """Generate a report of the specified type"""
        if report_type not in self.report_types:
            raise ValueError(f"Unknown report type: {report_type}")
        
        generator_func = self.report_types[report_type]
        return generator_func(**kwargs)
    
    def generate_daily_report(self, **kwargs) -> str:
        """Generate daily performance report"""
        try:
            # Extract parameters
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            agency = kwargs.get('agency')
            user_role = kwargs.get('user_role', 'management')
            include_campaigns = kwargs.get('include_campaigns', True)
            
            # For scheduled reports, use automatic date calculation
            if start_date is None and end_date is None:
                from datetime import date, timedelta
                yesterday = date.today() - timedelta(days=1)
                start_date = end_date = yesterday
            
            # Load data (using correct sheet names) 
            agency_data = self._load_filtered_data('Daily Agency Stats', start_date, end_date, agency)
            agent_data = self._load_filtered_data('Daily Agent Totals', start_date, end_date, agency)
            
            # Load campaign data only if user has permission
            vendor_data = pd.DataFrame()
            if include_campaigns and user_role in ['management', 'admin']:
                vendor_data = self._load_filtered_data('Daily Lead Vendor Totals', start_date, end_date, agency)
            
            # Calculate metrics
            stats = aggregate_agency_stats(agency_data, agent_data, vendor_data)
            top_agents = get_top_performers(agent_data, n=5)
            at_risk_agents = get_at_risk_agents(agent_data)
            
            # Format report date and agency info
            if start_date:
                report_date = start_date.strftime("%Y-%m-%d") if hasattr(start_date, 'strftime') else str(start_date)
            else:
                report_date = datetime.now().strftime("%Y-%m-%d")
            
            agency_info = f" - {agency}" if agency else ""
            date_range = f"{report_date}" if start_date == end_date else f"{start_date} to {end_date}"
            
            # Role-specific report title
            role_suffix = ""
            if user_role == 'agency_owner':
                role_suffix = " (Agency Report)"
            elif user_role == 'management':
                role_suffix = " (Management Report)"
            
            # Format report
            report_html = f"""
            <div style="font-family: Arial, sans-serif;">
                <h1>Daily Performance Report{agency_info}{role_suffix}</h1>
                <p><strong>Date:</strong> {date_range}</p>
                
                <h2>Key Metrics</h2>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ddd; padding: 8px;">Metric</th>
                        <th style="border: 1px solid #ddd; padding: 8px;">Value</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Total Revenue</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${stats['totalRevenue']:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Total Lead Spend</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${stats['totalLeadSpend']:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Total Profit</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${stats['totalProfit']:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Total Leads</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{stats['totalLeads']:,}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Total Sales</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{stats['totalSales']:,}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Average Closing Ratio</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{stats['avgClosingRatio']:.2f}%</td>
                    </tr>
                </table>
                
                <h2>Top Performing Agents</h2>
                {self._format_agent_table(top_agents)}
                
                <h2>At-Risk Agents</h2>
                {self._format_agent_table(at_risk_agents)}
            """
            
            # Add campaign analysis for management/admin users
            if include_campaigns and user_role in ['management', 'admin'] and not vendor_data.empty:
                campaign_performance = get_campaign_performance(vendor_data)
                report_html += f"""
                <h2>Campaign Performance</h2>
                {self._format_campaign_table(campaign_performance)}
                """
            
            report_html += """
            </div>
            """
            
            return report_html
            
        except Exception as e:
            return f"<div>Error generating daily report: {str(e)}</div>"
    
    def generate_weekly_report(self, **kwargs) -> str:
        """Generate weekly aggregated report"""
        try:
            # Extract parameters
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            agency = kwargs.get('agency')
            user_role = kwargs.get('user_role', 'management')
            include_campaigns = kwargs.get('include_campaigns', True)
            
            # For scheduled reports, use automatic date calculation (previous week Sunday-Saturday)
            if start_date is None and end_date is None:
                from datetime import date, timedelta
                today = date.today()
                days_since_sunday = (today.weekday() + 1) % 7  # Monday=0, Sunday=6 -> Sunday=0
                last_sunday = today - timedelta(days=days_since_sunday + 7)  # Previous week's Sunday
                last_saturday = last_sunday + timedelta(days=6)
                start_date, end_date = last_sunday, last_saturday
            
            # Load and aggregate data
            agency_data = self._load_filtered_data('Daily Agency Stats', start_date, end_date, agency)
            agent_data = self._load_filtered_data('Daily Agent Totals', start_date, end_date, agency)
            
            # Load campaign data only if user has permission
            vendor_data = pd.DataFrame()
            if include_campaigns and user_role in ['management', 'admin']:
                vendor_data = self._load_filtered_data('Daily Lead Vendor Totals', start_date, end_date, agency)
            
            # Get weekly summaries (data should already be aggregated by _load_filtered_data)
            if not agency_data.empty and 'Date' in agency_data.columns:
                agency_weekly = get_weekly_summary(agency_data)
            else:
                agency_weekly = agency_data
                
            if not agent_data.empty and 'Date' in agent_data.columns:
                agent_weekly = get_weekly_summary(agent_data)
            else:
                agent_weekly = agent_data
                
            vendor_weekly = pd.DataFrame()
            if not vendor_data.empty and 'Date' in vendor_data.columns:
                vendor_weekly = get_weekly_summary(vendor_data)
            elif not vendor_data.empty:
                vendor_weekly = vendor_data
            
            # Calculate metrics
            stats = aggregate_agency_stats(agency_weekly, agent_weekly, vendor_weekly)
            top_agents = get_top_performers(agent_weekly, n=10)
            
            # Format date range
            if start_date and end_date:
                date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            else:
                date_range = "Previous Week"
            
            agency_info = f" - {agency}" if agency else ""
            
            # Role-specific report title
            role_suffix = ""
            if user_role == 'agency_owner':
                role_suffix = " (Agency Report)"
            elif user_role == 'management':
                role_suffix = " (Management Report)"
            
            # Format report
            report_html = f"""
            <div style="font-family: Arial, sans-serif;">
                <h1>Weekly Aggregated Report{agency_info}{role_suffix}</h1>
                <p><strong>Period:</strong> {date_range}</p>
                
                <h2>Weekly Summary</h2>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ddd; padding: 8px;">Metric</th>
                        <th style="border: 1px solid #ddd; padding: 8px;">Total</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Total Revenue</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${stats['totalRevenue']:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Total Lead Spend</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${stats['totalLeadSpend']:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Total Profit</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">${stats['totalProfit']:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Total Leads</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{stats['totalLeads']:,}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Total Sales</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{stats['totalSales']:,}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;">Average Closing Ratio</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{stats['avgClosingRatio']:.2f}%</td>
                    </tr>
                </table>
                
                <h2>Top Performing Agents (Week)</h2>
                {self._format_agent_table(top_agents)}
            """
            
            # Add campaign analysis for management/admin users
            if include_campaigns and user_role in ['management', 'admin'] and not vendor_weekly.empty:
                campaign_performance = get_campaign_performance(vendor_weekly)
                report_html += f"""
                <h2>Campaign Performance (Week)</h2>
                {self._format_campaign_table(campaign_performance)}
                """
            
            report_html += """
            </div>
            """
            
            return report_html
            
        except Exception as e:
            return f"<div>Error generating weekly report: {str(e)}</div>"
    
    def generate_monthly_report(self, **kwargs) -> str:
        """Generate monthly comprehensive report"""
        try:
            # Extract parameters
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            agency = kwargs.get('agency')
            user_role = kwargs.get('user_role', 'management')
            include_campaigns = kwargs.get('include_campaigns', True)
            
            # For scheduled reports, use automatic date calculation (previous month)
            if start_date is None and end_date is None:
                from datetime import date, timedelta
                today = date.today()
                first_of_this_month = today.replace(day=1)
                last_day_prev_month = first_of_this_month - timedelta(days=1)
                start_date = last_day_prev_month.replace(day=1)
                end_date = last_day_prev_month
            
            # Load filtered data
            agency_data = self._load_filtered_data('Daily Agency Stats', start_date, end_date, agency)
            agent_data = self._load_filtered_data('Daily Agent Totals', start_date, end_date, agency)
            
            # Load campaign data only if user has permission
            vendor_data = pd.DataFrame()
            if include_campaigns and user_role in ['management', 'admin']:
                vendor_data = self._load_filtered_data('Daily Lead Vendor Totals', start_date, end_date, agency)
            
            # Calculate metrics
            stats = aggregate_agency_stats(agency_data, agent_data, vendor_data)
            top_agents = get_top_performers(agent_data, n=15)
            at_risk_agents = get_at_risk_agents(agent_data)
            campaign_performance = get_campaign_performance(vendor_data) if not vendor_data.empty else pd.DataFrame()
            
            # Format report date and agency info
            if start_date and end_date:
                if start_date == end_date:
                    report_period = start_date.strftime("%B %Y") if hasattr(start_date, 'strftime') else str(start_date)
                else:
                    start_str = start_date.strftime("%B %d") if hasattr(start_date, 'strftime') else str(start_date)
                    end_str = end_date.strftime("%B %d, %Y") if hasattr(end_date, 'strftime') else str(end_date)
                    report_period = f"{start_str} - {end_str}"
            else:
                report_period = datetime.now().strftime('%B %Y')
            
            agency_info = f" - {agency}" if agency else ""
            
            # Role-specific report title
            role_suffix = ""
            if user_role == 'agency_owner':
                role_suffix = " (Agency Report)"
            elif user_role == 'management':
                role_suffix = " (Management Report)"
            
            report_html = f"""
            <div style="font-family: Arial, sans-serif;">
                <h1>Monthly Performance Report{agency_info}{role_suffix}</h1>
                <p><strong>Period:</strong> {report_period}</p>
                
                <h2>Executive Summary</h2>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Total Revenue:</strong> ${stats['totalRevenue']:,.2f}</p>
                    <p><strong>Total Profit:</strong> ${stats['totalProfit']:,.2f}</p>
                    <p><strong>Profit Margin:</strong> {(stats['totalProfit']/stats['totalRevenue']*100) if stats['totalRevenue'] > 0 else 0:.1f}%</p>
                    <p><strong>Total Agents:</strong> {stats['totalAgents']} ({stats['atRiskAgents']} at risk)</p>
                    <p><strong>Average ROAS:</strong> {stats['avgROAS']:.2f}</p>
                </div>
                
                <h2>Top Performing Agents</h2>
                {self._format_agent_table(top_agents)}
                
                <h2>Campaign Analysis</h2>
                {self._format_campaign_table(campaign_performance)}
                
                <h2>Areas of Concern</h2>
                {self._format_agent_table(at_risk_agents) if len(at_risk_agents) > 0 else '<p>No agents currently at risk.</p>'}
                
                <h2>Recommendations</h2>
                <ul>
                    <li>Monitor agents with profitability below $200</li>
                    <li>Optimize campaigns with ROAS below 2.0</li>
                    <li>Review lead quality and cost per acquisition</li>
                    <li>Consider additional training for underperforming agents</li>
                </ul>
            </div>
            """
            
            return report_html
            
        except Exception as e:
            return f"<p>Error generating monthly report: {e}</p>"
    
    def generate_agent_performance_report(self, **kwargs) -> str:
        """Generate detailed agent performance analysis"""
        try:
            # Extract parameters
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            agency = kwargs.get('agency')
            
            agent_data = self._load_filtered_data('Daily Agent Totals', start_date, end_date, agency)
            
            if agent_data.empty:
                return "<p>No agent data available.</p>"
            
            processed_agents = calculate_agent_profitability(agent_data)
            top_agents = get_top_performers(agent_data, n=10)
            at_risk_agents = get_at_risk_agents(agent_data)
            
            # Calculate some statistics
            avg_profitability = processed_agents['agentProfitability'].mean() if 'agentProfitability' in processed_agents.columns else 0
            avg_closing_ratio = processed_agents['closingRatio'].mean() if 'closingRatio' in processed_agents.columns else 0
            
            report_html = f"""
            <div style="font-family: Arial, sans-serif;">
                <h1>Agent Performance Analysis</h1>
                <p><strong>Report Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
                
                <h2>Performance Overview</h2>
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Total Agents:</strong> {len(processed_agents)}</p>
                    <p><strong>Average Profitability:</strong> ${avg_profitability:.2f}</p>
                    <p><strong>Average Closing Ratio:</strong> {avg_closing_ratio:.2f}%</p>
                    <p><strong>Agents At Risk:</strong> {len(at_risk_agents)}</p>
                </div>
                
                <h2>Top Performers</h2>
                {self._format_agent_table(top_agents, show_all_columns=True)}
                
                <h2>Agents Requiring Attention</h2>
                {self._format_agent_table(at_risk_agents, show_all_columns=True) if len(at_risk_agents) > 0 else '<p>All agents performing well!</p>'}
            </div>
            """
            
            return report_html
            
        except Exception as e:
            return f"<p>Error generating agent performance report: {e}</p>"
    
    def generate_campaign_analysis_report(self, **kwargs) -> str:
        """Generate detailed campaign analysis"""
        try:
            # Extract parameters
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            agency = kwargs.get('agency')
            user_role = kwargs.get('user_role', 'management')
            
            # Load filtered vendor data
            vendor_data = self._load_filtered_data('Daily Lead Vendor Totals', start_date, end_date, agency)
            
            if vendor_data.empty:
                return "<p>No campaign data available for the selected period.</p>"
            
            campaign_performance = calculate_campaign_roas(vendor_data)
            
            # Sort by different metrics
            by_roas = campaign_performance.sort_values('ROAS', ascending=False) if 'ROAS' in campaign_performance.columns else campaign_performance
            by_profit = campaign_performance.sort_values('profit', ascending=False) if 'profit' in campaign_performance.columns else campaign_performance
            
            # Format report date and agency info
            if start_date and end_date:
                if start_date == end_date:
                    report_period = start_date.strftime("%Y-%m-%d") if hasattr(start_date, 'strftime') else str(start_date)
                else:
                    start_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, 'strftime') else str(start_date)
                    end_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, 'strftime') else str(end_date)
                    report_period = f"{start_str} to {end_str}"
            else:
                report_period = datetime.now().strftime('%Y-%m-%d')
            
            agency_info = f" - {agency}" if agency else ""
            
            # Role-specific report title
            role_suffix = ""
            if user_role == 'agency_owner':
                role_suffix = " (Agency Report)"
            elif user_role == 'management':
                role_suffix = " (Management Report)"
            
            report_html = f"""
            <div style="font-family: Arial, sans-serif;">
                <h1>Campaign Analysis Report{agency_info}{role_suffix}</h1>
                <p><strong>Period:</strong> {report_period}</p>
                
                <h2>Top Campaigns by ROAS</h2>
                {self._format_campaign_table(by_roas.head(10))}
                
                <h2>Top Campaigns by Profit</h2>
                {self._format_campaign_table(by_profit.head(10))}
                
                <h2>Campaign Performance Metrics</h2>
                <p>Review campaigns with ROAS below 2.0 for optimization opportunities.</p>
                <p>Consider increasing budget for high-performing campaigns.</p>
            </div>
            """
            
            return report_html
            
        except Exception as e:
            return f"<p>Error generating campaign analysis report: {e}</p>"
    
    def generate_executive_summary(self, **kwargs) -> str:
        """Generate executive summary report"""
        try:
            # Extract parameters
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            agency = kwargs.get('agency')
            user_role = kwargs.get('user_role', 'management')
            include_campaigns = kwargs.get('include_campaigns', True)
            
            # For scheduled reports, use automatic date calculation
            if start_date is None and end_date is None:
                from datetime import date, timedelta
                yesterday = date.today() - timedelta(days=1)
                start_date = end_date = yesterday
            
            # Load filtered data (same as other reports)
            agency_data = self._load_filtered_data('Daily Agency Stats', start_date, end_date, agency)
            agent_data = self._load_filtered_data('Daily Agent Totals', start_date, end_date, agency)
            
            # Load campaign data only if user has permission
            vendor_data = pd.DataFrame()
            if include_campaigns and user_role in ['management', 'admin']:
                vendor_data = self._load_filtered_data('Daily Lead Vendor Totals', start_date, end_date, agency)
            
            # Calculate comprehensive stats
            stats = aggregate_agency_stats(agency_data, agent_data, vendor_data)
            top_agents = get_top_performers(agent_data, n=5)
            at_risk_count = len(get_at_risk_agents(agent_data))
            
            # Calculate ROI and other key metrics
            roi = ((stats['totalRevenue'] - stats['totalLeadSpend']) / stats['totalLeadSpend'] * 100) if stats['totalLeadSpend'] > 0 else 0
            
            # Format report date and agency info
            if start_date:
                if start_date == end_date:
                    report_period = start_date.strftime("%Y-%m-%d") if hasattr(start_date, 'strftime') else str(start_date)
                else:
                    start_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, 'strftime') else str(start_date)
                    end_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, 'strftime') else str(end_date)
                    report_period = f"{start_str} to {end_str}"
            else:
                report_period = datetime.now().strftime('%Y-%m-%d')
            
            agency_info = f" - {agency}" if agency else ""
            
            # Role-specific report title
            role_suffix = ""
            if user_role == 'agency_owner':
                role_suffix = " (Agency Report)"
            elif user_role == 'management':
                role_suffix = " (Management Report)"
            
            report_html = f"""
            <div style="font-family: Arial, sans-serif;">
                <h1>Executive Summary{agency_info}{role_suffix}</h1>
                <p><strong>Period:</strong> {report_period}</p>
                
                <h2>Key Performance Indicators</h2>
                <div style="display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0;">
                    <div style="background-color: #4caf50; color: white; padding: 20px; border-radius: 8px; text-align: center; min-width: 150px;">
                        <h3 style="margin: 0;">Total Revenue</h3>
                        <p style="margin: 5px 0; font-size: 24px; font-weight: bold;">${stats['totalRevenue']:,.0f}</p>
                    </div>
                    <div style="background-color: #2196f3; color: white; padding: 20px; border-radius: 8px; text-align: center; min-width: 150px;">
                        <h3 style="margin: 0;">Total Profit</h3>
                        <p style="margin: 5px 0; font-size: 24px; font-weight: bold;">${stats['totalProfit']:,.0f}</p>
                    </div>
                    <div style="background-color: #ff9800; color: white; padding: 20px; border-radius: 8px; text-align: center; min-width: 150px;">
                        <h3 style="margin: 0;">ROI</h3>
                        <p style="margin: 5px 0; font-size: 24px; font-weight: bold;">{roi:.1f}%</p>
                    </div>
                    <div style="background-color: #9c27b0; color: white; padding: 20px; border-radius: 8px; text-align: center; min-width: 150px;">
                        <h3 style="margin: 0;">Average ROAS</h3>
                        <p style="margin: 5px 0; font-size: 24px; font-weight: bold;">{stats['avgROAS']:.1f}</p>
                    </div>
                </div>
                
                <h2>Operations Summary</h2>
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Metric</th>
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: right;">Value</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 12px;">Total Leads Generated</td>
                        <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">{stats['totalLeads']:,}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 12px;">Total Sales Closed</td>
                        <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">{stats['totalSales']:,}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 12px;">Average Closing Ratio</td>
                        <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">{stats['avgClosingRatio']:.1f}%</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 12px;">Active Agents</td>
                        <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">{stats['totalAgents']}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 12px;">Agents At Risk</td>
                        <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">{at_risk_count}</td>
                    </tr>
                </table>
                
                <h2>Top 5 Agents</h2>
                {self._format_agent_table(top_agents)}
                
                <h2>Strategic Recommendations</h2>
                <ul style="line-height: 1.6;">
                    <li><strong>Growth:</strong> {"Excellent performance! Consider scaling successful campaigns." if roi > 50 else "Focus on improving lead quality and agent training."}</li>
                    <li><strong>Efficiency:</strong> {"Strong ROAS indicates efficient marketing spend." if stats['avgROAS'] > 3 else "Review campaign performance and optimize underperforming channels."}</li>
                    <li><strong>Risk Management:</strong> {"Monitor at-risk agents and provide additional support." if at_risk_count > 0 else "Agent performance is strong across the board."}</li>
                </ul>
            </div>
            """
            
            return report_html
            
        except Exception as e:
            return f"<p>Error generating executive summary: {e}</p>"
    
    def _format_agent_table(self, agents_df: pd.DataFrame, show_all_columns: bool = False) -> str:
        """Format agent data as HTML table"""
        if agents_df.empty:
            return "<p>No agent data available.</p>"
        
        # Select columns to display
        display_cols = ['agent', 'totalSales', 'revenue', 'agentProfitability', 'closingRatio']
        if show_all_columns:
            display_cols.extend(['paidCalls', 'revenuePerCall'])
        
        # Filter to available columns
        available_cols = [col for col in display_cols if col in agents_df.columns]
        display_data = agents_df[available_cols]
        
        html = '<table style="border-collapse: collapse; width: 100%;">'
        html += '<tr style="background-color: #f2f2f2;">'
        
        # Column headers
        col_names = {
            'agent': 'Agent Name',
            'totalSales': 'Sales',
            'revenue': 'Revenue',
            'agentProfitability': 'Profitability',
            'closingRatio': 'Closing %',
            'paidCalls': 'Paid Calls',
            'revenuePerCall': 'Revenue/Call'
        }
        
        for col in available_cols:
            html += f'<th style="border: 1px solid #ddd; padding: 8px;">{col_names.get(col, col)}</th>'
        html += '</tr>'
        
        # Data rows
        for _, row in display_data.head(10).iterrows():
            html += '<tr>'
            for col in available_cols:
                value = row[col]
                if col in ['revenue', 'agentProfitability', 'revenuePerCall']:
                    formatted_value = f"${value:,.2f}"
                elif col == 'closingRatio':
                    formatted_value = f"{value:.1f}%"
                elif col in ['totalSales', 'paidCalls']:
                    formatted_value = f"{int(value):,}"
                else:
                    formatted_value = str(value)
                
                html += f'<td style="border: 1px solid #ddd; padding: 8px;">{formatted_value}</td>'
            html += '</tr>'
        
        html += '</table>'
        return html
    
    def _format_campaign_table(self, campaigns_df: pd.DataFrame) -> str:
        """Format campaign data as HTML table"""
        if campaigns_df.empty:
            return "<p>No campaign data available.</p>"
        
        # Select columns to display
        display_cols = ['vendor', 'leads', 'sales', 'revenue', 'leadSpend', 'ROAS', 'profit']
        available_cols = [col for col in display_cols if col in campaigns_df.columns]
        display_data = campaigns_df[available_cols]
        
        html = '<table style="border-collapse: collapse; width: 100%;">'
        html += '<tr style="background-color: #f2f2f2;">'
        
        # Column headers
        col_names = {
            'vendor': 'Campaign',
            'leads': 'Leads',
            'sales': 'Sales',
            'revenue': 'Revenue',
            'leadSpend': 'Spend',
            'ROAS': 'ROAS',
            'profit': 'Profit'
        }
        
        for col in available_cols:
            html += f'<th style="border: 1px solid #ddd; padding: 8px;">{col_names.get(col, col)}</th>'
        html += '</tr>'
        
        # Data rows
        for _, row in display_data.head(10).iterrows():
            html += '<tr>'
            for col in available_cols:
                value = row[col]
                if col in ['revenue', 'leadSpend', 'profit']:
                    formatted_value = f"${value:,.2f}"
                elif col == 'ROAS':
                    formatted_value = f"{value:.2f}"
                elif col in ['leads', 'sales']:
                    formatted_value = f"{int(value):,}"
                else:
                    formatted_value = str(value)
                
                html += f'<td style="border: 1px solid #ddd; padding: 8px;">{formatted_value}</td>'
            html += '</tr>'
        
        html += '</table>'
        return html

# Global report generator instance
report_generator = ReportGenerator() 