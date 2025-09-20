# Coding Standards - Personal AI Chatbot

## Overview

This document establishes coding standards and conventions for the Personal AI Chatbot project. As a personal productivity tool maintained by a single developer, these standards prioritize readability, maintainability, and developer experience while maintaining practical constraints.

## Python Standards

### Naming Conventions

Follow PEP 8 naming conventions with project-specific adaptations:

#### Variables and Functions
```python
# Good: snake_case for variables and functions
user_input = "Hello world"
def process_message(content: str) -> str:
    return content.strip()

# Avoid: camelCase, PascalCase for variables
userInput = "bad"  # ❌
processMessage = lambda x: x  # ❌
```

#### Classes and Types
```python
# Good: PascalCase for classes
class ChatController:
    pass

class MessageProcessor:
    pass

# Type aliases
MessageList = List[Message]
ConfigDict = Dict[str, Any]
```

#### Constants
```python
# Good: UPPER_SNAKE_CASE for constants
MAX_MESSAGE_LENGTH = 4000
DEFAULT_MODEL = "anthropic/claude-3-haiku"
API_TIMEOUT_SECONDS = 30
```

#### Private Members
```python
# Good: single underscore prefix for private methods/variables
class APIClient:
    def __init__(self):
        self._api_key = None
        self._session = None

    def _validate_response(self, response: dict) -> bool:
        pass
```

### Imports Organization

Group imports in this order with blank lines between groups:

```python
# Standard library imports
import json
import os
from typing import Dict, List, Optional

# Third-party imports
import gradio as gr
import requests
from openai import OpenAI

# Local imports
from .config import ConfigManager
from .models import Message, Conversation
```

### Code Structure

#### Function Length
- Functions should be ≤ 30 lines
- Complex functions should be broken into smaller, focused functions
- Use early returns to reduce nesting

```python
# Good: focused, single responsibility
def validate_message(content: str) -> tuple[bool, str]:
    if not content or not content.strip():
        return False, "Message cannot be empty"

    if len(content) > MAX_MESSAGE_LENGTH:
        return False, f"Message too long (max {MAX_MESSAGE_LENGTH} chars)"

    return True, ""

# Avoid: long, complex functions
def process_user_input(input_text):  # ❌ Too many responsibilities
    # validation, processing, API call, response handling all in one
    pass
```

#### Class Design
- Classes should have single responsibility
- Use dataclasses for data containers
- Keep classes focused and cohesive

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Message:
    id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    model: Optional[str] = None
    tokens: Optional[int] = None
```

## Gradio-Specific Patterns

### Component Naming
```python
# Good: descriptive names with component type
chat_input = gr.Textbox(label="Your message", placeholder="Type here...")
send_button = gr.Button("Send Message", variant="primary")
model_dropdown = gr.Dropdown(label="AI Model", choices=[])

# Avoid: generic names
textbox1 = gr.Textbox()  # ❌
btn = gr.Button()  # ❌
```

### State Management
```python
# Good: use Gradio's state management appropriately
def chat_interface():
    with gr.Blocks() as demo:
        # Shared state
        conversation_state = gr.State([])

        with gr.Row():
            chat_history = gr.Chatbot()
            model_selector = gr.Dropdown(choices=[], label="Model")

        # Event handlers maintain state
        send_btn.click(
            send_message,
            inputs=[user_input, model_selector, conversation_state],
            outputs=[chat_history, conversation_state]
        )

    return demo
```

### Event Handling
```python
# Good: clear event handler functions
def send_message(user_input: str, model: str, history: list) -> tuple:
    """Handle message sending with proper error handling"""
    try:
        # Process message
        response = get_ai_response(user_input, model)

        # Update history
        new_history = history + [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ]

        return new_history, new_history
    except Exception as e:
        gr.Error(f"Failed to send message: {str(e)}")
        return history, history
