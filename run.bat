@echo off
REM ============================================
REM AI Desktop Automation Agent - Quick Start
REM ============================================
REM This script installs dependencies and runs the agent
REM Use run_hidden.vbs for running without console window

echo ============================================
echo AI Desktop Automation Agent v2.0
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check for --install flag
if "%1"=="--install" goto :install
if "%1"=="-i" goto :install
goto :run

:install
echo [1/2] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies may not have installed correctly
    echo Trying minimal installation...
    pip install pyautogui keyboard opencv-python numpy pillow
)
echo.
echo Dependencies installed!
echo.

:run
echo [Starting Agent]
echo.
echo ============================================
echo Controls:
echo   F8  = Stop agent gracefully
echo   F9  = Emergency stop (immediate)
echo   F10 = Pause / Resume
echo ============================================
echo.

REM Run with arguments passed through
python main.py %*

echo.
echo Agent stopped.
pause
