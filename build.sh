#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting Statsig Slack Bot setup..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
python3 -m pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
python3 -m pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ Warning: .env file not found. Make sure you have set up your environment variables."
    echo "Required environment variables:"
    echo "- SLACK_BOT_TOKEN"
    echo "- SLACK_APP_TOKEN"
fi

# Run the bot
echo "🤖 Starting Statsig Slack Bot..."
python3 statsig_slack_bot.py 