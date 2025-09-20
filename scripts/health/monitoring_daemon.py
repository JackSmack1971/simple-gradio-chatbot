#!/usr/bin/env python3
"""
Monitoring Daemon for Personal AI Chatbot

This daemon runs continuous monitoring, health checks, and alerting for the
Personal AI Chatbot system. It can be run as a background service.

Usage:
    python scripts/health/monitoring_daemon.py [--config CONFIG_FILE] [--interval SECONDS]

Options:
    --config FILE     Path to configuration file (default: config/monitoring.json)
    --interval SEC    Monitoring interval in seconds (default: 60)
    --once            Run monitoring once and exit
    --help, -h        Show this help message
"""

import sys
import json
import time
import signal
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Ensure project root is on the path for package imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.monitoring.health_monitor import health_monitor
from src.monitoring.metrics_collector import metrics_collector
from src.monitoring.alert_manager import alert_manager
from src.monitoring.performance_monitor import performance_monitor
from src.monitoring.dashboard import monitoring_dashboard
from src.utils.logging import logger
from src.utils.events import event_bus, EventType


class MonitoringDaemon:
    """Monitoring daemon for continuous system monitoring."""

    def __init__(self, config_file: str = "config/monitoring.json", interval: int = 60):
        """Initialize monitoring daemon.

        Args:
            config_file: Path to configuration file
            interval: Monitoring interval in seconds
        """
        self.config_file = Path(config_file)
        self.interval = interval
        self.is_running = False
        self.config = self._load_config()

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info("Monitoring daemon initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration.

        Returns:
            Configuration dictionary
        """
        default_config = {
            "enabled_checks": ["system_resources", "disk_space", "memory_usage", "network_connectivity"],
            "alert_rules": [
                {
                    "name": "high_cpu_usage",
                    "description": "CPU usage is too high",
                    "metric_name": "cpu_usage",
                    "condition": "gt",
                    "threshold": 80.0,
                    "severity": "warning"
                },
                {
                    "name": "high_memory_usage",
                    "description": "Memory usage is too high",
                    "metric_name": "memory_usage",
                    "condition": "gt",
                    "threshold": 900.0,
                    "severity": "warning"
                },
                {
                    "name": "low_disk_space",
                    "description": "Disk space is running low",
                    "metric_name": "disk_usage",
                    "condition": "gt",
                    "threshold": 85.0,
                    "severity": "error"
                }
            ],
            "dashboard_export": {
                "enabled": True,
                "file_path": "data/monitoring/dashboard.json",
                "interval_minutes": 5
            },
            "log_level": "INFO"
        }

        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                default_config.update(loaded_config)
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                # Create default config file
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default configuration at {self.config_file}")

        except Exception as e:
            logger.warning(f"Failed to load config, using defaults: {str(e)}")

        return default_config

    def _setup_alert_rules(self):
        """Setup alert rules from configuration."""
        for rule_config in self.config.get("alert_rules", []):
            try:
                from src.monitoring.alert_manager import AlertRule
                rule = AlertRule(**rule_config)
                alert_manager.add_rule(rule)
                logger.info(f"Added alert rule: {rule.name}")
            except Exception as e:
                logger.error(f"Failed to add alert rule {rule_config.get('name', 'unknown')}: {str(e)}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.is_running = False

    def _run_monitoring_cycle(self):
        """Run one complete monitoring cycle."""
        try:
            logger.debug("Starting monitoring cycle")

            # Collect system metrics
            metrics_collector.collect_system_metrics()

            # Run health checks
            enabled_checks = self.config.get("enabled_checks", [])
            for check_name in enabled_checks:
                try:
                    health_monitor.run_health_check(check_name)
                except Exception as e:
                    logger.error(f"Health check '{check_name}' failed: {str(e)}")

            # Evaluate alert rules
            alert_manager.evaluate_rules()

            # Export dashboard if enabled
            dashboard_config = self.config.get("dashboard_export", {})
            if dashboard_config.get("enabled", False):
                try:
                    file_path = dashboard_config.get("file_path", "data/monitoring/dashboard.json")
                    monitoring_dashboard.export_dashboard(file_path)
                except Exception as e:
                    logger.error(f"Failed to export dashboard: {str(e)}")

            logger.debug("Monitoring cycle completed")

        except Exception as e:
            logger.error(f"Monitoring cycle failed: {str(e)}")

    def run_once(self):
        """Run monitoring once and exit."""
        logger.info("Running monitoring once")
        self._run_monitoring_cycle()
        logger.info("Monitoring completed")

    def run_continuous(self):
        """Run monitoring continuously."""
        logger.info(f"Starting continuous monitoring (interval: {self.interval}s)")

        # Setup alert rules
        self._setup_alert_rules()

        # Start monitoring components
        metrics_collector.start_collection()
        performance_monitor.start_monitoring()

        self.is_running = True
        cycle_count = 0

        try:
            while self.is_running:
                start_time = time.time()

                self._run_monitoring_cycle()
                cycle_count += 1

                # Log status periodically
                if cycle_count % 10 == 0:
                    logger.info(f"Monitoring cycle #{cycle_count} completed")

                # Sleep until next cycle
                elapsed = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed)

                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as e:
            logger.error(f"Monitoring daemon failed: {str(e)}")
        finally:
            self._shutdown()

    def _shutdown(self):
        """Shutdown monitoring daemon."""
        logger.info("Shutting down monitoring daemon")

        try:
            metrics_collector.stop_collection()
            performance_monitor.stop_monitoring()
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

        logger.info("Monitoring daemon shutdown complete")


def main():
    """Main entry point for monitoring daemon."""
    parser = argparse.ArgumentParser(
        description="Monitoring Daemon for Personal AI Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--config",
        default="config/monitoring.json",
        help="Path to configuration file"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Monitoring interval in seconds"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run monitoring once and exit"
    )

    args = parser.parse_args()

    try:
        daemon = MonitoringDaemon(args.config, args.interval)

        if args.once:
            daemon.run_once()
        else:
            daemon.run_continuous()

    except Exception as e:
        logger.error(f"Monitoring daemon failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()