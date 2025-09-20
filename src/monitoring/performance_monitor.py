# src/monitoring/performance_monitor.py
"""Performance monitoring system for Personal AI Chatbot."""

import time
import json
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.logging import logger
from ..utils.events import event_bus, EventType, EventPriority, Event
from .metrics_collector import metrics_collector


@dataclass
class PerformanceBaseline:
    """Performance baseline configuration."""
    metric_name: str
    target_value: float
    warning_threshold: float
    critical_threshold: float
    unit: str
    description: str


@dataclass
class PerformanceReport:
    """Performance report data."""
    timestamp: datetime
    metrics: Dict[str, Any]
    baselines: Dict[str, Any]
    violations: List[Dict[str, Any]]
    recommendations: List[str]


class PerformanceMonitor:
    """Comprehensive performance monitoring system."""

    def __init__(self):
        """Initialize performance monitor."""
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.is_monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.report_history: List[PerformanceReport] = []

        # Load performance baselines from documentation
        self._load_baselines()

        logger.info("PerformanceMonitor initialized")

    def _load_baselines(self):
        """Load performance baselines from configuration."""
        # These baselines are based on the performance-baselines.md document
        self.baselines = {
            "response_time_simple": PerformanceBaseline(
                metric_name="api_response_time",
                target_value=3.0,
                warning_threshold=8.0,
                critical_threshold=15.0,
                unit="seconds",
                description="Simple query response time"
            ),
            "response_time_complex": PerformanceBaseline(
                metric_name="api_response_time",
                target_value=8.0,
                warning_threshold=15.0,
                critical_threshold=30.0,
                unit="seconds",
                description="Complex query response time"
            ),
            "cpu_usage": PerformanceBaseline(
                metric_name="cpu_usage",
                target_value=50.0,
                warning_threshold=70.0,
                critical_threshold=90.0,
                unit="percent",
                description="CPU usage percentage"
            ),
            "memory_usage": PerformanceBaseline(
                metric_name="memory_usage",
                target_value=500.0,
                warning_threshold=800.0,
                critical_threshold=1000.0,
                unit="MB",
                description="Memory usage"
            ),
            "disk_usage": PerformanceBaseline(
                metric_name="disk_usage",
                target_value=70.0,
                warning_threshold=85.0,
                critical_threshold=95.0,
                unit="percent",
                description="Disk usage percentage"
            )
        }

    def add_baseline(self, baseline: PerformanceBaseline):
        """Add a performance baseline.

        Args:
            baseline: Performance baseline to add
        """
        self.baselines[baseline.metric_name] = baseline
        logger.info(f"Added performance baseline: {baseline.metric_name}")

    def remove_baseline(self, metric_name: str):
        """Remove a performance baseline.

        Args:
            metric_name: Name of baseline to remove
        """
        if metric_name in self.baselines:
            del self.baselines[metric_name]
            logger.info(f"Removed performance baseline: {metric_name}")

    def start_monitoring(self):
        """Start continuous performance monitoring."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                self._check_performance()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Performance monitoring error: {str(e)}")
                time.sleep(60)

    def _check_performance(self):
        """Check current performance against baselines."""
        violations = []
        recommendations = []

        for baseline in self.baselines.values():
            metric = metrics_collector.get_metric(baseline.metric_name)
            if not metric:
                continue

            # Get current value (average over last 5 minutes)
            current_value = metric.get_average(5)
            if current_value is None:
                continue

            # Check against thresholds
            if current_value >= baseline.critical_threshold:
                severity = "critical"
                violations.append({
                    "metric": baseline.metric_name,
                    "severity": severity,
                    "current_value": current_value,
                    "threshold": baseline.critical_threshold,
                    "description": baseline.description
                })
                recommendations.append(f"CRITICAL: {baseline.description} is {current_value:.2f}{baseline.unit} (threshold: {baseline.critical_threshold}{baseline.unit})")

            elif current_value >= baseline.warning_threshold:
                severity = "warning"
                violations.append({
                    "metric": baseline.metric_name,
                    "severity": severity,
                    "current_value": current_value,
                    "threshold": baseline.warning_threshold,
                    "description": baseline.description
                })
                recommendations.append(f"WARNING: {baseline.description} is {current_value:.2f}{baseline.unit} (threshold: {baseline.warning_threshold}{baseline.unit})")

            # Publish events for violations
            if violations:
                event = Event(
                    EventType.ERROR,
                    {
                        "performance_violations": violations,
                        "recommendations": recommendations
                    },
                    priority=EventPriority.HIGH if any(v["severity"] == "critical" for v in violations) else EventPriority.NORMAL,
                    source="performance_monitor"
                )
                event_bus.publish_sync(event)

    def generate_report(self) -> PerformanceReport:
        """Generate a comprehensive performance report.

        Returns:
            Performance report
        """
        metrics_summary = metrics_collector.get_metrics_summary()
        violations = []
        recommendations = []

        # Analyze each baseline
        for baseline in self.baselines.values():
            if baseline.metric_name in metrics_summary:
                metric_data = metrics_summary[baseline.metric_name]
                current_value = metric_data.get("current", 0)

                if current_value >= baseline.critical_threshold:
                    violations.append({
                        "metric": baseline.metric_name,
                        "severity": "critical",
                        "current_value": current_value,
                        "threshold": baseline.critical_threshold,
                        "description": baseline.description
                    })
                    recommendations.append(f"Reduce {baseline.description} - currently {current_value:.2f}{baseline.unit}")

                elif current_value >= baseline.warning_threshold:
                    violations.append({
                        "metric": baseline.metric_name,
                        "severity": "warning",
                        "current_value": current_value,
                        "threshold": baseline.warning_threshold,
                        "description": baseline.description
                    })
                    recommendations.append(f"Monitor {baseline.description} - approaching threshold at {current_value:.2f}{baseline.unit}")

        # Generate additional recommendations based on patterns
        recommendations.extend(self._generate_pattern_recommendations(metrics_summary))

        report = PerformanceReport(
            timestamp=datetime.now(),
            metrics=metrics_summary,
            baselines={name: {
                "target": b.target_value,
                "warning": b.warning_threshold,
                "critical": b.critical_threshold,
                "unit": b.unit,
                "description": b.description
            } for name, b in self.baselines.items()},
            violations=violations,
            recommendations=recommendations
        )

        self.report_history.append(report)
        return report

    def _generate_pattern_recommendations(self, metrics_summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on metric patterns.

        Args:
            metrics_summary: Current metrics summary

        Returns:
            List of recommendations
        """
        recommendations = []

        # Memory usage patterns
        memory_data = metrics_summary.get("memory_usage", {})
        if memory_data.get("current", 0) > 800:
            recommendations.append("Consider implementing memory cleanup routines")
            recommendations.append("Monitor for memory leaks in long-running sessions")

        # CPU usage patterns
        cpu_data = metrics_summary.get("cpu_usage", {})
        if cpu_data.get("current", 0) > 70:
            recommendations.append("High CPU usage detected - consider optimizing processing")
            recommendations.append("Check for CPU-intensive background tasks")

        # API response times
        api_data = metrics_summary.get("api_response_time", {})
        avg_response = api_data.get("average_5m", 0)
        if avg_response > 10:
            recommendations.append("API response times are elevated - investigate bottlenecks")
            recommendations.append("Consider implementing response time caching")

        # Error rates
        error_data = metrics_summary.get("api_errors_total", {})
        if error_data.get("current", 0) > 5:
            recommendations.append("High error rate detected - check API connectivity")
            recommendations.append("Review error handling and retry logic")

        return recommendations

    def get_recent_reports(self, count: int = 5) -> List[PerformanceReport]:
        """Get recent performance reports.

        Args:
            count: Number of recent reports to return

        Returns:
            List of recent performance reports
        """
        return self.report_history[-count:] if self.report_history else []

    def export_report(self, report: PerformanceReport, file_path: str):
        """Export performance report to file.

        Args:
            report: Performance report to export
            file_path: Path to export file
        """
        try:
            export_data = {
                "timestamp": report.timestamp.isoformat(),
                "summary": {
                    "total_violations": len(report.violations),
                    "critical_violations": len([v for v in report.violations if v["severity"] == "critical"]),
                    "warning_violations": len([v for v in report.violations if v["severity"] == "warning"]),
                    "total_recommendations": len(report.recommendations)
                },
                "metrics": report.metrics,
                "baselines": report.baselines,
                "violations": report.violations,
                "recommendations": report.recommendations
            }

            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            logger.info(f"Performance report exported to {file_path}")

        except Exception as e:
            logger.error(f"Failed to export performance report: {str(e)}")

    def get_performance_score(self) -> float:
        """Calculate overall performance score (0-100).

        Returns:
            Performance score where 100 is perfect
        """
        if not self.baselines:
            return 100.0

        total_score = 0.0
        baseline_count = 0

        for baseline in self.baselines.values():
            metric = metrics_collector.get_metric(baseline.metric_name)
            if not metric:
                continue

            current_value = metric.get_average(5)
            if current_value is None:
                continue

            baseline_count += 1

            # Calculate score for this metric (0-100)
            if current_value <= baseline.target_value:
                score = 100.0
            elif current_value >= baseline.critical_threshold:
                score = 0.0
            else:
                # Linear interpolation between target and critical
                range_size = baseline.critical_threshold - baseline.target_value
                if range_size > 0:
                    distance_from_target = current_value - baseline.target_value
                    score = max(0.0, 100.0 - (distance_from_target / range_size * 100.0))
                else:
                    score = 50.0  # Default if range is invalid

            total_score += score

        return total_score / baseline_count if baseline_count > 0 else 100.0


# Global performance monitor instance
performance_monitor = PerformanceMonitor()