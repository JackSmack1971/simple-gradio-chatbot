# Testing Standards - Personal AI Chatbot

## Overview

This document establishes testing standards and conventions for the Personal AI Chatbot project. As a personal productivity tool, testing focuses on critical functionality while maintaining practical development velocity.

## Testing Strategy

### Testing Pyramid

```
Integration Tests (Few, High Value)
    ├── API Integration
    ├── UI Component Integration
    └── End-to-End Flows

Unit Tests (Core Business Logic)
    ├── Controllers
    ├── Processors
    ├── Managers
    └── Utilities

Static Analysis (Automated)
    ├── Type Checking (MyPy)
    ├── Linting (Flake8)
    └── Formatting (Black)
```

### Test Coverage Goals

- **Core Business Logic**: 80%+ coverage
- **Data Layer**: 90%+ coverage (critical for data integrity)
- **API Integration**: 70%+ coverage
- **UI Components**: 50%+ coverage (focus on logic, not UI rendering)
- **Utilities**: 60%+ coverage

## Test Organization

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── unit/                    # Unit tests
│   ├── __init__.py
│   ├── test_controllers.py
│   ├── test_processors.py
│   ├── test_managers.py
│   ├── test_data_models.py
│   └── test_utils.py
├── integration/             # Integration tests
│   ├── __init__.py
│   ├── test_chat_flow.py
│   ├── test_api_integration.py
│   ├── test_storage_integration.py
│   └── test_ui_integration.py
├── fixtures/                # Test data and mocks
│   ├── __init__.py
│   ├── sample_messages.json
│   ├── mock_api_responses.json
│   ├── test_conversations.py
│   └── mock_clients.py
└── helpers/                 # Test utilities
    ├── __init__.py
    └── test_helpers.py
```

### Test File Naming

- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<feature>_integration.py`
- Fixtures: `<fixture_name>.py` or `<fixture_name>.json`

## Unit Testing Standards

### Test Structure

Each test should follow the Arrange-Act-Assert pattern:

```python
import pytest
from unittest.mock import Mock

def test_message_processor_validates_content():
    # Arrange
    processor = MessageProcessor()
    invalid_content = ""

    # Act
    is_valid, error_msg = processor.validate_message(invalid_content)

    # Assert
    assert not is_valid
    assert "empty" in error_msg.lower()
```

### Test Naming Conventions

```python
# Good: descriptive test names
def test_message_processor_validates_empty_content():
    pass

def test_message_processor_rejects_messages_over_max_length():
    pass

def test_api_client_handles_timeout_with_retry():
    pass

# Avoid: generic names
def test_validate():  # ❌ Too vague
    pass

def test_api_call():  # ❌ Not specific enough
    pass
```

### Mocking and Fixtures

Use fixtures for common test data:

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def sample_message():
    return Message(
        id="msg_001",
        role="user",
        content="Hello world",
        timestamp=datetime.now()
    )

@pytest.fixture
def mock_api_client():
    client = Mock()
    client.send_chat_request.return_value = {
        "choices": [{"message": {"content": "Hi there!"}}]
    }
    return client
```

### Parameterized Tests

Use pytest.mark.parametrize for multiple test cases:

```python
import pytest

@pytest.mark.parametrize("content,expected_valid,expected_error", [
    ("", False, "empty"),
    ("Valid message", True, ""),
    ("A" * 4001, False, "too long"),
])
def test_message_validation(content, expected_valid, expected_error):
    processor = MessageProcessor()
    is_valid, error_msg = processor.validate_message(content)

    assert is_valid == expected_valid
    if expected_error:
        assert expected_error in error_msg
```

## Integration Testing Standards

### API Integration Tests

Test external API interactions with proper mocking:

```python
def test_chat_controller_sends_message_to_api(mock_api_client):
    # Arrange
    controller = ChatController(api_client=mock_api_client)
    user_message = "Test message"

    # Act
    response = controller.send_message(user_message, "test-model")

    # Assert
    mock_api_client.send_chat_request.assert_called_once()
    assert response.content == "Hi there!"
```

### UI Integration Tests

Test Gradio component interactions:

```python
def test_gradio_interface_updates_chat_display():
    # This would require Gradio's testing utilities
    # Focus on business logic rather than UI rendering
    pass
```

### End-to-End Flow Tests

Test complete user journeys:

```python
def test_complete_chat_conversation_flow(temp_storage):
    # Arrange
    app = create_test_app(temp_storage)

    # Act
    conversation_id = app.create_conversation("Test Chat")
    message_id = app.send_message(conversation_id, "Hello", "test-model")
    response = app.get_message(conversation_id, message_id)

    # Assert
    assert response.role == "assistant"
    assert len(response.content) > 0
```

## Test Data Management

### Test Fixtures

Create reusable test data:

```python
# tests/fixtures/test_conversations.py
import json
from pathlib import Path

