#!/usr/bin/env bash
# ==============================================================================
# Toarps Herrklubb - Production Deployment Script
# Target Server: johansiedberg@192.168.86.35
# Path: /home/johansiedberg/Projects/Toarps_Herrklubb
# ==============================================================================

set -e

echo "🚀 [1/4] Pulling latest changes from origin/main..."
git pull origin main

echo "📦 [2/4] Applying database migrations..."
./venv/bin/python manage.py migrate

echo "📁 [3/4] Collecting static assets..."
./venv/bin/python manage.py collectstatic --noinput

echo "🔄 [4/4] Restarting Toarps Herrklubb background service (Port 8981)..."
pkill -f "8981" || true
sleep 1
nohup ./venv/bin/python manage.py runserver 127.0.0.1:8981 > runserver.log 2>&1 &

echo "✅ Deployment complete! Toarps Herrklubb is running on port 8981."
