# GitHub Token Setup for Automated Sync

To enable automatic synchronization between Streamlit and GitHub Actions, you need to set up a GitHub Personal Access Token.

## Step 1: Create GitHub Personal Access Token

1. Go to GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **"Generate new token (classic)"**
3. Set these permissions:
   - ✅ **repo** (Full control of private repositories)
   - ✅ **workflow** (Update GitHub Action workflows)
4. Set expiration to **"No expiration"** or a long period
5. Click **"Generate token"**
6. **Copy the token immediately** (you won't be able to see it again)

## Step 2: Add Token to Streamlit Cloud

1. Go to your Streamlit Cloud app
2. Click **"Settings"** → **"Secrets"**
3. Add this line to your secrets:

```toml
github_token = "ghp_your_token_here"
```

## Step 3: Add Token to GitHub Actions (already configured)

The GitHub Actions workflow will automatically use the built-in `GITHUB_TOKEN` for repository access.

## How It Works

Once configured:

1. **You manage scheduled reports** through the Streamlit interface
2. **Changes are automatically committed** to your GitHub repository  
3. **GitHub Actions picks up changes** and sends reports as scheduled
4. **Everything stays in sync** automatically

## Testing the Setup

In your Streamlit app, go to Reports → Scheduling. If GitHub sync is working, you'll see:
- ✅ "GitHub sync: Connected"
- Changes made in Streamlit will automatically appear in your repository

If there are issues, you'll see error messages explaining what needs to be fixed. 