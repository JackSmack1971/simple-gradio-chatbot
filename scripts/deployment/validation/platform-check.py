#!/usr/bin/env python3
"""
Platform Compatibility Check Script for Personal AI Chatbot
Validates platform-specific requirements and compatibility
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PlatformChecker:
    """Platform compatibility checker"""

    def __init__(self):
        self.system = platform.system().lower()
        self.machine = platform.machine().lower()
        self.version = platform.version()
        self.python_version = sys.version_info

        self.check_results: Dict[str, Any] = {
            "platform_info": {
                "system": self.system,
                "machine": self.machine,
                "version": self.version,
                "python_version": f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}"
            },
            "compatibility": {},
            "requirements": {},
            "recommendations": []
        }

    def check_python_version(self) -> Tuple[bool, str]:
        """Check Python version compatibility"""
        min_version = (3, 9, 0)
        current_version = (self.python_version.major, self.python_version.minor, self.python_version.micro)

        if current_version >= min_version:
            return True, f"Python {current_version[0]}.{current_version[1]} is compatible"
        else:
            return False, f"Python {current_version[0]}.{current_version[1]} is too old. Minimum required: {min_version[0]}.{min_version[1]}.{min_version[2]}"

    def check_system_requirements(self) -> Tuple[bool, str]:
        """Check system requirements"""
        if self.system == "windows":
            return self._check_windows_requirements()
        elif self.system == "linux":
            return self._check_linux_requirements()
        elif self.system == "darwin":
            return self._check_macos_requirements()
        else:
            return False, f"Unsupported operating system: {self.system}"

    def _check_windows_requirements(self) -> Tuple[bool, str]:
        """Check Windows-specific requirements"""
        # Check Windows version
        version_info = platform.version().split('.')
        if len(version_info) >= 2:
            major, minor = int(version_info[0]), int(version_info[1])
            if major >= 10:
                version_msg = "Windows 10+ detected - compatible"
            elif major == 6 and minor >= 1:
                version_msg = "Windows 7/8 detected - may have limited compatibility"
            else:
                return False, "Windows version too old (minimum: Windows 7)"
        else:
            version_msg = "Could not determine Windows version"

        # Check architecture
        if "64" in self.machine:
            arch_msg = "64-bit architecture detected"
        else:
            arch_msg = "32-bit architecture - 64-bit recommended"

        return True, f"{version_msg}. {arch_msg}"

    def _check_linux_requirements(self) -> Tuple[bool, str]:
        """Check Linux-specific requirements"""
        try:
            # Try to detect distribution
            with open('/etc/os-release', 'r') as f:
                os_release = f.read()

            if 'ubuntu' in os_release.lower():
                return True, "Ubuntu detected - compatible"
            elif 'centos' in os_release.lower() or 'rhel' in os_release.lower():
                return True, "CentOS/RHEL detected - compatible"
            elif 'fedora' in os_release.lower():
                return True, "Fedora detected - compatible"
            elif 'debian' in os_release.lower():
                return True, "Debian detected - compatible"
            else:
                return True, "Linux distribution detected - should be compatible"
        except:
            return True, "Linux system detected - compatibility assumed"

    def _check_macos_requirements(self) -> Tuple[bool, str]:
        """Check macOS-specific requirements"""
        version_parts = platform.mac_ver()[0].split('.')
        if len(version_parts) >= 2:
            major, minor = int(version_parts[0]), int(version_parts[1])
            if major >= 11:
                return True, f"macOS {major}.{minor} detected - compatible"
            elif major == 10 and minor >= 15:
                return True, f"macOS {major}.{minor} detected - compatible (Catalina or later)"
            else:
                return False, f"macOS {major}.{minor} is too old (minimum: 10.15 Catalina)"

        return True, "macOS detected - version could not be determined"

    def check_dependencies(self) -> Tuple[bool, str]:
        """Check for required Python dependencies"""
        required_packages = [
            'gradio',
            'openai',
            'python-dotenv',
            'requests',
            'cryptography'
        ]

        missing_packages = []
        outdated_packages = []

        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
            except Exception as e:
                logger.warning(f"Error importing {package}: {e}")

        if missing_packages:
            return False, f"Missing required packages: {', '.join(missing_packages)}"
        else:
            return True, "All required packages are available"

    def check_disk_space(self) -> Tuple[bool, str]:
        """Check available disk space"""
        try:
            # Get current directory's disk usage
            try:
                # Try Unix-like systems first
                statvfs = os.statvfs('.')
                free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
            except AttributeError:
                # Fall back to Windows/shutil
                import shutil
                total, used, free = shutil.disk_usage('.')
                free_space_gb = free / (1024**3)

            if free_space_gb >= 1.0:
                return True, ".1f"
            else:
                return False, ".1f"
        except:
            return True, "Could not determine disk space (assuming sufficient)"

    def check_memory(self) -> Tuple[bool, str]:
        """Check available memory"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)

            if available_gb >= 2.0:
                return True, ".1f"
            elif available_gb >= 1.0:
                return True, ".1f"
            else:
                return False, ".1f"
        except ImportError:
            return True, "Memory check requires psutil (install with: pip install psutil)"
        except:
            return True, "Could not determine memory (assuming sufficient)"

    def check_network_connectivity(self) -> Tuple[bool, str]:
        """Check network connectivity"""
        try:
            import urllib.request
            urllib.request.urlopen('https://openrouter.ai', timeout=10)
            return True, "Network connectivity to OpenRouter API confirmed"
        except:
            return False, "Cannot reach OpenRouter API - check internet connection"

    def check_firewall_settings(self) -> Tuple[bool, str]:
        """Check firewall settings for application port"""
        app_port = os.getenv('APP_PORT', '7860')

        if self.system == "windows":
            return self._check_windows_firewall(int(app_port))
        elif self.system == "linux":
            return self._check_linux_firewall(int(app_port))
        elif self.system == "darwin":
            return self._check_macos_firewall(int(app_port))
        else:
            return True, "Firewall check not implemented for this platform"

    def _check_windows_firewall(self, port: int) -> Tuple[bool, str]:
        """Check Windows firewall settings"""
        try:
            result = subprocess.run(
                ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
                capture_output=True, text=True, timeout=10
            )

            if f"LocalPort:{port}" in result.stdout:
                return True, f"Port {port} appears to be allowed in Windows Firewall"
            else:
                return False, f"Port {port} may be blocked by Windows Firewall"
        except:
            return True, "Could not check Windows Firewall settings"

    def _check_linux_firewall(self, port: int) -> Tuple[bool, str]:
        """Check Linux firewall settings"""
        try:
            # Try ufw first
            result = subprocess.run(
                ['ufw', 'status'], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and str(port) in result.stdout:
                return True, f"Port {port} appears to be allowed in UFW"
        except:
            pass

        try:
            # Try firewalld
            result = subprocess.run(
                ['firewall-cmd', '--list-ports'], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and f"{port}/tcp" in result.stdout:
                return True, f"Port {port} appears to be allowed in firewalld"
        except:
            pass

        return True, "Could not determine firewall status (assuming port is accessible)"

    def _check_macos_firewall(self, port: int) -> Tuple[bool, str]:
        """Check macOS firewall settings"""
        try:
            result = subprocess.run(
                ['/usr/libexec/ApplicationFirewall/socketfilterfw', '--getglobalstate'],
                capture_output=True, text=True, timeout=5
            )

            if "Firewall is enabled" in result.stdout:
                return True, "macOS firewall is enabled - check if application is allowed"
            else:
                return True, "macOS firewall is disabled"
        except:
            return True, "Could not check macOS firewall status"

    def generate_report(self) -> Dict[str, Any]:
        """Generate platform compatibility report"""
        return {
            "platform_info": self.check_results["platform_info"],
            "compatibility_checks": self.check_results["compatibility"],
            "requirements": self.check_results["requirements"],
            "recommendations": self.check_results["recommendations"],
            "overall_compatible": all(
                check.get("compatible", True)
                for check in self.check_results["compatibility"].values()
            )
        }

    def print_report(self):
        """Print compatibility report"""
        report = self.generate_report()

        print("\n" + "="*60)
        print("  Personal AI Chatbot Platform Compatibility Report")
        print("="*60)

        # Platform info
        info = report["platform_info"]
        print(f"Platform: {info['system'].title()} {info['machine']}")
        print(f"Python Version: {info['python_version']}")
        print()

        # Compatibility checks
        print("COMPATIBILITY CHECKS:")
        for check_name, check_info in report["compatibility_checks"].items():
            status = "✓" if check_info["compatible"] else "✗"
            print(f"  {status} {check_name}: {check_info['message']}")

        print()

        # Requirements
        if report["requirements"]:
            print("REQUIREMENTS:")
            for req_name, req_info in report["requirements"].items():
                status = "✓" if req_info["met"] else "✗"
                print(f"  {status} {req_name}: {req_info['message']}")

        print()

        # Recommendations
        if report["recommendations"]:
            print("RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")

        print()

        # Overall status
        if report["overall_compatible"]:
            print("✓ PLATFORM STATUS: COMPATIBLE")
            print("This platform should work with Personal AI Chatbot.")
        else:
            print("✗ PLATFORM STATUS: INCOMPATIBLE")
            print("This platform may have compatibility issues.")

        print("\n" + "="*60)

    def run_all_checks(self) -> bool:
        """Run all platform compatibility checks"""
        logger.info("Running platform compatibility checks...")

        checks = [
            ("Python Version", self.check_python_version),
            ("System Requirements", self.check_system_requirements),
            ("Dependencies", self.check_dependencies),
            ("Disk Space", self.check_disk_space),
            ("Memory", self.check_memory),
            ("Network Connectivity", self.check_network_connectivity),
            ("Firewall Settings", self.check_firewall_settings)
        ]

        all_compatible = True

        for check_name, check_func in checks:
            try:
                compatible, message = check_func()
                self.check_results["compatibility"][check_name] = {
                    "compatible": compatible,
                    "message": message
                }

                if not compatible:
                    all_compatible = False

                logger.info(f"{'✓' if compatible else '✗'} {check_name}: {message}")

            except Exception as e:
                logger.error(f"Error running {check_name}: {e}")
                self.check_results["compatibility"][check_name] = {
                    "compatible": False,
                    "message": f"Check failed: {e}"
                }
                all_compatible = False

        # Generate recommendations
        self._generate_recommendations()

        self.print_report()
        return all_compatible

    def _generate_recommendations(self):
        """Generate platform-specific recommendations"""
        recommendations = []

        # Python version recommendations
        if self.python_version < (3, 9):
            recommendations.append("Upgrade to Python 3.9 or later for best compatibility")

        # System-specific recommendations
        if self.system == "windows":
            recommendations.append("Ensure Windows Firewall allows the application port")
            if "32" in self.machine:
                recommendations.append("Consider upgrading to 64-bit Windows for better performance")
        elif self.system == "linux":
            recommendations.append("Ensure firewall (ufw/firewalld) allows the application port")
        elif self.system == "darwin":
            recommendations.append("Ensure macOS firewall allows the application")

        # Memory recommendations
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.available / (1024**3) < 2.0:
                recommendations.append("Consider adding more RAM (4GB recommended) for better performance")
        except:
            pass

        self.check_results["recommendations"] = recommendations


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Check platform compatibility for Personal AI Chatbot')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--output', help='Save results to JSON file')

    args = parser.parse_args()

    checker = PlatformChecker()
    compatible = checker.run_all_checks()

    if args.json or args.output:
        report = checker.generate_report()
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Results saved to: {args.output}")
        if args.json:
            print(json.dumps(report, indent=2))

    sys.exit(0 if compatible else 1)


if __name__ == '__main__':
    main()