#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Installs Personal AI Chatbot on Windows
.DESCRIPTION
    This script installs the Personal AI Chatbot application on Windows systems.
    It creates the necessary directories, installs dependencies, and sets up the application.
.PARAMETER InstallPath
    The installation directory (default: C:\Program Files\PersonalAIChatbot)
.PARAMETER DataPath
    The data directory for application data (default: %APPDATA%\PersonalAIChatbot)
.PARAMETER SkipDependencies
    Skip Python and pip dependency installation
.EXAMPLE
    .\install.ps1
.EXAMPLE
    .\install.ps1 -InstallPath "D:\Apps\PersonalAIChatbot" -DataPath "D:\Data\PersonalAIChatbot"
#>

param(
    [string]$InstallPath = "$env:ProgramFiles\PersonalAIChatbot",
    [string]$DataPath = "$env:APPDATA\PersonalAIChatbot",
    [switch]$SkipDependencies
)

# Script configuration
$ErrorActionPreference = "Stop"
$AppName = "Personal AI Chatbot"
$LogFile = "$env:TEMP\personal-ai-chatbot-install.log"

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

# Check prerequisites
function Test-Prerequisites {
    Write-Log "Checking prerequisites..."

    # Check Windows version
    $osInfo = Get-WmiObject -Class Win32_OperatingSystem
    if ([version]$osInfo.Version -lt [version]"10.0") {
        throw "Windows 10 or later is required"
    }
    Write-Log "✓ Windows version check passed"

    # Check if running as administrator
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "This script must be run as Administrator"
    }
    Write-Log "✓ Administrator privileges confirmed"

    # Check for Python
    try {
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -ne 0) { throw "Python not found" }
        Write-Log "✓ Python found: $pythonVersion"
    } catch {
        if (-not $SkipDependencies) {
            Write-Log "Python not found. Installing Python 3.9..."
            # Download and install Python silently
            $pythonUrl = "https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe"
            $pythonInstaller = "$env:TEMP\python-installer.exe"
            Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
            Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
            Remove-Item $pythonInstaller
            Write-Log "✓ Python installed successfully"
        } else {
            throw "Python is required but not found"
        }
    }
}

