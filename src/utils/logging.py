# src/utils/logging.py
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

class Logger:
    """Centralized logging configuration for the application."""

    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls) -> 'Logger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self) -> None:
        """Configure logging with file and console handlers."""
        self._logger = logging.getLogger('personal_ai_chatbot')
        self._logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        # Create logs directory if it doesn't exist
        log_dir = Path('data/logs')
        log_dir.mkdir(parents=True, exist_ok=True)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        if self._logger is None:
            self._setup_logger()
        return self._logger

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message."""
        self.get_logger().debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message."""
        self.get_logger().info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message."""
        self.get_logger().warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message."""
        self.get_logger().error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message."""
        self.get_logger().critical(message, *args, **kwargs)

# Global logger instance
logger = Logger().get_logger()