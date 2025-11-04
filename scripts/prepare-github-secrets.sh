#!/bin/bash
# Helper script to prepare GitHub Actions secrets
# Usage: ./scripts/prepare-github-secrets.sh

echo "=== GitHub Actions Secrets Setup Helper ==="
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install jq
    else
        echo "Please install jq: https://stedolan.github.io/jq/download/"
        exit 1
    fi
fi

echo "📋 Your Vercel Configuration:"
if [ -f ".vercel/project.json" ]; then
    echo "  Project ID: $(cat .vercel/project.json | jq -r '.projectId')"
    echo "  Org ID: $(cat .vercel/project.json | jq -r '.orgId')"
else
    echo "  ⚠️  .vercel/project.json not found. Run 'vercel link' first."
fi

echo ""
echo "📝 Required GitHub Secrets:"
echo ""
echo "1. VERCEL_TOKEN"
echo "   → Get from: https://vercel.com/account/tokens"
echo ""
echo "2. VERCEL_ORG_ID"
if [ -f ".vercel/project.json" ]; then
    echo "   → Value: $(cat .vercel/project.json | jq -r '.orgId')"
else
    echo "   → Get from: .vercel/project.json (run 'vercel link')"
fi
echo ""
echo "3. VERCEL_PROJECT_ID"
if [ -f ".vercel/project.json" ]; then
    echo "   → Value: $(cat .vercel/project.json | jq -r '.projectId')"
else
    echo "   → Get from: .vercel/project.json (run 'vercel link')"
fi
echo ""
echo "4. FIREBASE_SERVICE_ACCOUNT"
if [ -f "firebase-service-account.json" ]; then
    echo "   → Copy this single-line JSON:"
    echo ""
    cat firebase-service-account.json | jq -c
    echo ""
    echo "   Or use this command:"
    echo "   cat firebase-service-account.json | jq -c"
else
    echo "   → ⚠️  firebase-service-account.json not found"
    echo "   → Get from: Firebase Console → Project Settings → Service Accounts"
fi

echo ""
echo "🔗 Add secrets at: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
echo ""