# Create directories
function New-AppDirectories {
    Write-Log "Creating application directories..."

    # Create installation directory
    if (-not (Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    }
    Write-Log "✓ Created installation directory: $InstallPath"

    # Create data directories
    $dataDirs = @(
        $DataPath,
        "$DataPath\config",
        "$DataPath\conversations",
        "$DataPath\backups",
        "$DataPath\logs"
    )

    foreach ($dir in $dataDirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    Write-Log "✓ Created data directories in: $DataPath"
}

# Install dependencies
function Install-Dependencies {
    if ($SkipDependencies) {
        Write-Log "Skipping dependency installation"
        return
    }

    Write-Log "Installing Python dependencies..."

    # Upgrade pip
    python -m pip install --upgrade pip

    # Install requirements
    $requirementsPath = Join-Path $PSScriptRoot "..\..\requirements.txt"
    if (Test-Path $requirementsPath) {
        python -m pip install -r $requirementsPath
        Write-Log "✓ Python dependencies installed"
    } else {
        Write-Log "Warning: requirements.txt not found, installing basic dependencies"
        python -m pip install gradio openai python-dotenv requests cryptography
    }
}

# Copy application files
function Copy-AppFiles {
    Write-Log "Copying application files..."

    $sourcePath = Split-Path $PSScriptRoot -Parent
    $sourcePath = Split-Path $sourcePath -Parent  # Go up to personal-ai-chatbot root

    # Copy source files
    $srcDest = Join-Path $InstallPath "src"
    if (Test-Path "$sourcePath\src") {
        Copy-Item "$sourcePath\src" $srcDest -Recurse -Force
        Write-Log "✓ Source files copied"
    }

    # Copy requirements.txt
    if (Test-Path "$sourcePath\requirements.txt") {
        Copy-Item "$sourcePath\requirements.txt" $InstallPath
    }

    # Copy README
    if (Test-Path "$sourcePath\README.md") {
        Copy-Item "$sourcePath\README.md" $InstallPath
    }
}

# Create configuration
function New-AppConfiguration {
    Write-Log "Creating application configuration..."

    $configTemplate = @"
{
    "app": {
        "name": "Personal AI Chatbot",
        "version": "1.0.0",
        "port": 7860,
        "host": "127.0.0.1",
        "debug": false
    },
    "data": {
        "data_dir": "$DataPath",
        "config_dir": "$DataPath\\config",
        "conversations_dir": "$DataPath\\conversations",
        "backups_dir": "$DataPath\\backups",
        "logs_dir": "$DataPath\\logs"
    },
    "security": {
        "max_memory_mb": 500,
        "max_requests_per_minute": 50,
        "request_timeout_seconds": 30,
        "log_level": "INFO"
    }
}
"@

    $configPath = "$DataPath\config\app_config.json"
    $configTemplate | Out-File -FilePath $configPath -Encoding UTF8
    Write-Log "✓ Configuration file created: $configPath"

    # Create .env template
    $envTemplate = @"
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
DATA_DIR=$DataPath
CONFIG_FILE=$DataPath\config\app_config.json
LOG_LEVEL=INFO

# Security Configuration
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-32-char-encryption-key

# Performance Configuration
MAX_MEMORY_MB=500
MAX_REQUESTS_PER_MINUTE=50
REQUEST_TIMEOUT_SECONDS=30
"@

    $envPath = "$DataPath\.env.template"
    $envTemplate | Out-File -FilePath $envPath -Encoding UTF8
    Write-Log "✓ Environment template created: $envPath"
}

# Create startup scripts
function New-StartupScripts {
    Write-Log "Creating startup scripts..."

    # Create run.bat
    $runScript = @"
@echo off
echo Starting Personal AI Chatbot...
cd /d "$InstallPath"
python src\main.py
pause
"@

    $runPath = Join-Path $InstallPath "run.bat"
    $runScript | Out-File -FilePath $runPath -Encoding ASCII
    Write-Log "✓ Startup script created: $runPath"

    # Create desktop shortcut
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Personal AI Chatbot.lnk")
    $Shortcut.TargetPath = $runPath
    $Shortcut.WorkingDirectory = $InstallPath
    $Shortcut.Description = "Launch Personal AI Chatbot"
    $Shortcut.Save()
    Write-Log "✓ Desktop shortcut created"
}

# Set permissions
function Set-AppPermissions {
    Write-Log "Setting file permissions..."

    # Set restrictive permissions on data directory
    icacls $DataPath /grant:r "$env:USERNAME:(OI)(CI)F" /T /Q
    icacls $DataPath /remove:g "Everyone" /T /Q
    icacls $DataPath /remove:g "Users" /T /Q

    # Set restrictive permissions on config files
    $configFiles = @(
        "$DataPath\config\app_config.json",
        "$DataPath\.env"
    )

    foreach ($file in $configFiles) {
        if (Test-Path $file) {
            icacls $file /grant:r "$env:USERNAME:F" /Q
            icacls $file /remove:g "Everyone" /Q
            icacls $file /remove:g "Users" /Q
        }
    }

    Write-Log "✓ File permissions configured"
}

# Main installation function
function Install-App {
    try {
        Write-Log "Starting installation of $AppName"
        Write-Log "Install Path: $InstallPath"
        Write-Log "Data Path: $DataPath"

        Test-Prerequisites
        New-AppDirectories
        Install-Dependencies
        Copy-AppFiles
        New-AppConfiguration
        New-StartupScripts
        Set-AppPermissions

        Write-Log "Installation completed successfully!"
        Write-Log ""
        Write-Log "Next steps:"
        Write-Log "1. Copy $DataPath\.env.template to $DataPath\.env"
        Write-Log "2. Edit $DataPath\.env with your OpenRouter API key"
        Write-Log "3. Run the application using the desktop shortcut or run.bat"
        Write-Log ""
        Write-Log "Installation log: $LogFile"

    } catch {
        Write-Log "Installation failed: $($_.Exception.Message)" "ERROR"
        Write-Log "Check the log file for details: $LogFile"
        throw
    }
}

# Run installation
Install-App