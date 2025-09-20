# Integration Testing Procedures - Personal AI Chatbot

## Overview

This document defines comprehensive integration testing procedures for validating component interactions, end-to-end workflows, and system reliability. Integration tests ensure that all components work together correctly and handle real-world scenarios.

## Testing Strategy

### Test Pyramid for Integration

```
End-to-End Tests (Critical User Journeys)
    ├── Component Integration Tests (API Boundaries)
        ├── Data Flow Tests (Persistence Layer)
            └── Unit Integration Tests (Component Pairs)
```

### Test Environment Requirements

- **Test Database**: Isolated conversation storage for testing
- **Mock API**: Simulated OpenRouter API responses for reliable testing
- **Test Data**: Predefined conversations and message sets
- **Performance Monitoring**: Response time and resource usage tracking

## 1. Component Integration Tests

### 1.1 Data Layer Integration

**Purpose**: Validate data persistence and retrieval across components.

**Test Setup**:
```python
# tests/integration/test_data_integration.py
import pytest
import tempfile
from pathlib import Path
from src.storage.config_manager import ConfigManager
from src.storage.conversation_storage import ConversationStorage
from src.core.conversation_manager import ConversationManager

@pytest.fixture
def test_data_env(tmp_path):
    """Create isolated test environment."""
    config_dir = tmp_path / "config"
    storage_dir = tmp_path / "conversations"
    config_dir.mkdir()
    storage_dir.mkdir()

    config = ConfigManager(str(config_dir))
    storage = ConversationStorage(str(storage_dir))
    manager = ConversationManager(storage)

    return {
        "config": config,
        "storage": storage,
        "manager": manager
    }
```

**Test Cases**:

1. **Configuration Persistence Integration**:
   ```python
   def test_config_persistence_integration(test_data_env):
       """Test that configuration changes persist across component interactions."""
       config = test_data_env["config"]
       manager = test_data_env["manager"]

       # Set configuration
       config.set_setting("test.integration_value", "test_data")
       api_key = "sk-or-v1-test1234567890abcdef"
       config.set_api_key(api_key)

       # Create conversation using config-dependent manager
       conv_id = manager.create_conversation("Integration Test")

       # Verify configuration affects behavior
       assert conv_id is not None
       assert config.get_setting("test.integration_value") == "test_data"
       assert config.get_api_key() == api_key
   ```

2. **Conversation Data Flow Integration**:
   ```python
   def test_conversation_data_flow(test_data_env):
       """Test complete data flow from creation to persistence."""
       manager = test_data_env["manager"]

       # Create conversation
       conv_id = manager.create_conversation("Data Flow Test")

       # Add messages
       messages = [
           {"role": "user", "content": "Hello", "timestamp": "2024-01-01T10:00:00"},
           {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T10:00:01"}
       ]

       # Save through manager
       success = manager.save_conversation(conv_id, messages)
       assert success

       # Load through manager
       loaded = manager.load_conversation(conv_id)
       assert len(loaded) == 2
       assert loaded[0]["content"] == "Hello"
       assert loaded[1]["content"] == "Hi there!"

       # Verify through storage layer
       storage_data = test_data_env["storage"].load_conversation(conv_id)
       assert storage_data["id"] == conv_id
       assert len(storage_data["messages"]) == 2
   ```

### 1.2 API Integration Tests

**Purpose**: Validate API client integration with message processing and conversation management.

**Test Setup**:
```python
# tests/integration/test_api_integration.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.core.api_client import APIClient
from src.core.message_processor import MessageProcessor
from src.storage.config_manager import ConfigManager

@pytest.fixture
def mock_api_client(test_data_env):
    """Create API client with mocked HTTP responses."""
    config = test_data_env["config"]

    # Set test API key
    config.set_api_key("sk-or-v1-test1234567890abcdef")

    client = APIClient(config)

    # Mock the session and responses
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {"content": "Test response"},
            "finish_reason": "stop"
        }]
    }

    mock_session.post.return_value.__aenter__.return_value = mock_response
    client.session = mock_session

    return client
```

**Test Cases**:

