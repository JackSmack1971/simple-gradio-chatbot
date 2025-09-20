@echo off
REM Personal AI Chatbot Windows Startup Script
REM This script starts the Personal AI Chatbot application

echo Starting Personal AI Chatbot...
echo.

REM Set default paths if not provided
if "%INSTALL_PATH%"=="" set INSTALL_PATH=%~dp0..
if "%DATA_PATH%"=="" set DATA_PATH=%APPDATA%\PersonalAIChatbot

REM Change to installation directory
cd /d "%INSTALL_PATH%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or later from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found, using system Python
)

REM Set environment variables
if exist "%DATA_PATH%\.env" (
    echo Loading environment configuration...
    for /f "tokens=*" %%a in (%DATA_PATH%\.env) do set %%a
) else (
    echo Warning: .env file not found in %DATA_PATH%
    echo Please create .env file with your configuration
    echo You can copy from .env.template
)

REM Start the application
echo Launching Personal AI Chatbot...
python src\main.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo Application exited with error code %errorlevel%
    echo Check the logs in %DATA_PATH%\logs\ for details
) else (
    echo.
    echo Application exited normally
)

echo.
pause