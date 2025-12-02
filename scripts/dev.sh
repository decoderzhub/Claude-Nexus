#!/bin/bash
# Development startup script for Claude Nexus

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "=================================="
echo "Claude Nexus Development Server"
echo "=================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

# Create virtual environment if needed
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
fi

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -q -r "$BACKEND_DIR/requirements.txt"

# Initialize data directory if needed
if [ ! -f "$PROJECT_DIR/data/core/identity.json" ]; then
    echo "Initializing data directory..."
    python "$SCRIPT_DIR/init_data.py"
fi

# Start the server
echo ""
echo "Starting backend server..."
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "WebSocket: ws://localhost:8000/ws"
echo ""

cd "$BACKEND_DIR"
python main.py