1. **API Request Flow Integration**:
   ```python
   @pytest.mark.asyncio
   async def test_api_request_flow_integration(mock_api_client):
       """Test complete API request flow with message processing."""
       processor = MessageProcessor()

       # Prepare test message
       messages = [{"role": "user", "content": "Test message"}]

       # Send through API client
       response = await mock_api_client.send_chat_request(
           messages, "test-model", max_tokens=100
       )

       # Process response
       processed = processor.process_response(response, "test-model")

       # Verify integration
       assert processed["role"] == "assistant"
       assert processed["content"] == "Test response"
       assert "tokens" in processed
       assert processed["model"] == "test-model"
   ```

2. **Error Handling Integration**:
   ```python
   @pytest.mark.asyncio
   async def test_api_error_handling_integration(mock_api_client):
       """Test error handling across API and processing layers."""
       # Configure mock to return error
       mock_response = AsyncMock()
       mock_response.status = 429
       mock_response.headers = {"Retry-After": "60"}
       mock_api_client.session.post.return_value.__aenter__.return_value = mock_response

       # Attempt request
       with pytest.raises(RateLimitError):
           await mock_api_client.send_chat_request(
               [{"role": "user", "content": "test"}], "test-model"
           )
   ```

## 2. End-to-End Workflow Tests

### 2.1 Complete Chat Journey

**Purpose**: Test the full user journey from application start to conversation completion.

**Test Setup**:
```python
# tests/integration/test_e2e_chat_journey.py
import pytest
import asyncio
from pathlib import Path
from src.storage.config_manager import ConfigManager
from src.storage.conversation_storage import ConversationStorage
from src.core.message_processor import MessageProcessor
from src.core.api_client import APIClient
from src.core.conversation_manager import ConversationManager
from src.core.chat_controller import ChatController

@pytest.fixture
async def full_system_setup(tmp_path):
    """Set up complete system for end-to-end testing."""
    # Create directories
    config_dir = tmp_path / "config"
    storage_dir = tmp_path / "conversations"
    config_dir.mkdir()
    storage_dir.mkdir()

    # Initialize all components
    config = ConfigManager(str(config_dir))
    storage = ConversationStorage(str(storage_dir))
    processor = MessageProcessor()
    api_client = APIClient(config)
    conv_manager = ConversationManager(storage)
    chat_controller = ChatController(processor, conv_manager, api_client)

    # Configure test settings
    config.set_setting("api.timeout", 30)
    config.set_setting("api.max_retries", 1)

    yield {
        "config": config,
        "storage": storage,
        "processor": processor,
        "api_client": api_client,
        "conv_manager": conv_manager,
        "chat_controller": chat_controller
    }

    # Cleanup
    await api_client.close()
```

**Test Cases**:

1. **First-Time User Journey**:
   ```python
   @pytest.mark.asyncio
   async def test_first_time_user_journey(full_system_setup):
       """Test complete first-time user experience."""
       components = full_system_setup
       controller = components["chat_controller"]
       conv_manager = components["conv_manager"]

       # Simulate first interaction
       user_message = "Hello, I'm new to this AI assistant."

       # Mock API response
       mock_response = {
           "choices": [{
               "message": {"content": "Welcome! I'm here to help you."},
               "finish_reason": "stop"
           }]
       }

       # Mock the API call
       with patch.object(components["api_client"], 'send_chat_request',
                        return_value=mock_response):
           # Send message through controller
           response = await controller.send_message(user_message, "test-model")

           # Verify response
           assert response.role == "assistant"
           assert "Welcome" in response.content
           assert response.model == "test-model"

           # Verify conversation was created and saved
           conversations = conv_manager.list_conversations()
           assert len(conversations) == 1

           conv_id = conversations[0]["id"]
           messages = conv_manager.load_conversation(conv_id)
           assert len(messages) == 2  # User + Assistant
           assert messages[0]["content"] == user_message
           assert messages[1]["content"] == "Welcome! I'm here to help you."
   ```

