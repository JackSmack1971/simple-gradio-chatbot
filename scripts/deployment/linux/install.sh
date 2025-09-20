#!/bin/bash

# Personal AI Chatbot Linux Installation Script
# This script installs the Personal AI Chatbot on Linux systems

set -e  # Exit on any error

# Configuration
APP_NAME="Personal AI Chatbot"
INSTALL_PATH="/opt/personal-ai-chatbot"
DATA_PATH="$HOME/.local/share/personal-ai-chatbot"
LOG_FILE="/tmp/personal-ai-chatbot-install.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR" "$1"
    echo -e "${RED}Installation failed. Check log: $LOG_FILE${NC}"
    exit 1
}

# Detect Linux distribution
detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif [[ -f /etc/redhat-release ]]; then
        DISTRO="rhel"
        VERSION=$(cat /etc/redhat-release | sed 's/.*release \([0-9]\+\).*/\1/')
    elif [[ -f /etc/debian_version ]]; then
        DISTRO="debian"
        VERSION=$(cat /etc/debian_version)
    else
        DISTRO="unknown"
        VERSION="unknown"
    fi

    log "INFO" "Detected Linux distribution: $DISTRO $VERSION"
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites..."

    # Check if running on Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        error_exit "This script is for Linux only"
    fi

    # Detect distribution
    detect_distro

    # Check for Python
    if ! command -v python3 &> /dev/null; then
        log "WARNING" "Python3 not found. Installing..."
        install_python
    else
        local python_version=$(python3 --version)
        log "INFO" "✓ Python found: $python_version"
    fi

    # Check for pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        log "WARNING" "pip not found. Installing..."
        install_pip
    else
        log "INFO" "✓ pip found"
    fi
}

# Install Python if not present
install_python() {
    log "INFO" "Installing Python 3.9..."

    case $DISTRO in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
            ;;
        fedora|centos|rhel)
            if [[ $DISTRO == "fedora" ]]; then
                sudo dnf install -y python3 python3-pip
            else
                sudo yum install -y python3 python3-pip
            fi
            ;;
        arch)
            sudo pacman -S --noconfirm python python-pip
            ;;
        *)
            error_exit "Unsupported Linux distribution: $DISTRO. Please install Python 3.9 manually."
            ;;
    esac

    log "INFO" "✓ Python installed successfully"
}

# Install pip if not present
install_pip() {
    log "INFO" "Installing pip..."

    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py --user
    rm get-pip.py

    # Add to PATH
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

    log "INFO" "✓ pip installed successfully"
}

# Create directories
create_directories() {
    log "INFO" "Creating application directories..."

    # Create installation directory
    sudo mkdir -p "$INSTALL_PATH" || error_exit "Failed to create installation directory"
    sudo chown "$USER:$(id -gn)" "$INSTALL_PATH" || error_exit "Failed to set ownership"

    # Create data directories
    mkdir -p "$DATA_PATH" || error_exit "Failed to create data directory"
    mkdir -p "$DATA_PATH/config" || error_exit "Failed to create config directory"
    mkdir -p "$DATA_PATH/conversations" || error_exit "Failed to create conversations directory"
    mkdir -p "$DATA_PATH/backups" || error_exit "Failed to create backups directory"
    mkdir -p "$DATA_PATH/logs" || error_exit "Failed to create logs directory"

    log "INFO" "✓ Application directories created"
}

# Install dependencies
install_dependencies() {
    log "INFO" "Installing Python dependencies..."

    # Upgrade pip
    python3 -m pip install --upgrade pip

    # Find requirements.txt
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="$(cd "$script_dir/../../../.." && pwd)"
    local requirements_file="$project_root/requirements.txt"

    if [[ -f "$requirements_file" ]]; then
        python3 -m pip install -r "$requirements_file"
        log "INFO" "✓ Python dependencies installed from requirements.txt"
    else
        log "WARNING" "requirements.txt not found, installing basic dependencies"
        python3 -m pip install gradio openai python-dotenv requests cryptography
    fi
}

# Copy application files
copy_app_files() {
    log "INFO" "Copying application files..."

    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="$(cd "$script_dir/../../../.." && pwd)"

    # Copy source files
    if [[ -d "$project_root/src" ]]; then
        cp -r "$project_root/src" "$INSTALL_PATH/"
        log "INFO" "✓ Source files copied"
    fi

    # Copy requirements.txt
    if [[ -f "$project_root/requirements.txt" ]]; then
        cp "$project_root/requirements.txt" "$INSTALL_PATH/"
    fi

    # Copy README
    if [[ -f "$project_root/README.md" ]]; then
        cp "$project_root/README.md" "$INSTALL_PATH/"
    fi
}

