# macOS Installation Guide - Personal AI Chatbot

This guide provides detailed instructions for installing the Personal AI Chatbot on macOS systems.

## System Requirements

### Minimum Requirements
- **Operating System**: macOS 11.0 (Big Sur) or later
- **Processor**: Intel Core i5 or Apple Silicon M1/M2
- **Memory**: 4 GB RAM (8 GB recommended)
- **Storage**: 2 GB free disk space
- **Network**: Internet connection for API access

### Supported Versions
- macOS 11.0 Big Sur or later
- macOS 12.0 Monterey
- macOS 13.0 Ventura
- macOS 14.0 Sonoma

## Prerequisites

### 1. System Updates
Ensure your macOS is up to date:

1. Click the Apple menu ()
2. Select "System Settings" → "General" → "Software Update"
3. Install any available updates

### 2. Xcode Command Line Tools
Install Xcode Command Line Tools (required for some Python packages):

```bash
xcode-select --install
```

### 3. Homebrew (Recommended)
Install Homebrew package manager:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Add Homebrew to your PATH by following the instructions printed after installation.

### 4. Rosetta 2 (Intel Macs only)
If you're on an Intel Mac, install Rosetta 2 for compatibility:

```bash
softwareupdate --install-rosetta
```

## Installation Methods

### Method 1: Automated Installation (Recommended)

#### Step 1: Download Files
1. Download the deployment package
2. Extract to a directory (e.g., `~/Downloads/personal-ai-chatbot`)

#### Step 2: Run Installation Script
1. Open Terminal application
2. Navigate to the deployment directory:
   ```bash
   cd ~/Downloads/personal-ai-chatbot/scripts/deployment/macos
   ```

3. Make the script executable and run it:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

4. The script will:
   - Check system requirements
   - Install Python if needed (via Homebrew)
   - Create necessary directories
   - Install Python dependencies
   - Copy application files
   - Configure the application

#### Step 3: Configure API Key
1. After installation, copy the template file:
   ```bash
   cp ~/Library/Application\ Support/PersonalAIChatbot/.env.template ~/Library/Application\ Support/PersonalAIChatbot/.env
   ```

2. Edit the `.env` file with your API key:
   ```bash
   nano ~/Library/Application\ Support/PersonalAIChatbot/.env
   ```

   Add your OpenRouter API key:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
   ```

### Method 2: Manual Installation

#### Step 1: Install Python
```bash
# Using Homebrew (recommended)
brew install python@3.9
brew link python@3.9

# Or using the official installer from python.org
# Download and install Python 3.9 from https://python.org
```

#### Step 2: Create Directories
```bash
# Application directory
sudo mkdir -p /Applications/PersonalAIChatbot

# Data directories
mkdir -p ~/Library/Application\ Support/PersonalAIChatbot/{config,conversations,backups,logs}
```

#### Step 3: Install Dependencies
```bash
# Install Python packages
python3 -m pip install gradio openai python-dotenv requests cryptography
```

#### Step 4: Copy Application Files
```bash
# Copy application files
sudo cp -r src /Applications/PersonalAIChatbot/
sudo cp requirements.txt /Applications/PersonalAIChatbot/
sudo cp README.md /Applications/PersonalAIChatbot/

