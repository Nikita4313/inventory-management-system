#!/bin/bash
# ================================================
#  Inventory Management System - Quick Setup
#  Run this script to set up the project
# ================================================

echo ""
echo "📦 Inventory Management System - Setup"
echo "========================================"
echo ""

# Step 1: Check Python
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed!"
    echo "   Please install Python 3.10+ from https://python.org"
    exit 1
fi
python3 --version
echo "✅ Python found"
echo ""

# Step 2: Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Step 3: Activate and install dependencies
echo "[3/5] Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Step 4: Run migrations
echo "[4/5] Running database migrations..."
python manage.py migrate
echo "✅ Database ready"
echo ""

# Step 5: Done
echo "[5/5] Setup complete!"
echo ""
echo "========================================"
echo "🎉 Project is ready to run!"
echo "========================================"
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Then open: http://127.0.0.1:8000/"
echo ""
echo "To create an admin user:"
echo "  python manage.py createsuperuser"
echo ""
echo "Open this folder in VS Code for the best experience!"
