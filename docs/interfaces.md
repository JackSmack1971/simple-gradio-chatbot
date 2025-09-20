# Interface Specifications - Personal AI Chatbot

## Overview

This document provides complete interface specifications for all components in the Personal AI Chatbot system. Each interface includes method signatures, data contracts, interaction protocols, and error handling specifications.

## 1. Core Component Interfaces

### 1.1 ChatController Interface

**Purpose**: Orchestrates chat interactions and coordinates between UI and backend components

**Interface Definition**:
```python
class ChatController:
    """Main controller for chat functionality"""

    def __init__(self,
                 message_processor: MessageProcessor,
                 conversation_manager: ConversationManager,
                 api_client: APIClient,
                 config_manager: ConfigManager):
        """Initialize with required dependencies"""

    async def send_message(self, user_input: str, model_id: str) -> Message:
        """Process user message and return AI response

        Args:
            user_input: Raw user message text
            model_id: AI model identifier to use

        Returns:
            Message: AI response message object

        Raises:
            ValidationError: If input validation fails
            APIError: If API call fails
            ConversationError: If conversation state is invalid
        """

    def cancel_generation(self) -> bool:
        """Cancel ongoing message generation

        Returns:
            bool: True if cancellation successful, False otherwise
        """

    def get_conversation_state(self) -> ConversationState:
        """Get current conversation state

        Returns:
            ConversationState: Current state object
        """

    def update_model(self, model_id: str) -> bool:
        """Update active model for current conversation

        Args:
            model_id: New model identifier

        Returns:
            bool: True if update successful

        Raises:
            ModelError: If model is invalid or unavailable
        """

    def create_new_conversation(self, title: str = None) -> str:
        """Create new conversation and switch to it

        Args:
            title: Optional conversation title

        Returns:
            str: New conversation ID
        """

    def load_conversation(self, conversation_id: str) -> bool:
        """Load existing conversation

        Args:
            conversation_id: Conversation to load

        Returns:
            bool: True if load successful

        Raises:
            ConversationNotFoundError: If conversation doesn't exist
        """
```

**Data Contracts**:
```python
@dataclass
class ConversationState:
    """Current conversation state"""
    current_conversation_id: str
    active_model: str
    message_count: int
    is_generating: bool
    last_activity: datetime
    settings: Dict[str, Any]
```

### 1.2 MessageProcessor Interface

**Purpose**: Handles message validation, formatting, and processing logic

**Interface Definition**:
```python
class MessageProcessor:
    """Handles message processing and validation"""

    def validate_message(self, content: str) -> ValidationResult:
        """Validate message content and format

        Args:
            content: Message content to validate

        Returns:
            ValidationResult: Validation results with errors if any
        """

    def format_for_api(self, message: Message) -> Dict[str, Any]:
        """Format message for API submission

        Args:
            message: Message object to format

        Returns:
            Dict[str, Any]: API-formatted message data
        """

    def process_response(self, api_response: Dict[str, Any]) -> Message:
        """Process API response into Message object

        Args:
            api_response: Raw API response data

        Returns:
            Message: Processed message object

        Raises:
            ProcessingError: If response processing fails
        """

    def estimate_tokens(self, content: str) -> int:
        """Estimate token count for message content

        Args:
            content: Message content

        Returns:
            int: Estimated token count
        """

    def sanitize_content(self, content: str) -> str:
        """Sanitize message content for security

        Args:
            content: Raw content

        Returns:
            str: Sanitized content
        """
```

**Data Contracts**:
```python
@dataclass
class ValidationResult:
    """Message validation results"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_content: Optional[str] = None
```

### 1.3 ConversationManager Interface

**Purpose**: Manages conversation lifecycle and persistence

