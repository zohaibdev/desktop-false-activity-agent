@echo off
REM ============================================
REM AI Desktop Automation Agent - Build Script
REM ============================================
REM Creates a standalone executable using PyInstaller

echo ============================================
echo AI Desktop Automation Agent - Build
echo ============================================
echo.

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

REM Install PyInstaller if needed
echo [1/4] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Install dependencies
echo.
echo [2/4] Installing dependencies...
pip install -r requirements.txt

REM Clean previous builds
echo.
echo [3/4] Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Build executable
echo.
echo [4/4] Building executable...
echo.

REM Build with console (for debugging)
echo Building console version...
pyinstaller --onefile --name "AI-Agent" --icon=NONE ^
    --add-data "templates;templates" ^
    --hidden-import=keyboard ^
    --hidden-import=pyautogui ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=PIL ^
    main.py

REM Build without console (hidden mode)
echo.
echo Building hidden version (no console)...
pyinstaller --onefile --noconsole --name "AI-Agent-Hidden" --icon=NONE ^
    --add-data "templates;templates" ^
    --hidden-import=keyboard ^
    --hidden-import=pyautogui ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=PIL ^
    main.py

echo.
echo ============================================
echo Build complete!
echo ============================================
echo.
echo Executables created in 'dist' folder:
echo   - AI-Agent.exe        (with console)
echo   - AI-Agent-Hidden.exe (without console)
echo.
echo Controls:
echo   F8  = Stop agent
echo   F9  = Emergency stop
echo   F10 = Pause/Resume
echo.

pause
