# src/monitoring/dashboard.py
"""Monitoring dashboard for Personal AI Chatbot."""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.logging import logger
from .metrics_collector import metrics_collector
from .health_monitor import health_monitor
from .alert_manager import alert_manager
from .performance_monitor import performance_monitor


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    title: str = "Personal AI Chatbot - SRE Dashboard"
    refresh_interval: int = 30  # seconds
    max_history_points: int = 100
    enable_real_time: bool = True
    theme: str = "dark"


@dataclass
class SLODefinition:
    """Service Level Objective definition."""
    name: str
    description: str
    metric_name: str
    target_percentage: float  # e.g., 99.9 for 99.9%
    time_window_days: int = 30
    current_value: float = 0.0
    status: str = "unknown"  # 'meeting', 'warning', 'breach'


@dataclass
class ErrorBudget:
    """Error budget tracking."""
    slo_name: str
    total_budget_minutes: float
    consumed_minutes: float = 0.0
    remaining_minutes: float = 0.0
    percentage_consumed: float = 0.0
    status: str = "healthy"  # 'healthy', 'warning', 'exhausted'


class MonitoringDashboard:
    """Comprehensive monitoring dashboard."""

    def __init__(self, config: Optional[DashboardConfig] = None):
        """Initialize monitoring dashboard.

        Args:
            config: Dashboard configuration
        """
        self.config = config or DashboardConfig()
        self.slos: Dict[str, SLODefinition] = {}
        self.error_budgets: Dict[str, ErrorBudget] = {}

        # Initialize SLOs based on performance baselines
        self._initialize_slos()

        logger.info("MonitoringDashboard initialized")

    def _initialize_slos(self):
        """Initialize Service Level Objectives."""
        # Response time SLOs
        self.slos["api_response_time_99"] = SLODefinition(
            name="API Response Time 99%",
            description="99% of API responses should be under 8 seconds",
            metric_name="api_response_time",
            target_percentage=99.0,
            time_window_days=30
        )

        self.slos["api_response_time_95"] = SLODefinition(
            name="API Response Time 95%",
            description="95% of API responses should be under 15 seconds",
            metric_name="api_response_time",
            target_percentage=95.0,
            time_window_days=30
        )

        # Error rate SLOs
        self.slos["api_error_rate"] = SLODefinition(
            name="API Error Rate",
            description="API error rate should be below 5%",
            metric_name="api_errors_total",
            target_percentage=95.0,  # 95% success rate = 5% error rate
            time_window_days=30
        )

        # System availability SLO
        self.slos["system_availability"] = SLODefinition(
            name="System Availability",
            description="System should be available 99.5% of the time",
            metric_name="system_uptime",
            target_percentage=99.5,
            time_window_days=30
        )

        # Initialize error budgets
        for slo_name in self.slos.keys():
            self._initialize_error_budget(slo_name)

    def _initialize_error_budget(self, slo_name: str):
        """Initialize error budget for an SLO.

        Args:
            slo_name: Name of the SLO
        """
        slo = self.slos[slo_name]
        total_minutes = slo.time_window_days * 24 * 60
        budget_minutes = total_minutes * (1.0 - slo.target_percentage / 100.0)

        self.error_budgets[slo_name] = ErrorBudget(
            slo_name=slo_name,
            total_budget_minutes=budget_minutes,
            remaining_minutes=budget_minutes
        )

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data.

        Returns:
            Dictionary containing all dashboard data
        """
        # Get current metrics
        metrics_summary = metrics_collector.get_metrics_summary()

        # Get health status
        health_summary = health_monitor.get_health_summary()

        # Get active alerts
        active_alerts = alert_manager.get_active_alerts()

        # Get performance report
        performance_report = performance_monitor.generate_report()

        # Update SLOs and error budgets
        self._update_slos_and_budgets()

        # Generate dashboard data
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "title": self.config.title,
                "refresh_interval": self.config.refresh_interval,
                "theme": self.config.theme
            },
            "summary": {
                "overall_health": health_summary["overall_status"],
                "active_alerts_count": len(active_alerts),
                "performance_score": performance_monitor.get_performance_score(),
                "total_slo_violations": sum(1 for slo in self.slos.values() if slo.status in ["warning", "breach"])
            },
            "metrics": metrics_summary,
            "health": health_summary,
            "alerts": {
                "active": list(active_alerts.values()),
                "recent_history": alert_manager.get_alert_history(hours=24)
            },
            "performance": {
                "current_score": performance_monitor.get_performance_score(),
                "violations": performance_report.violations,
                "recommendations": performance_report.recommendations,
                "recent_reports": len(performance_monitor.get_recent_reports(5))
            },
            "slos": {
                slo_name: {
                    "name": slo.name,
                    "description": slo.description,
                    "target_percentage": slo.target_percentage,
                    "current_value": slo.current_value,
                    "status": slo.status,
                    "time_window_days": slo.time_window_days
                }
                for slo_name, slo in self.slos.items()
            },
            "error_budgets": {
                budget_name: {
                    "slo_name": budget.slo_name,
                    "total_budget_minutes": budget.total_budget_minutes,
                    "consumed_minutes": budget.consumed_minutes,
                    "remaining_minutes": budget.remaining_minutes,
                    "percentage_consumed": budget.percentage_consumed,
                    "status": budget.status
                }
                for budget_name, budget in self.error_budgets.items()
            }
        }

        return dashboard_data

    def _update_slos_and_budgets(self):
        """Update SLO status and error budgets."""
        for slo_name, slo in self.slos.items():
            self._update_slo_status(slo)
            self._update_error_budget(slo_name, slo)

    def _update_slo_status(self, slo: SLODefinition):
        """Update SLO status based on current metrics.

        Args:
            slo: SLO definition to update
        """
        # This is a simplified implementation
        # In production, this would analyze historical data
        metric = metrics_collector.get_metric(slo.metric_name)
        if not metric:
            slo.status = "unknown"
            return

        # Get data from last time window
        recent_points = metric.get_recent_points(slo.time_window_days * 24 * 60)  # Convert days to minutes
        if not recent_points:
            slo.status = "unknown"
            return

        # Calculate current performance percentage
        if slo.metric_name == "api_response_time":
            # For response time, calculate percentage within target
            target_responses = sum(1 for p in recent_points if p.value <= 8.0)  # 8 seconds target
            slo.current_value = (target_responses / len(recent_points)) * 100
        elif slo.metric_name == "api_errors_total":
            # For error rate, calculate success percentage
            total_requests = len(recent_points)
            error_requests = sum(1 for p in recent_points if p.value > 0)
            slo.current_value = ((total_requests - error_requests) / total_requests) * 100
        elif slo.metric_name == "system_uptime":
            # Simplified uptime calculation
            slo.current_value = 99.9  # Placeholder

        # Determine status
        if slo.current_value >= slo.target_percentage:
            slo.status = "meeting"
        elif slo.current_value >= slo.target_percentage * 0.95:  # Within 5% of target
            slo.status = "warning"
        else:
            slo.status = "breach"

    def _update_error_budget(self, slo_name: str, slo: SLODefinition):
        """Update error budget based on SLO performance.

        Args:
            slo_name: Name of the SLO
            slo: SLO definition
        """
        if slo_name not in self.error_budgets:
            return

        budget = self.error_budgets[slo_name]

        # Calculate consumed budget based on SLO violation
        if slo.status == "breach":
            # Full budget consumption for breach
            budget.consumed_minutes = budget.total_budget_minutes
        elif slo.status == "warning":
            # Partial budget consumption for warning
            budget.consumed_minutes = budget.total_budget_minutes * 0.7
        else:
            # Minimal consumption when meeting SLO
            budget.consumed_minutes = budget.total_budget_minutes * 0.1

        budget.remaining_minutes = budget.total_budget_minutes - budget.consumed_minutes
        budget.percentage_consumed = (budget.consumed_minutes / budget.total_budget_minutes) * 100

        # Update status
        if budget.percentage_consumed >= 100:
            budget.status = "exhausted"
        elif budget.percentage_consumed >= 80:
            budget.status = "warning"
        else:
            budget.status = "healthy"

    def export_dashboard(self, file_path: str):
        """Export dashboard data to file.

        Args:
            file_path: Path to export file
        """
        try:
            dashboard_data = self.get_dashboard_data()

            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)

            logger.info(f"Dashboard data exported to {file_path}")

        except Exception as e:
            logger.error(f"Failed to export dashboard: {str(e)}")

    def get_slo_status_summary(self) -> Dict[str, Any]:
        """Get SLO status summary.

        Returns:
            Dictionary with SLO status summary
        """
        total_slos = len(self.slos)
        meeting_slos = sum(1 for slo in self.slos.values() if slo.status == "meeting")
        warning_slos = sum(1 for slo in self.slos.values() if slo.status == "warning")
        breach_slos = sum(1 for slo in self.slos.values() if slo.status == "breach")

        return {
            "total_slos": total_slos,
            "meeting_slos": meeting_slos,
            "warning_slos": warning_slos,
            "breach_slos": breach_slos,
            "overall_slo_compliance": (meeting_slos / total_slos) * 100 if total_slos > 0 else 100
        }

    def get_error_budget_summary(self) -> Dict[str, Any]:
        """Get error budget summary.

        Returns:
            Dictionary with error budget summary
        """
        total_budgets = len(self.error_budgets)
        healthy_budgets = sum(1 for budget in self.error_budgets.values() if budget.status == "healthy")
        warning_budgets = sum(1 for budget in self.error_budgets.values() if budget.status == "warning")
        exhausted_budgets = sum(1 for budget in self.error_budgets.values() if budget.status == "exhausted")

        return {
            "total_budgets": total_budgets,
            "healthy_budgets": healthy_budgets,
            "warning_budgets": warning_budgets,
            "exhausted_budgets": exhausted_budgets,
            "overall_budget_health": (healthy_budgets / total_budgets) * 100 if total_budgets > 0 else 100
        }


# Global dashboard instance
monitoring_dashboard = MonitoringDashboard()