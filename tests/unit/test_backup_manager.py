# tests/unit/test_backup_manager.py
import pytest
import tempfile
import json
import gzip
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.storage.backup_manager import BackupManager

class TestBackupManager:
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backup_dir = self.temp_dir / "backups"
        self.source_dir = self.temp_dir / "source"
        self.source_dir.mkdir()

        # Create test source files
        self.config_file = self.source_dir / "config.json"
        with open(self.config_file, 'w') as f:
            json.dump({"test": "data"}, f)

        self.backup_manager = BackupManager(
            backup_dir=str(self.backup_dir),
            source_dirs=[str(self.source_dir)]
        )

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization_creates_directories(self):
        """Test that BackupManager creates necessary directories."""
        assert self.backup_dir.exists()

    def test_create_backup(self):
        """Test creating a backup."""
        backup_name = self.backup_manager.create_backup("test_backup")

        assert backup_name is not None
        assert "test_backup" in backup_name

        # Check that backup directory was created
        backup_path = self.backup_dir / backup_name
        assert backup_path.exists()

        # Check that metadata file exists
        metadata_file = backup_path / "metadata.json"
        assert metadata_file.exists()

        # Check metadata content
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        assert metadata['name'] == backup_name
        assert 'created_at' in metadata
        assert len(metadata['files']) > 0

    def test_create_backup_without_name(self):
        """Test creating a backup without specifying a name."""
        backup_name = self.backup_manager.create_backup()

        assert backup_name is not None
        assert backup_name.startswith("backup_")

    def test_verify_backup_integrity(self):
        """Test verifying backup integrity."""
        backup_name = self.backup_manager.create_backup("test_backup")
        assert backup_name is not None

        result = self.backup_manager.verify_backup_integrity(backup_name)
        assert result is True

    def test_verify_nonexistent_backup(self):
        """Test verifying a non-existent backup."""
        result = self.backup_manager.verify_backup_integrity("nonexistent")
        assert result is False

    def test_restore_backup(self):
        """Test restoring a backup."""
        # Create backup
        backup_name = self.backup_manager.create_backup("test_backup")
        assert backup_name is not None

        # Create restore directory
        restore_dir = self.temp_dir / "restore"

        # Restore backup
        result = self.backup_manager.restore_backup(backup_name, str(restore_dir))
        assert result is True

        # Check that files were restored
        restored_config = restore_dir / "source" / "config.json"
        assert restored_config.exists()

        with open(restored_config, 'r') as f:
            data = json.load(f)
        assert data == {"test": "data"}

    def test_restore_nonexistent_backup(self):
        """Test restoring a non-existent backup."""
        result = self.backup_manager.restore_backup("nonexistent")
        assert result is False

    def test_list_backups(self):
        """Test listing backups."""
        # Initially empty
        backups = self.backup_manager.list_backups()
        assert len(backups) == 0

        # Create backup
        self.backup_manager.create_backup("test_backup")

        # Check that backup is listed
        backups = self.backup_manager.list_backups()
        assert len(backups) == 1
        assert backups[0]['name'].startswith("test_backup")

    def test_get_backup_info(self):
        """Test getting backup information."""
        backup_name = self.backup_manager.create_backup("test_backup")
        assert backup_name is not None

        info = self.backup_manager.get_backup_info(backup_name)
        assert info is not None
        assert info['name'] == backup_name

        # Test non-existent backup
        info = self.backup_manager.get_backup_info("nonexistent")
        assert info is None

    def test_delete_backup(self):
        """Test deleting a backup."""
        backup_name = self.backup_manager.create_backup("test_backup")
        assert backup_name is not None

        # Verify backup exists
        backup_path = self.backup_dir / backup_name
        assert backup_path.exists()

        # Delete backup
        result = self.backup_manager.delete_backup(backup_name)
        assert result is True

        # Verify backup is deleted
        assert not backup_path.exists()

        # Verify not in backup list
        backups = self.backup_manager.list_backups()
        assert len(backups) == 0

    def test_delete_nonexistent_backup(self):
        """Test deleting a non-existent backup."""
        result = self.backup_manager.delete_backup("nonexistent")
        assert result is False

    def test_apply_retention_policy(self):
        """Test applying retention policy."""
        # Create multiple backups
        for i in range(15):  # More than max_backups (10)
            self.backup_manager.create_backup(f"backup_{i}")

        # Check that only max_backups are kept
        backups = self.backup_manager.list_backups()
        assert len(backups) <= self.backup_manager.max_backups

    def test_backup_with_missing_source_directory(self):
        """Test backup creation when source directory doesn't exist."""
        missing_source = self.temp_dir / "missing"
        backup_manager = BackupManager(
            backup_dir=str(self.backup_dir),
            source_dirs=[str(missing_source)]
        )

        backup_name = backup_manager.create_backup("test_backup")
        assert backup_name is not None

        # Should still create backup (empty)
        backup_path = self.backup_dir / backup_name
        assert backup_path.exists()

    def test_compressed_file_integrity(self):
        """Test that compressed files can be read back."""
        backup_name = self.backup_manager.create_backup("test_backup")
        assert backup_name is not None

        # Get backup info
        info = self.backup_manager.get_backup_info(backup_name)
        assert info is not None

        # Check compressed file
        compressed_file = Path(info['files'][0]['compressed'])
        assert compressed_file.exists()

        # Try to read compressed file
        with gzip.open(compressed_file, 'rb') as f:
            content = f.read()
        assert len(content) > 0

    @patch('src.storage.backup_manager.SCHEDULE_AVAILABLE', False)
    def test_schedule_backups_without_library(self):
        """Test scheduling backups when schedule library is not available."""
        self.backup_manager.schedule_backups(24)
        # Should not raise exception

    def test_stop_scheduled_backups(self):
        """Test stopping scheduled backups."""
        self.backup_manager.stop_scheduled_backups()
        # Should not raise exception

    def test_backup_metadata_persistence(self):
        """Test that backup metadata persists across instances."""
        # Create backup with first instance
        backup_name1 = self.backup_manager.create_backup("test_backup_1")

        # Create new instance
        backup_manager2 = BackupManager(
            backup_dir=str(self.backup_dir),
            source_dirs=[str(self.source_dir)]
        )

        # Check that backup is available in new instance
        backups = backup_manager2.list_backups()
        assert len(backups) >= 1

        found_backup = any(b['name'] == backup_name1 for b in backups)
        assert found_backup

    def test_backup_with_multiple_source_dirs(self):
        """Test backup with multiple source directories."""
        # Create another source directory
        source_dir2 = self.temp_dir / "source2"
        source_dir2.mkdir()
        config_file2 = source_dir2 / "config2.json"
        with open(config_file2, 'w') as f:
            json.dump({"test2": "data2"}, f)

        backup_manager = BackupManager(
            backup_dir=str(self.backup_dir),
            source_dirs=[str(self.source_dir), str(source_dir2)]
        )

        backup_name = backup_manager.create_backup("multi_source_backup")
        assert backup_name is not None

        # Check that both source dirs are backed up
        info = backup_manager.get_backup_info(backup_name)
        assert info is not None
        assert len(info['files']) == 2