# Set permissions
sudo chown -R $USER:staff /Applications/PersonalAIChatbot
```

#### Step 5: Create Configuration
Create `~/Library/Application Support/PersonalAIChatbot/config/app_config.json`:

```json
{
    "app": {
        "name": "Personal AI Chatbot",
        "version": "1.0.0",
        "port": 7860,
        "host": "127.0.0.1",
        "debug": false
    },
    "data": {
        "data_dir": "/Users/$USER/Library/Application Support/PersonalAIChatbot",
        "config_dir": "/Users/$USER/Library/Application Support/PersonalAIChatbot/config",
        "conversations_dir": "/Users/$USER/Library/Application Support/PersonalAIChatbot/conversations",
        "backups_dir": "/Users/$USER/Library/Application Support/PersonalAIChatbot/backups",
        "logs_dir": "/Users/$USER/Library/Application Support/PersonalAIChatbot/logs"
    },
    "security": {
        "max_memory_mb": 500,
        "max_requests_per_minute": 50,
        "request_timeout_seconds": 30,
        "log_level": "INFO"
    }
}
```

## Starting the Application

### Method 1: Using the Run Script
```bash
cd /Applications/PersonalAIChatbot
./run.sh
```

### Method 2: Direct Execution
```bash
cd /Applications/PersonalAIChatbot
python3 src/main.py
```

### Method 3: Creating a Launch Agent (Auto-start)
Create a launch agent for automatic startup:

```bash
# Create launch agent plist
cat > ~/Library/LaunchAgents/com.personal-ai-chatbot.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.personal-ai-chatbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/PersonalAIChatbot/run.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/$USER/Library/Logs/personal-ai-chatbot.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/$USER/Library/Logs/personal-ai-chatbot-error.log</string>
</dict>
</plist>
EOF

# Load the launch agent
launchctl load ~/Library/LaunchAgents/com.personal-ai-chatbot.plist

# Check status
launchctl list | grep personal-ai-chatbot
```

## Configuration

### Environment Variables
Create or edit `~/Library/Application Support/PersonalAIChatbot/.env`:

```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Application Configuration
APP_PORT=7860
APP_HOST=127.0.0.1
APP_DEBUG=false

# Data Storage Configuration
DATA_DIR=/Users/$USER/Library/Application Support/PersonalAIChatbot
CONFIG_FILE=/Users/$USER/Library/Application Support/PersonalAIChatbot/config/app_config.json
LOG_LEVEL=INFO

# Security Configuration
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-32-char-encryption-key

# Performance Configuration
MAX_MEMORY_MB=500
MAX_REQUESTS_PER_MINUTE=50
REQUEST_TIMEOUT_SECONDS=30
```

### Firewall Configuration
macOS automatically configures the firewall for local applications. To manually configure:

1. Open System Settings
2. Go to "Network" → "Firewall"
3. Click "Firewall Options"
4. Ensure "Block all incoming connections" is unchecked (or add exceptions if needed)

## Security Hardening

### File Permissions
The installation script automatically sets secure permissions. To manually verify:

```bash
# Check data directory permissions
ls -la ~/Library/Application\ Support/PersonalAIChatbot

# Should show drwx------ for data directory
# Should show -rw------- for config files
```

### Manual Security Setup
```bash
# Run security hardening scripts
./scripts/deployment/config/security/harden-permissions.sh
./scripts/deployment/config/security/setup-firewall.sh
./scripts/deployment/config/security/validate-security.sh
```

## Troubleshooting

### Installation Issues

#### Python Not Found
```bash
# Check Python installation
python3 --version

# Install via Homebrew
brew install python@3.9
brew link python@3.9

# Add to PATH if needed
echo 'export PATH="/usr/local/opt/python@3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Permission Denied
```bash
# Fix permissions on application directory
sudo chown -R $USER:staff /Applications/PersonalAIChatbot

# Fix permissions on data directory
chmod 700 ~/Library/Application\ Support/PersonalAIChatbot
chmod 600 ~/Library/Application\ Support/PersonalAIChatbot/.env
```

#### Homebrew Issues
```bash
# Update Homebrew
brew update

# Fix common issues
brew doctor
brew cleanup
```

### Runtime Issues

#### Application Won't Start
```bash
# Check Python dependencies
python3 -m pip list | grep -E "(gradio|openai|requests)"

# Check configuration
python3 scripts/deployment/validation/validate-config.py

# Check logs
tail -f ~/Library/Application\ Support/PersonalAIChatbot/logs/app.log
```

#### Port Already in Use
```bash
# Find what's using the port
lsof -i :7860

# Kill the process
kill -9 <PID>
```

#### API Connection Issues
```bash
# Test internet connectivity
ping -c 3 openrouter.ai

# Test API endpoint
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models

# Check API key format
echo $OPENROUTER_API_KEY | head -c 20
```

### Performance Issues

