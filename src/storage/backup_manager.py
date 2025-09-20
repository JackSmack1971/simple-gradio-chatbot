# src/storage/backup_manager.py
import json
import shutil
import hashlib
import gzip
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import threading
import time

from ..utils.logging import logger

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    logger.warning("schedule library not available, automatic backups disabled")

class BackupManager:
    """Manages automated backup creation and restoration with retention policies."""

    def __init__(self, backup_dir: str = "data/backups", source_dirs: Optional[List[str]] = None):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Default source directories to backup
        if source_dirs is None:
            source_dirs = ["data/config", "data/conversations"]
        self.source_dirs = [Path(d) for d in source_dirs]

        self.backup_schedule = None
        self.scheduler_thread = None
        self.stop_scheduler = False

        # Retention settings
        self.max_backups = 10
        self.retention_days = 30

        # Load existing backup metadata
        self._load_backup_metadata()

    def _load_backup_metadata(self) -> None:
        """Load metadata for existing backups."""
        self.backups = []
        metadata_file = self.backup_dir / "backup_metadata.json"

        try:
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.backups = json.load(f)
                logger.debug(f"Loaded metadata for {len(self.backups)} backups")
        except Exception as e:
            logger.error(f"Failed to load backup metadata: {e}")
            self.backups = []

    def _save_backup_metadata(self) -> None:
        """Save backup metadata."""
        metadata_file = self.backup_dir / "backup_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(self.backups, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")

    def _calculate_directory_hash(self, directory: Path, ignore_filenames: Optional[set[str]] = None) -> str:
        """Calculate SHA256 hash of all files in a directory."""
        hash_obj = hashlib.sha256()
        ignore_filenames = ignore_filenames or set()

        try:
            for file_path in sorted(directory.rglob("*")):
                if file_path.is_file():
                    if file_path.name in ignore_filenames:
                        continue
                    with open(file_path, 'rb') as f:
                        while chunk := f.read(8192):
                            hash_obj.update(chunk)
        except Exception as e:
            logger.error(f"Failed to calculate hash for {directory}: {e}")
            return ""

        return hash_obj.hexdigest()

    def _compress_directory(self, source_dir: Path, dest_file: Path) -> bool:
        """Compress a directory to a gzip file."""
        try:
            with gzip.open(dest_file, 'wb') as gz_file:
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        # Write relative path and file content metadata
                        rel_path = file_path.relative_to(source_dir)
                        gz_file.write(f"FILE:{rel_path}\n".encode("utf-8"))

                        file_size = file_path.stat().st_size
                        gz_file.write(f"SIZE:{file_size}\n".encode("utf-8"))

                        with open(file_path, 'rb') as src_file:
                            shutil.copyfileobj(src_file, gz_file)
            return True
        except Exception as e:
            logger.error(f"Failed to compress {source_dir}: {e}")
            return False

    def create_backup(self, backup_name: Optional[str] = None) -> Optional[str]:
        """Create a new backup."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if backup_name:
                backup_name = f"{backup_name}_{timestamp}"
            else:
                backup_name = f"backup_{timestamp}"

            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)

            backup_info = {
                'name': backup_name,
                'created_at': datetime.now().isoformat(),
                'source_dirs': [str(d) for d in self.source_dirs],
                'files': [],
                'total_size': 0,
                'hash': ''
            }

            # Backup each source directory
            for source_dir in self.source_dirs:
                if not source_dir.exists():
                    logger.warning(f"Source directory {source_dir} does not exist")
                    continue

                # Calculate hash before backup
                dir_hash = self._calculate_directory_hash(source_dir)

                # Create compressed backup
                compressed_file = backup_path / f"{source_dir.name}.tar.gz"
                if self._compress_directory(source_dir, compressed_file):
                    file_size = compressed_file.stat().st_size
                    backup_info['files'].append({
                        'source': str(source_dir),
                        'compressed': str(compressed_file),
                        'size': file_size,
                        'hash': dir_hash
                    })
                    backup_info['total_size'] += file_size
                else:
                    logger.error(f"Failed to backup {source_dir}")

            # Calculate overall backup hash
            backup_info['hash'] = self._calculate_directory_hash(backup_path, ignore_filenames={"metadata.json"})

            # Save backup metadata
            metadata_file = backup_path / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(backup_info, f, indent=2, default=str)

            self.backups.append(backup_info)
            self._save_backup_metadata()

            # Apply retention policy
            self._apply_retention_policy()

            logger.info(f"Created backup: {backup_name}")
            return backup_name

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def verify_backup_integrity(self, backup_name: str) -> bool:
        """Verify the integrity of a backup."""
        try:
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                logger.error(f"Backup {backup_name} does not exist")
                return False

            metadata_file = backup_path / "metadata.json"
            if not metadata_file.exists():
                logger.error(f"Backup metadata missing for {backup_name}")
                return False

            with open(metadata_file, 'r') as f:
                backup_info = json.load(f)

            # Verify overall backup hash
            current_hash = self._calculate_directory_hash(backup_path, ignore_filenames={"metadata.json"})
            if current_hash != backup_info.get('hash', ''):
                logger.error(f"Backup {backup_name} hash mismatch")
                return False

            # Verify individual files
            for file_info in backup_info.get('files', []):
                compressed_file = Path(file_info['compressed'])
                if not compressed_file.exists():
                    logger.error(f"Compressed file missing: {compressed_file}")
                    return False

                if compressed_file.stat().st_size != file_info['size']:
                    logger.error(f"File size mismatch for {compressed_file}")
                    return False

            logger.info(f"Backup {backup_name} integrity verified")
            return True

        except Exception as e:
            logger.error(f"Failed to verify backup {backup_name}: {e}")
            return False

    def restore_backup(self, backup_name: str, restore_dir: str = "data/restored") -> bool:
        """Restore a backup to a directory."""
        try:
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                logger.error(f"Backup {backup_name} does not exist")
                return False

            restore_path = Path(restore_dir)
            restore_path.mkdir(parents=True, exist_ok=True)

            metadata_file = backup_path / "metadata.json"
            with open(metadata_file, 'r') as f:
                backup_info = json.load(f)

            # Extract each compressed file
            for file_info in backup_info.get('files', []):
                compressed_file = Path(file_info['compressed'])
                source_dir_name = Path(file_info['source']).name
                target_dir = restore_path / source_dir_name
                target_dir.mkdir(exist_ok=True)

                if not self._extract_directory(compressed_file, target_dir):
                    logger.error(f"Failed to extract {compressed_file}")
                    return False

            logger.info(f"Restored backup {backup_name} to {restore_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup {backup_name}: {e}")
            return False

    def _extract_directory(self, compressed_file: Path, target_dir: Path) -> bool:
        """Extract a compressed directory."""
        try:
            with gzip.open(compressed_file, 'rb') as gz_file:
                while True:
                    header = gz_file.readline()
                    if not header:
                        break

                    if not header.startswith(b"FILE:"):
                        raise ValueError("Invalid backup format: missing FILE header")

                    rel_path_bytes = header[len(b"FILE:"):].rstrip(b"\n")
                    rel_path = rel_path_bytes.decode('utf-8')

                    size_line = gz_file.readline()
                    if not size_line.startswith(b"SIZE:"):
                        raise ValueError("Invalid backup format: missing SIZE header")

                    size_value = size_line[len(b"SIZE:"):].rstrip(b"\n")
                    try:
                        file_size = int(size_value)
                    except ValueError as exc:
                        raise ValueError("Invalid backup format: SIZE is not an integer") from exc

                    if file_size < 0:
                        raise ValueError("Invalid backup format: SIZE cannot be negative")

                    target_file = target_dir / rel_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)

                    bytes_remaining = file_size
                    with open(target_file, 'wb') as current_file_handle:
                        # Security: enforce exact byte counts to prevent truncation or over-read
                        while bytes_remaining > 0:
                            chunk = gz_file.read(min(bytes_remaining, 65536))
                            if not chunk:
                                raise IOError("Unexpected end of backup data")
                            current_file_handle.write(chunk)
                            bytes_remaining -= len(chunk)

                    # Backwards compatibility: discard legacy newline delimiter if present
                    if hasattr(gz_file, 'peek') and gz_file.peek(1)[:1] == b"\n":
                        gz_file.read(1)

            return True
        except Exception as e:
            logger.error(f"Failed to extract {compressed_file}: {e}")
            return False

    def _apply_retention_policy(self) -> None:
        """Apply retention policy to clean up old backups."""
        try:
            # Sort backups by creation date (newest first)
            self.backups.sort(key=lambda x: x['created_at'], reverse=True)

            # Remove backups beyond max count
            if len(self.backups) > self.max_backups:
                backups_to_remove = self.backups[self.max_backups:]
                for backup in backups_to_remove:
                    backup_path = self.backup_dir / backup['name']
                    if backup_path.exists():
                        shutil.rmtree(backup_path)
                        logger.info(f"Removed old backup: {backup['name']}")
                self.backups = self.backups[:self.max_backups]

            # Remove backups older than retention period
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            self.backups = [
                backup for backup in self.backups
                if datetime.fromisoformat(backup['created_at']) > cutoff_date
            ]

            self._save_backup_metadata()

        except Exception as e:
            logger.error(f"Failed to apply retention policy: {e}")

    def schedule_backups(self, interval_hours: int = 24) -> None:
        """Schedule automatic backups."""
        if not SCHEDULE_AVAILABLE:
            logger.warning("Cannot schedule backups: schedule library not available")
            return

        try:
            if self.backup_schedule:
                schedule.cancel_job(self.backup_schedule)

            self.backup_schedule = schedule.every(interval_hours).hours.do(
                lambda: self.create_backup()
            )

            # Start scheduler in background thread
            self.stop_scheduler = False
            self.scheduler_thread = threading.Thread(target=self._run_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()

            logger.info(f"Scheduled backups every {interval_hours} hours")

        except Exception as e:
            logger.error(f"Failed to schedule backups: {e}")

    def _run_scheduler(self) -> None:
        """Run the backup scheduler."""
        while not self.stop_scheduler:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def stop_scheduled_backups(self) -> None:
        """Stop scheduled backups."""
        self.stop_scheduler = True
        if self.backup_schedule:
            schedule.cancel_job(self.backup_schedule)
            self.backup_schedule = None
        logger.info("Stopped scheduled backups")

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        return self.backups.copy()

    def get_backup_info(self, backup_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific backup."""
        for backup in self.backups:
            if backup['name'] == backup_name:
                return backup.copy()
        return None

    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup."""
        try:
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                logger.warning(f"Backup {backup_name} does not exist")
                return False

            shutil.rmtree(backup_path)

            original_count = len(self.backups)
            self.backups = [b for b in self.backups if b['name'] != backup_name]
            if len(self.backups) != original_count:
                self._save_backup_metadata()

            logger.info(f"Deleted backup: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_name}: {e}")
            return False
