#!/usr/bin/env bash
set -e

echo "==> Installing system dependencies..."
apt-get update -qq && apt-get install -y ffmpeg

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running migrations..."
python manage.py migrate

echo "==> Build complete."