**Interface Definition**:
```python
class ConversationManager:
    """Manages conversation persistence and lifecycle"""

    def __init__(self, storage: ConversationStorage):
        """Initialize with storage backend"""

    def create_conversation(self, title: str = None) -> str:
        """Create new conversation

        Args:
            title: Optional conversation title

        Returns:
            str: New conversation ID
        """

    def save_conversation(self, conversation_id: str, messages: List[Message]) -> bool:
        """Save conversation to storage

        Args:
            conversation_id: Conversation identifier
            messages: List of messages to save

        Returns:
            bool: True if save successful

        Raises:
            StorageError: If save operation fails
        """

    def load_conversation(self, conversation_id: str) -> List[Message]:
        """Load conversation from storage

        Args:
            conversation_id: Conversation identifier

        Returns:
            List[Message]: Loaded messages

        Raises:
            ConversationNotFoundError: If conversation doesn't exist
        """

    def list_conversations(self) -> List[ConversationMetadata]:
        """List all conversations with metadata

        Returns:
            List[ConversationMetadata]: Conversation summaries
        """

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation from storage

        Args:
            conversation_id: Conversation to delete

        Returns:
            bool: True if deletion successful

        Raises:
            ConversationNotFoundError: If conversation doesn't exist
        """

    def archive_old_conversations(self, max_age_days: int) -> int:
        """Archive conversations older than specified age

        Args:
            max_age_days: Maximum age in days

        Returns:
            int: Number of conversations archived
        """
```

**Data Contracts**:
```python
@dataclass
class ConversationMetadata:
    """Conversation metadata for listing"""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    model_used: str
    total_tokens: int
    tags: List[str]
    size_bytes: int
```

### 1.4 APIClient Interface

**Purpose**: Handles all interactions with the OpenRouter API

**Interface Definition**:
```python
class APIClient:
    """OpenRouter API client interface"""

    def __init__(self, config_manager: ConfigManager):
        """Initialize with configuration"""

    async def send_chat_request(self,
                               messages: List[Dict[str, Any]],
                               model: str,
                               **kwargs) -> Dict[str, Any]:
        """Send chat completion request

        Args:
            messages: Formatted message list
            model: Model identifier
            **kwargs: Additional API parameters

        Returns:
            Dict[str, Any]: API response data

        Raises:
            APIError: If API call fails
            RateLimitError: If rate limit exceeded
            AuthenticationError: If authentication fails
        """

    def get_available_models(self) -> List[ModelInfo]:
        """Retrieve available models from API

        Returns:
            List[ModelInfo]: Available models list

        Raises:
            APIError: If model retrieval fails
        """

    def validate_model(self, model_id: str) -> bool:
        """Validate model availability

        Args:
            model_id: Model identifier to validate

        Returns:
            bool: True if model is available
        """

    def get_rate_limit_status(self) -> RateLimitInfo:
        """Get current rate limiting status

        Returns:
            RateLimitInfo: Rate limit information
        """

    async def stream_response(self,
                             messages: List[Dict[str, Any]],
                             model: str,
                             **kwargs) -> AsyncGenerator[str, None]:
        """Stream response from API

        Args:
            messages: Formatted message list
            model: Model identifier
            **kwargs: Additional parameters

        Yields:
            str: Response content chunks

        Raises:
            APIError: If streaming fails
        """
```

**Data Contracts**:
```python
@dataclass
class ModelInfo:
    """AI model information"""
    id: str
    name: str
    provider: str
    context_length: int
    pricing: Dict[str, float]
    capabilities: List[str]
    is_available: bool = True

@dataclass
class RateLimitInfo:
    """Rate limiting status"""
    requests_remaining: int
    reset_time: datetime
    limit_per_minute: int
    limit_per_hour: int
    current_usage_percent: float
```

## 2. Data Persistence Interfaces

### 2.1 ConversationStorage Interface

**Purpose**: Abstract storage operations for conversations

