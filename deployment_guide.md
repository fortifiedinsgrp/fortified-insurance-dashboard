# Fortified Insurance Dashboard - Deployment Guide

## Quick Start Summary

Your dashboard is ready for deployment! Here are the key files and what you need to know:

**Essential Files:**
- `requirements.txt` - All Python dependencies
- `app.py` - Main Streamlit application
- `pages/` - Dashboard pages (Dashboard, Reports, System Status)
- `utils/` - Core functionality (Google Sheets, calculations, reports, scheduling)

**Important:** For **automated report scheduling** to work independently, see the "Automated Reports Setup" section below.

## Automated Reports Setup 🤖

**CRITICAL**: The built-in scheduler only works when the Streamlit app is running. For true automation, choose one of these options:

### Option 1: Standalone Scheduler (Recommended) ⭐

Use the included `standalone_scheduler.py` for independent operation:

```bash
# Test the scheduler
python standalone_scheduler.py --test

# Check status
python standalone_scheduler.py --status

# Run once (good for cron jobs)
python standalone_scheduler.py

# Run continuously as daemon
python standalone_scheduler.py --daemon
```

**For Linux/macOS servers**, set up as a system service:

```bash
# Copy service file (update paths first!)
sudo cp scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable scheduler
sudo systemctl start scheduler

# Check status
sudo systemctl status scheduler
```

### Option 2: Cron Jobs (Simple)

Add to your crontab for regular checks:

```bash
# Edit crontab
crontab -e

# Add this line to check every 5 minutes
*/5 * * * * cd /path/to/fortified-insurance-dashboard && python standalone_scheduler.py >> /var/log/insurance-scheduler.log 2>&1

# Add this line for daily check at 8 AM
0 8 * * * cd /path/to/fortified-insurance-dashboard && python standalone_scheduler.py >> /var/log/insurance-scheduler.log 2>&1
```

### Option 3: Cloud Automation

**For Streamlit Cloud/Heroku:**
- Use external services like GitHub Actions, AWS Lambda, or Google Cloud Functions
- Set up webhooks to trigger your reports
- Use cloud cron services (like Google Cloud Scheduler)

**Example GitHub Action** (`.github/workflows/reports.yml`):
```yaml
name: Send Daily Reports
on:
  schedule:
    - cron: '0 8 * * *'  # 8 AM daily
jobs:
  send-reports:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Send reports
      run: python standalone_scheduler.py
```

## Deployment Platforms

### Option 1: Streamlit Community Cloud (Free) ⭐

**Best for**: Quick deployment, simple setup
**Automated Reports**: Use GitHub Actions or external scheduling

1. **Prepare Repository:**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set main file as `app.py`
   - Deploy!

3. **Configure Secrets:**
   - Add Google Sheets credentials in Streamlit secrets
   - Add email settings in secrets

### Option 2: Heroku (Paid but Reliable)

**Best for**: Professional deployment with automated scheduling
**Automated Reports**: Use Heroku Scheduler add-on

1. **Prepare Files:**
   ```bash
   # Create Procfile
   echo "web: streamlit run app.py --server.port \$PORT" > Procfile
   echo "scheduler: python standalone_scheduler.py --daemon" >> Procfile
   
   # Create runtime.txt
   echo "python-3.9.6" > runtime.txt
   ```

2. **Deploy:**
   ```bash
   heroku create your-insurance-dashboard
   heroku buildpacks:add heroku/python
   git push heroku main
   ```

3. **Enable Scheduler:**
   ```bash
   heroku addons:create scheduler:standard
   heroku addons:open scheduler
   ```
   
   Add job: `python standalone_scheduler.py` (run daily)

### Option 3: DigitalOcean App Platform

**Best for**: Balanced cost and features
**Automated Reports**: Use standalone scheduler as background service

1. **Create `app.yaml`:**
   ```yaml
   name: insurance-dashboard
   services:
   - name: web
     source_dir: /
     github:
       repo: your-username/fortified-insurance-dashboard
       branch: main
     run_command: streamlit run app.py --server.port $PORT
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
   - name: scheduler
     source_dir: /
     github:
       repo: your-username/fortified-insurance-dashboard  
       branch: main
     run_command: python standalone_scheduler.py --daemon
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
   ```

### Option 4: AWS EC2 (Full Control)

**Best for**: Enterprise deployment, complete control
**Automated Reports**: Full systemd service support

1. **Launch EC2 Instance** (Ubuntu 20.04 recommended)

2. **Setup Application:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install python3-pip python3-venv nginx -y
   
   # Clone and setup
   git clone https://github.com/your-username/fortified-insurance-dashboard.git
   cd fortified-insurance-dashboard
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Setup Services:**
   ```bash
   # Update paths in scheduler.service
   sudo cp scheduler.service /etc/systemd/system/
   sudo systemctl enable scheduler
   sudo systemctl start scheduler
   
   # Setup Streamlit as service (create streamlit.service)
   sudo systemctl enable streamlit
   sudo systemctl start streamlit
   ```

## Environment Variables & Secrets

For all deployment platforms, configure these secrets:

### Google Sheets Authentication
```
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account",...}
SPREADSHEET_ID=your_spreadsheet_id_here
```

### Email Configuration
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
```

### Application Settings
```
APP_NAME=Fortified Insurance Dashboard
DEFAULT_AGENCY=Your Agency Name
```

## Testing Your Deployment

### Before Going Live:

1. **Test Google Sheets Connection:**
   ```bash
   python -c "from utils.google_sheets import test_connection; test_connection()"
   ```

2. **Test Email Settings:**
   ```bash
   python standalone_scheduler.py --test
   ```

3. **Test Report Generation:**
   ```bash
   python -c "from utils.reports import ReportGenerator; print('✅ Reports working')"
   ```

4. **Test Scheduler:**
   ```bash
   python standalone_scheduler.py --status
   ```

### Post-Deployment Checklist:

- [ ] Dashboard loads correctly
- [ ] Google Sheets data appears
- [ ] Reports can be generated
- [ ] Email settings work
- [ ] Scheduled reports are configured
- [ ] Standalone scheduler is running (if applicable)

## Monitoring & Maintenance

### Check Scheduler Status:
```bash
# For standalone scheduler
python standalone_scheduler.py --status

# For systemd service
sudo systemctl status scheduler

# Check logs
sudo journalctl -u scheduler -f
```

### Update Application:
```bash
git pull origin main
pip install -r requirements.txt
sudo systemctl restart scheduler  # If using systemd
```

## Troubleshooting

### Common Issues:

1. **"No module named 'utils'"**
   - Ensure you're running from the correct directory
   - Check PYTHONPATH

2. **Google Sheets 503 Errors**
   - Normal - fallback cache system handles this
   - Check System Status page for details

3. **Email Not Sending**
   - Verify SMTP settings
   - Check app passwords for Gmail
   - Test with `python standalone_scheduler.py --test`

4. **Reports Not Generated**
   - Check scheduler status
   - Verify report configurations
   - Check logs for errors

### Support:

- **System Status Page**: Built-in diagnostics
- **Logs**: Check application and scheduler logs
- **GitHub Issues**: Report bugs and get help

## Security Considerations

### Production Checklist:

- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS/SSL
- [ ] Restrict database access
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Backup configurations

**Remember**: The standalone scheduler (`standalone_scheduler.py`) is key for automated reports working independently of the web interface! 