# src/monitoring/metrics_collector.py
"""Core metrics collection system for Personal AI Chatbot."""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

from ..utils.logging import logger
from ..utils.events import event_bus, EventType, EventPriority


@dataclass
class MetricPoint:
    """Represents a single metric measurement."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class TimeSeriesMetric:
    """Time series metric with historical data."""
    name: str
    description: str
    unit: str
    points: deque = field(default_factory=lambda: deque(maxlen=1000))
    labels: Dict[str, str] = field(default_factory=dict)

    def add_point(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Add a new metric point."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.points.append(point)

    def get_recent_points(self, minutes: int = 5) -> List[MetricPoint]:
        """Get points from the last N minutes."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [p for p in self.points if p.timestamp >= cutoff]

    def get_average(self, minutes: int = 5) -> Optional[float]:
        """Get average value over the last N minutes."""
        points = self.get_recent_points(minutes)
        if not points:
            return None
        return sum(p.value for p in points) / len(points)

    def get_max(self, minutes: int = 5) -> Optional[float]:
        """Get maximum value over the last N minutes."""
        points = self.get_recent_points(minutes)
        if not points:
            return None
        return max(p.value for p in points)


class MetricsCollector:
    """Central metrics collection system."""

    def __init__(self, collection_interval: int = 30):
        """Initialize metrics collector.

        Args:
            collection_interval: Seconds between metric collections
        """
        self.collection_interval = collection_interval
        self.metrics: Dict[str, TimeSeriesMetric] = {}
        self.is_running = False
        self.collection_thread: Optional[threading.Thread] = None

        # System metrics
        self._init_system_metrics()

        # Application metrics
        self._init_application_metrics()

        logger.info("MetricsCollector initialized")

    def _init_system_metrics(self):
        """Initialize system-level metrics."""
        self.metrics['cpu_usage'] = TimeSeriesMetric(
            name='cpu_usage',
            description='CPU usage percentage',
            unit='percent'
        )

        self.metrics['memory_usage'] = TimeSeriesMetric(
            name='memory_usage',
            description='Memory usage in MB',
            unit='MB'
        )

        self.metrics['disk_usage'] = TimeSeriesMetric(
            name='disk_usage',
            description='Disk usage percentage',
            unit='percent'
        )

        self.metrics['network_connections'] = TimeSeriesMetric(
            name='network_connections',
            description='Active network connections',
            unit='count'
        )

    def _init_application_metrics(self):
        """Initialize application-level metrics."""
        self.metrics['api_response_time'] = TimeSeriesMetric(
            name='api_response_time',
            description='API response time',
            unit='seconds'
        )

        self.metrics['api_requests_total'] = TimeSeriesMetric(
            name='api_requests_total',
            description='Total API requests',
            unit='count'
        )

        self.metrics['api_errors_total'] = TimeSeriesMetric(
            name='api_errors_total',
            description='Total API errors',
            unit='count'
        )

        self.metrics['conversations_active'] = TimeSeriesMetric(
            name='conversations_active',
            description='Active conversations',
            unit='count'
        )

        self.metrics['messages_processed'] = TimeSeriesMetric(
            name='messages_processed',
            description='Messages processed',
            unit='count'
        )

        self.metrics['event_processing_time'] = TimeSeriesMetric(
            name='event_processing_time',
            description='Event processing time',
            unit='seconds'
        )

    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric value."""
        if name not in self.metrics:
            logger.warning(f"Unknown metric: {name}")
            return

        self.metrics[name].add_point(value, labels)

        # Publish event for monitoring systems
        from ..utils.events import Event
        event = Event(
            EventType.SYSTEM_EVENT,
            {
                'event_type': 'metric_recorded',
                'metric_name': name,
                'value': value,
                'labels': labels or {},
                'timestamp': datetime.now().isoformat()
            },
            source="metrics_collector"
        )
        event_bus.publish_sync(event)

    def get_metric(self, name: str) -> Optional[TimeSeriesMetric]:
        """Get a metric by name."""
        return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, TimeSeriesMetric]:
        """Get all metrics."""
        return self.metrics.copy()

    def collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric('cpu_usage', cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            self.record_metric('memory_usage', memory_mb)

            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_metric('disk_usage', disk.percent)

            # Network connections
            connections = len(psutil.net_connections())
            self.record_metric('network_connections', connections)

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {str(e)}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        summary = {}

        for name, metric in self.metrics.items():
            recent_points = metric.get_recent_points(5)  # Last 5 minutes
            if recent_points:
                summary[name] = {
                    'current': recent_points[-1].value,
                    'average_5m': metric.get_average(5),
                    'max_5m': metric.get_max(5),
                    'count_5m': len(recent_points),
                    'unit': metric.unit,
                    'description': metric.description
                }

        return summary

    def start_collection(self):
        """Start automatic metric collection."""
        if self.is_running:
            return

        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        logger.info("Metrics collection started")

    def stop_collection(self):
        """Stop automatic metric collection."""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Metrics collection stopped")

    def _collection_loop(self):
        """Main collection loop."""
        while self.is_running:
            try:
                self.collect_system_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
                time.sleep(self.collection_interval)


# Global metrics collector instance
metrics_collector = MetricsCollector()