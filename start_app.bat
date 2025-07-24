@echo off
REM MyMCMB AI Command Center Launch Script for Windows
REM This script makes it easy to start the Streamlit application

echo 🚀 Starting MyMCMB AI Command Center...
echo =================================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ app.py not found. Please run this script from the MyMCMB-AI-Center directory.
    pause
    exit /b 1
)

REM Check if streamlit is installed
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing required dependencies...
    pip install -r requirements.txt
)

REM Check for secrets configuration
if not exist ".streamlit\secrets.toml" (
    echo.
    echo ⚠️  Configuration Required
    echo =================================================
    echo Before running the app, you need to create a .streamlit\secrets.toml file
    echo with your API keys and password. See README.md for instructions.
    echo.
    echo Required format:
    echo GEMINI_API_KEY = "your-google-gemini-api-key"
    echo APP_PASSWORD = "your-admin-password"
    echo.
    set /p "create=Would you like to create the secrets file now? (y/n): "
    if /i "%create%"=="y" (
        if not exist ".streamlit" mkdir .streamlit
        echo # MyMCMB AI Command Center Configuration > .streamlit\secrets.toml
        echo # Add your API keys and password below >> .streamlit\secrets.toml
        echo. >> .streamlit\secrets.toml
        echo GEMINI_API_KEY = "your-google-gemini-api-key-here" >> .streamlit\secrets.toml
        echo APP_PASSWORD = "your-admin-password-here" >> .streamlit\secrets.toml
        echo.
        echo ✅ Created .streamlit\secrets.toml
        echo 📝 Please edit this file and add your actual API keys before running the app.
        echo.
        echo Opening the file in notepad...
        notepad .streamlit\secrets.toml
        pause
        exit /b 0
    ) else (
        echo Please create the secrets file manually and run this script again.
        pause
        exit /b 1
    )
)

REM Start Streamlit
echo 🎯 Configuration found!
echo 🌐 Starting Streamlit server...
echo.
echo The app will open in your default browser automatically.
echo If it doesn't open, you can access it at: http://localhost:8501
echo.
echo 📋 To stop the server, press Ctrl+C
echo =================================================

REM Run streamlit with automatic browser opening
streamlit run app.py --browser.serverAddress=localhost --browser.serverPort=8501

echo.
echo 👋 Thanks for using MyMCMB AI Command Center!
pause