#### High Memory Usage
```bash
# Monitor memory usage
top -pid $(pgrep -f "python.*main.py")

# Check system memory
vm_stat

# Adjust configuration
nano ~/Library/Application\ Support/PersonalAIChatbot/config/app_config.json
# Reduce MAX_MEMORY_MB if needed
```

#### Slow Response Times
```bash
# Check network latency
ping -c 5 openrouter.ai

# Monitor application performance
python3 scripts/deployment/validation/health-check.py --watch 60
```

## Uninstallation

### Automated Uninstallation
```bash
# Run uninstall script
./scripts/deployment/macos/uninstall.sh
```

### Manual Uninstallation
```bash
# Stop application
pkill -f "python.*main.py"

# Remove launch agent if configured
launchctl unload ~/Library/LaunchAgents/com.personal-ai-chatbot.plist
rm ~/Library/LaunchAgents/com.personal-ai-chatbot.plist

# Remove application files
sudo rm -rf /Applications/PersonalAIChatbot

# Remove data files (optional)
rm -rf ~/Library/Application\ Support/PersonalAIChatbot

# Remove logs
rm -f ~/Library/Logs/personal-ai-chatbot*.log
```

## Advanced Configuration

### Custom Installation Paths
```bash
# Set custom paths
export INSTALL_DIR=/custom/path/to/app
export DATA_DIR=/custom/path/to/data

# Run installation
./scripts/deployment/macos/install.sh
```

### Virtual Environment
For isolated Python environment:
```bash
cd /Applications/PersonalAIChatbot
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt

# Update run script to use virtual environment
echo "source venv/bin/activate" >> run.sh
```

### Apple Silicon Optimization
For Apple Silicon Macs, ensure you're using the native Python:

```bash
# Check architecture
uname -m  # Should show 'arm64' for Apple Silicon

# Install native Python
brew install python@3.9

# Ensure you're using the right Python
which python3  # Should point to /opt/homebrew/bin/python3
```

## Integration with macOS

### Spotlight Integration
Create a Spotlight importer for better search integration (advanced):

```bash
# This requires additional development work
# For now, conversations are stored as JSON files
# which Spotlight can index automatically
```

### Notification Center
The application can integrate with macOS Notification Center for alerts.

### Accessibility
For screen reader support and accessibility features, ensure:

1. System Preferences → Accessibility → VoiceOver is enabled if needed
2. The application follows accessibility guidelines

## Support

### Getting Help
1. Check the troubleshooting section above
2. Review log files: `~/Library/Application Support/PersonalAIChatbot/logs/app.log`
3. Run validation scripts:
   ```bash
   python3 scripts/deployment/validation/validate-config.py
   python3 scripts/deployment/validation/health-check.py
   ```

### Log Files
- Application logs: `~/Library/Application Support/PersonalAIChatbot/logs/app.log`
- Launch agent logs: `~/Library/Logs/personal-ai-chatbot.log`
- Installation logs: `/tmp/personal-ai-chatbot-install.log`

### Validation Scripts
Run these to verify installation:
```bash
python3 scripts/deployment/validation/test-deployment.py
python3 scripts/deployment/validation/platform-check.py
```

## Next Steps

After successful installation:

1. **Configure API Key**: Set up your OpenRouter API key in `.env`
2. **Test Application**: Start the application and verify functionality
3. **Configure Security**: Run security hardening scripts
4. **Set Up Backups**: Configure automated backup schedule
5. **Monitor Health**: Set up health monitoring

For additional configuration options, see the main documentation.

## Known Issues and Workarounds

### Apple Silicon Compatibility
- Ensure you're using Python installed via Homebrew for native Apple Silicon support
- Some older packages may require Rosetta 2 for Intel emulation

### Gatekeeper
If you see "App is damaged" errors:
```bash
# Temporarily disable Gatekeeper for testing
sudo spctl --master-disable

# Re-enable after testing
sudo spctl --master-enable
```

### Firewall Blocking
macOS may block the application initially:
1. Go to System Settings → Privacy & Security
2. Allow the application when prompted
3. Or manually allow in Firewall settings