```

## Error Handling Patterns

### Exception Handling
```python
# Good: specific exception handling with user-friendly messages
def call_api_with_retry(request_func, max_retries=3):
    """Call API function with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return request_func()
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                raise APIError("Request timed out after retries")
            time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.ConnectionError:
            if attempt == max_retries - 1:
                raise APIError("Connection failed - check internet")
            time.sleep(1)

# Custom exceptions for domain-specific errors
class APIError(Exception):
    """Base API error"""
    pass

class RateLimitError(APIError):
    """Rate limit exceeded"""
    pass
```

### User Feedback
```python
# Good: clear, actionable error messages
def validate_api_key(api_key: str) -> tuple[bool, str]:
    if not api_key:
        return False, "API key is required"

    if not api_key.startswith("sk-"):
        return False, "API key should start with 'sk-'"

    if len(api_key) < 20:
        return False, "API key appears too short"

    return True, ""
```

## Type Hints

### Basic Typing
```python
# Good: use type hints for function parameters and return values
from typing import Dict, List, Optional, Tuple

def process_message(content: str, model: str) -> Message:
    pass

def get_conversation_list() -> List[ConversationMetadata]:
    pass

def find_conversation(conversation_id: str) -> Optional[Conversation]:
    pass

def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    pass
```

### Advanced Types
```python
# Good: use Union, Literal for complex types
from typing import Union, Literal

MessageRole = Literal["user", "assistant", "system"]

def create_message(
    role: MessageRole,
    content: str,
    metadata: Optional[Dict[str, Union[str, int, float]]] = None
) -> Message:
    pass
```

## Logging Standards

### Log Levels and Messages
```python
import logging

logger = logging.getLogger(__name__)

# Good: appropriate log levels with context
def send_chat_request(messages, model):
    logger.info(f"Sending request to model: {model}")

    try:
        response = api_call(messages, model)
        logger.debug(f"Received response with {len(response)} tokens")
        return response
    except Exception as e:
        logger.error(f"API call failed for model {model}: {str(e)}")
        raise
```

### Structured Logging
```python
# Good: include relevant context in log messages
def process_conversation_save(conversation_id: str, messages: list):
    logger.info(
        "Saving conversation",
        extra={
            "conversation_id": conversation_id,
            "message_count": len(messages),
            "total_tokens": sum(m.get("tokens", 0) for m in messages)
        }
    )
```

## Configuration Management

### Environment Variables
```python
# Good: clear naming with PROJECT prefix
# .env file
PERSONAL_CHATBOT_API_KEY=sk-...
PERSONAL_CHATBOT_DEFAULT_MODEL=anthropic/claude-3-haiku
PERSONAL_CHATBOT_MAX_TOKENS=4000

# Python usage
import os

API_KEY = os.getenv("PERSONAL_CHATBOT_API_KEY")
DEFAULT_MODEL = os.getenv("PERSONAL_CHATBOT_DEFAULT_MODEL", "anthropic/claude-3-haiku")
```

## Code Quality Tools

### Black Formatting
- Line length: 88 characters
- Use double quotes for strings
- Automatic import sorting

### Flake8 Linting
- Max line length: 88 (consistent with Black)
- Ignore E203 (whitespace before colon) for Black compatibility
- Max complexity: 10

### MyPy Type Checking
- Strict type checking enabled
- Disallow untyped calls
- Warn on missing imports

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
```

## Development Workflow

### Git Commit Messages
```
feat: add conversation export functionality
fix: handle API timeout errors gracefully
docs: update installation instructions
refactor: simplify message validation logic
```

### Branch Naming
```
feature/add-conversation-search
bugfix/api-rate-limit-handling
refactor/message-processor-cleanup
```

## Performance Considerations

### Memory Management
```python
# Good: clean up resources explicitly
class APIClient:
    def __init__(self):
        self._session = requests.Session()

    def __del__(self):
        if hasattr(self, '_session'):
            self._session.close()

    def close(self):
        """Explicit cleanup method"""
        if self._session:
            self._session.close()
            self._session = None
```

### Efficient Data Structures
```python
# Good: use appropriate data structures
from collections import deque

class MessageBuffer:
    def __init__(self, max_size=100):
        self._messages = deque(maxlen=max_size)

    def add_message(self, message):
        self._messages.append(message)

    def get_recent(self, count=10):
        return list(self._messages)[-count:]
```

## Security Practices

### Input Validation
```python
# Good: validate all inputs
def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters from filename"""
    import re
    return re.sub(r'[^\w\-_\.]', '', filename)

def validate_url(url: str) -> bool:
    """Basic URL validation"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)
```

### Sensitive Data Handling
```python
# Good: never log sensitive data
def log_api_call(endpoint: str, success: bool):
    # Log endpoint but not API key or full request
    logger.info(f"API call to {endpoint}: {'success' if success else 'failed'}")
```

These standards balance code quality with development velocity for a personal productivity tool. They should be enforced through automated tools where possible, with manual review for complex cases.