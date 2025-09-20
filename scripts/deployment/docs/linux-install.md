# Linux Installation Guide - Personal AI Chatbot

This guide provides detailed instructions for installing the Personal AI Chatbot on Linux systems.

## System Requirements

### Minimum Requirements
- **Operating System**: Ubuntu 20.04+, CentOS 8+, Fedora 34+, or equivalent
- **Processor**: 2 GHz dual-core CPU or equivalent
- **Memory**: 4 GB RAM (8 GB recommended)
- **Storage**: 2 GB free disk space
- **Network**: Internet connection for API access

### Supported Distributions
- **Ubuntu**: 20.04 LTS or later
- **Debian**: 11 (Bullseye) or later
- **CentOS/RHEL**: 8 or later
- **Fedora**: 34 or later
- **Arch Linux**: Latest stable
- **Other**: Any systemd-based Linux distribution

## Prerequisites

### 1. System Updates
Update your system before installation:

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get upgrade

# CentOS/RHEL
sudo yum update

# Fedora
sudo dnf update

# Arch Linux
sudo pacman -Syu
```

### 2. Required Packages
Install basic system dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install curl wget python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install curl wget python3 python3-pip

# Fedora
sudo dnf install curl wget python3 python3-pip

# Arch Linux
sudo pacman -S curl wget python python-pip
```

### 3. User Permissions
You should have sudo privileges for installation. The application will run as your regular user.

## Installation Methods

### Method 1: Automated Installation (Recommended)

#### Step 1: Download and Extract
```bash
# Download the deployment package
wget https://example.com/personal-ai-chatbot-deployment.tar.gz
tar -xzf personal-ai-chatbot-deployment.tar.gz
cd personal-ai-chatbot-deployment
```

#### Step 2: Run Installation Script
```bash
# Make script executable
chmod +x scripts/deployment/linux/install.sh

# Run installation
sudo ./scripts/deployment/linux/install.sh
```

The script will automatically:
- Detect your Linux distribution
- Install Python if needed
- Create necessary directories
- Install Python dependencies
- Copy application files
- Configure the application
- Set up systemd service (optional)
- Configure firewall rules

#### Step 3: Configure API Key
After installation:
```bash
# Copy template to actual config
cp ~/.local/share/personal-ai-chatbot/.env.template ~/.local/share/personal-ai-chatbot/.env

# Edit configuration
nano ~/.local/share/personal-ai-chatbot/.env
```

Add your OpenRouter API key:
```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
```

### Method 2: Manual Installation

#### Step 1: Install Python Dependencies
```bash
# Install system packages
sudo apt-get install python3 python3-pip python3-venv curl

# Install Python packages
python3 -m pip install --user gradio openai python-dotenv requests cryptography
```

#### Step 2: Create Directories
```bash
# Application directory
sudo mkdir -p /opt/personal-ai-chatbot

# Data directories
mkdir -p ~/.local/share/personal-ai-chatbot/{config,conversations,backups,logs}
```

#### Step 3: Copy Application Files
```bash
# Copy application to installation directory
sudo cp -r src /opt/personal-ai-chatbot/
sudo cp requirements.txt /opt/personal-ai-chatbot/
sudo cp README.md /opt/personal-ai-chatbot/

# Set permissions
sudo chown -R $USER:$USER /opt/personal-ai-chatbot
```

#### Step 4: Create Configuration
Create `~/.local/share/personal-ai-chatbot/config/app_config.json`:

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
        "data_dir": "/home/$USER/.local/share/personal-ai-chatbot",
        "config_dir": "/home/$USER/.local/share/personal-ai-chatbot/config",
        "conversations_dir": "/home/$USER/.local/share/personal-ai-chatbot/conversations",
        "backups_dir": "/home/$USER/.local/share/personal-ai-chatbot/backups",
        "logs_dir": "/home/$USER/.local/share/personal-ai-chatbot/logs"
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

### Method 1: Direct Execution
```bash
cd /opt/personal-ai-chatbot
python3 src/main.py
```

### Method 2: Using the Run Script
```bash
cd /opt/personal-ai-chatbot
./run.sh
```

### Method 3: Systemd Service (Recommended)
If you chose to install the systemd service during installation:

```bash
# Start service
sudo systemctl start personal-ai-chatbot

# Enable auto-start on boot
sudo systemctl enable personal-ai-chatbot

# Check status
sudo systemctl status personal-ai-chatbot

# View logs
sudo journalctl -u personal-ai-chatbot -f
```

## Configuration

### Environment Variables
Create or edit `~/.local/share/personal-ai-chatbot/.env`:

```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Application Configuration
APP_PORT=7860
APP_HOST=127.0.0.1
APP_DEBUG=false

# Data Storage Configuration
DATA_DIR=/home/$USER/.local/share/personal-ai-chatbot
CONFIG_FILE=/home/$USER/.local/share/personal-ai-chatbot/config/app_config.json
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
The installation script automatically configures the firewall. To manually configure:

#### UFW (Ubuntu/Debian)
```bash
sudo ufw allow 7860/tcp
sudo ufw reload
```

#### firewalld (CentOS/RHEL/Fedora)
```bash
sudo firewall-cmd --permanent --add-port=7860/tcp
sudo firewall-cmd --reload
```

#### iptables (Manual)
```bash
sudo iptables -A INPUT -p tcp --dport 7860 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

