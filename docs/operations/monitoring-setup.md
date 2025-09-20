# Monitoring Setup Guide

## Overview
This guide provides procedures for setting up comprehensive monitoring for the Personal AI Chatbot system, including metrics collection, alerting, and dashboards.

**Risk Level**: 🟢 Medium
**Estimated Time**: 30-45 minutes
**Required Access**: System administrator

## Prerequisites

### System Requirements
- Python 3.8+ with monitoring dependencies
- Write access to log directories
- Network access for external monitoring services
- SMTP access for email alerts (optional)

### Required Packages
```bash
pip install psutil requests python-dotenv
```

### Directory Structure
```bash
data/
├── logs/                 # Application logs
├── monitoring/          # Monitoring data
│   ├── metrics/         # Metrics storage
│   ├── alerts/          # Alert history
│   └── dashboards/      # Dashboard exports
└── backups/             # System backups
```

## Monitoring Components Setup

### 1. Metrics Collection Setup

#### Initialize Metrics Collector
```bash
# Create monitoring directories
mkdir -p data/monitoring/metrics
mkdir -p data/monitoring/alerts
mkdir -p data/monitoring/dashboards

# Test metrics collection
python -c "
from src.monitoring.metrics_collector import metrics_collector
metrics_collector.collect_system_metrics()
print('✓ Metrics collection working')
"
```

#### Configure Metrics Collection
```python
# config/monitoring.json
{
  "metrics": {
    "collection_interval": 30,
    "retention_days": 30,
    "enabled_metrics": [
      "cpu_usage",
      "memory_usage",
      "disk_usage",
      "api_response_time",
      "api_requests_total",
      "api_errors_total"
    ]
  }
}
```

### 2. Health Monitoring Setup

#### Configure Health Checks
```python
# Automatic health check configuration
health_checks_config = {
  "enabled_checks": [
    "system_resources",
    "disk_space",
    "memory_usage",
    "network_connectivity",
    "application_responsive",
    "data_integrity",
    "log_files"
  ],
  "check_interval": 60,
  "failure_threshold": 3
}
```

#### Setup Automated Health Checks
```bash
# Test health monitoring
python scripts/health/health_check.py --verbose

# Setup cron job for periodic checks
echo "*/5 * * * * cd /opt/personal-ai-chatbot && python scripts/health/health_check.py --json >> data/logs/health_checks.log 2>&1" | crontab -
```

### 3. Alert Management Setup

#### Configure Alert Rules
```python
# config/alerts.json
{
  "rules": [
    {
      "name": "high_cpu_usage",
      "description": "CPU usage is too high",
      "metric_name": "cpu_usage",
      "condition": "gt",
      "threshold": 80.0,
      "severity": "warning",
      "cooldown_minutes": 60
    },
    {
      "name": "high_memory_usage",
      "description": "Memory usage is too high",
      "metric_name": "memory_usage",
      "condition": "gt",
      "threshold": 900.0,
      "severity": "warning",
      "cooldown_minutes": 30
    },
    {
      "name": "low_disk_space",
      "description": "Disk space is running low",
      "metric_name": "disk_usage",
      "condition": "gt",
      "threshold": 85.0,
      "severity": "error",
      "cooldown_minutes": 120
    },
    {
      "name": "api_errors_high",
      "description": "API error rate is too high",
      "metric_name": "api_errors_total",
      "condition": "gt",
      "threshold": 5.0,
      "severity": "error",
      "cooldown_minutes": 15
    }
  ]
}
```

#### Setup Alert Notifications
```python
# Configure notification channels
notification_config = {
  "channels": {
    "console": {
      "enabled": true
    },
    "email": {
      "enabled": false,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "alerts@yourdomain.com",
      "password": "your_password",
      "recipients": ["admin@yourdomain.com"]
    },
    "file": {
      "enabled": true,
      "log_file": "data/logs/alerts.log"
    }
  }
}
```

### 4. Performance Monitoring Setup

#### Configure Performance Baselines
```python
# Performance baseline configuration
performance_baselines = {
  "response_time_target": 8.0,      # seconds
  "response_time_warning": 15.0,    # seconds
  "response_time_critical": 30.0,   # seconds
  "cpu_warning": 70.0,              # percent
  "cpu_critical": 90.0,             # percent
  "memory_warning": 800.0,          # MB
  "memory_critical": 1000.0,        # MB
  "disk_warning": 85.0,             # percent
  "disk_critical": 95.0             # percent
}
```

#### Setup Performance Tracking
```bash
# Test performance monitoring
python -c "
from src.monitoring.performance_monitor import performance_monitor
report = performance_monitor.generate_report()
print(f'Performance score: {performance_monitor.get_performance_score():.1f}')
"
```

### 5. Dashboard Setup

#### Configure Dashboard Export
```python
# Dashboard configuration
dashboard_config = {
  "title": "Personal AI Chatbot - SRE Dashboard",
  "refresh_interval": 30,
  "export": {
    "enabled": true,
    "file_path": "data/monitoring/dashboards/current.json",
    "interval_minutes": 5
  },
  "slos": {
    "api_response_time_99": {
      "target": 99.0,
      "metric": "api_response_time"
    },
    "api_error_rate": {
      "target": 95.0,
      "metric": "api_errors_total"
    }
  }
}
```

