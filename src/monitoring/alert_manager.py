# src/monitoring/alert_manager.py
"""Alert management system for Personal AI Chatbot."""

import time
import smtplib
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from ..utils.logging import logger
from ..utils.events import event_bus, EventType, EventPriority, Event
from .metrics_collector import metrics_collector


@dataclass
class AlertRule:
    """Represents an alert rule configuration."""
    name: str
    description: str
    metric_name: str
    condition: str  # 'gt', 'lt', 'eq', 'ne'
    threshold: float
    duration_minutes: int = 5
    severity: str = "warning"  # 'info', 'warning', 'error', 'critical'
    enabled: bool = True
    cooldown_minutes: int = 60
    last_triggered: Optional[datetime] = None


@dataclass
class Alert:
    """Represents an active alert."""
    id: str
    rule_name: str
    severity: str
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertManager:
    """Central alert management system."""

    def __init__(self, config_file: str = "config/alerts.json"):
        """Initialize alert manager.

        Args:
            config_file: Path to alert configuration file
        """
        self.config_file = Path(config_file)
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: Dict[str, Callable] = {}

        # Default notification channels
        self._setup_default_channels()

        # Load configuration
        self._load_config()

        logger.info("AlertManager initialized")

    def _setup_default_channels(self):
        """Set up default notification channels."""
        self.register_channel("console", self._notify_console)
        self.register_channel("email", self._notify_email)
        self.register_channel("file", self._notify_file)

    def register_channel(self, name: str, handler: Callable):
        """Register a notification channel.

        Args:
            name: Channel name
            handler: Function to handle notifications
        """
        self.notification_channels[name] = handler
        logger.debug(f"Registered notification channel: {name}")

    def add_rule(self, rule: AlertRule):
        """Add an alert rule.

        Args:
            rule: Alert rule to add
        """
        self.alert_rules[rule.name] = rule
        self._save_config()
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str):
        """Remove an alert rule.

        Args:
            rule_name: Name of rule to remove
        """
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            self._save_config()
            logger.info(f"Removed alert rule: {rule_name}")

    def get_rule(self, rule_name: str) -> Optional[AlertRule]:
        """Get an alert rule by name.

        Args:
            rule_name: Name of rule to get

        Returns:
            Alert rule or None if not found
        """
        return self.alert_rules.get(rule_name)

    def get_all_rules(self) -> Dict[str, AlertRule]:
        """Get all alert rules.

        Returns:
            Dictionary of all alert rules
        """
        return self.alert_rules.copy()

    def evaluate_rules(self):
        """Evaluate all alert rules against current metrics."""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            self._evaluate_rule(rule)

    def _evaluate_rule(self, rule: AlertRule):
        """Evaluate a single alert rule.

        Args:
            rule: Alert rule to evaluate
        """
        try:
            metric = metrics_collector.get_metric(rule.metric_name)
            if not metric:
                return

            # Get recent values
            recent_points = metric.get_recent_points(rule.duration_minutes)
            if not recent_points:
                return

            # Check condition
            current_value = recent_points[-1].value
            condition_met = self._check_condition(current_value, rule.condition, rule.threshold)

            if condition_met:
                # Check cooldown
                if rule.last_triggered:
                    cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                    if datetime.now() < cooldown_end:
                        return  # Still in cooldown

                # Trigger alert
                self._trigger_alert(rule, current_value)

                # Update last triggered
                rule.last_triggered = datetime.now()

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.name}: {str(e)}")

    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Check if a condition is met.

        Args:
            value: Current metric value
            condition: Condition operator
            threshold: Threshold value

        Returns:
            True if condition is met
        """
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return value == threshold
        elif condition == "ne":
            return value != threshold
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False

    def _trigger_alert(self, rule: AlertRule, current_value: float):
        """Trigger an alert.

        Args:
            rule: Alert rule that triggered
            current_value: Current metric value
        """
        alert_id = f"alert_{rule.name}_{int(time.time())}"

        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"{rule.description}: {current_value:.2f} {rule.condition} {rule.threshold}",
            value=current_value,
            threshold=rule.threshold,
            timestamp=datetime.now(),
            metadata={
                "metric_name": rule.metric_name,
                "condition": rule.condition,
                "duration_minutes": rule.duration_minutes
            }
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Publish event
        event = Event(
            EventType.ERROR,
            {
                "alert_type": "metric_threshold",
                "alert_id": alert_id,
                "rule_name": rule.name,
                "severity": rule.severity,
                "message": alert.message,
                "value": current_value,
                "threshold": rule.threshold
            },
            priority=self._severity_to_priority(rule.severity),
            source="alert_manager"
        )
        event_bus.publish_sync(event)

        # Send notifications
        self._send_notifications(alert)

        logger.warning(f"Alert triggered: {alert.message}")

    def resolve_alert(self, alert_id: str, resolved_by: str = "auto"):
        """Resolve an active alert.

        Args:
            alert_id: ID of alert to resolve
            resolved_by: Who/what resolved the alert
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            alert.metadata["resolved_by"] = resolved_by

            # Publish resolution event
            event = Event(
                EventType.SYSTEM_EVENT,
                {
                    "event_type": "alert_resolved",
                    "alert_id": alert_id,
                    "rule_name": alert.rule_name,
                    "resolved_by": resolved_by
                },
                priority=EventPriority.NORMAL,
                source="alert_manager"
            )
            event_bus.publish_sync(event)

            logger.info(f"Alert resolved: {alert_id}")

    def get_active_alerts(self) -> Dict[str, Alert]:
        """Get all active alerts.

        Returns:
            Dictionary of active alerts
        """
        return self.active_alerts.copy()

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            List of alerts in the time period
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff]

    def _severity_to_priority(self, severity: str) -> EventPriority:
        """Convert severity to event priority.

        Args:
            severity: Alert severity

        Returns:
            Event priority
        """
        mapping = {
            "info": EventPriority.LOW,
            "warning": EventPriority.NORMAL,
            "error": EventPriority.HIGH,
            "critical": EventPriority.CRITICAL
        }
        return mapping.get(severity, EventPriority.NORMAL)

    def _send_notifications(self, alert: Alert):
        """Send notifications for an alert.

        Args:
            alert: Alert to notify about
        """
        # For now, just use console notification
        # In production, this would be configurable
        if "console" in self.notification_channels:
            self.notification_channels["console"](alert)

    def _notify_console(self, alert: Alert):
        """Send console notification.

        Args:
            alert: Alert to notify about
        """
        severity_icon = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }.get(alert.severity, "❓")

        print(f"{severity_icon} ALERT [{alert.severity.upper()}]: {alert.message}")

    def _notify_email(self, alert: Alert):
        """Send email notification.

        Args:
            alert: Alert to notify about
        """
        # Email configuration would be loaded from config
        # This is a placeholder implementation
        logger.info(f"Email notification would be sent: {alert.message}")

    def _notify_file(self, alert: Alert):
        """Write alert to file.

        Args:
            alert: Alert to notify about
        """
        try:
            alert_dir = Path("data/alerts")
            alert_dir.mkdir(exist_ok=True)

            alert_file = alert_dir / f"alert_{alert.id}.json"
            with open(alert_file, 'w') as f:
                json.dump({
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "severity": alert.severity,
                    "message": alert.message,
                    "value": alert.value,
                    "threshold": alert.threshold,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata
                }, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to write alert to file: {str(e)}")

    def _load_config(self):
        """Load alert configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

                for rule_data in config_data.get("rules", []):
                    rule = AlertRule(**rule_data)
                    self.alert_rules[rule.name] = rule

                logger.info(f"Loaded {len(self.alert_rules)} alert rules from config")

        except Exception as e:
            logger.error(f"Failed to load alert config: {str(e)}")

    def _save_config(self):
        """Save alert configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            config_data = {
                "rules": [
                    {
                        "name": rule.name,
                        "description": rule.description,
                        "metric_name": rule.metric_name,
                        "condition": rule.condition,
                        "threshold": rule.threshold,
                        "duration_minutes": rule.duration_minutes,
                        "severity": rule.severity,
                        "enabled": rule.enabled,
                        "cooldown_minutes": rule.cooldown_minutes
                    }
                    for rule in self.alert_rules.values()
                ]
            }

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save alert config: {str(e)}")


# Global alert manager instance
alert_manager = AlertManager()