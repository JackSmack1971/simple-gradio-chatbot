#!/usr/bin/env python3
"""
Health Check Script for Personal AI Chatbot

This script performs comprehensive health checks on the system and reports
the results. It can be used for monitoring, CI/CD pipelines, and manual checks.

Usage:
    python scripts/health/health_check.py [--verbose] [--json] [--check CHECK_NAME]

Options:
    --verbose, -v    Show detailed output
    --json, -j       Output results in JSON format
    --check CHECK    Run only specific health check
    --help, -h       Show this help message
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from monitoring.health_monitor import health_monitor
from monitoring.metrics_collector import metrics_collector
from monitoring.performance_monitor import performance_monitor
from utils.logging import logger


def run_comprehensive_health_check() -> Dict[str, Any]:
    """Run comprehensive health check suite.

    Returns:
        Dictionary with health check results
    """
    print("🔍 Running Personal AI Chatbot Health Checks...")
    print("=" * 60)

    results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "unknown",
        "checks": {},
        "summary": {}
    }

    # Run all health checks
    health_results = health_monitor.run_all_checks()

    # Categorize results
    healthy_checks = []
    degraded_checks = []
    unhealthy_checks = []

    for name, check in health_results.items():
        results["checks"][name] = {
            "status": check.status,
            "message": check.message,
            "duration_ms": check.duration_ms,
            "timestamp": check.timestamp.isoformat(),
            "details": check.details
        }

        if check.status == "healthy":
            healthy_checks.append(name)
        elif check.status == "degraded":
            degraded_checks.append(name)
        elif check.status == "unhealthy":
            unhealthy_checks.append(name)

    # Determine overall status
    if unhealthy_checks:
        results["overall_status"] = "unhealthy"
    elif degraded_checks:
        results["overall_status"] = "degraded"
    else:
        results["overall_status"] = "healthy"

    # Generate summary
    results["summary"] = {
        "total_checks": len(health_results),
        "healthy": len(healthy_checks),
        "degraded": len(degraded_checks),
        "unhealthy": len(unhealthy_checks),
        "healthy_checks": healthy_checks,
        "degraded_checks": degraded_checks,
        "unhealthy_checks": unhealthy_checks
    }

    # Add performance metrics
    try:
        performance_report = performance_monitor.generate_report()
        results["performance"] = {
            "score": performance_monitor.get_performance_score(),
            "violations_count": len(performance_report.violations),
            "recommendations_count": len(performance_report.recommendations)
        }
    except Exception as e:
        logger.warning(f"Failed to generate performance report: {str(e)}")
        results["performance"] = {"error": str(e)}

    return results


def run_specific_health_check(check_name: str) -> Dict[str, Any]:
    """Run a specific health check.

    Args:
        check_name: Name of the health check to run

    Returns:
        Dictionary with health check result
    """
    print(f"🔍 Running health check: {check_name}")
    print("-" * 40)

    check_result = health_monitor.run_health_check(check_name)

    result = {
        "timestamp": datetime.now().isoformat(),
        "check_name": check_name,
        "status": check_result.status,
        "message": check_result.message,
        "duration_ms": check_result.duration_ms,
        "details": check_result.details
    }

    return result


def print_results(results: Dict[str, Any], verbose: bool = False):
    """Print health check results in human-readable format.

    Args:
        results: Health check results
        verbose: Whether to show detailed output
    """
    status_icons = {
        "healthy": "✅",
        "degraded": "⚠️",
        "unhealthy": "❌",
        "unknown": "❓"
    }

    overall_status = results.get("overall_status", "unknown")
    overall_icon = status_icons.get(overall_status, "❓")

    print(f"\n{overall_icon} Overall Health Status: {overall_status.upper()}")
    print("=" * 60)

    if "summary" in results:
        summary = results["summary"]
        print("📊 Summary:")
        print(f"   Total Checks: {summary['total_checks']}")
        print(f"   ✅ Healthy: {summary['healthy']}")
        print(f"   ⚠️  Degraded: {summary['degraded']}")
        print(f"   ❌ Unhealthy: {summary['unhealthy']}")
        print()

    if "performance" in results and "score" in results["performance"]:
        perf = results["performance"]
        print("⚡ Performance:")
        print(".1f")
        print(f"   Violations: {perf.get('violations_count', 0)}")
        print(f"   Recommendations: {perf.get('recommendations_count', 0)}")
        print()

    if "checks" in results:
        print("🔍 Detailed Check Results:")
        for name, check in results["checks"].items():
            icon = status_icons.get(check["status"], "❓")
            print(f"   {icon} {name}: {check['message']}")

            if verbose and check.get("details"):
                print(f"      Details: {check['details']}")
                print(f"      Duration: {check['duration_ms']:.2f}ms")
            print()

    if "message" in results:
        # Single check result
        icon = status_icons.get(results["status"], "❓")
        print(f"{icon} {results['check_name']}: {results['message']}")

        if results.get("details"):
            print(f"   Details: {results['details']}")

        print(f"   Duration: {results['duration_ms']:.2f}ms")


def main():
    """Main entry point for health check script."""
    parser = argparse.ArgumentParser(
        description="Health Check Script for Personal AI Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )

    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results in JSON format"
    )

    parser.add_argument(
        "--check",
        help="Run only specific health check"
    )

    args = parser.parse_args()

    try:
        if args.check:
            # Run specific health check
            results = run_specific_health_check(args.check)
        else:
            # Run comprehensive health check
            results = run_comprehensive_health_check()

        if args.json:
            # Output JSON
            print(json.dumps(results, indent=2, default=str))
        else:
            # Output human-readable
            print_results(results, args.verbose)

        # Exit with appropriate code
        overall_status = results.get("overall_status") or results.get("status", "unknown")
        if overall_status == "unhealthy":
            sys.exit(1)
        elif overall_status == "degraded":
            sys.exit(2)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()