#!/bin/bash
# Quick start script for Diary Generator Web Interface

echo "🚀 Starting Diary Generator Web Interface..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Please install uv first: https://docs.astral.sh/uv/"
    exit 1
fi

# Create necessary directories
mkdir -p output/web_sessions log templates static

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Start the web server
echo ""
echo "✅ Starting web server..."
echo "📍 Open http://localhost:5000 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run python web_app.py

