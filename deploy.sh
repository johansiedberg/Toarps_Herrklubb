#!/usr/bin/env bash
# ==============================================================================
# Toarps Herrklubb - Production Deployment & Release Fetch Script
# Target: Ubuntu PRD Server (johansiedberg@192.168.86.35)
# Path: /home/johansiedberg/Projects/Toarps_Herrklubb
# ==============================================================================

set -e

PROJECT_DIR="/home/johansiedberg/Projects/Toarps_Herrklubb"
HISTORY_FILE="${PROJECT_DIR}/deployment_history.json"

cd "$PROJECT_DIR"

echo "================================================================="
echo "⚽ Production Deployment: Toarps Herrklubb"
echo "================================================================="

# 1. Fetch tags from remote origin
echo "🔍 [1/6] Fetching latest commits and release tags from GitHub..."
git fetch --tags origin

CURRENT_COMMIT=$(git rev-parse --short HEAD)
PREV_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v1.0.0")

# Target tag selection
INPUT_TAG="$1"
if [[ -n "$INPUT_TAG" ]]; then
    TARGET_TAG="$INPUT_TAG"
    echo "📌 Deploying target release tag: $TARGET_TAG"
    git checkout --quiet "$TARGET_TAG"
else
    echo "📌 Deploying latest main branch (origin/main)..."
    git checkout --quiet main
    git reset --hard origin/main
    TARGET_TAG="main"
fi

NEW_COMMIT=$(git rev-parse --short HEAD)
NEW_VERSION="$TARGET_TAG"

echo "-----------------------------------------------------------------"
echo "📜 Change Summary & Commits ($PREV_VERSION -> $NEW_VERSION):"
git log --oneline -n 5 "$CURRENT_COMMIT..$NEW_COMMIT" 2>/dev/null || echo "Locked to release tag: $NEW_VERSION"
echo "-----------------------------------------------------------------"

# 2. Database Migrations
echo "📦 [2/6] Applying Django database migrations..."
./venv/bin/python manage.py migrate --noinput

# 3. Collect Static Assets
echo "📁 [3/6] Collecting static assets..."
./venv/bin/python manage.py collectstatic --noinput

# 4. Reload Production Systemd Service
echo "🔄 [4/6] Restarting Systemd Service (Port: 8981)..."
systemctl --user restart toarps-herrklubb.service

# 5. Service Health Check
echo "🩺 [5/6] Verifying service health..."
sleep 2

APP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8981/ || echo "ERR")

if [[ "$APP_STATUS" =~ ^(200|301|302)$ ]]; then
    echo "  ✅ App Service (Port 8981 / Proxy 1981): Healthy (HTTP $APP_STATUS)"
else
    echo "  ⚠️ App Service (Port 8981): Status $APP_STATUS. Check journalctl --user -u toarps-herrklubb.service"
fi

# 6. Structured Deployment Logging
echo "📝 [6/6] Logging deployment metadata..."
DEPLOY_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

./venv/bin/python -c "
import json, os
history_file = '$HISTORY_FILE'
entry = {
    'timestamp': '$DEPLOY_TIME',
    'deployed_version': '$NEW_VERSION',
    'previous_version': '$PREV_VERSION',
    'commit_hash': '$NEW_COMMIT',
    'app_health': '$APP_STATUS',
    'deployer': 'deploy.sh'
}
history = []
if os.path.exists(history_file):
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except Exception:
        history = []
history.append(entry)
with open(history_file, 'w') as f:
    json.dump(history, f, indent=2)
"

echo "================================================================="
echo "✅ PRD Deployment Complete! Active Release Tag: $NEW_VERSION ($NEW_COMMIT)"
echo "================================================================="
