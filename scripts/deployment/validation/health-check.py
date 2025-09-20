#!/usr/bin/env python3
"""
Health Check Script for Personal AI Chatbot
Monitors application health and provides diagnostic information
"""

import os
import sys
import json
import time
import psutil
import requests
import socket
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class HealthChecker:
    """Application health checker"""

    def __init__(self, app_host: str = "127.0.0.1", app_port: int = 7860):
        self.app_host = app_host
        self.app_port = app_port
        self.app_url = f"http://{app_host}:{app_port}"

        self.health_status = {
            "overall": "unknown",
            "checks": {},
            "timestamp": None,
            "uptime": None
        }

    def check_application_status(self) -> Dict[str, Any]:
        """Check if application is running and accessible"""
        result = {
            "status": "down",
            "message": "Application not accessible",
            "details": {}
        }

        # Check if port is listening
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            connection_result = sock.connect_ex((self.app_host, self.app_port))
            sock.close()

            if connection_result == 0:
                result["status"] = "listening"
                result["details"]["port"] = f"Port {self.app_port} is open"
            else:
                result["details"]["port"] = f"Port {self.app_port} is not accessible"
                return result
        except Exception as e:
            result["details"]["port"] = f"Error checking port: {e}"
            return result

        # Check HTTP endpoint
        try:
            response = requests.get(self.app_url, timeout=10)

            if response.status_code == 200:
                result["status"] = "healthy"
                result["message"] = "Application is responding"
                result["details"]["http"] = f"HTTP {response.status_code}"
                result["details"]["response_time"] = ".2f"
            else:
                result["status"] = "unhealthy"
                result["message"] = f"Application returned HTTP {response.status_code}"
                result["details"]["http"] = f"HTTP {response.status_code}"
        except requests.exceptions.RequestException as e:
            result["status"] = "unhealthy"
            result["message"] = f"HTTP request failed: {e}"
            result["details"]["http"] = f"Request failed: {e}"

        return result

    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        result = {
            "status": "unknown",
            "message": "Resource check incomplete",
            "details": {}
        }

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            result["details"]["cpu_usage"] = ".1f"

            if cpu_percent > 90:
                result["status"] = "critical"
                result["message"] = "High CPU usage detected"
            elif cpu_percent > 70:
                result["status"] = "warning"
                result["message"] = "Elevated CPU usage"
            else:
                result["status"] = "healthy"
                result["message"] = "CPU usage normal"

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)

            result["details"]["memory_usage"] = ".1f"
            result["details"]["memory_used"] = ".1f"
            result["details"]["memory_total"] = ".1f"

            if memory_percent > 90:
                result["status"] = "critical"
                result["message"] = "High memory usage detected"
            elif memory_percent > 80:
                if result["status"] != "critical":
                    result["status"] = "warning"
                    result["message"] = "High memory usage detected"

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)

            result["details"]["disk_usage"] = ".1f"
            result["details"]["disk_free"] = ".1f"

            if disk_percent > 95:
                result["status"] = "critical"
                result["message"] = "Very low disk space"
            elif disk_percent > 90:
                if result["status"] not in ["critical"]:
                    result["status"] = "warning"
                    result["message"] = "Low disk space"

            # If no issues found, mark as healthy
            if result["status"] == "unknown":
                result["status"] = "healthy"
                result["message"] = "System resources normal"

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Error checking system resources: {e}"

        return result

    def check_application_process(self) -> Dict[str, Any]:
        """Check application process status"""
        result = {
            "status": "not_found",
            "message": "Application process not found",
            "details": {}
        }

        try:
            # Look for Python processes running the application
            app_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                        cmdline = proc.info['cmdline']
                        if cmdline and any('main.py' in arg for arg in cmdline):
                            app_processes.append({
                                'pid': proc.info['pid'],
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_percent': proc.info['memory_percent'],
                                'cmdline': cmdline
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if app_processes:
                result["status"] = "running"
                result["message"] = f"Found {len(app_processes)} application process(es)"
                result["details"]["processes"] = app_processes

                # Check if any process is using too many resources
                for proc in app_processes:
                    if proc['cpu_percent'] > 80 or proc['memory_percent'] > 80:
                        result["status"] = "warning"
                        result["message"] = "Application process using high resources"
                        break
            else:
                result["details"]["note"] = "No Python processes found running main.py"

        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Error checking processes: {e}"

        return result

    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity to required services"""
        result = {
            "status": "unknown",
            "message": "Network check incomplete",
            "details": {}
        }

        # Test local connectivity
        try:
            socket.create_connection((self.app_host, self.app_port), timeout=5)
            result["details"]["local"] = "Local connection successful"
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Cannot connect locally: {e}"
            return result

        # Test external connectivity (OpenRouter API)
        try:
            response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
            if response.status_code == 200:
                result["details"]["openrouter"] = "OpenRouter API accessible"
            else:
                result["details"]["openrouter"] = f"OpenRouter API returned {response.status_code}"
                result["status"] = "warning"
                result["message"] = "OpenRouter API issue detected"
        except Exception as e:
            result["details"]["openrouter"] = f"Cannot reach OpenRouter API: {e}"
            result["status"] = "warning"
            result["message"] = "External connectivity issue"

        if result["status"] == "unknown":
            result["status"] = "healthy"
            result["message"] = "Network connectivity normal"

        return result

    def check_configuration_files(self) -> Dict[str, Any]:
        """Check configuration file status"""
        result = {
            "status": "unknown",
            "message": "Configuration check incomplete",
            "details": {}
        }

        data_dir = os.getenv('DATA_DIR', './data')

        # Check required directories
        required_dirs = ['config', 'logs', 'conversations']
        missing_dirs = []

        for dir_name in required_dirs:
            dir_path = os.path.join(data_dir, dir_name)
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_name)

        if missing_dirs:
            result["status"] = "error"
            result["message"] = f"Missing directories: {', '.join(missing_dirs)}"
            result["details"]["missing_dirs"] = missing_dirs
        else:
            result["details"]["directories"] = "All required directories present"

        # Check configuration file
        config_file = os.path.join(data_dir, 'config', 'app_config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    json.load(f)
                result["details"]["config_file"] = "Configuration file is valid JSON"
            except Exception as e:
                result["status"] = "error"
                result["message"] = f"Configuration file error: {e}"
        else:
            result["status"] = "warning"
            result["message"] = "Configuration file not found"

        # Check environment file
        env_file = os.path.join(data_dir, '.env')
        if os.path.exists(env_file):
            result["details"]["env_file"] = "Environment file exists"
        else:
            result["details"]["env_file"] = "Environment file not found"

        if result["status"] == "unknown":
            result["status"] = "healthy"
            result["message"] = "Configuration files OK"

        return result

    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        logger.info("Running comprehensive health check...")

        self.health_status["timestamp"] = time.time()

        checks = {
            "application": self.check_application_status,
            "system_resources": self.check_system_resources,
            "application_process": self.check_application_process,
            "network_connectivity": self.check_network_connectivity,
            "configuration": self.check_configuration_files
        }

        for check_name, check_func in checks.items():
            try:
                result = check_func()
                self.health_status["checks"][check_name] = result
                logger.info(f"✓ {check_name}: {result['message']}")
            except Exception as e:
                logger.error(f"✗ {check_name}: Error - {e}")
                self.health_status["checks"][check_name] = {
                    "status": "error",
                    "message": f"Check failed: {e}",
                    "details": {}
                }

        # Determine overall status
        statuses = [check["status"] for check in self.health_status["checks"].values()]

        if "error" in statuses:
            self.health_status["overall"] = "unhealthy"
        elif "critical" in statuses:
            self.health_status["overall"] = "critical"
        elif "warning" in statuses:
            self.health_status["overall"] = "warning"
        else:
            self.health_status["overall"] = "healthy"

        return self.health_status

    def print_report(self):
        """Print health check report"""
        status = self.health_status

        print("\n" + "="*60)
        print("  Personal AI Chatbot Health Check Report")
        print("="*60)
        print(f"Timestamp: {time.ctime(status['timestamp'])}")
        print(f"Overall Status: {status['overall'].upper()}")
        print()

        status_icons = {
            "healthy": "✓",
            "warning": "⚠",
            "critical": "✗",
            "error": "✗",
            "unknown": "?"
        }

        for check_name, check_result in status["checks"].items():
            icon = status_icons.get(check_result["status"], "?")
            print(f"{icon} {check_name.replace('_', ' ').title()}: {check_result['message']}")

            # Show additional details
            for detail_key, detail_value in check_result.get("details", {}).items():
                print(f"    • {detail_key}: {detail_value}")

            print()

        # Recommendations
        recommendations = self._generate_recommendations()
        if recommendations:
            print("RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"  • {rec}")
            print()

        print("="*60)

    def _generate_recommendations(self) -> List[str]:
        """Generate health check recommendations"""
        recommendations = []

        for check_name, check_result in self.health_status["checks"].items():
            status = check_result["status"]

            if check_name == "application" and status in ["down", "unhealthy"]:
                recommendations.append("Check if the application is running and restart if necessary")
                recommendations.append("Review application logs for error messages")

            elif check_name == "system_resources":
                if status == "critical":
                    recommendations.append("High resource usage detected - consider restarting the application")
                    recommendations.append("Check for memory leaks or excessive resource consumption")
                elif status == "warning":
                    recommendations.append("Monitor resource usage closely")

            elif check_name == "application_process" and status == "not_found":
                recommendations.append("Application process not found - start the application")

            elif check_name == "network_connectivity" and status in ["warning", "error"]:
                recommendations.append("Check network connectivity and firewall settings")
                recommendations.append("Verify API keys and external service access")

            elif check_name == "configuration" and status == "error":
                recommendations.append("Fix configuration file issues before restarting")

        if not recommendations:
            recommendations.append("All systems appear healthy - continue monitoring")

        return recommendations


def main():
    parser = argparse.ArgumentParser(description='Check Personal AI Chatbot health')
    parser.add_argument('--host', default='127.0.0.1', help='Application host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=7860, help='Application port (default: 7860)')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--output', help='Save results to JSON file')
    parser.add_argument('--watch', type=int, help='Watch mode - repeat every N seconds')

    args = parser.parse_args()

    checker = HealthChecker(args.host, args.port)

    if args.watch:
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                checker.run_health_check()
                checker.print_report()
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\nStopping health check...")
    else:
        checker.run_health_check()
        checker.print_report()

        if args.json or args.output:
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(checker.health_status, f, indent=2)
                logger.info(f"Results saved to: {args.output}")
            if args.json:
                print(json.dumps(checker.health_status, indent=2))

        # Exit with appropriate code
        overall_status = checker.health_status["overall"]
        if overall_status == "healthy":
            sys.exit(0)
        elif overall_status == "warning":
            sys.exit(1)
        else:  # critical, error, unhealthy
            sys.exit(2)


if __name__ == '__main__':
    main()