#### Setup Dashboard Generation
```bash
# Generate initial dashboard
python -c "
from src.monitoring.dashboard import monitoring_dashboard
data = monitoring_dashboard.get_dashboard_data()
print(f'Dashboard generated with {len(data.get(\"alerts\", {}).get(\"active\", []))} active alerts')
"
```

## Service Integration

### 6. Systemd Service Configuration

#### Create Monitoring Service
```ini
# /etc/systemd/system/personal-ai-chatbot-monitoring.service
[Unit]
Description=Personal AI Chatbot Monitoring Daemon
After=network.target personal-ai-chatbot.service

[Service]
Type=simple
User=personal-ai-chatbot
WorkingDirectory=/opt/personal-ai-chatbot
ExecStart=/opt/personal-ai-chatbot/venv/bin/python scripts/health/monitoring_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Service
```bash
# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable personal-ai-chatbot-monitoring
sudo systemctl start personal-ai-chatbot-monitoring

# Check service status
sudo systemctl status personal-ai-chatbot-monitoring
```

### 7. Log Rotation Setup

#### Configure Log Rotation
```bash
# /etc/logrotate.d/personal-ai-chatbot-monitoring
/opt/personal-ai-chatbot/data/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 personal-ai-chatbot personal-ai-chatbot
    postrotate
        systemctl reload personal-ai-chatbot-monitoring
    endscript
}
```

## Validation and Testing

### 8. Monitoring Validation

#### Test Metrics Collection
```bash
# Verify metrics are being collected
python -c "
from src.monitoring.metrics_collector import metrics_collector
summary = metrics_collector.get_metrics_summary()
for name, data in summary.items():
    print(f'{name}: {data.get(\"current\", \"N/A\")}')
"
```

#### Test Alert System
```bash
# Trigger a test alert
python -c "
from src.monitoring.alert_manager import alert_manager
from src.monitoring.alert_manager import AlertRule
rule = AlertRule(
    name='test_alert',
    description='Test alert for validation',
    metric_name='cpu_usage',
    condition='gt',
    threshold=0.1,
    severity='info'
)
alert_manager.add_rule(rule)
print('✓ Test alert rule added')
"
```

#### Test Health Checks
```bash
# Run comprehensive health check
python scripts/health/health_check.py --verbose

# Verify all checks pass
echo $?
```

#### Test Dashboard Generation
```bash
# Generate and validate dashboard
python -c "
from src.monitoring.dashboard import monitoring_dashboard
data = monitoring_dashboard.get_dashboard_data()
print(f'✓ Dashboard generated with {len(data)} sections')
"
```

## Maintenance Procedures

### 9. Regular Maintenance

#### Daily Checks
```bash
# Check monitoring service status
sudo systemctl status personal-ai-chatbot-monitoring

# Verify log rotation
ls -la data/logs/ | grep -E '\.gz$'

# Check disk usage
df -h /opt/personal-ai-chatbot
```

#### Weekly Maintenance
```bash
# Clean old monitoring data (older than 30 days)
find data/monitoring/ -name "*.json" -mtime +30 -delete

# Verify backup integrity
python scripts/backup/validate_backup.py

# Check alert rule effectiveness
python -c "
from src.monitoring.alert_manager import alert_manager
rules = alert_manager.get_all_rules()
print(f'Active alert rules: {len(rules)}')
"
```

#### Monthly Reviews
```bash
# Review performance trends
python -c "
from src.monitoring.performance_monitor import performance_monitor
reports = performance_monitor.get_recent_reports(30)
avg_score = sum(r.score for r in reports) / len(reports) if reports else 0
print(f'Average performance score (30 days): {avg_score:.1f}')
"

# Analyze alert patterns
python -c "
from src.monitoring.alert_manager import alert_manager
alerts = alert_manager.get_alert_history(30 * 24)  # 30 days
severity_counts = {}
for alert in alerts:
    severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
print('Alert summary (30 days):', severity_counts)
"
```

## Troubleshooting

### Common Issues

#### Monitoring Service Not Starting
```bash
# Check service logs
sudo journalctl -u personal-ai-chatbot-monitoring -n 50

# Check configuration
python -c "
import json
with open('config/monitoring.json') as f:
    config = json.load(f)
print('Configuration loaded successfully')
"
```

#### Missing Metrics
```bash
# Check metrics collector status
python -c "
from src.monitoring.metrics_collector import metrics_collector
print(f'Metrics collector running: {metrics_collector.is_running}')
summary = metrics_collector.get_metrics_summary()
print(f'Available metrics: {len(summary)}')
"
```

#### Alert Rules Not Working
```bash
# Validate alert rules
python -c "
from src.monitoring.alert_manager import alert_manager
rules = alert_manager.get_all_rules()
for name, rule in rules.items():
    print(f'{name}: {rule.description} (threshold: {rule.threshold})')
"
```

#### Performance Issues
```bash
# Check monitoring resource usage
ps aux | grep monitoring_daemon

# Review monitoring configuration
python -c "
import json
with open('config/monitoring.json') as f:
    print(json.dumps(json.load(f), indent=2))
"
```

## References
- [System Architecture](../../docs/architecture.md)
- [Performance Baselines](../../docs/performance-baselines.md)
- [Alert Response Procedures](alert-response.md)
- [Incident Response Guide](incident-response.md)
- [Troubleshooting Guide](troubleshooting.md)