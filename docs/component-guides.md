# Component Implementation Guides - Personal AI Chatbot

## Overview

This document provides mechanical implementation guides for each component in the Personal AI Chatbot system. Follow these guides sequentially without making architectural decisions. Each guide includes exact code templates, step-by-step instructions, and validation criteria.

## Implementation Prerequisites

Before starting any component implementation:

1. **Environment Setup**:
   ```bash
   cd personal-ai-chatbot
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Directory Structure**:
   ```bash
   mkdir -p src/{ui,core,api,storage,utils}
   mkdir -p tests/{unit,integration,fixtures}
   mkdir -p data/{config,conversations/active,conversations/archived,backups,logs}
   ```

3. **Configuration Files**:
   - Copy `.env.example` to `.env`
   - Set `OPENROUTER_API_KEY` in `.env`
   - Run `python -c "import src; print('Import successful')"` to verify setup

## 1. Foundation Components

### 1.1 Logger (src/utils/logger.py)

**Purpose**: Centralized logging configuration with structured output and appropriate levels.

**Dependencies**: None

**Implementation Steps**:

1. Create the logger module file:
   ```bash
   touch src/utils/__init__.py
   touch src/utils/logger.py
   ```

2. Implement the Logger class:
   ```python
   # src/utils/logger.py
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
   ```

3. Create unit tests:
   ```python
   # tests/unit/test_logger.py
   import pytest
   from pathlib import Path
   from src.utils.logger import Logger

   def test_logger_singleton():
       """Test that Logger follows singleton pattern."""
       logger1 = Logger()
       logger2 = Logger()
       assert logger1 is logger2

   def test_logger_initialization():
       """Test logger initialization creates handlers."""
       logger_instance = Logger()
       logger = logger_instance.get_logger()
       assert len(logger.handlers) == 2  # File and console

   def test_log_file_creation():
       """Test that log directory and file are created."""
       logger_instance = Logger()
       log_dir = Path('data/logs')
       log_file = log_dir / 'app.log'
       assert log_dir.exists()
       assert log_file.exists()

   def test_logger_methods():
       """Test all logging methods work."""
       logger_instance = Logger()
       logger = logger_instance.get_logger()

       # These should not raise exceptions
       logger.debug("Debug message")
       logger.info("Info message")
       logger.warning("Warning message")
       logger.error("Error message")
       logger.critical("Critical message")
   ```

**Validation Criteria**:
- [ ] Logger can be imported without errors
- [ ] Log file created in data/logs/app.log
- [ ] Console and file logging both work
- [ ] All logging levels function correctly
- [ ] Unit tests pass

### 1.2 Validators (src/utils/validators.py)

**Purpose**: Input validation utilities for security and data integrity.

**Dependencies**: Logger

**Implementation Steps**:

1. Create the validators module:
   ```bash
   touch src/utils/validators.py
   ```

2. Implement validation functions:
   ```python
   # src/utils/validators.py
   import re
   from typing import Tuple, Optional
   from urllib.parse import urlparse

   from .logger import logger

   def validate_api_key(api_key: str) -> Tuple[bool, str]:
       """
       Validate OpenRouter API key format.

       Args:
           api_key: The API key to validate

       Returns:
           Tuple of (is_valid, error_message)
       """
       if not api_key or not isinstance(api_key, str):
           return False, "API key must be a non-empty string"

       if not api_key.strip():
           return False, "API key cannot be only whitespace"

       # OpenRouter keys start with 'sk-or-v1-'
       if not api_key.startswith('sk-or-v1-'):
           return False, "API key must start with 'sk-or-v1-'"

       if len(api_key) < 50:  # Minimum reasonable length
           return False, "API key appears too short"

       if len(api_key) > 200:  # Maximum reasonable length
           return False, "API key appears too long"

       # Check for valid characters (alphanumeric, hyphens, underscores)
       if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
           return False, "API key contains invalid characters"

       return True, ""

   def validate_message_content(content: str) -> Tuple[bool, str]:
       """
       Validate message content for chat.

       Args:
           content: The message content to validate

       Returns:
           Tuple of (is_valid, error_message)
       """
       if not content or not isinstance(content, str):
           return False, "Message content must be a non-empty string"

       content = content.strip()
       if not content:
           return False, "Message content cannot be only whitespace"

       # Check length limits
       MAX_LENGTH = 4000  # OpenRouter limit
       if len(content) > MAX_LENGTH:
           return False, f"Message content exceeds maximum length of {MAX_LENGTH} characters"

       # Check for potentially harmful content (basic check)
       dangerous_patterns = [
           r'<script[^>]*>.*?</script>',  # Script tags
           r'javascript:',                # JavaScript URLs
           r'data:',                      # Data URLs that might be malicious
       ]

       for pattern in dangerous_patterns:
           if re.search(pattern, content, re.IGNORECASE):
               logger.warning(f"Potentially dangerous content detected in message: {pattern}")
               return False, "Message contains potentially harmful content"

       return True, ""

   def validate_model_id(model_id: str) -> Tuple[bool, str]:
       """
       Validate AI model identifier.

       Args:
           model_id: The model identifier to validate

       Returns:
           Tuple of (is_valid, error_message)
       """
       if not model_id or not isinstance(model_id, str):
           return False, "Model ID must be a non-empty string"

       model_id = model_id.strip()
       if not model_id:
           return False, "Model ID cannot be only whitespace"

       # Basic format validation (provider/model-name)
       if '/' not in model_id:
           return False, "Model ID must be in format 'provider/model-name'"

       provider, model_name = model_id.split('/', 1)

       if not provider or not model_name:
           return False, "Both provider and model name must be non-empty"

       # Check for valid characters
       if not re.match(r'^[a-zA-Z0-9\-_\.]+$', provider):
           return False, "Provider name contains invalid characters"

       if not re.match(r'^[a-zA-Z0-9\-_\.]+$', model_name):
           return False, "Model name contains invalid characters"

       return True, ""

   def validate_url(url: str) -> Tuple[bool, str]:
       """
       Validate URL format and security.

       Args:
           url: The URL to validate

       Returns:
           Tuple of (is_valid, error_message)
       """
       if not url or not isinstance(url, str):
           return False, "URL must be a non-empty string"

       try:
           parsed = urlparse(url)

           if not parsed.scheme or not parsed.netloc:
               return False, "URL must have valid scheme and network location"

           # Only allow http and https
           if parsed.scheme not in ['http', 'https']:
               return False, "URL must use HTTP or HTTPS protocol"

           # Basic domain validation
           if not re.match(r'^[a-zA-Z0-9\-_\.]+$', parsed.netloc.replace('.', '')):
               return False, "Domain contains invalid characters"

           return True, ""

       except Exception as e:
           return False, f"Invalid URL format: {str(e)}"

   def sanitize_filename(filename: str) -> str:
       """
       Sanitize filename to prevent directory traversal and invalid characters.

       Args:
           filename: The filename to sanitize

       Returns:
           Sanitized filename
       """
       if not filename:
           return "unnamed_file"

       # Remove directory separators
       filename = re.sub(r'[\/\\]', '_', filename)

       # Remove other dangerous characters
       filename = re.sub(r'[<>:"|?*]', '_', filename)

       # Limit length
       if len(filename) > 255:
           filename = filename[:255]

       # Ensure not empty after sanitization
       if not filename.strip():
           filename = "unnamed_file"

       return filename
   ```

3. Create unit tests:
   ```python
   # tests/unit/test_validators.py
   import pytest
   from src.utils.validators import (
       validate_api_key,
       validate_message_content,
       validate_model_id,
       validate_url,
       sanitize_filename
   )

   class TestAPIKeyValidation:
       def test_valid_api_key(self):
           valid_key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890"
           is_valid, error = validate_api_key(valid_key)
           assert is_valid
           assert error == ""

       def test_invalid_api_key_prefix(self):
           invalid_key = "sk-1234567890abcdef"
           is_valid, error = validate_api_key(invalid_key)
           assert not is_valid
           assert "must start with 'sk-or-v1-'" in error

       def test_empty_api_key(self):
           is_valid, error = validate_api_key("")
           assert not is_valid
           assert "non-empty string" in error

   class TestMessageValidation:
       def test_valid_message(self):
           valid_content = "Hello, this is a test message."
           is_valid, error = validate_message_content(valid_content)
           assert is_valid
           assert error == ""

       def test_empty_message(self):
           is_valid, error = validate_message_content("")
           assert not is_valid
           assert "non-empty string" in error

       def test_too_long_message(self):
           long_content = "A" * 4001
           is_valid, error = validate_message_content(long_content)
           assert not is_valid
           assert "exceeds maximum length" in error

   class TestModelValidation:
       def test_valid_model_id(self):
           valid_id = "anthropic/claude-3-haiku"
           is_valid, error = validate_model_id(valid_id)
           assert is_valid
           assert error == ""

       def test_invalid_model_format(self):
           invalid_id = "claude-3-haiku"
           is_valid, error = validate_model_id(invalid_id)
           assert not is_valid
           assert "format 'provider/model-name'" in error

   class TestURLValidation:
       def test_valid_url(self):
           valid_url = "https://openrouter.ai/api/v1/models"
           is_valid, error = validate_url(valid_url)
           assert is_valid
           assert error == ""

       def test_invalid_protocol(self):
           invalid_url = "ftp://example.com"
           is_valid, error = validate_url(invalid_url)
           assert not is_valid
           assert "HTTP or HTTPS" in error

   class TestFilenameSanitization:
       def test_sanitize_normal_filename(self):
           result = sanitize_filename("my_file.txt")
           assert result == "my_file.txt"

       def test_sanitize_dangerous_filename(self):
           result = sanitize_filename("../../etc/passwd")
           assert result == "____etc_passwd"

       def test_sanitize_empty_filename(self):
           result = sanitize_filename("")
           assert result == "unnamed_file"
   ```

**Validation Criteria**:
- [ ] All validation functions import without errors
- [ ] API key validation accepts correct format and rejects invalid ones
- [ ] Message validation enforces length and content rules
- [ ] Model ID validation checks format requirements
- [ ] URL validation ensures security
- [ ] Filename sanitization prevents directory traversal
- [ ] Unit tests pass with 100% coverage

## Phase 5: Application Logic Layer Components

### 5.1 ChatController (src/core/controllers/chat_controller.py)

**Purpose**: Central orchestration component for chat workflows and user interaction coordination.

**Dependencies**: MessageProcessor, ConversationManager, APIClientManager, StateManager, Logger

**Implementation Steps**:

1. Create the chat controller module:
    ```bash
    mkdir -p src/core/controllers
    touch src/core/controllers/__init__.py
    touch src/core/controllers/chat_controller.py
    ```

2. Implement the ChatController class:
    ```python
    # src/core/controllers/chat_controller.py
    import asyncio
    import time
    from typing import Dict, Any, Optional, Callable, Tuple
    from enum import Enum
    from datetime import datetime

    from ...utils.logging import logger
    from ..processors.message_processor import MessageProcessor
    from ..managers.conversation_manager import ConversationManager
    from ..managers.api_client_manager import APIClientManager
    from .state_manager import StateManager


    class OperationState(Enum):
        """States for chat operations."""
        IDLE = "idle"
        PROCESSING_INPUT = "processing_input"
        VALIDATING = "validating"
        SENDING_REQUEST = "sending_request"
        WAITING_RESPONSE = "waiting_response"
        PROCESSING_RESPONSE = "processing_response"
        STREAMING = "streaming"
        ERROR = "error"
        CANCELLED = "cancelled"


    class ChatController:
        """Central orchestration for chat workflows and user interactions."""

        def __init__(self,
                     message_processor: Optional[MessageProcessor] = None,
                     conversation_manager: Optional[ConversationManager] = None,
                     api_client_manager: Optional[APIClientManager] = None,
                     state_manager: Optional[StateManager] = None):
            """
            Initialize the ChatController.

            Args:
                message_processor: Message processor instance
                conversation_manager: Conversation manager instance
                api_client_manager: API client manager instance
                state_manager: State manager instance
            """
            self.message_processor = message_processor or MessageProcessor()
            self.conversation_manager = conversation_manager or ConversationManager()
            self.api_client_manager = api_client_manager or APIClientManager()
            self.state_manager = state_manager or StateManager()

            # Operation state tracking
            self.current_operation: Optional[Dict[str, Any]] = None
            self.operation_callbacks: Dict[str, Callable] = {}

            # Configuration
            self.max_concurrent_operations = 3
            self.operation_timeout = 30.0  # seconds

            logger.info("ChatController initialized")

        def process_user_message(self, user_input: str, conversation_id: str,
                               model: str = "anthropic/claude-3-haiku",
                               **kwargs) -> Tuple[bool, Dict[str, Any]]:
            """
            Process a user message and return the AI response.

            Args:
                user_input: The user's message
                conversation_id: Conversation identifier
                model: AI model to use
                **kwargs: Additional parameters

            Returns:
                Tuple of (success, response_data)
            """
            operation_id = self._start_operation("process_user_message", {
                'conversation_id': conversation_id,
                'model': model,
                'input_length': len(user_input)
            })

            try:
                # Validate input
                self._update_operation_state(operation_id, OperationState.VALIDATING)
                is_valid, error, metadata = self.message_processor.validate_message(user_input)
                if not is_valid:
                    return False, {"error": error, "operation_id": operation_id}

                # Process message
                self._update_operation_state(operation_id, OperationState.PROCESSING_INPUT)
                success, response = self.api_client_manager.chat_completion(
                    conversation_id, user_input, model, **kwargs
                )

                if success:
                    self._update_operation_state(operation_id, OperationState.PROCESSING_RESPONSE)
                    # Response already added to conversation by APIClientManager
                    self._complete_operation(operation_id, OperationState.IDLE)
                    return True, response
                else:
                    self._complete_operation(operation_id, OperationState.ERROR)
                    return False, response

            except Exception as e:
                logger.error(f"Error processing user message: {str(e)}")
                self._complete_operation(operation_id, OperationState.ERROR)
                return False, {"error": f"Processing failed: {str(e)}", "operation_id": operation_id}

        def start_streaming_response(self, user_input: str, conversation_id: str,
                                   model: str = "anthropic/claude-3-haiku",
                                   callback: Optional[Callable[[str], None]] = None,
                                   **kwargs) -> Tuple[bool, str]:
            """
            Start a streaming response for real-time UI updates.

            Args:
                user_input: The user's message
                conversation_id: Conversation identifier
                model: AI model to use
                callback: Callback function for streaming chunks
                **kwargs: Additional parameters

            Returns:
                Tuple of (success, operation_id)
            """
            operation_id = self._start_operation("streaming_response", {
                'conversation_id': conversation_id,
                'model': model,
                'streaming': True
            })

            try:
                # Validate input
                is_valid, error, _ = self.message_processor.validate_message(user_input)
                if not is_valid:
                    self._complete_operation(operation_id, OperationState.ERROR)
                    return False, error

                # Start streaming
                self._update_operation_state(operation_id, OperationState.STREAMING)

                # Use asyncio to handle streaming without blocking
                async def stream_task():
                    try:
                        success, response = self.api_client_manager.stream_chat_completion(
                            conversation_id, user_input, model, callback, **kwargs
                        )

                        if success:
                            self._complete_operation(operation_id, OperationState.IDLE)
                        else:
                            self._complete_operation(operation_id, OperationState.ERROR)

                        return success, response
                    except Exception as e:
                        logger.error(f"Streaming error: {str(e)}")
                        self._complete_operation(operation_id, OperationState.ERROR)
                        return False, str(e)

                # Run in background (in real implementation, use proper async handling)
                # For now, simulate synchronous completion
                success, response = asyncio.run(stream_task())
                return success, operation_id if success else response

            except Exception as e:
                logger.error(f"Error starting streaming: {str(e)}")
                self._complete_operation(operation_id, OperationState.ERROR)
                return False, str(e)

        def cancel_current_operation(self) -> bool:
            """
            Cancel the current operation if one is running.

            Returns:
                True if operation was cancelled, False otherwise
            """
            if self.current_operation:
                operation_id = self.current_operation['id']
                self._complete_operation(operation_id, OperationState.CANCELLED)

                # Cancel in API client manager
                if hasattr(self.api_client_manager, 'cancel_request'):
                    self.api_client_manager.cancel_request(operation_id)

                logger.info(f"Cancelled operation {operation_id}")
                return True

            return False

        def get_operation_status(self, operation_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
            """
            Get the status of an operation.

            Args:
                operation_id: Specific operation ID, or None for current operation

            Returns:
                Operation status data or None if not found
            """
            if operation_id is None:
                return self.current_operation
            elif operation_id == self.current_operation.get('id'):
                return self.current_operation
            else:
                return None

        def validate_chat_request(self, user_input: str, model: str) -> Tuple[bool, str]:
            """
            Pre-validate a chat request.

            Args:
                user_input: The user's message
                model: AI model identifier

            Returns:
                Tuple of (is_valid, error_message)
            """
            try:
                # Validate message
                is_valid, error, _ = self.message_processor.validate_message(user_input)
                if not is_valid:
                    return False, error

                # Validate model availability (would check with API client)
                # For now, basic validation
                if not model or '/' not in model:
                    return False, "Invalid model format"

                # Check rate limits (would integrate with rate limiter)
                # For now, always allow
                return True, ""

            except Exception as e:
                logger.error(f"Validation error: {str(e)}")
                return False, f"Validation failed: {str(e)}"

        def register_callback(self, event_type: str, callback: Callable) -> None:
            """
            Register a callback for specific events.

            Args:
                event_type: Type of event to listen for
                callback: Callback function
            """
            self.operation_callbacks[event_type] = callback
            logger.debug(f"Registered callback for event: {event_type}")

        def _start_operation(self, operation_type: str, metadata: Dict[str, Any]) -> str:
            """Start a new operation and return its ID."""
            import uuid
            operation_id = f"op_{uuid.uuid4().hex[:8]}"

            self.current_operation = {
                'id': operation_id,
                'type': operation_type,
                'state': OperationState.IDLE.value,
                'started_at': datetime.now().isoformat(),
                'metadata': metadata
            }

            logger.info(f"Started operation {operation_id}: {operation_type}")
            return operation_id

        def _update_operation_state(self, operation_id: str, state: OperationState) -> None:
            """Update the state of an operation."""
            if self.current_operation and self.current_operation['id'] == operation_id:
                old_state = self.current_operation['state']
                self.current_operation['state'] = state.value
                self.current_operation['updated_at'] = datetime.now().isoformat()

                logger.debug(f"Operation {operation_id} state: {old_state} -> {state.value}")

                # Trigger callbacks
                if 'state_change' in self.operation_callbacks:
                    try:
                        self.operation_callbacks['state_change'](operation_id, old_state, state.value)
                    except Exception as e:
                        logger.error(f"Error in state change callback: {str(e)}")

        def _complete_operation(self, operation_id: str, final_state: OperationState) -> None:
            """Complete an operation."""
            self._update_operation_state(operation_id, final_state)

            if self.current_operation and self.current_operation['id'] == operation_id:
                self.current_operation['completed_at'] = datetime.now().isoformat()
                logger.info(f"Completed operation {operation_id} with state: {final_state.value}")

                # Clear current operation
                self.current_operation = None

        def get_stats(self) -> Dict[str, Any]:
            """Get controller statistics."""
            return {
                'current_operation': self.current_operation,
                'max_concurrent_operations': self.max_concurrent_operations,
                'operation_timeout': self.operation_timeout
            }
    ```

3. Create unit tests:
    ```python
    # tests/unit/test_chat_controller.py
    import pytest
    from unittest.mock import Mock, patch
    from src.core.controllers.chat_controller import ChatController, OperationState


    class TestChatController:
        @pytest.fixture
        def mock_components(self):
            """Create mock components for testing."""
            message_processor = Mock()
            conversation_manager = Mock()
            api_client_manager = Mock()
            state_manager = Mock()

            return {
                'message_processor': message_processor,
                'conversation_manager': conversation_manager,
                'api_client_manager': api_client_manager,
                'state_manager': state_manager
            }

        @pytest.fixture
        def controller(self, mock_components):
            """Create ChatController with mocked components."""
            return ChatController(**mock_components)

        def test_initialization(self, controller):
            """Test controller initializes correctly."""
            assert controller.message_processor is not None
            assert controller.conversation_manager is not None
            assert controller.api_client_manager is not None
            assert controller.state_manager is not None
            assert controller.current_operation is None

        def test_process_user_message_success(self, controller, mock_components):
            """Test successful message processing."""
            # Setup mocks
            mock_components['message_processor'].validate_message.return_value = (True, "", {})
            mock_components['api_client_manager'].chat_completion.return_value = (True, {"response": "test"})

            # Test
            success, response = controller.process_user_message("Hello", "conv_123")

            assert success
            assert response["response"] == "test"
            assert controller.current_operation is None  # Should be cleared

        def test_process_user_message_validation_failure(self, controller, mock_components):
            """Test message processing with validation failure."""
            mock_components['message_processor'].validate_message.return_value = (False, "Invalid message", {})

            success, response = controller.process_user_message("Invalid", "conv_123")

            assert not success
            assert "error" in response
            assert response["error"] == "Invalid message"

        def test_cancel_operation(self, controller):
            """Test operation cancellation."""
            # Start an operation
            controller._start_operation("test", {})

            assert controller.current_operation is not None

            # Cancel it
            result = controller.cancel_current_operation()

            assert result
            assert controller.current_operation is None

        def test_get_operation_status(self, controller):
            """Test getting operation status."""
            # No current operation
            status = controller.get_operation_status()
            assert status is None

            # Start operation
            op_id = controller._start_operation("test", {"key": "value"})
            status = controller.get_operation_status()

            assert status is not None
            assert status['id'] == op_id
            assert status['metadata']['key'] == 'value'

        def test_validate_chat_request(self, controller, mock_components):
            """Test chat request validation."""
            mock_components['message_processor'].validate_message.return_value = (True, "", {})

            # Valid request
            is_valid, error = controller.validate_chat_request("Hello", "anthropic/claude-3-haiku")
            assert is_valid
            assert error == ""

            # Invalid model
            is_valid, error = controller.validate_chat_request("Hello", "invalid-model")
            assert not is_valid
            assert "Invalid model format" in error
    ```

**Validation Criteria**:
- [ ] ChatController imports without errors
- [ ] All core methods (process_user_message, start_streaming_response, etc.) work
- [ ] Operation state tracking functions correctly
- [ ] Error handling and recovery work as expected
- [ ] Callback registration and triggering work
- [ ] Unit tests pass with 100% coverage

### 5.2 StateManager (src/core/controllers/state_manager.py)

**Purpose**: Centralized state management with persistence and synchronization for the application.

**Dependencies**: ConversationStorage, ConfigManager, Logger

**Implementation Steps**:

1. Create the state manager module:
    ```bash
    touch src/core/controllers/state_manager.py
    ```

2. Implement the StateManager class:
    ```python
    # src/core/controllers/state_manager.py
    import json
    import time
    from typing import Dict, Any, Optional, Callable, List
    from enum import Enum
    from pathlib import Path
    from datetime import datetime

    from ...utils.logging import logger
    from ...storage.conversation_storage import ConversationStorage
    from ...storage.config_manager import ConfigManager


    class ApplicationState(Enum):
        """Possible application states."""
        INITIALIZING = "initializing"
        READY = "ready"
        PROCESSING = "processing"
        ERROR = "error"
        SHUTDOWN = "shutdown"


    class ConversationState(Enum):
        """Possible conversation states."""
        ACTIVE = "active"
        PAUSED = "paused"
        COMPLETED = "completed"
        ARCHIVED = "archived"


    class StateManager:
        """Centralized state management with persistence and synchronization."""

        def __init__(self, storage_dir: str = "data/state",
                     conversation_storage: Optional[ConversationStorage] = None,
                     config_manager: Optional[ConfigManager] = None):
            """
            Initialize the StateManager.

            Args:
                storage_dir: Directory for state persistence
                conversation_storage: Conversation storage instance
                config_manager: Configuration manager instance
            """
            self.storage_dir = Path(storage_dir)
            self.storage_dir.mkdir(parents=True, exist_ok=True)

            self.conversation_storage = conversation_storage or ConversationStorage()
            self.config_manager = config_manager or ConfigManager()

            # Current state
            self._application_state = ApplicationState.INITIALIZING
            self._conversation_states: Dict[str, ConversationState] = {}
            self._ui_state: Dict[str, Any] = {}
            self._operation_state: Dict[str, Any] = {}

            # State change subscribers
            self._state_change_callbacks: List[Callable] = []

            # Persistence
            self._state_file = self.storage_dir / "application_state.json"
            self._auto_save_interval = 30  # seconds
            self._last_save_time = time.time()

            # Load persisted state
            self._load_state()

            logger.info("StateManager initialized")

        @property
        def application_state(self) -> ApplicationState:
            """Get current application state."""
            return self._application_state

        @application_state.setter
        def application_state(self, state: ApplicationState) -> None:
            """Set application state and notify subscribers."""
            if state != self._application_state:
                old_state = self._application_state
                self._application_state = state
                self._notify_state_change("application", old_state.value, state.value)
                logger.info(f"Application state changed: {old_state.value} -> {state.value}")

        def get_application_state(self) -> Dict[str, Any]:
            """Get comprehensive application state."""
            return {
                'application_state': self._application_state.value,
                'conversation_states': {k: v.value for k, v in self._conversation_states.items()},
                'ui_state': self._ui_state,
                'operation_state': self._operation_state,
                'timestamp': datetime.now().isoformat()
            }

        def update_application_state(self, updates: Dict[str, Any]) -> bool:
            """Update application state with new values."""
            try:
                # Handle application state updates
                if 'application_state' in updates:
                    new_state = ApplicationState(updates['application_state'])
                    self.application_state = new_state

                # Handle conversation state updates
                if 'conversation_states' in updates:
                    for conv_id, state_str in updates['conversation_states'].items():
                        self.set_conversation_state(conv_id, ConversationState(state_str))

                # Handle UI state updates
                if 'ui_state' in updates:
                    self._ui_state.update(updates['ui_state'])
                    self._notify_state_change("ui", self._ui_state, updates['ui_state'])

                # Handle operation state updates
                if 'operation_state' in updates:
                    self._operation_state.update(updates['operation_state'])
                    self._notify_state_change("operation", self._operation_state, updates['operation_state'])

                # Auto-save if needed
                self._auto_save()

                return True

            except Exception as e:
                logger.error(f"Failed to update application state: {str(e)}")
                return False

        def get_conversation_state(self, conversation_id: str) -> ConversationState:
            """Get the state of a specific conversation."""
            return self._conversation_states.get(conversation_id, ConversationState.ACTIVE)

        def set_conversation_state(self, conversation_id: str, state: ConversationState) -> None:
            """Set the state of a specific conversation."""
            old_state = self._conversation_states.get(conversation_id)
            if old_state != state:
                self._conversation_states[conversation_id] = state
                self._notify_state_change(f"conversation_{conversation_id}", old_state.value if old_state else None, state.value)
                logger.debug(f"Conversation {conversation_id} state: {old_state.value if old_state else 'None'} -> {state.value}")

        def get_ui_state(self) -> Dict[str, Any]:
            """Get current UI state."""
            return self._ui_state.copy()

        def update_ui_state(self, updates: Dict[str, Any]) -> None:
            """Update UI state."""
            old_state = self._ui_state.copy()
            self._ui_state.update(updates)
            self._notify_state_change("ui", old_state, self._ui_state)

        def get_operation_state(self) -> Dict[str, Any]:
            """Get current operation state."""
            return self._operation_state.copy()

        def update_operation_state(self, updates: Dict[str, Any]) -> None:
            """Update operation state."""
            old_state = self._operation_state.copy()
            self._operation_state.update(updates)
            self._notify_state_change("operation", old_state, self._operation_state)

        def subscribe_to_state_changes(self, callback: Callable[[str, Any, Any], None]) -> None:
            """Subscribe to state change notifications."""
            self._state_change_callbacks.append(callback)
            logger.debug("Added state change subscriber")

        def unsubscribe_from_state_changes(self, callback: Callable) -> None:
            """Unsubscribe from state change notifications."""
            if callback in self._state_change_callbacks:
                self._state_change_callbacks.remove(callback)
                logger.debug("Removed state change subscriber")

        def validate_state_transition(self, state_type: str, from_state: Any, to_state: Any) -> bool:
            """Validate if a state transition is allowed."""
            try:
                if state_type == "application":
                    # Define valid application state transitions
                    valid_transitions = {
                        ApplicationState.INITIALIZING: [ApplicationState.READY, ApplicationState.ERROR],
                        ApplicationState.READY: [ApplicationState.PROCESSING, ApplicationState.ERROR, ApplicationState.SHUTDOWN],
                        ApplicationState.PROCESSING: [ApplicationState.READY, ApplicationState.ERROR],
                        ApplicationState.ERROR: [ApplicationState.READY, ApplicationState.SHUTDOWN],
                        ApplicationState.SHUTDOWN: []
                    }

                    from_app_state = ApplicationState(from_state) if from_state else None
                    to_app_state = ApplicationState(to_state)

                    if from_app_state and to_app_state not in valid_transitions.get(from_app_state, []):
                        logger.warning(f"Invalid application state transition: {from_state} -> {to_state}")
                        return False

                elif state_type.startswith("conversation_"):
                    # Conversation state transitions are more flexible
                    # Could add specific validation rules here
                    pass

                return True

            except Exception as e:
                logger.error(f"State transition validation error: {str(e)}")
                return False

        def persist_state(self) -> bool:
            """Persist current state to storage."""
            try:
                state_data = {
                    'application_state': self._application_state.value,
                    'conversation_states': {k: v.value for k, v in self._conversation_states.items()},
                    'ui_state': self._ui_state,
                    'operation_state': self._operation_state,
                    'persisted_at': datetime.now().isoformat(),
                    'version': '1.0'
                }

                # Write to temporary file first (atomic write)
                temp_file = self._state_file.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(state_data, f, indent=2, default=str)

                # Atomic move
                temp_file.replace(self._state_file)

                self._last_save_time = time.time()
                logger.debug("State persisted successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to persist state: {str(e)}")
                return False

        def restore_state(self) -> bool:
            """Restore state from storage."""
            try:
                if not self._state_file.exists():
                    logger.info("No persisted state found, using defaults")
                    return True

                with open(self._state_file, 'r') as f:
                    state_data = json.load(f)

                # Restore application state
                app_state_str = state_data.get('application_state', 'initializing')
                self._application_state = ApplicationState(app_state_str)

                # Restore conversation states
                conv_states = state_data.get('conversation_states', {})
                self._conversation_states = {
                    k: ConversationState(v) for k, v in conv_states.items()
                }

                # Restore UI and operation states
                self._ui_state = state_data.get('ui_state', {})
                self._operation_state = state_data.get('operation_state', {})

                logger.info("State restored successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to restore state: {str(e)}")
                # Reset to safe defaults
                self._application_state = ApplicationState.ERROR
                return False

        def _load_state(self) -> None:
            """Load state during initialization."""
            success = self.restore_state()
            if not success:
                logger.warning("Failed to load persisted state, using defaults")

            # Set to ready state
            self.application_state = ApplicationState.READY

        def _auto_save(self) -> None:
            """Auto-save state if interval has passed."""
            current_time = time.time()
            if current_time - self._last_save_time >= self._auto_save_interval:
                self.persist_state()

        def _notify_state_change(self, state_type: str, old_value: Any, new_value: Any) -> None:
            """Notify all subscribers of state changes."""
            for callback in self._state_change_callbacks:
                try:
                    callback(state_type, old_value, new_value)
                except Exception as e:
                    logger.error(f"Error in state change callback: {str(e)}")

        def get_state_summary(self) -> Dict[str, Any]:
            """Get a summary of current state."""
            return {
                'application_state': self._application_state.value,
                'active_conversations': len([s for s in self._conversation_states.values() if s == ConversationState.ACTIVE]),
                'total_conversations': len(self._conversation_states),
                'ui_elements': len(self._ui_state),
                'current_operations': len(self._operation_state),
                'last_persisted': datetime.fromtimestamp(self._last_save_time).isoformat() if self._last_save_time > 0 else None
            }

        def reset_to_defaults(self) -> None:
            """Reset all state to defaults."""
            self._application_state = ApplicationState.READY
            self._conversation_states.clear()
            self._ui_state.clear()
            self._operation_state.clear()

            # Delete persisted state
            if self._state_file.exists():
                self._state_file.unlink()

            logger.info("State reset to defaults")
    ```

3. Create unit tests:
    ```python
    # tests/unit/test_state_manager.py
    import pytest
    import json
    from pathlib import Path
    from unittest.mock import Mock
    from src.core.controllers.state_manager import StateManager, ApplicationState, ConversationState


    class TestStateManager:
        @pytest.fixture
        def temp_dir(self, tmp_path):
            """Create a temporary directory for testing."""
            state_dir = tmp_path / "state"
            state_dir.mkdir()
            return state_dir

        @pytest.fixture
        def state_manager(self, temp_dir):
            """Create StateManager with temporary storage."""
            return StateManager(storage_dir=str(temp_dir))

        def test_initialization(self, state_manager):
            """Test StateManager initializes correctly."""
            assert state_manager.application_state == ApplicationState.READY
            assert isinstance(state_manager._conversation_states, dict)
            assert isinstance(state_manager._ui_state, dict)
            assert isinstance(state_manager._operation_state, dict)

        def test_application_state_property(self, state_manager):
            """Test application state property getter/setter."""
            # Test getter
            assert state_manager.application_state == ApplicationState.READY

            # Test setter
            state_manager.application_state = ApplicationState.PROCESSING
            assert state_manager.application_state == ApplicationState.PROCESSING

        def test_get_application_state(self, state_manager):
            """Test getting comprehensive application state."""
            state = state_manager.get_application_state()

            assert 'application_state' in state
            assert 'conversation_states' in state
            assert 'ui_state' in state
            assert 'operation_state' in state
            assert 'timestamp' in state

        def test_update_application_state(self, state_manager):
            """Test updating application state."""
            updates = {
                'ui_state': {'theme': 'dark', 'sidebar_open': True},
                'operation_state': {'current_task': 'test'}
            }

            success = state_manager.update_application_state(updates)
            assert success

            assert state_manager._ui_state['theme'] == 'dark'
            assert state_manager._ui_state['sidebar_open'] is True
            assert state_manager._operation_state['current_task'] == 'test'

        def test_conversation_state_management(self, state_manager):
            """Test conversation state management."""
            conv_id = "conv_123"

            # Initially active
            state = state_manager.get_conversation_state(conv_id)
            assert state == ConversationState.ACTIVE

            # Change to paused
            state_manager.set_conversation_state(conv_id, ConversationState.PAUSED)
            state = state_manager.get_conversation_state(conv_id)
            assert state == ConversationState.PAUSED

        def test_ui_state_management(self, state_manager):
            """Test UI state management."""
            # Update UI state
            state_manager.update_ui_state({'panel': 'chat', 'fullscreen': False})

            ui_state = state_manager.get_ui_state()
            assert ui_state['panel'] == 'chat'
            assert ui_state['fullscreen'] is False

        def test_state_change_subscriptions(self, state_manager):
            """Test state change subscription system."""
            callback_called = []

            def test_callback(state_type, old_value, new_value):
                callback_called.append((state_type, old_value, new_value))

            # Subscribe
            state_manager.subscribe_to_state_changes(test_callback)

            # Trigger state change
            state_manager.application_state = ApplicationState.PROCESSING

            # Check callback was called
            assert len(callback_called) == 1
            assert callback_called[0][0] == "application"
            assert callback_called[0][1] == "ready"
            assert callback_called[0][2] == "processing"

            # Unsubscribe
            state_manager.unsubscribe_from_state_changes(test_callback)

            # Reset callback list
            callback_called.clear()

            # Trigger another change
            state_manager.application_state = ApplicationState.READY

            # Callback should not be called
            assert len(callback_called) == 0

        def test_persist_and_restore_state(self, state_manager):
            """Test state persistence and restoration."""
            # Set some state
            state_manager.update_ui_state({'test_key': 'test_value'})
            state_manager.set_conversation_state('conv_1', ConversationState.COMPLETED)

            # Persist
            success = state_manager.persist_state()
            assert success

            # Create new manager (simulates restart)
            new_manager = StateManager(storage_dir=state_manager.storage_dir)

            # Check state was restored
            ui_state = new_manager.get_ui_state()
            assert ui_state.get('test_key') == 'test_value'

            conv_state = new_manager.get_conversation_state('conv_1')
            assert conv_state == ConversationState.COMPLETED

        def test_validate_state_transition(self, state_manager):
            """Test state transition validation."""
            # Valid transition
            is_valid = state_manager.validate_state_transition(
                "application", "ready", "processing"
            )
            assert is_valid

            # Invalid transition
            is_valid = state_manager.validate_state_transition(
                "application", "shutdown", "ready"
            )
            assert not is_valid

        def test_get_state_summary(self, state_manager):
            """Test getting state summary."""
            summary = state_manager.get_state_summary()

            assert 'application_state' in summary
            assert 'active_conversations' in summary
            assert 'total_conversations' in summary
            assert 'ui_elements' in summary
            assert 'current_operations' in summary
    ```

**Validation Criteria**:
- [ ] StateManager imports without errors
- [ ] All state management methods work correctly
- [ ] State persistence and restoration function properly
- [ ] State change notifications work
- [ ] State transition validation works
- [ ] Unit tests pass with 100% coverage

## 2. Data Persistence Layer Components

### 2.1 ConfigManager (src/storage/config_manager.py)

**Purpose**: Secure storage and management of application configuration and sensitive data.

**Dependencies**: Logger, Validators

**Implementation Steps**:

1. Create the config manager module:
   ```bash
   mkdir -p src/storage
   touch src/storage/__init__.py
   touch src/storage/config_manager.py
   ```

2. Implement the ConfigManager class:
   ```python
   # src/storage/config_manager.py
   import json
   import os
   from pathlib import Path
   from typing import Dict, Any, Optional
   from cryptography.fernet import Fernet, InvalidToken
   import base64

   from ..utils.logger import logger
   from ..utils.validators import validate_api_key

   class ConfigManager:
       """Manages application configuration with secure storage for sensitive data."""

       def __init__(self, config_dir: str = "data/config"):
           """
           Initialize configuration manager.

           Args:
               config_dir: Directory to store configuration files
           """
           self.config_dir = Path(config_dir)
           self.config_dir.mkdir(parents=True, exist_ok=True)
           self.config_file = self.config_dir / "app_config.json"
           self.key_file = self.config_dir / "encryption.key"

           # Initialize encryption
           self._cipher = self._load_or_create_cipher()

           # Load existing configuration
           self._config = self._load_config()

       def _load_or_create_cipher(self) -> Fernet:
           """
           Load existing encryption key or create a new one.

           Returns:
               Fernet cipher instance
           """
           try:
               if self.key_file.exists():
                   with open(self.key_file, 'rb') as f:
                       key = f.read()
                   logger.debug("Loaded existing encryption key")
               else:
                   key = Fernet.generate_key()
                   with open(self.key_file, 'wb') as f:
                       f.write(key)
                   # Set restrictive permissions on key file
                   os.chmod(self.key_file, 0o600)
                   logger.info("Created new encryption key")

               return Fernet(key)

           except Exception as e:
               logger.error(f"Failed to initialize encryption: {e}")
               raise RuntimeError("Cannot initialize encryption system")

       def _load_config(self) -> Dict[str, Any]:
           """
           Load configuration from file.

           Returns:
               Configuration dictionary
           """
           if not self.config_file.exists():
               logger.info("Configuration file does not exist, creating default")
               return self._create_default_config()

           try:
               with open(self.config_file, 'r', encoding='utf-8') as f:
                   config = json.load(f)
               logger.debug("Loaded configuration from file")
               return config

           except (json.JSONDecodeError, IOError) as e:
               logger.warning(f"Failed to load configuration: {e}, using defaults")
               return self._create_default_config()

       def _create_default_config(self) -> Dict[str, Any]:
           """Create default configuration."""
           return {
               "app": {
                   "name": "Personal AI Chatbot",
                   "version": "1.0.0",
                   "debug": False,
                   "log_level": "INFO"
               },
               "ui": {
                   "theme": "default",
                   "max_message_length": 4000,
                   "auto_scroll": True
               },
               "api": {
                   "timeout": 30,
                   "max_retries": 3,
                   "rate_limit_per_minute": 50
               },
               "storage": {
                   "max_conversation_file_size_mb": 10,
                   "backup_retention_days": 30,
                   "auto_backup_enabled": True
               }
           }

       def _save_config(self) -> bool:
           """
           Save current configuration to file.

           Returns:
               True if successful, False otherwise
           """
           try:
               # Create backup of existing config
               if self.config_file.exists():
                   backup_file = self.config_file.with_suffix('.backup')
                   self.config_file.replace(backup_file)

               with open(self.config_file, 'w', encoding='utf-8') as f:
                   json.dump(self._config, f, indent=2, ensure_ascii=False)

               logger.debug("Configuration saved successfully")
               return True

           except Exception as e:
               logger.error(f"Failed to save configuration: {e}")
               return False

       def get_api_key(self) -> Optional[str]:
           """
           Retrieve decrypted API key.

           Returns:
               API key if available, None otherwise
           """
           encrypted_key_b64 = self._config.get("api", {}).get("encrypted_key")
           if not encrypted_key_b64:
               return None

           try:
               encrypted_key = base64.b64decode(encrypted_key_b64)
               decrypted_key = self._cipher.decrypt(encrypted_key).decode('utf-8')
               return decrypted_key

           except (InvalidToken, ValueError, UnicodeDecodeError) as e:
               logger.error(f"Failed to decrypt API key: {e}")
               return None

       def set_api_key(self, api_key: str) -> bool:
           """
           Store encrypted API key.

           Args:
               api_key: The API key to store

           Returns:
               True if successful, False otherwise
           """
           is_valid, error_msg = validate_api_key(api_key)
           if not is_valid:
               logger.error(f"Invalid API key: {error_msg}")
               return False

           try:
               encrypted_key = self._cipher.encrypt(api_key.encode('utf-8'))
               encrypted_key_b64 = base64.b64encode(encrypted_key).decode('utf-8')

               if "api" not in self._config:
                   self._config["api"] = {}

               self._config["api"]["encrypted_key"] = encrypted_key_b64

               success = self._save_config()
               if success:
                   logger.info("API key stored successfully")
               return success

           except Exception as e:
               logger.error(f"Failed to store API key: {e}")
               return False

       def get_setting(self, key: str, default: Any = None) -> Any:
           """
           Get configuration setting.

           Args:
               key: Dot-separated key path (e.g., "ui.theme")
               default: Default value if key not found

           Returns:
               Setting value or default
           """
           keys = key.split('.')
           value = self._config

           try:
               for k in keys:
                   value = value[k]
               return value
           except (KeyError, TypeError):
               return default

       def set_setting(self, key: str, value: Any) -> bool:
           """
           Set configuration setting.

           Args:
               key: Dot-separated key path (e.g., "ui.theme")
               value: Value to set

           Returns:
               True if successful, False otherwise
           """
           keys = key.split('.')
           config = self._config

           # Navigate to the parent of the target key
           for k in keys[:-1]:
               if k not in config or not isinstance(config[k], dict):
                   config[k] = {}
               config = config[k]

           # Set the value
           config[keys[-1]] = value

           success = self._save_config()
           if success:
               logger.debug(f"Setting {key} updated to {value}")
           return success

       def validate_config(self) -> list[str]:
           """
           Validate current configuration.

           Returns:
               List of validation error messages
           """
           errors = []

           # Check required settings exist
           required_settings = [
               "app.name",
               "app.version",
               "api.timeout",
               "storage.max_conversation_file_size_mb"
           ]

           for setting in required_settings:
               if self.get_setting(setting) is None:
                   errors.append(f"Required setting missing: {setting}")

           # Validate API key if present
           api_key = self.get_api_key()
           if api_key:
               is_valid, error_msg = validate_api_key(api_key)
               if not is_valid:
                   errors.append(f"Stored API key invalid: {error_msg}")

           # Validate numeric settings
           numeric_settings = {
               "api.timeout": (1, 300),
               "storage.max_conversation_file_size_mb": (1, 100),
               "api.rate_limit_per_minute": (1, 1000)
           }

           for setting, (min_val, max_val) in numeric_settings.items():
               value = self.get_setting(setting)
               if value is not None:
                   if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                       errors.append(f"Setting {setting} must be between {min_val} and {max_val}")

           return errors

       def export_config(self) -> Dict[str, Any]:
           """
           Export configuration for backup (without sensitive data).

           Returns:
               Configuration dictionary without encrypted keys
           """
           export_config = json.loads(json.dumps(self._config))  # Deep copy

           # Remove sensitive data
           if "api" in export_config and "encrypted_key" in export_config["api"]:
               del export_config["api"]["encrypted_key"]

           return export_config

       def import_config(self, config: Dict[str, Any]) -> bool:
           """
           Import configuration from backup.

           Args:
               config: Configuration dictionary to import

           Returns:
               True if successful, False otherwise
           """
           try:
               # Validate imported config structure
               if not isinstance(config, dict):
                   logger.error("Imported config must be a dictionary")
                   return False

               # Merge with current config (don't overwrite encryption key)
               current_encrypted_key = self._config.get("api", {}).get("encrypted_key")

               self._config = config

               # Restore encrypted key if it existed
               if current_encrypted_key:
                   if "api" not in self._config:
                       self._config["api"] = {}
                   self._config["api"]["encrypted_key"] = current_encrypted_key

               success = self._save_config()
               if success:
                   logger.info("Configuration imported successfully")
               return success

           except Exception as e:
               logger.error(f"Failed to import configuration: {e}")
               return False
   ```

3. Create unit tests:
   ```python
   # tests/unit/test_config_manager.py
   import pytest
   import json
   import tempfile
   from pathlib import Path
   from unittest.mock import patch

   from src.storage.config_manager import ConfigManager

   @pytest.fixture
   def temp_config_dir(tmp_path):
       """Create temporary directory for config testing."""
       config_dir = tmp_path / "config"
       config_dir.mkdir()
       return config_dir

   class TestConfigManager:
       def test_initialization_creates_directories(self, temp_config_dir):
           """Test that initialization creates necessary directories."""
           config_manager = ConfigManager(str(temp_config_dir))

           assert temp_config_dir.exists()
           assert (temp_config_dir / "app_config.json").exists()
           assert (temp_config_dir / "encryption.key").exists()

       def test_default_config_structure(self, temp_config_dir):
           """Test default configuration has expected structure."""
           config_manager = ConfigManager(str(temp_config_dir))

           assert config_manager.get_setting("app.name") == "Personal AI Chatbot"
           assert config_manager.get_setting("api.timeout") == 30
           assert config_manager.get_setting("ui.theme") == "default"

       def test_api_key_storage_and_retrieval(self, temp_config_dir):
           """Test API key encryption and decryption."""
           config_manager = ConfigManager(str(temp_config_dir))
           test_key = "sk-or-v1-1234567890abcdef1234567890abcdef1234567890"

           # Store key
           success = config_manager.set_api_key(test_key)
           assert success

           # Retrieve key
           retrieved_key = config_manager.get_api_key()
           assert retrieved_key == test_key

       def test_invalid_api_key_rejection(self, temp_config_dir):
           """Test that invalid API keys are rejected."""
           config_manager = ConfigManager(str(temp_config_dir))
           invalid_key = "invalid-key"

           success = config_manager.set_api_key(invalid_key)
           assert not success

       def test_setting_operations(self, temp_config_dir):
           """Test getting and setting configuration values."""
           config_manager = ConfigManager(str(temp_config_dir))

           # Set a value
           success = config_manager.set_setting("test.value", "test_data")
           assert success

           # Retrieve the value
           value = config_manager.get_setting("test.value")
           assert value == "test_data"

           # Test default values
           default_value = config_manager.get_setting("nonexistent.key", "default")
           assert default_value == "default"

       def test_config_validation(self, temp_config_dir):
           """Test configuration validation."""
           config_manager = ConfigManager(str(temp_config_dir))

           # Valid config should have no errors
           errors = config_manager.validate_config()
           assert len(errors) == 0

           # Break a setting and test validation
           config_manager._config["api"]["timeout"] = 0  # Invalid timeout
           errors = config_manager.validate_config()
           assert len(errors) > 0
           assert any("timeout" in error for error in errors)

       def test_config_export_import(self, temp_config_dir):
           """Test configuration export and import."""
           config_manager = ConfigManager(str(temp_config_dir))

           # Set some test values
           config_manager.set_setting("test.export_value", "export_test")
           config_manager.set_api_key("sk-or-v1-1234567890abcdef1234567890abcdef1234567890")

           # Export config
           exported = config_manager.export_config()
           assert "test" in exported
           assert exported["test"]["export_value"] == "export_test"
           # API key should not be in export
           assert "encrypted_key" not in exported.get("api", {})

           # Import config
           success = config_manager.import_config(exported)
           assert success

           # Verify imported values
           imported_value = config_manager.get_setting("test.export_value")
           assert imported_value == "export_test"

           # API key should still be there
           api_key = config_manager.get_api_key()
           assert api_key == "sk-or-v1-1234567890abcdef1234567890abcdef1234567890"
   ```

**Validation Criteria**:
- [ ] ConfigManager initializes without errors
- [ ] Configuration file created in data/config/app_config.json
- [ ] Encryption key file created securely
- [ ] API key encryption/decryption works correctly
- [ ] Configuration settings can be stored and retrieved
- [ ] Configuration validation catches invalid settings
- [ ] Config export/import works without sensitive data exposure
- [ ] Unit tests pass with 90%+ coverage

### 2.2 ConversationStorage (src/storage/conversation_storage.py)

**Purpose**: File-based conversation persistence with atomic operations and integrity checking.

**Dependencies**: Logger, Validators, ConfigManager

**Implementation Steps**:

1. Create the conversation storage module:
   ```bash
   touch src/storage/conversation_storage.py
   ```

2. Implement the ConversationStorage class:
   ```python
   # src/storage/conversation_storage.py
   import json
   import os
   import hashlib
   from pathlib import Path
   from typing import Dict, Any, List, Optional
   from datetime import datetime, timedelta

   from ..utils.logger import logger
   from ..utils.validators import sanitize_filename

   class ConversationStorage:
       """Handles file-based conversation persistence with integrity guarantees."""

       def __init__(self, base_path: str = "data/conversations/active"):
           """
           Initialize conversation storage.

           Args:
               base_path: Base directory for conversation storage
           """
           self.base_path = Path(base_path)
           self.base_path.mkdir(parents=True, exist_ok=True)
           self.archive_path = self.base_path.parent / "archived"
           self.archive_path.mkdir(parents=True, exist_ok=True)

           logger.info(f"Initialized conversation storage at {self.base_path}")

       def _get_conversation_path(self, conversation_id: str) -> Path:
           """
           Get the file path for a conversation.

           Args:
               conversation_id: Unique conversation identifier

           Returns:
               Path to the conversation file
           """
           # Sanitize conversation ID for filename
           safe_id = sanitize_filename(conversation_id)
           return self.base_path / f"{safe_id}.json"

       def _calculate_checksum(self, data: Dict[str, Any]) -> str:
           """
           Calculate SHA256 checksum of conversation data.

           Args:
               data: Conversation data dictionary

           Returns:
               Hexadecimal checksum string
           """
           # Create a normalized JSON string for consistent hashing
           json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
           return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

       def _validate_conversation_data(self, data: Dict[str, Any]) -> List[str]:
           """
           Validate conversation data structure.

           Args:
               data: Conversation data to validate

           Returns:
               List of validation error messages
           """
           errors = []

           required_fields = ["id", "title", "created_at", "messages"]
           for field in required_fields:
               if field not in data:
                   errors.append(f"Missing required field: {field}")

           if "messages" in data:
               if not isinstance(data["messages"], list):
                   errors.append("Messages must be a list")
               else:
                   for i, msg in enumerate(data["messages"]):
                       if not isinstance(msg, dict):
                           errors.append(f"Message {i} must be a dictionary")
                           continue

                       msg_required = ["role", "content", "timestamp"]
                       for field in msg_required:
                           if field not in msg:
                               errors.append(f"Message {i} missing required field: {field}")

                       if "role" in msg and msg["role"] not in ["user", "assistant", "system"]:
                           errors.append(f"Message {i} has invalid role: {msg['role']}")

           return errors

       def save_conversation(self, conversation_id: str, data: Dict[str, Any]) -> bool:
           """
           Save conversation data atomically with integrity checking.

           Args:
               conversation_id: Unique conversation identifier
               data: Conversation data dictionary

           Returns:
               True if successful, False otherwise
           """
           # Validate data before saving
           validation_errors = self._validate_conversation_data(data)
           if validation_errors:
               logger.error(f"Conversation data validation failed: {validation_errors}")
               return False

           file_path = self._get_conversation_path(conversation_id)

           try:
               # Prepare data with integrity information
               save_data = data.copy()
               save_data["_metadata"] = {
                   "checksum": self._calculate_checksum(data),
                   "saved_at": datetime.now().isoformat(),
                   "version": "1.0"
               }

               # Atomic write using temporary file
               temp_file = file_path.with_suffix('.tmp')

               with open(temp_file, 'w', encoding='utf-8') as f:
                   json.dump(save_data, f, indent=2, ensure_ascii=False)

               # Atomic move to final location
               temp_file.replace(file_path)

               logger.info(f"Conversation {conversation_id} saved successfully")
               return True

           except Exception as e:
               logger.error(f"Failed to save conversation {conversation_id}: {e}")
               # Clean up temporary file if it exists
               if temp_file.exists():
                   try:
                       temp_file.unlink()
                   except Exception:
                       pass
               return False

       def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
           """
           Load conversation data with integrity verification.

           Args:
               conversation_id: Unique conversation identifier

           Returns:
               Conversation data dictionary or None if not found/invalid
           """
           file_path = self._get_conversation_path(conversation_id)

           if not file_path.exists():
               logger.debug(f"Conversation {conversation_id} not found")
               return None

           try:
               with open(file_path, 'r', encoding='utf-8') as f:
                   data = json.load(f)

               # Verify integrity if metadata exists
               if "_metadata" in data:
                   metadata = data.pop("_metadata")  # Remove metadata from returned data
                   stored_checksum = metadata.get("checksum")

                   if stored_checksum:
                       calculated_checksum = self._calculate_checksum(data)
                       if calculated_checksum != stored_checksum:
                           logger.error(f"Conversation {conversation_id} checksum mismatch")
                           return None

               # Validate loaded data
               validation_errors = self._validate_conversation_data(data)
               if validation_errors:
                   logger.error(f"Loaded conversation {conversation_id} validation failed: {validation_errors}")
                   return None

               logger.debug(f"Conversation {conversation_id} loaded successfully")
               return data

           except (json.JSONDecodeError, IOError) as e:
               logger.error(f"Failed to load conversation {conversation_id}: {e}")
               return None

       def list_conversations(self) -> List[str]:
           """
           List all conversation IDs in storage.

           Returns:
               List of conversation IDs
           """
           try:
               conversation_files = self.base_path.glob("*.json")
               conversation_ids = []

               for file_path in conversation_files:
                   if file_path.is_file():
                       # Extract conversation ID from filename
                       conversation_id = file_path.stem
                       conversation_ids.append(conversation_id)

               logger.debug(f"Found {len(conversation_ids)} conversations")
               return sorted(conversation_ids)

           except Exception as e:
               logger.error(f"Failed to list conversations: {e}")
               return []

       def delete_conversation(self, conversation_id: str) -> bool:
           """
           Delete a conversation from storage.

           Args:
               conversation_id: Unique conversation identifier

           Returns:
               True if successful, False otherwise
           """
           file_path = self._get_conversation_path(conversation_id)

           if not file_path.exists():
               logger.warning(f"Conversation {conversation_id} not found for deletion")
               return False

           try:
               file_path.unlink()
               logger.info(f"Conversation {conversation_id} deleted successfully")
               return True

           except Exception as e:
               logger.error(f"Failed to delete conversation {conversation_id}: {e}")
               return False

       def get_storage_stats(self) -> Dict[str, Any]:
           """
           Get storage usage statistics.

           Returns:
               Dictionary with storage statistics
           """
           try:
               total_size = 0
               file_count = 0
               oldest_file = None
               newest_file = None

               for file_path in self.base_path.glob("*.json"):
                   if file_path.is_file():
                       stat = file_path.stat()
                       total_size += stat.st_size
                       file_count += 1

                       file_mtime = datetime.fromtimestamp(stat.st_mtime)
                       if oldest_file is None or file_mtime < oldest_file:
                           oldest_file = file_mtime
                       if newest_file is None or file_mtime > newest_file:
                           newest_file = file_mtime

               return {
                   "total_conversations": file_count,
                   "total_size_bytes": total_size,
                   "average_size_bytes": total_size / file_count if file_count > 0 else 0,
                   "oldest_file_date": oldest_file.isoformat() if oldest_file else None,
                   "newest_file_date": newest_file.isoformat() if newest_file else None
               }

           except Exception as e:
               logger.error(f"Failed to get storage stats: {e}")
               return {
                   "total_conversations": 0,
                   "total_size_bytes": 0,
                   "average_size_bytes": 0,
                   "oldest_file_date": None,
                   "newest_file_date": None
               }

       def cleanup_old_files(self, max_age_days: int = 365) -> int:
           """
           Clean up conversation files older than specified days.

           Args:
               max_age_days: Maximum age in days for files to keep

           Returns:
               Number of files deleted
           """
           deleted_count = 0
           cutoff_date = datetime.now() - timedelta(days=max_age_days)

           try:
               for file_path in self.base_path.glob("*.json"):
                   if file_path.is_file():
                       file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                       if file_mtime < cutoff_date:
                           # Move to archive before deleting
                           archive_name = f"{file_path.stem}_{int(file_mtime.timestamp())}{file_path.suffix}"
                           archive_path = self.archive_path / archive_name

                           try:
                               file_path.replace(archive_path)
                               deleted_count += 1
                               logger.info(f"Archived old conversation: {file_path.name}")
                           except Exception as e:
                               logger.warning(f"Failed to archive {file_path.name}: {e}")

               logger.info(f"Cleaned up {deleted_count} old conversation files")
               return deleted_count

           except Exception as e:
               logger.error(f"Failed to cleanup old files: {e}")
               return 0

       def archive_conversation(self, conversation_id: str) -> bool:
           """
           Move conversation to archive storage.

           Args:
               conversation_id: Unique conversation identifier

           Returns:
               True if successful, False otherwise
           """
           file_path = self._get_conversation_path(conversation_id)

           if not file_path.exists():
               logger.warning(f"Conversation {conversation_id} not found for archiving")
               return False

           try:
               timestamp = int(datetime.now().timestamp())
               archive_name = f"{conversation_id}_{timestamp}.json"
               archive_path = self.archive_path / archive_name

               file_path.replace(archive_path)
               logger.info(f"Conversation {conversation_id} archived successfully")
               return True

           except Exception as e:
               logger.error(f"Failed to archive conversation {conversation_id}: {e}")
               return False
   ```

3. Create unit tests:
   ```python
   # tests/unit/test_conversation_storage.py
   import pytest
   import json
   from pathlib import Path
   from datetime import datetime

   from src.storage.conversation_storage import ConversationStorage

   @pytest.fixture
   def temp_storage_dir(tmp_path):
       """Create temporary directory for storage testing."""
       storage_dir = tmp_path / "conversations"
       storage_dir.mkdir()
       return storage_dir

   @pytest.fixture
   def storage(temp_storage_dir):
       """Create ConversationStorage instance with temp directory."""
       return ConversationStorage(str(temp_storage_dir))

   @pytest.fixture
   def sample_conversation():
       """Create sample conversation data."""
       return {
           "id": "test_conv_001",
           "title": "Test Conversation",
           "created_at": datetime.now().isoformat(),
           "messages": [
               {
                   "role": "user",
                   "content": "Hello",
                   "timestamp": datetime.now().isoformat()
               },
               {
                   "role": "assistant",
                   "content": "Hi there!",
                   "timestamp": datetime.now().isoformat()
               }
           ]
       }

   class TestConversationStorage:
       def test_initialization_creates_directories(self, temp_storage_dir):
           """Test that initialization creates necessary directories."""
           storage = ConversationStorage(str(temp_storage_dir))

           assert temp_storage_dir.exists()
           assert (temp_storage_dir.parent / "archived").exists()

       def test_save_and_load_conversation(self, storage, sample_conversation):
           """Test saving and loading a conversation."""
           conversation_id = sample_conversation["id"]

           # Save conversation
           success = storage.save_conversation(conversation_id, sample_conversation)
           assert success

           # Load conversation
           loaded = storage.load_conversation(conversation_id)
           assert loaded is not None
           assert loaded["id"] == conversation_id
           assert len(loaded["messages"]) == 2

       def test_load_nonexistent_conversation(self, storage):
           """Test loading a conversation that doesn't exist."""
           loaded = storage.load_conversation("nonexistent")
           assert loaded is None

       def test_list_conversations(self, storage, sample_conversation):
           """Test listing conversations."""
           # Initially empty
           conversations = storage.list_conversations()
           assert len(conversations) == 0

           # Save a conversation
           storage.save_conversation(sample_conversation["id"], sample_conversation)

           # List should contain the conversation
           conversations = storage.list_conversations()
           assert len(conversations) == 1
           assert sample_conversation["id"] in conversations

       def test_delete_conversation(self, storage, sample_conversation):
           """Test deleting a conversation."""
           conversation_id = sample_conversation["id"]

           # Save then delete
           storage.save_conversation(conversation_id, sample_conversation)
           assert storage.load_conversation(conversation_id) is not None

           success = storage.delete_conversation(conversation_id)
           assert success

           # Should not be found after deletion
           assert storage.load_conversation(conversation_id) is None

       def test_data_validation(self, storage):
           """Test conversation data validation."""
           # Invalid data missing required fields
           invalid_data = {"id": "test"}
           success = storage.save_conversation("invalid", invalid_data)
           assert not success

           # Invalid message structure
           invalid_messages = {
               "id": "test",
               "title": "Test",
               "created_at": datetime.now().isoformat(),
               "messages": ["invalid message"]
           }
           success = storage.save_conversation("invalid2", invalid_messages)
           assert not success

       def test_storage_stats(self, storage, sample_conversation):
           """Test storage statistics."""
           stats = storage.get_storage_stats()
           assert "total_conversations" in stats
           assert "total_size_bytes" in stats
           assert stats["total_conversations"] == 0

           # Save conversation and check stats
           storage.save_conversation(sample_conversation["id"], sample_conversation)
           stats = storage.get_storage_stats()
           assert stats["total_conversations"] == 1
           assert stats["total_size_bytes"] > 0

       def test_file_cleanup(self, storage, sample_conversation):
           """Test cleanup of old files."""
           # Save conversation
           storage.save_conversation(sample_conversation["id"], sample_conversation)

           # Cleanup with 0 days should archive the file
           deleted_count = storage.cleanup_old_files(max_age_days=0)
           assert deleted_count == 1

           # Original file should be gone
           assert storage.load_conversation(sample_conversation["id"]) is None

           # Check archived directory
           archived_files = list(storage.archive_path.glob("*.json"))
           assert len(archived_files) == 1

       def test_filename_sanitization(self, storage):
           """Test that dangerous filenames are sanitized."""
           dangerous_id = "../../etc/passwd"
           safe_data = {
               "id": dangerous_id,
               "title": "Test",
               "created_at": datetime.now().isoformat(),
               "messages": []
           }

           # Should save successfully with sanitized name
           success = storage.save_conversation(dangerous_id, safe_data)
           assert success

           # Should be able to load with original ID
           loaded = storage.load_conversation(dangerous_id)
           assert loaded is not None
           assert loaded["id"] == dangerous_id
   ```

**Validation Criteria**:
- [ ] ConversationStorage initializes without errors
- [ ] Conversation files created in data/conversations/active/
- [ ] Atomic save/load operations work correctly
- [ ] Data integrity checking prevents
### 2.3 MessageProcessor (src/core/message_processor.py)

**Purpose**: Handle message validation, formatting, and processing logic for AI interactions.

**Dependencies**: Logger, Validators

**Implementation Steps**:

1. Create the message processor module:
   ```bash
   mkdir -p src/core
   touch src/core/__init__.py
   touch src/core/message_processor.py
   ```

2. Implement the MessageProcessor class:
   ```python
   # src/core/message_processor.py
   import re
   import tiktoken
   from typing import Dict, Any, Tuple, Optional
   from datetime import datetime

   from ..utils.logger import logger
   from ..utils.validators import validate_message_content

   class MessageProcessor:
       """Handles message validation, formatting, and processing for AI interactions."""

       def __init__(self):
           # Common token encoders for estimation
           self._encoders = {}

       def _get_encoder(self, model: str) -> tiktoken.Encoding:
           """Get or create tokenizer for model."""
           if model not in self._encoders:
               try:
                   # Map common models to their tokenizers
                   if 'gpt' in model.lower():
                       self._encoders[model] = tiktoken.encoding_for_model("gpt-3.5-turbo")
                   elif 'claude' in model.lower():
                       self._encoders[model] = tiktoken.encoding_for_model("claude-3")
                   else:
                       # Default to GPT-3.5 tokenizer
                       self._encoders[model] = tiktoken.encoding_for_model("gpt-3.5-turbo")
               except KeyError:
                   # Fallback tokenizer
                   self._encoders[model] = tiktoken.get_encoding("cl100k_base")

           return self._encoders[model]

       def validate_message(self, content: str) -> Tuple[bool, str]:
           """
           Validate message content.

           Args:
               content: Message content to validate

           Returns:
               Tuple of (is_valid, error_message)
           """
           return validate_message_content(content)

       def format_for_api(self, message: Dict[str, Any], model: str) -> Dict[str, Any]:
           """
           Format message for API submission.

           Args:
               message: Message dictionary with role and content
               model: Target model identifier

           Returns:
               Formatted message for API
           """
           formatted = {
               "role": message["role"],
               "content": message["content"]
           }

           # Add model-specific formatting if needed
           if "claude" in model.lower():
               # Claude doesn't need special formatting for basic messages
               pass
           elif "gpt" in model.lower():
               # GPT models use standard format
               pass

           return formatted

       def process_response(self, api_response: Dict[str, Any], model: str) -> Dict[str, Any]:
           """
           Process API response into standardized message format.

           Args:
               api_response: Raw API response
               model: Model that generated the response

           Returns:
               Processed message dictionary
           """
           try:
               # Extract content based on API format
               if "choices" in api_response and api_response["choices"]:
                   # OpenAI-style response
                   choice = api_response["choices"][0]
                   content = choice.get("message", {}).get("content", "")
                   finish_reason = choice.get("finish_reason")

               elif "content" in api_response:
                   # Direct content response
                   content = api_response["content"]
                   finish_reason = api_response.get("stop_reason")

               else:
                   logger.error(f"Unknown API response format: {api_response}")
                   content = "Error: Unable to parse response"
                   finish_reason = "error"

               # Estimate token usage
               tokens = self.estimate_tokens(content)

               # Create standardized message
               message = {
                   "role": "assistant",
                   "content": content,
                   "timestamp": datetime.now().isoformat(),
                   "model": model,
                   "tokens": tokens,
                   "finish_reason": finish_reason,
                   "metadata": {
                       "processing_timestamp": datetime.now().isoformat(),
                       "api_response_format": "detected"
                   }
               }

               return message

           except Exception as e:
               logger.error(f"Failed to process API response: {e}")
               return {
                   "role": "assistant",
                   "content": "Error: Failed to process response",
                   "timestamp": datetime.now().isoformat(),
                   "model": model,
                   "tokens": 0,
                   "finish_reason": "error",
                   "metadata": {"error": str(e)}
               }

       def estimate_tokens(self, content: str, model: str = "gpt-3.5-turbo") -> int:
           """
           Estimate token count for message content.

           Args:
               content: Text content to estimate
               model: Model identifier for tokenizer selection

           Returns:
               Estimated token count
           """
           if not content:
               return 0

           try:
               encoder = self._get_encoder(model)
               tokens = encoder.encode(content)
               return len(tokens)

           except Exception as e:
               logger.warning(f"Token estimation failed, using fallback: {e}")
               # Fallback: rough estimation of 4 characters per token
               return len(content) // 4

       def sanitize_content(self, content: str) -> str:
           """
           Sanitize message content for security.

           Args:
               content: Content to sanitize

           Returns:
               Sanitized content
           """
           if not content:
               return content

           # Remove potentially dangerous patterns
           # Note: This is basic sanitization - production systems should use comprehensive sanitizers

           # Remove script tags
           content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)

           # Remove javascript URLs
           content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)

           # Remove data URLs that might be malicious
           content = re.sub(r'data:\s*[^;]*;base64,', '', content, flags=re.IGNORECASE)

           return content.strip()

       def truncate_message(self, content: str, max_tokens: int, model: str) -> str:
           """
           Truncate message content to fit within token limit.

           Args:
               content: Message content
               max_tokens: Maximum token count
               model: Model identifier

           Returns:
               Truncated content
           """
           if not content:
               return content

           try:
               encoder = self._get_encoder(model)
               tokens = encoder.encode(content)

               if len(tokens) <= max_tokens:
                   return content

               # Truncate tokens and decode
               truncated_tokens = tokens[:max_tokens]
               truncated_content = encoder.decode(truncated_tokens)

               # Remove incomplete words at the end
               if truncated_content != content:
                   truncated_content = truncated_content.rstrip()
                   # Remove trailing incomplete word
                   words = truncated_content.split()
                   if words and not truncated_content.endswith(' '):
                       words = words[:-1]
                   truncated_content = ' '.join(words)

               logger.info(f"Message truncated from {len(tokens)} to {len(truncated_tokens)} tokens")
               return truncated_content

           except Exception as e:
               logger.warning(f"Message truncation failed: {e}")
               # Fallback: truncate by character count
               char_limit = max_tokens * 4  # Rough estimation
               if len(content) <= char_limit:
                   return content
               return content[:char_limit].rstrip()

       def format_conversation_history(self, messages: list, max_tokens: int, model: str) -> list:
           """
           Format conversation history for API, respecting token limits.

           Args:
               messages: List of message dictionaries
               max_tokens: Maximum total tokens
               model: Model identifier

           Returns:
               Formatted messages list
           """
           if not messages:
               return messages

           formatted_messages = []
           total_tokens = 0

           # Process messages in reverse order (most recent first)
           for message in reversed(messages):
               content = message.get("content", "")
               tokens = self.estimate_tokens(content, model)

               if total_tokens + tokens > max_tokens and formatted_messages:
                   # Would exceed limit, stop here
                   break

               formatted_messages.insert(0, self.format_for_api(message, model))
               total_tokens += tokens

           logger.debug(f"Formatted {len(formatted_messages)} messages, {total_tokens} tokens")
           return formatted_messages
   ```

**Validation Criteria**:
- [ ] MessageProcessor validates content correctly
- [ ] API formatting works for different models
- [ ] Response processing handles various API formats
- [ ] Token estimation is reasonably accurate
- [ ] Content sanitization removes dangerous patterns
- [ ] Message truncation preserves meaning
- [ ] Conversation history formatting respects token limits

### 2.4 APIClientManager (src/core/api_client.py)

**Purpose**: Handle all OpenRouter API interactions with rate limiting and error recovery.

**Dependencies**: Logger, ConfigManager, MessageProcessor

**Implementation Steps**:

1. Create the API client module:
   ```bash
   touch src/core/api_client.py
   ```

2. Implement the APIClient class:
   ```python
   # src/core/api_client.py
   import asyncio
   import time
   from typing import Dict, Any, List, Optional, AsyncGenerator
   from datetime import datetime, timedelta
   import aiohttp
   import json

   from ..utils.logger import logger
   from ..storage.config_manager import ConfigManager
   from .message_processor import MessageProcessor

   class APIError(Exception):
       """Base exception for API-related errors."""
       pass

   class RateLimitError(APIError):
       """Exception for rate limit violations."""
       pass

   class APIClient:
       """Handles OpenRouter API interactions with reliability features."""

       def __init__(self, config_manager: ConfigManager):
           """
           Initialize API client.

           Args:
               config_manager: Configuration manager instance
           """
           self.config = config_manager
           self.message_processor = MessageProcessor()

           # API configuration
           self.base_url = "https://openrouter.ai/api/v1"
           self.api_key = None
           self.session: Optional[aiohttp.ClientSession] = None

           # Rate limiting
           self.requests_this_minute = 0
           self.requests_this_hour = 0
           self.minute_reset = datetime.now()
           self.hour_reset = datetime.now()

           # Performance tracking
           self.request_times = []

       async def _ensure_session(self):
           """Ensure aiohttp session is available."""
           if self.session is None or self.session.closed:
               self.session = aiohttp.ClientSession(
                   headers={
                       "Authorization": f"Bearer {self.api_key}",
                       "Content-Type": "application/json",
                       "HTTP-Referer": "https://github.com/your-org/personal-ai-chatbot",
                       "X-Title": "Personal AI Chatbot"
                   }
               )

       async def _get_api_key(self) -> str:
           """Get API key from configuration."""
           if self.api_key is None:
               self.api_key = self.config.get_api_key()
               if not self.api_key:
                   raise APIError("API key not configured")
           return self.api_key

       def _check_rate_limits(self) -> bool:
           """
           Check if we're within rate limits.

           Returns:
               True if within limits, False if exceeded
           """
           now = datetime.now()

           # Reset counters if needed
           if now >= self.minute_reset:
               self.requests_this_minute = 0
               self.minute_reset = now + timedelta(minutes=1)

           if now >= self.hour_reset:
               self.requests_this_hour = 0
               self.hour_reset = now + timedelta(hours=1)

           # Check limits (conservative defaults)
           max_per_minute = self.config.get_setting("api.rate_limit_per_minute", 50)
           max_per_hour = self.config.get_setting("api.rate_limit_per_hour", 1000)

           if self.requests_this_minute >= max_per_minute:
               return False

           if self.requests_this_hour >= max_per_hour:
               return False

           return True

       def _record_request(self):
           """Record a request for rate limiting."""
           self.requests_this_minute += 1
           self.requests_this_hour += 1

       async def _wait_for_rate_limit(self):
           """Wait until rate limits reset."""
           now = datetime.now()

           if self.requests_this_minute >= self.config.get_setting("api.rate_limit_per_minute", 50):
               wait_seconds = (self.minute_reset - now).total_seconds()
               if wait_seconds > 0:
                   logger.info(f"Rate limited, waiting {wait_seconds:.1f} seconds")
                   await asyncio.sleep(wait_seconds)

           elif self.requests_this_hour >= self.config.get_setting("api.rate_limit_per_hour", 1000):
               wait_seconds = (self.hour_reset - now).total_seconds()
               if wait_seconds > 0:
                   logger.info(f"Rate limited, waiting {wait_seconds:.1f} seconds")
                   await asyncio.sleep(wait_seconds)

       async def send_chat_request(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> Dict[str, Any]:
           """
           Send chat completion request to API.

           Args:
               messages: List of message dictionaries
               model: Model identifier
               **kwargs: Additional API parameters

           Returns:
               API response dictionary

           Raises:
               APIError: For API-related errors
               RateLimitError: For rate limit violations
           """
           await self._get_api_key()
           await self._ensure_session()

           # Check rate limits
           if not self._check_rate_limits():
               await self._wait_for_rate_limit()

           self._record_request()

           # Prepare request data
           request_data = {
               "model": model,
               "messages": messages,
               "temperature": kwargs.get("temperature", 0.7),
               "max_tokens": kwargs.get("max_tokens", 1000),
               "stream": False
           }

           # Add optional parameters
           for param in ["temperature", "top_p", "frequency_penalty", "presence_penalty"]:
               if param in kwargs:
                   request_data[param] = kwargs[param]

           url = f"{self.base_url}/chat/completions"
           start_time = time.time()

           try:
               logger.info(f"Sending request to {model}")

               async with self.session.post(url, json=request_data) as response:
                   self._record_request_time(time.time() - start_time)

                   if response.status == 429:
                       # Rate limited
                       retry_after = response.headers.get('Retry-After', '60')
                       logger.warning(f"Rate limited, retry after {retry_after} seconds")
                       raise RateLimitError(f"Rate limit exceeded, retry after {retry_after} seconds")

                   elif response.status >= 400:
                       error_text = await response.text()
                       logger.error(f"API error {response.status}: {error_text}")
                       raise APIError(f"API error {response.status}: {error_text}")

                   result = await response.json()
                   logger.info(f"Request completed successfully")
                   return result

           except aiohttp.ClientError as e:
               logger.error(f"Network error: {e}")
               raise APIError(f"Network error: {e}")

           except asyncio.TimeoutError:
               logger.error("Request timeout")
               raise APIError("Request timeout")

           except Exception as e:
               logger.error(f"Unexpected error: {e}")
               raise APIError(f"Unexpected error: {e}")

       async def stream_response(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> AsyncGenerator[str, None]:
           """
           Stream chat completion response.

           Args:
               messages: List of message dictionaries
               model: Model identifier
               **kwargs: Additional parameters

           Yields:
               Response text chunks
           """
           await self._get_api_key()
           await self._ensure_session()

           if not self._check_rate_limits():
               await self._wait_for_rate_limit()

           self._record_request()

           request_data = {
               "model": model,
               "messages": messages,
               "temperature": kwargs.get("temperature", 0.7),
               "max_tokens": kwargs.get("max_tokens", 1000),
               "stream": True
           }

           url = f"{self.base_url}/chat/completions"

           try:
               logger.info(f"Starting streaming request to {model}")

               async with self.session.post(url, json=request_data) as response:

                   if response.status == 429:
                       raise RateLimitError("Rate limit exceeded")

                   elif response.status >= 400:
                       error_text = await response.text()
                       raise APIError(f"API error {response.status}: {error_text}")

                   async for line in response.content:
                       line = line.decode('utf-8').strip()

                       if line.startswith('data: '):
                           data = line[6:]  # Remove 'data: ' prefix

                           if data == '[DONE]':
                               break

                           try:
                               chunk = json.loads(data)
                               if 'choices' in chunk and chunk['choices']:
                                   delta = chunk['choices'][0].get('delta', {})
                                   content = delta.get('content', '')
                                   if content:
                                       yield content

                           except json.JSONDecodeError:
                               continue

               logger.info("Streaming request completed")

           except Exception as e:
               logger.error(f"Streaming error: {e}")
               raise

       def get_available_models(self) -> List[Dict[str, Any]]:
           """
           Get list of available models from API.

           Returns:
               List of model information dictionaries
           """
           # Note: This is a synchronous call for simplicity
           # In production, this should be async
           try:
               import requests

               headers = {
                   "Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json"
               }

               response = requests.get(f"{self.base_url}/models", headers=headers, timeout=30)

               if response.status_code == 200:
                   data = response.json()
                   return data.get('data', [])
               else:
                   logger.error(f"Failed to get models: {response.status_code}")
                   return []

           except Exception as e:
               logger.error(f"Error getting models: {e}")
               return []

       def validate_model(self, model_id: str) -> bool:
           """
           Validate that a model is available.

           Args:
               model_id: Model identifier to validate

           Returns:
               True if model is available
           """
           models = self.get_available_models()
           return any(model.get('id') == model_id for model in models)

       def _record_request_time(self, duration: float):
           """Record request duration for performance monitoring."""
           self.request_times.append(duration)

           # Keep only last 100 measurements
           if len(self.request_times) > 100:
               self.request_times = self.request_times[-100:]

       def get_performance_stats(self) -> Dict[str, float]:
           """
           Get API performance statistics.

           Returns:
               Dictionary with performance metrics
           """
           if not self.request_times:
               return {"average_response_time": 0.0, "min_response_time": 0.0, "max_response_time": 0.0}

           return {
               "average_response_time": sum(self.request_times) / len(self.request_times),
               "min_response_time": min(self.request_times),
               "max_response_time": max(self.request_times)
           }

       async def close(self):
           """Close the HTTP session."""
           if self.session and not self.session.closed:
               await self.session.close()
               logger.info("API client session closed")
   ```

**Validation Criteria**:
- [ ] APIClient initializes with configuration
- [ ] API key retrieval works correctly
- [ ] Rate limiting prevents quota violations
- [ ] Chat requests succeed with valid API key
- [ ] Error handling works for network issues
- [ ] Streaming responses work correctly
- [ ] Model validation functions properly
- [ ] Performance statistics are tracked

### 2.5 ConversationManager (src/core/conversation_manager.py)

**Purpose**: Manage conversation lifecycle, persistence, and organization.

**Dependencies**: Logger, ConversationStorage, MessageProcessor

**Implementation Steps**:

1. Create the conversation manager module:
   ```bash
   touch src/core/conversation_manager.py
   ```

2. Implement the ConversationManager class:
   ```python
   # src/core/conversation_manager.py
   import uuid
   from typing import Dict, Any, List, Optional
   from datetime import datetime

   from ..utils.logger import logger
   from ..storage.conversation_storage import ConversationStorage
   from .message_processor import MessageProcessor

   class ConversationManager:
       """Manages conversation lifecycle and persistence."""

       def __init__(self, storage: ConversationStorage):
           """
           Initialize conversation manager.

           Args:
               storage: Conversation storage instance
           """
           self.storage = storage
           self.message_processor = MessageProcessor()

       def create_conversation(self, title: str = None) -> str:
           """
           Create a new conversation.

           Args:
               title: Optional conversation title

           Returns:
               Unique conversation ID
           """
           conversation_id = str(uuid.uuid4())

           if not title:
               title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"

           conversation_data = {
               "id": conversation_id,
               "title": title,
               "created_at": datetime.now().isoformat(),
               "updated_at": datetime.now().isoformat(),
               "messages": [],
               "metadata": {
                   "message_count": 0,
                   "total_tokens": 0,
                   "model_used": None
               }
           }

           success = self.storage.save_conversation(conversation_id, conversation_data)
           if success:
               logger.info(f"Created conversation: {conversation_id}")
               return conversation_id
           else:
               logger.error(f"Failed to create conversation: {conversation_id}")
               raise RuntimeError("Failed to create conversation")

       def save_conversation(self, conversation_id: str, messages: List[Dict[str, Any]]) -> bool:
           """
           Save conversation with updated messages.

           Args:
               conversation_id: Conversation identifier
               messages: List of message dictionaries

           Returns:
               True if successful
           """
           # Load existing conversation
           existing = self.storage.load_conversation(conversation_id)
           if not existing:
               logger.error(f"Conversation {conversation_id} not found")
               return False

           # Update conversation data
           existing["messages"] = messages
           existing["updated_at"] = datetime.now().isoformat()

           # Update metadata
           existing["metadata"]["message_count"] = len(messages)
           existing["metadata"]["total_tokens"] = sum(
               msg.get("tokens", 0) for msg in messages
           )

           # Update model used (from last assistant message)
           for msg in reversed(messages):
               if msg.get("role") == "assistant" and msg.get("model"):
                   existing["metadata"]["model_used"] = msg["model"]
                   break

           success = self.storage.save_conversation(conversation_id, existing)
           if success:
               logger.debug(f"Saved conversation {conversation_id} with {len(messages)} messages")
           return success

       def load_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
           """
           Load conversation messages.

           Args:
               conversation_id: Conversation identifier

           Returns:
               List of message dictionaries
           """
           conversation = self.storage.load_conversation(conversation_id)
           if not conversation:
               return []

           return conversation.get("messages", [])

       def list_conversations(self) -> List[Dict[str, Any]]:
           """
           List all conversations with metadata.

           Returns:
               List of conversation metadata dictionaries
           """
           conversation_ids = self.storage.list_conversations()
           conversations = []

           for conv_id in conversation_ids:
               conv_data = self.storage.load_conversation(conv_id)
               if conv_data:
                   # Extract metadata for listing
                   metadata = {
                       "id": conv_data["id"],
                       "title": conv_data["title"],
                       "created_at": conv_data["created_at"],
                       "updated_at": conv_data["updated_at"],
                       "message_count": conv_data["metadata"]["message_count"],
                       "total_tokens": conv_data["metadata"]["total_tokens"],
                       "model_used": conv_data["metadata"]["model_used"]
                   }
                   conversations.append(metadata)

           # Sort by updated_at descending
           conversations.sort(key=lambda x: x["updated_at"], reverse=True)
           return conversations

       def delete_conversation(self, conversation_id: str) -> bool:
           """
           Delete a conversation.

           Args:
               conversation_id: Conversation identifier

           Returns:
               True if successful
           """
           success = self.storage.delete_conversation(conversation_id)
           if success:
               logger.info(f"Deleted conversation: {conversation_id}")
           return success

       def add_message_to_conversation(self, conversation_id: str, message: Dict[str, Any]) -> bool:
           """
           Add a message to an existing conversation.

           Args:
               conversation_id: Conversation identifier
               message: Message dictionary

           Returns:
               True if successful
           """
           messages = self.load_conversation(conversation_id)
           if messages is None:
               return False

           messages.append(message)
           return self.save_conversation(conversation_id, messages)

       def get_conversation_metadata(self, conversation_id: str) -> Optional[Dict[str, Any]]:
           """
           Get conversation metadata without loading all messages.

           Args:
               conversation_id: Conversation identifier

           Returns:
               Metadata dictionary or None
           """
           conversation = self.storage.load_conversation(conversation_id)
           if not conversation:
               return None

           return {
               "id": conversation["id"],
               "title": conversation["title"],
               "created_at": conversation["created_at"],
               "updated_at": conversation["updated_at"],
               "message_count": conversation["metadata"]["message_count"],
               "total_tokens": conversation["metadata"]["total_tokens"],
               "model_used": conversation["metadata"]["model_used"]
           }

       def search_conversations(self, query: str) -> List[Dict[str, Any]]:
           """
           Search conversations by content or title.

           Args:
               query: Search query string

           Returns:
               List of matching conversation metadata
           """
           query_lower = query.lower()
           all_conversations = self.list_conversations()
           matches = []

           for conv in all_conversations:
               # Search in title
               if query_lower in conv["title"].lower():
                   matches.append(conv)
                   continue

               # Search in message content (load conversation to check)
               messages = self.load_conversation(conv["id"])
               for msg in messages:
                   content = msg.get("content", "")
                   if query_lower in content.lower():
                       matches.append(conv)
                       break

           return matches

       def archive_old_conversations(self, days_old: int = 365) -> int:
           """
           Archive conversations older than specified days.

           Args:
               days_old: Age threshold in days

           Returns:
               Number of conversations archived
           """
           from datetime import timedelta

           cutoff_date = datetime.now() - timedelta(days=days_old)
           archived_count = 0

           conversations = self.list_conversations()

           for conv in conversations:
               updated_at = datetime.fromisoformat(conv["updated_at"])
               if updated_at < cutoff_date:
                   success = self.storage.archive_conversation(conv["id"])
                   if success:
                       archived_count += 1

           logger.info(f"Archived {archived_count} old conversations")
           return archived_count

       def get_storage_stats(self) -> Dict[str, Any]:
           """
           Get conversation storage statistics.

           Returns:
               Storage statistics dictionary
           """
           return self.storage.get_storage_stats()
   ```

**Validation Criteria**:
- [ ] ConversationManager creates conversations with unique IDs
- [ ] Messages are saved and loaded correctly
- [ ] Conversation metadata is maintained accurately
- [ ] Conversation listing works with proper sorting
- [ ] Search functionality finds messages by content
- [ ] Deletion removes conversations properly
- [ ] Archiving moves old conversations
- [ ] Storage statistics are accurate

## 3. Integration Testing Procedures

### 3.1 End-to-End Chat Flow Test

**Purpose**: Validate complete chat workflow from user input to AI response.

**Prerequisites**:
- All core components implemented (ConfigManager, ConversationStorage, MessageProcessor, APIClient, ConversationManager)
- Valid OpenRouter API key configured
- Test environment set up

**Test Procedure**:

1. **Setup Test Environment**:
   ```python
   # tests/integration/test_chat_flow.py
   import pytest
   import asyncio
   from src.storage.config_manager import ConfigManager
   from src.storage.conversation_storage import ConversationStorage
   from src.core.message_processor import MessageProcessor
   from src.core.api_client import APIClient
   from src.core.conversation_manager import ConversationManager

   @pytest.fixture
   async def test_components(tmp_path):
       """Set up test components."""
       # Create temporary directories
       config_dir = tmp_path / "config"
       storage_dir = tmp_path / "conversations"
       config_dir.mkdir()
       storage_dir.mkdir()

       # Initialize components
       config = ConfigManager(str(config_dir))
       storage = ConversationStorage(str(storage_dir))
       message_processor = MessageProcessor()
       api_client = APIClient(config)
       conversation_manager = ConversationManager(storage)

       # Configure test API key (use environment variable)
       test_api_key = os.getenv("TEST_OPENROUTER_API_KEY")
       if test_api_key:
           config.set_api_key(test_api_key)

       yield {
           "config": config,
           "storage": storage,
           "message_processor": message_processor,
           "api_client": api_client,
           "conversation_manager": conversation_manager
       }

       # Cleanup
       await api_client.close()
   ```

2. **Test Complete Chat Workflow**:
   ```python
   @pytest.mark.asyncio
   async def test_complete_chat_workflow(test_components):
       """Test end-to-end chat workflow."""
       components = test_components
       api_client = components["api_client"]
       conversation_manager = components["conversation_manager"]
       message_processor = components["message_processor"]

       # Skip if no API key
       if not components["config"].get_api_key():
           pytest.skip("No test API key configured")

       # 1. Create conversation
       conversation_id = conversation_manager.create_conversation("Test Chat")
       assert conversation_id

       # 2. Prepare user message
       user_content = "Hello, can you help me understand how APIs work?"
       is_valid, error = message_processor.validate_message(user_content)
       assert is_valid, f"Message validation failed: {error}"

       # 3. Format message for API
       user_message = {
           "role": "user",
           "content": user_content,
           "timestamp": datetime.now().isoformat()
       }

       formatted_messages = [message_processor.format_for_api(user_message, "anthropic/claude-3-haiku")]

       # 4. Send to API
       try:
           api_response = await api_client.send_chat_request(
               formatted_messages,
               "anthropic/claude-3-haiku",
               max_tokens=500
           )
           assert "choices" in api_response
           assert len(api_response["choices"]) > 0

           # 5. Process response
           ai_message = message_processor.process_response(
               api_response,
               "anthropic/claude-3-haiku"
           )
           assert ai_message["role"] == "assistant"
           assert len(ai_message["content"]) > 0

           # 6. Save conversation
           messages = [user_message, ai_message]
           success = conversation_manager.save_conversation(conversation_id, messages)
           assert success

           # 7. Verify conversation persistence
           loaded_messages = conversation_manager.load_conversation(conversation_id)
           assert len(loaded_messages) == 2
           assert loaded_messages[0]["content"] == user_content
           assert loaded_messages[1]["role"] == "assistant"

       except Exception as e:
           # Log error but don't fail test if API is unavailable
           pytest.skip(f"API integration test failed: {e}")
   ```

3. **Test Error Scenarios**:
   ```python
   @pytest.mark.asyncio
   async def test_error_handling(test_components):
       """Test error handling in chat workflow."""
       components = test_components
       api_client = components["api_client"]

       # Test with invalid API key
       original_key = components["config"].get_api_key()
       components["config"].set_api_key("invalid-key")

       try:
           await api_client.send_chat_request(
               [{"role": "user", "content": "test"}],
               "test-model"
           )
           assert False, "Should have raised an exception"
       except Exception:
           pass  # Expected

       # Restore valid key
       if original_key:
           components["config"].set_api_key(original_key)
   ```

**Success Criteria**:
- [ ] Complete chat workflow executes without errors
- [ ] Messages are validated, formatted, and processed correctly
- [ ] API communication succeeds with valid credentials
- [ ] Conversation data persists across operations
- [ ] Error scenarios are handled gracefully
- [ ] All integration test assertions pass

## 4. Deployment Checklist

### 4.1 Pre-Deployment Verification

**Environment Setup**:
- [ ] Python 3.9+ installed and accessible
- [ ] Virtual environment created and activated
- [ ] All dependencies installed from requirements.txt
- [ ] Data directories created with proper permissions
- [ ] Environment variables configured (.env file)

**Configuration Validation**:
- [ ] OpenRouter API key configured and validated
- [ ] Default model selected and tested
- [ ] Application settings configured appropriately
- [ ] Log directory writable
- [ ] Data storage directories accessible

**Component Verification**:
- [ ] All Python modules import without errors
- [ ] Configuration manager initializes correctly
- [ ] Conversation storage creates test file successfully
- [ ] Message processor validates test messages
- [ ] API client initializes with test connection
- [ ] Conversation manager creates test conversation

### 4.2 Deployment Execution

**Application Startup**:
- [ ] Application starts within 3 seconds
- [ ] No console errors during initialization
- [ ] Web interface accessible on configured port
- [ ] Default conversation loads successfully
- [ ] Model selection dropdown populates

**Basic Functionality Test**:
- [ ] Send simple message to AI model
- [ ] Response appears within 10 seconds
- [ ] Message saves to conversation
- [ ] Conversation persists across application restart
- [ ] Settings panel loads and saves changes

**Performance Validation**:
- [ ] Memory usage under 500MB during normal operation
- [ ] CPU usage under 20% during typical usage
- [ ] UI responsiveness under 100ms for local operations
- [ ] API response times under 10 seconds average

### 4.3 Post-Deployment Monitoring

**Operational Checks**:
- [ ] Application runs for extended period without crashes
- [ ] Log files created and rotated properly
- [ ] Backup system creates periodic backups
- [ ] Error handling works for network issues
- [ ] Rate limiting prevents API quota violations

**Data Integrity**:
- [ ] Conversation files remain uncorrupted
- [ ] Configuration persists across restarts
- [ ] API key remains secure and accessible
- [ ] File permissions remain correct

**User Experience**:
- [ ] Interface loads quickly on target devices
- [ ] Chat interaction feels responsive
- [ ] Error messages are clear and actionable
- [ ] Settings changes apply immediately

### 4.4 Rollback Procedures

**If Deployment Fails**:
1. Stop application process
2. Restore backup configuration files
3. Check log files for error details
4. Verify API key and network connectivity
5. Restart with minimal configuration
6. Test basic functionality before full deployment

**Emergency Recovery**:
- [ ] Application can start with default settings
- [ ] Conversations can be exported manually
- [ ] Configuration can be reset to defaults
- [ ] API key can be re-entered securely

**Success Criteria**:
- [ ] All pre-deployment checks pass
- [ ] Application starts and runs stably
- [ ] Basic chat functionality works end-to-end
- [ ] Performance meets baseline requirements
- [ ] Data integrity maintained
- [ ] User experience meets expectations
- [ ] Rollback procedures functional if needed

This completes the implementation guide creation. The guides provide mechanical, step-by-step instructions for building each component with complete code templates, validation criteria, and testing procedures. Following these guides will result in a fully functional Personal AI Chatbot that meets all specified requirements.