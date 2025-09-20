#!/usr/bin/env python3
"""
Configuration Validation Script for Personal AI Chatbot
Validates configuration files and environment variables before deployment
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ConfigValidator:
    """Configuration validator for Personal AI Chatbot"""

    def __init__(self, config_dir: Optional[str] = None, env_file: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else None
        self.env_file = Path(env_file) if env_file else None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_environment_variables(self) -> bool:
        """Validate required environment variables"""
        logger.info("Validating environment variables...")

        required_vars = [
            'OPENROUTER_API_KEY',
            'SECRET_KEY',
            'ENCRYPTION_KEY'
        ]

        recommended_vars = [
            'APP_HOST',
            'APP_PORT',
            'LOG_LEVEL'
        ]

        # Check required variables
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Required environment variable '{var}' is not set")
            elif len(value.strip()) == 0:
                self.errors.append(f"Required environment variable '{var}' is empty")
            elif var == 'OPENROUTER_API_KEY' and not self._is_valid_api_key(value):
                self.errors.append(f"Invalid OpenRouter API key format")

        # Check recommended variables
        for var in recommended_vars:
            value = os.getenv(var)
            if not value:
                self.warnings.append(f"Recommended environment variable '{var}' is not set")

        # Validate specific values
        self._validate_app_port()
        self._validate_log_level()

        return len(self.errors) == 0

    def _is_valid_api_key(self, api_key: str) -> bool:
        """Validate OpenRouter API key format"""
        if not api_key.startswith('sk-or-v1-'):
            return False
        if len(api_key) < 20:  # Basic length check
            return False
        return True

    def _validate_app_port(self):
        """Validate APP_PORT"""
        port_str = os.getenv('APP_PORT')
        if port_str:
            try:
                port = int(port_str)
                if port < 1024 or port > 65535:
                    self.errors.append(f"APP_PORT must be between 1024 and 65535, got {port}")
            except ValueError:
                self.errors.append(f"APP_PORT must be a valid integer, got '{port_str}'")

    def _validate_log_level(self):
        """Validate LOG_LEVEL"""
        log_level = os.getenv('LOG_LEVEL', '').upper()
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level and log_level not in valid_levels:
            self.warnings.append(f"LOG_LEVEL '{log_level}' is not standard. Valid levels: {', '.join(valid_levels)}")

    def validate_config_file(self) -> bool:
        """Validate JSON configuration file"""
        if not self.config_dir:
            logger.info("No config directory specified, skipping config file validation")
            return True

        config_file = self.config_dir / "app_config.json"
        if not config_file.exists():
            self.warnings.append(f"Configuration file not found: {config_file}")
            return True

        logger.info(f"Validating configuration file: {config_file}")

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            # Validate required sections
            required_sections = ['app', 'data', 'security']
            for section in required_sections:
                if section not in config:
                    self.errors.append(f"Required configuration section '{section}' is missing")

            # Validate app section
            if 'app' in config:
                app_config = config['app']
                if 'port' in app_config:
                    port = app_config['port']
                    if not isinstance(port, int) or port < 1024 or port > 65535:
                        self.errors.append(f"app.port must be between 1024 and 65535, got {port}")

            # Validate data section
            if 'data' in config:
                data_config = config['data']
                required_data_keys = ['data_dir', 'config_dir', 'logs_dir']
                for key in required_data_keys:
                    if key not in data_config:
                        self.errors.append(f"data.{key} is required")

            # Validate security section
            if 'security' in config:
                security_config = config['security']
                if 'max_memory_mb' in security_config:
                    memory = security_config['max_memory_mb']
                    if not isinstance(memory, int) or memory < 100:
                        self.warnings.append(f"security.max_memory_mb seems low: {memory}MB")

        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            self.errors.append(f"Error reading configuration file: {e}")

        return len(self.errors) == 0

    def validate_file_permissions(self) -> bool:
        """Validate file and directory permissions"""
        logger.info("Validating file permissions...")

        # Check config directory permissions
        if self.config_dir and self.config_dir.exists():
            config_stat = self.config_dir.stat()
            # Should be readable/writable by owner only (0o700)
            if oct(config_stat.st_mode)[-3:] != '700':
                self.warnings.append(f"Config directory permissions should be 700, got {oct(config_stat.st_mode)[-3:]}")

        # Check environment file permissions
        if self.env_file and self.env_file.exists():
            env_stat = self.env_file.stat()
            # Should be readable/writable by owner only (0o600)
            if oct(env_stat.st_mode)[-3:] != '600':
                self.errors.append(f"Environment file permissions should be 600, got {oct(env_stat.st_mode)[-3:]}")

        return len(self.errors) == 0

    def validate_network_connectivity(self) -> bool:
        """Validate network connectivity to required services"""
        logger.info("Validating network connectivity...")

        import urllib.request
        import socket

        # Test OpenRouter API connectivity
        try:
            urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=10)
            logger.info("✓ OpenRouter API is reachable")
        except Exception as e:
            self.warnings.append(f"Cannot reach OpenRouter API: {e}")

        # Test local port availability
        app_port = os.getenv('APP_PORT', '7860')
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('127.0.0.1', int(app_port)))
                if result == 0:
                    self.warnings.append(f"Port {app_port} is already in use")
        except Exception as e:
            self.warnings.append(f"Cannot check port availability: {e}")

        return True  # Network issues are warnings, not errors

    def run_validation(self) -> bool:
        """Run all validation checks"""
        logger.info("Starting configuration validation...")

        checks = [
            self.validate_environment_variables,
            self.validate_config_file,
            self.validate_file_permissions,
            self.validate_network_connectivity
        ]

        all_passed = True
        for check in checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                self.errors.append(f"Validation check failed: {e}")
                all_passed = False

        return all_passed

    def print_results(self):
        """Print validation results"""
        if self.errors:
            logger.error(f"Found {len(self.errors)} error(s):")
            for error in self.errors:
                logger.error(f"  - {error}")

        if self.warnings:
            logger.warning(f"Found {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        if not self.errors and not self.warnings:
            logger.info("✓ All validation checks passed!")

    def get_exit_code(self) -> int:
        """Get appropriate exit code based on validation results"""
        if self.errors:
            return 1  # Errors
        elif self.warnings:
            return 2  # Warnings only
        else:
            return 0  # Success


def main():
    parser = argparse.ArgumentParser(description='Validate Personal AI Chatbot configuration')
    parser.add_argument('--config-dir', help='Configuration directory path')
    parser.add_argument('--env-file', help='Environment file path')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')

    args = parser.parse_args()

    # Auto-detect paths if not provided
    if not args.config_dir:
        # Try to find config directory relative to script location
        script_dir = Path(__file__).parent
        possible_config_dirs = [
            script_dir / "../../data/config",
            Path.home() / ".local/share/personal-ai-chatbot/config",
            Path.home() / "Library/Application Support/PersonalAIChatbot/config",
            Path(os.getenv('APPDATA', '')) / "PersonalAIChatbot/config"
        ]
        for config_dir in possible_config_dirs:
            if config_dir.exists():
                args.config_dir = str(config_dir)
                break

    if not args.env_file:
        # Try to find .env file
        script_dir = Path(__file__).parent
        possible_env_files = [
            script_dir / "../../.env",
            Path.home() / ".local/share/personal-ai-chatbot/.env",
            Path.home() / "Library/Application Support/PersonalAIChatbot/.env",
            Path(os.getenv('APPDATA', '')) / "PersonalAIChatbot/.env"
        ]
        for env_file in possible_env_files:
            if env_file.exists():
                args.env_file = str(env_file)
                break

    validator = ConfigValidator(args.config_dir, args.env_file)

    if args.config_dir:
        logger.info(f"Using config directory: {args.config_dir}")
    else:
        logger.info("No config directory found")

    if args.env_file:
        logger.info(f"Using environment file: {args.env_file}")
    else:
        logger.info("No environment file found")

    success = validator.run_validation()
    validator.print_results()

    if args.strict and validator.warnings:
        logger.error("Strict mode: treating warnings as errors")
        success = False

    sys.exit(validator.get_exit_code())


if __name__ == '__main__':
    main()