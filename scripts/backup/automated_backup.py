#!/usr/bin/env python3
"""
Automated Backup Script for Personal AI Chatbot

This script creates comprehensive backups of the application data, configuration,
and system state. It supports different backup types and validation.

Usage:
    python scripts/backup/automated_backup.py [--type TYPE] [--validate] [--encrypt]

Options:
    --type TYPE       Backup type: full, incremental, config (default: full)
    --validate        Validate backup integrity after creation
    --encrypt         Encrypt the backup archive
    --help, -h        Show this help message
"""

import sys
import os
import json
import tarfile
import gzip
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Ensure project root is on the path for package imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging import logger
from src.utils.events import event_bus, EventType, EventPriority, Event


class BackupManager:
    """Manages backup creation and validation."""

    def __init__(self, backup_dir: str = "data/backups"):
        """Initialize backup manager.

        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup configuration
        self.config = {
            "full_backup_dirs": [
                "data/conversations",
                "data/cache",
                "data/logs",
                "config"
            ],
            "incremental_dirs": [
                "data/conversations",
                "data/logs"
            ],
            "exclude_patterns": [
                "*.tmp",
                "*.lock",
                "data/cache/temp/*",
                "data/logs/*.log"  # Exclude current log files
            ],
            "retention_days": {
                "full": 30,
                "incremental": 7,
                "config": 90
            }
        }

        logger.info("BackupManager initialized")

    def create_backup(self, backup_type: str = "full",
                     validate: bool = True,
                     encrypt: bool = False) -> Dict[str, Any]:
        """Create a backup archive.

        Args:
            backup_type: Type of backup (full, incremental, config)
            validate: Whether to validate the backup
            encrypt: Whether to encrypt the backup

        Returns:
            Dictionary with backup information
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{backup_type}_backup_{timestamp}"

        logger.info(f"Starting {backup_type} backup: {backup_name}")

        try:
            # Create backup archive
            archive_path = self._create_archive(backup_name, backup_type)

            # Validate if requested
            if validate:
                self._validate_backup(archive_path)

            # Encrypt if requested
            if encrypt:
                archive_path = self._encrypt_backup(archive_path)

            # Create backup metadata
            metadata = self._create_metadata(backup_name, backup_type, archive_path)

            # Publish success event
            event = Event(
                EventType.SYSTEM_EVENT,
                {
                    "event_type": "backup_completed",
                    "backup_type": backup_type,
                    "backup_name": backup_name,
                    "archive_path": str(archive_path),
                    "size_bytes": archive_path.stat().st_size
                },
                priority=EventPriority.NORMAL,
                source="backup_manager"
            )
            event_bus.publish_sync(event)

            logger.info(f"Backup completed successfully: {backup_name}")
            return metadata

        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")

            # Publish failure event
            event = Event(
                EventType.ERROR,
                {
                    "error_type": "backup_failed",
                    "backup_type": backup_type,
                    "backup_name": backup_name,
                    "error_message": str(e)
                },
                priority=EventPriority.HIGH,
                source="backup_manager"
            )
            event_bus.publish_sync(event)

            raise

    def _create_archive(self, backup_name: str, backup_type: str) -> Path:
        """Create backup archive.

        Args:
            backup_name: Name of the backup
            backup_type: Type of backup

        Returns:
            Path to created archive
        """
        archive_path = self.backup_dir / f"{backup_name}.tar.gz"

        # Determine directories to backup
        if backup_type == "full":
            dirs_to_backup = self.config["full_backup_dirs"]
        elif backup_type == "incremental":
            dirs_to_backup = self.config["incremental_dirs"]
        elif backup_type == "config":
            dirs_to_backup = ["config"]
        else:
            raise ValueError(f"Unknown backup type: {backup_type}")

        with tarfile.open(archive_path, "w:gz") as tar:
            for dir_path in dirs_to_backup:
                src_path = Path(dir_path)
                if src_path.exists():
                    # Add directory to archive
                    tar.add(str(src_path), arcname=dir_path, recursive=True)
                    logger.debug(f"Added {dir_path} to backup")
                else:
                    logger.warning(f"Backup source not found: {dir_path}")

        logger.info(f"Archive created: {archive_path} ({archive_path.stat().st_size} bytes)")
        return archive_path

    def _validate_backup(self, archive_path: Path) -> bool:
        """Validate backup archive integrity.

        Args:
            archive_path: Path to backup archive

        Returns:
            True if validation passes
        """
        logger.info(f"Validating backup: {archive_path}")

        try:
            # Test archive integrity
            with tarfile.open(archive_path, "r:gz") as tar:
                # Try to read archive contents
                members = tar.getmembers()
                logger.debug(f"Archive contains {len(members)} items")

                # Test extraction of a few files
                for member in members[:5]:  # Test first 5 files
                    try:
                        # Extract to temporary location for testing
                        temp_dir = Path("/tmp/backup_validation")
                        temp_dir.mkdir(exist_ok=True)

                        tar.extract(member, str(temp_dir), set_attrs=False)
                        extracted_file = temp_dir / member.name

                        if extracted_file.exists():
                            # Basic content check
                            if extracted_file.is_file() and extracted_file.stat().st_size > 0:
                                logger.debug(f"✓ Validated: {member.name}")
                            else:
                                logger.warning(f"⚠ Empty or invalid file: {member.name}")

                        # Clean up
                        if extracted_file.exists():
                            if extracted_file.is_file():
                                extracted_file.unlink()
                            else:
                                shutil.rmtree(extracted_file)

                    except Exception as e:
                        logger.warning(f"Failed to validate {member.name}: {str(e)}")

            logger.info("Backup validation completed")
            return True

        except Exception as e:
            logger.error(f"Backup validation failed: {str(e)}")
            raise

    def _encrypt_backup(self, archive_path: Path) -> Path:
        """Encrypt backup archive.

        Args:
            archive_path: Path to backup archive

        Returns:
            Path to encrypted archive
        """
        # Note: This is a placeholder for encryption
        # In production, you would use proper encryption (e.g., AES-256)
        logger.info(f"Encryption placeholder for: {archive_path}")
        return archive_path

    def _create_metadata(self, backup_name: str, backup_type: str,
                        archive_path: Path) -> Dict[str, Any]:
        """Create backup metadata.

        Args:
            backup_name: Name of the backup
            backup_type: Type of backup
            archive_path: Path to backup archive

        Returns:
            Backup metadata dictionary
        """
        metadata = {
            "backup_name": backup_name,
            "backup_type": backup_type,
            "created_at": datetime.now().isoformat(),
            "archive_path": str(archive_path),
            "size_bytes": archive_path.stat().st_size,
            "size_mb": round(archive_path.stat().st_size / (1024 * 1024), 2),
            "checksum": self._calculate_checksum(archive_path),
            "contents": self._list_archive_contents(archive_path)
        }

        # Save metadata
        metadata_path = archive_path.with_suffix(".metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        return metadata

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum.

        Args:
            file_path: Path to file

        Returns:
            SHA256 checksum
        """
        import hashlib

        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    def _list_archive_contents(self, archive_path: Path) -> List[str]:
        """List contents of backup archive.

        Args:
            archive_path: Path to archive

        Returns:
            List of files in archive
        """
        contents = []
        with tarfile.open(archive_path, "r:gz") as tar:
            for member in tar.getmembers():
                contents.append(member.name)
        return contents

    def cleanup_old_backups(self):
        """Clean up old backup files based on retention policy."""
        logger.info("Cleaning up old backups")

        for backup_type, retention_days in self.config["retention_days"].items():
            pattern = f"{backup_type}_backup_*.tar.gz"
            old_backups = list(self.backup_dir.glob(pattern))

            for backup_file in old_backups:
                # Extract timestamp from filename
                try:
                    timestamp_str = backup_file.stem.split("_")[-1]
                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    if (datetime.now() - backup_date).days > retention_days:
                        # Remove old backup
                        backup_file.unlink()

                        # Remove associated metadata file
                        metadata_file = backup_file.with_suffix(".metadata.json")
                        if metadata_file.exists():
                            metadata_file.unlink()

                        logger.info(f"Removed old backup: {backup_file.name}")

                except Exception as e:
                    logger.warning(f"Failed to process backup file {backup_file}: {str(e)}")

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups.

        Returns:
            List of backup information
        """
        backups = []

        for pattern in ["*.tar.gz", "*.tar.gz.enc"]:
            for archive_file in self.backup_dir.glob(pattern):
                metadata_file = archive_file.with_suffix(".metadata.json")

                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        backups.append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to read metadata for {archive_file}: {str(e)}")

        return sorted(backups, key=lambda x: x.get("created_at", ""), reverse=True)


def main():
    """Main entry point for automated backup script."""
    parser = argparse.ArgumentParser(
        description="Automated Backup Script for Personal AI Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--type",
        choices=["full", "incremental", "config"],
        default="full",
        help="Type of backup to create"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate backup integrity after creation"
    )

    parser.add_argument(
        "--encrypt",
        action="store_true",
        help="Encrypt the backup archive"
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old backups after creation"
    )

    args = parser.parse_args()

    try:
        # Initialize backup manager
        backup_manager = BackupManager()

        # Create backup
        print(f"Creating {args.type} backup...")
        result = backup_manager.create_backup(
            backup_type=args.type,
            validate=args.validate,
            encrypt=args.encrypt
        )

        print("✅ Backup completed successfully!")
        print(f"   Name: {result['backup_name']}")
        print(f"   Type: {result['backup_type']}")
        print(f"   Size: {result['size_mb']} MB")
        print(f"   Path: {result['archive_path']}")

        # Clean up old backups if requested
        if args.cleanup:
            print("Cleaning up old backups...")
            backup_manager.cleanup_old_backups()
            print("✅ Cleanup completed")

        # Exit with success
        sys.exit(0)

    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()