## Security Hardening

### File Permissions
The installation script automatically sets secure permissions. To manually verify:

```bash
# Check data directory permissions
ls -la ~/.local/share/personal-ai-chatbot

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

# Install Python if missing
sudo apt-get install python3 python3-pip  # Ubuntu/Debian
sudo yum install python3 python3-pip      # CentOS/RHEL
sudo dnf install python3 python3-pip      # Fedora
```

#### Permission Denied
```bash
# Fix permissions on installation directory
sudo chown -R $USER:$USER /opt/personal-ai-chatbot

# Fix permissions on data directory
chmod 700 ~/.local/share/personal-ai-chatbot
chmod 600 ~/.local/share/personal-ai-chatbot/.env
```

#### Package Installation Fails
```bash
# Update package manager
sudo apt-get update  # Ubuntu/Debian
sudo yum update      # CentOS/RHEL
sudo dnf update      # Fedora

# Clear package cache
sudo apt-get autoclean && sudo apt-get autoremove  # Ubuntu/Debian
```

### Runtime Issues

#### Application Won't Start
```bash
# Check Python dependencies
python3 -m pip list | grep -E "(gradio|openai|requests)"

# Check configuration
python3 scripts/deployment/validation/validate-config.py

# Check logs
tail -f ~/.local/share/personal-ai-chatbot/logs/app.log
```

#### Port Already in Use
```bash
# Find what's using the port
sudo netstat -tlnp | grep :7860

# Or using ss
sudo ss -tlnp | grep :7860

# Kill the process
sudo kill -9 <PID>
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

### Systemd Service Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status personal-ai-chatbot

# View service logs
sudo journalctl -u personal-ai-chatbot -f

# Check service file
sudo systemctl cat personal-ai-chatbot

# Reload systemd and restart
sudo systemctl daemon-reload
sudo systemctl restart personal-ai-chatbot
```

#### Service Fails on Boot
```bash
# Check if service is enabled
sudo systemctl is-enabled personal-ai-chatbot

# Enable service
sudo systemctl enable personal-ai-chatbot

# Check boot logs
sudo journalctl -b | grep personal-ai-chatbot
```

### Performance Issues

#### High Memory Usage
```bash
# Monitor memory usage
top -p $(pgrep -f "python.*main.py")

# Check system memory
free -h

# Adjust configuration
nano ~/.local/share/personal-ai-chatbot/config/app_config.json
# Reduce MAX_MEMORY_MB if needed
```

#### Slow Response Times
```bash
# Check network latency
ping -c 5 openrouter.ai

# Monitor application performance
python3 scripts/deployment/validation/health-check.py --watch 60

# Check system load
uptime
top
```

## Uninstallation

### Automated Uninstallation
```bash
# Run uninstall script
sudo ./scripts/deployment/linux/uninstall.sh
```

### Manual Uninstallation
```bash
# Stop application and service
sudo systemctl stop personal-ai-chatbot
sudo systemctl disable personal-ai-chatbot

# Remove systemd service file
sudo rm /etc/systemd/system/personal-ai-chatbot.service
sudo systemctl daemon-reload

# Remove application files
sudo rm -rf /opt/personal-ai-chatbot

# Remove data files (optional)
rm -rf ~/.local/share/personal-ai-chatbot

# Remove desktop entry
rm ~/.local/share/applications/personal-ai-chatbot.desktop

# Remove firewall rules
sudo ufw delete allow 7860/tcp  # UFW
sudo firewall-cmd --permanent --remove-port=7860/tcp && sudo firewall-cmd --reload  # firewalld
```

## Advanced Configuration

### Custom Installation Paths
```bash
# Set custom paths
export INSTALL_DIR=/custom/path/to/app
export DATA_DIR=/custom/path/to/data

# Run installation
sudo ./scripts/deployment/linux/install.sh
```

### Virtual Environment
For isolated Python environment:
```bash
cd /opt/personal-ai-chatbot
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt

# Update run script to use virtual environment
echo "source venv/bin/activate" >> run.sh
```

### Nginx Reverse Proxy
For production deployments with Nginx:
```bash
# Install Nginx
sudo apt-get install nginx

# Create site configuration
sudo tee /etc/nginx/sites-available/personal-ai-chatbot << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/personal-ai-chatbot /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## Support

### Getting Help
1. Check the troubleshooting section above
2. Review log files: `~/.local/share/personal-ai-chatbot/logs/app.log`
3. Run validation scripts:
   ```bash
   python3 scripts/deployment/validation/validate-config.py
   python3 scripts/deployment/validation/health-check.py
   ```

### Log Files
- Application logs: `~/.local/share/personal-ai-chatbot/logs/app.log`
- Systemd logs: `sudo journalctl -u personal-ai-chatbot`
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
5. **Monitor Health**: Set up health monitoring and alerts

For additional configuration options, see the main documentation.