#!/bin/bash

# MyMCMB AI Command Center Launch Script
# This script makes it easy to start the Streamlit application

set -e

echo "🚀 Starting MyMCMB AI Command Center..."
echo "================================================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please run this script from the MyMCMB-AI-Center directory."
    exit 1
fi

# Check if streamlit is installed
if ! python -c "import streamlit" &> /dev/null; then
    echo "📦 Installing required dependencies..."
    pip install -r requirements.txt
fi

# Check for secrets configuration
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo ""
    echo "⚠️  Configuration Required"
    echo "================================================="
    echo "Before running the app, you need to create a .streamlit/secrets.toml file"
    echo "with your API keys and password. See README.md for instructions."
    echo ""
    echo "Required format:"
    echo 'GEMINI_API_KEY = "your-google-gemini-api-key"'
    echo 'APP_PASSWORD = "your-admin-password"'
    echo ""
    read -p "Would you like to create the secrets file now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p .streamlit
        echo "# MyMCMB AI Command Center Configuration" > .streamlit/secrets.toml
        echo "# Add your API keys and password below" >> .streamlit/secrets.toml
        echo "" >> .streamlit/secrets.toml
        echo 'GEMINI_API_KEY = "your-google-gemini-api-key-here"' >> .streamlit/secrets.toml
        echo 'APP_PASSWORD = "your-admin-password-here"' >> .streamlit/secrets.toml
        echo ""
        echo "✅ Created .streamlit/secrets.toml"
        echo "📝 Please edit this file and add your actual API keys before running the app."
        echo ""
        if command -v code &> /dev/null; then
            read -p "Open in VS Code? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                code .streamlit/secrets.toml
            fi
        fi
        exit 0
    else
        echo "Please create the secrets file manually and run this script again."
        exit 1
    fi
fi

# Start Streamlit
echo "🎯 Configuration found!"
echo "🌐 Starting Streamlit server..."
echo ""
echo "The app will open in your default browser automatically."
echo "If it doesn't open, you can access it at: http://localhost:8501"
echo ""
echo "📋 To stop the server, press Ctrl+C"
echo "================================================="

# Run streamlit with automatic browser opening
streamlit run app.py --browser.serverAddress=localhost --browser.serverPort=8501

echo ""
echo "👋 Thanks for using MyMCMB AI Command Center!"