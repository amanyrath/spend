# GitHub Actions Configuration

This repository uses GitHub Actions for CI/CD. The workflows are configured in `.github/workflows/`.

## Workflows

### 1. CI Pipeline (`.github/workflows/ci.yml`)
- Runs on: Push and Pull Requests to main/master
- Tests: Runs pytest test suite
- Code Quality: Checks formatting with black and flake8

### 2. Deploy to Vercel (`.github/workflows/deploy.yml`)
- Runs on: Push to main/master or manual trigger
- Deploys: Production deployment to Vercel
- Requires: Vercel secrets configured

### 3. Test Firebase Connection (`.github/workflows/test-firebase.yml`)
- Runs on: Manual trigger or daily schedule
- Tests: Firebase/Firestore connectivity
- Validates: Service account configuration

## Setup Instructions

1. **Configure GitHub Secrets**
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add the required secrets (see `.github/GITHUB_ACTIONS_SETUP.md`)

2. **Get Vercel Credentials**
   ```bash
   # Get Vercel token from https://vercel.com/account/tokens
   # Get org and project IDs from .vercel/project.json
   cat .vercel/project.json
   ```

3. **Prepare Firebase Service Account**
   ```bash
   # Format JSON for GitHub secret
   cat firebase-service-account.json | jq -c
   ```

4. **Run Setup Helper**
   ```bash
   ./scripts/prepare-github-secrets.sh
   ```

## Quick Reference

- **VERCEL_TOKEN**: Create at https://vercel.com/account/tokens
- **VERCEL_ORG_ID**: `team_r4xaepY0kESqdpmGU2LqyNGJ` (from `.vercel/project.json`)
- **VERCEL_PROJECT_ID**: `prj_Fs6JQOACwlTjTOIFBQuaGsldTeD5` (from `.vercel/project.json`)
- **FIREBASE_SERVICE_ACCOUNT**: Single-line JSON from `firebase-service-account.json`

## Troubleshooting

- **Workflow fails on Firebase connection**: Check that `FIREBASE_SERVICE_ACCOUNT` secret is properly formatted (single-line JSON)
- **Vercel deployment fails**: Verify `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` are correct
- **Tests fail**: Ensure all dependencies are in `requirements.txt`