2. **Conversation Continuation Journey**:
   ```python
   @pytest.mark.asyncio
   async def test_conversation_continuation(full_system_setup):
       """Test continuing an existing conversation."""
       components = full_system_setup
       controller = components["chat_controller"]
       conv_manager = components["conv_manager"]

       # Create initial conversation
       conv_id = conv_manager.create_conversation("Continuation Test")

       # Add initial message
       initial_messages = [
           {"role": "user", "content": "What's the weather like?", "timestamp": "2024-01-01T10:00:00"},
           {"role": "assistant", "content": "I don't have access to weather data.", "timestamp": "2024-01-01T10:00:01"}
       ]
       conv_manager.save_conversation(conv_id, initial_messages)

       # Set active conversation
       controller.set_active_conversation(conv_id)

       # Continue conversation
       follow_up = "Can you help me with coding instead?"

       mock_response = {
           "choices": [{
               "message": {"content": "I'd be happy to help with coding!"},
               "finish_reason": "stop"
           }]
       }

       with patch.object(components["api_client"], 'send_chat_request',
                        return_value=mock_response):
           response = await controller.send_message(follow_up, "test-model")

           # Verify context was maintained
           assert response.role == "assistant"
           assert "coding" in response.content

           # Verify conversation now has 4 messages
           updated_messages = conv_manager.load_conversation(conv_id)
           assert len(updated_messages) == 4
           assert updated_messages[-1]["content"] == "I'd be happy to help with coding!"
   ```

### 2.2 Error Recovery Tests

**Purpose**: Validate system behavior during various error conditions.

**Test Cases**:

1. **Network Failure Recovery**:
   ```python
   @pytest.mark.asyncio
   async def test_network_failure_recovery(full_system_setup):
       """Test recovery from network connectivity issues."""
       components = full_system_setup
       controller = components["chat_controller"]

       # Simulate network failure
       with patch.object(components["api_client"], 'send_chat_request',
                        side_effect=asyncio.TimeoutError("Connection timeout")):

           # Attempt message send
           with pytest.raises(APIError):
               await controller.send_message("Test message", "test-model")

           # Verify system remains stable
           conversations = components["conv_manager"].list_conversations()
           # Should not crash the system
           assert isinstance(conversations, list)
   ```

2. **API Rate Limit Handling**:
   ```python
   @pytest.mark.asyncio
   async def test_rate_limit_handling(full_system_setup):
       """Test handling of API rate limits."""
       components = full_system_setup
       api_client = components["api_client"]

       # Simulate rate limit
       from src.core.api_client import RateLimitError
       with patch.object(api_client, 'send_chat_request',
                        side_effect=RateLimitError("Rate limit exceeded")):

           with pytest.raises(RateLimitError):
               await api_client.send_chat_request(
                   [{"role": "user", "content": "test"}], "test-model"
               )

           # Verify rate limiting state
           assert api_client.requests_this_minute >= 1
   ```

## 3. Performance and Load Testing

### 3.1 Concurrent Operations Test

**Purpose**: Validate system performance under concurrent load.

**Test Setup**:
```python
# tests/integration/test_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from src.core.api_client import APIClient
from src.storage.config_manager import ConfigManager

@pytest.mark.asyncio
async def test_concurrent_api_requests(full_system_setup):
    """Test handling of concurrent API requests."""
    components = full_system_setup
    api_client = components["api_client"]

    # Mock fast responses
    mock_response = {
        "choices": [{"message": {"content": "Concurrent response"}}]
    }

    with patch.object(api_client, 'send_chat_request',
                     return_value=mock_response) as mock_call:

        # Send 5 concurrent requests
        tasks = []
        for i in range(5):
            task = api_client.send_chat_request(
                [{"role": "user", "content": f"Request {i}"}],
                "test-model"
            )
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify all requests completed
        assert len(results) == 5
        assert all("choices" in r for r in results)

        # Verify reasonable completion time (< 1 second for mocked calls)
        assert (end_time - start_time) < 1.0

        # Verify rate limiting worked
        assert api_client.requests_this_minute == 5
```

### 3.2 Memory Usage Test

**Purpose**: Validate memory usage under sustained load.

**Test Cases**:

