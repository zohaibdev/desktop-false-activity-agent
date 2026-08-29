@echo off
REM ============================================
REM AI Desktop Automation Agent - Stop Script
REM ============================================
REM Force stops all running instances of the agent

echo Stopping AI Agent...

REM Kill Python processes running main.py or agent.py
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *AI*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq pythonw.exe" >nul 2>&1
taskkill /F /FI "IMAGENAME eq AI-Agent.exe" >nul 2>&1
taskkill /F /FI "IMAGENAME eq AI-Agent-Hidden.exe" >nul 2>&1

echo.
echo Agent stopped.
timeout /t 2 >nul
