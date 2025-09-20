#!/usr/bin/env python3
"""
Backup Validation Script for Personal AI Chatbot

This script validates backup integrity and performs restoration tests to ensure
backups are usable in case of emergency.

Usage:
    python scripts/backup/validate_backup.py [--backup FILE] [--test-restore] [--comprehensive]

Options:
    --backup FILE     Specific backup file to validate (default: latest)
    --test-restore    Perform test restoration
    --comprehensive   Run comprehensive validation including data integrity
    --help, -h        Show this help message
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Ensure project root is on the path for package imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging import logger


class BackupValidator:
    """Validates backup integrity and usability."""

    def __init__(self, backup_dir: str = "data/backups"):
        """Initialize backup validator.

        Args:
            backup_dir: Directory containing backups
        """
        self.backup_dir = Path(backup_dir)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="backup_validation_"))

        logger.info(f"BackupValidator initialized (temp dir: {self.temp_dir})")

    def __del__(self):
        """Cleanup temporary directory."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {str(e)}")

    def validate_backup(self, backup_path: Optional[str] = None,
                       test_restore: bool = False,
                       comprehensive: bool = False) -> Dict[str, Any]:
        """Validate a backup archive.

        Args:
            backup_path: Path to backup file (default: latest)
            test_restore: Whether to perform test restoration
            comprehensive: Whether to run comprehensive validation

        Returns:
            Validation results dictionary
        """
        # Find backup file
        if backup_path:
            backup_file = Path(backup_path)
        else:
            backup_file = self._find_latest_backup()

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        logger.info(f"Validating backup: {backup_file}")

        results = {
            "backup_file": str(backup_file),
            "validation_time": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "unknown",
            "recommendations": []
        }

        try:
            # Basic integrity check
            results["tests"]["integrity"] = self._check_integrity(backup_file)

            # Archive structure validation
            results["tests"]["structure"] = self._validate_structure(backup_file)

            # Metadata validation
            results["tests"]["metadata"] = self._validate_metadata(backup_file)

            if test_restore:
                # Test restoration
                results["tests"]["restoration"] = self._test_restoration(backup_file)

            if comprehensive:
                # Comprehensive data validation
                results["tests"]["data_integrity"] = self._validate_data_integrity(backup_file)

            # Determine overall status
            test_results = [test["status"] for test in results["tests"].values()]
            if all(status == "passed" for status in test_results):
                results["overall_status"] = "healthy"
            elif any(status == "failed" for status in test_results):
                results["overall_status"] = "unhealthy"
            else:
                results["overall_status"] = "degraded"

            # Generate recommendations
            results["recommendations"] = self._generate_recommendations(results)

            logger.info(f"Validation completed: {results['overall_status']}")
            return results

        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            results["overall_status"] = "error"
            results["error"] = str(e)
            return results

    def _find_latest_backup(self) -> Path:
        """Find the latest backup file.

        Returns:
            Path to latest backup file
        """
        backup_files = list(self.backup_dir.glob("*.tar.gz"))
        if not backup_files:
            raise FileNotFoundError("No backup files found")

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return backup_files[0]

    def _check_integrity(self, backup_file: Path) -> Dict[str, Any]:
        """Check basic archive integrity.

        Args:
            backup_file: Path to backup file

        Returns:
            Integrity check results
        """
        import tarfile

        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                # Test archive readability
                members = tar.getmembers()

                # Check for corrupted files
                corrupted_files = []
                for member in members:
                    try:
                        # Try to read file info
                        tar.getmember(member.name)
                    except Exception as e:
                        corrupted_files.append(member.name)

                result = {
                    "status": "passed" if not corrupted_files else "failed",
                    "total_files": len(members),
                    "corrupted_files": corrupted_files,
                    "archive_size_mb": round(backup_file.stat().st_size / (1024 * 1024), 2)
                }

                if corrupted_files:
                    result["message"] = f"Found {len(corrupted_files)} corrupted files"
                else:
                    result["message"] = f"Archive integrity OK ({len(members)} files)"

                return result

        except Exception as e:
            return {
                "status": "failed",
                "message": f"Integrity check failed: {str(e)}"
            }

    def _validate_structure(self, backup_file: Path) -> Dict[str, Any]:
        """Validate backup archive structure.

        Args:
            backup_file: Path to backup file

        Returns:
            Structure validation results
        """
        import tarfile

        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                members = tar.getmembers()
                file_paths = [m.name for m in members]

                # Expected structure
                expected_dirs = [
                    "data/conversations",
                    "data/cache",
                    "config"
                ]

                missing_dirs = []
                for expected_dir in expected_dirs:
                    if not any(path.startswith(expected_dir) for path in file_paths):
                        missing_dirs.append(expected_dir)

                result = {
                    "status": "passed" if not missing_dirs else "failed",
                    "total_files": len(file_paths),
                    "missing_directories": missing_dirs,
                    "top_level_dirs": list(set(path.split('/')[0] for path in file_paths if '/' in path))
                }

                if missing_dirs:
                    result["message"] = f"Missing expected directories: {missing_dirs}"
                else:
                    result["message"] = "Archive structure is valid"

                return result

        except Exception as e:
            return {
                "status": "failed",
                "message": f"Structure validation failed: {str(e)}"
            }

    def _validate_metadata(self, backup_file: Path) -> Dict[str, Any]:
        """Validate backup metadata.

        Args:
            backup_file: Path to backup file

        Returns:
            Metadata validation results
        """
        metadata_file = backup_file.with_suffix(".metadata.json")

        if not metadata_file.exists():
            return {
                "status": "failed",
                "message": "Metadata file not found"
            }

        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Validate required fields
            required_fields = ["backup_name", "backup_type", "created_at", "size_bytes"]
            missing_fields = [field for field in required_fields if field not in metadata]

            if missing_fields:
                return {
                    "status": "failed",
                    "message": f"Missing metadata fields: {missing_fields}"
                }

            # Validate backup type
            valid_types = ["full", "incremental", "config"]
            if metadata.get("backup_type") not in valid_types:
                return {
                    "status": "failed",
                    "message": f"Invalid backup type: {metadata.get('backup_type')}"
                }

            # Validate size matches
            actual_size = backup_file.stat().st_size
            metadata_size = metadata.get("size_bytes", 0)

            if abs(actual_size - metadata_size) > 1024:  # Allow 1KB difference
                return {
                    "status": "failed",
                    "message": f"Size mismatch: metadata={metadata_size}, actual={actual_size}"
                }

            return {
                "status": "passed",
                "message": "Metadata validation successful",
                "backup_type": metadata.get("backup_type"),
                "created_at": metadata.get("created_at")
            }

        except Exception as e:
            return {
                "status": "failed",
                "message": f"Metadata validation failed: {str(e)}"
            }

    def _test_restoration(self, backup_file: Path) -> Dict[str, Any]:
        """Test backup restoration.

        Args:
            backup_file: Path to backup file

        Returns:
            Restoration test results
        """
        import tarfile

        restore_temp_dir = self.temp_dir / "restore_test"
        restore_temp_dir.mkdir(exist_ok=True)

        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                # Extract a few key files for testing
                members = tar.getmembers()

                # Test extraction of first few files
                test_files = []
                for member in members[:10]:  # Test first 10 files
                    if member.isfile():
                        try:
                            tar.extract(member, str(restore_temp_dir), set_attrs=False)
                            extracted_file = restore_temp_dir / member.name

                            if extracted_file.exists() and extracted_file.stat().st_size > 0:
                                test_files.append(member.name)
                            else:
                                logger.warning(f"Extracted file is empty or missing: {member.name}")

                        except Exception as e:
                            logger.warning(f"Failed to extract {member.name}: {str(e)}")

                # Test configuration file parsing
                config_test_passed = False
                for root, dirs, files in os.walk(str(restore_temp_dir)):
                    for file in files:
                        if file.endswith('.json'):
                            try:
                                with open(os.path.join(root, file), 'r') as f:
                                    json.load(f)
                                config_test_passed = True
                                break
                            except Exception:
                                pass
                    if config_test_passed:
                        break

                result = {
                    "status": "passed" if test_files else "failed",
                    "extracted_files": len(test_files),
                    "config_test_passed": config_test_passed,
                    "message": f"Successfully extracted {len(test_files)} test files"
                }

                if not test_files:
                    result["message"] = "No files could be extracted for testing"

                return result

        except Exception as e:
            return {
                "status": "failed",
                "message": f"Restoration test failed: {str(e)}"
            }
        finally:
            # Cleanup
            try:
                if restore_temp_dir.exists():
                    shutil.rmtree(restore_temp_dir)
            except Exception:
                pass

    def _validate_data_integrity(self, backup_file: Path) -> Dict[str, Any]:
        """Perform comprehensive data integrity validation.

        Args:
            backup_file: Path to backup file

        Returns:
            Data integrity validation results
        """
        import tarfile

        integrity_temp_dir = self.temp_dir / "integrity_test"
        integrity_temp_dir.mkdir(exist_ok=True)

        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                # Extract and validate data files
                members = tar.getmembers()

                validation_results = {
                    "json_files_valid": 0,
                    "json_files_invalid": 0,
                    "total_files_checked": 0,
                    "issues": []
                }

                for member in members:
                    if member.isfile() and member.name.endswith('.json'):
                        try:
                            tar.extract(member, str(integrity_temp_dir), set_attrs=False)
                            extracted_file = integrity_temp_dir / member.name

                            with open(extracted_file, 'r') as f:
                                json.load(f)

                            validation_results["json_files_valid"] += 1

                        except Exception as e:
                            validation_results["json_files_invalid"] += 1
                            validation_results["issues"].append(f"Invalid JSON in {member.name}: {str(e)}")

                        validation_results["total_files_checked"] += 1

                # Determine status
                if validation_results["json_files_invalid"] == 0:
                    status = "passed"
                    message = f"All {validation_results['json_files_valid']} JSON files are valid"
                else:
                    status = "failed"
                    message = f"Found {validation_results['json_files_invalid']} invalid JSON files"

                return {
                    "status": status,
                    "message": message,
                    **validation_results
                }

        except Exception as e:
            return {
                "status": "failed",
                "message": f"Data integrity validation failed: {str(e)}"
            }
        finally:
            # Cleanup
            try:
                if integrity_temp_dir.exists():
                    shutil.rmtree(integrity_temp_dir)
            except Exception:
                pass

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results.

        Args:
            results: Validation results

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check test results
        for test_name, test_result in results.get("tests", {}).items():
            if test_result.get("status") == "failed":
                if test_name == "integrity":
                    recommendations.append("Recreate backup due to integrity issues")
                elif test_name == "structure":
                    recommendations.append("Review backup contents - missing expected directories")
                elif test_name == "metadata":
                    recommendations.append("Regenerate backup metadata")
                elif test_name == "restoration":
                    recommendations.append("Test backup restoration manually")
                elif test_name == "data_integrity":
                    recommendations.append("Validate and repair data files")

        # General recommendations
        if results.get("overall_status") == "unhealthy":
            recommendations.append("Do not rely on this backup for disaster recovery")
            recommendations.append("Create a new backup immediately")

        if not recommendations:
            recommendations.append("Backup validation successful - ready for use")

        return recommendations

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with basic info.

        Returns:
            List of backup information
        """
        backups = []

        for backup_file in self.backup_dir.glob("*.tar.gz"):
            info = {
                "filename": backup_file.name,
                "path": str(backup_file),
                "size_mb": round(backup_file.stat().st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                "has_metadata": backup_file.with_suffix(".metadata.json").exists()
            }
            backups.append(info)

        return sorted(backups, key=lambda x: x["modified"], reverse=True)


def main():
    """Main entry point for backup validation script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Backup Validation Script for Personal AI Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--backup",
        help="Specific backup file to validate"
    )

    parser.add_argument(
        "--test-restore",
        action="store_true",
        help="Perform test restoration"
    )

    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run comprehensive validation"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available backups"
    )

    args = parser.parse_args()

    try:
        validator = BackupValidator()

        if args.list:
            # List backups
            backups = validator.list_backups()
            print("Available backups:")
            for backup in backups:
                print(f"  {backup['filename']} - {backup['size_mb']}MB - {backup['modified']}")
            return

        # Validate backup
        print("🔍 Validating backup...")
        results = validator.validate_backup(
            backup_path=args.backup,
            test_restore=args.test_restore,
            comprehensive=args.comprehensive
        )

        # Print results
        status_icon = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "error": "💥"
        }.get(results["overall_status"], "❓")

        print(f"\n{status_icon} Validation Result: {results['overall_status'].upper()}")
        print("=" * 60)

        print(f"Backup File: {results['backup_file']}")
        print(f"Validation Time: {results['validation_time']}")
        print()

        print("Test Results:")
        for test_name, test_result in results.get("tests", {}).items():
            icon = "✅" if test_result["status"] == "passed" else "❌"
            print(f"  {icon} {test_name}: {test_result.get('message', 'No message')}")

        if results.get("recommendations"):
            print("\nRecommendations:")
            for rec in results["recommendations"]:
                print(f"  • {rec}")

        # Exit with appropriate code
        if results["overall_status"] == "healthy":
            sys.exit(0)
        elif results["overall_status"] == "degraded":
            sys.exit(1)
        else:
            sys.exit(2)

    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()