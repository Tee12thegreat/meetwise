#!/usr/bin/env bash
set -e

echo ""
echo "  ███╗   ███╗███████╗███████╗████████╗██╗    ██╗██╗███████╗███████╗"
echo "  ████╗ ████║██╔════╝██╔════╝╚══██╔══╝██║    ██║██║██╔════╝██╔════╝"
echo "  ██╔████╔██║█████╗  █████╗     ██║   ██║ █╗ ██║██║███████╗█████╗  "
echo "  ██║╚██╔╝██║██╔══╝  ██╔══╝     ██║   ██║███╗██║██║╚════██║██╔══╝  "
echo "  ██║ ╚═╝ ██║███████╗███████╗   ██║   ╚███╔███╔╝██║███████║███████╗"
echo "  ╚═╝     ╚═╝╚══════╝╚══════╝   ╚═╝    ╚══╝╚══╝ ╚═╝╚══════╝╚══════╝"
echo ""
echo "  Smart Meeting Scheduler & Minutes Platform"
echo "  ─────────────────────────────────────────"
echo ""

# Install dependencies
echo "▸ Installing dependencies..."
pip install -r requirements.txt -q

# Migrate
echo "▸ Running migrations..."
python manage.py migrate --run-syncdb -q 2>/dev/null || python manage.py migrate -q

# Seed demo data
echo "▸ Seeding demo data..."
python manage.py seed_demo

echo ""
echo "  ─────────────────────────────────────────"
echo "  ✓ Setup complete. Starting server..."
echo ""
echo "  Open: http://127.0.0.1:8000"
echo "  Admin: http://127.0.0.1:8000/admin"
echo "  ─────────────────────────────────────────"
echo ""

python manage.py runserver
