# 🏢 Fortified Insurance Dashboard

A comprehensive reporting dashboard for insurance agencies with automated report scheduling and email delivery.

## ✨ Features

- **📊 Real-time Dashboard**: View key metrics, agent performance, and campaign analytics
- **📋 Advanced Reports**: 6 different report types with date/agency filtering
- **📧 Automated Scheduling**: Set up daily, weekly, or monthly automated reports
- **🔧 System Status**: Monitor Google Sheets connectivity and troubleshoot issues
- **🗂️ User Management**: Manage agency users and their notification preferences
- **📱 Responsive Design**: Works on desktop, tablet, and mobile

## 🚀 Quick Start

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/your-username/fortified-insurance-dashboard.git
   cd fortified-insurance-dashboard
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Google Sheets:**
   - Create a Google Cloud project and enable Sheets API
   - Create a service account and download credentials
   - Share your Google Sheet with the service account email

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

### Production Deployment

See [deployment_guide.md](deployment_guide.md) for detailed deployment instructions.

## 📧 Automated Reports

### Built-in Scheduler
When the Streamlit app is running, reports are automatically sent based on your schedule.

### Standalone Scheduler (Recommended)
For true automation independent of the web app:

```bash
# Test configuration
python standalone_scheduler.py --test

# Check status
python standalone_scheduler.py --status

# Run once (good for cron jobs)
python standalone_scheduler.py

# Run continuously
python standalone_scheduler.py --daemon
```

### GitHub Actions (Cloud Deployment)
Automated reports run daily via GitHub Actions when deployed to Streamlit Cloud.

## 📊 Report Types

1. **Daily Performance**: Key metrics and top performers
2. **Weekly Aggregated**: Week-over-week comparisons
3. **Monthly Comprehensive**: Full monthly analysis
4. **Agent Performance**: Individual agent analytics
5. **Campaign Analysis**: Lead source effectiveness
6. **Executive Summary**: High-level overview for management

## 🛠️ Configuration

### Google Sheets Setup
Your spreadsheet should have these sheets:
- `Daily Agency Stats`
- `Daily Agent Totals` 
- `Daily Lead Vendor Totals`

### Email Configuration
Supports SMTP email delivery. Gmail setup:
1. Enable 2-factor authentication
2. Generate an app password
3. Use app password in SMTP settings

### User Management
Add users with different roles:
- `agency_owner`: Full access
- `management`: Reports and analytics
- `admin`: System administration

## 🔧 System Status

The dashboard includes comprehensive monitoring:
- Google Sheets connectivity status
- Automated scheduler status  
- Data cache management
- Error diagnostics and troubleshooting

## 📁 Project Structure

```
fortified-insurance-dashboard/
├── app.py                     # Main Streamlit application
├── standalone_scheduler.py    # Independent report scheduler
├── pages/                     # Dashboard pages
│   ├── 1_📊_Dashboard.py     # Main dashboard
│   ├── 2_📋_Reports.py       # Reports interface
│   └── 3_🔧_System_Status.py # System monitoring
├── utils/                     # Core functionality
│   ├── calculations.py       # Business logic and metrics
│   ├── google_sheets.py      # Google Sheets integration
│   ├── google_sheets_fallback.py # Fallback data system
│   ├── reports.py            # Report generation
│   ├── scheduler.py          # Report scheduling
│   ├── settings.py           # Settings management
│   └── status_info.py        # System status utilities
├── .github/workflows/        # GitHub Actions for automation
├── requirements.txt          # Python dependencies
└── deployment_guide.md       # Detailed deployment instructions
```

## 🧪 Testing

```bash
# Test all components
python -c "from utils.reports import ReportGenerator; print('✅ Reports working')"
python -c "from utils.google_sheets import test_connection; test_connection()"
python standalone_scheduler.py --test
```

## 📈 Data Sources

- **Google Sheets**: Primary data source with automatic fallback
- **Cached Data**: 24-hour TTL cache for reliability
- **Sample Data**: Fallback when Google Sheets unavailable

## 🔒 Security

- Environment variables for sensitive data
- Service account authentication for Google Sheets
- No credentials stored in code
- HTTPS/SSL support for production deployments

## 🆘 Troubleshooting

1. **Google Sheets 503 errors**: Normal - fallback system handles this
2. **Email not sending**: Check SMTP settings and app passwords
3. **Reports not generating**: Verify data access and scheduler status
4. **Module import errors**: Ensure all dependencies installed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

- **System Status Page**: Built-in diagnostics
- **GitHub Issues**: Bug reports and feature requests
- **Email**: support@fortified.com

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Built with ❤️ for Fortified Insurance Solutions 