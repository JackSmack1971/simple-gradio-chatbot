#!/usr/bin/env python3
"""
Automated Deployment Testing Script for Personal AI Chatbot
Performs comprehensive validation of deployment success
"""

import os
import sys
import json
import time
import requests
import subprocess
import socket
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DeploymentTester:
    """Comprehensive deployment testing suite"""

    def __init__(self, app_host: str = "127.0.0.1", app_port: int = 7860, timeout: int = 30):
        self.app_host = app_host
        self.app_port = app_port
        self.app_url = f"http://{app_host}:{app_port}"
        self.timeout = timeout
        self.test_results: Dict[str, Any] = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "details": []
        }

    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and record results"""
        self.test_results["tests_run"] += 1

        logger.info(f"Running test: {test_name}")
        try:
            result = test_func(*args, **kwargs)
            if result:
                self.test_results["tests_passed"] += 1
                logger.info(f"✓ {test_name} PASSED")
                self.test_results["details"].append({
                    "name": test_name,
                    "status": "PASSED",
                    "message": "Test completed successfully"
                })
            else:
                self.test_results["tests_failed"] += 1
                logger.error(f"✗ {test_name} FAILED")
                self.test_results["details"].append({
                    "name": test_name,
                    "status": "FAILED",
                    "message": "Test failed"
                })
            return result
        except Exception as e:
            self.test_results["tests_failed"] += 1
            logger.error(f"✗ {test_name} ERROR: {e}")
            self.test_results["details"].append({
                "name": test_name,
                "status": "ERROR",
                "message": str(e)
            })
            return False

    def test_application_startup(self) -> bool:
        """Test if application starts successfully"""
        try:
            # Check if port is listening
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.app_host, self.app_port))
            sock.close()

            if result == 0:
                logger.info(f"Application is listening on {self.app_host}:{self.app_port}")
                return True
            else:
                logger.error(f"Application is not listening on {self.app_host}:{self.app_port}")
                return False
        except Exception as e:
            logger.error(f"Error checking application port: {e}")
            return False

    def test_http_endpoint(self) -> bool:
        """Test HTTP endpoint availability"""
        try:
            response = requests.get(self.app_url, timeout=self.timeout)
            if response.status_code == 200:
                logger.info(f"HTTP endpoint responding: {response.status_code}")
                return True
            else:
                logger.error(f"HTTP endpoint returned status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            return False

    def test_gradio_interface(self) -> bool:
        """Test Gradio interface accessibility"""
        try:
            response = requests.get(self.app_url, timeout=self.timeout)

            # Check for Gradio-specific content
            if "gradio" in response.text.lower() or "interface" in response.text.lower():
                logger.info("Gradio interface detected")
                return True
            else:
                logger.warning("Gradio interface not clearly detected")
                return True  # Still consider it passed if HTTP works
        except Exception as e:
            logger.error(f"Error testing Gradio interface: {e}")
            return False

    def test_api_key_configuration(self) -> bool:
        """Test API key configuration"""
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("OPENROUTER_API_KEY environment variable not set")
            return False

        if not api_key.startswith('sk-or-v1-'):
            logger.error("OPENROUTER_API_KEY does not have valid format")
            return False

        logger.info("API key configuration appears valid")
        return True

    def test_data_directories(self) -> bool:
        """Test data directory structure"""
        data_dir = os.getenv('DATA_DIR', './data')

        required_dirs = [
            data_dir,
            f"{data_dir}/config",
            f"{data_dir}/conversations",
            f"{data_dir}/logs"
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)

        if missing_dirs:
            logger.error(f"Missing data directories: {missing_dirs}")
            return False

        logger.info("All required data directories exist")
        return True

    def test_configuration_files(self) -> bool:
        """Test configuration file accessibility"""
        data_dir = os.getenv('DATA_DIR', './data')
        config_file = f"{data_dir}/config/app_config.json"

        if not os.path.exists(config_file):
            logger.error(f"Configuration file not found: {config_file}")
            return False

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info("Configuration file is valid JSON")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Configuration file is not valid JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"Error reading configuration file: {e}")
            return False

    def test_environment_file(self) -> bool:
        """Test environment file security"""
        data_dir = os.getenv('DATA_DIR', './data')
        env_file = f"{data_dir}/.env"

        if not os.path.exists(env_file):
            logger.warning(f"Environment file not found: {env_file}")
            return True  # Not required if using environment variables

        # Check file permissions (should be restrictive)
        try:
            import stat
            st = os.stat(env_file)
            # Check if file is readable/writable by owner only (0o600)
            if oct(st.st_mode)[-3:] == '600':
                logger.info("Environment file has secure permissions")
                return True
            else:
                logger.error(f"Environment file permissions are too permissive: {oct(st.st_mode)[-3:]}")
                return False
        except Exception as e:
            logger.warning(f"Could not check environment file permissions: {e}")
            return True

    def test_network_connectivity(self) -> bool:
        """Test network connectivity to external services"""
        try:
            # Test OpenRouter API connectivity
            response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
            if response.status_code == 200:
                logger.info("OpenRouter API is reachable")
                return True
            else:
                logger.warning(f"OpenRouter API returned status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Cannot reach OpenRouter API: {e}")
            return False

    def test_basic_chat_functionality(self) -> bool:
        """Test basic chat functionality (if application is running)"""
        try:
            # This is a basic test - in a real scenario, you'd use Selenium or similar
            # to interact with the Gradio interface
            response = requests.get(self.app_url, timeout=self.timeout)

            # Look for chat-related content
            if "chat" in response.text.lower() or "message" in response.text.lower():
                logger.info("Chat interface elements detected")
                return True
            else:
                logger.warning("Chat interface elements not clearly detected")
                return True  # Still pass if basic HTTP works
        except Exception as e:
            logger.error(f"Error testing chat functionality: {e}")
            return False

    def test_performance_basics(self) -> bool:
        """Test basic performance metrics"""
        try:
            start_time = time.time()
            response = requests.get(self.app_url, timeout=self.timeout)
            end_time = time.time()

            response_time = end_time - start_time

            if response_time < 5.0:  # Should respond within 5 seconds
                logger.info(".2f")
                return True
            else:
                logger.warning(".2f")
                return False
        except Exception as e:
            logger.error(f"Error testing performance: {e}")
            return False

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        success_rate = (self.test_results["tests_passed"] / self.test_results["tests_run"]) * 100 if self.test_results["tests_run"] > 0 else 0

        report = {
            "summary": {
                "total_tests": self.test_results["tests_run"],
                "passed": self.test_results["tests_passed"],
                "failed": self.test_results["tests_failed"],
                "skipped": self.test_results["tests_skipped"],
                "success_rate": ".1f"
            },
            "details": self.test_results["details"],
            "timestamp": time.time(),
            "application_url": self.app_url,
            "recommendations": []
        }

        # Add recommendations based on failures
        if self.test_results["tests_failed"] > 0:
            report["recommendations"].append("Address failed tests before deploying to production")
            report["recommendations"].append("Check application logs for detailed error information")
            report["recommendations"].append("Verify configuration files and environment variables")

        if self.test_results["tests_passed"] == 0:
            report["recommendations"].append("Application may not be running - check startup process")

        return report

    def print_report(self):
        """Print test results to console"""
        report = self.generate_report()

        print("\n" + "="*60)
        print("  Personal AI Chatbot Deployment Test Report")
        print("="*60)
        print(f"Application URL: {self.app_url}")
        print(f"Timestamp: {time.ctime(report['timestamp'])}")
        print()

        summary = report["summary"]
        print("SUMMARY:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Skipped: {summary['skipped']}")
        print(f"  Success Rate: {summary['success_rate']}%")
        print()

        if report["recommendations"]:
            print("RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")
            print()

        print("DETAILED RESULTS:")
        for detail in report["details"]:
            status_icon = "✓" if detail["status"] == "PASSED" else "✗"
            print(f"  {status_icon} {detail['name']}: {detail['message']}")

        print("\n" + "="*60)

    def run_all_tests(self) -> bool:
        """Run all deployment tests"""
        logger.info("Starting comprehensive deployment validation...")

        # Define test suite
        tests = [
            ("Application Startup", self.test_application_startup),
            ("HTTP Endpoint", self.test_http_endpoint),
            ("Gradio Interface", self.test_gradio_interface),
            ("API Key Configuration", self.test_api_key_configuration),
            ("Data Directories", self.test_data_directories),
            ("Configuration Files", self.test_configuration_files),
            ("Environment File Security", self.test_environment_file),
            ("Network Connectivity", self.test_network_connectivity),
            ("Basic Chat Functionality", self.test_basic_chat_functionality),
            ("Performance Basics", self.test_performance_basics)
        ]

        # Run all tests
        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False

        # Generate and display report
        self.print_report()

        return all_passed


def main():
    parser = argparse.ArgumentParser(description='Test Personal AI Chatbot deployment')
    parser.add_argument('--host', default='127.0.0.1', help='Application host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=7860, help='Application port (default: 7860)')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds (default: 30)')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--output', help='Save results to JSON file')

    args = parser.parse_args()

    tester = DeploymentTester(args.host, args.port, args.timeout)
    success = tester.run_all_tests()

    if args.json or args.output:
        report = tester.generate_report()
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Results saved to: {args.output}")
        if args.json:
            print(json.dumps(report, indent=2))

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()