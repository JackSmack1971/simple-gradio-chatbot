# Backup Automation Scripts

This directory contains scripts for automated backup creation, validation, and management of the Personal AI Chatbot system.

## Scripts Overview

### `automated_backup.py`
Creates comprehensive backups of the application data, configuration, and system state.

**Features:**
- Multiple backup types (full, incremental, config)
- Integrity validation
- Automatic cleanup of old backups
- Event-driven notifications
- Comprehensive metadata generation

**Usage:**
```bash
# Create full backup
python scripts/backup/automated_backup.py

# Create incremental backup with validation
python scripts/backup/automated_backup.py --type incremental --validate

# Create config-only backup
python scripts/backup/automated_backup.py --type config

# Create encrypted backup
python scripts/backup/automated_backup.py --encrypt
```

### `validate_backup.py`
Validates backup integrity and performs restoration tests.

**Features:**
- Archive integrity checking
- Structure validation
- Metadata validation
- Test restoration
- Comprehensive data integrity checks

**Usage:**
```bash
# Validate latest backup
python scripts/backup/validate_backup.py

# Validate specific backup
python scripts/backup/validate_backup.py --backup data/backups/full_backup_20231201_120000.tar.gz

# Comprehensive validation with test restore
python scripts/backup/validate_backup.py --comprehensive --test-restore

# List all backups
python scripts/backup/validate_backup.py --list
```

## Backup Types

### Full Backup
- **Contents**: All application data, configuration, and logs
- **Frequency**: Daily or weekly
- **Retention**: 30 days
- **Use Case**: Complete system restoration

### Incremental Backup
- **Contents**: Conversations and logs since last full backup
- **Frequency**: Hourly or daily
- **Retention**: 7 days
- **Use Case**: Recent data recovery

### Configuration Backup
- **Contents**: Application configuration files only
- **Frequency**: After configuration changes
- **Retention**: 90 days
- **Use Case**: Configuration rollback

## Directory Structure

```
data/backups/
├── full_backup_20231201_120000.tar.gz          # Full backup archive
├── full_backup_20231201_120000.metadata.json   # Backup metadata
├── incremental_backup_20231201_130000.tar.gz   # Incremental backup
├── config_backup_20231201_140000.tar.gz        # Config backup
└── ...
```

## Backup Metadata

Each backup includes comprehensive metadata:

```json
{
  "backup_name": "full_backup_20231201_120000",
  "backup_type": "full",
  "created_at": "2023-12-01T12:00:00.000000",
  "archive_path": "data/backups/full_backup_20231201_120000.tar.gz",
  "size_bytes": 104857600,
  "size_mb": 100.0,
  "checksum": "abc123...",
  "contents": [
    "data/conversations/",
    "data/cache/",
    "config/app.json"
  ]
}
```

## Automation

### Cron Jobs (Linux/macOS)

```bash
# Daily full backup at 2 AM
0 2 * * * cd /opt/personal-ai-chatbot && python scripts/backup/automated_backup.py --type full --validate

# Hourly incremental backup
0 * * * * cd /opt/personal-ai-chatbot && python scripts/backup/automated_backup.py --type incremental

# Weekly cleanup
0 3 * * 0 cd /opt/personal-ai-chatbot && python scripts/backup/automated_backup.py --cleanup
```

### Windows Task Scheduler

Create scheduled tasks for:
- Daily full backups
- Hourly incremental backups
- Weekly validation and cleanup

### Systemd Timer (Linux)

```ini
# /etc/systemd/system/personal-ai-chatbot-backup.service
[Unit]
Description=Personal AI Chatbot Backup
After=network.target

[Service]
Type=oneshot
User=personal-ai-chatbot
WorkingDirectory=/opt/personal-ai-chatbot
ExecStart=/opt/personal-ai-chatbot/venv/bin/python scripts/backup/automated_backup.py --type full --validate
```

```ini
# /etc/systemd/system/personal-ai-chatbot-backup.timer
[Unit]
Description=Run Personal AI Chatbot backup daily
Requires=personal-ai-chatbot-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

## Validation and Testing

### Automated Validation
```bash
# Validate all backups
for backup in data/backups/*.tar.gz; do
    echo "Validating $backup..."
    python scripts/backup/validate_backup.py --backup "$backup" --test-restore
done
```

### Manual Testing
```bash
# Test restoration procedure
mkdir /tmp/backup_test
cd /tmp/backup_test
tar -xzf /opt/personal-ai-chatbot/data/backups/full_backup_20231201_120000.tar.gz

# Verify restored data
ls -la data/
ls -la config/
```

## Security Considerations

### Encryption
- Backups can be encrypted using `--encrypt` flag
- Encryption keys should be securely managed
- Encrypted backups have `.enc` extension

### Access Control
- Backup files should have restricted permissions
- Backup directory: `chmod 700 data/backups/`
- Backup files: `chmod 600 data/backups/*.tar.gz`

### Secure Storage
- Consider offsite backup storage
- Use encrypted cloud storage (AWS S3, Google Cloud Storage)
- Implement backup rotation policies

## Monitoring and Alerting

### Backup Success Monitoring
```python
# Integration with monitoring system
from monitoring.alert_manager import alert_manager

# Alert on backup failure
if backup_result["status"] != "success":
    alert_manager.trigger_alert(
        "backup_failed",
        f"Backup failed: {backup_result['error']}"
    )
```

### Backup Validation Alerts
- Alert when backup validation fails
- Alert when backup size is abnormal
- Alert when backup creation takes too long

## Disaster Recovery

### Recovery Procedures
1. Identify appropriate backup
2. Validate backup integrity
3. Restore to temporary location
4. Verify restored data
5. Switch to restored system

### Recovery Time Objectives
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour for incremental, 24 hours for full

## Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Check permissions
ls -la data/backups/

# Fix permissions
chmod 700 data/backups/
chmod 600 data/backups/*.tar.gz
```

#### Disk Space Issues
```bash
# Check disk space
df -h /opt/personal-ai-chatbot

# Clean old backups manually
find data/backups/ -name "*.tar.gz" -mtime +30 -delete
```

#### Backup Corruption
```bash
# Test archive integrity
tar -tzf data/backups/full_backup_20231201_120000.tar.gz > /dev/null

# Validate with script
python scripts/backup/validate_backup.py --backup data/backups/full_backup_20231201_120000.tar.gz
```

#### Large Backup Files
- Consider compression options
- Implement incremental backups
- Archive old data separately

## Performance Optimization

### Backup Performance
- Use parallel compression
- Exclude temporary files
- Schedule during low-usage periods
- Monitor backup duration

### Storage Optimization
- Compress backups (gzip default)
- Use incremental backups for large datasets
- Implement deduplication if supported
- Regular cleanup of old backups

## Integration

### Event System Integration
Backups publish events for monitoring:
- `backup_started`: Backup creation initiated
- `backup_completed`: Backup successfully created
- `backup_failed`: Backup creation failed
- `backup_validated`: Backup validation completed

### Monitoring Integration
- Backup success/failure metrics
- Backup size and duration tracking
- Validation results monitoring
- Storage usage monitoring

## References
- [System Architecture](../../docs/architecture.md)
- [Security Considerations](../../docs/security-considerations.md)
- [Monitoring Setup](../operations/monitoring-setup.md)
- [Disaster Recovery Plan](../operations/disaster-recovery.md)