# Create configuration
create_configuration() {
    log "INFO" "Creating application configuration..."

    # Create config.json
    cat > "$DATA_PATH/config/app_config.json" << EOF
{
    "app": {
        "name": "Personal AI Chatbot",
        "version": "1.0.0",
        "port": 7860,
        "host": "127.0.0.1",
        "debug": false
    },
    "data": {
        "data_dir": "$DATA_PATH",
        "config_dir": "$DATA_PATH/config",
        "conversations_dir": "$DATA_PATH/conversations",
        "backups_dir": "$DATA_PATH/backups",
        "logs_dir": "$DATA_PATH/logs"
    },
    "security": {
        "max_memory_mb": 500,
        "max_requests_per_minute": 50,
        "request_timeout_seconds": 30,
        "log_level": "INFO"
    }
}
EOF

    log "INFO" "✓ Configuration file created"

    # Create .env template
    cat > "$DATA_PATH/.env.template" << EOF
# Personal AI Chatbot Environment Configuration
# Copy this file to .env and configure your settings

# OpenRouter API Configuration
OPENROUTER_API_KEY=your-api-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Application Configuration
APP_PORT=7860
APP_HOST=127.0.0.1
APP_DEBUG=false

# Data Storage Configuration
DATA_DIR=$DATA_PATH
CONFIG_FILE=$DATA_PATH/config/app_config.json
LOG_LEVEL=INFO

# Security Configuration
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-32-char-encryption-key

# Performance Configuration
MAX_MEMORY_MB=500
MAX_REQUESTS_PER_MINUTE=50
REQUEST_TIMEOUT_SECONDS=30
EOF

    log "INFO" "✓ Environment template created"
}

# Create startup scripts
create_startup_scripts() {
    log "INFO" "Creating startup scripts..."

    # Create run.sh
    cat > "$INSTALL_PATH/run.sh" << 'EOF'
#!/bin/bash
# Personal AI Chatbot Linux Startup Script

echo "Starting Personal AI Chatbot..."
echo

# Set default paths
INSTALL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_PATH="$HOME/.local/share/personal-ai-chatbot"

# Change to installation directory
cd "$INSTALL_PATH"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found"
    exit 1
fi

# Load environment variables
if [[ -f "$DATA_PATH/.env" ]]; then
    echo "Loading environment configuration..."
    set -a
    source "$DATA_PATH/.env"
    set +a
else
    echo "Warning: .env file not found in $DATA_PATH"
    echo "Please create .env file with your configuration"
fi

# Start the application
echo "Launching Personal AI Chatbot..."
python3 src/main.py
EOF

    chmod +x "$INSTALL_PATH/run.sh"
    log "INFO" "✓ Startup script created"

    # Create desktop entry
    mkdir -p "$HOME/.local/share/applications"
    cat > "$HOME/.local/share/applications/personal-ai-chatbot.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Personal AI Chatbot
Comment=Personal AI Chatbot Application
Exec=$INSTALL_PATH/run.sh
Icon=applications-system
Terminal=false
Categories=Utility;Development;
EOF

    log "INFO" "✓ Desktop entry created"
}

# Set permissions
set_permissions() {
    log "INFO" "Setting file permissions..."

    # Set restrictive permissions on data directory
    chmod 700 "$DATA_PATH"
    chmod 700 "$DATA_PATH/config"
    chmod 700 "$DATA_PATH/conversations"
    chmod 700 "$DATA_PATH/backups"
    chmod 700 "$DATA_PATH/logs"

    # Set restrictive permissions on config files
    if [[ -f "$DATA_PATH/config/app_config.json" ]]; then
        chmod 600 "$DATA_PATH/config/app_config.json"
    fi

    if [[ -f "$DATA_PATH/.env" ]]; then
        chmod 600 "$DATA_PATH/.env"
    fi

    # Make scripts executable
    find "$INSTALL_PATH" -name "*.sh" -exec chmod +x {} \;

    log "INFO" "✓ File permissions configured"
}

# Setup systemd service (optional)
setup_systemd_service() {
    log "INFO" "Setting up systemd service..."

    # Check if systemd is available
    if ! command -v systemctl &> /dev/null; then
        log "WARNING" "systemd not available, skipping service setup"
        return
    fi

    # Create systemd service file
    sudo tee /etc/systemd/system/personal-ai-chatbot.service > /dev/null << EOF
[Unit]
Description=Personal AI Chatbot
After=network.target

[Service]
Type=simple
User=$USER
Environment=PATH=/usr/local/bin:/usr/bin:/bin
ExecStart=$INSTALL_PATH/run.sh
WorkingDirectory=$INSTALL_PATH
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable personal-ai-chatbot

    log "INFO" "✓ systemd service created and enabled"
}

# Main installation function
main() {
    log "INFO" "Starting installation of $APP_NAME"
    log "INFO" "Install Path: $INSTALL_PATH"
    log "INFO" "Data Path: $DATA_PATH"

    check_prerequisites
    create_directories
    install_dependencies
    copy_app_files
    create_configuration
    create_startup_scripts
    set_permissions
    setup_systemd_service

    log "INFO" "Installation completed successfully!"
    echo
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo
    echo "Next steps:"
    echo "1. Copy $DATA_PATH/.env.template to $DATA_PATH/.env"
    echo "2. Edit $DATA_PATH/.env with your OpenRouter API key"
    echo "3. Run the application: $INSTALL_PATH/run.sh"
    echo "4. Or start the systemd service: sudo systemctl start personal-ai-chatbot"
    echo
    echo "Installation log: $LOG_FILE"
}

# Run installation with error handling
trap 'error_exit "Installation interrupted"' INT TERM

main "$@"