**Interface Definition**:
```python
class ConversationStorage:
    """Abstract conversation storage interface"""

    def save_conversation(self, conversation_id: str, data: Dict[str, Any]) -> bool:
        """Save conversation data atomically

        Args:
            conversation_id: Unique conversation identifier
            data: Conversation data to save

        Returns:
            bool: True if save successful

        Raises:
            StorageError: If save operation fails
        """

    def load_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Load conversation data

        Args:
            conversation_id: Conversation identifier

        Returns:
            Dict[str, Any]: Conversation data

        Raises:
            ConversationNotFoundError: If conversation doesn't exist
        """

    def list_conversations(self) -> List[str]:
        """List all conversation IDs

        Returns:
            List[str]: Conversation ID list
        """

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation

        Args:
            conversation_id: Conversation to delete

        Returns:
            bool: True if deletion successful
        """

    def get_storage_stats(self) -> StorageStats:
        """Get storage usage statistics

        Returns:
            StorageStats: Storage statistics
        """

    def cleanup_old_files(self, max_age_days: int) -> int:
        """Clean up old conversation files

        Args:
            max_age_days: Maximum age in days

        Returns:
            int: Number of files cleaned up
        """
```

**Data Contracts**:
```python
@dataclass
class StorageStats:
    """Storage usage statistics"""
    total_conversations: int
    total_size_bytes: int
    average_size_bytes: int
    oldest_file_age_days: int
    corrupted_files: int
    free_space_bytes: int
```

### 2.2 ConfigManager Interface

**Purpose**: Manages application configuration and sensitive data

**Interface Definition**:
```python
class ConfigManager:
    """Configuration management interface"""

    def get_api_key(self) -> str:
        """Retrieve decrypted API key

        Returns:
            str: Decrypted API key

        Raises:
            ConfigError: If API key not found or decryption fails
        """

    def set_api_key(self, api_key: str) -> bool:
        """Store encrypted API key

        Args:
            api_key: API key to store

        Returns:
            bool: True if storage successful

        Raises:
            ConfigError: If storage fails
        """

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get configuration setting

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Any: Setting value
        """

    def set_setting(self, key: str, value: Any) -> None:
        """Set configuration setting

        Args:
            key: Setting key
            value: Setting value
        """

    def validate_config(self) -> List[str]:
        """Validate configuration completeness

        Returns:
            List[str]: List of validation errors
        """

    def export_config(self) -> Dict[str, Any]:
        """Export configuration for backup

        Returns:
            Dict[str, Any]: Configuration data
        """

    def import_config(self, config: Dict[str, Any]) -> bool:
        """Import configuration from backup

        Args:
            config: Configuration data to import

        Returns:
            bool: True if import successful
        """
```

## 3. User Interface Interfaces

### 3.1 GradioInterface Interface

**Purpose**: Main web interface abstraction

**Interface Definition**:
```python
class GradioInterface:
    """Gradio web interface abstraction"""

    def __init__(self, chat_controller: ChatController):
        """Initialize with chat controller"""

    def render_chat_panel(self) -> gr.Blocks:
        """Create main chat interface layout

        Returns:
            gr.Blocks: Gradio interface blocks
        """

    def update_conversation_display(self, messages: List[Message]) -> None:
        """Update chat display with new messages

        Args:
            messages: Messages to display
        """

    def show_error(self, error_msg: str, recovery_options: List[str]) -> None:
        """Display error with recovery options

        Args:
            error_msg: Error message to display
            recovery_options: List of recovery actions
        """

    def get_user_input(self) -> str:
        """Retrieve current user input

        Returns:
            str: Current input text
        """

    def clear_input_field(self) -> None:
        """Clear message input field"""

    def update_model_selector(self, models: List[ModelInfo]) -> None:
        """Update available model options

        Args:
            models: Available models list
        """

    def show_loading_indicator(self, show: bool) -> None:
        """Show/hide loading indicator

        Args:
            show: Whether to show loading indicator
        """
```

### 3.2 SettingsPanel Interface

**Purpose**: Configuration interface abstraction

