@echo off
REM ================================================
REM  Inventory Management System - Quick Setup
REM  Run this script to set up the project
REM ================================================

echo.
echo 📦 Inventory Management System - Setup
echo ========================================
echo.

REM Step 1: Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH!
    echo    Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
python --version
echo ✅ Python found
echo.

REM Step 2: Create virtual environment
echo [2/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)
echo.

REM Step 3: Activate and install dependencies
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo ✅ Dependencies installed
echo.

REM Step 4: Run migrations
echo [4/5] Running database migrations...
python manage.py migrate
echo ✅ Database ready
echo.

REM Step 5: Create superuser prompt
echo [5/5] Setup complete!
echo.
echo ========================================
echo 🎉 Project is ready to run!
echo ========================================
echo.
echo To start the server, run:
echo   venv\Scripts\activate
echo   python manage.py runserver
echo.
echo Then open: http://127.0.0.1:8000/
echo.
echo To create an admin user:
echo   python manage.py createsuperuser
echo.
echo Open this folder in VS Code for the best experience!
echo.
pause
