#!/bin/bash
# Full stack development startup script for Claude Nexus
# Runs both backend and frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "=================================="
echo "Claude Nexus Full Stack Dev"
echo "=================================="
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

# Check Node version
NODE_VERSION=$(node --version 2>&1 || echo "not installed")
echo "Node version: $NODE_VERSION"
echo ""

# Create virtual environment if needed
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
fi

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -q -r "$BACKEND_DIR/requirements.txt"

# Initialize data directory if needed
if [ ! -f "$PROJECT_DIR/data/core/identity.json" ]; then
    echo "Initializing data directory..."
    python "$SCRIPT_DIR/init_data.py"
fi

# Install frontend dependencies if needed
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd "$FRONTEND_DIR"
    npm install
    cd "$PROJECT_DIR"
fi

echo ""
echo "Starting services..."
echo ""

# Start backend
echo "Starting backend server..."
cd "$BACKEND_DIR"
python main.py &
BACKEND_PID=$!
cd "$PROJECT_DIR"

# Wait for backend to start
sleep 2

# Start frontend
echo "Starting frontend server..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!
cd "$PROJECT_DIR"

echo ""
echo "=================================="
echo "Services running:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "=================================="
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