**Interface Definition**:
```python
class SettingsPanel:
    """Settings configuration interface"""

    def __init__(self, config_manager: ConfigManager):
        """Initialize with config manager"""

    def load_settings(self) -> Dict[str, Any]:
        """Load current settings from storage

        Returns:
            Dict[str, Any]: Current settings
        """

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to storage

        Args:
            settings: Settings to save

        Returns:
            bool: True if save successful

        Raises:
            ValidationError: If settings validation fails
        """

    def validate_api_key(self, api_key: str) -> ValidationResult:
        """Validate API key format and functionality

        Args:
            api_key: API key to validate

        Returns:
            ValidationResult: Validation results
        """

    def test_model_connection(self, model_id: str) -> ValidationResult:
        """Test model availability and connection

        Args:
            model_id: Model to test

        Returns:
            ValidationResult: Test results
        """

    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models

        Returns:
            List[ModelInfo]: Available models
        """
```

## 4. Error Handling Interfaces

### 4.1 ErrorHandler Interface

**Purpose**: Centralized error handling and recovery

**Interface Definition**:
```python
class ErrorHandler:
    """Centralized error handling interface"""

    def handle_error(self, error: Exception, context: Dict[str, Any]) -> RecoveryResult:
        """Handle error with appropriate recovery strategy

        Args:
            error: Exception that occurred
            context: Error context information

        Returns:
            RecoveryResult: Recovery action result
        """

    def classify_error(self, error: Exception) -> ErrorType:
        """Classify error by type and severity

        Args:
            error: Exception to classify

        Returns:
            ErrorType: Classified error type
        """

    def select_recovery_strategy(self, error_type: ErrorType, context: Dict[str, Any]) -> RecoveryStrategy:
        """Select appropriate recovery strategy

        Args:
            error_type: Classified error type
            context: Error context

        Returns:
            RecoveryStrategy: Selected recovery strategy
        """

    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with context

        Args:
            error: Exception to log
            context: Error context
        """
```

**Data Contracts**:
```python
class ErrorType(Enum):
    """Error classification types"""
    NETWORK = "network"
    API = "api"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    STORAGE = "storage"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"

@dataclass
class RecoveryResult:
    """Error recovery result"""
    action: RecoveryAction
    success: bool
    message: str
    retry_data: Optional[Dict[str, Any]] = None

class RecoveryAction(Enum):
    """Recovery action types"""
    RETRY = "retry"
    RETRY_CORRECTED = "retry_corrected"
    USER_INTERVENTION = "user_intervention"
    FAIL = "fail"
    ALTERNATIVE_MODEL = "alternative_model"
```

## 5. Component Interaction Protocols

### 5.1 Event-Driven Communication

**UI to Logic Layer Communication**:
```python
# Event protocol for UI interactions
@dataclass
class UIEvent:
    """UI event structure"""
    event_type: UIEventType
    data: Dict[str, Any]
    timestamp: datetime
    source: str

class UIEventType(Enum):
    """UI event types"""
    MESSAGE_SEND = "message_send"
    MODEL_CHANGE = "model_change"
    CONVERSATION_LOAD = "conversation_load"
    SETTINGS_UPDATE = "settings_update"
    GENERATION_CANCEL = "generation_cancel"
```

**Logic to UI Layer Communication**:
```python
# State update protocol
@dataclass
class StateUpdate:
    """State update structure"""
    update_type: StateUpdateType
    data: Dict[str, Any]
    timestamp: datetime

class StateUpdateType(Enum):
    """State update types"""
    MESSAGES_UPDATED = "messages_updated"
    MODEL_CHANGED = "model_changed"
    CONVERSATION_LOADED = "conversation_loaded"
    ERROR_OCCURRED = "error_occurred"
    GENERATION_STARTED = "generation_started"
    GENERATION_COMPLETED = "generation_completed"
```

### 5.2 Asynchronous Communication Patterns

**Request-Response Pattern**:
```python
async def request_response_pattern():
    """Standard async request-response flow"""
    try:
        # Send request
        request_id = generate_request_id()
        request = Request(request_id, data)

        # Queue request
        await request_queue.put(request)

        # Wait for response with timeout
        response = await response_queue.get(timeout=30.0)

        if response.request_id != request_id:
            raise ProtocolError("Response ID mismatch")

        return response.data

    except asyncio.TimeoutError:
        raise TimeoutError("Request timed out")
    except Exception as e:
        logger.error(f"Request failed: {e}")
        raise
```

