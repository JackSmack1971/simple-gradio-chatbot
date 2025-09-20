# src/storage/config_manager.py
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet, InvalidToken
import base64

from ..utils.logging import logger
from ..utils.validators import validate_api_key

class ConfigManager:
    """Manages application configuration with secure storage for sensitive data."""

    def __init__(self, config_dir: str = "data/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / "encryption.key"
        self._config: Dict[str, Any] = {}
        self._cipher = None
        self._load_or_create_key()
        self._load_config()

    def _load_or_create_key(self) -> None:
        """Load existing encryption key or create a new one."""
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                self._cipher = Fernet(key)
                logger.debug("Loaded existing encryption key")
            else:
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions on key file
                os.chmod(self.key_file, 0o600)
                self._cipher = Fernet(key)
                logger.info("Created new encryption key")
        except Exception as e:
            logger.error(f"Failed to load/create encryption key: {e}")
            raise

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    encrypted_data = json.load(f)
                # Decrypt sensitive data
                if 'encrypted' in encrypted_data and self._cipher:
                    decrypted = self._cipher.decrypt(encrypted_data['encrypted'].encode())
                    sensitive_data = json.loads(decrypted.decode())
                else:
                    sensitive_data = {}
                # Load plain text data
                plain_data = encrypted_data.get('plain', {})
                self._config = {**plain_data, **sensitive_data}
                logger.debug("Configuration loaded successfully")
            else:
                self._config = {}
                # Persist empty configuration immediately to enforce restrictive permissions
                self._save_config()
                logger.info("No existing configuration found, starting fresh")
        except InvalidToken:
            logger.error("Invalid encryption token - configuration may be corrupted")
            raise
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Separate sensitive and non-sensitive data
            sensitive_keys = {'api_key', 'openrouter_key', 'secret_key'}
            plain_data = {}
            sensitive_data = {}

            for key, value in self._config.items():
                if key in sensitive_keys:
                    sensitive_data[key] = value
                else:
                    plain_data[key] = value

            # Encrypt sensitive data
            if sensitive_data and self._cipher:
                encrypted = self._cipher.encrypt(json.dumps(sensitive_data).encode())
                data_to_save = {
                    'plain': plain_data,
                    'encrypted': encrypted.decode()
                }
            else:
                data_to_save = {'plain': plain_data}

            with open(self.config_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)

            # Set restrictive permissions on config file
            os.chmod(self.config_file, 0o600)
            logger.debug("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
        self._save_config()

    def set_api_key(self, api_key: str) -> bool:
        """Set API key with validation."""
        is_valid, error = validate_api_key(api_key)
        if not is_valid:
            logger.error(f"Invalid API key: {error}")
            return False

        self.set('api_key', api_key)
        logger.info("API key set successfully")
        return True

    def get_api_key(self) -> Optional[str]:
        """Get API key."""
        return self.get('api_key')

    def delete(self, key: str) -> None:
        """Delete a configuration value."""
        if key in self._config:
            del self._config[key]
            self._save_config()
            logger.debug(f"Configuration key '{key}' deleted")

    def list_keys(self) -> list:
        """List all configuration keys."""
        return list(self._config.keys())

    def clear(self) -> None:
        """Clear all configuration."""
        self._config = {}
        self._save_config()
        logger.info("Configuration cleared")

    def validate_config(self) -> Dict[str, str]:
        """Validate current configuration."""
        errors = {}

        api_key = self.get_api_key()
        if api_key:
            is_valid, error = validate_api_key(api_key)
            if not is_valid:
                errors['api_key'] = error

        return errors