def load_sample_conversation():
    """Load sample conversation data for testing."""
    fixture_path = Path(__file__).parent / "sample_conversation.json"
    with open(fixture_path) as f:
        return json.load(f)

def create_test_conversation():
    """Create a test conversation with sample messages."""
    return Conversation(
        id="test_conv_001",
        title="Test Conversation",
        messages=[
            Message(id="msg_001", role="user", content="Hello"),
            Message(id="msg_002", role="assistant", content="Hi there!")
        ]
    )
```

### Mock Objects

Create mock clients for external dependencies:

```python
# tests/fixtures/mock_clients.py
from unittest.mock import Mock

class MockOpenRouterClient:
    def __init__(self):
        self.responses = []
        self.requests = []

    def send_chat_request(self, messages, model, **kwargs):
        self.requests.append((messages, model, kwargs))
        if self.responses:
            return self.responses.pop(0)
        return {"choices": [{"message": {"content": "Mock response"}}]}

    def add_response(self, response):
        self.responses.append(response)
```

## Testing Best Practices

### Test Isolation

- Each test should be independent
- Use unique test data to avoid conflicts
- Clean up resources after tests

```python
@pytest.fixture
def temp_conversation_storage(tmp_path):
    """Create temporary storage for testing."""
    storage = ConversationStorage(tmp_path / "conversations")
    yield storage
    # Cleanup happens automatically with tmp_path
```

### Test Categories

#### Happy Path Tests
```python
def test_successful_message_processing():
    """Test normal message processing flow."""
    processor = MessageProcessor()
    result = processor.process_message("Hello world")
    assert result is not None
```

#### Error Path Tests
```python
def test_api_timeout_handling():
    """Test graceful handling of API timeouts."""
    client = APIClient()
    with pytest.raises(APIError, match="timeout"):
        client.send_request_with_timeout("slow_endpoint", timeout=0.001)
```

#### Edge Case Tests
```python
def test_empty_conversation_handling():
    """Test behavior with empty conversations."""
    manager = ConversationManager()
    conversations = manager.list_conversations()
    assert len(conversations) == 0
```

### Async Testing

Handle async functions properly:

```python
import pytest_asyncio

@pytest.mark.asyncio
async def test_async_api_call():
    """Test asynchronous API operations."""
    client = APIClient()
    result = await client.send_async_request("test_endpoint")
    assert result is not None
```

## Test Automation

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
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
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = src
omit =
    src/__init__.py
    src/main.py
    tests/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
```

### Pre-commit Test Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Performance Testing

### Load Testing

Basic load testing for critical paths:

```python
def test_concurrent_api_requests():
    """Test handling of concurrent API requests."""
    import asyncio
    import aiohttp

    async def make_request(session, url):
        async with session.get(url) as response:
            return await response.text()

    async def test_load():
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session, f"http://api.example.com/{i}") for i in range(10)]
            results = await asyncio.gather(*tasks)
            assert len(results) == 10

    asyncio.run(test_load())
```

### Memory Testing

Monitor memory usage in critical operations:

```python
def test_memory_usage_in_conversation_loading():
    """Test memory usage when loading large conversations."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Load large conversation
    manager = ConversationManager()
    large_conversation = manager.load_conversation("large_conv_id")

    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    # Assert reasonable memory usage (e.g., < 50MB increase)
    assert memory_increase < 50 * 1024 * 1024
```

## Test Maintenance

### Test Code Quality

Apply same standards to test code:
- Use type hints in test files
- Follow naming conventions
- Keep tests readable and maintainable

### Flaky Test Management

Handle intermittent test failures:

```python
@pytest.mark.flaky(retries=3, delay=1)
def test_unreliable_api_integration():
    """Test that may occasionally fail due to network issues."""
    # Test implementation
    pass
```

### Test Documentation

Document complex test scenarios:

```python
def test_message_token_estimation_accuracy():
    """
    Test that token estimation is within 10% of actual API usage.

    This test ensures our token counting logic provides reasonable
    estimates for cost calculation and rate limiting.
    """
    estimator = TokenEstimator()
    test_messages = [
        "Hello world",
        "This is a longer message with more content",
        "Complex message with numbers 123 and symbols @#$%"
    ]

    for message in test_messages:
        estimated = estimator.estimate_tokens(message)
        actual = get_actual_token_count(message)  # From API

        # Allow 10% variance
        assert abs(estimated - actual) / actual <= 0.1
```

## Testing Tools Configuration

### Pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --disable-warnings
    --tb=short
    -v
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    flaky: marks tests that may fail intermittently
```

### Test Dependencies

```txt
# requirements-test.txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
responses>=0.23.0  # For HTTP mocking
freezegun>=1.2.0   # For time mocking
```

These standards provide comprehensive testing coverage while remaining practical for a personal development project. Focus on testing the most critical functionality and integration points to ensure reliability without excessive overhead.