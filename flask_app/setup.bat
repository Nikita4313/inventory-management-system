@echo off
REM ============================================
REM  Flask Inventory Management System - Setup
REM ============================================
setlocal
cd /d "%~dp0"
set PY=..\venv\Scripts\python.exe

echo [1/3] Checking virtual environment...
if not exist "%PY%" (
    echo     Creating virtual environment in ..\venv
    python -m venv ..\venv
    if errorlevel 1 goto :failed
) else (
    echo     Using existing ..\venv
)

echo [2/3] Installing dependencies...
"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto :failed
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo [3/3] Seeding demo data (users, categories, products)...
"%PY%" -m flask --app run.py seed
if errorlevel 1 goto :failed

echo.
echo Done! Start the server with:
echo     %PY% run.py
echo Then open http://127.0.0.1:5000/
echo Demo logins:  admin/admin123  staff/staff123  viewer/viewer123
goto :end

:failed
echo.
echo Setup failed. Please read the error above and try again.

:end
endlocal
pause
