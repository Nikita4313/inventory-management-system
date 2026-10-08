#!/usr/bin/env bash
# ============================================
#  Flask Inventory Management System - Setup
# ============================================
set -e
cd "$(dirname "$0")"

VENV="../venv"
if [ -x "$VENV/bin/python" ]; then
    PY="$VENV/bin/python"
elif [ -x "$VENV/Scripts/python.exe" ]; then
    PY="$VENV/Scripts/python.exe"
else
    echo "[1/3] Creating virtual environment in $VENV"
    python3 -m venv "$VENV"
    if [ -x "$VENV/bin/python" ]; then
        PY="$VENV/bin/python"
    else
        PY="$VENV/Scripts/python.exe"
    fi
fi

echo "[2/3] Installing dependencies..."
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt

echo "[3/3] Seeding demo data (users, categories, products)..."
"$PY" -m flask --app run.py seed

echo
echo "Done! Start the server with:"
echo "    $PY run.py"
echo "Then open http://127.0.0.1:5000/"
echo "Demo logins:  admin/admin123  staff/staff123  viewer/viewer123"