**Streaming Pattern**:
```python
async def streaming_pattern():
    """Streaming data pattern for real-time updates"""
    async with stream_connection() as stream:
        async for chunk in stream:
            # Process chunk
            processed_data = process_chunk(chunk)

            # Update subscribers
            await notify_subscribers(processed_data)

            # Check for completion
            if is_complete(chunk):
                break

        # Final processing
        final_result = finalize_stream()
        return final_result
```

## 6. Data Flow Contracts

### 6.1 Message Processing Pipeline

```python
# Message processing contract
@dataclass
class ProcessingPipeline:
    """Message processing pipeline contract"""

    def __init__(self, stages: List[ProcessingStage]):
        self.stages = stages

    async def process(self, input_data: Any) -> Any:
        """Process data through pipeline stages"""
        current_data = input_data

        for stage in self.stages:
            try:
                current_data = await stage.process(current_data)
            except Exception as e:
                logger.error(f"Pipeline stage failed: {stage.name}")
                raise PipelineError(f"Stage {stage.name} failed: {e}")

        return current_data
```

### 6.2 State Synchronization Contract

```python
# State synchronization contract
@dataclass
class StateSyncContract:
    """State synchronization between components"""

    def __init__(self, state_store: StateStore):
        self.state_store = state_store

    async def update_state(self, key: str, value: Any, source: str) -> bool:
        """Update state with conflict resolution"""
        try:
            # Check for conflicts
            current_value = await self.state_store.get(key)

            if self._has_conflict(current_value, value):
                # Resolve conflict
                resolved_value = await self._resolve_conflict(key, current_value, value, source)
                value = resolved_value

            # Update state
            await self.state_store.set(key, value, source)

            # Notify subscribers
            await self._notify_state_change(key, value, source)

            return True

        except Exception as e:
            logger.error(f"State update failed: {e}")
            return False

    def _has_conflict(self, current: Any, new: Any) -> bool:
        """Check for state conflicts"""
        # Implement conflict detection logic
        return False  # Placeholder

    async def _resolve_conflict(self, key: str, current: Any, new: Any, source: str) -> Any:
        """Resolve state conflicts"""
        # Implement conflict resolution logic
        return new  # Placeholder
```

## 7. Exception Handling Contracts

### 7.1 Custom Exception Hierarchy

```python
class ChatbotException(Exception):
    """Base exception for chatbot system"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code or self.__class__.__name__
        self.timestamp = datetime.now()

class ValidationError(ChatbotException):
    """Input validation errors"""
    pass

class APIError(ChatbotException):
    """API-related errors"""
    def __init__(self, message: str, status_code: int = None, retry_after: int = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after

class StorageError(ChatbotException):
    """Data storage errors"""
    pass

class ConfigurationError(ChatbotException):
    """Configuration-related errors"""
    pass

class NetworkError(ChatbotException):
    """Network connectivity errors"""
    pass
```

### 7.2 Error Recovery Contracts

```python
class RecoveryStrategy(ABC):
    """Abstract recovery strategy"""

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> RecoveryResult:
        """Execute recovery strategy"""
        pass

class RetryRecovery(RecoveryStrategy):
    """Retry-based recovery"""

    def __init__(self, max_attempts: int = 3, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor

    async def execute(self, context: Dict[str, Any]) -> RecoveryResult:
        attempt = context.get('attempt', 1)

        if attempt >= self.max_attempts:
            return RecoveryResult(RecoveryAction.FAIL, False, "Max retries exceeded")

        # Calculate backoff delay
        delay = self.backoff_factor ** attempt

        # Schedule retry
        await asyncio.sleep(delay)

        return RecoveryResult(RecoveryAction.RETRY, True, f"Retrying in {delay}s")
```

This interface specification provides the complete contract for component interactions, ensuring reliable and maintainable communication between all system components.