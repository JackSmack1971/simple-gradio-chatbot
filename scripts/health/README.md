# Health Check Scripts

This directory contains scripts for monitoring and maintaining the health of the Personal AI Chatbot system.

## Scripts Overview

### `health_check.py`
Comprehensive health check script that validates system components and reports status.

**Usage:**
```bash
# Run all health checks
python scripts/health/health_check.py

# Run with verbose output
python scripts/health/health_check.py --verbose

# Run specific health check
python scripts/health/health_check.py --check system_resources

# Output in JSON format
python scripts/health/health_check.py --json
```

**Exit Codes:**
- `0`: All checks passed (healthy)
- `1`: Critical issues found (unhealthy)
- `2`: Some issues found (degraded)

### `monitoring_daemon.py`
Continuous monitoring daemon that runs health checks, collects metrics, and manages alerts.

**Usage:**
```bash
# Run continuous monitoring
python scripts/health/monitoring_daemon.py

# Run with custom configuration
python scripts/health/monitoring_daemon.py --config config/custom-monitoring.json

# Run with custom interval (30 seconds)
python scripts/health/monitoring_daemon.py --interval 30

# Run once and exit
python scripts/health/monitoring_daemon.py --once
```

## Health Checks

The system includes the following built-in health checks:

- **system_resources**: CPU, memory, and disk usage
- **disk_space**: Available disk space validation
- **memory_usage**: Memory usage monitoring
- **network_connectivity**: Network connectivity testing
- **application_responsive**: Application process health
- **data_integrity**: Data file integrity validation
- **log_files**: Log file health and rotation

## Configuration

### Monitoring Configuration (`config/monitoring.json`)

```json
{
  "enabled_checks": [
    "system_resources",
    "disk_space",
    "memory_usage",
    "network_connectivity"
  ],
  "alert_rules": [
    {
      "name": "high_cpu_usage",
      "description": "CPU usage is too high",
      "metric_name": "cpu_usage",
      "condition": "gt",
      "threshold": 80.0,
      "severity": "warning"
    }
  ],
  "dashboard_export": {
    "enabled": true,
    "file_path": "data/monitoring/dashboard.json",
    "interval_minutes": 5
  }
}
```

## Integration

These scripts integrate with the monitoring system components:

- **Health Monitor**: Performs detailed health checks
- **Metrics Collector**: Collects system and application metrics
- **Alert Manager**: Manages alert rules and notifications
- **Performance Monitor**: Tracks performance baselines
- **Event System**: Publishes health events for other components

## Automation

### Systemd Service (Linux)

Create `/etc/systemd/system/personal-ai-chatbot-monitoring.service`:

```ini
[Unit]
Description=Personal AI Chatbot Monitoring Daemon
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/personal-ai-chatbot
ExecStart=/usr/bin/python3 scripts/health/monitoring_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Cron Job (Linux/macOS)

Add to crontab for periodic health checks:

```bash
# Health check every 5 minutes
*/5 * * * * cd /path/to/personal-ai-chatbot && python3 scripts/health/health_check.py --json >> data/logs/health_checks.log 2>&1
```

### Windows Task Scheduler

Create a scheduled task to run health checks:

```powershell
# PowerShell command for Task Scheduler
cd C:\path\to\personal-ai-chatbot
python scripts\health\health_check.py --json
```

## Monitoring Output

Health check results are logged and can be exported in various formats:

- **Console Output**: Human-readable status reports
- **JSON Output**: Structured data for dashboards and APIs
- **Log Files**: Detailed logs in `data/logs/`
- **Dashboard Export**: Complete monitoring dashboard in JSON format

## Alerts and Notifications

The monitoring system supports multiple notification channels:

- **Console**: Local console output
- **Email**: SMTP-based email notifications
- **File**: Alert logging to files
- **Custom**: Extensible notification system

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Python path includes the `src` directory
2. **Permission Errors**: Check file permissions for log and data directories
3. **Network Issues**: Verify network connectivity for external checks
4. **Configuration Errors**: Validate JSON configuration file syntax

### Debug Mode

Enable debug logging:

```bash
export PYTHONPATH=/path/to/personal-ai-chatbot/src:$PYTHONPATH
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python scripts/health/health_check.py --verbose