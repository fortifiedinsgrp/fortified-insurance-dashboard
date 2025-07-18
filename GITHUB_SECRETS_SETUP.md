# GitHub Secrets Setup for Automated Reports

To make your scheduled reports work on GitHub Actions, you need to add these secrets to your GitHub repository:

## How to Add Secrets
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each item below

## Required Secrets

### Google Sheets Access
- **SPREADSHEET_ID**: `1w44fvhU8wT8e4H6emmcw6XISUqvrHSgE1eOfVYMzMTg`

### Google Service Account (copy exactly from your secrets.toml)
- **GCP_TYPE**: `service_account`
- **GCP_PROJECT_ID**: `sales-dashboard-3ecbe`
- **GCP_PRIVATE_KEY_ID**: `188b77a24690068df83380b3723e00e616e8910c`
- **GCP_PRIVATE_KEY**: `-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCy4ykiVVCQZ2Ug
URuJOrIiJADUnZW35B4CxY9ldNLKbQepsvM1jA7nlBSPCNid9aAwvPJUJYCbH6Pe
uG8L0hWEcAaspAfew0tbADwnMC0KcO9CMcLIUY2Zo2IqvVck4bTJgyqiVjcIZjmx
5s5yscTdrMlbFJ0Q06JsqdXlF0qxjyNCSRt4/jQWCE8dqNsDtD++QUUkhKNI32eU
wl24LTJ0XZxNQXFf8bhH2hJgII0VNLLKe6wKjkFRaqHyUHZ1rd1nxwXiWhlLnPXC
Zj8xfkA3Ujqy01koSf3eA3t5lqZWZYgG60kMem+j5ilVLPUDGWOm/XH9fTtbzqe1
ksgILnx/AgMBAAECggEAVPzXbhhaTkDRKqleC7R3LQEt49V6bANUvrxdhDYcb0+d
dGIwaiBAdIVFvy7UuzcXBBDAkHnAv/IoSIgXOeZ1kpYmlZ7YnlzqUDGsYnHg9DTz
dt9tSv5z56pX2TZbUIpq+dH3T2jmfHcUshCVxKfwf+C3SS5h8LybTkTh+hU2x2QN
p5/GzbB/Gj4xM8vo1RErH3yuH+ouCmt1p2oDok2VgOw7JOE6B14o9j5TBFJzg/sj
pm1MpzCOLLo9e05CU23ungFRN29nxK66Asvj6iA+ZQBH8dQuX5Pou0XQFtXUtDN6
7wKyIwU8RpHpDSEj9BKlsRbZAI4dFARmyLRxN1LsAQKBgQDpD/NIG9TWXCMGEr1H
peoiOFu5PT3SA8ZmSoSTa/OiV7+JUzuMbJ7oupfgoGdofU81pSq4pVMKrxFI418P
+wEEZxNA8mosj+bp8NOK9L8pNcmKwRqrd1kog5U/6/tfZ33tkmc7mXeo1vzDUdkK
x7HUUTULNbZpr62eDJ6rKD4+EQKBgQDEfkMG0lB2ofm2m+oGVa7AP1IYsSP5F6JY
OOEWO8VWoslBZ8Rj9X4Wr2bz5dQL8LR9IgUFHjdas6UJr92v3wwTDO/lGHM4V4v1
1kKqUklpk9SeKtjGhgk71sJVGg4omANeLxNvRuFeQEwyc9o4dmrEtuWF5bZDUNHi
4D6fA6/BjwKBgQCCC+VrUiRULHtakzBM/3aC+8GqvlJ1kqetQl1xyWXcK2x0Gx56
P833/M5sh/TLqEh/nZcWCyIoLwHNExpjV2L86usibWHzVaS62yefPOxB+YJpS1Ev
Zlw4sBui3HGajawF2ZCDACJ18uh9sHkUe9NtrpaTl7gehumw7EfJJ557kQKBgQC2
OYobh2wLuQeGbG3KVifsLk0KjS0ZUuvB+W31WpUWVX1jZMJjGUZH738A7cGLGT2p
VqVlK7KWMUf7BdgHxEjEWhkYU2Z3d+laocvNfOaMPQbPcFj9M0zY67/pgHJk/yUQ
cYQKjKdw6xw/JeXYuyklKaEOXgx7vTYIu4IXoimazQKBgDE+aGXAfx6Jj5CCjcOp
MGkbdmfMQtLyVyFqLj24qvyKC3YOw3+84PWyy6Fw1Eqn67u46zS75tRg/3JD7ZBl
NOYdF7sOoOhuVUnCA9N0YpBdkeH4ndVguT0gVhLzwbZHrH1UgG1Y7HJkjUKipEy7
7qK+U5JGM7X1efqZS8X88X7C
-----END PRIVATE KEY-----`
- **GCP_CLIENT_EMAIL**: `sheets-reader@sales-dashboard-3ecbe.iam.gserviceaccount.com`
- **GCP_CLIENT_ID**: `107168258769803414916`
- **GCP_AUTH_URI**: `https://accounts.google.com/o/oauth2/auth`
- **GCP_TOKEN_URI**: `https://oauth2.googleapis.com/token`
- **GCP_AUTH_PROVIDER_X509_CERT_URL**: `https://www.googleapis.com/oauth2/v1/certs`
- **GCP_CLIENT_X509_CERT_URL**: `https://www.googleapis.com/robot/v1/metadata/x509/sheets-reader%40sales-dashboard-3ecbe.iam.gserviceaccount.com`

### Email Settings (Required for sending reports)
- **SMTP_SERVER**: `smtp.gmail.com`
- **SMTP_PORT**: `587`
- **SMTP_USERNAME**: `msinger@fortifiedinsgrp.com`
- **SMTP_PASSWORD**: `[Your 16-character app password from Google]`
- **SENDER_EMAIL**: `msinger@fortifiedinsgrp.com`
- **SENDER_NAME**: `Fortified Insurance Dashboard`

## After Adding Secrets

1. The GitHub Action will run daily at 8 AM UTC
2. You can manually trigger it by going to **Actions** → **Daily Report Scheduler** → **Run workflow**
3. Check the **Actions** tab to see if it runs successfully

## Troubleshooting

If the action fails:
1. Check the **Actions** tab for error logs
2. Verify all secrets are entered correctly
3. Make sure your email app password is generated and valid 