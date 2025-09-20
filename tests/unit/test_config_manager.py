# tests/unit/test_config_manager.py
import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from cryptography.fernet import Fernet

from src.storage.config_manager import ConfigManager
from src.utils.validators import validate_api_key

class TestConfigManager:
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.temp_dir / "config"
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / "encryption.key"

    def teardown_method(self):
        """Clean up test environment."""
        # Remove all files and directories
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization_creates_directories(self):
        """Test that ConfigManager creates necessary directories."""
        config_manager = ConfigManager(str(self.config_dir))

        assert self.config_dir.exists()
        assert self.key_file.exists()
        assert self.config_file.exists()

    def test_encryption_key_creation(self):
        """Test that encryption key is created and loaded properly."""
        config_manager = ConfigManager(str(self.config_dir))

        # Check that key file exists
        assert self.key_file.exists()

        # Check that cipher is initialized
        assert config_manager._cipher is not None

        # Verify key file permissions (should be restrictive)
        key_perms = oct(os.stat(self.key_file).st_mode)[-3:]
        assert key_perms in ['600', '700']  # Restrictive permissions

    def test_set_and_get_plain_config(self):
        """Test setting and getting plain (non-sensitive) configuration."""
        config_manager = ConfigManager(str(self.config_dir))

        # Set a plain config value
        config_manager.set('theme', 'dark')
        config_manager.set('language', 'en')

        # Get the values
        assert config_manager.get('theme') == 'dark'
        assert config_manager.get('language') == 'en'
        assert config_manager.get('nonexistent', 'default') == 'default'

    def test_set_api_key_with_validation(self):
        """Test setting API key with validation."""
        config_manager = ConfigManager(str(self.config_dir))

        # Valid API key
        valid_key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890"
        assert config_manager.set_api_key(valid_key)
        assert config_manager.get_api_key() == valid_key

    def test_set_invalid_api_key(self):
        """Test setting invalid API key."""
        config_manager = ConfigManager(str(self.config_dir))

        # Invalid API key
        invalid_key = "invalid-key"
        assert not config_manager.set_api_key(invalid_key)
        assert config_manager.get_api_key() is None

    def test_encrypted_storage(self):
        """Test that sensitive data is encrypted."""
        config_manager = ConfigManager(str(self.config_dir))

        # Set API key (sensitive data)
        api_key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890"
        config_manager.set_api_key(api_key)

        # Set plain data
        config_manager.set('theme', 'dark')

        # Check that config file contains encrypted data
        with open(self.config_file, 'r') as f:
            data = json.load(f)

        # Should have plain and encrypted sections
        assert 'plain' in data
        assert 'encrypted' in data

        # Plain data should be readable
        assert data['plain']['theme'] == 'dark'

        # Encrypted data should not be readable as plain text
        assert data['encrypted'] != api_key

    def test_config_persistence(self):
        """Test that configuration persists across instances."""
        # First instance
        config_manager1 = ConfigManager(str(self.config_dir))
        config_manager1.set('theme', 'dark')
        config_manager1.set_api_key("sk-or-v1-1234567890abcdef1234567890abcdef1234567890")

        # Second instance (should load existing config)
        config_manager2 = ConfigManager(str(self.config_dir))

        assert config_manager2.get('theme') == 'dark'
        assert config_manager2.get_api_key() == "sk-or-v1-1234567890abcdef1234567890abcdef1234567890"

    def test_delete_config(self):
        """Test deleting configuration values."""
        config_manager = ConfigManager(str(self.config_dir))

        # Set some values
        config_manager.set('theme', 'dark')
        config_manager.set('language', 'en')

        # Delete one
        config_manager.delete('theme')

        assert config_manager.get('theme') is None
        assert config_manager.get('language') == 'en'

    def test_list_keys(self):
        """Test listing all configuration keys."""
        config_manager = ConfigManager(str(self.config_dir))

        config_manager.set('theme', 'dark')
        config_manager.set('language', 'en')
        config_manager.set_api_key("sk-or-v1-1234567890abcdef1234567890abcdef1234567890")

        keys = config_manager.list_keys()

        assert 'theme' in keys
        assert 'language' in keys
        assert 'api_key' in keys

    def test_clear_config(self):
        """Test clearing all configuration."""
        config_manager = ConfigManager(str(self.config_dir))

        config_manager.set('theme', 'dark')
        config_manager.set_api_key("sk-or-v1-1234567890abcdef1234567890abcdef1234567890")

        config_manager.clear()

        assert config_manager.get('theme') is None
        assert config_manager.get_api_key() is None
        assert len(config_manager.list_keys()) == 0

    def test_validate_config(self):
        """Test configuration validation."""
        config_manager = ConfigManager(str(self.config_dir))

        # Set valid API key
        valid_key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890"
        config_manager.set_api_key(valid_key)

        errors = config_manager.validate_config()
        assert len(errors) == 0

        # Set invalid API key manually (bypassing validation)
        config_manager.set('api_key', 'invalid-key')

        errors = config_manager.validate_config()
        assert 'api_key' in errors

    def test_file_permissions(self):
        """Test that configuration files have correct permissions."""
        config_manager = ConfigManager(str(self.config_dir))

        # Check config file permissions
        config_perms = oct(os.stat(self.config_file).st_mode)[-3:]
        assert config_perms in ['600', '700']

        # Check key file permissions
        key_perms = oct(os.stat(self.key_file).st_mode)[-3:]
        assert key_perms in ['600', '700']

    @patch('os.chmod')
    def test_permission_setting_on_windows(self, mock_chmod):
        """Test permission setting (may not work on Windows)."""
        config_manager = ConfigManager(str(self.config_dir))

        # On Windows, os.chmod might not work as expected
        # The code should still work without raising exceptions
        config_manager.set('test', 'value')
        assert config_manager.get('test') == 'value'