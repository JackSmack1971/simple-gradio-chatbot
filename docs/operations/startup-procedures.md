# Application Startup Procedures

## Overview
This runbook provides procedures for safely starting the Personal AI Chatbot application, including validation steps and troubleshooting.

**Risk Level**: 🟢 Medium
**Estimated Time**: 10-15 minutes
**Required Access**: System administrator

## Prerequisites

### System Requirements
- Python 3.8+
- 4GB RAM minimum
- 10GB disk space
- Network connectivity to OpenRouter API

### Access Requirements
- SSH access to server
- Sudo privileges for service management
- Access to application configuration files

### Pre-Startup Checks
```bash
# Check system resources
python scripts/health/health_check.py --check system_resources

# Verify configuration files exist
ls -la config/
ls -la data/

# Check API key configuration
echo $OPENROUTER_API_KEY | head -c 10  # Should show first 10 chars

# Verify network connectivity
ping -c 3 openrouter.ai
```

## Startup Procedure

### 1. Environment Preparation

#### Activate Virtual Environment
```bash
cd /opt/personal-ai-chatbot
source venv/bin/activate
```

#### Verify Dependencies
```bash
# Check Python version
python --version

# Verify key packages
python -c "import gradio, psutil, requests; print('Dependencies OK')"
```

#### Validate Configuration
```bash
# Check configuration files
python -c "
from pathlib import Path
config_files = ['config/app.json', 'config/monitoring.json']
for cf in config_files:
    if Path(cf).exists():
        print(f'✓ {cf} exists')
    else:
        print(f'✗ {cf} missing')
"
```

### 2. Pre-Startup Validation

#### Data Directory Check
```bash
# Ensure data directories exist
mkdir -p data/logs
mkdir -p data/conversations
mkdir -p data/cache
mkdir -p data/backups

# Set proper permissions
chmod 755 data/
chmod 644 data/conversations/*
```

#### Log Rotation Check
```bash
# Check log file size
ls -lh data/logs/app.log

# Rotate if necessary
if [ $(stat -f%z data/logs/app.log 2>/dev/null || stat -c%s data/logs/app.log) -gt 10485760 ]; then
    mv data/logs/app.log data/logs/app.log.$(date +%Y%m%d_%H%M%S)
    touch data/logs/app.log
fi
```

#### Backup Validation
```bash
# Check recent backups
ls -la data/backups/ | head -5

# Validate latest backup integrity
if [ -f data/backups/latest.tar.gz ]; then
    tar -tzf data/backups/latest.tar.gz > /dev/null && echo "✓ Backup integrity OK"
fi
```

### 3. Application Startup

#### Manual Startup (Development/Testing)
```bash
# Start with verbose logging
python -m src.main

# Or with custom configuration
OPENROUTER_API_KEY=your_key_here python -m src.main
```

#### Service Startup (Production)
```bash
# Using systemd
sudo systemctl start personal-ai-chatbot

# Check service status
sudo systemctl status personal-ai-chatbot

# View service logs
sudo journalctl -u personal-ai-chatbot -f
```

#### Docker Startup (Containerized)
```bash
# Build and start container
docker build -t personal-ai-chatbot .
docker run -d \
  --name personal-ai-chatbot \
  -p 7860:7860 \
  -v /opt/personal-ai-chatbot/data:/app/data \
  -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  personal-ai-chatbot

# Check container status
docker ps | grep personal-ai-chatbot
docker logs -f personal-ai-chatbot
```

### 4. Post-Startup Validation

#### Health Check Validation
```bash
# Wait for application to fully start
sleep 30

# Run comprehensive health check
python scripts/health/health_check.py --verbose

# Expected output should show all checks as healthy
```

#### Application Readiness Check
```bash
# Test API endpoint (if exposed)
curl -s http://localhost:7860/health || echo "Health endpoint not available"

# Check application logs for startup errors
tail -20 data/logs/app.log | grep -i error || echo "No errors in recent logs"
```

#### Performance Validation
```bash
# Check initial resource usage
python scripts/health/health_check.py --check system_resources

# Verify application is responding
timeout 10 bash -c 'until curl -s http://localhost:7860 > /dev/null; do sleep 1; done' && echo "✓ Application responding"
```

### 5. Monitoring Setup

#### Start Monitoring Daemon
```bash
# Start background monitoring
python scripts/health/monitoring_daemon.py &

# Verify monitoring is running
ps aux | grep monitoring_daemon
```

#### Validate Monitoring Integration
```bash
# Check that metrics are being collected
sleep 60
python -c "
from src.monitoring.metrics_collector import metrics_collector
summary = metrics_collector.get_metrics_summary()
print(f'✓ Collecting {len(summary)} metrics')
"
```

## Troubleshooting

### Common Startup Issues

#### Configuration Errors
```bash
# Check for configuration syntax errors
python -c "
import json
try:
    with open('config/app.json') as f:
        json.load(f)
    print('✓ Configuration syntax OK')
except Exception as e:
    print(f'✗ Configuration error: {e}')
"
```

#### Permission Issues
```bash
# Check file permissions
ls -la data/
ls -la config/

# Fix permissions if needed
chmod -R 755 data/
chmod 644 config/*.json
```

#### Port Conflicts
```bash
# Check if port 7860 is available
netstat -tlnp | grep :7860 || echo "Port 7860 available"

# Find process using the port
lsof -i :7860
```

#### Memory Issues
```bash
# Check available memory
free -h

# Check system limits
ulimit -a

# Increase limits if needed
ulimit -n 65536  # File descriptors
ulimit -u 2048   # Processes
```

#### Network Issues
```bash
# Test OpenRouter connectivity
curl -I https://openrouter.ai/api/v1/models

# Check DNS resolution
nslookup openrouter.ai

# Test with API key
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/auth/key
```

### Recovery Procedures

#### Failed Startup Recovery
```bash
# Stop any running processes
pkill -f "python.*main.py"

# Clear temporary files
rm -f data/cache/*.tmp

# Restart with clean state
python -m src.main
```

#### Database Corruption Recovery
```bash
# Stop application
sudo systemctl stop personal-ai-chatbot

# Restore from backup
tar -xzf data/backups/latest.tar.gz -C /

# Restart application
sudo systemctl start personal-ai-chatbot
```

## Validation Checklist

- [ ] System resources meet requirements
- [ ] Configuration files are valid
- [ ] Data directories exist with correct permissions
- [ ] Network connectivity to external services
- [ ] Application starts without errors
- [ ] Health checks pass
- [ ] Monitoring system is collecting metrics
- [ ] Application is accessible on expected port

## Rollback Procedure

If startup fails and needs to be rolled back:

```bash
# Stop the application
sudo systemctl stop personal-ai-chatbot

# Restore previous configuration
cp config/app.json.backup config/app.json

# Clear any corrupted data
rm -f data/conversations/*.tmp

# Restart with previous version
sudo systemctl start personal-ai-chatbot
```

## References
- [System Architecture](../../docs/architecture.md)
- [Deployment Guide](../../docs/deployment.md)
- [Configuration Guide](../../docs/configuration.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Monitoring Setup](monitoring-setup.md)