1. **Conversation Scaling Test**:
   ```python
   def test_memory_usage_with_large_conversations(full_system_setup):
       """Test memory usage with large conversation datasets."""
       import psutil
       import os

       components = full_system_setup
       conv_manager = components["conv_manager"]

       process = psutil.Process(os.getpid())
       initial_memory = process.memory_info().rss

       # Create many conversations with many messages
       for i in range(10):
           conv_id = conv_manager.create_conversation(f"Scale Test {i}")
           messages = []
           for j in range(50):  # 50 messages per conversation
               messages.append({
                   "role": "user" if j % 2 == 0 else "assistant",
                   "content": f"Message {j} in conversation {i}",
                   "timestamp": f"2024-01-01T10:{j:02d}:00"
               })

           conv_manager.save_conversation(conv_id, messages)

       final_memory = process.memory_info().rss
       memory_increase = final_memory - initial_memory

       # Should not exceed reasonable memory usage (under 100MB increase)
       assert memory_increase < 100 * 1024 * 1024
   ```

## 4. Data Integrity Tests

### 4.1 Backup and Recovery

**Purpose**: Validate backup creation and data recovery capabilities.

**Test Cases**:

1. **Backup Creation Test**:
   ```python
   def test_backup_creation_and_recovery(full_system_setup):
       """Test backup creation and data recovery."""
       components = full_system_setup
       storage = components["storage"]
       conv_manager = components["conv_manager"]

       # Create test data
       conv_id = conv_manager.create_conversation("Backup Test")
       messages = [
           {"role": "user", "content": "Test message", "timestamp": "2024-01-01T10:00:00"}
       ]
       conv_manager.save_conversation(conv_id, messages)

       # Create backup
       backup_id = storage.create_backup()
       assert backup_id

       # Verify backup contains data
       backup_data = storage.load_backup(backup_id)
       assert conv_id in backup_data

       # Simulate data loss
       storage.delete_conversation(conv_id)
       assert storage.load_conversation(conv_id) is None

       # Restore from backup
       success = storage.restore_backup(backup_id)
       assert success

       # Verify data recovery
       recovered_messages = conv_manager.load_conversation(conv_id)
       assert len(recovered_messages) == 1
       assert recovered_messages[0]["content"] == "Test message"
   ```

## 5. Cross-Platform Compatibility Tests

### 5.1 File System Operations

**Purpose**: Validate file operations work across different operating systems.

**Test Cases**:

1. **Path Handling Test**:
   ```python
   def test_cross_platform_path_handling(full_system_setup):
       """Test file operations work with different path formats."""
       components = full_system_setup
       storage = components["storage"]

       # Test with various conversation IDs that could cause path issues
       test_ids = [
           "normal_id",
           "id-with-dashes",
           "id_with_underscores",
           "id with spaces",
           "id/with/slashes",  # Should be sanitized
           "../../escape_attempt"  # Should be sanitized
       ]

       for test_id in test_ids:
           # Should not raise exceptions
           success = storage.save_conversation(test_id, {
               "id": test_id,
               "title": "Path Test",
               "created_at": "2024-01-01T00:00:00",
               "messages": [],
               "metadata": {"message_count": 0, "total_tokens": 0}
           })
           assert success

           # Should be able to load
           data = storage.load_conversation(test_id)
           assert data is not None
           assert data["id"] == test_id
   ```

## Test Execution and Reporting

### Automated Test Execution

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[test]
      - name: Run integration tests
        run: pytest tests/integration/ -v --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Test Result Analysis

**Success Criteria**:
- [ ] All integration tests pass without errors
- [ ] API integration works with mock and real endpoints
- [ ] Data flows correctly between all components
- [ ] Error conditions are handled gracefully
- [ ] Performance remains within acceptable limits
- [ ] Memory usage stays under defined thresholds
- [ ] Cross-platform compatibility verified

**Failure Analysis**:
- Review test logs for component interaction issues
- Check API rate limiting and error responses
- Validate data persistence and integrity
- Analyze performance bottlenecks
- Verify error handling and recovery mechanisms

These integration testing procedures ensure that all components work together reliably and handle real-world usage scenarios effectively.