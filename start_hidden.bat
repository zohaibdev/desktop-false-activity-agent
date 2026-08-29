@echo off
REM ============================================
REM AI Desktop Automation Agent - Hidden Mode
REM ============================================
REM Starts the agent without a console window
REM Use F8 to stop, F9 for emergency stop, F10 to pause/resume

cd /d "%~dp0"

REM Check if pythonw exists
where pythonw >nul 2>&1
if errorlevel 1 (
    echo ERROR: pythonw not found. Using alternative method...
    start /B "" pythonw main.py
    goto :end
)

REM Run using VBScript for completely hidden operation
cscript //nologo run_hidden.vbs

:end
echo Agent started in background.
echo.
echo Controls:
echo   F8  = Stop agent
echo   F9  = Emergency stop
echo   F10 = Pause/Resume
echo.
echo This window will close in 3 seconds...
timeout /t 3 >nul
