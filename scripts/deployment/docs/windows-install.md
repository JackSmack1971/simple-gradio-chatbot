# Windows Installation Guide - Personal AI Chatbot

This guide provides detailed instructions for installing the Personal AI Chatbot on Windows systems.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10 (64-bit) or Windows 11
- **Processor**: Intel Core i3 or equivalent (2 GHz or faster)
- **Memory**: 4 GB RAM (8 GB recommended)
- **Storage**: 2 GB free disk space
- **Network**: Internet connection for API access

### Supported Versions
- Windows 10 version 1903 or later
- Windows 11 all versions
- Windows Server 2019 or later (for server deployments)

## Prerequisites

### 1. Administrative Privileges
You must have administrator privileges to install the application.

### 2. Python Installation
The installer will automatically install Python 3.9 if not present. However, you can pre-install it manually:

1. Download Python 3.9 from: https://python.org/downloads/
2. Run the installer as Administrator
3. **Important**: Check "Add Python to PATH" during installation
4. **Important**: Select "Install for all users"

### 3. Antivirus Software
Configure your antivirus software to allow the installation and execution of Python applications.

## Installation Methods

### Method 1: Automated Installation (Recommended)

#### Step 1: Download Files
1. Download the deployment package
2. Extract to a temporary directory (e.g., `C:\Temp\personal-ai-chatbot`)

#### Step 2: Run Installation Script
1. Open PowerShell as Administrator:
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. Navigate to the deployment directory:
   ```powershell
   cd C:\Temp\personal-ai-chatbot\scripts\deployment\windows
   ```

3. Run the installation script:
   ```powershell
   .\install.ps1
   ```

4. The script will:
   - Check system requirements
   - Install Python if needed
   - Create necessary directories
   - Install Python dependencies
   - Copy application files
   - Configure the application
   - Create desktop shortcuts

#### Step 3: Configure API Key
1. After installation, the script will prompt you to configure your OpenRouter API key
2. Copy the template file:
   ```
   copy "C:\Users\%USERNAME%\AppData\Roaming\PersonalAIChatbot\.env.template" "C:\Users\%USERNAME%\AppData\Roaming\PersonalAIChatbot\.env"
   ```
3. Edit the `.env` file with your API key:
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
   ```

### Method 2: Manual Installation

#### Step 1: Install Python
1. Download Python 3.9 from https://python.org
2. Run installer as Administrator
3. Ensure "Add Python to PATH" is checked

#### Step 2: Create Directories
```cmd
mkdir "C:\Program Files\PersonalAIChatbot"
mkdir "%APPDATA%\PersonalAIChatbot\config"
mkdir "%APPDATA%\PersonalAIChatbot\conversations"
mkdir "%APPDATA%\PersonalAIChatbot\backups"
mkdir "%APPDATA%\PersonalAIChatbot\logs"
```

#### Step 3: Install Dependencies
```cmd
cd "C:\Program Files\PersonalAIChatbot"
python -m pip install gradio openai python-dotenv requests cryptography
```

#### Step 4: Copy Application Files
Copy the application files to `C:\Program Files\PersonalAIChatbot\`

#### Step 5: Create Configuration
Create `app_config.json` in `%APPDATA%\PersonalAIChatbot\config\`:

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
        "data_dir": "C:\\Users\\%USERNAME%\\AppData\\Roaming\\PersonalAIChatbot",
        "config_dir": "C:\\Users\\%USERNAME%\\AppData\\Roaming\\PersonalAIChatbot\\config",
        "conversations_dir": "C:\\Users\\%USERNAME%\\AppData\\Roaming\\PersonalAIChatbot\\conversations",
        "backups_dir": "C:\\Users\\%USERNAME%\\AppData\\Roaming\\PersonalAIChatbot\\backups",
        "logs_dir": "C:\\Users\\%USERNAME%\\AppData\\Roaming\\PersonalAIChatbot\\logs"
    }
}
```

## Starting the Application

### Method 1: Desktop Shortcut
1. Double-click the "Personal AI Chatbot" shortcut on your desktop
2. The application will start and open in your default web browser

### Method 2: Command Line
```cmd
cd "C:\Program Files\PersonalAIChatbot"
python src\main.py
```

### Method 3: Using the Batch File
```cmd
"C:\Program Files\PersonalAIChatbot\run.bat"
```

## Configuration

