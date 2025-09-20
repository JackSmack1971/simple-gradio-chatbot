#!/bin/bash

# Personal AI Chatbot Linux Startup Script
# This script starts the Personal AI Chatbot application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Starting Personal AI Chatbot..."
echo

# Set default paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PATH="$(dirname "$SCRIPT_DIR")"
DATA_PATH="$HOME/.local/share/personal-ai-chatbot"

# Change to installation directory
cd "$INSTALL_PATH"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python3 is not installed or not in PATH${NC}"
    echo "Please install Python 3.9 or later"
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
REQUIRED_VERSION="3.9"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo -e "${YELLOW}Warning: Python $PYTHON_VERSION detected. Python $REQUIRED_VERSION or later recommended.${NC}"
fi

# Check if virtual environment exists and activate it
if [[ -f "venv/bin/activate" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [[ -f ".venv/bin/activate" ]]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
else
    echo -e "${YELLOW}Warning: Virtual environment not found, using system Python${NC}"
fi

# Load environment variables
if [[ -f "$DATA_PATH/.env" ]]; then
    echo "Loading environment configuration..."
    set -a
    source "$DATA_PATH/.env"
    set +a
elif [[ -f ".env" ]]; then
    echo "Loading environment configuration (.env in current directory)..."
    set -a
    source ".env"
    set +a
else
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Please create .env file with your OpenRouter API key"
    echo "You can copy from $DATA_PATH/.env.template"
    echo
    echo -e "${YELLOW}Continuing without configuration...${NC}"
fi

# Validate API key if present
if [[ -n "$OPENROUTER_API_KEY" ]]; then
    if [[ "$OPENROUTER_API_KEY" == "your-api-key-here" ]] || [[ ${#OPENROUTER_API_KEY} -lt 20 ]]; then
        echo -e "${YELLOW}Warning: OPENROUTER_API_KEY appears to be a placeholder${NC}"
        echo "Please set a valid OpenRouter API key in your .env file"
    fi
fi

# Set default configuration if not set
export APP_HOST=${APP_HOST:-"127.0.0.1"}
export APP_PORT=${APP_PORT:-7860}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

# Check if port is available
if command -v netstat &> /dev/null; then
    if netstat -tln 2>/dev/null | grep -q ":$APP_PORT "; then
        echo -e "${YELLOW}Warning: Port $APP_PORT is already in use${NC}"
        echo "The application may fail to start or use a different port"
    fi
elif command -v ss &> /dev/null; then
    if ss -tln 2>/dev/null | grep -q ":$APP_PORT "; then
        echo -e "${YELLOW}Warning: Port $APP_PORT is already in use${NC}"
        echo "The application may fail to start or use a different port"
    fi
fi

# Start the application
echo "Launching Personal AI Chatbot..."
echo "Application will be available at: http://$APP_HOST:$APP_PORT"
echo "Press Ctrl+C to stop the application"
echo

# Start with proper error handling
if python3 src/main.py; then
    echo
    echo -e "${GREEN}Application exited normally${NC}"
else
    EXIT_CODE=$?
    echo
    echo -e "${RED}Application exited with error code: $EXIT_CODE${NC}"

    if [[ -d "$DATA_PATH/logs" ]]; then
        echo "Check the logs in $DATA_PATH/logs/ for details"
        # Show recent log entries if available
        if [[ -f "$DATA_PATH/logs/app.log" ]]; then
            echo
            echo "Recent log entries:"
            tail -20 "$DATA_PATH/logs/app.log" 2>/dev/null || true
        fi
    fi

    exit $EXIT_CODE
fi