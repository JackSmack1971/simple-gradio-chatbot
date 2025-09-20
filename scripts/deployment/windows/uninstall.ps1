#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Uninstalls Personal AI Chatbot from Windows
.DESCRIPTION
    This script uninstalls the Personal AI Chatbot application from Windows systems.
    It removes application files, data (optional), and registry entries.
.PARAMETER InstallPath
    The installation directory (default: C:\Program Files\PersonalAIChatbot)
.PARAMETER DataPath
    The data directory for application data (default: %APPDATA%\PersonalAIChatbot)
.PARAMETER KeepData
    Keep user data and configuration files
.EXAMPLE
    .\uninstall.ps1
.EXAMPLE
    .\uninstall.ps1 -KeepData
#>

param(
    [string]$InstallPath = "$env:ProgramFiles\PersonalAIChatbot",
    [string]$DataPath = "$env:APPDATA\PersonalAIChatbot",
    [switch]$KeepData
)

# Script configuration
$ErrorActionPreference = "Stop"
$AppName = "Personal AI Chatbot"
$LogFile = "$env:TEMP\personal-ai-chatbot-uninstall.log"

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

# Stop running processes
function Stop-AppProcesses {
    Write-Log "Stopping running application processes..."

    # Find and stop Python processes running the app
    $processes = Get-Process | Where-Object {
        $_.ProcessName -eq "python" -and $_.CommandLine -like "*main.py*"
    }

    foreach ($process in $processes) {
        Write-Log "Stopping process: $($process.Id)"
        Stop-Process -Id $process.Id -Force
    }

    # Wait a moment for processes to terminate
    Start-Sleep -Seconds 2
    Write-Log "✓ Application processes stopped"
}

# Remove application files
function Remove-AppFiles {
    Write-Log "Removing application files..."

    if (Test-Path $InstallPath) {
        Remove-Item $InstallPath -Recurse -Force
        Write-Log "✓ Application files removed from: $InstallPath"
    } else {
        Write-Log "Installation directory not found: $InstallPath"
    }
}

# Remove data files
function Remove-DataFiles {
    if ($KeepData) {
        Write-Log "Keeping user data as requested"
        return
    }

    Write-Log "Removing application data..."

    if (Test-Path $DataPath) {
        # Create backup before removal
        $backupPath = "$DataPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $DataPath $backupPath -Recurse
        Write-Log "✓ Backup created: $backupPath"

        Remove-Item $DataPath -Recurse -Force
        Write-Log "✓ Application data removed from: $DataPath"
        Write-Log "Note: Backup available at: $backupPath"
    } else {
        Write-Log "Data directory not found: $DataPath"
    }
}

# Remove desktop shortcut
function Remove-DesktopShortcut {
    Write-Log "Removing desktop shortcuts..."

    $shortcutPath = "$env:USERPROFILE\Desktop\Personal AI Chatbot.lnk"
    if (Test-Path $shortcutPath) {
        Remove-Item $shortcutPath -Force
        Write-Log "✓ Desktop shortcut removed"
    }

    # Check Start Menu
    $startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Personal AI Chatbot.lnk"
    if (Test-Path $startMenuPath) {
        Remove-Item $startMenuPath -Force
        Write-Log "✓ Start Menu shortcut removed"
    }
}

# Clean registry
function Clear-Registry {
    Write-Log "Cleaning registry entries..."

    # Remove uninstall entry
    $uninstallKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PersonalAIChatbot"
    if (Test-Path $uninstallKey) {
        Remove-Item $uninstallKey -Recurse -Force
        Write-Log "✓ Uninstall registry entry removed"
    }

    # Remove application registry key
    $appKey = "HKCU:\SOFTWARE\PersonalAIChatbot"
    if (Test-Path $appKey) {
        Remove-Item $appKey -Recurse -Force
        Write-Log "✓ Application registry key removed"
    }
}

# Remove Python packages (optional)
function Remove-PythonPackages {
    Write-Log "Would you like to remove Python dependencies? (Recommended: No)"
    $response = Read-Host "Remove Python packages? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Log "Removing Python dependencies..."

        # List of packages to remove
        $packages = @(
            "gradio",
            "openai",
            "python-dotenv",
            "requests",
            "cryptography",
            "keyring",
            "psutil"
        )

        foreach ($package in $packages) {
            try {
                python -m pip uninstall $package -y 2>$null
                Write-Log "✓ Removed package: $package"
            } catch {
                Write-Log "Warning: Could not remove package: $package"
            }
        }
    } else {
        Write-Log "Keeping Python dependencies"
    }
}

# Clean temp files
function Clear-TempFiles {
    Write-Log "Cleaning temporary files..."

    # Remove temp files created during installation
    $tempFiles = @(
        "$env:TEMP\personal-ai-chatbot-install.log",
        "$env:TEMP\python-installer.exe"
    )

    foreach ($file in $tempFiles) {
        if (Test-Path $file) {
            Remove-Item $file -Force
            Write-Log "✓ Removed temp file: $file"
        }
    }
}

# Main uninstallation function
function Uninstall-App {
    try {
        Write-Log "Starting uninstallation of $AppName"
        Write-Log "Install Path: $InstallPath"
        Write-Log "Data Path: $DataPath"
        Write-Log "Keep Data: $KeepData"

        Stop-AppProcesses
        Remove-AppFiles
        Remove-DataFiles
        Remove-DesktopShortcut
        Clear-Registry
        Remove-PythonPackages
        Clear-TempFiles

        Write-Log "Uninstallation completed successfully!"
        Write-Log ""
        if ($KeepData) {
            Write-Log "Note: User data preserved in: $DataPath"
        } else {
            Write-Log "Note: If you need your data, check the backup in $DataPath.backup.*"
        }
        Write-Log "Uninstallation log: $LogFile"

    } catch {
        Write-Log "Uninstallation failed: $($_.Exception.Message)" "ERROR"
        Write-Log "Check the log file for details: $LogFile"
        throw
    }
}

# Confirmation prompt
Write-Host "This will uninstall $AppName from your system."
if (-not $KeepData) {
    Write-Host "Warning: This will also remove all user data and configuration files."
    Write-Host "A backup will be created automatically."
}
Write-Host ""

$response = Read-Host "Continue with uninstallation? (y/N)"
if ($response -ne 'y' -and $response -ne 'Y') {
    Write-Host "Uninstallation cancelled."
    exit 0
}

# Run uninstallation
Uninstall-App