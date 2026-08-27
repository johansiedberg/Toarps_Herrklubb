#!/usr/bin/env bash
# ==============================================================================
# DEV -> PRD One-Touch Release & Deployment Script (create_release.sh)
# Run on DEV device (or instruct AI agent) to cut release and deploy to PRD.
# ==============================================================================

set -e

PROJECT_DIR="${1:-$(pwd)}"
cd "$PROJECT_DIR"

if [[ ! -d ".git" ]]; then
    echo "❌ Error: $PROJECT_DIR is not a valid Git repository."
    exit 1
fi

PROJECT_NAME=$(basename "$PROJECT_DIR")
MANIFEST_FILE="release_manifest.json"
CHANGELOG_FILE="CHANGELOG.md"

SERVER_USER="johansiedberg"
SERVER_IP="192.168.86.35"
REMOTE_PATH="/home/johansiedberg/Projects/${PROJECT_NAME}"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
PREV_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")

echo "================================================================="
echo "🏷️  DEV -> PRD Release & Remote Deployer"
echo "Project: $PROJECT_NAME"
echo "Current Branch: $CURRENT_BRANCH"
echo "Latest Existing Tag: $PREV_TAG"
echo "================================================================="

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  Uncommitted local changes detected in $PROJECT_NAME:"
    git status -s
    read -p "Commit changes now? (Y/n): " -r ans
    if [[ ! "$ans" =~ ^[Nn]$ ]]; then
        read -p "Enter commit message (e.g., feat: prepare release): " -r msg
        if [[ -z "$msg" ]]; then msg="chore: prepare release"; fi
        git add .
        git commit -m "$msg"
    else
        echo "❌ Release cancelled. Please commit or stash changes."
        exit 1
    fi
fi

# Determine target version tag
read -p "Enter release version tag (e.g. v2.6.0 or press Enter for current $PREV_TAG): " -r NEW_TAG

if [[ -z "$NEW_TAG" ]]; then
    NEW_TAG="$PREV_TAG"
    echo "📌 Keeping current version tag: $NEW_TAG"
else
    if [[ "$NEW_TAG" != v* ]]; then
        NEW_TAG="v${NEW_TAG}"
    fi
fi

RELEASE_DATE=$(date -u +"%Y-%m-%d")
COMMIT_HASH=$(git rev-parse --short HEAD)

# Update release_manifest.json
if [[ -f "$MANIFEST_FILE" ]]; then
    echo "📝 Updating $MANIFEST_FILE..."
    python3 -c "
import json
with open('$MANIFEST_FILE', 'r') as f:
    data = json.load(f)
data['version'] = '$NEW_TAG'.lstrip('v')
data['tag'] = '$NEW_TAG'
data['release_date'] = '$RELEASE_DATE'
data['commit_hash'] = '$COMMIT_HASH'
with open('$MANIFEST_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
    git add "$MANIFEST_FILE"
fi

# Update CHANGELOG.md & commit release bump
if [[ -f "$CHANGELOG_FILE" && "$NEW_TAG" != "$PREV_TAG" ]]; then
    echo "📝 Updating $CHANGELOG_FILE..."
    git commit -m "chore(release): bump version to $NEW_TAG" --allow-empty || true
fi

# Create Git Tag
if [[ "$NEW_TAG" != "$PREV_TAG" ]]; then
    echo "🏷️  Cutting Git Release Tag: $NEW_TAG..."
    git tag -a "$NEW_TAG" -m "Release $NEW_TAG - $RELEASE_DATE"
else
    echo "ℹ️  Re-using tag: $NEW_TAG"
fi

# Push to GitHub
echo "🚀 Pushing commits and release tags to GitHub..."
git push origin "$CURRENT_BRANCH"
git push origin --tags

echo "================================================================="
echo "✅ Release $NEW_TAG published to GitHub!"
echo "================================================================="

# Ask/Execute Remote PRD Deployment via SSH
read -p "🚀 Deploy release $NEW_TAG to PRD server ($SERVER_IP) now? (Y/n): " -r deploy_ans

if [[ ! "$deploy_ans" =~ ^[Nn]$ ]]; then
    echo "🌐 Connecting to PRD server ($SERVER_IP) to execute deployment..."
    ssh -t "${SERVER_USER}@${SERVER_IP}" "cd ${REMOTE_PATH} && ./deploy.sh ${NEW_TAG}"
    echo "================================================================="
    echo "🎉 Release $NEW_TAG successfully deployed to PRD!"
    echo "================================================================="
else
    echo "ℹ️  Remote deployment skipped. You can deploy later on PRD via:"
    echo "   ./deploy.sh $NEW_TAG"
fi
