# GitHub Actions Secrets Setup Guide

This document explains how to configure the required secrets for GitHub Actions workflows.

## Required Secrets

Add these secrets to your GitHub repository:
- Go to Settings → Secrets and variables → Actions → New repository secret

### 1. VERCEL_TOKEN
- Get from: https://vercel.com/account/tokens
- Click "Create Token"
- Name it (e.g., "github-actions")
- Copy the token and add it as `VERCEL_TOKEN`

### 2. VERCEL_ORG_ID
- Get from: Your Vercel project settings
- Or run: `vercel whoami` locally and check `.vercel/project.json`
- Format: `team_xxxxxxxxxxxxx` or `org_xxxxxxxxxxxxx`
- Current value: `team_r4xaepY0kESqdpmGU2LqyNGJ`

### 3. VERCEL_PROJECT_ID
- Get from: `.vercel/project.json` file
- Or from Vercel dashboard → Project Settings
- Format: `prj_xxxxxxxxxxxxx`
- Current value: `prj_Fs6JQOACwlTjTOIFBQuaGsldTeD5`

### 4. FIREBASE_SERVICE_ACCOUNT
- Get from: `firebase-service-account.json` file
- Copy the ENTIRE JSON content as a single-line string
- Important: Remove all newlines and format as one line
- Example command: `cat firebase-service-account.json | jq -c`

## Quick Setup Commands

```bash
# Get Vercel org and project IDs
cat .vercel/project.json

# Format Firebase service account for GitHub secret
cat firebase-service-account.json | jq -c

# Test Vercel token
vercel whoami
```

## Security Notes

- Never commit `firebase-service-account.json` to the repository
- All secrets are encrypted by GitHub
- Secrets are only available to workflows during execution
- Use environment-specific secrets if needed (production vs development)