### Environment Variables
Create or edit `%APPDATA%\PersonalAIChatbot\.env`:

```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Application Configuration
APP_PORT=7860
APP_HOST=127.0.0.1
APP_DEBUG=false

# Data Storage Configuration
DATA_DIR=%APPDATA%\PersonalAIChatbot
CONFIG_FILE=%APPDATA%\PersonalAIChatbot\config\app_config.json
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
The installation script automatically configures Windows Firewall. If you need to manually configure:

1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Click "Inbound Rules" → "New Rule"
4. Select "Port" → TCP → Specific local ports: 7860
5. Allow the connection
6. Name it "Personal AI Chatbot"

## Security Hardening

### File Permissions
The installation script automatically sets secure file permissions. To manually verify:

```powershell
# Check permissions on data directory
icacls "%APPDATA%\PersonalAIChatbot"

# Should show restrictive permissions for the user only
```

### Secure API Key Storage
- API keys are stored encrypted in the configuration
- The `.env` file should have restrictive permissions (600)
- Never commit API keys to version control

## Troubleshooting

### Installation Issues

#### "Execution Policy" Error
```powershell
# Run PowerShell as Administrator and execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```

#### Python Not Found
- Ensure Python is installed and added to PATH
- Try: `python --version`
- If not found, reinstall Python with "Add to PATH" option

#### Permission Denied
- Run PowerShell/Command Prompt as Administrator
- Check antivirus software is not blocking the installation

### Runtime Issues

#### Application Won't Start
1. Check Python installation: `python --version`
2. Verify dependencies: `python -m pip list | findstr gradio`
3. Check logs: `type "%APPDATA%\PersonalAIChatbot\logs\app.log"`

#### Port Already in Use
```cmd
# Find what's using port 7860
netstat -ano | findstr :7860

# Kill the process (replace XXXX with actual PID)
taskkill /PID XXXX /F
```

#### API Connection Issues
1. Verify internet connection
2. Check API key in `.env` file
3. Test API endpoint: `curl https://openrouter.ai/api/v1/models`

### Performance Issues

#### High Memory Usage
- Check system has sufficient RAM (minimum 4GB)
- Monitor memory usage with Task Manager
- Consider reducing MAX_MEMORY_MB in configuration

#### Slow Response Times
- Check internet connection speed
- Verify API key is valid
- Check system resources with Task Manager

## Uninstallation

### Automated Uninstallation
```powershell
cd C:\Path\To\Deployment\scripts\deployment\windows
.\uninstall.ps1
```

### Manual Uninstallation
1. Stop the application
2. Delete installation directory: `rmdir /s "C:\Program Files\PersonalAIChatbot"`
3. Delete data directory: `rmdir /s "%APPDATA%\PersonalAIChatbot"`
4. Remove desktop shortcut
5. Remove firewall rules if configured manually

## Advanced Configuration

### Custom Installation Paths
```powershell
.\install.ps1 -InstallPath "D:\Apps\PersonalAIChatbot" -DataPath "D:\Data\PersonalAIChatbot"
```

### Virtual Environment
For isolated Python environment:
```cmd
cd "C:\Program Files\PersonalAIChatbot"
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Service Installation
To run as a Windows service (requires additional setup):
1. Install NSSM (Non-Sucking Service Manager)
2. Configure service to run the batch file
3. Start service from Services management console

## Support

### Getting Help
1. Check the troubleshooting section above
2. Review log files in `%APPDATA%\PersonalAIChatbot\logs\`
3. Run validation scripts:
   ```cmd
   python scripts\deployment\validation\validate-config.py
   python scripts\deployment\validation\health-check.py
   ```

### Log Files
- Application logs: `%APPDATA%\PersonalAIChatbot\logs\app.log`
- Installation logs: `%TEMP%\personal-ai-chatbot-install.log`

### Validation Scripts
Run these to verify installation:
```cmd
python scripts\deployment\validation\test-deployment.py
python scripts\deployment\validation\platform-check.py
```

## Next Steps

After successful installation:

1. **Configure API Key**: Set up your OpenRouter API key
2. **Test Application**: Start the application and verify functionality
3. **Configure Security**: Run security hardening scripts if needed
4. **Set Up Backups**: Configure automated backup schedule
5. **Monitor Health**: Set up health monitoring

For additional configuration options, see the main documentation.