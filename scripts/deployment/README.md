# Deployment Package

This directory contains the complete deployment package for the Personal AI Chatbot application, including installation scripts, configuration templates, and operational procedures for Windows, macOS, and Linux platforms.

## Directory Structure

```
scripts/deployment/
├── windows/                 # Windows deployment scripts
│   ├── install.ps1         # PowerShell installation script
│   ├── uninstall.ps1       # PowerShell uninstallation script
│   ├── create-msi.ps1      # MSI installer creation script
│   └── run.bat             # Startup batch file
├── macos/                  # macOS deployment scripts
│   ├── install.sh          # Installation script
│   ├── uninstall.sh        # Uninstallation script
│   ├── create-homebrew.sh  # Homebrew formula creation
│   └── run.sh              # Startup script
├── linux/                  # Linux deployment scripts
│   ├── install.sh          # Installation script
│   ├── uninstall.sh        # Uninstallation script
│   ├── systemd/            # Systemd service files
│   │   ├── personal-ai-chatbot.service
│   │   └── install-service.sh
│   └── run.sh              # Startup script
├── config/                 # Configuration management
│   ├── templates/          # Configuration templates
│   │   ├── config.json.template
│   │   ├── .env.template
│   │   └── docker-compose.yml.template
│   ├── security/           # Security hardening scripts
│   │   ├── harden-permissions.sh
│   │   ├── setup-firewall.sh
│   │   └── validate-security.sh
│   └── validation/         # Configuration validation
│       ├── validate-config.py
│       └── pre-flight-check.py
├── backup/                 # Backup and recovery
│   ├── create-backup.sh    # Backup creation script
│   ├── restore-backup.sh   # Backup restoration script
│   ├── disaster-recovery.md # Disaster recovery procedures
│   └── rollback.sh         # Rollback procedures
├── validation/             # Deployment validation
│   ├── test-deployment.py  # Automated deployment tests
│   ├── platform-check.py   # Platform compatibility checks
│   └── health-check.py     # Application health validation
└── docs/                   # Documentation
    ├── windows-install.md  # Windows installation guide
    ├── macos-install.md    # macOS installation guide
    ├── linux-install.md    # Linux installation guide
    ├── troubleshooting.md  # Troubleshooting guide
    └── security-hardening.md # Security hardening procedures
```

## Quick Start

### Windows
```powershell
# Run PowerShell as Administrator
.\scripts\deployment\windows\install.ps1
```

### macOS
```bash
# Make script executable and run
chmod +x scripts/deployment/macos/install.sh
./scripts/deployment/macos/install.sh
```

### Linux
```bash
# Make script executable and run
chmod +x scripts/deployment/linux/install.sh
sudo ./scripts/deployment/linux/install.sh
```

## Security Features

- **Encrypted API key storage** using Fernet encryption
- **File permission hardening** (600 for sensitive files)
- **Input validation** and sanitization
- **Rate limiting** protection
- **Secure logging** with sensitive data redaction
- **Network security** with SSL certificate validation

## Configuration Management

The deployment package includes secure configuration management:

- **Environment variables** for sensitive data (API keys, secrets)
- **Encrypted configuration files** for persistent settings
- **Template-based setup** for easy deployment
- **Validation** of configuration before startup

## Backup and Recovery

- **Automated backups** of conversations and configuration
- **Encrypted backup storage** for sensitive data
- **Point-in-time recovery** capabilities
- **Disaster recovery procedures** documented

## Monitoring and Health Checks

- **Health monitoring** with configurable thresholds
- **Performance metrics** collection
- **Log analysis** and alerting
- **Automated validation** of deployment success

## Platform Compatibility

Tested on:
- **Windows**: 10, 11 (PowerShell 5.1+, .NET Framework 4.8+)
- **macOS**: 11+ (Intel and Apple Silicon)
- **Linux**: Ubuntu 20.04+, CentOS 8+, Fedora 34+

## Support

For deployment issues, see:
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Security Hardening Guide](docs/security-hardening.md)
- Platform-specific installation guides