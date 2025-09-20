# src/monitoring/health_monitor.py
"""Health monitoring system for Personal AI Chatbot."""

import time
import psutil
import requests
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.logging import logger
from ..utils.events import event_bus, EventType, EventPriority, Event
from .metrics_collector import metrics_collector


@dataclass
class HealthCheck:
    """Represents a health check result."""
    name: str
    status: str  # 'healthy', 'unhealthy', 'degraded'
    message: str
    timestamp: datetime
    duration_ms: float
    details: Optional[Dict[str, Any]] = None


class HealthMonitor:
    """Comprehensive health monitoring system."""

    def __init__(self):
        """Initialize health monitor."""
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_functions: Dict[str, Callable] = {}

        # Register built-in health checks
        self._register_builtin_checks()

        logger.info("HealthMonitor initialized")

    def _register_builtin_checks(self):
        """Register built-in health checks."""
        self.register_check("system_resources", self._check_system_resources)
        self.register_check("disk_space", self._check_disk_space)
        self.register_check("memory_usage", self._check_memory_usage)
        self.register_check("network_connectivity", self._check_network_connectivity)
        self.register_check("application_responsive", self._check_application_responsive)
        self.register_check("data_integrity", self._check_data_integrity)
        self.register_check("log_files", self._check_log_files)

    def register_check(self, name: str, check_function: Callable):
        """Register a custom health check.

        Args:
            name: Name of the health check
            check_function: Function that returns (status, message, details)
        """
        self.check_functions[name] = check_function
        logger.debug(f"Registered health check: {name}")

    def run_health_check(self, name: str) -> HealthCheck:
        """Run a specific health check.

        Args:
            name: Name of the health check to run

        Returns:
            HealthCheck result
        """
        if name not in self.check_functions:
            return HealthCheck(
                name=name,
                status="unhealthy",
                message=f"Health check '{name}' not found",
                timestamp=datetime.now(),
                duration_ms=0.0
            )

        start_time = time.time()

        try:
            status, message, details = self.check_functions[name]()
            duration_ms = (time.time() - start_time) * 1000

            health_check = HealthCheck(
                name=name,
                status=status,
                message=message,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                details=details
            )

            self.health_checks[name] = health_check

            # Record metrics
            metrics_collector.record_metric(
                f"health_check_{name}_duration",
                duration_ms,
                {"status": status}
            )

            # Publish event for critical issues
            if status in ["unhealthy", "degraded"]:
                event = Event(
                    EventType.ERROR,
                    {
                        "error_type": "health_check_failure",
                        "check_name": name,
                        "status": status,
                        "message": message,
                        "details": details or {}
                    },
                    priority=EventPriority.HIGH if status == "unhealthy" else EventPriority.NORMAL,
                    source="health_monitor"
                )
                event_bus.publish_sync(event)

            return health_check

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Health check '{name}' failed: {str(e)}")

            health_check = HealthCheck(
                name=name,
                status="unhealthy",
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=duration_ms
            )

            self.health_checks[name] = health_check
            return health_check

    def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks.

        Returns:
            Dictionary of all health check results
        """
        results = {}

        for name in self.check_functions.keys():
            results[name] = self.run_health_check(name)

        return results

    def get_overall_health(self) -> str:
        """Get overall system health status.

        Returns:
            'healthy', 'degraded', or 'unhealthy'
        """
        if not self.health_checks:
            return "unknown"

        statuses = [check.status for check in self.health_checks.values()]

        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"

    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary.

        Returns:
            Dictionary with health status and details
        """
        overall_status = self.get_overall_health()
        results = self.run_all_checks()

        summary = {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                name: {
                    "status": check.status,
                    "message": check.message,
                    "duration_ms": check.duration_ms,
                    "timestamp": check.timestamp.isoformat()
                }
                for name, check in results.items()
            }
        }

        return summary

    # Built-in health check implementations

    def _check_system_resources(self) -> tuple[str, str, Dict[str, Any]]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            }

            # Determine status based on thresholds
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
                status = "unhealthy"
                message = "System resources critically high"
            elif cpu_percent > 70 or memory.percent > 80 or disk.percent > 85:
                status = "degraded"
                message = "System resources elevated"
            else:
                status = "healthy"
                message = "System resources normal"

            return status, message, details

        except Exception as e:
            return "unhealthy", f"Failed to check system resources: {str(e)}", {}

    def _check_disk_space(self) -> tuple[str, str, Dict[str, Any]]:
        """Check available disk space."""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            percent_free = 100 - disk.percent

            details = {
                "free_gb": free_gb,
                "percent_free": percent_free,
                "total_gb": disk.total / (1024**3)
            }

            if percent_free < 5:  # Less than 5% free
                status = "unhealthy"
                message = ".2f"
            elif percent_free < 10:  # Less than 10% free
                status = "degraded"
                message = ".2f"
            else:
                status = "healthy"
                message = ".2f"

            return status, message, details

        except Exception as e:
            return "unhealthy", f"Failed to check disk space: {str(e)}", {}

    def _check_memory_usage(self) -> tuple[str, str, Dict[str, Any]]:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            used_gb = memory.used / (1024**3)
            percent_used = memory.percent

            details = {
                "used_gb": used_gb,
                "percent_used": percent_used,
                "total_gb": memory.total / (1024**3)
            }

            if percent_used > 90:
                status = "unhealthy"
                message = ".2f"
            elif percent_used > 80:
                status = "degraded"
                message = ".2f"
            else:
                status = "healthy"
                message = ".2f"

            return status, message, details

        except Exception as e:
            return "unhealthy", f"Failed to check memory usage: {str(e)}", {}

    def _check_network_connectivity(self) -> tuple[str, str, Dict[str, Any]]:
        """Check network connectivity."""
        try:
            # Test connectivity to a reliable endpoint
            response = requests.get("https://httpbin.org/status/200", timeout=5)
            response.raise_for_status()

            details = {
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "status_code": response.status_code
            }

            status = "healthy"
            message = "Network connectivity OK"

            return status, message, details

        except requests.exceptions.RequestException as e:
            return "unhealthy", f"Network connectivity failed: {str(e)}", {}
        except Exception as e:
            return "unhealthy", f"Failed to check network: {str(e)}", {}

    def _check_application_responsive(self) -> tuple[str, str, Dict[str, Any]]:
        """Check if the application is responsive."""
        try:
            # This would need to be customized based on how the app exposes health endpoints
            # For now, just check if the main process is running
            current_process = psutil.Process()
            details = {
                "process_id": current_process.pid,
                "process_status": current_process.status(),
                "cpu_percent": current_process.cpu_percent(),
                "memory_mb": current_process.memory_info().rss / (1024**2)
            }

            status = "healthy"
            message = "Application process running"

            return status, message, details

        except Exception as e:
            return "unhealthy", f"Application responsiveness check failed: {str(e)}", {}

    def _check_data_integrity(self) -> tuple[str, str, Dict[str, Any]]:
        """Check data integrity."""
        try:
            # Check if critical data files exist and are readable
            data_dir = Path("data")
            critical_files = [
                "data/conversations",
                "data/logs/app.log"
            ]

            missing_files = []
            corrupted_files = []

            for file_path in critical_files:
                path = Path(file_path)
                if not path.exists():
                    missing_files.append(str(file_path))
                elif path.is_file():
                    try:
                        # Try to read the file to check if it's corrupted
                        with open(path, 'r', encoding='utf-8') as f:
                            f.read(1024)  # Read first 1KB
                    except Exception:
                        corrupted_files.append(str(file_path))

            details = {
                "missing_files": missing_files,
                "corrupted_files": corrupted_files,
                "data_dir_exists": data_dir.exists()
            }

            if missing_files or corrupted_files:
                status = "unhealthy"
                message = f"Data integrity issues: {len(missing_files)} missing, {len(corrupted_files)} corrupted"
            else:
                status = "healthy"
                message = "Data integrity OK"

            return status, message, details

        except Exception as e:
            return "unhealthy", f"Data integrity check failed: {str(e)}", {}

    def _check_log_files(self) -> tuple[str, str, Dict[str, Any]]:
        """Check log file health."""
        try:
            log_dir = Path("data/logs")
            log_file = log_dir / "app.log"

            details = {
                "log_dir_exists": log_dir.exists(),
                "log_file_exists": log_file.exists(),
                "log_file_size_mb": 0,
                "last_modified": None
            }

            if log_file.exists():
                stat = log_file.stat()
                details["log_file_size_mb"] = stat.st_size / (1024**2)
                details["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()

                # Check if log file is too large (>100MB)
                if stat.st_size > 100 * 1024 * 1024:
                    status = "degraded"
                    message = ".2f"
                else:
                    status = "healthy"
                    message = "Log files healthy"
            else:
                status = "degraded"
                message = "Log file does not exist"

            return status, message, details

        except Exception as e:
            return "unhealthy", f"Log file check failed: {str(e)}", {}


# Global health monitor instance
health_monitor = HealthMonitor()